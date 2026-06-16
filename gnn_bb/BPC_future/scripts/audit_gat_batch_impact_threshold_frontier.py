#!/usr/bin/env python3
"""Audit the full GAT batch-impact threshold frontier.

This script is offline/diagnostic-only.  It loads an existing
``GATBatchImpactModel`` checkpoint, scores the dataset split recorded by the
training summary, and materializes threshold metrics plus reject reasons.  It
does not run BPC, pricing, RMP, workers, or certificate logic.
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
from BPC_future.scripts.train_gat_batch_impact import (
    _candidate_admission_scores,
    _deployment_metrics,
    _family_delay_fallback_threshold_metrics,
    _family_local_threshold_metrics,
    _load_sample,
    _normalize_sample,
    _prediction_records,
    _threshold_values,
    _wilson_ci_low,
)


DEFAULT_DATASET_DIR = Path("BPC_future/data/gat_batch_impact/v3_signature_20260616")
DEFAULT_CHECKPOINT = Path("BPC_future/data/gat_batch_impact/v3_signature_20260616/gat_batch_impact.pt")
DEFAULT_TRAINING_SUMMARY = Path("BPC_future/results/gat_batch_impact_training_v3_signature_20260616/summary.json")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_batch_impact_threshold_frontier_v3_signature_20260616")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_batch_impact_threshold_frontier_v3_signature_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--training-summary", type=Path, default=DEFAULT_TRAINING_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--max-dynamic-thresholds", type=int, default=128)
    parser.add_argument("--top-k", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_threshold_frontier(
        dataset_dir=args.dataset_dir,
        checkpoint=args.checkpoint,
        training_summary=args.training_summary,
        output_dir=args.output_dir,
        report=args.report,
        device=str(args.device),
        max_dynamic_thresholds=max(1, int(args.max_dynamic_thresholds)),
        top_k=max(1, int(args.top_k)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_threshold_frontier(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    checkpoint: Path = DEFAULT_CHECKPOINT,
    training_summary: Path = DEFAULT_TRAINING_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    device: str = "cpu",
    max_dynamic_thresholds: int = 128,
    top_k: int = 20,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    checkpoint_data = torch.load(checkpoint, map_location="cpu", weights_only=False)
    training = _read_json(Path(training_summary))
    manifest = _read_json(dataset_dir / "manifest.json")
    _assert_contracts(checkpoint_data, training, manifest)

    model = GATBatchImpactModel(**checkpoint_data["model_config"]).to(torch.device(device))
    model.load_state_dict(checkpoint_data["model_state_dict"])
    model.eval()
    samples = [
        _normalize_sample(_load_sample(dataset_dir / item["path"]), manifest)
        for item in manifest.get("samples", [])
    ]
    all_records = _prediction_records(model, samples, torch.device(device))
    record_items = [
        (
            str(
                getattr(sample, "batch_impact_instance_path", "")
                or getattr(sample, "batch_impact_instance", "")
            ),
            record,
        )
        for sample, record in zip(samples, all_records)
    ]
    split = training.get("split") or checkpoint_data.get("training_contract", {}).get("main_split") or {}
    train_records, validation_records = records_for_split(
        record_items,
        train_instances={str(instance) for instance in split.get("train_instances", [])},
        validation_instances={str(instance) for instance in split.get("validation_instances", [])},
    )
    if not train_records or not validation_records:
        raise ValueError("training split does not match threshold-frontier dataset")

    gate_config = dict(checkpoint_data.get("deployment_gate", {}).get("gate_config") or {})
    if not gate_config:
        raise ValueError("checkpoint is missing deployment_gate.gate_config")
    frontier = evaluate_threshold_frontier_records(
        validation_records,
        gate_config=gate_config,
        max_dynamic_thresholds=int(max_dynamic_thresholds),
    )
    train_selected = _deployment_metrics(
        train_records,
        batch_threshold=float(frontier["best_candidate"]["batch_threshold"]),
        candidate_threshold=float(frontier["best_candidate"]["candidate_threshold"]),
        gate_config=gate_config,
        batch_thresholds_by_family=dict(frontier["best_candidate"].get("batch_thresholds_by_family") or {}),
        delay_fallback_families=list(frontier["best_candidate"].get("family_delay_fallback_families") or []),
        context_delay_fallback_contexts=list(
            frontier["best_candidate"].get("context_delay_fallback_contexts") or []
        ),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    global_path = output_dir / "frontier_global.jsonl"
    family_path = output_dir / "frontier_family_local.jsonl"
    fallback_path = output_dir / "frontier_family_delay_fallback.jsonl"
    global_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in frontier["global_rows"])
        + ("\n" if frontier["global_rows"] else ""),
        encoding="utf-8",
    )
    family_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in frontier["family_local_rows"])
        + ("\n" if frontier["family_local_rows"] else ""),
        encoding="utf-8",
    )
    fallback_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in frontier["family_delay_fallback_rows"])
        + ("\n" if frontier["family_delay_fallback_rows"] else ""),
        encoding="utf-8",
    )
    summary = {
        "schema_version": "gat_batch_impact_threshold_frontier_v1",
        "status": "gat_batch_impact_threshold_frontier_audited",
        "dataset_dir": str(dataset_dir),
        "checkpoint": str(checkpoint),
        "training_summary": str(training_summary),
        "output_dir": str(output_dir),
        "frontier_global_path": str(global_path),
        "frontier_family_local_path": str(family_path),
        "frontier_family_delay_fallback_path": str(fallback_path),
        "sample_count": int(manifest.get("sample_count") or 0),
        "candidate_count": int(manifest.get("candidate_count") or 0),
        "train_record_count": len(train_records),
        "validation_record_count": len(validation_records),
        "candidate_signature_source_coverage": manifest.get("candidate_signature_source_coverage"),
        "gate_config": gate_config,
        "global_frontier_count": len(frontier["global_rows"]),
        "family_local_frontier_count": len(frontier["family_local_rows"]),
        "family_delay_fallback_frontier_count": len(frontier["family_delay_fallback_rows"]),
        "feasible_threshold_count": int(frontier["feasible_threshold_count"]),
        "checkpoint_feasible_threshold_count": int(frontier["checkpoint_feasible_threshold_count"]),
        "local_reject_reason_counts": frontier["local_reject_reason_counts"],
        "checkpoint_reject_reason_counts": frontier["checkpoint_reject_reason_counts"],
        "best_candidate": frontier["best_candidate"],
        "best_global_candidate": frontier["best_global_candidate"],
        "best_family_local_candidate": frontier["best_family_local_candidate"],
        "best_family_delay_fallback_candidate": frontier["best_family_delay_fallback_candidate"],
        "top_candidates": frontier["top_candidates"][: int(top_k)],
        "train_metrics_at_best_candidate": _compact_metric_row(train_selected),
        "min_all_success_samples_needed": _min_all_success_samples_needed(gate_config),
        "diagnosis": _diagnosis(frontier),
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


def evaluate_threshold_frontier_records(
    records: list[dict[str, Any]],
    *,
    gate_config: dict[str, Any],
    max_dynamic_thresholds: int = 128,
) -> dict[str, Any]:
    grid = {0.0, 0.5, 0.65, 0.75, 0.85, 0.9, 0.95, 0.99, 1.0}
    batch_scores = [float(record["batch_score"]) for record in records]
    candidate_scores = [
        float(score)
        for record in records
        for score in _candidate_admission_scores(record, gate_config=gate_config)
    ]
    batch_thresholds = _threshold_values(
        batch_scores,
        grid=grid,
        max_dynamic=int(max_dynamic_thresholds),
    )
    candidate_thresholds = _threshold_values(
        candidate_scores,
        grid=grid,
        max_dynamic=int(max_dynamic_thresholds),
    )
    global_metrics = [
        _deployment_metrics(
            records,
            batch_threshold=float(batch_threshold),
            candidate_threshold=float(candidate_threshold),
            gate_config=gate_config,
        )
        for batch_threshold in batch_thresholds
        for candidate_threshold in candidate_thresholds
    ]
    family_local_metrics = _family_local_threshold_metrics(
        records,
        candidate_thresholds=candidate_thresholds,
        gate_config=gate_config,
    )
    family_delay_fallback_metrics = _family_delay_fallback_threshold_metrics(
        records,
        evaluated=[*global_metrics, *family_local_metrics],
        gate_config=gate_config,
    )
    global_rows = [
        _frontier_row(
            metrics,
            scope="global",
        )
        for metrics in global_metrics
    ]
    family_local_rows = [
        _frontier_row(row, scope="family_local")
        for row in family_local_metrics
    ]
    family_delay_fallback_rows = [
        _frontier_row(row, scope="family_delay_fallback")
        for row in family_delay_fallback_metrics
    ]
    rows = [*global_rows, *family_local_rows, *family_delay_fallback_rows]
    feasible = [row for row in rows if bool(row["threshold_local_gate_pass"])]
    checkpoint_feasible = [row for row in rows if bool(row["checkpoint_gate_pass"])]
    best_candidate = _best_candidate(rows)
    best_global_candidate = _best_candidate(global_rows)
    best_family_local_candidate = _best_candidate(family_local_rows)
    best_family_delay_fallback_candidate = _best_candidate(family_delay_fallback_rows)
    local_reject_counts = Counter(
        reason
        for row in rows
        for reason in row.get("threshold_local_reject_reasons", [])
    )
    checkpoint_reject_counts = Counter(
        reason
        for row in rows
        for reason in row.get("checkpoint_gate_reject_reasons", [])
    )
    top_candidates = sorted(rows, key=_frontier_sort_key, reverse=True)[:50]
    return {
        "global_rows": global_rows,
        "family_local_rows": family_local_rows,
        "family_delay_fallback_rows": family_delay_fallback_rows,
        "global_frontier_count": len(global_rows),
        "family_local_frontier_count": len(family_local_rows),
        "family_delay_fallback_frontier_count": len(family_delay_fallback_rows),
        "feasible_threshold_count": len(feasible),
        "checkpoint_feasible_threshold_count": len(checkpoint_feasible),
        "best_candidate": best_candidate,
        "best_global_candidate": best_global_candidate,
        "best_family_local_candidate": best_family_local_candidate,
        "best_family_delay_fallback_candidate": best_family_delay_fallback_candidate,
        "top_candidates": top_candidates,
        "local_reject_reason_counts": dict(sorted(local_reject_counts.items())),
        "checkpoint_reject_reason_counts": dict(sorted(checkpoint_reject_counts.items())),
    }


def records_for_split(
    record_items: list[tuple[str, dict[str, Any]]],
    *,
    train_instances: set[str],
    validation_instances: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    train_records = [
        record
        for instance, record in record_items
        if str(instance) in train_instances
    ]
    validation_records = [
        record
        for instance, record in record_items
        if str(instance) in validation_instances
    ]
    return train_records, validation_records


def _frontier_row(metrics: dict[str, Any], *, scope: str) -> dict[str, Any]:
    row = _compact_metric_row(metrics)
    row["threshold_scope"] = str(scope)
    return row


def _compact_metric_row(metrics: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "threshold_mode",
        "threshold",
        "batch_threshold",
        "candidate_threshold",
        "candidate_admission_score_mode",
        "candidate_delay_score_penalty",
        "candidate_delay_gate_enabled",
        "candidate_delay_risk_threshold",
        "candidate_delay_gate_blocked_count",
        "candidate_risk_adjusted_suppressed_count",
        "batch_thresholds_by_family",
        "family_delay_fallback_families",
        "context_delay_fallback_contexts",
        "total_batches",
        "accepted_batch_count",
        "accepted_batch_rate",
        "accepted_batch_roi",
        "accepted_batch_roi_ci_low",
        "accepted_batch_roi_over_baseline",
        "accepted_batch_roi_over_baseline_ci_low",
        "safe_precision",
        "safe_precision_ci_low",
        "high_priority_prediction_count",
        "high_priority_true_positive_count",
        "high_priority_precision",
        "high_priority_precision_ci_low",
        "false_high_priority_on_delay_count",
        "delay_label_count",
        "false_high_priority_on_delay",
        "false_safe_rate_label_unsafe",
        "false_safe_rate_union",
        "coverage_non_ood",
        "delay_rate",
        "expected_trajectory_utility",
        "family_holdout_min_precision",
        "family_holdout_min_accepted_roi",
        "family_holdout_missing_accepted_families",
        "family_holdout_missing_accepted_opportunity_families",
        "family_specific_delay_fallback_families",
        "family_holdout_oracle_high_roi_families",
        "checkpoint_gate_pass",
        "checkpoint_gate_reject_reasons",
        "threshold_local_gate_pass",
        "threshold_local_reject_reasons",
    )
    return {key: metrics.get(key) for key in keys if key in metrics}


def _best_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    return max(rows, key=_frontier_sort_key)


def _frontier_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        bool(row.get("threshold_local_gate_pass")),
        -len(row.get("threshold_local_reject_reasons", [])),
        _none_to_negative(row.get("safe_precision_ci_low")),
        _none_to_negative(row.get("accepted_batch_roi_ci_low")),
        _none_to_negative(row.get("safe_precision")),
        _none_to_negative(row.get("accepted_batch_roi")),
        int(row.get("accepted_batch_count") or 0),
        _none_to_negative(row.get("expected_trajectory_utility")),
        -len(row.get("family_delay_fallback_families", [])),
        -len(row.get("context_delay_fallback_contexts", [])),
        -float(row.get("false_high_priority_on_delay") or 0.0),
        -float(row.get("batch_threshold") or 0.0),
        -float(row.get("candidate_threshold") or 0.0),
    )


def _none_to_negative(value: Any) -> float:
    if value is None:
        return -1.0
    return float(value)


def _min_all_success_samples_needed(gate_config: dict[str, Any]) -> dict[str, Any]:
    z = float(gate_config.get("confidence_z", 1.96))
    return {
        "high_priority_precision_ci_low_target": gate_config.get("min_high_priority_precision_ci_low"),
        "high_priority_all_success_count": _min_all_successes_for_wilson(
            gate_config.get("min_high_priority_precision_ci_low"),
            z=z,
        ),
        "safe_precision_ci_low_target": gate_config.get("min_safe_precision_ci_low"),
        "safe_all_success_count": _min_all_successes_for_wilson(
            gate_config.get("min_safe_precision_ci_low"),
            z=z,
        ),
    }


def _min_all_successes_for_wilson(target: Any, *, z: float) -> int | None:
    if target is None:
        return None
    target_value = float(target)
    for count in range(1, 10001):
        low = _wilson_ci_low(count, count, z=z)
        if low is not None and low >= target_value:
            return count
    return None


def _diagnosis(frontier: dict[str, Any]) -> dict[str, Any]:
    best = dict(frontier.get("best_candidate") or {})
    local_counts = dict(frontier.get("local_reject_reason_counts") or {})
    if int(frontier.get("feasible_threshold_count") or 0) > 0:
        primary = "has_local_feasible_threshold"
    elif "safe_precision_ci_low_below_threshold_or_not_measurable" in local_counts:
        primary = "confidence_lower_bound_sample_size_or_acceptance_count_blocker"
    elif "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable" in local_counts:
        primary = "accepted_roi_confidence_blocker"
    elif "false_high_priority_on_delay_too_high" in local_counts:
        primary = "model_ranking_false_delay_blocker"
    else:
        primary = "no_local_feasible_threshold"
    return {
        "primary_blocker": primary,
        "best_accepted_batch_count": int(best.get("accepted_batch_count") or 0),
        "best_safe_precision_ci_low": best.get("safe_precision_ci_low"),
        "best_accepted_batch_roi_ci_low": best.get("accepted_batch_roi_ci_low"),
        "best_local_reject_reasons": best.get("threshold_local_reject_reasons", []),
    }


def _assert_contracts(
    checkpoint_data: dict[str, Any],
    training: dict[str, Any],
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
    if manifest.get("schema_version") != "gat_batch_impact_dataset_manifest_v1":
        raise ValueError("batch-impact dataset manifest schema mismatch")
    if not bool(manifest.get("diagnostic_only")):
        raise ValueError("batch-impact dataset must be diagnostic_only")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    best = summary["best_candidate"]
    best_fallback = summary.get("best_family_delay_fallback_candidate") or {}
    lines = [
        "# GAT Batch Impact Threshold Frontier 报告",
        "",
        "日期：2026-06-16",
        "",
        "## 结论",
        "",
        "本报告展开 Stage 3 checkpoint 的 threshold frontier，用同一套 deployment gate",
        "检查 precision / ROI / safety / coverage。该流程只做离线审计，不运行 BPC、",
        "pricing、RMP 或 certificate。",
        "",
        "```text",
        f"global_frontier_count = {summary['global_frontier_count']}",
        f"family_local_frontier_count = {summary['family_local_frontier_count']}",
        f"family_delay_fallback_frontier_count = {summary['family_delay_fallback_frontier_count']}",
        f"feasible_threshold_count = {summary['feasible_threshold_count']}",
        f"checkpoint_feasible_threshold_count = {summary['checkpoint_feasible_threshold_count']}",
        f"primary_blocker = {summary['diagnosis']['primary_blocker']}",
        f"best_accepted_batch_count = {best.get('accepted_batch_count')}",
        f"candidate_admission_score_mode = {best.get('candidate_admission_score_mode')}",
        f"candidate_delay_score_penalty = {best.get('candidate_delay_score_penalty')}",
        f"candidate_delay_gate_enabled = {best.get('candidate_delay_gate_enabled')}",
        f"candidate_delay_risk_threshold = {best.get('candidate_delay_risk_threshold')}",
        f"candidate_delay_gate_blocked_count = {best.get('candidate_delay_gate_blocked_count')}",
        f"candidate_risk_adjusted_suppressed_count = {best.get('candidate_risk_adjusted_suppressed_count')}",
        f"best_family_delay_fallback_families = {best.get('family_delay_fallback_families')}",
        f"best_context_delay_fallback_contexts = {best.get('context_delay_fallback_contexts')}",
        f"best_safe_precision_ci_low = {best.get('safe_precision_ci_low')}",
        f"best_accepted_batch_roi_ci_low = {best.get('accepted_batch_roi_ci_low')}",
        f"best_local_reject_reasons = {best.get('threshold_local_reject_reasons')}",
        f"best_fallback_accepted_batch_count = {best_fallback.get('accepted_batch_count')}",
        f"best_fallback_safe_precision_ci_low = {best_fallback.get('safe_precision_ci_low')}",
        f"best_fallback_accepted_batch_roi_ci_low = {best_fallback.get('accepted_batch_roi_ci_low')}",
        f"best_fallback_delay_families = {best_fallback.get('family_delay_fallback_families')}",
        f"best_fallback_delay_contexts = {best_fallback.get('context_delay_fallback_contexts')}",
        f"best_fallback_reject_reasons = {best_fallback.get('threshold_local_reject_reasons')}",
        "production_ready = false",
        "selector_can_certificate = false",
        "```",
        "",
        "## Reject Reason Counts",
        "",
        "```json",
        json.dumps(
            {
                "local_reject_reason_counts": summary["local_reject_reason_counts"],
                "checkpoint_reject_reason_counts": summary["checkpoint_reject_reason_counts"],
                "min_all_success_samples_needed": summary["min_all_success_samples_needed"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
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
