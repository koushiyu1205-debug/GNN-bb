#!/usr/bin/env python3
"""Build the v107 optimized target-mode sample-expansion artifacts.

This is an offline data-contract builder.  It reads an existing
``gat_batch_impact`` graph dataset and expands each candidate observation into
target-level rows, batch rows, same-context hard-pair rows, and the manifests
required by ``gat_target_mode_targeted_sample_expansion_plan_v107_optimized``.

Exactness boundary:
* does not run BPC, pricing, RMP, workers, or certificates;
* does not train a model and does not enable GAT online;
* does not use kNN/OOD audit fields as model inputs;
* true-RC negative delay rows remain delay evidence, not reject evidence.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch


DEFAULT_DATASET_DIR = Path("BPC_future/data/gat_batch_impact/v75_v66_path_tokens_slack_20260617")
DEFAULT_OUTPUT_DIR = Path(
    f"BPC_future/results/gat_target_mode_targeted_sample_expansion_v107_optimized_{date.today():%Y%m%d}"
)
SCHEMA_VERSION = "gat_target_mode_targeted_sample_expansion_v107_optimized"
LABEL_THRESHOLD_MANIFEST_ID = "label_threshold_manifest_v107_optimized_default"


SCALE_TARGETS: dict[int, int] = {20: 2500, 30: 500, 50: 1000, 100: 1000}
FAMILY_TARGETS: dict[str, int] = {
    "sector-wave": 2000,
    "random-wave": 1800,
    "greedy-anchor": 1200,
}
FAMILY_SCALE_TARGETS: dict[tuple[int, str], int] = {
    (20, "sector-wave"): 1000,
    (20, "random-wave"): 900,
    (20, "greedy-anchor"): 600,
    (30, "sector-wave"): 175,
    (30, "random-wave"): 200,
    (30, "greedy-anchor"): 125,
    (50, "sector-wave"): 425,
    (50, "random-wave"): 350,
    (50, "greedy-anchor"): 225,
    (100, "sector-wave"): 400,
    (100, "random-wave"): 350,
    (100, "greedy-anchor"): 250,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-effective-target-rows", type=int, default=5000)
    parser.add_argument("--min-effective-batch-samples", type=int, default=500)
    parser.add_argument("--min-effective-hard-pairs", type=int, default=1200)
    parser.add_argument("--min-unique-contexts", type=int, default=350)
    parser.add_argument("--min-level-ab-target-rows", type=int, default=1500)
    parser.add_argument("--min-level-ab-hard-pairs", type=int, default=500)
    parser.add_argument("--min-task20-level-ab-target-rows", type=int, default=800)
    parser.add_argument("--min-task20-hard-pairs", type=int, default=600)
    parser.add_argument("--max-level-c-weak-rows", type=int, default=3500)
    parser.add_argument("--max-level-c-only-hard-pair-ratio", type=float, default=0.40)
    parser.add_argument("--true-rc-negative-eps", type=float, default=1.0e-9)
    parser.add_argument("--min-positive-primal-roi", type=float, default=0.65)
    parser.add_argument("--max-low-roi-primal-roi", type=float, default=0.65)
    parser.add_argument("--min-hard-pair-roi-gap", type=float, default=0.65)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_targeted_sample_expansion(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        min_effective_target_rows=max(1, int(args.min_effective_target_rows)),
        min_effective_batch_samples=max(1, int(args.min_effective_batch_samples)),
        min_effective_hard_pairs=max(1, int(args.min_effective_hard_pairs)),
        min_unique_contexts=max(1, int(args.min_unique_contexts)),
        min_level_ab_target_rows=max(0, int(args.min_level_ab_target_rows)),
        min_level_ab_hard_pairs=max(0, int(args.min_level_ab_hard_pairs)),
        min_task20_level_ab_target_rows=max(0, int(args.min_task20_level_ab_target_rows)),
        min_task20_hard_pairs=max(0, int(args.min_task20_hard_pairs)),
        max_level_c_weak_rows=max(0, int(args.max_level_c_weak_rows)),
        max_level_c_only_hard_pair_ratio=max(0.0, float(args.max_level_c_only_hard_pair_ratio)),
        true_rc_negative_eps=float(args.true_rc_negative_eps),
        min_positive_primal_roi=float(args.min_positive_primal_roi),
        max_low_roi_primal_roi=float(args.max_low_roi_primal_roi),
        min_hard_pair_roi_gap=float(args.min_hard_pair_roi_gap),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["checks"]["build_artifacts_complete"] else 1


def build_targeted_sample_expansion(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    min_effective_target_rows: int = 5000,
    min_effective_batch_samples: int = 500,
    min_effective_hard_pairs: int = 1200,
    min_unique_contexts: int = 350,
    min_level_ab_target_rows: int = 1500,
    min_level_ab_hard_pairs: int = 500,
    min_task20_level_ab_target_rows: int = 800,
    min_task20_hard_pairs: int = 600,
    max_level_c_weak_rows: int = 3500,
    max_level_c_only_hard_pair_ratio: float = 0.40,
    true_rc_negative_eps: float = 1.0e-9,
    min_positive_primal_roi: float = 0.65,
    max_low_roi_primal_roi: float = 0.65,
    min_hard_pair_roi_gap: float = 0.65,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    output_dir = Path(output_dir)
    manifest_path = dataset_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing dataset manifest: {manifest_path}")
    dataset_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_rows = _load_source_rows(dataset_manifest)
    threshold_manifest = _label_threshold_manifest(
        true_rc_negative_eps=true_rc_negative_eps,
        min_positive_primal_roi=min_positive_primal_roi,
        max_low_roi_primal_roi=max_low_roi_primal_roi,
        min_hard_pair_roi_gap=min_hard_pair_roi_gap,
    )

    raw_target_rows, raw_batch_rows = _collect_rows(
        dataset_dir=dataset_dir,
        dataset_manifest=dataset_manifest,
        source_rows=source_rows,
        threshold_manifest=threshold_manifest,
    )
    raw_hard_pairs = _build_hard_pairs(
        raw_target_rows,
        min_hard_pair_roi_gap=float(threshold_manifest["min_hard_pair_roi_gap"]),
    )
    target_rows, selection_manifest = _select_training_target_rows(
        raw_target_rows,
        raw_hard_pairs,
        target_count=min_effective_target_rows,
        min_batch_samples=min_effective_batch_samples,
        min_unique_contexts=min_unique_contexts,
    )
    batch_rows = _filter_batch_rows_for_selected_targets(raw_batch_rows, target_rows)
    hard_pairs = _build_hard_pairs(
        target_rows,
        min_hard_pair_roi_gap=float(threshold_manifest["min_hard_pair_roi_gap"]),
    )
    split_manifest = _build_split_manifest(target_rows, hard_pairs)
    causal_evidence_manifest = _build_causal_evidence_manifest(target_rows, hard_pairs)
    audit_binding_manifest = _build_stage4_audit_binding_manifest()
    schema_manifest = _build_schema_manifest(dataset_manifest)

    counts = _summarize_counts(target_rows, batch_rows, hard_pairs)
    raw_pool_counts = _summarize_counts(raw_target_rows, raw_batch_rows, raw_hard_pairs)
    gates = _quality_gates(
        counts=counts,
        min_effective_target_rows=min_effective_target_rows,
        min_effective_batch_samples=min_effective_batch_samples,
        min_effective_hard_pairs=min_effective_hard_pairs,
        min_unique_contexts=min_unique_contexts,
        min_level_ab_target_rows=min_level_ab_target_rows,
        min_level_ab_hard_pairs=min_level_ab_hard_pairs,
        min_task20_level_ab_target_rows=min_task20_level_ab_target_rows,
        min_task20_hard_pairs=min_task20_hard_pairs,
        max_level_c_weak_rows=max_level_c_weak_rows,
        max_level_c_only_hard_pair_ratio=max_level_c_only_hard_pair_ratio,
    )
    checks = {
        "build_artifacts_complete": True,
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "production_ready_false": True,
        "target_rows_written": bool(target_rows),
        "batch_samples_written": bool(batch_rows),
        "hard_pairs_written": bool(hard_pairs),
        "knn_ood_not_model_input": True,
        "delay_queue_not_reject": True,
    }
    status_flags = {
        "targeted_sample_expansion_complete": bool(gates["all_quality_gates_pass"]),
        "stage3_retraining_data_ready": bool(gates["all_quality_gates_pass"]),
        "stage4_audit_precondition_data_ready": False,
        "stage3_completed": False,
        "stage4_candidate_ready": False,
        "production_ready": False,
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": "targeted_sample_expansion_artifacts_built",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "dataset_dir": str(dataset_dir),
        "output_dir": str(output_dir),
        "source_dataset_sample_count": int(dataset_manifest.get("sample_count") or 0),
        "source_dataset_candidate_count": int(dataset_manifest.get("candidate_count") or 0),
        "counts": counts,
        "raw_pool_counts": raw_pool_counts,
        "selection_manifest": selection_manifest,
        "quality_gates": gates,
        "status_flags": status_flags,
        "checks": checks,
        "artifacts": {
            "target_rows": "stage3_targeted_target_rows_v107_optimized.jsonl",
            "batch_samples": "stage3_targeted_batch_samples_v107_optimized.jsonl",
            "hard_pair_index": "stage3_targeted_pair_index_v107_optimized.jsonl",
            "label_threshold_manifest": "label_threshold_manifest_v107_optimized.json",
            "causal_evidence_manifest": "causal_evidence_manifest_v107_optimized.json",
            "split_manifest": "split_manifest_v107_optimized.json",
            "schema_manifest": "schema_manifest_v107_optimized.json",
            "selection_manifest": "selection_manifest_v107_optimized.json",
            "stage4_gate_audit_binding_manifest": (
                "stage4_gate_audit_binding_manifest_v107_optimized.json"
            ),
            "report": "sample_allocation_report_v107_optimized.md",
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(output_dir / summary["artifacts"]["target_rows"], target_rows)
    _write_jsonl(output_dir / summary["artifacts"]["batch_samples"], batch_rows)
    _write_jsonl(output_dir / summary["artifacts"]["hard_pair_index"], hard_pairs)
    _write_json(output_dir / summary["artifacts"]["label_threshold_manifest"], threshold_manifest)
    _write_json(output_dir / summary["artifacts"]["causal_evidence_manifest"], causal_evidence_manifest)
    _write_json(output_dir / summary["artifacts"]["split_manifest"], split_manifest)
    _write_json(output_dir / summary["artifacts"]["schema_manifest"], schema_manifest)
    _write_json(output_dir / summary["artifacts"]["selection_manifest"], selection_manifest)
    _write_json(output_dir / summary["artifacts"]["stage4_gate_audit_binding_manifest"], audit_binding_manifest)
    _write_json(output_dir / "manifest.json", summary)
    _write_report(output_dir / summary["artifacts"]["report"], summary)
    return summary


def _collect_rows(
    *,
    dataset_dir: Path,
    dataset_manifest: dict[str, Any],
    source_rows: list[dict[str, Any]],
    threshold_manifest: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sample_dir = dataset_dir / "samples"
    candidate_feature_schema = list(dataset_manifest.get("candidate_feature_schema") or [])
    true_rc_index = candidate_feature_schema.index("true_reduced_cost") if "true_reduced_cost" in candidate_feature_schema else -1
    target_rows: list[dict[str, Any]] = []
    batch_rows: list[dict[str, Any]] = []
    graph_hash_cache: dict[str, str] = {}

    for sample_path in sorted(sample_dir.glob("sample_*.pt")):
        sample = torch.load(sample_path, map_location="cpu", weights_only=False)
        source_row = _source_row_for_sample(sample, source_rows)
        sample_name = sample_path.name
        context_hash = str(getattr(sample, "batch_impact_context_hash", "") or "")
        instance_path = str(getattr(sample, "batch_impact_instance_path", "") or "")
        candidate_signature_ids = list(getattr(sample, "batch_impact_candidate_signature_ids", []) or [])
        candidate_ids = list(getattr(sample, "batch_impact_candidate_ids", []) or [])
        candidate_source_present = list(
            getattr(sample, "batch_impact_candidate_signature_source_present", []) or []
        )
        candidate_count = len(candidate_signature_ids)
        candidate_batch_id = _stable_id("batch", context_hash, sample_name, str(getattr(sample, "batch_impact_source_row_index", "")))
        evidence_level = _evidence_level(source_row, candidate_count)
        batch_roi = _float_tensor_scalar(getattr(sample, "y_accepted_batch_roi", None))
        normalized_batch_roi = _normalize_roi(batch_roi, int(getattr(sample, "batch_impact_task_count", 0) or 0), threshold_manifest)
        batch_bad_mode = _bool_tensor_scalar(getattr(sample, "y_bad_mode_switch", None))
        batch_tail_improved = _bool_tensor_scalar(getattr(sample, "y_tail_improved", None))
        batch_support_changed_good = _bool_tensor_scalar(getattr(sample, "y_support_changed_good", None))
        batch_objective_progress = _bool_tensor_scalar(getattr(sample, "y_objective_progress", None))
        batch_delta_v = _float_tensor_scalar(getattr(sample, "y_delta_v", None))
        batch_barrier_slack = _float_tensor_scalar(getattr(sample, "y_barrier_slack", None))
        source_jsonl = str(getattr(sample, "batch_impact_source_jsonl", "") or "")
        source_row_index = int(getattr(sample, "batch_impact_source_row_index", -1) or -1)
        logical_graph_hash = graph_hash_cache.get(instance_path)
        if logical_graph_hash is None:
            logical_graph_hash = _file_sha1(instance_path) if instance_path else ""
            graph_hash_cache[instance_path] = logical_graph_hash

        row_ids: list[str] = []
        positive_target_count = 0
        negative_target_count = 0
        true_rc_negative_count = 0
        nonnegative_count = 0
        for candidate_index, signature_id in enumerate(candidate_signature_ids):
            true_reduced_cost = _candidate_true_reduced_cost(sample, candidate_index, true_rc_index)
            true_rc_negative = bool(true_reduced_cost < -abs(float(threshold_manifest["true_rc_negative_eps"])))
            label_group = _label_group(
                true_rc_negative=true_rc_negative,
                primal_roi=batch_roi,
                bad_mode=batch_bad_mode,
                batch_objective_progress=batch_objective_progress,
                threshold_manifest=threshold_manifest,
            )
            if label_group == "high_roi_positive":
                positive_target_count += 1
            elif label_group == "nonnegative_reject_only":
                nonnegative_count += 1
            else:
                negative_target_count += 1
            if true_rc_negative:
                true_rc_negative_count += 1

            target_task_set, target_task_sequence = _target_tasks(sample, candidate_index)
            path_tokens = _path_ids(sample, "candidate_path_token_ids", candidate_index)
            path_pairs = _path_ids(sample, "candidate_path_pair_ids", candidate_index)
            path_types = _path_ids(sample, "candidate_path_type_ids", candidate_index)
            intervention_signature = _stable_id(
                "intervention",
                context_hash,
                sample_name,
                str(candidate_index),
                str(signature_id),
                str(round(batch_roi, 12)),
                label_group,
            )
            target_id = str(signature_id or (candidate_ids[candidate_index] if candidate_index < len(candidate_ids) else ""))
            sample_id = _stable_id("target", context_hash, intervention_signature)
            causal_evidence_id = _stable_id(
                "evidence",
                source_jsonl,
                str(source_row_index),
                sample_name,
                str(candidate_index),
                context_hash,
                str(signature_id),
            )
            split = _split_for_instance(instance_path, str(getattr(sample, "batch_impact_instance_family", "") or ""), int(getattr(sample, "batch_impact_task_count", 0) or 0))
            row = {
                "schema_version": SCHEMA_VERSION,
                "sample_id": sample_id,
                "source_dataset_dir": str(dataset_dir),
                "source_sample_path": str(sample_path),
                "source_jsonl": source_jsonl,
                "source_row_index": source_row_index,
                "source_candidate_index": int(candidate_index),
                "context_hash": context_hash,
                "true_dual_hash": _row_hash_value(source_row, "true_dual_hash"),
                "fleet_dual_hash": _row_hash_value(source_row, "fleet_dual_hash", fallback_keys=("fleet_dual",)),
                "cut_dual_hash": _row_hash_value(source_row, "cut_dual_hash", fallback_keys=("cut_dual", "cut_duals")),
                "cut_hash": _row_hash_value(source_row, "cut_hash"),
                "branch_hash": _row_hash_value(source_row, "branch_hash"),
                "pool_signature_hash": _row_hash_value(source_row, "pool_signature_hash"),
                "active_support_hash": _row_hash_value(source_row, "active_support_hash"),
                "pricing_config_hash": _row_hash_value(source_row, "pricing_config_hash"),
                "forbidden_signature_hash": _row_hash_value(source_row, "forbidden_signature_hash"),
                "logical_graph_hash": logical_graph_hash,
                "path_option_universe_hash": _sample_tensor_hash(sample, "option_pair_id"),
                "start_time_candidate_hash": _sample_tensor_hash(sample, "candidate_path_token_ids"),
                "active_fleet_limit": source_row.get("active_fleet_limit"),
                "rc_formula_version": "journey_true_reduced_cost_v1",
                "feature_schema_version": _stable_id(
                    "feature-schema",
                    json.dumps(dataset_manifest.get("candidate_feature_schema") or [], sort_keys=True),
                    json.dumps(dataset_manifest.get("context_feature_schema") or [], sort_keys=True),
                    json.dumps(dataset_manifest.get("batch_feature_schema") or [], sort_keys=True),
                ),
                "label_threshold_manifest_id": threshold_manifest["label_threshold_manifest_id"],
                "instance": str(getattr(sample, "batch_impact_instance", "") or ""),
                "instance_path": instance_path,
                "region": str(getattr(sample, "batch_impact_instance_region", "") or ""),
                "family": str(getattr(sample, "batch_impact_instance_family", "") or ""),
                "task_count": int(getattr(sample, "batch_impact_task_count", 0) or 0),
                "candidate_batch_id": candidate_batch_id,
                "target_id": target_id,
                "candidate_signature_id": str(signature_id or ""),
                "intervention_signature": intervention_signature,
                "intervention_type": _intervention_type(source_row),
                "true_reduced_cost": true_reduced_cost,
                "target_task_set": target_task_set,
                "target_task_sequence": target_task_sequence,
                "target_transition_sequence": path_pairs,
                "target_arc_option_sequence": path_tokens,
                "target_arc_option_sequence_encoding": "hashed_bucket",
                "target_path_type_pattern": path_types,
                "primal_roi": batch_roi,
                "normalized_primal_roi": _normalize_roi(batch_roi, int(getattr(sample, "batch_impact_task_count", 0) or 0), threshold_manifest),
                "retry_roi": _retry_roi(source_row),
                "normalized_retry_roi": _normalize_roi(_retry_roi(source_row), int(getattr(sample, "batch_impact_task_count", 0) or 0), threshold_manifest),
                "accepted_impact_delta": batch_roi,
                "bad_mode_switch": bool(batch_bad_mode),
                "support_changed_good": bool(batch_support_changed_good),
                "tail_improved": bool(batch_tail_improved),
                "final_judge_retry_delta": _finite_float(source_row.get("final_judge_retry_delta")),
                "hidden_negative_delta": _finite_float(source_row.get("hidden_negative_delta")),
                "label_group": label_group,
                "same_context_pair_group": context_hash,
                "causal_evidence_id": causal_evidence_id,
                "replay_script_hash": _stable_id("script", "build_gat_target_mode_targeted_sample_expansion.py"),
                "replay_artifact_path": source_jsonl,
                "evidence_level": evidence_level,
                "audit_missing": True,
                "audit_ready_for_checkpoint": False,
                "stage4_gate_evaluable": False,
                "stage4_ready_for_checkpoint_id": "",
                "split": split,
                "training_label_allowed": bool(source_row.get("training_label_allowed", True)),
                "effective_training_row": bool(
                    candidate_source_present[candidate_index]
                    if candidate_index < len(candidate_source_present)
                    else bool(signature_id)
                )
                and bool(source_row.get("training_label_allowed", True))
                and label_group
                != "unsupported",
            }
            target_rows.append(row)
            row_ids.append(sample_id)

        batch_rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "batch_sample_id": candidate_batch_id,
                "source_sample_path": str(sample_path),
                "context_hash": context_hash,
                "candidate_batch_id": candidate_batch_id,
                "target_ids": row_ids,
                "positive_target_count": int(positive_target_count),
                "negative_target_count": int(negative_target_count),
                "true_rc_negative_count": int(true_rc_negative_count),
                "nonnegative_count": int(nonnegative_count),
                "batch_features": _tensor_to_list(getattr(sample, "batch_features", None)),
                "batch_type": _batch_type(getattr(sample, "batch_features", None), dataset_manifest),
                "batch_roi": batch_roi,
                "normalized_batch_roi": normalized_batch_roi,
                "batch_objective_progress": bool(batch_objective_progress),
                "batch_tail_improved": bool(batch_tail_improved),
                "batch_bad_mode_switch": bool(batch_bad_mode),
                "batch_support_changed_good": bool(batch_support_changed_good),
                "batch_delta_v": batch_delta_v,
                "batch_barrier_slack": batch_barrier_slack,
                "batch_accepted_roi": batch_roi,
                "split": _split_for_instance(instance_path, str(getattr(sample, "batch_impact_instance_family", "") or ""), int(getattr(sample, "batch_impact_task_count", 0) or 0)),
            }
        )
    return target_rows, batch_rows


def _build_hard_pairs(target_rows: list[dict[str, Any]], *, min_hard_pair_roi_gap: float) -> list[dict[str, Any]]:
    rows_by_context: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in target_rows:
        if row.get("effective_training_row"):
            rows_by_context[str(row.get("context_hash") or "")].append(row)
    pairs: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for context_hash, rows in sorted(rows_by_context.items()):
        positives = [row for row in rows if row.get("label_group") == "high_roi_positive"]
        negatives = [
            row
            for row in rows
            if row.get("label_group")
            in {"accepted_low_roi_negative", "bad_mode_negative", "delay_risk_negative"}
        ]
        for positive in positives:
            for negative in negatives:
                if positive["candidate_signature_id"] == negative["candidate_signature_id"]:
                    continue
                roi_gap = _finite_float(positive.get("primal_roi")) - _finite_float(negative.get("primal_roi"))
                if roi_gap < min_hard_pair_roi_gap:
                    continue
                key = (context_hash, positive["target_id"], negative["target_id"])
                if key in seen:
                    continue
                seen.add(key)
                pair_type = _pair_type(positive, negative)
                pair_id = _stable_id("pair", *key)
                pos_level = str(positive.get("evidence_level") or "")
                neg_level = str(negative.get("evidence_level") or "")
                has_level_ab = pos_level in {"A", "B"} or neg_level in {"A", "B"}
                pairs.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "pair_id": pair_id,
                        "context_hash": context_hash,
                        "positive_target_id": positive["target_id"],
                        "negative_target_id": negative["target_id"],
                        "positive_sample_id": positive["sample_id"],
                        "negative_sample_id": negative["sample_id"],
                        "positive_roi": _finite_float(positive.get("primal_roi")),
                        "negative_roi": _finite_float(negative.get("primal_roi")),
                        "roi_gap": roi_gap,
                        "task_count": int(positive.get("task_count") or 0),
                        "family": str(positive.get("family") or ""),
                        "raw_score_gap_before": None,
                        "safe_score_gap_before": None,
                        "pair_type": pair_type,
                        "causal_evidence_id": _stable_id(
                            "pair-evidence",
                            positive["causal_evidence_id"],
                            negative["causal_evidence_id"],
                        ),
                        "positive_evidence_level": pos_level,
                        "negative_evidence_level": neg_level,
                        "has_level_ab_evidence": bool(has_level_ab),
                        "level_c_only": not has_level_ab,
                        "label_threshold_manifest_id": positive["label_threshold_manifest_id"],
                        "split": positive.get("split") if positive.get("split") == negative.get("split") else "pair_cross_split_blocked",
                    }
                )
    return pairs


def _select_training_target_rows(
    target_rows: list[dict[str, Any]],
    hard_pairs: list[dict[str, Any]],
    *,
    target_count: int,
    min_batch_samples: int,
    min_unique_contexts: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Select the quota-governed 5000-row training subset from a larger raw pool."""

    target_count = max(1, int(target_count))
    effective_rows = [dict(row) for row in target_rows if row.get("effective_training_row")]
    pair_endpoint_ids: set[str] = set()
    for pair in hard_pairs:
        positive_id = str(pair.get("positive_sample_id") or "")
        negative_id = str(pair.get("negative_sample_id") or "")
        if positive_id:
            pair_endpoint_ids.add(positive_id)
        if negative_id:
            pair_endpoint_ids.add(negative_id)

    selected_ids: set[str] = set()
    selected_rows: list[dict[str, Any]] = []

    def add_row(row: dict[str, Any], reason: str) -> bool:
        if len(selected_rows) >= target_count:
            return False
        sample_id = str(row.get("sample_id") or "")
        if not sample_id or sample_id in selected_ids:
            return False
        selected = dict(row)
        selected["selected_for_training"] = True
        selected["selection_reason"] = reason
        selected_ids.add(sample_id)
        selected_rows.append(selected)
        return True

    sorted_rows = sorted(
        effective_rows,
        key=lambda row: _selection_sort_key(row, pair_endpoint_ids),
    )

    for row in sorted_rows:
        if str(row.get("evidence_level") or "") in {"A", "B"}:
            add_row(row, "level_ab_priority")

    for row in sorted_rows:
        if str(row.get("sample_id") or "") in pair_endpoint_ids:
            add_row(row, "hard_pair_endpoint")

    add_group_representatives(
        rows=sorted_rows,
        selected_rows=selected_rows,
        add_row=add_row,
        field="context_hash",
        min_groups=min_unique_contexts,
        reason="unique_context_coverage",
    )
    add_group_representatives(
        rows=sorted_rows,
        selected_rows=selected_rows,
        add_row=add_row,
        field="candidate_batch_id",
        min_groups=min_batch_samples,
        reason="batch_sample_coverage",
    )

    for (scale, family), quota in _stage4_family_scale_fill_order():
        selected_in_bucket = sum(
            1
            for row in selected_rows
            if int(row.get("task_count") or 0) == scale and str(row.get("family") or "") == family
        )
        if selected_in_bucket >= quota or len(selected_rows) >= target_count:
            continue
        for row in sorted_rows:
            if selected_in_bucket >= quota or len(selected_rows) >= target_count:
                break
            if int(row.get("task_count") or 0) != scale:
                continue
            if str(row.get("family") or "") != family:
                continue
            if add_row(row, "family_scale_quota"):
                selected_in_bucket += 1

    for row in sorted_rows:
        if len(selected_rows) >= target_count:
            break
        add_row(row, "quota_backfill")

    selected_task_counts = Counter(str(int(row.get("task_count") or 0)) for row in selected_rows)
    selected_family_counts = Counter(str(row.get("family") or "") for row in selected_rows)
    selected_family_task_counts = Counter(
        f"{int(row.get('task_count') or 0)}|{row.get('family') or ''}"
        for row in selected_rows
    )
    selection_manifest = {
        "schema_version": f"{SCHEMA_VERSION}_selection_manifest",
        "selection_policy": "stage4_biased_family_scale_quota_with_level_ab_and_hard_pair_priority",
        "target_selected_target_rows": int(target_count),
        "min_selected_batch_samples": int(min_batch_samples),
        "min_selected_unique_contexts": int(min_unique_contexts),
        "raw_target_rows_available": int(len(target_rows)),
        "raw_effective_target_rows_available": int(len(effective_rows)),
        "selected_target_rows": int(len(selected_rows)),
        "unselected_effective_target_rows": int(max(0, len(effective_rows) - len(selected_rows))),
        "raw_hard_pairs_available": int(len(hard_pairs)),
        "raw_hard_pair_endpoint_rows_available": int(len(pair_endpoint_ids)),
        "selection_reason_counts": dict(
            sorted(Counter(str(row.get("selection_reason") or "") for row in selected_rows).items())
        ),
        "selected_task_count_counts": dict(sorted(selected_task_counts.items(), key=lambda item: int(item[0]))),
        "selected_family_counts": dict(sorted(selected_family_counts.items())),
        "selected_family_task_counts": dict(sorted(selected_family_task_counts.items())),
        "scale_targets": {str(scale): int(target) for scale, target in SCALE_TARGETS.items()},
        "family_targets": dict(FAMILY_TARGETS),
        "family_scale_targets": {
            f"{scale}|{family}": int(target)
            for (scale, family), target in FAMILY_SCALE_TARGETS.items()
        },
        "family_scale_shortages": {
            f"{scale}|{family}": int(max(0, target - selected_family_task_counts.get(f"{scale}|{family}", 0)))
            for (scale, family), target in FAMILY_SCALE_TARGETS.items()
        },
        "selected_rows_are_training_artifact_rows": True,
        "raw_pool_rows_are_reported_only": True,
    }
    return selected_rows, selection_manifest


