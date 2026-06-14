#!/usr/bin/env python3
"""Run offline no-certificate-effect RMP replays from capture manifests.

The replay is deliberately local to the captured RMP pool.  It rebuilds
JourneyColumn objects through ``evaluate_timed_trip`` and ``make_journey``,
then compares the control RMP against treatment RMPs.  It does not run pricing,
branching, cuts separation, final judge, or certificate logic.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
from typing import Any

from BPC_future.core.columns import TimedTrip, evaluate_timed_trip
from BPC_future.core.cuts import (
    FleetLowerBoundCut,
    FleetUpperBoundCut,
    FutureCut,
    SubsetRowCut,
)
from BPC_future.core.data import ArcOption, FutureData, load_future_data
from BPC_future.core.journey import JourneyColumn, JourneyPool, make_journey
from BPC_future.master.journey_rmp import JourneyDuals, solve_journey_rmp


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _load_case_data(case: dict[str, Any]) -> FutureData:
    instance_path = str(case.get("instance_path") or "").strip()
    if instance_path and Path(instance_path).exists():
        data = load_future_data(instance_path)
    else:
        data = load_future_data(str(case.get("instance") or ""))
    if case.get("vehicle_count") is not None:
        vehicle_count = max(1, _as_int(case.get("vehicle_count"), len(data.vehicles)))
        if vehicle_count != len(data.vehicles):
            data = replace(data, vehicles=tuple(range(1, vehicle_count + 1)))
    return data


def _cut_from_payload(payload: dict[str, Any], *, issues: list[str]) -> FutureCut | None:
    kind = str(payload.get("kind", "") or "")
    body = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
    if kind == "fleet_lower_bound":
        try:
            return FleetLowerBoundCut(lb=_as_int(body.get("lb", body.get("rhs")), 0))
        except Exception:
            issues.append("cut_fleet_lower_bound_not_reconstructable")
            return None
    if kind == "fleet_upper_bound":
        try:
            return FleetUpperBoundCut(
                ub=_as_int(body.get("ub", body.get("rhs")), 0),
                incumbent=_as_float(body.get("incumbent")),
                unavoidable_cost_lb=_as_float(body.get("unavoidable_cost_lb")),
            )
        except Exception:
            issues.append("cut_fleet_upper_bound_not_reconstructable")
            return None
    if kind == "subset_row":
        try:
            return SubsetRowCut(
                tasks=tuple(_as_int(task) for task in body.get("tasks", []) or []),
                k=_as_int(body.get("k"), 0),
            )
        except Exception:
            issues.append("cut_subset_row_not_reconstructable")
            return None
    issues.append(f"unsupported_cut_kind_{kind or 'empty'}")
    return None


def _cuts_from_case(case: dict[str, Any], *, issues: list[str]) -> tuple[FutureCut, ...]:
    cuts: list[FutureCut] = []
    for payload in case.get("cuts", []) or []:
        if not isinstance(payload, dict):
            issues.append("cut_payload_not_object")
            continue
        cut = _cut_from_payload(payload, issues=issues)
        if cut is not None:
            cuts.append(cut)
    return tuple(cuts)


def _arc_options_from_ids(
    data: FutureData,
    tasks: tuple[int, ...],
    option_ids: tuple[str, ...],
) -> tuple[ArcOption, ...] | None:
    if len(option_ids) != len(tasks) + 1:
        return None
    current = 0
    selected: list[ArcOption] = []
    for destination, option_id in zip((*tasks, 0), option_ids):
        matches = [
            option
            for option in data.options(int(current), int(destination))
            if str(option.option_id) == str(option_id)
        ]
        if not matches:
            return None
        selected.append(matches[0])
        current = int(destination)
    return tuple(selected)


def _materialize_trip(
    data: FutureData,
    payload: dict[str, Any],
    *,
    time_bucket_size: float,
    issues: list[str],
) -> TimedTrip | None:
    tasks = tuple(int(task) for task in payload.get("tasks", []) or [])
    option_ids = tuple(str(option_id) for option_id in payload.get("arc_option_ids", []) or [])
    arc_options = _arc_options_from_ids(data, tasks, option_ids)
    if arc_options is None:
        issues.append("trip_arc_options_not_reconstructable")
        return None
    trip = evaluate_timed_trip(
        data,
        tasks,
        _as_float(payload.get("start_time")),
        time_bucket_size=float(time_bucket_size),
        arc_options=arc_options,
        include_physical_paths=False,
    )
    if trip is None:
        issues.append("trip_evaluate_timed_trip_infeasible")
        return None
    for key in ("start_time", "end_time", "cost", "energy"):
        if abs(_as_float(getattr(trip, key), 0.0) - _as_float(payload.get(key), 0.0)) > 1.0e-5:
            issues.append(f"trip_{key}_mismatch")
    return trip


def _materialize_journey(
    data: FutureData,
    payload: dict[str, Any],
    *,
    time_bucket_size: float,
    issues: list[str],
) -> JourneyColumn | None:
    trips: list[TimedTrip] = []
    for trip_payload in payload.get("trips", []) or []:
        trip = _materialize_trip(
            data,
            trip_payload,
            time_bucket_size=time_bucket_size,
            issues=issues,
        )
        if trip is None:
            return None
        trips.append(trip)
    journey = make_journey(data, trips)
    if journey is None:
        issues.append("make_journey_infeasible")
        return None
    if tuple(journey.signature) != tuple(
        (tuple(item[0]), tuple(str(option) for option in item[1]), float(item[2]))
        for item in payload.get("signature", []) or []
    ):
        issues.append("journey_signature_mismatch")
    if abs(float(journey.cost) - _as_float(payload.get("cost"))) > 1.0e-5:
        issues.append("journey_cost_mismatch")
    return journey


def _materialize_journeys(
    data: FutureData,
    payloads: list[dict[str, Any]],
    *,
    time_bucket_size: float,
    issues: list[str],
) -> list[JourneyColumn]:
    journeys: list[JourneyColumn] = []
    for payload in payloads:
        journey = _materialize_journey(
            data,
            payload,
            time_bucket_size=time_bucket_size,
            issues=issues,
        )
        if journey is not None:
            journeys.append(journey)
    return journeys


def _pool_from_journeys(journeys: list[JourneyColumn]) -> JourneyPool:
    pool = JourneyPool()
    for journey in journeys:
        pool.add(journey)
    return pool


def _dual_l1(left: JourneyDuals | None, right: JourneyDuals | None) -> float | None:
    if left is None or right is None:
        return None
    tasks = set(left.cover) | set(right.cover)
    value = sum(abs(float(left.cover.get(task, 0.0)) - float(right.cover.get(task, 0.0))) for task in tasks)
    value += abs(float(left.fleet_limit) - float(right.fleet_limit))
    cut_keys = set(left.cuts or {}) | set(right.cuts or {})
    value += sum(
        abs(float((left.cuts or {}).get(key, 0.0)) - float((right.cuts or {}).get(key, 0.0)))
        for key in cut_keys
    )
    return round(float(value), 9)


def _solve_pool(
    data: FutureData,
    journeys: list[JourneyColumn],
    *,
    cuts: tuple[FutureCut, ...],
    fleet_limit: int | None,
) -> dict[str, Any]:
    result = solve_journey_rmp(
        data,
        journeys,
        cuts=cuts,
        fleet_limit=fleet_limit,
        capture_reduced_costs=True,
    )
    return {
        "status": result.status,
        "objective": None if result.objective is None else round(float(result.objective), 9),
        "duals": result.duals,
        "journey_count": len(journeys),
        "variable_count": int(result.variable_count),
        "selected_count": len(result.journey_values),
    }


def _run_case(case: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if case.get("ready_for_rmp_replay") is False:
        manifest_issues = list(case.get("issues") or [])
        if not manifest_issues:
            manifest_issues.append("manifest_case_not_ready_for_rmp_replay")
        return {
            "case_id": case.get("case_id", ""),
            "ready_for_replay": False,
            "issues": sorted(set(str(issue) for issue in manifest_issues)),
            "treatments": [],
        }
    if case.get("branch_constraints"):
        issues.append("branch_constraints_not_supported_by_replay_runner")
    cuts = _cuts_from_case(case, issues=issues)
    fleet_limit = None
    if case.get("vehicle_count") is not None:
        fleet_limit = max(1, _as_int(case.get("vehicle_count"), 0))
    data = _load_case_data(case)
    time_bucket_size = _as_float(case.get("pricing_time_bucket_size"), 5.0)
    pool_journeys = _materialize_journeys(
        data,
        list(case.get("pool_journeys") or []),
        time_bucket_size=time_bucket_size,
        issues=issues,
    )
    returned_journeys = _materialize_journeys(
        data,
        list(case.get("returned_journeys") or []),
        time_bucket_size=time_bucket_size,
        issues=issues,
    )
    if issues:
        return {
            "case_id": case.get("case_id", ""),
            "ready_for_replay": False,
            "issues": sorted(set(issues)),
            "treatments": [],
        }
    control = _solve_pool(
        data,
        list(_pool_from_journeys(pool_journeys).journeys),
        cuts=cuts,
        fleet_limit=fleet_limit,
    )
    candidate_by_id = {
        candidate["candidate_id"]: returned_journeys[int(candidate["journey_index"])]
        for candidate in case.get("candidates", []) or []
        if int(candidate.get("journey_index", -1)) < len(returned_journeys)
    }
    treatment_results: list[dict[str, Any]] = []
    for treatment in case.get("treatments", []) or []:
        pool = _pool_from_journeys(pool_journeys)
        before_count = len(pool.journeys)
        selected = [
            candidate_by_id[candidate_id]
            for candidate_id in treatment.get("candidate_ids", []) or []
            if candidate_id in candidate_by_id
        ]
        for journey in selected:
            pool.add(journey)
        after_count = len(pool.journeys)
        solved = _solve_pool(data, list(pool.journeys), cuts=cuts, fleet_limit=fleet_limit)
        objective_delta = None
        if control["objective"] is not None and solved["objective"] is not None:
            objective_delta = round(float(solved["objective"]) - float(control["objective"]), 9)
        treatment_results.append(
            {
                "treatment_id": treatment.get("treatment_id", ""),
                "candidate_ids": list(treatment.get("candidate_ids", []) or []),
                "changed_journey_count": int(after_count - before_count),
                "status": solved["status"],
                "objective": solved["objective"],
                "objective_delta_vs_control": objective_delta,
                "dual_l1_delta_vs_control": _dual_l1(control["duals"], solved["duals"]),
                "selected_count": solved["selected_count"],
                "journey_count": solved["journey_count"],
                "no_op_treatment": bool(after_count == before_count and objective_delta == 0.0),
            }
        )
    noncontrol = [item for item in treatment_results if item["treatment_id"] != "control_no_addition"]
    improving = [
        item for item in noncontrol
        if item.get("objective_delta_vs_control") is not None
        and float(item["objective_delta_vs_control"]) < -1.0e-9
    ]
    changed = [item for item in noncontrol if int(item.get("changed_journey_count") or 0) > 0]
    objective_deltas = [
        float(item["objective_delta_vs_control"])
        for item in noncontrol
        if item.get("objective_delta_vs_control") is not None
    ]
    return {
        "case_id": case.get("case_id", ""),
        "ready_for_replay": True,
        "issues": [],
        "control": {
            key: value
            for key, value in control.items()
            if key != "duals"
        },
        "materialized_pool_journey_count": len(pool_journeys),
        "materialized_returned_journey_count": len(returned_journeys),
        "treatments": treatment_results,
        "changed_treatment_count": len(changed),
        "improving_treatment_count": len(improving),
        "best_objective_delta": None if not objective_deltas else min(objective_deltas),
    }


def run_replay(manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases = [_run_case(case) for case in manifest.get("cases", []) or []]
    ready_cases = [case for case in cases if case.get("ready_for_replay")]
    changed_treatments = sum(_as_int(case.get("changed_treatment_count")) for case in ready_cases)
    improving_treatments = sum(_as_int(case.get("improving_treatment_count")) for case in ready_cases)
    checks = {
        "has_replay_cases": bool(cases),
        "all_replay_is_no_certificate_effect": True,
        "all_ready_cases_replayed": bool(ready_cases) and len(ready_cases) == len(cases),
        "no_replay_issues": all(not case.get("issues") for case in cases),
        "control_rmp_solved": all(
            (case.get("control") or {}).get("status") == "OPTIMAL" for case in ready_cases
        ),
    }
    return {
        "schema_version": "counterfactual_replay_result_v1",
        "manifest_path": str(manifest_path),
        "case_count": len(cases),
        "ready_case_count": len(ready_cases),
        "changed_treatment_count": changed_treatments,
        "improving_treatment_count": improving_treatments,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "interpretation": (
            "Replay result measures immediate local RMP impact only. It is not "
            "an official bound, certificate, or full BPC speedup proof."
        ),
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Path to replay_cases.json.")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = run_replay(args.manifest)
    summary = {
        key: value
        for key, value in result.items()
        if key != "cases"
    }
    summary["case_summaries"] = [
        {
            "case_id": case.get("case_id"),
            "ready_for_replay": case.get("ready_for_replay"),
            "issues": case.get("issues", []),
            "control": case.get("control", {}),
            "changed_treatment_count": case.get("changed_treatment_count", 0),
            "improving_treatment_count": case.get("improving_treatment_count", 0),
            "best_objective_delta": case.get("best_objective_delta"),
        }
        for case in result["cases"]
    ]
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "replay_results.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
