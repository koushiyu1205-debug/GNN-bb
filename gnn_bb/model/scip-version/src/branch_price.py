"""中文摘要：本文件实现严格分支定价模型，在 SCIP 分支定界过程中通过 Pricer 动态生成路径列。"""

from dataclasses import dataclass, field
import heapq
from math import isfinite

from .io_utils import round_float
from .route_generation import evaluate_route, task_ids
from .terrain import arc_key


DOMINANCE_TOL = 1.0e-9
ARTIFICIAL_TASK_PENALTY = 1.0e6


@dataclass(order=True)
class Label:
    # 中文注释：priority 只影响搜索顺序，不截断搜索，因此不破坏 pricing 的完整性。
    priority: float
    node: int = field(compare=False)
    task_id: int | None = field(compare=False)
    parent: object = field(compare=False)
    visited: frozenset = field(compare=False)
    time: float = field(compare=False)
    load: float = field(compare=False)
    energy: float = field(compare=False)
    travel_time: float = field(compare=False)
    cost: float = field(compare=False)
    service_start_time: float | None = field(compare=False)
    arc_path: list | None = field(compare=False)


def _task_value(instance, task_id, field_name):
    return float(instance["tasks"][str(task_id)][field_name])


def _route_signature(route):
    return tuple(int(task) for task in route["tasks"])


def _status_name(status):
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