def add_group_representatives(
    *,
    rows: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
    add_row: Any,
    field: str,
    min_groups: int,
    reason: str,
) -> None:
    represented = {str(row.get(field) or "") for row in selected_rows if row.get(field)}
    if len(represented) >= int(min_groups):
        return
    for row in rows:
        if len(represented) >= int(min_groups):
            break
        value = str(row.get(field) or "")
        if not value or value in represented:
            continue
        if add_row(row, reason):
            represented.add(value)


def _filter_batch_rows_for_selected_targets(
    batch_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_batch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in target_rows:
        batch_id = str(row.get("candidate_batch_id") or "")
        if batch_id:
            rows_by_batch[batch_id].append(row)

    selected_batch_rows: list[dict[str, Any]] = []
    for batch_row in batch_rows:
        batch_id = str(batch_row.get("candidate_batch_id") or batch_row.get("batch_sample_id") or "")
        selected_targets = rows_by_batch.get(batch_id)
        if not selected_targets:
            continue
        updated = dict(batch_row)
        updated["target_ids"] = [str(row.get("sample_id") or "") for row in selected_targets]
        updated["positive_target_count"] = sum(
            1 for row in selected_targets if row.get("label_group") == "high_roi_positive"
        )
        updated["nonnegative_count"] = sum(
            1 for row in selected_targets if row.get("label_group") == "nonnegative_reject_only"
        )
        updated["negative_target_count"] = sum(
            1
            for row in selected_targets
            if row.get("label_group")
            in {"accepted_low_roi_negative", "bad_mode_negative", "delay_risk_negative"}
        )
        updated["true_rc_negative_count"] = sum(
            1 for row in selected_targets if _finite_float(row.get("true_reduced_cost")) < -1.0e-9
        )
        updated["selected_for_training"] = True
        selected_batch_rows.append(updated)
    return selected_batch_rows


def _stage4_family_scale_fill_order() -> list[tuple[tuple[int, str], int]]:
    scale_priority = {20: 0, 100: 1, 50: 2, 30: 3}
    family_priority = {"sector-wave": 0, "random-wave": 1, "greedy-anchor": 2}
    return sorted(
        FAMILY_SCALE_TARGETS.items(),
        key=lambda item: (scale_priority.get(item[0][0], 99), family_priority.get(item[0][1], 99)),
    )


def _selection_sort_key(row: dict[str, Any], pair_endpoint_ids: set[str]) -> tuple[Any, ...]:
    evidence_priority = {"A": 0, "B": 1, "C": 2, "raw": 3, "": 4}
    label_priority = {
        "high_roi_positive": 0,
        "bad_mode_negative": 1,
        "delay_risk_negative": 2,
        "accepted_low_roi_negative": 3,
        "nonnegative_reject_only": 4,
    }
    scale_priority = {20: 0, 100: 1, 50: 2, 30: 3}
    family_priority = {"sector-wave": 0, "random-wave": 1, "greedy-anchor": 2}
    split_priority = {
        "train": 0,
        "validation": 1,
        "context_holdout": 2,
        "family_holdout": 3,
        "scale_holdout": 4,
    }
    sample_id = str(row.get("sample_id") or "")
    return (
        evidence_priority.get(str(row.get("evidence_level") or ""), 9),
        0 if sample_id in pair_endpoint_ids else 1,
        label_priority.get(str(row.get("label_group") or ""), 9),
        scale_priority.get(int(row.get("task_count") or 0), 99),
        family_priority.get(str(row.get("family") or ""), 99),
        split_priority.get(str(row.get("split") or ""), 99),
        str(row.get("context_hash") or ""),
        str(row.get("source_sample_path") or ""),
        int(row.get("source_candidate_index") or 0),
        sample_id,
    )


def _summarize_counts(
    target_rows: list[dict[str, Any]],
    batch_rows: list[dict[str, Any]],
    hard_pairs: list[dict[str, Any]],
) -> dict[str, Any]:
    effective = [row for row in target_rows if row.get("effective_training_row")]
    label_counts = Counter(str(row.get("label_group") or "") for row in effective)
    task_counts = Counter(str(int(row.get("task_count") or 0)) for row in effective)
    family_counts = Counter(str(row.get("family") or "") for row in effective)
    family_task_counts = Counter(
        f"{int(row.get('task_count') or 0)}|{row.get('family') or ''}" for row in effective
    )
    evidence_counts = Counter(str(row.get("evidence_level") or "") for row in effective)
    split_counts = Counter(str(row.get("split") or "") for row in effective)
    level_ab_task_counts = Counter(
        str(int(row.get("task_count") or 0))
        for row in effective
        if str(row.get("evidence_level") or "") in {"A", "B"}
    )
    hard_pair_task_counts = Counter(str(int(pair.get("task_count") or 0)) for pair in hard_pairs)
    stage4_gate_evaluable = sum(1 for row in effective if row.get("stage4_gate_evaluable"))
    level_ab_target_rows = sum(
        1 for row in effective if str(row.get("evidence_level") or "") in {"A", "B"}
    )
    level_c_weak_rows = sum(
        1 for row in effective if str(row.get("evidence_level") or "") == "C"
    )
    level_ab_pairs = sum(1 for pair in hard_pairs if pair.get("has_level_ab_evidence"))
    level_c_only_pairs = sum(1 for pair in hard_pairs if pair.get("level_c_only"))
    return {
        "raw_target_rows": len(target_rows),
        "effective_target_rows": len(effective),
        "effective_batch_samples": len(batch_rows),
        "effective_hard_pairs": len(hard_pairs),
        "level_ab_target_rows": int(level_ab_target_rows),
        "level_c_weak_rows": int(level_c_weak_rows),
        "level_ab_hard_pairs": int(level_ab_pairs),
        "level_c_only_hard_pairs": int(level_c_only_pairs),
        "level_c_only_hard_pair_ratio": (
            round(level_c_only_pairs / len(hard_pairs), 6) if hard_pairs else 0.0
        ),
        "unique_contexts": len({row.get("context_hash") for row in effective}),
        "unique_instances": len({row.get("instance_path") for row in effective}),
        "label_group_counts": dict(sorted(label_counts.items())),
        "task_count_counts": dict(sorted(task_counts.items(), key=lambda item: int(item[0]))),
        "family_counts": dict(sorted(family_counts.items())),
        "family_task_counts": dict(sorted(family_task_counts.items())),
        "evidence_level_counts": dict(sorted(evidence_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "level_ab_task_count_counts": dict(
            sorted(level_ab_task_counts.items(), key=lambda item: int(item[0]))
        ),
        "hard_pair_task_count_counts": dict(
            sorted(hard_pair_task_counts.items(), key=lambda item: int(item[0]))
        ),
        "stage4_gate_evaluable_rows": int(stage4_gate_evaluable),
        "audit_missing_rows": int(sum(1 for row in effective if row.get("audit_missing"))),
    }


def _quality_gates(
    *,
    counts: dict[str, Any],
    min_effective_target_rows: int,
    min_effective_batch_samples: int,
    min_effective_hard_pairs: int,
    min_unique_contexts: int,
    min_level_ab_target_rows: int,
    min_level_ab_hard_pairs: int,
    min_task20_level_ab_target_rows: int,
    min_task20_hard_pairs: int,
    max_level_c_weak_rows: int,
    max_level_c_only_hard_pair_ratio: float,
) -> dict[str, Any]:
    gate_results: dict[str, bool] = {
        "effective_target_rows_ge_min": counts["effective_target_rows"] >= min_effective_target_rows,
        "effective_batch_samples_ge_min": counts["effective_batch_samples"] >= min_effective_batch_samples,
        "effective_hard_pairs_ge_min": counts["effective_hard_pairs"] >= min_effective_hard_pairs,
        "unique_contexts_ge_min": counts["unique_contexts"] >= min_unique_contexts,
        "level_ab_target_rows_ge_min": counts["level_ab_target_rows"] >= min_level_ab_target_rows,
        "level_ab_hard_pairs_ge_min": counts["level_ab_hard_pairs"] >= min_level_ab_hard_pairs,
        "task20_level_ab_target_rows_ge_min": int(
            counts.get("level_ab_task_count_counts", {}).get("20", 0)
        )
        >= min_task20_level_ab_target_rows,
        "task20_hard_pairs_ge_min": int(
            counts.get("hard_pair_task_count_counts", {}).get("20", 0)
        )
        >= min_task20_hard_pairs,
        "level_c_weak_rows_le_max": counts["level_c_weak_rows"] <= max_level_c_weak_rows,
        "level_c_only_hard_pair_ratio_le_max": (
            counts["level_c_only_hard_pair_ratio"] <= max_level_c_only_hard_pair_ratio
        ),
        "stage4_gate_evaluable_audit_complete": counts["stage4_gate_evaluable_rows"] > 0
        and counts["audit_missing_rows"] == 0,
    }
    task_counts = {int(key): int(value) for key, value in counts["task_count_counts"].items()}
    family_counts = {str(key): int(value) for key, value in counts["family_counts"].items()}
    family_task_counts: dict[tuple[int, str], int] = {}
    for key, value in counts["family_task_counts"].items():
        task_text, family = key.split("|", 1)
        family_task_counts[(int(task_text), family)] = int(value)
    scale_gate_details = {
        str(scale): {
            "actual": int(task_counts.get(scale, 0)),
            "minimum": int(math.ceil(target * 0.8)),
            "pass": int(task_counts.get(scale, 0)) >= int(math.ceil(target * 0.8)),
        }
        for scale, target in SCALE_TARGETS.items()
    }
    family_gate_details = {
        family: {
            "actual": int(family_counts.get(family, 0)),
            "minimum": int(math.ceil(target * 0.8)),
            "pass": int(family_counts.get(family, 0)) >= int(math.ceil(target * 0.8)),
        }
        for family, target in FAMILY_TARGETS.items()
    }
    family_scale_gate_details = {
        f"{scale}|{family}": {
            "actual": int(family_task_counts.get((scale, family), 0)),
            "minimum": int(math.ceil(target * 0.8)),
            "pass": int(family_task_counts.get((scale, family), 0)) >= int(math.ceil(target * 0.8)),
        }
        for (scale, family), target in FAMILY_SCALE_TARGETS.items()
    }
    gate_results["scale_80pct_gates_pass"] = all(item["pass"] for item in scale_gate_details.values())
    gate_results["family_80pct_gates_pass"] = all(item["pass"] for item in family_gate_details.values())
    gate_results["family_scale_80pct_gates_pass"] = all(
        item["pass"] for item in family_scale_gate_details.values()
    )
    return {
        "all_quality_gates_pass": all(gate_results.values()),
        "gate_results": gate_results,
        "scale_gate_details": scale_gate_details,
        "family_gate_details": family_gate_details,
        "family_scale_gate_details": family_scale_gate_details,
        "thresholds": {
            "min_effective_target_rows": int(min_effective_target_rows),
            "min_effective_batch_samples": int(min_effective_batch_samples),
            "min_effective_hard_pairs": int(min_effective_hard_pairs),
            "min_unique_contexts": int(min_unique_contexts),
            "min_level_ab_target_rows": int(min_level_ab_target_rows),
            "min_level_ab_hard_pairs": int(min_level_ab_hard_pairs),
            "min_task20_level_ab_target_rows": int(min_task20_level_ab_target_rows),
            "min_task20_hard_pairs": int(min_task20_hard_pairs),
            "max_level_c_weak_rows": int(max_level_c_weak_rows),
            "max_level_c_only_hard_pair_ratio": float(max_level_c_only_hard_pair_ratio),
        },
    }


def _build_split_manifest(target_rows: list[dict[str, Any]], hard_pairs: list[dict[str, Any]]) -> dict[str, Any]:
    split_counts = Counter(str(row.get("split") or "") for row in target_rows if row.get("effective_training_row"))
    instance_splits: dict[str, set[str]] = defaultdict(set)
    context_splits: dict[str, set[str]] = defaultdict(set)
    for row in target_rows:
        if not row.get("effective_training_row"):
            continue
        instance_splits[str(row.get("instance_path") or "")].add(str(row.get("split") or ""))
        context_splits[str(row.get("context_hash") or "")].add(str(row.get("split") or ""))
    return {
        "schema_version": f"{SCHEMA_VERSION}_split_manifest",
        "split_policy": "deterministic_instance_hash_no_primary_train_validation_instance_overlap",
        "split_counts": dict(sorted(split_counts.items())),
        "instance_cross_split_violations": sorted(
            instance for instance, splits in instance_splits.items() if len(splits) > 1
        ),
        "context_cross_split_violations": sorted(
            context for context, splits in context_splits.items() if len(splits) > 1
        ),
        "hard_pair_cross_split_blocked_count": sum(
            1 for pair in hard_pairs if pair.get("split") == "pair_cross_split_blocked"
        ),
        "primary_validation_claim_allowed": False,
        "random_row_split_allowed_for_primary_claim": False,
    }


def _build_causal_evidence_manifest(
    target_rows: list[dict[str, Any]], hard_pairs: list[dict[str, Any]]
) -> dict[str, Any]:
    evidence_counts = Counter(str(row.get("evidence_level") or "") for row in target_rows if row.get("effective_training_row"))
    return {
        "schema_version": f"{SCHEMA_VERSION}_causal_evidence_manifest",
        "evidence_level_counts": dict(sorted(evidence_counts.items())),
        "hard_pair_count": len(hard_pairs),
        "level_ab_hard_pair_count": sum(1 for pair in hard_pairs if pair.get("has_level_ab_evidence")),
        "level_c_only_hard_pair_count": sum(1 for pair in hard_pairs if pair.get("level_c_only")),
        "level_c_usage_boundary": (
            "Level C rows are weak same-context signature-matched labels. They may support "
            "Stage 3 retraining, but cannot by themselves prove Stage 4 candidate readiness."
        ),
    }


def _build_stage4_audit_binding_manifest() -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_VERSION}_stage4_gate_audit_binding_manifest",
        "checkpoint_id": "",
        "embedding_model_config_hash": "",
        "training_manifest_hash": "",
        "threshold_config_hash": "",
        "knn_train_split_id": "",
        "stage4_gate_rule_id": "",
        "safe_source_export_id": "",
        "audit_rows_complete": False,
        "stage4_gate_evaluable_subset_ready": False,
        "audit_missing_default": True,
        "note": "New checkpoint/threshold/OOD rule requires a fresh audit pass before Stage 4 gates.",
    }


def _build_schema_manifest(dataset_manifest: dict[str, Any]) -> dict[str, Any]:
    forbidden_model_input_prefixes = [
        "state_next_",
        "delta_",
        "horizon_",
        "label_",
        "post_addition_",
        "future_",
        "knn_",
        "ood_",
        "threshold_",
        "stage4_gate_",
    ]
    return {
        "schema_version": f"{SCHEMA_VERSION}_schema_manifest",
        "source_candidate_feature_schema": list(dataset_manifest.get("candidate_feature_schema") or []),
        "source_context_feature_schema": list(dataset_manifest.get("context_feature_schema") or []),
        "source_batch_feature_schema": list(dataset_manifest.get("batch_feature_schema") or []),
        "target_row_schema_version": SCHEMA_VERSION,
        "forbidden_model_input_prefixes": forbidden_model_input_prefixes,
        "knn_ood_fields_are_audit_only": True,
    }


def _label_threshold_manifest(
    *,
    true_rc_negative_eps: float,
    min_positive_primal_roi: float,
    max_low_roi_primal_roi: float,
    min_hard_pair_roi_gap: float,
) -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_VERSION}_label_threshold_manifest",
        "label_threshold_manifest_id": LABEL_THRESHOLD_MANIFEST_ID,
        "horizon_H": "same_context_observed_replay_horizon",
        "true_rc_negative_eps": float(abs(true_rc_negative_eps)),
        "min_positive_primal_roi": float(min_positive_primal_roi),
        "min_positive_retry_roi": 0.0,
        "min_positive_accepted_impact_delta": float(min_positive_primal_roi),
        "max_low_roi_primal_roi": float(max_low_roi_primal_roi),
        "max_low_roi_retry_roi": 0.0,
        "min_hard_pair_roi_gap": float(min_hard_pair_roi_gap),
        "bad_mode_retry_delta_threshold": 0.0,
        "bad_mode_hidden_negative_delta_threshold": 0.0,
        "bad_mode_dual_l1_delta_threshold": 0.0,
        "support_changed_good_definition": "batch_roi_positive_and_not_bad_mode_with_active_support_change",
        "normalized_roi_scale_by_task_count": {
            "5": 0.25,
            "10": 0.5,
            "20": 1.0,
            "30": 1.5,
            "50": 2.5,
            "100": 5.0,
        },
    }


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    raw_counts = summary.get("raw_pool_counts") or {}
    gates = summary["quality_gates"]
    failed_gates = [
        key for key, value in gates["gate_results"].items() if not value
    ]
    lines = [
        "# GAT Target Mode v107 Optimized Targeted Sample Expansion Report",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Scope",
        "",
        "Offline data expansion only. This run did not train a model, run BPC/pricing, "
        "enable GAT online, produce certificates, or produce official bounds.",
        "",
        "## Counts",
        "",
        "Quality gates are evaluated on the selected training subset, not on the full raw pool.",
        "",
        f"- Effective target-level rows: {counts['effective_target_rows']}",
        f"- Effective batch-level samples: {counts['effective_batch_samples']}",
        f"- Same-context hard pairs: {counts['effective_hard_pairs']}",
        f"- Level A/B target rows: {counts['level_ab_target_rows']}",
        f"- Level C weak rows: {counts['level_c_weak_rows']}",
        f"- Level A/B hard pairs: {counts['level_ab_hard_pairs']}",
        "- 20-task Level A/B target rows: "
        f"{counts['level_ab_task_count_counts'].get('20', 0)}",
        "- 20-task hard pairs: "
        f"{counts['hard_pair_task_count_counts'].get('20', 0)}",
        f"- Unique contexts: {counts['unique_contexts']}",
        f"- Stage-4-gate-evaluable rows: {counts['stage4_gate_evaluable_rows']}",
        "",
        "## Raw Pool",
        "",
        f"- Raw effective target-level rows available: {raw_counts.get('effective_target_rows', 0)}",
        f"- Raw batch-level samples available: {raw_counts.get('effective_batch_samples', 0)}",
        f"- Raw same-context hard pairs available: {raw_counts.get('effective_hard_pairs', 0)}",
        f"- Raw Level A/B target rows available: {raw_counts.get('level_ab_target_rows', 0)}",
        f"- Raw Level C weak rows available: {raw_counts.get('level_c_weak_rows', 0)}",
        "",
        "## Selection",
        "",
        "```json",
        json.dumps(summary["selection_manifest"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Label Groups",
        "",
        "```json",
        json.dumps(counts["label_group_counts"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Coverage",
        "",
        "```json",
        json.dumps(
            {
                "task_count_counts": counts["task_count_counts"],
                "family_counts": counts["family_counts"],
                "family_task_counts": counts["family_task_counts"],
                "evidence_level_counts": counts["evidence_level_counts"],
                "level_ab_task_count_counts": counts["level_ab_task_count_counts"],
                "hard_pair_task_count_counts": counts["hard_pair_task_count_counts"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Quality Gates",
        "",
        "```json",
        json.dumps(gates, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Status Flags",
        "",
        "```json",
        json.dumps(summary["status_flags"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Main Finding",
        "",
    ]
    if failed_gates:
        lines.extend(
            [
                "The artifacts were evaluated against the 5000-row v107 optimized target. "
                "The strict quality gate is not fully satisfied yet.",
                "",
                "Failed gates:",
                "",
                *[f"- {gate}" for gate in failed_gates],
                "",
                "The most important remaining work is to add missing scale/family coverage and "
                "run checkpoint-bound kNN/OOD audit before claiming Stage 4 readiness.",
            ]
        )
    else:
        lines.append("All configured v107 optimized quality gates passed for this offline artifact set.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_source_rows(dataset_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_path in dataset_manifest.get("source_jsonl_paths") or []:
        path = Path(str(raw_path))
        if not path.exists():
            continue
        with path.open(encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                text = line.strip()
                if not text:
                    continue
                try:
                    row = json.loads(text)
                except json.JSONDecodeError:
                    row = {}
                rows.append(row if isinstance(row, dict) else {})
    return rows


def _source_row_for_sample(sample: Any, source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    index = int(getattr(sample, "batch_impact_source_row_index", -1) or -1)
    if 0 <= index < len(source_rows):
        return source_rows[index]
    return {}


def _evidence_level(source_row: dict[str, Any], candidate_count: int) -> str:
    if source_row.get("same_context_target_intervention_observed") and source_row.get(
        "worker_target_causal_match"
    ):
        return "A" if candidate_count == 1 else "B"
    if source_row.get("same_run_intervention_observed"):
        return "C"
    return "raw"


def _intervention_type(source_row: dict[str, Any]) -> str:
    if source_row.get("same_context_target_intervention_observed"):
        return "same_context_target_intervention"
    if source_row.get("same_run_intervention_observed"):
        return "same_context_signature_matched_batch"
    return "unknown_offline_observation"


def _label_group(
    *,
    true_rc_negative: bool,
    primal_roi: float,
    bad_mode: bool,
    batch_objective_progress: bool,
    threshold_manifest: dict[str, Any],
) -> str:
    if not true_rc_negative:
        return "nonnegative_reject_only"
    if bad_mode:
        return "bad_mode_negative"
    if primal_roi >= float(threshold_manifest["min_positive_primal_roi"]):
        return "high_roi_positive"
    if batch_objective_progress:
        return "accepted_low_roi_negative"
    return "delay_risk_negative"


def _pair_type(positive: dict[str, Any], negative: dict[str, Any]) -> str:
    neg_label = str(negative.get("label_group") or "")
    if neg_label == "accepted_low_roi_negative":
        return "missed_high_roi_vs_accepted_low_roi"
    if neg_label == "bad_mode_negative":
        return "missed_high_roi_vs_bad_mode_negative"
    return "missed_high_roi_vs_delay_risk_negative"


def _target_tasks(sample: Any, candidate_index: int) -> tuple[list[int], list[int]]:
    task_ids = [int(value) for value in _tensor_to_list(getattr(sample, "task_ids", None))]
    membership_rows = _tensor_to_list(getattr(sample, "candidate_task_membership", None))
    position_rows = _tensor_to_list(getattr(sample, "candidate_sequence_positions", None))
    membership = membership_rows[candidate_index] if candidate_index < len(membership_rows) else []
    positions = position_rows[candidate_index] if candidate_index < len(position_rows) else []
    task_set = [
        task_id
        for task_id, present in zip(task_ids, membership)
        if _finite_float(present) > 0.5
    ]
    sortable: list[tuple[float, int]] = []
    for task_id, present, position in zip(task_ids, membership, positions):
        if _finite_float(present) > 0.5:
            sortable.append((_finite_float(position, default=float(len(sortable) + 1)), task_id))
    sequence = [task_id for _, task_id in sorted(sortable)]
    return sorted(task_set), sequence


def _path_ids(sample: Any, attr_name: str, candidate_index: int) -> list[int]:
    rows = _tensor_to_list(getattr(sample, attr_name, None))
    if candidate_index >= len(rows):
        return []
    result: list[int] = []
    for value in rows[candidate_index]:
        item = int(_finite_float(value))
        if item:
            result.append(item)
    return result


def _candidate_true_reduced_cost(sample: Any, candidate_index: int, true_rc_index: int) -> float:
    features = getattr(sample, "candidate_features", None)
    if features is not None and true_rc_index >= 0:
        try:
            return float(features[candidate_index, true_rc_index].item())
        except Exception:
            pass
    negative = _bool_tensor_item(getattr(sample, "y_candidate_true_rc_negative", None), candidate_index)
    return -1.0 if negative else 0.0


def _retry_roi(source_row: dict[str, Any]) -> float:
    retry_delta = _finite_float(source_row.get("final_judge_retry_delta"))
    hidden_delta = _finite_float(source_row.get("hidden_negative_delta"))
    return -(retry_delta + hidden_delta)


def _normalize_roi(value: float, task_count: int, threshold_manifest: dict[str, Any]) -> float:
    scale_map = threshold_manifest.get("normalized_roi_scale_by_task_count") or {}
    scale = _finite_float(scale_map.get(str(int(task_count))), default=max(1.0, float(task_count) / 20.0))
    if abs(scale) <= 1.0e-12:
        return value
    return value / scale


def _batch_type(batch_features: Any, dataset_manifest: dict[str, Any]) -> str:
    values = _tensor_to_list(batch_features)
    if values and isinstance(values[0], list):
        values = values[0]
    schema = list(dataset_manifest.get("batch_feature_schema") or [])
    flags = {
        name: _finite_float(values[index])
        for index, name in enumerate(schema)
        if index < len(values) and name.startswith("batch_type_")
    }
    active = [name.replace("batch_type_", "") for name, value in flags.items() if value > 0.5]
    return active[0] if active else "unknown"


def _split_for_instance(instance_path: str, family: str, task_count: int) -> str:
    digest = int(hashlib.sha1(str(instance_path).encode("utf-8", errors="ignore")).hexdigest()[:8], 16)
    bucket = digest % 100
    if family == "greedy-anchor" and bucket < 35:
        return "family_holdout"
    if int(task_count) in {50, 100} and bucket < 45:
        return "scale_holdout"
    if bucket < 20:
        return "validation"
    if bucket < 25:
        return "context_holdout"
    return "train"


def _row_hash_value(
    row: dict[str, Any], key: str, *, fallback_keys: Iterable[str] = ()
) -> str:
    value = row.get(key)
    if value not in (None, ""):
        return str(value)
    for fallback_key in fallback_keys:
        value = row.get(fallback_key)
        if value not in (None, ""):
            return _stable_id(key, _json_dumps(value))
    return ""


def _sample_tensor_hash(sample: Any, attr_name: str) -> str:
    value = getattr(sample, attr_name, None)
    if value is None:
        return ""
    return _stable_id(attr_name, _json_dumps(_tensor_to_list(value)))


def _file_sha1(path_text: str) -> str:
    path = Path(path_text)
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha1()
    for part in parts:
        digest.update(str(part).encode("utf-8", errors="ignore"))
        digest.update(b"\0")
    return digest.hexdigest()


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _tensor_to_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if hasattr(value, "detach"):
        value = value.detach().cpu().tolist()
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, list):
        return value
    return [value]


def _bool_tensor_scalar(value: Any) -> bool:
    return _float_tensor_scalar(value) > 0.5


def _float_tensor_scalar(value: Any) -> float:
    if value is None:
        return 0.0
    if hasattr(value, "numel") and value.numel() > 0:
        return _finite_float(value.flatten()[0].item())
    if isinstance(value, list) and value:
        return _finite_float(value[0])
    return _finite_float(value)


def _bool_tensor_item(value: Any, index: int) -> bool:
    if value is None:
        return False
    if hasattr(value, "numel") and value.numel() > index:
        return bool(float(value.flatten()[index].item()) > 0.5)
    if isinstance(value, list) and index < len(value):
        return bool(_finite_float(value[index]) > 0.5)
    return False


def _finite_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    if not math.isfinite(result):
        return float(default)
    return result


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
