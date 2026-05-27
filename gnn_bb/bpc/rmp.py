"""中文摘要：本文件用 SCIP 构建并求解当前节点的 Restricted Master。

LP 版本负责提供节点 bound 和 dual；binary 版本只作为 primal heuristic，
用于在已有 route pool 上找真实可行 incumbent，不参与 lower bound 证明。
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

from .branching import BranchConstraint, route_allowed_by_branch, route_branch_coefficient
from .columns import RouteColumn, route_work_time_lower_bound
from .cuts import Cut, normalize_signatures
from .data import BPCData
from .schedule_capacity import find_schedule_capacity_conflict
from .validation import ScheduleInfeasibilityWitness, check_route_set_schedule_feasible, diagnose_route_set_schedule
from .validation import exact_route_set_schedule_capacity


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


@dataclass
class RestrictedIntegerResult:
    status: str
    objective: float | None
    assigned_routes: dict[int, list[RouteColumn]]
    solving_time: float
    variable_count: int
    constraint_count: int
    selected_routes: int
    raw_objective: float | None = None
    rejected_solutions: int = 0
    no_good_cuts: int = 0
    pair_conflict_cuts: int = 0
    route_set_packing_cuts: int = 0
    schedule_capacity_cuts: int = 0
    rejected_conflicts: tuple[tuple[int, tuple[RouteColumn, ...]], ...] = tuple()
    source: str = "restricted_integer_master"
    repair_attempts: int = 0
    repair_successes: int = 0
    repair_time: float = 0.0
    repair_states: int = 0
    repair_best_objective: float | None = None
    solution_pool_scanned: int = 0
    solution_pool_accepted_rank: int | None = None

    @property
    def feasible(self) -> bool:
        return self.objective is not None and bool(self.assigned_routes)


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


def _solution_value(model, solution, var) -> float:
    try:
        return float(model.getSolVal(solution, var))
    except Exception:
        return float(model.getVal(var))


def _extract_integer_assignment(
    data: BPCData,
    routes: list[RouteColumn],
    route_vars: dict[tuple[int, int], Any],
    model,
    solution,
) -> tuple[dict[int, list[RouteColumn]], int]:
    assigned: dict[int, list[RouteColumn]] = {int(vehicle): [] for vehicle in data.vehicles}
    selected_routes = 0
    for (route_id, vehicle), var in route_vars.items():
        if _solution_value(model, solution, var) > 0.5:
            assigned[int(vehicle)].append(routes[route_id])
            selected_routes += 1
    return assigned, selected_routes


def _assignment_objective(data: BPCData, assigned: dict[int, list[RouteColumn]]) -> float:
    used = sum(1 for routes in assigned.values() if routes)
    return sum(route.cost for routes in assigned.values() for route in routes) + used * data.fixed_vehicle_cost


def _assignment_feasible(data: BPCData, assigned: dict[int, list[RouteColumn]]) -> bool:
    covered: list[int] = []
    for routes in assigned.values():
        if len(routes) > data.sortie_limit:
            return False
        if not check_route_set_schedule_feasible(data, routes).feasible:
            return False
        for route in routes:
            covered.extend(int(task) for task in route.tasks)
    return sorted(covered) == sorted(int(task) for task in data.tasks) and len(covered) == len(set(covered))


def _repair_route_assignment(
    data: BPCData,
    routes: list[RouteColumn],
    *,
    incumbent_bound: float | None,
    max_states: int,
) -> tuple[dict[int, list[RouteColumn]] | None, float | None, int]:
    """中文注释：只重新分配 route 到车辆；成功结果必须满足原问题排程可行性。"""

    if not routes:
        return None, None, 0
    if len(routes) > len(data.vehicles) * int(data.sortie_limit):
        return None, None, 0
    ordered_routes = sorted(routes, key=lambda route: (-len(route.tasks), -route.cycle_time, route.signature))
    assigned: dict[int, list[RouteColumn]] = {int(vehicle): [] for vehicle in data.vehicles}
    best: dict[int, list[RouteColumn]] | None = None
    best_objective = float("inf") if incumbent_bound is None else float(incumbent_bound)
    fixed_route_cost = sum(route.cost for route in ordered_routes)
    visited = 0
    state_limit = max(1, int(max_states))

    def search(index: int) -> None:
        nonlocal best, best_objective, visited
        visited += 1
        if visited > state_limit:
            return
        used = sum(1 for vehicle_routes in assigned.values() if vehicle_routes)
        lower_bound = fixed_route_cost + used * data.fixed_vehicle_cost
        if lower_bound >= best_objective - 1.0e-6:
            return
        if index == len(ordered_routes):
            candidate = {vehicle: list(items) for vehicle, items in assigned.items()}
            if not _assignment_feasible(data, candidate):
                return
            objective = _assignment_objective(data, candidate)
            if objective < best_objective - 1.0e-6:
                best_objective = objective
                best = candidate
            return

        route = ordered_routes[index]
        tried_empty_vehicle = False
        vehicles = sorted(data.vehicles, key=lambda vehicle: (len(assigned[int(vehicle)]) == 0, len(assigned[int(vehicle)]), int(vehicle)))
        for vehicle_raw in vehicles:
            vehicle = int(vehicle_raw)
            if len(assigned[vehicle]) >= data.sortie_limit:
                continue
            if not assigned[vehicle]:
                if tried_empty_vehicle:
                    continue
                tried_empty_vehicle = True
            candidate_routes = [*assigned[vehicle], route]
            if not check_route_set_schedule_feasible(data, candidate_routes).feasible:
                continue
            assigned[vehicle].append(route)
            search(index + 1)
            assigned[vehicle].pop()

    search(0)
    if best is None:
        return None, None, visited
    return best, best_objective, visited


def _first_schedule_conflict(
    data: BPCData,
    assigned: dict[int, list[RouteColumn]],
) -> tuple[int, ScheduleInfeasibilityWitness, tuple[RouteColumn, ...]] | None:
    for vehicle, vehicle_routes in assigned.items():
        if not vehicle_routes:
            continue
        witness = diagnose_route_set_schedule(data, vehicle_routes)
        if witness is None:
            continue
        return int(vehicle), witness, tuple(vehicle_routes)
    return None


def solve_restricted_integer_master(
    data: BPCData,
    routes: list[RouteColumn],
    cuts: list[Cut],
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    rmp_params: dict[str, Any] | None = None,
    time_limit: float = 20.0,
    task_vehicle_linking_enabled: bool = True,
    incumbent_bound: float | None = None,
    schedule_aware: bool = True,
    max_no_good_rounds: int = 20,
    schedule_capacity_oracle_max_states: int = 200000,
    schedule_capacity_conflict_max_subset_size: int = 10,
    repair_enabled: bool = True,
    repair_max_attempts: int = 3,
    repair_max_states: int = 50000,
    scan_solution_pool: bool = False,
    solution_pool_scan_limit: int = 20,
) -> RestrictedIntegerResult:
    """中文注释：在当前 route pool 上解 binary RMP，并可迭代排除排程不可行的整数解。"""

    from pyscipopt import Model, quicksum

    # 中文注释：这里不用 SCIP objlimit；排程不可行的低目标解可能提前触发 objlimit 停止。
    # 下面用线性目标 cutoff 约束过滤不可能改进 incumbent 的候选，同时保留 no-good 迭代能力。
    started = time.perf_counter()
    model = Model(f"clean_bpc_restricted_integer_{data.name}")
    _try_set_param(model, "display/verblevel", 0)
    _try_set_param(model, "parallel/maxnthreads", 1)
    if time_limit > 0:
        _try_set_param(model, "limits/time", float(time_limit))
    for name, value in (rmp_params or {}).items():
        if str(name).startswith("display/") or str(name).startswith("parallel/"):
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
            vtype="B",
            lb=lb,
            ub=ub,
            obj=data.fixed_vehicle_cost,
            name=f"y[{vehicle}]",
        )

    route_vars: dict[tuple[int, int], Any] = {}
    for route_index, route in enumerate(routes):
        for vehicle in data.vehicles:
            if not route_allowed_by_branch(route, vehicle, branch_constraints):
                continue
            route_vars[(route_index, vehicle)] = model.addVar(
                vtype="B",
                obj=float(route.cost),
                name=f"lambda[{route_index},{vehicle}]",
            )

    for task in data.tasks:
        terms = [
            var
            for (route_id, _vehicle), var in route_vars.items()
            if int(task) in routes[route_id].task_set
        ]
        model.addCons(quicksum(terms) == 1.0, name=f"cover[{task}]")

    if task_vehicle_linking_enabled:
        for task in data.tasks:
            for vehicle in data.vehicles:
                terms = [
                    var
                    for (route_id, var_vehicle), var in route_vars.items()
                    if int(var_vehicle) == int(vehicle) and int(task) in routes[route_id].task_set
                ]
                model.addCons(quicksum(terms) - y[vehicle] <= 0.0, name=f"task_vehicle_link[{task},{vehicle}]")

    for vehicle in data.vehicles:
        vehicle_vars = [
            (routes[route_id], var)
            for (route_id, var_vehicle), var in route_vars.items()
            if int(var_vehicle) == int(vehicle)
        ]
        model.addCons(quicksum(var for _route, var in vehicle_vars) - data.sortie_limit * y[vehicle] <= 0.0, name=f"sortie_count[{vehicle}]")
        model.addCons(
            quicksum(route_work_time_lower_bound(data, route) * var for route, var in vehicle_vars)
            - data.horizon * y[vehicle]
            <= 0.0,
            name=f"vehicle_time[{vehicle}]",
        )

    for left, right in zip(data.vehicles[:-1], data.vehicles[1:]):
        model.addCons(y[right] <= y[left], name=f"vehicle_order[{left}]")

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
        if cut.sense == "<=":
            model.addCons(expr <= cut.rhs, name=f"cut[{cut.id}]")
        elif cut.sense == ">=":
            model.addCons(expr >= cut.rhs, name=f"cut[{cut.id}]")
        else:
            raise ValueError(f"未知 cut sense: {cut.sense}")

    for index, constraint in enumerate(branch_constraints):
        if constraint.kind != "arc_on":
            continue
        terms = [
            route_branch_coefficient(routes[route_id], vehicle, constraint) * var
            for (route_id, vehicle), var in route_vars.items()
            if route_branch_coefficient(routes[route_id], vehicle, constraint) != 0.0
        ]
        model.addCons(quicksum(terms) >= 1.0, name=f"branch_arc_on[{index}]")

    objective_expr = quicksum(
        [float(data.fixed_vehicle_cost) * var for var in y.values()]
        + [float(routes[route_id].cost) * var for (route_id, _vehicle), var in route_vars.items()]
    )
    if incumbent_bound is not None:
        model.addCons(objective_expr <= float(incumbent_bound) - 1.0e-6, name="incumbent_cutoff")

    raw_best_objective: float | None = None
    rejected_solutions = 0
    no_good_cuts = 0
    pair_conflict_cuts = 0
    route_set_packing_cuts = 0
    schedule_capacity_cuts = 0
    repair_attempts = 0
    repair_successes = 0
    repair_time = 0.0
    repair_states = 0
    repair_best_objective: float | None = None
    repair_seen: set[tuple[tuple[int, ...], ...]] = set()
    rejected_conflicts: list[tuple[int, tuple[RouteColumn, ...]]] = []
    temporary_pair_keys: set[tuple[int, tuple[tuple[int, ...], tuple[int, ...]]]] = set()
    temporary_route_pack_keys: set[tuple[int, tuple[tuple[int, ...], ...], int]] = set()
    temporary_capacity_keys: set[tuple[int, tuple[int, ...]]] = set()
    route_set_packing_cache: dict[tuple[tuple[int, ...], ...], tuple[int, int] | None] = {}
    last_status = "UNKNOWN"
    no_good_limit = max(0, int(max_no_good_rounds))
    deadline = started + float(time_limit) if time_limit > 0 else None
    solution_pool_scanned = 0

    def route_set_schedule_bound(conflict_routes: tuple[RouteColumn, ...]) -> tuple[int | None, int | None]:
        signatures = normalize_signatures(tuple(route.signature for route in conflict_routes))
        cached = route_set_packing_cache.get(signatures)
        if cached is not None:
            return cached
        if signatures in route_set_packing_cache and cached is None:
            return (None, None)
        result = exact_route_set_schedule_capacity(
            data,
            conflict_routes,
            max_states=schedule_capacity_oracle_max_states,
        )
        if result is None or not result.exact:
            route_set_packing_cache[signatures] = None
            return (None, None)
        value = (int(result.upper_bound), int(result.states_explored))
        route_set_packing_cache[signatures] = value
        return value

    while True:
        if deadline is not None:
            remaining = deadline - time.perf_counter()
            if remaining <= 0.0:
                last_status = "TIME_LIMIT"
                break
            _try_set_param(model, "limits/time", max(0.001, float(remaining)))

        model.optimize()
        last_status = _status_name(model.getStatus())
        solution = None
        try:
            if model.getNSols() > 0:
                solution = model.getBestSol()
        except Exception:
            solution = None
        if solution is None:
            break

        pool_solutions = [solution]
        if scan_solution_pool:
            try:
                fetched = list(model.getSols())
            except Exception:
                fetched = []
            if fetched:
                try:
                    fetched.sort(key=lambda sol: float(model.getSolObjVal(sol)))
                except Exception:
                    pass
                limit = max(1, int(solution_pool_scan_limit))
                pool_solutions = fetched[:limit]

        best_candidate: tuple[
            float,
            dict[int, list[RouteColumn]],
            int,
            tuple[int, ScheduleInfeasibilityWitness, tuple[RouteColumn, ...]] | None,
        ] | None = None

        for pool_rank, candidate_solution in enumerate(pool_solutions):
            if scan_solution_pool:
                solution_pool_scanned += 1
            raw_objective = float(model.getSolObjVal(candidate_solution))
            if raw_best_objective is None or raw_objective < raw_best_objective:
                raw_best_objective = raw_objective
            assigned, selected_routes = _extract_integer_assignment(data, routes, route_vars, model, candidate_solution)
            if pool_rank == 0:
                best_candidate = (raw_objective, assigned, selected_routes, None)
            if not schedule_aware:
                return RestrictedIntegerResult(
                    status=last_status,
                    objective=raw_objective,
                    assigned_routes=assigned,
                    solving_time=time.perf_counter() - started,
                    variable_count=model.getNVars(),
                    constraint_count=model.getNConss(),
                    selected_routes=selected_routes,
                    raw_objective=raw_best_objective,
                    rejected_solutions=rejected_solutions,
                    no_good_cuts=no_good_cuts,
                    pair_conflict_cuts=pair_conflict_cuts,
                    route_set_packing_cuts=route_set_packing_cuts,
                    schedule_capacity_cuts=schedule_capacity_cuts,
                    rejected_conflicts=tuple(rejected_conflicts),
                    repair_attempts=repair_attempts,
                    repair_successes=repair_successes,
                    repair_time=repair_time,
                    repair_states=repair_states,
                    repair_best_objective=repair_best_objective,
                    solution_pool_scanned=solution_pool_scanned,
                    solution_pool_accepted_rank=pool_rank if scan_solution_pool else None,
                )

            conflict = _first_schedule_conflict(data, assigned)
            if pool_rank == 0:
                best_candidate = (raw_objective, assigned, selected_routes, conflict)
            if conflict is None:
                return RestrictedIntegerResult(
                    status=last_status,
                    objective=raw_objective,
                    assigned_routes=assigned,
                    solving_time=time.perf_counter() - started,
                    variable_count=model.getNVars(),
                    constraint_count=model.getNConss(),
                    selected_routes=selected_routes,
                    raw_objective=raw_best_objective,
                    rejected_solutions=rejected_solutions,
                    no_good_cuts=no_good_cuts,
                    pair_conflict_cuts=pair_conflict_cuts,
                    route_set_packing_cuts=route_set_packing_cuts,
                    schedule_capacity_cuts=schedule_capacity_cuts,
                    rejected_conflicts=tuple(rejected_conflicts),
                    source="restricted_integer_master_solution_pool" if pool_rank > 0 else "restricted_integer_master",
                    repair_attempts=repair_attempts,
                    repair_successes=repair_successes,
                    repair_time=repair_time,
                    repair_states=repair_states,
                    repair_best_objective=repair_best_objective,
                    solution_pool_scanned=solution_pool_scanned,
                    solution_pool_accepted_rank=pool_rank if scan_solution_pool else None,
                )

        if best_candidate is None:
            break
        raw_objective, assigned, selected_routes, conflict = best_candidate
        if not schedule_aware:
            return RestrictedIntegerResult(
                status=last_status,
                objective=raw_objective,
                assigned_routes=assigned,
                solving_time=time.perf_counter() - started,
                variable_count=model.getNVars(),
                constraint_count=model.getNConss(),
                selected_routes=selected_routes,
                raw_objective=raw_best_objective,
                rejected_solutions=rejected_solutions,
                no_good_cuts=no_good_cuts,
                pair_conflict_cuts=pair_conflict_cuts,
                route_set_packing_cuts=route_set_packing_cuts,
                schedule_capacity_cuts=schedule_capacity_cuts,
                rejected_conflicts=tuple(rejected_conflicts),
                repair_attempts=repair_attempts,
                repair_successes=repair_successes,
                repair_time=repair_time,
                repair_states=repair_states,
                repair_best_objective=repair_best_objective,
                solution_pool_scanned=solution_pool_scanned,
            )

        if conflict is None:
            return RestrictedIntegerResult(
                status=last_status,
                objective=raw_objective,
                assigned_routes=assigned,
                solving_time=time.perf_counter() - started,
                variable_count=model.getNVars(),
                constraint_count=model.getNConss(),
                selected_routes=selected_routes,
                raw_objective=raw_best_objective,
                rejected_solutions=rejected_solutions,
                no_good_cuts=no_good_cuts,
                pair_conflict_cuts=pair_conflict_cuts,
                route_set_packing_cuts=route_set_packing_cuts,
                schedule_capacity_cuts=schedule_capacity_cuts,
                rejected_conflicts=tuple(rejected_conflicts),
                repair_attempts=repair_attempts,
                repair_successes=repair_successes,
                repair_time=repair_time,
                repair_states=repair_states,
                repair_best_objective=repair_best_objective,
                solution_pool_scanned=solution_pool_scanned,
            )

        conflict_vehicle, witness, full_conflict_routes = conflict
        conflict_routes = tuple(witness.routes)
        selected_route_list = [route for vehicle_routes in assigned.values() for route in vehicle_routes]
        selected_signature_key = normalize_signatures(tuple(route.signature for route in selected_route_list))
        if (
            repair_enabled
            and repair_attempts < max(0, int(repair_max_attempts))
            and selected_signature_key not in repair_seen
            and (
                incumbent_bound is None
                or raw_objective < float(incumbent_bound) + float(data.fixed_vehicle_cost) - 1.0e-6
            )
        ):
            repair_seen.add(selected_signature_key)
            repair_attempts += 1
            repair_started = time.perf_counter()
            repaired = _repair_route_assignment(
                data,
                selected_route_list,
                incumbent_bound=incumbent_bound,
                max_states=repair_max_states,
            )
            repair_time += time.perf_counter() - repair_started
            repaired_assigned, repaired_objective, states = repaired
            repair_states += int(states)
            if repaired_assigned is not None and repaired_objective is not None:
                repair_successes += 1
                repair_best_objective = (
                    repaired_objective
                    if repair_best_objective is None
                    else min(float(repair_best_objective), float(repaired_objective))
                )
                rejected_solutions += 1
                return RestrictedIntegerResult(
                    status="REPAIRED",
                    objective=repaired_objective,
                    assigned_routes=repaired_assigned,
                    solving_time=time.perf_counter() - started,
                    variable_count=model.getNVars(),
                    constraint_count=model.getNConss(),
                    selected_routes=selected_routes,
                    raw_objective=raw_best_objective,
                    rejected_solutions=rejected_solutions,
                    no_good_cuts=no_good_cuts,
                    pair_conflict_cuts=pair_conflict_cuts,
                    route_set_packing_cuts=route_set_packing_cuts,
                    schedule_capacity_cuts=schedule_capacity_cuts,
                    rejected_conflicts=tuple(rejected_conflicts),
                    source="restricted_integer_master_repair",
                    repair_attempts=repair_attempts,
                    repair_successes=repair_successes,
                    repair_time=repair_time,
                    repair_states=repair_states,
                    repair_best_objective=repair_best_objective,
                    solution_pool_scanned=solution_pool_scanned,
                )

        rejected_solutions += 1
        rejected_conflicts.append((int(conflict_vehicle), tuple(full_conflict_routes)))
        if rejected_solutions > no_good_limit:
            last_status = "SCHEDULE_REJECTED_LIMIT"
            break

        conflict_signatures = {route.signature for route in conflict_routes}
        try:
            model.freeTransform()
        except Exception:
            pass

        added_pair = False
        for pair in witness.pair_conflicts:
            pair_signatures = pair.signatures
            signature_set = set(pair_signatures)
            for vehicle in data.vehicles:
                key = (int(vehicle), pair_signatures)
                if key in temporary_pair_keys:
                    continue
                pair_terms = [
                    var
                    for (route_id, var_vehicle), var in route_vars.items()
                    if int(var_vehicle) == int(vehicle) and routes[route_id].signature in signature_set
                ]
                if len(pair_terms) < 2:
                    continue
                model.addCons(
                    quicksum(pair_terms) <= 1.0,
                    name=f"tmp_schedule_pair_conflict[{pair_conflict_cuts},{vehicle}]",
                )
                temporary_pair_keys.add(key)
                pair_conflict_cuts += 1
                added_pair = True
            if added_pair:
                break
        if added_pair:
            continue

        conflict_signature_tuple = normalize_signatures(tuple(route.signature for route in full_conflict_routes))
        route_pack_upper_bound, _route_pack_states = route_set_schedule_bound(full_conflict_routes)
        if route_pack_upper_bound is not None and route_pack_upper_bound < len(conflict_signature_tuple) - 1:
            added_route_pack = False
            signature_set = set(conflict_signature_tuple)
            for vehicle in data.vehicles:
                key = (int(vehicle), conflict_signature_tuple, int(route_pack_upper_bound))
                if key in temporary_route_pack_keys:
                    continue
                route_pack_terms = [
                    var
                    for (route_id, var_vehicle), var in route_vars.items()
                    if int(var_vehicle) == int(vehicle) and routes[route_id].signature in signature_set
                ]
                if not route_pack_terms:
                    continue
                model.addCons(
                    quicksum(route_pack_terms) - int(route_pack_upper_bound) * y[vehicle] <= 0.0,
                    name=f"tmp_schedule_route_set_packing[{route_set_packing_cuts},{vehicle}]",
                )
                temporary_route_pack_keys.add(key)
                route_set_packing_cuts += 1
                added_route_pack = True
            if added_route_pack:
                continue

        structural = find_schedule_capacity_conflict(
            data,
            conflict_routes,
            max_subset_size=schedule_capacity_conflict_max_subset_size,
            max_states=schedule_capacity_oracle_max_states,
        )
        if structural is not None:
            added_structural = False
            subset = set(structural.tasks)
            for vehicle in data.vehicles:
                key = (int(vehicle), structural.tasks)
                if key in temporary_capacity_keys:
                    continue
                terms = [
                    sum(1 for task in routes[route_id].task_set if int(task) in subset) * var
                    for (route_id, var_vehicle), var in route_vars.items()
                    if int(var_vehicle) == int(vehicle)
                    and sum(1 for task in routes[route_id].task_set if int(task) in subset) > 0
                ]
                if not terms:
                    continue
                model.addCons(
                    quicksum(terms) - int(structural.upper_bound) * y[vehicle] <= 0.0,
                    name=f"tmp_schedule_capacity[{schedule_capacity_cuts},{vehicle}]",
                )
                temporary_capacity_keys.add(key)
                schedule_capacity_cuts += 1
                added_structural = True
            if added_structural:
                continue

        added_any = False
        for vehicle in data.vehicles:
            no_good_terms = [
                var
                for (route_id, var_vehicle), var in route_vars.items()
                if int(var_vehicle) == int(vehicle) and routes[route_id].signature in conflict_signatures
            ]
            if not no_good_terms:
                continue
            model.addCons(
                quicksum(no_good_terms) <= max(0, len(conflict_signatures) - 1),
                name=f"tmp_schedule_nogood[{no_good_cuts},{vehicle}]",
            )
            no_good_cuts += 1
            added_any = True
        if not added_any:
            last_status = "SCHEDULE_REJECTED"
            break

    return RestrictedIntegerResult(
        status=last_status,
        objective=None,
        assigned_routes={},
        solving_time=time.perf_counter() - started,
        variable_count=model.getNVars(),
        constraint_count=model.getNConss(),
        selected_routes=0,
        raw_objective=raw_best_objective,
        rejected_solutions=rejected_solutions,
        no_good_cuts=no_good_cuts,
        pair_conflict_cuts=pair_conflict_cuts,
        route_set_packing_cuts=route_set_packing_cuts,
        schedule_capacity_cuts=schedule_capacity_cuts,
        rejected_conflicts=tuple(rejected_conflicts),
        repair_attempts=repair_attempts,
        repair_successes=repair_successes,
        repair_time=repair_time,
        repair_states=repair_states,
        repair_best_objective=repair_best_objective,
        solution_pool_scanned=solution_pool_scanned,
    )
