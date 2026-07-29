#!/usr/bin/env python3
"""Fail-closed sample and oracle-headroom gate for branch GAT training."""

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
    BRANCH_NODE_FEATURE_SCHEMA_V2,
    REAL_MAP_SP50_DOMAIN,
    validate_branch_survival_row,
)


SCHEMA_VERSION = "lunar_ice_bpc.branch_training_readiness.v1"


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


def _bootstrap_mean_interval(
    values: list[float],
    *,
    samples: int,
    seed: int,
    alpha: float = 0.05,
) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    generator = random.Random(int(seed))
    draws = sorted(
        mean(generator.choice(values) for _ in values)
        for _ in range(max(1, int(samples)))
    )
    lower_index = max(
        0,
        min(len(draws) - 1, int((alpha / 2.0) * len(draws))),
    )
    upper_index = max(
        0,
        min(
            len(draws) - 1,
            int((1.0 - alpha / 2.0) * len(draws)) - 1,
        ),
    )
    return float(draws[lower_index]), float(draws[upper_index])


def _balanced_instance_values(
    values: dict[int, dict[str, list[float]]],
) -> tuple[float | None, dict[int, list[float]]]:
    clusters = {
        int(scale): [
            mean(instance_values)
            for instance_values in by_instance.values()
            if instance_values
        ]
        for scale, by_instance in values.items()
    }
    clusters = {
        scale: rows for scale, rows in clusters.items() if rows
    }
    return (
        None
        if not clusters
        else mean(mean(rows) for rows in clusters.values()),
        clusters,
    )


