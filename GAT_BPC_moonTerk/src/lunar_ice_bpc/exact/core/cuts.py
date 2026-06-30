"""Exact cut-context helpers for journey-column reduced costs."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Iterable

from lunar_ice_bpc.exact.core.journey import JourneyColumn


SUBSET_ROW_CUT = "subset_row"
FLEET_LOWER_BOUND_CUT = "fleet_lower_bound"
CUT_TYPES = (SUBSET_ROW_CUT, FLEET_LOWER_BOUND_CUT)


@dataclass(frozen=True)
class CutDefinition:
    cut_id: str
    cut_type: str
    tasks: tuple[str, ...] = tuple()
    divisor: int = 2
    rhs: float = 0.0

    def __post_init__(self) -> None:
        if not str(self.cut_id):
            raise ValueError("cut_id must be non-empty")
        if str(self.cut_type) not in CUT_TYPES:
            raise ValueError(f"unsupported cut_type {self.cut_type!r}")
        normalized_tasks = tuple(sorted({str(task_id) for task_id in self.tasks}))
        object.__setattr__(self, "tasks", normalized_tasks)
        object.__setattr__(self, "cut_type", str(self.cut_type))
        object.__setattr__(self, "cut_id", str(self.cut_id))
        object.__setattr__(self, "divisor", int(self.divisor))
        object.__setattr__(self, "rhs", float(self.rhs))
        if self.cut_type == SUBSET_ROW_CUT:
            if len(normalized_tasks) < 2:
                raise ValueError("subset_row cut requires at least two tasks")
            if int(self.divisor) < 2:
                raise ValueError("subset_row divisor must be at least 2")
        if self.cut_type == FLEET_LOWER_BOUND_CUT and float(self.rhs) <= 0.0:
            raise ValueError("fleet_lower_bound cut requires positive rhs")

    def coefficient(self, column: JourneyColumn) -> float:
        if self.cut_type == SUBSET_ROW_CUT:
            overlap = len({str(task_id) for task_id in column.task_set}.intersection(self.tasks))
            return float(floor(overlap / int(self.divisor)))
        if self.cut_type == FLEET_LOWER_BOUND_CUT:
            return 1.0 if column.task_set else 0.0
        raise ValueError(f"unsupported cut_type {self.cut_type!r}")

    def to_payload(self) -> dict:
        return {
            "cut_id": self.cut_id,
            "cut_type": self.cut_type,
            "tasks": list(self.tasks),
            "divisor": self.divisor,
            "rhs": self.rhs,
        }


@dataclass(frozen=True)
class CutContext:
    cuts: tuple[CutDefinition, ...] = tuple()

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for cut in self.cuts:
            if cut.cut_id in seen:
                raise ValueError(f"duplicate cut_id {cut.cut_id!r}")
            seen.add(cut.cut_id)

    @property
    def empty(self) -> bool:
        return not self.cuts

    def coefficients_for(self, column: JourneyColumn) -> dict[str, float]:
        return cut_coefficients_for_journey(column, self)

    def to_payload(self) -> dict:
        return {
            "schema_version": "lunar_ice_bpc.cut_context.v1",
            "cut_count": len(self.cuts),
            "cuts": [cut.to_payload() for cut in self.cuts],
            "note": "Exact cut coefficient context. Current runner records no active cuts by default.",
        }


def subset_row_cut(cut_id: str, tasks: Iterable[str], *, divisor: int = 2) -> CutDefinition:
    task_tuple = tuple(str(task_id) for task_id in tasks)
    return CutDefinition(
        cut_id=str(cut_id),
        cut_type=SUBSET_ROW_CUT,
        tasks=task_tuple,
        divisor=int(divisor),
        rhs=float(floor(len(set(task_tuple)) / int(divisor))),
    )


def fleet_lower_bound_cut(cut_id: str, *, min_vehicles: int) -> CutDefinition:
    return CutDefinition(
        cut_id=str(cut_id),
        cut_type=FLEET_LOWER_BOUND_CUT,
        tasks=tuple(),
        divisor=1,
        rhs=float(min_vehicles),
    )


def cut_coefficients_for_journey(column: JourneyColumn, context: CutContext | None) -> dict[str, float]:
    if context is None or context.empty:
        return {}
    return {
        cut.cut_id: coefficient
        for cut in context.cuts
        for coefficient in (cut.coefficient(column),)
        if abs(float(coefficient)) > 1.0e-12
    }


def cut_context_from_payload(payload: dict | None) -> CutContext:
    if not payload:
        return CutContext()
    cuts = []
    for row in payload.get("cuts", []) or []:
        cuts.append(
            CutDefinition(
                cut_id=str(row["cut_id"]),
                cut_type=str(row["cut_type"]),
                tasks=tuple(str(task_id) for task_id in row.get("tasks", []) or []),
                divisor=int(row.get("divisor", 2)),
                rhs=float(row.get("rhs", 0.0)),
            )
        )
    return CutContext(cuts=tuple(cuts))
