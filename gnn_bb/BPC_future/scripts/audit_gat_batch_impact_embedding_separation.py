#!/usr/bin/env python3
"""Audit whether missed high-ROI batches are separable in GAT embedding space.

This is an offline diagnostic. It scores a frozen ``GATBatchImpactModel``,
applies the frozen deployment-facing thresholds, and compares missed high-ROI
validation batches against train-split high-ROI and low-ROI/bad neighbors in
the model embedding space. It never runs BPC, pricing, RMP, workers, or
certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.learning.batch_impact_model import (
    BATCH_IMPACT_EXACTNESS_CONTRACT,
    GATBatchImpactModel,
)
from BPC_future.scripts.audit_gat_batch_impact_knn_ood import (
    _candidate_prediction_indices,
    _score_dataset,
    _selected_thresholds,
)


DEFAULT_DATASET_DIR = Path(
    "BPC_future/data/gat_batch_impact/v15_mixed_v14_plus_exact_safe_hits_batch8_ab_roi_20260616"
)
DEFAULT_CHECKPOINT = Path(
    "BPC_future/results/gat_batch_impact_training_v15_exact_safe_hits_batch8_ab_roi_20260616/gat_batch_impact.pt"
)
DEFAULT_TRAINING_SUMMARY = Path(
    "BPC_future/results/gat_batch_impact_training_v15_exact_safe_hits_batch8_ab_roi_20260616/metrics.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_batch_impact_embedding_separation_v15_exact_safe_hits_batch8_ab_roi_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage3_v32_v15_embedding_separation_audit_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--training-summary", type=Path, default=DEFAULT_TRAINING_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--knn-k", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_embedding_separation(
        dataset_dir=Path(args.dataset_dir),
        checkpoint=Path(args.checkpoint),
        training_summary=Path(args.training_summary),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        device=str(args.device),
        knn_k=max(1, int(args.knn_k)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_embedding_separation(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    checkpoint: Path = DEFAULT_CHECKPOINT,
    training_summary: Path = DEFAULT_TRAINING_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    device: str = "cpu",
    knn_k: int = 5,
) -> dict[str, Any]:
    checkpoint_data = torch.load(checkpoint, map_location="cpu", weights_only=False)
    training = _read_json(Path(training_summary))
    manifest = _read_json(Path(dataset_dir) / "manifest.json")
    _assert_contracts(checkpoint_data, training, manifest)

    model = GATBatchImpactModel(**checkpoint_data["model_config"]).to(torch.device(device))
    model.load_state_dict(checkpoint_data["model_state_dict"])
    model.eval()
    records = _score_dataset(
        dataset_dir=Path(dataset_dir),
        manifest=manifest,
        model=model,
        device=torch.device(device),
    )
    split = training.get("split") or checkpoint_data.get("training_contract", {}).get("main_split") or {}
    train_instances = {str(instance) for instance in split.get("train_instances", [])}
    validation_instances = {str(instance) for instance in split.get("validation_instances", [])}
    train_records = [record for record in records if str(record["instance"]) in train_instances]
    validation_records = [
        record for record in records if str(record["instance"]) in validation_instances
    ]
    if not train_records or not validation_records:
        raise ValueError("training split does not match batch-impact dataset")

    thresholds = _selected_thresholds(training, checkpoint_data)
    min_roi = _min_accepted_batch_roi(training, checkpoint_data)
    separation_records = audit_embedding_separation_records(
        train_records=train_records,
        validation_records=validation_records,
        thresholds=thresholds,
        min_accepted_batch_roi=min_roi,
        knn_k=int(knn_k),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    records_path = output_dir / "validation_embedding_separation.jsonl"
    missed_path = output_dir / "missed_high_roi_embedding_separation.jsonl"
    _write_jsonl(records_path, separation_records)
    _write_jsonl(
        missed_path,
        [
            record
            for record in separation_records
            if bool(record.get("is_missed_high_roi_opportunity"))
        ],
    )

    summary = {
        "schema_version": "gat_batch_impact_embedding_separation_audit_v1",
        "status": "gat_batch_impact_embedding_separation_audited",
        "dataset_dir": str(dataset_dir),
        "checkpoint": str(checkpoint),
        "training_summary": str(training_summary),
        "output_dir": str(output_dir),
        "validation_embedding_separation_path": str(records_path),
        "missed_high_roi_embedding_separation_path": str(missed_path),
        "train_record_count": len(train_records),
        "validation_record_count": len(validation_records),
        "selected_threshold": thresholds,
        "min_accepted_batch_roi": float(min_roi),
        "knn_k": int(knn_k),
        "embedding_summary": summarize_embedding_separation(separation_records),
        "top_missed_high_roi": sorted(
            [
                record
                for record in separation_records
                if bool(record.get("is_missed_high_roi_opportunity"))
            ],
            key=lambda item: (
                float(item.get("accepted_batch_roi_label") or 0.0),
                -float(item.get("nearest_positive_distance") or 0.0),
            ),
            reverse=True,
        )[:25],
        "recommended_next_step": _recommended_next_step(separation_records),
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


def audit_embedding_separation_records(
    *,
    train_records: list[dict[str, Any]],
    validation_records: list[dict[str, Any]],
    thresholds: dict[str, Any],
    min_accepted_batch_roi: float,
    knn_k: int = 5,
) -> list[dict[str, Any]]:
    scaler = _embedding_scaler([record["embedding"] for record in train_records])
    scaled_train = [
        {
            **record,
            "scaled_embedding": _scale_embedding(record["embedding"], scaler),
            "is_high_roi_opportunity": _is_high_roi_opportunity(
                record,
                min_accepted_batch_roi=min_accepted_batch_roi,
            ),
            "accepted": _record_is_accepted(record, thresholds=thresholds),
        }
        for record in train_records
    ]
    rows: list[dict[str, Any]] = []
    for record in validation_records:
        accepted = _record_is_accepted(record, thresholds=thresholds)
        high_roi = _is_high_roi_opportunity(
            record,
            min_accepted_batch_roi=min_accepted_batch_roi,
        )
        query = _scale_embedding(record["embedding"], scaler)
        neighbor_stats = _neighbor_stats(query, scaled_train, knn_k=max(1, int(knn_k)))
        candidate_threshold = float(thresholds.get("candidate_threshold", 0.0))
        max_candidate_score = max([float(score) for score in record.get("candidate_scores", [])] or [0.0])
        row = {
            "instance": str(record.get("instance") or ""),
            "sample_path": str(record.get("sample_path") or ""),
            "context_hash": str(record.get("context_hash") or ""),
            "family": str(record.get("instance_family") or "unknown"),
            "task_count": int(float(record.get("instance_task_count") or 0)),
            "accepted": bool(accepted),
            "is_high_roi_opportunity": bool(high_roi),
            "is_accepted_high_roi_opportunity": bool(high_roi and accepted),
            "is_missed_high_roi_opportunity": bool(high_roi and not accepted),
            "is_accepted_low_roi_or_bad": bool(accepted and not high_roi),
            "accepted_batch_roi_label": float(record.get("accepted_batch_roi_label") or 0.0),
            "batch_score": float(record.get("batch_score") or 0.0),
            "candidate_threshold": candidate_threshold,
            "max_candidate_score": float(max_candidate_score),
            "max_candidate_score_margin": float(max_candidate_score - candidate_threshold),
            "candidate_count": len(record.get("candidate_scores", []) or []),
            **neighbor_stats,
        }
        rows.append(row)
    return rows


def summarize_embedding_separation(records: list[dict[str, Any]]) -> dict[str, Any]:
    high_roi = [record for record in records if bool(record.get("is_high_roi_opportunity"))]
    accepted_high_roi = [
        record for record in records if bool(record.get("is_accepted_high_roi_opportunity"))
    ]
    missed_high_roi = [
        record for record in records if bool(record.get("is_missed_high_roi_opportunity"))
    ]
    accepted_low = [record for record in records if bool(record.get("is_accepted_low_roi_or_bad"))]
    return {
        "records": len(records),
        "high_roi_opportunities": len(high_roi),
        "accepted_high_roi_opportunities": len(accepted_high_roi),
        "missed_high_roi_opportunities": len(missed_high_roi),
        "accepted_low_roi_or_bad": len(accepted_low),
        "missed_nearest_negative_closer_count": sum(
            int(bool(record.get("nearest_negative_closer"))) for record in missed_high_roi
        ),
        "missed_knn_positive_fraction_mean": _mean_or_none(
            [float(record.get("knn_positive_fraction") or 0.0) for record in missed_high_roi]
        ),
        "missed_knn_positive_fraction_median": _median_or_none(
            [float(record.get("knn_positive_fraction") or 0.0) for record in missed_high_roi]
        ),
        "accepted_high_roi_knn_positive_fraction_mean": _mean_or_none(
            [float(record.get("knn_positive_fraction") or 0.0) for record in accepted_high_roi]
        ),
        "accepted_high_roi_knn_positive_fraction_median": _median_or_none(
            [float(record.get("knn_positive_fraction") or 0.0) for record in accepted_high_roi]
        ),
        "missed_nearest_positive_distance_mean": _mean_or_none(
            [
                float(record["nearest_positive_distance"])
                for record in missed_high_roi
                if record.get("nearest_positive_distance") is not None
            ]
        ),
        "missed_nearest_negative_distance_mean": _mean_or_none(
            [
                float(record["nearest_negative_distance"])
                for record in missed_high_roi
                if record.get("nearest_negative_distance") is not None
            ]
        ),
        "accepted_high_roi_nearest_positive_distance_mean": _mean_or_none(
            [
                float(record["nearest_positive_distance"])
                for record in accepted_high_roi
                if record.get("nearest_positive_distance") is not None
            ]
        ),
        "family": _family_summary(records),
        "task_count_counts": dict(
            sorted(Counter(str(record.get("task_count") or 0) for record in records).items())
        ),
    }


def _record_is_accepted(record: dict[str, Any], *, thresholds: dict[str, Any]) -> bool:
    family = str(record.get("instance_family") or "unknown")
    batch_threshold = float(
        dict(thresholds.get("batch_thresholds_by_family") or {}).get(
            family,
            thresholds.get("batch_threshold", thresholds.get("threshold", 0.0)),
        )
    )
    if float(record.get("batch_score") or 0.0) < batch_threshold:
        return False
    if family in {str(value) for value in thresholds.get("family_delay_fallback_families", [])}:
        return False
    if str(record.get("context_hash") or "") in {
        str(value) for value in thresholds.get("context_delay_fallback_contexts", [])
    }:
        return False
    predicted, _, _, _, _ = _candidate_prediction_indices(
        record,
        candidate_threshold=float(thresholds.get("candidate_threshold", batch_threshold)),
        candidate_admission_score_mode=str(
            thresholds.get("candidate_admission_score_mode", "high_priority") or "high_priority"
        ),
        candidate_delay_score_penalty=float(thresholds.get("candidate_delay_score_penalty", 0.0)),
        candidate_delay_gate_enabled=bool(thresholds.get("candidate_delay_gate_enabled", False)),
        candidate_delay_risk_threshold=float(thresholds.get("candidate_delay_risk_threshold", 1.0)),
        candidate_rescue_raw_score_threshold=float(
            thresholds.get("candidate_rescue_raw_score_threshold", 1.0)
        ),
        candidate_rescue_delay_risk_threshold=float(
            thresholds.get("candidate_rescue_delay_risk_threshold", 1.0)
        ),
        candidate_rescue_delay_score_penalty=float(
            thresholds.get("candidate_rescue_delay_score_penalty", 0.0)
        ),
    )
    delay_labels = [int(value) for value in record.get("candidate_delay_labels", [])]
    predicted_delay = any(idx < len(delay_labels) and int(delay_labels[idx]) for idx in predicted)
    return bool(predicted and not predicted_delay)


def _is_high_roi_opportunity(record: dict[str, Any], *, min_accepted_batch_roi: float) -> bool:
    return (
        float(record.get("accepted_batch_roi_label") or 0.0) >= float(min_accepted_batch_roi)
        and int(record.get("bad_mode_switch") or 0) == 0
    )


def _neighbor_stats(
    query: list[float],
    train_records: list[dict[str, Any]],
    *,
    knn_k: int,
) -> dict[str, Any]:
    distances = [
        (_distance(query, record["scaled_embedding"]), record)
        for record in train_records
    ]
    distances.sort(key=lambda item: item[0])
    neighbors = distances[: max(1, int(knn_k))]
    positive_neighbors = [
        (distance, record)
        for distance, record in distances
        if bool(record.get("is_high_roi_opportunity"))
    ]
    negative_neighbors = [
        (distance, record)
        for distance, record in distances
        if not bool(record.get("is_high_roi_opportunity"))
    ]
    nearest_positive = positive_neighbors[0] if positive_neighbors else None
    nearest_negative = negative_neighbors[0] if negative_neighbors else None
    positive_fraction = (
        sum(int(bool(record.get("is_high_roi_opportunity"))) for _, record in neighbors)
        / float(len(neighbors))
        if neighbors
        else 0.0
    )
    accepted_positive_fraction = (
        sum(
            int(bool(record.get("accepted")) and bool(record.get("is_high_roi_opportunity")))
            for _, record in neighbors
        )
        / float(len(neighbors))
        if neighbors
        else 0.0
    )
    return {
        "knn_positive_fraction": float(positive_fraction),
        "knn_accepted_positive_fraction": float(accepted_positive_fraction),
        "nearest_positive_distance": None if nearest_positive is None else float(nearest_positive[0]),
        "nearest_negative_distance": None if nearest_negative is None else float(nearest_negative[0]),
        "nearest_negative_closer": bool(
            nearest_positive is not None
            and nearest_negative is not None
            and float(nearest_negative[0]) < float(nearest_positive[0])
        ),
        "nearest_positive_family": (
            None if nearest_positive is None else str(nearest_positive[1].get("instance_family") or "unknown")
        ),
        "nearest_negative_family": (
            None if nearest_negative is None else str(nearest_negative[1].get("instance_family") or "unknown")
        ),
        "nearest_positive_candidate_score": (
            None
            if nearest_positive is None
            else max([float(score) for score in nearest_positive[1].get("candidate_scores", [])] or [0.0])
        ),
        "nearest_negative_candidate_score": (
            None
            if nearest_negative is None
            else max([float(score) for score in nearest_negative[1].get("candidate_scores", [])] or [0.0])
        ),
    }


def _embedding_scaler(vectors: list[list[float]]) -> dict[str, list[float]]:
    if not vectors:
        raise ValueError("cannot fit embedding scaler without vectors")
    width = len(vectors[0])
    if any(len(vector) != width for vector in vectors):
        raise ValueError("embedding vectors must have stable width")
    means = [sum(float(vector[idx]) for vector in vectors) / float(len(vectors)) for idx in range(width)]
    scales: list[float] = []
    for idx in range(width):
        variance = sum((float(vector[idx]) - means[idx]) ** 2 for vector in vectors) / float(len(vectors))
        scale = math.sqrt(variance)
        scales.append(scale if scale > 1.0e-12 else 1.0)
    return {"mean": means, "scale": scales}


def _scale_embedding(vector: list[float], scaler: dict[str, list[float]]) -> list[float]:
    return [
        (float(value) - float(mean)) / float(scale)
        for value, mean, scale in zip(vector, scaler["mean"], scaler["scale"])
    ]


def _distance(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("embedding distance requires equal vector widths")
    if not left:
        return 0.0
    return math.sqrt(sum((float(a) - float(b)) ** 2 for a, b in zip(left, right)) / float(len(left)))


def _family_summary(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    family: dict[str, dict[str, Any]] = {}
    for record in records:
        name = str(record.get("family") or record.get("instance_family") or "unknown")
        row = family.setdefault(
            name,
            {
                "records": 0,
                "high_roi_opportunities": 0,
                "accepted_high_roi_opportunities": 0,
                "missed_high_roi_opportunities": 0,
                "accepted_low_roi_or_bad": 0,
                "missed_nearest_negative_closer_count": 0,
            },
        )
        row["records"] += 1
        row["high_roi_opportunities"] += int(bool(record.get("is_high_roi_opportunity")))
        row["accepted_high_roi_opportunities"] += int(
            bool(record.get("is_accepted_high_roi_opportunity"))
        )
        row["missed_high_roi_opportunities"] += int(
            bool(record.get("is_missed_high_roi_opportunity"))
        )
        row["accepted_low_roi_or_bad"] += int(bool(record.get("is_accepted_low_roi_or_bad")))
        row["missed_nearest_negative_closer_count"] += int(
            bool(record.get("is_missed_high_roi_opportunity"))
            and bool(record.get("nearest_negative_closer"))
        )
    return dict(sorted(family.items()))


def _recommended_next_step(records: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize_embedding_separation(records)
    missed = [record for record in records if bool(record.get("is_missed_high_roi_opportunity"))]
    if not missed:
        return {"primary": "no_missed_high_roi_embedding_blocker"}
    negative_closer = int(summary["missed_nearest_negative_closer_count"])
    positive_fraction = summary.get("missed_knn_positive_fraction_mean")
    if negative_closer >= max(1, len(missed) // 2):
        primary = "collect_context_local_positive_negative_pairs_or_add_embedding_contrast"
    elif positive_fraction is not None and float(positive_fraction) >= 0.5:
        primary = "candidate_head_under_scores_structurally_near_positive_neighbors"
    else:
        primary = "increase_candidate_representation_capacity_or_collect_same_context_contrast"
    return {
        "primary": primary,
        "missed_high_roi_opportunities": len(missed),
        "missed_nearest_negative_closer_count": negative_closer,
        "missed_knn_positive_fraction_mean": positive_fraction,
    }


def _min_accepted_batch_roi(training: dict[str, Any], checkpoint_data: dict[str, Any]) -> float:
    metrics = training.get("validation_deployment_metrics") or {}
    gate = checkpoint_data.get("deployment_gate", {}).get("gate_config") or {}
    return float(
        metrics.get(
            "min_accepted_batch_roi",
            gate.get("min_accepted_batch_roi", training.get("hard_roi_threshold", 0.65)),
        )
    )


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


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records)
        + ("\n" if records else ""),
        encoding="utf-8",
    )


def _mean_or_none(values: list[float]) -> float | None:
    return None if not values else float(mean(values))


def _median_or_none(values: list[float]) -> float | None:
    return None if not values else float(median(values))


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stats = summary["embedding_summary"]
    recommended = summary["recommended_next_step"]
    lines = [
        "# GAT Batch Impact Embedding Separation Audit 报告",
        "",
        "日期：2026-06-16",
        "",
        "## 结论",
        "",
        "本报告只做离线 embedding / kNN 结构审计，用来判断 missed high-ROI 是分数阈值边界问题，还是模型表示空间中与低 ROI / bad 样本混杂。",
        "它不运行 BPC、pricing、RMP、worker 或 certificate。",
        "",
        "```text",
        f"train_record_count = {summary['train_record_count']}",
        f"validation_record_count = {summary['validation_record_count']}",
        f"candidate_threshold = {summary['selected_threshold'].get('candidate_threshold')}",
        f"knn_k = {summary['knn_k']}",
        f"high_roi_opportunities = {stats['high_roi_opportunities']}",
        f"accepted_high_roi_opportunities = {stats['accepted_high_roi_opportunities']}",
        f"missed_high_roi_opportunities = {stats['missed_high_roi_opportunities']}",
        f"accepted_low_roi_or_bad = {stats['accepted_low_roi_or_bad']}",
        f"missed_nearest_negative_closer_count = {stats['missed_nearest_negative_closer_count']}",
        f"missed_knn_positive_fraction_mean = {stats['missed_knn_positive_fraction_mean']}",
        f"accepted_high_roi_knn_positive_fraction_mean = {stats['accepted_high_roi_knn_positive_fraction_mean']}",
        f"recommended_primary = {recommended.get('primary')}",
        "diagnostic_only = true",
        "runs_bpc_or_pricing = false",
        "selector_can_certificate = false",
        "```",
        "",
        "## Family Summary",
        "",
        "```json",
        json.dumps(stats["family"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Top Missed High-ROI",
        "",
        "```json",
        json.dumps(summary["top_missed_high_roi"][:10], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
