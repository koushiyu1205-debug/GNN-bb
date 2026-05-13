"""中文摘要：本文件实现 schedule capacity upper-bound cut 使用的精确单车 oracle。若无法在安全状态数内证明 U(S)，调用方应跳过 cut。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

from .data import BPCData


ORACLE_TOL = 1.0e-9


class ScheduleCapacityResult(NamedTuple):
    upper_bound: int
    states_explored: int
    exact: bool


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
