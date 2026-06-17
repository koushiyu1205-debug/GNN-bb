#!/usr/bin/env python3
"""Combine score-margin and embedding audits for missed high-ROI batches.

This script is offline/diagnostic-only. It reads existing audit summaries and
classifies whether missed high-ROI opportunities are mostly threshold-border
cases, candidate-head score gaps, embedding-space structural gaps, or mixed
head/embedding gaps. It does not run BPC, pricing, RMP, workers, or certificate
logic.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any


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
DEFAULT_WORKER_ROWS_SUMMARY = Path(
    "BPC_future/results/"
    "gat_multibatch_worker_batch_impact_rows_v15_first_tranche_top3_20260616/"
    "summary.json"
)
DEFAULT_NEXT_TRAINING_SUMMARY = Path(
    "BPC_future/results/"
    "gat_batch_impact_training_v16_first_tranche_top3_ab_roi_20260616/"
    "metrics.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "gat_batch_impact_missed_high_roi_diagnosis_v15_exact_safe_hits_batch8_ab_roi_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage3_v43_v15_missed_high_roi_diagnosis_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score-margin-summary", type=Path, default=DEFAULT_SCORE_MARGIN_SUMMARY)
    parser.add_argument("--embedding-summary", type=Path, default=DEFAULT_EMBEDDING_SUMMARY)
    parser.add_argument("--worker-rows-summary", type=Path, default=DEFAULT_WORKER_ROWS_SUMMARY)
    parser.add_argument("--next-training-summary", type=Path, default=DEFAULT_NEXT_TRAINING_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--near-threshold-bucket",
        default="near_candidate_threshold",
        help="Margin bucket treated as a threshold-border miss.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_missed_high_roi_diagnosis(
        score_margin_summary=Path(args.score_margin_summary),
        embedding_summary=Path(args.embedding_summary),
        worker_rows_summary=Path(args.worker_rows_summary),
        next_training_summary=Path(args.next_training_summary),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        near_threshold_bucket=str(args.near_threshold_bucket),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_missed_high_roi_diagnosis(
    *,
    score_margin_summary: Path = DEFAULT_SCORE_MARGIN_SUMMARY,
    embedding_summary: Path = DEFAULT_EMBEDDING_SUMMARY,
    worker_rows_summary: Path | None = DEFAULT_WORKER_ROWS_SUMMARY,
    next_training_summary: Path | None = DEFAULT_NEXT_TRAINING_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    near_threshold_bucket: str = "near_candidate_threshold",
) -> dict[str, Any]:
    score = _read_json(score_margin_summary)
    embedding = _read_json(embedding_summary)
    worker = _read_optional_json(worker_rows_summary)
    next_training = _read_optional_json(next_training_summary)
    _assert_contracts(score, embedding, worker, next_training)

    margin_summary = dict(score.get("margin_summary") or {})
    embedding_summary_data = dict(embedding.get("embedding_summary") or {})
    family_rows = _family_diagnosis_rows(
        margin_summary,
        embedding_summary_data,
        near_threshold_bucket=near_threshold_bucket,
    )
    decision = _decision_summary(
        margin_summary,
        embedding_summary_data,
        family_rows,
        worker,
        next_training,
        near_threshold_bucket=near_threshold_bucket,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    family_path = output_dir / "family_missed_high_roi_diagnosis.jsonl"
    _write_jsonl(family_path, family_rows)

    summary = {
        "schema_version": "gat_batch_impact_missed_high_roi_diagnosis_v1",
        "status": "gat_batch_impact_missed_high_roi_diagnosed",
        "score_margin_summary": str(score_margin_summary),
        "embedding_summary": str(embedding_summary),
        "worker_rows_summary": str(worker_rows_summary) if worker_rows_summary else None,
        "next_training_summary": str(next_training_summary) if next_training_summary else None,
        "output_dir": str(output_dir),
        "family_diagnosis_path": str(family_path),
        "decision_summary": decision,
        "family_diagnosis": family_rows,
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
    _write_report(report, summary)
    return summary


def _family_diagnosis_rows(
    margin_summary: dict[str, Any],
    embedding_summary: dict[str, Any],
    *,
    near_threshold_bucket: str,
) -> list[dict[str, Any]]:
    margin_family = dict(margin_summary.get("family") or {})
    embedding_family = dict(embedding_summary.get("family") or {})
    family_names = sorted(set(margin_family).union(embedding_family))
    rows: list[dict[str, Any]] = []
    for family in family_names:
        margin = dict(margin_family.get(family) or {})
        embedding = dict(embedding_family.get(family) or {})
        missed = int(margin.get("missed_high_roi_opportunities") or embedding.get("missed_high_roi_opportunities") or 0)
        bucket_counts = _counter_dict(margin.get("candidate_margin_bucket_counts"))
        near_count = int(bucket_counts.get(near_threshold_bucket, 0))
        deep_count = int(bucket_counts.get("deep_candidate_score_gap", 0))
        moderate_count = int(bucket_counts.get("moderate_candidate_score_gap", 0))
        negative_closer = int(embedding.get("missed_nearest_negative_closer_count") or 0)
        row = {
            "family": str(family),
            "missed_high_roi_opportunities": missed,
            "near_threshold_miss_count": near_count,
            "non_near_threshold_miss_count": max(0, missed - near_count),
            "deep_candidate_score_gap_count": deep_count,
            "moderate_candidate_score_gap_count": moderate_count,
            "missed_without_same_context_contrast_count": int(
                margin.get("missed_without_same_context_contrast_count") or 0
            ),
            "missed_nearest_negative_closer_count": negative_closer,
            "missed_nearest_negative_closer_rate": (
                negative_closer / float(missed) if missed else 0.0
            ),
            "candidate_margin_bucket_counts": dict(sorted(bucket_counts.items())),
            "task_count_counts": dict(sorted(_counter_dict(margin.get("task_count_counts")).items())),
            "classification": _family_classification(
                missed=missed,
                near_count=near_count,
                negative_closer=negative_closer,
            ),
        }
        rows.append(row)
    return rows


def _decision_summary(
    margin_summary: dict[str, Any],
    embedding_summary: dict[str, Any],
    family_rows: list[dict[str, Any]],
    worker_summary: dict[str, Any] | None,
    next_training: dict[str, Any] | None,
    *,
    near_threshold_bucket: str,
) -> dict[str, Any]:
    missed = int(margin_summary.get("missed_high_roi_opportunities") or 0)
    bucket_counts = _counter_dict(margin_summary.get("candidate_margin_bucket_counts"))
    near_count = int(bucket_counts.get(near_threshold_bucket, 0))
    negative_closer = int(embedding_summary.get("missed_nearest_negative_closer_count") or 0)
    missed_knn_fraction = _float_or_none(embedding_summary.get("missed_knn_positive_fraction_mean"))
    accepted_knn_fraction = _float_or_none(
        embedding_summary.get("accepted_high_roi_knn_positive_fraction_mean")
    )
    max_margin = _float_or_none(margin_summary.get("missed_candidate_score_margin_max"))
    candidate_score_gap_primary = bool(missed > 0 and near_count == 0 and (max_margin is None or max_margin < 0.0))
    embedding_structural_gap = bool(
        missed > 0
        and negative_closer > 0
        and (
            missed_knn_fraction is None
            or accepted_knn_fraction is None
            or missed_knn_fraction < accepted_knn_fraction
        )
    )
    if candidate_score_gap_primary and embedding_structural_gap:
        primary = "candidate_head_score_gap_plus_embedding_structural_gap"
    elif near_count > 0 and near_count >= max(1, missed // 2):
        primary = "threshold_borderline_missed_high_roi"
    elif candidate_score_gap_primary:
        primary = "candidate_head_score_gap"
    elif embedding_structural_gap:
        primary = "embedding_structural_gap"
    else:
        primary = "mixed_or_insufficient_evidence"

    worker = _worker_feedback(worker_summary)
    next_training_gate = _next_training_gate(next_training)
    return {
        "primary": primary,
        "missed_high_roi_opportunities": missed,
        "accepted_high_roi_opportunities": int(margin_summary.get("accepted_high_roi_opportunities") or 0),
        "candidate_threshold": _float_or_none(margin_summary.get("candidate_threshold")),
        "near_threshold_miss_count": near_count,
        "non_near_threshold_miss_count": max(0, missed - near_count),
        "candidate_margin_bucket_counts": dict(sorted(bucket_counts.items())),
        "missed_candidate_score_margin_mean": _float_or_none(
            margin_summary.get("missed_candidate_score_margin_mean")
        ),
        "missed_candidate_score_margin_min": _float_or_none(
            margin_summary.get("missed_candidate_score_margin_min")
        ),
        "missed_candidate_score_margin_max": max_margin,
        "missed_without_same_context_contrast_count": int(
            margin_summary.get("missed_without_same_context_contrast_count") or 0
        ),
        "missed_nearest_negative_closer_count": negative_closer,
        "missed_nearest_negative_closer_rate": negative_closer / float(missed) if missed else 0.0,
        "missed_knn_positive_fraction_mean": missed_knn_fraction,
        "accepted_high_roi_knn_positive_fraction_mean": accepted_knn_fraction,
        "family_classification_counts": dict(
            sorted(Counter(str(row["classification"]) for row in family_rows).items())
        ),
        "worker_feedback": worker,
        "next_training_gate": next_training_gate,
        "stage4_candidate_ready": False,
        "recommended_next_step": _recommended_next_step(
            primary=primary,
            worker_feedback=worker,
            next_training_gate=next_training_gate,
        ),
    }


def _family_classification(*, missed: int, near_count: int, negative_closer: int) -> str:
    if missed <= 0:
        return "no_missed_high_roi"
    if near_count > 0 and near_count >= missed:
        return "threshold_borderline"
    if negative_closer >= missed:
        return "embedding_structural_gap"
    if negative_closer > 0:
        return "mixed_candidate_head_embedding_gap"
    return "candidate_head_score_gap"


def _worker_feedback(worker_summary: dict[str, Any] | None) -> dict[str, Any]:
    if not worker_summary:
        return {"available": False}
    positive = int(worker_summary.get("positive_trajectory_roi_count") or 0)
    nonpositive = int(worker_summary.get("nonpositive_trajectory_roi_count") or 0)
    row_count = int(worker_summary.get("row_count") or worker_summary.get("record_count") or positive + nonpositive)
    return {
        "available": True,
        "row_count": row_count,
        "positive_trajectory_roi_count": positive,
        "nonpositive_trajectory_roi_count": nonpositive,
        "positive_trajectory_roi_rate": positive / float(row_count) if row_count else 0.0,
        "roi_class_counts": dict(sorted(_counter_dict(worker_summary.get("roi_class_counts")).items())),
        "hard_negative_dominant": bool(nonpositive > positive),
        "certificate_ready": bool(worker_summary.get("certificate_ready", False)),
        "official_bound_effect": bool(worker_summary.get("official_bound_effect", False)),
    }


def _next_training_gate(next_training: dict[str, Any] | None) -> dict[str, Any]:
    if not next_training:
        return {"available": False}
    metrics = dict(next_training.get("validation_deployment_metrics") or {})
    return {
        "available": True,
        "checkpoint_gate_pass": bool(next_training.get("checkpoint_gate_pass", False)),
        "stage4_candidate_ready": bool(next_training.get("stage4_candidate_ready", False)),
        "accepted_batch_count": int(metrics.get("accepted_batch_count") or 0),
        "safe_precision_ci_low": _float_or_none(metrics.get("safe_precision_ci_low")),
        "false_high_priority_on_delay": _float_or_none(metrics.get("false_high_priority_on_delay")),
        "false_safe_rate_union": _float_or_none(metrics.get("false_safe_rate_union")),
        "threshold_local_reject_reasons": [
            str(reason) for reason in metrics.get("threshold_local_reject_reasons", [])
        ],
    }


def _recommended_next_step(
    *,
    primary: str,
    worker_feedback: dict[str, Any],
    next_training_gate: dict[str, Any],
) -> str:
    if bool(worker_feedback.get("hard_negative_dominant")):
        return "collect_train_split_same_context_positive_negative_pairs_and_delay_hard_negatives"
    if primary == "threshold_borderline_missed_high_roi":
        return "audit_precision_safe_threshold_frontier_before_lowering_candidate_threshold"
    if not bool(next_training_gate.get("checkpoint_gate_pass", False)):
        return "train_split_context_local_contrast_then_reaudit_score_and_embedding"
    return "rerun_stage3_frontier_and_knn_ood_before_stage4_shadow"


def _assert_contracts(
    score: dict[str, Any],
    embedding: dict[str, Any],
    worker: dict[str, Any] | None,
    next_training: dict[str, Any] | None,
) -> None:
    if score.get("schema_version") != "gat_batch_impact_score_margin_audit_v1":
        raise ValueError("score-margin summary schema mismatch")
    if embedding.get("schema_version") != "gat_batch_impact_embedding_separation_audit_v1":
        raise ValueError("embedding-separation summary schema mismatch")
    if not bool(score.get("all_checks_pass")):
        raise ValueError("score-margin summary did not pass checks")
    if not bool(embedding.get("all_checks_pass")):
        raise ValueError("embedding-separation summary did not pass checks")
    if int((score.get("margin_summary") or {}).get("missed_high_roi_opportunities") or 0) != int(
        (embedding.get("embedding_summary") or {}).get("missed_high_roi_opportunities") or 0
    ):
        raise ValueError("score and embedding missed high-ROI counts differ")
    if worker and worker.get("schema_version") != "gat_multibatch_worker_batch_impact_rows_summary_v1":
        raise ValueError("worker rows summary schema mismatch")
    if next_training and next_training.get("schema_version") != "gat_batch_impact_training_summary_v1":
        raise ValueError("next training summary schema mismatch")


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    decision = summary["decision_summary"]
    worker = decision["worker_feedback"]
    next_training = decision["next_training_gate"]
    lines = [
        "# BPC Future GAT Target Mode Stage 3 v43 v15 Missed High-ROI 诊断",
        "",
        "日期：2026-06-16",
        "",
        "## 结论",
        "",
        "本报告将 v15 score-margin 与 embedding-separation 审计合并为可复跑诊断。",
        "结论是：v15 missed high-ROI 不是简单阈值差一点，而是 candidate-head",
        "分数缺口和 embedding 结构混杂同时存在；Stage4 first-tranche 回流还显示",
        "显式 target worker 候选 ROI 混合，不能直接作为 HIGH_PRIORITY 证据。",
        "",
        "```text",
        f"primary = {decision['primary']}",
        f"missed_high_roi_opportunities = {decision['missed_high_roi_opportunities']}",
        f"accepted_high_roi_opportunities = {decision['accepted_high_roi_opportunities']}",
        f"candidate_threshold = {decision['candidate_threshold']}",
        f"near_threshold_miss_count = {decision['near_threshold_miss_count']}",
        f"non_near_threshold_miss_count = {decision['non_near_threshold_miss_count']}",
        f"candidate_margin_bucket_counts = {decision['candidate_margin_bucket_counts']}",
        f"missed_candidate_score_margin_mean = {decision['missed_candidate_score_margin_mean']}",
        f"missed_candidate_score_margin_min = {decision['missed_candidate_score_margin_min']}",
        f"missed_candidate_score_margin_max = {decision['missed_candidate_score_margin_max']}",
        f"missed_nearest_negative_closer_count = {decision['missed_nearest_negative_closer_count']}",
        f"missed_nearest_negative_closer_rate = {decision['missed_nearest_negative_closer_rate']}",
        f"missed_knn_positive_fraction_mean = {decision['missed_knn_positive_fraction_mean']}",
        f"accepted_high_roi_knn_positive_fraction_mean = {decision['accepted_high_roi_knn_positive_fraction_mean']}",
        f"worker_positive_trajectory_roi_count = {worker.get('positive_trajectory_roi_count')}",
        f"worker_nonpositive_trajectory_roi_count = {worker.get('nonpositive_trajectory_roi_count')}",
        f"v16_checkpoint_gate_pass = {next_training.get('checkpoint_gate_pass')}",
        f"v16_stage4_candidate_ready = {next_training.get('stage4_candidate_ready')}",
        f"recommended_next_step = {decision['recommended_next_step']}",
        "production_ready = false",
        "selector_can_certificate = false",
        "```",
        "",
        "## Family Diagnosis",
        "",
        "```json",
        json.dumps(summary["family_diagnosis"], ensure_ascii=False, indent=2, sort_keys=True),
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


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_optional_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not Path(path).exists():
        return None
    return _read_json(Path(path))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )


def _counter_dict(value: Any) -> dict[str, int]:
    return {str(key): int(count) for key, count in dict(value or {}).items()}


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    raise SystemExit(main())
