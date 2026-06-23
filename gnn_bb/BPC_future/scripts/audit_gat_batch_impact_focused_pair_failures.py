#!/usr/bin/env python3
"""Audit focused positive-vs-hard-negative pair failure anatomy.

This diagnostic reads an offline GAT batch-impact training metrics file and
the corresponding batch-impact dataset. It classifies focused same-context
pair failures by score margin, context, candidate signature overlap, path token
overlap, and selected slack / batch features. It does not run BPC, pricing,
RMP, workers, or certificate logic.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from statistics import mean, median
from typing import Any


DEFAULT_METRICS = Path(
    "BPC_future/results/"
    "gat_batch_impact_training_v96_seed13_explicit_focused_tranche_v75_delay_risk_pairwise_20260617/"
    "metrics.json"
)
DEFAULT_DATASET_DIR = Path("BPC_future/data/gat_batch_impact/v75_v66_path_tokens_slack_20260617")
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v98_v96_20260617"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260617_bpc_future_gat_target_mode_stage3_v98_focused_pair_failure_anatomy_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--near-margin-abs",
        type=float,
        default=0.01,
        help="Absolute score margin treated as near-zero / trainable by loss pressure.",
    )
    parser.add_argument(
        "--deep-margin-abs",
        type=float,
        default=0.05,
        help="Negative score margin whose magnitude is treated as a deep ordering gap.",
    )
    parser.add_argument("--top-contexts", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_focused_pair_failures(
        metrics=Path(args.metrics),
        dataset_dir=Path(args.dataset_dir),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        near_margin_abs=float(args.near_margin_abs),
        deep_margin_abs=float(args.deep_margin_abs),
        top_contexts=max(1, int(args.top_contexts)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def audit_focused_pair_failures(
    *,
    metrics: Path = DEFAULT_METRICS,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    near_margin_abs: float = 0.01,
    deep_margin_abs: float = 0.05,
    top_contexts: int = 20,
) -> dict[str, Any]:
    metrics = Path(metrics)
    dataset_dir = Path(dataset_dir)
    output_dir = Path(output_dir)
    training_metrics = _read_json(metrics)
    manifest = _read_json(dataset_dir / "manifest.json")
    _assert_offline_contract(training_metrics, manifest)

    pair_rows = list(
        dict(row)
        for row in (training_metrics.get("focused_pair_gate") or {}).get("pair_rows", [])
    )
    row_index = {
        int(item.get("row_index") or 0): item
        for item in manifest.get("samples", [])
    }
    sample_summaries = _sample_feature_summaries(
        dataset_dir,
        row_index,
        pair_rows,
        manifest=manifest,
    )
    enriched_pairs = [
        _enrich_pair(
            pair,
            row_index=row_index,
            sample_summaries=sample_summaries,
            near_margin_abs=near_margin_abs,
            deep_margin_abs=deep_margin_abs,
        )
        for pair in pair_rows
    ]
    context_rows = _context_rows(enriched_pairs)
    summary_stats = _summary_stats(
        enriched_pairs,
        context_rows,
        near_margin_abs=near_margin_abs,
        deep_margin_abs=deep_margin_abs,
    )
    recommendation = _recommend_next_step(summary_stats)

    output_dir.mkdir(parents=True, exist_ok=True)
    pair_path = output_dir / "focused_pair_failure_rows.jsonl"
    context_path = output_dir / "focused_pair_failure_contexts.jsonl"
    _write_jsonl(pair_path, enriched_pairs)
    _write_jsonl(context_path, context_rows)

    summary = {
        "schema_version": "gat_batch_impact_focused_pair_failure_audit_v1",
        "status": "gat_batch_impact_focused_pair_failures_audited",
        "metrics": str(metrics),
        "dataset_dir": str(dataset_dir),
        "output_dir": str(output_dir),
        "focused_pair_failure_rows_path": str(pair_path),
        "focused_pair_failure_contexts_path": str(context_path),
        "near_margin_abs": float(near_margin_abs),
        "deep_margin_abs": float(deep_margin_abs),
        "sample_count": int(manifest.get("sample_count") or 0),
        "pair_count": len(pair_rows),
        "summary": summary_stats,
        "top_contexts_by_failure": sorted(
            context_rows,
            key=lambda row: (int(row["failed_pair_count"]), int(row["pair_count"])),
            reverse=True,
        )[: int(top_contexts)],
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


def _sample_feature_summaries(
    dataset_dir: Path,
    row_index: dict[int, dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    *,
    manifest: dict[str, Any],
) -> dict[int, dict[str, Any]]:
    needed = {
        int(pair.get("positive_row_index"))
        for pair in pair_rows
        if pair.get("positive_row_index") is not None
    } | {
        int(pair.get("negative_row_index"))
        for pair in pair_rows
        if pair.get("negative_row_index") is not None
    }
    summaries: dict[int, dict[str, Any]] = {}
    for idx in sorted(needed):
        item = row_index.get(idx)
        if item is None:
            summaries[idx] = {"feature_available": False, "missing_reason": "manifest_row_missing"}
            continue
        path = dataset_dir / str(item.get("path") or "")
        summaries[idx] = _load_sample_feature_summary(path, manifest=manifest)
    return summaries


def _load_sample_feature_summary(path: Path, *, manifest: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return {"feature_available": False, "missing_reason": "sample_file_missing"}
    try:
        import torch
    except ImportError:
        return {"feature_available": False, "missing_reason": "torch_not_available"}
    try:
        sample = torch.load(path, map_location="cpu", weights_only=False)
    except Exception as exc:  # pragma: no cover - defensive diagnostic path.
        return {"feature_available": False, "missing_reason": f"sample_load_failed:{exc}"}

    candidate_schema = list(manifest.get("candidate_feature_schema") or [])
    batch_schema = list(manifest.get("batch_feature_schema") or [])
    return {
        "feature_available": True,
        "candidate_count": _tensor_row_count(getattr(sample, "candidate_features", None)),
        "candidate_feature_summary": _candidate_feature_summary(
            getattr(sample, "candidate_features", None),
            candidate_schema,
        ),
        "batch_feature_summary": _named_tensor_values(
            getattr(sample, "batch_features", None),
            batch_schema,
            names=[
                "negative_candidate_count",
                "best_true_reduced_cost",
                "mean_true_reduced_cost",
                "replacement_ratio",
                "support_changing_ratio",
                "batch_type_new_task_set",
                "batch_type_replacement_heavy",
                "batch_type_active_support_overlap",
            ],
        ),
        "path_token_summary": _path_token_summary(sample),
    }


def _candidate_feature_summary(
    tensor: Any,
    schema: list[str],
) -> dict[str, Any]:
    names = [
        "true_reduced_cost",
        "cost",
        "sequence_length",
        "sortie_count",
        "trace_trip_count",
        "trace_arc_option_count",
        "trace_unique_arc_option_count",
        "trace_total_distance",
        "trace_total_energy",
        "trace_total_risk",
        "trace_total_travel_time",
        "trace_min_survival_energy",
        "trace_service_start_span",
        "trace_idle_time_proxy",
        "slack_min_late_time",
        "slack_mean_late_time",
        "slack_min_early_time",
    ]
    if tensor is None or not hasattr(tensor, "detach"):
        return {}
    rows = tensor.detach().cpu()
    if len(getattr(rows, "shape", [])) != 2:
        return {}
    result: dict[str, Any] = {}
    for name in names:
        if name not in schema:
            continue
        idx = schema.index(name)
        if idx >= int(rows.shape[1]):
            continue
        values = [float(value) for value in rows[:, idx].tolist()]
        result[name] = _distribution(values)
    return result


def _named_tensor_values(tensor: Any, schema: list[str], *, names: list[str]) -> dict[str, float]:
    if tensor is None or not hasattr(tensor, "detach"):
        return {}
    values = tensor.detach().cpu().flatten().tolist()
    result: dict[str, float] = {}
    for name in names:
        if name not in schema:
            continue
        idx = schema.index(name)
        if idx < len(values):
            result[name] = float(values[idx])
    return result


def _path_token_summary(sample: Any) -> dict[str, Any]:
    token_ids = getattr(sample, "candidate_path_token_ids", None)
    token_mask = getattr(sample, "candidate_path_token_mask", None)
    type_ids = getattr(sample, "candidate_path_type_ids", None)
    tokens = _masked_int_values(token_ids, token_mask)
    types = _masked_int_values(type_ids, token_mask)
    return {
        "token_count": len(tokens),
        "unique_token_count": len(set(tokens)),
        "type_counts": dict(sorted(Counter(str(value) for value in types).items())),
        "token_set": sorted(set(tokens)),
    }


def _masked_int_values(values: Any, mask: Any) -> list[int]:
    if values is None or not hasattr(values, "detach"):
        return []
    value_tensor = values.detach().cpu()
    if mask is None or not hasattr(mask, "detach"):
        mask_tensor = value_tensor != 0
    else:
        mask_tensor = mask.detach().cpu().bool()
    selected = value_tensor[mask_tensor]
    return [int(value) for value in selected.flatten().tolist() if int(value) != 0]


def _enrich_pair(
    pair: dict[str, Any],
    *,
    row_index: dict[int, dict[str, Any]],
    sample_summaries: dict[int, dict[str, Any]],
    near_margin_abs: float,
    deep_margin_abs: float,
) -> dict[str, Any]:
    positive_idx = int(pair.get("positive_row_index") or -1)
    negative_idx = int(pair.get("negative_row_index") or -1)
    positive_item = row_index.get(positive_idx, {})
    negative_item = row_index.get(negative_idx, {})
    positive_features = sample_summaries.get(positive_idx, {})
    negative_features = sample_summaries.get(negative_idx, {})
    raw_margin = _float(pair.get("raw_margin"))
    admission_margin = _float(pair.get("admission_margin"))
    delay_margin = _float(pair.get("delay_risk_margin"))
    batch_margin = _float(pair.get("batch_margin"))
    positive_signatures = set(str(value) for value in pair.get("positive_signature_ids") or [])
    negative_signatures = set(str(value) for value in pair.get("negative_signature_ids") or [])
    signature_overlap = positive_signatures & negative_signatures
    positive_tokens = set(
        int(value)
        for value in (
            positive_features.get("path_token_summary", {}).get("token_set", [])
            if positive_features
            else []
        )
    )
    negative_tokens = set(
        int(value)
        for value in (
            negative_features.get("path_token_summary", {}).get("token_set", [])
            if negative_features
            else []
        )
    )
    failure_modes = _failure_modes(
        raw_margin=raw_margin,
        admission_margin=admission_margin,
        delay_margin=delay_margin,
    )
    margin_buckets = {
        "raw": _margin_bucket(raw_margin, near_margin_abs, deep_margin_abs),
        "admission": _margin_bucket(admission_margin, near_margin_abs, deep_margin_abs),
        "delay_risk": _margin_bucket(delay_margin, near_margin_abs, deep_margin_abs),
        "batch": _margin_bucket(batch_margin, near_margin_abs, deep_margin_abs),
    }
    failed_margins = [
        value
        for name, value in (
            ("raw_order_fail", raw_margin),
            ("admission_order_fail", admission_margin),
            ("delay_risk_order_fail", delay_margin),
        )
        if name in failure_modes
    ]
    return {
        **pair,
        "task_count": int(positive_item.get("task_count") or negative_item.get("task_count") or 0),
        "positive_instance": str(positive_item.get("instance") or ""),
        "negative_instance": str(negative_item.get("instance") or ""),
        "positive_candidate_count": int(positive_item.get("candidate_count") or 0),
        "negative_candidate_count": int(negative_item.get("candidate_count") or 0),
        "failure_modes": failure_modes,
        "margin_buckets": margin_buckets,
        "failed_head_count": len(failure_modes),
        "all_failed_heads_near": bool(
            failed_margins and all(abs(value) <= float(near_margin_abs) for value in failed_margins)
        ),
        "any_failed_head_deep": bool(
            any(value <= -float(deep_margin_abs) for value in failed_margins)
        ),
        "signature_overlap_count": len(signature_overlap),
        "signature_jaccard": _jaccard(positive_signatures, negative_signatures),
        "signature_overlap_ids": sorted(signature_overlap),
        "path_token_jaccard": _jaccard(positive_tokens, negative_tokens),
        "positive_feature_summary": _compact_feature_summary(positive_features),
        "negative_feature_summary": _compact_feature_summary(negative_features),
        "feature_delta_summary": _feature_delta_summary(positive_features, negative_features),
        "diagnosis": _pair_diagnosis(
            failure_modes=failure_modes,
            failed_margins=failed_margins,
            signature_overlap_count=len(signature_overlap),
            signature_jaccard=_jaccard(positive_signatures, negative_signatures),
            path_token_jaccard=_jaccard(positive_tokens, negative_tokens),
            near_margin_abs=near_margin_abs,
            deep_margin_abs=deep_margin_abs,
        ),
        "diagnostic_only": True,
        "selector_can_certificate": False,
    }


def _failure_modes(
    *,
    raw_margin: float,
    admission_margin: float,
    delay_margin: float,
) -> list[str]:
    modes: list[str] = []
    if raw_margin <= 0.0:
        modes.append("raw_order_fail")
    if admission_margin <= 0.0:
        modes.append("admission_order_fail")
    if delay_margin <= 0.0:
        modes.append("delay_risk_order_fail")
    return modes


def _pair_diagnosis(
    *,
    failure_modes: list[str],
    failed_margins: list[float],
    signature_overlap_count: int,
    signature_jaccard: float,
    path_token_jaccard: float,
    near_margin_abs: float,
    deep_margin_abs: float,
) -> str:
    if not failure_modes:
        return "pair_passes"
    if failed_margins and all(abs(value) <= float(near_margin_abs) for value in failed_margins):
        if signature_overlap_count > 0:
            return "near_margin_with_shared_signature"
        return "near_margin_loss_tuning_candidate"
    if any(value <= -float(deep_margin_abs) for value in failed_margins):
        if signature_jaccard >= 0.5 or path_token_jaccard >= 0.5:
            return "deep_gap_despite_high_path_or_signature_overlap"
        return "deep_structural_score_gap"
    if signature_overlap_count > 0:
        return "shared_signature_confounder"
    return "mixed_margin_failure"


def _context_rows(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in pairs:
        groups[str(pair.get("context_key") or pair.get("context_hash") or "")].append(pair)
    rows: list[dict[str, Any]] = []
    for key, group in sorted(groups.items()):
        first = group[0]
        failed = [pair for pair in group if pair.get("failure_modes")]
        diagnosis_counts = Counter(str(pair.get("diagnosis")) for pair in group)
        mode_counts = Counter(
            mode
            for pair in group
            for mode in pair.get("failure_modes", [])
        )
        rows.append(
            {
                "context_key": key,
                "context_hash": str(first.get("context_hash") or ""),
                "family": str(first.get("family") or ""),
                "task_count": int(first.get("task_count") or 0),
                "pair_count": len(group),
                "failed_pair_count": len(failed),
                "pair_pass_count": len(group) - len(failed),
                "raw_fail_count": int(mode_counts.get("raw_order_fail", 0)),
                "admission_fail_count": int(mode_counts.get("admission_order_fail", 0)),
                "delay_risk_fail_count": int(mode_counts.get("delay_risk_order_fail", 0)),
                "all_failed_heads_near_count": sum(
                    int(bool(pair.get("all_failed_heads_near"))) for pair in failed
                ),
                "any_failed_head_deep_count": sum(
                    int(bool(pair.get("any_failed_head_deep"))) for pair in failed
                ),
                "signature_overlap_pair_count": sum(
                    int(int(pair.get("signature_overlap_count") or 0) > 0) for pair in group
                ),
                "mean_signature_jaccard": _mean_or_none(
                    [_float(pair.get("signature_jaccard")) for pair in group]
                ),
                "mean_path_token_jaccard": _mean_or_none(
                    [_float(pair.get("path_token_jaccard")) for pair in group]
                ),
                "min_raw_margin": _min_or_none([_float(pair.get("raw_margin")) for pair in group]),
                "min_admission_margin": _min_or_none(
                    [_float(pair.get("admission_margin")) for pair in group]
                ),
                "min_delay_risk_margin": _min_or_none(
                    [_float(pair.get("delay_risk_margin")) for pair in group]
                ),
                "diagnosis_counts": dict(sorted(diagnosis_counts.items())),
                "primary": _dominant_key(diagnosis_counts),
                "diagnostic_only": True,
            }
        )
    return rows


def _summary_stats(
    pairs: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    *,
    near_margin_abs: float,
    deep_margin_abs: float,
) -> dict[str, Any]:
    failed = [pair for pair in pairs if pair.get("failure_modes")]
    mode_counts = Counter(mode for pair in pairs for mode in pair.get("failure_modes", []))
    diagnosis_counts = Counter(str(pair.get("diagnosis")) for pair in pairs)
    raw_failed = [pair for pair in failed if "raw_order_fail" in pair.get("failure_modes", [])]
    admission_failed = [
        pair for pair in failed if "admission_order_fail" in pair.get("failure_modes", [])
    ]
    delay_failed = [
        pair for pair in failed if "delay_risk_order_fail" in pair.get("failure_modes", [])
    ]
    near_failed = [pair for pair in failed if bool(pair.get("all_failed_heads_near"))]
    deep_failed = [pair for pair in failed if bool(pair.get("any_failed_head_deep"))]
    signature_overlap = [
        pair for pair in pairs if int(pair.get("signature_overlap_count") or 0) > 0
    ]
    path_jaccards = [_float(pair.get("path_token_jaccard")) for pair in pairs]
    return {
        "pair_count": len(pairs),
        "failed_pair_count": len(failed),
        "pair_pass_count": len(pairs) - len(failed),
        "strict_pair_pass_rate": _rate(len(pairs) - len(failed), len(pairs)),
        "raw_fail_count": int(mode_counts.get("raw_order_fail", 0)),
        "admission_fail_count": int(mode_counts.get("admission_order_fail", 0)),
        "delay_risk_fail_count": int(mode_counts.get("delay_risk_order_fail", 0)),
        "raw_fail_rate": _rate(len(raw_failed), len(pairs)),
        "admission_fail_rate": _rate(len(admission_failed), len(pairs)),
        "delay_risk_fail_rate": _rate(len(delay_failed), len(pairs)),
        "all_failed_heads_near_count": len(near_failed),
        "all_failed_heads_near_rate_among_failed": _rate(len(near_failed), len(failed)),
        "any_failed_head_deep_count": len(deep_failed),
        "any_failed_head_deep_rate_among_failed": _rate(len(deep_failed), len(failed)),
        "signature_overlap_pair_count": len(signature_overlap),
        "signature_overlap_pair_rate": _rate(len(signature_overlap), len(pairs)),
        "path_token_jaccard_median": _median_or_none(path_jaccards),
        "path_token_jaccard_mean": _mean_or_none(path_jaccards),
        "raw_margin_stats": _distribution([_float(pair.get("raw_margin")) for pair in pairs]),
        "admission_margin_stats": _distribution(
            [_float(pair.get("admission_margin")) for pair in pairs]
        ),
        "delay_risk_margin_stats": _distribution(
            [_float(pair.get("delay_risk_margin")) for pair in pairs]
        ),
        "diagnosis_counts": dict(sorted(diagnosis_counts.items())),
        "context_count": len(context_rows),
        "contexts_with_failure_count": sum(
            int(int(row.get("failed_pair_count") or 0) > 0) for row in context_rows
        ),
        "near_margin_abs": float(near_margin_abs),
        "deep_margin_abs": float(deep_margin_abs),
        "primary": _dominant_key(diagnosis_counts),
    }


def _recommend_next_step(summary: dict[str, Any]) -> dict[str, Any]:
    failed = int(summary.get("failed_pair_count") or 0)
    if failed <= 0:
        return {
            "primary": "focused_pair_gate_passed_move_to_global_stage3_gate",
            "reason": "no focused pair ordering failures were found",
        }
    near_rate = float(summary.get("all_failed_heads_near_rate_among_failed") or 0.0)
    deep_rate = float(summary.get("any_failed_head_deep_rate_among_failed") or 0.0)
    raw_fail_rate = float(summary.get("raw_fail_rate") or 0.0)
    delay_fail_rate = float(summary.get("delay_risk_fail_rate") or 0.0)
    signature_rate = float(summary.get("signature_overlap_pair_rate") or 0.0)
    if near_rate >= 0.70 and deep_rate <= 0.10:
        return {
            "primary": "train_combined_focused_candidate_admission_delay_loss",
            "reason": "most failed focused pairs are near-margin rather than deep structural gaps",
            "avoid": "do_not_collect_more_data_before_testing_explicit_tranche_full_training",
        }
    if raw_fail_rate >= 0.40 and signature_rate >= 0.40:
        return {
            "primary": "repair_candidate_action_consequence_representation",
            "reason": "raw candidate ordering fails frequently with shared signatures",
            "avoid": "do_not_lower_candidate_threshold",
        }
    if delay_fail_rate >= 0.40:
        return {
            "primary": "train_delay_risk_head_with_explicit_focused_tranche",
            "reason": "delay-risk ordering remains the dominant focused pair failure",
            "avoid": "do_not_use_delay_gate_as_certificate_or_hard_prune",
        }
    return {
        "primary": "add_or_repair_context_action_consequence_features_before_more_sweeps",
        "reason": "focused pair failures include non-near mixed/deep margins",
        "avoid": "do_not_continue_blind_multiplier_sweeps",
    }


def _compact_feature_summary(features: dict[str, Any]) -> dict[str, Any]:
    if not features or not bool(features.get("feature_available")):
        return {"feature_available": False, "missing_reason": features.get("missing_reason")}
    path_summary = dict(features.get("path_token_summary") or {})
    path_summary.pop("token_set", None)
    return {
        "feature_available": True,
        "candidate_count": features.get("candidate_count"),
        "candidate_feature_summary": features.get("candidate_feature_summary", {}),
        "batch_feature_summary": features.get("batch_feature_summary", {}),
        "path_token_summary": path_summary,
    }


def _feature_delta_summary(
    positive: dict[str, Any],
    negative: dict[str, Any],
) -> dict[str, Any]:
    if not positive or not negative:
        return {}
    result: dict[str, Any] = {}
    for name in (
        "slack_min_late_time",
        "slack_mean_late_time",
        "slack_min_early_time",
        "trace_min_survival_energy",
        "trace_total_risk",
        "trace_idle_time_proxy",
    ):
        p_value = _nested_feature_mean(positive, name)
        n_value = _nested_feature_mean(negative, name)
        if p_value is not None and n_value is not None:
            result[f"{name}_mean_delta"] = float(p_value) - float(n_value)
    for name in (
        "best_true_reduced_cost",
        "mean_true_reduced_cost",
        "negative_candidate_count",
        "replacement_ratio",
        "support_changing_ratio",
    ):
        p_batch = (positive.get("batch_feature_summary") or {}).get(name)
        n_batch = (negative.get("batch_feature_summary") or {}).get(name)
        if p_batch is not None and n_batch is not None:
            result[f"{name}_delta"] = float(p_batch) - float(n_batch)
    return result


def _nested_feature_mean(features: dict[str, Any], name: str) -> float | None:
    values = (
        features.get("candidate_feature_summary", {})
        .get(name, {})
    )
    if not values or values.get("mean") is None:
        return None
    return float(values["mean"])


def _margin_bucket(value: float, near_margin_abs: float, deep_margin_abs: float) -> str:
    if value > float(near_margin_abs):
        return "positive_clear"
    if value > 0.0:
        return "positive_near"
    if abs(value) <= float(near_margin_abs):
        return "negative_or_zero_near"
    if value <= -float(deep_margin_abs):
        return "negative_deep"
    return "negative_mid"


def _distribution(values: list[float]) -> dict[str, Any]:
    clean = [float(value) for value in values if value is not None]
    if not clean:
        return {"count": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "count": len(clean),
        "min": min(clean),
        "median": float(median(clean)),
        "mean": float(mean(clean)),
        "max": max(clean),
    }


def _tensor_row_count(tensor: Any) -> int:
    if tensor is None or not hasattr(tensor, "shape") or len(tensor.shape) <= 0:
        return 0
    return int(tensor.shape[0])


def _jaccard(left: set[Any], right: set[Any]) -> float:
    if not left and not right:
        return 0.0
    return len(left & right) / float(len(left | right))


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _rate(count: int, total: int) -> float | None:
    if total <= 0:
        return None
    return float(count) / float(total)


def _mean_or_none(values: list[float]) -> float | None:
    return float(mean(values)) if values else None


def _median_or_none(values: list[float]) -> float | None:
    return float(median(values)) if values else None


def _min_or_none(values: list[float]) -> float | None:
    return min(values) if values else None


def _dominant_key(counter: Counter[str]) -> str:
    if not counter:
        return "none"
    return sorted(counter.items(), key=lambda item: (item[1], item[0]), reverse=True)[0][0]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )


def _assert_offline_contract(metrics: dict[str, Any], manifest: dict[str, Any]) -> None:
    if bool(metrics.get("production_ready", False)):
        raise ValueError("metrics unexpectedly marks production_ready=true")
    if bool(manifest.get("production_ready", False)):
        raise ValueError("manifest unexpectedly marks production_ready=true")
    if bool(manifest.get("runs_bpc_or_pricing", False)):
        raise ValueError("focused pair failure audit requires offline dataset manifest")


def _write_report(report: Path, summary: dict[str, Any]) -> None:
    s = summary["summary"]
    lines = [
        _report_title(report),
        "",
        "## 目的",
        "",
        "对指定 checkpoint 的 focused same-context positive/negative pair failures 做离线分类，",
        "判断失败更像 near-margin loss tuning 问题，还是 candidate/action-consequence",
        "表示结构性不可分问题。该审计只读 metrics / dataset，不运行 BPC / pricing / RMP / worker / certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_batch_impact_focused_pair_failure_audit = current",
        f"status = {summary['status']}",
        f"pair_count = {s['pair_count']}",
        f"failed_pair_count = {s['failed_pair_count']}",
        f"strict_pair_pass_rate = {s['strict_pair_pass_rate']}",
        f"raw_fail_rate = {s['raw_fail_rate']}",
        f"admission_fail_rate = {s['admission_fail_rate']}",
        f"delay_risk_fail_rate = {s['delay_risk_fail_rate']}",
        f"all_failed_heads_near_rate_among_failed = {s['all_failed_heads_near_rate_among_failed']}",
        f"any_failed_head_deep_rate_among_failed = {s['any_failed_head_deep_rate_among_failed']}",
        f"signature_overlap_pair_rate = {s['signature_overlap_pair_rate']}",
        f"path_token_jaccard_median = {s['path_token_jaccard_median']}",
        f"primary = {s['primary']}",
        f"recommended_next_step = {summary['recommended_next_step']['primary']}",
        "stage3_completed = false",
        "stage4_candidate_ready = false",
        "production_ready = false",
        "selector_can_certificate = false",
        "all_checks_pass = true",
        "```",
        "",
        "## 关键结论",
        "",
        f"- focused pair 总数：`{s['pair_count']}`，失败：`{s['failed_pair_count']}`。",
        f"- near-margin 失败占失败 pair：`{s['all_failed_heads_near_rate_among_failed']}`。",
        f"- deep 失败占失败 pair：`{s['any_failed_head_deep_rate_among_failed']}`。",
        f"- signature overlap pair rate：`{s['signature_overlap_pair_rate']}`。",
        f"- 主要诊断：`{s['primary']}`。",
        "",
        "## Recommended Next Step",
        "",
        "```json",
        json.dumps(summary["recommended_next_step"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Margin Stats",
        "",
        "```json",
        json.dumps(
            {
                "raw_margin_stats": s["raw_margin_stats"],
                "admission_margin_stats": s["admission_margin_stats"],
                "delay_risk_margin_stats": s["delay_risk_margin_stats"],
                "diagnosis_counts": s["diagnosis_counts"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Top Contexts",
        "",
        "```json",
        json.dumps(summary["top_contexts_by_failure"][:10], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Output Artifacts",
        "",
        "```text",
        f"summary = {summary['output_dir']}/summary.json",
        f"pair_rows = {summary['focused_pair_failure_rows_path']}",
        f"context_rows = {summary['focused_pair_failure_contexts_path']}",
        "```",
        "",
        "## Exactness Boundary",
        "",
        "- `diagnostic_only=true`；",
        "- `runs_bpc_or_pricing=false`；",
        "- `runs_rmp=false`；",
        "- `production_ready=false`；",
        "- `selector_is_pricing_oracle=false`；",
        "- `selector_can_certificate=false`；",
        "- `gate_can_permanently_discard_negative_columns=false`；",
        "- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。",
        "",
    ]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")


def _report_title(report: Path) -> str:
    stem = Path(report).stem
    parts = stem.split("_")
    date = parts[0] if parts and parts[0].isdigit() and len(parts[0]) == 8 else ""
    version = next((part for part in parts if part.startswith("v") and part[1:].isdigit()), "current")
    if date:
        date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        return f"# {date} BPC_future GAT Stage 3 {version} Focused Pair Failure Anatomy 报告"
    return f"# BPC_future GAT Stage 3 {version} Focused Pair Failure Anatomy 报告"


if __name__ == "__main__":
    raise SystemExit(main())
