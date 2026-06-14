#!/usr/bin/env python3
"""Analyze pre-online GAT embedding audit A/B run outputs.

This script reads result CSVs and the GAT capture-validation summary generated
by ``build_gat_embedding_audit_ab_runbook.py``.  It is diagnostic-only and does
not run BPC/pricing/RMP, workers, or certificates.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_embedding_audit_ab_analysis_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_gat_embedding_audit_ab_analysis_zh.md"
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


def _row_key(row: dict[str, str]) -> str:
    return str(row.get("instance") or "")


def _compare_pair(pair: dict[str, Any]) -> dict[str, Any]:
    baseline_csv = Path(str(pair["baseline_csv"]))
    capture_csv = Path(str(pair["capture_csv"]))
    baseline_rows = _read_csv(baseline_csv)
    capture_rows = _read_csv(capture_csv)
    baseline_by_instance = {_row_key(row): row for row in baseline_rows}
    capture_by_instance = {_row_key(row): row for row in capture_rows}
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
    external = validation.get("external_validation_summary") or validation
    metrics = external.get("validation_metrics", {}).get("overall", {})
    task5_pair = next((pair for pair in pairs if int(pair["task_count"]) == 5), {})
    task10_pair = next((pair for pair in pairs if int(pair["task_count"]) == 10), {})
    task20_pair = next((pair for pair in pairs if int(pair["task_count"]) == 20), {})
    checks = {
        "runbook_checks_pass": bool(runbook.get("all_checks_pass")),
        "task5_official_results_match": bool(task5_pair.get("official_results_match")),
        "task10_official_results_match": bool(task10_pair.get("official_results_match")),
        "task20_official_results_match_for_capture_only": bool(
            task20_pair.get("official_results_match")
        ),
        "gat_capture_validation_checks_pass": bool(validation.get("all_checks_pass")),
        "gat_validation_has_high_priority_signal": int(metrics.get("predicted_positive") or 0) > 0,
        "gat_validation_has_zero_false_positive": int(metrics.get("fp") or 0) == 0,
        "no_certificate_effect": (
            runbook.get("certificate_ready") is False
            and validation.get("certificate_effect", False) is False
            and validation.get("official_bound_effect", False) is False
        ),
        "no_active_worker_effect": (
            runbook.get("active_worker_ready") is False
            and validation.get("active_worker_effect", False) is False
        ),
    }
    five_ten_no_regression_pass = bool(
        checks["task5_official_results_match"]
        and checks["task10_official_results_match"]
    )
    twenty_roi_audit_ready = bool(
        checks["task20_official_results_match_for_capture_only"]
        and checks["gat_capture_validation_checks_pass"]
        and checks["gat_validation_has_zero_false_positive"]
    )
    pre_online_gate_ready = all(bool(value) for value in checks.values())
    summary = {
        "schema_version": "gat_embedding_audit_ab_analysis_v1",
        "status": (
            "gat_embedding_pre_online_audit_gate_ready"
            if pre_online_gate_ready
            else "gat_embedding_pre_online_audit_gate_incomplete"
        ),
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "runbook_summary": str(runbook_summary),
        "gat_validation_summary": str(validation_summary_path),
        "pair_results": pairs,
        "gat_validation_metrics": metrics,
        "five_ten_no_regression_pass": five_ten_no_regression_pass,
        "twenty_roi_audit_ready": twenty_roi_audit_ready,
        "twenty_wall_time_roi_proven": False,
        "pre_online_gate_ready": pre_online_gate_ready,
        "production_ready": False,
        "online_effect_enabled": False,
        "wall_time_roi_proven": False,
        "official_certificate_effect": False,
        "gat_role": "embedding_and_trajectory_impact_representation",
        "safety_shell": "knn_ood_delay_queue",
        "safe_negative_decision": "HIGH_PRIORITY",
        "unsafe_negative_decision": "DELAY_QUEUE",
        "nonnegative_decision": "REJECT_NONNEGATIVE_ONLY",
        "negative_columns_must_remain_eventually_reachable": True,
        "gate_can_permanently_discard_negative_columns": False,
        "productionization_standard": {
            "task5_10_no_regression_required": True,
            "task20_wall_time_roi_required": True,
            "critical_disagreement_allowed": False,
            "certificate_effect_allowed": False,
            "default_enable_allowed": False,
            "negative_column_discard_allowed": False,
        },
        "twenty_roi_required_metrics": [
            "wall_time_decreases_or_gap_improves",
            "worker_or_scheduler_high_priority_count_positive",
            "added_or_prioritized_new_task_sets_positive",
            "followup_legacy_final_judge_or_retry_count_decreases",
            "official_result_unchanged",
        ],
        "checks": checks,
        "all_checks_pass": bool(
            checks["runbook_checks_pass"]
            and checks["no_certificate_effect"]
            and checks["no_active_worker_effect"]
        ),
        "remaining_blockers": [
            "no_online_opt_in_solver_integration_yet",
            "no_online_wall_time_roi_evidence_yet",
        ],
        "goal_complete": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Embedding Audit A/B Analysis 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "读取 GAT embedding audit-only A/B 的结果 CSV 和 validation summary。",
        "该脚本不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_embedding_audit_ab_analysis = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"pre_online_gate_ready = {str(summary['pre_online_gate_ready']).lower()}",
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
                "five_ten_no_regression_pass": summary["five_ten_no_regression_pass"],
                "twenty_roi_audit_ready": summary["twenty_roi_audit_ready"],
                "twenty_wall_time_roi_proven": summary["twenty_wall_time_roi_proven"],
                "productionization_standard": summary["productionization_standard"],
                "twenty_roi_required_metrics": summary["twenty_roi_required_metrics"],
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
        "- 通过该分析只能说明 pre-online audit gate 可继续推进；",
        "- `wall_time_roi_proven=false` 是刻意保守，因为还没有 online opt-in effect；",
        "- GAT 只负责 embedding / trajectory impact 表达，kNN/OOD 只负责安全壳；",
        "- 负列只能进入 HIGH_PRIORITY 或 DELAY_QUEUE，不能被永久丢弃；",
        "- 5/10 no-regression 在这里指 capture-only 官方结果不变，不代表未来 online gate 已安全；",
        "- exact certificate 仍只来自 true-dual exact final judge。",
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
                "pre_online_gate_ready": summary["pre_online_gate_ready"],
                "production_ready": summary["production_ready"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
