"""中文摘要：节点内生命周期的 persistent RMP，用于减少主 CG loop 重建开销。"""

from __future__ import annotations

from typing import Any

from .branching import BranchConstraint, route_allowed_by_branch, route_branch_coefficient
from .columns import RouteColumn, route_work_time_lower_bound
from .cuts import Cut
from .data import BPCData
from .rmp import RMPSolution, _DualCapturePricer, _status_name, _try_set_param


class PersistentRMPRequiresRebuild(RuntimeError):
    """中文注释：当前 persistent model 不能安全增量同步，调用方应重建。"""


class PersistentRMP:
    """节点内 persistent RMP。

    中文注释：本类只复用同一节点、同一 phase、同一 branch constraints 下的 LP 模型。
    它保持与 rmp.solve_rmp_lp 完全相同的数学模型；pricing 仍在 Python 层独立执行。
    """

    def __init__(
        self,
        data: BPCData,
        routes: list[RouteColumn],
        cuts: list[Cut],
        branch_constraints: tuple[BranchConstraint, ...],
        *,
        phase: str,
        rmp_params: dict[str, Any] | None = None,
        verbose: bool = False,
        task_vehicle_linking_enabled: bool = True,
    ) -> None:
        if phase not in {"phase1", "phase2"}:
            raise ValueError(f"未知 RMP phase: {phase}")
        self.data = data
        self.phase = str(phase)
        self.branch_constraints = tuple(branch_constraints)
        self.rmp_params = dict(rmp_params or {})
        self.verbose = bool(verbose)
        self.task_vehicle_linking_enabled = bool(task_vehicle_linking_enabled)
        self.routes: list[RouteColumn] = []
        self.cuts: list[Cut] = []
        self.y: dict[int, Any] = {}
        self.route_vars: dict[tuple[int, int], Any] = {}
        self.artificial: dict[int, Any] = {}
        self.cut_artificial: dict[int, Any] = {}
        self.cover_cons: dict[int, Any] = {}
        self.task_vehicle_cons: dict[tuple[int, int], Any] = {}
        self.sortie_cons: dict[int, Any] = {}
        self.time_cons: dict[int, Any] = {}
        self.cut_cons: dict[int, Any] = {}
        self.branch_cons: dict[int, Any] = {}

        from pyscipopt import Model

        self.model = Model(f"persistent_clean_bpc_rmp_{data.name}_{phase}")
        _try_set_param(self.model, "display/verblevel", 4 if verbose else 0)
        _try_set_param(self.model, "presolving/maxrounds", 0)
        _try_set_param(self.model, "separating/maxrounds", 0)
        _try_set_param(self.model, "parallel/maxnthreads", 1)
        for name, value in self.rmp_params.items():
            _try_set_param(self.model, name, value)

        self._build_base_variables()
        self._build_base_constraints()
        for route in routes:
            self._add_route(route)
        for cut in cuts:
            self._add_cut(cut)
        self.dual_capture = _DualCapturePricer(
            self.cover_cons,
            self.task_vehicle_cons,
            self.sortie_cons,
            self.time_cons,
            self.cut_cons,
            self.branch_cons,
        )
        self.model.includePricer(
            self.dual_capture.plugin,
            "persistent_clean_bpc_dual_capture",
            "读取 persistent RMP LP dual 的空 pricer",
            priority=1,
            delay=False,
        )

    def sync(self, routes: list[RouteColumn], cuts: list[Cut]) -> None:
        """同步追加的 route/cut；删除、重排或替换要求调用方重建。"""

        if len(routes) < len(self.routes) or len(cuts) < len(self.cuts):
            raise PersistentRMPRequiresRebuild("routes/cuts were removed")
        for index, route in enumerate(self.routes):
            if routes[index] is not route:
                raise PersistentRMPRequiresRebuild("route prefix changed")
        for index, cut in enumerate(self.cuts):
            if cuts[index] is not cut:
                raise PersistentRMPRequiresRebuild("cut prefix changed")
        if len(routes) == len(self.routes) and len(cuts) == len(self.cuts):
            return
        self._free_transform()
        for route in routes[len(self.routes) :]:
            self._add_route(route)
        for cut in cuts[len(self.cuts) :]:
            self._add_cut(cut)

    def solve(self, *, capture_lambda_reduced_costs: bool = False) -> RMPSolution:
        self.dual_capture.cover_cons = dict(self.cover_cons)
        self.dual_capture.task_vehicle_cons = dict(self.task_vehicle_cons)
        self.dual_capture.sortie_cons = dict(self.sortie_cons)
        self.dual_capture.time_cons = dict(self.time_cons)
        self.dual_capture.cut_cons = dict(self.cut_cons)
        self.dual_capture.branch_cons = dict(self.branch_cons)
        self.dual_capture.duals = None

        self.model.optimize()
        status = _status_name(self.model.getStatus())
        if status != "OPTIMAL":
            return RMPSolution(
                status=status,
                objective=None,
                duals=None,
                artificial_sum=0.0,
                route_values=[],
                y_values={},
                variable_count=self.model.getNVars(),
                constraint_count=self.model.getNConss(),
                lambda_reduced_costs={} if capture_lambda_reduced_costs else None,
            )

        objective = float(self.model.getObjVal())
        artificial_sum = (
            sum(float(self.model.getVal(var)) for var in self.artificial.values())
            + sum(float(self.model.getVal(var)) for var in self.cut_artificial.values())
            if self.phase == "phase1"
            else 0.0
        )
        route_values = [
            (self.routes[route_id], vehicle, float(self.model.getVal(var)))
            for (route_id, vehicle), var in self.route_vars.items()
            if abs(float(self.model.getVal(var))) > 1.0e-9
        ]
        y_values = {vehicle: float(self.model.getVal(var)) for vehicle, var in self.y.items()}
        duals = self.dual_capture.duals
        if duals is None:
            raise RuntimeError("SCIP 未调用 persistent RMP dual capture pricer。")
        lambda_reduced_costs = None
        if capture_lambda_reduced_costs:
            lambda_reduced_costs = {
                (int(route_id), int(vehicle)): float(self.model.getVarRedcost(var))
                for (route_id, vehicle), var in self.route_vars.items()
            }
        return RMPSolution(
            status=status,
            objective=objective,
            duals=duals,
            artificial_sum=artificial_sum,
            route_values=route_values,
            y_values=y_values,
            variable_count=self.model.getNVars(),
            constraint_count=self.model.getNConss(),
            lambda_reduced_costs=lambda_reduced_costs,
        )

    def _build_base_variables(self) -> None:
        for vehicle in self.data.vehicles:
            vehicle = int(vehicle)
            lb = 0.0
            ub = 1.0
            for constraint in self.branch_constraints:
                if constraint.kind == "vehicle_use_on" and int(constraint.vehicle) == vehicle:
                    lb = 1.0
                elif constraint.kind == "vehicle_use_off" and int(constraint.vehicle) == vehicle:
                    ub = 0.0
            self.y[vehicle] = self.model.addVar(
                vtype="C",
                lb=lb,
                ub=ub,
                obj=0.0 if self.phase == "phase1" else self.data.fixed_vehicle_cost,
                name=f"y[{vehicle}]",
            )
        if self.phase == "phase1":
            for task in self.data.tasks:
                task = int(task)
                self.artificial[task] = self.model.addVar(
                    vtype="C",
                    lb=0.0,
                    ub=1.0,
                    obj=1.0,
                    name=f"artificial[{task}]",
                )

    def _build_base_constraints(self) -> None:
        from pyscipopt import quicksum

        for task in self.data.tasks:
            task = int(task)
            terms = [self.artificial[task]] if self.phase == "phase1" else []
            self.cover_cons[task] = self.model.addCons(
                quicksum(terms) == 1.0,
                name=f"cover[{task}]",
                modifiable=True,
            )
        if self.task_vehicle_linking_enabled:
            for task in self.data.tasks:
                task = int(task)
                for vehicle in self.data.vehicles:
                    vehicle = int(vehicle)
                    self.task_vehicle_cons[(task, vehicle)] = self.model.addCons(
                        -self.y[vehicle] <= 0.0,
                        name=f"task_vehicle_link[{task},{vehicle}]",
                        modifiable=True,
                    )
        for vehicle in self.data.vehicles:
            vehicle = int(vehicle)
            self.sortie_cons[vehicle] = self.model.addCons(
                -self.data.sortie_limit * self.y[vehicle] <= 0.0,
                name=f"sortie_count[{vehicle}]",
                modifiable=True,
            )
            self.time_cons[vehicle] = self.model.addCons(
                -self.data.horizon * self.y[vehicle] <= 0.0,
                name=f"vehicle_time[{vehicle}]",
                modifiable=True,
            )
        for left, right in zip(self.data.vehicles[:-1], self.data.vehicles[1:]):
            self.model.addCons(self.y[int(right)] <= self.y[int(left)], name=f"vehicle_order[{left}]")
        for index, constraint in enumerate(self.branch_constraints):
            if constraint.kind != "arc_on":
                continue
            self.branch_cons[index] = self.model.addCons(
                quicksum([]) >= 1.0,
                name=f"branch_arc_on[{index}]",
                modifiable=True,
            )

    def _add_route(self, route: RouteColumn) -> None:
        route_index = len(self.routes)
        self.routes.append(route)
        for vehicle in self.data.vehicles:
            vehicle = int(vehicle)
            if not route_allowed_by_branch(route, vehicle, self.branch_constraints):
                continue
            var = self.model.addVar(
                vtype="C",
                lb=0.0,
                ub=1.0,
                obj=0.0 if self.phase == "phase1" else float(route.cost),
                name=f"lambda[{route_index},{vehicle}]",
            )
            self.route_vars[(route_index, vehicle)] = var
            for task in route.task_set:
                task = int(task)
                self.model.addCoefLinear(self.cover_cons[task], var, 1.0)
                if self.task_vehicle_linking_enabled:
                    self.model.addCoefLinear(self.task_vehicle_cons[(task, vehicle)], var, 1.0)
            self.model.addCoefLinear(self.sortie_cons[vehicle], var, 1.0)
            self.model.addCoefLinear(self.time_cons[vehicle], var, route_work_time_lower_bound(self.data, route))
            for cut in self.cuts:
                coefficient = cut.coefficient(route, vehicle)
                if coefficient != 0.0:
                    self.model.addCoefLinear(self.cut_cons[cut.id], var, coefficient)
            for index, constraint in enumerate(self.branch_constraints):
                if constraint.kind != "arc_on":
                    continue
                coefficient = route_branch_coefficient(route, vehicle, constraint)
                if coefficient != 0.0:
                    self.model.addCoefLinear(self.branch_cons[index], var, coefficient)

    def _add_cut(self, cut: Cut) -> None:
        from pyscipopt import quicksum

        if self.phase == "phase1":
            self.cut_artificial[cut.id] = self.model.addVar(
                vtype="C",
                lb=0.0,
                obj=1.0,
                name=f"cut_artificial[{cut.id}]",
            )
        terms = [
            cut.coefficient(self.routes[route_id], vehicle) * var
            for (route_id, vehicle), var in self.route_vars.items()
            if cut.coefficient(self.routes[route_id], vehicle) != 0.0
        ]
        y_terms = [
            cut.y_coefficient(vehicle) * var
            for vehicle, var in self.y.items()
            if hasattr(cut, "y_coefficient") and cut.y_coefficient(vehicle) != 0.0
        ]
        expr = quicksum([*terms, *y_terms])
        if self.phase == "phase1":
            if cut.sense == "<=":
                expr -= self.cut_artificial[cut.id]
            elif cut.sense == ">=":
                expr += self.cut_artificial[cut.id]
            else:
                raise ValueError(f"未知 cut sense: {cut.sense}")
        if cut.sense == "<=":
            cons = self.model.addCons(expr <= cut.rhs, name=f"cut[{cut.id}]", modifiable=True)
        elif cut.sense == ">=":
            cons = self.model.addCons(expr >= cut.rhs, name=f"cut[{cut.id}]", modifiable=True)
        else:
            raise ValueError(f"未知 cut sense: {cut.sense}")
        self.cut_cons[cut.id] = cons
        self.cuts.append(cut)

    def _free_transform(self) -> None:
        try:
            self.model.freeTransform()
        except Exception:
            pass

