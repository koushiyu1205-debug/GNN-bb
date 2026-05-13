"""中文摘要：Layer 2 heuristic route-to-schedule composition DP。"""

from __future__ import annotations

from dataclasses import dataclass, field
import heapq
import math
import time
from typing import Any

from .branching import BranchConstraint, partial_allowed_by_branch, same_components, schedule_allowed_by_branch
from .columns import ScheduleColumn
from .data import InstanceData
from .rmp import RMPDuals, manual_reduced_cost
from .route_pool import SortieRoute, evaluate_sortie_route, route_reduced_contribution


@dataclass(order=True)
class DPLabel:
    priority: float
    covered: frozenset[int] = field(compare=False)
    used_sorties: int = field(compare=False)
    ready_time: float = field(compare=False)
    contribution: float = field(compare=False)
    routes: tuple[SortieRoute, ...] = field(compare=False)
    branch_state: tuple[tuple[int, tuple[int, ...], tuple[int, ...]], ...] = field(compare=False, default_factory=tuple)


@dataclass
class ScheduleDPStats:
    labels_created: int = 0
    labels_pruned_by_subset_dominance: int = 0
    labels_pruned_by_beam: int = 0
    exhausted: bool = True
    early_stopped: bool = False
    negative_schedules_found: int = 0
    best_rc: float | None = None
    elapsed: float = 0.0


@dataclass
class ScheduleDPResult:
    columns: list[ScheduleColumn]
    stats: ScheduleDPStats


def schedule_constant(data: InstanceData, duals: RMPDuals, phase: str) -> float:
    base = 0.0 if phase == "phase1" else float(data.fixed_vehicle_cost)
    return base - float(duals.fleet) - float(duals.vehicle_lb)


def _make_column(data: InstanceData, routes: tuple[SortieRoute, ...], start_ready: float = 0.0) -> ScheduleColumn | None:
    sorties = []
    ready = float(start_ready)
    task_set: set[int] = set()
    variable_cost = 0.0
    for route in routes:
        if task_set & route.task_set:
            return None
        sortie = evaluate_sortie_route(data, route.tasks, ready)
        if sortie is None:
            return None
        sorties.append(sortie)
        task_set.update(route.task_set)
        variable_cost += float(sortie.cost)
        ready = float(sortie.ready_time)
    if not sorties:
        return None
    return ScheduleColumn(
        id=-1,
        sorties=tuple(sorties),
        task_set=frozenset(task_set),
        cost=round(data.fixed_vehicle_cost + variable_cost, 6),
        variable_cost=round(variable_cost, 6),
        ready_time=round(ready, 6),
    )


def _branch_state(covered: frozenset[int], constraints: tuple[BranchConstraint, ...]) -> tuple[tuple[int, tuple[int, ...], tuple[int, ...]], ...]:
    # 中文注释：保守地把 same component 的 partial/full coverage 纳入 dominance 状态。
    state = []
    components, _separates = same_components(constraints)
    for index, component in enumerate(components):
        hit = tuple(sorted(covered & component))
        if hit:
            state.append((index, tuple(sorted(component)), hit))
    return tuple(state)


def label_dominates(left: DPLabel, right: DPLabel) -> bool:
    if not left.covered and right.covered:
        return False
    return (
        left.covered.issubset(right.covered)
        and left.used_sorties <= right.used_sorties
        and left.ready_time <= right.ready_time + 1.0e-9
        and left.contribution <= right.contribution + 1.0e-9
        and left.branch_state == right.branch_state
    )


def _passes_final_branch(column: ScheduleColumn, constraints: tuple[BranchConstraint, ...]) -> bool:
    return schedule_allowed_by_branch(column, constraints)


