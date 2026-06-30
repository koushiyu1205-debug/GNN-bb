"""Small-scale journey-column dynamic-programming baseline.

This is not the final BPC driver. It solves a restricted canonical-path journey
column universe so the lunar-ice schema has a real exact baseline path before
true-dual pricing, cuts, and branching are ported. The result must not be used
as an official BPC certificate.
"""

from __future__ import annotations

from dataclasses import dataclass
import heapq
from itertools import permutations, product
from time import perf_counter
from typing import Iterable

from lunar_ice_bpc.domain.scenario import PATH_TYPES
from lunar_ice_bpc.exact.core.columns import SortieLeg, TimedSortie, build_timed_sortie
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn, build_journey_column


CANONICAL_PATH_POLICIES: tuple[tuple[str, ...], ...] = (
    ("low_time",),
    ("low_energy",),
    ("low_risk",),
)


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


@dataclass(frozen=True)
class CanonicalJourneyUniverse:
    columns: tuple[JourneyColumn, ...]
    best_label_by_mask: dict[int, "_JourneyLabel"]
    generated_sortie_count: int
    route_template_count: int
    pareto_label_count: int


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
        return round(self.base_cost + data.objective.beta_journey_end_time * self.end_time, 6)


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
    discovery_completion_term: float
    base_cost: float


@dataclass(frozen=True)
class _SortieCandidate:
    task_mask: int
    sortie: TimedSortie
    base_cost: float


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
    ) -> None:
        super().__init__(message)
        self.stage = str(stage)
        self.generated_journey_count = int(generated_journey_count)
        self.generated_sortie_count = int(generated_sortie_count)
        self.route_template_count = int(route_template_count)
        self.pareto_label_count = int(pareto_label_count)
        self.set_partition_state_count = int(set_partition_state_count)


def solve_small_journey_baseline(data: LunarIceData, *, max_exact_tasks: int = 10) -> JourneyBaselineResult:
    """Solve a small instance over the restricted canonical-path universe."""

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
    )


def solve_direct_journey_baseline(
    data: LunarIceData,
    *,
    max_exact_tasks: int = 5,
    wall_time_limit_sec: float | None = None,
) -> JourneyBaselineResult:
    """Solve a small instance over all fixed logical-graph path options."""

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
        )
    deadline = _deadline_from_limit(wall_time_limit_sec)
    try:
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=int(max_exact_tasks), deadline=deadline)
    except DirectBaselineTimeLimitExceeded as exc:
        return JourneyBaselineResult(
            status="DIRECT_DP_BASELINE_TIME_LIMIT",
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
        )
    try:
        best_labels, state_count = _select_vehicle_partition(
            data,
            universe.best_label_by_mask,
            deadline=deadline,
        )
    except DirectBaselineTimeLimitExceeded as exc:
        return JourneyBaselineResult(
            status="DIRECT_DP_BASELINE_TIME_LIMIT",
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
        )
    if best_labels is None:
        return JourneyBaselineResult(
            status="NO_COLUMN_COVER_IN_DIRECT_DP_UNIVERSE",
            exact_status="NOT_SOLVED",
            objective=None,
            journeys=tuple(),
            generated_journey_count=len(universe.best_label_by_mask),
            generated_sortie_count=universe.generated_sortie_count,
            route_template_count=universe.route_template_count,
            pareto_label_count=universe.pareto_label_count,
            set_partition_state_count=state_count,
            note="No cover was found in the exhaustive direct-path journey universe.",
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
    )


