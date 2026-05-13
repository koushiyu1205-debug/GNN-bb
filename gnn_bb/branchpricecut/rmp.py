"""中文摘要：用 SCIP 求解 vehicle-schedule Restricted Master LP 并读取 dual。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .branching import BranchConstraint, schedule_allowed_by_branch
from .columns import ScheduleColumn
from .data import InstanceData


@dataclass
class RMPDuals:
    cover: dict[int, float]
    fleet: float


@dataclass
class RMPSolution:
    status: str
    objective: float | None
    artificial_sum: float
    duals: RMPDuals | None
    schedule_values: list[tuple[ScheduleColumn, float]]
    variable_count: int
    constraint_count: int

    @property
    def optimal(self) -> bool:
        return self.status == "OPTIMAL"


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
    rmp_params: dict[str, Any] | None = None,
    capture_duals: bool = True,
) -> RMPSolution:
    from pyscipopt import Model, quicksum

    model = Model(f"vehicle_schedule_rmp_{data.name}_{phase}")
    _try_set_param(model, "display/verblevel", 0)
    _try_set_param(model, "presolving/maxrounds", 0)
    _try_set_param(model, "separating/maxrounds", 0)
    _try_set_param(model, "parallel/maxnthreads", 1)
    for name, value in (rmp_params or {}).items():
        _try_set_param(model, name, value)

    variables = {}
    for index, column in enumerate(columns):
        if not schedule_allowed_by_branch(column, branch_constraints):
            continue
        variables[index] = model.addVar(
            vtype="C",
            lb=0.0,
            ub=1.0,
            obj=0.0 if phase == "phase1" else float(column.cost),
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

    fleet_cons = model.addCons(quicksum(variables.values()) <= float(data.vehicle_count), name="fleet")
    model.optimize()
    status = _status_name(model.getStatus())

    duals = None
    if capture_duals and status == "OPTIMAL":
        transformed_cover = {task: model.getTransformedCons(cons) for task, cons in cover_cons.items()}
        transformed_fleet = model.getTransformedCons(fleet_cons)
        duals = RMPDuals(
            cover={task: float(model.getDualsolLinear(cons)) for task, cons in transformed_cover.items()},
            fleet=float(model.getDualsolLinear(transformed_fleet)),
        )

    schedule_values = []
    if status == "OPTIMAL":
        for index, var in variables.items():
            value = float(model.getVal(var))
            if value > 1.0e-9:
                schedule_values.append((columns[index], value))
    artificial_sum = 0.0
    if phase == "phase1" and status == "OPTIMAL":
        artificial_sum = sum(float(model.getVal(var)) for var in artificial.values())

    return RMPSolution(
        status=status,
        objective=None if status != "OPTIMAL" else float(model.getObjVal()),
        artificial_sum=artificial_sum,
        duals=duals,
        schedule_values=schedule_values,
        variable_count=len(variables),
        constraint_count=len(data.tasks) + 1,
    )

