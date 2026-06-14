#!/usr/bin/env python3
"""Build no-certificate-effect replay case manifests from capture logs.

This is an offline diagnostic tool.  It reads
``journey_counterfactual_replay_capture`` JSONL events and converts complete
returned-batch captures into replay case descriptions.  It does not run the
solver, add columns, or change any certificate/lower-bound behavior.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from BPC_future.scripts.audit_counterfactual_replay_capture import (
    EVENT_NAME,
    _event_issues,
    _iter_jsonl_paths,
    _read_jsonl,
)


def _task_key(value: Any) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple, set, frozenset)):
        return tuple()
    return tuple(sorted(int(task) for task in value))


def _signature_key(value: Any) -> str:
    return repr(value)


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _iter_capture_events(paths: Iterable[Path]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in _iter_jsonl_paths(paths):
        for record in _read_jsonl(path):
            if record.get("event") != EVENT_NAME:
                continue
            event = dict(record)
            event["_source_file"] = str(path)
            events.append(event)
    return events


def _pool_cost_by_task_set(pool_journeys: list[dict[str, Any]]) -> dict[tuple[int, ...], float]:
    best: dict[tuple[int, ...], float] = {}
    for journey in pool_journeys:
        task_key = _task_key(journey.get("task_set"))
        if not task_key:
            continue
        cost = _as_float(journey.get("cost"))
        if task_key not in best or cost < best[task_key]:
            best[task_key] = cost
    return best


def _journey_candidate_record(
    journey: dict[str, Any],
    index: int,
    *,
    pool_task_sets: set[tuple[int, ...]],
    pool_signatures: set[str],
    forbidden_signatures: set[str],
    pool_costs: dict[tuple[int, ...], float],
    active_task_sets: set[tuple[int, ...]],
) -> dict[str, Any]:
    task_key = _task_key(journey.get("task_set"))
    signature_key = _signature_key(journey.get("signature"))
    existing_task_set = task_key in pool_task_sets
    duplicate_signature = signature_key in pool_signatures
    forbidden_signature = signature_key in forbidden_signatures
    journey_cost = _as_float(journey.get("cost"))
    incumbent_cost = pool_costs.get(task_key)
    strict_replacement = bool(
        existing_task_set
        and incumbent_cost is not None
        and journey_cost < float(incumbent_cost) - 1.0e-9
    )
    replacement_uncertain = bool(existing_task_set and incumbent_cost is None and not duplicate_signature)
    new_task_set = not existing_task_set
    active_support_changing = bool((new_task_set or strict_replacement) and task_key in active_task_sets)
    weak_replacement_or_duplicate = bool(
        existing_task_set
        and not strict_replacement
        and not active_support_changing
    )
    return {
        "candidate_id": f"journey_{index:04d}",
        "journey_index": int(index),
        "task_set": list(task_key),
        "signature": journey.get("signature"),
        "sequence": journey.get("sequence"),
        "true_reduced_cost": journey.get("true_reduced_cost"),
        "cost": journey.get("cost"),
        "existing_task_set": existing_task_set,
        "new_task_set": new_task_set,
        "duplicate_signature": duplicate_signature,
        "forbidden_signature": forbidden_signature,
        "strict_replacement_by_cost": strict_replacement,
        "replacement_uncertain_without_pool_cost": replacement_uncertain,
        "active_support_changing": active_support_changing,
        "weak_replacement_or_duplicate": weak_replacement_or_duplicate,
        "pool_incumbent_cost": None if incumbent_cost is None else round(float(incumbent_cost), 9),
        "trip_count": len(journey.get("trips", []) or []),
    }


def _treatments(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    treatments: list[dict[str, Any]] = [
        {
            "treatment_id": "control_no_addition",
            "description": "Replay current context without adding returned journeys.",
            "candidate_ids": [],
        },
        {
            "treatment_id": "full_returned_batch",
            "description": "Replay by adding the full captured returned batch.",
            "candidate_ids": [item["candidate_id"] for item in candidates],
        },
    ]
    for candidate in candidates:
        treatments.append(
            {
                "treatment_id": f"single_{candidate['candidate_id']}",
                "description": "Replay by adding exactly one captured returned journey.",
                "candidate_ids": [candidate["candidate_id"]],
            }
        )
    new_candidates = [item["candidate_id"] for item in candidates if item["new_task_set"]]
    support_candidates = [
        item["candidate_id"] for item in candidates if item["active_support_changing"]
    ]
    nonduplicate_candidates = [
        item["candidate_id"] for item in candidates if not item["duplicate_signature"]
    ]
    if new_candidates:
        treatments.append(
            {
                "treatment_id": "new_task_sets_only",
                "description": "Replay by adding captured journeys with task sets absent from the pool.",
                "candidate_ids": new_candidates,
            }
        )
    if support_candidates:
        treatments.append(
            {
                "treatment_id": "active_support_changing_only",
                "description": "Replay by adding captured journeys that change active-support task sets.",
                "candidate_ids": support_candidates,
            }
        )
    if nonduplicate_candidates:
        treatments.append(
            {
                "treatment_id": "nonduplicate_signatures_only",
                "description": "Replay by adding captured journeys whose signatures are not already in the pool.",
                "candidate_ids": nonduplicate_candidates,
            }
        )
    return treatments


def _case_from_event(event: dict[str, Any], index: int) -> dict[str, Any]:
    issues = _event_issues(event)
    vehicle_count = event.get("vehicle_count")
    if vehicle_count is None:
        issues.append("missing_vehicle_count_for_replay")
    elif _as_float(vehicle_count) <= 0.0:
        issues.append("invalid_vehicle_count_for_replay")
    pool_journeys = list(event.get("pool_journeys") or [])
    returned_journeys = list(event.get("returned_journeys") or [])
    active_basis_rows = list(event.get("active_basis_rows") or [])
    pool_task_sets = {_task_key(task_set) for task_set in event.get("pool_task_sets", []) or []}
    active_task_sets = {_task_key(task_set) for task_set in event.get("active_task_sets", []) or []}
    pool_signatures = {_signature_key(signature) for signature in event.get("pool_signatures", []) or []}
    forbidden_signatures = {
        _signature_key(signature)
        for signature in (
            event.get("forbidden_signatures")
            or event.get("forbidden_journey_signatures")
            or []
        )
    }
    pool_costs = _pool_cost_by_task_set(pool_journeys)
    candidates = [
        _journey_candidate_record(
            journey,
            journey_index,
            pool_task_sets=pool_task_sets,
            pool_signatures=pool_signatures,
            forbidden_signatures=forbidden_signatures,
            pool_costs=pool_costs,
            active_task_sets=active_task_sets,
        )
        for journey_index, journey in enumerate(returned_journeys)
    ]
    complete_returned_batch = bool(event.get("returned_batch_complete")) and not bool(
        event.get("returned_batch_truncated")
    )
    complete_pool_payload = bool(
        not event.get("pool_snapshot_truncated")
        and int(event.get("pool_journey_count") or 0) == int(event.get("pool_journey_payload_count") or 0)
        and len(pool_journeys) == int(event.get("pool_journey_count") or 0)
    )
    ready_for_rmp_replay = bool(
        not issues
        and complete_returned_batch
        and complete_pool_payload
        and returned_journeys
        and pool_journeys
        and event.get("diagnostic_only") is True
        and event.get("replay_no_certificate_effect") is True
        and event.get("certificate_capable") is False
        and event.get("official_bound_effect") is False
    )
    return {
        "case_id": f"capture_case_{index:04d}",
        "source_file": event.get("_source_file", ""),
        "instance": event.get("instance", ""),
        "instance_path": event.get("instance_path", ""),
        "task_count": event.get("task_count"),
        "vehicle_count": vehicle_count,
        "cg_iter": event.get("cg_iter"),
        "pricing_kind": event.get("pricing_kind"),
        "pricing_state": event.get("pricing_state"),
        "pricing_reason": event.get("pricing_reason"),
        "pricing_time_bucket_size": event.get("pricing_time_bucket_size"),
        "rmp_objective_before": event.get("rmp_objective_before"),
        "active_hash_before": event.get("active_hash_before"),
        "pool_active_task_set_hash_before": event.get("pool_active_task_set_hash_before"),
        "context_hash": event.get("context_hash", ""),
        "true_dual_hash": event.get("true_dual_hash", ""),
        "cut_hash": event.get("cut_hash", ""),
        "branch_hash": event.get("branch_hash", ""),
        "forbidden_signature_hash": event.get("forbidden_signature_hash", ""),
        "forbidden_signature_count": event.get("forbidden_signature_count"),
        "forbidden_signature_payload_count": event.get(
            "forbidden_signature_payload_count"
        ),
        "forbidden_signature_payload_limit": event.get(
            "forbidden_signature_payload_limit"
        ),
        "forbidden_signature_payload_complete": (
            event.get("forbidden_signature_payload_complete") is True
        ),
        "forbidden_signature_payload_truncated": (
            event.get("forbidden_signature_payload_truncated") is True
        ),
        "returned_journey_count": event.get("returned_journey_count"),
        "captured_journey_count": event.get("captured_journey_count"),
        "pool_journey_count": event.get("pool_journey_count"),
        "pool_journey_payload_count": event.get("pool_journey_payload_count"),
        "active_basis_snapshot_enabled": event.get("active_basis_snapshot_enabled") is True,
        "active_basis_snapshot_schema_version": event.get("active_basis_snapshot_schema_version"),
        "active_basis_journey_count": event.get("active_basis_journey_count"),
        "active_basis_payload_count": event.get("active_basis_payload_count"),
        "active_basis_snapshot_hash": event.get("active_basis_snapshot_hash"),
        "active_basis_snapshot_complete": event.get("active_basis_snapshot_complete") is True,
        "active_basis_snapshot_truncated": event.get("active_basis_snapshot_truncated") is True,
        "active_basis_snapshot_limit": event.get("active_basis_snapshot_limit"),
        "active_basis_lambda_sum": event.get("active_basis_lambda_sum"),
        "active_basis_fractional_journey_count": event.get("active_basis_fractional_journey_count"),
        "complete_returned_batch": complete_returned_batch,
        "complete_pool_payload": complete_pool_payload,
        "ready_for_rmp_replay": ready_for_rmp_replay,
        "diagnostic_only": event.get("diagnostic_only") is True,
        "replay_no_certificate_effect": event.get("replay_no_certificate_effect") is True,
        "issues": issues,
        "candidate_summary": {
            "candidate_count": len(candidates),
            "new_task_set_count": sum(int(item["new_task_set"]) for item in candidates),
            "duplicate_signature_count": sum(int(item["duplicate_signature"]) for item in candidates),
            "forbidden_signature_count": sum(int(item["forbidden_signature"]) for item in candidates),
            "strict_replacement_by_cost_count": sum(
                int(item["strict_replacement_by_cost"]) for item in candidates
            ),
            "replacement_uncertain_without_pool_cost_count": sum(
                int(item["replacement_uncertain_without_pool_cost"]) for item in candidates
            ),
            "active_support_changing_count": sum(
                int(item["active_support_changing"]) for item in candidates
            ),
            "weak_replacement_or_duplicate_count": sum(
                int(item["weak_replacement_or_duplicate"]) for item in candidates
            ),
        },
        "true_dual_vector": event.get("true_dual_vector", []),
        "cuts": event.get("cuts", []),
        "branch_constraints": event.get("branch_constraints", []),
        "candidates": candidates,
        "pool_journeys": pool_journeys,
        "pool_task_sets": event.get("pool_task_sets", []),
        "pool_signatures": event.get("pool_signatures", []),
        "forbidden_signatures": event.get("forbidden_signatures", []),
        "forbidden_journey_signatures": event.get("forbidden_journey_signatures", []),
        "active_basis_task_sets": event.get("active_basis_task_sets", []),
        "active_basis_rows": active_basis_rows,
        "returned_journeys": returned_journeys,
        "treatments": _treatments(candidates),
        "replay_contract": {
            "no_certificate_effect": True,
            "requires_exact_context_hash_match": True,
            "requires_pool_payload": True,
            "requires_true_dual_vector": True,
            "requires_cut_payload": True,
            "requires_branch_and_forbidden_context": True,
        },
    }


def build_manifest(paths: Iterable[Path], *, ready_only: bool = False) -> dict[str, Any]:
    all_cases = [
        _case_from_event(event, index)
        for index, event in enumerate(_iter_capture_events(paths), start=1)
    ]
    cases = [case for case in all_cases if case["ready_for_rmp_replay"]] if ready_only else all_cases
    ready_cases = [case for case in cases if case["ready_for_rmp_replay"]]
    candidate_count = sum(int(case["candidate_summary"]["candidate_count"]) for case in cases)
    treatment_count = sum(len(case["treatments"]) for case in cases)
    checks = {
        "has_capture_cases": bool(cases),
        "has_ready_rmp_replay_cases": bool(ready_cases),
        "all_cases_no_certificate_effect": all(
            case["diagnostic_only"] and case["replay_no_certificate_effect"] for case in cases
        ),
        "all_ready_cases_have_complete_pool_payload": all(
            case["complete_pool_payload"] for case in ready_cases
        ),
        "all_ready_cases_have_complete_returned_batch": all(
            case["complete_returned_batch"] for case in ready_cases
        ),
        "all_ready_cases_have_treatments": all(bool(case["treatments"]) for case in ready_cases),
    }
    return {
        "schema_version": "counterfactual_replay_manifest_v1",
        "input_paths": [str(path) for path in paths],
        "ready_only": bool(ready_only),
        "raw_case_count": len(all_cases),
        "case_count": len(cases),
        "ready_case_count": len(ready_cases),
        "candidate_count": candidate_count,
        "treatment_count": treatment_count,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "interpretation": (
            "A ready manifest means exact-context replay inputs are available. "
            "It is not evidence that any treatment improves optimization."
        ),
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="JSONL files or directories to scan.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--ready-only",
        action="store_true",
        help="Write only complete, no-certificate-effect cases ready for local RMP replay.",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(args.paths, ready_only=bool(args.ready_only))
    summary = {
        key: value
        for key, value in manifest.items()
        if key != "cases"
    }
    summary["case_summaries"] = [
        {
            "case_id": case["case_id"],
            "source_file": case["source_file"],
            "instance": case["instance"],
            "cg_iter": case["cg_iter"],
            "pricing_kind": case["pricing_kind"],
            "pricing_state": case["pricing_state"],
            "context_hash": case["context_hash"],
            "ready_for_rmp_replay": case["ready_for_rmp_replay"],
            "candidate_summary": case["candidate_summary"],
            "treatment_count": len(case["treatments"]),
            "issues": case["issues"],
        }
        for case in manifest["cases"]
    ]
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "replay_cases.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
