"""Optional compact MILP oracles for lunar-ice fixed-graph experiments."""

from __future__ import annotations

from collections import defaultdict
from itertools import product
import math
from time import perf_counter
from typing import Iterable

from lunar_ice_bpc.exact.core.columns import build_timed_sortie
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn, build_journey_column
from lunar_ice_bpc.exact.core.objective import (
    aggregate_journey_objective_breakdown,
    objective_references,
    service_risk_value,
)
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals, manual_journey_reduced_cost
from lunar_ice_bpc.exact.solver.journey_driver import _nondominated_path_type_cache


def estimate_gurobi_compact_size(
    data: LunarIceData,
    *,
    max_sorties_per_vehicle: int | None = None,
) -> dict:
    tasks = tuple(data.task_ids)
    vehicle_count = int(data.fleet_size)
    slot_bound = _safe_sortie_slot_bound(data)
    sortie_slots = int(max_sorties_per_vehicle) if max_sorties_per_vehicle is not None else int(slot_bound["slot_count"])
    min_return_duration = float(slot_bound["min_return_duration_lower_bound"])
    min_active_duration = float(slot_bound["min_duration_lower_bound"])
    min_out_return_travel = float(slot_bound["min_out_return_travel_lower_bound"])
    nodes = ("depot", *tasks)
    path_type_cache, pruning = _time_window_feasible_path_type_cache(data, _nondominated_path_type_cache(data))
    arc_var_count = 0
    for _vehicle in range(vehicle_count):
        for _slot in range(sortie_slots):
            for source in nodes:
                for target in nodes:
                    if source == target or (source == "depot" and target == "depot"):
                        continue
                    arc_var_count += len(path_type_cache.get((str(source), str(target)), tuple()))
    y_count = vehicle_count * sortie_slots * len(tasks)
    z_count = vehicle_count * sortie_slots
    variable_count = arc_var_count + (2 * y_count) + (4 * z_count)
    constraint_count = (
        len(tasks)
        + 2 * vehicle_count * max(0, sortie_slots - 1)
        + vehicle_count * sortie_slots * (12 + 5 * len(tasks))
        + arc_var_count
    )
    return {
        "task_count": len(tasks),
        "vehicle_count": vehicle_count,
        "sortie_slots_per_vehicle": sortie_slots,
        "sortie_slot_bound_source": slot_bound["source"] if max_sorties_per_vehicle is None else "explicit",
        "sortie_slot_horizon_count_bound": slot_bound["horizon_slot_count_bound"],
        "sortie_slot_latest_start_count_bound": slot_bound["latest_start_slot_count_bound"],
        "sortie_slot_latest_service_start_upper_bound": slot_bound["latest_service_start_upper_bound"],
        "sortie_slot_min_depot_outbound_travel_lower_bound": slot_bound["min_depot_outbound_travel_lower_bound"],
        "sortie_slot_min_duration_lower_bound": slot_bound["min_duration_lower_bound"],
        "sortie_slot_min_return_duration_lower_bound": slot_bound["min_return_duration_lower_bound"],
        "sortie_slot_min_out_return_travel_lower_bound": slot_bound["min_out_return_travel_lower_bound"],
        "binary_arc_var_count": int(arc_var_count),
        **pruning,
        "task_assignment_var_count": int(y_count),
        "estimated_variable_count": int(variable_count),
        "estimated_constraint_count": int(constraint_count),
        "path_option_policy": str(data.path_option_policy_id),
    }


def _safe_sortie_slot_bound(data: LunarIceData, *, latest_service_start_bound: bool = True) -> dict:
    tasks = tuple(data.task_ids)
    if not tasks:
        return {
            "slot_count": 0,
            "source": "empty_instance",
            "horizon_slot_count_bound": 0,
            "latest_start_slot_count_bound": 0,
            "latest_service_start_upper_bound": 0.0,
            "min_depot_outbound_travel_lower_bound": 0.0,
            "min_return_duration_lower_bound": 0.0,
            "min_duration_lower_bound": 0.0,
            "min_out_return_travel_lower_bound": 0.0,
        }
    min_outbound = min(
        float(option.travel_time_min)
        for task_id in tasks
        for option in data.arcs[("depot", str(task_id))].values()
    )
    min_return = min(
        float(option.travel_time_min)
        for task_id in tasks
        for option in data.arcs[(str(task_id), "depot")].values()
    )
    min_service = min(float(task.service_time) for task in data.tasks.values())
    min_out_return_travel = max(1.0e-9, min_outbound + min_return)
    min_return_duration = max(1.0e-9, min_outbound + min_return + min_service)
    min_duration = max(
        1.0e-9,
        min_return_duration + float(data.dock_overhead_min),
    )
    horizon_slot_count = max(1, int(math.floor((float(data.horizon) + 1.0e-9) / min_duration)))
    latest_service_start = max(
        float(task.due_time) - float(task.service_time)
        for task in data.tasks.values()
    )
    latest_start_slot_count = max(
        1,
        int(math.floor((latest_service_start - min_outbound + 1.0e-9) / min_duration)) + 1,
    )
    if latest_service_start_bound:
        slot_count = min(len(tasks), horizon_slot_count, latest_start_slot_count)
        if slot_count == len(tasks):
            source = "task_count_bound"
        elif slot_count == latest_start_slot_count and latest_start_slot_count <= horizon_slot_count:
            source = "latest_service_start_min_active_sortie_duration_bound"
        else:
            source = "horizon_min_active_sortie_duration_bound"
    else:
        slot_count = min(len(tasks), horizon_slot_count)
        source = "task_count_bound" if slot_count == len(tasks) else "horizon_min_active_sortie_duration_bound"
    return {
        "slot_count": int(slot_count),
        "source": source,
        "latest_service_start_slot_bound_enabled": bool(latest_service_start_bound),
        "horizon_slot_count_bound": int(min(len(tasks), horizon_slot_count)),
        "latest_start_slot_count_bound": int(min(len(tasks), latest_start_slot_count)),
        "latest_service_start_upper_bound": round(float(latest_service_start), 9),
        "min_depot_outbound_travel_lower_bound": round(float(min_outbound), 9),
        "min_return_duration_lower_bound": round(float(min_return_duration), 9),
        "min_duration_lower_bound": round(float(min_duration), 9),
        "min_out_return_travel_lower_bound": round(float(min_out_return_travel), 9),
    }


def _time_arc_big_m(
    data: LunarIceData,
    *,
    travel: float,
    service: float = 0.0,
    source: str = "depot",
) -> float:
    if source != "depot" and source in data.tasks:
        task = data.tasks[source]
        latest_start = max(0.0, float(task.due_time) - float(task.service_time))
        return latest_start + float(service) + float(travel)
    return float(data.horizon) + float(service) + float(travel)


def _time_window_feasible_path_type_cache(
    data: LunarIceData,
    path_type_cache: dict[tuple[str, str], tuple[str, ...]],
) -> tuple[dict[tuple[str, str], tuple[str, ...]], dict]:
    feasible: dict[tuple[str, str], tuple[str, ...]] = {}
    total_count = 0
    pruned_count = 0
    for arc_key, path_types in path_type_cache.items():
        source, target = arc_key
        kept: list[str] = []
        for path_type in path_types:
            total_count += 1
            if _arc_option_time_window_impossible(data, source, target, path_type):
                pruned_count += 1
                continue
            kept.append(str(path_type))
        if kept:
            feasible[(str(source), str(target))] = tuple(kept)
    return feasible, {
        "time_window_arc_pruning_enabled": True,
        "time_window_arc_option_count": int(total_count),
        "time_window_impossible_arc_option_count": int(pruned_count),
    }


def _arc_option_time_window_impossible(
    data: LunarIceData,
    source: str,
    target: str,
    path_type: str,
) -> bool:
    source = str(source)
    target = str(target)
    if source == target or (source == "depot" and target == "depot"):
        return True
    option = data.option(source, target, path_type)
    travel = float(option.travel_time_min)
    if source == "depot":
        if target == "depot":
            return True
        latest_target_start = _latest_task_service_start(data, target)
        return travel > latest_target_start + 1.0e-9
    earliest_source_start = _earliest_task_service_start_lower_bound(data, source)
    source_task = data.tasks[source]
    if target == "depot":
        earliest_end = (
            earliest_source_start
            + float(source_task.service_time)
            + travel
            + float(data.dock_overhead_min)
        )
        return earliest_end > float(data.horizon) + 1.0e-9
    latest_target_start = _latest_task_service_start(data, target)
    earliest_target_start = earliest_source_start + float(source_task.service_time) + travel
    return earliest_target_start > latest_target_start + 1.0e-9


def _pricing_path_type_cache(
    data: LunarIceData,
    *,
    time_window_arc_pruning: bool = True,
) -> tuple[dict[tuple[str, str], tuple[str, ...]], dict]:
    base = _nondominated_path_type_cache(data)
    if time_window_arc_pruning:
        return _time_window_feasible_path_type_cache(data, base)
    total_count = sum(len(path_types) for path_types in base.values())
    return base, {
        "time_window_arc_pruning_enabled": False,
        "time_window_arc_option_count": int(total_count),
        "time_window_impossible_arc_option_count": 0,
    }


def _earliest_task_service_start_lower_bound(data: LunarIceData, task_id: str) -> float:
    task = data.tasks[str(task_id)]
    min_depot_outbound = min(
        float(option.travel_time_min)
        for option in data.arcs[("depot", str(task_id))].values()
    )
    return max(float(task.ready_time), min_depot_outbound)


def _latest_task_service_start(data: LunarIceData, task_id: str) -> float:
    task = data.tasks[str(task_id)]
    return float(task.due_time) - float(task.service_time)


