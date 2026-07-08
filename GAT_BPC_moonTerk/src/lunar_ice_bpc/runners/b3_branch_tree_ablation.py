"""B3 branch-and-price tree ablation runner and report writer."""

from __future__ import annotations

import csv
import gc
import json
from pathlib import Path
import signal
from statistics import mean
from time import perf_counter
from typing import Callable, Iterable

from lunar_ice_bpc.exact.bpc.solver.branch_tree_solver import (
    _QueuedNode,
    _solve_b3_node,
    solve_b3_branch_price_tree_baseline,
)
from lunar_ice_bpc.exact.bpc.solver.root_node_solver import (
    dense_rmp_memory_precheck,
    representative_universe_column_count,
)
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (
    B2B_R3_MODE,
    B2_PRODUCT_MODE,
    solve_b2_pricing_tail_baseline,
    solve_b2_product_exact_solver,
)
from lunar_ice_bpc.exact.core.branching import BranchContext
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.core.objective import flatten_objective_payload, objective_metadata
from lunar_ice_bpc.exact.solver.journey_driver import (
    enumerate_direct_journey_columns,
    solve_direct_journey_baseline,
)
from lunar_ice_bpc.io.instance_io import read_json
from lunar_ice_bpc.runners.b0_b1_ablation import B0_MODE, OBJECTIVE_CSV_COLUMNS


B3A_MODE = "B3A_full_universe_branch_audit"
B3B_MODE = "B3B_seeded_branch_price_tree"

B3_MODES = (
    B0_MODE,
    B2_PRODUCT_MODE,
    B2B_R3_MODE,
    B3A_MODE,
    B3B_MODE,
)

CSV_COLUMNS = (
    "matrix_group",
    "scale",
    "instance_id",
    "mode",
    "algorithm_status",
    "certificate_scope",
    "pricing_state",
    "uses_true_dual_bpc_certificate",
    "B0_direct_objective",
    "reference_solution_upper_bound",
    "reference_solution_upper_bound_source",
    "direct_bound_pruning_root_bound",
    "direct_bound_pruning_active",
    "journey_label_bound_pruned_count",
    *OBJECTIVE_CSV_COLUMNS,
    "B2B_R3_root_lp_bound",
    "B3_global_lb",
    "B3_global_ub",
    "B3_global_gap",
    "objective_diff_vs_B0",
    "B3_tree_closed",
    "BPC_TREE_OPTIMAL_count",
    "BPC_NODE_LP_CERTIFIED_count",
    "node_count",
    "evaluated_node_count",
    "open_node_count",
    "incomplete_node_count",
    "pruned_by_bound_count",
    "integer_incumbent_count",
    "branch_count",
    "max_depth_reached",
    "NO_FRACTIONAL_RF_PAIR_count",
    "manual_rc_audit_pass",
    "pricing_rc_audit_pass",
    "branch_pricing_audit_pass",
    "proof_debt_unreleased_count",
    "selected_harvest_addability_fail_count",
    "all_node_ledgers_valid",
    "direct_dp_used_as_bpc_certificate",
    "root_bound_gt_B0_violation",
    "tree_incumbent_diff_vs_B0",
    "certificate_scope_regression",
    "manual_rc_fail",
    "pricing_rc_fail",
    "branch_pricing_audit_fail",
    "proof_debt_unreleased_certified",
    "direct_dp_certificate_leak",
    "NO_FRACTIONAL_RF_PAIR_treated_as_integral",
    "open_node_but_tree_optimal",
    "incomplete_node_but_tree_optimal",
    "wall_time",
    "fail_closed_reason",
    "attempted_exception_type",
    "attempted_max_direct_tasks",
    "rmp_memory_precheck_failed",
    "rmp_memory_precheck_stage",
    "rmp_memory_precheck_reason",
    "rmp_memory_precheck_estimated_column_count",
    "rmp_memory_precheck_estimated_tableau_cells",
    "rmp_memory_precheck_cell_limit",
)


def run_b3_branch_tree_ablation(
    instances: Iterable[dict | str | Path],
    *,
    modes: Iterable[str] = B3_MODES,
    max_direct_tasks: int = 5,
    b2_max_rounds: int = 8,
    b3_max_rounds_per_node: int = 16,
    max_tree_nodes: int = 31,
    max_branch_depth: int = 4,
    matrix_group: str = "",
    row_time_limit_sec: float | None = None,
    allow_b3a_full_universe: bool = False,
) -> dict:
    rows: list[dict] = []
    selected_modes = tuple(modes)
    for item in instances:
        instance = _load_instance(item)
        b0_cache: dict | None = None
        b2b_r3_cache: dict | None = None
        for mode in selected_modes:
            if mode == B0_MODE:
                row, b0_cache = _run_guarded_row(
                    instance,
                    mode=mode,
                    max_direct_tasks=max_direct_tasks,
                    b2_max_rounds=b2_max_rounds,
                    b3_max_rounds_per_node=b3_max_rounds_per_node,
                    max_tree_nodes=max_tree_nodes,
                    max_branch_depth=max_branch_depth,
                    matrix_group=matrix_group,
                    row_time_limit_sec=row_time_limit_sec,
                    allow_b3a_full_universe=allow_b3a_full_universe,
                    b0_direct=None,
                    b2b_r3=None,
                )
            elif mode == B2B_R3_MODE:
                row, b2b_r3_cache = _run_guarded_row(
                    instance,
                    mode=mode,
                    max_direct_tasks=max_direct_tasks,
                    b2_max_rounds=b2_max_rounds,
                    b3_max_rounds_per_node=b3_max_rounds_per_node,
                    max_tree_nodes=max_tree_nodes,
                    max_branch_depth=max_branch_depth,
                    matrix_group=matrix_group,
                    row_time_limit_sec=row_time_limit_sec,
                    allow_b3a_full_universe=allow_b3a_full_universe,
                    b0_direct=b0_cache,
                    b2b_r3=None,
                )
            else:
                row, _ = _run_guarded_row(
                    instance,
                    mode=mode,
                    max_direct_tasks=max_direct_tasks,
                    b2_max_rounds=b2_max_rounds,
                    b3_max_rounds_per_node=b3_max_rounds_per_node,
                    max_tree_nodes=max_tree_nodes,
                    max_branch_depth=max_branch_depth,
                    matrix_group=matrix_group,
                    row_time_limit_sec=row_time_limit_sec,
                    allow_b3a_full_universe=allow_b3a_full_universe,
                    b0_direct=b0_cache,
                    b2b_r3=b2b_r3_cache,
                )
            rows.append(row)
    return _report_from_rows(rows)