class RouteSlotPricer:
    """中文注释：Pricer 负责在每个 LP 节点后寻找负 reduced cost 的路径-槽位变量。"""

    def __init__(self, instance, pairwise, data, eps=1.0e-6):
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
        self.routes = []
        self.route_by_signature = {}
        self.columns = []
        self.column_keys = set()
        self.column_by_key = {}
        self.generated_by_redcost = 0
        self.generated_by_farkas = 0
        self.redcost_calls = 0
        self.farkas_calls = 0
        self.early_pricing_returns = 0
        self.dominated_labels = 0

    def on_pricer_init(self, model):
        # 中文注释：进入求解阶段后，SCIP 会把原问题对象变换成内部对象；这里更新约束引用。
        self.data["cover_cons"] = {k: model.getTransformedCons(cons) for k, cons in self.data["cover_cons"].items()}
        self.data["slot_cons"] = {key: model.getTransformedCons(cons) for key, cons in self.data["slot_cons"].items()}
        self.data["vehicle_time_cons"] = {r: model.getTransformedCons(cons) for r, cons in self.data["vehicle_time_cons"].items()}

    def _register_route(self, route):
        signature = _route_signature(route)
        existing = self.route_by_signature.get(signature)
        if existing is not None:
            return existing
        route = dict(route)
        route["id"] = len(self.routes)
        self.routes.append(route)
        self.route_by_signature[signature] = route
        return route

    def add_column(self, model, route, r, s, priced_var, source="initial"):
        route = self._register_route(route)
        key = (route["id"], r, s)
        if key in self.column_keys:
            return False

        var = model.addVar(
            name=f"x[{route['id']},{r},{s}]",
            vtype="B",
            lb=0.0,
            ub=1.0,
            obj=float(route["cost"]),
            pricedVar=priced_var,
        )
        # 中文注释：新列必须加入所有含有它的主问题约束；这些约束在建模时都设置为 modifiable。
        for task_id in route["task_set"]:
            model.addCoefLinear(self.data["cover_cons"][int(task_id)], var, 1.0)
        model.addCoefLinear(self.data["slot_cons"][r, s], var, 1.0)
        model.addCoefLinear(self.data["vehicle_time_cons"][r], var, float(route["cycle_time"]))

        column = {"var": var, "route_id": route["id"], "vehicle": r, "sortie": s, "source": source}
        self.columns.append(column)
        self.column_keys.add(key)
        self.column_by_key[key] = column
        if source == "redcost":
            self.generated_by_redcost += 1
        elif source == "farkas":
            self.generated_by_farkas += 1
        return True

    def find_column(self, route, r, s):
        signature = _route_signature(route)
        existing = self.route_by_signature.get(signature)
        if existing is None:
            return None
        key = (existing["id"], r, s)
        return self.column_by_key.get(key)

    def _duals(self, model):
        cover_duals = {k: float(model.getDualsolLinear(cons)) for k, cons in self.data["cover_cons"].items()}
        slot_duals = {key: float(model.getDualsolLinear(cons)) for key, cons in self.data["slot_cons"].items()}
        vehicle_time_duals = {r: float(model.getDualsolLinear(cons)) for r, cons in self.data["vehicle_time_cons"].items()}
        return cover_duals, slot_duals, vehicle_time_duals

    def _farkas_duals(self, model):
        # 中文注释：当 restricted master LP 不可行时，SCIP 给出 Farkas 对偶射线。
        # 对新路径列 x_j，只看它在可修改主约束中的系数 a_j；若 pi^T a_j > 0，
        # 该列有机会切断当前不可行性证明，必须通过 Farkas pricing 加入。
        cover_duals = {k: float(model.getDualfarkasLinear(cons)) for k, cons in self.data["cover_cons"].items()}
        slot_duals = {key: float(model.getDualfarkasLinear(cons)) for key, cons in self.data["slot_cons"].items()}
        vehicle_time_duals = {r: float(model.getDualfarkasLinear(cons)) for r, cons in self.data["vehicle_time_cons"].items()}
        return cover_duals, slot_duals, vehicle_time_duals

    def _label_chain(self, label):
        chain = []
        cursor = label
        while cursor.parent is not None:
            chain.append(cursor)
            cursor = cursor.parent
        chain.reverse()
        return chain

    def _label_sequence(self, label):
        # 中文注释：标签内部只保存 parent pointer；只有准备加列或输出路径时才回溯完整任务序列。
        return tuple(node.task_id for node in self._label_chain(label))

    def _route_summary_from_label(self, label):
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

    def _complete_route_from_label(self, label, summary=None):
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
            "physical_paths": [*physical_paths, {"from": label.node, "to": 0, "path": return_segment["path"]}],
        }

    def _reduced_cost(self, route, r, s, cover_duals, slot_duals, vehicle_time_duals):
        # 中文注释：SCIP 的列 reduced cost 按 c_j - y^T A_j 计算；这里 A_j 是该路径列在各主约束中的系数。
        return (
            float(route["cost"])
            - sum(float(cover_duals[int(task_id)]) for task_id in route["task_set"])
            - float(slot_duals[r, s])
            - float(vehicle_time_duals[r]) * float(route["cycle_time"])
        )

    def _farkas_score(self, route, r, s, cover_duals, slot_duals, vehicle_time_duals):
        # 中文注释：SCIP 文档中 Farkas pricing 要找 pi^T A_j > 0 的列。
        # 为了和 reduced cost pricing 共用“越小越好、< -eps 加列”的流程，这里返回 -pi^T A_j。
        farkas_value = (
            sum(float(cover_duals[int(task_id)]) for task_id in route["task_set"])
            + float(slot_duals[r, s])
            + float(vehicle_time_duals[r]) * float(route["cycle_time"])
        )
        return -farkas_value

    def _column_already_exists_by_signature(self, signature, r, s):
        existing = self.route_by_signature.get(signature)
        return existing is not None and (existing["id"], r, s) in self.column_keys

    def _column_score(self, route, r, s, cover_duals, slot_duals, vehicle_time_duals, pricing_mode):
        if pricing_mode == "farkas":
            return self._farkas_score(route, r, s, cover_duals, slot_duals, vehicle_time_duals)
        return self._reduced_cost(route, r, s, cover_duals, slot_duals, vehicle_time_duals)

    def _label_priority(self, sequence, cost, cover_duals, pricing_mode):
        # 中文注释：priority 只决定标签弹出顺序，不作为剪枝条件；Farkas 模式下原目标成本不参与判定。
        dual_sum = sum(float(cover_duals[task]) for task in sequence)
        if pricing_mode == "farkas":
            return -dual_sum
        return cost - dual_sum

    def _dominates(self, left, right):
        # 中文注释：只在“当前位置相同、已访问任务集合完全相同”时做 dominance。
        # 这比常见的 visited-subset dominance 更保守，但不会误删覆盖任务集合不同的列。
        if left.node != right.node or left.visited != right.visited:
            return False
        return (
            left.time <= right.time + DOMINANCE_TOL
            and left.load <= right.load + DOMINANCE_TOL
            and left.energy <= right.energy + DOMINANCE_TOL
            and left.cost <= right.cost + DOMINANCE_TOL
        )

    def _is_dominated_or_record(self, label, nondominated):
        key = (label.node, label.visited)
        labels = nondominated.setdefault(key, [])
        for existing in labels:
            if self._dominates(existing, label):
                return True

        kept = []
        for existing in labels:
            if not self._dominates(label, existing):
                kept.append(existing)
        kept.append(label)
        nondominated[key] = kept
        return False

    def _exact_pricing(self, cover_duals, slot_duals, vehicle_time_duals, pricing_mode, stop_after_first_route=False):
        tasks = task_ids(self.instance)
        vehicles = self.instance["vehicles"]
        q_limit = float(vehicles["Q"])
        b_limit = float(vehicles["B_use"])
        horizon = float(vehicles["H"])
        best_columns = []
        # 中文注释：只有当车辆时间对偶不奖励更长 cycle_time 时，资源 dominance 才是安全的。
        # SCIP 对 <= 主约束通常给出非正对偶；若遇到正值，就关闭 dominance 保守求解。
        use_dominance = max(vehicle_time_duals.values(), default=0.0) <= DOMINANCE_TOL
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
            arc_path=None,
        )
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

                next_visited = frozenset((*label.visited, task_id))
                next_cost = label.cost + float(segment["cost"]) + _task_value(self.instance, task_id, "c_srv")
                next_label = Label(
                    priority=self._label_priority(next_visited, next_cost, cover_duals, pricing_mode),
                    node=task_id,
                    task_id=task_id,
                    parent=label,
                    visited=next_visited,
                    time=finish,
                    load=next_load,
                    energy=next_energy,
                    travel_time=label.travel_time + float(segment["tau"]),
                    cost=next_cost,
                    service_start_time=start,
                    arc_path=segment["path"],
                )
                if use_dominance and self._is_dominated_or_record(next_label, nondominated):
                    self.dominated_labels += 1
                    continue

                route_summary = self._route_summary_from_label(next_label)
                route_signature = route_summary["sequence"]
                route_columns = []
                for r in self.data["R"]:
                    for s in self.data["S"]:
                        if self._column_already_exists_by_signature(route_signature, r, s):
                            continue
                        score = self._column_score(route_summary, r, s, cover_duals, slot_duals, vehicle_time_duals, pricing_mode)
                        if score < -self.eps:
                            route_columns.append((score, r, s))
                if route_columns:
                    route = self._complete_route_from_label(next_label, route_summary)
                    best_columns.extend((score, route, r, s) for score, r, s in route_columns)
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
        cover_duals, slot_duals, vehicle_time_duals = self._duals(model)
        priced_columns = self._exact_pricing(
            cover_duals,
            slot_duals,
            vehicle_time_duals,
            pricing_mode="redcost",
            stop_after_first_route=True,
        )
        added = 0
        for _, route, r, s in priced_columns:
            if self.add_column(model, route, r, s, priced_var=True, source="redcost"):
                added += 1

        return {"result": SCIP_RESULT.SUCCESS}

    def on_pricer_farkas(self, model):
        from pyscipopt import SCIP_RESULT

        self.farkas_calls += 1
        cover_duals, slot_duals, vehicle_time_duals = self._farkas_duals(model)
        priced_columns = self._exact_pricing(
            cover_duals,
            slot_duals,
            vehicle_time_duals,
            pricing_mode="farkas",
            stop_after_first_route=True,
        )
        added = 0
        for _, route, r, s in priced_columns:
            if self.add_column(model, route, r, s, priced_var=True, source="farkas"):
                added += 1

        return {"result": SCIP_RESULT.SUCCESS}


