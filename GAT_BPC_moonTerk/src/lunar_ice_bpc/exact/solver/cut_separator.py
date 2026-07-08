"""One-round diagnostic cut separation over a supplied journey-column pool."""

from __future__ import annotations

from typing import Iterable, Mapping

from lunar_ice_bpc.exact.core.cuts import CUT_TYPES, CutContext, cut_context_from_payload
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.master.journey_rmp import RestrictedRMPResult, solve_restricted_journey_rmp
from lunar_ice_bpc.exact.solver.cut_probe import build_cut_probe


def run_restricted_cut_separation_round(
    task_ids: Iterable[str],
    columns: Iterable[JourneyColumn],
    *,
    fleet_size: int,
    root_rmp: RestrictedRMPResult | None = None,
    cut_probe: Mapping[str, object] | None = None,
    max_rows: int = 3,
    violation_eps: float = 1.0e-6,
    include_fleet_lower_bound: bool = False,
    add_violated_only: bool = True,
) -> dict:
    """Add selected probe cuts to a second restricted RMP solve.

    This is a diagnostic bridge toward the future cut loop. It never mutates the
    caller's incumbent, does not update official bounds, and cannot certify a
    node because pricing is still limited to the supplied column pool.
    """

    ordered_tasks = tuple(str(task_id) for task_id in task_ids)
    pool = tuple(columns)
    root = root_rmp or solve_restricted_journey_rmp(ordered_tasks, pool, fleet_size=int(fleet_size))
    probe = dict(
        cut_probe
        if cut_probe is not None
        else build_cut_probe(
            ordered_tasks,
            pool,
            root.primal_columns,
            fleet_size=int(fleet_size),
            violation_eps=float(violation_eps),
        )
    )
    selected_cut_payloads = _selected_cut_payloads(
        probe,
        max_rows=max_rows,
        violation_eps=violation_eps,
        include_fleet_lower_bound=include_fleet_lower_bound,
        add_violated_only=add_violated_only,
    )
    if not selected_cut_payloads:
        return {
            "schema_version": "lunar_ice_bpc.cut_separation_round.v1",
            "status": "NO_CUT_ROW_ADDED",
            "evaluation_scope": "supplied_column_pool_only",
            "root_restricted_rmp_status": root.status,
            "root_objective_bound": root.objective_bound,
            "cut_probe_status": probe.get("status"),
            "candidate_cut_count": _candidate_count(probe, include_fleet_lower_bound=include_fleet_lower_bound),
            "selected_cut_count": 0,
            "rows_added_to_rmp": 0,
            "cut_rows_active": False,
            "cut_context": CutContext().to_payload(),
            "cut_rmp_status": "NOT_RUN",
            "cut_rmp_objective_bound": None,
            "cut_rmp_bound_delta": None,
            "cut_rmp_min_reduced_cost": None,
            "primal_cut_violation_max": None,
            "selected_cuts": [],
            "restricted_pricing_claimed_no_negative": False,
            "lower_bound_official": False,
            "mutates_solver": False,
            "can_certify": False,
            "exact_status_effect": "none",
            "note": "No violated eligible cut candidate was selected for the diagnostic cut RMP.",
        }

    context = cut_context_from_payload({"cuts": selected_cut_payloads})
    cut_rmp = solve_restricted_journey_rmp(
        ordered_tasks,
        pool,
        fleet_size=int(fleet_size),
        cut_context=context,
    )
    return {
        "schema_version": "lunar_ice_bpc.cut_separation_round.v1",
        "status": "RESTRICTED_CUT_SEPARATION_EVALUATED",
        "evaluation_scope": "supplied_column_pool_only",
        "root_restricted_rmp_status": root.status,
        "root_objective_bound": root.objective_bound,
        "cut_probe_status": probe.get("status"),
        "candidate_cut_count": _candidate_count(probe, include_fleet_lower_bound=include_fleet_lower_bound),
        "selected_cut_count": len(selected_cut_payloads),
        "rows_added_to_rmp": len(selected_cut_payloads),
        "cut_rows_active": True,
        "cut_context": context.to_payload(),
        "cut_rmp_status": cut_rmp.status,
        "cut_rmp_exact_status": cut_rmp.exact_status,
        "cut_rmp_objective_bound": cut_rmp.objective_bound,
        "cut_rmp_bound_delta": _bound_delta(root.objective_bound, cut_rmp.objective_bound),
        "cut_rmp_min_reduced_cost": cut_rmp.min_reduced_cost,
        "cut_rmp_active_column_count": cut_rmp.active_column_count,
        "cut_rmp_iteration_count": cut_rmp.iteration_count,
        "cut_duals": dict(cut_rmp.duals.cuts or {}),
        "primal_cut_activities": list(cut_rmp.primal_cut_activities),
        "primal_cut_violation_max": cut_rmp.primal_cut_violation_max,
        "selected_cuts": list(selected_cut_payloads),
        "selected_cut_diagnostics": _selected_cut_diagnostics(probe, selected_cut_payloads),
        "restricted_pricing_claimed_no_negative": False,
        "lower_bound_official": False,
        "mutates_solver": False,
        "can_certify": False,
        "exact_status_effect": "none",
        "note": (
            "One diagnostic cut-separation round over the supplied restricted journey-column pool. "
            "The cut RMP value is not an official BPC bound."
        ),
    }