def run_b3_branch_tree_ablation_matrix(
    *,
    manifest_path: str | Path,
    project_root: str | Path,
    scale5_limit: int = 20,
    scale10_limit: int = 5,
    scale20_probe_limit: int = 5,
    fail_closed_max_direct_tasks: int = 10,
    b2_max_rounds: int = 8,
    b3_max_rounds_per_node: int = 16,
    max_tree_nodes: int = 31,
    max_branch_depth: int = 4,
    row_time_limit_sec: float | None = 60.0,
) -> dict:
    project_root = Path(project_root)
    manifest_path = Path(manifest_path)
    if not manifest_path.is_absolute():
        manifest_path = project_root / manifest_path
    rows: list[dict] = []
    notes = [
        "B3 runner is serial by default to avoid concurrent branch/final-judge memory spikes.",
        "B3B uses B2B_R3 node pricing; B3A full-universe branch audit is diagnostic only.",
        "20-scale selected direct20 probe defaults to 5 instances; use --scale20-probe-limit 0 only for a skipped diagnostic.",
    ]

    scale5_all = _manifest_instance_paths(manifest_path, project_root, scale=5)
    scale5 = scale5_all[: max(0, int(scale5_limit))]
    rows.extend(
        run_b3_branch_tree_ablation(
            scale5,
            max_direct_tasks=5,
            b2_max_rounds=b2_max_rounds,
            b3_max_rounds_per_node=b3_max_rounds_per_node,
            max_tree_nodes=max_tree_nodes,
            max_branch_depth=max_branch_depth,
            matrix_group="5-scale full" if len(scale5) == len(scale5_all) else "5-scale selected",
            row_time_limit_sec=row_time_limit_sec,
            allow_b3a_full_universe=True,
        )["rows"]
    )

    scale10_all = _manifest_instance_paths(manifest_path, project_root, scale=10)
    scale10 = scale10_all[: max(0, int(scale10_limit))]
    rows.extend(
        run_b3_branch_tree_ablation(
            scale10,
            max_direct_tasks=10,
            b2_max_rounds=b2_max_rounds,
            b3_max_rounds_per_node=b3_max_rounds_per_node,
            max_tree_nodes=max_tree_nodes,
            max_branch_depth=max_branch_depth,
            matrix_group="10-scale selected5" if len(scale10) < len(scale10_all) else "10-scale full",
            row_time_limit_sec=row_time_limit_sec,
            allow_b3a_full_universe=False,
        )["rows"]
    )
    if len(scale10) < len(scale10_all):
        notes.append(f"10-scale ran selected {len(scale10)}/{len(scale10_all)} first; full run is deferred.")

    scale20_all = _manifest_instance_paths(manifest_path, project_root, scale=20)
    rows.extend(
        run_b3_branch_tree_ablation(
            scale20_all,
            modes=B3_MODES,
            max_direct_tasks=fail_closed_max_direct_tasks,
            b2_max_rounds=b2_max_rounds,
            b3_max_rounds_per_node=b3_max_rounds_per_node,
            max_tree_nodes=max_tree_nodes,
            max_branch_depth=max_branch_depth,
            matrix_group="20-scale fail-closed guard",
            row_time_limit_sec=row_time_limit_sec,
        )["rows"]
    )
    notes.append("20-scale fail-closed guard uses max_direct_tasks below 20; fail-closed is expected.")

    scale20_probe = scale20_all[: max(0, int(scale20_probe_limit))]
    if scale20_probe:
        rows.extend(
            run_b3_branch_tree_ablation(
                scale20_probe,
                modes=B3_MODES,
                max_direct_tasks=20,
                b2_max_rounds=b2_max_rounds,
                b3_max_rounds_per_node=b3_max_rounds_per_node,
                max_tree_nodes=max_tree_nodes,
                max_branch_depth=max_branch_depth,
                matrix_group="20-scale selected direct20 probe",
                row_time_limit_sec=row_time_limit_sec,
            )["rows"]
        )
        notes.append(f"20-scale selected direct20 probe used {len(scale20_probe)} instance(s).")

    scale30_all = _manifest_instance_paths(manifest_path, project_root, scale=30)
    rows.extend(
        run_b3_branch_tree_ablation(
            scale30_all,
            modes=B3_MODES,
            max_direct_tasks=fail_closed_max_direct_tasks,
            b2_max_rounds=b2_max_rounds,
            b3_max_rounds_per_node=b3_max_rounds_per_node,
            max_tree_nodes=max_tree_nodes,
            max_branch_depth=max_branch_depth,
            matrix_group="30-scale fail-closed diagnostic",
            row_time_limit_sec=row_time_limit_sec,
        )["rows"]
    )
    notes.append("30-scale diagnostic is expected to fail closed unless an explicit larger exact-pricing limit is selected.")

    report = _report_from_rows(rows)
    report["notes"] = notes
    return report


