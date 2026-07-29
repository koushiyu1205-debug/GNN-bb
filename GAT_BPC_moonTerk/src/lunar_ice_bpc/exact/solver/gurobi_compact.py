"""Optional compact MILP oracles for lunar-ice fixed-graph experiments."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations, permutations, product
import math
import os
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


COMPACT_HIGHS_OPTION_ENV_PREFIX = "LUNAR_ICE_COMPACT_HIGHS_"
COMPACT_MIP_START_SORT_INDICES_ENV = "LUNAR_ICE_COMPACT_MIP_START_SORT_INDICES"


def _env_bool_value(raw: str) -> bool:
    value = str(raw).strip().lower()
    return value in {"1", "true", "t", "yes", "y", "on"}


def _apply_compact_highs_option_overrides(highs) -> dict:
    """Apply exact-safe HiGHS search-option overrides for compact pricing probes."""

    option_specs = {
        "random_seed": int,
        "mip_detect_symmetry": _env_bool_value,
        "mip_heuristic_effort": float,
        "mip_heuristic_run_feasibility_jump": _env_bool_value,
        "mip_heuristic_run_rens": _env_bool_value,
        "mip_heuristic_run_rins": _env_bool_value,
        "mip_heuristic_run_root_reduced_cost": _env_bool_value,
        "mip_heuristic_run_shifting": _env_bool_value,
        "mip_heuristic_run_zi_round": _env_bool_value,
        "mip_pscost_minreliable": int,
        "mip_lp_age_limit": int,
        "mip_pool_age_limit": int,
        "mip_report_level": int,
        "presolve": str,
        "parallel": str,
        "simplex_strategy": int,
        "simplex_scale_strategy": int,
    }
    applied: dict[str, object] = {}
    for option_name, parser in option_specs.items():
        env_name = f"{COMPACT_HIGHS_OPTION_ENV_PREFIX}{option_name.upper()}"
        raw = os.environ.get(env_name)
        if raw is None:
            continue
        try:
            value = parser(raw)
            highs.setOptionValue(option_name, value)
            applied[option_name] = value
        except Exception as exc:  # pragma: no cover - defensive telemetry
            applied[f"{option_name}_error"] = f"{type(exc).__name__}: {exc}"
    return applied


def _compact_mip_start_sort_indices_enabled() -> bool:
    raw = os.environ.get(COMPACT_MIP_START_SORT_INDICES_ENV)
    if raw is None:
        return True
    return _env_bool_value(raw)


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
        + 2 * arc_var_count
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
        "sortie_slot_min_sortie_energy_lower_bound": slot_bound["min_sortie_energy_lower_bound"],
        "sortie_slot_min_energy_recharge_duration_lower_bound": (
            slot_bound["min_energy_recharge_duration_lower_bound"]
        ),
        "binary_arc_var_count": int(arc_var_count),
        **pruning,
        "task_assignment_var_count": int(y_count),
        "estimated_variable_count": int(variable_count),
        "estimated_constraint_count": int(constraint_count),
        "path_option_policy": str(data.path_option_policy_id),
    }


def _safe_sortie_slot_bound(
    data: LunarIceData,
    *,
    latest_service_start_bound: bool = True,
    recharge_aware_duration_bound: bool = False,
) -> dict:
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
            "min_sortie_energy_lower_bound": 0.0,
            "min_energy_recharge_duration_lower_bound": 0.0,
            "recharge_aware_duration_bound_enabled": bool(recharge_aware_duration_bound),
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
    min_outbound_energy = min(
        float(option.energy_proxy)
        for task_id in tasks
        for option in data.arcs[("depot", str(task_id))].values()
    )
    min_return_energy = min(
        float(option.energy_proxy)
        for task_id in tasks
        for option in data.arcs[(str(task_id), "depot")].values()
    )
    min_service_energy = min(float(task.service_energy) for task in data.tasks.values())
    min_sortie_energy = max(
        0.0,
        float(min_outbound_energy) + float(min_return_energy) + float(min_service_energy),
    )
    min_recharge_duration_available = float(min_sortie_energy) / max(
        1.0e-9,
        float(data.recharge_power_proxy_per_min),
    )
    min_recharge_duration = (
        float(min_recharge_duration_available)
        if bool(recharge_aware_duration_bound)
        else 0.0
    )
    min_out_return_travel = max(1.0e-9, min_outbound + min_return)
    min_return_duration = max(1.0e-9, min_outbound + min_return + min_service)
    min_duration = max(
        1.0e-9,
        min_return_duration + float(data.dock_overhead_min) + float(min_recharge_duration),
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
        "min_sortie_energy_lower_bound": round(float(min_sortie_energy), 9),
        "min_energy_recharge_duration_lower_bound": round(float(min_recharge_duration), 9),
        "min_energy_recharge_duration_available_lower_bound": round(
            float(min_recharge_duration_available),
            9,
        ),
        "recharge_aware_duration_bound_enabled": bool(recharge_aware_duration_bound),
    }


def _max_slot_task_matching(
    slot_feasible_tasks: dict[int, tuple[str, ...]],
    slot_capacities: dict[int, int],
) -> int:
    """Maximum distinct task count assignable to slot copies under safe slot capacities."""

    slot_copies: list[tuple[int, int]] = []
    for slot, capacity in sorted(slot_capacities.items()):
        for copy_index in range(max(0, int(capacity))):
            slot_copies.append((int(slot), int(copy_index)))
    matched_copy_by_task: dict[str, int] = {}

    def _augment(copy_index: int, seen_tasks: set[str]) -> bool:
        slot, _copy = slot_copies[copy_index]
        for task_id in slot_feasible_tasks.get(slot, tuple()):
            if task_id in seen_tasks:
                continue
            seen_tasks.add(task_id)
            previous_copy = matched_copy_by_task.get(task_id)
            if previous_copy is None or _augment(previous_copy, seen_tasks):
                matched_copy_by_task[task_id] = copy_index
                return True
        return False

    matching_size = 0
    for copy_index in range(len(slot_copies)):
        if _augment(copy_index, set()):
            matching_size += 1
    return int(matching_size)


def _min_prefix_slots_for_task_count(
    slot_capacities: Iterable[int],
    task_count: int,
) -> int | None:
    """Minimum ordered prefix length whose safe slot capacities can cover tasks."""

    remaining = int(task_count)
    if remaining <= 0:
        return 0
    covered = 0
    for index, capacity in enumerate(slot_capacities, start=1):
        covered += max(0, int(capacity))
        if int(covered) >= remaining:
            return int(index)
    return None


def _slot_task_sequence_capacity_bounds(
    data: LunarIceData,
    *,
    model_tasks: tuple[str, ...],
    slot_feasible_tasks: dict[int, tuple[str, ...]],
    min_active_duration: float,
    min_depot_outbound_travel: float,
    min_return_travel: float,
) -> dict:
    """Safe per-slot task-count upper bounds from time-window and horizon lower bounds."""

    if not model_tasks:
        return {
            "slot_sequence_capacity_by_slot": [],
            "slot_sequence_capacity_upper_bound": 0,
            "slot_sequence_capacity_limited_slot_count": 0,
            "slot_sequence_capacity_empty_slot_count": 0,
            "slot_matching_capacity_upper_bound": 0,
        }
    min_service = min(float(data.tasks[task_id].service_time) for task_id in model_tasks)
    min_service_energy = min(float(data.tasks[task_id].service_energy) for task_id in model_tasks)
    min_intertask_travel = 0.0
    min_intertask_energy = 0.0
    if len(model_tasks) > 1:
        min_intertask_travel = min(
            float(option.travel_time_min)
            for source in model_tasks
            for target in model_tasks
            if source != target
            for option in data.arcs[(str(source), str(target))].values()
        )
        min_intertask_energy = min(
            float(option.energy_proxy)
            for source in model_tasks
            for target in model_tasks
            if source != target
            for option in data.arcs[(str(source), str(target))].values()
        )
    min_outbound_energy = min(
        float(option.energy_proxy)
        for task_id in model_tasks
        for option in data.arcs[("depot", str(task_id))].values()
    )
    min_return_energy = min(
        float(option.energy_proxy)
        for task_id in model_tasks
        for option in data.arcs[(str(task_id), "depot")].values()
    )
    max_tasks_per_slot = max(1, int(data.max_tasks_per_trip))
    slot_capacities: dict[int, int] = {}
    limited_slot_count = 0
    for slot, feasible_tasks in sorted(slot_feasible_tasks.items()):
        latest_starts = sorted(
            (
                float(data.tasks[task_id].due_time) - float(data.tasks[task_id].service_time)
                for task_id in feasible_tasks
            ),
            reverse=True,
        )
        raw_capacity = min(max_tasks_per_slot, len(latest_starts))
        capacity = 0
        earliest_slot_start = float(slot) * float(min_active_duration)
        for task_count in range(1, raw_capacity + 1):
            kth_service_start_lb = (
                earliest_slot_start
                + float(min_depot_outbound_travel)
                + float(task_count - 1) * (float(min_service) + float(min_intertask_travel))
            )
            if kth_service_start_lb > latest_starts[task_count - 1] + 1.0e-9:
                break
            route_return_lb = (
                earliest_slot_start
                + float(min_depot_outbound_travel)
                + float(task_count) * float(min_service)
                + float(task_count - 1) * float(min_intertask_travel)
                + float(min_return_travel)
            )
            energy_lb = (
                float(min_outbound_energy)
                + float(min_return_energy)
                + float(task_count) * float(min_service_energy)
                + float(task_count - 1) * float(min_intertask_energy)
            )
            recharge_lb = energy_lb / max(1.0e-9, float(data.recharge_power_proxy_per_min))
            end_lb = route_return_lb + float(data.dock_overhead_min) + recharge_lb
            if route_return_lb > float(data.horizon) + 1.0e-9 or end_lb > float(data.horizon) + 1.0e-9:
                break
            capacity = task_count
        slot_capacities[int(slot)] = int(capacity)
        if int(capacity) < int(raw_capacity):
            limited_slot_count += 1
    return {
        "slot_sequence_capacity_by_slot": [
            int(slot_capacities.get(slot, 0)) for slot in sorted(slot_feasible_tasks)
        ],
        "slot_sequence_capacity_upper_bound": int(sum(slot_capacities.values())),
        "slot_sequence_capacity_limited_slot_count": int(limited_slot_count),
        "slot_sequence_capacity_empty_slot_count": int(
            sum(1 for capacity in slot_capacities.values() if int(capacity) <= 0)
        ),
        "slot_matching_capacity_upper_bound": _max_slot_task_matching(
            slot_feasible_tasks,
            slot_capacities,
        ),
    }


def _first_zero_capacity_slot(slot_capacities: Iterable[int]) -> int | None:
    """Return the first prefix slot that cannot carry any task."""

    for index, capacity in enumerate(slot_capacities):
        if int(capacity) <= 0:
            return int(index)
    return None


def _task_slot_pair_conflict_capacity_upper_bound(
    *,
    highspy_module,
    model_tasks: tuple[str, ...],
    slot_feasible_tasks: dict[int, tuple[str, ...]],
    slot_capacities: dict[int, int],
    pair_conflicts: set[tuple[str, str]],
    hyperedge_conflicts: set[tuple[str, ...]] | None = None,
    time_limit_sec: float = 1.0,
    threads: int = 1,
) -> dict:
    """Exact small MILP upper bound for assignable tasks under pair conflicts."""

    start_wall = perf_counter()
    if not model_tasks or not slot_feasible_tasks:
        return {
            "enabled": True,
            "optimal": True,
            "upper_bound": 0,
            "variable_count": 0,
            "constraint_count": 0,
            "pair_conflict_count": int(len(pair_conflicts)),
            "hyperedge_conflict_count": int(len(hyperedge_conflicts or set())),
            "wall_time_sec": round(perf_counter() - start_wall, 6),
            "status": "EMPTY",
        }
    highs = highspy_module.Highs()
    highs.setOptionValue("output_flag", False)
    highs.setOptionValue("threads", max(1, int(threads)))
    highs.setOptionValue("mip_rel_gap", 0.0)
    highs.setOptionValue("time_limit", max(0.001, float(time_limit_sec)))
    highs.setMinimize()
    infinity = highs.getInfinity()

    def add_var() -> int:
        index = highs.getNumCol()
        highs.addVar(0.0, 1.0)
        highs.changeColCost(index, -1.0)
        highs.changeColIntegrality(index, highspy_module.HighsVarType.kInteger)
        return index

    def add_row(coefficients: dict[int, float], lb: float, ub: float) -> None:
        cleaned = {int(col): float(value) for col, value in coefficients.items() if abs(float(value)) > 1.0e-12}
        highs.addRow(float(lb), float(ub), len(cleaned), list(cleaned), list(cleaned.values()))

    y: dict[tuple[int, str], int] = {}
    for slot, feasible_tasks in sorted(slot_feasible_tasks.items()):
        if int(slot_capacities.get(slot, 0)) <= 0:
            continue
        for task_id in feasible_tasks:
            y[int(slot), str(task_id)] = add_var()
    for task_id in model_tasks:
        coeffs = {col: 1.0 for (slot, row_task), col in y.items() if row_task == str(task_id)}
        if coeffs:
            add_row(coeffs, -infinity, 1.0)
    for slot, feasible_tasks in sorted(slot_feasible_tasks.items()):
        coeffs = {y[int(slot), str(task_id)]: 1.0 for task_id in feasible_tasks if (int(slot), str(task_id)) in y}
        if coeffs:
            add_row(coeffs, -infinity, float(max(0, int(slot_capacities.get(slot, 0)))))
    pair_conflict_row_count = 0
    hyperedge_conflict_row_count = 0
    for slot, feasible_tasks in sorted(slot_feasible_tasks.items()):
        feasible_lookup = set(str(task_id) for task_id in feasible_tasks)
        for left_task, right_task in pair_conflicts:
            if left_task not in feasible_lookup or right_task not in feasible_lookup:
                continue
            left_col = y.get((int(slot), str(left_task)))
            right_col = y.get((int(slot), str(right_task)))
            if left_col is None or right_col is None:
                continue
            add_row({left_col: 1.0, right_col: 1.0}, -infinity, 1.0)
            pair_conflict_row_count += 1
        for conflict in hyperedge_conflicts or set():
            conflict_tasks = tuple(str(task_id) for task_id in conflict)
            if len(conflict_tasks) <= 2:
                continue
            if any(task_id not in feasible_lookup for task_id in conflict_tasks):
                continue
            coeffs = {
                y[int(slot), task_id]: 1.0
                for task_id in conflict_tasks
                if (int(slot), task_id) in y
            }
            if len(coeffs) != len(conflict_tasks):
                continue
            add_row(coeffs, -infinity, float(len(conflict_tasks) - 1))
            hyperedge_conflict_row_count += 1
    highs.run()
    status = highs.getModelStatus()
    status_name = str(highs.modelStatusToString(status))
    optimal = status == highspy_module.HighsModelStatus.kOptimal
    upper_bound = None
    if optimal:
        upper_bound = int(round(max(0.0, -float(highs.getObjectiveValue()))))
    return {
        "enabled": True,
        "optimal": bool(optimal),
        "upper_bound": upper_bound,
        "variable_count": int(highs.getNumCol()),
        "constraint_count": int(highs.getNumRow()),
        "pair_conflict_count": int(len(pair_conflicts)),
        "pair_conflict_row_count": int(pair_conflict_row_count),
        "hyperedge_conflict_count": int(len(hyperedge_conflicts or set())),
        "hyperedge_conflict_row_count": int(hyperedge_conflict_row_count),
        "wall_time_sec": round(perf_counter() - start_wall, 6),
        "status": status_name,
    }


def _dual_task_slot_reduced_cost_lower_bound(
    highspy_module,
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    model_tasks: tuple[str, ...],
    slot_feasible_tasks: dict[int, tuple[str, ...]],
    slot_capacities: dict[int, int],
    required_task_count: int,
    required_active_sortie_count: int,
    cost_coeff: float,
    risk_coeff: float,
    completion_coeff: float,
    min_active_duration: float,
    min_depot_travel_by_task: dict[str, float],
    pair_conflicts: set[tuple[str, str]] | None = None,
    hyperedge_conflicts: set[tuple[str, ...]] | None = None,
    time_limit_sec: float = 1.0,
    threads: int = 1,
) -> dict:
    """Small exact assignment relaxation lower bound for a fixed (task-count, sortie-count) region."""

    start_wall = perf_counter()
    if required_task_count < 1 or required_active_sortie_count < 1:
        return {
            "enabled": True,
            "applicable": False,
            "optimal": False,
            "region_infeasible": True,
            "lower_bound": None,
            "variable_count": 0,
            "constraint_count": 0,
            "pair_conflict_row_count": 0,
            "hyperedge_conflict_row_count": 0,
            "wall_time_sec": round(perf_counter() - start_wall, 6),
            "status": "EMPTY_OR_INVALID_REGION",
        }

    active_slots = tuple(range(int(required_active_sortie_count)))
    if any(int(slot_capacities.get(slot, 0)) <= 0 for slot in active_slots):
        return {
            "enabled": True,
            "applicable": True,
            "optimal": True,
            "region_infeasible": True,
            "lower_bound": None,
            "variable_count": 0,
            "constraint_count": 0,
            "pair_conflict_row_count": 0,
            "hyperedge_conflict_row_count": 0,
            "wall_time_sec": round(perf_counter() - start_wall, 6),
            "status": "EMPTY_ACTIVE_SLOT",
        }

    def _arc_objective(source: str, target: str) -> float:
        options = data.arcs.get((str(source), str(target)), {})
        if not options:
            return 0.0
        return min(
            float(cost_coeff) * (float(option.distance_km) + float(option.energy_proxy))
            + float(risk_coeff) * float(option.risk_integral)
            for option in options.values()
        )

    depot_outbound_lb = min((_arc_objective("depot", task_id) for task_id in model_tasks), default=0.0)
    depot_return_lb = min((_arc_objective(task_id, "depot") for task_id in model_tasks), default=0.0)
    intertask_lb = (
        min(
            _arc_objective(source, target)
            for source in model_tasks
            for target in model_tasks
            if source != target
        )
        if len(model_tasks) > 1
        else 0.0
    )
    global_route_arc_constant_lb = (
        float(required_active_sortie_count) * (float(depot_outbound_lb) + float(depot_return_lb))
        + max(0, int(required_task_count) - int(required_active_sortie_count)) * float(intertask_lb)
    )
    slot_outbound_lb_by_slot: dict[int, float] = {}
    slot_return_lb_by_slot: dict[int, float] = {}
    slot_incoming_arc_lb: dict[tuple[int, str], float] = {}
    slot_outgoing_arc_lb: dict[tuple[int, str], float] = {}
    for slot in active_slots:
        feasible_tasks = tuple(str(task_id) for task_id in slot_feasible_tasks.get(slot, tuple()))
        slot_outbound_lb_by_slot[int(slot)] = min(
            (_arc_objective("depot", task_id) for task_id in feasible_tasks),
            default=0.0,
        )
        slot_return_lb_by_slot[int(slot)] = min(
            (_arc_objective(task_id, "depot") for task_id in feasible_tasks),
            default=0.0,
        )
        for task_id in feasible_tasks:
            incoming_sources = ("depot",) + tuple(
                other_task_id for other_task_id in feasible_tasks if other_task_id != task_id
            )
            outgoing_targets = ("depot",) + tuple(
                other_task_id for other_task_id in feasible_tasks if other_task_id != task_id
            )
            slot_incoming_arc_lb[int(slot), task_id] = min(
                (_arc_objective(source, task_id) for source in incoming_sources),
                default=0.0,
            )
            slot_outgoing_arc_lb[int(slot), task_id] = min(
                (_arc_objective(task_id, target) for target in outgoing_targets),
                default=0.0,
            )
    slot_outbound_lb_sum = sum(float(value) for value in slot_outbound_lb_by_slot.values())
    slot_return_lb_sum = sum(float(value) for value in slot_return_lb_by_slot.values())
    slot_route_arc_constant_lb = (
        float(slot_outbound_lb_sum)
        + float(slot_return_lb_sum)
        + max(0, int(required_task_count) - int(required_active_sortie_count)) * float(intertask_lb)
    )
    route_arc_constant_lb = max(float(global_route_arc_constant_lb), float(slot_route_arc_constant_lb))
    constant_lb = -float(duals.fleet_limit)

    highs = highspy_module.Highs()
    highs.setOptionValue("output_flag", False)
    highs.setOptionValue("threads", max(1, int(threads)))
    highs.setOptionValue("mip_rel_gap", 0.0)
    highs.setOptionValue("time_limit", max(0.001, float(time_limit_sec)))
    highs.setMinimize()
    infinity = highs.getInfinity()

    def add_var(
        cost: float,
        *,
        lb: float = 0.0,
        ub: float = 1.0,
        integer: bool = True,
    ) -> int:
        index = highs.getNumCol()
        highs.addVar(float(lb), float(ub))
        highs.changeColCost(index, float(cost))
        if bool(integer):
            highs.changeColIntegrality(index, highspy_module.HighsVarType.kInteger)
        return index

    def add_row(coefficients: dict[int, float], lb: float, ub: float) -> None:
        cleaned = {int(col): float(value) for col, value in coefficients.items() if abs(float(value)) > 1.0e-12}
        highs.addRow(float(lb), float(ub), len(cleaned), list(cleaned), list(cleaned.values()))

    y: dict[tuple[int, str], int] = {}
    weighted_service_start_lb: dict[tuple[int, str], float] = {}
    for slot in active_slots:
        earliest_slot_start = float(slot) * float(min_active_duration)
        for task_id in slot_feasible_tasks.get(slot, tuple()):
            task = data.tasks[str(task_id)]
            service_cost = float(cost_coeff) * (float(task.service_cost) + float(task.service_energy))
            service_cost += float(risk_coeff) * service_risk_value(task)
            service_cost += (
                float(completion_coeff)
                * float(task.science_weight)
                * float(task.service_time)
            )
            service_cost -= float(duals.cover.get(str(task_id), 0.0))
            service_start_lb = max(
                float(task.ready_time),
                earliest_slot_start + float(min_depot_travel_by_task.get(str(task_id), 0.0)),
            )
            weighted_service_start_lb[int(slot), str(task_id)] = (
                max(0.0, float(task.science_weight)) * float(service_start_lb)
            )
            service_cost += (
                float(completion_coeff)
                * float(task.science_weight)
                * float(service_start_lb)
            )
            y[int(slot), str(task_id)] = add_var(service_cost)

    for task_id in model_tasks:
        coeffs = {col: 1.0 for (slot, row_task), col in y.items() if row_task == str(task_id)}
        if coeffs:
            add_row(coeffs, -infinity, 1.0)

    all_coeffs = {col: 1.0 for col in y.values()}
    if all_coeffs:
        add_row(all_coeffs, float(required_task_count), float(required_task_count))
    for slot in active_slots:
        coeffs = {
            y[int(slot), str(task_id)]: 1.0
            for task_id in slot_feasible_tasks.get(slot, tuple())
            if (int(slot), str(task_id)) in y
        }
        if coeffs:
            add_row(coeffs, 1.0, float(max(0, int(slot_capacities.get(slot, 0)))))
        else:
            return {
                "enabled": True,
                "applicable": True,
                "optimal": True,
                "region_infeasible": True,
                "lower_bound": None,
                "variable_count": int(highs.getNumCol()),
                "constraint_count": int(highs.getNumRow()),
                "pair_conflict_row_count": 0,
                "hyperedge_conflict_row_count": 0,
                "wall_time_sec": round(perf_counter() - start_wall, 6),
                "status": "EMPTY_ACTIVE_SLOT",
            }

    pair_conflict_row_count = 0
    hyperedge_conflict_row_count = 0
    for slot in active_slots:
        feasible_lookup = set(str(task_id) for task_id in slot_feasible_tasks.get(slot, tuple()))
        for left_task, right_task in pair_conflicts or set():
            if left_task not in feasible_lookup or right_task not in feasible_lookup:
                continue
            left_col = y.get((int(slot), str(left_task)))
            right_col = y.get((int(slot), str(right_task)))
            if left_col is None or right_col is None:
                continue
            add_row({left_col: 1.0, right_col: 1.0}, -infinity, 1.0)
            pair_conflict_row_count += 1
        for conflict in hyperedge_conflicts or set():
            conflict_tasks = tuple(str(task_id) for task_id in conflict)
            if len(conflict_tasks) <= 2:
                continue
            if any(task_id not in feasible_lookup for task_id in conflict_tasks):
                continue
            coeffs = {
                y[int(slot), task_id]: 1.0
                for task_id in conflict_tasks
                if (int(slot), task_id) in y
            }
            if len(coeffs) != len(conflict_tasks):
                continue
            add_row(coeffs, -infinity, float(len(conflict_tasks) - 1))
            hyperedge_conflict_row_count += 1

    route_arc_lb_col = add_var(1.0, lb=0.0, ub=infinity, integer=False)
    route_arc_bound_row_count = 0
    incoming_coeffs = {route_arc_lb_col: 1.0}
    for (slot, task_id), col in y.items():
        incoming_lb = float(slot_incoming_arc_lb.get((int(slot), str(task_id)), 0.0))
        if incoming_lb:
            incoming_coeffs[int(col)] = incoming_coeffs.get(int(col), 0.0) - incoming_lb
    add_row(incoming_coeffs, float(slot_return_lb_sum), infinity)
    route_arc_bound_row_count += 1
    outgoing_coeffs = {route_arc_lb_col: 1.0}
    for (slot, task_id), col in y.items():
        outgoing_lb = float(slot_outgoing_arc_lb.get((int(slot), str(task_id)), 0.0))
        if outgoing_lb:
            outgoing_coeffs[int(col)] = outgoing_coeffs.get(int(col), 0.0) - outgoing_lb
    add_row(outgoing_coeffs, float(slot_outbound_lb_sum), infinity)
    route_arc_bound_row_count += 1
    add_row({route_arc_lb_col: 1.0}, float(route_arc_constant_lb), infinity)
    route_arc_bound_row_count += 1

    single_task_route_arc_bound_row_count = 0
    single_task_route_arc_bound_min: float | None = None
    single_task_route_arc_bound_max: float | None = None
    if int(required_task_count) == int(required_active_sortie_count):
        single_route_coeffs = {route_arc_lb_col: 1.0}
        for (slot, task_id), col in y.items():
            single_route_lb = max(
                0.0,
                _arc_objective("depot", str(task_id)) + _arc_objective(str(task_id), "depot"),
            )
            if single_route_lb <= 1.0e-12:
                continue
            single_route_coeffs[int(col)] = (
                single_route_coeffs.get(int(col), 0.0) - float(single_route_lb)
            )
            single_task_route_arc_bound_min = (
                float(single_route_lb)
                if single_task_route_arc_bound_min is None
                else min(float(single_task_route_arc_bound_min), float(single_route_lb))
            )
            single_task_route_arc_bound_max = (
                float(single_route_lb)
                if single_task_route_arc_bound_max is None
                else max(float(single_task_route_arc_bound_max), float(single_route_lb))
            )
        if len(single_route_coeffs) > 1:
            add_row(single_route_coeffs, 0.0, infinity)
            single_task_route_arc_bound_row_count = 1

    one_pair_rest_single_route_arc_var_count = 0
    one_pair_rest_single_route_arc_row_count = 0
    one_pair_rest_single_route_arc_pair_count = 0
    one_pair_rest_single_route_arc_separation_row_count = 0
    one_pair_rest_single_route_arc_separation_iteration_count = 0
    one_pair_rest_single_route_arc_big_m = 0.0
    one_pair_rest_single_route_arc_base_coeffs: dict[int, float] = {}
    one_pair_rest_single_route_arc_conditional_rows: dict[
        tuple[int, tuple[str, str]],
        tuple[int, int, float],
    ] = {}
    one_pair_rest_single_route_arc_separated_pairs: set[tuple[int, tuple[str, str]]] = set()
    if (
        int(required_active_sortie_count) >= 2
        and int(required_task_count) == int(required_active_sortie_count) + 1
    ):
        single_route_lb_by_col: dict[int, float] = {}
        for (slot, task_id), col in y.items():
            single_route_lb = max(
                0.0,
                _arc_objective("depot", str(task_id)) + _arc_objective(str(task_id), "depot"),
            )
            single_route_lb_by_col[int(col)] = float(single_route_lb)
        pair_rows: list[tuple[int, str, str, int, int, float]] = []
        max_abs_delta = 0.0
        largest_single_sum = sum(
            sorted(single_route_lb_by_col.values(), reverse=True)[
                : max(0, int(required_task_count))
            ]
        )
        for slot in active_slots:
            feasible_tasks = tuple(str(task_id) for task_id in slot_feasible_tasks.get(slot, tuple()))
            if len(feasible_tasks) < 2:
                continue
            for left_task, right_task in combinations(feasible_tasks, 2):
                left_col = y.get((int(slot), str(left_task)))
                right_col = y.get((int(slot), str(right_task)))
                if left_col is None or right_col is None:
                    continue
                left_then_right = (
                    _arc_objective("depot", str(left_task))
                    + _arc_objective(str(left_task), str(right_task))
                    + _arc_objective(str(right_task), "depot")
                )
                right_then_left = (
                    _arc_objective("depot", str(right_task))
                    + _arc_objective(str(right_task), str(left_task))
                    + _arc_objective(str(left_task), "depot")
                )
                pair_route_lb = max(0.0, min(float(left_then_right), float(right_then_left)))
                one_pair_rest_single_route_arc_pair_count += 1
                left_single_lb = max(
                    0.0,
                    _arc_objective("depot", str(left_task))
                    + _arc_objective(str(left_task), "depot"),
                )
                right_single_lb = max(
                    0.0,
                    _arc_objective("depot", str(right_task))
                    + _arc_objective(str(right_task), "depot"),
                )
                delta = float(pair_route_lb) - float(left_single_lb) - float(right_single_lb)
                pair_rows.append(
                    (
                        int(slot),
                        str(left_task),
                        str(right_task),
                        int(left_col),
                        int(right_col),
                        float(delta),
                    )
                )
                max_abs_delta = max(float(max_abs_delta), abs(float(delta)))
        if pair_rows:
            base_coeffs = {route_arc_lb_col: 1.0}
            for col, single_route_lb in single_route_lb_by_col.items():
                if abs(float(single_route_lb)) > 1.0e-12:
                    base_coeffs[int(col)] = base_coeffs.get(int(col), 0.0) - float(single_route_lb)
            one_pair_rest_single_route_arc_base_coeffs = dict(base_coeffs)
            one_pair_rest_single_route_arc_big_m = max(
                1.0,
                float(largest_single_sum) + float(max_abs_delta) + 1.0,
            )
            for slot, left_task, right_task, left_col, right_col, delta in pair_rows:
                pair_key = (int(slot), tuple(sorted((str(left_task), str(right_task)))))
                one_pair_rest_single_route_arc_conditional_rows[pair_key] = (
                    int(left_col),
                    int(right_col),
                    float(delta),
                )
            min_pair_delta = min(
                float(delta)
                for _slot, _left_task, _right_task, _left_col, _right_col, delta in pair_rows
            )
            add_row(base_coeffs, float(min_pair_delta), infinity)
            one_pair_rest_single_route_arc_row_count += 1

    pair_route_arc_bound_row_count = 0
    pair_route_arc_bound_min: float | None = None
    pair_route_arc_bound_max: float | None = None
    if int(required_task_count) == 2:
        for slot in active_slots:
            feasible_tasks = tuple(str(task_id) for task_id in slot_feasible_tasks.get(slot, tuple()))
            if len(feasible_tasks) < 2:
                continue
            for left_task, right_task in combinations(feasible_tasks, 2):
                left_col = y.get((int(slot), str(left_task)))
                right_col = y.get((int(slot), str(right_task)))
                if left_col is None or right_col is None:
                    continue
                left_then_right = (
                    _arc_objective("depot", str(left_task))
                    + _arc_objective(str(left_task), str(right_task))
                    + _arc_objective(str(right_task), "depot")
                )
                right_then_left = (
                    _arc_objective("depot", str(right_task))
                    + _arc_objective(str(right_task), str(left_task))
                    + _arc_objective(str(left_task), "depot")
                )
                pair_route_lb = max(0.0, min(float(left_then_right), float(right_then_left)))
                if pair_route_lb <= 1.0e-12:
                    continue
                add_row(
                    {
                        route_arc_lb_col: 1.0,
                        int(left_col): -float(pair_route_lb),
                        int(right_col): -float(pair_route_lb),
                    },
                    -float(pair_route_lb),
                    infinity,
                )
                pair_route_arc_bound_row_count += 1
                pair_route_arc_bound_min = (
                    float(pair_route_lb)
                    if pair_route_arc_bound_min is None
                    else min(float(pair_route_arc_bound_min), float(pair_route_lb))
                )
                pair_route_arc_bound_max = (
                    float(pair_route_lb)
                    if pair_route_arc_bound_max is None
                    else max(float(pair_route_arc_bound_max), float(pair_route_lb))
                )

    triple_route_arc_bound_row_count = 0
    triple_route_arc_bound_min: float | None = None
    triple_route_arc_bound_max: float | None = None
    if int(required_task_count) == 3 and int(required_active_sortie_count) == 1:
        for slot in active_slots:
            feasible_tasks = tuple(str(task_id) for task_id in slot_feasible_tasks.get(slot, tuple()))
            if len(feasible_tasks) < 3:
                continue
            for triple in combinations(feasible_tasks, 3):
                cols = [y.get((int(slot), str(task_id))) for task_id in triple]
                if any(col is None for col in cols):
                    continue
                best_route_lb = math.inf
                for order in permutations(tuple(str(task_id) for task_id in triple)):
                    route_lb = _arc_objective("depot", order[0])
                    for source, target in zip(order, order[1:]):
                        route_lb += _arc_objective(source, target)
                    route_lb += _arc_objective(order[-1], "depot")
                    best_route_lb = min(float(best_route_lb), float(route_lb))
                if not math.isfinite(best_route_lb):
                    continue
                triple_route_lb = max(0.0, float(best_route_lb))
                if triple_route_lb <= 1.0e-12:
                    continue
                coeffs = {route_arc_lb_col: 1.0}
                for col in cols:
                    coeffs[int(col)] = coeffs.get(int(col), 0.0) - float(triple_route_lb)
                add_row(coeffs, -2.0 * float(triple_route_lb), infinity)
                triple_route_arc_bound_row_count += 1
                triple_route_arc_bound_min = (
                    float(triple_route_lb)
                    if triple_route_arc_bound_min is None
                    else min(float(triple_route_arc_bound_min), float(triple_route_lb))
                )
                triple_route_arc_bound_max = (
                    float(triple_route_lb)
                    if triple_route_arc_bound_max is None
                    else max(float(triple_route_arc_bound_max), float(triple_route_lb))
                )

    pair_completion_lift_var_count = 0
    pair_completion_lift_row_count = 0
    pair_completion_lift_min: float | None = None
    pair_completion_lift_max: float | None = None
    pair_completion_depot_to = (
        _single_source_shortest_travel_lower_bounds(data, "depot")
        if float(completion_coeff) > 1.0e-12
        else {}
    )
    pair_completion_to_depot = (
        _task_to_depot_shortest_travel_lower_bounds(data)
        if float(completion_coeff) > 1.0e-12
        else {}
    )
    single_task_recharge_duration_lb_by_task = (
        {
            str(task_id): float(energy_lb) / max(1.0e-9, float(data.recharge_power_proxy_per_min))
            for task_id, energy_lb in _single_task_route_energy_lower_bounds(data).items()
        }
        if float(completion_coeff) > 1.0e-12
        else {}
    )
    pair_route_energy_lb_by_pair = (
        _pair_route_energy_lower_bounds(data)
        if float(completion_coeff) > 1.0e-12
        else {}
    )
    pair_completion_from_task = (
        {
            task_id: _single_source_shortest_travel_lower_bounds(data, task_id)
            for task_id in model_tasks
        }
        if float(completion_coeff) > 1.0e-12
        else {}
    )

    def _pair_weighted_start_absolute_lb(
        left_task: str,
        right_task: str,
        *,
        sortie_start_lb: float,
    ) -> float:
        def _ordered(first_task_id: str, second_task_id: str) -> float:
            first = data.tasks[str(first_task_id)]
            second = data.tasks[str(second_task_id)]
            first_weight = max(0.0, float(first.science_weight))
            second_weight = max(0.0, float(second.science_weight))
            first_start = max(
                float(first.ready_time),
                float(sortie_start_lb)
                + float(pair_completion_depot_to.get(str(first_task_id), 0.0)),
            )
            second_start = max(
                float(second.ready_time),
                first_start
                + float(first.service_time)
                + float(pair_completion_from_task[str(first_task_id)].get(str(second_task_id), 0.0)),
            )
            return float(first_weight) * float(first_start) + float(second_weight) * float(second_start)

        return min(
            _ordered(str(left_task), str(right_task)),
            _ordered(str(right_task), str(left_task)),
        )

    for slot in active_slots:
        feasible_tasks = tuple(str(task_id) for task_id in slot_feasible_tasks.get(slot, tuple()))
        if len(feasible_tasks) < 2:
            continue
        lift_col: int | None = None
        earliest_slot_start = float(slot) * float(min_active_duration)
        for left_task, right_task in combinations(feasible_tasks, 2):
            left_col = y.get((int(slot), str(left_task)))
            right_col = y.get((int(slot), str(right_task)))
            if left_col is None or right_col is None:
                continue
            left_weight = max(0.0, float(data.tasks[str(left_task)].science_weight))
            right_weight = max(0.0, float(data.tasks[str(right_task)].science_weight))
            total_weight = float(left_weight) + float(right_weight)
            if total_weight <= 1.0e-12:
                continue
            absolute_pair_lb = _pair_weighted_start_absolute_lb(
                str(left_task),
                str(right_task),
                sortie_start_lb=float(earliest_slot_start),
            )
            individual_pair_lb = float(weighted_service_start_lb.get((int(slot), str(left_task)), 0.0))
            individual_pair_lb += float(weighted_service_start_lb.get((int(slot), str(right_task)), 0.0))
            lift = max(0.0, float(absolute_pair_lb) - float(individual_pair_lb))
            if lift <= 1.0e-9:
                continue
            if lift_col is None:
                lift_col = add_var(
                    float(completion_coeff),
                    lb=0.0,
                    ub=infinity,
                    integer=False,
                )
                pair_completion_lift_var_count += 1
            add_row({lift_col: 1.0, int(left_col): -float(lift), int(right_col): -float(lift)}, -float(lift), infinity)
            pair_completion_lift_row_count += 1
            pair_completion_lift_min = (
                float(lift)
                if pair_completion_lift_min is None
                else min(float(pair_completion_lift_min), float(lift))
            )
            pair_completion_lift_max = (
                float(lift)
                if pair_completion_lift_max is None
                else max(float(pair_completion_lift_max), float(lift))
            )

    cross_slot_completion_lift_var_count = 0
    cross_slot_completion_lift_row_count = 0
    cross_slot_pair_completion_separation_row_count = 0
    cross_slot_completion_lift_min: float | None = None
    cross_slot_completion_lift_max: float | None = None
    cross_slot_lift_col: int | None = None
    if float(completion_coeff) > 1.0e-12 and len(active_slots) >= 2:
        for earlier_slot in active_slots:
            for later_slot in active_slots:
                if int(later_slot) <= int(earlier_slot):
                    continue
                earlier_tasks = tuple(str(task_id) for task_id in slot_feasible_tasks.get(earlier_slot, tuple()))
                later_tasks = tuple(str(task_id) for task_id in slot_feasible_tasks.get(later_slot, tuple()))
                if not earlier_tasks or not later_tasks:
                    continue
                earlier_slot_start_lb = float(earlier_slot) * float(min_active_duration)
                for earlier_task_id in earlier_tasks:
                    earlier_col = y.get((int(earlier_slot), str(earlier_task_id)))
                    if earlier_col is None:
                        continue
                    earlier_task = data.tasks[str(earlier_task_id)]
                    earlier_weight = max(0.0, float(earlier_task.science_weight))
                    earlier_start_lb = max(
                        float(earlier_task.ready_time),
                        float(earlier_slot_start_lb)
                        + float(pair_completion_depot_to.get(str(earlier_task_id), 0.0)),
                    )
                    earlier_sortie_end_lb = (
                        float(earlier_start_lb)
                        + float(earlier_task.service_time)
                        + float(pair_completion_to_depot.get(str(earlier_task_id), 0.0))
                        + float(data.dock_overhead_min)
                        + float(single_task_recharge_duration_lb_by_task.get(str(earlier_task_id), 0.0))
                    )
                    for later_task_id in later_tasks:
                        later_col = y.get((int(later_slot), str(later_task_id)))
                        if later_col is None:
                            continue
                        later_task = data.tasks[str(later_task_id)]
                        later_weight = max(0.0, float(later_task.science_weight))
                        total_weight = float(earlier_weight) + float(later_weight)
                        if total_weight <= 1.0e-12:
                            continue
                        later_start_lb = max(
                            float(later_task.ready_time),
                            float(earlier_sortie_end_lb)
                            + float(pair_completion_depot_to.get(str(later_task_id), 0.0)),
                        )
                        absolute_pair_lb = (
                            float(earlier_weight) * float(earlier_start_lb)
                            + float(later_weight) * float(later_start_lb)
                        )
                        individual_pair_lb = float(
                            weighted_service_start_lb.get((int(earlier_slot), str(earlier_task_id)), 0.0)
                        )
                        individual_pair_lb += float(
                            weighted_service_start_lb.get((int(later_slot), str(later_task_id)), 0.0)
                        )
                        lift = max(0.0, float(absolute_pair_lb) - float(individual_pair_lb))
                        if lift <= 1.0e-9:
                            continue
                        if cross_slot_lift_col is None:
                            cross_slot_lift_col = add_var(
                                float(completion_coeff),
                                lb=0.0,
                                ub=infinity,
                                integer=False,
                            )
                            cross_slot_completion_lift_var_count = 1
                        add_row(
                            {
                                cross_slot_lift_col: 1.0,
                                int(earlier_col): -float(lift),
                                int(later_col): -float(lift),
                            },
                            -float(lift),
                            infinity,
                        )
                        cross_slot_completion_lift_row_count += 1
                        cross_slot_completion_lift_min = (
                            float(lift)
                            if cross_slot_completion_lift_min is None
                            else min(float(cross_slot_completion_lift_min), float(lift))
                        )
                        cross_slot_completion_lift_max = (
                            float(lift)
                            if cross_slot_completion_lift_max is None
                            else max(float(cross_slot_completion_lift_max), float(lift))
                        )

    def _pair_to_later_weighted_later_start_absolute_lb(
        pair_tasks: tuple[str, str],
        later_task_id: str,
        *,
        pair_slot_start_lb: float,
    ) -> float:
        later_task = data.tasks[str(later_task_id)]
        later_weight = max(0.0, float(later_task.science_weight))
        pair_key = tuple(sorted(str(task_id) for task_id in pair_tasks))
        pair_recharge_lb = float(pair_route_energy_lb_by_pair.get(pair_key, 0.0)) / max(
            1.0e-9,
            float(data.recharge_power_proxy_per_min),
        )
        best = math.inf
        for first_task_id, second_task_id in permutations(pair_key):
            first = data.tasks[str(first_task_id)]
            second = data.tasks[str(second_task_id)]
            first_start = max(
                float(first.ready_time),
                float(pair_slot_start_lb)
                + float(pair_completion_depot_to.get(str(first_task_id), 0.0)),
            )
            second_start = max(
                float(second.ready_time),
                float(first_start)
                + float(first.service_time)
                + float(pair_completion_from_task[str(first_task_id)].get(str(second_task_id), 0.0)),
            )
            pair_end = (
                float(second_start)
                + float(second.service_time)
                + float(pair_completion_to_depot.get(str(second_task_id), 0.0))
                + float(data.dock_overhead_min)
                + float(pair_recharge_lb)
            )
            later_start = max(
                float(later_task.ready_time),
                float(pair_end) + float(pair_completion_depot_to.get(str(later_task_id), 0.0)),
            )
            best = min(
                float(best),
                float(later_weight) * float(later_start),
            )
        return float(best) if math.isfinite(best) else 0.0

    def _selected_slot_task_sets_from_solution(solution) -> dict[int, tuple[str, ...]]:
        selected_by_slot: dict[int, list[str]] = defaultdict(list)
        for (slot, task_id), col in y.items():
            if float(solution.col_value[int(col)]) > 0.5:
                selected_by_slot[int(slot)].append(str(task_id))
        return {
            int(slot): tuple(sorted(tasks_for_slot))
            for slot, tasks_for_slot in sorted(selected_by_slot.items())
        }

    def _add_one_pair_rest_single_route_separation_row(solution) -> bool:
        nonlocal one_pair_rest_single_route_arc_separation_row_count
        nonlocal cross_slot_lift_col
        nonlocal cross_slot_completion_lift_var_count
        nonlocal cross_slot_completion_lift_row_count
        nonlocal cross_slot_pair_completion_separation_row_count
        nonlocal cross_slot_completion_lift_min
        nonlocal cross_slot_completion_lift_max
        selected_slot_task_sets = _selected_slot_task_sets_from_solution(solution)
        for slot, tasks_for_slot in selected_slot_task_sets.items():
            if len(tasks_for_slot) != 2:
                continue
            pair_key = (int(slot), tuple(sorted(str(task_id) for task_id in tasks_for_slot)))
            if pair_key in one_pair_rest_single_route_arc_separated_pairs:
                continue
            row_payload = one_pair_rest_single_route_arc_conditional_rows.get(pair_key)
            if row_payload is None:
                continue
            left_col, right_col, delta = row_payload
            big_m = float(one_pair_rest_single_route_arc_big_m)
            if big_m <= 0.0:
                continue
            coeffs = dict(one_pair_rest_single_route_arc_base_coeffs)
            coeffs[int(left_col)] = coeffs.get(int(left_col), 0.0) - float(big_m)
            coeffs[int(right_col)] = coeffs.get(int(right_col), 0.0) - float(big_m)
            add_row(coeffs, float(delta) - 2.0 * float(big_m), infinity)
            one_pair_rest_single_route_arc_separated_pairs.add(pair_key)
            one_pair_rest_single_route_arc_separation_row_count += 1
            if float(completion_coeff) > 1.0e-12:
                for later_slot, later_tasks in selected_slot_task_sets.items():
                    if int(later_slot) <= int(slot):
                        continue
                    for later_task_id in later_tasks:
                        later_col = y.get((int(later_slot), str(later_task_id)))
                        if later_col is None:
                            continue
                        absolute_lb = _pair_to_later_weighted_later_start_absolute_lb(
                            tuple(str(task_id) for task_id in tasks_for_slot),
                            str(later_task_id),
                            pair_slot_start_lb=float(slot) * float(min_active_duration),
                        )
                        individual_lb = float(
                            weighted_service_start_lb.get((int(later_slot), str(later_task_id)), 0.0)
                        )
                        lift = max(0.0, float(absolute_lb) - float(individual_lb))
                        if lift <= 1.0e-9:
                            continue
                        if cross_slot_lift_col is None:
                            cross_slot_lift_col = add_var(
                                float(completion_coeff),
                                lb=0.0,
                                ub=infinity,
                                integer=False,
                            )
                            cross_slot_completion_lift_var_count = 1
                        coeffs_completion = {cross_slot_lift_col: 1.0}
                        for task_id in tasks_for_slot:
                            pair_task_col = y.get((int(slot), str(task_id)))
                            if pair_task_col is not None:
                                coeffs_completion[int(pair_task_col)] = (
                                    coeffs_completion.get(int(pair_task_col), 0.0) - float(lift)
                                )
                        coeffs_completion[int(later_col)] = (
                            coeffs_completion.get(int(later_col), 0.0) - float(lift)
                        )
                        add_row(coeffs_completion, -2.0 * float(lift), infinity)
                        cross_slot_completion_lift_row_count += 1
                        cross_slot_pair_completion_separation_row_count += 1
                        cross_slot_completion_lift_min = (
                            float(lift)
                            if cross_slot_completion_lift_min is None
                            else min(float(cross_slot_completion_lift_min), float(lift))
                        )
                        cross_slot_completion_lift_max = (
                            float(lift)
                            if cross_slot_completion_lift_max is None
                            else max(float(cross_slot_completion_lift_max), float(lift))
                        )
            return True
        return False

    highs.run()
    status = highs.getModelStatus()
    status_name = str(highs.modelStatusToString(status))
    optimal = status == highspy_module.HighsModelStatus.kOptimal
    infeasible = status == highspy_module.HighsModelStatus.kInfeasible
    if float(time_limit_sec) >= 1.0:
        max_separation_iterations = 24
    else:
        max_separation_iterations = 0
    while (
        optimal
        and one_pair_rest_single_route_arc_conditional_rows
        and one_pair_rest_single_route_arc_separation_iteration_count < max_separation_iterations
    ):
        remaining = float(time_limit_sec) - float(perf_counter() - start_wall)
        if remaining <= 1.0e-3:
            break
        solution = highs.getSolution()
        if not _add_one_pair_rest_single_route_separation_row(solution):
            break
        one_pair_rest_single_route_arc_separation_iteration_count += 1
        highs.setOptionValue("time_limit", max(0.001, remaining))
        highs.run()
        status = highs.getModelStatus()
        status_name = str(highs.modelStatusToString(status))
        optimal = status == highspy_module.HighsModelStatus.kOptimal
        infeasible = status == highspy_module.HighsModelStatus.kInfeasible
    lower_bound = None
    route_arc_lower_bound_value = None
    selected_task_set: tuple[str, ...] = tuple()
    selected_slot_task_sets: dict[int, tuple[str, ...]] = {}
    if optimal:
        lower_bound = float(highs.getObjectiveValue()) + float(constant_lb)
        solution = highs.getSolution()
        route_arc_lower_bound_value = float(solution.col_value[route_arc_lb_col])
        selected_slot_task_sets = _selected_slot_task_sets_from_solution(solution)
        selected_task_set = tuple(
            sorted(task_id for tasks_for_slot in selected_slot_task_sets.values() for task_id in tasks_for_slot)
        )
    return {
        "enabled": True,
        "applicable": True,
        "optimal": bool(optimal),
        "region_infeasible": bool(infeasible),
        "lower_bound": None if lower_bound is None else round(float(lower_bound), 9),
        "constant_lower_bound": round(float(constant_lb), 9),
        "depot_outbound_arc_lower_bound": round(float(depot_outbound_lb), 9),
        "depot_return_arc_lower_bound": round(float(depot_return_lb), 9),
        "intertask_arc_lower_bound": round(float(intertask_lb), 9),
        "route_arc_lower_bound_mode": "slot_incoming_outgoing_max",
        "route_arc_lower_bound_value": (
            None
            if route_arc_lower_bound_value is None
            else round(float(route_arc_lower_bound_value), 9)
        ),
        "route_arc_lower_bound_row_count": int(route_arc_bound_row_count),
        "route_arc_global_constant_lower_bound": round(float(global_route_arc_constant_lb), 9),
        "route_arc_slot_constant_lower_bound": round(float(slot_route_arc_constant_lb), 9),
        "route_arc_constant_lower_bound": round(float(route_arc_constant_lb), 9),
        "route_arc_slot_outbound_lower_bound_sum": round(float(slot_outbound_lb_sum), 9),
        "route_arc_slot_return_lower_bound_sum": round(float(slot_return_lb_sum), 9),
        "single_task_route_arc_bound_row_count": int(single_task_route_arc_bound_row_count),
        "single_task_route_arc_bound_min": (
            None
            if single_task_route_arc_bound_min is None
            else round(float(single_task_route_arc_bound_min), 9)
        ),
        "single_task_route_arc_bound_max": (
            None
            if single_task_route_arc_bound_max is None
            else round(float(single_task_route_arc_bound_max), 9)
        ),
        "one_pair_rest_single_route_arc_var_count": int(
            one_pair_rest_single_route_arc_var_count
        ),
        "one_pair_rest_single_route_arc_row_count": int(
            one_pair_rest_single_route_arc_row_count
        ),
        "one_pair_rest_single_route_arc_pair_count": int(
            one_pair_rest_single_route_arc_pair_count
        ),
        "one_pair_rest_single_route_arc_separation_row_count": int(
            one_pair_rest_single_route_arc_separation_row_count
        ),
        "one_pair_rest_single_route_arc_separation_iteration_count": int(
            one_pair_rest_single_route_arc_separation_iteration_count
        ),
        "pair_route_arc_bound_row_count": int(pair_route_arc_bound_row_count),
        "pair_route_arc_bound_min": (
            None
            if pair_route_arc_bound_min is None
            else round(float(pair_route_arc_bound_min), 9)
        ),
        "pair_route_arc_bound_max": (
            None
            if pair_route_arc_bound_max is None
            else round(float(pair_route_arc_bound_max), 9)
        ),
        "triple_route_arc_bound_row_count": int(triple_route_arc_bound_row_count),
        "triple_route_arc_bound_min": (
            None
            if triple_route_arc_bound_min is None
            else round(float(triple_route_arc_bound_min), 9)
        ),
        "triple_route_arc_bound_max": (
            None
            if triple_route_arc_bound_max is None
            else round(float(triple_route_arc_bound_max), 9)
        ),
        "pair_completion_lift_var_count": int(pair_completion_lift_var_count),
        "pair_completion_lift_row_count": int(pair_completion_lift_row_count),
        "pair_completion_lift_min": (
            None
            if pair_completion_lift_min is None
            else round(float(pair_completion_lift_min), 9)
        ),
        "pair_completion_lift_max": (
            None
            if pair_completion_lift_max is None
            else round(float(pair_completion_lift_max), 9)
        ),
        "cross_slot_completion_lift_var_count": int(cross_slot_completion_lift_var_count),
        "cross_slot_completion_lift_row_count": int(cross_slot_completion_lift_row_count),
        "cross_slot_pair_completion_separation_row_count": int(
            cross_slot_pair_completion_separation_row_count
        ),
        "cross_slot_completion_lift_min": (
            None
            if cross_slot_completion_lift_min is None
            else round(float(cross_slot_completion_lift_min), 9)
        ),
        "cross_slot_completion_lift_max": (
            None
            if cross_slot_completion_lift_max is None
            else round(float(cross_slot_completion_lift_max), 9)
        ),
        "selected_task_set": list(selected_task_set),
        "selected_slot_task_sets": {
            str(slot): list(tasks_for_slot)
            for slot, tasks_for_slot in selected_slot_task_sets.items()
        },
        "variable_count": int(highs.getNumCol()),
        "constraint_count": int(highs.getNumRow()),
        "pair_conflict_row_count": int(pair_conflict_row_count),
        "hyperedge_conflict_row_count": int(hyperedge_conflict_row_count),
        "wall_time_sec": round(perf_counter() - start_wall, 6),
        "status": status_name,
    }


def _dual_task_slot_full_space_lower_bound_scan(
    highspy_module,
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    model_tasks: tuple[str, ...],
    slot_feasible_tasks: dict[int, tuple[str, ...]],
    slot_capacities: dict[int, int],
    cost_coeff: float,
    risk_coeff: float,
    completion_coeff: float,
    min_active_duration: float,
    min_depot_travel_by_task: dict[str, float],
    pair_conflicts: set[tuple[str, str]] | None = None,
    hyperedge_conflicts: set[tuple[str, ...]] | None = None,
    negative_eps: float = 1.0e-6,
    per_region_time_limit_sec: float = 0.25,
    early_stop_on_negative_bound: bool = True,
    threads: int = 1,
) -> dict:
    """Scan a safe task-count/active-sortie partition lower bound.

    The assignment relaxation lower bound is valid for each exact
    (task-count, active-sortie-count) region.  If every nonempty journey region
    is either infeasible or has lower_bound >= -eps, the full pricing space has
    no negative reduced-cost column.
    """

    start_wall = perf_counter()
    max_task_count = min(
        len(model_tasks),
        sum(max(0, int(capacity)) for capacity in slot_capacities.values()),
    )
    if max_task_count < 1:
        return {
            "enabled": True,
            "applicable": True,
            "coverage_complete": True,
            "can_certify_no_negative": True,
            "region_count": 0,
            "optimal_region_count": 0,
            "infeasible_region_count": 0,
            "unsupported_region_count": 0,
            "negative_bound_region_count": 0,
            "min_lower_bound": None,
            "min_lower_bound_task_count": None,
            "min_lower_bound_active_sortie_count": None,
            "wall_time_sec": round(perf_counter() - start_wall, 6),
            "status": "EMPTY_FULL_SPACE",
        }

    region_count = 0
    optimal_region_count = 0
    infeasible_region_count = 0
    unsupported_region_count = 0
    negative_bound_region_count = 0
    min_lower_bound: float | None = None
    min_lower_bound_task_count: int | None = None
    min_lower_bound_active_sortie_count: int | None = None
    early_stopped_on_negative_bound = False
    max_tasks_per_sortie = max(1, int(data.max_tasks_per_trip))
    sortie_slots = len(slot_feasible_tasks)
    for task_count in range(1, int(max_task_count) + 1):
        min_active_sorties = int(math.ceil(float(task_count) / float(max_tasks_per_sortie)))
        max_active_sorties = min(int(task_count), int(sortie_slots))
        for active_sortie_count in range(min_active_sorties, max_active_sorties + 1):
            region_count += 1
            result = _dual_task_slot_reduced_cost_lower_bound(
                highspy_module,
                data,
                duals,
                model_tasks=model_tasks,
                slot_feasible_tasks=slot_feasible_tasks,
                slot_capacities=slot_capacities,
                required_task_count=int(task_count),
                required_active_sortie_count=int(active_sortie_count),
                cost_coeff=float(cost_coeff),
                risk_coeff=float(risk_coeff),
                completion_coeff=float(completion_coeff),
                min_active_duration=float(min_active_duration),
                min_depot_travel_by_task=min_depot_travel_by_task,
                pair_conflicts=pair_conflicts,
                hyperedge_conflicts=hyperedge_conflicts,
                time_limit_sec=float(per_region_time_limit_sec),
                threads=int(threads),
            )
            if bool(result.get("region_infeasible")):
                infeasible_region_count += 1
                continue
            if not bool(result.get("optimal")) or result.get("lower_bound") is None:
                unsupported_region_count += 1
                continue
            optimal_region_count += 1
            lower_bound = float(result["lower_bound"])
            if min_lower_bound is None or lower_bound < float(min_lower_bound):
                min_lower_bound = lower_bound
                min_lower_bound_task_count = int(task_count)
                min_lower_bound_active_sortie_count = int(active_sortie_count)
            if lower_bound < -abs(float(negative_eps)):
                negative_bound_region_count += 1
                if bool(early_stop_on_negative_bound):
                    early_stopped_on_negative_bound = True
                    break
        if early_stopped_on_negative_bound:
            break

    coverage_complete = bool((not early_stopped_on_negative_bound) and unsupported_region_count == 0)
    can_certify = bool(
        coverage_complete
        and negative_bound_region_count == 0
        and (min_lower_bound is None or float(min_lower_bound) >= -abs(float(negative_eps)))
    )
    if can_certify:
        status = "CERTIFIED_NO_NEGATIVE"
    elif early_stopped_on_negative_bound:
        status = "BOUND_SCAN_NEGATIVE_REGION_EARLY_STOP"
    else:
        status = "BOUND_SCAN_INCOMPLETE_OR_NEGATIVE"
    return {
        "enabled": True,
        "applicable": True,
        "early_stop_on_negative_bound": bool(early_stop_on_negative_bound),
        "early_stopped_on_negative_bound": bool(early_stopped_on_negative_bound),
        "coverage_complete": coverage_complete,
        "can_certify_no_negative": can_certify,
        "region_count": int(region_count),
        "optimal_region_count": int(optimal_region_count),
        "infeasible_region_count": int(infeasible_region_count),
        "unsupported_region_count": int(unsupported_region_count),
        "negative_bound_region_count": int(negative_bound_region_count),
        "min_lower_bound": None if min_lower_bound is None else round(float(min_lower_bound), 9),
        "min_lower_bound_task_count": min_lower_bound_task_count,
        "min_lower_bound_active_sortie_count": min_lower_bound_active_sortie_count,
        "wall_time_sec": round(perf_counter() - start_wall, 6),
        "status": status,
    }


def _time_arc_big_m(
    data: LunarIceData,
    *,
    travel: float,
    service: float = 0.0,
    source: str = "depot",
    source_start_upper_bound: float | None = None,
) -> float:
    if source_start_upper_bound is not None:
        return max(0.0, float(source_start_upper_bound)) + float(service) + float(travel)
    if source != "depot" and source in data.tasks:
        task = data.tasks[source]
        latest_start = max(0.0, float(task.due_time) - float(task.service_time))
        return latest_start + float(service) + float(travel)
    return float(data.horizon) + float(service) + float(travel)


def _time_arc_upper_big_m(data: LunarIceData) -> float:
    """Safe deactivation constant for the no-wait upper time equality.

    The lower propagation can use the source task's latest start.  That value
    is not safe for the upper counterpart when an inactive early-window source
    arc points to an active late-window task.  All service and return times are
    in ``[0, horizon]``, so the horizon safely deactivates this direction.
    """

    return float(data.horizon)


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


def _arc_option_resource_impossible(
    data: LunarIceData,
    source: str,
    target: str,
    path_type: str,
    *,
    depot_energy_lb_by_task: dict[str, float],
    task_to_depot_energy_lb_by_task: dict[str, float],
    depot_shadow_lb_by_task: dict[str, float],
    task_to_depot_shadow_lb_by_task: dict[str, float],
) -> tuple[bool, str]:
    """Return whether a directed arc option cannot appear in any feasible sortie.

    The test uses optimistic lower bounds around the arc, so pruning is safe:
    if even the cheapest possible depot-prefix plus this arc plus cheapest
    depot-return violates a sortie resource, adding more tasks cannot repair it.
    """

    source = str(source)
    target = str(target)
    if source == target or (source == "depot" and target == "depot"):
        return True, "structural"
    option = data.option(source, target, path_type)
    involved_tasks = tuple(task_id for task_id in (source, target) if task_id != "depot")
    if any(float(data.tasks[task_id].demand) > float(data.capacity) + 1.0e-9 for task_id in involved_tasks):
        return True, "demand"
    if len(involved_tasks) == 2:
        demand_lb = sum(float(data.tasks[task_id].demand) for task_id in involved_tasks)
        if demand_lb > float(data.capacity) + 1.0e-9:
            return True, "demand"

    first_task = target if source == "depot" else source
    last_task = source if target == "depot" else target
    energy_lb = float(option.energy_proxy)
    shadow_lb = float(option.shadow_exposure_min)
    if first_task != "depot":
        energy_lb += float(depot_energy_lb_by_task.get(first_task, 0.0))
        shadow_lb += float(depot_shadow_lb_by_task.get(first_task, 0.0))
    if last_task != "depot":
        energy_lb += float(task_to_depot_energy_lb_by_task.get(last_task, 0.0))
        shadow_lb += float(task_to_depot_shadow_lb_by_task.get(last_task, 0.0))
    for task_id in involved_tasks:
        task = data.tasks[task_id]
        energy_lb += float(task.service_energy)
        shadow_lb += float(task.local_shadow_score) * float(task.service_time)
    if energy_lb > float(data.energy_limit) + 1.0e-9:
        return True, "energy"
    if shadow_lb > float(data.max_shadow_exposure_per_sortie) + 1.0e-9:
        return True, "shadow"
    return False, ""


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


def _depot_to_task_shortest_travel_lower_bounds(data: LunarIceData) -> dict[str, float]:
    """Shortest travel-time lower bound from depot to each task.

    This deliberately computes the shortest path over the full fixed graph
    instead of using the direct depot-task arc.  The generated path options do
    not need to satisfy triangle inequality, so direct travel is not always a
    valid lower bound for reaching a later task through intermediate tasks.
    """

    return {
        task_id: value
        for task_id, value in _single_source_shortest_travel_lower_bounds(data, "depot").items()
        if task_id in set(data.task_ids)
    }


def _task_to_depot_shortest_travel_lower_bounds(data: LunarIceData) -> dict[str, float]:
    """Shortest travel-time lower bound from each task back to the depot."""

    distances_to_depot = _single_source_shortest_travel_lower_bounds(data, "depot", reverse=True)
    return {
        task_id: max(0.0, float(distances_to_depot.get(task_id, 0.0)))
        for task_id in data.task_ids
    }


def _pair_route_duration_lower_bounds(data: LunarIceData) -> dict[tuple[str, str], float]:
    """Lower bound on sortie duration when two tasks are served together."""

    tasks = tuple(data.task_ids)
    depot_to = _single_source_shortest_travel_lower_bounds(data, "depot")
    to_depot = _single_source_shortest_travel_lower_bounds(data, "depot", reverse=True)
    from_task = {
        task_id: _single_source_shortest_travel_lower_bounds(data, task_id)
        for task_id in tasks
    }
    bounds: dict[tuple[str, str], float] = {}
    for left_index, left_task in enumerate(tasks):
        left_service = float(data.tasks[left_task].service_time)
        for right_task in tasks[left_index + 1 :]:
            right_service = float(data.tasks[right_task].service_time)
            left_then_right = (
                float(depot_to.get(left_task, 0.0))
                + left_service
                + float(from_task[left_task].get(right_task, 0.0))
                + right_service
                + float(to_depot.get(right_task, 0.0))
            )
            right_then_left = (
                float(depot_to.get(right_task, 0.0))
                + right_service
                + float(from_task[right_task].get(left_task, 0.0))
                + left_service
                + float(to_depot.get(left_task, 0.0))
            )
            bounds[(left_task, right_task)] = max(0.0, min(left_then_right, right_then_left))
    return bounds


def _pair_weighted_completion_lower_bounds(data: LunarIceData) -> dict[tuple[str, str], float]:
    """Lower bound on weighted service starts when two tasks share a sortie."""

    tasks = tuple(data.task_ids)
    depot_to = _single_source_shortest_travel_lower_bounds(data, "depot")
    from_task = {
        task_id: _single_source_shortest_travel_lower_bounds(data, task_id)
        for task_id in tasks
    }
    bounds: dict[tuple[str, str], float] = {}
    for left_index, left_task in enumerate(tasks):
        left = data.tasks[left_task]
        left_weight = max(0.0, float(left.science_weight))
        left_service = float(left.service_time)
        for right_task in tasks[left_index + 1 :]:
            right = data.tasks[right_task]
            right_weight = max(0.0, float(right.science_weight))
            if left_weight + right_weight <= 1.0e-12:
                continue
            right_service = float(right.service_time)
            left_then_right = (
                left_weight * float(depot_to.get(left_task, 0.0))
                + right_weight
                * (
                    float(depot_to.get(left_task, 0.0))
                    + left_service
                    + float(from_task[left_task].get(right_task, 0.0))
                )
            )
            right_then_left = (
                right_weight * float(depot_to.get(right_task, 0.0))
                + left_weight
                * (
                    float(depot_to.get(right_task, 0.0))
                    + right_service
                    + float(from_task[right_task].get(left_task, 0.0))
                )
            )
            bounds[(left_task, right_task)] = max(0.0, min(left_then_right, right_then_left))
    return bounds


def _pair_time_window_infeasible_pairs(data: LunarIceData) -> dict[tuple[str, str], float]:
    """Task pairs that cannot be served in the same sortie in either order.

    The check uses full-graph shortest travel-time lower bounds and allows
    waiting, so a detected infeasible pair is safe to cut.  The returned value is
    the smallest lower-bound violation margin over both orders.
    """

    tasks = tuple(data.task_ids)
    depot_to = _single_source_shortest_travel_lower_bounds(data, "depot")
    to_depot = _single_source_shortest_travel_lower_bounds(data, "depot", reverse=True)
    from_task = {
        task_id: _single_source_shortest_travel_lower_bounds(data, task_id)
        for task_id in tasks
    }
    infeasible: dict[tuple[str, str], float] = {}
    for left_index, left_task in enumerate(tasks):
        for right_task in tasks[left_index + 1 :]:
            left_margin = _two_task_time_window_violation_lower_bound(
                data,
                first_task=left_task,
                second_task=right_task,
                depot_to=depot_to,
                to_depot=to_depot,
                from_task=from_task,
            )
            right_margin = _two_task_time_window_violation_lower_bound(
                data,
                first_task=right_task,
                second_task=left_task,
                depot_to=depot_to,
                to_depot=to_depot,
                from_task=from_task,
            )
            if left_margin > 1.0e-9 and right_margin > 1.0e-9:
                infeasible[(left_task, right_task)] = round(min(left_margin, right_margin), 9)
    return infeasible


def _pair_time_window_forced_precedence_pairs(data: LunarIceData) -> dict[tuple[str, str], float]:
    """Task-pair precedence implications from one-way time-window infeasibility.

    Keys are ``(must_precede, must_follow)``.  If the two tasks are selected in
    the same sortie, the first task in the key must be served before the second.
    The value is the infeasible-order lower-bound violation margin.
    """

    tasks = tuple(data.task_ids)
    depot_to = _single_source_shortest_travel_lower_bounds(data, "depot")
    to_depot = _single_source_shortest_travel_lower_bounds(data, "depot", reverse=True)
    from_task = {
        task_id: _single_source_shortest_travel_lower_bounds(data, task_id)
        for task_id in tasks
    }
    forced: dict[tuple[str, str], float] = {}
    for left_index, left_task in enumerate(tasks):
        for right_task in tasks[left_index + 1 :]:
            left_before_right_margin = _two_task_time_window_violation_lower_bound(
                data,
                first_task=left_task,
                second_task=right_task,
                depot_to=depot_to,
                to_depot=to_depot,
                from_task=from_task,
            )
            right_before_left_margin = _two_task_time_window_violation_lower_bound(
                data,
                first_task=right_task,
                second_task=left_task,
                depot_to=depot_to,
                to_depot=to_depot,
                from_task=from_task,
            )
            left_before_right_infeasible = left_before_right_margin > 1.0e-9
            right_before_left_infeasible = right_before_left_margin > 1.0e-9
            if left_before_right_infeasible and not right_before_left_infeasible:
                forced[(right_task, left_task)] = round(left_before_right_margin, 9)
            elif right_before_left_infeasible and not left_before_right_infeasible:
                forced[(left_task, right_task)] = round(right_before_left_margin, 9)
    return forced


def _triple_time_window_infeasible_triples(
    data: LunarIceData,
    *,
    pair_time_window_infeasible_by_pair: dict[tuple[str, str], float] | None = None,
) -> dict[tuple[str, str, str], float]:
    """Task triples that cannot be served in the same sortie in any order.

    The test is deliberately optimistic: every travel leg uses a shortest-path
    lower bound and the schedule starts each task as early as possible.  If all
    six optimistic permutations violate a task time window or the horizon return
    limit, every real fixed-graph route serving the triple in one sortie is
    infeasible.
    """

    tasks = tuple(data.task_ids)
    depot_to = _single_source_shortest_travel_lower_bounds(data, "depot")
    to_depot = _single_source_shortest_travel_lower_bounds(data, "depot", reverse=True)
    from_task = {
        task_id: _single_source_shortest_travel_lower_bounds(data, task_id)
        for task_id in tasks
    }
    pair_infeasible = {
        tuple(sorted(pair))
        for pair in (pair_time_window_infeasible_by_pair or {})
    }
    infeasible: dict[tuple[str, str, str], float] = {}
    for triple in combinations(tasks, 3):
        if any(tuple(sorted(pair)) in pair_infeasible for pair in combinations(triple, 2)):
            continue
        permutation_margins = tuple(
            _task_sequence_time_window_violation_lower_bound(
                data,
                task_sequence=ordering,
                depot_to=depot_to,
                to_depot=to_depot,
                from_task=from_task,
            )
            for ordering in permutations(triple)
        )
        if permutation_margins and min(permutation_margins) > 1.0e-9:
            infeasible[triple] = round(min(permutation_margins), 9)
    return infeasible


def _quad_time_window_infeasible_quads(
    data: LunarIceData,
    *,
    pair_time_window_infeasible_by_pair: dict[tuple[str, str], float] | None = None,
    triple_time_window_infeasible_by_triple: dict[tuple[str, str, str], float] | None = None,
) -> dict[tuple[str, str, str, str], float]:
    """Task quads that cannot be served in the same sortie in any order."""

    tasks = tuple(data.task_ids)
    depot_to = _single_source_shortest_travel_lower_bounds(data, "depot")
    to_depot = _single_source_shortest_travel_lower_bounds(data, "depot", reverse=True)
    from_task = {
        task_id: _single_source_shortest_travel_lower_bounds(data, task_id)
        for task_id in tasks
    }
    pair_infeasible = {
        tuple(sorted(pair))
        for pair in (pair_time_window_infeasible_by_pair or {})
    }
    triple_infeasible = {
        tuple(sorted(triple))
        for triple in (triple_time_window_infeasible_by_triple or {})
    }
    infeasible: dict[tuple[str, str, str, str], float] = {}
    for quad in combinations(tasks, 4):
        if any(tuple(sorted(pair)) in pair_infeasible for pair in combinations(quad, 2)):
            continue
        if any(tuple(sorted(triple)) in triple_infeasible for triple in combinations(quad, 3)):
            continue
        permutation_margins = tuple(
            _task_sequence_time_window_violation_lower_bound(
                data,
                task_sequence=ordering,
                depot_to=depot_to,
                to_depot=to_depot,
                from_task=from_task,
            )
            for ordering in permutations(quad)
        )
        if permutation_margins and min(permutation_margins) > 1.0e-9:
            infeasible[quad] = round(min(permutation_margins), 9)
    return infeasible


def _task_sequence_time_window_violation_lower_bound(
    data: LunarIceData,
    *,
    task_sequence: Iterable[str],
    depot_to: dict[str, float],
    to_depot: dict[str, float],
    from_task: dict[str, dict[str, float]],
) -> float:
    sequence = tuple(str(task_id) for task_id in task_sequence)
    if not sequence:
        return 0.0
    first_task = data.tasks[sequence[0]]
    current_start = max(
        float(first_task.ready_time),
        float(depot_to.get(sequence[0], 0.0)),
    )
    max_violation = current_start - (float(first_task.due_time) - float(first_task.service_time))
    previous_task_id = sequence[0]
    previous_task = first_task
    for task_id in sequence[1:]:
        task = data.tasks[task_id]
        current_start = max(
            float(task.ready_time),
            current_start
            + float(previous_task.service_time)
            + float(from_task[previous_task_id].get(task_id, 0.0)),
        )
        max_violation = max(
            max_violation,
            current_start - (float(task.due_time) - float(task.service_time)),
        )
        previous_task_id = task_id
        previous_task = task
    return_finish = (
        current_start
        + float(previous_task.service_time)
        + float(to_depot.get(previous_task_id, 0.0))
        + float(data.dock_overhead_min)
    )
    return max(max_violation, return_finish - float(data.horizon))


def _two_task_time_window_violation_lower_bound(
    data: LunarIceData,
    *,
    first_task: str,
    second_task: str,
    depot_to: dict[str, float],
    to_depot: dict[str, float],
    from_task: dict[str, dict[str, float]],
) -> float:
    first = data.tasks[str(first_task)]
    second = data.tasks[str(second_task)]
    first_latest = float(first.due_time) - float(first.service_time)
    second_latest = float(second.due_time) - float(second.service_time)
    first_start = max(float(first.ready_time), float(depot_to.get(str(first_task), 0.0)))
    second_start = max(
        float(second.ready_time),
        first_start
        + float(first.service_time)
        + float(from_task[str(first_task)].get(str(second_task), 0.0)),
    )
    return_finish = (
        second_start
        + float(second.service_time)
        + float(to_depot.get(str(second_task), 0.0))
        + float(data.dock_overhead_min)
    )
    return max(
        first_start - first_latest,
        second_start - second_latest,
        return_finish - float(data.horizon),
    )


def _pair_route_energy_lower_bounds(data: LunarIceData) -> dict[tuple[str, str], float]:
    """Lower bound on sortie energy when two tasks are served together."""

    tasks = tuple(data.task_ids)
    energy_distances = _all_source_shortest_arc_attribute_lower_bounds(data, "energy_proxy")
    return _pair_route_energy_lower_bounds_from_distances(data, energy_distances, tasks=tasks)


def _single_task_route_energy_lower_bounds(data: LunarIceData) -> dict[str, float]:
    """Lower bound on sortie energy when a task is selected."""

    depot_to = _single_source_shortest_arc_attribute_lower_bounds(data, "depot", "energy_proxy")
    to_depot = _single_source_shortest_arc_attribute_lower_bounds(data, "depot", "energy_proxy", reverse=True)
    return {
        task_id: max(
            0.0,
            float(depot_to.get(task_id, 0.0))
            + float(data.tasks[task_id].service_energy)
            + float(to_depot.get(task_id, 0.0)),
        )
        for task_id in data.task_ids
    }


def _single_task_route_shadow_lower_bounds(data: LunarIceData) -> dict[str, float]:
    """Lower bound on sortie shadow exposure when a task is selected."""

    depot_to = _single_source_shortest_arc_attribute_lower_bounds(data, "depot", "shadow_exposure_min")
    to_depot = _single_source_shortest_arc_attribute_lower_bounds(
        data,
        "depot",
        "shadow_exposure_min",
        reverse=True,
    )
    return {
        task_id: max(
            0.0,
            float(depot_to.get(task_id, 0.0))
            + float(data.tasks[task_id].local_shadow_score) * float(data.tasks[task_id].service_time)
            + float(to_depot.get(task_id, 0.0)),
        )
        for task_id in data.task_ids
    }


def _pair_route_shadow_lower_bounds(data: LunarIceData) -> dict[tuple[str, str], float]:
    """Lower bound on sortie shadow exposure when two tasks are served together."""

    tasks = tuple(data.task_ids)
    shadow_distances = _all_source_shortest_arc_attribute_lower_bounds(data, "shadow_exposure_min")
    depot_to = _single_source_shortest_arc_attribute_lower_bounds(data, "depot", "shadow_exposure_min")
    to_depot = _single_source_shortest_arc_attribute_lower_bounds(
        data,
        "depot",
        "shadow_exposure_min",
        reverse=True,
    )
    bounds: dict[tuple[str, str], float] = {}
    for left_index, left_task in enumerate(tasks):
        left_service = float(data.tasks[left_task].local_shadow_score) * float(data.tasks[left_task].service_time)
        for right_task in tasks[left_index + 1 :]:
            right_service = float(data.tasks[right_task].local_shadow_score) * float(
                data.tasks[right_task].service_time
            )
            left_then_right = (
                float(depot_to.get(left_task, 0.0))
                + left_service
                + float(shadow_distances[left_task].get(right_task, 0.0))
                + right_service
                + float(to_depot.get(right_task, 0.0))
            )
            right_then_left = (
                float(depot_to.get(right_task, 0.0))
                + right_service
                + float(shadow_distances[right_task].get(left_task, 0.0))
                + left_service
                + float(to_depot.get(left_task, 0.0))
            )
            bounds[(left_task, right_task)] = max(0.0, min(left_then_right, right_then_left))
    return bounds


def _triple_route_shadow_infeasible_lower_bounds(
    data: LunarIceData,
    pair_shadow_lb_by_pair: dict[tuple[str, str], float],
) -> dict[tuple[str, str, str], float]:
    """Shadow-infeasible three-task sets not already dominated by pair cuts."""

    tasks = tuple(data.task_ids)
    shadow_distances = _all_source_shortest_arc_attribute_lower_bounds(data, "shadow_exposure_min")
    depot_to = _single_source_shortest_arc_attribute_lower_bounds(data, "depot", "shadow_exposure_min")
    to_depot = _single_source_shortest_arc_attribute_lower_bounds(
        data,
        "depot",
        "shadow_exposure_min",
        reverse=True,
    )
    infeasible_triples: dict[tuple[str, str, str], float] = {}
    limit = float(data.max_shadow_exposure_per_sortie)
    for triple in combinations(tasks, 3):
        if any(
            float(pair_shadow_lb_by_pair.get(tuple(sorted(pair)), 0.0)) > limit + 1.0e-9
            for pair in combinations(triple, 2)
        ):
            continue
        best = math.inf
        for order in permutations(triple):
            shadow = float(depot_to.get(order[0], 0.0))
            for source, target in zip(order, order[1:]):
                shadow += float(data.tasks[source].local_shadow_score) * float(data.tasks[source].service_time)
                shadow += float(shadow_distances[source].get(target, 0.0))
            shadow += float(data.tasks[order[-1]].local_shadow_score) * float(data.tasks[order[-1]].service_time)
            shadow += float(to_depot.get(order[-1], 0.0))
            best = min(best, shadow)
        if math.isfinite(best) and best > limit + 1.0e-9:
            infeasible_triples[tuple(sorted(triple))] = max(0.0, float(best))
    return infeasible_triples


def _demand_cover_subsets(
    data: LunarIceData,
    *,
    max_cover_size: int = 5,
) -> dict[tuple[str, ...], float]:
    """Minimal demand covers up to a bounded cardinality."""

    tasks = tuple(data.task_ids)
    limit = float(data.capacity)
    covers: dict[tuple[str, ...], float] = {}
    max_size = min(max(2, int(max_cover_size)), len(tasks), int(data.max_tasks_per_trip))
    task_demand = {task_id: float(data.tasks[task_id].demand) for task_id in tasks}
    for size in range(2, max_size + 1):
        for subset in combinations(tasks, size):
            demand = sum(task_demand[task_id] for task_id in subset)
            if demand <= limit + 1.0e-9:
                continue
            minimal = True
            for index in range(size):
                proper = subset[:index] + subset[index + 1 :]
                if sum(task_demand[task_id] for task_id in proper) > limit + 1.0e-9:
                    minimal = False
                    break
            if minimal:
                covers[tuple(sorted(subset))] = max(0.0, float(demand))
    return covers


def _pair_route_energy_lower_bounds_from_distances(
    data: LunarIceData,
    energy_distances: dict[str, dict[str, float]],
    *,
    tasks: tuple[str, ...],
) -> dict[tuple[str, str], float]:
    depot_to = _single_source_shortest_arc_attribute_lower_bounds(data, "depot", "energy_proxy")
    to_depot = _single_source_shortest_arc_attribute_lower_bounds(data, "depot", "energy_proxy", reverse=True)
    bounds: dict[tuple[str, str], float] = {}
    for left_index, left_task in enumerate(tasks):
        left_service = float(data.tasks[left_task].service_energy)
        for right_task in tasks[left_index + 1 :]:
            right_service = float(data.tasks[right_task].service_energy)
            left_then_right = (
                float(depot_to.get(left_task, 0.0))
                + left_service
                + float(energy_distances[left_task].get(right_task, 0.0))
                + right_service
                + float(to_depot.get(right_task, 0.0))
            )
            right_then_left = (
                float(depot_to.get(right_task, 0.0))
                + right_service
                + float(energy_distances[right_task].get(left_task, 0.0))
                + left_service
                + float(to_depot.get(left_task, 0.0))
            )
            bounds[(left_task, right_task)] = max(0.0, min(left_then_right, right_then_left))
    return bounds


def _triple_route_energy_infeasible_lower_bounds(
    data: LunarIceData,
    pair_energy_lb_by_pair: dict[tuple[str, str], float],
) -> dict[tuple[str, str, str], float]:
    """Energy-infeasible three-task sets not already dominated by pair cuts."""

    tasks = tuple(data.task_ids)
    energy_distances = _all_source_shortest_arc_attribute_lower_bounds(data, "energy_proxy")
    depot_to = _single_source_shortest_arc_attribute_lower_bounds(data, "depot", "energy_proxy")
    to_depot = _single_source_shortest_arc_attribute_lower_bounds(data, "depot", "energy_proxy", reverse=True)
    infeasible_triples: dict[tuple[str, str, str], float] = {}
    limit = float(data.energy_limit)
    for triple in combinations(tasks, 3):
        if any(
            float(pair_energy_lb_by_pair.get(tuple(sorted(pair)), 0.0)) > limit + 1.0e-9
            for pair in combinations(triple, 2)
        ):
            continue
        best = math.inf
        for order in permutations(triple):
            energy = float(depot_to.get(order[0], 0.0))
            for source, target in zip(order, order[1:]):
                energy += float(data.tasks[source].service_energy)
                energy += float(energy_distances[source].get(target, 0.0))
            energy += float(data.tasks[order[-1]].service_energy)
            energy += float(to_depot.get(order[-1], 0.0))
            best = min(best, energy)
        if math.isfinite(best) and best > limit + 1.0e-9:
            infeasible_triples[tuple(sorted(triple))] = max(0.0, float(best))
    return infeasible_triples


def _all_source_shortest_arc_attribute_lower_bounds(
    data: LunarIceData,
    arc_attribute: str,
) -> dict[str, dict[str, float]]:
    nodes = ("depot", *data.task_ids)
    return {
        node: _single_source_shortest_arc_attribute_lower_bounds(data, node, arc_attribute)
        for node in nodes
    }


def _single_source_shortest_travel_lower_bounds(
    data: LunarIceData,
    source_node: str,
    *,
    reverse: bool = False,
) -> dict[str, float]:
    return _single_source_shortest_arc_attribute_lower_bounds(
        data,
        source_node,
        "travel_time_min",
        reverse=reverse,
    )


def _single_source_shortest_arc_attribute_lower_bounds(
    data: LunarIceData,
    source_node: str,
    arc_attribute: str,
    *,
    reverse: bool = False,
) -> dict[str, float]:
    tasks = tuple(data.task_ids)
    nodes = ("depot", *tasks)
    distances = {node: math.inf for node in nodes}
    distances[str(source_node)] = 0.0
    unvisited = set(nodes)
    min_arc_travel: dict[tuple[str, str], float] = {}
    for (source, target), options in data.arcs.items():
        arc_source = str(target) if reverse else str(source)
        arc_target = str(source) if reverse else str(target)
        if arc_source not in unvisited or arc_target not in unvisited or arc_source == arc_target:
            continue
        values = [float(getattr(option, str(arc_attribute))) for option in options.values()]
        if values:
            min_arc_travel[(arc_source, arc_target)] = max(0.0, min(values))

    while unvisited:
        current = min(unvisited, key=lambda node: distances[node])
        if not math.isfinite(distances[current]):
            break
        unvisited.remove(current)
        for target in tuple(unvisited):
            travel = min_arc_travel.get((current, target))
            if travel is None:
                continue
            candidate = distances[current] + travel
            if candidate < distances[target]:
                distances[target] = candidate

    return {
        node: max(0.0, float(distance)) if math.isfinite(distance) else 0.0
        for node, distance in distances.items()
    }


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
                model.addConstr(
                    sortie_start[vehicle, slot]
                    >= sortie_end[vehicle, slot - 1]
                    - float(data.horizon) * (1 - z[vehicle, slot]),
                    name=f"sortie_seq[{vehicle},{slot}]",
            )
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
                    upper_time_m = _time_arc_upper_big_m(data)
                    model.addConstr(
                        service_start[vehicle, slot, target]
                        >= sortie_start[vehicle, slot] + travel - time_m * (1 - x[key]),
                        name=f"time_depot[{vehicle},{slot},{target},{path_type}]",
                    )
                    model.addConstr(
                        service_start[vehicle, slot, target]
                        <= sortie_start[vehicle, slot] + travel
                        + upper_time_m * (1 - x[key]),
                        name=f"time_depot_no_wait[{vehicle},{slot},{target},{path_type}]",
                    )
                elif source != "depot" and target != "depot":
                    service = float(data.tasks[source].service_time)
                    time_m = _time_arc_big_m(data, travel=travel, service=service, source=source)
                    upper_time_m = _time_arc_upper_big_m(data)
                    model.addConstr(
                        service_start[vehicle, slot, target]
                        >= service_start[vehicle, slot, source] + service + travel - time_m * (1 - x[key]),
                        name=f"time_task[{vehicle},{slot},{source},{target},{path_type}]",
                    )
                    model.addConstr(
                        service_start[vehicle, slot, target]
                        <= service_start[vehicle, slot, source] + service + travel
                        + upper_time_m * (1 - x[key]),
                        name=f"time_task_no_wait[{vehicle},{slot},{source},{target},{path_type}]",
                    )
                elif source != "depot" and target == "depot":
                    service = float(data.tasks[source].service_time)
                    time_m = _time_arc_big_m(data, travel=travel, service=service, source=source)
                    upper_time_m = _time_arc_upper_big_m(data)
                    model.addConstr(
                        sortie_return[vehicle, slot]
                        >= service_start[vehicle, slot, source] + service + travel - time_m * (1 - x[key]),
                        name=f"time_return[{vehicle},{slot},{source},{path_type}]",
                    )
                    model.addConstr(
                        sortie_return[vehicle, slot]
                        <= service_start[vehicle, slot, source] + service + travel
                        + upper_time_m * (1 - x[key]),
                        name=f"time_return_no_wait[{vehicle},{slot},{source},{path_type}]",
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
            "sortie_slot_min_sortie_energy_lower_bound": slot_bound["min_sortie_energy_lower_bound"],
            "sortie_slot_min_energy_recharge_duration_lower_bound": (
                slot_bound["min_energy_recharge_duration_lower_bound"]
            ),
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
        "sortie_slot_min_sortie_energy_lower_bound": slot_bound["min_sortie_energy_lower_bound"],
        "sortie_slot_min_energy_recharge_duration_lower_bound": (
            slot_bound["min_energy_recharge_duration_lower_bound"]
        ),
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
        "sort_indices": _compact_mip_start_sort_indices_enabled(),
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
                    upper_time_m = _time_arc_upper_big_m(data)
                    add_ge(
                        {
                            service_start[vehicle, slot, target]: 1.0,
                            sortie_start[vehicle, slot]: -1.0,
                            x_col: -time_m,
                        },
                        travel - time_m,
                    )
                    add_le(
                        {
                            service_start[vehicle, slot, target]: 1.0,
                            sortie_start[vehicle, slot]: -1.0,
                            x_col: upper_time_m,
                        },
                        travel + upper_time_m,
                    )
                elif source != "depot" and target != "depot":
                    service = float(data.tasks[source].service_time)
                    time_m = _time_arc_big_m(data, travel=travel, service=service, source=source)
                    upper_time_m = _time_arc_upper_big_m(data)
                    add_ge(
                        {
                            service_start[vehicle, slot, target]: 1.0,
                            service_start[vehicle, slot, source]: -1.0,
                            x_col: -time_m,
                        },
                        service + travel - time_m,
                    )
                    add_le(
                        {
                            service_start[vehicle, slot, target]: 1.0,
                            service_start[vehicle, slot, source]: -1.0,
                            x_col: upper_time_m,
                        },
                        service + travel + upper_time_m,
                    )
                elif source != "depot" and target == "depot":
                    service = float(data.tasks[source].service_time)
                    time_m = _time_arc_big_m(data, travel=travel, service=service, source=source)
                    upper_time_m = _time_arc_upper_big_m(data)
                    add_ge(
                        {
                            sortie_return[vehicle, slot]: 1.0,
                            service_start[vehicle, slot, source]: -1.0,
                            x_col: -time_m,
                        },
                        service + travel - time_m,
                    )
                    add_le(
                        {
                            sortie_return[vehicle, slot]: 1.0,
                            service_start[vehicle, slot, source]: -1.0,
                            x_col: upper_time_m,
                        },
                        service + travel + upper_time_m,
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
    resource_arc_pruning: bool = False,
    slot_task_time_pruning: bool = False,
    slot_arc_support_pruning: bool = False,
    slot_sequence_capacity_arc_pruning: bool = False,
    single_task_per_active_sortie_arc_pruning: bool = True,
    sortie_slot_position_bounds: bool = False,
    service_start_depot_travel_lb: bool = False,
    task_to_depot_return_travel_lb: bool = False,
    pair_route_duration_lb: bool = False,
    pair_weighted_completion_lb: bool = False,
    demand_cover_cut: bool = False,
    single_task_energy_lb: bool = False,
    single_task_shadow_lb: bool = False,
    pair_energy_lb: bool = False,
    pair_shadow_lb: bool = False,
    pair_energy_infeasible_cut: bool = False,
    pair_time_window_infeasible_cut: bool = False,
    pair_time_window_precedence_cut: bool = False,
    triple_time_window_infeasible_cut: bool = False,
    quad_time_window_infeasible_cut: bool = False,
    pair_shadow_infeasible_cut: bool = False,
    triple_shadow_infeasible_cut: bool = False,
    triple_energy_infeasible_cut: bool = False,
    task_slot_pair_conflict_capacity_bound: bool = False,
    dual_task_slot_lower_bound: bool = False,
    dual_task_slot_full_space_lower_bound: bool = False,
    dual_task_slot_full_space_lb_time_limit_sec: float = 0.25,
    dual_task_slot_full_space_lb_early_stop_on_negative: bool = True,
    recharge_aware_slot_bound: bool = False,
    objective_bound_no_negative_cutoff: bool = False,
    zero_capacity_slot_truncation: bool = False,
    slot_sequence_capacity_live_bound: bool = False,
    tight_service_start_bounds: bool = False,
    tight_time_arc_big_m: bool = False,
    active_time_z_bounds: bool = False,
    slot_service_start_y_lower_bound: bool = False,
    negative_feasibility_search: bool = False,
    forbidden_arc_patterns: Iterable[Iterable[tuple[int, str, str, str]]] | None = None,
    forbidden_task_sets: Iterable[Iterable[str]] | None = None,
    required_task_set: Iterable[str] | None = None,
    required_task_count: int | None = None,
    required_active_sortie_count: int | None = None,
    mip_start_journey: JourneyColumn | None = None,
    mip_start_zero_fill_integers: bool = False,
    mip_start_inactive_tail_time: bool = False,
    mip_start_inactive_tail_time_mode: str = "zero",
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

    required_task_set_raw = (
        None
        if required_task_set is None
        else tuple(str(task_id) for task_id in required_task_set)
    )
    required_task_set_unknown = tuple(sorted(set(required_task_set_raw or tuple()) - set(tasks)))
    if required_task_set_unknown:
        return {
            "status": "COMPACT_HIGHS_PRICING_INVALID_REQUIRED_TASK_SET",
            "algorithm_status": "COMPACT_HIGHS_PRICING_INVALID_REQUIRED_TASK_SET",
            "pricing_state": "INCOMPLETE_LIMIT",
            "best_reduced_cost": None,
            "dual_bound": None,
            "negative_found": False,
            "can_certify_no_negative": False,
            "journeys": tuple(),
            "required_task_set_enabled": True,
            "required_task_set": list(required_task_set_raw or tuple()),
            "required_task_set_unknown": list(required_task_set_unknown),
            "wall_time_sec": round(perf_counter() - start_wall, 6),
            "note": "Required task-set pricing received tasks outside the instance; fail closed.",
        }
    required_task_set_normalized = (
        None
        if required_task_set_raw is None
        else tuple(sorted(set(required_task_set_raw)))
    )
    if required_task_set_raw is not None and not required_task_set_normalized:
        return {
            "status": "COMPACT_HIGHS_PRICING_EMPTY_REQUIRED_TASK_SET",
            "algorithm_status": "COMPACT_HIGHS_PRICING_EMPTY_REQUIRED_TASK_SET",
            "pricing_state": "INCOMPLETE_LIMIT",
            "best_reduced_cost": None,
            "dual_bound": None,
            "negative_found": False,
            "can_certify_no_negative": False,
            "journeys": tuple(),
            "required_task_set_enabled": True,
            "required_task_set": [],
            "wall_time_sec": round(perf_counter() - start_wall, 6),
            "note": "Required task-set pricing needs a nonempty task set; fail closed.",
        }
    required_task_count_normalized = None
    if required_task_count is not None:
        required_task_count_normalized = int(required_task_count)
        if required_task_count_normalized < 1 or required_task_count_normalized > len(tasks):
            return {
                "status": "COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_INFEASIBLE",
                "algorithm_status": "COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_INFEASIBLE",
                "exact_status": "REQUIRED_TASK_COUNT_PRICING_INFEASIBLE",
                "pricing_state": "INCOMPLETE_LIMIT",
                "best_reduced_cost": None,
                "dual_bound": None,
                "negative_found": False,
                "can_certify_no_negative": False,
                "journeys": tuple(),
                "required_task_count_enabled": True,
                "required_task_count": required_task_count_normalized,
                "pricing_complete_for_required_task_count": True,
                "required_task_count_region_can_certify_no_negative": True,
                "required_task_count_can_certify_full_space": False,
                "required_task_count_feasible_task_count": 0,
                "required_task_count_slot_capacity_task_upper_bound": 0,
                "required_task_count_min_active_sorties": 0,
                "required_task_count_active_sortie_lb_count": 0,
                "required_task_count_infeasible_by_feasible_task_count": True,
                "required_task_count_infeasible_by_slot_capacity": True,
                "wall_time_sec": round(perf_counter() - start_wall, 6),
                "note": "Required task-count pricing region has no feasible nonempty journey columns.",
            }
    required_active_sortie_count_normalized = None
    if required_active_sortie_count is not None:
        required_active_sortie_count_normalized = int(required_active_sortie_count)
        if required_active_sortie_count_normalized < 1:
            return {
                "status": "COMPACT_HIGHS_PRICING_REQUIRED_ACTIVE_SORTIE_COUNT_INFEASIBLE",
                "algorithm_status": "COMPACT_HIGHS_PRICING_REQUIRED_ACTIVE_SORTIE_COUNT_INFEASIBLE",
                "exact_status": "REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE",
                "pricing_state": "INCOMPLETE_LIMIT",
                "best_reduced_cost": None,
                "dual_bound": None,
                "negative_found": False,
                "can_certify_no_negative": False,
                "journeys": tuple(),
                "required_active_sortie_count_enabled": True,
                "required_active_sortie_count": required_active_sortie_count_normalized,
                "pricing_complete_for_required_active_sortie_count": True,
                "required_active_sortie_count_region_can_certify_no_negative": True,
                "required_active_sortie_count_can_certify_full_space": False,
                "required_active_sortie_count_infeasible": True,
                "wall_time_sec": round(perf_counter() - start_wall, 6),
                "note": "Required active-sortie-count pricing region has no feasible nonempty journey columns.",
            }
    model_tasks = required_task_set_normalized if required_task_set_normalized is not None else tasks

    slot_bound = _safe_sortie_slot_bound(
        data,
        latest_service_start_bound=bool(latest_service_start_slot_bound),
        recharge_aware_duration_bound=bool(recharge_aware_slot_bound),
    )
    sortie_slots = (
        int(max_sorties_per_journey)
        if max_sorties_per_journey is not None
        else int(slot_bound["slot_count"])
    )
    if required_task_set_normalized is not None:
        sortie_slots = min(sortie_slots, len(required_task_set_normalized))
    if required_task_count_normalized is not None:
        sortie_slots = min(sortie_slots, required_task_count_normalized)
    required_task_size_for_active_bounds = (
        len(required_task_set_normalized)
        if required_task_set_normalized is not None
        else required_task_count_normalized
    )
    required_active_sortie_count_min = (
        int(math.ceil(float(required_task_size_for_active_bounds) / max(1.0, float(data.max_tasks_per_trip))))
        if required_task_size_for_active_bounds is not None
        else 1
    )
    required_active_sortie_count_max = (
        min(int(required_task_size_for_active_bounds), int(sortie_slots))
        if required_task_size_for_active_bounds is not None
        else int(sortie_slots)
    )
    required_active_sortie_count_expected_counts = (
        list(range(int(required_active_sortie_count_min), int(required_active_sortie_count_max) + 1))
        if required_active_sortie_count_normalized is not None
        else []
    )
    pre_active_sortie_slot_count = int(sortie_slots)
    if required_active_sortie_count_normalized is not None:
        sortie_slots = min(sortie_slots, int(required_active_sortie_count_normalized))
    required_active_sortie_count_slots_fixed = bool(
        required_active_sortie_count_normalized is not None
        and int(sortie_slots) == int(required_active_sortie_count_normalized)
    )
    single_task_per_active_sortie_arc_pruning_enabled = bool(
        single_task_per_active_sortie_arc_pruning
        and required_active_sortie_count_slots_fixed
        and required_task_size_for_active_bounds is not None
        and required_active_sortie_count_normalized is not None
        and int(required_task_size_for_active_bounds) == int(required_active_sortie_count_normalized)
    )
    single_task_per_active_sortie_arc_pruned_option_count = 0
    slot_sequence_capacity_arc_pruned_option_count = 0
    mtz_connectivity_effective = bool(mtz_connectivity) and not bool(
        single_task_per_active_sortie_arc_pruning_enabled
    )
    mtz_endpoint_order_cuts_effective = bool(
        mtz_connectivity_effective and mtz_endpoint_order_cuts
    )
    pair_time_window_precedence_cut_effective = bool(
        mtz_connectivity_effective and pair_time_window_precedence_cut
    )
    min_return_duration = float(slot_bound["min_return_duration_lower_bound"])
    min_active_duration = float(slot_bound["min_duration_lower_bound"])
    min_out_return_travel = float(slot_bound["min_out_return_travel_lower_bound"])
    latest_sortie_start_upper_bound = max(
        0.0,
        float(slot_bound["latest_service_start_upper_bound"])
        - float(slot_bound["min_depot_outbound_travel_lower_bound"]),
    )
    tight_time_arc_big_m_enabled = bool(tight_time_arc_big_m)
    sortie_start_upper_bound = (
        min(float(data.horizon), float(latest_sortie_start_upper_bound))
        if tight_time_arc_big_m_enabled
        else float(data.horizon)
    )
    active_time_z_bounds_enabled = bool(active_time_z_bounds)
    nodes = ("depot", *model_tasks)
    path_type_cache, pruning = _pricing_path_type_cache(
        data,
        time_window_arc_pruning=bool(time_window_arc_pruning),
    )
    depot_energy_lb_by_task = _single_source_shortest_arc_attribute_lower_bounds(
        data,
        "depot",
        "energy_proxy",
    )
    task_to_depot_energy_lb_by_task = _single_source_shortest_arc_attribute_lower_bounds(
        data,
        "depot",
        "energy_proxy",
        reverse=True,
    )
    depot_shadow_lb_by_task = _single_source_shortest_arc_attribute_lower_bounds(
        data,
        "depot",
        "shadow_exposure_min",
    )
    task_to_depot_shadow_lb_by_task = _single_source_shortest_arc_attribute_lower_bounds(
        data,
        "depot",
        "shadow_exposure_min",
        reverse=True,
    )
    min_depot_travel_by_task = {
        str(task_id): min(
            float(option.travel_time_min)
            for option in data.arcs[("depot", str(task_id))].values()
        )
        for task_id in model_tasks
    }
    min_return_travel_by_task = {
        str(task_id): min(
            float(option.travel_time_min)
            for option in data.arcs[(str(task_id), "depot")].values()
        )
        for task_id in model_tasks
    }
    min_round_trip_energy_by_task = {
        str(task_id): (
            min(float(option.energy_proxy) for option in data.arcs[("depot", str(task_id))].values())
            + min(float(option.energy_proxy) for option in data.arcs[(str(task_id), "depot")].values())
            + float(data.tasks[str(task_id)].service_energy)
        )
        for task_id in model_tasks
    }

    def build_slot_feasible_tasks(
        slot_count: int,
    ) -> tuple[dict[int, tuple[str, ...]], int, int, int]:
        feasible_by_slot: dict[int, tuple[str, ...]] = {}
        pruned_assignment_count = 0
        pruned_due_count = 0
        pruned_horizon_count = 0
        for slot in range(int(slot_count)):
            feasible_for_slot: list[str] = []
            earliest_slot_start = float(slot) * min_active_duration
            for task_id in model_tasks:
                task = data.tasks[task_id]
                latest_service_start = float(data.tasks[task_id].due_time) - float(
                    data.tasks[task_id].service_time
                )
                earliest_service_start = earliest_slot_start + float(
                    min_depot_travel_by_task[str(task_id)]
                )
                if bool(slot_task_time_pruning):
                    due_infeasible = earliest_service_start > latest_service_start + 1.0e-9
                    earliest_return = (
                        earliest_service_start
                        + float(task.service_time)
                        + float(min_return_travel_by_task[str(task_id)])
                    )
                    recharge_lb = float(min_round_trip_energy_by_task[str(task_id)]) / max(
                        1.0e-9,
                        float(data.recharge_power_proxy_per_min),
                    )
                    earliest_end = earliest_return + float(data.dock_overhead_min) + recharge_lb
                    horizon_infeasible = (
                        earliest_return > float(data.horizon) + 1.0e-9
                        or earliest_end > float(data.horizon) + 1.0e-9
                    )
                    if due_infeasible or horizon_infeasible:
                        pruned_assignment_count += 1
                        if due_infeasible:
                            pruned_due_count += 1
                        if horizon_infeasible:
                            pruned_horizon_count += 1
                        continue
                feasible_for_slot.append(str(task_id))
            feasible_by_slot[slot] = tuple(feasible_for_slot)
        return (
            feasible_by_slot,
            int(pruned_assignment_count),
            int(pruned_due_count),
            int(pruned_horizon_count),
        )

    (
        slot_feasible_tasks,
        slot_task_time_pruned_assignment_count,
        slot_task_time_pruned_due_count,
        slot_task_time_pruned_horizon_count,
    ) = build_slot_feasible_tasks(int(sortie_slots))
    slot_task_time_feasible_assignment_count = sum(len(row) for row in slot_feasible_tasks.values())
    preflight_task_count_feasible_task_count = len(
        {task_id for feasible_tasks in slot_feasible_tasks.values() for task_id in feasible_tasks}
    )
    preflight_task_count_slot_capacity_upper_bound = sum(
        min(int(data.max_tasks_per_trip), len(feasible_tasks))
        for feasible_tasks in slot_feasible_tasks.values()
    )
    preflight_slot_sequence_capacity_bounds = _slot_task_sequence_capacity_bounds(
        data,
        model_tasks=tuple(str(task_id) for task_id in model_tasks),
        slot_feasible_tasks=slot_feasible_tasks,
        min_active_duration=float(min_active_duration),
        min_depot_outbound_travel=float(slot_bound["min_depot_outbound_travel_lower_bound"]),
        min_return_travel=min(float(value) for value in min_return_travel_by_task.values()),
    )
    preflight_slot_sequence_capacity_by_slot = {
        int(slot): int(capacity)
        for slot, capacity in enumerate(
            preflight_slot_sequence_capacity_bounds.get(
                "slot_sequence_capacity_by_slot",
                [],
            )
        )
    }
    preflight_task_count_slot_sequence_capacity_upper_bound = int(
        preflight_slot_sequence_capacity_bounds["slot_sequence_capacity_upper_bound"]
    )
    preflight_task_count_slot_matching_capacity_upper_bound = int(
        preflight_slot_sequence_capacity_bounds["slot_matching_capacity_upper_bound"]
    )
    pre_active_slot_sequence_capacity_bounds = preflight_slot_sequence_capacity_bounds
    if (
        required_active_sortie_count_normalized is not None
        and required_task_size_for_active_bounds is not None
        and int(pre_active_sortie_slot_count) > int(sortie_slots)
    ):
        pre_active_slot_feasible_tasks, _ignored_assignments, _ignored_due, _ignored_horizon = (
            build_slot_feasible_tasks(int(pre_active_sortie_slot_count))
        )
        pre_active_slot_sequence_capacity_bounds = _slot_task_sequence_capacity_bounds(
            data,
            model_tasks=tuple(str(task_id) for task_id in model_tasks),
            slot_feasible_tasks=pre_active_slot_feasible_tasks,
            min_active_duration=float(min_active_duration),
            min_depot_outbound_travel=float(slot_bound["min_depot_outbound_travel_lower_bound"]),
            min_return_travel=min(float(value) for value in min_return_travel_by_task.values()),
        )
    preflight_required_active_sortie_count_capacity_min = (
        _min_prefix_slots_for_task_count(
            pre_active_slot_sequence_capacity_bounds["slot_sequence_capacity_by_slot"],
            int(required_task_size_for_active_bounds),
        )
        if required_task_size_for_active_bounds is not None
        else None
    )
    preflight_required_active_sortie_count_infeasible_by_capacity_min = bool(
        required_active_sortie_count_normalized is not None
        and preflight_required_active_sortie_count_capacity_min is not None
        and int(required_active_sortie_count_normalized)
        < int(preflight_required_active_sortie_count_capacity_min)
    )
    preflight_required_task_set_size = (
        len(required_task_set_normalized)
        if required_task_set_normalized is not None
        else 0
    )
    preflight_required_task_set_min_active_sorties = (
        int(math.ceil(float(preflight_required_task_set_size) / max(1.0, float(data.max_tasks_per_trip))))
        if required_task_set_normalized is not None
        else 0
    )
    preflight_required_task_set_infeasible_by_feasible_task_count = bool(
        required_task_set_normalized is not None
        and int(preflight_required_task_set_size) > int(preflight_task_count_feasible_task_count)
    )
    preflight_required_task_set_infeasible_by_slot_capacity = bool(
        required_task_set_normalized is not None
        and (
            int(preflight_required_task_set_size) > int(preflight_task_count_slot_capacity_upper_bound)
            or int(preflight_required_task_set_min_active_sorties) > int(sortie_slots)
        )
    )
    preflight_required_task_set_infeasible_by_slot_sequence_capacity = bool(
        required_task_set_normalized is not None
        and int(preflight_required_task_set_size) > int(preflight_task_count_slot_sequence_capacity_upper_bound)
    )
    preflight_required_task_set_infeasible_by_slot_matching = bool(
        required_task_set_normalized is not None
        and int(preflight_required_task_set_size) > int(preflight_task_count_slot_matching_capacity_upper_bound)
    )
    preflight_required_task_count_min_active_sorties = (
        int(math.ceil(float(required_task_count_normalized) / max(1.0, float(data.max_tasks_per_trip))))
        if required_task_count_normalized is not None
        else 0
    )
    preflight_required_task_count_infeasible_by_feasible_task_count = bool(
        required_task_count_normalized is not None
        and int(required_task_count_normalized) > int(preflight_task_count_feasible_task_count)
    )
    preflight_required_task_count_infeasible_by_slot_capacity = bool(
        required_task_count_normalized is not None
        and (
            int(required_task_count_normalized) > int(preflight_task_count_slot_capacity_upper_bound)
            or int(preflight_required_task_count_min_active_sorties) > int(sortie_slots)
        )
    )
    preflight_required_task_count_infeasible_by_slot_sequence_capacity = bool(
        required_task_count_normalized is not None
        and int(required_task_count_normalized) > int(preflight_task_count_slot_sequence_capacity_upper_bound)
    )
    preflight_required_task_count_infeasible_by_slot_matching = bool(
        required_task_count_normalized is not None
        and int(required_task_count_normalized) > int(preflight_task_count_slot_matching_capacity_upper_bound)
    )
    preflight_required_active_sortie_count_infeasible = bool(
        required_active_sortie_count_normalized is not None
        and (
            int(required_active_sortie_count_normalized) < int(required_active_sortie_count_min)
            or int(required_active_sortie_count_normalized) > int(required_active_sortie_count_max)
            or int(required_active_sortie_count_normalized) > int(sortie_slots)
            or preflight_required_active_sortie_count_infeasible_by_capacity_min
        )
    )
    if (
        (
            required_task_set_normalized is not None
            and (
                preflight_required_task_set_infeasible_by_feasible_task_count
                or preflight_required_task_set_infeasible_by_slot_capacity
                or preflight_required_task_set_infeasible_by_slot_sequence_capacity
                or preflight_required_task_set_infeasible_by_slot_matching
            )
        )
        or
        (
            required_task_count_normalized is not None
            and (
                preflight_required_task_count_infeasible_by_feasible_task_count
                or preflight_required_task_count_infeasible_by_slot_capacity
                or preflight_required_task_count_infeasible_by_slot_sequence_capacity
                or preflight_required_task_count_infeasible_by_slot_matching
            )
        )
        or preflight_required_active_sortie_count_infeasible
    ):
        active_sortie_infeasible_only = bool(
            preflight_required_active_sortie_count_infeasible
            and not preflight_required_task_count_infeasible_by_feasible_task_count
            and not preflight_required_task_count_infeasible_by_slot_capacity
            and not preflight_required_task_count_infeasible_by_slot_sequence_capacity
            and not preflight_required_task_count_infeasible_by_slot_matching
            and not preflight_required_task_set_infeasible_by_feasible_task_count
            and not preflight_required_task_set_infeasible_by_slot_capacity
            and not preflight_required_task_set_infeasible_by_slot_sequence_capacity
            and not preflight_required_task_set_infeasible_by_slot_matching
        )
        status = (
            "COMPACT_HIGHS_PRICING_REQUIRED_ACTIVE_SORTIE_COUNT_INFEASIBLE"
            if active_sortie_infeasible_only
            else "COMPACT_HIGHS_PRICING_REQUIRED_TASK_SET_INFEASIBLE"
            if required_task_set_normalized is not None
            and (
                preflight_required_task_set_infeasible_by_feasible_task_count
                or preflight_required_task_set_infeasible_by_slot_capacity
                or preflight_required_task_set_infeasible_by_slot_sequence_capacity
                or preflight_required_task_set_infeasible_by_slot_matching
            )
            else "COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_INFEASIBLE"
        )
        exact_status = (
            "REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE"
            if active_sortie_infeasible_only
            else "REQUIRED_TASK_SET_PRICING_INFEASIBLE"
            if required_task_set_normalized is not None
            and (
                preflight_required_task_set_infeasible_by_feasible_task_count
                or preflight_required_task_set_infeasible_by_slot_capacity
                or preflight_required_task_set_infeasible_by_slot_sequence_capacity
                or preflight_required_task_set_infeasible_by_slot_matching
            )
            else "REQUIRED_TASK_COUNT_PRICING_INFEASIBLE"
        )
        return {
            "status": status,
            "algorithm_status": status,
            "exact_status": exact_status,
            "pricing_state": "INCOMPLETE_LIMIT",
            "best_reduced_cost": None,
            "dual_bound": None,
            "negative_found": False,
            "can_certify_no_negative": False,
            "journeys": tuple(),
            "task_count": len(tasks),
            "pricing_model_task_count": len(model_tasks),
            "sortie_slots_per_journey": int(sortie_slots),
            "pricing_complete_for_all_task_subsets": False,
            "pricing_complete_by_compact_milp": False,
            "required_task_set_enabled": bool(required_task_set_normalized is not None),
            "required_task_set": list(required_task_set_normalized or tuple()),
            "required_task_set_count": int(preflight_required_task_set_size),
            "pricing_complete_for_required_task_set": bool(
                required_task_set_normalized is not None
            ),
            "required_task_set_region_can_certify_no_negative": bool(
                required_task_set_normalized is not None
            ),
            "required_task_set_can_certify_full_space": False,
            "required_task_set_model_reduction_enabled": bool(required_task_set_normalized is not None),
            "required_task_set_model_task_count": (
                len(model_tasks) if required_task_set_normalized is not None else None
            ),
            "required_task_set_model_task_reduction_count": (
                int(len(tasks) - len(model_tasks))
                if required_task_set_normalized is not None
                else 0
            ),
            "required_task_set_infeasible_by_feasible_task_count": bool(
                preflight_required_task_set_infeasible_by_feasible_task_count
            ),
            "required_task_set_infeasible_by_slot_capacity": bool(
                preflight_required_task_set_infeasible_by_slot_capacity
            ),
            "required_task_set_infeasible_by_slot_sequence_capacity": bool(
                preflight_required_task_set_infeasible_by_slot_sequence_capacity
            ),
            "required_task_set_infeasible_by_slot_matching": bool(
                preflight_required_task_set_infeasible_by_slot_matching
            ),
            "required_task_count_enabled": bool(required_task_count_normalized is not None),
            "required_task_count": required_task_count_normalized,
            "pricing_complete_for_required_task_count": bool(
                required_task_count_normalized is not None
            ),
            "required_task_count_region_can_certify_no_negative": bool(
                required_task_count_normalized is not None
            ),
            "required_task_count_can_certify_full_space": False,
            "required_task_count_feasible_task_count": int(preflight_task_count_feasible_task_count),
            "required_task_count_slot_capacity_task_upper_bound": int(
                preflight_task_count_slot_capacity_upper_bound
            ),
            "required_task_count_slot_sequence_capacity_upper_bound": int(
                preflight_task_count_slot_sequence_capacity_upper_bound
            ),
            "required_task_count_slot_matching_capacity_upper_bound": int(
                preflight_task_count_slot_matching_capacity_upper_bound
            ),
            "required_task_count_pair_conflict_capacity_upper_bound": None,
            "required_task_count_min_active_sorties": int(preflight_required_task_count_min_active_sorties),
            "required_task_count_active_sortie_lb_count": 0,
            "required_task_count_infeasible_by_feasible_task_count": bool(
                preflight_required_task_count_infeasible_by_feasible_task_count
            ),
            "required_task_count_infeasible_by_slot_capacity": bool(
                preflight_required_task_count_infeasible_by_slot_capacity
            ),
            "required_task_count_infeasible_by_slot_sequence_capacity": bool(
                preflight_required_task_count_infeasible_by_slot_sequence_capacity
            ),
            "required_task_count_infeasible_by_slot_matching": bool(
                preflight_required_task_count_infeasible_by_slot_matching
            ),
            "required_task_count_infeasible_by_pair_conflict_capacity": False,
            "required_task_count_certified_by_dual_task_slot_lower_bound": False,
            "required_task_count_infeasible_by_dual_task_slot_lower_bound": False,
            "dual_task_slot_lower_bound_enabled": bool(dual_task_slot_lower_bound),
            "dual_task_slot_lower_bound_applicable": False,
            "dual_task_slot_lower_bound_optimal": False,
            "dual_task_slot_lower_bound_status": "",
            "dual_task_slot_lower_bound_value": None,
            "dual_task_slot_lower_bound_region_infeasible": False,
            "dual_task_slot_lower_bound_wall_time_sec": 0.0,
            "dual_task_slot_lower_bound_variable_count": 0,
            "dual_task_slot_lower_bound_constraint_count": 0,
            "dual_task_slot_lower_bound_pair_conflict_row_count": 0,
            "dual_task_slot_lower_bound_hyperedge_conflict_row_count": 0,
            "dual_task_slot_full_space_lower_bound_enabled": bool(dual_task_slot_full_space_lower_bound),
            "dual_task_slot_full_space_lower_bound_applicable": False,
            "dual_task_slot_full_space_lower_bound_early_stop_on_negative": bool(
                dual_task_slot_full_space_lb_early_stop_on_negative
            ),
            "dual_task_slot_full_space_lower_bound_early_stopped_on_negative": False,
            "dual_task_slot_full_space_lower_bound_coverage_complete": False,
            "dual_task_slot_full_space_lower_bound_can_certify": False,
            "dual_task_slot_full_space_lower_bound_region_count": 0,
            "dual_task_slot_full_space_lower_bound_optimal_region_count": 0,
            "dual_task_slot_full_space_lower_bound_infeasible_region_count": 0,
            "dual_task_slot_full_space_lower_bound_unsupported_region_count": 0,
            "dual_task_slot_full_space_lower_bound_negative_region_count": 0,
            "dual_task_slot_full_space_lower_bound_value": None,
            "dual_task_slot_full_space_lower_bound_task_count": None,
            "dual_task_slot_full_space_lower_bound_active_sortie_count": None,
            "dual_task_slot_full_space_lower_bound_wall_time_sec": 0.0,
            "dual_task_slot_full_space_lower_bound_status": "",
            "required_active_sortie_count_enabled": bool(
                required_active_sortie_count_normalized is not None
            ),
            "required_active_sortie_count": required_active_sortie_count_normalized,
            "pricing_complete_for_required_active_sortie_count": bool(
                required_active_sortie_count_normalized is not None
            ),
            "required_active_sortie_count_region_can_certify_no_negative": bool(
                required_active_sortie_count_normalized is not None
                and preflight_required_active_sortie_count_infeasible
            ),
            "required_active_sortie_count_can_certify_full_space": False,
            "required_active_sortie_count_min": int(required_active_sortie_count_min),
            "required_active_sortie_count_max": int(required_active_sortie_count_max),
            "required_active_sortie_count_capacity_min": (
                None
                if preflight_required_active_sortie_count_capacity_min is None
                else int(preflight_required_active_sortie_count_capacity_min)
            ),
            "required_active_sortie_count_expected_counts": required_active_sortie_count_expected_counts,
            "required_active_sortie_count_infeasible": bool(
                preflight_required_active_sortie_count_infeasible
            ),
            "required_active_sortie_count_infeasible_by_empty_slot": False,
            "required_active_sortie_count_infeasible_by_capacity_min": bool(
                preflight_required_active_sortie_count_infeasible_by_capacity_min
            ),
            "required_active_sortie_count_slots_fixed": bool(required_active_sortie_count_slots_fixed),
            "required_active_sortie_count_fixed_slot_count": (
                int(sortie_slots) if required_active_sortie_count_slots_fixed else 0
            ),
            "slot_task_time_pruning_enabled": bool(slot_task_time_pruning),
            "slot_task_time_feasible_assignment_count": int(slot_task_time_feasible_assignment_count),
            "slot_task_time_pruned_assignment_count": int(slot_task_time_pruned_assignment_count),
            "slot_task_time_pruned_due_count": int(slot_task_time_pruned_due_count),
            "slot_task_time_pruned_horizon_count": int(slot_task_time_pruned_horizon_count),
            "slot_task_time_total_assignment_count": int(sortie_slots * len(model_tasks)),
            "slot_task_time_original_total_assignment_count": int(sortie_slots * len(model_tasks)),
            "slot_task_model_assignment_count": int(slot_task_time_feasible_assignment_count),
            "slot_arc_support_pruning_enabled": bool(slot_arc_support_pruning),
            "slot_arc_support_feasible_assignment_count": int(slot_task_time_feasible_assignment_count),
            "slot_arc_support_pruned_assignment_count": 0,
            "slot_arc_support_pruned_unreachable_count": 0,
            "slot_arc_support_pruned_no_return_count": 0,
            "slot_arc_support_pruned_option_count": 0,
            "slot_arc_time_pruned_option_count": 0,
            "single_task_per_active_sortie_arc_pruning_enabled": bool(
                single_task_per_active_sortie_arc_pruning_enabled
            ),
            "single_task_per_active_sortie_arc_pruned_option_count": 0,
            "single_task_per_active_sortie_mtz_disabled": bool(
                single_task_per_active_sortie_arc_pruning_enabled and mtz_connectivity
            ),
            "mtz_connectivity_effective": bool(
                mtz_connectivity and not single_task_per_active_sortie_arc_pruning_enabled
            ),
            "fixed_active_sortie_redundant_constraint_skipped_count": 0,
            "single_task_per_active_sortie_slot_visit_eq_count": 0,
            "single_task_per_active_sortie_y_z_link_skipped_count": 0,
            "resource_arc_pruning_enabled": bool(resource_arc_pruning),
            "resource_arc_pruned_option_count": 0,
            "resource_arc_energy_pruned_option_count": 0,
            "resource_arc_shadow_pruned_option_count": 0,
            "resource_arc_demand_pruned_option_count": 0,
            "task_slot_pair_conflict_capacity_bound_enabled": False,
            "task_slot_pair_conflict_capacity_near_matching_cap": False,
            "task_slot_pair_conflict_capacity_bound_optimal": False,
            "task_slot_pair_conflict_capacity_bound_status": "",
            "task_slot_pair_conflict_capacity_bound_wall_time_sec": 0.0,
            "task_slot_pair_conflict_capacity_bound_variable_count": 0,
            "task_slot_pair_conflict_capacity_bound_constraint_count": 0,
            "task_slot_pair_conflict_capacity_pair_count": 0,
            "task_slot_pair_conflict_capacity_row_count": 0,
            "task_slot_pair_conflict_capacity_hyperedge_count": 0,
            "task_slot_pair_conflict_capacity_hyperedge_row_count": 0,
            "variable_count": 0,
            "constraint_count": 0,
            "wall_time_sec": round(perf_counter() - start_wall, 6),
            "note": (
                "Required region was proven infeasible by pre-MILP slot-task capacity "
                "bounds before building compact arc variables."
            ),
        }

    slot_arc_time_pruned_option_count = 0
    resource_arc_pruned_option_count = 0
    resource_arc_energy_pruned_option_count = 0
    resource_arc_shadow_pruned_option_count = 0
    resource_arc_demand_pruned_option_count = 0
    candidate_arc_options_by_slot: dict[int, list[tuple[str, str, str]]] = {
        slot: [] for slot in range(sortie_slots)
    }
    for slot in range(sortie_slots):
        feasible_task_lookup = set(slot_feasible_tasks[slot])
        for source in nodes:
            if source != "depot" and str(source) not in feasible_task_lookup:
                continue
            for target in nodes:
                if source == target or (source == "depot" and target == "depot"):
                    continue
                if target != "depot" and str(target) not in feasible_task_lookup:
                    continue
                arc_key = (str(source), str(target))
                if arc_key not in path_type_cache:
                    continue
                for path_type in path_type_cache[arc_key]:
                    if (
                        single_task_per_active_sortie_arc_pruning_enabled
                        and source != "depot"
                        and target != "depot"
                    ):
                        single_task_per_active_sortie_arc_pruned_option_count += 1
                        continue
                    if (
                        bool(slot_sequence_capacity_arc_pruning)
                        and int(
                            preflight_slot_sequence_capacity_by_slot.get(
                                int(slot),
                                int(data.max_tasks_per_trip),
                            )
                        )
                        <= 1
                        and source != "depot"
                        and target != "depot"
                    ):
                        slot_sequence_capacity_arc_pruned_option_count += 1
                        continue
                    if bool(resource_arc_pruning):
                        resource_impossible, resource_reason = _arc_option_resource_impossible(
                            data,
                            str(source),
                            str(target),
                            str(path_type),
                            depot_energy_lb_by_task=depot_energy_lb_by_task,
                            task_to_depot_energy_lb_by_task=task_to_depot_energy_lb_by_task,
                            depot_shadow_lb_by_task=depot_shadow_lb_by_task,
                            task_to_depot_shadow_lb_by_task=task_to_depot_shadow_lb_by_task,
                        )
                        if resource_impossible:
                            resource_arc_pruned_option_count += 1
                            if resource_reason == "energy":
                                resource_arc_energy_pruned_option_count += 1
                            elif resource_reason == "shadow":
                                resource_arc_shadow_pruned_option_count += 1
                            elif resource_reason == "demand":
                                resource_arc_demand_pruned_option_count += 1
                            continue
                    option = data.option(source, target, path_type)
                    if bool(slot_task_time_pruning) and source != "depot" and target != "depot":
                        source_task = data.tasks[str(source)]
                        target_task = data.tasks[str(target)]
                        earliest_source_start = max(
                            float(source_task.ready_time),
                            float(slot) * min_active_duration + float(min_depot_travel_by_task[str(source)]),
                        )
                        latest_target_start = float(target_task.due_time) - float(target_task.service_time)
                        earliest_target_start = (
                            earliest_source_start
                            + float(source_task.service_time)
                            + float(option.travel_time_min)
                        )
                        if earliest_target_start > latest_target_start + 1.0e-9:
                            slot_arc_time_pruned_option_count += 1
                            continue
                    candidate_arc_options_by_slot[slot].append(
                        (str(source), str(target), str(path_type))
                    )

    slot_arc_support_pruned_assignment_count = 0
    slot_arc_support_pruned_unreachable_count = 0
    slot_arc_support_pruned_no_return_count = 0
    slot_arc_support_pruned_option_count = 0
    if bool(slot_arc_support_pruning):

        def reachable_from(seed: str, adjacency: dict[str, set[str]]) -> set[str]:
            seen = {str(seed)}
            stack = [str(seed)]
            while stack:
                current = stack.pop()
                for nxt in adjacency.get(current, set()):
                    if nxt in seen:
                        continue
                    seen.add(nxt)
                    stack.append(nxt)
            return seen

        for slot in range(sortie_slots):
            slot_arcs = candidate_arc_options_by_slot[slot]
            adjacency: dict[str, set[str]] = defaultdict(set)
            reverse_adjacency: dict[str, set[str]] = defaultdict(set)
            for source, target, _path_type in slot_arcs:
                adjacency[str(source)].add(str(target))
                reverse_adjacency[str(target)].add(str(source))
            depot_reachable = reachable_from("depot", adjacency)
            can_return_to_depot = reachable_from("depot", reverse_adjacency)
            supported_tasks: list[str] = []
            for task_id in slot_feasible_tasks[slot]:
                reachable = str(task_id) in depot_reachable
                can_return = str(task_id) in can_return_to_depot
                if reachable and can_return:
                    supported_tasks.append(str(task_id))
                    continue
                slot_arc_support_pruned_assignment_count += 1
                if not reachable:
                    slot_arc_support_pruned_unreachable_count += 1
                if not can_return:
                    slot_arc_support_pruned_no_return_count += 1
            supported_lookup = set(supported_tasks)
            slot_feasible_tasks[slot] = tuple(supported_tasks)
            filtered_arcs = [
                (source, target, path_type)
                for source, target, path_type in slot_arcs
                if (source == "depot" or source in supported_lookup)
                and (target == "depot" or target in supported_lookup)
            ]
            slot_arc_support_pruned_option_count += len(slot_arcs) - len(filtered_arcs)
            candidate_arc_options_by_slot[slot] = filtered_arcs

    slot_task_model_assignment_count = sum(len(row) for row in slot_feasible_tasks.values())
    task_count_feasible_task_count = len(
        {task_id for feasible_tasks in slot_feasible_tasks.values() for task_id in feasible_tasks}
    )
    task_count_slot_capacity_upper_bound = sum(
        min(int(data.max_tasks_per_trip), len(feasible_tasks))
        for feasible_tasks in slot_feasible_tasks.values()
    )
    zero_capacity_slot_truncation_original_slot_count = int(sortie_slots)
    zero_capacity_slot_truncation_effective_slot_count = int(sortie_slots)
    zero_capacity_slot_truncation_trimmed_slot_count = 0
    zero_capacity_slot_truncation_first_zero_slot = None
    slot_sequence_capacity_bounds = (
        _slot_task_sequence_capacity_bounds(
            data,
            model_tasks=tuple(str(task_id) for task_id in model_tasks),
            slot_feasible_tasks=slot_feasible_tasks,
            min_active_duration=float(min_active_duration),
            min_depot_outbound_travel=float(slot_bound["min_depot_outbound_travel_lower_bound"]),
            min_return_travel=min(float(value) for value in min_return_travel_by_task.values()),
        )
        if bool(slot_arc_support_pruning)
        else preflight_slot_sequence_capacity_bounds
    )
    if bool(zero_capacity_slot_truncation) and not bool(required_active_sortie_count_slots_fixed):
        first_zero_slot = _first_zero_capacity_slot(
            slot_sequence_capacity_bounds["slot_sequence_capacity_by_slot"]
        )
        if first_zero_slot is not None and int(first_zero_slot) < int(sortie_slots):
            # z is a prefix-contiguous active-sortie vector.  If slot k cannot
            # carry any task, z_k is forced to zero by the visit lower-bound
            # row, so every later slot is impossible as well.
            zero_capacity_slot_truncation_first_zero_slot = int(first_zero_slot)
            effective_slot_count = max(1, int(first_zero_slot))
            if effective_slot_count < int(sortie_slots):
                sortie_slots = int(effective_slot_count)
                slot_feasible_tasks = {
                    int(slot): tuple(tasks_for_slot)
                    for slot, tasks_for_slot in slot_feasible_tasks.items()
                    if int(slot) < int(sortie_slots)
                }
                candidate_arc_options_by_slot = {
                    int(slot): list(options)
                    for slot, options in candidate_arc_options_by_slot.items()
                    if int(slot) < int(sortie_slots)
                }
                slot_task_model_assignment_count = sum(
                    len(row) for row in slot_feasible_tasks.values()
                )
                task_count_feasible_task_count = len(
                    {
                        task_id
                        for feasible_tasks in slot_feasible_tasks.values()
                        for task_id in feasible_tasks
                    }
                )
                task_count_slot_capacity_upper_bound = sum(
                    min(int(data.max_tasks_per_trip), len(feasible_tasks))
                    for feasible_tasks in slot_feasible_tasks.values()
                )
                slot_sequence_capacity_bounds = _slot_task_sequence_capacity_bounds(
                    data,
                    model_tasks=tuple(str(task_id) for task_id in model_tasks),
                    slot_feasible_tasks=slot_feasible_tasks,
                    min_active_duration=float(min_active_duration),
                    min_depot_outbound_travel=float(
                        slot_bound["min_depot_outbound_travel_lower_bound"]
                    ),
                    min_return_travel=min(float(value) for value in min_return_travel_by_task.values()),
                )
                zero_capacity_slot_truncation_effective_slot_count = int(sortie_slots)
                zero_capacity_slot_truncation_trimmed_slot_count = (
                    int(zero_capacity_slot_truncation_original_slot_count) - int(sortie_slots)
                )
    task_count_slot_sequence_capacity_upper_bound = int(
        slot_sequence_capacity_bounds["slot_sequence_capacity_upper_bound"]
    )
    task_count_slot_matching_capacity_upper_bound = int(
        slot_sequence_capacity_bounds["slot_matching_capacity_upper_bound"]
    )
    slot_capacity_by_slot = {
        int(slot): int(capacity)
        for slot, capacity in zip(
            sorted(slot_feasible_tasks),
            slot_sequence_capacity_bounds["slot_sequence_capacity_by_slot"],
        )
    }
    slot_sequence_capacity_mtz_disabled_by_slot = {
        int(slot): bool(
            slot_sequence_capacity_arc_pruning
            and int(slot_capacity_by_slot.get(int(slot), int(data.max_tasks_per_trip))) <= 1
        )
        for slot in range(sortie_slots)
    }
    slot_sequence_capacity_mtz_disabled_slot_count = sum(
        1 for disabled in slot_sequence_capacity_mtz_disabled_by_slot.values() if disabled
    )
    slot_sequence_capacity_live_bound_by_slot: dict[int, int] = {}
    slot_sequence_capacity_live_bound_tightened_slot_count = 0
    for slot in range(sortie_slots):
        default_capacity = max(1, int(data.max_tasks_per_trip))
        if bool(slot_sequence_capacity_live_bound):
            live_capacity = min(default_capacity, max(0, int(slot_capacity_by_slot.get(slot, 0))))
        else:
            live_capacity = default_capacity
        slot_sequence_capacity_live_bound_by_slot[int(slot)] = int(live_capacity)
        effective_existing_capacity = min(default_capacity, len(slot_feasible_tasks.get(slot, tuple())))
        if bool(slot_sequence_capacity_live_bound) and int(live_capacity) < int(effective_existing_capacity):
            slot_sequence_capacity_live_bound_tightened_slot_count += 1
    pair_energy_lb_by_pair = (
        _pair_route_energy_lower_bounds(data)
        if pair_energy_lb or pair_energy_infeasible_cut or triple_energy_infeasible_cut
        else {}
    )
    pair_time_window_infeasible_by_pair = (
        _pair_time_window_infeasible_pairs(data)
        if pair_time_window_infeasible_cut
        else {}
    )
    pair_shadow_lb_by_pair = (
        _pair_route_shadow_lower_bounds(data)
        if pair_shadow_lb or pair_shadow_infeasible_cut or triple_shadow_infeasible_cut
        else {}
    )
    pair_conflicts_for_capacity: set[tuple[str, str]] = set()
    if pair_energy_infeasible_cut:
        pair_conflicts_for_capacity.update(
            tuple(sorted((str(left_task), str(right_task))))
            for (left_task, right_task), energy_lb in pair_energy_lb_by_pair.items()
            if float(energy_lb) > float(data.energy_limit) + 1.0e-9
        )
    if pair_time_window_infeasible_cut:
        pair_conflicts_for_capacity.update(
            tuple(sorted((str(left_task), str(right_task))))
            for left_task, right_task in pair_time_window_infeasible_by_pair
        )
    if pair_shadow_infeasible_cut:
        pair_conflicts_for_capacity.update(
            tuple(sorted((str(left_task), str(right_task))))
            for (left_task, right_task), shadow_lb in pair_shadow_lb_by_pair.items()
            if float(shadow_lb) > float(data.max_shadow_exposure_per_sortie) + 1.0e-9
        )
    triple_time_window_infeasible_by_triple = (
        _triple_time_window_infeasible_triples(
            data,
            pair_time_window_infeasible_by_pair=pair_time_window_infeasible_by_pair
            if pair_time_window_infeasible_cut
            else {},
        )
        if triple_time_window_infeasible_cut
        else {}
    )
    quad_time_window_infeasible_by_quad = (
        _quad_time_window_infeasible_quads(
            data,
            pair_time_window_infeasible_by_pair=pair_time_window_infeasible_by_pair
            if pair_time_window_infeasible_cut
            else {},
            triple_time_window_infeasible_by_triple=triple_time_window_infeasible_by_triple
            if triple_time_window_infeasible_cut
            else {},
        )
        if quad_time_window_infeasible_cut
        else {}
    )
    triple_shadow_infeasible_lb_by_triple = (
        _triple_route_shadow_infeasible_lower_bounds(data, pair_shadow_lb_by_pair)
        if triple_shadow_infeasible_cut
        else {}
    )
    triple_energy_infeasible_lb_by_triple = (
        _triple_route_energy_infeasible_lower_bounds(data, pair_energy_lb_by_pair)
        if triple_energy_infeasible_cut
        else {}
    )
    hyperedge_conflicts_for_capacity: set[tuple[str, ...]] = set()
    if triple_time_window_infeasible_cut:
        hyperedge_conflicts_for_capacity.update(
            tuple(sorted(str(task_id) for task_id in triple))
            for triple in triple_time_window_infeasible_by_triple
        )
    if quad_time_window_infeasible_cut:
        hyperedge_conflicts_for_capacity.update(
            tuple(sorted(str(task_id) for task_id in quad))
            for quad in quad_time_window_infeasible_by_quad
        )
    if triple_shadow_infeasible_cut:
        hyperedge_conflicts_for_capacity.update(
            tuple(sorted(str(task_id) for task_id in triple))
            for triple in triple_shadow_infeasible_lb_by_triple
        )
    if triple_energy_infeasible_cut:
        hyperedge_conflicts_for_capacity.update(
            tuple(sorted(str(task_id) for task_id in triple))
            for triple in triple_energy_infeasible_lb_by_triple
        )
    refs = objective_references(data)
    cost_coeff = float(data.objective.weight_operating_cost) / float(refs.reference_cost)
    risk_coeff = float(data.objective.weight_risk) / float(refs.reference_risk)
    completion_coeff = float(data.objective.weight_completion) / float(refs.reference_completion)
    pair_conflict_capacity_result = {
        "enabled": False,
        "optimal": False,
        "upper_bound": None,
        "variable_count": 0,
        "constraint_count": 0,
        "pair_conflict_count": int(len(pair_conflicts_for_capacity)),
        "pair_conflict_row_count": 0,
        "hyperedge_conflict_count": int(len(hyperedge_conflicts_for_capacity)),
        "hyperedge_conflict_row_count": 0,
        "wall_time_sec": 0.0,
        "status": "",
    }
    dual_task_slot_lb_result = {
        "enabled": bool(dual_task_slot_lower_bound),
        "applicable": False,
        "optimal": False,
        "region_infeasible": False,
        "lower_bound": None,
        "constant_lower_bound": None,
        "depot_outbound_arc_lower_bound": None,
        "depot_return_arc_lower_bound": None,
        "intertask_arc_lower_bound": None,
        "route_arc_lower_bound_mode": "",
        "route_arc_lower_bound_value": None,
        "route_arc_lower_bound_row_count": 0,
        "route_arc_global_constant_lower_bound": None,
        "route_arc_slot_constant_lower_bound": None,
        "route_arc_constant_lower_bound": None,
        "route_arc_slot_outbound_lower_bound_sum": None,
        "route_arc_slot_return_lower_bound_sum": None,
        "single_task_route_arc_bound_row_count": 0,
        "single_task_route_arc_bound_min": None,
        "single_task_route_arc_bound_max": None,
        "one_pair_rest_single_route_arc_var_count": 0,
        "one_pair_rest_single_route_arc_row_count": 0,
        "one_pair_rest_single_route_arc_pair_count": 0,
        "one_pair_rest_single_route_arc_separation_row_count": 0,
        "one_pair_rest_single_route_arc_separation_iteration_count": 0,
        "pair_route_arc_bound_row_count": 0,
        "pair_route_arc_bound_min": None,
        "pair_route_arc_bound_max": None,
        "triple_route_arc_bound_row_count": 0,
        "triple_route_arc_bound_min": None,
        "triple_route_arc_bound_max": None,
        "pair_completion_lift_var_count": 0,
        "pair_completion_lift_row_count": 0,
        "pair_completion_lift_min": None,
        "pair_completion_lift_max": None,
        "cross_slot_completion_lift_var_count": 0,
        "cross_slot_completion_lift_row_count": 0,
        "cross_slot_pair_completion_separation_row_count": 0,
        "cross_slot_completion_lift_min": None,
        "cross_slot_completion_lift_max": None,
        "selected_task_set": [],
        "selected_slot_task_sets": {},
        "variable_count": 0,
        "constraint_count": 0,
        "pair_conflict_row_count": 0,
        "hyperedge_conflict_row_count": 0,
        "wall_time_sec": 0.0,
        "status": "",
    }
    dual_task_slot_full_space_lb_result = {
        "enabled": bool(dual_task_slot_full_space_lower_bound),
        "applicable": False,
        "coverage_complete": False,
        "can_certify_no_negative": False,
        "region_count": 0,
        "optimal_region_count": 0,
        "infeasible_region_count": 0,
        "unsupported_region_count": 0,
        "negative_bound_region_count": 0,
        "min_lower_bound": None,
        "min_lower_bound_task_count": None,
        "min_lower_bound_active_sortie_count": None,
        "wall_time_sec": 0.0,
        "status": "",
    }
    pair_conflict_capacity_near_matching_cap = bool(
        required_task_count_normalized is not None
        and int(required_task_count_normalized) <= int(task_count_feasible_task_count)
        and int(required_task_count_normalized) <= int(task_count_slot_capacity_upper_bound)
        and int(required_task_count_normalized) <= int(task_count_slot_sequence_capacity_upper_bound)
        and int(required_task_count_normalized) <= int(task_count_slot_matching_capacity_upper_bound)
        and int(required_task_count_normalized)
        > max(0, int(task_count_slot_matching_capacity_upper_bound) - 2)
    )
    pair_conflict_capacity_bound_requested = bool(
        pair_conflict_capacity_near_matching_cap
        or task_slot_pair_conflict_capacity_bound
    )
    if (
        pair_conflict_capacity_bound_requested
        and required_active_sortie_count_normalized is not None
        and (pair_conflicts_for_capacity or hyperedge_conflicts_for_capacity)
    ):
        pair_conflict_capacity_result = _task_slot_pair_conflict_capacity_upper_bound(
            highspy_module=highspy,
            model_tasks=tuple(str(task_id) for task_id in model_tasks),
            slot_feasible_tasks=slot_feasible_tasks,
            slot_capacities=slot_capacity_by_slot,
            pair_conflicts=pair_conflicts_for_capacity,
            hyperedge_conflicts=hyperedge_conflicts_for_capacity,
            time_limit_sec=min(1.0, max(0.001, float(time_limit_sec or 1.0))),
            threads=int(threads),
        )
    task_count_pair_conflict_capacity_upper_bound = pair_conflict_capacity_result.get("upper_bound")
    required_task_count_min_active_sorties = (
        int(math.ceil(float(required_task_count_normalized) / max(1.0, float(data.max_tasks_per_trip))))
        if required_task_count_normalized is not None
        else 0
    )
    required_task_count_infeasible_by_feasible_task_count = bool(
        required_task_count_normalized is not None
        and int(required_task_count_normalized) > int(task_count_feasible_task_count)
    )
    required_task_count_infeasible_by_slot_capacity = bool(
        required_task_count_normalized is not None
        and int(required_task_count_normalized) > int(task_count_slot_capacity_upper_bound)
    )
    required_task_count_infeasible_by_slot_sequence_capacity = bool(
        required_task_count_normalized is not None
        and int(required_task_count_normalized) > int(task_count_slot_sequence_capacity_upper_bound)
    )
    required_task_count_infeasible_by_slot_matching = bool(
        required_task_count_normalized is not None
        and int(required_task_count_normalized) > int(task_count_slot_matching_capacity_upper_bound)
    )
    required_task_count_infeasible_by_pair_conflict_capacity = bool(
        required_task_count_normalized is not None
        and bool(pair_conflict_capacity_result.get("optimal"))
        and task_count_pair_conflict_capacity_upper_bound is not None
        and int(required_task_count_normalized) > int(task_count_pair_conflict_capacity_upper_bound)
    )
    required_active_sortie_count_infeasible_by_empty_slot = bool(
        required_active_sortie_count_normalized is not None
        and required_active_sortie_count_slots_fixed
        and any(
            int(capacity) <= 0
            for capacity in slot_sequence_capacity_bounds["slot_sequence_capacity_by_slot"][
                : int(sortie_slots)
            ]
        )
    )
    required_active_sortie_count_capacity_min = (
        preflight_required_active_sortie_count_capacity_min
    )
    required_active_sortie_count_infeasible_by_capacity_min = bool(
        preflight_required_active_sortie_count_infeasible_by_capacity_min
    )
    required_active_sortie_count_infeasible = bool(
        required_active_sortie_count_normalized is not None
        and (
            int(required_active_sortie_count_normalized) < int(required_active_sortie_count_min)
            or int(required_active_sortie_count_normalized) > int(required_active_sortie_count_max)
            or int(required_active_sortie_count_normalized) > int(sortie_slots)
            or required_active_sortie_count_infeasible_by_empty_slot
            or required_active_sortie_count_infeasible_by_capacity_min
        )
    )
    if (
        bool(dual_task_slot_lower_bound)
        and not bool(negative_feasibility_search)
        and not bool(duals.cuts)
        and required_task_count_normalized is not None
        and required_active_sortie_count_normalized is not None
        and required_active_sortie_count_slots_fixed
        and not required_task_count_infeasible_by_feasible_task_count
        and not required_task_count_infeasible_by_slot_capacity
        and not required_task_count_infeasible_by_slot_sequence_capacity
        and not required_task_count_infeasible_by_slot_matching
        and not required_task_count_infeasible_by_pair_conflict_capacity
        and not required_active_sortie_count_infeasible
        and required_task_count_min_active_sorties <= int(sortie_slots)
    ):
        dual_task_slot_lb_result = _dual_task_slot_reduced_cost_lower_bound(
            highspy_module=highspy,
            data=data,
            duals=duals,
            model_tasks=tuple(str(task_id) for task_id in model_tasks),
            slot_feasible_tasks=slot_feasible_tasks,
            slot_capacities=slot_capacity_by_slot,
            required_task_count=int(required_task_count_normalized),
            required_active_sortie_count=int(required_active_sortie_count_normalized),
            cost_coeff=float(cost_coeff),
            risk_coeff=float(risk_coeff),
            completion_coeff=float(completion_coeff),
            min_active_duration=float(min_active_duration),
            min_depot_travel_by_task=min_depot_travel_by_task,
            pair_conflicts=pair_conflicts_for_capacity,
            hyperedge_conflicts=hyperedge_conflicts_for_capacity,
            time_limit_sec=min(5.0, max(0.001, float(time_limit_sec or 5.0))),
            threads=int(threads),
        )
    if (
        bool(dual_task_slot_full_space_lower_bound)
        and not bool(negative_feasibility_search)
        and not bool(duals.cuts)
        and required_task_set_normalized is None
        and required_task_count_normalized is None
        and required_active_sortie_count_normalized is None
        and not forbidden_arc_patterns
        and not forbidden_task_sets
    ):
        dual_task_slot_full_space_lb_result = _dual_task_slot_full_space_lower_bound_scan(
            highspy,
            data,
            duals,
            model_tasks=tuple(str(task_id) for task_id in model_tasks),
            slot_feasible_tasks=slot_feasible_tasks,
            slot_capacities=slot_capacity_by_slot,
            cost_coeff=float(cost_coeff),
            risk_coeff=float(risk_coeff),
            completion_coeff=float(completion_coeff),
            min_active_duration=float(min_active_duration),
            min_depot_travel_by_task=min_depot_travel_by_task,
            pair_conflicts=pair_conflicts_for_capacity,
            hyperedge_conflicts=hyperedge_conflicts_for_capacity,
            negative_eps=float(negative_eps),
            per_region_time_limit_sec=float(dual_task_slot_full_space_lb_time_limit_sec),
            early_stop_on_negative_bound=bool(
                dual_task_slot_full_space_lb_early_stop_on_negative
            ),
            threads=int(threads),
        )
    dual_task_slot_lb_value = dual_task_slot_lb_result.get("lower_bound")
    dual_task_slot_full_space_lb_value = dual_task_slot_full_space_lb_result.get("min_lower_bound")
    if bool(dual_task_slot_full_space_lb_result.get("can_certify_no_negative")):
        return {
            "status": "COMPACT_HIGHS_PRICING_DUAL_TASK_SLOT_FULL_SPACE_LB_CERTIFIED",
            "algorithm_status": "COMPACT_HIGHS_PRICING_DUAL_TASK_SLOT_FULL_SPACE_LB_CERTIFIED",
            "exact_status": "EXACT_PRICING_DUAL_TASK_SLOT_FULL_SPACE_LB_CERTIFIED",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "best_reduced_cost": None,
            "dual_bound": (
                None
                if dual_task_slot_full_space_lb_value is None
                else round(float(dual_task_slot_full_space_lb_value), 9)
            ),
            "bound": (
                None
                if dual_task_slot_full_space_lb_value is None
                else round(float(dual_task_slot_full_space_lb_value), 9)
            ),
            "global_remaining_rc_lb": (
                None
                if dual_task_slot_full_space_lb_value is None
                else round(float(dual_task_slot_full_space_lb_value), 9)
            ),
            "global_remaining_rc_lb_valid": True,
            "global_remaining_rc_lb_coverage_complete": True,
            "frontier_region_count": int(dual_task_slot_full_space_lb_result.get("region_count") or 0),
            "frontier_unsupported_region_count": 0,
            "negative_found": False,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "journeys": tuple(),
            "task_count": len(tasks),
            "pricing_model_task_count": len(model_tasks),
            "dual_task_slot_full_space_lower_bound_enabled": True,
            "dual_task_slot_full_space_lower_bound_applicable": True,
            "dual_task_slot_full_space_lower_bound_early_stop_on_negative": bool(
                dual_task_slot_full_space_lb_result.get("early_stop_on_negative_bound")
            ),
            "dual_task_slot_full_space_lower_bound_early_stopped_on_negative": bool(
                dual_task_slot_full_space_lb_result.get("early_stopped_on_negative_bound")
            ),
            "dual_task_slot_full_space_lower_bound_coverage_complete": True,
            "dual_task_slot_full_space_lower_bound_can_certify": True,
            "dual_task_slot_full_space_lower_bound_region_count": int(
                dual_task_slot_full_space_lb_result.get("region_count") or 0
            ),
            "dual_task_slot_full_space_lower_bound_optimal_region_count": int(
                dual_task_slot_full_space_lb_result.get("optimal_region_count") or 0
            ),
            "dual_task_slot_full_space_lower_bound_infeasible_region_count": int(
                dual_task_slot_full_space_lb_result.get("infeasible_region_count") or 0
            ),
            "dual_task_slot_full_space_lower_bound_unsupported_region_count": int(
                dual_task_slot_full_space_lb_result.get("unsupported_region_count") or 0
            ),
            "dual_task_slot_full_space_lower_bound_negative_region_count": int(
                dual_task_slot_full_space_lb_result.get("negative_bound_region_count") or 0
            ),
            "dual_task_slot_full_space_lower_bound_value": dual_task_slot_full_space_lb_value,
            "dual_task_slot_full_space_lower_bound_task_count": (
                dual_task_slot_full_space_lb_result.get("min_lower_bound_task_count")
            ),
            "dual_task_slot_full_space_lower_bound_active_sortie_count": (
                dual_task_slot_full_space_lb_result.get("min_lower_bound_active_sortie_count")
            ),
            "dual_task_slot_full_space_lower_bound_wall_time_sec": float(
                dual_task_slot_full_space_lb_result.get("wall_time_sec") or 0.0
            ),
            "variable_count": 0,
            "constraint_count": 0,
            "wall_time_sec": round(perf_counter() - start_wall, 6),
            "note": "Full pricing space has no negative reduced-cost column by safe dual task-slot lower-bound partition scan.",
        }
    required_task_count_certified_by_dual_task_slot_lb = bool(
        required_task_count_normalized is not None
        and bool(dual_task_slot_lb_result.get("optimal"))
        and dual_task_slot_lb_value is not None
        and float(dual_task_slot_lb_value) >= -abs(float(negative_eps))
    )
    required_task_count_infeasible_by_dual_task_slot_lb = bool(
        required_task_count_normalized is not None
        and bool(dual_task_slot_lb_result.get("region_infeasible"))
    )
    if (
        required_task_count_normalized is not None
        and (
            required_task_count_infeasible_by_feasible_task_count
            or required_task_count_infeasible_by_slot_capacity
            or required_task_count_infeasible_by_slot_sequence_capacity
            or required_task_count_infeasible_by_slot_matching
            or required_task_count_infeasible_by_pair_conflict_capacity
            or required_task_count_certified_by_dual_task_slot_lb
            or required_task_count_infeasible_by_dual_task_slot_lb
            or required_task_count_min_active_sorties > int(sortie_slots)
        )
    ) or required_active_sortie_count_infeasible:
        active_sortie_infeasible_only = bool(
            required_active_sortie_count_infeasible
            and not required_task_count_infeasible_by_feasible_task_count
            and not required_task_count_infeasible_by_slot_capacity
            and not required_task_count_infeasible_by_slot_sequence_capacity
            and not required_task_count_infeasible_by_slot_matching
            and not required_task_count_infeasible_by_pair_conflict_capacity
            and required_task_count_min_active_sorties <= int(sortie_slots)
        )
        return {
            "status": (
                "COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_DUAL_TASK_SLOT_LB_CERTIFIED"
                if required_task_count_certified_by_dual_task_slot_lb
                else (
                "COMPACT_HIGHS_PRICING_REQUIRED_ACTIVE_SORTIE_COUNT_INFEASIBLE"
                if active_sortie_infeasible_only
                else "COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_INFEASIBLE"
                )
            ),
            "algorithm_status": (
                "COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_DUAL_TASK_SLOT_LB_CERTIFIED"
                if required_task_count_certified_by_dual_task_slot_lb
                else (
                "COMPACT_HIGHS_PRICING_REQUIRED_ACTIVE_SORTIE_COUNT_INFEASIBLE"
                if active_sortie_infeasible_only
                else "COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_INFEASIBLE"
                )
            ),
            "exact_status": (
                "REQUIRED_TASK_COUNT_PRICING_DUAL_TASK_SLOT_LB_CERTIFIED"
                if required_task_count_certified_by_dual_task_slot_lb
                else (
                "REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE"
                if active_sortie_infeasible_only
                else "REQUIRED_TASK_COUNT_PRICING_INFEASIBLE"
                )
            ),
            "pricing_state": "INCOMPLETE_LIMIT",
            "best_reduced_cost": None,
            "dual_bound": (
                None
                if dual_task_slot_lb_value is None
                else round(float(dual_task_slot_lb_value), 9)
            ),
            "negative_found": False,
            "can_certify_no_negative": False,
            "journeys": tuple(),
            "task_count": len(tasks),
            "pricing_model_task_count": len(model_tasks),
            "required_task_count_enabled": bool(required_task_count_normalized is not None),
            "required_task_count": required_task_count_normalized,
            "pricing_complete_for_required_task_count": bool(
                required_task_count_normalized is not None
            ),
            "required_task_count_region_can_certify_no_negative": bool(
                required_task_count_normalized is not None
            ),
            "required_task_count_can_certify_full_space": False,
            "required_task_count_feasible_task_count": int(task_count_feasible_task_count),
            "required_task_count_slot_capacity_task_upper_bound": int(task_count_slot_capacity_upper_bound),
            "required_task_count_slot_sequence_capacity_upper_bound": int(
                task_count_slot_sequence_capacity_upper_bound
            ),
            "required_task_count_slot_matching_capacity_upper_bound": int(
                task_count_slot_matching_capacity_upper_bound
            ),
            "required_task_count_pair_conflict_capacity_upper_bound": (
                None
                if task_count_pair_conflict_capacity_upper_bound is None
                else int(task_count_pair_conflict_capacity_upper_bound)
            ),
            "required_task_count_min_active_sorties": int(required_task_count_min_active_sorties),
            "required_task_count_active_sortie_lb_count": 0,
            "required_task_count_infeasible_by_feasible_task_count": required_task_count_infeasible_by_feasible_task_count,
            "required_task_count_infeasible_by_slot_capacity": bool(
                required_task_count_infeasible_by_slot_capacity
                or required_task_count_min_active_sorties > int(sortie_slots)
            ),
            "required_task_count_infeasible_by_slot_sequence_capacity": bool(
                required_task_count_infeasible_by_slot_sequence_capacity
            ),
            "required_task_count_infeasible_by_slot_matching": bool(
                required_task_count_infeasible_by_slot_matching
            ),
            "required_task_count_infeasible_by_pair_conflict_capacity": bool(
                required_task_count_infeasible_by_pair_conflict_capacity
            ),
            "required_task_count_certified_by_dual_task_slot_lower_bound": bool(
                required_task_count_certified_by_dual_task_slot_lb
            ),
            "required_task_count_infeasible_by_dual_task_slot_lower_bound": bool(
                required_task_count_infeasible_by_dual_task_slot_lb
            ),
            "dual_task_slot_lower_bound_enabled": bool(dual_task_slot_lb_result.get("enabled")),
            "dual_task_slot_lower_bound_applicable": bool(dual_task_slot_lb_result.get("applicable")),
            "dual_task_slot_lower_bound_optimal": bool(dual_task_slot_lb_result.get("optimal")),
            "dual_task_slot_lower_bound_status": str(dual_task_slot_lb_result.get("status") or ""),
            "dual_task_slot_lower_bound_value": (
                None
                if dual_task_slot_lb_value is None
                else round(float(dual_task_slot_lb_value), 9)
            ),
            "dual_task_slot_lower_bound_region_infeasible": bool(
                dual_task_slot_lb_result.get("region_infeasible")
            ),
            "dual_task_slot_lower_bound_constant": dual_task_slot_lb_result.get("constant_lower_bound"),
            "dual_task_slot_lower_bound_depot_outbound_arc": dual_task_slot_lb_result.get(
                "depot_outbound_arc_lower_bound"
            ),
            "dual_task_slot_lower_bound_depot_return_arc": dual_task_slot_lb_result.get(
                "depot_return_arc_lower_bound"
            ),
            "dual_task_slot_lower_bound_intertask_arc": dual_task_slot_lb_result.get(
                "intertask_arc_lower_bound"
            ),
            "dual_task_slot_lower_bound_route_arc_mode": dual_task_slot_lb_result.get(
                "route_arc_lower_bound_mode"
            ),
            "dual_task_slot_lower_bound_route_arc_value": dual_task_slot_lb_result.get(
                "route_arc_lower_bound_value"
            ),
            "dual_task_slot_lower_bound_route_arc_row_count": int(
                dual_task_slot_lb_result.get("route_arc_lower_bound_row_count") or 0
            ),
            "dual_task_slot_lower_bound_route_arc_global_constant": dual_task_slot_lb_result.get(
                "route_arc_global_constant_lower_bound"
            ),
            "dual_task_slot_lower_bound_route_arc_slot_constant": dual_task_slot_lb_result.get(
                "route_arc_slot_constant_lower_bound"
            ),
            "dual_task_slot_lower_bound_route_arc_constant": dual_task_slot_lb_result.get(
                "route_arc_constant_lower_bound"
            ),
            "dual_task_slot_lower_bound_route_arc_slot_outbound_sum": dual_task_slot_lb_result.get(
                "route_arc_slot_outbound_lower_bound_sum"
            ),
            "dual_task_slot_lower_bound_route_arc_slot_return_sum": dual_task_slot_lb_result.get(
                "route_arc_slot_return_lower_bound_sum"
            ),
            "dual_task_slot_lower_bound_single_task_route_arc_bound_row_count": int(
                dual_task_slot_lb_result.get("single_task_route_arc_bound_row_count") or 0
            ),
            "dual_task_slot_lower_bound_single_task_route_arc_bound_min": dual_task_slot_lb_result.get(
                "single_task_route_arc_bound_min"
            ),
            "dual_task_slot_lower_bound_single_task_route_arc_bound_max": dual_task_slot_lb_result.get(
                "single_task_route_arc_bound_max"
            ),
            "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_var_count": int(
                dual_task_slot_lb_result.get("one_pair_rest_single_route_arc_var_count") or 0
            ),
            "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_row_count": int(
                dual_task_slot_lb_result.get("one_pair_rest_single_route_arc_row_count") or 0
            ),
            "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_pair_count": int(
                dual_task_slot_lb_result.get("one_pair_rest_single_route_arc_pair_count") or 0
            ),
            "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_separation_row_count": int(
                dual_task_slot_lb_result.get("one_pair_rest_single_route_arc_separation_row_count") or 0
            ),
            "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_separation_iteration_count": int(
                dual_task_slot_lb_result.get("one_pair_rest_single_route_arc_separation_iteration_count") or 0
            ),
            "dual_task_slot_lower_bound_pair_route_arc_bound_row_count": int(
                dual_task_slot_lb_result.get("pair_route_arc_bound_row_count") or 0
            ),
            "dual_task_slot_lower_bound_pair_route_arc_bound_min": dual_task_slot_lb_result.get(
                "pair_route_arc_bound_min"
            ),
            "dual_task_slot_lower_bound_pair_route_arc_bound_max": dual_task_slot_lb_result.get(
                "pair_route_arc_bound_max"
            ),
            "dual_task_slot_lower_bound_triple_route_arc_bound_row_count": int(
                dual_task_slot_lb_result.get("triple_route_arc_bound_row_count") or 0
            ),
            "dual_task_slot_lower_bound_triple_route_arc_bound_min": dual_task_slot_lb_result.get(
                "triple_route_arc_bound_min"
            ),
            "dual_task_slot_lower_bound_triple_route_arc_bound_max": dual_task_slot_lb_result.get(
                "triple_route_arc_bound_max"
            ),
            "dual_task_slot_lower_bound_pair_completion_lift_var_count": int(
                dual_task_slot_lb_result.get("pair_completion_lift_var_count") or 0
            ),
            "dual_task_slot_lower_bound_pair_completion_lift_row_count": int(
                dual_task_slot_lb_result.get("pair_completion_lift_row_count") or 0
            ),
            "dual_task_slot_lower_bound_pair_completion_lift_min": dual_task_slot_lb_result.get(
                "pair_completion_lift_min"
            ),
            "dual_task_slot_lower_bound_pair_completion_lift_max": dual_task_slot_lb_result.get(
                "pair_completion_lift_max"
            ),
            "dual_task_slot_lower_bound_cross_slot_completion_lift_var_count": int(
                dual_task_slot_lb_result.get("cross_slot_completion_lift_var_count") or 0
            ),
            "dual_task_slot_lower_bound_cross_slot_completion_lift_row_count": int(
                dual_task_slot_lb_result.get("cross_slot_completion_lift_row_count") or 0
            ),
            "dual_task_slot_lower_bound_cross_slot_pair_completion_separation_row_count": int(
                dual_task_slot_lb_result.get("cross_slot_pair_completion_separation_row_count") or 0
            ),
            "dual_task_slot_lower_bound_cross_slot_completion_lift_min": dual_task_slot_lb_result.get(
                "cross_slot_completion_lift_min"
            ),
            "dual_task_slot_lower_bound_cross_slot_completion_lift_max": dual_task_slot_lb_result.get(
                "cross_slot_completion_lift_max"
            ),
            "dual_task_slot_lower_bound_selected_task_set": list(
                dual_task_slot_lb_result.get("selected_task_set") or []
            ),
            "dual_task_slot_lower_bound_selected_slot_task_sets": dict(
                dual_task_slot_lb_result.get("selected_slot_task_sets") or {}
            ),
            "dual_task_slot_lower_bound_wall_time_sec": float(
                dual_task_slot_lb_result.get("wall_time_sec") or 0.0
            ),
            "dual_task_slot_lower_bound_variable_count": int(
                dual_task_slot_lb_result.get("variable_count") or 0
            ),
            "dual_task_slot_lower_bound_constraint_count": int(
                dual_task_slot_lb_result.get("constraint_count") or 0
            ),
            "dual_task_slot_lower_bound_pair_conflict_row_count": int(
                dual_task_slot_lb_result.get("pair_conflict_row_count") or 0
            ),
            "dual_task_slot_lower_bound_hyperedge_conflict_row_count": int(
                dual_task_slot_lb_result.get("hyperedge_conflict_row_count") or 0
            ),
            "task_slot_pair_conflict_capacity_bound_enabled": bool(
                pair_conflict_capacity_result.get("enabled")
            ),
            "task_slot_pair_conflict_capacity_near_matching_cap": bool(
                pair_conflict_capacity_near_matching_cap
            ),
            "task_slot_pair_conflict_capacity_bound_requested": bool(
                pair_conflict_capacity_bound_requested
            ),
            "task_slot_pair_conflict_capacity_bound_optimal": bool(
                pair_conflict_capacity_result.get("optimal")
            ),
            "task_slot_pair_conflict_capacity_bound_status": str(
                pair_conflict_capacity_result.get("status") or ""
            ),
            "task_slot_pair_conflict_capacity_bound_wall_time_sec": float(
                pair_conflict_capacity_result.get("wall_time_sec") or 0.0
            ),
            "task_slot_pair_conflict_capacity_bound_variable_count": int(
                pair_conflict_capacity_result.get("variable_count") or 0
            ),
            "task_slot_pair_conflict_capacity_bound_constraint_count": int(
                pair_conflict_capacity_result.get("constraint_count") or 0
            ),
            "task_slot_pair_conflict_capacity_pair_count": int(
                pair_conflict_capacity_result.get("pair_conflict_count") or 0
            ),
            "task_slot_pair_conflict_capacity_row_count": int(
                pair_conflict_capacity_result.get("pair_conflict_row_count") or 0
            ),
            "task_slot_pair_conflict_capacity_hyperedge_count": int(
                pair_conflict_capacity_result.get("hyperedge_conflict_count") or 0
            ),
            "task_slot_pair_conflict_capacity_hyperedge_row_count": int(
                pair_conflict_capacity_result.get("hyperedge_conflict_row_count") or 0
            ),
            "required_active_sortie_count_enabled": bool(
                required_active_sortie_count_normalized is not None
            ),
            "required_active_sortie_count": required_active_sortie_count_normalized,
            "pricing_complete_for_required_active_sortie_count": bool(
                required_active_sortie_count_normalized is not None
            ),
            "required_active_sortie_count_region_can_certify_no_negative": bool(
                required_active_sortie_count_normalized is not None
            ),
            "required_active_sortie_count_can_certify_full_space": False,
            "required_active_sortie_count_min": int(required_active_sortie_count_min),
            "required_active_sortie_count_max": int(required_active_sortie_count_max),
            "required_active_sortie_count_capacity_min": (
                None
                if required_active_sortie_count_capacity_min is None
                else int(required_active_sortie_count_capacity_min)
            ),
            "required_active_sortie_count_expected_counts": required_active_sortie_count_expected_counts,
            "required_active_sortie_count_infeasible": bool(required_active_sortie_count_infeasible),
            "required_active_sortie_count_infeasible_by_empty_slot": bool(
                required_active_sortie_count_infeasible_by_empty_slot
            ),
            "required_active_sortie_count_infeasible_by_capacity_min": bool(
                required_active_sortie_count_infeasible_by_capacity_min
            ),
            "required_active_sortie_count_slots_fixed": bool(required_active_sortie_count_slots_fixed),
            "required_active_sortie_count_fixed_slot_count": (
                int(sortie_slots) if required_active_sortie_count_slots_fixed else 0
            ),
            "sortie_slots_per_journey": int(sortie_slots),
            "slot_task_time_pruning_enabled": bool(slot_task_time_pruning),
            "slot_task_time_feasible_assignment_count": int(slot_task_time_feasible_assignment_count),
            "slot_task_time_pruned_assignment_count": int(slot_task_time_pruned_assignment_count),
            "slot_task_time_pruned_due_count": int(slot_task_time_pruned_due_count),
            "slot_task_time_pruned_horizon_count": int(slot_task_time_pruned_horizon_count),
            "slot_task_time_total_assignment_count": int(len(model_tasks) * sortie_slots),
            "slot_task_time_original_total_assignment_count": int(len(tasks) * sortie_slots),
            "slot_task_model_assignment_count": int(slot_task_model_assignment_count),
            "slot_arc_support_pruning_enabled": bool(slot_arc_support_pruning),
            "slot_arc_support_feasible_assignment_count": int(slot_task_model_assignment_count),
            "slot_arc_support_pruned_assignment_count": int(slot_arc_support_pruned_assignment_count),
            "slot_arc_support_pruned_unreachable_count": int(
                slot_arc_support_pruned_unreachable_count
            ),
            "slot_arc_support_pruned_no_return_count": int(
                slot_arc_support_pruned_no_return_count
            ),
            "slot_arc_support_pruned_option_count": int(slot_arc_support_pruned_option_count),
            "slot_arc_time_pruned_option_count": int(slot_arc_time_pruned_option_count),
            "single_task_per_active_sortie_arc_pruning_enabled": bool(
                single_task_per_active_sortie_arc_pruning_enabled
            ),
            "single_task_per_active_sortie_arc_pruned_option_count": int(
                single_task_per_active_sortie_arc_pruned_option_count
            ),
            "single_task_per_active_sortie_mtz_disabled": bool(
                single_task_per_active_sortie_arc_pruning_enabled and mtz_connectivity
            ),
            "mtz_connectivity_effective": bool(mtz_connectivity_effective),
            "fixed_active_sortie_redundant_constraint_skipped_count": 0,
            "single_task_per_active_sortie_slot_visit_eq_count": 0,
            "single_task_per_active_sortie_y_z_link_skipped_count": 0,
            "resource_arc_pruning_enabled": bool(resource_arc_pruning),
            "resource_arc_pruned_option_count": int(resource_arc_pruned_option_count),
            "resource_arc_energy_pruned_option_count": int(resource_arc_energy_pruned_option_count),
            "resource_arc_shadow_pruned_option_count": int(resource_arc_shadow_pruned_option_count),
            "resource_arc_demand_pruned_option_count": int(resource_arc_demand_pruned_option_count),
            "slot_task_sequence_capacity_by_slot": list(
                slot_sequence_capacity_bounds["slot_sequence_capacity_by_slot"]
            ),
            "slot_task_sequence_capacity_upper_bound": int(
                slot_sequence_capacity_bounds["slot_sequence_capacity_upper_bound"]
            ),
            "slot_task_sequence_capacity_limited_slot_count": int(
                slot_sequence_capacity_bounds["slot_sequence_capacity_limited_slot_count"]
            ),
            "slot_task_sequence_capacity_empty_slot_count": int(
                slot_sequence_capacity_bounds["slot_sequence_capacity_empty_slot_count"]
            ),
            "slot_task_matching_capacity_upper_bound": int(
                slot_sequence_capacity_bounds["slot_matching_capacity_upper_bound"]
            ),
            "variable_count": 0,
            "constraint_count": 0,
            "wall_time_sec": round(perf_counter() - start_wall, 6),
            "note": (
                "Required task-count pricing region has no negative reduced-cost column by safe dual task-slot lower bound."
                if required_task_count_certified_by_dual_task_slot_lb
                else "Required task-count pricing region is infeasible by safe task/slot count bounds."
            ),
        }
    forbidden_patterns = tuple(_normalize_forbidden_arc_pattern(row) for row in (forbidden_arc_patterns or tuple()))
    forbidden_patterns = tuple(row for row in forbidden_patterns if row)
    forbidden_task_sets_normalized = tuple(
        _normalize_forbidden_task_set(row, valid_tasks=set(tasks))
        for row in (forbidden_task_sets or tuple())
    )
    forbidden_task_sets_normalized = tuple(row for row in forbidden_task_sets_normalized if row)
    service_start_lb_by_task = (
        _depot_to_task_shortest_travel_lower_bounds(data)
        if service_start_depot_travel_lb
        else {task_id: 0.0 for task_id in tasks}
    )
    task_return_lb_by_task = (
        _task_to_depot_shortest_travel_lower_bounds(data)
        if task_to_depot_return_travel_lb
        else {task_id: 0.0 for task_id in tasks}
    )
    pair_route_duration_lb_by_pair = (
        _pair_route_duration_lower_bounds(data)
        if pair_route_duration_lb
        else {}
    )
    pair_weighted_completion_lb_by_pair = (
        _pair_weighted_completion_lower_bounds(data)
        if pair_weighted_completion_lb
        else {}
    )
    demand_cover_by_subset = (
        _demand_cover_subsets(data)
        if demand_cover_cut
        else {}
    )
    single_task_energy_lb_by_task = (
        _single_task_route_energy_lower_bounds(data)
        if single_task_energy_lb
        else {}
    )
    single_task_shadow_lb_by_task = (
        _single_task_route_shadow_lower_bounds(data)
        if single_task_shadow_lb
        else {}
    )
    pair_time_window_precedence_by_pair = (
        _pair_time_window_forced_precedence_pairs(data)
        if pair_time_window_precedence_cut_effective
        else {}
    )

    highs = highspy.Highs()
    highs.setOptionValue("output_flag", bool(output_flag))
    highs.setOptionValue("threads", max(1, int(threads)))
    highs.setOptionValue("mip_rel_gap", max(0.0, float(mip_gap)))
    objective_bound_no_negative_cutoff_enabled = bool(
        objective_bound_no_negative_cutoff and not negative_feasibility_search
    )
    objective_bound_no_negative_cutoff_value = (
        -abs(float(negative_eps)) if objective_bound_no_negative_cutoff_enabled else None
    )
    if time_limit_sec is not None:
        highs.setOptionValue("time_limit", max(0.001, float(time_limit_sec)))
    highs.setMinimize()
    if objective_bound_no_negative_cutoff_enabled:
        # For a minimization model, HiGHS' objective_bound is a cutoff. If the
        # model is infeasible under objective <= -eps, no negative reduced-cost
        # journey exists. This is a proof target, not a heuristic incumbent stop.
        highs.setOptionValue("objective_bound", float(objective_bound_no_negative_cutoff_value))
    highs_option_overrides = _apply_compact_highs_option_overrides(highs)
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
        for source, target, path_type in candidate_arc_options_by_slot[slot]:
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
    horizon = float(data.horizon)
    tight_service_start_bound_values: list[float] = []
    tight_service_start_bound_count = 0
    slot_service_start_y_lower_bound_count = 0
    slot_service_start_y_lower_bound_max_lift = 0.0
    slot_service_start_y_lower_bound_values: list[float] = []
    for slot in range(sortie_slots):
        for task_id in slot_feasible_tasks[slot]:
            task = data.tasks[task_id]
            y_cost = cost_coeff * (float(task.service_cost) + float(task.service_energy))
            y_cost += risk_coeff * service_risk_value(task)
            y_cost += completion_coeff * float(task.science_weight) * float(task.service_time)
            y_cost -= float(duals.cover.get(str(task_id), 0.0))
            y[vehicle, slot, task_id] = add_var(0.0, 1.0, y_cost, integer=True)
            add_reduced_cost_coefficient(y[vehicle, slot, task_id], y_cost)
            service_start_ub = horizon
            if bool(tight_service_start_bounds):
                service_start_ub = min(horizon, max(0.0, _latest_task_service_start(data, task_id)))
                tight_service_start_bound_values.append(float(service_start_ub))
                if service_start_ub < horizon - 1.0e-9:
                    tight_service_start_bound_count += 1
            service_start[vehicle, slot, task_id] = add_var(
                0.0,
                service_start_ub,
                completion_coeff * float(task.science_weight),
                integer=False,
            )
            add_reduced_cost_coefficient(
                service_start[vehicle, slot, task_id],
                completion_coeff * float(task.science_weight),
            )
            if mtz_connectivity_effective:
                if not slot_sequence_capacity_mtz_disabled_by_slot.get(slot, False):
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
        z_lb = 1.0 if required_active_sortie_count_slots_fixed else 0.0
        z[vehicle, slot] = add_var(z_lb, 1.0, 0.0, integer=True)
        sortie_start[vehicle, slot] = add_var(0.0, float(sortie_start_upper_bound), 0.0)
        sortie_return[vehicle, slot] = add_var(0.0, float(data.horizon), 0.0)
        sortie_end[vehicle, slot] = add_var(0.0, float(data.horizon), 0.0)

    all_task_slot_coefficients: dict[int, float] = {}
    for task_id in model_tasks:
        task_slot_coefficients = {
            y[vehicle, slot, task_id]: 1.0
            for slot in range(sortie_slots)
            if (vehicle, slot, task_id) in y
        }
        all_task_slot_coefficients.update(task_slot_coefficients)
        if task_slot_coefficients:
            add_le(task_slot_coefficients, 1.0)
        if required_task_set_normalized is not None:
            required_rhs = 1.0 if str(task_id) in set(required_task_set_normalized) else 0.0
            add_eq(task_slot_coefficients, required_rhs)
    if required_task_count_normalized is not None:
        add_eq(all_task_slot_coefficients, float(required_task_count_normalized))
    if not required_active_sortie_count_slots_fixed:
        add_ge({z[vehicle, slot]: 1.0 for slot in range(sortie_slots)}, 1.0)
    if required_active_sortie_count_normalized is not None and not required_active_sortie_count_slots_fixed:
        add_eq(
            {z[vehicle, slot]: 1.0 for slot in range(sortie_slots)},
            float(required_active_sortie_count_normalized),
        )
    required_task_count_active_sortie_lb_count_total = 0
    if required_task_count_normalized is not None:
        for slot in range(min(int(required_task_count_min_active_sorties), int(sortie_slots))):
            if not required_active_sortie_count_slots_fixed:
                add_ge({z[vehicle, slot]: 1.0}, 1.0)
                required_task_count_active_sortie_lb_count_total += 1

    pair_adjacency_cut_count_total = 0
    mtz_endpoint_order_cut_count_total = 0
    sortie_slot_position_bound_count_total = 0
    service_start_depot_travel_lb_count_total = 0
    task_to_depot_return_travel_lb_count_total = 0
    pair_route_duration_lb_count_total = 0
    pair_weighted_completion_lb_count_total = 0
    demand_cover_cut_count_total = 0
    single_task_energy_lb_count_total = 0
    single_task_shadow_lb_count_total = 0
    pair_energy_lb_count_total = 0
    pair_shadow_lb_count_total = 0
    pair_energy_infeasible_cut_count_total = 0
    pair_time_window_infeasible_cut_count_total = 0
    pair_time_window_precedence_cut_count_total = 0
    triple_time_window_infeasible_cut_count_total = 0
    quad_time_window_infeasible_cut_count_total = 0
    pair_shadow_infeasible_cut_count_total = 0
    triple_shadow_infeasible_cut_count_total = 0
    triple_energy_infeasible_cut_count_total = 0
    fixed_active_sortie_redundant_constraint_skipped_count = 0
    single_task_per_active_sortie_slot_visit_eq_count = 0
    single_task_per_active_sortie_y_z_link_skipped_count = 0
    tight_time_arc_big_m_active_time_bound_count_total = 0
    tight_time_arc_big_m_depot_arc_count_total = 0
    tight_time_arc_big_m_max_reduction = 0.0
    tight_conditional_sequence_big_m_count_total = 0
    tight_conditional_sequence_big_m_max_reduction = 0.0
    for slot in range(sortie_slots):
        feasible_tasks_for_slot = slot_feasible_tasks[slot]
        feasible_task_lookup = set(feasible_tasks_for_slot)
        z_col = z[vehicle, slot]
        # journey_active is fixed to one in single-journey pricing, and z_col already
        # has ub=1. The z <= journey_active row is therefore redundant in every
        # region, not only when active sortie slots are fixed.
        fixed_active_sortie_redundant_constraint_skipped_count += 1
        if slot + 1 < sortie_slots:
            if required_active_sortie_count_slots_fixed:
                fixed_active_sortie_redundant_constraint_skipped_count += 1
            else:
                add_le({z[vehicle, slot + 1]: 1.0, z_col: -1.0}, 0.0)
        if slot > 0:
            sequence_m = float(data.horizon)
            if required_active_sortie_count_slots_fixed:
                sequence_m = 0.0
            elif (
                not active_time_z_bounds_enabled
                and float(sortie_start_upper_bound) >= float(data.horizon) - 1.0e-9
            ):
                # Legacy V4S/V4SZ semantics: inactive slots keep dummy time
                # variables free, so the sequence chain can remain unconditional.
                # This tightens only dummy timing; it does not remove any active
                # journey route.  If active_time_z_bounds fixes inactive times to
                # zero, or tight-time lowers the start upper bound below the
                # horizon, a Big-M relaxation is still required.
                sequence_m = 0.0
            elif tight_time_arc_big_m_enabled and not active_time_z_bounds_enabled:
                # If the current slot is inactive, sortie_start is a dummy time
                # variable. It can safely take any value up to its variable upper
                # bound, so only the part of the previous end time above that
                # bound needs Big-M relaxation. When active_time_z_bounds is on,
                # inactive start is fixed to zero and this tightening is invalid.
                sequence_m = max(
                    0.0,
                    float(data.horizon) - float(sortie_start_upper_bound),
                )
            sequence_reduction = float(data.horizon) - float(sequence_m)
            if sequence_reduction > 1.0e-9:
                tight_conditional_sequence_big_m_count_total += 1
                tight_conditional_sequence_big_m_max_reduction = max(
                    float(tight_conditional_sequence_big_m_max_reduction),
                    float(sequence_reduction),
                )
            add_ge(
                {
                    sortie_start[vehicle, slot]: 1.0,
                    sortie_end[vehicle, slot - 1]: -1.0,
                    z_col: -float(sequence_m),
                },
                -float(sequence_m),
            )
        add_ge({sortie_end[vehicle, slot]: 1.0, sortie_start[vehicle, slot]: -1.0}, 0.0)
        if bool(active_time_z_bounds_enabled):
            add_le(
                {
                    sortie_start[vehicle, slot]: 1.0,
                    z_col: -float(sortie_start_upper_bound),
                },
                0.0,
            )
            add_le(
                {
                    sortie_end[vehicle, slot]: 1.0,
                    z_col: -float(data.horizon),
                },
                0.0,
            )
            tight_time_arc_big_m_active_time_bound_count_total += 2
        if sortie_slot_position_bounds:
            start_lb = float(slot) * min_active_duration
            if start_lb > 1.0e-9:
                add_ge({sortie_start[vehicle, slot]: 1.0, z_col: -start_lb}, 0.0)
                sortie_slot_position_bound_count_total += 1
            end_lb = float(slot + 1) * min_active_duration
            if end_lb > 1.0e-9:
                add_ge({sortie_end[vehicle, slot]: 1.0, z_col: -end_lb}, 0.0)
                sortie_slot_position_bound_count_total += 1
            add_le(
                {
                    sortie_start[vehicle, slot]: 1.0,
                    z_col: float(data.horizon) - latest_sortie_start_upper_bound,
                },
                float(data.horizon),
            )
            sortie_slot_position_bound_count_total += 1
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
        total_task_expr = {y[vehicle, slot, task_id]: 1.0 for task_id in feasible_tasks_for_slot}
        if single_task_per_active_sortie_arc_pruning_enabled:
            add_eq({**total_task_expr, z_col: -1.0}, 0.0)
            single_task_per_active_sortie_slot_visit_eq_count += 1
        else:
            add_le(
                {
                    **total_task_expr,
                    z_col: -float(slot_sequence_capacity_live_bound_by_slot.get(slot, int(data.max_tasks_per_trip))),
                },
                0.0,
            )
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
        for task_id in feasible_tasks_for_slot:
            task = data.tasks[task_id]
            y_col = y[vehicle, slot, task_id]
            start_col = service_start[vehicle, slot, task_id]
            if single_task_per_active_sortie_arc_pruning_enabled:
                single_task_per_active_sortie_y_z_link_skipped_count += 1
            else:
                add_le({y_col: 1.0, z_col: -1.0}, 0.0)
            add_eq({**{x[key]: 1.0 for key in outgoing[(vehicle, slot, task_id)]}, y_col: -1.0}, 0.0)
            add_eq({**{x[key]: 1.0 for key in incoming[(vehicle, slot, task_id)]}, y_col: -1.0}, 0.0)
            if flow_connectivity:
                task_flow = {flow[key]: 1.0 for key in incoming[(vehicle, slot, task_id)]}
                for key in outgoing[(vehicle, slot, task_id)]:
                    task_flow[flow[key]] = task_flow.get(flow[key], 0.0) - 1.0
                add_eq({**task_flow, y_col: -1.0}, 0.0)
            if mtz_connectivity_effective and not slot_sequence_capacity_mtz_disabled_by_slot.get(slot, False):
                order_col = visit_order[vehicle, slot, task_id]
                add_le({order_col: 1.0, y_col: -float(data.max_tasks_per_trip)}, 0.0)
                add_ge({order_col: 1.0, y_col: -1.0}, 0.0)
            service_start_y_lb = float(task.ready_time)
            if bool(slot_service_start_y_lower_bound):
                slot_lb = (
                    float(slot) * float(min_active_duration)
                    + float(min_depot_travel_by_task[str(task_id)])
                )
                tightened_lb = max(float(service_start_y_lb), float(slot_lb))
                lift = float(tightened_lb) - float(service_start_y_lb)
                if lift > 1.0e-9:
                    slot_service_start_y_lower_bound_count += 1
                    slot_service_start_y_lower_bound_max_lift = max(
                        float(slot_service_start_y_lower_bound_max_lift),
                        float(lift),
                    )
                service_start_y_lb = float(tightened_lb)
                slot_service_start_y_lower_bound_values.append(float(service_start_y_lb))
            add_ge({start_col: 1.0, y_col: -float(service_start_y_lb)}, 0.0)
            depot_travel_lb = float(service_start_lb_by_task.get(str(task_id), 0.0))
            if service_start_depot_travel_lb and depot_travel_lb > 1.0e-9:
                time_m = float(data.horizon)
                add_ge(
                    {
                        start_col: 1.0,
                        sortie_start[vehicle, slot]: -1.0,
                        y_col: -float(time_m + depot_travel_lb),
                    },
                    -time_m,
                )
                service_start_depot_travel_lb_count_total += 1
            task_return_lb = float(task.service_time) + float(task_return_lb_by_task.get(str(task_id), 0.0))
            if task_to_depot_return_travel_lb and task_return_lb > 1.0e-9:
                time_m = float(data.horizon)
                add_ge(
                    {
                        sortie_return[vehicle, slot]: 1.0,
                        start_col: -1.0,
                        y_col: -float(time_m + task_return_lb),
                    },
                    -time_m,
                )
                task_to_depot_return_travel_lb_count_total += 1
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
            for left_index, left_task in enumerate(feasible_tasks_for_slot):
                for right_task in feasible_tasks_for_slot[left_index + 1 :]:
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

        if pair_route_duration_lb:
            for (left_task, right_task), duration_lb in pair_route_duration_lb_by_pair.items():
                if left_task not in feasible_task_lookup or right_task not in feasible_task_lookup:
                    continue
                pair_lb = float(duration_lb)
                if pair_lb <= 1.0e-9:
                    continue
                time_m = max(float(data.horizon), pair_lb)
                add_ge(
                    {
                        sortie_return[vehicle, slot]: 1.0,
                        sortie_start[vehicle, slot]: -1.0,
                        y[vehicle, slot, left_task]: -time_m,
                        y[vehicle, slot, right_task]: -time_m,
                    },
                    pair_lb - (2.0 * time_m),
                )
                pair_route_duration_lb_count_total += 1

        if pair_weighted_completion_lb:
            for (left_task, right_task), completion_lb in pair_weighted_completion_lb_by_pair.items():
                if left_task not in feasible_task_lookup or right_task not in feasible_task_lookup:
                    continue
                pair_lb = float(completion_lb)
                if pair_lb <= 1.0e-9:
                    continue
                left_weight = max(0.0, float(data.tasks[left_task].science_weight))
                right_weight = max(0.0, float(data.tasks[right_task].science_weight))
                total_weight = left_weight + right_weight
                if total_weight <= 1.0e-12:
                    continue
                time_m = pair_lb + total_weight * float(data.horizon)
                add_ge(
                    {
                        service_start[vehicle, slot, left_task]: left_weight,
                        service_start[vehicle, slot, right_task]: right_weight,
                        sortie_start[vehicle, slot]: -total_weight,
                        y[vehicle, slot, left_task]: -time_m,
                        y[vehicle, slot, right_task]: -time_m,
                    },
                    pair_lb - (2.0 * time_m),
                )
                pair_weighted_completion_lb_count_total += 1

        if demand_cover_cut:
            for cover in demand_cover_by_subset:
                if any(task_id not in feasible_task_lookup for task_id in cover):
                    continue
                add_le(
                    {y[vehicle, slot, task_id]: 1.0 for task_id in cover},
                    float(len(cover) - 1),
                )
                demand_cover_cut_count_total += 1

        if single_task_energy_lb:
            for task_id, energy_lb in single_task_energy_lb_by_task.items():
                if task_id not in feasible_task_lookup:
                    continue
                lb = float(energy_lb)
                if lb <= 1.0e-9:
                    continue
                coefficients = dict(energy_coefficients)
                y_col = y[vehicle, slot, task_id]
                coefficients[y_col] = coefficients.get(y_col, 0.0) - lb
                add_ge(coefficients, 0.0)
                single_task_energy_lb_count_total += 1

        if single_task_shadow_lb:
            for task_id, shadow_lb in single_task_shadow_lb_by_task.items():
                if task_id not in feasible_task_lookup:
                    continue
                lb = float(shadow_lb)
                if lb <= 1.0e-9:
                    continue
                coefficients = dict(shadow_coefficients)
                y_col = y[vehicle, slot, task_id]
                coefficients[y_col] = coefficients.get(y_col, 0.0) - lb
                add_ge(coefficients, 0.0)
                single_task_shadow_lb_count_total += 1

        if pair_energy_infeasible_cut:
            for (left_task, right_task), energy_lb in pair_energy_lb_by_pair.items():
                if left_task not in feasible_task_lookup or right_task not in feasible_task_lookup:
                    continue
                if float(energy_lb) <= float(data.energy_limit) + 1.0e-9:
                    continue
                add_le(
                    {
                        y[vehicle, slot, left_task]: 1.0,
                        y[vehicle, slot, right_task]: 1.0,
                    },
                    1.0,
                )
                pair_energy_infeasible_cut_count_total += 1

        if pair_time_window_infeasible_cut:
            for left_task, right_task in pair_time_window_infeasible_by_pair:
                if left_task not in feasible_task_lookup or right_task not in feasible_task_lookup:
                    continue
                add_le(
                    {
                        y[vehicle, slot, left_task]: 1.0,
                        y[vehicle, slot, right_task]: 1.0,
                    },
                    1.0,
                )
                pair_time_window_infeasible_cut_count_total += 1

        if (
            pair_time_window_precedence_cut_effective
            and not slot_sequence_capacity_mtz_disabled_by_slot.get(slot, False)
        ):
            order_m = float(data.max_tasks_per_trip)
            for must_precede_task, must_follow_task in pair_time_window_precedence_by_pair:
                if (
                    must_precede_task not in feasible_task_lookup
                    or must_follow_task not in feasible_task_lookup
                ):
                    continue
                add_ge(
                    {
                        visit_order[vehicle, slot, must_follow_task]: 1.0,
                        visit_order[vehicle, slot, must_precede_task]: -1.0,
                        y[vehicle, slot, must_precede_task]: -order_m,
                        y[vehicle, slot, must_follow_task]: -order_m,
                    },
                    1.0 - (2.0 * order_m),
                )
                pair_time_window_precedence_cut_count_total += 1

        if triple_time_window_infeasible_cut:
            for left_task, middle_task, right_task in triple_time_window_infeasible_by_triple:
                if (
                    left_task not in feasible_task_lookup
                    or middle_task not in feasible_task_lookup
                    or right_task not in feasible_task_lookup
                ):
                    continue
                add_le(
                    {
                        y[vehicle, slot, left_task]: 1.0,
                        y[vehicle, slot, middle_task]: 1.0,
                        y[vehicle, slot, right_task]: 1.0,
                    },
                    2.0,
                )
                triple_time_window_infeasible_cut_count_total += 1

        if quad_time_window_infeasible_cut:
            for quad in quad_time_window_infeasible_by_quad:
                first_task, second_task, third_task, fourth_task = quad
                if any(task_id not in feasible_task_lookup for task_id in quad):
                    continue
                add_le(
                    {
                        y[vehicle, slot, first_task]: 1.0,
                        y[vehicle, slot, second_task]: 1.0,
                        y[vehicle, slot, third_task]: 1.0,
                        y[vehicle, slot, fourth_task]: 1.0,
                    },
                    3.0,
                )
                quad_time_window_infeasible_cut_count_total += 1

        if pair_shadow_infeasible_cut:
            for (left_task, right_task), shadow_lb in pair_shadow_lb_by_pair.items():
                if left_task not in feasible_task_lookup or right_task not in feasible_task_lookup:
                    continue
                if float(shadow_lb) <= float(data.max_shadow_exposure_per_sortie) + 1.0e-9:
                    continue
                add_le(
                    {
                        y[vehicle, slot, left_task]: 1.0,
                        y[vehicle, slot, right_task]: 1.0,
                    },
                    1.0,
                )
                pair_shadow_infeasible_cut_count_total += 1

        if triple_energy_infeasible_cut:
            for triple in triple_energy_infeasible_lb_by_triple:
                left_task, middle_task, right_task = triple
                if any(task_id not in feasible_task_lookup for task_id in triple):
                    continue
                add_le(
                    {
                        y[vehicle, slot, left_task]: 1.0,
                        y[vehicle, slot, middle_task]: 1.0,
                        y[vehicle, slot, right_task]: 1.0,
                    },
                    2.0,
                )
                triple_energy_infeasible_cut_count_total += 1

        if triple_shadow_infeasible_cut:
            for triple in triple_shadow_infeasible_lb_by_triple:
                left_task, middle_task, right_task = triple
                if any(task_id not in feasible_task_lookup for task_id in triple):
                    continue
                add_le(
                    {
                        y[vehicle, slot, left_task]: 1.0,
                        y[vehicle, slot, middle_task]: 1.0,
                        y[vehicle, slot, right_task]: 1.0,
                    },
                    2.0,
                )
                triple_shadow_infeasible_cut_count_total += 1

        if pair_energy_lb:
            for (left_task, right_task), energy_lb in pair_energy_lb_by_pair.items():
                if left_task not in feasible_task_lookup or right_task not in feasible_task_lookup:
                    continue
                pair_lb = float(energy_lb)
                if pair_lb <= 1.0e-9:
                    continue
                energy_m = max(float(data.energy_limit), pair_lb)
                coefficients = dict(energy_coefficients)
                coefficients[y[vehicle, slot, left_task]] = (
                    coefficients.get(y[vehicle, slot, left_task], 0.0) - energy_m
                )
                coefficients[y[vehicle, slot, right_task]] = (
                    coefficients.get(y[vehicle, slot, right_task], 0.0) - energy_m
                )
                add_ge(
                    coefficients,
                    pair_lb - (2.0 * energy_m),
                )
                pair_energy_lb_count_total += 1

        if pair_shadow_lb:
            for (left_task, right_task), shadow_lb in pair_shadow_lb_by_pair.items():
                if left_task not in feasible_task_lookup or right_task not in feasible_task_lookup:
                    continue
                pair_lb = float(shadow_lb)
                if pair_lb <= 1.0e-9:
                    continue
                shadow_m = max(float(data.max_shadow_exposure_per_sortie), pair_lb)
                coefficients = dict(shadow_coefficients)
                coefficients[y[vehicle, slot, left_task]] = (
                    coefficients.get(y[vehicle, slot, left_task], 0.0) - shadow_m
                )
                coefficients[y[vehicle, slot, right_task]] = (
                    coefficients.get(y[vehicle, slot, right_task], 0.0) - shadow_m
                )
                add_ge(
                    coefficients,
                    pair_lb - (2.0 * shadow_m),
                )
                pair_shadow_lb_count_total += 1

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
                loose_time_m = _time_arc_big_m(data, travel=travel)
                upper_time_m = _time_arc_upper_big_m(data)
                time_m = _time_arc_big_m(
                    data,
                    travel=travel,
                    source_start_upper_bound=sortie_start_upper_bound
                    if tight_time_arc_big_m_enabled
                    else None,
                )
                if tight_time_arc_big_m_enabled:
                    tight_time_arc_big_m_depot_arc_count_total += 1
                    tight_time_arc_big_m_max_reduction = max(
                        float(tight_time_arc_big_m_max_reduction),
                        float(loose_time_m) - float(time_m),
                    )
                add_ge(
                    {
                        service_start[vehicle, slot, target]: 1.0,
                        sortie_start[vehicle, slot]: -1.0,
                        x_col: -time_m,
                    },
                    travel - time_m,
                )
                add_le(
                    {
                        service_start[vehicle, slot, target]: 1.0,
                        sortie_start[vehicle, slot]: -1.0,
                        x_col: upper_time_m,
                    },
                    travel + upper_time_m,
                )
            elif source != "depot" and target != "depot":
                service = float(data.tasks[source].service_time)
                time_m = _time_arc_big_m(data, travel=travel, service=service, source=source)
                upper_time_m = _time_arc_upper_big_m(data)
                add_ge(
                    {
                        service_start[vehicle, slot, target]: 1.0,
                        service_start[vehicle, slot, source]: -1.0,
                        x_col: -time_m,
                    },
                    service + travel - time_m,
                )
                add_le(
                    {
                        service_start[vehicle, slot, target]: 1.0,
                        service_start[vehicle, slot, source]: -1.0,
                        x_col: upper_time_m,
                    },
                    service + travel + upper_time_m,
                )
            elif source != "depot" and target == "depot":
                service = float(data.tasks[source].service_time)
                time_m = _time_arc_big_m(data, travel=travel, service=service, source=source)
                upper_time_m = _time_arc_upper_big_m(data)
                add_ge(
                    {
                        sortie_return[vehicle, slot]: 1.0,
                        service_start[vehicle, slot, source]: -1.0,
                        x_col: -time_m,
                    },
                    service + travel - time_m,
                )
                add_le(
                    {
                        sortie_return[vehicle, slot]: 1.0,
                        service_start[vehicle, slot, source]: -1.0,
                        x_col: upper_time_m,
                    },
                    service + travel + upper_time_m,
                )
            slot_mtz_connectivity_effective = bool(
                mtz_connectivity_effective
                and not slot_sequence_capacity_mtz_disabled_by_slot.get(slot, False)
            )
            slot_mtz_endpoint_order_cuts_effective = bool(
                mtz_endpoint_order_cuts_effective
                and not slot_sequence_capacity_mtz_disabled_by_slot.get(slot, False)
            )
            if slot_mtz_endpoint_order_cuts_effective and source == "depot" and target != "depot":
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
            elif slot_mtz_endpoint_order_cuts_effective and source != "depot" and target == "depot":
                # If a task returns to the depot, it is the last task in that sortie.
                order_m = float(data.max_tasks_per_trip)
                coefficients = {
                    visit_order[vehicle, slot, source]: 1.0,
                    x_col: -order_m,
                }
                for task_id in feasible_tasks_for_slot:
                    y_col = y[vehicle, slot, task_id]
                    coefficients[y_col] = coefficients.get(y_col, 0.0) - 1.0
                add_ge(coefficients, -order_m)
                mtz_endpoint_order_cut_count_total += 1
            if slot_mtz_connectivity_effective and source != "depot" and target != "depot":
                order_m = float(data.max_tasks_per_trip)
                add_ge(
                    {
                        visit_order[vehicle, slot, target]: 1.0,
                        visit_order[vehicle, slot, source]: -1.0,
                        x_col: -order_m,
                    },
                    1.0 - order_m,
                )

    negative_feasibility_zero_objective_enabled = False
    if negative_feasibility_search:
        # Exact alternative to minimizing reduced cost: ask whether any journey
        # column with rc <= -eps exists.  Infeasibility is then a no-negative
        # proof; a feasible solution is a negative column; time limits remain
        # fail-closed.
        add_le(reduced_cost_coefficients, -abs(float(negative_eps)))
        for col in range(highs.getNumCol()):
            highs.changeColCost(col, 0.0)
        negative_feasibility_zero_objective_enabled = True

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
    forbidden_task_set_skipped_by_required_task_count = 0
    for task_set in forbidden_task_sets_normalized:
        if required_task_count_normalized is not None and len(task_set) != int(required_task_count_normalized):
            forbidden_task_set_skipped_by_required_task_count += 1
            continue
        if any(
            not any((vehicle, slot, task_id) in y for slot in range(sortie_slots))
            for task_id in task_set
        ):
            continue
        coefficients: dict[int, float] = {}
        forbidden_lookup = set(task_set)
        for task_id in tasks:
            sign = 1.0 if task_id in forbidden_lookup else -1.0
            for slot in range(sortie_slots):
                col = y.get((vehicle, slot, task_id))
                if col is not None:
                    coefficients[col] = sign
        if not coefficients:
            continue
        # Forbid exactly this task set while still allowing proper subsets and
        # supersets.  This is only used in restricted discovery, never as a
        # no-negative certificate for the full pricing space.
        add_le(coefficients, float(len(task_set) - 1))
        forbidden_task_set_count += 1

    mip_start_payload = _set_highs_single_journey_mip_start(
        highs,
        data=data,
        duals=duals,
        journey=mip_start_journey,
        vehicle=vehicle,
        sortie_slots=sortie_slots,
        flow_connectivity=bool(flow_connectivity),
        x=x,
        y=y,
        z=z,
        service_start=service_start,
        sortie_start=sortie_start,
        sortie_return=sortie_return,
        sortie_end=sortie_end,
        visit_order=visit_order,
        forbidden_patterns=forbidden_patterns,
        forbidden_task_sets=forbidden_task_sets_normalized,
        required_task_set=required_task_set_normalized,
        required_task_count=required_task_count_normalized,
        required_active_sortie_count=required_active_sortie_count_normalized,
        journey_active=journey_active,
        zero_fill_integers=bool(mip_start_zero_fill_integers),
        inactive_tail_time_upper_bound=float(sortie_start_upper_bound)
        if bool(mip_start_inactive_tail_time)
        else None,
        inactive_tail_time_mode=str(mip_start_inactive_tail_time_mode),
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
    pricing_model_reduced_cost = (
        best_rc
        if negative_feasibility_zero_objective_enabled and best_rc is not None
        else model_objective
    )
    negative_found = bool(best_rc is not None and float(best_rc) < -abs(float(negative_eps)))
    dual_bound_can_certify_no_negative = bool(
        bound is not None
        and float(bound) >= -abs(float(negative_eps))
        and not negative_found
        and not negative_feasibility_search
        and not negative_feasibility_zero_objective_enabled
    )
    restricted_by_required_task_set = required_task_set_normalized is not None
    restricted_by_required_task_count = required_task_count_normalized is not None
    restricted_by_required_active_sortie_count = required_active_sortie_count_normalized is not None
    restricted_by_forbidden_patterns = (
        forbidden_pattern_count > 0
        or forbidden_task_set_count > 0
        or restricted_by_required_task_set
        or restricted_by_required_task_count
        or restricted_by_required_active_sortie_count
    )
    required_task_set_region_can_certify_no_negative = bool(
        restricted_by_required_task_set
        and (
            (optimal and not negative_found and best_rc is not None)
            or infeasible
            or dual_bound_can_certify_no_negative
        )
    )
    required_task_count_region_can_certify_no_negative = bool(
        restricted_by_required_task_count
        and (
            (optimal and not negative_found and best_rc is not None)
            or infeasible
            or dual_bound_can_certify_no_negative
        )
    )
    required_active_sortie_count_region_can_certify_no_negative = bool(
        restricted_by_required_active_sortie_count
        and (
            (optimal and not negative_found and best_rc is not None)
            or infeasible
            or dual_bound_can_certify_no_negative
        )
    )
    objective_bound_cutoff_can_certify_no_negative = bool(
        objective_bound_no_negative_cutoff_enabled
        and infeasible
        and not negative_found
    )
    can_certify_no_negative = bool(
        (
            (optimal and not negative_found and best_rc is not None and not negative_feasibility_search)
            or infeasible
            or dual_bound_can_certify_no_negative
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
            "COMPACT_HIGHS_PRICING_OBJECTIVE_BOUND_NO_NEGATIVE"
            if objective_bound_cutoff_can_certify_no_negative
            and not restricted_by_forbidden_patterns
            else "COMPACT_HIGHS_PRICING_RESTRICTED_OBJECTIVE_BOUND_NO_NEGATIVE"
            if objective_bound_cutoff_can_certify_no_negative
            and restricted_by_forbidden_patterns
            else
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
                "RESTRICTED_OBJECTIVE_BOUND_NO_NEGATIVE"
                if restricted_by_forbidden_patterns
                else "EXACT_OBJECTIVE_BOUND_NO_NEGATIVE"
            )
            if objective_bound_cutoff_can_certify_no_negative
            else
            (
                "RESTRICTED_NEGATIVE_FEASIBILITY_INFEASIBLE"
                if restricted_by_forbidden_patterns
                else "EXACT_NEGATIVE_FEASIBILITY_INFEASIBLE"
            )
            if infeasible and negative_feasibility_search
            else "REQUIRED_TASK_SET_PRICING_INFEASIBLE"
            if infeasible and restricted_by_required_task_set
            else "REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE"
            if infeasible and restricted_by_required_active_sortie_count
            else "REQUIRED_TASK_COUNT_PRICING_INFEASIBLE"
            if infeasible and restricted_by_required_task_count
            else "RESTRICTED_PRICING_INFEASIBLE"
            if infeasible and restricted_by_forbidden_patterns
            else "EXACT_PRICING_INFEASIBLE_NO_COLUMNS"
            if infeasible
            else "EXACT_PRICING_OPTIMAL"
            if optimal and not restricted_by_forbidden_patterns
            else "REQUIRED_TASK_SET_PRICING_OPTIMAL"
            if optimal and restricted_by_required_task_set
            else "REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_OPTIMAL"
            if optimal and restricted_by_required_active_sortie_count
            else "REQUIRED_TASK_COUNT_PRICING_OPTIMAL"
            if optimal and restricted_by_required_task_count
            else "RESTRICTED_PRICING_OPTIMAL"
            if optimal
            else "NOT_SOLVED"
        ),
        "pricing_state": pricing_state,
        "task_count": len(tasks),
        "pricing_model_task_count": len(model_tasks),
        "required_task_set_model_reduction_enabled": bool(required_task_set_normalized is not None),
        "required_task_set_model_task_count": len(model_tasks)
        if required_task_set_normalized is not None
        else None,
        "required_task_set_model_task_reduction_count": int(len(tasks) - len(model_tasks))
        if required_task_set_normalized is not None
        else 0,
        "solver_backend": "HiGHS compact single-journey pricing MILP",
        "pricing_complete_by_compact_milp": bool(
            (optimal or infeasible or dual_bound_can_certify_no_negative)
            and not restricted_by_forbidden_patterns
        ),
        "pricing_complete_by_dual_bound": bool(dual_bound_can_certify_no_negative),
        "dual_bound_can_certify_no_negative": bool(dual_bound_can_certify_no_negative),
        "pricing_complete_for_all_tasks": bool(
            (optimal or infeasible or dual_bound_can_certify_no_negative)
            and not restricted_by_forbidden_patterns
        ),
        "pricing_complete_for_all_task_subsets": bool(
            (optimal or infeasible or dual_bound_can_certify_no_negative)
            and not restricted_by_forbidden_patterns
        ),
        "pricing_complete_for_required_task_set": bool(
            (optimal or infeasible or dual_bound_can_certify_no_negative)
            and restricted_by_required_task_set
        ),
        "pricing_complete_for_required_task_count": bool(
            (optimal or infeasible or dual_bound_can_certify_no_negative)
            and restricted_by_required_task_count
        ),
        "pricing_complete_for_required_active_sortie_count": bool(
            (optimal or infeasible or dual_bound_can_certify_no_negative)
            and restricted_by_required_active_sortie_count
        ),
        "required_task_set_enabled": bool(restricted_by_required_task_set),
        "required_task_set": list(required_task_set_normalized or tuple()),
        "required_task_set_count": 0 if required_task_set_normalized is None else len(required_task_set_normalized),
        "required_task_set_region_can_certify_no_negative": required_task_set_region_can_certify_no_negative,
        "required_task_set_can_certify_full_space": False,
        "required_task_set_infeasible_by_feasible_task_count": False,
        "required_task_set_infeasible_by_slot_capacity": False,
        "required_task_set_infeasible_by_slot_sequence_capacity": False,
        "required_task_set_infeasible_by_slot_matching": False,
        "required_task_count_enabled": bool(restricted_by_required_task_count),
        "required_task_count": required_task_count_normalized,
        "required_task_count_region_can_certify_no_negative": required_task_count_region_can_certify_no_negative,
        "required_task_count_can_certify_full_space": False,
        "required_task_count_feasible_task_count": int(task_count_feasible_task_count),
        "required_task_count_slot_capacity_task_upper_bound": int(task_count_slot_capacity_upper_bound),
        "required_task_count_slot_sequence_capacity_upper_bound": int(
            task_count_slot_sequence_capacity_upper_bound
        ),
        "required_task_count_slot_matching_capacity_upper_bound": int(
            task_count_slot_matching_capacity_upper_bound
        ),
        "required_task_count_pair_conflict_capacity_upper_bound": (
            None
            if task_count_pair_conflict_capacity_upper_bound is None
            else int(task_count_pair_conflict_capacity_upper_bound)
        ),
        "required_task_count_min_active_sorties": int(required_task_count_min_active_sorties),
        "required_task_count_active_sortie_lb_count": int(required_task_count_active_sortie_lb_count_total),
        "required_task_count_infeasible_by_feasible_task_count": required_task_count_infeasible_by_feasible_task_count,
        "required_task_count_infeasible_by_slot_capacity": required_task_count_infeasible_by_slot_capacity,
        "required_task_count_infeasible_by_slot_sequence_capacity": bool(
            required_task_count_infeasible_by_slot_sequence_capacity
        ),
        "required_task_count_infeasible_by_slot_matching": bool(
            required_task_count_infeasible_by_slot_matching
        ),
        "required_task_count_infeasible_by_pair_conflict_capacity": bool(
            required_task_count_infeasible_by_pair_conflict_capacity
        ),
        "required_task_count_certified_by_dual_task_slot_lower_bound": bool(
            required_task_count_certified_by_dual_task_slot_lb
        ),
        "required_task_count_infeasible_by_dual_task_slot_lower_bound": bool(
            required_task_count_infeasible_by_dual_task_slot_lb
        ),
        "dual_task_slot_lower_bound_enabled": bool(dual_task_slot_lb_result.get("enabled")),
        "dual_task_slot_lower_bound_applicable": bool(dual_task_slot_lb_result.get("applicable")),
        "dual_task_slot_lower_bound_optimal": bool(dual_task_slot_lb_result.get("optimal")),
        "dual_task_slot_lower_bound_status": str(dual_task_slot_lb_result.get("status") or ""),
        "dual_task_slot_lower_bound_value": (
            None if dual_task_slot_lb_value is None else round(float(dual_task_slot_lb_value), 9)
        ),
        "dual_task_slot_lower_bound_region_infeasible": bool(
            dual_task_slot_lb_result.get("region_infeasible")
        ),
        "dual_task_slot_lower_bound_constant": dual_task_slot_lb_result.get("constant_lower_bound"),
        "dual_task_slot_lower_bound_depot_outbound_arc": dual_task_slot_lb_result.get(
            "depot_outbound_arc_lower_bound"
        ),
        "dual_task_slot_lower_bound_depot_return_arc": dual_task_slot_lb_result.get(
            "depot_return_arc_lower_bound"
        ),
        "dual_task_slot_lower_bound_intertask_arc": dual_task_slot_lb_result.get("intertask_arc_lower_bound"),
        "dual_task_slot_lower_bound_route_arc_mode": dual_task_slot_lb_result.get(
            "route_arc_lower_bound_mode"
        ),
        "dual_task_slot_lower_bound_route_arc_value": dual_task_slot_lb_result.get(
            "route_arc_lower_bound_value"
        ),
        "dual_task_slot_lower_bound_route_arc_row_count": int(
            dual_task_slot_lb_result.get("route_arc_lower_bound_row_count") or 0
        ),
        "dual_task_slot_lower_bound_route_arc_global_constant": dual_task_slot_lb_result.get(
            "route_arc_global_constant_lower_bound"
        ),
        "dual_task_slot_lower_bound_route_arc_slot_constant": dual_task_slot_lb_result.get(
            "route_arc_slot_constant_lower_bound"
        ),
        "dual_task_slot_lower_bound_route_arc_constant": dual_task_slot_lb_result.get(
            "route_arc_constant_lower_bound"
        ),
        "dual_task_slot_lower_bound_route_arc_slot_outbound_sum": dual_task_slot_lb_result.get(
            "route_arc_slot_outbound_lower_bound_sum"
        ),
        "dual_task_slot_lower_bound_route_arc_slot_return_sum": dual_task_slot_lb_result.get(
            "route_arc_slot_return_lower_bound_sum"
        ),
        "dual_task_slot_lower_bound_single_task_route_arc_bound_row_count": int(
            dual_task_slot_lb_result.get("single_task_route_arc_bound_row_count") or 0
        ),
        "dual_task_slot_lower_bound_single_task_route_arc_bound_min": dual_task_slot_lb_result.get(
            "single_task_route_arc_bound_min"
        ),
        "dual_task_slot_lower_bound_single_task_route_arc_bound_max": dual_task_slot_lb_result.get(
            "single_task_route_arc_bound_max"
        ),
        "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_var_count": int(
            dual_task_slot_lb_result.get("one_pair_rest_single_route_arc_var_count") or 0
        ),
        "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_row_count": int(
            dual_task_slot_lb_result.get("one_pair_rest_single_route_arc_row_count") or 0
        ),
        "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_pair_count": int(
            dual_task_slot_lb_result.get("one_pair_rest_single_route_arc_pair_count") or 0
        ),
        "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_separation_row_count": int(
            dual_task_slot_lb_result.get("one_pair_rest_single_route_arc_separation_row_count") or 0
        ),
        "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_separation_iteration_count": int(
            dual_task_slot_lb_result.get("one_pair_rest_single_route_arc_separation_iteration_count") or 0
        ),
        "dual_task_slot_lower_bound_pair_route_arc_bound_row_count": int(
            dual_task_slot_lb_result.get("pair_route_arc_bound_row_count") or 0
        ),
        "dual_task_slot_lower_bound_pair_route_arc_bound_min": dual_task_slot_lb_result.get(
            "pair_route_arc_bound_min"
        ),
        "dual_task_slot_lower_bound_pair_route_arc_bound_max": dual_task_slot_lb_result.get(
            "pair_route_arc_bound_max"
        ),
        "dual_task_slot_lower_bound_triple_route_arc_bound_row_count": int(
            dual_task_slot_lb_result.get("triple_route_arc_bound_row_count") or 0
        ),
        "dual_task_slot_lower_bound_triple_route_arc_bound_min": dual_task_slot_lb_result.get(
            "triple_route_arc_bound_min"
        ),
        "dual_task_slot_lower_bound_triple_route_arc_bound_max": dual_task_slot_lb_result.get(
            "triple_route_arc_bound_max"
        ),
        "dual_task_slot_lower_bound_pair_completion_lift_var_count": int(
            dual_task_slot_lb_result.get("pair_completion_lift_var_count") or 0
        ),
        "dual_task_slot_lower_bound_pair_completion_lift_row_count": int(
            dual_task_slot_lb_result.get("pair_completion_lift_row_count") or 0
        ),
        "dual_task_slot_lower_bound_pair_completion_lift_min": dual_task_slot_lb_result.get(
            "pair_completion_lift_min"
        ),
        "dual_task_slot_lower_bound_pair_completion_lift_max": dual_task_slot_lb_result.get(
            "pair_completion_lift_max"
        ),
        "dual_task_slot_lower_bound_cross_slot_completion_lift_var_count": int(
            dual_task_slot_lb_result.get("cross_slot_completion_lift_var_count") or 0
        ),
        "dual_task_slot_lower_bound_cross_slot_completion_lift_row_count": int(
            dual_task_slot_lb_result.get("cross_slot_completion_lift_row_count") or 0
        ),
        "dual_task_slot_lower_bound_cross_slot_pair_completion_separation_row_count": int(
            dual_task_slot_lb_result.get("cross_slot_pair_completion_separation_row_count") or 0
        ),
        "dual_task_slot_lower_bound_cross_slot_completion_lift_min": dual_task_slot_lb_result.get(
            "cross_slot_completion_lift_min"
        ),
        "dual_task_slot_lower_bound_cross_slot_completion_lift_max": dual_task_slot_lb_result.get(
            "cross_slot_completion_lift_max"
        ),
        "dual_task_slot_lower_bound_selected_task_set": list(
            dual_task_slot_lb_result.get("selected_task_set") or []
        ),
        "dual_task_slot_lower_bound_selected_slot_task_sets": dict(
            dual_task_slot_lb_result.get("selected_slot_task_sets") or {}
        ),
        "dual_task_slot_lower_bound_wall_time_sec": float(
            dual_task_slot_lb_result.get("wall_time_sec") or 0.0
        ),
        "dual_task_slot_lower_bound_variable_count": int(
            dual_task_slot_lb_result.get("variable_count") or 0
        ),
        "dual_task_slot_lower_bound_constraint_count": int(
            dual_task_slot_lb_result.get("constraint_count") or 0
        ),
        "dual_task_slot_lower_bound_pair_conflict_row_count": int(
            dual_task_slot_lb_result.get("pair_conflict_row_count") or 0
        ),
        "dual_task_slot_lower_bound_hyperedge_conflict_row_count": int(
            dual_task_slot_lb_result.get("hyperedge_conflict_row_count") or 0
        ),
        "dual_task_slot_full_space_lower_bound_enabled": bool(
            dual_task_slot_full_space_lb_result.get("enabled")
        ),
        "dual_task_slot_full_space_lower_bound_applicable": bool(
            dual_task_slot_full_space_lb_result.get("applicable")
        ),
        "dual_task_slot_full_space_lower_bound_early_stop_on_negative": bool(
            dual_task_slot_full_space_lb_result.get("early_stop_on_negative_bound")
        ),
        "dual_task_slot_full_space_lower_bound_early_stopped_on_negative": bool(
            dual_task_slot_full_space_lb_result.get("early_stopped_on_negative_bound")
        ),
        "dual_task_slot_full_space_lower_bound_coverage_complete": bool(
            dual_task_slot_full_space_lb_result.get("coverage_complete")
        ),
        "dual_task_slot_full_space_lower_bound_can_certify": bool(
            dual_task_slot_full_space_lb_result.get("can_certify_no_negative")
        ),
        "dual_task_slot_full_space_lower_bound_region_count": int(
            dual_task_slot_full_space_lb_result.get("region_count") or 0
        ),
        "dual_task_slot_full_space_lower_bound_optimal_region_count": int(
            dual_task_slot_full_space_lb_result.get("optimal_region_count") or 0
        ),
        "dual_task_slot_full_space_lower_bound_infeasible_region_count": int(
            dual_task_slot_full_space_lb_result.get("infeasible_region_count") or 0
        ),
        "dual_task_slot_full_space_lower_bound_unsupported_region_count": int(
            dual_task_slot_full_space_lb_result.get("unsupported_region_count") or 0
        ),
        "dual_task_slot_full_space_lower_bound_negative_region_count": int(
            dual_task_slot_full_space_lb_result.get("negative_bound_region_count") or 0
        ),
        "dual_task_slot_full_space_lower_bound_value": dual_task_slot_full_space_lb_value,
        "dual_task_slot_full_space_lower_bound_task_count": (
            dual_task_slot_full_space_lb_result.get("min_lower_bound_task_count")
        ),
        "dual_task_slot_full_space_lower_bound_active_sortie_count": (
            dual_task_slot_full_space_lb_result.get("min_lower_bound_active_sortie_count")
        ),
        "dual_task_slot_full_space_lower_bound_wall_time_sec": float(
            dual_task_slot_full_space_lb_result.get("wall_time_sec") or 0.0
        ),
        "dual_task_slot_full_space_lower_bound_status": str(
            dual_task_slot_full_space_lb_result.get("status") or ""
        ),
        "task_slot_pair_conflict_capacity_bound_enabled": bool(
            pair_conflict_capacity_result.get("enabled")
        ),
        "task_slot_pair_conflict_capacity_near_matching_cap": bool(
            pair_conflict_capacity_near_matching_cap
        ),
        "task_slot_pair_conflict_capacity_bound_requested": bool(
            pair_conflict_capacity_bound_requested
        ),
        "task_slot_pair_conflict_capacity_bound_optimal": bool(
            pair_conflict_capacity_result.get("optimal")
        ),
        "task_slot_pair_conflict_capacity_bound_status": str(
            pair_conflict_capacity_result.get("status") or ""
        ),
        "task_slot_pair_conflict_capacity_bound_wall_time_sec": float(
            pair_conflict_capacity_result.get("wall_time_sec") or 0.0
        ),
        "task_slot_pair_conflict_capacity_bound_variable_count": int(
            pair_conflict_capacity_result.get("variable_count") or 0
        ),
        "task_slot_pair_conflict_capacity_bound_constraint_count": int(
            pair_conflict_capacity_result.get("constraint_count") or 0
        ),
        "task_slot_pair_conflict_capacity_pair_count": int(
            pair_conflict_capacity_result.get("pair_conflict_count") or 0
        ),
        "task_slot_pair_conflict_capacity_row_count": int(
            pair_conflict_capacity_result.get("pair_conflict_row_count") or 0
        ),
        "task_slot_pair_conflict_capacity_hyperedge_count": int(
            pair_conflict_capacity_result.get("hyperedge_conflict_count") or 0
        ),
        "task_slot_pair_conflict_capacity_hyperedge_row_count": int(
            pair_conflict_capacity_result.get("hyperedge_conflict_row_count") or 0
        ),
        "required_active_sortie_count_enabled": bool(restricted_by_required_active_sortie_count),
        "required_active_sortie_count": required_active_sortie_count_normalized,
        "required_active_sortie_count_region_can_certify_no_negative": (
            required_active_sortie_count_region_can_certify_no_negative
        ),
        "required_active_sortie_count_can_certify_full_space": False,
        "required_active_sortie_count_min": int(required_active_sortie_count_min),
        "required_active_sortie_count_max": int(required_active_sortie_count_max),
        "required_active_sortie_count_capacity_min": (
            None
            if required_active_sortie_count_capacity_min is None
            else int(required_active_sortie_count_capacity_min)
        ),
        "required_active_sortie_count_expected_counts": required_active_sortie_count_expected_counts,
        "required_active_sortie_count_infeasible": bool(required_active_sortie_count_infeasible),
        "required_active_sortie_count_infeasible_by_empty_slot": bool(
            required_active_sortie_count_infeasible_by_empty_slot
        ),
        "required_active_sortie_count_infeasible_by_capacity_min": bool(
            required_active_sortie_count_infeasible_by_capacity_min
        ),
        "required_active_sortie_count_slots_fixed": bool(required_active_sortie_count_slots_fixed),
        "required_active_sortie_count_fixed_slot_count": (
            int(sortie_slots) if required_active_sortie_count_slots_fixed else 0
        ),
        "best_reduced_cost": None if best_rc is None else round(float(best_rc), 9),
        "model_objective": None if model_objective is None else round(float(model_objective), 9),
        "pricing_model_reduced_cost": None
        if pricing_model_reduced_cost is None
        else round(float(pricing_model_reduced_cost), 9),
        "manual_best_reduced_cost": None if manual_rc is None else round(float(manual_rc), 9),
        "pricing_best_reduced_cost": None if best_rc is None else round(float(best_rc), 9),
        "dual_bound": None if bound is None else round(float(bound), 9),
        "bound": None if bound is None else round(float(bound), 9),
        "gap": None if gap is None else round(float(gap), 9),
        "highs_option_overrides": dict(highs_option_overrides),
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
        "single_journey_mip_start": mip_start_payload,
        "single_journey_mip_start_enabled": bool(mip_start_payload.get("enabled")),
        "single_journey_mip_start_status": str(mip_start_payload.get("status") or ""),
        "single_journey_mip_start_source": str(mip_start_payload.get("source") or ""),
        "single_journey_mip_start_entry_count": int(mip_start_payload.get("entry_count") or 0),
        "single_journey_mip_start_zero_fill_integers": bool(
            mip_start_payload.get("zero_fill_integers")
        ),
        "single_journey_mip_start_zero_fill_integer_entry_count": int(
            mip_start_payload.get("zero_fill_integer_entry_count") or 0
        ),
        "single_journey_mip_start_inactive_tail_time_entry_count": int(
            mip_start_payload.get("inactive_tail_time_entry_count") or 0
        ),
        "single_journey_mip_start_inactive_tail_time_mode": str(
            mip_start_payload.get("inactive_tail_time_mode") or ""
        ),
        "single_journey_mip_start_sort_indices": bool(
            mip_start_payload.get("sort_indices", True)
        ),
        "single_journey_mip_start_sortie_count": int(mip_start_payload.get("sortie_count") or 0),
        "single_journey_mip_start_task_count": int(mip_start_payload.get("task_count") or 0),
        "single_journey_mip_start_objective": mip_start_payload.get("objective"),
        "single_journey_mip_start_reduced_cost": mip_start_payload.get("reduced_cost"),
        "model_status_code": int(status),
        "model_status_name": status_name,
        "solver_info": solver_info,
        "flow_connectivity_enabled": bool(flow_connectivity),
        "mtz_connectivity_enabled": bool(mtz_connectivity),
        "mtz_connectivity_effective": bool(mtz_connectivity_effective),
        "single_task_per_active_sortie_mtz_disabled": bool(
            single_task_per_active_sortie_arc_pruning_enabled and mtz_connectivity
        ),
        "fixed_active_sortie_redundant_constraint_skipped_count": int(
            fixed_active_sortie_redundant_constraint_skipped_count
        ),
        "single_task_per_active_sortie_slot_visit_eq_count": int(
            single_task_per_active_sortie_slot_visit_eq_count
        ),
        "single_task_per_active_sortie_y_z_link_skipped_count": int(
            single_task_per_active_sortie_y_z_link_skipped_count
        ),
        "mtz_endpoint_order_cuts_enabled": bool(mtz_endpoint_order_cuts_effective),
        "mtz_endpoint_order_cut_count": int(mtz_endpoint_order_cut_count_total),
        "pair_adjacency_cuts_enabled": bool(pair_adjacency_cuts),
        "pair_adjacency_cut_count": int(pair_adjacency_cut_count_total),
        "sortie_slot_position_bounds_enabled": bool(sortie_slot_position_bounds),
        "sortie_slot_position_bound_count": int(sortie_slot_position_bound_count_total),
        "sortie_slot_latest_start_upper_bound": round(float(latest_sortie_start_upper_bound), 9),
        "sortie_start_upper_bound": round(float(sortie_start_upper_bound), 9),
        "tight_time_arc_big_m_enabled": bool(tight_time_arc_big_m_enabled),
        "active_time_z_bounds_enabled": bool(active_time_z_bounds_enabled),
        "tight_time_arc_big_m_depot_arc_count": int(
            tight_time_arc_big_m_depot_arc_count_total
        ),
        "tight_time_arc_big_m_active_time_bound_count": int(
            tight_time_arc_big_m_active_time_bound_count_total
        ),
        "tight_time_arc_big_m_max_reduction": round(
            float(tight_time_arc_big_m_max_reduction),
            9,
        ),
        "tight_conditional_sequence_big_m_enabled": bool(
            tight_conditional_sequence_big_m_count_total > 0
        ),
        "tight_conditional_sequence_big_m_count": int(
            tight_conditional_sequence_big_m_count_total
        ),
        "tight_conditional_sequence_big_m_max_reduction": round(
            float(tight_conditional_sequence_big_m_max_reduction),
            9,
        ),
        "slot_service_start_y_lower_bound_enabled": bool(slot_service_start_y_lower_bound),
        "slot_service_start_y_lower_bound_count": int(
            slot_service_start_y_lower_bound_count
        ),
        "slot_service_start_y_lower_bound_max_lift": round(
            float(slot_service_start_y_lower_bound_max_lift),
            9,
        ),
        "slot_service_start_y_lower_bound_min": (
            None
            if not slot_service_start_y_lower_bound_values
            else round(float(min(slot_service_start_y_lower_bound_values)), 9)
        ),
        "slot_service_start_y_lower_bound_max": (
            None
            if not slot_service_start_y_lower_bound_values
            else round(float(max(slot_service_start_y_lower_bound_values)), 9)
        ),
        "service_start_depot_travel_lb_enabled": bool(service_start_depot_travel_lb),
        "service_start_depot_travel_lb_count": int(service_start_depot_travel_lb_count_total),
        "service_start_depot_travel_lb_min": (
            round(min(service_start_lb_by_task.values()), 9) if service_start_lb_by_task else None
        ),
        "service_start_depot_travel_lb_max": (
            round(max(service_start_lb_by_task.values()), 9) if service_start_lb_by_task else None
        ),
        "task_to_depot_return_travel_lb_enabled": bool(task_to_depot_return_travel_lb),
        "task_to_depot_return_travel_lb_count": int(task_to_depot_return_travel_lb_count_total),
        "task_to_depot_return_travel_lb_min": (
            round(min(task_return_lb_by_task.values()), 9) if task_return_lb_by_task else None
        ),
        "task_to_depot_return_travel_lb_max": (
            round(max(task_return_lb_by_task.values()), 9) if task_return_lb_by_task else None
        ),
        "pair_route_duration_lb_enabled": bool(pair_route_duration_lb),
        "pair_route_duration_lb_count": int(pair_route_duration_lb_count_total),
        "pair_route_duration_lb_min": (
            round(min(pair_route_duration_lb_by_pair.values()), 9)
            if pair_route_duration_lb_by_pair
            else None
        ),
        "pair_route_duration_lb_max": (
            round(max(pair_route_duration_lb_by_pair.values()), 9)
            if pair_route_duration_lb_by_pair
            else None
        ),
        "pair_weighted_completion_lb_enabled": bool(pair_weighted_completion_lb),
        "pair_weighted_completion_lb_count": int(pair_weighted_completion_lb_count_total),
        "pair_weighted_completion_lb_min": (
            round(min(pair_weighted_completion_lb_by_pair.values()), 9)
            if pair_weighted_completion_lb_by_pair
            else None
        ),
        "pair_weighted_completion_lb_max": (
            round(max(pair_weighted_completion_lb_by_pair.values()), 9)
            if pair_weighted_completion_lb_by_pair
            else None
        ),
        "demand_cover_cut_enabled": bool(demand_cover_cut),
        "demand_cover_cut_count": int(demand_cover_cut_count_total),
        "demand_cover_subset_count": int(len(demand_cover_by_subset)),
        "demand_cover_max_size": 5 if demand_cover_cut else 0,
        "demand_cover_min_demand": (
            round(min(demand_cover_by_subset.values()), 9) if demand_cover_by_subset else None
        ),
        "demand_cover_max_demand": (
            round(max(demand_cover_by_subset.values()), 9) if demand_cover_by_subset else None
        ),
        "single_task_energy_lb_enabled": bool(single_task_energy_lb),
        "single_task_energy_lb_count": int(single_task_energy_lb_count_total),
        "single_task_energy_lb_min": (
            round(min(single_task_energy_lb_by_task.values()), 9) if single_task_energy_lb_by_task else None
        ),
        "single_task_energy_lb_max": (
            round(max(single_task_energy_lb_by_task.values()), 9) if single_task_energy_lb_by_task else None
        ),
        "single_task_shadow_lb_enabled": bool(single_task_shadow_lb),
        "single_task_shadow_lb_count": int(single_task_shadow_lb_count_total),
        "single_task_shadow_lb_min": (
            round(min(single_task_shadow_lb_by_task.values()), 9) if single_task_shadow_lb_by_task else None
        ),
        "single_task_shadow_lb_max": (
            round(max(single_task_shadow_lb_by_task.values()), 9) if single_task_shadow_lb_by_task else None
        ),
        "pair_energy_lb_enabled": bool(pair_energy_lb),
        "pair_energy_lb_count": int(pair_energy_lb_count_total),
        "pair_energy_lb_min": (
            round(min(pair_energy_lb_by_pair.values()), 9) if pair_energy_lb_by_pair else None
        ),
        "pair_energy_lb_max": (
            round(max(pair_energy_lb_by_pair.values()), 9) if pair_energy_lb_by_pair else None
        ),
        "pair_energy_lb_exceeds_limit_count": int(
            sum(1 for value in pair_energy_lb_by_pair.values() if float(value) > float(data.energy_limit) + 1.0e-9)
        ),
        "pair_shadow_lb_enabled": bool(pair_shadow_lb),
        "pair_shadow_lb_count": int(pair_shadow_lb_count_total),
        "pair_shadow_lb_min": (
            round(min(pair_shadow_lb_by_pair.values()), 9) if pair_shadow_lb_by_pair else None
        ),
        "pair_shadow_lb_max": (
            round(max(pair_shadow_lb_by_pair.values()), 9) if pair_shadow_lb_by_pair else None
        ),
        "pair_shadow_lb_exceeds_limit_count": int(
            sum(
                1
                for value in pair_shadow_lb_by_pair.values()
                if float(value) > float(data.max_shadow_exposure_per_sortie) + 1.0e-9
            )
        ),
        "pair_energy_infeasible_cut_enabled": bool(pair_energy_infeasible_cut),
        "pair_energy_infeasible_cut_count": int(pair_energy_infeasible_cut_count_total),
        "pair_energy_infeasible_pair_count": int(
            sum(1 for value in pair_energy_lb_by_pair.values() if float(value) > float(data.energy_limit) + 1.0e-9)
        ),
        "pair_time_window_infeasible_cut_enabled": bool(pair_time_window_infeasible_cut),
        "pair_time_window_infeasible_cut_count": int(pair_time_window_infeasible_cut_count_total),
        "pair_time_window_infeasible_pair_count": int(len(pair_time_window_infeasible_by_pair)),
        "pair_time_window_infeasible_margin_min": (
            round(min(pair_time_window_infeasible_by_pair.values()), 9)
            if pair_time_window_infeasible_by_pair
            else None
        ),
        "pair_time_window_infeasible_margin_max": (
            round(max(pair_time_window_infeasible_by_pair.values()), 9)
            if pair_time_window_infeasible_by_pair
            else None
        ),
        "pair_time_window_precedence_cut_enabled": bool(
            pair_time_window_precedence_cut_effective
        ),
        "pair_time_window_precedence_cut_count": int(pair_time_window_precedence_cut_count_total),
        "pair_time_window_precedence_pair_count": int(len(pair_time_window_precedence_by_pair)),
        "pair_time_window_precedence_margin_min": (
            round(min(pair_time_window_precedence_by_pair.values()), 9)
            if pair_time_window_precedence_by_pair
            else None
        ),
        "pair_time_window_precedence_margin_max": (
            round(max(pair_time_window_precedence_by_pair.values()), 9)
            if pair_time_window_precedence_by_pair
            else None
        ),
        "triple_time_window_infeasible_cut_enabled": bool(triple_time_window_infeasible_cut),
        "triple_time_window_infeasible_cut_count": int(triple_time_window_infeasible_cut_count_total),
        "triple_time_window_infeasible_triple_count": int(len(triple_time_window_infeasible_by_triple)),
        "triple_time_window_infeasible_margin_min": (
            round(min(triple_time_window_infeasible_by_triple.values()), 9)
            if triple_time_window_infeasible_by_triple
            else None
        ),
        "triple_time_window_infeasible_margin_max": (
            round(max(triple_time_window_infeasible_by_triple.values()), 9)
            if triple_time_window_infeasible_by_triple
            else None
        ),
        "quad_time_window_infeasible_cut_enabled": bool(quad_time_window_infeasible_cut),
        "quad_time_window_infeasible_cut_count": int(quad_time_window_infeasible_cut_count_total),
        "quad_time_window_infeasible_quad_count": int(len(quad_time_window_infeasible_by_quad)),
        "quad_time_window_infeasible_margin_min": (
            round(min(quad_time_window_infeasible_by_quad.values()), 9)
            if quad_time_window_infeasible_by_quad
            else None
        ),
        "quad_time_window_infeasible_margin_max": (
            round(max(quad_time_window_infeasible_by_quad.values()), 9)
            if quad_time_window_infeasible_by_quad
            else None
        ),
        "pair_shadow_infeasible_cut_enabled": bool(pair_shadow_infeasible_cut),
        "pair_shadow_infeasible_cut_count": int(pair_shadow_infeasible_cut_count_total),
        "pair_shadow_infeasible_pair_count": int(
            sum(
                1
                for value in pair_shadow_lb_by_pair.values()
                if float(value) > float(data.max_shadow_exposure_per_sortie) + 1.0e-9
            )
        ),
        "pair_shadow_infeasible_lb_min": (
            round(min(pair_shadow_lb_by_pair.values()), 9) if pair_shadow_lb_by_pair else None
        ),
        "pair_shadow_infeasible_lb_max": (
            round(max(pair_shadow_lb_by_pair.values()), 9) if pair_shadow_lb_by_pair else None
        ),
        "triple_shadow_infeasible_cut_enabled": bool(triple_shadow_infeasible_cut),
        "triple_shadow_infeasible_cut_count": int(triple_shadow_infeasible_cut_count_total),
        "triple_shadow_infeasible_triple_count": int(len(triple_shadow_infeasible_lb_by_triple)),
        "triple_shadow_infeasible_lb_min": (
            round(min(triple_shadow_infeasible_lb_by_triple.values()), 9)
            if triple_shadow_infeasible_lb_by_triple
            else None
        ),
        "triple_shadow_infeasible_lb_max": (
            round(max(triple_shadow_infeasible_lb_by_triple.values()), 9)
            if triple_shadow_infeasible_lb_by_triple
            else None
        ),
        "triple_energy_infeasible_cut_enabled": bool(triple_energy_infeasible_cut),
        "triple_energy_infeasible_cut_count": int(triple_energy_infeasible_cut_count_total),
        "triple_energy_infeasible_triple_count": int(len(triple_energy_infeasible_lb_by_triple)),
        "triple_energy_infeasible_lb_min": (
            round(min(triple_energy_infeasible_lb_by_triple.values()), 9)
            if triple_energy_infeasible_lb_by_triple
            else None
        ),
        "triple_energy_infeasible_lb_max": (
            round(max(triple_energy_infeasible_lb_by_triple.values()), 9)
            if triple_energy_infeasible_lb_by_triple
            else None
        ),
        "negative_feasibility_search_enabled": bool(negative_feasibility_search),
        "negative_feasibility_zero_objective_enabled": bool(
            negative_feasibility_zero_objective_enabled
        ),
        "objective_bound_no_negative_cutoff_enabled": bool(
            objective_bound_no_negative_cutoff_enabled
        ),
        "objective_bound_no_negative_cutoff_value": (
            None
            if objective_bound_no_negative_cutoff_value is None
            else round(float(objective_bound_no_negative_cutoff_value), 9)
        ),
        "objective_bound_no_negative_cutoff_can_certify": bool(
            objective_bound_cutoff_can_certify_no_negative
        ),
        "zero_capacity_slot_truncation_enabled": bool(zero_capacity_slot_truncation),
        "zero_capacity_slot_truncation_original_slot_count": int(
            zero_capacity_slot_truncation_original_slot_count
        ),
        "zero_capacity_slot_truncation_effective_slot_count": int(
            zero_capacity_slot_truncation_effective_slot_count
        ),
        "zero_capacity_slot_truncation_trimmed_slot_count": int(
            zero_capacity_slot_truncation_trimmed_slot_count
        ),
        "zero_capacity_slot_truncation_first_zero_slot": (
            None
            if zero_capacity_slot_truncation_first_zero_slot is None
            else int(zero_capacity_slot_truncation_first_zero_slot)
        ),
        "slot_sequence_capacity_live_bound_enabled": bool(slot_sequence_capacity_live_bound),
        "slot_sequence_capacity_live_bound_by_slot": [
            int(slot_sequence_capacity_live_bound_by_slot.get(slot, int(data.max_tasks_per_trip)))
            for slot in range(sortie_slots)
        ],
        "slot_sequence_capacity_live_bound_tightened_slot_count": int(
            slot_sequence_capacity_live_bound_tightened_slot_count
        ),
        "tight_service_start_bounds_enabled": bool(tight_service_start_bounds),
        "tight_service_start_bound_count": int(tight_service_start_bound_count),
        "tight_service_start_bound_min": (
            round(min(tight_service_start_bound_values), 9)
            if tight_service_start_bound_values
            else None
        ),
        "tight_service_start_bound_max": (
            round(max(tight_service_start_bound_values), 9)
            if tight_service_start_bound_values
            else None
        ),
        "forbidden_arc_pattern_count": int(forbidden_pattern_count),
        "forbidden_arc_patterns_can_certify_full_space": bool(forbidden_pattern_count == 0),
        "forbidden_task_set_count": int(forbidden_task_set_count),
        "forbidden_task_set_skipped_by_required_task_count": int(
            forbidden_task_set_skipped_by_required_task_count
        ),
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
        "sortie_slot_min_sortie_energy_lower_bound": slot_bound["min_sortie_energy_lower_bound"],
        "sortie_slot_min_energy_recharge_duration_lower_bound": (
            slot_bound["min_energy_recharge_duration_lower_bound"]
        ),
        "slot_task_time_pruning_enabled": bool(slot_task_time_pruning),
        "slot_task_time_feasible_assignment_count": int(slot_task_time_feasible_assignment_count),
        "slot_task_time_pruned_assignment_count": int(slot_task_time_pruned_assignment_count),
        "slot_task_time_pruned_due_count": int(slot_task_time_pruned_due_count),
        "slot_task_time_pruned_horizon_count": int(slot_task_time_pruned_horizon_count),
        "slot_task_time_total_assignment_count": int(len(model_tasks) * sortie_slots),
        "slot_task_time_original_total_assignment_count": int(len(tasks) * sortie_slots),
        "slot_task_model_assignment_count": int(slot_task_model_assignment_count),
        "slot_arc_support_pruning_enabled": bool(slot_arc_support_pruning),
        "slot_arc_support_feasible_assignment_count": int(slot_task_model_assignment_count),
        "slot_arc_support_pruned_assignment_count": int(slot_arc_support_pruned_assignment_count),
        "slot_arc_support_pruned_unreachable_count": int(
            slot_arc_support_pruned_unreachable_count
        ),
        "slot_arc_support_pruned_no_return_count": int(slot_arc_support_pruned_no_return_count),
        "slot_arc_support_pruned_option_count": int(slot_arc_support_pruned_option_count),
        "slot_task_sequence_capacity_by_slot": list(
            slot_sequence_capacity_bounds["slot_sequence_capacity_by_slot"]
        ),
        "slot_task_sequence_capacity_upper_bound": int(
            slot_sequence_capacity_bounds["slot_sequence_capacity_upper_bound"]
        ),
        "slot_task_sequence_capacity_limited_slot_count": int(
            slot_sequence_capacity_bounds["slot_sequence_capacity_limited_slot_count"]
        ),
        "slot_task_sequence_capacity_empty_slot_count": int(
            slot_sequence_capacity_bounds["slot_sequence_capacity_empty_slot_count"]
        ),
        "slot_task_matching_capacity_upper_bound": int(
            slot_sequence_capacity_bounds["slot_matching_capacity_upper_bound"]
        ),
        "slot_arc_time_pruned_option_count": int(slot_arc_time_pruned_option_count),
        "slot_sequence_capacity_arc_pruning_enabled": bool(slot_sequence_capacity_arc_pruning),
        "slot_sequence_capacity_arc_pruned_option_count": int(
            slot_sequence_capacity_arc_pruned_option_count
        ),
        "slot_sequence_capacity_mtz_disabled_slot_count": int(
            slot_sequence_capacity_mtz_disabled_slot_count
        ),
        "single_task_per_active_sortie_arc_pruning_enabled": bool(
            single_task_per_active_sortie_arc_pruning_enabled
        ),
        "single_task_per_active_sortie_arc_pruned_option_count": int(
            single_task_per_active_sortie_arc_pruned_option_count
        ),
        "single_task_per_active_sortie_mtz_disabled": bool(
            single_task_per_active_sortie_arc_pruning_enabled and mtz_connectivity
        ),
        "mtz_connectivity_effective": bool(mtz_connectivity_effective),
        "fixed_active_sortie_redundant_constraint_skipped_count": int(
            fixed_active_sortie_redundant_constraint_skipped_count
        ),
        "single_task_per_active_sortie_slot_visit_eq_count": int(
            single_task_per_active_sortie_slot_visit_eq_count
        ),
        "single_task_per_active_sortie_y_z_link_skipped_count": int(
            single_task_per_active_sortie_y_z_link_skipped_count
        ),
        "resource_arc_pruning_enabled": bool(resource_arc_pruning),
        "resource_arc_pruned_option_count": int(resource_arc_pruned_option_count),
        "resource_arc_energy_pruned_option_count": int(resource_arc_energy_pruned_option_count),
        "resource_arc_shadow_pruned_option_count": int(resource_arc_shadow_pruned_option_count),
        "resource_arc_demand_pruned_option_count": int(resource_arc_demand_pruned_option_count),
        **pruning,
        "variable_count": int(highs.getNumCol()),
        "constraint_count": int(highs.getNumRow()),
        "wall_time_sec": round(perf_counter() - start_wall, 6),
        "note": (
            "Compact HiGHS single-journey pricing solved exactly."
            if optimal
            else (
                "Compact HiGHS single-journey objective-bound cutoff proved no journey has reduced cost <= -eps."
                if objective_bound_cutoff_can_certify_no_negative
                else
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
        "sort_indices": _compact_mip_start_sort_indices_enabled(),
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
                values[z[vehicle, slot]] = 0.0

    try:
        import numpy as np
    except Exception as exc:  # pragma: no cover - numpy is part of highspy's runtime stack locally
        payload["status"] = "NUMPY_UNAVAILABLE"
        payload["note"] = f"Could not pass sparse HiGHS solution without numpy: {type(exc).__name__}: {exc}"
        return payload

    ordered_indices = sorted(values) if payload["sort_indices"] else list(values)
    indices = np.array(ordered_indices, dtype=np.int32)
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


def _set_highs_single_journey_mip_start(
    highs,
    *,
    data: LunarIceData,
    duals: JourneyDuals,
    journey: JourneyColumn | None,
    vehicle: int,
    sortie_slots: int,
    flow_connectivity: bool,
    x: dict[tuple[int, int, str, str, str], int],
    y: dict[tuple[int, int, str], int],
    z: dict[tuple[int, int], int],
    service_start: dict[tuple[int, int, str], int],
    sortie_start: dict[tuple[int, int], int],
    sortie_return: dict[tuple[int, int], int],
    sortie_end: dict[tuple[int, int], int],
    visit_order: dict[tuple[int, int, str], int],
    forbidden_patterns: tuple[tuple[tuple[int, str, str, str], ...], ...],
    forbidden_task_sets: tuple[tuple[str, ...], ...],
    required_task_set: tuple[str, ...] | None = None,
    required_task_count: int | None = None,
    required_active_sortie_count: int | None = None,
    journey_active: int | None = None,
    zero_fill_integers: bool = False,
    inactive_tail_time_upper_bound: float | None = None,
    inactive_tail_time_mode: str = "zero",
) -> dict:
    payload = {
        "enabled": bool(journey is not None),
        "status": "DISABLED",
        "entry_count": 0,
        "zero_fill_integers": bool(zero_fill_integers),
        "zero_fill_integer_entry_count": 0,
        "inactive_tail_time_entry_count": 0,
        "inactive_tail_time_mode": str(inactive_tail_time_mode or "zero"),
        "sort_indices": _compact_mip_start_sort_indices_enabled(),
        "sortie_count": 0,
        "task_count": 0,
        "objective": None,
        "reduced_cost": None,
        "source": "column_pool_journey",
        "note": "",
    }
    if journey is None:
        payload["note"] = "No single-journey MIP start was provided."
        return payload
    payload["status"] = "NOT_SET"
    payload["sortie_count"] = len(journey.sorties)
    payload["task_count"] = len(journey.task_set)
    payload["objective"] = round(float(journey.objective), 9)
    payload["reduced_cost"] = round(float(manual_journey_reduced_cost(journey, duals)), 9)
    if flow_connectivity:
        payload["status"] = "UNSUPPORTED_FLOW_CONNECTIVITY"
        payload["note"] = "Single-journey MIP start is disabled when flow-connectivity variables are active."
        return payload
    if len(journey.sorties) > int(sortie_slots):
        payload["status"] = "TOO_MANY_SORTIES"
        payload["note"] = f"Warm-start sortie_count={len(journey.sorties)} exceeds slots={sortie_slots}."
        return payload
    if not all(sortie.feasible for sortie in journey.sorties):
        payload["status"] = "INFEASIBLE_JOURNEY"
        payload["note"] = "Warm-start journey contains an infeasible sortie."
        return payload
    valid_tasks = set(data.task_ids)
    if any(str(task_id) not in valid_tasks for task_id in journey.task_set):
        payload["status"] = "UNKNOWN_TASK"
        payload["note"] = "Warm-start journey contains a task outside the pricing instance."
        return payload
    task_set = tuple(sorted(str(task_id) for task_id in journey.task_set))
    if required_task_set is not None and task_set != tuple(required_task_set):
        payload["status"] = "MISMATCH_REQUIRED_TASK_SET"
        payload["note"] = "Warm-start journey task set does not match the required task-set region."
        return payload
    if required_task_count is not None and len(task_set) != int(required_task_count):
        payload["status"] = "MISMATCH_REQUIRED_TASK_COUNT"
        payload["note"] = "Warm-start journey task count does not match the required task-count region."
        return payload
    if required_active_sortie_count is not None and len(journey.sorties) != int(required_active_sortie_count):
        payload["status"] = "MISMATCH_REQUIRED_ACTIVE_SORTIE_COUNT"
        payload["note"] = "Warm-start journey sortie count does not match the required active-sortie-count region."
        return payload
    if task_set in set(forbidden_task_sets):
        payload["status"] = "FORBIDDEN_BY_RESTRICTED_TASK_SET"
        payload["note"] = "Warm-start journey is excluded by a restricted task-set no-good row."
        return payload
    arc_pattern = tuple(
        (int(slot), str(leg.source), str(leg.target), str(leg.path_type))
        for slot, sortie in enumerate(journey.sorties)
        for leg in sortie.legs
    )
    if arc_pattern and arc_pattern in set(forbidden_patterns):
        payload["status"] = "FORBIDDEN_BY_RESTRICTED_ARC_PATTERN"
        payload["note"] = "Warm-start journey is excluded by a restricted arc-pattern no-good row."
        return payload

    values: dict[int, float] = {}
    if zero_fill_integers:
        for col in x.values():
            values[int(col)] = 0.0
        for col in y.values():
            values[int(col)] = 0.0
        for col in z.values():
            values[int(col)] = 0.0
        if journey_active is not None:
            values[int(journey_active)] = 1.0
        payload["zero_fill_integer_entry_count"] = int(len(values))
    values[z[vehicle, 0]] = 1.0 if journey.sorties else 0.0
    previous_end = 0.0
    for slot in range(sortie_slots):
        if slot < len(journey.sorties):
            sortie = journey.sorties[slot]
            z_key = (vehicle, slot)
            values[z[z_key]] = 1.0
            values[sortie_start[z_key]] = float(sortie.start_time)
            values[sortie_return[z_key]] = float(sortie.return_time)
            values[sortie_end[z_key]] = float(sortie.end_time)
            for order, task_id in enumerate(sortie.tasks, start=1):
                task_key = (vehicle, slot, str(task_id))
                if task_key not in y or task_key not in service_start:
                    payload["status"] = "MISSING_TASK_VARIABLE"
                    payload["note"] = f"Warm-start task has no compact y/service variable: {task_key!r}."
                    return payload
                values[y[task_key]] = 1.0
                values[service_start[task_key]] = float(sortie.service_starts[str(task_id)])
                if task_key in visit_order:
                    values[visit_order[task_key]] = float(order)
            for leg in sortie.legs:
                arc_key = (vehicle, slot, str(leg.source), str(leg.target), str(leg.path_type))
                if arc_key not in x:
                    payload["status"] = "MISSING_ARC_VARIABLE"
                    payload["note"] = f"Warm-start leg has no compact x variable: {arc_key!r}."
                    return payload
                values[x[arc_key]] = 1.0
            previous_end = float(sortie.end_time)
        else:
            z_key = (vehicle, slot)
            values[z[z_key]] = 0.0
            if inactive_tail_time_upper_bound is not None:
                mode = str(inactive_tail_time_mode or "zero").strip().lower()
                bounded_previous_end = min(
                    max(0.0, float(previous_end)),
                    max(0.0, float(inactive_tail_time_upper_bound)),
                )
                if mode == "previous_end":
                    start_value = float(bounded_previous_end)
                    return_value = 0.0
                    end_value = float(bounded_previous_end)
                elif mode == "previous_end_all":
                    start_value = float(bounded_previous_end)
                    return_value = float(bounded_previous_end)
                    end_value = float(bounded_previous_end)
                else:
                    start_value = 0.0
                    return_value = 0.0
                    end_value = 0.0
                values[sortie_start[z_key]] = float(start_value)
                values[sortie_return[z_key]] = float(return_value)
                values[sortie_end[z_key]] = float(end_value)
                payload["inactive_tail_time_entry_count"] = int(
                    payload["inactive_tail_time_entry_count"]
                ) + 3

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
        payload["note"] = f"highs.setSolution failed: {type(exc).__name__}: {exc}"
        return payload

    payload["status"] = _highs_status_name(status)
    payload["entry_count"] = int(len(indices))
    payload["note"] = "Column-pool journey warm start was passed to HiGHS as a solver hint."
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
