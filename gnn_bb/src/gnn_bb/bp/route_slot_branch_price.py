"""中文摘要：本文件实现 route-vehicle 原生 SCIP Pricer 分支定价。主问题列为路径-车辆变量，去掉 slot 对称复制，保留 RCSP pricing、Farkas pricing、Phase-I 人工列和 warm start。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import heapq
from math import isfinite
from pathlib import Path
from typing import Any

from gnn_bb.data.instances import task_ids
from gnn_bb.data.io_utils import ensure_dir, round_float, write_json
from gnn_bb.data.terrain import arc_key


DOMINANCE_TOL = 1.0e-9
ARTIFICIAL_TASK_PENALTY = 1.0e6


@dataclass(order=True)
class Label:
    # 中文注释：pricing 标签只保存 parent pointer；完整路径只在准备加列或输出时回溯。
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
    arc_path: list[str] | None = field(compare=False)


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


def _task_value(instance: dict[str, Any], task_id: int, field_name: str) -> float:
    return float(instance["tasks"][str(task_id)][field_name])


def _route_signature(route: dict[str, Any]) -> tuple[int, ...]:
    return tuple(int(task) for task in route["tasks"])


def _status_name(status: Any) -> str:
    text = str(status).lower()
    status_map = {
        "optimal": "OPTIMAL",
        "infeasible": "INFEASIBLE",
        "unbounded": "UNBOUNDED",
        "inforunbd": "INF_OR_UNBD",
        "timelimit": "TIME_LIMIT",
        "nodelimit": "NODE_LIMIT",
        "gaplimit": "GAP_LIMIT",
        "memlimit": "MEMORY_LIMIT",
        "userinterrupt": "INTERRUPTED",
        "solutionlimit": "SOLUTION_LIMIT",
    }
    return status_map.get(text, text.upper())


def _safe_call(func, default=None):
    try:
        value = func()
    except Exception:
        return default
    if isinstance(value, float) and not isfinite(value):
        return value
    return value


def _try_set_param(model, name: str, value: Any) -> None:
    try:
        model.setParam(name, value)
    except Exception:
        pass


def evaluate_route(instance: dict[str, Any], pairwise: dict[str, dict[str, Any]], sequence: list[int] | tuple[int, ...]) -> dict[str, Any] | None:
    vehicles = instance["vehicles"]
    q_limit = float(vehicles["Q"])
    b_limit = float(vehicles["B_use"])
    horizon = float(vehicles["H"])
    rho = float(vehicles["rho"])

    load = sum(_task_value(instance, task, "d") for task in sequence)
    if load > q_limit + 1.0e-9:
        return None

    travel_time = 0.0
    travel_energy = 0.0
    travel_cost = 0.0
    service_energy = 0.0
    service_cost = 0.0
    service_start = {}
    current = 0
    current_time = 0.0
    physical_paths = []

    for task_id in sequence:
        segment = pairwise[arc_key(current, task_id)]
        travel_time += float(segment["tau"])
        travel_energy += float(segment["energy"])
        travel_cost += float(segment["cost"])
        physical_paths.append({"from": current, "to": task_id, "path": segment.get("path", [])})

        arrival = current_time + float(segment["tau"])
        start = max(_task_value(instance, task_id, "r"), arrival)
        if start + _task_value(instance, task_id, "sigma") > _task_value(instance, task_id, "D") + 1.0e-9:
            return None

        service_start[int(task_id)] = start
        current_time = start + _task_value(instance, task_id, "sigma")
        service_energy += _task_value(instance, task_id, "g")
        service_cost += _task_value(instance, task_id, "c_srv")
        current = task_id

    back = pairwise[arc_key(current, 0)]
    travel_time += float(back["tau"])
    travel_energy += float(back["energy"])
    travel_cost += float(back["cost"])
    physical_paths.append({"from": current, "to": 0, "path": back.get("path", [])})

    return_time = current_time + float(back["tau"])
    total_energy = travel_energy + service_energy
    total_cost = travel_cost + service_cost
    if total_energy > b_limit + 1.0e-9 or return_time > horizon + 1.0e-9:
        return None

    return {
        "tasks": list(int(task) for task in sequence),
        "task_set": sorted(int(task) for task in sequence),
        "task_count": len(sequence),
        "load": round_float(load),
        "travel_time": round_float(travel_time),
        "return_time": round_float(return_time),
        "energy": round_float(total_energy),
        "cost": round_float(total_cost),
        "cycle_time": round_float(return_time + total_energy / rho),
        "service_start": {str(task): round_float(time) for task, time in service_start.items()},
        "physical_paths": physical_paths,
    }


class RouteVehiclePricer:
    """中文注释：SCIP 原生 Pricer。每次调用只找一批必要路径-车辆列，列由 SCIP 加入当前节点 LP。"""

    def __init__(self, instance: dict[str, Any], pairwise: dict[str, dict[str, Any]], data: dict[str, Any], eps: float = 1.0e-6):
        from pyscipopt import Pricer

        class _Pricer(Pricer):
            def __init__(self, outer):
                super().__init__()
                self.outer = outer

            def pricerinit(self):
                self.outer.on_pricer_init(self.model)

            def pricerredcost(self):
                return self.outer.on_pricer_redcost(self.model)

            def pricerfarkas(self):
                return self.outer.on_pricer_farkas(self.model)

        self.plugin = _Pricer(self)
        self.instance = instance
        self.pairwise = pairwise
        self.data = data
        self.eps = eps
        self.routes: list[dict[str, Any]] = []
        self.route_by_signature: dict[tuple[int, ...], dict[str, Any]] = {}
        self.columns: list[dict[str, Any]] = []
        self.column_keys: set[tuple[int, int]] = set()
        self.column_by_key: dict[tuple[int, int], dict[str, Any]] = {}
        self.generated_by_redcost = 0
        self.generated_by_farkas = 0
        self.redcost_calls = 0
        self.farkas_calls = 0
        self.early_pricing_returns = 0
        self.dominated_labels = 0

    def on_pricer_init(self, model) -> None:
        # 中文注释：SCIP transform 后必须把原始约束引用更新成 transformed 约束。
        self.data["cover_cons"] = {k: model.getTransformedCons(cons) for k, cons in self.data["cover_cons"].items()}
        self.data["sortie_count_cons"] = {r: model.getTransformedCons(cons) for r, cons in self.data["sortie_count_cons"].items()}
        self.data["vehicle_time_cons"] = {r: model.getTransformedCons(cons) for r, cons in self.data["vehicle_time_cons"].items()}

    def _register_route(self, route: dict[str, Any]) -> dict[str, Any]:
        signature = _route_signature(route)
        existing = self.route_by_signature.get(signature)
        if existing is not None:
            return existing
        route = dict(route)
        route["id"] = len(self.routes)
        self.routes.append(route)
        self.route_by_signature[signature] = route
        return route

    def add_column(self, model, route: dict[str, Any], r: int, priced_var: bool, source: str = "initial") -> bool:
        route = self._register_route(route)
        key = (int(route["id"]), int(r))
        if key in self.column_keys:
            return False

        var = model.addVar(
            name=f"lambda[{route['id']},{r}]",
            vtype="B",
            lb=0.0,
            ub=1.0,
            obj=float(route["cost"]),
            pricedVar=priced_var,
        )
        for task_id in route["task_set"]:
            model.addCoefLinear(self.data["cover_cons"][int(task_id)], var, 1.0)
        model.addCoefLinear(self.data["sortie_count_cons"][int(r)], var, 1.0)
        model.addCoefLinear(self.data["vehicle_time_cons"][int(r)], var, float(route["cycle_time"]))

        column = {"var": var, "route_id": int(route["id"]), "vehicle": int(r), "source": source}
        self.columns.append(column)
        self.column_keys.add(key)
        self.column_by_key[key] = column
        if source == "redcost":
            self.generated_by_redcost += 1
        elif source == "farkas":
            self.generated_by_farkas += 1
        return True

    def find_column(self, route: dict[str, Any], r: int) -> dict[str, Any] | None:
        existing = self.route_by_signature.get(_route_signature(route))
        if existing is None:
            return None
        return self.column_by_key.get((int(existing["id"]), int(r)))

    def _duals(self, model):
        cover_duals = {k: float(model.getDualsolLinear(cons)) for k, cons in self.data["cover_cons"].items()}
        sortie_count_duals = {r: float(model.getDualsolLinear(cons)) for r, cons in self.data["sortie_count_cons"].items()}
        vehicle_time_duals = {r: float(model.getDualsolLinear(cons)) for r, cons in self.data["vehicle_time_cons"].items()}
        return cover_duals, sortie_count_duals, vehicle_time_duals

    def _farkas_duals(self, model):
        # 中文注释：RMP 不可行时，用 Farkas 对偶射线寻找能破坏不可行性证明的列。
        cover_duals = {k: float(model.getDualfarkasLinear(cons)) for k, cons in self.data["cover_cons"].items()}
        sortie_count_duals = {r: float(model.getDualfarkasLinear(cons)) for r, cons in self.data["sortie_count_cons"].items()}
        vehicle_time_duals = {r: float(model.getDualfarkasLinear(cons)) for r, cons in self.data["vehicle_time_cons"].items()}
        return cover_duals, sortie_count_duals, vehicle_time_duals

    def _label_chain(self, label: Label) -> list[Label]:
        chain = []
        cursor = label
        while cursor.parent is not None:
            chain.append(cursor)
            cursor = cursor.parent
        chain.reverse()
        return chain

    def _label_sequence(self, label: Label) -> tuple[int, ...]:
        return tuple(int(node.task_id) for node in self._label_chain(label) if node.task_id is not None)

    def _route_summary_from_label(self, label: Label) -> dict[str, Any]:
        vehicles = self.instance["vehicles"]
        rho = float(vehicles["rho"])
        return_segment = self.pairwise[arc_key(label.node, 0)]
        return_time = label.time + float(return_segment["tau"])
        total_energy = label.energy + float(return_segment["energy"])
        total_cost = label.cost + float(return_segment["cost"])
        total_travel_time = label.travel_time + float(return_segment["tau"])
        sequence = self._label_sequence(label)
        return {
            "sequence": sequence,
            "task_set": sorted(label.visited),
            "task_count": len(label.visited),
            "load": round_float(label.load),
            "travel_time": round_float(total_travel_time),
            "return_time": round_float(return_time),
            "energy": round_float(total_energy),
            "cost": round_float(total_cost),
            "cycle_time": round_float(return_time + total_energy / rho),
        }

    def _complete_route_from_label(self, label: Label, summary: dict[str, Any] | None = None) -> dict[str, Any]:
        summary = self._route_summary_from_label(label) if summary is None else summary
        service_start = {}
        physical_paths = []
        for node in self._label_chain(label):
            service_start[str(node.task_id)] = round_float(node.service_start_time)
            physical_paths.append({"from": node.parent.node, "to": node.task_id, "path": node.arc_path})
        return_segment = self.pairwise[arc_key(label.node, 0)]
        return {
            "tasks": list(summary["sequence"]),
            "task_set": summary["task_set"],
            "task_count": summary["task_count"],
            "load": summary["load"],
            "travel_time": summary["travel_time"],
            "return_time": summary["return_time"],
            "energy": summary["energy"],
            "cost": summary["cost"],
            "cycle_time": summary["cycle_time"],
            "service_start": service_start,
            "physical_paths": [*physical_paths, {"from": label.node, "to": 0, "path": return_segment.get("path", [])}],
        }

    def _reduced_cost(self, route: dict[str, Any], r: int, cover_duals, sortie_count_duals, vehicle_time_duals) -> float:
        return (
            float(route["cost"])
            - sum(float(cover_duals[int(task_id)]) for task_id in route["task_set"])
            - float(sortie_count_duals[int(r)])
            - float(vehicle_time_duals[int(r)]) * float(route["cycle_time"])
        )

    def _farkas_score(self, route: dict[str, Any], r: int, cover_duals, sortie_count_duals, vehicle_time_duals) -> float:
        farkas_value = (
            sum(float(cover_duals[int(task_id)]) for task_id in route["task_set"])
            + float(sortie_count_duals[int(r)])
            + float(vehicle_time_duals[int(r)]) * float(route["cycle_time"])
        )
        return -farkas_value

    def _column_already_exists_by_signature(self, signature: tuple[int, ...], r: int) -> bool:
        existing = self.route_by_signature.get(signature)
        return existing is not None and (int(existing["id"]), int(r)) in self.column_keys

    def _column_score(self, route: dict[str, Any], r: int, cover_duals, sortie_count_duals, vehicle_time_duals, pricing_mode: str) -> float:
        if pricing_mode == "farkas":
            return self._farkas_score(route, r, cover_duals, sortie_count_duals, vehicle_time_duals)
        return self._reduced_cost(route, r, cover_duals, sortie_count_duals, vehicle_time_duals)

    def _label_priority(self, sequence: tuple[int, ...] | frozenset[int], cost: float, cover_duals, pricing_mode: str) -> float:
        dual_sum = sum(float(cover_duals[int(task)]) for task in sequence)
        if pricing_mode == "farkas":
            return -dual_sum
        return cost - dual_sum

    def _dominates(self, left: Label, right: Label) -> bool:
        if left.node != right.node or left.visited != right.visited:
            return False
        return (
            left.time <= right.time + DOMINANCE_TOL
            and left.load <= right.load + DOMINANCE_TOL
            and left.energy <= right.energy + DOMINANCE_TOL
            and left.cost <= right.cost + DOMINANCE_TOL
        )

    def _is_dominated_or_record(self, label: Label, nondominated: dict[tuple[int, frozenset[int]], list[Label]]) -> bool:
        key = (label.node, label.visited)
        labels = nondominated.setdefault(key, [])
        for existing in labels:
            if self._dominates(existing, label):
                return True
        nondominated[key] = [existing for existing in labels if not self._dominates(label, existing)]
        nondominated[key].append(label)
        return False

    def _exact_pricing(self, cover_duals, sortie_count_duals, vehicle_time_duals, pricing_mode: str, stop_after_first_route: bool = False):
        tasks = task_ids(self.instance)
        vehicles = self.instance["vehicles"]
        q_limit = float(vehicles["Q"])
        b_limit = float(vehicles["B_use"])
        horizon = float(vehicles["H"])
        best_columns = []
        use_dominance = max(vehicle_time_duals.values(), default=0.0) <= DOMINANCE_TOL
        start_label = Label(0.0, 0, None, None, frozenset(), 0.0, 0.0, 0.0, 0.0, 0.0, None, None)
        queue = [start_label]
        nondominated = {(start_label.node, start_label.visited): [start_label]} if use_dominance else {}

        while queue:
            label = heapq.heappop(queue)
            if use_dominance and not any(existing is label for existing in nondominated.get((label.node, label.visited), [])):
                continue
            for task_id in tasks:
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
                total_energy_with_return = next_energy + float(return_segment["energy"])
                if return_time > horizon + 1.0e-9 or total_energy_with_return > b_limit + 1.0e-9:
                    continue

                next_visited = frozenset((*label.visited, int(task_id)))
                next_cost = label.cost + float(segment["cost"]) + _task_value(self.instance, task_id, "c_srv")
                next_label = Label(
                    priority=self._label_priority(next_visited, next_cost, cover_duals, pricing_mode),
                    node=int(task_id),
                    task_id=int(task_id),
                    parent=label,
                    visited=next_visited,
                    time=finish,
                    load=next_load,
                    energy=next_energy,
                    travel_time=label.travel_time + float(segment["tau"]),
                    cost=next_cost,
                    service_start_time=start,
                    arc_path=segment.get("path", []),
                )
                if use_dominance and self._is_dominated_or_record(next_label, nondominated):
                    self.dominated_labels += 1
                    continue

                route_summary = self._route_summary_from_label(next_label)
                route_signature = tuple(route_summary["sequence"])
                route_columns = []
                for r in self.data["R"]:
                    if self._column_already_exists_by_signature(route_signature, r):
                        continue
                    score = self._column_score(route_summary, r, cover_duals, sortie_count_duals, vehicle_time_duals, pricing_mode)
                    if score < -self.eps:
                        route_columns.append((score, r))
                if route_columns:
                    route = self._complete_route_from_label(next_label, route_summary)
                    best_columns.extend((score, route, r) for score, r in route_columns)
                    if stop_after_first_route:
                        self.early_pricing_returns += 1
                        best_columns.sort(key=lambda item: item[0])
                        return best_columns
                heapq.heappush(queue, next_label)

        best_columns.sort(key=lambda item: item[0])
        return best_columns

    def on_pricer_redcost(self, model):
        from pyscipopt import SCIP_RESULT

        self.redcost_calls += 1
        cover_duals, sortie_count_duals, vehicle_time_duals = self._duals(model)
        priced_columns = self._exact_pricing(
            cover_duals,
            sortie_count_duals,
            vehicle_time_duals,
            pricing_mode="redcost",
            stop_after_first_route=True,
        )
        for _, route, r in priced_columns:
            self.add_column(model, route, r, priced_var=True, source="redcost")
        return {"result": SCIP_RESULT.SUCCESS}

    def on_pricer_farkas(self, model):
        from pyscipopt import SCIP_RESULT

        self.farkas_calls += 1
        cover_duals, sortie_count_duals, vehicle_time_duals = self._farkas_duals(model)
        priced_columns = self._exact_pricing(
            cover_duals,
            sortie_count_duals,
            vehicle_time_duals,
            pricing_mode="farkas",
            stop_after_first_route=True,
        )
        for _, route, r in priced_columns:
            self.add_column(model, route, r, priced_var=True, source="farkas")
        return {"result": SCIP_RESULT.SUCCESS}


def _build_initial_routes(instance: dict[str, Any], pairwise: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    routes = []
    for task_id in task_ids(instance):
        route = evaluate_route(instance, pairwise, [task_id])
        if route is None:
            raise ValueError(f"任务 {task_id} 无法作为单任务路径独立可行")
        routes.append(route)
    return routes


def _task_order(instance: dict[str, Any], tasks: set[int]) -> list[int]:
    return sorted(tasks, key=lambda task_id: (_task_value(instance, task_id, "D"), _task_value(instance, task_id, "r"), task_id))


def _best_insert_route(instance: dict[str, Any], pairwise: dict[str, dict[str, Any]], sequence: list[int], uncovered: set[int], remaining_cycle_time: float):
    best = None
    for task_id in _task_order(instance, uncovered):
        for position in range(len(sequence) + 1):
            candidate_sequence = [*sequence[:position], task_id, *sequence[position:]]
            route = evaluate_route(instance, pairwise, candidate_sequence)
            if route is None or float(route["cycle_time"]) > remaining_cycle_time + 1.0e-9:
                continue
            score = (float(route["cycle_time"]), float(route["cost"]), _task_value(instance, task_id, "D"), task_id)
            if best is None or score < best[0]:
                best = (score, route)
    return None if best is None else best[1]


def _build_warm_start_assignments(instance: dict[str, Any], pairwise: dict[str, dict[str, Any]], R: list[int], sortie_limit: int):
    # 中文注释：warm start 只提供初始可行解和初始真实列，不限制后续 exact pricing。
    horizon = float(instance["vehicles"]["H"])
    uncovered = set(task_ids(instance))
    vehicle_cycle_time = {r: 0.0 for r in R}
    assignments = []
    for r in R:
        for sortie_index in range(1, sortie_limit + 1):
            if not uncovered:
                break
            sequence = []
            route = None
            remaining_cycle_time = horizon - vehicle_cycle_time[r]
            while uncovered:
                candidate = _best_insert_route(instance, pairwise, sequence, uncovered, remaining_cycle_time)
                if candidate is None:
                    break
                route = candidate
                sequence = list(candidate["tasks"])
                for task_id in route["task_set"]:
                    uncovered.discard(int(task_id))
            if route is None:
                continue
            assignments.append({"vehicle": r, "sortie": sortie_index, "route": route})
            vehicle_cycle_time[r] += float(route["cycle_time"])
        if not uncovered:
            break
    return assignments, uncovered


def _submit_warm_start_solution(model, pricer: RouteVehiclePricer, data: dict[str, Any], assignments: list[dict[str, Any]], uncovered_tasks: set[int]) -> bool:
    try:
        solution = model.createSol()
        selected_columns = set()
        used_vehicles = set()
        for assignment in assignments:
            column = pricer.find_column(assignment["route"], assignment["vehicle"])
            if column is None:
                continue
            selected_columns.add((column["route_id"], column["vehicle"]))
            used_vehicles.add(assignment["vehicle"])
        for column in pricer.columns:
            key = (column["route_id"], column["vehicle"])
            model.setSolVal(solution, column["var"], 1.0 if key in selected_columns else 0.0)
        for r, var in data["y"].items():
            model.setSolVal(solution, var, 1.0 if r in used_vehicles else 0.0)
        for task_id, var in data["artificial"].items():
            model.setSolVal(solution, var, 1.0 if task_id in uncovered_tasks else 0.0)
        result = model.addSol(solution)
        return True if result is None else bool(result)
    except Exception:
        return False


def _add_warm_start(model, pricer: RouteVehiclePricer, data: dict[str, Any], instance: dict[str, Any], pairwise: dict[str, dict[str, Any]]) -> dict[str, Any]:
    assignments, uncovered = _build_warm_start_assignments(instance, pairwise, data["R"], int(instance["vehicles"]["S_bar"]))
    for assignment in assignments:
        pricer.add_column(model, assignment["route"], assignment["vehicle"], priced_var=False, source="warm_start")
    submitted = _submit_warm_start_solution(model, pricer, data, assignments, uncovered)
    covered_tasks = sorted(set(task_ids(instance)) - set(uncovered))
    return {
        "enabled": True,
        "submitted": submitted,
        "routes": len(assignments),
        "covered_tasks": len(covered_tasks),
        "uncovered_tasks": sorted(uncovered),
    }


def build_branch_price_model(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    *,
    eps: float = 1.0e-6,
    warm_start: bool = True,
    rmp_params: dict[str, Any] | None = None,
):
    from pyscipopt import Model, quicksum

    vehicles = instance["vehicles"]
    tasks = task_ids(instance)
    R = list(range(1, int(vehicles["R_bar"]) + 1))
    sortie_limit = int(vehicles["S_bar"])
    fixed_vehicle_cost = float(vehicles["F"])
    horizon = float(vehicles["H"])

    model = Model("route_vehicle_branch_price")
    y = {r: model.addVar(vtype="B", obj=fixed_vehicle_cost, name=f"y[{r}]") for r in R}

    cover_cons = {}
    for task_id in tasks:
        cover_cons[task_id] = model.addCons(quicksum([]) == 1, name=f"cover[{task_id}]", modifiable=True)

    artificial = {}
    for task_id in tasks:
        artificial[task_id] = model.addVar(vtype="B", lb=0.0, ub=1.0, obj=ARTIFICIAL_TASK_PENALTY, name=f"phase1_artificial_cover[{task_id}]")
        model.addCoefLinear(cover_cons[task_id], artificial[task_id], 1.0)

    sortie_count_cons = {}
    for r in R:
        sortie_count_cons[r] = model.addCons(
            quicksum([]) - sortie_limit * y[r] <= 0,
            name=f"vehicle_sortie_count[{r}]",
            modifiable=True,
        )

    vehicle_time_cons = {}
    for r in R:
        vehicle_time_cons[r] = model.addCons(quicksum([]) - horizon * y[r] <= 0, name=f"vehicle_cycle_time[{r}]", modifiable=True)

    for r in R[:-1]:
        model.addCons(y[r + 1] <= y[r], name=f"vehicle_sequence[{r}]")

    for name, value in (rmp_params or {}).items():
        _try_set_param(model, name, value)

    data = {
        "R": R,
        "S_bar": sortie_limit,
        "tasks": tasks,
        "y": y,
        "artificial": artificial,
        "cover_cons": cover_cons,
        "sortie_count_cons": sortie_count_cons,
        "vehicle_time_cons": vehicle_time_cons,
    }
    pricer = RouteVehiclePricer(instance, pairwise, data, eps=eps)
    model.includePricer(pricer.plugin, "route_vehicle_pricer", "严格分支定价路径-车辆列生成器", priority=1, delay=True)

    for route in _build_initial_routes(instance, pairwise):
        for r in R:
            pricer.add_column(model, route, r, priced_var=False)

    data["warm_start"] = _add_warm_start(model, pricer, data, instance, pairwise) if warm_start else {"enabled": False}
    return model, pricer, data


def solve_branch_price(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    *,
    time_limit: float | None = None,
    node_limit: int | None = None,
    verbose: bool = True,
    eps: float = 1.0e-6,
    warm_start: bool = True,
    rmp_params: dict[str, Any] | None = None,
    memory_limit_mb: float | None = None,
):
    model, pricer, data = build_branch_price_model(instance, pairwise, eps=eps, warm_start=warm_start, rmp_params=rmp_params)
    if time_limit is not None:
        _try_set_param(model, "limits/time", float(time_limit))
    if node_limit is not None:
        _try_set_param(model, "limits/nodes", int(node_limit))
    if memory_limit_mb is not None:
        _try_set_param(model, "limits/memory", float(memory_limit_mb))
    _try_set_param(model, "display/verblevel", 4 if verbose else 0)
    model.optimize()

    solution_count = int(_safe_call(model.getNSols, 0) or 0)
    has_solution = solution_count > 0
    raw_status = str(_safe_call(model.getStatus, "unknown"))
    objective = round_float(_safe_call(model.getObjVal)) if has_solution else None
    best_bound = round_float(_safe_call(model.getDualbound))
    gap = round_float(_safe_call(model.getGap)) if has_solution else None
    summary = {
        "status": _status_name(raw_status),
        "status_code": raw_status,
        "objective": objective,
        "runtime": round_float(_safe_call(model.getSolvingTime, 0.0)),
        "best_bound": best_bound,
        "mip_gap": gap,
        "node_count": round_float(_safe_call(model.getNNodes, 0.0)),
        "solution_count": solution_count,
    }

    solution = {"summary": summary, "vehicles": {}, "sorties": [], "selected_route_ids": [], "artificial_tasks": []}
    if has_solution:
        for r in data["R"]:
            solution["vehicles"][str(r)] = round_float(model.getVal(data["y"][r]))
        for task_id, var in data["artificial"].items():
            if float(model.getVal(var)) > 0.5:
                solution["artificial_tasks"].append(int(task_id))
        route_by_id = {route["id"]: route for route in pricer.routes}
        sortie_index_by_vehicle = {r: 0 for r in data["R"]}
        for column in pricer.columns:
            if model.getVal(column["var"]) <= 0.5:
                continue
            route = route_by_id[column["route_id"]]
            sortie_index_by_vehicle[column["vehicle"]] += 1
            solution["selected_route_ids"].append(route["id"])
            solution["sorties"].append(
                {
                    "vehicle": column["vehicle"],
                    "sortie": sortie_index_by_vehicle[column["vehicle"]],
                    "route_id": route["id"],
                    "tasks": route["tasks"],
                    "cost": route["cost"],
                    "load": route["load"],
                    "energy": route["energy"],
                    "return_time": route["return_time"],
                    "cycle_time": route["cycle_time"],
                    "service_start": route["service_start"],
                }
            )
    solution["summary"]["uses_artificial"] = bool(solution["artificial_tasks"])
    solution["summary"]["artificial_task_count"] = len(solution["artificial_tasks"])

    report = {
        "mode": "route_vehicle_branch_price",
        "generated_routes": len(pricer.routes),
        "generated_columns": len(pricer.columns),
        "priced_columns": pricer.generated_by_redcost + pricer.generated_by_farkas,
        "redcost_columns": pricer.generated_by_redcost,
        "farkas_columns": pricer.generated_by_farkas,
        "redcost_calls": pricer.redcost_calls,
        "farkas_calls": pricer.farkas_calls,
        "pricing_calls": pricer.redcost_calls + pricer.farkas_calls,
        "early_pricing_returns": pricer.early_pricing_returns,
        "dominated_labels": pricer.dominated_labels,
        "artificial_penalty": ARTIFICIAL_TASK_PENALTY,
        "warm_start": data["warm_start"],
        "strict_pricing": True,
        "eps": eps,
    }
    return pricer.routes, report, solution


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
    artificial_penalty: float = ARTIFICIAL_TASK_PENALTY,
    rmp_params: dict[str, Any] | None = None,
    seed: int | None = None,
    log_level: str = "progress",
) -> BPResult:
    del integer_tol, max_cg_iterations_per_node, max_columns_per_pricing, artificial_penalty
    verbose = log_level != "quiet"
    routes, report, solution = solve_branch_price(
        instance,
        pairwise,
        time_limit=time_limit,
        node_limit=max_nodes,
        verbose=verbose,
        eps=pricing_eps,
        warm_start=True,
        rmp_params=rmp_params,
        memory_limit_mb=memory_limit_mb,
    )
    if solution_path is not None:
        write_json(solution_path, {"routes": routes, "report": report, "solution": solution})
    if log_path is not None:
        ensure_dir(Path(log_path).parent)
        write_json(log_path, {"summary": solution["summary"], "report": report})

    summary = solution["summary"]
    uses_artificial = bool(summary.get("uses_artificial"))
    status = str(summary.get("status", "UNKNOWN"))
    primal = None if uses_artificial else summary.get("objective")
    result = BPResult(
        instance=str(instance.get("name", "instance")),
        task_count=len(task_ids(instance)),
        vehicle_count=int(instance["vehicles"]["R_bar"]),
        sortie_count=int(instance["vehicles"]["S_bar"]),
        status=status,
        primal_bound=round_float(primal),
        dual_bound=round_float(summary.get("best_bound")),
        gap=round_float(summary.get("mip_gap")) if primal is not None else None,
        solving_time=round_float(summary.get("runtime", 0.0)),
        node_count=int(summary.get("node_count") or 0),
        rmp_solves=0,
        cg_iterations=int(report.get("pricing_calls", 0)),
        pricing_calls=int(report.get("pricing_calls", 0)),
        exact_pricing_calls=int(report.get("pricing_calls", 0)),
        generated_routes=int(report.get("generated_routes", 0)),
        generated_columns=int(report.get("generated_columns", 0)),
        root_relaxation=None,
        incumbent_node=None,
        log_path=str(log_path or ""),
        instance_path=str(instance_path),
        seed=seed,
    )
    if max_nodes and result.node_count >= int(max_nodes) and status == "TIME_LIMIT":
        return result
    return result
