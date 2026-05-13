"""中文摘要：定义 vehicle-schedule master 上的 Ryan-Foster 分支。"""

from __future__ import annotations

from dataclasses import dataclass

from .columns import ScheduleColumn


@dataclass(frozen=True)
class BranchConstraint:
    kind: str
    i: int
    j: int

    def name(self) -> str:
        return f"RF({self.i},{self.j})={self.kind}"


@dataclass(frozen=True)
class BranchCandidate:
    i: int
    j: int
    value: float
    fractionality: float


def schedule_allowed_by_branch(column: ScheduleColumn, constraints: tuple[BranchConstraint, ...]) -> bool:
    for constraint in constraints:
        has_i = constraint.i in column.task_set
        has_j = constraint.j in column.task_set
        if constraint.kind == "same" and has_i != has_j:
            return False
        if constraint.kind == "separate" and has_i and has_j:
            return False
    return True


def partial_allowed_by_branch(covered: frozenset[int], constraints: tuple[BranchConstraint, ...]) -> bool:
    # 中文注释：separate 分支可以早过滤；same 分支只有完整 schedule 才能判断，不能过早剪掉只含一个端点的前缀。
    for constraint in constraints:
        if constraint.kind == "separate" and constraint.i in covered and constraint.j in covered:
            return False
    return True


def generate_rf_candidates(
    tasks: tuple[int, ...],
    schedule_values: list[tuple[ScheduleColumn, float]],
    tol: float,
) -> list[BranchCandidate]:
    pair_value: dict[tuple[int, int], float] = {}
    for column, value in schedule_values:
        if value <= tol:
            continue
        ordered = sorted(column.task_set)
        for left_index, i in enumerate(ordered):
            for j in ordered[left_index + 1 :]:
                pair_value[(int(i), int(j))] = pair_value.get((int(i), int(j)), 0.0) + float(value)

    candidates: list[BranchCandidate] = []
    for left_index, i in enumerate(tasks):
        for j in tasks[left_index + 1 :]:
            value = pair_value.get((int(i), int(j)), 0.0)
            fractionality = min(value - int(value), int(value + 1.0) - value)
            if tol < fractionality < 1.0 - tol:
                candidates.append(BranchCandidate(int(i), int(j), value, fractionality))
    candidates.sort(key=lambda item: (-item.fractionality, item.i, item.j))
    return candidates

