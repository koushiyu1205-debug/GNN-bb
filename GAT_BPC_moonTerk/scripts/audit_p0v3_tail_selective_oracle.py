#!/usr/bin/env python3
"""Audit a one-shot tail-only selective branch landing before training."""

from __future__ import annotations

import argparse
import hashlib
import json
from math import ceil, isclose, isfinite
from pathlib import Path
import random
from statistics import mean
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.branch_e2e_costs import (  # noqa: E402
    canonical_guided_e2e_costs,
    canonical_selective_guidance_costs,
)
from lunar_ice_bpc.guidance.branch_tail_trigger import (  # noqa: E402
    FIRST_EXACT_TOP3_ELAPSED_PER_TASK_V1,
    evaluate_branch_tail_trigger,
)


SCHEMA_VERSION = "lunar_ice_bpc.tail_selective_oracle_gate.v1"
SPLIT_SCHEMA_VERSION = "lunar_ice_bpc.branch_grouped_split_manifest.v2"
REAL_MAP_SP50_DOMAIN = "real_lunar_south_pole_sp50_benchmark_v1"
CENSUS_SCHEMA_VERSION = (
    "lunar_ice_bpc.no_task_wait_v3_branch_opportunity_census.v1"
)
E2E_SCHEMA_VERSION = (
    "lunar_ice_bpc.no_task_wait_v3_branch_state_oracle.v2"
)


def _tail_stop_loss_decision(
    *,
    evidence_role: str,
    pilot_threshold_reached: bool,
    all_census_exact: bool,
    tail_trigger_count: int,
    missing_trigger_gold_count: int,
    oracle_upper: float | None,
    oracle_gold_ready: bool,
    instance_cap_reached: bool,
) -> dict:
    if evidence_role == "DESIGN_ONLY":
        positive = bool(
            tail_trigger_count > 0
            and oracle_upper is not None
            and float(oracle_upper) > 0.0
        )
        return {
            "decision_reason_code": (
                "FRESH_VALIDATION_AUTHORIZED"
                if positive
                else "DESIGN_SIGNAL_INSUFFICIENT"
            ),
            "terminate_tail_selective_landing": False,
            "fresh_validation_collection_authorized": positive,
            "matched_e2e_collection_authorized": False,
            "bounded_fresh_expansion_authorized": False,
        }
    if (
        pilot_threshold_reached
        and all_census_exact
        and int(tail_trigger_count) == 0
    ):
        return {
            "decision_reason_code": "FRESH_EXACT_PILOT_ZERO_TAIL_TRIGGER",
            "terminate_tail_selective_landing": True,
            "fresh_validation_collection_authorized": False,
            "matched_e2e_collection_authorized": False,
            "bounded_fresh_expansion_authorized": False,
        }
    if int(missing_trigger_gold_count) > 0:
        return {
            "decision_reason_code": "TAIL_TRIGGER_MATCHED_E2E_GOLD_MISSING",
            "terminate_tail_selective_landing": False,
            "fresh_validation_collection_authorized": False,
            "matched_e2e_collection_authorized": True,
            "bounded_fresh_expansion_authorized": False,
        }
    if (
        pilot_threshold_reached
        and all_census_exact
        and oracle_upper is not None
        and float(oracle_upper) <= 0.0
    ):
        return {
            "decision_reason_code": "FRESH_SELECTIVE_ORACLE_NONPOSITIVE",
            "terminate_tail_selective_landing": True,
            "fresh_validation_collection_authorized": False,
            "matched_e2e_collection_authorized": False,
            "bounded_fresh_expansion_authorized": False,
        }
    positive = bool(
        oracle_upper is not None and float(oracle_upper) > 0.0
    )
    if (
        pilot_threshold_reached
        and all_census_exact
        and positive
        and not oracle_gold_ready
        and not instance_cap_reached
    ):
        return {
            "decision_reason_code": "BOUNDED_FRESH_EXPANSION_ONLY",
            "terminate_tail_selective_landing": False,
            "fresh_validation_collection_authorized": False,
            "matched_e2e_collection_authorized": False,
            "bounded_fresh_expansion_authorized": True,
        }
    if instance_cap_reached and not oracle_gold_ready:
        return {
            "decision_reason_code": (
                "FRESH_CAP_REACHED_WITH_INSUFFICIENT_TAIL_GOLD"
            ),
            "terminate_tail_selective_landing": True,
            "fresh_validation_collection_authorized": False,
            "matched_e2e_collection_authorized": False,
            "bounded_fresh_expansion_authorized": False,
        }
    return {
        "decision_reason_code": "FRESH_ORACLE_EVALUATION_INCOMPLETE",
        "terminate_tail_selective_landing": False,
        "fresh_validation_collection_authorized": False,
        "matched_e2e_collection_authorized": False,
        "bounded_fresh_expansion_authorized": False,
    }


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _balanced_bootstrap(
    values: dict[int, dict[str, list[float]]],
    *,
    samples: int,
    seed: int,
) -> tuple[float | None, list[float | None], int]:
    clusters = {
        int(scale): [
            mean(rows) for rows in by_instance.values() if rows
        ]
        for scale, by_instance in values.items()
    }
    clusters = {
        scale: rows for scale, rows in clusters.items() if rows
    }
    if not clusters:
        return None, [None, None], 0
    observed = mean(mean(rows) for rows in clusters.values())
    generator = random.Random(int(seed))
    draws = sorted(
        mean(
            mean(generator.choice(rows) for _ in rows)
            for rows in clusters.values()
        )
        for _ in range(max(1, int(samples)))
    )
    return (
        observed,
        [
            float(draws[max(0, int(0.025 * len(draws)))]),
            float(
                draws[
                    max(
                        0,
                        min(
                            len(draws) - 1,
                            int(0.975 * len(draws)) - 1,
                        ),
                    )
                ]
            ),
        ],
        sum(len(rows) for rows in clusters.values()),
    )


