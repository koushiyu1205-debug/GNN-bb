"""Small-scale journey-column dynamic-programming baseline.

This is not the final BPC driver. It solves a restricted canonical-path journey
column universe so the lunar-ice schema has a real exact baseline path before
true-dual pricing, cuts, and branching are ported. The result must not be used
as an official BPC certificate.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import heapq
from itertools import permutations, product
from math import ceil, floor, isfinite
from time import perf_counter
from typing import Iterable, Mapping

from lunar_ice_bpc.domain.scenario import PATH_OPTION_POLICY_ID, PATH_TYPES
from lunar_ice_bpc.exact.bpc.core.task_index import TaskIndexMap
from lunar_ice_bpc.exact.bpc.pricing.status import (
    AlgorithmStatus,
    CertificateScope,
    certificate_scope_for_algorithm_status,
)
from lunar_ice_bpc.exact.core.columns import SortieLeg, TimedSortie, build_timed_sortie
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn, build_journey_column
from lunar_ice_bpc.exact.core.objective import (
    additive_objective_value,
    aggregate_journey_objective_breakdown,
    objective_references,
    operating_cost_value,
    service_risk_value,
    sortie_objective_value,
)
from lunar_ice_bpc.exact.master.journey_rmp import _simplex_max_leq


CANONICAL_PATH_POLICIES: tuple[tuple[str, ...], ...] = (
    ("low_time",),
    ("low_energy",),
    ("low_risk",),
)
_TIME_AWARE_LB_BUCKET_MIN = 10.0
_DIRECT_BOUND_PRUNING_MIN_ROOT_RATIO = 0.5


@dataclass(frozen=True)
class JourneyBaselineResult:
    status: str
    exact_status: str
    objective: float | None
    journeys: tuple[JourneyColumn, ...]
    generated_journey_count: int
    generated_sortie_count: int
    route_template_count: int
    pareto_label_count: int
    set_partition_state_count: int
    note: str
    wall_time_sec: float | None = None
    certificate_scope: str = CertificateScope.FEASIBLE_INCUMBENT_ONLY.value
    path_option_dominance_policy: str = PATH_OPTION_POLICY_ID
    path_option_dominance_filtered_count: int = 0
    infeasibility_scope_if_any: str = ""
    objective_breakdown: dict | None = None
    reference_solution_upper_bound: float | None = None
    reference_solution_upper_bound_source: str = ""
    journey_label_bound_pruned_count: int = 0
    direct_bound_pruning_root_bound: float | None = None
    direct_bound_pruning_active: bool = False


@dataclass(frozen=True)
class CanonicalJourneyUniverse:
    columns: tuple[JourneyColumn, ...]
    best_label_by_mask: dict[int, "_JourneyLabel"]
    generated_sortie_count: int
    route_template_count: int
    pareto_label_count: int
    journey_label_bound_pruned_count: int = 0
    direct_bound_pruning_root_bound: float | None = None
    direct_bound_pruning_active: bool = False


@dataclass(frozen=True)
class _SortieTemplate:
    task_mask: int
    sequence: tuple[str, ...]
    path_types: tuple[str, ...]


@dataclass(frozen=True)
class _JourneyLabel:
    task_mask: int
    sorties: tuple[TimedSortie, ...]
    end_time: float
    base_cost: float

    def objective(self, data: LunarIceData) -> float:
        return round(self.base_cost, 6)


@dataclass(frozen=True)
class _PartialSortieLabel:
    task_mask: int
    last_task: str
    sequence: tuple[str, ...]
    path_types: tuple[str, ...]
    start_time: float
    elapsed: float
    service_starts: dict[str, float]
    travel_time: float
    distance_km: float
    energy_proxy: float
    risk_integral: float
    shadow_exposure_min: float
    demand: float
    service_cost: float
    discovery_completion_term: float
    base_cost: float


@dataclass(frozen=True)
class _SortieCandidate:
    task_mask: int
    sortie: TimedSortie
    base_cost: float


@dataclass(frozen=True)
class _ReferenceSolutionUpperBound:
    objective: float
    journeys: tuple[JourneyColumn, ...]
    source: str


class DirectBaselineTimeLimitExceeded(RuntimeError):
    """Raised when an exact fixed-graph direct baseline exceeds its wall-time budget."""

    def __init__(
        self,
        message: str = "Fixed-graph direct DP exceeded its wall-time budget.",
        *,
        stage: str = "unknown",
        generated_journey_count: int = 0,
        generated_sortie_count: int = 0,
        route_template_count: int = 0,
        pareto_label_count: int = 0,
        set_partition_state_count: int = 0,
        journey_label_bound_pruned_count: int = 0,
        direct_bound_pruning_root_bound: float | None = None,
        direct_bound_pruning_active: bool = False,
        partial_label: object | None = None,
        partial_stats: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.stage = str(stage)
        self.generated_journey_count = int(generated_journey_count)
        self.generated_sortie_count = int(generated_sortie_count)
        self.route_template_count = int(route_template_count)
        self.pareto_label_count = int(pareto_label_count)
        self.set_partition_state_count = int(set_partition_state_count)
        self.journey_label_bound_pruned_count = int(journey_label_bound_pruned_count)
        self.direct_bound_pruning_root_bound = direct_bound_pruning_root_bound
        self.direct_bound_pruning_active = bool(direct_bound_pruning_active)
        self.partial_label = partial_label
        self.partial_stats = dict(partial_stats or {})


def _task_to_bit_mapping(task_index: TaskIndexMap) -> dict[str, int]:
    return {task_id: task_index.mask_of(task_id) for task_id in task_index.external_ids}


def _full_task_mask(data: LunarIceData) -> int:
    return TaskIndexMap(data.task_ids).full_mask


def solve_small_journey_baseline(data: LunarIceData, *, max_exact_tasks: int = 10) -> JourneyBaselineResult:
    """Solve a small instance over the restricted canonical-path universe."""

    start = perf_counter()
    dominance_audit = path_option_dominance_audit(data)
    if len(data.task_ids) > int(max_exact_tasks):
        return JourneyBaselineResult(
            status="SKIPPED_TOO_LARGE_FOR_ENUM_BASELINE",
            exact_status="NOT_SOLVED",
            objective=None,
            journeys=tuple(),
            generated_journey_count=0,
            generated_sortie_count=0,
            route_template_count=0,
            pareto_label_count=0,
            set_partition_state_count=0,
            note=f"task_count={len(data.task_ids)} exceeds max_exact_tasks={max_exact_tasks}",
            wall_time_sec=_elapsed_sec(start),
            path_option_dominance_policy=str(dominance_audit["policy"]),
            path_option_dominance_filtered_count=int(dominance_audit["filtered_count"]),
        )
    universe = enumerate_canonical_journey_columns(data, max_exact_tasks=int(max_exact_tasks))
    best_labels, state_count = _select_vehicle_partition(data, universe.best_label_by_mask)
    if best_labels is None:
        return JourneyBaselineResult(
            status="NO_COLUMN_COVER_IN_CANONICAL_UNIVERSE",
            exact_status="NOT_SOLVED",
            objective=None,
            journeys=tuple(),
            generated_journey_count=len(universe.best_label_by_mask),
            generated_sortie_count=universe.generated_sortie_count,
            route_template_count=universe.route_template_count,
            pareto_label_count=universe.pareto_label_count,
            set_partition_state_count=state_count,
            note="No cover was found in the restricted canonical-path journey universe.",
            wall_time_sec=_elapsed_sec(start),
            path_option_dominance_policy=str(dominance_audit["policy"]),
            path_option_dominance_filtered_count=int(dominance_audit["filtered_count"]),
            infeasibility_scope_if_any="NO_COLUMN_COVER_IN_POOL",
        )
    best = tuple(build_journey_column(data, label.sorties) for label in best_labels)
    return JourneyBaselineResult(
        status="CANONICAL_DP_BASELINE_OPTIMAL",
        exact_status="NOT_BPC_CERTIFIED",
        objective=round(sum(journey.objective for journey in best), 6),
        journeys=tuple(best),
        generated_journey_count=len(universe.best_label_by_mask),
        generated_sortie_count=universe.generated_sortie_count,
        route_template_count=universe.route_template_count,
        pareto_label_count=universe.pareto_label_count,
        set_partition_state_count=state_count,
        note=(
            "Optimal only within the restricted canonical-path journey-column universe "
            f"{tuple(PATH_TYPES)}; no true-dual BPC certificate."
        ),
        wall_time_sec=_elapsed_sec(start),
        path_option_dominance_policy=str(dominance_audit["policy"]),
        path_option_dominance_filtered_count=int(dominance_audit["filtered_count"]),
        objective_breakdown=aggregate_journey_objective_breakdown(data, best),
    )


def solve_direct_journey_baseline(
    data: LunarIceData,
    *,
    max_exact_tasks: int = 5,
    wall_time_limit_sec: float | None = None,
) -> JourneyBaselineResult:
    """Solve a small instance over all fixed logical-graph path options."""

    start = perf_counter()
    dominance_audit = path_option_dominance_audit(data)
    if len(data.task_ids) > int(max_exact_tasks):
        return JourneyBaselineResult(
            status="SKIPPED_TOO_LARGE_FOR_DIRECT_DP_BASELINE",
            exact_status="NOT_SOLVED",
            objective=None,
            journeys=tuple(),
            generated_journey_count=0,
            generated_sortie_count=0,
            route_template_count=0,
            pareto_label_count=0,
            set_partition_state_count=0,
            note=f"task_count={len(data.task_ids)} exceeds max_exact_tasks={max_exact_tasks}",
            wall_time_sec=_elapsed_sec(start),
            certificate_scope=certificate_scope_for_algorithm_status(
                AlgorithmStatus.SKIPPED_TOO_LARGE_FOR_DIRECT_DP_BASELINE
            ).value,
            path_option_dominance_policy=str(dominance_audit["policy"]),
            path_option_dominance_filtered_count=int(dominance_audit["filtered_count"]),
    )
    deadline = _deadline_from_limit(wall_time_limit_sec)
    reference_upper = _reference_solution_upper_bound(data)
    reference_upper_value = None if reference_upper is None else float(reference_upper.objective)
    reference_upper_source = "" if reference_upper is None else str(reference_upper.source)
    try:
        universe = enumerate_direct_journey_columns(
            data,
            max_exact_tasks=int(max_exact_tasks),
            deadline=deadline,
            incumbent_upper_bound=reference_upper_value,
        )
    except DirectBaselineTimeLimitExceeded as exc:
        return JourneyBaselineResult(
            status=AlgorithmStatus.DIRECT_DP_TIME_LIMIT.value,
            exact_status="NOT_SOLVED",
            objective=None,
            journeys=tuple(),
            generated_journey_count=exc.generated_journey_count,
            generated_sortie_count=exc.generated_sortie_count,
            route_template_count=exc.route_template_count,
            pareto_label_count=exc.pareto_label_count,
            set_partition_state_count=exc.set_partition_state_count,
            note=(
                f"Fixed-graph direct DP exceeded wall_time_limit_sec={wall_time_limit_sec} "
                f"during {exc.stage}; partial counts are diagnostic only."
            ),
            wall_time_sec=_elapsed_sec(start),
            certificate_scope=certificate_scope_for_algorithm_status(AlgorithmStatus.DIRECT_DP_TIME_LIMIT).value,
            path_option_dominance_policy=str(dominance_audit["policy"]),
            path_option_dominance_filtered_count=int(dominance_audit["filtered_count"]),
            reference_solution_upper_bound=reference_upper_value,
            reference_solution_upper_bound_source=reference_upper_source,
            journey_label_bound_pruned_count=int(exc.journey_label_bound_pruned_count),
            direct_bound_pruning_root_bound=exc.direct_bound_pruning_root_bound,
            direct_bound_pruning_active=exc.direct_bound_pruning_active,
        )
    try:
        best_labels, state_count = _select_vehicle_partition(
            data,
            universe.best_label_by_mask,
            deadline=deadline,
        )
    except DirectBaselineTimeLimitExceeded as exc:
        return JourneyBaselineResult(
            status=AlgorithmStatus.DIRECT_DP_TIME_LIMIT.value,
            exact_status="NOT_SOLVED",
            objective=None,
            journeys=tuple(),
            generated_journey_count=exc.generated_journey_count or len(universe.best_label_by_mask),
            generated_sortie_count=exc.generated_sortie_count or universe.generated_sortie_count,
            route_template_count=exc.route_template_count or universe.route_template_count,
            pareto_label_count=exc.pareto_label_count or universe.pareto_label_count,
            set_partition_state_count=exc.set_partition_state_count,
            note=(
                f"Fixed-graph direct DP exceeded wall_time_limit_sec={wall_time_limit_sec} "
                f"during {exc.stage}; partial counts are diagnostic only."
            ),
            wall_time_sec=_elapsed_sec(start),
            certificate_scope=certificate_scope_for_algorithm_status(AlgorithmStatus.DIRECT_DP_TIME_LIMIT).value,
            path_option_dominance_policy=str(dominance_audit["policy"]),
            path_option_dominance_filtered_count=int(dominance_audit["filtered_count"]),
            reference_solution_upper_bound=reference_upper_value,
            reference_solution_upper_bound_source=reference_upper_source,
            journey_label_bound_pruned_count=universe.journey_label_bound_pruned_count,
            direct_bound_pruning_root_bound=universe.direct_bound_pruning_root_bound,
            direct_bound_pruning_active=universe.direct_bound_pruning_active,
        )
    if best_labels is None:
        return JourneyBaselineResult(
            status=AlgorithmStatus.DIRECT_DP_NO_COVER.value,
            exact_status="NOT_SOLVED",
            objective=None,
            journeys=tuple(),
            generated_journey_count=len(universe.best_label_by_mask),
            generated_sortie_count=universe.generated_sortie_count,
            route_template_count=universe.route_template_count,
            pareto_label_count=universe.pareto_label_count,
            set_partition_state_count=state_count,
            note="No cover was found in the exhaustive direct-path journey universe.",
            wall_time_sec=_elapsed_sec(start),
            certificate_scope=certificate_scope_for_algorithm_status(AlgorithmStatus.DIRECT_DP_NO_COVER).value,
            path_option_dominance_policy=str(dominance_audit["policy"]),
            path_option_dominance_filtered_count=int(dominance_audit["filtered_count"]),
            infeasibility_scope_if_any=CertificateScope.DIRECT_DP_NO_COVER.value,
            reference_solution_upper_bound=reference_upper_value,
            reference_solution_upper_bound_source=reference_upper_source,
            journey_label_bound_pruned_count=universe.journey_label_bound_pruned_count,
            direct_bound_pruning_root_bound=universe.direct_bound_pruning_root_bound,
            direct_bound_pruning_active=universe.direct_bound_pruning_active,
        )
    best = tuple(build_journey_column(data, label.sorties) for label in best_labels)
    return JourneyBaselineResult(
        status="DIRECT_DP_BASELINE_OPTIMAL",
        exact_status="EXACT_BASELINE_OPTIMAL",
        objective=round(sum(journey.objective for journey in best), 6),
        journeys=tuple(best),
        generated_journey_count=len(universe.best_label_by_mask),
        generated_sortie_count=universe.generated_sortie_count,
        route_template_count=universe.route_template_count,
        pareto_label_count=universe.pareto_label_count,
        set_partition_state_count=state_count,
        note=(
            "Optimal over the fixed logical graph with all three per-leg path choices "
            "and exhaustive direct DP; this is an exact baseline, not a true-dual BPC certificate."
        ),
        wall_time_sec=_elapsed_sec(start),
        certificate_scope=certificate_scope_for_algorithm_status(AlgorithmStatus.DIRECT_DP_BASELINE_OPTIMAL).value,
        path_option_dominance_policy=str(dominance_audit["policy"]),
        path_option_dominance_filtered_count=int(dominance_audit["filtered_count"]),
        objective_breakdown=aggregate_journey_objective_breakdown(data, best),
        reference_solution_upper_bound=reference_upper_value,
        reference_solution_upper_bound_source=reference_upper_source,
        journey_label_bound_pruned_count=universe.journey_label_bound_pruned_count,
        direct_bound_pruning_root_bound=universe.direct_bound_pruning_root_bound,
        direct_bound_pruning_active=universe.direct_bound_pruning_active,
    )


def enumerate_canonical_journey_columns(data: LunarIceData, *, max_exact_tasks: int = 10) -> CanonicalJourneyUniverse:
    """Return the best restricted canonical journey column for each task set."""

    if len(data.task_ids) > int(max_exact_tasks):
        raise ValueError(f"task_count={len(data.task_ids)} exceeds max_exact_tasks={max_exact_tasks}")
    task_to_bit = _task_to_bit_mapping(TaskIndexMap(data.task_ids))
    templates_by_mask, sortie_count = _enumerate_sortie_templates(data, task_to_bit, mode="canonical")
    best_label_by_mask, pareto_label_count = _build_single_vehicle_journeys(data, templates_by_mask)
    columns = tuple(
        build_journey_column(data, label.sorties)
        for _, label in sorted(best_label_by_mask.items(), key=lambda item: item[0])
    )
    return CanonicalJourneyUniverse(
        columns=columns,
        best_label_by_mask=best_label_by_mask,
        generated_sortie_count=sortie_count,
        route_template_count=sum(len(values) for values in templates_by_mask.values()),
        pareto_label_count=pareto_label_count,
    )


def enumerate_direct_journey_columns(
    data: LunarIceData,
    *,
    max_exact_tasks: int = 5,
    deadline: float | None = None,
    incumbent_upper_bound: float | None = None,
) -> CanonicalJourneyUniverse:
    """Return the best exhaustive direct-path journey column for each task set."""

    if len(data.task_ids) > int(max_exact_tasks):
        raise ValueError(f"task_count={len(data.task_ids)} exceeds max_exact_tasks={max_exact_tasks}")
    _raise_if_deadline_exceeded(deadline)
    task_to_bit = _task_to_bit_mapping(TaskIndexMap(data.task_ids))
    (
        best_label_by_mask,
        sortie_count,
        route_template_count,
        pareto_label_count,
        journey_label_bound_pruned_count,
        direct_bound_pruning_root_bound,
        direct_bound_pruning_active,
    ) = _build_direct_journeys_label_dp(
        data,
        task_to_bit,
        deadline=deadline,
        incumbent_upper_bound=incumbent_upper_bound,
    )
    columns = tuple(
        build_journey_column(data, label.sorties)
        for _, label in sorted(best_label_by_mask.items(), key=lambda item: item[0])
    )
    return CanonicalJourneyUniverse(
        columns=columns,
        best_label_by_mask=best_label_by_mask,
        generated_sortie_count=sortie_count,
        route_template_count=route_template_count,
        pareto_label_count=pareto_label_count,
        journey_label_bound_pruned_count=journey_label_bound_pruned_count,
        direct_bound_pruning_root_bound=direct_bound_pruning_root_bound,
        direct_bound_pruning_active=direct_bound_pruning_active,
    )


def enumerate_direct_journey_columns_by_template(
    data: LunarIceData,
    *,
    max_exact_tasks: int = 5,
) -> CanonicalJourneyUniverse:
    """Compatibility path using explicit permutation x path-template enumeration."""

    if len(data.task_ids) > int(max_exact_tasks):
        raise ValueError(f"task_count={len(data.task_ids)} exceeds max_exact_tasks={max_exact_tasks}")
    task_to_bit = _task_to_bit_mapping(TaskIndexMap(data.task_ids))
    templates_by_mask, sortie_count = _enumerate_sortie_templates(data, task_to_bit, mode="direct")
    best_label_by_mask, pareto_label_count = _build_single_vehicle_journeys(data, templates_by_mask)
    columns = tuple(
        build_journey_column(data, label.sorties)
        for _, label in sorted(best_label_by_mask.items(), key=lambda item: item[0])
    )
    return CanonicalJourneyUniverse(
        columns=columns,
        best_label_by_mask=best_label_by_mask,
        generated_sortie_count=sortie_count,
        route_template_count=sum(len(values) for values in templates_by_mask.values()),
        pareto_label_count=pareto_label_count,
    )


def _build_direct_journeys_label_dp(
    data: LunarIceData,
    task_to_bit: dict[str, int],
    *,
    deadline: float | None = None,
    incumbent_upper_bound: float | None = None,
) -> tuple[dict[int, _JourneyLabel], int, int, int, int, float | None, bool]:
    full_mask = _full_task_mask(data)
    path_type_cache = _nondominated_path_type_cache(data)
    path_type_lb_cache = _path_type_lower_bound_cache(data, path_type_cache)
    incumbent_bound = _finite_upper_bound(incumbent_upper_bound)
    service_lower_bound = _remaining_task_visit_lower_bound_fn(data) if incumbent_bound is not None else None
    return_lower_bound = _remaining_return_path_lower_bound_fn(data) if incumbent_bound is not None else None
    endpoint_lower_bound = _remaining_endpoint_path_lower_bound_fn(data) if incumbent_bound is not None else None
    tail_lower_bound = _remaining_future_sortie_tail_lower_bound_fn(data) if incumbent_bound is not None else None
    direct_bound_pruning_root_bound = _direct_bound_pruning_root_bound(
        full_mask,
        tail_lower_bound=tail_lower_bound,
    )
    bound_pruning_active = _direct_bound_pruning_active(
        full_mask,
        incumbent_bound=incumbent_bound,
        root_bound=direct_bound_pruning_root_bound,
    )
    labels_by_mask: dict[int, list[_JourneyLabel]] = {
        0: [_JourneyLabel(task_mask=0, sorties=tuple(), end_time=0.0, base_cost=0.0)]
    }
    sortie_cache_limit = _direct_sortie_cache_limit(data)
    sortie_cache: OrderedDict[tuple[float, int, float | None], tuple[tuple[_SortieCandidate, ...], int, int, int]] = (
        OrderedDict()
    )
    generated_sortie_count = 0
    route_template_count = 0
    journey_label_bound_pruned_count = 0

    pending_masks = [0]
    queued_masks = {0}
    processed_masks: set[int] = set()
    while pending_masks:
        _raise_if_direct_deadline_exceeded(
            deadline,
            stage="journey_label_dp",
            labels_by_mask=labels_by_mask,
            generated_sortie_count=generated_sortie_count,
            route_template_count=route_template_count,
            journey_label_bound_pruned_count=journey_label_bound_pruned_count,
            direct_bound_pruning_root_bound=direct_bound_pruning_root_bound,
            direct_bound_pruning_active=bound_pruning_active,
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
        for label in current_labels:
            if bound_pruning_active and service_lower_bound is not None and incumbent_bound is not None:
                full_remaining_after_label = full_mask ^ int(label.task_mask)
                optimistic_total = (
                    float(label.base_cost)
                    + (
                        0.0
                        if tail_lower_bound is None
                        else float(tail_lower_bound(full_remaining_after_label, float(label.end_time)))
                    )
                )
                if optimistic_total > float(incumbent_bound) + 1.0e-9:
                    journey_label_bound_pruned_count += 1
                    continue
            cache_key = (
                round(float(label.end_time), 6),
                int(remaining_mask),
                round(float(label.base_cost), 6) if bound_pruning_active else None,
            )
            cached = sortie_cache.get(cache_key)
            if cached is None:
                try:
                    candidates, generated_count, route_count, sortie_bound_pruned_count = (
                        _direct_sortie_candidates_from_start(
                            data,
                            task_to_bit,
                            remaining_mask=remaining_mask,
                            start_time=float(label.end_time),
                            deadline=deadline,
                            path_type_cache=path_type_cache,
                            path_type_lb_cache=path_type_lb_cache,
                            prefix_task_mask=int(current_mask),
                            prefix_base_cost=float(label.base_cost),
                            full_mask=int(full_mask),
                            incumbent_upper_bound=incumbent_bound if bound_pruning_active else None,
                            remaining_lower_bound=service_lower_bound if bound_pruning_active else None,
                            return_lower_bound=return_lower_bound if bound_pruning_active else None,
                        )
                    )
                except DirectBaselineTimeLimitExceeded as exc:
                    raise _direct_timeout(
                        stage=f"sortie_candidate_generation:{exc.stage}",
                        labels_by_mask=labels_by_mask,
                        generated_sortie_count=generated_sortie_count + int(exc.generated_sortie_count),
                        route_template_count=route_template_count + int(exc.route_template_count),
                        journey_label_bound_pruned_count=journey_label_bound_pruned_count
                        + int(exc.journey_label_bound_pruned_count),
                        direct_bound_pruning_root_bound=direct_bound_pruning_root_bound,
                        direct_bound_pruning_active=bound_pruning_active,
                    ) from exc
                cached = (tuple(candidates), generated_count, route_count, sortie_bound_pruned_count)
                sortie_cache[cache_key] = cached
                if sortie_cache_limit is not None:
                    while len(sortie_cache) > int(sortie_cache_limit):
                        sortie_cache.popitem(last=False)
                generated_sortie_count += generated_count
                route_template_count += route_count
                journey_label_bound_pruned_count += int(sortie_bound_pruned_count)
            elif sortie_cache_limit is not None:
                sortie_cache.move_to_end(cache_key)
            candidates = cached[0]
            for candidate in candidates:
                if candidate.task_mask & current_mask:
                    continue
                new_mask = current_mask | candidate.task_mask
                if new_mask == current_mask:
                    continue
                if new_mask not in queued_masks:
                    heapq.heappush(pending_masks, new_mask)
                    queued_masks.add(new_mask)
                _add_pareto_label(
                    labels_by_mask.setdefault(new_mask, []),
                    _extend_label(data, label, candidate.sortie, candidate.task_mask),
                )

    best_by_mask: dict[int, _JourneyLabel] = {}
    pareto_count = 0
    for mask, labels in labels_by_mask.items():
        if mask == 0:
            continue
        pareto_count += len(labels)
        best_by_mask[mask] = min(labels, key=lambda label: (label.objective(data), label.end_time, len(label.sorties)))
    return (
        best_by_mask,
        generated_sortie_count,
        route_template_count,
        pareto_count,
        journey_label_bound_pruned_count,
        direct_bound_pruning_root_bound,
        bound_pruning_active,
    )


def _direct_sortie_candidates_from_start(
    data: LunarIceData,
    task_to_bit: dict[str, int],
    *,
    remaining_mask: int,
    start_time: float,
    deadline: float | None = None,
    path_type_cache: dict[tuple[str, str], tuple[str, ...]] | None = None,
    path_type_lb_cache: dict[tuple[str, str], tuple[float, float, float]] | None = None,
    prefix_task_mask: int = 0,
    prefix_base_cost: float = 0.0,
    full_mask: int | None = None,
    incumbent_upper_bound: float | None = None,
    remaining_lower_bound=None,
    return_lower_bound=None,
) -> tuple[list[_SortieCandidate], int, int, int]:
    bit_to_task = {bit: task_id for task_id, bit in task_to_bit.items()}
    path_type_cache = path_type_cache or _nondominated_path_type_cache(data)
    path_type_lb_cache = path_type_lb_cache or _path_type_lower_bound_cache(data, path_type_cache)
    max_len = min(len(data.task_ids), int(data.max_tasks_per_trip), int(remaining_mask).bit_count())
    initial = _PartialSortieLabel(
        task_mask=0,
        last_task="depot",
        sequence=tuple(),
        path_types=tuple(),
        start_time=round(float(start_time), 6),
        elapsed=round(float(start_time), 6),
        service_starts={},
        travel_time=0.0,
        distance_km=0.0,
        energy_proxy=0.0,
        risk_integral=0.0,
        shadow_exposure_min=0.0,
        demand=0.0,
        service_cost=0.0,
        discovery_completion_term=0.0,
        base_cost=0.0,
    )
    current_level = [initial]
    candidates_by_mask: dict[int, list[_SortieCandidate]] = {}
    generated_count = 0
    route_count = 0
    bound_pruned_count = 0
    incumbent_bound = _finite_upper_bound(incumbent_upper_bound)

    for _depth in range(1, max_len + 1):
        _raise_if_sortie_generation_deadline_exceeded(
            deadline,
            generated_count=generated_count,
            route_count=route_count,
            journey_label_bound_pruned_count=bound_pruned_count,
        )
        next_by_key: dict[tuple[int, str], list[_PartialSortieLabel]] = {}
        for label_index, label in enumerate(current_level):
            if label_index % 64 == 0:
                _raise_if_sortie_generation_deadline_exceeded(
                    deadline,
                    generated_count=generated_count,
                    route_count=route_count,
                    journey_label_bound_pruned_count=bound_pruned_count,
                )
            if _partial_sortie_bound_exceeds_incumbent(
                label,
                prefix_task_mask=int(prefix_task_mask),
                prefix_base_cost=float(prefix_base_cost),
                full_mask=full_mask,
                incumbent_bound=incumbent_bound,
                remaining_lower_bound=remaining_lower_bound,
                return_lower_bound=return_lower_bound,
                task_to_bit=task_to_bit,
            ):
                bound_pruned_count += 1
                continue
            available = int(remaining_mask) & ~int(label.task_mask)
            while available:
                bit = available & -available
                available -= bit
                task_id = bit_to_task[bit]
                task = data.tasks[task_id]
                if float(label.demand) + float(task.demand) > float(data.capacity) + 1.0e-9:
                    continue
                arc_key = (str(label.last_task), str(task_id))
                min_travel, min_energy, min_shadow = path_type_lb_cache[arc_key]
                earliest_service_start = max(float(label.elapsed) + min_travel, float(task.ready_time))
                if earliest_service_start > float(task.due_time) - float(task.service_time) + 1.0e-9:
                    continue
                if (
                    float(label.energy_proxy) + min_energy + float(task.service_energy)
                    > float(data.energy_limit) + 1.0e-9
                ):
                    continue
                service_shadow = float(task.local_shadow_score) * float(task.service_time)
                if (
                    float(label.shadow_exposure_min) + min_shadow + service_shadow
                    > float(data.max_shadow_exposure_per_sortie) + 1.0e-9
                ):
                    continue
                for path_type in path_type_cache[arc_key]:
                    generated_count += 1
                    if generated_count % 4096 == 0:
                        _raise_if_sortie_generation_deadline_exceeded(
                            deadline,
                            generated_count=generated_count,
                            route_count=route_count,
                            journey_label_bound_pruned_count=bound_pruned_count,
                        )
                    extended = _extend_partial_sortie_label(data, label, task_id, bit, path_type)
                    if extended is None:
                        continue
                    if _partial_sortie_bound_exceeds_incumbent(
                        extended,
                        prefix_task_mask=int(prefix_task_mask),
                        prefix_base_cost=float(prefix_base_cost),
                        full_mask=full_mask,
                        incumbent_bound=incumbent_bound,
                        remaining_lower_bound=remaining_lower_bound,
                        return_lower_bound=return_lower_bound,
                        task_to_bit=task_to_bit,
                    ):
                        bound_pruned_count += 1
                        continue
                    key = (extended.task_mask, extended.last_task)
                    _add_partial_sortie_label(next_by_key.setdefault(key, []), extended)
        current_level = [label for labels in next_by_key.values() for label in labels]
        for label_index, label in enumerate(current_level):
            if label_index % 64 == 0:
                _raise_if_sortie_generation_deadline_exceeded(
                    deadline,
                    generated_count=generated_count,
                    route_count=route_count,
                    journey_label_bound_pruned_count=bound_pruned_count,
                )
            for return_index, return_path_type in enumerate(path_type_cache[(str(label.last_task), "depot")]):
                generated_count += 1
                if return_index % 256 == 0:
                    _raise_if_sortie_generation_deadline_exceeded(
                        deadline,
                        generated_count=generated_count,
                        route_count=route_count,
                        journey_label_bound_pruned_count=bound_pruned_count,
                    )
                candidate = _close_partial_sortie_label(data, label, return_path_type)
                if candidate is None:
                    continue
                route_count += 1
                _add_sortie_candidate(candidates_by_mask.setdefault(candidate.task_mask, []), candidate)

    return (
        [candidate for values in candidates_by_mask.values() for candidate in values],
        generated_count,
        route_count,
        bound_pruned_count,
    )


def _partial_sortie_bound_exceeds_incumbent(
    label: _PartialSortieLabel,
    *,
    prefix_task_mask: int,
    prefix_base_cost: float,
    full_mask: int | None,
    incumbent_bound: float | None,
    remaining_lower_bound,
    return_lower_bound,
    task_to_bit: dict[str, int],
) -> bool:
    if incumbent_bound is None or full_mask is None or remaining_lower_bound is None:
        return False
    covered = int(prefix_task_mask) | int(label.task_mask)
    remaining = int(full_mask) & ~covered
    possible_final_mask = int(remaining)
    if label.last_task != "depot":
        possible_final_mask |= int(task_to_bit.get(str(label.last_task), 0))
    optimistic_total = (
        float(prefix_base_cost)
        + float(label.base_cost)
        + float(remaining_lower_bound(remaining, float(label.elapsed)))
        + (0.0 if return_lower_bound is None else float(return_lower_bound(possible_final_mask)))
    )
    return optimistic_total > float(incumbent_bound) + 1.0e-9


def _direct_bound_pruning_active(
    full_mask: int,
    *,
    incumbent_bound: float | None,
    root_bound: float | None,
) -> bool:
    _ = full_mask
    if incumbent_bound is None or root_bound is None:
        return False
    if float(incumbent_bound) <= 1.0e-12:
        return False
    return root_bound >= float(_DIRECT_BOUND_PRUNING_MIN_ROOT_RATIO) * float(incumbent_bound)


def _direct_bound_pruning_root_bound(
    full_mask: int,
    *,
    tail_lower_bound,
) -> float | None:
    if tail_lower_bound is None:
        return None
    return round(float(tail_lower_bound(int(full_mask), 0.0)), 9)


def _extend_partial_sortie_label(
    data: LunarIceData,
    label: _PartialSortieLabel,
    task_id: str,
    task_bit: int,
    path_type: str,
) -> _PartialSortieLabel | None:
    task = data.tasks[task_id]
    option = data.option(label.last_task, task_id, path_type)
    elapsed = float(label.elapsed) + float(option.travel_time_min)
    service_start = max(elapsed, float(task.ready_time))
    if service_start > float(task.due_time) - float(task.service_time) + 1.0e-9:
        return None
    elapsed = service_start + float(task.service_time)
    demand = float(label.demand) + float(task.demand)
    if demand > float(data.capacity) + 1.0e-9:
        return None
    energy = float(label.energy_proxy) + float(option.energy_proxy) + float(task.service_energy)
    if energy > float(data.energy_limit) + 1.0e-9:
        return None
    risk = (
        float(label.risk_integral)
        + float(option.risk_integral)
        + float(task.local_thermal_risk) * float(task.service_time) * 0.01
    )
    shadow = (
        float(label.shadow_exposure_min)
        + float(option.shadow_exposure_min)
        + float(task.local_shadow_score) * float(task.service_time)
    )
    if shadow > float(data.max_shadow_exposure_per_sortie) + 1.0e-9:
        return None
    service_cost = float(label.service_cost) + float(task.service_cost)
    completion = float(label.discovery_completion_term) + float(task.science_weight) * elapsed
    distance = float(label.distance_km) + float(option.distance_km)
    base_cost = additive_objective_value(
        data,
        operating_cost=operating_cost_value(
            service_cost=service_cost,
            distance_km=distance,
            energy_proxy=energy,
        ),
        risk_integral=risk,
        weighted_completion_time=completion,
    )
    service_starts = dict(label.service_starts)
    service_starts[task_id] = round(service_start, 6)
    return _PartialSortieLabel(
        task_mask=int(label.task_mask) | int(task_bit),
        last_task=task_id,
        sequence=(*label.sequence, task_id),
        path_types=(*label.path_types, path_type),
        start_time=label.start_time,
        elapsed=round(elapsed, 6),
        service_starts=service_starts,
        travel_time=round(float(label.travel_time) + float(option.travel_time_min), 6),
        distance_km=round(distance, 6),
        energy_proxy=round(energy, 6),
        risk_integral=round(risk, 6),
        shadow_exposure_min=round(shadow, 6),
        demand=round(demand, 6),
        service_cost=round(service_cost, 6),
        discovery_completion_term=round(completion, 6),
        base_cost=round(base_cost, 6),
    )


def _nondominated_path_types(data: LunarIceData, source: str, target: str) -> tuple[str, ...]:
    options = data.arcs[(str(source), str(target))]
    kept: list[str] = []
    for path_type in PATH_TYPES:
        option = options[str(path_type)]
        dominated = False
        for other_type in PATH_TYPES:
            if other_type == path_type:
                continue
            other = options[str(other_type)]
            weakly_better = (
                float(other.travel_time_min) <= float(option.travel_time_min) + 1.0e-9
                and float(other.distance_km) <= float(option.distance_km) + 1.0e-9
                and float(other.energy_proxy) <= float(option.energy_proxy) + 1.0e-9
                and float(other.risk_integral) <= float(option.risk_integral) + 1.0e-9
                and float(other.shadow_exposure_min) <= float(option.shadow_exposure_min) + 1.0e-9
            )
            strictly_better = (
                float(other.travel_time_min) < float(option.travel_time_min) - 1.0e-9
                or float(other.distance_km) < float(option.distance_km) - 1.0e-9
                or float(other.energy_proxy) < float(option.energy_proxy) - 1.0e-9
                or float(other.risk_integral) < float(option.risk_integral) - 1.0e-9
                or float(other.shadow_exposure_min) < float(option.shadow_exposure_min) - 1.0e-9
            )
            if weakly_better and strictly_better:
                dominated = True
                break
        if not dominated:
            kept.append(str(path_type))
    return tuple(kept)


def _nondominated_path_type_cache(data: LunarIceData) -> dict[tuple[str, str], tuple[str, ...]]:
    return {
        (source, target): _nondominated_path_types(data, source, target)
        for source, target in data.arcs
    }


def _path_type_lower_bound_cache(
    data: LunarIceData,
    path_type_cache: dict[tuple[str, str], tuple[str, ...]],
) -> dict[tuple[str, str], tuple[float, float, float]]:
    lower_bounds: dict[tuple[str, str], tuple[float, float, float]] = {}
    for (source, target), path_types in path_type_cache.items():
        options = [data.option(source, target, path_type) for path_type in path_types]
        lower_bounds[(source, target)] = (
            min(float(option.travel_time_min) for option in options),
            min(float(option.energy_proxy) for option in options),
            min(float(option.shadow_exposure_min) for option in options),
        )
    return lower_bounds


def path_option_dominance_audit(data: LunarIceData) -> dict:
    cache = _nondominated_path_type_cache(data)
    filtered_count = sum(max(0, len(PATH_TYPES) - len(kept)) for kept in cache.values())
    kept_count = sum(len(kept) for kept in cache.values())
    return {
        "policy": str(data.path_option_policy_id or PATH_OPTION_POLICY_ID),
        "path_types": tuple(PATH_TYPES),
        "arc_count": len(cache),
        "kept_count": int(kept_count),
        "filtered_count": int(filtered_count),
    }


def _close_partial_sortie_label(
    data: LunarIceData,
    label: _PartialSortieLabel,
    return_path_type: str,
) -> _SortieCandidate | None:
    if not label.sequence:
        return None
    back = data.option(label.last_task, "depot", return_path_type)
    return_time = float(label.elapsed) + float(back.travel_time_min)
    energy = float(label.energy_proxy) + float(back.energy_proxy)
    if energy > float(data.energy_limit) + 1.0e-9:
        return None
    risk = float(label.risk_integral) + float(back.risk_integral)
    shadow = float(label.shadow_exposure_min) + float(back.shadow_exposure_min)
    if shadow > float(data.max_shadow_exposure_per_sortie) + 1.0e-9:
        return None
    recharge = float(data.dock_overhead_min) + energy / max(1.0e-9, float(data.recharge_power_proxy_per_min))
    end_time = return_time + recharge
    if end_time > float(data.horizon) + 1.0e-9:
        return None
    path_types = (*label.path_types, return_path_type)
    current = "depot"
    legs: list[SortieLeg] = []
    for index, task_id in enumerate(label.sequence):
        legs.append(SortieLeg(source=current, target=task_id, path_type=path_types[index]))
        current = task_id
    legs.append(SortieLeg(source=current, target="depot", path_type=return_path_type))
    sortie = TimedSortie(
        tasks=tuple(label.sequence),
        legs=tuple(legs),
        start_time=round(float(label.start_time), 6),
        service_starts=dict(label.service_starts),
        return_time=round(return_time, 6),
        recharge_time=round(recharge, 6),
        end_time=round(end_time, 6),
        travel_time=round(float(label.travel_time) + float(back.travel_time_min), 6),
        distance_km=round(float(label.distance_km) + float(back.distance_km), 6),
        energy_proxy=round(energy, 6),
        risk_integral=round(risk, 6),
        service_cost=round(float(label.service_cost), 6),
        shadow_exposure_min=round(shadow, 6),
        demand=round(float(label.demand), 6),
        discovery_completion_term=round(float(label.discovery_completion_term), 6),
        task_completion_times={
            task_id: round(float(label.service_starts[task_id]) + float(data.tasks[task_id].service_time), 6)
            for task_id in label.sequence
        },
        feasible=True,
    )
    base_cost = sortie_objective_value(data, sortie)
    return _SortieCandidate(task_mask=int(label.task_mask), sortie=sortie, base_cost=round(base_cost, 6))


def _add_partial_sortie_label(labels: list[_PartialSortieLabel], candidate: _PartialSortieLabel) -> None:
    kept: list[_PartialSortieLabel] = []
    for old in labels:
        if (
            float(old.elapsed) <= float(candidate.elapsed) + 1.0e-9
            and float(old.energy_proxy) <= float(candidate.energy_proxy) + 1.0e-9
            and float(old.shadow_exposure_min) <= float(candidate.shadow_exposure_min) + 1.0e-9
            and float(old.base_cost) <= float(candidate.base_cost) + 1.0e-9
        ):
            return
        if (
            float(candidate.elapsed) <= float(old.elapsed) + 1.0e-9
            and float(candidate.energy_proxy) <= float(old.energy_proxy) + 1.0e-9
            and float(candidate.shadow_exposure_min) <= float(old.shadow_exposure_min) + 1.0e-9
            and float(candidate.base_cost) <= float(old.base_cost) + 1.0e-9
        ):
            continue
        kept.append(old)
    kept.append(candidate)
    labels[:] = kept


def _add_sortie_candidate(labels: list[_SortieCandidate], candidate: _SortieCandidate) -> None:
    kept: list[_SortieCandidate] = []
    for old in labels:
        if (
            float(old.sortie.end_time) <= float(candidate.sortie.end_time) + 1.0e-9
            and float(old.base_cost) <= float(candidate.base_cost) + 1.0e-9
        ):
            return
        if (
            float(candidate.sortie.end_time) <= float(old.sortie.end_time) + 1.0e-9
            and float(candidate.base_cost) <= float(old.base_cost) + 1.0e-9
        ):
            continue
        kept.append(old)
    kept.append(candidate)
    labels[:] = kept


def _enumerate_sortie_templates(
    data: LunarIceData,
    task_to_bit: dict[str, int],
    *,
    mode: str,
) -> tuple[dict[int, list[_SortieTemplate]], int]:
    templates_by_mask: dict[int, list[_SortieTemplate]] = {}
    sortie_counter = 0
    for sequence in _candidate_sequences(data.task_ids, data.max_tasks_per_trip):
        task_mask = 0
        for task_id in sequence:
            task_mask |= task_to_bit[task_id]
        for path_types in _path_type_assignments(sequence, mode=mode):
            sortie_counter += 1
            if not build_timed_sortie(data, sequence, path_types, start_time=0.0).feasible:
                continue
            templates_by_mask.setdefault(task_mask, []).append(
                _SortieTemplate(task_mask=task_mask, sequence=tuple(sequence), path_types=path_types)
            )
    return templates_by_mask, sortie_counter


def _path_type_assignments(sequence: tuple[str, ...], *, mode: str) -> Iterable[tuple[str, ...]]:
    if mode == "canonical":
        for policy in CANONICAL_PATH_POLICIES:
            yield tuple(policy[0] for _ in range(len(sequence) + 1))
        return
    if mode == "direct":
        yield from product(PATH_TYPES, repeat=len(sequence) + 1)
        return
    raise ValueError(f"unknown path enumeration mode: {mode}")


def _candidate_sequences(remaining: Iterable[str], max_tasks_per_trip: int) -> Iterable[tuple[str, ...]]:
    ordered = tuple(sorted(remaining))
    limit = min(len(ordered), int(max_tasks_per_trip))
    for length in range(1, limit + 1):
        yield from permutations(ordered, length)


def _build_single_vehicle_journeys(
    data: LunarIceData,
    templates_by_mask: dict[int, list[_SortieTemplate]],
) -> tuple[dict[int, _JourneyLabel], int]:
    full_mask = _full_task_mask(data)
    labels_by_mask: dict[int, list[_JourneyLabel]] = {
        0: [_JourneyLabel(task_mask=0, sorties=tuple(), end_time=0.0, base_cost=0.0)]
    }
    for current_mask in range(full_mask + 1):
        current_labels = list(labels_by_mask.get(current_mask, []))
        if not current_labels:
            continue
        remaining_mask = full_mask ^ current_mask
        submask = remaining_mask
        while submask:
            for template in templates_by_mask.get(submask, []):
                for label in current_labels:
                    sortie = build_timed_sortie(data, template.sequence, template.path_types, start_time=label.end_time)
                    if not sortie.feasible:
                        continue
                    _add_pareto_label(
                        labels_by_mask.setdefault(current_mask | submask, []),
                        _extend_label(data, label, sortie, template.task_mask),
                    )
            submask = (submask - 1) & remaining_mask

    best_by_mask: dict[int, _JourneyLabel] = {}
    pareto_count = 0
    for mask, labels in labels_by_mask.items():
        if mask == 0:
            continue
        pareto_count += len(labels)
        best_by_mask[mask] = min(labels, key=lambda label: (label.objective(data), label.end_time, len(label.sorties)))
    return best_by_mask, pareto_count


def _extend_label(data: LunarIceData, label: _JourneyLabel, sortie: TimedSortie, task_mask: int) -> _JourneyLabel:
    add_base = sortie_objective_value(data, sortie)
    return _JourneyLabel(
        task_mask=label.task_mask | task_mask,
        sorties=(*label.sorties, sortie),
        end_time=sortie.end_time,
        base_cost=round(label.base_cost + add_base, 6),
    )


def _add_pareto_label(labels: list[_JourneyLabel], candidate: _JourneyLabel) -> None:
    kept: list[_JourneyLabel] = []
    for old in labels:
        if old.end_time <= candidate.end_time + 1.0e-9 and old.base_cost <= candidate.base_cost + 1.0e-9:
            return
        if candidate.end_time <= old.end_time + 1.0e-9 and candidate.base_cost <= old.base_cost + 1.0e-9:
            continue
        kept.append(old)
    kept.append(candidate)
    labels[:] = kept


def _select_vehicle_partition(
    data: LunarIceData,
    best_label_by_mask: dict[int, _JourneyLabel],
    *,
    deadline: float | None = None,
) -> tuple[tuple[_JourneyLabel, ...] | None, int]:
    full_mask = _full_task_mask(data)
    if not best_label_by_mask:
        return None, 1
    cost_by_mask = {mask: label.objective(data) for mask, label in best_label_by_mask.items()}
    masks_by_required_bit: dict[int, list[int]] = {}
    for mask in best_label_by_mask:
        bits = int(mask)
        while bits:
            bit = bits & -bits
            bits -= bit
            masks_by_required_bit.setdefault(bit, []).append(mask)
    max_cover_size = max(int(mask).bit_count() for mask in best_label_by_mask)
    best_value = float("inf")
    best_masks: tuple[int, ...] | None = None
    state_count = 0
    use_large_partition_bounds = len(data.task_ids) > 20
    if use_large_partition_bounds:
        for masks in masks_by_required_bit.values():
            masks.sort(
                key=lambda mask: (
                    float(cost_by_mask[mask]) / max(1, int(mask).bit_count()),
                    float(cost_by_mask[mask]),
                    -int(mask).bit_count(),
                    mask,
                )
            )
        try:
            service_lb = _remaining_task_visit_lower_bound_fn(data)
            dual_lb = _remaining_cover_dual_lower_bound_fn(
                cost_by_mask,
                masks_by_required_bit,
                task_count=len(data.task_ids),
                deadline=deadline,
            )
            cardinality_lb = _remaining_cardinality_lower_bound_fn(
                cost_by_mask,
                task_count=len(data.task_ids),
                max_slots=int(data.fleet_size),
                deadline=deadline,
            )
            lp_cover_lb = (
                _remaining_lp_cover_lower_bound_fn(
                    cost_by_mask,
                    task_count=len(data.task_ids),
                    deadline=deadline,
                )
                if _remaining_wall_time(deadline) >= 180.0
                else (lambda _mask: 0.0)
            )
            remaining_lb = lambda mask: max(service_lb(mask), dual_lb(mask), lp_cover_lb(mask))
            remaining_slot_lb = lambda mask, slots: max(remaining_lb(mask), cardinality_lb(mask, slots))
            incumbent_candidates = [
                _greedy_partition_cover(
                    full_mask,
                    int(data.fleet_size),
                    cost_by_mask=cost_by_mask,
                    masks_by_required_bit=masks_by_required_bit,
                ),
                _beam_partition_cover(
                    full_mask,
                    int(data.fleet_size),
                    cost_by_mask=cost_by_mask,
                    masks_by_required_bit=masks_by_required_bit,
                    lower_bound=remaining_lb,
                    deadline=deadline,
                ),
            ]
        except DirectBaselineTimeLimitExceeded as exc:
            raise DirectBaselineTimeLimitExceeded(
                stage="fleet_set_partition",
                generated_journey_count=len(best_label_by_mask),
                generated_sortie_count=0,
                route_template_count=0,
                pareto_label_count=0,
                set_partition_state_count=state_count,
            ) from exc
        for incumbent_masks in incumbent_candidates:
            if incumbent_masks is None:
                continue
            incumbent_value = sum(float(cost_by_mask[mask]) for mask in incumbent_masks)
            if incumbent_value < best_value - 1.0e-9:
                best_masks = incumbent_masks
                best_value = incumbent_value
    else:
        for masks in masks_by_required_bit.values():
            masks.sort(key=lambda mask: (-int(mask).bit_count(), cost_by_mask[mask], mask))
        remaining_lb = lambda _mask: 0.0
        remaining_slot_lb = lambda _mask, _slots: 0.0
    branch_bits_by_support = _branch_bits_by_support(masks_by_required_bit)
    state_best_accumulated: dict[tuple[int, int], float] = {}

    def branch_bit_for(remaining_mask: int) -> int:
        if not use_large_partition_bounds:
            return remaining_mask & -remaining_mask
        return _static_branch_bit(remaining_mask, branch_bits_by_support)

    def search(remaining_mask: int, vehicle_slots: int, accumulated_cost: float, chosen_masks: list[int]) -> None:
        nonlocal best_value, best_masks, state_count
        try:
            _raise_if_deadline_exceeded(deadline)
        except DirectBaselineTimeLimitExceeded as exc:
            raise DirectBaselineTimeLimitExceeded(
                stage="fleet_set_partition",
                generated_journey_count=len(best_label_by_mask),
                generated_sortie_count=0,
                route_template_count=0,
                pareto_label_count=0,
                set_partition_state_count=state_count,
            ) from exc
        state_count += 1
        if remaining_mask == 0:
            if accumulated_cost < best_value - 1.0e-9:
                best_value = accumulated_cost
                best_masks = tuple(chosen_masks)
            return
        if vehicle_slots <= 0:
            return
        if accumulated_cost >= best_value - 1.0e-9:
            return
        if accumulated_cost + remaining_slot_lb(remaining_mask, vehicle_slots) >= best_value - 1.0e-9:
            return
        if int(remaining_mask).bit_count() > int(vehicle_slots) * max_cover_size:
            return
        if use_large_partition_bounds:
            state_key = (int(remaining_mask), int(vehicle_slots))
            previous_best = state_best_accumulated.get(state_key)
            if previous_best is not None and previous_best <= accumulated_cost + 1.0e-9:
                return
            state_best_accumulated[state_key] = float(accumulated_cost)
        if vehicle_slots == 1:
            label_cost = cost_by_mask.get(remaining_mask)
            if label_cost is not None and accumulated_cost + label_cost < best_value - 1.0e-9:
                best_value = accumulated_cost + label_cost
                best_masks = tuple((*chosen_masks, remaining_mask))
            return
        if vehicle_slots == 2:
            direct_cost = cost_by_mask.get(remaining_mask)
            if direct_cost is not None and accumulated_cost + direct_cost < best_value - 1.0e-9:
                best_value = accumulated_cost + direct_cost
                best_masks = tuple((*chosen_masks, remaining_mask))
            required_bit = branch_bit_for(remaining_mask)
            for mask in masks_by_required_bit.get(required_bit, []):
                if mask & remaining_mask != mask:
                    continue
                complement = remaining_mask ^ mask
                if complement == 0:
                    continue
                label_cost = cost_by_mask.get(complement)
                if label_cost is None:
                    continue
                next_cost = accumulated_cost + cost_by_mask[mask] + label_cost
                if next_cost < best_value - 1.0e-9:
                    best_value = next_cost
                    best_masks = tuple((*chosen_masks, mask, complement))
            return
        required_bit = branch_bit_for(remaining_mask)
        for mask in masks_by_required_bit.get(required_bit, []):
            if mask & remaining_mask != mask:
                continue
            remaining_after = remaining_mask ^ mask
            if int(remaining_after).bit_count() > int(vehicle_slots - 1) * max_cover_size:
                continue
            next_cost = accumulated_cost + cost_by_mask[mask]
            if next_cost >= best_value - 1.0e-9:
                continue
            if next_cost + remaining_slot_lb(remaining_after, vehicle_slots - 1) >= best_value - 1.0e-9:
                continue
            search(remaining_after, vehicle_slots - 1, next_cost, [*chosen_masks, mask])

    search(full_mask, data.fleet_size, 0.0, [])
    if best_masks is None:
        return None, state_count
    return tuple(best_label_by_mask[mask] for mask in best_masks), state_count


def _greedy_partition_cover(
    full_mask: int,
    vehicle_slots: int,
    *,
    cost_by_mask: dict[int, float],
    masks_by_required_bit: dict[int, list[int]],
) -> tuple[int, ...] | None:
    branch_bits_by_support = _branch_bits_by_support(masks_by_required_bit)
    remaining_mask = int(full_mask)
    slots = int(vehicle_slots)
    chosen: list[int] = []
    while remaining_mask:
        if slots <= 0:
            return None
        required_bit = _static_branch_bit(remaining_mask, branch_bits_by_support)
        candidates = [
            mask
            for mask in masks_by_required_bit.get(required_bit, [])
            if mask & remaining_mask == mask
        ]
        if not candidates:
            return None
        mask = min(candidates, key=lambda row: (-int(row).bit_count(), float(cost_by_mask[row]), row))
        chosen.append(mask)
        remaining_mask ^= mask
        slots -= 1
    return tuple(chosen)


def _beam_partition_cover(
    full_mask: int,
    vehicle_slots: int,
    *,
    cost_by_mask: dict[int, float],
    masks_by_required_bit: dict[int, list[int]],
    lower_bound,
    deadline: float | None = None,
    beam_width: int = 4096,
    branch_limit: int = 96,
) -> tuple[int, ...] | None:
    """Find a feasible partition quickly; the result is only an incumbent."""

    branch_bits_by_support = _branch_bits_by_support(masks_by_required_bit)
    states: list[tuple[float, float, int, int, tuple[int, ...]]] = [
        (float(lower_bound(full_mask)), 0.0, int(full_mask), int(vehicle_slots), tuple())
    ]
    best_complete: tuple[float, tuple[int, ...]] | None = None
    for _depth in range(max(1, int(vehicle_slots))):
        _raise_if_deadline_exceeded(deadline)
        next_states: list[tuple[float, float, int, int, tuple[int, ...]]] = []
        for _score, cost, remaining_mask, slots, chosen in states:
            _raise_if_deadline_exceeded(deadline)
            if remaining_mask == 0:
                if best_complete is None or cost < best_complete[0] - 1.0e-9:
                    best_complete = (cost, chosen)
                continue
            if slots <= 0:
                continue
            required_bit = _static_branch_bit(remaining_mask, branch_bits_by_support)
            candidates: list[int] = []
            scanned = 0
            for mask in masks_by_required_bit.get(required_bit, []):
                scanned += 1
                if scanned % 1024 == 0:
                    _raise_if_deadline_exceeded(deadline)
                if mask & remaining_mask != mask:
                    continue
                candidates.append(mask)
                if len(candidates) >= max(1, int(branch_limit)):
                    break
            for mask in candidates:
                next_remaining = remaining_mask ^ mask
                next_cost = cost + float(cost_by_mask[mask])
                next_chosen = (*chosen, mask)
                if next_remaining == 0:
                    if best_complete is None or next_cost < best_complete[0] - 1.0e-9:
                        best_complete = (next_cost, next_chosen)
                    continue
                next_slots = slots - 1
                if next_slots <= 0:
                    continue
                score = next_cost + float(lower_bound(next_remaining))
                next_states.append((score, next_cost, next_remaining, next_slots, next_chosen))
        if best_complete is not None:
            return best_complete[1]
        if not next_states:
            return None
        next_states.sort(key=lambda row: (row[0], row[1], int(row[2]).bit_count(), row[2]))
        states = next_states[: max(1, int(beam_width))]
    return best_complete[1] if best_complete is not None else None


def _branch_bits_by_support(masks_by_required_bit: dict[int, list[int]]) -> tuple[int, ...]:
    return tuple(sorted(masks_by_required_bit, key=lambda bit: (len(masks_by_required_bit[bit]), bit)))


def _static_branch_bit(remaining_mask: int, branch_bits_by_support: tuple[int, ...]) -> int:
    for bit in branch_bits_by_support:
        if int(remaining_mask) & int(bit):
            return int(bit)
    return int(remaining_mask) & -int(remaining_mask)


def _remaining_lp_cover_lower_bound_fn(
    cost_by_mask: dict[int, float],
    *,
    task_count: int,
    deadline: float | None = None,
    max_rounds: int = 10,
    initial_constraint_count: int = 224,
    add_per_round: int = 200,
):
    """Build a feasible nonnegative cover-dual lower bound by constraint generation."""

    if not cost_by_mask or any(float(cost) < -1.0e-9 for cost in cost_by_mask.values()):
        return lambda _mask: 0.0
    task_count = int(task_count)
    objective = [1.0 for _ in range(task_count)]
    active: set[int] = set()
    for mask in cost_by_mask:
        if int(mask) & (int(mask) - 1) == 0:
            active.add(int(mask))
    for mask, _cost in sorted(
        cost_by_mask.items(),
        key=lambda item: (
            float(item[1]) / max(1, int(item[0]).bit_count()),
            float(item[1]),
            -int(item[0]).bit_count(),
            int(item[0]),
        ),
    )[: max(0, int(initial_constraint_count))]:
        active.add(int(mask))

    best_feasible_dual: tuple[float, ...] | None = None
    best_feasible_value = 0.0
    current_dual: tuple[float, ...] = tuple(0.0 for _ in range(task_count))
    for _round in range(max(1, int(max_rounds))):
        _raise_if_deadline_exceeded(deadline)
        rows: list[list[float]] = []
        rhs: list[float] = []
        for mask in active:
            rows.append(_mask_row(mask, task_count))
            rhs.append(float(cost_by_mask[mask]))
        simplex = _simplex_max_leq(objective, rows, rhs, max_pivots=1000)
        if simplex.status != "OPTIMAL" or simplex.objective is None:
            break
        current_dual = tuple(max(0.0, float(value)) for value in simplex.solution)
        violations: list[tuple[float, int]] = []
        feasible_scale = 1.0
        for index, (mask, cost) in enumerate(cost_by_mask.items()):
            if index % 4096 == 0:
                _raise_if_deadline_exceeded(deadline)
            value = _mask_dual_sum(mask, current_dual)
            if value > 1.0e-12:
                feasible_scale = min(feasible_scale, float(cost) / value)
            violation = value - float(cost)
            if violation > 1.0e-6:
                violations.append((float(violation), int(mask)))
        scale = max(0.0, min(1.0, feasible_scale) * (1.0 - 1.0e-10))
        scaled_dual = tuple(scale * value for value in current_dual)
        scaled_value = sum(scaled_dual)
        if scaled_value > best_feasible_value + 1.0e-9:
            best_feasible_value = scaled_value
            best_feasible_dual = scaled_dual
        if not violations:
            best_feasible_dual = current_dual
            best_feasible_value = sum(current_dual)
            break
        for _violation, mask in heapq.nlargest(max(1, int(add_per_round)), violations):
            active.add(mask)

    dual = best_feasible_dual or tuple(0.0 for _ in range(task_count))

    def lower_bound(mask: int) -> float:
        return _mask_dual_sum(int(mask), dual)

    return lower_bound


def _mask_row(mask: int, task_count: int) -> list[float]:
    row = [0.0 for _ in range(int(task_count))]
    bits = int(mask)
    while bits:
        bit = bits & -bits
        bits -= bit
        index = bit.bit_length() - 1
        if 0 <= index < int(task_count):
            row[index] = 1.0
    return row


def _mask_dual_sum(mask: int, dual: tuple[float, ...]) -> float:
    bits = int(mask)
    value = 0.0
    while bits:
        bit = bits & -bits
        bits -= bit
        index = bit.bit_length() - 1
        if 0 <= index < len(dual):
            value += float(dual[index])
    return value


def _remaining_cardinality_lower_bound_fn(
    cost_by_mask: dict[int, float],
    *,
    task_count: int,
    max_slots: int,
    deadline: float | None = None,
):
    """Relax the partition tail to cheapest column sizes covering enough tasks."""

    if not cost_by_mask or any(float(cost) < -1.0e-9 for cost in cost_by_mask.values()):
        return lambda _mask, _slots: 0.0
    task_count = int(task_count)
    max_slots = max(0, int(max_slots))
    best_cost_by_size: dict[int, float] = {}
    for mask, cost in cost_by_mask.items():
        size = int(mask).bit_count()
        if size <= 0:
            continue
        best_cost_by_size[size] = min(float(cost), best_cost_by_size.get(size, float("inf")))
    if not best_cost_by_size:
        return lambda _mask, _slots: 0.0

    dp = [[float("inf")] * (task_count + 1) for _ in range(max_slots + 1)]
    dp[0][0] = 0.0
    suffix_best = [[float("inf")] * (task_count + 1) for _ in range(max_slots + 1)]
    for slot in range(1, max_slots + 1):
        _raise_if_deadline_exceeded(deadline)
        previous = dp[slot - 1]
        current = list(previous)
        for covered, value in enumerate(previous):
            if value == float("inf"):
                continue
            for size, cost in best_cost_by_size.items():
                next_covered = min(task_count, covered + int(size))
                candidate = float(value) + float(cost)
                if candidate < current[next_covered]:
                    current[next_covered] = candidate
        dp[slot] = current
    for slot in range(max_slots + 1):
        best = float("inf")
        for covered in range(task_count, -1, -1):
            best = min(best, dp[slot][covered])
            suffix_best[slot][covered] = best

    def lower_bound(mask: int, slots: int) -> float:
        slots = max(0, min(int(slots), max_slots))
        required = max(0, min(task_count, int(mask).bit_count()))
        value = suffix_best[slots][required]
        return value if value != float("inf") else float("inf")

    return lower_bound


def _remaining_cover_dual_lower_bound_fn(
    cost_by_mask: dict[int, float],
    masks_by_required_bit: dict[int, list[int]],
    *,
    task_count: int,
    deadline: float | None = None,
):
    """Build dual-feasible task-cover lower bounds for the partition tail."""

    if not cost_by_mask or any(float(cost) < -1.0e-9 for cost in cost_by_mask.values()):
        return lambda _mask: 0.0
    bits = tuple(1 << index for index in range(int(task_count)))
    support_size = {bit: len(masks_by_required_bit.get(bit, ())) for bit in bits}
    singleton_cost = {bit: float(cost_by_mask.get(bit, float("inf"))) for bit in bits}
    orders: list[tuple[int, ...]] = []

    def add_order(order: Iterable[int]) -> None:
        ordered = tuple(int(bit) for bit in order)
        if ordered and ordered not in orders:
            orders.append(ordered)

    add_order(bits)
    add_order(reversed(bits))
    add_order(sorted(bits, key=lambda bit: (support_size[bit], singleton_cost[bit], bit)))
    add_order(sorted(bits, key=lambda bit: (singleton_cost[bit], support_size[bit], bit)))
    add_order(sorted(bits, key=lambda bit: (-singleton_cost[bit], support_size[bit], bit)))

    vectors: list[tuple[float, ...]] = []
    for order in orders:
        _raise_if_deadline_exceeded(deadline)
        vector = _build_cover_dual_vector(
            cost_by_mask,
            masks_by_required_bit,
            bits=bits,
            order=order,
            deadline=deadline,
        )
        if sum(vector) > 1.0e-9 and vector not in vectors:
            vectors.append(vector)
    if not vectors:
        return lambda _mask: 0.0

    cache: dict[int, float] = {0: 0.0}

    def lower_bound(mask: int) -> float:
        mask = int(mask)
        cached = cache.get(mask)
        if cached is not None:
            return cached
        best = 0.0
        for vector in vectors:
            bits_left = mask
            value = 0.0
            while bits_left:
                bit = bits_left & -bits_left
                bits_left -= bit
                value += vector[bit.bit_length() - 1]
            best = max(best, value)
        cache[mask] = max(0.0, best)
        return cache[mask]

    return lower_bound


def _build_cover_dual_vector(
    cost_by_mask: dict[int, float],
    masks_by_required_bit: dict[int, list[int]],
    *,
    bits: tuple[int, ...],
    order: tuple[int, ...],
    deadline: float | None = None,
) -> tuple[float, ...]:
    slack_by_mask = {mask: float(cost) for mask, cost in cost_by_mask.items()}
    dual_by_bit = {bit: 0.0 for bit in bits}
    for bit in order:
        _raise_if_deadline_exceeded(deadline)
        supports = masks_by_required_bit.get(bit, [])
        if not supports:
            continue
        increase = min(float(slack_by_mask[mask]) for mask in supports)
        increase = max(0.0, increase - 1.0e-9)
        if increase <= 1.0e-9:
            continue
        dual_by_bit[bit] += increase
        for index, mask in enumerate(supports):
            if index % 4096 == 0:
                _raise_if_deadline_exceeded(deadline)
            slack_by_mask[mask] = float(slack_by_mask[mask]) - increase
    return tuple(max(0.0, dual_by_bit[bit]) for bit in bits)


def _reference_solution_upper_bound(data: LunarIceData) -> _ReferenceSolutionUpperBound | None:
    payload = data.reference_solution
    if not isinstance(payload, Mapping):
        return None
    journeys_payload = list(payload.get("journeys") or [])
    if not journeys_payload or len(journeys_payload) > int(data.fleet_size):
        return None

    path_type_cache = _nondominated_path_type_cache(data)
    covered: set[str] = set()
    columns: list[JourneyColumn] = []
    for journey_payload in journeys_payload:
        sorties_payload = list((journey_payload or {}).get("sorties") or [])
        if not sorties_payload:
            continue
        sorties: list[TimedSortie] = []
        previous_end = 0.0
        for sortie_payload in sorties_payload:
            legs_payload = list((sortie_payload or {}).get("legs") or [])
            if not legs_payload:
                return None
            sequence = tuple(str(leg.get("to")) for leg in legs_payload if str(leg.get("to")) != "depot")
            path_types = tuple(str(leg.get("path_type")) for leg in legs_payload)
            if len(path_types) != len(sequence) + 1:
                return None
            if len(set(sequence)) != len(sequence):
                return None
            if covered.intersection(sequence):
                return None
            try:
                reference_start = float(sortie_payload.get("start_time", previous_end))
                sortie = _best_reference_sortie_for_sequence(
                    data,
                    sequence=sequence,
                    preferred_path_types=path_types,
                    start_time=max(reference_start, previous_end),
                    path_type_cache=path_type_cache,
                )
            except (KeyError, TypeError, ValueError):
                return None
            if sortie is None:
                return None
            if not sortie.feasible:
                return None
            sorties.append(sortie)
            covered.update(sequence)
            previous_end = float(sortie.end_time)
        if sorties:
            columns.append(build_journey_column(data, tuple(sorties)))

    if covered != set(data.task_ids) or len(columns) > int(data.fleet_size):
        return None
    objective = round(sum(float(column.objective) for column in columns), 6)
    if not isfinite(objective):
        return None
    return _ReferenceSolutionUpperBound(
        objective=objective,
        journeys=tuple(columns),
        source="instance_reference_solution_best_path_repair",
    )


def _best_reference_sortie_for_sequence(
    data: LunarIceData,
    *,
    sequence: tuple[str, ...],
    preferred_path_types: tuple[str, ...],
    start_time: float,
    path_type_cache: dict[tuple[str, str], tuple[str, ...]],
) -> TimedSortie | None:
    nodes = ("depot", *sequence, "depot")
    choices: list[tuple[str, ...]] = []
    for index, (source, target) in enumerate(zip(nodes[:-1], nodes[1:])):
        available = tuple(path_type_cache.get((str(source), str(target)), tuple()))
        if not available:
            return None
        preferred = preferred_path_types[index] if index < len(preferred_path_types) else ""
        ordered = tuple(dict.fromkeys((preferred, *available))) if preferred in available else available
        choices.append(tuple(ordered))

    best: tuple[tuple[float, float, float, tuple[str, ...]], TimedSortie] | None = None
    for path_types in product(*choices):
        sortie = build_timed_sortie(
            data,
            sequence,
            tuple(str(path_type) for path_type in path_types),
            start_time=start_time,
        )
        if not sortie.feasible:
            continue
        objective = build_journey_column(data, (sortie,)).objective
        key = (
            float(objective),
            float(sortie.end_time),
            float(sortie.return_time),
            tuple(str(path_type) for path_type in path_types),
        )
        if best is None or key < best[0]:
            best = (key, sortie)
    return None if best is None else best[1]


def _finite_upper_bound(value: float | None) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None


def _remaining_service_lower_bound_fn(data: LunarIceData):
    return _remaining_task_visit_lower_bound_fn(data)


def _remaining_task_visit_lower_bound_fn(data: LunarIceData):
    if (
        float(data.objective.weight_operating_cost) < 0.0
        or float(data.objective.weight_risk) < 0.0
        or float(data.objective.weight_completion) < 0.0
        or any(float(data.tasks[task_id].science_weight) < 0.0 for task_id in data.task_ids)
    ):
        return lambda _mask, _earliest_service_floor=0.0: 0.0
    refs = objective_references(data)
    min_inbound_by_task = _min_inbound_path_metric_by_task(data)
    static_by_bit: dict[int, float] = {}
    completion_coeff_by_bit: dict[int, float] = {}
    ready_by_bit: dict[int, float] = {}
    service_by_bit: dict[int, float] = {}
    for index, task_id in enumerate(data.task_ids):
        task = data.tasks[task_id]
        min_distance, min_energy, min_risk = min_inbound_by_task.get(str(task_id), (0.0, 0.0, 0.0))
        bit = 1 << index
        operating = operating_cost_value(
            service_cost=float(task.service_cost),
            distance_km=float(min_distance),
            energy_proxy=float(task.service_energy) + float(min_energy),
        )
        risk = service_risk_value(task) + float(min_risk)
        static_by_bit[bit] = max(
            0.0,
            float(data.objective.weight_operating_cost) * float(operating) / float(refs.reference_cost)
            + float(data.objective.weight_risk) * float(risk) / float(refs.reference_risk),
        )
        completion_coeff_by_bit[bit] = (
            float(data.objective.weight_completion)
            * float(task.science_weight)
            / float(refs.reference_completion)
        )
        ready_by_bit[bit] = max(0.0, float(task.ready_time))
        service_by_bit[bit] = max(0.0, float(task.service_time))
    cache: dict[tuple[int, float], float] = {(0, 0.0): 0.0}

    def lower_bound(mask: int, earliest_service_floor: float = 0.0) -> float:
        mask = int(mask)
        bucket = _lower_bound_time_bucket(earliest_service_floor)
        cached = cache.get((mask, bucket))
        if cached is not None:
            return cached
        bits = mask
        value = 0.0
        while bits:
            bit = bits & -bits
            bits -= bit
            completion_time_lb = max(ready_by_bit.get(bit, 0.0), bucket) + service_by_bit.get(bit, 0.0)
            value += (
                static_by_bit.get(bit, 0.0)
                + completion_coeff_by_bit.get(bit, 0.0) * completion_time_lb
            )
        cache[(mask, bucket)] = value
        return value

    return lower_bound


def _lower_bound_time_bucket(value: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not isfinite(number) or number <= 0.0:
        return 0.0
    bucket = max(1.0e-9, float(_TIME_AWARE_LB_BUCKET_MIN))
    return floor(number / bucket) * bucket


def _remaining_return_path_lower_bound_fn(data: LunarIceData):
    if (
        float(data.objective.weight_operating_cost) < 0.0
        or float(data.objective.weight_risk) < 0.0
        or float(data.objective.weight_completion) < 0.0
    ):
        return lambda _mask: 0.0
    refs = objective_references(data)
    by_bit: dict[int, float] = {}
    for index, task_id in enumerate(data.task_ids):
        best_distance = float("inf")
        best_energy = float("inf")
        best_risk = float("inf")
        options = data.arcs.get((str(task_id), "depot"), {})
        for option in options.values():
            best_distance = min(best_distance, float(option.distance_km))
            best_energy = min(best_energy, float(option.energy_proxy))
            best_risk = min(best_risk, float(option.risk_integral))
        if not isfinite(best_distance):
            by_bit[1 << index] = 0.0
            continue
        operating = operating_cost_value(
            service_cost=0.0,
            distance_km=max(0.0, best_distance),
            energy_proxy=max(0.0, best_energy),
        )
        value = (
            float(data.objective.weight_operating_cost) * float(operating) / float(refs.reference_cost)
            + float(data.objective.weight_risk) * max(0.0, float(best_risk)) / float(refs.reference_risk)
        )
        by_bit[1 << index] = max(0.0, float(value))
    cache = {0: 0.0}

    def lower_bound(mask: int) -> float:
        mask = int(mask)
        cached = cache.get(mask)
        if cached is not None:
            return cached
        bits = mask
        best = float("inf")
        while bits:
            bit = bits & -bits
            bits -= bit
            best = min(best, by_bit.get(bit, 0.0))
        value = 0.0 if best == float("inf") else max(0.0, best)
        cache[mask] = value
        return value

    return lower_bound


def _remaining_endpoint_path_lower_bound_fn(data: LunarIceData):
    if (
        float(data.objective.weight_operating_cost) < 0.0
        or float(data.objective.weight_risk) < 0.0
        or float(data.objective.weight_completion) < 0.0
    ):
        return lambda _mask: 0.0
    refs = objective_references(data)
    min_inbound = _min_inbound_path_metric_by_task(data)
    start_extra_by_bit: dict[int, float] = {}
    return_by_bit: dict[int, float] = {}
    demand_by_bit: dict[int, float] = {}
    for index, task_id in enumerate(data.task_ids):
        bit = 1 << index
        task = data.tasks[task_id]
        demand_by_bit[bit] = max(0.0, float(task.demand))
        inbound_distance, inbound_energy, inbound_risk = min_inbound.get(str(task_id), (0.0, 0.0, 0.0))
        inbound_value = _path_metric_objective_component(
            data,
            refs,
            distance_km=inbound_distance,
            energy_proxy=inbound_energy,
            risk_integral=inbound_risk,
        )
        best_outbound = float("inf")
        for option in data.arcs.get(("depot", str(task_id)), {}).values():
            best_outbound = min(
                best_outbound,
                _path_metric_objective_component(
                    data,
                    refs,
                    distance_km=float(option.distance_km),
                    energy_proxy=float(option.energy_proxy),
                    risk_integral=float(option.risk_integral),
                ),
            )
        start_extra_by_bit[bit] = 0.0 if not isfinite(best_outbound) else max(0.0, best_outbound - inbound_value)

        best_return = float("inf")
        for option in data.arcs.get((str(task_id), "depot"), {}).values():
            best_return = min(
                best_return,
                _path_metric_objective_component(
                    data,
                    refs,
                    distance_km=float(option.distance_km),
                    energy_proxy=float(option.energy_proxy),
                    risk_integral=float(option.risk_integral),
                ),
            )
        return_by_bit[bit] = 0.0 if not isfinite(best_return) else max(0.0, best_return)
    cache = {0: 0.0}

    def lower_bound(mask: int) -> float:
        mask = int(mask)
        cached = cache.get(mask)
        if cached is not None:
            return cached
        bits = mask
        task_count = 0
        total_demand = 0.0
        start_extras: list[float] = []
        returns: list[float] = []
        while bits:
            bit = bits & -bits
            bits -= bit
            task_count += 1
            total_demand += demand_by_bit.get(bit, 0.0)
            start_extras.append(start_extra_by_bit.get(bit, 0.0))
            returns.append(return_by_bit.get(bit, 0.0))
        if task_count <= 0:
            cache[mask] = 0.0
            return 0.0
        max_tasks = max(1, int(data.max_tasks_per_trip))
        capacity = max(1.0e-9, float(data.capacity))
        min_sorties = max(1, ceil(task_count / max_tasks), ceil(total_demand / capacity))
        min_sorties = min(int(min_sorties), task_count)
        value = sum(sorted(start_extras)[:min_sorties]) + sum(sorted(returns)[:min_sorties])
        cache[mask] = max(0.0, round(float(value), 9))
        return cache[mask]

    return lower_bound


def _remaining_future_sortie_tail_lower_bound_fn(data: LunarIceData):
    inbound_task_visit = _remaining_task_visit_lower_bound_fn(data)
    endpoint_path = _remaining_endpoint_path_lower_bound_fn(data)
    outgoing_task_visit = _remaining_outgoing_task_visit_lower_bound_fn(data)
    start_path = _remaining_start_path_lower_bound_fn(data)
    cache: dict[tuple[int, float], float] = {(0, 0.0): 0.0}

    def lower_bound(mask: int, earliest_service_floor: float = 0.0) -> float:
        mask = int(mask)
        bucket = _lower_bound_time_bucket(earliest_service_floor)
        cached = cache.get((mask, bucket))
        if cached is not None:
            return cached
        inbound_bound = float(inbound_task_visit(mask, bucket)) + float(endpoint_path(mask))
        outgoing_bound = float(outgoing_task_visit(mask, bucket)) + float(start_path(mask))
        value = max(0.0, inbound_bound, outgoing_bound)
        cache[(mask, bucket)] = round(value, 9)
        return cache[(mask, bucket)]

    return lower_bound


def _remaining_outgoing_task_visit_lower_bound_fn(data: LunarIceData):
    if (
        float(data.objective.weight_operating_cost) < 0.0
        or float(data.objective.weight_risk) < 0.0
        or float(data.objective.weight_completion) < 0.0
        or any(float(data.tasks[task_id].science_weight) < 0.0 for task_id in data.task_ids)
    ):
        return lambda _mask, _earliest_service_floor=0.0: 0.0
    refs = objective_references(data)
    static_by_bit: dict[int, float] = {}
    completion_coeff_by_bit: dict[int, float] = {}
    ready_by_bit: dict[int, float] = {}
    service_by_bit: dict[int, float] = {}
    task_set = set(data.task_ids)
    for index, task_id in enumerate(data.task_ids):
        bit = 1 << index
        task = data.tasks[task_id]
        best_outgoing = float("inf")
        for (source, target), options in data.arcs.items():
            if str(source) != str(task_id) or str(target) == str(task_id):
                continue
            if str(target) != "depot" and str(target) not in task_set:
                continue
            for option in options.values():
                best_outgoing = min(
                    best_outgoing,
                    _path_metric_objective_component(
                        data,
                        refs,
                        distance_km=float(option.distance_km),
                        energy_proxy=float(option.energy_proxy),
                        risk_integral=float(option.risk_integral),
                    ),
                )
        service_operating = operating_cost_value(
            service_cost=float(task.service_cost),
            distance_km=0.0,
            energy_proxy=float(task.service_energy),
        )
        static_by_bit[bit] = max(
            0.0,
            float(data.objective.weight_operating_cost) * float(service_operating) / float(refs.reference_cost)
            + float(data.objective.weight_risk) * float(service_risk_value(task)) / float(refs.reference_risk)
            + (0.0 if not isfinite(best_outgoing) else max(0.0, best_outgoing)),
        )
        completion_coeff_by_bit[bit] = (
            float(data.objective.weight_completion)
            * float(task.science_weight)
            / float(refs.reference_completion)
        )
        ready_by_bit[bit] = max(0.0, float(task.ready_time))
        service_by_bit[bit] = max(0.0, float(task.service_time))
    cache: dict[tuple[int, float], float] = {(0, 0.0): 0.0}

    def lower_bound(mask: int, earliest_service_floor: float = 0.0) -> float:
        mask = int(mask)
        bucket = _lower_bound_time_bucket(earliest_service_floor)
        cached = cache.get((mask, bucket))
        if cached is not None:
            return cached
        bits = mask
        value = 0.0
        while bits:
            bit = bits & -bits
            bits -= bit
            completion_time_lb = max(ready_by_bit.get(bit, 0.0), bucket) + service_by_bit.get(bit, 0.0)
            value += (
                static_by_bit.get(bit, 0.0)
                + completion_coeff_by_bit.get(bit, 0.0) * completion_time_lb
            )
        cache[(mask, bucket)] = round(value, 9)
        return cache[(mask, bucket)]

    return lower_bound


def _remaining_start_path_lower_bound_fn(data: LunarIceData):
    if (
        float(data.objective.weight_operating_cost) < 0.0
        or float(data.objective.weight_risk) < 0.0
        or float(data.objective.weight_completion) < 0.0
    ):
        return lambda _mask: 0.0
    refs = objective_references(data)
    start_by_bit: dict[int, float] = {}
    demand_by_bit: dict[int, float] = {}
    for index, task_id in enumerate(data.task_ids):
        bit = 1 << index
        task = data.tasks[task_id]
        demand_by_bit[bit] = max(0.0, float(task.demand))
        best_start = float("inf")
        for option in data.arcs.get(("depot", str(task_id)), {}).values():
            best_start = min(
                best_start,
                _path_metric_objective_component(
                    data,
                    refs,
                    distance_km=float(option.distance_km),
                    energy_proxy=float(option.energy_proxy),
                    risk_integral=float(option.risk_integral),
                ),
            )
        start_by_bit[bit] = 0.0 if not isfinite(best_start) else max(0.0, best_start)
    cache = {0: 0.0}

    def lower_bound(mask: int) -> float:
        mask = int(mask)
        cached = cache.get(mask)
        if cached is not None:
            return cached
        bits = mask
        task_count = 0
        total_demand = 0.0
        starts: list[float] = []
        while bits:
            bit = bits & -bits
            bits -= bit
            task_count += 1
            total_demand += demand_by_bit.get(bit, 0.0)
            starts.append(start_by_bit.get(bit, 0.0))
        if task_count <= 0:
            cache[mask] = 0.0
            return 0.0
        max_tasks = max(1, int(data.max_tasks_per_trip))
        capacity = max(1.0e-9, float(data.capacity))
        min_sorties = max(1, ceil(task_count / max_tasks), ceil(total_demand / capacity))
        min_sorties = min(int(min_sorties), task_count)
        value = sum(sorted(starts)[:min_sorties])
        cache[mask] = max(0.0, round(float(value), 9))
        return cache[mask]

    return lower_bound


def _path_metric_objective_component(
    data: LunarIceData,
    refs,
    *,
    distance_km: float,
    energy_proxy: float,
    risk_integral: float,
) -> float:
    operating = operating_cost_value(
        service_cost=0.0,
        distance_km=max(0.0, float(distance_km)),
        energy_proxy=max(0.0, float(energy_proxy)),
    )
    return (
        float(data.objective.weight_operating_cost) * float(operating) / float(refs.reference_cost)
        + float(data.objective.weight_risk) * max(0.0, float(risk_integral)) / float(refs.reference_risk)
    )


def _min_inbound_path_metric_by_task(data: LunarIceData) -> dict[str, tuple[float, float, float]]:
    values: dict[str, tuple[float, float, float]] = {}
    task_set = set(data.task_ids)
    for target in data.task_ids:
        best_distance = float("inf")
        best_energy = float("inf")
        best_risk = float("inf")
        for (source, arc_target), options in data.arcs.items():
            if str(arc_target) != str(target) or str(source) == str(target):
                continue
            if str(source) != "depot" and str(source) not in task_set:
                continue
            for option in options.values():
                best_distance = min(best_distance, float(option.distance_km))
                best_energy = min(best_energy, float(option.energy_proxy))
                best_risk = min(best_risk, float(option.risk_integral))
        values[str(target)] = (
            0.0 if not isfinite(best_distance) else max(0.0, best_distance),
            0.0 if not isfinite(best_energy) else max(0.0, best_energy),
            0.0 if not isfinite(best_risk) else max(0.0, best_risk),
        )
    return values


def _deadline_from_limit(wall_time_limit_sec: float | None) -> float | None:
    if wall_time_limit_sec is None:
        return None
    limit = float(wall_time_limit_sec)
    if limit <= 0.0:
        return perf_counter()
    return perf_counter() + limit


def _elapsed_sec(start: float) -> float:
    return round(perf_counter() - float(start), 6)


def _remaining_wall_time(deadline: float | None) -> float:
    if deadline is None:
        return float("inf")
    return max(0.0, float(deadline) - perf_counter())


def _direct_sortie_cache_limit(data: LunarIceData) -> int | None:
    if len(data.task_ids) <= 20:
        return None
    return 256


def _raise_if_deadline_exceeded(deadline: float | None) -> None:
    if deadline is not None and perf_counter() > float(deadline):
        raise DirectBaselineTimeLimitExceeded()


def _raise_if_direct_deadline_exceeded(
    deadline: float | None,
    *,
    stage: str,
    labels_by_mask: dict[int, list[_JourneyLabel]],
    generated_sortie_count: int,
    route_template_count: int,
    journey_label_bound_pruned_count: int = 0,
    direct_bound_pruning_root_bound: float | None = None,
    direct_bound_pruning_active: bool = False,
) -> None:
    if deadline is not None and perf_counter() > float(deadline):
        raise _direct_timeout(
            stage=stage,
            labels_by_mask=labels_by_mask,
            generated_sortie_count=generated_sortie_count,
            route_template_count=route_template_count,
            journey_label_bound_pruned_count=journey_label_bound_pruned_count,
            direct_bound_pruning_root_bound=direct_bound_pruning_root_bound,
            direct_bound_pruning_active=direct_bound_pruning_active,
        )


def _raise_if_sortie_generation_deadline_exceeded(
    deadline: float | None,
    *,
    generated_count: int,
    route_count: int,
    journey_label_bound_pruned_count: int = 0,
) -> None:
    if deadline is not None and perf_counter() > float(deadline):
        raise DirectBaselineTimeLimitExceeded(
            stage="unknown",
            generated_sortie_count=int(generated_count),
            route_template_count=int(route_count),
            journey_label_bound_pruned_count=int(journey_label_bound_pruned_count),
        )


def _direct_timeout(
    *,
    stage: str,
    labels_by_mask: dict[int, list[_JourneyLabel]],
    generated_sortie_count: int,
    route_template_count: int,
    journey_label_bound_pruned_count: int = 0,
    direct_bound_pruning_root_bound: float | None = None,
    direct_bound_pruning_active: bool = False,
) -> DirectBaselineTimeLimitExceeded:
    partial_masks = max(0, len(labels_by_mask) - (1 if 0 in labels_by_mask else 0))
    pareto_count = sum(len(labels) for mask, labels in labels_by_mask.items() if mask)
    return DirectBaselineTimeLimitExceeded(
        stage=stage,
        generated_journey_count=partial_masks,
        generated_sortie_count=generated_sortie_count,
        route_template_count=route_template_count,
        pareto_label_count=pareto_count,
        set_partition_state_count=0,
        journey_label_bound_pruned_count=journey_label_bound_pruned_count,
        direct_bound_pruning_root_bound=direct_bound_pruning_root_bound,
        direct_bound_pruning_active=direct_bound_pruning_active,
    )
