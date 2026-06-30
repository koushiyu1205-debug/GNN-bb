"""Seed journey-column pools for scalable diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from lunar_ice_bpc.domain.scenario import PATH_TYPES
from lunar_ice_bpc.exact.core.columns import build_timed_sortie
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn, build_journey_column


@dataclass(frozen=True)
class SeededJourneyPool:
    columns: tuple[JourneyColumn, ...]
    reference_journey_count: int
    reference_sortie_count: int
    singleton_count: int
    invalid_reference_journey_count: int
    invalid_reference_sortie_count: int
    covered_task_count: int

    def to_payload(self) -> dict:
        return {
            "status": "SEEDED_JOURNEY_POOL_BUILT",
            "column_count": len(self.columns),
            "reference_journey_count": self.reference_journey_count,
            "reference_sortie_count": self.reference_sortie_count,
            "singleton_count": self.singleton_count,
            "invalid_reference_journey_count": self.invalid_reference_journey_count,
            "invalid_reference_sortie_count": self.invalid_reference_sortie_count,
            "covered_task_count": self.covered_task_count,
            "note": "Seeded diagnostic pool from reference journeys, reference sorties, and singleton journeys.",
        }


def build_seeded_journey_pool(data: LunarIceData, reference_solution: dict[str, Any]) -> SeededJourneyPool:
    columns: list[JourneyColumn] = []
    invalid_reference_journey_count = 0
    invalid_reference_sortie_count = 0
    reference_journey_count = 0
    reference_sortie_count = 0

    for journey in reference_solution.get("journeys", []) or []:
        sorties = []
        journey_valid = True
        for sortie_payload in journey.get("sorties", []) or []:
            sortie = _sortie_from_payload(data, sortie_payload)
            if sortie is None:
                invalid_reference_sortie_count += 1
                journey_valid = False
                continue
            sorties.append(sortie)
            columns.append(build_journey_column(data, (sortie,)))
            reference_sortie_count += 1
        if journey_valid and sorties:
            columns.append(build_journey_column(data, tuple(sorties)))
            reference_journey_count += 1
        elif sorties:
            invalid_reference_journey_count += 1

    singleton_count = 0
    for task_id in data.task_ids:
        best: JourneyColumn | None = None
        for path_type in PATH_TYPES:
            sortie = build_timed_sortie(data, (task_id,), (path_type, path_type), start_time=0.0)
            if not sortie.feasible:
                continue
            column = build_journey_column(data, (sortie,))
            if best is None or column.objective < best.objective:
                best = column
        if best is not None:
            columns.append(best)
            singleton_count += 1

    unique = _dedupe_columns(columns)
    covered = {task_id for column in unique for task_id in column.task_set}
    return SeededJourneyPool(
        columns=unique,
        reference_journey_count=reference_journey_count,
        reference_sortie_count=reference_sortie_count,
        singleton_count=singleton_count,
        invalid_reference_journey_count=invalid_reference_journey_count,
        invalid_reference_sortie_count=invalid_reference_sortie_count,
        covered_task_count=len(covered),
    )


def _sortie_from_payload(data: LunarIceData, payload: dict[str, Any]):
    tasks = tuple(str(task_id) for task_id in payload.get("tasks", []) or [])
    path_types = tuple(str(leg.get("path_type")) for leg in payload.get("legs", []) or [])
    if len(path_types) != len(tasks) + 1:
        return None
    try:
        sortie = build_timed_sortie(data, tasks, path_types, start_time=float(payload.get("start_time", 0.0)))
    except Exception:
        return None
    return sortie if sortie.feasible else None


def _dedupe_columns(columns: list[JourneyColumn]) -> tuple[JourneyColumn, ...]:
    best: dict[tuple[tuple[str, ...], tuple[tuple[tuple[str, str, str], ...], ...]], JourneyColumn] = {}
    for column in columns:
        signature = (
            tuple(sorted(column.task_set)),
            tuple(
                tuple((leg.source, leg.target, leg.path_type) for leg in sortie.legs)
                for sortie in column.sorties
            ),
        )
        old = best.get(signature)
        if old is None or column.objective < old.objective - 1.0e-9:
            best[signature] = column
    return tuple(best[key] for key in sorted(best))
