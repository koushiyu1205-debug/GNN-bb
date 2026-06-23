#!/usr/bin/env python3
"""Audit why Journey tail-impact rows lack useful tail-reduction positives."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_tail_positive_gap_audit_20260623")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260623_bpc_future_journey_tail_positive_gap_audit_zh.md"
)


def _iter_rows(paths: Iterable[Path]) -> Iterable[dict[str, Any]]:
    for path in paths:
        if path.is_dir():
            yield from _iter_jsonl(path / "tail_impact_training_rows.jsonl")
        elif path.name == "summary.json":
            yield from _iter_jsonl(path.parent / "tail_impact_training_rows.jsonl")
        elif path.suffix == ".jsonl":
            yield from _iter_jsonl(path)


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def _float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return float(default)
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    if result != result:
        return float(default)
    return float(result)


def _labels(row: dict[str, Any]) -> dict[str, float]:
    labels = row.get("labels")
    if not isinstance(labels, dict):
        return {}
    return {str(key): _float(value) for key, value in labels.items()}


def _tail_badness(row: dict[str, Any]) -> float:
    labels = _labels(row)
    return (
        100.0 * labels.get("y_completion_bound_tail", 0.0)
        + 50.0 * labels.get("y_early_branch_continues", 0.0)
        + 30.0 * labels.get("y_negative_chain_continues", 0.0)
        + 10.0 * labels.get("y_inactive_only", 0.0)
        + labels.get("y_child_negative_pricing_events", 0.0)
        + 5.0 * labels.get("y_child_completion_bound_retries", 0.0)
        + 3.0 * labels.get("y_child_early_branch_triggers", 0.0)
    )


def _compact_row(row: dict[str, Any]) -> dict[str, Any]:
    labels = _labels(row)
    return {
        "source_type": row.get("source_type"),
        "log_file": row.get("log_file"),
        "node_id": row.get("node_id"),
        "depth": row.get("depth"),
        "task_i": row.get("task_i"),
        "task_j": row.get("task_j"),
        "tail_class": row.get("tail_class"),
        "tail_badness_score": round(_tail_badness(row), 6),
        "y_active_touch": labels.get("y_active_touch", 0.0),
        "y_inactive_only": labels.get("y_inactive_only", 0.0),
        "y_completion_bound_tail": labels.get("y_completion_bound_tail", 0.0),
        "y_early_branch_continues": labels.get("y_early_branch_continues", 0.0),
        "y_negative_chain_continues": labels.get("y_negative_chain_continues", 0.0),
        "y_child_negative_pricing_events": labels.get("y_child_negative_pricing_events", 0.0),
        "y_child_completion_bound_retries": labels.get("y_child_completion_bound_retries", 0.0),
        "y_child_early_branch_triggers": labels.get("y_child_early_branch_triggers", 0.0),
    }


def audit_positive_gap(
    paths: list[Path],
    output_dir: Path,
    report: Path,
    *,
    top_n: int = 12,
) -> dict[str, Any]:
    rows = list(_iter_rows(paths))
    labels_by_row = [_labels(row) for row in rows]
    source_counts = Counter(str(row.get("source_type") or "") for row in rows)
    tail_class_counts = Counter(str(row.get("tail_class") or "") for row in rows)
    useful_rows = [
        row for row, labels in zip(rows, labels_by_row, strict=False)
        if labels.get("y_useful_tail_reduction", 0.0) > 0.5
    ]
    active_touch_rows = [
        row for row, labels in zip(rows, labels_by_row, strict=False)
        if labels.get("y_active_touch", 0.0) > 0.5
    ]
    active_touch_tail_risk_rows = [
        row for row, labels in zip(rows, labels_by_row, strict=False)
        if labels.get("y_active_touch", 0.0) > 0.5
        and labels.get("y_tail_risk", 0.0) > 0.5
    ]
    near_positive_rows = sorted(
        active_touch_tail_risk_rows,
        key=lambda row: (
            _tail_badness(row),
            str(row.get("log_file") or ""),
            int(row.get("node_id") or 0),
        ),
    )[:top_n]
    summary = {
        "schema_version": "journey_tail_positive_gap_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "stage4_candidate_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "input_paths": [str(path) for path in paths],
        "row_count": len(rows),
        "source_counts": dict(sorted(source_counts.items())),
        "tail_class_counts": dict(sorted(tail_class_counts.items())),
        "useful_tail_reduction_positive_count": len(useful_rows),
        "tail_risk_count": int(
            sum(1 for labels in labels_by_row if labels.get("y_tail_risk", 0.0) > 0.5)
        ),
        "active_touch_count": len(active_touch_rows),
        "active_touch_still_tail_risk_count": len(active_touch_tail_risk_rows),
        "active_touch_completion_bound_tail_count": int(
            sum(
                1
                for row in active_touch_tail_risk_rows
                if _labels(row).get("y_completion_bound_tail", 0.0) > 0.5
            )
        ),
        "active_touch_early_branch_count": int(
            sum(
                1
                for row in active_touch_tail_risk_rows
                if _labels(row).get("y_early_branch_continues", 0.0) > 0.5
            )
        ),
        "active_touch_negative_chain_count": int(
            sum(
                1
                for row in active_touch_tail_risk_rows
                if _labels(row).get("y_negative_chain_continues", 0.0) > 0.5
            )
        ),
        "weak_negative_filtered_count": int(
            sum(1 for labels in labels_by_row if labels.get("y_weak_negative_filtered", 0.0) > 0.5)
        ),
        "contrastive_tail_training_ready": bool(useful_rows and active_touch_tail_risk_rows),
        "hard_negative_catalog_ready": bool(rows),
        "positive_gap_reason": (
            "no_useful_tail_reduction_positive"
            if not useful_rows
            else "positive_rows_present"
        ),
        "near_positive_rows": [_compact_row(row) for row in near_positive_rows],
        "interpretation": (
            "Current rows contain tail-risk and active-touch failures but no useful "
            "tail-reduction positive.  They can guide hard-negative suppression, "
            "not train a contrastive acceleration policy."
        ),
    }
    write_outputs(summary, output_dir, report)
    return summary


def write_outputs(summary: dict[str, Any], output_dir: Path, report: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "near_positive_rows.jsonl").write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in summary.get("near_positive_rows", [])
        ),
        encoding="utf-8",
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_render_report(summary, output_dir), encoding="utf-8")


def _render_report(summary: dict[str, Any], output_dir: Path) -> str:
    return "\n".join(
        [
            "# Journey Tail Positive Gap Audit",
            "",
            "日期：2026-06-23",
            "",
            "## 目的",
            "",
            "读取 tail-impact training rows，审计是否已经具备可训练的 tail-reduction 正例。该脚本只读离线 artifact，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
            "",
            "## 机器字段",
            "",
            "```text",
            "journey_tail_positive_gap_audit = current",
            f"output_dir = {output_dir}",
            f"row_count = {summary.get('row_count')}",
            f"source_counts = {summary.get('source_counts')}",
            f"tail_class_counts = {summary.get('tail_class_counts')}",
            f"useful_tail_reduction_positive_count = {summary.get('useful_tail_reduction_positive_count')}",
            f"tail_risk_count = {summary.get('tail_risk_count')}",
            f"active_touch_count = {summary.get('active_touch_count')}",
            f"active_touch_still_tail_risk_count = {summary.get('active_touch_still_tail_risk_count')}",
            f"active_touch_completion_bound_tail_count = {summary.get('active_touch_completion_bound_tail_count')}",
            f"active_touch_early_branch_count = {summary.get('active_touch_early_branch_count')}",
            f"active_touch_negative_chain_count = {summary.get('active_touch_negative_chain_count')}",
            f"weak_negative_filtered_count = {summary.get('weak_negative_filtered_count')}",
            f"positive_gap_reason = {summary.get('positive_gap_reason')}",
            f"contrastive_tail_training_ready = {str(summary.get('contrastive_tail_training_ready')).lower()}",
            "production_ready = false",
            "stage4_candidate_ready = false",
            "certificate_effect = false",
            "official_bound_effect = false",
            "```",
            "",
            "## 解释",
            "",
            "当前数据可以支持 hard-negative suppression：weak-negative filtered、inactive-only、completion-bound tail、early-branch tail 都有证据。但 `useful_tail_reduction_positive_count=0` 时，它不能支持 GAT 学习“哪个候选会加速证明”。",
            "",
            "## Near Positive Rows",
            "",
            "```json",
            json.dumps(summary.get("near_positive_rows", []), ensure_ascii=False, indent=2, sort_keys=True),
            "```",
        ]
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--top-n", type=int, default=12)
    args = parser.parse_args()

    summary = audit_positive_gap(args.paths, args.output_dir, args.report, top_n=args.top_n)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
