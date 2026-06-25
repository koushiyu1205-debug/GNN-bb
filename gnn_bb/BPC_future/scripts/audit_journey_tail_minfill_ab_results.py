#!/usr/bin/env python3
"""Audit paired Journey tail low-min-fill A/B replay results.

This script reads an existing runbook and already-finished solver outputs.  It
does not run BPC, pricing, RMP, or produce certificates.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_tail_minfill_ab_results_20260625")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260625_bpc_future_journey_tail_minfill_ab_results_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_first_csv_row(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            return dict(row)
    return {}


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if path.is_dir():
        for child in sorted(path.rglob("*.jsonl")):
            yield from _iter_jsonl(child)
        return
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            yield record


def _float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return int(default)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _csv_metrics(result_dir: Path) -> dict[str, Any]:
    row = _read_first_csv_row(result_dir / "results.csv")
    return {
        "result_dir": str(result_dir),
        "has_result": bool(row),
        "status": row.get("status"),
        "external_timeout": _bool(row.get("external_timeout")),
        "wall_time": round(_float(row.get("wall_time")), 6),
        "solving_time": round(_float(row.get("solving_time")), 6),
        "node_count": _int(row.get("node_count")),
        "rmp_solves": _int(row.get("rmp_solves")),
        "pricing_calls": _int(row.get("pricing_calls")),
        "exact_pricing_calls": _int(row.get("exact_pricing_calls")),
        "generated_sequences": _int(row.get("generated_sequences")),
        "evaluated_timed_trips": _int(row.get("evaluated_timed_trips")),
        "columns": _int(row.get("columns")),
        "primal_bound": row.get("primal_bound"),
        "dual_bound": row.get("dual_bound"),
        "gap": row.get("gap"),
    }


def _tail_minfill_log_metrics(result_dir: Path) -> dict[str, Any]:
    log_dir = result_dir / "logs"
    reason_counts: Counter[str] = Counter()
    pricing_state_counts: Counter[str] = Counter()
    candidate_count = 0
    applied_count = 0
    optin_disabled_count = 0
    completion_retry_count = 0
    negative_journeys = 0
    selected_trips = 0
    direct_label_min_fill_values: set[int] = set()
    for record in _iter_jsonl(log_dir):
        if record.get("event") == "journey_exact_pricing_completion_bound_retry":
            mode = record.get("retry_mode")
            if isinstance(mode, dict):
                if _bool(mode.get("completion_bound_diverse_harvest_tail_min_fill_candidate")):
                    candidate_count += 1
                if _bool(mode.get("completion_bound_diverse_harvest_tail_min_fill_applied")):
                    applied_count += 1
                reason = str(mode.get("completion_bound_diverse_harvest_tail_min_fill_reason") or "")
                if reason:
                    reason_counts[reason] += 1
                    if reason == "optin_disabled":
                        optin_disabled_count += 1
        if record.get("event") == "journey_pricing" and str(record.get("pricing_kind") or "").startswith(
            "exact_completion_bound"
        ):
            completion_retry_count += 1
            pricing_state_counts[
                f"{record.get('pricing_state')}:{record.get('reason')}"
            ] += 1
            negative_journeys += _int(record.get("negative_journeys"))
            selected_trips += _int(record.get("selected_trips"))
            if record.get("direct_label_harvest_min_fill") is not None:
                direct_label_min_fill_values.add(_int(record.get("direct_label_harvest_min_fill")))
    return {
        "tail_minfill_candidate_count": candidate_count,
        "tail_minfill_applied_count": applied_count,
        "tail_minfill_optin_disabled_count": optin_disabled_count,
        "tail_minfill_reason_counts": dict(sorted(reason_counts.items())),
        "completion_retry_count": completion_retry_count,
        "completion_retry_state_counts": dict(sorted(pricing_state_counts.items())),
        "completion_retry_negative_journeys": int(negative_journeys),
        "completion_retry_selected_trips": int(selected_trips),
        "direct_label_harvest_min_fill_values": sorted(direct_label_min_fill_values),
    }


def _delta(optin: dict[str, Any], baseline: dict[str, Any], key: str) -> float:
    return round(_float(optin.get(key)) - _float(baseline.get(key)), 6)


def _classify(
    baseline: dict[str, Any],
    optin: dict[str, Any],
    *,
    target_wall: float,
    wall_eps: float,
) -> tuple[str, str]:
    baseline_status = str(baseline.get("status") or "")
    optin_status = str(optin.get("status") or "")
    baseline_wall = _float(baseline.get("wall_time"))
    optin_wall = _float(optin.get("wall_time"))
    if not baseline.get("has_result") or not optin.get("has_result"):
        return "missing_result", "baseline_or_optin_result_missing"
    if optin_status == "OPTIMAL" and optin_wall <= float(target_wall):
        if baseline_status != "OPTIMAL":
            return "strong_positive", "nonoptimal_to_target_optimal"
        if baseline_wall > float(target_wall):
            return "strong_positive", "slow_optimal_to_target_optimal"
        if optin_wall + wall_eps < baseline_wall:
            return "positive_speedup", "already_target_optimal_wall_reduced"
    if baseline_status == "OPTIMAL" and baseline_wall <= float(target_wall):
        if optin_status != "OPTIMAL":
            return "regression", "target_optimal_lost"
        if optin_wall > baseline_wall + wall_eps:
            return "regression", "target_optimal_wall_regressed"
    if optin_status != "OPTIMAL" and baseline_status != "OPTIMAL":
        if optin_wall + wall_eps < baseline_wall:
            return "weak_improvement", "both_nonoptimal_wall_reduced"
        return "hard_negative", "both_nonoptimal_no_target_resolution"
    if baseline_status == "OPTIMAL" and optin_status == "OPTIMAL":
        if optin_wall + wall_eps < baseline_wall:
            return "positive_speedup", "both_optimal_wall_reduced"
        if optin_wall > baseline_wall + wall_eps:
            return "regression", "both_optimal_wall_regressed"
    return "no_effect", "no_target_or_wall_change"


def audit_tail_minfill_ab(
    *,
    runbook: Path,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    target_wall: float = 200.0,
    wall_eps: float = 1.0,
) -> dict[str, Any]:
    payload = _read_json(runbook)
    entries = payload.get("entries") if isinstance(payload.get("entries"), list) else []
    rows: list[dict[str, Any]] = []
    class_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        baseline_dir = Path(str(entry.get("baseline_result_dir") or ""))
        optin_dir = Path(str(entry.get("optin_result_dir") or ""))
        baseline = {**_csv_metrics(baseline_dir), **_tail_minfill_log_metrics(baseline_dir)}
        optin = {**_csv_metrics(optin_dir), **_tail_minfill_log_metrics(optin_dir)}
        classification, reason = _classify(
            baseline,
            optin,
            target_wall=target_wall,
            wall_eps=wall_eps,
        )
        class_counts[classification] += 1
        reason_counts[reason] += 1
        row = {
            "schema_version": "journey_tail_minfill_ab_result_row_v1",
            "diagnostic_only": True,
            "runs_bpc_or_pricing": False,
            "certificate_effect": False,
            "official_bound_effect": False,
            "instance": entry.get("instance"),
            "entry_id": entry.get("entry_id"),
            "classification": classification,
            "classification_reason": reason,
            "source_completion_retry_class": entry.get("source_completion_retry_class"),
            "source_tail_min_fill_candidate_count": entry.get("source_tail_min_fill_candidate_count"),
            "baseline": baseline,
            "optin": optin,
            "deltas": {
                key: _delta(optin, baseline, key)
                for key in (
                    "wall_time",
                    "solving_time",
                    "node_count",
                    "rmp_solves",
                    "pricing_calls",
                    "exact_pricing_calls",
                    "generated_sequences",
                    "evaluated_timed_trips",
                    "columns",
                    "completion_retry_count",
                    "completion_retry_negative_journeys",
                    "completion_retry_selected_trips",
                )
            },
        }
        rows.append(row)
    summary = {
        "schema_version": "journey_tail_minfill_ab_results_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "runbook": str(runbook),
        "target_wall": float(target_wall),
        "wall_eps": float(wall_eps),
        "entry_count": len(entries),
        "row_count": len(rows),
        "classification_counts": dict(sorted(class_counts.items())),
        "classification_reason_counts": dict(sorted(reason_counts.items())),
        "strong_positive_count": int(class_counts.get("strong_positive", 0)),
        "regression_count": int(class_counts.get("regression", 0)),
        "hard_negative_count": int(class_counts.get("hard_negative", 0)),
        "rows": rows,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "tail_minfill_ab_rows.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Journey Tail Min-Fill A/B Results",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "读取已完成的 paired replay 输出，判断低 min-fill opt-in 是 strong positive、"
        "hard negative、regression 还是 no-effect。该脚本只读日志，不运行 BPC / pricing / RMP。",
        "",
        "## 机器字段",
        "",
        "```text",
        "journey_tail_minfill_ab_results = current",
        f"entry_count = {summary['entry_count']}",
        f"row_count = {summary['row_count']}",
        f"target_wall = {summary['target_wall']}",
        f"classification_counts = {summary['classification_counts']}",
        f"classification_reason_counts = {summary['classification_reason_counts']}",
        f"strong_positive_count = {summary['strong_positive_count']}",
        f"hard_negative_count = {summary['hard_negative_count']}",
        f"regression_count = {summary['regression_count']}",
        "runs_bpc_or_pricing = false",
        "certificate_effect = false",
        "official_bound_effect = false",
        "```",
        "",
        "## Rows",
        "",
        "```json",
        json.dumps(summary["rows"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runbook", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--target-wall", type=float, default=200.0)
    parser.add_argument("--wall-eps", type=float, default=1.0)
    args = parser.parse_args()
    audit_tail_minfill_ab(
        runbook=args.runbook,
        output_dir=args.output_dir,
        report=args.report,
        target_wall=args.target_wall,
        wall_eps=args.wall_eps,
    )


if __name__ == "__main__":
    main()
