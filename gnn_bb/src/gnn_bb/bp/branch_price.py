"""中文摘要：本文件实现 no-ML 分支定价 baseline：RMP、exact pricing、手写搜索树和 Ryan-Foster 分支。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import heapq
import math
import time
from pathlib import Path
from typing import Any

from gnn_bb.data.instances import task_ids
from gnn_bb.data.io_utils import ensure_dir, round_float, write_json
from gnn_bb.data.terrain import arc_key


@dataclass(frozen=True)
class Route:
    id: int
    tasks: tuple[int, ...]
    task_set: frozenset[int]
    arcs: tuple[tuple[int, int], ...]
    cost: float
    load: float
    energy: float
    return_time: float
    travel_time: float
    cycle_time: float
    service_start: dict[str, float]


@dataclass(frozen=True)
class Column:
    id: int
    route_id: int
    vehicle: int
    sortie: int
    key: tuple[tuple[int, ...], int, int]
    source: str


@dataclass(frozen=True)
class BranchConstraint:
    # 中文注释：kind=ryan_foster 表示任务对是否同一路径服务；task_vehicle/route/vehicle 聚合分支用于避免弱 column 分支。
    kind: str
    sense: str
    rhs: float
    arc: tuple[int, int] | None = None
    pair: tuple[int, int] | None = None
    task_id: int | None = None
    route_signature: tuple[int, ...] | None = None
    vehicle: int | None = None
    column_key: tuple[tuple[int, ...], int, int] | None = None

    def short_name(self) -> str:
        if self.kind == "ryan_foster" and self.pair is not None:
            i, j = self.pair
            return f"rf_{i}_{j}_{self.sense}_{self.rhs:g}"
        if self.kind == "arc" and self.arc is not None:
            i, j = self.arc
            return f"arc_{i}_{j}_{self.sense}_{self.rhs:g}"
        if self.kind == "task_vehicle" and self.task_id is not None and self.vehicle is not None:
            return f"taskveh_{self.task_id}_v{self.vehicle}_{self.sense}_{self.rhs:g}"
        if self.kind == "route_total" and self.route_signature is not None:
            route_text = "_".join(str(task) for task in self.route_signature) or "empty"
            return f"route_{route_text}_{self.sense}_{self.rhs:g}"
        if self.kind == "route_vehicle" and self.route_signature is not None and self.vehicle is not None:
            route_text = "_".join(str(task) for task in self.route_signature) or "empty"
            return f"routeveh_{route_text}_v{self.vehicle}_{self.sense}_{self.rhs:g}"
        if self.column_key is not None:
            route, r, s = self.column_key
            route_text = "_".join(str(task) for task in route) or "empty"
            return f"col_{route_text}_{r}_{s}_{self.sense}_{self.rhs:g}"
        return f"branch_{self.kind}_{self.sense}_{self.rhs:g}"


@dataclass(order=True)
class SearchNode:
    lower_bound: float
    id: int = field(compare=False)
    depth: int = field(compare=False)
    branches: tuple[BranchConstraint, ...] = field(compare=False)


@dataclass(order=True)
class Label:
    priority: float
    node: int = field(compare=False)
    task_id: int | None = field(compare=False)
    parent: object = field(compare=False)
    visited: frozenset[int] = field(compare=False)
    time: float = field(compare=False)
    load: float = field(compare=False)
    energy: float = field(compare=False)
    travel_time: float = field(compare=False)
    cost: float = field(compare=False)
    service_start_time: float | None = field(compare=False)


@dataclass
class NodeResult:
    status: str
    bound: float | None = None
    solution: dict[str, float] | None = None
    artificial_sum: float = 0.0
    cg_iterations: int = 0
    pricing_calls: int = 0
    generated_columns: int = 0
    rmp_solves: int = 0


@dataclass
class BPResult:
    instance: str
    task_count: int
    vehicle_count: int
    sortie_count: int
    status: str
    primal_bound: float | None
    dual_bound: float | None
    gap: float | None
    solving_time: float
    node_count: int
    rmp_solves: int
    cg_iterations: int
    pricing_calls: int
    exact_pricing_calls: int
    generated_routes: int
    generated_columns: int
    root_relaxation: float | None
    incumbent_node: int | None
    log_path: str
    instance_path: str
    seed: int | None

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


class RoutePool:
    """中文注释：全局列池保存已生成路径和路径-slot 列，所有搜索节点共享。"""

    def __init__(self, R: list[int], S: list[int]):
        self.R = R
        self.S = S
        self.routes: list[Route] = []
        self.route_by_signature: dict[tuple[int, ...], Route] = {}
        self.columns: list[Column] = []
        self.column_keys: set[tuple[tuple[int, ...], int, int]] = set()

    def add_route(self, route_data: dict[str, Any]) -> Route:
        signature = tuple(int(task) for task in route_data["tasks"])
        existing = self.route_by_signature.get(signature)
        if existing is not None:
            return existing
        route = Route(
            id=len(self.routes),
            tasks=signature,
            task_set=frozenset(int(task) for task in route_data["task_set"]),
            arcs=tuple(route_data["arcs"]),
            cost=float(route_data["cost"]),
            load=float(route_data["load"]),
            energy=float(route_data["energy"]),
            return_time=float(route_data["return_time"]),
            travel_time=float(route_data["travel_time"]),
            cycle_time=float(route_data["cycle_time"]),
            service_start={str(k): float(v) for k, v in route_data["service_start"].items()},
        )
        self.routes.append(route)
        self.route_by_signature[signature] = route
        return route

    def add_column(self, route: Route, r: int, s: int, source: str) -> bool:
        key = (route.tasks, int(r), int(s))
        if key in self.column_keys:
            return False
        column = Column(id=len(self.columns), route_id=route.id, vehicle=int(r), sortie=int(s), key=key, source=source)
        self.columns.append(column)
        self.column_keys.add(key)
        return True

    def has_column(self, route_signature: tuple[int, ...], r: int, s: int) -> bool:
        return (route_signature, int(r), int(s)) in self.column_keys

    def route_for_column(self, column: Column) -> Route:
        return self.routes[column.route_id]


def _task_value(instance: dict[str, Any], task_id: int, field_name: str) -> float:
    return float(instance["tasks"][str(task_id)][field_name])


def _route_arcs(sequence: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    nodes = (0, *sequence, 0)
    return tuple((int(i), int(j)) for i, j in zip(nodes[:-1], nodes[1:]))


def evaluate_sequence(instance: dict[str, Any], pairwise: dict[str, dict[str, Any]], sequence: tuple[int, ...]) -> dict[str, Any] | None:
    vehicles = instance["vehicles"]
    q_limit = float(vehicles["Q"])
    b_limit = float(vehicles["B_use"])
    horizon = float(vehicles["H"])
    rho = float(vehicles["rho"])

    current = 0
    current_time = 0.0
    load = 0.0
    energy = 0.0
    cost = 0.0
    travel_time = 0.0
    service_start: dict[str, float] = {}

    for task_id in sequence:
        segment = pairwise[arc_key(current, task_id)]
        arrival = current_time + float(segment["tau"])
        start = max(_task_value(instance, task_id, "r"), arrival)
        finish = start + _task_value(instance, task_id, "sigma")
        if finish > _task_value(instance, task_id, "D") + 1.0e-9:
            return None
        load += _task_value(instance, task_id, "d")
        if load > q_limit + 1.0e-9:
            return None
        energy += float(segment["energy"]) + _task_value(instance, task_id, "g")
        if energy > b_limit + 1.0e-9:
            return None
        cost += float(segment["cost"]) + _task_value(instance, task_id, "c_srv")
        travel_time += float(segment["tau"])
        current_time = finish
        current = task_id
        service_start[str(task_id)] = round(start, 6)

    return_segment = pairwise[arc_key(current, 0)]
    return_time = current_time + float(return_segment["tau"])
    total_energy = energy + float(return_segment["energy"])
    if return_time > horizon + 1.0e-9 or total_energy > b_limit + 1.0e-9:
        return None
    total_cost = cost + float(return_segment["cost"])
    total_travel_time = travel_time + float(return_segment["tau"])
    return {
        "tasks": sequence,
        "task_set": frozenset(sequence),
        "arcs": _route_arcs(sequence),
        "cost": round(total_cost, 6),
        "load": round(load, 6),
        "energy": round(total_energy, 6),
        "return_time": round(return_time, 6),
        "travel_time": round(total_travel_time, 6),
        "cycle_time": round(return_time + total_energy / rho, 6),
        "service_start": service_start,
    }


def _label_chain(label: Label) -> list[Label]:
    chain = []
    cursor = label
    while cursor.parent is not None:
        chain.append(cursor)
        cursor = cursor.parent
    chain.reverse()
    return chain


def _sequence_from_label(label: Label) -> tuple[int, ...]:
    return tuple(node.task_id for node in _label_chain(label) if node.task_id is not None)


def _route_from_label(instance: dict[str, Any], pairwise: dict[str, dict[str, Any]], label: Label) -> dict[str, Any]:
    sequence = _sequence_from_label(label)
    route = evaluate_sequence(instance, pairwise, sequence)
    if route is None:
        raise ValueError("内部错误：label 对应的路径应当已经满足资源约束")
    return route


def _branch_coefficient_for_route(route: Route | dict[str, Any], branch: BranchConstraint, column_key=None) -> float:
    signature = route.tasks if isinstance(route, Route) else tuple(route["tasks"])
    if branch.kind == "ryan_foster":
        if branch.pair is None:
            return 0.0
        task_set = route.task_set if isinstance(route, Route) else route["task_set"]
        i, j = branch.pair
        return 1.0 if i in task_set and j in task_set else 0.0
    if branch.kind == "arc":
        arcs = route.arcs if isinstance(route, Route) else tuple(route["arcs"])
        return float(sum(1 for arc in arcs if arc == branch.arc))
    if branch.kind == "task_vehicle":
        if column_key is None or branch.task_id is None:
            return 0.0
        _, r, _ = column_key
        task_set = route.task_set if isinstance(route, Route) else route["task_set"]
        return 1.0 if int(r) == branch.vehicle and branch.task_id in task_set else 0.0
    if branch.kind == "route_total":
        return 1.0 if signature == branch.route_signature else 0.0
    if branch.kind == "route_vehicle":
        if column_key is None:
            return 0.0
        _, r, _ = column_key
        return 1.0 if signature == branch.route_signature and int(r) == branch.vehicle else 0.0
    if branch.kind == "column":
        return 1.0 if column_key == branch.column_key else 0.0
    return 0.0


def _branch_coefficient_for_column(pool: RoutePool, column: Column, branch: BranchConstraint) -> float:
    route = pool.route_for_column(column)
    return _branch_coefficient_for_route(route, branch, column.key)


def _safe_call(func, default=None):
    try:
        value = func()
    except Exception:
        return default
    if isinstance(value, float) and (not math.isfinite(value) or abs(value) >= 1.0e19):
        return default
    return value


def _try_set_param(model, name: str, value: Any) -> None:
    try:
        model.setParam(name, value)
    except Exception:
        pass


class BranchPriceSolver:
    """中文注释：no-ML B&P 求解器。先保证 exact pricing 和分支完整性，再作为 3PB/2LBB 的基线。"""

    def __init__(
        self,
        instance: dict[str, Any],
        pairwise: dict[str, dict[str, Any]],
        *,
        time_limit: float = 3600.0,
        pricing_eps: float = 1.0e-6,
        integer_tol: float = 1.0e-6,
        max_nodes: int = 100000,
        max_cg_iterations_per_node: int = 200,
        max_columns_per_pricing: int = 200,
        artificial_penalty: float = 1.0e6,
        rmp_params: dict[str, Any] | None = None,
        log_path: str | Path | None = None,
        instance_path: str | Path = "",
        seed: int | None = None,
        log_level: str = "progress",
    ):
        vehicles = instance["vehicles"]
        self.instance = instance
        self.pairwise = pairwise
        self.time_limit = float(time_limit)
        self.pricing_eps = float(pricing_eps)
        self.integer_tol = float(integer_tol)
        self.max_nodes = int(max_nodes)
        self.max_cg_iterations_per_node = int(max_cg_iterations_per_node)
        self.max_columns_per_pricing = int(max_columns_per_pricing)
        self.artificial_penalty = float(artificial_penalty)
        self.rmp_params = rmp_params or {}
        self.log_path = Path(log_path) if log_path is not None else None
        self.instance_path = str(instance_path)
        self.seed = seed
        self.log_level = log_level
        self.display_log = log_level != "quiet"
        self.show_scip_log = log_level == "scip"
        self.tasks = task_ids(instance)
        self.R = list(range(1, int(vehicles["R_bar"]) + 1))
        self.S = list(range(1, int(vehicles["S_bar"]) + 1))
        self.horizon = float(vehicles["H"])
        self.pool = RoutePool(self.R, self.S)

        self.started = 0.0
        self.next_node_id = 0
        self.nodes_processed = 0
        self.rmp_solves = 0
        self.cg_iterations = 0
        self.pricing_calls = 0
        self.exact_pricing_calls = 0
        self.generated_columns = 0
        self.root_relaxation: float | None = None
        self.incumbent_value: float | None = None
        self.incumbent_solution: dict[str, Any] | None = None
        self.incumbent_node: int | None = None
        self.termination_status: str | None = None
        self.log_lines: list[str] = []

    def _log(self, message: str, level: str = "progress") -> None:
        self.log_lines.append(message)
        if self.display_log and level != "debug":
            elapsed = time.perf_counter() - self.started if self.started else 0.0
            print(f"[B&P {elapsed:8.2f}s] {message}", flush=True)

    def _remaining_time(self) -> float:
        return max(0.0, self.time_limit - (time.perf_counter() - self.started))

    def _time_exceeded(self) -> bool:
        return self._remaining_time() <= 0.0

    def _new_node(self, depth: int, branches: tuple[BranchConstraint, ...], lower_bound: float) -> SearchNode:
        node = SearchNode(lower_bound=float(lower_bound), id=self.next_node_id, depth=depth, branches=branches)
        self.next_node_id += 1
        return node

    def initialize_columns(self) -> None:
        # 中文注释：单任务路径保证每个任务至少有真实列，Phase-I 人工变量只兜底异常分支节点。
        for task_id in self.tasks:
            route_data = evaluate_sequence(self.instance, self.pairwise, (task_id,))
            if route_data is None:
                raise ValueError(f"任务 {task_id} 不能形成单任务可行路径")
            route = self.pool.add_route(route_data)
            for r in self.R:
                for s in self.S:
                    self.pool.add_column(route, r, s, source="single_task")

    def _build_rmp(self, branches: tuple[BranchConstraint, ...]):
        from pyscipopt import Model, quicksum

        model = Model(f"rmp_{self.instance.get('name', 'instance')}")
        # 中文注释：列生成需要读取原始 cover/slot/branch 约束的对偶。
        # 关闭 presolve/cuts，避免 SCIP 删除约束导致 getDualsolLinear 无法稳定取值。
        _try_set_param(model, "presolving/maxrounds", 0)
        _try_set_param(model, "separating/maxrounds", 0)
        _try_set_param(model, "separating/maxroundsroot", 0)
        _try_set_param(model, "propagating/maxrounds", 0)
        _try_set_param(model, "propagating/maxroundsroot", 0)
        _try_set_param(model, "heuristics/trivial/freq", -1)
        for name, value in self.rmp_params.items():
            _try_set_param(model, name, value)
        # 中文注释：默认只输出 B&P 进度。需要 SCIP 原始 RMP 表格时用 --scip-log 打开。
        if not self.show_scip_log:
            _try_set_param(model, "display/verblevel", 0)
        if self._remaining_time() > 0:
            _try_set_param(model, "limits/time", self._remaining_time())

        lambda_vars = {}
        for column in self.pool.columns:
            route = self.pool.route_for_column(column)
            lambda_vars[column.key] = model.addVar(vtype="C", lb=0.0, ub=1.0, obj=route.cost, name=f"lam[{column.id}]")
        z = {(r, s): model.addVar(vtype="C", lb=0.0, ub=1.0, name=f"z[{r},{s}]") for r in self.R for s in self.S}
        y = {
            r: model.addVar(vtype="C", lb=0.0, ub=1.0, obj=float(self.instance["vehicles"]["F"]), name=f"y[{r}]")
            for r in self.R
        }
        artificial_cover = {
            task_id: model.addVar(vtype="C", lb=0.0, obj=self.artificial_penalty, name=f"art_cover[{task_id}]")
            for task_id in self.tasks
        }
        artificial_branch = {
            idx: model.addVar(vtype="C", lb=0.0, obj=self.artificial_penalty, name=f"art_branch[{idx}]")
            for idx, _ in enumerate(branches)
        }

        cover_cons = {}
        for task_id in self.tasks:
            expr = quicksum(
                lambda_vars[column.key]
                for column in self.pool.columns
                if task_id in self.pool.route_for_column(column).task_set
            )
            cover_cons[task_id] = model.addCons(expr + artificial_cover[task_id] == 1.0, name=f"cover[{task_id}]")

        slot_cons = {}
        for r in self.R:
            for s in self.S:
                expr = quicksum(lambda_vars[column.key] for column in self.pool.columns if column.vehicle == r and column.sortie == s)
                slot_cons[r, s] = model.addCons(expr - z[r, s] == 0.0, name=f"slot[{r},{s}]")
                model.addCons(z[r, s] <= y[r], name=f"slot_requires_vehicle[{r},{s}]")

        route_count_cons = {}
        sortie_limit = float(self.instance["vehicles"]["S_bar"])
        for r in self.R:
            expr = quicksum(lambda_vars[column.key] for column in self.pool.columns if column.vehicle == r)
            # 中文注释：由 slot 容量推出的有效不等式，显式加入可强化 LP 对偶信息。
            route_count_cons[r] = model.addCons(expr - sortie_limit * y[r] <= 0.0, name=f"vehicle_route_count[{r}]")

        vehicle_load_cons = {}
        load_limit = float(self.instance["vehicles"]["Q"]) * sortie_limit
        for r in self.R:
            expr = quicksum(
                self.pool.route_for_column(column).load * lambda_vars[column.key]
                for column in self.pool.columns
                if column.vehicle == r
            )
            # 中文注释：车辆最多执行 S_bar 个 sortie，每个 sortie 载重不超过 Q，因此总载重不超过 S_bar*Q。
            vehicle_load_cons[r] = model.addCons(expr - load_limit * y[r] <= 0.0, name=f"vehicle_load[{r}]")

        vehicle_time_cons = {}
        for r in self.R:
            expr = quicksum(
                self.pool.route_for_column(column).cycle_time * lambda_vars[column.key]
                for column in self.pool.columns
                if column.vehicle == r
            )
            vehicle_time_cons[r] = model.addCons(expr - self.horizon * y[r] <= 0.0, name=f"vehicle_time[{r}]")

        task_vehicle_cons = {}
        for task_id in self.tasks:
            for r in self.R:
                expr = quicksum(
                    lambda_vars[column.key]
                    for column in self.pool.columns
                    if column.vehicle == r and task_id in self.pool.route_for_column(column).task_set
                )
                # 中文注释：强 linking 约束。只要车辆 r 服务了任务 i 的任何比例，y[r] 就必须至少覆盖该比例。
                # 这能消除同一路径在多个 sortie 副本上分数拆分导致的固定车辆成本低估。
                task_vehicle_cons[task_id, r] = model.addCons(
                    expr - y[r] <= 0.0,
                    name=f"task_vehicle_link[{task_id},{r}]",
                )

        for r in self.R:
            for s in self.S[:-1]:
                model.addCons(z[r, s + 1] <= z[r, s], name=f"sortie_sequence[{r},{s}]")
        for r in self.R[:-1]:
            model.addCons(y[r + 1] <= y[r], name=f"vehicle_sequence[{r}]")

        branch_cons = []
        for idx, branch in enumerate(branches):
            expr = quicksum(
                _branch_coefficient_for_column(self.pool, column, branch) * lambda_vars[column.key]
                for column in self.pool.columns
            )
            if branch.sense == "<=":
                cons = model.addCons(expr - artificial_branch[idx] <= branch.rhs, name=f"branch[{idx}]_{branch.short_name()}")
            else:
                cons = model.addCons(expr + artificial_branch[idx] >= branch.rhs, name=f"branch[{idx}]_{branch.short_name()}")
            branch_cons.append(cons)

        data = {
            "lambda": lambda_vars,
            "z": z,
            "y": y,
            "artificial_cover": artificial_cover,
            "artificial_branch": artificial_branch,
            "cover_cons": cover_cons,
            "slot_cons": slot_cons,
            "route_count_cons": route_count_cons,
            "vehicle_load_cons": vehicle_load_cons,
            "vehicle_time_cons": vehicle_time_cons,
            "task_vehicle_cons": task_vehicle_cons,
            "branch_cons": branch_cons,
        }
        return model, data

    def _solve_rmp(self, branches: tuple[BranchConstraint, ...]) -> tuple[str, Any, dict[str, Any]]:
        model, data = self._build_rmp(branches)
        model.optimize()
        self.rmp_solves += 1
        status = str(_safe_call(model.getStatus, "unknown")).lower()
        return status, model, data

    def _duals(self, model, data: dict[str, Any], branches: tuple[BranchConstraint, ...]) -> dict[str, Any]:
        return {
            "cover": {task_id: float(model.getDualsolLinear(cons)) for task_id, cons in data["cover_cons"].items()},
            "slot": {key: float(model.getDualsolLinear(cons)) for key, cons in data["slot_cons"].items()},
            "route_count": {r: float(model.getDualsolLinear(cons)) for r, cons in data["route_count_cons"].items()},
            "vehicle_load": {r: float(model.getDualsolLinear(cons)) for r, cons in data["vehicle_load_cons"].items()},
            "vehicle_time": {r: float(model.getDualsolLinear(cons)) for r, cons in data["vehicle_time_cons"].items()},
            "task_vehicle": {key: float(model.getDualsolLinear(cons)) for key, cons in data["task_vehicle_cons"].items()},
            "branch": {
                branch: float(model.getDualsolLinear(cons))
                for branch, cons in zip(branches, data["branch_cons"])
            },
        }

    def _route_reduced_cost(self, route: Route | dict[str, Any], r: int, s: int, duals: dict[str, Any], branches: tuple[BranchConstraint, ...]) -> float:
        task_set = route.task_set if isinstance(route, Route) else route["task_set"]
        cost = route.cost if isinstance(route, Route) else float(route["cost"])
        load = route.load if isinstance(route, Route) else float(route["load"])
        cycle_time = route.cycle_time if isinstance(route, Route) else float(route["cycle_time"])
        signature = route.tasks if isinstance(route, Route) else tuple(route["tasks"])
        column_key = (signature, int(r), int(s))
        rc = (
            cost
            - sum(float(duals["cover"][int(task_id)]) for task_id in task_set)
            - float(duals["slot"][int(r), int(s)])
            - float(duals["route_count"][int(r)])
            - float(duals["vehicle_load"][int(r)]) * load
            - float(duals["vehicle_time"][int(r)]) * cycle_time
            - sum(float(duals["task_vehicle"][int(task_id), int(r)]) for task_id in task_set)
        )
        for branch in branches:
            rc -= float(duals["branch"][branch]) * _branch_coefficient_for_route(route, branch, column_key)
        return rc

    def _label_priority(self, visited: frozenset[int], cost: float, duals: dict[str, Any]) -> float:
        return cost - sum(float(duals["cover"][task_id]) for task_id in visited)

    def _exact_pricing(self, duals: dict[str, Any], branches: tuple[BranchConstraint, ...]) -> list[tuple[float, dict[str, Any], int, int]] | None:
        self.pricing_calls += 1
        self.exact_pricing_calls += 1
        vehicles = self.instance["vehicles"]
        q_limit = float(vehicles["Q"])
        b_limit = float(vehicles["B_use"])
        horizon = float(vehicles["H"])

        start_label = Label(
            priority=0.0,
            node=0,
            task_id=None,
            parent=None,
            visited=frozenset(),
            time=0.0,
            load=0.0,
            energy=0.0,
            travel_time=0.0,
            cost=0.0,
            service_start_time=None,
        )
        queue = [start_label]
        candidates: list[tuple[float, dict[str, Any], int, int]] = []
        # 中文注释：存在 branch dual 时，不用 label dominance，避免按资源误删对分支约束 reduced cost 有利的路径。
        use_dominance = not branches and max(duals["vehicle_time"].values(), default=0.0) <= 1.0e-9
        nondominated: dict[tuple[int, frozenset[int]], list[Label]] = {(0, frozenset()): [start_label]} if use_dominance else {}
        popped_labels = 0
        last_progress = time.perf_counter()

        while queue:
            if self._time_exceeded():
                return None
            label = heapq.heappop(queue)
            popped_labels += 1
            now = time.perf_counter()
            if self.display_log and now - last_progress >= 5.0:
                self._log(
                    "pricing progress: "
                    f"labels={popped_labels}, queue={len(queue)}, candidates={len(candidates)}, "
                    f"routes={len(self.pool.routes)}, columns={len(self.pool.columns)}"
                )
                last_progress = now
            if use_dominance and label not in nondominated.get((label.node, label.visited), []):
                continue
            for task_id in self.tasks:
                if task_id in label.visited:
                    continue
                segment = self.pairwise[arc_key(label.node, task_id)]
                arrival = label.time + float(segment["tau"])
                start = max(_task_value(self.instance, task_id, "r"), arrival)
                finish = start + _task_value(self.instance, task_id, "sigma")
                if finish > _task_value(self.instance, task_id, "D") + 1.0e-9:
                    continue
                next_load = label.load + _task_value(self.instance, task_id, "d")
                if next_load > q_limit + 1.0e-9:
                    continue
                next_energy = label.energy + float(segment["energy"]) + _task_value(self.instance, task_id, "g")
                if next_energy > b_limit + 1.0e-9:
                    continue
                return_segment = self.pairwise[arc_key(task_id, 0)]
                return_time = finish + float(return_segment["tau"])
                total_energy = next_energy + float(return_segment["energy"])
                if return_time > horizon + 1.0e-9 or total_energy > b_limit + 1.0e-9:
                    continue

                visited = frozenset((*label.visited, task_id))
                next_cost = label.cost + float(segment["cost"]) + _task_value(self.instance, task_id, "c_srv")
                next_label = Label(
                    priority=self._label_priority(visited, next_cost, duals),
                    node=task_id,
                    task_id=task_id,
                    parent=label,
                    visited=visited,
                    time=finish,
                    load=next_load,
                    energy=next_energy,
                    travel_time=label.travel_time + float(segment["tau"]),
                    cost=next_cost,
                    service_start_time=start,
                )
                if use_dominance and self._is_dominated_or_record(next_label, nondominated):
                    continue

                route_data = _route_from_label(self.instance, self.pairwise, next_label)
                signature = tuple(route_data["tasks"])
                for r in self.R:
                    for s in self.S:
                        if self.pool.has_column(signature, r, s):
                            continue
                        rc = self._route_reduced_cost(route_data, r, s, duals, branches)
                        if rc < -self.pricing_eps:
                            candidates.append((rc, route_data, r, s))
                heapq.heappush(queue, next_label)

        candidates.sort(key=lambda item: item[0])
        return candidates[: self.max_columns_per_pricing]

    def _is_dominated_or_record(self, label: Label, nondominated: dict[tuple[int, frozenset[int]], list[Label]]) -> bool:
        key = (label.node, label.visited)
        labels = nondominated.setdefault(key, [])
        for existing in labels:
            if (
                existing.time <= label.time + 1.0e-9
                and existing.load <= label.load + 1.0e-9
                and existing.energy <= label.energy + 1.0e-9
                and existing.cost <= label.cost + 1.0e-9
            ):
                return True
        labels[:] = [
            existing
            for existing in labels
            if not (
                label.time <= existing.time + 1.0e-9
                and label.load <= existing.load + 1.0e-9
                and label.energy <= existing.energy + 1.0e-9
                and label.cost <= existing.cost + 1.0e-9
            )
        ]
        labels.append(label)
        return False

    def _add_priced_columns(self, priced: list[tuple[float, dict[str, Any], int, int]]) -> int:
        added = 0
        for _, route_data, r, s in priced:
            route = self.pool.add_route(route_data)
            if self.pool.add_column(route, r, s, source="pricing"):
                added += 1
        self.generated_columns += added
        return added

    def _current_solution(self, model, data: dict[str, Any]) -> tuple[dict[tuple[tuple[int, ...], int, int], float], float]:
        values = {key: float(model.getVal(var)) for key, var in data["lambda"].items()}
        artificial_sum = sum(float(model.getVal(var)) for var in data["artificial_cover"].values())
        artificial_sum += sum(float(model.getVal(var)) for var in data["artificial_branch"].values())
        return values, artificial_sum

    def solve_node(self, node: SearchNode) -> NodeResult:
        total_generated = 0
        for iteration in range(1, self.max_cg_iterations_per_node + 1):
            if self._time_exceeded():
                return NodeResult(status="TIME_LIMIT")
            self._log(
                f"node {node.id} d={node.depth} cg={iteration}: solve RMP "
                f"(cols={len(self.pool.columns)}, branches={len(node.branches)})"
            )
            status, model, data = self._solve_rmp(node.branches)
            if status not in {"optimal", "bestsollimit"}:
                return NodeResult(status=status.upper())
            bound_text = round_float(_safe_call(model.getObjVal))
            self._log(f"node {node.id} d={node.depth} cg={iteration}: RMP {status}, lp={bound_text}")
            duals = self._duals(model, data, node.branches)
            self._log(f"node {node.id} d={node.depth} cg={iteration}: exact pricing")
            priced = self._exact_pricing(duals, node.branches)
            if priced is None:
                return NodeResult(status="TIME_LIMIT")
            added = self._add_priced_columns(priced)
            total_generated += added
            self.cg_iterations += 1
            cap_note = " batch_cap_hit" if len(priced) >= self.max_columns_per_pricing else ""
            self._log(
                f"node {node.id} d={node.depth} cg={iteration}: pricing priced={len(priced)}, "
                f"added={added}, total_cols={len(self.pool.columns)}{cap_note}"
            )
            if added == 0:
                values, artificial_sum = self._current_solution(model, data)
                bound = float(model.getObjVal())
                return NodeResult(
                    status="OPTIMAL",
                    bound=bound,
                    solution=values,
                    artificial_sum=artificial_sum,
                    cg_iterations=iteration,
                    pricing_calls=iteration,
                    generated_columns=total_generated,
                    rmp_solves=iteration,
                )
        return NodeResult(status="CG_ITERATION_LIMIT", generated_columns=total_generated)

    def _is_integral_solution(self, values: dict[tuple[tuple[int, ...], int, int], float]) -> bool:
        return all(abs(value - round(value)) <= self.integer_tol for value in values.values())

    def _incumbent_from_solution(self, values: dict[tuple[tuple[int, ...], int, int], float], objective: float, node_id: int) -> None:
        selected = []
        used_vehicles = set()
        for column in self.pool.columns:
            value = values.get(column.key, 0.0)
            if value <= 0.5:
                continue
            route = self.pool.route_for_column(column)
            used_vehicles.add(column.vehicle)
            selected.append(
                {
                    "vehicle": column.vehicle,
                    "sortie": column.sortie,
                    "route_id": route.id,
                    "tasks": list(route.tasks),
                    "cost": route.cost,
                    "load": route.load,
                    "energy": route.energy,
                    "return_time": route.return_time,
                    "cycle_time": route.cycle_time,
                    "service_start": route.service_start,
                }
            )
        self.incumbent_value = objective
        self.incumbent_node = node_id
        self.incumbent_solution = {
            "objective": round_float(objective),
            "node_id": node_id,
            "used_vehicles": sorted(used_vehicles),
            "sorties": selected,
        }

    def _arc_flows(self, values: dict[tuple[tuple[int, ...], int, int], float]) -> dict[tuple[int, int], float]:
        flows: dict[tuple[int, int], float] = {}
        for column in self.pool.columns:
            value = values.get(column.key, 0.0)
            if abs(value) <= self.integer_tol:
                continue
            route = self.pool.route_for_column(column)
            for arc in route.arcs:
                flows[arc] = flows.get(arc, 0.0) + value
        return flows

    def _together_flows(self, values: dict[tuple[tuple[int, ...], int, int], float]) -> dict[tuple[int, int], float]:
        # 中文注释：Ryan-Foster 的分支量是“任务 i 和 j 是否被同一条 sortie 路径共同服务”。
        flows: dict[tuple[int, int], float] = {}
        for column in self.pool.columns:
            value = values.get(column.key, 0.0)
            if abs(value) <= self.integer_tol:
                continue
            route = self.pool.route_for_column(column)
            route_tasks = sorted(route.task_set)
            for first_index, i in enumerate(route_tasks):
                for j in route_tasks[first_index + 1 :]:
                    pair = (int(i), int(j))
                    flows[pair] = flows.get(pair, 0.0) + value
        return flows

    def _route_total_flows(self, values: dict[tuple[tuple[int, ...], int, int], float]) -> dict[tuple[int, ...], float]:
        # 中文注释：聚合同一路径在所有 vehicle/sortie 副本上的使用量，先切掉路径副本对称性。
        flows: dict[tuple[int, ...], float] = {}
        for column in self.pool.columns:
            value = values.get(column.key, 0.0)
            if abs(value) <= self.integer_tol:
                continue
            route = self.pool.route_for_column(column)
            flows[route.tasks] = flows.get(route.tasks, 0.0) + value
        return flows

    def _route_vehicle_flows(self, values: dict[tuple[tuple[int, ...], int, int], float]) -> dict[tuple[tuple[int, ...], int], float]:
        # 中文注释：如果路径总使用量已整数，再看该路径分配到哪个 vehicle；这比直接 column 分支强。
        flows: dict[tuple[tuple[int, ...], int], float] = {}
        for column in self.pool.columns:
            value = values.get(column.key, 0.0)
            if abs(value) <= self.integer_tol:
                continue
            route = self.pool.route_for_column(column)
            key = (route.tasks, column.vehicle)
            flows[key] = flows.get(key, 0.0) + value
        return flows

    def _task_vehicle_flows(self, values: dict[tuple[tuple[int, ...], int, int], float]) -> dict[tuple[int, int], float]:
        # 中文注释：任务-车辆流表示任务 i 由车辆 r 服务的比例；整数解中它必须是 0/1。
        flows: dict[tuple[int, int], float] = {}
        for column in self.pool.columns:
            value = values.get(column.key, 0.0)
            if abs(value) <= self.integer_tol:
                continue
            route = self.pool.route_for_column(column)
            for task_id in route.task_set:
                key = (int(task_id), column.vehicle)
                flows[key] = flows.get(key, 0.0) + value
        return flows

    def _most_fractional_pair(self, values: dict[tuple[tuple[int, ...], int, int], float]) -> tuple[tuple[int, int], float] | None:
        best_pair = None
        best_score = -1.0
        for pair, value in self._together_flows(values).items():
            fraction = abs(value - math.floor(value))
            fraction = min(fraction, 1.0 - fraction)
            if fraction > self.integer_tol and fraction > best_score:
                best_score = fraction
                best_pair = (pair, value)
        return best_pair

    def _most_fractional_route(self, values: dict[tuple[tuple[int, ...], int, int], float]) -> tuple[tuple[int, ...], float] | None:
        best_route = None
        best_score = -1.0
        for route_signature, value in self._route_total_flows(values).items():
            fraction = abs(value - math.floor(value))
            fraction = min(fraction, 1.0 - fraction)
            if fraction > self.integer_tol and fraction > best_score:
                best_score = fraction
                best_route = (route_signature, value)
        return best_route

    def _most_fractional_route_vehicle(
        self, values: dict[tuple[tuple[int, ...], int, int], float]
    ) -> tuple[tuple[int, ...], int, float] | None:
        best_route_vehicle = None
        best_score = -1.0
        for (route_signature, vehicle), value in self._route_vehicle_flows(values).items():
            fraction = abs(value - math.floor(value))
            fraction = min(fraction, 1.0 - fraction)
            if fraction > self.integer_tol and fraction > best_score:
                best_score = fraction
                best_route_vehicle = (route_signature, vehicle, value)
        return best_route_vehicle

    def _most_fractional_task_vehicle(self, values: dict[tuple[tuple[int, ...], int, int], float]) -> tuple[int, int, float] | None:
        best_task_vehicle = None
        best_score = -1.0
        for (task_id, vehicle), value in self._task_vehicle_flows(values).items():
            fraction = abs(value - math.floor(value))
            fraction = min(fraction, 1.0 - fraction)
            if fraction > self.integer_tol and fraction > best_score:
                best_score = fraction
                best_task_vehicle = (task_id, vehicle, value)
        return best_task_vehicle

    def _choose_branch(self, values: dict[tuple[tuple[int, ...], int, int], float]) -> tuple[BranchConstraint, BranchConstraint] | None:
        best_pair = self._most_fractional_pair(values)
        if best_pair is not None:
            pair, _ = best_pair
            return (
                BranchConstraint(kind="ryan_foster", sense="<=", rhs=0.0, pair=pair),
                BranchConstraint(kind="ryan_foster", sense=">=", rhs=1.0, pair=pair),
            )

        best_task_vehicle = self._most_fractional_task_vehicle(values)
        if best_task_vehicle is not None:
            task_id, vehicle, value = best_task_vehicle
            return (
                BranchConstraint(
                    kind="task_vehicle",
                    sense="<=",
                    rhs=math.floor(value),
                    task_id=task_id,
                    vehicle=vehicle,
                ),
                BranchConstraint(
                    kind="task_vehicle",
                    sense=">=",
                    rhs=math.ceil(value),
                    task_id=task_id,
                    vehicle=vehicle,
                ),
            )

        # 中文注释：如果没有可用的任务对/任务车辆分支，再退回任务层弧流分支。
        best_arc = None
        best_score = -1.0
        for arc, value in self._arc_flows(values).items():
            fraction = abs(value - math.floor(value))
            fraction = min(fraction, 1.0 - fraction)
            if fraction > self.integer_tol and fraction > best_score:
                best_score = fraction
                best_arc = (arc, value)
        if best_arc is not None:
            arc, value = best_arc
            return (
                BranchConstraint(kind="arc", sense="<=", rhs=math.floor(value), arc=arc),
                BranchConstraint(kind="arc", sense=">=", rhs=math.ceil(value), arc=arc),
            )

        best_route = self._most_fractional_route(values)
        if best_route is not None:
            route_signature, value = best_route
            return (
                BranchConstraint(kind="route_total", sense="<=", rhs=math.floor(value), route_signature=route_signature),
                BranchConstraint(kind="route_total", sense=">=", rhs=math.ceil(value), route_signature=route_signature),
            )

        best_route_vehicle = self._most_fractional_route_vehicle(values)
        if best_route_vehicle is not None:
            route_signature, vehicle, value = best_route_vehicle
            return (
                BranchConstraint(
                    kind="route_vehicle",
                    sense="<=",
                    rhs=math.floor(value),
                    route_signature=route_signature,
                    vehicle=vehicle,
                ),
                BranchConstraint(
                    kind="route_vehicle",
                    sense=">=",
                    rhs=math.ceil(value),
                    route_signature=route_signature,
                    vehicle=vehicle,
                ),
            )

        # 中文注释：若所有聚合分支都已整数但列变量仍分数，最后才用单列分支兜底。
        best_column = None
        best_score = -1.0
        for key, value in values.items():
            fraction = abs(value - math.floor(value))
            fraction = min(fraction, 1.0 - fraction)
            if fraction > self.integer_tol and fraction > best_score:
                best_score = fraction
                best_column = (key, value)
        if best_column is None:
            return None
        key, value = best_column
        return (
            BranchConstraint(kind="column", sense="<=", rhs=math.floor(value), column_key=key),
            BranchConstraint(kind="column", sense=">=", rhs=math.ceil(value), column_key=key),
        )

    def _global_dual_bound(self, open_nodes: list[SearchNode]) -> float | None:
        if open_nodes:
            return min(node.lower_bound for node in open_nodes)
        return self.incumbent_value

    def _relative_gap(self, dual_bound: float | None) -> float | None:
        if self.incumbent_value is None or dual_bound is None:
            return None
        if abs(self.incumbent_value) <= self.integer_tol:
            return 0.0 if abs(dual_bound - self.incumbent_value) <= self.integer_tol else None
        return max(0.0, (self.incumbent_value - dual_bound) / abs(self.incumbent_value))

    def _bound_snapshot(self, open_nodes: list[SearchNode], candidate_bound: float | None = None) -> tuple[float | None, float | None]:
        bounds = [node.lower_bound for node in open_nodes]
        if candidate_bound is not None:
            bounds.append(candidate_bound)
        dual_bound = min(bounds) if bounds else self.incumbent_value
        return dual_bound, self._relative_gap(dual_bound)

    def solve(self) -> BPResult:
        self.started = time.perf_counter()
        self._log(
            f"start instance={self.instance.get('name', 'instance')} tasks={len(self.tasks)} "
            f"vehicles={len(self.R)} sorties_per_vehicle={len(self.S)} time_limit={self.time_limit:g}s "
            f"max_nodes={self.max_nodes} max_cols_per_pricing={self.max_columns_per_pricing}"
        )
        self.initialize_columns()
        self._log(f"initial columns={len(self.pool.columns)} initial_routes={len(self.pool.routes)}")
        root = self._new_node(depth=0, branches=tuple(), lower_bound=-math.inf)
        open_nodes = [root]

        while open_nodes and self.nodes_processed < self.max_nodes and not self._time_exceeded():
            node = heapq.heappop(open_nodes)
            self._log(
                f"process node {node.id} d={node.depth}: node_lb={round_float(node.lower_bound)}, "
                f"open={len(open_nodes)}, incumbent={round_float(self.incumbent_value)}"
            )
            if self.incumbent_value is not None and node.lower_bound >= self.incumbent_value - self.integer_tol:
                continue
            node_result = self.solve_node(node)
            self.nodes_processed += 1
            if node_result.status in {"TIME_LIMIT", "CG_ITERATION_LIMIT"}:
                # 中文注释：节点内部中断时，该节点仍未被完整定价和分支；最终全局下界必须保留它的已知下界。
                heapq.heappush(open_nodes, node)
                self._log(
                    f"stop inside node {node.id}: status={node_result.status}, "
                    f"keep_node_lb={round_float(node.lower_bound)}, open={len(open_nodes)}"
                )
                self.termination_status = node_result.status
                break
            if node_result.status != "OPTIMAL" or node_result.bound is None or node_result.solution is None:
                self._log(f"node={node.id} depth={node.depth} status={node_result.status}")
                continue
            dual_snapshot, gap_snapshot = self._bound_snapshot(open_nodes, node_result.bound)
            self._log(
                f"node {node.id} d={node.depth}: lp={node_result.bound:.6f}, "
                f"global_lb={round_float(dual_snapshot)}, incumbent={round_float(self.incumbent_value)}, "
                f"bp_gap={round_float(gap_snapshot)}, open={len(open_nodes)}"
            )
            if node.depth == 0 and self.root_relaxation is None and node_result.artificial_sum <= self.integer_tol:
                self.root_relaxation = node_result.bound
            if node_result.artificial_sum > self.integer_tol:
                self._log(f"node={node.id} depth={node.depth} artificial={node_result.artificial_sum:.6g} fathom=infeasible")
                continue
            if self.incumbent_value is not None and node_result.bound >= self.incumbent_value - self.integer_tol:
                continue
            if self._is_integral_solution(node_result.solution):
                if self.incumbent_value is None or node_result.bound < self.incumbent_value - self.integer_tol:
                    self._incumbent_from_solution(node_result.solution, node_result.bound, node.id)
                    self._log(f"incumbent node={node.id} value={node_result.bound:.6f}")
                continue
            branch_pair = self._choose_branch(node_result.solution)
            if branch_pair is None:
                # 中文注释：理论上不会出现；若出现，保守地把当前 LP 当作候选整数解处理。
                if self.incumbent_value is None or node_result.bound < self.incumbent_value - self.integer_tol:
                    self._incumbent_from_solution(node_result.solution, node_result.bound, node.id)
                continue
            for branch in branch_pair:
                child = self._new_node(
                    depth=node.depth + 1,
                    branches=(*node.branches, branch),
                    lower_bound=node_result.bound,
                )
                heapq.heappush(open_nodes, child)
            left_branch, right_branch = branch_pair
            self._log(
                f"branch node {node.id}: left={left_branch.short_name()}, right={right_branch.short_name()}"
            )
            dual_snapshot, gap_snapshot = self._bound_snapshot(open_nodes)
            self._log(
                f"tree after node {node.id}: global_lb={round_float(dual_snapshot)}, "
                f"incumbent={round_float(self.incumbent_value)}, bp_gap={round_float(gap_snapshot)}, open={len(open_nodes)}"
            )

        elapsed = time.perf_counter() - self.started
        dual_bound = self._global_dual_bound(open_nodes)
        if self.incumbent_value is None:
            gap = None
        elif dual_bound is None or abs(self.incumbent_value) <= self.integer_tol:
            gap = 0.0 if dual_bound == self.incumbent_value else None
        else:
            gap = max(0.0, (self.incumbent_value - dual_bound) / abs(self.incumbent_value))
        if self.termination_status is not None:
            status = self.termination_status
        elif self.nodes_processed >= self.max_nodes and open_nodes:
            status = "NODE_LIMIT"
        else:
            status = "OPTIMAL" if self.incumbent_value is not None and not open_nodes and not self._time_exceeded() else "TIME_LIMIT"
        if self.incumbent_value is None and not open_nodes:
            status = "INFEASIBLE"

        if self.log_path is not None:
            ensure_dir(self.log_path.parent)
            self.log_path.write_text("\n".join(self.log_lines) + ("\n" if self.log_lines else ""), encoding="utf-8")

        return BPResult(
            instance=str(self.instance.get("name", "instance")),
            task_count=len(self.tasks),
            vehicle_count=len(self.R),
            sortie_count=len(self.S),
            status=status,
            primal_bound=round_float(self.incumbent_value),
            dual_bound=round_float(dual_bound),
            gap=round_float(gap),
            solving_time=round_float(elapsed),
            node_count=self.nodes_processed,
            rmp_solves=self.rmp_solves,
            cg_iterations=self.cg_iterations,
            pricing_calls=self.pricing_calls,
            exact_pricing_calls=self.exact_pricing_calls,
            generated_routes=len(self.pool.routes),
            generated_columns=len(self.pool.columns),
            root_relaxation=round_float(self.root_relaxation),
            incumbent_node=self.incumbent_node,
            log_path=str(self.log_path or ""),
            instance_path=self.instance_path,
            seed=self.seed,
        )

    def write_solution(self, path: str | Path) -> None:
        if self.incumbent_solution is None:
            return
        routes = [
            {
                "id": route.id,
                "tasks": list(route.tasks),
                "task_set": sorted(route.task_set),
                "arcs": [list(arc) for arc in route.arcs],
                "cost": route.cost,
                "load": route.load,
                "energy": route.energy,
                "return_time": route.return_time,
                "travel_time": route.travel_time,
                "cycle_time": route.cycle_time,
                "service_start": route.service_start,
            }
            for route in self.pool.routes
        ]
        write_json(path, {"summary": self.incumbent_solution, "routes": routes})


def solve_bp_no_ml(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    *,
    instance_path: str | Path,
    time_limit: float,
    log_path: str | Path,
    solution_path: str | Path | None = None,
    pricing_eps: float = 1.0e-6,
    integer_tol: float = 1.0e-6,
    max_nodes: int = 100000,
    max_cg_iterations_per_node: int = 200,
    max_columns_per_pricing: int = 200,
    artificial_penalty: float = 1.0e6,
    rmp_params: dict[str, Any] | None = None,
    seed: int | None = None,
    log_level: str = "progress",
) -> BPResult:
    solver = BranchPriceSolver(
        instance,
        pairwise,
        time_limit=time_limit,
        pricing_eps=pricing_eps,
        integer_tol=integer_tol,
        max_nodes=max_nodes,
        max_cg_iterations_per_node=max_cg_iterations_per_node,
        max_columns_per_pricing=max_columns_per_pricing,
        artificial_penalty=artificial_penalty,
        rmp_params=rmp_params,
        log_path=log_path,
        instance_path=instance_path,
        seed=seed,
        log_level=log_level,
    )
    result = solver.solve()
    if solution_path is not None:
        solver.write_solution(solution_path)
    return result
