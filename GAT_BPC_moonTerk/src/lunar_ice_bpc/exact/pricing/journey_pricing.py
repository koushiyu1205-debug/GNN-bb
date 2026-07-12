"""Pricing routines for restricted and direct-label journey diagnostics."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
import heapq
from itertools import combinations, permutations, product
from time import perf_counter

from lunar_ice_bpc.domain.scenario import PATH_TYPES
from lunar_ice_bpc.exact.bpc.core.task_index import TaskIndexMap
from lunar_ice_bpc.exact.core.columns import TimedSortie, build_timed_sortie
from lunar_ice_bpc.exact.core.branching import (
    DIFFERENT_JOURNEY,
    SAME_JOURNEY,
    BranchContext,
    journey_satisfies_branch_context,
)
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
    _direct_sortie_cache_limit,
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
        *,
        deadline: float | None = None,
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
        templates_by_mask, attempt_count = _enumerate_direct_sortie_templates(
            data,
            candidate_key,
            task_to_bit,
            deadline=deadline,
        )
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
    wall_time_limit_sec: float | None = None,
    completion_bound_enabled: bool = True,
    cut_context: CutContext | None = None,
    branch_context: BranchContext | None = None,
) -> tuple[dict, tuple[JourneyColumn, ...]]:
    """Return best direct-label column per candidate task set."""

    all_task_ids = tuple(data.task_ids)
    context = cut_context or CutContext()
    branch = branch_context or BranchContext()
    start = perf_counter()
    deadline = None if wall_time_limit_sec is None else start + max(0.0, float(wall_time_limit_sec))
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
    raw_candidate_set_count = len(candidate_sets)
    candidate_sets = _filter_candidate_sets_by_branch_context(candidate_sets, branch)
    branch_filtered_candidate_set_count = raw_candidate_set_count - len(candidate_sets)
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
        if _deadline_exceeded(deadline):
            return _direct_label_time_limit_payload(
                data,
                context=context,
                branch=branch,
                max_direct_tasks=max_direct_tasks,
                candidate_sets=candidate_sets,
                candidate_summaries=candidate_summaries,
                attempt_count=attempt_count,
                feasible_template_count=feasible_template_count,
                pareto_count=pareto_count,
                branch_filtered_count=branch_filtered_count,
                branch_filtered_candidate_set_count=branch_filtered_candidate_set_count,
                timeout_stage="candidate_loop",
                completion_summaries=completion_summaries,
                cache=cache,
                started_at=start,
            ), tuple(column for _, _, column in priced_columns)
        if cache is None:
            priced_candidate_task_ids = tuple(sorted(candidate_task_ids))
            task_index = TaskIndexMap(priced_candidate_task_ids)
            task_to_bit = {task_id: task_index.mask_of(task_id) for task_id in task_index.external_ids}
            try:
                templates_by_mask, attempts = _enumerate_direct_sortie_templates(
                    data,
                    priced_candidate_task_ids,
                    task_to_bit,
                    deadline=deadline,
                )
            except DirectBaselineTimeLimitExceeded as exc:
                return _direct_label_time_limit_payload(
                    data,
                    context=context,
                    branch=branch,
                    max_direct_tasks=max_direct_tasks,
                    candidate_sets=candidate_sets,
                    candidate_summaries=candidate_summaries,
                    attempt_count=attempt_count + int(exc.generated_sortie_count),
                    feasible_template_count=feasible_template_count + int(exc.route_template_count),
                    pareto_count=pareto_count + int(exc.pareto_label_count),
                    branch_filtered_count=branch_filtered_count,
                    branch_filtered_candidate_set_count=branch_filtered_candidate_set_count,
                    timeout_stage=f"sortie_template_enumeration:{exc.stage}",
                    completion_summaries=completion_summaries,
                    cache=cache,
                    started_at=start,
                ), tuple(column for _, _, column in priced_columns)
            cache_hit = False
        else:
            try:
                priced_candidate_task_ids, templates_by_mask, attempts, cache_hit = cache.get_or_build(
                    data,
                    candidate_task_ids,
                    deadline=deadline,
                )
            except DirectBaselineTimeLimitExceeded as exc:
                return _direct_label_time_limit_payload(
                    data,
                    context=context,
                    branch=branch,
                    max_direct_tasks=max_direct_tasks,
                    candidate_sets=candidate_sets,
                    candidate_summaries=candidate_summaries,
                    attempt_count=attempt_count + int(exc.generated_sortie_count),
                    feasible_template_count=feasible_template_count + int(exc.route_template_count),
                    pareto_count=pareto_count + int(exc.pareto_label_count),
                    branch_filtered_count=branch_filtered_count,
                    branch_filtered_candidate_set_count=branch_filtered_candidate_set_count,
                    timeout_stage=f"sortie_template_cache:{exc.stage}",
                    completion_summaries=completion_summaries,
                    cache=cache,
                    started_at=start,
                ), tuple(column for _, _, column in priced_columns)
        try:
            candidate_label, full_label, candidate_pareto_count, completion_payload = _best_direct_label(
                data,
                duals,
                priced_candidate_task_ids,
                templates_by_mask,
                deadline=deadline,
                completion_bound_enabled=bool(completion_bound_enabled) and context.empty and branch.empty,
                cut_context=context,
            )
        except DirectBaselineTimeLimitExceeded as exc:
            return _direct_label_time_limit_payload(
                data,
                context=context,
                branch=branch,
                max_direct_tasks=max_direct_tasks,
                candidate_sets=candidate_sets,
                candidate_summaries=candidate_summaries,
                attempt_count=attempt_count + attempts + int(exc.generated_sortie_count),
                feasible_template_count=feasible_template_count + int(exc.route_template_count),
                pareto_count=pareto_count + int(exc.pareto_label_count),
                branch_filtered_count=branch_filtered_count,
                branch_filtered_candidate_set_count=branch_filtered_candidate_set_count,
                timeout_stage=f"direct_label_dp:{exc.stage}",
                completion_summaries=completion_summaries,
                cache=cache,
                started_at=start,
            ), tuple(column for _, _, column in priced_columns)
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
            "branch_filtered_candidate_set_count": int(branch_filtered_candidate_set_count),
            "branch_filtered_column_count": branch_filtered_count,
            "completion_bound": _aggregate_completion_bounds(completion_summaries),
            "sortie_template_cache": _cache_payload(cache),
            "can_certify_no_negative": False,
            "uses_true_dual_bpc_certificate": False,
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
        "branch_filtered_candidate_set_count": int(branch_filtered_candidate_set_count),
        "branch_filtered_column_count": branch_filtered_count,
        "completion_bound": _aggregate_completion_bounds(completion_summaries),
        "sortie_template_cache": _cache_payload(cache),
        "can_certify_no_negative": False,
        "uses_true_dual_bpc_certificate": False,
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
    negative_harvest_target: int = 1,
    completion_bound_enabled: bool = True,
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
    negative_harvest_target = max(1, int(negative_harvest_target))
    candidate_sets = _select_direct_candidate_sets(data, duals, int(max_direct_tasks))
    candidate_sets = _merge_candidate_sets(
        data,
        seed_task_sets,
        candidate_sets,
        max_candidate_task_count=int(max_direct_tasks),
    )
    raw_candidate_set_count = len(candidate_sets)
    candidate_sets = _filter_candidate_sets_by_branch_context(candidate_sets, branch)
    branch_filtered_candidate_set_count = raw_candidate_set_count - len(candidate_sets)
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
    completion_summaries: list[dict] = []
    active_completion_bound = bool(completion_bound_enabled) and context.empty and branch.empty

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
                completion_bound_enabled=active_completion_bound,
                cut_context=context,
                branch_context=branch,
                negative_eps=negative_eps,
                stop_at_first_negative=bool(stop_at_first_negative),
                negative_harvest_target=1,
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
        completion_payload = stats.get("completion_bound")
        if isinstance(completion_payload, dict):
            completion_summaries.append(completion_payload)
        summary = {
            "candidate_task_ids": list(candidate_task_ids),
            "sortie_attempt_count": int(stats["sortie_attempt_count"]),
            "feasible_sortie_template_count": int(stats["feasible_sortie_template_count"]),
            "pareto_label_count": int(stats["pareto_label_count"]),
            "best_reduced_cost": None,
            "negative_found": False,
            "branch_feasible": None,
            "completion_bound": completion_payload or _disabled_completion_bound_payload(),
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
                negative_count = sum(
                    1 for existing_rc, _, _column in priced_columns
                    if existing_rc < -abs(float(negative_eps))
                )
                if (
                    bool(stop_at_first_negative)
                    and rc < -abs(float(negative_eps))
                    and negative_count >= negative_harvest_target
                ):
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
        "negative_harvest_target": int(negative_harvest_target),
        "negative_harvest_early_stop_enabled": bool(stop_at_first_negative),
        "negative_harvest_early_stop_triggered": bool(
            stop_at_first_negative and len(negative_columns) >= negative_harvest_target
        ),
        "candidate_label_early_negative_stop_enabled": bool(stop_at_first_negative),
        "branch_context_active": not branch.empty,
        "branch_decision_count": len(branch.pair_decisions),
        "branch_filtered_candidate_set_count": int(branch_filtered_candidate_set_count),
        "branch_filtered_column_count": branch_filtered_count,
        "cut_context_active": not context.empty,
        "cut_count": len(context.cuts),
        "completion_bound": _aggregate_completion_bounds(completion_summaries),
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


def price_full_universe_incremental_journey_columns(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    negative_eps: float = 1.0e-6,
    max_direct_tasks: int = 12,
    max_returned_columns: int = 1,
    wall_time_limit_sec: float | None = None,
    completion_bound_enabled: bool = True,
    cut_context: CutContext | None = None,
    branch_context: BranchContext | None = None,
    stop_at_first_negative: bool = False,
    active_task_sets_for_harvest: Iterable[Iterable[str]] | None = None,
) -> tuple[dict, tuple[JourneyColumn, ...]]:
    """Price the full task universe with one incremental resource-label DP.

    This is a proof precursor toward a mature SPPRC final judge.  For a cut-free
    fixed graph within ``max_direct_tasks``, the incremental label search over
    the full task universe can find the minimum reduced-cost journey over all
    nonempty task subsets without running one pricing call per subset.  Branch
    decisions are applied only when a complete label is eligible to become the
    best priced column, so partial labels that may later satisfy SAME_JOURNEY are
    not pruned too early.  The routine remains fail-closed: it does not itself
    claim a BPC certificate.
    """

    start = perf_counter()
    context = cut_context or CutContext()
    branch = branch_context or BranchContext()
    task_ids = tuple(sorted(str(task_id) for task_id in data.task_ids))
    if len(task_ids) > int(max_direct_tasks):
        return _full_universe_incremental_fail_payload(
            data,
            status="SKIPPED_TOO_LARGE_FOR_FULL_UNIVERSE_INCREMENTAL_LABEL_PRICING",
            max_direct_tasks=max_direct_tasks,
            started_at=start,
            note=f"task_count={len(task_ids)} exceeds max_direct_tasks={max_direct_tasks}; fail closed.",
        ), tuple()
    if not task_ids:
        return _full_universe_incremental_fail_payload(
            data,
            status="EMPTY_FULL_UNIVERSE_INCREMENTAL_LABEL_PRICING",
            max_direct_tasks=max_direct_tasks,
            started_at=start,
            note="No tasks are present; no pricing column can be generated.",
        ), tuple()
    if not context.empty:
        payload = _full_universe_incremental_fail_payload(
            data,
            status="SKIPPED_CUT_CONTEXT_FOR_FULL_UNIVERSE_INCREMENTAL_LABEL_PRICING",
            max_direct_tasks=max_direct_tasks,
            started_at=start,
            note="Full-universe incremental label proof with live cuts is not yet enabled; fail closed.",
        )
        payload["cut_context_active"] = True
        payload["cut_count"] = len(context.cuts)
        return payload, tuple()

    deadline = None if wall_time_limit_sec is None else start + max(0.0, float(wall_time_limit_sec))
    try:
        label, stats = _best_direct_label_incremental(
            data,
            duals,
            task_ids,
            deadline=deadline,
            completion_bound_enabled=bool(completion_bound_enabled) and branch.empty,
            cut_context=context,
            branch_context=branch,
            negative_eps=negative_eps,
            stop_at_first_negative=bool(stop_at_first_negative),
            negative_harvest_target=max_returned_columns,
            active_task_sets_for_harvest=active_task_sets_for_harvest,
        )
    except DirectBaselineTimeLimitExceeded as exc:
        payload = _full_universe_incremental_fail_payload(
            data,
            status="FULL_UNIVERSE_INCREMENTAL_LABEL_TIME_LIMIT",
            max_direct_tasks=max_direct_tasks,
            started_at=start,
            note="Full-universe incremental label pricing exceeded its time budget; fail closed.",
        )
        partial_stats = dict(getattr(exc, "partial_stats", {}) or {})
        partial_labels = tuple(partial_stats.get("_all_pareto_labels") or tuple())
        partial_best_label = getattr(exc, "partial_label", None)
        if partial_best_label is None and partial_labels:
            branch_feasible_partial_labels = tuple(
                label
                for label in partial_labels
                if _label_satisfies_branch_context(label, TaskIndexMap(task_ids), branch)
            )
            if branch_feasible_partial_labels:
                partial_best_label = min(
                    branch_feasible_partial_labels,
                    key=lambda label: label.reduced_cost(
                        data,
                        duals,
                        cut_context=context,
                        candidate_task_ids=task_ids,
                    ),
                )
        returned_columns: tuple[JourneyColumn, ...] = tuple()
        harvest_payload: dict = {}
        if partial_best_label is not None:
            returned_columns, harvest_payload = _select_full_universe_incremental_return_columns(
                data,
                duals,
                partial_labels or (partial_best_label,),
                best_label=partial_best_label,
                candidate_task_ids=task_ids,
                branch_context=branch,
                cut_context=context,
                negative_eps=negative_eps,
                max_returned_columns=max_returned_columns,
                active_task_sets=active_task_sets_for_harvest,
            )
            payload.update(harvest_payload)
            payload["returned_column_count"] = len(returned_columns)
            payload["returned_column_policy"] = harvest_payload.get("returned_column_policy", "")
            payload["returned_column_semantics"] = (
                "partial_timeout_negative_columns_from_incremental_labeling"
                if returned_columns
                else "partial_timeout_no_columns_returned"
            )
            payload["partial_timeout_returned_column_count"] = len(returned_columns)
            payload["partial_timeout_negative_harvest_enabled"] = True
        else:
            payload["returned_column_count"] = 0
            payload["returned_column_policy"] = "none"
            payload["returned_column_semantics"] = "timeout_before_any_branch_feasible_label"
            payload["partial_timeout_returned_column_count"] = 0
            payload["partial_timeout_negative_harvest_enabled"] = False
        payload["timeout_stage"] = exc.stage
        payload["sortie_attempt_count"] = int(exc.generated_sortie_count)
        payload["feasible_sortie_template_count"] = int(exc.route_template_count)
        payload["pareto_label_count"] = int(exc.pareto_label_count)
        payload["observed_task_mask_count_by_task_count"] = dict(
            partial_stats.get("observed_task_mask_count_by_task_count") or {}
        )
        payload["processed_task_mask_count_by_task_count"] = dict(
            partial_stats.get("processed_task_mask_count_by_task_count") or {}
        )
        payload["pending_task_mask_count_by_task_count"] = dict(
            partial_stats.get("pending_task_mask_count_by_task_count") or {}
        )
        payload["branch_context_active"] = not branch.empty
        payload["branch_decision_count"] = len(branch.pair_decisions)
        return payload, returned_columns
    if label is None:
        payload = _full_universe_incremental_fail_payload(
            data,
            status="FULL_UNIVERSE_INCREMENTAL_LABEL_NO_COLUMN",
            max_direct_tasks=max_direct_tasks,
            started_at=start,
            note="No full-universe incremental label was generated; fail closed.",
        )
        payload["completion_bound"] = stats.get("completion_bound") or _disabled_completion_bound_payload()
        payload["branch_context_active"] = not branch.empty
        payload["branch_decision_count"] = len(branch.pair_decisions)
        return payload, tuple()

    column = build_journey_column(data, label.sorties)
    rc = manual_journey_reduced_cost(column, duals, cut_coefficients=context.coefficients_for(column))
    returned_columns, harvest_payload = _select_full_universe_incremental_return_columns(
        data,
        duals,
        tuple(stats.get("_all_pareto_labels") or (label,)),
        best_label=label,
        candidate_task_ids=task_ids,
        branch_context=branch,
        cut_context=context,
        negative_eps=negative_eps,
        max_returned_columns=max_returned_columns,
        active_task_sets=active_task_sets_for_harvest,
    )
    candidate_sets = _all_nonempty_task_subsets(data)
    early_negative_stop = bool(stats.get("early_negative_stop"))
    global_min_proof_complete = not early_negative_stop
    priced_count_by_task_count = (
        _candidate_set_count_by_task_count(candidate_sets)
        if global_min_proof_complete
        else dict(stats.get("observed_task_mask_count_by_task_count") or {})
    )
    payload = {
        "status": (
            "FULL_UNIVERSE_INCREMENTAL_LABEL_FOUND_NEGATIVE_EARLY"
            if early_negative_stop
            else "FULL_UNIVERSE_INCREMENTAL_LABEL_PRICED"
        ),
        "exact_status": "NOT_BPC_CERTIFIED",
        "task_count": len(task_ids),
        "max_direct_tasks": int(max_direct_tasks),
        "candidate_round_count": 1,
        "candidate_round_limit": 1,
        "candidate_task_count": len(task_ids),
        "candidate_task_ids": list(task_ids),
        "candidate_sets": [list(task_ids)],
        "candidate_set_count_by_task_count": _candidate_set_count_by_task_count(candidate_sets),
        "priced_candidate_set_count_by_task_count": priced_count_by_task_count,
        "search_region_count": len(candidate_sets),
        "search_region_count_by_task_count": _candidate_set_count_by_task_count(candidate_sets),
        "search_region_count_semantics": "all_nonempty_task_subsets_covered_by_one_incremental_label_dp",
        "returned_column_count": len(returned_columns),
        "returned_column_policy": harvest_payload["returned_column_policy"],
        "returned_column_semantics": harvest_payload["returned_column_semantics"],
        "returned_columns_are_complete_universe": False,
        **harvest_payload,
        "pricing_complete_for_all_tasks": bool(global_min_proof_complete),
        "pricing_complete_for_all_task_subsets": bool(global_min_proof_complete),
        "pricing_complete_for_branch_context": bool(global_min_proof_complete),
        "pricing_coverage_algorithm": "full_universe_incremental_label",
        "full_universe_incremental_label": True,
        "global_min_proof_complete": bool(global_min_proof_complete),
        "global_min_reduced_cost": rc if global_min_proof_complete else None,
        "global_min_reduced_cost_source": (
            "full_universe_incremental_label_dp"
            if global_min_proof_complete
            else "partial_incremental_label_dp_found_negative"
        ),
        "global_min_reduced_cost_scope": (
            "branch_feasible_nonempty_task_subsets"
            if global_min_proof_complete and not branch.empty
            else "partial_branch_feasible_observed_labels"
            if early_negative_stop and not branch.empty
            else "partial_observed_labels"
            if early_negative_stop
            else "all_nonempty_task_subsets"
        ),
        "global_min_proof_requires_true_dual_reaudit": True,
        "sortie_attempt_count": int(stats.get("sortie_attempt_count") or 0),
        "feasible_sortie_template_count": int(stats.get("feasible_sortie_template_count") or 0),
        "pareto_label_count": int(stats.get("pareto_label_count") or 0),
        "label_expansion_order_policy": stats.get("label_expansion_order_policy") or "",
        "label_best_bound_order_enabled": bool(stats.get("label_best_bound_order_enabled")),
        "label_queue_push_count": int(stats.get("label_queue_push_count") or 0),
        "label_queue_stale_pop_count": int(stats.get("label_queue_stale_pop_count") or 0),
        "label_queue_max_pending_count": int(stats.get("label_queue_max_pending_count") or 0),
        "sortie_candidate_cache_enabled": bool(stats.get("sortie_candidate_cache_enabled")),
        "sortie_candidate_cache_limit": stats.get("sortie_candidate_cache_limit"),
        "sortie_candidate_cache_entry_count": int(stats.get("sortie_candidate_cache_entry_count") or 0),
        "sortie_candidate_cache_hit_count": int(stats.get("sortie_candidate_cache_hit_count") or 0),
        "sortie_candidate_cache_miss_count": int(stats.get("sortie_candidate_cache_miss_count") or 0),
        "sortie_candidate_cache_reused_candidate_count": int(
            stats.get("sortie_candidate_cache_reused_candidate_count") or 0
        ),
        "early_negative_stop": bool(early_negative_stop),
        "early_negative_stop_can_certify_no_negative": False,
        "early_negative_stop_trigger_count": int(stats.get("early_negative_stop_trigger_count") or 0),
        "early_negative_distinct_task_set_stop_enabled": bool(
            stats.get("early_negative_distinct_task_set_stop_enabled")
        ),
        "early_negative_distinct_task_set_count": int(
            stats.get("early_negative_distinct_task_set_count") or 0
        ),
        "early_negative_preferred_task_set_count": int(
            stats.get("early_negative_preferred_task_set_count") or 0
        ),
        "early_negative_active_task_set_reference_count": int(
            stats.get("early_negative_active_task_set_reference_count") or 0
        ),
        "early_negative_active_preference_required": bool(
            stats.get("early_negative_active_preference_required")
        ),
        "early_negative_raw_stop_cap": int(stats.get("early_negative_raw_stop_cap") or 0),
        "observed_task_mask_count_by_task_count": dict(
            stats.get("observed_task_mask_count_by_task_count") or {}
        ),
        "processed_task_mask_count_by_task_count": dict(
            stats.get("processed_task_mask_count_by_task_count") or {}
        ),
        "pending_task_mask_count_by_task_count": dict(
            stats.get("pending_task_mask_count_by_task_count") or {}
        ),
        "best_reduced_cost": rc,
        "negative_found": bool(rc < -abs(float(negative_eps))),
        "negative_column_count": int(harvest_payload["exact_negative_harvest_candidate_count"]),
        "returned_negative_column_count": int(harvest_payload["exact_negative_harvest_selected_count"]),
        "cut_context_active": False,
        "cut_count": 0,
        "branch_context_active": not branch.empty,
        "branch_decision_count": len(branch.pair_decisions),
        "branch_filtered_candidate_set_count": 0,
        "branch_filtered_column_count": 0,
        "completion_bound": stats.get("completion_bound") or _disabled_completion_bound_payload(),
        "can_certify_no_negative": False,
        "uses_true_dual_bpc_certificate": False,
        "timeout_stage": "",
        "wall_time_sec": round(perf_counter() - start, 6),
        "best_column": _best_column_payload(column),
        "note": (
            "Full-universe incremental label pricing covers all nonempty task subsets in one "
            "resource-label DP for this fixed graph. It is a proof precursor; the BPC "
            "certificate layer must still bind it to the current true-dual node."
        ),
    }
    return payload, returned_columns


def price_exhaustive_direct_journey_columns(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    negative_eps: float = 1.0e-6,
    max_direct_tasks: int = 5,
    cache: DirectPricingCache | None = None,
    completion_bound_enabled: bool = True,
    wall_time_limit_sec: float | None = None,
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
            "exhaustive_candidate_set_count_by_task_count": {},
            "priced_candidate_set_count": 0,
            "priced_candidate_set_count_by_task_count": {},
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
        wall_time_limit_sec=wall_time_limit_sec,
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
    timed_out = str(payload.get("status") or "").endswith("TIME_LIMIT")
    payload["pricing_complete_for_all_task_subsets"] = not timed_out
    payload["exhaustive_candidate_set_count"] = len(candidate_sets)
    payload["exhaustive_candidate_set_count_by_task_count"] = _candidate_set_count_by_task_count(
        candidate_sets
    )
    candidate_summaries = payload.get("candidate_summaries") or []
    payload["priced_candidate_set_count"] = len(candidate_summaries)
    payload["priced_candidate_set_count_by_task_count"] = _candidate_summary_count_by_task_count(
        candidate_summaries
    )
    payload["can_certify_no_negative"] = False
    payload["wall_time_limit_sec"] = wall_time_limit_sec
    payload["note"] = (
        "Exhaustive direct-label pricing over every nonempty task subset for the fixed logical graph; "
        "diagnostic proof precursor only, not an official BPC certificate."
        if not timed_out
        else "Exhaustive direct-label pricing exceeded the wall-time budget; fail closed for no-negative proof."
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


def _full_universe_incremental_fail_payload(
    data: LunarIceData,
    *,
    status: str,
    max_direct_tasks: int,
    started_at: float,
    note: str,
) -> dict:
    return {
        "status": str(status),
        "exact_status": "NOT_SOLVED",
        "task_count": len(data.task_ids),
        "max_direct_tasks": int(max_direct_tasks),
        "candidate_round_count": 0,
        "candidate_round_limit": 1,
        "candidate_task_count": 0,
        "candidate_task_ids": [],
        "candidate_sets": [],
        "candidate_set_count_by_task_count": {},
        "priced_candidate_set_count_by_task_count": {},
        "search_region_count": 0,
        "search_region_count_by_task_count": {},
        "search_region_count_semantics": "no_search_region_covered",
        "returned_column_count": 0,
        "returned_column_policy": "none",
        "returned_column_semantics": "no_columns_returned",
        "returned_columns_are_complete_universe": False,
        "pricing_complete_for_all_tasks": False,
        "pricing_complete_for_all_task_subsets": False,
        "pricing_coverage_algorithm": "full_universe_incremental_label",
        "full_universe_incremental_label": False,
        "global_min_proof_complete": False,
        "global_min_reduced_cost": None,
        "global_min_reduced_cost_source": "",
        "global_min_reduced_cost_scope": "",
        "global_min_proof_requires_true_dual_reaudit": True,
        "sortie_attempt_count": 0,
        "feasible_sortie_template_count": 0,
        "pareto_label_count": 0,
        "best_reduced_cost": None,
        "negative_found": False,
        "negative_column_count": 0,
        "cut_context_active": False,
        "cut_count": 0,
        "branch_context_active": False,
        "branch_decision_count": 0,
        "branch_filtered_candidate_set_count": 0,
        "branch_filtered_column_count": 0,
        "completion_bound": _disabled_completion_bound_payload(),
        "can_certify_no_negative": False,
        "uses_true_dual_bpc_certificate": False,
        "timeout_stage": "",
        "wall_time_sec": round(perf_counter() - float(started_at), 6),
        "best_column": None,
        "note": str(note),
    }


def _direct_label_time_limit_payload(
    data: LunarIceData,
    *,
    context: CutContext,
    branch: BranchContext,
    max_direct_tasks: int,
    candidate_sets: tuple[tuple[str, ...], ...],
    candidate_summaries: list[dict],
    attempt_count: int,
    feasible_template_count: int,
    pareto_count: int,
    branch_filtered_count: int,
    branch_filtered_candidate_set_count: int,
    timeout_stage: str,
    completion_summaries: list[dict],
    cache: DirectPricingCache | None,
    started_at: float,
) -> dict:
    return {
        "status": "DIRECT_LABEL_PRICING_TIME_LIMIT",
        "exact_status": "NOT_SOLVED",
        "task_count": len(data.task_ids),
        "max_direct_tasks": int(max_direct_tasks),
        "candidate_round_count": len(candidate_summaries),
        "candidate_round_limit": len(candidate_sets),
        "candidate_set_count_by_task_count": _candidate_set_count_by_task_count(candidate_sets),
        "priced_candidate_set_count_by_task_count": _candidate_summary_count_by_task_count(
            candidate_summaries
        ),
        "candidate_task_count": 0,
        "candidate_task_ids": [],
        "candidate_sets": [list(row) for row in candidate_sets],
        "candidate_summaries": candidate_summaries,
        "pricing_complete_for_all_tasks": False,
        "pricing_complete_for_all_task_subsets": False,
        "sortie_attempt_count": int(attempt_count),
        "feasible_sortie_template_count": int(feasible_template_count),
        "pareto_label_count": int(pareto_count),
        "best_reduced_cost": None,
        "negative_found": False,
        "negative_column_count": 0,
        "cut_context_active": not context.empty,
        "cut_count": len(context.cuts),
        "branch_context_active": not branch.empty,
        "branch_decision_count": len(branch.pair_decisions),
        "branch_filtered_candidate_set_count": int(branch_filtered_candidate_set_count),
        "branch_filtered_column_count": int(branch_filtered_count),
        "completion_bound": _aggregate_completion_bounds(completion_summaries),
        "sortie_template_cache": _cache_payload(cache),
        "can_certify_no_negative": False,
        "uses_true_dual_bpc_certificate": False,
        "timeout_stage": str(timeout_stage),
        "wall_time_sec": round(perf_counter() - float(started_at), 6),
        "best_column": None,
        "note": "Direct-label pricing exceeded the wall-time budget; fail closed for no-negative proof.",
    }


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


def _filter_candidate_sets_by_branch_context(
    candidate_sets: tuple[tuple[str, ...], ...],
    branch_context: BranchContext,
) -> tuple[tuple[str, ...], ...]:
    if branch_context.empty:
        return candidate_sets
    return tuple(
        row
        for row in candidate_sets
        if _candidate_set_has_branch_feasible_subset(row, branch_context)
    )


def _candidate_set_has_branch_feasible_subset(
    candidate_set: tuple[str, ...],
    branch_context: BranchContext,
) -> bool:
    """Return whether the candidate universe can produce any branch-feasible column.

    Direct-label pricing may return a strict subset of ``candidate_set``.  The
    only safe task-set-level pruning is therefore to remove universes that cannot
    contain even one nonempty subset satisfying the Ryan-Foster decisions.
    """

    if branch_context.empty:
        return bool(candidate_set)
    available = {str(task_id) for task_id in candidate_set}
    same_components = _same_journey_components(branch_context)
    for task_id in sorted(available):
        closure = _same_journey_closure(task_id, same_components)
        if not closure.issubset(available):
            continue
        if _task_group_violates_different_decision(closure, branch_context):
            continue
        return True
    return False


def _same_journey_components(branch_context: BranchContext) -> list[set[str]]:
    components: list[set[str]] = []
    for decision in branch_context.pair_decisions:
        if decision.sense != SAME_JOURNEY:
            continue
        pair = {str(decision.task_a), str(decision.task_b)}
        merged: set[str] = set(pair)
        remaining: list[set[str]] = []
        for component in components:
            if component & merged:
                merged.update(component)
            else:
                remaining.append(component)
        remaining.append(merged)
        components = remaining
    return components


def _same_journey_closure(task_id: str, components: list[set[str]]) -> set[str]:
    task = str(task_id)
    for component in components:
        if task in component:
            return set(component)
    return {task}


def _task_group_violates_different_decision(
    task_group: set[str],
    branch_context: BranchContext,
) -> bool:
    for decision in branch_context.pair_decisions:
        if decision.sense != DIFFERENT_JOURNEY:
            continue
        if str(decision.task_a) in task_group and str(decision.task_b) in task_group:
            return True
    return False


def _candidate_set_count_by_task_count(candidate_sets: tuple[tuple[str, ...], ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in candidate_sets:
        key = str(len(row))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: int(item[0])))


def _candidate_summary_count_by_task_count(candidate_summaries: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for summary in candidate_summaries:
        task_ids = summary.get("candidate_task_ids") or []
        key = str(len(task_ids))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: int(item[0])))


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
    *,
    deadline: float | None = None,
) -> tuple[dict[int, tuple[_DirectSortieTemplate, ...]], int]:
    templates_by_mask: dict[int, list[_DirectSortieTemplate]] = {}
    attempt_count = 0
    ordered = tuple(sorted(candidate_task_ids))
    limit = min(len(ordered), int(data.max_tasks_per_trip))
    path_type_cache = _nondominated_path_type_cache(data)
    for length in range(1, limit + 1):
        for sequence in permutations(ordered, length):
            if attempt_count % 1024 == 0 and _deadline_exceeded(deadline):
                raise DirectBaselineTimeLimitExceeded(
                    stage="direct_sortie_template_enumeration",
                    generated_sortie_count=attempt_count,
                    route_template_count=sum(len(values) for values in templates_by_mask.values()),
                )
            task_mask = 0
            for task_id in sequence:
                task_mask |= task_to_bit[task_id]
            for path_types in _direct_path_type_assignments(data, sequence, path_type_cache):
                attempt_count += 1
                if attempt_count % 1024 == 0 and _deadline_exceeded(deadline):
                    raise DirectBaselineTimeLimitExceeded(
                        stage="direct_sortie_path_assignment",
                        generated_sortie_count=attempt_count,
                        route_template_count=sum(len(values) for values in templates_by_mask.values()),
                    )
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
    deadline: float | None = None,
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
        if _deadline_exceeded(deadline):
            raise DirectBaselineTimeLimitExceeded(
                stage="direct_label_dp_mask_loop",
                pareto_label_count=sum(len(labels) for mask, labels in labels_by_mask.items() if mask),
            )
        current_labels = list(labels_by_mask.get(current_mask, []))
        if not current_labels:
            continue
        remaining_mask = full_mask ^ current_mask
        expandable_labels: list[_DirectJourneyLabel] = []
        for label in current_labels:
            if completion_payload["evaluated_label_count"] % 64 == 0 and _deadline_exceeded(deadline):
                raise DirectBaselineTimeLimitExceeded(
                    stage="direct_label_dp_label_loop",
                    pareto_label_count=sum(len(labels) for mask, labels in labels_by_mask.items() if mask),
                    journey_label_bound_pruned_count=int(completion_payload["pruned_label_count"]),
                )
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
                    if completion_payload["evaluated_label_count"] % 1024 == 0 and _deadline_exceeded(deadline):
                        raise DirectBaselineTimeLimitExceeded(
                            stage="direct_label_dp_extension_loop",
                            pareto_label_count=sum(len(labels) for mask, labels in labels_by_mask.items() if mask),
                            journey_label_bound_pruned_count=int(completion_payload["pruned_label_count"]),
                        )
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
    completion_bound_enabled: bool = True,
    cut_context: CutContext | None = None,
    branch_context: BranchContext | None = None,
    negative_eps: float = 1.0e-6,
    stop_at_first_negative: bool = False,
    negative_harvest_target: int = 1,
    active_task_sets_for_harvest: Iterable[Iterable[str]] | None = None,
) -> tuple[_DirectJourneyLabel | None, dict]:
    task_index = TaskIndexMap(candidate_task_ids)
    full_mask = task_index.full_mask
    task_to_bit = {task_id: task_index.mask_of(task_id) for task_id in task_index.external_ids}
    task_by_bit = {task_index.mask_of(task_id): task_id for task_id in task_index.external_ids}
    context = cut_context or CutContext()
    branch = branch_context or BranchContext()
    completion_bound = build_positive_cover_completion_bound(candidate_task_ids, duals.cover)
    completion_payload = completion_bound.to_payload()
    completion_payload["enabled"] = bool(completion_bound_enabled) and context.empty and branch.empty
    completion_payload["pruned_label_count"] = 0
    completion_payload["evaluated_label_count"] = 0
    path_type_cache = _nondominated_path_type_cache(data)
    path_type_lb_cache = _path_type_lower_bound_cache(data, path_type_cache)
    sortie_candidate_cache_limit = _direct_sortie_cache_limit(data)
    sortie_candidate_cache = OrderedDict()
    sortie_candidate_cache_hit_count = 0
    sortie_candidate_cache_miss_count = 0
    sortie_candidate_cache_reused_candidate_count = 0
    labels_by_mask: dict[int, list[_DirectJourneyLabel]] = {
        0: [_DirectJourneyLabel(task_mask=0, sorties=tuple(), end_time=0.0, reduced_base=0.0)]
    }
    mask_best_priority = {
        0: _incremental_mask_queue_priority(
            0,
            labels_by_mask[0],
            task_by_bit=task_by_bit,
            duals=duals,
            completion_bound=completion_bound,
            completion_bound_enabled=bool(completion_payload["enabled"]),
        )
    }
    push_counter = 0
    pending_masks = [(
        0,
        mask_best_priority[0],
        push_counter,
        0,
    )]
    processed_masks: set[int] = set()
    generated_sortie_count = 0
    route_template_count = 0
    stale_pop_count = 0
    max_pending_count = 1
    best: _DirectJourneyLabel | None = None
    early_negative_count = 0
    negative_threshold = -abs(float(negative_eps))
    negative_harvest_target = max(1, int(negative_harvest_target))
    active_harvest_masks = {
        task_index.mask_from_ids(row)
        for row in (active_task_sets_for_harvest or tuple())
        if set(str(task_id) for task_id in row).issubset(set(task_index.external_ids))
    }
    active_preference_required = len(active_harvest_masks) < 4000
    early_negative_distinct_task_masks: set[int] = set()
    early_negative_preferred_task_masks: set[int] = set()
    early_negative_raw_cap = max(negative_harvest_target, negative_harvest_target * 8)

    def build_stats(*, early_negative_stop: bool = False) -> dict:
        return {
            "sortie_attempt_count": int(generated_sortie_count),
            "feasible_sortie_template_count": int(route_template_count),
            "pareto_label_count": sum(len(labels) for mask, labels in labels_by_mask.items() if mask),
            "completion_bound": completion_payload,
            "label_expansion_order_policy": "topological_task_count_then_best_bound_mask_priority",
            "label_best_bound_order_enabled": True,
            "label_queue_push_count": int(push_counter + 1),
            "label_queue_stale_pop_count": int(stale_pop_count),
            "label_queue_max_pending_count": int(max_pending_count),
            "sortie_candidate_cache_enabled": True,
            "sortie_candidate_cache_limit": (
                None if sortie_candidate_cache_limit is None else int(sortie_candidate_cache_limit)
            ),
            "sortie_candidate_cache_entry_count": int(len(sortie_candidate_cache)),
            "sortie_candidate_cache_hit_count": int(sortie_candidate_cache_hit_count),
            "sortie_candidate_cache_miss_count": int(sortie_candidate_cache_miss_count),
            "sortie_candidate_cache_reused_candidate_count": int(sortie_candidate_cache_reused_candidate_count),
            "early_negative_stop": bool(early_negative_stop),
            "early_negative_stop_trigger_count": int(early_negative_count),
            "early_negative_distinct_task_set_stop_enabled": bool(stop_at_first_negative),
            "early_negative_distinct_task_set_count": int(len(early_negative_distinct_task_masks)),
            "early_negative_preferred_task_set_count": int(len(early_negative_preferred_task_masks)),
            "early_negative_active_task_set_reference_count": int(len(active_harvest_masks)),
            "early_negative_active_preference_required": bool(active_preference_required),
            "early_negative_raw_stop_cap": int(early_negative_raw_cap),
            "observed_task_mask_count_by_task_count": _mask_count_by_task_count(labels_by_mask.keys()),
            "processed_task_mask_count_by_task_count": _mask_count_by_task_count(processed_masks),
            "pending_task_mask_count_by_task_count": _mask_count_by_task_count(
                mask for _count, _priority, _push_index, mask in pending_masks
            ),
            "_all_pareto_labels": tuple(
                label
                for mask, labels in labels_by_mask.items()
                if mask
                for label in labels
            ),
        }

    def raise_time_limit(stage: str, *, cause: Exception | None = None) -> None:
        exc = DirectBaselineTimeLimitExceeded(
            stage=stage,
            generated_sortie_count=generated_sortie_count,
            route_template_count=route_template_count,
            pareto_label_count=sum(len(labels) for mask, labels in labels_by_mask.items() if mask),
            partial_label=best,
            partial_stats=build_stats(early_negative_stop=False),
        )
        if cause is not None:
            raise exc from cause
        raise exc

    while pending_masks:
        if _deadline_exceeded(deadline):
            raise_time_limit("incremental_journey_label_dp")
        _current_count, current_priority, _push_index, current_mask = heapq.heappop(pending_masks)
        if current_mask in processed_masks:
            stale_pop_count += 1
            continue
        if current_priority > mask_best_priority.get(current_mask, current_priority) + 1.0e-12:
            stale_pop_count += 1
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
                raise_time_limit("incremental_journey_label_dp")
            completion_payload["evaluated_label_count"] += 1
            if completion_payload["enabled"] and best is not None:
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
            try:
                cache_key = (round(float(label.end_time), 6), int(remaining_mask))
                cached = sortie_candidate_cache.get(cache_key)
                if cached is None:
                    candidates, generated_count, route_count, _ = _direct_sortie_candidates_from_start(
                        data,
                        task_to_bit,
                        remaining_mask=remaining_mask,
                        start_time=float(label.end_time),
                        deadline=deadline,
                        path_type_cache=path_type_cache,
                        path_type_lb_cache=path_type_lb_cache,
                    )
                    cached = (tuple(candidates), int(generated_count), int(route_count))
                    sortie_candidate_cache[cache_key] = cached
                    if sortie_candidate_cache_limit is not None:
                        while len(sortie_candidate_cache) > int(sortie_candidate_cache_limit):
                            sortie_candidate_cache.popitem(last=False)
                    sortie_candidate_cache_miss_count += 1
                    generated_sortie_count += int(generated_count)
                    route_template_count += int(route_count)
                else:
                    if sortie_candidate_cache_limit is not None:
                        sortie_candidate_cache.move_to_end(cache_key)
                    sortie_candidate_cache_hit_count += 1
                    sortie_candidate_cache_reused_candidate_count += len(cached[0])
                candidates = cached[0]
            except DirectBaselineTimeLimitExceeded as exc:
                generated_sortie_count += int(exc.generated_sortie_count)
                route_template_count += int(exc.route_template_count)
                raise_time_limit(f"sortie_candidate_generation:{exc.stage}", cause=exc)
            for candidate_index, candidate in enumerate(candidates):
                if candidate_index % 1024 == 0 and _deadline_exceeded(deadline):
                    raise_time_limit("incremental_candidate_extension")
                if candidate.task_mask & current_mask:
                    continue
                new_mask = current_mask | candidate.task_mask
                if new_mask == current_mask:
                    continue
                new_label = _extend_direct_label(data, duals, label, candidate.sortie, candidate.task_mask)
                target_labels = labels_by_mask.setdefault(new_mask, [])
                _add_direct_pareto_label(target_labels, new_label)
                if new_mask not in processed_masks:
                    new_priority = _incremental_mask_queue_priority(
                        new_mask,
                        target_labels,
                        task_by_bit=task_by_bit,
                        duals=duals,
                        completion_bound=completion_bound,
                        completion_bound_enabled=bool(completion_payload["enabled"]),
                    )
                    old_priority = mask_best_priority.get(new_mask)
                    if old_priority is None or new_priority < old_priority - 1.0e-12:
                        mask_best_priority[new_mask] = new_priority
                        push_counter += 1
                        heapq.heappush(
                            pending_masks,
                            (new_mask.bit_count(), new_priority, push_counter, new_mask),
                        )
                        max_pending_count = max(max_pending_count, len(pending_masks))
                if not _label_satisfies_branch_context(new_label, task_index, branch):
                    continue
                candidate_rc = new_label.reduced_cost(
                    data,
                    duals,
                    cut_context=context,
                    candidate_task_ids=candidate_task_ids,
                )
                if (
                    best is None
                    or candidate_rc
                    < best.reduced_cost(
                        data,
                        duals,
                        cut_context=context,
                        candidate_task_ids=candidate_task_ids,
                    )
                    - 1.0e-9
                ):
                    best = new_label
                if candidate_rc < negative_threshold:
                    early_negative_count += 1
                    early_negative_distinct_task_masks.add(int(new_mask))
                    if not active_preference_required or int(new_mask) not in active_harvest_masks:
                        early_negative_preferred_task_masks.add(int(new_mask))
                    if bool(stop_at_first_negative) and early_negative_count >= negative_harvest_target:
                        enough_preferred = (
                            len(early_negative_preferred_task_masks) >= negative_harvest_target
                        )
                        raw_cap_reached = early_negative_count >= early_negative_raw_cap
                        if enough_preferred or raw_cap_reached:
                            return best, build_stats(early_negative_stop=True)

    return best, build_stats(early_negative_stop=False)


def _mask_count_by_task_count(masks: Iterable[int]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for mask in masks:
        value = int(mask)
        if value == 0:
            continue
        key = str(value.bit_count())
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: int(item[0])))


def _incremental_mask_queue_priority(
    mask: int,
    labels: Iterable[_DirectJourneyLabel],
    *,
    task_by_bit: dict[int, str],
    duals: JourneyDuals,
    completion_bound,
    completion_bound_enabled: bool,
) -> float:
    """Return an exact-safe queue key for labels in the same topological layer."""

    remaining_mask = 0
    for bit in task_by_bit:
        if not mask & bit:
            remaining_mask |= bit
    remaining_tasks = tuple(task_id for bit, task_id in task_by_bit.items() if remaining_mask & bit)
    best_priority: float | None = None
    for label in labels:
        if completion_bound_enabled:
            priority = completion_bound.optimistic_label_bound(
                current_reduced_base=label.reduced_base,
                current_end_time=label.end_time,
                beta_journey_end_time=0.0,
                remaining_task_ids=remaining_tasks,
            )
            priority = round(float(priority) - float(duals.fleet_limit), 9)
        else:
            priority = round(float(label.reduced_base) - float(duals.fleet_limit), 9)
        if best_priority is None or priority < best_priority:
            best_priority = priority
    return float("inf") if best_priority is None else float(best_priority)


def _select_full_universe_incremental_return_columns(
    data: LunarIceData,
    duals: JourneyDuals,
    labels: tuple[_DirectJourneyLabel, ...],
    *,
    best_label: _DirectJourneyLabel,
    candidate_task_ids: tuple[str, ...],
    branch_context: BranchContext,
    cut_context: CutContext,
    negative_eps: float,
    max_returned_columns: int,
    active_task_sets: Iterable[Iterable[str]] | None = None,
) -> tuple[tuple[JourneyColumn, ...], dict]:
    task_index = TaskIndexMap(candidate_task_ids)
    target = max(1, int(max_returned_columns))
    active_task_set_lookup = {
        tuple(sorted(str(task_id) for task_id in row))
        for row in (active_task_sets or tuple())
    }
    rows: list[dict] = []
    seen_signatures: set[tuple] = set()
    for label in labels:
        if not label.task_mask:
            continue
        if not _label_satisfies_branch_context(label, task_index, branch_context):
            continue
        try:
            column = build_journey_column(data, label.sorties)
        except ValueError:
            continue
        signature = _column_signature(column)
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        rc = manual_journey_reduced_cost(
            column,
            duals,
            cut_coefficients=cut_context.coefficients_for(column),
        )
        rows.append(
            {
                "column": column,
                "signature": signature,
                "task_set": tuple(sorted(str(task_id) for task_id in column.task_set)),
                "task_set_is_active": tuple(sorted(str(task_id) for task_id in column.task_set))
                in active_task_set_lookup,
                "reduced_cost": float(rc),
                "objective": float(column.objective),
                "sortie_count": len(column.sorties),
            }
        )
    rows.sort(
        key=lambda row: (
            float(row["reduced_cost"]),
            tuple(row["task_set"]),
            float(row["objective"]),
            int(row["sortie_count"]),
            tuple(row["signature"]),
        )
    )
    threshold = -abs(float(negative_eps))
    negative_rows = [row for row in rows if float(row["reduced_cost"]) < threshold]
    best_signature = _column_signature(build_journey_column(data, best_label.sorties))
    selected: list[dict] = []
    selected_signatures: set[tuple] = set()
    selected_task_sets: set[tuple[str, ...]] = set()

    def add(row: dict) -> None:
        signature = row["signature"]
        if signature in selected_signatures:
            return
        selected.append(row)
        selected_signatures.add(signature)
        selected_task_sets.add(tuple(row["task_set"]))

    best_row = next((row for row in rows if row["signature"] == best_signature), None)
    if best_row is not None:
        add(best_row)
    source_rows = negative_rows if negative_rows else rows
    non_active_source_rows = [row for row in source_rows if not bool(row["task_set_is_active"])]
    active_source_rows = [row for row in source_rows if bool(row["task_set_is_active"])]
    for row in non_active_source_rows:
        if len(selected) >= target:
            break
        if tuple(row["task_set"]) in selected_task_sets:
            continue
        add(row)
    for row in active_source_rows:
        if len(selected) >= target:
            break
        if tuple(row["task_set"]) in selected_task_sets:
            continue
        add(row)
    for row in non_active_source_rows:
        if len(selected) >= target:
            break
        add(row)
    for row in active_source_rows:
        if len(selected) >= target:
            break
        add(row)

    returned = tuple(row["column"] for row in selected)
    selected_negative_count = sum(1 for row in selected if float(row["reduced_cost"]) < threshold)
    selected_new_task_set_count = len({tuple(row["task_set"]) for row in selected})
    selected_active_task_set_count = sum(1 for row in selected if bool(row["task_set_is_active"]))
    selected_non_active_task_set_count = len(selected) - int(selected_active_task_set_count)
    policy = (
        "global_min_plus_diverse_negative_harvest"
        if selected_negative_count > 1
        else "single_global_min_column"
    )
    semantics = (
        "global_min_column_plus_diverse_negative_columns_from_full_space_labeling"
        if selected_negative_count > 1
        else "single_best_column_from_full_space_labeling"
    )
    return returned, {
        "returned_column_policy": policy,
        "returned_column_semantics": semantics,
        "exact_negative_harvest_target": int(target),
        "exact_negative_harvest_candidate_count": len(negative_rows),
        "exact_negative_harvest_selected_count": int(selected_negative_count),
        "exact_negative_harvest_selected_new_task_set_count": int(selected_new_task_set_count),
        "exact_negative_harvest_selected_replacement_task_set_count": max(
            0,
            int(len(selected)) - int(selected_new_task_set_count),
        ),
        "exact_negative_harvest_active_task_set_count": int(selected_active_task_set_count),
        "exact_negative_harvest_non_active_task_set_count": int(selected_non_active_task_set_count),
        "exact_negative_harvest_active_task_set_reference_count": len(active_task_set_lookup),
        "exact_negative_harvest_selection_policy": (
            "global_min_first_then_non_active_distinct_task_sets_then_active_distinct_task_sets_then_replacements"
        ),
        "exact_negative_harvest_best_rc": None
        if not negative_rows
        else round(float(negative_rows[0]["reduced_cost"]), 9),
        "exact_negative_harvest_worst_selected_rc": None
        if not selected
        else round(max(float(row["reduced_cost"]) for row in selected), 9),
    }


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


def _label_satisfies_branch_context(
    label: _DirectJourneyLabel,
    task_index: TaskIndexMap,
    branch_context: BranchContext,
) -> bool:
    if branch_context.empty:
        return True
    tasks = set(task_index.ids_from_mask(label.task_mask))
    for decision in branch_context.pair_decisions:
        has_a = str(decision.task_a) in tasks
        has_b = str(decision.task_b) in tasks
        if decision.sense == SAME_JOURNEY and has_a != has_b:
            return False
        if decision.sense == DIFFERENT_JOURNEY and has_a and has_b:
            return False
    return True


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
