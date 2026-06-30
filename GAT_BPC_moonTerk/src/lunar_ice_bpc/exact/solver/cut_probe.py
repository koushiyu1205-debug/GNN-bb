"""Diagnostic cut-candidate probing over restricted RMP primal lambdas."""

from __future__ import annotations

from itertools import combinations
from typing import Iterable, Mapping

from lunar_ice_bpc.exact.core.cuts import fleet_lower_bound_cut, subset_row_cut
from lunar_ice_bpc.exact.core.journey import JourneyColumn


def build_cut_probe(
    task_ids: Iterable[str],
    columns: Iterable[JourneyColumn],
    primal_columns: Iterable[Mapping[str, object]],
    *,
    fleet_size: int,
    max_subset_candidates: int = 10,
    subset_size: int = 3,
    violation_eps: float = 1.0e-6,
) -> dict:
    """Return diagnostic cut candidates without adding rows to the RMP.

    The activities are computed from the restricted RMP primal lambda payload.
    They can expose useful cut workload and candidate rows, but no row is added
    to the master and no lower-bound or certificate status can change.
    """

    ordered_tasks = tuple(sorted(str(task_id) for task_id in task_ids))
    pool = tuple(columns)
    primal_rows = tuple(primal_columns)
    subset_candidates = _subset_row_candidates(
        ordered_tasks,
        primal_rows,
        max_candidates=max_subset_candidates,
        subset_size=subset_size,
        violation_eps=violation_eps,
    )
    fleet_candidate = _fleet_lower_bound_candidate(
        ordered_tasks,
        primal_rows,
        fleet_size=int(fleet_size),
        violation_eps=violation_eps,
    )
    violated_subset_count = sum(1 for row in subset_candidates if bool(row["violated"]))
    return {
        "schema_version": "lunar_ice_bpc.cut_probe.v1",
        "status": "CUT_PROBE_READY" if subset_candidates or fleet_candidate else "NO_CUT_PROBE_CANDIDATE",
        "evaluation_scope": "restricted_rmp_primal_only",
        "column_pool_size": len(pool),
        "primal_column_count": len(primal_rows),
        "task_count": len(ordered_tasks),
        "subset_size": int(subset_size),
        "subset_candidate_count": len(subset_candidates),
        "violated_subset_candidate_count": violated_subset_count,
        "fleet_lower_bound_candidate": fleet_candidate,
        "subset_candidates": subset_candidates,
        "rows_added_to_rmp": 0,
        "cut_rows_active": False,
        "lower_bound_official": False,
        "exact_status_effect": "none",
        "mutates_solver": False,
        "can_certify": False,
        "note": (
            "Diagnostic cut probe over restricted RMP primal lambdas. Candidate rows are not added "
            "to the RMP and cannot affect bounds, pricing certificates, or optimality claims."
        ),
    }


def _subset_row_candidates(
    task_ids: tuple[str, ...],
    primal_rows: tuple[Mapping[str, object], ...],
    *,
    max_candidates: int,
    subset_size: int,
    violation_eps: float,
) -> list[dict]:
    if len(task_ids) < int(subset_size):
        return []
    candidates: list[dict] = []
    for subset in combinations(task_ids, int(subset_size)):
        cut = subset_row_cut("sri_probe", subset, divisor=2)
        activity = 0.0
        support_count = 0
        for row in primal_rows:
            overlap = len(set(str(task_id) for task_id in row.get("tasks", []) or []).intersection(subset))
            coefficient = float(overlap // int(cut.divisor))
            if coefficient <= 0.0:
                continue
            support_count += 1
            activity += coefficient * float(row.get("lambda_value") or 0.0)
        violation = activity - float(cut.rhs)
        candidates.append(
            {
                "cut_type": "subset_row",
                "tasks": list(subset),
                "divisor": cut.divisor,
                "rhs": cut.rhs,
                "activity": round(float(activity), 9),
                "violation": round(float(violation), 9),
                "violated": bool(violation > abs(float(violation_eps))),
                "support_column_count": support_count,
                "cut_context": subset_row_cut(_subset_cut_id(subset), subset, divisor=2).to_payload(),
            }
        )
    candidates.sort(
        key=lambda row: (
            -float(row["violation"]),
            -int(row["support_column_count"]),
            tuple(str(task_id) for task_id in row["tasks"]),
        )
    )
    return candidates[: max(0, int(max_candidates))]


def _fleet_lower_bound_candidate(
    task_ids: tuple[str, ...],
    primal_rows: tuple[Mapping[str, object], ...],
    *,
    fleet_size: int,
    violation_eps: float,
) -> dict | None:
    if not task_ids:
        return None
    min_vehicles = 1 if len(task_ids) <= max(1, int(fleet_size)) else 2
    cut = fleet_lower_bound_cut("fleet_lb_probe", min_vehicles=min_vehicles)
    activity = sum(float(row.get("lambda_value") or 0.0) for row in primal_rows)
    violation = float(cut.rhs) - activity
    return {
        "cut_type": "fleet_lower_bound",
        "rhs": cut.rhs,
        "activity": round(float(activity), 9),
        "violation": round(float(violation), 9),
        "violated": bool(violation > abs(float(violation_eps))),
        "support_column_count": len(primal_rows),
        "cut_context": cut.to_payload(),
    }


def _subset_cut_id(subset: tuple[str, ...]) -> str:
    return "sri_probe_" + "_".join(str(task_id) for task_id in subset)
