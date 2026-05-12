"""中文摘要：本文件是 clean BPC 对外入口。它读取数据、运行显式 BPC 树，并整理 CSV/JSON 输出字段。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .columns import route_to_json
from .data import BPCData
from .logger import BPCLogger
from .tree import CleanBPCTree, incumbent_to_solution


@dataclass
class BPCResult:
    instance: str
    task_count: int
    vehicle_count: int
    sortie_count: int
    status: str
    primal_bound: float | None
    dual_bound: float | None
    gap: float | None
    solving_time: float
    node_count: int
    rmp_solves: int
    pricing_calls: int
    exact_pricing_calls: int
    branch_lp_test_rmp_solves: int
    branch_heuristic_test_rmp_solves: int
    branch_heuristic_test_pricing_calls: int
    branch_lp_candidates_tested: int
    branch_heuristic_candidates_tested: int
    branch_testing_time: float
    generated_routes: int
    generated_columns: int
    cuts_added: int
    root_relaxation: float | None
    incumbent_node: int | None
    log_path: str
    instance_path: str
    seed: int | None

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


def _round(value: Any, digits: int = 6) -> Any:
    if value is None:
        return None
    if isinstance(value, float):
        return round(value, digits)
    return value


def solve_bpc_clean(
    data: BPCData,
    *,
    time_limit: float,
    max_nodes: int,
    pricing_eps: float,
    integer_tol: float,
    max_routes_per_pricing: int,
    max_labels_per_pricing: int,
    rmp_params: dict[str, Any] | None,
    log_path: str | Path | None,
    solution_path: str | Path | None,
    seed: int | None,
    quiet: bool,
    branching_strategy: str = "3pb",
    three_pb_pseudocost_candidates: int = 6,
    three_pb_fractional_candidates: int = 6,
    three_pb_lp_candidates: int = 3,
    three_pb_heuristic_cg_iterations: int = 3,
    three_pb_heuristic_routes_per_iter: int = 50,
    three_pb_heuristic_max_labels: int = 800,
) -> BPCResult:
    logger = BPCLogger(log_path, console=not quiet)
    try:
        tree = CleanBPCTree(
            data,
            time_limit=time_limit,
            max_nodes=max_nodes,
            eps=pricing_eps,
            integer_tol=integer_tol,
            max_routes_per_pricing=max_routes_per_pricing,
            max_labels_per_pricing=max_labels_per_pricing,
            rmp_params=rmp_params,
            logger=logger,
            branching_strategy=branching_strategy,
            three_pb_pseudocost_candidates=three_pb_pseudocost_candidates,
            three_pb_fractional_candidates=three_pb_fractional_candidates,
            three_pb_lp_candidates=three_pb_lp_candidates,
            three_pb_heuristic_cg_iterations=three_pb_heuristic_cg_iterations,
            three_pb_heuristic_routes_per_iter=three_pb_heuristic_routes_per_iter,
            three_pb_heuristic_max_labels=three_pb_heuristic_max_labels,
        )
        tree_result = tree.solve()
    finally:
        logger.close()

    generated_columns = len(tree_result.routes) * len(data.vehicles)
    result = BPCResult(
        instance=data.name,
        task_count=len(data.tasks),
        vehicle_count=len(data.vehicles),
        sortie_count=data.sortie_limit,
        status=tree_result.status,
        primal_bound=_round(tree_result.primal_bound),
        dual_bound=_round(tree_result.dual_bound),
        gap=_round(tree_result.gap),
        solving_time=_round(tree_result.solving_time),
        node_count=tree_result.node_count,
        rmp_solves=tree_result.stats.rmp_solves,
        pricing_calls=tree_result.stats.pricing_calls,
        exact_pricing_calls=tree_result.stats.exact_pricing_calls,
        branch_lp_test_rmp_solves=tree_result.stats.branch_lp_test_rmp_solves,
        branch_heuristic_test_rmp_solves=tree_result.stats.branch_heuristic_test_rmp_solves,
        branch_heuristic_test_pricing_calls=tree_result.stats.branch_heuristic_test_pricing_calls,
        branch_lp_candidates_tested=tree_result.stats.branch_lp_candidates_tested,
        branch_heuristic_candidates_tested=tree_result.stats.branch_heuristic_candidates_tested,
        branch_testing_time=_round(tree_result.stats.branch_testing_time),
        generated_routes=len(tree_result.routes),
        generated_columns=generated_columns,
        cuts_added=len(tree_result.cuts),
        root_relaxation=_round(tree_result.stats.root_relaxation),
        incumbent_node=None if tree_result.incumbent is None else tree_result.incumbent.node_id,
        log_path=str(log_path or ""),
        instance_path=str(data.instance_path),
        seed=seed,
    )

    if solution_path is not None:
        import json

        output = {
            "summary": result.to_row(),
            "solution": incumbent_to_solution(data, tree_result.incumbent),
            "routes": [route_to_json(route) for route in tree_result.routes],
            "cuts": [
                {
                    "id": cut.id,
                    "vehicle": cut.vehicle,
                    "kind": cut.kind,
                    "source_vehicle": cut.source_vehicle,
                    "signatures": [list(signature) for signature in cut.signatures],
                    "rhs": cut.rhs,
                }
                for cut in tree_result.cuts
            ],
        }
        path = Path(solution_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(output, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    return result
