"""B0/B1 scope and certificate ablation runner."""

from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
import gc
import json
from pathlib import Path
import signal
from statistics import mean
from time import perf_counter
from typing import Callable, Iterable

from lunar_ice_bpc.exact.bpc.solver.root_node_solver import (
    build_b1_seed_columns,
    solve_b1_root_node_baseline,
    _reference_seed_direct_placeholder,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.core.objective import flatten_objective_payload, objective_metadata
from lunar_ice_bpc.exact.solver.journey_driver import solve_direct_journey_baseline
from lunar_ice_bpc.io.instance_io import read_json, write_json


B0_MODE = "B0_pure_direct_dp"
B1A_MODE = "B1A_full_universe_root_audit"
B1B_MODE = "B1B_seeded_root_CG"

OBJECTIVE_CSV_COLUMNS = (
    "objective_schema_version",
    "objective_mode",
    "objective_reference_cost",
    "objective_reference_risk",
    "objective_reference_completion",
    "objective_reference_makespan_metric",
    "objective_makespan_enters_pricing_objective",
    "solution_raw_operating_cost",
    "solution_raw_risk",
    "solution_raw_weighted_completion_time",
    "solution_raw_makespan",
    "solution_raw_objective_unscaled_weighted_sum",
    "solution_normalized_operating_cost",
    "solution_normalized_risk",
    "solution_normalized_weighted_completion_time",
    "solution_normalized_makespan_metric",
    "solution_normalized_objective",
    "solution_official_objective",
    "solution_makespan_enters_pricing_objective",
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
    "bpc_certificate_status",
    "official_lower_bound_source",
    "official_lower_bound_scope",
    "best_diagnostic_bound_source",
    "B0_direct_objective",
    "reference_solution_upper_bound",
    "reference_solution_upper_bound_source",
    "direct_bound_pruning_root_bound",
    "direct_bound_pruning_active",
    "journey_label_bound_pruned_count",
    *OBJECTIVE_CSV_COLUMNS,
    "B1_root_lp_bound",
    "root_lp_bound_official",
    "root_lp_bound_le_direct_dp_integer_objective",
    "root_lp_vs_direct_dp_gap",
    "integral_root",
    "pricing_round_count",
    "added_column_count",
    "final_judge_status",
    "final_judge_exact_status",
    "final_judge_compact_pricing_phase",
    "final_judge_negative_search_status",
    "final_judge_negative_search_wall_time",
    "final_judge_negative_search_best_reduced_cost",
    "final_judge_negative_search_dual_bound",
    "final_judge_negative_search_negative_found",
    "final_judge_compact_negative_batch_found_count",
    "final_judge_compact_negative_batch_search_call_count",
    "final_judge_compact_negative_no_good_scope",
    "final_judge_forbidden_task_set_count",
    "final_judge_optimization_proof_status",
    "final_judge_optimization_proof_wall_time",
    "final_judge_optimization_proof_best_reduced_cost",
    "final_judge_optimization_proof_dual_bound",
    "final_judge_call_count",
    "final_judge_total_wall_time",
    "final_judge_found_negative_count",
    "final_judge_best_negative_reduced_cost",
    "final_judge_incomplete_count",
    "final_judge_certified_no_negative_count",
    "pricing_history_json",
    "final_judge_wall_time",
    "final_judge_generated_journey_count",
    "final_judge_generated_sortie_count",
    "final_judge_route_template_count",
    "final_judge_pareto_label_count",
    "final_judge_best_reduced_cost",
    "final_judge_dual_bound",
    "final_judge_mip_gap",
    "final_judge_solver_backend",
    "final_judge_model_status_name",
    "final_judge_variable_count",
    "final_judge_constraint_count",
    "final_judge_pricing_complete_by_compact_milp",
    "final_judge_negative_feasibility_search_enabled",
    "final_judge_mtz_connectivity_enabled",
    "final_judge_mtz_endpoint_order_cuts_enabled",
    "final_judge_mtz_endpoint_order_cut_count",
    "final_judge_pair_adjacency_cuts_enabled",
    "final_judge_pair_adjacency_cut_count",
    "final_judge_sortie_slots_per_journey",
    "final_judge_sortie_slot_bound_source",
    "final_judge_sortie_slot_horizon_count_bound",
    "final_judge_sortie_slot_latest_start_count_bound",
    "final_judge_time_window_arc_pruning_enabled",
    "final_judge_time_window_arc_option_count",
    "final_judge_time_window_impossible_arc_option_count",
    "final_judge_representative_universe_total_count",
    "final_judge_representative_universe_audited_count",
    "final_judge_representative_universe_completion_ratio",
    "final_judge_representative_universe_remaining_count",
    "manual_rc_audit_pass",
    "pricing_rc_audit_pass",
    "proof_debt_unreleased_count",
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
    "direct_root_official_leak",
    "b1_mode",
    "seed_mode",
    "solve_b0_direct_first",
    "initial_column_count",
    "feasible_incumbent_seed_source",
    "feasible_incumbent_seed_column_count",
    "feasible_incumbent_seed_used_as_certificate",
    "full_universe_column_count",
    "full_universe_preloaded",
)


def run_b0_b1_ablation(
    instances: Iterable[dict | str | Path],
    *,
    modes: Iterable[str] = (B0_MODE, B1A_MODE, B1B_MODE),
    max_direct_tasks: int = 5,
    b1_max_rounds: int = 8,
    matrix_group: str = "",
    row_time_limit_sec: float | None = None,
    max_workers: int = 1,
    b1_solve_b0_direct_first: bool = True,
) -> dict:
    selected_modes = tuple(modes)
    jobs: list[dict] = []
    for item in instances:
        if B0_MODE in selected_modes:
            jobs.append(
                _job(
                    item=item,
                    mode=B0_MODE,
                    seed_mode="",
                    max_direct_tasks=max_direct_tasks,
                    max_rounds=b1_max_rounds,
                    matrix_group=matrix_group,
                    row_time_limit_sec=row_time_limit_sec,
                    solve_b0_direct_first=b1_solve_b0_direct_first,
                )
            )
        if B1A_MODE in selected_modes:
            jobs.append(
                _job(
                    item=item,
                    mode=B1A_MODE,
                    seed_mode="full_universe",
                    max_direct_tasks=max_direct_tasks,
                    max_rounds=b1_max_rounds,
                    matrix_group=matrix_group,
                    row_time_limit_sec=row_time_limit_sec,
                    solve_b0_direct_first=b1_solve_b0_direct_first,
                )
            )
        if B1B_MODE in selected_modes:
            jobs.append(
                _job(
                    item=item,
                    mode=B1B_MODE,
                    seed_mode="b0_incumbent_plus_singletons",
                    max_direct_tasks=max_direct_tasks,
                    max_rounds=b1_max_rounds,
                    matrix_group=matrix_group,
                    row_time_limit_sec=row_time_limit_sec,
                    solve_b0_direct_first=b1_solve_b0_direct_first,
                )
            )
    rows = _run_jobs(jobs, max_workers=max_workers)
    return _report_from_rows(rows)


def run_b0_b1_ablation_matrix(
    *,
    manifest_path: str | Path,
    project_root: str | Path,
    scale10_limit: int = 5,
    scale10_row_time_limit_sec: float | None = 60.0,
    scale20_probe_limit: int = 5,
    direct20_probe_time_limit_sec: float = 120.0,
    fail_closed_max_direct_tasks: int = 10,
    b1_max_rounds: int = 8,
    max_workers: int = 1,
) -> dict:
    project_root = Path(project_root)
    manifest_path = Path(manifest_path)
    if not manifest_path.is_absolute():
        manifest_path = project_root / manifest_path
    rows: list[dict] = []
    matrix_notes: list[str] = []

    scale5 = _manifest_instance_paths(manifest_path, project_root, scale=5)
    rows.extend(
        run_b0_b1_ablation(
            scale5,
            max_direct_tasks=5,
            b1_max_rounds=b1_max_rounds,
            matrix_group="5-scale full",
            max_workers=max_workers,
        )["rows"]
    )

    scale10_all = _manifest_instance_paths(manifest_path, project_root, scale=10)
    scale10 = scale10_all[: max(0, int(scale10_limit))]
    rows.extend(
        run_b0_b1_ablation(
            scale10,
            max_direct_tasks=10,
            b1_max_rounds=b1_max_rounds,
            matrix_group="10-scale selected5" if len(scale10) < len(scale10_all) else "10-scale full",
            row_time_limit_sec=scale10_row_time_limit_sec,
            max_workers=max_workers,
        )["rows"]
    )
    if len(scale10) < len(scale10_all):
        matrix_notes.append(
            f"10-scale ran selected {len(scale10)}/{len(scale10_all)} first; run full after this gate if wall time is acceptable."
        )

    scale20_all = _manifest_instance_paths(manifest_path, project_root, scale=20)
    rows.extend(
        run_b0_b1_ablation(
            scale20_all,
            max_direct_tasks=int(fail_closed_max_direct_tasks),
            b1_max_rounds=b1_max_rounds,
            matrix_group="20-scale fail-closed guard",
            max_workers=max_workers,
        )["rows"]
    )
    matrix_notes.append(
        "20-scale fail-closed guard deliberately sets max_direct_tasks below 20; "
        "B0 optimal=0 in that group is an expected skip, not evidence that direct20 B0 fails."
    )

    scale20_probe = scale20_all[: max(0, int(scale20_probe_limit))]
    if scale20_probe:
        rows.extend(
            run_b0_b1_ablation(
                scale20_probe,
                modes=(B0_MODE, B1A_MODE, B1B_MODE),
                max_direct_tasks=20,
                b1_max_rounds=b1_max_rounds,
                matrix_group="20-scale selected direct20 probe",
                row_time_limit_sec=float(direct20_probe_time_limit_sec),
                max_workers=max_workers,
            )["rows"]
        )
        matrix_notes.append(
            f"20-scale direct20 probe used {len(scale20_probe)} selected instance(s), modes B0/B1A/B1B, "
            f"with per-row timeout {direct20_probe_time_limit_sec}s."
        )

    scale30_all = _manifest_instance_paths(manifest_path, project_root, scale=30)
    rows.extend(
        run_b0_b1_ablation(
            scale30_all,
            max_direct_tasks=int(fail_closed_max_direct_tasks),
            b1_max_rounds=b1_max_rounds,
            matrix_group="30-scale fail-closed diagnostic",
            max_workers=max_workers,
        )["rows"]
    )

    report = _report_from_rows(rows)
    report["matrix"] = {
        "manifest_path": str(manifest_path),
        "scale5_count": len(scale5),
        "scale10_selected_count": len(scale10),
        "scale10_total_count": len(scale10_all),
        "scale10_row_time_limit_sec": scale10_row_time_limit_sec,
        "scale20_fail_closed_count": len(scale20_all),
        "scale20_probe_count": len(scale20_probe),
        "scale20_probe_modes": [B0_MODE, B1A_MODE, B1B_MODE],
        "scale30_count": len(scale30_all),
        "fail_closed_max_direct_tasks": int(fail_closed_max_direct_tasks),
        "direct20_probe_time_limit_sec": float(direct20_probe_time_limit_sec),
        "max_workers": int(max_workers),
        "notes": matrix_notes,
    }
    return report


def write_b0_b1_ablation_artifacts(
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
    with rows_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in report.get("rows", []):
            writer.writerow({key: row.get(key) for key in CSV_COLUMNS})
    write_json(summary_json, report)
    report_md.write_text(render_b0_b1_ablation_markdown(report, rows_csv=rows_csv, summary_json=summary_json), encoding="utf-8")


def render_b0_b1_ablation_markdown(report: dict, *, rows_csv: str | Path, summary_json: str | Path) -> str:
    redlines = report.get("redlines") or {}
    matrix = report.get("matrix") or {}
    lines = [
        "# B0/B1 proof-safe 消融报告",
        "",
        "## 完成范围",
        "",
        "- B0 accepted evidence: 5-scale full、10-scale selected direct-DP、20-scale selected direct20 probe。",
        "- B1 accepted: 5-scale proof-safe root closure。",
        "- B1 not yet accepted: 10/20 root closure；当前 selected 10 与 selected direct20 仍由 row timeout fail-closed。",
        "- B2 entry purpose: target 10-scale B1 timeout / pricing-tail / addability / final judge cost，不声称 B1 已在 10/20 完成。",
        "- B2/B3/B4/B5 文件若存在，仅视为 scaffold / preliminary module，不纳入当前完成状态。",
        "- 本报告不启用 harvesting、GAT、cuts 或 full branch tree。",
        "",
        "## Objective Boundary",
        "",
        "- Official objective: `1.0 * normalized_operating_cost + 1.0 * normalized_risk + 0.4 * normalized_weighted_completion_time`。",
        "- `makespan` 只作为 report/evaluation metric，不进入 pricing objective 或 reduced cost。",
        "- CSV 中 `objective_*` 为 per-instance reference；`solution_*` 为 incumbent/direct-DP 解的 raw/normalized 分解。",
        "- `solution_normalized_objective`/`solution_official_objective` 是本轮 official objective；"
        "`solution_raw_objective_unscaled_weighted_sum` 只用于尺度诊断，不参与 reduced cost 或证书判定。",
        "",
        "## 产物",
        "",
        f"- CSV rows: `{rows_csv}`",
        f"- JSON summary: `{summary_json}`",
        "",
        "## 矩阵",
        "",
        f"- max_workers: {matrix.get('max_workers', 1)}。",
        f"- 5-scale full: {matrix.get('scale5_count', 0)} instances。",
        f"- 10-scale: {matrix.get('scale10_selected_count', 0)}/{matrix.get('scale10_total_count', 0)} instances。",
        f"- 10-scale row timeout: {matrix.get('scale10_row_time_limit_sec')} 秒。",
        f"- 20-scale fail-closed guard: {matrix.get('scale20_fail_closed_count', 0)} instances。",
        f"- 20-scale selected direct20 probe: {matrix.get('scale20_probe_count', 0)} instances。",
        f"- 20-scale selected direct20 probe modes: {', '.join(matrix.get('scale20_probe_modes') or [])}。",
        f"- 30-scale fail-closed diagnostic: {matrix.get('scale30_count', 0)} instances。",
        "- 20-scale fail-closed guard 中的 B0 optimal=0 是预期行为；该组不测试 direct20 能力，只测试 task_count > max_direct_tasks 时是否 fail-closed。",
        "",
        "## 红线",
        "",
        "| metric | value | required |",
        "| --- | ---: | ---: |",
        f"| root_bound_gt_B0_violation_count | {redlines.get('root_bound_gt_B0_violation_count')} | 0 |",
        f"| direct_root_official_leak_count | {redlines.get('direct_root_official_leak_count')} | 0 |",
        f"| manual_rc_fail_count | {redlines.get('manual_rc_fail_count')} | 0 |",
        f"| pricing_rc_fail_count | {redlines.get('pricing_rc_fail_count')} | 0 |",
        "",
        "## 汇总",
        "",
        "| scale | group | mode | runs | B0 optimal | BPC node LP | fail-closed | bound>B0 | manual RC fail | pricing RC fail | direct-root leak | mean wall | p90 wall | mean added | mean rounds |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report.get("summary_rows", []):
        lines.append(
            "| {scale} | {matrix_group} | {mode} | {run_count} | {B0_direct_optimal_count} | "
            "{BPC_NODE_LP_CERTIFIED_count} | {fail_closed_count} | {root_bound_gt_B0_violation_count} | "
            "{manual_rc_fail_count} | {pricing_rc_fail_count} | {direct_root_official_leak_count} | "
            "{mean_wall_time} | {p90_wall_time} | {mean_added_columns} | {mean_pricing_rounds} |".format(**row)
        )
    direct20_rows = [
        row for row in report.get("rows", [])
        if row.get("matrix_group") == "20-scale selected direct20 probe"
    ]
    if direct20_rows:
        lines.extend(["", "## 20-scale direct20 对照", ""])
        by_instance: dict[str, list[dict]] = defaultdict(list)
        for row in direct20_rows:
            by_instance[str(row.get("instance_id"))].append(row)
        for instance_id, instance_rows in by_instance.items():
            by_mode = {row.get("mode"): row for row in instance_rows}
            b0 = by_mode.get(B0_MODE)
            b1a = by_mode.get(B1A_MODE)
            b1b = by_mode.get(B1B_MODE)
            if b0:
                lines.append(
                    f"- `{instance_id}` B0 direct-DP: {b0.get('algorithm_status')} / "
                    f"{b0.get('certificate_scope')}，wall={b0.get('wall_time')}s。"
                )
            if b1a:
                lines.append(
                    f"- `{instance_id}` B1A full-universe root audit: {b1a.get('algorithm_status')} / "
                    f"{b1a.get('certificate_scope')}，wall={b1a.get('wall_time')}s，reason={b1a.get('fail_closed_reason')}。"
                )
            if b1b:
                lines.append(
                    f"- `{instance_id}` B1B seeded-CG: {b1b.get('algorithm_status')} / "
                    f"{b1b.get('certificate_scope')}，wall={b1b.get('wall_time')}s，reason={b1b.get('fail_closed_reason')}。"
                )
        lines.append("- 结论：同一 selected direct20 instance 上 direct-DP integer oracle 能闭合；当前瓶颈是 B1 root pricing closure / final judge 成本。")
    lines.extend(["", "## B1B seeded-CG 说明", ""])
    b1b_rows = [row for row in report.get("rows", []) if row.get("mode") == B1B_MODE]
    zero_added = [row for row in b1b_rows if _float(row.get("added_column_count")) == 0.0]
    positive_added = [row for row in b1b_rows if (_float(row.get("added_column_count")) or 0.0) > 0.0]
    lines.append(f"- B1B rows: {len(b1b_rows)}; added_column_count > 0 rows: {len(positive_added)}; added_column_count = 0 rows: {len(zero_added)}。")
    if zero_added:
        closed_zero = [
            row for row in zero_added
            if row.get("certificate_scope") == "BPC_NODE_LP_CERTIFIED"
            and row.get("pricing_round_count") == 1
        ]
        timeout_zero = [
            row for row in zero_added
            if "row_time_limit_sec" in str(row.get("fail_closed_reason") or "")
        ]
        over_limit_zero = [
            row for row in zero_added
            if "exceeds max_direct_tasks" in str(row.get("fail_closed_reason") or "")
        ]
        explained = set(map(id, closed_zero + timeout_zero + over_limit_zero))
        failed_zero = [row for row in zero_added if id(row) not in explained]
        lines.append(f"- 0-add 且一轮闭合 rows: {len(closed_zero)}，解释为 seed pool 已足够或 root already closed。")
        lines.append(f"- 0-add 且 task_count 超过 max_direct_tasks rows: {len(over_limit_zero)}，解释为 fail-closed guard。")
        lines.append(f"- 0-add 且触发行超时 rows: {len(timeout_zero)}，解释为 direct exhaustive pricing 成本过高，本轮不能声称 B1B closure。")
        lines.append(f"- 0-add 且其他未闭合 rows: {len(failed_zero)}，需查看 fail_closed_reason，不能解释为 B1B CG 成功。")
    else:
        lines.append("- B1B 没有 0-add rows；seeded-column CG 已实际 add columns。")
    if matrix.get("notes"):
        lines.extend(["", "## 备注", ""])
        for note in matrix["notes"]:
            lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "## 结论边界",
            "",
            "- B0 pure 路径不得产生 true-dual BPC certificate。",
            "- B1A/B1B 只有 true-dual final judge closure、manual RC audit、pricing RC audit、proof debt gate 全通过时，才允许 `BPC_NODE_LP_CERTIFIED`。",
            "- `direct_fixed_graph_root_lp` 只允许作为 diagnostic audit，不允许进入 official BPC bound。",
            "- B1A full-universe 若未来加入 `full_universe_membership_rc_audit`，必须先证明 initial columns 等于 complete fixed pricing universe；否则仍必须走 true-dual final judge。",
        ]
    )
    return "\n".join(lines) + "\n"


def _report_from_rows(rows: list[dict]) -> dict:
    summary_rows = _summary_rows(rows)
    return {
        "schema_version": "lunar_ice_bpc.b0_b1_ablation.v1",
        "accepted_baseline_layers": ["B0", "B1"],
        "not_accepted_layers": ["B2", "B3", "B4", "B5"],
        "b2_entry_blocked_until": [
            "B0/B1 5-scale ablation redlines pass",
            "B1B seeded-column root CG closes from a non-full-universe seed pool",
        ],
        "row_count": len(rows),
        "rows": rows,
        "summary_rows": summary_rows,
        "redlines": _redlines(summary_rows),
    }


def _run_b0_row(
    instance: dict,
    *,
    max_direct_tasks: int,
    matrix_group: str = "",
    wall_time_limit_sec: float | None = None,
    solve_b0_direct_first: bool = True,
) -> dict:
    data = load_lunar_ice_data(instance)
    start = perf_counter()
    b0 = solve_direct_journey_baseline(
        data,
        max_exact_tasks=int(max_direct_tasks),
        wall_time_limit_sec=wall_time_limit_sec,
    )
    elapsed = perf_counter() - start
    fail_reason = "" if b0.status == "DIRECT_DP_BASELINE_OPTIMAL" else b0.note
    row = _base_row(data, mode=B0_MODE, matrix_group=matrix_group)
    row.update(
        {
            "algorithm_status": b0.status,
            "certificate_scope": b0.certificate_scope,
            "pricing_state": "",
            "uses_true_dual_bpc_certificate": False,
            "bpc_certificate_status": "NOT_PORTED_TRUE_DUAL_BPC",
            "official_lower_bound_source": "analytic_relaxation" if b0.objective is not None else None,
            "official_lower_bound_scope": "global_relaxation" if b0.objective is not None else None,
            "best_diagnostic_bound_source": "direct_fixed_graph_root_lp" if b0.objective is not None else None,
            "B0_direct_objective": b0.objective,
            "reference_solution_upper_bound": b0.reference_solution_upper_bound,
            "reference_solution_upper_bound_source": b0.reference_solution_upper_bound_source,
            "direct_bound_pruning_root_bound": b0.direct_bound_pruning_root_bound,
            "direct_bound_pruning_active": b0.direct_bound_pruning_active,
            "journey_label_bound_pruned_count": b0.journey_label_bound_pruned_count,
            "B1_root_lp_bound": None,
            "root_lp_bound_official": False,
            "root_lp_bound_le_direct_dp_integer_objective": None,
            "root_lp_vs_direct_dp_gap": None,
            "integral_root": None,
            "pricing_round_count": 0,
            "added_column_count": 0,
            "manual_rc_audit_pass": None,
            "pricing_rc_audit_pass": None,
            "proof_debt_unreleased_count": 0,
            "wall_time": round(elapsed, 6),
            "fail_closed_reason": fail_reason,
            "direct_root_official_leak": False,
        }
    )
    row.update(flatten_objective_payload(b0.objective_breakdown, prefix="solution"))
    return row


def _compact_negative_phase_summary(compact_phases: dict) -> dict:
    direct = compact_phases.get("negative_feasibility_search")
    if isinstance(direct, dict) and direct:
        return direct
    rows = [
        value
        for key, value in sorted(compact_phases.items())
        if str(key).startswith("negative_feasibility_search_") and isinstance(value, dict)
    ]
    if not rows:
        return {}
    best_values = [_float_or_none(row.get("best_reduced_cost")) for row in rows]
    best_values = [value for value in best_values if value is not None]
    dual_bounds = [_float_or_none(row.get("dual_bound")) for row in rows]
    dual_bounds = [value for value in dual_bounds if value is not None]
    wall_times = [_float_or_none(row.get("wall_time_sec")) for row in rows]
    return {
        "status": rows[-1].get("status"),
        "wall_time_sec": round(sum(value for value in wall_times if value is not None), 6),
        "best_reduced_cost": min(best_values) if best_values else None,
        "dual_bound": min(dual_bounds) if dual_bounds else None,
        "negative_found": any(bool(row.get("negative_found")) for row in rows),
    }


def _float_or_none(value) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _run_b1_row(
    instance: dict,
    *,
    mode: str,
    seed_mode: str,
    max_direct_tasks: int,
    max_rounds: int,
    matrix_group: str = "",
    wall_time_limit_sec: float | None = None,
    solve_b0_direct_first: bool = True,
) -> dict:
    data = load_lunar_ice_data(instance)
    start = perf_counter()
    result = solve_b1_root_node_baseline(
        data,
        max_direct_tasks=int(max_direct_tasks),
        max_rounds=int(max_rounds),
        wall_time_limit_sec=wall_time_limit_sec,
        seed_mode=seed_mode,
        solve_b0_direct_first=solve_b0_direct_first,
    )
    elapsed = perf_counter() - start
    certified = result.get("certificate_scope") == "BPC_NODE_LP_CERTIFIED"
    official = bool(result.get("root_lp_bound_official"))
    manual_rc_audit_pass = result.get("manual_rc_audit_pass")
    pricing_rc_audit_pass = result.get("pricing_rc_audit_pass")
    if result.get("root_rmp_status") is None and result.get("final_judge_status") is None:
        manual_rc_audit_pass = None
        pricing_rc_audit_pass = None
    final_judge = result.get("final_judge") or {}
    compact_phases = final_judge.get("compact_pricing_phase_payloads") or {}
    negative_phase = _compact_negative_phase_summary(compact_phases)
    optimization_phase = compact_phases.get("optimization_proof") or {}
    row = _base_row(data, mode=mode, matrix_group=matrix_group)
    row.update(
        {
            "algorithm_status": result.get("algorithm_status"),
            "certificate_scope": result.get("certificate_scope"),
            "pricing_state": result.get("pricing_state"),
            "uses_true_dual_bpc_certificate": bool(result.get("uses_true_dual_bpc_certificate")),
            "bpc_certificate_status": "CERTIFIED_NO_NEGATIVE" if certified else "NOT_PORTED_TRUE_DUAL_BPC",
            "official_lower_bound_source": "b1_root_true_dual_pricing_closure" if official else None,
            "official_lower_bound_scope": "BPC_NODE_LP_CERTIFIED" if official else None,
            "best_diagnostic_bound_source": None if official else "b1_restricted_root_rmp",
            "B0_direct_objective": (result.get("b0_ablation") or {}).get("direct_dp_objective"),
            "reference_solution_upper_bound": (result.get("b0_ablation") or {}).get("reference_solution_upper_bound"),
            "reference_solution_upper_bound_source": (result.get("b0_ablation") or {}).get(
                "reference_solution_upper_bound_source"
            ),
            "direct_bound_pruning_root_bound": (result.get("b0_ablation") or {}).get(
                "direct_bound_pruning_root_bound"
            ),
            "direct_bound_pruning_active": (result.get("b0_ablation") or {}).get(
                "direct_bound_pruning_active"
            ),
            "journey_label_bound_pruned_count": (result.get("b0_ablation") or {}).get(
                "journey_label_bound_pruned_count"
            ),
            "B1_root_lp_bound": result.get("root_lp_bound"),
            "root_lp_bound_official": official,
            "root_lp_bound_le_direct_dp_integer_objective": (result.get("b0_ablation") or {}).get(
                "root_bound_le_direct_dp_integer_objective"
            ),
            "root_lp_vs_direct_dp_gap": result.get("root_lp_vs_direct_dp_gap"),
            "integral_root": result.get("integral_root"),
            "pricing_round_count": result.get("pricing_round_count"),
            "added_column_count": result.get("added_column_count"),
            "final_judge_status": result.get("final_judge_status"),
            "final_judge_exact_status": final_judge.get("exact_status"),
            "final_judge_compact_pricing_phase": final_judge.get("compact_pricing_phase"),
            "final_judge_negative_search_status": negative_phase.get("status"),
            "final_judge_negative_search_wall_time": negative_phase.get("wall_time_sec"),
            "final_judge_negative_search_best_reduced_cost": negative_phase.get("best_reduced_cost"),
            "final_judge_negative_search_dual_bound": negative_phase.get("dual_bound"),
            "final_judge_negative_search_negative_found": negative_phase.get("negative_found"),
            "final_judge_compact_negative_batch_found_count": final_judge.get("compact_negative_batch_found_count"),
            "final_judge_compact_negative_batch_search_call_count": final_judge.get(
                "compact_negative_batch_search_call_count"
            ),
            "final_judge_compact_negative_no_good_scope": final_judge.get("compact_negative_no_good_scope"),
            "final_judge_forbidden_task_set_count": final_judge.get("forbidden_task_set_count"),
            "final_judge_optimization_proof_status": optimization_phase.get("status"),
            "final_judge_optimization_proof_wall_time": optimization_phase.get("wall_time_sec"),
            "final_judge_optimization_proof_best_reduced_cost": optimization_phase.get("best_reduced_cost"),
            "final_judge_optimization_proof_dual_bound": optimization_phase.get("dual_bound"),
            "final_judge_call_count": result.get("final_judge_call_count"),
            "final_judge_total_wall_time": result.get("final_judge_total_wall_time"),
            "final_judge_found_negative_count": result.get("final_judge_found_negative_count"),
            "final_judge_best_negative_reduced_cost": result.get("final_judge_best_negative_reduced_cost"),
            "final_judge_incomplete_count": result.get("final_judge_incomplete_count"),
            "final_judge_certified_no_negative_count": result.get("final_judge_certified_no_negative_count"),
            "pricing_history_json": json.dumps(result.get("history") or [], ensure_ascii=False, separators=(",", ":")),
            "final_judge_wall_time": final_judge.get("final_judge_wall_time"),
            "final_judge_generated_journey_count": final_judge.get("generated_journey_count"),
            "final_judge_generated_sortie_count": final_judge.get("feasible_sortie_template_count"),
            "final_judge_route_template_count": final_judge.get("route_template_count"),
            "final_judge_pareto_label_count": final_judge.get("pareto_label_count"),
            "final_judge_best_reduced_cost": final_judge.get("best_reduced_cost"),
            "final_judge_dual_bound": final_judge.get("dual_bound", final_judge.get("bound")),
            "final_judge_mip_gap": final_judge.get("gap"),
            "final_judge_solver_backend": final_judge.get("solver_backend", ""),
            "final_judge_model_status_name": final_judge.get("model_status_name", ""),
            "final_judge_variable_count": final_judge.get("variable_count"),
            "final_judge_constraint_count": final_judge.get("constraint_count"),
            "final_judge_pricing_complete_by_compact_milp": bool(
                final_judge.get("pricing_complete_by_compact_milp")
            ),
            "final_judge_negative_feasibility_search_enabled": bool(
                final_judge.get("negative_feasibility_search_enabled")
            ),
            "final_judge_mtz_connectivity_enabled": bool(final_judge.get("mtz_connectivity_enabled")),
            "final_judge_mtz_endpoint_order_cuts_enabled": bool(
                final_judge.get("mtz_endpoint_order_cuts_enabled")
            ),
            "final_judge_mtz_endpoint_order_cut_count": final_judge.get("mtz_endpoint_order_cut_count"),
            "final_judge_pair_adjacency_cuts_enabled": bool(final_judge.get("pair_adjacency_cuts_enabled")),
            "final_judge_pair_adjacency_cut_count": final_judge.get("pair_adjacency_cut_count"),
            "final_judge_sortie_slots_per_journey": final_judge.get("sortie_slots_per_journey"),
            "final_judge_sortie_slot_bound_source": final_judge.get("sortie_slot_bound_source"),
            "final_judge_sortie_slot_horizon_count_bound": final_judge.get("sortie_slot_horizon_count_bound"),
            "final_judge_sortie_slot_latest_start_count_bound": final_judge.get(
                "sortie_slot_latest_start_count_bound"
            ),
            "final_judge_time_window_arc_pruning_enabled": bool(
                final_judge.get("time_window_arc_pruning_enabled")
            ),
            "final_judge_time_window_arc_option_count": final_judge.get("time_window_arc_option_count"),
            "final_judge_time_window_impossible_arc_option_count": final_judge.get(
                "time_window_impossible_arc_option_count"
            ),
            "final_judge_representative_universe_total_count": final_judge.get(
                "representative_universe_total_count"
            ),
            "final_judge_representative_universe_audited_count": final_judge.get(
                "representative_universe_audited_count"
            ),
            "final_judge_representative_universe_completion_ratio": final_judge.get(
                "representative_universe_completion_ratio"
            ),
            "final_judge_representative_universe_remaining_count": final_judge.get(
                "representative_universe_remaining_count"
            ),
            "manual_rc_audit_pass": manual_rc_audit_pass,
            "pricing_rc_audit_pass": pricing_rc_audit_pass,
            "proof_debt_unreleased_count": result.get("proof_debt_unreleased_count"),
            "wall_time": round(elapsed, 6),
            "fail_closed_reason": "" if certified else str(result.get("note") or ""),
            "direct_root_official_leak": False,
            "b1_mode": result.get("b1_mode"),
            "seed_mode": result.get("seed_mode"),
            "solve_b0_direct_first": bool(result.get("solve_b0_direct_first", True)),
            "initial_column_count": result.get("initial_column_count"),
            "feasible_incumbent_seed_source": result.get("feasible_incumbent_seed_source") or "",
            "feasible_incumbent_seed_column_count": result.get("feasible_incumbent_seed_column_count"),
            "feasible_incumbent_seed_used_as_certificate": bool(
                result.get("feasible_incumbent_seed_used_as_certificate")
            ),
            "full_universe_column_count": result.get("full_universe_column_count"),
            "full_universe_preloaded": result.get("full_universe_preloaded"),
            "rmp_memory_precheck_failed": bool(result.get("rmp_memory_precheck_failed")),
            "rmp_memory_precheck_stage": result.get("rmp_memory_precheck_stage") or "",
            "rmp_memory_precheck_reason": result.get("rmp_memory_precheck_reason") or "",
            "rmp_memory_precheck_estimated_column_count": result.get("rmp_memory_precheck_estimated_column_count"),
            "rmp_memory_precheck_estimated_tableau_cells": result.get("rmp_memory_precheck_estimated_tableau_cells"),
            "rmp_memory_precheck_cell_limit": result.get("rmp_memory_precheck_cell_limit"),
        }
    )
    row.update(
        flatten_objective_payload(
            (result.get("b0_ablation") or {}).get("direct_dp_objective_breakdown"),
            prefix="solution",
        )
    )
    return row


def _job(
    *,
    item: dict | str | Path,
    mode: str,
    seed_mode: str,
    max_direct_tasks: int,
    max_rounds: int,
    matrix_group: str,
    row_time_limit_sec: float | None,
    solve_b0_direct_first: bool = True,
) -> dict:
    return {
        "item": item,
        "mode": mode,
        "seed_mode": seed_mode,
        "max_direct_tasks": int(max_direct_tasks),
        "max_rounds": int(max_rounds),
        "matrix_group": str(matrix_group),
        "row_time_limit_sec": row_time_limit_sec,
        "solve_b0_direct_first": bool(solve_b0_direct_first),
    }


def _run_jobs(jobs: list[dict], *, max_workers: int) -> list[dict]:
    if int(max_workers) <= 1:
        return [_run_job(job) for job in jobs]
    indexed_jobs = [(index, job) for index, job in enumerate(jobs)]
    rows_by_index: dict[int, dict] = {}
    with ProcessPoolExecutor(max_workers=int(max_workers)) as executor:
        futures = {executor.submit(_run_job, job): index for index, job in indexed_jobs}
        for future in as_completed(futures):
            rows_by_index[futures[future]] = future.result()
    return [rows_by_index[index] for index in range(len(indexed_jobs))]


def _run_job(job: dict) -> dict:
    instance = _load_instance(job["item"])
    mode = str(job["mode"])
    if mode == B0_MODE:
        return _run_guarded_row(
            instance,
            mode=mode,
            matrix_group=str(job["matrix_group"]),
            max_direct_tasks=int(job["max_direct_tasks"]),
            row_time_limit_sec=job["row_time_limit_sec"],
            fn=lambda: _run_b0_row(
                instance,
                max_direct_tasks=int(job["max_direct_tasks"]),
                matrix_group=str(job["matrix_group"]),
                wall_time_limit_sec=_inner_direct_wall_time_limit(job["row_time_limit_sec"]),
            ),
        )
    return _run_guarded_row(
        instance,
        mode=mode,
        matrix_group=str(job["matrix_group"]),
        max_direct_tasks=int(job["max_direct_tasks"]),
        row_time_limit_sec=job["row_time_limit_sec"],
        fn=lambda: _run_b1_row(
            instance,
            mode=mode,
            seed_mode=str(job["seed_mode"]),
            max_direct_tasks=int(job["max_direct_tasks"]),
            max_rounds=int(job["max_rounds"]),
            matrix_group=str(job["matrix_group"]),
            wall_time_limit_sec=_inner_direct_wall_time_limit(job["row_time_limit_sec"]),
            solve_b0_direct_first=bool(job.get("solve_b0_direct_first", True)),
        ),
        fallback_extra=_b1_reference_seed_fallback_fields(
            instance,
            mode=mode,
            seed_mode=str(job["seed_mode"]),
            max_direct_tasks=int(job["max_direct_tasks"]),
            solve_b0_direct_first=bool(job.get("solve_b0_direct_first", True)),
        ),
    )


def _run_guarded_row(
    instance: dict,
    *,
    mode: str,
    matrix_group: str,
    max_direct_tasks: int,
    row_time_limit_sec: float | None,
    fn: Callable[[], dict],
    fallback_extra: dict | None = None,
) -> dict:
    if row_time_limit_sec is None:
        return fn()
    fallback_row = _base_row(load_lunar_ice_data(instance), mode=mode, matrix_group=matrix_group)
    start = perf_counter()
    try:
        return _with_timeout(fn, float(row_time_limit_sec))
    except TimeoutError:
        return _fail_closed_attempt_row(
            fallback_row,
            mode=mode,
            max_direct_tasks=max_direct_tasks,
            elapsed=perf_counter() - start,
            reason=f"row_time_limit_sec={row_time_limit_sec} exceeded at max_direct_tasks={max_direct_tasks}",
            exception_type="TimeoutError",
            extra=fallback_extra,
        )
    except MemoryError:
        gc.collect()
        return _fail_closed_attempt_row(
            fallback_row,
            mode=mode,
            max_direct_tasks=max_direct_tasks,
            elapsed=perf_counter() - start,
            reason=(
                "row failed closed after MemoryError while attempting strict rerun "
                f"at max_direct_tasks={max_direct_tasks}"
            ),
            exception_type="MemoryError",
            extra=fallback_extra,
        )


def _inner_direct_wall_time_limit(row_time_limit_sec: float | None) -> float | None:
    if row_time_limit_sec is None:
        return None
    limit = float(row_time_limit_sec)
    reserve = min(30.0, max(10.0, 0.02 * limit))
    return max(0.001, limit - reserve)


def _fail_closed_attempt_row(
    base_row: dict,
    *,
    mode: str,
    max_direct_tasks: int,
    elapsed: float,
    reason: str,
    exception_type: str,
    extra: dict | None = None,
) -> dict:
    row = dict(base_row)
    row.update(
        {
            "algorithm_status": "BPC_INCOMPLETE_PRICING" if mode != B0_MODE else "DIRECT_DP_TIME_LIMIT",
            "certificate_scope": "FEASIBLE_INCUMBENT_ONLY",
            "pricing_state": "INCOMPLETE_LIMIT" if mode != B0_MODE else "",
            "uses_true_dual_bpc_certificate": False,
            "bpc_certificate_status": "NOT_PORTED_TRUE_DUAL_BPC",
            "root_lp_bound_official": False,
            "pricing_round_count": 0,
            "added_column_count": 0,
            "final_judge_status": None,
            "final_judge_exact_status": None,
            "final_judge_compact_pricing_phase": None,
            "final_judge_negative_search_status": None,
            "final_judge_negative_search_wall_time": None,
            "final_judge_negative_search_best_reduced_cost": None,
            "final_judge_negative_search_dual_bound": None,
            "final_judge_negative_search_negative_found": None,
            "final_judge_optimization_proof_status": None,
            "final_judge_optimization_proof_wall_time": None,
            "final_judge_optimization_proof_best_reduced_cost": None,
            "final_judge_optimization_proof_dual_bound": None,
            "final_judge_call_count": 0,
            "final_judge_total_wall_time": 0.0,
            "final_judge_found_negative_count": 0,
            "final_judge_best_negative_reduced_cost": None,
            "final_judge_incomplete_count": 0,
            "final_judge_certified_no_negative_count": 0,
            "pricing_history_json": "[]",
            "final_judge_wall_time": None,
            "final_judge_generated_journey_count": None,
            "final_judge_generated_sortie_count": None,
            "final_judge_route_template_count": None,
            "final_judge_pareto_label_count": None,
            "final_judge_best_reduced_cost": None,
            "final_judge_dual_bound": None,
            "final_judge_mip_gap": None,
            "final_judge_solver_backend": "",
            "final_judge_model_status_name": "",
            "final_judge_variable_count": None,
            "final_judge_constraint_count": None,
            "final_judge_pricing_complete_by_compact_milp": False,
            "final_judge_negative_feasibility_search_enabled": False,
            "final_judge_mtz_connectivity_enabled": False,
            "final_judge_mtz_endpoint_order_cuts_enabled": False,
            "final_judge_mtz_endpoint_order_cut_count": None,
            "final_judge_pair_adjacency_cuts_enabled": False,
            "final_judge_pair_adjacency_cut_count": None,
            "final_judge_sortie_slots_per_journey": None,
            "final_judge_sortie_slot_bound_source": "",
            "final_judge_sortie_slot_horizon_count_bound": None,
            "final_judge_sortie_slot_latest_start_count_bound": None,
            "final_judge_time_window_arc_pruning_enabled": False,
            "final_judge_time_window_arc_option_count": None,
            "final_judge_time_window_impossible_arc_option_count": None,
            "final_judge_representative_universe_total_count": None,
            "final_judge_representative_universe_audited_count": None,
            "final_judge_representative_universe_completion_ratio": None,
            "final_judge_representative_universe_remaining_count": None,
            "manual_rc_audit_pass": None,
            "pricing_rc_audit_pass": None,
            "proof_debt_unreleased_count": 0,
            "wall_time": round(float(elapsed), 6),
            "fail_closed_reason": str(reason),
            "attempted_exception_type": str(exception_type),
            "attempted_max_direct_tasks": int(max_direct_tasks),
            "rmp_memory_precheck_failed": False,
            "rmp_memory_precheck_stage": "",
            "rmp_memory_precheck_reason": "",
            "rmp_memory_precheck_estimated_column_count": None,
            "rmp_memory_precheck_estimated_tableau_cells": None,
            "rmp_memory_precheck_cell_limit": None,
            "direct_root_official_leak": False,
        }
    )
    row.update(extra or {})
    return row


def _b1_reference_seed_fallback_fields(
    instance: dict,
    *,
    mode: str,
    seed_mode: str,
    max_direct_tasks: int,
    solve_b0_direct_first: bool,
) -> dict:
    if mode == B0_MODE or bool(solve_b0_direct_first):
        return {}
    data = load_lunar_ice_data(instance)
    placeholder = _reference_seed_direct_placeholder(data)
    try:
        _, seed_report = build_b1_seed_columns(
            data,
            b0_direct=placeholder,
            seed_mode=seed_mode,
            max_direct_tasks=int(max_direct_tasks),
        )
    except Exception:
        return {
            "solve_b0_direct_first": False,
            "reference_solution_upper_bound": placeholder.reference_solution_upper_bound,
            "reference_solution_upper_bound_source": placeholder.reference_solution_upper_bound_source,
        }
    return {
        "solve_b0_direct_first": False,
        "seed_mode": seed_report.get("seed_mode"),
        "initial_column_count": seed_report.get("initial_column_count"),
        "feasible_incumbent_seed_source": seed_report.get("feasible_incumbent_seed_source", ""),
        "feasible_incumbent_seed_column_count": seed_report.get("feasible_incumbent_seed_column_count", 0),
        "feasible_incumbent_seed_used_as_certificate": bool(
            seed_report.get("feasible_incumbent_seed_used_as_certificate", False)
        ),
        "full_universe_column_count": seed_report.get("full_universe_column_count"),
        "full_universe_preloaded": seed_report.get("full_universe_preloaded"),
        "reference_solution_upper_bound": placeholder.reference_solution_upper_bound,
        "reference_solution_upper_bound_source": placeholder.reference_solution_upper_bound_source,
    }


def _with_timeout(fn: Callable[[], dict], seconds: float) -> dict:
    def _raise_timeout(_signum, _frame):
        raise TimeoutError("row timed out")

    previous = signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, float(seconds)))
    try:
        return fn()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous)


