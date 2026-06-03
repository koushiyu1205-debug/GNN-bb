"""Exact-safe fleet upper-bound override for BPC_future."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
import itertools
import math
from typing import Any

from BPC_future.core.columns import TimedTrip, candidate_start_times_for_trip, evaluate_timed_trip
from BPC_future.core.data import FutureData


@dataclass(frozen=True)
class FleetBoundDiagnostics:
    mode: str
    old_R_bar: int
    new_R_bar: int
    heuristic_R: int | None
    heuristic_UB: float | None
    unavoidable_cost_lb: float
    cost_safe: bool
    reason: str

    def payload(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "old_R_bar": self.old_R_bar,
            "new_R_bar": self.new_R_bar,
            "heuristic_R": self.heuristic_R,
            "heuristic_UB": None if self.heuristic_UB is None else round(float(self.heuristic_UB), 6),
            "unavoidable_cost_lb": round(float(self.unavoidable_cost_lb), 6),
            "cost_safe": self.cost_safe,
            "reason": self.reason,
        }


def apply_fleet_bound_override(data: FutureData, config: dict[str, Any]) -> tuple[FutureData, FleetBoundDiagnostics]:
    mode = str(config.get("fleet_bound_mode", "fixed")).lower()
    old = len(data.vehicles)
    if mode != "computed":
        return data, FleetBoundDiagnostics(
            mode=mode,
            old_R_bar=old,
            new_R_bar=old,
            heuristic_R=None,
            heuristic_UB=None,
            unavoidable_cost_lb=0.0,
            cost_safe=True,
            reason="fixed",
        )

    heuristic = constructive_fleet_schedule(data, config)
    task_count = max(1, len(data.tasks))
    max_override = config.get("fleet_bound_max")
    try:
        unavoidable_lb = unavoidable_nonvehicle_cost_lb(data)
    except Exception:
        unavoidable_lb = 0.0
    if heuristic is None:
        chosen = task_count
        reason = "heuristic_failed_fallback_task_count"
        cost_safe = False
        heuristic_R = None
        heuristic_UB = None
    else:
        heuristic_R, heuristic_UB = heuristic
        slack = int(config.get("fleet_bound_slack", 1))
        target = min(task_count, max(heuristic_R, heuristic_R + max(0, slack)))
        fixed_cost = max(0.0, float(data.fixed_vehicle_cost))
        tol = float(config.get("integer_tol", 1.0e-6))
        if not bool(config.get("fleet_bound_cost_safe", True)):
            chosen = target
            reason = "cost_safety_disabled"
            cost_safe = False
        elif fixed_cost <= 1.0e-12:
            chosen = task_count
            reason = "zero_fixed_cost_fallback_task_count"
            cost_safe = True
        else:
            candidate_vehicle_count = int(target) + 1
            try:
                candidate_unavoidable_lb = unavoidable_nonvehicle_cost_lb(
                    data,
                    min_nonempty_vehicles=candidate_vehicle_count,
                )
            except Exception:
                candidate_unavoidable_lb = unavoidable_lb
            if math.isfinite(candidate_unavoidable_lb):
                unavoidable_lb = max(float(unavoidable_lb), float(candidate_unavoidable_lb))
            if candidate_vehicle_count * fixed_cost + candidate_unavoidable_lb >= heuristic_UB - tol:
                chosen = target
                reason = "target_plus_one_fixed_cost_plus_conditional_unavoidable_lb_dominates_heuristic_UB"
                cost_safe = True
            else:
                residual = max(0.0, heuristic_UB - unavoidable_lb)
                chosen = min(task_count, max(heuristic_R, int(math.floor(residual / fixed_cost))))
                reason = "objective_safe_floor_residual_UB_over_fixed_cost"
                cost_safe = True
    if max_override is not None:
        cap = int(max_override)
        if heuristic is None:
            chosen = min(chosen, max(1, cap))
            reason += "_capped"
        elif cap >= int(heuristic_R):
            chosen = min(chosen, cap)
            reason += "_capped"
        else:
            reason += "_cap_ignored_below_heuristic_R"
    chosen = max(1, min(task_count, int(chosen)))
    updated = _replace_vehicle_count(data, chosen)
    return updated, FleetBoundDiagnostics(
        mode=mode,
        old_R_bar=old,
        new_R_bar=chosen,
        heuristic_R=heuristic_R,
        heuristic_UB=heuristic_UB,
        unavoidable_cost_lb=unavoidable_lb,
        cost_safe=cost_safe,
        reason=reason,
    )


def constructive_fleet_schedule(data: FutureData, config: dict[str, Any]) -> tuple[int, float] | None:
    bucket = float(config.get("time_bucket_size", 5.0))
    start_step = float(config.get("pricing_start_time_step", max(5.0, bucket)))
    try:
        candidates_by_task = _single_task_candidates(data, bucket=bucket, start_step=start_step)
    except Exception:
        return None
    if any(not candidates_by_task.get(task) for task in data.tasks):
        return None
    task_order = sorted(
        data.tasks,
        key=lambda task: (
            len(candidates_by_task[int(task)]),
            data.task_value(int(task), "D"),
            data.task_value(int(task), "r"),
            int(task),
        ),
    )
    for vehicle_count in range(1, len(data.tasks) + 1):
        assignment = _try_pack_single_task_trips(data, candidates_by_task, task_order, vehicle_count)
        if assignment is not None:
            used = sum(1 for trips in assignment if trips)
            cost = used * float(data.fixed_vehicle_cost) + sum(trip.cost for trips in assignment for trip in trips)
            return used, float(cost)
    return None


def unavoidable_nonvehicle_cost_lb(data: FutureData, *, min_nonempty_vehicles: int | None = None) -> float:
    """Return an objective lower bound that excludes fixed vehicle costs.

    The bound is intentionally one-sided.  It may underestimate the best
    nonvehicle cost, but it must never overestimate it because downstream
    fleet-limit cuts use it to prove that extra vehicles cannot improve the
    incumbent.
    """
    service_cost = sum(data.task_value(task, "c_srv") for task in data.tasks)
    inbound_sum = 0.0
    outbound_sum = 0.0
    for task in data.tasks:
        inbound = min(
            _min_arc_cost(data, source, task)
            for source in (0, *data.tasks)
            if int(source) != int(task) and (int(source), int(task)) in data.arc_options
        )
        outbound = min(
            _min_arc_cost(data, task, target)
            for target in (0, *data.tasks)
            if int(target) != int(task) and (int(task), int(target)) in data.arc_options
        )
        inbound_sum += inbound
        outbound_sum += outbound
    degree_lb = float(service_cost + max(inbound_sum, outbound_sum))
    assignment_lb = _sortie_path_assignment_nonvehicle_lb(
        data,
        service_cost,
        min_nonempty_sorties=min_nonempty_vehicles,
    )
    return float(max(degree_lb, assignment_lb))


def _sortie_path_assignment_nonvehicle_lb(
    data: FutureData,
    service_cost: float | None = None,
    *,
    min_nonempty_sorties: int | None = None,
) -> float:
    """Assignment-relaxation lower bound for a set of depot-to-depot sorties.

    For a fixed number q of nonempty sorties, any feasible multi-sortie
    schedule induces q depot starts, q depot returns, and every task has one
    predecessor and one successor.  Replicating the depot q times gives a
    bipartite assignment relaxation.  It still permits disconnected task
    cycles, so it is a relaxation and therefore a lower bound.

    A schedule may use more than the minimum number of sorties, so the valid
    lower bound is the minimum assignment value over q in [K, n].
    """
    tasks = tuple(int(task) for task in data.tasks)
    if not tasks:
        return 0.0
    if service_cost is None:
        service_cost = sum(data.task_value(task, "c_srv") for task in tasks)
    min_sorties = _minimum_sortie_count_lb(data)
    if min_nonempty_sorties is not None:
        min_sorties = max(min_sorties, int(min_nonempty_sorties))
    if min_sorties > len(tasks):
        return math.inf
    best = math.inf
    for sortie_count in range(min_sorties, len(tasks) + 1):
        value = _sortie_path_assignment_travel_lb(data, sortie_count)
        if value < best:
            best = value
    if not math.isfinite(best):
        return float(service_cost)
    return float(service_cost + best)


def _minimum_sortie_count_lb(data: FutureData) -> int:
    if not data.tasks:
        return 0
    total_demand = sum(max(0.0, data.task_value(task, "d")) for task in data.tasks)
    if data.capacity <= 1.0e-12:
        return len(data.tasks)
    return max(1, min(len(data.tasks), int(math.ceil(total_demand / float(data.capacity) - 1.0e-12))))


def _sortie_path_assignment_travel_lb(data: FutureData, sortie_count: int) -> float:
    tasks = tuple(int(task) for task in data.tasks)
    q = int(sortie_count)
    if q <= 0:
        return 0.0 if not tasks else math.inf
    if q > len(tasks):
        return math.inf

    # Left side: q depot-start copies followed by task predecessor nodes.
    # Right side: task successor nodes followed by q depot-end copies.
    size = len(tasks) + q
    inf = 1.0e12
    matrix = [[inf for _ in range(size)] for _ in range(size)]
    for left in range(size):
        for right in range(size):
            if left < q and right < len(tasks):
                matrix[left][right] = _min_arc_cost(data, 0, tasks[right])
            elif left >= q and right >= len(tasks):
                matrix[left][right] = _min_arc_cost(data, tasks[left - q], 0)
            elif left >= q and right < len(tasks):
                source = tasks[left - q]
                target = tasks[right]
                if source != target:
                    matrix[left][right] = _min_arc_cost(data, source, target)
            # depot-start to depot-end is intentionally infeasible: each of the
            # q depot starts must open a nonempty relaxed path.
    value = _hungarian_min_cost(matrix, inf=inf)
    if value >= inf / 2:
        return math.inf
    return float(value)


def _min_arc_cost(data: FutureData, i: int, j: int) -> float:
    try:
        return float(min(option.cost for option in data.options(int(i), int(j))))
    except Exception:
        return math.inf


def _hungarian_min_cost(cost: list[list[float]], *, inf: float = 1.0e12) -> float:
    """Solve a square minimum-cost assignment with the Hungarian algorithm."""
    n = len(cost)
    if n == 0:
        return 0.0
    if any(len(row) != n for row in cost):
        raise ValueError("Hungarian input must be square")
    u = [0.0] * (n + 1)
    v = [0.0] * (n + 1)
    p = [0] * (n + 1)
    way = [0] * (n + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [math.inf] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = math.inf
            j1 = 0
            for j in range(1, n + 1):
                if used[j]:
                    continue
                cur = float(cost[i0 - 1][j - 1]) - u[i0] - v[j]
                if cur < minv[j]:
                    minv[j] = cur
                    way[j] = j0
                if minv[j] < delta:
                    delta = minv[j]
                    j1 = j
            if not math.isfinite(delta):
                return math.inf
            for j in range(0, n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    assignment = [0] * (n + 1)
    for j in range(1, n + 1):
        assignment[p[j]] = j
    value = 0.0
    for i in range(1, n + 1):
        value += float(cost[i - 1][assignment[i] - 1])
    if value >= inf / 2:
        return math.inf
    return float(value)


def _single_task_candidates(data: FutureData, *, bucket: float, start_step: float) -> dict[int, list[TimedTrip]]:
    candidates: dict[int, list[TimedTrip]] = {}
    max_per_task = 300
    for task in data.tasks:
        trips: list[TimedTrip] = []
        for outbound, inbound in itertools.product(data.options(0, task), data.options(task, 0)):
            options = (outbound, inbound)
            for start in candidate_start_times_for_trip(data, (task,), options, start_step=start_step):
                trip = evaluate_timed_trip(
                    data,
                    (task,),
                    start,
                    time_bucket_size=bucket,
                    arc_options=options,
                    include_physical_paths=False,
                )
                if trip is not None:
                    trips.append(trip)
        trips.sort(key=lambda trip: (trip.end_time, trip.start_time, trip.cost, trip.arc_option_ids))
        candidates[int(task)] = trips[:max_per_task]
    return candidates


def _try_pack_single_task_trips(
    data: FutureData,
    candidates_by_task: dict[int, list[TimedTrip]],
    task_order: list[int],
    vehicle_count: int,
) -> list[list[TimedTrip]] | None:
    assignment: list[list[TimedTrip]] = [[] for _ in range(vehicle_count)]
    for task in task_order:
        chosen_vehicle: int | None = None
        chosen_trip: TimedTrip | None = None
        for vehicle_index, trips in enumerate(assignment):
            if len(trips) >= data.sortie_limit:
                continue
            for trip in candidates_by_task[int(task)]:
                if _compatible_with_vehicle(trip, trips):
                    chosen_vehicle = vehicle_index
                    chosen_trip = trip
                    break
            if chosen_trip is not None:
                break
        if chosen_vehicle is None or chosen_trip is None:
            return None
        assignment[chosen_vehicle].append(chosen_trip)
        assignment[chosen_vehicle].sort(key=lambda item: (item.start_time, item.end_time, item.tasks))
    return assignment


def _compatible_with_vehicle(candidate: TimedTrip, selected: list[TimedTrip]) -> bool:
    for trip in selected:
        if candidate.start_time < trip.end_time - 1.0e-9 and trip.start_time < candidate.end_time - 1.0e-9:
            return False
    return True


def _replace_vehicle_count(data: FutureData, count: int) -> FutureData:
    instance = deepcopy(data.instance)
    instance.setdefault("vehicles", {})["R_bar"] = int(count)
    instance.setdefault("vehicle", {})["fleet_size"] = int(count)
    instance["vehicle"]["R_bar"] = int(count)
    return replace(data, instance=instance, vehicles=tuple(range(1, int(count) + 1)))
