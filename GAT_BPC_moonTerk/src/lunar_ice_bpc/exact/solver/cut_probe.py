"""Diagnostic cut-candidate probing over restricted RMP primal lambdas."""

from __future__ import annotations

import hashlib
import json
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
        pool,
        primal_rows,
        max_candidates=max_subset_candidates,
        subset_size=subset_size,
        violation_eps=violation_eps,
    )
    fleet_candidate = _fleet_lower_bound_candidate(
        ordered_tasks,
        pool,
        primal_rows,
        fleet_size=int(fleet_size),
        violation_eps=violation_eps,
    )
    violated_subset_count = sum(1 for row in subset_candidates if bool(row["violated"]))
    violations = [float(row["violation"]) for row in subset_candidates]
    support_counts = [int(row["support_column_count"]) for row in subset_candidates]
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
        "max_violation": round(max(violations), 9) if violations else None,
        "mean_violation": round(sum(violations) / len(violations), 9) if violations else None,
        "violated_subset_size_histogram": _violated_subset_size_histogram(subset_candidates),
        "affected_column_count": max(support_counts) if support_counts else 0,
        "active_support_overlap": (
            round(max(support_counts) / len(primal_rows), 9)
            if support_counts and primal_rows
            else 0.0
        ),
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
    columns: tuple[JourneyColumn, ...],
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
        cut_payload = subset_row_cut(_subset_cut_id(subset), subset, divisor=2).to_payload()
        candidates.append(
            {
                "cut_kind": "subset_row",
                "cut_key": cut_payload["cut_id"],
                "cut_type": "subset_row",
                "tasks": list(subset),
                "subset_size": len(subset),
                "divisor": cut.divisor,
                "rhs": cut.rhs,
                "sense": "<=",
                "coefficient_dependency": "task_set",
                "pricing_supported": True,
                "completion_bound_supported": False,
                "dominance_compatible": True,
                "activity": round(float(activity), 9),
                "violation": round(float(violation), 9),
                "violated": bool(violation > abs(float(violation_eps))),
                "would_bind_on_current_rmp": bool(activity >= float(cut.rhs) - abs(float(violation_eps))),
                "would_change_dual_support": bool(violation > abs(float(violation_eps))),
                "support_column_count": support_count,
                "affected_column_count": support_count,
                "active_support_overlap": (
                    round(float(support_count) / len(primal_rows), 9)
                    if primal_rows
                    else 0.0
                ),
                "coefficient_vector_hash": _coefficient_vector_hash(cut, columns),
                "cut_context": cut_payload,
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
    columns: tuple[JourneyColumn, ...],
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
        "cut_kind": "fleet_lower_bound",
        "cut_key": cut.cut_id,
        "cut_type": "fleet_lower_bound",
        "rhs": cut.rhs,
        "sense": ">=",
        "coefficient_dependency": "nonempty_journey_indicator",
        "pricing_supported": True,
        "completion_bound_supported": False,
        "dominance_compatible": False,
        "activity": round(float(activity), 9),
        "violation": round(float(violation), 9),
        "violated": bool(violation > abs(float(violation_eps))),
        "would_bind_on_current_rmp": bool(activity <= float(cut.rhs) + abs(float(violation_eps))),
        "would_change_dual_support": bool(violation > abs(float(violation_eps))),
        "support_column_count": len(primal_rows),
        "affected_column_count": len(primal_rows),
        "active_support_overlap": 1.0 if primal_rows else 0.0,
        "coefficient_vector_hash": _coefficient_vector_hash(cut, columns),
        "cut_context": cut.to_payload(),
    }


def _subset_cut_id(subset: tuple[str, ...]) -> str:
    return "sri_probe_" + "_".join(str(task_id) for task_id in subset)


def _coefficient_vector_hash(cut, columns: tuple[JourneyColumn, ...]) -> str:
    vector = [
        [index, round(float(cut.coefficient(column)), 9)]
        for index, column in enumerate(columns)
        if abs(float(cut.coefficient(column))) > 1.0e-12
    ]
    return hashlib.sha256(json.dumps(vector, sort_keys=True).encode("utf-8")).hexdigest()


def _violated_subset_size_histogram(candidates: list[dict]) -> dict[str, int]:
    histogram: dict[str, int] = {}
    for row in candidates:
        if not row.get("violated"):
            continue
        key = str(row.get("subset_size") or len(row.get("tasks") or []))
        histogram[key] = histogram.get(key, 0) + 1
    return histogram
