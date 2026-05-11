"""中文摘要：本文件实现车辆日程列的 no-ML 分支定价。列表示一辆车执行的一组 sortie，主问题只保留任务覆盖和车辆数约束。"""

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
class Schedule:
    id: int
    route_ids: tuple[int, ...]
    key: tuple[tuple[int, ...], ...]
    task_set: frozenset[int]
    cost: float
    route_cost: float
    cycle_time: float
    source: str


@dataclass(frozen=True)
class BranchConstraint:
    # 中文注释：这些分支都定义在车辆日程列上，不依赖具体车辆编号，因此不会引入路径-slot 对称性。
    kind: str
    sense: str
    rhs: float
    pair: tuple[int, int] | None = None
    arc: tuple[int, int] | None = None
    route_signature: tuple[int, ...] | None = None
    schedule_key: tuple[tuple[int, ...], ...] | None = None

    def short_name(self) -> str:
        if self.kind == "ryan_foster" and self.pair is not None:
            i, j = self.pair
            return f"rf_{i}_{j}_{self.sense}_{self.rhs:g}"
        if self.kind == "arc" and self.arc is not None:
            i, j = self.arc
            return f"arc_{i}_{j}_{self.sense}_{self.rhs:g}"
        if self.kind == "route_total" and self.route_signature is not None:
            route_text = "_".join(str(task) for task in self.route_signature) or "empty"
            return f"route_{route_text}_{self.sense}_{self.rhs:g}"
        if self.kind == "schedule" and self.schedule_key is not None:
            sched_text = "__".join("_".join(str(task) for task in route) for route in self.schedule_key) or "empty"
            return f"sched_{sched_text}_{self.sense}_{self.rhs:g}"
        return f"branch_{self.kind}_{self.sense}_{self.rhs:g}"


@dataclass(order=True)
class SearchNode:
    lower_bound: float
    id: int = field(compare=False)
    depth: int = field(compare=False)
    branches: tuple[BranchConstraint, ...] = field(compare=False)


@dataclass(order=True)
class IntegratedPricingLabel:
    # 中文注释：一体化 pricing 标签。它同时描述已闭合的 sortie 和当前正在扩展的 sortie。
    priority: float
    route_ids: tuple[int, ...] = field(compare=False)
    task_set: frozenset[int] = field(compare=False)
    used_sorties: int = field(compare=False)
    cycle_time: float = field(compare=False)
    closed_reduced_cost: float = field(compare=False)
    current_node: int = field(compare=False)
    route_tasks: tuple[int, ...] = field(compare=False)
    route_time: float = field(compare=False)
    route_load: float = field(compare=False)
    route_energy: float = field(compare=False)
    route_cost: float = field(compare=False)
    route_travel_time: float = field(compare=False)
    route_reduced_cost: float = field(compare=False)

    @property
    def has_open_route(self) -> bool:
        return bool(self.route_tasks)


@dataclass
class NodeResult:
    status: str
    bound: float | None = None
    solution: dict[tuple[tuple[int, ...], ...], float] | None = None
    artificial_sum: float = 0.0


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