def _selected_cut_payloads(
    cut_probe: Mapping[str, object],
    *,
    max_rows: int,
    violation_eps: float,
    include_fleet_lower_bound: bool,
    add_violated_only: bool,
) -> tuple[dict, ...]:
    rows: list[dict] = []
    for candidate in cut_probe.get("subset_candidates", []) or []:
        _append_candidate_cut(
            rows,
            candidate,
            violation_eps=violation_eps,
            add_violated_only=add_violated_only,
        )
        if len(rows) >= int(max_rows):
            return tuple(rows)
    if include_fleet_lower_bound and len(rows) < int(max_rows):
        _append_candidate_cut(
            rows,
            cut_probe.get("fleet_lower_bound_candidate") or {},
            violation_eps=violation_eps,
            add_violated_only=add_violated_only,
        )
    deduped: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        cut_id = str(row.get("cut_id") or "")
        cut_type = str(row.get("cut_type") or "")
        if not cut_id or cut_type not in CUT_TYPES or cut_id in seen:
            continue
        seen.add(cut_id)
        deduped.append(row)
    return tuple(deduped[: max(0, int(max_rows))])


def _append_candidate_cut(
    rows: list[dict],
    candidate: Mapping[str, object],
    *,
    violation_eps: float,
    add_violated_only: bool,
) -> None:
    if not candidate:
        return
    violation = float(candidate.get("violation") or 0.0)
    if add_violated_only and violation <= abs(float(violation_eps)):
        return
    cut_payload = candidate.get("cut_context")
    if isinstance(cut_payload, dict):
        rows.append(dict(cut_payload))


def _candidate_count(cut_probe: Mapping[str, object], *, include_fleet_lower_bound: bool) -> int:
    count = len(cut_probe.get("subset_candidates", []) or [])
    if include_fleet_lower_bound and cut_probe.get("fleet_lower_bound_candidate"):
        count += 1
    return count


def _selected_cut_diagnostics(cut_probe: Mapping[str, object], selected_cut_payloads: tuple[dict, ...]) -> list[dict]:
    by_id: dict[str, dict] = {}
    for candidate in cut_probe.get("subset_candidates", []) or []:
        payload = candidate.get("cut_context") if isinstance(candidate, Mapping) else None
        if isinstance(payload, Mapping):
            by_id[str(payload.get("cut_id") or "")] = dict(candidate)
    fleet = cut_probe.get("fleet_lower_bound_candidate") or {}
    if isinstance(fleet, Mapping):
        payload = fleet.get("cut_context")
        if isinstance(payload, Mapping):
            by_id[str(payload.get("cut_id") or "")] = dict(fleet)
    return [by_id.get(str(row.get("cut_id") or ""), {"cut_key": row.get("cut_id")}) for row in selected_cut_payloads]


def _bound_delta(root_bound: float | None, cut_bound: float | None) -> float | None:
    if root_bound is None or cut_bound is None:
        return None
    return round(float(cut_bound) - float(root_bound), 9)