def _base_row(data, *, mode: str, matrix_group: str) -> dict:
    row = {
        "matrix_group": matrix_group,
        "scale": len(data.task_ids),
        "instance_id": data.instance_id,
        "mode": mode,
        "algorithm_status": None,
        "certificate_scope": None,
        "pricing_state": None,
        "uses_true_dual_bpc_certificate": False,
        "bpc_certificate_status": None,
        "official_lower_bound_source": None,
        "official_lower_bound_scope": None,
        "best_diagnostic_bound_source": None,
        "B0_direct_objective": None,
        "reference_solution_upper_bound": None,
        "reference_solution_upper_bound_source": "",
        "direct_bound_pruning_root_bound": None,
        "direct_bound_pruning_active": False,
        "journey_label_bound_pruned_count": 0,
        "B1_root_lp_bound": None,
        "root_lp_bound_official": False,
        "root_lp_bound_le_direct_dp_integer_objective": None,
        "root_lp_vs_direct_dp_gap": None,
        "integral_root": None,
        "pricing_round_count": None,
        "added_column_count": None,
        "final_judge_status": None,
        "final_judge_exact_status": None,
        "final_judge_compact_pricing_phase": None,
        "final_judge_negative_search_status": None,
        "final_judge_negative_search_wall_time": None,
        "final_judge_negative_search_best_reduced_cost": None,
        "final_judge_negative_search_dual_bound": None,
        "final_judge_negative_search_negative_found": None,
        "final_judge_optimization_proof_status": None,
        "final_judge_optimization_proof_wall_time": None,
        "final_judge_optimization_proof_best_reduced_cost": None,
        "final_judge_optimization_proof_dual_bound": None,
        "final_judge_call_count": 0,
        "final_judge_total_wall_time": 0.0,
        "final_judge_found_negative_count": 0,
        "final_judge_best_negative_reduced_cost": None,
        "final_judge_incomplete_count": 0,
        "final_judge_certified_no_negative_count": 0,
        "pricing_history_json": "[]",
        "final_judge_wall_time": None,
        "final_judge_generated_journey_count": None,
        "final_judge_generated_sortie_count": None,
        "final_judge_route_template_count": None,
        "final_judge_pareto_label_count": None,
        "final_judge_best_reduced_cost": None,
        "final_judge_dual_bound": None,
        "final_judge_mip_gap": None,
        "final_judge_solver_backend": "",
        "final_judge_model_status_name": "",
        "final_judge_variable_count": None,
        "final_judge_constraint_count": None,
        "final_judge_pricing_complete_by_compact_milp": False,
        "final_judge_negative_feasibility_search_enabled": False,
        "final_judge_mtz_connectivity_enabled": False,
        "final_judge_mtz_endpoint_order_cuts_enabled": False,
        "final_judge_mtz_endpoint_order_cut_count": None,
        "final_judge_pair_adjacency_cuts_enabled": False,
        "final_judge_pair_adjacency_cut_count": None,
        "final_judge_sortie_slots_per_journey": None,
        "final_judge_sortie_slot_bound_source": "",
        "final_judge_sortie_slot_horizon_count_bound": None,
        "final_judge_sortie_slot_latest_start_count_bound": None,
        "final_judge_time_window_arc_pruning_enabled": False,
        "final_judge_time_window_arc_option_count": None,
        "final_judge_time_window_impossible_arc_option_count": None,
        "final_judge_representative_universe_total_count": None,
        "final_judge_representative_universe_audited_count": None,
        "final_judge_representative_universe_completion_ratio": None,
        "final_judge_representative_universe_remaining_count": None,
        "manual_rc_audit_pass": None,
        "pricing_rc_audit_pass": None,
        "proof_debt_unreleased_count": None,
        "wall_time": None,
        "fail_closed_reason": "",
        "direct_root_official_leak": False,
        "b1_mode": None,
        "seed_mode": None,
        "initial_column_count": None,
        "full_universe_column_count": None,
        "full_universe_preloaded": None,
        "rmp_memory_precheck_failed": False,
        "rmp_memory_precheck_stage": "",
        "rmp_memory_precheck_reason": "",
        "rmp_memory_precheck_estimated_column_count": None,
        "rmp_memory_precheck_estimated_tableau_cells": None,
        "rmp_memory_precheck_cell_limit": None,
    }
    row.update(flatten_objective_payload(objective_metadata(data), prefix="objective"))
    return row


