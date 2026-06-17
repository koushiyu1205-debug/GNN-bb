#!/usr/bin/env python3
"""Audit candidate score margins for missed high-ROI batch opportunities.

This script is offline/diagnostic-only. It consumes the existing opportunity
mining JSONL output, groups missed high-ROI records by family/context, and
reports whether the current blocker is a near-threshold score gap, a deep score
gap, a batch-threshold gap, or missing same-context contrast data. It does not
run BPC, pricing, RMP, workers, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DEFAULT_OPPORTUNITY_SUMMARY = Path(
    "BPC_future/results/gat_batch_impact_opportunity_mining_v13_sequential_badmode_20260616/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_batch_impact_score_margin_audit_v13_sequential_badmode_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_batch_impact_score_margin_audit_v13_sequential_badmode_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opportunity-summary", type=Path, default=DEFAULT_OPPORTUNITY_SUMMARY)
    parser.add_argument("--validation-opportunities", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--top-k", type=int, default=25)
    parser.add_argument("--near-miss-window", type=float, default=0.05)
    parser.add_argument("--deep-miss-margin", type=float, default=-0.20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_score_margins(
        opportunity_summary=Path(args.opportunity_summary),
        validation_opportunities=(
            Path(args.validation_opportunities) if args.validation_opportunities else None
        ),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        top_k=max(1, int(args.top_k)),
        near_miss_window=float(args.near_miss_window),
        deep_miss_margin=float(args.deep_miss_margin),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_score_margins(
    *,
    opportunity_summary: Path = DEFAULT_OPPORTUNITY_SUMMARY,
    validation_opportunities: Path | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    top_k: int = 25,
    near_miss_window: float = 0.05,
    deep_miss_margin: float = -0.20,
) -> dict[str, Any]:
    opportunity_summary = Path(opportunity_summary)
    opportunity = _read_json(opportunity_summary)
    _assert_opportunity_contract(opportunity)
    if validation_opportunities is None:
        validation_opportunities = Path(str(opportunity.get("validation_opportunities_path") or ""))
    validation_opportunities = Path(validation_opportunities)
    records = _read_jsonl(validation_opportunities)
    if not records:
        raise ValueError("validation_opportunities is empty")

    selected_threshold = dict(opportunity.get("selected_threshold") or {})
    candidate_threshold = float(selected_threshold.get("candidate_threshold") or 0.0)
    batch_threshold = float(selected_threshold.get("batch_threshold") or 0.0)

    context_groups = _context_groups(records)
    missed_records = [
        _enrich_missed_record(
            record,
            context_records=context_groups[_context_key(record)],
            near_miss_window=near_miss_window,
            deep_miss_margin=deep_miss_margin,
        )
        for record in records
        if bool(record.get("is_missed_high_roi_opportunity"))
    ]
    context_rows = _context_margin_rows(context_groups)
    output_dir.mkdir(parents=True, exist_ok=True)
    missed_path = output_dir / "missed_high_roi_score_margins.jsonl"
    context_path = output_dir / "context_score_margin_summary.jsonl"
    _write_jsonl(missed_path, sorted(missed_records, key=_missed_sort_key))
    _write_jsonl(context_path, sorted(context_rows, key=_context_sort_key))

    summary = {
        "schema_version": "gat_batch_impact_score_margin_audit_v1",
        "status": "gat_batch_impact_score_margins_audited",
        "opportunity_summary": str(opportunity_summary),
        "validation_opportunities": str(validation_opportunities),
        "output_dir": str(output_dir),
        "missed_high_roi_score_margins_path": str(missed_path),
        "context_score_margin_summary_path": str(context_path),
        "validation_record_count": len(records),
        "selected_threshold": {
            "threshold_scope": selected_threshold.get("threshold_scope"),
            "threshold_mode": selected_threshold.get("threshold_mode"),
            "batch_threshold": batch_threshold,
            "candidate_threshold": candidate_threshold,
        },
        "near_miss_window": float(near_miss_window),
        "deep_miss_margin": float(deep_miss_margin),
        "margin_summary": summarize_score_margins(
            records,
            missed_records,
            context_rows,
            candidate_threshold=candidate_threshold,
            batch_threshold=batch_threshold,
        ),
        "top_missed_by_roi": sorted(
            missed_records,
            key=lambda item: float(item.get("accepted_batch_roi_label") or 0.0),
            reverse=True,
        )[: int(top_k)],
        "top_missed_by_candidate_gap": sorted(
            missed_records,
            key=lambda item: float(item.get("max_safe_candidate_score_margin") or 0.0),
        )[: int(top_k)],
        "recommended_next_step": _recommended_next_step(missed_records, context_rows),
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
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def summarize_score_margins(
    records: list[dict[str, Any]],
    missed_records: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    *,
    candidate_threshold: float,
    batch_threshold: float,
) -> dict[str, Any]:
    high_roi = [record for record in records if bool(record.get("is_high_roi_opportunity"))]
    accepted_high_roi = [
        record for record in records if bool(record.get("is_accepted_high_roi_opportunity"))
    ]
    candidate_margins = [
        float(record.get("max_safe_candidate_score_margin") or 0.0)
        for record in missed_records
    ]
    raw_candidate_margins = [
        _raw_candidate_margin(record)
        for record in missed_records
    ]
    batch_margins = [
        float(record.get("batch_score_margin") or 0.0)
        for record in missed_records
    ]
    family = _family_summary(missed_records)
    task_counts = Counter(str(record.get("task_count") or 0) for record in missed_records)
    severity_counts = Counter(
        str(record.get("candidate_margin_bucket") or "unknown") for record in missed_records
    )
    raw_severity_counts = Counter(
        str(record.get("raw_candidate_margin_bucket") or "unknown") for record in missed_records
    )
    reason_counts = Counter(
        str(reason)
        for record in missed_records
        for reason in record.get("missed_reasons") or []
    )
    risk_adjusted_suppression = [
        record for record in missed_records if _is_risk_adjusted_suppressed_miss(record)
    ]
    raw_score_gap = [
        record for record in missed_records if _raw_candidate_margin(record) < 0.0
    ]
    batch_score_gap = [
        record for record in missed_records if float(record.get("batch_score_margin") or 0.0) < 0.0
    ]
    return {
        "records": len(records),
        "high_roi_opportunities": len(high_roi),
        "accepted_high_roi_opportunities": len(accepted_high_roi),
        "missed_high_roi_opportunities": len(missed_records),
        "accepted_high_roi_capture_rate": (
            len(accepted_high_roi) / float(len(high_roi)) if high_roi else 0.0
        ),
        "candidate_threshold": float(candidate_threshold),
        "batch_threshold": float(batch_threshold),
        "missed_candidate_score_margin_min": _min_or_none(candidate_margins),
        "missed_candidate_score_margin_median": _median_or_none(candidate_margins),
        "missed_candidate_score_margin_mean": _mean_or_none(candidate_margins),
        "missed_candidate_score_margin_max": _max_or_none(candidate_margins),
        "missed_raw_candidate_score_margin_min": _min_or_none(raw_candidate_margins),
        "missed_raw_candidate_score_margin_median": _median_or_none(raw_candidate_margins),
        "missed_raw_candidate_score_margin_mean": _mean_or_none(raw_candidate_margins),
        "missed_raw_candidate_score_margin_max": _max_or_none(raw_candidate_margins),
        "missed_batch_score_margin_min": _min_or_none(batch_margins),
        "missed_batch_score_margin_median": _median_or_none(batch_margins),
        "missed_batch_score_margin_mean": _mean_or_none(batch_margins),
        "missed_batch_score_margin_max": _max_or_none(batch_margins),
        "missed_reason_counts": dict(sorted(reason_counts.items())),
        "candidate_margin_bucket_counts": dict(sorted(severity_counts.items())),
        "raw_candidate_margin_bucket_counts": dict(sorted(raw_severity_counts.items())),
        "risk_adjusted_suppressed_miss_count": len(risk_adjusted_suppression),
        "raw_candidate_score_gap_miss_count": len(raw_score_gap),
        "batch_score_gap_miss_count": len(batch_score_gap),
        "task_count_counts": dict(sorted(task_counts.items())),
        "missed_without_same_context_contrast_count": sum(
            int(bool(record.get("needs_same_context_contrast"))) for record in missed_records
        ),
        "contexts_with_missed_high_roi": sum(
            int(row["missed_high_roi_opportunities"] > 0) for row in context_rows
        ),
        "contexts_with_missed_without_contrast": sum(
            int(row["missed_high_roi_opportunities"] > 0 and not row["has_low_roi_or_delay_contrast"])
            for row in context_rows
        ),
        "family": family,
    }


def _enrich_missed_record(
    record: dict[str, Any],
    *,
    context_records: list[dict[str, Any]],
    near_miss_window: float,
    deep_miss_margin: float,
) -> dict[str, Any]:
    enriched = dict(record)
    max_safe_margin = float(record.get("max_safe_candidate_score_margin") or 0.0)
    raw_margin = _raw_candidate_margin(record)
    batch_margin = float(record.get("batch_score_margin") or 0.0)
    low_roi_or_delay_records = [
        item for item in context_records if _is_low_roi_or_delay_contrast(item)
    ]
    high_roi_context_records = [
        item for item in context_records if bool(item.get("is_high_roi_opportunity"))
    ]
    bucket = _margin_bucket(
        max_safe_margin,
        near_miss_window=near_miss_window,
        deep_miss_margin=deep_miss_margin,
    )
    raw_bucket = _margin_bucket(
        raw_margin,
        near_miss_window=near_miss_window,
        deep_miss_margin=deep_miss_margin,
    )
    enriched.update(
        {
            "candidate_margin_bucket": bucket,
            "raw_candidate_margin_bucket": raw_bucket,
            "candidate_score_gap_to_threshold": max(0.0, -max_safe_margin),
            "raw_candidate_score_gap_to_threshold": max(0.0, -raw_margin),
            "risk_adjusted_suppressed_miss": _is_risk_adjusted_suppressed_miss(record),
            "batch_score_gap_to_threshold": max(0.0, -batch_margin),
            "same_context_record_count": len(context_records),
            "same_context_high_roi_count": len(high_roi_context_records),
            "same_context_low_roi_or_delay_count": len(low_roi_or_delay_records),
            "same_context_delay_labeled_record_count": sum(
                int(int(item.get("delay_candidate_label_count") or 0) > 0)
                for item in context_records
            ),
            "same_context_bad_mode_count": sum(
                int(bool(item.get("bad_mode_switch"))) for item in context_records
            ),
            "same_context_best_low_roi_or_delay_max_safe_score": _max_or_none(
                [float(item.get("max_safe_candidate_score") or 0.0) for item in low_roi_or_delay_records]
            ),
            "same_context_best_low_roi_or_delay_margin": _max_or_none(
                [
                    float(item.get("max_safe_candidate_score_margin") or 0.0)
                    for item in low_roi_or_delay_records
                ]
            ),
            "has_same_context_low_roi_or_delay_contrast": bool(low_roi_or_delay_records),
            "needs_same_context_contrast": not bool(low_roi_or_delay_records),
        }
    )
    return enriched


def _context_margin_rows(
    context_groups: dict[tuple[str, str], list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (family, context_hash), group in context_groups.items():
        high_roi = [item for item in group if bool(item.get("is_high_roi_opportunity"))]
        missed = [item for item in group if bool(item.get("is_missed_high_roi_opportunity"))]
        accepted_high_roi = [
            item for item in group if bool(item.get("is_accepted_high_roi_opportunity"))
        ]
        low_roi_or_delay = [item for item in group if _is_low_roi_or_delay_contrast(item)]
        max_safe_margins = [
            float(item.get("max_safe_candidate_score_margin") or 0.0) for item in group
        ]
        missed_safe_margins = [
            float(item.get("max_safe_candidate_score_margin") or 0.0) for item in missed
        ]
        missed_raw_margins = [_raw_candidate_margin(item) for item in missed]
        rows.append(
            {
                "family": family,
                "context_hash": context_hash,
                "records": len(group),
                "task_counts": sorted({int(item.get("task_count") or 0) for item in group}),
                "instances": sorted({str(item.get("instance") or "") for item in group}),
                "high_roi_opportunities": len(high_roi),
                "accepted_high_roi_opportunities": len(accepted_high_roi),
                "missed_high_roi_opportunities": len(missed),
                "low_roi_or_delay_contrast_records": len(low_roi_or_delay),
                "has_low_roi_or_delay_contrast": bool(low_roi_or_delay),
                "max_safe_candidate_score_margin": _max_or_none(max_safe_margins),
                "missed_safe_candidate_score_margin_min": _min_or_none(missed_safe_margins),
                "missed_safe_candidate_score_margin_median": _median_or_none(missed_safe_margins),
                "missed_safe_candidate_score_margin_max": _max_or_none(missed_safe_margins),
                "missed_raw_candidate_score_margin_min": _min_or_none(missed_raw_margins),
                "missed_raw_candidate_score_margin_median": _median_or_none(missed_raw_margins),
                "missed_raw_candidate_score_margin_max": _max_or_none(missed_raw_margins),
                "risk_adjusted_suppressed_miss_count": sum(
                    int(_is_risk_adjusted_suppressed_miss(item)) for item in missed
                ),
                "max_accepted_batch_roi_label": _max_or_none(
                    [float(item.get("accepted_batch_roi_label") or 0.0) for item in group]
                ),
                "missed_accepted_batch_roi_label_max": _max_or_none(
                    [float(item.get("accepted_batch_roi_label") or 0.0) for item in missed]
                ),
                "needs_same_context_contrast": bool(missed and not low_roi_or_delay),
            }
        )
    return rows


def _family_summary(missed_records: list[dict[str, Any]]) -> dict[str, Any]:
    families: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in missed_records:
        families[str(record.get("family") or "unknown")].append(record)
    summary: dict[str, Any] = {}
    for family, items in families.items():
        margins = [float(item.get("max_safe_candidate_score_margin") or 0.0) for item in items]
        raw_margins = [_raw_candidate_margin(item) for item in items]
        summary[family] = {
            "missed_high_roi_opportunities": len(items),
            "task_count_counts": dict(
                sorted(Counter(str(item.get("task_count") or 0) for item in items).items())
            ),
            "candidate_margin_bucket_counts": dict(
                sorted(
                    Counter(str(item.get("candidate_margin_bucket") or "unknown") for item in items).items()
                )
            ),
            "raw_candidate_margin_bucket_counts": dict(
                sorted(
                    Counter(str(item.get("raw_candidate_margin_bucket") or "unknown") for item in items).items()
                )
            ),
            "missed_candidate_score_margin_mean": _mean_or_none(margins),
            "missed_candidate_score_margin_min": _min_or_none(margins),
            "missed_raw_candidate_score_margin_mean": _mean_or_none(raw_margins),
            "missed_raw_candidate_score_margin_min": _min_or_none(raw_margins),
            "risk_adjusted_suppressed_miss_count": sum(
                int(_is_risk_adjusted_suppressed_miss(item)) for item in items
            ),
            "missed_without_same_context_contrast_count": sum(
                int(bool(item.get("needs_same_context_contrast"))) for item in items
            ),
            "contexts": sorted({str(item.get("context_hash") or "") for item in items}),
        }
    return dict(sorted(summary.items()))


def _recommended_next_step(
    missed_records: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if not missed_records:
        return {"primary": "no_missed_high_roi_opportunities_under_selected_threshold"}
    missed_without_contrast = [
        item for item in missed_records if bool(item.get("needs_same_context_contrast"))
    ]
    bucket_counts = Counter(str(item.get("candidate_margin_bucket") or "unknown") for item in missed_records)
    raw_bucket_counts = Counter(str(item.get("raw_candidate_margin_bucket") or "unknown") for item in missed_records)
    risk_suppressed_count = sum(int(_is_risk_adjusted_suppressed_miss(item)) for item in missed_records)
    family_counts = Counter(str(item.get("family") or "unknown") for item in missed_records)
    if risk_suppressed_count > len(missed_records) / 2.0:
        primary = "calibrate_delay_risk_penalty_or_two_stage_rescue_window"
    elif missed_without_contrast:
        primary = "collect_same_context_positive_negative_pairs_for_missed_high_roi_contexts"
    elif bucket_counts.get("deep_candidate_score_gap", 0):
        primary = "collect_high_roi_candidate_margin_pairs_for_deep_score_gap_contexts"
    elif bucket_counts.get("near_candidate_threshold", 0):
        primary = "audit_threshold_frontier_for_near_miss_high_roi_contexts"
    else:
        primary = "inspect_candidate_feature_signal_for_missed_high_roi_contexts"
    return {
        "primary": primary,
        "missed_family_counts": dict(sorted(family_counts.items())),
        "candidate_margin_bucket_counts": dict(sorted(bucket_counts.items())),
        "raw_candidate_margin_bucket_counts": dict(sorted(raw_bucket_counts.items())),
        "risk_adjusted_suppressed_miss_count": int(risk_suppressed_count),
        "missed_without_same_context_contrast": len(missed_without_contrast),
        "contexts_needing_contrast": [
            {
                "family": row["family"],
                "context_hash": row["context_hash"],
                "task_counts": row["task_counts"],
                "missed_high_roi_opportunities": row["missed_high_roi_opportunities"],
            }
            for row in context_rows
            if bool(row.get("needs_same_context_contrast"))
        ],
    }


def _context_groups(records: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[_context_key(record)].append(record)
    return grouped


def _context_key(record: dict[str, Any]) -> tuple[str, str]:
    return (str(record.get("family") or "unknown"), str(record.get("context_hash") or ""))


def _is_low_roi_or_delay_contrast(record: dict[str, Any]) -> bool:
    return (
        not bool(record.get("is_high_roi_opportunity"))
        or int(record.get("delay_candidate_label_count") or 0) > 0
        or bool(record.get("bad_mode_switch"))
    )


def _raw_candidate_margin(record: dict[str, Any]) -> float:
    if "max_raw_candidate_score_margin" in record:
        return float(record.get("max_raw_candidate_score_margin") or 0.0)
    return float(record.get("max_candidate_score_margin") or record.get("max_safe_candidate_score_margin") or 0.0)


def _is_risk_adjusted_suppressed_miss(record: dict[str, Any]) -> bool:
    return (
        _raw_candidate_margin(record) >= 0.0
        and float(record.get("max_safe_candidate_score_margin") or 0.0) < 0.0
        and (
            "candidate_risk_adjusted_below_threshold" in set(record.get("missed_reasons") or [])
            or int(record.get("candidate_risk_adjusted_suppressed_count") or 0) > 0
        )
    )


def _margin_bucket(
    margin: float,
    *,
    near_miss_window: float,
    deep_miss_margin: float,
) -> str:
    if float(margin) >= -float(near_miss_window):
        return "near_candidate_threshold"
    if float(margin) <= float(deep_miss_margin):
        return "deep_candidate_score_gap"
    return "moderate_candidate_score_gap"


def _missed_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        str(item.get("family") or ""),
        int(item.get("task_count") or 0),
        str(item.get("context_hash") or ""),
        float(item.get("max_safe_candidate_score_margin") or 0.0),
        -float(item.get("accepted_batch_roi_label") or 0.0),
    )


def _context_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -int(item.get("missed_high_roi_opportunities") or 0),
        bool(item.get("has_low_roi_or_delay_contrast")),
        float(item.get("missed_safe_candidate_score_margin_min") or 0.0),
        str(item.get("family") or ""),
        str(item.get("context_hash") or ""),
    )


def _assert_opportunity_contract(summary: dict[str, Any]) -> None:
    if summary.get("schema_version") != "gat_batch_impact_opportunity_mining_v1":
        raise ValueError("opportunity summary schema mismatch")
    if bool(summary.get("production_ready")):
        raise ValueError("opportunity summary must not be production_ready")
    if bool(summary.get("runs_bpc_or_pricing")):
        raise ValueError("score margin audit input must not run BPC or pricing")
    if bool(summary.get("selector_can_certificate")):
        raise ValueError("opportunity summary must not be certificate-capable")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    margin = summary["margin_summary"]
    recommended = summary["recommended_next_step"]
    threshold = summary["selected_threshold"]
    lines = [
        "# GAT Batch Impact Score Margin Audit 报告",
        "",
        "日期：2026-06-16",
        "",
        "## 结论",
        "",
        "本报告复用 opportunity mining 的 validation records，审计 missed high-ROI batch",
        "距离当前 candidate / batch threshold 还差多少，以及是否缺同 context 对照样本。",
        "它只做离线诊断，不运行 BPC、pricing、RMP、worker 或 certificate。",
        "",
        "```text",
        f"validation_record_count = {summary['validation_record_count']}",
        f"candidate_threshold = {threshold.get('candidate_threshold')}",
        f"batch_threshold = {threshold.get('batch_threshold')}",
        f"high_roi_opportunities = {margin['high_roi_opportunities']}",
        f"accepted_high_roi_opportunities = {margin['accepted_high_roi_opportunities']}",
        f"missed_high_roi_opportunities = {margin['missed_high_roi_opportunities']}",
        f"missed_candidate_score_margin_mean = {margin['missed_candidate_score_margin_mean']}",
        f"missed_candidate_score_margin_min = {margin['missed_candidate_score_margin_min']}",
        f"missed_raw_candidate_score_margin_mean = {margin['missed_raw_candidate_score_margin_mean']}",
        f"missed_raw_candidate_score_margin_min = {margin['missed_raw_candidate_score_margin_min']}",
        f"risk_adjusted_suppressed_miss_count = {margin['risk_adjusted_suppressed_miss_count']}",
        f"missed_without_same_context_contrast_count = {margin['missed_without_same_context_contrast_count']}",
        f"recommended_primary = {recommended.get('primary')}",
        "production_ready = false",
        "selector_can_certificate = false",
        "```",
        "",
        "## Candidate Margin Buckets",
        "",
        "```json",
        json.dumps(
            margin["candidate_margin_bucket_counts"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Raw Candidate Margin Buckets",
        "",
        "```json",
        json.dumps(
            margin["raw_candidate_margin_bucket_counts"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Family Summary",
        "",
        "```json",
        json.dumps(margin["family"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Recommended Next Step",
        "",
        "```json",
        json.dumps(recommended, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Exactness Boundary",
        "",
        "- `diagnostic_only=true`；",
        "- `runs_bpc_or_pricing=false`；",
        "- `selector_is_pricing_oracle=false`；",
        "- `selector_can_certificate=false`；",
        "- `gate_can_permanently_discard_negative_columns=false`；",
        "- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _mean_or_none(values: list[float]) -> float | None:
    return float(mean(values)) if values else None


def _median_or_none(values: list[float]) -> float | None:
    return float(median(values)) if values else None


def _min_or_none(values: list[float]) -> float | None:
    return float(min(values)) if values else None


def _max_or_none(values: list[float]) -> float | None:
    return float(max(values)) if values else None


if __name__ == "__main__":
    raise SystemExit(main())
