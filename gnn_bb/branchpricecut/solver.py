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
        log_path=str(log_path),
        solution_path=str(solution_path),
    )
