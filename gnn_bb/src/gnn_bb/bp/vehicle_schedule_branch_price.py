"""中文摘要：本文件实现真实车辆日程列 master。一个列是一辆车按时间顺序执行的完整 sortie 日程，pricing 在同一个标签 DP 中处理 sortie 内任务扩展、返回基地、充电/周转后开启下一条 sortie。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import heapq
from math import isfinite
from pathlib import Path
from typing import Any

from gnn_bb.bp.schedule_preprocessing import SchedulePreprocessResult, build_schedule_preprocess, build_trivial_schedule_preprocess
from gnn_bb.data.instances import task_ids
from gnn_bb.data.io_utils import ensure_dir, round_float, write_json
from gnn_bb.data.terrain import arc_key


DOMINANCE_TOL = 1.0e-9
ARTIFICIAL_TASK_PENALTY = 1.0e6


@dataclass(order=True)
class SchedulePricingLabel:
    # 中文注释：closed label 表示车辆在基地可出发；open label 表示正在执行一条 sortie。
    priority: float
    covered: frozenset[int] = field(compare=False)
    routes: tuple[tuple[int, ...], ...] = field(compare=False)
    used_sorties: int = field(compare=False)
    ready_time: float = field(compare=False)
    cost: float = field(compare=False)
    current_node: int = field(compare=False)
    route_tasks: tuple[int, ...] = field(compare=False)
    route_time: float = field(compare=False)
    route_load: float = field(compare=False)
    route_energy: float = field(compare=False)
    route_cost: float = field(compare=False)
    route_travel_time: float = field(compare=False)

    @property
    def is_open(self) -> bool:
        return bool(self.route_tasks)


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


def evaluate_route_at_start(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    sequence: tuple[int, ...],
    start_time: float,
) -> dict[str, Any] | None:
    """中文注释：按绝对出发时间评价一条 sortie；后续 sortie 的开始时间必须等前序返回并完成能耗折算时间。"""
    vehicles = instance["vehicles"]
    q_limit = float(vehicles["Q"])
    b_limit = float(vehicles["B_use"])
    horizon = float(vehicles["H"])
    rho = float(vehicles["rho"])

    current = 0
    current_time = float(start_time)
    load = 0.0
    energy = 0.0
    cost = 0.0
    travel_time = 0.0
    service_start: dict[str, float] = {}
    physical_paths = []

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
        physical_paths.append({"from": current, "to": int(task_id), "path": segment.get("path", [])})
        current = int(task_id)
        current_time = finish
        service_start[str(task_id)] = round_float(start)

    back = pairwise[arc_key(current, 0)]
    return_time = current_time + float(back["tau"])
    energy += float(back["energy"])
    cost += float(back["cost"])
    travel_time += float(back["tau"])
    physical_paths.append({"from": current, "to": 0, "path": back.get("path", [])})
    if energy > b_limit + 1.0e-9:
        return None

    ready_time = return_time + energy / rho
    if ready_time > horizon + 1.0e-9:
        return None

    return {
        "tasks": list(int(task) for task in sequence),
        "task_set": sorted(int(task) for task in sequence),
        "start_time": round_float(start_time),
        "return_time": round_float(return_time),
        "ready_time": round_float(ready_time),
        "duration": round_float(ready_time - start_time),
        "load": round_float(load),
        "energy": round_float(energy),
        "cost": round_float(cost),
        "travel_time": round_float(travel_time),
        "service_start": service_start,
        "physical_paths": physical_paths,
    }


def evaluate_schedule(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    routes: tuple[tuple[int, ...], ...],
) -> dict[str, Any] | None:
    vehicles = instance["vehicles"]
    fixed_cost = float(vehicles["F"])
    horizon = float(vehicles["H"])
    sortie_limit = int(vehicles["S_bar"])
    if not routes or len(routes) > sortie_limit:
        return None

    ready_time = 0.0
    covered: set[int] = set()
    sortie_data = []
    route_cost = 0.0
    for route_index, sequence in enumerate(routes, start=1):
        if covered.intersection(sequence):
            return None
        route = evaluate_route_at_start(instance, pairwise, sequence, ready_time)
        if route is None:
            return None
        covered.update(int(task) for task in sequence)
        ready_time = float(route["ready_time"])
        route_cost += float(route["cost"])
        sortie_data.append({"sortie": route_index, **route})
    if ready_time > horizon + 1.0e-9:
        return None
    return {
        "routes": [list(route) for route in routes],
        "key": tuple(tuple(int(task) for task in route) for route in routes),
        "task_set": sorted(covered),
        "task_count": len(covered),
        "sorties": sortie_data,
        "sortie_count": len(routes),
        "route_cost": round_float(route_cost),
        "cost": round_float(fixed_cost + route_cost),
        "ready_time": round_float(ready_time),
    }


def _clean_schedule(schedule: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in schedule.items() if key != "var"}


class VehicleSchedulePricer:
    """中文注释：车辆日程列 Pricer。列是一辆车完整日程，因此 master 不再有车辆编号或 slot 编号。"""

    def __init__(
        self,
        instance: dict[str, Any],
        pairwise: dict[str, dict[str, Any]],
        data: dict[str, Any],
        eps: float = 1.0e-6,
        max_columns_per_pricing: int = 20,
        max_pool_size: int = 200,
        pool_score_margin: float = 50.0,
        stabilized_pricing: bool = True,
        stabilization_alpha: float = 0.7,
        stabilization_min_alpha: float = 0.2,
        stabilization_max_alpha: float = 0.95,
        stabilization_label_limit: int = 20000,
        stabilization_volatility_threshold: float = 0.25,
        pricing_preprocess: bool = True,
    ):
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
        self.pricing_preprocess_enabled = bool(pricing_preprocess)
        self.preprocess: SchedulePreprocessResult = (
            build_schedule_preprocess(instance, pairwise)
            if self.pricing_preprocess_enabled
            else build_trivial_schedule_preprocess(instance)
        )
        self.eps = eps
        self.max_columns_per_pricing = max(1, int(max_columns_per_pricing))
        self.max_pool_size = max(0, int(max_pool_size))
        self.pool_score_margin = float(pool_score_margin)
        self.stabilized_pricing = bool(stabilized_pricing)
        self.stabilization_alpha = min(max(float(stabilization_alpha), float(stabilization_min_alpha)), float(stabilization_max_alpha))
        self.stabilization_min_alpha = float(stabilization_min_alpha)
        self.stabilization_max_alpha = float(stabilization_max_alpha)
        self.stabilization_label_limit = max(0, int(stabilization_label_limit))
        self.stabilization_volatility_threshold = float(stabilization_volatility_threshold)
        self.dual_center_cover: dict[int, float] | None = None
        self.dual_center_vehicle: float | None = None
        self.last_dual_volatility = 0.0
        self.stabilized_calls = 0
        self.stabilized_hits = 0
        self.stabilized_columns_added = 0
        self.stabilized_fallbacks = 0
        self.exact_fallback_calls = 0
        self.stabilized_label_pops = 0
        self.exact_label_pops = 0
        self.alpha_increases = 0
        self.alpha_decreases = 0
        self.stabilized_success_streak = 0
        self.stabilized_fail_streak = 0
        self.schedules: list[dict[str, Any]] = []
        self.schedule_keys: set[tuple[tuple[int, ...], ...]] = set()
        self.column_pool: dict[tuple[tuple[int, ...], ...], dict[str, Any]] = {}
        self.column_pool_heap: list[tuple[float, int, tuple[tuple[int, ...], ...]]] = []
        self.column_pool_serial = 0
        self.generated_by_redcost = 0
        self.generated_by_farkas = 0
        self.redcost_calls = 0
        self.farkas_calls = 0
        self.early_pricing_returns = 0
        self.pricing_batch_cap_hits = 0
        self.pool_scans = 0
        self.pool_hits = 0
        self.pool_columns_added = 0
        self.pool_evictions = 0
        self.pool_rejected_full = 0
        self.pool_replaced_worst = 0
        self.pool_skipped_by_margin = 0
        self.dominated_labels = 0
        self.preprocess_skip_depot_start = 0
        self.preprocess_skip_task_arc = 0
        self.preprocess_skip_return_to_depot = 0

    def on_pricer_init(self, model) -> None:
        self.data["cover_cons"] = {k: model.getTransformedCons(cons) for k, cons in self.data["cover_cons"].items()}
        self.data["vehicle_count_cons"] = model.getTransformedCons(self.data["vehicle_count_cons"])

    def add_column(self, model, schedule: dict[str, Any], priced_var: bool, source: str = "initial") -> bool:
        key = tuple(tuple(int(task) for task in route) for route in schedule["key"])
        if key in self.schedule_keys:
            return False
        schedule = dict(schedule)
        schedule["id"] = len(self.schedules)
        var = model.addVar(
            name=f"sched[{schedule['id']}]",
            vtype="B",
            lb=0.0,
            ub=1.0,
            obj=float(schedule["cost"]),
            pricedVar=priced_var,
        )
        for task_id in schedule["task_set"]:
            model.addCoefLinear(self.data["cover_cons"][int(task_id)], var, 1.0)
        model.addCoefLinear(self.data["vehicle_count_cons"], var, 1.0)
        schedule["var"] = var
        schedule["source"] = source
        self.schedules.append(schedule)
        self.schedule_keys.add(key)
        self.column_pool.pop(key, None)
        if source == "redcost":
            self.generated_by_redcost += 1
        elif source == "farkas":
            self.generated_by_farkas += 1
        return True

    def _duals(self, model):
        cover_duals = {k: float(model.getDualsolLinear(cons)) for k, cons in self.data["cover_cons"].items()}
        vehicle_dual = float(model.getDualsolLinear(self.data["vehicle_count_cons"]))
        return cover_duals, vehicle_dual

    def _farkas_duals(self, model):
        cover_duals = {k: float(model.getDualfarkasLinear(cons)) for k, cons in self.data["cover_cons"].items()}
        vehicle_dual = float(model.getDualfarkasLinear(self.data["vehicle_count_cons"]))
        return cover_duals, vehicle_dual

    def _schedule_score(self, schedule: dict[str, Any], cover_duals: dict[int, float], vehicle_dual: float, pricing_mode: str) -> float:
        dual_sum = sum(float(cover_duals[int(task)]) for task in schedule["task_set"])
        if pricing_mode == "farkas":
            return -(dual_sum + vehicle_dual)
        return float(schedule["cost"]) - dual_sum - vehicle_dual

    def _pool_item_score(self, item: dict[str, Any], cover_duals: dict[int, float], vehicle_dual: float, pricing_mode: str) -> float:
        dual_sum = sum(float(cover_duals[int(task)]) for task in item["task_set"])
        if pricing_mode == "farkas":
            return -(dual_sum + vehicle_dual)
        return float(item["cost"]) - dual_sum - vehicle_dual

    def _init_or_update_dual_center(self, cover_duals: dict[int, float], vehicle_dual: float, rate: float = 0.10) -> None:
        if self.dual_center_cover is None or self.dual_center_vehicle is None:
            self.dual_center_cover = {int(k): float(v) for k, v in cover_duals.items()}
            self.dual_center_vehicle = float(vehicle_dual)
            return
        for task_id, value in cover_duals.items():
            old = float(self.dual_center_cover.get(int(task_id), 0.0))
            self.dual_center_cover[int(task_id)] = (1.0 - rate) * old + rate * float(value)
        self.dual_center_vehicle = (1.0 - rate) * float(self.dual_center_vehicle) + rate * float(vehicle_dual)

    def _dual_volatility(self, cover_duals: dict[int, float], vehicle_dual: float) -> float:
        if self.dual_center_cover is None or self.dual_center_vehicle is None:
            return 0.0
        values = []
        for task_id, value in cover_duals.items():
            center = float(self.dual_center_cover.get(int(task_id), 0.0))
            values.append(abs(float(value) - center) / (1.0 + abs(float(value))))
        values.append(abs(float(vehicle_dual) - float(self.dual_center_vehicle)) / (1.0 + abs(float(vehicle_dual))))
        return sum(values) / max(1, len(values))

    def _stabilized_duals(self, cover_duals: dict[int, float], vehicle_dual: float) -> tuple[dict[int, float], float]:
        if self.dual_center_cover is None or self.dual_center_vehicle is None:
            return cover_duals, vehicle_dual
        alpha = float(self.stabilization_alpha)
        stable_cover = {
            int(task_id): alpha * float(value) + (1.0 - alpha) * float(self.dual_center_cover.get(int(task_id), value))
            for task_id, value in cover_duals.items()
        }
        stable_vehicle = alpha * float(vehicle_dual) + (1.0 - alpha) * float(self.dual_center_vehicle)
        return stable_cover, stable_vehicle

    def _change_alpha(self, delta: float) -> None:
        old = self.stabilization_alpha
        self.stabilization_alpha = min(self.stabilization_max_alpha, max(self.stabilization_min_alpha, self.stabilization_alpha + delta))
        if self.stabilization_alpha > old + 1.0e-12:
            self.alpha_increases += 1
        elif self.stabilization_alpha < old - 1.0e-12:
            self.alpha_decreases += 1

    def _adapt_stabilization_before_pricing(self, cover_duals: dict[int, float], vehicle_dual: float) -> None:
        self._init_or_update_dual_center(cover_duals, vehicle_dual, rate=0.0)
        self.last_dual_volatility = self._dual_volatility(cover_duals, vehicle_dual)
        if self.last_dual_volatility > self.stabilization_volatility_threshold:
            self._change_alpha(-0.10)

    def _adapt_stabilization_after_pricing(self, outcome: str, cover_duals: dict[int, float], vehicle_dual: float) -> None:
        if outcome in {"pool_hit", "stabilized_hit"}:
            self.stabilized_success_streak += 1
            self.stabilized_fail_streak = 0
            if self.stabilized_success_streak >= 2:
                self._change_alpha(0.05)
        elif outcome == "stabilized_miss_exact_hit":
            self.stabilized_success_streak = 0
            self.stabilized_fail_streak = 0
            self._change_alpha(0.03)
        elif outcome == "exact_no_column":
            self.stabilized_success_streak = 0
            self.stabilized_fail_streak += 1
            if self.stabilized_fail_streak >= 2:
                self._change_alpha(-0.05)
        self._init_or_update_dual_center(cover_duals, vehicle_dual, rate=0.10)

    def _pool_schedule(self, schedule: dict[str, Any], score: float | None = None) -> None:
        if self.max_pool_size <= 0:
            return
        if score is not None and score > self.pool_score_margin:
            self.pool_skipped_by_margin += 1
            return
        key = tuple(tuple(int(task) for task in route) for route in schedule["key"])
        if key in self.schedule_keys or key in self.column_pool:
            return
        if len(self.column_pool) >= self.max_pool_size:
            if score is None or not self._replace_worst_pool_item_if_better(key, score):
                self.pool_rejected_full += 1
                return
        self.column_pool_serial += 1
        self.column_pool[key] = {
            "key": key,
            "task_set": tuple(int(task) for task in schedule["task_set"]),
            "cost": float(schedule["cost"]),
            "pool_score": float(score if score is not None else self.pool_score_margin),
            "serial": self.column_pool_serial,
        }
        heapq.heappush(self.column_pool_heap, (-(float(score if score is not None else self.pool_score_margin)), self.column_pool_serial, key))

    def _replace_worst_pool_item_if_better(self, key: tuple[tuple[int, ...], ...], score: float) -> bool:
        while self.column_pool_heap:
            neg_score, serial, worst_key = self.column_pool_heap[0]
            item = self.column_pool.get(worst_key)
            if item is not None and int(item["serial"]) == int(serial):
                worst_score = -float(neg_score)
                if score >= worst_score - DOMINANCE_TOL:
                    return False
                heapq.heappop(self.column_pool_heap)
                self.column_pool.pop(worst_key, None)
                self.pool_evictions += 1
                self.pool_replaced_worst += 1
                return True
            heapq.heappop(self.column_pool_heap)
        return True

    def _scan_column_pool(self, cover_duals, vehicle_dual, pricing_mode: str):
        if not self.column_pool:
            return []
        self.pool_scans += 1
        candidates = []
        stale_keys = []
        for key, item in list(self.column_pool.items()):
            if key in self.schedule_keys:
                stale_keys.append(key)
                continue
            score = self._pool_item_score(item, cover_duals, vehicle_dual, pricing_mode)
            if score >= -self.eps:
                continue
            schedule = evaluate_schedule(self.instance, self.pairwise, key)
            if schedule is None:
                stale_keys.append(key)
                continue
            candidates.append((score, schedule))
            if len(candidates) >= self.max_columns_per_pricing:
                break
        for key in stale_keys:
            self.column_pool.pop(key, None)
        candidates.sort(key=lambda item: item[0])
        if candidates:
            self.pool_hits += 1
        return candidates

    def _label_priority(self, label: SchedulePricingLabel, cover_duals: dict[int, float], vehicle_dual: float, pricing_mode: str) -> float:
        dual_sum = sum(float(cover_duals[int(task)]) for task in label.covered)
        if pricing_mode == "farkas":
            return -dual_sum
        fixed = float(self.instance["vehicles"]["F"]) - vehicle_dual if label.routes else 0.0
        return label.cost + fixed - dual_sum

    def _record_closed(self, label: SchedulePricingLabel, nondominated: dict[Any, list[SchedulePricingLabel]]) -> bool:
        key = ("closed", label.covered)
        labels = nondominated.setdefault(key, [])
        for existing in labels:
            if (
                existing.used_sorties <= label.used_sorties
                and existing.ready_time <= label.ready_time + DOMINANCE_TOL
                and existing.cost <= label.cost + DOMINANCE_TOL
            ):
                return False
        nondominated[key] = [
            existing
            for existing in labels
            if not (
                label.used_sorties <= existing.used_sorties
                and label.ready_time <= existing.ready_time + DOMINANCE_TOL
                and label.cost <= existing.cost + DOMINANCE_TOL
            )
        ]
        nondominated[key].append(label)
        return True

    def _open_total_cost(self, label: SchedulePricingLabel) -> float:
        return float(label.cost) + float(label.route_cost)

    def _open_return_ready_time(self, label: SchedulePricingLabel) -> float:
        vehicles = self.instance["vehicles"]
        segment = self.pairwise[arc_key(label.current_node, 0)]
        return_time = float(label.route_time) + float(segment["tau"])
        return_energy = float(label.route_energy) + float(segment["energy"])
        return return_time + return_energy / float(vehicles["rho"])

    def _record_open(self, label: SchedulePricingLabel, nondominated: dict[Any, list[SchedulePricingLabel]]) -> bool:
        # 中文注释：同一已覆盖集合、当前节点、已关闭 sortie 数下，当前 open sortie 的具体任务顺序不影响后续可行扩展。
        key = ("open", label.covered, label.current_node, label.used_sorties)
        labels = nondominated.setdefault(key, [])
        label_total_cost = self._open_total_cost(label)
        label_return_ready = self._open_return_ready_time(label)
        for existing in labels:
            existing_total_cost = self._open_total_cost(existing)
            existing_return_ready = self._open_return_ready_time(existing)
            if (
                existing.route_time <= label.route_time + DOMINANCE_TOL
                and existing.route_load <= label.route_load + DOMINANCE_TOL
                and existing.route_energy <= label.route_energy + DOMINANCE_TOL
                and existing_return_ready <= label_return_ready + DOMINANCE_TOL
                and existing_total_cost <= label_total_cost + DOMINANCE_TOL
            ):
                return False
        nondominated[key] = [
            existing
            for existing in labels
            if not (
                label.route_time <= existing.route_time + DOMINANCE_TOL
                and label.route_load <= existing.route_load + DOMINANCE_TOL
                and label.route_energy <= existing.route_energy + DOMINANCE_TOL
                and label_return_ready <= self._open_return_ready_time(existing) + DOMINANCE_TOL
                and label_total_cost <= self._open_total_cost(existing) + DOMINANCE_TOL
            )
        ]
        nondominated[key].append(label)
        return True

    def _route_close(self, label: SchedulePricingLabel) -> SchedulePricingLabel | None:
        if label.current_node not in self.preprocess.task_to_depot_feasible:
            self.preprocess_skip_return_to_depot += 1
            return None
        vehicles = self.instance["vehicles"]
        rho = float(vehicles["rho"])
        horizon = float(vehicles["H"])
        segment = self.pairwise[arc_key(label.current_node, 0)]
        return_time = label.route_time + float(segment["tau"])
        route_energy = label.route_energy + float(segment["energy"])
        if route_energy > float(vehicles["B_use"]) + 1.0e-9:
            return None
        ready_time = return_time + route_energy / rho
        if ready_time > horizon + 1.0e-9:
            return None
        route_cost = label.route_cost + float(segment["cost"])
        return SchedulePricingLabel(
            priority=label.priority,
            covered=label.covered,
            routes=(*label.routes, label.route_tasks),
            used_sorties=label.used_sorties + 1,
            ready_time=ready_time,
            cost=label.cost + route_cost,
            current_node=0,
            route_tasks=tuple(),
            route_time=ready_time,
            route_load=0.0,
            route_energy=0.0,
            route_cost=0.0,
            route_travel_time=0.0,
        )

    def _extend_from_depot(self, label: SchedulePricingLabel, task_id: int) -> SchedulePricingLabel | None:
        if int(task_id) not in self.preprocess.depot_to_task_feasible:
            self.preprocess_skip_depot_start += 1
            return None
        return self._extend_open_route(label, task_id, start_from_depot=True)

    def _extend_open_route(self, label: SchedulePricingLabel, task_id: int, start_from_depot: bool = False) -> SchedulePricingLabel | None:
        if not start_from_depot and not self.preprocess.task_arc_feasible(label.current_node, int(task_id)):
            self.preprocess_skip_task_arc += 1
            return None
        vehicles = self.instance["vehicles"]
        source = 0 if start_from_depot else label.current_node
        base_time = label.ready_time if start_from_depot else label.route_time
        segment = self.pairwise[arc_key(source, task_id)]
        arrival = base_time + float(segment["tau"])
        service_start = max(_task_value(self.instance, task_id, "r"), arrival)
        finish = service_start + _task_value(self.instance, task_id, "sigma")
        if finish > _task_value(self.instance, task_id, "D") + 1.0e-9:
            return None
        load = (0.0 if start_from_depot else label.route_load) + _task_value(self.instance, task_id, "d")
        if load > float(vehicles["Q"]) + 1.0e-9:
            return None
        energy = (0.0 if start_from_depot else label.route_energy) + float(segment["energy"]) + _task_value(self.instance, task_id, "g")
        if energy > float(vehicles["B_use"]) + 1.0e-9:
            return None
        back = self.pairwise[arc_key(task_id, 0)]
        ready_after_return = finish + float(back["tau"]) + (energy + float(back["energy"])) / float(vehicles["rho"])
        if ready_after_return > float(vehicles["H"]) + 1.0e-9:
            return None
        route_cost = (0.0 if start_from_depot else label.route_cost) + float(segment["cost"]) + _task_value(self.instance, task_id, "c_srv")
        route_travel_time = (0.0 if start_from_depot else label.route_travel_time) + float(segment["tau"])
        return SchedulePricingLabel(
            priority=label.priority,
            covered=frozenset((*label.covered, int(task_id))),
            routes=label.routes,
            used_sorties=label.used_sorties,
            ready_time=label.ready_time,
            cost=label.cost,
            current_node=int(task_id),
            route_tasks=(*(() if start_from_depot else label.route_tasks), int(task_id)),
            route_time=finish,
            route_load=load,
            route_energy=energy,
            route_cost=route_cost,
            route_travel_time=route_travel_time,
        )

    def _exact_pricing(
        self,
        cover_duals,
        vehicle_dual,
        pricing_mode: str,
        max_schedules: int | None = None,
        *,
        true_cover_duals=None,
        true_vehicle_dual=None,
        max_label_pops: int | None = None,
    ):
        vehicles = self.instance["vehicles"]
        tasks = task_ids(self.instance)
        sortie_limit = int(vehicles["S_bar"])
        batch_limit = self.max_columns_per_pricing if max_schedules is None else max(1, int(max_schedules))
        score_cover_duals = cover_duals if true_cover_duals is None else true_cover_duals
        score_vehicle_dual = vehicle_dual if true_vehicle_dual is None else true_vehicle_dual
        candidates = []
        local_keys: set[tuple[tuple[int, ...], ...]] = set()
        start = SchedulePricingLabel(0.0, frozenset(), tuple(), 0, 0.0, 0.0, 0, tuple(), 0.0, 0.0, 0.0, 0.0, 0.0)
        queue = [start]
        nondominated: dict[Any, list[SchedulePricingLabel]] = {("closed", frozenset()): [start]}
        popped_labels = 0

        while queue:
            label = heapq.heappop(queue)
            popped_labels += 1
            if max_label_pops is not None and max_label_pops > 0 and popped_labels > max_label_pops:
                candidates.sort(key=lambda item: item[0])
                return candidates, False, popped_labels
            if not label.is_open:
                if label.routes:
                    schedule = evaluate_schedule(self.instance, self.pairwise, label.routes)
                    key = tuple(tuple(int(task) for task in route) for route in schedule["key"]) if schedule is not None else tuple()
                    if schedule is not None and key not in self.schedule_keys and key not in local_keys:
                        score = self._schedule_score(schedule, score_cover_duals, score_vehicle_dual, pricing_mode)
                        if score < -self.eps:
                            candidates.append((score, schedule))
                            local_keys.add(key)
                            # 中文注释：找到一批负 reduced-cost 列后立即返回；若没有返回，则说明 DP 已穷尽，pricing 结论才是 exact。
                            if len(candidates) >= batch_limit:
                                self.early_pricing_returns += 1
                                self.pricing_batch_cap_hits += 1
                                candidates.sort(key=lambda item: item[0])
                                return candidates, False, popped_labels
                        else:
                            self._pool_schedule(schedule, score=score)
                if label.used_sorties >= sortie_limit:
                    continue
                for task_id in sorted(self.preprocess.depot_to_task_feasible):
                    if task_id in label.covered:
                        continue
                    next_label = self._extend_from_depot(label, task_id)
                    if next_label is None:
                        continue
                    next_label.priority = self._label_priority(next_label, cover_duals, vehicle_dual, pricing_mode)
                    if self._record_open(next_label, nondominated):
                        heapq.heappush(queue, next_label)
                    else:
                        self.dominated_labels += 1
                continue

            closed = self._route_close(label)
            if closed is not None:
                closed.priority = self._label_priority(closed, cover_duals, vehicle_dual, pricing_mode)
                if self._record_closed(closed, nondominated):
                    heapq.heappush(queue, closed)
                else:
                    self.dominated_labels += 1
            for task_id in self.preprocess.task_successors.get(label.current_node, tuple()):
                if task_id in label.covered:
                    continue
                next_label = self._extend_open_route(label, task_id)
                if next_label is None:
                    continue
                next_label.priority = self._label_priority(next_label, cover_duals, vehicle_dual, pricing_mode)
                if self._record_open(next_label, nondominated):
                    heapq.heappush(queue, next_label)
                else:
                    self.dominated_labels += 1

        candidates.sort(key=lambda item: item[0])
        return candidates, True, popped_labels

    def on_pricer_redcost(self, model):
        from pyscipopt import SCIP_RESULT

        self.redcost_calls += 1
        cover_duals, vehicle_dual = self._duals(model)
        if self.stabilized_pricing:
            self._adapt_stabilization_before_pricing(cover_duals, vehicle_dual)
        pool_candidates = self._scan_column_pool(cover_duals, vehicle_dual, "redcost")
        if pool_candidates:
            for _, schedule in pool_candidates:
                if self.add_column(model, schedule, priced_var=True, source="redcost"):
                    self.pool_columns_added += 1
            if self.stabilized_pricing:
                self._adapt_stabilization_after_pricing("pool_hit", cover_duals, vehicle_dual)
            return {"result": SCIP_RESULT.SUCCESS}

        if self.stabilized_pricing:
            stable_cover_duals, stable_vehicle_dual = self._stabilized_duals(cover_duals, vehicle_dual)
            self.stabilized_calls += 1
            stabilized_candidates, _exhausted, label_pops = self._exact_pricing(
                stable_cover_duals,
                stable_vehicle_dual,
                "redcost",
                true_cover_duals=cover_duals,
                true_vehicle_dual=vehicle_dual,
                max_label_pops=self.stabilization_label_limit,
            )
            self.stabilized_label_pops += label_pops
            if stabilized_candidates:
                self.stabilized_hits += 1
                for _, schedule in stabilized_candidates:
                    if self.add_column(model, schedule, priced_var=True, source="redcost"):
                        self.stabilized_columns_added += 1
                self._adapt_stabilization_after_pricing("stabilized_hit", cover_duals, vehicle_dual)
                return {"result": SCIP_RESULT.SUCCESS}
            self.stabilized_fallbacks += 1

        self.exact_fallback_calls += 1
        exact_candidates, _exhausted, label_pops = self._exact_pricing(cover_duals, vehicle_dual, "redcost")
        self.exact_label_pops += label_pops
        added = 0
        for _, schedule in exact_candidates:
            if self.add_column(model, schedule, priced_var=True, source="redcost"):
                added += 1
        if self.stabilized_pricing:
            self._adapt_stabilization_after_pricing(
                "stabilized_miss_exact_hit" if added else "exact_no_column",
                cover_duals,
                vehicle_dual,
            )
        return {"result": SCIP_RESULT.SUCCESS}

    def on_pricer_farkas(self, model):
        from pyscipopt import SCIP_RESULT

        self.farkas_calls += 1
        cover_duals, vehicle_dual = self._farkas_duals(model)
        pool_candidates = self._scan_column_pool(cover_duals, vehicle_dual, "farkas")
        if pool_candidates:
            for _, schedule in pool_candidates:
                if self.add_column(model, schedule, priced_var=True, source="farkas"):
                    self.pool_columns_added += 1
            return {"result": SCIP_RESULT.SUCCESS}
        candidates, _exhausted, label_pops = self._exact_pricing(cover_duals, vehicle_dual, "farkas")
        self.exact_label_pops += label_pops
        for _, schedule in candidates:
            self.add_column(model, schedule, priced_var=True, source="farkas")
        return {"result": SCIP_RESULT.SUCCESS}


def _task_order(instance: dict[str, Any], tasks: set[int]) -> list[int]:
    return sorted(tasks, key=lambda task_id: (_task_value(instance, task_id, "D"), _task_value(instance, task_id, "r"), task_id))


def _best_insert_route(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    sequence: tuple[int, ...],
    uncovered: set[int],
    ready_time: float,
) -> tuple[int, ...] | None:
    best = None
    for task_id in _task_order(instance, uncovered):
        for position in range(len(sequence) + 1):
            candidate = (*sequence[:position], task_id, *sequence[position:])
            route = evaluate_route_at_start(instance, pairwise, candidate, ready_time)
            if route is None:
                continue
            score = (float(route["ready_time"]), float(route["cost"]), _task_value(instance, task_id, "D"), task_id)
            if best is None or score < best[0]:
                best = (score, candidate)
    return None if best is None else best[1]


def _build_warm_start_schedules(instance: dict[str, Any], pairwise: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], set[int]]:
    uncovered = set(task_ids(instance))
    schedules = []
    for _ in range(int(instance["vehicles"]["R_bar"])):
        routes = []
        ready_time = 0.0
        for _sortie in range(int(instance["vehicles"]["S_bar"])):
            if not uncovered:
                break
            sequence: tuple[int, ...] = tuple()
            while uncovered:
                candidate = _best_insert_route(instance, pairwise, sequence, uncovered, ready_time)
                if candidate is None:
                    break
                sequence = candidate
                for task_id in sequence:
                    uncovered.discard(int(task_id))
            if not sequence:
                break
            route = evaluate_route_at_start(instance, pairwise, sequence, ready_time)
            if route is None:
                break
            routes.append(sequence)
            ready_time = float(route["ready_time"])
        if routes:
            schedule = evaluate_schedule(instance, pairwise, tuple(routes))
            if schedule is not None:
                schedules.append(schedule)
        if not uncovered:
            break
    return schedules, uncovered


def build_branch_price_model(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    *,
    eps: float = 1.0e-6,
    warm_start: bool = True,
    max_columns_per_pricing: int = 20,
    max_pool_size: int = 200,
    pool_score_margin: float = 50.0,
    stabilized_pricing: bool = True,
    stabilization_alpha: float = 0.7,
    stabilization_min_alpha: float = 0.2,
    stabilization_max_alpha: float = 0.95,
    stabilization_label_limit: int = 20000,
    stabilization_volatility_threshold: float = 0.25,
    pricing_preprocess: bool = True,
    rmp_params: dict[str, Any] | None = None,
):
    from pyscipopt import Model, quicksum

    tasks = task_ids(instance)
    model = Model("vehicle_schedule_branch_price")

    cover_cons = {}
    for task_id in tasks:
        cover_cons[task_id] = model.addCons(quicksum([]) == 1, name=f"cover[{task_id}]", modifiable=True)

    artificial = {}
    for task_id in tasks:
        artificial[task_id] = model.addVar(vtype="B", lb=0.0, ub=1.0, obj=ARTIFICIAL_TASK_PENALTY, name=f"phase1_artificial_cover[{task_id}]")
        model.addCoefLinear(cover_cons[task_id], artificial[task_id], 1.0)

    vehicle_count_cons = model.addCons(quicksum([]) <= int(instance["vehicles"]["R_bar"]), name="vehicle_count", modifiable=True)

    for name, value in (rmp_params or {}).items():
        _try_set_param(model, name, value)

    data = {"tasks": tasks, "cover_cons": cover_cons, "vehicle_count_cons": vehicle_count_cons, "artificial": artificial}
    pricer = VehicleSchedulePricer(
        instance,
        pairwise,
        data,
        eps=eps,
        max_columns_per_pricing=max_columns_per_pricing,
        max_pool_size=max_pool_size,
        pool_score_margin=pool_score_margin,
        stabilized_pricing=stabilized_pricing,
        stabilization_alpha=stabilization_alpha,
        stabilization_min_alpha=stabilization_min_alpha,
        stabilization_max_alpha=stabilization_max_alpha,
        stabilization_label_limit=stabilization_label_limit,
        stabilization_volatility_threshold=stabilization_volatility_threshold,
        pricing_preprocess=pricing_preprocess,
    )
    model.includePricer(pricer.plugin, "vehicle_schedule_pricer", "严格车辆日程列生成器", priority=1, delay=True)

    for task_id in tasks:
        schedule = evaluate_schedule(instance, pairwise, ((int(task_id),),))
        if schedule is not None:
            pricer.add_column(model, schedule, priced_var=False, source="initial")

    warm_start_info = {"enabled": False}
    if warm_start:
        schedules, uncovered = _build_warm_start_schedules(instance, pairwise)
        for schedule in schedules:
            pricer.add_column(model, schedule, priced_var=False, source="warm_start")
        warm_start_info = {
            "enabled": True,
            "routes": sum(len(schedule["routes"]) for schedule in schedules),
            "schedules": len(schedules),
            "covered_tasks": len(set(tasks) - set(uncovered)),
            "uncovered_tasks": sorted(uncovered),
        }
        try:
            solution = model.createSol()
            selected = {tuple(tuple(route) for route in schedule["key"]) for schedule in schedules}
            for schedule in pricer.schedules:
                model.setSolVal(solution, schedule["var"], 1.0 if schedule["key"] in selected else 0.0)
            for task_id, var in artificial.items():
                model.setSolVal(solution, var, 1.0 if task_id in uncovered else 0.0)
            added = model.addSol(solution)
            warm_start_info["submitted"] = True if added is None else bool(added)
        except Exception:
            warm_start_info["submitted"] = False
    data["warm_start"] = warm_start_info
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
    max_columns_per_pricing: int = 20,
    max_pool_size: int = 200,
    pool_score_margin: float = 50.0,
    stabilized_pricing: bool = True,
    stabilization_alpha: float = 0.7,
    stabilization_min_alpha: float = 0.2,
    stabilization_max_alpha: float = 0.95,
    stabilization_label_limit: int = 20000,
    stabilization_volatility_threshold: float = 0.25,
    pricing_preprocess: bool = True,
    rmp_params: dict[str, Any] | None = None,
    memory_limit_mb: float | None = None,
):
    model, pricer, data = build_branch_price_model(
        instance,
        pairwise,
        eps=eps,
        warm_start=warm_start,
        max_columns_per_pricing=max_columns_per_pricing,
        max_pool_size=max_pool_size,
        pool_score_margin=pool_score_margin,
        stabilized_pricing=stabilized_pricing,
        stabilization_alpha=stabilization_alpha,
        stabilization_min_alpha=stabilization_min_alpha,
        stabilization_max_alpha=stabilization_max_alpha,
        stabilization_label_limit=stabilization_label_limit,
        stabilization_volatility_threshold=stabilization_volatility_threshold,
        pricing_preprocess=pricing_preprocess,
        rmp_params=rmp_params,
    )
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
    summary = {
        "status": _status_name(raw_status),
        "status_code": raw_status,
        "objective": round_float(_safe_call(model.getObjVal)) if has_solution else None,
        "runtime": round_float(_safe_call(model.getSolvingTime, 0.0)),
        "best_bound": round_float(_safe_call(model.getDualbound)),
        "mip_gap": round_float(_safe_call(model.getGap)) if has_solution else None,
        "node_count": round_float(_safe_call(model.getNNodes, 0.0)),
        "solution_count": solution_count,
    }

    solution = {"summary": summary, "schedules": [], "artificial_tasks": []}
    if has_solution:
        for task_id, var in data["artificial"].items():
            if float(model.getVal(var)) > 0.5:
                solution["artificial_tasks"].append(int(task_id))
        for schedule in pricer.schedules:
            if model.getVal(schedule["var"]) <= 0.5:
                continue
            clean = {key: value for key, value in schedule.items() if key not in {"var"}}
            solution["schedules"].append(clean)
    solution["summary"]["uses_artificial"] = bool(solution["artificial_tasks"])
    solution["summary"]["artificial_task_count"] = len(solution["artificial_tasks"])

    route_keys = {tuple(route) for schedule in pricer.schedules for route in schedule["key"]}
    clean_schedules = [_clean_schedule(schedule) for schedule in pricer.schedules]
    report = {
        "mode": "vehicle_schedule_branch_price",
        "generated_routes": len(route_keys),
        "generated_columns": len(pricer.schedules),
        "priced_columns": pricer.generated_by_redcost + pricer.generated_by_farkas,
        "redcost_columns": pricer.generated_by_redcost,
        "farkas_columns": pricer.generated_by_farkas,
        "redcost_calls": pricer.redcost_calls,
        "farkas_calls": pricer.farkas_calls,
        "pricing_calls": pricer.redcost_calls + pricer.farkas_calls,
        "early_pricing_returns": pricer.early_pricing_returns,
        "pricing_batch_cap_hits": pricer.pricing_batch_cap_hits,
        "max_columns_per_pricing": pricer.max_columns_per_pricing,
        "pool_size": len(pricer.column_pool),
        "max_pool_size": pricer.max_pool_size,
        "pool_score_margin": pricer.pool_score_margin,
        "pool_scans": pricer.pool_scans,
        "pool_hits": pricer.pool_hits,
        "pool_columns_added": pricer.pool_columns_added,
        "pool_evictions": pricer.pool_evictions,
        "pool_rejected_full": pricer.pool_rejected_full,
        "pool_replaced_worst": pricer.pool_replaced_worst,
        "pool_skipped_by_margin": pricer.pool_skipped_by_margin,
        "stabilized_pricing": pricer.stabilized_pricing,
        "stabilization_alpha": pricer.stabilization_alpha,
        "stabilization_min_alpha": pricer.stabilization_min_alpha,
        "stabilization_max_alpha": pricer.stabilization_max_alpha,
        "stabilization_label_limit": pricer.stabilization_label_limit,
        "stabilization_volatility_threshold": pricer.stabilization_volatility_threshold,
        "last_dual_volatility": pricer.last_dual_volatility,
        "stabilized_calls": pricer.stabilized_calls,
        "stabilized_hits": pricer.stabilized_hits,
        "stabilized_columns_added": pricer.stabilized_columns_added,
        "stabilized_fallbacks": pricer.stabilized_fallbacks,
        "exact_fallback_calls": pricer.exact_fallback_calls,
        "stabilized_label_pops": pricer.stabilized_label_pops,
        "exact_label_pops": pricer.exact_label_pops,
        "alpha_increases": pricer.alpha_increases,
        "alpha_decreases": pricer.alpha_decreases,
        "open_label_dominance": "covered_current_node_used_sorties_with_return_ready",
        "pricing_preprocess_enabled": pricer.pricing_preprocess_enabled,
        "pricing_preprocess": pricer.preprocess.to_report(),
        "preprocess_skip_depot_start": pricer.preprocess_skip_depot_start,
        "preprocess_skip_task_arc": pricer.preprocess_skip_task_arc,
        "preprocess_skip_return_to_depot": pricer.preprocess_skip_return_to_depot,
        "dominated_labels": pricer.dominated_labels,
        "artificial_penalty": ARTIFICIAL_TASK_PENALTY,
        "warm_start": data["warm_start"],
        "strict_pricing": True,
        "eps": eps,
    }
    return clean_schedules, report, solution


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
    max_pool_size: int = 200,
    pool_score_margin: float = 50.0,
    stabilized_pricing: bool = True,
    stabilization_alpha: float = 0.7,
    stabilization_min_alpha: float = 0.2,
    stabilization_max_alpha: float = 0.95,
    stabilization_label_limit: int = 20000,
    stabilization_volatility_threshold: float = 0.25,
    pricing_preprocess: bool = True,
    memory_limit_mb: float | None = None,
    artificial_penalty: float = ARTIFICIAL_TASK_PENALTY,
    rmp_params: dict[str, Any] | None = None,
    seed: int | None = None,
    log_level: str = "progress",
) -> BPResult:
    del integer_tol, max_cg_iterations_per_node, artificial_penalty
    schedules, report, solution = solve_branch_price(
        instance,
        pairwise,
        time_limit=time_limit,
        node_limit=max_nodes,
        verbose=log_level != "quiet",
        eps=pricing_eps,
        warm_start=True,
        max_columns_per_pricing=max_columns_per_pricing,
        max_pool_size=max_pool_size,
        pool_score_margin=pool_score_margin,
        stabilized_pricing=stabilized_pricing,
        stabilization_alpha=stabilization_alpha,
        stabilization_min_alpha=stabilization_min_alpha,
        stabilization_max_alpha=stabilization_max_alpha,
        stabilization_label_limit=stabilization_label_limit,
        stabilization_volatility_threshold=stabilization_volatility_threshold,
        pricing_preprocess=pricing_preprocess,
        rmp_params=rmp_params,
        memory_limit_mb=memory_limit_mb,
    )
    if solution_path is not None:
        write_json(solution_path, {"schedules": schedules, "report": report, "solution": solution})
    if log_path is not None:
        ensure_dir(Path(log_path).parent)
        write_json(log_path, {"summary": solution["summary"], "report": report})

    summary = solution["summary"]
    uses_artificial = bool(summary.get("uses_artificial"))
    primal = None if uses_artificial else summary.get("objective")
    return BPResult(
        instance=str(instance.get("name", "instance")),
        task_count=len(task_ids(instance)),
        vehicle_count=int(instance["vehicles"]["R_bar"]),
        sortie_count=int(instance["vehicles"]["S_bar"]),
        status=str(summary.get("status", "UNKNOWN")),
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