def solve_gurobi_compact_fixed_graph(
    data: LunarIceData,
    *,
    time_limit_sec: float | None = None,
    max_sorties_per_vehicle: int | None = None,
    threads: int = 1,
    mip_gap: float = 0.0,
    output_flag: bool = False,
) -> dict:
    """Solve the fixed-graph product model as a compact MILP.

    This is an optional oracle/probe path.  It is not a BPC certificate by
    itself; an OPTIMAL status certifies the fixed-graph product model objective.
    """

    start_wall = perf_counter()
    try:
        import gurobipy as gp
        from gurobipy import GRB
    except Exception as exc:  # pragma: no cover - depends on local environment
        return {
            "algorithm_status": "GUROBI_COMPACT_UNAVAILABLE",
            "certificate_scope": "FEASIBLE_INCUMBENT_ONLY",
            "objective": None,
            "bound": None,
            "gap": None,
            "journeys": tuple(),
            "has_feasible_incumbent": False,
            "wall_time_sec": round(perf_counter() - start_wall, 6),
            "note": f"gurobipy is unavailable: {type(exc).__name__}: {exc}",
        }

    tasks = tuple(data.task_ids)
    vehicle_count = int(data.fleet_size)
    slot_bound = _safe_sortie_slot_bound(data)
    sortie_slots = int(max_sorties_per_vehicle) if max_sorties_per_vehicle is not None else int(slot_bound["slot_count"])
    min_return_duration = float(slot_bound["min_return_duration_lower_bound"])
    min_active_duration = float(slot_bound["min_duration_lower_bound"])
    min_out_return_travel = float(slot_bound["min_out_return_travel_lower_bound"])
    if not tasks:
        return {
            "algorithm_status": "GUROBI_COMPACT_OPTIMAL",
            "certificate_scope": "DIRECT_DP_FIXED_GRAPH_OPTIMAL",
            "objective": 0.0,
            "bound": 0.0,
            "gap": 0.0,
            "journeys": tuple(),
            "wall_time_sec": round(perf_counter() - start_wall, 6),
            "has_feasible_incumbent": True,
            "note": "Empty instance.",
        }

    path_type_cache, pruning = _time_window_feasible_path_type_cache(data, _nondominated_path_type_cache(data))
    nodes = ("depot", *tasks)
    x_keys: list[tuple[int, int, str, str, str]] = []
    outgoing: dict[tuple[int, int, str], list[tuple[int, int, str, str, str]]] = defaultdict(list)
    incoming: dict[tuple[int, int, str], list[tuple[int, int, str, str, str]]] = defaultdict(list)
    for vehicle in range(vehicle_count):
        for slot in range(sortie_slots):
            for source in nodes:
                for target in nodes:
                    if source == target or (source == "depot" and target == "depot"):
                        continue
                    arc_key = (str(source), str(target))
                    if arc_key not in path_type_cache:
                        continue
                    for path_type in path_type_cache[arc_key]:
                        key = (vehicle, slot, str(source), str(target), str(path_type))
                        x_keys.append(key)
                        outgoing[(vehicle, slot, str(source))].append(key)
                        incoming[(vehicle, slot, str(target))].append(key)

    y_keys = [(vehicle, slot, task_id) for vehicle in range(vehicle_count) for slot in range(sortie_slots) for task_id in tasks]
    z_keys = [(vehicle, slot) for vehicle in range(vehicle_count) for slot in range(sortie_slots)]
    model = gp.Model("lunar_ice_fixed_graph_compact")
    model.Params.OutputFlag = 1 if output_flag else 0
    model.Params.Threads = max(1, int(threads))
    model.Params.MIPGap = max(0.0, float(mip_gap))
    model.Params.MIPGapAbs = 1.0e-8
    if time_limit_sec is not None:
        model.Params.TimeLimit = max(0.001, float(time_limit_sec))

    x = model.addVars(x_keys, vtype=GRB.BINARY, name="x")
    y = model.addVars(y_keys, vtype=GRB.BINARY, name="y")
    z = model.addVars(z_keys, vtype=GRB.BINARY, name="z")
    service_start = model.addVars(y_keys, lb=0.0, ub=float(data.horizon), vtype=GRB.CONTINUOUS, name="service_start")
    sortie_start = model.addVars(z_keys, lb=0.0, ub=float(data.horizon), vtype=GRB.CONTINUOUS, name="sortie_start")
    sortie_return = model.addVars(z_keys, lb=0.0, ub=float(data.horizon), vtype=GRB.CONTINUOUS, name="sortie_return")
    sortie_end = model.addVars(z_keys, lb=0.0, ub=float(data.horizon), vtype=GRB.CONTINUOUS, name="sortie_end")

    for task_id in tasks:
        model.addConstr(
            gp.quicksum(y[vehicle, slot, task_id] for vehicle in range(vehicle_count) for slot in range(sortie_slots)) == 1,
            name=f"cover[{task_id}]",
        )

    for vehicle in range(vehicle_count):
        for slot in range(sortie_slots):
            z_var = z[vehicle, slot]
            if slot + 1 < sortie_slots:
                model.addConstr(z[vehicle, slot + 1] <= z_var, name=f"sortie_order[{vehicle},{slot}]")
            if slot > 0:
                model.addConstr(sortie_start[vehicle, slot] >= sortie_end[vehicle, slot - 1], name=f"sortie_seq[{vehicle},{slot}]")
            model.addConstr(sortie_end[vehicle, slot] >= sortie_start[vehicle, slot], name=f"end_after_start[{vehicle},{slot}]")
            min_return_m = float(data.horizon) + min_return_duration
            min_active_m = float(data.horizon) + min_active_duration
            model.addConstr(
                sortie_return[vehicle, slot]
                >= sortie_start[vehicle, slot] + min_return_duration - min_return_m * (1 - z_var),
                name=f"min_return_duration[{vehicle},{slot}]",
            )
            model.addConstr(
                sortie_end[vehicle, slot]
                >= sortie_start[vehicle, slot] + min_active_duration - min_active_m * (1 - z_var),
                name=f"min_active_duration[{vehicle},{slot}]",
            )
            model.addConstr(
                gp.quicksum(x[key] for key in outgoing[(vehicle, slot, "depot")]) == z_var,
                name=f"depart_depot[{vehicle},{slot}]",
            )
            model.addConstr(
                gp.quicksum(x[key] for key in incoming[(vehicle, slot, "depot")]) == z_var,
                name=f"return_depot[{vehicle},{slot}]",
            )
            task_count_expr = gp.quicksum(y[vehicle, slot, task_id] for task_id in tasks)
            model.addConstr(task_count_expr <= int(data.max_tasks_per_trip) * z_var, name=f"trip_task_cap[{vehicle},{slot}]")
            model.addConstr(task_count_expr >= z_var, name=f"active_has_task[{vehicle},{slot}]")

            energy_expr = gp.LinExpr()
            shadow_expr = gp.LinExpr()
            demand_expr = gp.LinExpr()
            service_duration_expr = gp.LinExpr()
            for key in x_keys_for_vehicle_slot(outgoing, vehicle, slot, nodes):
                _vehicle, _slot, source, target, path_type = key
                option = data.option(source, target, path_type)
                energy_expr += float(option.energy_proxy) * x[key]
                shadow_expr += float(option.shadow_exposure_min) * x[key]
            for task_id in tasks:
                task = data.tasks[task_id]
                y_var = y[vehicle, slot, task_id]
                model.addConstr(y_var <= z_var, name=f"task_active_link[{vehicle},{slot},{task_id}]")
                model.addConstr(
                    gp.quicksum(x[key] for key in outgoing[(vehicle, slot, task_id)]) == y_var,
                    name=f"task_out[{vehicle},{slot},{task_id}]",
                )
                model.addConstr(
                    gp.quicksum(x[key] for key in incoming[(vehicle, slot, task_id)]) == y_var,
                    name=f"task_in[{vehicle},{slot},{task_id}]",
                )
                model.addConstr(
                    service_start[vehicle, slot, task_id] >= float(task.ready_time) * y_var,
                    name=f"ready[{vehicle},{slot},{task_id}]",
                )
                model.addConstr(
                    service_start[vehicle, slot, task_id] <= (float(task.due_time) - float(task.service_time)) * y_var,
                    name=f"due[{vehicle},{slot},{task_id}]",
                )
                energy_expr += float(task.service_energy) * y_var
                shadow_expr += float(task.local_shadow_score) * float(task.service_time) * y_var
                demand_expr += float(task.demand) * y_var
                service_duration_expr += float(task.service_time) * y_var

            model.addConstr(demand_expr <= float(data.capacity) * z_var, name=f"capacity[{vehicle},{slot}]")
            model.addConstr(energy_expr <= float(data.energy_limit) * z_var, name=f"energy[{vehicle},{slot}]")
            model.addConstr(shadow_expr <= float(data.max_shadow_exposure_per_sortie) * z_var, name=f"shadow[{vehicle},{slot}]")
            model.addConstr(sortie_return[vehicle, slot] <= float(data.horizon) * z_var, name=f"return_inactive_zero[{vehicle},{slot}]")
            model.addConstr(
                sortie_return[vehicle, slot]
                >= sortie_start[vehicle, slot]
                + service_duration_expr
                + (min_out_return_travel + float(data.horizon)) * z_var
                - float(data.horizon),
                name=f"service_travel_duration_lb[{vehicle},{slot}]",
            )
            model.addConstr(
                sortie_end[vehicle, slot]
                >= sortie_return[vehicle, slot]
                + float(data.dock_overhead_min) * z_var
                + energy_expr / max(1.0e-9, float(data.recharge_power_proxy_per_min)),
                name=f"recharge[{vehicle},{slot}]",
            )

            for key in x_keys_for_vehicle_slot(outgoing, vehicle, slot, nodes):
                _vehicle, _slot, source, target, path_type = key
                option = data.option(source, target, path_type)
                travel = float(option.travel_time_min)
                if source == "depot" and target != "depot":
                    time_m = _time_arc_big_m(data, travel=travel)
                    model.addConstr(
                        service_start[vehicle, slot, target]
                        >= sortie_start[vehicle, slot] + travel - time_m * (1 - x[key]),
                        name=f"time_depot[{vehicle},{slot},{target},{path_type}]",
                    )
                elif source != "depot" and target != "depot":
                    service = float(data.tasks[source].service_time)
                    time_m = _time_arc_big_m(data, travel=travel, service=service, source=source)
                    model.addConstr(
                        service_start[vehicle, slot, target]
                        >= service_start[vehicle, slot, source] + service + travel - time_m * (1 - x[key]),
                        name=f"time_task[{vehicle},{slot},{source},{target},{path_type}]",
                    )
                elif source != "depot" and target == "depot":
                    service = float(data.tasks[source].service_time)
                    time_m = _time_arc_big_m(data, travel=travel, service=service, source=source)
                    model.addConstr(
                        sortie_return[vehicle, slot]
                        >= service_start[vehicle, slot, source] + service + travel - time_m * (1 - x[key]),
                        name=f"time_return[{vehicle},{slot},{source},{path_type}]",
                    )

    refs = objective_references(data)
    cost_coeff = float(data.objective.weight_operating_cost) / float(refs.reference_cost)
    risk_coeff = float(data.objective.weight_risk) / float(refs.reference_risk)
    completion_coeff = float(data.objective.weight_completion) / float(refs.reference_completion)
    operating_expr = gp.LinExpr()
    risk_expr = gp.LinExpr()
    completion_expr = gp.LinExpr()
    for key in x_keys:
        _vehicle, _slot, source, target, path_type = key
        option = data.option(source, target, path_type)
        operating_expr += (float(option.distance_km) + float(option.energy_proxy)) * x[key]
        risk_expr += float(option.risk_integral) * x[key]
    for vehicle, slot, task_id in y_keys:
        task = data.tasks[task_id]
        y_var = y[vehicle, slot, task_id]
        operating_expr += (float(task.service_cost) + float(task.service_energy)) * y_var
        risk_expr += service_risk_value(task) * y_var
        completion_expr += float(task.science_weight) * (
            service_start[vehicle, slot, task_id] + float(task.service_time) * y_var
        )
    model.setObjective(cost_coeff * operating_expr + risk_coeff * risk_expr + completion_coeff * completion_expr, GRB.MINIMIZE)
    model.update()
    try:
        model.optimize()
    except gp.GurobiError as exc:
        return {
            "algorithm_status": "GUROBI_COMPACT_SOLVER_ERROR",
            "certificate_scope": "FEASIBLE_INCUMBENT_ONLY",
            "objective": None,
            "model_objective": None,
            "objective_breakdown": None,
            "bound": None,
            "gap": None,
            "journeys": tuple(),
            "journey_count": 0,
            "has_feasible_incumbent": False,
            "model_status_code": None,
            "model_status_name": "SOLVER_ERROR",
            "sol_count": 0,
            "vehicle_count": vehicle_count,
            "sortie_slots_per_vehicle": sortie_slots,
            "sortie_slot_bound_source": slot_bound["source"] if max_sorties_per_vehicle is None else "explicit",
            "sortie_slot_horizon_count_bound": slot_bound["horizon_slot_count_bound"],
            "sortie_slot_latest_start_count_bound": slot_bound["latest_start_slot_count_bound"],
            "sortie_slot_latest_service_start_upper_bound": slot_bound["latest_service_start_upper_bound"],
            "sortie_slot_min_depot_outbound_travel_lower_bound": slot_bound["min_depot_outbound_travel_lower_bound"],
            "sortie_slot_min_duration_lower_bound": slot_bound["min_duration_lower_bound"],
            "sortie_slot_min_return_duration_lower_bound": slot_bound["min_return_duration_lower_bound"],
            "sortie_slot_min_out_return_travel_lower_bound": slot_bound["min_out_return_travel_lower_bound"],
            "binary_arc_var_count": len(x_keys),
            **pruning,
            "task_assignment_var_count": len(y_keys),
            "constraint_count": int(model.NumConstrs),
            "variable_count": int(model.NumVars),
            "wall_time_sec": round(perf_counter() - start_wall, 6),
            "note": f"Gurobi compact MILP failed before producing a solution: {type(exc).__name__}: {exc}",
        }

    status_name = _gurobi_status_name(model.Status, GRB)
    journeys = _extract_journeys(data, model, x, z, sortie_start, vehicle_count, sortie_slots, nodes)
    objective = None
    objective_breakdown = None
    if journeys:
        objective = round(sum(column.objective for column in journeys), 6)
        objective_breakdown = aggregate_journey_objective_breakdown(data, journeys)
    has_feasible_incumbent = bool(journeys)
    bound = None
    gap = None
    if model.SolCount:
        try:
            gap = _finite_or_none(float(model.MIPGap))
        except Exception:
            gap = None
    try:
        bound = _finite_or_none(float(model.ObjBound))
    except Exception:
        bound = None
    optimal = model.Status == GRB.OPTIMAL
    return {
        "algorithm_status": "GUROBI_COMPACT_OPTIMAL" if optimal else f"GUROBI_COMPACT_{status_name}",
        "certificate_scope": "DIRECT_DP_FIXED_GRAPH_OPTIMAL" if optimal else "FEASIBLE_INCUMBENT_ONLY",
        "objective": objective,
        "model_objective": round(float(model.ObjVal), 9) if model.SolCount else None,
        "objective_breakdown": objective_breakdown,
        "bound": None if bound is None else round(bound, 9),
        "gap": None if gap is None else round(gap, 9),
        "journeys": tuple(journeys),
        "journey_count": len(journeys),
        "has_feasible_incumbent": has_feasible_incumbent,
        "model_status_code": int(model.Status),
        "model_status_name": status_name,
        "sol_count": int(model.SolCount),
        "vehicle_count": vehicle_count,
        "sortie_slots_per_vehicle": sortie_slots,
        "sortie_slot_bound_source": slot_bound["source"] if max_sorties_per_vehicle is None else "explicit",
        "sortie_slot_horizon_count_bound": slot_bound["horizon_slot_count_bound"],
        "sortie_slot_latest_start_count_bound": slot_bound["latest_start_slot_count_bound"],
        "sortie_slot_latest_service_start_upper_bound": slot_bound["latest_service_start_upper_bound"],
        "sortie_slot_min_depot_outbound_travel_lower_bound": slot_bound["min_depot_outbound_travel_lower_bound"],
        "sortie_slot_min_duration_lower_bound": slot_bound["min_duration_lower_bound"],
        "sortie_slot_min_return_duration_lower_bound": slot_bound["min_return_duration_lower_bound"],
        "sortie_slot_min_out_return_travel_lower_bound": slot_bound["min_out_return_travel_lower_bound"],
        "binary_arc_var_count": len(x_keys),
        **pruning,
        "task_assignment_var_count": len(y_keys),
        "constraint_count": int(model.NumConstrs),
        "variable_count": int(model.NumVars),
        "wall_time_sec": round(perf_counter() - start_wall, 6),
        "note": (
            "Compact Gurobi fixed-graph product model solved to optimality; this is an exact product oracle, not a BPC certificate."
            if optimal
            else (
                "Compact Gurobi fixed-graph product model stopped without a reconstructable feasible incumbent."
                if not has_feasible_incumbent
                else "Compact Gurobi fixed-graph product model found a feasible incumbent but did not prove optimality within the configured limits."
            )
        ),
    }


