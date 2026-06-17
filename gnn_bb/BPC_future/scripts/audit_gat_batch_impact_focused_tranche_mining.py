#!/usr/bin/env python3
"""Mine label-defined same-context focused regression tranches.

This diagnostic reads a batch-impact dataset manifest and finds same-context
positive-vs-hard-negative rows that can be used as a fixed focused training or
checkpoint-gate tranche. It does not load a model and does not run BPC,
pricing, RMP, workers, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from statistics import mean
from typing import Any


DEFAULT_DATASET_DIR = Path("BPC_future/data/gat_batch_impact/v75_v66_path_tokens_slack_20260617")
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_batch_impact_focused_tranche_mining_v95_v75_20260617"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260617_bpc_future_gat_target_mode_stage3_v95_focused_tranche_mining_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--min-positive-roi",
        type=float,
        default=0.65,
        help="Minimum accepted_batch_roi for a row to be a focused positive.",
    )
    parser.add_argument(
        "--max-hard-negative-roi",
        type=float,
        default=0.0,
        help="Maximum accepted_batch_roi that always qualifies a delay row as hard-negative.",
    )
    parser.add_argument(
        "--min-roi-gap",
        type=float,
        default=1.0e-6,
        help="Minimum ROI gap required between positive and negative rows.",
    )
    parser.add_argument("--top-contexts", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = mine_focused_tranche(
        dataset_dir=Path(args.dataset_dir),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        min_positive_roi=float(args.min_positive_roi),
        max_hard_negative_roi=float(args.max_hard_negative_roi),
        min_roi_gap=float(args.min_roi_gap),
        top_contexts=max(1, int(args.top_contexts)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def mine_focused_tranche(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    min_positive_roi: float = 0.65,
    max_hard_negative_roi: float = 0.0,
    min_roi_gap: float = 1.0e-6,
    top_contexts: int = 20,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    manifest = _read_json(dataset_dir / "manifest.json")
    _assert_offline_manifest(manifest)
    rows = [
        _manifest_row(
            item,
            min_positive_roi=min_positive_roi,
            max_hard_negative_roi=max_hard_negative_roi,
        )
        for item in manifest.get("samples", [])
    ]
    context_rows, pair_rows = _context_and_pair_rows(rows, min_roi_gap=min_roi_gap)
    focused_row_indices = sorted(
        {
            int(pair["positive_row_index"])
            for pair in pair_rows
        }
        | {
            int(pair["negative_row_index"])
            for pair in pair_rows
        }
    )
    focused_rows = [
        row for row in rows if int(row["row_index"]) in set(focused_row_indices)
    ]
    summary = _summary(
        manifest,
        rows,
        focused_rows,
        context_rows,
        pair_rows,
        min_positive_roi=min_positive_roi,
        max_hard_negative_roi=max_hard_negative_roi,
        min_roi_gap=min_roi_gap,
        top_contexts=top_contexts,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    focused_rows_path = output_dir / "focused_rows.jsonl"
    context_rows_path = output_dir / "focused_contexts.jsonl"
    pair_rows_path = output_dir / "focused_pairs.jsonl"
    focused_row_indices_path = output_dir / "focused_row_indices.json"
    _write_jsonl(focused_rows_path, focused_rows)
    _write_jsonl(context_rows_path, context_rows)
    _write_jsonl(pair_rows_path, pair_rows)
    focused_row_indices_path.write_text(
        json.dumps(focused_row_indices, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    summary.update(
        {
            "dataset_dir": str(dataset_dir),
            "output_dir": str(output_dir),
            "focused_rows_path": str(focused_rows_path),
            "focused_contexts_path": str(context_rows_path),
            "focused_pairs_path": str(pair_rows_path),
            "focused_row_indices_path": str(focused_row_indices_path),
        }
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(Path(report), summary)
    return summary


def _manifest_row(
    item: dict[str, Any],
    *,
    min_positive_roi: float,
    max_hard_negative_roi: float,
) -> dict[str, Any]:
    accepted_roi = _float_or_default(item.get("accepted_batch_roi"), 0.0)
    high_priority_count = int(item.get("high_priority_candidate_count") or 0)
    delay_count = int(item.get("delay_candidate_count") or 0)
    label_positive = int(item.get("label_batch_roi_positive") or 0) > 0
    positive = (
        label_positive
        and accepted_roi >= float(min_positive_roi)
        and high_priority_count > 0
    )
    hard_negative = (
        delay_count > 0
        and (
            not label_positive
            or accepted_roi <= float(max_hard_negative_roi)
        )
    )
    if positive:
        label_class = "focused_positive"
    elif hard_negative:
        label_class = "focused_hard_negative"
    elif label_positive:
        label_class = "positive_below_focused_roi"
    elif delay_count > 0:
        label_class = "delay_nonfocused_negative"
    else:
        label_class = "ambiguous"
    return {
        "row_index": int(item.get("row_index") or 0),
        "path": str(item.get("path") or ""),
        "source_file": str(item.get("source_file") or ""),
        "context_key": _context_key(item),
        "context_hash": str(item.get("context_hash") or ""),
        "instance": str(item.get("instance") or ""),
        "family": str(item.get("instance_family") or "unknown"),
        "region": str(item.get("instance_region") or "unknown"),
        "task_count": int(item.get("task_count") or 0),
        "candidate_count": int(item.get("candidate_count") or 0),
        "candidate_signature_ids": list(item.get("candidate_signature_ids") or []),
        "accepted_batch_roi": accepted_roi,
        "objective_improvement": _float_or_default(item.get("objective_improvement"), 0.0),
        "label_batch_roi_positive": int(label_positive),
        "high_priority_candidate_count": high_priority_count,
        "delay_candidate_count": delay_count,
        "negative_candidate_count": int(item.get("negative_candidate_count") or 0),
        "label_class": label_class,
        "diagnostic_only": True,
    }


def _context_and_pair_rows(
    rows: list[dict[str, Any]],
    *,
    min_roi_gap: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_context: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_context[str(row["context_key"])].append(row)
    context_rows: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    for context_key, group in sorted(by_context.items()):
        positives = [row for row in group if row["label_class"] == "focused_positive"]
        negatives = [row for row in group if row["label_class"] == "focused_hard_negative"]
        pairs = [
            _pair_row(positive, negative)
            for positive in positives
            for negative in negatives
            if float(positive["accepted_batch_roi"]) - float(negative["accepted_batch_roi"])
            >= float(min_roi_gap)
        ]
        pair_rows.extend(pairs)
        context_rows.append(_context_row(context_key, group, positives, negatives, pairs))
    return context_rows, pair_rows


def _pair_row(positive: dict[str, Any], negative: dict[str, Any]) -> dict[str, Any]:
    return {
        "context_key": str(positive["context_key"]),
        "context_hash": str(positive["context_hash"]),
        "family": str(positive["family"]),
        "region": str(positive["region"]),
        "task_count": int(positive["task_count"]),
        "positive_row_index": int(positive["row_index"]),
        "negative_row_index": int(negative["row_index"]),
        "positive_roi": float(positive["accepted_batch_roi"]),
        "negative_roi": float(negative["accepted_batch_roi"]),
        "roi_gap": float(positive["accepted_batch_roi"]) - float(negative["accepted_batch_roi"]),
        "positive_high_priority_candidate_count": int(positive["high_priority_candidate_count"]),
        "negative_delay_candidate_count": int(negative["delay_candidate_count"]),
        "positive_signature_ids": list(positive.get("candidate_signature_ids") or []),
        "negative_signature_ids": list(negative.get("candidate_signature_ids") or []),
        "diagnostic_only": True,
    }


def _context_row(
    context_key: str,
    group: list[dict[str, Any]],
    positives: list[dict[str, Any]],
    negatives: list[dict[str, Any]],
    pairs: list[dict[str, Any]],
) -> dict[str, Any]:
    first = group[0]
    labels = Counter(str(row["label_class"]) for row in group)
    return {
        "context_key": context_key,
        "context_hash": str(first["context_hash"]),
        "family": str(first["family"]),
        "region": str(first["region"]),
        "task_count": int(first["task_count"]),
        "row_count": len(group),
        "positive_count": len(positives),
        "hard_negative_count": len(negatives),
        "pair_count": len(pairs),
        "max_positive_roi": max([float(row["accepted_batch_roi"]) for row in positives], default=None),
        "min_negative_roi": min([float(row["accepted_batch_roi"]) for row in negatives], default=None),
        "row_indices": [int(row["row_index"]) for row in sorted(group, key=lambda row: int(row["row_index"]))],
        "label_counts": dict(sorted(labels.items())),
        "diagnostic_only": True,
    }


def _summary(
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
    focused_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    *,
    min_positive_roi: float,
    max_hard_negative_roi: float,
    min_roi_gap: float,
    top_contexts: int,
) -> dict[str, Any]:
    label_counts = Counter(str(row["label_class"]) for row in rows)
    focused_label_counts = Counter(str(row["label_class"]) for row in focused_rows)
    family_counts = _counter_by(rows, "family")
    focused_family_counts = _counter_by(focused_rows, "family")
    task_counts = Counter(str(int(row["task_count"])) for row in rows)
    focused_task_counts = Counter(str(int(row["task_count"])) for row in focused_rows)
    trainable_contexts = [row for row in context_rows if int(row["pair_count"]) > 0]
    negative_only_contexts = [
        row
        for row in context_rows
        if int(row["hard_negative_count"]) > 0 and int(row["positive_count"]) <= 0
    ]
    positive_only_contexts = [
        row
        for row in context_rows
        if int(row["positive_count"]) > 0 and int(row["hard_negative_count"]) <= 0
    ]
    focused_indices = sorted(int(row["row_index"]) for row in focused_rows)
    row_index_min = min(focused_indices) if focused_indices else None
    if row_index_min is None:
        row_index_min_selected_count = 0
    else:
        row_index_min_selected_count = sum(1 for row in rows if int(row["row_index"]) >= row_index_min)
    roi_gaps = [float(row["roi_gap"]) for row in pair_rows]
    return {
        "schema_version": "gat_batch_impact_focused_tranche_mining_v1",
        "status": "gat_batch_impact_focused_tranche_mined",
        "dataset_dir": "",
        "sample_count": int(manifest.get("sample_count") or len(rows)),
        "candidate_count": int(manifest.get("candidate_count") or 0),
        "min_positive_roi": float(min_positive_roi),
        "max_hard_negative_roi": float(max_hard_negative_roi),
        "min_roi_gap": float(min_roi_gap),
        "context_count": len(context_rows),
        "trainable_context_count": len(trainable_contexts),
        "focused_pair_count": len(pair_rows),
        "focused_row_count": len(focused_rows),
        "focused_positive_row_count": int(focused_label_counts.get("focused_positive", 0)),
        "focused_hard_negative_row_count": int(focused_label_counts.get("focused_hard_negative", 0)),
        "negative_only_context_count": len(negative_only_contexts),
        "positive_only_context_count": len(positive_only_contexts),
        "label_counts": dict(sorted(label_counts.items())),
        "focused_label_counts": dict(sorted(focused_label_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "focused_family_counts": dict(sorted(focused_family_counts.items())),
        "task_count_counts": dict(sorted(task_counts.items(), key=lambda item: int(item[0]))),
        "focused_task_count_counts": dict(sorted(focused_task_counts.items(), key=lambda item: int(item[0]))),
        "roi_gap_min": min(roi_gaps) if roi_gaps else None,
        "roi_gap_mean": mean(roi_gaps) if roi_gaps else None,
        "roi_gap_max": max(roi_gaps) if roi_gaps else None,
        "focused_row_indices": focused_indices,
        "row_index_min_selector": {
            "row_index_min": row_index_min,
            "selected_count": row_index_min_selected_count,
            "focused_count": len(focused_rows),
            "extra_nonfocused_count": max(0, row_index_min_selected_count - len(focused_rows)),
            "extra_nonfocused_rate": (
                max(0, row_index_min_selected_count - len(focused_rows))
                / float(row_index_min_selected_count)
                if row_index_min_selected_count
                else 0.0
            ),
        },
        "recommended_selector": (
            "explicit_row_indices"
            if row_index_min_selected_count > len(focused_rows)
            else "row_index_min"
        ),
        "top_trainable_contexts": sorted(
            trainable_contexts,
            key=lambda row: (int(row["pair_count"]), int(row["row_count"])),
            reverse=True,
        )[: int(top_contexts)],
        "top_negative_only_contexts": sorted(
            negative_only_contexts,
            key=lambda row: (int(row["hard_negative_count"]), int(row["row_count"])),
            reverse=True,
        )[: int(top_contexts)],
        "stage3_focused_tranche_ready": bool(pair_rows),
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "all_checks_pass": True,
    }


def _counter_by(rows: list[dict[str, Any]], key: str) -> Counter[str]:
    return Counter(str(row.get(key) or "unknown") for row in rows)


def _context_key(item: dict[str, Any]) -> str:
    return f"{item.get('instance') or ''}|{item.get('context_hash') or ''}"


def _assert_offline_manifest(manifest: dict[str, Any]) -> None:
    if not bool(manifest.get("diagnostic_only", True)):
        raise ValueError("batch-impact manifest must be diagnostic-only")
    if bool(manifest.get("runs_bpc_or_pricing", False)):
        raise ValueError("focused tranche mining requires offline dataset manifest")
    if bool(manifest.get("production_ready", False)):
        raise ValueError("focused tranche mining must not consume production-ready claims")
    if bool(manifest.get("certificate_source", False)):
        raise ValueError("batch-impact dataset must not be a certificate source")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )


def _float_or_default(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def write_report(report: Path, summary: dict[str, Any]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "\n".join(
            [
                "# 2026-06-17 BPC_future GAT Stage 3 v95 Focused Tranche Mining 报告",
                "",
                "## 目的",
                "",
                "从 batch-impact dataset manifest 中挖掘同一 context 的 high-ROI positive "
                "vs delay / hard-negative focused regression tranche。该审计不加载模型，"
                "不运行 BPC / pricing / RMP / worker / certificate。",
                "",
                "## 机器字段",
                "",
                "```text",
                "gat_batch_impact_focused_tranche_mining = current",
                f"status = {summary['status']}",
                f"sample_count = {summary['sample_count']}",
                f"context_count = {summary['context_count']}",
                f"trainable_context_count = {summary['trainable_context_count']}",
                f"focused_row_count = {summary['focused_row_count']}",
                f"focused_pair_count = {summary['focused_pair_count']}",
                f"focused_family_counts = {summary['focused_family_counts']}",
                f"focused_task_count_counts = {summary['focused_task_count_counts']}",
                f"recommended_selector = {summary['recommended_selector']}",
                f"row_index_min_selector = {summary['row_index_min_selector']}",
                f"stage3_focused_tranche_ready = {str(summary['stage3_focused_tranche_ready']).lower()}",
                "production_ready = false",
                "selector_can_certificate = false",
                "all_checks_pass = true",
                "```",
                "",
                "## 关键结论",
                "",
                f"- 可训练同 context positive/negative context 数：`{summary['trainable_context_count']}`。",
                f"- 可形成 focused pair：`{summary['focused_pair_count']}`。",
                f"- focused rows 覆盖 family：`{summary['focused_family_counts']}`。",
                f"- negative-only contexts：`{summary['negative_only_context_count']}`，"
                "这些只能提供 delay / hard-negative 监督，不能单独训练 positive > negative ranking。",
                f"- 当前 `row_index_min` selector 会额外带入 "
                f"`{summary['row_index_min_selector']['extra_nonfocused_count']}` 个非 focused row；"
                "后续 trainer 应支持 explicit row-index selector。",
                "",
                "## Output Artifacts",
                "",
                "```text",
                f"summary = {summary['output_dir']}/summary.json",
                f"focused_rows = {summary['focused_rows_path']}",
                f"focused_pairs = {summary['focused_pairs_path']}",
                f"focused_row_indices = {summary['focused_row_indices_path']}",
                "```",
                "",
                "## Exactness Boundary",
                "",
                "- `diagnostic_only=true`；",
                "- `runs_bpc_or_pricing=false`；",
                "- `production_ready=false`；",
                "- `selector_is_pricing_oracle=false`；",
                "- `selector_can_certificate=false`；",
                "- `gate_can_permanently_discard_negative_columns=false`；",
                "- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。",
                "",
            ]
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
