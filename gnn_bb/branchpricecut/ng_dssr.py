"""ng-relaxed DSSR pricing for vehicle-schedule columns."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import heapq
import os
import resource
import sys
import time

from .branching import BranchConstraint, partial_allowed_by_branch, same_components, schedule_allowed_by_branch
from .columns import ScheduleColumn, Sortie
from .data import InstanceData
from .rmp import RMPDuals


@dataclass(order=True)
class NGLabel:
    priority: float
    ready_time: float
    dssr_seen: frozenset[int] = field(compare=False)
    ng_memory: frozenset[int] = field(compare=False)
    visits: tuple[int, ...] = field(compare=False)
    completed: tuple[Sortie, ...] = field(compare=False)
    current_tasks: tuple[int, ...] = field(compare=False)
    current_node: int = field(compare=False)
    current_time: float = field(compare=False)
    current_load: float = field(compare=False)
    current_energy: float = field(compare=False)
    current_cost: float = field(compare=False)
    total_cost: float = field(compare=False)
    current_service_start: dict[str, float] = field(compare=False)


@dataclass
class NGDSSRResult:
    columns: list[ScheduleColumn]
    exhausted: bool
    best_reduced_cost: float | None
    label_pops: int
    generated_labels: int
    queue_peak: int
    stop_reason: str | None
    certificate: bool = False
    labels_pruned_by_dominance: int = 0
    memory_peak_mb: float | None = None
    algorithm: str = "ng_dssr"
    dssr_iterations: int = 0
    dssr_memory_size: int = 0
    dssr_non_elementary_negative: int = 0
    ng_size: int = 0
    certificate_from_relaxation: bool = False
    full_memory_fallback_called: bool = False


def rss_mb() -> float:
    try:
        page_size = float(os.sysconf("SC_PAGE_SIZE"))
        with open("/proc/self/statm", encoding="utf-8") as handle:
            resident_pages = float(handle.read().split()[1])
        return resident_pages * page_size / (1024.0 * 1024.0)
    except (FileNotFoundError, IndexError, OSError, ValueError):
        usage = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        if sys.platform == "darwin":
            return usage / (1024.0 * 1024.0)
        return usage / 1024.0


def relaxed_reduced_cost(column: ScheduleColumn, duals: RMPDuals, phase: str) -> float:
    visits = [task for sortie in column.sorties for task in sortie.tasks]
    objective = 0.0 if phase == "phase1" else float(column.cost)
    return objective - sum(float(duals.cover[task]) for task in visits) - float(duals.fleet) - float(duals.vehicle_lb)


def relaxed_priority(visits: tuple[int, ...], cost: float, duals: RMPDuals, phase: str, fixed: float) -> float:
    objective = 0.0 if phase == "phase1" else fixed + cost
    return objective - sum(float(duals.cover[task]) for task in visits)


def make_schedule(data: InstanceData, completed: tuple[Sortie, ...]) -> ScheduleColumn:
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


def is_elementary(column: ScheduleColumn) -> bool:
    visits = [int(task) for sortie in column.sorties for task in sortie.tasks]
    return len(visits) == len(set(visits))


def repeated_tasks(column: ScheduleColumn) -> set[int]:
    seen: set[int] = set()
    repeated: set[int] = set()
    for sortie in column.sorties:
        for task in sortie.tasks:
            task = int(task)
            if task in seen:
                repeated.add(task)
            seen.add(task)
    return repeated


def branch_state_for_tasks(tasks: frozenset[int], constraints: tuple[BranchConstraint, ...]) -> tuple[tuple[str, int, tuple[int, ...]], ...]:
    components, separates = same_components(constraints)
    state: list[tuple[str, int, tuple[int, ...]]] = []
    for index, component in enumerate(components):
        hit = tuple(sorted(tasks & component))
        if hit:
            state.append(("same", index, hit))
    for index, (left, right) in enumerate(separates):
        left_hit = bool(tasks & left)
        right_hit = bool(tasks & right)
        if left_hit or right_hit:
            side = (1 if left_hit else 0, 1 if right_hit else 0)
            state.append(("separate", index, side))
    return tuple(state)


def build_ng_neighborhoods(
    data: InstanceData,
    constraints: tuple[BranchConstraint, ...],
    *,
    ng_size: int,
    include_time_compatible: bool,
    include_branch_components: bool,
) -> dict[int, frozenset[int]]:
    size = max(1, int(ng_size))
    components, _separates = same_components(constraints)
    branch_pairs = {(constraint.i, constraint.j) for constraint in constraints}
    branch_pairs |= {(j, i) for i, j in branch_pairs}
    neighborhoods: dict[int, frozenset[int]] = {}
    for task in data.tasks:
        task = int(task)
        candidates: list[tuple[float, int]] = []
        for other in data.tasks:
            other = int(other)
            if other == task:
                continue
            segment = data.arc(task, other)
            score = float(segment["cost"]) + 0.01 * float(segment["tau"])
            if include_time_compatible:
                arrival = data.task_value(task, "r") + data.task_value(task, "sigma") + float(segment["tau"])
                slack = data.task_value(other, "D") - max(data.task_value(other, "r"), arrival)
                if slack >= -1.0e-9:
                    score -= min(slack, 1000.0) * 1.0e-4
                else:
                    score += abs(slack)
            candidates.append((score, other))
        selected = {task}
        for _score, other in sorted(candidates)[: max(0, size - 1)]:
            selected.add(other)
        if include_branch_components:
            for component in components:
                if task in component:
                    selected.update(int(item) for item in component)
            for left, right in branch_pairs:
                if task == left:
                    selected.add(int(right))
        neighborhoods[task] = frozenset(selected)
    return neighborhoods


def label_key(label: NGLabel, constraints: tuple[BranchConstraint, ...]) -> tuple[
    frozenset[int],
    frozenset[int],
    frozenset[int],
    int,
    int,
    tuple[tuple[str, int, tuple[int, ...]], ...],
]:
    visited_set = frozenset(label.visits)
    return (
        label.dssr_seen,
        label.ng_memory,
        frozenset(label.current_tasks),
        int(label.current_node),
        len(label.completed),
        branch_state_for_tasks(visited_set, constraints),
    )


def label_dominates(left: NGLabel, right: NGLabel) -> bool:
    return (
        left.priority <= right.priority + 1.0e-9
        and left.ready_time <= right.ready_time + 1.0e-9
        and left.current_time <= right.current_time + 1.0e-9
        and left.current_load <= right.current_load + 1.0e-9
        and left.current_energy <= right.current_energy + 1.0e-9
        and left.current_cost <= right.current_cost + 1.0e-9
        and left.total_cost <= right.total_cost + 1.0e-9
    )


def ng_dssr_schedule_pricing(
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
    max_memory_mb: float = 0.0,
    memory_check_interval: int = 4096,
    enable_dominance: bool = True,
    ng_size: int = 8,
    include_time_compatible: bool = True,
    include_branch_components: bool = True,
    initial_memory_size: int = 0,
    max_iterations: int = 8,
    memory_growth: int = 4,
    certificate_without_full_memory: bool = True,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
    progress_interval_seconds: float = 0.0,
    progress_label_interval: int = 0,
) -> NGDSSRResult:
    all_tasks = frozenset(int(task) for task in data.tasks)
    memory = frozenset(int(task) for task in data.tasks[: max(0, int(initial_memory_size))])
    neighborhoods = build_ng_neighborhoods(
        data,
        branch_constraints,
        ng_size=ng_size,
        include_time_compatible=include_time_compatible,
        include_branch_components=include_branch_components,
    )
    deadline = time.perf_counter() + float(max_seconds) if max_seconds and max_seconds > 0.0 else None
    total_labels = 0
    total_generated = 0
    total_pruned = 0
    queue_peak = 0
    best_rc: float | None = None
    memory_peak_mb = rss_mb()
    non_elementary_negative = 0
    iterations = 0

    for iteration in range(1, max(1, int(max_iterations)) + 1):
        iterations = iteration
        remaining = 0.0 if deadline is None else deadline - time.perf_counter()
        if deadline is not None and remaining <= 0.0:
            return NGDSSRResult(
                [],
                False,
                best_rc,
                total_labels,
                total_generated,
                queue_peak,
                "time_limit",
                labels_pruned_by_dominance=total_pruned,
                memory_peak_mb=round(memory_peak_mb, 3),
                dssr_iterations=iterations,
                dssr_memory_size=len(memory),
                dssr_non_elementary_negative=non_elementary_negative,
                ng_size=int(ng_size),
            )
        result, repeated = _ng_relaxed_iteration(
            data,
            existing_columns,
            duals,
            branch_constraints,
            neighborhoods,
            memory=memory,
            phase=phase,
            eps=eps,
            max_columns_to_return=max_columns_to_return,
            max_labels=max_labels,
            max_generated_labels=max_generated_labels,
            max_queue_size=max_queue_size,
            max_candidate_pool=max_candidate_pool,
            max_seconds=0.0 if deadline is None else max(0.0, remaining),
            max_memory_mb=max_memory_mb,
            memory_check_interval=memory_check_interval,
            enable_dominance=enable_dominance,
            progress_callback=progress_callback,
            progress_interval_seconds=progress_interval_seconds,
            progress_label_interval=progress_label_interval,
            iteration=iteration,
            ng_size=int(ng_size),
        )
        total_labels += result.label_pops
        total_generated += result.generated_labels
        total_pruned += result.labels_pruned_by_dominance
        queue_peak = max(queue_peak, result.queue_peak)
        memory_peak_mb = max(memory_peak_mb, float(result.memory_peak_mb or 0.0))
        if result.best_reduced_cost is not None:
            best_rc = result.best_reduced_cost if best_rc is None else min(best_rc, result.best_reduced_cost)
        non_elementary_negative += len(repeated)

        if result.columns:
            return _aggregate_result(
                result,
                total_labels,
                total_generated,
                total_pruned,
                queue_peak,
                memory_peak_mb,
                iterations,
                len(memory),
                non_elementary_negative,
                int(ng_size),
            )
        if not result.exhausted:
            return _aggregate_result(
                result,
                total_labels,
                total_generated,
                total_pruned,
                queue_peak,
                memory_peak_mb,
                iterations,
                len(memory),
                non_elementary_negative,
                int(ng_size),
            )
        if result.best_reduced_cost is None or result.best_reduced_cost >= -eps:
            result.certificate = bool(certificate_without_full_memory)
            result.certificate_from_relaxation = bool(certificate_without_full_memory)
            return _aggregate_result(
                result,
                total_labels,
                total_generated,
                total_pruned,
                queue_peak,
                memory_peak_mb,
                iterations,
                len(memory),
                non_elementary_negative,
                int(ng_size),
            )
        grow = set(repeated)
        if len(grow) < int(memory_growth):
            scored = sorted(
                (abs(float(duals.cover[task])), int(task)) for task in data.tasks if int(task) not in memory
            )
            for _score, task in reversed(scored):
                grow.add(task)
                if len(grow) >= int(memory_growth):
                    break
        new_memory = frozenset(set(memory) | grow)
        if new_memory == memory:
            result.stop_reason = "negative_relaxed_no_memory_growth"
            result.certificate = False
            return _aggregate_result(
                result,
                total_labels,
                total_generated,
                total_pruned,
                queue_peak,
                memory_peak_mb,
                iterations,
                len(memory),
                non_elementary_negative,
                int(ng_size),
            )
        memory = new_memory
        if memory == all_tasks:
            continue

    return NGDSSRResult(
        [],
        False,
        best_rc,
        total_labels,
        total_generated,
        queue_peak,
        "dssr_iteration_limit",
        certificate=False,
        labels_pruned_by_dominance=total_pruned,
        memory_peak_mb=round(memory_peak_mb, 3),
        dssr_iterations=iterations,
        dssr_memory_size=len(memory),
        dssr_non_elementary_negative=non_elementary_negative,
        ng_size=int(ng_size),
    )


def _aggregate_result(
    result: NGDSSRResult,
    labels: int,
    generated: int,
    pruned: int,
    queue_peak: int,
    memory_peak_mb: float,
    iterations: int,
    memory_size: int,
    non_elementary_negative: int,
    ng_size: int,
) -> NGDSSRResult:
    result.label_pops = labels
    result.generated_labels = generated
    result.labels_pruned_by_dominance = pruned
    result.queue_peak = queue_peak
    result.memory_peak_mb = round(memory_peak_mb, 3)
    result.dssr_iterations = iterations
    result.dssr_memory_size = memory_size
    result.dssr_non_elementary_negative = non_elementary_negative
    result.ng_size = ng_size
    result.algorithm = "ng_dssr"
    return result


def _ng_relaxed_iteration(
    data: InstanceData,
    existing_columns: list[ScheduleColumn],
    duals: RMPDuals,
    branch_constraints: tuple[BranchConstraint, ...],
    neighborhoods: dict[int, frozenset[int]],
    *,
    memory: frozenset[int],
    phase: str,
    eps: float,
    max_columns_to_return: int,
    max_labels: int,
    max_generated_labels: int,
    max_queue_size: int,
    max_candidate_pool: int,
    max_seconds: float,
    max_memory_mb: float,
    memory_check_interval: int,
    enable_dominance: bool,
    progress_callback: Callable[[dict[str, object]], None] | None,
    progress_interval_seconds: float,
    progress_label_interval: int,
    iteration: int,
    ng_size: int,
) -> tuple[NGDSSRResult, set[int]]:
    existing = {column.signature for column in existing_columns}
    candidates: dict[tuple[tuple[int, ...], ...], tuple[float, ScheduleColumn]] = {}
    repeated_negative: set[int] = set()
    best_rc: float | None = None
    label_pops = 0
    generated_labels = 0
    queue_peak = 1
    labels_pruned_by_dominance = 0
    stop_reason: str | None = None
    exhausted = True
    started = time.perf_counter()
    deadline = started + float(max_seconds) if max_seconds and max_seconds > 0.0 else None
    memory_check_interval = max(1, int(memory_check_interval))
    memory_peak_mb = rss_mb()
    memory_check_counter = 0
    progress_interval_seconds = max(0.0, float(progress_interval_seconds))
    progress_label_interval = max(0, int(progress_label_interval))
    last_progress_time = started
    last_progress_labels = 0
    start = NGLabel(
        priority=0.0,
        ready_time=0.0,
        dssr_seen=frozenset(),
        ng_memory=frozenset(),
        visits=tuple(),
        completed=tuple(),
        current_tasks=tuple(),
        current_node=0,
        current_time=0.0,
        current_load=0.0,
        current_energy=0.0,
        current_cost=0.0,
        total_cost=0.0,
        current_service_start={},
    )
    queue: list[NGLabel] = [start]
    dominance_buckets: dict[tuple[object, ...], list[NGLabel]] = {}
    if enable_dominance:
        dominance_buckets[label_key(start, branch_constraints)] = [start]

    def time_exceeded() -> bool:
        return deadline is not None and time.perf_counter() >= deadline

    def memory_exceeded() -> bool:
        nonlocal memory_check_counter, memory_peak_mb
        if max_memory_mb <= 0.0:
            return False
        memory_check_counter += 1
        if memory_check_counter % memory_check_interval != 0:
            return False
        memory_peak_mb = max(memory_peak_mb, rss_mb())
        return memory_peak_mb >= max_memory_mb

    def emit_progress() -> None:
        nonlocal last_progress_labels, last_progress_time, memory_peak_mb
        if progress_callback is None:
            return
        now = time.perf_counter()
        by_time = progress_interval_seconds > 0.0 and now - last_progress_time >= progress_interval_seconds
        by_labels = progress_label_interval > 0 and label_pops - last_progress_labels >= progress_label_interval
        if not by_time and not by_labels:
            return
        memory_peak_mb = max(memory_peak_mb, rss_mb())
        progress_callback(
            {
                "elapsed": round(now - started, 6),
                "labels": label_pops,
                "generated_labels": generated_labels,
                "queue_size": len(queue),
                "queue_peak": queue_peak,
                "candidate_count": len(candidates),
                "best_rc": None if best_rc is None else round(best_rc, 6),
                "labels_pruned_by_dominance": labels_pruned_by_dominance,
                "memory_peak_mb": round(memory_peak_mb, 3),
                "dssr_memory_size": len(memory),
                "dssr_iteration": iteration,
                "ng_size": ng_size,
                "algorithm": "ng_dssr",
            }
        )
        last_progress_time = now
        last_progress_labels = label_pops

    def label_is_active(item: NGLabel) -> bool:
        if not enable_dominance:
            return True
        return any(old is item for old in dominance_buckets.get(label_key(item, branch_constraints), []))

    def dominance_pruned(item: NGLabel) -> bool:
        nonlocal labels_pruned_by_dominance
        if not enable_dominance:
            return False
        key = label_key(item, branch_constraints)
        bucket = dominance_buckets.setdefault(key, [])
        if any(label_dominates(old, item) for old in bucket):
            labels_pruned_by_dominance += 1
            return True
        keep = []
        for old in bucket:
            if label_dominates(item, old):
                labels_pruned_by_dominance += 1
                continue
            keep.append(old)
        keep.append(item)
        dominance_buckets[key] = keep
        return False

    def push_label(item: NGLabel) -> bool:
        nonlocal generated_labels, queue_peak, exhausted, stop_reason
        if time_exceeded():
            exhausted = False
            stop_reason = "time_limit"
            return False
        if memory_exceeded():
            exhausted = False
            stop_reason = "memory_limit"
            return False
        if max_generated_labels > 0 and generated_labels >= max_generated_labels:
            exhausted = False
            stop_reason = "generated_label_limit"
            return False
        if max_queue_size > 0 and len(queue) + 1 > max_queue_size:
            exhausted = False
            stop_reason = "queue_limit"
            return False
        if dominance_pruned(item):
            return True
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
        if memory_exceeded():
            exhausted = False
            stop_reason = "memory_limit"
            break
        if max_labels > 0 and label_pops >= max_labels:
            exhausted = False
            stop_reason = "label_pop_limit"
            break
        label = heapq.heappop(queue)
        if not label_is_active(label):
            continue
        label_pops += 1
        emit_progress()

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
                    column = make_schedule(data, completed)
                    total_cost = label.total_cost + float(back["cost"])
                    if schedule_allowed_by_branch(column, branch_constraints):
                        rc = relaxed_reduced_cost(column, duals, phase)
                        best_rc = rc if best_rc is None else min(best_rc, rc)
                        if rc < -eps:
                            if is_elementary(column):
                                if column.signature not in existing:
                                    old = candidates.get(column.signature)
                                    if old is None or rc < old[0]:
                                        candidates[column.signature] = (rc, column)
                                        prune_candidate_pool()
                            else:
                                repeated_negative.update(repeated_tasks(column))
                    if len(completed) < data.sortie_limit:
                        next_label = NGLabel(
                            priority=relaxed_priority(label.visits, column.variable_cost, duals, phase, data.fixed_vehicle_cost),
                            ready_time=ready_time,
                            dssr_seen=label.dssr_seen,
                            ng_memory=label.ng_memory,
                            visits=label.visits,
                            completed=completed,
                            current_tasks=tuple(),
                            current_node=0,
                            current_time=ready_time,
                            current_load=0.0,
                            current_energy=0.0,
                            current_cost=0.0,
                            total_cost=total_cost,
                            current_service_start={},
                        )
                        if not push_label(next_label):
                            break
            if stop_reason is not None:
                break

        for task in data.tasks:
            task = int(task)
            if task in label.current_tasks:
                continue
            if task in label.dssr_seen or task in label.ng_memory:
                continue
            next_visits = (*label.visits, task)
            next_visited_set = frozenset(next_visits)
            if not partial_allowed_by_branch(next_visited_set, branch_constraints):
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
            next_total_cost = label.total_cost + float(segment["cost"]) + data.task_value(task, "c_srv")
            next_tasks = (*label.current_tasks, task)
            next_dssr_seen = label.dssr_seen | ({task} if task in memory else set())
            next_ng_memory = frozenset((label.ng_memory & neighborhoods[task]) | {task} | next_dssr_seen)
            if not push_label(
                NGLabel(
                    priority=relaxed_priority(next_visits, next_total_cost, duals, phase, data.fixed_vehicle_cost),
                    ready_time=label.ready_time,
                    dssr_seen=frozenset(next_dssr_seen),
                    ng_memory=next_ng_memory,
                    visits=next_visits,
                    completed=label.completed,
                    current_tasks=next_tasks,
                    current_node=task,
                    current_time=finish,
                    current_load=next_load,
                    current_energy=next_energy,
                    current_cost=next_cost,
                    total_cost=next_total_cost,
                    current_service_start=next_service_start,
                )
            ):
                break
        if stop_reason is not None:
            break

    selected = sorted(candidates.values(), key=lambda item: item[0])
    if max_columns_to_return > 0:
        selected = selected[:max_columns_to_return]
    memory_peak_mb = max(memory_peak_mb, rss_mb())
    return (
        NGDSSRResult(
            columns=[column for _rc, column in selected],
            exhausted=exhausted,
            best_reduced_cost=best_rc,
            label_pops=label_pops,
            generated_labels=generated_labels,
            queue_peak=queue_peak,
            stop_reason=stop_reason,
            certificate=False,
            labels_pruned_by_dominance=labels_pruned_by_dominance,
            memory_peak_mb=round(memory_peak_mb, 3),
            algorithm="ng_dssr",
            dssr_memory_size=len(memory),
            dssr_non_elementary_negative=len(repeated_negative),
            ng_size=ng_size,
        ),
        repeated_negative,
    )
