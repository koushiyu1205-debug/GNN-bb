"""中文摘要：本文件实现最小 route-vehicle branch-price-and-cut。列仍是单条 sortie route-vehicle 变量，pricing 仍是 RCSP；新增 no-good cuts 用 exact schedule checker 排除同一车辆不可排序的 route 组合。"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import time
from typing import Any

from gnn_bb.bp.route_slot_branch_price import (
    ARTIFICIAL_TASK_PENALTY,
    BPResult,
    RouteVehiclePricer,
    _add_warm_start,
    _build_initial_routes,
    _route_signature,
    _safe_call,
    _status_name,
    _try_set_param,
    _task_value,
    evaluate_route,
)
from gnn_bb.bp.schedule_checker import (
    check_route_set_schedule_feasible,
    find_pairwise_incompatible_cuts,
    route_signature,
    route_work_time_lower_bound,
    shrink_infeasible_route_set,
)
from gnn_bb.data.instances import task_ids
from gnn_bb.data.io_utils import ensure_dir, round_float, write_json


INTEGRAL_TOL = 1.0e-6


def _cut_signatures(signatures: list[tuple[int, ...]] | tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(sorted(tuple(int(task) for task in signature) for signature in signatures))


def _cut_key(signatures: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return _cut_signatures(signatures)


class RouteVehicleBPCPricer(RouteVehiclePricer):
    """中文注释：带 schedule no-good cuts 的 route-vehicle pricer。新列若属于某个 cut，必须在该 cut 中带系数。"""

    def on_pricer_init(self, model) -> None:
        super().on_pricer_init(model)
        for cut in self.data["schedule_cuts"]:
            cut["cons"] = model.getTransformedCons(cut["cons"])

    def _route_time_coefficient(self, route: dict[str, Any]) -> float:
        return route_work_time_lower_bound(self.instance, route)

    def _matching_schedule_cuts(self, route: dict[str, Any], r: int) -> list[dict[str, Any]]:
        signature = route_signature(route)
        return [
            cut
            for cut in self.data["schedule_cuts"]
            if int(cut["vehicle"]) == int(r) and signature in cut["signatures"]
        ]

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
        model.addCoefLinear(self.data["vehicle_time_cons"][int(r)], var, self._route_time_coefficient(route))
        for cut in self._matching_schedule_cuts(route, r):
            model.addCoefLinear(cut["cons"], var, 1.0)

        column = {"var": var, "route_id": int(route["id"]), "vehicle": int(r), "source": source}
        self.columns.append(column)
        self.column_keys.add(key)
        self.column_by_key[key] = column
        if source == "redcost":
            self.generated_by_redcost += 1
        elif source == "farkas":
            self.generated_by_farkas += 1
        return True

    def _schedule_cut_duals(self, model, farkas: bool = False) -> list[float]:
        values = []
        for cut in self.data["schedule_cuts"]:
            getter = model.getDualfarkasLinear if farkas else model.getDualsolLinear
            values.append(float(getter(cut["cons"])))
        return values

    def on_pricer_redcost(self, model):
        self.current_schedule_cut_duals = self._schedule_cut_duals(model, farkas=False)
        return super().on_pricer_redcost(model)

    def on_pricer_farkas(self, model):
        self.current_schedule_cut_duals = self._schedule_cut_duals(model, farkas=True)
        return super().on_pricer_farkas(model)

    def _cut_dual_contribution(self, route: dict[str, Any], r: int) -> float:
        signature = route_signature(route)
        total = 0.0
        for index, cut in enumerate(self.data["schedule_cuts"]):
            if int(cut["vehicle"]) == int(r) and signature in cut["signatures"]:
                total += float(getattr(self, "current_schedule_cut_duals", [0.0] * len(self.data["schedule_cuts"]))[index])
        return total

    def _reduced_cost(self, route: dict[str, Any], r: int, cover_duals, sortie_count_duals, vehicle_time_duals) -> float:
        return (
            float(route["cost"])
            - sum(float(cover_duals[int(task_id)]) for task_id in route["task_set"])
            - float(sortie_count_duals[int(r)])
            - float(vehicle_time_duals[int(r)]) * self._route_time_coefficient(route)
            - self._cut_dual_contribution(route, r)
        )

    def _farkas_score(self, route: dict[str, Any], r: int, cover_duals, sortie_count_duals, vehicle_time_duals) -> float:
        farkas_value = (
            sum(float(cover_duals[int(task_id)]) for task_id in route["task_set"])
            + float(sortie_count_duals[int(r)])
            + float(vehicle_time_duals[int(r)]) * self._route_time_coefficient(route)
            + self._cut_dual_contribution(route, r)
        )
        return -farkas_value

    def _can_use_dominance(self, vehicle_time_duals) -> bool:
        return super()._can_use_dominance(vehicle_time_duals)

    def _dominance_key(self, label):
        if self.data.get("schedule_cuts"):
            # 中文注释：schedule cut duals 依赖完整 route 签名；只有相同前缀序列的标签才安全比较。
            return (label.node, label.visited, self._label_sequence(label))
        return super()._dominance_key(label)


class ScheduleFeasibilityConshdlr:
    """中文注释：SCIP 树内日程可行性约束处理器。只对整数候选解分离安全 no-good cuts。"""

    def __init__(
        self,
        instance: dict[str, Any],
        pairwise: dict[str, dict[str, Any]],
        data: dict[str, Any],
        pricer: RouteVehicleBPCPricer,
        cut_keys: set[tuple[tuple[int, ...], ...]],
        raw_cuts: list[dict[str, Any]],
        tol: float = INTEGRAL_TOL,
    ):
        from pyscipopt import Conshdlr

        class _Conshdlr(Conshdlr):
            def __init__(self, outer):
                super().__init__()
                self.outer = outer

            def conscheck(self, constraints, solution, checkintegrality, checklprows, printreason, completely):
                return self.outer.conscheck(solution)

            def consenfolp(self, constraints, nusefulconss, solinfeasible):
                return self.outer.enforce_current_solution()

            def consenfops(self, constraints, nusefulconss, solinfeasible, objinfeasible):
                return self.outer.enforce_current_solution()

            def conssepasol(self, constraints, nusefulconss, solution):
                return self.outer.separate_solution(solution)

            def conslock(self, constraint, locktype, nlockspos, nlocksneg):
                return None

        self.plugin = _Conshdlr(self)
        self.instance = instance
        self.pairwise = pairwise
        self.data = data
        self.pricer = pricer
        self.cut_keys = cut_keys
        self.raw_cuts = raw_cuts
        self.tol = tol
        self.check_calls = 0
        self.enforce_calls = 0
        self.sepasol_calls = 0
        self.cuts_added = 0
        self.cut_constraints_added = 0
        self.infeasible_solutions = 0
        self.generated_cuts: list[dict[str, Any]] = []
        self.last_conflicts: list[dict[str, Any]] = []

    @property
    def model(self):
        return self.plugin.model

    def _value(self, solution, var) -> float:
        if solution is None:
            return float(self.model.getVal(var))
        return float(self.model.getSolVal(solution, var))

    def _selected_routes_by_vehicle(self, solution) -> tuple[dict[int, list[dict[str, Any]]], bool]:
        route_by_id = {int(route["id"]): route for route in self.pricer.routes}
        grouped: dict[int, list[dict[str, Any]]] = {}
        fractional = False
        for column in self.pricer.columns:
            value = self._value(solution, column["var"])
            if self.tol < value < 1.0 - self.tol:
                fractional = True
            if value > 1.0 - self.tol:
                grouped.setdefault(int(column["vehicle"]), []).append(route_by_id[int(column["route_id"])])
        return grouped, fractional

    def _add_global_cut(self, source_vehicle: int, routes: list[dict[str, Any]], kind: str) -> bool:
        from pyscipopt import quicksum

        signatures = _cut_signatures([route_signature(route) for route in routes])
        key = _cut_key(signatures)
        if key in self.cut_keys:
            return False

        raw_cut = {
            "scope": "all_vehicles",
            "source_vehicle": int(source_vehicle),
            "signatures": signatures,
            "kind": kind,
        }
        self.cut_keys.add(key)
        self.raw_cuts.append(raw_cut)
        self.generated_cuts.append(raw_cut)

        route_signature_by_id = {int(route["id"]): route_signature(route) for route in self.pricer.routes}
        for r in self.data["R"]:
            variables = [
                column["var"]
                for column in self.pricer.columns
                if int(column["vehicle"]) == int(r) and route_signature_by_id[int(column["route_id"])] in signatures
            ]
            # 中文注释：cut 对未来 priced columns 也是有效的，所以必须建成 modifiable 约束，并登记给 pricer。
            cons = self.model.addCons(
                quicksum(variables) <= len(signatures) - 1,
                name=f"schedule_lazy_nogood[{len(self.raw_cuts)-1},v{r}]",
                initial=False,
                separate=True,
                enforce=True,
                check=True,
                modifiable=True,
                dynamic=True,
            )
            self.data["schedule_cuts"].append(
                {
                    "global_cut_id": len(self.raw_cuts) - 1,
                    "vehicle": int(r),
                    "source_vehicle": int(source_vehicle),
                    "signatures": signatures,
                    "kind": kind,
                    "cons": cons,
                }
            )
            self.cut_constraints_added += 1
        self.cuts_added += 1
        return True

    def _check_and_separate(self, solution, add_cuts: bool) -> tuple[bool, int, list[dict[str, Any]], bool]:
        grouped, fractional = self._selected_routes_by_vehicle(solution)
        if fractional:
            return True, 0, [], True

        added = 0
        conflicts = []
        all_feasible = True
        for vehicle, selected in grouped.items():
            check = check_route_set_schedule_feasible(self.instance, self.pairwise, selected)
            if check.feasible:
                continue
            all_feasible = False
            conflict = shrink_infeasible_route_set(self.instance, self.pairwise, selected)
            conflict_info = {
                "vehicle": int(vehicle),
                "route_ids": [int(route["id"]) for route in conflict],
                "signatures": [list(route_signature(route)) for route in conflict],
            }
            conflicts.append(conflict_info)
            if add_cuts and self._add_global_cut(vehicle, conflict, "infeasible_route_set"):
                added += 1
            for left_sig, right_sig in find_pairwise_incompatible_cuts(self.instance, self.pairwise, conflict):
                pair_routes = [route for route in conflict if route_signature(route) in {left_sig, right_sig}]
                if len(pair_routes) == 2 and add_cuts and self._add_global_cut(vehicle, pair_routes, "pairwise_incompatible"):
                    added += 1
        self.last_conflicts = conflicts
        if not all_feasible:
            self.infeasible_solutions += 1
        return all_feasible, added, conflicts, False

    def conscheck(self, solution):
        from pyscipopt import SCIP_RESULT

        self.check_calls += 1
        feasible, _, _, fractional = self._check_and_separate(solution, add_cuts=True)
        if fractional:
            return {"result": SCIP_RESULT.FEASIBLE}
        return {"result": SCIP_RESULT.FEASIBLE if feasible else SCIP_RESULT.INFEASIBLE}

    def enforce_current_solution(self):
        from pyscipopt import SCIP_RESULT

        self.enforce_calls += 1
        feasible, added, _, fractional = self._check_and_separate(None, add_cuts=True)
        if fractional or feasible:
            return {"result": SCIP_RESULT.FEASIBLE}
        if added > 0:
            return {"result": SCIP_RESULT.CONSADDED}
        return {"result": SCIP_RESULT.SOLVELP}

    def separate_solution(self, solution):
        from pyscipopt import SCIP_RESULT

        self.sepasol_calls += 1
        feasible, added, _, fractional = self._check_and_separate(solution, add_cuts=True)
        if fractional or feasible:
            return {"result": SCIP_RESULT.DIDNOTFIND}
        if added > 0:
            return {"result": SCIP_RESULT.CONSADDED}
        return {"result": SCIP_RESULT.DIDNOTFIND}

    def stats(self) -> dict[str, Any]:
        own_cuts = [cut for cut in self.generated_cuts]
        return {
            "enabled": True,
            "check_calls": self.check_calls,
            "enforce_calls": self.enforce_calls,
            "sepasol_calls": self.sepasol_calls,
            "infeasible_solutions": self.infeasible_solutions,
            "cuts_added": self.cuts_added,
            "cut_constraints_added": self.cut_constraints_added,
            "raw_cut_count": len(own_cuts),
            "cut_kinds": {
                "infeasible_route_set": sum(1 for cut in own_cuts if cut.get("kind") == "infeasible_route_set"),
                "pairwise_incompatible": sum(1 for cut in own_cuts if cut.get("kind") == "pairwise_incompatible"),
            },
            "generated_cuts": [
                {
                    "scope": cut.get("scope", "all_vehicles"),
                    "source_vehicle": cut.get("source_vehicle"),
                    "kind": cut.get("kind", "nogood"),
                    "signatures": [list(signature) for signature in cut["signatures"]],
                }
                for cut in own_cuts
            ],
            "last_conflicts": self.last_conflicts,
        }


def _schedule_task_order(instance: dict[str, Any]) -> list[int]:
    return sorted(task_ids(instance), key=lambda task_id: (_task_value(instance, task_id, "D"), _task_value(instance, task_id, "r"), task_id))


def _schedule_route_set_cost(routes: list[dict[str, Any]]) -> float:
    return sum(float(route["cost"]) for route in routes)


def _schedule_ready_time(instance: dict[str, Any], pairwise: dict[str, dict[str, Any]], routes: list[dict[str, Any]]) -> float | None:
    checked = check_route_set_schedule_feasible(instance, pairwise, routes)
    return None if not checked.feasible else float(checked.ready_time or 0.0)


def _build_schedule_feasible_assignments(instance: dict[str, Any], pairwise: dict[str, dict[str, Any]], R: list[int], sortie_limit: int):
    # 中文注释：构造真实可排程的初始解。它只提交 incumbent，不限制后续 exact pricing。
    assigned: dict[int, list[dict[str, Any]]] = {r: [] for r in R}
    for task_id in _schedule_task_order(instance):
        best_score = None
        best_vehicle = None
        best_routes = None
        for r in R:
            current_routes = assigned[r]
            current_cost = _schedule_route_set_cost(current_routes)

            if len(current_routes) < sortie_limit:
                route = evaluate_route(instance, pairwise, [task_id])
                if route is not None:
                    candidate_routes = [*current_routes, route]
                    ready_time = _schedule_ready_time(instance, pairwise, candidate_routes)
                    if ready_time is not None:
                        score = (1, float(route["cost"]), ready_time, r, len(current_routes), tuple(route["tasks"]))
                        if best_score is None or score < best_score:
                            best_score = score
                            best_vehicle = int(r)
                            best_routes = candidate_routes

            for route_index, old_route in enumerate(current_routes):
                old_sequence = list(old_route["tasks"])
                for position in range(len(old_sequence) + 1):
                    sequence = [*old_sequence[:position], int(task_id), *old_sequence[position:]]
                    route = evaluate_route(instance, pairwise, sequence)
                    if route is None:
                        continue
                    candidate_routes = [*current_routes[:route_index], route, *current_routes[route_index + 1 :]]
                    ready_time = _schedule_ready_time(instance, pairwise, candidate_routes)
                    if ready_time is None:
                        continue
                    delta_cost = _schedule_route_set_cost(candidate_routes) - current_cost
                    score = (0, delta_cost, ready_time, r, route_index, tuple(route["tasks"]))
                    if best_score is None or score < best_score:
                        best_score = score
                        best_vehicle = int(r)
                        best_routes = candidate_routes
        if best_vehicle is None or best_routes is None:
            return None
        assigned[best_vehicle] = best_routes
    return assigned


def _submit_schedule_feasible_start(model, pricer: RouteVehicleBPCPricer, data: dict[str, Any], instance: dict[str, Any], pairwise: dict[str, dict[str, Any]]) -> dict[str, Any]:
    assignments = _build_schedule_feasible_assignments(instance, pairwise, data["R"], int(data["S_bar"]))
    if assignments is None:
        return {"enabled": True, "submitted": False, "reason": "no_schedule_feasible_assignment"}

    try:
        solution = model.createSol()
        selected = []
        used_vehicles = set()
        for r, routes in assignments.items():
            if not routes:
                continue
            used_vehicles.add(int(r))
            for route in routes:
                pricer.add_column(model, route, int(r), priced_var=False, source="schedule_start")
                column = pricer.find_column(route, int(r))
                if column is None:
                    continue
                model.setSolVal(solution, column["var"], 1.0)
                selected.append((int(r), int(column["route_id"]), list(route["tasks"])))

        for r, var in data["y"].items():
            model.setSolVal(solution, var, 1.0 if int(r) in used_vehicles else 0.0)
        for var in data["artificial"].values():
            model.setSolVal(solution, var, 0.0)

        submitted = bool(model.addSol(solution))
        return {
            "enabled": True,
            "submitted": submitted,
            "vehicles_used": len(used_vehicles),
            "routes": len(selected),
            "selected": selected,
        }
    except Exception as exc:
        return {"enabled": True, "submitted": False, "reason": type(exc).__name__, "message": str(exc)}


def build_branch_price_cut_model(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    *,
    schedule_cuts: list[dict[str, Any]] | None = None,
    eps: float = 1.0e-6,
    warm_start: bool = True,
    rmp_params: dict[str, Any] | None = None,
    tree_schedule_cuts: bool = False,
    pricing_time_budget: float = 0.0,
    pricing_progress_interval: int = 0,
    schedule_start: bool = True,
):
    from pyscipopt import Model, quicksum

    vehicles = instance["vehicles"]
    tasks = task_ids(instance)
    R = list(range(1, int(vehicles["R_bar"]) + 1))
    sortie_limit = int(vehicles["S_bar"])
    fixed_vehicle_cost = float(vehicles["F"])
    horizon = float(vehicles["H"])

    model = Model("route_vehicle_branch_price_cut")
    y = {r: model.addVar(vtype="B", obj=fixed_vehicle_cost, name=f"y[{r}]") for r in R}

    cover_cons = {}
    for task_id in tasks:
        cover_cons[task_id] = model.addCons(quicksum([]) == 1, name=f"cover[{task_id}]", modifiable=True)

    artificial = {}
    for task_id in tasks:
        artificial[task_id] = model.addVar(vtype="B", lb=0.0, ub=1.0, obj=ARTIFICIAL_TASK_PENALTY, name=f"phase1_artificial_cover[{task_id}]")
        model.addCoefLinear(cover_cons[task_id], artificial[task_id], 1.0)

    sortie_count_cons = {}
    vehicle_time_cons = {}
    for r in R:
        sortie_count_cons[r] = model.addCons(quicksum([]) - sortie_limit * y[r] <= 0, name=f"vehicle_sortie_count[{r}]", modifiable=True)
        vehicle_time_cons[r] = model.addCons(quicksum([]) - horizon * y[r] <= 0, name=f"vehicle_work_time_lb[{r}]", modifiable=True)
    for r in R[:-1]:
        model.addCons(y[r + 1] <= y[r], name=f"vehicle_sequence[{r}]")

    transformed_cuts = []
    raw_cuts = []
    cut_keys = set()
    for index, cut in enumerate(schedule_cuts or []):
        signatures = _cut_signatures(cut["signatures"])
        raw_cuts.append(
            {
                "scope": cut.get("scope", "all_vehicles"),
                "source_vehicle": cut.get("source_vehicle"),
                "signatures": signatures,
                "kind": cut.get("kind", "nogood"),
            }
        )
        cut_keys.add(_cut_key(signatures))
        for r in R:
            # 中文注释：车辆同质时，一个 route 集合若不可排程，则它在任何车辆上都不可排程。
            cons = model.addCons(
                quicksum([]) <= len(signatures) - 1,
                name=f"schedule_nogood[{index},v{r}]",
                modifiable=True,
            )
            transformed_cuts.append(
                {
                    "global_cut_id": index,
                    "vehicle": int(r),
                    "source_vehicle": cut.get("source_vehicle"),
                    "signatures": signatures,
                    "kind": cut.get("kind", "nogood"),
                    "cons": cons,
                }
            )

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
        "schedule_cuts": transformed_cuts,
        "raw_schedule_cuts": raw_cuts,
        "schedule_cut_keys": cut_keys,
        "schedule_handler": None,
        "pricing_time_budget": max(0.0, float(pricing_time_budget)),
        "pricing_progress_interval": max(0, int(pricing_progress_interval)),
    }
    pricer = RouteVehicleBPCPricer(instance, pairwise, data, eps=eps)
    model.includePricer(pricer.plugin, "route_vehicle_bpc_pricer", "带日程 cut 的路径-车辆列生成器", priority=1, delay=True)

    for route in _build_initial_routes(instance, pairwise):
        for r in R:
            pricer.add_column(model, route, r, priced_var=False)

    if tree_schedule_cuts:
        handler = ScheduleFeasibilityConshdlr(instance, pairwise, data, pricer, cut_keys, raw_cuts)
        model.includeConshdlr(
            handler.plugin,
            "schedule_feasibility_lazy",
            "真实车辆日程可行性 lazy constraint handler",
            sepapriority=100000,
            enfopriority=100000,
            chckpriority=100000,
            sepafreq=1,
            needscons=True,
        )
        model.addPyCons(
            model.createCons(
                handler.plugin,
                "schedule_feasibility_lazy_cons",
                initial=False,
                separate=True,
                enforce=True,
                check=True,
                propagate=False,
            )
        )
        data["schedule_handler"] = handler
    schedule_start_report = _submit_schedule_feasible_start(model, pricer, data, instance, pairwise) if schedule_start else {"enabled": False}
    legacy_start_report = {"enabled": False, "skipped": True}
    if warm_start and not schedule_start_report.get("submitted"):
        legacy_start_report = _add_warm_start(model, pricer, data, instance, pairwise)
    data["warm_start"] = {"schedule_feasible": schedule_start_report, "legacy": legacy_start_report}
    return model, pricer, data


def solve_branch_price_cut(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    *,
    schedule_cuts: list[dict[str, Any]] | None = None,
    time_limit: float | None = None,
    node_limit: int | None = None,
    verbose: bool = True,
    eps: float = 1.0e-6,
    warm_start: bool = True,
    rmp_params: dict[str, Any] | None = None,
    memory_limit_mb: float | None = None,
    tree_schedule_cuts: bool = False,
    pricing_time_budget: float = 0.0,
    pricing_progress_interval: int = 0,
    schedule_start: bool = True,
):
    model, pricer, data = build_branch_price_cut_model(
        instance,
        pairwise,
        schedule_cuts=schedule_cuts,
        eps=eps,
        warm_start=warm_start,
        rmp_params=rmp_params,
        tree_schedule_cuts=tree_schedule_cuts,
        pricing_time_budget=pricing_time_budget,
        pricing_progress_interval=pricing_progress_interval,
        schedule_start=schedule_start,
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
    best_solution = model.getBestSol() if has_solution else None
    raw_status = str(_safe_call(model.getStatus, "unknown"))
    pricing_budget_interrupted = bool(pricer.pricing_incomplete_due_to_budget)
    summary = {
        "status": "PRICING_TIME_BUDGET" if pricing_budget_interrupted else _status_name(raw_status),
        "status_code": raw_status,
        "objective": round_float(_safe_call(model.getObjVal)) if has_solution else None,
        "runtime": round_float(_safe_call(model.getSolvingTime, 0.0)),
        # 中文注释：pricing 未完成时，dual/gap 不是完整定价后的有效证明，必须置空。
        "best_bound": None if pricing_budget_interrupted else round_float(_safe_call(model.getDualbound)),
        "mip_gap": None if pricing_budget_interrupted else (round_float(_safe_call(model.getGap)) if has_solution else None),
        "node_count": round_float(_safe_call(model.getNNodes, 0.0)),
        "solution_count": solution_count,
        "pricing_budget_interrupted": pricing_budget_interrupted,
        "pricing_budget_incomplete_phase": pricer.pricing_budget_incomplete_phase,
    }

    solution = {"summary": summary, "vehicles": {}, "sorties": [], "selected_route_ids": [], "artificial_tasks": []}
    route_by_id = {route["id"]: route for route in pricer.routes}
    if best_solution is not None:
        for r in data["R"]:
            solution["vehicles"][str(r)] = round_float(model.getSolVal(best_solution, data["y"][r]))
        for task_id, var in data["artificial"].items():
            if float(model.getSolVal(best_solution, var)) > 0.5:
                solution["artificial_tasks"].append(int(task_id))
        sortie_index_by_vehicle = {r: 0 for r in data["R"]}
        for column in pricer.columns:
            if model.getSolVal(best_solution, column["var"]) <= 0.5:
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
                    "work_time_lb": round_float(route_work_time_lower_bound(instance, route)),
                    "service_start": route["service_start"],
                }
            )
    solution["summary"]["uses_artificial"] = bool(solution["artificial_tasks"])
    solution["summary"]["artificial_task_count"] = len(solution["artificial_tasks"])

    report = {
        "mode": "route_vehicle_branch_price_cut_inner",
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
        "schedule_cut_count": len(schedule_cuts or []),
        "schedule_cut_constraint_count": len(data["schedule_cuts"]),
        "tree_schedule_cuts": bool(tree_schedule_cuts),
        "tree_schedule_cut_handler": data["schedule_handler"].stats() if data.get("schedule_handler") is not None else {"enabled": False},
        "raw_schedule_cut_count": len(data["raw_schedule_cuts"]),
        "pricing_time_budget": pricer.pricing_time_budget,
        "pricing_progress_interval": pricer.pricing_progress_interval,
        "pricing_budget_interrupts": pricer.pricing_budget_interrupts,
        "pricing_incomplete_due_to_budget": pricer.pricing_incomplete_due_to_budget,
        "pricing_budget_incomplete_phase": pricer.pricing_budget_incomplete_phase,
        "pricing_phase_stats": {
            phase: {key: round_float(value) if isinstance(value, float) else value for key, value in stats.items()}
            for phase, stats in sorted(pricer.pricing_phase_stats.items())
        },
        "artificial_penalty": ARTIFICIAL_TASK_PENALTY,
        "warm_start": data["warm_start"],
        "strict_pricing": not pricer.pricing_incomplete_due_to_budget,
        "eps": eps,
    }
    return pricer.routes, report, solution


def _routes_by_vehicle(solution: dict[str, Any], routes: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    route_by_id = {int(route["id"]): route for route in routes}
    grouped: dict[int, list[dict[str, Any]]] = {}
    for sortie in solution.get("sorties", []):
        grouped.setdefault(int(sortie["vehicle"]), []).append(route_by_id[int(sortie["route_id"])])
    return grouped


def _make_cut(vehicle: int, routes: list[dict[str, Any]], kind: str) -> dict[str, Any]:
    return {
        "scope": "all_vehicles",
        "source_vehicle": int(vehicle),
        "signatures": _cut_signatures([route_signature(route) for route in routes]),
        "kind": kind,
    }


def _add_cut_if_new(cuts: list[dict[str, Any]], cut_keys: set, cut: dict[str, Any]) -> bool:
    key = _cut_key(cut["signatures"])
    if key in cut_keys:
        return False
    cut_keys.add(key)
    cuts.append(cut)
    return True


def _separate_schedule_cuts(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    routes: list[dict[str, Any]],
    solution: dict[str, Any],
    cuts: list[dict[str, Any]],
    cut_keys: set,
) -> tuple[int, list[dict[str, Any]], bool, list[dict[str, Any]]]:
    added = 0
    schedules = []
    conflicts = []
    all_feasible = True
    for vehicle, selected in _routes_by_vehicle(solution, routes).items():
        check = check_route_set_schedule_feasible(instance, pairwise, selected)
        if check.feasible:
            schedules.append(
                {
                    "vehicle": int(vehicle),
                    "ready_time": check.ready_time,
                    "route_order": [int(selected[index]["id"]) for index in check.order],
                    "routes": [
                        {
                            "route_id": int(selected[index]["id"]),
                            "tasks": selected[index]["tasks"],
                            "cost": selected[index]["cost"],
                            "energy": selected[index]["energy"],
                        }
                        for index in check.order
                    ],
                }
            )
            continue

        all_feasible = False
        conflict = shrink_infeasible_route_set(instance, pairwise, selected)
        conflicts.append(
            {
                "vehicle": int(vehicle),
                "route_ids": [int(route["id"]) for route in conflict],
                "signatures": [list(route_signature(route)) for route in conflict],
            }
        )
        if _add_cut_if_new(cuts, cut_keys, _make_cut(vehicle, conflict, "infeasible_route_set")):
            added += 1
        for left_sig, right_sig in find_pairwise_incompatible_cuts(instance, pairwise, conflict):
            pair_routes = [route for route in conflict if route_signature(route) in {left_sig, right_sig}]
            if len(pair_routes) == 2 and _add_cut_if_new(cuts, cut_keys, _make_cut(vehicle, pair_routes, "pairwise_incompatible")):
                added += 1
    return added, schedules, all_feasible, conflicts


def solve_bpc_no_ml(
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
    max_cut_rounds: int = 20,
    memory_limit_mb: float | None = None,
    artificial_penalty: float = ARTIFICIAL_TASK_PENALTY,
    rmp_params: dict[str, Any] | None = None,
    seed: int | None = None,
    log_level: str = "progress",
    tree_schedule_cuts: bool = False,
    pricing_time_budget: float = 0.0,
    pricing_progress_interval: int = 0,
    schedule_start: bool = True,
) -> BPResult:
    del integer_tol, artificial_penalty
    start_time = time.perf_counter()
    cuts: list[dict[str, Any]] = []
    cut_keys = set()
    last_routes: list[dict[str, Any]] = []
    last_report: dict[str, Any] = {}
    last_solution: dict[str, Any] = {"summary": {"status": "UNKNOWN"}}
    feasible_schedules: list[dict[str, Any]] = []
    last_conflicts: list[dict[str, Any]] = []
    verified_schedule_feasible = False
    total_added_cuts = 0
    rounds_completed = 0

    for round_index in range(1, max_cut_rounds + 1):
        elapsed = time.perf_counter() - start_time
        remaining = max(0.0, float(time_limit) - elapsed)
        if remaining <= 0.0:
            break
        routes, report, solution = solve_branch_price_cut(
            instance,
            pairwise,
            schedule_cuts=cuts,
            time_limit=remaining,
            node_limit=max_nodes,
            verbose=log_level != "quiet",
            eps=pricing_eps,
            warm_start=True,
            rmp_params=rmp_params,
            memory_limit_mb=memory_limit_mb,
            tree_schedule_cuts=tree_schedule_cuts,
            pricing_time_budget=pricing_time_budget,
            pricing_progress_interval=pricing_progress_interval,
            schedule_start=schedule_start,
        )
        rounds_completed = round_index
        last_routes, last_report, last_solution = routes, report, solution
        if not solution["summary"].get("solution_count") or solution["summary"].get("uses_artificial"):
            break
        added, feasible_schedules, all_feasible, conflicts = _separate_schedule_cuts(instance, pairwise, routes, solution, cuts, cut_keys)
        last_conflicts = conflicts
        total_added_cuts += added
        if all_feasible:
            verified_schedule_feasible = True
            solution["vehicle_schedules"] = feasible_schedules
            break
        if added == 0:
            solution["summary"]["status"] = "CUT_STALLED"
            solution["summary"]["status_code"] = "cutstalled"
            solution["summary"]["mip_gap"] = None
            break

    summary = dict(last_solution.get("summary", {}))
    pricing_budget_interrupted = bool(summary.get("pricing_budget_interrupted"))
    if not pricing_budget_interrupted and not verified_schedule_feasible and summary.get("solution_count") and not summary.get("uses_artificial"):
        if summary.get("status") != "CUT_STALLED":
            summary["status"] = "CUT_ROUND_LIMIT" if rounds_completed >= max_cut_rounds else "TIME_LIMIT"
            summary["status_code"] = "cutroundlimit" if rounds_completed >= max_cut_rounds else "timelimit"
        summary["mip_gap"] = None
    last_solution["summary"] = summary
    if verified_schedule_feasible:
        last_solution["vehicle_schedules"] = feasible_schedules
    else:
        last_solution.pop("vehicle_schedules", None)

    tree_stats = dict(last_report.get("tree_schedule_cut_handler", {"enabled": False}))
    tree_cuts_added = int(tree_stats.get("cuts_added", 0) or 0)
    tree_cut_constraints_added = int(tree_stats.get("cut_constraints_added", 0) or 0)
    outer_cut_constraints = len(cuts) * int(instance["vehicles"]["R_bar"])
    report = {
        **last_report,
        "mode": "route_vehicle_branch_price_cut",
        "cut_rounds": rounds_completed,
        "schedule_cuts_added": total_added_cuts + tree_cuts_added,
        "outer_schedule_cuts_added": total_added_cuts,
        "tree_schedule_cuts_added": tree_cuts_added,
        "final_schedule_cut_count": len(cuts) + tree_cuts_added,
        "final_schedule_cut_constraint_count": outer_cut_constraints + tree_cut_constraints_added,
        "cut_kinds": {
            "infeasible_route_set": sum(1 for cut in cuts if cut.get("kind") == "infeasible_route_set")
            + int(tree_stats.get("cut_kinds", {}).get("infeasible_route_set", 0) or 0),
            "pairwise_incompatible": sum(1 for cut in cuts if cut.get("kind") == "pairwise_incompatible")
            + int(tree_stats.get("cut_kinds", {}).get("pairwise_incompatible", 0) or 0),
        },
        "schedule_feasible_solution": verified_schedule_feasible and not bool(last_solution.get("artificial_tasks")),
        "last_schedule_conflicts": last_conflicts,
        "schedule_cuts": [
            {
                "scope": cut.get("scope", "all_vehicles"),
                "source_vehicle": cut.get("source_vehicle"),
                "kind": cut.get("kind", "nogood"),
                "signatures": [list(signature) for signature in cut["signatures"]],
            }
            for cut in cuts
        ]
        + list(tree_stats.get("generated_cuts", [])),
    }

    if solution_path is not None:
        write_json(solution_path, {"routes": last_routes, "report": report, "solution": last_solution})
    if log_path is not None:
        ensure_dir(Path(log_path).parent)
        write_json(log_path, {"summary": last_solution["summary"], "report": report})

    uses_artificial = bool(last_solution["summary"].get("uses_artificial"))
    primal = None if uses_artificial or not report["schedule_feasible_solution"] else last_solution["summary"].get("objective")
    return BPResult(
        instance=str(instance.get("name", "instance")),
        task_count=len(task_ids(instance)),
        vehicle_count=int(instance["vehicles"]["R_bar"]),
        sortie_count=int(instance["vehicles"]["S_bar"]),
        status=str(last_solution["summary"].get("status", "UNKNOWN")),
        primal_bound=round_float(primal),
        dual_bound=round_float(last_solution["summary"].get("best_bound")),
        gap=round_float(last_solution["summary"].get("mip_gap")) if primal is not None else None,
        solving_time=round_float(time.perf_counter() - start_time),
        node_count=int(last_solution["summary"].get("node_count") or 0),
        rmp_solves=rounds_completed,
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
