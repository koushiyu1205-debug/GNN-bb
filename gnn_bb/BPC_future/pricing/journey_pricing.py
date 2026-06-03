"""Exact-safe journey pricing for the BPC_future journey master."""

from __future__ import annotations

from dataclasses import dataclass
import bisect
import heapq
import itertools
import math
import time
from typing import Any

from BPC_future.core.branching import BranchConstraint, partial_sequence_allowed
from BPC_future.core.columns import TimedTrip, evaluate_timed_trip, rounded
from BPC_future.core.cuts import FutureCut
from BPC_future.core.data import ArcOption, FutureData
from BPC_future.core.journey import JourneyColumn, make_journey
from BPC_future.master.journey_rmp import JourneyDuals
from BPC_future.master.rmp import FutureDuals, manual_reduced_cost
from BPC_future.pricing.trip_pricing import (
    _PartialNoWaitingPathProfile,
    PricingConfig,
    _PricingTimeout,
    _OptimizedArcProfile,
    _complete_no_waiting_partial,
    _extend_no_waiting_partial,
    _max_tasks_per_trip,
    _optimized_arc_profiles_for_sequence,
    _sequence_reduced_cost_lower_bound,
    _sequence_resource_precheck,
    _task_order,
    price_timed_trips,
)


@dataclass(frozen=True)
class JourneyPricingConfig:
    time_bucket_size: float = 10.0
    max_tasks_per_trip: int = 6
    max_sequences: int = 0
    max_timed_evaluations: int = 0
    time_limit: float = 0.0
    start_time_step: float = 10.0
    path_dominance_enabled: bool = True
    start_optimization_enabled: bool = True
    max_path_combinations_per_sequence: int = 0
    max_candidate_trips: int = 0
    max_dp_states: int = 200000
    allow_partial_negative: bool = False
    profile_pricing_enabled: bool = True
    direct_journey_label_pricing_enabled: bool = False
    direct_journey_label_early_return_negative: bool = True
    direct_journey_label_next_sortie_cache_enabled: bool = True
    direct_journey_label_task_set_bound_pruning_enabled: bool = True
    profile_generation_time_fraction: float = 0.75
    profile_labeling_enabled: bool = False
    profile_labeling_best_first_enabled: bool = True
    profile_labeling_resume_enabled: bool = False
    profile_labeling_physical_catalog_resume_enabled: bool = False
    profile_labeling_task_set_superset_pruning_enabled: bool = False
    profile_cross_dominance_enabled: bool = True
    max_returned_journeys: int = 1
    duplicate_retry_factor: int = 4
    early_return_negative: bool = False
    early_return_negative_min_count: int = 1
    early_return_unique_masks_enabled: bool = False
    streaming_pricing_enabled: bool = False
    streaming_profile_batch_size: int = 5000
    streaming_min_negative_batch: int = 1
    streaming_min_returned_journeys: int = 1
    streaming_partial_return_after_time: float = 0.0
    streaming_partial_return_min_journeys: int = 0
    streaming_profile_cap_per_mask: int = 0
    min_add_reduced_cost: float = 0.0
    dp_bound_pruning_enabled: bool = True
    dp_disjoint_bound_pruning_enabled: bool = True
    dp_disjoint_bound_max_tasks: int = 12
    dp_cross_count_dominance_enabled: bool = True
    dp_same_completion_pruning_enabled: bool = False
    profile_catalog_enabled: bool = False
    profile_catalog_resume_enabled: bool = False
    profile_catalog_max_tasks: int = 10
    profile_catalog_max_profiles: int = 200000
    generalized_partial_dominance_enabled: bool = False
    task_set_bound_pruning_enabled: bool = False
    task_set_resource_pruning_enabled: bool = False
    partial_profile_bound_pruning_enabled: bool = False
    profile_online_dominance_enabled: bool = False
    journey_selection_mode: str = "reduced_cost"
    duplicate_scan_limit: int = 10000
    eps: float = 1.0e-6


@dataclass
class JourneyPricingResult:
    journeys: list[JourneyColumn]
    exhausted: bool
    best_reduced_cost: float | None
    generated_sequences: int
    evaluated_timed_trips: int
    candidate_trips: int
    selected_trips: int
    status: str
    reason: str = ""
    profile_dominance_pruned: int = 0
    existing_journeys_filtered: int = 0
    profile_cut_penalty_pruned: int = 0
    weak_negative_journeys_filtered: int = 0
    dp_bound_pruned_labels: int = 0
    dp_cross_count_pruned_labels: int = 0
    profile_catalog_hit: bool = False
    profile_catalog_size: int = 0
    profile_generation_time: float = 0.0
    profile_filter_time: float = 0.0
    profile_dp_time: float = 0.0
    duplicate_candidate_scan_count: int = 0
    duplicate_candidates_filtered: int = 0
    duplicate_scan_limited: bool = False
    direct_next_sortie_cache_hits: int = 0
    direct_next_sortie_cache_misses: int = 0
    dp_disjoint_bound_pruned_labels: int = 0
    dominated_task_set_journeys_filtered: int = 0
    task_set_resource_pruned_sequences: int = 0
    partial_profile_bound_pruned_labels: int = 0
    label_physical_catalog: bool = False
    label_physical_catalog_exhausted: bool = False
    label_resume_heap: int = 0
    label_resume_profiles: int = 0
    label_resume_exhausted: bool = False
    profile_mask_cap_pruned: int = 0
    branch_mask_pruned_sequences: int = 0
    dp_processed_labels: int = 0
    dp_state_count: int = 0
    dp_profile_record_scans: int = 0
    dp_profile_time_filtered: int = 0
    dp_extension_attempts: int = 0
    dp_same_completion_pruned_labels: int = 0


@dataclass(frozen=True)
class _SortieProfile:
    sequence: tuple[int, ...]
    arc_options: tuple[ArcOption, ...]
    lower_start: float
    upper_start: float
    end_offset: float
    cost: float
    mask: int
    contribution: float


@dataclass
class _SortieProfileCatalogState:
    profiles: list[_SortieProfile]
    keys: set[tuple]
    generated: int = 0
    evaluated: int = 0
    next_size: int = 1
    next_permutation_index: int = 0
    exhausted: bool = False
    reason: str = ""


@dataclass
class _SortieLabelResumeState:
    labels_by_key: dict[tuple[int, int], list["_SortiePartialLabel"]]
    profiles_by_key: dict[tuple, _SortieProfile]
    heap: list[tuple[float, int, float, tuple[int, ...], int, "_SortiePartialLabel"]]
    profiles_by_mask: dict[int, list[_SortieProfile]] | None = None
    serial: int = 0
    generated: int = 0
    evaluated: int = 0
    best_profile_rc: float | None = None
    exhausted: bool = False
    reason: str = ""
    online_dominance_pruned: int = 0
    profile_mask_cap_pruned: int = 0


@dataclass(frozen=True)
class _JourneyLabel:
    end_time: float
    value: float
    selected: tuple[tuple[int, float], ...]


@dataclass(frozen=True)
class _SortiePartialLabel:
    sequence: tuple[int, ...]
    mask: int
    last: int
    partial: _PartialNoWaitingPathProfile


@dataclass(frozen=True)
class _DirectJourneyLabel:
    end_time: float
    value: float
    mask: int
    trips: tuple[TimedTrip, ...]


class _StreamingPricingStop(Exception):
    def __init__(self, result: JourneyPricingResult) -> None:
        super().__init__(result.reason)
        self.result = result


class _CompatibleProfileCache:
    def __init__(self, ordered_records: tuple[tuple[int, int, _SortieProfile], ...], *, task_count: int) -> None:
        self.ordered_records = ordered_records
        self.upper_start_records = tuple(
            sorted(
                ordered_records,
                key=lambda record: (
                    round(float(record[2].upper_start), 9),
                    record[0],
                    record[1],
                    record[2].sequence,
                ),
            )
        )
        self.upper_start_values = tuple(float(record[2].upper_start) for record in self.upper_start_records)
        self.enabled = int(task_count) <= 10
        self.requires_overlap_check = not self.enabled
        self.full_mask = (1 << int(task_count)) - 1 if self.enabled else 0
        self.by_profile_mask: dict[int, list[tuple[int, int, _SortieProfile]]] = {}
        self.by_used_mask: dict[int, tuple[tuple[int, int, _SortieProfile], ...]] = {}
        if self.enabled:
            for record in ordered_records:
                self.by_profile_mask.setdefault(int(record[2].mask), []).append(record)

    def records(
        self,
        used_mask: int,
        *,
        min_upper_start: float | None = None,
    ) -> tuple[tuple[int, int, _SortieProfile], ...]:
        time_threshold = None if min_upper_start is None else float(min_upper_start) - 1.0e-9
        if not self.enabled:
            if time_threshold is None:
                return self.ordered_records
            start = bisect.bisect_left(self.upper_start_values, float(time_threshold))
            return tuple(sorted(self.upper_start_records[start:], key=lambda record: record[0]))
        used_mask = int(used_mask)
        cached = self.by_used_mask.get(used_mask)
        if cached is not None:
            if time_threshold is None:
                return cached
            return tuple(record for record in cached if float(record[2].upper_start) + 1.0e-9 >= float(min_upper_start))
        available = self.full_mask ^ used_mask
        records: list[tuple[int, int, _SortieProfile]] = []
        submask = available
        while submask:
            records.extend(self.by_profile_mask.get(submask, ()))
            submask = (submask - 1) & available
        records.sort(key=lambda record: record[0])
        cached = tuple(records)
        self.by_used_mask[used_mask] = cached
        if time_threshold is not None:
            return tuple(record for record in cached if float(record[2].upper_start) + 1.0e-9 >= float(min_upper_start))
        return cached


class _TaskSetReducedCostLowerBoundCache:
    """Safe task-set lower bound before order/path expansion.

    The bound minimizes travel cost over the task set using the cheapest logical
    option on each arc and ignores time and energy feasibility.  It is therefore
    optimistic for every feasible sortie over the same task set.  If this lower
    bound is already above the profile threshold, all permutations and path
    combinations for that task set can be skipped without losing a negative
    reduced-cost column.
    """

    def __init__(self, data: FutureData, duals: FutureDuals, vehicle: int, task_to_bit: dict[int, int]) -> None:
        self.data = data
        self.duals = duals
        self.vehicle = int(vehicle)
        self.task_by_bit = {int(bit): int(task) for task, bit in task_to_bit.items()}
        self.arc_cache: dict[tuple[int, int], float] = {}
        self.travel_cache: dict[tuple[int, int], float] = {}
        self.value_cache: dict[int, float] = {}

    def value(self, mask: int) -> float:
        mask = int(mask)
        cached = self.value_cache.get(mask)
        if cached is not None:
            return cached
        travel = self._travel(mask, 0)
        if travel == float("inf"):
            self.value_cache[mask] = float("inf")
            return float("inf")
        service = 0.0
        dual_sum = 0.0
        remaining = mask
        while remaining:
            bit = remaining & -remaining
            task = self.task_by_bit[bit.bit_length() - 1]
            service += float(self.data.task_value(task, "c_srv"))
            dual_sum += float(self.duals.cover.get(int(task), 0.0))
            dual_sum += float(self.duals.task_vehicle.get((int(task), int(self.vehicle)), 0.0))
            remaining ^= bit
        value = float(travel) + float(service) - float(dual_sum) - float(self.duals.sortie_count.get(int(self.vehicle), 0.0))
        self.value_cache[mask] = value
        return value

    def _travel(self, mask: int, current: int) -> float:
        key = (int(mask), int(current))
        cached = self.travel_cache.get(key)
        if cached is not None:
            return cached
        if int(mask) == 0:
            value = self._arc_cost_lb(int(current), 0)
            self.travel_cache[key] = value
            return value
        best = float("inf")
        remaining = int(mask)
        while remaining:
            bit = remaining & -remaining
            task = self.task_by_bit[bit.bit_length() - 1]
            arc = self._arc_cost_lb(int(current), int(task))
            if arc != float("inf"):
                tail = self._travel(int(mask) ^ bit, int(task))
                if tail != float("inf"):
                    best = min(best, float(arc) + float(tail))
            remaining ^= bit
        self.travel_cache[key] = best
        return best

    def _arc_cost_lb(self, origin: int, destination: int) -> float:
        key = (int(origin), int(destination))
        cached = self.arc_cache.get(key)
        if cached is not None:
            return cached
        options = self.data.options(int(origin), int(destination))
        if not options:
            value = float("inf")
        else:
            value = min(float(option.cost) for option in options)
        self.arc_cache[key] = value
        return value


class _TaskSetResourceLowerBoundCache:
    """Optimistic resource feasibility test for a task set.

    The cache uses the cheapest energy and time arcs independently, so the
    resulting closed-tour energy/time values are optimistic lower bounds for
    any concrete sortie over the same task set.  If even this optimistic
    closed tour violates capacity, battery, or horizon, no ordered path-option
    expansion for that task set can be feasible.
    """

    def __init__(self, data: FutureData, task_to_bit: dict[int, int], *, enabled: bool) -> None:
        self.data = data
        self.enabled = bool(enabled)
        self.task_by_bit = {int(bit): int(task) for task, bit in task_to_bit.items()}
        self.load_by_bit = {
            int(bit): float(data.task_value(int(task), "d"))
            for task, bit in task_to_bit.items()
        }
        self.service_time_by_bit = {
            int(bit): float(data.task_value(int(task), "sigma"))
            for task, bit in task_to_bit.items()
        }
        self.service_energy_by_bit = {
            int(bit): float(data.task_value(int(task), "g"))
            for task, bit in task_to_bit.items()
        }
        self.arc_energy_cache: dict[tuple[int, int], float] = {}
        self.arc_time_cache: dict[tuple[int, int], float] = {}
        self.travel_energy_cache: dict[tuple[int, int], float] = {}
        self.travel_time_cache: dict[tuple[int, int], float] = {}
        self.feasible_cache: dict[int, bool] = {}

    def maybe_feasible(self, mask: int) -> bool:
        if not self.enabled:
            return True
        mask = int(mask)
        if mask == 0:
            return True
        cached = self.feasible_cache.get(mask)
        if cached is not None:
            return bool(cached)
        load = 0.0
        service_energy = 0.0
        remaining = mask
        while remaining:
            bit = remaining & -remaining
            bit_index = bit.bit_length() - 1
            load += float(self.load_by_bit.get(bit_index, 0.0))
            service_energy += float(self.service_energy_by_bit.get(bit_index, 0.0))
            remaining ^= bit
        if load > float(self.data.capacity) + 1.0e-9:
            self.feasible_cache[mask] = False
            return False
        energy_lb = self._travel_energy(mask, 0)
        time_lb = self._travel_time(mask, 0)
        if energy_lb == float("inf") or time_lb == float("inf"):
            self.feasible_cache[mask] = False
            return False
        total_energy_lb = float(energy_lb) + float(service_energy) + float(self.data.survival_energy_rate) * float(time_lb)
        if total_energy_lb > float(self.data.energy_limit) + 1.0e-9:
            self.feasible_cache[mask] = False
            return False
        recharge_lb = float(total_energy_lb) / max(1.0e-9, float(self.data.rho))
        feasible = float(time_lb) + float(recharge_lb) <= float(self.data.horizon) + 1.0e-9
        self.feasible_cache[mask] = bool(feasible)
        return bool(feasible)

    def _travel_energy(self, mask: int, current: int) -> float:
        key = (int(mask), int(current))
        cached = self.travel_energy_cache.get(key)
        if cached is not None:
            return cached
        if int(mask) == 0:
            value = self._arc_energy_lb(int(current), 0)
            self.travel_energy_cache[key] = value
            return value
        best = float("inf")
        remaining = int(mask)
        while remaining:
            bit = remaining & -remaining
            task = self.task_by_bit[bit.bit_length() - 1]
            arc = self._arc_energy_lb(int(current), int(task))
            if arc != float("inf"):
                tail = self._travel_energy(int(mask) ^ bit, int(task))
                if tail != float("inf"):
                    best = min(best, float(arc) + float(tail))
            remaining ^= bit
        self.travel_energy_cache[key] = best
        return best

    def _travel_time(self, mask: int, current: int) -> float:
        key = (int(mask), int(current))
        cached = self.travel_time_cache.get(key)
        if cached is not None:
            return cached
        if int(mask) == 0:
            value = self._arc_time_lb(int(current), 0)
            self.travel_time_cache[key] = value
            return value
        best = float("inf")
        remaining = int(mask)
        while remaining:
            bit = remaining & -remaining
            bit_index = bit.bit_length() - 1
            task = self.task_by_bit[bit_index]
            arc = self._arc_time_lb(int(current), int(task))
            if arc != float("inf"):
                tail = self._travel_time(int(mask) ^ bit, int(task))
                if tail != float("inf"):
                    best = min(best, float(arc) + float(self.service_time_by_bit.get(bit_index, 0.0)) + float(tail))
            remaining ^= bit
        self.travel_time_cache[key] = best
        return best

    def _arc_energy_lb(self, origin: int, destination: int) -> float:
        key = (int(origin), int(destination))
        cached = self.arc_energy_cache.get(key)
        if cached is not None:
            return cached
        options = self.data.options(int(origin), int(destination))
        value = float("inf") if not options else min(float(option.energy) for option in options)
        self.arc_energy_cache[key] = value
        return value

    def _arc_time_lb(self, origin: int, destination: int) -> float:
        key = (int(origin), int(destination))
        cached = self.arc_time_cache.get(key)
        if cached is not None:
            return cached
        options = self.data.options(int(origin), int(destination))
        value = float("inf") if not options else min(float(option.tau) for option in options)
        self.arc_time_cache[key] = value
        return value


def _task_set_resource_cache_key(data: FutureData, task_to_bit: dict[int, int]) -> tuple:
    return (
        "task_set_resource_lower_bound_v1",
        str(data.instance_path),
        tuple(sorted((int(task), int(bit)) for task, bit in task_to_bit.items())),
        round(float(data.capacity), 9),
        round(float(data.energy_limit), 9),
        round(float(data.horizon), 9),
        round(float(data.rho), 9),
        round(float(data.survival_energy_rate), 9),
    )


def _get_task_set_resource_lower_bound_cache(
    data: FutureData,
    task_to_bit: dict[int, int],
    *,
    enabled: bool,
    resource_cache: dict[tuple, Any] | None,
) -> _TaskSetResourceLowerBoundCache:
    if not bool(enabled):
        return _TaskSetResourceLowerBoundCache(data, task_to_bit, enabled=False)
    if resource_cache is None:
        return _TaskSetResourceLowerBoundCache(data, task_to_bit, enabled=True)
    key = _task_set_resource_cache_key(data, task_to_bit)
    cached = resource_cache.get(key)
    if isinstance(cached, _TaskSetResourceLowerBoundCache):
        return cached
    cache = _TaskSetResourceLowerBoundCache(data, task_to_bit, enabled=True)
    resource_cache[key] = cache
    return cache


class _PartialSortieProfileLowerBoundCache:
    """Optimistic continuation bound for a partial sortie label.

    The bound uses cheapest arc costs and ignores time/energy feasibility for
    future tasks.  It is therefore no larger than the best feasible completion
    contribution.  If it is already above the profile threshold, no descendant
    of the partial label can produce a useful sortie profile.
    """

    def __init__(self, data: FutureData, duals: FutureDuals, vehicle: int, task_to_bit: dict[int, int], *, enabled: bool) -> None:
        self.data = data
        self.duals = duals
        self.vehicle = int(vehicle)
        self.enabled = bool(enabled)
        self.task_by_bit = {int(bit): int(task) for task, bit in task_to_bit.items()}
        self.full_mask = 0
        for bit in self.task_by_bit:
            self.full_mask |= 1 << int(bit)
        self.arc_cache: dict[tuple[int, int], float] = {}
        self.tail_cache: dict[tuple[int, int, int], float] = {}

    def value(self, label: _SortiePartialLabel, remaining_slots: int) -> float:
        if not self.enabled:
            return -float("inf")
        current = self._partial_contribution(label)
        if current == float("inf"):
            return float("inf")
        available_mask = self.full_mask & ~int(label.mask)
        tail = self._tail(int(label.last), int(available_mask), max(0, int(remaining_slots)))
        if tail == float("inf"):
            return float("inf")
        return float(current) + float(tail)

    def _partial_contribution(self, label: _SortiePartialLabel) -> float:
        dual_sum = 0.0
        for task in set(label.sequence):
            task = int(task)
            dual_sum += float(self.duals.cover.get(task, 0.0))
            dual_sum += float(self.duals.task_vehicle.get((task, int(self.vehicle)), 0.0))
        return float(label.partial.travel_cost) + float(label.partial.service_cost) - float(dual_sum)

    def _tail(self, current: int, available_mask: int, remaining_slots: int) -> float:
        key = (int(current), int(available_mask), int(remaining_slots))
        cached = self.tail_cache.get(key)
        if cached is not None:
            return cached
        best = self._arc_cost_lb(int(current), 0)
        if int(remaining_slots) > 0:
            remaining = int(available_mask)
            while remaining:
                bit = remaining & -remaining
                bit_index = bit.bit_length() - 1
                task = self.task_by_bit[bit_index]
                arc = self._arc_cost_lb(int(current), int(task))
                if arc != float("inf"):
                    dual = float(self.duals.cover.get(int(task), 0.0))
                    dual += float(self.duals.task_vehicle.get((int(task), int(self.vehicle)), 0.0))
                    service = float(self.data.task_value(int(task), "c_srv"))
                    tail = self._tail(int(task), int(available_mask) ^ bit, int(remaining_slots) - 1)
                    if tail != float("inf"):
                        best = min(best, float(arc) + float(service) - float(dual) + float(tail))
                remaining ^= bit
        self.tail_cache[key] = best
        return best

    def _arc_cost_lb(self, origin: int, destination: int) -> float:
        key = (int(origin), int(destination))
        cached = self.arc_cache.get(key)
        if cached is not None:
            return cached
        options = self.data.options(int(origin), int(destination))
        value = float("inf") if not options else min(float(option.cost) for option in options)
        self.arc_cache[key] = value
        return value


class _OptimisticProfileBoundCache:
    """Safe lower bound on extra profile contribution for DP label pruning.

    It ignores time compatibility and mutual overlap among future profiles, so
    the value can only be more optimistic than a real continuation.  That makes
    it safe for proving that a label cannot lead to a negative journey.
    """

    def __init__(self, compatible_profile_cache: _CompatibleProfileCache) -> None:
        self.compatible_profile_cache = compatible_profile_cache
        self.cache: dict[tuple[int, int], float] = {}

    def value(self, used_mask: int, remaining_count: int) -> float:
        remaining_count = int(remaining_count)
        if remaining_count <= 0:
            return 0.0
        key = (int(used_mask), remaining_count)
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        values = [
            float(profile.contribution)
            for _position, _profile_index, profile in self.compatible_profile_cache.records(int(used_mask))
            if float(profile.contribution) < 0.0
        ]
        if not values:
            self.cache[key] = 0.0
            return 0.0
        values.sort()
        bound = float(sum(values[:remaining_count]))
        self.cache[key] = bound
        return bound


class _DisjointProfileBoundCache:
    """Safe lower bound using only task-disjoint future profile masks.

    The bound ignores timing and ordering, so it is still optimistic for the
    true continuation.  Unlike ``_OptimisticProfileBoundCache``, it respects
    task-mask disjointness among the remaining profiles, which makes the lower
    bound much tighter on degenerate pools with many profiles over the same
    tasks.
    """

    def __init__(self, ordered_records: tuple[tuple[int, int, _SortieProfile], ...], *, task_count: int, enabled: bool) -> None:
        self.enabled = bool(enabled) and int(task_count) <= 20
        self.task_count = int(task_count)
        self.full_mask = (1 << int(task_count)) - 1 if self.enabled else 0
        self.dp_by_count: list[list[float]] = []
        if not self.enabled:
            return
        size = self.full_mask + 1
        best_by_mask = [float("inf")] * size
        for _position, _profile_index, profile in ordered_records:
            mask = int(profile.mask)
            if mask <= 0 or mask > self.full_mask:
                continue
            contribution = float(profile.contribution)
            if contribution < best_by_mask[mask]:
                best_by_mask[mask] = contribution
        active_masks = [mask for mask, value in enumerate(best_by_mask) if mask > 0 and value < 0.0]
        previous = [0.0] * size
        self.dp_by_count = [previous]
        max_count = int(task_count)
        for _count in range(1, max_count + 1):
            current = previous[:]
            for mask in range(size):
                best = current[mask]
                for profile_mask in active_masks:
                    if profile_mask & mask != profile_mask:
                        continue
                    candidate = best_by_mask[profile_mask] + previous[mask ^ profile_mask]
                    if candidate < best:
                        best = candidate
                current[mask] = best
            self.dp_by_count.append(current)
            previous = current

    def value(self, used_mask: int, remaining_count: int) -> float | None:
        if not self.enabled or not self.dp_by_count:
            return None
        count = max(0, min(int(remaining_count), len(self.dp_by_count) - 1))
        available = self.full_mask ^ int(used_mask)
        if available < 0 or available > self.full_mask:
            return None
        return float(self.dp_by_count[count][available])