def enumerate_canonical_journey_columns(data: LunarIceData, *, max_exact_tasks: int = 10) -> CanonicalJourneyUniverse:
    """Return the best restricted canonical journey column for each task set."""

    if len(data.task_ids) > int(max_exact_tasks):
        raise ValueError(f"task_count={len(data.task_ids)} exceeds max_exact_tasks={max_exact_tasks}")
    task_to_bit = {task_id: 1 << index for index, task_id in enumerate(data.task_ids)}
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
) -> CanonicalJourneyUniverse:
    """Return the best exhaustive direct-path journey column for each task set."""

    if len(data.task_ids) > int(max_exact_tasks):
        raise ValueError(f"task_count={len(data.task_ids)} exceeds max_exact_tasks={max_exact_tasks}")
    _raise_if_deadline_exceeded(deadline)
    task_to_bit = {task_id: 1 << index for index, task_id in enumerate(data.task_ids)}
    best_label_by_mask, sortie_count, route_template_count, pareto_label_count = _build_direct_journeys_label_dp(
        data,
        task_to_bit,
        deadline=deadline,
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
    )


def enumerate_direct_journey_columns_by_template(
    data: LunarIceData,
    *,
    max_exact_tasks: int = 5,
) -> CanonicalJourneyUniverse:
    """Compatibility path using explicit permutation x path-template enumeration."""

    if len(data.task_ids) > int(max_exact_tasks):
        raise ValueError(f"task_count={len(data.task_ids)} exceeds max_exact_tasks={max_exact_tasks}")
    task_to_bit = {task_id: 1 << index for index, task_id in enumerate(data.task_ids)}
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
) -> tuple[dict[int, _JourneyLabel], int, int, int]:
    full_mask = (1 << len(data.task_ids)) - 1
    path_type_cache = _nondominated_path_type_cache(data)
    labels_by_mask: dict[int, list[_JourneyLabel]] = {
        0: [_JourneyLabel(task_mask=0, sorties=tuple(), end_time=0.0, base_cost=0.0)]
    }
    sortie_cache: dict[float, tuple[tuple[_SortieCandidate, ...], int, int]] = {}
    generated_sortie_count = 0
    route_template_count = 0

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
            cache_key = round(float(label.end_time), 6)
            cached = sortie_cache.get(cache_key)
            if cached is None:
                try:
                    candidates, generated_count, route_count = _direct_sortie_candidates_from_start(
                        data,
                        task_to_bit,
                        remaining_mask=full_mask,
                        start_time=float(label.end_time),
                        deadline=deadline,
                        path_type_cache=path_type_cache,
                    )
                except DirectBaselineTimeLimitExceeded as exc:
                    raise _direct_timeout(
                        stage=f"sortie_candidate_generation:{exc.stage}",
                        labels_by_mask=labels_by_mask,
                        generated_sortie_count=generated_sortie_count,
                        route_template_count=route_template_count,
                    ) from exc
                cached = (tuple(candidates), generated_count, route_count)
                sortie_cache[cache_key] = cached
                generated_sortie_count += generated_count
                route_template_count += route_count
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
    return best_by_mask, generated_sortie_count, route_template_count, pareto_count


