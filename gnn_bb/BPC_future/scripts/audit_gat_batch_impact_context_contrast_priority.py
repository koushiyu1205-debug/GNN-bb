#!/usr/bin/env python3
"""Prioritize context-local contrast collection for missed high-ROI batches.

This offline diagnostic merges candidate score-margin evidence with embedding
separation evidence. It ranks missed high-ROI contexts by whether they need
same-context positive/negative intervention rows, candidate-head contrast, or
only threshold-boundary diagnostics. It never runs BPC, pricing, RMP, workers,
or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
from statistics import mean, median
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DEFAULT_SCORE_MARGIN_SUMMARY = Path(
    "BPC_future/results/"
    "gat_batch_impact_score_margin_audit_v15_exact_safe_hits_batch8_ab_roi_20260616/"
    "summary.json"
)
DEFAULT_EMBEDDING_SUMMARY = Path(
    "BPC_future/results/"
    "gat_batch_impact_embedding_separation_v15_exact_safe_hits_batch8_ab_roi_20260616/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "gat_batch_impact_context_contrast_priority_v15_structural_gap_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage3_v33_v15_context_contrast_priority_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score-margin-summary", type=Path, default=DEFAULT_SCORE_MARGIN_SUMMARY)
    parser.add_argument("--embedding-summary", type=Path, default=DEFAULT_EMBEDDING_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--top-contexts", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_context_contrast_priority(
        score_margin_summary=Path(args.score_margin_summary),
        embedding_summary=Path(args.embedding_summary),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        top_contexts=max(1, int(args.top_contexts)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_context_contrast_priority(
    *,
    score_margin_summary: Path = DEFAULT_SCORE_MARGIN_SUMMARY,
    embedding_summary: Path = DEFAULT_EMBEDDING_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    top_contexts: int = 20,
) -> dict[str, Any]:
    score_summary = _read_json(score_margin_summary)
    embedding = _read_json(embedding_summary)
    _assert_offline_contract(score_summary, label="score_margin_summary")
    _assert_offline_contract(embedding, label="embedding_summary")

    score_records = _dedupe_records(
        _read_jsonl(Path(str(score_summary.get("missed_high_roi_score_margins_path") or ""))),
        key_fields=(
            "context_hash",
            "instance_path",
            "instance",
            "accepted_batch_roi_label",
            "max_safe_candidate_score",
            "candidate_count",
        ),
    )
    embedding_records = _dedupe_records(
        _read_jsonl(Path(str(embedding.get("missed_high_roi_embedding_separation_path") or ""))),
        key_fields=(
            "context_hash",
            "sample_path",
            "accepted_batch_roi_label",
            "max_candidate_score",
            "candidate_count",
        ),
    )
    rows = build_context_priority_rows(score_records, embedding_records)
    output_dir.mkdir(parents=True, exist_ok=True)
    context_path = output_dir / "context_contrast_priority.jsonl"
    top_path = output_dir / "top_context_contrast_priority.jsonl"
    _write_jsonl(context_path, rows)
    _write_jsonl(top_path, rows[: int(top_contexts)])

    priority_summary = summarize_context_priority(rows)
    summary = {
        "schema_version": "gat_batch_impact_context_contrast_priority_v1",
        "status": "gat_batch_impact_context_contrast_prioritized",
        "score_margin_summary": str(score_margin_summary),
        "embedding_summary": str(embedding_summary),
        "output_dir": str(output_dir),
        "context_contrast_priority_path": str(context_path),
        "top_context_contrast_priority_path": str(top_path),
        "score_margin_record_count": len(score_records),
        "embedding_record_count": len(embedding_records),
        "top_contexts_requested": int(top_contexts),
        "priority_summary": priority_summary,
        "top_contexts": rows[: int(top_contexts)],
        "recommended_next_step": _recommended_next_step(priority_summary),
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "training_label_allowed_before_worker_reachability": False,
        "all_checks_pass": True,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def build_context_priority_rows(
    score_records: list[dict[str, Any]],
    embedding_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    score_by_context: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    embedding_by_context: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for record in score_records:
        score_by_context[_context_key(record)].append(record)
    for record in embedding_records:
        embedding_by_context[_context_key(record)].append(record)

    rows: list[dict[str, Any]] = []
    for key in sorted(set(score_by_context) | set(embedding_by_context)):
        score_group = score_by_context.get(key, [])
        embedding_group = embedding_by_context.get(key, [])
        row = _context_priority_row(key, score_group, embedding_group)
        rows.append(row)
    return sorted(rows, key=_priority_sort_key)


def summarize_context_priority(rows: list[dict[str, Any]]) -> dict[str, Any]:
    action_counts = Counter(str(row.get("primary_action") or "") for row in rows)
    family_counts = Counter(str(row.get("family") or "") for row in rows)
    task_counts = Counter(str(row.get("task_count") or 0) for row in rows)
    data_collection = [
        row
        for row in rows
        if str(row.get("primary_action") or "").startswith("collect_same_context")
    ]
    model_change = [
        row
        for row in rows
        if row.get("primary_action") == "add_context_local_candidate_margin_or_head_capacity"
    ]
    negative_mixture = [
        row
        for row in rows
        if int(row.get("nearest_negative_closer_count") or 0) > 0
    ]
    deep_gap = [row for row in rows if int(row.get("deep_candidate_gap_count") or 0) > 0]
    return {
        "context_count": len(rows),
        "contexts_requiring_data_collection": len(data_collection),
        "contexts_requiring_model_change": len(model_change),
        "contexts_with_negative_neighbor_mixture": len(negative_mixture),
        "contexts_with_deep_candidate_gap": len(deep_gap),
        "action_counts": dict(sorted(action_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "task_count_counts": dict(sorted(task_counts.items())),
        "missed_high_roi_score_records": sum(
            int(row.get("score_missed_high_roi_count") or 0) for row in rows
        ),
        "missed_high_roi_embedding_records": sum(
            int(row.get("embedding_missed_high_roi_count") or 0) for row in rows
        ),
        "max_priority_score": _max_or_none(
            [float(row.get("priority_score") or 0.0) for row in rows]
        ),
        "median_priority_score": _median_or_none(
            [float(row.get("priority_score") or 0.0) for row in rows]
        ),
        "primary_blocker": _primary_blocker(rows),
    }


def _context_priority_row(
    key: tuple[str, str, int],
    score_group: list[dict[str, Any]],
    embedding_group: list[dict[str, Any]],
) -> dict[str, Any]:
    context_hash, family, task_count = key
    all_records = [*score_group, *embedding_group]
    roi_values = [_float(record.get("accepted_batch_roi_label")) for record in all_records]
    candidate_margins = [
        _float(record.get("max_safe_candidate_score_margin"))
        for record in score_group
        if record.get("max_safe_candidate_score_margin") is not None
    ]
    if not candidate_margins:
        candidate_margins = [
            _float(record.get("max_candidate_score_margin"))
            for record in embedding_group
            if record.get("max_candidate_score_margin") is not None
        ]
    deep_gap_count = sum(
        int(str(record.get("candidate_margin_bucket") or "") == "deep_candidate_score_gap")
        for record in score_group
    )
    moderate_gap_count = sum(
        int(str(record.get("candidate_margin_bucket") or "") == "moderate_candidate_score_gap")
        for record in score_group
    )
    near_threshold_count = sum(
        int(str(record.get("candidate_margin_bucket") or "") == "near_candidate_threshold")
        for record in score_group
    )
    if not score_group:
        deep_gap_count = sum(
            int(_float(record.get("max_candidate_score_margin")) <= -0.20)
            for record in embedding_group
        )
        moderate_gap_count = sum(
            int(-0.20 < _float(record.get("max_candidate_score_margin")) < -0.05)
            for record in embedding_group
        )
        near_threshold_count = sum(
            int(_float(record.get("max_candidate_score_margin")) >= -0.05)
            for record in embedding_group
        )

    missing_contrast_count = sum(
        int(
            bool(record.get("needs_same_context_contrast"))
            or not bool(record.get("has_same_context_low_roi_or_delay_contrast", True))
        )
        for record in score_group
    )
    negative_closer_count = sum(
        int(bool(record.get("nearest_negative_closer"))) for record in embedding_group
    )
    knn_positive_fractions = [
        _float(record.get("knn_positive_fraction"))
        for record in embedding_group
        if record.get("knn_positive_fraction") is not None
    ]
    same_context_low_or_delay = sum(
        int(_float(record.get("same_context_low_roi_or_delay_count")) > 0.0)
        for record in score_group
    )
    priority_score = _priority_score(
        missed_count=max(len(score_group), len(embedding_group)),
        max_roi=_max_or_none(roi_values) or 0.0,
        deep_gap_count=deep_gap_count,
        moderate_gap_count=moderate_gap_count,
        near_threshold_count=near_threshold_count,
        missing_contrast_count=missing_contrast_count,
        negative_closer_count=negative_closer_count,
        mean_knn_positive_fraction=_mean_or_none(knn_positive_fractions),
        family=family,
        task_count=task_count,
    )
    primary_action = _primary_action(
        missing_contrast_count=missing_contrast_count,
        negative_closer_count=negative_closer_count,
        mean_knn_positive_fraction=_mean_or_none(knn_positive_fractions),
        deep_gap_count=deep_gap_count,
        moderate_gap_count=moderate_gap_count,
        near_threshold_count=near_threshold_count,
    )
    return {
        "context_hash": context_hash,
        "family": family,
        "task_count": task_count,
        "region": _first_nonempty(record.get("region") for record in all_records),
        "score_missed_high_roi_count": len(score_group),
        "embedding_missed_high_roi_count": len(embedding_group),
        "missed_high_roi_count_proxy": max(len(score_group), len(embedding_group)),
        "max_missed_roi": _max_or_none(roi_values),
        "mean_missed_roi": _mean_or_none(roi_values),
        "min_candidate_margin": _min_or_none(candidate_margins),
        "mean_candidate_margin": _mean_or_none(candidate_margins),
        "deep_candidate_gap_count": deep_gap_count,
        "moderate_candidate_gap_count": moderate_gap_count,
        "near_candidate_threshold_count": near_threshold_count,
        "missing_same_context_contrast_count": missing_contrast_count,
        "same_context_low_roi_or_delay_record_count": same_context_low_or_delay,
        "nearest_negative_closer_count": negative_closer_count,
        "mean_knn_positive_fraction": _mean_or_none(knn_positive_fractions),
        "median_knn_positive_fraction": _median_or_none(knn_positive_fractions),
        "priority_score": priority_score,
        "primary_action": primary_action,
        "exact_safe_scope": "diagnostic_only_no_certificate_effect",
        "training_label_allowed_before_worker_reachability": False,
    }


def _priority_score(
    *,
    missed_count: int,
    max_roi: float,
    deep_gap_count: int,
    moderate_gap_count: int,
    near_threshold_count: int,
    missing_contrast_count: int,
    negative_closer_count: int,
    mean_knn_positive_fraction: float | None,
    family: str,
    task_count: int,
) -> float:
    score = 5.0 * float(missed_count)
    score += 4.0 * float(deep_gap_count)
    score += 2.0 * float(moderate_gap_count)
    score += 1.0 * float(near_threshold_count)
    score += 4.0 * float(negative_closer_count)
    score += 3.0 * float(missing_contrast_count)
    score += min(max(float(max_roi), 0.0), 5.0)
    if mean_knn_positive_fraction is not None and mean_knn_positive_fraction <= 0.2:
        score += 2.0
    if family == "random-wave" and task_count == 50:
        score += 2.0
    if family == "sector-wave" and task_count == 20:
        score += 1.0
    return float(score)


def _primary_action(
    *,
    missing_contrast_count: int,
    negative_closer_count: int,
    mean_knn_positive_fraction: float | None,
    deep_gap_count: int,
    moderate_gap_count: int,
    near_threshold_count: int,
) -> str:
    if missing_contrast_count > 0 or negative_closer_count > 0:
        return "collect_same_context_positive_negative_contrast"
    if mean_knn_positive_fraction is not None and mean_knn_positive_fraction <= 0.2:
        return "collect_same_context_positive_negative_contrast"
    if deep_gap_count > 0 or moderate_gap_count > 0:
        return "add_context_local_candidate_margin_or_head_capacity"
    if near_threshold_count > 0:
        return "threshold_boundary_diagnostic_only"
    return "continue_monitoring"


def _primary_blocker(rows: list[dict[str, Any]]) -> str:
    if any(int(row.get("nearest_negative_closer_count") or 0) > 0 for row in rows):
        return "structural_negative_neighbor_mixture_or_missing_context_contrast"
    if any(int(row.get("deep_candidate_gap_count") or 0) > 0 for row in rows):
        return "candidate_head_deep_score_gap"
    if any(int(row.get("near_candidate_threshold_count") or 0) > 0 for row in rows):
        return "threshold_boundary_secondary"
    return "no_missed_high_roi_context_priority"


def _recommended_next_step(priority_summary: dict[str, Any]) -> dict[str, Any]:
    primary = str(priority_summary.get("primary_blocker") or "")
    if primary == "structural_negative_neighbor_mixture_or_missing_context_contrast":
        next_step = "collect_context_local_contrast_before_threshold_or_rescue_changes"
    elif primary == "candidate_head_deep_score_gap":
        next_step = "add_context_local_margin_or_candidate_head_capacity_then_reaudit"
    else:
        next_step = "threshold_boundary_audit_only_keep_stage3_gate"
    return {
        "primary": next_step,
        "do_not_do": [
            "lower_candidate_threshold_to_force_acceptance",
            "treat_true_rc_negative_or_exact_safe_hit_as_positive_label",
            "use_gat_or_knn_ood_as_certificate_source",
        ],
    }


def _context_key(record: dict[str, Any]) -> tuple[str, str, int]:
    return (
        str(record.get("context_hash") or ""),
        str(record.get("family") or record.get("instance_family") or "unknown"),
        int(float(record.get("task_count") or record.get("instance_task_count") or 0)),
    )


def _priority_sort_key(row: dict[str, Any]) -> tuple[float, float, int, str]:
    return (
        -float(row.get("priority_score") or 0.0),
        -float(row.get("max_missed_roi") or 0.0),
        -int(row.get("missed_high_roi_count_proxy") or 0),
        str(row.get("context_hash") or ""),
    )


def _dedupe_records(
    records: list[dict[str, Any]],
    *,
    key_fields: Iterable[str],
) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    result: list[dict[str, Any]] = []
    for record in records:
        key = tuple(_dedupe_value(record.get(field)) for field in key_fields)
        if key in seen:
            continue
        seen.add(key)
        result.append(record)
    return result


def _dedupe_value(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 9)
    if isinstance(value, int):
        return value
    return str(value)


def _assert_offline_contract(summary: dict[str, Any], *, label: str) -> None:
    if not bool(summary.get("diagnostic_only", True)):
        raise ValueError(f"{label} is not diagnostic_only")
    if bool(summary.get("runs_bpc_or_pricing", False)):
        raise ValueError(f"{label} unexpectedly runs BPC or pricing")
    if bool(summary.get("selector_can_certificate", False)):
        raise ValueError(f"{label} unexpectedly can certify")
    if bool(summary.get("official_bound_effect", False)):
        raise ValueError(f"{label} unexpectedly affects official bounds")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    stats = summary["priority_summary"]
    lines = [
        "# BPC Future GAT Stage 3 v33 v15 Context Contrast Priority 审计",
        "",
        "日期：2026-06-16",
        "",
        "## 结论",
        "",
        "本报告把 v15 的 score-margin 审计和 v32 embedding separation 审计合并到 context 级别，",
        "只用于决定下一轮 same-context contrast / candidate-head 结构修正优先级。",
        "它不运行 BPC、pricing、RMP、worker 或 certificate。",
        "",
        "```text",
        "stage = Stage 3",
        "variant = v33_v15_context_contrast_priority",
        f"context_count = {stats['context_count']}",
        f"contexts_requiring_data_collection = {stats['contexts_requiring_data_collection']}",
        f"contexts_requiring_model_change = {stats['contexts_requiring_model_change']}",
        f"contexts_with_negative_neighbor_mixture = {stats['contexts_with_negative_neighbor_mixture']}",
        f"contexts_with_deep_candidate_gap = {stats['contexts_with_deep_candidate_gap']}",
        f"primary_blocker = {stats['primary_blocker']}",
        "diagnostic_only = true",
        "runs_bpc_or_pricing = false",
        "selector_can_certificate = false",
        "official_bound_effect = false",
        "training_label_allowed_before_worker_reachability = false",
        "```",
        "",
        "## Top Contexts",
        "",
        "```json",
        json.dumps(summary["top_contexts"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 下一步",
        "",
        "```json",
        json.dumps(summary["recommended_next_step"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Exact-safe 边界",
        "",
        "- 该审计只读离线 artifact，不产生训练标签；",
        "- worker reachability / causal ROI 审计完成前，任何候选都不能转成 positive label；",
        "- GAT / kNN / OOD 仍不能产生 official bound 或 certificate；",
        "- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result


def _mean_or_none(values: Iterable[float]) -> float | None:
    clean = [float(value) for value in values]
    return float(mean(clean)) if clean else None


def _median_or_none(values: Iterable[float]) -> float | None:
    clean = [float(value) for value in values]
    return float(median(clean)) if clean else None


def _min_or_none(values: Iterable[float]) -> float | None:
    clean = [float(value) for value in values]
    return min(clean) if clean else None


def _max_or_none(values: Iterable[float]) -> float | None:
    clean = [float(value) for value in values]
    return max(clean) if clean else None


def _first_nonempty(values: Iterable[Any]) -> str:
    for value in values:
        if value not in (None, ""):
            return str(value)
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
