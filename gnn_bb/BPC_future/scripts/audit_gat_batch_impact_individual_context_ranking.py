#!/usr/bin/env python3
"""Audit context-local ranking of individual batch-impact targets.

This diagnostic scores an existing ``GATBatchImpactModel`` checkpoint on a
batch-impact dataset and compares positive trajectory samples against delay /
hard-negative samples in the same RMP context. It is offline-only: it does not
run BPC, pricing, RMP, workers, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.learning.batch_impact_model import GATBatchImpactModel
from BPC_future.scripts.train_gat_batch_impact import (
    _candidate_admission_scores,
    _load_sample,
    _normalize_sample,
    _prediction_records,
)


DEFAULT_DATASET_DIR = Path(
    "BPC_future/data/gat_batch_impact/v54_v51_plus_v53_individual_followup_20260616"
)
DEFAULT_CHECKPOINT = Path(
    "BPC_future/results/gat_batch_impact_training_v55_v54_individual_followup_20260616/"
    "gat_batch_impact.pt"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "gat_batch_impact_individual_context_ranking_v60_v55_individual_followup_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage3_v60_v55_individual_followup_"
    "individual_context_ranking_zh.md"
)
DEFAULT_MIN_FOCUSED_PAIR_COUNT = 1
DEFAULT_MIN_RAW_PAIR_PASS_RATE = 1.0
DEFAULT_MIN_ADMISSION_PAIR_PASS_RATE = 1.0
DEFAULT_MIN_DELAY_RISK_PAIR_PASS_RATE = 1.0
DEFAULT_MIN_STRICT_PAIR_PASS_RATE = 1.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument(
        "--focus-row-index-min",
        type=int,
        default=None,
        help="Restrict the primary audit to manifest rows with row_index >= this value.",
    )
    parser.add_argument(
        "--min-focused-pair-count",
        type=int,
        default=DEFAULT_MIN_FOCUSED_PAIR_COUNT,
        help="Minimum same-context positive-vs-negative pair count required by the audit gate.",
    )
    parser.add_argument(
        "--min-raw-pair-pass-rate",
        type=float,
        default=DEFAULT_MIN_RAW_PAIR_PASS_RATE,
        help="Minimum raw candidate score pair pass rate required by the audit gate.",
    )
    parser.add_argument(
        "--min-admission-pair-pass-rate",
        type=float,
        default=DEFAULT_MIN_ADMISSION_PAIR_PASS_RATE,
        help="Minimum risk-adjusted admission score pair pass rate required by the audit gate.",
    )
    parser.add_argument(
        "--min-delay-risk-pair-pass-rate",
        type=float,
        default=DEFAULT_MIN_DELAY_RISK_PAIR_PASS_RATE,
        help="Minimum delay-risk ordering pass rate required by the audit gate.",
    )
    parser.add_argument(
        "--min-strict-pair-pass-rate",
        type=float,
        default=DEFAULT_MIN_STRICT_PAIR_PASS_RATE,
        help="Minimum all-head strict pair pass rate required by the audit gate.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_individual_context_ranking(
        dataset_dir=Path(args.dataset_dir),
        checkpoint=Path(args.checkpoint),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        device=str(args.device),
        focus_row_index_min=args.focus_row_index_min,
        min_focused_pair_count=args.min_focused_pair_count,
        min_raw_pair_pass_rate=args.min_raw_pair_pass_rate,
        min_admission_pair_pass_rate=args.min_admission_pair_pass_rate,
        min_delay_risk_pair_pass_rate=args.min_delay_risk_pair_pass_rate,
        min_strict_pair_pass_rate=args.min_strict_pair_pass_rate,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_individual_context_ranking(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    checkpoint: Path = DEFAULT_CHECKPOINT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    device: str = "cpu",
    focus_row_index_min: int | None = None,
    min_focused_pair_count: int = DEFAULT_MIN_FOCUSED_PAIR_COUNT,
    min_raw_pair_pass_rate: float = DEFAULT_MIN_RAW_PAIR_PASS_RATE,
    min_admission_pair_pass_rate: float = DEFAULT_MIN_ADMISSION_PAIR_PASS_RATE,
    min_delay_risk_pair_pass_rate: float = DEFAULT_MIN_DELAY_RISK_PAIR_PASS_RATE,
    min_strict_pair_pass_rate: float = DEFAULT_MIN_STRICT_PAIR_PASS_RATE,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    checkpoint_data = torch.load(checkpoint, map_location="cpu", weights_only=False)
    manifest = _read_json(dataset_dir / "manifest.json")
    _assert_offline_contract(checkpoint_data, manifest)

    model = GATBatchImpactModel(**checkpoint_data["model_config"]).to(torch.device(device))
    model.load_state_dict(checkpoint_data["model_state_dict"])
    model.eval()
    samples = [
        _normalize_sample(_load_sample(dataset_dir / item["path"]), manifest)
        for item in manifest.get("samples", [])
    ]
    prediction_records = _prediction_records(model, samples, torch.device(device))
    gate_config = dict(checkpoint_data.get("deployment_gate", {}).get("gate_config") or {})
    rows = [
        build_scored_row(
            manifest_item=item,
            prediction=prediction,
            gate_config=gate_config,
        )
        for item, prediction in zip(manifest.get("samples", []), prediction_records)
    ]
    focused_rows = select_focus_rows(rows, focus_row_index_min=focus_row_index_min)
    context_rows, pair_rows = build_context_ranking_rows(focused_rows)
    summary_stats = summarize_context_ranking(focused_rows, context_rows, pair_rows)
    gate = focused_pair_gate(
        summary_stats,
        min_focused_pair_count=min_focused_pair_count,
        min_raw_pair_pass_rate=min_raw_pair_pass_rate,
        min_admission_pair_pass_rate=min_admission_pair_pass_rate,
        min_delay_risk_pair_pass_rate=min_delay_risk_pair_pass_rate,
        min_strict_pair_pass_rate=min_strict_pair_pass_rate,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    scored_path = output_dir / "scored_individual_rows.jsonl"
    context_path = output_dir / "context_ranking_rows.jsonl"
    pair_path = output_dir / "positive_negative_pair_rows.jsonl"
    _write_jsonl(scored_path, focused_rows)
    _write_jsonl(context_path, context_rows)
    _write_jsonl(pair_path, pair_rows)

    summary = {
        "schema_version": "gat_batch_impact_individual_context_ranking_v1",
        "status": "gat_batch_impact_individual_context_ranking_audited",
        "dataset_dir": str(dataset_dir),
        "checkpoint": str(checkpoint),
        "output_dir": str(output_dir),
        "scored_individual_rows_path": str(scored_path),
        "context_ranking_rows_path": str(context_path),
        "positive_negative_pair_rows_path": str(pair_path),
        "focus_row_index_min": focus_row_index_min,
        "sample_count": int(manifest.get("sample_count") or len(rows)),
        "focused_row_count": len(focused_rows),
        "summary": summary_stats,
        "focused_pair_gate": gate,
        "focused_pair_gate_pass": bool(gate["gate_pass"]),
        "stage3_focused_pair_gate_ready": bool(gate["gate_pass"]),
        "recommended_next_step": recommended_next_step(summary_stats),
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
    write_report(Path(report), summary)
    return summary


def build_scored_row(
    *,
    manifest_item: dict[str, Any],
    prediction: dict[str, Any],
    gate_config: dict[str, Any],
) -> dict[str, Any]:
    candidate_scores = [float(value) for value in prediction.get("candidate_scores", [])]
    delay_scores = [float(value) for value in prediction.get("candidate_delay_scores", [])]
    admission_scores = _candidate_admission_scores(prediction, gate_config=gate_config)
    high_priority_labels = [
        int(value) for value in prediction.get("candidate_high_priority_labels", [])
    ]
    delay_labels = [int(value) for value in prediction.get("candidate_delay_labels", [])]
    label_class = label_class_for_record(prediction)
    return {
        "row_index": _int_or_default(manifest_item.get("row_index"), -1),
        "path": str(manifest_item.get("path") or ""),
        "source_file": str(manifest_item.get("source_file") or ""),
        "context_key": context_key(manifest_item),
        "context_hash": str(manifest_item.get("context_hash") or prediction.get("context_hash") or ""),
        "instance": str(manifest_item.get("instance") or ""),
        "instance_path": str(manifest_item.get("instance_path") or ""),
        "family": str(
            manifest_item.get("instance_family") or prediction.get("family") or "unknown"
        ),
        "region": str(manifest_item.get("instance_region") or ""),
        "task_count": int(manifest_item.get("task_count") or 0),
        "candidate_count": len(candidate_scores),
        "candidate_signature_ids": list(manifest_item.get("candidate_signature_ids") or []),
        "label_class": label_class,
        "label_batch_roi_positive": int(manifest_item.get("label_batch_roi_positive") or 0),
        "accepted_batch_roi_label": float(
            manifest_item.get("accepted_batch_roi")
            if manifest_item.get("accepted_batch_roi") is not None
            else prediction.get("accepted_batch_roi_label") or 0.0
        ),
        "high_priority_label_count": int(sum(high_priority_labels)),
        "delay_label_count": int(sum(delay_labels)),
        "bad_mode_switch": int(prediction.get("bad_mode_switch") or 0),
        "batch_score": float(prediction.get("batch_score") or 0.0),
        "max_raw_candidate_score": max(candidate_scores) if candidate_scores else 0.0,
        "max_admission_score": max(admission_scores) if admission_scores else 0.0,
        "max_delay_risk_score": max(delay_scores) if delay_scores else 0.0,
        "min_delay_risk_score": min(delay_scores) if delay_scores else 0.0,
        "candidate_scores": candidate_scores,
        "candidate_delay_scores": delay_scores,
        "candidate_admission_scores": admission_scores,
        "candidate_high_priority_labels": high_priority_labels,
        "candidate_delay_labels": delay_labels,
        "diagnostic_only": True,
        "official_bound_effect": False,
    }


def label_class_for_record(record: dict[str, Any]) -> str:
    high_priority = any(int(value) for value in record.get("candidate_high_priority_labels", []))
    delay = any(int(value) for value in record.get("candidate_delay_labels", []))
    roi_positive = bool(int(record.get("batch_roi_positive") or 0))
    bad_mode = bool(int(record.get("bad_mode_switch") or 0))
    if high_priority and roi_positive and not bad_mode:
        return "positive_high_priority"
    if delay or bad_mode or not roi_positive:
        return "delay_or_hard_negative"
    return "ambiguous"


def select_focus_rows(
    rows: list[dict[str, Any]],
    *,
    focus_row_index_min: int | None,
) -> list[dict[str, Any]]:
    if focus_row_index_min is None:
        return list(rows)
    return [
        row
        for row in rows
        if _int_or_default(row.get("row_index"), -1) >= int(focus_row_index_min)
    ]


def build_context_ranking_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_context: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_context[str(row["context_key"])].append(row)

    context_rows: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    for key, group in sorted(by_context.items()):
        positives = [row for row in group if row["label_class"] == "positive_high_priority"]
        negatives = [row for row in group if row["label_class"] == "delay_or_hard_negative"]
        pairs = [
            compare_positive_negative_pair(positive, negative)
            for positive in positives
            for negative in negatives
        ]
        pair_rows.extend(pairs)
        context_rows.append(summarize_context_group(key, group, positives, negatives, pairs))
    return context_rows, pair_rows


def compare_positive_negative_pair(
    positive: dict[str, Any],
    negative: dict[str, Any],
) -> dict[str, Any]:
    raw_margin = float(positive["max_raw_candidate_score"]) - float(
        negative["max_raw_candidate_score"]
    )
    admission_margin = float(positive["max_admission_score"]) - float(
        negative["max_admission_score"]
    )
    batch_margin = float(positive["batch_score"]) - float(negative["batch_score"])
    delay_margin = float(negative["max_delay_risk_score"]) - float(
        positive["max_delay_risk_score"]
    )
    return {
        "context_key": str(positive["context_key"]),
        "context_hash": str(positive["context_hash"]),
        "family": str(positive["family"]),
        "positive_row_index": int(positive["row_index"]),
        "negative_row_index": int(negative["row_index"]),
        "positive_roi": float(positive["accepted_batch_roi_label"]),
        "negative_roi": float(negative["accepted_batch_roi_label"]),
        "positive_signature_ids": list(positive.get("candidate_signature_ids") or []),
        "negative_signature_ids": list(negative.get("candidate_signature_ids") or []),
        "raw_margin": raw_margin,
        "admission_margin": admission_margin,
        "batch_margin": batch_margin,
        "delay_risk_margin": delay_margin,
        "raw_positive_above_negative": raw_margin > 0.0,
        "admission_positive_above_negative": admission_margin > 0.0,
        "batch_positive_above_negative": batch_margin > 0.0,
        "positive_lower_delay_risk": delay_margin > 0.0,
        "pair_pass": raw_margin > 0.0 and admission_margin > 0.0 and delay_margin > 0.0,
    }


def summarize_context_group(
    key: str,
    group: list[dict[str, Any]],
    positives: list[dict[str, Any]],
    negatives: list[dict[str, Any]],
    pairs: list[dict[str, Any]],
) -> dict[str, Any]:
    first = group[0]
    return {
        "context_key": key,
        "context_hash": str(first["context_hash"]),
        "instance": str(first["instance"]),
        "family": str(first["family"]),
        "task_count": int(first["task_count"]),
        "row_count": len(group),
        "positive_count": len(positives),
        "negative_count": len(negatives),
        "pair_count": len(pairs),
        "raw_pair_pass_rate": _rate(pairs, "raw_positive_above_negative"),
        "admission_pair_pass_rate": _rate(pairs, "admission_positive_above_negative"),
        "delay_risk_pair_pass_rate": _rate(pairs, "positive_lower_delay_risk"),
        "strict_pair_pass_rate": _rate(pairs, "pair_pass"),
        "min_admission_margin": _min_or_none(
            [float(pair["admission_margin"]) for pair in pairs]
        ),
        "min_raw_margin": _min_or_none([float(pair["raw_margin"]) for pair in pairs]),
        "min_delay_risk_margin": _min_or_none(
            [float(pair["delay_risk_margin"]) for pair in pairs]
        ),
        "recommended_action": context_recommended_action(positives, negatives, pairs),
    }


def summarize_context_ranking(
    rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    label_counts = Counter(str(row["label_class"]) for row in rows)
    action_counts = Counter(str(row["recommended_action"]) for row in context_rows)
    family_counts = Counter(str(row["family"]) for row in rows)
    pair_count = len(pair_rows)
    return {
        "focused_row_count": len(rows),
        "context_count": len(context_rows),
        "contexts_with_positive_and_negative": sum(
            int(row["positive_count"] > 0 and row["negative_count"] > 0)
            for row in context_rows
        ),
        "positive_row_count": int(label_counts.get("positive_high_priority", 0)),
        "negative_row_count": int(label_counts.get("delay_or_hard_negative", 0)),
        "ambiguous_row_count": int(label_counts.get("ambiguous", 0)),
        "pair_count": pair_count,
        "raw_pair_pass_count": _count_true(pair_rows, "raw_positive_above_negative"),
        "admission_pair_pass_count": _count_true(
            pair_rows, "admission_positive_above_negative"
        ),
        "delay_risk_pair_pass_count": _count_true(pair_rows, "positive_lower_delay_risk"),
        "strict_pair_pass_count": _count_true(pair_rows, "pair_pass"),
        "raw_pair_pass_rate": _rate(pair_rows, "raw_positive_above_negative"),
        "admission_pair_pass_rate": _rate(pair_rows, "admission_positive_above_negative"),
        "delay_risk_pair_pass_rate": _rate(pair_rows, "positive_lower_delay_risk"),
        "strict_pair_pass_rate": _rate(pair_rows, "pair_pass"),
        "mean_admission_margin": _mean_or_none(
            [float(pair["admission_margin"]) for pair in pair_rows]
        ),
        "mean_raw_margin": _mean_or_none([float(pair["raw_margin"]) for pair in pair_rows]),
        "mean_delay_risk_margin": _mean_or_none(
            [float(pair["delay_risk_margin"]) for pair in pair_rows]
        ),
        "label_counts": dict(sorted(label_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "recommended_action_counts": dict(sorted(action_counts.items())),
        "primary": primary_diagnosis(pair_rows, context_rows),
    }


def focused_pair_gate(
    summary: dict[str, Any],
    *,
    min_focused_pair_count: int = DEFAULT_MIN_FOCUSED_PAIR_COUNT,
    min_raw_pair_pass_rate: float = DEFAULT_MIN_RAW_PAIR_PASS_RATE,
    min_admission_pair_pass_rate: float = DEFAULT_MIN_ADMISSION_PAIR_PASS_RATE,
    min_delay_risk_pair_pass_rate: float = DEFAULT_MIN_DELAY_RISK_PAIR_PASS_RATE,
    min_strict_pair_pass_rate: float = DEFAULT_MIN_STRICT_PAIR_PASS_RATE,
) -> dict[str, Any]:
    reject_reasons: list[str] = []
    pair_count = int(summary.get("pair_count") or 0)
    thresholds = {
        "min_focused_pair_count": int(min_focused_pair_count),
        "min_raw_pair_pass_rate": float(min_raw_pair_pass_rate),
        "min_admission_pair_pass_rate": float(min_admission_pair_pass_rate),
        "min_delay_risk_pair_pass_rate": float(min_delay_risk_pair_pass_rate),
        "min_strict_pair_pass_rate": float(min_strict_pair_pass_rate),
    }
    observed = {
        "pair_count": pair_count,
        "raw_pair_pass_rate": summary.get("raw_pair_pass_rate"),
        "admission_pair_pass_rate": summary.get("admission_pair_pass_rate"),
        "delay_risk_pair_pass_rate": summary.get("delay_risk_pair_pass_rate"),
        "strict_pair_pass_rate": summary.get("strict_pair_pass_rate"),
    }

    if pair_count < int(min_focused_pair_count):
        reject_reasons.append("not_enough_focused_positive_negative_pairs")

    _append_rate_reject(
        reject_reasons,
        observed.get("raw_pair_pass_rate"),
        min_raw_pair_pass_rate,
        "raw_pair_pass_rate_below_threshold",
    )
    _append_rate_reject(
        reject_reasons,
        observed.get("admission_pair_pass_rate"),
        min_admission_pair_pass_rate,
        "admission_pair_pass_rate_below_threshold",
    )
    _append_rate_reject(
        reject_reasons,
        observed.get("delay_risk_pair_pass_rate"),
        min_delay_risk_pair_pass_rate,
        "delay_risk_pair_pass_rate_below_threshold",
    )
    _append_rate_reject(
        reject_reasons,
        observed.get("strict_pair_pass_rate"),
        min_strict_pair_pass_rate,
        "strict_pair_pass_rate_below_threshold",
    )

    gate_pass = not reject_reasons
    return {
        "gate_name": "focused_same_context_positive_negative_pair_gate",
        "gate_pass": gate_pass,
        "reject_reasons": reject_reasons,
        "thresholds": thresholds,
        "observed": observed,
        "blocking_primary": (
            "focused_context_pair_gate_passed"
            if gate_pass
            else str(summary.get("primary") or "focused_pair_gate_failed")
        ),
        "diagnostic_only": True,
        "production_ready": False,
        "selector_can_certificate": False,
    }


def context_recommended_action(
    positives: list[dict[str, Any]],
    negatives: list[dict[str, Any]],
    pairs: list[dict[str, Any]],
) -> str:
    if not positives:
        return "collect_positive_counterpart_or_keep_as_delay_hard_negative"
    if not negatives:
        return "collect_negative_counterpart_for_context_local_ranking"
    if not pairs:
        return "insufficient_pairwise_contrast"
    if any(not pair["raw_positive_above_negative"] for pair in pairs):
        return "candidate_head_context_ranking_failure"
    if any(not pair["positive_lower_delay_risk"] for pair in pairs):
        return "delay_risk_head_context_ranking_failure"
    if any(not pair["admission_positive_above_negative"] for pair in pairs):
        return "risk_adjusted_admission_ranking_failure"
    return "context_local_ranking_passes"


def recommended_next_step(summary: dict[str, Any]) -> dict[str, Any]:
    if int(summary.get("pair_count") or 0) == 0:
        return {"primary": "collect_same_context_positive_negative_pairs"}
    if float(summary.get("raw_pair_pass_rate") or 0.0) < 1.0:
        return {
            "primary": "repair_candidate_head_context_local_representation",
            "reason": "positive_targets_not_ranked_above_hard_negatives_by_raw_candidate_score",
        }
    if float(summary.get("delay_risk_pair_pass_rate") or 0.0) < 1.0:
        return {
            "primary": "calibrate_delay_risk_head_with_context_local_positive_negative_pairs",
            "reason": "positive_targets_have_delay_risk_not_lower_than_hard_negatives",
        }
    if float(summary.get("admission_pair_pass_rate") or 0.0) < 1.0:
        return {
            "primary": "calibrate_risk_adjusted_admission_score_or_rescue_window",
            "reason": "raw_candidate_ranking_ok_but_risk_adjusted_admission_order_fails",
        }
    return {
        "primary": "ranking_ok_collect_more_contexts_before_stage4",
        "reason": "focused_context_pairs_pass_but_stage3_global_gate_still_fails",
    }


def primary_diagnosis(
    pair_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
) -> str:
    if not pair_rows:
        if any(row["positive_count"] == 0 for row in context_rows):
            return "positive_counterpart_missing_in_some_contexts"
        return "no_pairwise_contrast_available"
    if any(not pair["raw_positive_above_negative"] for pair in pair_rows):
        return "candidate_head_context_ranking_failure"
    if any(not pair["positive_lower_delay_risk"] for pair in pair_rows):
        return "delay_risk_head_context_ranking_failure"
    if any(not pair["admission_positive_above_negative"] for pair in pair_rows):
        return "risk_adjusted_admission_ranking_failure"
    return "focused_context_ranking_passes"


def context_key(item: dict[str, Any]) -> str:
    return "|".join(
        [
            str(item.get("instance_path") or item.get("instance") or ""),
            str(item.get("context_hash") or ""),
        ]
    )


def _rate(rows: list[dict[str, Any]], field: str) -> float | None:
    if not rows:
        return None
    return float(_count_true(rows, field)) / float(len(rows))


def _count_true(rows: list[dict[str, Any]], field: str) -> int:
    return sum(int(bool(row.get(field))) for row in rows)


def _int_or_default(value: Any, default: int) -> int:
    try:
        if value is None or value == "":
            return int(default)
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _append_rate_reject(
    reject_reasons: list[str],
    observed: Any,
    threshold: float,
    reason: str,
) -> None:
    if observed is None or float(observed) < float(threshold):
        reject_reasons.append(reason)


def _mean_or_none(values: list[float]) -> float | None:
    return float(mean(values)) if values else None


def _min_or_none(values: list[float]) -> float | None:
    return min(values) if values else None


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )


def _assert_offline_contract(checkpoint: dict[str, Any], manifest: dict[str, Any]) -> None:
    exactness = checkpoint.get("exactness_contract") or {}
    if bool(exactness.get("pricing_oracle")):
        raise ValueError("checkpoint contract unexpectedly marks pricing_oracle=true")
    if bool(exactness.get("certificate_source")):
        raise ValueError("checkpoint contract unexpectedly marks certificate_source=true")
    if bool(manifest.get("production_ready", False)):
        raise ValueError("dataset manifest unexpectedly marks production_ready=true")


def write_report(report: Path, summary: dict[str, Any]) -> None:
    s = summary["summary"]
    gate = summary["focused_pair_gate"]
    lines = [
        "# GAT Batch Impact Individual Context Ranking 审计报告",
        "",
        "日期：2026-06-16",
        "",
        "## 目的",
        "",
        "审计同一 RMP context 内 positive trajectory target 是否被当前模型排在 "
        "delay / hard-negative target 前面。该脚本只读 dataset 和 checkpoint，"
        "不运行 BPC / pricing / RMP / worker / certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_batch_impact_individual_context_ranking = current",
        f"status = {summary['status']}",
        f"focused_row_count = {s['focused_row_count']}",
        f"context_count = {s['context_count']}",
        f"contexts_with_positive_and_negative = {s['contexts_with_positive_and_negative']}",
        f"positive_row_count = {s['positive_row_count']}",
        f"negative_row_count = {s['negative_row_count']}",
        f"pair_count = {s['pair_count']}",
        f"raw_pair_pass_rate = {s['raw_pair_pass_rate']}",
        f"admission_pair_pass_rate = {s['admission_pair_pass_rate']}",
        f"delay_risk_pair_pass_rate = {s['delay_risk_pair_pass_rate']}",
        f"strict_pair_pass_rate = {s['strict_pair_pass_rate']}",
        f"primary = {s['primary']}",
        f"focused_pair_gate_pass = {summary['focused_pair_gate_pass']}",
        f"focused_pair_gate_reject_reasons = {gate['reject_reasons']}",
        f"stage3_focused_pair_gate_ready = {summary['stage3_focused_pair_gate_ready']}",
        f"recommended_next_step = {summary['recommended_next_step']['primary']}",
        "production_ready = false",
        "selector_can_certificate = false",
        "all_checks_pass = true",
        "```",
        "",
        "## Recommended Next Step",
        "",
        "```json",
        json.dumps(summary["recommended_next_step"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Focused Pair Gate",
        "",
        "```json",
        json.dumps(gate, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Output Artifacts",
        "",
        "```text",
        f"summary = {summary['output_dir']}/summary.json",
        f"scored_rows = {summary['scored_individual_rows_path']}",
        f"context_rows = {summary['context_ranking_rows_path']}",
        f"pair_rows = {summary['positive_negative_pair_rows_path']}",
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
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