class _TaskSetContinuationLowerBoundCache:
    """Optimistic lower bound for future direct-journey labels.

    It combines task-set sortie lower bounds over disjoint remaining task
    subsets and ignores timing/order compatibility.  The result is therefore a
    lower bound on the best possible continuation; if even this optimistic
    value cannot make the label negative, the label is safe to prune.
    """

    def __init__(
        self,
        task_set_cache: _TaskSetReducedCostLowerBoundCache,
        *,
        task_count: int,
        max_tasks_per_sortie: int,
        enabled: bool,
    ) -> None:
        self.task_set_cache = task_set_cache
        self.task_count = int(task_count)
        self.max_tasks_per_sortie = max(1, int(max_tasks_per_sortie))
        self.enabled = bool(enabled)
        self.full_mask = (1 << int(task_count)) - 1 if self.enabled else 0
        self.cache: dict[tuple[int, int], float] = {}

    def value(self, used_mask: int, remaining_count: int) -> float | None:
        if not self.enabled:
            return None
        available = self.full_mask ^ int(used_mask)
        if available < 0 or available > self.full_mask:
            return None
        return self._value(int(available), int(remaining_count))

    def _value(self, available: int, remaining_count: int) -> float:
        if int(available) == 0 or int(remaining_count) <= 0:
            return 0.0
        key = (int(available), int(remaining_count))
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        best = 0.0
        submask = int(available)
        while submask:
            if int(submask).bit_count() <= self.max_tasks_per_sortie:
                sortie_lb = self.task_set_cache.value(int(submask))
                if sortie_lb < 0.0:
                    tail = self._value(int(available) ^ int(submask), int(remaining_count) - 1)
                    best = min(best, float(sortie_lb) + float(tail))
            submask = (submask - 1) & int(available)
        self.cache[key] = best
        return best


class _TaskSetSupersetLowerBoundCache:
    """Best optimistic sortie lower bound among supersets of a partial task set."""

    def __init__(
        self,
        task_set_cache: _TaskSetReducedCostLowerBoundCache,
        *,
        task_count: int,
        max_tasks_per_sortie: int,
        enabled: bool,
    ) -> None:
        self.task_set_cache = task_set_cache
        self.enabled = bool(enabled) and int(task_count) <= 20
        self.full_mask = (1 << int(task_count)) - 1 if self.enabled else 0
        self.max_tasks_per_sortie = max(1, int(max_tasks_per_sortie))
        self.cache: dict[tuple[int, int], float] = {}

    def value(self, required_mask: int, available_mask: int | None = None) -> float | None:
        if not self.enabled:
            return None
        required = int(required_mask)
        available = self.full_mask if available_mask is None else int(available_mask)
        if required & ~available:
            return float("inf")
        key = (required, available)
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        if required.bit_count() > self.max_tasks_per_sortie:
            self.cache[key] = float("inf")
            return float("inf")
        optional = int(available) ^ int(required)
        remaining_slots = self.max_tasks_per_sortie - int(required).bit_count()
        best = self.task_set_cache.value(required)
        submask = optional
        while submask:
            if int(submask).bit_count() <= remaining_slots:
                best = min(best, self.task_set_cache.value(required | int(submask)))
            submask = (submask - 1) & optional
        self.cache[key] = best
        return best


def price_journeys(
    data: FutureData,
    duals: JourneyDuals,
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    config: JourneyPricingConfig,
    cuts: tuple[FutureCut, ...] = tuple(),
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None = None,
    resource_cache: dict[tuple, Any] | None = None,
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    dominant_task_set_costs: dict[frozenset[int], float] | None = None,
) -> JourneyPricingResult:
    """Return at most one most-negative journey or an exact no-negative certificate."""

    if any(constraint.kind not in {"same_vehicle", "separate_vehicle"} for constraint in branch_constraints):
        return JourneyPricingResult([], False, None, 0, 0, 0, 0, "UNSUPPORTED", "branch_or_cut_not_supported")
    if any(not _journey_pricing_cut_supported(cut) for cut in cuts):
        return JourneyPricingResult([], False, None, 0, 0, 0, 0, "UNSUPPORTED", "branch_or_cut_not_supported")
    if bool(config.profile_pricing_enabled):
        return _price_journeys_by_profiles(
            data,
            duals,
            branch_constraints=branch_constraints,
            config=config,
            cuts=cuts,
            trip_cache=trip_cache,
            resource_cache=resource_cache,
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
        )
    started = time.perf_counter()
    vehicle = int(data.vehicles[0])
    trip_duals = FutureDuals(
        cover={int(task): float(value) for task, value in duals.cover.items()},
        task_vehicle={},
        sortie_count={int(vehicle): 0.0},
        time_occupation={},
        ordering={},
        branches={},
        cuts={},
    )
    trip_result = price_timed_trips(
        data,
        trip_duals,
        tuple(),
        vehicle=vehicle,
        config=PricingConfig(
            time_bucket_size=float(config.time_bucket_size),
            max_tasks_per_trip=int(config.max_tasks_per_trip),
            max_sequences=int(config.max_sequences),
            max_timed_evaluations=int(config.max_timed_evaluations),
            max_returned_trips=int(config.max_candidate_trips)
            if bool(config.allow_partial_negative) and int(config.max_candidate_trips) > 0
            else 0,
            eps=float(config.eps),
            heuristic=False,
            time_limit=float(config.time_limit),
            start_time_step=float(config.start_time_step),
            selection_mode="reduced_cost",
            max_path_combinations_per_sequence=int(config.max_path_combinations_per_sequence),
            path_dominance_enabled=bool(config.path_dominance_enabled),
            start_optimization_enabled=bool(config.start_optimization_enabled),
            max_negative_trips_per_sequence=0,
            max_negative_starts_per_profile=0,
            generalized_partial_dominance_enabled=bool(config.generalized_partial_dominance_enabled),
        ),
        cuts=tuple(),
        phase="phase2",
        trip_cache=trip_cache,
    )
    partial_trip_scan = not bool(trip_result.exhausted)
    if partial_trip_scan and (not bool(config.allow_partial_negative) or not trip_result.trips):
        return JourneyPricingResult(
            [],
            False,
            trip_result.best_reduced_cost,
            trip_result.generated_sequences,
            trip_result.evaluated_timed_trips,
            len(trip_result.trips),
            0,
            "INCOMPLETE",
            "timed_trip_pricing_incomplete",
        )
    base = float(data.fixed_vehicle_cost) - float(duals.fleet_limit)
    if not trip_result.trips:
        if base < -float(config.eps):
            return JourneyPricingResult(
                [],
                False,
                base if trip_result.best_reduced_cost is None else base + float(trip_result.best_reduced_cost),
                trip_result.generated_sequences,
                trip_result.evaluated_timed_trips,
                0,
                0,
                "INCOMPLETE",
                "negative_fleet_base_requires_nonnegative_trip_scan",
            )
        return JourneyPricingResult(
            [],
            True,
            None if trip_result.best_reduced_cost is None else base + float(trip_result.best_reduced_cost),
            trip_result.generated_sequences,
            trip_result.evaluated_timed_trips,
            0,
            0,
            "OPTIMAL",
            "no_negative_trip_contribution",
        )
    max_candidates = int(config.max_candidate_trips)
    if max_candidates > 0 and len(trip_result.trips) > max_candidates:
        return JourneyPricingResult(
            [],
            False,
            trip_result.best_reduced_cost,
            trip_result.generated_sequences,
            trip_result.evaluated_timed_trips,
            len(trip_result.trips),
            0,
            "INCOMPLETE",
            "candidate_trip_budget",
        )
    remaining_time = 0.0
    if float(config.time_limit) > 0.0:
        remaining_time = max(0.0, float(config.time_limit) - (time.perf_counter() - started))
        if remaining_time <= 0.0:
            return JourneyPricingResult(
                [],
                False,
                trip_result.best_reduced_cost,
                trip_result.generated_sequences,
                trip_result.evaluated_timed_trips,
                len(trip_result.trips),
                0,
                "INCOMPLETE",
                "time_limit_before_selection_mip",
            )
    selected, objective, status = _solve_best_journey_selection_dp(
        data,
        trip_result.trips,
        trip_duals,
        base_reduced_cost=base,
        max_states=int(config.max_dp_states),
    )
    if status != "OPTIMAL":
        return JourneyPricingResult(
            [],
            False,
            objective,
            trip_result.generated_sequences,
            trip_result.evaluated_timed_trips,
            len(trip_result.trips),
            len(selected),
            status,
            "selection_mip_not_optimal",
        )
    if objective is None or objective >= -float(config.eps):
        return JourneyPricingResult(
            [],
            not partial_trip_scan,
            objective,
            trip_result.generated_sequences,
            trip_result.evaluated_timed_trips,
            len(trip_result.trips),
            len(selected),
            "OPTIMAL" if not partial_trip_scan else "INCOMPLETE",
            "no_negative_journey" if not partial_trip_scan else "partial_scan_no_negative_journey",
        )
    journey = make_journey(data, selected)
    if journey is None:
        return JourneyPricingResult(
            [],
            False,
            objective,
            trip_result.generated_sequences,
            trip_result.evaluated_timed_trips,
            len(trip_result.trips),
            len(selected),
            "INCOMPLETE",
            "selected_trips_not_a_valid_journey",
        )
    add_threshold = max(float(config.eps), float(config.min_add_reduced_cost))
    if objective >= -add_threshold:
        return JourneyPricingResult(
            [],
            False,
            objective,
            trip_result.generated_sequences,
            trip_result.evaluated_timed_trips,
            len(trip_result.trips),
            len(selected),
            "INCOMPLETE",
            "weak_negative_journeys_filtered",
            weak_negative_journeys_filtered=1,
        )
    if journey.signature in (forbidden_journey_signatures or set()):
        return JourneyPricingResult(
            [],
            False,
            objective,
            trip_result.generated_sequences,
            trip_result.evaluated_timed_trips,
            len(trip_result.trips),
            len(selected),
            "INCOMPLETE",
            "negative_journey_already_in_pool",
            existing_journeys_filtered=1,
        )
    return JourneyPricingResult(
        [journey],
        not partial_trip_scan,
        objective,
        trip_result.generated_sequences,
        trip_result.evaluated_timed_trips,
        len(trip_result.trips),
        len(selected),
        "OPTIMAL" if not partial_trip_scan else "INCOMPLETE",
        "negative_journey" if not partial_trip_scan else "partial_negative_journey",
    )


def _price_journeys_by_profiles(
    data: FutureData,
    duals: JourneyDuals,
    *,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
    config: JourneyPricingConfig,
    cuts: tuple[FutureCut, ...],
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None,
    resource_cache: dict[tuple, Any] | None = None,
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    dominant_task_set_costs: dict[frozenset[int], float] | None = None,
) -> JourneyPricingResult:
    if (
        bool(config.direct_journey_label_pricing_enabled)
        and not branch_constraints
        and not bool(data.instance.get("scheduling", {}).get("task_waiting_allowed", True))
    ):
        return _price_journeys_by_direct_labels(
            data,
            duals,
            config=config,
            cuts=cuts,
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
        )
    if bool(config.streaming_pricing_enabled):
        return _price_journeys_by_streaming_profiles(
            data,
            duals,
            branch_constraints=branch_constraints,
            config=config,
            cuts=cuts,
            trip_cache=trip_cache,
            resource_cache=resource_cache,
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
        )
    started = time.perf_counter()
    deadline = None if float(config.time_limit) <= 0.0 else started + float(config.time_limit)
    generation_deadline = deadline
    if deadline is not None:
        fraction = min(1.0, max(0.05, float(config.profile_generation_time_fraction)))
        generation_deadline = started + float(config.time_limit) * fraction
    vehicle = int(data.vehicles[0])
    trip_duals = FutureDuals(
        cover={int(task): float(value) for task, value in duals.cover.items()},
        task_vehicle={},
        sortie_count={int(vehicle): 0.0},
        time_occupation={},
        ordering={},
        branches={},
        cuts={},
    )
    base = float(data.fixed_vehicle_cost) - float(duals.fleet_limit)
    catalog_stats: dict[str, int] = {}
    dominant_task_set_cost_by_mask = _dominant_task_set_costs_by_mask(data, dominant_task_set_costs)
    generation_started = time.perf_counter()
    profiles, generated, evaluated, best_profile_rc, exhausted, reason, cut_penalty_pruned = _generate_negative_sortie_profiles(
        data,
        trip_duals,
        base_reduced_cost=base,
        config=config,
        trip_cache=trip_cache,
        resource_cache=resource_cache,
        started=started,
        deadline=generation_deadline,
        journey_cut_duals=duals.cuts or {},
        journey_cuts=cuts,
        catalog_stats=catalog_stats,
        branch_constraints=branch_constraints,
    )
    profile_generation_time = time.perf_counter() - generation_started
    if not exhausted and not profiles:
        return JourneyPricingResult(
            [],
            False,
            best_profile_rc,
            generated,
            evaluated,
            len(profiles),
            0,
            "INCOMPLETE",
            reason or "profile_generation_incomplete",
            profile_cut_penalty_pruned=cut_penalty_pruned,
            profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
            profile_catalog_size=int(catalog_stats.get("size", 0)),
            profile_generation_time=profile_generation_time,
            **_resource_stats_kwargs(catalog_stats),
        )
    if not profiles:
        if base < -float(config.eps):
            return JourneyPricingResult(
                [],
                False,
                best_profile_rc,
                generated,
                evaluated,
                0,
                0,
                "INCOMPLETE",
                "negative_fleet_base_requires_profiles",
                profile_cut_penalty_pruned=cut_penalty_pruned,
                profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
                profile_catalog_size=int(catalog_stats.get("size", 0)),
                profile_generation_time=profile_generation_time,
                **_resource_stats_kwargs(catalog_stats),
            )
        return JourneyPricingResult(
            [],
            exhausted,
            None if best_profile_rc is None else base + float(best_profile_rc),
            generated,
            evaluated,
            0,
            0,
            "OPTIMAL" if exhausted else "INCOMPLETE",
            "no_negative_sortie_profile" if exhausted else reason,
            profile_cut_penalty_pruned=cut_penalty_pruned,
            profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
            profile_catalog_size=int(catalog_stats.get("size", 0)),
            profile_generation_time=profile_generation_time,
            **_resource_stats_kwargs(catalog_stats),
            )
    profile_dominance_pruned = 0
    filter_started = time.perf_counter()
    if bool(catalog_stats.get("online_dominance_applied", 0)):
        profile_dominance_pruned = int(catalog_stats.get("online_dominance_pruned", 0))
    elif bool(config.profile_cross_dominance_enabled):
        profiles, profile_dominance_pruned = _filter_dominated_sortie_profiles(profiles)
    profile_filter_time = time.perf_counter() - filter_started
    max_returned = max(1, int(config.max_returned_journeys))
    candidate_return_limit = max_returned * max(1, int(config.duplicate_retry_factor))
    dp_stats: dict[str, int] = {}
    dp_started = time.perf_counter()
    selected_candidates, objective, status = _solve_best_journey_profile_dp(
        data,
        profiles,
        base_reduced_cost=base,
        cut_duals=duals.cuts or {},
        cuts=cuts,
        cut_masks=_cut_masks(data, cuts),
        max_states=int(config.max_dp_states),
        deadline=deadline,
        max_returned=candidate_return_limit,
        early_return_negative=bool(config.early_return_negative),
        early_return_min_count=max(1, int(config.early_return_negative_min_count)),
        optimistic_bound_pruning=bool(config.dp_bound_pruning_enabled),
        cross_count_dominance=bool(config.dp_cross_count_dominance_enabled),
        selection_mode=str(config.journey_selection_mode),
        dp_stats=dp_stats,
        forbidden_journey_signatures=forbidden_journey_signatures,
        duplicate_scan_limit=int(config.duplicate_scan_limit),
        dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
        pricing_config=config,
        branch_constraints=branch_constraints,
        eps=float(config.eps),
    )
    profile_dp_time = time.perf_counter() - dp_started
    if status != "OPTIMAL":
        journeys, existing_filtered, weak_filtered = _instantiate_profile_journey_candidates(
            data,
            profiles,
            selected_candidates,
            config,
            eps=float(config.eps),
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
            max_journeys=max_returned,
            branch_constraints=branch_constraints,
        )
        if journeys:
            min_returned = max(1, int(config.streaming_min_returned_journeys))
            if len(journeys) < min_returned:
                return None
            return JourneyPricingResult(
                journeys,
                False,
                objective,
                generated,
                evaluated,
                len(profiles),
                max((len(selected) for selected, _obj in selected_candidates), default=0),
                "INCOMPLETE",
                "partial_dp_negative_journey",
                profile_dominance_pruned,
                existing_filtered,
                cut_penalty_pruned,
                weak_filtered,
                dp_stats.get("bound_pruned_labels", 0),
                dp_stats.get("cross_count_pruned_labels", 0),
                bool(catalog_stats.get("hit", 0)),
                int(catalog_stats.get("size", 0)),
                profile_generation_time,
                profile_filter_time,
                profile_dp_time,
                **_resource_stats_kwargs(catalog_stats),
                **_duplicate_stats_kwargs(dp_stats),
            )
        if weak_filtered > 0:
            return JourneyPricingResult(
                [],
                False,
                objective,
                generated,
                evaluated,
                len(profiles),
                max((len(selected) for selected, _obj in selected_candidates), default=0),
                "INCOMPLETE",
                "weak_negative_journeys_filtered",
                profile_dominance_pruned,
                existing_filtered,
                cut_penalty_pruned,
                weak_filtered,
                dp_stats.get("bound_pruned_labels", 0),
                dp_stats.get("cross_count_pruned_labels", 0),
                bool(catalog_stats.get("hit", 0)),
                int(catalog_stats.get("size", 0)),
                profile_generation_time,
                profile_filter_time,
                profile_dp_time,
                **_resource_stats_kwargs(catalog_stats),
                **_duplicate_stats_kwargs(dp_stats),
            )
        return JourneyPricingResult(
            [],
            False,
            objective,
            generated,
            evaluated,
            len(profiles),
            0,
            status,
            _profile_dp_incomplete_reason(status, dp_stats),
            profile_dominance_pruned,
            existing_filtered,
            cut_penalty_pruned,
            weak_filtered,
            dp_stats.get("bound_pruned_labels", 0),
            dp_stats.get("cross_count_pruned_labels", 0),
            bool(catalog_stats.get("hit", 0)),
            int(catalog_stats.get("size", 0)),
            profile_generation_time,
            profile_filter_time,
            profile_dp_time,
            **_resource_stats_kwargs(catalog_stats),
            **_duplicate_stats_kwargs(dp_stats),
        )
    if objective is None or objective >= -float(config.eps):
        return JourneyPricingResult(
            [],
            bool(exhausted),
            objective,
            generated,
            evaluated,
            len(profiles),
            0,
            "OPTIMAL" if exhausted else "INCOMPLETE",
            "no_negative_journey" if exhausted else "partial_profile_scan_no_negative_journey",
            profile_dominance_pruned,
            dp_bound_pruned_labels=dp_stats.get("bound_pruned_labels", 0),
            dp_cross_count_pruned_labels=dp_stats.get("cross_count_pruned_labels", 0),
            profile_cut_penalty_pruned=cut_penalty_pruned,
            profile_catalog_hit=bool(catalog_stats.get("hit", 0)),
            profile_catalog_size=int(catalog_stats.get("size", 0)),
            profile_generation_time=profile_generation_time,
            profile_filter_time=profile_filter_time,
            profile_dp_time=profile_dp_time,
            **_resource_stats_kwargs(catalog_stats),
            **_duplicate_stats_kwargs(dp_stats),
        )
    journeys, existing_filtered, weak_filtered = _instantiate_profile_journey_candidates(
        data,
        profiles,
        selected_candidates,
        config,
        eps=float(config.eps),
        forbidden_journey_signatures=forbidden_journey_signatures,
        dominant_task_set_costs=dominant_task_set_costs,
        max_journeys=max_returned,
        branch_constraints=branch_constraints,
    )
    if not journeys:
        reason = "selected_profiles_not_a_valid_journey"
        exhausted_for_result = False
        status_for_result = "INCOMPLETE"
        if weak_filtered > 0:
            reason = "weak_negative_journeys_filtered"
        if existing_filtered > 0 or int(dp_stats.get("duplicate_candidates_filtered", 0)) > 0:
            reason = "negative_journeys_already_in_pool"
        elif weak_filtered <= 0:
            exhausted_for_result = False
        return JourneyPricingResult(
            [],
            exhausted_for_result,
            objective,
            generated,
            evaluated,
            len(profiles),
            0,
            status_for_result,
            reason,
            profile_dominance_pruned,
            existing_filtered,
            cut_penalty_pruned,
            weak_filtered,
            dp_stats.get("bound_pruned_labels", 0),
            dp_stats.get("cross_count_pruned_labels", 0),
            bool(catalog_stats.get("hit", 0)),
            int(catalog_stats.get("size", 0)),
            profile_generation_time,
            profile_filter_time,
            profile_dp_time,
            **_resource_stats_kwargs(catalog_stats),
            **_duplicate_stats_kwargs(dp_stats),
        )
    return JourneyPricingResult(
        journeys,
        bool(exhausted),
        objective,
        generated,
        evaluated,
        len(profiles),
        max((len(selected) for selected, _obj in selected_candidates), default=0),
        "OPTIMAL" if exhausted else "INCOMPLETE",
        "negative_journey" if exhausted else "partial_negative_journey",
        profile_dominance_pruned,
        existing_filtered,
        cut_penalty_pruned,
        weak_filtered,
        dp_stats.get("bound_pruned_labels", 0),
        dp_stats.get("cross_count_pruned_labels", 0),
        bool(catalog_stats.get("hit", 0)),
        int(catalog_stats.get("size", 0)),
        profile_generation_time,
        profile_filter_time,
        profile_dp_time,
        **_resource_stats_kwargs(catalog_stats),
        **_duplicate_stats_kwargs(dp_stats),
    )