def _direct_sortie_candidates_from_start(
    data: LunarIceData,
    task_to_bit: dict[str, int],
    *,
    remaining_mask: int,
    start_time: float,
    deadline: float | None = None,
    path_type_cache: dict[tuple[str, str], tuple[str, ...]] | None = None,
) -> tuple[list[_SortieCandidate], int, int]:
    bit_to_task = {bit: task_id for task_id, bit in task_to_bit.items()}
    path_type_cache = path_type_cache or _nondominated_path_type_cache(data)
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
        discovery_completion_term=0.0,
        base_cost=0.0,
    )
    current_level = [initial]
    candidates_by_mask: dict[int, list[_SortieCandidate]] = {}
    generated_count = 0
    route_count = 0

    for _depth in range(1, max_len + 1):
        _raise_if_deadline_exceeded(deadline)
        next_by_key: dict[tuple[int, str], list[_PartialSortieLabel]] = {}
        for label in current_level:
            available = int(remaining_mask) & ~int(label.task_mask)
            while available:
                bit = available & -available
                available -= bit
                task_id = bit_to_task[bit]
                for path_type in path_type_cache[(str(label.last_task), str(task_id))]:
                    generated_count += 1
                    extended = _extend_partial_sortie_label(data, label, task_id, bit, path_type)
                    if extended is None:
                        continue
                    key = (extended.task_mask, extended.last_task)
                    _add_partial_sortie_label(next_by_key.setdefault(key, []), extended)
        current_level = [label for labels in next_by_key.values() for label in labels]
        for label in current_level:
            for return_path_type in path_type_cache[(str(label.last_task), "depot")]:
                generated_count += 1
                candidate = _close_partial_sortie_label(data, label, return_path_type)
                if candidate is None:
                    continue
                route_count += 1
                _add_sortie_candidate(candidates_by_mask.setdefault(candidate.task_mask, []), candidate)

    return [candidate for values in candidates_by_mask.values() for candidate in values], generated_count, route_count


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
    completion = float(label.discovery_completion_term) + float(task.science_weight) * elapsed
    base_cost = (
        float(data.objective.alpha_discovery_completion) * completion
        + float(data.objective.gamma_lunar_ice_risk) * risk
        + float(data.objective.delta_energy) * energy
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
        distance_km=round(float(label.distance_km) + float(option.distance_km), 6),
        energy_proxy=round(energy, 6),
        risk_integral=round(risk, 6),
        shadow_exposure_min=round(shadow, 6),
        demand=round(demand, 6),
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
                and float(other.energy_proxy) <= float(option.energy_proxy) + 1.0e-9
                and float(other.risk_integral) <= float(option.risk_integral) + 1.0e-9
                and float(other.shadow_exposure_min) <= float(option.shadow_exposure_min) + 1.0e-9
            )
            strictly_better = (
                float(other.travel_time_min) < float(option.travel_time_min) - 1.0e-9
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
        shadow_exposure_min=round(shadow, 6),
        demand=round(float(label.demand), 6),
        discovery_completion_term=round(float(label.discovery_completion_term), 6),
        feasible=True,
    )
    base_cost = (
        float(data.objective.alpha_discovery_completion) * float(sortie.discovery_completion_term)
        + float(data.objective.gamma_lunar_ice_risk) * float(sortie.risk_integral)
        + float(data.objective.delta_energy) * float(sortie.energy_proxy)
    )
    return _SortieCandidate(task_mask=int(label.task_mask), sortie=sortie, base_cost=round(base_cost, 6))


