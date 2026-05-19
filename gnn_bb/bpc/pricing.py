"""中文摘要：本文件实现 clean BPC 的 RCSP route pricing。

定价始终使用 true dual 计算 reduced cost。调用方可以用 label 上限做启发式找列，
但只有完整枚举 exhausted=True 的调用才能作为节点最优性证明。
"""

from __future__ import annotations

from dataclasses import dataclass
import heapq

from .branching import BranchConstraint, route_allowed_by_branch, route_branch_coefficient
from .columns import RouteColumn, evaluate_route, route_work_time_lower_bound
from .cuts import SIGNATURE_CUT_KINDS, Cut
from .data import BPCData
from .rmp import RMPDuals


@dataclass(order=True)
class Label:
    priority: float
    node: int
    sequence: tuple[int, ...]
    visited_mask: int
    crossing_counts: tuple[int, ...]
    arc_on_mask: int
    signature_prefix_mask: int
    time: float
    load: float
    energy: float
    travel_time: float
    cost: float
    service_time: float
    task_dual_sum: float


@dataclass
class PricingResult:
    routes: list[RouteColumn]
    exhausted: bool
    best_reduced_cost: float | None
    label_pops: int
    generated_labels: int
    negative_routes: int
    dominance_enabled: bool = False
    dominance_pruned: int = 0


Candidate = tuple[float, RouteColumn]