def _summary_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[int, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        grouped[(int(row["scale"]), str(row.get("matrix_group") or ""), str(row["mode"]))].append(row)
    summaries = []
    for (scale, matrix_group, mode), group in sorted(grouped.items()):
        wall_times = [_float(row.get("wall_time")) for row in group if _float(row.get("wall_time")) is not None]
        added = [_float(row.get("added_column_count")) for row in group if _float(row.get("added_column_count")) is not None]
        rounds = [_float(row.get("pricing_round_count")) for row in group if _float(row.get("pricing_round_count")) is not None]
        summaries.append(
            {
                "scale": scale,
                "matrix_group": matrix_group,
                "mode": mode,
                "run_count": len(group),
                "B0_direct_optimal_count": sum(
                    1 for row in group if row.get("algorithm_status") == "DIRECT_DP_BASELINE_OPTIMAL"
                ),
                "BPC_NODE_LP_CERTIFIED_count": sum(
                    1 for row in group if row.get("certificate_scope") == "BPC_NODE_LP_CERTIFIED"
                ),
                "fail_closed_count": sum(1 for row in group if row.get("fail_closed_reason")),
                "root_bound_gt_B0_violation_count": sum(
                    1 for row in group if row.get("root_lp_bound_le_direct_dp_integer_objective") is False
                ),
                "manual_rc_fail_count": sum(1 for row in group if row.get("manual_rc_audit_pass") is False),
                "pricing_rc_fail_count": sum(1 for row in group if row.get("pricing_rc_audit_pass") is False),
                "direct_root_official_leak_count": sum(1 for row in group if row.get("direct_root_official_leak")),
                "mean_wall_time": round(mean(wall_times), 6) if wall_times else None,
                "p90_wall_time": _p90(wall_times),
                "mean_added_columns": round(mean(added), 6) if added else None,
                "mean_pricing_rounds": round(mean(rounds), 6) if rounds else None,
            }
        )
    return summaries


def _redlines(summary_rows: list[dict]) -> dict:
    return {
        "root_bound_gt_B0_violation_count": sum(row["root_bound_gt_B0_violation_count"] for row in summary_rows),
        "direct_root_official_leak_count": sum(row["direct_root_official_leak_count"] for row in summary_rows),
        "manual_rc_fail_count": sum(row["manual_rc_fail_count"] for row in summary_rows),
        "pricing_rc_fail_count": sum(row["pricing_rc_fail_count"] for row in summary_rows),
    }


def _manifest_instance_paths(manifest_path: Path, project_root: Path, *, scale: int) -> list[Path]:
    manifest = read_json(manifest_path)
    rows = []
    for row in manifest.get("instances", []):
        if int(row.get("scale") or _scale_from_path(row.get("path"))) != int(scale):
            continue
        raw = Path(str(row["path"]))
        path = raw if raw.is_absolute() else project_root / raw
        rows.append(path)
    return rows


def _scale_from_path(path: object) -> int:
    text = str(path or "")
    for scale in (5, 10, 20, 30, 50, 100):
        if f"{scale:03d}" in text:
            return scale
    return 0


def _load_instance(item: dict | str | Path) -> dict:
    if isinstance(item, dict):
        return item
    return read_json(item)


def _float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _p90(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(0.9 * (len(ordered) - 1)))
    return round(ordered[index], 6)
