"""中文摘要：本文件实现成本型 schedule lower-bound cut 使用的精确小规模单车 oracle。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

from .data import BPCData


ORACLE_TOL = 1.0e-9


class ScheduleSubsetCostResult(NamedTuple):
    lower_bound: float | None
    states_explored: int
    exact: bool
    feasible: bool


@dataclass(frozen=True)
class _CostLabel:
    mask: int
    node: int
    time: float
    load: float
    energy: float
    completed_sorties: int
    cost: float


def exact_schedule_subset_cost(
    data: BPCData,
    tasks: tuple[int, ...],
    *,
    max_states: int,
) -> ScheduleSubsetCostResult | None:
    """精确求一辆车真实 schedule 服务任务集 S 的最小变量成本。

    中文注释：状态数超过上限时返回 None，调用方不得加成本型 cut。若 exact
    搜索证明 S 不能由一辆车服务，则返回 feasible=False；这类 infeasible 集合应交给
    schedule_capacity cut，而不是成本下界 cut。
    """

    tasks = tuple(sorted(int(task) for task in tasks))
    if not tasks:
        return ScheduleSubsetCostResult(0.0, 0, True, True)
    if any(data.task_value(task, "d") > data.capacity + ORACLE_TOL for task in tasks):
        return ScheduleSubsetCostResult(None, 0, True, False)

    task_by_bit = {index: task for index, task in enumerate(tasks)}
    full_mask = (1 << len(tasks)) - 1
    initial = _CostLabel(mask=0, node=0, time=0.0, load=0.0, energy=0.0, completed_sorties=0, cost=0.0)
    queue = [initial]
    labels_by_key: dict[tuple[int, int, int], list[_CostLabel]] = {(0, 0, 0): [initial]}
    best_cost = float("inf")
    explored = 0

    while queue:
        label = queue.pop()
        explored += 1
        if max_states > 0 and explored > max_states:
            return None
        if label.cost >= best_cost - ORACLE_TOL:
            continue

        if label.mask == full_mask and label.node == 0:
            best_cost = min(best_cost, label.cost)
            continue

        closed = _close_current_sortie(data, label)
        if closed is not None:
            _push_label(queue, labels_by_key, closed)

        if label.mask == full_mask:
            continue
        if label.node == 0 and label.completed_sorties >= data.sortie_limit:
            continue

        for bit, task in task_by_bit.items():
            if label.mask & (1 << bit):
                continue
            nxt = _extend_to_task(data, label, task, bit)
            if nxt is None:
                continue
            _push_label(queue, labels_by_key, nxt)

    if best_cost == float("inf"):
        return ScheduleSubsetCostResult(None, explored, True, False)
    return ScheduleSubsetCostResult(round(best_cost, 6), explored, True, True)


def _close_current_sortie(data: BPCData, label: _CostLabel) -> _CostLabel | None:
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
    return _CostLabel(
        mask=label.mask,
        node=0,
        time=ready_time,
        load=0.0,
        energy=0.0,
        completed_sorties=label.completed_sorties + 1,
        cost=label.cost + float(back["cost"]),
    )


def _extend_to_task(data: BPCData, label: _CostLabel, task: int, bit: int) -> _CostLabel | None:
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

    return _CostLabel(
        mask=label.mask | (1 << bit),
        node=int(task),
        time=finish,
        load=load,
        energy=energy,
        completed_sorties=label.completed_sorties,
        cost=label.cost + float(segment["cost"]) + data.task_value(task, "c_srv"),
    )


def _push_label(
    queue: list[_CostLabel],
    labels_by_key: dict[tuple[int, int, int], list[_CostLabel]],
    label: _CostLabel,
) -> None:
    key = (int(label.mask), int(label.node), int(label.completed_sorties))
    bucket = labels_by_key.get(key, [])
    if any(_dominates(existing, label) for existing in bucket):
        return
    labels_by_key[key] = [existing for existing in bucket if not _dominates(label, existing)]
    labels_by_key[key].append(label)
    queue.append(label)


def _dominates(left: _CostLabel, right: _CostLabel) -> bool:
    return (
        left.time <= right.time + ORACLE_TOL
        and left.load <= right.load + ORACLE_TOL
        and left.energy <= right.energy + ORACLE_TOL
        and left.cost <= right.cost + ORACLE_TOL
    )
