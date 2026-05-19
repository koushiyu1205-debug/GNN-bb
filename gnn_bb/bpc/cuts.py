"""中文摘要：本文件定义 clean BPC 的有效 cuts。包含日程 no-good、统一 crossing cut 和 schedule capacity cut。"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from .columns import RouteColumn
from .data import BPCData


SIGNATURE_CUT_KINDS = frozenset(
    {
        "schedule_nogood",
        "schedule_nogood_core",
        "schedule_nogood_full",
        "schedule_pair_conflict",
    }
)


def normalize_signatures(signatures: list[tuple[int, ...]] | tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(sorted(tuple(int(task) for task in signature) for signature in signatures))


def route_crossing_count(route: RouteColumn, tasks: tuple[int, ...]) -> float:
    subset = set(tasks)
    sequence = (0, *route.tasks, 0)
    crossings = 0
    for left, right in zip(sequence[:-1], sequence[1:]):
        if (int(left) in subset) != (int(right) in subset):
            crossings += 1
    return float(crossings)


@dataclass(frozen=True)
class ScheduleNoGoodCut:
    id: int
    vehicle: int
    signatures: tuple[tuple[int, ...], ...]
    kind: str = "schedule_nogood"
    source_vehicle: int | None = None

    @property
    def rhs(self) -> float:
        return float(len(self.signatures) - 1)

    @property
    def sense(self) -> str:
        return "<="

    @property
    def key(self) -> tuple:
        return (self.kind, int(self.vehicle), self.signatures)

    def coefficient(self, route: RouteColumn, vehicle: int) -> float:
        if int(vehicle) != int(self.vehicle):
            return 0.0
        return 1.0 if route.signature in self.signatures else 0.0


def make_no_good_cuts_for_all_vehicles(
    vehicles: tuple[int, ...],
    routes: list[RouteColumn],
    first_id: int,
    *,
    source_vehicle: int,
    kind: str,
) -> list[ScheduleNoGoodCut]:
    signatures = normalize_signatures(tuple(route.signature for route in routes))
    return [
        ScheduleNoGoodCut(
            id=first_id + index,
            vehicle=int(vehicle),
            signatures=signatures,
            kind=kind,
            source_vehicle=int(source_vehicle),
        )
        for index, vehicle in enumerate(vehicles)
    ]


@dataclass(frozen=True)
class CrossingCut:
    """中文注释：统一 crossing cut，K(S)=max(Kcap(S), Kresource(S))，只保留同一 S 的最强 RHS。"""

    id: int
    tasks: tuple[int, ...]
    rhs: float
    k_bound: int
    capacity_bound: int
    resource_bound: int
    demand: float
    capacity: float
    kind: str = "crossing_cut"

    @property
    def sense(self) -> str:
        return ">="

    @property
    def key(self) -> tuple:
        return (self.kind, frozenset(self.tasks))

    def coefficient(self, route: RouteColumn, vehicle: int) -> float:
        return route_crossing_count(route, self.tasks)


@dataclass(frozen=True)
class ScheduleCapacityCut:
    """中文注释：单车真实 schedule 最多服务 U(S) 个任务的上界 cut。"""

    id: int
    vehicle: int
    tasks: tuple[int, ...]
    upper_bound: int
    oracle_states: int
    source_vehicle: int | None = None
    source: str = "separation"
    kind: str = "schedule_capacity"

    @property
    def rhs(self) -> float:
        return 0.0

    @property
    def sense(self) -> str:
        return "<="

    @property
    def key(self) -> tuple:
        return (self.kind, int(self.vehicle), self.tasks)

    def coefficient(self, route: RouteColumn, vehicle: int) -> float:
        if int(vehicle) != int(self.vehicle):
            return 0.0
        subset = set(self.tasks)
        return float(sum(1 for task in route.task_set if int(task) in subset))

    def y_coefficient(self, vehicle: int) -> float:
        if int(vehicle) != int(self.vehicle):
            return 0.0
        return -float(self.upper_bound)


def make_schedule_capacity_cuts_for_all_vehicles(
    vehicles: tuple[int, ...],
    tasks: tuple[int, ...],
    upper_bound: int,
    oracle_states: int,
    first_id: int,
    *,
    source_vehicle: int,
    source: str,
) -> list[ScheduleCapacityCut]:
    tasks = tuple(sorted(int(task) for task in tasks))
    return [
        ScheduleCapacityCut(
            id=first_id + index,
            vehicle=int(vehicle),
            tasks=tasks,
            upper_bound=int(upper_bound),
            oracle_states=int(oracle_states),
            source_vehicle=int(source_vehicle),
            source=str(source),
        )
        for index, vehicle in enumerate(vehicles)
    ]


Cut = ScheduleNoGoodCut | CrossingCut | ScheduleCapacityCut


def rounded_capacity_rhs(data: BPCData, tasks: tuple[int, ...]) -> float:
    demand = sum(data.task_value(task, "d") for task in tasks)
    return float(2 * ceil(demand / data.capacity))


def capacity_route_lower_bound(data: BPCData, tasks: tuple[int, ...]) -> int:
    demand = sum(data.task_value(task, "d") for task in tasks)
    return int(ceil(demand / data.capacity))