def _build_initial_routes(instance, pairwise):
    routes = []
    for task_id in task_ids(instance):
        route = evaluate_route(instance, pairwise, [task_id])
        if route is None:
            raise ValueError(f"任务 {task_id} 无法作为单任务路径独立可行")
        routes.append(route)
    return routes


def _task_order(instance, tasks):
    return sorted(tasks, key=lambda task_id: (_task_value(instance, task_id, "D"), _task_value(instance, task_id, "r"), task_id))


def _best_insert_route(instance, pairwise, sequence, uncovered, remaining_cycle_time):
    best = None
    for task_id in _task_order(instance, uncovered):
        for position in range(len(sequence) + 1):
            candidate_sequence = [*sequence[:position], task_id, *sequence[position:]]
            route = evaluate_route(instance, pairwise, candidate_sequence)
            if route is None:
                continue
            if float(route["cycle_time"]) > remaining_cycle_time + 1.0e-9:
                continue
            score = (
                float(route["cycle_time"]),
                float(route["cost"]),
                _task_value(instance, task_id, "D"),
                task_id,
            )
            if best is None or score < best[0]:
                best = (score, route)
    return None if best is None else best[1]


def _build_warm_start_assignments(instance, pairwise, R, S):
    # 中文注释：warm start 只用于给 SCIP 一个可行起点和若干真实路径列；
    # 它不限制后续 pricing 的完整搜索，因此不改变最终最优性。
    horizon = float(instance["vehicles"]["H"])
    uncovered = set(task_ids(instance))
    vehicle_cycle_time = {r: 0.0 for r in R}
    assignments = []

    for r in R:
        for s in S:
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
            assignments.append({"vehicle": r, "sortie": s, "route": route})
            vehicle_cycle_time[r] += float(route["cycle_time"])
        if not uncovered:
            break

    return assignments, uncovered


