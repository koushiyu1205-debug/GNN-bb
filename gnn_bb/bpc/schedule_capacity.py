"""中文摘要：本文件实现 schedule capacity upper-bound cut 使用的精确单车 oracle。

若无法在安全状态数内证明 U(S)，调用方应跳过 cut。这里还提供从不可排程
route 集合中提取候选任务集合的工具，用于生成更结构化的 schedule feasibility cut。
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import NamedTuple

from .columns import RouteColumn
from .data import BPCData


ORACLE_TOL = 1.0e-9


class ScheduleCapacityResult(NamedTuple):
    upper_bound: int
    states_explored: int
    exact: bool


class ScheduleCapacityConflict(NamedTuple):
    tasks: tuple[int, ...]
    upper_bound: int
    states_explored: int


@dataclass(frozen=True)
class _Label:
    mask: int
    node: int
    time: float
    load: float
    energy: float
    completed_sorties: int


def _dominates(left: _Label, right: _Label) -> bool:
    return (
        left.time <= right.time + ORACLE_TOL
        and left.load <= right.load + ORACLE_TOL
        and left.energy <= right.energy + ORACLE_TOL
        and left.completed_sorties <= right.completed_sorties
    )


def exact_schedule_task_capacity(
    data: BPCData,
    tasks: tuple[int, ...],
    *,
    max_states: int,
) -> ScheduleCapacityResult | None:
    """返回一辆车在真实多 sortie schedule 中最多能服务 tasks 里的多少个任务。

    中文注释：这是 exact labeling。状态数超过 max_states 时返回 None，表示没有证明更强上界，调用方不能加 cut。
    """

    tasks = tuple(sorted(int(task) for task in tasks))
    if not tasks:
        return ScheduleCapacityResult(0, 0, True)
    if len(tasks) == 1:
        return ScheduleCapacityResult(1, 1, True)

    task_by_bit = {index: task for index, task in enumerate(tasks)}
    initial = _Label(mask=0, node=0, time=0.0, load=0.0, energy=0.0, completed_sorties=0)
    queue = [initial]
    labels_by_key: dict[tuple[int, int], list[_Label]] = {(0, 0): [initial]}
    best = 0
    explored = 0

    while queue:
        label = queue.pop()
        explored += 1
        if explored > max_states:
            return None
        best = max(best, label.mask.bit_count())

        closed = _close_current_sortie(data, label)
        if closed is not None:
            best = max(best, closed.mask.bit_count())
            _push_label(queue, labels_by_key, closed)

        if label.node == 0 and label.completed_sorties >= data.sortie_limit:
            continue

        for bit, task in task_by_bit.items():
            if label.mask & (1 << bit):
                continue
            nxt = _extend_to_task(data, label, task, bit)
            if nxt is None:
                continue
            _push_label(queue, labels_by_key, nxt)

    return ScheduleCapacityResult(best, explored, True)


def schedule_capacity_conflict_candidates(
    routes: list[RouteColumn] | tuple[RouteColumn, ...],
    *,
    max_subset_size: int,
    max_candidates: int = 500,
) -> list[tuple[int, ...]]:
    """从不可排程 route 集合中生成用于结构性 cut 的任务集合候选。

    中文注释：候选生成只决定“试哪些 S”；真正是否加 cut 仍由 exact oracle 证明。
    """

    max_subset_size = max(2, int(max_subset_size))
    route_task_sets = [tuple(sorted(int(task) for task in route.task_set)) for route in routes if route.task_set]
    all_tasks = tuple(sorted({task for tasks in route_task_sets for task in tasks}))
    if len(all_tasks) < 2:
        return []

    candidates: set[tuple[int, ...]] = set()
    if len(all_tasks) <= max_subset_size:
        candidates.add(all_tasks)

    for tasks in route_task_sets:
        if 2 <= len(tasks) <= max_subset_size:
            candidates.add(tasks)

    max_route_combo = min(4, len(route_task_sets))
    for size in range(2, max_route_combo + 1):
        for combo in combinations(route_task_sets, size):
            tasks = tuple(sorted({task for route_tasks in combo for task in route_tasks}))
            if 2 <= len(tasks) <= max_subset_size:
                candidates.add(tasks)
            if len(candidates) >= max_candidates:
                break
        if len(candidates) >= max_candidates:
            break

    ordered_tasks = sorted(all_tasks)
    small_combo_limit = min(5, max_subset_size, len(ordered_tasks))
    for size in range(2, small_combo_limit + 1):
        for tasks in combinations(ordered_tasks, size):
            candidates.add(tuple(int(task) for task in tasks))
            if len(candidates) >= max_candidates:
                break
        if len(candidates) >= max_candidates:
            break

    ordered = sorted(candidates, key=lambda item: (-len(item), item))
    return ordered[: max(0, int(max_candidates))]


def find_schedule_capacity_conflict(
    data: BPCData,
    routes: list[RouteColumn] | tuple[RouteColumn, ...],
    *,
    max_subset_size: int,
    max_states: int,
    max_candidates: int = 500,
) -> ScheduleCapacityConflict | None:
    """返回一个由 exact oracle 证明的结构性任务容量冲突。

    若返回 `(S, U(S), states)`，则任意单车真实 schedule 都不能服务超过 `U(S)`
    个 `S` 内任务，因此可加入 `sum_i z[i,r] <= U(S) y_r`。
    """

    for tasks in schedule_capacity_conflict_candidates(
        routes,
        max_subset_size=max_subset_size,
        max_candidates=max_candidates,
    ):
        result = exact_schedule_task_capacity(data, tasks, max_states=max_states)
        if result is None or not result.exact:
            continue
        if int(result.upper_bound) < len(tasks):
            return ScheduleCapacityConflict(
                tasks=tuple(sorted(int(task) for task in tasks)),
                upper_bound=int(result.upper_bound),
                states_explored=int(result.states_explored),
            )
    return None


def _close_current_sortie(data: BPCData, label: _Label) -> _Label | None:
    if label.node == 0:
        return None
    if label.completed_sorties + 1 > data.sortie_limit:
        return None
    back = data.arc(label.node, 0)
    return_time = label.time + float(back["tau"])
    total_energy = label.energy + float(back["energy"])
    if total_energy > data.energy_limit + ORACLE_TOL:
        return None
    ready_time = return_time + total_energy / data.rho
    if ready_time > data.horizon + ORACLE_TOL:
        return None
    return _Label(
        mask=label.mask,
        node=0,
        time=ready_time,
        load=0.0,
        energy=0.0,
        completed_sorties=label.completed_sorties + 1,
    )


def _extend_to_task(data: BPCData, label: _Label, task: int, bit: int) -> _Label | None:
    segment = data.arc(label.node, task)
    arrival = label.time + float(segment["tau"])
    start = max(data.task_value(task, "r"), arrival)
    finish = start + data.task_value(task, "sigma")
    if finish > data.task_value(task, "D") + ORACLE_TOL:
        return None

    load = (0.0 if label.node == 0 else label.load) + data.task_value(task, "d")
    if load > data.capacity + ORACLE_TOL:
        return None

    energy = (0.0 if label.node == 0 else label.energy) + float(segment["energy"]) + data.task_value(task, "g")
    if energy > data.energy_limit + ORACLE_TOL:
        return None

    back = data.arc(task, 0)
    return_time = finish + float(back["tau"])
    total_energy = energy + float(back["energy"])
    ready_time = return_time + total_energy / data.rho
    if total_energy > data.energy_limit + ORACLE_TOL or ready_time > data.horizon + ORACLE_TOL:
        return None

    return _Label(
        mask=label.mask | (1 << bit),
        node=int(task),
        time=finish,
        load=load,
        energy=energy,
        completed_sorties=label.completed_sorties,
    )


def _push_label(queue: list[_Label], labels_by_key: dict[tuple[int, int], list[_Label]], label: _Label) -> None:
    key = (label.mask, label.node)
    bucket = labels_by_key.setdefault(key, [])
    if any(_dominates(existing, label) for existing in bucket):
        return
    labels_by_key[key] = [existing for existing in bucket if not _dominates(label, existing)]
    labels_by_key[key].append(label)
    queue.append(label)