def write_b3_branch_tree_ablation_artifacts(
    report: dict,
    *,
    rows_csv: str | Path,
    summary_json: str | Path,
    report_md: str | Path,
) -> None:
    rows_csv = Path(rows_csv)
    summary_json = Path(summary_json)
    report_md = Path(report_md)
    rows_csv.parent.mkdir(parents=True, exist_ok=True)
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    report_md.parent.mkdir(parents=True, exist_ok=True)
    with rows_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow({key: _csv_value(row.get(key)) for key in CSV_COLUMNS})
    summary = {key: value for key, value in report.items() if key != "rows"}
    summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report_md.write_text(_markdown_report(report, rows_csv=rows_csv, summary_json=summary_json), encoding="utf-8")


def _run_guarded_row(
    instance: dict,
    *,
    mode: str,
    max_direct_tasks: int,
    b2_max_rounds: int,
    b3_max_rounds_per_node: int,
    max_tree_nodes: int,
    max_branch_depth: int,
    matrix_group: str,
    row_time_limit_sec: float | None,
    allow_b3a_full_universe: bool,
    b0_direct,
    b2b_r3,
) -> tuple[dict, dict | None]:
    scale = int(instance.get("scale") or len(instance.get("tasks") or []))
    instance_id = str(instance.get("instance_id") or "")
    data = load_lunar_ice_data(instance)
    start = perf_counter()
    try:
        raw = _call_with_timeout(
            lambda: _run_mode(
                instance,
                mode=mode,
                max_direct_tasks=max_direct_tasks,
                b2_max_rounds=b2_max_rounds,
                b3_max_rounds_per_node=b3_max_rounds_per_node,
                max_tree_nodes=max_tree_nodes,
                max_branch_depth=max_branch_depth,
                allow_b3a_full_universe=allow_b3a_full_universe,
                row_time_limit_sec=row_time_limit_sec,
                b0_direct=b0_direct,
                b2b_r3=b2b_r3,
            ),
            timeout_sec=row_time_limit_sec,
        )
        wall = perf_counter() - start
        row = _row_from_raw(
            raw,
            mode=mode,
            matrix_group=matrix_group,
            scale=scale,
            instance_id=instance_id,
            data=data,
            wall_time=wall,
        )
        cache_value = raw if mode in {B0_MODE, B2B_R3_MODE} else None
        return row, cache_value
    except TimeoutError:
        wall = perf_counter() - start
        row = _fail_closed_row(
            mode=mode,
            matrix_group=matrix_group,
            scale=scale,
            instance_id=instance_id,
            data=data,
            wall_time=wall,
            reason=f"row_time_limit_sec={row_time_limit_sec}",
            exception_type="TimeoutError",
            max_direct_tasks=max_direct_tasks,
        )
        return row, None
    except MemoryError:
        gc.collect()
        wall = perf_counter() - start
        row = _fail_closed_row(
            mode=mode,
            matrix_group=matrix_group,
            scale=scale,
            instance_id=instance_id,
            data=data,
            wall_time=wall,
            reason=(
                "row failed closed after MemoryError while attempting strict rerun "
                f"at max_direct_tasks={max_direct_tasks}"
            ),
            exception_type="MemoryError",
            max_direct_tasks=max_direct_tasks,
        )
        return row, None


