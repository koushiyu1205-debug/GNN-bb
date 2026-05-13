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
    components, separates = same_components(constraints)
    for component in components:
        count = sum(1 for task in component if task in column.task_set)
        if 0 < count < len(component):
            return False
    for left, right in separates:
        if any(task in column.task_set for task in left) and any(task in column.task_set for task in right):
            return False
    return True


def partial_allowed_by_branch(covered: frozenset[int], constraints: tuple[BranchConstraint, ...]) -> bool:
    # 中文注释：separate 分支可以早过滤；same 分支只有完整 schedule 才能判断，不能过早剪掉只含一个端点的前缀。
    _components, separates = same_components(constraints)
    for left, right in separates:
        if any(task in covered for task in left) and any(task in covered for task in right):
            return False
    return True


def same_components(constraints: tuple[BranchConstraint, ...]) -> tuple[list[frozenset[int]], list[tuple[frozenset[int], frozenset[int]]]]:
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for constraint in constraints:
        parent.setdefault(constraint.i, constraint.i)
        parent.setdefault(constraint.j, constraint.j)
        if constraint.kind == "same":
            union(constraint.i, constraint.j)

    groups: dict[int, set[int]] = {}
    for task in list(parent):
        groups.setdefault(find(task), set()).add(task)
    components = [frozenset(group) for group in groups.values() if len(group) > 1]

    def component_of(task: int) -> frozenset[int]:
        root = find(task)
        return frozenset(groups.get(root, {task}))

    separates: list[tuple[frozenset[int], frozenset[int]]] = []
    for constraint in constraints:
        if constraint.kind == "separate":
            left = component_of(constraint.i)
            right = component_of(constraint.j)
            if left != right:
                separates.append((left, right))
    return components, separates


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
