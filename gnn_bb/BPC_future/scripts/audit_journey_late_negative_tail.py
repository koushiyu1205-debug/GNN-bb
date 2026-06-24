#!/usr/bin/env python3
"""Audit Journey late true-negative and weak-negative pricing tails.

This diagnostic-only script reads solver JSONL logs and joins pricing events
with the corresponding column-addition events.  It does not run BPC, pricing,
RMP, or produce any certificate.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_late_negative_tail_audit_20260623")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260623_bpc_future_journey_late_negative_tail_audit_zh.md"
)


def _iter_jsonl(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.suffix == ".jsonl":
            yield path
        elif path.is_dir():
            yield from sorted(path.rglob("*.jsonl"))


def _read_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            events.append(record)
    return events


def _int(record: dict[str, Any], key: str, default: int = 0) -> int:
    value = record.get(key, default)
    if value in (None, ""):
        return int(default)
    try:
        return int(value)
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


def _event_key(record: dict[str, Any]) -> tuple[Any, Any, Any, str]:
    return (
        record.get("node_id"),
        record.get("depth"),
        record.get("cg_iter"),
        str(record.get("pricing_kind") or ""),
    )


def _sample_key(sample: Any) -> str:
    if not isinstance(sample, (list, tuple)):
        return ""
    try:
        values = tuple(int(task) for task in sample)
    except (TypeError, ValueError):
        return ""
    if not values:
        return ""
    return ",".join(str(task) for task in values)


def _sample_keys(samples: Any) -> list[str]:
    if not isinstance(samples, (list, tuple)):
        return []
    keys: list[str] = []
    for sample in samples:
        key = _sample_key(sample)
        if key:
            keys.append(key)
    return keys


def _has_true_negative(record: dict[str, Any]) -> bool:
    return _int(record, "negative_journeys") > 0 or _int(record, "selected_trips") > 0


def _has_weak_negative(record: dict[str, Any]) -> bool:
    return (
        _int(record, "weak_negative_journeys_filtered") > 0
        or _int(record, "profile_weak_filtered_materialized_count") > 0
        or str(record.get("oracle_classification") or "") == "weak_negative_filtered_incomplete"
        or str(record.get("reason") or "") == "weak_negative_journeys_filtered"
    )


def _negative_tail_class(pricing: dict[str, Any], addition: dict[str, Any] | None) -> str:
    true_negative = _has_true_negative(pricing)
    weak_negative = _has_weak_negative(pricing)
    if true_negative and addition is not None:
        active_changed = _int(addition, "active_changed_task_set_count")
        inactive_changed = _int(addition, "inactive_changed_task_set_count")
        new_task_sets = _int(addition, "new_task_set_count")
        productivity = str(addition.get("addition_productivity_class") or "")
        if active_changed > 0:
            return "true_negative_active_support_changing"
        if inactive_changed > 0 or productivity == "changed_inactive_only" or new_task_sets > 0:
            return "true_negative_inactive_only"
        return "true_negative_duplicate_or_unchanged"
    if true_negative:
        return "true_negative_no_addition_observed"
    if weak_negative:
        return "weak_false_negative_filtered"
    return "other_pricing_tail"


def _pricing_row(path: Path, pricing: dict[str, Any], addition: dict[str, Any] | None) -> dict[str, Any]:
    tail_class = _negative_tail_class(pricing, addition)
    has_true_negative = _has_true_negative(pricing)
    has_weak_filtered = _has_weak_negative(pricing)
    changed_samples = _sample_keys(None if addition is None else addition.get("changed_task_set_samples"))
    active_samples = _sample_keys(None if addition is None else addition.get("active_changed_task_set_samples"))
    inactive_samples = _sample_keys(None if addition is None else addition.get("inactive_changed_task_set_samples"))
    weak_samples = _sample_keys(pricing.get("diagnostic_selected_weak_filtered_task_set_samples"))
    return {
        "schema_version": "journey_late_negative_tail_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "log_file": str(path),
        "tail_class": tail_class,
        "has_true_negative": bool(has_true_negative),
        "has_weak_filtered": bool(has_weak_filtered),
        "node_id": pricing.get("node_id"),
        "depth": pricing.get("depth"),
        "cg_iter": pricing.get("cg_iter"),
        "time": pricing.get("time"),
        "pricing_kind": pricing.get("pricing_kind"),
        "pricing_state": pricing.get("pricing_state") or pricing.get("status"),
        "reason": pricing.get("reason"),
        "oracle_classification": pricing.get("oracle_classification"),
        "negative_journeys": pricing.get("negative_journeys"),
        "selected_trips": pricing.get("selected_trips"),
        "best_reduced_cost": pricing.get("best_reduced_cost"),
        "generated_sequences": pricing.get("generated_sequences"),
        "evaluated_timed_trips": pricing.get("evaluated_timed_trips"),
        "pricing_time_limit": pricing.get("pricing_time_limit"),
        "profile_generation_time": pricing.get("profile_generation_time"),
        "profile_dp_time": pricing.get("profile_dp_time"),
        "dp_state_count": pricing.get("dp_state_count"),
        "weak_negative_journeys_filtered": pricing.get("weak_negative_journeys_filtered"),
        "profile_weak_filtered_materialized_count": pricing.get(
            "profile_weak_filtered_materialized_count"
        ),
        "profile_weak_filtered_best_rough_rc": pricing.get("profile_weak_filtered_best_rough_rc"),
        "profile_weak_filtered_best_true_rc": pricing.get("profile_weak_filtered_best_true_rc"),
        "profile_weak_filtered_max_true_minus_rough": pricing.get(
            "profile_weak_filtered_max_true_minus_rough"
        ),
        "global_remaining_rc_lb": pricing.get("global_remaining_rc_lb"),
        "global_remaining_rc_lb_valid": pricing.get("global_remaining_rc_lb_valid"),
        "pricing_proof_kind": pricing.get("pricing_proof_kind"),
        "frontier_unsupported_region_count": pricing.get("frontier_unsupported_region_count"),
        "addition_observed": addition is not None,
        "added_journeys": None if addition is None else addition.get("added_journeys"),
        "new_journeys": None if addition is None else addition.get("new_journeys"),
        "duplicate_journeys": None if addition is None else addition.get("duplicate_journeys"),
        "addition_productivity_class": None
        if addition is None
        else addition.get("addition_productivity_class"),
        "changed_task_set_count": None if addition is None else addition.get("changed_task_set_count"),
        "active_changed_task_set_count": None
        if addition is None
        else addition.get("active_changed_task_set_count"),
        "inactive_changed_task_set_count": None
        if addition is None
        else addition.get("inactive_changed_task_set_count"),
        "new_task_set_count": None if addition is None else addition.get("new_task_set_count"),
        "replacement_task_set_count": None
        if addition is None
        else addition.get("replacement_task_set_count"),
        "changed_task_set_samples": changed_samples,
        "active_changed_task_set_samples": active_samples,
        "inactive_changed_task_set_samples": inactive_samples,
        "weak_task_set_samples": weak_samples,
    }


def summarize(
    paths: Iterable[Path],
    *,
    min_cg_iter: int = 0,
    min_time: float = 0.0,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    log_paths = list(_iter_jsonl(paths))
    for path in log_paths:
        events = _read_events(path)
        additions: dict[tuple[Any, Any, Any, str], list[dict[str, Any]]] = {}
        for record in events:
            if record.get("event") != "journey_column_addition":
                continue
            additions.setdefault(_event_key(record), []).append(record)
        for record in events:
            if record.get("event") != "journey_pricing":
                continue
            if _int(record, "cg_iter") < int(min_cg_iter):
                continue
            if _float(record, "time") < float(min_time):
                continue
            if not (_has_true_negative(record) or _has_weak_negative(record)):
                continue
            matched_additions = additions.get(_event_key(record), [])
            addition = matched_additions[0] if matched_additions else None
            rows.append(_pricing_row(path, record, addition))

    class_counts = Counter(str(row.get("tail_class") or "") for row in rows)
    pricing_kind_counts = Counter(str(row.get("pricing_kind") or "") for row in rows)
    reason_counts = Counter(str(row.get("reason") or "") for row in rows)
    node_counts = Counter(f"depth={row.get('depth')}|node={row.get('node_id')}" for row in rows)
    changed_sample_counts: Counter[str] = Counter()
    weak_sample_counts: Counter[str] = Counter()
    for row in rows:
        for key in row.get("changed_task_set_samples", []) or []:
            changed_sample_counts[str(key)] += 1
        for key in row.get("weak_task_set_samples", []) or []:
            weak_sample_counts[str(key)] += 1

    total_true_negative_events = sum(
        1 for row in rows if bool(row.get("has_true_negative"))
    )
    total_weak_events = sum(1 for row in rows if bool(row.get("has_weak_filtered")))
    total_weak_only_events = int(class_counts.get("weak_false_negative_filtered", 0))
    total_negative_journeys = sum(_int(row, "negative_journeys") for row in rows)
    total_selected_trips = sum(_int(row, "selected_trips") for row in rows)
    total_added_journeys = sum(_int(row, "added_journeys") for row in rows)
    total_active_changed = sum(_int(row, "active_changed_task_set_count") for row in rows)
    total_inactive_changed = sum(_int(row, "inactive_changed_task_set_count") for row in rows)
    total_weak_filtered = sum(_int(row, "weak_negative_journeys_filtered") for row in rows)
    total_weak_materialized = sum(
        _int(row, "profile_weak_filtered_materialized_count") for row in rows
    )
    return {
        "schema_version": "journey_late_negative_tail_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "min_cg_iter": int(min_cg_iter),
        "min_time": round(float(min_time), 6),
        "log_count": len(log_paths),
        "tail_event_count": len(rows),
        "true_negative_event_count": int(total_true_negative_events),
        "weak_filtered_event_count": int(total_weak_events),
        "weak_false_negative_event_count": int(total_weak_only_events),
        "total_negative_journeys": int(total_negative_journeys),
        "total_selected_trips": int(total_selected_trips),
        "total_added_journeys": int(total_added_journeys),
        "total_active_changed_task_sets": int(total_active_changed),
        "total_inactive_changed_task_sets": int(total_inactive_changed),
        "total_weak_negative_journeys_filtered": int(total_weak_filtered),
        "total_profile_weak_filtered_materialized_count": int(total_weak_materialized),
        "tail_class_counts": dict(sorted(class_counts.items())),
        "pricing_kind_counts": dict(sorted(pricing_kind_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "node_counts": dict(sorted(node_counts.items())),
        "changed_task_set_sample_counts": dict(changed_sample_counts.most_common(20)),
        "weak_task_set_sample_counts": dict(weak_sample_counts.most_common(20)),
        "repeated_changed_task_set_sample_count": int(
            sum(1 for count in changed_sample_counts.values() if int(count) > 1)
        ),
        "repeated_weak_task_set_sample_count": int(
            sum(1 for count in weak_sample_counts.values() if int(count) > 1)
        ),
        "interpretation": (
            "True negative rows require exact true-RC verification before addition; "
            "weak false-negative rows are materialized and then filtered. This audit "
            "is suitable for support-aware admission and weak-delay diagnostics, but "
            "is not a pruning or certificate source."
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
    with (output_dir / "late_negative_tail_rows.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_render_report(summary_without_rows, output_dir), encoding="utf-8")


def _render_report(summary: dict[str, Any], output_dir: Path) -> str:
    lines = [
        "# Journey Late Negative Tail Audit",
        "",
        "日期：2026-06-24",
        "",
        "## 目的",
        "",
        "统一解析 solver JSONL 中的 true-negative pricing、column addition 和 weak false-negative filtered 事件，区分 active-support-changing、inactive-only 与 weak/noise tail。该脚本只读日志，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "journey_late_negative_tail_audit = current",
        f"output_dir = {output_dir}",
        f"log_count = {summary.get('log_count')}",
        f"tail_event_count = {summary.get('tail_event_count')}",
        f"min_cg_iter = {summary.get('min_cg_iter')}",
        f"min_time = {summary.get('min_time')}",
        f"true_negative_event_count = {summary.get('true_negative_event_count')}",
        f"weak_filtered_event_count = {summary.get('weak_filtered_event_count')}",
        f"weak_false_negative_event_count = {summary.get('weak_false_negative_event_count')}",
        f"total_active_changed_task_sets = {summary.get('total_active_changed_task_sets')}",
        f"total_inactive_changed_task_sets = {summary.get('total_inactive_changed_task_sets')}",
        "runs_bpc_or_pricing = false",
        "certificate_effect = false",
        "official_bound_effect = false",
        "```",
        "",
        "## 分类",
        "",
        "```json",
        json.dumps(summary.get("tail_class_counts", {}), ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 定价类型",
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
    parser.add_argument("--min-cg-iter", type=int, default=0)
    parser.add_argument("--min-time", type=float, default=0.0)
    args = parser.parse_args()
    summary = summarize(args.paths, min_cg_iter=args.min_cg_iter, min_time=args.min_time)
    write_outputs(summary, args.output_dir, args.report)
    printable = dict(summary)
    printable.pop("rows", None)
    print(json.dumps(printable, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