def _run_mode(
    instance: dict,
    *,
    mode: str,
    max_direct_tasks: int,
    b2_max_rounds: int,
    b3_max_rounds_per_node: int,
    max_tree_nodes: int,
    max_branch_depth: int,
    allow_b3a_full_universe: bool,
    row_time_limit_sec: float | None,
    b0_direct,
    b2b_r3,
) -> dict:
    data = load_lunar_ice_data(instance)
    direct_wall_time_limit_sec = _inner_direct_wall_time_limit(row_time_limit_sec)
    if mode == B0_MODE:
        result = solve_direct_journey_baseline(
            data,
            max_exact_tasks=int(max_direct_tasks),
            wall_time_limit_sec=direct_wall_time_limit_sec,
        )
        return {
            "algorithm_status": result.status,
            "certificate_scope": result.certificate_scope,
            "pricing_state": "NOT_PRICED",
            "uses_true_dual_bpc_certificate": False,
            "B0_direct_objective": result.objective,
            "objective_breakdown": result.objective_breakdown,
            "reference_solution_upper_bound": result.reference_solution_upper_bound,
            "reference_solution_upper_bound_source": result.reference_solution_upper_bound_source,
            "direct_bound_pruning_root_bound": result.direct_bound_pruning_root_bound,
            "direct_bound_pruning_active": result.direct_bound_pruning_active,
            "journey_label_bound_pruned_count": result.journey_label_bound_pruned_count,
            "fail_closed_reason": "" if result.objective is not None else result.note,
        }
    if mode == B2_PRODUCT_MODE:
        product = solve_b2_product_exact_solver(
            data,
            max_direct_tasks=int(max_direct_tasks),
            wall_time_limit_sec=direct_wall_time_limit_sec,
        )
        return {**product, "B0_direct_objective": product.get("product_exact_objective")}
    if mode == B2B_R3_MODE:
        return solve_b2_pricing_tail_baseline(
            data,
            max_direct_tasks=int(max_direct_tasks),
            max_rounds=int(b2_max_rounds),
            wall_time_limit_sec=direct_wall_time_limit_sec,
            max_columns_per_round=512,
            mode=B2B_R3_MODE,
            previous_baseline=None,
        )
    if mode == B3A_MODE:
        if not allow_b3a_full_universe:
            b0_payload = b0_direct if isinstance(b0_direct, dict) else {}
            return {
                "algorithm_status": "BPC_INCOMPLETE_PRICING",
                "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                "pricing_state": "INCOMPLETE_LIMIT",
                "uses_true_dual_bpc_certificate": False,
                "B0_direct_objective": b0_payload.get("B0_direct_objective"),
                "objective_breakdown": b0_payload.get("objective_breakdown"),
                "fail_closed_reason": "B3A full-universe branch audit is disabled for this resource-guarded group.",
            }
        estimated_columns = representative_universe_column_count(len(data.task_ids))
        precheck = dense_rmp_memory_precheck(
            data,
            active_column_count=estimated_columns,
            stage="b3a_full_universe_node_active_rmp",
        )
        if precheck["rmp_memory_precheck_failed"]:
            b0_payload = b0_direct if isinstance(b0_direct, dict) else {}
            b0_objective = (
                b0_payload.get("B0_direct_objective")
                if b0_payload
                else getattr(b0_direct, "objective", None)
            )
            objective_breakdown = (
                b0_payload.get("objective_breakdown")
                if b0_payload
                else getattr(b0_direct, "objective_breakdown", None)
            )
            return {
                "algorithm_status": "BPC_INCOMPLETE_PRICING",
                "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                "pricing_state": "INCOMPLETE_LIMIT",
                "uses_true_dual_bpc_certificate": False,
                "B0_direct_objective": b0_objective,
                "objective_breakdown": objective_breakdown,
                "B3_global_lb": None,
                "B3_global_ub": b0_objective,
                "B3_tree_closed": False,
                "node_count": 0,
                "evaluated_node_count": 0,
                "BPC_NODE_LP_CERTIFIED_count": 0,
                "fail_closed_reason": str(precheck["rmp_memory_precheck_reason"]),
                "note": str(precheck["rmp_memory_precheck_reason"]),
                **precheck,
            }
        b0_baseline = _b0_baseline_or_solve(
            data,
            b0_direct=b0_direct,
            max_direct_tasks=max_direct_tasks,
            wall_time_limit_sec=direct_wall_time_limit_sec,
        )
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=int(max_direct_tasks)).columns
        node = _solve_b3_node(
            data,
            universe,
            _QueuedNode("node_000", None, 0, BranchContext()),
            b0_direct=b0_baseline,
            incumbent_objective_at_entry=None,
            max_direct_tasks=int(max_direct_tasks),
            max_rounds=int(b3_max_rounds_per_node),
            wall_time_limit_sec=direct_wall_time_limit_sec,
            negative_eps=1.0e-6,
            max_columns_per_round=512,
        )
        return {
            **node,
            "algorithm_status": "BPC_GAP_AVAILABLE" if node.get("node_lp_bound_official") else "BPC_INCOMPLETE_PRICING",
            "B0_direct_objective": getattr(b0_baseline, "objective", None),
            "objective_breakdown": getattr(b0_baseline, "objective_breakdown", None),
            "reference_solution_upper_bound": getattr(b0_baseline, "reference_solution_upper_bound", None),
            "reference_solution_upper_bound_source": getattr(
                b0_baseline, "reference_solution_upper_bound_source", ""
            ),
            "direct_bound_pruning_root_bound": getattr(b0_baseline, "direct_bound_pruning_root_bound", None),
            "direct_bound_pruning_active": getattr(b0_baseline, "direct_bound_pruning_active", False),
            "journey_label_bound_pruned_count": getattr(b0_baseline, "journey_label_bound_pruned_count", 0),
            "B3_global_lb": node.get("node_lp_bound"),
            "B3_global_ub": None,
            "B3_tree_closed": False,
            "node_count": 1,
            "evaluated_node_count": 1,
            "BPC_NODE_LP_CERTIFIED_count": int(bool(node.get("node_lp_bound_official"))),
            "fail_closed_reason": "" if node.get("node_lp_bound_official") else node.get("note"),
        }
    if mode == B3B_MODE:
        b0_baseline = _b0_baseline_or_solve(
            data,
            b0_direct=b0_direct,
            max_direct_tasks=max_direct_tasks,
            wall_time_limit_sec=direct_wall_time_limit_sec,
        )
        return solve_b3_branch_price_tree_baseline(
            data,
            b0_direct=b0_baseline,
            max_direct_tasks=int(max_direct_tasks),
            max_rounds_per_node=int(b3_max_rounds_per_node),
            wall_time_limit_sec=direct_wall_time_limit_sec,
            max_tree_nodes=int(max_tree_nodes),
            max_branch_depth=int(max_branch_depth),
            max_columns_per_round=512,
        )
    raise ValueError(f"unsupported B3 mode={mode!r}")


def _inner_direct_wall_time_limit(row_time_limit_sec: float | None) -> float | None:
    if row_time_limit_sec is None:
        return None
    limit = float(row_time_limit_sec)
    reserve = min(30.0, max(10.0, 0.02 * limit))
    return max(0.001, limit - reserve)


