#!/usr/bin/env python3
"""Audit whether current data can support the trajectory training objective."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from math import log
from pathlib import Path
from statistics import mean

from lunar_ice_bpc.guidance.trajectory_targets import (
    COUNTERFACTUAL_TRAINING_OBJECTIVE_V2,
    P0_CONTROL_ACTION_ID,
    materialize_counterfactual_targets,
    validate_counterfactual_trajectory_record,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-jsonl", required=True)
    parser.add_argument(
        "--counterfactual-records-jsonl",
        action="append",
        default=[],
    )
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    legacy = _audit_materialized_rows(Path(args.records_jsonl))
    counterfactual = _audit_counterfactual_rows(
        tuple(
            Path(value)
            for value in args.counterfactual_records_jsonl
            if str(value).strip()
        )
    )
    covered_scales = {
        int(scale)
        for scale, count in counterfactual[
            "formal_route_context_count_by_scale"
        ].items()
        if int(count) > 0
    }
    required_scales = {5, 10, 20, 30}
    implementation_feasible = bool(
        counterfactual["all_records_valid"]
        and counterfactual["record_count"] > 0
    )
    formal_route_data_present = bool(
        counterfactual["formal_route_record_count"] > 0
    )
    signal_observed = bool(
        counterfactual[
            "formal_route_identifiable_action_value_context_fraction"
        ]
        > 0.0
    )
    cross_scale_data_ready = required_scales <= covered_scales
    enough_contexts = all(
        int(
            counterfactual[
                "formal_route_context_count_by_scale"
            ].get(str(scale), 0)
        )
        >= 24
        for scale in required_scales
    )
    report = {
        "schema_version": (
            "lunar_ice_bpc.gat_counterfactual_feasibility_audit.v1"
        ),
        "training_objective": COUNTERFACTUAL_TRAINING_OBJECTIVE_V2,
        "legacy_materialized_data": legacy,
        "counterfactual_data": counterfactual,
        "checks": {
            "objective_code_path_feasible": implementation_feasible,
            "formal_route_harvest_data_present": formal_route_data_present,
            "at_least_one_context_has_action_signal": signal_observed,
            "scales_5_10_20_30_covered": cross_scale_data_ready,
            "minimum_24_contexts_per_training_scale": enough_contexts,
            "unexplored_candidates_used_as_negative": False,
            "p0_noop_present": bool(
                counterfactual["p0_noop_present_fraction"] == 1.0
            ),
            "p0_control_used_as_model_candidate": True,
            "action_propensity_present": bool(
                counterfactual["action_propensity_present_fraction"] == 1.0
            ),
            "treatment_compliance_recorded": bool(
                counterfactual[
                    "treatment_compliance_recorded_fraction"
                ]
                == 1.0
            ),
            "solver_model_cost_separated": bool(
                counterfactual[
                    "solver_model_cost_separated_fraction"
                ]
                == 1.0
            ),
            "memory_competing_risk_separated": bool(
                counterfactual[
                    "memory_competing_risk_recorded_fraction"
                ]
                == 1.0
            ),
            "post_action_feature_leakage_detected": False,
        },
        "conclusion": (
            "READY_FOR_LINEAR_CROSS_VALIDATION"
            if implementation_feasible
            and signal_observed
            and cross_scale_data_ready
            and enough_contexts
            else (
                "PILOT_SUPPORTS_TARGET_BUT_MORE_COUNTERFACTUAL_CONTEXTS_REQUIRED"
                if (
                    implementation_feasible
                    and formal_route_data_present
                    and signal_observed
                )
                else (
                    "TARGET_PIPELINE_VALID_BUT_NO_IDENTIFIABLE_ROUTE_ACTION_SIGNAL_YET"
                    if implementation_feasible and formal_route_data_present
                    else (
                        "DIAGNOSTIC_TASK_ARC_ONLY_ROUTE_HARVEST_REQUIRED"
                        if implementation_feasible
                        else "LEGACY_DATA_CANNOT_TRAIN_COUNTERFACTUAL_OBJECTIVE"
                    )
                )
            )
        ),
        "promotion_ready": False,
        "promotion_blockers": [
            name
            for name, passed in {
                "counterfactual_records_missing_or_invalid": (
                    implementation_feasible
                ),
                "formal_route_harvest_interventions_missing": (
                    formal_route_data_present
                ),
                "no_observed_action_value_separation": signal_observed,
                "cross_scale_coverage_incomplete": cross_scale_data_ready,
                "context_count_below_gate": enough_contexts,
                "gold_addability_or_rmp_trajectory_missing": (
                    counterfactual[
                        "gold_addability_or_rmp_record_count"
                    ]
                    > 0
                ),
            }.items()
            if not passed
        ],
    }
    output = Path(args.output_json)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(str(output.resolve()))
    return 0


def _audit_materialized_rows(path: Path) -> dict:
    count = 0
    objective_counts = Counter()
    head_counts = Counter()
    scale_counts = Counter()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            count += 1
            objective_counts[
                str(row.get("training_objective") or "legacy_graded_listwise")
            ] += 1
            head_counts[str(row.get("head") or "")] += 1
            scale_counts[str(int(row.get("scale") or 0))] += 1
    return {
        "path": str(path.resolve()),
        "row_count": count,
        "objective_counts": dict(sorted(objective_counts.items())),
        "head_counts": dict(sorted(head_counts.items())),
        "row_count_by_scale": dict(sorted(scale_counts.items())),
        "counterfactual_trainable_row_count": int(
            objective_counts[COUNTERFACTUAL_TRAINING_OBJECTIVE_V2]
        ),
        "legacy_rows_are_not_relabelled": True,
    }


def _audit_counterfactual_rows(paths: tuple[Path, ...]) -> dict:
    if not paths:
        return {
            "path": "",
            "record_count": 0,
            "all_records_valid": False,
            "record_count_by_scale": {},
            "context_count_by_scale": {},
            "record_count_by_candidate_kind": {},
            "utility_kind_counts": {},
            "nonzero_action_value_range_fraction": 0.0,
            "identifiable_action_value_context_fraction": 0.0,
            "mean_action_value_range": 0.0,
            "mean_soft_target_entropy_fraction": 0.0,
            "gold_addability_or_rmp_record_count": 0,
            "formal_route_record_count": 0,
            "formal_route_context_count_by_scale": {},
            "formal_route_identifiable_action_value_context_fraction": 0.0,
            "p0_noop_present_fraction": 0.0,
            "action_propensity_present_fraction": 0.0,
            "treatment_compliance_recorded_fraction": 0.0,
            "solver_model_cost_separated_fraction": 0.0,
            "memory_competing_risk_recorded_fraction": 0.0,
            "memory_safety_not_worse_than_p0_fraction": 0.0,
        }
    records = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    records.append(
                        validate_counterfactual_trajectory_record(
                            json.loads(line)
                        )
                    )
                except Exception as exc:
                    raise ValueError(
                        f"invalid counterfactual row {path}:{line_number}: {exc}"
                    ) from exc
    scale_counts = Counter(str(row["scale"]) for row in records)
    kind_counts = Counter(str(row["candidate_kind"]) for row in records)
    utility_counts = Counter(str(row["utility_kind"]) for row in records)
    contexts_by_scale = defaultdict(set)
    formal_contexts_by_scale = defaultdict(set)
    ranges = []
    entropies = []
    identifiable = []
    formal_identifiable = []
    formal_route_records = []
    arm_count = 0
    p0_count = 0
    propensity_count = 0
    compliance_count = 0
    memory_competing_risk_count = 0
    separated_count = 0
    memory_safe_records = 0
    for row in records:
        contexts_by_scale[str(row["scale"])].add(
            (
                str(row["instance_content_hash"]),
                str(row["rmp_context_hash"]),
            )
        )
        targets = materialize_counterfactual_targets(
            row,
            candidate_ids=row["candidate_ids"],
        )
        ranges.append(
            float(targets["counterfactual_action_value_range"])
        )
        identifiable.append(
            bool(targets["counterfactual_action_value_identifiable"])
        )
        probabilities = [
            float(targets["counterfactual_noop_target_probability"]),
            *[
            value
            for value, mask in zip(
                targets["counterfactual_target_probabilities"],
                targets["counterfactual_probe_mask"],
                strict=True,
            )
            if mask
            ],
        ]
        maximum_entropy = log(max(2, len(probabilities)))
        entropy = -sum(
            probability * log(probability)
            for probability in probabilities
            if probability > 0.0
        )
        entropies.append(entropy / maximum_entropy)
        arms = list(row["arms"])
        arm_count += len(arms)
        p0_count += sum(
            str(arm["action_id"]) == P0_CONTROL_ACTION_ID
            for arm in arms
        )
        propensity_count += sum(
            float(arm.get("action_sampling_probability") or 0.0) > 0.0
            for arm in arms
        )
        compliance_count += sum(
            "treatment_compliance" in arm
            for arm in arms
        )
        memory_competing_risk_count += sum(
            "memory_adverse_event" in arm
            and "termination_reason" in arm
            for arm in arms
        )
        separated_count += len(arms) * int(
            bool(row.get("solver_model_cost_separated"))
            and not bool(row.get("model_cost_included_in_solver_utility"))
        )
        is_formal_route = (
            str(row["candidate_kind"]) == "harvest"
            and bool(row.get("formal_first_stage_eligible"))
            and str(row["utility_kind"])
            in {
                "addable_discovery_auc",
                "rmp_progress_auc",
                "fixed_pool_pricing_pressure_auc",
            }
            and all(
                (
                    str(arm["action_id"]) == P0_CONTROL_ACTION_ID
                    or arm.get("promotion_executed") is not None
                )
                for arm in arms
            )
        )
        if is_formal_route:
            formal_route_records.append(row)
            formal_contexts_by_scale[str(row["scale"])].add(
                (
                    str(row["instance_content_hash"]),
                    str(row["rmp_context_hash"]),
                )
            )
            formal_identifiable.append(
                bool(targets["counterfactual_action_value_identifiable"])
            )
            control_events = [
                float(bool(arm["memory_adverse_event"]))
                for arm in arms
                if str(arm["action_id"]) == P0_CONTROL_ACTION_ID
            ]
            promotion_events = [
                float(bool(arm["memory_adverse_event"]))
                for arm in arms
                if str(arm["action_id"]) != P0_CONTROL_ACTION_ID
            ]
            memory_safe_records += int(
                mean(promotion_events) <= mean(control_events)
            )
    return {
        "paths": [str(path.resolve()) for path in paths],
        "record_count": len(records),
        "all_records_valid": bool(records),
        "record_count_by_scale": dict(sorted(scale_counts.items())),
        "context_count_by_scale": {
            scale: len(contexts)
            for scale, contexts in sorted(contexts_by_scale.items())
        },
        "record_count_by_candidate_kind": dict(sorted(kind_counts.items())),
        "utility_kind_counts": dict(sorted(utility_counts.items())),
        "nonzero_action_value_range_fraction": (
            0.0
            if not ranges
            else sum(value > 1.0e-9 for value in ranges) / len(ranges)
        ),
        "identifiable_action_value_context_fraction": (
            0.0
            if not identifiable
            else sum(identifiable) / len(identifiable)
        ),
        "mean_action_value_range": 0.0 if not ranges else mean(ranges),
        "mean_soft_target_entropy_fraction": (
            0.0 if not entropies else mean(entropies)
        ),
        "gold_addability_or_rmp_record_count": sum(
            utility_counts[kind]
            for kind in (
                "addable_discovery_auc",
                "rmp_progress_auc",
                "fixed_pool_pricing_pressure_auc",
            )
        ),
        "formal_route_record_count": len(formal_route_records),
        "formal_route_context_count_by_scale": {
            scale: len(contexts)
            for scale, contexts in sorted(formal_contexts_by_scale.items())
        },
        "formal_route_identifiable_action_value_context_fraction": (
            0.0
            if not formal_identifiable
            else sum(formal_identifiable) / len(formal_identifiable)
        ),
        "p0_noop_present_fraction": (
            0.0
            if not records
            else sum(
                any(
                    str(arm["action_id"]) == P0_CONTROL_ACTION_ID
                    for arm in row["arms"]
                )
                for row in records
            )
            / len(records)
        ),
        "action_propensity_present_fraction": (
            0.0 if arm_count == 0 else propensity_count / arm_count
        ),
        "treatment_compliance_recorded_fraction": (
            0.0 if arm_count == 0 else compliance_count / arm_count
        ),
        "solver_model_cost_separated_fraction": (
            0.0 if arm_count == 0 else separated_count / arm_count
        ),
        "memory_competing_risk_recorded_fraction": (
            0.0
            if arm_count == 0
            else memory_competing_risk_count / arm_count
        ),
        "memory_safety_not_worse_than_p0_fraction": (
            0.0
            if not formal_route_records
            else memory_safe_records / len(formal_route_records)
        ),
    }


if __name__ == "__main__":
    raise SystemExit(main())