def _bootstrap_balanced_instance_interval(
    values: dict[int, dict[str, list[float]]],
    *,
    samples: int,
    seed: int,
    alpha: float = 0.05,
) -> tuple[float | None, float | None, int]:
    _, clusters = _balanced_instance_values(values)
    if not clusters:
        return None, None, 0
    generator = random.Random(int(seed))
    draws = []
    for _ in range(max(1, int(samples))):
        scale_means = []
        for rows in clusters.values():
            scale_means.append(
                mean(generator.choice(rows) for _ in rows)
            )
        draws.append(mean(scale_means))
    draws.sort()
    lower_index = max(
        0,
        min(len(draws) - 1, int((alpha / 2.0) * len(draws))),
    )
    upper_index = max(
        0,
        min(
            len(draws) - 1,
            int((1.0 - alpha / 2.0) * len(draws)) - 1,
        ),
    )
    return (
        float(draws[lower_index]),
        float(draws[upper_index]),
        sum(len(rows) for rows in clusters.values()),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-jsonl", required=True)
    parser.add_argument("--output-report", required=True)
    parser.add_argument("--cross-domain-pilot-report", default="")
    parser.add_argument("--minimum-state-count", type=int, default=20)
    parser.add_argument(
        "--minimum-instance-count-per-scale",
        type=int,
        default=10,
    )
    parser.add_argument("--minimum-gold-count", type=int, default=10)
    parser.add_argument(
        "--minimum-gold-count-per-scale",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--minimum-survival-event-count",
        type=int,
        default=12,
    )
    parser.add_argument(
        "--minimum-positive-gold-count",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--minimum-target-instance-count-per-scale",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--minimum-target-gold-count-per-scale",
        type=int,
        default=3,
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
    required_scales = (20, 30)
    rows = [
        json.loads(line)
        for line in records_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for row in rows:
        validate_branch_survival_row(row)
        if str(row.get("branch_node_feature_schema") or "") != (
            BRANCH_NODE_FEATURE_SCHEMA_V2
        ):
            raise SystemExit(
                "branch readiness feature schema mismatch"
            )
        if (
            row.get("calibration_used") is not False
            or row.get("protected_final_test_used") is not False
        ):
            raise SystemExit(
                "branch readiness received protected partition data"
            )
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
                "branch readiness lifecycle overhead mismatch"
            )
    pilot = None
    if args.cross_domain_pilot_report:
        pilot_path = Path(args.cross_domain_pilot_report)
        pilot = json.loads(pilot_path.read_text(encoding="utf-8"))
        if (
            str(pilot.get("schema_version") or "")
            != "lunar_ice_bpc.branch_cross_domain_pilot.v1"
            or pilot.get("calibration_used") is not False
            or pilot.get("protected_final_test_used") is not False
            or str(pilot.get("target_domain") or "")
            != REAL_MAP_SP50_DOMAIN
        ):
            raise SystemExit("cross-domain pilot report binding mismatch")
        current_rows = {
            (
                str(row["instance_content_hash"]),
                str(row["path_hash"]),
            ): _row_sha256(row)
            for row in rows
        }
        pilot_bindings = list(pilot.get("pilot_row_bindings") or ())
        if not pilot_bindings:
            raise SystemExit(
                "cross-domain pilot has no immutable row bindings"
            )
        for binding in pilot_bindings:
            key = (
                str(binding["instance_content_hash"]),
                str(binding["path_hash"]),
            )
            if current_rows.get(key) != str(binding["row_sha256"]):
                raise SystemExit(
                    "cross-domain pilot rows are missing or changed"
                )
    pilot_transfer = (
        {} if pilot is None else dict(
            pilot.get("transfer_evaluation") or {}
        )
    )
    selected_training_regime = (
        None
        if pilot is None
        else pilot_transfer.get("selected_training_regime")
    )
    pilot_passed = bool(
        pilot is not None
        and pilot.get("terminate_target_direction") is False
        and pilot.get("target_headroom_pilot_passed") is True
        and pilot.get("full_collection_authorized") is True
        and pilot_transfer.get("linear_real_map_pilot_passed") is True
        and selected_training_regime in {
            "REAL_ONLY",
            "SYNTHETIC_PRETRAIN_REAL_FINETUNE",
            "JOINT_DOMAIN_BALANCED",
        }
        and (
            selected_training_regime == "REAL_ONLY"
            or pilot.get("synthetic_inclusion_authorized") is True
        )
    )
    instance_by_scale: dict[int, set[str]] = {}
    target_instance_by_scale: dict[int, set[str]] = {}
    state_keys = set()
    event_count = 0
    observed_count = 0
    gold_rows = []
    trusted_pairwise_state_count = 0
    trusted_pairwise_comparison_count = 0
    for row in rows:
        scale = int(row["scale"])
        instance_hash = str(row["instance_content_hash"])
        instance_by_scale.setdefault(scale, set()).add(instance_hash)
        if str(row["instance_generator_domain"]) == REAL_MAP_SP50_DOMAIN:
            target_instance_by_scale.setdefault(
                scale, set()
            ).add(instance_hash)
        state_key = (
            instance_hash,
            str(row["path_hash"]),
        )
        if state_key in state_keys:
            raise SystemExit(f"duplicate independent state {state_key}")
        state_keys.add(state_key)
        for events, masks in zip(
            row["branch_child_event_observed"],
            row["branch_child_observed_mask"],
            strict=True,
        ):
            event_count += sum(
                bool(event) and bool(mask)
                for event, mask in zip(events, masks, strict=True)
            )
            observed_count += sum(bool(mask) for mask in masks)
        if row.get("branch_e2e_gold_rank_index") is not None:
            gold_rows.append(row)
        preferences = list(
            row.get("branch_e2e_trusted_pairwise_preferences") or ()
        )
        if preferences:
            trusted_pairwise_state_count += 1
            trusted_pairwise_comparison_count += len(preferences)
    gold_winners = [
        int(row["branch_e2e_gold_rank_index"]) for row in gold_rows
    ]
    gold_count_by_scale = {
        scale: sum(int(row["scale"]) == scale for row in gold_rows)
        for scale in required_scales
    }
    target_gold_count_by_scale = {
        scale: sum(
            int(row["scale"]) == scale
            and str(row["instance_generator_domain"])
            == REAL_MAP_SP50_DOMAIN
            for row in gold_rows
        )
        for scale in required_scales
    }
    net_gains = []
    net_gains_by_scale_instance: dict[
        int, dict[str, list[float]]
    ] = {}
    for row in gold_rows:
        value = float(
            row.get("branch_e2e_gold_net_gain_sec") or 0.0
        )
        net_gains.append(value)
        net_gains_by_scale_instance.setdefault(
            int(row["scale"]),
            {},
        ).setdefault(
            str(row["instance_content_hash"]),
            [],
        ).append(value)
    balanced_net_gain_mean, _ = _balanced_instance_values(
        net_gains_by_scale_instance
    )
    lower, upper, bootstrap_cluster_count = (
        _bootstrap_balanced_instance_interval(
            net_gains_by_scale_instance,
            samples=int(args.bootstrap_samples),
            seed=int(args.bootstrap_seed),
        )
    )
    checks = {
        "state_count": len(state_keys) >= int(args.minimum_state_count),
        "instance_count_per_scale": all(
            len(instance_by_scale.get(scale, set()))
            >= int(args.minimum_instance_count_per_scale)
            for scale in required_scales
        ),
        "gold_count": len(gold_rows) >= int(args.minimum_gold_count),
        "gold_count_per_scale": all(
            gold_count_by_scale[scale]
            >= int(args.minimum_gold_count_per_scale)
            for scale in required_scales
        ),
        "survival_event_count": event_count
        >= int(args.minimum_survival_event_count),
        "positive_gold_count": sum(value > 0.0 for value in net_gains)
        >= int(args.minimum_positive_gold_count),
        "target_instance_count_per_scale": all(
            len(target_instance_by_scale.get(scale, set()))
            >= int(args.minimum_target_instance_count_per_scale)
            for scale in required_scales
        ),
        "target_gold_count_per_scale": all(
            target_gold_count_by_scale[scale]
            >= int(args.minimum_target_gold_count_per_scale)
            for scale in required_scales
        ),
        "cross_domain_linear_pilot_passed": pilot_passed,
        "winner_diversity": (
            0 in gold_winners
            and any(value > 0 for value in gold_winners)
        ),
        "perfect_policy_net_gain_upper_bound_positive": (
            upper is not None and upper > 0.0
        ),
        "all_children_observed": observed_count == 6 * len(rows),
        "scale_scope_exact": set(instance_by_scale).issubset(
            set(required_scales)
        ),
    }
    sample_threshold_reached = all(
        checks[key]
        for key in (
            "state_count",
            "instance_count_per_scale",
            "gold_count",
            "gold_count_per_scale",
            "survival_event_count",
            "all_children_observed",
            "scale_scope_exact",
            "target_instance_count_per_scale",
            "target_gold_count_per_scale",
        )
    )
    terminate_direction = bool(
        (
            pilot is not None
            and pilot.get("terminate_target_direction") is True
        )
        or (
            sample_threshold_reached
            and not checks[
                "perfect_policy_net_gain_upper_bound_positive"
            ]
        )
    )
    passed = bool(all(checks.values()))
    report = {
        "schema_version": SCHEMA_VERSION,
        "records_jsonl": str(records_path.resolve()),
        "records_sha256": _file_sha256(records_path),
        "training_authorized": passed,
        "deployment_authorized": False,
        "terminate_branch_ranking_direction": terminate_direction,
        "sample_threshold_reached": sample_threshold_reached,
        "checks": checks,
        "thresholds": {
            "minimum_state_count": int(args.minimum_state_count),
            "minimum_instance_count_per_scale": int(
                args.minimum_instance_count_per_scale
            ),
            "minimum_gold_count": int(args.minimum_gold_count),
            "minimum_gold_count_per_scale": int(
                args.minimum_gold_count_per_scale
            ),
            "minimum_survival_event_count": int(
                args.minimum_survival_event_count
            ),
            "minimum_positive_gold_count": int(
                args.minimum_positive_gold_count
            ),
            "minimum_target_instance_count_per_scale": int(
                args.minimum_target_instance_count_per_scale
            ),
            "minimum_target_gold_count_per_scale": int(
                args.minimum_target_gold_count_per_scale
            ),
            "guidance_lifecycle_overhead_sec": float(
                args.guidance_lifecycle_overhead_sec
            ),
        },
        "observed": {
            "state_count": len(state_keys),
            "instance_count_by_scale": {
                str(scale): len(values)
                for scale, values in sorted(instance_by_scale.items())
            },
            "target_instance_count_by_scale": {
                str(scale): len(values)
                for scale, values in sorted(
                    target_instance_by_scale.items()
                )
            },
            "survival_observation_count": observed_count,
            "survival_event_count": event_count,
            "gold_count": len(gold_rows),
            "trusted_censored_pairwise_state_count": (
                trusted_pairwise_state_count
            ),
            "trusted_censored_pairwise_comparison_count": (
                trusted_pairwise_comparison_count
            ),
            "gold_count_by_scale": {
                str(scale): count
                for scale, count in sorted(
                    gold_count_by_scale.items()
                )
            },
            "target_gold_count_by_scale": {
                str(scale): count
                for scale, count in sorted(
                    target_gold_count_by_scale.items()
                )
            },
            "positive_gold_count": sum(
                value > 0.0 for value in net_gains
            ),
            "gold_winner_count_by_rank": {
                str(rank): gold_winners.count(rank) for rank in (0, 1, 2)
            },
            "perfect_policy_net_gain_sec_mean_after_overhead": (
                balanced_net_gain_mean
            ),
            "perfect_policy_net_gain_sec_bootstrap_95ci": [
                lower,
                upper,
            ],
            "perfect_policy_bootstrap_weighting": (
                "scale_equal_instance_cluster_equal_state_mean"
            ),
            "perfect_policy_bootstrap_instance_cluster_count": (
                bootstrap_cluster_count
            ),
        },
        "note": (
            "The oracle upper-bound check is only a direction viability "
            "screen. Passing it authorizes shadow training, never online "
            "branch changes or an exactness claim."
        ),
        "cross_domain_pilot": {
            "report_supplied": pilot is not None,
            "report_path": (
                None
                if pilot is None
                else str(
                    Path(
                        args.cross_domain_pilot_report
                    ).resolve()
                )
            ),
            "report_sha256": (
                None
                if pilot is None
                else _file_sha256(
                    Path(args.cross_domain_pilot_report)
                )
            ),
            "passed": pilot_passed,
            "split_manifest_hash": (
                None
                if pilot is None
                else pilot.get("split_manifest_hash")
            ),
            "selected_training_regime": selected_training_regime,
            "synthetic_inclusion_authorized": bool(
                pilot is not None
                and pilot.get(
                    "synthetic_inclusion_authorized"
                )
                is True
            ),
        },
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
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
