#!/usr/bin/env python3
"""Build a narrow repair plan from ROI-neighbor gated decision records.

This is an offline diagnostic. It reads previously generated kNN/OOD decision
records and ranks contexts where the ROI-neighbor shell delayed true high-ROI
rows, or where accepted high point-ROI rows still look too sparse to support a
stable ROI CI. It never runs BPC, pricing, RMP, workers, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable


DEFAULT_DECISION_RECORDS = [
    Path(
        "BPC_future/results/"
        "gat_batch_impact_knn_ood_v35_v28_rescue_roi_mean065_global_20260616/"
        "decision_records.jsonl"
    ),
    Path(
        "BPC_future/results/"
        "gat_batch_impact_knn_ood_v35_v29_p075_rescue_roi_mean065_global_20260616/"
        "decision_records.jsonl"
    ),
]
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_batch_impact_neighbor_roi_repair_plan_v36_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage3_v36_neighbor_roi_repair_plan_zh.md"
)

ROI_NEIGHBOR_DELAY_REASONS = {
    "knn_roi_mean_delay_queue",
    "knn_roi_ci_low_delay_queue",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--decision-records-jsonl",
        type=Path,
        action="append",
        default=None,
        help="Path to a kNN/OOD decision_records.jsonl file; may be repeated.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-high-roi", type=float, default=0.65)
    parser.add_argument("--top-k", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_neighbor_roi_repair_plan(
        decision_records_jsonl=args.decision_records_jsonl or DEFAULT_DECISION_RECORDS,
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        min_high_roi=float(args.min_high_roi),
        top_k=max(1, int(args.top_k)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def build_neighbor_roi_repair_plan(
    *,
    decision_records_jsonl: Iterable[Path],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    min_high_roi: float = 0.65,
    top_k: int = 20,
) -> dict[str, Any]:
    source_paths = [Path(path) for path in decision_records_jsonl]
    records = read_decision_records(source_paths)
    repair_rows = build_repair_candidate_rows(records, min_high_roi=float(min_high_roi))
    context_rows = build_context_repair_rows(repair_rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    repair_path = output_dir / "repair_candidates.jsonl"
    context_path = output_dir / "context_repair_priority.jsonl"
    _write_jsonl(repair_path, repair_rows)
    _write_jsonl(context_path, context_rows)

    summary = summarize_repair_plan(
        records=records,
        repair_rows=repair_rows,
        context_rows=context_rows,
        source_paths=source_paths,
        output_dir=output_dir,
        repair_path=repair_path,
        context_path=context_path,
        min_high_roi=float(min_high_roi),
        top_k=int(top_k),
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(Path(report), summary)
    return summary


def read_decision_records(paths: Iterable[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        path = Path(path)
        variant = path.parent.name
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                record = json.loads(line)
                record["_source_decision_records"] = str(path)
                record["_source_variant"] = variant
                record["_source_line_number"] = line_number
                records.append(record)
    return records


def build_repair_candidate_rows(
    records: list[dict[str, Any]],
    *,
    min_high_roi: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        if is_roi_neighbor_delayed_high_roi(record, min_high_roi=min_high_roi):
            rows.append(_repair_row(record, "roi_neighbor_delayed_high_roi"))
        if is_accepted_high_point_roi(record, min_high_roi=min_high_roi):
            rows.append(_repair_row(record, "accepted_high_point_roi_unstable"))
    return sorted(rows, key=_repair_sort_key)


def build_context_repair_rows(repair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in repair_rows:
        key = (
            str(row.get("context_hash") or ""),
            str(row.get("instance_family") or ""),
            int(row.get("instance_task_count") or 0),
        )
        grouped[key].append(row)

    context_rows: list[dict[str, Any]] = []
    for (context_hash, family, task_count), rows in grouped.items():
        roi_values = [_float(row.get("accepted_batch_roi_label")) for row in rows]
        delayed_rows = [
            row for row in rows if row.get("repair_type") == "roi_neighbor_delayed_high_roi"
        ]
        accepted_rows = [
            row for row in rows if row.get("repair_type") == "accepted_high_point_roi_unstable"
        ]
        source_variants = sorted({str(row.get("source_variant") or "") for row in rows})
        neighbor_means = [
            _float(row.get("neighbor_accepted_batch_roi_mean"))
            for row in rows
            if row.get("neighbor_accepted_batch_roi_mean") is not None
        ]
        priority_score = (
            len(delayed_rows) * 10.0
            + _max_or_zero(roi_values)
            + _sum_int(rows, "candidate_rescue_window_promoted_count") * 0.05
            + _sum_int(rows, "candidate_risk_adjusted_suppressed_count") * 0.05
            + len(accepted_rows) * 2.0
            - _mean_or_zero(neighbor_means)
        )
        action = _context_action(delayed_rows=delayed_rows, accepted_rows=accepted_rows)
        context_rows.append(
            {
                "schema_version": "gat_batch_impact_neighbor_roi_context_repair_v1",
                "context_hash": context_hash,
                "instance_family": family,
                "instance_task_count": task_count,
                "instance": _first_nonempty(rows, "instance"),
                "source_variants": source_variants,
                "repair_candidate_count": len(rows),
                "delayed_high_roi_count": len(delayed_rows),
                "accepted_high_point_roi_unstable_count": len(accepted_rows),
                "max_accepted_batch_roi_label": _max_or_zero(roi_values),
                "mean_accepted_batch_roi_label": _mean_or_zero(roi_values),
                "median_accepted_batch_roi_label": _median_or_none(roi_values),
                "mean_neighbor_accepted_batch_roi": _mean_or_none(neighbor_means),
                "candidate_rescue_window_promoted_count": _sum_int(
                    rows, "candidate_rescue_window_promoted_count"
                ),
                "candidate_risk_adjusted_suppressed_count": _sum_int(
                    rows, "candidate_risk_adjusted_suppressed_count"
                ),
                "candidate_predicted_high_priority_count": _sum_int(
                    rows, "candidate_predicted_high_priority_count"
                ),
                "primary_action": action,
                "priority_score": priority_score,
                "exact_safe_scope": "diagnostic_only_no_certificate_effect",
                "training_label_allowed_before_worker_reachability": False,
            }
        )
    return sorted(context_rows, key=lambda row: (-float(row["priority_score"]), row["context_hash"]))


def is_roi_neighbor_delayed_high_roi(
    record: dict[str, Any],
    *,
    min_high_roi: float,
) -> bool:
    if str(record.get("decision_reason") or "") not in ROI_NEIGHBOR_DELAY_REASONS:
        return False
    if str(record.get("decision_name") or "") != "DELAY_QUEUE":
        return False
    if bool(record.get("is_label_unsafe")):
        return False
    if int(record.get("label_high_priority") or 0) != 1:
        return False
    return _float(record.get("accepted_batch_roi_label")) >= float(min_high_roi)


def is_accepted_high_point_roi(
    record: dict[str, Any],
    *,
    min_high_roi: float,
) -> bool:
    if str(record.get("decision_name") or "") != "HIGH_PRIORITY":
        return False
    if bool(record.get("is_label_unsafe")):
        return False
    return _float(record.get("accepted_batch_roi_label")) >= float(min_high_roi)


def summarize_repair_plan(
    *,
    records: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    source_paths: list[Path],
    output_dir: Path,
    repair_path: Path,
    context_path: Path,
    min_high_roi: float,
    top_k: int,
) -> dict[str, Any]:
    repair_type_counts = Counter(str(row.get("repair_type") or "") for row in repair_rows)
    family_counts = Counter(str(row.get("instance_family") or "") for row in repair_rows)
    task_counts = Counter(str(row.get("instance_task_count") or "") for row in repair_rows)
    delayed_high = [
        row for row in repair_rows if row.get("repair_type") == "roi_neighbor_delayed_high_roi"
    ]
    accepted_high = [
        row for row in repair_rows if row.get("repair_type") == "accepted_high_point_roi_unstable"
    ]
    summary = {
        "schema_version": "gat_batch_impact_neighbor_roi_repair_plan_v1",
        "status": "gat_batch_impact_neighbor_roi_repair_plan_built",
        "stage": "Stage 3",
        "variant": "v36_neighbor_roi_repair_plan",
        "decision_records_jsonl": [str(path) for path in source_paths],
        "output_dir": str(output_dir),
        "repair_candidates_path": str(repair_path),
        "context_repair_priority_path": str(context_path),
        "min_high_roi": float(min_high_roi),
        "source_record_count": len(records),
        "repair_candidate_count": len(repair_rows),
        "context_repair_count": len(context_rows),
        "roi_neighbor_delayed_high_roi_count": len(delayed_high),
        "accepted_high_point_roi_unstable_count": len(accepted_high),
        "repair_type_counts": dict(sorted(repair_type_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "task_count_counts": dict(sorted(task_counts.items())),
        "top_contexts": context_rows[: int(top_k)],
        "recommended_next_step": _recommended_next_step(
            delayed_high_count=len(delayed_high),
            accepted_high_count=len(accepted_high),
        ),
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "official_bound_effect": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "training_label_allowed_before_worker_reachability": False,
        "stage4_candidate_ready": False,
        "all_checks_pass": True,
    }
    return summary


def write_report(report: Path, summary: dict[str, Any]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    top_contexts = summary.get("top_contexts") or []
    lines = [
        "# 2026-06-16 BPC_future GAT Target Mode Stage 3 v36 Neighbor ROI Repair Plan 报告",
        "",
        "## 结论",
        "",
        "v36 是离线 repair-plan，不是 Stage 4 candidate，也不运行 BPC / pricing / RMP / worker / certificate。",
        "它把 v35 的 ROI-neighbor blocker 拆成两个可执行队列：",
        "",
        "- `roi_neighbor_delayed_high_roi`：被 ROI-neighbor shell 延迟、但真实 trajectory ROI 已过线的样本；",
        "- `accepted_high_point_roi_unstable`：被接受且 point ROI 高、但需要继续做 context/outlier 分解的样本。",
        "",
        "```text",
        f"source_record_count = {summary['source_record_count']}",
        f"repair_candidate_count = {summary['repair_candidate_count']}",
        f"context_repair_count = {summary['context_repair_count']}",
        f"roi_neighbor_delayed_high_roi_count = {summary['roi_neighbor_delayed_high_roi_count']}",
        f"accepted_high_point_roi_unstable_count = {summary['accepted_high_point_roi_unstable_count']}",
        f"stage4_candidate_ready = {str(summary['stage4_candidate_ready']).lower()}",
        "```",
        "",
        "## Top Contexts",
        "",
        "| context | family | task | delayed high ROI | accepted high point ROI | max ROI | median ROI | action |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in top_contexts[:10]:
        lines.append(
            "| {context} | {family} | {task} | {delayed} | {accepted} | {roi:.4f} | {median_roi:.4f} | {action} |".format(
                context=str(row.get("context_hash") or ""),
                family=str(row.get("instance_family") or ""),
                task=int(row.get("instance_task_count") or 0),
                delayed=int(row.get("delayed_high_roi_count") or 0),
                accepted=int(row.get("accepted_high_point_roi_unstable_count") or 0),
                roi=float(row.get("max_accepted_batch_roi_label") or 0.0),
                median_roi=float(row.get("median_accepted_batch_roi_label") or 0.0),
                action=str(row.get("primary_action") or ""),
            )
        )
    lines.extend(
        [
            "",
            "## 判断",
            "",
            "这批样本不支持继续全局放宽 threshold / rescue window。下一步应围绕 top contexts 做 narrow same-context contrast，",
            "并把训练目标补成 ROI-neighborhood stability / context-local ROI ranking，而不是用 true-RC 命中率替代 trajectory ROI。",
            "",
            "## Exact-safe Boundary",
            "",
            "```text",
            "diagnostic_only = true",
            "runs_bpc_or_pricing = false",
            "production_ready = false",
            "default_enabled = false",
            "official_bound_effect = false",
            "selector_can_certificate = false",
            "gate_can_permanently_discard_negative_columns = false",
            "```",
            "",
            "GAT / CBF / kNN / OOD 只能做 discovery ordering 和 finite-delay admission scheduling。",
            "最终 OPTIMAL / no-negative certificate 仍只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 exhaustive closure。",
            "",
            "## 产物",
            "",
            "```text",
            f"summary = {summary['output_dir']}/summary.json",
            f"repair_candidates = {summary['repair_candidates_path']}",
            f"context_repair_priority = {summary['context_repair_priority_path']}",
            "```",
            "",
            "## 下一步",
            "",
            str(summary.get("recommended_next_step") or ""),
            "",
        ]
    )
    report.write_text("\n".join(lines), encoding="utf-8")


def _repair_row(record: dict[str, Any], repair_type: str) -> dict[str, Any]:
    return {
        "schema_version": "gat_batch_impact_neighbor_roi_repair_candidate_v1",
        "repair_type": repair_type,
        "context_hash": str(record.get("context_hash") or ""),
        "instance": str(record.get("instance") or record.get("instance_path") or ""),
        "instance_family": str(record.get("instance_family") or ""),
        "instance_task_count": int(record.get("instance_task_count") or 0),
        "accepted_batch_roi_label": _float(record.get("accepted_batch_roi_label")),
        "decision_name": str(record.get("decision_name") or ""),
        "decision_reason": str(record.get("decision_reason") or ""),
        "batch_score": _float(record.get("batch_score")),
        "candidate_threshold": _float(record.get("candidate_threshold")),
        "neighbor_accepted_batch_roi_mean": _optional_float(
            record.get("neighbor_accepted_batch_roi_mean")
        ),
        "neighbor_accepted_batch_roi_ci_low": _optional_float(
            record.get("neighbor_accepted_batch_roi_ci_low")
        ),
        "neighbor_accepted_batch_roi_count": int(
            record.get("neighbor_accepted_batch_roi_count") or 0
        ),
        "neighbor_delay_fraction": _optional_float(record.get("neighbor_delay_fraction")),
        "candidate_predicted_high_priority_count": int(
            record.get("candidate_predicted_high_priority_count") or 0
        ),
        "candidate_rescue_window_promoted_count": int(
            record.get("candidate_rescue_window_promoted_count") or 0
        ),
        "candidate_risk_adjusted_suppressed_count": int(
            record.get("candidate_risk_adjusted_suppressed_count") or 0
        ),
        "candidate_signature_id_count": int(record.get("candidate_signature_id_count") or 0),
        "candidate_signature_ids": list(record.get("candidate_signature_ids") or []),
        "high_priority_candidate_signature_ids": list(
            record.get("high_priority_candidate_signature_ids") or []
        ),
        "sample_path": str(record.get("sample_path") or ""),
        "source_variant": str(record.get("_source_variant") or ""),
        "source_decision_records": str(record.get("_source_decision_records") or ""),
        "source_line_number": int(record.get("_source_line_number") or 0),
        "exact_safe_scope": "diagnostic_only_no_certificate_effect",
        "training_label_allowed_before_worker_reachability": False,
    }


def _repair_sort_key(row: dict[str, Any]) -> tuple[float, float, str, str]:
    type_priority = 1.0 if row.get("repair_type") == "roi_neighbor_delayed_high_roi" else 0.0
    return (
        -type_priority,
        -float(row.get("accepted_batch_roi_label") or 0.0),
        str(row.get("context_hash") or ""),
        str(row.get("source_variant") or ""),
    )


def _context_action(
    *,
    delayed_rows: list[dict[str, Any]],
    accepted_rows: list[dict[str, Any]],
) -> str:
    if delayed_rows and accepted_rows:
        return "collect_same_context_contrast_and_audit_accepted_outliers"
    if delayed_rows:
        return "collect_same_context_positive_negative_contrast_or_repair_embedding_neighbors"
    return "audit_outlier_context_and_add_local_negative_contrast"


def _recommended_next_step(*, delayed_high_count: int, accepted_high_count: int) -> str:
    if delayed_high_count:
        return (
            "围绕 delayed high-ROI contexts 构建 narrow same-context contrast tranche，"
            "再加入 ROI-neighborhood stability 诊断后重训；在此之前不要进入 Stage 4 replay。"
        )
    if accepted_high_count:
        return (
            "先分解 accepted high point-ROI contexts 的 outlier 风险，并补 local negative contrast，"
            "再考虑放宽 ROI-neighbor shell。"
        )
    return "没有找到 repair candidates；需要先检查上游 v35 decision record 覆盖。"


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return _float(value)


def _sum_int(rows: Iterable[dict[str, Any]], key: str) -> int:
    return sum(int(row.get(key) or 0) for row in rows)


def _first_nonempty(rows: Iterable[dict[str, Any]], key: str) -> str:
    for row in rows:
        value = str(row.get(key) or "")
        if value:
            return value
    return ""


def _max_or_zero(values: Iterable[float]) -> float:
    values = list(values)
    return max(values) if values else 0.0


def _mean_or_zero(values: Iterable[float]) -> float:
    values = list(values)
    return float(mean(values)) if values else 0.0


def _mean_or_none(values: Iterable[float]) -> float | None:
    values = list(values)
    return float(mean(values)) if values else None


def _median_or_none(values: Iterable[float]) -> float | None:
    values = list(values)
    return float(median(values)) if values else None


if __name__ == "__main__":
    raise SystemExit(main())