def x_keys_for_vehicle_slot(
    outgoing: dict[tuple[int, int, str], list[tuple[int, int, str, str, str]]],
    vehicle: int,
    slot: int,
    nodes: Iterable[str],
) -> tuple[tuple[int, int, str, str, str], ...]:
    keys: list[tuple[int, int, str, str, str]] = []
    for source in nodes:
        keys.extend(outgoing[(vehicle, slot, str(source))])
    return tuple(keys)


def _extract_journeys(
    data: LunarIceData,
    model,
    x,
    z,
    sortie_start,
    vehicle_count: int,
    sortie_slots: int,
    nodes: tuple[str, ...],
) -> tuple[JourneyColumn, ...]:
    if getattr(model, "SolCount", 0) <= 0:
        return tuple()
    journeys: list[JourneyColumn] = []
    for vehicle in range(vehicle_count):
        sorties = []
        for slot in range(sortie_slots):
            if z[vehicle, slot].X <= 0.5:
                continue
            sequence: list[str] = []
            path_types: list[str] = []
            current = "depot"
            visited = set()
            for _ in range(len(nodes) + 1):
                selected = []
                for key in x.keys():
                    v, s, source, target, path_type = key
                    if v == vehicle and s == slot and source == current and x[key].X > 0.5:
                        selected.append((target, path_type))
                if not selected:
                    break
                target, path_type = selected[0]
                path_types.append(path_type)
                if target == "depot":
                    break
                if target in visited:
                    break
                visited.add(target)
                sequence.append(target)
                current = target
            if sequence and len(path_types) == len(sequence) + 1:
                sortie = build_timed_sortie(
                    data,
                    tuple(sequence),
                    tuple(path_types),
                    start_time=float(sortie_start[vehicle, slot].X),
                )
                if sortie.feasible:
                    sorties.append(sortie)
        if sorties:
            journeys.append(build_journey_column(data, tuple(sorties)))
    return tuple(journeys)


def _gurobi_status_name(status: int, GRB) -> str:
    names = {
        GRB.LOADED: "LOADED",
        GRB.OPTIMAL: "OPTIMAL",
        GRB.INFEASIBLE: "INFEASIBLE",
        GRB.INF_OR_UNBD: "INF_OR_UNBD",
        GRB.UNBOUNDED: "UNBOUNDED",
        GRB.CUTOFF: "CUTOFF",
        GRB.ITERATION_LIMIT: "ITERATION_LIMIT",
        GRB.NODE_LIMIT: "NODE_LIMIT",
        GRB.TIME_LIMIT: "TIME_LIMIT",
        GRB.SOLUTION_LIMIT: "SOLUTION_LIMIT",
        GRB.INTERRUPTED: "INTERRUPTED",
        GRB.NUMERIC: "NUMERIC",
        GRB.SUBOPTIMAL: "SUBOPTIMAL",
        GRB.INPROGRESS: "INPROGRESS",
        GRB.USER_OBJ_LIMIT: "USER_OBJ_LIMIT",
        GRB.WORK_LIMIT: "WORK_LIMIT",
        GRB.MEM_LIMIT: "MEM_LIMIT",
    }
    return names.get(status, f"STATUS_{status}")


