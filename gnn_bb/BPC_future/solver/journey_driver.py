"""Root journey-column branch-price prototype for BPC_future."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import heapq
import hashlib
import math
import itertools
from pathlib import Path
import time
from typing import Any

from BPC_future.core.branching import BranchConstraint
from BPC_future.core.cuts import FutureCut, FleetLowerBoundCut, SubsetRowCut, fleet_lower_bound
from BPC_future.core.data import FutureData
from BPC_future.core.fleet_bound import unavoidable_nonvehicle_cost_lb
from BPC_future.core.journey import JourneyPool, build_journey_pool, make_journey
from BPC_future.master.journey_rmp import (
    JourneyDuals,
    manual_journey_reduced_cost,
    solve_journey_pool_master,
    solve_journey_rmp,
    solve_journey_stabilized_dual,
)
from BPC_future.pricing.journey_pricing import JourneyPricingConfig, price_journeys
from BPC_future.solver.driver import (
    FutureResult,
    _journey_source_trips,
    _seed_initial_composite_trips,
    _seed_initial_savings_trips,
    _seed_initial_trips,
)
from BPC_future.solver.logger import FutureLogger


@dataclass(order=True)
class JourneyNode:
    queue_key: tuple[float, int, int] = field(init=False, repr=False)
    lower_bound: float = field(compare=False)
    id: int = field(compare=False)
    depth: int = field(compare=False)
    branch_constraints: tuple[BranchConstraint, ...] = field(compare=False, default_factory=tuple)
    lower_bound_exact: bool = field(compare=False, default=False)
    priority_width: int = field(compare=False, default=0)

    def __post_init__(self) -> None:
        self.queue_key = (round(float(self.lower_bound), 9), int(self.priority_width), int(self.id))


@dataclass
class JourneyBranchStats:
    nodes_processed: int = 0
    rmp_solves: int = 0
    pricing_calls: int = 0
    exact_pricing_calls: int = 0
    generated_sequences: int = 0
    evaluated_timed_trips: int = 0
    dynamic_cuts_total: int = 0
    dynamic_subset_row_cuts_total: int = 0
    branch_nodes: int = 0
    pricing_incomplete_nodes: int = 0
    pool_integer_solves: int = 0
    restarts: int = 0


@dataclass
class _JourneyLearningRuntime:
    stabilizer: Any
    anchor: dict[int, float]
    objective_history: list[float]
    filter_true_rc: bool
    true_rc_tol: float
    true_rc_keep_threshold: float
    true_rc_fallback_keep_threshold: float
    true_rc_fallback_max_kept_per_round: int
    true_rc_max_kept_per_round: int
    stop_after_no_strong_round: bool
    min_kept_to_continue: int
    pricing_rounds_used: int = 0
    suppress_after_no_strong_round: bool = False


_JOURNEY_LEARNING_STABILIZER_CACHE: dict[tuple[Any, ...], Any] = {}
_JOURNEY_LEARNING_DEFAULT_PRICING_MAX_ROUNDS = 1
_JOURNEY_LEARNING_DEFAULT_TRUE_RC_MAX_KEPT_PER_ROUND = 4


def solve_bpc_future_journey(data: FutureData, config: dict[str, Any], *, logger: FutureLogger) -> FutureResult:
    if bool(config.get("journey_branching_enabled", False)):
        return _solve_bpc_future_journey_branch_price(data, config, logger=logger)

    started = time.perf_counter()
    time_limit = float(config.get("time_limit", 300.0))
    bucket = float(config.get("time_bucket_size", 10.0))
    start_step = float(config.get("pricing_start_time_step", bucket))
    integer_tol = float(config.get("integer_tol", 1.0e-6))
    eps = float(config.get("pricing_eps", 1.0e-6))

    from BPC_future.core.columns import TripPool

    trip_cache: dict[tuple, tuple] = {}
    resource_cache: dict[tuple, Any] = {}
    trip_pool = TripPool()
    _seed_initial_trips(data, trip_pool, bucket, start_step, int(config.get("initial_single_task_starts_per_task", 0)))
    composite_seed_added = _seed_initial_composite_trips(data, config, trip_pool, bucket, start_step, trip_cache=trip_cache)
    savings_seed_added = _seed_initial_savings_trips(data, config, trip_pool, bucket, trip_cache=trip_cache)
    journey_pool = JourneyPool()
    initial_source = _journey_source_trips(trip_pool.trips, int(config.get("journey_initial_source_trip_limit", 1200)))
    initial_journeys = build_journey_pool(
        data,
        initial_source,
        max_trips_per_journey=int(config.get("journey_pool_max_trips_per_journey", data.sortie_limit)),
        max_columns=int(config.get("journey_initial_max_columns", config.get("journey_pool_max_columns", 5000))),
        max_extensions_per_prefix=int(config.get("journey_pool_max_extensions_per_prefix", 80)),
    )
    for journey in initial_journeys.journeys:
        journey_pool.add(journey)
    cuts = _journey_static_cuts(data, config)
    cut_keys = {cut.key for cut in cuts}
    _log_journey_static_cut_diagnostics(logger, config, cuts, node_id=0, depth=0)

    logger.log(
        "start",
        instance=data.name,
        tasks=len(data.tasks),
        vehicles=len(data.vehicles),
        initial_trip_columns=len(trip_pool.trips),
        initial_composite_seed_added=composite_seed_added,
        initial_savings_seed_added=savings_seed_added,
        initial_journey_columns=len(journey_pool.journeys),
        time_bucket_size=bucket,
        master="journey_root",
        cuts_active=len(cuts),
    )
    incumbent = math.inf
    incumbent_solution: dict[int, list[Any]] = {}
    active_fleet_limit = len(data.vehicles)
    if _journey_initial_pool_integer_enabled(config):
        initial_mip = solve_journey_pool_master(
            data,
            journey_pool.journeys,
            solve_integer=True,
            time_limit=float(config.get("journey_pool_time_limit", 3.0)),
        )
        if initial_mip.mip_objective is not None:
            incumbent = float(initial_mip.mip_objective)
            incumbent_solution = _journey_assignment(initial_mip.selected_journeys)
            logger.log("incumbent", node_id=0, objective=round(incumbent, 6), vehicles=len(incumbent_solution), source="initial_journey_pool_mip")
            active_fleet_limit = _update_journey_fleet_limit(
                data,
                logger,
                active_fleet_limit,
                incumbent,
                incumbent_solution,
                0,
                slack=_journey_fleet_limit_slack(config),
            )
    else:
        logger.log("journey_initial_pool_integer", node_id=0, status="SKIPPED", reason="disabled")

    rmp_solves = 0
    pricing_calls = 0
    exact_pricing_calls = 0
    generated_sequences = 0
    evaluated_timed_trips = 0
    status = "TIME_LIMIT"
    dual_bound: float | None = None
    final_solution: dict[int, list[Any]] = incumbent_solution
    max_cg = int(config.get("journey_max_cg_iterations", config.get("max_cg_iterations", 100)))
    min_pricing_time = float(config.get("journey_min_pricing_time", 1.0e-3))
    post_pricing_reserve = max(0.0, float(config.get("journey_post_pricing_time_reserve", 2.0)))
    pool_probe_enabled = bool(config.get("journey_pool_integer_heuristic_enabled", config.get("pool_integer_heuristic_enabled", True)))
    pool_probe_frequency = max(1, int(config.get("journey_pool_integer_frequency", config.get("pool_integer_heuristic_frequency", 2))))
    heuristic_round_limit = int(config.get("journey_heuristic_max_rounds", config.get("heuristic_pricing_max_rounds", 0)))
    previous_dual_vector: tuple[float, ...] | None = None
    previous_pricing_duals: JourneyDuals | None = None
    previous_rmp_objective: float | None = None
    previous_support_hash: str | None = None
    certificate_flat_rounds = 0
    certificate_no_column_rounds = 0
    restart_degenerate_rounds = 0
    restart_count = 0
    recent_priced_journeys: list[Any] = []
    dynamic_cuts_total = 0
    dynamic_subset_row_cuts_total = 0
    learning_runtime: _JourneyLearningRuntime | None = None
    learning_runtime_initialized = False
    learning_certificate_gate_logged = False
    for cg_iter in range(1, max_cg + 1):
        if time.perf_counter() - started >= time_limit:
            break
        active_fleet_limit = _update_journey_fleet_limit(
            data,
            logger,
            active_fleet_limit,
            incumbent,
            final_solution,
            cg_iter,
            slack=_journey_fleet_limit_slack(config),
        )
        solution = solve_journey_rmp(data, journey_pool.journeys, cuts=tuple(cuts), fleet_limit=active_fleet_limit)
        rmp_solves += 1
        logger.log(
            "journey_rmp",
            node_id=0,
            cg_iter=cg_iter,
            objective=None if solution.objective is None else round(float(solution.objective), 6),
            status=solution.status,
            journeys=len(journey_pool.journeys),
            variables=solution.variable_count,
            fleet_limit=active_fleet_limit,
        )
        if not solution.optimal or solution.duals is None or solution.objective is None:
            break
        dynamic_cuts_added = _separate_journey_subset_row_cuts(data, config, solution, cuts, cut_keys, logger, cg_iter)
        if dynamic_cuts_added > 0:
            dynamic_cuts_total += int(dynamic_cuts_added)
            dynamic_subset_row_cuts_total += int(dynamic_cuts_added)
            continue
        _log_journey_learning_dual_trace(
            data,
            config,
            logger,
            solution.duals,
            objective=float(solution.objective),
            cg_iter=cg_iter,
            node_id=0,
            depth=0,
        )
        scip_dual_vector = _journey_dual_vector(data, solution.duals, len(cuts))
        support_hash = _journey_support_hash(solution.journey_values)
        objective_delta = None if previous_rmp_objective is None else float(solution.objective) - float(previous_rmp_objective)
        scip_dual_l1_delta = None if previous_dual_vector is None else sum(abs(a - b) for a, b in zip(scip_dual_vector, previous_dual_vector))
        certificate_candidate = bool(
            math.isfinite(float(incumbent))
            and float(solution.objective) >= float(incumbent) - float(integer_tol)
        )
        if certificate_candidate and objective_delta is not None and abs(float(objective_delta)) <= max(eps, float(integer_tol)):
            certificate_flat_rounds += 1
        else:
            certificate_flat_rounds = 0
        progress_classification = _journey_progress_classification(
            objective_delta,
            scip_dual_l1_delta,
            previous_support_hash,
            support_hash,
            eps,
        )
        if progress_classification in {
            "dual_changed_degenerate",
            "support_changed_objective_flat",
            "stalled_same_dual_support",
        }:
            restart_degenerate_rounds += 1
        else:
            restart_degenerate_rounds = 0
        pricing_duals, pricing_dual_source = _select_journey_pricing_duals(
            data,
            config,
            journey_pool,
            tuple(cuts),
            active_fleet_limit,
            float(solution.objective),
            solution.duals,
            previous_pricing_duals,
            logger,
            cg_iter,
            progress_classification=progress_classification,
            incumbent=incumbent,
            integer_tol=integer_tol,
            remaining_time=max(0.0, time_limit - (time.perf_counter() - started)),
            certificate_flat_rounds=certificate_flat_rounds,
        )
        dual_vector = _journey_dual_vector(data, pricing_duals, len(cuts))
        dual_hash = _journey_dual_hash(dual_vector)
        dual_l1_delta = None if previous_dual_vector is None else sum(abs(a - b) for a, b in zip(dual_vector, previous_dual_vector))
        dual_linf_delta = None if previous_dual_vector is None else max(abs(a - b) for a, b in zip(dual_vector, previous_dual_vector))
        logger.log(
            "journey_rmp_dual_diagnostics",
            node_id=0,
            cg_iter=cg_iter,
            objective=round(float(solution.objective), 6),
            objective_delta=None if objective_delta is None else round(objective_delta, 9),
            dual_hash=dual_hash,
            dual_l1_delta=None if dual_l1_delta is None else round(dual_l1_delta, 9),
            dual_linf_delta=None if dual_linf_delta is None else round(dual_linf_delta, 9),
            active_journeys=len(solution.journey_values),
            active_support_hash=support_hash,
        )
        logger.log(
            "journey_cg_progress_diagnostics",
            node_id=0,
            cg_iter=cg_iter,
            classification=progress_classification,
            objective_delta=None if objective_delta is None else round(objective_delta, 9),
            dual_changed=None if dual_l1_delta is None else bool(dual_l1_delta > eps),
            scip_dual_l1_delta=None if scip_dual_l1_delta is None else round(scip_dual_l1_delta, 9),
            support_changed=None if previous_support_hash is None else bool(previous_support_hash != support_hash),
            dual_hash=dual_hash,
            pricing_dual_source=pricing_dual_source,
            active_support_hash=support_hash,
            certificate_candidate=certificate_candidate,
            certificate_flat_rounds=certificate_flat_rounds,
            restart_degenerate_rounds=restart_degenerate_rounds,
        )
        previous_dual_vector = dual_vector
        previous_pricing_duals = pricing_duals
        previous_rmp_objective = float(solution.objective)
        previous_support_hash = support_hash
        if _journey_lp_integral(solution.journey_values, integer_tol):
            old_incumbent = incumbent
            incumbent = min(incumbent, float(solution.objective))
            final_solution = _journey_assignment(solution.journey_values)
            updated_certificate_candidate = bool(
                math.isfinite(float(incumbent))
                and float(solution.objective) >= float(incumbent) - float(integer_tol)
            )
            if updated_certificate_candidate and not certificate_candidate:
                logger.log(
                    "journey_certificate_candidate_updated",
                    node_id=0,
                    cg_iter=cg_iter,
                    reason="integral_rmp_incumbent",
                    old_incumbent=None if old_incumbent == math.inf else round(float(old_incumbent), 6),
                    incumbent=round(float(incumbent), 6),
                    rmp_objective=round(float(solution.objective), 6),
                )
            certificate_candidate = updated_certificate_candidate
        pricing = None
        base_heuristic_allowed = (
            bool(config.get("journey_heuristic_pricing_enabled", True))
            and (heuristic_round_limit <= 0 or cg_iter <= heuristic_round_limit)
        )
        learning_certificate_disabled = _journey_learning_certificate_gate_disabled(config, certificate_candidate)
        if (
            not learning_runtime_initialized
            and learning_certificate_disabled
            and bool(config.get("journey_learning_enabled", False))
            and not learning_certificate_gate_logged
        ):
            logger.log(
                "journey_learning",
                node_id=0,
                depth=0,
                cg_iter=cg_iter,
                status="DISABLED",
                reason="certificate_candidate_gate",
                certificate_candidate=bool(certificate_candidate),
            )
            learning_certificate_gate_logged = True
        if (
            not learning_runtime_initialized
            and not learning_certificate_disabled
            and bool(config.get("journey_learning_enabled", False))
        ):
            learning_runtime = _maybe_create_journey_learning_runtime(data, config, logger, node_id=0, depth=0)
            learning_runtime_initialized = True
        active_learning_runtime = _journey_learning_runtime_for_pricing(
            learning_runtime,
            config,
            cg_iter=cg_iter,
            certificate_disabled=learning_certificate_disabled,
        )
        learning_heuristic_allowed = active_learning_runtime is not None
        heuristic_allowed = bool(base_heuristic_allowed or learning_heuristic_allowed)
        if heuristic_allowed:
            remaining = max(0.0, time_limit - (time.perf_counter() - started))
            if remaining <= min_pricing_time:
                break
            heuristic_pricing_config = _journey_pricing_config(
                data,
                config,
                bucket,
                start_step,
                eps,
                remaining,
                heuristic=True,
                cg_iter=cg_iter,
            )
            heuristic_duals, heuristic_dual_source, learning_smoothed = _journey_learning_pricing_duals(
                active_learning_runtime,
                solution.duals,
                rmp_objective=float(solution.objective),
                branch_depth=0,
                logger=logger,
                cg_iter=cg_iter,
                node_id=0,
                depth=0,
            )
            if not learning_smoothed:
                heuristic_duals, heuristic_dual_source = pricing_duals, pricing_dual_source
            if not learning_smoothed and not base_heuristic_allowed:
                logger.log(
                    "journey_learning_smoothing",
                    node_id=0,
                    depth=0,
                    cg_iter=cg_iter,
                    status="SKIPPED",
                    reason="learning_not_active_and_base_heuristic_disabled",
                )
            else:
                if learning_smoothed:
                    heuristic_pricing_config = _journey_learning_pricing_config(config, heuristic_pricing_config)
                heuristic_trip_cache, heuristic_resource_cache = _journey_pricing_caches_for_learning_pass(
                    learning_smoothed=learning_smoothed,
                    trip_cache=trip_cache,
                    resource_cache=resource_cache,
                )
                pricing = price_journeys(
                    data,
                    heuristic_duals,
                    tuple(),
                    config=heuristic_pricing_config,
                    cuts=tuple(cuts),
                    trip_cache=heuristic_trip_cache,
                    resource_cache=heuristic_resource_cache,
                    forbidden_journey_signatures=set(journey_pool.by_signature.keys()),
                    dominant_task_set_costs=_journey_pricing_dominant_task_set_costs(journey_pool, cuts, tuple()),
                )
                pricing_calls += 1
                generated_sequences += pricing.generated_sequences
                evaluated_timed_trips += pricing.evaluated_timed_trips
                _log_journey_pricing(
                    logger,
                    pricing,
                    cg_iter,
                    pricing_kind="heuristic",
                    config=heuristic_pricing_config,
                    pricing_dual_source=heuristic_dual_source,
                )
                priced_journeys = pricing.journeys
                if learning_smoothed and learning_runtime is not None and learning_runtime.filter_true_rc:
                    priced_journeys = _journey_learning_true_rc_filter(
                        logger,
                        pricing.journeys,
                        true_duals=solution.duals,
                        cuts=tuple(cuts),
                        tol=learning_runtime.true_rc_tol if learning_runtime is not None else 1.0e-5,
                        keep_threshold=learning_runtime.true_rc_keep_threshold
                        if learning_runtime is not None
                        else 0.0,
                        max_kept=learning_runtime.true_rc_max_kept_per_round
                        if learning_runtime is not None
                        else 0,
                        fallback_keep_threshold=learning_runtime.true_rc_fallback_keep_threshold
                        if learning_runtime is not None
                        else 0.0,
                        fallback_max_kept=learning_runtime.true_rc_fallback_max_kept_per_round
                        if learning_runtime is not None
                        else 0,
                        cg_iter=cg_iter,
                        node_id=0,
                        depth=0,
                        pricing_kind="heuristic",
                    )
                if priced_journeys:
                    pricing_for_add = replace(pricing, journeys=list(priced_journeys))
                    added = _add_priced_journeys(journey_pool, list(priced_journeys))
                    _log_journey_addition(logger, pricing_for_add, added, cg_iter, pricing_kind="heuristic")
                    if learning_smoothed and learning_runtime is not None:
                        _journey_learning_handle_smoothed_pricing_result(
                            logger,
                            learning_runtime,
                            found_negative_column=added > 0,
                            candidate_journeys=len(pricing.journeys),
                            kept_journeys=len(priced_journeys),
                            added_journeys=added,
                            cg_iter=cg_iter,
                            node_id=0,
                            depth=0,
                            pricing_kind="heuristic",
                        )
                    if added > 0 and _should_run_journey_pool_probe(pool_probe_enabled, cg_iter, pool_probe_frequency):
                        incumbent, final_solution = _run_journey_pool_incumbent_probe(
                            data,
                            config,
                            journey_pool,
                            logger,
                            cg_iter,
                            incumbent,
                            final_solution,
                            fleet_limit=active_fleet_limit,
                            remaining=max(0.0, time_limit - (time.perf_counter() - started)),
                        )
                    active_fleet_limit = _update_journey_fleet_limit(
                        data,
                        logger,
                        active_fleet_limit,
                        incumbent,
                        final_solution,
                        cg_iter,
                        slack=_journey_fleet_limit_slack(config),
                    )
                    if added > 0:
                        certificate_no_column_rounds = 0
                        continue
                elif learning_smoothed and learning_runtime is not None:
                    _journey_learning_handle_smoothed_pricing_result(
                        logger,
                        learning_runtime,
                        found_negative_column=False,
                        candidate_journeys=len(pricing.journeys),
                        kept_journeys=0,
                        added_journeys=0,
                        cg_iter=cg_iter,
                        node_id=0,
                        depth=0,
                        pricing_kind="heuristic",
                    )
        remaining = max(0.0, time_limit - (time.perf_counter() - started))
        if remaining <= min_pricing_time:
            break
        exact_budget, reserve_used, budget_reason = _journey_exact_pricing_budget(
            remaining=remaining,
            post_pricing_reserve=post_pricing_reserve,
            min_pricing_time=min_pricing_time,
            incumbent=incumbent,
            rmp_objective=float(solution.objective),
            integer_tol=integer_tol,
            cg_iter=cg_iter,
            certificate_no_reserve_enabled=bool(config.get("journey_certificate_no_reserve_enabled", True)),
            certificate_no_reserve_min_cg_iter=int(config.get("journey_certificate_no_reserve_min_cg_iter", 3)),
        )
        logger.log(
            "journey_exact_pricing_budget",
            node_id=0,
            cg_iter=cg_iter,
            remaining=round(float(remaining), 6),
            exact_budget=round(float(exact_budget), 6),
            post_pricing_reserve=round(float(post_pricing_reserve), 6),
            reserve_used=round(float(reserve_used), 6),
            reason=budget_reason,
            incumbent=None if incumbent == math.inf else round(float(incumbent), 6),
            rmp_objective=round(float(solution.objective), 6),
        )
        exact_pricing_config = _journey_pricing_config(
            data,
            config,
            bucket,
            start_step,
            eps,
            exact_budget,
            heuristic=False,
            cg_iter=cg_iter,
        )
        exact_pricing_config, certificate_pricing_mode = _journey_certificate_pricing_config(
            config,
            exact_pricing_config,
            certificate_candidate=certificate_candidate,
            certificate_flat_rounds=certificate_flat_rounds,
            certificate_no_column_rounds=certificate_no_column_rounds,
            depth=0,
        )
        exact_pricing_config, immediate_no_reserve = _journey_immediate_certificate_no_reserve_config(
            config,
            exact_pricing_config,
            certificate_candidate=certificate_candidate,
            budget_reason=budget_reason,
            exact_budget=exact_budget,
        )
        if immediate_no_reserve:
            logger.log(
                "journey_certificate_immediate_no_reserve",
                node_id=0,
                cg_iter=cg_iter,
                time_limit=round(float(exact_pricing_config.time_limit), 6),
                profile_generation_time_fraction=round(float(exact_pricing_config.profile_generation_time_fraction), 6),
            )
        if certificate_pricing_mode.get("fast_negative_return"):
            logger.log(
                "journey_certificate_fast_negative_return",
                node_id=0,
                cg_iter=cg_iter,
                certificate_flat_rounds=certificate_flat_rounds,
                early_return_negative=bool(exact_pricing_config.early_return_negative),
                early_return_negative_min_count=int(exact_pricing_config.early_return_negative_min_count),
                streaming_min_negative_batch=int(exact_pricing_config.streaming_min_negative_batch),
                remaining=round(float(remaining), 6),
            )
        if certificate_pricing_mode.get("full_scan"):
            logger.log(
                "journey_certificate_full_scan",
                node_id=0,
                cg_iter=cg_iter,
                certificate_flat_rounds=certificate_flat_rounds,
                full_scan_after=int(certificate_pricing_mode.get("full_scan_after", 0)),
                streaming_pricing_enabled=False,
                early_return_negative=False,
                max_sequences=int(exact_pricing_config.max_sequences),
                max_timed_evaluations=int(exact_pricing_config.max_timed_evaluations),
                remaining=round(float(remaining), 6),
            )
        exact_duals, exact_dual_source = _journey_exact_pricing_duals(
            solution.duals,
            pricing_duals,
            pricing_dual_source,
            learning_runtime=learning_runtime,
            certificate_candidate=certificate_candidate,
            completion_bound_enabled=exact_pricing_config.direct_journey_label_completion_bound_enabled,
        )
        pricing = price_journeys(
            data,
            exact_duals,
            tuple(),
            config=exact_pricing_config,
            cuts=tuple(cuts),
            trip_cache=trip_cache,
            resource_cache=resource_cache,
            forbidden_journey_signatures=set(journey_pool.by_signature.keys()),
            dominant_task_set_costs=_journey_pricing_dominant_task_set_costs(journey_pool, cuts, tuple()),
        )
        pricing_calls += 1
        exact_pricing_calls += 1
        generated_sequences += pricing.generated_sequences
        evaluated_timed_trips += pricing.evaluated_timed_trips
        _log_journey_pricing(
            logger,
            pricing,
            cg_iter,
            pricing_kind="exact",
            config=exact_pricing_config,
            pricing_dual_source=exact_dual_source,
        )
        if pricing.journeys:
            added = _add_priced_journeys(journey_pool, pricing.journeys)
            _log_journey_addition(logger, pricing, added, cg_iter, pricing_kind="exact")
            if added > 0:
                recent_priced_journeys = list(pricing.journeys)
            if added > 0 and _should_run_journey_pool_probe(pool_probe_enabled, cg_iter, pool_probe_frequency):
                incumbent, final_solution = _run_journey_pool_incumbent_probe(
                    data,
                    config,
                    journey_pool,
                    logger,
                    cg_iter,
                    incumbent,
                    final_solution,
                    fleet_limit=active_fleet_limit,
                    remaining=max(0.0, time_limit - (time.perf_counter() - started)),
                )
                active_fleet_limit = _update_journey_fleet_limit(
                    data,
                    logger,
                    active_fleet_limit,
                    incumbent,
                    final_solution,
                    cg_iter,
                    slack=_journey_fleet_limit_slack(config),
                )
            if added > 0:
                certificate_no_column_rounds = 0
                journey_pool, restarted = _maybe_restart_journey_pool(
                    data,
                    config,
                    journey_pool,
                    solution,
                    final_solution,
                    recent_priced_journeys,
                    logger,
                    cg_iter,
                    certificate_flat_rounds,
                    restart_count,
                    progress_classification=progress_classification,
                    degenerate_rounds=restart_degenerate_rounds,
                    node_id=0,
                    depth=0,
                )
                restart_count += int(restarted)
                continue
            logger.log(
                "journey_pricing_duplicate_block",
                node_id=0,
                cg_iter=cg_iter,
                pricing_kind="exact",
                exhausted=pricing.exhausted,
                reason="negative_journey_already_in_pool",
                rmp_objective=round(float(solution.objective), 9),
                dual_hash=dual_hash,
                pricing_status=pricing.status,
                pricing_reason=pricing.reason,
                existing_journeys_filtered=getattr(pricing, "existing_journeys_filtered", 0),
                **_journey_duplicate_diagnostics(journey_pool, getattr(pricing, "journeys", []) or [], exact_duals, tuple(cuts)),
            )
            break
        if not pricing.exhausted:
            certificate_no_column_rounds += 1
            retry_enabled = bool(config.get("journey_retry_incomplete_no_column_enabled", True))
            retry_min_time = float(config.get("journey_retry_incomplete_no_column_min_time", 1.0))
            retry_remaining = max(0.0, time_limit - (time.perf_counter() - started))
            if retry_enabled and retry_remaining > max(min_pricing_time, retry_min_time):
                final_probe_config, _final_probe_mode = _journey_certificate_pricing_config(
                    config,
                    exact_pricing_config,
                    certificate_candidate=certificate_candidate,
                    certificate_flat_rounds=certificate_flat_rounds,
                    certificate_no_column_rounds=certificate_no_column_rounds,
                    depth=0,
                    completion_bound_phase="after_retry",
                )
                final_completion_bound_eligible = bool(
                    config.get("journey_certificate_completion_bound_after_retry_enabled", False)
                ) and bool(final_probe_config.direct_journey_label_completion_bound_enabled)
                retry_budget, completion_bound_final_reserve = _journey_retry_budget_with_completion_reserve(
                    config,
                    retry_remaining=retry_remaining,
                    min_pricing_time=min_pricing_time,
                    retry_min_time=retry_min_time,
                    final_completion_bound_eligible=final_completion_bound_eligible,
                )
                retry_config = replace(
                    exact_pricing_config,
                    time_limit=retry_budget,
                    profile_generation_time_fraction=float(
                        config.get("journey_retry_incomplete_no_column_generation_fraction", 1.0)
                    ),
                )
                retry_config, retry_force_ng = _journey_retry_force_ng_config(
                    config,
                    retry_config,
                    depth=0,
                )
                logger.log(
                    "journey_exact_pricing_retry",
                    node_id=0,
                    cg_iter=cg_iter,
                    remaining=round(float(retry_remaining), 6),
                    previous_status=pricing.status,
                    previous_reason=pricing.reason,
                    previous_best_reduced_cost=None
                    if pricing.best_reduced_cost is None
                    else round(float(pricing.best_reduced_cost), 9),
                    certificate_no_column_rounds=certificate_no_column_rounds,
                    completion_bound_enabled=bool(retry_config.direct_journey_label_completion_bound_enabled),
                    direct_journey_label_pricing_enabled=bool(retry_config.direct_journey_label_pricing_enabled),
                    direct_journey_label_ng_dssr_enabled=bool(retry_config.direct_journey_label_ng_dssr_enabled),
                    retry_force_ng=bool(retry_force_ng),
                    completion_bound_final_reserve=round(float(completion_bound_final_reserve), 6),
                )
                retry_pricing_kind = "exact_retry"
                pricing = price_journeys(
                    data,
                    exact_duals,
                    tuple(),
                    config=retry_config,
                    cuts=tuple(cuts),
                    trip_cache=trip_cache,
                    resource_cache=resource_cache,
                    forbidden_journey_signatures=set(journey_pool.by_signature.keys()),
                    dominant_task_set_costs=_journey_pricing_dominant_task_set_costs(journey_pool, cuts, tuple()),
                )
                pricing_calls += 1
                exact_pricing_calls += 1
                generated_sequences += pricing.generated_sequences
                evaluated_timed_trips += pricing.evaluated_timed_trips
                _log_journey_pricing(
                    logger,
                    pricing,
                    cg_iter,
                    pricing_kind="exact_retry",
                    config=retry_config,
                    pricing_dual_source=exact_dual_source,
                )
                if _journey_completion_bound_final_probe_needed(config, pricing):
                    final_remaining = max(0.0, time_limit - (time.perf_counter() - started))
                    final_min_time = float(
                        config.get("journey_certificate_completion_bound_after_retry_min_time", retry_min_time)
                    )
                    if final_remaining > max(min_pricing_time, final_min_time):
                        final_config, final_mode = _journey_certificate_pricing_config(
                            config,
                            retry_config,
                            certificate_candidate=certificate_candidate,
                            certificate_flat_rounds=certificate_flat_rounds,
                            certificate_no_column_rounds=certificate_no_column_rounds,
                            depth=0,
                            completion_bound_phase="after_retry",
                        )
                        final_config = replace(
                            final_config,
                            time_limit=final_remaining,
                            profile_generation_time_fraction=float(
                                config.get("journey_retry_incomplete_no_column_generation_fraction", 1.0)
                            ),
                        )
                        if (
                            bool(final_config.direct_journey_label_completion_bound_enabled)
                            and not bool(retry_config.direct_journey_label_completion_bound_enabled)
                        ):
                            logger.log(
                                "journey_exact_pricing_completion_bound_retry",
                                node_id=0,
                                cg_iter=cg_iter,
                                remaining=round(float(final_remaining), 6),
                                previous_status=pricing.status,
                                previous_reason=pricing.reason,
                                previous_best_reduced_cost=None
                                if pricing.best_reduced_cost is None
                                else round(float(pricing.best_reduced_cost), 9),
                                certificate_no_column_rounds=certificate_no_column_rounds,
                                completion_bound_enabled=True,
                                direct_journey_label_pricing_enabled=True,
                                retry_mode=final_mode,
                            )
                            pricing = price_journeys(
                                data,
                                exact_duals,
                                tuple(),
                                config=final_config,
                                cuts=tuple(cuts),
                                trip_cache=trip_cache,
                                resource_cache=resource_cache,
                                forbidden_journey_signatures=set(journey_pool.by_signature.keys()),
                                dominant_task_set_costs=_journey_pricing_dominant_task_set_costs(
                                    journey_pool, cuts, tuple()
                                ),
                            )
                            pricing_calls += 1
                            exact_pricing_calls += 1
                            generated_sequences += pricing.generated_sequences
                            evaluated_timed_trips += pricing.evaluated_timed_trips
                            retry_config = final_config
                            retry_pricing_kind = "exact_completion_bound_retry"
                            _log_journey_pricing(
                                logger,
                                pricing,
                                cg_iter,
                                pricing_kind=retry_pricing_kind,
                                config=retry_config,
                                pricing_dual_source=exact_dual_source,
                            )
                if pricing.journeys:
                    added = _add_priced_journeys(journey_pool, pricing.journeys)
                    _log_journey_addition(logger, pricing, added, cg_iter, pricing_kind=retry_pricing_kind)
                    if added > 0:
                        recent_priced_journeys = list(pricing.journeys)
                    if added > 0 and _should_run_journey_pool_probe(pool_probe_enabled, cg_iter, pool_probe_frequency):
                        incumbent, final_solution = _run_journey_pool_incumbent_probe(
                            data,
                            config,
                            journey_pool,
                            logger,
                            cg_iter,
                            incumbent,
                            final_solution,
                            fleet_limit=active_fleet_limit,
                            remaining=max(0.0, time_limit - (time.perf_counter() - started)),
                        )
                        active_fleet_limit = _update_journey_fleet_limit(
                            data,
                            logger,
                            active_fleet_limit,
                            incumbent,
                            final_solution,
                            cg_iter,
                            slack=_journey_fleet_limit_slack(config),
                        )
                    if added > 0:
                        certificate_no_column_rounds = 0
                        journey_pool, restarted = _maybe_restart_journey_pool(
                            data,
                            config,
                            journey_pool,
                            solution,
                            final_solution,
                            recent_priced_journeys,
                            logger,
                            cg_iter,
                            certificate_flat_rounds,
                            restart_count,
                            progress_classification=progress_classification,
                            degenerate_rounds=restart_degenerate_rounds,
                        )
                        restart_count += int(restarted)
                        continue
                if pricing.exhausted:
                    pass
                else:
                    break
            else:
                break
        if not pricing.exhausted:
            break
        dual_bound = float(solution.objective)
        pool_mip = solve_journey_pool_master(
            data,
            journey_pool.journeys,
            solve_integer=True,
            time_limit=float(config.get("journey_pool_time_limit", 3.0)),
            fleet_limit=active_fleet_limit,
        )
        logger.log(
            "journey_pool_integer",
            node_id=0,
            cg_iter=cg_iter,
            status=pool_mip.status,
            lp_objective=None if pool_mip.lp_objective is None else round(float(pool_mip.lp_objective), 6),
            mip_objective=None if pool_mip.mip_objective is None else round(float(pool_mip.mip_objective), 6),
            journeys=len(journey_pool.journeys),
        )
        if pool_mip.mip_objective is not None and pool_mip.mip_objective < incumbent - integer_tol:
            incumbent = float(pool_mip.mip_objective)
            final_solution = _journey_assignment(pool_mip.selected_journeys)
        if pool_mip.mip_objective is not None and pool_mip.mip_objective <= float(solution.objective) + integer_tol:
            status = "OPTIMAL"
            dual_bound = float(solution.objective)
        break

    elapsed = time.perf_counter() - started
    gap = None
    if incumbent < math.inf and dual_bound is not None:
        gap = max(0.0, (incumbent - dual_bound) / max(1.0, abs(incumbent)))
    result = FutureResult(
        status=status,
        primal_bound=None if incumbent == math.inf else round(float(incumbent), 6),
        dual_bound=None if dual_bound is None else round(float(dual_bound), 6),
        gap=None if gap is None else round(float(gap), 6),
        solving_time=round(elapsed, 6),
        node_count=1,
        rmp_solves=rmp_solves,
        pricing_calls=pricing_calls,
        exact_pricing_calls=exact_pricing_calls,
        generated_sequences=generated_sequences,
        evaluated_timed_trips=evaluated_timed_trips,
        columns=len(journey_pool.journeys),
        cuts_added=len(cuts),
        subset_row_cuts_added=_journey_cut_count(cuts, "subset_row"),
        sortie_lb_cut_added=0,
        fleet_lb_cut_added=_journey_cut_count(cuts, "fleet_lower_bound"),
        solution=final_solution,
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
    )
    return result


def _solve_bpc_future_journey_branch_price(
    data: FutureData,
    config: dict[str, Any],
    *,
    logger: FutureLogger,
) -> FutureResult:
    """Exact-safe Ryan-Foster branch-and-price over journey columns.

    This driver keeps the existing journey pricing oracle and only treats a
    node LP value as a valid lower bound after exact pricing reports exhausted.
    A branch node whose finite RMP pool is temporarily infeasible is marked
    incomplete rather than fathomed, because missing branch-feasible columns are
    not an infeasibility proof.
    """

    started = time.perf_counter()
    deadline = started + float(config.get("time_limit", 300.0))
    bucket = float(config.get("time_bucket_size", 10.0))
    start_step = float(config.get("pricing_start_time_step", bucket))
    integer_tol = float(config.get("integer_tol", 1.0e-6))
    eps = float(config.get("pricing_eps", 1.0e-6))
    max_nodes = int(config.get("journey_max_nodes", config.get("max_nodes", 1000)))

    from BPC_future.core.columns import TripPool

    trip_cache: dict[tuple, tuple] = {}
    trip_pool = TripPool()
    _seed_initial_trips(data, trip_pool, bucket, start_step, int(config.get("initial_single_task_starts_per_task", 0)))
    composite_seed_added = _seed_initial_composite_trips(
        data, config, trip_pool, bucket, start_step, trip_cache=trip_cache
    )
    savings_seed_added = _seed_initial_savings_trips(data, config, trip_pool, bucket, trip_cache=trip_cache)
    journey_pool = JourneyPool()
    initial_source = _journey_source_trips(trip_pool.trips, int(config.get("journey_initial_source_trip_limit", 1200)))
    initial_journeys = build_journey_pool(
        data,
        initial_source,
        max_trips_per_journey=int(config.get("journey_pool_max_trips_per_journey", data.sortie_limit)),
        max_columns=int(config.get("journey_initial_max_columns", config.get("journey_pool_max_columns", 5000))),
        max_extensions_per_prefix=int(config.get("journey_pool_max_extensions_per_prefix", 80)),
    )
    for journey in initial_journeys.journeys:
        journey_pool.add(journey)
    cuts = _journey_static_cuts(data, config)
    cut_keys = {cut.key for cut in cuts}
    _log_journey_static_cut_diagnostics(logger, config, cuts, node_id=0, depth=0)

    logger.log(
        "start",
        instance=data.name,
        tasks=len(data.tasks),
        vehicles=len(data.vehicles),
        initial_trip_columns=len(trip_pool.trips),
        initial_composite_seed_added=composite_seed_added,
        initial_savings_seed_added=savings_seed_added,
        initial_journey_columns=len(journey_pool.journeys),
        time_bucket_size=bucket,
        master="journey_branch_price",
        cuts_active=len(cuts),
        max_nodes=max_nodes,
    )

    incumbent = math.inf
    final_solution: dict[int, list[Any]] = {}
    active_fleet_limit = len(data.vehicles)
    if _journey_initial_pool_integer_enabled(config):
        initial_mip = solve_journey_pool_master(
            data,
            journey_pool.journeys,
            solve_integer=True,
            time_limit=float(config.get("journey_pool_time_limit", 3.0)),
        )
        if initial_mip.mip_objective is not None:
            incumbent = float(initial_mip.mip_objective)
            final_solution = _journey_assignment(initial_mip.selected_journeys)
            logger.log(
                "incumbent",
                node_id=0,
                objective=round(incumbent, 6),
                vehicles=len(final_solution),
                source="initial_journey_pool_mip",
            )
            active_fleet_limit = _update_journey_fleet_limit(
                data,
                logger,
                active_fleet_limit,
                incumbent,
                final_solution,
                0,
                slack=_journey_fleet_limit_slack(config),
            )
    else:
        logger.log("journey_initial_pool_integer", node_id=0, status="SKIPPED", reason="disabled")

    stats = JourneyBranchStats()
    open_nodes: list[JourneyNode] = [JourneyNode(0.0, 0, 0, tuple())]
    next_node_id = 1
    exact_node_bounds: list[float] = []
    search_incomplete = False
    branch_pricing_trip_cache: dict[tuple, Any] = {}
    branch_pricing_resource_cache: dict[tuple, Any] = {}

    while open_nodes and stats.nodes_processed < max_nodes and time.perf_counter() < deadline:
        node = heapq.heappop(open_nodes)
        if (
            bool(node.lower_bound_exact)
            and math.isfinite(incumbent)
            and float(node.lower_bound) >= float(incumbent) - integer_tol
        ):
            logger.log(
                "journey_fathom",
                node_id=node.id,
                depth=node.depth,
                reason="inherited_bound",
                lower_bound=round(float(node.lower_bound), 6),
                incumbent=round(float(incumbent), 6),
            )
            continue
        logger.log(
            "journey_node_start",
            node_id=node.id,
            depth=node.depth,
            lower_bound=round(float(node.lower_bound), 6),
            lower_bound_exact=bool(node.lower_bound_exact),
            open_nodes=len(open_nodes),
            branch_constraints=[constraint.name() for constraint in node.branch_constraints],
        )
        node_result = _process_journey_branch_node(
            data,
            config,
            journey_pool,
            cuts,
            cut_keys,
            node,
            incumbent,
            final_solution,
            active_fleet_limit,
            logger,
            stats,
            deadline=deadline,
            bucket=bucket,
            start_step=start_step,
            eps=eps,
            shared_pricing_trip_cache=branch_pricing_trip_cache,
            shared_pricing_resource_cache=branch_pricing_resource_cache,
        )
        _trim_journey_branch_pricing_cache(
            config,
            logger,
            branch_pricing_trip_cache,
            branch_pricing_resource_cache,
            node_id=node.id,
            depth=node.depth,
        )
        stats.nodes_processed += 1
        if node_result.get("incumbent_objective") is not None and float(node_result["incumbent_objective"]) < incumbent - integer_tol:
            incumbent = float(node_result["incumbent_objective"])
            final_solution = node_result.get("incumbent_solution", {}) or {}
            active_fleet_limit = _update_journey_fleet_limit(
                data,
                logger,
                active_fleet_limit,
                incumbent,
                final_solution,
                stats.nodes_processed,
                slack=_journey_fleet_limit_slack(config),
            )
        if node_result.get("active_fleet_limit") is not None:
            active_fleet_limit = int(node_result["active_fleet_limit"])

        status = str(node_result.get("status", "PRICING_INCOMPLETE"))
        if status == "INFEASIBLE":
            logger.log("journey_fathom", node_id=node.id, depth=node.depth, reason="proven_infeasible")
            continue
        if status == "PRICING_INCOMPLETE":
            search_incomplete = True
            stats.pricing_incomplete_nodes += 1
            logger.log(
                "journey_node_incomplete",
                node_id=node.id,
                depth=node.depth,
                reason=str(node_result.get("reason", "pricing_incomplete")),
            )
            continue
        if status == "BRANCH":
            solution = node_result["solution"]
            _log_journey_branch_candidates(
                data,
                config,
                logger,
                solution.journey_values,
                node.branch_constraints,
                integer_tol,
                node_id=node.id,
                depth=node.depth,
                incumbent_solution=final_solution,
                journey_pool=journey_pool,
            )
            branch = _choose_journey_branch(
                data,
                solution.journey_values,
                node.branch_constraints,
                integer_tol,
                tie_tolerance=float(config.get("journey_branch_fractionality_tie_tolerance", 0.0)),
                priority_mode=str(config.get("journey_branch_candidate_priority", "fractionality")),
                incumbent_solution=final_solution,
                journey_pool=journey_pool,
            )
            if branch is None:
                search_incomplete = True
                logger.log(
                    "journey_node_incomplete",
                    node_id=node.id,
                    depth=node.depth,
                    reason="early_branch_requested_but_no_ryan_foster_branch",
                )
                continue
            left, right = branch
            stats.branch_nodes += 1
            logger.log(
                "journey_branch",
                node_id=node.id,
                depth=node.depth,
                bound=round(float(node.lower_bound), 6),
                left=left.name(),
                right=right.name(),
                source="early_incomplete_pricing",
                exact_bound_available=False,
                child_lower_bound_exact=False,
            )
            by_width = bool(config.get("journey_child_priority_by_width_enabled", False))
            priority_mode = str(config.get("journey_child_priority_mode", "width" if by_width else "declared"))
            same_mass = _journey_branch_same_mass(solution.journey_values, branch)
            for constraint, allowed_count in _journey_child_constraint_order(
                journey_pool,
                node.branch_constraints,
                (left, right),
                by_width=by_width,
                priority_mode=priority_mode,
                journey_values=solution.journey_values,
                incumbent_solution=final_solution,
            ):
                queue_width = int(allowed_count) if by_width else 0
                logger.log(
                    "journey_child_queued",
                    parent_node_id=node.id,
                    child_node_id=next_node_id,
                    depth=node.depth + 1,
                    constraint=constraint.name(),
                    allowed_current_journeys=int(allowed_count),
                    priority_mode=priority_mode,
                    branch_same_mass=None if same_mass is None else round(float(same_mass), 9),
                    lower_bound=round(float(node.lower_bound), 6),
                    lower_bound_exact=False,
                )
                child = JourneyNode(
                    float(node.lower_bound),
                    next_node_id,
                    node.depth + 1,
                    (*node.branch_constraints, constraint),
                    False,
                    queue_width,
                )
                next_node_id += 1
                heapq.heappush(open_nodes, child)
            continue

        solution = node_result["solution"]
        bound = float(node_result["bound"])
        exact_node_bounds.append(bound)
        if math.isfinite(incumbent) and bound >= incumbent - integer_tol:
            logger.log(
                "journey_fathom",
                node_id=node.id,
                depth=node.depth,
                reason="bound",
                bound=round(bound, 6),
                incumbent=round(float(incumbent), 6),
            )
            continue
        if bool(node_result.get("integral", False)):
            if bound < incumbent - integer_tol:
                incumbent = bound
                final_solution = _journey_assignment(solution.journey_values)
                logger.log(
                    "incumbent",
                    node_id=node.id,
                    depth=node.depth,
                    objective=round(float(incumbent), 6),
                    vehicles=len(final_solution),
                    source="integral_journey_lp_after_exact_pricing",
                )
            logger.log("journey_fathom", node_id=node.id, depth=node.depth, reason="integral")
            continue

        _log_journey_branch_candidates(
            data,
            config,
            logger,
            solution.journey_values,
            node.branch_constraints,
            integer_tol,
            node_id=node.id,
            depth=node.depth,
            incumbent_solution=final_solution,
            journey_pool=journey_pool,
        )
        branch = _choose_journey_branch(
            data,
            solution.journey_values,
            node.branch_constraints,
            integer_tol,
            tie_tolerance=float(config.get("journey_branch_fractionality_tie_tolerance", 0.0)),
            priority_mode=str(config.get("journey_branch_candidate_priority", "fractionality")),
            incumbent_solution=final_solution,
            journey_pool=journey_pool,
        )
        if branch is None:
            search_incomplete = True
            logger.log(
                "journey_node_incomplete",
                node_id=node.id,
                depth=node.depth,
                reason="fractional_no_ryan_foster_branch",
                bound=round(bound, 6),
            )
            continue
        left, right = branch
        stats.branch_nodes += 1
        logger.log(
            "journey_branch",
            node_id=node.id,
            depth=node.depth,
            bound=round(bound, 6),
            left=left.name(),
            right=right.name(),
            child_lower_bound_exact=True,
        )
        by_width = bool(config.get("journey_child_priority_by_width_enabled", False))
        priority_mode = str(config.get("journey_child_priority_mode", "width" if by_width else "declared"))
        same_mass = _journey_branch_same_mass(solution.journey_values, branch)
        for constraint, allowed_count in _journey_child_constraint_order(
            journey_pool,
            node.branch_constraints,
            (left, right),
            by_width=by_width,
            priority_mode=priority_mode,
            journey_values=solution.journey_values,
            incumbent_solution=final_solution,
        ):
            queue_width = int(allowed_count) if by_width else 0
            logger.log(
                "journey_child_queued",
                parent_node_id=node.id,
                child_node_id=next_node_id,
                depth=node.depth + 1,
                constraint=constraint.name(),
                allowed_current_journeys=int(allowed_count),
                priority_mode=priority_mode,
                branch_same_mass=None if same_mass is None else round(float(same_mass), 9),
                lower_bound=round(float(bound), 6),
                lower_bound_exact=True,
            )
            child = JourneyNode(
                bound,
                next_node_id,
                node.depth + 1,
                (*node.branch_constraints, constraint),
                True,
                queue_width,
            )
            next_node_id += 1
            heapq.heappush(open_nodes, child)

    node_limit_hit = bool(open_nodes) and stats.nodes_processed >= max_nodes
    timed_out = time.perf_counter() >= deadline or bool(open_nodes) or node_limit_hit
    status = "OPTIMAL" if not timed_out and not search_incomplete and incumbent < math.inf else "TIME_LIMIT"
    lower_candidates = [float(node.lower_bound) for node in open_nodes if bool(node.lower_bound_exact)]
    lower_candidates.extend(exact_node_bounds)
    dual_bound = None
    if status == "OPTIMAL" and incumbent < math.inf:
        dual_bound = incumbent
    elif lower_candidates:
        dual_bound = min(lower_candidates)
    gap = None
    if incumbent < math.inf and dual_bound is not None:
        gap = max(0.0, (incumbent - dual_bound) / max(1.0, abs(incumbent)))
    elapsed = time.perf_counter() - started
    result = FutureResult(
        status=status,
        primal_bound=None if incumbent == math.inf else round(float(incumbent), 6),
        dual_bound=None if dual_bound is None else round(float(dual_bound), 6),
        gap=None if gap is None else round(float(gap), 6),
        solving_time=round(elapsed, 6),
        node_count=stats.nodes_processed,
        rmp_solves=stats.rmp_solves,
        pricing_calls=stats.pricing_calls,
        exact_pricing_calls=stats.exact_pricing_calls,
        generated_sequences=stats.generated_sequences,
        evaluated_timed_trips=stats.evaluated_timed_trips,
        columns=len(journey_pool.journeys),
        cuts_added=len(cuts),
        subset_row_cuts_added=_journey_cut_count(cuts, "subset_row"),
        sortie_lb_cut_added=0,
        fleet_lb_cut_added=_journey_cut_count(cuts, "fleet_lower_bound"),
        solution=final_solution,
    )
    logger.log(
        "finish",
        status=result.status,
        primal_bound=result.primal_bound,
        dual_bound=result.dual_bound,
        gap=result.gap,
        nodes=result.node_count,
        open_nodes=len(open_nodes),
        columns=result.columns,
        pricing_calls=result.pricing_calls,
        exact_pricing_calls=result.exact_pricing_calls,
        cuts_added=result.cuts_added,
        branch_nodes=stats.branch_nodes,
        pricing_incomplete_nodes=stats.pricing_incomplete_nodes,
        restarts=stats.restarts,
    )
    return result


def _process_journey_branch_node(
    data: FutureData,
    config: dict[str, Any],
    journey_pool: JourneyPool,
    cuts: list[FutureCut],
    cut_keys: set[tuple],
    node: JourneyNode,
    incumbent: float,
    final_solution: dict[int, list[Any]],
    active_fleet_limit: int,
    logger: FutureLogger,
    stats: JourneyBranchStats,
    *,
    deadline: float,
    bucket: float,
    start_step: float,
    eps: float,
    shared_pricing_trip_cache: dict[tuple, Any] | None = None,
    shared_pricing_resource_cache: dict[tuple, Any] | None = None,
) -> dict[str, Any]:
    integer_tol = float(config.get("integer_tol", 1.0e-6))
    max_cg = int(config.get("journey_max_cg_iterations", config.get("max_cg_iterations", 100)))
    min_pricing_time = float(config.get("journey_min_pricing_time", 1.0e-3))
    post_pricing_reserve = max(0.0, float(config.get("journey_post_pricing_time_reserve", 2.0)))
    pool_probe_enabled = bool(config.get("journey_pool_integer_heuristic_enabled", config.get("pool_integer_heuristic_enabled", True)))
    pool_probe_frequency = max(1, int(config.get("journey_pool_integer_frequency", config.get("pool_integer_heuristic_frequency", 2))))
    heuristic_round_limit = int(config.get("journey_heuristic_max_rounds", config.get("heuristic_pricing_max_rounds", 0)))
    previous_dual_vector: tuple[float, ...] | None = None
    previous_pricing_duals: JourneyDuals | None = None
    previous_rmp_objective: float | None = None
    previous_support_hash: str | None = None
    certificate_flat_rounds = 0
    restart_degenerate_rounds = 0
    restart_count = 0
    recent_priced_journeys: list[Any] = []
    cache_enabled = bool(config.get("journey_pricing_trip_cache_enabled", True))
    if int(node.depth) > 0 and "journey_branch_pricing_trip_cache_enabled" in config:
        cache_enabled = bool(config.get("journey_branch_pricing_trip_cache_enabled", cache_enabled))
    cross_node_cache_enabled = bool(config.get("journey_branch_pricing_cross_node_cache_enabled", False))
    if (
        cache_enabled
        and cross_node_cache_enabled
        and int(node.depth) > 0
        and shared_pricing_trip_cache is not None
    ):
        pricing_trip_cache: dict[tuple, Any] | None = shared_pricing_trip_cache
    else:
        pricing_trip_cache = {} if cache_enabled else None
    if cross_node_cache_enabled and int(node.depth) > 0 and shared_pricing_resource_cache is not None:
        pricing_resource_cache: dict[tuple, Any] = shared_pricing_resource_cache
    else:
        pricing_resource_cache = {}
    local_incumbent = float(incumbent)
    local_solution = final_solution
    learning_runtime: _JourneyLearningRuntime | None = None
    learning_runtime_initialized = False
    learning_certificate_gate_logged = False
    certificate_no_column_rounds = 0
    retry_negative_after_no_column_rounds = 0

    def payload(status: str, **extra: Any) -> dict[str, Any]:
        extra["status"] = status
        extra["active_fleet_limit"] = int(active_fleet_limit)
        if local_incumbent < float(incumbent) - integer_tol:
            extra["incumbent_objective"] = local_incumbent
            extra["incumbent_solution"] = local_solution
        return extra

    for cg_iter in range(1, max_cg + 1):
        if time.perf_counter() >= deadline:
            return payload("PRICING_INCOMPLETE", reason="time_limit")
        active_fleet_limit = _update_journey_fleet_limit(
            data,
            logger,
            active_fleet_limit,
            local_incumbent,
            local_solution,
            cg_iter,
            node_id=node.id,
            depth=node.depth,
            slack=_journey_fleet_limit_slack(config),
        )
        node_journeys = _filter_journeys_by_branch(journey_pool.journeys, node.branch_constraints)
        if not node_journeys:
            return payload("PRICING_INCOMPLETE", reason="empty_branch_filtered_pool")
        solution = solve_journey_rmp(data, node_journeys, cuts=tuple(cuts), fleet_limit=active_fleet_limit)
        stats.rmp_solves += 1
        logger.log(
            "journey_rmp",
            node_id=node.id,
            depth=node.depth,
            cg_iter=cg_iter,
            objective=None if solution.objective is None else round(float(solution.objective), 6),
            status=solution.status,
            journeys=len(node_journeys),
            global_journeys=len(journey_pool.journeys),
            variables=solution.variable_count,
            fleet_limit=active_fleet_limit,
        )
        if not solution.optimal or solution.duals is None or solution.objective is None:
            return payload("PRICING_INCOMPLETE", reason=f"rmp_{solution.status.lower()}")
        if node.depth == 0:
            dynamic_cuts_added = _separate_journey_subset_row_cuts(
                data,
                config,
                solution,
                cuts,
                cut_keys,
                logger,
                cg_iter,
                node_id=node.id,
                depth=node.depth,
            )
            if dynamic_cuts_added > 0:
                stats.dynamic_cuts_total += int(dynamic_cuts_added)
                stats.dynamic_subset_row_cuts_total += int(dynamic_cuts_added)
                continue
        _log_journey_learning_dual_trace(
            data,
            config,
            logger,
            solution.duals,
            objective=float(solution.objective),
            cg_iter=cg_iter,
            node_id=node.id,
            depth=node.depth,
        )

        scip_dual_vector = _journey_dual_vector(data, solution.duals, len(cuts))
        support_hash = _journey_support_hash(solution.journey_values)
        objective_delta = None if previous_rmp_objective is None else float(solution.objective) - float(previous_rmp_objective)
        scip_dual_l1_delta = None if previous_dual_vector is None else sum(abs(a - b) for a, b in zip(scip_dual_vector, previous_dual_vector))
        certificate_candidate = bool(
            math.isfinite(local_incumbent)
            and float(solution.objective) >= float(local_incumbent) - float(integer_tol)
        )
        if certificate_candidate and objective_delta is not None and abs(float(objective_delta)) <= max(eps, float(integer_tol)):
            certificate_flat_rounds += 1
        else:
            certificate_flat_rounds = 0
        progress_classification = _journey_progress_classification(
            objective_delta,
            scip_dual_l1_delta,
            previous_support_hash,
            support_hash,
            eps,
        )
        if progress_classification in {
            "dual_changed_degenerate",
            "support_changed_objective_flat",
            "stalled_same_dual_support",
        }:
            restart_degenerate_rounds += 1
        else:
            restart_degenerate_rounds = 0
        pricing_duals, pricing_dual_source = _select_journey_pricing_duals(
            data,
            config,
            journey_pool,
            tuple(cuts),
            active_fleet_limit,
            float(solution.objective),
            solution.duals,
            previous_pricing_duals,
            logger,
            cg_iter,
            progress_classification=progress_classification,
            incumbent=local_incumbent,
            integer_tol=integer_tol,
            remaining_time=max(0.0, deadline - time.perf_counter()),
            certificate_flat_rounds=certificate_flat_rounds,
        )
        dual_vector = _journey_dual_vector(data, pricing_duals, len(cuts))
        dual_hash = _journey_dual_hash(dual_vector)
        dual_l1_delta = None if previous_dual_vector is None else sum(abs(a - b) for a, b in zip(dual_vector, previous_dual_vector))
        dual_linf_delta = None if previous_dual_vector is None else max(abs(a - b) for a, b in zip(dual_vector, previous_dual_vector))
        logger.log(
            "journey_rmp_dual_diagnostics",
            node_id=node.id,
            depth=node.depth,
            cg_iter=cg_iter,
            objective=round(float(solution.objective), 6),
            objective_delta=None if objective_delta is None else round(objective_delta, 9),
            dual_hash=dual_hash,
            dual_l1_delta=None if dual_l1_delta is None else round(dual_l1_delta, 9),
            dual_linf_delta=None if dual_linf_delta is None else round(dual_linf_delta, 9),
            active_journeys=len(solution.journey_values),
            active_support_hash=support_hash,
        )
        logger.log(
            "journey_cg_progress_diagnostics",
            node_id=node.id,
            depth=node.depth,
            cg_iter=cg_iter,
            classification=progress_classification,
            objective_delta=None if objective_delta is None else round(objective_delta, 9),
            dual_changed=None if dual_l1_delta is None else bool(dual_l1_delta > eps),
            scip_dual_l1_delta=None if scip_dual_l1_delta is None else round(scip_dual_l1_delta, 9),
            support_changed=None if previous_support_hash is None else bool(previous_support_hash != support_hash),
            dual_hash=dual_hash,
            pricing_dual_source=pricing_dual_source,
            active_support_hash=support_hash,
            certificate_candidate=certificate_candidate,
            certificate_flat_rounds=certificate_flat_rounds,
            restart_degenerate_rounds=restart_degenerate_rounds,
        )
        previous_dual_vector = dual_vector
        previous_pricing_duals = pricing_duals
        previous_rmp_objective = float(solution.objective)
        previous_support_hash = support_hash

        if _journey_lp_integral(solution.journey_values, integer_tol):
            old_incumbent = local_incumbent
            if float(solution.objective) < local_incumbent - integer_tol:
                local_incumbent = float(solution.objective)
                local_solution = _journey_assignment(solution.journey_values)
            updated_certificate_candidate = bool(
                math.isfinite(local_incumbent)
                and float(solution.objective) >= float(local_incumbent) - float(integer_tol)
            )
            if updated_certificate_candidate and not certificate_candidate:
                logger.log(
                    "journey_certificate_candidate_updated",
                    node_id=node.id,
                    depth=node.depth,
                    cg_iter=cg_iter,
                    reason="integral_rmp_incumbent",
                    old_incumbent=None if old_incumbent == math.inf else round(float(old_incumbent), 6),
                    incumbent=round(float(local_incumbent), 6),
                    rmp_objective=round(float(solution.objective), 6),
                )
            certificate_candidate = updated_certificate_candidate

        base_heuristic_allowed = (
            bool(config.get("journey_heuristic_pricing_enabled", True))
            and (heuristic_round_limit <= 0 or cg_iter <= heuristic_round_limit)
        )
        learning_certificate_disabled = _journey_learning_certificate_gate_disabled(config, certificate_candidate)
        if (
            not learning_runtime_initialized
            and learning_certificate_disabled
            and bool(config.get("journey_learning_enabled", False))
            and not learning_certificate_gate_logged
        ):
            logger.log(
                "journey_learning",
                node_id=node.id,
                depth=node.depth,
                cg_iter=cg_iter,
                status="DISABLED",
                reason="certificate_candidate_gate",
                certificate_candidate=bool(certificate_candidate),
            )
            learning_certificate_gate_logged = True
        if (
            not learning_runtime_initialized
            and not learning_certificate_disabled
            and bool(config.get("journey_learning_enabled", False))
        ):
            learning_runtime = _maybe_create_journey_learning_runtime(data, config, logger, node_id=node.id, depth=node.depth)
            learning_runtime_initialized = True
        active_learning_runtime = _journey_learning_runtime_for_pricing(
            learning_runtime,
            config,
            cg_iter=cg_iter,
            certificate_disabled=learning_certificate_disabled,
        )
        learning_heuristic_allowed = active_learning_runtime is not None
        heuristic_allowed = bool(base_heuristic_allowed or learning_heuristic_allowed)
        if heuristic_allowed:
            remaining = max(0.0, deadline - time.perf_counter())
            if remaining <= min_pricing_time:
                return payload("PRICING_INCOMPLETE", reason="time_limit")
            heuristic_config = _journey_pricing_config(
                data,
                config,
                bucket,
                start_step,
                eps,
                remaining,
                heuristic=True,
                cg_iter=cg_iter,
            )
            heuristic_config = _journey_node_depth_pricing_config(config, heuristic_config, node.depth)
            heuristic_duals, heuristic_dual_source, learning_smoothed = _journey_learning_pricing_duals(
                active_learning_runtime,
                solution.duals,
                rmp_objective=float(solution.objective),
                branch_depth=int(node.depth),
                logger=logger,
                cg_iter=cg_iter,
                node_id=node.id,
                depth=node.depth,
            )
            if not learning_smoothed:
                heuristic_duals, heuristic_dual_source = pricing_duals, pricing_dual_source
            if not learning_smoothed and not base_heuristic_allowed:
                logger.log(
                    "journey_learning_smoothing",
                    node_id=node.id,
                    depth=node.depth,
                    cg_iter=cg_iter,
                    status="SKIPPED",
                    reason="learning_not_active_and_base_heuristic_disabled",
                )
            else:
                if learning_smoothed:
                    heuristic_config = _journey_learning_pricing_config(config, heuristic_config)
                heuristic_trip_cache, heuristic_resource_cache = _journey_pricing_caches_for_learning_pass(
                    learning_smoothed=learning_smoothed,
                    trip_cache=pricing_trip_cache if pricing_trip_cache is not None else {},
                    resource_cache=pricing_resource_cache,
                )
                pricing = price_journeys(
                    data,
                    heuristic_duals,
                    node.branch_constraints,
                    config=heuristic_config,
                    cuts=tuple(cuts),
                    trip_cache=heuristic_trip_cache,
                    resource_cache=heuristic_resource_cache,
                    forbidden_journey_signatures=_journey_forbidden_signatures_for_node(
                        journey_pool, node.branch_constraints
                    ),
                    dominant_task_set_costs=_journey_pricing_dominant_task_set_costs(
                        journey_pool, cuts, node.branch_constraints
                    ),
                )
                stats.pricing_calls += 1
                stats.generated_sequences += pricing.generated_sequences
                stats.evaluated_timed_trips += pricing.evaluated_timed_trips
                _log_journey_pricing(
                    logger,
                    pricing,
                    cg_iter,
                    pricing_kind="heuristic",
                    config=heuristic_config,
                    pricing_dual_source=heuristic_dual_source,
                    node_id=node.id,
                    depth=node.depth,
                )
                priced_journeys = pricing.journeys
                if learning_smoothed and learning_runtime is not None and learning_runtime.filter_true_rc:
                    priced_journeys = _journey_learning_true_rc_filter(
                        logger,
                        pricing.journeys,
                        true_duals=solution.duals,
                        cuts=tuple(cuts),
                        tol=learning_runtime.true_rc_tol if learning_runtime is not None else 1.0e-5,
                        keep_threshold=learning_runtime.true_rc_keep_threshold
                        if learning_runtime is not None
                        else 0.0,
                        max_kept=learning_runtime.true_rc_max_kept_per_round
                        if learning_runtime is not None
                        else 0,
                        fallback_keep_threshold=learning_runtime.true_rc_fallback_keep_threshold
                        if learning_runtime is not None
                        else 0.0,
                        fallback_max_kept=learning_runtime.true_rc_fallback_max_kept_per_round
                        if learning_runtime is not None
                        else 0,
                        cg_iter=cg_iter,
                        node_id=node.id,
                        depth=node.depth,
                        pricing_kind="heuristic",
                    )
                if priced_journeys:
                    pricing_for_add = replace(pricing, journeys=list(priced_journeys))
                    added = _add_priced_journeys(journey_pool, list(priced_journeys))
                    _log_journey_addition(
                        logger,
                        pricing_for_add,
                        added,
                        cg_iter,
                        pricing_kind="heuristic",
                        node_id=node.id,
                        depth=node.depth,
                    )
                    if learning_smoothed and learning_runtime is not None:
                        _journey_learning_handle_smoothed_pricing_result(
                            logger,
                            learning_runtime,
                            found_negative_column=added > 0,
                            candidate_journeys=len(pricing.journeys),
                            kept_journeys=len(priced_journeys),
                            added_journeys=added,
                            cg_iter=cg_iter,
                            node_id=node.id,
                            depth=node.depth,
                            pricing_kind="heuristic",
                        )
                    if added > 0 and _should_run_journey_pool_probe(pool_probe_enabled, cg_iter, pool_probe_frequency):
                        local_incumbent, local_solution = _run_journey_pool_incumbent_probe(
                            data,
                            config,
                            journey_pool,
                            logger,
                            cg_iter,
                            local_incumbent,
                            local_solution,
                            fleet_limit=active_fleet_limit,
                            remaining=max(0.0, deadline - time.perf_counter()),
                            node_id=node.id,
                            depth=node.depth,
                        )
                    if added > 0:
                        certificate_no_column_rounds = 0
                        retry_negative_after_no_column_rounds = 0
                        continue
                elif learning_smoothed and learning_runtime is not None:
                    _journey_learning_handle_smoothed_pricing_result(
                        logger,
                        learning_runtime,
                        found_negative_column=False,
                        candidate_journeys=len(pricing.journeys),
                        kept_journeys=0,
                        added_journeys=0,
                        cg_iter=cg_iter,
                        node_id=node.id,
                        depth=node.depth,
                        pricing_kind="heuristic",
                    )

        remaining = max(0.0, deadline - time.perf_counter())
        if remaining <= min_pricing_time:
            return payload("PRICING_INCOMPLETE", reason="time_limit")
        exact_budget, reserve_used, budget_reason = _journey_exact_pricing_budget(
            remaining=remaining,
            post_pricing_reserve=post_pricing_reserve,
            min_pricing_time=min_pricing_time,
            incumbent=local_incumbent,
            rmp_objective=float(solution.objective),
            integer_tol=integer_tol,
            cg_iter=cg_iter,
            certificate_no_reserve_enabled=bool(config.get("journey_certificate_no_reserve_enabled", True)),
            certificate_no_reserve_min_cg_iter=int(config.get("journey_certificate_no_reserve_min_cg_iter", 3)),
        )
        logger.log(
            "journey_exact_pricing_budget",
            node_id=node.id,
            depth=node.depth,
            cg_iter=cg_iter,
            remaining=round(float(remaining), 6),
            exact_budget=round(float(exact_budget), 6),
            post_pricing_reserve=round(float(post_pricing_reserve), 6),
            reserve_used=round(float(reserve_used), 6),
            reason=budget_reason,
            incumbent=None if local_incumbent == math.inf else round(float(local_incumbent), 6),
            rmp_objective=round(float(solution.objective), 6),
        )
        exact_config = _journey_pricing_config(
            data,
            config,
            bucket,
            start_step,
            eps,
            exact_budget,
            heuristic=False,
            cg_iter=cg_iter,
        )
        exact_config = _journey_node_depth_pricing_config(config, exact_config, node.depth)
        exact_config, certificate_pricing_mode = _journey_certificate_pricing_config(
            config,
            exact_config,
            certificate_candidate=certificate_candidate,
            certificate_flat_rounds=certificate_flat_rounds,
            certificate_no_column_rounds=certificate_no_column_rounds,
            depth=node.depth,
        )
        exact_config, immediate_no_reserve = _journey_immediate_certificate_no_reserve_config(
            config,
            exact_config,
            certificate_candidate=certificate_candidate,
            budget_reason=budget_reason,
            exact_budget=exact_budget,
        )
        if immediate_no_reserve:
            logger.log(
                "journey_certificate_immediate_no_reserve",
                node_id=node.id,
                depth=node.depth,
                cg_iter=cg_iter,
                time_limit=round(float(exact_config.time_limit), 6),
                profile_generation_time_fraction=round(float(exact_config.profile_generation_time_fraction), 6),
            )
        skip_short_exact = _journey_should_skip_short_exact_pricing(
            config,
            depth=node.depth,
            cg_iter=cg_iter,
            certificate_candidate=certificate_candidate,
            retry_negative_after_no_column_rounds=retry_negative_after_no_column_rounds,
        )
        if skip_short_exact:
            old_time_limit = float(exact_config.time_limit)
            skip_time_limit = max(float(old_time_limit), float(exact_budget))
            max_skip_time_limit = float(config.get("journey_skip_short_exact_max_time_limit", 0.0))
            if max_skip_time_limit > 0.0:
                skip_time_limit = min(float(skip_time_limit), float(max_skip_time_limit))
            exact_config = replace(
                exact_config,
                time_limit=skip_time_limit,
                profile_generation_time_fraction=float(
                    config.get("journey_retry_incomplete_no_column_generation_fraction", 1.0)
                ),
            )
            logger.log(
                "journey_skip_short_exact_pricing",
                node_id=node.id,
                depth=node.depth,
                cg_iter=cg_iter,
                retry_negative_after_no_column_rounds=int(retry_negative_after_no_column_rounds),
                old_time_limit=round(float(old_time_limit), 6),
                new_time_limit=round(float(exact_config.time_limit), 6),
                profile_generation_time_fraction=round(float(exact_config.profile_generation_time_fraction), 6),
                certificate_candidate=bool(certificate_candidate),
            )
        final_probe_preview, _final_probe_preview_mode = _journey_certificate_pricing_config(
            config,
            exact_config,
            certificate_candidate=certificate_candidate,
            certificate_flat_rounds=certificate_flat_rounds,
            certificate_no_column_rounds=certificate_no_column_rounds + 1,
            depth=node.depth,
            completion_bound_phase="after_retry",
        )
        pre_retry_reserve = _journey_pre_retry_completion_reserve_time(
            config,
            remaining=remaining,
            exact_time_limit=float(exact_config.time_limit),
            min_pricing_time=min_pricing_time,
            final_completion_bound_eligible=bool(final_probe_preview.direct_journey_label_completion_bound_enabled),
            exact_completion_bound_enabled=bool(exact_config.direct_journey_label_completion_bound_enabled),
        )
        if pre_retry_reserve > 0.0:
            old_time_limit = float(exact_config.time_limit)
            exact_config = replace(exact_config, time_limit=max(float(min_pricing_time), old_time_limit - pre_retry_reserve))
            logger.log(
                "journey_exact_pricing_completion_bound_pre_reserve",
                node_id=node.id,
                depth=node.depth,
                cg_iter=cg_iter,
                old_time_limit=round(float(old_time_limit), 6),
                new_time_limit=round(float(exact_config.time_limit), 6),
                reserved_time=round(float(old_time_limit) - float(exact_config.time_limit), 6),
                remaining=round(float(remaining), 6),
                remaining_threshold=round(
                    float(config.get("journey_certificate_completion_bound_pre_retry_reserve_remaining_threshold", 0.0)),
                    6,
                ),
            )
        exact_duals, exact_dual_source = _journey_exact_pricing_duals(
            solution.duals,
            pricing_duals,
            pricing_dual_source,
            learning_runtime=learning_runtime,
            certificate_candidate=certificate_candidate,
            completion_bound_enabled=exact_config.direct_journey_label_completion_bound_enabled,
        )
        pricing = price_journeys(
            data,
            exact_duals,
            node.branch_constraints,
            config=exact_config,
            cuts=tuple(cuts),
            trip_cache=pricing_trip_cache if pricing_trip_cache is not None else {},
            resource_cache=pricing_resource_cache,
            forbidden_journey_signatures=_journey_forbidden_signatures_for_node(
                journey_pool, node.branch_constraints
            ),
            dominant_task_set_costs=_journey_pricing_dominant_task_set_costs(
                journey_pool, cuts, node.branch_constraints
            ),
        )
        stats.pricing_calls += 1
        stats.exact_pricing_calls += 1
        stats.generated_sequences += pricing.generated_sequences
        stats.evaluated_timed_trips += pricing.evaluated_timed_trips
        _log_journey_pricing(
            logger,
            pricing,
            cg_iter,
            pricing_kind="exact",
            config=exact_config,
            pricing_dual_source=exact_dual_source,
            node_id=node.id,
            depth=node.depth,
        )
        if pricing.journeys:
            added = _add_priced_journeys(journey_pool, pricing.journeys)
            _log_journey_addition(
                logger,
                pricing,
                added,
                cg_iter,
                pricing_kind="exact",
                node_id=node.id,
                depth=node.depth,
            )
            if added > 0:
                recent_priced_journeys = list(pricing.journeys)
            if added > 0 and _should_run_journey_pool_probe(pool_probe_enabled, cg_iter, pool_probe_frequency):
                local_incumbent, local_solution = _run_journey_pool_incumbent_probe(
                    data,
                    config,
                    journey_pool,
                    logger,
                    cg_iter,
                    local_incumbent,
                    local_solution,
                    fleet_limit=active_fleet_limit,
                    remaining=max(0.0, deadline - time.perf_counter()),
                    node_id=node.id,
                    depth=node.depth,
                )
            if added > 0:
                certificate_no_column_rounds = 0
                if not bool(skip_short_exact):
                    retry_negative_after_no_column_rounds = 0
                if _journey_should_early_branch(config, node, cg_iter, solution, integer_tol):
                    logger.log(
                        "journey_early_branch_trigger",
                        node_id=node.id,
                        depth=node.depth,
                        cg_iter=cg_iter,
                        reason="negative_columns_tailing",
                        added_journeys=added,
                        inherited_lower_bound=round(float(node.lower_bound), 6),
                        rmp_objective=round(float(solution.objective), 6),
                        exact_bound_available=False,
                        child_lower_bound_exact=False,
                    )
                    return payload("BRANCH", solution=solution, bound=float(node.lower_bound), exact_bound=False)
                restarted_pool, restarted = _maybe_restart_journey_pool(
                    data,
                    config,
                    journey_pool,
                    solution,
                    local_solution,
                    recent_priced_journeys,
                    logger,
                    cg_iter,
                    certificate_flat_rounds,
                    restart_count,
                    progress_classification=progress_classification,
                    degenerate_rounds=restart_degenerate_rounds,
                )
                if restarted:
                    journey_pool.journeys = restarted_pool.journeys
                    journey_pool.by_signature = restarted_pool.by_signature
                    journey_pool.by_task_set = restarted_pool.by_task_set
                    stats.restarts += 1
                    restart_count += 1
                continue
            logger.log(
                "journey_pricing_duplicate_block",
                node_id=node.id,
                depth=node.depth,
                cg_iter=cg_iter,
                pricing_kind="exact",
                exhausted=pricing.exhausted,
                reason="negative_journey_already_in_pool",
                rmp_objective=round(float(solution.objective), 9),
                dual_hash=dual_hash,
                pricing_status=pricing.status,
                pricing_reason=pricing.reason,
                existing_journeys_filtered=getattr(pricing, "existing_journeys_filtered", 0),
                **_journey_duplicate_diagnostics(journey_pool, getattr(pricing, "journeys", []) or [], exact_duals, tuple(cuts)),
            )
            return payload("PRICING_INCOMPLETE", reason="duplicate_negative_journey")
        if not pricing.exhausted:
            certificate_no_column_rounds += 1
            retry_enabled = bool(config.get("journey_retry_incomplete_no_column_enabled", True)) and not bool(
                skip_short_exact
            )
            retry_min_time = float(config.get("journey_retry_incomplete_no_column_min_time", 1.0))
            retry_remaining = max(0.0, deadline - time.perf_counter())
            if retry_enabled and retry_remaining > max(min_pricing_time, retry_min_time):
                retry_config, retry_mode = _journey_certificate_pricing_config(
                    config,
                    exact_config,
                    certificate_candidate=certificate_candidate,
                    certificate_flat_rounds=certificate_flat_rounds,
                    certificate_no_column_rounds=certificate_no_column_rounds,
                    depth=node.depth,
                )
                final_probe_config, _final_probe_mode = _journey_certificate_pricing_config(
                    config,
                    exact_config,
                    certificate_candidate=certificate_candidate,
                    certificate_flat_rounds=certificate_flat_rounds,
                    certificate_no_column_rounds=certificate_no_column_rounds,
                    depth=node.depth,
                    completion_bound_phase="after_retry",
                )
                final_completion_bound_eligible = bool(
                    config.get("journey_certificate_completion_bound_after_retry_enabled", False)
                ) and bool(final_probe_config.direct_journey_label_completion_bound_enabled)
                retry_budget, completion_bound_final_reserve = _journey_retry_budget_with_completion_reserve(
                    config,
                    retry_remaining=retry_remaining,
                    min_pricing_time=min_pricing_time,
                    retry_min_time=retry_min_time,
                    final_completion_bound_eligible=final_completion_bound_eligible,
                )
                retry_config = replace(
                    retry_config,
                    time_limit=retry_budget,
                    profile_generation_time_fraction=float(
                        config.get("journey_retry_incomplete_no_column_generation_fraction", 1.0)
                    ),
                )
                retry_config, retry_force_ng = _journey_retry_force_ng_config(
                    config,
                    retry_config,
                    depth=node.depth,
                )
                logger.log(
                    "journey_exact_pricing_retry",
                    node_id=node.id,
                    depth=node.depth,
                    cg_iter=cg_iter,
                    remaining=round(float(retry_remaining), 6),
                    previous_status=pricing.status,
                    previous_reason=pricing.reason,
                    previous_best_reduced_cost=None
                    if pricing.best_reduced_cost is None
                    else round(float(pricing.best_reduced_cost), 9),
                    certificate_no_column_rounds=certificate_no_column_rounds,
                    completion_bound_enabled=bool(retry_config.direct_journey_label_completion_bound_enabled),
                    direct_journey_label_pricing_enabled=bool(retry_config.direct_journey_label_pricing_enabled),
                    direct_journey_label_ng_dssr_enabled=bool(retry_config.direct_journey_label_ng_dssr_enabled),
                    retry_force_ng=bool(retry_force_ng),
                    completion_bound_final_reserve=round(float(completion_bound_final_reserve), 6),
                    retry_mode=retry_mode,
                )
                retry_pricing_kind = "exact_retry"
                pricing = price_journeys(
                    data,
                    exact_duals,
                    node.branch_constraints,
                    config=retry_config,
                    cuts=tuple(cuts),
                    trip_cache=pricing_trip_cache if pricing_trip_cache is not None else {},
                    resource_cache=pricing_resource_cache,
                    forbidden_journey_signatures=_journey_forbidden_signatures_for_node(
                        journey_pool, node.branch_constraints
                    ),
                    dominant_task_set_costs=_journey_pricing_dominant_task_set_costs(
                        journey_pool, cuts, node.branch_constraints
                    ),
                )
                stats.pricing_calls += 1
                stats.exact_pricing_calls += 1
                stats.generated_sequences += pricing.generated_sequences
                stats.evaluated_timed_trips += pricing.evaluated_timed_trips
                _log_journey_pricing(
                    logger,
                    pricing,
                    cg_iter,
                    pricing_kind="exact_retry",
                    config=retry_config,
                    pricing_dual_source=exact_dual_source,
                    node_id=node.id,
                    depth=node.depth,
                )
                if _journey_completion_bound_final_probe_needed(config, pricing):
                    final_remaining = max(0.0, deadline - time.perf_counter())
                    final_min_time = float(
                        config.get("journey_certificate_completion_bound_after_retry_min_time", retry_min_time)
                    )
                    if final_remaining > max(min_pricing_time, final_min_time):
                        final_config, final_mode = _journey_certificate_pricing_config(
                            config,
                            retry_config,
                            certificate_candidate=certificate_candidate,
                            certificate_flat_rounds=certificate_flat_rounds,
                            certificate_no_column_rounds=certificate_no_column_rounds,
                            depth=node.depth,
                            completion_bound_phase="after_retry",
                        )
                        final_config = replace(
                            final_config,
                            time_limit=final_remaining,
                            profile_generation_time_fraction=float(
                                config.get("journey_retry_incomplete_no_column_generation_fraction", 1.0)
                            ),
                        )
                        if (
                            bool(final_config.direct_journey_label_completion_bound_enabled)
                            and not bool(retry_config.direct_journey_label_completion_bound_enabled)
                        ):
                            logger.log(
                                "journey_exact_pricing_completion_bound_retry",
                                node_id=node.id,
                                depth=node.depth,
                                cg_iter=cg_iter,
                                remaining=round(float(final_remaining), 6),
                                previous_status=pricing.status,
                                previous_reason=pricing.reason,
                                previous_best_reduced_cost=None
                                if pricing.best_reduced_cost is None
                                else round(float(pricing.best_reduced_cost), 9),
                                certificate_no_column_rounds=certificate_no_column_rounds,
                                completion_bound_enabled=True,
                                direct_journey_label_pricing_enabled=True,
                                retry_mode=final_mode,
                            )
                            pricing = price_journeys(
                                data,
                                exact_duals,
                                node.branch_constraints,
                                config=final_config,
                                cuts=tuple(cuts),
                                trip_cache=pricing_trip_cache if pricing_trip_cache is not None else {},
                                resource_cache=pricing_resource_cache,
                                forbidden_journey_signatures=_journey_forbidden_signatures_for_node(
                                    journey_pool, node.branch_constraints
                                ),
                                dominant_task_set_costs=_journey_pricing_dominant_task_set_costs(
                                    journey_pool, cuts, node.branch_constraints
                                ),
                            )
                            stats.pricing_calls += 1
                            stats.exact_pricing_calls += 1
                            stats.generated_sequences += pricing.generated_sequences
                            stats.evaluated_timed_trips += pricing.evaluated_timed_trips
                            retry_config = final_config
                            retry_pricing_kind = "exact_completion_bound_retry"
                            _log_journey_pricing(
                                logger,
                                pricing,
                                cg_iter,
                                pricing_kind=retry_pricing_kind,
                                config=retry_config,
                                pricing_dual_source=exact_dual_source,
                                node_id=node.id,
                                depth=node.depth,
                            )
                if pricing.journeys:
                    added = _add_priced_journeys(journey_pool, pricing.journeys)
                    _log_journey_addition(
                        logger,
                        pricing,
                        added,
                        cg_iter,
                        pricing_kind=retry_pricing_kind,
                        node_id=node.id,
                        depth=node.depth,
                    )
                    if added > 0:
                        certificate_no_column_rounds = 0
                        retry_negative_after_no_column_rounds += 1
                        continue
                    duplicate_resolved_by_final_probe = False
                    if (
                        retry_pricing_kind != "exact_completion_bound_retry"
                        and _journey_completion_bound_final_probe_needed(config, pricing, added_columns=added)
                    ):
                        final_remaining = max(0.0, deadline - time.perf_counter())
                        final_min_time = float(
                            config.get("journey_certificate_completion_bound_after_retry_min_time", retry_min_time)
                        )
                        if final_remaining > max(min_pricing_time, final_min_time):
                            final_config, final_mode = _journey_certificate_pricing_config(
                                config,
                                retry_config,
                                certificate_candidate=certificate_candidate,
                                certificate_flat_rounds=certificate_flat_rounds,
                                certificate_no_column_rounds=certificate_no_column_rounds,
                                depth=node.depth,
                                completion_bound_phase="after_retry",
                            )
                            final_config = replace(
                                final_config,
                                time_limit=final_remaining,
                                profile_generation_time_fraction=float(
                                    config.get("journey_retry_incomplete_no_column_generation_fraction", 1.0)
                                ),
                            )
                            if bool(final_config.direct_journey_label_completion_bound_enabled) and not bool(
                                retry_config.direct_journey_label_completion_bound_enabled
                            ):
                                logger.log(
                                    "journey_exact_pricing_completion_bound_retry",
                                    node_id=node.id,
                                    depth=node.depth,
                                    cg_iter=cg_iter,
                                    remaining=round(float(final_remaining), 6),
                                    previous_status=pricing.status,
                                    previous_reason=pricing.reason,
                                    previous_best_reduced_cost=None
                                    if pricing.best_reduced_cost is None
                                    else round(float(pricing.best_reduced_cost), 9),
                                    certificate_no_column_rounds=certificate_no_column_rounds,
                                    completion_bound_enabled=True,
                                    direct_journey_label_pricing_enabled=True,
                                    retry_mode=final_mode,
                                    trigger="duplicate_no_new_columns",
                                )
                                pricing = price_journeys(
                                    data,
                                    exact_duals,
                                    node.branch_constraints,
                                    config=final_config,
                                    cuts=tuple(cuts),
                                    trip_cache=pricing_trip_cache if pricing_trip_cache is not None else {},
                                    resource_cache=pricing_resource_cache,
                                    forbidden_journey_signatures=_journey_forbidden_signatures_for_node(
                                        journey_pool, node.branch_constraints
                                    ),
                                    dominant_task_set_costs=_journey_pricing_dominant_task_set_costs(
                                        journey_pool, cuts, node.branch_constraints
                                    ),
                                )
                                stats.pricing_calls += 1
                                stats.exact_pricing_calls += 1
                                stats.generated_sequences += pricing.generated_sequences
                                stats.evaluated_timed_trips += pricing.evaluated_timed_trips
                                retry_config = final_config
                                retry_pricing_kind = "exact_completion_bound_retry"
                                _log_journey_pricing(
                                    logger,
                                    pricing,
                                    cg_iter,
                                    pricing_kind=retry_pricing_kind,
                                    config=retry_config,
                                    pricing_dual_source=exact_dual_source,
                                    node_id=node.id,
                                    depth=node.depth,
                                )
                                if pricing.journeys:
                                    added = _add_priced_journeys(journey_pool, pricing.journeys)
                                    _log_journey_addition(
                                        logger,
                                        pricing,
                                        added,
                                        cg_iter,
                                        pricing_kind=retry_pricing_kind,
                                        node_id=node.id,
                                        depth=node.depth,
                                    )
                                    if added > 0:
                                        certificate_no_column_rounds = 0
                                        retry_negative_after_no_column_rounds += 1
                                        continue
                                if pricing.exhausted:
                                    duplicate_resolved_by_final_probe = True
                    if duplicate_resolved_by_final_probe:
                        pass
                    else:
                        logger.log(
                            "journey_pricing_duplicate_block",
                            node_id=node.id,
                            depth=node.depth,
                            cg_iter=cg_iter,
                            pricing_kind=retry_pricing_kind,
                            exhausted=pricing.exhausted,
                            reason="negative_journey_already_in_pool",
                            rmp_objective=round(float(solution.objective), 9),
                            dual_hash=dual_hash,
                            pricing_status=pricing.status,
                            pricing_reason=pricing.reason,
                            existing_journeys_filtered=getattr(pricing, "existing_journeys_filtered", 0),
                            **_journey_duplicate_diagnostics(
                                journey_pool, getattr(pricing, "journeys", []) or [], exact_duals, tuple(cuts)
                            ),
                        )
                        return payload("PRICING_INCOMPLETE", reason="duplicate_negative_journey")
                if pricing.exhausted:
                    pass
                else:
                    return payload("PRICING_INCOMPLETE", reason=str(pricing.reason or "pricing_incomplete"))
            else:
                if _journey_completion_bound_final_probe_needed(config, pricing):
                    final_remaining = max(0.0, deadline - time.perf_counter())
                    final_min_time = float(
                        config.get("journey_certificate_completion_bound_after_retry_min_time", retry_min_time)
                    )
                    if final_remaining > max(min_pricing_time, final_min_time):
                        final_config, final_mode = _journey_certificate_pricing_config(
                            config,
                            exact_config,
                            certificate_candidate=certificate_candidate,
                            certificate_flat_rounds=certificate_flat_rounds,
                            certificate_no_column_rounds=certificate_no_column_rounds,
                            depth=node.depth,
                            completion_bound_phase="after_retry",
                        )
                        final_config = replace(
                            final_config,
                            time_limit=final_remaining,
                            profile_generation_time_fraction=float(
                                config.get("journey_retry_incomplete_no_column_generation_fraction", 1.0)
                            ),
                        )
                        if bool(final_config.direct_journey_label_completion_bound_enabled):
                            logger.log(
                                "journey_exact_pricing_completion_bound_retry",
                                node_id=node.id,
                                depth=node.depth,
                                cg_iter=cg_iter,
                                remaining=round(float(final_remaining), 6),
                                previous_status=pricing.status,
                                previous_reason=pricing.reason,
                                previous_best_reduced_cost=None
                                if pricing.best_reduced_cost is None
                                else round(float(pricing.best_reduced_cost), 9),
                                certificate_no_column_rounds=certificate_no_column_rounds,
                                completion_bound_enabled=True,
                                direct_journey_label_pricing_enabled=True,
                                retry_mode=final_mode,
                                trigger="no_retry_budget",
                            )
                            pricing = price_journeys(
                                data,
                                exact_duals,
                                node.branch_constraints,
                                config=final_config,
                                cuts=tuple(cuts),
                                trip_cache=pricing_trip_cache if pricing_trip_cache is not None else {},
                                resource_cache=pricing_resource_cache,
                                forbidden_journey_signatures=_journey_forbidden_signatures_for_node(
                                    journey_pool, node.branch_constraints
                                ),
                                dominant_task_set_costs=_journey_pricing_dominant_task_set_costs(
                                    journey_pool, cuts, node.branch_constraints
                                ),
                            )
                            stats.pricing_calls += 1
                            stats.exact_pricing_calls += 1
                            stats.generated_sequences += pricing.generated_sequences
                            stats.evaluated_timed_trips += pricing.evaluated_timed_trips
                            _log_journey_pricing(
                                logger,
                                pricing,
                                cg_iter,
                                pricing_kind="exact_completion_bound_retry",
                                config=final_config,
                                pricing_dual_source=exact_dual_source,
                                node_id=node.id,
                                depth=node.depth,
                            )
                            if pricing.journeys:
                                added = _add_priced_journeys(journey_pool, pricing.journeys)
                                _log_journey_addition(
                                    logger,
                                    pricing,
                                    added,
                                    cg_iter,
                                    pricing_kind="exact_completion_bound_retry",
                                    node_id=node.id,
                                    depth=node.depth,
                                )
                                if added > 0:
                                    certificate_no_column_rounds = 0
                                    retry_negative_after_no_column_rounds += 1
                                    continue
                            if pricing.exhausted:
                                pass
                            else:
                                return payload("PRICING_INCOMPLETE", reason=str(pricing.reason or "pricing_incomplete"))
                        else:
                            return payload("PRICING_INCOMPLETE", reason=str(pricing.reason or "pricing_incomplete"))
                    else:
                        return payload("PRICING_INCOMPLETE", reason=str(pricing.reason or "pricing_incomplete"))
                else:
                    return payload("PRICING_INCOMPLETE", reason=str(pricing.reason or "pricing_incomplete"))
        if not pricing.exhausted:
            return payload("PRICING_INCOMPLETE", reason=str(pricing.reason or "pricing_incomplete"))

        if (
            bool(config.get("journey_skip_pool_integer_when_bound_fathoms_enabled", True))
            and math.isfinite(local_incumbent)
            and float(solution.objective) >= float(local_incumbent) - integer_tol
        ):
            logger.log(
                "journey_pool_integer_skip",
                node_id=node.id,
                depth=node.depth,
                cg_iter=cg_iter,
                reason="lp_bound_fathoms",
                lp_objective=round(float(solution.objective), 6),
                incumbent=round(float(local_incumbent), 6),
                journeys=len(_filter_journeys_by_branch(journey_pool.journeys, node.branch_constraints)),
            )
            return payload(
                "COMPLETE",
                solution=solution,
                bound=float(solution.objective),
                integral=_journey_lp_integral(solution.journey_values, integer_tol),
            )

        pool_mip = solve_journey_pool_master(
            data,
            _filter_journeys_by_branch(journey_pool.journeys, node.branch_constraints),
            solve_integer=True,
            time_limit=float(config.get("journey_pool_time_limit", 3.0)),
            fleet_limit=active_fleet_limit,
        )
        stats.pool_integer_solves += 1
        logger.log(
            "journey_pool_integer",
            node_id=node.id,
            depth=node.depth,
            cg_iter=cg_iter,
            status=pool_mip.status,
            lp_objective=None if pool_mip.lp_objective is None else round(float(pool_mip.lp_objective), 6),
            mip_objective=None if pool_mip.mip_objective is None else round(float(pool_mip.mip_objective), 6),
            journeys=len(_filter_journeys_by_branch(journey_pool.journeys, node.branch_constraints)),
        )
        if pool_mip.mip_objective is not None and pool_mip.mip_objective < local_incumbent - integer_tol:
            local_incumbent = float(pool_mip.mip_objective)
            local_solution = _journey_assignment(pool_mip.selected_journeys)
            logger.log(
                "incumbent",
                node_id=node.id,
                depth=node.depth,
                cg_iter=cg_iter,
                objective=round(float(local_incumbent), 6),
                vehicles=len(local_solution),
                source="journey_pool_integer_after_certificate",
            )
        return payload(
            "COMPLETE",
            solution=solution,
            bound=float(solution.objective),
            integral=_journey_lp_integral(solution.journey_values, integer_tol),
        )
    return payload("PRICING_INCOMPLETE", reason="max_cg_iterations")


def _journey_lp_integral(values: list[tuple[Any, float]], tol: float) -> bool:
    return all(abs(float(value) - round(float(value))) <= float(tol) for _journey, value in values)


def _trim_journey_branch_pricing_cache(
    config: dict[str, Any],
    logger: FutureLogger,
    trip_cache: dict[tuple, Any],
    resource_cache: dict[tuple, Any],
    *,
    node_id: int,
    depth: int,
) -> None:
    if not bool(config.get("journey_branch_pricing_cross_node_cache_enabled", False)):
        return
    max_entries = int(config.get("journey_branch_pricing_cross_node_cache_max_entries", 20000))
    if max_entries <= 0 or len(trip_cache) <= max_entries:
        return
    logger.log(
        "journey_branch_pricing_cache_clear",
        node_id=int(node_id),
        depth=int(depth),
        entries=int(len(trip_cache)),
        resource_entries=int(len(resource_cache)),
        max_entries=int(max_entries),
        reason="max_entries_exceeded",
    )
    trip_cache.clear()
    resource_cache.clear()


def _journey_allowed_by_branch(journey: Any, constraints: tuple[BranchConstraint, ...]) -> bool:
    task_set = {int(task) for task in getattr(journey, "task_set", frozenset())}
    for constraint in constraints:
        if constraint.task_j is None:
            return False
        left = int(constraint.task_i) in task_set
        right = int(constraint.task_j) in task_set
        if constraint.kind == "same_vehicle" and left != right:
            return False
        if constraint.kind == "separate_vehicle" and left and right:
            return False
        if constraint.kind not in {"same_vehicle", "separate_vehicle"}:
            return False
    return True


def _filter_journeys_by_branch(journeys: list[Any], constraints: tuple[BranchConstraint, ...]) -> list[Any]:
    if not constraints:
        return list(journeys)
    return [journey for journey in journeys if _journey_allowed_by_branch(journey, constraints)]


def _ordered_journey_child_constraints(
    journey_pool: JourneyPool,
    parent_constraints: tuple[BranchConstraint, ...],
    branch: tuple[BranchConstraint, BranchConstraint],
) -> list[tuple[BranchConstraint, int]]:
    ranked = []
    for constraint in branch:
        constraints = (*parent_constraints, constraint)
        allowed = sum(1 for journey in journey_pool.journeys if _journey_allowed_by_branch(journey, constraints))
        ranked.append((constraint, int(allowed)))
    ranked.sort(key=lambda item: (item[1], item[0].kind, item[0].task_i, item[0].task_j or -1))
    return ranked


def _journey_child_constraint_order(
    journey_pool: JourneyPool,
    parent_constraints: tuple[BranchConstraint, ...],
    branch: tuple[BranchConstraint, BranchConstraint],
    *,
    by_width: bool,
    priority_mode: str | None = None,
    journey_values: list[tuple[Any, float]] | None = None,
    incumbent_solution: dict[int, list[Any]] | None = None,
) -> list[tuple[BranchConstraint, int]]:
    ordered = _ordered_journey_child_constraints(journey_pool, parent_constraints, branch)
    mode = str(priority_mode or ("width" if by_width else "declared"))
    if mode == "width" or (bool(by_width) and mode in {"", "declared"}):
        return ordered
    allowed_by_key = {_branch_constraint_key(constraint): allowed for constraint, allowed in ordered}
    declared = [(constraint, int(allowed_by_key.get(_branch_constraint_key(constraint), 0))) for constraint in branch]
    if mode == "incumbent_relation":
        relation = _journey_incumbent_pair_relation(incumbent_solution or {}, branch[0].task_i, branch[0].task_j)
        if relation is None:
            return declared
        order_index = {_branch_constraint_key(constraint): index for index, constraint in enumerate(branch)}

        def incumbent_rank(item: tuple[BranchConstraint, int]) -> tuple[int, int]:
            constraint, _allowed = item
            preferred = (constraint.kind == "same_vehicle") if bool(relation) else (constraint.kind == "separate_vehicle")
            return (0 if preferred else 1, int(order_index.get(_branch_constraint_key(constraint), 0)))

        return sorted(declared, key=incumbent_rank)
    if mode not in {"lp_rounding", "lp_rounding_wide_tie"}:
        return declared
    same_mass = _journey_branch_same_mass(journey_values or [], branch)
    if same_mass is None:
        return declared
    if mode == "lp_rounding_wide_tie" and abs(float(same_mass) - 0.5) <= 1.0e-9:
        order_index = {_branch_constraint_key(constraint): index for index, constraint in enumerate(branch)}
        return sorted(
            declared,
            key=lambda item: (-int(item[1]), int(order_index.get(_branch_constraint_key(item[0]), 0))),
        )
    prefer_same = float(same_mass) >= 0.5
    order_index = {_branch_constraint_key(constraint): index for index, constraint in enumerate(branch)}

    def rank(item: tuple[BranchConstraint, int]) -> tuple[int, int]:
        constraint, _allowed = item
        preferred = (constraint.kind == "same_vehicle") if prefer_same else (constraint.kind == "separate_vehicle")
        return (0 if preferred else 1, int(order_index.get(_branch_constraint_key(constraint), 0)))

    return sorted(declared, key=rank)


def _journey_branch_same_mass(
    journey_values: list[tuple[Any, float]] | None,
    branch: tuple[BranchConstraint, BranchConstraint],
) -> float | None:
    pairs = [
        (int(constraint.task_i), int(constraint.task_j))
        for constraint in branch
        if constraint.task_j is not None and constraint.kind in {"same_vehicle", "separate_vehicle"}
    ]
    if not pairs:
        return None
    i, j = pairs[0]
    total = 0.0
    for journey, value in journey_values or []:
        task_set = getattr(journey, "task_set", frozenset())
        if int(i) in task_set and int(j) in task_set:
            total += float(value)
    return float(total)


def _branch_constraint_key(constraint: BranchConstraint) -> tuple:
    return (
        str(constraint.kind),
        int(constraint.task_i),
        None if constraint.task_j is None else int(constraint.task_j),
        None if constraint.vehicle is None else int(constraint.vehicle),
    )


def _journey_incumbent_pair_relation(
    incumbent_solution: dict[int, list[Any]],
    task_i: int,
    task_j: int | None,
) -> bool | None:
    if task_j is None or not incumbent_solution:
        return None
    owner: dict[int, int] = {}
    for vehicle, trips in incumbent_solution.items():
        for trip in trips or []:
            for task in getattr(trip, "tasks", tuple()) or tuple():
                owner[int(task)] = int(vehicle)
    left = owner.get(int(task_i))
    right = owner.get(int(task_j))
    if left is None or right is None:
        return None
    return bool(left == right)


def _choose_journey_branch(
    data: FutureData,
    journey_values: list[tuple[Any, float]],
    constraints: tuple[BranchConstraint, ...],
    tol: float,
    *,
    tie_tolerance: float = 0.0,
    priority_mode: str = "fractionality",
    incumbent_solution: dict[int, list[Any]] | None = None,
    journey_pool: JourneyPool | None = None,
) -> tuple[BranchConstraint, BranchConstraint] | None:
    candidates = _journey_branch_candidates(
        data,
        journey_values,
        constraints,
        tol,
        incumbent_solution=incumbent_solution,
        journey_pool=journey_pool,
    )
    if not candidates:
        return None
    max_frac = max(float(candidate["fractionality"]) for candidate in candidates)
    tolerance = max(0.0, float(tie_tolerance))
    eligible = [
        candidate
        for candidate in candidates
        if float(candidate["fractionality"]) >= float(max_frac) - float(tolerance) - 1.0e-12
    ]
    mode = str(priority_mode)
    if mode == "pool_split":
        with_width = [candidate for candidate in eligible if candidate.get("pool_same_allowed") is not None]
        pool = with_width or eligible
        chosen = min(
            pool,
            key=lambda candidate: (
                int(candidate.get("pool_max_child_width", 10**12)),
                int(candidate.get("pool_total_child_width", 10**12)),
                int(candidate.get("pool_balance_gap", 10**12)),
                -float(candidate["fractionality"]),
                int(candidate["task_i"]),
                int(candidate["task_j"]),
            ),
        )
    elif mode == "incumbent_disagreement":
        with_relation = [candidate for candidate in eligible if candidate.get("incumbent_relation") is not None]
        pool = with_relation or eligible
        chosen = min(
            pool,
            key=lambda candidate: (
                -float(candidate.get("incumbent_disagreement", 0.0)),
                -float(candidate["fractionality"]),
                -int(candidate.get("support_count", 0)),
                int(candidate["task_i"]),
                int(candidate["task_j"]),
            ),
        )
    elif mode == "low_task_index":
        chosen = min(
            eligible,
            key=lambda candidate: (
                int(candidate["task_i"]),
                int(candidate["task_j"]),
                -float(candidate["fractionality"]),
                round(float(candidate["same_mass"]), 9),
            ),
        )
    else:
        chosen = min(
            candidates,
            key=lambda candidate: (
                -float(candidate["fractionality"]),
                int(candidate["task_i"]),
                int(candidate["task_j"]),
                round(float(candidate["same_mass"]), 9),
            ),
        )
    i = int(chosen["task_i"])
    j = int(chosen["task_j"])
    return (
        BranchConstraint("same_vehicle", i, j),
        BranchConstraint("separate_vehicle", i, j),
    )


def _journey_branch_candidates(
    data: FutureData,
    journey_values: list[tuple[Any, float]],
    constraints: tuple[BranchConstraint, ...],
    tol: float,
    *,
    incumbent_solution: dict[int, list[Any]] | None = None,
    journey_pool: JourneyPool | None = None,
) -> list[dict[str, Any]]:
    fixed_pairs = {
        tuple(sorted((int(constraint.task_i), int(constraint.task_j))))
        for constraint in constraints
        if constraint.kind in {"same_vehicle", "separate_vehicle"} and constraint.task_j is not None
    }
    candidates: list[dict[str, Any]] = []
    for index, i in enumerate(data.tasks):
        for j in data.tasks[index + 1 :]:
            key = tuple(sorted((int(i), int(j))))
            if key in fixed_pairs:
                continue
            same_mass = 0.0
            support = 0
            for journey, value in journey_values:
                task_set = getattr(journey, "task_set", frozenset())
                if int(i) in task_set and int(j) in task_set:
                    same_mass += float(value)
                    if float(value) > float(tol):
                        support += 1
            frac = abs(float(same_mass) - round(float(same_mass)))
            if frac <= float(tol):
                continue
            relation = _journey_incumbent_pair_relation(incumbent_solution or {}, int(i), int(j))
            if relation is None:
                incumbent_disagreement = 0.0
            elif bool(relation):
                incumbent_disagreement = max(0.0, 1.0 - float(same_mass))
            else:
                incumbent_disagreement = max(0.0, float(same_mass))
            pool_same_allowed: int | None = None
            pool_separate_allowed: int | None = None
            pool_max_child_width: int | None = None
            pool_total_child_width: int | None = None
            pool_balance_gap: int | None = None
            if journey_pool is not None:
                same_constraint = BranchConstraint("same_vehicle", int(i), int(j))
                separate_constraint = BranchConstraint("separate_vehicle", int(i), int(j))
                same_constraints = (*constraints, same_constraint)
                separate_constraints = (*constraints, separate_constraint)
                pool_same_allowed = sum(
                    1 for journey in journey_pool.journeys if _journey_allowed_by_branch(journey, same_constraints)
                )
                pool_separate_allowed = sum(
                    1 for journey in journey_pool.journeys if _journey_allowed_by_branch(journey, separate_constraints)
                )
                pool_max_child_width = max(int(pool_same_allowed), int(pool_separate_allowed))
                pool_total_child_width = int(pool_same_allowed) + int(pool_separate_allowed)
                pool_balance_gap = abs(int(pool_same_allowed) - int(pool_separate_allowed))
            candidates.append(
                {
                    "task_i": int(i),
                    "task_j": int(j),
                    "same_mass": float(same_mass),
                    "fractionality": float(frac),
                    "support_count": int(support),
                    "incumbent_relation": relation,
                    "incumbent_disagreement": float(incumbent_disagreement),
                    "pool_same_allowed": pool_same_allowed,
                    "pool_separate_allowed": pool_separate_allowed,
                    "pool_max_child_width": pool_max_child_width,
                    "pool_total_child_width": pool_total_child_width,
                    "pool_balance_gap": pool_balance_gap,
                }
            )
    candidates.sort(
        key=lambda candidate: (
            -float(candidate["fractionality"]),
            int(candidate["task_i"]),
            int(candidate["task_j"]),
            round(float(candidate["same_mass"]), 9),
        )
    )
    return candidates


def _log_journey_branch_candidates(
    data: FutureData,
    config: dict[str, Any],
    logger: FutureLogger,
    journey_values: list[tuple[Any, float]],
    constraints: tuple[BranchConstraint, ...],
    tol: float,
    *,
    node_id: int,
    depth: int,
    incumbent_solution: dict[int, list[Any]] | None = None,
    journey_pool: JourneyPool | None = None,
) -> None:
    top_n = int(config.get("journey_branch_candidate_log_top_n", 0))
    if top_n <= 0:
        return
    candidates = _journey_branch_candidates(
        data,
        journey_values,
        constraints,
        tol,
        incumbent_solution=incumbent_solution,
        journey_pool=journey_pool,
    )
    max_frac = None if not candidates else max(float(candidate["fractionality"]) for candidate in candidates)
    logger.log(
        "journey_branch_candidates",
        node_id=node_id,
        depth=depth,
        candidate_count=len(candidates),
        max_fractionality=None if max_frac is None else round(float(max_frac), 9),
        tie_tolerance=round(float(config.get("journey_branch_fractionality_tie_tolerance", 0.0)), 9),
        priority_mode=str(config.get("journey_branch_candidate_priority", "fractionality")),
        top=[
            {
                "task_i": int(candidate["task_i"]),
                "task_j": int(candidate["task_j"]),
                "same_mass": round(float(candidate["same_mass"]), 9),
                "fractionality": round(float(candidate["fractionality"]), 9),
                "support_count": int(candidate["support_count"]),
                "incumbent_relation": candidate.get("incumbent_relation"),
                "incumbent_disagreement": round(float(candidate.get("incumbent_disagreement", 0.0)), 9),
                "pool_same_allowed": candidate.get("pool_same_allowed"),
                "pool_separate_allowed": candidate.get("pool_separate_allowed"),
                "pool_max_child_width": candidate.get("pool_max_child_width"),
                "pool_balance_gap": candidate.get("pool_balance_gap"),
            }
            for candidate in candidates[: max(0, top_n)]
        ],
    )


def _journey_should_early_branch(
    config: dict[str, Any],
    node: JourneyNode,
    cg_iter: int,
    solution: Any,
    integer_tol: float,
) -> bool:
    """Return whether incomplete-pricing branching is allowed.

    This is a branching heuristic only.  The caller must not use the current
    RMP objective as an exact node lower bound when this returns true.
    """

    if not bool(config.get("journey_early_branching_enabled", False)):
        return False
    if int(node.depth) > int(config.get("journey_early_branching_max_depth", 0)):
        return False
    if int(node.depth) > 0:
        min_cg_iter = int(
            config.get(
                "journey_early_branching_child_min_cg_iter",
                config.get("journey_early_branching_min_cg_iter", 1),
            )
        )
    else:
        min_cg_iter = int(config.get("journey_early_branching_min_cg_iter", 1))
    if int(cg_iter) < max(1, min_cg_iter):
        return False
    if _journey_lp_integral(getattr(solution, "journey_values", []) or [], float(integer_tol)):
        return False
    if _choose_journey_branch_placeholder(solution, node.branch_constraints, float(integer_tol)) is None:
        return False
    return True


def _choose_journey_branch_placeholder(
    solution: Any,
    constraints: tuple[BranchConstraint, ...],
    tol: float,
) -> tuple[int, int] | None:
    fixed_pairs = {
        tuple(sorted((int(constraint.task_i), int(constraint.task_j))))
        for constraint in constraints
        if constraint.kind in {"same_vehicle", "separate_vehicle"} and constraint.task_j is not None
    }
    tasks = sorted(
        {
            int(task)
            for journey, _value in getattr(solution, "journey_values", []) or []
            for task in getattr(journey, "task_set", frozenset())
        }
    )
    for index, i in enumerate(tasks):
        for j in tasks[index + 1 :]:
            key = tuple(sorted((int(i), int(j))))
            if key in fixed_pairs:
                continue
            same_mass = 0.0
            for journey, value in getattr(solution, "journey_values", []) or []:
                task_set = getattr(journey, "task_set", frozenset())
                if int(i) in task_set and int(j) in task_set:
                    same_mass += float(value)
            if abs(float(same_mass) - round(float(same_mass))) > float(tol):
                return int(i), int(j)
    return None


def _journey_exact_pricing_budget(
    *,
    remaining: float,
    post_pricing_reserve: float,
    min_pricing_time: float,
    incumbent: float,
    rmp_objective: float,
    integer_tol: float,
    cg_iter: int = 1,
    certificate_no_reserve_enabled: bool = True,
    certificate_no_reserve_min_cg_iter: int = 3,
) -> tuple[float, float, str]:
    remaining = max(0.0, float(remaining))
    reserve = max(0.0, float(post_pricing_reserve))
    min_time = max(0.0, float(min_pricing_time))
    if remaining <= min_time:
        return remaining, 0.0, "below_min_pricing_time"
    if (
        bool(certificate_no_reserve_enabled)
        and int(cg_iter) >= max(1, int(certificate_no_reserve_min_cg_iter))
        and math.isfinite(float(incumbent))
        and float(rmp_objective) >= float(incumbent) - float(integer_tol)
    ):
        return remaining, 0.0, "certificate_candidate_no_reserve"
    if reserve > 0.0 and remaining > reserve + min_time:
        return max(min_time, remaining - reserve), reserve, "post_pricing_reserve"
    return remaining, 0.0, "full_remaining"


def _journey_immediate_certificate_no_reserve_config(
    config: dict[str, Any],
    pricing_config: JourneyPricingConfig,
    *,
    certificate_candidate: bool,
    budget_reason: str,
    exact_budget: float,
) -> tuple[JourneyPricingConfig, bool]:
    if not bool(config.get("journey_certificate_immediate_no_reserve_enabled", False)):
        return pricing_config, False
    if not bool(certificate_candidate) or str(budget_reason) != "certificate_candidate_no_reserve":
        return pricing_config, False
    budget = max(0.0, float(exact_budget))
    if budget <= float(pricing_config.time_limit) + 1.0e-9:
        return pricing_config, False
    generation_fraction = float(
        config.get(
            "journey_certificate_immediate_no_reserve_generation_fraction",
            config.get("journey_retry_incomplete_no_column_generation_fraction", pricing_config.profile_generation_time_fraction),
        )
    )
    return (
        replace(
            pricing_config,
            time_limit=budget,
            profile_generation_time_fraction=generation_fraction,
        ),
        True,
    )


def _journey_initial_pool_integer_enabled(config: dict[str, Any]) -> bool:
    if "journey_initial_pool_integer_heuristic_enabled" in config:
        return bool(config.get("journey_initial_pool_integer_heuristic_enabled", True))
    return bool(config.get("initial_pool_integer_heuristic_enabled", True))


def _journey_learning_pricing_max_rounds(config: dict[str, Any]) -> int:
    return int(config.get("journey_learning_pricing_max_rounds", _JOURNEY_LEARNING_DEFAULT_PRICING_MAX_ROUNDS))


def _journey_learning_true_rc_max_kept_per_round(config: dict[str, Any]) -> int:
    return max(
        0,
        int(
            config.get(
                "journey_learning_true_rc_max_kept_per_round",
                _JOURNEY_LEARNING_DEFAULT_TRUE_RC_MAX_KEPT_PER_ROUND,
            )
        ),
    )


def _journey_learning_true_rc_keep_threshold(config: dict[str, Any]) -> float:
    return max(0.0, float(config.get("journey_learning_true_rc_keep_threshold", 0.0)))


def _journey_learning_true_rc_fallback_keep_threshold(config: dict[str, Any]) -> float:
    return max(0.0, float(config.get("journey_learning_true_rc_fallback_keep_threshold", 0.0)))


def _journey_learning_true_rc_fallback_max_kept_per_round(config: dict[str, Any]) -> int:
    return max(0, int(config.get("journey_learning_true_rc_fallback_max_kept_per_round", 0)))


def _journey_learning_filter_true_rc_enabled(config: dict[str, Any]) -> bool:
    return bool(config.get("journey_learning_filter_true_rc", True))


def _journey_learning_certificate_gate_disabled(config: dict[str, Any], certificate_candidate: bool) -> bool:
    """Return whether the exact-safe default disables learning at certificate time."""

    return bool(config.get("journey_learning_disable_on_certificate_candidate", True)) and bool(certificate_candidate)


def _journey_learning_pricing_config(
    config: dict[str, Any],
    pricing_config: JourneyPricingConfig,
) -> JourneyPricingConfig:
    """Apply learning-only pricing budget overrides.

    The learning pass is a true-RC-filtered candidate generator.  Keeping its
    budget separate from exact pricing prevents a noisy anchor from consuming
    the certificate tail's wall-clock budget.  All keys are optional; when none
    are present this helper returns the original config object unchanged.
    """

    updated = pricing_config
    if "journey_learning_pricing_time_limit" in config:
        budget = float(config["journey_learning_pricing_time_limit"])
        if budget > 0.0:
            updated = replace(updated, time_limit=min(float(updated.time_limit), budget))
    if "journey_learning_profile_generation_time_fraction" in config:
        updated = replace(
            updated,
            profile_generation_time_fraction=float(config["journey_learning_profile_generation_time_fraction"]),
        )
    if "journey_learning_max_returned_journeys" in config:
        updated = replace(updated, max_returned_journeys=max(1, int(config["journey_learning_max_returned_journeys"])))
    if "journey_learning_streaming_profile_batch_size" in config:
        updated = replace(
            updated,
            streaming_profile_batch_size=max(1, int(config["journey_learning_streaming_profile_batch_size"])),
        )
    if "journey_learning_streaming_min_negative_batch" in config:
        value = max(1, int(config["journey_learning_streaming_min_negative_batch"]))
        updated = replace(
            updated,
            streaming_min_negative_batch=value,
            early_return_negative_min_count=min(int(updated.early_return_negative_min_count), value),
        )
    if "journey_learning_early_return_negative_min_count" in config:
        updated = replace(
            updated,
            early_return_negative_min_count=max(1, int(config["journey_learning_early_return_negative_min_count"])),
        )
    if "journey_learning_streaming_min_returned_journeys" in config:
        updated = replace(
            updated,
            streaming_min_returned_journeys=max(1, int(config["journey_learning_streaming_min_returned_journeys"])),
        )
    if "journey_learning_streaming_partial_return_after_time" in config:
        updated = replace(
            updated,
            streaming_partial_return_after_time=max(0.0, float(config["journey_learning_streaming_partial_return_after_time"])),
        )
    if "journey_learning_streaming_partial_return_min_journeys" in config:
        updated = replace(
            updated,
            streaming_partial_return_min_journeys=max(0, int(config["journey_learning_streaming_partial_return_min_journeys"])),
        )
    return updated


def _journey_pricing_caches_for_learning_pass(
    *,
    learning_smoothed: bool,
    trip_cache: dict[tuple, Any],
    resource_cache: dict[tuple, Any],
) -> tuple[dict[tuple, Any], dict[tuple, Any]]:
    """Return pricing caches, isolating smoothed-dual search state.

    Some journey pricing caches hold label-resume/catalog state initialized
    under the current reduced-cost vector.  A GNN-smoothed vector is allowed to
    suggest candidate columns, but its search state must never be reused by the
    true-dual exact certificate path.
    """

    if learning_smoothed:
        return {}, {}
    return trip_cache, resource_cache


def _journey_learning_runtime_for_pricing(
    runtime: _JourneyLearningRuntime | None,
    config: dict[str, Any],
    *,
    cg_iter: int,
    certificate_disabled: bool,
) -> _JourneyLearningRuntime | None:
    """Return the learning runtime only when smoothed pricing is allowed now."""

    if runtime is None:
        return None
    if bool(getattr(runtime, "suppress_after_no_strong_round", False)):
        return None
    if bool(certificate_disabled):
        return None
    if not bool(config.get("journey_learning_pricing_enabled", True)):
        return None
    max_rounds = _journey_learning_pricing_max_rounds(config)
    pricing_rounds_used = int(getattr(runtime, "pricing_rounds_used", 0))
    if max_rounds > 0 and pricing_rounds_used >= max_rounds:
        return None
    return runtime


def _maybe_create_journey_learning_runtime(
    data: FutureData,
    config: dict[str, Any],
    logger: FutureLogger,
    *,
    node_id: int,
    depth: int,
) -> _JourneyLearningRuntime | None:
    if not bool(config.get("journey_learning_enabled", False)):
        return None
    checkpoint_path = str(config.get("journey_learning_checkpoint_path", "") or "")
    if not checkpoint_path:
        logger.log(
            "journey_learning",
            node_id=node_id,
            depth=depth,
            status="DISABLED",
            reason="missing_checkpoint_path",
        )
        return None
    try:
        from BPC_future.learning.dual_stabilizer import DualStabilizer, DualStabilizerConfig
        from BPC_future.learning.graph_builder import FutureGraphBuilder

        stabilizer_config = DualStabilizerConfig(
            checkpoint_path=checkpoint_path,
            device=str(config.get("journey_learning_device", "cpu")),
            alpha_init=float(config.get("journey_learning_alpha_init", 0.8)),
            alpha_min_active=float(config.get("journey_learning_alpha_min_active", 0.2)),
            alpha_decay=float(config.get("journey_learning_alpha_decay", 0.05)),
            stagnation_patience=int(config.get("journey_learning_stagnation_patience", 3)),
            stagnation_rel_improve=float(config.get("journey_learning_stagnation_rel_improve", 1.0e-3)),
            disable_on_branch_depth_gt=int(config.get("journey_learning_disable_on_branch_depth_gt", 0)),
            filter_true_rc=_journey_learning_filter_true_rc_enabled(config),
            rc_filter_tol=float(config.get("journey_learning_true_rc_tol", 1.0e-5)),
            debug_checks=bool(config.get("journey_learning_debug_checks", False)),
        )
        cache_key = _journey_learning_cache_key(stabilizer_config)
        cache_enabled = bool(config.get("journey_learning_cache_enabled", True))
        cache_hit = bool(cache_enabled and cache_key in _JOURNEY_LEARNING_STABILIZER_CACHE)
        if cache_hit:
            stabilizer = _JOURNEY_LEARNING_STABILIZER_CACHE[cache_key]
            stabilizer.reset_runtime_state()
        else:
            stabilizer = DualStabilizer(stabilizer_config)
            if cache_enabled:
                _JOURNEY_LEARNING_STABILIZER_CACHE[cache_key] = stabilizer
        if stabilizer.should_disable(branch_depth=int(depth), certificate_mode=False):
            logger.log(
                "journey_learning",
                node_id=node_id,
                depth=depth,
                status="DISABLED",
                reason="branch_depth_disabled",
                checkpoint_path=checkpoint_path,
                cache_hit=cache_hit,
            )
            return None
        graph_builder = FutureGraphBuilder.from_checkpoint(stabilizer.checkpoint, normalize=False)
        graph_data = graph_builder.build_from_future_data(data)
        anchor = stabilizer.predict_anchor(graph_data)
    except Exception as exc:
        if bool(config.get("journey_learning_fail_hard", False)):
            raise
        logger.log(
            "journey_learning",
            node_id=node_id,
            depth=depth,
            status="DISABLED",
            reason="initialization_failed",
            error=repr(exc),
            checkpoint_path=checkpoint_path,
        )
        return None
    anchor_values = list(anchor.values())
    anchor_l1 = sum(abs(float(value)) for value in anchor_values)
    anchor_linf = max((abs(float(value)) for value in anchor_values), default=0.0)
    logger.log(
        "journey_learning",
        node_id=node_id,
        depth=depth,
        status="ENABLED",
        checkpoint_path=checkpoint_path,
        device=str(config.get("journey_learning_device", "cpu")),
        cache_hit=cache_hit,
        cache_enabled=bool(config.get("journey_learning_cache_enabled", True)),
        task_count=len(anchor),
        anchor_l1=round(float(anchor_l1), 9),
        anchor_linf=round(float(anchor_linf), 9),
        alpha=round(float(stabilizer.alpha), 9),
        pricing_max_rounds=_journey_learning_pricing_max_rounds(config),
        true_rc_max_kept_per_round=_journey_learning_true_rc_max_kept_per_round(config),
        true_rc_keep_threshold=round(float(_journey_learning_true_rc_keep_threshold(config)), 9),
        true_rc_fallback_keep_threshold=round(float(_journey_learning_true_rc_fallback_keep_threshold(config)), 9),
        true_rc_fallback_max_kept_per_round=_journey_learning_true_rc_fallback_max_kept_per_round(config),
        stop_after_no_strong_round=bool(config.get("journey_learning_stop_after_no_strong_round", True)),
        min_kept_to_continue=max(1, int(config.get("journey_learning_min_kept_to_continue", 1))),
    )
    return _JourneyLearningRuntime(
        stabilizer=stabilizer,
        anchor=anchor,
        objective_history=[],
        filter_true_rc=bool(stabilizer_config.filter_true_rc),
        true_rc_tol=float(config.get("journey_learning_true_rc_tol", 1.0e-5)),
        true_rc_keep_threshold=_journey_learning_true_rc_keep_threshold(config),
        true_rc_fallback_keep_threshold=_journey_learning_true_rc_fallback_keep_threshold(config),
        true_rc_fallback_max_kept_per_round=_journey_learning_true_rc_fallback_max_kept_per_round(config),
        true_rc_max_kept_per_round=_journey_learning_true_rc_max_kept_per_round(config),
        stop_after_no_strong_round=bool(config.get("journey_learning_stop_after_no_strong_round", True)),
        min_kept_to_continue=max(1, int(config.get("journey_learning_min_kept_to_continue", 1))),
    )


def _journey_learning_cache_key(config: Any) -> tuple[Any, ...]:
    checkpoint_path = Path(str(config.checkpoint_path)).expanduser()
    try:
        checkpoint_key = str(checkpoint_path.resolve())
    except OSError:
        checkpoint_key = str(checkpoint_path)
    return (
        checkpoint_key,
        str(config.device),
        round(float(config.alpha_init), 12),
        round(float(config.alpha_min_active), 12),
        round(float(config.alpha_decay), 12),
        int(config.stagnation_patience),
        round(float(config.stagnation_rel_improve), 12),
        int(config.disable_on_branch_depth_gt),
        bool(config.filter_true_rc),
        round(float(config.rc_filter_tol), 12),
        bool(config.debug_checks),
    )


def _log_journey_learning_dual_trace(
    data: FutureData,
    config: dict[str, Any],
    logger: FutureLogger,
    duals: JourneyDuals,
    *,
    objective: float,
    cg_iter: int,
    node_id: int,
    depth: int,
) -> None:
    if not bool(config.get("journey_learning_dual_trace_enabled", False)):
        return
    if int(depth) > int(config.get("journey_learning_dual_trace_max_depth", 0)):
        return
    logger.log(
        "journey_learning_dual_trace",
        node_id=node_id,
        depth=depth,
        cg_iter=cg_iter,
        instance_name=str(data.name),
        instance_path=str(data.instance_path),
        objective=round(float(objective), 9),
        cover={str(int(task)): round(float(duals.cover.get(int(task), 0.0)), 12) for task in data.tasks},
        fleet_limit=round(float(duals.fleet_limit), 12),
        cut_count=len(duals.cuts or {}),
    )


def _journey_learning_pricing_duals(
    runtime: _JourneyLearningRuntime | None,
    true_duals: JourneyDuals,
    *,
    rmp_objective: float,
    branch_depth: int,
    logger: FutureLogger,
    cg_iter: int,
    node_id: int,
    depth: int,
) -> tuple[JourneyDuals, str, bool]:
    if runtime is None:
        return true_duals, "scip", False
    runtime.objective_history.append(float(rmp_objective))
    alpha = float(
        runtime.stabilizer.update_alpha(
            runtime.objective_history,
            pricing_stats=None,
            branch_depth=int(branch_depth),
        )
    )
    if alpha <= 0.0 or runtime.stabilizer.should_disable(branch_depth=int(branch_depth), certificate_mode=False):
        logger.log(
            "journey_learning_smoothing",
            node_id=node_id,
            depth=depth,
            cg_iter=cg_iter,
            status="DISABLED",
            reason="alpha_zero_or_depth_disabled",
            alpha=round(alpha, 9),
        )
        return true_duals, "scip", False
    runtime.pricing_rounds_used += 1
    smoothed_cover = runtime.stabilizer.smooth_task_duals(
        true_task_duals={int(task): float(value) for task, value in true_duals.cover.items()},
        predicted_anchor=runtime.anchor,
        alpha=alpha,
    )
    l1_delta = sum(
        abs(float(smoothed_cover[int(task)]) - float(true_duals.cover.get(int(task), 0.0)))
        for task in true_duals.cover
    )
    linf_delta = max(
        (
            abs(float(smoothed_cover[int(task)]) - float(true_duals.cover.get(int(task), 0.0)))
            for task in true_duals.cover
        ),
        default=0.0,
    )
    logger.log(
        "journey_learning_smoothing",
        node_id=node_id,
        depth=depth,
        cg_iter=cg_iter,
        status="ENABLED",
        alpha=round(alpha, 9),
        learning_pricing_round=int(runtime.pricing_rounds_used),
        task_count=len(smoothed_cover),
        smoothed_true_l1_delta=round(float(l1_delta), 9),
        smoothed_true_linf_delta=round(float(linf_delta), 9),
    )
    return (
        JourneyDuals(
            cover={int(task): float(value) for task, value in smoothed_cover.items()},
            fleet_limit=float(true_duals.fleet_limit),
            cuts=dict(true_duals.cuts or {}),
        ),
        "learning_smoothed",
        True,
    )


def _journey_learning_true_rc_filter(
    logger: FutureLogger,
    journeys: list[Any],
    *,
    true_duals: JourneyDuals,
    cuts: tuple[FutureCut, ...],
    tol: float,
    keep_threshold: float,
    max_kept: int = 0,
    fallback_keep_threshold: float = 0.0,
    fallback_max_kept: int = 0,
    cg_iter: int,
    node_id: int,
    depth: int,
    pricing_kind: str,
) -> list[Any]:
    kept_with_rc: list[tuple[float, Any]] = []
    fallback_with_rc: list[tuple[float, Any]] = []
    best_true_rc: float | None = None
    effective_threshold = max(abs(float(tol)), abs(float(keep_threshold)))
    fallback_effective_threshold = max(abs(float(tol)), abs(float(fallback_keep_threshold)))
    for journey in journeys:
        true_rc = float(manual_journey_reduced_cost(journey, true_duals, cuts))
        best_true_rc = true_rc if best_true_rc is None else min(float(best_true_rc), true_rc)
        if true_rc < -effective_threshold:
            kept_with_rc.append((true_rc, journey))
        if true_rc < -fallback_effective_threshold:
            fallback_with_rc.append((true_rc, journey))
    strong_before_cap = len(kept_with_rc)
    fallback_before_cap = len(fallback_with_rc)
    max_kept_int = max(0, int(max_kept))
    fallback_max_kept_int = max(0, int(fallback_max_kept))
    fallback_used = False
    if kept_with_rc:
        kept_with_rc.sort(key=lambda item: float(item[0]))
        if max_kept_int > 0 and len(kept_with_rc) > max_kept_int:
            kept_with_rc = kept_with_rc[:max_kept_int]
    elif fallback_max_kept_int > 0 and fallback_with_rc:
        fallback_with_rc.sort(key=lambda item: float(item[0]))
        kept_with_rc = fallback_with_rc[:fallback_max_kept_int]
        fallback_used = True
    kept = [journey for _rc, journey in kept_with_rc]
    kept_rcs = [float(rc) for rc, _journey in kept_with_rc]
    eligible_before_cap = fallback_before_cap if fallback_used else strong_before_cap
    logger.log(
        "journey_learning_true_rc_filter",
        node_id=node_id,
        depth=depth,
        cg_iter=cg_iter,
        pricing_kind=pricing_kind,
        candidate_journeys=len(journeys),
        true_negative_journeys=strong_before_cap,
        fallback_true_negative_journeys=fallback_before_cap,
        fallback_used=bool(fallback_used),
        kept_journeys=len(kept),
        cap_dropped_journeys=max(0, eligible_before_cap - len(kept)),
        true_rc_max_kept_per_round=max_kept_int,
        true_rc_fallback_max_kept_per_round=fallback_max_kept_int,
        rejected_journeys=max(0, len(journeys) - len(kept)),
        true_rc_tol=round(abs(float(tol)), 9),
        true_rc_keep_threshold=round(abs(float(keep_threshold)), 9),
        true_rc_effective_threshold=round(float(effective_threshold), 9),
        true_rc_fallback_keep_threshold=round(abs(float(fallback_keep_threshold)), 9),
        true_rc_fallback_effective_threshold=round(float(fallback_effective_threshold), 9),
        best_true_reduced_cost=None if best_true_rc is None else round(float(best_true_rc), 9),
        kept_best_true_reduced_cost=None if not kept_rcs else round(min(kept_rcs), 9),
        kept_worst_true_reduced_cost=None if not kept_rcs else round(max(kept_rcs), 9),
        kept_mean_true_reduced_cost=None if not kept_rcs else round(sum(kept_rcs) / len(kept_rcs), 9),
    )
    return kept


def _journey_learning_handle_smoothed_pricing_result(
    logger: FutureLogger,
    runtime: _JourneyLearningRuntime,
    *,
    found_negative_column: bool,
    candidate_journeys: int,
    kept_journeys: int,
    added_journeys: int,
    cg_iter: int,
    node_id: int,
    depth: int,
    pricing_kind: str,
) -> None:
    decision = runtime.stabilizer.handle_smoothed_pricing_result(
        found_negative_column=bool(found_negative_column),
        certificate_mode=False,
    )
    weak_learning_round = int(kept_journeys) < max(1, int(runtime.min_kept_to_continue))
    suppress_future_learning = (
        bool(runtime.stop_after_no_strong_round)
        and bool(weak_learning_round)
        and bool(decision.use_true_dual_exact_pricing)
    )
    if bool(runtime.stop_after_no_strong_round) and bool(weak_learning_round) and not bool(decision.use_true_dual_exact_pricing):
        suppress_future_learning = True
    if suppress_future_learning:
        runtime.suppress_after_no_strong_round = True
    logger.log(
        "journey_learning_fallback",
        node_id=node_id,
        depth=depth,
        cg_iter=cg_iter,
        pricing_kind=pricing_kind,
        candidate_journeys=int(candidate_journeys),
        kept_journeys=int(kept_journeys),
        added_journeys=int(added_journeys),
        min_kept_to_continue=int(runtime.min_kept_to_continue),
        use_true_dual_exact_pricing=bool(decision.use_true_dual_exact_pricing),
        suppress_future_learning=bool(suppress_future_learning),
        alpha=round(float(decision.alpha), 9),
        reason=str(decision.reason),
    )


def _journey_exact_pricing_duals(
    scip_duals: JourneyDuals,
    pricing_duals: JourneyDuals,
    pricing_dual_source: str,
    *,
    learning_runtime: Any | None,
    certificate_candidate: bool,
    completion_bound_enabled: bool,
) -> tuple[JourneyDuals, str]:
    """Choose the dual vector for exact pricing without weakening certificates."""
    if learning_runtime is not None:
        return scip_duals, "scip_learning_certificate"
    if bool(certificate_candidate) or bool(completion_bound_enabled):
        return scip_duals, "scip_certificate"
    return pricing_duals, pricing_dual_source


def _select_journey_pricing_duals(
    data: FutureData,
    config: dict[str, Any],
    journey_pool: JourneyPool,
    cuts: tuple[FutureCut, ...],
    fleet_limit: int,
    rmp_objective: float,
    scip_duals: JourneyDuals,
    previous_pricing_duals: JourneyDuals | None,
    logger: FutureLogger,
    cg_iter: int,
    *,
    progress_classification: str = "",
    incumbent: float = math.inf,
    integer_tol: float = 1.0e-6,
    remaining_time: float | None = None,
    certificate_flat_rounds: int | None = None,
) -> tuple[JourneyDuals, str]:
    if not bool(config.get("journey_dual_stabilization_enabled", False)):
        return scip_duals, "scip"
    if cg_iter < int(config.get("journey_dual_stabilization_min_cg_iter", 1)):
        return scip_duals, "scip"
    certificate_candidate = bool(
        math.isfinite(float(incumbent))
        and float(rmp_objective) >= float(incumbent) - float(integer_tol)
    )
    if bool(config.get("journey_dual_stabilization_disable_on_certificate_candidate", False)) and certificate_candidate:
        logger.log(
            "journey_dual_stabilization",
            node_id=0,
            cg_iter=cg_iter,
            status="SKIPPED",
            accepted=False,
            reason="certificate_candidate_uses_scip_dual",
            progress_classification=str(progress_classification),
            certificate_candidate=certificate_candidate,
            certificate_gate_enabled=bool(config.get("journey_dual_stabilization_certificate_candidate_enabled", False)),
            pricing_dual_source="scip",
        )
        return scip_duals, "scip"
    disable_below_remaining = float(config.get("journey_dual_stabilization_disable_below_remaining", 0.0))
    disable_below_max_flat = int(config.get("journey_dual_stabilization_disable_below_remaining_max_flat_rounds", -1))
    flat_gate_passed = (
        disable_below_max_flat < 0
        or certificate_flat_rounds is None
        or int(certificate_flat_rounds) <= disable_below_max_flat
    )
    if (
        certificate_candidate
        and disable_below_remaining > 0.0
        and remaining_time is not None
        and float(remaining_time) < disable_below_remaining
        and flat_gate_passed
    ):
        logger.log(
            "journey_dual_stabilization",
            node_id=0,
            cg_iter=cg_iter,
            status="SKIPPED",
            accepted=False,
            reason="certificate_low_remaining_uses_scip_dual",
            progress_classification=str(progress_classification),
            certificate_candidate=certificate_candidate,
            certificate_gate_enabled=bool(config.get("journey_dual_stabilization_certificate_candidate_enabled", False)),
            remaining=round(float(remaining_time), 6),
            disable_below_remaining=round(float(disable_below_remaining), 6),
            certificate_flat_rounds=None if certificate_flat_rounds is None else int(certificate_flat_rounds),
            disable_below_remaining_max_flat_rounds=disable_below_max_flat,
            pricing_dual_source="scip",
        )
        return scip_duals, "scip"
    if bool(config.get("journey_dual_stabilization_tail_only_enabled", False)):
        allowed = {
            "dual_changed_degenerate",
            "support_changed_objective_flat",
            "stalled_same_dual_support",
        }
        certificate_gate_enabled = bool(
            config.get("journey_dual_stabilization_certificate_candidate_enabled", False)
        )
        if str(progress_classification) not in allowed and not (certificate_gate_enabled and certificate_candidate):
            logger.log(
                "journey_dual_stabilization",
                node_id=0,
                cg_iter=cg_iter,
                status="SKIPPED",
                accepted=False,
                reason="not_tail_degenerate",
                progress_classification=str(progress_classification),
                certificate_candidate=certificate_candidate,
                certificate_gate_enabled=certificate_gate_enabled,
                pricing_dual_source="scip",
            )
            return scip_duals, "scip"
    tolerance = float(config.get("journey_dual_stabilization_tolerance", 1.0e-6))
    reference = previous_pricing_duals if previous_pricing_duals is not None else scip_duals
    cover_upper_bounds: dict[int, float] = {}
    pair_upper_bounds: dict[tuple[int, int], float] = {}
    if bool(config.get("journey_dual_optimal_inequalities_enabled", False)):
        include_pairs = bool(config.get("journey_deep_dual_optimal_inequalities_enabled", False))
        cover_upper_bounds, pair_upper_bounds = _journey_dual_optimal_inequality_bounds(
            data,
            journey_pool.journeys,
            include_pairs=include_pairs,
        )
    result = solve_journey_stabilized_dual(
        data,
        journey_pool.journeys,
        cuts=cuts,
        fleet_limit=fleet_limit,
        objective_value=float(rmp_objective),
        reference=reference,
        mode=str(config.get("journey_dual_stabilization_mode", "l1_reference")),
        slack_cap=float(config.get("journey_dual_stabilization_slack_cap", 1000.0)),
        cover_upper_bounds=cover_upper_bounds,
        pair_upper_bounds=pair_upper_bounds,
        time_limit=float(config.get("journey_dual_stabilization_time_limit", 1.0)),
        tolerance=tolerance,
    )
    pool_min_rc = None
    pool_negative_rc_count = None
    if result.duals is not None:
        pool_min_rc, pool_negative_rc_count = _journey_dual_current_pool_validation(
            journey_pool.journeys,
            result.duals,
            cuts,
            tolerance=max(10.0 * tolerance, 1.0e-6),
        )
    objective_matches = bool(
        result.objective_value is not None
        and abs(float(result.objective_value) - float(rmp_objective)) <= max(10.0 * tolerance, 1.0e-6)
    )
    current_pool_dual_feasible = bool(pool_negative_rc_count is not None and int(pool_negative_rc_count) == 0)
    accepted = bool(result.duals is not None and objective_matches and current_pool_dual_feasible)
    logger.log(
        "journey_dual_stabilization",
        node_id=0,
        cg_iter=cg_iter,
        status=result.status,
        accepted=accepted,
        rmp_objective=round(float(rmp_objective), 9),
        dual_objective=None if result.objective_value is None else round(float(result.objective_value), 9),
        variable_count=result.variable_count,
        constraint_count=result.constraint_count,
        reference="previous" if previous_pricing_duals is not None else "scip",
        mode=str(config.get("journey_dual_stabilization_mode", "l1_reference")),
        tail_only_enabled=bool(config.get("journey_dual_stabilization_tail_only_enabled", False)),
        progress_classification=str(progress_classification),
        certificate_candidate=certificate_candidate,
        certificate_gate_enabled=bool(config.get("journey_dual_stabilization_certificate_candidate_enabled", False)),
        doi_enabled=bool(config.get("journey_dual_optimal_inequalities_enabled", False)),
        doi_cover_bounds=len(cover_upper_bounds),
        ddoi_pair_bounds=len(pair_upper_bounds),
        objective_matches=objective_matches,
        current_pool_dual_feasible=current_pool_dual_feasible,
        current_pool_min_reduced_cost=None if pool_min_rc is None else round(float(pool_min_rc), 9),
        current_pool_negative_reduced_cost_count=pool_negative_rc_count,
        pricing_dual_source="stabilized" if accepted else "scip",
    )
    return (result.duals, "stabilized") if accepted and result.duals is not None else (scip_duals, "scip")


def _journey_dual_current_pool_validation(
    journeys: list[Any],
    duals: JourneyDuals,
    cuts: tuple[FutureCut, ...],
    *,
    tolerance: float,
) -> tuple[float | None, int]:
    min_rc: float | None = None
    negative_count = 0
    for journey in journeys:
        rc = float(manual_journey_reduced_cost(journey, duals, cuts))
        min_rc = rc if min_rc is None else min(min_rc, rc)
        if rc < -float(tolerance):
            negative_count += 1
    return min_rc, negative_count


def _journey_dual_optimal_inequality_bounds(
    data: FutureData,
    journeys: list[Any],
    *,
    include_pairs: bool,
) -> tuple[dict[int, float], dict[tuple[int, int], float]]:
    """Return conservative dual-selection bounds from exact current columns.

    These bounds are used only inside the optional alternative-dual selector.
    If they cut off the current optimal dual face, the selector fails and the
    solver falls back to SCIP's original RMP dual.
    """

    single: dict[int, float] = {}
    pair: dict[tuple[int, int], float] = {}
    for journey in journeys:
        tasks = tuple(sorted(int(task) for task in getattr(journey, "task_set", tuple())))
        if len(tasks) == 1:
            task = int(tasks[0])
            cost = float(getattr(journey, "cost", math.inf))
            single[task] = min(single.get(task, math.inf), cost)
        elif include_pairs and len(tasks) == 2:
            key = (int(tasks[0]), int(tasks[1]))
            cost = float(getattr(journey, "cost", math.inf))
            pair[key] = min(pair.get(key, math.inf), cost)
    return (
        {int(task): float(value) for task, value in single.items() if int(task) in data.tasks and math.isfinite(float(value))},
        {tuple(key): float(value) for key, value in pair.items() if math.isfinite(float(value))},
    )


def _update_journey_fleet_limit(
    data: FutureData,
    logger: FutureLogger,
    current_limit: int,
    incumbent: float,
    incumbent_solution: dict[int, list[Any]],
    cg_iter: int,
    *,
    node_id: int = 0,
    depth: int = 0,
    slack: int = 0,
) -> int:
    if incumbent == math.inf or not incumbent_solution:
        return int(current_limit)
    used = len(incumbent_solution)
    if used <= 0 or used >= int(current_limit):
        return int(current_limit)
    target = min(int(current_limit), int(used) + max(0, int(slack)))
    if target >= int(current_limit):
        return int(current_limit)
    fixed = float(data.fixed_vehicle_cost)
    if fixed <= 1.0e-9:
        return int(current_limit)
    required_nonempty_vehicles = int(target) + 1
    unavoidable = float(
        unavoidable_nonvehicle_cost_lb(
            data,
            min_nonempty_vehicles=required_nonempty_vehicles,
        )
    )
    next_vehicle_lb = float(target + 1) * fixed + unavoidable
    if next_vehicle_lb < float(incumbent) - 1.0e-6:
        return int(current_limit)
    new_limit = max(1, int(target))
    logger.log(
        "journey_fleet_limit_tightened",
        node_id=node_id,
        depth=depth,
        cg_iter=cg_iter,
        old_limit=int(current_limit),
        new_limit=new_limit,
        incumbent=round(float(incumbent), 6),
        incumbent_vehicles=used,
        slack=max(0, int(slack)),
        fixed_vehicle_cost=round(fixed, 6),
        unavoidable_nonvehicle_lb=round(unavoidable, 6),
        next_vehicle_cost_lb=round(next_vehicle_lb, 6),
        reason="incumbent_cost_safe",
    )
    return new_limit


def _journey_fleet_limit_slack(config: dict[str, Any]) -> int:
    return max(
        0,
        int(
            config.get(
                "journey_fleet_limit_slack",
                config.get("incumbent_fleet_upper_slack", 0),
            )
        ),
    )


def _run_journey_pool_incumbent_probe(
    data: FutureData,
    config: dict[str, Any],
    journey_pool: JourneyPool,
    logger: FutureLogger,
    cg_iter: int,
    incumbent: float,
    final_solution: dict[int, list[Any]],
    *,
    fleet_limit: int | None,
    remaining: float,
    node_id: int = 0,
    depth: int = 0,
) -> tuple[float, dict[int, list[Any]]]:
    budget = min(float(config.get("journey_pool_time_limit", 3.0)), max(0.0, float(remaining)))
    if budget <= 1.0e-3:
        return incumbent, final_solution
    pool_mip = solve_journey_pool_master(
        data,
        journey_pool.journeys,
        solve_integer=True,
        time_limit=budget,
        fleet_limit=fleet_limit,
    )
    logger.log(
        "journey_pool_integer_probe",
        node_id=node_id,
        depth=depth,
        cg_iter=cg_iter,
        status=pool_mip.status,
        lp_objective=None if pool_mip.lp_objective is None else round(float(pool_mip.lp_objective), 6),
        mip_objective=None if pool_mip.mip_objective is None else round(float(pool_mip.mip_objective), 6),
        incumbent=None if incumbent == math.inf else round(float(incumbent), 6),
        journeys=len(journey_pool.journeys),
        fleet_limit=fleet_limit,
        time_budget=round(float(budget), 6),
    )
    if pool_mip.mip_objective is not None and pool_mip.mip_objective < incumbent - 1.0e-6:
        incumbent = float(pool_mip.mip_objective)
        final_solution = _journey_assignment(pool_mip.selected_journeys)
        logger.log(
            "incumbent",
            node_id=node_id,
            depth=depth,
            cg_iter=cg_iter,
            objective=round(float(incumbent), 6),
            vehicles=len(final_solution),
            source="journey_pool_integer_probe",
        )
    return incumbent, final_solution


def _should_run_journey_pool_probe(enabled: bool, cg_iter: int, frequency: int) -> bool:
    return bool(enabled) and int(cg_iter) > 0 and int(cg_iter) % max(1, int(frequency)) == 0


def _journey_should_skip_short_exact_pricing(
    config: dict[str, Any],
    *,
    depth: int,
    cg_iter: int,
    certificate_candidate: bool,
    retry_negative_after_no_column_rounds: int,
) -> bool:
    """Return whether to skip the short exact-pricing pass this CG round.

    This is an opt-in cadence control.  It does not certify anything and only
    replaces a repeatedly unproductive short pass with the same true-dual
    pricing oracle using the longer retry-style budget.
    """

    if not bool(config.get("journey_skip_short_exact_after_retry_negative_enabled", False)):
        return False
    if bool(config.get("journey_skip_short_exact_root_only", True)) and int(depth) > 0:
        return False
    if bool(config.get("journey_skip_short_exact_certificate_only", True)) and not bool(certificate_candidate):
        return False
    min_cg_iter = int(config.get("journey_skip_short_exact_min_cg_iter", 2))
    if int(cg_iter) < max(1, int(min_cg_iter)):
        return False
    min_hits = int(config.get("journey_skip_short_exact_min_retry_negative_rounds", 2))
    return int(retry_negative_after_no_column_rounds) >= max(1, int(min_hits))


def _journey_retry_budget_with_completion_reserve(
    config: dict[str, Any],
    *,
    retry_remaining: float,
    min_pricing_time: float,
    retry_min_time: float,
    final_completion_bound_eligible: bool,
) -> tuple[float, float]:
    """Return normal-retry time limit and time reserved for final bound proof.

    The reserve is opt-in and only applies when a final after-retry completion
    bound call can actually be constructed.  Capping a normal retry is
    exact-safe because an incomplete retry still cannot certify anything; it
    only leaves time for another exact pricing attempt.
    """

    retry_budget = max(0.0, float(retry_remaining))
    if not bool(final_completion_bound_eligible):
        return retry_budget, 0.0
    requested_reserve = max(
        0.0,
        float(config.get("journey_certificate_completion_bound_after_retry_reserve_time", 0.0)),
    )
    if requested_reserve <= 0.0:
        return retry_budget, 0.0
    minimum_retry_budget = max(float(min_pricing_time), float(retry_min_time))
    if retry_budget <= requested_reserve + minimum_retry_budget:
        return retry_budget, 0.0
    capped_retry_budget = max(float(minimum_retry_budget), retry_budget - requested_reserve)
    return capped_retry_budget, max(0.0, retry_budget - capped_retry_budget)


def _journey_pre_retry_completion_reserve_time(
    config: dict[str, Any],
    *,
    remaining: float,
    exact_time_limit: float,
    min_pricing_time: float,
    final_completion_bound_eligible: bool,
    exact_completion_bound_enabled: bool,
) -> float:
    """Return time to reserve before the first ordinary exact attempt.

    This is deliberately stricter than the after-retry reserve.  Completion
    Bound is the final judge, so the first Level 2/3 exact-pricing attempt must
    not be shortened in normal runs.  A positive reserve is allowed only when an
    experiment explicitly sets a low remaining-time threshold.
    """

    if not bool(final_completion_bound_eligible) or bool(exact_completion_bound_enabled):
        return 0.0
    requested_reserve = max(
        0.0,
        float(config.get("journey_certificate_completion_bound_pre_retry_reserve_time", 0.0)),
    )
    remaining_threshold = max(
        0.0,
        float(config.get("journey_certificate_completion_bound_pre_retry_reserve_remaining_threshold", 0.0)),
    )
    if requested_reserve <= 0.0 or remaining_threshold <= 0.0:
        return 0.0
    if float(remaining) > float(remaining_threshold):
        return 0.0
    if float(exact_time_limit) <= float(requested_reserve) + float(min_pricing_time):
        return 0.0
    return min(float(requested_reserve), max(0.0, float(exact_time_limit) - float(min_pricing_time)))


def _journey_completion_bound_final_probe_needed(
    config: dict[str, Any],
    pricing: Any,
    *,
    added_columns: int | None = None,
) -> bool:
    """Return whether Level 4 completion-bound proof should run.

    The completion-bound oracle is a final certificate probe.  It is not used
    after an exhausted no-negative pricing call, because that call is already a
    valid certificate.  It is used only when ordinary retry pricing failed to
    prove anything and produced no new column for the RMP.
    """

    if not bool(config.get("journey_certificate_completion_bound_after_retry_enabled", False)):
        return False
    if bool(getattr(pricing, "exhausted", False)):
        return False
    if added_columns is not None:
        return int(added_columns) <= 0
    return not bool(getattr(pricing, "journeys", None))


def _journey_retry_force_ng_config(
    config: dict[str, Any],
    pricing_config: JourneyPricingConfig,
    *,
    depth: int,
) -> tuple[JourneyPricingConfig, bool]:
    """Optionally force NG-DSSR on an incomplete true-dual retry.

    The first short exact-pricing call already failed to certify the node.  This
    opt-in hook changes only the follow-up retry oracle, still under true RMP
    duals, so it cannot certify anything by itself unless the normal exact-safe
    NG certificate flags are explicitly enabled elsewhere.
    """

    if not bool(config.get("journey_retry_incomplete_no_column_force_ng_enabled", False)):
        return pricing_config, False
    if bool(config.get("journey_retry_incomplete_no_column_force_ng_root_only", True)) and int(depth) > 0:
        return pricing_config, False

    updates: dict[str, Any] = {
        "direct_journey_label_ng_dssr_enabled": True,
        "direct_journey_label_ng_exact_probe_enabled": bool(
            config.get("journey_retry_incomplete_no_column_force_ng_exact_probe_enabled", True)
        ),
    }
    if "journey_retry_incomplete_no_column_force_ng_max_labels" in config:
        updates["direct_journey_label_ng_max_labels"] = int(
            config["journey_retry_incomplete_no_column_force_ng_max_labels"]
        )
    if "journey_retry_incomplete_no_column_force_ng_min_negative_journeys" in config:
        updates["direct_journey_label_ng_min_negative_journeys"] = int(
            config["journey_retry_incomplete_no_column_force_ng_min_negative_journeys"]
        )
    if "journey_retry_incomplete_no_column_force_ng_probe_time_limit" in config:
        updates["direct_journey_label_ng_probe_time_limit"] = float(
            config["journey_retry_incomplete_no_column_force_ng_probe_time_limit"]
        )
    if "journey_retry_incomplete_no_column_force_ng_probe_min_journeys_for_early_return" in config:
        updates["direct_journey_label_ng_probe_min_journeys_for_early_return"] = int(
            config["journey_retry_incomplete_no_column_force_ng_probe_min_journeys_for_early_return"]
        )
    return replace(pricing_config, **updates), True


def _journey_certificate_pricing_config(
    config: dict[str, Any],
    pricing_config: JourneyPricingConfig,
    *,
    certificate_candidate: bool,
    certificate_flat_rounds: int,
    certificate_no_column_rounds: int | None = None,
    depth: int = 0,
    completion_bound_phase: str = "standard",
) -> tuple[JourneyPricingConfig, dict[str, Any]]:
    """Adjust exact-pricing search cadence near a candidate certificate.

    These adjustments only control how quickly pricing returns true negative
    columns.  They never turn an incomplete pricing run into a certificate.
    """

    completion_bound_exact_proof_min_depth = int(
        config.get("journey_certificate_completion_bound_exact_proof_min_depth", 1)
    )
    completion_bound_exact_proof_min_incomplete_rounds = int(
        config.get(
            "journey_certificate_completion_bound_exact_proof_min_incomplete_rounds",
            config.get("journey_certificate_completion_bound_exact_proof_min_no_column_rounds", 1),
        )
    )
    exact_proof_incomplete_rounds = 0 if certificate_no_column_rounds is None else int(certificate_no_column_rounds)
    completion_bound_exact_proof = (
        bool(config.get("journey_certificate_completion_bound_exact_proof_enabled", False))
        and int(depth) >= max(0, completion_bound_exact_proof_min_depth)
        and int(exact_proof_incomplete_rounds) >= max(0, completion_bound_exact_proof_min_incomplete_rounds)
    )
    if not bool(certificate_candidate) and not completion_bound_exact_proof:
        return pricing_config, {}
    updated = pricing_config
    mode: dict[str, Any] = {}
    round_metric = str(config.get("journey_certificate_proof_round_metric", "flat"))
    proof_rounds = (
        int(certificate_no_column_rounds)
        if round_metric == "no_column" and certificate_no_column_rounds is not None
        else int(certificate_flat_rounds)
    )
    fast_negative_min_rounds = int(
        config.get(
            "journey_certificate_fast_negative_return_min_proof_rounds",
            config.get("journey_certificate_fast_negative_return_min_flat_rounds", 0),
        )
    )
    if (
        bool(certificate_candidate)
        and bool(config.get("journey_certificate_fast_negative_return_enabled", False))
        and proof_rounds >= max(0, fast_negative_min_rounds)
    ):
        min_count = max(1, int(config.get("journey_certificate_fast_negative_return_min_count", 1)))
        updated = replace(
            updated,
            early_return_negative=True,
            early_return_negative_min_count=min_count,
            streaming_min_negative_batch=min_count,
        )
        mode["fast_negative_return"] = True
        mode["fast_negative_min_rounds"] = fast_negative_min_rounds
    full_scan_after = int(config.get("journey_certificate_full_scan_after_flat_rounds", 0))
    if bool(certificate_candidate) and full_scan_after > 0 and proof_rounds >= max(1, full_scan_after):
        updated = replace(
            updated,
            streaming_pricing_enabled=False,
            early_return_negative=False,
            profile_generation_time_fraction=1.0,
            max_sequences=int(config.get("journey_certificate_full_scan_max_sequences", updated.max_sequences)),
            max_timed_evaluations=int(
                config.get("journey_certificate_full_scan_max_timed_evaluations", updated.max_timed_evaluations)
            ),
        )
        mode["full_scan"] = True
        mode["full_scan_after"] = full_scan_after
        mode["proof_rounds"] = proof_rounds
        mode["proof_round_metric"] = round_metric
    completion_bound_final_probe_only = bool(
        config.get("journey_certificate_completion_bound_final_probe_only", True)
    )
    completion_bound_is_final_probe = str(completion_bound_phase) == "after_retry"
    completion_bound_allowed = (
        bool(config.get("journey_certificate_completion_bound_enabled", False))
        and (bool(certificate_candidate) or completion_bound_exact_proof)
        and (int(depth) <= 0 or not bool(config.get("journey_certificate_completion_bound_root_only", True)))
        and (not completion_bound_final_probe_only or completion_bound_is_final_probe)
        and (
            not bool(config.get("journey_certificate_completion_bound_after_retry_enabled", False))
            or completion_bound_is_final_probe
        )
        and proof_rounds
        >= max(0, int(config.get("journey_certificate_completion_bound_min_flat_rounds", 0)))
    )
    if completion_bound_allowed:
        pricing_energy_bucket_value = config.get(
            "journey_pricing_direct_journey_label_completion_bound_energy_buckets",
            None,
        )
        default_energy_buckets = (
            int(pricing_energy_bucket_value)
            if pricing_energy_bucket_value is not None
            else 10
        )
        updated = replace(
            updated,
            direct_journey_label_pricing_enabled=True,
            direct_journey_label_completion_bound_enabled=True,
            direct_journey_label_completion_bound_time_buckets=int(
                config.get(
                    "journey_certificate_completion_bound_time_buckets",
                    config.get(
                        "journey_pricing_direct_journey_label_completion_bound_time_buckets",
                        updated.direct_journey_label_completion_bound_time_buckets,
                    ),
                )
            ),
            direct_journey_label_completion_bound_energy_buckets=int(
                config.get(
                    "journey_certificate_completion_bound_energy_buckets",
                    default_energy_buckets,
                )
            ),
            direct_journey_label_completion_bound_partial_pruning_enabled=bool(
                config.get(
                    "journey_certificate_completion_bound_partial_pruning_enabled",
                    config.get(
                        "journey_pricing_direct_journey_label_completion_bound_partial_pruning_enabled",
                        updated.direct_journey_label_completion_bound_partial_pruning_enabled,
                    ),
                )
            ),
            direct_journey_label_completion_bound_audit_enabled=bool(
                config.get(
                    "journey_certificate_completion_bound_audit_enabled",
                    config.get(
                        "journey_pricing_direct_journey_label_completion_bound_audit_enabled",
                        updated.direct_journey_label_completion_bound_audit_enabled,
                    ),
                )
            ),
            direct_journey_label_completion_bound_unique_task_helper_enabled=bool(
                config.get(
                    "journey_certificate_completion_bound_unique_task_helper_enabled",
                    config.get(
                        "journey_pricing_direct_journey_label_completion_bound_unique_task_helper_enabled",
                        updated.direct_journey_label_completion_bound_unique_task_helper_enabled,
                    ),
                )
            ),
            direct_journey_label_completion_bound_unique_route_helper_enabled=bool(
                config.get(
                    "journey_certificate_completion_bound_unique_route_helper_enabled",
                    config.get(
                        "journey_pricing_direct_journey_label_completion_bound_unique_route_helper_enabled",
                        updated.direct_journey_label_completion_bound_unique_route_helper_enabled,
                    ),
                )
            ),
        )
        mode["completion_bound"] = True
        mode["completion_bound_final_probe_only"] = bool(completion_bound_final_probe_only)
        if not bool(certificate_candidate) and completion_bound_exact_proof:
            mode["completion_bound_exact_proof"] = True
            mode["completion_bound_exact_proof_min_depth"] = max(0, completion_bound_exact_proof_min_depth)
            mode["completion_bound_exact_proof_min_incomplete_rounds"] = max(
                0,
                completion_bound_exact_proof_min_incomplete_rounds,
            )
        mode["completion_bound_energy_buckets"] = int(updated.direct_journey_label_completion_bound_energy_buckets)
        mode["completion_bound_audit"] = bool(updated.direct_journey_label_completion_bound_audit_enabled)
        mode["completion_bound_unique_task_helper"] = bool(
            updated.direct_journey_label_completion_bound_unique_task_helper_enabled
        )
        mode["completion_bound_unique_route_helper"] = bool(
            updated.direct_journey_label_completion_bound_unique_route_helper_enabled
        )
    return updated, mode


def _journey_node_depth_pricing_config(
    config: dict[str, Any],
    pricing_config: JourneyPricingConfig,
    depth: int,
) -> JourneyPricingConfig:
    if int(depth) <= 0:
        return pricing_config
    updated = pricing_config
    if bool(updated.direct_journey_label_completion_bound_enabled) and bool(
        config.get("journey_certificate_completion_bound_root_only", True)
    ):
        updated = replace(updated, direct_journey_label_completion_bound_enabled=False)
    if "journey_branch_pricing_time_limit" in config:
        updated = replace(
            updated,
            time_limit=min(float(updated.time_limit), float(config.get("journey_branch_pricing_time_limit", updated.time_limit))),
        )
    if "journey_branch_pricing_max_returned_journeys" in config:
        updated = replace(updated, max_returned_journeys=int(config["journey_branch_pricing_max_returned_journeys"]))
    if "journey_branch_pricing_streaming_min_negative_batch" in config:
        value = int(config["journey_branch_pricing_streaming_min_negative_batch"])
        updated = replace(updated, streaming_min_negative_batch=value)
    if "journey_branch_pricing_streaming_min_returned_journeys" in config:
        value = int(config["journey_branch_pricing_streaming_min_returned_journeys"])
        updated = replace(updated, streaming_min_returned_journeys=value)
    if "journey_branch_pricing_streaming_partial_return_after_time" in config:
        updated = replace(
            updated,
            streaming_partial_return_after_time=float(config["journey_branch_pricing_streaming_partial_return_after_time"]),
        )
    if "journey_branch_pricing_streaming_partial_return_min_journeys" in config:
        updated = replace(
            updated,
            streaming_partial_return_min_journeys=int(config["journey_branch_pricing_streaming_partial_return_min_journeys"]),
        )
    if "journey_branch_pricing_early_return_negative_min_count" in config:
        updated = replace(
            updated,
            early_return_negative_min_count=int(config["journey_branch_pricing_early_return_negative_min_count"]),
        )
    if "journey_branch_pricing_direct_journey_label_ng_dssr_enabled" in config:
        updated = replace(
            updated,
            direct_journey_label_ng_dssr_enabled=bool(
                config["journey_branch_pricing_direct_journey_label_ng_dssr_enabled"]
            ),
        )
    if "journey_branch_pricing_direct_journey_label_ng_probe_time_limit" in config:
        updated = replace(
            updated,
            direct_journey_label_ng_probe_time_limit=float(
                config["journey_branch_pricing_direct_journey_label_ng_probe_time_limit"]
            ),
        )
    if "journey_branch_pricing_direct_journey_label_ng_probe_min_journeys_for_early_return" in config:
        updated = replace(
            updated,
            direct_journey_label_ng_probe_min_journeys_for_early_return=int(
                config["journey_branch_pricing_direct_journey_label_ng_probe_min_journeys_for_early_return"]
            ),
        )
    if "journey_branch_pricing_selection_mode" in config:
        updated = replace(updated, journey_selection_mode=str(config["journey_branch_pricing_selection_mode"]))
    if "journey_branch_pricing_profile_labeling_physical_catalog_share_across_branches_enabled" in config:
        updated = replace(
            updated,
            profile_labeling_physical_catalog_share_across_branches_enabled=bool(
                config["journey_branch_pricing_profile_labeling_physical_catalog_share_across_branches_enabled"]
            ),
        )
    return updated


def _separate_journey_subset_row_cuts(
    data: FutureData,
    config: dict[str, Any],
    solution: Any,
    cuts: list[FutureCut],
    cut_keys: set[tuple],
    logger: FutureLogger,
    cg_iter: int,
    *,
    node_id: int = 0,
    depth: int = 0,
) -> int:
    if not bool(config.get("journey_dynamic_subset_row_cuts_enabled", False)):
        return 0
    if cg_iter > int(config.get("journey_dynamic_subset_row_max_rounds", 1)):
        return 0
    budget = int(config.get("journey_dynamic_subset_row_cut_budget", config.get("subset_row_candidate_budget", 100)))
    max_added = int(config.get("journey_dynamic_subset_row_max_added", config.get("subset_row_max_cuts_per_round", 20)))
    max_subset = int(config.get("journey_dynamic_subset_row_max_subset_size", config.get("subset_row_max_subset_size", 6)))
    min_violation = float(config.get("journey_dynamic_subset_row_min_violation", config.get("subset_row_min_violation", 1.0e-6)))
    if budget <= 0 or max_added <= 0:
        return 0
    active = [(journey, float(value)) for journey, value in solution.journey_values if float(value) > 1.0e-9]
    if not active:
        return 0
    task_mass = {
        int(task): sum(value for journey, value in active if int(task) in journey.task_set)
        for task in data.tasks
    }
    ordered_tasks = sorted(data.tasks, key=lambda task: (-task_mass[int(task)], int(task)))
    candidates: list[tuple[float, SubsetRowCut]] = []
    generated = 0
    for k, sizes in ((2, (3, 4, 5)), (3, (4, 5, 6))):
        for size in sizes:
            if size > max_subset or size > len(data.tasks):
                continue
            for tasks in itertools.combinations(ordered_tasks, size):
                generated += 1
                if generated > budget:
                    break
                cut = SubsetRowCut(tuple(int(task) for task in tasks), k)
                if cut.key in cut_keys:
                    continue
                activity = 0.0
                cut_tasks = set(cut.tasks)
                for journey, value in active:
                    coeff = len(cut_tasks.intersection(journey.task_set)) // int(k)
                    if coeff:
                        activity += float(value) * float(coeff)
                violation = activity - float(cut.rhs)
                if violation > min_violation:
                    candidates.append((violation, cut))
            if generated > budget:
                break
        if generated > budget:
            break
    candidates.sort(key=lambda item: (-item[0], len(item[1].tasks), item[1].k, item[1].tasks))
    added = 0
    for violation, cut in candidates[:max_added]:
        if cut.key in cut_keys:
            continue
        cuts.append(cut)
        cut_keys.add(cut.key)
        added += 1
        logger.log(
            "journey_cut_added",
            node_id=node_id,
            depth=depth,
            cg_iter=cg_iter,
            kind=cut.kind,
            tasks=list(cut.tasks),
            k=int(cut.k),
            rhs=cut.rhs,
            violation=round(float(violation), 9),
            source="dynamic_subset_row",
        )
    logger.log(
        "journey_cut_separation",
        node_id=node_id,
        depth=depth,
        cg_iter=cg_iter,
        generated=generated,
        violated=len(candidates),
        added=added,
        active_cuts=len(cuts),
        separator="dynamic_subset_row",
    )
    return added


def _journey_static_cuts(data: FutureData, config: dict[str, Any]) -> list[FutureCut]:
    cuts: list[FutureCut] = []
    if not bool(config.get("cuts_enabled", True)):
        return cuts
    if bool(config.get("fleet_lower_bound_cut_enabled", True)):
        cuts.append(FleetLowerBoundCut(fleet_lower_bound(data)))
    if not bool(config.get("static_subset_row_cuts_enabled", False)):
        return cuts
    budget = int(config.get("static_subset_row_cut_budget", 0))
    if budget <= 0:
        return cuts
    max_subset = int(config.get("static_subset_row_max_subset_size", 5))
    for k, sizes in ((2, (3, 4, 5)), (3, (4, 5, 6))):
        for size in sizes:
            if size > max_subset or size > len(data.tasks):
                continue
            for tasks in itertools.combinations(data.tasks, size):
                cuts.append(SubsetRowCut(tuple(int(task) for task in tasks), k))
                if _journey_cut_count(cuts, "subset_row") >= budget:
                    return cuts
    return cuts


def _log_journey_static_cut_diagnostics(
    logger: FutureLogger,
    config: dict[str, Any],
    cuts: list[FutureCut],
    *,
    node_id: int,
    depth: int,
) -> None:
    unsupported: list[str] = []
    if bool(config.get("cuts_enabled", True)) and bool(config.get("sortie_lower_bound_cut_enabled", False)):
        unsupported.append("sortie_lower_bound")
    logger.log(
        "journey_static_cuts",
        node_id=node_id,
        depth=depth,
        active_cuts=len(cuts),
        fleet_lower_bound_cuts=_journey_cut_count(cuts, "fleet_lower_bound"),
        subset_row_cuts=_journey_cut_count(cuts, "subset_row"),
        unsupported_config_cuts=unsupported,
        unsupported_reason=(
            "sortie_lower_bound depends on sortie count and is disabled in journey mode until task-set dominance is lifted"
            if unsupported
            else ""
        ),
    )


def _journey_cut_count(cuts: list[FutureCut] | tuple[FutureCut, ...], kind: str) -> int:
    return sum(1 for cut in cuts if getattr(cut, "kind", "") == str(kind))


def _journey_pricing_config(
    data: FutureData,
    config: dict[str, Any],
    bucket: float,
    start_step: float,
    eps: float,
    remaining: float,
    *,
    heuristic: bool,
    cg_iter: int = 1,
) -> JourneyPricingConfig:
    prefix = "journey_heuristic" if heuristic else "journey_pricing"
    exact_time_default = config.get("exact_pricing_time_limit", 30.0)
    label_enabled = bool(
        config.get(
            f"{prefix}_profile_labeling_enabled",
            config.get("journey_pricing_profile_labeling_enabled", False),
        )
    )
    label_min_cg = int(
        config.get(
            f"{prefix}_profile_labeling_min_cg_iter",
            config.get("journey_pricing_profile_labeling_min_cg_iter", 1),
        )
    )
    if int(cg_iter) < max(1, int(label_min_cg)):
        label_enabled = False
    direct_enabled = bool(
        config.get(
            f"{prefix}_direct_journey_label_pricing_enabled",
            config.get(
                f"{prefix}_direct_label_enabled",
                config.get(
                    "journey_pricing_direct_journey_label_pricing_enabled",
                    config.get("journey_pricing_direct_label_enabled", False),
                ),
            ),
        )
    )
    direct_min_cg = int(
        config.get(
            f"{prefix}_direct_journey_label_min_cg_iter",
            config.get("journey_pricing_direct_journey_label_min_cg_iter", 1),
        )
    )
    if int(cg_iter) < max(1, int(direct_min_cg)):
        direct_enabled = False
    ng_dssr_enabled = bool(
        config.get(
            f"{prefix}_direct_journey_label_ng_dssr_enabled",
            config.get("journey_pricing_direct_journey_label_ng_dssr_enabled", False),
        )
    )
    ng_min_cg = int(
        config.get(
            f"{prefix}_direct_journey_label_ng_min_cg_iter",
            config.get("journey_pricing_direct_journey_label_ng_min_cg_iter", direct_min_cg),
        )
    )
    if int(cg_iter) < max(1, int(ng_min_cg)):
        ng_dssr_enabled = False
    ng_disable_remaining = float(
        config.get(
            f"{prefix}_direct_journey_label_ng_disable_below_remaining",
            config.get("journey_pricing_direct_journey_label_ng_disable_below_remaining", 0.0),
        )
    )
    ng_disable_exact_enabled = bool(
        config.get(
            f"{prefix}_direct_journey_label_ng_disable_below_remaining_exact_enabled",
            config.get("journey_pricing_direct_journey_label_ng_disable_below_remaining_exact_enabled", False),
        )
    )
    # 软门控：剩余时间门槛默认只影响 heuristic/candidate 阶段。
    # true-dual exact/certificate pricing 不应因为接近时限自动退回 raw DP。
    if (
        ng_disable_remaining > 0.0
        and float(remaining) < ng_disable_remaining
        and (bool(heuristic) or bool(ng_disable_exact_enabled))
    ):
        ng_dssr_enabled = False
    max_returned = int(
        config.get(
            f"{prefix}_max_returned_journeys",
            config.get("journey_pricing_max_returned_journeys", 1 if heuristic else 8),
        )
    )
    late_max_returned = int(
        config.get(
            f"{prefix}_late_max_returned_journeys",
            config.get("journey_pricing_late_max_returned_journeys", 0),
        )
    )
    late_min_cg = int(
        config.get(
            f"{prefix}_late_max_returned_min_cg_iter",
            config.get("journey_pricing_late_max_returned_min_cg_iter", 3),
        )
    )
    if late_max_returned > 0 and int(cg_iter) >= max(1, late_min_cg):
        max_returned = max(max_returned, late_max_returned)
    streaming_enabled = bool(
        config.get(
            f"{prefix}_streaming_pricing_enabled",
            config.get("journey_pricing_streaming_enabled", False),
        )
    )
    streaming_min_cg = int(
        config.get(
            f"{prefix}_streaming_min_cg_iter",
            config.get("journey_pricing_streaming_min_cg_iter", 1),
        )
    )
    if int(cg_iter) < max(1, int(streaming_min_cg)):
        streaming_enabled = False
    return JourneyPricingConfig(
        time_bucket_size=bucket,
        max_tasks_per_trip=int(config.get("max_tasks_per_trip", 6)),
        max_sequences=int(config.get(f"{prefix}_max_sequences", config.get("exact_max_sequences", 0))),
        max_timed_evaluations=int(config.get(f"{prefix}_max_timed_evaluations", config.get("exact_max_timed_evaluations", 0))),
        time_limit=min(float(remaining), float(config.get(f"{prefix}_time_limit", config.get("journey_pricing_time_limit", exact_time_default)))),
        start_time_step=start_step,
        path_dominance_enabled=bool(config.get(f"{prefix}_path_dominance_enabled", config.get("journey_pricing_path_dominance_enabled", config.get("exact_path_dominance_enabled", True)))),
        start_optimization_enabled=bool(config.get(f"{prefix}_start_optimization_enabled", config.get("journey_pricing_start_optimization_enabled", config.get("exact_start_optimization_enabled", True)))),
        max_path_combinations_per_sequence=int(config.get(f"{prefix}_max_path_combinations_per_sequence", config.get("journey_pricing_max_path_combinations_per_sequence", config.get("exact_max_path_combinations_per_sequence", 0)))),
        max_candidate_trips=int(config.get(f"{prefix}_max_candidate_trips", config.get("journey_pricing_max_candidate_trips", 3000))),
        max_dp_states=int(config.get(f"{prefix}_max_dp_states", config.get("journey_pricing_max_dp_states", 200000))),
        allow_partial_negative=bool(heuristic),
        direct_journey_label_pricing_enabled=direct_enabled,
        direct_journey_label_early_return_negative=bool(
            config.get(
                f"{prefix}_direct_journey_label_early_return_negative",
                config.get("journey_pricing_direct_journey_label_early_return_negative", True),
            )
        ),
        direct_journey_label_next_sortie_cache_enabled=bool(
            config.get(
                f"{prefix}_direct_journey_label_next_sortie_cache_enabled",
                config.get("journey_pricing_direct_journey_label_next_sortie_cache_enabled", True),
            )
        ),
        direct_journey_label_task_set_bound_pruning_enabled=bool(
            config.get(
                f"{prefix}_direct_journey_label_task_set_bound_pruning_enabled",
                config.get("journey_pricing_direct_journey_label_task_set_bound_pruning_enabled", True),
            )
        ),
        direct_journey_label_completion_bound_enabled=bool(
            config.get(
                f"{prefix}_direct_journey_label_completion_bound_enabled",
                config.get("journey_pricing_direct_journey_label_completion_bound_enabled", False),
            )
        ),
        direct_journey_label_completion_bound_time_buckets=int(
            config.get(
                f"{prefix}_direct_journey_label_completion_bound_time_buckets",
                config.get("journey_pricing_direct_journey_label_completion_bound_time_buckets", 10),
            )
        ),
        direct_journey_label_completion_bound_energy_buckets=int(
            config.get(
                f"{prefix}_direct_journey_label_completion_bound_energy_buckets",
                config.get("journey_pricing_direct_journey_label_completion_bound_energy_buckets", 0),
            )
        ),
        direct_journey_label_completion_bound_partial_pruning_enabled=bool(
            config.get(
                f"{prefix}_direct_journey_label_completion_bound_partial_pruning_enabled",
                config.get("journey_pricing_direct_journey_label_completion_bound_partial_pruning_enabled", True),
            )
        ),
        direct_journey_label_completion_bound_audit_enabled=bool(
            config.get(
                f"{prefix}_direct_journey_label_completion_bound_audit_enabled",
                config.get("journey_pricing_direct_journey_label_completion_bound_audit_enabled", False),
            )
        ),
        direct_journey_label_completion_bound_unique_task_helper_enabled=bool(
            config.get(
                f"{prefix}_direct_journey_label_completion_bound_unique_task_helper_enabled",
                config.get("journey_pricing_direct_journey_label_completion_bound_unique_task_helper_enabled", False),
            )
        ),
        direct_journey_label_completion_bound_unique_route_helper_enabled=bool(
            config.get(
                f"{prefix}_direct_journey_label_completion_bound_unique_route_helper_enabled",
                config.get("journey_pricing_direct_journey_label_completion_bound_unique_route_helper_enabled", False),
            )
        ),
        direct_journey_label_ng_dssr_enabled=ng_dssr_enabled,
        direct_journey_label_ng_memory_size=int(
            config.get(
                f"{prefix}_direct_journey_label_ng_memory_size",
                config.get("journey_pricing_direct_journey_label_ng_memory_size", 8),
            )
        ),
        direct_journey_label_dssr_initial_memory_size=int(
            config.get(
                f"{prefix}_direct_journey_label_dssr_initial_memory_size",
                config.get("journey_pricing_direct_journey_label_dssr_initial_memory_size", 0),
            )
        ),
        direct_journey_label_dssr_max_iterations=int(
            config.get(
                f"{prefix}_direct_journey_label_dssr_max_iterations",
                config.get("journey_pricing_direct_journey_label_dssr_max_iterations", 4),
            )
        ),
        direct_journey_label_dssr_memory_growth=int(
            config.get(
                f"{prefix}_direct_journey_label_dssr_memory_growth",
                config.get("journey_pricing_direct_journey_label_dssr_memory_growth", 4),
            )
        ),
        direct_journey_label_ng_max_labels=int(
            config.get(
                f"{prefix}_direct_journey_label_ng_max_labels",
                config.get("journey_pricing_direct_journey_label_ng_max_labels", 200000),
            )
        ),
        direct_journey_label_ng_min_negative_journeys=int(
            config.get(
                f"{prefix}_direct_journey_label_ng_min_negative_journeys",
                config.get("journey_pricing_direct_journey_label_ng_min_negative_journeys", 1),
            )
        ),
        direct_journey_label_ng_probe_time_limit=float(
            config.get(
                f"{prefix}_direct_journey_label_ng_probe_time_limit",
                config.get("journey_pricing_direct_journey_label_ng_probe_time_limit", 0.0),
            )
        ),
        direct_journey_label_ng_probe_min_journeys_for_early_return=int(
            config.get(
                f"{prefix}_direct_journey_label_ng_probe_min_journeys_for_early_return",
                config.get("journey_pricing_direct_journey_label_ng_probe_min_journeys_for_early_return", 1),
            )
        ),
        direct_journey_label_ng_probe_certificate_enabled=bool(
            config.get(
                f"{prefix}_direct_journey_label_ng_probe_certificate_enabled",
                config.get("journey_pricing_direct_journey_label_ng_probe_certificate_enabled", False),
            )
        ),
        direct_journey_label_ng_dominance_enabled=bool(
            config.get(
                f"{prefix}_direct_journey_label_ng_dominance_enabled",
                config.get("journey_pricing_direct_journey_label_ng_dominance_enabled", True),
            )
        ),
        direct_journey_label_ng_sequence_key_enabled=bool(
            config.get(
                f"{prefix}_direct_journey_label_ng_sequence_key_enabled",
                config.get("journey_pricing_direct_journey_label_ng_sequence_key_enabled", True),
            )
        ),
        direct_journey_label_ng_visit_mask_dominance_enabled=bool(
            config.get(
                f"{prefix}_direct_journey_label_ng_visit_mask_dominance_enabled",
                config.get("journey_pricing_direct_journey_label_ng_visit_mask_dominance_enabled", False),
            )
        ),
        direct_journey_label_ng_reset_memory_between_sorties_enabled=bool(
            config.get(
                f"{prefix}_direct_journey_label_ng_reset_memory_between_sorties_enabled",
                config.get("journey_pricing_direct_journey_label_ng_reset_memory_between_sorties_enabled", False),
            )
        ),
        direct_journey_label_ng_certificate_enabled=bool(
            config.get(
                f"{prefix}_direct_journey_label_ng_certificate_enabled",
                config.get("journey_pricing_direct_journey_label_ng_certificate_enabled", False),
            )
        ),
        direct_journey_label_ng_exact_probe_enabled=bool(
            config.get(
                f"{prefix}_direct_journey_label_ng_exact_probe_enabled",
                config.get("journey_pricing_direct_journey_label_ng_exact_probe_enabled", False),
            )
        ),
        profile_generation_time_fraction=float(
            config.get(
                f"{prefix}_profile_generation_time_fraction",
                config.get("journey_pricing_profile_generation_time_fraction", 0.75),
            )
        ),
        profile_labeling_enabled=label_enabled,
        profile_labeling_best_first_enabled=bool(
            config.get(
                f"{prefix}_profile_labeling_best_first_enabled",
                config.get("journey_pricing_profile_labeling_best_first_enabled", True),
            )
        ),
        profile_labeling_resume_enabled=bool(
            config.get(
                f"{prefix}_profile_labeling_resume_enabled",
                config.get("journey_pricing_profile_labeling_resume_enabled", False),
            )
        ),
        profile_labeling_physical_catalog_resume_enabled=bool(
            config.get(
                f"{prefix}_profile_labeling_physical_catalog_resume_enabled",
                config.get("journey_pricing_profile_labeling_physical_catalog_resume_enabled", False),
            )
        ),
        profile_labeling_physical_catalog_share_across_branches_enabled=bool(
            config.get(
                f"{prefix}_profile_labeling_physical_catalog_share_across_branches_enabled",
                config.get(
                    "journey_pricing_profile_labeling_physical_catalog_share_across_branches_enabled",
                    False,
                ),
            )
        ),
        profile_labeling_task_set_superset_pruning_enabled=bool(
            config.get(
                f"{prefix}_profile_labeling_task_set_superset_pruning_enabled",
                config.get("journey_pricing_profile_labeling_task_set_superset_pruning_enabled", False),
            )
        ),
        profile_cross_dominance_enabled=bool(
            config.get(
                f"{prefix}_profile_cross_dominance_enabled",
                config.get("journey_pricing_profile_cross_dominance_enabled", True),
            )
        ),
        max_returned_journeys=max_returned,
        duplicate_retry_factor=int(
            config.get(
                f"{prefix}_duplicate_retry_factor",
                config.get("journey_pricing_duplicate_retry_factor", 4),
            )
        ),
        early_return_negative=bool(
            config.get(
                f"{prefix}_early_return_negative",
                config.get("journey_pricing_early_return_negative", False),
            )
        ),
        early_return_negative_min_count=int(
            config.get(
                f"{prefix}_early_return_negative_min_count",
                config.get("journey_pricing_early_return_negative_min_count", 1),
            )
        ),
        early_return_unique_masks_enabled=bool(
            config.get(
                f"{prefix}_early_return_unique_masks_enabled",
                config.get("journey_pricing_early_return_unique_masks_enabled", False),
            )
        ),
        streaming_pricing_enabled=streaming_enabled,
        streaming_profile_batch_size=int(
            config.get(
                f"{prefix}_streaming_profile_batch_size",
                config.get("journey_pricing_streaming_profile_batch_size", 5000),
            )
        ),
        streaming_min_negative_batch=int(
            config.get(
                f"{prefix}_streaming_min_negative_batch",
                config.get("journey_pricing_streaming_min_negative_batch", 1),
            )
        ),
        streaming_min_returned_journeys=int(
            config.get(
                f"{prefix}_streaming_min_returned_journeys",
                config.get("journey_pricing_streaming_min_returned_journeys", 1),
            )
        ),
        streaming_partial_return_after_time=float(
            config.get(
                f"{prefix}_streaming_partial_return_after_time",
                config.get("journey_pricing_streaming_partial_return_after_time", 0.0),
            )
        ),
        streaming_partial_return_min_journeys=int(
            config.get(
                f"{prefix}_streaming_partial_return_min_journeys",
                config.get("journey_pricing_streaming_partial_return_min_journeys", 0),
            )
        ),
        streaming_final_dp_time_reserve=float(
            config.get(
                f"{prefix}_streaming_final_dp_time_reserve",
                config.get("journey_pricing_streaming_final_dp_time_reserve", 0.0),
            )
        ),
        streaming_profile_cap_per_mask=int(
            config.get(
                f"{prefix}_streaming_profile_cap_per_mask",
                config.get("journey_pricing_streaming_profile_cap_per_mask", 0),
            )
        ),
        min_add_reduced_cost=float(
            config.get(
                f"{prefix}_min_add_reduced_cost",
                config.get("journey_pricing_min_add_reduced_cost", 0.0),
            )
        ),
        dp_bound_pruning_enabled=bool(
            config.get(
                f"{prefix}_dp_bound_pruning_enabled",
                config.get("journey_pricing_dp_bound_pruning_enabled", True),
            )
        ),
        dp_disjoint_bound_pruning_enabled=bool(
            config.get(
                f"{prefix}_dp_disjoint_bound_pruning_enabled",
                config.get("journey_pricing_dp_disjoint_bound_pruning_enabled", True),
            )
        ),
        dp_disjoint_bound_max_tasks=int(
            config.get(
                f"{prefix}_dp_disjoint_bound_max_tasks",
                config.get("journey_pricing_dp_disjoint_bound_max_tasks", 12),
            )
        ),
        dp_cross_count_dominance_enabled=bool(
            config.get(
                f"{prefix}_dp_cross_count_dominance_enabled",
                config.get("journey_pricing_dp_cross_count_dominance_enabled", True),
            )
        ),
        dp_same_completion_pruning_enabled=bool(
            config.get(
                f"{prefix}_dp_same_completion_pruning_enabled",
                config.get("journey_pricing_dp_same_completion_pruning_enabled", False),
            )
        ),
        profile_catalog_enabled=bool(
            config.get(
                f"{prefix}_profile_catalog_enabled",
                config.get("journey_pricing_profile_catalog_enabled", False),
            )
        ),
        profile_catalog_resume_enabled=bool(
            config.get(
                f"{prefix}_profile_catalog_resume_enabled",
                config.get("journey_pricing_profile_catalog_resume_enabled", False),
            )
        ),
        profile_catalog_max_tasks=int(
            config.get(
                f"{prefix}_profile_catalog_max_tasks",
                config.get("journey_pricing_profile_catalog_max_tasks", 10),
            )
        ),
        profile_catalog_max_profiles=int(
            config.get(
                f"{prefix}_profile_catalog_max_profiles",
                config.get("journey_pricing_profile_catalog_max_profiles", 200000),
            )
        ),
        generalized_partial_dominance_enabled=bool(
            config.get(
                f"{prefix}_generalized_partial_dominance_enabled",
                config.get("journey_pricing_generalized_partial_dominance_enabled", False),
            )
        ),
        task_set_bound_pruning_enabled=bool(
            config.get(
                f"{prefix}_task_set_bound_pruning_enabled",
                config.get("journey_pricing_task_set_bound_pruning_enabled", False),
            )
        ),
        task_set_resource_pruning_enabled=bool(
            config.get(
                f"{prefix}_task_set_resource_pruning_enabled",
                config.get("journey_pricing_task_set_resource_pruning_enabled", False),
            )
        ),
        partial_profile_bound_pruning_enabled=bool(
            config.get(
                f"{prefix}_partial_profile_bound_pruning_enabled",
                config.get("journey_pricing_partial_profile_bound_pruning_enabled", False),
            )
        ),
        profile_online_dominance_enabled=bool(
            config.get(
                f"{prefix}_profile_online_dominance_enabled",
                config.get("journey_pricing_profile_online_dominance_enabled", False),
            )
        ),
        journey_selection_mode=str(
            config.get(
                f"{prefix}_selection_mode",
                config.get("journey_pricing_selection_mode", "reduced_cost"),
            )
        ),
        duplicate_scan_limit=int(
            config.get(
                f"{prefix}_duplicate_scan_limit",
                config.get("journey_pricing_duplicate_scan_limit", 10000),
            )
        ),
        eps=eps,
    )


def _log_journey_pricing(
    logger: FutureLogger,
    pricing: Any,
    cg_iter: int,
    *,
    pricing_kind: str,
    config: Any | None = None,
    pricing_dual_source: str = "scip",
    node_id: int = 0,
    depth: int = 0,
) -> None:
    logger.log(
        "journey_pricing",
        node_id=node_id,
        depth=depth,
        cg_iter=cg_iter,
        pricing_kind=pricing_kind,
        pricing_dual_source=pricing_dual_source,
        pricing_time_limit=None if config is None else round(float(getattr(config, "time_limit", 0.0)), 6),
        allow_partial_negative=None if config is None else bool(getattr(config, "allow_partial_negative", False)),
        best_reduced_cost=None if pricing.best_reduced_cost is None else round(float(pricing.best_reduced_cost), 9),
        candidate_trips=pricing.candidate_trips,
        selected_trips=pricing.selected_trips,
        negative_journeys=len(pricing.journeys),
        profile_dominance_pruned=getattr(pricing, "profile_dominance_pruned", 0),
        profile_cut_penalty_pruned=getattr(pricing, "profile_cut_penalty_pruned", 0),
        existing_journeys_filtered=getattr(pricing, "existing_journeys_filtered", 0),
        weak_negative_journeys_filtered=getattr(pricing, "weak_negative_journeys_filtered", 0),
        dominated_task_set_journeys_filtered=getattr(pricing, "dominated_task_set_journeys_filtered", 0),
        task_set_resource_pruned_sequences=getattr(pricing, "task_set_resource_pruned_sequences", 0),
        partial_profile_bound_pruned_labels=getattr(pricing, "partial_profile_bound_pruned_labels", 0),
        profile_mask_cap_pruned=getattr(pricing, "profile_mask_cap_pruned", 0),
        profile_completion_time_pruned=getattr(pricing, "profile_completion_time_pruned", 0),
        branch_mask_pruned_sequences=getattr(pricing, "branch_mask_pruned_sequences", 0),
        label_physical_catalog=getattr(pricing, "label_physical_catalog", False),
        label_physical_catalog_exhausted=getattr(pricing, "label_physical_catalog_exhausted", False),
        label_resume_heap=getattr(pricing, "label_resume_heap", 0),
        label_resume_profiles=getattr(pricing, "label_resume_profiles", 0),
        label_resume_exhausted=getattr(pricing, "label_resume_exhausted", False),
        dp_bound_pruned_labels=getattr(pricing, "dp_bound_pruned_labels", 0),
        dp_disjoint_bound_pruned_labels=getattr(pricing, "dp_disjoint_bound_pruned_labels", 0),
        dp_cross_count_pruned_labels=getattr(pricing, "dp_cross_count_pruned_labels", 0),
        dp_processed_labels=getattr(pricing, "dp_processed_labels", 0),
        dp_state_count=getattr(pricing, "dp_state_count", 0),
        dp_profile_record_scans=getattr(pricing, "dp_profile_record_scans", 0),
        dp_profile_time_filtered=getattr(pricing, "dp_profile_time_filtered", 0),
        dp_extension_attempts=getattr(pricing, "dp_extension_attempts", 0),
        dp_same_completion_pruned_labels=getattr(pricing, "dp_same_completion_pruned_labels", 0),
        completion_bound_enabled=getattr(pricing, "completion_bound_enabled", False),
        bound_build_time=round(float(getattr(pricing, "bound_build_time", 0.0)), 6),
        lb_state_count=getattr(pricing, "lb_state_count", 0),
        lb_min_value=None
        if getattr(pricing, "lb_min_value", None) is None
        else round(float(getattr(pricing, "lb_min_value")), 9),
        lb_mean_value=None
        if getattr(pricing, "lb_mean_value", None) is None
        else round(float(getattr(pricing, "lb_mean_value")), 9),
        lb_negative_state_count=getattr(pricing, "lb_negative_state_count", 0),
        expanded_labels_before_bound=getattr(pricing, "expanded_labels_before_bound", 0),
        expanded_labels_after_bound=getattr(pricing, "expanded_labels_after_bound", 0),
        lb_pruned_labels=getattr(pricing, "lb_pruned_labels", 0),
        generated_next_sorties_before_bound=getattr(pricing, "generated_next_sorties_before_bound", 0),
        generated_next_sorties_after_bound=getattr(pricing, "generated_next_sorties_after_bound", 0),
        profile_catalog_hit=getattr(pricing, "profile_catalog_hit", False),
        profile_catalog_size=getattr(pricing, "profile_catalog_size", 0),
        profile_generation_time=round(float(getattr(pricing, "profile_generation_time", 0.0)), 6),
        profile_filter_time=round(float(getattr(pricing, "profile_filter_time", 0.0)), 6),
        profile_dp_time=round(float(getattr(pricing, "profile_dp_time", 0.0)), 6),
        duplicate_candidate_scan_count=getattr(pricing, "duplicate_candidate_scan_count", 0),
        duplicate_candidates_filtered=getattr(pricing, "duplicate_candidates_filtered", 0),
        duplicate_scan_limited=getattr(pricing, "duplicate_scan_limited", False),
        streaming_pricing_enabled=None if config is None else bool(getattr(config, "streaming_pricing_enabled", False)),
        early_return_unique_masks_enabled=None
        if config is None
        else bool(getattr(config, "early_return_unique_masks_enabled", False)),
        streaming_min_returned_journeys=None
        if config is None
        else int(getattr(config, "streaming_min_returned_journeys", 1)),
        streaming_partial_return_after_time=None
        if config is None
        else round(float(getattr(config, "streaming_partial_return_after_time", 0.0)), 6),
        streaming_partial_return_min_journeys=None
        if config is None
        else int(getattr(config, "streaming_partial_return_min_journeys", 0)),
        streaming_final_dp_time_reserve=None
        if config is None
        else round(float(getattr(config, "streaming_final_dp_time_reserve", 0.0)), 6),
        streaming_profile_cap_per_mask=None
        if config is None
        else int(getattr(config, "streaming_profile_cap_per_mask", 0)),
        min_add_reduced_cost=None if config is None else round(float(getattr(config, "min_add_reduced_cost", 0.0)), 9),
        duplicate_scan_limit=None if config is None else int(getattr(config, "duplicate_scan_limit", 0)),
        dp_bound_pruning_enabled=None if config is None else bool(getattr(config, "dp_bound_pruning_enabled", False)),
        dp_disjoint_bound_pruning_enabled=None if config is None else bool(getattr(config, "dp_disjoint_bound_pruning_enabled", False)),
        dp_disjoint_bound_max_tasks=None if config is None else int(getattr(config, "dp_disjoint_bound_max_tasks", 0)),
        dp_cross_count_dominance_enabled=None if config is None else bool(getattr(config, "dp_cross_count_dominance_enabled", False)),
        dp_same_completion_pruning_enabled=None
        if config is None
        else bool(getattr(config, "dp_same_completion_pruning_enabled", False)),
        profile_catalog_enabled=None if config is None else bool(getattr(config, "profile_catalog_enabled", False)),
        profile_catalog_resume_enabled=None
        if config is None
        else bool(getattr(config, "profile_catalog_resume_enabled", False)),
        direct_journey_label_pricing_enabled=None if config is None else bool(getattr(config, "direct_journey_label_pricing_enabled", False)),
        direct_next_sortie_cache_hits=getattr(pricing, "direct_next_sortie_cache_hits", 0),
        direct_next_sortie_cache_misses=getattr(pricing, "direct_next_sortie_cache_misses", 0),
        direct_journey_label_next_sortie_cache_enabled=None
        if config is None
        else bool(getattr(config, "direct_journey_label_next_sortie_cache_enabled", False)),
        direct_journey_label_task_set_bound_pruning_enabled=None
        if config is None
        else bool(getattr(config, "direct_journey_label_task_set_bound_pruning_enabled", False)),
        direct_journey_label_completion_bound_enabled=None
        if config is None
        else bool(getattr(config, "direct_journey_label_completion_bound_enabled", False)),
        direct_journey_label_completion_bound_time_buckets=None
        if config is None
        else int(getattr(config, "direct_journey_label_completion_bound_time_buckets", 0)),
        direct_journey_label_completion_bound_energy_buckets=None
        if config is None
        else int(getattr(config, "direct_journey_label_completion_bound_energy_buckets", 0)),
        direct_journey_label_completion_bound_partial_pruning_enabled=None
        if config is None
        else bool(getattr(config, "direct_journey_label_completion_bound_partial_pruning_enabled", True)),
        direct_journey_label_completion_bound_audit_enabled=None
        if config is None
        else bool(getattr(config, "direct_journey_label_completion_bound_audit_enabled", False)),
        direct_journey_label_completion_bound_unique_task_helper_enabled=None
        if config is None
        else bool(getattr(config, "direct_journey_label_completion_bound_unique_task_helper_enabled", False)),
        direct_journey_label_completion_bound_unique_route_helper_enabled=None
        if config is None
        else bool(getattr(config, "direct_journey_label_completion_bound_unique_route_helper_enabled", False)),
        direct_journey_label_ng_dssr_enabled=None
        if config is None
        else bool(getattr(config, "direct_journey_label_ng_dssr_enabled", False)),
        direct_journey_label_ng_memory_size=None
        if config is None
        else int(getattr(config, "direct_journey_label_ng_memory_size", 0)),
        direct_journey_label_dssr_max_iterations=None
        if config is None
        else int(getattr(config, "direct_journey_label_dssr_max_iterations", 0)),
        direct_journey_label_ng_max_labels=None
        if config is None
        else int(getattr(config, "direct_journey_label_ng_max_labels", 0)),
        direct_journey_label_ng_min_negative_journeys=None
        if config is None
        else int(getattr(config, "direct_journey_label_ng_min_negative_journeys", 0)),
        direct_journey_label_ng_probe_time_limit=None
        if config is None
        else round(float(getattr(config, "direct_journey_label_ng_probe_time_limit", 0.0)), 6),
        direct_journey_label_ng_probe_min_journeys_for_early_return=None
        if config is None
        else int(getattr(config, "direct_journey_label_ng_probe_min_journeys_for_early_return", 1)),
        direct_journey_label_ng_probe_certificate_enabled=None
        if config is None
        else bool(getattr(config, "direct_journey_label_ng_probe_certificate_enabled", False)),
        direct_journey_label_ng_sequence_key_enabled=None
        if config is None
        else bool(getattr(config, "direct_journey_label_ng_sequence_key_enabled", True)),
        direct_journey_label_ng_visit_mask_dominance_enabled=None
        if config is None
        else bool(getattr(config, "direct_journey_label_ng_visit_mask_dominance_enabled", False)),
        direct_journey_label_ng_reset_memory_between_sorties_enabled=None
        if config is None
        else bool(getattr(config, "direct_journey_label_ng_reset_memory_between_sorties_enabled", False)),
        direct_journey_label_ng_exact_probe_enabled=None
        if config is None
        else bool(getattr(config, "direct_journey_label_ng_exact_probe_enabled", False)),
        ng_relaxation_enabled=bool(getattr(pricing, "ng_relaxation_enabled", False)),
        ng_dssr_iterations=int(getattr(pricing, "ng_dssr_iterations", 0)),
        ng_memory_size=int(getattr(pricing, "ng_memory_size", 0)),
        ng_non_elementary_negative=int(getattr(pricing, "ng_non_elementary_negative", 0)),
        ng_label_pops=int(getattr(pricing, "ng_label_pops", 0)),
        ng_generated_labels=int(getattr(pricing, "ng_generated_labels", 0)),
        ng_dominance_pruned_labels=int(getattr(pricing, "ng_dominance_pruned_labels", 0)),
        ng_fallback_to_elementary=bool(getattr(pricing, "ng_fallback_to_elementary", False)),
        ng_certificate_from_relaxation=bool(getattr(pricing, "ng_certificate_from_relaxation", False)),
        ng_best_relaxed_reduced_cost=None
        if getattr(pricing, "ng_best_relaxed_reduced_cost", None) is None
        else round(float(getattr(pricing, "ng_best_relaxed_reduced_cost")), 9),
        profile_labeling_enabled=None if config is None else bool(getattr(config, "profile_labeling_enabled", False)),
        profile_labeling_best_first_enabled=None if config is None else bool(getattr(config, "profile_labeling_best_first_enabled", False)),
        profile_labeling_resume_enabled=None
        if config is None
        else bool(getattr(config, "profile_labeling_resume_enabled", False)),
        profile_labeling_physical_catalog_resume_enabled=None
        if config is None
        else bool(getattr(config, "profile_labeling_physical_catalog_resume_enabled", False)),
        profile_labeling_physical_catalog_share_across_branches_enabled=None
        if config is None
        else bool(getattr(config, "profile_labeling_physical_catalog_share_across_branches_enabled", False)),
        profile_labeling_task_set_superset_pruning_enabled=None
        if config is None
        else bool(getattr(config, "profile_labeling_task_set_superset_pruning_enabled", False)),
        task_set_bound_pruning_enabled=None
        if config is None
        else bool(getattr(config, "task_set_bound_pruning_enabled", False)),
        task_set_resource_pruning_enabled=None
        if config is None
        else bool(getattr(config, "task_set_resource_pruning_enabled", False)),
        partial_profile_bound_pruning_enabled=None
        if config is None
        else bool(getattr(config, "partial_profile_bound_pruning_enabled", False)),
        profile_online_dominance_enabled=None
        if config is None
        else bool(getattr(config, "profile_online_dominance_enabled", False)),
        journey_selection_mode=None if config is None else str(getattr(config, "journey_selection_mode", "reduced_cost")),
        exhausted=pricing.exhausted,
        oracle_classification=_journey_pricing_oracle_classification(pricing),
        status=pricing.status,
        reason=pricing.reason,
        generated_sequences=pricing.generated_sequences,
        evaluated_timed_trips=pricing.evaluated_timed_trips,
    )


def _journey_pricing_oracle_classification(pricing: Any) -> str:
    if getattr(pricing, "journeys", None):
        return "negative_column_found"
    reason = str(getattr(pricing, "reason", ""))
    if bool(getattr(pricing, "duplicate_scan_limited", False)):
        return "duplicate_scan_limited"
    if int(getattr(pricing, "duplicate_candidates_filtered", 0)) > 0 or reason == "negative_journeys_already_in_pool":
        return "duplicate_tail"
    if int(getattr(pricing, "weak_negative_journeys_filtered", 0)) > 0:
        return "weak_negative_filtered_incomplete"
    if bool(getattr(pricing, "exhausted", False)) and str(getattr(pricing, "status", "")) == "OPTIMAL":
        return "exact_certificate"
    if "time" in reason:
        return "pricing_time_incomplete"
    return "pricing_incomplete"


def _log_journey_addition(
    logger: FutureLogger,
    pricing: Any,
    added: int,
    cg_iter: int,
    *,
    pricing_kind: str,
    node_id: int = 0,
    depth: int = 0,
) -> None:
    requested = len(getattr(pricing, "journeys", []) or [])
    signatures = [str(getattr(journey, "signature", "")) for journey in getattr(pricing, "journeys", []) or []]
    logger.log(
        "journey_column_addition",
        node_id=node_id,
        depth=depth,
        cg_iter=cg_iter,
        pricing_kind=pricing_kind,
        requested_journeys=requested,
        added_journeys=int(added),
        duplicate_journeys=max(0, requested - int(added)),
        candidate_signature_hash=_hash_strings(signatures),
    )


def _add_priced_journeys(journey_pool: JourneyPool, journeys: list[Any]) -> int:
    added = 0
    for journey in journeys:
        before = len(journey_pool.journeys)
        task_key = frozenset(int(task) for task in getattr(journey, "task_set", frozenset()))
        previous = journey_pool.by_task_set.get(task_key)
        stored = journey_pool.add(journey)
        replaced = bool(
            previous is not None
            and int(stored.id) == int(previous.id)
            and (
                tuple(getattr(stored, "signature", tuple())) != tuple(getattr(previous, "signature", tuple()))
                or float(getattr(stored, "cost", 0.0)) < float(getattr(previous, "cost", 0.0)) - 1.0e-9
            )
        )
        added += int(len(journey_pool.journeys) > before or replaced)
    return added


def _journey_forbidden_signatures_for_node(
    journey_pool: JourneyPool,
    branch_constraints: tuple[BranchConstraint, ...],
) -> set[tuple]:
    if not branch_constraints:
        return set(journey_pool.by_signature.keys())
    return {
        tuple(getattr(journey, "signature", tuple()))
        for journey in _filter_journeys_by_branch(journey_pool.journeys, branch_constraints)
    }


def _maybe_restart_journey_pool(
    data: FutureData,
    config: dict[str, Any],
    journey_pool: JourneyPool,
    solution: Any,
    final_solution: dict[int, list[Any]],
    recent_priced_journeys: list[Any],
    logger: FutureLogger,
    cg_iter: int,
    certificate_flat_rounds: int,
    restart_count: int,
    *,
    progress_classification: str = "",
    degenerate_rounds: int = 0,
    node_id: int = 0,
    depth: int = 0,
) -> tuple[JourneyPool, bool]:
    if not bool(config.get("journey_pool_restart_enabled", False)):
        return journey_pool, False
    if int(depth) < int(config.get("journey_pool_restart_min_depth", 0)):
        return journey_pool, False
    if int(restart_count) >= int(config.get("journey_pool_restart_max_times", 1)):
        return journey_pool, False
    triggered, trigger_reason = _journey_pool_restart_triggered(
        config,
        cg_iter,
        certificate_flat_rounds,
        restart_count,
        progress_classification=progress_classification,
        degenerate_rounds=degenerate_rounds,
    )
    if not triggered:
        return journey_pool, False
    old_size = len(journey_pool.journeys)
    min_columns = int(config.get("journey_pool_restart_min_columns", 250))
    if old_size < max(1, min_columns):
        return journey_pool, False

    keep_task_sets = max(0, int(config.get("journey_pool_restart_keep_task_sets", 80)))
    keep_recent = max(0, int(config.get("journey_pool_restart_keep_recent", 128)))
    new_pool = JourneyPool(task_set_dominance_enabled=bool(journey_pool.task_set_dominance_enabled))
    sources: dict[str, int] = {}

    def add_one(journey: Any, source: str) -> None:
        if journey is None:
            return
        before = len(new_pool.journeys)
        new_pool.add(journey)
        if len(new_pool.journeys) > before:
            sources[source] = int(sources.get(source, 0)) + 1

    for journey, value in getattr(solution, "journey_values", []) or []:
        if float(value) > 1.0e-8:
            add_one(journey, "active")

    for trips in final_solution.values():
        journey = make_journey(data, trips)
        if journey is not None:
            add_one(journey, "incumbent")

    for journey in recent_priced_journeys[:keep_recent]:
        add_one(journey, "recent")

    singleton_by_task: dict[int, Any] = {}
    for journey in journey_pool.journeys:
        tasks = tuple(sorted(int(task) for task in getattr(journey, "task_set", ())))
        if len(tasks) != 1:
            continue
        task = int(tasks[0])
        incumbent = singleton_by_task.get(task)
        if incumbent is None or float(journey.cost) < float(incumbent.cost) - 1.0e-9:
            singleton_by_task[task] = journey
    for journey in singleton_by_task.values():
        add_one(journey, "singleton")

    task_set_representatives = sorted(
        journey_pool.by_task_set.values(),
        key=lambda journey: (
            len(getattr(journey, "task_set", ())),
            round(float(getattr(journey, "cost", math.inf)), 9),
            tuple(sorted(int(task) for task in getattr(journey, "task_set", ()))),
            tuple(getattr(journey, "signature", ())),
        ),
    )
    for journey in task_set_representatives[:keep_task_sets]:
        add_one(journey, "task_set_best")

    new_size = len(new_pool.journeys)
    if new_size <= 0 or new_size >= old_size:
        return journey_pool, False
    logger.log(
        "journey_pool_restart",
        node_id=node_id,
        depth=depth,
        cg_iter=cg_iter,
        restart_count=int(restart_count) + 1,
        old_journeys=old_size,
        new_journeys=new_size,
        trigger_reason=trigger_reason,
        progress_classification=str(progress_classification),
        degenerate_rounds=int(degenerate_rounds),
        certificate_flat_rounds=int(certificate_flat_rounds),
        keep_task_sets=keep_task_sets,
        keep_recent=keep_recent,
        source_counts=sources,
        exact_safe=True,
        official_bound_unchanged=True,
    )
    return new_pool, True


def _journey_pool_restart_triggered(
    config: dict[str, Any],
    cg_iter: int,
    certificate_flat_rounds: int,
    restart_count: int,
    *,
    progress_classification: str = "",
    degenerate_rounds: int = 0,
) -> tuple[bool, str]:
    """Return whether a configured exact-safe pool rebuild should run.

    The historical behavior is ``certificate_flat``.  Additional triggers are
    experimental diagnostics only: they rebuild the finite RMP column pool but
    never certify a lower bound and never prune the pricing search space.
    """

    raw_triggers = config.get("journey_pool_restart_trigger", "certificate_flat")
    if isinstance(raw_triggers, str):
        triggers = {item.strip() for item in raw_triggers.split(",") if item.strip()}
    else:
        triggers = {str(item).strip() for item in raw_triggers or () if str(item).strip()}
    if not triggers:
        triggers = {"certificate_flat"}

    flat_threshold = max(1, int(config.get("journey_pool_restart_after_flat_rounds", 3)))
    if "certificate_flat" in triggers and int(certificate_flat_rounds) >= flat_threshold:
        return True, "certificate_flat"

    degenerate_threshold = max(
        1,
        int(config.get("journey_pool_restart_after_degenerate_rounds", flat_threshold)),
    )
    if "degenerate_flat" in triggers and int(degenerate_rounds) >= degenerate_threshold:
        return True, "degenerate_flat"

    allowed_progress = {
        "dual_changed_degenerate",
        "support_changed_objective_flat",
        "stalled_same_dual_support",
    }
    if "objective_flat" in triggers and str(progress_classification) in allowed_progress:
        return True, "objective_flat"

    interval = int(config.get("journey_pool_restart_interval", 0))
    if "fixed_interval" in triggers and interval > 0 and int(cg_iter) > 0 and int(cg_iter) % interval == 0:
        return True, "fixed_interval"

    return False, "not_triggered"


def _journey_pool_task_set_costs(journey_pool: JourneyPool) -> dict[frozenset[int], float]:
    return {
        frozenset(int(task) for task in task_set): float(journey.cost)
        for task_set, journey in journey_pool.by_task_set.items()
    }


def _journey_pricing_dominant_task_set_costs(
    journey_pool: JourneyPool,
    cuts: list[FutureCut] | tuple[FutureCut, ...],
    branch_constraints: tuple[BranchConstraint, ...],
) -> dict[frozenset[int], float]:
    if not bool(journey_pool.task_set_dominance_enabled):
        return {}
    if not _journey_task_set_dominance_safe(cuts, branch_constraints):
        return {}
    return _journey_pool_task_set_costs(journey_pool)


def _journey_task_set_dominance_safe(
    cuts: list[FutureCut] | tuple[FutureCut, ...],
    branch_constraints: tuple[BranchConstraint, ...],
) -> bool:
    safe_cut_kinds = {"subset_row", "fleet_lower_bound", "fleet_upper_bound"}
    for cut in cuts:
        if getattr(cut, "kind", "") not in safe_cut_kinds:
            return False
    for constraint in branch_constraints:
        if constraint.kind not in {"same_vehicle", "separate_vehicle"} or constraint.task_j is None:
            return False
    return True


def _journey_dual_vector(data: FutureData, duals: Any, cut_count: int) -> tuple[float, ...]:
    values: list[float] = [round(float(duals.fleet_limit), 9)]
    values.extend(round(float(duals.cover.get(int(task), 0.0)), 9) for task in data.tasks)
    cut_duals = duals.cuts or {}
    values.extend(round(float(cut_duals.get(index, 0.0)), 9) for index in range(int(cut_count)))
    return tuple(values)


def _journey_dual_hash(vector: tuple[float, ...]) -> str:
    return hashlib.sha1(repr(tuple(round(float(value), 9) for value in vector)).encode("utf-8")).hexdigest()[:16]


def _journey_progress_classification(
    objective_delta: float | None,
    dual_l1_delta: float | None,
    previous_support_hash: str | None,
    support_hash: str,
    eps: float,
) -> str:
    if objective_delta is None:
        return "initial_rmp"
    if objective_delta < -float(eps):
        return "objective_improved"
    if abs(float(objective_delta)) <= float(eps):
        dual_changed = dual_l1_delta is not None and float(dual_l1_delta) > float(eps)
        support_changed = previous_support_hash is not None and previous_support_hash != support_hash
        if dual_changed:
            return "dual_changed_degenerate"
        if support_changed:
            return "support_changed_objective_flat"
        return "stalled_same_dual_support"
    return "objective_worsened"


def _journey_duplicate_diagnostics(
    journey_pool: JourneyPool,
    journeys: list[Any],
    duals: Any,
    cuts: tuple[FutureCut, ...],
) -> dict[str, Any]:
    duplicate_signatures = []
    duplicate_manual_rcs = []
    duplicate_cost_deltas = []
    existing = journey_pool.by_signature
    for journey in journeys:
        signature = getattr(journey, "signature", None)
        if signature not in existing:
            continue
        duplicate_signatures.append(str(signature))
        stored = existing[signature]
        try:
            duplicate_manual_rcs.append(float(manual_journey_reduced_cost(stored, duals, cuts)))
        except Exception:
            pass
        try:
            duplicate_cost_deltas.append(round(float(getattr(journey, "cost")) - float(stored.cost), 9))
        except Exception:
            pass
    return {
        "duplicate_signature_count": len(duplicate_signatures),
        "duplicate_signature_hash": _hash_strings(duplicate_signatures),
        "duplicate_manual_rc_min": None if not duplicate_manual_rcs else round(min(duplicate_manual_rcs), 9),
        "duplicate_manual_rc_max": None if not duplicate_manual_rcs else round(max(duplicate_manual_rcs), 9),
        "duplicate_negative_manual_rc_count": sum(1 for value in duplicate_manual_rcs if value < -1.0e-6),
        "duplicate_cost_delta_min": None if not duplicate_cost_deltas else min(duplicate_cost_deltas),
        "duplicate_cost_delta_max": None if not duplicate_cost_deltas else max(duplicate_cost_deltas),
    }


def _journey_support_hash(values: list[tuple[Any, float]]) -> str:
    parts = [
        f"{getattr(journey, 'signature', '')}:{round(float(value), 9)}"
        for journey, value in sorted(
            values,
            key=lambda item: (str(getattr(item[0], "signature", "")), round(float(item[1]), 9)),
        )
    ]
    return _hash_strings(parts)


def _hash_strings(values: list[str]) -> str:
    payload = "\n".join(values)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def _journey_assignment(values: list[tuple[Any, float]]) -> dict[int, list[Any]]:
    assignment: dict[int, list[Any]] = {}
    vehicle = 1
    for journey, value in values:
        if float(value) <= 1.0e-6:
            continue
        assignment[vehicle] = list(journey.trips)
        vehicle += 1
    return assignment