def _authorized_split_hashes(split: dict) -> set[str]:
    return {
        str(split["manifest_hash"]),
        *{
            str(value)
            for value in split.get(
                "authorized_collection_split_manifest_hashes"
            )
            or ()
        },
    }


def _target_census_rows(
    *,
    paths: list[Path],
    split_manifest: dict,
    required_scales: tuple[int, ...],
) -> tuple[list[dict], list[dict]]:
    development = {
        str(row["instance_content_hash"]): row
        for row in split_manifest.get("development") or ()
        if str(row.get("instance_generator_domain") or "")
        == REAL_MAP_SP50_DOMAIN
        and int(row["scale"]) in required_scales
    }
    authorized = _authorized_split_hashes(split_manifest)
    rows = []
    bindings = []
    seen = set()
    for path in paths:
        report = _load(path)
        if (
            str(report.get("schema_version") or "")
            != CENSUS_SCHEMA_VERSION
            or str(report.get("split_manifest_hash") or "")
            not in authorized
            or str(report.get("instance_generator_domain") or "")
            != REAL_MAP_SP50_DOMAIN
            or int(report.get("scale") or 0) not in required_scales
            or report.get("development_only") is not True
            or report.get("training_authorized") is not False
        ):
            raise SystemExit("tail census binding mismatch")
        scale = int(report["scale"])
        bindings.append(
            {
                "path": str(path.resolve()),
                "sha256": _file_sha256(path),
                "scale": scale,
            }
        )
        for source in report.get("rows") or ():
            content_hash = str(source["instance_content_hash"])
            key = (content_hash, scale)
            if (
                key in seen
                or content_hash not in development
                or int(development[content_hash]["scale"]) != scale
            ):
                raise SystemExit("tail census row outside development")
            seen.add(key)
            status = str(source.get("status") or "")
            if status not in {
                "EXACT_ACTIONABLE",
                "EXACT_NONACTIONABLE",
                "ROOT_CENSORED",
                "TREE_CENSORED",
                "INFRASTRUCTURE_CENSORED",
            }:
                raise SystemExit("unknown tail census status")
            rows.append(
                {
                    "instance_content_hash": content_hash,
                    "scale": scale,
                    "status": status,
                    "driver_wall_sec": float(
                        source.get("driver_wall_sec") or 0.0
                    ),
                }
            )
    return rows, bindings