def solve_highs_compact_fixed_graph(
    data: LunarIceData,
    *,
    time_limit_sec: float | None = None,
    max_sorties_per_vehicle: int | None = None,
    threads: int = 1,
    mip_gap: float = 0.0,
    output_flag: bool = False,
    use_singleton_mip_start: bool = False,
    reference_solution: dict | None = None,
) -> dict:
    """Solve the compact fixed-graph product model with HiGHS."""

    start_wall = perf_counter()
    try:
        import highspy
    except Exception as exc:  # pragma: no cover - depends on local environment
        return {
            "algorithm_status": "HIGHS_COMPACT_UNAVAILABLE",
            "certificate_scope": "FEASIBLE_INCUMBENT_ONLY",
            "objective": None,
            "bound": None,
            "gap": None,
            "journeys": tuple(),
            "has_feasible_incumbent": False,
            "wall_time_sec": round(perf_counter() - start_wall, 6),
            "note": f"highspy is unavailable: {type(exc).__name__}: {exc}",
        }

    tasks = tuple(data.task_ids)
    vehicle_count = int(data.fleet_size)
    slot_bound = _safe_sortie_slot_bound(data)
    sortie_slots = int(max_sorties_per_vehicle) if max_sorties_per_vehicle is not None else int(slot_bound["slot_count"])
    min_return_duration = float(slot_bound["min_return_duration_lower_bound"])
    min_active_duration = float(slot_bound["min_duration_lower_bound"])
    min_out_return_travel = float(slot_bound["min_out_return_travel_lower_bound"])
    nodes = ("depot", *tasks)
    path_type_cache, pruning = _time_window_feasible_path_type_cache(data, _nondominated_path_type_cache(data))
    size = estimate_gurobi_compact_size(data, max_sorties_per_vehicle=max_sorties_per_vehicle)

    highs = highspy.Highs()
    highs.setOptionValue("output_flag", bool(output_flag))
    highs.setOptionValue("threads", max(1, int(threads)))
    highs.setOptionValue("mip_rel_gap", max(0.0, float(mip_gap)))
    if time_limit_sec is not None:
        highs.setOptionValue("time_limit", max(0.001, float(time_limit_sec)))
    highs.setMinimize()
    infinity = highs.getInfinity()

    var_lb: list[float] = []
    var_ub: list[float] = []
    var_cost: list[float] = []
    var_integer: list[bool] = []

    def add_var(lb: float, ub: float, cost: float = 0.0, *, integer: bool = False) -> int:
        index = len(var_lb)
        highs.addVar(float(lb), float(ub))
        highs.changeColCost(index, float(cost))
        if integer:
            highs.changeColIntegrality(index, highspy.HighsVarType.kInteger)
        var_lb.append(float(lb))
        var_ub.append(float(ub))
        var_cost.append(float(cost))
        var_integer.append(bool(integer))
        return index

    refs = objective_references(data)
    cost_coeff = float(data.objective.weight_operating_cost) / float(refs.reference_cost)
    risk_coeff = float(data.objective.weight_risk) / float(refs.reference_risk)
    completion_coeff = float(data.objective.weight_completion) / float(refs.reference_completion)

    x: dict[tuple[int, int, str, str, str], int] = {}
    outgoing: dict[tuple[int, int, str], list[tuple[int, int, str, str, str]]] = defaultdict(list)
    incoming: dict[tuple[int, int, str], list[tuple[int, int, str, str, str]]] = defaultdict(list)
    for vehicle in range(vehicle_count):
        for slot in range(sortie_slots):
            for source in nodes:
                for target in nodes:
                    if source == target or (source == "depot" and target == "depot"):
                        continue
                    arc_key = (str(source), str(target))
                    if arc_key not in path_type_cache:
                        continue
                    for path_type in path_type_cache[arc_key]:
                        option = data.option(source, target, path_type)
                        objective = cost_coeff * (float(option.distance_km) + float(option.energy_proxy))
                        objective += risk_coeff * float(option.risk_integral)
                        key = (vehicle, slot, str(source), str(target), str(path_type))
                        x[key] = add_var(0.0, 1.0, objective, integer=True)
                        outgoing[(vehicle, slot, str(source))].append(key)
                        incoming[(vehicle, slot, str(target))].append(key)

    y: dict[tuple[int, int, str], int] = {}
    service_start: dict[tuple[int, int, str], int] = {}
    for vehicle in range(vehicle_count):
        for slot in range(sortie_slots):
            for task_id in tasks:
                task = data.tasks[task_id]
                y_cost = cost_coeff * (float(task.service_cost) + float(task.service_energy))
                y_cost += risk_coeff * service_risk_value(task)
                y_cost += completion_coeff * float(task.science_weight) * float(task.service_time)
                y[vehicle, slot, task_id] = add_var(0.0, 1.0, y_cost, integer=True)
                service_start[vehicle, slot, task_id] = add_var(
                    0.0,
                    float(data.horizon),
                    completion_coeff * float(task.science_weight),
                    integer=False,
                )

    z: dict[tuple[int, int], int] = {}
    sortie_start: dict[tuple[int, int], int] = {}
    sortie_return: dict[tuple[int, int], int] = {}
    sortie_end: dict[tuple[int, int], int] = {}
    for vehicle in range(vehicle_count):
        for slot in range(sortie_slots):
            z[vehicle, slot] = add_var(0.0, 1.0, 0.0, integer=True)
            sortie_start[vehicle, slot] = add_var(0.0, float(data.horizon), 0.0)
            sortie_return[vehicle, slot] = add_var(0.0, float(data.horizon), 0.0)
            sortie_end[vehicle, slot] = add_var(0.0, float(data.horizon), 0.0)

    mip_start_payload = {
        "enabled": bool(use_singleton_mip_start or reference_solution),
        "status": "DISABLED",
        "entry_count": 0,
        "sortie_count": 0,
        "objective": None,
        "source": "",
        "note": "",
    }

    def add_row(coefficients: dict[int, float], lb: float, ub: float) -> None:
        cleaned = {int(col): float(value) for col, value in coefficients.items() if abs(float(value)) > 1.0e-12}
        highs.addRow(float(lb), float(ub), len(cleaned), list(cleaned), list(cleaned.values()))

    def add_eq(coefficients: dict[int, float], rhs: float) -> None:
        add_row(coefficients, float(rhs), float(rhs))

    def add_le(coefficients: dict[int, float], rhs: float) -> None:
        add_row(coefficients, -infinity, float(rhs))

    def add_ge(coefficients: dict[int, float], rhs: float) -> None:
        add_row(coefficients, float(rhs), infinity)

    for task_id in tasks:
        add_eq({y[vehicle, slot, task_id]: 1.0 for vehicle in range(vehicle_count) for slot in range(sortie_slots)}, 1.0)

    for vehicle in range(vehicle_count):
        for slot in range(sortie_slots):
            z_col = z[vehicle, slot]
            if slot + 1 < sortie_slots:
                add_le({z[vehicle, slot + 1]: 1.0, z_col: -1.0}, 0.0)
            if slot > 0:
                add_ge({sortie_start[vehicle, slot]: 1.0, sortie_end[vehicle, slot - 1]: -1.0}, 0.0)
            add_ge({sortie_end[vehicle, slot]: 1.0, sortie_start[vehicle, slot]: -1.0}, 0.0)
            min_return_m = float(data.horizon) + min_return_duration
            min_active_m = float(data.horizon) + min_active_duration
            add_ge(
                {
                    sortie_return[vehicle, slot]: 1.0,
                    sortie_start[vehicle, slot]: -1.0,
                    z_col: -float(min_return_m),
                },
                float(min_return_duration) - float(min_return_m),
            )
            add_ge(
                {
                    sortie_end[vehicle, slot]: 1.0,
                    sortie_start[vehicle, slot]: -1.0,
                    z_col: -float(min_active_m),
                },
                float(min_active_duration) - float(min_active_m),
            )
            add_eq({**{x[key]: 1.0 for key in outgoing[(vehicle, slot, "depot")]}, z_col: -1.0}, 0.0)
            add_eq({**{x[key]: 1.0 for key in incoming[(vehicle, slot, "depot")]}, z_col: -1.0}, 0.0)
            add_le({**{y[vehicle, slot, task_id]: 1.0 for task_id in tasks}, z_col: -float(data.max_tasks_per_trip)}, 0.0)
            add_ge({**{y[vehicle, slot, task_id]: 1.0 for task_id in tasks}, z_col: -1.0}, 0.0)

            energy_coefficients: dict[int, float] = {}
            shadow_coefficients: dict[int, float] = {}
            demand_coefficients: dict[int, float] = {}
            service_duration_coefficients: dict[int, float] = {}
            for key in x_keys_for_vehicle_slot(outgoing, vehicle, slot, nodes):
                _vehicle, _slot, source, target, path_type = key
                option = data.option(source, target, path_type)
                energy_coefficients[x[key]] = energy_coefficients.get(x[key], 0.0) + float(option.energy_proxy)
                shadow_coefficients[x[key]] = shadow_coefficients.get(x[key], 0.0) + float(option.shadow_exposure_min)
            for task_id in tasks:
                task = data.tasks[task_id]
                y_col = y[vehicle, slot, task_id]
                start_col = service_start[vehicle, slot, task_id]
                add_le({y_col: 1.0, z_col: -1.0}, 0.0)
                add_eq({**{x[key]: 1.0 for key in outgoing[(vehicle, slot, task_id)]}, y_col: -1.0}, 0.0)
                add_eq({**{x[key]: 1.0 for key in incoming[(vehicle, slot, task_id)]}, y_col: -1.0}, 0.0)
                add_ge({start_col: 1.0, y_col: -float(task.ready_time)}, 0.0)
                add_le({start_col: 1.0, y_col: -(float(task.due_time) - float(task.service_time))}, 0.0)
                energy_coefficients[y_col] = energy_coefficients.get(y_col, 0.0) + float(task.service_energy)
                shadow_coefficients[y_col] = (
                    shadow_coefficients.get(y_col, 0.0)
                    + float(task.local_shadow_score) * float(task.service_time)
                )
                demand_coefficients[y_col] = demand_coefficients.get(y_col, 0.0) + float(task.demand)
                service_duration_coefficients[y_col] = (
                    service_duration_coefficients.get(y_col, 0.0) + float(task.service_time)
                )

            add_le({**demand_coefficients, z_col: -float(data.capacity)}, 0.0)
            add_le({**energy_coefficients, z_col: -float(data.energy_limit)}, 0.0)
            add_le({**shadow_coefficients, z_col: -float(data.max_shadow_exposure_per_sortie)}, 0.0)
            add_le({sortie_return[vehicle, slot]: 1.0, z_col: -float(data.horizon)}, 0.0)
            add_ge(
                {
                    sortie_return[vehicle, slot]: 1.0,
                    sortie_start[vehicle, slot]: -1.0,
                    z_col: -float(min_out_return_travel + float(data.horizon)),
                    **{col: -value for col, value in service_duration_coefficients.items()},
                },
                -float(data.horizon),
            )
            recharge_coefficients = {
                sortie_end[vehicle, slot]: -1.0,
                sortie_return[vehicle, slot]: 1.0,
                z_col: float(data.dock_overhead_min),
            }
            for col, value in energy_coefficients.items():
                recharge_coefficients[col] = recharge_coefficients.get(col, 0.0) + value / max(
                    1.0e-9,
                    float(data.recharge_power_proxy_per_min),
                )
            add_le(recharge_coefficients, 0.0)

            for key in x_keys_for_vehicle_slot(outgoing, vehicle, slot, nodes):
                _vehicle, _slot, source, target, path_type = key
                option = data.option(source, target, path_type)
                travel = float(option.travel_time_min)
                x_col = x[key]
                if source == "depot" and target != "depot":
                    time_m = _time_arc_big_m(data, travel=travel)
                    add_ge(
                        {
                            service_start[vehicle, slot, target]: 1.0,
                            sortie_start[vehicle, slot]: -1.0,
                            x_col: -time_m,
                        },
                        travel - time_m,
                    )
                elif source != "depot" and target != "depot":
                    service = float(data.tasks[source].service_time)
                    time_m = _time_arc_big_m(data, travel=travel, service=service, source=source)
                    add_ge(
                        {
                            service_start[vehicle, slot, target]: 1.0,
                            service_start[vehicle, slot, source]: -1.0,
                            x_col: -time_m,
                        },
                        service + travel - time_m,
                    )
                elif source != "depot" and target == "depot":
                    service = float(data.tasks[source].service_time)
                    time_m = _time_arc_big_m(data, travel=travel, service=service, source=source)
                    add_ge(
                        {
                            sortie_return[vehicle, slot]: 1.0,
                            service_start[vehicle, slot, source]: -1.0,
                            x_col: -time_m,
                        },
                        service + travel - time_m,
                    )

    if use_singleton_mip_start or reference_solution:
        mip_start_payload = _set_highs_singleton_mip_start(
            highs,
            data=data,
            tasks=tasks,
            path_type_cache=path_type_cache,
            vehicle_count=vehicle_count,
            sortie_slots=sortie_slots,
            x=x,
            y=y,
            z=z,
            service_start=service_start,
            sortie_start=sortie_start,
            sortie_return=sortie_return,
            sortie_end=sortie_end,
            reference_solution=reference_solution,
        )

    highs.run()
    status = highs.getModelStatus()
    status_name = highs.modelStatusToString(status).upper().replace(" ", "_")
    solution = highs.getSolution()
    col_values = tuple(float(value) for value in solution.col_value)
    has_solution = bool(col_values) and status in {
        highspy.HighsModelStatus.kOptimal,
        highspy.HighsModelStatus.kTimeLimit,
        highspy.HighsModelStatus.kSolutionLimit,
    }
    journeys = _extract_highs_journeys(
        data,
        col_values,
        x,
        z,
        sortie_start,
        vehicle_count,
        sortie_slots,
        nodes,
    ) if has_solution else tuple()
    objective = None
    objective_breakdown = None
    if journeys:
        objective = round(sum(column.objective for column in journeys), 6)
        objective_breakdown = aggregate_journey_objective_breakdown(data, journeys)
    has_feasible_incumbent = bool(journeys)
    try:
        info = highs.getInfo()
        bound = _finite_or_none(getattr(info, "mip_dual_bound", None))
        gap = _finite_or_none(getattr(info, "mip_gap", None))
        solver_info = _highs_info_payload(info)
    except Exception:
        bound = None
        gap = None
        solver_info = {}
    optimal = status == highspy.HighsModelStatus.kOptimal
    return {
        "algorithm_status": "HIGHS_COMPACT_OPTIMAL" if optimal else f"HIGHS_COMPACT_{status_name}",
        "certificate_scope": "DIRECT_DP_FIXED_GRAPH_OPTIMAL" if optimal else "FEASIBLE_INCUMBENT_ONLY",
        "objective": objective,
        "model_objective": round(float(highs.getObjectiveValue()), 9) if journeys else None,
        "objective_breakdown": objective_breakdown,
        "bound": None if bound is None else round(float(bound), 9),
        "gap": None if gap is None else round(float(gap), 9),
        "journeys": tuple(journeys),
        "journey_count": len(journeys),
        "has_feasible_incumbent": has_feasible_incumbent,
        "model_status_code": int(status),
        "model_status_name": status_name,
        "solver_info": solver_info,
        "mip_start": mip_start_payload,
        "vehicle_count": vehicle_count,
        "sortie_slots_per_vehicle": sortie_slots,
        **size,
        **pruning,
        "constraint_count": int(highs.getNumRow()),
        "variable_count": int(highs.getNumCol()),
        "wall_time_sec": round(perf_counter() - start_wall, 6),
        "note": (
            "Compact HiGHS fixed-graph product model solved to optimality; this is an exact product oracle, not a BPC certificate."
            if optimal
            else (
                "Compact HiGHS fixed-graph product model stopped without a reconstructable feasible incumbent."
                if not has_feasible_incumbent
                else "Compact HiGHS fixed-graph product model found a feasible incumbent but did not prove optimality within the configured limits."
            )
        ),
    }


