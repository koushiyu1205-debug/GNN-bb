#!/usr/bin/env python3
"""Audit GAT target-priority worker A/B result CSVs.

The audit is read-only.  It compares no-learning baseline runs against
explicit opt-in target-priority worker runs and reports ROI signals without
changing solver behavior or certificate semantics.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


DEFAULT_RUNBOOK_SUMMARIES = (
    Path("BPC_future/results/gat_target_priority_worker_ab_20260614/summary.json"),
    Path("BPC_future/results/gat_target_priority_worker_ab_auto_candidates_20260614/summary.json"),
    Path("BPC_future/results/gat_target_priority_worker_ab_20roi_smoke_auto_20260614/summary.json"),
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_target_priority_worker_ab_audit_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_gat_target_priority_worker_ab_audit_zh.md"
)


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


def _roi_class(record: dict[str, Any]) -> str:
    if not record["baseline_csv_exists"] or not record["worker_csv_exists"]:
        return "missing_result"
    if record["official_bound_effect"]:
        return "invalid_certificate_effect"
    primal_delta = record.get("primal_improvement")
    columns_delta = record.get("columns_delta")
    if primal_delta is not None and primal_delta > 1.0e-9:
        return "positive_primal_roi"
    if columns_delta is not None and columns_delta > 0:
        return "columns_only_roi"
    if primal_delta is not None and primal_delta < -1.0e-9:
        return "negative_primal_roi"
    return "no_observed_roi"


def _candidate_record(
    candidate: dict[str, Any],
    *,
    baseline_fallbacks: dict[str, tuple[Path, dict[str, Any]]],
) -> dict[str, Any]:
    baseline_csv = Path(str(candidate.get("baseline_csv") or ""))
    worker_csv = Path(str(candidate.get("worker_csv") or ""))
    instance = str(candidate.get("instance") or "")
    baseline = _read_first_csv_row(baseline_csv)
    fallback_used = False
    if baseline is None and instance in baseline_fallbacks:
        baseline_csv, baseline = baseline_fallbacks[instance]
        fallback_used = True
    worker = _read_first_csv_row(worker_csv)
    baseline_primal = _float_value(baseline, "primal_bound")
    worker_primal = _float_value(worker, "primal_bound")
    baseline_dual = _float_value(baseline, "dual_bound")
    worker_dual = _float_value(worker, "dual_bound")
    baseline_columns = _int_value(baseline, "columns")
    worker_columns = _int_value(worker, "columns")
    baseline_exact = _int_value(baseline, "exact_pricing_calls")
    worker_exact = _int_value(worker, "exact_pricing_calls")
    baseline_sequences = _int_value(baseline, "generated_sequences")
    worker_sequences = _int_value(worker, "generated_sequences")
    record = {
        "name": str(candidate.get("name") or ""),
        "instance": instance,
        "expected_context_hash": str(candidate.get("expected_context_hash") or ""),
        "target_sequence": list(candidate.get("target_sequence") or []),
        "target_arc_option_sequence": list(candidate.get("target_arc_option_sequence") or []),
        "baseline_csv": str(baseline_csv),
        "baseline_fallback_used": fallback_used,
        "worker_csv": str(worker_csv),
        "baseline_csv_exists": baseline is not None,
        "worker_csv_exists": worker is not None,
        "baseline_status": _status(baseline),
        "worker_status": _status(worker),
        "baseline_primal": baseline_primal,
        "worker_primal": worker_primal,
        "primal_improvement": (
            None
            if baseline_primal is None or worker_primal is None
            else baseline_primal - worker_primal
        ),
        "baseline_dual_bound": baseline_dual,
        "worker_dual_bound": worker_dual,
        "baseline_columns": baseline_columns,
        "worker_columns": worker_columns,
        "columns_delta": (
            None if baseline_columns is None or worker_columns is None else worker_columns - baseline_columns
        ),
        "baseline_exact_pricing_calls": baseline_exact,
        "worker_exact_pricing_calls": worker_exact,
        "exact_pricing_calls_delta": (
            None if baseline_exact is None or worker_exact is None else worker_exact - baseline_exact
        ),
        "generated_sequences_delta": (
            None
            if baseline_sequences is None or worker_sequences is None
            else worker_sequences - baseline_sequences
        ),
        "official_bound_effect": bool(worker_dual is not None and baseline_dual != worker_dual),
        "certificate_effect": False,
    }
    record["roi_class"] = _roi_class(record)
    return record


def audit_results(
    *,
    runbook_summaries: list[Path],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    candidates: list[dict[str, Any]] = []
    loaded_summaries: list[str] = []
    for summary_path in runbook_summaries:
        path = Path(summary_path)
        if not path.exists():
            continue
        summary = json.loads(path.read_text(encoding="utf-8"))
        loaded_summaries.append(str(path))
        if summary.get("certificate_ready") or summary.get("official_bound_effect"):
            raise ValueError(f"runbook summary has forbidden certificate effect: {path}")
        for candidate in summary.get("candidate_runs") or []:
            candidates.append(dict(candidate))

    baseline_fallbacks: dict[str, tuple[Path, dict[str, Any]]] = {}
    for candidate in candidates:
        instance = str(candidate.get("instance") or "")
        baseline_csv = Path(str(candidate.get("baseline_csv") or ""))
        baseline = _read_first_csv_row(baseline_csv)
        if instance and baseline is not None:
            baseline_fallbacks.setdefault(instance, (baseline_csv, baseline))

    records = [
        _candidate_record(candidate, baseline_fallbacks=baseline_fallbacks)
        for candidate in candidates
    ]

    roi_counts: dict[str, int] = {}
    for record in records:
        roi_counts[record["roi_class"]] = roi_counts.get(record["roi_class"], 0) + 1
    positive = [record for record in records if record["roi_class"] == "positive_primal_roi"]
    no_roi = [record for record in records if record["roi_class"] == "no_observed_roi"]
    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "no_certificate_effect": all(not record["certificate_effect"] for record in records),
        "no_official_bound_effect": all(not record["official_bound_effect"] for record in records),
        "has_records": bool(records),
        "has_positive_and_nonpositive_evidence": bool(positive) and bool(no_roi),
    }
    summary = {
        "schema_version": "gat_target_priority_worker_ab_audit_v1",
        "status": "audited" if records else "no_records",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "runbook_summaries": loaded_summaries,
        "record_count": len(records),
        "roi_class_counts": dict(sorted(roi_counts.items())),
        "positive_primal_roi_count": len(positive),
        "no_observed_roi_count": len(no_roi),
        "records": records,
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "next_decision": (
            "keep_worker_opt_in_and_expand_ab"
            if positive and no_roi
            else "collect_more_ab_evidence"
        ),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Target-Priority Worker A/B Audit 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "聚合 GAT target-priority worker A/B 的 CSV 结果，判断候选是否有真实 ROI。",
        "该脚本只读 CSV，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_target_priority_worker_ab_audit = current",
        f"status = {summary['status']}",
        f"record_count = {summary['record_count']}",
        f"roi_class_counts = {summary['roi_class_counts']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## Records",
        "",
        "```json",
        json.dumps(summary["records"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 判断",
        "",
        "- `positive_primal_roi` 表示 worker primal 严格优于同实例 baseline；",
        "- `no_observed_roi` 表示 worker 与 baseline 没有可观测改善；",
        "- 只要正负 ROI 同时存在，GAT HIGH_PRIORITY 就不能直接默认触发 worker；",
        "- 所有结果都不能参与 no-negative certificate 或 official lower bound。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runbook-summary",
        dest="runbook_summaries",
        action="append",
        type=Path,
        default=[],
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    runbook_summaries = list(args.runbook_summaries or [])
    if not runbook_summaries:
        runbook_summaries = list(DEFAULT_RUNBOOK_SUMMARIES)
    summary = audit_results(
        runbook_summaries=runbook_summaries,
        output_dir=args.output_dir,
        report=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