class SchedulePool:
    """中文注释：保存 sortie 路径和车辆日程列。日程列是一辆车可执行的若干条互不重叠路径。"""

    def __init__(self, max_routes_per_schedule: int, horizon: float, fixed_cost: float):
        self.max_routes_per_schedule = int(max_routes_per_schedule)
        self.horizon = float(horizon)
        self.fixed_cost = float(fixed_cost)
        self.routes: list[Route] = []
        self.route_by_signature: dict[tuple[int, ...], Route] = {}
        self.schedules: list[Schedule] = []
        self.schedule_keys: set[tuple[tuple[int, ...], ...]] = set()

    def add_route(self, route_data: dict[str, Any]) -> Route:
        signature = tuple(int(task) for task in route_data["tasks"])
        existing = self.route_by_signature.get(signature)
        if existing is not None:
            return existing
        route = Route(
            id=len(self.routes),
            tasks=signature,
            task_set=frozenset(int(task) for task in route_data["task_set"]),
            arcs=tuple((int(i), int(j)) for i, j in route_data["arcs"]),
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

    def _normalize_route_ids(self, route_ids: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(sorted(route_ids, key=lambda route_id: self.routes[route_id].tasks))

    def schedule_key_from_route_ids(self, route_ids: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
        return tuple(self.routes[route_id].tasks for route_id in self._normalize_route_ids(route_ids))

    def has_schedule_key(self, key: tuple[tuple[int, ...], ...]) -> bool:
        return key in self.schedule_keys

    def add_schedule(self, routes: list[Route] | tuple[Route, ...], source: str) -> bool:
        route_ids = self._normalize_route_ids(tuple(route.id for route in routes))
        if not route_ids or len(route_ids) > self.max_routes_per_schedule:
            return False
        task_set: set[int] = set()
        route_cost = 0.0
        cycle_time = 0.0
        for route_id in route_ids:
            route = self.routes[route_id]
            if task_set.intersection(route.task_set):
                return False
            task_set.update(route.task_set)
            route_cost += route.cost
            cycle_time += route.cycle_time
        if cycle_time > self.horizon + 1.0e-9:
            return False
        key = self.schedule_key_from_route_ids(route_ids)
        if key in self.schedule_keys:
            return False
        schedule = Schedule(
            id=len(self.schedules),
            route_ids=route_ids,
            key=key,
            task_set=frozenset(task_set),
            cost=self.fixed_cost + route_cost,
            route_cost=route_cost,
            cycle_time=cycle_time,
            source=source,
        )
        self.schedules.append(schedule)
        self.schedule_keys.add(key)
        return True

    def routes_for_schedule(self, schedule: Schedule) -> list[Route]:
        return [self.routes[route_id] for route_id in schedule.route_ids]


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


def _resident_memory_mb() -> float | None:
    try:
        status = Path("/proc/self/status").read_text(encoding="utf-8")
    except OSError:
        return None
    for line in status.splitlines():
        if line.startswith("VmRSS:"):
            parts = line.split()
            if len(parts) >= 2:
                return float(parts[1]) / 1024.0
    return None


def _branch_coefficient_for_schedule(pool: SchedulePool, schedule: Schedule, branch: BranchConstraint) -> float:
    routes = pool.routes_for_schedule(schedule)
    if branch.kind == "ryan_foster" and branch.pair is not None:
        i, j = branch.pair
        return float(any(i in route.task_set and j in route.task_set for route in routes))
    if branch.kind == "arc" and branch.arc is not None:
        return float(sum(1 for route in routes for arc in route.arcs if arc == branch.arc))
    if branch.kind == "route_total" and branch.route_signature is not None:
        return 1.0 if branch.route_signature in schedule.key else 0.0
    if branch.kind == "schedule" and branch.schedule_key is not None:
        return 1.0 if branch.schedule_key == schedule.key else 0.0
    return 0.0


def _branch_coefficient_for_route(route: Route | dict[str, Any], branch: BranchConstraint) -> float:
    task_set = route.task_set if isinstance(route, Route) else route["task_set"]
    arcs = route.arcs if isinstance(route, Route) else tuple(route["arcs"])
    signature = route.tasks if isinstance(route, Route) else tuple(route["tasks"])
    if branch.kind == "ryan_foster" and branch.pair is not None:
        i, j = branch.pair
        return 1.0 if i in task_set and j in task_set else 0.0
    if branch.kind == "arc" and branch.arc is not None:
        return float(sum(1 for arc in arcs if arc == branch.arc))
    if branch.kind == "route_total" and branch.route_signature is not None:
        return 1.0 if signature == branch.route_signature else 0.0
    return 0.0


class BranchPriceSolver:
    """中文注释：车辆日程列 B&P。每个列自带固定车辆成本，减少路径-slot formulation 的对称退化。"""

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
        memory_limit_mb: float | None = None,
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
        self.memory_limit_mb = float(memory_limit_mb) if memory_limit_mb is not None else None
        self.artificial_penalty = float(artificial_penalty)
        self.rmp_params = rmp_params or {}
        self.log_path = Path(log_path) if log_path is not None else None
        self.instance_path = str(instance_path)
        self.seed = seed
        self.log_level = log_level
        self.display_log = log_level != "quiet"
        self.show_scip_log = log_level == "scip"
        self.tasks = task_ids(instance)
        self.vehicle_limit = int(vehicles["R_bar"])
        self.sortie_limit = int(vehicles["S_bar"])
        self.horizon = float(vehicles["H"])
        self.fixed_cost = float(vehicles["F"])
        self.pool = SchedulePool(self.sortie_limit, self.horizon, self.fixed_cost)

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
        self.log_handle = None

    def _log(self, message: str, level: str = "progress") -> None:
        if self.log_handle is not None:
            self.log_handle.write(message + "\n")
            self.log_handle.flush()
        if self.display_log and level != "debug":
            elapsed = time.perf_counter() - self.started if self.started else 0.0
            print(f"[B&P {elapsed:8.2f}s] {message}", flush=True)

    def _open_log(self) -> None:
        if self.log_path is None:
            return
        ensure_dir(self.log_path.parent)
        self.log_handle = self.log_path.open("w", encoding="utf-8")

    def _close_log(self) -> None:
        if self.log_handle is not None:
            self.log_handle.close()
            self.log_handle = None

    def _remaining_time(self) -> float:
        return max(0.0, self.time_limit - (time.perf_counter() - self.started))

    def _time_exceeded(self) -> bool:
        return self._remaining_time() <= 0.0

    def _memory_exceeded(self) -> bool:
        if self.memory_limit_mb is None:
            return False
        rss_mb = _resident_memory_mb()
        return rss_mb is not None and rss_mb >= self.memory_limit_mb

    def _new_node(self, depth: int, branches: tuple[BranchConstraint, ...], lower_bound: float) -> SearchNode:
        node = SearchNode(lower_bound=float(lower_bound), id=self.next_node_id, depth=depth, branches=branches)
        self.next_node_id += 1
        return node

    def initialize_columns(self) -> None:
        # 中文注释：先放入单任务日程列。多 sortie 日程由 pricing 自动生成，人工列只兜底 RMP 可行性。
        for task_id in self.tasks:
            route_data = evaluate_sequence(self.instance, self.pairwise, (task_id,))
            if route_data is None:
                raise ValueError(f"任务 {task_id} 不能形成单任务可行路径")
            route = self.pool.add_route(route_data)
            self.pool.add_schedule((route,), source="single_task_schedule")

    def _build_rmp(self, branches: tuple[BranchConstraint, ...]):
        from pyscipopt import Model, quicksum

        model = Model(f"schedule_rmp_{self.instance.get('name', 'instance')}")
        _try_set_param(model, "presolving/maxrounds", 0)
        _try_set_param(model, "separating/maxrounds", 0)
        _try_set_param(model, "separating/maxroundsroot", 0)
        _try_set_param(model, "propagating/maxrounds", 0)
        _try_set_param(model, "propagating/maxroundsroot", 0)
        _try_set_param(model, "heuristics/trivial/freq", -1)
        for name, value in self.rmp_params.items():
            _try_set_param(model, name, value)
        if not self.show_scip_log:
            _try_set_param(model, "display/verblevel", 0)
        if self._remaining_time() > 0:
            _try_set_param(model, "limits/time", self._remaining_time())
        if self.memory_limit_mb is not None:
            _try_set_param(model, "limits/memory", self.memory_limit_mb)

        lambda_vars = {
            schedule.key: model.addVar(vtype="C", lb=0.0, ub=1.0, obj=schedule.cost, name=f"sched[{schedule.id}]")
            for schedule in self.pool.schedules
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
                lambda_vars[schedule.key]
                for schedule in self.pool.schedules
                if task_id in schedule.task_set
            )
            cover_cons[task_id] = model.addCons(expr + artificial_cover[task_id] == 1.0, name=f"cover[{task_id}]")

        vehicle_count_cons = model.addCons(
            quicksum(lambda_vars[schedule.key] for schedule in self.pool.schedules) <= self.vehicle_limit,
            name="vehicle_count",
        )

        branch_cons = []
        for idx, branch in enumerate(branches):
            expr = quicksum(
                _branch_coefficient_for_schedule(self.pool, schedule, branch) * lambda_vars[schedule.key]
                for schedule in self.pool.schedules
            )
            if branch.sense == "<=":
                cons = model.addCons(expr - artificial_branch[idx] <= branch.rhs, name=f"branch[{idx}]_{branch.short_name()}")
            else:
                cons = model.addCons(expr + artificial_branch[idx] >= branch.rhs, name=f"branch[{idx}]_{branch.short_name()}")
            branch_cons.append(cons)

        data = {
            "lambda": lambda_vars,
            "artificial_cover": artificial_cover,
            "artificial_branch": artificial_branch,
            "cover_cons": cover_cons,
            "vehicle_count_cons": vehicle_count_cons,
            "branch_cons": branch_cons,
        }
        return model, data

    def _solve_rmp(self, branches: tuple[BranchConstraint, ...]):
        model, data = self._build_rmp(branches)
        model.optimize()
        self.rmp_solves += 1
        return str(_safe_call(model.getStatus, "unknown")).lower(), model, data

    def _duals(self, model, data: dict[str, Any], branches: tuple[BranchConstraint, ...]) -> dict[str, Any]:
        return {
            "cover": {task_id: float(model.getDualsolLinear(cons)) for task_id, cons in data["cover_cons"].items()},
            "vehicle_count": float(model.getDualsolLinear(data["vehicle_count_cons"])),
            "branch": {branch: float(model.getDualsolLinear(cons)) for branch, cons in zip(branches, data["branch_cons"])},
        }

    def _route_pricing_contribution(self, route: Route | dict[str, Any], duals: dict[str, Any], branches: tuple[BranchConstraint, ...]) -> float:
        task_set = route.task_set if isinstance(route, Route) else route["task_set"]
        cost = route.cost if isinstance(route, Route) else float(route["cost"])
        value = cost - sum(float(duals["cover"][int(task_id)]) for task_id in task_set)
        for branch in branches:
            if branch.kind in {"ryan_foster", "arc", "route_total"}:
                value -= float(duals["branch"][branch]) * _branch_coefficient_for_route(route, branch)
        return value

    def _schedule_reduced_cost(self, routes: tuple[Route, ...], key: tuple[tuple[int, ...], ...], duals: dict[str, Any], branches: tuple[BranchConstraint, ...]) -> float:
        rc = self.fixed_cost - float(duals["vehicle_count"])
        rc += sum(self._route_pricing_contribution(route, duals, branches) for route in routes)
        for branch in branches:
            if branch.kind == "schedule" and branch.schedule_key == key:
                rc -= float(duals["branch"][branch])
        return rc

    def _integrated_label_key(self, label: IntegratedPricingLabel, exact_route_order: bool) -> tuple[Any, ...]:
        if label.has_open_route:
            route_state = label.route_tasks if exact_route_order else frozenset(label.route_tasks)
            return ("open", label.task_set, route_state, label.current_node)
        return ("closed", label.task_set)

    def _record_integrated_label(
        self,
        label: IntegratedPricingLabel,
        nondominated: dict[tuple[Any, ...], list[IntegratedPricingLabel]],
        exact_route_order: bool,
    ) -> bool:
        # 中文注释：一体化标签 dominance 只在未来可扩展集合相同的状态内使用，保证不会因为剪枝漏掉负列。
        key = self._integrated_label_key(label, exact_route_order)
        labels = nondominated.setdefault(key, [])
        label_rc = label.closed_reduced_cost + label.route_reduced_cost
        for existing in labels:
            existing_rc = existing.closed_reduced_cost + existing.route_reduced_cost
            if (
                existing.used_sorties <= label.used_sorties
                and existing.cycle_time <= label.cycle_time + 1.0e-9
                and existing.route_time <= label.route_time + 1.0e-9
                and existing.route_load <= label.route_load + 1.0e-9
                and existing.route_energy <= label.route_energy + 1.0e-9
                and existing_rc <= label_rc + self.pricing_eps
            ):
                return False
        labels[:] = [
            existing
            for existing in labels
            if not (
                label.used_sorties <= existing.used_sorties
                and label.cycle_time <= existing.cycle_time + 1.0e-9
                and label.route_time <= existing.route_time + 1.0e-9
                and label.route_load <= existing.route_load + 1.0e-9
                and label.route_energy <= existing.route_energy + 1.0e-9
                and label_rc <= existing.closed_reduced_cost + existing.route_reduced_cost + self.pricing_eps
            )
        ]
        labels.append(label)
        return True

    def _partial_route_reduced_cost_increment(
        self,
        from_node: int,
        task_id: int,
        route_task_set: frozenset[int],
        segment: dict[str, Any],
        duals: dict[str, Any],
        branches: tuple[BranchConstraint, ...],
    ) -> float:
        value = float(segment["cost"]) + _task_value(self.instance, task_id, "c_srv") - float(duals["cover"][task_id])
        for branch in branches:
            branch_dual = float(duals["branch"][branch])
            if branch.kind == "arc" and branch.arc == (from_node, task_id):
                value -= branch_dual
            elif branch.kind == "ryan_foster" and branch.pair is not None and task_id in branch.pair:
                other = branch.pair[0] if branch.pair[1] == task_id else branch.pair[1]
                if other in route_task_set:
                    value -= branch_dual
        return value

    def _route_data_from_integrated_label(self, label: IntegratedPricingLabel) -> dict[str, Any] | None:
        if not label.route_tasks:
            return None
        # 中文注释：service_start 不存进 label，避免大量 Python 元组常驻内存；闭合 route 时按序列重算。
        return evaluate_sequence(self.instance, self.pairwise, label.route_tasks)

    def _exact_pricing(self, duals: dict[str, Any], branches: tuple[BranchConstraint, ...]) -> list[tuple[float, tuple[Route, ...]]] | None:
        self.pricing_calls += 1
        self.exact_pricing_calls += 1
        has_schedule_branch = any(branch.kind == "schedule" for branch in branches)
        exact_route_order = any(branch.kind in {"route_total", "schedule"} for branch in branches)
        candidates: list[tuple[float, tuple[Route, ...]]] = []
        seen_keys: set[tuple[tuple[int, ...], ...]] = set()
        base = self.fixed_cost - float(duals["vehicle_count"])
        vehicles = self.instance["vehicles"]
        q_limit = float(vehicles["Q"])
        b_limit = float(vehicles["B_use"])

        try:
            def label_priority(closed_rc: float, route_rc: float) -> float:
                # 中文注释：priority 只影响找列顺序，不参与证明无负列。
                return closed_rc + route_rc

            root = IntegratedPricingLabel(
                priority=label_priority(base, 0.0),
                route_ids=tuple(),
                task_set=frozenset(),
                used_sorties=0,
                cycle_time=0.0,
                closed_reduced_cost=base,
                current_node=0,
                route_tasks=tuple(),
                route_time=0.0,
                route_load=0.0,
                route_energy=0.0,
                route_cost=0.0,
                route_travel_time=0.0,
                route_reduced_cost=0.0,
            )
            queue = [root]
            nondominated: dict[tuple[Any, ...], list[IntegratedPricingLabel]] = {}
            if not has_schedule_branch:
                self._record_integrated_label(root, nondominated, exact_route_order)
            popped_labels = 0
            last_progress = time.perf_counter()

            while queue:
                if self._time_exceeded():
                    raise TimeoutError
                if popped_labels % 1000 == 0 and self._memory_exceeded():
                    raise MemoryError
                label = heapq.heappop(queue)
                popped_labels += 1
                now = time.perf_counter()
                if now - last_progress >= 5.0:
                    nondom_count = sum(len(labels) for labels in nondominated.values())
                    self._log(
                        f"pricing integrated-labels: labels={popped_labels}, queue={len(queue)}, "
                        f"candidates={len(candidates)}, routes={len(self.pool.routes)}, nondom={nondom_count}"
                    )
                    last_progress = now

                if label.has_open_route:
                    route_data = self._route_data_from_integrated_label(label)
                    if route_data is not None:
                        route = self.pool.add_route(route_data)
                        next_route_ids = (*label.route_ids, route.id)
                        route_ids = self.pool._normalize_route_ids(next_route_ids)
                        key = self.pool.schedule_key_from_route_ids(route_ids)
                        route_tuple = tuple(self.pool.routes[route_id] for route_id in route_ids)
                        full_rc = self._schedule_reduced_cost(route_tuple, key, duals, branches)
                        if key not in seen_keys and not self.pool.has_schedule_key(key) and full_rc < -self.pricing_eps:
                            seen_keys.add(key)
                            candidates.append((full_rc, route_tuple))
                            # 中文注释：找到一批负 reduced-cost 日程即可返回；后续 CG 迭代会继续调用 exact pricing。
                            if len(candidates) >= self.max_columns_per_pricing:
                                raise StopIteration

                        next_used = label.used_sorties + 1
                        next_cycle = label.cycle_time + route.cycle_time
                        if (
                            next_used < self.sortie_limit
                            and next_cycle <= self.horizon + 1.0e-9
                            and len(label.task_set) < len(self.tasks)
                        ):
                            route_contribution = self._route_pricing_contribution(route, duals, branches)
                            closed_label = IntegratedPricingLabel(
                                priority=label_priority(label.closed_reduced_cost + route_contribution, 0.0),
                                route_ids=route_ids,
                                task_set=label.task_set,
                                used_sorties=next_used,
                                cycle_time=next_cycle,
                                closed_reduced_cost=label.closed_reduced_cost + route_contribution,
                                current_node=0,
                                route_tasks=tuple(),
                                route_time=0.0,
                                route_load=0.0,
                                route_energy=0.0,
                                route_cost=0.0,
                                route_travel_time=0.0,
                                route_reduced_cost=0.0,
                            )
                            if has_schedule_branch or self._record_integrated_label(closed_label, nondominated, exact_route_order):
                                heapq.heappush(queue, closed_label)

                if label.used_sorties >= self.sortie_limit:
                    continue

                for task_id in self.tasks:
                    if task_id in label.task_set:
                        continue
                    from_node = label.current_node if label.has_open_route else 0
                    segment = self.pairwise[arc_key(from_node, task_id)]
                    arrival = label.route_time + float(segment["tau"])
                    start = max(_task_value(self.instance, task_id, "r"), arrival)
                    finish = start + _task_value(self.instance, task_id, "sigma")
                    if finish > _task_value(self.instance, task_id, "D") + 1.0e-9:
                        continue
                    next_load = label.route_load + _task_value(self.instance, task_id, "d")
                    if next_load > q_limit + 1.0e-9:
                        continue
                    next_energy = label.route_energy + float(segment["energy"]) + _task_value(self.instance, task_id, "g")
                    if next_energy > b_limit + 1.0e-9:
                        continue
                    return_segment = self.pairwise[arc_key(task_id, 0)]
                    return_time = finish + float(return_segment["tau"])
                    total_energy = next_energy + float(return_segment["energy"])
                    if return_time > self.horizon + 1.0e-9 or total_energy > b_limit + 1.0e-9:
                        continue
                    route_cycle_lower = return_time + total_energy / float(vehicles["rho"])
                    if label.cycle_time + route_cycle_lower > self.horizon + 1.0e-9:
                        continue
                    route_task_set = frozenset(label.route_tasks)
                    next_route_rc = label.route_reduced_cost + self._partial_route_reduced_cost_increment(
                        from_node,
                        task_id,
                        route_task_set,
                        segment,
                        duals,
                        branches,
                    )
                    next_label = IntegratedPricingLabel(
                        priority=label_priority(label.closed_reduced_cost, next_route_rc),
                        route_ids=label.route_ids,
                        task_set=frozenset((*label.task_set, task_id)),
                        used_sorties=label.used_sorties,
                        cycle_time=label.cycle_time,
                        closed_reduced_cost=label.closed_reduced_cost,
                        current_node=task_id,
                        route_tasks=(*label.route_tasks, task_id),
                        route_time=finish,
                        route_load=next_load,
                        route_energy=next_energy,
                        route_cost=label.route_cost + float(segment["cost"]) + _task_value(self.instance, task_id, "c_srv"),
                        route_travel_time=label.route_travel_time + float(segment["tau"]),
                        route_reduced_cost=next_route_rc,
                    )
                    if not has_schedule_branch and not self._record_integrated_label(next_label, nondominated, exact_route_order):
                        continue
                    heapq.heappush(queue, next_label)
        except StopIteration:
            candidates.sort(key=lambda item: item[0])
            return candidates[: self.max_columns_per_pricing]
        except MemoryError:
            self.termination_status = "MEMORY_LIMIT"
            return None
        except TimeoutError:
            self.termination_status = "TIME_LIMIT"
            return None
        candidates.sort(key=lambda item: item[0])
        return candidates[: self.max_columns_per_pricing]

    def _add_priced_schedules(self, priced: list[tuple[float, tuple[Route, ...]]]) -> int:
        added = 0
        for _, routes in priced:
            if self.pool.add_schedule(routes, source="pricing"):
                added += 1
        self.generated_columns += added
        return added

    def _current_solution(self, model, data: dict[str, Any]) -> tuple[dict[tuple[tuple[int, ...], ...], float], float]:
        values = {key: float(model.getVal(var)) for key, var in data["lambda"].items()}
        artificial_sum = sum(float(model.getVal(var)) for var in data["artificial_cover"].values())
        artificial_sum += sum(float(model.getVal(var)) for var in data["artificial_branch"].values())
        return values, artificial_sum

    def solve_node(self, node: SearchNode) -> NodeResult:
        for iteration in range(1, self.max_cg_iterations_per_node + 1):
            if self._time_exceeded():
                return NodeResult(status="TIME_LIMIT")
            if self._memory_exceeded():
                return NodeResult(status="MEMORY_LIMIT")
            self._log(f"node {node.id} d={node.depth} cg={iteration}: solve RMP (schedules={len(self.pool.schedules)}, branches={len(node.branches)})")
            status, model, data = self._solve_rmp(node.branches)
            if status not in {"optimal", "bestsollimit"}:
                return NodeResult(status=status.upper())
            self._log(f"node {node.id} d={node.depth} cg={iteration}: RMP {status}, lp={round_float(_safe_call(model.getObjVal))}")
            duals = self._duals(model, data, node.branches)
            self._log(f"node {node.id} d={node.depth} cg={iteration}: exact schedule-labeling pricing")
            priced = self._exact_pricing(duals, node.branches)
            if priced is None:
                return NodeResult(status=self.termination_status or "TIME_LIMIT")
            added = self._add_priced_schedules(priced)
            self.cg_iterations += 1
            cap_note = " batch_cap_hit" if len(priced) >= self.max_columns_per_pricing else ""
            self._log(f"node {node.id} d={node.depth} cg={iteration}: pricing priced={len(priced)}, added={added}, schedules={len(self.pool.schedules)}{cap_note}")
            if added == 0:
                values, artificial_sum = self._current_solution(model, data)
                return NodeResult(status="OPTIMAL", bound=float(model.getObjVal()), solution=values, artificial_sum=artificial_sum)
        return NodeResult(status="CG_ITERATION_LIMIT")

    def _is_integral_solution(self, values: dict[tuple[tuple[int, ...], ...], float]) -> bool:
        return all(abs(value - round(value)) <= self.integer_tol for value in values.values())

    def _incumbent_from_solution(self, values: dict[tuple[tuple[int, ...], ...], float], objective: float, node_id: int) -> None:
        schedules = []
        vehicle_index = 1
        for schedule in self.pool.schedules:
            if values.get(schedule.key, 0.0) <= 0.5:
                continue
            routes = []
            for sortie_index, route in enumerate(self.pool.routes_for_schedule(schedule), start=1):
                routes.append(
                    {
                        "vehicle": vehicle_index,
                        "sortie": sortie_index,
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
            schedules.append({"vehicle": vehicle_index, "schedule_id": schedule.id, "cost": schedule.cost, "sorties": routes})
            vehicle_index += 1
        self.incumbent_value = objective
        self.incumbent_node = node_id
        self.incumbent_solution = {
            "objective": round_float(objective),
            "node_id": node_id,
            "used_vehicles": list(range(1, vehicle_index)),
            "vehicle_schedules": schedules,
        }

    def _schedule_values(self, values: dict[tuple[tuple[int, ...], ...], float]) -> list[tuple[Schedule, float]]:
        return [(schedule, values.get(schedule.key, 0.0)) for schedule in self.pool.schedules if abs(values.get(schedule.key, 0.0)) > self.integer_tol]

    def _together_flows(self, values: dict[tuple[tuple[int, ...], ...], float]) -> dict[tuple[int, int], float]:
        flows: dict[tuple[int, int], float] = {}
        for schedule, value in self._schedule_values(values):
            for route in self.pool.routes_for_schedule(schedule):
                tasks = sorted(route.task_set)
                for first, i in enumerate(tasks):
                    for j in tasks[first + 1 :]:
                        flows[(int(i), int(j))] = flows.get((int(i), int(j)), 0.0) + value
        return flows

    def _arc_flows(self, values: dict[tuple[tuple[int, ...], ...], float]) -> dict[tuple[int, int], float]:
        flows: dict[tuple[int, int], float] = {}
        for schedule, value in self._schedule_values(values):
            for route in self.pool.routes_for_schedule(schedule):
                for arc in route.arcs:
                    flows[arc] = flows.get(arc, 0.0) + value
        return flows

    def _route_flows(self, values: dict[tuple[tuple[int, ...], ...], float]) -> dict[tuple[int, ...], float]:
        flows: dict[tuple[int, ...], float] = {}
        for schedule, value in self._schedule_values(values):
            for route in self.pool.routes_for_schedule(schedule):
                flows[route.tasks] = flows.get(route.tasks, 0.0) + value
        return flows

    def _most_fractional(self, items):
        best = None
        best_score = -1.0
        for key, value in items.items():
            fraction = abs(value - math.floor(value))
            fraction = min(fraction, 1.0 - fraction)
            if fraction > self.integer_tol and fraction > best_score:
                best = (key, value)
                best_score = fraction
        return best

    def _choose_branch(self, values: dict[tuple[tuple[int, ...], ...], float]) -> tuple[BranchConstraint, BranchConstraint] | None:
        pair = self._most_fractional(self._together_flows(values))
        if pair is not None:
            key, _ = pair
            return (
                BranchConstraint("ryan_foster", "<=", 0.0, pair=key),
                BranchConstraint("ryan_foster", ">=", 1.0, pair=key),
            )
        arc = self._most_fractional(self._arc_flows(values))
        if arc is not None:
            key, value = arc
            return (
                BranchConstraint("arc", "<=", math.floor(value), arc=key),
                BranchConstraint("arc", ">=", math.ceil(value), arc=key),
            )
        route = self._most_fractional(self._route_flows(values))
        if route is not None:
            key, value = route
            return (
                BranchConstraint("route_total", "<=", math.floor(value), route_signature=key),
                BranchConstraint("route_total", ">=", math.ceil(value), route_signature=key),
            )
        schedule = self._most_fractional(values)
        if schedule is None:
            return None
        key, value = schedule
        return (
            BranchConstraint("schedule", "<=", math.floor(value), schedule_key=key),
            BranchConstraint("schedule", ">=", math.ceil(value), schedule_key=key),
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
        self._open_log()
        try:
            self._log(
                f"start schedule-master instance={self.instance.get('name', 'instance')} tasks={len(self.tasks)} "
                f"vehicle_limit={self.vehicle_limit} sorties_per_vehicle={self.sortie_limit} time_limit={self.time_limit:g}s"
            )
            self.initialize_columns()
            self._log(f"initial schedules={len(self.pool.schedules)} initial_routes={len(self.pool.routes)}")
            open_nodes = [self._new_node(0, tuple(), -math.inf)]

            while open_nodes and self.nodes_processed < self.max_nodes and not self._time_exceeded():
                if self._memory_exceeded():
                    self.termination_status = "MEMORY_LIMIT"
                    break
                node = heapq.heappop(open_nodes)
                self._log(f"process node {node.id} d={node.depth}: node_lb={round_float(node.lower_bound)}, open={len(open_nodes)}, incumbent={round_float(self.incumbent_value)}")
                if self.incumbent_value is not None and node.lower_bound >= self.incumbent_value - self.integer_tol:
                    continue
                node_result = self.solve_node(node)
                self.nodes_processed += 1
                if node_result.status in {"TIME_LIMIT", "CG_ITERATION_LIMIT", "MEMORY_LIMIT"}:
                    heapq.heappush(open_nodes, node)
                    self.termination_status = node_result.status
                    self._log(f"stop inside node {node.id}: status={node_result.status}, open={len(open_nodes)}")
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
                    if self.incumbent_value is None or node_result.bound < self.incumbent_value - self.integer_tol:
                        self._incumbent_from_solution(node_result.solution, node_result.bound, node.id)
                    continue
                for branch in branch_pair:
                    heapq.heappush(open_nodes, self._new_node(node.depth + 1, (*node.branches, branch), node_result.bound))
                left, right = branch_pair
                self._log(f"branch node {node.id}: left={left.short_name()}, right={right.short_name()}")
                dual_snapshot, gap_snapshot = self._bound_snapshot(open_nodes)
                self._log(f"tree after node {node.id}: global_lb={round_float(dual_snapshot)}, incumbent={round_float(self.incumbent_value)}, bp_gap={round_float(gap_snapshot)}, open={len(open_nodes)}")

            elapsed = time.perf_counter() - self.started
            dual_bound = self._global_dual_bound(open_nodes)
            gap = self._relative_gap(dual_bound)
            if self.termination_status is not None:
                status = self.termination_status
            elif self.nodes_processed >= self.max_nodes and open_nodes:
                status = "NODE_LIMIT"
            else:
                status = "OPTIMAL" if self.incumbent_value is not None and not open_nodes and not self._time_exceeded() else "TIME_LIMIT"
            if self.incumbent_value is None and not open_nodes:
                status = "INFEASIBLE"
            return BPResult(
                instance=str(self.instance.get("name", "instance")),
                task_count=len(self.tasks),
                vehicle_count=self.vehicle_limit,
                sortie_count=self.sortie_limit,
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
                generated_columns=len(self.pool.schedules),
                root_relaxation=round_float(self.root_relaxation),
                incumbent_node=self.incumbent_node,
                log_path=str(self.log_path or ""),
                instance_path=self.instance_path,
                seed=self.seed,
            )
        finally:
            self._close_log()

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
        schedules = [
            {
                "id": schedule.id,
                "key": [list(route) for route in schedule.key],
                "route_ids": list(schedule.route_ids),
                "task_set": sorted(schedule.task_set),
                "cost": schedule.cost,
                "cycle_time": schedule.cycle_time,
                "source": schedule.source,
            }
            for schedule in self.pool.schedules
        ]
        write_json(path, {"summary": self.incumbent_solution, "routes": routes, "schedules": schedules})


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
    memory_limit_mb: float | None = None,
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
        memory_limit_mb=memory_limit_mb,
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