def _price_journeys_by_direct_labels(
    data: FutureData,
    duals: JourneyDuals,
    *,
    config: JourneyPricingConfig,
    cuts: tuple[FutureCut, ...],
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    dominant_task_set_costs: dict[frozenset[int], float] | None = None,
) -> JourneyPricingResult:
    started = time.perf_counter()
    deadline = None if float(config.time_limit) <= 0.0 else started + float(config.time_limit)
    vehicle = int(data.vehicles[0])
    trip_duals = FutureDuals(
        cover={int(task): float(value) for task, value in duals.cover.items()},
        task_vehicle={},
        sortie_count={int(vehicle): 0.0},
        time_occupation={},
        ordering={},
        branches={},
        cuts={},
    )
    base = float(data.fixed_vehicle_cost) - float(duals.fleet_limit)
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    task_order = _task_order(data, trip_duals, vehicle, PricingConfig(heuristic=False, heuristic_top_tasks=0))
    cut_masks = _cut_masks(data, cuts)
    cut_duals = duals.cuts or {}
    has_nonzero_cut_dual = any(abs(float(value)) > 1.0e-9 for value in cut_duals.values())
    cut_pruning_safe = _profile_cut_penalty_pruning_safe(cut_duals, cuts)
    labels_by_count: list[dict[int, list[_DirectJourneyLabel]]] = [dict() for _ in range(int(data.sortie_limit) + 1)]
    initial = _DirectJourneyLabel(end_time=0.0, value=0.0, mask=0, trips=tuple())
    labels_by_count[0][0] = [initial]
    heap: list[tuple[float, int, float, int, _DirectJourneyLabel]] = [(0.0, 0, 0.0, 0, initial)]
    serial = 0
    generated = 0
    evaluated = 0
    state_count = 1
    best_objective: float | None = None
    candidates: list[tuple[float, JourneyColumn]] = []
    duplicate_filtered = 0
    weak_filtered = 0
    dominated_task_set_filtered = 0
    forbidden = forbidden_journey_signatures or set()
    exhausted = True
    reason = ""
    next_sortie_cache: dict[int, tuple[list[_SortieProfile], int, int, str]] = {}
    next_sortie_cache_hits = 0
    next_sortie_cache_misses = 0
    use_next_sortie_cache = bool(config.direct_journey_label_next_sortie_cache_enabled)
    direct_bound_pruned = 0
    task_set_continuation_bound = None
    if (
        bool(config.direct_journey_label_task_set_bound_pruning_enabled)
        and not has_nonzero_cut_dual
        and len(data.tasks) <= int(config.dp_disjoint_bound_max_tasks)
    ):
        task_set_continuation_bound = _TaskSetContinuationLowerBoundCache(
            _TaskSetReducedCostLowerBoundCache(data, trip_duals, vehicle, task_to_bit),
            task_count=len(data.tasks),
            max_tasks_per_sortie=_max_tasks_per_trip(data, int(config.max_tasks_per_trip)),
            enabled=True,
        )

    while heap:
        if deadline is not None and time.perf_counter() > deadline:
            exhausted = False
            reason = "time_limit"
            break
        _priority, count, _end, _serial, label = heapq.heappop(heap)
        if label not in labels_by_count[int(count)].get(int(label.mask), []):
            continue
        objective = _direct_journey_objective(float(base), label, cut_duals, cuts, cut_masks)
        best_objective = objective if best_objective is None else min(best_objective, objective)
        if label.trips and objective < -float(config.eps):
            journey = make_journey(data, label.trips)
            if journey is not None:
                if journey.signature in forbidden:
                    duplicate_filtered += 1
                elif _journey_task_set_cost_dominated(journey, dominant_task_set_costs):
                    dominated_task_set_filtered += 1
                else:
                    add_threshold = max(float(config.eps), float(config.min_add_reduced_cost))
                    if objective >= -add_threshold:
                        weak_filtered += 1
                    else:
                        candidates.append((objective, journey))
                        if bool(config.direct_journey_label_early_return_negative) and len(candidates) >= max(1, int(config.max_returned_journeys)):
                            candidates.sort(key=lambda item: (round(item[0], 9), item[1].signature))
                            selected = [journey for _obj, journey in candidates[: max(1, int(config.max_returned_journeys))]]
                            return JourneyPricingResult(
                                selected,
                                False,
                                best_objective,
                                generated,
                                evaluated,
                                state_count,
                                max((len(journey.trips) for journey in selected), default=0),
                                "INCOMPLETE",
                                "direct_label_partial_negative_journey",
                                existing_journeys_filtered=duplicate_filtered,
                                weak_negative_journeys_filtered=weak_filtered,
                                dp_bound_pruned_labels=direct_bound_pruned,
                                profile_generation_time=time.perf_counter() - started,
                                direct_next_sortie_cache_hits=next_sortie_cache_hits,
                                direct_next_sortie_cache_misses=next_sortie_cache_misses,
                                dominated_task_set_journeys_filtered=dominated_task_set_filtered,
                            )
        if int(count) >= int(data.sortie_limit):
            continue
        if task_set_continuation_bound is not None:
            remaining = int(data.sortie_limit) - int(count)
            continuation = task_set_continuation_bound.value(int(label.mask), remaining)
            if continuation is not None and float(base) + float(label.value) + float(continuation) >= -float(config.eps):
                direct_bound_pruned += 1
                continue
        remaining_threshold = max(0.0, -float(base) - float(label.value)) + float(config.eps)
        if cut_duals and not cut_pruning_safe:
            # Journey-level cut coefficients depend on the final task mask.
            # A sortie that is not attractive by its own contribution can still
            # be part of a negative journey after cut duals are applied.
            remaining_threshold = float("inf")
        if use_next_sortie_cache:
            cached = next_sortie_cache.get(int(label.mask))
            if cached is None:
                next_sortie_cache_misses += 1
                profiles, gen_inc, profile_eval_inc, incomplete_reason = _direct_next_sortie_profiles(
                    data,
                    trip_duals,
                    task_order,
                    task_to_bit,
                    used_mask=int(label.mask),
                    config=config,
                    deadline=deadline,
                )
                next_sortie_cache[int(label.mask)] = (profiles, gen_inc, profile_eval_inc, incomplete_reason)
            else:
                next_sortie_cache_hits += 1
                profiles, _cached_gen, _cached_eval, incomplete_reason = cached
                gen_inc = 0
                profile_eval_inc = 0
            next_trips, instantiate_eval_inc, conversion_reason = _direct_sortie_profiles_to_trips(
                data,
                profiles,
                earliest_start=float(label.end_time),
                threshold=remaining_threshold,
                cut_duals=cut_duals,
                cuts=cuts,
                cut_masks=cut_masks,
                cut_pruning_safe=cut_pruning_safe,
                config=config,
                deadline=deadline,
            )
            eval_inc = int(profile_eval_inc) + int(instantiate_eval_inc)
            incomplete_reason = incomplete_reason or conversion_reason
        else:
            next_trips, gen_inc, eval_inc, incomplete_reason = _direct_next_sortie_trips(
                data,
                trip_duals,
                task_order,
                task_to_bit,
                used_mask=int(label.mask),
                earliest_start=float(label.end_time),
                threshold=remaining_threshold,
                cut_duals=cut_duals,
                cuts=cuts,
                cut_masks=cut_masks,
                cut_pruning_safe=cut_pruning_safe,
                config=config,
                deadline=deadline,
            )
        generated += gen_inc
        evaluated += eval_inc
        if incomplete_reason:
            exhausted = False
            reason = incomplete_reason
            break
        for trip, contribution, trip_mask in next_trips:
            if int(label.mask) & int(trip_mask):
                continue
            new_label = _DirectJourneyLabel(
                end_time=float(trip.end_time),
                value=round(float(label.value) + float(contribution), 9),
                mask=int(label.mask) | int(trip_mask),
                trips=(*label.trips, trip),
            )
            added = _add_direct_journey_label(labels_by_count[int(count) + 1], int(new_label.mask), new_label)
            state_count += int(added)
            if not added:
                continue
            if int(config.max_dp_states) > 0 and state_count > int(config.max_dp_states):
                exhausted = False
                reason = "direct_label_state_budget"
                break
            serial += 1
            heapq.heappush(
                heap,
                (
                    _direct_journey_label_priority(float(base), new_label, cut_duals, cuts, cut_masks),
                    int(count) + 1,
                    round(float(new_label.end_time), 9),
                    serial,
                    new_label,
                ),
            )
        if not exhausted:
            break

    candidates.sort(key=lambda item: (round(item[0], 9), item[1].signature))
    selected = [journey for _obj, journey in candidates[: max(1, int(config.max_returned_journeys))]]
    if selected:
        return JourneyPricingResult(
            selected,
            bool(exhausted),
            best_objective,
            generated,
            evaluated,
            state_count,
            max((len(journey.trips) for journey in selected), default=0),
            "OPTIMAL" if exhausted else "INCOMPLETE",
            "direct_label_negative_journey" if exhausted else reason or "direct_label_partial_negative_journey",
            existing_journeys_filtered=duplicate_filtered,
            weak_negative_journeys_filtered=weak_filtered,
            dp_bound_pruned_labels=direct_bound_pruned,
            profile_generation_time=time.perf_counter() - started,
            direct_next_sortie_cache_hits=next_sortie_cache_hits,
            direct_next_sortie_cache_misses=next_sortie_cache_misses,
            dominated_task_set_journeys_filtered=dominated_task_set_filtered,
        )
    status = "OPTIMAL" if exhausted else "INCOMPLETE"
    final_reason = "direct_label_no_negative_journey" if exhausted else reason or "direct_label_incomplete"
    if weak_filtered > 0:
        status = "INCOMPLETE"
        final_reason = "weak_negative_journeys_filtered"
    if duplicate_filtered > 0 and not exhausted:
        final_reason = "negative_journeys_already_in_pool"
    if dominated_task_set_filtered > 0 and not exhausted:
        final_reason = "dominated_task_set_journeys_filtered"
    return JourneyPricingResult(
        [],
        bool(exhausted) and weak_filtered <= 0,
        best_objective,
        generated,
        evaluated,
        state_count,
        0,
        status,
        final_reason,
        existing_journeys_filtered=duplicate_filtered,
        weak_negative_journeys_filtered=weak_filtered,
        dp_bound_pruned_labels=direct_bound_pruned,
        profile_generation_time=time.perf_counter() - started,
        direct_next_sortie_cache_hits=next_sortie_cache_hits,
        direct_next_sortie_cache_misses=next_sortie_cache_misses,
        dominated_task_set_journeys_filtered=dominated_task_set_filtered,
    )

def _direct_next_sortie_trips(
    data: FutureData,
    duals: FutureDuals,
    task_order: tuple[int, ...],
    task_to_bit: dict[int, int],
    *,
    used_mask: int,
    earliest_start: float,
    threshold: float,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    cut_pruning_safe: bool,
    config: JourneyPricingConfig,
    deadline: float | None,
) -> tuple[list[tuple[TimedTrip, float, int]], int, int, str]:
    max_tasks = _max_tasks_per_trip(data, int(config.max_tasks_per_trip))
    initial = _SortiePartialLabel(
        sequence=tuple(),
        mask=0,
        last=0,
        partial=_PartialNoWaitingPathProfile(
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=float(data.horizon),
            offset=0.0,
            travel_cost=0.0,
            travel_energy=0.0,
            service_cost=0.0,
            service_energy=0.0,
        ),
    )
    labels_by_key: dict[tuple[int, int], list[_SortiePartialLabel]] = {(0, 0): [initial]}
    heap: list[tuple[float, int, float, tuple[int, ...], int, _SortiePartialLabel]] = [
        (_sortie_partial_label_priority(initial, duals), 0, 0.0, tuple(), 0, initial)
    ]
    serial = 0
    generated = 0
    evaluated = 0
    trips_by_signature: dict[tuple, tuple[TimedTrip, float, int]] = {}
    available_mask = ((1 << len(data.tasks)) - 1) ^ int(used_mask)
    superset_bound_cache = (
        _TaskSetSupersetLowerBoundCache(
            _TaskSetReducedCostLowerBoundCache(data, duals, int(data.vehicles[0]), task_to_bit),
            task_count=len(data.tasks),
            max_tasks_per_sortie=max_tasks,
            enabled=True,
        )
        if bool(config.profile_labeling_task_set_superset_pruning_enabled) and threshold < float("inf")
        else None
    )
    while heap:
        if deadline is not None and time.perf_counter() > deadline:
            return list(trips_by_signature.values()), generated, evaluated, "time_limit"
        _priority, _depth, _offset, _seq_key, _serial, label = heapq.heappop(heap)
        if label not in labels_by_key.get((int(label.mask), int(label.last)), []):
            continue
        if len(label.sequence) >= max_tasks:
            continue
        for task in task_order:
            task = int(task)
            global_bit = 1 << task_to_bit[task]
            if int(used_mask) & global_bit or label.mask & global_bit:
                continue
            sequence = (*label.sequence, task)
            local_mask = label.mask | global_bit
            if superset_bound_cache is not None:
                superset_lb = superset_bound_cache.value(local_mask, available_mask)
                if superset_lb is not None and superset_lb >= threshold:
                    continue
            if not _sequence_resource_precheck(data, sequence):
                continue
            options = data.options(int(label.last), task)
            if not options:
                continue
            for option in options:
                if deadline is not None and time.perf_counter() > deadline:
                    return list(trips_by_signature.values()), generated, evaluated, "time_limit"
                extended = _extend_no_waiting_partial(data, sequence, len(label.sequence), label.partial, option)
                if extended is None:
                    continue
                generated += 1
                if int(config.max_sequences) > 0 and generated > int(config.max_sequences):
                    return list(trips_by_signature.values()), generated, evaluated, "direct_label_sequence_budget"
                new_label = _SortiePartialLabel(sequence=sequence, mask=local_mask, last=task, partial=extended)
                if not _add_sortie_partial_label(labels_by_key.setdefault((local_mask, task), []), new_label):
                    continue
                serial += 1
                heapq.heappush(
                    heap,
                    (
                        _sortie_partial_label_priority(new_label, duals),
                        len(new_label.sequence),
                        round(float(new_label.partial.offset), 9),
                        tuple(int(item) for item in new_label.sequence),
                        serial,
                        new_label,
                    ),
                )
                completed, eval_inc = _complete_direct_sortie_label_trips(
                    data,
                    duals,
                    new_label,
                    config,
                    earliest_start=earliest_start,
                    threshold=threshold,
                    cut_duals=cut_duals,
                    cuts=cuts,
                    cut_masks=cut_masks,
                    cut_pruning_safe=cut_pruning_safe,
                    task_to_bit=task_to_bit,
                )
                evaluated += eval_inc
                for trip, contribution, trip_mask in completed:
                    old = trips_by_signature.get(trip.signature)
                    if old is None or contribution < old[1] - 1.0e-9:
                        trips_by_signature[trip.signature] = (trip, contribution, trip_mask)
                if int(config.max_timed_evaluations) > 0 and evaluated > int(config.max_timed_evaluations):
                    return list(trips_by_signature.values()), generated, evaluated, "direct_label_profile_evaluation_budget"
    return list(trips_by_signature.values()), generated, evaluated, ""


def _direct_next_sortie_profiles(
    data: FutureData,
    duals: FutureDuals,
    task_order: tuple[int, ...],
    task_to_bit: dict[int, int],
    *,
    used_mask: int,
    config: JourneyPricingConfig,
    deadline: float | None,
) -> tuple[list[_SortieProfile], int, int, str]:
    max_tasks = _max_tasks_per_trip(data, int(config.max_tasks_per_trip))
    initial = _SortiePartialLabel(
        sequence=tuple(),
        mask=0,
        last=0,
        partial=_PartialNoWaitingPathProfile(
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=float(data.horizon),
            offset=0.0,
            travel_cost=0.0,
            travel_energy=0.0,
            service_cost=0.0,
            service_energy=0.0,
        ),
    )
    labels_by_key: dict[tuple[int, int], list[_SortiePartialLabel]] = {(0, 0): [initial]}
    heap: list[tuple[float, int, float, tuple[int, ...], int, _SortiePartialLabel]] = [
        (_sortie_partial_label_priority(initial, duals), 0, 0.0, tuple(), 0, initial)
    ]
    serial = 0
    generated = 0
    evaluated = 0
    profiles_by_key: dict[tuple, _SortieProfile] = {}
    profiles_by_mask: dict[int, list[_SortieProfile]] = {}
    while heap:
        if deadline is not None and time.perf_counter() > deadline:
            return list(profiles_by_key.values()), generated, evaluated, "time_limit"
        _priority, _depth, _offset, _seq_key, _serial, label = heapq.heappop(heap)
        if label not in labels_by_key.get((int(label.mask), int(label.last)), []):
            continue
        if len(label.sequence) >= max_tasks:
            continue
        for task in task_order:
            task = int(task)
            global_bit = 1 << task_to_bit[task]
            if int(used_mask) & global_bit or label.mask & global_bit:
                continue
            sequence = (*label.sequence, task)
            if not _sequence_resource_precheck(data, sequence):
                continue
            options = data.options(int(label.last), task)
            if not options:
                continue
            for option in options:
                if deadline is not None and time.perf_counter() > deadline:
                    return list(profiles_by_key.values()), generated, evaluated, "time_limit"
                extended = _extend_no_waiting_partial(data, sequence, len(label.sequence), label.partial, option)
                if extended is None:
                    continue
                generated += 1
                if int(config.max_sequences) > 0 and generated > int(config.max_sequences):
                    return list(profiles_by_key.values()), generated, evaluated, "direct_label_sequence_budget"
                local_mask = label.mask | global_bit
                new_label = _SortiePartialLabel(sequence=sequence, mask=local_mask, last=task, partial=extended)
                if not _add_sortie_partial_label(labels_by_key.setdefault((local_mask, task), []), new_label):
                    continue
                serial += 1
                heapq.heappush(
                    heap,
                    (
                        _sortie_partial_label_priority(new_label, duals),
                        len(new_label.sequence),
                        round(float(new_label.partial.offset), 9),
                        tuple(int(item) for item in new_label.sequence),
                        serial,
                        new_label,
                    ),
                )
                completed, eval_inc = _complete_direct_sortie_label_profiles(
                    data,
                    duals,
                    new_label,
                    task_to_bit,
                )
                evaluated += eval_inc
                for profile in completed:
                    key = (
                        tuple(int(task) for task in profile.sequence),
                        tuple(option.option_id for option in profile.arc_options),
                        round(float(profile.lower_start), 6),
                        round(float(profile.upper_start), 6),
                        round(float(profile.end_offset), 6),
                    )
                    old = profiles_by_key.get(key)
                    if old is None or profile.contribution < old.contribution - 1.0e-9:
                        profiles_by_key[key] = profile
                if int(config.max_timed_evaluations) > 0 and evaluated > int(config.max_timed_evaluations):
                    return list(profiles_by_key.values()), generated, evaluated, "direct_label_profile_evaluation_budget"
    return list(profiles_by_key.values()), generated, evaluated, ""


def _complete_direct_sortie_label_profiles(
    data: FutureData,
    duals: FutureDuals,
    label: _SortiePartialLabel,
    task_to_bit: dict[int, int],
) -> tuple[list[_SortieProfile], int]:
    options = data.options(int(label.last), 0)
    if not options:
        return [], 0
    dual_sum = sum(float(duals.cover.get(int(task), 0.0)) for task in set(label.sequence))
    completed: list[_SortieProfile] = []
    evaluated = 0
    mask = 0
    for task in set(label.sequence):
        mask |= 1 << task_to_bit[int(task)]
    for option in options:
        base = _complete_no_waiting_partial(data, label.partial, option)
        if base is None:
            continue
        evaluated += 1
        profile = base.profile
        contribution = float(profile.cost) - dual_sum
        completed.append(
            _SortieProfile(
                sequence=tuple(int(task) for task in label.sequence),
                arc_options=base.arc_options,
                lower_start=float(profile.lower_start),
                upper_start=float(profile.upper_start),
                end_offset=float(profile.end_offset),
                cost=float(profile.cost),
                mask=mask,
                contribution=contribution,
            )
        )
    return completed, evaluated


def _direct_sortie_profiles_to_trips(
    data: FutureData,
    profiles: list[_SortieProfile],
    *,
    earliest_start: float,
    threshold: float,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    cut_pruning_safe: bool,
    config: JourneyPricingConfig,
    deadline: float | None = None,
) -> tuple[list[tuple[TimedTrip, float, int]], int, str]:
    trips_by_signature: dict[tuple, tuple[TimedTrip, float, int]] = {}
    evaluated = 0
    for profile in profiles:
        if deadline is not None and time.perf_counter() > deadline:
            return list(trips_by_signature.values()), evaluated, "time_limit"
        profile_cut_penalty = _profile_cut_penalty(
            int(profile.mask),
            cut_duals,
            cuts,
            cut_masks,
            enabled=bool(cut_pruning_safe),
        )
        if float(profile.contribution) + profile_cut_penalty >= float(threshold):
            continue
        start = max(float(earliest_start), float(profile.lower_start))
        if start > float(profile.upper_start) + 1.0e-9:
            continue
        trip = evaluate_timed_trip(
            data,
            profile.sequence,
            start,
            time_bucket_size=float(config.time_bucket_size),
            arc_options=profile.arc_options,
        )
        evaluated += 1
        if trip is None:
            continue
        old = trips_by_signature.get(trip.signature)
        contribution = float(profile.contribution)
        if old is None or contribution < old[1] - 1.0e-9:
            trips_by_signature[trip.signature] = (trip, contribution, int(profile.mask))
    return list(trips_by_signature.values()), evaluated, ""


def _complete_direct_sortie_label_trips(
    data: FutureData,
    duals: FutureDuals,
    label: _SortiePartialLabel,
    config: JourneyPricingConfig,
    *,
    earliest_start: float,
    threshold: float,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    cut_pruning_safe: bool,
    task_to_bit: dict[int, int],
) -> tuple[list[tuple[TimedTrip, float, int]], int]:
    options = data.options(int(label.last), 0)
    if not options:
        return [], 0
    dual_sum = sum(float(duals.cover.get(int(task), 0.0)) for task in set(label.sequence))
    completed: list[tuple[TimedTrip, float, int]] = []
    evaluated = 0
    mask = 0
    for task in set(label.sequence):
        mask |= 1 << task_to_bit[int(task)]
    profile_cut_penalty = _profile_cut_penalty(mask, cut_duals, cuts, cut_masks, enabled=bool(cut_pruning_safe))
    completion_cost_lb = float(label.partial.travel_cost) + float(label.partial.service_cost) + min(
        float(option.cost) for option in options
    )
    if completion_cost_lb - dual_sum + profile_cut_penalty >= float(threshold):
        return [], 0
    for option in options:
        base = _complete_no_waiting_partial(data, label.partial, option)
        if base is None:
            continue
        profile = base.profile
        start = max(float(earliest_start), float(profile.lower_start))
        if start > float(profile.upper_start) + 1.0e-9:
            continue
        contribution = float(profile.cost) - dual_sum
        if contribution + profile_cut_penalty >= float(threshold):
            continue
        trip = evaluate_timed_trip(
            data,
            label.sequence,
            start,
            time_bucket_size=float(config.time_bucket_size),
            arc_options=base.arc_options,
            include_physical_paths=False,
        )
        evaluated += 1
        if trip is None:
            continue
        completed.append((trip, contribution, mask))
    return completed, evaluated


def _direct_journey_objective(
    base_reduced_cost: float,
    label: _DirectJourneyLabel,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
) -> float:
    return (
        float(base_reduced_cost)
        + float(label.value)
        - _journey_cut_dual_value_cached(int(label.mask), cut_duals, cuts, cut_masks, {})
    )


def _direct_journey_label_priority(
    base_reduced_cost: float,
    label: _DirectJourneyLabel,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
) -> float:
    return round(_direct_journey_objective(base_reduced_cost, label, cut_duals, cuts, cut_masks), 9)


def _add_direct_journey_label(store: dict[int, list[_DirectJourneyLabel]], mask: int, label: _DirectJourneyLabel) -> bool:
    labels = store.setdefault(int(mask), [])
    for old in labels:
        if _dominates_direct_journey_label(old, label):
            return False
    labels[:] = [old for old in labels if not _dominates_direct_journey_label(label, old)]
    labels.append(label)
    return True


def _dominates_direct_journey_label(left: _DirectJourneyLabel, right: _DirectJourneyLabel) -> bool:
    return bool(
        float(left.end_time) <= float(right.end_time) + 1.0e-9
        and float(left.value) <= float(right.value) + 1.0e-9
    )