def solve_highs_compact_single_journey_pricing(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    time_limit_sec: float | None = None,
    max_sorties_per_journey: int | None = None,
    threads: int = 1,
    mip_gap: float = 0.0,
    output_flag: bool = False,
    negative_eps: float = 1.0e-6,
    flow_connectivity: bool = False,
    mtz_connectivity: bool = False,
    mtz_endpoint_order_cuts: bool = True,
    pair_adjacency_cuts: bool = False,
    latest_service_start_slot_bound: bool = True,
    time_window_arc_pruning: bool = True,
    negative_feasibility_search: bool = False,
    forbidden_arc_patterns: Iterable[Iterable[tuple[int, str, str, str]]] | None = None,
    forbidden_task_sets: Iterable[Iterable[str]] | None = None,
) -> dict:
    """Solve exact fixed-graph single-journey reduced-cost pricing with HiGHS.

    The model searches over one nonempty journey: a sequence of active sorties,
    each starting and ending at the depot, with each task visited at most once.
    An OPTIMAL result is an exact reduced-cost pricing result for the fixed
    graph and can certify no negative column when the optimum is nonnegative.
    """

    start_wall = perf_counter()
    try:
        import highspy
    except Exception as exc:  # pragma: no cover - depends on local environment
        return {
            "status": "COMPACT_HIGHS_PRICING_UNAVAILABLE",
            "algorithm_status": "COMPACT_HIGHS_PRICING_UNAVAILABLE",
            "pricing_state": "INCOMPLETE_LIMIT",
            "best_reduced_cost": None,
            "dual_bound": None,
            "negative_found": False,
            "can_certify_no_negative": False,
            "journeys": tuple(),
            "wall_time_sec": round(perf_counter() - start_wall, 6),
            "note": f"highspy is unavailable: {type(exc).__name__}: {exc}",
        }

    tasks = tuple(data.task_ids)
    if not tasks:
        return {
            "status": "COMPACT_HIGHS_PRICING_EMPTY_INSTANCE",
            "algorithm_status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "best_reduced_cost": None,
            "dual_bound": None,
            "negative_found": False,
            "can_certify_no_negative": True,
            "journeys": tuple(),
            "wall_time_sec": round(perf_counter() - start_wall, 6),
            "note": "Empty instance has no nonempty journey columns.",
        }

    slot_bound = _safe_sortie_slot_bound(
        data,
        latest_service_start_bound=bool(latest_service_start_slot_bound),
    )
    sortie_slots = (
        int(max_sorties_per_journey)
        if max_sorties_per_journey is not None
        else int(slot_bound["slot_count"])
    )
    min_return_duration = float(slot_bound["min_return_duration_lower_bound"])
    min_active_duration = float(slot_bound["min_duration_lower_bound"])
    min_out_return_travel = float(slot_bound["min_out_return_travel_lower_bound"])
    nodes = ("depot", *tasks)
    path_type_cache, pruning = _pricing_path_type_cache(
        data,
        time_window_arc_pruning=bool(time_window_arc_pruning),
    )
    forbidden_patterns = tuple(_normalize_forbidden_arc_pattern(row) for row in (forbidden_arc_patterns or tuple()))
    forbidden_patterns = tuple(row for row in forbidden_patterns if row)
    forbidden_task_sets_normalized = tuple(
        _normalize_forbidden_task_set(row, valid_tasks=set(tasks))
        for row in (forbidden_task_sets or tuple())
    )
    forbidden_task_sets_normalized = tuple(row for row in forbidden_task_sets_normalized if row)

    highs = highspy.Highs()
    highs.setOptionValue("output_flag", bool(output_flag))
    highs.setOptionValue("threads", max(1, int(threads)))
    highs.setOptionValue("mip_rel_gap", max(0.0, float(mip_gap)))
    if time_limit_sec is not None:
        highs.setOptionValue("time_limit", max(0.001, float(time_limit_sec)))
    highs.setMinimize()
    infinity = highs.getInfinity()

    def add_var(lb: float, ub: float, cost: float = 0.0, *, integer: bool = False) -> int:
        index = highs.getNumCol()
        highs.addVar(float(lb), float(ub))
        highs.changeColCost(index, float(cost))
        if integer:
            highs.changeColIntegrality(index, highspy.HighsVarType.kInteger)
        return index

    def add_row(coefficients: dict[int, float], lb: float, ub: float) -> None:
        cleaned = {int(col): float(value) for col, value in coefficients.items() if abs(float(value)) > 1.0e-12}
        highs.addRow(float(lb), float(ub), len(cleaned), list(cleaned), list(cleaned.values()))

    def add_eq(coefficients: dict[int, float], rhs: float) -> None:
        add_row(coefficients, float(rhs), float(rhs))

    def add_le(coefficients: dict[int, float], rhs: float) -> None:
        add_row(coefficients, -infinity, float(rhs))

    def add_ge(coefficients: dict[int, float], rhs: float) -> None:
        add_row(coefficients, float(rhs), infinity)

    refs = objective_references(data)
    cost_coeff = float(data.objective.weight_operating_cost) / float(refs.reference_cost)
    risk_coeff = float(data.objective.weight_risk) / float(refs.reference_risk)
    completion_coeff = float(data.objective.weight_completion) / float(refs.reference_completion)
    reduced_cost_coefficients: dict[int, float] = {}

    def add_reduced_cost_coefficient(col: int, value: float) -> None:
        if abs(float(value)) <= 1.0e-12:
            return
        reduced_cost_coefficients[int(col)] = reduced_cost_coefficients.get(int(col), 0.0) + float(value)

    x: dict[tuple[int, int, str, str, str], int] = {}
    flow: dict[tuple[int, int, str, str, str], int] = {}
    outgoing: dict[tuple[int, int, str], list[tuple[int, int, str, str, str]]] = defaultdict(list)
    incoming: dict[tuple[int, int, str], list[tuple[int, int, str, str, str]]] = defaultdict(list)
    vehicle = 0
    for slot in range(sortie_slots):
        for source in nodes:
            for target in nodes:
                if source == target or (source == "depot" and target == "depot"):
                    continue
                arc_key = (str(source), str(target))
                if arc_key not in path_type_cache:
                    continue
                for path_type in path_type_cache[arc_key]:
                    option = data.option(source, target, path_type)
                    objective = cost_coeff * (float(option.distance_km) + float(option.energy_proxy))
                    objective += risk_coeff * float(option.risk_integral)
                    key = (vehicle, slot, str(source), str(target), str(path_type))
                    x[key] = add_var(0.0, 1.0, objective, integer=True)
                    add_reduced_cost_coefficient(x[key], objective)
                    if flow_connectivity:
                        flow[key] = add_var(0.0, float(data.max_tasks_per_trip), 0.0, integer=False)
                    outgoing[(vehicle, slot, str(source))].append(key)
                    incoming[(vehicle, slot, str(target))].append(key)

    y: dict[tuple[int, int, str], int] = {}
    service_start: dict[tuple[int, int, str], int] = {}
    visit_order: dict[tuple[int, int, str], int] = {}
    for slot in range(sortie_slots):
        for task_id in tasks:
            task = data.tasks[task_id]
            y_cost = cost_coeff * (float(task.service_cost) + float(task.service_energy))
            y_cost += risk_coeff * service_risk_value(task)
            y_cost += completion_coeff * float(task.science_weight) * float(task.service_time)
            y_cost -= float(duals.cover.get(str(task_id), 0.0))
            y[vehicle, slot, task_id] = add_var(0.0, 1.0, y_cost, integer=True)
            add_reduced_cost_coefficient(y[vehicle, slot, task_id], y_cost)
            service_start[vehicle, slot, task_id] = add_var(
                0.0,
                float(data.horizon),
                completion_coeff * float(task.science_weight),
                integer=False,
            )
            add_reduced_cost_coefficient(
                service_start[vehicle, slot, task_id],
                completion_coeff * float(task.science_weight),
            )
            if mtz_connectivity:
                visit_order[vehicle, slot, task_id] = add_var(
                    0.0,
                    float(data.max_tasks_per_trip),
                    0.0,
                    integer=False,
                )

    journey_active = add_var(1.0, 1.0, -float(duals.fleet_limit), integer=True)
    add_reduced_cost_coefficient(journey_active, -float(duals.fleet_limit))
    z: dict[tuple[int, int], int] = {}
    sortie_start: dict[tuple[int, int], int] = {}
    sortie_return: dict[tuple[int, int], int] = {}
    sortie_end: dict[tuple[int, int], int] = {}
    for slot in range(sortie_slots):
        z[vehicle, slot] = add_var(0.0, 1.0, 0.0, integer=True)
        sortie_start[vehicle, slot] = add_var(0.0, float(data.horizon), 0.0)
        sortie_return[vehicle, slot] = add_var(0.0, float(data.horizon), 0.0)
        sortie_end[vehicle, slot] = add_var(0.0, float(data.horizon), 0.0)

    for task_id in tasks:
        add_le({y[vehicle, slot, task_id]: 1.0 for slot in range(sortie_slots)}, 1.0)
    add_ge({z[vehicle, slot]: 1.0 for slot in range(sortie_slots)}, 1.0)

    pair_adjacency_cut_count_total = 0
    mtz_endpoint_order_cut_count_total = 0
    for slot in range(sortie_slots):
        z_col = z[vehicle, slot]
        add_le({z_col: 1.0, journey_active: -1.0}, 0.0)
        if slot + 1 < sortie_slots:
            add_le({z[vehicle, slot + 1]: 1.0, z_col: -1.0}, 0.0)
        if slot > 0:
            add_ge({sortie_start[vehicle, slot]: 1.0, sortie_end[vehicle, slot - 1]: -1.0}, 0.0)
        add_ge({sortie_end[vehicle, slot]: 1.0, sortie_start[vehicle, slot]: -1.0}, 0.0)
        min_return_m = float(data.horizon) + min_return_duration
        min_active_m = float(data.horizon) + min_active_duration
        add_ge(
            {
                sortie_return[vehicle, slot]: 1.0,
                sortie_start[vehicle, slot]: -1.0,
                z_col: -float(min_return_m),
            },
            float(min_return_duration) - float(min_return_m),
        )
        add_ge(
            {
                sortie_end[vehicle, slot]: 1.0,
                sortie_start[vehicle, slot]: -1.0,
                z_col: -float(min_active_m),
            },
            float(min_active_duration) - float(min_active_m),
        )
        add_eq({**{x[key]: 1.0 for key in outgoing[(vehicle, slot, "depot")]}, z_col: -1.0}, 0.0)
        add_eq({**{x[key]: 1.0 for key in incoming[(vehicle, slot, "depot")]}, z_col: -1.0}, 0.0)
        total_task_expr = {y[vehicle, slot, task_id]: 1.0 for task_id in tasks}
        add_le({**total_task_expr, z_col: -float(data.max_tasks_per_trip)}, 0.0)
        add_ge({**total_task_expr, z_col: -1.0}, 0.0)
        if flow_connectivity:
            depot_flow = {flow[key]: 1.0 for key in outgoing[(vehicle, slot, "depot")]}
            for key in incoming[(vehicle, slot, "depot")]:
                depot_flow[flow[key]] = depot_flow.get(flow[key], 0.0) - 1.0
            add_eq({**depot_flow, **{col: -value for col, value in total_task_expr.items()}}, 0.0)

        energy_coefficients: dict[int, float] = {}
        shadow_coefficients: dict[int, float] = {}
        demand_coefficients: dict[int, float] = {}
        service_duration_coefficients: dict[int, float] = {}
        for key in x_keys_for_vehicle_slot(outgoing, vehicle, slot, nodes):
            _vehicle, _slot, source, target, path_type = key
            option = data.option(source, target, path_type)
            energy_coefficients[x[key]] = energy_coefficients.get(x[key], 0.0) + float(option.energy_proxy)
            shadow_coefficients[x[key]] = shadow_coefficients.get(x[key], 0.0) + float(option.shadow_exposure_min)
            if flow_connectivity:
                add_le({flow[key]: 1.0, x[key]: -float(data.max_tasks_per_trip)}, 0.0)
        for task_id in tasks:
            task = data.tasks[task_id]
            y_col = y[vehicle, slot, task_id]
            start_col = service_start[vehicle, slot, task_id]
            add_le({y_col: 1.0, z_col: -1.0}, 0.0)
            add_eq({**{x[key]: 1.0 for key in outgoing[(vehicle, slot, task_id)]}, y_col: -1.0}, 0.0)
            add_eq({**{x[key]: 1.0 for key in incoming[(vehicle, slot, task_id)]}, y_col: -1.0}, 0.0)
            if flow_connectivity:
                task_flow = {flow[key]: 1.0 for key in incoming[(vehicle, slot, task_id)]}
                for key in outgoing[(vehicle, slot, task_id)]:
                    task_flow[flow[key]] = task_flow.get(flow[key], 0.0) - 1.0
                add_eq({**task_flow, y_col: -1.0}, 0.0)
            if mtz_connectivity:
                order_col = visit_order[vehicle, slot, task_id]
                add_le({order_col: 1.0, y_col: -float(data.max_tasks_per_trip)}, 0.0)
                add_ge({order_col: 1.0, y_col: -1.0}, 0.0)
            add_ge({start_col: 1.0, y_col: -float(task.ready_time)}, 0.0)
            add_le({start_col: 1.0, y_col: -(float(task.due_time) - float(task.service_time))}, 0.0)
            energy_coefficients[y_col] = energy_coefficients.get(y_col, 0.0) + float(task.service_energy)
            shadow_coefficients[y_col] = (
                shadow_coefficients.get(y_col, 0.0)
                + float(task.local_shadow_score) * float(task.service_time)
            )
            demand_coefficients[y_col] = demand_coefficients.get(y_col, 0.0) + float(task.demand)
            service_duration_coefficients[y_col] = (
                service_duration_coefficients.get(y_col, 0.0) + float(task.service_time)
            )

        if pair_adjacency_cuts:
            for left_index, left_task in enumerate(tasks):
                for right_task in tasks[left_index + 1 :]:
                    coefficients: dict[int, float] = {}
                    for key in outgoing[(vehicle, slot, left_task)]:
                        _vehicle, _slot, _source, target, _path_type = key
                        if target == right_task:
                            coefficients[x[key]] = coefficients.get(x[key], 0.0) + 1.0
                    for key in outgoing[(vehicle, slot, right_task)]:
                        _vehicle, _slot, _source, target, _path_type = key
                        if target == left_task:
                            coefficients[x[key]] = coefficients.get(x[key], 0.0) + 1.0
                    if not coefficients:
                        continue
                    coefficients[y[vehicle, slot, left_task]] = coefficients.get(
                        y[vehicle, slot, left_task],
                        0.0,
                    ) - 0.5
                    coefficients[y[vehicle, slot, right_task]] = coefficients.get(
                        y[vehicle, slot, right_task],
                        0.0,
                    ) - 0.5
                    add_le(coefficients, 0.0)
                    pair_adjacency_cut_count_total += 1

        add_le({**demand_coefficients, z_col: -float(data.capacity)}, 0.0)
        add_le({**energy_coefficients, z_col: -float(data.energy_limit)}, 0.0)
        add_le({**shadow_coefficients, z_col: -float(data.max_shadow_exposure_per_sortie)}, 0.0)
        add_le({sortie_return[vehicle, slot]: 1.0, z_col: -float(data.horizon)}, 0.0)
        add_ge(
            {
                sortie_return[vehicle, slot]: 1.0,
                sortie_start[vehicle, slot]: -1.0,
                z_col: -float(min_out_return_travel + float(data.horizon)),
                **{col: -value for col, value in service_duration_coefficients.items()},
            },
            -float(data.horizon),
        )
        recharge_coefficients = {
            sortie_end[vehicle, slot]: -1.0,
            sortie_return[vehicle, slot]: 1.0,
            z_col: float(data.dock_overhead_min),
        }
        for col, value in energy_coefficients.items():
            recharge_coefficients[col] = recharge_coefficients.get(col, 0.0) + value / max(
                1.0e-9,
                float(data.recharge_power_proxy_per_min),
            )
        add_le(recharge_coefficients, 0.0)

        for key in x_keys_for_vehicle_slot(outgoing, vehicle, slot, nodes):
            _vehicle, _slot, source, target, path_type = key
            option = data.option(source, target, path_type)
            travel = float(option.travel_time_min)
            x_col = x[key]
            if source == "depot" and target != "depot":
                time_m = _time_arc_big_m(data, travel=travel)
                add_ge(
                    {
                        service_start[vehicle, slot, target]: 1.0,
                        sortie_start[vehicle, slot]: -1.0,
                        x_col: -time_m,
                    },
                    travel - time_m,
                )
            elif source != "depot" and target != "depot":
                service = float(data.tasks[source].service_time)
                time_m = _time_arc_big_m(data, travel=travel, service=service, source=source)
                add_ge(
                    {
                        service_start[vehicle, slot, target]: 1.0,
                        service_start[vehicle, slot, source]: -1.0,
                        x_col: -time_m,
                    },
                    service + travel - time_m,
                )
            elif source != "depot" and target == "depot":
                service = float(data.tasks[source].service_time)
                time_m = _time_arc_big_m(data, travel=travel, service=service, source=source)
                add_ge(
                    {
                        sortie_return[vehicle, slot]: 1.0,
                        service_start[vehicle, slot, source]: -1.0,
                        x_col: -time_m,
                    },
                    service + travel - time_m,
                )
            if mtz_connectivity and mtz_endpoint_order_cuts and source == "depot" and target != "depot":
                # If a task is the first task after the depot, its visit order is 1.
                order_m = float(data.max_tasks_per_trip)
                add_le(
                    {
                        visit_order[vehicle, slot, target]: 1.0,
                        x_col: order_m - 1.0,
                    },
                    order_m,
                )
                mtz_endpoint_order_cut_count_total += 1
            elif mtz_connectivity and mtz_endpoint_order_cuts and source != "depot" and target == "depot":
                # If a task returns to the depot, it is the last task in that sortie.
                order_m = float(data.max_tasks_per_trip)
                coefficients = {
                    visit_order[vehicle, slot, source]: 1.0,
                    x_col: -order_m,
                }
                for task_id in tasks:
                    y_col = y[vehicle, slot, task_id]
                    coefficients[y_col] = coefficients.get(y_col, 0.0) - 1.0
                add_ge(coefficients, -order_m)
                mtz_endpoint_order_cut_count_total += 1
            if mtz_connectivity and source != "depot" and target != "depot":
                order_m = float(data.max_tasks_per_trip)
                add_ge(
                    {
                        visit_order[vehicle, slot, target]: 1.0,
                        visit_order[vehicle, slot, source]: -1.0,
                        x_col: -order_m,
                    },
                    1.0 - order_m,
                )

    if negative_feasibility_search:
        # Exact alternative to minimizing reduced cost: ask whether any journey
        # column with rc <= -eps exists.  Infeasibility is then a no-negative
        # proof; a feasible solution is a negative column; time limits remain
        # fail-closed.
        add_le(reduced_cost_coefficients, -abs(float(negative_eps)))

    forbidden_pattern_count = 0
    for pattern in forbidden_patterns:
        coefficients = {
            x[(vehicle, slot, source, target, path_type)]: 1.0
            for slot, source, target, path_type in pattern
            if (vehicle, slot, source, target, path_type) in x
        }
        if len(coefficients) != len(pattern) or not coefficients:
            continue
        add_le(coefficients, float(len(coefficients) - 1))
        forbidden_pattern_count += 1

    forbidden_task_set_count = 0
    for task_set in forbidden_task_sets_normalized:
        coefficients: dict[int, float] = {}
        forbidden_lookup = set(task_set)
        for task_id in tasks:
            sign = 1.0 if task_id in forbidden_lookup else -1.0
            for slot in range(sortie_slots):
                coefficients[y[vehicle, slot, task_id]] = sign
        if not coefficients:
            continue
        # Forbid exactly this task set while still allowing proper subsets and
        # supersets.  This is only used in restricted discovery, never as a
        # no-negative certificate for the full pricing space.
        add_le(coefficients, float(len(task_set) - 1))
        forbidden_task_set_count += 1

    highs.run()
    status = highs.getModelStatus()
    status_name = highs.modelStatusToString(status).upper().replace(" ", "_")
    solution = highs.getSolution()
    col_values = tuple(float(value) for value in solution.col_value)
    has_solution = bool(col_values) and status in {
        highspy.HighsModelStatus.kOptimal,
        highspy.HighsModelStatus.kTimeLimit,
        highspy.HighsModelStatus.kSolutionLimit,
    }
    journeys = (
        _extract_highs_journeys(
            data,
            col_values,
            x,
            z,
            sortie_start,
            1,
            sortie_slots,
            nodes,
        )
        if has_solution
        else tuple()
    )
    best_journey = journeys[0] if journeys else None
    manual_rc = (
        manual_journey_reduced_cost(best_journey, duals)
        if best_journey is not None
        else None
    )
    try:
        info = highs.getInfo()
        bound = _finite_or_none(getattr(info, "mip_dual_bound", None))
        gap = _finite_or_none(getattr(info, "mip_gap", None))
        solver_info = _highs_info_payload(info)
    except Exception:
        bound = None
        gap = None
        solver_info = {}
    model_objective = _finite_or_none(highs.getObjectiveValue()) if has_solution else None
    optimal = status == highspy.HighsModelStatus.kOptimal
    infeasible = status == highspy.HighsModelStatus.kInfeasible
    best_rc = manual_rc if manual_rc is not None else model_objective
    negative_found = bool(best_rc is not None and float(best_rc) < -abs(float(negative_eps)))
    restricted_by_forbidden_patterns = forbidden_pattern_count > 0 or forbidden_task_set_count > 0
    can_certify_no_negative = bool(
        (
            (optimal and not negative_found and best_rc is not None and not negative_feasibility_search)
            or infeasible
        )
        and not restricted_by_forbidden_patterns
    )
    if negative_found:
        pricing_state = "FOUND_NEGATIVE"
    elif can_certify_no_negative:
        pricing_state = "CERTIFIED_NO_NEGATIVE"
    else:
        pricing_state = "INCOMPLETE_LIMIT"
    if optimal:
        algorithm_status = "COMPACT_HIGHS_PRICING_OPTIMAL"
    elif infeasible:
        algorithm_status = (
            "COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE"
            if restricted_by_forbidden_patterns
            else "COMPACT_HIGHS_PRICING_INFEASIBLE_NO_NEGATIVE"
            if negative_feasibility_search
            else "COMPACT_HIGHS_PRICING_INFEASIBLE_NO_COLUMNS"
        )
    else:
        algorithm_status = f"COMPACT_HIGHS_PRICING_{status_name}"
    return {
        "status": algorithm_status,
        "algorithm_status": algorithm_status,
        "exact_status": (
            (
                "RESTRICTED_NEGATIVE_FEASIBILITY_INFEASIBLE"
                if restricted_by_forbidden_patterns
                else "EXACT_NEGATIVE_FEASIBILITY_INFEASIBLE"
            )
            if infeasible and negative_feasibility_search
            else "EXACT_PRICING_OPTIMAL"
            if optimal and not restricted_by_forbidden_patterns
            else "RESTRICTED_PRICING_OPTIMAL"
            if optimal
            else "NOT_SOLVED"
        ),
        "pricing_state": pricing_state,
        "task_count": len(tasks),
        "solver_backend": "HiGHS compact single-journey pricing MILP",
        "pricing_complete_by_compact_milp": bool((optimal or infeasible) and not restricted_by_forbidden_patterns),
        "pricing_complete_for_all_tasks": bool((optimal or infeasible) and not restricted_by_forbidden_patterns),
        "pricing_complete_for_all_task_subsets": bool((optimal or infeasible) and not restricted_by_forbidden_patterns),
        "best_reduced_cost": None if best_rc is None else round(float(best_rc), 9),
        "model_objective": None if model_objective is None else round(float(model_objective), 9),
        "manual_best_reduced_cost": None if manual_rc is None else round(float(manual_rc), 9),
        "pricing_best_reduced_cost": None if best_rc is None else round(float(best_rc), 9),
        "dual_bound": None if bound is None else round(float(bound), 9),
        "bound": None if bound is None else round(float(bound), 9),
        "gap": None if gap is None else round(float(gap), 9),
        "negative_found": negative_found,
        "negative_column_count": int(negative_found),
        "can_certify_no_negative": can_certify_no_negative,
        "uses_true_dual_bpc_certificate": can_certify_no_negative,
        "pricing_rc_audit_pass": bool(
            best_rc is None
            or manual_rc is None
            or abs(float(best_rc) - float(manual_rc)) <= 1.0e-6
        ),
        "journeys": tuple(journeys),
        "journey_count": len(journeys),
        "has_feasible_incumbent": bool(journeys),
        "best_column": _pricing_best_column_payload(best_journey),
        "model_status_code": int(status),
        "model_status_name": status_name,
        "solver_info": solver_info,
        "flow_connectivity_enabled": bool(flow_connectivity),
        "mtz_connectivity_enabled": bool(mtz_connectivity),
        "mtz_endpoint_order_cuts_enabled": bool(mtz_connectivity and mtz_endpoint_order_cuts),
        "mtz_endpoint_order_cut_count": int(mtz_endpoint_order_cut_count_total),
        "pair_adjacency_cuts_enabled": bool(pair_adjacency_cuts),
        "pair_adjacency_cut_count": int(pair_adjacency_cut_count_total),
        "negative_feasibility_search_enabled": bool(negative_feasibility_search),
        "forbidden_arc_pattern_count": int(forbidden_pattern_count),
        "forbidden_arc_patterns_can_certify_full_space": bool(forbidden_pattern_count == 0),
        "forbidden_task_set_count": int(forbidden_task_set_count),
        "forbidden_task_sets_can_certify_full_space": bool(forbidden_task_set_count == 0),
        "sortie_slots_per_journey": sortie_slots,
        "sortie_slot_bound_source": slot_bound["source"] if max_sorties_per_journey is None else "explicit",
        "latest_service_start_slot_bound_enabled": bool(latest_service_start_slot_bound)
        if max_sorties_per_journey is None
        else False,
        "sortie_slot_horizon_count_bound": slot_bound["horizon_slot_count_bound"],
        "sortie_slot_latest_start_count_bound": slot_bound["latest_start_slot_count_bound"],
        "sortie_slot_latest_service_start_upper_bound": slot_bound["latest_service_start_upper_bound"],
        "sortie_slot_min_depot_outbound_travel_lower_bound": slot_bound["min_depot_outbound_travel_lower_bound"],
        "sortie_slot_min_duration_lower_bound": slot_bound["min_duration_lower_bound"],
        "sortie_slot_min_return_duration_lower_bound": slot_bound["min_return_duration_lower_bound"],
        "sortie_slot_min_out_return_travel_lower_bound": slot_bound["min_out_return_travel_lower_bound"],
        **pruning,
        "variable_count": int(highs.getNumCol()),
        "constraint_count": int(highs.getNumRow()),
        "wall_time_sec": round(perf_counter() - start_wall, 6),
        "note": (
            "Compact HiGHS single-journey pricing solved exactly."
            if optimal
            else (
                (
                    "Compact HiGHS single-journey negative-feasibility model proved no negative reduced-cost journey exists."
                    if forbidden_pattern_count == 0
                    else "Restricted compact HiGHS negative-feasibility discovery stopped after excluding prior arc patterns; this is not a full-space no-negative certificate."
                )
                if infeasible and negative_feasibility_search
                else (
                "Compact HiGHS single-journey pricing proved there are no feasible nonempty journey columns."
                if infeasible
                else "Compact HiGHS single-journey pricing stopped before an exact pricing proof."
                )
            )
        ),
    }