def _gold_binding(
    *,
    path: Path,
    split_manifest: dict,
    census_actionable_hashes: set[str],
    guidance_lifecycle_overhead_sec: float,
) -> dict:
    report = _load(path)
    content_hash = str(report.get("instance_content_hash") or "")
    development = {
        str(row["instance_content_hash"]): row
        for row in split_manifest.get("development") or ()
        if str(row.get("instance_generator_domain") or "")
        == REAL_MAP_SP50_DOMAIN
    }
    states = list(report.get("state_reports") or ())
    if (
        str(report.get("schema_version") or "") != E2E_SCHEMA_VERSION
        or str(report.get("split_manifest_hash") or "")
        not in _authorized_split_hashes(split_manifest)
        or content_hash not in development
        or content_hash not in census_actionable_hashes
        or report.get("development_only") is not True
        or report.get("training_authorized") is not False
        or report.get("deployable") is not False
        or report.get("one_deviation_only") is not True
        or report.get("control_exact_safe") is not True
        or report.get("control_universe_safe") is not True
        or int(report.get("guidance_branch_pair_drop_count") or 0) != 0
        or int(report.get("guidance_filter_count") or 0) != 0
        or len(states) != 1
    ):
        raise SystemExit("tail E2E report binding mismatch")
    state = states[0]
    control = dict(report.get("control") or {})
    arms = list(state.get("arms") or ())
    top3 = list(state.get("top3_candidate_ids") or ())
    before = state.get("legal_branch_shortlist_hash_before_sort")
    after = state.get("legal_branch_shortlist_hash_after_sort")
    if (
        state.get("complete_matched_e2e_gold") is not True
        or state.get("objective_matches_across_arms") is not True
        or int(state.get("candidate_count") or 0) != 3
        or len(top3) != 3
        or before != after
        or control.get("exact_safe") is not True
        or control.get("universe_safe") is not True
        or control.get("descendant_pricing_certificate_reused") is not False
        or len(arms) != 2
    ):
        raise SystemExit("tail E2E exact safety mismatch")
    by_rank = {0: control}
    for arm in arms:
        rank = int(arm.get("requested_rank_index") or -1)
        if (
            rank not in {1, 2}
            or rank in by_rank
            or arm.get("exact_safe") is not True
            or arm.get("universe_safe") is not True
            or arm.get("counterfactual_universe_matches_control")
            is not True
            or arm.get("descendant_pricing_certificate_reused") is not False
            or int(arm.get("target_selected_rank_index") or -1) != rank
            or list(arm.get("target_top3_candidate_ids") or ()) != top3
            or arm.get(
                "target_legal_branch_shortlist_hash_before_sort"
            )
            != before
            or arm.get(
                "target_legal_branch_shortlist_hash_after_sort"
            )
            != after
        ):
            raise SystemExit("tail E2E arm safety mismatch")
        by_rank[rank] = arm
    if set(by_rank) != {0, 1, 2}:
        raise SystemExit("tail E2E report lacks all three arms")
    objectives = [float(by_rank[index]["objective"]) for index in range(3)]
    if not all(isfinite(value) for value in objectives) or not all(
        isclose(value, objectives[0], rel_tol=0.0, abs_tol=1.0e-6)
        for value in objectives
    ):
        raise SystemExit("tail E2E objectives differ")
    costs = canonical_guided_e2e_costs(
        arm_by_rank=by_rank,
        guidance_lifecycle_overhead_sec=float(
            guidance_lifecycle_overhead_sec
        ),
    )
    return {
        "instance_content_hash": content_hash,
        "scale": int(development[content_hash]["scale"]),
        "path_hash": str(state["path_hash"]),
        "branch_e2e_p0_control_wall_sec": float(
            costs["p0_control_wall_sec"]
        ),
        "branch_guidance_lifecycle_overhead_sec": float(
            costs["guidance_lifecycle_overhead_sec"]
        ),
        "branch_e2e_wall_sec_by_rank": dict(
            costs["guided_action_wall_sec_by_rank"]
        ),
        "e2e_report_path": str(path.resolve()),
        "e2e_report_sha256": _file_sha256(path),
    }


def _details(paths: list[Path]) -> dict[str, dict]:
    result = {}
    for path in paths:
        report = _load(path)
        for row in report.get("rows") or ():
            content_hash = str(row["instance_content_hash"])
            if content_hash in result:
                raise SystemExit("duplicate tail census instance")
            result[content_hash] = {
                **row,
                "scale": int(report["scale"]),
            }
    return result


