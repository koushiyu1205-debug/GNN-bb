#!/usr/bin/env python3
"""Build offline training rows from Journey tail low-min-fill A/B audits.

The input is produced by ``audit_journey_tail_minfill_ab_results.py``.  This
script does not run BPC, pricing, RMP, or produce certificates.  It only turns
paired replay outcomes into a stable, non-production training-row format.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_tail_minfill_training_rows_20260625")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260625_bpc_future_journey_tail_minfill_training_rows_zh.md"
)

FEATURE_SCHEMA: tuple[str, ...] = (
    "source_tail_min_fill_candidate_count",
    "source_class_certified_no_negative",
    "source_class_found_negative",
    "source_class_time_limit_no_column_uncertified",
    "source_class_no_completion_bound_retry",
    "candidate_min_fill_gap",
)

OUTCOME_SCHEMA: tuple[str, ...] = (
    "baseline_wall_time",
    "optin_wall_time",
    "wall_time_delta",
    "baseline_solving_time",
    "optin_solving_time",
    "solving_time_delta",
    "baseline_status_optimal",
    "optin_status_optimal",
    "baseline_external_timeout",
    "optin_external_timeout",
    "pricing_calls_delta",
    "exact_pricing_calls_delta",
    "completion_retry_count_delta",
    "completion_retry_negative_journeys_delta",
    "completion_retry_selected_trips_delta",
    "baseline_tail_minfill_candidate_count",
    "optin_tail_minfill_candidate_count",
    "baseline_tail_minfill_applied_count",
    "optin_tail_minfill_applied_count",
)

LABEL_SCHEMA: tuple[str, ...] = (
    "y_strict_positive",
    "y_positive_speedup",
    "y_hard_negative",
    "y_no_effect_guard",
    "y_regression",
    "y_target200_success",
    "y_timeout_resolved",
    "y_wall_time_reduced",
    "y_completion_retry_reduced",
    "y_exact_pricing_reduced",
    "y_trainable_positive",
    "y_trainable_negative",
    "y_shadow_only",
)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


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


def _load_ab_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            summary = _read_json(path / "summary.json")
            raw_rows = summary.get("rows")
            if isinstance(raw_rows, list):
                rows.extend(row for row in raw_rows if isinstance(row, dict))
            else:
                rows.extend(_iter_jsonl(path / "tail_minfill_ab_rows.jsonl"))
            continue
        if path.name == "summary.json":
            raw_rows = _read_json(path).get("rows")
            if isinstance(raw_rows, list):
                rows.extend(row for row in raw_rows if isinstance(row, dict))
            continue
        if path.suffix == ".jsonl":
            rows.extend(_iter_jsonl(path))
            continue
        raw_rows = _read_json(path).get("rows")
        if isinstance(raw_rows, list):
            rows.extend(row for row in raw_rows if isinstance(row, dict))
    return rows


def _float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return int(default)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _status_optimal(metrics: dict[str, Any]) -> float:
    return 1.0 if str(metrics.get("status") or "") == "OPTIMAL" else 0.0


def _bool_float(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, str):
        return 1.0 if value.strip().lower() in {"1", "true", "yes", "y"} else 0.0
    return 1.0 if value else 0.0


def _one_hot_source_class(source_class: str) -> dict[str, float]:
    normalized = source_class.strip()
    return {
        "source_class_certified_no_negative": 1.0
        if normalized == "completion_bound_certified_no_negative"
        else 0.0,
        "source_class_found_negative": 1.0
        if normalized == "completion_bound_found_negative"
        else 0.0,
        "source_class_time_limit_no_column_uncertified": 1.0
        if normalized == "completion_bound_time_limit_no_column_uncertified"
        else 0.0,
        "source_class_no_completion_bound_retry": 1.0
        if normalized == "no_completion_bound_retry"
        else 0.0,
    }


def _first_int(values: Any, default: int) -> int:
    if isinstance(values, list) and values:
        return _int(values[0], default)
    return int(default)


def _build_row(ab_row: dict[str, Any]) -> dict[str, Any]:
    baseline = ab_row.get("baseline") if isinstance(ab_row.get("baseline"), dict) else {}
    optin = ab_row.get("optin") if isinstance(ab_row.get("optin"), dict) else {}
    deltas = ab_row.get("deltas") if isinstance(ab_row.get("deltas"), dict) else {}
    classification = str(ab_row.get("classification") or "")
    source_class = str(ab_row.get("source_completion_retry_class") or "")
    base_min_fill = _first_int(baseline.get("direct_label_harvest_min_fill_values"), 10)
    target_min_fill = _first_int(optin.get("direct_label_harvest_min_fill_values"), 4)
    features = {
        "source_tail_min_fill_candidate_count": float(
            _int(ab_row.get("source_tail_min_fill_candidate_count"))
        ),
        **_one_hot_source_class(source_class),
        "candidate_min_fill_gap": float(base_min_fill - target_min_fill),
    }
    outcomes = {
        "baseline_wall_time": _float(baseline.get("wall_time")),
        "optin_wall_time": _float(optin.get("wall_time")),
        "wall_time_delta": _float(deltas.get("wall_time")),
        "baseline_solving_time": _float(baseline.get("solving_time")),
        "optin_solving_time": _float(optin.get("solving_time")),
        "solving_time_delta": _float(deltas.get("solving_time")),
        "baseline_status_optimal": _status_optimal(baseline),
        "optin_status_optimal": _status_optimal(optin),
        "baseline_external_timeout": _bool_float(baseline.get("external_timeout")),
        "optin_external_timeout": _bool_float(optin.get("external_timeout")),
        "pricing_calls_delta": _float(deltas.get("pricing_calls")),
        "exact_pricing_calls_delta": _float(deltas.get("exact_pricing_calls")),
        "completion_retry_count_delta": _float(deltas.get("completion_retry_count")),
        "completion_retry_negative_journeys_delta": _float(
            deltas.get("completion_retry_negative_journeys")
        ),
        "completion_retry_selected_trips_delta": _float(
            deltas.get("completion_retry_selected_trips")
        ),
        "baseline_tail_minfill_candidate_count": float(
            _int(baseline.get("tail_minfill_candidate_count"))
        ),
        "optin_tail_minfill_candidate_count": float(_int(optin.get("tail_minfill_candidate_count"))),
        "baseline_tail_minfill_applied_count": float(
            _int(baseline.get("tail_minfill_applied_count"))
        ),
        "optin_tail_minfill_applied_count": float(_int(optin.get("tail_minfill_applied_count"))),
    }
    wall_reduced = outcomes["wall_time_delta"] < 0.0
    retry_reduced = outcomes["completion_retry_count_delta"] < 0.0
    exact_reduced = outcomes["exact_pricing_calls_delta"] < 0.0
    labels = {
        "y_strict_positive": 1.0 if classification == "strong_positive" else 0.0,
        "y_positive_speedup": 1.0 if classification == "positive_speedup" else 0.0,
        "y_hard_negative": 1.0 if classification == "hard_negative" else 0.0,
        "y_no_effect_guard": 1.0 if classification == "no_effect" else 0.0,
        "y_regression": 1.0 if classification == "regression" else 0.0,
        "y_target200_success": 1.0
        if classification in {"strong_positive", "positive_speedup"}
        and outcomes["optin_status_optimal"] > 0.0
        and outcomes["optin_wall_time"] <= 200.0
        else 0.0,
        "y_timeout_resolved": 1.0
        if str(baseline.get("status") or "") != "OPTIMAL"
        and str(optin.get("status") or "") == "OPTIMAL"
        else 0.0,
        "y_wall_time_reduced": 1.0 if wall_reduced else 0.0,
        "y_completion_retry_reduced": 1.0 if retry_reduced else 0.0,
        "y_exact_pricing_reduced": 1.0 if exact_reduced else 0.0,
        "y_trainable_positive": 1.0 if classification == "strong_positive" else 0.0,
        "y_trainable_negative": 1.0
        if classification in {"hard_negative", "regression", "no_effect"}
        else 0.0,
        "y_shadow_only": 1.0 if classification in {"positive_speedup", "weak_improvement"} else 0.0,
    }
    return {
        "schema_version": "journey_tail_minfill_training_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "instance": ab_row.get("instance"),
        "entry_id": ab_row.get("entry_id"),
        "action": "tail_minfill_optin",
        "base_min_fill": base_min_fill,
        "target_min_fill": target_min_fill,
        "classification": classification,
        "classification_reason": ab_row.get("classification_reason"),
        "source_completion_retry_class": source_class,
        "feature_schema": list(FEATURE_SCHEMA),
        "features": [features[name] for name in FEATURE_SCHEMA],
        "feature_values": features,
        "outcome_schema": list(OUTCOME_SCHEMA),
        "outcomes": [outcomes[name] for name in OUTCOME_SCHEMA],
        "outcome_values": outcomes,
        "label_schema": list(LABEL_SCHEMA),
        "labels": labels,
    }


def build_tail_minfill_training_rows(
    ab_results: Iterable[Path],
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    ab_rows = _load_ab_rows(ab_results)
    skipped_rows = [
        row for row in ab_rows if str(row.get("classification") or "") == "missing_result"
    ]
    training_rows = [
        _build_row(row)
        for row in ab_rows
        if str(row.get("classification") or "") != "missing_result"
    ]
    class_counts = Counter(str(row.get("classification") or "") for row in training_rows)
    label_positive_counts: Counter[str] = Counter()
    for row in training_rows:
        labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
        for name in LABEL_SCHEMA:
            if _float(labels.get(name)) > 0.0:
                label_positive_counts[name] += 1
    summary = {
        "schema_version": "journey_tail_minfill_training_rows_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "ab_result_inputs": [str(path) for path in ab_results],
        "feature_schema": list(FEATURE_SCHEMA),
        "outcome_schema": list(OUTCOME_SCHEMA),
        "label_schema": list(LABEL_SCHEMA),
        "training_row_count": len(training_rows),
        "skipped_missing_result_count": len(skipped_rows),
        "classification_counts": dict(sorted(class_counts.items())),
        "label_positive_counts": dict(sorted(label_positive_counts.items())),
        "strict_positive_count": int(label_positive_counts.get("y_strict_positive", 0)),
        "hard_negative_count": int(label_positive_counts.get("y_hard_negative", 0)),
        "regression_count": int(label_positive_counts.get("y_regression", 0)),
        "no_effect_guard_count": int(label_positive_counts.get("y_no_effect_guard", 0)),
        "shadow_only_count": int(label_positive_counts.get("y_shadow_only", 0)),
        "minimal_contrastive_ready": bool(
            label_positive_counts.get("y_strict_positive", 0) >= 1
            and label_positive_counts.get("y_trainable_negative", 0) >= 1
        ),
        "shadow_training_ready": bool(label_positive_counts.get("y_strict_positive", 0) >= 15),
        "optin_training_ready": bool(label_positive_counts.get("y_strict_positive", 0) >= 30),
        "training_rows": training_rows,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "tail_minfill_training_rows.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in training_rows),
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Journey Tail Min-Fill Training Rows",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把 low min-fill paired replay 的 A/B 审计结果转换成离线训练样本。"
        "该脚本只读既有审计文件，不运行 BPC / pricing / RMP，也不改变 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "journey_tail_minfill_training_rows = current",
        f"training_row_count = {summary['training_row_count']}",
        f"skipped_missing_result_count = {summary['skipped_missing_result_count']}",
        f"classification_counts = {summary['classification_counts']}",
        f"label_positive_counts = {summary['label_positive_counts']}",
        f"strict_positive_count = {summary['strict_positive_count']}",
        f"hard_negative_count = {summary['hard_negative_count']}",
        f"no_effect_guard_count = {summary['no_effect_guard_count']}",
        f"shadow_only_count = {summary['shadow_only_count']}",
        f"minimal_contrastive_ready = {summary['minimal_contrastive_ready']}",
        f"shadow_training_ready = {summary['shadow_training_ready']}",
        f"optin_training_ready = {summary['optin_training_ready']}",
        "production_ready = false",
        "runs_bpc_or_pricing = false",
        "certificate_effect = false",
        "official_bound_effect = false",
        "```",
        "",
        "## 解释",
        "",
        "strict positive 只包括把实例带进 200 秒 OPTIMAL 的样本；200 秒外的加速样本"
        "只作为 shadow-only，不进入 opt-in 正例。hard negative / regression / no-effect"
        "都可作为 guard negative，但当前正例数量不足，不能训练会影响求解行为的模型。",
        "",
        "## Rows",
        "",
        "```json",
        json.dumps(summary["training_rows"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ab-results", type=Path, nargs="+", required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    build_tail_minfill_training_rows(
        args.ab_results,
        output_dir=args.output_dir,
        report=args.report,
    )


if __name__ == "__main__":
    main()