def _pricing_best_column_payload(column: JourneyColumn | None) -> dict | None:
    if column is None:
        return None
    return {
        "task_count": len(column.task_set),
        "tasks": sorted(column.task_set),
        "objective": column.objective,
        "end_time": column.end_time,
        "sortie_count": len(column.sorties),
        "legs": [
            [
                {"from": leg.source, "to": leg.target, "path_type": leg.path_type}
                for leg in sortie.legs
            ]
            for sortie in column.sorties
        ],
    }


def _highs_info_payload(info) -> dict:
    fields = (
        "valid",
        "objective_function_value",
        "mip_dual_bound",
        "mip_gap",
        "mip_node_count",
        "simplex_iteration_count",
        "ipm_iteration_count",
        "pdlp_iteration_count",
        "primal_solution_status",
        "dual_solution_status",
        "max_primal_infeasibility",
        "max_dual_infeasibility",
        "max_integrality_violation",
        "primal_dual_integral",
    )
    payload = {}
    for field in fields:
        value = getattr(info, field, None)
        if isinstance(value, bool):
            payload[field] = value
        elif isinstance(value, int):
            payload[field] = int(value)
        else:
            payload[field] = _finite_or_none(value)
    return payload


def _finite_or_none(value) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _normalize_forbidden_arc_pattern(
    pattern: Iterable[tuple[int, str, str, str]],
) -> tuple[tuple[int, str, str, str], ...]:
    normalized: list[tuple[int, str, str, str]] = []
    for row in pattern:
        if len(row) != 4:
            continue
        slot, source, target, path_type = row
        normalized.append((int(slot), str(source), str(target), str(path_type)))
    return tuple(normalized)


