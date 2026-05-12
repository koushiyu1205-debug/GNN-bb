"""中文摘要：本文件实现 clean BPC 的 pricing-compatible branching。主规则是 Ryan-Foster，fallback 是 task-vehicle、arc-usage 和 vehicle-use 分支。"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .columns import RouteColumn
from .data import BPCData


@dataclass(frozen=True)
class BranchConstraint:
    kind: str
    task_i: int
    task_j: int | None = None
    vehicle: int | None = None

    def name(self) -> str:
        if self.kind in {"ryan_together", "ryan_separate"}:
            relation = "same" if self.kind == "ryan_together" else "separate"
            return f"RF({self.task_i},{self.task_j})={relation}"
        if self.kind in {"arc_on", "arc_off"}:
            relation = "on" if self.kind == "arc_on" else "off"
            return f"arc({self.task_i},{self.task_j})={relation}"
        if self.kind in {"vehicle_use_on", "vehicle_use_off"}:
            relation = "on" if self.kind == "vehicle_use_on" else "off"
            return f"vehicle({self.vehicle})={relation}"
        relation = "on" if self.kind == "task_vehicle_on" else "off"
        return f"task_vehicle({self.task_i},{self.vehicle})={relation}"


@dataclass(frozen=True)
class BranchCandidate:
    """中文注释：3PB 使用的分支候选。value 是当前 LP 中对应结构变量的聚合值。"""

    kind: str
    left: BranchConstraint
    right: BranchConstraint
    value: float
    fractionality: float

    @property
    def key(self) -> str:
        if self.kind == "ryan_foster":
            return f"rf:{self.left.task_i}:{self.left.task_j}"
        if self.kind == "task_vehicle":
            return f"task_vehicle:{self.left.task_i}:{self.left.vehicle}"
        if self.kind == "arc":
            return f"arc:{self.left.task_i}:{self.left.task_j}"
        if self.kind == "vehicle":
            return f"vehicle:{self.left.vehicle}"
        return f"{self.kind}:{self.left.name()}:{self.right.name()}"

    def compact(self) -> dict:
        return {
            "key": self.key,
            "kind": self.kind,
            "left": self.left.name(),
            "right": self.right.name(),
            "value": round(float(self.value), 9),
            "fractionality": round(float(self.fractionality), 9),
        }


def route_uses_arc(route: RouteColumn, tail: int, head: int) -> bool:
    return any(int(left) == int(tail) and int(right) == int(head) for left, right in zip(route.tasks[:-1], route.tasks[1:]))


def route_branch_coefficient(route: RouteColumn, vehicle: int, constraint: BranchConstraint) -> float:
    if constraint.kind == "arc_on":
        assert constraint.task_j is not None
        return 1.0 if route_uses_arc(route, constraint.task_i, constraint.task_j) else 0.0
    return 0.0


def route_allowed_by_branch(route: RouteColumn, vehicle: int, constraints: tuple[BranchConstraint, ...]) -> bool:
    task_set = route.task_set
    for constraint in constraints:
        if constraint.kind == "ryan_together":
            assert constraint.task_j is not None
            contains = int(constraint.task_i) in task_set, int(constraint.task_j) in task_set
            if contains[0] != contains[1]:
                return False
        elif constraint.kind == "ryan_separate":
            assert constraint.task_j is not None
            if int(constraint.task_i) in task_set and int(constraint.task_j) in task_set:
                return False
        elif constraint.kind == "task_vehicle_on":
            if int(constraint.task_i) in task_set and int(vehicle) != int(constraint.vehicle):
                return False
        elif constraint.kind == "task_vehicle_off":
            if int(constraint.task_i) in task_set and int(vehicle) == int(constraint.vehicle):
                return False
        elif constraint.kind == "vehicle_use_off":
            if int(vehicle) == int(constraint.vehicle):
                return False
        elif constraint.kind == "arc_off":
            assert constraint.task_j is not None
            if route_uses_arc(route, constraint.task_i, constraint.task_j):
                return False
        elif constraint.kind in {"vehicle_use_on", "arc_on"}:
            continue
        else:
            raise ValueError(f"未知 branching constraint: {constraint.kind}")
    return True


def partial_sequence_allowed(sequence: tuple[int, ...], vehicle: int, constraints: tuple[BranchConstraint, ...]) -> bool:
    task_set = set(sequence)
    for constraint in constraints:
        if constraint.kind == "ryan_separate":
            assert constraint.task_j is not None
            if int(constraint.task_i) in task_set and int(constraint.task_j) in task_set:
                return False
        elif constraint.kind == "task_vehicle_off":
            if int(vehicle) == int(constraint.vehicle) and int(constraint.task_i) in task_set:
                return False
        elif constraint.kind == "task_vehicle_on":
            if int(vehicle) != int(constraint.vehicle) and int(constraint.task_i) in task_set:
                return False
        elif constraint.kind == "vehicle_use_off":
            if int(vehicle) == int(constraint.vehicle):
                return False
        elif constraint.kind == "arc_off":
            assert constraint.task_j is not None
            for left, right in zip(sequence[:-1], sequence[1:]):
                if int(left) == int(constraint.task_i) and int(right) == int(constraint.task_j):
                    return False
        elif constraint.kind in {"vehicle_use_on", "arc_on", "ryan_together"}:
            continue
    return True


def _fixed_rf_pairs(constraints: tuple[BranchConstraint, ...]) -> set[tuple[int, int]]:
    pairs = set()
    for constraint in constraints:
        if constraint.kind in {"ryan_together", "ryan_separate"} and constraint.task_j is not None:
            pairs.add(tuple(sorted((int(constraint.task_i), int(constraint.task_j)))))
    return pairs


def _fixed_task_vehicle_pairs(constraints: tuple[BranchConstraint, ...]) -> set[tuple[int, int]]:
    pairs = set()
    for constraint in constraints:
        if constraint.kind in {"task_vehicle_on", "task_vehicle_off"} and constraint.vehicle is not None:
            pairs.add((int(constraint.task_i), int(constraint.vehicle)))
    return pairs


def _task_has_vehicle_on(constraints: tuple[BranchConstraint, ...], task: int) -> bool:
    return any(constraint.kind == "task_vehicle_on" and int(constraint.task_i) == int(task) for constraint in constraints)


def _fixed_vehicles(constraints: tuple[BranchConstraint, ...]) -> set[int]:
    return {
        int(constraint.vehicle)
        for constraint in constraints
        if constraint.kind in {"vehicle_use_on", "vehicle_use_off"} and constraint.vehicle is not None
    }


def _fixed_arcs(constraints: tuple[BranchConstraint, ...]) -> set[tuple[int, int]]:
    return {
        (int(constraint.task_i), int(constraint.task_j))
        for constraint in constraints
        if constraint.kind in {"arc_on", "arc_off"} and constraint.task_j is not None
    }


def generate_branch_candidates(
    data: BPCData,
    route_values: list[tuple[RouteColumn, int, float]],
    y_values: dict[int, float],
    constraints: tuple[BranchConstraint, ...],
    *,
    tol: float = 1.0e-6,
) -> list[BranchCandidate]:
    candidates: list[BranchCandidate] = []

    fixed_rf = _fixed_rf_pairs(constraints)
    pair_values = {pair: 0.0 for pair in combinations(data.tasks, 2)}
    for route, _vehicle, value in route_values:
        if abs(value) <= tol:
            continue
        for pair in combinations(sorted(route.task_set), 2):
            pair_values[pair] = pair_values.get(pair, 0.0) + float(value)
    for (left, right), value in pair_values.items():
        if tuple(sorted((left, right))) in fixed_rf:
            continue
        if tol < value < 1.0 - tol:
            candidates.append(
                BranchCandidate(
                    "ryan_foster",
                    BranchConstraint("ryan_separate", int(left), int(right)),
                    BranchConstraint("ryan_together", int(left), int(right)),
                    float(value),
                    0.5 - abs(float(value) - 0.5),
                )
            )

    fixed_task_vehicle = _fixed_task_vehicle_pairs(constraints)
    assignment_values: dict[tuple[int, int], float] = {(task, vehicle): 0.0 for task in data.tasks for vehicle in data.vehicles}
    for route, vehicle, value in route_values:
        if abs(value) <= tol:
            continue
        for task in route.task_set:
            assignment_values[(int(task), int(vehicle))] += float(value)
    for (task, vehicle), value in assignment_values.items():
        if (task, vehicle) in fixed_task_vehicle or _task_has_vehicle_on(constraints, task):
            continue
        if tol < value < 1.0 - tol:
            candidates.append(
                BranchCandidate(
                    "task_vehicle",
                    BranchConstraint("task_vehicle_off", int(task), vehicle=int(vehicle)),
                    BranchConstraint("task_vehicle_on", int(task), vehicle=int(vehicle)),
                    float(value),
                    0.5 - abs(float(value) - 0.5),
                )
            )

    fixed_arcs = _fixed_arcs(constraints)
    arc_values: dict[tuple[int, int], float] = {}
    for route, _vehicle, value in route_values:
        if abs(value) <= tol:
            continue
        for tail, head in zip(route.tasks[:-1], route.tasks[1:]):
            arc = (int(tail), int(head))
            arc_values[arc] = arc_values.get(arc, 0.0) + float(value)
    for (tail, head), value in arc_values.items():
        if (tail, head) in fixed_arcs:
            continue
        if tol < value < 1.0 - tol:
            candidates.append(
                BranchCandidate(
                    "arc",
                    BranchConstraint("arc_off", int(tail), int(head)),
                    BranchConstraint("arc_on", int(tail), int(head)),
                    float(value),
                    0.5 - abs(float(value) - 0.5),
                )
            )

    fixed_vehicles = _fixed_vehicles(constraints)
    for vehicle, value in sorted(y_values.items()):
        if int(vehicle) in fixed_vehicles:
            continue
        if tol < value < 1.0 - tol:
            candidates.append(
                BranchCandidate(
                    "vehicle",
                    BranchConstraint("vehicle_use_off", 0, vehicle=int(vehicle)),
                    BranchConstraint("vehicle_use_on", 0, vehicle=int(vehicle)),
                    float(value),
                    0.5 - abs(float(value) - 0.5),
                )
            )
    return candidates


def choose_branch(
    data: BPCData,
    route_values: list[tuple[RouteColumn, int, float]],
    y_values: dict[int, float],
    constraints: tuple[BranchConstraint, ...],
    *,
    tol: float = 1.0e-6,
) -> tuple[BranchConstraint, BranchConstraint] | None:
    # 中文注释：兼容旧的首个候选策略；3PB 会直接使用 generate_branch_candidates。
    candidates = generate_branch_candidates(data, route_values, y_values, constraints, tol=tol)
    if not candidates:
        return None
    priority = {"ryan_foster": 0, "task_vehicle": 1, "arc": 2, "vehicle": 3}
    candidate = min(candidates, key=lambda item: (priority.get(item.kind, 99), -item.fractionality, item.key))
    return candidate.left, candidate.right