def _trigger_from_census_row(row: dict) -> dict:
    status = str(row["status"])
    output_dir = Path(str(row["output_dir"]))
    opportunity_path = output_dir / "branch_opportunity_report.json"
    opportunity = _load(opportunity_path) if opportunity_path.is_file() else {}
    exact_actionable = status == "EXACT_ACTIONABLE"
    candidate_count = int(
        opportunity.get("candidate_count")
        if opportunity
        else row.get("candidate_count")
        or 0
    )
    before = str(
        opportunity.get("legal_branch_shortlist_hash_before_sort") or ""
    )
    after = str(
        opportunity.get("legal_branch_shortlist_hash_after_sort") or ""
    )
    node = {
        "node_id": "node_000",
        "node_status": "BRANCHED" if exact_actionable else status,
        "pricing_state": (
            "CERTIFIED_NO_NEGATIVE" if exact_actionable else "INCOMPLETE_LIMIT"
        ),
        "node_lp_bound_official": exact_actionable,
        "development_branch_selected_rank_index": 0,
        "development_branch_rank_fallback_to_p0": False,
        "guidance_branch_pair_drop_count": int(
            opportunity.get("guidance_branch_pair_drop_count") or 0
        ),
        "guidance_filter_count": int(
            opportunity.get("guidance_filter_count") or 0
        ),
        "legal_branch_shortlist_hash_before_sort": before,
        "legal_branch_shortlist_hash_after_sort": after,
        "tree_elapsed_sec_at_exit": float(
            opportunity.get("p0_root_node_wall_sec")
            or row.get("tree_wall_sec")
            or 0.0
        ),
        "fractional_branch_probe": {
            "candidates": [
                {"candidate_index": index}
                for index in range(candidate_count)
            ]
        },
    }
    decision = evaluate_branch_tail_trigger(
        node=node,
        root_wall_sec=float(
            opportunity.get("root_wall_sec")
            or row.get("root_wall_sec")
            or 0.0
        ),
        scale=int(row["scale"]),
        already_triggered=False,
        policy_id=FIRST_EXACT_TOP3_ELAPSED_PER_TASK_V1,
    )
    return {
        **decision.to_payload(),
        "opportunity_report_path": (
            None if not opportunity_path.is_file() else str(opportunity_path)
        ),
        "opportunity_report_sha256": (
            None
            if not opportunity_path.is_file()
            else _file_sha256(opportunity_path)
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument(
        "--target-census-report",
        action="append",
        required=True,
    )
    parser.add_argument(
        "--e2e-oracle-report",
        action="append",
        default=[],
    )
    parser.add_argument("--output-report", required=True)
    parser.add_argument(
        "--evidence-role",
        choices=("DESIGN_ONLY", "FRESH_VALIDATION"),
        default="DESIGN_ONLY",
    )
    parser.add_argument(
        "--required-independent-trigger-gold-per-scale",
        type=int,
        default=20,
    )
    parser.add_argument(
        "--required-oracle-trigger-gold-per-scale",
        type=int,
        default=2,
    )
    parser.add_argument(
        "--minimum-fresh-pilot-instances-per-scale",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--maximum-fresh-instances-per-scale",
        type=int,
        default=6,
    )
    parser.add_argument(
        "--maximum-projected-development-instances-per-scale",
        type=int,
        default=120,
    )
    parser.add_argument(
        "--guidance-lifecycle-overhead-sec",
        type=float,
        default=0.02,
    )
    parser.add_argument("--bootstrap-samples", type=int, default=20000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260726)
    args = parser.parse_args()

    split_path = Path(args.split_manifest)
    split = _load(split_path)
    if (
        str(split.get("schema_version") or "") != SPLIT_SCHEMA_VERSION
        or not bool((split.get("audit") or {}).get("passed"))
        or split.get("calibration_read_authorized") is not False
    ):
        raise SystemExit("tail selective split is invalid")
    census_paths = [Path(value) for value in args.target_census_report]
    census_rows, census_bindings = _target_census_rows(
        paths=census_paths,
        split_manifest=split,
        required_scales=(20, 30),
    )
    details = _details(census_paths)
    actionable_hashes = {
        str(row["instance_content_hash"])
        for row in census_rows
        if str(row["status"]) == "EXACT_ACTIONABLE"
    }
    gold_bindings = [
        _gold_binding(
            path=Path(value),
            split_manifest=split,
            census_actionable_hashes=actionable_hashes,
            guidance_lifecycle_overhead_sec=float(
                args.guidance_lifecycle_overhead_sec
            ),
        )
        for value in args.e2e_oracle_report
    ]
    gold_by_hash = {
        str(row["instance_content_hash"]): row
        for row in gold_bindings
    }
    event_rows = []
    gain_clusters: dict[int, dict[str, list[float]]] = {}
    missing_trigger_gold = []
    for census in census_rows:
        content_hash = str(census["instance_content_hash"])
        detail = details[content_hash]
        trigger = _trigger_from_census_row(detail)
        status = str(census["status"])
        net_gain = None
        action = None
        if trigger["tail_triggered"]:
            gold = gold_by_hash.get(content_hash)
            if gold is None:
                missing_trigger_gold.append(content_hash)
            else:
                selective = canonical_selective_guidance_costs(
                    {
                        "p0_control_wall_sec": float(
                            gold["branch_e2e_p0_control_wall_sec"]
                        ),
                        "guidance_lifecycle_overhead_sec": float(
                            gold[
                                "branch_guidance_lifecycle_overhead_sec"
                            ]
                        ),
                        "guided_action_wall_sec_by_rank": dict(
                            gold["branch_e2e_wall_sec_by_rank"]
                        ),
                    }
                )
                net_gain = float(
                    selective["selective_oracle_net_gain_sec"]
                )
                action = str(selective["selective_oracle_action"])
        elif status in {"EXACT_ACTIONABLE", "EXACT_NONACTIONABLE"}:
            net_gain = 0.0
            action = "PRE_IMPORT_BYPASS"
        if net_gain is not None:
            gain_clusters.setdefault(int(census["scale"]), {}).setdefault(
                content_hash,
                [],
            ).append(net_gain)
        event_rows.append(
            {
                **census,
                **trigger,
                "selective_oracle_action": action,
                "selective_oracle_net_gain_sec": net_gain,
            }
        )
    observed, interval, cluster_count = _balanced_bootstrap(
        gain_clusters,
        samples=int(args.bootstrap_samples),
        seed=int(args.bootstrap_seed),
    )
    exact_by_scale = {
        scale: sum(
            int(row["scale"]) == scale
            and str(row["status"])
            in {"EXACT_ACTIONABLE", "EXACT_NONACTIONABLE"}
            for row in event_rows
        )
        for scale in (20, 30)
    }
    trigger_by_scale = {
        scale: sum(
            int(row["scale"]) == scale
            and row["tail_triggered"] is True
            for row in event_rows
        )
        for scale in (20, 30)
    }
    gold_by_scale = {
        scale: sum(
            int(row["scale"]) == scale
            and row["tail_triggered"] is True
            and row["selective_oracle_net_gain_sec"] is not None
            for row in event_rows
        )
        for scale in (20, 30)
    }
    projected = {}
    required = int(args.required_independent_trigger_gold_per_scale)
    for scale in (20, 30):
        if not exact_by_scale[scale] or not trigger_by_scale[scale]:
            projected[str(scale)] = None
        else:
            rate = trigger_by_scale[scale] / exact_by_scale[scale]
            projected[str(scale)] = int(ceil(required / rate))
    all_census_exact = all(
        str(row["status"])
        in {"EXACT_ACTIONABLE", "EXACT_NONACTIONABLE"}
        for row in event_rows
    )
    gold_complete = not missing_trigger_gold
    enough_training_gold = all(
        gold_by_scale[scale] >= required for scale in (20, 30)
    )
    enough_oracle_gold = all(
        gold_by_scale[scale]
        >= int(args.required_oracle_trigger_gold_per_scale)
        for scale in (20, 30)
    )
    projected_feasible = all(
        projected[str(scale)] is not None
        and int(projected[str(scale)])
        <= int(args.maximum_projected_development_instances_per_scale)
        for scale in (20, 30)
    )
    oracle_lcb_positive = bool(
        interval[0] is not None and float(interval[0]) > 0.0
    )
    census_count_by_scale = {
        scale: sum(int(row["scale"]) == scale for row in event_rows)
        for scale in (20, 30)
    }
    pilot_threshold_reached = all(
        census_count_by_scale[scale]
        >= int(args.minimum_fresh_pilot_instances_per_scale)
        for scale in (20, 30)
    )
    instance_cap_reached = all(
        census_count_by_scale[scale]
        >= int(args.maximum_fresh_instances_per_scale)
        for scale in (20, 30)
    )
    decision = _tail_stop_loss_decision(
        evidence_role=str(args.evidence_role),
        pilot_threshold_reached=pilot_threshold_reached,
        all_census_exact=all_census_exact,
        tail_trigger_count=sum(trigger_by_scale.values()),
        missing_trigger_gold_count=len(missing_trigger_gold),
        oracle_upper=interval[1],
        oracle_gold_ready=enough_oracle_gold,
        instance_cap_reached=instance_cap_reached,
    )
    landing_validated = bool(
        str(args.evidence_role) == "FRESH_VALIDATION"
        and all_census_exact
        and gold_complete
        and enough_oracle_gold
        and projected_feasible
        and oracle_lcb_positive
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "evidence_role": str(args.evidence_role),
        "split_manifest_path": str(split_path.resolve()),
        "split_manifest_hash": split["manifest_hash"],
        "target_domain": REAL_MAP_SP50_DOMAIN,
        "tail_trigger_policy_id": (
            FIRST_EXACT_TOP3_ELAPSED_PER_TASK_V1
        ),
        "one_shot_per_instance": True,
        "pre_import_bypass_required": True,
        "calibration_used": False,
        "protected_final_test_used": False,
        "census_bindings": census_bindings,
        "gold_label_bindings": gold_bindings,
        "event_rows": event_rows,
        "observed": {
            "census_instance_count_by_scale": {
                str(key): value
                for key, value in census_count_by_scale.items()
            },
            "exact_instance_count_by_scale": {
                str(key): value for key, value in exact_by_scale.items()
            },
            "tail_trigger_count_by_scale": {
                str(key): value for key, value in trigger_by_scale.items()
            },
            "tail_trigger_gold_count_by_scale": {
                str(key): value for key, value in gold_by_scale.items()
            },
            "missing_tail_trigger_gold_hashes": sorted(
                missing_trigger_gold
            ),
            "selective_oracle_net_gain_sec_balanced_mean": observed,
            "selective_oracle_net_gain_sec_bootstrap_95ci": interval,
            "evaluable_instance_cluster_count": cluster_count,
            "projected_instances_for_required_trigger_gold_by_scale": (
                projected
            ),
        },
        "thresholds": {
            "required_independent_trigger_gold_per_scale": required,
            "required_oracle_trigger_gold_per_scale": int(
                args.required_oracle_trigger_gold_per_scale
            ),
            "minimum_fresh_pilot_instances_per_scale": int(
                args.minimum_fresh_pilot_instances_per_scale
            ),
            "maximum_fresh_instances_per_scale": int(
                args.maximum_fresh_instances_per_scale
            ),
            "maximum_projected_development_instances_per_scale": int(
                args.maximum_projected_development_instances_per_scale
            ),
            "guidance_lifecycle_overhead_sec": float(
                args.guidance_lifecycle_overhead_sec
            ),
        },
        "all_census_exact": all_census_exact,
        "tail_trigger_gold_complete": gold_complete,
        "fresh_pilot_threshold_reached": pilot_threshold_reached,
        "fresh_instance_cap_reached": instance_cap_reached,
        "required_oracle_trigger_gold_reached": enough_oracle_gold,
        "required_training_trigger_gold_reached": (
            enough_training_gold
        ),
        "projected_collection_feasible": projected_feasible,
        "selective_oracle_lcb_positive": oracle_lcb_positive,
        "decision_reason_code": decision["decision_reason_code"],
        "terminate_tail_selective_landing": decision[
            "terminate_tail_selective_landing"
        ],
        "fresh_validation_collection_authorized": (
            decision["fresh_validation_collection_authorized"]
        ),
        "matched_e2e_collection_authorized": decision[
            "matched_e2e_collection_authorized"
        ],
        "bounded_fresh_expansion_authorized": decision[
            "bounded_fresh_expansion_authorized"
        ],
        "tail_selective_landing_validated": landing_validated,
        "formal_feature_collection_authorized": landing_validated,
        "linear_training_authorized": bool(
            landing_validated and enough_training_gold
        ),
        "gat_training_authorized": False,
        "deployment_authorized": False,
    }
    output = Path(args.output_report)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
