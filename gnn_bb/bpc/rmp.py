"""中文摘要：本文件用 SCIP 构建并求解当前节点的 Restricted Master LP。SCIP 只负责 LP 和 dual，不负责 BPC 搜索树。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .branching import BranchConstraint, route_allowed_by_branch, route_branch_coefficient
from .columns import RouteColumn, route_work_time_lower_bound
from .cuts import Cut
from .data import BPCData


@dataclass
class RMPDuals:
    cover: dict[int, float]
    task_vehicle: dict[tuple[int, int], float]
    sortie_count: dict[int, float]
    vehicle_time: dict[int, float]
    cuts: dict[int, float]
    branches: dict[int, float]


@dataclass
class RMPSolution:
    status: str
    objective: float | None
    duals: RMPDuals | None
    artificial_sum: float
    route_values: list[tuple[RouteColumn, int, float]]
    y_values: dict[int, float]
    variable_count: int
    constraint_count: int
    lambda_reduced_costs: dict[tuple[int, int], float] | None = None

    @property
    def optimal(self) -> bool:
        return self.status.lower() == "optimal"


class _DualCapturePricer:
    """中文注释：只在 SCIP pricing callback 中读取 dual，不生成列；真正 pricing 由 clean BPC 外层执行。"""

    def __init__(
        self,
        cover_cons,
        task_vehicle_cons,
        sortie_cons,
        time_cons,
        cut_cons,
        branch_cons,
    ):
        from pyscipopt import Pricer

        class _Pricer(Pricer):
            def __init__(self, outer):
                super().__init__()
                self.outer = outer

            def pricerinit(self):
                self.outer.on_init(self.model)

            def pricerredcost(self):
                return self.outer.on_redcost(self.model)

            def pricerfarkas(self):
                return self.outer.on_redcost(self.model)

        self.plugin = _Pricer(self)
        self.cover_cons = dict(cover_cons)
        self.task_vehicle_cons = dict(task_vehicle_cons)
        self.sortie_cons = dict(sortie_cons)
        self.time_cons = dict(time_cons)
        self.cut_cons = dict(cut_cons)
        self.branch_cons = dict(branch_cons)
        self.duals: RMPDuals | None = None

    def on_init(self, model) -> None:
        self.cover_cons = {key: model.getTransformedCons(cons) for key, cons in self.cover_cons.items()}
        self.task_vehicle_cons = {key: model.getTransformedCons(cons) for key, cons in self.task_vehicle_cons.items()}
        self.sortie_cons = {key: model.getTransformedCons(cons) for key, cons in self.sortie_cons.items()}
        self.time_cons = {key: model.getTransformedCons(cons) for key, cons in self.time_cons.items()}
        self.cut_cons = {key: model.getTransformedCons(cons) for key, cons in self.cut_cons.items()}
        self.branch_cons = {key: model.getTransformedCons(cons) for key, cons in self.branch_cons.items()}

    def on_redcost(self, model):
        from pyscipopt import SCIP_RESULT

        self.duals = RMPDuals(
            cover={task: float(model.getDualsolLinear(cons)) for task, cons in self.cover_cons.items()},
            task_vehicle={key: float(model.getDualsolLinear(cons)) for key, cons in self.task_vehicle_cons.items()},
            sortie_count={vehicle: float(model.getDualsolLinear(cons)) for vehicle, cons in self.sortie_cons.items()},
            vehicle_time={vehicle: float(model.getDualsolLinear(cons)) for vehicle, cons in self.time_cons.items()},
            cuts={cut_id: float(model.getDualsolLinear(cons)) for cut_id, cons in self.cut_cons.items()},
            branches={index: float(model.getDualsolLinear(cons)) for index, cons in self.branch_cons.items()},
        )
        return {"result": SCIP_RESULT.SUCCESS}


def _try_set_param(model, name: str, value: Any) -> None:
    try:
        model.setParam(name, value)
    except Exception:
        pass


def _status_name(status: Any) -> str:
    text = str(status).lower()
    mapping = {
        "optimal": "OPTIMAL",
        "infeasible": "INFEASIBLE",
        "unbounded": "UNBOUNDED",
        "inforunbd": "INF_OR_UNBD",
        "timelimit": "TIME_LIMIT",
        "memlimit": "MEMORY_LIMIT",
        "userinterrupt": "INTERRUPTED",
    }
    return mapping.get(text, text.upper())


def solve_rmp_lp(
    data: BPCData,
    routes: list[RouteColumn],
    cuts: list[Cut],
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    phase: str,
    rmp_params: dict[str, Any] | None = None,
    verbose: bool = False,
    task_vehicle_linking_enabled: bool = True,
    capture_lambda_reduced_costs: bool = False,
) -> RMPSolution:
    from pyscipopt import Model, quicksum

    if phase not in {"phase1", "phase2"}:
        raise ValueError(f"未知 RMP phase: {phase}")

    model = Model(f"clean_bpc_rmp_{data.name}_{phase}")
    _try_set_param(model, "display/verblevel", 4 if verbose else 0)
    # 中文注释：关闭 presolve 让 dual 和原约束一一对应，便于 reduced cost 审计。
    _try_set_param(model, "presolving/maxrounds", 0)
    _try_set_param(model, "separating/maxrounds", 0)
    _try_set_param(model, "parallel/maxnthreads", 1)
    for name, value in (rmp_params or {}).items():
        _try_set_param(model, name, value)

    y = {}
    for vehicle in data.vehicles:
        lb = 0.0
        ub = 1.0
        for constraint in branch_constraints:
            if constraint.kind == "vehicle_use_on" and int(constraint.vehicle) == int(vehicle):
                lb = 1.0
            elif constraint.kind == "vehicle_use_off" and int(constraint.vehicle) == int(vehicle):
                ub = 0.0
        y[vehicle] = model.addVar(
            vtype="C",
            lb=lb,
            ub=ub,
            obj=0.0 if phase == "phase1" else data.fixed_vehicle_cost,
            name=f"y[{vehicle}]",
        )

    route_vars: dict[tuple[int, int], Any] = {}
    for route_index, route in enumerate(routes):
        for vehicle in data.vehicles:
            if not route_allowed_by_branch(route, vehicle, branch_constraints):
                continue
            # 中文注释：RMP 内部用当前 routes 列表下标做 key，避免临时 RouteColumn(id=-1) 造成变量覆盖。
            route_vars[(route_index, vehicle)] = model.addVar(
                vtype="C",
                lb=0.0,
                ub=1.0,
                obj=0.0 if phase == "phase1" else float(route.cost),
                name=f"lambda[{route_index},{vehicle}]",
            )

    artificial = {}
    if phase == "phase1":
        artificial = {
            task: model.addVar(vtype="C", lb=0.0, ub=1.0, obj=1.0, name=f"artificial[{task}]")
            for task in data.tasks
        }
    cut_artificial = {}
    if phase == "phase1":
        cut_artificial = {
            cut.id: model.addVar(vtype="C", lb=0.0, obj=1.0, name=f"cut_artificial[{cut.id}]")
            for cut in cuts
        }

    cover_cons = {}
    for task in data.tasks:
        terms = [
            var
            for (route_id, _vehicle), var in route_vars.items()
            if task in routes[route_id].task_set
        ]
        if phase == "phase1":
            terms.append(artificial[task])
        cover_cons[task] = model.addCons(quicksum(terms) == 1.0, name=f"cover[{task}]", modifiable=True)

    task_vehicle_cons = {}
    if task_vehicle_linking_enabled:
        for task in data.tasks:
            for vehicle in data.vehicles:
                terms = [
                    var
                    for (route_id, var_vehicle), var in route_vars.items()
                    if int(var_vehicle) == int(vehicle) and task in routes[route_id].task_set
                ]
                # 中文注释：如果任务 i 在车辆 r 上被服务，则车辆 r 必须启用；这是有限 linking row，不依赖潜在列数量。
                task_vehicle_cons[(int(task), int(vehicle))] = model.addCons(
                    quicksum(terms) - y[vehicle] <= 0.0,
                    name=f"task_vehicle_link[{task},{vehicle}]",
                    modifiable=True,
                )

    sortie_cons = {}
    time_cons = {}
    for vehicle in data.vehicles:
        vehicle_vars = [
            (routes[route_id], var)
            for (route_id, var_vehicle), var in route_vars.items()
            if int(var_vehicle) == int(vehicle)
        ]
        sortie_cons[vehicle] = model.addCons(
            quicksum(var for _route, var in vehicle_vars) - data.sortie_limit * y[vehicle] <= 0.0,
            name=f"sortie_count[{vehicle}]",
            modifiable=True,
        )
        time_cons[vehicle] = model.addCons(
            quicksum(route_work_time_lower_bound(data, route) * var for route, var in vehicle_vars)
            - data.horizon * y[vehicle]
            <= 0.0,
            name=f"vehicle_time[{vehicle}]",
            modifiable=True,
        )

    for left, right in zip(data.vehicles[:-1], data.vehicles[1:]):
        model.addCons(y[right] <= y[left], name=f"vehicle_order[{left}]")

    cut_cons = {}
    for cut in cuts:
        terms = [
            cut.coefficient(routes[route_id], vehicle) * var
            for (route_id, vehicle), var in route_vars.items()
            if cut.coefficient(routes[route_id], vehicle) != 0.0
        ]
        y_terms = [
            cut.y_coefficient(vehicle) * var
            for vehicle, var in y.items()
            if hasattr(cut, "y_coefficient") and cut.y_coefficient(vehicle) != 0.0
        ]
        expr = quicksum([*terms, *y_terms])
        if phase == "phase1":
            if cut.sense == "<=":
                expr -= cut_artificial[cut.id]
            elif cut.sense == ">=":
                expr += cut_artificial[cut.id]
            else:
                raise ValueError(f"未知 cut sense: {cut.sense}")
        if cut.sense == "<=":
            cut_cons[cut.id] = model.addCons(expr <= cut.rhs, name=f"cut[{cut.id}]", modifiable=True)
        elif cut.sense == ">=":
            cut_cons[cut.id] = model.addCons(expr >= cut.rhs, name=f"cut[{cut.id}]", modifiable=True)
        else:
            raise ValueError(f"未知 cut sense: {cut.sense}")

    branch_cons = {}
    for index, constraint in enumerate(branch_constraints):
        if constraint.kind != "arc_on":
            continue
        terms = [
            route_branch_coefficient(routes[route_id], vehicle, constraint) * var
            for (route_id, vehicle), var in route_vars.items()
            if route_branch_coefficient(routes[route_id], vehicle, constraint) != 0.0
        ]
        branch_cons[index] = model.addCons(quicksum(terms) >= 1.0, name=f"branch_arc_on[{index}]", modifiable=True)

    dual_capture = _DualCapturePricer(
        cover_cons,
        task_vehicle_cons,
        sortie_cons,
        time_cons,
        cut_cons,
        branch_cons,
    )
    model.includePricer(dual_capture.plugin, "clean_bpc_dual_capture", "读取 RMP LP dual 的空 pricer", priority=1, delay=False)

    model.optimize()
    status = _status_name(model.getStatus())
    if status != "OPTIMAL":
        return RMPSolution(
            status=status,
            objective=None,
            duals=None,
            artificial_sum=0.0,
            route_values=[],
            y_values={},
            variable_count=model.getNVars(),
            constraint_count=model.getNConss(),
            lambda_reduced_costs={} if capture_lambda_reduced_costs else None,
        )

    objective = float(model.getObjVal())
    artificial_sum = (
        sum(float(model.getVal(var)) for var in artificial.values())
        + sum(float(model.getVal(var)) for var in cut_artificial.values())
        if phase == "phase1"
        else 0.0
    )
    route_values = [
        (routes[route_id], vehicle, float(model.getVal(var)))
        for (route_id, vehicle), var in route_vars.items()
        if abs(float(model.getVal(var))) > 1.0e-9
    ]
    y_values = {vehicle: float(model.getVal(var)) for vehicle, var in y.items()}
    duals = dual_capture.duals
    if duals is None:
        raise RuntimeError("SCIP 未调用 dual capture pricer，无法取得 RMP dual。")
    lambda_reduced_costs = None
    if capture_lambda_reduced_costs:
        # 中文注释：只用于 reduced-cost 一致性测试；正常 BPC 不依赖已有变量的 solver reduced cost。
        lambda_reduced_costs = {
            (int(route_id), int(vehicle)): float(model.getVarRedcost(var))
            for (route_id, vehicle), var in route_vars.items()
        }
    return RMPSolution(
        status=status,
        objective=objective,
        duals=duals,
        artificial_sum=artificial_sum,
        route_values=route_values,
        y_values=y_values,
        variable_count=model.getNVars(),
        constraint_count=model.getNConss(),
        lambda_reduced_costs=lambda_reduced_costs,
    )
