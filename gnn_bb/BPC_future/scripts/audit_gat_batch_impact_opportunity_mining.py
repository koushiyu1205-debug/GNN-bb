#!/usr/bin/env python3
"""Mine validation high-ROI opportunities missed by the Stage 3 gate.

This script is offline/diagnostic-only. It loads the existing batch-impact
checkpoint, scores the validation split, applies the selected threshold rule
from the threshold-frontier artifact, and explains which high-ROI opportunities
are accepted or missed. It does not run BPC, pricing, RMP, workers, or
certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.learning.batch_impact_model import (
    BATCH_IMPACT_EXACTNESS_CONTRACT,
    GATBatchImpactModel,
)
from BPC_future.scripts.audit_gat_batch_impact_threshold_frontier import records_for_split
from BPC_future.scripts.train_gat_batch_impact import (
    _load_sample,
    _normalize_sample,
    _prediction_records,
)


DEFAULT_DATASET_DIR = Path("BPC_future/data/gat_batch_impact/v3_signature_20260616")
DEFAULT_CHECKPOINT = Path("BPC_future/data/gat_batch_impact/v3_signature_20260616/gat_batch_impact.pt")
DEFAULT_TRAINING_SUMMARY = Path("BPC_future/results/gat_batch_impact_training_v3_signature_20260616/summary.json")
DEFAULT_THRESHOLD_SUMMARY = Path(
    "BPC_future/results/gat_batch_impact_threshold_frontier_v3_signature_20260616/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_batch_impact_opportunity_mining_v3_signature_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_batch_impact_opportunity_mining_v3_signature_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--training-summary", type=Path, default=DEFAULT_TRAINING_SUMMARY)
    parser.add_argument("--threshold-summary", type=Path, default=DEFAULT_THRESHOLD_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--top-k", type=int, default=25)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_opportunity_mining(
        dataset_dir=Path(args.dataset_dir),
        checkpoint=Path(args.checkpoint),
        training_summary=Path(args.training_summary),
        threshold_summary=Path(args.threshold_summary),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        device=str(args.device),
        top_k=max(1, int(args.top_k)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_opportunity_mining(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    checkpoint: Path = DEFAULT_CHECKPOINT,
    training_summary: Path = DEFAULT_TRAINING_SUMMARY,
    threshold_summary: Path = DEFAULT_THRESHOLD_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    device: str = "cpu",
    top_k: int = 25,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    checkpoint_data = torch.load(checkpoint, map_location="cpu", weights_only=False)
    training = _read_json(Path(training_summary))
    threshold = _read_json(Path(threshold_summary))
    manifest = _read_json(dataset_dir / "manifest.json")
    _assert_contracts(checkpoint_data, training, threshold, manifest)

    model = GATBatchImpactModel(**checkpoint_data["model_config"]).to(torch.device(device))
    model.load_state_dict(checkpoint_data["model_state_dict"])
    model.eval()
    samples = [
        _normalize_sample(_load_sample(dataset_dir / item["path"]), manifest)
        for item in manifest.get("samples", [])
    ]
    records = _prediction_records(model, samples, torch.device(device))
    enriched_record_items = [
        (
            str(
                getattr(sample, "batch_impact_instance_path", "")
                or getattr(sample, "batch_impact_instance", "")
            ),
            _attach_sample_metadata(record, sample),
        )
        for sample, record in zip(samples, records)
    ]
    split = training.get("split") or checkpoint_data.get("training_contract", {}).get("main_split") or {}
    _, validation_records = records_for_split(
        enriched_record_items,
        train_instances={str(instance) for instance in split.get("train_instances", [])},
        validation_instances={str(instance) for instance in split.get("validation_instances", [])},
    )
    if not validation_records:
        raise ValueError("training split does not match opportunity-mining dataset")
    selected_threshold = dict(threshold.get("best_candidate") or {})
    if not selected_threshold:
        raise ValueError("threshold summary is missing best_candidate")
    gate_config = dict(threshold.get("gate_config") or {})
    decisions = [
        classify_opportunity_record(
            record,
            batch_threshold=float(selected_threshold["batch_threshold"]),
            candidate_threshold=float(selected_threshold["candidate_threshold"]),
            candidate_delay_gate_enabled=bool(selected_threshold.get("candidate_delay_gate_enabled", False)),
            candidate_delay_risk_threshold=float(selected_threshold.get("candidate_delay_risk_threshold", 1.0)),
            candidate_admission_score_mode=str(
                selected_threshold.get("candidate_admission_score_mode", "high_priority") or "high_priority"
            ),
            candidate_delay_score_penalty=float(selected_threshold.get("candidate_delay_score_penalty", 0.0)),
            candidate_rescue_raw_score_threshold=float(
                selected_threshold.get("candidate_rescue_raw_score_threshold", 1.0)
            ),
            candidate_rescue_delay_risk_threshold=float(
                selected_threshold.get("candidate_rescue_delay_risk_threshold", 1.0)
            ),
            candidate_rescue_delay_score_penalty=float(
                selected_threshold.get("candidate_rescue_delay_score_penalty", 0.0)
            ),
            batch_thresholds_by_family=dict(selected_threshold.get("batch_thresholds_by_family") or {}),
            family_delay_fallback_families=list(
                selected_threshold.get("family_delay_fallback_families") or []
            ),
            context_delay_fallback_contexts=list(
                selected_threshold.get("context_delay_fallback_contexts") or []
            ),
            min_accepted_batch_roi=float(gate_config["min_accepted_batch_roi"]),
        )
        for record in validation_records
    ]
    top_missed = sorted(
        [item for item in decisions if item["is_missed_high_roi_opportunity"]],
        key=lambda item: (
            float(item["accepted_batch_roi_label"]),
            float(item["max_safe_candidate_score"]),
            float(item["batch_score"]),
        ),
        reverse=True,
    )[: int(top_k)]
    output_dir.mkdir(parents=True, exist_ok=True)
    opportunities_path = output_dir / "validation_opportunities.jsonl"
    top_missed_path = output_dir / "top_missed_high_roi_opportunities.jsonl"
    opportunities_path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in decisions)
        + ("\n" if decisions else ""),
        encoding="utf-8",
    )
    top_missed_path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in top_missed)
        + ("\n" if top_missed else ""),
        encoding="utf-8",
    )
    summary = {
        "schema_version": "gat_batch_impact_opportunity_mining_v1",
        "status": "gat_batch_impact_opportunity_mining_audited",
        "dataset_dir": str(dataset_dir),
        "checkpoint": str(checkpoint),
        "training_summary": str(training_summary),
        "threshold_summary": str(threshold_summary),
        "output_dir": str(output_dir),
        "validation_opportunities_path": str(opportunities_path),
        "top_missed_high_roi_path": str(top_missed_path),
        "validation_record_count": len(validation_records),
        "selected_threshold": {
            "threshold_scope": selected_threshold.get("threshold_scope"),
            "threshold_mode": selected_threshold.get("threshold_mode"),
            "batch_threshold": selected_threshold.get("batch_threshold"),
            "candidate_threshold": selected_threshold.get("candidate_threshold"),
            "candidate_admission_score_mode": selected_threshold.get(
                "candidate_admission_score_mode", "high_priority"
            ),
            "candidate_delay_score_penalty": selected_threshold.get("candidate_delay_score_penalty", 0.0),
            "candidate_rescue_raw_score_threshold": selected_threshold.get(
                "candidate_rescue_raw_score_threshold", 1.0
            ),
            "candidate_rescue_delay_risk_threshold": selected_threshold.get(
                "candidate_rescue_delay_risk_threshold", 1.0
            ),
            "candidate_rescue_delay_score_penalty": selected_threshold.get(
                "candidate_rescue_delay_score_penalty", 0.0
            ),
            "candidate_delay_gate_enabled": selected_threshold.get("candidate_delay_gate_enabled", False),
            "candidate_delay_risk_threshold": selected_threshold.get("candidate_delay_risk_threshold", 1.0),
            "batch_thresholds_by_family": selected_threshold.get("batch_thresholds_by_family") or {},
            "family_delay_fallback_families": selected_threshold.get(
                "family_delay_fallback_families"
            )
            or [],
            "context_delay_fallback_contexts": selected_threshold.get(
                "context_delay_fallback_contexts"
            )
            or [],
        },
        "gate_config": gate_config,
        "opportunity_summary": _opportunity_summary(decisions),
        "top_missed_high_roi_opportunities": top_missed,
        "recommended_next_step": _recommended_next_step(decisions),
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


def classify_opportunity_record(
    record: dict[str, Any],
    *,
    batch_threshold: float,
    candidate_threshold: float,
    candidate_delay_gate_enabled: bool = False,
    candidate_delay_risk_threshold: float = 1.0,
    candidate_admission_score_mode: str = "high_priority",
    candidate_delay_score_penalty: float = 0.0,
    candidate_rescue_raw_score_threshold: float = 1.0,
    candidate_rescue_delay_risk_threshold: float = 1.0,
    candidate_rescue_delay_score_penalty: float = 0.0,
    batch_thresholds_by_family: dict[str, float] | None = None,
    family_delay_fallback_families: list[str] | None = None,
    context_delay_fallback_contexts: list[str] | None = None,
    min_accepted_batch_roi: float = 0.65,
) -> dict[str, Any]:
    family = str(record.get("family") or "unknown")
    family_batch_threshold = float(
        (batch_thresholds_by_family or {}).get(family, batch_threshold)
    )
    batch_score = float(record["batch_score"])
    raw_candidate_scores = [float(score) for score in record["candidate_scores"]]
    candidate_delay_scores = _candidate_delay_scores(
        record,
        candidate_delay_gate_enabled=bool(candidate_delay_gate_enabled),
    )
    candidate_scores = _candidate_admission_scores(
        raw_candidate_scores,
        candidate_delay_scores,
        candidate_admission_score_mode=candidate_admission_score_mode,
        candidate_delay_score_penalty=candidate_delay_score_penalty,
        candidate_rescue_raw_score_threshold=candidate_rescue_raw_score_threshold,
        candidate_rescue_delay_risk_threshold=candidate_rescue_delay_risk_threshold,
        candidate_rescue_delay_score_penalty=candidate_rescue_delay_score_penalty,
    )
    base_candidate_scores = _candidate_base_admission_scores(
        raw_candidate_scores,
        candidate_delay_scores,
        candidate_admission_score_mode=candidate_admission_score_mode,
        candidate_delay_score_penalty=candidate_delay_score_penalty,
    )
    rescue_eligible_indices = [
        idx
        for idx, raw_score in enumerate(raw_candidate_scores)
        if _candidate_rescue_window_eligible(
            raw_score,
            candidate_delay_scores[idx],
            candidate_admission_score_mode=candidate_admission_score_mode,
            candidate_rescue_raw_score_threshold=candidate_rescue_raw_score_threshold,
            candidate_rescue_delay_risk_threshold=candidate_rescue_delay_risk_threshold,
        )
    ]
    candidate_delay_labels = [int(value) for value in record["candidate_delay_labels"]]
    candidate_hp_labels = [int(value) for value in record["candidate_high_priority_labels"]]
    fallback_families = {str(value) for value in (family_delay_fallback_families or [])}
    fallback_contexts = {str(value) for value in (context_delay_fallback_contexts or [])}
    family_delay_fallback = family in fallback_families
    context_delay_fallback = str(record.get("context_hash") or "") in fallback_contexts
    predicted_indices = [
        idx
        for idx, score in enumerate(candidate_scores)
        if score >= float(candidate_threshold)
        and (
            not bool(candidate_delay_gate_enabled)
            or float(candidate_delay_scores[idx]) <= float(candidate_delay_risk_threshold)
            or idx in set(rescue_eligible_indices)
        )
    ]
    if family_delay_fallback or context_delay_fallback:
        predicted_indices = []
    delay_gate_blocked_indices = [
        idx
        for idx, score in enumerate(raw_candidate_scores)
        if score >= float(candidate_threshold)
        and bool(candidate_delay_gate_enabled)
        and float(candidate_delay_scores[idx]) > float(candidate_delay_risk_threshold)
    ]
    risk_adjusted_suppressed_indices = [
        idx
        for idx, raw_score in enumerate(raw_candidate_scores)
        if _candidate_admission_score_mode(candidate_admission_score_mode) != "high_priority"
        and raw_score >= float(candidate_threshold)
        and idx < len(base_candidate_scores)
        and base_candidate_scores[idx] < float(candidate_threshold)
    ]
    rescue_promoted_indices = [
        idx
        for idx in predicted_indices
        if idx in set(rescue_eligible_indices)
        and (
            idx >= len(base_candidate_scores)
            or base_candidate_scores[idx] < float(candidate_threshold)
            or (
                bool(candidate_delay_gate_enabled)
                and float(candidate_delay_scores[idx]) > float(candidate_delay_risk_threshold)
            )
        )
    ]
    predicted_delay_indices = [
        idx for idx in predicted_indices if idx < len(candidate_delay_labels) and candidate_delay_labels[idx]
    ]
    safe_candidate_indices = [
        idx for idx, label in enumerate(candidate_delay_labels) if not int(label)
    ]
    predicted_safe_indices = [
        idx for idx in predicted_indices if idx in set(safe_candidate_indices)
    ]
    batch_pass = batch_score >= family_batch_threshold
    accepted = bool(
        batch_pass
        and predicted_indices
        and not predicted_delay_indices
        and not family_delay_fallback
        and not context_delay_fallback
    )
    high_roi_opportunity = bool(
        float(record.get("accepted_batch_roi_label") or 0.0) >= float(min_accepted_batch_roi)
        and not int(record.get("bad_mode_switch") or 0)
    )
    missed_reasons: list[str] = []
    if high_roi_opportunity and not accepted:
        if not batch_pass:
            missed_reasons.append("batch_score_below_family_threshold")
        if family_delay_fallback:
            missed_reasons.append("family_delay_fallback")
        if context_delay_fallback:
            missed_reasons.append("context_delay_fallback")
        if not predicted_indices and not (family_delay_fallback or context_delay_fallback):
            missed_reasons.append("no_candidate_above_threshold")
        if risk_adjusted_suppressed_indices:
            missed_reasons.append("candidate_risk_adjusted_below_threshold")
        if delay_gate_blocked_indices:
            missed_reasons.append("candidate_delay_risk_above_threshold")
        if predicted_delay_indices:
            missed_reasons.append("candidate_delay_conflict")
        if not missed_reasons:
            missed_reasons.append("not_accepted_unknown")
    max_candidate_score = max(candidate_scores) if candidate_scores else 0.0
    max_raw_candidate_score = max(raw_candidate_scores) if raw_candidate_scores else 0.0
    max_safe_candidate_score = (
        max(candidate_scores[idx] for idx in safe_candidate_indices)
        if safe_candidate_indices
        else 0.0
    )
    max_delay_candidate_score = (
        max(candidate_scores[idx] for idx, label in enumerate(candidate_delay_labels) if int(label))
        if any(int(label) for label in candidate_delay_labels)
        else 0.0
    )
    signature_ids = list(record.get("candidate_signature_ids") or [])
    predicted_signature_ids = [
        str(signature_ids[idx])
        for idx in predicted_indices
        if idx < len(signature_ids)
    ]
    return {
        "family": family,
        "context_hash": str(record.get("context_hash") or ""),
        "instance": str(record.get("instance") or ""),
        "instance_path": str(record.get("instance_path") or ""),
        "region": str(record.get("region") or ""),
        "task_count": int(record.get("task_count") or 0),
        "accepted": accepted,
        "is_high_roi_opportunity": high_roi_opportunity,
        "is_missed_high_roi_opportunity": bool(high_roi_opportunity and not accepted),
        "is_accepted_high_roi_opportunity": bool(high_roi_opportunity and accepted),
        "is_accepted_low_roi_or_bad": bool(accepted and not high_roi_opportunity),
        "missed_reasons": missed_reasons,
        "batch_score": batch_score,
        "family_batch_threshold": family_batch_threshold,
        "batch_score_margin": float(batch_score - family_batch_threshold),
        "candidate_threshold": float(candidate_threshold),
        "candidate_admission_score_mode": _candidate_admission_score_mode(candidate_admission_score_mode),
        "candidate_delay_score_penalty": max(0.0, float(candidate_delay_score_penalty)),
        "candidate_rescue_raw_score_threshold": min(
            1.0,
            max(0.0, float(candidate_rescue_raw_score_threshold)),
        ),
        "candidate_rescue_delay_risk_threshold": min(
            1.0,
            max(0.0, float(candidate_rescue_delay_risk_threshold)),
        ),
        "candidate_rescue_delay_score_penalty": max(
            0.0,
            float(candidate_rescue_delay_score_penalty),
        ),
        "candidate_delay_gate_enabled": bool(candidate_delay_gate_enabled),
        "candidate_delay_risk_threshold": float(candidate_delay_risk_threshold),
        "family_delay_fallback": bool(family_delay_fallback),
        "context_delay_fallback": bool(context_delay_fallback),
        "candidate_count": len(candidate_scores),
        "predicted_candidate_count": len(predicted_indices),
        "candidate_delay_gate_blocked_count": len(delay_gate_blocked_indices),
        "candidate_risk_adjusted_suppressed_count": len(risk_adjusted_suppressed_indices),
        "candidate_rescue_window_eligible_count": len(rescue_eligible_indices),
        "candidate_rescue_window_promoted_count": len(rescue_promoted_indices),
        "predicted_safe_candidate_count": len(predicted_safe_indices),
        "predicted_delay_candidate_count": len(predicted_delay_indices),
        "max_candidate_score": float(max_candidate_score),
        "max_candidate_score_margin": float(max_candidate_score - float(candidate_threshold)),
        "max_raw_candidate_score": float(max_raw_candidate_score),
        "max_raw_candidate_score_margin": float(max_raw_candidate_score - float(candidate_threshold)),
        "max_safe_candidate_score": float(max_safe_candidate_score),
        "max_safe_candidate_score_margin": float(max_safe_candidate_score - float(candidate_threshold)),
        "max_delay_candidate_score": float(max_delay_candidate_score),
        "true_high_priority_candidate_count": int(sum(candidate_hp_labels)),
        "delay_candidate_label_count": int(sum(candidate_delay_labels)),
        "batch_roi_positive": int(record.get("batch_roi_positive") or 0),
        "bad_mode_switch": int(record.get("bad_mode_switch") or 0),
        "tail_improved": int(record.get("tail_improved") or 0),
        "support_changed_good": int(record.get("support_changed_good") or 0),
        "accepted_batch_roi_label": float(record.get("accepted_batch_roi_label") or 0.0),
        "candidate_signature_id_count": len(signature_ids),
        "predicted_candidate_signature_ids": predicted_signature_ids[:20],
    }


def _candidate_delay_scores(record: dict[str, Any], *, candidate_delay_gate_enabled: bool) -> list[float]:
    candidate_scores = [float(score) for score in record.get("candidate_scores", [])]
    delay_scores = [float(score) for score in record.get("candidate_delay_scores", [])]
    if len(delay_scores) == len(candidate_scores):
        return delay_scores
    default_score = 1.0 if bool(candidate_delay_gate_enabled) else 0.0
    return [float(default_score) for _ in candidate_scores]


def _candidate_admission_score_mode(mode: str) -> str:
    mode = str(mode or "high_priority")
    if mode not in {"high_priority", "risk_adjusted_product", "risk_adjusted_rescue_window"}:
        return "high_priority"
    return mode


def _risk_adjusted_scores(
    candidate_scores: list[float],
    delay_scores: list[float],
    *,
    penalty: float,
) -> list[float]:
    return [
        max(0.0, min(1.0, float(candidate_score) * (max(0.0, min(1.0, 1.0 - float(delay_score))) ** max(0.0, float(penalty)))))
        for candidate_score, delay_score in zip(candidate_scores, delay_scores)
    ]


def _candidate_base_admission_scores(
    candidate_scores: list[float],
    delay_scores: list[float],
    *,
    candidate_admission_score_mode: str,
    candidate_delay_score_penalty: float,
) -> list[float]:
    if _candidate_admission_score_mode(candidate_admission_score_mode) == "high_priority":
        return [float(score) for score in candidate_scores]
    return _risk_adjusted_scores(
        candidate_scores,
        delay_scores,
        penalty=candidate_delay_score_penalty,
    )


def _candidate_rescue_window_eligible(
    raw_score: float,
    delay_score: float,
    *,
    candidate_admission_score_mode: str,
    candidate_rescue_raw_score_threshold: float,
    candidate_rescue_delay_risk_threshold: float,
) -> bool:
    if _candidate_admission_score_mode(candidate_admission_score_mode) != "risk_adjusted_rescue_window":
        return False
    return (
        float(raw_score) >= min(1.0, max(0.0, float(candidate_rescue_raw_score_threshold)))
        and float(delay_score) <= min(1.0, max(0.0, float(candidate_rescue_delay_risk_threshold)))
    )


def _candidate_admission_scores(
    candidate_scores: list[float],
    delay_scores: list[float],
    *,
    candidate_admission_score_mode: str,
    candidate_delay_score_penalty: float,
    candidate_rescue_raw_score_threshold: float = 1.0,
    candidate_rescue_delay_risk_threshold: float = 1.0,
    candidate_rescue_delay_score_penalty: float = 0.0,
) -> list[float]:
    mode = _candidate_admission_score_mode(candidate_admission_score_mode)
    base_scores = _candidate_base_admission_scores(
        candidate_scores,
        delay_scores,
        candidate_admission_score_mode=mode,
        candidate_delay_score_penalty=candidate_delay_score_penalty,
    )
    if mode != "risk_adjusted_rescue_window":
        return base_scores
    rescue_scores = _risk_adjusted_scores(
        candidate_scores,
        delay_scores,
        penalty=candidate_rescue_delay_score_penalty,
    )
    return [
        max(float(base_score), float(rescue_scores[idx]))
        if idx < len(rescue_scores)
        and _candidate_rescue_window_eligible(
            candidate_scores[idx],
            delay_scores[idx],
            candidate_admission_score_mode=mode,
            candidate_rescue_raw_score_threshold=candidate_rescue_raw_score_threshold,
            candidate_rescue_delay_risk_threshold=candidate_rescue_delay_risk_threshold,
        )
        else float(base_score)
        for idx, base_score in enumerate(base_scores)
    ]


def _attach_sample_metadata(record: dict[str, Any], sample: Any) -> dict[str, Any]:
    enriched = dict(record)
    enriched.update(
        {
            "instance": str(getattr(sample, "batch_impact_instance", "") or ""),
            "instance_path": str(getattr(sample, "batch_impact_instance_path", "") or ""),
            "region": str(getattr(sample, "batch_impact_instance_region", "") or ""),
            "task_count": int(getattr(sample, "batch_impact_task_count", 0) or 0),
            "candidate_signature_ids": list(
                getattr(sample, "batch_impact_candidate_signature_ids", []) or []
            ),
        }
    )
    return enriched


def _opportunity_summary(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    family: dict[str, dict[str, int]] = {}
    missed_reasons = Counter()
    task_counts = Counter()
    for item in decisions:
        fam = str(item["family"])
        row = family.setdefault(
            fam,
            {
                "records": 0,
                "accepted": 0,
                "high_roi_opportunities": 0,
                "accepted_high_roi_opportunities": 0,
                "missed_high_roi_opportunities": 0,
                "accepted_low_roi_or_bad": 0,
            },
        )
        row["records"] += 1
        row["accepted"] += int(bool(item["accepted"]))
        row["high_roi_opportunities"] += int(bool(item["is_high_roi_opportunity"]))
        row["accepted_high_roi_opportunities"] += int(bool(item["is_accepted_high_roi_opportunity"]))
        row["missed_high_roi_opportunities"] += int(bool(item["is_missed_high_roi_opportunity"]))
        row["accepted_low_roi_or_bad"] += int(bool(item["is_accepted_low_roi_or_bad"]))
        missed_reasons.update(str(reason) for reason in item.get("missed_reasons") or [])
        task_counts.update([str(item.get("task_count") or 0)])
    high_roi = [item for item in decisions if item["is_high_roi_opportunity"]]
    accepted = [item for item in decisions if item["accepted"]]
    accepted_high_roi = [item for item in decisions if item["is_accepted_high_roi_opportunity"]]
    missed_high_roi = [item for item in decisions if item["is_missed_high_roi_opportunity"]]
    return {
        "records": len(decisions),
        "accepted": len(accepted),
        "high_roi_opportunities": len(high_roi),
        "accepted_high_roi_opportunities": len(accepted_high_roi),
        "missed_high_roi_opportunities": len(missed_high_roi),
        "accepted_low_roi_or_bad": sum(int(item["is_accepted_low_roi_or_bad"]) for item in decisions),
        "candidate_rescue_window_eligible_count": sum(
            int(item.get("candidate_rescue_window_eligible_count") or 0)
            for item in decisions
        ),
        "candidate_rescue_window_promoted_count": sum(
            int(item.get("candidate_rescue_window_promoted_count") or 0)
            for item in decisions
        ),
        "accepted_high_roi_capture_rate": (
            len(accepted_high_roi) / float(len(high_roi)) if high_roi else 0.0
        ),
        "missed_reason_counts": dict(sorted(missed_reasons.items())),
        "family": dict(sorted(family.items())),
        "task_count_counts": dict(sorted(task_counts.items())),
    }


def _recommended_next_step(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    missed = [item for item in decisions if item["is_missed_high_roi_opportunity"]]
    if not missed:
        return {"primary": "no_missed_high_roi_opportunities_under_selected_threshold"}
    reason_counts = Counter(reason for item in missed for reason in item.get("missed_reasons") or [])
    family_counts = Counter(str(item["family"]) for item in missed)
    if any(int(item.get("candidate_rescue_window_promoted_count") or 0) > 0 for item in missed):
        primary = "calibrate_rescue_window_against_remaining_missed_high_roi_candidates"
    elif reason_counts.get("batch_score_below_family_threshold", 0) >= reason_counts.get(
        "no_candidate_above_threshold", 0
    ):
        primary = "improve_batch_roi_ranking_or_collect_more_high_roi_batch_examples"
    elif reason_counts.get("candidate_risk_adjusted_below_threshold", 0) > 0:
        primary = "calibrate_delay_risk_penalty_against_missed_high_roi_safe_candidates"
    elif reason_counts.get("no_candidate_above_threshold", 0) > 0:
        primary = "improve_candidate_high_priority_scores_for_high_roi_batches"
    elif reason_counts.get("candidate_delay_conflict", 0) > 0:
        primary = "inspect_delay_labels_and_false_delay_penalty_for_high_roi_batches"
    else:
        primary = "inspect_selected_threshold_rule"
    return {
        "primary": primary,
        "missed_reason_counts": dict(sorted(reason_counts.items())),
        "missed_family_counts": dict(sorted(family_counts.items())),
    }


def _assert_contracts(
    checkpoint_data: dict[str, Any],
    training: dict[str, Any],
    threshold: dict[str, Any],
    manifest: dict[str, Any],
) -> None:
    if checkpoint_data.get("target_label") != "same_context_batch_trajectory_roi":
        raise ValueError("batch-impact checkpoint target label mismatch")
    if checkpoint_data.get("exactness_contract") != BATCH_IMPACT_EXACTNESS_CONTRACT:
        raise ValueError("batch-impact exactness contract mismatch")
    if bool(checkpoint_data.get("training_contract", {}).get("production_ready")):
        raise ValueError("batch-impact checkpoint must be diagnostic-only")
    if training.get("schema_version") != "gat_batch_impact_training_summary_v1":
        raise ValueError("batch-impact training summary schema mismatch")
    if bool(training.get("production_ready")):
        raise ValueError("batch-impact training summary must not be production_ready")
    if threshold.get("schema_version") != "gat_batch_impact_threshold_frontier_v1":
        raise ValueError("threshold frontier summary schema mismatch")
    if bool(threshold.get("production_ready")):
        raise ValueError("threshold frontier must not be production_ready")
    if bool(threshold.get("runs_bpc_or_pricing")):
        raise ValueError("threshold frontier must not run BPC or pricing")
    if manifest.get("schema_version") != "gat_batch_impact_dataset_manifest_v1":
        raise ValueError("batch-impact dataset manifest schema mismatch")
    if not bool(manifest.get("diagnostic_only")):
        raise ValueError("batch-impact dataset must be diagnostic_only")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    opportunity = summary["opportunity_summary"]
    recommended = summary["recommended_next_step"]
    threshold = summary["selected_threshold"]
    lines = [
        "# GAT Batch Impact Opportunity Mining 报告",
        "",
        "日期：2026-06-16",
        "",
        "## 结论",
        "",
        "本报告在 validation split 上应用当前 best threshold，定位 high-ROI batch 是被接受还是被错过。",
        "它只做离线模型/阈值审计，不运行 BPC、pricing、RMP 或 certificate。",
        "",
        "```text",
        f"validation_record_count = {summary['validation_record_count']}",
        f"threshold_scope = {threshold.get('threshold_scope')}",
        f"threshold_mode = {threshold.get('threshold_mode')}",
        f"batch_threshold = {threshold.get('batch_threshold')}",
        f"candidate_threshold = {threshold.get('candidate_threshold')}",
        f"candidate_admission_score_mode = {threshold.get('candidate_admission_score_mode')}",
        f"candidate_delay_score_penalty = {threshold.get('candidate_delay_score_penalty')}",
        f"candidate_rescue_raw_score_threshold = {threshold.get('candidate_rescue_raw_score_threshold')}",
        f"candidate_rescue_delay_risk_threshold = {threshold.get('candidate_rescue_delay_risk_threshold')}",
        f"candidate_rescue_delay_score_penalty = {threshold.get('candidate_rescue_delay_score_penalty')}",
        f"candidate_delay_gate_enabled = {threshold.get('candidate_delay_gate_enabled')}",
        f"candidate_delay_risk_threshold = {threshold.get('candidate_delay_risk_threshold')}",
        f"family_delay_fallback_families = {threshold.get('family_delay_fallback_families')}",
        f"context_delay_fallback_contexts = {threshold.get('context_delay_fallback_contexts')}",
        f"accepted = {opportunity['accepted']}",
        f"high_roi_opportunities = {opportunity['high_roi_opportunities']}",
        f"accepted_high_roi_opportunities = {opportunity['accepted_high_roi_opportunities']}",
        f"missed_high_roi_opportunities = {opportunity['missed_high_roi_opportunities']}",
        f"accepted_high_roi_capture_rate = {opportunity['accepted_high_roi_capture_rate']}",
        f"accepted_low_roi_or_bad = {opportunity['accepted_low_roi_or_bad']}",
        f"recommended_primary = {recommended.get('primary')}",
        "production_ready = false",
        "selector_can_certificate = false",
        "```",
        "",
        "## Missed Reasons",
        "",
        "```json",
        json.dumps(opportunity["missed_reason_counts"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Family Summary",
        "",
        "```json",
        json.dumps(opportunity["family"], ensure_ascii=False, indent=2, sort_keys=True),
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


if __name__ == "__main__":
    raise SystemExit(main())
