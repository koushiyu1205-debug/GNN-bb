"""中文摘要：本文件定义 clean BPC 的有效 cuts。包含日程、容量、rank-1 和成本型排程下界 cut。"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from math import floor

from .columns import RouteColumn
from .data import BPCData


SIGNATURE_CUT_KINDS = frozenset(
    {
        "schedule_nogood",
        "schedule_nogood_core",
        "schedule_nogood_full",
        "schedule_pair_conflict",
        "schedule_clique_conflict",
        "schedule_route_set_packing",
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
    rhs_value: float | None = None
    scale_by_vehicle_use: bool = True

    @property
    def upper_bound(self) -> float:
        if self.rhs_value is not None:
            return float(self.rhs_value)
        return float(len(self.signatures) - 1)

    @property
    def rhs(self) -> float:
        if self.scale_by_vehicle_use:
            return 0.0
        return self.upper_bound

    @property
    def sense(self) -> str:
        return "<="

    @property
    def key(self) -> tuple:
        return (self.kind, int(self.vehicle), self.signatures, self.upper_bound, bool(self.scale_by_vehicle_use))

    def coefficient(self, route: RouteColumn, vehicle: int) -> float:
        if int(vehicle) != int(self.vehicle):
            return 0.0
        return 1.0 if route.signature in self.signatures else 0.0

    def y_coefficient(self, vehicle: int) -> float:
        if not self.scale_by_vehicle_use or int(vehicle) != int(self.vehicle):
            return 0.0
        return -self.upper_bound


@dataclass(frozen=True)
class WeightedScheduleRouteSetPackingCut:
    """中文注释：有限 route support 上的 weighted schedule packing cut。"""

    id: int
    vehicle: int
    signatures: tuple[tuple[int, ...], ...]
    weights: tuple[float, ...]
    upper_bound: float
    oracle_states: int
    source_vehicle: int | None = None
    source: str = "separation"
    alpha_pattern: str = "lp_value"
    kind: str = "weighted_schedule_route_set_packing"

    def __post_init__(self) -> None:
        if len(self.signatures) != len(self.weights):
            raise ValueError("weighted route-set packing cut requires one weight per signature")

    @property
    def rhs(self) -> float:
        return 0.0

    @property
    def sense(self) -> str:
        return "<="

    @property
    def key(self) -> tuple:
        return (
            self.kind,
            int(self.vehicle),
            self.signatures,
            tuple(round(float(weight), 9) for weight in self.weights),
            round(float(self.upper_bound), 9),
        )

    @property
    def weight_by_signature(self) -> dict[tuple[int, ...], float]:
        return {signature: float(weight) for signature, weight in zip(self.signatures, self.weights)}

    def coefficient(self, route: RouteColumn, vehicle: int) -> float:
        if int(vehicle) != int(self.vehicle):
            return 0.0
        return self.weight_by_signature.get(route.signature, 0.0)

    def y_coefficient(self, vehicle: int) -> float:
        if int(vehicle) != int(self.vehicle):
            return 0.0
        return -float(self.upper_bound)


def make_no_good_cuts_for_all_vehicles(
    vehicles: tuple[int, ...],
    routes: list[RouteColumn],
    first_id: int,
    *,
    source_vehicle: int,
    kind: str,
    rhs_value: float | None = None,
    scale_by_vehicle_use: bool = True,
) -> list[ScheduleNoGoodCut]:
    signatures = normalize_signatures(tuple(route.signature for route in routes))
    return [
        ScheduleNoGoodCut(
            id=first_id + index,
            vehicle=int(vehicle),
            signatures=signatures,
            kind=kind,
            source_vehicle=int(source_vehicle),
            rhs_value=rhs_value,
            scale_by_vehicle_use=scale_by_vehicle_use,
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


@dataclass(frozen=True)
class ScheduleSubsetCostLowerBoundCut:
    """中文注释：若车辆 r 完整服务任务集 S，则其真实变量成本至少为 L(S)。"""

    id: int
    vehicle: int
    tasks: tuple[int, ...]
    lower_bound: float
    oracle_states: int
    source: str = "separation"
    kind: str = "schedule_subset_cost_lb"

    @property
    def rhs(self) -> float:
        return 0.0

    @property
    def sense(self) -> str:
        return ">="

    @property
    def key(self) -> tuple:
        return (self.kind, int(self.vehicle), self.tasks, round(float(self.lower_bound), 9))

    def coefficient(self, route: RouteColumn, vehicle: int) -> float:
        if int(vehicle) != int(self.vehicle):
            return 0.0
        subset = set(self.tasks)
        covered = sum(1 for task in route.task_set if int(task) in subset)
        return float(route.cost) - float(self.lower_bound) * float(covered)

    def y_coefficient(self, vehicle: int) -> float:
        if int(vehicle) != int(self.vehicle):
            return 0.0
        return float(self.lower_bound) * float(max(0, len(self.tasks) - 1))


@dataclass(frozen=True)
class FleetLowerBoundCut:
    """中文注释：exact oracle 证明的全局车辆数下界 cut。"""

    id: int
    lower_bound: int
    tasks: tuple[int, ...]
    oracle_upper_bound: int
    oracle_states: int
    source: str = "single_vehicle_schedule_capacity"
    kind: str = "fleet_lower_bound"

    @property
    def rhs(self) -> float:
        return float(self.lower_bound)

    @property
    def sense(self) -> str:
        return ">="

    @property
    def key(self) -> tuple:
        return (self.kind, int(self.lower_bound), self.tasks)

    def coefficient(self, route: RouteColumn, vehicle: int) -> float:
        del route, vehicle
        return 0.0

    def y_coefficient(self, vehicle: int) -> float:
        del vehicle
        return 1.0


@dataclass(frozen=True)
class SubsetRowCut:
    """中文注释：经典 VRP subset-row cut：sum floor(|p∩S|/k) lambda <= floor(|S|/k)。"""

    id: int
    tasks: tuple[int, ...]
    divisor: int = 2
    kind: str = "subset_row"

    @property
    def rhs(self) -> float:
        return float(floor(len(self.tasks) / int(self.divisor)))

    @property
    def sense(self) -> str:
        return "<="

    @property
    def key(self) -> tuple:
        return (self.kind, self.tasks, int(self.divisor))

    def coefficient(self, route: RouteColumn, vehicle: int) -> float:
        del vehicle
        subset = set(self.tasks)
        count = sum(1 for task in route.task_set if int(task) in subset)
        return float(floor(count / int(self.divisor)))


@dataclass(frozen=True)
class LimitedMemoryRank1Cut:
    """中文注释：小 memory rank-1 CG cut，允许非均匀任务 multiplier。"""

    id: int
    tasks: tuple[int, ...]
    multipliers: tuple[int, ...]
    denominator: int = 3
    memory_tasks: tuple[int, ...] = tuple()
    kind: str = "limited_memory_rank1"

    @property
    def rhs(self) -> float:
        return float(floor(sum(int(value) for value in self.multipliers) / int(self.denominator)))

    @property
    def sense(self) -> str:
        return "<="

    @property
    def key(self) -> tuple:
        return (self.kind, self.tasks, self.multipliers, int(self.denominator))

    def coefficient(self, route: RouteColumn, vehicle: int) -> float:
        del vehicle
        weight_by_task = {int(task): int(weight) for task, weight in zip(self.tasks, self.multipliers)}
        route_weight = sum(weight_by_task.get(int(task), 0) for task in route.task_set)
        return float(floor(route_weight / int(self.denominator)))


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


Cut = (
    ScheduleNoGoodCut
    | WeightedScheduleRouteSetPackingCut
    | CrossingCut
    | ScheduleCapacityCut
    | ScheduleSubsetCostLowerBoundCut
    | FleetLowerBoundCut
    | SubsetRowCut
    | LimitedMemoryRank1Cut
)


def rounded_capacity_rhs(data: BPCData, tasks: tuple[int, ...]) -> float:
    demand = sum(data.task_value(task, "d") for task in tasks)
    return float(2 * ceil(demand / data.capacity))


def capacity_route_lower_bound(data: BPCData, tasks: tuple[int, ...]) -> int:
    demand = sum(data.task_value(task, "d") for task in tasks)
    return int(ceil(demand / data.capacity))
