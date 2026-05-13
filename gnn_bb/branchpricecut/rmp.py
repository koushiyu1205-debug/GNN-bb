"""中文摘要：用 SCIP 求解 vehicle-schedule RMP LP，并提供 reduced-cost 一致性审计。"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from .branching import BranchConstraint, schedule_allowed_by_branch
from .columns import ScheduleColumn
from .data import InstanceData


@dataclass
class RMPDuals:
    cover: dict[int, float]
    fleet: float
    vehicle_lb: float


@dataclass
class RMPSolution:
    status: str
    objective: float | None
    artificial_sum: float
    duals: RMPDuals | None
    schedule_values: list[tuple[ScheduleColumn, float]]
    variable_count: int
    constraint_count: int
    reduced_costs: dict[int, float]
    manual_reduced_costs: dict[int, float]
    max_reduced_cost_error: float | None
    vehicle_lower_bound_value: int

    @property
    def optimal(self) -> bool:
        return self.status == "OPTIMAL"


@dataclass
class RestrictedMasterIntegerSolution:
    status: str
    objective: float | None
    selected_columns: list[ScheduleColumn]
    variable_count: int
    constraint_count: int

    @property
    def feasible(self) -> bool:
        return self.objective is not None and bool(self.selected_columns)


def vehicle_lower_bound(data: InstanceData) -> int:
    demand = sum(data.task_value(task, "d") for task in data.tasks)
    denom = max(1.0e-9, data.sortie_limit * data.capacity)
    return max(0, min(data.vehicle_count, int(math.ceil(demand / denom - 1.0e-12))))


def schedule_objective(column: ScheduleColumn, phase: str) -> float:
    return 0.0 if phase == "phase1" else float(column.cost)


def manual_reduced_cost(column: ScheduleColumn, duals: RMPDuals, phase: str) -> float:
    return (
        schedule_objective(column, phase)
        - sum(float(duals.cover[task]) for task in column.task_set)
        - float(duals.fleet)
        - float(duals.vehicle_lb)
    )


def check_schedule_reduced_cost_consistency(solution: RMPSolution, *, tolerance: float = 1.0e-6) -> float:
    """Return max manual-vs-solver reduced-cost error and fail fast if it is too large."""

    error = 0.0 if solution.max_reduced_cost_error is None else float(solution.max_reduced_cost_error)
    if error > tolerance:
        raise AssertionError(f"schedule reduced-cost consistency failed: max_error={error:.12g}")
    return error


def _try_set_param(model, name: str, value: Any) -> None:
    try:
        model.setParam(name, value)
    except Exception:
        pass


def _status_name(status: Any) -> str:
    text = str(status).lower()
    return {
        "optimal": "OPTIMAL",
        "infeasible": "INFEASIBLE",
        "unbounded": "UNBOUNDED",
        "inforunbd": "INF_OR_UNBD",
        "timelimit": "TIME_LIMIT",
    }.get(text, text.upper())


def solve_rmp_lp(
    data: InstanceData,
    columns: list[ScheduleColumn],
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    phase: str,
    master_cover_mode: str,
    vehicle_lower_bound_cut_enabled: bool,
    rmp_params: dict[str, Any] | None = None,
    capture_duals: bool = True,
    check_reduced_costs: bool = True,
) -> RMPSolution:
    from pyscipopt import Model, quicksum

    if phase not in {"phase1", "phase2"}:
        raise ValueError(f"未知 RMP phase: {phase}")
    if master_cover_mode not in {"partitioning", "covering"}:
        raise ValueError(f"未知 master_cover_mode: {master_cover_mode}")

    model = Model(f"vehicle_schedule_rmp_{data.name}_{phase}")
    _try_set_param(model, "display/verblevel", 0)
    _try_set_param(model, "presolving/maxrounds", 0)
    _try_set_param(model, "separating/maxrounds", 0)
    _try_set_param(model, "parallel/maxnthreads", 1)
    for name, value in (rmp_params or {}).items():
        _try_set_param(model, name, value)

    variables = {}
    active_indices: list[int] = []
    for index, column in enumerate(columns):
        if not schedule_allowed_by_branch(column, branch_constraints):
            continue
        active_indices.append(index)
        variables[index] = model.addVar(
            vtype="C",
            lb=0.0,
            ub=1.0,
            obj=schedule_objective(column, phase),
            name=f"x[{index}]",
        )

    artificial = {}
    if phase == "phase1":
        for task in data.tasks:
            artificial[task] = model.addVar(vtype="C", lb=0.0, ub=1.0, obj=1.0, name=f"artificial[{task}]")

    cover_cons = {}
    for task in data.tasks:
        terms = [var for index, var in variables.items() if columns[index].covers(task)]
        if phase == "phase1":
            terms.append(artificial[task])
            cover_cons[task] = model.addCons(quicksum(terms) == 1.0, name=f"cover[{task}]")
        elif master_cover_mode == "covering":
            cover_cons[task] = model.addCons(quicksum(terms) >= 1.0, name=f"cover[{task}]")
        else:
            cover_cons[task] = model.addCons(quicksum(terms) == 1.0, name=f"cover[{task}]")

    fleet_cons = model.addCons(quicksum(variables.values()) <= float(data.vehicle_count), name="fleet")
    vehicle_lb_value = vehicle_lower_bound(data) if vehicle_lower_bound_cut_enabled else 0
    vehicle_lb_cons = None
    if vehicle_lower_bound_cut_enabled:
        vehicle_lb_cons = model.addCons(quicksum(variables.values()) >= float(vehicle_lb_value), name="vehicle_lb")

    model.optimize()
    status = _status_name(model.getStatus())

    duals = None
    if capture_duals and status == "OPTIMAL":
        transformed_cover = {task: model.getTransformedCons(cons) for task, cons in cover_cons.items()}
        transformed_fleet = model.getTransformedCons(fleet_cons)
        transformed_vehicle_lb = None if vehicle_lb_cons is None else model.getTransformedCons(vehicle_lb_cons)
        duals = RMPDuals(
            cover={task: float(model.getDualsolLinear(cons)) for task, cons in transformed_cover.items()},
            fleet=float(model.getDualsolLinear(transformed_fleet)),
            vehicle_lb=0.0 if transformed_vehicle_lb is None else float(model.getDualsolLinear(transformed_vehicle_lb)),
        )

    schedule_values = []
    reduced_costs: dict[int, float] = {}
    manual_rc: dict[int, float] = {}
    max_error = None
    if status == "OPTIMAL":
        for index, var in variables.items():
            value = float(model.getVal(var))
            if value > 1.0e-9:
                schedule_values.append((columns[index], value))
            try:
                reduced_costs[index] = float(model.getVarRedcost(var))
            except Exception:
                reduced_costs[index] = 0.0
        if duals is not None and check_reduced_costs:
            errors = []
            for index in active_indices:
                manual = manual_reduced_cost(columns[index], duals, phase)
                manual_rc[index] = manual
                if index in reduced_costs:
                    errors.append(abs(manual - reduced_costs[index]))
            max_error = max(errors) if errors else 0.0

    artificial_sum = 0.0
    if phase == "phase1" and status == "OPTIMAL":
        artificial_sum = sum(float(model.getVal(var)) for var in artificial.values())

    constraint_count = len(data.tasks) + 1 + int(vehicle_lb_cons is not None)
    return RMPSolution(
        status=status,
        objective=None if status != "OPTIMAL" else float(model.getObjVal()),
        artificial_sum=artificial_sum,
        duals=duals,
        schedule_values=schedule_values,
        variable_count=len(variables),
        constraint_count=constraint_count,
        reduced_costs=reduced_costs,
        manual_reduced_costs=manual_rc,
        max_reduced_cost_error=max_error,
        vehicle_lower_bound_value=vehicle_lb_value,
    )


def solve_restricted_master_integer(
    data: InstanceData,
    columns: list[ScheduleColumn],
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    master_cover_mode: str,
    vehicle_lower_bound_cut_enabled: bool,
    time_limit: float = 0.0,
    rmp_params: dict[str, Any] | None = None,
) -> RestrictedMasterIntegerSolution:
    from pyscipopt import Model, quicksum

    if master_cover_mode not in {"partitioning", "covering"}:
        raise ValueError(f"未知 master_cover_mode: {master_cover_mode}")

    model = Model(f"vehicle_schedule_integer_master_{data.name}")
    _try_set_param(model, "display/verblevel", 0)
    _try_set_param(model, "parallel/maxnthreads", 1)
    if time_limit and time_limit > 0.0:
        _try_set_param(model, "limits/time", float(time_limit))
    for name, value in (rmp_params or {}).items():
        _try_set_param(model, name, value)

    variables = {}
    for index, column in enumerate(columns):
        if not schedule_allowed_by_branch(column, branch_constraints):
            continue
        variables[index] = model.addVar(vtype="B", obj=float(column.cost), name=f"z[{index}]")

    cover_cons = {}
    for task in data.tasks:
        terms = [var for index, var in variables.items() if columns[index].covers(task)]
        if master_cover_mode == "covering":
            cover_cons[task] = model.addCons(quicksum(terms) >= 1.0, name=f"cover[{task}]")
        else:
            cover_cons[task] = model.addCons(quicksum(terms) == 1.0, name=f"cover[{task}]")

    fleet_cons = model.addCons(quicksum(variables.values()) <= float(data.vehicle_count), name="fleet")
    vehicle_lb_cons = None
    if vehicle_lower_bound_cut_enabled:
        vehicle_lb_cons = model.addCons(
            quicksum(variables.values()) >= float(vehicle_lower_bound(data)),
            name="vehicle_lb",
        )

    model.optimize()
    status = _status_name(model.getStatus())
    selected: list[ScheduleColumn] = []
    objective: float | None = None
    if model.getNSols() > 0:
        solution = model.getBestSol()
        for index, var in variables.items():
            if float(model.getSolVal(solution, var)) > 0.5:
                selected.append(columns[index])
        objective = float(model.getSolObjVal(solution))

    return RestrictedMasterIntegerSolution(
        status=status,
        objective=objective,
        selected_columns=selected,
        variable_count=len(variables),
        constraint_count=len(data.tasks) + 1 + int(vehicle_lb_cons is not None),
    )
