#!/usr/bin/env python3
"""Expand weak context competitors for Journey tree-policy event rows.

This is an offline data transformation. It does not run BPC, pricing, RMP, or
certificates. Generated competitor rows are low-weight ranking negatives: they
mean "not selected by the recovered successful policy in this context", not a
standalone full-replay failure certificate.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/data/gat_branch_action_sanity/v514_tree_policy_top200_context_competitors_20260627"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/20260627_bpc_future_v514_tree_policy_top200_context_competitors_zh.md"
)


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if path.is_dir():
        path = path / "tree_policy_event_rows.jsonl"
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


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _pair(value: Any) -> tuple[int, int] | None:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        left = _int(value[0], -1)
        right = _int(value[1], -1)
        if left > 0 and right > 0 and left != right:
            return tuple(sorted((left, right)))
    return None


def _candidate_pair(candidate: dict[str, Any]) -> tuple[int, int] | None:
    return _pair([candidate.get("task_i"), candidate.get("task_j")])


def _context_key(row: dict[str, Any], pair: tuple[int, int] | None) -> tuple[Any, ...]:
    return (
        row.get("instance"),
        row.get("node_id"),
        row.get("depth"),
        json.dumps(row.get("baseline_pair"), sort_keys=True),
        pair,
    )


def _candidate_rows(row: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    merged: dict[tuple[int, int], dict[str, Any]] = {}
    for key in ("top", "priority_top"):
        candidates = row.get(key)
        if not isinstance(candidates, list):
            continue
        for candidate in candidates[: max(0, int(limit)) or None]:
            if not isinstance(candidate, dict):
                continue
            pair = _candidate_pair(candidate)
            if pair is None:
                continue
            if pair not in merged:
                merged[pair] = dict(candidate)
            else:
                merged[pair].update({name: value for name, value in candidate.items() if value is not None})
    return list(merged.values())


def expand_context_competitors(
    input_path: Path,
    output_dir: Path,
    report: Path,
    *,
    max_competitors_per_positive: int = 200,
    competitor_weight: float = 0.05,
    drop_existing_context_competitors: bool = True,
) -> dict[str, Any]:
    rows = list(_iter_jsonl(input_path))
    output_rows: list[dict[str, Any]] = []
    existing_keys: set[tuple[Any, ...]] = set()
    skipped: Counter[str] = Counter()

    for row in rows:
        label_type = str(row.get("tree_policy_label_type") or "")
        if drop_existing_context_competitors and label_type == "context_competitor_negative":
            skipped["dropped_existing_context_competitor"] += 1
            continue
        pair = _pair(row.get("selected_pair"))
        output_rows.append(row)
        existing_keys.add(_context_key(row, pair))

    added = 0
    for row in rows:
        if float(row.get("y_tree_policy_positive") or 0.0) <= 0.5:
            continue
        selected = _pair(row.get("selected_pair"))
        if selected is None:
            skipped["positive_without_selected_pair"] += 1
            continue
        count_for_row = 0
        for candidate in _candidate_rows(row, int(max_competitors_per_positive)):
            pair = _candidate_pair(candidate)
            if pair is None:
                skipped["invalid_candidate_pair"] += 1
                continue
            if pair == selected:
                continue
            key = _context_key(row, pair)
            if key in existing_keys:
                skipped["duplicate_context_pair"] += 1
                continue
            competitor = dict(row)
            competitor["selected_pair"] = list(pair)
            competitor["alternative_pair"] = list(pair)
            competitor["selected_raw"] = dict(candidate)
            competitor["selected_score"] = candidate.get("branch_score")
            competitor["selected_score_source"] = candidate.get("branch_score_source")
            competitor["branch_tree_policy_label"] = False
            competitor["single_pair_label"] = False
            competitor["y_tree_policy_positive"] = 0.0
            competitor["y_tree_policy_hard_negative"] = 1.0
            competitor["tree_policy_label_type"] = "context_competitor_negative"
            competitor["tree_policy_label_reason"] = "same_context_top_candidate_not_selected_by_successful_policy"
            competitor["event_loss_weight"] = float(competitor_weight)
            competitor["policy_run"] = f"{row.get('policy_run') or 'tree_policy'}_top200_context_competitor"
            competitor["candidate_counterfactual_observed"] = False
            competitor["source_positive_selected_pair"] = list(selected)
            competitor["source_positive_capped_wall_time_gain"] = row.get("capped_wall_time_gain")
            output_rows.append(competitor)
            existing_keys.add(key)
            added += 1
            count_for_row += 1
        if count_for_row <= 0:
            skipped["positive_without_added_competitor"] += 1

    label_counts: Counter[str] = Counter(str(row.get("tree_policy_label_type") or "") for row in output_rows)
    summary = {
        "schema_version": "gat_tree_policy_context_competitor_expansion_v1",
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "output_path": str(output_dir / "tree_policy_event_rows.jsonl"),
        "input_row_count": len(rows),
        "output_row_count": len(output_rows),
        "added_context_competitor_count": int(added),
        "max_competitors_per_positive": int(max_competitors_per_positive),
        "competitor_weight": float(competitor_weight),
        "drop_existing_context_competitors": bool(drop_existing_context_competitors),
        "label_type_counts": dict(label_counts),
        "skipped_counts": dict(skipped),
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "production_ready": False,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "tree_policy_event_rows.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in output_rows) + "\n",
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(report: Path, summary: dict[str, Any]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Tree-Policy Top200 Context Competitors",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 机器字段",
        "",
        "```text",
        f"input_row_count = {summary['input_row_count']}",
        f"output_row_count = {summary['output_row_count']}",
        f"added_context_competitor_count = {summary['added_context_competitor_count']}",
        f"max_competitors_per_positive = {summary['max_competitors_per_positive']}",
        f"competitor_weight = {summary['competitor_weight']}",
        f"label_type_counts = {summary['label_type_counts']}",
        f"skipped_counts = {summary['skipped_counts']}",
        "runs_bpc_or_pricing = false",
        "official_bound_effect = false",
        "certificate_effect = false",
        "production_ready = false",
        "```",
        "",
        "## 边界",
        "",
        "新增 competitor rows 是低权重排序负例，不是完整反事实求解失败证书；只能用于 tree-policy 排序训练。",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-competitors-per-positive", type=int, default=200)
    parser.add_argument("--competitor-weight", type=float, default=0.05)
    parser.add_argument("--keep-existing-context-competitors", action="store_true")
    args = parser.parse_args()

    summary = expand_context_competitors(
        args.input,
        args.output_dir,
        args.report,
        max_competitors_per_positive=int(args.max_competitors_per_positive),
        competitor_weight=float(args.competitor_weight),
        drop_existing_context_competitors=not bool(args.keep_existing_context_competitors),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