def _jaccard(left: frozenset[int], right: frozenset[int]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def _select_negative_candidates(
    candidates: dict[tuple[tuple[int, ...], ...], tuple[float, ScheduleColumn]],
    *,
    max_return: int,
    jaccard_limit: float,
    max_similar: int,
) -> list[tuple[float, ScheduleColumn]]:
    if max_return <= 0:
        return []
    selected: list[tuple[float, ScheduleColumn]] = []
    seen_task_sets: set[frozenset[int]] = set()
    for item in sorted(candidates.values(), key=lambda item: item[0]):
        _rc, column = item
        if column.task_set in seen_task_sets:
            continue
        similar = sum(1 for _old_rc, old in selected if _jaccard(column.task_set, old.task_set) >= jaccard_limit)
        if similar >= max_similar:
            continue
        seen_task_sets.add(column.task_set)
        selected.append(item)
        if len(selected) >= max_return:
            break
    return selected


def compose_schedules_heuristic(
    data: InstanceData,
    routes: list[SortieRoute],
    duals: RMPDuals,
    branch_constraints: tuple[BranchConstraint, ...],
    config: dict[str, Any],
    *,
    phase: str,
    eps: float,
    max_seconds: float = 0.0,
) -> ScheduleDPResult:
    started = time.perf_counter()
    deadline = started + float(max_seconds) if max_seconds and max_seconds > 0.0 else None
    stats = ScheduleDPStats()
    max_labels = int(config.get("schedule_dp_max_labels", 200000))
    beam_width = int(config.get("schedule_dp_beam_width", 5000))
    per_bucket = int(config.get("schedule_dp_max_labels_per_bucket", 5))
    time_bucket = max(1.0e-9, float(config.get("schedule_dp_time_bucket_size", 10)))
    enable_subset = bool(config.get("schedule_dp_enable_subset_dominance", True))
    enable_beam = bool(config.get("schedule_dp_enable_beam_pruning", True))
    max_return = int(config.get("max_negative_schedules_per_pricing", 20))
    jaccard_limit = float(config.get("schedule_dp_jaccard_similarity_limit", 0.9))
    max_similar = int(config.get("schedule_dp_max_jaccard_similar", 2))
    early_stop_on_full_batch = bool(config.get("schedule_dp_early_stop_on_full_batch", True))
    constant = schedule_constant(data, duals, phase)

    route_order = sorted(routes, key=lambda route: route_reduced_contribution(route, duals, phase))
    root = DPLabel(0.0, frozenset(), 0, 0.0, 0.0, tuple(), tuple())
    queue: list[DPLabel] = [root]
    dominance_buckets: dict[tuple[int, int, int], list[DPLabel]] = {}
    beam_buckets: dict[tuple[int, int, int, int], list[DPLabel]] = {}
    candidates: dict[tuple[tuple[int, ...], ...], tuple[float, ScheduleColumn]] = {}
    stop_search = False

    while queue and not stop_search:
        if deadline is not None and time.perf_counter() >= deadline:
            stats.exhausted = False
            break
        if max_labels > 0 and stats.labels_created >= max_labels:
            stats.exhausted = False
            break
        label = heapq.heappop(queue)
        for route in route_order:
            if deadline is not None and time.perf_counter() >= deadline:
                stats.exhausted = False
                break
            if route.task_set & label.covered:
                continue
            if label.used_sorties + 1 > data.sortie_limit:
                continue
            covered = frozenset((*label.covered, *route.task_set))
            if not partial_allowed_by_branch(covered, branch_constraints):
                continue
            sortie = evaluate_sortie_route(data, route.tasks, label.ready_time)
            if sortie is None:
                continue
            routes_next = (*label.routes, route)
            contribution = label.contribution + route_reduced_contribution(route, duals, phase)
            branch_state = _branch_state(covered, branch_constraints)
            next_label = DPLabel(
                priority=constant + contribution,
                covered=covered,
                used_sorties=label.used_sorties + 1,
                ready_time=float(sortie.ready_time),
                contribution=contribution,
                routes=routes_next,
                branch_state=branch_state,
            )
            stats.labels_created += 1
            if enable_subset:
                dominance_key = (
                    next_label.used_sorties,
                    int(math.floor(next_label.ready_time / time_bucket)),
                    hash(next_label.branch_state),
                )
                dominance_bucket = dominance_buckets.setdefault(dominance_key, [])
                if any(label_dominates(existing, next_label) for existing in dominance_bucket):
                    stats.labels_pruned_by_subset_dominance += 1
                    continue
            if enable_beam and per_bucket > 0:
                beam_key = (
                    next_label.used_sorties,
                    int(math.floor(next_label.ready_time / time_bucket)),
                    len(next_label.covered),
                    hash(next_label.branch_state),
                )
                beam_bucket = beam_buckets.setdefault(beam_key, [])
                beam_bucket.append(next_label)
                keep = sorted(beam_bucket, key=lambda item: item.contribution)[:per_bucket]
                if next_label not in keep:
                    stats.labels_pruned_by_beam += 1
                    stats.exhausted = False
                    continue
                beam_buckets[beam_key] = keep
                if len(beam_bucket) > len(keep):
                    stats.labels_pruned_by_beam += len(beam_bucket) - len(keep)
                    stats.exhausted = False
            if enable_subset:
                dominance_buckets[dominance_key].append(next_label)
            column = _make_column(data, routes_next)
            if column is not None and _passes_final_branch(column, branch_constraints):
                rc = manual_reduced_cost(column, duals, phase)
                stats.best_rc = rc if stats.best_rc is None else min(stats.best_rc, rc)
                if rc < -eps:
                    old = candidates.get(column.signature)
                    if old is None or rc < old[0]:
                        candidates[column.signature] = (rc, column)
                    if early_stop_on_full_batch and max_return > 0 and len(candidates) >= max_return:
                        selected_now = _select_negative_candidates(
                            candidates,
                            max_return=max_return,
                            jaccard_limit=jaccard_limit,
                            max_similar=max_similar,
                        )
                        if len(selected_now) >= max_return:
                            stats.exhausted = False
                            stats.early_stopped = True
                            stop_search = True
                            break
            heapq.heappush(queue, next_label)
        if stop_search:
            break
        if not stats.exhausted and deadline is not None and time.perf_counter() >= deadline:
            break
        if enable_beam and len(queue) > beam_width:
            queue = heapq.nsmallest(beam_width, queue)
            heapq.heapify(queue)
            stats.labels_pruned_by_beam += 1
            stats.exhausted = False

    selected = _select_negative_candidates(
        candidates,
        max_return=max_return,
        jaccard_limit=jaccard_limit,
        max_similar=max_similar,
    )
    stats.negative_schedules_found = len(selected)
    stats.elapsed = time.perf_counter() - started
    return ScheduleDPResult([column for _rc, column in selected], stats)
