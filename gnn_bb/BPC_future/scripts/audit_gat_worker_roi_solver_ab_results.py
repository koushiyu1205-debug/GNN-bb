#!/usr/bin/env python3
"""Audit worker-ROI GAT solver A/B results.

This is a read-only post-run audit.  It compares CSVs emitted by
``build_gat_worker_roi_solver_ab_runbook.py`` and checks:

* 5/10 sentinel runs completed without the new worker;
* 20-task worker runs do not create certificate or official-bound effects;
* worker ROI is classified from actual downstream result deltas.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from BPC_future.scripts.audit_gat_target_intervention_reachability import (
    _classify_candidate as _classify_target_reachability,
)


DEFAULT_RUNBOOK_SUMMARY = Path("BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/summary.json")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_worker_roi_solver_ab_audit_v31_20260615")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_worker_roi_solver_ab_audit_v31_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runbook-summary", type=Path, default=DEFAULT_RUNBOOK_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_results(
        runbook_summary=args.runbook_summary,
        output_dir=args.output_dir,
        report=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_results(
    *,
    runbook_summary: Path = DEFAULT_RUNBOOK_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    runbook = json.loads(Path(runbook_summary).read_text(encoding="utf-8"))
    if runbook.get("certificate_ready") or runbook.get("official_bound_effect"):
        raise ValueError("runbook has forbidden certificate or official-bound effect")
    small_records = [_small_record(item) for item in runbook.get("small_no_regression") or []]
    commands = list(runbook.get("commands") or [])
    candidate_records = [
        _candidate_record(item, commands=commands) for item in runbook.get("candidate_runs") or []
    ]
    roi_counts: dict[str, int] = {}
    for record in candidate_records:
        roi_counts[record["roi_class"]] = roi_counts.get(record["roi_class"], 0) + 1
    positive_roi = [
        record for record in candidate_records if str(record["roi_class"]).startswith("positive_")
    ]
    negative_roi = [
        record for record in candidate_records if str(record["roi_class"]).startswith("negative_")
    ]
    no_observed = [record for record in candidate_records if record["roi_class"] == "no_observed_roi"]
    target_not_reached = [
        record for record in candidate_records if record["roi_class"] == "target_not_reached"
    ]
    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "runbook_checks_pass": bool(runbook.get("all_checks_pass")),
        "small_5_10_results_present": all(record["csv_exists"] for record in small_records),
        "small_5_10_no_regression_optimal": all(
            record["status"] == "OPTIMAL" for record in small_records if record["csv_exists"]
        ),
        "candidate_results_present": bool(candidate_records)
        and all(record["baseline_csv_exists"] and record["worker_csv_exists"] for record in candidate_records),
        "no_certificate_effect": all(not record["certificate_effect"] for record in candidate_records),
        "no_official_bound_effect": all(not record["official_bound_effect"] for record in candidate_records),
    }
    summary = {
        "schema_version": "gat_worker_roi_solver_ab_audit_v1",
        "status": "audited" if candidate_records or small_records else "no_records",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "runbook_summary": str(runbook_summary),
        "small_records": small_records,
        "candidate_records": candidate_records,
        "record_count": len(candidate_records),
        "roi_class_counts": dict(sorted(roi_counts.items())),
        "positive_trajectory_roi_count": len(positive_roi),
        "negative_trajectory_roi_count": len(negative_roi),
        "no_observed_roi_count": len(no_observed),
        "target_not_reached_count": len(target_not_reached),
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "next_decision": (
            "worker_roi_gat_has_solver_roi_signal"
            if positive_roi and all(bool(checks[key]) for key in ("no_certificate_effect", "no_official_bound_effect"))
            else "run_or_collect_more_solver_ab"
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _small_record(item: dict[str, Any]) -> dict[str, Any]:
    task_count = int(item.get("task_count") or 0)
    csv_path = _small_csv_path(item)
    row = _read_first_csv_row(csv_path)
    return {
        "task_count": task_count,
        "csv": str(csv_path),
        "csv_exists": row is not None,
        "status": _status(row),
        "solving_time": _float_value(row, "solving_time"),
        "primal_bound": _float_value(row, "primal_bound"),
        "dual_bound": _float_value(row, "dual_bound"),
    }


def _small_csv_path(item: dict[str, Any]) -> Path:
    if item.get("results_csv"):
        return Path(str(item["results_csv"]))
    task_count = int(item.get("task_count") or 0)
    return DEFAULT_RUNBOOK_SUMMARY.parent / f"task{task_count:03d}_mainline_no_regression_no_new_worker" / "results.csv"


def _candidate_record(candidate: dict[str, Any], *, commands: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    baseline_csv = Path(str(candidate.get("baseline_csv") or ""))
    worker_csv = Path(str(candidate.get("worker_csv") or ""))
    baseline = _read_first_csv_row(baseline_csv)
    worker = _read_first_csv_row(worker_csv)
    baseline_primal = _float_value(baseline, "primal_bound")
    worker_primal = _float_value(worker, "primal_bound")
    baseline_dual = _float_value(baseline, "dual_bound")
    worker_dual = _float_value(worker, "dual_bound")
    baseline_exact = _int_value(baseline, "exact_pricing_calls")
    worker_exact = _int_value(worker, "exact_pricing_calls")
    baseline_pricing = _int_value(baseline, "pricing_calls")
    worker_pricing = _int_value(worker, "pricing_calls")
    baseline_time = _float_value(baseline, "solving_time")
    worker_time = _float_value(worker, "solving_time")
    reachability = _target_reachability(candidate, commands=commands or [])
    record = {
        "name": str(candidate.get("name") or ""),
        "instance": str(candidate.get("instance") or ""),
        "expected_context_hash": str(candidate.get("expected_context_hash") or ""),
        "target_sequence": list(candidate.get("target_sequence") or []),
        "baseline_csv": str(baseline_csv),
        "worker_csv": str(worker_csv),
        "baseline_csv_exists": baseline is not None,
        "worker_csv_exists": worker is not None,
        "baseline_status": _status(baseline),
        "worker_status": _status(worker),
        "baseline_primal": baseline_primal,
        "worker_primal": worker_primal,
        "primal_improvement": (
            None if baseline_primal is None or worker_primal is None else baseline_primal - worker_primal
        ),
        "baseline_dual_bound": baseline_dual,
        "worker_dual_bound": worker_dual,
        "baseline_exact_pricing_calls": baseline_exact,
        "worker_exact_pricing_calls": worker_exact,
        "exact_pricing_calls_delta": (
            None if baseline_exact is None or worker_exact is None else worker_exact - baseline_exact
        ),
        "baseline_pricing_calls": baseline_pricing,
        "worker_pricing_calls": worker_pricing,
        "pricing_calls_delta": (
            None if baseline_pricing is None or worker_pricing is None else worker_pricing - baseline_pricing
        ),
        "baseline_solving_time": baseline_time,
        "worker_solving_time": worker_time,
        "solving_time_delta": (
            None if baseline_time is None or worker_time is None else worker_time - baseline_time
        ),
        "official_bound_effect": bool(worker_dual is not None and baseline_dual != worker_dual),
        "certificate_effect": False,
        "source_roi_class": str(candidate.get("roi_class") or ""),
        "worker_roi_score": candidate.get("worker_roi_score"),
        "target_reachability_class": reachability.get("reachability_class", ""),
        "target_training_label_allowed": reachability.get("training_label_allowed"),
        "target_worker_log_count": reachability.get("worker_log_count"),
        "target_worker_event_count": reachability.get("worker_event_count"),
        "target_expected_context_worker_event_count": reachability.get(
            "expected_context_worker_event_count"
        ),
        "target_expected_context_executed_event_count": reachability.get(
            "expected_context_executed_event_count"
        ),
        "target_causal_match_count": reachability.get("target_causal_match_count"),
        "target_stage_compatible": reachability.get("stage_compatible"),
        "target_learning_policy_kept": reachability.get("learning_policy_kept"),
        "first_expected_context_skip_reason": reachability.get("first_expected_context_skip_reason"),
    }
    result_roi_class = _roi_class(record)
    record["result_roi_class"] = result_roi_class
    if _has_worker_reachability_evidence(record) and not bool(
        record.get("target_training_label_allowed")
    ):
        record["roi_class"] = "target_not_reached"
    else:
        record["roi_class"] = result_roi_class
    return record


def _target_reachability(
    candidate: dict[str, Any],
    *,
    commands: list[dict[str, Any]],
) -> dict[str, Any]:
    try:
        return _classify_target_reachability(candidate, commands)
    except Exception:
        return {}


def _has_worker_reachability_evidence(record: dict[str, Any]) -> bool:
    if int(record.get("target_worker_log_count") or 0) > 0:
        return True
    if int(record.get("target_worker_event_count") or 0) > 0:
        return True
    return bool(record.get("first_expected_context_skip_reason"))


def _roi_class(record: dict[str, Any]) -> str:
    if not record["baseline_csv_exists"] or not record["worker_csv_exists"]:
        return "missing_result"
    if record["official_bound_effect"]:
        return "invalid_certificate_effect"
    baseline_status_rank = _status_rank(record.get("baseline_status"))
    worker_status_rank = _status_rank(record.get("worker_status"))
    if worker_status_rank > baseline_status_rank:
        return "positive_status_roi"
    if worker_status_rank < baseline_status_rank:
        return "negative_status_roi"
    primal_delta = record.get("primal_improvement")
    exact_delta = record.get("exact_pricing_calls_delta")
    pricing_delta = record.get("pricing_calls_delta")
    time_delta = record.get("solving_time_delta")
    if primal_delta is not None and primal_delta > 1.0e-9:
        return "positive_primal_roi"
    if primal_delta is not None and primal_delta < -1.0e-9:
        return "negative_primal_roi"
    if exact_delta is not None and exact_delta < 0:
        return "positive_retry_roi"
    if pricing_delta is not None and pricing_delta < 0 and (exact_delta is None or exact_delta <= 0):
        return "positive_pricing_roi"
    if time_delta is not None and time_delta < -1.0:
        return "positive_walltime_roi"
    if exact_delta is not None and exact_delta > 0:
        return "negative_retry_roi"
    if time_delta is not None and time_delta > 1.0:
        return "negative_walltime_roi"
    return "no_observed_roi"


def _read_first_csv_row(path: Path) -> dict[str, Any] | None:
    if not Path(path).exists():
        return None
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            return dict(row)
    return None


def _float_value(row: dict[str, Any] | None, key: str) -> float | None:
    if not row:
        return None
    value = row.get(key)
    if value is None or str(value).strip() == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(result) or math.isinf(result) else result


def _int_value(row: dict[str, Any] | None, key: str) -> int | None:
    value = _float_value(row, key)
    return None if value is None else int(value)


def _status(row: dict[str, Any] | None) -> str | None:
    if not row:
        return None
    value = row.get("status")
    return str(value) if value is not None else None


def _status_rank(status: str | None) -> int:
    value = str(status or "").strip().upper()
    if value == "OPTIMAL":
        return 3
    if value in {"TIME_LIMIT", "INCOMPLETE", "FEASIBLE"}:
        return 1
    if value:
        return 0
    return 0


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Worker ROI Solver A/B Audit 报告",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "只读审计 worker-ROI GAT solver A/B 的 CSV 结果。它不运行 BPC / pricing，",
        "不启用 worker，也不产生 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_worker_roi_solver_ab_audit = current",
        f"status = {summary['status']}",
        f"record_count = {summary['record_count']}",
        f"roi_class_counts = {summary['roi_class_counts']}",
        f"target_not_reached_count = {summary['target_not_reached_count']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## Small Records",
        "",
        "```json",
        json.dumps(summary["small_records"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Candidate Records",
        "",
        "```json",
        json.dumps(summary["candidate_records"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 边界",
        "",
        "- 5/10 sentinel 必须保持 OPTIMAL 才能过 no-regression；",
        "- 20 worker 只能作为显式 opt-in ROI probe；",
        "- 任何 official-bound 或 certificate 副作用都阻塞；",
        "- 生产化仍需后续更大矩阵验证。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