def _add_partial_sortie_label(labels: list[_PartialSortieLabel], candidate: _PartialSortieLabel) -> None:
    kept: list[_PartialSortieLabel] = []
    for old in labels:
        if (
            float(old.elapsed) <= float(candidate.elapsed) + 1.0e-9
            and float(old.energy_proxy) <= float(candidate.energy_proxy) + 1.0e-9
            and float(old.risk_integral) <= float(candidate.risk_integral) + 1.0e-9
            and float(old.shadow_exposure_min) <= float(candidate.shadow_exposure_min) + 1.0e-9
            and float(old.base_cost) <= float(candidate.base_cost) + 1.0e-9
        ):
            return
        if (
            float(candidate.elapsed) <= float(old.elapsed) + 1.0e-9
            and float(candidate.energy_proxy) <= float(old.energy_proxy) + 1.0e-9
            and float(candidate.risk_integral) <= float(old.risk_integral) + 1.0e-9
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
    full_mask = (1 << len(data.task_ids)) - 1
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
    add_base = (
        data.objective.alpha_discovery_completion * sortie.discovery_completion_term
        + data.objective.gamma_lunar_ice_risk * sortie.risk_integral
        + data.objective.delta_energy * sortie.energy_proxy
    )
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
    full_mask = (1 << len(data.task_ids)) - 1
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
    for masks in masks_by_required_bit.values():
        masks.sort(key=lambda mask: (-int(mask).bit_count(), cost_by_mask[mask], mask))

    max_cover_size = max(int(mask).bit_count() for mask in best_label_by_mask)
    best_value = float("inf")
    best_masks: tuple[int, ...] | None = None
    state_count = 0
    use_large_partition_bounds = len(data.task_ids) > 20
    remaining_lb = (
        _remaining_service_lower_bound_fn(data)
        if use_large_partition_bounds
        else (lambda _mask: 0.0)
    )
    if use_large_partition_bounds:
        greedy_masks = _greedy_partition_cover(
            full_mask,
            int(data.fleet_size),
            cost_by_mask=cost_by_mask,
            masks_by_required_bit=masks_by_required_bit,
        )
        if greedy_masks is not None:
            best_masks = greedy_masks
            best_value = sum(float(cost_by_mask[mask]) for mask in greedy_masks)

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
        if accumulated_cost + remaining_lb(remaining_mask) >= best_value - 1.0e-9:
            return
        if int(remaining_mask).bit_count() > int(vehicle_slots) * max_cover_size:
            return
        if vehicle_slots == 1:
            label_cost = cost_by_mask.get(remaining_mask)
            if label_cost is not None and accumulated_cost + label_cost < best_value - 1.0e-9:
                best_value = accumulated_cost + label_cost
                best_masks = tuple((*chosen_masks, remaining_mask))
            return

        required_bit = remaining_mask & -remaining_mask
        for mask in masks_by_required_bit.get(required_bit, []):
            if mask & remaining_mask != mask:
                continue
            next_cost = accumulated_cost + cost_by_mask[mask]
            if next_cost >= best_value - 1.0e-9:
                continue
            search(remaining_mask ^ mask, vehicle_slots - 1, next_cost, [*chosen_masks, mask])

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
    remaining_mask = int(full_mask)
    slots = int(vehicle_slots)
    chosen: list[int] = []
    while remaining_mask:
        if slots <= 0:
            return None
        required_bit = remaining_mask & -remaining_mask
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


def _remaining_service_lower_bound_fn(data: LunarIceData):
    if (
        float(data.objective.alpha_discovery_completion) < 0.0
        or float(data.objective.gamma_lunar_ice_risk) < 0.0
        or float(data.objective.delta_energy) < 0.0
    ):
        return lambda _mask: 0.0
    by_bit: dict[int, float] = {}
    for index, task_id in enumerate(data.task_ids):
        task = data.tasks[task_id]
        service_completion = max(0.0, float(task.ready_time)) + float(task.service_time)
        value = (
            float(data.objective.alpha_discovery_completion)
            * float(task.science_weight)
            * service_completion
            + float(data.objective.gamma_lunar_ice_risk)
            * float(task.local_thermal_risk)
            * float(task.service_time)
            * 0.01
            + float(data.objective.delta_energy) * float(task.service_energy)
        )
        by_bit[1 << index] = max(0.0, float(value))
    cache = {0: 0.0}

    def lower_bound(mask: int) -> float:
        mask = int(mask)
        cached = cache.get(mask)
        if cached is not None:
            return cached
        bits = mask
        value = 0.0
        while bits:
            bit = bits & -bits
            bits -= bit
            value += by_bit.get(bit, 0.0)
        cache[mask] = value
        return value

    return lower_bound


def _deadline_from_limit(wall_time_limit_sec: float | None) -> float | None:
    if wall_time_limit_sec is None:
        return None
    limit = float(wall_time_limit_sec)
    if limit <= 0.0:
        return perf_counter()
    return perf_counter() + limit


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
) -> None:
    if deadline is not None and perf_counter() > float(deadline):
        raise _direct_timeout(
            stage=stage,
            labels_by_mask=labels_by_mask,
            generated_sortie_count=generated_sortie_count,
            route_template_count=route_template_count,
        )


def _direct_timeout(
    *,
    stage: str,
    labels_by_mask: dict[int, list[_JourneyLabel]],
    generated_sortie_count: int,
    route_template_count: int,
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
    )
