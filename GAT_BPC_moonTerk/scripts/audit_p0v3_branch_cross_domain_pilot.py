#!/usr/bin/env python3
"""Early-stop gate before expensive cross-domain branch-GAT collection."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
from statistics import mean
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.branch_survival import (  # noqa: E402
    REAL_MAP_SP50_DOMAIN,
    SYNTHETIC_POLAR_GRID_DOMAIN,
    validate_branch_survival_row,
)


SCHEMA_VERSION = "lunar_ice_bpc.branch_cross_domain_pilot.v1"
TRANSFER_SCHEMA_VERSION = (
    "lunar_ice_bpc.branch_cross_domain_transfer_evaluation.v1"
)
SPLIT_SCHEMA_VERSION = (
    "lunar_ice_bpc.branch_grouped_split_manifest.v2"
)
CENSUS_SCHEMA_VERSION = (
    "lunar_ice_bpc.no_task_wait_v3_branch_opportunity_census.v1"
)
TARGET_HEADROOM_SCHEMA_VERSION = (
    "lunar_ice_bpc.branch_target_headroom_gate.v1"
)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _row_sha256(row: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            row,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def _row_bindings(rows: list[dict]) -> list[dict]:
    return sorted(
        (
            {
                "instance_content_hash": str(
                    row["instance_content_hash"]
                ),
                "path_hash": str(row["path_hash"]),
                "row_sha256": _row_sha256(row),
            }
            for row in rows
        ),
        key=lambda row: (
            row["instance_content_hash"],
            row["path_hash"],
        ),
    )


def _e2e_label_payload(row: dict) -> dict:
    walls = row.get("branch_e2e_wall_sec_by_rank") or {}
    return {
        "instance_content_hash": str(row["instance_content_hash"]),
        "scale": int(row["scale"]),
        "path_hash": str(row["path_hash"]),
        "branch_e2e_gold_rank_index": int(
            row["branch_e2e_gold_rank_index"]
        ),
        "branch_e2e_gold_net_gain_sec": float(
            row["branch_e2e_gold_net_gain_sec"]
        ),
        "branch_e2e_p0_control_wall_sec": float(
            row["branch_e2e_p0_control_wall_sec"]
        ),
        "branch_guidance_lifecycle_overhead_sec": float(
            row["branch_guidance_lifecycle_overhead_sec"]
        ),
        "branch_e2e_cost_semantics": str(
            row["branch_e2e_cost_semantics"]
        ),
        "branch_e2e_wall_sec_by_rank": {
            str(index): float(walls[str(index)])
            for index in range(3)
        },
    }


def _e2e_label_hash(row: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            _e2e_label_payload(row),
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def _balanced_bootstrap(
    values: dict[int, dict[str, list[float]]],
    *,
    samples: int,
    seed: int,
) -> tuple[float | None, list[float | None], int]:
    clusters = {
        int(scale): [
            mean(rows)
            for rows in by_instance.values()
            if rows
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
    draws = []
    for _ in range(max(1, int(samples))):
        draws.append(
            mean(
                mean(generator.choice(rows) for _ in rows)
                for rows in clusters.values()
            )
        )
    draws.sort()
    lower = draws[max(0, int(0.025 * len(draws)))]
    upper = draws[
        max(0, min(len(draws) - 1, int(0.975 * len(draws)) - 1))
    ]
    return observed, [float(lower), float(upper)], sum(
        len(rows) for rows in clusters.values()
    )


def _target_census_rows(
    *,
    paths: list[Path],
    split_manifest: dict,
    required_scales: tuple[int, ...],
) -> tuple[list[dict], list[dict]]:
    target_development = {
        str(row["instance_content_hash"]): row
        for row in split_manifest.get("development") or ()
        if str(row.get("instance_generator_domain") or "")
        == REAL_MAP_SP50_DOMAIN
        and int(row["scale"]) in required_scales
    }
    rows = []
    bindings = []
    seen = set()
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
    for path in paths:
        report = json.loads(path.read_text(encoding="utf-8"))
        if (
            str(report.get("schema_version") or "")
            != CENSUS_SCHEMA_VERSION
            or str(report.get("split_manifest_hash") or "")
            not in authorized_split_hashes
            or str(report.get("instance_generator_domain") or "")
            != REAL_MAP_SP50_DOMAIN
            or int(report.get("scale") or 0) not in required_scales
            or report.get("development_only") is not True
            or report.get("training_authorized") is not False
        ):
            raise SystemExit("target opportunity census binding mismatch")
        scale = int(report["scale"])
        bindings.append(
            {
                "path": str(path.resolve()),
                "sha256": _file_sha256(path),
                "scale": scale,
            }
        )
        for row in report.get("rows") or ():
            content_hash = str(row["instance_content_hash"])
            key = (content_hash, scale)
            manifest_row = target_development.get(content_hash)
            if (
                key in seen
                or manifest_row is None
                or int(manifest_row["scale"]) != scale
            ):
                raise SystemExit(
                    "target census row is duplicate or outside development"
                )
            seen.add(key)
            status = str(row.get("status") or "")
            if status not in {
                "EXACT_ACTIONABLE",
                "EXACT_NONACTIONABLE",
                "ROOT_CENSORED",
                "TREE_CENSORED",
                "INFRASTRUCTURE_CENSORED",
            }:
                raise SystemExit("unknown target census status")
            rows.append(
                {
                    "instance_content_hash": content_hash,
                    "scale": scale,
                    "status": status,
                    "driver_wall_sec": float(
                        row.get("driver_wall_sec") or 0.0
                    ),
                }
            )
    return rows, bindings


def _target_stop_loss_decision(
    *,
    target_sample_ready: bool,
    target_screen_exact_complete: bool,
    target_actionable_gold_complete: bool,
    target_cap_reached: bool,
    target_upper: float | None,
    positive_gold_count: int,
    minimum_positive_gold_count: int,
) -> dict:
    positive_target_signal = bool(
        int(positive_gold_count) >= int(minimum_positive_gold_count)
        and target_upper is not None
        and float(target_upper) > 0.0
    )
    terminate = bool(
        target_sample_ready
        and not positive_target_signal
        or (
            target_screen_exact_complete
            and target_actionable_gold_complete
            and (
                target_upper is None
                or float(target_upper) <= 0.0
                or int(positive_gold_count) == 0
            )
        )
        or (
            target_cap_reached
            and target_actionable_gold_complete
            and not target_sample_ready
        )
    )
    if (
        target_cap_reached
        and target_actionable_gold_complete
        and not target_sample_ready
    ):
        decision_reason = (
            "TARGET_CAP_REACHED_WITH_INSUFFICIENT_EVALUABLE_GOLD"
        )
    elif terminate:
        decision_reason = "PERFECT_POLICY_NONPOSITIVE_OR_NO_POSITIVE_GOLD"
    elif (
        target_screen_exact_complete
        and target_actionable_gold_complete
        and not target_sample_ready
        and positive_target_signal
    ):
        decision_reason = "BOUNDED_TARGET_EXPANSION_ONLY"
    elif not target_actionable_gold_complete:
        decision_reason = "MATCHED_E2E_GOLD_INCOMPLETE"
    elif target_sample_ready and positive_target_signal:
        decision_reason = "TARGET_HEADROOM_ELIGIBLE"
    else:
        decision_reason = "TARGET_SCREEN_INCOMPLETE"
    return {
        "positive_target_signal": positive_target_signal,
        "decision_reason_code": decision_reason,
        "terminate_target_direction": terminate,
        "matched_e2e_collection_authorized": bool(
            not target_actionable_gold_complete
        ),
        "bounded_target_expansion_authorized": bool(
            target_screen_exact_complete
            and target_actionable_gold_complete
            and not target_sample_ready
            and not target_cap_reached
            and positive_target_signal
        ),
    }


def _transfer_decision(
    path: Path | None,
    *,
    records_sha256: str,
) -> dict:
    if path is None:
        return {
            "report_supplied": False,
            "linear_real_map_pilot_passed": False,
            "selected_training_regime": None,
            "synthetic_inclusion_authorized": False,
            "reason": "NO_TRANSFER_EVALUATION_REPORT",
        }
    report = json.loads(path.read_text(encoding="utf-8"))
    if (
        str(report.get("schema_version") or "")
        != TRANSFER_SCHEMA_VERSION
        or str(report.get("records_sha256") or "")
        != str(records_sha256)
        or report.get("calibration_used") is not False
        or report.get("protected_final_test_used") is not False
        or str(report.get("model_kind") or "") != "linear"
        or str(report.get("target_domain") or "")
        != REAL_MAP_SP50_DOMAIN
    ):
        raise SystemExit("cross-domain transfer report binding mismatch")
    target_lcb = report.get(
        "real_map_vs_p0_improvement_bootstrap_lower95"
    )
    target_ratio = report.get(
        "real_map_mean_model_to_p0_wall_ratio"
    )
    linear_passed = bool(
        target_lcb is not None
        and float(target_lcb) >= 0.0
        and target_ratio is not None
        and float(target_ratio) < 1.0
    )
    selected = (
        str(report.get("selected_training_regime") or "")
        or None
    )
    if selected not in {
        None,
        "REAL_ONLY",
        "SYNTHETIC_PRETRAIN_REAL_FINETUNE",
        "JOINT_DOMAIN_BALANCED",
    }:
        raise SystemExit("unknown cross-domain training regime")
    source_lcb = report.get(
        "selected_vs_real_only_real_map_improvement_lower95"
    )
    includes_synthetic = selected in {
        "SYNTHETIC_PRETRAIN_REAL_FINETUNE",
        "JOINT_DOMAIN_BALANCED",
    }
    synthetic_authorized = bool(
        linear_passed
        and includes_synthetic
        and source_lcb is not None
        and float(source_lcb) >= 0.0
    )
    if includes_synthetic and not synthetic_authorized:
        selected = "REAL_ONLY" if linear_passed else None
    return {
        "report_supplied": True,
        "report_path": str(path.resolve()),
        "report_sha256": _file_sha256(path),
        "linear_real_map_pilot_passed": linear_passed,
        "selected_training_regime": selected,
        "synthetic_inclusion_authorized": synthetic_authorized,
        "reason": (
            "PASS"
            if linear_passed
            else "LINEAR_REAL_MAP_HELDOUT_DID_NOT_BEAT_P0"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-jsonl", required=True)
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument("--target-headroom-report", required=True)
    parser.add_argument(
        "--target-census-report",
        action="append",
        required=True,
    )
    parser.add_argument("--output-report", required=True)
    parser.add_argument("--transfer-evaluation-report", default="")
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
        "--minimum-source-gold-count-per-scale",
        type=int,
        default=2,
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

    records_path = Path(args.records_jsonl)
    records_sha256 = _file_sha256(records_path)
    split_path = Path(args.split_manifest)
    split_manifest = json.loads(
        split_path.read_text(encoding="utf-8")
    )
    if (
        str(split_manifest.get("schema_version") or "")
        != SPLIT_SCHEMA_VERSION
        or not bool((split_manifest.get("audit") or {}).get("passed"))
        or split_manifest.get("calibration_read_authorized") is not False
    ):
        raise SystemExit("cross-domain split manifest is invalid")
    target_headroom_path = Path(args.target_headroom_report)
    target_headroom = json.loads(
        target_headroom_path.read_text(encoding="utf-8")
    )
    if (
        str(target_headroom.get("schema_version") or "")
        != TARGET_HEADROOM_SCHEMA_VERSION
        or str(target_headroom.get("split_manifest_hash") or "")
        != str(split_manifest["manifest_hash"])
        or str(target_headroom.get("target_domain") or "")
        != REAL_MAP_SP50_DOMAIN
        or target_headroom.get("calibration_used") is not False
        or target_headroom.get("protected_final_test_used") is not False
        or target_headroom.get("target_headroom_passed") is not True
        or target_headroom.get("terminate_target_direction") is not False
        or target_headroom.get(
            "formal_feature_aux_collection_authorized"
        )
        is not True
    ):
        raise SystemExit(
            "target headroom did not authorize formal row collection"
        )
    rows = [
        json.loads(line)
        for line in records_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for row in rows:
        validate_branch_survival_row(row)
        if (
            row.get("calibration_used") is not False
            or row.get("protected_final_test_used") is not False
        ):
            raise SystemExit("pilot received calibration/protected data")
        if (
            row.get("branch_e2e_gold_rank_index") is not None
            and abs(
                float(
                    row["branch_guidance_lifecycle_overhead_sec"]
                )
                - float(args.guidance_lifecycle_overhead_sec)
            )
            > 1.0e-12
        ):
            raise SystemExit(
                "pilot guidance lifecycle overhead mismatch"
            )

    required_scales = (20, 30)
    census_rows, census_bindings = _target_census_rows(
        paths=[
            Path(value) for value in args.target_census_report
        ],
        split_manifest=split_manifest,
        required_scales=required_scales,
    )
    target_census_hashes = {
        str(row["instance_content_hash"]) for row in census_rows
    }
    domains = (
        SYNTHETIC_POLAR_GRID_DOMAIN,
        REAL_MAP_SP50_DOMAIN,
    )
    instance_sets = {
        domain: {scale: set() for scale in required_scales}
        for domain in domains
    }
    gold_counts = {
        domain: {scale: 0 for scale in required_scales}
        for domain in domains
    }
    positive_counts = {domain: 0 for domain in domains}
    gains = {
        domain: {} for domain in domains
    }
    for row in rows:
        domain = str(row["instance_generator_domain"])
        scale = int(row["scale"])
        if domain not in instance_sets or scale not in required_scales:
            raise SystemExit("pilot row domain/scale is out of scope")
        instance_hash = str(row["instance_content_hash"])
        if (
            domain == REAL_MAP_SP50_DOMAIN
            and instance_hash not in target_census_hashes
        ):
            raise SystemExit(
                "real-map pilot row lacks precommitted census membership"
            )
        instance_sets[domain][scale].add(instance_hash)
        if row.get("branch_e2e_gold_rank_index") is None:
            continue
        gain = float(
            row.get("branch_e2e_gold_net_gain_sec") or 0.0
        )
        gold_counts[domain][scale] += 1
        positive_counts[domain] += int(gain > 0.0)
        gains[domain].setdefault(scale, {}).setdefault(
            instance_hash, []
        ).append(gain)

    target_gold_rows = {
        (
            str(row["instance_content_hash"]),
            str(row["path_hash"]),
        ): row
        for row in rows
        if (
            str(row["instance_generator_domain"])
            == REAL_MAP_SP50_DOMAIN
            and row.get("branch_e2e_gold_rank_index") is not None
        )
    }
    headroom_gold_bindings = list(
        target_headroom.get("gold_label_bindings") or ()
    )
    if not headroom_gold_bindings:
        raise SystemExit("target headroom has no gold label bindings")
    for binding in headroom_gold_bindings:
        key = (
            str(binding["instance_content_hash"]),
            str(binding["path_hash"]),
        )
        row = target_gold_rows.get(key)
        if (
            row is None
            or _e2e_label_hash(row)
            != str(binding.get("label_sha256") or "")
        ):
            raise SystemExit(
                "formal target row changed a headroom E2E label"
            )
    if len(target_gold_rows) != len(headroom_gold_bindings):
        raise SystemExit(
            "formal target gold set differs from headroom gate"
        )

    target_gold_gain_by_instance = {}
    for row in rows:
        if (
            str(row["instance_generator_domain"])
            != REAL_MAP_SP50_DOMAIN
            or row.get("branch_e2e_gold_rank_index") is None
        ):
            continue
        instance_hash = str(row["instance_content_hash"])
        if instance_hash in target_gold_gain_by_instance:
            raise SystemExit(
                "headroom pilot accepts one root gold state per instance"
            )
        target_gold_gain_by_instance[instance_hash] = float(
            row.get("branch_e2e_gold_net_gain_sec") or 0.0
        )

    target_census_counts = {
        scale: sum(
            int(row["scale"]) == scale for row in census_rows
        )
        for scale in required_scales
    }
    target_exact_counts = {
        scale: sum(
            int(row["scale"]) == scale
            and str(row["status"])
            in {"EXACT_ACTIONABLE", "EXACT_NONACTIONABLE"}
            for row in census_rows
        )
        for scale in required_scales
    }
    target_actionable_counts = {
        scale: sum(
            int(row["scale"]) == scale
            and str(row["status"]) == "EXACT_ACTIONABLE"
            for row in census_rows
        )
        for scale in required_scales
    }
    missing_actionable_gold = [
        row
        for row in census_rows
        if str(row["status"]) == "EXACT_ACTIONABLE"
        and str(row["instance_content_hash"])
        not in target_gold_gain_by_instance
    ]
    census_gains: dict[int, dict[str, list[float]]] = {}
    for row in census_rows:
        status = str(row["status"])
        if status == "EXACT_NONACTIONABLE":
            value = 0.0
        elif status == "EXACT_ACTIONABLE":
            instance_hash = str(row["instance_content_hash"])
            if instance_hash not in target_gold_gain_by_instance:
                continue
            value = target_gold_gain_by_instance[instance_hash]
        else:
            continue
        census_gains.setdefault(
            int(row["scale"]), {}
        ).setdefault(
            str(row["instance_content_hash"]), []
        ).append(value)

    domain_metrics = {}
    for index, domain in enumerate(domains):
        domain_gains = (
            census_gains
            if domain == REAL_MAP_SP50_DOMAIN
            else gains[domain]
        )
        observed, interval, cluster_count = _balanced_bootstrap(
            domain_gains,
            samples=int(args.bootstrap_samples),
            seed=int(args.bootstrap_seed) + index,
        )
        domain_metrics[domain] = {
            "instance_count_by_scale": {
                str(scale): len(instance_sets[domain][scale])
                for scale in required_scales
            },
            "gold_count_by_scale": {
                str(scale): gold_counts[domain][scale]
                for scale in required_scales
            },
            "positive_gold_count": positive_counts[domain],
            "perfect_policy_net_gain_sec_mean_after_overhead": observed,
            "perfect_policy_net_gain_sec_bootstrap_95ci": interval,
            "instance_cluster_count": cluster_count,
        }
    target_metric = domain_metrics[REAL_MAP_SP50_DOMAIN]
    target_metric.update(
        {
            "instance_count_by_scale": {
                str(scale): target_census_counts[scale]
                for scale in required_scales
            },
            "exact_screen_count_by_scale": {
                str(scale): target_exact_counts[scale]
                for scale in required_scales
            },
            "actionable_count_by_scale": {
                str(scale): target_actionable_counts[scale]
                for scale in required_scales
            },
            "missing_actionable_gold_count": len(
                missing_actionable_gold
            ),
            "screen_driver_wall_sec_total": sum(
                float(row["driver_wall_sec"]) for row in census_rows
            ),
            "headroom_denominator": (
                "all_exact_precommitted_census_instances;"
                "exact_nonactionable_gain_zero"
            ),
        }
    )

    target = domain_metrics[REAL_MAP_SP50_DOMAIN]
    source = domain_metrics[SYNTHETIC_POLAR_GRID_DOMAIN]
    target_screen_threshold_reached = all(
        target_census_counts[scale]
        >= int(args.minimum_target_instance_count_per_scale)
        for scale in required_scales
    )
    target_screen_exact_complete = bool(
        target_screen_threshold_reached
        and all(
            target_exact_counts[scale]
            == target_census_counts[scale]
            for scale in required_scales
        )
    )
    target_actionable_gold_complete = bool(
        not missing_actionable_gold
    )
    target_sample_ready = bool(
        target_screen_exact_complete
        and target_actionable_gold_complete
        and all(
            int(target["gold_count_by_scale"][str(scale)])
            >= int(args.minimum_target_gold_count_per_scale)
            for scale in required_scales
        )
    )
    source_sample_ready = all(
        int(source["gold_count_by_scale"][str(scale)])
        >= int(args.minimum_source_gold_count_per_scale)
        for scale in required_scales
    )
    target_upper = target[
        "perfect_policy_net_gain_sec_bootstrap_95ci"
    ][1]
    target_headroom_passed = bool(
        target_headroom.get("target_headroom_passed") is True
        and
        target_sample_ready
        and int(target["positive_gold_count"])
        >= int(args.minimum_target_positive_gold_count)
        and target_upper is not None
        and float(target_upper) > 0.0
    )
    target_cap_reached = all(
        target_census_counts[scale]
        >= int(args.maximum_target_instance_count_per_scale)
        for scale in required_scales
    )
    target_decision = _target_stop_loss_decision(
        target_sample_ready=target_sample_ready,
        target_screen_exact_complete=target_screen_exact_complete,
        target_actionable_gold_complete=(
            target_actionable_gold_complete
        ),
        target_cap_reached=target_cap_reached,
        target_upper=target_upper,
        positive_gold_count=int(target["positive_gold_count"]),
        minimum_positive_gold_count=int(
            args.minimum_target_positive_gold_count
        ),
    )
    terminate_target_direction = bool(
        target_decision["terminate_target_direction"]
    )
    matched_e2e_collection_authorized = bool(
        target_decision["matched_e2e_collection_authorized"]
    )
    bounded_target_expansion_authorized = bool(
        target_decision["bounded_target_expansion_authorized"]
    )
    transfer = _transfer_decision(
        None
        if not args.transfer_evaluation_report
        else Path(args.transfer_evaluation_report),
        records_sha256=records_sha256,
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "records_jsonl": str(records_path.resolve()),
        "records_sha256": records_sha256,
        "split_manifest_path": str(split_path.resolve()),
        "split_manifest_hash": split_manifest["manifest_hash"],
        "target_headroom_report_path": str(
            target_headroom_path.resolve()
        ),
        "target_headroom_report_sha256": _file_sha256(
            target_headroom_path
        ),
        "target_census_bindings": census_bindings,
        "pilot_row_bindings": _row_bindings(rows),
        "target_domain": REAL_MAP_SP50_DOMAIN,
        "source_domain": SYNTHETIC_POLAR_GRID_DOMAIN,
        "calibration_used": False,
        "protected_final_test_used": False,
        "domain_metrics": domain_metrics,
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
            "minimum_source_gold_count_per_scale": int(
                args.minimum_source_gold_count_per_scale
            ),
            "maximum_target_instance_count_per_scale": int(
                args.maximum_target_instance_count_per_scale
            ),
            "guidance_lifecycle_overhead_sec": float(
                args.guidance_lifecycle_overhead_sec
            ),
        },
        "target_sample_threshold_reached": target_sample_ready,
        "target_screen_threshold_reached": (
            target_screen_threshold_reached
        ),
        "target_screen_exact_complete": target_screen_exact_complete,
        "target_actionable_gold_complete": (
            target_actionable_gold_complete
        ),
        "target_instance_cap_reached": target_cap_reached,
        "source_sample_threshold_reached": source_sample_ready,
        "target_headroom_pilot_passed": target_headroom_passed,
        "terminate_target_direction": terminate_target_direction,
        "decision_reason_code": target_decision[
            "decision_reason_code"
        ],
        "matched_e2e_collection_authorized": (
            matched_e2e_collection_authorized
        ),
        "bounded_target_expansion_authorized": (
            bounded_target_expansion_authorized
        ),
        "expanded_collection_authorized": (
            bounded_target_expansion_authorized
        ),
        "linear_real_map_pilot_authorized": target_headroom_passed,
        "synthetic_transfer_pilot_authorized": bool(
            target_headroom_passed and source_sample_ready
        ),
        "linear_transfer_pilot_authorized": target_headroom_passed,
        "transfer_evaluation": transfer,
        "full_collection_authorized": bool(
            target_headroom_passed
            and transfer["linear_real_map_pilot_passed"]
        ),
        "synthetic_inclusion_authorized": bool(
            transfer["synthetic_inclusion_authorized"]
        ),
        "gat_training_authorized": False,
        "deployment_authorized": False,
        "note": (
            "GAT remains locked. Headroom first authorizes only a linear "
            "cross-domain pilot; expanded collection requires real-map "
            "held-out improvement, and synthetic rows require a nonnegative "
            "transfer lower confidence bound."
        ),
    }
    destination = Path(args.output_report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["full_collection_authorized"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
