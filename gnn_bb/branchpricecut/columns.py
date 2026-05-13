"""中文摘要：定义完整 vehicle schedule column 及其 JSON 输出格式。"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any


@dataclass(frozen=True)
class Sortie:
    tasks: tuple[int, ...]
    start_time: float
    return_time: float
    ready_time: float
    load: float
    energy: float
    cost: float
    service_start: dict[str, float]


@dataclass(frozen=True)
class ScheduleColumn:
    id: int
    sorties: tuple[Sortie, ...]
    task_set: frozenset[int]
    cost: float
    variable_cost: float
    ready_time: float

    @property
    def signature(self) -> tuple[tuple[int, ...], ...]:
        return tuple(sortie.tasks for sortie in self.sorties)

    def covers(self, task: int) -> bool:
        return int(task) in self.task_set


class SchedulePool:
    """中文注释：用完整 schedule signature 做强查重。"""

    def __init__(self) -> None:
        self.columns: list[ScheduleColumn] = []
        self.by_signature: dict[tuple[tuple[int, ...], ...], ScheduleColumn] = {}

    def add(self, column: ScheduleColumn) -> ScheduleColumn:
        existing = self.by_signature.get(column.signature)
        if existing is not None:
            return existing
        stored = replace(column, id=len(self.columns))
        self.columns.append(stored)
        self.by_signature[stored.signature] = stored
        return stored

    def contains(self, signature: tuple[tuple[int, ...], ...]) -> bool:
        return signature in self.by_signature


def schedule_to_json(column: ScheduleColumn) -> dict[str, Any]:
    return {
        "id": int(column.id),
        "signature": [list(sortie) for sortie in column.signature],
        "tasks": sorted(column.task_set),
        "cost": round(float(column.cost), 6),
        "variable_cost": round(float(column.variable_cost), 6),
        "ready_time": round(float(column.ready_time), 6),
        "sorties": [
            {
                "tasks": list(sortie.tasks),
                "start_time": round(float(sortie.start_time), 6),
                "return_time": round(float(sortie.return_time), 6),
                "ready_time": round(float(sortie.ready_time), 6),
                "load": round(float(sortie.load), 6),
                "energy": round(float(sortie.energy), 6),
                "cost": round(float(sortie.cost), 6),
                "service_start": sortie.service_start,
            }
            for sortie in column.sorties
        ],
    }

