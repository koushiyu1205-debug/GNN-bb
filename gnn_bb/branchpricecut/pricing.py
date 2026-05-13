"""中文摘要：实现完整 vehicle schedule column 的 integrated schedule-labeling pricing。"""

from __future__ import annotations

from dataclasses import dataclass, field
import heapq
import time

from .branching import BranchConstraint, partial_allowed_by_branch, schedule_allowed_by_branch
from .columns import ScheduleColumn, Sortie
from .data import InstanceData
from .rmp import RMPDuals


@dataclass(order=True)
class Label:
    priority: float
    ready_time: float
    covered: frozenset[int] = field(compare=False)
    completed: tuple[Sortie, ...] = field(compare=False)
    current_tasks: tuple[int, ...] = field(compare=False)
    current_node: int = field(compare=False)
    current_time: float = field(compare=False)
    current_load: float = field(compare=False)
    current_energy: float = field(compare=False)
    current_cost: float = field(compare=False)
    current_service_start: dict[str, float] = field(compare=False)


@dataclass
class PricingResult:
    columns: list[ScheduleColumn]
    exhausted: bool
    best_reduced_cost: float | None
    label_pops: int
    generated_labels: int
    queue_peak: int
    stop_reason: str | None


def reduced_cost(column: ScheduleColumn, duals: RMPDuals, phase: str) -> float:
    objective_cost = 0.0 if phase == "phase1" else float(column.cost)
    return objective_cost - sum(float(duals.cover[task]) for task in column.task_set) - float(duals.fleet)


def _make_schedule(data: InstanceData, completed: tuple[Sortie, ...]) -> ScheduleColumn:
    task_set = frozenset(task for sortie in completed for task in sortie.tasks)
    variable_cost = sum(float(sortie.cost) for sortie in completed)
    return ScheduleColumn(
        id=-1,
        sorties=completed,
        task_set=task_set,
        cost=round(data.fixed_vehicle_cost + variable_cost, 6),
        variable_cost=round(variable_cost, 6),
        ready_time=round(float(completed[-1].ready_time), 6),
    )


def _priority(covered: frozenset[int], cost: float, duals: RMPDuals, phase: str, fixed: float) -> float:
    base = 0.0 if phase == "phase1" else fixed + cost
    return base - sum(float(duals.cover[task]) for task in covered)


