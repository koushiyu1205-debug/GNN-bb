"""Integer selection over a supplied journey-column pool."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from lunar_ice_bpc.exact.bpc.core.task_index import TaskIndexMap
from lunar_ice_bpc.exact.core.journey import JourneyColumn


@dataclass(frozen=True)
class ColumnPoolSelection:
    status: str
    objective: float | None
    columns: tuple[JourneyColumn, ...]
    candidate_column_count: int
    unique_task_set_count: int
    state_count: int
    note: str


def select_journey_column_pool(
    task_ids: Iterable[str],
    columns: Iterable[JourneyColumn],
    *,
    fleet_size: int,
    max_states: int | None = None,
) -> ColumnPoolSelection:
    """Select a minimum-cost exact task cover from a supplied column pool."""

    ordered_tasks = tuple(sorted(str(task_id) for task_id in task_ids))
    if not ordered_tasks:
        return ColumnPoolSelection(
            status="EMPTY_COLUMN_POOL_SELECTION",
            objective=0.0,
            columns=tuple(),
            candidate_column_count=0,
            unique_task_set_count=0,
            state_count=1,
            note="No tasks were supplied.",
        )
    task_index = TaskIndexMap(ordered_tasks)
    task_to_bit = {task_id: task_index.mask_of(task_id) for task_id in task_index.external_ids}
    best_by_mask: dict[int, JourneyColumn] = {}
    candidate_count = 0
    for column in columns:
        if not column.task_set:
            continue
        mask = 0
        valid = True
        for task_id in column.task_set:
            bit = task_to_bit.get(str(task_id))
            if bit is None:
                valid = False
                break
            mask |= bit
        if not valid or mask == 0:
            continue
        candidate_count += 1
        old = best_by_mask.get(mask)
        if old is None or column.objective < old.objective - 1.0e-9:
            best_by_mask[mask] = column

    full_mask = task_index.full_mask
    available_masks = tuple(sorted(best_by_mask))
    layers: list[dict[int, float]] = [{0: 0.0}]
    predecessor: dict[tuple[int, int], tuple[int, int]] = {}
    state_count = 1
    for vehicle_count in range(1, int(fleet_size) + 1):
        previous = layers[-1]
        current: dict[int, float] = dict(previous)
        for mask, value in previous.items():
            remaining = full_mask ^ mask
            for submask in available_masks:
                if submask & remaining != submask:
                    continue
                column = best_by_mask.get(submask)
                if column is not None:
                    new_mask = mask | submask
                    new_value = value + float(column.objective)
                    if new_value < current.get(new_mask, float("inf")) - 1.0e-9:
                        current[new_mask] = new_value
                        predecessor[(vehicle_count, new_mask)] = (mask, submask)
                        if max_states is not None and len(current) + state_count > int(max_states):
                            return ColumnPoolSelection(
                                status="COLUMN_POOL_STATE_LIMIT",
                                objective=None,
                                columns=tuple(),
                                candidate_column_count=candidate_count,
                                unique_task_set_count=len(best_by_mask),
                                state_count=state_count + len(current),
                                note=f"Stopped after reaching max_states={max_states}.",
                            )
        state_count += len(current)
        layers.append(current)

    if full_mask not in layers[-1]:
        return ColumnPoolSelection(
            status="NO_EXACT_COVER_IN_COLUMN_POOL",
            objective=None,
            columns=tuple(),
            candidate_column_count=candidate_count,
            unique_task_set_count=len(best_by_mask),
            state_count=state_count,
            note="No exact cover was found within the supplied journey-column pool.",
        )

    selected: list[JourneyColumn] = []
    vehicle_count = int(fleet_size)
    mask = full_mask
    while vehicle_count > 0 and mask:
        prev = predecessor.get((vehicle_count, mask))
        if prev is None:
            vehicle_count -= 1
            continue
        old_mask, chosen_mask = prev
        selected.append(best_by_mask[chosen_mask])
        mask = old_mask
        vehicle_count -= 1
    selected.reverse()
    return ColumnPoolSelection(
        status="COLUMN_POOL_EXACT_COVER",
        objective=round(sum(column.objective for column in selected), 6),
        columns=tuple(selected),
        candidate_column_count=candidate_count,
        unique_task_set_count=len(best_by_mask),
        state_count=state_count,
        note="Optimal only within the supplied journey-column pool.",
    )
