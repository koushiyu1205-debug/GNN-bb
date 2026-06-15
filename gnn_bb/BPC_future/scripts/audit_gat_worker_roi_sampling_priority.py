#!/usr/bin/env python3
"""Build a GAT worker ROI sampling priority matrix.

This offline audit reads existing target-priority worker ROI labels and,
optionally, one or more unsampled candidate files.  It never runs BPC,
pricing, RMP, workers, or certificates.  Its purpose is to keep the GAT ROI
dataset balanced by scale/family/terrain instead of repeatedly sampling
near-duplicate hard negatives.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
from typing import Any, Iterable


DEFAULT_ROI_JSONL = Path(
    "BPC_future/results/"
    "gat_same_run_combined_plus_seed_cross_family_v12_worker_roi_dataset_20260615/"
    "gat_worker_roi_rows.jsonl"
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_worker_roi_sampling_priority_20260615")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260615_bpc_future_gat_worker_roi_sampling_priority_zh.md"
)

POSITIVE_ROI = {
    "positive_primal_roi",
    "positive_status_roi",
    "positive_retry_roi",
    "positive_pricing_roi",
}
TRAINING_NEGATIVE_ROI = {
    "negative_primal_roi",
    "negative_status_roi",
    "negative_retry_roi",
    "no_observed_roi",
}
UNSUPPORTED_ROI = {"columns_only_roi"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roi-jsonl", type=Path, default=DEFAULT_ROI_JSONL)
    parser.add_argument("--candidate-file", type=Path, action="append", default=[])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-positive-per-cell", type=int, default=2)
    parser.add_argument("--min-negative-per-cell", type=int, default=2)
    parser.add_argument("--max-recommendations", type=int, default=12)
    parser.add_argument(
        "--max-per-cell",
        type=int,
        default=2,
        help=(
            "Maximum recommendations from the same family/region cell. Use 0 "
            "for unlimited. This prevents one low-positive-rate cell from "
            "monopolizing the next ROI-label batch."
        ),
    )
    parser.add_argument(
        "--candidate-task-count",
        type=int,
        action="append",
        default=[],
        help=(
            "Optional task-count filter for unsampled candidates. Repeat to allow multiple "
            "scales; omitted means all candidate scales."
        ),
    )
    args = parser.parse_args()
    return args


def main() -> int:
    args = parse_args()
    summary = build_sampling_priority(
        roi_jsonl=args.roi_jsonl,
        candidate_files=tuple(args.candidate_file or ()),
        output_dir=args.output_dir,
        report=args.report,
        min_positive_per_cell=int(args.min_positive_per_cell),
        min_negative_per_cell=int(args.min_negative_per_cell),
        max_recommendations=int(args.max_recommendations),
        max_per_cell=int(args.max_per_cell),
        candidate_task_counts=tuple(int(value) for value in args.candidate_task_count or ()),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def build_sampling_priority(
    *,
    roi_jsonl: Path = DEFAULT_ROI_JSONL,
    candidate_files: Iterable[Path] = tuple(),
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    min_positive_per_cell: int = 2,
    min_negative_per_cell: int = 2,
    max_recommendations: int = 12,
    max_per_cell: int = 2,
    candidate_task_counts: tuple[int, ...] = tuple(),
) -> dict[str, Any]:
    candidate_files = tuple(Path(path) for path in candidate_files)
    rows = [_enrich_record(row) for row in _read_jsonl(Path(roi_jsonl))]
    existing_targets = _existing_targets(rows)
    family_region = _cell_stats(rows, keys=("instance_family", "instance_region"))
    family_region_ordinal = _cell_stats(
        rows, keys=("instance_family", "instance_region", "instance_ordinal")
    )
    candidates = _load_candidates(candidate_files, existing_targets)
    if candidate_task_counts:
        allowed_task_counts = {int(value) for value in candidate_task_counts}
        candidates = [
            candidate
            for candidate in candidates
            if int(candidate.get("instance_task_count") or -1) in allowed_task_counts
        ]
    recommendations = _recommend_candidates(
        candidates=candidates,
        cell_stats=family_region,
        ordinal_stats=family_region_ordinal,
        max_recommendations=int(max_recommendations),
        min_positive_per_cell=int(min_positive_per_cell),
        min_negative_per_cell=int(min_negative_per_cell),
        max_per_cell=int(max_per_cell),
    )
    checks = {
        "diagnostic_only": True,
        "has_rows": bool(rows),
        "no_certificate_effect": True,
        "runs_bpc_or_pricing_false": True,
        "recommendations_have_no_existing_roi_target": all(
            not bool(item.get("existing_roi_target")) for item in recommendations
        ),
    }
    summary = {
        "schema_version": "gat_worker_roi_sampling_priority_v1",
        "status": "built",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_ready": False,
        "production_ready": False,
        "roi_jsonl": str(roi_jsonl),
        "row_count": len(rows),
        "candidate_file_count": len(candidate_files),
        "candidate_task_counts": [int(value) for value in candidate_task_counts],
        "candidate_count": len(candidates),
        "recommendation_count": len(recommendations),
        "min_positive_per_cell": int(min_positive_per_cell),
        "min_negative_per_cell": int(min_negative_per_cell),
        "max_per_cell": int(max_per_cell),
        "roi_class_counts": dict(sorted(Counter(row["roi_class"] for row in rows).items())),
        "family_region_cells": family_region,
        "family_region_ordinal_cells": family_region_ordinal,
        "sample_gaps": _sample_gaps(
            family_region,
            min_positive_per_cell=int(min_positive_per_cell),
            min_negative_per_cell=int(min_negative_per_cell),
        ),
        "recommendations": recommendations,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "checks": checks,
    }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "recommendations.json").write_text(
        json.dumps({"recommendations": recommendations}, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "recommended_candidates.json").write_text(
        json.dumps({"candidates": recommendations}, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _enrich_record(record: dict[str, Any]) -> dict[str, Any]:
    item = dict(record)
    item.update(_instance_metadata(str(item.get("instance") or item.get("name") or "")))
    if item.get("instance_family") in {None, "", "unknown"}:
        item["instance_family"] = _family_from_name(str(item.get("name") or "unknown"))
    if item.get("instance_region") in {None, "", "unknown"}:
        item["instance_region"] = _region_from_name(str(item.get("name") or "unknown"))
    if item.get("instance_ordinal") is None:
        item["instance_ordinal"] = _ordinal_from_text(
            str(item.get("instance") or "") + " " + str(item.get("name") or "")
        )
    return item


def _instance_metadata(text: str) -> dict[str, Any]:
    path = Path(str(text))
    task_count: int | None = None
    family = "unknown"
    region = "unknown"
    for idx, part in enumerate(path.parts):
        match = re.fullmatch(r"tasks_(\d+)", part)
        if match:
            task_count = int(match.group(1))
            if idx + 1 < len(path.parts):
                family = str(path.parts[idx + 1])
            if idx + 2 < len(path.parts):
                region = str(path.parts[idx + 2])
            break
    return {
        "instance_task_count": task_count,
        "instance_family": family,
        "instance_region": region,
        "instance_ordinal": _ordinal_from_text(str(text)),
    }


def _ordinal_from_text(text: str) -> int | None:
    match = re.search(r"_tasks\d{3}_(\d+)_seed", str(text))
    if match:
        return int(match.group(1))
    match = re.search(r"tasks020_(\d+)_", str(text))
    if match:
        return int(match.group(1))
    return None


def _family_from_name(name: str) -> str:
    if "greedy_anchor" in name or "greedy-anchor" in name:
        return "greedy-anchor"
    if "random_wave" in name or "random-wave" in name:
        return "random-wave"
    if "sector_wave" in name or "sector-wave" in name:
        return "sector-wave"
    return "unknown"


def _region_from_name(name: str) -> str:
    if "apollo15_20km" in name:
        return "apollo15_20km"
    if "tranquillitatis_balmer_like_20km" in name:
        return "tranquillitatis_balmer_like_20km"
    return "unknown"


def _cell_stats(rows: list[dict[str, Any]], *, keys: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(key) for key in keys)].append(row)
    stats: dict[str, dict[str, Any]] = {}
    for key, items in sorted(grouped.items(), key=lambda kv: tuple(str(v) for v in kv[0])):
        roi_counts = Counter(str(item.get("roi_class")) for item in items)
        positive_improvements = [
            float(item.get("primal_improvement") or 0.0)
            for item in items
            if item.get("roi_class") in POSITIVE_ROI
        ]
        negative_count = sum(roi_counts.get(name, 0) for name in TRAINING_NEGATIVE_ROI)
        positive_count = sum(roi_counts.get(name, 0) for name in POSITIVE_ROI)
        cell_key = "|".join(str(part) for part in key)
        stats[cell_key] = {
            "key": list(key),
            "row_count": len(items),
            "roi_class_counts": dict(sorted(roi_counts.items())),
            "positive_count": int(positive_count),
            "training_negative_count": int(negative_count),
            "unsupported_count": int(sum(roi_counts.get(name, 0) for name in UNSUPPORTED_ROI)),
            "positive_rate": (
                float(positive_count) / float(len(items)) if items else 0.0
            ),
            "avg_positive_primal_improvement": (
                sum(positive_improvements) / float(len(positive_improvements))
                if positive_improvements
                else 0.0
            ),
        }
    return stats


def _sample_gaps(
    cells: dict[str, dict[str, Any]], *, min_positive_per_cell: int, min_negative_per_cell: int
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for key, cell in cells.items():
        positive_gap = max(0, int(min_positive_per_cell) - int(cell["positive_count"]))
        negative_gap = max(0, int(min_negative_per_cell) - int(cell["training_negative_count"]))
        if positive_gap or negative_gap:
            gaps.append(
                {
                    "cell": key,
                    "positive_gap": positive_gap,
                    "negative_gap": negative_gap,
                    "row_count": int(cell["row_count"]),
                    "positive_rate": float(cell["positive_rate"]),
                    "avg_positive_primal_improvement": float(cell["avg_positive_primal_improvement"]),
                }
            )
    gaps.sort(
        key=lambda item: (
            -int(item["positive_gap"]),
            -float(item["avg_positive_primal_improvement"]),
            -float(item["positive_rate"]),
            str(item["cell"]),
        )
    )
    return gaps


def _existing_targets(rows: list[dict[str, Any]]) -> set[tuple[str, tuple[int, ...]]]:
    targets: set[tuple[str, tuple[int, ...]]] = set()
    for row in rows:
        context_hash = str(row.get("expected_context_hash") or row.get("context_hash") or "")
        sequence = tuple(int(task) for task in (row.get("target_sequence") or []))
        if context_hash and sequence:
            targets.add((context_hash, sequence))
    return targets


def _load_candidates(
    candidate_files: tuple[Path, ...], existing_targets: set[tuple[str, tuple[int, ...]]]
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, tuple[int, ...]]] = set()
    for path in candidate_files:
        if not path.exists():
            raise FileNotFoundError(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        for raw in payload.get("candidates") or []:
            item = _enrich_record(dict(raw))
            sequence = tuple(int(task) for task in (item.get("target_sequence") or []))
            context_hash = str(item.get("expected_context_hash") or item.get("context_hash") or "")
            key = (context_hash, sequence)
            if key in seen:
                continue
            seen.add(key)
            item["source_candidate_file"] = str(path)
            item["existing_roi_target"] = key in existing_targets
            if item["existing_roi_target"]:
                continue
            candidates.append(item)
    return candidates


def _recommend_candidates(
    *,
    candidates: list[dict[str, Any]],
    cell_stats: dict[str, dict[str, Any]],
    ordinal_stats: dict[str, dict[str, Any]],
    max_recommendations: int,
    min_positive_per_cell: int,
    min_negative_per_cell: int,
    max_per_cell: int,
) -> list[dict[str, Any]]:
    scored = []
    for candidate in candidates:
        cell_key = "|".join(
            str(candidate.get(key))
            for key in ("instance_family", "instance_region")
        )
        ordinal_key = "|".join(
            str(candidate.get(key))
            for key in ("instance_family", "instance_region", "instance_ordinal")
        )
        cell = cell_stats.get(cell_key, {})
        ordinal = ordinal_stats.get(ordinal_key, {})
        positive_count = int(cell.get("positive_count", 0))
        negative_count = int(cell.get("training_negative_count", 0))
        positive_gap = max(0, int(min_positive_per_cell) - positive_count)
        negative_gap = max(0, int(min_negative_per_cell) - negative_count)
        probability = float(candidate.get("decision_probability") or 0.0)
        best_rc = float(candidate.get("best_true_reduced_cost") or 0.0)
        avg_gain = float(cell.get("avg_positive_primal_improvement") or 0.0)
        positive_rate = float(cell.get("positive_rate") or 0.0)
        ordinal_positive_rate = float(ordinal.get("positive_rate") or 0.0)
        support_bonus = 0.5 if candidate.get("target_support_changing_proxy") else 0.0
        new_task_bonus = 0.5 if candidate.get("target_task_set_new") else 0.0
        roi_yield_signal = max(
            positive_rate,
            ordinal_positive_rate,
            min(1.0, max(0.0, avg_gain) / 50.0),
        )
        positive_gap_weight = 2.0 + 8.0 * roi_yield_signal
        if positive_rate < 0.15 and negative_count >= int(min_negative_per_cell):
            positive_gap_weight = min(positive_gap_weight, 2.5)
        score = (
            positive_gap_weight * positive_gap
            + 2.0 * negative_gap
            + 3.0 * positive_rate
            + 2.0 * ordinal_positive_rate
            + min(5.0, max(0.0, avg_gain) / 10.0)
            + probability
            + min(2.0, abs(best_rc) / 20.0)
            + support_bonus
            + new_task_bonus
        )
        reason = "positive_gap" if positive_gap > 0 else "candidate_pool_high_score"
        if positive_gap > 0 and negative_count >= int(min_negative_per_cell):
            reason = "positive_gap_with_negative_support"
        elif positive_count > 0 and positive_rate >= 0.5:
            reason = "positive_like_cell"
        elif negative_gap > 0:
            reason = "negative_balance_gap"
        if positive_count > 0 and positive_rate >= 0.35:
            recommendation_bucket = "positive_rich_exploit"
        elif positive_gap > 0:
            recommendation_bucket = "positive_gap_explore"
        elif negative_gap > 0:
            recommendation_bucket = "negative_balance"
        else:
            recommendation_bucket = "candidate_pool_high_score"
        scored.append(
            {
                **candidate,
                "score": round(score, 6),
                "reason": reason,
                "recommendation_bucket": recommendation_bucket,
                "roi_yield_signal": round(roi_yield_signal, 6),
                "positive_gap_weight": round(positive_gap_weight, 6),
                "cell": cell_key,
                "ordinal_cell": ordinal_key,
                "cell_positive_count": positive_count,
                "cell_training_negative_count": negative_count,
                "cell_positive_rate": round(positive_rate, 6),
                "cell_avg_positive_primal_improvement": round(avg_gain, 6),
                "ordinal_positive_rate": round(ordinal_positive_rate, 6),
                "positive_gap": positive_gap,
                "negative_gap": negative_gap,
                "name": candidate.get("name"),
                "instance": candidate.get("instance"),
                "instance_family": candidate.get("instance_family"),
                "instance_region": candidate.get("instance_region"),
                "instance_ordinal": candidate.get("instance_ordinal"),
                "decision_name": candidate.get("decision_name"),
                "decision_probability": probability,
                "best_true_reduced_cost": best_rc,
                "target_sequence": candidate.get("target_sequence"),
                "source_candidate_file": candidate.get("source_candidate_file"),
                "existing_roi_target": bool(candidate.get("existing_roi_target")),
            }
        )
    scored.sort(key=lambda item: (-float(item["score"]), str(item["name"])))
    limit = max(0, int(max_recommendations))
    if limit <= 0:
        return []
    per_cell_limit = int(max_per_cell)
    if per_cell_limit <= 0:
        return scored[:limit]

    selected: list[dict[str, Any]] = []
    selected_keys: set[tuple[str, tuple[int, ...]]] = set()
    per_cell_counts: Counter[str] = Counter()
    for item in scored:
        if len(selected) >= limit:
            break
        cell = str(item.get("cell") or "")
        if per_cell_counts[cell] >= per_cell_limit:
            continue
        key = _candidate_target_key(item)
        selected.append(item)
        selected_keys.add(key)
        per_cell_counts[cell] += 1

    return selected


def _candidate_target_key(item: dict[str, Any]) -> tuple[str, tuple[int, ...]]:
    return (
        str(item.get("expected_context_hash") or item.get("context_hash") or ""),
        tuple(int(task) for task in (item.get("target_sequence") or [])),
    )


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    top_cells = sorted(
        summary["family_region_cells"].items(),
        key=lambda item: (
            -float(item[1]["avg_positive_primal_improvement"]),
            -float(item[1]["positive_rate"]),
            str(item[0]),
        ),
    )[:8]
    lines = [
        "# GAT Worker ROI Sampling Priority Audit 报告",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "根据已有 target-priority worker ROI 标签，找出下一批最值得采样的",
        "family/region/ordinal cell。该流程只读现有 JSON/JSONL，不运行 BPC、",
        "pricing、RMP、worker，也不产生证书或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_worker_roi_sampling_priority = current",
        f"row_count = {summary['row_count']}",
        f"candidate_count = {summary['candidate_count']}",
        f"recommendation_count = {summary['recommendation_count']}",
        f"max_per_cell = {summary['max_per_cell']}",
        f"roi_class_counts = {summary['roi_class_counts']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        "```",
        "",
        "## Positive-rich cells",
        "",
        "```json",
        json.dumps(dict(top_cells), ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Sample gaps",
        "",
        "```json",
        json.dumps(summary["sample_gaps"][:12], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Recommendations",
        "",
        "```json",
        json.dumps(summary["recommendations"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 结论",
        "",
        "- 正 ROI 高度集中，不能按 rc 或 HIGH 数量盲目采样；",
        "- 每个 family/region cell 都需要正负样本平衡；",
        "- 候选推荐只用于下一批 audit-only A/B，不允许默认启用 worker；",
        "- GAT/kNN/OOD 仍不能证书，不能产生 official lower bound。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