def _price_journeys_by_streaming_profiles(
    data: FutureData,
    duals: JourneyDuals,
    *,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
    config: JourneyPricingConfig,
    cuts: tuple[FutureCut, ...],
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None,
    resource_cache: dict[tuple, Any] | None = None,
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    dominant_task_set_costs: dict[frozenset[int], float] | None = None,
) -> JourneyPricingResult:
    """Interleave sortie-profile generation with journey DP.

    A partial streaming hit is a valid negative-column search result, but not an
    exact no-negative certificate.  If profile generation exhausts, the final DP
    result is handled exactly like the materialized profile oracle.
    """

    started = time.perf_counter()
    deadline = None if float(config.time_limit) <= 0.0 else started + float(config.time_limit)
    vehicle = int(data.vehicles[0])
    trip_duals = FutureDuals(
        cover={int(task): float(value) for task, value in duals.cover.items()},
        task_vehicle={},
        sortie_count={int(vehicle): 0.0},
        time_occupation={},
        ordering={},
        branches={},
        cuts={},
    )
    base = float(data.fixed_vehicle_cost) - float(duals.fleet_limit)
    max_returned = max(1, int(config.max_returned_journeys))
    candidate_return_limit = max_returned * max(1, int(config.duplicate_retry_factor))
    cut_masks = _cut_masks(data, cuts)
    dominant_task_set_cost_by_mask = _dominant_task_set_costs_by_mask(data, dominant_task_set_costs)
    stream_batch = max(1, int(config.streaming_profile_batch_size))
    stream_min_negative = max(1, int(config.streaming_min_negative_batch))
    catalog_stats: dict[str, int] = {}
    best_partial_result: JourneyPricingResult | None = None

    def remember_partial(result: JourneyPricingResult) -> None:
        nonlocal best_partial_result
        if not result.journeys:
            return
        if best_partial_result is None:
            best_partial_result = result
            return
        current_count = len(result.journeys)
        best_count = len(best_partial_result.journeys)
        current_rc = math.inf if result.best_reduced_cost is None else float(result.best_reduced_cost)
        best_rc = math.inf if best_partial_result.best_reduced_cost is None else float(best_partial_result.best_reduced_cost)
        if current_count > best_count or (current_count == best_count and current_rc < best_rc - 1.0e-9):
            best_partial_result = result

    def stream_callback(
        profiles: list[_SortieProfile],
        generated: int,
        evaluated: int,
        best_profile_rc: float | None,
        cut_penalty_pruned: int,
    ) -> JourneyPricingResult | None:
        candidate_profiles = profiles
        profile_dominance_pruned = 0
        if bool(config.profile_cross_dominance_enabled):
            candidate_profiles, profile_dominance_pruned = _filter_dominated_sortie_profiles(candidate_profiles)
        dp_stats: dict[str, int] = {}
        selected_candidates, objective, status = _solve_best_journey_profile_dp(
            data,
            candidate_profiles,
            base_reduced_cost=base,
            cut_duals=duals.cuts or {},
            cuts=cuts,
            cut_masks=cut_masks,
            max_states=int(config.max_dp_states),
            deadline=deadline,
            max_returned=candidate_return_limit,
            early_return_negative=bool(config.early_return_negative),
            early_return_min_count=stream_min_negative,
            optimistic_bound_pruning=bool(config.dp_bound_pruning_enabled),
            cross_count_dominance=bool(config.dp_cross_count_dominance_enabled),
            selection_mode=str(config.journey_selection_mode),
            dp_stats=dp_stats,
            forbidden_journey_signatures=forbidden_journey_signatures,
            duplicate_scan_limit=int(config.duplicate_scan_limit),
            dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
            pricing_config=config,
            branch_constraints=branch_constraints,
            eps=float(config.eps),
        )
        if not selected_candidates:
            return None
        journeys, existing_filtered, weak_filtered = _instantiate_profile_journey_candidates(
            data,
            candidate_profiles,
            selected_candidates,
            config,
            eps=float(config.eps),
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
            max_journeys=max_returned,
            branch_constraints=branch_constraints,
        )
        if journeys:
            min_returned = max(1, int(config.streaming_min_returned_journeys))
            result = JourneyPricingResult(
                journeys,
                False,
                objective,
                generated,
                evaluated,
                len(candidate_profiles),
                max((len(selected) for selected, _obj in selected_candidates), default=0),
                "INCOMPLETE",
                "streaming_partial_negative_journey",
                profile_dominance_pruned,
                existing_filtered,
                cut_penalty_pruned,
                weak_filtered,
                dp_stats.get("bound_pruned_labels", 0),
                dp_stats.get("cross_count_pruned_labels", 0),
                duplicate_candidate_scan_count=dp_stats.get("duplicate_candidate_scan_count", 0),
                duplicate_candidates_filtered=dp_stats.get("duplicate_candidates_filtered", 0),
                duplicate_scan_limited=bool(dp_stats.get("duplicate_scan_limited", 0)),
                **_dp_profile_stats_kwargs(dp_stats),
                **_resource_stats_kwargs(catalog_stats),
            )
            remember_partial(result)
            if len(journeys) < min_returned:
                adaptive_min = int(config.streaming_partial_return_min_journeys)
                adaptive_after = float(config.streaming_partial_return_after_time)
                if (
                    adaptive_min > 0
                    and adaptive_after > 0.0
                    and len(journeys) >= adaptive_min
                    and time.perf_counter() - started >= adaptive_after
                ):
                    return result
                return None
            return result
        if weak_filtered > 0:
            return JourneyPricingResult(
                [],
                False,
                objective,
                generated,
                evaluated,
                len(candidate_profiles),
                max((len(selected) for selected, _obj in selected_candidates), default=0),
                "INCOMPLETE",
                "weak_negative_journeys_filtered",
                profile_dominance_pruned,
                existing_filtered,
                cut_penalty_pruned,
                weak_filtered,
                dp_stats.get("bound_pruned_labels", 0),
                dp_stats.get("cross_count_pruned_labels", 0),
                duplicate_candidate_scan_count=dp_stats.get("duplicate_candidate_scan_count", 0),
                duplicate_candidates_filtered=dp_stats.get("duplicate_candidates_filtered", 0),
                duplicate_scan_limited=bool(dp_stats.get("duplicate_scan_limited", 0)),
                **_dp_profile_stats_kwargs(dp_stats),
                **_resource_stats_kwargs(catalog_stats),
            )
        if status != "OPTIMAL" and existing_filtered <= 0:
            if deadline is None or time.perf_counter() <= float(deadline):
                return None
            return JourneyPricingResult(
                [],
                False,
                objective,
                generated,
                evaluated,
                len(candidate_profiles),
                0,
                "INCOMPLETE",
                "streaming_profile_dp_incomplete",
                profile_dominance_pruned,
                existing_filtered,
                cut_penalty_pruned,
                weak_filtered,
                dp_stats.get("bound_pruned_labels", 0),
                dp_stats.get("cross_count_pruned_labels", 0),
                **_dp_profile_stats_kwargs(dp_stats),
                **_resource_stats_kwargs(catalog_stats),
            )
        return None

    try:
        profiles, generated, evaluated, best_profile_rc, exhausted, reason, cut_penalty_pruned = _generate_negative_sortie_profiles(
            data,
            trip_duals,
            base_reduced_cost=base,
            config=config,
            trip_cache=trip_cache,
            resource_cache=resource_cache,
            started=started,
            deadline=deadline,
            journey_cut_duals=duals.cuts or {},
            journey_cuts=cuts,
            stream_callback=stream_callback,
            stream_profile_batch_size=stream_batch,
            catalog_stats=catalog_stats,
            branch_constraints=branch_constraints,
        )
    except _StreamingPricingStop as stop:
        return stop.result
    if best_partial_result is not None and not exhausted and deadline is not None and time.perf_counter() >= deadline:
        return best_partial_result
    if not exhausted and not profiles:
        if best_partial_result is not None:
            return best_partial_result
        return JourneyPricingResult(
            [],
            False,
            best_profile_rc,
            generated,
            evaluated,
            0,
            0,
            "INCOMPLETE",
            reason or "streaming_profile_generation_incomplete",
            profile_cut_penalty_pruned=cut_penalty_pruned,
            **_resource_stats_kwargs(catalog_stats),
        )
    if not profiles:
        if base < -float(config.eps):
            return JourneyPricingResult(
                [],
                False,
                best_profile_rc,
                generated,
                evaluated,
                0,
                0,
                "INCOMPLETE",
                "negative_fleet_base_requires_profiles",
                profile_cut_penalty_pruned=cut_penalty_pruned,
                **_resource_stats_kwargs(catalog_stats),
            )
        return JourneyPricingResult(
            [],
            exhausted,
            None if best_profile_rc is None else base + float(best_profile_rc),
            generated,
            evaluated,
            0,
            0,
            "OPTIMAL" if exhausted else "INCOMPLETE",
            "no_negative_sortie_profile" if exhausted else reason,
            profile_cut_penalty_pruned=cut_penalty_pruned,
            **_resource_stats_kwargs(catalog_stats),
        )
    profile_dominance_pruned = 0
    if bool(config.profile_cross_dominance_enabled):
        profiles, profile_dominance_pruned = _filter_dominated_sortie_profiles(profiles)
    dp_stats: dict[str, int] = {}
    selected_candidates, objective, status = _solve_best_journey_profile_dp(
        data,
        profiles,
        base_reduced_cost=base,
        cut_duals=duals.cuts or {},
        cuts=cuts,
        cut_masks=cut_masks,
        max_states=int(config.max_dp_states),
        deadline=deadline,
        max_returned=candidate_return_limit,
        early_return_negative=bool(config.early_return_negative),
        early_return_min_count=stream_min_negative,
        optimistic_bound_pruning=bool(config.dp_bound_pruning_enabled),
        cross_count_dominance=bool(config.dp_cross_count_dominance_enabled),
        selection_mode=str(config.journey_selection_mode),
        dp_stats=dp_stats,
        forbidden_journey_signatures=forbidden_journey_signatures,
        duplicate_scan_limit=int(config.duplicate_scan_limit),
        dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
        pricing_config=config,
        branch_constraints=branch_constraints,
        eps=float(config.eps),
    )
    if status != "OPTIMAL":
        journeys, existing_filtered, weak_filtered = _instantiate_profile_journey_candidates(
            data,
            profiles,
            selected_candidates,
            config,
            eps=float(config.eps),
            forbidden_journey_signatures=forbidden_journey_signatures,
            dominant_task_set_costs=dominant_task_set_costs,
            max_journeys=max_returned,
            branch_constraints=branch_constraints,
        )
        if journeys:
            return JourneyPricingResult(
                journeys,
                False,
                objective,
                generated,
                evaluated,
                len(profiles),
                max((len(selected) for selected, _obj in selected_candidates), default=0),
                "INCOMPLETE",
                "streaming_partial_dp_negative_journey",
                profile_dominance_pruned,
                existing_filtered,
                cut_penalty_pruned,
                weak_filtered,
                dp_stats.get("bound_pruned_labels", 0),
                dp_stats.get("cross_count_pruned_labels", 0),
                duplicate_candidate_scan_count=dp_stats.get("duplicate_candidate_scan_count", 0),
                duplicate_candidates_filtered=dp_stats.get("duplicate_candidates_filtered", 0),
                duplicate_scan_limited=bool(dp_stats.get("duplicate_scan_limited", 0)),
                **_dp_profile_stats_kwargs(dp_stats),
                **_resource_stats_kwargs(catalog_stats),
            )
        reason_text = _profile_dp_incomplete_reason("profile_dp_incomplete", dp_stats)
        if weak_filtered > 0:
            reason_text = "weak_negative_journeys_filtered"
        if existing_filtered > 0 or int(dp_stats.get("duplicate_candidates_filtered", 0)) > 0:
            reason_text = "negative_journeys_already_in_pool"
        if best_partial_result is not None:
            return best_partial_result
        return JourneyPricingResult(
            [],
            False,
            objective,
            generated,
            evaluated,
            len(profiles),
            0,
            "INCOMPLETE",
            reason_text,
            profile_dominance_pruned,
            existing_filtered,
            cut_penalty_pruned,
            weak_filtered,
            dp_stats.get("bound_pruned_labels", 0),
            dp_stats.get("cross_count_pruned_labels", 0),
            duplicate_candidate_scan_count=dp_stats.get("duplicate_candidate_scan_count", 0),
            duplicate_candidates_filtered=dp_stats.get("duplicate_candidates_filtered", 0),
            duplicate_scan_limited=bool(dp_stats.get("duplicate_scan_limited", 0)),
            **_dp_profile_stats_kwargs(dp_stats),
            **_resource_stats_kwargs(catalog_stats),
        )
    if objective is None or objective >= -float(config.eps):
        return JourneyPricingResult(
            [],
            bool(exhausted),
            objective,
            generated,
            evaluated,
            len(profiles),
            0,
            "OPTIMAL" if exhausted else "INCOMPLETE",
            "no_negative_journey" if exhausted else "partial_profile_scan_no_negative_journey",
            profile_dominance_pruned,
            dp_bound_pruned_labels=dp_stats.get("bound_pruned_labels", 0),
            dp_cross_count_pruned_labels=dp_stats.get("cross_count_pruned_labels", 0),
            profile_cut_penalty_pruned=cut_penalty_pruned,
            duplicate_candidate_scan_count=dp_stats.get("duplicate_candidate_scan_count", 0),
            duplicate_candidates_filtered=dp_stats.get("duplicate_candidates_filtered", 0),
            duplicate_scan_limited=bool(dp_stats.get("duplicate_scan_limited", 0)),
            **_dp_profile_stats_kwargs(dp_stats),
            **_resource_stats_kwargs(catalog_stats),
        )
    journeys, existing_filtered, weak_filtered = _instantiate_profile_journey_candidates(
        data,
        profiles,
        selected_candidates,
        config,
        eps=float(config.eps),
        forbidden_journey_signatures=forbidden_journey_signatures,
        dominant_task_set_costs=dominant_task_set_costs,
        max_journeys=max_returned,
        branch_constraints=branch_constraints,
    )
    if not journeys:
        reason_text = "selected_profiles_not_a_valid_journey"
        if weak_filtered > 0:
            reason_text = "weak_negative_journeys_filtered"
        if existing_filtered > 0 or int(dp_stats.get("duplicate_candidates_filtered", 0)) > 0:
            reason_text = "negative_journeys_already_in_pool"
        if best_partial_result is not None:
            return best_partial_result
        return JourneyPricingResult(
            [],
            False,
            objective,
            generated,
            evaluated,
            len(profiles),
            0,
            "INCOMPLETE",
            reason_text,
            profile_dominance_pruned,
            existing_filtered,
            cut_penalty_pruned,
            weak_filtered,
            dp_stats.get("bound_pruned_labels", 0),
            dp_stats.get("cross_count_pruned_labels", 0),
            duplicate_candidate_scan_count=dp_stats.get("duplicate_candidate_scan_count", 0),
            duplicate_candidates_filtered=dp_stats.get("duplicate_candidates_filtered", 0),
            duplicate_scan_limited=bool(dp_stats.get("duplicate_scan_limited", 0)),
            **_dp_profile_stats_kwargs(dp_stats),
            **_resource_stats_kwargs(catalog_stats),
        )
    return JourneyPricingResult(
        journeys,
        bool(exhausted),
        objective,
        generated,
        evaluated,
        len(profiles),
        max((len(selected) for selected, _obj in selected_candidates), default=0),
        "OPTIMAL" if exhausted else "INCOMPLETE",
        "negative_journey" if exhausted else "partial_negative_journey",
        profile_dominance_pruned,
        existing_filtered,
        cut_penalty_pruned,
        weak_filtered,
        dp_stats.get("bound_pruned_labels", 0),
        dp_stats.get("cross_count_pruned_labels", 0),
        duplicate_candidate_scan_count=dp_stats.get("duplicate_candidate_scan_count", 0),
        duplicate_candidates_filtered=dp_stats.get("duplicate_candidates_filtered", 0),
        duplicate_scan_limited=bool(dp_stats.get("duplicate_scan_limited", 0)),
        **_dp_profile_stats_kwargs(dp_stats),
        **_resource_stats_kwargs(catalog_stats),
    )


def _duplicate_stats_kwargs(dp_stats: dict[str, int]) -> dict[str, Any]:
    return {
        "duplicate_candidate_scan_count": int(dp_stats.get("duplicate_candidate_scan_count", 0)),
        "duplicate_candidates_filtered": int(dp_stats.get("duplicate_candidates_filtered", 0)),
        "duplicate_scan_limited": bool(dp_stats.get("duplicate_scan_limited", 0)),
        "dp_disjoint_bound_pruned_labels": int(dp_stats.get("disjoint_bound_pruned_labels", 0)),
        "dp_processed_labels": int(dp_stats.get("processed_labels", 0)),
        "dp_state_count": int(dp_stats.get("state_count", 0)),
        "dp_profile_record_scans": int(dp_stats.get("profile_record_scans", 0)),
        "dp_profile_time_filtered": int(dp_stats.get("profile_time_filtered", 0)),
        "dp_extension_attempts": int(dp_stats.get("extension_attempts", 0)),
        "dp_same_completion_pruned_labels": int(dp_stats.get("same_completion_pruned_labels", 0)),
    }


def _dp_profile_stats_kwargs(dp_stats: dict[str, int]) -> dict[str, Any]:
    return {
        "dp_processed_labels": int(dp_stats.get("processed_labels", 0)),
        "dp_state_count": int(dp_stats.get("state_count", 0)),
        "dp_profile_record_scans": int(dp_stats.get("profile_record_scans", 0)),
        "dp_profile_time_filtered": int(dp_stats.get("profile_time_filtered", 0)),
        "dp_extension_attempts": int(dp_stats.get("extension_attempts", 0)),
        "dp_same_completion_pruned_labels": int(dp_stats.get("same_completion_pruned_labels", 0)),
    }


def _resource_stats_kwargs(catalog_stats: dict[str, int] | None) -> dict[str, Any]:
    return {
        "task_set_resource_pruned_sequences": int(
            (catalog_stats or {}).get("task_set_resource_pruned_sequences", 0)
        ),
        "partial_profile_bound_pruned_labels": int(
            (catalog_stats or {}).get("partial_profile_bound_pruned_labels", 0)
        ),
        "profile_mask_cap_pruned": int((catalog_stats or {}).get("profile_mask_cap_pruned", 0)),
        "branch_mask_pruned_sequences": int((catalog_stats or {}).get("branch_mask_pruned_sequences", 0)),
        "label_physical_catalog": bool((catalog_stats or {}).get("label_physical_catalog", 0)),
        "label_physical_catalog_exhausted": bool(
            (catalog_stats or {}).get("label_physical_catalog_exhausted", 0)
        ),
        "label_resume_heap": int((catalog_stats or {}).get("label_resume_heap", 0)),
        "label_resume_profiles": int((catalog_stats or {}).get("label_resume_profiles", 0)),
        "label_resume_exhausted": bool((catalog_stats or {}).get("label_resume_exhausted", 0)),
    }


def _profile_dp_incomplete_reason(status: str, dp_stats: dict[str, int]) -> str:
    if int(dp_stats.get("duplicate_scan_limited", 0)) > 0:
        return "duplicate_scan_incomplete"
    if int(dp_stats.get("duplicate_candidates_filtered", 0)) > 0:
        return "negative_journeys_already_in_pool"
    return str(status) if str(status) != "INCOMPLETE" else "profile_dp_incomplete"


