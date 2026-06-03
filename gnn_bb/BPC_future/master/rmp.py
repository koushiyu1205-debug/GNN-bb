"""SCIP restricted master for the BPC_future trip-time model."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any

from BPC_future.core.branching import BranchConstraint, branch_coefficient, trip_allowed_by_branch
from BPC_future.core.columns import TimedTrip
from BPC_future.core.cuts import FutureCut
from BPC_future.core.data import FutureData


@dataclass(frozen=True)
class FutureDuals:
    cover: dict[int, float]
    task_vehicle: dict[tuple[int, int], float]
    sortie_count: dict[int, float]
    time_occupation: dict[tuple[int, int], float]
    ordering: dict[int, float]
    branches: dict[tuple[int, int], float]
    cuts: dict[int, float] = field(default_factory=dict)


@dataclass
class FutureRMPSolution:
    status: str
    objective: float | None
    duals: FutureDuals | None
    trip_values: list[tuple[TimedTrip, int, float]]
    y_values: dict[int, float]
    artificial_cover_values: dict[int, float]
    variable_count: int
    constraint_count: int
    theta_reduced_costs: dict[tuple[int, int], float]

    @property
    def optimal(self) -> bool:
        return self.status == "OPTIMAL"

    @property
    def artificial_mass(self) -> float:
        return sum(float(value) for value in self.artificial_cover_values.values())


@dataclass
class FuturePoolIntegerResult:
    status: str
    objective: float | None
    assignment: dict[int, list[TimedTrip]]
    variable_count: int
    constraint_count: int

    @property
    def feasible(self) -> bool:
        return self.objective is not None and bool(self.assignment)


class _DualCapturePricer:
    """Capture transformed LP duals without creating columns inside SCIP."""

    def __init__(
        self,
        cover_cons: dict[int, Any],
        task_vehicle_cons: dict[tuple[int, int], Any],
        sortie_cons: dict[int, Any],
        time_cons: dict[tuple[int, int], Any],
        ordering_cons: dict[int, Any],
        branch_cons: dict[tuple[int, int], Any],
        cut_cons: dict[int, Any],
    ) -> None:
        from pyscipopt import Pricer

        class _Pricer(Pricer):
            def __init__(self, outer: _DualCapturePricer) -> None:
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
        self.ordering_cons = dict(ordering_cons)
        self.branch_cons = dict(branch_cons)
        self.cut_cons = dict(cut_cons)
        self.duals: FutureDuals | None = None

    def on_init(self, model: Any) -> None:
        self.cover_cons = {key: model.getTransformedCons(cons) for key, cons in self.cover_cons.items()}
        self.task_vehicle_cons = {key: model.getTransformedCons(cons) for key, cons in self.task_vehicle_cons.items()}
        self.sortie_cons = {key: model.getTransformedCons(cons) for key, cons in self.sortie_cons.items()}
        self.time_cons = {key: model.getTransformedCons(cons) for key, cons in self.time_cons.items()}
        self.ordering_cons = {key: model.getTransformedCons(cons) for key, cons in self.ordering_cons.items()}
        self.branch_cons = {key: model.getTransformedCons(cons) for key, cons in self.branch_cons.items()}
        self.cut_cons = {key: model.getTransformedCons(cons) for key, cons in self.cut_cons.items()}

    def on_redcost(self, model: Any) -> dict[str, Any]:
        from pyscipopt import SCIP_RESULT

        self.duals = FutureDuals(
            cover={task: float(model.getDualsolLinear(cons)) for task, cons in self.cover_cons.items()},
            task_vehicle={key: float(model.getDualsolLinear(cons)) for key, cons in self.task_vehicle_cons.items()},
            sortie_count={vehicle: float(model.getDualsolLinear(cons)) for vehicle, cons in self.sortie_cons.items()},
            time_occupation={key: float(model.getDualsolLinear(cons)) for key, cons in self.time_cons.items()},
            ordering={key: float(model.getDualsolLinear(cons)) for key, cons in self.ordering_cons.items()},
            branches={key: float(model.getDualsolLinear(cons)) for key, cons in self.branch_cons.items()},
            cuts={key: float(model.getDualsolLinear(cons)) for key, cons in self.cut_cons.items()},
        )
        return {"result": SCIP_RESULT.SUCCESS}


def solve_trip_time_rmp(
    data: FutureData,
    trips: list[TimedTrip],
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    time_bucket_size: float,
    phase: str = "phase2",
    rmp_params: dict[str, Any] | None = None,
    cuts: tuple[FutureCut, ...] = tuple(),
    verbose: bool = False,
    capture_reduced_costs: bool = False,
    active_time_buckets: tuple[tuple[int, int], ...] | None = None,
) -> FutureRMPSolution:
    from pyscipopt import Model, quicksum

    if phase not in {"phase1", "phase2"}:
        raise ValueError(f"unsupported RMP phase {phase!r}")
    active_vehicles = _active_vehicles_from_cuts(data, cuts)
    if any(
        constraint.kind == "task_vehicle_on"
        and constraint.vehicle is not None
        and int(constraint.vehicle) not in active_vehicles
        for constraint in branch_constraints
    ):
        return FutureRMPSolution("INFEASIBLE", None, None, [], {}, {}, 0, 0, {})
    model = Model(f"bpc_future_trip_time_{phase}_{data.name}")
    _try_set_param(model, "display/verblevel", 4 if verbose else 0)
    _try_set_param(model, "presolving/maxrounds", 0)
    _try_set_param(model, "separating/maxrounds", 0)
    _try_set_param(model, "parallel/maxnthreads", 1)
    for name, value in (rmp_params or {}).items():
        _try_set_param(model, name, value)

    y = {
        vehicle: model.addVar(
            vtype="C",
            lb=0.0,
            ub=1.0,
            obj=0.0 if phase == "phase1" else data.fixed_vehicle_cost,
            name=f"y[{vehicle}]",
        )
        for vehicle in active_vehicles
    }
    artificial = {}
    if phase == "phase1":
        artificial = {
            task: model.addVar(vtype="C", lb=0.0, ub=1.0, obj=1.0, name=f"artificial_cover[{task}]")
            for task in data.tasks
        }
    theta = {}
    for index, trip in enumerate(trips):
        for vehicle in active_vehicles:
            if trip_allowed_by_branch(trip, vehicle, branch_constraints):
                theta[(index, vehicle)] = model.addVar(
                    vtype="C",
                    lb=0.0,
                    ub=1.0,
                    obj=0.0 if phase == "phase1" else float(trip.cost),
                    name=f"theta[{index},{vehicle}]",
                )

    cover_cons = {}
    for task in data.tasks:
        terms = [var for (trip_id, _vehicle), var in theta.items() if task in trips[trip_id].task_set]
        if phase == "phase1":
            cover_expr = quicksum(terms) + artificial[task]
        else:
            cover_expr = quicksum(terms)
        cover_cons[task] = model.addCons(cover_expr == 1.0, name=f"cover[{task}]", modifiable=True)

    task_vehicle_cons = {}
    for task in data.tasks:
        for vehicle in active_vehicles:
            terms = [
                var
                for (trip_id, r), var in theta.items()
                if int(r) == int(vehicle) and task in trips[trip_id].task_set
            ]
            task_vehicle_cons[(int(task), int(vehicle))] = model.addCons(
                quicksum(terms) - y[vehicle] <= 0.0,
                name=f"task_vehicle[{task},{vehicle}]",
                modifiable=True,
            )

    sortie_cons = {}
    for vehicle in active_vehicles:
        terms = [var for (trip_id, r), var in theta.items() if r == vehicle]
        sortie_cons[vehicle] = model.addCons(
            quicksum(terms) - data.sortie_limit * y[vehicle] <= 0.0,
            name=f"sorties[{vehicle}]",
            modifiable=True,
        )

    bucket_count = int(math.ceil(data.horizon / time_bucket_size))
    active_time_bucket_set = None
    if active_time_buckets is not None:
        active_time_bucket_set = {(int(vehicle), int(bucket)) for vehicle, bucket in active_time_buckets}
    time_cons = {}
    for vehicle in active_vehicles:
        for bucket in range(bucket_count):
            if active_time_bucket_set is not None and (int(vehicle), int(bucket)) not in active_time_bucket_set:
                continue
            terms = [
                float(trips[trip_id].occupancy.get(bucket, 0.0)) * var
                for (trip_id, r), var in theta.items()
                if r == vehicle and trips[trip_id].occupancy.get(bucket, 0.0) > 0.0
            ]
            time_cons[(vehicle, bucket)] = model.addCons(
                quicksum(terms) - y[vehicle] <= 0.0,
                name=f"occupation[{vehicle},{bucket}]",
                modifiable=True,
            )

    ordering_cons = {}
    vehicle_list = list(active_vehicles)
    for left, right in zip(vehicle_list[:-1], vehicle_list[1:]):
        ordering_cons[left] = model.addCons(y[right] - y[left] <= 0.0, name=f"vehicle_order[{left},{right}]", modifiable=True)

    branch_cons = {}
    for c_index, constraint in enumerate(branch_constraints):
        for vehicle in data.vehicles:
            if vehicle not in active_vehicles:
                continue
            terms = [
                branch_coefficient(trips[trip_id], vehicle, constraint) * var
                for (trip_id, r), var in theta.items()
                if r == vehicle and abs(branch_coefficient(trips[trip_id], vehicle, constraint)) > 0.0
            ]
            if constraint.kind == "same_vehicle":
                branch_cons[(c_index, vehicle)] = model.addCons(
                    quicksum(terms) == 0.0,
                    name=f"branch_same[{c_index},{vehicle}]",
                    modifiable=True,
                )
            elif constraint.kind == "separate_vehicle":
                branch_cons[(c_index, vehicle)] = model.addCons(
                    quicksum(terms) - y[vehicle] <= 0.0,
                    name=f"branch_sep[{c_index},{vehicle}]",
                    modifiable=True,
                )
            elif constraint.kind == "task_vehicle_on":
                rhs = 1.0 if int(vehicle) == int(constraint.vehicle) else 0.0
                branch_cons[(c_index, vehicle)] = model.addCons(
                    quicksum(terms) == rhs,
                    name=f"branch_tv_on[{c_index},{vehicle}]",
                    modifiable=True,
                )
            elif constraint.kind == "task_vehicle_off":
                branch_cons[(c_index, vehicle)] = model.addCons(
                    quicksum(terms) == 0.0,
                    name=f"branch_tv_off[{c_index},{vehicle}]",
                    modifiable=True,
                )

    cut_cons = {}
    for cut_index, cut in enumerate(cuts):
        theta_terms = [
            cut.coefficient(trips[trip_id], vehicle) * var
            for (trip_id, vehicle), var in theta.items()
            if abs(cut.coefficient(trips[trip_id], vehicle)) > 0.0
        ]
        y_terms = [
            cut.y_coefficient(vehicle) * var
            for vehicle, var in y.items()
            if abs(cut.y_coefficient(vehicle)) > 0.0
        ]
        expr = quicksum(theta_terms) + quicksum(y_terms)
        if cut.sense == "<=":
            cut_cons[cut_index] = model.addCons(expr <= cut.rhs, name=f"cut[{cut_index},{cut.kind}]", modifiable=True)
        elif cut.sense == ">=":
            cut_cons[cut_index] = model.addCons(expr >= cut.rhs, name=f"cut[{cut_index},{cut.kind}]", modifiable=True)
        elif cut.sense == "==":
            cut_cons[cut_index] = model.addCons(expr == cut.rhs, name=f"cut[{cut_index},{cut.kind}]", modifiable=True)
        else:
            raise ValueError(f"unsupported cut sense {cut.sense!r}")

    dual_capture = _DualCapturePricer(cover_cons, task_vehicle_cons, sortie_cons, time_cons, ordering_cons, branch_cons, cut_cons)
    model.includePricer(
        dual_capture.plugin,
        "bpc_future_dual_capture",
        "capture transformed trip-time RMP LP duals",
        priority=1,
        delay=False,
    )

    model.optimize()
    status = _status_name(model.getStatus())
    if status != "OPTIMAL":
        return FutureRMPSolution(status, None, None, [], {}, {}, len(theta) + len(y) + len(artificial), model.getNConss(), {})

    if dual_capture.duals is None:
        raise RuntimeError("SCIP did not call BPC_future dual capture pricer")
    duals = dual_capture.duals
    trip_values = [
        (trips[trip_id], vehicle, float(model.getVal(var)))
        for (trip_id, vehicle), var in theta.items()
        if model.getVal(var) > 1.0e-9
    ]
    y_values = {vehicle: 0.0 for vehicle in data.vehicles}
    y_values.update({vehicle: float(model.getVal(var)) for vehicle, var in y.items()})
    artificial_values = {task: float(model.getVal(var)) for task, var in artificial.items() if model.getVal(var) > 1.0e-9}
    rc = {}
    if capture_reduced_costs:
        rc = {(trip_id, vehicle): float(model.getVarRedcost(var)) for (trip_id, vehicle), var in theta.items()}
    return FutureRMPSolution(
        status=status,
        objective=float(model.getObjVal()),
        duals=duals,
        trip_values=trip_values,
        y_values=y_values,
        artificial_cover_values=artificial_values,
        variable_count=len(theta) + len(y) + len(artificial),
        constraint_count=model.getNConss(),
        theta_reduced_costs=rc,
    )


def solve_trip_time_pool_integer(
    data: FutureData,
    trips: list[TimedTrip],
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    time_bucket_size: float,
    time_limit: float = 10.0,
    verbose: bool = False,
    active_vehicles: tuple[int, ...] | None = None,
) -> FuturePoolIntegerResult:
    """Solve the current finite trip pool as a primal integer heuristic."""

    from pyscipopt import Model, quicksum

    vehicles = tuple(int(vehicle) for vehicle in (active_vehicles or data.vehicles))
    if any(
        constraint.kind == "task_vehicle_on"
        and constraint.vehicle is not None
        and int(constraint.vehicle) not in vehicles
        for constraint in branch_constraints
    ):
        return FuturePoolIntegerResult("INFEASIBLE", None, {}, 0, 0)
    model = Model(f"bpc_future_pool_mip_{data.name}")
    _try_set_param(model, "display/verblevel", 4 if verbose else 0)
    _try_set_param(model, "parallel/maxnthreads", 1)
    if time_limit > 0:
        _try_set_param(model, "limits/time", float(time_limit))

    y = {
        vehicle: model.addVar(vtype="B", obj=data.fixed_vehicle_cost, name=f"y[{vehicle}]")
        for vehicle in vehicles
    }
    theta = {}
    for index, trip in enumerate(trips):
        for vehicle in vehicles:
            if trip_allowed_by_branch(trip, vehicle, branch_constraints):
                theta[(index, vehicle)] = model.addVar(vtype="B", obj=float(trip.cost), name=f"theta[{index},{vehicle}]")

    for task in data.tasks:
        terms = [var for (trip_id, _vehicle), var in theta.items() if task in trips[trip_id].task_set]
        model.addCons(quicksum(terms) == 1.0, name=f"cover[{task}]")

    for task in data.tasks:
        for vehicle in vehicles:
            terms = [
                var
                for (trip_id, r), var in theta.items()
                if int(r) == int(vehicle) and task in trips[trip_id].task_set
            ]
            model.addCons(quicksum(terms) - y[vehicle] <= 0.0, name=f"task_vehicle[{task},{vehicle}]")

    for vehicle in vehicles:
        vehicle_terms = [var for (_trip_id, r), var in theta.items() if int(r) == int(vehicle)]
        model.addCons(quicksum(vehicle_terms) - data.sortie_limit * y[vehicle] <= 0.0, name=f"sorties[{vehicle}]")

    bucket_count = int(math.ceil(data.horizon / time_bucket_size))
    for vehicle in vehicles:
        for bucket in range(bucket_count):
            terms = [
                float(trips[trip_id].occupancy.get(bucket, 0.0)) * var
                for (trip_id, r), var in theta.items()
                if int(r) == int(vehicle) and trips[trip_id].occupancy.get(bucket, 0.0) > 0.0
            ]
            if terms:
                model.addCons(quicksum(terms) - y[vehicle] <= 0.0, name=f"occupation[{vehicle},{bucket}]")

    vehicle_list = list(vehicles)
    for left, right in zip(vehicle_list[:-1], vehicle_list[1:]):
        model.addCons(y[right] - y[left] <= 0.0, name=f"vehicle_order[{left},{right}]")

    for c_index, constraint in enumerate(branch_constraints):
        for vehicle in data.vehicles:
            if vehicle not in vehicles:
                continue
            terms = [
                branch_coefficient(trips[trip_id], vehicle, constraint) * var
                for (trip_id, r), var in theta.items()
                if int(r) == int(vehicle) and abs(branch_coefficient(trips[trip_id], vehicle, constraint)) > 0.0
            ]
            if constraint.kind == "same_vehicle":
                model.addCons(quicksum(terms) == 0.0, name=f"branch_same[{c_index},{vehicle}]")
            elif constraint.kind == "separate_vehicle":
                model.addCons(quicksum(terms) - y[vehicle] <= 0.0, name=f"branch_sep[{c_index},{vehicle}]")
            elif constraint.kind == "task_vehicle_on":
                rhs = 1.0 if int(vehicle) == int(constraint.vehicle) else 0.0
                model.addCons(quicksum(terms) == rhs, name=f"branch_tv_on[{c_index},{vehicle}]")
            elif constraint.kind == "task_vehicle_off":
                model.addCons(quicksum(terms) == 0.0, name=f"branch_tv_off[{c_index},{vehicle}]")

    model.optimize()
    status = _status_name(model.getStatus())
    if model.getNSols() <= 0:
        return FuturePoolIntegerResult(status, None, {}, len(theta) + len(y), model.getNConss())

    sol = model.getBestSol()
    assignment: dict[int, list[TimedTrip]] = {int(vehicle): [] for vehicle in vehicles}
    for (trip_id, vehicle), var in theta.items():
        if float(model.getSolVal(sol, var)) > 0.5:
            assignment[int(vehicle)].append(trips[trip_id])
    assignment = {vehicle: sorted(selected, key=lambda trip: (trip.start_time, trip.end_time, trip.tasks)) for vehicle, selected in assignment.items() if selected}
    return FuturePoolIntegerResult(
        status=status,
        objective=float(model.getSolObjVal(sol)),
        assignment=assignment,
        variable_count=len(theta) + len(y),
        constraint_count=model.getNConss(),
    )


def manual_reduced_cost(
    trip: TimedTrip,
    vehicle: int,
    duals: FutureDuals,
    branch_constraints: tuple[BranchConstraint, ...],
    cuts: tuple[FutureCut, ...] = tuple(),
    *,
    phase: str = "phase2",
) -> float:
    if phase not in {"phase1", "phase2"}:
        raise ValueError(f"unsupported reduced-cost phase {phase!r}")
    rc = 0.0 if phase == "phase1" else float(trip.cost)
    for task in trip.task_set:
        rc -= float(duals.cover.get(int(task), 0.0))
        rc -= float(duals.task_vehicle.get((int(task), int(vehicle)), 0.0))
    rc -= float(duals.sortie_count.get(int(vehicle), 0.0))
    for bucket, coeff in trip.occupancy.items():
        rc -= float(duals.time_occupation.get((int(vehicle), int(bucket)), 0.0)) * float(coeff)
    for c_index, constraint in enumerate(branch_constraints):
        rc -= float(duals.branches.get((int(c_index), int(vehicle)), 0.0)) * branch_coefficient(trip, int(vehicle), constraint)
    for cut_index, cut in enumerate(cuts):
        rc -= float(duals.cuts.get(int(cut_index), 0.0)) * cut.coefficient(trip, int(vehicle))
    return round(rc, 9)


def _active_vehicles_from_cuts(data: FutureData, cuts: tuple[FutureCut, ...]) -> tuple[int, ...]:
    max_vehicle = max(int(vehicle) for vehicle in data.vehicles)
    for cut in cuts:
        if getattr(cut, "kind", "") == "fleet_prefix_disable":
            max_vehicle = min(max_vehicle, int(getattr(cut, "max_vehicle")))
    return tuple(int(vehicle) for vehicle in data.vehicles if int(vehicle) <= max_vehicle)


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
