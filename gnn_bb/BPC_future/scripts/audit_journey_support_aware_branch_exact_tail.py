#!/usr/bin/env python3
"""Audit support-aware categories for branch exact pricing tails.

This diagnostic-only script reads solver JSONL logs. It does not run BPC,
pricing, RMP, or produce any certificate or official bound.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_support_aware_branch_exact_tail_audit_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_journey_support_aware_branch_exact_tail_audit_zh.md"
)

ROW_FIELDS = [
    "schema_version",
    "diagnostic_only",
    "runs_bpc_or_pricing",
    "certificate_effect",
    "official_bound_effect",
    "log_file",
    "time",
    "node_id",
    "depth",
    "cg_iter",
    "pricing_kind",
    "status",
    "reason",
    "support_tail_class",
    "support_aware_admission_enabled",
    "candidate_journeys",
    "admitted_journeys",
    "true_negative_journeys",
    "high_priority_journeys",
    "delay_queue_journeys",
    "released_journeys",
    "delayed_negative_journeys",
    "support_candidate_active_support_changing_journeys",
    "support_candidate_new_task_set_journeys",
    "support_candidate_inactive_only_journeys",
    "support_online_high_priority_journeys",
    "support_high_priority_journeys",
    "support_delayed_inactive_only_journeys",
    "support_demoted_safe_hit_journeys",
    "support_delay_depth_blocked_journeys",
    "certificate_candidate",
    "certificate_blocked_by_delayed_negative",
    "exact_path_preserved",
]


def _iter_jsonl(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.suffix == ".jsonl":
            yield path
        elif path.is_dir():
            yield from sorted(path.rglob("*.jsonl"))


def _read_events(path: Path) -> Iterable[dict[str, Any]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            yield record


def _int(record: dict[str, Any], key: str, default: int = 0) -> int:
    value = record.get(key, default)
    if value in (None, ""):
        return int(default)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _float(record: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = record.get(key, default)
    if value in (None, ""):
        return float(default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _bool(record: dict[str, Any], key: str) -> bool:
    value = record.get(key)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _matches_pricing_kind(record: dict[str, Any], prefixes: tuple[str, ...]) -> bool:
    pricing_kind = str(record.get("pricing_kind") or "")
    return bool(pricing_kind) and any(pricing_kind.startswith(prefix) for prefix in prefixes)


def _support_tail_class(record: dict[str, Any]) -> str:
    active = _int(record, "support_candidate_active_support_changing_journeys")
    new = _int(record, "support_candidate_new_task_set_journeys")
    inactive = _int(record, "support_candidate_inactive_only_journeys")
    if active > 0:
        return "active_support_changing"
    if new > 0:
        return "new_task_set"
    if inactive > 0:
        return "inactive_only"
    if _bool(record, "support_aware_admission_enabled"):
        return "support_context_no_candidate_class"
    return "support_context_missing_or_disabled"


def _row(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    row = {
        "schema_version": "journey_support_aware_branch_exact_tail_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "log_file": str(path),
        "support_tail_class": _support_tail_class(record),
    }
    for field in ROW_FIELDS:
        if field in row:
            continue
        row[field] = record.get(field)
    return row


def summarize(
    paths: Iterable[Path],
    *,
    min_depth: int = 1,
    min_time: float = 0.0,
    pricing_kind_prefixes: tuple[str, ...] = ("exact",),
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    log_paths = list(_iter_jsonl(paths))
    prefixes = tuple(str(prefix) for prefix in pricing_kind_prefixes if str(prefix))
    if not prefixes:
        prefixes = ("exact",)
    for path in log_paths:
        for record in _read_events(path):
            if record.get("event") != "journey_gat_target_mode_admission":
                continue
            if _int(record, "depth") < int(min_depth):
                continue
            if _float(record, "time") < float(min_time):
                continue
            if not _matches_pricing_kind(record, prefixes):
                continue
            rows.append(_row(path, record))

    class_counts = Counter(str(row.get("support_tail_class") or "") for row in rows)
    pricing_kind_counts = Counter(str(row.get("pricing_kind") or "") for row in rows)
    reason_counts = Counter(str(row.get("reason") or "") for row in rows)
    status_counts = Counter(str(row.get("status") or "") for row in rows)
    depth_counts = Counter(str(row.get("depth")) for row in rows)
    node_counts = Counter(f"depth={row.get('depth')}|node={row.get('node_id')}" for row in rows)

    total_candidate = sum(_int(row, "candidate_journeys") for row in rows)
    total_true_negative = sum(_int(row, "true_negative_journeys") for row in rows)
    total_active = sum(_int(row, "support_candidate_active_support_changing_journeys") for row in rows)
    total_new = sum(_int(row, "support_candidate_new_task_set_journeys") for row in rows)
    total_inactive = sum(_int(row, "support_candidate_inactive_only_journeys") for row in rows)
    total_delayed_inactive = sum(_int(row, "support_delayed_inactive_only_journeys") for row in rows)
    total_delay_depth_blocked = sum(_int(row, "support_delay_depth_blocked_journeys") for row in rows)
    support_enabled_rows = sum(1 for row in rows if _bool(row, "support_aware_admission_enabled"))
    blocked_rows = sum(1 for row in rows if _bool(row, "certificate_blocked_by_delayed_negative"))

    inactive_share = 0.0
    support_total = int(total_active + total_new + total_inactive)
    if support_total > 0:
        inactive_share = float(total_inactive) / float(support_total)

    return {
        "schema_version": "journey_support_aware_branch_exact_tail_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "min_depth": int(min_depth),
        "min_time": round(float(min_time), 6),
        "pricing_kind_prefixes": list(prefixes),
        "log_count": len(log_paths),
        "admission_event_count": len(rows),
        "support_enabled_event_count": int(support_enabled_rows),
        "certificate_blocked_by_delayed_negative_event_count": int(blocked_rows),
        "total_candidate_journeys": int(total_candidate),
        "total_true_negative_journeys": int(total_true_negative),
        "total_support_active_journeys": int(total_active),
        "total_support_new_journeys": int(total_new),
        "total_support_inactive_journeys": int(total_inactive),
        "total_support_delayed_inactive_journeys": int(total_delayed_inactive),
        "total_support_delay_depth_blocked_journeys": int(total_delay_depth_blocked),
        "support_inactive_share": round(float(inactive_share), 6),
        "support_tail_class_counts": dict(sorted(class_counts.items())),
        "pricing_kind_counts": dict(sorted(pricing_kind_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "depth_counts": dict(sorted(depth_counts.items())),
        "node_counts": dict(sorted(node_counts.items())),
        "interpretation": (
            "Rows are support-aware admission log events in branch exact pricing tails. "
            "The audit only measures active/new/inactive-only composition; it does not "
            "change column admission, certify no-negative pricing, or provide official "
            "node bounds. A large inactive share would justify a later opt-in delay A/B; "
            "a low inactive share points toward branch-impact, child proof-cost, cuts, "
            "or incumbent-search rather than inactive-only delay."
        ),
        "rows": rows,
    }


def write_outputs(summary: dict[str, Any], output_dir: Path, report: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = list(summary.get("rows", []))
    summary_without_rows = dict(summary)
    summary_without_rows.pop("rows", None)
    (output_dir / "summary.json").write_text(
        json.dumps(summary_without_rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (output_dir / "support_aware_branch_exact_tail_rows.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    with (output_dir / "support_aware_branch_exact_tail_rows.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=ROW_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in ROW_FIELDS})
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_render_report(summary_without_rows, output_dir), encoding="utf-8")


def _render_report(summary: dict[str, Any], output_dir: Path) -> str:
    lines = [
        "# Journey Support-Aware Branch Exact Tail Audit",
        "",
        "日期：2026-06-24",
        "",
        "## 目的",
        "",
        "解析 solver JSONL 中 branch exact pricing tail 的 support-aware admission 日志，统计 active-support-changing、new task-set 与 inactive-only 的构成。该脚本只读日志，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "journey_support_aware_branch_exact_tail_audit = current",
        f"output_dir = {output_dir}",
        f"log_count = {summary.get('log_count')}",
        f"admission_event_count = {summary.get('admission_event_count')}",
        f"support_enabled_event_count = {summary.get('support_enabled_event_count')}",
        f"min_depth = {summary.get('min_depth')}",
        f"min_time = {summary.get('min_time')}",
        f"pricing_kind_prefixes = {summary.get('pricing_kind_prefixes')}",
        f"total_candidate_journeys = {summary.get('total_candidate_journeys')}",
        f"total_true_negative_journeys = {summary.get('total_true_negative_journeys')}",
        f"total_support_active_journeys = {summary.get('total_support_active_journeys')}",
        f"total_support_new_journeys = {summary.get('total_support_new_journeys')}",
        f"total_support_inactive_journeys = {summary.get('total_support_inactive_journeys')}",
        f"support_inactive_share = {summary.get('support_inactive_share')}",
        "runs_bpc_or_pricing = false",
        "certificate_effect = false",
        "official_bound_effect = false",
        "```",
        "",
        "## Support 分类",
        "",
        "```json",
        json.dumps(summary.get("support_tail_class_counts", {}), ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Pricing Kind",
        "",
        "```json",
        json.dumps(summary.get("pricing_kind_counts", {}), ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 解释",
        "",
        str(summary.get("interpretation") or ""),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-depth", type=int, default=1)
    parser.add_argument("--min-time", type=float, default=0.0)
    parser.add_argument(
        "--pricing-kind-prefix",
        action="append",
        default=None,
        help="Pricing kind prefix to include. Defaults to exact.",
    )
    args = parser.parse_args()
    prefixes = tuple(args.pricing_kind_prefix or ("exact",))
    summary = summarize(
        args.paths,
        min_depth=args.min_depth,
        min_time=args.min_time,
        pricing_kind_prefixes=prefixes,
    )
    write_outputs(summary, args.output_dir, args.report)
    printable = dict(summary)
    printable.pop("rows", None)
    print(json.dumps(printable, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