def exact_schedule_pricing(
    data: InstanceData,
    existing_columns: list[ScheduleColumn],
    duals: RMPDuals,
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    phase: str,
    eps: float,
    max_columns_to_return: int,
    max_labels: int = 0,
    max_generated_labels: int = 0,
    max_queue_size: int = 0,
    max_candidate_pool: int = 0,
    max_seconds: float = 0.0,
) -> PricingResult:
    existing = {column.signature for column in existing_columns}
    candidates: dict[tuple[tuple[int, ...], ...], tuple[float, ScheduleColumn]] = {}
    best_rc: float | None = None
    label_pops = 0
    generated_labels = 0
    queue_peak = 1
    stop_reason: str | None = None
    exhausted = True
    started = time.perf_counter()
    deadline = started + float(max_seconds) if max_seconds and max_seconds > 0.0 else None

    start = Label(
        priority=0.0,
        ready_time=0.0,
        covered=frozenset(),
        completed=tuple(),
        current_tasks=tuple(),
        current_node=0,
        current_time=0.0,
        current_load=0.0,
        current_energy=0.0,
        current_cost=0.0,
        current_service_start={},
    )
    queue: list[Label] = [start]

    def time_exceeded() -> bool:
        return deadline is not None and time.perf_counter() >= deadline

    def push_label(item: Label) -> bool:
        nonlocal generated_labels, queue_peak, exhausted, stop_reason
        if time_exceeded():
            exhausted = False
            stop_reason = "time_limit"
            return False
        if max_generated_labels > 0 and generated_labels >= max_generated_labels:
            exhausted = False
            stop_reason = "generated_label_limit"
            return False
        if max_queue_size > 0 and len(queue) + 1 > max_queue_size:
            exhausted = False
            stop_reason = "queue_limit"
            return False
        heapq.heappush(queue, item)
        generated_labels += 1
        queue_peak = max(queue_peak, len(queue))
        return True

    def prune_candidate_pool() -> None:
        if max_candidate_pool <= 0 or len(candidates) <= max_candidate_pool:
            return
        keep = max(1, max_columns_to_return if max_columns_to_return > 0 else max_candidate_pool)
        keep = min(keep, max_candidate_pool)
        selected = sorted(candidates.values(), key=lambda item: item[0])[:keep]
        candidates.clear()
        candidates.update((column.signature, (rc, column)) for rc, column in selected)

    while queue:
        if stop_reason is not None:
            break
        if time_exceeded():
            exhausted = False
            stop_reason = "time_limit"
            break
        if max_labels > 0 and label_pops >= max_labels:
            exhausted = False
            stop_reason = "label_pop_limit"
            break
        label = heapq.heappop(queue)
        label_pops += 1

        if label.current_tasks:
            back = data.arc(label.current_node, 0)
            return_time = label.current_time + float(back["tau"])
            total_energy = label.current_energy + float(back["energy"])
            if total_energy <= data.energy_limit + 1.0e-9:
                ready_time = return_time + total_energy / data.rho
                if ready_time <= data.horizon + 1.0e-9:
                    sortie = Sortie(
                        tasks=label.current_tasks,
                        start_time=round(label.ready_time, 6),
                        return_time=round(return_time, 6),
                        ready_time=round(ready_time, 6),
                        load=round(label.current_load, 6),
                        energy=round(total_energy, 6),
                        cost=round(label.current_cost + float(back["cost"]), 6),
                        service_start=dict(label.current_service_start),
                    )
                    completed = (*label.completed, sortie)
                    column = _make_schedule(data, completed)
                    if schedule_allowed_by_branch(column, branch_constraints) and column.signature not in existing:
                        rc = reduced_cost(column, duals, phase)
                        best_rc = rc if best_rc is None else min(best_rc, rc)
                        if rc < -eps:
                            old = candidates.get(column.signature)
                            if old is None or rc < old[0]:
                                candidates[column.signature] = (rc, column)
                                prune_candidate_pool()

                    if len(completed) < data.sortie_limit:
                        next_label = Label(
                            priority=_priority(column.task_set, column.variable_cost, duals, phase, data.fixed_vehicle_cost),
                            ready_time=ready_time,
                            covered=column.task_set,
                            completed=completed,
                            current_tasks=tuple(),
                            current_node=0,
                            current_time=ready_time,
                            current_load=0.0,
                            current_energy=0.0,
                            current_cost=0.0,
                            current_service_start={},
                        )
                        if not push_label(next_label):
                            break
            if stop_reason is not None:
                break

        for task in data.tasks:
            if task in label.covered or task in label.current_tasks:
                continue
            next_covered = frozenset((*label.covered, *label.current_tasks, int(task)))
            if not partial_allowed_by_branch(next_covered, branch_constraints):
                continue
            segment = data.arc(label.current_node, task)
            arrival = label.current_time + float(segment["tau"])
            service_start = max(data.task_value(task, "r"), arrival)
            finish = service_start + data.task_value(task, "sigma")
            if finish > data.task_value(task, "D") + 1.0e-9:
                continue
            next_load = label.current_load + data.task_value(task, "d")
            if next_load > data.capacity + 1.0e-9:
                continue
            next_energy = label.current_energy + float(segment["energy"]) + data.task_value(task, "g")
            if next_energy > data.energy_limit + 1.0e-9:
                continue
            back = data.arc(task, 0)
            if finish + float(back["tau"]) > data.horizon + 1.0e-9:
                continue
            if next_energy + float(back["energy"]) > data.energy_limit + 1.0e-9:
                continue
            next_service_start = dict(label.current_service_start)
            next_service_start[str(task)] = round(service_start, 6)
            next_cost = label.current_cost + float(segment["cost"]) + data.task_value(task, "c_srv")
            next_tasks = (*label.current_tasks, int(task))
            if not push_label(
                Label(
                    priority=_priority(next_covered, next_cost, duals, phase, data.fixed_vehicle_cost),
                    ready_time=label.ready_time,
                    covered=label.covered,
                    completed=label.completed,
                    current_tasks=next_tasks,
                    current_node=int(task),
                    current_time=finish,
                    current_load=next_load,
                    current_energy=next_energy,
                    current_cost=next_cost,
                    current_service_start=next_service_start,
                )
            ):
                break
        if stop_reason is not None:
            break

    selected = sorted(candidates.values(), key=lambda item: item[0])
    if max_columns_to_return > 0:
        selected = selected[:max_columns_to_return]
    return PricingResult(
        columns=[column for _rc, column in selected],
        exhausted=exhausted,
        best_reduced_cost=best_rc,
        label_pops=label_pops,
        generated_labels=generated_labels,
        queue_peak=queue_peak,
        stop_reason=stop_reason,
    )