def _submit_warm_start_solution(model, pricer, data, assignments, uncovered_tasks):
    try:
        solution = model.createSol()
        selected_columns = set()
        used_slots = set()
        used_vehicles = set()

        for assignment in assignments:
            column = pricer.find_column(assignment["route"], assignment["vehicle"], assignment["sortie"])
            if column is None:
                continue
            selected_columns.add((column["route_id"], column["vehicle"], column["sortie"]))
            used_slots.add((assignment["vehicle"], assignment["sortie"]))
            used_vehicles.add(assignment["vehicle"])

        for column in pricer.columns:
            key = (column["route_id"], column["vehicle"], column["sortie"])
            model.setSolVal(solution, column["var"], 1.0 if key in selected_columns else 0.0)
        for (r, s), var in data["z"].items():
            model.setSolVal(solution, var, 1.0 if (r, s) in used_slots else 0.0)
        for r, var in data["y"].items():
            model.setSolVal(solution, var, 1.0 if r in used_vehicles else 0.0)
        for task_id, var in data["artificial"].items():
            model.setSolVal(solution, var, 1.0 if task_id in uncovered_tasks else 0.0)

        result = model.addSol(solution)
        return True if result is None else bool(result)
    except Exception:
        return False


def _add_warm_start(model, pricer, data, instance, pairwise):
    assignments, uncovered = _build_warm_start_assignments(instance, pairwise, data["R"], data["S"])
    for assignment in assignments:
        pricer.add_column(
            model,
            assignment["route"],
            assignment["vehicle"],
            assignment["sortie"],
            priced_var=False,
            source="warm_start",
        )

    submitted = _submit_warm_start_solution(model, pricer, data, assignments, uncovered)
    covered_tasks = sorted(set(task_ids(instance)) - set(uncovered))
    return {
        "enabled": True,
        "submitted": submitted,
        "routes": len(assignments),
        "covered_tasks": len(covered_tasks),
        "uncovered_tasks": sorted(uncovered),
    }


