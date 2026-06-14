#!/usr/bin/env python3
"""Audit online feature gaps behind CBF delay-queue false positives.

The input is the H=2 trajectory dataset plus the false-positive catalog from
``audit_cbf_delay_queue_false_positive_catalog.py``.  The script asks two
offline questions:

1. Do false-positive rows look closer to safe rows than to other unsafe rows in
   the currently available online feature space?
2. Is there a simple one-feature conservative delay guard that covers the
   false positives while retaining a useful fraction of safe rows?

It is diagnostic-only: no BPC/pricing/RMP run is triggered, no columns are
generated, and no certificate or official lower bound is produced.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
from typing import Any

from BPC_future.scripts.audit_cbf_delay_queue_false_positive_catalog import (
    DEFAULT_OUTPUT_DIR as DEFAULT_FP_OUTPUT_DIR,
)
from BPC_future.scripts.audit_cbf_trajectory_gate_policy import (
    _label_counts,
    _trajectory_labels,
    trajectory_gate_feature_names,
)
from BPC_future.scripts.train_cbf_gate import (
    _features,
    _is_no_effect_row,
    load_rows,
)


DEFAULT_DATASET = Path(
    "BPC_future/results/cbf_trajectory_gate_dataset_global_all_h2_20260614/"
    "cbf_trajectory_gate_transitions.jsonl"
)
DEFAULT_FALSE_POSITIVES = (
    DEFAULT_FP_OUTPUT_DIR.parent
    / "cbf_delay_queue_false_positive_catalog_global_all_h2_20260614"
    / "false_positive_records.jsonl"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/cbf_delay_queue_feature_gap_audit_global_all_h2_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_delay_queue_feature_gap_audit_global_all_h2_zh.md"
)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (TypeError, ValueError):
        return default


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            rows.append(json.loads(raw))
    return rows


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = max(0.0, min(1.0, float(q))) * (len(ordered) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return ordered[lo]
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def _standardize_matrix(xs: list[list[float]]) -> list[list[float]]:
    if not xs:
        return []
    width = len(xs[0])
    means: list[float] = []
    stds: list[float] = []
    for idx in range(width):
        vals = [row[idx] for row in xs]
        mean = sum(vals) / float(len(vals))
        var = sum((value - mean) ** 2 for value in vals) / float(len(vals))
        std = math.sqrt(var)
        means.append(mean)
        stds.append(std if std > 1.0e-12 else 1.0)
    return [
        [(value - means[idx]) / stds[idx] for idx, value in enumerate(row)]
        for row in xs
    ]


def _distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _nearest_profile(
    rows: list[dict[str, Any]],
    *,
    feature_names: list[str],
    false_positive_indices: set[int],
) -> dict[str, Any]:
    labels = _trajectory_labels(rows)
    xs = _standardize_matrix([_features(row, feature_names) for row in rows])
    safe_indices = [idx for idx, label in enumerate(labels) if int(label) == 1]
    unsafe_non_fp_indices = [
        idx
        for idx, label in enumerate(labels)
        if int(label) == 0 and idx not in false_positive_indices
    ]
    profiles: list[dict[str, Any]] = []
    safe_like_count = 0
    for idx in sorted(false_positive_indices):
        if idx < 0 or idx >= len(xs):
            continue
        nearest_safe = min(
            (_distance(xs[idx], xs[safe_idx]) for safe_idx in safe_indices),
            default=None,
        )
        nearest_unsafe = min(
            (
                _distance(xs[idx], xs[unsafe_idx])
                for unsafe_idx in unsafe_non_fp_indices
                if unsafe_idx != idx
            ),
            default=None,
        )
        safe_like = bool(
            nearest_safe is not None
            and (nearest_unsafe is None or nearest_safe <= nearest_unsafe)
        )
        if safe_like:
            safe_like_count += 1
        profiles.append(
            {
                "row_index": idx,
                "instance": str(rows[idx].get("instance", "")),
                "family": _family_from_source(rows[idx]),
                "nearest_safe_distance": nearest_safe,
                "nearest_unsafe_non_fp_distance": nearest_unsafe,
                "safe_like_in_online_feature_space": safe_like,
            }
        )
    return {
        "false_positive_neighbor_profiles": profiles,
        "safe_like_false_positive_count": safe_like_count,
        "safe_like_false_positive_ratio": (
            None
            if not profiles
            else safe_like_count / float(len(profiles))
        ),
    }


def _family_from_source(row: dict[str, Any]) -> str:
    text = f"{row.get('instance', '')} {row.get('source_file', '')}".lower()
    for family in ("greedy-anchor", "random-wave", "sector-wave"):
        if family in text:
            return family
    if "very_small" in text:
        return "very_small"
    if "tasks10" in text:
        return "moon_trek_tasks10"
    if "tasks20" in text:
        return "moon_trek_tasks20"
    return "unknown"


def _single_feature_guard_candidates(
    rows: list[dict[str, Any]],
    *,
    feature_names: list[str],
    false_positive_indices: set[int],
    min_safe_retention: float,
) -> list[dict[str, Any]]:
    labels = _trajectory_labels(rows)
    safe_indices = [idx for idx, label in enumerate(labels) if int(label) == 1]
    fp_indices = sorted(idx for idx in false_positive_indices if 0 <= idx < len(rows))
    candidates: list[dict[str, Any]] = []
    if not fp_indices or not safe_indices:
        return candidates
    for feature in feature_names:
        values = [_safe_float(row.get(feature)) for row in rows]
        fp_values = [values[idx] for idx in fp_indices]
        safe_values = [values[idx] for idx in safe_indices]
        for direction in ("delay_high", "delay_low"):
            if direction == "delay_high":
                threshold = min(fp_values)
                fp_covered = sum(1 for value in fp_values if value >= threshold)
                safe_delayed = sum(1 for value in safe_values if value >= threshold)
            else:
                threshold = max(fp_values)
                fp_covered = sum(1 for value in fp_values if value <= threshold)
                safe_delayed = sum(1 for value in safe_values if value <= threshold)
            safe_retained = len(safe_values) - safe_delayed
            safe_retention = safe_retained / float(len(safe_values))
            fp_coverage = fp_covered / float(len(fp_values))
            if fp_coverage >= 1.0 and safe_retention >= float(min_safe_retention):
                candidates.append(
                    {
                        "feature": feature,
                        "direction": direction,
                        "threshold": threshold,
                        "false_positive_coverage": fp_coverage,
                        "safe_retention": safe_retention,
                        "safe_retained_count": safe_retained,
                        "safe_delayed_count": safe_delayed,
                        "false_positive_count": len(fp_values),
                    }
                )
    candidates.sort(
        key=lambda item: (
            float(item["safe_retention"]),
            int(item["safe_retained_count"]),
            -abs(float(item["threshold"])),
        ),
        reverse=True,
    )
    return candidates


def _feature_overlap_summary(
    rows: list[dict[str, Any]],
    *,
    feature_names: list[str],
    false_positive_indices: set[int],
) -> list[dict[str, Any]]:
    labels = _trajectory_labels(rows)
    safe_rows = [row for row, label in zip(rows, labels) if int(label) == 1]
    fp_rows = [rows[idx] for idx in sorted(false_positive_indices) if 0 <= idx < len(rows)]
    summaries: list[dict[str, Any]] = []
    for feature in feature_names:
        safe_values = [_safe_float(row.get(feature)) for row in safe_rows]
        fp_values = [_safe_float(row.get(feature)) for row in fp_rows]
        if not safe_values or not fp_values:
            continue
        safe_min = min(safe_values)
        safe_max = max(safe_values)
        fp_inside_safe_range = sum(1 for value in fp_values if safe_min <= value <= safe_max)
        summaries.append(
            {
                "feature": feature,
                "safe_min": safe_min,
                "safe_q10": _quantile(safe_values, 0.1),
                "safe_median": _quantile(safe_values, 0.5),
                "safe_q90": _quantile(safe_values, 0.9),
                "safe_max": safe_max,
                "false_positive_min": min(fp_values),
                "false_positive_median": _quantile(fp_values, 0.5),
                "false_positive_max": max(fp_values),
                "false_positive_inside_safe_range_count": fp_inside_safe_range,
                "false_positive_count": len(fp_values),
            }
        )
    summaries.sort(
        key=lambda item: (
            int(item["false_positive_inside_safe_range_count"]),
            str(item["feature"]),
        )
    )
    return summaries


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Delay-Queue Feature Gap 审计报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "分析 delay scheduler 的 false-positive 是否来自在线特征缺口。",
        "本脚本只读 H=2 dataset 和 false-positive catalog，不运行 BPC / pricing / RMP，",
        "不生成列，不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_delay_queue_feature_gap_audit = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"unique_false_positive_row_count = {summary['unique_false_positive_row_count']}",
        f"safe_like_false_positive_ratio = {summary['safe_like_false_positive_ratio']}",
        f"single_feature_guard_available = {str(summary['single_feature_guard_available']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 摘要",
        "",
        "```json",
        json.dumps(
            {
                "row_count": summary["row_count"],
                "label_counts": summary["label_counts"],
                "unique_false_positive_row_count": summary["unique_false_positive_row_count"],
                "safe_like_false_positive_count": summary["safe_like_false_positive_count"],
                "safe_like_false_positive_ratio": summary["safe_like_false_positive_ratio"],
                "single_feature_guard_available": summary["single_feature_guard_available"],
                "top_single_feature_guards": summary["top_single_feature_guards"],
                "false_positive_by_family": summary["false_positive_by_family"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 结论",
        "",
        "- 如果 FP 在在线特征空间里更接近 safe 样本，说明当前特征不足以稳定区分 H=2 风险；",
        "- 单特征 guard 只可作为补采/诊断线索，不能直接上线；",
        "- 当前建议仍是 affected bucket force-delay / abstain，并补采 false-positive 邻域。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def audit_feature_gap(
    dataset: Path,
    false_positive_records: Path,
    *,
    output_dir: Path,
    report: Path,
    min_safe_retention: float = 0.5,
) -> dict[str, Any]:
    rows = load_rows(dataset)
    fp_records = _read_jsonl(false_positive_records)
    no_effect_count = sum(1 for row in rows if _is_no_effect_row(row))
    fp_indices = {
        int(record["row_index"])
        for record in fp_records
        if "row_index" in record
    }
    feature_names = trajectory_gate_feature_names(rows)
    nearest = _nearest_profile(
        rows,
        feature_names=feature_names,
        false_positive_indices=fp_indices,
    )
    guard_candidates = _single_feature_guard_candidates(
        rows,
        feature_names=feature_names,
        false_positive_indices=fp_indices,
        min_safe_retention=min_safe_retention,
    )
    overlap = _feature_overlap_summary(
        rows,
        feature_names=feature_names,
        false_positive_indices=fp_indices,
    )
    fp_by_family = Counter(
        f"{record.get('task_count')}|{record.get('family')}"
        for record in fp_records
    )
    checks = {
        "all_rows_no_certificate_effect": bool(rows and no_effect_count == len(rows)),
        "false_positive_records_no_official_effect": all(
            record.get("official_bound_effect") is False for record in fp_records
        ),
        "uses_online_features_only": all(
            not name.startswith(("state_next_", "delta_", "horizon_", "next_"))
            and not name.startswith("label_")
            for name in feature_names
        ),
        "has_false_positive_catalog": bool(fp_records),
    }
    summary = {
        "schema_version": "cbf_delay_queue_feature_gap_audit_v1",
        "status": "cbf_delay_queue_feature_gap_audited",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "dataset": str(dataset),
        "false_positive_records": str(false_positive_records),
        "row_count": len(rows),
        "label_counts": _label_counts(rows),
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "false_positive_record_count": len(fp_records),
        "unique_false_positive_row_count": len(fp_indices),
        "false_positive_by_family": dict(sorted(fp_by_family.items())),
        "safe_like_false_positive_count": nearest["safe_like_false_positive_count"],
        "safe_like_false_positive_ratio": nearest["safe_like_false_positive_ratio"],
        "false_positive_neighbor_profiles": nearest["false_positive_neighbor_profiles"],
        "single_feature_guard_available": bool(guard_candidates),
        "min_safe_retention": float(min_safe_retention),
        "top_single_feature_guards": guard_candidates[:10],
        "feature_overlap_summary": overlap,
        "recommended_action": "force_delay_affected_buckets_and_collect_fp_neighborhood",
        "production_ready": False,
        "official_bound_effect": False,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "goal_complete": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--false-positive-records", type=Path, default=DEFAULT_FALSE_POSITIVES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-safe-retention", type=float, default=0.5)
    args = parser.parse_args(argv)
    summary = audit_feature_gap(
        args.dataset,
        args.false_positive_records,
        output_dir=args.output_dir,
        report=args.report,
        min_safe_retention=args.min_safe_retention,
    )
    print(
        json.dumps(
            {
                "summary": str(args.output_dir / "summary.json"),
                "report": str(args.report),
                "all_checks_pass": summary["all_checks_pass"],
                "unique_false_positive_row_count": summary["unique_false_positive_row_count"],
                "safe_like_false_positive_ratio": summary["safe_like_false_positive_ratio"],
                "single_feature_guard_available": summary["single_feature_guard_available"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
