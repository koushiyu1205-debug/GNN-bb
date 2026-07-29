#!/usr/bin/env python3
"""Gate expensive branch feature/aux collection using E2E gold alone."""

from __future__ import annotations

import argparse
import hashlib
import json
from math import isclose, isfinite
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_p0v3_branch_cross_domain_pilot import (  # noqa: E402
    REAL_MAP_SP50_DOMAIN,
    SPLIT_SCHEMA_VERSION,
    _balanced_bootstrap,
    _file_sha256,
    _target_census_rows,
    _target_stop_loss_decision,
)
from lunar_ice_bpc.guidance.branch_e2e_costs import (  # noqa: E402
    canonical_guided_e2e_costs,
)


SCHEMA_VERSION = "lunar_ice_bpc.branch_target_headroom_gate.v1"
E2E_SCHEMA_VERSION = (
    "lunar_ice_bpc.no_task_wait_v3_branch_state_oracle.v2"
)


def _label_payload(
    *,
    instance_content_hash: str,
    scale: int,
    path_hash: str,
    rank: int,
    net_gain_sec: float,
    walls: dict[str, float],
    p0_control_wall_sec: float,
    guidance_lifecycle_overhead_sec: float,
    cost_semantics: str,
) -> dict:
    return {
        "instance_content_hash": str(instance_content_hash),
        "scale": int(scale),
        "path_hash": str(path_hash),
        "branch_e2e_gold_rank_index": int(rank),
        "branch_e2e_gold_net_gain_sec": float(net_gain_sec),
        "branch_e2e_p0_control_wall_sec": float(
            p0_control_wall_sec
        ),
        "branch_guidance_lifecycle_overhead_sec": float(
            guidance_lifecycle_overhead_sec
        ),
        "branch_e2e_cost_semantics": str(cost_semantics),
        "branch_e2e_wall_sec_by_rank": {
            str(index): float(walls[str(index)])
            for index in range(3)
        },
    }