def _b0_baseline_or_solve(data, *, b0_direct, max_direct_tasks: int, wall_time_limit_sec: float | None = None):
    if b0_direct is not None and hasattr(b0_direct, "objective") and hasattr(b0_direct, "journeys"):
        return b0_direct
    return solve_direct_journey_baseline(
        data,
        max_exact_tasks=int(max_direct_tasks),
        wall_time_limit_sec=wall_time_limit_sec,
    )


def _row_from_raw(
    raw: dict,
    *,
    mode: str,
    matrix_group: str,
    scale: int,
    instance_id: str,
    data,
    wall_time: float,
) -> dict:
    b0 = raw.get("b0_ablation") if isinstance(raw.get("b0_ablation"), dict) else {}
    direct_objective = _float_or_none(
        raw.get("B0_direct_objective")
        if raw.get("B0_direct_objective") is not None
        else b0.get("direct_dp_objective")
    )
    objective_breakdown = raw.get("objective_breakdown") or b0.get("direct_dp_objective_breakdown")
    root_bound = _float_or_none(raw.get("root_lp_bound") or raw.get("root_rmp_objective") or raw.get("node_lp_bound"))
    global_ub = _float_or_none(raw.get("global_ub") or raw.get("incumbent_objective"))
    comparison_objective = _first_float(
        global_ub,
        raw.get("product_exact_objective"),
        raw.get("B3_global_ub"),
        raw.get("root_rmp_objective"),
        raw.get("root_lp_bound"),
        raw.get("node_lp_bound"),
    )
    objective_diff_vs_b0 = (
        None
        if comparison_objective is None or direct_objective is None
        else round(float(comparison_objective) - float(direct_objective), 9)
    )
    certificate_scope = str(raw.get("certificate_scope") or "")
    tree_optimal = certificate_scope == "BPC_TREE_OPTIMAL"
    node_lp_certified_count = int(raw.get("bpc_node_lp_certified_count") or raw.get("node_lp_certified_count") or 0)
    if node_lp_certified_count == 0 and certificate_scope in {"BPC_NODE_LP_CERTIFIED", "BPC_TREE_OPTIMAL"}:
        node_lp_certified_count = 1
    root_bound_gt_b0 = int(root_bound is not None and direct_objective is not None and root_bound > direct_objective + 1.0e-6)
    incumbent_diff_vs_b0 = int(
        tree_optimal and global_ub is not None and direct_objective is not None and abs(global_ub - direct_objective) > 1.0e-6
    )
    direct_leak = int(bool(raw.get("direct_dp_used_as_bpc_certificate") or b0.get("direct_dp_used_as_bpc_certificate")))
    no_rf_count = int(raw.get("no_fractional_rf_pair_count") or raw.get("NO_FRACTIONAL_RF_PAIR_count") or 0)
    open_nodes = int(raw.get("open_node_count") or 0)
    incomplete_nodes = int(raw.get("incomplete_node_count") or 0)
    fail_closed_reason = str(raw.get("fail_closed_reason") or "")
    if (
        not fail_closed_reason
        and certificate_scope in {"DIAGNOSTIC_RMP_BOUND", "DIAGNOSTIC_PRICING_FRONTIER", "FEASIBLE_INCUMBENT_ONLY"}
        and raw.get("note")
    ):
        fail_closed_reason = str(raw.get("note") or "")
    row = {
        "matrix_group": matrix_group,
        "scale": int(scale),
        "instance_id": instance_id or str(raw.get("instance_id") or ""),
        "mode": mode,
        "algorithm_status": raw.get("algorithm_status") or "",
        "certificate_scope": certificate_scope,
        "pricing_state": raw.get("pricing_state") or "",
        "uses_true_dual_bpc_certificate": bool(raw.get("uses_true_dual_bpc_certificate")),
        "B0_direct_objective": direct_objective,
        "reference_solution_upper_bound": raw.get("reference_solution_upper_bound")
        or b0.get("reference_solution_upper_bound"),
        "reference_solution_upper_bound_source": raw.get("reference_solution_upper_bound_source")
        or b0.get("reference_solution_upper_bound_source")
        or "",
        "direct_bound_pruning_root_bound": raw.get("direct_bound_pruning_root_bound")
        or b0.get("direct_bound_pruning_root_bound"),
        "direct_bound_pruning_active": bool(
            raw.get("direct_bound_pruning_active") or b0.get("direct_bound_pruning_active") or False
        ),
        "journey_label_bound_pruned_count": int(
            raw.get("journey_label_bound_pruned_count") or b0.get("journey_label_bound_pruned_count") or 0
        ),
        "B2B_R3_root_lp_bound": root_bound if mode == B2B_R3_MODE else None,
        "B3_global_lb": _float_or_none(raw.get("global_lower_bound") or raw.get("global_lb") or raw.get("B3_global_lb")),
        "B3_global_ub": global_ub,
        "B3_global_gap": _float_or_none(raw.get("global_gap")),
        "objective_diff_vs_B0": objective_diff_vs_b0,
        "B3_tree_closed": bool(raw.get("tree_closed") or raw.get("B3_tree_closed")),
        "BPC_TREE_OPTIMAL_count": int(raw.get("bpc_tree_optimal_count") or int(tree_optimal)),
        "BPC_NODE_LP_CERTIFIED_count": node_lp_certified_count,
        "node_count": int(raw.get("node_count") or 0),
        "evaluated_node_count": int(raw.get("evaluated_node_count") or 0),
        "open_node_count": open_nodes,
        "incomplete_node_count": incomplete_nodes,
        "pruned_by_bound_count": int(raw.get("pruned_by_bound_count") or 0),
        "integer_incumbent_count": int(raw.get("integer_incumbent_count") or 0),
        "branch_count": int(raw.get("branch_count") or 0),
        "max_depth_reached": _max_depth(raw),
        "NO_FRACTIONAL_RF_PAIR_count": no_rf_count,
        "manual_rc_audit_pass": raw.get("manual_rc_audit_pass"),
        "pricing_rc_audit_pass": raw.get("pricing_rc_audit_pass"),
        "branch_pricing_audit_pass": raw.get("branch_pricing_audit_pass", raw.get("all_priced_columns_satisfy_branch_context")),
        "proof_debt_unreleased_count": int(raw.get("proof_debt_unreleased_count") or 0),
        "selected_harvest_addability_fail_count": int(raw.get("selected_harvest_addability_fail_count") or 0),
        "all_node_ledgers_valid": bool(raw.get("all_certificate_ledgers_valid", raw.get("certificate_ledger", {}).get("valid", False))),
        "direct_dp_used_as_bpc_certificate": bool(direct_leak),
        "root_bound_gt_B0_violation": root_bound_gt_b0,
        "tree_incumbent_diff_vs_B0": incumbent_diff_vs_b0,
        "certificate_scope_regression": 0,
        "manual_rc_fail": int(certificate_scope in {"BPC_NODE_LP_CERTIFIED", "BPC_TREE_OPTIMAL"} and raw.get("manual_rc_audit_pass") is False),
        "pricing_rc_fail": int(certificate_scope in {"BPC_NODE_LP_CERTIFIED", "BPC_TREE_OPTIMAL"} and raw.get("pricing_rc_audit_pass") is False),
        "branch_pricing_audit_fail": int(
            certificate_scope in {"BPC_NODE_LP_CERTIFIED", "BPC_TREE_OPTIMAL"}
            and raw.get("branch_pricing_audit_pass", raw.get("all_priced_columns_satisfy_branch_context")) is False
        ),
        "proof_debt_unreleased_certified": int(
            certificate_scope in {"BPC_NODE_LP_CERTIFIED", "BPC_TREE_OPTIMAL"} and int(raw.get("proof_debt_unreleased_count") or 0) > 0
        ),
        "direct_dp_certificate_leak": direct_leak,
        "NO_FRACTIONAL_RF_PAIR_treated_as_integral": int(no_rf_count > 0 and tree_optimal),
        "open_node_but_tree_optimal": int(open_nodes > 0 and tree_optimal),
        "incomplete_node_but_tree_optimal": int(incomplete_nodes > 0 and tree_optimal),
        "wall_time": round(float(wall_time), 6),
        "fail_closed_reason": fail_closed_reason,
        "rmp_memory_precheck_failed": bool(raw.get("rmp_memory_precheck_failed")),
        "rmp_memory_precheck_stage": raw.get("rmp_memory_precheck_stage") or "",
        "rmp_memory_precheck_reason": raw.get("rmp_memory_precheck_reason") or "",
        "rmp_memory_precheck_estimated_column_count": raw.get("rmp_memory_precheck_estimated_column_count"),
        "rmp_memory_precheck_estimated_tableau_cells": raw.get("rmp_memory_precheck_estimated_tableau_cells"),
        "rmp_memory_precheck_cell_limit": raw.get("rmp_memory_precheck_cell_limit"),
    }
    row.update(flatten_objective_payload(objective_metadata(data), prefix="objective"))
    row.update(flatten_objective_payload(objective_breakdown, prefix="solution"))
    return row


