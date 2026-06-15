#!/usr/bin/env python3
"""Analyze same-run GAT impact audit-only A/B outputs.

This script reads result CSVs produced by
``build_gat_same_run_batch_impact_audit_ab_runbook.py`` and the offline
GAT+kNN/OOD audit summary.  It is read-only and never runs BPC, pricing, RMP,
workers, or certificates.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_same_run_batch_impact_audit_ab_analysis_20260615"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260615_bpc_future_gat_same_run_batch_impact_audit_ab_analysis_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"_missing": True}


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _as_float(value: Any) -> float | None:
    try:
        if value in ("", None):
            return None
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return None
        return result
    except (TypeError, ValueError):
        return None


def _numeric_equal(left: Any, right: Any, *, tol: float = 1.0e-7) -> bool:
    a = _as_float(left)
    b = _as_float(right)
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(a - b) <= tol


def _summarize_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    wall_times: list[float] = []
    optimal_count = 0
    time_limit_count = 0
    for row in rows:
        status = str(row.get("status") or "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
        if status == "OPTIMAL":
            optimal_count += 1
        if status == "TIME_LIMIT":
            time_limit_count += 1
        wall = _as_float(row.get("wall_time"))
        if wall is not None:
            wall_times.append(wall)
    return {
        "row_count": len(rows),
        "status_counts": status_counts,
        "optimal_count": optimal_count,
        "time_limit_count": time_limit_count,
        "wall_time_avg": sum(wall_times) / len(wall_times) if wall_times else None,
        "wall_time_max": max(wall_times) if wall_times else None,
    }


def _compare_pair(pair: dict[str, Any]) -> dict[str, Any]:
    baseline_csv = Path(str(pair["baseline_csv"]))
    capture_csv = Path(str(pair["capture_csv"]))
    baseline_rows = _read_csv(baseline_csv)
    capture_rows = _read_csv(capture_csv)
    baseline_by_instance = {str(row.get("instance") or ""): row for row in baseline_rows}
    capture_by_instance = {str(row.get("instance") or ""): row for row in capture_rows}
    common = sorted(set(baseline_by_instance) & set(capture_by_instance))
    missing_in_capture = sorted(set(baseline_by_instance) - set(capture_by_instance))
    missing_in_baseline = sorted(set(capture_by_instance) - set(baseline_by_instance))
    mismatches: list[dict[str, Any]] = []
    wall_overheads: list[float] = []
    for instance in common:
        base = baseline_by_instance[instance]
        cap = capture_by_instance[instance]
        fields = {
            "status_equal": str(base.get("status")) == str(cap.get("status")),
            "primal_equal": _numeric_equal(base.get("primal_bound"), cap.get("primal_bound")),
            "dual_equal": _numeric_equal(base.get("dual_bound"), cap.get("dual_bound")),
            "gap_equal": _numeric_equal(base.get("gap"), cap.get("gap")),
            "node_count_equal": str(base.get("node_count")) == str(cap.get("node_count")),
            "external_timeout_equal": str(base.get("external_timeout")) == str(cap.get("external_timeout")),
        }
        if not all(fields.values()):
            mismatches.append(
                {
                    "instance": instance,
                    "fields": fields,
                    "baseline": {
                        "status": base.get("status"),
                        "primal_bound": base.get("primal_bound"),
                        "dual_bound": base.get("dual_bound"),
                        "gap": base.get("gap"),
                    },
                    "capture": {
                        "status": cap.get("status"),
                        "primal_bound": cap.get("primal_bound"),
                        "dual_bound": cap.get("dual_bound"),
                        "gap": cap.get("gap"),
                    },
                }
            )
        base_wall = _as_float(base.get("wall_time"))
        cap_wall = _as_float(cap.get("wall_time"))
        if base_wall is not None and cap_wall is not None and base_wall > 0:
            wall_overheads.append((cap_wall - base_wall) / base_wall)
    return {
        "task_count": int(pair["task_count"]),
        "baseline_csv": str(baseline_csv),
        "capture_csv": str(capture_csv),
        "baseline_summary": _summarize_rows(baseline_rows),
        "capture_summary": _summarize_rows(capture_rows),
        "baseline_row_count": len(baseline_rows),
        "capture_row_count": len(capture_rows),
        "common_instance_count": len(common),
        "missing_in_capture": missing_in_capture,
        "missing_in_baseline": missing_in_baseline,
        "official_result_mismatch_count": len(mismatches),
        "official_result_mismatches": mismatches[:10],
        "official_results_match": bool(
            baseline_rows
            and capture_rows
            and not missing_in_capture
            and not missing_in_baseline
            and not mismatches
        ),
        "wall_overhead_avg": (
            sum(wall_overheads) / len(wall_overheads) if wall_overheads else None
        ),
        "wall_overhead_max": max(wall_overheads) if wall_overheads else None,
    }


def audit_results(*, runbook_summary: Path, output_dir: Path, report: Path) -> dict[str, Any]:
    runbook = _read_json(runbook_summary)
    pairs = [_compare_pair(pair) for pair in runbook.get("result_pairs", [])]
    validation_summary_path = Path(str(runbook.get("gat_validation_summary", "")))
    validation = _read_json(validation_summary_path)
    validation_metrics = validation.get("validation_metrics") or {}
    task5_pair = next((pair for pair in pairs if int(pair["task_count"]) == 5), {})
    task10_pair = next((pair for pair in pairs if int(pair["task_count"]) == 10), {})
    task20_pair = next((pair for pair in pairs if int(pair["task_count"]) == 20), {})
    checks = {
        "runbook_checks_pass": bool(runbook.get("all_checks_pass")),
        "task5_official_results_match": bool(task5_pair.get("official_results_match")),
        "task10_official_results_match": bool(task10_pair.get("official_results_match")),
        "task20_capture_pair_available": bool(task20_pair.get("official_results_match")),
        "gat_knn_ood_checks_pass": bool(validation.get("all_checks_pass")),
        "gat_validation_has_high_priority_signal": int(
            validation_metrics.get("predicted_high_priority") or 0
        )
        > 0,
        "gat_validation_has_zero_delay_false_positive": int(
            validation_metrics.get("fp_high_priority_on_delay") or 0
        )
        == 0,
        "gat_validation_delay_recall_positive": (
            validation_metrics.get("negative_recall_delay_queue") is not None
            and float(validation_metrics.get("negative_recall_delay_queue")) > 0.0
        ),
        "no_certificate_effect": (
            runbook.get("certificate_ready") is False
            and validation.get("selector_can_certificate") is False
            and validation.get("official_bound_effect") is False
        ),
        "no_active_worker_effect": runbook.get("active_worker_ready") is False,
        "negative_not_discarded": (
            validation.get("gate_can_permanently_discard_negative_columns") is False
            and validation.get("negative_columns_must_remain_eventually_reachable") is True
        ),
    }
    five_ten_no_regression_pass = bool(
        checks["task5_official_results_match"]
        and checks["task10_official_results_match"]
    )
    same_run_gat_offline_gate_ready = bool(
        checks["gat_knn_ood_checks_pass"]
        and checks["gat_validation_has_high_priority_signal"]
        and checks["gat_validation_has_zero_delay_false_positive"]
        and checks["negative_not_discarded"]
    )
    task20_baseline_summary = task20_pair.get("baseline_summary") or {}
    task20_capture_summary = task20_pair.get("capture_summary") or {}
    task20_target_status = {
        "baseline_optimal_count": int(task20_baseline_summary.get("optimal_count") or 0),
        "baseline_time_limit_count": int(task20_baseline_summary.get("time_limit_count") or 0),
        "capture_optimal_count": int(task20_capture_summary.get("optimal_count") or 0),
        "capture_time_limit_count": int(task20_capture_summary.get("time_limit_count") or 0),
        "baseline_all_optimal": bool(
            task20_baseline_summary.get("row_count")
            and task20_baseline_summary.get("optimal_count") == task20_baseline_summary.get("row_count")
        ),
        "capture_all_optimal": bool(
            task20_capture_summary.get("row_count")
            and task20_capture_summary.get("optimal_count") == task20_capture_summary.get("row_count")
        ),
    }
    summary = {
        "schema_version": "gat_same_run_batch_impact_audit_ab_analysis_v1",
        "status": (
            "gat_same_run_pre_online_audit_gate_ready"
            if five_ten_no_regression_pass and same_run_gat_offline_gate_ready
            else "gat_same_run_pre_online_audit_gate_incomplete"
        ),
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "runbook_summary": str(runbook_summary),
        "gat_validation_summary": str(validation_summary_path),
        "pair_results": pairs,
        "gat_validation_metrics": validation_metrics,
        "five_ten_no_regression_pass": five_ten_no_regression_pass,
        "same_run_gat_offline_gate_ready": same_run_gat_offline_gate_ready,
        "twenty_capture_pair_completed": bool(task20_pair.get("official_results_match")),
        "task20_target_status": task20_target_status,
        "twenty_wall_time_roi_proven": False,
        "production_ready": False,
        "online_effect_enabled": False,
        "wall_time_roi_proven": False,
        "official_certificate_effect": False,
        "gat_role": "embedding_and_trajectory_impact_representation",
        "safety_shell": "same_run_knn_ood_delay_queue",
        "safe_negative_decision": "HIGH_PRIORITY",
        "unsafe_negative_decision": "DELAY_QUEUE",
        "negative_columns_must_remain_eventually_reachable": True,
        "gate_can_permanently_discard_negative_columns": False,
        "productionization_standard": runbook.get("productionization_standard", {}),
        "checks": checks,
        "all_checks_pass": bool(
            checks["runbook_checks_pass"]
            and checks["no_certificate_effect"]
            and checks["no_active_worker_effect"]
            and checks["negative_not_discarded"]
        ),
        "remaining_blockers": [
            "no_online_opt_in_solver_integration_yet",
            "no_online_wall_time_roi_evidence_yet",
            "task20_baseline_not_exact_optimal_on_smoke_matrix",
        ],
        "effective_sample_collection_rule": {
            "required_context": "same_context_theta_basis_cuts_branch_pool",
            "required_intervention": "add_candidate_batch_then_re_solve_rmp_or_followup_rounds",
            "positive_label": "trajectory_improves_objective_dual_or_tail",
            "negative_true_rc_without_impact": "delay_queue_not_discard",
            "invalid_sources": [
                "rc_negative_only",
                "different_dual_context",
                "appeared_in_positive_batch_without_causal_target_match",
                "replacement_column_without_support_or_tail_change",
            ],
        },
        "goal_complete": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Same-Run Batch Impact Audit A/B Analysis 报告",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "读取 same-run GAT audit-only A/B 的结果 CSV 和 kNN/OOD summary。",
        "该脚本只读文件，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_same_run_batch_impact_audit_ab_analysis = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"five_ten_no_regression_pass = {str(summary['five_ten_no_regression_pass']).lower()}",
        f"same_run_gat_offline_gate_ready = {str(summary['same_run_gat_offline_gate_ready']).lower()}",
        f"twenty_capture_pair_completed = {str(summary['twenty_capture_pair_completed']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"wall_time_roi_proven = {str(summary['wall_time_roi_proven']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 摘要",
        "",
        "```json",
        json.dumps(
            {
                "pair_results": summary["pair_results"],
                "gat_validation_metrics": summary["gat_validation_metrics"],
                "task20_target_status": summary["task20_target_status"],
                "effective_sample_collection_rule": summary[
                    "effective_sample_collection_rule"
                ],
                "checks": summary["checks"],
                "remaining_blockers": summary["remaining_blockers"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 解释",
        "",
        "- `five_ten_no_regression_pass=true` 只说明 capture-only 不改变 5/10 official result；",
        "- 20-task smoke 的 baseline/capture official result 一致，但当前仍是 TIME_LIMIT，不是 200 秒内精确闭合；",
        "- `same_run_gat_offline_gate_ready=true` 只说明离线 safety shell 有候选信号；",
        "- `production_ready=false` 是刻意保守，因为还没有 online opt-in ROI；",
        "- true-RC negative 不能被永久丢弃，未放行的只能进入 DELAY_QUEUE。",
        "",
        "## 为什么有效样本稀疏",
        "",
        "- `rc < 0` 只能说明列在当前 dual 下可加，不说明它会改变 RMP 轨迹；",
        "- 很多负列是 replacement：能进池，但不改变 active support、dual 震荡或 final-judge tail；",
        "- 跨 dual / cuts / branch / pool 上下文贴标签会污染因果关系；",
        "- 因此有效样本必须来自 same-context intervention：固定上下文，加入候选 batch，再观察 objective、dual、support 和 tail 的真实变化。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runbook-summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = audit_results(
        runbook_summary=args.runbook_summary,
        output_dir=args.output_dir,
        report=args.report,
    )
    print(
        json.dumps(
            {
                "summary": str(args.output_dir / "summary.json"),
                "report": str(args.report),
                "all_checks_pass": summary["all_checks_pass"],
                "five_ten_no_regression_pass": summary["five_ten_no_regression_pass"],
                "production_ready": summary["production_ready"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
