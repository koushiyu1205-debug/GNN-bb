#!/usr/bin/env python3
"""Build ROI labels for GAT target-priority worker candidates.

This is an offline bridge from audited target-priority worker A/B runs to a
second-stage GAT productivity dataset.  It is read-only: it consumes existing
audit/candidate JSON, writes labels, and never runs BPC, pricing, RMP, workers,
or certificates.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


DEFAULT_AUDIT_SUMMARY = Path(
    "BPC_future/results/gat_target_priority_worker_ab_audit_20260614/summary.json"
)
DEFAULT_CANDIDATE_SUMMARIES = (
    Path("BPC_future/results/gat_target_priority_candidates_20260614/summary.json"),
    Path("BPC_future/results/gat_target_priority_candidates_20roi_smoke_20260614/summary.json"),
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_worker_roi_dataset_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_gat_worker_roi_dataset_zh.md"
)


TRAINABLE_ROI_CLASSES = {"positive_primal_roi", "no_observed_roi", "negative_primal_roi"}


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _seq_key(value: Any) -> tuple[int, ...]:
    if not isinstance(value, list):
        return tuple()
    result: list[int] = []
    for item in value:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            return tuple()
    return tuple(result)


def _arc_key(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return tuple()
    return tuple(str(item) for item in value)


def _candidate_key(item: dict[str, Any]) -> tuple[str, str, tuple[int, ...], tuple[str, ...]]:
    return (
        str(item.get("instance") or ""),
        str(item.get("expected_context_hash") or ""),
        _seq_key(item.get("target_sequence")),
        _arc_key(item.get("target_arc_option_sequence")),
    )


def _load_candidate_features(paths: Iterable[Path]) -> dict[tuple[str, str, tuple[int, ...], tuple[str, ...]], dict[str, Any]]:
    features: dict[tuple[str, str, tuple[int, ...], tuple[str, ...]], dict[str, Any]] = {}
    for source in paths:
        path = Path(source)
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        candidates = payload.get("candidates")
        if candidates is None and (path.parent / "candidates.json").exists():
            candidates = json.loads((path.parent / "candidates.json").read_text(encoding="utf-8")).get("candidates")
        for candidate in candidates or []:
            if not isinstance(candidate, dict):
                continue
            key = _candidate_key(candidate)
            if key[0] and key[1] and key[2]:
                features.setdefault(key, dict(candidate))
    return features


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _label_row(record: dict[str, Any], candidate: dict[str, Any] | None) -> dict[str, Any]:
    roi_class = str(record.get("roi_class") or "unknown")
    primal_improvement = _float_or_none(record.get("primal_improvement"))
    columns_delta = _float_or_none(record.get("columns_delta"))
    exact_delta = _float_or_none(record.get("exact_pricing_calls_delta"))
    generated_delta = _float_or_none(record.get("generated_sequences_delta"))
    target_sequence = list(record.get("target_sequence") or [])
    arcs = list(record.get("target_arc_option_sequence") or [])
    worker_columns_added = bool(columns_delta is not None and columns_delta > 0)
    positive_primal_roi = bool(primal_improvement is not None and primal_improvement > 1.0e-9)
    negative_primal_roi = bool(primal_improvement is not None and primal_improvement < -1.0e-9)
    trainable = bool(
        roi_class in TRAINABLE_ROI_CLASSES
        and record.get("baseline_csv_exists")
        and record.get("worker_csv_exists")
        and not record.get("official_bound_effect")
        and not record.get("certificate_effect")
    )
    label = None
    if trainable:
        label = 1 if positive_primal_roi else 0
    candidate = candidate or {}
    return {
        "schema_version": "gat_worker_roi_dataset_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "instance": str(record.get("instance") or ""),
        "name": str(record.get("name") or ""),
        "expected_context_hash": str(record.get("expected_context_hash") or ""),
        "target_sequence": target_sequence,
        "target_arc_option_sequence": arcs,
        "target_length": len(target_sequence),
        "target_arc_count": len(arcs),
        "decision_name": str(candidate.get("decision_name") or ""),
        "decision_probability": _float_or_none(candidate.get("decision_probability")),
        "decision_reason": str(candidate.get("decision_reason") or ""),
        "best_true_reduced_cost": _float_or_none(candidate.get("best_true_reduced_cost")),
        "capture_cg_iter": _int_or_zero(candidate.get("capture_cg_iter")),
        "capture_returned_journey_count": _int_or_zero(candidate.get("capture_returned_journey_count")),
        "source_file": str(candidate.get("source_file") or ""),
        "candidate_feature_joined": bool(candidate),
        "baseline_status": str(record.get("baseline_status") or ""),
        "worker_status": str(record.get("worker_status") or ""),
        "baseline_primal": _float_or_none(record.get("baseline_primal")),
        "worker_primal": _float_or_none(record.get("worker_primal")),
        "primal_improvement": primal_improvement,
        "baseline_columns": _float_or_none(record.get("baseline_columns")),
        "worker_columns": _float_or_none(record.get("worker_columns")),
        "columns_delta": columns_delta,
        "exact_pricing_calls_delta": exact_delta,
        "generated_sequences_delta": generated_delta,
        "roi_class": roi_class,
        "label_worker_roi_positive": None if label is None else int(label),
        "label_worker_adds_columns": int(worker_columns_added),
        "label_positive_primal_roi": int(positive_primal_roi),
        "label_negative_primal_roi": int(negative_primal_roi),
        "training_eligible": bool(trainable),
        "training_exclusion_reason": "" if trainable else _exclusion_reason(record, roi_class),
    }


def _exclusion_reason(record: dict[str, Any], roi_class: str) -> str:
    if record.get("official_bound_effect") or record.get("certificate_effect"):
        return "forbidden_certificate_or_bound_effect"
    if not record.get("baseline_csv_exists") or not record.get("worker_csv_exists"):
        return "missing_ab_result"
    if roi_class not in TRAINABLE_ROI_CLASSES:
        return f"unsupported_roi_class:{roi_class}"
    return "not_training_eligible"


def build_roi_dataset(
    *,
    audit_summary_path: Path = DEFAULT_AUDIT_SUMMARY,
    candidate_summary_paths: Iterable[Path] = DEFAULT_CANDIDATE_SUMMARIES,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    min_positive_for_training: int = 5,
    min_negative_for_training: int = 5,
) -> dict[str, Any]:
    audit_path = Path(audit_summary_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("official_bound_effect") or audit.get("certificate_ready"):
        raise ValueError(f"audit summary has forbidden certificate/bound effect: {audit_path}")
    candidate_features = _load_candidate_features(candidate_summary_paths)
    rows: list[dict[str, Any]] = []
    for record in audit.get("records") or []:
        if not isinstance(record, dict):
            continue
        rows.append(_label_row(record, candidate_features.get(_candidate_key(record))))

    training_rows = [row for row in rows if row["training_eligible"]]
    label_counts = Counter(
        str(row["label_worker_roi_positive"]) for row in training_rows if row["label_worker_roi_positive"] is not None
    )
    roi_counts = Counter(str(row["roi_class"]) for row in rows)
    joined_count = sum(1 for row in rows if row["candidate_feature_joined"])
    positive_count = int(label_counts.get("1", 0))
    negative_count = int(label_counts.get("0", 0))
    training_ready = bool(
        positive_count >= int(min_positive_for_training)
        and negative_count >= int(min_negative_for_training)
    )
    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "no_certificate_effect": all(not row["certificate_effect"] for row in rows),
        "no_official_bound_effect": all(not row["official_bound_effect"] for row in rows),
        "has_rows": bool(rows),
        "has_training_rows": bool(training_rows),
        "has_positive_and_negative_training_labels": bool(positive_count > 0 and negative_count > 0),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "gat_worker_roi_rows.jsonl"
    csv_path = output_dir / "gat_worker_roi_rows.csv"
    _write_jsonl(jsonl_path, rows)
    _write_csv(csv_path, rows)
    summary = {
        "schema_version": "gat_worker_roi_dataset_summary_v1",
        "status": "built" if rows else "no_rows",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "audit_summary_path": str(audit_summary_path),
        "candidate_summary_paths": [str(path) for path in candidate_summary_paths],
        "jsonl_path": str(jsonl_path),
        "csv_path": str(csv_path),
        "row_count": len(rows),
        "training_row_count": len(training_rows),
        "candidate_feature_joined_count": joined_count,
        "label_counts": dict(sorted(label_counts.items())),
        "roi_class_counts": dict(sorted(roi_counts.items())),
        "positive_training_label_count": positive_count,
        "negative_training_label_count": negative_count,
        "min_positive_for_training": int(min_positive_for_training),
        "min_negative_for_training": int(min_negative_for_training),
        "training_ready": training_ready,
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "next_decision": "train_roi_gate" if training_ready else "collect_more_roi_labels",
    }
    _json_dump(output_dir / "summary.json", summary)
    _write_report(report, summary, rows)
    return summary


def _write_report(path: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    examples = [
        {
            "name": row["name"],
            "roi_class": row["roi_class"],
            "label_worker_roi_positive": row["label_worker_roi_positive"],
            "primal_improvement": row["primal_improvement"],
            "columns_delta": row["columns_delta"],
            "decision_probability": row["decision_probability"],
            "best_true_reduced_cost": row["best_true_reduced_cost"],
        }
        for row in rows[:12]
    ]
    lines = [
        "# GAT Worker ROI Dataset 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "把 target-priority worker A/B 审计结果转成第二阶段 GAT ROI 标签。",
        "该数据集用于学习“候选是否真的改变 RMP / primal 轨迹”，不是 pricing oracle，",
        "不运行 BPC / pricing / RMP / worker，也不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_worker_roi_dataset = current",
        f"status = {summary['status']}",
        f"row_count = {summary['row_count']}",
        f"training_row_count = {summary['training_row_count']}",
        f"label_counts = {summary['label_counts']}",
        f"roi_class_counts = {summary['roi_class_counts']}",
        f"training_ready = {str(summary['training_ready']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 样例",
        "",
        "```json",
        json.dumps(examples, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 结论",
        "",
    ]
    if summary["training_ready"]:
        lines.append("- 当前 positive / negative ROI 标签数量达到训练门槛，可进入 ROI gate 训练。")
    else:
        lines.append(
            "- 当前 ROI 标签数量仍不足以训练可靠 gate；应继续扩充 20-task A/B 标签。"
        )
    lines.extend(
        [
            "- `positive_primal_roi` 作为保守正样本；`no_observed_roi` / `negative_primal_roi` 作为负样本；",
            "- `columns_only_roi` 暂不作为主训练标签，可作为辅助分析；",
            "- missing / certificate-effect / official-bound-effect 样本不进入训练；",
            "- 该数据集只能用于离线校准，不能参与证书或官方下界。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-summary", type=Path, default=DEFAULT_AUDIT_SUMMARY)
    parser.add_argument("--candidate-summary", type=Path, action="append", default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-positive-for-training", type=int, default=5)
    parser.add_argument("--min-negative-for-training", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_roi_dataset(
        audit_summary_path=args.audit_summary,
        candidate_summary_paths=args.candidate_summary or list(DEFAULT_CANDIDATE_SUMMARIES),
        output_dir=args.output_dir,
        report=args.report,
        min_positive_for_training=max(1, int(args.min_positive_for_training)),
        min_negative_for_training=max(1, int(args.min_negative_for_training)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