def _report_from_rows(rows: list[dict]) -> dict:
    redline_keys = (
        "root_bound_gt_B0_violation",
        "tree_incumbent_diff_vs_B0",
        "certificate_scope_regression",
        "manual_rc_fail",
        "pricing_rc_fail",
        "branch_pricing_audit_fail",
        "proof_debt_unreleased_certified",
        "selected_harvest_addability_fail_count",
        "direct_dp_certificate_leak",
        "NO_FRACTIONAL_RF_PAIR_treated_as_integral",
        "open_node_but_tree_optimal",
        "incomplete_node_but_tree_optimal",
    )
    redlines = {
        (key if key.endswith("_count") else key + "_count"): sum(int(row.get(key) or 0) for row in rows)
        for key in redline_keys
    }
    by_group_mode: dict[tuple[str, str, int], list[dict]] = {}
    for row in rows:
        by_group_mode.setdefault((str(row["matrix_group"]), str(row["mode"]), int(row["scale"])), []).append(row)
    summary_rows = []
    for (group, mode, scale), group_rows in sorted(by_group_mode.items()):
        walls = [float(row["wall_time"]) for row in group_rows if row.get("wall_time") is not None]
        summary_rows.append(
            {
                "matrix_group": group,
                "scale": scale,
                "mode": mode,
                "runs": len(group_rows),
                "BPC_TREE_OPTIMAL_count": sum(int(row.get("BPC_TREE_OPTIMAL_count") or 0) for row in group_rows),
                "BPC_NODE_LP_CERTIFIED_count": sum(int(row.get("BPC_NODE_LP_CERTIFIED_count") or 0) for row in group_rows),
                "fail_closed_count": sum(1 for row in group_rows if row.get("fail_closed_reason")),
                "mean_wall": round(mean(walls), 6) if walls else None,
                "mean_node_count": round(mean(int(row.get("node_count") or 0) for row in group_rows), 6),
                "incomplete_node_count": sum(int(row.get("incomplete_node_count") or 0) for row in group_rows),
            }
        )
    scale5_b3b = [row for row in rows if row["matrix_group"] == "5-scale full" and row["mode"] == B3B_MODE]
    scale10_b2b = {
        str(row["instance_id"]): row
        for row in rows
        if str(row["matrix_group"]).startswith("10-scale") and row["mode"] == B2B_R3_MODE
    }
    scale10_b3b = [
        row for row in rows if str(row["matrix_group"]).startswith("10-scale") and row["mode"] == B3B_MODE
    ]
    scale10_regression_count = _scale10_regression_count(scale10_b2b, scale10_b3b)
    scale10_no_regression = bool(len(scale10_b3b) >= 5 and scale10_regression_count == 0)
    scale20_selected_b3b = [
        row for row in rows if row["matrix_group"] == "20-scale selected direct20 probe" and row["mode"] == B3B_MODE
    ]
    scale20_selected_clean = bool(
        len({str(row["instance_id"]) for row in scale20_selected_b3b}) >= 5
        and all(int(row.get("direct_dp_certificate_leak") or 0) == 0 for row in scale20_selected_b3b)
        and all(int(row.get("selected_harvest_addability_fail_count") or 0) == 0 for row in scale20_selected_b3b)
        and all(int(row.get("branch_pricing_audit_fail") or 0) == 0 for row in scale20_selected_b3b)
    )
    b3b_rows = [row for row in rows if row["mode"] == B3B_MODE]
    local_b3b_tree_optimal_count = sum(int(row.get("BPC_TREE_OPTIMAL_count") or 0) for row in b3b_rows)
    cross_scale_acceptance_evaluated = bool(scale5_b3b and scale10_b3b and scale20_selected_b3b)
    accepted = bool(
        cross_scale_acceptance_evaluated
        and scale5_b3b
        and len(scale5_b3b) == 20
        and all(int(row.get("BPC_TREE_OPTIMAL_count") or 0) == 1 for row in scale5_b3b)
        and scale10_no_regression
        and scale20_selected_clean
        and all(value == 0 for value in redlines.values())
    )
    return {
        "schema_version": "lunar_ice_bpc.b3_branch_tree_ablation_report.v1",
        "row_count": len(rows),
        "rows": rows,
        "summary_rows": summary_rows,
        "redlines": redlines,
        "acceptance": {
            "b3b_seeded_branch_price_tree_accepted": accepted,
            "scale5_full_b3b_tree_optimal_count": sum(int(row.get("BPC_TREE_OPTIMAL_count") or 0) for row in scale5_b3b),
            "scale5_full_b3b_run_count": len(scale5_b3b),
            "scale10_selected_b3b_run_count": len(scale10_b3b),
            "scale10_selected_no_regression_vs_b2b_r3": scale10_no_regression,
            "scale10_selected_regression_count": scale10_regression_count,
            "scale20_selected_direct20_b3b_run_count": len(scale20_selected_b3b),
            "scale20_selected_direct20_unique_instance_count": len(
                {str(row["instance_id"]) for row in scale20_selected_b3b}
            ),
            "scale20_selected_direct20_clean_diagnostics": scale20_selected_clean,
            "can_enter_b4": accepted,
            "cross_scale_acceptance_evaluated": cross_scale_acceptance_evaluated,
            "local_b3b_tree_optimal_count": local_b3b_tree_optimal_count,
            "local_b3b_run_count": len(b3b_rows),
            "local_b3b_all_tree_optimal": bool(
                b3b_rows and local_b3b_tree_optimal_count == len(b3b_rows)
            ),
        },
        "notes": [],
    }