def build_branch_price_model(instance, pairwise, eps=1.0e-6, warm_start=True):
    from pyscipopt import Model, quicksum

    vehicles = instance["vehicles"]
    tasks = task_ids(instance)
    R = list(range(1, int(vehicles["R_bar"]) + 1))
    S = list(range(1, int(vehicles["S_bar"]) + 1))
    fixed_vehicle_cost = float(vehicles["F"])
    horizon = float(vehicles["H"])

    model = Model("branch_price_cvrptw_scip")
    z = {(r, s): model.addVar(vtype="B", name=f"z[{r},{s}]") for r in R for s in S}
    y = {r: model.addVar(vtype="B", obj=fixed_vehicle_cost, name=f"y[{r}]") for r in R}

    # 中文注释：这些主问题约束后续会被 pricer 添加新列，因此必须设置 modifiable=True。
    cover_cons = {}
    for task_id in tasks:
        cover_cons[task_id] = model.addCons(quicksum([]) == 1, name=f"cover[{task_id}]", modifiable=True)

    artificial = {}
    for task_id in tasks:
        artificial[task_id] = model.addVar(
            vtype="B",
            lb=0.0,
            ub=1.0,
            obj=ARTIFICIAL_TASK_PENALTY,
            name=f"phase1_artificial_cover[{task_id}]",
        )
        # 中文注释：Phase-I 人工列只用于保证 restricted master 初始可行。
        # 最终若仍有人工列取 1，该解不能视为原问题可行解。
        model.addCoefLinear(cover_cons[task_id], artificial[task_id], 1.0)

    slot_cons = {}
    for r in R:
        for s in S:
            slot_cons[r, s] = model.addCons(quicksum([]) - z[r, s] == 0, name=f"slot[{r},{s}]", modifiable=True)
            model.addCons(z[r, s] <= y[r], name=f"slot_requires_vehicle[{r},{s}]")

    vehicle_time_cons = {}
    for r in R:
        vehicle_time_cons[r] = model.addCons(quicksum([]) - horizon * y[r] <= 0, name=f"vehicle_cycle_time[{r}]", modifiable=True)

    for r in R:
        for s in S[:-1]:
            model.addCons(z[r, s + 1] <= z[r, s], name=f"sortie_sequence[{r},{s}]")
    for r in R[:-1]:
        model.addCons(y[r + 1] <= y[r], name=f"vehicle_sequence[{r}]")

    data = {
        "R": R,
        "S": S,
        "tasks": tasks,
        "z": z,
        "y": y,
        "artificial": artificial,
        "cover_cons": cover_cons,
        "slot_cons": slot_cons,
        "vehicle_time_cons": vehicle_time_cons,
    }
    pricer = RouteSlotPricer(instance, pairwise, data, eps=eps)
    # 中文注释：PySCIPOpt 6.1 没有 activatePricer；includePricer 会把 Python Pricer 注册给 SCIP 调用。
    model.includePricer(pricer.plugin, "route_slot_pricer", "严格分支定价路径列生成器", priority=1, delay=True)

    for route in _build_initial_routes(instance, pairwise):
        for r in R:
            for s in S:
                pricer.add_column(model, route, r, s, priced_var=False)

    data["warm_start"] = _add_warm_start(model, pricer, data, instance, pairwise) if warm_start else {"enabled": False}
    return model, pricer, data


def solve_branch_price(instance, pairwise, time_limit=None, verbose=True, eps=1.0e-6, warm_start=True):
    model, pricer, data = build_branch_price_model(instance, pairwise, eps=eps, warm_start=warm_start)
    if time_limit is not None:
        model.setParam("limits/time", float(time_limit))
    model.setParam("display/verblevel", 4 if verbose else 0)
    model.optimize()

    solution_count = int(_safe_call(model.getNSols, 0) or 0)
    has_solution = solution_count > 0
    raw_status = str(_safe_call(model.getStatus, "unknown"))
    summary = {
        "status": _status_name(raw_status),
        "status_code": raw_status,
        "objective": round_float(_safe_call(model.getObjVal)) if has_solution else None,
        "runtime": round_float(_safe_call(model.getSolvingTime, 0.0)),
        "best_bound": round_float(_safe_call(model.getDualbound)) if has_solution else None,
        "mip_gap": round_float(_safe_call(model.getGap)) if has_solution else None,
        "node_count": round_float(_safe_call(model.getNNodes, 0.0)),
        "solution_count": solution_count,
    }

    solution = {"summary": summary, "vehicles": {}, "sorties": [], "selected_route_ids": [], "artificial_tasks": []}
    if has_solution:
        for r in data["R"]:
            solution["vehicles"][str(r)] = round_float(model.getVal(data["y"][r]))
        for task_id, var in data["artificial"].items():
            value = float(model.getVal(var))
            if value > 0.5:
                solution["artificial_tasks"].append(int(task_id))
        route_by_id = {route["id"]: route for route in pricer.routes}
        for column in pricer.columns:
            if model.getVal(column["var"]) <= 0.5:
                continue
            route = route_by_id[column["route_id"]]
            solution["selected_route_ids"].append(route["id"])
            solution["sorties"].append(
                {
                    "vehicle": column["vehicle"],
                    "sortie": column["sortie"],
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
        "mode": "branch_price",
        "generated_routes": len(pricer.routes),
        "generated_columns": len(pricer.columns),
        "priced_columns": pricer.generated_by_redcost + pricer.generated_by_farkas,
        "redcost_columns": pricer.generated_by_redcost,
        "farkas_columns": pricer.generated_by_farkas,
        "redcost_calls": pricer.redcost_calls,
        "farkas_calls": pricer.farkas_calls,
        "early_pricing_returns": pricer.early_pricing_returns,
        "dominated_labels": pricer.dominated_labels,
        "artificial_penalty": ARTIFICIAL_TASK_PENALTY,
        "warm_start": data["warm_start"],
        "strict_pricing": True,
        "eps": eps,
    }
    return pricer.routes, report, solution