def _normalize_forbidden_task_set(
    task_set: Iterable[str],
    *,
    valid_tasks: set[str],
) -> tuple[str, ...]:
    normalized = sorted({str(task_id) for task_id in task_set if str(task_id) in valid_tasks})
    return tuple(normalized)


def _highs_status_name(status) -> str:
    text = str(status).split(".")[-1]
    if text.startswith("k") and len(text) > 1 and text[1].isupper():
        text = text[1:]
    return text.upper()


def _set_highs_singleton_mip_start(
    highs,
    *,
    data: LunarIceData,
    tasks: tuple[str, ...],
    path_type_cache: dict[tuple[str, str], tuple[str, ...]],
    vehicle_count: int,
    sortie_slots: int,
    x: dict[tuple[int, int, str, str, str], int],
    y: dict[tuple[int, int, str], int],
    z: dict[tuple[int, int], int],
    service_start: dict[tuple[int, int, str], int],
    sortie_start: dict[tuple[int, int], int],
    sortie_return: dict[tuple[int, int], int],
    sortie_end: dict[tuple[int, int], int],
    reference_solution: dict | None = None,
) -> dict:
    payload = {
        "enabled": True,
        "status": "NOT_SET",
        "entry_count": 0,
        "sortie_count": 0,
        "objective": None,
        "source": "",
        "note": "",
    }
    source = "singleton_sortie_greedy"
    schedule = None
    reference_failure = ""
    if reference_solution:
        schedule, reference_failure = _build_reference_warm_start_schedule(
            data,
            tasks=tasks,
            reference_solution=reference_solution,
            path_type_cache=path_type_cache,
            vehicle_count=vehicle_count,
            sortie_slots=sortie_slots,
        )
        if schedule is not None:
            source = "instance_reference_solution"
    if schedule is None:
        schedule = _build_singleton_warm_start_schedule(
            data,
            tasks=tasks,
            path_type_cache=path_type_cache,
            vehicle_count=vehicle_count,
            sortie_slots=sortie_slots,
        )
    if schedule is None:
        payload["status"] = "NO_FEASIBLE_SINGLETON_SCHEDULE"
        payload["source"] = source
        payload["note"] = (
            "Could not construct a feasible singleton-sortie warm start covering all tasks."
            if not reference_failure
            else f"Reference warm start failed ({reference_failure}); singleton fallback also failed."
        )
        return payload

    values: dict[int, float] = {}
    selected_sorties = 0
    for vehicle, sorties in enumerate(schedule):
        previous_end = 0.0
        for slot in range(sortie_slots):
            if slot < len(sorties):
                sortie = sorties[slot]
                selected_sorties += 1
                values[z[vehicle, slot]] = 1.0
                values[sortie_start[vehicle, slot]] = float(sortie.start_time)
                values[sortie_return[vehicle, slot]] = float(sortie.return_time)
                values[sortie_end[vehicle, slot]] = float(sortie.end_time)
                for task_id in sortie.tasks:
                    values[y[vehicle, slot, task_id]] = 1.0
                    values[service_start[vehicle, slot, task_id]] = float(sortie.service_starts[task_id])
                for leg in sortie.legs:
                    key = (vehicle, slot, str(leg.source), str(leg.target), str(leg.path_type))
                    if key not in x:
                        payload["status"] = "MISSING_ARC_VARIABLE"
                        payload["note"] = f"Warm-start leg has no compact x variable: {key!r}."
                        return payload
                    values[x[key]] = 1.0
                previous_end = float(sortie.end_time)
            else:
                # Inactive slots after active sorties must still respect sortie_start[q] >= sortie_end[q-1].
                if previous_end > 0.0:
                    values[sortie_start[vehicle, slot]] = previous_end
                    values[sortie_end[vehicle, slot]] = previous_end

    try:
        import numpy as np
    except Exception as exc:  # pragma: no cover - numpy is part of highspy's runtime stack locally
        payload["status"] = "NUMPY_UNAVAILABLE"
        payload["note"] = f"Could not pass sparse HiGHS solution without numpy: {type(exc).__name__}: {exc}"
        return payload

    indices = np.array(sorted(values), dtype=np.int32)
    col_values = np.array([values[int(index)] for index in indices], dtype=np.float64)
    try:
        status = highs.setSolution(len(indices), indices, col_values)
    except Exception as exc:
        payload["status"] = "SET_SOLUTION_ERROR"
        payload["entry_count"] = int(len(indices))
        payload["sortie_count"] = int(selected_sorties)
        payload["note"] = f"highs.setSolution failed: {type(exc).__name__}: {exc}"
        return payload

    journeys = tuple(
        build_journey_column(data, tuple(sorties))
        for sorties in schedule
        if sorties
    )
    payload["status"] = _highs_status_name(status)
    payload["entry_count"] = int(len(indices))
    payload["sortie_count"] = int(selected_sorties)
    payload["objective"] = round(sum(journey.objective for journey in journeys), 6) if journeys else None
    payload["source"] = source
    payload["note"] = f"{source} warm start was passed to HiGHS."
    return payload