def _markdown_report(report: dict, *, rows_csv: Path, summary_json: Path) -> str:
    lines = [
        "# B3 Branch-and-Price Tree 消融报告",
        "",
        "## Objective Boundary",
        "",
        "- Official objective: `1.0 * normalized_operating_cost + 1.0 * normalized_risk + 0.4 * normalized_weighted_completion_time`。",
        "- `makespan` 只作为 report/evaluation metric，不进入 pricing objective 或 reduced cost。",
        "- `BPC_TREE_OPTIMAL` 只证明 normalized additive objective 的 exact optimum，不证明 makespan-in-objective optimum。",
        "",
        "## Artifacts",
        "",
        f"- CSV rows: `{rows_csv}`",
        f"- JSON summary: `{summary_json}`",
        "",
        "## Redlines",
        "",
        "| metric | value | required |",
        "| --- | ---: | ---: |",
    ]
    for key, value in report["redlines"].items():
        lines.append(f"| {key} | {value} | 0 |")
    lines.extend(["", "## Summary", ""])
    lines.append("| scale | group | mode | runs | BPC tree | BPC node LP | fail-closed | mean wall | mean nodes | incomplete nodes |")
    lines.append("| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in report["summary_rows"]:
        lines.append(
            "| {scale} | {group} | {mode} | {runs} | {tree} | {node} | {fail} | {wall} | {nodes} | {inc} |".format(
                scale=row["scale"],
                group=row["matrix_group"],
                mode=row["mode"],
                runs=row["runs"],
                tree=row["BPC_TREE_OPTIMAL_count"],
                node=row["BPC_NODE_LP_CERTIFIED_count"],
                fail=row["fail_closed_count"],
                wall=row["mean_wall"],
                nodes=row["mean_node_count"],
                inc=row["incomplete_node_count"],
            )
        )
    acceptance = report["acceptance"]
    lines.extend(["", "## Acceptance Scope", ""])
    if acceptance.get("cross_scale_acceptance_evaluated"):
        lines.extend(
            [
                f"- Cross-scale B3B accepted: {acceptance['b3b_seeded_branch_price_tree_accepted']}.",
                f"- 5-scale full B3B BPC_TREE_OPTIMAL: {acceptance['scale5_full_b3b_tree_optimal_count']}/{acceptance['scale5_full_b3b_run_count']}.",
                f"- 10-scale selected no-regression vs B2B_R3: {acceptance['scale10_selected_no_regression_vs_b2b_r3']} "
                f"(regressions={acceptance['scale10_selected_regression_count']}, runs={acceptance['scale10_selected_b3b_run_count']}).",
                f"- 20-scale selected direct20 clean diagnostics: {acceptance['scale20_selected_direct20_clean_diagnostics']} "
                f"(unique instances={acceptance['scale20_selected_direct20_unique_instance_count']}).",
                f"- Can enter B4: {acceptance['can_enter_b4']}.",
            ]
        )
    else:
        lines.extend(
            [
                "- Cross-scale B3 acceptance is not evaluated in this artifact; this report may contain only one scale or one batch.",
                f"- Local B3B BPC_TREE_OPTIMAL: {acceptance['local_b3b_tree_optimal_count']}/{acceptance['local_b3b_run_count']}.",
                f"- Local B3B all tree optimal: {acceptance['local_b3b_all_tree_optimal']}.",
                "- Use the master normalized objective report for cross-scale B0/B3B alignment and final acceptance boundaries.",
            ]
        )
    lines.extend(["", "## Notes", ""])
    for note in report.get("notes") or []:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def _manifest_instance_paths(manifest_path: Path, project_root: Path, *, scale: int) -> list[Path]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = [
        row
        for row in manifest.get("instances", [])
        if int(row.get("scale") or 0) == int(scale) and str(row.get("status") or "") == "accepted"
    ]
    paths = []
    for row in sorted(rows, key=lambda item: str(item.get("instance_id") or "")):
        path = Path(row["path"])
        paths.append(path if path.is_absolute() else project_root / path)
    return paths


def _load_instance(item: dict | str | Path) -> dict:
    if isinstance(item, dict):
        return item
    return read_json(item)


def _call_with_timeout(fn: Callable[[], dict], *, timeout_sec: float | None) -> dict:
    if timeout_sec is None or timeout_sec <= 0:
        return fn()

    def _raise_timeout(_signum, _frame) -> None:
        raise TimeoutError("row time limit exceeded")

    old_handler = signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, float(timeout_sec))
    try:
        return fn()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, old_handler)


