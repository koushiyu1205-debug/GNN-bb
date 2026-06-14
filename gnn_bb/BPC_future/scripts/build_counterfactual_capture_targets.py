#!/usr/bin/env python3
"""Build exact-context capture targets from replay candidate manifests.

This diagnostic tool does not run the solver.  It converts the first recommended
counterfactual replay candidates into concrete no-certificate-effect capture
targets, so later runs can capture complete RMP/dual/cut/returned-batch payloads
for replay calibration instead of scanning logs opportunistically.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path(
    "BPC_future/results/root_cause_counterfactual_replay_candidates_20260613/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_counterfactual_capture_targets_20260613"
)

REQUIRED_CAPTURE_PAYLOAD_FIELDS = [
    "vehicle_count",
    "context_hash",
    "true_dual_hash",
    "cut_hash",
    "branch_hash",
    "forbidden_signature_hash",
    "active_hash_before",
    "pool_active_task_set_hash_before",
    "rmp_objective_before",
    "true_dual_vector",
    "cuts",
    "branch_constraints",
    "pool_journeys",
    "pool_signatures",
    "pool_task_sets",
    "returned_journeys",
    "returned_journey.trips.tasks",
    "returned_journey.trips.start_time",
    "returned_journey.trips.end_time",
    "returned_journey.trips.arc_option_ids",
    "returned_journey.trips.occupancy",
]

CAPTURE_CONFIG_REQUIREMENTS = {
    "journey_counterfactual_replay_capture_enabled": True,
    "journey_counterfactual_replay_capture_no_certificate_effect": True,
    "journey_counterfactual_replay_capture_require_complete_pool": True,
    "journey_counterfactual_replay_capture_require_complete_returned_batch": True,
    "journey_counterfactual_replay_capture_forbidden_signatures_enabled": True,
    "journey_counterfactual_replay_capture_forbidden_signature_max_count": 0,
}


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _context_from_key(context_key: list[Any]) -> dict[str, Any]:
    padded = [str(item) for item in context_key] + [""] * 5
    return {
        "instance": padded[0],
        "cg_iter": _as_int(padded[1]),
        "pricing_kind": padded[2],
        "active_hash_before": padded[3],
        "rmp_objective_before": _as_float(padded[4]),
        "raw_context_key": [str(item) for item in context_key],
    }


def _descriptor_capture_target(group: dict[str, Any], label: str) -> dict[str, Any]:
    descriptor = dict(group.get("descriptor") or {})
    samples = list(group.get("samples") or [])
    return {
        "label": label,
        "support_rows": _as_int(group.get("rows")),
        "label_counts": group.get("label_counts", {}),
        "profile_counts": group.get("profile_counts", {}),
        "dataset_counts": group.get("dataset_counts", {}),
        "expected_returned_count": _as_int(descriptor.get("returned_count")),
        "expected_materialized_count": _as_int(descriptor.get("materialized_count")),
        "expected_selected_count": _as_int(descriptor.get("selected_count")),
        "expected_best_rc": descriptor.get("best_rc", ""),
        "expected_returned_task_sets": descriptor.get("returned_task_sets", ""),
        "expected_returned_sequences": descriptor.get("returned_sequences", ""),
        "expected_returned_arc_families": descriptor.get("returned_arc_families", ""),
        "example_source_rows": samples[:3],
    }


def _target_from_candidate(candidate: dict[str, Any], index: int) -> dict[str, Any]:
    context = _context_from_key(list(candidate.get("context_key") or []))
    improved = _descriptor_capture_target(candidate["improved_descriptor"], "improved")
    worsened = _descriptor_capture_target(candidate["worsened_descriptor"], "worsened")
    return {
        "target_id": f"capture_target_{index:03d}",
        "candidate_id": candidate["candidate_id"],
        "candidate_risk": candidate["candidate_risk"],
        "replay_priority_score": candidate["replay_priority_score"],
        "context": context,
        "context_label_counts": candidate.get("context_label_counts", {}),
        "context_mixed_descriptor_count": _as_int(
            candidate.get("context_mixed_descriptor_count")
        ),
        "descriptors_to_capture": [improved, worsened],
        "exact_context_match_requirements": {
            "instance": context["instance"],
            "cg_iter": context["cg_iter"],
            "pricing_kind": context["pricing_kind"],
            "active_hash_before": context["active_hash_before"],
            "rmp_objective_before": context["rmp_objective_before"],
        },
        "capture_contract": {
            "diagnostic_only": True,
            "replay_no_certificate_effect": True,
            "certificate_capable": False,
            "official_bound_effect": False,
            "must_not_change_solver_path": True,
            "required_payload_fields": REQUIRED_CAPTURE_PAYLOAD_FIELDS,
            "config_requirements": CAPTURE_CONFIG_REQUIREMENTS,
        },
        "ready_for_replay_now": False,
        "not_ready_reason": "observational_candidate_needs_exact_context_capture",
    }


def build_targets(input_path: Path, top_n: int | None = None) -> dict[str, Any]:
    summary = json.loads(input_path.read_text(encoding="utf-8"))
    recommended_ids = list(summary.get("recommended_candidate_ids") or [])
    candidates = [
        candidate
        for candidate in list(summary.get("candidates") or [])
        if candidate.get("candidate_id") in recommended_ids
    ]
    order = {candidate_id: index for index, candidate_id in enumerate(recommended_ids)}
    candidates.sort(key=lambda item: order.get(item.get("candidate_id"), 10**9))
    if top_n is not None:
        candidates = candidates[: max(0, top_n)]
    targets = [
        _target_from_candidate(candidate, index)
        for index, candidate in enumerate(candidates, start=1)
    ]
    contexts = {
        "|".join(target["context"]["raw_context_key"])
        for target in targets
        if target["context"]["raw_context_key"]
    }
    low_noise_targets = [
        target for target in targets if target["candidate_risk"] == "low_context_noise"
    ]
    mixed_targets = [
        target
        for target in targets
        if target["candidate_risk"] == "mixed_descriptor_context"
    ]
    checks = {
        "has_capture_targets": bool(targets),
        "targets_match_recommended_candidates": [
            target["candidate_id"] for target in targets
        ]
        == recommended_ids[: len(targets)],
        "has_two_low_context_noise_targets": len(low_noise_targets) == 2,
        "has_one_mixed_context_stress_target": len(mixed_targets) == 1,
        "all_targets_are_diagnostic_only": all(
            target["capture_contract"]["diagnostic_only"] for target in targets
        ),
        "all_targets_require_no_certificate_effect": all(
            target["capture_contract"]["replay_no_certificate_effect"]
            and not target["capture_contract"]["certificate_capable"]
            and not target["capture_contract"]["official_bound_effect"]
            for target in targets
        ),
        "all_targets_require_complete_payload": all(
            bool(target["capture_contract"]["required_payload_fields"])
            for target in targets
        ),
        "targets_are_not_replay_ready_without_capture": all(
            not target["ready_for_replay_now"] for target in targets
        ),
    }
    return {
        "input": str(input_path),
        "target_count": len(targets),
        "candidate_ids": [target["candidate_id"] for target in targets],
        "exact_context_count": len(contexts),
        "low_context_noise_target_count": len(low_noise_targets),
        "mixed_descriptor_context_target_count": len(mixed_targets),
        "required_payload_fields": REQUIRED_CAPTURE_PAYLOAD_FIELDS,
        "capture_config_requirements": CAPTURE_CONFIG_REQUIREMENTS,
        "targets": targets,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
    }


def _write_targets_csv(path: Path, targets: list[dict[str, Any]]) -> None:
    fieldnames = [
        "target_id",
        "candidate_id",
        "candidate_risk",
        "instance",
        "cg_iter",
        "pricing_kind",
        "active_hash_before",
        "rmp_objective_before",
        "improved_returned_count",
        "worsened_returned_count",
        "improved_task_sets",
        "worsened_task_sets",
        "not_ready_reason",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for target in targets:
            improved, worsened = target["descriptors_to_capture"]
            context = target["context"]
            writer.writerow(
                {
                    "target_id": target["target_id"],
                    "candidate_id": target["candidate_id"],
                    "candidate_risk": target["candidate_risk"],
                    "instance": context["instance"],
                    "cg_iter": context["cg_iter"],
                    "pricing_kind": context["pricing_kind"],
                    "active_hash_before": context["active_hash_before"],
                    "rmp_objective_before": context["rmp_objective_before"],
                    "improved_returned_count": improved["expected_returned_count"],
                    "worsened_returned_count": worsened["expected_returned_count"],
                    "improved_task_sets": improved["expected_returned_task_sets"],
                    "worsened_task_sets": worsened["expected_returned_task_sets"],
                    "not_ready_reason": target["not_ready_reason"],
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--top-n", type=int, default=None)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = build_targets(args.input, args.top_n)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    _write_targets_csv(args.output_dir / "targets.csv", summary["targets"])
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
