"""中文摘要：本文件定义 clean BPC 的有效 cuts。当前只实现日程不可行 route 集合的 no-good cut。"""

from __future__ import annotations

from dataclasses import dataclass

from .columns import RouteColumn


def normalize_signatures(signatures: list[tuple[int, ...]] | tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(sorted(tuple(int(task) for task in signature) for signature in signatures))


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
    def key(self) -> tuple[int, tuple[tuple[int, ...], ...]]:
        return (int(self.vehicle), self.signatures)

    def coefficient(self, route: RouteColumn, vehicle: int) -> float:
        if int(vehicle) != int(self.vehicle):
            return 0.0
        return 1.0 if route.signature in self.signatures else 0.0


def make_no_good_cuts_for_all_vehicles(
    vehicles: tuple[int, ...],
    routes: list[RouteColumn],
    existing_count: int,
    *,
    source_vehicle: int,
    kind: str,
) -> list[ScheduleNoGoodCut]:
    signatures = normalize_signatures(tuple(route.signature for route in routes))
    return [
        ScheduleNoGoodCut(
            id=existing_count + index,
            vehicle=int(vehicle),
            signatures=signatures,
            kind=kind,
            source_vehicle=int(source_vehicle),
        )
        for index, vehicle in enumerate(vehicles)
    ]
