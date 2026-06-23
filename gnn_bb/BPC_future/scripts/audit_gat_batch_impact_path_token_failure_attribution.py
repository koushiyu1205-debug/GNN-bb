#!/usr/bin/env python3
"""Audit path-token contribution on focused same-context pair failures.

This diagnostic is intentionally narrow: it loads an offline batch-impact GAT
checkpoint, recomputes focused pair scores for the currently failing pairs,
and compares normal scoring with an all-path-token-masked ablation. It does not
run BPC, pricing, RMP, workers, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
import math
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.learning.batch_impact_model import GATBatchImpactModel
from BPC_future.scripts.train_gat_batch_impact import (
    _load_sample,
    _normalize_sample,
    _sample_model_kwargs,
)


DEFAULT_DATASET_DIR = Path(
    "BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622"
)
DEFAULT_CHECKPOINT = Path(
    "BPC_future/results/gat_batch_impact_training_v140_trainonly_failure_analog_boost_seed13_20260623/"
    "model.pt"
)
DEFAULT_METRICS = Path(
    "BPC_future/results/gat_batch_impact_training_v140_trainonly_failure_analog_boost_seed13_20260623/"
    "metrics.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_batch_impact_path_token_failure_attribution_v142_v140_remaining_20260623"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260623_bpc_future_gat_target_mode_stage3_v142_v140_remaining_path_token_failure_attribution_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument(
        "--margin-change-epsilon",
        type=float,
        default=1.0e-4,
        help="Minimum normal-vs-ablated margin change counted as path-token influence.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_path_token_failure_attribution(
        dataset_dir=Path(args.dataset_dir),
        checkpoint=Path(args.checkpoint),
        metrics=Path(args.metrics),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        device=str(args.device),
        margin_change_epsilon=float(args.margin_change_epsilon),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_path_token_failure_attribution(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    checkpoint: Path = DEFAULT_CHECKPOINT,
    metrics: Path = DEFAULT_METRICS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    device: str = "cpu",
    margin_change_epsilon: float = 1.0e-4,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    checkpoint_data = torch.load(Path(checkpoint), map_location="cpu", weights_only=False)
    training_metrics = _read_json(Path(metrics))
    manifest = _read_json(dataset_dir / "manifest.json")
    _assert_offline_contract(checkpoint_data, training_metrics)

    pair_rows = [
        dict(row)
        for row in (training_metrics.get("focused_pair_gate") or {}).get("pair_rows", [])
        if not bool(row.get("pair_pass"))
    ]
    row_items = {
        int(item.get("row_index")): item
        for item in manifest.get("samples", [])
        if item.get("row_index") is not None
    }
    model = GATBatchImpactModel(**checkpoint_data["model_config"]).to(torch.device(device))
    model.load_state_dict(checkpoint_data["model_state_dict"])
    model.eval()
    path_token_enabled = getattr(model, "path_token_encoder", None) is not None
    if not path_token_enabled:
        raise ValueError("checkpoint does not enable path-token encoder")

    gate_config = dict((training_metrics.get("training_run_config") or {}).get("gate_config") or {})
    needed_rows = sorted(
        {
            int(row[key])
            for row in pair_rows
            for key in ("positive_row_index", "negative_row_index")
            if row.get(key) is not None
        }
    )
    row_outputs = _score_needed_rows(
        dataset_dir=dataset_dir,
        manifest=manifest,
        row_items=row_items,
        row_indices=needed_rows,
        model=model,
        device=torch.device(device),
        gate_config=gate_config,
    )
    enriched_pairs = [
        _enrich_pair(
            row,
            row_outputs=row_outputs,
            gate_config=gate_config,
            margin_change_epsilon=float(margin_change_epsilon),
        )
        for row in pair_rows
    ]
    summary_stats = _summary_stats(
        enriched_pairs,
        path_token_enabled=path_token_enabled,
        margin_change_epsilon=float(margin_change_epsilon),
    )
    recommendation = _recommend_next_step(summary_stats)

    output_dir.mkdir(parents=True, exist_ok=True)
    pair_path = output_dir / "path_token_failure_pair_rows.jsonl"
    row_path = output_dir / "path_token_failure_row_rows.jsonl"
    _write_jsonl(pair_path, enriched_pairs)
    _write_jsonl(
        row_path,
        [
            _compact_row_output(row_index, row_output)
            for row_index, row_output in sorted(row_outputs.items())
        ],
    )
    summary = {
        "schema_version": "gat_batch_impact_path_token_failure_attribution_v1",
        "status": "gat_batch_impact_path_token_failure_attribution_audited",
        "dataset_dir": str(dataset_dir),
        "checkpoint": str(checkpoint),
        "metrics": str(metrics),
        "output_dir": str(output_dir),
        "pair_rows_path": str(pair_path),
        "row_rows_path": str(row_path),
        "focused_failed_pair_count": len(pair_rows),
        "needed_row_count": len(needed_rows),
        "path_token_encoder_enabled": bool(path_token_enabled),
        "gate_config_subset": {
            "candidate_admission_score_mode": gate_config.get("candidate_admission_score_mode"),
            "candidate_delay_score_penalty": gate_config.get("candidate_delay_score_penalty"),
            "candidate_delay_gate_enabled": gate_config.get("candidate_delay_gate_enabled"),
            "candidate_delay_risk_threshold": gate_config.get("candidate_delay_risk_threshold"),
        },
        "summary": summary_stats,
        "recommended_next_step": recommendation,
        "stage3_completed": False,
        "stage4_candidate_ready": False,
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "runs_rmp": False,
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


def _score_needed_rows(
    *,
    dataset_dir: Path,
    manifest: dict[str, Any],
    row_items: dict[int, dict[str, Any]],
    row_indices: list[int],
    model: GATBatchImpactModel,
    device: torch.device,
    gate_config: dict[str, Any],
) -> dict[int, dict[str, Any]]:
    outputs: dict[int, dict[str, Any]] = {}
    with torch.no_grad():
        for row_index in row_indices:
            item = row_items.get(int(row_index))
            if item is None:
                raise ValueError(f"focused row {row_index} missing from manifest")
            sample = _normalize_sample(_load_sample(dataset_dir / str(item["path"])), manifest).to(device)
            normal_output = _model_output(model, sample, ablate_path_tokens=False)
            ablated_output = _model_output(model, sample, ablate_path_tokens=True)
            outputs[int(row_index)] = {
                "manifest_item": item,
                "sample": sample,
                "normal_output": normal_output,
                "ablated_output": ablated_output,
                "normal_scores": _row_score_summary(
                    sample,
                    normal_output,
                    gate_config=gate_config,
                ),
                "ablated_scores": _row_score_summary(
                    sample,
                    ablated_output,
                    gate_config=gate_config,
                ),
                "path_embedding_delta": _embedding_delta_summary(
                    normal_output.get("candidate_path_embedding"),
                    ablated_output.get("candidate_path_embedding"),
                ),
                "candidate_embedding_delta": _embedding_delta_summary(
                    normal_output.get("candidate_embedding"),
                    ablated_output.get("candidate_embedding"),
                ),
            }
    return outputs


def _model_output(
    model: GATBatchImpactModel,
    sample: Any,
    *,
    ablate_path_tokens: bool,
) -> dict[str, torch.Tensor]:
    kwargs = _sample_model_kwargs(model, sample)
    if ablate_path_tokens and getattr(model, "path_token_encoder", None) is not None:
        kwargs.update(
            {
                "candidate_path_token_ids": torch.zeros_like(sample.candidate_path_token_ids),
                "candidate_path_pair_ids": torch.zeros_like(sample.candidate_path_pair_ids),
                "candidate_path_type_ids": torch.zeros_like(sample.candidate_path_type_ids),
                "candidate_path_token_mask": torch.zeros_like(
                    sample.candidate_path_token_mask,
                    dtype=torch.bool,
                ),
            }
        )
    return model(
        sample,
        sample.candidate_task_membership,
        sample.candidate_sequence_positions,
        sample.candidate_features,
        sample.context_features,
        **kwargs,
    )


def _row_score_summary(
    sample: Any,
    output: dict[str, torch.Tensor],
    *,
    gate_config: dict[str, Any],
) -> dict[str, Any]:
    raw_scores = _tensor_values(output["high_priority_probability"])
    delay_scores = _tensor_values(output["delay_risk_probability"])
    admission_scores = _candidate_admission_scores(
        raw_scores,
        delay_scores,
        gate_config=gate_config,
    )
    action_scores = _tensor_values(output["candidate_action_priority_probability"])
    candidate_path_embedding = output.get("candidate_path_embedding")
    candidate_embedding = output.get("candidate_embedding")
    return {
        "candidate_count": len(raw_scores),
        "safe_label_count": int(
            torch.sum(sample.y_candidate_high_priority.detach().cpu().reshape(-1) > 0.5).item()
        ),
        "delay_label_count": int(
            torch.sum(sample.y_candidate_delay_risk.detach().cpu().reshape(-1) > 0.5).item()
        ),
        "raw": _max_score_summary(sample, raw_scores, "raw"),
        "admission": _max_score_summary(sample, admission_scores, "admission"),
        "delay_risk": _max_score_summary(sample, delay_scores, "delay_risk"),
        "action_priority": _max_score_summary(sample, action_scores, "action_priority"),
        "all_candidate_path_token_union": _token_union_for_indices(
            sample,
            list(range(len(raw_scores))),
        ),
        "safe_candidate_path_token_union": _token_union_for_indices(
            sample,
            _candidate_label_indices(sample, "y_candidate_high_priority"),
        ),
        "delay_candidate_path_token_union": _token_union_for_indices(
            sample,
            _candidate_label_indices(sample, "y_candidate_delay_risk"),
        ),
        "path_embedding_norms": _row_norm_summary(candidate_path_embedding),
        "candidate_embedding_norms": _row_norm_summary(candidate_embedding),
    }


def _max_score_summary(sample: Any, scores: list[float], score_name: str) -> dict[str, Any]:
    if not scores:
        return {
            "score_name": score_name,
            "max_index": None,
            "max_score": None,
            "candidate": {},
        }
    max_index = max(range(len(scores)), key=lambda idx: float(scores[idx]))
    return {
        "score_name": score_name,
        "max_index": int(max_index),
        "max_score": float(scores[max_index]),
        "candidate": _candidate_summary(sample, int(max_index)),
    }


def _candidate_summary(sample: Any, index: int) -> dict[str, Any]:
    signatures = list(getattr(sample, "batch_impact_candidate_signature_ids", []) or [])
    candidate_ids = list(getattr(sample, "batch_impact_candidate_ids", []) or [])
    token_ids = _candidate_token_values(sample, index, "candidate_path_token_ids")
    pair_ids = _candidate_token_values(sample, index, "candidate_path_pair_ids")
    type_ids = _candidate_token_values(sample, index, "candidate_path_type_ids")
    return {
        "index": int(index),
        "candidate_id": str(candidate_ids[index]) if index < len(candidate_ids) else "",
        "signature_id": str(signatures[index]) if index < len(signatures) else "",
        "safe_label": _candidate_label(sample, index, "y_candidate_high_priority"),
        "delay_label": _candidate_label(sample, index, "y_candidate_delay_risk"),
        "path_token_count": len(token_ids),
        "path_unique_token_count": len(set(token_ids)),
        "path_type_counts": dict(sorted(Counter(str(value) for value in type_ids).items())),
        "path_token_ids": token_ids,
        "path_pair_ids": pair_ids,
        "path_type_ids": type_ids,
    }


def _candidate_token_values(sample: Any, index: int, attr_name: str) -> list[int]:
    values = getattr(sample, attr_name, None)
    mask = getattr(sample, "candidate_path_token_mask", None)
    if values is None or mask is None:
        return []
    value_tensor = values.detach().cpu()
    mask_tensor = mask.detach().cpu().bool()
    if int(index) < 0 or int(index) >= int(value_tensor.shape[0]):
        return []
    row = value_tensor[int(index)]
    row_mask = mask_tensor[int(index)]
    selected = row[row_mask]
    return [int(value) for value in selected.flatten().tolist() if int(value) != 0]


def _candidate_label(sample: Any, index: int, attr_name: str) -> int:
    values = getattr(sample, attr_name, None)
    if values is None:
        return 0
    tensor = values.detach().cpu().reshape(-1)
    if int(index) < 0 or int(index) >= int(tensor.numel()):
        return 0
    return int(float(tensor[int(index)].item()) > 0.5)


def _candidate_label_indices(sample: Any, attr_name: str) -> list[int]:
    values = getattr(sample, attr_name, None)
    if values is None:
        return []
    tensor = values.detach().cpu().reshape(-1)
    return [int(idx) for idx, value in enumerate(tensor.tolist()) if float(value) > 0.5]


def _token_union_for_indices(sample: Any, indices: list[int]) -> dict[str, Any]:
    token_values: list[int] = []
    pair_values: list[int] = []
    type_values: list[int] = []
    for index in indices:
        token_values.extend(_candidate_token_values(sample, int(index), "candidate_path_token_ids"))
        pair_values.extend(_candidate_token_values(sample, int(index), "candidate_path_pair_ids"))
        type_values.extend(_candidate_token_values(sample, int(index), "candidate_path_type_ids"))
    return {
        "candidate_index_count": len(indices),
        "token_count": len(token_values),
        "unique_token_count": len(set(token_values)),
        "unique_pair_count": len(set(pair_values)),
        "type_counts": dict(sorted(Counter(str(value) for value in type_values).items())),
        "token_set": sorted(set(token_values)),
        "pair_set": sorted(set(pair_values)),
    }


def _enrich_pair(
    pair: dict[str, Any],
    *,
    row_outputs: dict[int, dict[str, Any]],
    gate_config: dict[str, Any],
    margin_change_epsilon: float,
) -> dict[str, Any]:
    positive_idx = int(pair["positive_row_index"])
    negative_idx = int(pair["negative_row_index"])
    positive = row_outputs[positive_idx]
    negative = row_outputs[negative_idx]
    normal = _pair_margin_summary(
        positive["normal_scores"],
        negative["normal_scores"],
    )
    ablated = _pair_margin_summary(
        positive["ablated_scores"],
        negative["ablated_scores"],
    )
    margin_delta = {
        key: float(normal[f"{key}_margin"]) - float(ablated[f"{key}_margin"])
        for key in ("raw", "admission", "delay_risk")
    }
    selected_overlap = _selected_path_overlap(
        positive["normal_scores"],
        negative["normal_scores"],
    )
    positive_union = positive["normal_scores"]["safe_candidate_path_token_union"]
    if not positive_union["token_set"]:
        positive_union = positive["normal_scores"]["all_candidate_path_token_union"]
    negative_union = negative["normal_scores"]["all_candidate_path_token_union"]
    union_overlap = _path_set_overlap(positive_union, negative_union)
    path_helped = any(
        float(delta) > float(margin_change_epsilon) for delta in margin_delta.values()
    )
    path_hurt = any(
        float(delta) < -float(margin_change_epsilon) for delta in margin_delta.values()
    )
    path_changed = any(
        abs(float(delta)) > float(margin_change_epsilon) for delta in margin_delta.values()
    )
    return {
        **pair,
        "normal_recomputed": normal,
        "path_ablated_recomputed": ablated,
        "margin_delta_normal_minus_path_ablated": margin_delta,
        "normal_pair_pass": bool(normal["pair_pass"]),
        "path_ablated_pair_pass": bool(ablated["pair_pass"]),
        "path_ablation_repairs_failure": (not bool(normal["pair_pass"])) and bool(ablated["pair_pass"]),
        "path_ablation_breaks_pair": bool(normal["pair_pass"]) and not bool(ablated["pair_pass"]),
        "path_signal_helped_any_margin": path_helped,
        "path_signal_hurt_any_margin": path_hurt,
        "path_signal_changed_any_margin": path_changed,
        "selected_path_overlap": selected_overlap,
        "safe_or_all_positive_vs_negative_path_union_overlap": union_overlap,
        "positive_score_summary": _compact_score_summary(positive["normal_scores"]),
        "negative_score_summary": _compact_score_summary(negative["normal_scores"]),
        "positive_path_embedding_delta": positive["path_embedding_delta"],
        "negative_path_embedding_delta": negative["path_embedding_delta"],
        "positive_candidate_embedding_delta": positive["candidate_embedding_delta"],
        "negative_candidate_embedding_delta": negative["candidate_embedding_delta"],
        "diagnosis": _pair_diagnosis(
            normal=normal,
            ablated=ablated,
            margin_delta=margin_delta,
            selected_overlap=selected_overlap,
            union_overlap=union_overlap,
            positive_scores=positive["normal_scores"],
            negative_scores=negative["normal_scores"],
            margin_change_epsilon=margin_change_epsilon,
        ),
        "gate_config_subset": {
            "candidate_admission_score_mode": gate_config.get("candidate_admission_score_mode"),
            "candidate_delay_score_penalty": gate_config.get("candidate_delay_score_penalty"),
        },
        "diagnostic_only": True,
        "selector_can_certificate": False,
    }


def _pair_margin_summary(
    positive_scores: dict[str, Any],
    negative_scores: dict[str, Any],
) -> dict[str, Any]:
    raw_margin = _score(positive_scores, "raw") - _score(negative_scores, "raw")
    admission_margin = _score(positive_scores, "admission") - _score(negative_scores, "admission")
    delay_margin = _score(negative_scores, "delay_risk") - _score(positive_scores, "delay_risk")
    return {
        "raw_margin": float(raw_margin),
        "admission_margin": float(admission_margin),
        "delay_risk_margin": float(delay_margin),
        "raw_positive_above_negative": raw_margin > 0.0,
        "admission_positive_above_negative": admission_margin > 0.0,
        "positive_lower_delay_risk": delay_margin > 0.0,
        "pair_pass": raw_margin > 0.0 and admission_margin > 0.0 and delay_margin > 0.0,
    }


def _score(row_scores: dict[str, Any], key: str) -> float:
    value = row_scores[key].get("max_score")
    if value is None:
        return 0.0
    return float(value)


def _selected_path_overlap(
    positive_scores: dict[str, Any],
    negative_scores: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in ("raw", "admission", "delay_risk", "action_priority"):
        positive_candidate = positive_scores[key]["candidate"]
        negative_candidate = negative_scores[key]["candidate"]
        result[key] = _candidate_path_overlap(positive_candidate, negative_candidate)
    return result


def _candidate_path_overlap(
    positive_candidate: dict[str, Any],
    negative_candidate: dict[str, Any],
) -> dict[str, Any]:
    positive_tokens = [int(value) for value in positive_candidate.get("path_token_ids") or []]
    negative_tokens = [int(value) for value in negative_candidate.get("path_token_ids") or []]
    positive_pairs = [int(value) for value in positive_candidate.get("path_pair_ids") or []]
    negative_pairs = [int(value) for value in negative_candidate.get("path_pair_ids") or []]
    positive_types = [int(value) for value in positive_candidate.get("path_type_ids") or []]
    negative_types = [int(value) for value in negative_candidate.get("path_type_ids") or []]
    return {
        "positive_candidate_index": positive_candidate.get("index"),
        "negative_candidate_index": negative_candidate.get("index"),
        "positive_signature_id": positive_candidate.get("signature_id"),
        "negative_signature_id": negative_candidate.get("signature_id"),
        "token_jaccard": _jaccard(set(positive_tokens), set(negative_tokens)),
        "pair_jaccard": _jaccard(set(positive_pairs), set(negative_pairs)),
        "typed_token_jaccard": _jaccard(
            set(zip(positive_tokens, positive_types)),
            set(zip(negative_tokens, negative_types)),
        ),
        "token_lcs_ratio": _lcs_ratio(positive_tokens, negative_tokens),
        "exact_token_sequence_match": positive_tokens == negative_tokens,
        "positive_token_count": len(positive_tokens),
        "negative_token_count": len(negative_tokens),
    }


def _path_set_overlap(positive_union: dict[str, Any], negative_union: dict[str, Any]) -> dict[str, Any]:
    positive_tokens = set(int(value) for value in positive_union.get("token_set") or [])
    negative_tokens = set(int(value) for value in negative_union.get("token_set") or [])
    positive_pairs = set(int(value) for value in positive_union.get("pair_set") or [])
    negative_pairs = set(int(value) for value in negative_union.get("pair_set") or [])
    return {
        "token_jaccard": _jaccard(positive_tokens, negative_tokens),
        "pair_jaccard": _jaccard(positive_pairs, negative_pairs),
        "positive_unique_token_count": len(positive_tokens),
        "negative_unique_token_count": len(negative_tokens),
        "positive_candidate_index_count": int(positive_union.get("candidate_index_count") or 0),
        "negative_candidate_index_count": int(negative_union.get("candidate_index_count") or 0),
    }


def _summary_stats(
    pair_rows: list[dict[str, Any]],
    *,
    path_token_enabled: bool,
    margin_change_epsilon: float,
) -> dict[str, Any]:
    failed_count = len(pair_rows)
    ablation_repairs = sum(int(row["path_ablation_repairs_failure"]) for row in pair_rows)
    path_helped = sum(int(row["path_signal_helped_any_margin"]) for row in pair_rows)
    path_hurt = sum(int(row["path_signal_hurt_any_margin"]) for row in pair_rows)
    path_changed = sum(int(row["path_signal_changed_any_margin"]) for row in pair_rows)
    low_selected_overlap = sum(
        int(float(row["selected_path_overlap"]["raw"]["token_jaccard"]) < 0.5)
        for row in pair_rows
    )
    multi_candidate_positive = sum(
        int(int(row["positive_score_summary"]["candidate_count"]) > 1) for row in pair_rows
    )
    diagnosis_counts = Counter(str(row.get("diagnosis") or "") for row in pair_rows)
    return {
        "focused_failed_pair_count": failed_count,
        "path_token_encoder_enabled": bool(path_token_enabled),
        "margin_change_epsilon": float(margin_change_epsilon),
        "path_ablation_repairs_failure_count": ablation_repairs,
        "path_ablation_repairs_failure_rate": _rate(ablation_repairs, failed_count),
        "path_signal_helped_pair_count": path_helped,
        "path_signal_hurt_pair_count": path_hurt,
        "path_signal_changed_pair_count": path_changed,
        "low_selected_raw_path_overlap_pair_count": low_selected_overlap,
        "multi_candidate_positive_failure_count": multi_candidate_positive,
        "diagnosis_counts": dict(sorted(diagnosis_counts.items())),
        "primary": _dominant_key(diagnosis_counts),
    }


def _pair_diagnosis(
    *,
    normal: dict[str, Any],
    ablated: dict[str, Any],
    margin_delta: dict[str, float],
    selected_overlap: dict[str, Any],
    union_overlap: dict[str, Any],
    positive_scores: dict[str, Any],
    negative_scores: dict[str, Any],
    margin_change_epsilon: float,
) -> str:
    if (not bool(normal["pair_pass"])) and bool(ablated["pair_pass"]):
        return "path_token_branch_hurts_this_pair"
    if any(float(delta) > float(margin_change_epsilon) for delta in margin_delta.values()):
        if not bool(normal["pair_pass"]):
            return "path_token_branch_helps_but_head_still_fails"
        return "path_token_branch_helps_and_pair_passes"
    if any(float(delta) < -float(margin_change_epsilon) for delta in margin_delta.values()):
        return "path_token_branch_moves_margin_wrong_direction"
    raw_overlap = float(selected_overlap["raw"]["token_jaccard"])
    union_token_overlap = float(union_overlap["token_jaccard"])
    if raw_overlap < 0.5 and union_token_overlap < 0.5:
        return "path_tokens_distinct_but_score_insensitive"
    if int(positive_scores["candidate_count"]) > 1 and int(negative_scores["candidate_count"]) == 1:
        return "multi_candidate_positive_batch_primary_selection_confounder"
    return "path_token_effect_small_or_ambiguous"


def _recommend_next_step(summary: dict[str, Any]) -> dict[str, Any]:
    primary = str(summary.get("primary") or "")
    if primary == "path_token_branch_hurts_this_pair":
        return {
            "primary": "audit_path_token_collision_or_label_alignment_before_more_training",
            "reason": "masking path tokens repairs at least one focused failure",
            "avoid": "do_not_increase_path_weight_blindly",
        }
    if primary == "path_token_branch_helps_but_head_still_fails":
        return {
            "primary": "strengthen_targeted_context_pair_or_action_priority_comparator",
            "reason": "path-token signal moves margins in the right direction but is not decisive",
            "avoid": "do_not_add_duplicate_path_token_features",
        }
    if primary == "path_tokens_distinct_but_score_insensitive":
        return {
            "primary": "add_or_train_path_aware_context_pair_comparator_not_more_scalar_features",
            "reason": "path tokens are present and distinct, but current heads barely use them",
            "avoid": "do_not_relabel_v141_as_missing_path_tokens",
        }
    if primary == "multi_candidate_positive_batch_primary_selection_confounder":
        return {
            "primary": "audit_positive_batch_candidate_selection_and_safe_label_pooling",
            "reason": "a positive multi-candidate batch is compared against a single hard negative",
            "avoid": "do_not_treat_batch_label_as_single_candidate_label_without_audit",
        }
    return {
        "primary": "combine_path_token_attribution_with_context_pair_comparator_audit",
        "reason": "path-token influence is mixed or too small to close focused gate",
        "avoid": "do_not_advance_stage4_before_focused_gate_passes",
    }


def _compact_row_output(row_index: int, row_output: dict[str, Any]) -> dict[str, Any]:
    manifest_item = dict(row_output["manifest_item"])
    return {
        "row_index": int(row_index),
        "path": manifest_item.get("path"),
        "instance": manifest_item.get("instance"),
        "context_hash": manifest_item.get("context_hash"),
        "candidate_count": manifest_item.get("candidate_count"),
        "normal_scores": _compact_score_summary(row_output["normal_scores"]),
        "path_ablated_scores": _compact_score_summary(row_output["ablated_scores"]),
        "path_embedding_delta": row_output["path_embedding_delta"],
        "candidate_embedding_delta": row_output["candidate_embedding_delta"],
    }


def _compact_score_summary(scores: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_count": scores["candidate_count"],
        "safe_label_count": scores["safe_label_count"],
        "delay_label_count": scores["delay_label_count"],
        "raw": scores["raw"],
        "admission": scores["admission"],
        "delay_risk": scores["delay_risk"],
        "action_priority": scores["action_priority"],
        "all_candidate_path_token_union": _compact_token_union(
            scores["all_candidate_path_token_union"]
        ),
        "safe_candidate_path_token_union": _compact_token_union(
            scores["safe_candidate_path_token_union"]
        ),
        "delay_candidate_path_token_union": _compact_token_union(
            scores["delay_candidate_path_token_union"]
        ),
        "path_embedding_norms": scores["path_embedding_norms"],
        "candidate_embedding_norms": scores["candidate_embedding_norms"],
    }


def _compact_token_union(union: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in union.items()
        if key not in {"token_set", "pair_set"}
    }


def _embedding_delta_summary(
    normal: torch.Tensor | None,
    ablated: torch.Tensor | None,
) -> dict[str, Any]:
    if normal is None or ablated is None:
        return {"available": False}
    normal_cpu = normal.detach().cpu()
    ablated_cpu = ablated.detach().cpu()
    if normal_cpu.shape != ablated_cpu.shape:
        return {"available": False, "reason": "shape_mismatch"}
    delta = normal_cpu - ablated_cpu
    norms = torch.linalg.vector_norm(delta, dim=1) if delta.dim() == 2 else torch.abs(delta.reshape(-1))
    return {
        "available": True,
        "row_count": int(normal_cpu.shape[0]) if normal_cpu.dim() > 0 else 1,
        "mean_l2": _mean(_tensor_values(norms)),
        "max_l2": max(_tensor_values(norms), default=0.0),
    }


def _row_norm_summary(tensor: torch.Tensor | None) -> dict[str, Any]:
    if tensor is None:
        return {"available": False}
    tensor_cpu = tensor.detach().cpu()
    norms = torch.linalg.vector_norm(tensor_cpu, dim=1) if tensor_cpu.dim() == 2 else torch.abs(tensor_cpu.reshape(-1))
    values = _tensor_values(norms)
    return {
        "available": True,
        "mean_l2": _mean(values),
        "max_l2": max(values, default=0.0),
    }


def _candidate_admission_scores(
    candidate_scores: list[float],
    delay_scores: list[float],
    *,
    gate_config: dict[str, Any],
) -> list[float]:
    mode = str(gate_config.get("candidate_admission_score_mode", "high_priority") or "high_priority")
    if mode == "high_priority":
        return list(candidate_scores)
    penalty = max(0.0, float(gate_config.get("candidate_delay_score_penalty", 0.0) or 0.0))
    adjusted: list[float] = []
    for candidate_score, delay_score in zip(candidate_scores, delay_scores):
        risk_factor = max(0.0, min(1.0, 1.0 - float(delay_score)))
        adjusted.append(max(0.0, min(1.0, float(candidate_score) * (risk_factor ** penalty))))
    return adjusted


def _tensor_values(tensor: torch.Tensor) -> list[float]:
    return [float(value) for value in tensor.detach().cpu().reshape(-1).tolist()]


def _jaccard(left: set[Any], right: set[Any]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / float(len(union))


def _lcs_ratio(left: list[int], right: list[int]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    previous = [0] * (len(right) + 1)
    for left_value in left:
        current = [0]
        for col, right_value in enumerate(right, start=1):
            if left_value == right_value:
                current.append(previous[col - 1] + 1)
            else:
                current.append(max(previous[col], current[-1]))
        previous = current
    return previous[-1] / float(max(len(left), len(right)))


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(float(value) for value in values) / float(len(values))


def _rate(numerator: int, denominator: int) -> float | None:
    if int(denominator) <= 0:
        return None
    return float(numerator) / float(denominator)


def _dominant_key(counter: Counter[str]) -> str:
    if not counter:
        return "none"
    return sorted(counter.items(), key=lambda item: (-int(item[1]), str(item[0])))[0][0]


def _assert_offline_contract(checkpoint_data: dict[str, Any], training_metrics: dict[str, Any]) -> None:
    contract = dict(checkpoint_data.get("exactness_contract") or {})
    if contract.get("certificate_source") or contract.get("official_bound_effect"):
        raise ValueError("path-token attribution audit requires diagnostic-only checkpoint")
    if bool(training_metrics.get("production_ready")) or bool(training_metrics.get("stage4_candidate_ready")):
        raise ValueError("path-token attribution audit expects non-production training metrics")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _format_float(value: Any, digits: int = 6) -> str:
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return "NA"
    if not math.isfinite(value_float):
        return "NA"
    return f"{value_float:.{digits}f}"


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stats = summary["summary"]
    pair_rows = [
        json.loads(line)
        for line in Path(summary["pair_rows_path"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    lines = [
        "# 2026-06-23 BPC_future GAT Stage 3 v142 Path-token 失败归因审计",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 结论",
        "",
        "本轮只审计 v140 剩余 focused pair failures 的 path-token 输入和消融影响，",
        "不运行 BPC、pricing、RMP、worker 或 certificate。",
        "",
        "```text",
        f"checkpoint = {summary['checkpoint']}",
        f"metrics = {summary['metrics']}",
        f"failed_pair_count = {stats['focused_failed_pair_count']}",
        f"path_token_encoder_enabled = {str(stats['path_token_encoder_enabled']).lower()}",
        "path_ablation_repairs_failure_count = "
        f"{stats['path_ablation_repairs_failure_count']}",
        f"path_signal_helped_pair_count = {stats['path_signal_helped_pair_count']}",
        f"path_signal_hurt_pair_count = {stats['path_signal_hurt_pair_count']}",
        "low_selected_raw_path_overlap_pair_count = "
        f"{stats['low_selected_raw_path_overlap_pair_count']}",
        f"primary = {stats['primary']}",
        f"recommended_next_step = {summary['recommended_next_step']['primary']}",
        "stage4_candidate_ready = false",
        "production_ready = false",
        "selector_can_certificate = false",
        "```",
        "",
        "## 解释",
        "",
        "v141 的 feature-structure 报告提示 `selected_arc_option_sequence` 欠指定。",
        "本轮核对当前模型后，需要把这个结论收窄：v140 checkpoint 实际启用了",
        "`PathTokenEncoder`，数据样本也包含 `candidate_path_token_ids / pair_ids / type_ids / mask`。",
        "因此问题不是“完全没有 path token”，而是 path-token 分支是否足以改变",
        "context-local positive-vs-hard-negative 排序。",
        "",
        "## 剩余失败 Pair",
        "",
        "| context | family | pair | raw | adm | delay | ablated raw | ablated adm | ablated delay | raw path J | diagnosis |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in pair_rows:
        normal = row["normal_recomputed"]
        ablated = row["path_ablated_recomputed"]
        raw_overlap = row["selected_path_overlap"]["raw"]["token_jaccard"]
        lines.append(
            "| {context} | {family} | {pair} | {raw} | {adm} | {delay} | "
            "{abl_raw} | {abl_adm} | {abl_delay} | {jaccard} | {diagnosis} |".format(
                context=row["context_hash"],
                family=row["family"],
                pair=f"{row['positive_row_index']}>{row['negative_row_index']}",
                raw=_format_float(normal["raw_margin"]),
                adm=_format_float(normal["admission_margin"]),
                delay=_format_float(normal["delay_risk_margin"]),
                abl_raw=_format_float(ablated["raw_margin"]),
                abl_adm=_format_float(ablated["admission_margin"]),
                abl_delay=_format_float(ablated["delay_risk_margin"]),
                jaccard=_format_float(raw_overlap, 3),
                diagnosis=row["diagnosis"],
            )
        )
    lines.extend(
        [
            "",
            "## 判断",
            "",
            "- path token 已进入模型输入，不能再把下一步简单描述为“添加 path token”；",
            "- 如果 path 消融后失败仍在，说明当前 head/comparator 对已有 path-token 信号利用不足；",
            "- 如果某个 pair 消融后反而修复，说明 path-token 分支可能在该局部给出误导信号，需要查 token collision 或 label 对齐；",
            "- 无论哪一种，本轮都不满足 focused gate，不能进入 Stage 4。",
            "",
            "## Exactness Boundary",
            "",
            "```text",
            "diagnostic_only = true",
            "runs_bpc_or_pricing = false",
            "runs_rmp = false",
            "production_ready = false",
            "default_enabled = false",
            "stage3_completed = false",
            "stage4_candidate_ready = false",
            "selector_is_pricing_oracle = false",
            "selector_can_certificate = false",
            "gate_can_permanently_discard_negative_columns = false",
            "```",
            "",
            "最终 certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。",
            "",
            "## Output Artifacts",
            "",
            "```text",
            f"summary = {summary['output_dir']}/summary.json",
            f"pairs = {summary['pair_rows_path']}",
            f"rows = {summary['row_rows_path']}",
            "```",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
