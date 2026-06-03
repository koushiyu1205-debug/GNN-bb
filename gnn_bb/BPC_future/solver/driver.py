"""Branch-price driver for the BPC_future trip-time master."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import heapq
import itertools
import json
import math
from pathlib import Path
import time
from typing import Any

from BPC_future.core.branching import BranchConstraint
from BPC_future.core.columns import TimedTrip, TripPool, candidate_start_times_for_trip, evaluate_timed_trip, trip_to_json
from BPC_future.core.cuts import FutureCut, FleetLowerBoundCut, FleetPrefixDisableCut, FleetUpperBoundCut, add_cut_unique, fleet_lower_bound, separate_pricing_compatible_cuts
from BPC_future.core.data import FutureData
from BPC_future.core.fleet_bound import unavoidable_nonvehicle_cost_lb
from BPC_future.core.journey import build_journey_pool
from BPC_future.master.journey_rmp import solve_journey_pool_master
from BPC_future.master.rmp import FutureDuals, FutureRMPSolution, solve_trip_time_pool_integer, solve_trip_time_rmp
from BPC_future.pricing.trip_pricing import (
    PricingConfig,
    _optimized_arc_profiles_for_sequence,
    _sequence_resource_precheck,
    price_timed_trips,
)
from BPC_future.solver.logger import FutureLogger


@dataclass(order=True)
class FutureNode:
    lower_bound: float
    id: int = field(compare=False)
    depth: int = field(compare=False)
    branch_constraints: tuple[BranchConstraint, ...] = field(compare=False, default_factory=tuple)


@dataclass
class FutureStats:
    nodes_processed: int = 0
    rmp_solves: int = 0
    pricing_calls: int = 0
    exact_pricing_calls: int = 0
    heuristic_pricing_calls: int = 0
    generated_sequences: int = 0
    evaluated_timed_trips: int = 0
    columns_added: int = 0
    branch_nodes: int = 0
    pricing_incomplete_nodes: int = 0
    pool_integer_solves: int = 0
    cuts_added: int = 0
    subset_row_cuts_added: int = 0
    sortie_lb_cut_added: int = 0
    fleet_lb_cut_added: int = 0


@dataclass
class FutureResult:
    status: str
    primal_bound: float | None
    dual_bound: float | None
    gap: float | None
    solving_time: float
    node_count: int
    rmp_solves: int
    pricing_calls: int
    exact_pricing_calls: int
    generated_sequences: int
    evaluated_timed_trips: int
    columns: int
    cuts_added: int
    subset_row_cuts_added: int
    sortie_lb_cut_added: int
    fleet_lb_cut_added: int
    solution: dict[int, list[TimedTrip]]


def solve_bpc_future(data: FutureData, config: dict[str, Any], *, logger: FutureLogger) -> FutureResult:
    started = time.perf_counter()
    time_limit = float(config.get("time_limit", 300.0))
    max_nodes = int(config.get("max_nodes", 1000))
    eps = float(config.get("pricing_eps", 1.0e-6))
    integer_tol = float(config.get("integer_tol", 1.0e-6))
    bucket = float(config.get("time_bucket_size", 1.0))
    start_step = float(config.get("pricing_start_time_step", max(5.0, bucket)))
    pool = TripPool()
    _seed_initial_trips(data, pool, bucket, start_step, int(config.get("initial_single_task_starts_per_task", 0)))
    composite_seed_added = _seed_initial_composite_trips(data, config, pool, bucket, start_step)
    stats = FutureStats()
    cuts: list[FutureCut] = []
    cut_keys: set[tuple] = set()
    _add_initial_cuts(data, config, cuts, cut_keys, stats, logger=None)
    incumbent = math.inf
    incumbent_solution: dict[int, list[TimedTrip]] = {}
    open_nodes: list[FutureNode] = [FutureNode(0.0, 0, 0, tuple())]
    next_node_id = 1
    global_dual_bound: float | None = None
    search_incomplete = False

    logger.log(
        "start",
        instance=data.name,
        tasks=len(data.tasks),
        vehicles=len(data.vehicles),
        initial_columns=len(pool.trips),
        initial_composite_seed_added=composite_seed_added,
        time_bucket_size=bucket,
        master="trip_time_grid",
        cuts_active=len(cuts),
    )
    for cut in cuts:
        logger.log("cut_added", node_id=-1, depth=-1, **cut.payload(), source="initial")
    logger.log("cuts_active", active=len(cuts))
    if bool(config.get("initial_pool_integer_heuristic_enabled", True)):
        initial_pool_result = solve_trip_time_pool_integer(
            data,
            pool.trips,
            tuple(),
            time_bucket_size=bucket,
            time_limit=float(config.get("initial_pool_integer_time_limit", config.get("pool_integer_time_limit", 3.0))),
        )
        stats.pool_integer_solves += 1
        logger.log(
            "initial_pool_integer",
            status=initial_pool_result.status,
            objective=None if initial_pool_result.objective is None else round(float(initial_pool_result.objective), 6),
            columns=len(pool.trips),
            vehicles=len(initial_pool_result.assignment),
        )
        if initial_pool_result.feasible and initial_pool_result.objective is not None:
            incumbent = float(initial_pool_result.objective)
            incumbent_solution = initial_pool_result.assignment
            logger.log("incumbent", node_id=-1, objective=round(incumbent, 6), vehicles=len(incumbent_solution), source="initial_pool_integer")
            _add_incumbent_fleet_upper_cut(
                data,
                config,
                cuts,
                cut_keys,
                stats,
                logger,
                FutureNode(0.0, -1, 0, tuple()),
                incumbent,
            )
    _run_journey_pool_diagnostics_if_enabled(
        data,
        config,
        pool,
        logger,
        node_id=-1,
        depth=0,
        cg_iter=0,
        stage="initial",
    )

    while open_nodes and stats.nodes_processed < max_nodes and time.perf_counter() - started < time_limit:
        node = heapq.heappop(open_nodes)
        if node.lower_bound >= incumbent - integer_tol:
            continue
        logger.log("node_start", node_id=node.id, depth=node.depth, lower_bound=round(node.lower_bound, 6), open_nodes=len(open_nodes))
        node_result = _process_node(data, config, pool, cuts, cut_keys, node, incumbent, logger, stats, deadline=started + time_limit)
        stats.nodes_processed += 1
        if (
            node_result.get("incumbent_objective") is not None
            and float(node_result["incumbent_objective"]) < incumbent - integer_tol
        ):
            incumbent = float(node_result["incumbent_objective"])
            incumbent_solution = node_result.get("incumbent_assignment", {}) or {}
        if node_result["status"] == "INFEASIBLE":
            logger.log("fathom", node_id=node.id, reason="rmp_infeasible")
            continue
        if node_result["status"] == "PRICING_INCOMPLETE":
            stats.pricing_incomplete_nodes += 1
            search_incomplete = True
            logger.log("node_incomplete", node_id=node.id, reason="pricing_incomplete")
            continue
        solution: FutureRMPSolution = node_result["solution"]
        assert solution.objective is not None
        global_dual_bound = solution.objective if global_dual_bound is None else min(global_dual_bound, solution.objective)
        if solution.objective >= incumbent - integer_tol:
            logger.log("fathom", node_id=node.id, reason="bound", bound=round(solution.objective, 6))
            continue
        if _is_integral(solution, integer_tol):
            assignment = _integral_assignment(solution, integer_tol)
            incumbent = float(solution.objective)
            incumbent_solution = assignment
            logger.log("incumbent", node_id=node.id, objective=round(incumbent, 6), vehicles=sum(1 for trips in assignment.values() if trips))
            continue
        branch = _choose_branch(data, solution, node.branch_constraints, integer_tol)
        if branch is None:
            pool_result = solve_trip_time_pool_integer(
                data,
                pool.trips,
                node.branch_constraints,
                time_bucket_size=bucket,
                time_limit=float(config.get("pool_integer_time_limit", 10.0)),
                active_vehicles=_pricing_vehicle_order(data, cuts),
            )
            stats.pool_integer_solves += 1
            logger.log(
                "pool_integer",
                node_id=node.id,
                status=pool_result.status,
                objective=None if pool_result.objective is None else round(pool_result.objective, 6),
                lp_bound=round(solution.objective, 6),
            )
            if pool_result.feasible and pool_result.objective is not None and pool_result.objective < incumbent - integer_tol:
                incumbent = float(pool_result.objective)
                incumbent_solution = pool_result.assignment
                logger.log("incumbent", node_id=node.id, objective=round(incumbent, 6), vehicles=len(incumbent_solution), source="pool_integer")
            if pool_result.feasible and pool_result.objective is not None and pool_result.objective <= solution.objective + integer_tol:
                logger.log("fathom", node_id=node.id, reason="pool_integer_matches_lp_bound", bound=round(solution.objective, 6))
                continue
            search_incomplete = True
            logger.log("node_incomplete", node_id=node.id, reason="fractional_no_branch", bound=round(solution.objective, 6))
            continue
        left, right = branch
        stats.branch_nodes += 1
        logger.log("branch", node_id=node.id, left=left.name(), right=right.name())
        for constraint in (left, right):
            child = FutureNode(
                float(solution.objective),
                next_node_id,
                node.depth + 1,
                (*node.branch_constraints, constraint),
            )
            next_node_id += 1
            heapq.heappush(open_nodes, child)

    status = "OPTIMAL" if not open_nodes and not search_incomplete and incumbent < math.inf else "TIME_LIMIT"
    dual_bound = incumbent if status == "OPTIMAL" and incumbent < math.inf else global_dual_bound
    gap = None
    if incumbent < math.inf and dual_bound is not None:
        gap = max(0.0, (incumbent - dual_bound) / max(1.0, abs(incumbent)))
    elapsed = time.perf_counter() - started
    result = FutureResult(
        status=status,
        primal_bound=None if incumbent == math.inf else round(incumbent, 6),
        dual_bound=None if dual_bound is None else round(float(dual_bound), 6),
        gap=None if gap is None else round(gap, 6),
        solving_time=round(elapsed, 6),
        node_count=stats.nodes_processed,
        rmp_solves=stats.rmp_solves,
        pricing_calls=stats.pricing_calls,
        exact_pricing_calls=stats.exact_pricing_calls,
        generated_sequences=stats.generated_sequences,
        evaluated_timed_trips=stats.evaluated_timed_trips,
        columns=len(pool.trips),
        cuts_added=stats.cuts_added,
        subset_row_cuts_added=stats.subset_row_cuts_added,
        sortie_lb_cut_added=stats.sortie_lb_cut_added,
        fleet_lb_cut_added=stats.fleet_lb_cut_added,
        solution=incumbent_solution,
    )
    logger.log(
        "finish",
        status=result.status,
        primal_bound=result.primal_bound,
        dual_bound=result.dual_bound,
        gap=result.gap,
        nodes=result.node_count,
        columns=result.columns,
        pricing_calls=result.pricing_calls,
        cuts_added=result.cuts_added,
        subset_row_cuts_added=result.subset_row_cuts_added,
        sortie_lb_cut_added=result.sortie_lb_cut_added,
        fleet_lb_cut_added=result.fleet_lb_cut_added,
    )
    return result


def _process_node(
    data: FutureData,
    config: dict[str, Any],
    pool: TripPool,
    cuts: list[FutureCut],
    cut_keys: set[tuple],
    node: FutureNode,
    incumbent: float,
    logger: FutureLogger,
    stats: FutureStats,
    *,
    deadline: float,
) -> dict[str, Any]:
    max_cg = int(config.get("max_cg_iterations", 100))
    bucket = float(config.get("time_bucket_size", 1.0))
    integer_tol = float(config.get("integer_tol", 1.0e-6))
    phase = "phase1" if bool(config.get("phase1_enabled", True)) else "phase2"
    best_incumbent_objective: float | None = None
    best_incumbent_assignment: dict[int, list[TimedTrip]] | None = None
    pricing_trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] = {}
    time_row_mode = str(
        config.get(
            "time_occupation_row_mode",
            "bucket_lazy" if bool(config.get("time_occupation_row_generation_enabled", False)) else "full",
        )
    )
    if time_row_mode not in {"full", "bucket_lazy", "point_cuts"}:
        raise ValueError(f"unsupported time_occupation_row_mode {time_row_mode!r}")
    active_time_buckets: set[tuple[int, int]] | None = None if time_row_mode == "full" else set()
    separate_bucket_time_rows = time_row_mode == "bucket_lazy"
    previous_dual_vector: tuple[float, ...] | None = None

    def finish(payload: dict[str, Any]) -> dict[str, Any]:
        if best_incumbent_objective is not None:
            payload["incumbent_objective"] = best_incumbent_objective
            payload["incumbent_assignment"] = best_incumbent_assignment or {}
        return payload

    def current_incumbent() -> float:
        if best_incumbent_objective is None:
            return incumbent
        return min(incumbent, best_incumbent_objective)

    for cg_iter in range(1, max_cg + 1):
        if time.perf_counter() >= deadline:
            return finish({"status": "PRICING_INCOMPLETE"})
        solution = solve_trip_time_rmp(
            data,
            pool.trips,
            node.branch_constraints,
            time_bucket_size=bucket,
            phase=phase,
            rmp_params=config.get("rmp_params", {}),
            cuts=tuple(cuts),
            capture_reduced_costs=False,
            active_time_buckets=None if active_time_buckets is None else tuple(sorted(active_time_buckets)),
        )
        stats.rmp_solves += 1
        logger.log(
            "rmp",
            node_id=node.id,
            cg_iter=cg_iter,
            objective=None if solution.objective is None else round(solution.objective, 6),
            status=solution.status,
            phase=phase,
            columns=len(pool.trips),
            variables=solution.variable_count,
            artificial_mass=round(solution.artificial_mass, 6),
            cuts_active=len(cuts),
        )
        if not solution.optimal or solution.duals is None:
            return finish({"status": "INFEASIBLE"})
        dual_vector = _dual_vector(solution.duals)
        dual_delta = _dual_delta(previous_dual_vector, dual_vector)
        logger.log(
            "rmp_dual_diagnostics",
            node_id=node.id,
            cg_iter=cg_iter,
            dual_hash=_dual_hash(dual_vector),
            dual_l1_delta=None if dual_delta is None else round(dual_delta[0], 9),
            dual_max_delta=None if dual_delta is None else round(dual_delta[1], 9),
            nonzero_duals=sum(1 for value in dual_vector if abs(value) > 1.0e-9),
        )
        previous_dual_vector = dual_vector

        if active_time_buckets is not None and separate_bucket_time_rows:
            added_time_rows = _separate_time_occupation_rows(
                data,
                solution,
                active_time_buckets,
                bucket,
                float(config.get("time_occupation_row_generation_min_violation", 1.0e-7)),
                _pricing_vehicle_order(data, cuts),
            )
            if added_time_rows:
                logger.log(
                    "time_row_separation",
                    node_id=node.id,
                    depth=node.depth,
                    cg_iter=cg_iter,
                    added=len(added_time_rows),
                    active=len(active_time_buckets),
                    max_violation=round(max(violation for _vehicle, _bucket, violation in added_time_rows), 9),
                    rows=[
                        {"vehicle": int(vehicle), "bucket": int(bucket_index), "violation": round(float(violation), 9)}
                        for vehicle, bucket_index, violation in added_time_rows[:20]
                    ],
                )
                continue

        if phase == "phase1" and solution.artificial_mass <= integer_tol:
            logger.log(
                "phase_transition",
                node_id=node.id,
                cg_iter=cg_iter,
                from_phase="phase1",
                to_phase="phase2",
                columns=len(pool.trips),
            )
            phase = "phase2"
            continue

        if phase == "phase2":
            sep = separate_pricing_compatible_cuts(
                data,
                solution.trip_values,
                solution.y_values,
                solution.duals.cover,
                cuts,
                cut_keys,
                config=config,
                depth=node.depth,
            )
            logger.log(
                "cut_separation",
                node_id=node.id,
                depth=node.depth,
                cg_iter=cg_iter,
                generated=sep.generated,
                added=sep.added,
                duplicate=sep.duplicate,
                best_violation=round(sep.best_violation, 9),
                by_type=sep.by_type,
                artificial_mass=round(solution.artificial_mass, 6),
            )
            if sep.added > 0:
                stats.cuts_added += sep.added
                for cut in sep.added_cuts or []:
                    if cut.kind == "subset_row":
                        stats.subset_row_cuts_added += 1
                    elif cut.kind == "sortie_lower_bound":
                        stats.sortie_lb_cut_added += 1
                    elif cut.kind == "fleet_lower_bound":
                        stats.fleet_lb_cut_added += 1
                    logger.log("cut_added", node_id=node.id, depth=node.depth, **cut.payload(), source="separation")
                logger.log("cuts_active", active=len(cuts), node_id=node.id, depth=node.depth)
                continue
            _run_journey_pool_diagnostics_if_enabled(
                data,
                config,
                pool,
                logger,
                node_id=node.id,
                depth=node.depth,
                cg_iter=cg_iter,
                stage="root_cg",
            )
            pool_result = _try_pool_integer_heuristic(
                data,
                config,
                pool,
                node,
                solution,
                logger,
                stats,
                cg_iter=cg_iter,
                bucket=bucket,
                incumbent=current_incumbent(),
                cuts=cuts,
            )
            if pool_result is not None and pool_result.feasible and pool_result.objective is not None:
                if pool_result.objective < current_incumbent() - integer_tol:
                    best_incumbent_objective = float(pool_result.objective)
                    best_incumbent_assignment = pool_result.assignment
                    logger.log(
                        "incumbent",
                        node_id=node.id,
                        objective=round(best_incumbent_objective, 6),
                        vehicles=len(best_incumbent_assignment),
                        source="pool_integer_early",
                    )
                    if _add_incumbent_fleet_upper_cut(
                        data,
                        config,
                        cuts,
                        cut_keys,
                        stats,
                        logger,
                        node,
                        best_incumbent_objective,
                    ):
                        continue
            _cleanup_trip_pool_if_needed(data, config, pool, solution, best_incumbent_assignment, logger, node)

        heuristic_round_limit = int(config.get("heuristic_pricing_max_rounds", 0))
        added = 0
        if heuristic_round_limit <= 0 or cg_iter <= heuristic_round_limit:
            added = _run_pricing_round(
                data,
                config,
                pool,
                cuts,
                node,
                solution,
                logger,
                stats,
                heuristic=True,
                deadline=deadline,
                phase=phase,
                trip_cache=pricing_trip_cache,
            )
        if added > 0:
            continue
        added = _run_pricing_round(
            data,
            config,
            pool,
            cuts,
            node,
            solution,
            logger,
            stats,
            heuristic=False,
            deadline=deadline,
            phase=phase,
            trip_cache=pricing_trip_cache,
            certify=_should_use_bulk_exact_pricing(config, cg_iter, phase, solution, current_incumbent(), integer_tol),
        )
        if added > 0:
            continue
        if getattr(_run_pricing_round, "last_exact_exhausted", False):
            if phase == "phase1":
                logger.log(
                    "phase_one_infeasible",
                    node_id=node.id,
                    artificial_mass=round(solution.artificial_mass, 6),
                    artificial_tasks=sorted(int(task) for task in solution.artificial_cover_values),
                )
                return finish({"status": "INFEASIBLE"})
            return finish({"status": "COMPLETE", "solution": solution})
        return finish({"status": "PRICING_INCOMPLETE"})
    return finish({"status": "PRICING_INCOMPLETE"})


def _separate_time_occupation_rows(
    data: FutureData,
    solution: FutureRMPSolution,
    active_time_buckets: set[tuple[int, int]],
    time_bucket_size: float,
    min_violation: float,
    vehicles: tuple[int, ...],
) -> list[tuple[int, int, float]]:
    bucket_count = int(math.ceil(float(data.horizon) / float(time_bucket_size)))
    activity: dict[tuple[int, int], float] = {}
    for trip, vehicle, value in solution.trip_values:
        if int(vehicle) not in vehicles:
            continue
        if abs(float(value)) <= 1.0e-12:
            continue
        for bucket, coeff in trip.occupancy.items():
            key = (int(vehicle), int(bucket))
            if key in active_time_buckets:
                continue
            activity[key] = activity.get(key, 0.0) + float(value) * float(coeff)
    added: list[tuple[int, int, float]] = []
    threshold = max(0.0, float(min_violation))
    for vehicle in vehicles:
        y_value = float(solution.y_values.get(int(vehicle), 0.0))
        for bucket in range(bucket_count):
            key = (int(vehicle), int(bucket))
            if key in active_time_buckets:
                continue
            violation = activity.get(key, 0.0) - y_value
            if violation > threshold:
                active_time_buckets.add(key)
                added.append((int(vehicle), int(bucket), float(violation)))
    return added


def _should_use_bulk_exact_pricing(
    config: dict[str, Any],
    cg_iter: int,
    phase: str,
    solution: FutureRMPSolution,
    incumbent: float,
    integer_tol: float,
) -> bool:
    if phase != "phase2" or solution.objective is None:
        return False
    if math.isinf(float(incumbent)):
        return False
    objective = float(solution.objective)
    incumbent_value = float(incumbent)
    certificate_ready = (
        bool(config.get("exact_certificate_mode_enabled", False))
        and int(cg_iter) >= int(config.get("exact_certificate_min_cg_iter", 0))
        and objective >= incumbent_value - float(integer_tol)
    )
    if certificate_ready:
        return True
    if not bool(config.get("exact_degenerate_bulk_pricing_enabled", False)):
        return False
    if int(cg_iter) < int(config.get("exact_degenerate_bulk_min_cg_iter", 1)):
        return False
    threshold = float(config.get("exact_degenerate_bulk_gap_threshold", 1.0e-6))
    return incumbent_value - objective <= max(threshold, float(integer_tol))


def _run_pricing_round(
    data: FutureData,
    config: dict[str, Any],
    pool: TripPool,
    cuts: list[FutureCut],
    node: FutureNode,
    solution: FutureRMPSolution,
    logger: FutureLogger,
    stats: FutureStats,
    *,
    heuristic: bool,
    deadline: float,
    phase: str,
    trip_cache: dict[tuple, tuple[tuple[TimedTrip, ...], int, int]] | None,
    certify: bool = False,
) -> int:
    assert solution.duals is not None
    remaining = max(0.0, deadline - time.perf_counter())
    configured_time = float(config.get("heuristic_pricing_time_limit" if heuristic else "exact_pricing_time_limit", 0.0))
    pricing_time_limit = remaining if configured_time <= 0.0 else min(configured_time, remaining)
    if pricing_time_limit <= 0.0:
        if not heuristic:
            setattr(_run_pricing_round, "last_exact_exhausted", False)
        return 0
    base = PricingConfig(
        time_bucket_size=float(config.get("time_bucket_size", 1.0)),
        max_tasks_per_trip=int(config.get("max_tasks_per_trip", 0)),
        max_sequences=int(config.get("heuristic_max_sequences" if heuristic else "exact_max_sequences", 0)),
        max_timed_evaluations=int(config.get("heuristic_max_timed_evaluations" if heuristic else "exact_max_timed_evaluations", 0)),
        max_returned_trips=int(config.get("max_trips_per_pricing", 100)),
        eps=float(config.get("pricing_eps", 1.0e-6)),
        heuristic=heuristic,
        heuristic_top_tasks=int(config.get("heuristic_top_tasks", 8)),
        time_limit=pricing_time_limit,
        start_time_step=float(config.get("pricing_start_time_step", max(5.0, float(config.get("time_bucket_size", 1.0))))),
        selection_mode=str(
            config.get(
                "heuristic_pricing_selection_mode" if heuristic else "exact_pricing_selection_mode",
                "diverse" if heuristic else "reduced_cost",
            )
        ),
        max_path_combinations_per_sequence=int(
            config.get(
                "heuristic_max_path_combinations_per_sequence" if heuristic else "exact_max_path_combinations_per_sequence",
                0,
            )
        ),
        path_dominance_enabled=bool(
            config.get(
                "heuristic_path_dominance_enabled" if heuristic else "exact_path_dominance_enabled",
                heuristic,
            )
        ),
        start_optimization_enabled=bool(
            config.get(
                "heuristic_start_optimization_enabled" if heuristic else "exact_start_optimization_enabled",
                False,
            )
        ),
        best_start_per_path_profile_enabled=bool(
            config.get(
                "heuristic_best_start_per_path_profile_enabled" if heuristic else "exact_best_start_per_path_profile_enabled",
                False,
            )
        ),
        early_stop_negative_per_sequence_enabled=bool(
            config.get(
                "heuristic_early_stop_negative_per_sequence_enabled" if heuristic else "exact_early_stop_negative_per_sequence_enabled",
                False,
            )
        ),
        stop_after_negative_trips=int(
            config.get(
                "heuristic_stop_after_negative_trips" if heuristic else "exact_stop_after_negative_trips",
                0,
            )
        ),
        max_negative_trips_per_sequence=int(
            config.get(
                "heuristic_negative_trips_per_sequence" if heuristic else "exact_negative_trips_per_sequence",
                1,
            )
        ),
        max_negative_starts_per_profile=int(
            config.get(
                "heuristic_negative_starts_per_profile" if heuristic else "exact_negative_starts_per_profile",
                0,
            )
        ),
    )
    added = 0
    all_exhausted = True
    best_rc: float | None = None
    vehicle_limit = int(config.get("heuristic_pricing_vehicle_limit", 0)) if heuristic else 0
    stop_after_first_add = bool(config.get("heuristic_pricing_stop_after_first_add", False)) if heuristic else False
    exact_stop_after_first_add = bool(config.get("exact_pricing_stop_after_first_add", True)) if not heuristic else False
    if certify and not heuristic:
        certificate_stop_after = int(
            config.get(
                "certificate_stop_after_negative_trips",
                config.get("certificate_max_returned_trips", 5000),
            )
        )
        base = PricingConfig(
            time_bucket_size=base.time_bucket_size,
            max_tasks_per_trip=base.max_tasks_per_trip,
            max_sequences=base.max_sequences,
            max_timed_evaluations=base.max_timed_evaluations,
            max_returned_trips=int(config.get("certificate_max_returned_trips", 5000)),
            eps=base.eps,
            heuristic=base.heuristic,
            heuristic_top_tasks=base.heuristic_top_tasks,
            time_limit=base.time_limit,
            start_time_step=base.start_time_step,
            selection_mode=base.selection_mode,
            max_path_combinations_per_sequence=base.max_path_combinations_per_sequence,
            path_dominance_enabled=base.path_dominance_enabled,
            start_optimization_enabled=base.start_optimization_enabled,
            best_start_per_path_profile_enabled=base.best_start_per_path_profile_enabled,
            early_stop_negative_per_sequence_enabled=base.early_stop_negative_per_sequence_enabled,
            stop_after_negative_trips=certificate_stop_after,
            max_negative_trips_per_sequence=int(config.get("certificate_negative_trips_per_sequence", 0)),
            max_negative_starts_per_profile=int(config.get("certificate_negative_starts_per_profile", 0)),
        )
        # If any negative column is found, this dual vector is no longer a
        # certificate candidate.  Re-solving the RMP is exact-safe and avoids
        # pricing symmetric vehicles with stale duals.
        exact_stop_after_first_add = bool(config.get("certificate_stop_after_first_add", True))
    vehicles_checked = 0
    for vehicle in _pricing_vehicle_order(data, cuts):
        if vehicle_limit > 0 and vehicles_checked >= vehicle_limit:
            break
        if time.perf_counter() >= deadline:
            all_exhausted = False
            break
        before_vehicle = len(pool.trips)
        existing_signatures = set(pool.by_signature)
        result = price_timed_trips(
            data,
            solution.duals,
            node.branch_constraints,
            vehicle=vehicle,
            config=base,
            cuts=tuple(cuts),
            true_duals=solution.duals if heuristic else None,
            phase=phase,
            trip_cache=trip_cache,
        )
        stats.pricing_calls += 1
        stats.generated_sequences += result.generated_sequences
        stats.evaluated_timed_trips += result.evaluated_timed_trips
        if heuristic:
            stats.heuristic_pricing_calls += 1
        else:
            stats.exact_pricing_calls += 1
        all_exhausted = all_exhausted and result.exhausted
        if result.best_reduced_cost is not None:
            best_rc = result.best_reduced_cost if best_rc is None else min(best_rc, result.best_reduced_cost)
        duplicate_candidates = 0
        added_this_vehicle = 0
        for trip in result.trips:
            if trip.signature in existing_signatures:
                duplicate_candidates += 1
            before = len(pool.trips)
            pool.add(trip)
            if len(pool.trips) > before:
                added += 1
                added_this_vehicle += 1
                existing_signatures.add(trip.signature)
        logger.log(
            "pricing",
            node_id=node.id,
            cg_iter=stats.rmp_solves,
            pricing_kind="heuristic" if heuristic else "exact",
            vehicle=vehicle,
            best_reduced_cost=None if result.best_reduced_cost is None else round(result.best_reduced_cost, 9),
            negative_trips=result.negative_trips,
            added_trips=added,
            added_trips_this_vehicle=added_this_vehicle,
            duplicate_trips=duplicate_candidates,
            exhausted=result.exhausted,
            generated_sequences=result.generated_sequences,
            evaluated_timed_trips=result.evaluated_timed_trips,
            false_candidate_trips=result.false_candidate_trips,
            dominance_pruned=result.dominance_pruned,
            diverse_selected=result.diverse_selected,
            cache_hits=result.cache_hits,
            cuts_active=len(cuts),
            phase=phase,
            certify=bool(certify and not heuristic),
        )
        vehicles_checked += 1
        if heuristic and stop_after_first_add and len(pool.trips) > before_vehicle:
            break
        if (not heuristic) and exact_stop_after_first_add and len(pool.trips) > before_vehicle:
            break
    if not heuristic:
        setattr(_run_pricing_round, "last_exact_exhausted", all_exhausted and added == 0)
    stats.columns_added += added
    return added


def _run_journey_pool_diagnostics_if_enabled(
    data: FutureData,
    config: dict[str, Any],
    pool: TripPool,
    logger: FutureLogger,
    *,
    node_id: int,
    depth: int,
    cg_iter: int,
    stage: str,
) -> None:
    if not bool(config.get("journey_pool_diagnostics_enabled", False)):
        return
    if depth > int(config.get("journey_pool_diagnostics_max_depth", 0)):
        return
    frequency = int(config.get("journey_pool_diagnostics_frequency", 0))
    if stage != "initial" and frequency <= 0:
        return
    if stage != "initial" and cg_iter % frequency != 0:
        return
    source_trips = _journey_source_trips(pool.trips, int(config.get("journey_pool_source_trip_limit", 1200)))
    started = time.perf_counter()
    journey_pool = build_journey_pool(
        data,
        source_trips,
        max_trips_per_journey=int(config.get("journey_pool_max_trips_per_journey", data.sortie_limit)),
        max_columns=int(config.get("journey_pool_max_columns", 5000)),
        max_extensions_per_prefix=int(config.get("journey_pool_max_extensions_per_prefix", 80)),
    )
    build_time = time.perf_counter() - started
    if not journey_pool.journeys:
        logger.log(
            "journey_pool_diagnostics",
            node_id=node_id,
            depth=depth,
            cg_iter=cg_iter,
            stage=stage,
            trip_pool_columns=len(pool.trips),
            source_trips=len(source_trips),
            journey_columns=0,
            build_time=round(build_time, 6),
            official_certificate=False,
            reason="empty_journey_pool",
        )
        return
    result = solve_journey_pool_master(
        data,
        journey_pool.journeys,
        solve_integer=bool(config.get("journey_pool_solve_integer", True)),
        time_limit=float(config.get("journey_pool_time_limit", 3.0)),
    )
    logger.log(
        "journey_pool_diagnostics",
        node_id=node_id,
        depth=depth,
        cg_iter=cg_iter,
        stage=stage,
        trip_pool_columns=len(pool.trips),
        source_trips=len(source_trips),
        journey_columns=len(journey_pool.journeys),
        lp_objective=None if result.lp_objective is None else round(float(result.lp_objective), 6),
        mip_objective=None if result.mip_objective is None else round(float(result.mip_objective), 6),
        status=result.status,
        selected_journeys=len(result.selected_journeys),
        max_trips_per_journey=int(config.get("journey_pool_max_trips_per_journey", data.sortie_limit)),
        build_time=round(build_time, 6),
        official_certificate=False,
    )


def _journey_source_trips(trips: list[TimedTrip], limit: int) -> list[TimedTrip]:
    if limit <= 0 or len(trips) <= limit:
        return list(trips)
    best_by_task_set: dict[frozenset[int], TimedTrip] = {}
    for trip in trips:
        old = best_by_task_set.get(trip.task_set)
        if old is None or (trip.cost, trip.start_time, trip.end_time, trip.arc_option_ids) < (
            old.cost,
            old.start_time,
            old.end_time,
            old.arc_option_ids,
        ):
            best_by_task_set[trip.task_set] = trip
    chosen = {trip.signature for trip in best_by_task_set.values()}
    ordered = sorted(
        trips,
        key=lambda trip: (
            -len(trip.task_set),
            trip.cost,
            trip.start_time,
            trip.end_time,
            trip.tasks,
            trip.arc_option_ids,
        ),
    )
    for trip in ordered:
        if len(chosen) >= limit:
            break
        chosen.add(trip.signature)
    return [trip for trip in trips if trip.signature in chosen]


def _dual_vector(duals: FutureDuals) -> tuple[float, ...]:
    values: list[float] = []
    values.extend(float(value) for _key, value in sorted(duals.cover.items()))
    values.extend(float(value) for _key, value in sorted(duals.task_vehicle.items()))
    values.extend(float(value) for _key, value in sorted(duals.sortie_count.items()))
    values.extend(float(value) for _key, value in sorted(duals.time_occupation.items()))
    values.extend(float(value) for _key, value in sorted(duals.ordering.items()))
    values.extend(float(value) for _key, value in sorted(duals.branches.items()))
    values.extend(float(value) for _key, value in sorted(duals.cuts.items()))
    return tuple(round(value, 9) for value in values)


def _dual_hash(dual_vector: tuple[float, ...]) -> str:
    payload = json.dumps(dual_vector, separators=(",", ":"))
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def _dual_delta(previous: tuple[float, ...] | None, current: tuple[float, ...]) -> tuple[float, float] | None:
    if previous is None or len(previous) != len(current):
        return None
    diffs = [abs(float(left) - float(right)) for left, right in zip(previous, current)]
    if not diffs:
        return (0.0, 0.0)
    return (sum(diffs), max(diffs))


def _pricing_vehicle_order(data: FutureData, cuts: list[FutureCut]) -> tuple[int, ...]:
    max_vehicle = max(int(vehicle) for vehicle in data.vehicles)
    for cut in cuts:
        if getattr(cut, "kind", "") == "fleet_prefix_disable":
            max_vehicle = min(max_vehicle, int(getattr(cut, "max_vehicle")))
    return tuple(int(vehicle) for vehicle in data.vehicles if int(vehicle) <= max_vehicle)


def _cleanup_trip_pool_if_needed(
    data: FutureData,
    config: dict[str, Any],
    pool: TripPool,
    solution: FutureRMPSolution,
    incumbent_assignment: dict[int, list[TimedTrip]] | None,
    logger: FutureLogger,
    node: FutureNode,
) -> None:
    if not bool(config.get("column_cleanup_enabled", True)):
        return
    threshold = int(config.get("column_cleanup_threshold", 0))
    if threshold <= 0 or len(pool.trips) <= threshold:
        return
    keep_per_task_set = max(1, int(config.get("column_cleanup_keep_per_task_set", 8)))
    keep_signatures = {trip.signature for trip, _vehicle, value in solution.trip_values if value > 1.0e-8}
    if incumbent_assignment:
        for trips in incumbent_assignment.values():
            keep_signatures.update(trip.signature for trip in trips)
    for task in data.tasks:
        candidates = [trip for trip in pool.trips if trip.task_set == frozenset({int(task)})]
        if candidates:
            keep_signatures.add(min(candidates, key=lambda trip: (trip.cost, trip.start_time, trip.arc_option_ids)).signature)

    grouped: dict[frozenset[int], list[TimedTrip]] = {}
    for trip in pool.trips:
        grouped.setdefault(trip.task_set, []).append(trip)
    for trips in grouped.values():
        trips.sort(key=lambda trip: (trip.cost, trip.start_time, trip.arc_option_ids))
        for trip in trips[:keep_per_task_set]:
            keep_signatures.add(trip.signature)

    kept = [trip for trip in pool.trips if trip.signature in keep_signatures]
    if len(kept) >= len(pool.trips):
        return
    before = len(pool.trips)
    pool.rebuild(kept)
    logger.log(
        "column_cleanup",
        node_id=node.id,
        depth=node.depth,
        before=before,
        after=len(pool.trips),
        removed=before - len(pool.trips),
        keep_per_task_set=keep_per_task_set,
    )


def _try_pool_integer_heuristic(
    data: FutureData,
    config: dict[str, Any],
    pool: TripPool,
    node: FutureNode,
    solution: FutureRMPSolution,
    logger: FutureLogger,
    stats: FutureStats,
    *,
    cg_iter: int,
    bucket: float,
    incumbent: float,
    cuts: list[FutureCut],
) -> Any | None:
    if not bool(config.get("pool_integer_heuristic_enabled", False)):
        return None
    max_columns = int(config.get("pool_integer_max_columns", 0))
    if max_columns > 0 and len(pool.trips) > max_columns:
        logger.log(
            "pool_integer_skipped",
            node_id=node.id,
            cg_iter=cg_iter,
            columns=len(pool.trips),
            reason="column_limit",
            max_columns=max_columns,
        )
        return None
    min_columns = int(config.get("pool_integer_heuristic_min_columns", 0))
    if len(pool.trips) < min_columns:
        return None
    if (
        not math.isinf(incumbent)
        and solution.objective is not None
        and float(incumbent) - float(solution.objective) <= float(config.get("pool_integer_skip_if_lp_gap_below", 1.0e-6))
    ):
        logger.log(
            "pool_integer_skipped",
            node_id=node.id,
            cg_iter=cg_iter,
            columns=len(pool.trips),
            reason="lp_gap_below_threshold",
            incumbent=round(float(incumbent), 6),
            lp_bound=round(float(solution.objective), 6),
            threshold=float(config.get("pool_integer_skip_if_lp_gap_below", 1.0e-6)),
        )
        return None
    frequency = int(config.get("pool_integer_heuristic_frequency", 3))
    if frequency > 0 and cg_iter % frequency != 0:
        return None
    pool_result = solve_trip_time_pool_integer(
        data,
        pool.trips,
        node.branch_constraints,
        time_bucket_size=bucket,
        time_limit=float(config.get("pool_integer_time_limit", 5.0)),
        active_vehicles=_pricing_vehicle_order(data, cuts),
    )
    stats.pool_integer_solves += 1
    logger.log(
        "pool_integer",
        node_id=node.id,
        cg_iter=cg_iter,
        status=pool_result.status,
        objective=None if pool_result.objective is None else round(pool_result.objective, 6),
        incumbent=None if math.isinf(incumbent) else round(incumbent, 6),
        lp_bound=None if solution.objective is None else round(solution.objective, 6),
        source="early",
    )
    return pool_result


def _add_incumbent_fleet_upper_cut(
    data: FutureData,
    config: dict[str, Any],
    cuts: list[FutureCut],
    cut_keys: set[tuple],
    stats: FutureStats,
    logger: FutureLogger,
    node: FutureNode,
    incumbent: float,
) -> bool:
    if not bool(config.get("incumbent_fleet_upper_cut_enabled", True)):
        return False
    if data.fixed_vehicle_cost <= 1.0e-9:
        return False
    unavoidable = unavoidable_nonvehicle_cost_lb(data)
    ub = int(math.floor(max(0.0, float(incumbent) - unavoidable) / float(data.fixed_vehicle_cost) + 1.0e-9))
    ub = max(1, min(int(ub), len(data.vehicles)))
    while ub > 1:
        conditional = unavoidable_nonvehicle_cost_lb(data, min_nonempty_vehicles=ub)
        if float(ub) * float(data.fixed_vehicle_cost) + float(conditional) < float(incumbent) - 1.0e-6:
            break
        unavoidable = max(float(unavoidable), float(conditional))
        ub -= 1
    if ub >= len(data.vehicles):
        return False
    cut = FleetUpperBoundCut(ub, float(incumbent), unavoidable)
    if not add_cut_unique(cuts, cut_keys, cut):
        added_any = False
    else:
        stats.cuts_added += 1
        logger.log("cut_added", node_id=node.id, depth=node.depth, **cut.payload(), source="incumbent")
        added_any = True
    if (
        bool(config.get("incumbent_fleet_prefix_disable_enabled", True))
        and not node.branch_constraints
    ):
        prefix_cut = FleetPrefixDisableCut(ub)
        if add_cut_unique(cuts, cut_keys, prefix_cut):
            stats.cuts_added += 1
            logger.log("cut_added", node_id=node.id, depth=node.depth, **prefix_cut.payload(), source="incumbent_symmetry")
            added_any = True
    if not added_any:
        return False
    logger.log("cuts_active", active=len(cuts), node_id=node.id, depth=node.depth)
    return True


def _add_initial_cuts(
    data: FutureData,
    config: dict[str, Any],
    cuts: list[FutureCut],
    cut_keys: set[tuple],
    stats: FutureStats,
    logger: FutureLogger | None,
) -> None:
    if not bool(config.get("cuts_enabled", True)):
        return
    if not bool(config.get("fleet_lower_bound_cut_enabled", True)):
        return
    cut = FleetLowerBoundCut(fleet_lower_bound(data))
    if add_cut_unique(cuts, cut_keys, cut):
        stats.cuts_added += 1
        stats.fleet_lb_cut_added += 1
        if logger is not None:
            logger.log("cut_added", node_id=-1, depth=-1, **cut.payload(), source="initial")
    if bool(config.get("static_subset_row_cuts_enabled", False)):
        from BPC_future.core.cuts import SubsetRowCut

        budget = int(config.get("static_subset_row_cut_budget", 200))
        max_subset = int(config.get("static_subset_row_max_subset_size", 5))
        added = 0
        for k, sizes in ((2, (3, 4, 5)), (3, (4, 5, 6))):
            for size in sizes:
                if size > max_subset or size > len(data.tasks):
                    continue
                for tasks in itertools.combinations(data.tasks, size):
                    if added >= budget:
                        return
                    static_cut = SubsetRowCut(tuple(int(task) for task in tasks), k)
                    if add_cut_unique(cuts, cut_keys, static_cut):
                        stats.cuts_added += 1
                        stats.subset_row_cuts_added += 1
                        added += 1
                        if logger is not None:
                            logger.log("cut_added", node_id=-1, depth=-1, **static_cut.payload(), source="initial_static")


def _seed_initial_trips(data: FutureData, pool: TripPool, bucket: float, start_step: float, starts_per_task: int = 0) -> None:
    for task in data.tasks:
        candidates: list[TimedTrip] = []
        for outbound, inbound in itertools.product(data.options(0, task), data.options(task, 0)):
            arc_options = (outbound, inbound)
            for start in candidate_start_times_for_trip(data, (task,), arc_options, start_step=start_step):
                trip = evaluate_timed_trip(
                    data,
                    (task,),
                    start,
                    time_bucket_size=bucket,
                    arc_options=arc_options,
                    include_physical_paths=False,
                )
                if trip is not None:
                    candidates.append(trip)
        if not candidates:
            raise ValueError(f"task {task} has no feasible single-task timed trip on the configured grid")
        candidates.sort(key=lambda trip: (trip.start_time, trip.cost, trip.arc_option_ids))
        for trip in _select_initial_start_representatives(candidates, starts_per_task):
            pool.add(trip)


def _seed_initial_composite_trips(
    data: FutureData,
    config: dict[str, Any],
    pool: TripPool,
    bucket: float,
    start_step: float,
    *,
    trip_cache: dict[tuple, tuple] | None = None,
) -> int:
    if not bool(config.get("initial_composite_seed_enabled", False)):
        return 0
    if not data.vehicles:
        return 0
    cover_bonus = float(config.get("initial_composite_seed_cover_bonus", 1000.0))
    duals = FutureDuals(
        cover={int(task): cover_bonus for task in data.tasks},
        task_vehicle={},
        sortie_count={int(data.vehicles[0]): 0.0},
        time_occupation={},
        ordering={},
        branches={},
        cuts={},
    )
    result = price_timed_trips(
        data,
        duals,
        tuple(),
        vehicle=int(data.vehicles[0]),
        config=PricingConfig(
            time_bucket_size=bucket,
            max_tasks_per_trip=int(config.get("max_tasks_per_trip", 0)),
            max_sequences=int(config.get("initial_composite_seed_max_sequences", 200)),
            max_timed_evaluations=int(config.get("initial_composite_seed_max_timed_evaluations", 0)),
            max_returned_trips=int(config.get("initial_composite_seed_max_trips", 300)),
            eps=float(config.get("pricing_eps", 1.0e-6)),
            heuristic=True,
            heuristic_top_tasks=int(config.get("initial_composite_seed_top_tasks", len(data.tasks))),
            time_limit=float(config.get("initial_composite_seed_time_limit", 2.0)),
            start_time_step=start_step,
            selection_mode=str(config.get("initial_composite_seed_selection_mode", "diverse")),
            max_path_combinations_per_sequence=int(config.get("initial_composite_seed_path_combinations", 24)),
            path_dominance_enabled=bool(config.get("initial_composite_seed_path_dominance_enabled", True)),
            start_optimization_enabled=False,
            best_start_per_path_profile_enabled=False,
            early_stop_negative_per_sequence_enabled=False,
            stop_after_negative_trips=int(config.get("initial_composite_seed_stop_after_trips", 0)),
            max_negative_trips_per_sequence=int(config.get("initial_composite_seed_negative_trips_per_sequence", 2)),
        ),
        cuts=tuple(),
        phase="phase2",
        trip_cache={} if trip_cache is None else trip_cache,
    )
    added = 0
    for trip in result.trips:
        before = len(pool.trips)
        pool.add(trip)
        added += int(len(pool.trips) > before)
    return added


def _seed_initial_savings_trips(
    data: FutureData,
    config: dict[str, Any],
    pool: TripPool,
    bucket: float,
    *,
    trip_cache: dict[tuple, tuple] | None = None,
) -> int:
    """Add deterministic high-coverage constructive sortie columns.

    This is a primal-column warm start only.  Every added column is still built
    by the exact timed-trip evaluator, so it cannot affect bounds or exactness.
    """

    if not bool(config.get("initial_savings_seed_enabled", False)):
        return 0
    if not data.vehicles:
        return 0
    max_tasks = max(1, int(config.get("initial_savings_seed_max_tasks", config.get("max_tasks_per_trip", 6))))
    max_evaluations = int(config.get("initial_savings_seed_max_evaluations", 3000))
    max_trips = int(config.get("initial_savings_seed_max_trips", 200))
    if max_trips <= 0:
        return 0
    vehicle = int(data.vehicles[0])
    pricing_config = PricingConfig(
        time_bucket_size=float(bucket),
        max_tasks_per_trip=max_tasks,
        max_sequences=0,
        max_timed_evaluations=0,
        eps=float(config.get("pricing_eps", 1.0e-6)),
        heuristic=False,
        start_time_step=float(config.get("pricing_start_time_step", bucket)),
        max_path_combinations_per_sequence=int(config.get("initial_savings_seed_path_combinations", 0)),
        path_dominance_enabled=bool(config.get("initial_savings_seed_path_dominance_enabled", True)),
        start_optimization_enabled=True,
    )
    local_trip_cache: dict[tuple, tuple] = {} if trip_cache is None else trip_cache
    best_cache: dict[tuple[int, ...], TimedTrip | None] = {}
    evaluations = 0

    def best_trip(sequence: tuple[int, ...]) -> TimedTrip | None:
        nonlocal evaluations
        sequence = tuple(int(task) for task in sequence)
        cached = best_cache.get(sequence)
        if sequence in best_cache:
            return cached
        if max_evaluations > 0 and evaluations >= max_evaluations:
            best_cache[sequence] = None
            return None
        evaluations += 1
        if not sequence or len(sequence) > max_tasks:
            best_cache[sequence] = None
            return None
        if not _sequence_resource_precheck(data, sequence):
            best_cache[sequence] = None
            return None
        profiles, _pruned, _hit = _optimized_arc_profiles_for_sequence(
            data,
            sequence,
            pricing_config,
            local_trip_cache,
            True,
            tuple(),
            vehicle,
            True,
        )
        if not profiles:
            best_cache[sequence] = None
            return None
        candidates: list[TimedTrip] = []
        for profile in profiles:
            if not profile.starts:
                continue
            start = float(profile.starts[0].start)
            trip = evaluate_timed_trip(
                data,
                sequence,
                start,
                time_bucket_size=float(bucket),
                arc_options=profile.arc_options,
                include_physical_paths=False,
            )
            if trip is not None:
                candidates.append(trip)
        if not candidates:
            best_cache[sequence] = None
            return None
        best = min(candidates, key=lambda trip: (float(trip.cost), float(trip.end_time), trip.tasks, trip.arc_option_ids))
        best_cache[sequence] = best
        return best

    def roundtrip_cost(task: int) -> tuple[float, int]:
        outbound = data.options(0, int(task))
        inbound = data.options(int(task), 0)
        if not outbound or not inbound:
            return (float("inf"), int(task))
        return (min(float(option.cost) for option in outbound) + min(float(option.cost) for option in inbound), int(task))

    task_order = tuple(task for _cost, task in sorted(roundtrip_cost(int(task)) for task in data.tasks))
    candidates: dict[tuple[tuple[int, ...], tuple[str, ...], float], TimedTrip] = {}
    remembered_sequences: set[tuple[int, ...]] = set()

    def remember(trip: TimedTrip | None) -> None:
        if trip is not None:
            candidates[trip.signature] = trip
            remembered_sequences.add(tuple(int(task) for task in trip.tasks))

    def grow_sequence(seed: int, allowed_tasks: set[int]) -> tuple[int, ...]:
        sequence = (int(seed),)
        remember(best_trip(sequence))
        while len(sequence) < max_tasks:
            used = set(sequence)
            best_choice: tuple[float, float, tuple[int, ...], TimedTrip] | None = None
            for task in task_order:
                task = int(task)
                if task in used or task not in allowed_tasks:
                    continue
                for position in range(len(sequence) + 1):
                    trial = (*sequence[:position], task, *sequence[position:])
                    trip = best_trip(trial)
                    if trip is None:
                        continue
                    score = (float(trip.cost) / max(1, len(trial)), float(trip.cost), trial, trip)
                    if best_choice is None or score < best_choice:
                        best_choice = score
            if best_choice is None:
                break
            sequence = best_choice[2]
            remember(best_choice[3])
            if max_evaluations > 0 and evaluations >= max_evaluations:
                break
        return sequence

    all_tasks = {int(task) for task in data.tasks}
    for seed in task_order:
        grow_sequence(int(seed), set(all_tasks))

    partition_orders = (
        task_order,
        tuple(reversed(task_order)),
        tuple(sorted(int(task) for task in data.tasks)),
    )
    for order in partition_orders:
        remaining = {int(task) for task in order}
        while remaining:
            seed = next((int(task) for task in order if int(task) in remaining), None)
            if seed is None:
                break
            sequence = grow_sequence(seed, remaining)
            used = set(sequence)
            if not used.intersection(remaining):
                remaining.remove(seed)
            else:
                remaining.difference_update(used)
            if max_evaluations > 0 and evaluations >= max_evaluations:
                break
        if max_evaluations > 0 and evaluations >= max_evaluations:
            break

    for sequence in list(remembered_sequences):
        if len(sequence) < 2:
            continue
        complement = all_tasks.difference(int(task) for task in sequence)
        if not complement:
            continue
        for seed in task_order:
            seed = int(seed)
            if seed not in complement:
                continue
            grow_sequence(seed, set(complement))
            if max_evaluations > 0 and evaluations >= max_evaluations:
                break
        if max_evaluations > 0 and evaluations >= max_evaluations:
            break

    ordered = sorted(
        candidates.values(),
        key=lambda trip: (
            -len(trip.task_set),
            float(trip.cost) / max(1, len(trip.task_set)),
            float(trip.cost),
            float(trip.start_time),
            trip.tasks,
            trip.arc_option_ids,
        ),
    )
    added = 0
    for trip in ordered[:max_trips]:
        before = len(pool.trips)
        pool.add(trip)
        added += int(len(pool.trips) > before)
    return added


def _select_initial_start_representatives(candidates: list[TimedTrip], limit: int) -> list[TimedTrip]:
    if limit <= 0 or limit >= len(candidates):
        return candidates
    if limit == 1:
        return [candidates[0]]
    indexes = {
        int(round(index * (len(candidates) - 1) / (limit - 1)))
        for index in range(limit)
    }
    return [candidates[index] for index in sorted(indexes)]


def _is_integral(solution: FutureRMPSolution, tol: float) -> bool:
    for _trip, _vehicle, value in solution.trip_values:
        if abs(value - round(value)) > tol:
            return False
    return all(abs(value - round(value)) <= tol for value in solution.y_values.values())


def _integral_assignment(solution: FutureRMPSolution, tol: float) -> dict[int, list[TimedTrip]]:
    assignment: dict[int, list[TimedTrip]] = {}
    for trip, vehicle, value in solution.trip_values:
        if value > 1.0 - tol:
            assignment.setdefault(int(vehicle), []).append(trip)
    for vehicle in assignment:
        assignment[vehicle].sort(key=lambda trip: (trip.start_time, trip.end_time, trip.tasks))
    return assignment


def _choose_branch(
    data: FutureData,
    solution: FutureRMPSolution,
    constraints: tuple[BranchConstraint, ...],
    tol: float,
) -> tuple[BranchConstraint, BranchConstraint] | None:
    fixed_pairs = {
        tuple(sorted((constraint.task_i, int(constraint.task_j))))
        for constraint in constraints
        if constraint.kind in {"same_vehicle", "separate_vehicle"} and constraint.task_j is not None
    }
    z = {(task, vehicle): 0.0 for task in data.tasks for vehicle in data.vehicles}
    for trip, vehicle, value in solution.trip_values:
        for task in trip.task_set:
            z[(int(task), int(vehicle))] += float(value)
    best_pair: tuple[float, int, int] | None = None
    for i_index, i in enumerate(data.tasks):
        for j in data.tasks[i_index + 1 :]:
            key = tuple(sorted((int(i), int(j))))
            if key in fixed_pairs:
                continue
            same_mass = sum(min(z[(int(i), vehicle)], z[(int(j), vehicle)]) for vehicle in data.vehicles)
            frac = abs(same_mass - round(same_mass))
            if frac > tol and (best_pair is None or frac > best_pair[0]):
                best_pair = (frac, int(i), int(j))
    if best_pair is not None:
        _frac, i, j = best_pair
        return (
            BranchConstraint("same_vehicle", i, j),
            BranchConstraint("separate_vehicle", i, j),
        )

    fixed_task_vehicle = {
        (constraint.task_i, int(constraint.vehicle))
        for constraint in constraints
        if constraint.kind in {"task_vehicle_on", "task_vehicle_off"} and constraint.vehicle is not None
    }
    best_tv: tuple[float, int, int, float] | None = None
    for task in data.tasks:
        for vehicle in data.vehicles:
            if (int(task), int(vehicle)) in fixed_task_vehicle:
                continue
            value = z[(int(task), int(vehicle))]
            frac = abs(value - round(value))
            if frac > tol and (best_tv is None or frac > best_tv[0]):
                best_tv = (frac, int(task), int(vehicle), value)
    if best_tv is None:
        return None
    _frac, task, vehicle, _value = best_tv
    return (
        BranchConstraint("task_vehicle_on", task, vehicle=vehicle),
        BranchConstraint("task_vehicle_off", task, vehicle=vehicle),
    )


def write_solution(path: str | Path, result: FutureResult) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": result.status,
        "primal_bound": result.primal_bound,
        "dual_bound": result.dual_bound,
        "gap": result.gap,
        "vehicles": {
            str(vehicle): [trip_to_json(trip) for trip in trips]
            for vehicle, trips in sorted(result.solution.items())
        },
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
