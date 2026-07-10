"""Pricing routines for restricted and direct-label journey diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
import heapq
from itertools import combinations, permutations, product
from time import perf_counter

from lunar_ice_bpc.domain.scenario import PATH_TYPES
from lunar_ice_bpc.exact.bpc.core.task_index import TaskIndexMap
from lunar_ice_bpc.exact.core.columns import TimedSortie, build_timed_sortie
from lunar_ice_bpc.exact.core.branching import BranchContext, journey_satisfies_branch_context
from lunar_ice_bpc.exact.core.cuts import FLEET_LOWER_BOUND_CUT, SUBSET_ROW_CUT, CutContext
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn, build_journey_column
from lunar_ice_bpc.exact.core.objective import (
    additive_objective_value,
    operating_cost_value,
    service_risk_value,
    sortie_objective_value,
)
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals, solve_restricted_journey_rmp, manual_journey_reduced_cost
from lunar_ice_bpc.exact.pricing.completion_bounds import build_positive_cover_completion_bound
from lunar_ice_bpc.exact.solver.column_pool import select_journey_column_pool
from lunar_ice_bpc.exact.solver.journey_driver import (
    DirectBaselineTimeLimitExceeded,
    _direct_sortie_candidates_from_start,
    _nondominated_path_type_cache,
    _path_type_lower_bound_cache,
    enumerate_canonical_journey_columns,
)


@dataclass(frozen=True)
class _DirectSortieTemplate:
    task_mask: int
    sequence: tuple[str, ...]
    path_types: tuple[str, ...]


@dataclass
class DirectPricingCache:
    """Caches direct sortie templates for candidate task sets.

    The cached templates depend only on the instance and the candidate task
    set, not on RMP duals. Reduced-cost labels are still rebuilt every call.
    """

    templates_by_candidate: dict[
        tuple[str, tuple[str, ...]],
        tuple[dict[int, tuple[_DirectSortieTemplate, ...]], int],
    ] = field(default_factory=dict)
    hit_count: int = 0
    miss_count: int = 0
    built_sortie_attempt_count: int = 0
    reused_sortie_attempt_count: int = 0

    def get_or_build(
        self,
        data: LunarIceData,
        candidate_task_ids: tuple[str, ...],
    ) -> tuple[tuple[str, ...], dict[int, tuple[_DirectSortieTemplate, ...]], int, bool]:
        candidate_key = tuple(sorted(str(task_id) for task_id in candidate_task_ids))
        key = (str(data.instance_id), candidate_key)
        cached = self.templates_by_candidate.get(key)
        if cached is not None:
            self.hit_count += 1
            self.reused_sortie_attempt_count += cached[1]
            return candidate_key, cached[0], cached[1], True

        task_index = TaskIndexMap(candidate_key)
        task_to_bit = {task_id: task_index.mask_of(task_id) for task_id in task_index.external_ids}
        templates_by_mask, attempt_count = _enumerate_direct_sortie_templates(data, candidate_key, task_to_bit)
        self.templates_by_candidate[key] = (templates_by_mask, attempt_count)
        self.miss_count += 1
        self.built_sortie_attempt_count += attempt_count
        return candidate_key, templates_by_mask, attempt_count, False

    def stats(self) -> dict:
        return {
            "enabled": True,
            "entry_count": len(self.templates_by_candidate),
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "built_sortie_attempt_count": self.built_sortie_attempt_count,
            "reused_sortie_attempt_count": self.reused_sortie_attempt_count,
        }


@dataclass(frozen=True)
class _DirectJourneyLabel:
    task_mask: int
    sorties: tuple[TimedSortie, ...]
    end_time: float
    reduced_base: float

    def reduced_cost(
        self,
        data: LunarIceData,
        duals: JourneyDuals,
        *,
        cut_context: CutContext | None = None,
        candidate_task_ids: tuple[str, ...] = tuple(),
    ) -> float:
        cut_penalty = _label_cut_dual_penalty(self, duals, cut_context, candidate_task_ids)
        return round(
            self.reduced_base
            - float(duals.fleet_limit)
            - cut_penalty,
            9,
        )


def price_canonical_journey_universe(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    negative_eps: float = 1.0e-6,
    max_exact_tasks: int = 10,
    cut_context: CutContext | None = None,
) -> dict:
    """Enumerate the current restricted universe and return negative-RC columns.

    This is not the final true-dual exhaustive pricing oracle. It is a small
    bridge for testing reduced-cost semantics while the new project is being
    brought up.
    """

    if len(data.task_ids) > int(max_exact_tasks):
        return {
            "status": "SKIPPED_TOO_LARGE_FOR_CANONICAL_PRICING",
            "exact_status": "NOT_SOLVED",
            "generated_journey_count": 0,
            "generated_sortie_count": 0,
            "route_template_count": 0,
            "pareto_label_count": 0,
            "negative_count": 0,
            "negative_columns": [],
            "note": f"task_count={len(data.task_ids)} exceeds max_exact_tasks={max_exact_tasks}",
        }
    universe = enumerate_canonical_journey_columns(data, max_exact_tasks=int(max_exact_tasks))
    context = cut_context or CutContext()
    priced = [
        (manual_journey_reduced_cost(column, duals, cut_coefficients=context.coefficients_for(column)), column)
        for column in universe.columns
    ]
    negatives = [
        {"reduced_cost": rc, "task_count": len(column.task_set), "objective": column.objective}
        for rc, column in sorted(priced, key=lambda item: item[0])
        if rc < -abs(float(negative_eps))
    ]
    return {
        "status": "CANONICAL_UNIVERSE_PRICED",
        "exact_status": "NOT_BPC_CERTIFIED",
        "generated_journey_count": len(universe.columns),
        "generated_sortie_count": universe.generated_sortie_count,
        "route_template_count": universe.route_template_count,
        "pareto_label_count": universe.pareto_label_count,
        "negative_count": len(negatives),
        "negative_columns": negatives,
        "cut_context_active": not context.empty,
        "cut_count": len(context.cuts),
        "note": "Restricted canonical-path universe only; not a true-dual exhaustive pricing certificate.",
    }


def price_direct_journey_labels(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    negative_eps: float = 1.0e-6,
    max_direct_tasks: int = 5,
    allow_partial: bool = True,
    seed_task_sets: tuple[tuple[str, ...], ...] = tuple(),
    cache: DirectPricingCache | None = None,
    max_candidate_sets: int | None = None,
    completion_bound_enabled: bool = True,
    cut_context: CutContext | None = None,
    branch_context: BranchContext | None = None,
) -> dict:
    """Return JSON-safe direct-label pricing diagnostics."""

    payload, _ = price_direct_journey_column(
        data,
        duals,
        negative_eps=negative_eps,
        max_direct_tasks=max_direct_tasks,
        allow_partial=allow_partial,
        seed_task_sets=seed_task_sets,
        cache=cache,
        max_candidate_sets=max_candidate_sets,
        completion_bound_enabled=completion_bound_enabled,
        cut_context=cut_context,
        branch_context=branch_context,
    )
    return payload


def price_direct_journey_column(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    negative_eps: float = 1.0e-6,
    max_direct_tasks: int = 5,
    allow_partial: bool = True,
    seed_task_sets: tuple[tuple[str, ...], ...] = tuple(),
    cache: DirectPricingCache | None = None,
    max_candidate_sets: int | None = None,
    completion_bound_enabled: bool = True,
    cut_context: CutContext | None = None,
    branch_context: BranchContext | None = None,
) -> tuple[dict, JourneyColumn | None]:
    """Search reduced cost over direct labels with independent leg path choices.

    This is a small protected bridge toward true pricing. For instances within
    ``max_direct_tasks`` it enumerates all elementary sortie sequences and all
    per-leg choices from the three configured path options, then extends
    multi-sortie journey labels with simple Pareto dominance. It does not yet
    produce an official BPC certificate.
    """

    payload, columns = price_direct_journey_columns(
        data,
        duals,
        negative_eps=negative_eps,
        max_direct_tasks=max_direct_tasks,
        allow_partial=allow_partial,
        seed_task_sets=seed_task_sets,
        cache=cache,
        max_candidate_sets=max_candidate_sets,
        completion_bound_enabled=completion_bound_enabled,
        cut_context=cut_context,
        branch_context=branch_context,
    )
    return payload, columns[0] if columns else None


def price_direct_journey_columns(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    negative_eps: float = 1.0e-6,
    max_direct_tasks: int = 5,
    allow_partial: bool = True,
    seed_task_sets: tuple[tuple[str, ...], ...] = tuple(),
    cache: DirectPricingCache | None = None,
    max_candidate_sets: int | None = None,
    completion_bound_enabled: bool = True,
    cut_context: CutContext | None = None,
    branch_context: BranchContext | None = None,
) -> tuple[dict, tuple[JourneyColumn, ...]]:
    """Return best direct-label column per candidate task set."""

    all_task_ids = tuple(data.task_ids)
    context = cut_context or CutContext()
    branch = branch_context or BranchContext()
    complete_for_all_tasks = len(all_task_ids) <= int(max_direct_tasks)
    if not complete_for_all_tasks and not allow_partial:
        return {
            "status": "SKIPPED_TOO_LARGE_FOR_DIRECT_LABEL_PRICING",
            "exact_status": "NOT_SOLVED",
            "task_count": len(all_task_ids),
            "max_direct_tasks": int(max_direct_tasks),
            "candidate_task_count": 0,
            "candidate_round_limit": int(max_candidate_sets) if max_candidate_sets is not None else None,
            "candidate_task_ids": [],
            "pricing_complete_for_all_tasks": False,
            "sortie_attempt_count": 0,
            "feasible_sortie_template_count": 0,
            "pareto_label_count": 0,
            "best_reduced_cost": None,
            "negative_found": False,
            "cut_context_active": not context.empty,
            "cut_count": len(context.cuts),
            "branch_context_active": not branch.empty,
            "branch_decision_count": len(branch.pair_decisions),
            "branch_filtered_column_count": 0,
            "completion_bound": _disabled_completion_bound_payload(),
            "sortie_template_cache": _cache_payload(cache),
            "note": f"task_count={len(data.task_ids)} exceeds max_direct_tasks={max_direct_tasks}",
        }, tuple()
    candidate_sets = (
        (all_task_ids,)
        if complete_for_all_tasks
        else _select_direct_candidate_sets(data, duals, int(max_direct_tasks))
    )
    candidate_sets = _merge_candidate_sets(
        data,
        candidate_sets,
        seed_task_sets,
        max_candidate_task_count=int(max_direct_tasks),
    )
    if max_candidate_sets is not None:
        candidate_sets = candidate_sets[: max(0, int(max_candidate_sets))]
    attempt_count = 0
    feasible_template_count = 0
    pareto_count = 0
    priced_columns: list[tuple[float, tuple[str, ...], JourneyColumn]] = []
    candidate_summaries: list[dict] = []
    completion_summaries: list[dict] = []
    branch_filtered_count = 0
    for candidate_task_ids in candidate_sets:
        if cache is None:
            priced_candidate_task_ids = tuple(sorted(candidate_task_ids))
            task_index = TaskIndexMap(priced_candidate_task_ids)
            task_to_bit = {task_id: task_index.mask_of(task_id) for task_id in task_index.external_ids}
            templates_by_mask, attempts = _enumerate_direct_sortie_templates(
                data,
                priced_candidate_task_ids,
                task_to_bit,
            )
            cache_hit = False
        else:
            priced_candidate_task_ids, templates_by_mask, attempts, cache_hit = cache.get_or_build(data, candidate_task_ids)
        candidate_label, full_label, candidate_pareto_count, completion_payload = _best_direct_label(
            data,
            duals,
            priced_candidate_task_ids,
            templates_by_mask,
            completion_bound_enabled=bool(completion_bound_enabled) and context.empty and branch.empty,
            cut_context=context,
        )
        completion_summaries.append(completion_payload)
        feasible_count = sum(len(values) for values in templates_by_mask.values())
        attempt_count += attempts
        feasible_template_count += feasible_count
        pareto_count += candidate_pareto_count
        summary = {
            "candidate_task_ids": list(priced_candidate_task_ids),
            "sortie_template_cache_hit": cache_hit,
            "sortie_attempt_count": attempts,
            "feasible_sortie_template_count": feasible_count,
            "pareto_label_count": candidate_pareto_count,
            "best_reduced_cost": None,
            "negative_found": False,
            "branch_feasible": None,
            "completion_bound": completion_payload,
        }
        if candidate_label is not None:
            column = build_journey_column(data, candidate_label.sorties)
            rc = manual_journey_reduced_cost(
                column,
                duals,
                cut_coefficients=context.coefficients_for(column),
            )
            summary["best_reduced_cost"] = rc
            summary["negative_found"] = bool(rc < -abs(float(negative_eps)))
            branch_feasible = journey_satisfies_branch_context(column, branch)
            summary["branch_feasible"] = bool(branch_feasible)
            if branch_feasible:
                priced_columns.append((rc, priced_candidate_task_ids, column))
            else:
                branch_filtered_count += 1
        if full_label is not None:
            full_column = build_journey_column(data, full_label.sorties)
            full_rc = manual_journey_reduced_cost(
                full_column,
                duals,
                cut_coefficients=context.coefficients_for(full_column),
            )
            summary["full_cover_objective"] = full_column.objective
            summary["full_cover_reduced_cost"] = full_rc
            full_branch_feasible = journey_satisfies_branch_context(full_column, branch)
            summary["full_cover_branch_feasible"] = bool(full_branch_feasible)
            if full_branch_feasible:
                priced_columns.append((full_rc, priced_candidate_task_ids, full_column))
            else:
                branch_filtered_count += 1
        candidate_summaries.append(summary)
    priced_columns.sort(key=lambda item: item[0])
    negative_columns = tuple(
        column for rc, _, column in priced_columns if rc < -abs(float(negative_eps))
    )
    if not priced_columns:
        return {
            "status": "NO_DIRECT_LABEL_FOUND",
            "exact_status": "NOT_SOLVED",
            "task_count": len(all_task_ids),
            "max_direct_tasks": int(max_direct_tasks),
            "candidate_round_count": len(candidate_sets),
            "candidate_round_limit": int(max_candidate_sets) if max_candidate_sets is not None else None,
            "candidate_task_count": 0,
            "candidate_task_ids": [],
            "candidate_sets": [list(row) for row in candidate_sets],
            "candidate_summaries": candidate_summaries,
            "pricing_complete_for_all_tasks": bool(complete_for_all_tasks),
            "sortie_attempt_count": attempt_count,
            "feasible_sortie_template_count": feasible_template_count,
            "pareto_label_count": pareto_count,
            "best_reduced_cost": None,
            "negative_found": False,
            "negative_column_count": 0,
            "cut_context_active": not context.empty,
            "cut_count": len(context.cuts),
            "branch_context_active": not branch.empty,
            "branch_decision_count": len(branch.pair_decisions),
            "branch_filtered_column_count": branch_filtered_count,
            "completion_bound": _aggregate_completion_bounds(completion_summaries),
            "sortie_template_cache": _cache_payload(cache),
            "note": "No feasible direct-label journey was found.",
        }, tuple()
    rc, best_candidate_task_ids, best_column = priced_columns[0]
    payload = {
        "status": "DIRECT_LABEL_PRICED" if complete_for_all_tasks else "PARTIAL_DIRECT_LABEL_PRICED",
        "exact_status": "NOT_BPC_CERTIFIED" if complete_for_all_tasks else "NOT_SOLVED",
        "task_count": len(all_task_ids),
        "max_direct_tasks": int(max_direct_tasks),
        "candidate_round_count": len(candidate_sets),
        "candidate_round_limit": int(max_candidate_sets) if max_candidate_sets is not None else None,
        "candidate_task_count": len(best_candidate_task_ids),
        "candidate_task_ids": list(best_candidate_task_ids),
        "candidate_sets": [list(row) for row in candidate_sets],
        "candidate_summaries": candidate_summaries,
        "pricing_complete_for_all_tasks": bool(complete_for_all_tasks),
        "sortie_attempt_count": attempt_count,
        "feasible_sortie_template_count": feasible_template_count,
        "pareto_label_count": pareto_count,
        "best_reduced_cost": rc,
        "negative_found": bool(rc < -abs(float(negative_eps))),
        "negative_column_count": len(negative_columns),
        "cut_context_active": not context.empty,
        "cut_count": len(context.cuts),
        "branch_context_active": not branch.empty,
        "branch_decision_count": len(branch.pair_decisions),
        "branch_filtered_column_count": branch_filtered_count,
        "completion_bound": _aggregate_completion_bounds(completion_summaries),
        "sortie_template_cache": _cache_payload(cache),
        "best_column": {
            "task_count": len(best_column.task_set),
            "tasks": sorted(best_column.task_set),
            "objective": best_column.objective,
            "end_time": best_column.end_time,
            "sortie_count": len(best_column.sorties),
            "legs": [
                [
                    {"from": leg.source, "to": leg.target, "path_type": leg.path_type}
                    for leg in sortie.legs
                ]
                for sortie in best_column.sorties
            ],
        },
        "note": (
            "Direct-label pricing over all three per-leg path choices for the full task set within max_direct_tasks; "
            "not an official BPC certificate."
            if complete_for_all_tasks
            else "Partial direct-label pricing on a selected candidate task subset; negative columns are valid diagnostics, but no-negative is not exhaustive."
        ),
    }
    return payload, tuple(column for _, _, column in priced_columns)


def price_direct_journey_columns_incremental(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    negative_eps: float = 1.0e-6,
    max_direct_tasks: int = 12,
    seed_task_sets: tuple[tuple[str, ...], ...] = tuple(),
    max_candidate_sets: int | None = None,
    wall_time_limit_sec: float | None = None,
    stop_at_first_negative: bool = True,
    cut_context: CutContext | None = None,
    branch_context: BranchContext | None = None,
) -> tuple[dict, tuple[JourneyColumn, ...]]:
    """Reduced-cost route-template pricing over selected multi-sortie task sets.

    This opt-in probe is exact for each selected candidate task set, but it is not
    an exhaustive full-space pricing certificate unless the selected sets cover
    the full pricing space.  A returned negative column is still valid because it
    is audited with the current true RMP duals before being reported.
    """

    start = perf_counter()
    deadline = None if wall_time_limit_sec is None else start + max(0.0, float(wall_time_limit_sec))
    context = cut_context or CutContext()
    branch = branch_context or BranchContext()
    candidate_sets = _select_direct_candidate_sets(data, duals, int(max_direct_tasks))
    candidate_sets = _merge_candidate_sets(
        data,
        seed_task_sets,
        candidate_sets,
        max_candidate_task_count=int(max_direct_tasks),
    )
    if max_candidate_sets is not None:
        candidate_sets = candidate_sets[: max(0, int(max_candidate_sets))]

    priced_columns: list[tuple[float, tuple[str, ...], JourneyColumn]] = []
    candidate_summaries: list[dict] = []
    attempt_count = 0
    feasible_template_count = 0
    pareto_count = 0
    timed_out = False
    timeout_stage = ""
    branch_filtered_count = 0

    for candidate_task_ids in candidate_sets:
        if _deadline_exceeded(deadline):
            timed_out = True
            timeout_stage = "candidate_loop"
            break
        try:
            label, stats = _best_direct_label_incremental(
                data,
                duals,
                tuple(sorted(candidate_task_ids)),
                deadline=deadline,
                cut_context=context,
            )
        except DirectBaselineTimeLimitExceeded as exc:
            timed_out = True
            timeout_stage = f"incremental_route_template:{exc.stage}"
            attempt_count += int(exc.generated_sortie_count)
            feasible_template_count += int(exc.route_template_count)
            pareto_count += int(exc.pareto_label_count)
            break
        attempt_count += int(stats["sortie_attempt_count"])
        feasible_template_count += int(stats["feasible_sortie_template_count"])
        pareto_count += int(stats["pareto_label_count"])
        summary = {
            "candidate_task_ids": list(candidate_task_ids),
            "sortie_attempt_count": int(stats["sortie_attempt_count"]),
            "feasible_sortie_template_count": int(stats["feasible_sortie_template_count"]),
            "pareto_label_count": int(stats["pareto_label_count"]),
            "best_reduced_cost": None,
            "negative_found": False,
            "branch_feasible": None,
        }
        if label is not None:
            column = build_journey_column(data, label.sorties)
            rc = manual_journey_reduced_cost(
                column,
                duals,
                cut_coefficients=context.coefficients_for(column),
            )
            summary["best_reduced_cost"] = rc
            summary["negative_found"] = bool(rc < -abs(float(negative_eps)))
            branch_feasible = journey_satisfies_branch_context(column, branch)
            summary["branch_feasible"] = bool(branch_feasible)
            if branch_feasible:
                priced_columns.append((rc, tuple(sorted(candidate_task_ids)), column))
                if bool(stop_at_first_negative) and rc < -abs(float(negative_eps)):
                    candidate_summaries.append(summary)
                    break
            else:
                branch_filtered_count += 1
        candidate_summaries.append(summary)

    priced_columns.sort(key=lambda item: item[0])
    negative_columns = tuple(
        column for rc, _, column in priced_columns if rc < -abs(float(negative_eps))
    )
    best_rc = priced_columns[0][0] if priced_columns else None
    best_column = priced_columns[0][2] if priced_columns else None
    status = (
        "INCREMENTAL_DIRECT_LABEL_PRICING_TIME_LIMIT"
        if timed_out
        else "INCREMENTAL_DIRECT_LABEL_NEGATIVE_FOUND"
        if negative_columns
        else "INCREMENTAL_DIRECT_LABEL_NO_NEGATIVE_IN_SELECTED_SETS"
    )
    payload = {
        "status": status,
        "exact_status": "NOT_SOLVED",
        "task_count": len(data.task_ids),
        "max_direct_tasks": int(max_direct_tasks),
        "candidate_round_count": len(candidate_summaries),
        "candidate_round_limit": int(max_candidate_sets) if max_candidate_sets is not None else None,
        "candidate_sets": [list(row) for row in candidate_sets],
        "seed_task_sets_first": True,
        "seed_task_set_count": len(seed_task_sets),
        "candidate_summaries": candidate_summaries,
        "pricing_complete_for_all_tasks": False,
        "pricing_complete_for_all_task_subsets": False,
        "sortie_attempt_count": int(attempt_count),
        "feasible_sortie_template_count": int(feasible_template_count),
        "pareto_label_count": int(pareto_count),
        "best_reduced_cost": best_rc,
        "negative_found": bool(negative_columns),
        "negative_column_count": len(negative_columns),
        "branch_context_active": not branch.empty,
        "branch_decision_count": len(branch.pair_decisions),
        "branch_filtered_column_count": branch_filtered_count,
        "cut_context_active": not context.empty,
        "cut_count": len(context.cuts),
        "can_certify_no_negative": False,
        "uses_true_dual_bpc_certificate": False,
        "timeout_stage": timeout_stage,
        "wall_time_sec": round(perf_counter() - start, 6),
        "best_column": None if best_column is None else _best_column_payload(best_column),
        "note": (
            "Incremental direct-label route-template pricing over selected task sets. "
            "Negative columns are true-dual audited and addable diagnostics; no-column "
            "results are not exhaustive certificates."
        ),
    }
    return payload, negative_columns or tuple(column for _, _, column in priced_columns)


def price_exhaustive_direct_journey_columns(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    negative_eps: float = 1.0e-6,
    max_direct_tasks: int = 5,
    cache: DirectPricingCache | None = None,
    completion_bound_enabled: bool = True,
    cut_context: CutContext | None = None,
    branch_context: BranchContext | None = None,
) -> tuple[dict, tuple[JourneyColumn, ...]]:
    """Price every nonempty task subset for a small fixed-graph instance.

    This is a true-dual pricing coverage precursor for small instances. It is
    still fail-closed: callers must not treat it as an official certificate
    until the full BPC proof path binds it to an official node bound.
    """

    if len(data.task_ids) > int(max_direct_tasks):
        return {
            "status": "SKIPPED_TOO_LARGE_FOR_EXHAUSTIVE_DIRECT_PRICING",
            "exact_status": "NOT_SOLVED",
            "task_count": len(data.task_ids),
            "max_direct_tasks": int(max_direct_tasks),
            "pricing_complete_for_all_task_subsets": False,
            "exhaustive_candidate_set_count": 0,
            "best_reduced_cost": None,
            "negative_found": False,
            "can_certify_no_negative": False,
            "note": f"task_count={len(data.task_ids)} exceeds max_direct_tasks={max_direct_tasks}",
        }, tuple()
    candidate_sets = _all_nonempty_task_subsets(data)
    payload, columns = price_direct_journey_columns(
        data,
        duals,
        negative_eps=negative_eps,
        max_direct_tasks=int(max_direct_tasks),
        allow_partial=False,
        seed_task_sets=candidate_sets,
        cache=cache,
        completion_bound_enabled=completion_bound_enabled,
        cut_context=cut_context,
        branch_context=branch_context,
    )
    payload = dict(payload)
    payload["status"] = (
        "EXHAUSTIVE_DIRECT_LABEL_PRICED"
        if payload.get("status") == "DIRECT_LABEL_PRICED"
        else f"EXHAUSTIVE_{payload.get('status')}"
    )
    payload["exact_status"] = "NOT_BPC_CERTIFIED"
    payload["pricing_complete_for_all_task_subsets"] = True
    payload["exhaustive_candidate_set_count"] = len(candidate_sets)
    payload["can_certify_no_negative"] = False
    payload["note"] = (
        "Exhaustive direct-label pricing over every nonempty task subset for the fixed logical graph; "
        "diagnostic proof precursor only, not an official BPC certificate."
    )
    return payload, columns


def run_direct_pricing_column_generation(
    data: LunarIceData,
    initial_columns: tuple[JourneyColumn, ...],
    *,
    max_direct_tasks: int = 5,
    max_rounds: int = 3,
    negative_eps: float = 1.0e-6,
    cut_context: CutContext | None = None,
    branch_context: BranchContext | None = None,
) -> dict:
    """Run a protected direct-pricing CG diagnostic loop.

    This loop adds direct-label priced columns back into the pure-Python RMP.
    It is still a diagnostic path: partial pricing cannot prove no-negative,
    and even complete direct pricing here is not yet the official BPC
    certificate path.
    """

    columns: list[JourneyColumn] = list(initial_columns)
    seen = {_column_signature(column) for column in columns}
    seed_task_sets = _incumbent_seed_task_sets(data, columns)
    cache = DirectPricingCache()
    history: list[dict] = []
    added_count = 0
    final_rmp = None
    first_pricing: dict | None = None
    last_pricing: dict | None = None
    for round_index in range(1, int(max_rounds) + 1):
        rmp = solve_restricted_journey_rmp(
            data.task_ids,
            columns,
            fleet_size=data.fleet_size,
            cut_context=cut_context,
            branch_context=branch_context,
        )
        final_rmp = rmp
        if rmp.status != "RESTRICTED_RMP_OPTIMAL":
            return {
                "enabled": True,
                "status": "DIRECT_CG_RMP_NOT_OPTIMAL",
                "exact_status": "NOT_SOLVED",
                "round_count": round_index,
                "added_column_count": added_count,
                "final_rmp_status": rmp.status,
                "final_bound": rmp.objective_bound,
                "history": history,
                "first_direct_pricing": first_pricing,
                "last_direct_pricing": last_pricing,
                "sortie_template_cache": cache.stats(),
                "note": "Stopped because the restricted RMP did not solve to OPTIMAL.",
            }
        pricing, priced_columns = price_direct_journey_columns(
            data,
            rmp.duals,
            negative_eps=negative_eps,
            max_direct_tasks=int(max_direct_tasks),
            seed_task_sets=seed_task_sets,
            cache=cache,
            cut_context=cut_context,
            branch_context=branch_context,
        )
        if first_pricing is None:
            first_pricing = pricing
        last_pricing = pricing
        rc = pricing.get("best_reduced_cost")
        negative = bool(pricing.get("negative_found"))
        add_count = 0
        duplicate = False
        for column in priced_columns:
            signature = _column_signature(column)
            if signature in seen:
                duplicate = True
                continue
            seen.add(signature)
            columns.append(column)
            added_count += 1
            add_count += 1
        history.append(
            {
                "round": round_index,
                "rmp_bound": rmp.objective_bound,
                "rmp_active_column_count": rmp.active_column_count,
                "direct_pricing_status": pricing.get("status"),
                "direct_pricing_complete_for_all_tasks": pricing.get("pricing_complete_for_all_tasks"),
                "best_reduced_cost": rc,
                "negative_found": negative,
                "priced_column_count": len(priced_columns),
                "added_column_count": add_count,
                "duplicate_column": duplicate,
                "sortie_template_cache": pricing.get("sortie_template_cache"),
            }
        )
        if not negative:
            complete = bool(pricing.get("pricing_complete_for_all_tasks"))
            return {
                "enabled": True,
                "status": "DIRECT_CG_NO_NEGATIVE" if complete else "DIRECT_CG_PARTIAL_NO_NEGATIVE_FOUND",
                "exact_status": "NOT_BPC_CERTIFIED" if complete else "NOT_SOLVED",
                "round_count": round_index,
                "added_column_count": added_count,
                "final_rmp_status": rmp.status,
                "final_bound": rmp.objective_bound,
                "final_active_column_count": rmp.active_column_count,
                "history": history,
                "first_direct_pricing": first_pricing,
                "last_direct_pricing": pricing,
                "sortie_template_cache": cache.stats(),
                "integer_incumbent": _integer_incumbent_payload(data, columns),
                "note": (
                    "No direct-label negative column was found for the complete priced task set, but this remains outside the official BPC certificate path."
                    if complete
                    else "No negative was found by partial direct pricing; this is not exhaustive."
                ),
            }
        if duplicate and add_count == 0:
            return {
                "enabled": True,
                "status": "DIRECT_CG_DUPLICATE_NEGATIVE_COLUMN",
                "exact_status": "NOT_SOLVED",
                "round_count": round_index,
                "added_column_count": added_count,
                "final_rmp_status": rmp.status,
                "final_bound": rmp.objective_bound,
                "final_active_column_count": rmp.active_column_count,
                "history": history,
                "first_direct_pricing": first_pricing,
                "last_direct_pricing": pricing,
                "sortie_template_cache": cache.stats(),
                "integer_incumbent": _integer_incumbent_payload(data, columns),
                "note": "Direct pricing returned a negative column already present in the diagnostic pool.",
            }
    final_rmp = solve_restricted_journey_rmp(
        data.task_ids,
        columns,
        fleet_size=data.fleet_size,
        cut_context=cut_context,
        branch_context=branch_context,
    )
    integer_incumbent = _integer_incumbent_payload(data, columns)
    return {
        "enabled": True,
        "status": "DIRECT_CG_ROUND_LIMIT",
        "exact_status": "NOT_SOLVED",
        "round_count": int(max_rounds),
        "added_column_count": added_count,
        "final_rmp_status": final_rmp.status,
        "final_bound": final_rmp.objective_bound,
        "final_active_column_count": final_rmp.active_column_count,
        "history": history,
        "first_direct_pricing": first_pricing,
        "last_direct_pricing": last_pricing,
        "sortie_template_cache": cache.stats(),
        "integer_incumbent": integer_incumbent,
        "note": f"Stopped after max_rounds={max_rounds}; direct pricing may still find negative columns.",
    }


def _cache_payload(cache: DirectPricingCache | None) -> dict:
    if cache is None:
        return {"enabled": False}
    return cache.stats()


def _deadline_exceeded(deadline: float | None) -> bool:
    return deadline is not None and perf_counter() > float(deadline)


def _best_column_payload(column: JourneyColumn) -> dict:
    return {
        "task_count": len(column.task_set),
        "tasks": sorted(column.task_set),
        "objective": column.objective,
        "end_time": column.end_time,
        "sortie_count": len(column.sorties),
        "legs": [
            [
                {"from": leg.source, "to": leg.target, "path_type": leg.path_type}
                for leg in sortie.legs
            ]
            for sortie in column.sorties
        ],
    }


def _disabled_completion_bound_payload() -> dict:
    return {
        "enabled": False,
        "schema_version": "lunar_ice_bpc.completion_bound.v1",
        "bound_type": "positive_cover_dual_optimistic_tail",
        "pruning_is_exact_safe": True,
        "can_certify_no_negative": False,
        "pruned_label_count": 0,
        "evaluated_label_count": 0,
    }


def _aggregate_completion_bounds(rows: list[dict]) -> dict:
    if not rows:
        return _disabled_completion_bound_payload()
    first = rows[0]
    return {
        "enabled": any(bool(row.get("enabled")) for row in rows),
        "schema_version": "lunar_ice_bpc.completion_bound.v1",
        "bound_type": "positive_cover_dual_optimistic_tail",
        "candidate_count": len(rows),
        "pruned_label_count": sum(int(row.get("pruned_label_count") or 0) for row in rows),
        "evaluated_label_count": sum(int(row.get("evaluated_label_count") or 0) for row in rows),
        "includes_fleet_dual": False,
        "includes_cut_duals": False,
        "includes_branch_duals": False,
        "pruning_is_exact_safe": bool(first.get("pruning_is_exact_safe", True)),
        "can_certify_no_negative": False,
        "note": "Aggregated direct-label completion-bound diagnostics; not an official pricing certificate.",
    }


def _column_signature(column: JourneyColumn) -> tuple:
    return tuple(
        tuple((leg.source, leg.target, leg.path_type) for leg in sortie.legs)
        for sortie in column.sorties
    )


def _integer_incumbent_payload(data: LunarIceData, columns: list[JourneyColumn]) -> dict:
    selection = select_journey_column_pool(data.task_ids, columns, fleet_size=data.fleet_size)
    return {
        "status": selection.status,
        "objective": selection.objective,
        "journey_count": len(selection.columns),
        "candidate_column_count": selection.candidate_column_count,
        "unique_task_set_count": selection.unique_task_set_count,
        "state_count": selection.state_count,
        "journeys": [
            column.to_solution_payload(vehicle_id=f"rover_pool_{index + 1:02d}")
            for index, column in enumerate(selection.columns)
        ],
        "note": selection.note,
    }


def _incumbent_seed_task_sets(data: LunarIceData, columns: list[JourneyColumn]) -> tuple[tuple[str, ...], ...]:
    selection = select_journey_column_pool(data.task_ids, columns, fleet_size=data.fleet_size)
    return tuple(tuple(sorted(column.task_set)) for column in selection.columns)


def _merge_candidate_sets(
    data: LunarIceData,
    candidate_sets: tuple[tuple[str, ...], ...],
    seed_task_sets: tuple[tuple[str, ...], ...],
    *,
    max_candidate_task_count: int | None = None,
) -> tuple[tuple[str, ...], ...]:
    all_tasks = set(data.task_ids)
    max_size = (
        int(max_candidate_task_count)
        if max_candidate_task_count is not None
        else int(data.max_tasks_per_trip)
    )
    unique: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()

    def add(row: tuple[str, ...]) -> None:
        cleaned = tuple(str(task_id) for task_id in row if str(task_id) in all_tasks)
        normalized = tuple(sorted(cleaned))
        if cleaned and len(cleaned) <= max_size and normalized not in seen:
            seen.add(normalized)
            unique.append(cleaned)

    for row in candidate_sets:
        add(row)
    for row in seed_task_sets:
        add(row)
    return tuple(unique)


def _all_nonempty_task_subsets(data: LunarIceData) -> tuple[tuple[str, ...], ...]:
    ordered = tuple(sorted(data.task_ids))
    limit = min(len(ordered), int(data.max_tasks_per_trip))
    rows: list[tuple[str, ...]] = []
    for size in range(1, limit + 1):
        rows.extend(tuple(row) for row in combinations(ordered, size))
    return tuple(rows)


def _enumerate_direct_sortie_templates(
    data: LunarIceData,
    candidate_task_ids: tuple[str, ...],
    task_to_bit: dict[str, int],
) -> tuple[dict[int, tuple[_DirectSortieTemplate, ...]], int]:
    templates_by_mask: dict[int, list[_DirectSortieTemplate]] = {}
    attempt_count = 0
    ordered = tuple(sorted(candidate_task_ids))
    limit = min(len(ordered), int(data.max_tasks_per_trip))
    path_type_cache = _nondominated_path_type_cache(data)
    for length in range(1, limit + 1):
        for sequence in permutations(ordered, length):
            task_mask = 0
            for task_id in sequence:
                task_mask |= task_to_bit[task_id]
            for path_types in _direct_path_type_assignments(data, sequence, path_type_cache):
                attempt_count += 1
                if not build_timed_sortie(data, sequence, tuple(path_types), start_time=0.0).feasible:
                    continue
                templates_by_mask.setdefault(task_mask, []).append(
                    _DirectSortieTemplate(
                        task_mask=task_mask,
                        sequence=tuple(sequence),
                        path_types=tuple(path_types),
                    )
                )
    return {mask: tuple(templates) for mask, templates in templates_by_mask.items()}, attempt_count


def _direct_path_type_assignments(
    data: LunarIceData,
    sequence: tuple[str, ...],
    path_type_cache: dict[tuple[str, str], tuple[str, ...]],
) -> Iterable[tuple[str, ...]]:
    current = "depot"
    per_leg: list[tuple[str, ...]] = []
    for task_id in sequence:
        per_leg.append(path_type_cache[(current, task_id)])
        current = task_id
    per_leg.append(path_type_cache[(current, "depot")])
    yield from product(*per_leg)


def _best_direct_label(
    data: LunarIceData,
    duals: JourneyDuals,
    candidate_task_ids: tuple[str, ...],
    templates_by_mask: dict[int, tuple[_DirectSortieTemplate, ...]],
    *,
    completion_bound_enabled: bool = True,
    cut_context: CutContext | None = None,
) -> tuple[_DirectJourneyLabel | None, _DirectJourneyLabel | None, int, dict]:
    task_index = TaskIndexMap(candidate_task_ids)
    full_mask = task_index.full_mask
    context = cut_context or CutContext()
    task_by_bit = {task_index.mask_of(task_id): task_id for task_id in task_index.external_ids}
    completion_bound = build_positive_cover_completion_bound(candidate_task_ids, duals.cover)
    completion_payload = completion_bound.to_payload()
    completion_payload["enabled"] = bool(completion_bound_enabled)
    completion_payload["pruned_label_count"] = 0
    completion_payload["evaluated_label_count"] = 0
    labels_by_mask: dict[int, list[_DirectJourneyLabel]] = {
        0: [_DirectJourneyLabel(task_mask=0, sorties=tuple(), end_time=0.0, reduced_base=0.0)]
    }
    best: _DirectJourneyLabel | None = None
    for current_mask in range(full_mask + 1):
        current_labels = list(labels_by_mask.get(current_mask, []))
        if not current_labels:
            continue
        remaining_mask = full_mask ^ current_mask
        expandable_labels: list[_DirectJourneyLabel] = []
        for label in current_labels:
            completion_payload["evaluated_label_count"] += 1
            if not completion_bound_enabled or best is None or current_mask == full_mask:
                expandable_labels.append(label)
                continue
            remaining_tasks = tuple(
                task_id
                for bit, task_id in task_by_bit.items()
                if remaining_mask & bit
            )
            optimistic_without_fleet = completion_bound.optimistic_label_bound(
                current_reduced_base=label.reduced_base,
                current_end_time=label.end_time,
                beta_journey_end_time=0.0,
                remaining_task_ids=remaining_tasks,
            )
            optimistic_with_fleet = round(optimistic_without_fleet - float(duals.fleet_limit), 9)
            if optimistic_with_fleet >= best.reduced_cost(
                data,
                duals,
                cut_context=context,
                candidate_task_ids=candidate_task_ids,
            ) - 1.0e-9:
                completion_payload["pruned_label_count"] += 1
                continue
            expandable_labels.append(label)
        if not expandable_labels:
            continue
        submask = remaining_mask
        while submask:
            for template in templates_by_mask.get(submask, []):
                for label in expandable_labels:
                    sortie = build_timed_sortie(data, template.sequence, template.path_types, start_time=label.end_time)
                    if not sortie.feasible:
                        continue
                    candidate = _extend_direct_label(data, duals, label, sortie, template.task_mask)
                    _add_direct_pareto_label(labels_by_mask.setdefault(current_mask | submask, []), candidate)
                    if candidate.task_mask and (
                        best is None
                        or candidate.reduced_cost(
                            data,
                            duals,
                            cut_context=context,
                            candidate_task_ids=candidate_task_ids,
                        )
                        < best.reduced_cost(
                            data,
                            duals,
                            cut_context=context,
                            candidate_task_ids=candidate_task_ids,
                        )
                        - 1.0e-9
                    ):
                        best = candidate
            submask = (submask - 1) & remaining_mask
    pareto_count = sum(len(labels) for mask, labels in labels_by_mask.items() if mask)
    full_labels = labels_by_mask.get(full_mask, [])
    best_full: _DirectJourneyLabel | None = None
    if full_labels:
        best_full = min(
            full_labels,
            key=lambda label: (
                build_journey_column(data, label.sorties).objective,
                label.end_time,
                len(label.sorties),
            ),
        )
    return best, best_full, pareto_count, completion_payload


def _best_direct_label_incremental(
    data: LunarIceData,
    duals: JourneyDuals,
    candidate_task_ids: tuple[str, ...],
    *,
    deadline: float | None = None,
    cut_context: CutContext | None = None,
) -> tuple[_DirectJourneyLabel | None, dict]:
    task_index = TaskIndexMap(candidate_task_ids)
    full_mask = task_index.full_mask
    task_to_bit = {task_id: task_index.mask_of(task_id) for task_id in task_index.external_ids}
    context = cut_context or CutContext()
    path_type_cache = _nondominated_path_type_cache(data)
    path_type_lb_cache = _path_type_lower_bound_cache(data, path_type_cache)
    labels_by_mask: dict[int, list[_DirectJourneyLabel]] = {
        0: [_DirectJourneyLabel(task_mask=0, sorties=tuple(), end_time=0.0, reduced_base=0.0)]
    }
    pending_masks = [0]
    queued_masks = {0}
    processed_masks: set[int] = set()
    generated_sortie_count = 0
    route_template_count = 0
    best: _DirectJourneyLabel | None = None

    while pending_masks:
        if _deadline_exceeded(deadline):
            raise DirectBaselineTimeLimitExceeded(
                stage="incremental_journey_label_dp",
                generated_sortie_count=generated_sortie_count,
                route_template_count=route_template_count,
                pareto_label_count=sum(len(labels) for mask, labels in labels_by_mask.items() if mask),
            )
        current_mask = heapq.heappop(pending_masks)
        if current_mask in processed_masks:
            continue
        processed_masks.add(current_mask)
        current_labels = list(labels_by_mask.get(current_mask, []))
        if not current_labels:
            continue
        remaining_mask = full_mask ^ current_mask
        if remaining_mask == 0:
            continue
        for label_index, label in enumerate(current_labels):
            if label_index % 32 == 0 and _deadline_exceeded(deadline):
                raise DirectBaselineTimeLimitExceeded(
                    stage="incremental_journey_label_dp",
                    generated_sortie_count=generated_sortie_count,
                    route_template_count=route_template_count,
                    pareto_label_count=sum(len(labels) for mask, labels in labels_by_mask.items() if mask),
                )
            try:
                candidates, generated_count, route_count, _ = _direct_sortie_candidates_from_start(
                    data,
                    task_to_bit,
                    remaining_mask=remaining_mask,
                    start_time=float(label.end_time),
                    deadline=deadline,
                    path_type_cache=path_type_cache,
                    path_type_lb_cache=path_type_lb_cache,
                )
            except DirectBaselineTimeLimitExceeded as exc:
                raise DirectBaselineTimeLimitExceeded(
                    stage=f"sortie_candidate_generation:{exc.stage}",
                    generated_sortie_count=generated_sortie_count + int(exc.generated_sortie_count),
                    route_template_count=route_template_count + int(exc.route_template_count),
                    pareto_label_count=sum(len(labels) for mask, labels in labels_by_mask.items() if mask),
                ) from exc
            generated_sortie_count += int(generated_count)
            route_template_count += int(route_count)
            for candidate_index, candidate in enumerate(candidates):
                if candidate_index % 1024 == 0 and _deadline_exceeded(deadline):
                    raise DirectBaselineTimeLimitExceeded(
                        stage="incremental_candidate_extension",
                        generated_sortie_count=generated_sortie_count,
                        route_template_count=route_template_count,
                        pareto_label_count=sum(len(labels) for mask, labels in labels_by_mask.items() if mask),
                    )
                if candidate.task_mask & current_mask:
                    continue
                new_mask = current_mask | candidate.task_mask
                if new_mask == current_mask:
                    continue
                if new_mask not in queued_masks:
                    heapq.heappush(pending_masks, new_mask)
                    queued_masks.add(new_mask)
                new_label = _extend_direct_label(data, duals, label, candidate.sortie, candidate.task_mask)
                _add_direct_pareto_label(labels_by_mask.setdefault(new_mask, []), new_label)
                if (
                    best is None
                    or new_label.reduced_cost(
                        data,
                        duals,
                        cut_context=context,
                        candidate_task_ids=candidate_task_ids,
                    )
                    < best.reduced_cost(
                        data,
                        duals,
                        cut_context=context,
                        candidate_task_ids=candidate_task_ids,
                    )
                    - 1.0e-9
                ):
                    best = new_label

    stats = {
        "sortie_attempt_count": int(generated_sortie_count),
        "feasible_sortie_template_count": int(route_template_count),
        "pareto_label_count": sum(len(labels) for mask, labels in labels_by_mask.items() if mask),
    }
    return best, stats


def _select_direct_candidate_sets(data: LunarIceData, duals: JourneyDuals, limit: int) -> tuple[tuple[str, ...], ...]:
    if int(limit) <= 0:
        return tuple()
    all_tasks = tuple(sorted(data.task_ids))
    all_task_set = set(all_tasks)
    ranked_primary = _rank_direct_candidate_tasks(data, duals, mode="primary")
    ranked_cover = _rank_direct_candidate_tasks(data, duals, mode="cover")
    ranked_science = _rank_direct_candidate_tasks(data, duals, mode="science")
    ranked_spatial = _rank_direct_candidate_tasks(data, duals, mode="spatial")
    unique: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()

    def add(row: tuple[str, ...]) -> None:
        normalized = tuple(sorted(row))
        if row and normalized not in seen:
            seen.add(normalized)
            unique.append(row)

    base_rows = [
        tuple(ranked_primary[: int(limit)]),
        tuple(ranked_cover[: int(limit)]),
        tuple(ranked_science[: int(limit)]),
        tuple(ranked_spatial[: int(limit)]),
    ]
    for ranked in (ranked_primary, ranked_cover, ranked_science, ranked_spatial):
        for start in range(0, len(ranked), int(limit)):
            base_rows.append(tuple(ranked[start : start + int(limit)]))
    for row in base_rows:
        add(row)
        complement = tuple(task_id for task_id in all_tasks if task_id not in set(row))
        if 0 < len(complement) <= int(limit):
            add(complement)
    return tuple(unique)


def _rank_direct_candidate_tasks(data: LunarIceData, duals: JourneyDuals, *, mode: str) -> list[str]:
    depot_xy = data.depot_xy_km
    ranked: list[tuple[float, str]] = []
    for task_id in data.task_ids:
        task = data.tasks[task_id]
        distance_proxy = ((task.xy_km[0] - depot_xy[0]) ** 2 + (task.xy_km[1] - depot_xy[1]) ** 2) ** 0.5
        if mode == "cover":
            score = float(duals.cover.get(task_id, 0.0))
        elif mode == "science":
            score = float(task.science_weight)
        elif mode == "spatial":
            score = -distance_proxy
        else:
            score = _direct_candidate_primary_score(data, duals, task_id)
        ranked.append((score, task_id))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [task_id for _, task_id in ranked]


def _direct_candidate_primary_score(data: LunarIceData, duals: JourneyDuals, task_id: str) -> float:
    depot = "depot"
    task = data.tasks[task_id]
    best_out = min(
        data.option(depot, task_id, path_type).travel_time_min + data.option(task_id, depot, path_type).travel_time_min
        for path_type in PATH_TYPES
    )
    rough_cost = additive_objective_value(
        data,
        operating_cost=operating_cost_value(
            service_cost=float(task.service_cost),
            distance_km=0.0,
            energy_proxy=float(task.service_energy),
        ),
        risk_integral=service_risk_value(task),
        weighted_completion_time=float(task.science_weight) * (best_out + float(task.service_time)),
    )
    return float(duals.cover.get(task_id, 0.0)) - 0.01 * rough_cost


def _extend_direct_label(
    data: LunarIceData,
    duals: JourneyDuals,
    label: _DirectJourneyLabel,
    sortie: TimedSortie,
    task_mask: int,
) -> _DirectJourneyLabel:
    cover_reward = sum(float(duals.cover.get(task_id, 0.0)) for task_id in sortie.tasks)
    add_base = sortie_objective_value(data, sortie) - cover_reward
    return _DirectJourneyLabel(
        task_mask=label.task_mask | task_mask,
        sorties=(*label.sorties, sortie),
        end_time=sortie.end_time,
        reduced_base=round(label.reduced_base + add_base, 9),
    )


def _label_cut_dual_penalty(
    label: _DirectJourneyLabel,
    duals: JourneyDuals,
    cut_context: CutContext | None,
    candidate_task_ids: tuple[str, ...],
) -> float:
    if cut_context is None or cut_context.empty or not duals.cuts:
        return 0.0
    task_index = TaskIndexMap(candidate_task_ids)
    tasks = set(task_index.ids_from_mask(label.task_mask))
    if not tasks:
        return 0.0
    penalty = 0.0
    for cut in cut_context.cuts:
        if cut.cut_type == SUBSET_ROW_CUT:
            coefficient = float(len(tasks.intersection(cut.tasks)) // int(cut.divisor))
        elif cut.cut_type == FLEET_LOWER_BOUND_CUT:
            coefficient = 1.0
        else:
            continue
        if abs(coefficient) <= 1.0e-12:
            continue
        penalty += float(duals.cuts.get(cut.cut_id, 0.0)) * coefficient
    return penalty


def _add_direct_pareto_label(labels: list[_DirectJourneyLabel], candidate: _DirectJourneyLabel) -> None:
    kept: list[_DirectJourneyLabel] = []
    for old in labels:
        if old.end_time <= candidate.end_time + 1.0e-9 and old.reduced_base <= candidate.reduced_base + 1.0e-9:
            return
        if candidate.end_time <= old.end_time + 1.0e-9 and candidate.reduced_base <= old.reduced_base + 1.0e-9:
            continue
        kept.append(old)
    kept.append(candidate)
    labels[:] = kept