def _round(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def reduced_cost(
    data: BPCData,
    route: RouteColumn,
    vehicle: int,
    duals: RMPDuals,
    cuts: list[Cut],
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    phase: str,
) -> float:
    route_cost = 0.0 if phase == "phase1" else float(route.cost)
    value = (
        route_cost
        - sum(float(duals.cover[task]) for task in route.task_set)
        - sum(float(duals.task_vehicle.get((int(task), int(vehicle)), 0.0)) for task in route.task_set)
        - float(duals.sortie_count[vehicle])
        - float(duals.vehicle_time[vehicle]) * route_work_time_lower_bound(data, route)
    )
    for cut in cuts:
        coeff = cut.coefficient(route, vehicle)
        if coeff:
            value -= float(duals.cuts.get(cut.id, 0.0)) * coeff
    for index, constraint in enumerate(branch_constraints):
        coeff = route_branch_coefficient(route, vehicle, constraint)
        if coeff:
            value -= float(duals.branches.get(index, 0.0)) * coeff
    return value


def _branch_pricing_state(
    tasks: tuple[int, ...],
    task_bits: dict[int, int],
    vehicle: int,
    constraints: tuple[BranchConstraint, ...],
) -> tuple[bool, int, dict[int, int], set[tuple[int, int]], list[int]]:
    """中文注释：把 branching 约束预编译成 pricing 内层循环可用的轻量结构。"""

    vehicle_disabled = False
    forbidden_task_mask = 0
    separate_masks = {int(task): 0 for task in tasks}
    arc_off_pairs: set[tuple[int, int]] = set()
    together_masks: list[int] = []

    for constraint in constraints:
        if constraint.kind == "vehicle_use_off":
            if int(vehicle) == int(constraint.vehicle):
                vehicle_disabled = True
        elif constraint.kind == "vehicle_use_on":
            continue
        elif constraint.kind == "task_vehicle_on":
            task = int(constraint.task_i)
            if int(vehicle) != int(constraint.vehicle):
                forbidden_task_mask |= task_bits.get(task, 0)
        elif constraint.kind == "task_vehicle_off":
            task = int(constraint.task_i)
            if int(vehicle) == int(constraint.vehicle):
                forbidden_task_mask |= task_bits.get(task, 0)
        elif constraint.kind == "ryan_separate":
            assert constraint.task_j is not None
            left = int(constraint.task_i)
            right = int(constraint.task_j)
            left_bit = task_bits.get(left, 0)
            right_bit = task_bits.get(right, 0)
            if left in separate_masks:
                separate_masks[left] |= right_bit
            if right in separate_masks:
                separate_masks[right] |= left_bit
        elif constraint.kind == "ryan_together":
            assert constraint.task_j is not None
            together_masks.append(task_bits.get(int(constraint.task_i), 0) | task_bits.get(int(constraint.task_j), 0))
        elif constraint.kind == "arc_off":
            assert constraint.task_j is not None
            arc_off_pairs.add((int(constraint.task_i), int(constraint.task_j)))
        elif constraint.kind == "arc_on":
            continue
        else:
            raise ValueError(f"未知 branching constraint: {constraint.kind}")

    return vehicle_disabled, forbidden_task_mask, separate_masks, arc_off_pairs, together_masks


def _route_satisfies_together_constraints(visited_mask: int, together_masks: list[int]) -> bool:
    for pair_mask in together_masks:
        hit = visited_mask & pair_mask
        if hit and hit != pair_mask:
            return False
    return True


def _label_prefix_score(label: Label, *, phase: str, vehicle_time_dual: float, rho: float) -> float:
    route_cost = 0.0 if phase == "phase1" else float(label.cost)
    work_time = float(label.travel_time) + float(label.service_time) + float(label.energy) / float(rho)
    return route_cost - float(label.task_dual_sum) - float(vehicle_time_dual) * work_time


def _dominates(left: tuple[float, float, float, float], right: tuple[float, float, float, float], tol: float) -> bool:
    left_time, left_load, left_energy, left_score = left
    right_time, right_load, right_energy, right_score = right
    return (
        left_time <= right_time + tol
        and left_load <= right_load + tol
        and left_energy <= right_energy + tol
        and left_score <= right_score + tol
    )


def _signature_prefix_masks(signatures: set[tuple[int, ...]]) -> dict[tuple[int, ...], int]:
    prefix_masks: dict[tuple[int, ...], int] = {}
    for index, signature in enumerate(sorted(signatures)):
        bit = 1 << index
        for length in range(len(signature) + 1):
            prefix = signature[:length]
            prefix_masks[prefix] = prefix_masks.get(prefix, 0) | bit
    return prefix_masks


def _append_unique(selected: list[Candidate], seen: set[tuple[int, ...]], item: Candidate, limit: int) -> bool:
    if len(selected) >= limit:
        return False
    signature = item[1].signature
    if signature in seen:
        return False
    selected.append(item)
    seen.add(signature)
    return True


def _select_by_reduced_cost(candidates: list[Candidate], limit: int) -> list[Candidate]:
    ordered = sorted(candidates, key=lambda item: (item[0], len(item[1].tasks), item[1].signature))
    if limit > 0:
        return ordered[:limit]
    return ordered


def _select_diverse_candidates(data: BPCData, candidates: list[Candidate], limit: int) -> list[Candidate]:
    ordered = _select_by_reduced_cost(candidates, 0)
    if limit <= 0 or len(ordered) <= limit:
        return ordered

    selected: list[Candidate] = []
    seen: set[tuple[int, ...]] = set()

    # 中文注释：先保留 reduced cost 最好的列，保证主要下降方向不丢失。
    low_rc_quota = max(1, int(limit * 0.50))
    for item in ordered[:low_rc_quota]:
        _append_unique(selected, seen, item, limit)

    per_task: dict[int, list[Candidate]] = {int(task): [] for task in data.tasks}
    by_size: dict[str, list[Candidate]] = {"single": [], "pair": [], "triple": [], "multi": []}
    per_task_keep = max(2, min(8, limit // max(1, len(data.tasks))))
    size_keep = max(8, limit // 8)
    for item in ordered:
        route = item[1]
        size = len(route.tasks)
        if size <= 1:
            bucket = "single"
        elif size == 2:
            bucket = "pair"
        elif size == 3:
            bucket = "triple"
        else:
            bucket = "multi"
        if len(by_size[bucket]) < size_keep:
            by_size[bucket].append(item)
        for task in route.task_set:
            task_items = per_task.get(int(task))
            if task_items is not None and len(task_items) < per_task_keep:
                task_items.append(item)

    # 中文注释：每个任务至少尝试带入若干负 reduced-cost 路线，避免只注入相似的大路线。
    per_task_quota = max(1, int(limit * 0.25))
    while len(selected) < min(limit, low_rc_quota + per_task_quota):
        changed = False
        for task in data.tasks:
            task_items = per_task[int(task)]
            while task_items:
                if _append_unique(selected, seen, task_items.pop(0), limit):
                    changed = True
                    break
            if len(selected) >= min(limit, low_rc_quota + per_task_quota):
                break
        if not changed:
            break

    # 中文注释：补充不同路线长度的列，给后续 cut 和 branching 更多结构。
    for bucket in ("single", "pair", "triple", "multi"):
        for item in by_size[bucket]:
            _append_unique(selected, seen, item, limit)
            if len(selected) >= limit:
                return selected

    for item in ordered:
        _append_unique(selected, seen, item, limit)
        if len(selected) >= limit:
            break
    return selected


def _select_pricing_candidates(
    data: BPCData,
    candidate_by_signature: dict[tuple[int, ...], Candidate],
    *,
    limit: int,
    selection_mode: str,
) -> list[Candidate]:
    candidates = list(candidate_by_signature.values())
    if selection_mode == "diverse":
        return _select_diverse_candidates(data, candidates, limit)
    return _select_by_reduced_cost(candidates, limit)


def exact_pricing(
    data: BPCData,
    routes: list[RouteColumn],
    duals: RMPDuals,
    cuts: list[Cut],
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    phase: str,
    eps: float,
    max_routes_to_return: int,
    max_labels: int = 0,
    selection_mode: str = "reduced_cost",
    dominance_enabled: bool = False,
) -> PricingResult:
    existing_signatures = {route.signature for route in routes}
    candidate_by_signature: dict[tuple[int, ...], tuple[float, RouteColumn]] = {}
    best_reduced_cost: float | None = None
    label_pops = 0
    generated_labels = 0
    dominance_pruned = 0
    dominance_tol = 1.0e-9
    exhausted = True

    # 中文注释：exactness 来自完整枚举 elementary sequence；下面的预计算只减少字典查询和重复 route 重建。
    tasks = tuple(int(task) for task in data.tasks)
    task_bits = {task: 1 << index for index, task in enumerate(tasks)}
    ready = {task: data.task_value(task, "r") for task in tasks}
    due = {task: data.task_value(task, "D") for task in tasks}
    service_time = {task: data.task_value(task, "sigma") for task in tasks}
    demand = {task: data.task_value(task, "d") for task in tasks}
    service_energy = {task: data.task_value(task, "g") for task in tasks}
    service_cost = {task: data.task_value(task, "c_srv") for task in tasks}
    arc_tau: dict[tuple[int, int], float] = {}
    arc_energy: dict[tuple[int, int], float] = {}
    arc_cost: dict[tuple[int, int], float] = {}
    for left in (0, *tasks):
        for right in (0, *tasks):
            if left == right:
                continue
            segment = data.arc(left, right)
            arc_tau[(left, right)] = float(segment["tau"])
            arc_energy[(left, right)] = float(segment["energy"])
            arc_cost[(left, right)] = float(segment["cost"])

    cut_specs: list[tuple[str, int | None, frozenset[int], set[tuple[int, ...]], float, int]] = []
    crossing_specs: list[tuple[frozenset[int], float]] = []
    for cut in cuts:
        dual = float(duals.cuts.get(cut.id, 0.0))
        if dual == 0.0:
            continue
        if cut.kind in SIGNATURE_CUT_KINDS:
            cut_specs.append((cut.kind, int(cut.vehicle), frozenset(), set(cut.signatures), dual, 0))
        elif cut.kind == "crossing_cut":
            subset = frozenset(int(task) for task in cut.tasks)
            cut_specs.append((cut.kind, None, subset, set(), dual, len(crossing_specs)))
            crossing_specs.append((subset, dual))
        elif cut.kind == "schedule_capacity":
            mask = 0
            for task in cut.tasks:
                mask |= task_bits.get(int(task), 0)
            cut_specs.append((cut.kind, int(cut.vehicle), frozenset(int(task) for task in cut.tasks), set(), dual, mask))
        else:
            raise ValueError(f"未知 cut kind: {cut.kind}")

    arc_on_duals = [
        (index, int(constraint.task_i), int(constraint.task_j), float(duals.branches.get(index, 0.0)))
        for index, constraint in enumerate(branch_constraints)
        if constraint.kind == "arc_on" and constraint.task_j is not None and float(duals.branches.get(index, 0.0)) != 0.0
    ]
    active_dominance = bool(dominance_enabled)

    for vehicle in data.vehicles:
        (
            vehicle_disabled,
            forbidden_task_mask,
            separate_masks,
            arc_off_pairs,
            together_masks,
        ) = _branch_pricing_state(tasks, task_bits, int(vehicle), branch_constraints)
        if vehicle_disabled:
            continue

        task_dual = {
            task: float(duals.cover[task]) + float(duals.task_vehicle.get((int(task), int(vehicle)), 0.0))
            for task in tasks
        }
        sortie_dual = float(duals.sortie_count[vehicle])
        vehicle_time_dual = float(duals.vehicle_time[vehicle])
        signature_signatures = {
            signature
            for kind, cut_vehicle, _cut_tasks, cut_signatures, _cut_dual, _cut_mask in cut_specs
            if kind in SIGNATURE_CUT_KINDS and int(cut_vehicle or -1) == int(vehicle)
            for signature in cut_signatures
        }
        signature_prefix_masks = _signature_prefix_masks(signature_signatures)
        initial_signature_prefix_mask = signature_prefix_masks.get(tuple(), 0)
        dominance: dict[tuple[int, int, tuple[int, ...], int, int], list[tuple[float, float, float, float]]] = {}
        queue: list[Label] = [
            Label(
                0.0,
                0,
                tuple(),
                0,
                tuple(0 for _subset, _dual in crossing_specs),
                0,
                initial_signature_prefix_mask,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            )
        ]
        while queue:
            if max_labels > 0 and label_pops >= max_labels:
                exhausted = False
                break
            label = heapq.heappop(queue)
            label_pops += 1
            for task in tasks:
                task_bit = task_bits[task]
                if label.visited_mask & task_bit:
                    continue
                if forbidden_task_mask & task_bit:
                    continue
                if label.visited_mask & separate_masks[task]:
                    continue
                if (int(label.node), int(task)) in arc_off_pairs:
                    continue
                next_sequence = (*label.sequence, int(task))

                segment_tau = arc_tau[(int(label.node), int(task))]
                arrival = label.time + segment_tau
                start = max(ready[task], arrival)
                finish = start + service_time[task]
                if finish > due[task] + 1.0e-9:
                    continue
                next_load = label.load + demand[task]
                if next_load > data.capacity + 1.0e-9:
                    continue
                next_energy = label.energy + arc_energy[(int(label.node), int(task))] + service_energy[task]
                if next_energy > data.energy_limit + 1.0e-9:
                    continue
                return_time = finish + arc_tau[(int(task), 0)]
                total_energy = next_energy + arc_energy[(int(task), 0)]
                if return_time > data.horizon + 1.0e-9 or total_energy > data.energy_limit + 1.0e-9:
                    continue

                next_cost = label.cost + arc_cost[(int(label.node), int(task))] + service_cost[task]
                next_travel_time = label.travel_time + segment_tau
                next_service_time = label.service_time + service_time[task]
                next_task_dual_sum = label.task_dual_sum + task_dual[task]
                next_visited_mask = label.visited_mask | task_bit
                if crossing_specs:
                    crossing_counts = tuple(
                        count
                        + int(((int(label.node) in subset) if int(label.node) != 0 else False) != (int(task) in subset))
                        for count, (subset, _dual) in zip(label.crossing_counts, crossing_specs)
                    )
                else:
                    crossing_counts = tuple()
                arc_on_mask = label.arc_on_mask
                for arc_index, (_branch_index, tail, head, _branch_dual) in enumerate(arc_on_duals):
                    if int(label.node) == int(tail) and int(task) == int(head):
                        arc_on_mask |= 1 << arc_index
                signature_prefix_mask = signature_prefix_masks.get(next_sequence, 0)
                next_label = Label(
                    priority=(0.0 if phase == "phase1" else next_cost) - next_task_dual_sum,
                    node=int(task),
                    sequence=next_sequence,
                    visited_mask=next_visited_mask,
                    crossing_counts=crossing_counts,
                    arc_on_mask=arc_on_mask,
                    signature_prefix_mask=signature_prefix_mask,
                    time=finish,
                    load=next_load,
                    energy=next_energy,
                    travel_time=next_travel_time,
                    cost=next_cost,
                    service_time=next_service_time,
                    task_dual_sum=next_task_dual_sum,
                )
                generated_labels += 1

                if next_sequence not in existing_signatures and _route_satisfies_together_constraints(
                    next_visited_mask, together_masks
                ):
                    route_cost = 0.0 if phase == "phase1" else _round(next_cost + arc_cost[(int(task), 0)])
                    route_travel_time = _round(next_travel_time + arc_tau[(int(task), 0)])
                    route_energy = _round(total_energy)
                    work_time = route_travel_time + next_service_time + route_energy / data.rho
                    rc = route_cost - next_task_dual_sum - sortie_dual - vehicle_time_dual * work_time

                    for kind, cut_vehicle, cut_tasks, cut_signatures, cut_dual, cut_mask in cut_specs:
                        if cut_vehicle is not None and int(cut_vehicle) != int(vehicle):
                            continue
                        if kind in SIGNATURE_CUT_KINDS:
                            if next_sequence in cut_signatures:
                                rc -= cut_dual
                        elif kind == "crossing_cut":
                            crossing_index = int(cut_mask)
                            coeff = float(crossing_counts[crossing_index])
                            if int(task) in cut_tasks:
                                coeff += 1.0
                            if coeff:
                                rc -= cut_dual * coeff
                        elif kind == "schedule_capacity":
                            coeff = float((next_visited_mask & int(cut_mask)).bit_count())
                            if coeff:
                                rc -= cut_dual * coeff

                    for arc_index, (_index, _tail, _head, branch_dual) in enumerate(arc_on_duals):
                        if arc_on_mask & (1 << arc_index):
                            rc -= branch_dual

                    best_reduced_cost = rc if best_reduced_cost is None else min(best_reduced_cost, rc)
                    if rc < -eps:
                        route = evaluate_route(data, next_sequence)
                        if route is not None and route_allowed_by_branch(route, vehicle, branch_constraints):
                            actual_rc = reduced_cost(data, route, vehicle, duals, cuts, branch_constraints, phase=phase)
                            best_reduced_cost = min(best_reduced_cost, actual_rc)
                            if actual_rc < -eps:
                                current = candidate_by_signature.get(route.signature)
                                if current is None or actual_rc < current[0]:
                                    candidate_by_signature[route.signature] = (actual_rc, route)

                if active_dominance:
                    key = (next_visited_mask, int(task), crossing_counts, arc_on_mask, signature_prefix_mask)
                    score = _label_prefix_score(
                        next_label,
                        phase=phase,
                        vehicle_time_dual=vehicle_time_dual,
                        rho=data.rho,
                    )
                    item = (float(finish), float(next_load), float(next_energy), float(score))
                    bucket = dominance.get(key, [])
                    if any(_dominates(existing, item, dominance_tol) for existing in bucket):
                        dominance_pruned += 1
                        continue
                    dominance[key] = [
                        existing for existing in bucket if not _dominates(item, existing, dominance_tol)
                    ]
                    dominance[key].append(item)
                heapq.heappush(queue, next_label)
        if not exhausted:
            break

    candidates = _select_pricing_candidates(
        data,
        candidate_by_signature,
        limit=int(max_routes_to_return),
        selection_mode=str(selection_mode),
    )
    return PricingResult(
        routes=[route for _rc, route in candidates],
        exhausted=exhausted,
        best_reduced_cost=best_reduced_cost,
        label_pops=label_pops,
        generated_labels=generated_labels,
        negative_routes=len(candidate_by_signature),
        dominance_enabled=active_dominance,
        dominance_pruned=dominance_pruned,
    )
