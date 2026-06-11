"""Available-mask completion lower bound for exact journey final judges.

AMCB is an opt-in optimistic reduced-cost lower bound.  It keeps task memory
through available masks, so each task-cover dual can be used at most once, and
uses scalar dynamic programs instead of resource Pareto fronts.  Resource
checks are only optimistic filters; if the bound cannot be computed within its
budget it returns no bound.
"""

from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
import time
from typing import Any

from BPC_future.core.data import FutureData


@dataclass(frozen=True)
class AMCBQueryResult:
    value: float | None = None
    disabled: bool = False


class _AMCBDisabled(Exception):
    pass


class AvailableMaskCompletionBound:
    """Task-memory scalar completion lower bound.

    The lower bound relaxes time windows and physical coupling by using
    cheapest directed arc costs, while retaining task-set disjointness through
    ``available_mask``.  It is therefore optimistic for exact completion.
    """

    def __init__(
        self,
        data: FutureData,
        duals: Any,
        task_to_bit: dict[int, int],
        *,
        max_tasks_per_sortie: int,
        sortie_limit: int,
        max_subset_size: int | None = None,
        max_states: int = 0,
        deadline: float | None = None,
    ) -> None:
        started = time.perf_counter()
        self.data = data
        self.duals = duals
        self.task_to_bit = {int(task): int(bit) for task, bit in task_to_bit.items()}
        self.task_by_bit = {int(bit): int(task) for task, bit in self.task_to_bit.items()}
        self.tasks = tuple(int(task) for task in data.tasks if int(task) in self.task_to_bit)
        self.full_mask = 0
        for task in self.tasks:
            self.full_mask |= 1 << int(self.task_to_bit[int(task)])
        self.max_tasks_per_sortie = max(1, int(max_tasks_per_sortie))
        subset_limit = self.max_tasks_per_sortie if max_subset_size is None else int(max_subset_size)
        self._subset_budget_safe = int(subset_limit) >= min(self.max_tasks_per_sortie, len(self.tasks))
        self.max_subset_size = max(0, min(self.max_tasks_per_sortie, subset_limit, len(self.tasks)))
        self.sortie_limit = max(0, int(sortie_limit))
        self.max_states = max(0, int(max_states))
        self.deadline = None if deadline is None else float(deadline)
        self.capacity = max(0.0, float(data.capacity))
        self.energy_limit = max(0.0, float(data.energy_limit))
        self.horizon = max(0.0, float(data.horizon))
        self.rho = max(1.0e-9, float(data.rho))
        self.survival_energy_rate = max(0.0, float(data.survival_energy_rate))
        self.task_reward = {int(task): float(getattr(duals, "cover", {}).get(int(task), 0.0)) for task in self.tasks}
        self.service_cost = {int(task): float(data.task_value(int(task), "c_srv")) for task in self.tasks}
        self.service_energy = {int(task): float(data.task_value(int(task), "g")) for task in self.tasks}
        self.service_time = {int(task): float(data.task_value(int(task), "sigma")) for task in self.tasks}
        self.task_load = {int(task): float(data.task_value(int(task), "d")) for task in self.tasks}
        self._arc_cost_cache: dict[tuple[int, int], float] = {}
        self._arc_energy_cache: dict[tuple[int, int], float] = {}
        self._arc_time_cache: dict[tuple[int, int], float] = {}
        self._open_cache: dict[tuple[int, int], float] = {}
        self._closed_cache: dict[int, float] = {}
        self._tail_cache: dict[tuple[int, int], float] = {}
        self._load_cache: dict[int, float] = {}
        self._service_energy_cache: dict[int, float] = {}
        self._service_time_cache: dict[int, float] = {}
        self._travel_energy_cache: dict[tuple[int, int], float] = {}
        self._travel_time_cache: dict[tuple[int, int], float] = {}
        self._candidate_subsets = self._build_candidate_subsets()
        self.query_count = 0
        self.disabled = not bool(self._subset_budget_safe)
        self.disable_reason: str | None = (
            None if self._subset_budget_safe else "subset_budget_below_sortie_capacity"
        )
        self.resource_filtered_subsets = 0
        self.closed_subset_count = 0
        self.tail_state_count = 0
        self.build_time = time.perf_counter() - started

    @property
    def enabled(self) -> bool:
        return not bool(self.disabled)

    @property
    def state_count(self) -> int:
        return (
            len(self._open_cache)
            + len(self._closed_cache)
            + len(self._tail_cache)
            + len(self._travel_energy_cache)
            + len(self._travel_time_cache)
        )

    def stats(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "build_time": float(self.build_time),
            "closed_subset_count": int(self.closed_subset_count),
            "tail_state_count": int(self.tail_state_count),
            "query_count": int(self.query_count),
            "state_count": int(self.state_count),
            "disabled": bool(self.disabled),
            "disable_reason": self.disable_reason,
            "resource_filtered_subsets": int(self.resource_filtered_subsets),
        }

    def lower_bound_for_partial(
        self,
        *,
        last: int,
        available_mask: int,
        remaining_slots_current_sortie: int,
        remaining_sorties_after_current: int,
        remaining_capacity: float | None = None,
        remaining_energy: float | None = None,
        remaining_occupation: float | None = None,
    ) -> AMCBQueryResult:
        self.query_count += 1
        if self.disabled:
            return AMCBQueryResult(disabled=True)
        try:
            available = int(available_mask) & int(self.full_mask)
            slots = max(0, min(int(remaining_slots_current_sortie), int(self.max_subset_size)))
            future_sorties = max(0, int(remaining_sorties_after_current))
            best: float | None = None
            for subset in self._subsets_of(available, slots, include_empty=True):
                if not self._resource_maybe_feasible_open(
                    int(last),
                    int(subset),
                    remaining_capacity=remaining_capacity,
                    remaining_energy=remaining_energy,
                    remaining_occupation=remaining_occupation,
                ):
                    self.resource_filtered_subsets += 1
                    continue
                open_value = self._open_value(int(last), int(subset))
                tail_value = self._tail_value(int(future_sorties), int(available) ^ int(subset))
                if math.isinf(float(open_value)) or math.isinf(float(tail_value)):
                    continue
                value = float(open_value) + float(tail_value)
                best = value if best is None else min(float(best), float(value))
            return AMCBQueryResult(value=best)
        except _AMCBDisabled:
            return AMCBQueryResult(disabled=True)

    def lower_bound_for_suffix(
        self,
        *,
        available_mask: int,
        remaining_sorties: int,
    ) -> AMCBQueryResult:
        self.query_count += 1
        if self.disabled:
            return AMCBQueryResult(disabled=True)
        try:
            value = self._tail_value(max(0, int(remaining_sorties)), int(available_mask) & int(self.full_mask))
            if math.isinf(float(value)):
                return AMCBQueryResult(value=None)
            return AMCBQueryResult(value=float(value))
        except _AMCBDisabled:
            return AMCBQueryResult(disabled=True)

    def _build_candidate_subsets(self) -> tuple[int, ...]:
        bits = tuple(1 << int(self.task_to_bit[int(task)]) for task in self.tasks)
        masks: list[int] = []
        for size in range(1, int(self.max_subset_size) + 1):
            for combo in itertools.combinations(bits, size):
                mask = 0
                for bit in combo:
                    mask |= int(bit)
                masks.append(mask)
        return tuple(masks)

    def _subsets_of(self, mask: int, max_size: int, *, include_empty: bool) -> tuple[int, ...] | list[int]:
        allowed = int(mask)
        limit = max(0, int(max_size))
        values: list[int] = [0] if include_empty else []
        for subset in self._candidate_subsets:
            if int(subset) & ~allowed:
                continue
            if int(subset).bit_count() <= limit:
                values.append(int(subset))
        return values

    def _ensure_budget(self) -> None:
        if self.max_states <= 0:
            return
        if self.state_count >= int(self.max_states):
            self.disabled = True
            self.disable_reason = "state_budget"
            raise _AMCBDisabled
        if self.deadline is not None and time.perf_counter() > float(self.deadline):
            self.disabled = True
            self.disable_reason = "deadline"
            raise _AMCBDisabled

    def _arc_rc_lb(self, origin: int, destination: int) -> float:
        key = (int(origin), int(destination))
        cached = self._arc_cost_cache.get(key)
        if cached is not None:
            return cached
        try:
            options = self.data.options(int(origin), int(destination))
        except KeyError:
            options = tuple()
        if not options:
            value = 0.0 if int(origin) == 0 and int(destination) == 0 else float("inf")
        else:
            value = min(float(option.cost) for option in options)
            if int(destination) in self.task_to_bit:
                value += float(self.service_cost[int(destination)]) - float(self.task_reward[int(destination)])
        self._arc_cost_cache[key] = float(value)
        return float(value)

    def _arc_energy_lb(self, origin: int, destination: int) -> float:
        key = (int(origin), int(destination))
        cached = self._arc_energy_cache.get(key)
        if cached is not None:
            return cached
        try:
            options = self.data.options(int(origin), int(destination))
        except KeyError:
            options = tuple()
        value = 0.0 if int(origin) == 0 and int(destination) == 0 else float("inf")
        if options:
            value = min(float(option.energy) for option in options)
        self._arc_energy_cache[key] = float(value)
        return float(value)

    def _arc_time_lb(self, origin: int, destination: int) -> float:
        key = (int(origin), int(destination))
        cached = self._arc_time_cache.get(key)
        if cached is not None:
            return cached
        try:
            options = self.data.options(int(origin), int(destination))
        except KeyError:
            options = tuple()
        value = 0.0 if int(origin) == 0 and int(destination) == 0 else float("inf")
        if options:
            value = min(float(option.tau) for option in options)
        self._arc_time_cache[key] = float(value)
        return float(value)

    def _open_value(self, last: int, subset: int) -> float:
        key = (int(last), int(subset))
        cached = self._open_cache.get(key)
        if cached is not None:
            return cached
        self._ensure_budget()
        if int(subset) == 0:
            value = self._arc_rc_lb(int(last), 0)
        else:
            value = float("inf")
            remaining = int(subset)
            while remaining:
                bit = remaining & -remaining
                task = self.task_by_bit[bit.bit_length() - 1]
                arc = self._arc_rc_lb(int(last), int(task))
                if not math.isinf(float(arc)):
                    tail = self._open_value(int(task), int(subset) ^ int(bit))
                    if not math.isinf(float(tail)):
                        value = min(float(value), float(arc) + float(tail))
                remaining ^= bit
        self._open_cache[key] = float(value)
        return float(value)

    def _closed_value(self, subset: int) -> float:
        subset = int(subset)
        cached = self._closed_cache.get(subset)
        if cached is not None:
            return cached
        self._ensure_budget()
        value = 0.0 if subset == 0 else self._open_value(0, subset)
        self._closed_cache[subset] = float(value)
        self.closed_subset_count = len(self._closed_cache)
        return float(value)

    def _tail_value(self, sorties: int, available_mask: int) -> float:
        key = (max(0, int(sorties)), int(available_mask) & int(self.full_mask))
        cached = self._tail_cache.get(key)
        if cached is not None:
            return cached
        self._ensure_budget()
        sorties, available = key
        best = 0.0
        if int(sorties) > 0 and int(available) > 0:
            for subset in self._subsets_of(available, self.max_subset_size, include_empty=False):
                if not self._resource_maybe_feasible_closed(int(subset)):
                    self.resource_filtered_subsets += 1
                    continue
                closed = self._closed_value(int(subset))
                if math.isinf(float(closed)):
                    continue
                tail = self._tail_value(int(sorties) - 1, int(available) ^ int(subset))
                if math.isinf(float(tail)):
                    continue
                best = min(float(best), float(closed) + float(tail))
        self._tail_cache[key] = float(best)
        self.tail_state_count = len(self._tail_cache)
        return float(best)

    def _mask_load(self, mask: int) -> float:
        cached = self._load_cache.get(int(mask))
        if cached is not None:
            return cached
        total = 0.0
        remaining = int(mask)
        while remaining:
            bit = remaining & -remaining
            task = self.task_by_bit[bit.bit_length() - 1]
            total += float(self.task_load[int(task)])
            remaining ^= bit
        self._load_cache[int(mask)] = float(total)
        return float(total)

    def _mask_service_energy(self, mask: int) -> float:
        cached = self._service_energy_cache.get(int(mask))
        if cached is not None:
            return cached
        total = 0.0
        remaining = int(mask)
        while remaining:
            bit = remaining & -remaining
            task = self.task_by_bit[bit.bit_length() - 1]
            total += float(self.service_energy[int(task)])
            remaining ^= bit
        self._service_energy_cache[int(mask)] = float(total)
        return float(total)

    def _mask_service_time(self, mask: int) -> float:
        cached = self._service_time_cache.get(int(mask))
        if cached is not None:
            return cached
        total = 0.0
        remaining = int(mask)
        while remaining:
            bit = remaining & -remaining
            task = self.task_by_bit[bit.bit_length() - 1]
            total += float(self.service_time[int(task)])
            remaining ^= bit
        self._service_time_cache[int(mask)] = float(total)
        return float(total)

    def _travel_energy_lb(self, last: int, mask: int) -> float:
        key = (int(last), int(mask))
        cached = self._travel_energy_cache.get(key)
        if cached is not None:
            return cached
        self._ensure_budget()
        if int(mask) == 0:
            value = self._arc_energy_lb(int(last), 0)
        else:
            value = float("inf")
            remaining = int(mask)
            while remaining:
                bit = remaining & -remaining
                task = self.task_by_bit[bit.bit_length() - 1]
                arc = self._arc_energy_lb(int(last), int(task))
                tail = self._travel_energy_lb(int(task), int(mask) ^ int(bit))
                if not math.isinf(float(arc)) and not math.isinf(float(tail)):
                    value = min(float(value), float(arc) + float(tail))
                remaining ^= bit
        self._travel_energy_cache[key] = float(value)
        return float(value)

    def _travel_time_lb(self, last: int, mask: int) -> float:
        key = (int(last), int(mask))
        cached = self._travel_time_cache.get(key)
        if cached is not None:
            return cached
        self._ensure_budget()
        if int(mask) == 0:
            value = self._arc_time_lb(int(last), 0)
        else:
            value = float("inf")
            remaining = int(mask)
            while remaining:
                bit = remaining & -remaining
                task = self.task_by_bit[bit.bit_length() - 1]
                arc = self._arc_time_lb(int(last), int(task))
                tail = self._travel_time_lb(int(task), int(mask) ^ int(bit))
                if not math.isinf(float(arc)) and not math.isinf(float(tail)):
                    value = min(
                        float(value),
                        float(arc) + float(self.service_time[int(task)]) + float(tail),
                    )
                remaining ^= bit
        self._travel_time_cache[key] = float(value)
        return float(value)

    def _resource_maybe_feasible_open(
        self,
        last: int,
        subset: int,
        *,
        remaining_capacity: float | None,
        remaining_energy: float | None,
        remaining_occupation: float | None,
    ) -> bool:
        if int(subset) == 0:
            return True
        capacity = self.capacity if remaining_capacity is None else float(remaining_capacity)
        energy_limit = self.energy_limit if remaining_energy is None else float(remaining_energy)
        occupation = self.horizon if remaining_occupation is None else float(remaining_occupation)
        return self._resource_maybe_feasible(
            int(last),
            int(subset),
            capacity_limit=float(capacity),
            energy_limit=float(energy_limit),
            occupation_limit=float(occupation),
        )

    def _resource_maybe_feasible_closed(self, subset: int) -> bool:
        return self._resource_maybe_feasible(
            0,
            int(subset),
            capacity_limit=float(self.capacity),
            energy_limit=float(self.energy_limit),
            occupation_limit=float(self.horizon),
        )

    def _resource_maybe_feasible(
        self,
        last: int,
        subset: int,
        *,
        capacity_limit: float,
        energy_limit: float,
        occupation_limit: float,
    ) -> bool:
        if int(subset) == 0:
            return True
        load = self._mask_load(int(subset))
        if float(load) > float(capacity_limit) + 1.0e-9:
            return False
        travel_energy = self._travel_energy_lb(int(last), int(subset))
        travel_time = self._travel_time_lb(int(last), int(subset))
        if math.isinf(float(travel_energy)) or math.isinf(float(travel_time)):
            return False
        total_energy = (
            float(travel_energy)
            + self._mask_service_energy(int(subset))
            + float(self.survival_energy_rate) * float(travel_time)
        )
        if total_energy > float(energy_limit) + 1.0e-9:
            return False
        recharge = float(total_energy) / float(self.rho)
        return float(travel_time) + float(recharge) <= float(occupation_limit) + 1.0e-9