def _label_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def _gold_binding(
    *,
    path: Path,
    split_manifest: dict,
    census_actionable_hashes: set[str],
    guidance_lifecycle_overhead_sec: float = 0.02,
) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    content_hash = str(report.get("instance_content_hash") or "")
    development = {
        str(row["instance_content_hash"]): row
        for row in split_manifest.get("development") or ()
        if str(row.get("instance_generator_domain") or "")
        == REAL_MAP_SP50_DOMAIN
    }
    manifest_row = development.get(content_hash)
    states = list(report.get("state_reports") or ())
    authorized_split_hashes = {
        str(split_manifest["manifest_hash"]),
        *{
            str(value)
            for value in split_manifest.get(
                "authorized_collection_split_manifest_hashes"
            )
            or ()
        },
    }
    if (
        str(report.get("schema_version") or "")
        != E2E_SCHEMA_VERSION
        or str(report.get("split_manifest_hash") or "")
        not in authorized_split_hashes
        or manifest_row is None
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
        raise SystemExit("target E2E gold report binding mismatch")
    state = states[0]
    control = dict(report.get("control") or {})
    arms = list(state.get("arms") or ())
    top3 = list(state.get("top3_candidate_ids") or ())
    before = state.get("legal_branch_shortlist_hash_before_sort")
    after = state.get("legal_branch_shortlist_hash_after_sort")
    if (
        state.get("complete_matched_e2e_gold") is not True
        or state.get("objective_matches_across_arms") is not True
        or int(state.get("depth") or 0) != 0
        or list(state.get("path_signature") or ()) != []
        or int(state.get("candidate_count") or 0) != 3
        or len(top3) != 3
        or before != after
        or control.get("exact_safe") is not True
        or control.get("universe_safe") is not True
        or control.get("descendant_pricing_certificate_reused") is not False
        or int(control.get("requested_rank_index") or 0) != 0
        or int(control.get("target_selected_rank_index") or 0) != 0
        or list(control.get("target_top3_candidate_ids") or ()) != top3
        or control.get("target_legal_branch_shortlist_hash_before_sort")
        != before
        or control.get("target_legal_branch_shortlist_hash_after_sort")
        != after
        or len(arms) != 2
    ):
        raise SystemExit("target E2E gold safety semantics mismatch")
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
            raise SystemExit("target E2E arm safety semantics mismatch")
        by_rank[rank] = arm
    if set(by_rank) != {0, 1, 2}:
        raise SystemExit("target E2E gold lacks a matched top-3 arm")
    objectives = [float(by_rank[index]["objective"]) for index in range(3)]
    if (
        not all(isfinite(value) for value in objectives)
        or not all(
            isclose(
                value,
                objectives[0],
                rel_tol=0.0,
                abs_tol=1.0e-6,
            )
            for value in objectives
        )
    ):
        raise SystemExit("target E2E arm objectives differ")
    reported_walls = {
        str(index): float(
            by_rank[index]["matched_end_to_end_wall_sec"]
        )
        for index in range(3)
    }
    if not all(
        isfinite(value) and value > 0.0
        for value in reported_walls.values()
    ):
        raise SystemExit("target E2E walls must be finite and positive")
    report_rank = min(
        range(3),
        key=lambda index: (reported_walls[str(index)], index),
    )
    report_gain = (
        reported_walls["0"] - reported_walls[str(report_rank)]
    )
    if (
        int(state.get("oracle_selected_rank_index") or 0)
        != report_rank
        or not isclose(
            float(state.get("oracle_net_gain_sec") or 0.0),
            report_gain,
            rel_tol=0.0,
            abs_tol=1.0e-6,
        )
    ):
        raise SystemExit("target E2E oracle label is inconsistent")
    costs = canonical_guided_e2e_costs(
        arm_by_rank=by_rank,
        guidance_lifecycle_overhead_sec=float(
            guidance_lifecycle_overhead_sec
        ),
    )
    payload = _label_payload(
        instance_content_hash=content_hash,
        scale=int(manifest_row["scale"]),
        path_hash=str(state["path_hash"]),
        rank=int(costs["oracle_selected_rank_index"]),
        net_gain_sec=float(costs["oracle_net_gain_sec"]),
        walls=costs["guided_action_wall_sec_by_rank"],
        p0_control_wall_sec=float(costs["p0_control_wall_sec"]),
        guidance_lifecycle_overhead_sec=float(
            costs["guidance_lifecycle_overhead_sec"]
        ),
        cost_semantics=str(costs["cost_semantics"]),
    )
    return {
        **payload,
        "label_sha256": _label_hash(payload),
        "e2e_report_path": str(path.resolve()),
        "e2e_report_sha256": _file_sha256(path),
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
        "--minimum-target-instance-count-per-scale",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--minimum-target-gold-count-per-scale",
        type=int,
        default=2,
    )
    parser.add_argument(
        "--minimum-target-positive-gold-count",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--maximum-target-instance-count-per-scale",
        type=int,
        default=6,
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
    split = json.loads(split_path.read_text(encoding="utf-8"))
    if (
        str(split.get("schema_version") or "") != SPLIT_SCHEMA_VERSION
        or not bool((split.get("audit") or {}).get("passed"))
        or split.get("calibration_read_authorized") is not False
    ):
        raise SystemExit("target headroom split is invalid")
    required_scales = (20, 30)
    census_rows, census_bindings = _target_census_rows(
        paths=[Path(value) for value in args.target_census_report],
        split_manifest=split,
        required_scales=required_scales,
    )
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
    if len(gold_bindings) != len(
        {row["instance_content_hash"] for row in gold_bindings}
    ):
        raise SystemExit("duplicate target E2E gold instance")
    gold_by_hash = {
        str(row["instance_content_hash"]): row
        for row in gold_bindings
    }
    census_count = {
        scale: sum(int(row["scale"]) == scale for row in census_rows)
        for scale in required_scales
    }
    exact_count = {
        scale: sum(
            int(row["scale"]) == scale
            and str(row["status"])
            in {"EXACT_ACTIONABLE", "EXACT_NONACTIONABLE"}
            for row in census_rows
        )
        for scale in required_scales
    }
    actionable_count = {
        scale: sum(
            int(row["scale"]) == scale
            and str(row["status"]) == "EXACT_ACTIONABLE"
            for row in census_rows
        )
        for scale in required_scales
    }
    gold_count = {
        scale: sum(int(row["scale"]) == scale for row in gold_bindings)
        for scale in required_scales
    }
    positive_gold_count = sum(
        float(row["branch_e2e_gold_net_gain_sec"]) > 0.0
        for row in gold_bindings
    )
    missing_actionable = sorted(actionable_hashes - set(gold_by_hash))
    gains: dict[int, dict[str, list[float]]] = {}
    for row in census_rows:
        status = str(row["status"])
        content_hash = str(row["instance_content_hash"])
        if status == "EXACT_NONACTIONABLE":
            gain = 0.0
        elif status == "EXACT_ACTIONABLE" and content_hash in gold_by_hash:
            gain = (
                float(
                    gold_by_hash[content_hash][
                        "branch_e2e_gold_net_gain_sec"
                    ]
                )
            )
        else:
            continue
        gains.setdefault(int(row["scale"]), {}).setdefault(
            content_hash, []
        ).append(gain)
    observed, interval, cluster_count = _balanced_bootstrap(
        gains,
        samples=int(args.bootstrap_samples),
        seed=int(args.bootstrap_seed),
    )
    screen_threshold = all(
        census_count[scale]
        >= int(args.minimum_target_instance_count_per_scale)
        for scale in required_scales
    )
    screen_exact = bool(
        screen_threshold
        and all(
            exact_count[scale] == census_count[scale]
            for scale in required_scales
        )
    )
    # Completeness of labels for *observed actionable* states is distinct
    # from completeness of the census.  Conflating them leaves a capped
    # census with one censored instance in a permanent neither-run-nor-stop
    # state and invites unbounded label chasing.
    gold_complete = not missing_actionable
    sample_ready = bool(
        gold_complete
        and all(
            gold_count[scale]
            >= int(args.minimum_target_gold_count_per_scale)
            for scale in required_scales
        )
    )
    cap_reached = all(
        census_count[scale]
        >= int(args.maximum_target_instance_count_per_scale)
        for scale in required_scales
    )
    upper = interval[1]
    decision = _target_stop_loss_decision(
        target_sample_ready=sample_ready,
        target_screen_exact_complete=screen_exact,
        target_actionable_gold_complete=gold_complete,
        target_cap_reached=cap_reached,
        target_upper=upper,
        positive_gold_count=positive_gold_count,
        minimum_positive_gold_count=int(
            args.minimum_target_positive_gold_count
        ),
    )
    headroom_passed = bool(
        sample_ready
        and decision["positive_target_signal"]
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "split_manifest_path": str(split_path.resolve()),
        "split_manifest_hash": split["manifest_hash"],
        "target_domain": REAL_MAP_SP50_DOMAIN,
        "calibration_used": False,
        "protected_final_test_used": False,
        "census_bindings": census_bindings,
        "gold_label_bindings": gold_bindings,
        "thresholds": {
            "minimum_target_instance_count_per_scale": int(
                args.minimum_target_instance_count_per_scale
            ),
            "minimum_target_gold_count_per_scale": int(
                args.minimum_target_gold_count_per_scale
            ),
            "minimum_target_positive_gold_count": int(
                args.minimum_target_positive_gold_count
            ),
            "maximum_target_instance_count_per_scale": int(
                args.maximum_target_instance_count_per_scale
            ),
            "guidance_lifecycle_overhead_sec": float(
                args.guidance_lifecycle_overhead_sec
            ),
        },
        "observed": {
            "census_count_by_scale": {
                str(scale): census_count[scale]
                for scale in required_scales
            },
            "exact_screen_count_by_scale": {
                str(scale): exact_count[scale]
                for scale in required_scales
            },
            "actionable_count_by_scale": {
                str(scale): actionable_count[scale]
                for scale in required_scales
            },
            "gold_count_by_scale": {
                str(scale): gold_count[scale]
                for scale in required_scales
            },
            "positive_gold_count": positive_gold_count,
            "missing_actionable_instance_hashes": missing_actionable,
            "perfect_policy_net_gain_sec_mean_after_overhead": observed,
            "perfect_policy_net_gain_sec_bootstrap_95ci": interval,
            "perfect_policy_instance_cluster_count": cluster_count,
            "headroom_denominator": (
                "all_exact_precommitted_census_instances;"
                "exact_nonactionable_gain_zero"
            ),
        },
        "target_screen_threshold_reached": screen_threshold,
        "target_screen_exact_complete": screen_exact,
        "target_actionable_gold_complete": gold_complete,
        "target_sample_threshold_reached": sample_ready,
        "target_instance_cap_reached": cap_reached,
        "target_headroom_passed": headroom_passed,
        "terminate_target_direction": decision[
            "terminate_target_direction"
        ],
        "decision_reason_code": decision["decision_reason_code"],
        "matched_e2e_collection_authorized": decision[
            "matched_e2e_collection_authorized"
        ],
        "bounded_target_expansion_authorized": decision[
            "bounded_target_expansion_authorized"
        ],
        "formal_feature_aux_collection_authorized": headroom_passed,
        "linear_training_authorized": False,
        "gat_training_authorized": False,
        "deployment_authorized": False,
        "note": (
            "This gate consumes census and matched E2E summaries only. "
            "Passing authorizes feature/aux materialization, never model "
            "training or online branch guidance."
        ),
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
    return 0 if headroom_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