def _fail_closed_row(
    *,
    mode: str,
    matrix_group: str,
    scale: int,
    instance_id: str,
    data,
    wall_time: float,
    reason: str,
    exception_type: str = "",
    max_direct_tasks: int | None = None,
) -> dict:
    row = {
        "matrix_group": matrix_group,
        "scale": int(scale),
        "instance_id": instance_id,
        "mode": mode,
        "algorithm_status": "BPC_INCOMPLETE_PRICING",
        "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
        "pricing_state": "INCOMPLETE_LIMIT",
        "uses_true_dual_bpc_certificate": False,
        "BPC_TREE_OPTIMAL_count": 0,
        "BPC_NODE_LP_CERTIFIED_count": 0,
        "wall_time": round(float(wall_time), 6),
        "fail_closed_reason": reason,
        "attempted_exception_type": str(exception_type or ""),
        "attempted_max_direct_tasks": max_direct_tasks,
        "rmp_memory_precheck_failed": False,
        "rmp_memory_precheck_stage": "",
        "rmp_memory_precheck_reason": "",
        "rmp_memory_precheck_estimated_column_count": None,
        "rmp_memory_precheck_estimated_tableau_cells": None,
        "rmp_memory_precheck_cell_limit": None,
    }
    row.update(flatten_objective_payload(objective_metadata(data), prefix="objective"))
    return row


def _csv_value(value):
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True)
    return value


def _float_or_none(value) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _first_float(*values) -> float | None:
    for value in values:
        result = _float_or_none(value)
        if result is not None:
            return result
    return None


def _certificate_rank(scope: str) -> int:
    ranks = {
        "": 0,
        "DIAGNOSTIC_PRICING_FRONTIER": 0,
        "FEASIBLE_INCUMBENT_ONLY": 0,
        "DIAGNOSTIC_RMP_BOUND": 1,
        "BPC_NODE_LP_CERTIFIED": 2,
        "BPC_TREE_OPTIMAL": 3,
    }
    return ranks.get(str(scope or ""), 0)


def _scale10_regression_count(b2b_rows: dict[str, dict], b3b_rows: list[dict]) -> int:
    regressions = 0
    for row in b3b_rows:
        instance_id = str(row["instance_id"])
        b2b = b2b_rows.get(instance_id)
        if b2b is None:
            regressions += 1
            continue
        if _certificate_rank(str(row.get("certificate_scope") or "")) < _certificate_rank(
            str(b2b.get("certificate_scope") or "")
        ):
            regressions += 1
    return regressions


def _max_depth(raw: dict) -> int:
    if raw.get("max_depth_reached") is not None:
        return int(raw.get("max_depth_reached") or 0)
    nodes = raw.get("nodes") if isinstance(raw.get("nodes"), list) else []
    return max((int(node.get("depth") or 0) for node in nodes), default=0)
