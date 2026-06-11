"""Resource-Pareto completion envelope for exact journey final judges.

The envelope is an opt-in optimistic lower bound for direct-label completion
checks.  It deliberately relaxes task uniqueness and task time windows, uses
only task-cover duals, and disables overflowing states instead of truncating
fronts.  Disabled states return no bound, so they can only reduce pruning.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import Any

import numpy as np

from BPC_future.core.data import FutureData


_RC = 0
_ENERGY = 1
_LOAD = 2
_OCCUPATION = 3
_FRONT_DIM = 4
_ZERO_FRONT = np.zeros((1, _FRONT_DIM), dtype=float)
_EMPTY_FRONT = np.empty((0, _FRONT_DIM), dtype=float)


@dataclass(frozen=True)
class ParetoQueryResult:
    value: float | None = None
    infeasible: bool = False
    disabled: bool = False


def _quantized_rc(values: np.ndarray, rc_eps: float) -> np.ndarray:
    if float(rc_eps) <= 0.0:
        return values.astype(float, copy=True)
    step = float(rc_eps)
    return np.floor(values.astype(float, copy=False) / step) * step


def _resource_compare_values(values: np.ndarray, resource_eps: np.ndarray) -> np.ndarray:
    compare = values.astype(float, copy=True)
    for index, eps in enumerate(resource_eps, start=_ENERGY):
        if float(eps) > 0.0:
            compare[:, index] = np.floor(compare[:, index] / float(eps) + 1.0e-12)
    return compare


def _quantize_resources_down(values: np.ndarray, resource_eps: np.ndarray) -> np.ndarray:
    result = values.astype(float, copy=True)
    for index, eps in enumerate(resource_eps, start=_ENERGY):
        if float(eps) > 0.0:
            step = float(eps)
            result[:, index] = np.floor(result[:, index] / step + 1.0e-12) * step
    return result


def filter_pareto_vectors(
    vectors: np.ndarray,
    *,
    rc_eps: float = 0.0,
    resource_eps: tuple[float, float, float] | np.ndarray = (0.0, 0.0, 0.0),
    max_front_size: int = 0,
) -> tuple[np.ndarray, bool]:
    """Return a Pareto front plus a disabled flag.

    Vectors have shape ``(n, 4)`` and store ``(rc, energy, load,
    occupation)``.  Raw time is intentionally not a Pareto dimension: the
    direct-label caller already tracks current time, while RPCE only needs the
    optimistic remaining occupation budget.  RC and resource values are rounded
    downward before comparison and storage, so epsilon-relaxed dominance stays
    optimistic through recursive front composition.
    """

    if vectors.size <= 0:
        return _EMPTY_FRONT.copy(), False
    array = np.asarray(vectors, dtype=float)
    if array.ndim != 2 or array.shape[1] != _FRONT_DIM:
        raise ValueError("resource Pareto vectors must have shape (n, 4)")
    finite = array[np.all(np.isfinite(array), axis=1)].copy()
    if finite.size <= 0:
        return _EMPTY_FRONT.copy(), False
    finite[:, _RC] = _quantized_rc(finite[:, _RC], float(rc_eps))
    eps = np.asarray(resource_eps, dtype=float)
    if eps.shape != (3,):
        raise ValueError("resource_eps must have three entries")
    finite = _quantize_resources_down(finite, eps)
    limit = max(0, int(max_front_size))
    if limit > 0 and finite.shape[0] > limit * 16:
        return _EMPTY_FRONT.copy(), True
    compare = _resource_compare_values(finite, eps)
    order = np.lexsort(
        (
            compare[:, _OCCUPATION],
            compare[:, _LOAD],
            compare[:, _ENERGY],
            finite[:, _RC],
        )
    )
    sorted_vectors = finite[order]
    sorted_compare = compare[order]
    kept_vectors = np.empty((0, _FRONT_DIM), dtype=float)
    kept_compare = np.empty((0, _FRONT_DIM), dtype=float)
    for vector, cmp_vector in zip(sorted_vectors, sorted_compare, strict=False):
        if kept_vectors.size:
            dominated = np.all(kept_compare <= cmp_vector + 1.0e-12, axis=1)
            if bool(np.any(dominated)):
                continue
            dominated_by_new = np.all(cmp_vector <= kept_compare + 1.0e-12, axis=1)
            if bool(np.any(dominated_by_new)):
                keep_mask = ~dominated_by_new
                kept_vectors = kept_vectors[keep_mask]
                kept_compare = kept_compare[keep_mask]
        kept_vectors = np.vstack((kept_vectors, vector.reshape(1, _FRONT_DIM)))
        kept_compare = np.vstack((kept_compare, cmp_vector.reshape(1, _FRONT_DIM)))
        if limit > 0 and kept_vectors.shape[0] > limit:
            return _EMPTY_FRONT.copy(), True
    return kept_vectors, False


class ResourceParetoCompletionEnvelope:
    """Lazy resource-Pareto lower bound over relaxed completion sorties."""

    def __init__(
        self,
        data: FutureData,
        duals: Any,
        *,
        max_tasks_per_sortie: int,
        sortie_limit: int,
        max_front_size: int = 5000,
        time_eps: float = 1.0e-3,
        energy_eps: float = 1.0e-3,
        load_eps: float = 1.0e-6,
        rc_eps: float = 1.0e-9,
        lazy_enabled: bool = True,
        deadline: float | None = None,
    ) -> None:
        started = time.perf_counter()
        self.data = data
        self.duals = duals
        self.tasks = tuple(int(task) for task in data.tasks)
        self.task_to_bit = {int(task): index for index, task in enumerate(self.tasks)}
        self.nodes = (0, *self.tasks)
        self.max_tasks_per_sortie = max(1, int(max_tasks_per_sortie))
        self.sortie_limit = max(0, int(sortie_limit))
        self.max_front_size = max(0, int(max_front_size))
        self.time_eps = max(0.0, float(time_eps))
        self.energy_eps = max(0.0, float(energy_eps))
        self.load_eps = max(0.0, float(load_eps))
        self.occupation_eps = self.time_eps
        self.rc_eps = max(0.0, float(rc_eps))
        self.lazy_enabled = bool(lazy_enabled)
        self.deadline = None if deadline is None else float(deadline)
        self.rho = max(1.0e-9, float(data.rho))
        self.horizon = max(0.0, float(data.horizon))
        self.capacity = max(0.0, float(data.capacity))
        self.energy_limit = max(0.0, float(data.energy_limit))
        self.survival_energy_rate = max(0.0, float(data.survival_energy_rate))
        self.resource_eps = np.asarray(
            (self.energy_eps, self.load_eps, self.occupation_eps),
            dtype=float,
        )
        self.service_time = {int(task): float(data.task_value(int(task), "sigma")) for task in self.tasks}
        self.service_energy = {int(task): float(data.task_value(int(task), "g")) for task in self.tasks}
        self.service_cost = {int(task): float(data.task_value(int(task), "c_srv")) for task in self.tasks}
        self.task_load = {int(task): float(data.task_value(int(task), "d")) for task in self.tasks}
        self.task_reward = {int(task): float(getattr(duals, "cover", {}).get(int(task), 0.0)) for task in self.tasks}
        self._arc_front_cache: dict[tuple[int, int], np.ndarray | None] = {}
        self._sortie_front_cache: dict[tuple[int, int, int], np.ndarray | None] = {}
        self._closed_tail_sortie_front: np.ndarray | None | bool = False
        self._tail_front_cache: dict[int, np.ndarray | None] = {}
        self.overflow_state_count = 0
        self.disabled_state_count = 0
        self.query_count = 0
        self.query_feasible_count = 0
        self.query_disabled_count = 0
        self.resource_infeasible_count = 0
        self.runtime_disabled = False
        self.disable_reason: str | None = None
        self._lb_sum = 0.0
        self._lb_count = 0
        self.min_lb: float | None = None
        if not self.lazy_enabled:
            for slots in range(self.max_tasks_per_sortie + 1):
                for node in self.nodes:
                    self._sortie_front(int(node), int(slots))
            for sorties in range(self.sortie_limit + 1):
                self._tail_front(int(sorties))
        self.build_time = time.perf_counter() - started

    def _deadline_exceeded(self) -> bool:
        return self.deadline is not None and time.perf_counter() > float(self.deadline)

    @property
    def arc_front_count(self) -> int:
        return len(self._arc_front_cache)

    @property
    def sortie_front_count(self) -> int:
        return len(self._sortie_front_cache)

    @property
    def tail_front_count(self) -> int:
        return len(self._tail_front_cache)

    @property
    def mean_lb(self) -> float | None:
        if self._lb_count <= 0:
            return None
        return self._lb_sum / float(self._lb_count)

    @property
    def is_available(self) -> bool:
        return not bool(self.runtime_disabled)

    def _mark_disabled(self, reason: str) -> None:
        self.runtime_disabled = True
        if self.disable_reason is None:
            self.disable_reason = str(reason)

    def stats(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "build_time": float(self.build_time),
            "arc_front_count": int(self.arc_front_count),
            "sortie_front_count": int(self.sortie_front_count),
            "tail_front_count": int(self.tail_front_count),
            "overflow_state_count": int(self.overflow_state_count),
            "disabled_state_count": int(self.disabled_state_count),
            "query_count": int(self.query_count),
            "query_feasible_count": int(self.query_feasible_count),
            "query_disabled_count": int(self.query_disabled_count),
            "resource_infeasible_count": int(self.resource_infeasible_count),
            "runtime_disabled": bool(self.runtime_disabled),
            "disable_reason": self.disable_reason,
            "min_lb": self.min_lb,
            "mean_lb": self.mean_lb,
        }

    def _filter_front(self, vectors: np.ndarray) -> np.ndarray | None:
        front, disabled = filter_pareto_vectors(
            vectors,
            rc_eps=self.rc_eps,
            resource_eps=self.resource_eps,
            max_front_size=self.max_front_size,
        )
        if disabled:
            self.overflow_state_count += 1
            self.disabled_state_count += 1
            self._mark_disabled("front_overflow")
            return None
        return front

    def _combine_fronts(self, left: np.ndarray, right: np.ndarray) -> np.ndarray | None:
        if left.size <= 0 or right.size <= 0:
            return _EMPTY_FRONT.copy()
        if self.max_front_size > 0 and left.shape[0] * right.shape[0] > self.max_front_size * 16:
            self.overflow_state_count += 1
            self.disabled_state_count += 1
            self._mark_disabled("candidate_overflow")
            return None
        combined = (left[:, None, :] + right[None, :, :]).reshape(-1, _FRONT_DIM)
        return self._filter_front(combined)

    def _arc_front(self, source: int, target: int) -> np.ndarray | None:
        key = (int(source), int(target))
        cached = self._arc_front_cache.get(key)
        if cached is not None or key in self._arc_front_cache:
            return cached
        if self._deadline_exceeded():
            self.disabled_state_count += 1
            self._mark_disabled("deadline")
            self._arc_front_cache[key] = None
            return None
        if int(source) == int(target):
            result = _EMPTY_FRONT.copy()
            self._arc_front_cache[key] = result
            return result
        rows: list[tuple[float, float, float, float]] = []
        for option in self.data.options(int(source), int(target)):
            travel_time = max(0.0, float(option.tau))
            travel_energy = max(0.0, float(option.energy))
            if int(target) == 0:
                energy = travel_energy + self.survival_energy_rate * travel_time
                occupation = travel_time + energy / self.rho
                rows.append((float(option.cost), energy, 0.0, occupation))
            else:
                service_time = max(0.0, self.service_time[int(target)])
                service_energy = max(0.0, self.service_energy[int(target)])
                elapsed = travel_time + service_time
                energy = travel_energy + service_energy + self.survival_energy_rate * elapsed
                occupation = elapsed + energy / self.rho
                rc = (
                    float(option.cost)
                    + float(self.service_cost[int(target)])
                    - float(self.task_reward[int(target)])
                )
                rows.append((rc, energy, max(0.0, self.task_load[int(target)]), occupation))
        vectors = np.asarray(rows, dtype=float) if rows else _EMPTY_FRONT.copy()
        result = self._filter_front(vectors)
        self._arc_front_cache[key] = result
        return result

    def _sortie_front(self, last: int, slots: int, visited_mask: int = 0) -> np.ndarray | None:
        effective_visited_mask = int(visited_mask)
        if int(last) in self.task_to_bit:
            effective_visited_mask |= 1 << int(self.task_to_bit[int(last)])
        key = (
            int(last),
            max(0, min(int(slots), self.max_tasks_per_sortie)),
            int(effective_visited_mask),
        )
        cached = self._sortie_front_cache.get(key)
        if cached is not None or key in self._sortie_front_cache:
            return cached
        if self._deadline_exceeded():
            self.disabled_state_count += 1
            self._mark_disabled("deadline")
            self._sortie_front_cache[key] = None
            return None
        candidates: list[np.ndarray] = []
        return_front = self._arc_front(int(last), 0)
        if return_front is None:
            self._sortie_front_cache[key] = None
            return None
        candidates.append(return_front)
        if int(slots) > 0:
            for task in self.tasks:
                bit = 1 << int(self.task_to_bit[int(task)])
                if int(task) == int(last):
                    continue
                if int(effective_visited_mask) & int(bit):
                    continue
                arc = self._arc_front(int(last), int(task))
                suffix = self._sortie_front(int(task), int(slots) - 1, int(effective_visited_mask) | int(bit))
                if arc is None or suffix is None:
                    self._sortie_front_cache[key] = None
                    return None
                combined = self._combine_fronts(arc, suffix)
                if combined is None:
                    self._sortie_front_cache[key] = None
                    return None
                if combined.size:
                    candidates.append(combined)
        stacked = np.vstack(candidates) if candidates else _EMPTY_FRONT.copy()
        result = self._filter_front(stacked)
        self._sortie_front_cache[key] = result
        return result

    def _closed_tail_sortie_options(self) -> np.ndarray | None:
        if self._closed_tail_sortie_front is not False:
            return self._closed_tail_sortie_front
        front = self._sortie_front(0, self.max_tasks_per_sortie, 0)
        if front is None:
            self._closed_tail_sortie_front = None
            return None
        feasible = front[
            (front[:, _ENERGY] <= self.energy_limit + self.energy_eps)
            & (front[:, _LOAD] <= self.capacity + self.load_eps)
            & (front[:, _OCCUPATION] <= self.horizon + self.occupation_eps)
        ].copy()
        if feasible.size:
            feasible[:, _ENERGY] = 0.0
            feasible[:, _LOAD] = 0.0
        result = self._filter_front(np.vstack((_ZERO_FRONT, feasible)) if feasible.size else _ZERO_FRONT)
        self._closed_tail_sortie_front = result
        return result

    def _tail_front(self, sorties: int) -> np.ndarray | None:
        sorties = max(0, min(int(sorties), self.sortie_limit))
        cached = self._tail_front_cache.get(sorties)
        if cached is not None or sorties in self._tail_front_cache:
            return cached
        if sorties <= 0:
            result = _ZERO_FRONT.copy()
            self._tail_front_cache[sorties] = result
            return result
        sortie_front = self._closed_tail_sortie_options()
        previous = self._tail_front(sorties - 1)
        if sortie_front is None or previous is None:
            self._tail_front_cache[sorties] = None
            return None
        combined = self._combine_fronts(sortie_front, previous)
        if combined is None:
            self._tail_front_cache[sorties] = None
            return None
        result = self._filter_front(np.vstack((_ZERO_FRONT, combined)))
        self._tail_front_cache[sorties] = result
        return result

    def _record_value(self, value: float) -> float:
        value = float(value)
        self.query_feasible_count += 1
        self._lb_count += 1
        self._lb_sum += value
        self.min_lb = value if self.min_lb is None else min(float(self.min_lb), value)
        return value

    def partial_value(
        self,
        last: int,
        remaining_slots_in_sortie: int,
        future_sorties: int,
        current_time: float,
        current_energy: float,
        current_load: float,
        current_mask: int = 0,
    ) -> ParetoQueryResult:
        self.query_count += 1
        if self.runtime_disabled:
            self.query_disabled_count += 1
            return ParetoQueryResult(disabled=True)
        current_front = self._sortie_front(
            int(last),
            max(0, int(remaining_slots_in_sortie)),
            int(current_mask),
        )
        future_front = self._tail_front(max(0, int(future_sorties)))
        if current_front is None or future_front is None:
            self.query_disabled_count += 1
            return ParetoQueryResult(disabled=True)
        current_front = current_front[
            (current_front[:, _ENERGY] <= self.energy_limit - float(current_energy) + self.energy_eps)
            & (current_front[:, _LOAD] <= self.capacity - float(current_load) + self.load_eps)
        ]
        if current_front.size <= 0:
            self.resource_infeasible_count += 1
            return ParetoQueryResult(value=float("inf"), infeasible=True)
        remaining_occupation = (
            self.horizon
            - max(0.0, float(current_time))
            - max(0.0, float(current_energy)) / self.rho
        )
        best: float | None = None
        for row in current_front:
            budget = float(remaining_occupation) - float(row[_OCCUPATION])
            feasible_tail = future_front[future_front[:, _OCCUPATION] <= budget + self.occupation_eps]
            if feasible_tail.size <= 0:
                continue
            tail_best = float(np.min(feasible_tail[:, _RC]))
            value = float(row[_RC]) + tail_best
            best = value if best is None else min(best, value)
        if best is None:
            self.resource_infeasible_count += 1
            return ParetoQueryResult(value=float("inf"), infeasible=True)
        return ParetoQueryResult(value=self._record_value(best))

    def suffix_value(self, remaining_sorties: int, end_time: float) -> ParetoQueryResult:
        self.query_count += 1
        if self.runtime_disabled:
            self.query_disabled_count += 1
            return ParetoQueryResult(disabled=True)
        if int(remaining_sorties) <= 0 or float(end_time) > self.horizon + self.occupation_eps:
            return ParetoQueryResult(value=self._record_value(0.0))
        tail = self._tail_front(max(0, int(remaining_sorties)))
        if tail is None:
            self.query_disabled_count += 1
            return ParetoQueryResult(disabled=True)
        budget = self.horizon - max(0.0, float(end_time))
        feasible = tail[tail[:, _OCCUPATION] <= budget + self.occupation_eps]
        if feasible.size <= 0:
            return ParetoQueryResult(value=self._record_value(0.0))
        return ParetoQueryResult(value=self._record_value(min(0.0, float(np.min(feasible[:, _RC])))))
