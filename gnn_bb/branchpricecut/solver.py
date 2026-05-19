"""中文摘要：branchpricecut 对外求解入口，支持 hybrid route master 和 vehicle-schedule baseline。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from .columns import schedule_to_json
from .data import InstanceData
from .logger import BPCLogger
from .tree import VehicleScheduleBPCTree


@dataclass
class SolverResult:
    instance: str
    master_type: str
    master_cover_mode: str
    task_count: int
    vehicle_count: int
    sortie_limit: int
    status: str
    primal_bound: float | None
    dual_bound: float | None
    gap: float | None
    solving_time: float
    node_count: int
    rmp_solves: int
    pricing_calls: int
    generated_columns: int
    label_pops: int
    generated_labels: int
    pricing_queue_peak: int
    branch_nodes: int
    root_relaxation: float | None
    phase_switch_count: int
    manual_rc_check_max_error: float
    vehicle_lb_dual_effective_value: float
    pool_scan_columns_found: int
    pool_scan_time: float
    route_pool_size: int
    low_cbar_routes_kept: int
    per_task_routes_kept: int
    route_size_bucket_routes_kept: int
    time_flexible_routes_kept: int
    micro_routes_kept: int
    branch_relevant_routes_kept: int
    historical_routes_kept: int
    diverse_routes_kept: int
    schedule_dp_calls: int
    schedule_dp_labels_created: int
    schedule_dp_labels_pruned_by_subset_dominance: int
    schedule_dp_labels_pruned_by_beam: int
    schedule_dp_exhausted: bool
    schedule_dp_negative_schedules_found: int
    schedule_dp_best_rc: float | None
    schedule_dp_time: float
    heuristic_degradation_skips: int
    restricted_master_integer_calls: int
    restricted_master_integer_feasible: int
    restricted_master_integer_time: float
    restricted_master_integer_best_objective: float | None
    exact_pricing_calls: int
    exact_pricing_called: int
    exact_pricing_exhausted: int
    exact_pricing_best_rc: float | None
    exact_pricing_time: float
    ng_dssr_max_ng_size: int
    dssr_iterations: int
    dssr_memory_size: int
    dssr_non_elementary_negative: int
    dssr_certificate_from_relaxation: int
    full_memory_fallback_called: int
    pricing_certificate_layer: str | None
    generated_routes: int
    cuts_added: int
    crossing_cuts_added: int
    crossing_cuts_upgraded: int
    robust_capacity_cuts_added: int
    resource_lower_bound_cuts_added: int
    schedule_nogood_cuts_added: int
    schedule_capacity_cuts_added: int
    cuts_purged: int
    branch_testing_time: float
    log_path: str
    solution_path: str

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


def _to_hybrid_data(data: InstanceData):
    from bpc.data import BPCData

    return BPCData(
        instance=data.instance,
        pairwise=data.pairwise,
        instance_path=data.instance_path,
        name=data.name,
        tasks=data.tasks,
        vehicles=tuple(range(1, int(data.vehicle_count) + 1)),
        sortie_limit=data.sortie_limit,
        capacity=data.capacity,
        energy_limit=data.energy_limit,
        rho=data.rho,
        fixed_vehicle_cost=data.fixed_vehicle_cost,
        horizon=data.horizon,
    )


def _hybrid_value(config: dict[str, Any], name: str, fallback: Any) -> Any:
    return config.get(name, fallback)


def _solve_hybrid_route_bpc(
    data: InstanceData,
    *,
    config: dict[str, Any],
    log_path: str | Path,
    solution_path: str | Path,
    quiet: bool,
) -> SolverResult:
    from bpc.solver import solve_bpc_clean

    hybrid_data = _to_hybrid_data(data)
    result = solve_bpc_clean(
        hybrid_data,
        time_limit=float(config.get("time_limit", 3600)),
        max_nodes=int(config.get("max_nodes", 100000)),
        pricing_eps=float(config.get("pricing_eps", 1.0e-6)),
        integer_tol=float(config.get("integer_tol", 1.0e-6)),
        max_routes_per_pricing=int(config.get("max_routes_per_pricing", config.get("max_columns_per_pricing", 200))),
        max_labels_per_pricing=int(config.get("hybrid_max_labels_per_pricing", config.get("max_labels_per_pricing", 0)) or 0),
        root_max_routes_per_pricing=int(config.get("root_max_routes_per_pricing", 0) or 0),
        heuristic_pricing_enabled=bool(config.get("heuristic_pricing_enabled", False)),
        heuristic_pricing_max_labels=int(config.get("heuristic_pricing_max_labels", 100000)),
        heuristic_pricing_routes_per_round=int(config.get("heuristic_pricing_routes_per_round", 500)),
        heuristic_pricing_selection_mode=str(config.get("heuristic_pricing_selection_mode", "diverse")),
        exact_pricing_selection_mode=str(config.get("exact_pricing_selection_mode", "reduced_cost")),
        branch_node_heuristic_boost_enabled=bool(config.get("branch_node_heuristic_boost_enabled", False)),
        branch_node_heuristic_boost_max_labels=int(config.get("branch_node_heuristic_boost_max_labels", 800000)),
        branch_node_heuristic_boost_routes_per_round=int(config.get("branch_node_heuristic_boost_routes_per_round", 1000)),
        branch_node_heuristic_boost_min_depth=int(config.get("branch_node_heuristic_boost_min_depth", 1)),
        exact_pricing_dominance_enabled=bool(
            config.get("exact_pricing_dominance_enabled", config.get("exact_pricing_enable_dominance", False))
        ),
        restricted_master_heuristic_enabled=bool(config.get("restricted_master_heuristic_enabled", False)),
        restricted_master_time_limit=float(config.get("restricted_master_time_limit", 20.0)),
        restricted_master_max_routes=int(config.get("restricted_master_max_routes", 4000)),
        restricted_master_max_calls=int(config.get("restricted_master_max_calls", 20)),
        restricted_master_max_depth=int(config.get("restricted_master_max_depth", 3)),
        restricted_master_schedule_aware=bool(config.get("restricted_master_schedule_aware", True)),
        restricted_master_max_no_good_rounds=int(config.get("restricted_master_max_no_good_rounds", 20)),
        rmp_params=dict(config.get("rmp_params", {})),
        log_path=log_path,
        solution_path=solution_path,
        seed=int(config["random_seed"]) if config.get("random_seed") is not None else None,
        quiet=quiet,
        branching_strategy=str(config.get("branching_strategy", "3pb")),
        three_pb_pseudocost_candidates=int(_hybrid_value(config, "three_pb_pseudocost_candidates", 6)),
        three_pb_fractional_candidates=int(_hybrid_value(config, "three_pb_fractional_candidates", 6)),
        three_pb_lp_candidates=int(_hybrid_value(config, "three_pb_lp_candidates", 3)),
        three_pb_heuristic_cg_iterations=int(_hybrid_value(config, "three_pb_heuristic_cg_iterations", 3)),
        three_pb_heuristic_routes_per_iter=int(_hybrid_value(config, "three_pb_heuristic_routes_per_iter", 50)),
        three_pb_heuristic_max_labels=int(_hybrid_value(config, "three_pb_heuristic_max_labels", 800)),
        task_vehicle_linking_enabled=bool(_hybrid_value(config, "task_vehicle_linking_enabled", True)),
        robust_capacity_cuts_enabled=bool(_hybrid_value(config, "robust_capacity_cuts_enabled", True)),
        robust_capacity_cut_max_depth=int(_hybrid_value(config, "robust_capacity_cut_max_depth", 0)),
        robust_capacity_cut_max_subset_size=int(_hybrid_value(config, "robust_capacity_cut_max_subset_size", 5)),
        robust_capacity_cut_max_per_round=int(_hybrid_value(config, "robust_capacity_cut_max_per_round", 20)),
        robust_capacity_cut_min_violation=float(_hybrid_value(config, "robust_capacity_cut_min_violation", 1.0e-5)),
        robust_capacity_cut_max_rounds_per_node=int(_hybrid_value(config, "robust_capacity_cut_max_rounds_per_node", 3)),
        resource_lower_bound_cuts_enabled=bool(_hybrid_value(config, "resource_lower_bound_cuts_enabled", True)),
        resource_cut_max_depth=int(_hybrid_value(config, "resource_cut_max_depth", 0)),
        resource_cut_max_subset_size=int(_hybrid_value(config, "resource_cut_max_subset_size", 6)),
        resource_cut_max_per_round=int(_hybrid_value(config, "resource_cut_max_per_round", 20)),
        resource_cut_min_violation=float(_hybrid_value(config, "resource_cut_min_violation", 1.0e-5)),
        resource_cut_max_rounds_per_node=int(_hybrid_value(config, "resource_cut_max_rounds_per_node", 3)),
        schedule_capacity_cuts_enabled=bool(_hybrid_value(config, "schedule_capacity_cuts_enabled", True)),
        schedule_capacity_cut_max_depth=int(_hybrid_value(config, "schedule_capacity_cut_max_depth", 0)),
        schedule_capacity_cut_max_subset_size=int(_hybrid_value(config, "schedule_capacity_cut_max_subset_size", 10)),
        schedule_capacity_cut_max_per_round=int(_hybrid_value(config, "schedule_capacity_cut_max_per_round", 20)),
        schedule_capacity_cut_min_violation=float(_hybrid_value(config, "schedule_capacity_cut_min_violation", 1.0e-5)),
        schedule_capacity_cut_max_rounds_per_node=int(_hybrid_value(config, "schedule_capacity_cut_max_rounds_per_node", 3)),
        schedule_capacity_oracle_max_states=int(_hybrid_value(config, "schedule_capacity_oracle_max_states", 200000)),
        schedule_capacity_candidate_top_tasks=int(_hybrid_value(config, "schedule_capacity_candidate_top_tasks", 12)),
        schedule_capacity_candidate_max_combinations=int(_hybrid_value(config, "schedule_capacity_candidate_max_combinations", 300)),
        schedule_capacity_route_union_top_routes=int(_hybrid_value(config, "schedule_capacity_route_union_top_routes", 8)),
        schedule_capacity_route_union_max_routes=int(_hybrid_value(config, "schedule_capacity_route_union_max_routes", 4)),
        cut_purge_age=int(_hybrid_value(config, "cut_purge_age", 20)),
        cut_purge_slack=float(_hybrid_value(config, "cut_purge_slack", 1.0e-5)),
        cut_purge_dual=float(_hybrid_value(config, "cut_purge_dual", 1.0e-8)),
    )

    exhausted_pricing_calls = result.exact_pricing_calls
    if result.status == "PRICING_INCOMPLETE" and exhausted_pricing_calls > 0:
        exhausted_pricing_calls -= 1

    return SolverResult(
        instance=result.instance,
        master_type="hybrid_route",
        master_cover_mode="route_vehicle",
        task_count=result.task_count,
        vehicle_count=result.vehicle_count,
        sortie_limit=result.sortie_count,
        status=result.status,
        primal_bound=result.primal_bound,
        dual_bound=result.dual_bound,
        gap=result.gap,
        solving_time=result.solving_time,
        node_count=result.node_count,
        rmp_solves=result.rmp_solves,
        pricing_calls=result.pricing_calls,
        generated_columns=result.generated_columns,
        label_pops=result.label_pops,
        generated_labels=result.generated_labels,
        pricing_queue_peak=0,
        branch_nodes=result.branch_nodes,
        root_relaxation=result.root_relaxation,
        phase_switch_count=0,
        manual_rc_check_max_error=0.0,
        vehicle_lb_dual_effective_value=0.0,
        pool_scan_columns_found=0,
        pool_scan_time=0.0,
        route_pool_size=result.generated_routes,
        low_cbar_routes_kept=0,
        per_task_routes_kept=0,
        route_size_bucket_routes_kept=0,
        time_flexible_routes_kept=0,
        micro_routes_kept=0,
        branch_relevant_routes_kept=0,
        historical_routes_kept=0,
        diverse_routes_kept=0,
        schedule_dp_calls=0,
        schedule_dp_labels_created=0,
        schedule_dp_labels_pruned_by_subset_dominance=0,
        schedule_dp_labels_pruned_by_beam=0,
        schedule_dp_exhausted=False,
        schedule_dp_negative_schedules_found=0,
        schedule_dp_best_rc=None,
        schedule_dp_time=0.0,
        heuristic_degradation_skips=0,
        restricted_master_integer_calls=result.restricted_master_integer_calls,
        restricted_master_integer_feasible=result.restricted_master_integer_feasible,
        restricted_master_integer_time=result.restricted_master_integer_time,
        restricted_master_integer_best_objective=result.restricted_master_integer_best_objective,
        exact_pricing_calls=result.exact_pricing_calls,
        exact_pricing_called=result.exact_pricing_calls,
        exact_pricing_exhausted=exhausted_pricing_calls,
        exact_pricing_best_rc=None,
        exact_pricing_time=0.0,
        ng_dssr_max_ng_size=0,
        dssr_iterations=0,
        dssr_memory_size=0,
        dssr_non_elementary_negative=0,
        dssr_certificate_from_relaxation=0,
        full_memory_fallback_called=0,
        pricing_certificate_layer="route_rcsp",
        generated_routes=result.generated_routes,
        cuts_added=result.cuts_added,
        crossing_cuts_added=result.crossing_cuts_added,
        crossing_cuts_upgraded=result.crossing_cuts_upgraded,
        robust_capacity_cuts_added=result.robust_capacity_cuts_added,
        resource_lower_bound_cuts_added=result.resource_lower_bound_cuts_added,
        schedule_nogood_cuts_added=result.schedule_nogood_cuts_added,
        schedule_capacity_cuts_added=result.schedule_capacity_cuts_added,
        cuts_purged=result.cuts_purged,
        branch_testing_time=result.branch_testing_time,
        log_path=result.log_path,
        solution_path=str(solution_path),
    )


def solve_vehicle_schedule_bpc(
    data: InstanceData,
    *,
    config: dict[str, Any],
    log_path: str | Path,
    solution_path: str | Path,
    quiet: bool = False,
) -> SolverResult:
    master_type = str(config.get("master_type", "hybrid_route")).lower()
    if master_type == "hybrid_route":
        return _solve_hybrid_route_bpc(data, config=config, log_path=log_path, solution_path=solution_path, quiet=quiet)
    if master_type != "vehicle_schedule":
        raise ValueError(f"未知 master_type: {master_type}")

    logger = BPCLogger(log_path, console=not quiet)
    try:
        tree = VehicleScheduleBPCTree(
            data,
            time_limit=float(config.get("time_limit", 3600)),
            max_nodes=int(config.get("max_nodes", 100000)),
            eps=float(config.get("pricing_eps", 1.0e-6)),
            integer_tol=float(config.get("integer_tol", 1.0e-6)),
            max_columns_per_pricing=int(config.get("max_columns_per_pricing", 100)),
            max_labels_per_pricing=int(config.get("max_labels_per_pricing", 0) or 0),
            max_generated_labels_per_pricing=int(config.get("max_generated_labels_per_pricing", 0) or 0),
            max_queue_size_per_pricing=int(config.get("max_queue_size_per_pricing", 0) or 0),
            max_candidate_pool_per_pricing=int(config.get("max_candidate_pool_per_pricing", 0) or 0),
            max_pricing_seconds=float(config.get("max_pricing_seconds", 0.0) or 0.0),
            master_cover_mode=str(config.get("master_cover_mode", "partitioning")),
            vehicle_lower_bound_cut_enabled=bool(config.get("vehicle_lower_bound_cut_enabled", False)),
            schedule_column_pool_enabled=bool(config.get("schedule_column_pool_enabled", True)),
            max_schedule_pool_size=int(config.get("max_schedule_pool_size", 100000)),
            route_pool_pricing_enabled=bool(config.get("route_pool_pricing_enabled", True)),
            exact_pricing_fallback_enabled=bool(config.get("exact_pricing_fallback_enabled", True)),
            exact_pricing_required_for_certificate=bool(config.get("exact_pricing_required_for_certificate", True)),
            config=config,
            rmp_params=dict(config.get("rmp_params", {})),
            logger=logger,
        )
        result = tree.solve()
    finally:
        logger.close()

    solution_path = Path(solution_path)
    solution_path.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "summary": {
            "status": result.status,
            "master_cover_mode": str(config.get("master_cover_mode", "partitioning")),
            "primal_bound": None if result.primal_bound is None else round(result.primal_bound, 6),
            "dual_bound": None if result.dual_bound is None else round(result.dual_bound, 6),
            "gap": None if result.gap is None else round(result.gap, 6),
        },
        "incumbent": None
        if result.incumbent is None
        else {
            "objective": round(result.incumbent.objective, 6),
            "node_id": result.incumbent.node_id,
            "schedules": [schedule_to_json(column) for column in result.incumbent.columns],
        },
        "columns": [schedule_to_json(column) for column in result.columns],
    }
    solution_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    return SolverResult(
        instance=data.name,
        master_type="vehicle_schedule",
        master_cover_mode=str(config.get("master_cover_mode", "partitioning")),
        task_count=len(data.tasks),
        vehicle_count=data.vehicle_count,
        sortie_limit=data.sortie_limit,
        status=result.status,
        primal_bound=None if result.primal_bound is None else round(result.primal_bound, 6),
        dual_bound=None if result.dual_bound is None else round(result.dual_bound, 6),
        gap=None if result.gap is None else round(result.gap, 6),
        solving_time=round(result.elapsed, 6),
        node_count=result.stats.nodes,
        rmp_solves=result.stats.rmp_solves,
        pricing_calls=result.stats.pricing_calls,
        generated_columns=result.stats.generated_columns,
        label_pops=result.stats.label_pops,
        generated_labels=result.stats.generated_labels,
        pricing_queue_peak=result.stats.pricing_queue_peak,
        branch_nodes=result.stats.branch_nodes,
        root_relaxation=None if result.stats.root_relaxation is None else round(result.stats.root_relaxation, 6),
        phase_switch_count=result.stats.phase_switch_count,
        manual_rc_check_max_error=round(result.stats.manual_rc_check_max_error, 10),
        vehicle_lb_dual_effective_value=round(result.stats.vehicle_lb_dual_effective_value, 10),
        pool_scan_columns_found=result.stats.pool_scan_columns_found,
        pool_scan_time=round(result.stats.pool_scan_time, 6),
        route_pool_size=result.stats.route_pool_size,
        low_cbar_routes_kept=result.stats.low_cbar_routes_kept,
        per_task_routes_kept=result.stats.per_task_routes_kept,
        route_size_bucket_routes_kept=result.stats.route_size_bucket_routes_kept,
        time_flexible_routes_kept=result.stats.time_flexible_routes_kept,
        micro_routes_kept=result.stats.micro_routes_kept,
        branch_relevant_routes_kept=result.stats.branch_relevant_routes_kept,
        historical_routes_kept=result.stats.historical_routes_kept,
        diverse_routes_kept=result.stats.diverse_routes_kept,
        schedule_dp_calls=result.stats.schedule_dp_calls,
        schedule_dp_labels_created=result.stats.schedule_dp_labels_created,
        schedule_dp_labels_pruned_by_subset_dominance=result.stats.schedule_dp_labels_pruned_by_subset_dominance,
        schedule_dp_labels_pruned_by_beam=result.stats.schedule_dp_labels_pruned_by_beam,
        schedule_dp_exhausted=result.stats.schedule_dp_exhausted,
        schedule_dp_negative_schedules_found=result.stats.schedule_dp_negative_schedules_found,
        schedule_dp_best_rc=None if result.stats.schedule_dp_best_rc is None else round(result.stats.schedule_dp_best_rc, 6),
        schedule_dp_time=round(result.stats.schedule_dp_time, 6),
        heuristic_degradation_skips=result.stats.heuristic_degradation_skips,
        restricted_master_integer_calls=result.stats.restricted_master_integer_calls,
        restricted_master_integer_feasible=result.stats.restricted_master_integer_feasible,
        restricted_master_integer_time=round(result.stats.restricted_master_integer_time, 6),
        restricted_master_integer_best_objective=None
        if result.stats.restricted_master_integer_best_objective is None
        else round(result.stats.restricted_master_integer_best_objective, 6),
        exact_pricing_calls=result.stats.exact_pricing_calls,
        exact_pricing_called=result.stats.exact_pricing_called,
        exact_pricing_exhausted=result.stats.exact_pricing_exhausted,
        exact_pricing_best_rc=None if result.stats.exact_pricing_best_rc is None else round(result.stats.exact_pricing_best_rc, 6),
        exact_pricing_time=round(result.stats.exact_pricing_time, 6),
        ng_dssr_max_ng_size=result.stats.ng_dssr_max_ng_size,
        dssr_iterations=result.stats.dssr_iterations,
        dssr_memory_size=result.stats.dssr_memory_size,
        dssr_non_elementary_negative=result.stats.dssr_non_elementary_negative,
        dssr_certificate_from_relaxation=result.stats.dssr_certificate_from_relaxation,
        full_memory_fallback_called=result.stats.full_memory_fallback_called,
        pricing_certificate_layer=result.stats.pricing_certificate_layer,
        generated_routes=result.stats.route_pool_size,
        cuts_added=0,
        crossing_cuts_added=0,
        crossing_cuts_upgraded=0,
        robust_capacity_cuts_added=0,
        resource_lower_bound_cuts_added=0,
        schedule_nogood_cuts_added=0,
        schedule_capacity_cuts_added=0,
        cuts_purged=0,
        branch_testing_time=0.0,
        log_path=str(log_path),
        solution_path=str(solution_path),
    )
