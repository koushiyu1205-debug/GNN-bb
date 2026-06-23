#!/usr/bin/env python3
"""Audit weak rough-negative Journey pricing tails from JSONL logs.

The script is diagnostic-only.  It reads solver JSONL logs and extracts
pricing events where profile/rough reduced-cost candidates were materialized
but filtered by true-RC verification.  It does not run BPC, pricing, RMP, or
produce any certificate.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_weak_negative_tail_audit_20260623")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260623_bpc_future_journey_weak_negative_tail_audit_zh.md"
)


def _iter_jsonl(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.suffix == ".jsonl":
            yield path
        elif path.is_dir():
            yield from sorted(path.rglob("*.jsonl"))


def _read_events(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def _int(record: dict[str, Any], key: str, default: int = 0) -> int:
    value = record.get(key, default)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float(record: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = record.get(key, default)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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


def _weak_event(record: dict[str, Any]) -> bool:
    if record.get("event") != "journey_pricing":
        return False
    return (
        _int(record, "weak_negative_journeys_filtered") > 0
        or _int(record, "profile_weak_filtered_materialized_count") > 0
        or str(record.get("oracle_classification") or "") == "weak_negative_filtered_incomplete"
        or str(record.get("reason") or "") == "weak_negative_journeys_filtered"
    )


def _weak_row(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    samples = [
        tuple(int(task) for task in sample)
        for sample in tuple(record.get("diagnostic_selected_weak_filtered_task_set_samples") or tuple())
        if _sample_key(sample)
    ]
    return {
        "schema_version": "journey_weak_negative_tail_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "log_file": str(path),
        "node_id": record.get("node_id"),
        "depth": record.get("depth"),
        "cg_iter": record.get("cg_iter"),
        "time": record.get("time"),
        "pricing_kind": record.get("pricing_kind"),
        "pricing_state": record.get("pricing_state") or record.get("status"),
        "reason": record.get("reason"),
        "oracle_classification": record.get("oracle_classification"),
        "pricing_dual_source": record.get("pricing_dual_source"),
        "pricing_time_limit": record.get("pricing_time_limit"),
        "profile_generation_time": record.get("profile_generation_time"),
        "profile_dp_time": record.get("profile_dp_time"),
        "dp_state_count": record.get("dp_state_count"),
        "dp_profile_record_scans": record.get("dp_profile_record_scans"),
        "negative_journeys": record.get("negative_journeys"),
        "selected_trips": record.get("selected_trips"),
        "profile_negative_candidate_count": record.get("profile_negative_candidate_count"),
        "profile_negative_unique_mask_count": record.get("profile_negative_unique_mask_count"),
        "profile_negative_selected_candidate_count": record.get(
            "profile_negative_selected_candidate_count"
        ),
        "profile_selected_candidate_input_count": record.get("profile_selected_candidate_input_count"),
        "profile_selected_candidate_scanned_count": record.get("profile_selected_candidate_scanned_count"),
        "profile_selected_candidate_materialized_count": record.get(
            "profile_selected_candidate_materialized_count"
        ),
        "weak_negative_journeys_filtered": record.get("weak_negative_journeys_filtered"),
        "profile_weak_filtered_materialized_count": record.get(
            "profile_weak_filtered_materialized_count"
        ),
        "profile_weak_filtered_best_rough_rc": record.get("profile_weak_filtered_best_rough_rc"),
        "profile_weak_filtered_best_true_rc": record.get("profile_weak_filtered_best_true_rc"),
        "profile_weak_filtered_max_true_minus_rough": record.get(
            "profile_weak_filtered_max_true_minus_rough"
        ),
        "profile_weak_filtered_max_true_minus_rough_mask": record.get(
            "profile_weak_filtered_max_true_minus_rough_mask"
        ),
        "weak_task_set_samples": samples,
    }


def summarize(paths: Iterable[Path]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    log_paths = list(_iter_jsonl(paths))
    for path in log_paths:
        for record in _read_events(path):
            if _weak_event(record):
                rows.append(_weak_row(path, record))

    pricing_kind_counts = Counter(str(row.get("pricing_kind") or "") for row in rows)
    reason_counts = Counter(str(row.get("reason") or "") for row in rows)
    node_counts = Counter(
        f"depth={row.get('depth')}|node={row.get('node_id')}" for row in rows
    )
    mask_counts = Counter(
        str(row.get("profile_weak_filtered_max_true_minus_rough_mask"))
        for row in rows
        if row.get("profile_weak_filtered_max_true_minus_rough_mask") is not None
    )
    sample_counts: Counter[str] = Counter()
    for row in rows:
        for sample in row.get("weak_task_set_samples", []):
            key = _sample_key(sample)
            if key:
                sample_counts[key] += 1

    total_weak_filtered = sum(_int(row, "weak_negative_journeys_filtered") for row in rows)
    total_materialized = sum(_int(row, "profile_weak_filtered_materialized_count") for row in rows)
    total_profile_generation_time = sum(_float(row, "profile_generation_time") for row in rows)
    total_profile_dp_time = sum(_float(row, "profile_dp_time") for row in rows)
    total_dp_states = sum(_int(row, "dp_state_count") for row in rows)
    max_true_minus_rough = max(
        (_float(row, "profile_weak_filtered_max_true_minus_rough") for row in rows),
        default=0.0,
    )
    best_rough = min(
        (
            _float(row, "profile_weak_filtered_best_rough_rc")
            for row in rows
            if row.get("profile_weak_filtered_best_rough_rc") is not None
        ),
        default=None,
    )
    best_true = min(
        (
            _float(row, "profile_weak_filtered_best_true_rc")
            for row in rows
            if row.get("profile_weak_filtered_best_true_rc") is not None
        ),
        default=None,
    )
    repeated_sample_count = sum(1 for count in sample_counts.values() if int(count) > 1)
    repeated_mask_count = sum(1 for count in mask_counts.values() if int(count) > 1)

    return {
        "schema_version": "journey_weak_negative_tail_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "log_count": len(log_paths),
        "weak_event_count": len(rows),
        "weak_training_row_count": len(rows),
        "total_weak_negative_journeys_filtered": int(total_weak_filtered),
        "total_profile_weak_filtered_materialized_count": int(total_materialized),
        "total_profile_generation_time": round(float(total_profile_generation_time), 6),
        "total_profile_dp_time": round(float(total_profile_dp_time), 6),
        "total_dp_state_count": int(total_dp_states),
        "max_true_minus_rough": round(float(max_true_minus_rough), 9),
        "best_rough_rc": None if best_rough is None else round(float(best_rough), 9),
        "best_true_rc_after_materialization": None if best_true is None else round(float(best_true), 9),
        "pricing_kind_counts": dict(sorted(pricing_kind_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "node_counts": dict(sorted(node_counts.items())),
        "weak_mask_counts": dict(mask_counts.most_common(20)),
        "weak_task_set_sample_counts": dict(sample_counts.most_common(20)),
        "repeated_weak_mask_count": int(repeated_mask_count),
        "repeated_weak_task_set_sample_count": int(repeated_sample_count),
        "interpretation": (
            "weak rough-negative events are true-RC filtered after materialization; "
            "they are useful as GAT/priority/delay training negatives, but cannot "
            "be used for pruning or certificate."
        ),
        "rows": rows,
    }


def write_outputs(summary: dict[str, Any], output_dir: Path, report: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = list(summary.get("rows", []))
    summary_path = output_dir / "summary.json"
    rows_path = output_dir / "weak_negative_tail_rows.jsonl"
    summary_without_rows = dict(summary)
    summary_without_rows.pop("rows", None)
    summary_path.write_text(
        json.dumps(summary_without_rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with rows_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_render_report(summary_without_rows, output_dir), encoding="utf-8")


def _render_report(summary: dict[str, Any], output_dir: Path) -> str:
    lines = [
        "# Journey Weak Negative Tail Audit",
        "",
        "日期：2026-06-23",
        "",
        "## 目的",
        "",
        "读取 solver JSONL 日志，提取 rough reduced-cost 为负、但 true-RC 复算后被过滤的 weak negative tail 事件。该脚本只读日志，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "journey_weak_negative_tail_audit = current",
        f"output_dir = {output_dir}",
        f"log_count = {summary.get('log_count')}",
        f"weak_event_count = {summary.get('weak_event_count')}",
        f"weak_training_row_count = {summary.get('weak_training_row_count')}",
        f"total_weak_negative_journeys_filtered = {summary.get('total_weak_negative_journeys_filtered')}",
        f"total_profile_weak_filtered_materialized_count = {summary.get('total_profile_weak_filtered_materialized_count')}",
        f"total_profile_generation_time = {summary.get('total_profile_generation_time')}",
        f"total_profile_dp_time = {summary.get('total_profile_dp_time')}",
        f"max_true_minus_rough = {summary.get('max_true_minus_rough')}",
        f"best_rough_rc = {summary.get('best_rough_rc')}",
        f"best_true_rc_after_materialization = {summary.get('best_true_rc_after_materialization')}",
        f"pricing_kind_counts = {summary.get('pricing_kind_counts')}",
        f"reason_counts = {summary.get('reason_counts')}",
        f"repeated_weak_mask_count = {summary.get('repeated_weak_mask_count')}",
        f"repeated_weak_task_set_sample_count = {summary.get('repeated_weak_task_set_sample_count')}",
        "production_ready = false",
        "certificate_effect = false",
        "official_bound_effect = false",
        "```",
        "",
        "## 解释",
        "",
        "这些 row 表示当前 profile/rough objective 的负列信号在 true-RC materialization 后失效。它们可以作为 GAT branch-impact / proof-tail 模型的负样本，或作为未来 worker priority / finite-delay 的训练依据；但不能作为 pruning、no-negative certificate 或 official lower bound。",
        "",
        "## Top Weak Masks",
        "",
        "```json",
        json.dumps(summary.get("weak_mask_counts", {}), ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Top Weak Task-Set Samples",
        "",
        "```json",
        json.dumps(summary.get("weak_task_set_sample_counts", {}), ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = summarize(args.paths)
    write_outputs(summary, args.output_dir, args.report)
    printable = dict(summary)
    printable.pop("rows", None)
    print(json.dumps(printable, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