def _build_reference_warm_start_schedule(
    data: LunarIceData,
    *,
    tasks: tuple[str, ...],
    reference_solution: dict,
    path_type_cache: dict[tuple[str, str], tuple[str, ...]],
    vehicle_count: int,
    sortie_slots: int,
) -> tuple[tuple[TimedSortie, ...], ...] | tuple[None, str]:
    journeys = list(reference_solution.get("journeys") or [])
    if not journeys:
        return None, "missing journeys"
    if len(journeys) > vehicle_count:
        return None, f"journey_count={len(journeys)} exceeds vehicle_count={vehicle_count}"

    covered: set[str] = set()
    schedule: list[list[TimedSortie]] = [[] for _ in range(vehicle_count)]
    for vehicle, journey_payload in enumerate(journeys):
        sorties_payload = list(journey_payload.get("sorties") or [])
        if len(sorties_payload) > sortie_slots:
            return None, f"vehicle {vehicle} sortie_count={len(sorties_payload)} exceeds slots={sortie_slots}"
        previous_end = 0.0
        for sortie_payload in sorties_payload:
            legs_payload = list(sortie_payload.get("legs") or [])
            if not legs_payload:
                return None, f"vehicle {vehicle} has sortie without legs"
            sequence = tuple(str(leg["to"]) for leg in legs_payload if str(leg.get("to")) != "depot")
            path_types = tuple(str(leg["path_type"]) for leg in legs_payload)
            if len(path_types) != len(sequence) + 1:
                return None, f"vehicle {vehicle} sortie has inconsistent legs/path types"
            if covered.intersection(sequence):
                return None, f"duplicate task in reference warm start: {sorted(covered.intersection(sequence))}"
            reference_start_time = float(sortie_payload.get("start_time", previous_end))
            start_time = max(reference_start_time, previous_end)
            sortie = _best_available_sortie_for_sequence(
                data,
                sequence=sequence,
                preferred_path_types=path_types,
                start_time=start_time,
                path_type_cache=path_type_cache,
            )
            if sortie is None:
                return None, "reference sortie cannot be represented with compact path options"
            schedule[vehicle].append(sortie)
            covered.update(sequence)
            previous_end = float(sortie.end_time)

    missing = set(tasks) - covered
    extra = covered - set(tasks)
    if missing or extra:
        return None, f"task coverage mismatch missing={len(missing)} extra={len(extra)}"
    return tuple(tuple(sorties) for sorties in schedule), ""


def _best_available_sortie_for_sequence(
    data: LunarIceData,
    *,
    sequence: tuple[str, ...],
    preferred_path_types: tuple[str, ...],
    start_time: float,
    path_type_cache: dict[tuple[str, str], tuple[str, ...]],
) -> TimedSortie | None:
    nodes = ("depot", *sequence, "depot")
    choices: list[tuple[str, ...]] = []
    for index, (source, target) in enumerate(zip(nodes[:-1], nodes[1:])):
        available = tuple(path_type_cache.get((str(source), str(target)), tuple()))
        if not available:
            return None
        preferred = preferred_path_types[index] if index < len(preferred_path_types) else ""
        ordered = tuple(dict.fromkeys((preferred, *available))) if preferred in available else available
        choices.append(tuple(ordered))

    best = None
    for path_types in product(*choices):
        sortie = build_timed_sortie(data, sequence, tuple(str(path_type) for path_type in path_types), start_time=start_time)
        if not sortie.feasible:
            continue
        objective = build_journey_column(data, (sortie,)).objective
        key = (
            float(objective),
            float(sortie.end_time),
            float(sortie.return_time),
            tuple(str(path_type) for path_type in path_types),
        )
        if best is None or key < best[0]:
            best = (key, sortie)
    return None if best is None else best[1]


def _build_singleton_warm_start_schedule(
    data: LunarIceData,
    *,
    tasks: tuple[str, ...],
    path_type_cache: dict[tuple[str, str], tuple[str, ...]],
    vehicle_count: int,
    sortie_slots: int,
) -> tuple[tuple, ...] | None:
    if len(tasks) > vehicle_count * sortie_slots:
        return None
    schedule: list[list] = [[] for _ in range(vehicle_count)]
    available = [0.0 for _ in range(vehicle_count)]
    ordered_tasks = sorted(
        tasks,
        key=lambda task_id: (
            float(data.tasks[task_id].due_time),
            float(data.tasks[task_id].ready_time),
            str(task_id),
        ),
    )
    for task_id in ordered_tasks:
        best = None
        for vehicle in range(vehicle_count):
            if len(schedule[vehicle]) >= sortie_slots:
                continue
            start_time = float(available[vehicle])
            for outbound in path_type_cache.get(("depot", str(task_id)), tuple()):
                for inbound in path_type_cache.get((str(task_id), "depot"), tuple()):
                    sortie = build_timed_sortie(
                        data,
                        (str(task_id),),
                        (str(outbound), str(inbound)),
                        start_time=start_time,
                    )
                    if not sortie.feasible:
                        continue
                    candidate_key = (
                        float(sortie.end_time),
                        float(sortie.task_completion_times[str(task_id)]),
                        len(schedule[vehicle]),
                        vehicle,
                        str(outbound),
                        str(inbound),
                    )
                    if best is None or candidate_key < best[0]:
                        best = (candidate_key, vehicle, sortie)
        if best is None:
            return None
        _key, vehicle, sortie = best
        schedule[vehicle].append(sortie)
        available[vehicle] = float(sortie.end_time)
    return tuple(tuple(sorties) for sorties in schedule)


def _extract_highs_journeys(
    data: LunarIceData,
    col_values: tuple[float, ...],
    x: dict[tuple[int, int, str, str, str], int],
    z: dict[tuple[int, int], int],
    sortie_start: dict[tuple[int, int], int],
    vehicle_count: int,
    sortie_slots: int,
    nodes: tuple[str, ...],
) -> tuple[JourneyColumn, ...]:
    journeys: list[JourneyColumn] = []
    for vehicle in range(vehicle_count):
        sorties = []
        for slot in range(sortie_slots):
            if col_values[z[vehicle, slot]] <= 0.5:
                continue
            sequence: list[str] = []
            path_types: list[str] = []
            current = "depot"
            visited = set()
            for _ in range(len(nodes) + 1):
                selected = []
                for key, col in x.items():
                    v, s, source, target, path_type = key
                    if v == vehicle and s == slot and source == current and col_values[col] > 0.5:
                        selected.append((target, path_type))
                if not selected:
                    break
                target, path_type = selected[0]
                path_types.append(path_type)
                if target == "depot":
                    break
                if target in visited:
                    break
                visited.add(target)
                sequence.append(target)
                current = target
            if sequence and len(path_types) == len(sequence) + 1:
                sortie = build_timed_sortie(
                    data,
                    tuple(sequence),
                    tuple(path_types),
                    start_time=col_values[sortie_start[vehicle, slot]],
                )
                if sortie.feasible:
                    sorties.append(sortie)
        if sorties:
            journeys.append(build_journey_column(data, tuple(sorties)))
    return tuple(journeys)