def _generate_negative_sortie_profiles(
    data: FutureData,
    duals: FutureDuals,
    *,
    base_reduced_cost: float,
    config: JourneyPricingConfig,
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None,
    started: float,
    resource_cache: dict[tuple, Any] | None = None,
    deadline: float | None = None,
    journey_cut_duals: dict[int, float] | None = None,
    journey_cuts: tuple[FutureCut, ...] = tuple(),
    stream_callback: Any | None = None,
    stream_profile_batch_size: int = 0,
    catalog_stats: dict[str, int] | None = None,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple[list[_SortieProfile], int, int, float | None, bool, str, int]:
    vehicle = int(data.vehicles[0])
    max_tasks = _max_tasks_per_trip(data, int(config.max_tasks_per_trip))
    task_order = _task_order(
        data,
        duals,
        vehicle,
        PricingConfig(heuristic=False, heuristic_top_tasks=0),
    )
    pricing_config = PricingConfig(
        time_bucket_size=float(config.time_bucket_size),
        max_tasks_per_trip=int(config.max_tasks_per_trip),
        max_sequences=int(config.max_sequences),
        max_timed_evaluations=int(config.max_timed_evaluations),
        eps=float(config.eps),
        heuristic=False,
        time_limit=float(config.time_limit),
        start_time_step=float(config.start_time_step),
        max_path_combinations_per_sequence=int(config.max_path_combinations_per_sequence),
        path_dominance_enabled=bool(config.path_dominance_enabled),
        start_optimization_enabled=bool(config.start_optimization_enabled),
        generalized_partial_dominance_enabled=bool(config.generalized_partial_dominance_enabled),
    )
    generated = 0
    evaluated = 0
    best_profile_rc: float | None = None
    exhausted = True
    reason = ""
    profiles_by_key: dict[tuple, _SortieProfile] = {}
    profiles_by_mask: dict[int, list[_SortieProfile]] = {}
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    catalog_key = _sortie_profile_catalog_key(data, config, max_tasks, branch_constraints=branch_constraints)
    if catalog_key is not None and trip_cache is not None and catalog_key in trip_cache:
        cached_catalog, cached_generated, cached_evaluated = trip_cache[catalog_key]  # type: ignore[assignment]
        profiles, best_profile_rc, cut_penalty_pruned = _filter_sortie_profile_catalog(
            cached_catalog,  # type: ignore[arg-type]
            duals,
            base_reduced_cost=base_reduced_cost,
            config=config,
            journey_cut_duals=journey_cut_duals or {},
            journey_cuts=journey_cuts,
            task_to_bit=task_to_bit,
        )
        if catalog_stats is not None:
            catalog_stats["hit"] = 1
            catalog_stats["size"] = len(cached_catalog)  # type: ignore[arg-type]
        return profiles, int(cached_generated), int(cached_evaluated), best_profile_rc, True, "", cut_penalty_pruned
    threshold = max(0.0, -float(base_reduced_cost)) + float(config.eps)
    cut_penalty_enabled = _profile_cut_penalty_pruning_safe(journey_cut_duals or {}, journey_cuts)
    if (duals.cuts or {}) or ((journey_cut_duals or {}) and not cut_penalty_enabled):
        # Cut contributions are evaluated on the final journey mask.  Keep all
        # potentially feasible sortie profiles to preserve exactness.
        threshold = float("inf")
    cut_masks = _cut_masks(data, journey_cuts)
    cut_penalty_pruned = 0
    next_stream_profile_count = max(1, int(stream_profile_batch_size)) if stream_callback is not None else 0
    online_dominance = bool(config.profile_online_dominance_enabled) and bool(config.profile_cross_dominance_enabled)
    online_dominance_pruned = 0

    def current_profiles() -> list[_SortieProfile]:
        if not online_dominance:
            return list(profiles_by_key.values())
        return [profile for group in profiles_by_mask.values() for profile in group]

    def record_online_stats() -> None:
        if catalog_stats is not None and online_dominance:
            catalog_stats["online_dominance_pruned"] = int(online_dominance_pruned)

    task_set_bound_cache = (
        _TaskSetReducedCostLowerBoundCache(data, duals, vehicle, task_to_bit)
        if bool(config.task_set_bound_pruning_enabled)
        else None
    )
    if (
        bool(config.profile_labeling_enabled)
        and not bool(data.instance.get("scheduling", {}).get("task_waiting_allowed", True))
    ):
        if bool(config.profile_labeling_physical_catalog_resume_enabled) and trip_cache is not None:
            return _generate_negative_sortie_profiles_by_label_physical_catalog(
                data,
                duals,
                base_reduced_cost=base_reduced_cost,
                config=config,
                deadline=deadline,
                task_order=task_order,
                task_to_bit=task_to_bit,
                trip_cache=trip_cache,
                resource_cache=resource_cache,
                catalog_stats=catalog_stats,
                journey_cut_duals=journey_cut_duals or {},
                journey_cuts=journey_cuts,
                stream_callback=stream_callback,
                stream_profile_batch_size=stream_profile_batch_size,
                branch_constraints=branch_constraints,
            )
        labeled = _generate_negative_sortie_profiles_by_labels(
            data,
            duals,
            base_reduced_cost=base_reduced_cost,
            config=config,
            deadline=deadline,
            task_order=task_order,
            threshold=threshold,
            task_to_bit=task_to_bit,
            trip_cache=trip_cache,
            resource_cache=resource_cache,
            catalog_stats=catalog_stats,
            stream_callback=stream_callback,
            stream_profile_batch_size=stream_profile_batch_size,
            branch_constraints=branch_constraints,
        )
        return (*labeled, 0)
    if (
        catalog_key is not None
        and trip_cache is not None
        and stream_callback is None
        and bool(config.profile_catalog_resume_enabled)
    ):
        resume_key = (*catalog_key, "resume_v1")
        state = trip_cache.get(resume_key)
        if not isinstance(state, _SortieProfileCatalogState):
            state = _SortieProfileCatalogState(profiles=[], keys=set())
            trip_cache[resume_key] = state  # type: ignore[assignment]
        before_generated = int(state.generated)
        before_evaluated = int(state.evaluated)
        _resume_sortie_profile_catalog(
            data,
            config,
            trip_cache,
            state,
            deadline=deadline,
            max_tasks=max_tasks,
            task_order=tuple(int(task) for task in data.tasks),
            branch_constraints=branch_constraints,
        )
        if catalog_stats is not None:
            catalog_stats["hit"] = int(before_evaluated > 0)
            catalog_stats["size"] = len(state.profiles)
            catalog_stats["resume"] = 1
            catalog_stats["resume_exhausted"] = int(state.exhausted)
        profiles, best_profile_rc, cut_penalty_pruned = _filter_sortie_profile_catalog(
            state.profiles,
            duals,
            base_reduced_cost=base_reduced_cost,
            config=config,
            journey_cut_duals=journey_cut_duals or {},
            journey_cuts=journey_cuts,
            task_to_bit=task_to_bit,
        )
        return (
            profiles,
            int(state.generated) - before_generated,
            int(state.evaluated) - before_evaluated,
            best_profile_rc,
            bool(state.exhausted),
            str(state.reason),
            cut_penalty_pruned,
        )
    if catalog_key is not None and trip_cache is not None and stream_callback is None:
        catalog, generated, evaluated, catalog_exhausted, catalog_reason = _build_sortie_profile_catalog(
            data,
            config,
            trip_cache,
            deadline=deadline,
            max_tasks=max_tasks,
            task_order=tuple(int(task) for task in data.tasks),
            branch_constraints=branch_constraints,
        )
        if catalog_exhausted and len(catalog) <= int(config.profile_catalog_max_profiles):
            trip_cache[catalog_key] = (tuple(catalog), int(generated), int(evaluated))  # type: ignore[assignment]
        if catalog_stats is not None:
            catalog_stats["hit"] = 0
            catalog_stats["size"] = len(catalog)
        profiles, best_profile_rc, cut_penalty_pruned = _filter_sortie_profile_catalog(
            catalog,
            duals,
            base_reduced_cost=base_reduced_cost,
            config=config,
            journey_cut_duals=journey_cut_duals or {},
            journey_cuts=journey_cuts,
            task_to_bit=task_to_bit,
        )
        return profiles, generated, evaluated, best_profile_rc, catalog_exhausted, catalog_reason, cut_penalty_pruned
    try:
        task_set_lb_pruned_masks: set[int] = set()
        for size in range(1, max_tasks + 1):
            for sequence in itertools.permutations(task_order, size):
                if deadline is not None and time.perf_counter() > deadline:
                    record_online_stats()
                    return current_profiles(), generated, evaluated, best_profile_rc, False, "time_limit", cut_penalty_pruned
                mask = 0
                for task in set(sequence):
                    mask |= 1 << task_to_bit[int(task)]
                if task_set_bound_cache is not None and mask in task_set_lb_pruned_masks:
                    if catalog_stats is not None:
                        catalog_stats["task_set_bound_pruned_sequences"] = int(
                            catalog_stats.get("task_set_bound_pruned_sequences", 0)
                        ) + 1
                    continue
                if not _sortie_profile_mask_allowed_by_branch(mask, branch_constraints, task_to_bit):
                    if catalog_stats is not None:
                        catalog_stats["branch_mask_pruned_sequences"] = int(
                            catalog_stats.get("branch_mask_pruned_sequences", 0)
                        ) + 1
                    continue
                profile_cut_penalty = _profile_cut_penalty(
                    mask,
                    journey_cut_duals or {},
                    journey_cuts,
                    cut_masks,
                    enabled=cut_penalty_enabled,
                )
                task_set_lb = (
                    float("-inf")
                    if task_set_bound_cache is None
                    else task_set_bound_cache.value(mask) + profile_cut_penalty
                )
                if task_set_bound_cache is not None and task_set_lb >= threshold:
                    task_set_lb_pruned_masks.add(mask)
                    if catalog_stats is not None:
                        catalog_stats["task_set_bound_pruned_sequences"] = int(
                            catalog_stats.get("task_set_bound_pruned_sequences", 0)
                        ) + 1
                    cut_penalty_pruned += int(profile_cut_penalty > 0.0)
                    continue
                if not partial_sequence_allowed(tuple(sequence), vehicle, tuple()):
                    continue
                if not _sequence_resource_precheck(data, tuple(sequence)):
                    continue
                generated += 1
                if int(config.max_sequences) > 0 and generated > int(config.max_sequences):
                    record_online_stats()
                    return current_profiles(), generated, evaluated, best_profile_rc, False, "sequence_budget", cut_penalty_pruned
                sequence_lb = _sequence_reduced_cost_lower_bound(
                    data,
                    tuple(sequence),
                    vehicle,
                    duals,
                    tuple(),
                    tuple(),
                    "phase2",
                )
                sequence_lb += profile_cut_penalty
                if sequence_lb >= threshold:
                    cut_penalty_pruned += int(profile_cut_penalty > 0.0)
                    continue
                arc_profiles, pruned, _cache_hit = _optimized_arc_profiles_for_sequence(
                    data,
                    tuple(sequence),
                    pricing_config,
                    trip_cache,
                    True,
                    tuple(),
                    vehicle,
                    True,
                    deadline=deadline,
                )
                if pruned > 0 and not bool(config.path_dominance_enabled):
                    exhausted = False
                    reason = "unsafe_profile_pruning"
                dual_sum = sum(float(duals.cover.get(int(task), 0.0)) for task in set(sequence))
                for arc_profile in arc_profiles:
                    if deadline is not None and time.perf_counter() > deadline:
                        record_online_stats()
                        return current_profiles(), generated, evaluated, best_profile_rc, False, "time_limit", cut_penalty_pruned
                    evaluated += 1
                    profile = arc_profile.profile
                    contribution = float(profile.cost) - dual_sum
                    best_profile_rc = contribution if best_profile_rc is None else min(best_profile_rc, contribution)
                    if contribution + profile_cut_penalty >= threshold:
                        cut_penalty_pruned += int(profile_cut_penalty > 0.0)
                        continue
                    key = (
                        tuple(int(task) for task in sequence),
                        tuple(option.option_id for option in arc_profile.arc_options),
                        round(float(profile.lower_start), 6),
                        round(float(profile.upper_start), 6),
                        round(float(profile.end_offset), 6),
                    )
                    candidate = _SortieProfile(
                        sequence=tuple(int(task) for task in sequence),
                        arc_options=arc_profile.arc_options,
                        lower_start=float(profile.lower_start),
                        upper_start=float(profile.upper_start),
                        end_offset=float(profile.end_offset),
                        cost=float(profile.cost),
                        mask=mask,
                        contribution=contribution,
                    )
                    old = profiles_by_key.get(key)
                    if old is None or candidate.contribution < old.contribution - 1.0e-9:
                        profiles_by_key[key] = candidate
                        if online_dominance:
                            added, pruned = _add_sortie_profile_skyline(profiles_by_mask, candidate)
                            online_dominance_pruned += int(pruned)
                            if not added:
                                online_dominance_pruned += 1
                    if stream_callback is not None and len(profiles_by_key) >= next_stream_profile_count:
                        result = stream_callback(
                            list(profiles_by_key.values()),
                            generated,
                            evaluated,
                            best_profile_rc,
                            cut_penalty_pruned,
                        )
                        next_stream_profile_count = len(profiles_by_key) + max(1, int(stream_profile_batch_size))
                        if result is not None:
                            raise _StreamingPricingStop(result)
                        if int(config.max_candidate_trips) > 0 and len(profiles_by_key) > int(config.max_candidate_trips):
                            record_online_stats()
                            return current_profiles(), generated, evaluated, best_profile_rc, False, "candidate_profile_budget", cut_penalty_pruned
                        if int(config.max_timed_evaluations) > 0 and evaluated > int(config.max_timed_evaluations):
                            record_online_stats()
                            return current_profiles(), generated, evaluated, best_profile_rc, False, "profile_evaluation_budget", cut_penalty_pruned
    except _PricingTimeout:
        record_online_stats()
        return current_profiles(), generated, evaluated, best_profile_rc, False, "time_limit", cut_penalty_pruned
    record_online_stats()
    return current_profiles(), generated, evaluated, best_profile_rc, exhausted, reason, cut_penalty_pruned


def _sortie_profile_catalog_key(
    data: FutureData,
    config: JourneyPricingConfig,
    max_tasks: int,
    *,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple | None:
    if not bool(config.profile_catalog_enabled):
        return None
    if len(data.tasks) > int(config.profile_catalog_max_tasks):
        return None
    if int(config.max_candidate_trips) > 0:
        return None
    if bool(config.profile_labeling_enabled):
        return None
    return (
        "journey_sortie_profile_catalog_v2",
        str(data.instance_path),
        _branch_constraints_cache_key(branch_constraints),
        int(max_tasks),
        int(config.max_sequences),
        int(config.max_timed_evaluations),
        round(float(config.time_bucket_size), 9),
        round(float(config.start_time_step), 9),
        int(config.max_path_combinations_per_sequence),
        bool(config.path_dominance_enabled),
        bool(config.start_optimization_enabled),
    )


def _resume_sortie_profile_catalog(
    data: FutureData,
    config: JourneyPricingConfig,
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None,
    state: _SortieProfileCatalogState,
    *,
    deadline: float | None,
    max_tasks: int,
    task_order: tuple[int, ...],
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> None:
    if bool(state.exhausted):
        return
    vehicle = int(data.vehicles[0])
    pricing_config = PricingConfig(
        time_bucket_size=float(config.time_bucket_size),
        max_tasks_per_trip=int(config.max_tasks_per_trip),
        max_sequences=int(config.max_sequences),
        max_timed_evaluations=int(config.max_timed_evaluations),
        eps=float(config.eps),
        heuristic=False,
        time_limit=float(config.time_limit),
        start_time_step=float(config.start_time_step),
        max_path_combinations_per_sequence=int(config.max_path_combinations_per_sequence),
        path_dominance_enabled=bool(config.path_dominance_enabled),
        start_optimization_enabled=bool(config.start_optimization_enabled),
        generalized_partial_dominance_enabled=bool(config.generalized_partial_dominance_enabled),
    )
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    try:
        for size in range(max(1, int(state.next_size)), int(max_tasks) + 1):
            start_index = int(state.next_permutation_index) if size == int(state.next_size) else 0
            for permutation_index, sequence in enumerate(itertools.permutations(task_order, size)):
                if permutation_index < start_index:
                    continue
                if deadline is not None and time.perf_counter() > deadline:
                    state.reason = "time_limit"
                    return
                sequence = tuple(int(task) for task in sequence)
                mask = 0
                for task in set(sequence):
                    mask |= 1 << task_to_bit[int(task)]
                if not _sortie_profile_mask_allowed_by_branch(mask, branch_constraints, task_to_bit):
                    state.next_size = size
                    state.next_permutation_index = permutation_index + 1
                    continue
                if not partial_sequence_allowed(sequence, vehicle, tuple()):
                    state.next_size = size
                    state.next_permutation_index = permutation_index + 1
                    continue
                if not _sequence_resource_precheck(data, sequence):
                    state.next_size = size
                    state.next_permutation_index = permutation_index + 1
                    continue
                if int(config.max_sequences) > 0 and int(state.generated) + 1 > int(config.max_sequences):
                    state.reason = "sequence_budget"
                    return
                arc_profiles, _pruned, _cache_hit = _optimized_arc_profiles_for_sequence(
                    data,
                    sequence,
                    pricing_config,
                    trip_cache,
                    True,
                    tuple(),
                    vehicle,
                    True,
                    deadline=deadline,
                )
                for arc_profile in arc_profiles:
                    if deadline is not None and time.perf_counter() > deadline:
                        state.reason = "time_limit"
                        return
                    profile = arc_profile.profile
                    key = (
                        sequence,
                        tuple(option.option_id for option in arc_profile.arc_options),
                        round(float(profile.lower_start), 6),
                        round(float(profile.upper_start), 6),
                        round(float(profile.end_offset), 6),
                    )
                    if key not in state.keys:
                        state.keys.add(key)
                        state.profiles.append(
                            _SortieProfile(
                                sequence=sequence,
                                arc_options=arc_profile.arc_options,
                                lower_start=float(profile.lower_start),
                                upper_start=float(profile.upper_start),
                                end_offset=float(profile.end_offset),
                                cost=float(profile.cost),
                                mask=mask,
                                contribution=float(profile.cost),
                            )
                        )
                    state.evaluated += 1
                    if len(state.profiles) > int(config.profile_catalog_max_profiles):
                        state.reason = "profile_catalog_budget"
                        return
                    if int(config.max_timed_evaluations) > 0 and int(state.evaluated) > int(config.max_timed_evaluations):
                        state.reason = "profile_evaluation_budget"
                        return
                state.generated += 1
                state.next_size = size
                state.next_permutation_index = permutation_index + 1
            state.next_size = size + 1
            state.next_permutation_index = 0
        state.exhausted = True
        state.reason = ""
    except _PricingTimeout:
        state.reason = "time_limit"


def _build_sortie_profile_catalog(
    data: FutureData,
    config: JourneyPricingConfig,
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None,
    *,
    deadline: float | None,
    max_tasks: int,
    task_order: tuple[int, ...],
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple[list[_SortieProfile], int, int, bool, str]:
    vehicle = int(data.vehicles[0])
    pricing_config = PricingConfig(
        time_bucket_size=float(config.time_bucket_size),
        max_tasks_per_trip=int(config.max_tasks_per_trip),
        max_sequences=int(config.max_sequences),
        max_timed_evaluations=int(config.max_timed_evaluations),
        eps=float(config.eps),
        heuristic=False,
        time_limit=float(config.time_limit),
        start_time_step=float(config.start_time_step),
        max_path_combinations_per_sequence=int(config.max_path_combinations_per_sequence),
        path_dominance_enabled=bool(config.path_dominance_enabled),
        start_optimization_enabled=bool(config.start_optimization_enabled),
        generalized_partial_dominance_enabled=bool(config.generalized_partial_dominance_enabled),
    )
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    generated = 0
    evaluated = 0
    exhausted = True
    reason = ""
    catalog: list[_SortieProfile] = []
    try:
        for size in range(1, int(max_tasks) + 1):
            for sequence in itertools.permutations(task_order, size):
                if deadline is not None and time.perf_counter() > deadline:
                    return catalog, generated, evaluated, False, "time_limit"
                mask = 0
                for task in set(sequence):
                    mask |= 1 << task_to_bit[int(task)]
                if not _sortie_profile_mask_allowed_by_branch(mask, branch_constraints, task_to_bit):
                    continue
                if not partial_sequence_allowed(tuple(sequence), vehicle, tuple()):
                    continue
                if not _sequence_resource_precheck(data, tuple(sequence)):
                    continue
                generated += 1
                if int(config.max_sequences) > 0 and generated > int(config.max_sequences):
                    return catalog, generated, evaluated, False, "sequence_budget"
                arc_profiles, _pruned, _cache_hit = _optimized_arc_profiles_for_sequence(
                    data,
                    tuple(sequence),
                    pricing_config,
                    trip_cache,
                    True,
                    tuple(),
                    vehicle,
                    True,
                    deadline=deadline,
                )
                for arc_profile in arc_profiles:
                    if deadline is not None and time.perf_counter() > deadline:
                        return catalog, generated, evaluated, False, "time_limit"
                    evaluated += 1
                    profile = arc_profile.profile
                    catalog.append(
                        _SortieProfile(
                            sequence=tuple(int(task) for task in sequence),
                            arc_options=arc_profile.arc_options,
                            lower_start=float(profile.lower_start),
                            upper_start=float(profile.upper_start),
                            end_offset=float(profile.end_offset),
                            cost=float(profile.cost),
                            mask=mask,
                            contribution=float(profile.cost),
                        )
                    )
                    if len(catalog) > int(config.profile_catalog_max_profiles):
                        return catalog, generated, evaluated, False, "profile_catalog_budget"
                    if int(config.max_timed_evaluations) > 0 and evaluated > int(config.max_timed_evaluations):
                        return catalog, generated, evaluated, False, "profile_evaluation_budget"
    except _PricingTimeout:
        return catalog, generated, evaluated, False, "time_limit"
    return catalog, generated, evaluated, exhausted, reason


def _filter_sortie_profile_catalog(
    catalog: tuple[_SortieProfile, ...] | list[_SortieProfile],
    duals: FutureDuals,
    *,
    base_reduced_cost: float,
    config: JourneyPricingConfig,
    journey_cut_duals: dict[int, float],
    journey_cuts: tuple[FutureCut, ...],
    task_to_bit: dict[int, int],
) -> tuple[list[_SortieProfile], float | None, int]:
    threshold = max(0.0, -float(base_reduced_cost)) + float(config.eps)
    cut_penalty_enabled = _profile_cut_penalty_pruning_safe(journey_cut_duals or {}, journey_cuts)
    if (duals.cuts or {}) or ((journey_cut_duals or {}) and not cut_penalty_enabled):
        threshold = float("inf")
    cut_masks = _cut_masks_from_task_bits(journey_cuts, task_to_bit)
    cut_penalty_pruned = 0
    best_profile_rc: float | None = None
    profiles: list[_SortieProfile] = []
    for base_profile in catalog:
        dual_sum = sum(float(duals.cover.get(int(task), 0.0)) for task in set(base_profile.sequence))
        contribution = float(base_profile.cost) - dual_sum
        best_profile_rc = contribution if best_profile_rc is None else min(best_profile_rc, contribution)
        profile_cut_penalty = _profile_cut_penalty(
            int(base_profile.mask),
            journey_cut_duals or {},
            journey_cuts,
            cut_masks,
            enabled=cut_penalty_enabled,
        )
        if contribution + profile_cut_penalty >= threshold:
            cut_penalty_pruned += int(profile_cut_penalty > 0.0)
            continue
        profiles.append(
            _SortieProfile(
                sequence=base_profile.sequence,
                arc_options=base_profile.arc_options,
                lower_start=base_profile.lower_start,
                upper_start=base_profile.upper_start,
                end_offset=base_profile.end_offset,
                cost=base_profile.cost,
                mask=base_profile.mask,
                contribution=contribution,
            )
        )
    return profiles, best_profile_rc, cut_penalty_pruned


def _generate_negative_sortie_profiles_by_label_physical_catalog(
    data: FutureData,
    duals: FutureDuals,
    *,
    base_reduced_cost: float,
    config: JourneyPricingConfig,
    deadline: float | None,
    task_order: tuple[int, ...],
    task_to_bit: dict[int, int],
    trip_cache: dict[tuple, Any],
    resource_cache: dict[tuple, Any] | None,
    catalog_stats: dict[str, int] | None,
    journey_cut_duals: dict[int, float],
    journey_cuts: tuple[FutureCut, ...],
    stream_callback: Any | None = None,
    stream_profile_batch_size: int = 0,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple[list[_SortieProfile], int, int, float | None, bool, str, int]:
    max_tasks = _max_tasks_per_trip(data, int(config.max_tasks_per_trip))
    catalog_key = _sortie_label_physical_catalog_key(data, config, task_order, max_tasks, branch_constraints)
    state = trip_cache.get(catalog_key)
    hit = isinstance(state, _SortieLabelResumeState)
    if not hit:
        state = _initial_sortie_label_resume_state(data, duals)
        trip_cache[catalog_key] = state
    assert isinstance(state, _SortieLabelResumeState)
    if hit:
        _reprioritize_sortie_label_state(state, duals)
    before_generated = int(state.generated)
    before_evaluated = int(state.evaluated)
    resource_bound_cache = _get_task_set_resource_lower_bound_cache(
        data,
        task_to_bit,
        enabled=bool(config.task_set_resource_pruning_enabled),
        resource_cache=resource_cache,
    )
    if catalog_stats is not None:
        catalog_stats["hit"] = int(hit)
        catalog_stats["label_physical_catalog"] = 1
        catalog_stats["label_resume_heap"] = len(state.heap)
        catalog_stats["label_resume_profiles"] = len(_sortie_label_state_profiles(state, config))
        catalog_stats["label_resume_exhausted"] = int(state.exhausted)
    try:
        _advance_sortie_label_resume_state(
            data,
            duals,
            state,
            config=config,
            deadline=deadline,
            task_order=task_order,
            threshold=float("inf"),
            task_to_bit=task_to_bit,
            max_tasks=max_tasks,
            resource_bound_cache=resource_bound_cache,
            catalog_stats=catalog_stats,
            stream_callback=stream_callback,
            stream_profile_batch_size=stream_profile_batch_size,
            branch_constraints=branch_constraints,
        )
    finally:
        if catalog_stats is not None:
            catalog_stats["hit"] = int(hit)
            catalog_stats["size"] = len(state.profiles_by_key)
            catalog_stats["label_physical_catalog"] = 1
            catalog_stats["label_physical_catalog_exhausted"] = int(state.exhausted)
            catalog_stats["label_resume_heap"] = len(state.heap)
            catalog_stats["label_resume_profiles"] = len(_sortie_label_state_profiles(state, config))
            catalog_stats["label_resume_exhausted"] = int(state.exhausted)
    profiles, best_profile_rc, cut_penalty_pruned = _filter_sortie_profile_catalog(
        list(state.profiles_by_key.values()),
        duals,
        base_reduced_cost=base_reduced_cost,
        config=config,
        journey_cut_duals=journey_cut_duals,
        journey_cuts=journey_cuts,
        task_to_bit=task_to_bit,
    )
    return (
        profiles,
        int(state.generated) - before_generated,
        int(state.evaluated) - before_evaluated,
        best_profile_rc,
        bool(state.exhausted),
        str(state.reason),
        int(cut_penalty_pruned),
    )


def _sortie_label_physical_catalog_key(
    data: FutureData,
    config: JourneyPricingConfig,
    task_order: tuple[int, ...],
    max_tasks: int,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple:
    return (
        "journey_sortie_label_physical_catalog_v2",
        str(data.instance_path),
        tuple(int(task) for task in data.tasks),
        _branch_constraints_cache_key(branch_constraints),
        int(max_tasks),
        int(config.max_sequences),
        int(config.max_timed_evaluations),
        int(config.max_candidate_trips),
        bool(config.generalized_partial_dominance_enabled),
    )


def _zero_sortie_profile_duals(data: FutureData) -> FutureDuals:
    return FutureDuals(
        cover={int(task): 0.0 for task in data.tasks},
        task_vehicle={},
        sortie_count={int(data.vehicles[0]): 0.0},
        time_occupation={},
        ordering={},
        branches={},
        cuts={},
    )


def _generate_negative_sortie_profiles_by_labels(
    data: FutureData,
    duals: FutureDuals,
    *,
    base_reduced_cost: float,
    config: JourneyPricingConfig,
    deadline: float | None,
    task_order: tuple[int, ...],
    threshold: float,
    task_to_bit: dict[int, int],
    trip_cache: dict[tuple, Any] | None = None,
    resource_cache: dict[tuple, Any] | None = None,
    catalog_stats: dict[str, int] | None = None,
    stream_callback: Any | None = None,
    stream_profile_batch_size: int = 0,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple[list[_SortieProfile], int, int, float | None, bool, str]:
    if bool(config.profile_labeling_best_first_enabled):
        return _generate_negative_sortie_profiles_by_best_first_labels(
            data,
            duals,
            config=config,
            deadline=deadline,
            task_order=task_order,
            threshold=threshold,
            task_to_bit=task_to_bit,
            trip_cache=trip_cache,
            resource_cache=resource_cache,
            catalog_stats=catalog_stats,
            stream_callback=stream_callback,
            stream_profile_batch_size=stream_profile_batch_size,
            branch_constraints=branch_constraints,
        )
    max_tasks = _max_tasks_per_trip(data, int(config.max_tasks_per_trip))
    initial = _SortiePartialLabel(
        sequence=tuple(),
        mask=0,
        last=0,
        partial=_PartialNoWaitingPathProfile(
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=float(data.horizon),
            offset=0.0,
            travel_cost=0.0,
            travel_energy=0.0,
            service_cost=0.0,
            service_energy=0.0,
        ),
    )
    labels_by_key: dict[tuple[int, int], list[_SortiePartialLabel]] = {(0, 0): [initial]}
    profiles_by_key: dict[tuple, _SortieProfile] = {}
    generated = 0
    evaluated = 0
    best_profile_rc: float | None = None
    exhausted = True
    reason = ""
    superset_bound_cache = (
        _TaskSetSupersetLowerBoundCache(
            _TaskSetReducedCostLowerBoundCache(data, duals, int(data.vehicles[0]), task_to_bit),
            task_count=len(data.tasks),
            max_tasks_per_sortie=max_tasks,
            enabled=True,
        )
        if bool(config.profile_labeling_task_set_superset_pruning_enabled) and threshold < float("inf")
        else None
    )
    resource_bound_cache = _get_task_set_resource_lower_bound_cache(
        data,
        task_to_bit,
        enabled=bool(config.task_set_resource_pruning_enabled),
        resource_cache=resource_cache,
    )
    partial_bound_cache = _PartialSortieProfileLowerBoundCache(
        data,
        duals,
        int(data.vehicles[0]),
        task_to_bit,
        enabled=bool(config.partial_profile_bound_pruning_enabled) and threshold < float("inf"),
    )
    for depth in range(max_tasks):
        if deadline is not None and time.perf_counter() > deadline:
            return list(profiles_by_key.values()), generated, evaluated, best_profile_rc, False, "time_limit"
        snapshot = [label for labels in labels_by_key.values() for label in labels if len(label.sequence) == depth]
        if not snapshot:
            break
        for label in snapshot:
            if deadline is not None and time.perf_counter() > deadline:
                return list(profiles_by_key.values()), generated, evaluated, best_profile_rc, False, "time_limit"
            for task in task_order:
                task = int(task)
                bit = 1 << task_to_bit[task]
                if label.mask & bit:
                    continue
                sequence = (*label.sequence, task)
                new_mask = label.mask | bit
                if not _sortie_profile_mask_allowed_by_branch(new_mask, branch_constraints, task_to_bit):
                    if catalog_stats is not None:
                        catalog_stats["branch_mask_pruned_sequences"] = int(
                            catalog_stats.get("branch_mask_pruned_sequences", 0)
                        ) + 1
                    continue
                if superset_bound_cache is not None:
                    superset_lb = superset_bound_cache.value(new_mask)
                    if superset_lb is not None and superset_lb >= threshold:
                        if catalog_stats is not None:
                            catalog_stats["task_set_bound_pruned_sequences"] = int(
                                catalog_stats.get("task_set_bound_pruned_sequences", 0)
                            ) + 1
                        continue
                if not resource_bound_cache.maybe_feasible(new_mask):
                    if catalog_stats is not None:
                        catalog_stats["task_set_resource_pruned_sequences"] = int(
                            catalog_stats.get("task_set_resource_pruned_sequences", 0)
                        ) + 1
                    continue
                if not _sequence_resource_precheck(data, sequence):
                    continue
                options = data.options(int(label.last), task)
                if not options:
                    continue
                for option in options:
                    if deadline is not None and time.perf_counter() > deadline:
                        return list(profiles_by_key.values()), generated, evaluated, best_profile_rc, False, "time_limit"
                    extended = _extend_no_waiting_partial(data, sequence, len(label.sequence), label.partial, option)
                    if extended is None:
                        continue
                    generated += 1
                    if int(config.max_sequences) > 0 and generated > int(config.max_sequences):
                        return list(profiles_by_key.values()), generated, evaluated, best_profile_rc, False, "label_budget"
                    new_label = _SortiePartialLabel(sequence=sequence, mask=new_mask, last=task, partial=extended)
                    if partial_bound_cache.value(new_label, max_tasks - len(new_label.sequence)) >= threshold:
                        if catalog_stats is not None:
                            catalog_stats["partial_profile_bound_pruned_labels"] = int(
                                catalog_stats.get("partial_profile_bound_pruned_labels", 0)
                            ) + 1
                        continue
                    _add_sortie_partial_label(
                        labels_by_key.setdefault((new_mask, task), []),
                        new_label,
                        generalized=bool(config.generalized_partial_dominance_enabled),
                    )
                    eval_inc, best_added_rc = _complete_sortie_label_profiles(
                        data,
                        duals,
                        new_label,
                        config,
                        profiles_by_key,
                        threshold,
                        task_to_bit,
                    )
                    evaluated += eval_inc
                    if best_added_rc is not None:
                        best_profile_rc = best_added_rc if best_profile_rc is None else min(best_profile_rc, best_added_rc)
                    if int(config.max_candidate_trips) > 0 and len(profiles_by_key) > int(config.max_candidate_trips):
                        return list(profiles_by_key.values()), generated, evaluated, best_profile_rc, False, "candidate_profile_budget"
                    if int(config.max_timed_evaluations) > 0 and evaluated > int(config.max_timed_evaluations):
                        return list(profiles_by_key.values()), generated, evaluated, best_profile_rc, False, "profile_evaluation_budget"
    return list(profiles_by_key.values()), generated, evaluated, best_profile_rc, exhausted, reason


def _generate_negative_sortie_profiles_by_best_first_labels(
    data: FutureData,
    duals: FutureDuals,
    *,
    config: JourneyPricingConfig,
    deadline: float | None,
    task_order: tuple[int, ...],
    threshold: float,
    task_to_bit: dict[int, int],
    trip_cache: dict[tuple, Any] | None = None,
    resource_cache: dict[tuple, Any] | None = None,
    catalog_stats: dict[str, int] | None = None,
    stream_callback: Any | None = None,
    stream_profile_batch_size: int = 0,
    resource_bound_cache: _TaskSetResourceLowerBoundCache | None = None,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple[list[_SortieProfile], int, int, float | None, bool, str]:
    max_tasks = _max_tasks_per_trip(data, int(config.max_tasks_per_trip))
    superset_bound_cache = (
        _TaskSetSupersetLowerBoundCache(
            _TaskSetReducedCostLowerBoundCache(data, duals, int(data.vehicles[0]), task_to_bit),
            task_count=len(data.tasks),
            max_tasks_per_sortie=max_tasks,
            enabled=True,
        )
        if bool(config.profile_labeling_task_set_superset_pruning_enabled) and threshold < float("inf")
        else None
    )
    if resource_bound_cache is None:
        resource_bound_cache = _get_task_set_resource_lower_bound_cache(
            data,
            task_to_bit,
            enabled=bool(config.task_set_resource_pruning_enabled),
            resource_cache=resource_cache,
        )
    partial_bound_cache = _PartialSortieProfileLowerBoundCache(
        data,
        duals,
        int(data.vehicles[0]),
        task_to_bit,
        enabled=bool(config.partial_profile_bound_pruning_enabled) and threshold < float("inf"),
    )
    resume_key = _sortie_label_resume_key(data, duals, config, task_order, threshold, max_tasks, branch_constraints)
    if resume_key is not None and trip_cache is not None:
        state = trip_cache.get(resume_key)
        hit = isinstance(state, _SortieLabelResumeState)
        if not hit:
            state = _initial_sortie_label_resume_state(data, duals)
            trip_cache[resume_key] = state
        assert isinstance(state, _SortieLabelResumeState)
        before_generated = int(state.generated)
        before_evaluated = int(state.evaluated)
        _advance_sortie_label_resume_state(
            data,
            duals,
            state,
            config=config,
            deadline=deadline,
            task_order=task_order,
            threshold=threshold,
            task_to_bit=task_to_bit,
            max_tasks=max_tasks,
            superset_bound_cache=superset_bound_cache,
            resource_bound_cache=resource_bound_cache,
            partial_bound_cache=partial_bound_cache,
            catalog_stats=catalog_stats,
            stream_callback=stream_callback,
            stream_profile_batch_size=stream_profile_batch_size,
            branch_constraints=branch_constraints,
        )
        if catalog_stats is not None:
            catalog_stats["hit"] = int(hit)
            catalog_stats["size"] = len(_sortie_label_state_profiles(state, config))
            catalog_stats["label_resume"] = 1
            catalog_stats["label_resume_hit"] = int(hit)
            catalog_stats["label_resume_heap"] = len(state.heap)
            catalog_stats["label_resume_profiles"] = len(_sortie_label_state_profiles(state, config))
            catalog_stats["label_resume_exhausted"] = int(state.exhausted)
            if bool(config.profile_online_dominance_enabled) and bool(config.profile_cross_dominance_enabled):
                catalog_stats["online_dominance_applied"] = 1
            catalog_stats["online_dominance_pruned"] = int(getattr(state, "online_dominance_pruned", 0))
        return (
            _sortie_label_state_profiles(state, config),
            int(state.generated) - before_generated,
            int(state.evaluated) - before_evaluated,
            state.best_profile_rc,
            bool(state.exhausted),
            str(state.reason),
        )
    state = _initial_sortie_label_resume_state(data, duals)
    _advance_sortie_label_resume_state(
        data,
        duals,
        state,
        config=config,
        deadline=deadline,
        task_order=task_order,
        threshold=threshold,
        task_to_bit=task_to_bit,
        max_tasks=max_tasks,
        superset_bound_cache=superset_bound_cache,
        resource_bound_cache=resource_bound_cache,
        partial_bound_cache=partial_bound_cache,
        catalog_stats=catalog_stats,
        stream_callback=stream_callback,
        stream_profile_batch_size=stream_profile_batch_size,
        branch_constraints=branch_constraints,
    )
    return (
        _sortie_label_state_profiles(state, config),
        int(state.generated),
        int(state.evaluated),
        state.best_profile_rc,
        bool(state.exhausted),
        str(state.reason),
    )


def _sortie_label_resume_key(
    data: FutureData,
    duals: FutureDuals,
    config: JourneyPricingConfig,
    task_order: tuple[int, ...],
    threshold: float,
    max_tasks: int,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple | None:
    if not bool(config.profile_labeling_resume_enabled):
        return None
    return (
        "journey_sortie_label_resume_v2",
        str(data.instance_path),
        tuple(int(task) for task in task_order),
        _branch_constraints_cache_key(branch_constraints),
        tuple((int(task), round(float(duals.cover.get(int(task), 0.0)), 9)) for task in data.tasks),
        round(float(threshold), 9),
        int(max_tasks),
        int(config.max_sequences),
        int(config.max_timed_evaluations),
        int(config.max_candidate_trips),
        bool(config.generalized_partial_dominance_enabled),
        bool(config.profile_online_dominance_enabled) and bool(config.profile_cross_dominance_enabled),
        bool(config.task_set_resource_pruning_enabled),
        bool(config.partial_profile_bound_pruning_enabled),
    )


def _initial_sortie_label_resume_state(data: FutureData, duals: FutureDuals) -> _SortieLabelResumeState:
    initial = _SortiePartialLabel(
        sequence=tuple(),
        mask=0,
        last=0,
        partial=_PartialNoWaitingPathProfile(
            arc_options=tuple(),
            lower_start=0.0,
            upper_start=float(data.horizon),
            offset=0.0,
            travel_cost=0.0,
            travel_energy=0.0,
            service_cost=0.0,
            service_energy=0.0,
        ),
    )
    labels_by_key: dict[tuple[int, int], list[_SortiePartialLabel]] = {(0, 0): [initial]}
    profiles_by_key: dict[tuple, _SortieProfile] = {}
    heap: list[tuple[float, int, float, tuple[int, ...], int, _SortiePartialLabel]] = []
    heapq.heappush(heap, (_sortie_partial_label_priority(initial, duals), 0, 0.0, tuple(), 0, initial))
    return _SortieLabelResumeState(
        labels_by_key=labels_by_key,
        profiles_by_key=profiles_by_key,
        profiles_by_mask={},
        heap=heap,
    )


def _sortie_label_state_profiles(state: _SortieLabelResumeState, config: JourneyPricingConfig) -> list[_SortieProfile]:
    online = bool(config.profile_online_dominance_enabled) and bool(config.profile_cross_dominance_enabled)
    profiles_by_mask = getattr(state, "profiles_by_mask", None)
    if not online or profiles_by_mask is None:
        return list(state.profiles_by_key.values())
    return [profile for group in profiles_by_mask.values() for profile in group]


def _advance_sortie_label_resume_state(
    data: FutureData,
    duals: FutureDuals,
    state: _SortieLabelResumeState,
    *,
    config: JourneyPricingConfig,
    deadline: float | None,
    task_order: tuple[int, ...],
    threshold: float,
    task_to_bit: dict[int, int],
    max_tasks: int,
    superset_bound_cache: _TaskSetSupersetLowerBoundCache | None = None,
    resource_bound_cache: _TaskSetResourceLowerBoundCache | None = None,
    partial_bound_cache: _PartialSortieProfileLowerBoundCache | None = None,
    catalog_stats: dict[str, int] | None = None,
    stream_callback: Any | None = None,
    stream_profile_batch_size: int = 0,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> None:
    if bool(state.exhausted):
        return
    state.reason = ""
    next_stream_profile_count = (
        len(state.profiles_by_key) + max(1, int(stream_profile_batch_size))
        if stream_callback is not None
        else 0
    )
    online_dominance = bool(config.profile_online_dominance_enabled) and bool(config.profile_cross_dominance_enabled)
    if online_dominance and getattr(state, "profiles_by_mask", None) is None:
        state.profiles_by_mask = {}
    while state.heap:
        if deadline is not None and time.perf_counter() > deadline:
            state.reason = "time_limit"
            return
        _priority, _depth_key, _offset_key, _seq_key, _serial, label = heapq.heappop(state.heap)
        if label not in state.labels_by_key.get((int(label.mask), int(label.last)), []):
            continue
        if len(label.sequence) >= max_tasks:
            continue
        for task in task_order:
            task = int(task)
            bit = 1 << task_to_bit[task]
            if label.mask & bit:
                continue
            sequence = (*label.sequence, task)
            new_mask = label.mask | bit
            if not _sortie_profile_mask_allowed_by_branch(new_mask, branch_constraints, task_to_bit):
                if catalog_stats is not None:
                    catalog_stats["branch_mask_pruned_sequences"] = int(
                        catalog_stats.get("branch_mask_pruned_sequences", 0)
                    ) + 1
                continue
            if superset_bound_cache is not None:
                superset_lb = superset_bound_cache.value(new_mask)
                if superset_lb is not None and superset_lb >= threshold:
                    if catalog_stats is not None:
                        catalog_stats["task_set_bound_pruned_sequences"] = int(
                            catalog_stats.get("task_set_bound_pruned_sequences", 0)
                        ) + 1
                    continue
            if resource_bound_cache is not None and not resource_bound_cache.maybe_feasible(new_mask):
                if catalog_stats is not None:
                    catalog_stats["task_set_resource_pruned_sequences"] = int(
                        catalog_stats.get("task_set_resource_pruned_sequences", 0)
                    ) + 1
                continue
            if not _sequence_resource_precheck(data, sequence):
                continue
            options = data.options(int(label.last), task)
            if not options:
                continue
            for option in options:
                if deadline is not None and time.perf_counter() > deadline:
                    _requeue_sortie_label_state(state, duals, label)
                    state.reason = "time_limit"
                    return
                extended = _extend_no_waiting_partial(data, sequence, len(label.sequence), label.partial, option)
                if extended is None:
                    continue
                state.generated += 1
                if int(config.max_sequences) > 0 and int(state.generated) > int(config.max_sequences):
                    _requeue_sortie_label_state(state, duals, label)
                    state.reason = "label_budget"
                    return
                new_label = _SortiePartialLabel(sequence=sequence, mask=new_mask, last=task, partial=extended)
                if partial_bound_cache is not None and partial_bound_cache.value(
                    new_label,
                    max_tasks - len(new_label.sequence),
                ) >= threshold:
                    if catalog_stats is not None:
                        catalog_stats["partial_profile_bound_pruned_labels"] = int(
                            catalog_stats.get("partial_profile_bound_pruned_labels", 0)
                        ) + 1
                    continue
                if not _add_sortie_partial_label(
                    state.labels_by_key.setdefault((new_mask, task), []),
                    new_label,
                    generalized=bool(config.generalized_partial_dominance_enabled),
                ):
                    continue
                state.serial += 1
                heapq.heappush(
                    state.heap,
                    (
                        _sortie_partial_label_priority(new_label, duals),
                        len(new_label.sequence),
                        round(float(new_label.partial.offset), 9),
                        tuple(int(item) for item in new_label.sequence),
                        int(state.serial),
                        new_label,
                    ),
                )
                cap_pruned_before = int((catalog_stats or {}).get("profile_mask_cap_pruned", 0))
                eval_inc, best_added_rc = _complete_sortie_label_profiles(
                    data,
                    duals,
                    new_label,
                    config,
                    state.profiles_by_key,
                    threshold,
                    task_to_bit,
                    profiles_by_mask=state.profiles_by_mask if online_dominance else None,
                    catalog_stats=catalog_stats,
                    profile_cap_per_mask=(
                        int(config.streaming_profile_cap_per_mask)
                        if stream_callback is not None and int(config.streaming_profile_cap_per_mask) > 0
                        else 0
                    ),
                )
                cap_pruned_after = int((catalog_stats or {}).get("profile_mask_cap_pruned", 0))
                if cap_pruned_after > cap_pruned_before:
                    state.profile_mask_cap_pruned += cap_pruned_after - cap_pruned_before
                state.evaluated += eval_inc
                if best_added_rc is not None:
                    state.best_profile_rc = (
                        best_added_rc if state.best_profile_rc is None else min(state.best_profile_rc, best_added_rc)
                    )
                current_profile_count = len(state.profiles_by_key)
                if stream_callback is not None and current_profile_count >= next_stream_profile_count:
                    if catalog_stats is not None:
                        catalog_stats["size"] = int(current_profile_count)
                        catalog_stats["label_resume_heap"] = len(state.heap)
                        catalog_stats["label_resume_profiles"] = len(_sortie_label_state_profiles(state, config))
                        catalog_stats["label_resume_exhausted"] = int(state.exhausted)
                    result = stream_callback(
                        _sortie_label_state_profiles(state, config),
                        int(state.generated),
                        int(state.evaluated),
                        state.best_profile_rc,
                        0,
                    )
                    next_stream_profile_count = current_profile_count + max(1, int(stream_profile_batch_size))
                    if result is not None:
                        raise _StreamingPricingStop(result)
                if int(config.max_candidate_trips) > 0 and current_profile_count > int(config.max_candidate_trips):
                    _requeue_sortie_label_state(state, duals, label)
                    state.reason = "candidate_profile_budget"
                    return
                if int(config.profile_catalog_max_profiles) > 0 and current_profile_count > int(config.profile_catalog_max_profiles):
                    _requeue_sortie_label_state(state, duals, label)
                    state.reason = "profile_catalog_budget"
                    return
                if int(config.max_timed_evaluations) > 0 and int(state.evaluated) > int(config.max_timed_evaluations):
                    _requeue_sortie_label_state(state, duals, label)
                    state.reason = "profile_evaluation_budget"
                    return
    if int(state.profile_mask_cap_pruned) > 0:
        state.exhausted = False
        state.reason = "profile_mask_cap_incomplete"
    else:
        state.exhausted = True
        state.reason = ""


def _requeue_sortie_label_state(
    state: _SortieLabelResumeState,
    duals: FutureDuals,
    label: _SortiePartialLabel,
) -> None:
    state.serial += 1
    heapq.heappush(
        state.heap,
        (
            _sortie_partial_label_priority(label, duals),
            len(label.sequence),
            round(float(label.partial.offset), 9),
            tuple(int(item) for item in label.sequence),
            int(state.serial),
            label,
        ),
    )


def _reprioritize_sortie_label_state(state: _SortieLabelResumeState, duals: FutureDuals) -> None:
    if not state.heap:
        return
    rebuilt: list[tuple[float, int, float, tuple[int, ...], int, _SortiePartialLabel]] = []
    for _priority, _depth, _offset, _seq_key, _serial, label in state.heap:
        state.serial += 1
        rebuilt.append(
            (
                _sortie_partial_label_priority(label, duals),
                len(label.sequence),
                round(float(label.partial.offset), 9),
                tuple(int(item) for item in label.sequence),
                int(state.serial),
                label,
            )
        )
    heapq.heapify(rebuilt)
    state.heap = rebuilt


def _sortie_partial_label_priority(label: _SortiePartialLabel, duals: FutureDuals) -> float:
    dual_sum = sum(float(duals.cover.get(int(task), 0.0)) for task in set(label.sequence))
    partial_cost = float(label.partial.travel_cost) + float(label.partial.service_cost)
    return round(partial_cost - dual_sum, 9)


def _filter_dominated_sortie_profiles(profiles: list[_SortieProfile]) -> tuple[list[_SortieProfile], int]:
    profiles, duplicate_pruned = _deduplicate_sortie_profiles_for_dominance(profiles)
    by_mask: dict[int, list[_SortieProfile]] = {}
    for profile in profiles:
        by_mask.setdefault(int(profile.mask), []).append(profile)
    kept: list[_SortieProfile] = []
    pruned = int(duplicate_pruned)
    for group in by_mask.values():
        skyline: list[_SortieProfile] = []
        for profile in sorted(group, key=_sortie_profile_sort_key):
            if any(_dominates_sortie_profile(old, profile) for old in skyline):
                pruned += 1
                continue
            survivors: list[_SortieProfile] = []
            for old in skyline:
                if _dominates_sortie_profile(profile, old):
                    pruned += 1
                    continue
                survivors.append(old)
            survivors.append(profile)
            skyline = survivors
        kept.extend(skyline)
    kept.sort(key=_sortie_profile_sort_key)
    return kept, pruned


def _add_sortie_profile_skyline(store: dict[int, list[_SortieProfile]], profile: _SortieProfile) -> tuple[bool, int]:
    group = store.setdefault(int(profile.mask), [])
    for old in group:
        if _dominates_sortie_profile(old, profile):
            return False, 0
    survivors: list[_SortieProfile] = []
    removed = 0
    for old in group:
        if _dominates_sortie_profile(profile, old):
            removed += 1
            continue
        survivors.append(old)
    survivors.append(profile)
    store[int(profile.mask)] = survivors
    return True, removed


def _deduplicate_sortie_profiles_for_dominance(profiles: list[_SortieProfile]) -> tuple[list[_SortieProfile], int]:
    best_by_resource: dict[tuple, _SortieProfile] = {}
    for profile in profiles:
        key = _sortie_profile_resource_key(profile)
        old = best_by_resource.get(key)
        if old is None or _sortie_profile_sort_key(profile) < _sortie_profile_sort_key(old):
            best_by_resource[key] = profile
    return list(best_by_resource.values()), max(0, len(profiles) - len(best_by_resource))


def _sortie_profile_resource_key(profile: _SortieProfile) -> tuple:
    return (
        int(profile.mask),
        round(float(profile.lower_start), 6),
        round(float(profile.upper_start), 6),
        round(float(profile.end_offset), 6),
    )


def _sortie_profile_sort_key(profile: _SortieProfile) -> tuple:
    return (
        int(profile.mask),
        round(float(profile.contribution), 9),
        round(float(profile.lower_start), 9),
        round(float(profile.end_offset), 9),
        round(-float(profile.upper_start), 9),
        tuple(int(task) for task in profile.sequence),
        tuple(option.option_id for option in profile.arc_options),
    )


def _dominates_sortie_profile(left: _SortieProfile, right: _SortieProfile) -> bool:
    if int(left.mask) != int(right.mask):
        return False
    no_worse = (
        float(left.contribution) <= float(right.contribution) + 1.0e-9
        and float(left.lower_start) <= float(right.lower_start) + 1.0e-9
        and float(left.upper_start) >= float(right.upper_start) - 1.0e-9
        and float(left.end_offset) <= float(right.end_offset) + 1.0e-9
    )
    strict = (
        float(left.contribution) < float(right.contribution) - 1.0e-9
        or float(left.lower_start) < float(right.lower_start) - 1.0e-9
        or float(left.upper_start) > float(right.upper_start) + 1.0e-9
        or float(left.end_offset) < float(right.end_offset) - 1.0e-9
    )
    return bool(no_worse and strict)


def _complete_sortie_label_profiles(
    data: FutureData,
    duals: FutureDuals,
    label: _SortiePartialLabel,
    config: JourneyPricingConfig,
    profiles_by_key: dict[tuple, _SortieProfile],
    threshold: float,
    task_to_bit: dict[int, int],
    profiles_by_mask: dict[int, list[_SortieProfile]] | None = None,
    catalog_stats: dict[str, int] | None = None,
    profile_cap_per_mask: int = 0,
) -> tuple[int, float | None]:
    evaluated = 0
    best_added_rc: float | None = None
    options = data.options(int(label.last), 0)
    if not options:
        return 0, None
    dual_sum = sum(float(duals.cover.get(int(task), 0.0)) for task in set(label.sequence))
    completion_cost_lb = float(label.partial.travel_cost) + float(label.partial.service_cost) + min(
        float(option.cost) for option in options
    )
    if completion_cost_lb - dual_sum >= float(threshold):
        return 0, None
    for option in options:
        base = _complete_no_waiting_partial(data, label.partial, option)
        if base is None:
            continue
        evaluated += 1
        profile = base.profile
        contribution = float(profile.cost) - dual_sum
        if contribution >= threshold:
            continue
        mask = 0
        for task in set(label.sequence):
            mask |= 1 << task_to_bit[int(task)]
        key = (
            tuple(int(task) for task in label.sequence),
            tuple(option.option_id for option in base.arc_options),
            round(float(profile.lower_start), 6),
            round(float(profile.upper_start), 6),
            round(float(profile.end_offset), 6),
        )
        candidate = _SortieProfile(
            sequence=tuple(int(task) for task in label.sequence),
            arc_options=base.arc_options,
            lower_start=float(profile.lower_start),
            upper_start=float(profile.upper_start),
            end_offset=float(profile.end_offset),
            cost=float(profile.cost),
            mask=mask,
            contribution=contribution,
        )
        if profiles_by_mask is not None:
            added, cap_pruned = _add_sortie_profile_online_skyline(
                profiles_by_key,
                profiles_by_mask,
                key,
                candidate,
                profile_cap_per_mask=profile_cap_per_mask,
            )
            if cap_pruned:
                if catalog_stats is not None:
                    catalog_stats["profile_mask_cap_pruned"] = int(
                        catalog_stats.get("profile_mask_cap_pruned", 0)
                    ) + 1
            if added:
                best_added_rc = candidate.contribution if best_added_rc is None else min(best_added_rc, candidate.contribution)
            continue
        old = profiles_by_key.get(key)
        if old is None or candidate.contribution < old.contribution - 1.0e-9:
            profiles_by_key[key] = candidate
            best_added_rc = candidate.contribution if best_added_rc is None else min(best_added_rc, candidate.contribution)
    return evaluated, best_added_rc


def _sortie_profile_key(profile: _SortieProfile) -> tuple:
    return (
        tuple(int(task) for task in profile.sequence),
        tuple(option.option_id for option in profile.arc_options),
        round(float(profile.lower_start), 6),
        round(float(profile.upper_start), 6),
        round(float(profile.end_offset), 6),
    )


def _add_sortie_profile_online_skyline(
    profiles_by_key: dict[tuple, _SortieProfile],
    profiles_by_mask: dict[int, list[_SortieProfile]],
    key: tuple,
    candidate: _SortieProfile,
    *,
    profile_cap_per_mask: int = 0,
) -> tuple[bool, bool]:
    group = profiles_by_mask.setdefault(int(candidate.mask), [])
    candidate_resource_key = _sortie_profile_resource_key(candidate)
    old_same_key = profiles_by_key.get(key)
    if old_same_key is not None:
        if _sortie_profile_sort_key(old_same_key) <= _sortie_profile_sort_key(candidate):
            return False, False
        profiles_by_key.pop(key, None)
    for old in group:
        if _sortie_profile_resource_key(old) == candidate_resource_key:
            if _sortie_profile_sort_key(old) <= _sortie_profile_sort_key(candidate):
                return False, False
            continue
        if _dominates_sortie_profile(old, candidate):
            return False, False
    survivors: list[_SortieProfile] = []
    for old in group:
        same_resource = _sortie_profile_resource_key(old) == candidate_resource_key
        if same_resource or _dominates_sortie_profile(candidate, old):
            profiles_by_key.pop(_sortie_profile_key(old), None)
            continue
        survivors.append(old)
    cap = int(profile_cap_per_mask)
    if cap > 0 and len(survivors) >= cap:
        if old_same_key is not None:
            profiles_by_key[key] = old_same_key
        return False, True
    survivors.append(candidate)
    profiles_by_mask[int(candidate.mask)] = survivors
    profiles_by_key[key] = candidate
    return True, False


def _add_sortie_partial_label(
    labels: list[_SortiePartialLabel],
    candidate: _SortiePartialLabel,
    *,
    generalized: bool = False,
) -> bool:
    for old in labels:
        if _dominates_sortie_partial_label(old, candidate, generalized=generalized):
            return False
    labels[:] = [
        old
        for old in labels
        if not _dominates_sortie_partial_label(candidate, old, generalized=generalized)
    ]
    labels.append(candidate)
    return True


def _dominates_sortie_partial_label(
    left: _SortiePartialLabel,
    right: _SortiePartialLabel,
    *,
    generalized: bool = False,
) -> bool:
    a = left.partial
    b = right.partial
    if bool(generalized):
        a_current_low = float(a.lower_start) + float(a.offset)
        a_current_high = float(a.upper_start) + float(a.offset)
        b_current_low = float(b.lower_start) + float(b.offset)
        b_current_high = float(b.upper_start) + float(b.offset)
        interval_no_worse = (
            a_current_low <= b_current_low + 1.0e-9
            and a_current_high >= b_current_high - 1.0e-9
            and float(a.offset) <= float(b.offset) + 1.0e-9
        )
        interval_strict = (
            a_current_low < b_current_low - 1.0e-9
            or a_current_high > b_current_high + 1.0e-9
            or float(a.offset) < float(b.offset) - 1.0e-9
        )
    else:
        interval_no_worse = (
            float(a.lower_start) <= float(b.lower_start) + 1.0e-9
            and float(a.upper_start) >= float(b.upper_start) - 1.0e-9
            and float(a.offset) <= float(b.offset) + 1.0e-9
        )
        interval_strict = (
            float(a.lower_start) < float(b.lower_start) - 1.0e-9
            or float(a.upper_start) > float(b.upper_start) + 1.0e-9
            or float(a.offset) < float(b.offset) - 1.0e-9
        )
    no_worse = (
        interval_no_worse
        and float(a.travel_cost) <= float(b.travel_cost) + 1.0e-9
        and float(a.travel_energy) <= float(b.travel_energy) + 1.0e-9
        and float(a.service_cost) <= float(b.service_cost) + 1.0e-9
        and float(a.service_energy) <= float(b.service_energy) + 1.0e-9
    )
    strict = (
        interval_strict
        or float(a.travel_cost) < float(b.travel_cost) - 1.0e-9
        or float(a.travel_energy) < float(b.travel_energy) - 1.0e-9
        or float(a.service_cost) < float(b.service_cost) - 1.0e-9
        or float(a.service_energy) < float(b.service_energy) - 1.0e-9
    )
    return bool(no_worse and strict)


def _solve_best_journey_profile_dp(
    data: FutureData,
    profiles: list[_SortieProfile],
    *,
    base_reduced_cost: float,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    max_states: int,
    deadline: float | None = None,
    max_returned: int = 1,
    early_return_negative: bool = False,
    early_return_min_count: int = 1,
    optimistic_bound_pruning: bool = True,
    cross_count_dominance: bool = True,
    selection_mode: str = "reduced_cost",
    dp_stats: dict[str, int] | None = None,
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    duplicate_scan_limit: int = 10000,
    dominant_task_set_cost_by_mask: dict[int, float] | None = None,
    pricing_config: JourneyPricingConfig | None = None,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
    eps: float = 1.0e-6,
) -> tuple[list[tuple[tuple[tuple[int, float], ...], float]], float | None, str]:
    cut_value_cache: dict[int, float] = {}
    early_candidates: list[tuple[float, tuple[tuple[int, float], ...], int]] = []
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    ordered = sorted(
        enumerate(profiles),
        key=lambda item: (item[1].upper_start + item[1].end_offset, item[1].lower_start, item[1].contribution, item[1].sequence),
    )
    ordered_records = tuple((position, profile_index, profile) for position, (profile_index, profile) in enumerate(ordered))
    compatible_profile_cache = _CompatibleProfileCache(ordered_records, task_count=len(data.tasks))
    optimistic_cache = _OptimisticProfileBoundCache(compatible_profile_cache)
    disjoint_cache = _DisjointProfileBoundCache(
        ordered_records,
        task_count=len(data.tasks),
        enabled=bool(optimistic_bound_pruning)
        and pricing_config is not None
        and bool(getattr(pricing_config, "dp_disjoint_bound_pruning_enabled", True))
        and len(data.tasks) <= int(getattr(pricing_config, "dp_disjoint_bound_max_tasks", 12)),
    )
    bound_pruning_safe = bool(optimistic_bound_pruning) and _profile_cut_penalty_pruning_safe(cut_duals, cuts)
    labels_by_count: list[dict[int, list[_JourneyLabel]]] = [dict() for _ in range(int(data.sortie_limit) + 1)]
    labels_by_count[0][0] = [_JourneyLabel(0.0, 0.0, tuple())]
    state_count = 1
    processed_labels = 0
    profile_record_scans = 0
    profile_time_filtered = 0
    extension_attempts = 0

    def record_dp_stats() -> None:
        if dp_stats is None:
            return
        dp_stats["processed_labels"] = int(processed_labels)
        dp_stats["state_count"] = int(state_count)
        dp_stats["profile_record_scans"] = int(profile_record_scans)
        dp_stats["profile_time_filtered"] = int(profile_time_filtered)
        dp_stats["extension_attempts"] = int(extension_attempts)

    for count in range(int(data.sortie_limit)):
        if deadline is not None and time.perf_counter() > deadline:
            record_dp_stats()
            return _collect_negative_journey_profile_labels(
                labels_by_count,
                data,
                profiles,
                base_reduced_cost,
                cut_duals,
                cuts,
                cut_masks,
                cut_value_cache,
                max_returned,
                selection_mode,
                forbidden_journey_signatures=forbidden_journey_signatures,
                duplicate_scan_limit=duplicate_scan_limit,
                dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
                pricing_config=pricing_config,
                branch_constraints=branch_constraints,
                dp_stats=dp_stats,
            )
        for mask, labels in list(labels_by_count[count].items()):
            if deadline is not None and time.perf_counter() > deadline:
                record_dp_stats()
                return _collect_negative_journey_profile_labels(
                    labels_by_count,
                    data,
                    profiles,
                    base_reduced_cost,
                    cut_duals,
                    cuts,
                    cut_masks,
                    cut_value_cache,
                    max_returned,
                    selection_mode,
                    forbidden_journey_signatures=forbidden_journey_signatures,
                    duplicate_scan_limit=duplicate_scan_limit,
                    dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
                    pricing_config=pricing_config,
                    branch_constraints=branch_constraints,
                    dp_stats=dp_stats,
                    status="INCOMPLETE",
                )
            for label in list(labels):
                processed_labels += 1
                if deadline is not None and time.perf_counter() > deadline:
                    record_dp_stats()
                    return _collect_negative_journey_profile_labels(
                        labels_by_count,
                        data,
                        profiles,
                        base_reduced_cost,
                        cut_duals,
                        cuts,
                        cut_masks,
                        cut_value_cache,
                        max_returned,
                        selection_mode,
                        forbidden_journey_signatures=forbidden_journey_signatures,
                        duplicate_scan_limit=duplicate_scan_limit,
                        dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
                        pricing_config=pricing_config,
                        branch_constraints=branch_constraints,
                        dp_stats=dp_stats,
                        status="INCOMPLETE",
                    )
                if bound_pruning_safe:
                    remaining = int(data.sortie_limit) - int(count)
                    disjoint_extra = disjoint_cache.value(int(mask), remaining)
                    if disjoint_extra is None:
                        optimistic_extra = optimistic_cache.value(int(mask), remaining)
                    else:
                        optimistic_extra = float(disjoint_extra)
                    lower_bound_objective = float(base_reduced_cost) + float(label.value) + float(optimistic_extra)
                    if lower_bound_objective >= -float(eps):
                        if dp_stats is not None:
                            dp_stats["bound_pruned_labels"] = int(dp_stats.get("bound_pruned_labels", 0)) + 1
                            if disjoint_extra is None:
                                pass
                            else:
                                dp_stats["disjoint_bound_pruned_labels"] = int(dp_stats.get("disjoint_bound_pruned_labels", 0)) + 1
                        continue
                all_candidate_count = None
                if dp_stats is not None:
                    all_candidate_count = len(compatible_profile_cache.records(mask))
                candidate_records = compatible_profile_cache.records(mask, min_upper_start=float(label.end_time))
                profile_record_scans += len(candidate_records)
                if all_candidate_count is not None:
                    profile_time_filtered += max(0, int(all_candidate_count) - len(candidate_records))
                for _position, profile_index, profile in candidate_records:
                    extension_attempts += 1
                    if deadline is not None and time.perf_counter() > deadline:
                        record_dp_stats()
                        return _collect_negative_journey_profile_labels(
                            labels_by_count,
                            data,
                            profiles,
                            base_reduced_cost,
                            cut_duals,
                            cuts,
                            cut_masks,
                            cut_value_cache,
                            max_returned,
                            selection_mode,
                            forbidden_journey_signatures=forbidden_journey_signatures,
                            duplicate_scan_limit=duplicate_scan_limit,
                            dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
                            pricing_config=pricing_config,
                            branch_constraints=branch_constraints,
                            dp_stats=dp_stats,
                            status="INCOMPLETE",
                        )
                    if compatible_profile_cache.requires_overlap_check and (mask & profile.mask):
                        continue
                    start = max(float(profile.lower_start), float(label.end_time))
                    if start > float(profile.upper_start) + 1.0e-9:
                        continue
                    new_end = start + float(profile.end_offset)
                    new_value = float(label.value) + float(profile.contribution)
                    new_selected = (*label.selected, (int(profile_index), round(start, 6)))
                    new_mask = mask | profile.mask
                    if not _journey_mask_branch_allowed(new_mask, branch_constraints, task_to_bit, final=False):
                        continue
                    remaining_slots = int(data.sortie_limit) - int(count) - 1
                    if bool(getattr(pricing_config, "dp_same_completion_pruning_enabled", False)) and not (
                        _journey_same_completion_possible(
                            new_mask,
                            new_end,
                            remaining_slots,
                            branch_constraints,
                            task_to_bit,
                            compatible_profile_cache,
                        )
                    ):
                        if dp_stats is not None:
                            dp_stats["same_completion_pruned_labels"] = int(
                                dp_stats.get("same_completion_pruned_labels", 0)
                            ) + 1
                        continue
                    candidate = _JourneyLabel(new_end, new_value, new_selected)
                    if bool(cross_count_dominance):
                        added = _add_profile_label_cross_count(labels_by_count, count + 1, new_mask, candidate, dp_stats)
                    else:
                        added = _add_profile_label(labels_by_count[count + 1], new_mask, candidate)
                    state_count += int(added)
                    if bool(early_return_negative) and added:
                        objective = (
                            float(base_reduced_cost)
                            + float(new_value)
                            - _journey_cut_dual_value_cached(int(new_mask), cut_duals, cuts, cut_masks, cut_value_cache)
                        )
                        if objective < -float(eps):
                            if not _journey_mask_branch_allowed(new_mask, branch_constraints, task_to_bit, final=True):
                                continue
                            if _profile_candidate_task_set_cost_dominated(
                                data,
                                profiles,
                                new_selected,
                                int(new_mask),
                                dominant_task_set_cost_by_mask,
                            ):
                                if dp_stats is not None:
                                    dp_stats["dominated_task_set_candidates_filtered"] = int(
                                        dp_stats.get("dominated_task_set_candidates_filtered", 0)
                                    ) + 1
                                continue
                            early_candidates.append((objective, new_selected, int(new_mask)))
                            if _early_return_candidate_count(early_candidates, pricing_config) >= max(1, int(early_return_min_count)):
                                early_candidates.sort(key=lambda item: (round(item[0], 9), len(item[1]), item[2], item[1]))
                                limited = _select_negative_journey_candidates(early_candidates, max_returned, selection_mode)
                                return [(selected, objective) for objective, selected, _mask in limited], early_candidates[0][0], "INCOMPLETE"
                    if max_states > 0 and state_count > int(max_states):
                        record_dp_stats()
                        return _collect_negative_journey_profile_labels(
                            labels_by_count,
                            data,
                            profiles,
                            base_reduced_cost,
                            cut_duals,
                            cuts,
                            cut_masks,
                            cut_value_cache,
                            max_returned,
                            selection_mode,
                            forbidden_journey_signatures=forbidden_journey_signatures,
                            duplicate_scan_limit=duplicate_scan_limit,
                            dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
                            pricing_config=pricing_config,
                            branch_constraints=branch_constraints,
                            dp_stats=dp_stats,
                            status="INCOMPLETE",
                        )
    record_dp_stats()
    return _collect_negative_journey_profile_labels(
        labels_by_count,
        data,
        profiles,
        base_reduced_cost,
        cut_duals,
        cuts,
        cut_masks,
        cut_value_cache,
        max_returned,
        selection_mode,
        forbidden_journey_signatures=forbidden_journey_signatures,
        duplicate_scan_limit=duplicate_scan_limit,
        dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
        pricing_config=pricing_config,
        branch_constraints=branch_constraints,
        dp_stats=dp_stats,
        status="OPTIMAL",
    )


def _collect_negative_journey_profile_labels(
    labels_by_count: list[dict[int, list[_JourneyLabel]]],
    data: FutureData,
    profiles: list[_SortieProfile],
    base_reduced_cost: float,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    cut_value_cache: dict[int, float],
    max_returned: int,
    selection_mode: str,
    *,
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    duplicate_scan_limit: int = 10000,
    dominant_task_set_cost_by_mask: dict[int, float] | None = None,
    pricing_config: JourneyPricingConfig | None = None,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
    dp_stats: dict[str, int] | None = None,
    status: str = "INCOMPLETE",
) -> tuple[list[tuple[tuple[tuple[int, float], ...], float]], float | None, str]:
    candidates: list[tuple[float, tuple[tuple[int, float], ...], int]] = []
    best_value: float | None = None
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    for labels_by_mask in labels_by_count[1:]:
        for mask, labels in labels_by_mask.items():
            if not _journey_mask_branch_allowed(int(mask), branch_constraints, task_to_bit, final=True):
                continue
            for label in labels:
                if not label.selected:
                    continue
                objective = (
                    float(base_reduced_cost)
                    + float(label.value)
                    - _journey_cut_dual_value_cached(int(mask), cut_duals, cuts, cut_masks, cut_value_cache)
                )
                if best_value is None or objective < best_value - 1.0e-9:
                    best_value = objective
                if objective < -1.0e-9:
                    candidates.append((objective, label.selected, int(mask)))
    limited, status = _select_nonduplicate_negative_journey_candidates(
        data,
        profiles,
        candidates,
        max_returned,
        selection_mode,
        forbidden_journey_signatures=forbidden_journey_signatures,
        duplicate_scan_limit=duplicate_scan_limit,
        dominant_task_set_cost_by_mask=dominant_task_set_cost_by_mask,
        pricing_config=pricing_config,
        dp_stats=dp_stats,
        status=status,
    )
    return [(selected, objective) for objective, selected, _mask in limited], best_value, status


def _journey_mask_branch_allowed(
    mask: int,
    constraints: tuple[BranchConstraint, ...],
    task_to_bit: dict[int, int],
    *,
    final: bool,
) -> bool:
    mask = int(mask)
    for constraint in constraints:
        if constraint.task_j is None:
            return False
        left_bit = task_to_bit.get(int(constraint.task_i))
        right_bit = task_to_bit.get(int(constraint.task_j))
        if left_bit is None or right_bit is None:
            continue
        left = bool(mask & (1 << int(left_bit)))
        right = bool(mask & (1 << int(right_bit)))
        if constraint.kind == "separate_vehicle":
            if left and right:
                return False
        elif constraint.kind == "same_vehicle":
            if bool(final) and left != right:
                return False
        else:
            return False
    return True


def _journey_same_completion_possible(
    mask: int,
    end_time: float,
    remaining_slots: int,
    constraints: tuple[BranchConstraint, ...],
    task_to_bit: dict[int, int],
    compatible_profile_cache: _CompatibleProfileCache,
) -> bool:
    """Return whether a partial journey can still satisfy same-vehicle rows.

    This is a one-sided exact-safe pruning test.  If a same-vehicle pair is
    currently split across the partial journey mask, the missing task must be
    present in at least one future sortie profile that can still be appended in
    time and without reusing already covered tasks.  If not, no completion of
    the partial label can satisfy the branch row.
    """

    mask = int(mask)
    if int(remaining_slots) <= 0:
        for constraint in constraints:
            if constraint.kind != "same_vehicle" or constraint.task_j is None:
                continue
            left_bit = task_to_bit.get(int(constraint.task_i))
            right_bit = task_to_bit.get(int(constraint.task_j))
            if left_bit is None or right_bit is None:
                continue
            if bool(mask & (1 << int(left_bit))) != bool(mask & (1 << int(right_bit))):
                return False
        return True

    missing_bits: set[int] = set()
    for constraint in constraints:
        if constraint.kind != "same_vehicle" or constraint.task_j is None:
            continue
        left_bit = task_to_bit.get(int(constraint.task_i))
        right_bit = task_to_bit.get(int(constraint.task_j))
        if left_bit is None or right_bit is None:
            continue
        left_mask = 1 << int(left_bit)
        right_mask = 1 << int(right_bit)
        left = bool(mask & left_mask)
        right = bool(mask & right_mask)
        if left and not right:
            missing_bits.add(right_mask)
        elif right and not left:
            missing_bits.add(left_mask)
    if not missing_bits:
        return True

    remaining = set(missing_bits)
    for _position, _profile_index, profile in compatible_profile_cache.records(mask, min_upper_start=float(end_time)):
        profile_mask = int(profile.mask)
        if profile_mask & mask:
            continue
        covered = {bit for bit in remaining if profile_mask & bit}
        if covered:
            remaining.difference_update(covered)
            if not remaining:
                return True
    return False


def _sortie_profile_mask_allowed_by_branch(
    mask: int,
    constraints: tuple[BranchConstraint, ...],
    task_to_bit: dict[int, int],
) -> bool:
    """Safe profile-level branch pruning.

    A separate-vehicle Ryan-Foster constraint forbids any final journey from
    containing both tasks, so a single sortie profile containing both can be
    discarded immediately.  Same-vehicle constraints are not applied here:
    a profile containing only one side may still be completed by another
    sortie in the same journey.
    """

    mask = int(mask)
    for constraint in constraints:
        if constraint.kind != "separate_vehicle" or constraint.task_j is None:
            continue
        left_bit = task_to_bit.get(int(constraint.task_i))
        right_bit = task_to_bit.get(int(constraint.task_j))
        if left_bit is None or right_bit is None:
            continue
        if (mask & (1 << int(left_bit))) and (mask & (1 << int(right_bit))):
            return False
    return True


def _branch_constraints_cache_key(constraints: tuple[BranchConstraint, ...]) -> tuple:
    return tuple(
        (
            str(constraint.kind),
            int(constraint.task_i),
            None if constraint.task_j is None else int(constraint.task_j),
            None if constraint.vehicle is None else int(constraint.vehicle),
        )
        for constraint in constraints
    )


def _early_return_candidate_count(
    candidates: list[tuple[float, tuple[tuple[int, float], ...], int]],
    pricing_config: JourneyPricingConfig | None,
) -> int:
    if pricing_config is not None and bool(getattr(pricing_config, "early_return_unique_masks_enabled", False)):
        return len({int(mask) for _objective, _selected, mask in candidates})
    return len(candidates)


def _select_negative_journey_candidates(
    candidates: list[tuple[float, tuple[tuple[int, float], ...], int]],
    max_returned: int,
    selection_mode: str,
) -> list[tuple[float, tuple[tuple[int, float], ...], int]]:
    if not candidates:
        return []
    limit = max(1, int(max_returned))
    ordered = sorted(candidates, key=lambda item: (round(item[0], 9), len(item[1]), item[2], item[1]))
    ordered = _best_negative_candidate_per_task_mask(ordered)
    mode = str(selection_mode)
    if mode not in {"diverse", "integer_diverse"} or len(ordered) <= limit:
        return ordered[:limit]
    if mode == "integer_diverse":
        return _select_integer_diverse_negative_journey_candidates(ordered, limit)

    selected: list[tuple[float, tuple[tuple[int, float], ...], int]] = []
    seen_masks: set[int] = set()

    def add(candidate: tuple[float, tuple[tuple[int, float], ...], int]) -> None:
        if len(selected) >= limit or candidate in selected:
            return
        selected.append(candidate)
        seen_masks.add(int(candidate[2]))

    for candidate in ordered[: max(1, limit // 2)]:
        add(candidate)
    for candidate in ordered:
        if int(candidate[2]) not in seen_masks:
            add(candidate)
        if len(selected) >= limit:
            break
    by_task_count_seen = {int(candidate[2]).bit_count() for candidate in selected}
    for candidate in ordered:
        task_count = int(candidate[2]).bit_count()
        if task_count not in by_task_count_seen:
            add(candidate)
            by_task_count_seen.add(task_count)
        if len(selected) >= limit:
            break
    for candidate in ordered:
        add(candidate)
        if len(selected) >= limit:
            break
    return selected


def _best_negative_candidate_per_task_mask(
    ordered: list[tuple[float, tuple[tuple[int, float], ...], int]]
) -> list[tuple[float, tuple[tuple[int, float], ...], int]]:
    """Keep only the best candidate for each final task set.

    Journey-master coefficients currently depend on the final task set, fleet
    count, and subset-row cuts.  For two candidates with the same final mask,
    the lower reduced-cost candidate has no larger journey cost and dominates
    the other for the current master.  Returning only this representative
    avoids feeding the RMP many equivalent schedule variants during degenerate
    tailing rounds.
    """

    best_by_mask: dict[int, tuple[float, tuple[tuple[int, float], ...], int]] = {}
    for candidate in ordered:
        mask = int(candidate[2])
        if mask not in best_by_mask:
            best_by_mask[mask] = candidate
    return sorted(best_by_mask.values(), key=lambda item: (round(item[0], 9), len(item[1]), item[2], item[1]))


def _select_integer_diverse_negative_journey_candidates(
    ordered: list[tuple[float, tuple[tuple[int, float], ...], int]],
    limit: int,
) -> list[tuple[float, tuple[tuple[int, float], ...], int]]:
    selected: list[tuple[float, tuple[tuple[int, float], ...], int]] = []
    seed_count = max(1, int(limit) // 3)
    seen_signatures: set[tuple] = set()

    def feature(candidate: tuple[float, tuple[tuple[int, float], ...], int]) -> tuple:
        _objective, selected_profiles, mask = candidate
        starts = tuple(round(float(start), 1) for _profile_index, start in selected_profiles)
        start_bucket = None if not starts else int(min(starts) // 60)
        return (
            int(mask),
            int(mask).bit_count(),
            len(selected_profiles),
            start_bucket,
        )

    def add(candidate: tuple[float, tuple[tuple[int, float], ...], int]) -> None:
        if len(selected) >= int(limit) or candidate in selected:
            return
        selected.append(candidate)
        seen_signatures.add(feature(candidate))

    for candidate in ordered[:seed_count]:
        add(candidate)
    for candidate in ordered:
        if feature(candidate) not in seen_signatures:
            add(candidate)
        if len(selected) >= int(limit):
            break

    seen_masks = {int(candidate[2]) for candidate in selected}
    for candidate in ordered:
        mask = int(candidate[2])
        if mask in seen_masks:
            continue
        add(candidate)
        seen_masks.add(mask)
        if len(selected) >= int(limit):
            break

    seen_sortie_counts = {len(candidate[1]) for candidate in selected}
    for candidate in ordered:
        count = len(candidate[1])
        if count in seen_sortie_counts:
            continue
        add(candidate)
        seen_sortie_counts.add(count)
        if len(selected) >= int(limit):
            break

    for candidate in ordered:
        add(candidate)
        if len(selected) >= int(limit):
            break
    return selected


def _select_nonduplicate_negative_journey_candidates(
    data: FutureData,
    profiles: list[_SortieProfile],
    candidates: list[tuple[float, tuple[tuple[int, float], ...], int]],
    max_returned: int,
    selection_mode: str,
    *,
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None,
    duplicate_scan_limit: int,
    dominant_task_set_cost_by_mask: dict[int, float] | None,
    pricing_config: JourneyPricingConfig | None,
    dp_stats: dict[str, int] | None,
    status: str,
) -> tuple[list[tuple[float, tuple[tuple[int, float], ...], int]], str]:
    if not candidates:
        return [], status
    forbidden = forbidden_journey_signatures or set()
    if not forbidden:
        return _select_negative_journey_candidates(candidates, max_returned, selection_mode), status

    ordered = _select_negative_journey_candidates(candidates, len(candidates), selection_mode)
    scan_limit = int(duplicate_scan_limit)
    if scan_limit <= 0:
        scan_limit = len(ordered)
    selected: list[tuple[float, tuple[tuple[int, float], ...], int]] = []
    scanned = 0
    filtered = 0
    limited = False
    for candidate in ordered:
        if scanned >= scan_limit:
            limited = True
            break
        scanned += 1
        _objective, selected_profiles, _mask = candidate
        if _profile_candidate_task_set_cost_dominated(
            data,
            profiles,
            selected_profiles,
            int(_mask),
            dominant_task_set_cost_by_mask,
        ):
            filtered += 1
            if dp_stats is not None:
                dp_stats["dominated_task_set_candidates_filtered"] = int(
                    dp_stats.get("dominated_task_set_candidates_filtered", 0)
                ) + 1
            continue
        signature = _selected_profile_journey_signature(data, profiles, selected_profiles, pricing_config)
        if signature in forbidden:
            filtered += 1
            continue
        selected.append(candidate)
        if len(selected) >= max(1, int(max_returned)):
            break
    if dp_stats is not None:
        dp_stats["duplicate_candidate_scan_count"] = int(dp_stats.get("duplicate_candidate_scan_count", 0)) + int(scanned)
        dp_stats["duplicate_candidates_filtered"] = int(dp_stats.get("duplicate_candidates_filtered", 0)) + int(filtered)
        if limited:
            dp_stats["duplicate_scan_limited"] = 1
    if limited and not selected:
        return [], "INCOMPLETE"
    return selected, status


def _dominant_task_set_costs_by_mask(
    data: FutureData,
    dominant_task_set_costs: dict[frozenset[int], float] | None,
) -> dict[int, float]:
    if not dominant_task_set_costs:
        return {}
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    result: dict[int, float] = {}
    for task_set, cost in dominant_task_set_costs.items():
        mask = 0
        valid = True
        for task in task_set:
            task = int(task)
            if task not in task_to_bit:
                valid = False
                break
            mask |= 1 << task_to_bit[task]
        if not valid or mask == 0:
            continue
        result[mask] = min(float(result.get(mask, float("inf"))), float(cost))
    return result


def _profile_candidate_task_set_cost_dominated(
    data: FutureData,
    profiles: list[_SortieProfile],
    selected: tuple[tuple[int, float], ...],
    mask: int,
    dominant_task_set_cost_by_mask: dict[int, float] | None,
) -> bool:
    if not dominant_task_set_cost_by_mask:
        return False
    incumbent_cost = dominant_task_set_cost_by_mask.get(int(mask))
    if incumbent_cost is None:
        return False
    candidate_cost = float(data.fixed_vehicle_cost)
    for profile_index, _start in selected:
        candidate_cost += float(profiles[int(profile_index)].cost)
    return bool(float(incumbent_cost) <= candidate_cost + 1.0e-9)


def _journey_task_set_cost_dominated(
    journey: JourneyColumn,
    dominant_task_set_costs: dict[frozenset[int], float] | None,
) -> bool:
    if not dominant_task_set_costs:
        return False
    key = frozenset(int(task) for task in journey.task_set)
    incumbent_cost = dominant_task_set_costs.get(key)
    return bool(incumbent_cost is not None and float(incumbent_cost) <= float(journey.cost) + 1.0e-9)


def _selected_profile_journey_signature(
    data: FutureData,
    profiles: list[_SortieProfile],
    selected: tuple[tuple[int, float], ...],
    pricing_config: JourneyPricingConfig | None,
) -> tuple[tuple[tuple[int, ...], tuple[str, ...], float], ...]:
    # This mirrors JourneyColumn.signature without building full TimedTrip
    # objects.  It keeps duplicate filtering inside the pricing oracle cheap.
    trip_keys: list[tuple[float, float, tuple[int, ...], tuple[str, ...], tuple[tuple[int, ...], tuple[str, ...], float]]] = []
    for profile_index, start in selected:
        profile = profiles[int(profile_index)]
        start_time = rounded(float(start))
        end_time = rounded(float(start) + float(profile.end_offset))
        arc_option_ids = tuple(option.option_id for option in profile.arc_options)
        trip_signature = (tuple(int(task) for task in profile.sequence), arc_option_ids, start_time)
        trip_keys.append((start_time, end_time, tuple(int(task) for task in profile.sequence), arc_option_ids, trip_signature))
    trip_keys.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
    return tuple(item[-1] for item in trip_keys)


def _journey_cut_dual_value_cached(
    mask: int,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    cache: dict[int, float],
) -> float:
    if int(mask) not in cache:
        cache[int(mask)] = _journey_cut_dual_value(int(mask), cut_duals, cuts, cut_masks)
    return cache[int(mask)]


def _profile_cut_penalty_pruning_safe(cut_duals: dict[int, float], cuts: tuple[FutureCut, ...]) -> bool:
    for cut_index, cut in enumerate(cuts):
        dual = float(cut_duals.get(int(cut_index), 0.0))
        if abs(dual) <= 1.0e-9:
            continue
        if getattr(cut, "kind", "") != "subset_row":
            return False
        if dual > 1.0e-9:
            return False
    return True


def _profile_cut_penalty(
    mask: int,
    cut_duals: dict[int, float],
    cuts: tuple[FutureCut, ...],
    cut_masks: tuple[int, ...],
    *,
    enabled: bool,
) -> float:
    if not enabled or not cut_duals or not cuts:
        return 0.0
    value = 0.0
    for cut_index, cut in enumerate(cuts):
        if getattr(cut, "kind", "") != "subset_row":
            continue
        dual = float(cut_duals.get(int(cut_index), 0.0))
        if dual >= -1.0e-12 or cut_index >= len(cut_masks):
            continue
        k = int(getattr(cut, "k", 2))
        overlap = (int(mask) & int(cut_masks[cut_index])).bit_count()
        value += -dual * float(overlap // k)
    return value


def _journey_cut_dual_value(mask: int, cut_duals: dict[int, float], cuts: tuple[FutureCut, ...], cut_masks: tuple[int, ...]) -> float:
    if not cut_duals or not cuts:
        return 0.0
    value = 0.0
    for cut_index, cut in enumerate(cuts):
        kind = getattr(cut, "kind", "")
        if kind in {"fleet_lower_bound", "fleet_upper_bound"}:
            if int(mask) != 0:
                value += float(cut_duals.get(int(cut_index), 0.0))
            continue
        if kind != "subset_row":
            continue
        k = int(getattr(cut, "k", 2))
        if cut_index >= len(cut_masks):
            continue
        overlap = (int(mask) & int(cut_masks[cut_index])).bit_count()
        value += float(cut_duals.get(int(cut_index), 0.0)) * float(overlap // k)
    return value


def _journey_pricing_cut_supported(cut: FutureCut) -> bool:
    return getattr(cut, "kind", "") in {"subset_row", "fleet_lower_bound", "fleet_upper_bound"}


def _cut_masks(data: FutureData, cuts: tuple[FutureCut, ...]) -> tuple[int, ...]:
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    return _cut_masks_from_task_bits(cuts, task_to_bit)


def _cut_masks_from_task_bits(cuts: tuple[FutureCut, ...], task_to_bit: dict[int, int]) -> tuple[int, ...]:
    masks: list[int] = []
    for cut in cuts:
        mask = 0
        if getattr(cut, "kind", "") == "subset_row":
            for task in getattr(cut, "tasks", tuple()):
                if int(task) in task_to_bit:
                    mask |= 1 << task_to_bit[int(task)]
        masks.append(mask)
    return tuple(masks)


def _add_profile_label(store: dict[int, list[_JourneyLabel]], mask: int, label: _JourneyLabel) -> bool:
    labels = store.setdefault(int(mask), [])
    for old in labels:
        if _dominates_journey_label(old, label):
            return False
    labels[:] = [
        old
        for old in labels
        if not _dominates_journey_label(label, old)
    ]
    labels.append(label)
    return True


def _add_profile_label_cross_count(
    labels_by_count: list[dict[int, list[_JourneyLabel]]],
    count: int,
    mask: int,
    label: _JourneyLabel,
    dp_stats: dict[str, int] | None,
) -> bool:
    mask = int(mask)
    count = int(count)
    for old_count in range(0, count + 1):
        for old in labels_by_count[old_count].get(mask, []):
            if _dominates_journey_label(old, label):
                if dp_stats is not None:
                    dp_stats["cross_count_pruned_labels"] = int(dp_stats.get("cross_count_pruned_labels", 0)) + 1
                return False

    removed = 0
    for old_count in range(count, len(labels_by_count)):
        labels = labels_by_count[old_count].get(mask)
        if not labels:
            continue
        survivors: list[_JourneyLabel] = []
        for old in labels:
            if _dominates_journey_label(label, old):
                removed += 1
                continue
            survivors.append(old)
        if survivors:
            labels_by_count[old_count][mask] = survivors
        else:
            labels_by_count[old_count].pop(mask, None)
    labels_by_count[count].setdefault(mask, []).append(label)
    if removed and dp_stats is not None:
        dp_stats["cross_count_pruned_labels"] = int(dp_stats.get("cross_count_pruned_labels", 0)) + int(removed)
    return True


def _dominates_journey_label(left: _JourneyLabel, right: _JourneyLabel) -> bool:
    return bool(
        float(left.end_time) <= float(right.end_time) + 1.0e-9
        and float(left.value) <= float(right.value) + 1.0e-9
    )


def _instantiate_profile_journey(
    data: FutureData,
    profiles: list[_SortieProfile],
    selected: tuple[tuple[int, float], ...],
    config: JourneyPricingConfig,
) -> list[TimedTrip]:
    trips: list[TimedTrip] = []
    for profile_index, start in selected:
        profile = profiles[int(profile_index)]
        trip = evaluate_timed_trip(
            data,
            profile.sequence,
            float(start),
            time_bucket_size=float(config.time_bucket_size),
            arc_options=profile.arc_options,
            include_physical_paths=False,
        )
        if trip is None:
            return []
        trips.append(trip)
    trips.sort(key=lambda trip: (trip.start_time, trip.end_time, trip.tasks, trip.arc_option_ids))
    return trips


def _instantiate_profile_journey_candidates(
    data: FutureData,
    profiles: list[_SortieProfile],
    selected_candidates: list[tuple[tuple[tuple[int, float], ...], float]],
    config: JourneyPricingConfig,
    *,
    eps: float,
    forbidden_journey_signatures: set[tuple] | frozenset[tuple] | None = None,
    dominant_task_set_costs: dict[frozenset[int], float] | None = None,
    max_journeys: int | None = None,
    branch_constraints: tuple[BranchConstraint, ...] = tuple(),
) -> tuple[list[JourneyColumn], int, int]:
    journeys: list[JourneyColumn] = []
    seen: set[tuple] = set()
    seen_task_sets: set[frozenset[int]] = set()
    forbidden = forbidden_journey_signatures or set()
    existing_filtered = 0
    weak_negative_filtered = 0
    add_threshold = max(float(eps), float(config.min_add_reduced_cost))
    for selected, objective in selected_candidates:
        if objective >= -float(eps):
            continue
        if objective >= -add_threshold:
            weak_negative_filtered += 1
            continue
        trips = _instantiate_profile_journey(data, profiles, selected, config)
        journey = make_journey(data, trips)
        if journey is None or journey.signature in seen:
            continue
        if not _journey_task_set_branch_allowed(journey.task_set, branch_constraints):
            existing_filtered += 1
            continue
        task_set_key = frozenset(int(task) for task in journey.task_set)
        if task_set_key in seen_task_sets:
            existing_filtered += 1
            continue
        if journey.signature in forbidden:
            existing_filtered += 1
            continue
        if _journey_task_set_cost_dominated(journey, dominant_task_set_costs):
            existing_filtered += 1
            continue
        seen.add(journey.signature)
        seen_task_sets.add(task_set_key)
        journeys.append(journey)
        if max_journeys is not None and len(journeys) >= int(max_journeys):
            break
    return journeys, existing_filtered, weak_negative_filtered


def _journey_task_set_branch_allowed(task_set: frozenset[int] | set[int], constraints: tuple[BranchConstraint, ...]) -> bool:
    tasks = {int(task) for task in task_set}
    for constraint in constraints:
        if constraint.task_j is None:
            return False
        left = int(constraint.task_i) in tasks
        right = int(constraint.task_j) in tasks
        if constraint.kind == "separate_vehicle" and left and right:
            return False
        if constraint.kind == "same_vehicle" and left != right:
            return False
        if constraint.kind not in {"same_vehicle", "separate_vehicle"}:
            return False
    return True


def _solve_best_journey_selection_dp(
    data: FutureData,
    trips: list[TimedTrip],
    duals: FutureDuals,
    *,
    base_reduced_cost: float,
    max_states: int,
) -> tuple[list[TimedTrip], float | None, str]:
    task_to_bit = {int(task): index for index, task in enumerate(data.tasks)}
    if len(task_to_bit) > 62:
        return [], None, "INCOMPLETE"
    prepared: list[tuple[float, TimedTrip, int, float]] = []
    vehicle = int(data.vehicles[0])
    for trip in trips:
        mask = 0
        for task in trip.task_set:
            mask |= 1 << task_to_bit[int(task)]
        contribution = manual_reduced_cost(trip, vehicle, duals, tuple(), phase="phase2")
        prepared.append((float(trip.end_time), trip, mask, float(contribution)))
    prepared.sort(key=lambda item: (item[0], item[1].start_time, item[3], item[1].signature))

    states: dict[tuple[int, int], tuple[float, tuple[int, ...]]] = {(0, 0): (0.0, tuple())}
    snapshot_ends = [float("-inf")]
    snapshots: list[dict[tuple[int, int], tuple[float, tuple[int, ...]]]] = [dict(states)]
    index_by_signature = {trip.signature: index for index, (_end, trip, _mask, _contribution) in enumerate(prepared)}

    position = 0
    while position < len(prepared):
        end_time = prepared[position][0]
        group: list[tuple[TimedTrip, int, float]] = []
        while position < len(prepared) and abs(prepared[position][0] - end_time) <= 1.0e-9:
            _end, trip, mask, contribution = prepared[position]
            group.append((trip, mask, contribution))
            position += 1
        updates: dict[tuple[int, int], tuple[float, tuple[int, ...]]] = {}
        for trip, trip_mask, contribution in group:
            pred = bisect.bisect_right(snapshot_ends, float(trip.start_time) + 1.0e-9) - 1
            base_states = snapshots[max(0, pred)]
            trip_index = index_by_signature[trip.signature]
            for (mask, count), (value, selected) in base_states.items():
                if count >= int(data.sortie_limit):
                    continue
                if mask & trip_mask:
                    continue
                new_key = (mask | trip_mask, count + 1)
                new_value = value + contribution
                old = updates.get(new_key)
                if old is None or new_value < old[0] - 1.0e-9:
                    updates[new_key] = (new_value, (*selected, trip_index))
        for key, candidate in updates.items():
            old = states.get(key)
            if old is None or candidate[0] < old[0] - 1.0e-9:
                states[key] = candidate
        if max_states > 0 and len(states) > int(max_states):
            return [], None, "INCOMPLETE"
        snapshot_ends.append(float(end_time))
        snapshots.append(dict(states))

    best_value: float | None = None
    best_selected: tuple[int, ...] = tuple()
    for (mask, count), (value, selected) in states.items():
        if mask == 0 or count == 0:
            continue
        objective = float(base_reduced_cost) + float(value)
        if best_value is None or objective < best_value - 1.0e-9:
            best_value = objective
            best_selected = selected
    if best_value is None:
        return [], None, "OPTIMAL"
    selected_trips = [prepared[index][1] for index in best_selected]
    selected_trips.sort(key=lambda trip: (trip.start_time, trip.end_time, trip.tasks, trip.arc_option_ids))
    return selected_trips, best_value, "OPTIMAL"


def _solve_best_journey_selection(
    data: FutureData,
    trips: list[TimedTrip],
    duals: FutureDuals,
    *,
    base_reduced_cost: float,
    time_limit: float,
) -> tuple[list[TimedTrip], float | None, str]:
    from pyscipopt import Model, quicksum

    model = Model(f"bpc_future_journey_pricing_{data.name}")
    _try_set_param(model, "display/verblevel", 0)
    _try_set_param(model, "parallel/maxnthreads", 1)
    if time_limit > 0.0:
        _try_set_param(model, "limits/time", float(time_limit))
    z = {
        index: model.addVar(
            vtype="B",
            obj=float(manual_reduced_cost(trip, int(data.vehicles[0]), duals, tuple(), phase="phase2")),
            name=f"z_trip[{index}]",
        )
        for index, trip in enumerate(trips)
    }
    for task in data.tasks:
        terms = [var for index, var in z.items() if int(task) in trips[index].task_set]
        if terms:
            model.addCons(quicksum(terms) <= 1.0, name=f"task_once[{task}]")
    model.addCons(quicksum(z.values()) >= 1.0, name="nonempty_journey")
    model.addCons(quicksum(z.values()) <= float(data.sortie_limit), name="sortie_limit")
    for point_index, point in enumerate(_interval_clique_points(trips)):
        terms = [
            var
            for index, var in z.items()
            if trips[index].start_time <= point + 1.0e-9 and point < trips[index].end_time - 1.0e-9
        ]
        if len(terms) > 1:
            model.addCons(quicksum(terms) <= 1.0, name=f"time_clique[{point_index}]")
    model.addVar(vtype="C", lb=1.0, ub=1.0, obj=float(base_reduced_cost), name="journey_base")
    model.optimize()
    status = _status_name(model.getStatus())
    if model.getNSols() <= 0:
        return [], None, status
    sol = model.getBestSol()
    selected = [
        trips[index]
        for index, var in z.items()
        if float(model.getSolVal(sol, var)) > 0.5
    ]
    selected.sort(key=lambda trip: (trip.start_time, trip.end_time, trip.tasks, trip.arc_option_ids))
    return selected, float(model.getSolObjVal(sol)), status


def _interval_clique_points(trips: list[TimedTrip]) -> tuple[float, ...]:
    endpoints = sorted(
        {
            round(float(trip.start_time), 6)
            for trip in trips
        }
        | {
            round(float(trip.end_time), 6)
            for trip in trips
        }
    )
    points: set[float] = set()
    for left, right in zip(endpoints[:-1], endpoints[1:]):
        if right > left + 1.0e-9:
            points.add(round((left + right) / 2.0, 6))
    return tuple(sorted(points))


def _try_set_param(model: Any, name: str, value: Any) -> None:
    try:
        model.setParam(name, value)
    except Exception:
        pass


def _status_name(status: Any) -> str:
    text = str(status).lower()
    mapping = {
        "optimal": "OPTIMAL",
        "infeasible": "INFEASIBLE",
        "unbounded": "UNBOUNDED",
        "inforunbd": "INF_OR_UNBD",
        "timelimit": "TIME_LIMIT",
    }
    return mapping.get(text, text.upper())
