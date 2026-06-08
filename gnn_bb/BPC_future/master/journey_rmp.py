"""Journey-column restricted master problem.

One column is a feasible multi-sortie schedule for one rover.  A node lower
bound is official only after the matching journey-pricing oracle proves that no
negative reduced-cost journey remains.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any

from BPC_future.core.data import FutureData
from BPC_future.core.cuts import FutureCut
from BPC_future.core.journey import JourneyColumn


@dataclass
class JourneyPoolMasterResult:
    status: str
    lp_objective: float | None
    mip_objective: float | None
    selected_journeys: list[tuple[JourneyColumn, float]]
    journey_count: int
    variable_count: int
    constraint_count: int
    time_limit: float

    @property
    def has_lp_bound(self) -> bool:
        return self.lp_objective is not None

    @property
    def has_mip_solution(self) -> bool:
        return self.mip_objective is not None


@dataclass(frozen=True)
class JourneyDuals:
    cover: dict[int, float]
    fleet_limit: float
    cuts: dict[int, float] | None = None


@dataclass
class JourneyRMPSolution:
    status: str
    objective: float | None
    duals: JourneyDuals | None
    journey_values: list[tuple[JourneyColumn, float]]
    variable_count: int
    constraint_count: int
    reduced_costs: dict[int, float]
    variable_values: dict[int, float] = field(default_factory=dict)

    @property
    def optimal(self) -> bool:
        return self.status == "OPTIMAL"


@dataclass
class JourneyDualStabilizationResult:
    status: str
    duals: JourneyDuals | None
    objective_value: float | None
    variable_count: int
    constraint_count: int


@dataclass
class JourneyAnalyticCenterDualResult:
    status: str
    duals: JourneyDuals | None
    objective_value: float | None
    variable_count: int
    constraint_count: int
    barrier_iterations: int | None = None
    solver: str = "gurobi"


class _JourneyDualCapture:
    def __init__(self, cover_cons: dict[int, Any], fleet_cons: Any | None, cut_cons: dict[int, Any]) -> None:
        from pyscipopt import Pricer

        class _Pricer(Pricer):
            def __init__(self, outer: _JourneyDualCapture) -> None:
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
        self.fleet_cons = fleet_cons
        self.cut_cons = dict(cut_cons)
        self.duals: JourneyDuals | None = None

    def on_init(self, model: Any) -> None:
        self.cover_cons = {key: model.getTransformedCons(cons) for key, cons in self.cover_cons.items()}
        if self.fleet_cons is not None:
            self.fleet_cons = model.getTransformedCons(self.fleet_cons)
        self.cut_cons = {key: model.getTransformedCons(cons) for key, cons in self.cut_cons.items()}

    def on_redcost(self, model: Any) -> dict[str, Any]:
        from pyscipopt import SCIP_RESULT

        self.duals = JourneyDuals(
            cover={task: float(model.getDualsolLinear(cons)) for task, cons in self.cover_cons.items()},
            fleet_limit=0.0 if self.fleet_cons is None else float(model.getDualsolLinear(self.fleet_cons)),
            cuts={key: float(model.getDualsolLinear(cons)) for key, cons in self.cut_cons.items()},
        )
        return {"result": SCIP_RESULT.SUCCESS}


def solve_journey_rmp(
    data: FutureData,
    journeys: list[JourneyColumn],
    *,
    cuts: tuple[FutureCut, ...] = tuple(),
    fleet_limit: int | None = None,
    verbose: bool = False,
    capture_reduced_costs: bool = False,
) -> JourneyRMPSolution:
    """Solve the official journey RMP LP over the current journey pool."""

    from pyscipopt import Model, quicksum

    model = Model(f"bpc_future_journey_rmp_{data.name}")
    _try_set_param(model, "display/verblevel", 4 if verbose else 0)
    _try_set_param(model, "presolving/maxrounds", 0)
    _try_set_param(model, "separating/maxrounds", 0)
    _try_set_param(model, "parallel/maxnthreads", 1)

    x = {
        index: model.addVar(vtype="C", lb=0.0, ub=1.0, obj=float(journey.cost), name=f"x_journey[{index}]")
        for index, journey in enumerate(journeys)
    }
    cover_cons = {}
    for task in data.tasks:
        terms = [var for index, var in x.items() if int(task) in journeys[index].task_set]
        cover_cons[int(task)] = model.addCons(quicksum(terms) == 1.0, name=f"cover[{task}]", modifiable=True)
    active_fleet_limit = len(data.vehicles) if fleet_limit is None else max(1, min(int(fleet_limit), len(data.vehicles)))
    fleet_cons = model.addCons(quicksum(x.values()) <= float(active_fleet_limit), name="fleet_limit", modifiable=True)
    cut_cons = {}
    for cut_index, cut in enumerate(cuts):
        if not _journey_cut_supported(cut):
            raise ValueError(f"unsupported journey cut kind {getattr(cut, 'kind', '')!r}")
        terms = []
        for index, var in x.items():
            coeff = _journey_cut_coefficient(cut, journeys[index])
            if abs(coeff) > 0.0:
                terms.append(float(coeff) * var)
        expr = quicksum(terms)
        if cut.sense == "<=":
            cut_cons[cut_index] = model.addCons(expr <= cut.rhs, name=f"cut[{cut_index},{cut.kind}]", modifiable=True)
        elif cut.sense == ">=":
            cut_cons[cut_index] = model.addCons(expr >= cut.rhs, name=f"cut[{cut_index},{cut.kind}]", modifiable=True)
        elif cut.sense == "==":
            cut_cons[cut_index] = model.addCons(expr == cut.rhs, name=f"cut[{cut_index},{cut.kind}]", modifiable=True)
        else:
            raise ValueError(f"unsupported cut sense {cut.sense!r}")

    dual_capture = _JourneyDualCapture(cover_cons, fleet_cons, cut_cons)
    model.includePricer(
        dual_capture.plugin,
        "bpc_future_journey_dual_capture",
        "capture transformed journey RMP LP duals",
        priority=1,
        delay=False,
    )
    model.optimize()
    status = _status_name(model.getStatus())
    if status != "OPTIMAL":
        return JourneyRMPSolution(status, None, None, [], len(x), model.getNConss(), {})
    if dual_capture.duals is None:
        raise RuntimeError("SCIP did not call BPC_future journey dual capture pricer")
    variable_values = {index: float(model.getVal(var)) for index, var in x.items()}
    values = [
        (journeys[index], value)
        for index, value in variable_values.items()
        if value > 1.0e-9
    ]
    reduced_costs = {}
    if capture_reduced_costs:
        reduced_costs = {index: float(model.getVarRedcost(var)) for index, var in x.items()}
    return JourneyRMPSolution(
        status=status,
        objective=float(model.getObjVal()),
        duals=dual_capture.duals,
        journey_values=values,
        variable_count=len(x),
        constraint_count=model.getNConss(),
        reduced_costs=reduced_costs,
        variable_values=variable_values,
    )


def manual_journey_reduced_cost(journey: JourneyColumn, duals: JourneyDuals, cuts: tuple[FutureCut, ...] = tuple()) -> float:
    rc = float(journey.cost) - float(duals.fleet_limit)
    for task in journey.task_set:
        rc -= float(duals.cover.get(int(task), 0.0))
    for cut_index, cut in enumerate(cuts):
        rc -= float((duals.cuts or {}).get(int(cut_index), 0.0)) * _journey_cut_coefficient(cut, journey)
    return round(rc, 9)


def solve_journey_gurobi_barrier_dual(
    data: FutureData,
    journeys: list[JourneyColumn],
    *,
    cuts: tuple[FutureCut, ...] = tuple(),
    fleet_limit: int | None = None,
    time_limit: float = 1.0,
    verbose: bool = False,
) -> JourneyAnalyticCenterDualResult:
    """Solve the current journey RMP with Gurobi barrier and return row duals.

    This is a sidecar dual selector for pricing experiments.  It must not be
    used by itself as a node certificate: the official certificate remains the
    SCIP true-dual exact-pricing closure in the driver.
    """

    try:
        import gurobipy as gp
    except Exception:
        return JourneyAnalyticCenterDualResult("UNAVAILABLE", None, None, len(journeys), 0)

    model = gp.Model(f"bpc_future_journey_barrier_{data.name}")
    model.Params.OutputFlag = 1 if verbose else 0
    model.Params.Method = 2
    model.Params.Crossover = 0
    model.Params.Threads = 1
    if float(time_limit) > 0.0:
        model.Params.TimeLimit = float(time_limit)

    x = {
        index: model.addVar(lb=0.0, ub=1.0, obj=float(journey.cost), name=f"x_journey[{index}]")
        for index, journey in enumerate(journeys)
    }
    model.ModelSense = gp.GRB.MINIMIZE

    cover_cons = {}
    for task in data.tasks:
        expr = gp.quicksum(var for index, var in x.items() if int(task) in journeys[index].task_set)
        cover_cons[int(task)] = model.addConstr(expr == 1.0, name=f"cover[{task}]")

    active_fleet_limit = len(data.vehicles) if fleet_limit is None else max(1, min(int(fleet_limit), len(data.vehicles)))
    fleet_cons = model.addConstr(gp.quicksum(x.values()) <= float(active_fleet_limit), name="fleet_limit")

    cut_cons = {}
    for cut_index, cut in enumerate(cuts):
        if not _journey_cut_supported(cut):
            raise ValueError(f"unsupported journey cut kind {getattr(cut, 'kind', '')!r}")
        expr = gp.LinExpr()
        for index, var in x.items():
            coeff = _journey_cut_coefficient(cut, journeys[index])
            if abs(coeff) > 0.0:
                expr.add(var, float(coeff))
        if cut.sense == "<=":
            cut_cons[cut_index] = model.addConstr(expr <= float(cut.rhs), name=f"cut[{cut_index},{cut.kind}]")
        elif cut.sense == ">=":
            cut_cons[cut_index] = model.addConstr(expr >= float(cut.rhs), name=f"cut[{cut_index},{cut.kind}]")
        elif cut.sense == "==":
            cut_cons[cut_index] = model.addConstr(expr == float(cut.rhs), name=f"cut[{cut_index},{cut.kind}]")
        else:
            raise ValueError(f"unsupported cut sense {cut.sense!r}")

    model.optimize()
    status = _gurobi_status_name(int(model.Status), gp)
    if int(model.Status) != int(gp.GRB.OPTIMAL):
        return JourneyAnalyticCenterDualResult(status, None, None, len(x), model.NumConstrs)

    duals = JourneyDuals(
        cover={task: float(cons.Pi) for task, cons in cover_cons.items()},
        fleet_limit=float(fleet_cons.Pi),
        cuts={key: float(cons.Pi) for key, cons in cut_cons.items()},
    )
    return JourneyAnalyticCenterDualResult(
        status,
        duals,
        float(model.ObjVal),
        len(x),
        model.NumConstrs,
        barrier_iterations=int(model.BarIterCount),
    )


def solve_journey_stabilized_dual(
    data: FutureData,
    journeys: list[JourneyColumn],
    *,
    cuts: tuple[FutureCut, ...] = tuple(),
    fleet_limit: int | None = None,
    objective_value: float,
    reference: JourneyDuals | None = None,
    mode: str = "l1_reference",
    slack_cap: float = 1000.0,
    cover_upper_bounds: dict[int, float] | None = None,
    pair_upper_bounds: dict[tuple[int, int], float] | None = None,
    time_limit: float = 1.0,
    tolerance: float = 1.0e-6,
    verbose: bool = False,
) -> JourneyDualStabilizationResult:
    """Select an alternative optimal RMP dual by L1 distance to a reference.

    The returned dual is official only if its dual objective is within
    ``tolerance`` of the RMP objective and all current journey dual constraints
    are enforced by this LP.
    """

    from pyscipopt import Model, quicksum

    model = Model(f"bpc_future_journey_dual_stabilization_{data.name}")
    _try_set_param(model, "display/verblevel", 4 if verbose else 0)
    _try_set_param(model, "parallel/maxnthreads", 1)
    if time_limit > 0:
        _try_set_param(model, "limits/time", float(time_limit))
    inf = model.infinity()
    active_fleet_limit = len(data.vehicles) if fleet_limit is None else max(1, min(int(fleet_limit), len(data.vehicles)))

    pi = {int(task): model.addVar(vtype="C", lb=-inf, ub=inf, name=f"pi[{task}]") for task in data.tasks}
    mu = model.addVar(vtype="C", lb=-inf, ub=0.0, name="mu_fleet")
    gamma = {}
    for cut_index, cut in enumerate(cuts):
        if not _journey_cut_supported(cut):
            raise ValueError(f"unsupported journey cut kind {getattr(cut, 'kind', '')!r}")
        lb, ub = _journey_dual_bounds_for_sense(str(cut.sense), inf)
        gamma[cut_index] = model.addVar(vtype="C", lb=lb, ub=ub, name=f"gamma[{cut_index}]")

    dual_column_exprs: list[Any] = []
    for journey_index, journey in enumerate(journeys):
        expr = quicksum(pi[int(task)] for task in journey.task_set) + mu
        for cut_index, cut in enumerate(cuts):
            if cut_index not in gamma:
                continue
            coeff = _journey_cut_coefficient(cut, journey)
            if coeff:
                expr += float(coeff) * gamma[cut_index]
        dual_column_exprs.append(expr)
        model.addCons(expr <= float(journey.cost), name=f"dual_col[{journey_index}]")

    dual_objective = quicksum(pi[int(task)] for task in data.tasks) + float(active_fleet_limit) * mu
    for cut_index, cut in enumerate(cuts):
        if cut_index in gamma:
            dual_objective += float(cut.rhs) * gamma[cut_index]
    model.addCons(dual_objective >= float(objective_value) - float(tolerance), name="dual_obj_lb")
    model.addCons(dual_objective <= float(objective_value) + float(tolerance), name="dual_obj_ub")

    for task, upper in (cover_upper_bounds or {}).items():
        task_id = int(task)
        if task_id in pi and math.isfinite(float(upper)):
            model.addCons(pi[task_id] <= float(upper), name=f"doi_cover_ub[{task_id}]")
    for tasks, upper in (pair_upper_bounds or {}).items():
        pair = tuple(sorted(int(task) for task in tasks))
        if len(pair) != 2 or pair[0] not in pi or pair[1] not in pi or not math.isfinite(float(upper)):
            continue
        model.addCons(pi[pair[0]] + pi[pair[1]] <= float(upper), name=f"ddoi_pair_ub[{pair[0]},{pair[1]}]")

    mode = str(mode)
    if mode in {"l1", "l1_reference", "reference"}:
        abs_terms = []
        ref_cover = {} if reference is None else dict(reference.cover)
        ref_cuts = {} if reference is None else dict(reference.cuts or {})
        ref_mu = 0.0 if reference is None else float(reference.fleet_limit)
        for task, var in pi.items():
            ref = float(ref_cover.get(int(task), 0.0))
            dev = model.addVar(vtype="C", lb=0.0, name=f"abs_pi[{task}]")
            model.addCons(var - ref <= dev)
            model.addCons(ref - var <= dev)
            abs_terms.append(dev)
        dev_mu = model.addVar(vtype="C", lb=0.0, name="abs_mu")
        model.addCons(mu - ref_mu <= dev_mu)
        model.addCons(ref_mu - mu <= dev_mu)
        abs_terms.append(dev_mu)
        for cut_index, var in gamma.items():
            ref = float(ref_cuts.get(int(cut_index), 0.0))
            dev = model.addVar(vtype="C", lb=0.0, name=f"abs_gamma[{cut_index}]")
            model.addCons(var - ref <= dev)
            model.addCons(ref - var <= dev)
            abs_terms.append(dev)
        model.setObjective(quicksum(abs_terms), "minimize")
    elif mode in {"slack_center", "capped_slack_center", "interior", "interior_slack", "interior_slack_center"}:
        slack_terms = []
        cap = max(0.0, float(slack_cap))
        for journey_index, (journey, expr) in enumerate(zip(journeys, dual_column_exprs)):
            slack = model.addVar(vtype="C", lb=0.0, ub=cap, name=f"capped_slack[{journey_index}]")
            model.addCons(expr + slack <= float(journey.cost), name=f"slack_link[{journey_index}]")
            slack_terms.append(slack)
        model.setObjective(quicksum(slack_terms), "maximize")
    else:
        raise ValueError(f"unsupported journey dual stabilization mode {mode!r}")
    model.optimize()
    status = _status_name(model.getStatus())
    if status != "OPTIMAL":
        return JourneyDualStabilizationResult(status, None, None, model.getNVars(), model.getNConss())
    duals = JourneyDuals(
        cover={int(task): float(model.getVal(var)) for task, var in pi.items()},
        fleet_limit=float(model.getVal(mu)),
        cuts={int(cut_index): float(model.getVal(var)) for cut_index, var in gamma.items()},
    )
    value = sum(float(duals.cover.get(int(task), 0.0)) for task in data.tasks) + float(active_fleet_limit) * float(duals.fleet_limit)
    for cut_index, cut in enumerate(cuts):
        value += float(cut.rhs) * float((duals.cuts or {}).get(int(cut_index), 0.0))
    return JourneyDualStabilizationResult(status, duals, float(value), model.getNVars(), model.getNConss())


def _journey_cut_coefficient(cut: FutureCut, journey: JourneyColumn) -> float:
    kind = getattr(cut, "kind", "")
    if kind == "subset_row":
        tasks = set(getattr(cut, "tasks", tuple()))
        k = int(getattr(cut, "k", 2))
        return float(len(tasks.intersection(journey.task_set)) // k)
    if kind in {"fleet_lower_bound", "fleet_upper_bound"}:
        return 1.0
    return 0.0


def _journey_cut_supported(cut: FutureCut) -> bool:
    return getattr(cut, "kind", "") in {"subset_row", "fleet_lower_bound", "fleet_upper_bound"}


def _journey_dual_bounds_for_sense(sense: str, infinity: float) -> tuple[float, float]:
    if sense == "<=":
        return -float(infinity), 0.0
    if sense == ">=":
        return 0.0, float(infinity)
    if sense == "==":
        return -float(infinity), float(infinity)
    raise ValueError(f"unsupported cut sense {sense!r}")


def solve_journey_pool_master(
    data: FutureData,
    journeys: list[JourneyColumn],
    *,
    solve_integer: bool = True,
    time_limit: float = 3.0,
    fleet_limit: int | None = None,
    verbose: bool = False,
) -> JourneyPoolMasterResult:
    """Solve LP and optionally MIP over a finite journey pool."""

    lp_result = _solve(data, journeys, integral=False, time_limit=max(0.0, min(float(time_limit), 1.0)), fleet_limit=fleet_limit, verbose=verbose)
    mip_result = None
    if solve_integer:
        mip_budget = max(0.0, float(time_limit))
        mip_result = _solve(data, journeys, integral=True, time_limit=mip_budget, fleet_limit=fleet_limit, verbose=verbose)
    return JourneyPoolMasterResult(
        status=mip_result[0] if mip_result is not None else lp_result[0],
        lp_objective=lp_result[1],
        mip_objective=None if mip_result is None else mip_result[1],
        selected_journeys=mip_result[2] if mip_result is not None and mip_result[2] else lp_result[2],
        journey_count=len(journeys),
        variable_count=lp_result[3],
        constraint_count=lp_result[4],
        time_limit=float(time_limit),
    )


def _solve(
    data: FutureData,
    journeys: list[JourneyColumn],
    *,
    integral: bool,
    time_limit: float,
    fleet_limit: int | None,
    verbose: bool,
) -> tuple[str, float | None, list[tuple[JourneyColumn, float]], int, int]:
    from pyscipopt import Model, quicksum

    model = Model(f"bpc_future_journey_pool_{'mip' if integral else 'lp'}_{data.name}")
    _try_set_param(model, "display/verblevel", 4 if verbose else 0)
    _try_set_param(model, "parallel/maxnthreads", 1)
    if not integral:
        _try_set_param(model, "presolving/maxrounds", 0)
        _try_set_param(model, "separating/maxrounds", 0)
    if time_limit > 0:
        _try_set_param(model, "limits/time", float(time_limit))

    x = {
        index: model.addVar(
            vtype="B" if integral else "C",
            lb=0.0,
            ub=1.0,
            obj=float(journey.cost),
            name=f"journey[{index}]",
        )
        for index, journey in enumerate(journeys)
    }
    for task in data.tasks:
        terms = [var for index, var in x.items() if int(task) in journeys[index].task_set]
        model.addCons(quicksum(terms) == 1.0, name=f"cover[{task}]")
    active_fleet_limit = len(data.vehicles) if fleet_limit is None else max(1, min(int(fleet_limit), len(data.vehicles)))
    model.addCons(quicksum(x.values()) <= float(active_fleet_limit), name="fleet_limit")

    model.optimize()
    status = _status_name(model.getStatus())
    if model.getNSols() <= 0:
        return status, None, [], len(x), model.getNConss()
    sol = model.getBestSol()
    selected = [
        (journeys[index], float(model.getSolVal(sol, var)))
        for index, var in x.items()
        if float(model.getSolVal(sol, var)) > 1.0e-9
    ]
    selected.sort(key=lambda item: (-item[1], item[0].cost, item[0].signature))
    objective = float(model.getSolObjVal(sol))
    if not integral:
        objective = float(model.getObjVal())
        selected = [
            (journeys[index], float(model.getVal(var)))
            for index, var in x.items()
            if float(model.getVal(var)) > 1.0e-9
        ]
        selected.sort(key=lambda item: (-item[1], item[0].cost, item[0].signature))
    return status, objective, selected, len(x), model.getNConss()


def _try_set_param(model: Any, name: str, value: Any) -> None:
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
    }
    return mapping.get(text, text.upper())


def _gurobi_status_name(status: int, gp: Any) -> str:
    mapping = {
        int(gp.GRB.OPTIMAL): "OPTIMAL",
        int(gp.GRB.INFEASIBLE): "INFEASIBLE",
        int(gp.GRB.UNBOUNDED): "UNBOUNDED",
        int(gp.GRB.INF_OR_UNBD): "INF_OR_UNBD",
        int(gp.GRB.TIME_LIMIT): "TIME_LIMIT",
    }
    return mapping.get(int(status), str(status))
