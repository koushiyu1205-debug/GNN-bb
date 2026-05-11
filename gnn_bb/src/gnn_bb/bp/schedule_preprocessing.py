"""中文摘要：本文件实现 vehicle schedule pricing 前的确定性可行性预处理。它提前识别 depot-task、task-task、task-depot 中永远不可能可行的连接，供标签 DP 在扩展前快速剪枝。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from gnn_bb.data.instances import task_ids
from gnn_bb.data.terrain import arc_key


TOL = 1.0e-9


def _task_value(instance: dict[str, Any], task_id: int, field_name: str) -> float:
    return float(instance["tasks"][str(task_id)][field_name])


@dataclass
class SchedulePreprocessResult:
    # 中文注释：这些集合只删除确定不可能可行的连接；后续 DP 仍会做完整资源检查。
    single_task_feasible: set[int]
    single_task_infeasible_reasons: dict[int, list[str]]
    depot_to_task_feasible: set[int]
    task_to_depot_feasible: set[int]
    task_successors: dict[int, tuple[int, ...]]
    deleted_task_arc_reasons: dict[str, int] = field(default_factory=dict)

    def task_arc_feasible(self, source: int, target: int) -> bool:
        return int(target) in self.task_successors.get(int(source), tuple())

    def to_report(self) -> dict[str, Any]:
        total_arcs = sum(len(successors) for successors in self.task_successors.values())
        infeasible_reasons = {
            str(task_id): list(reasons)
            for task_id, reasons in sorted(self.single_task_infeasible_reasons.items())
        }
        return {
            "single_task_feasible": len(self.single_task_feasible),
            "single_task_infeasible": len(self.single_task_infeasible_reasons),
            "single_task_infeasible_reasons": infeasible_reasons,
            "depot_to_task_feasible": len(self.depot_to_task_feasible),
            "task_to_depot_feasible": len(self.task_to_depot_feasible),
            "task_task_feasible_arcs": total_arcs,
            "deleted_task_arc_reasons": dict(sorted(self.deleted_task_arc_reasons.items())),
        }


def _record_reason(reasons: dict[str, int], reason: str) -> None:
    reasons[reason] = reasons.get(reason, 0) + 1


def _check_depot_to_task(instance: dict[str, Any], pairwise: dict[str, dict[str, Any]], task_id: int) -> tuple[bool, list[str]]:
    vehicles = instance["vehicles"]
    reasons: list[str] = []
    outbound = pairwise[arc_key(0, task_id)]
    arrival = float(outbound["tau"])
    service_start = max(_task_value(instance, task_id, "r"), arrival)
    finish = service_start + _task_value(instance, task_id, "sigma")
    energy = float(outbound["energy"]) + _task_value(instance, task_id, "g")
    if finish > _task_value(instance, task_id, "D") + TOL:
        reasons.append("depot_to_task_time")
    if finish > float(vehicles["H"]) + TOL:
        reasons.append("depot_to_task_horizon")
    if _task_value(instance, task_id, "d") > float(vehicles["Q"]) + TOL:
        reasons.append("depot_to_task_capacity")
    if energy > float(vehicles["B_use"]) + TOL:
        reasons.append("depot_to_task_energy")
    return not reasons, reasons


def _min_arrival_lower_bounds(instance: dict[str, Any], pairwise: dict[str, dict[str, Any]], tasks: list[int]) -> dict[int, float]:
    bounds: dict[int, float] = {}
    for target in tasks:
        best = float(pairwise[arc_key(0, target)]["tau"])
        for source in tasks:
            if int(source) == int(target):
                continue
            source_finish_lb = _task_value(instance, source, "r") + _task_value(instance, source, "sigma")
            best = min(best, source_finish_lb + float(pairwise[arc_key(source, target)]["tau"]))
        bounds[int(target)] = best
    return bounds


def _min_energy_before_bounds(instance: dict[str, Any], pairwise: dict[str, dict[str, Any]], tasks: list[int]) -> dict[int, float]:
    bounds: dict[int, float] = {}
    for target in tasks:
        best = float(pairwise[arc_key(0, target)]["energy"])
        for source in tasks:
            if int(source) == int(target):
                continue
            best = min(best, _task_value(instance, source, "g") + float(pairwise[arc_key(source, target)]["energy"]))
        bounds[int(target)] = best
    return bounds


def _min_energy_after_bounds(instance: dict[str, Any], pairwise: dict[str, dict[str, Any]], tasks: list[int]) -> dict[int, float]:
    bounds: dict[int, float] = {}
    for source in tasks:
        best = float(pairwise[arc_key(source, 0)]["energy"])
        for target in tasks:
            if int(source) == int(target):
                continue
            best = min(best, float(pairwise[arc_key(source, target)]["energy"]) + _task_value(instance, target, "g"))
        bounds[int(source)] = best
    return bounds


def _earliest_finish_anywhere(instance: dict[str, Any], task_id: int, min_arrival: dict[int, float]) -> float:
    service_start = max(_task_value(instance, task_id, "r"), float(min_arrival[int(task_id)]))
    return service_start + _task_value(instance, task_id, "sigma")


def _check_task_to_depot(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    task_id: int,
    min_arrival: dict[int, float],
    min_energy_before: dict[int, float],
) -> tuple[bool, list[str]]:
    vehicles = instance["vehicles"]
    reasons: list[str] = []
    inbound = pairwise[arc_key(task_id, 0)]
    earliest_finish = _earliest_finish_anywhere(instance, task_id, min_arrival)
    energy = float(min_energy_before[int(task_id)]) + _task_value(instance, task_id, "g") + float(inbound["energy"])
    ready_time = earliest_finish + float(inbound["tau"]) + energy / float(vehicles["rho"])
    if earliest_finish > _task_value(instance, task_id, "D") + TOL:
        reasons.append("task_to_depot_task_time")
    if ready_time > float(vehicles["H"]) + TOL:
        reasons.append("task_to_depot_horizon")
    if _task_value(instance, task_id, "d") > float(vehicles["Q"]) + TOL:
        reasons.append("task_to_depot_capacity")
    if energy > float(vehicles["B_use"]) + TOL:
        reasons.append("task_to_depot_energy")
    return not reasons, reasons


def _check_single_task(instance: dict[str, Any], pairwise: dict[str, dict[str, Any]], task_id: int) -> tuple[bool, list[str]]:
    vehicles = instance["vehicles"]
    reasons: list[str] = []
    outbound = pairwise[arc_key(0, task_id)]
    inbound = pairwise[arc_key(task_id, 0)]
    arrival = float(outbound["tau"])
    service_start = max(_task_value(instance, task_id, "r"), arrival)
    finish = service_start + _task_value(instance, task_id, "sigma")
    energy = float(outbound["energy"]) + _task_value(instance, task_id, "g") + float(inbound["energy"])
    ready_time = finish + float(inbound["tau"]) + energy / float(vehicles["rho"])
    if finish > _task_value(instance, task_id, "D") + TOL:
        reasons.append("single_task_time")
    if ready_time > float(vehicles["H"]) + TOL:
        reasons.append("single_task_horizon")
    if _task_value(instance, task_id, "d") > float(vehicles["Q"]) + TOL:
        reasons.append("single_task_capacity")
    if energy > float(vehicles["B_use"]) + TOL:
        reasons.append("single_task_energy")
    return not reasons, reasons


def _check_task_arc(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    source: int,
    target: int,
    min_arrival: dict[int, float],
    min_energy_before: dict[int, float],
    min_energy_after: dict[int, float],
) -> tuple[bool, list[str]]:
    vehicles = instance["vehicles"]
    reasons: list[str] = []
    segment = pairwise[arc_key(source, target)]

    earliest_finish_source = _earliest_finish_anywhere(instance, source, min_arrival)
    latest_start_target = _task_value(instance, target, "D") - _task_value(instance, target, "sigma")
    earliest_arrival_target = earliest_finish_source + float(segment["tau"])
    earliest_start_target = max(_task_value(instance, target, "r"), earliest_arrival_target)
    earliest_finish_target = earliest_start_target + _task_value(instance, target, "sigma")

    if earliest_arrival_target > latest_start_target + TOL:
        reasons.append("task_arc_time")
    if _task_value(instance, source, "d") + _task_value(instance, target, "d") > float(vehicles["Q"]) + TOL:
        reasons.append("task_arc_capacity")
    if (
        float(min_energy_before[int(source)])
        + _task_value(instance, source, "g")
        + float(segment["energy"])
        + _task_value(instance, target, "g")
        + float(min_energy_after[int(target)])
        > float(vehicles["B_use"]) + TOL
    ):
        reasons.append("task_arc_energy")
    if earliest_finish_source > _task_value(instance, source, "D") + TOL:
        reasons.append("task_arc_source_time")
    if earliest_finish_target > _task_value(instance, target, "D") + TOL:
        reasons.append("task_arc_target_time")
    if earliest_finish_target > float(vehicles["H"]) + TOL:
        reasons.append("task_arc_horizon")

    return not reasons, reasons


def build_schedule_preprocess(instance: dict[str, Any], pairwise: dict[str, dict[str, Any]]) -> SchedulePreprocessResult:
    tasks = task_ids(instance)
    min_arrival = _min_arrival_lower_bounds(instance, pairwise, tasks)
    min_energy_before = _min_energy_before_bounds(instance, pairwise, tasks)
    min_energy_after = _min_energy_after_bounds(instance, pairwise, tasks)
    single_task_feasible: set[int] = set()
    single_task_infeasible_reasons: dict[int, list[str]] = {}
    depot_to_task_feasible: set[int] = set()
    task_to_depot_feasible: set[int] = set()
    task_successors: dict[int, list[int]] = {int(task_id): [] for task_id in tasks}
    deleted_task_arc_reasons: dict[str, int] = {}

    for task_id in tasks:
        single_ok, single_reasons = _check_single_task(instance, pairwise, task_id)
        if single_ok:
            single_task_feasible.add(int(task_id))
        else:
            single_task_infeasible_reasons[int(task_id)] = single_reasons

        depot_ok, _depot_reasons = _check_depot_to_task(instance, pairwise, task_id)
        if depot_ok:
            depot_to_task_feasible.add(int(task_id))

        return_ok, _return_reasons = _check_task_to_depot(instance, pairwise, task_id, min_arrival, min_energy_before)
        if return_ok:
            task_to_depot_feasible.add(int(task_id))

    for source in tasks:
        for target in tasks:
            if int(source) == int(target):
                continue
            arc_ok, arc_reasons = _check_task_arc(
                instance,
                pairwise,
                int(source),
                int(target),
                min_arrival,
                min_energy_before,
                min_energy_after,
            )
            if arc_ok:
                task_successors[int(source)].append(int(target))
                continue
            for reason in arc_reasons:
                _record_reason(deleted_task_arc_reasons, reason)

    return SchedulePreprocessResult(
        single_task_feasible=single_task_feasible,
        single_task_infeasible_reasons=single_task_infeasible_reasons,
        depot_to_task_feasible=depot_to_task_feasible,
        task_to_depot_feasible=task_to_depot_feasible,
        task_successors={task_id: tuple(sorted(successors)) for task_id, successors in task_successors.items()},
        deleted_task_arc_reasons=deleted_task_arc_reasons,
    )


def build_trivial_schedule_preprocess(instance: dict[str, Any]) -> SchedulePreprocessResult:
    """中文注释：用于 ablation；不做静态剪枝，只提供全连接候选图，完整可行性仍由 DP 检查。"""
    tasks = task_ids(instance)
    return SchedulePreprocessResult(
        single_task_feasible=set(tasks),
        single_task_infeasible_reasons={},
        depot_to_task_feasible=set(tasks),
        task_to_depot_feasible=set(tasks),
        task_successors={int(source): tuple(int(target) for target in tasks if int(target) != int(source)) for source in tasks},
        deleted_task_arc_reasons={},
    )
