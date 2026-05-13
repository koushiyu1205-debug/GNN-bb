"""中文摘要：vehicle-schedule BPC 对外求解入口，负责读配置、运行树搜索并整理结果。"""

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
    log_path: str
    solution_path: str

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


def solve_vehicle_schedule_bpc(
    data: InstanceData,
    *,
    config: dict[str, Any],
    log_path: str | Path,
    solution_path: str | Path,
    quiet: bool = False,
) -> SolverResult:
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
        log_path=str(log_path),
        solution_path=str(solution_path),
    )
