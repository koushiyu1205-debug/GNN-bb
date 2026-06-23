#!/usr/bin/env python3
"""Build offline GAT batch-impact samples from same-context intervention rows.

The input rows are produced by ``build_gat_same_run_batch_impact_dataset.py``.
Each output sample contains the logical graph, one returned candidate journey
batch, ordered candidate task positions, RMP/context features, batch features,
and multi-head trajectory labels for ``GATBatchImpactModel``.

Exactness boundary:
* diagnostic/offline only;
* does not run BPC, pricing, RMP, workers, or certificates;
* does not create official bounds or no-negative certificates;
* true-RC negative candidates from non-improving batches remain delay labels,
  not permanent reject labels.
"""

from __future__ import annotations

import argparse
from collections import Counter
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

from BPC_future.learning.batch_impact_model import batch_impact_exactness_contract
from BPC_future.learning.graph_builder import FutureGraphBuilder
from BPC_future.scripts.build_gnn_column_selector_dataset import (
    CANDIDATE_FEATURE_SCHEMA as BASE_CANDIDATE_FEATURE_SCHEMA,
    CONTEXT_FEATURE_SCHEMA as BASE_CONTEXT_FEATURE_SCHEMA,
)
from BPC_future.solver.gat_candidate_id import journey_gat_candidate_id_from_signature


DEFAULT_INPUT = Path(
    "BPC_future/results/gat_same_run_batch_impact_dataset_20260615/"
    "same_run_batch_impact_rows.jsonl"
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/data/gat_batch_impact/v1")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260615_bpc_future_gat_batch_impact_dataset_zh.md"
)
PATH_TOKEN_HASH_BUCKET_COUNT = 4096
PATH_PAIR_HASH_BUCKET_COUNT = 4096
PATH_TYPE_TO_ID: dict[str, int] = {
    "low_time": 1,
    "low_energy": 2,
    "low_risk": 3,
}

BATCH_IMPACT_CANDIDATE_FEATURE_SCHEMA: tuple[str, ...] = (
    *BASE_CANDIDATE_FEATURE_SCHEMA,
    "sequence_length",
    "sortie_count",
    "order_observed",
    "best_position",
    "trace_trip_count",
    "trace_arc_option_count",
    "trace_unique_arc_option_count",
    "trace_low_time_arc_count",
    "trace_low_energy_arc_count",
    "trace_low_risk_arc_count",
    "trace_journey_start_time",
    "trace_journey_end_time",
    "trace_journey_duration",
    "trace_total_distance",
    "trace_total_energy",
    "trace_total_risk",
    "trace_total_travel_time",
    "trace_total_recharge_time",
    "trace_max_load",
    "trace_min_survival_energy",
    "trace_service_start_min",
    "trace_service_start_max",
    "trace_service_start_span",
    "trace_inter_sortie_gap_sum",
    "trace_inter_sortie_gap_max",
    "trace_idle_time_proxy",
    "trace_occupancy_bucket_count",
    "slack_min_late_time",
    "slack_mean_late_time",
    "slack_min_early_time",
    "active_basis_exact_task_set_count_before",
    "active_basis_task_overlap_count_before",
    "active_basis_task_overlap_fraction_max_before",
    "active_basis_task_jaccard_max_before",
    "active_basis_lambda_overlap_sum_before",
    "active_basis_lambda_exact_task_set_sum_before",
    "active_basis_signature_duplicate_count_before",
    "pool_task_overlap_count_before",
    "pool_task_jaccard_max_before",
    "forbidden_signature_duplicate_count_before",
    "forbidden_task_overlap_count_before",
    "branch_constraint_touch_count",
    "branch_constraint_violation_count",
    "branch_same_vehicle_pair_partial_count",
    "branch_separate_vehicle_pair_violation_count",
    "candidate_cut_coeff_l1_sum",
    "candidate_cut_subset_row_coeff_sum",
    "candidate_cut_fleet_coeff_count",
    "candidate_cut_dual_abs_weighted_coeff_sum",
)

BATCH_IMPACT_CONTEXT_FEATURE_SCHEMA: tuple[str, ...] = (
    *BASE_CONTEXT_FEATURE_SCHEMA,
    "node_id",
    "depth",
    "fleet_dual",
    "cut_dual_l1_norm",
    "branch_constraint_count",
    "certificate_flat_rounds",
    "certificate_no_column_rounds",
    "final_judge_retry_count",
    "hidden_negative_count",
)

BATCH_IMPACT_BATCH_FEATURE_SCHEMA: tuple[str, ...] = (
    "returned_journey_count",
    "added_journeys",
    "new_journeys",
    "replacement_journeys",
    "new_task_set_count",
    "replacement_task_set_count",
    "active_changed_task_set_count",
    "negative_candidate_count",
    "nonnegative_candidate_count",
    "best_true_reduced_cost",
    "mean_true_reduced_cost",
    "replacement_ratio",
    "support_changing_ratio",
    "batch_type_best_rc",
    "batch_type_replacement_heavy",
    "batch_type_new_task_set",
    "batch_type_active_support_overlap",
    "batch_type_random_or_unknown",
)

LABEL_SCHEMA: tuple[str, ...] = (
    "y_candidate_high_priority",
    "y_candidate_delay_risk",
    "y_candidate_true_rc_negative",
    "y_batch_roi_positive",
    "y_objective_progress",
    "y_tail_improved",
    "y_bad_mode_switch",
    "y_support_changed_good",
    "y_delta_v",
    "y_barrier_slack",
    "y_accepted_batch_roi",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-jsonl",
        type=Path,
        action="append",
        default=None,
        help="May be repeated. Defaults to the same-run batch-impact rows.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--max-candidates-per-row", type=int, default=0)
    parser.add_argument("--true-rc-negative-eps", type=float, default=1.0e-9)
    parser.add_argument("--min-samples-for-training", type=int, default=50)
    parser.add_argument("--min-positive-batches-for-training", type=int, default=10)
    parser.add_argument("--min-delay-candidates-for-training", type=int, default=10)
    parser.add_argument("--min-same-context-pairs-for-ranking", type=int, default=1)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_dataset(
        input_jsonl=args.input_jsonl or DEFAULT_INPUT,
        output_dir=args.output_dir,
        report=args.report,
        max_rows=max(0, int(args.max_rows)),
        max_candidates_per_row=max(0, int(args.max_candidates_per_row)),
        true_rc_negative_eps=float(args.true_rc_negative_eps),
        min_samples_for_training=max(1, int(args.min_samples_for_training)),
        min_positive_batches_for_training=max(0, int(args.min_positive_batches_for_training)),
        min_delay_candidates_for_training=max(0, int(args.min_delay_candidates_for_training)),
        min_same_context_pairs_for_ranking=max(0, int(args.min_same_context_pairs_for_ranking)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def build_dataset(
    *,
    input_jsonl: Path | Iterable[Path] = DEFAULT_INPUT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    max_rows: int = 0,
    max_candidates_per_row: int = 0,
    true_rc_negative_eps: float = 1.0e-9,
    min_samples_for_training: int = 50,
    min_positive_batches_for_training: int = 10,
    min_delay_candidates_for_training: int = 10,
    min_same_context_pairs_for_ranking: int = 1,
) -> dict[str, Any]:
    input_jsonl_paths = _input_jsonl_paths(input_jsonl)
    rows: list[dict[str, Any]] = []
    for path in input_jsonl_paths:
        rows.extend(_read_jsonl(path))
    output_dir = Path(output_dir)
    sample_dir = output_dir / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    for stale in sample_dir.glob("sample_*.pt"):
        stale.unlink()

    builder = FutureGraphBuilder()
    graph_cache: dict[str, Any] = {}
    capture_cache: dict[str, dict[tuple[str, int, str, int, int], dict[str, Any]]] = {}

    samples: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    batch_label_counts: Counter[str] = Counter()
    candidate_label_counts: Counter[str] = Counter()
    instance_counts: Counter[str] = Counter()
    region_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    task_count_counts: Counter[str] = Counter()
    batch_type_counts: Counter[str] = Counter()
    candidate_count_total = 0
    candidate_signature_source_present_total = 0
    matched_context_rows = 0
    (
        explicit_long_horizon_candidate_keys,
        conflicting_explicit_long_horizon_candidate_keys,
    ) = _explicit_long_horizon_candidate_key_sets(rows)

    for row_index, row in enumerate(rows):
        if max_rows and len(samples) >= int(max_rows):
            break
        if row.get("schema_version") != "gat_same_run_batch_impact_row_v1":
            skipped["unsupported_row_schema"] += 1
            continue
        if not row.get("diagnostic_only") or row.get("official_bound_effect") or row.get("certificate_effect"):
            skipped["non_diagnostic_or_official_effect"] += 1
            continue
        same_run_intervention = bool(row.get("same_run_intervention_observed"))
        target_intervention = bool(
            row.get("same_context_target_intervention_observed")
            and row.get("worker_target_causal_match")
        )
        if not (same_run_intervention or target_intervention) or not row.get("training_label_allowed"):
            skipped["missing_same_run_intervention_evidence"] += 1
            continue
        source_file = Path(str(row.get("source_file") or ""))
        if not source_file.exists():
            skipped["missing_source_file"] += 1
            continue
        events = capture_cache.get(str(source_file))
        if events is None:
            events = _load_capture_events(source_file)
            capture_cache[str(source_file)] = events
        key = (
            str(row.get("context_hash") or ""),
            int(row.get("cg_iter") or -1),
            str(row.get("pricing_kind") or ""),
            int(row.get("node_id") or 0),
            int(row.get("depth") or 0),
        )
        event = events.get(key)
        if event is None:
            skipped["missing_matching_capture_event"] += 1
            continue
        matched_context_rows += 1

        returned = list(event.get("returned_journeys") or [])
        target_signature_samples = _row_target_signature_samples(row)
        target_trace_key = _row_target_trace_key(row)
        if target_signature_samples:
            returned = [
                journey
                for journey in returned
                if _journey_signature_sample_text(journey.get("signature"))
                in target_signature_samples
            ]
        elif target_trace_key:
            returned = [
                journey
                for journey in returned
                if _journey_trace_key(journey) == target_trace_key
            ]
        if max_candidates_per_row:
            returned = returned[: int(max_candidates_per_row)]
        if not returned:
            skipped[
                "target_candidate_not_found_in_capture"
                if target_trace_key or target_signature_samples
                else "empty_returned_batch"
            ] += 1
            continue
        candidate_keys = [
            _long_horizon_candidate_key(row, journey)
            for journey in returned
            if isinstance(journey, dict)
        ]
        if candidate_keys and any(
            key in conflicting_explicit_long_horizon_candidate_keys for key in candidate_keys
        ):
            skipped["conflicting_explicit_long_horizon_label"] += 1
            continue
        if not _has_explicit_long_horizon_label(row):
            if candidate_keys and all(
                key in explicit_long_horizon_candidate_keys for key in candidate_keys
            ):
                skipped["shadowed_by_explicit_long_horizon_label"] += 1
                continue

        graph_path = Path(str(row.get("instance_path") or event.get("instance_path") or ""))
        if not graph_path.exists():
            skipped["missing_logical_graph"] += 1
            continue
        graph = graph_cache.get(str(graph_path))
        if graph is None:
            try:
                graph = builder.build_from_json(graph_path)
            except Exception:
                skipped["invalid_logical_graph"] += 1
                continue
            graph_cache[str(graph_path)] = graph
        task_time_windows = _graph_task_time_windows(graph)

        task_ids = [int(value) for value in graph.task_ids.tolist()]
        candidate_membership: list[list[float]] = []
        candidate_positions: list[list[float]] = []
        candidate_features: list[list[float]] = []
        candidate_path_token_ids: list[list[int]] = []
        candidate_path_pair_ids: list[list[int]] = []
        candidate_path_type_ids: list[list[int]] = []
        candidate_high_priority: list[float] = []
        candidate_delay_risk: list[float] = []
        candidate_true_rc_negative: list[float] = []
        kept_journeys: list[dict[str, Any]] = []

        objective_improvement = _finite_float(row.get("objective_improvement"))
        immediate_objective_improved = bool(int(row.get("label_objective_improved") or 0))
        accepted_batch_roi = _first_finite(
            row,
            (
                "accepted_batch_roi_label",
                "accepted_batch_roi",
                "trajectory_accepted_batch_roi",
            ),
            default=objective_improvement / max(1.0, _finite_float(row.get("added_journeys"), 1.0)),
        )
        tail_retry_delta = _first_finite(
            row,
            (
                "final_judge_retry_delta",
                "pricing_tail_retry_delta",
                "hidden_negative_delta",
            ),
            default=0.0,
        )
        bad_mode_switch_default = bool(
            (not immediate_objective_improved)
            and (
                _finite_float(row.get("replacement_journeys")) > 0.0
                or _finite_float(row.get("active_changed_task_set_count")) > 0.0
            )
        )
        bad_mode_switch = _row_bool_label(
            row,
            "label_bad_mode_switch",
            default=bad_mode_switch_default,
        )
        batch_roi_positive = _row_bool_label(
            row,
            "label_batch_roi_positive",
            default=immediate_objective_improved,
        )
        support_changed_good = _row_bool_label(
            row,
            "label_support_changed_good",
            default=bool(
                batch_roi_positive
                and not bad_mode_switch
                and _finite_float(row.get("active_changed_task_set_count")) > 0.0
            ),
        )
        tail_improved = _row_bool_label(
            row,
            "label_tail_improved",
            default=bool(tail_retry_delta < 0.0),
        )
        delta_v_label = _first_finite(
            row,
            ("delta_v_label", "trajectory_delta_v_label", "y_delta_v"),
            default=-objective_improvement,
        )
        barrier_slack_label = _first_finite(
            row,
            ("barrier_slack_label", "trajectory_barrier_slack_label", "y_barrier_slack"),
            default=objective_improvement - max(0.0, tail_retry_delta),
        )
        for journey in returned:
            if not isinstance(journey, dict):
                continue
            task_set = _task_set(journey.get("task_set"))
            sequence = _journey_sequence(journey)
            if not sequence and task_set:
                sequence = sorted(task_set)
            if not task_set and sequence:
                task_set = set(sequence)
            if not task_set:
                continue
            membership = [1.0 if task_id in task_set else 0.0 for task_id in task_ids]
            if sum(membership) <= 0:
                continue
            positions = _sequence_positions(sequence, task_ids)
            if sum(positions) <= 0.0:
                continue
            true_rc = _true_reduced_cost(journey)
            is_negative = true_rc < -abs(float(true_rc_negative_eps))
            candidate_membership.append(membership)
            candidate_positions.append(positions)
            candidate_features.append(
                [
                    _candidate_feature(
                        event,
                        journey,
                        field,
                        sequence=sequence,
                        task_ids=task_ids,
                        task_time_windows=task_time_windows,
                    )
                    for field in BATCH_IMPACT_CANDIDATE_FEATURE_SCHEMA
                ]
            )
            token_ids, pair_ids, type_ids = _candidate_path_token_rows(journey)
            candidate_path_token_ids.append(token_ids)
            candidate_path_pair_ids.append(pair_ids)
            candidate_path_type_ids.append(type_ids)
            candidate_true_rc_negative.append(1.0 if is_negative else 0.0)
            high_priority = bool(is_negative and batch_roi_positive and not bad_mode_switch)
            candidate_high_priority.append(1.0 if high_priority else 0.0)
            candidate_delay_risk.append(1.0 if is_negative and not high_priority else 0.0)
            kept_journeys.append(journey)
            if high_priority:
                candidate_label_counts["high_priority"] += 1
            elif is_negative:
                candidate_label_counts["delay_queue"] += 1
            else:
                candidate_label_counts["nonnegative_reject_only"] += 1
        if not candidate_membership:
            skipped["no_candidate_tasks_in_graph"] += 1
            continue

        batch_features = _batch_features(row, kept_journeys)
        batch_type = _batch_type_name(batch_features)
        batch_type_counts[batch_type] += 1

        sample = graph.clone()
        sample.candidate_task_membership = torch.tensor(candidate_membership, dtype=torch.float32)
        sample.candidate_sequence_positions = torch.tensor(candidate_positions, dtype=torch.float32)
        sample.candidate_features = torch.tensor(candidate_features, dtype=torch.float32)
        sample.candidate_path_token_ids = _padded_long_tensor(candidate_path_token_ids)
        sample.candidate_path_pair_ids = _padded_long_tensor(candidate_path_pair_ids)
        sample.candidate_path_type_ids = _padded_long_tensor(candidate_path_type_ids)
        sample.candidate_path_token_mask = _padded_bool_mask(candidate_path_token_ids)
        sample.context_features = torch.tensor(
            [_context_feature(event, row, field) for field in BATCH_IMPACT_CONTEXT_FEATURE_SCHEMA],
            dtype=torch.float32,
        )
        sample.batch_features = torch.tensor(batch_features, dtype=torch.float32)
        sample.y_candidate_high_priority = torch.tensor(candidate_high_priority, dtype=torch.float32)
        sample.y_candidate_delay_risk = torch.tensor(candidate_delay_risk, dtype=torch.float32)
        sample.y_candidate_true_rc_negative = torch.tensor(candidate_true_rc_negative, dtype=torch.float32)
        sample.y_batch_roi_positive = torch.tensor([1.0 if batch_roi_positive else 0.0], dtype=torch.float32)
        sample.y_objective_progress = torch.tensor([1.0 if objective_improvement > 1.0e-9 else 0.0], dtype=torch.float32)
        sample.y_tail_improved = torch.tensor([1.0 if tail_improved else 0.0], dtype=torch.float32)
        sample.y_bad_mode_switch = torch.tensor([1.0 if bad_mode_switch else 0.0], dtype=torch.float32)
        sample.y_support_changed_good = torch.tensor([1.0 if support_changed_good else 0.0], dtype=torch.float32)
        sample.y_delta_v = torch.tensor([delta_v_label], dtype=torch.float32)
        sample.y_barrier_slack = torch.tensor([barrier_slack_label], dtype=torch.float32)
        sample.y_accepted_batch_roi = torch.tensor([accepted_batch_roi], dtype=torch.float32)
        sample.batch_impact_instance = str(row.get("instance") or event.get("instance") or "")
        sample.batch_impact_instance_path = str(graph_path)
        sample.batch_impact_instance_region = str(row.get("instance_region") or "")
        sample.batch_impact_instance_family = _instance_family(graph_path, row=row, event=event)
        sample.batch_impact_task_count = _task_count_from_path(graph_path)
        sample.batch_impact_context_hash = str(row.get("context_hash") or "")
        sample.batch_impact_source_jsonl = str(source_file)
        sample.batch_impact_source_row_index = int(row_index)
        sample.batch_impact_candidate_ids = [
            str(journey.get("id", idx)) for idx, journey in enumerate(kept_journeys)
        ]
        candidate_signature_ids = [
            journey_gat_candidate_id_from_signature(journey.get("signature"))
            for journey in kept_journeys
        ]
        candidate_signature_source_present = [
            bool(journey.get("signature")) for journey in kept_journeys
        ]
        sample.batch_impact_candidate_signature_ids = candidate_signature_ids
        sample.batch_impact_candidate_signature_source_present = candidate_signature_source_present

        sample_name = f"sample_{len(samples):06d}.pt"
        torch.save(sample, sample_dir / sample_name)
        samples.append(
            {
                "path": f"samples/{sample_name}",
                "instance": sample.batch_impact_instance,
                "instance_region": sample.batch_impact_instance_region,
                "instance_family": sample.batch_impact_instance_family,
                "task_count": int(sample.batch_impact_task_count),
                "context_hash": sample.batch_impact_context_hash,
                "source_file": str(source_file),
                "row_index": int(row_index),
                "candidate_count": len(candidate_membership),
                "candidate_ids": list(sample.batch_impact_candidate_ids),
                "candidate_signature_ids": list(candidate_signature_ids),
                "candidate_signature_source_present_count": int(sum(candidate_signature_source_present)),
                "negative_candidate_count": int(sum(candidate_true_rc_negative)),
                "high_priority_candidate_count": int(sum(candidate_high_priority)),
                "delay_candidate_count": int(sum(candidate_delay_risk)),
                "batch_type": batch_type,
                "label_batch_roi_positive": int(batch_roi_positive),
                "objective_improvement": float(objective_improvement),
                "accepted_batch_roi": float(accepted_batch_roi),
            }
        )
        candidate_count_total += len(candidate_membership)
        candidate_signature_source_present_total += int(sum(candidate_signature_source_present))
        batch_label_counts["roi_positive" if batch_roi_positive else "non_improving"] += 1
        instance_counts[sample.batch_impact_instance] += 1
        region_counts[sample.batch_impact_instance_region] += 1
        family_counts[sample.batch_impact_instance_family] += 1
        task_count_counts[str(int(sample.batch_impact_task_count))] += 1

    candidate_feature_mean, candidate_feature_std = _feature_stats(sample_dir, "candidate_features")
    context_feature_mean, context_feature_std = _feature_stats(sample_dir, "context_features")
    batch_feature_mean, batch_feature_std = _feature_stats(sample_dir, "batch_features")

    training_blockers: list[str] = []
    if len(samples) < int(min_samples_for_training):
        training_blockers.append("need_more_batch_impact_samples")
    if batch_label_counts.get("roi_positive", 0) < int(min_positive_batches_for_training):
        training_blockers.append("need_more_roi_positive_batches")
    if candidate_label_counts.get("delay_queue", 0) < int(min_delay_candidates_for_training):
        training_blockers.append("need_more_delay_queue_negative_candidates")
    if len(instance_counts) < 2:
        training_blockers.append("need_more_instances_for_holdout")
    if len(region_counts) < 2:
        training_blockers.append("need_more_regions_for_holdout")
    pairwise_context_stats = _pairwise_context_stats(samples)
    ranking_blockers: list[str] = []
    if pairwise_context_stats["same_context_pair_count"] <= 0:
        ranking_blockers.append("need_same_context_batch_pairs_for_pairwise_ranking")
    elif pairwise_context_stats["same_context_comparable_pair_count"] < int(min_same_context_pairs_for_ranking):
        ranking_blockers.append("need_same_context_roi_diverse_pairs_for_pairwise_ranking")

    context_match_rate = (
        round(float(matched_context_rows) / float(len(rows)), 6) if rows else 0.0
    )
    candidate_signature_source_coverage = (
        round(float(candidate_signature_source_present_total) / float(candidate_count_total), 6)
        if candidate_count_total
        else 0.0
    )
    exactness_contract = batch_impact_exactness_contract()
    manifest = {
        "schema_version": "gat_batch_impact_dataset_manifest_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "source_jsonl": str(input_jsonl_paths[0]) if len(input_jsonl_paths) == 1 else "",
        "source_jsonl_paths": [str(path) for path in input_jsonl_paths],
        "sample_count": len(samples),
        "candidate_count": int(candidate_count_total),
        "candidate_signature_source_present_count": int(candidate_signature_source_present_total),
        "candidate_signature_source_coverage": candidate_signature_source_coverage,
        "explicit_long_horizon_candidate_key_count": len(explicit_long_horizon_candidate_keys),
        "conflicting_explicit_long_horizon_candidate_key_count": len(
            conflicting_explicit_long_horizon_candidate_keys
        ),
        "context_match_rate": context_match_rate,
        "skipped_counts": dict(sorted(skipped.items())),
        "batch_label_counts": dict(sorted(batch_label_counts.items())),
        "candidate_label_counts": dict(sorted(candidate_label_counts.items())),
        "batch_type_counts": dict(sorted(batch_type_counts.items())),
        "pairwise_context_stats": pairwise_context_stats,
        "ranking_blockers": ranking_blockers,
        "ranking_ready": not ranking_blockers,
        "instance_counts": dict(sorted(instance_counts.items())),
        "region_counts": dict(sorted(region_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "task_count_counts": dict(sorted(task_count_counts.items())),
        "candidate_feature_schema": list(BATCH_IMPACT_CANDIDATE_FEATURE_SCHEMA),
        "context_feature_schema": list(BATCH_IMPACT_CONTEXT_FEATURE_SCHEMA),
        "batch_feature_schema": list(BATCH_IMPACT_BATCH_FEATURE_SCHEMA),
        "candidate_path_token_schema": {
            "token_ids": "stable_sha1_hash_bucket_of_full_arc_option_id",
            "pair_ids": "stable_sha1_hash_bucket_of_directed_arc_pair",
            "type_ids": dict(PATH_TYPE_TO_ID),
            "padding_id": 0,
            "token_hash_bucket_count": int(PATH_TOKEN_HASH_BUCKET_COUNT),
            "pair_hash_bucket_count": int(PATH_PAIR_HASH_BUCKET_COUNT),
        },
        "label_schema": list(LABEL_SCHEMA),
        "candidate_feature_mean": candidate_feature_mean,
        "candidate_feature_std": candidate_feature_std,
        "context_feature_mean": context_feature_mean,
        "context_feature_std": context_feature_std,
        "batch_feature_mean": batch_feature_mean,
        "batch_feature_std": batch_feature_std,
        "exactness_contract": exactness_contract,
        "training_blockers": training_blockers,
        "training_ready": not training_blockers,
        "samples": samples,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    checks = {
        "has_samples": bool(samples),
        "has_candidates": candidate_count_total > 0,
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "production_ready_false": not manifest["production_ready"],
        "no_pricing_oracle": not exactness_contract["pricing_oracle"],
        "no_certificate_source": not exactness_contract["certificate_source"],
        "no_official_bound_effect": not exactness_contract["official_bound_effect"],
        "negative_delay_not_reject_contract": not exactness_contract["can_permanently_discard_true_rc_negative"],
    }
    summary = {
        "schema_version": "gat_batch_impact_dataset_summary_v1",
        "status": "gat_batch_impact_dataset_built" if samples else "no_samples",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "source_jsonl": str(input_jsonl_paths[0]) if len(input_jsonl_paths) == 1 else "",
        "source_jsonl_paths": [str(path) for path in input_jsonl_paths],
        "output_dir": str(output_dir),
        "sample_count": len(samples),
        "candidate_count": int(candidate_count_total),
        "candidate_signature_source_present_count": int(candidate_signature_source_present_total),
        "candidate_signature_source_coverage": candidate_signature_source_coverage,
        "explicit_long_horizon_candidate_key_count": len(explicit_long_horizon_candidate_keys),
        "conflicting_explicit_long_horizon_candidate_key_count": len(
            conflicting_explicit_long_horizon_candidate_keys
        ),
        "context_match_rate": context_match_rate,
        "batch_label_counts": dict(sorted(batch_label_counts.items())),
        "candidate_label_counts": dict(sorted(candidate_label_counts.items())),
        "batch_type_counts": dict(sorted(batch_type_counts.items())),
        "candidate_path_token_schema": {
            "token_hash_bucket_count": int(PATH_TOKEN_HASH_BUCKET_COUNT),
            "pair_hash_bucket_count": int(PATH_PAIR_HASH_BUCKET_COUNT),
            "type_ids": dict(PATH_TYPE_TO_ID),
            "padding_id": 0,
        },
        "pairwise_context_stats": pairwise_context_stats,
        "ranking_blockers": ranking_blockers,
        "ranking_ready": not ranking_blockers,
        "instance_count": len(instance_counts),
        "region_count": len(region_counts),
        "family_counts": dict(sorted(family_counts.items())),
        "task_count_counts": dict(sorted(task_count_counts.items())),
        "skipped_counts": dict(sorted(skipped.items())),
        "training_blockers": training_blockers,
        "training_ready": not training_blockers,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "checks": checks,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _pairwise_context_stats(samples: list[dict[str, Any]]) -> dict[str, Any]:
    context_counts: Counter[str] = Counter()
    samples_by_context: dict[str, list[dict[str, Any]]] = {}
    family_context_counts: dict[str, Counter[str]] = {}
    task_context_counts: dict[str, Counter[str]] = {}
    for sample in samples:
        context_hash = str(sample.get("context_hash") or "unknown")
        family = str(sample.get("instance_family") or "unknown")
        task_count = str(int(sample.get("task_count") or 0))
        context_counts[context_hash] += 1
        samples_by_context.setdefault(context_hash, []).append(sample)
        family_context_counts.setdefault(family, Counter())[context_hash] += 1
        task_context_counts.setdefault(task_count, Counter())[context_hash] += 1

    def summarize(counts: Counter[str]) -> dict[str, int]:
        same_context_pair_count = 0
        multi_context_count = 0
        largest_context_size = 0
        for count in counts.values():
            largest_context_size = max(largest_context_size, int(count))
            if count >= 2:
                multi_context_count += 1
                same_context_pair_count += int(count) * (int(count) - 1) // 2
        return {
            "context_count": len(counts),
            "multi_context_count": multi_context_count,
            "same_context_pair_count": same_context_pair_count,
            "largest_context_size": largest_context_size,
        }

    summary = summarize(context_counts)
    summary["sample_count"] = len(samples)
    comparable_pair_count = 0
    roi_diverse_context_count = 0
    positive_negative_label_pair_count = 0
    for context_samples in samples_by_context.values():
        if len(context_samples) < 2:
            continue
        context_comparable_pairs = 0
        for left_index, left in enumerate(context_samples):
            left_roi = _finite_float(left.get("accepted_batch_roi"))
            left_label = int(left.get("label_batch_roi_positive") or 0)
            for right in context_samples[left_index + 1 :]:
                right_roi = _finite_float(right.get("accepted_batch_roi"))
                right_label = int(right.get("label_batch_roi_positive") or 0)
                if abs(left_roi - right_roi) > 1.0e-9:
                    comparable_pair_count += 1
                    context_comparable_pairs += 1
                if left_label != right_label:
                    positive_negative_label_pair_count += 1
        if context_comparable_pairs > 0:
            roi_diverse_context_count += 1
    return {
        **summary,
        "same_context_comparable_pair_count": comparable_pair_count,
        "roi_diverse_context_count": roi_diverse_context_count,
        "positive_negative_label_pair_count": positive_negative_label_pair_count,
        "by_family": {
            family: {"sample_count": sum(counts.values()), **summarize(counts)}
            for family, counts in sorted(family_context_counts.items())
        },
        "by_task_count": {
            task_count: {"sample_count": sum(counts.values()), **summarize(counts)}
            for task_count, counts in sorted(task_context_counts.items(), key=lambda item: int(item[0]))
        },
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                rows.append(event)
    return rows


def _input_jsonl_paths(value: Path | Iterable[Path]) -> tuple[Path, ...]:
    if isinstance(value, (str, Path)):
        paths = (Path(value),)
    else:
        paths = tuple(Path(path) for path in value)
    if not paths:
        raise ValueError("at least one input JSONL is required")
    return paths


def _load_capture_events(path: Path) -> dict[tuple[str, int, str, int, int], dict[str, Any]]:
    events: dict[tuple[str, int, str, int, int], dict[str, Any]] = {}
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("event") != "journey_counterfactual_replay_capture":
                continue
            key = (
                str(event.get("context_hash") or ""),
                int(event.get("cg_iter") or -1),
                str(event.get("pricing_kind") or ""),
                int(event.get("node_id") or 0),
                int(event.get("depth") or 0),
            )
            events[key] = event
    return events


def _explicit_long_horizon_candidate_key_sets(
    rows: list[dict[str, Any]],
) -> tuple[set[tuple[Any, ...]], set[tuple[Any, ...]]]:
    keys: set[tuple[Any, ...]] = set()
    label_signatures_by_key: dict[tuple[Any, ...], set[str]] = {}
    capture_cache: dict[str, dict[tuple[str, int, str, int, int], dict[str, Any]]] = {}
    for row in rows:
        if not _has_explicit_long_horizon_label(row):
            continue
        label_signature = _explicit_long_horizon_label_signature(row)
        source_file = Path(str(row.get("source_file") or ""))
        if not source_file.exists():
            continue
        events = capture_cache.get(str(source_file))
        if events is None:
            events = _load_capture_events(source_file)
            capture_cache[str(source_file)] = events
        event = events.get(_capture_key(row))
        if event is None:
            continue
        for journey in _matched_returned_journeys(row, event):
            if isinstance(journey, dict):
                key = _long_horizon_candidate_key(row, journey)
                keys.add(key)
                label_signatures_by_key.setdefault(key, set()).add(label_signature)
    conflicting_keys = {
        key
        for key, signatures in label_signatures_by_key.items()
        if len(signatures) > 1
    }
    return keys, conflicting_keys


def _explicit_long_horizon_candidate_keys(rows: list[dict[str, Any]]) -> set[tuple[Any, ...]]:
    keys, _conflicting_keys = _explicit_long_horizon_candidate_key_sets(rows)
    return keys


def _has_explicit_long_horizon_label(row: dict[str, Any]) -> bool:
    for key in (
        "accepted_batch_roi_label",
        "trajectory_accepted_batch_roi",
        "label_batch_roi_positive",
        "label_bad_mode_switch",
        "label_support_changed_good",
        "delta_v_label",
        "trajectory_delta_v_label",
        "barrier_slack_label",
        "trajectory_barrier_slack_label",
    ):
        if key in row and row.get(key) not in (None, ""):
            return True
    return False


def _explicit_long_horizon_label_signature(row: dict[str, Any]) -> str:
    values: dict[str, Any] = {}
    for key in (
        "accepted_batch_roi_label",
        "trajectory_accepted_batch_roi",
        "label_batch_roi_positive",
        "label_bad_mode_switch",
        "label_tail_improved",
        "label_support_changed_good",
        "delta_v_label",
        "trajectory_delta_v_label",
        "barrier_slack_label",
        "trajectory_barrier_slack_label",
    ):
        if key not in row or row.get(key) in (None, ""):
            continue
        if key.startswith("label_"):
            values[key] = int(_row_bool_label(row, key, default=False))
        else:
            values[key] = round(_finite_float(row.get(key)), 9)
    return json.dumps(values, sort_keys=True)


def _capture_key(row: dict[str, Any]) -> tuple[str, int, str, int, int]:
    return (
        str(row.get("context_hash") or ""),
        int(row.get("cg_iter") or -1),
        str(row.get("pricing_kind") or ""),
        int(row.get("node_id") or 0),
        int(row.get("depth") or 0),
    )


def _matched_returned_journeys(row: dict[str, Any], event: dict[str, Any]) -> list[dict[str, Any]]:
    returned = [journey for journey in (event.get("returned_journeys") or []) if isinstance(journey, dict)]
    target_signature_samples = _row_target_signature_samples(row)
    target_trace_key = _row_target_trace_key(row)
    if target_signature_samples:
        return [
            journey
            for journey in returned
            if _journey_signature_sample_text(journey.get("signature")) in target_signature_samples
        ]
    if target_trace_key:
        return [
            journey
            for journey in returned
            if _journey_trace_key(journey) == target_trace_key
        ]
    return returned


def _long_horizon_candidate_key(row: dict[str, Any], journey: dict[str, Any]) -> tuple[Any, ...]:
    signature = journey.get("signature")
    signature_id = journey_gat_candidate_id_from_signature(signature)
    if not signature:
        signature_id = json.dumps(_journey_trace_key(journey), sort_keys=True)
    return (
        str(row.get("context_hash") or ""),
        int(row.get("cg_iter") or -1),
        str(row.get("pricing_kind") or ""),
        int(row.get("node_id") or 0),
        int(row.get("depth") or 0),
        str(signature_id),
    )


def _row_target_trace_key(row: dict[str, Any]) -> tuple[tuple[tuple[int, ...], tuple[str, ...], float], ...]:
    traces = row.get("target_sortie_traces") or row.get("target_materialized_sortie_traces")
    if not isinstance(traces, list) or not traces:
        return tuple()
    return _trace_payload_key(traces)


def _row_target_signature_samples(row: dict[str, Any]) -> set[str]:
    samples = (
        row.get("target_signature_samples")
        or row.get("target_materialized_signature_samples")
        or row.get("worker_returned_candidate_signature_samples")
    )
    if not isinstance(samples, list):
        return set()
    return {str(sample) for sample in samples if str(sample)}


def _journey_signature_sample_text(signature: Any) -> str:
    if not isinstance(signature, list) or not signature:
        return ""
    parts: list[str] = []
    for item in signature:
        if not isinstance(item, (list, tuple)) or len(item) < 3:
            return ""
        sequence = _flatten_task_sequence(item[0])
        arcs = tuple(str(arc) for arc in (item[1] or []))
        if not sequence or len(arcs) != len(sequence) + 1:
            return ""
        start_time = str(round(_finite_float(item[2]), 9))
        parts.append(
            f"{','.join(str(task) for task in sequence)}@{start_time}:"
            f"{','.join(arcs)}"
        )
    return "|".join(parts)


def _journey_trace_key(journey: dict[str, Any]) -> tuple[tuple[tuple[int, ...], tuple[str, ...], float], ...]:
    trips = journey.get("trips")
    if isinstance(trips, list) and trips:
        traces: list[dict[str, Any]] = []
        for trip in trips:
            if not isinstance(trip, dict):
                return tuple()
            sequence = _flatten_task_sequence(
                trip.get("tasks")
                or trip.get("task_sequence")
                or trip.get("task_ids")
                or trip.get("sequence")
            )
            arcs = tuple(str(arc) for arc in (trip.get("arc_option_ids") or []))
            if not sequence or len(arcs) != len(sequence) + 1:
                return tuple()
            traces.append(
                {
                    "sequence": sequence,
                    "arc_option_sequence": list(arcs),
                    "start_time": _finite_float(trip.get("start_time")),
                }
            )
        return _trace_payload_key(traces)
    signature = journey.get("signature")
    if isinstance(signature, list) and signature and all(isinstance(item, (list, tuple)) for item in signature):
        traces = []
        for item in signature:
            if len(item) < 3:
                return tuple()
            sequence = _flatten_task_sequence(item[0])
            arcs = tuple(str(arc) for arc in (item[1] or []))
            if not sequence or len(arcs) != len(sequence) + 1:
                return tuple()
            traces.append(
                {
                    "sequence": sequence,
                    "arc_option_sequence": list(arcs),
                    "start_time": _finite_float(item[2]),
                }
            )
        return _trace_payload_key(traces)
    return tuple()


def _trace_payload_key(value: list[Any]) -> tuple[tuple[tuple[int, ...], tuple[str, ...], float], ...]:
    key: list[tuple[tuple[int, ...], tuple[str, ...], float]] = []
    for trace in value:
        if not isinstance(trace, dict):
            return tuple()
        sequence = _flatten_task_sequence(trace.get("sequence"))
        arcs = tuple(str(arc) for arc in (trace.get("arc_option_sequence") or []))
        if not sequence or len(arcs) != len(sequence) + 1:
            return tuple()
        key.append((tuple(sequence), arcs, round(_finite_float(trace.get("start_time")), 9)))
    return tuple(key)


def _journey_sequence(journey: dict[str, Any]) -> list[int]:
    for key in ("sequence", "task_sequence", "tasks"):
        sequence = _flatten_task_sequence(journey.get(key))
        if sequence:
            return sequence
    trips = journey.get("trips")
    if isinstance(trips, list):
        result: list[int] = []
        for trip in trips:
            if not isinstance(trip, dict):
                continue
            for key in ("task_sequence", "tasks", "task_ids", "sequence"):
                sequence = _flatten_task_sequence(trip.get(key))
                if sequence:
                    result.extend(sequence)
                    break
        return _dedupe_preserve_order(result)
    return []


def _flatten_task_sequence(value: Any) -> list[int]:
    result: list[int] = []
    if not isinstance(value, list):
        return result
    for item in value:
        if isinstance(item, list):
            result.extend(_flatten_task_sequence(item))
            continue
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            return []
    return _dedupe_preserve_order(result)


def _dedupe_preserve_order(values: Iterable[int]) -> list[int]:
    result: list[int] = []
    seen: set[int] = set()
    for value in values:
        item = int(value)
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _sequence_positions(sequence: list[int], task_ids: list[int]) -> list[float]:
    position_by_task = {int(task): float(index + 1) for index, task in enumerate(sequence)}
    return [position_by_task.get(int(task_id), 0.0) for task_id in task_ids]


def _task_set(value: Any) -> set[int]:
    result: set[int] = set()
    if isinstance(value, list):
        for item in value:
            try:
                result.add(int(item))
            except (TypeError, ValueError):
                return set()
    return result


def _instance_family(graph_path: Path, *, row: dict[str, Any], event: dict[str, Any]) -> str:
    for key in ("family", "instance_family", "dataset_family"):
        value = row.get(key, event.get(key))
        if value:
            return str(value)
    parts = Path(graph_path).parts
    for candidate in ("sector-wave", "random-wave", "greedy-anchor"):
        if candidate in parts:
            return candidate
    text = str(graph_path)
    for candidate in ("sector-wave", "random-wave", "greedy-anchor"):
        if candidate in text:
            return candidate
    return "unknown"


def _task_count_from_path(graph_path: Path) -> int:
    for part in Path(graph_path).parts:
        if part.startswith("tasks_"):
            digits = "".join(ch for ch in part if ch.isdigit())
            if digits:
                return int(digits)
        if "tasks" in part:
            marker = part.split("tasks", 1)[1]
            digits = ""
            for ch in marker:
                if ch.isdigit():
                    digits += ch
                elif digits:
                    break
            if digits:
                return int(digits)
    return 0


def _candidate_feature(
    event: dict[str, Any],
    journey: dict[str, Any],
    field: str,
    *,
    sequence: list[int],
    task_ids: list[int],
    task_time_windows: dict[int, tuple[float, float]],
) -> float:
    task_set = _task_set(journey.get("task_set")) or set(sequence)
    if field == "true_reduced_cost":
        return _true_reduced_cost(journey)
    if field == "cost":
        return _finite_float(journey.get("cost"))
    if field == "task_count":
        return float(len(task_set))
    if field == "vehicle_count":
        return float(len(journey.get("trips") or []))
    if field == "new_task_set":
        return 0.0 if _task_set_in_payload(task_set, event.get("pool_task_sets")) else 1.0
    if field == "strict_replacement_by_cost":
        return 0.0
    if field == "weak_replacement_or_duplicate":
        return 1.0 if _task_set_in_payload(task_set, event.get("pool_task_sets")) else 0.0
    if field == "duplicate_signature":
        return 1.0 if _signature_in_payload(journey.get("signature"), event.get("pool_signatures")) else 0.0
    if field == "duplicate_signature_pool_count_before":
        return float(_signature_count(journey.get("signature"), event.get("pool_signatures")))
    if field == "task_set_pool_count_before":
        return float(_task_set_count(task_set, event.get("pool_task_sets")))
    if field == "sequence_length":
        return float(len(sequence))
    if field == "sortie_count":
        trips = journey.get("trips")
        if isinstance(trips, list) and trips:
            return float(len(trips))
        outer_sequence = journey.get("sequence")
        if isinstance(outer_sequence, list) and any(isinstance(item, list) for item in outer_sequence):
            return float(len(outer_sequence))
        return 1.0 if sequence else 0.0
    if field == "order_observed":
        return 1.0 if bool(_journey_sequence(journey)) else 0.0
    if field == "best_position":
        positions = _sequence_positions(sequence, task_ids)
        nonzero = [value for value in positions if value > 0.0]
        return min(nonzero) if nonzero else 0.0
    if field.startswith("slack_"):
        return _slack_candidate_feature(journey, field, task_time_windows=task_time_windows)
    if field.startswith("trace_"):
        return _trace_candidate_feature(journey, field)
    if field.startswith("active_basis_"):
        return _active_basis_candidate_feature(event, journey, field, task_set=task_set)
    if field.startswith("pool_"):
        return _pool_candidate_feature(event, field, task_set=task_set)
    if field.startswith("forbidden_"):
        return _forbidden_candidate_feature(event, journey, field, task_set=task_set)
    if field.startswith("branch_"):
        return _branch_candidate_feature(event, field, task_set=task_set)
    if field.startswith("candidate_cut_"):
        return _cut_candidate_feature(event, journey, field, task_set=task_set)
    return 0.0


def _trace_candidate_feature(journey: dict[str, Any], field: str) -> float:
    trips = _journey_trip_dicts(journey)
    arc_ids = _journey_arc_option_ids(journey)
    service_starts = _journey_service_start_times(journey)
    trip_starts = [
        _finite_float(trip.get("start_time"))
        for trip in trips
        if _has_finite_number(trip.get("start_time"))
    ]
    trip_ends = [
        _finite_float(trip.get("end_time"))
        for trip in trips
        if _has_finite_number(trip.get("end_time"))
    ]
    sorted_trip_bounds = sorted(zip(trip_starts, trip_ends))
    gaps = [
        max(0.0, sorted_trip_bounds[idx + 1][0] - sorted_trip_bounds[idx][1])
        for idx in range(len(sorted_trip_bounds) - 1)
    ]
    start_time = _finite_float(journey.get("start_time"))
    end_time = _finite_float(journey.get("end_time"))
    duration = max(0.0, end_time - start_time)
    total_travel_time = _sum_trip_numeric_field(trips, "travel_time")
    if field == "trace_trip_count":
        return float(len(trips))
    if field == "trace_arc_option_count":
        return float(len(arc_ids))
    if field == "trace_unique_arc_option_count":
        return float(len(set(arc_ids)))
    if field == "trace_low_time_arc_count":
        return float(sum(_arc_option_has_type(arc, "low_time") for arc in arc_ids))
    if field == "trace_low_energy_arc_count":
        return float(sum(_arc_option_has_type(arc, "low_energy") for arc in arc_ids))
    if field == "trace_low_risk_arc_count":
        return float(sum(_arc_option_has_type(arc, "low_risk") for arc in arc_ids))
    if field == "trace_journey_start_time":
        return start_time
    if field == "trace_journey_end_time":
        return end_time
    if field == "trace_journey_duration":
        return duration
    if field == "trace_total_distance":
        return _sum_trip_numeric_field(trips, "distance")
    if field == "trace_total_energy":
        return _sum_trip_numeric_field(trips, "energy")
    if field == "trace_total_risk":
        return _sum_trip_numeric_field(trips, "risk")
    if field == "trace_total_travel_time":
        return total_travel_time
    if field == "trace_total_recharge_time":
        return _sum_trip_numeric_field(trips, "recharge_time")
    if field == "trace_max_load":
        return _max_or_zero(_finite_float(trip.get("load")) for trip in trips)
    if field == "trace_min_survival_energy":
        return _min_or_zero(
            _finite_float(trip.get("survival_energy"))
            for trip in trips
            if _has_finite_number(trip.get("survival_energy"))
        )
    if field == "trace_service_start_min":
        return _min_or_zero(service_starts)
    if field == "trace_service_start_max":
        return _max_or_zero(service_starts)
    if field == "trace_service_start_span":
        return _max_or_zero(service_starts) - _min_or_zero(service_starts) if service_starts else 0.0
    if field == "trace_inter_sortie_gap_sum":
        return float(sum(gaps))
    if field == "trace_inter_sortie_gap_max":
        return _max_or_zero(gaps)
    if field == "trace_idle_time_proxy":
        return max(0.0, duration - total_travel_time)
    if field == "trace_occupancy_bucket_count":
        return float(
            sum(
                len(trip.get("occupancy") or {})
                for trip in trips
                if isinstance(trip.get("occupancy"), dict)
            )
        )
    return 0.0


def _slack_candidate_feature(
    journey: dict[str, Any],
    field: str,
    *,
    task_time_windows: dict[int, tuple[float, float]],
) -> float:
    slacks = _journey_task_time_window_slacks(journey, task_time_windows=task_time_windows)
    if not slacks:
        return 0.0
    late_slacks = [late for _early, late in slacks]
    early_slacks = [early for early, _late in slacks]
    if field == "slack_min_late_time":
        return _min_or_zero(late_slacks)
    if field == "slack_mean_late_time":
        return float(sum(late_slacks)) / float(len(late_slacks))
    if field == "slack_min_early_time":
        return _min_or_zero(early_slacks)
    return 0.0


def _active_basis_candidate_feature(
    event: dict[str, Any],
    journey: dict[str, Any],
    field: str,
    *,
    task_set: set[int],
) -> float:
    rows = _active_basis_records(event)
    active_task_sets = [
        active_task_set
        for active_task_set, _lambda_value, _signature in rows
        if active_task_set
    ]
    if not active_task_sets:
        active_task_sets = _payload_task_sets(event.get("active_basis_task_sets") or event.get("active_task_sets"))
    if field == "active_basis_exact_task_set_count_before":
        return float(sum(1 for active_task_set in active_task_sets if active_task_set == task_set))
    if field == "active_basis_task_overlap_count_before":
        return float(sum(1 for active_task_set in active_task_sets if task_set & active_task_set))
    if field == "active_basis_task_overlap_fraction_max_before":
        denom = max(1.0, float(len(task_set)))
        return _max_or_zero(
            float(len(task_set & active_task_set)) / denom
            for active_task_set in active_task_sets
        )
    if field == "active_basis_task_jaccard_max_before":
        return _max_or_zero(_task_set_jaccard(task_set, active_task_set) for active_task_set in active_task_sets)
    if field == "active_basis_lambda_overlap_sum_before":
        return float(
            sum(
                lambda_value
                for active_task_set, lambda_value, _signature in rows
                if task_set & active_task_set
            )
        )
    if field == "active_basis_lambda_exact_task_set_sum_before":
        return float(
            sum(
                lambda_value
                for active_task_set, lambda_value, _signature in rows
                if task_set == active_task_set
            )
        )
    if field == "active_basis_signature_duplicate_count_before":
        signature = journey.get("signature")
        return float(
            sum(
                1
                for _active_task_set, _lambda_value, active_signature in rows
                if _signature_equal(signature, active_signature)
            )
        )
    return 0.0


def _pool_candidate_feature(
    event: dict[str, Any],
    field: str,
    *,
    task_set: set[int],
) -> float:
    pool_task_sets = _payload_task_sets(event.get("pool_task_sets"))
    if field == "pool_task_overlap_count_before":
        return float(sum(1 for pool_task_set in pool_task_sets if task_set & pool_task_set))
    if field == "pool_task_jaccard_max_before":
        return _max_or_zero(_task_set_jaccard(task_set, pool_task_set) for pool_task_set in pool_task_sets)
    return 0.0


def _forbidden_candidate_feature(
    event: dict[str, Any],
    journey: dict[str, Any],
    field: str,
    *,
    task_set: set[int],
) -> float:
    forbidden_signatures = event.get("forbidden_signatures")
    if field == "forbidden_signature_duplicate_count_before":
        return float(_signature_count(journey.get("signature"), forbidden_signatures))
    if field == "forbidden_task_overlap_count_before":
        signature_task_sets = [
            signature_task_set
            for signature_task_set in (
                _signature_task_set(signature)
                for signature in (forbidden_signatures or [])
            )
            if signature_task_set
        ]
        return float(sum(1 for signature_task_set in signature_task_sets if task_set & signature_task_set))
    return 0.0


def _branch_candidate_feature(
    event: dict[str, Any],
    field: str,
    *,
    task_set: set[int],
) -> float:
    constraints = _branch_constraints(event)
    touch_count = 0
    violation_count = 0
    same_partial_count = 0
    separate_violation_count = 0
    for constraint in constraints:
        kind = str(constraint.get("kind") or "")
        task_i = constraint.get("task_i")
        task_j = constraint.get("task_j")
        vehicle = constraint.get("vehicle")
        touched = (
            (task_i is not None and int(task_i) in task_set)
            or (task_j is not None and int(task_j) in task_set)
        )
        touch_count += int(touched)
        if kind == "separate_vehicle" and task_i is not None and task_j is not None:
            violated = int(task_i) in task_set and int(task_j) in task_set
            separate_violation_count += int(violated)
            violation_count += int(violated)
        elif kind == "same_vehicle" and task_i is not None and task_j is not None:
            same_partial_count += int((int(task_i) in task_set) != (int(task_j) in task_set))
    values = {
        "branch_constraint_touch_count": float(touch_count),
        "branch_constraint_violation_count": float(violation_count),
        "branch_same_vehicle_pair_partial_count": float(same_partial_count),
        "branch_separate_vehicle_pair_violation_count": float(separate_violation_count),
    }
    return values.get(field, 0.0)


def _cut_candidate_feature(
    event: dict[str, Any],
    journey: dict[str, Any],
    field: str,
    *,
    task_set: set[int],
) -> float:
    cuts = _cut_payloads(event)
    coeffs: list[float] = []
    subset_coeffs: list[float] = []
    fleet_coeff_count = 0
    weighted = 0.0
    for index, cut in enumerate(cuts):
        kind = str(cut.get("kind") or "")
        coeff = _candidate_cut_coefficient(cut, journey, task_set=task_set)
        coeffs.append(coeff)
        if kind == "subset_row":
            subset_coeffs.append(coeff)
        if kind in {"fleet_lower_bound", "fleet_upper_bound"} and abs(coeff) > 0.0:
            fleet_coeff_count += 1
        weighted += abs(_cut_dual(event, index)) * abs(coeff)
    values = {
        "candidate_cut_coeff_l1_sum": float(sum(abs(value) for value in coeffs)),
        "candidate_cut_subset_row_coeff_sum": float(sum(subset_coeffs)),
        "candidate_cut_fleet_coeff_count": float(fleet_coeff_count),
        "candidate_cut_dual_abs_weighted_coeff_sum": float(weighted),
    }
    return values.get(field, 0.0)


def _active_basis_records(event: dict[str, Any]) -> list[tuple[set[int], float, Any]]:
    rows = event.get("active_basis_rows")
    result: list[tuple[set[int], float, Any]] = []
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            task_set = _task_set(row.get("active_journey_task_set"))
            if not task_set:
                task_set = _task_set_from_sequence(row.get("active_journey_sequence"))
            result.append(
                (
                    task_set,
                    _finite_float(row.get("active_lambda_value")),
                    row.get("active_journey_signature"),
                )
            )
    if result:
        return result
    return [
        (task_set, 1.0, None)
        for task_set in _payload_task_sets(event.get("active_basis_task_sets") or event.get("active_task_sets"))
    ]


def _payload_task_sets(payload: Any) -> list[set[int]]:
    if not isinstance(payload, list):
        return []
    return [task_set for task_set in (_task_set(item) for item in payload) if task_set]


def _task_set_from_sequence(value: Any) -> set[int]:
    return set(_flatten_task_sequence(value))


def _task_set_jaccard(left: set[int], right: set[int]) -> float:
    if not left and not right:
        return 0.0
    union = left | right
    return float(len(left & right)) / float(len(union)) if union else 0.0


def _signature_equal(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return False
    return json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)


def _signature_task_set(signature: Any) -> set[int]:
    if not isinstance(signature, list):
        return set()
    result: set[int] = set()
    for item in signature:
        if isinstance(item, (list, tuple)) and item:
            result.update(_flatten_task_sequence(item[0]))
        elif isinstance(item, int):
            result.add(int(item))
    return result


def _branch_constraints(event: dict[str, Any]) -> list[dict[str, int | str | None]]:
    raw_constraints = event.get("branch_constraints")
    if not isinstance(raw_constraints, list):
        return []
    result: list[dict[str, int | str | None]] = []
    for raw in raw_constraints:
        parsed = _parse_branch_constraint(raw)
        if parsed is not None:
            result.append(parsed)
    return result


def _parse_branch_constraint(raw: Any) -> dict[str, int | str | None] | None:
    if isinstance(raw, dict):
        kind = str(raw.get("kind") or raw.get("type") or "")
        return {
            "kind": kind,
            "task_i": _optional_int(raw.get("task_i", raw.get("i", raw.get("task")))),
            "task_j": _optional_int(raw.get("task_j", raw.get("j"))),
            "vehicle": _optional_int(raw.get("vehicle")),
        }
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    if text.startswith("RF(") and ")=" in text:
        pair, kind = text[3:].split(")=", 1)
        parts = [part.strip() for part in pair.split(",")]
        if len(parts) == 2:
            return {
                "kind": kind.strip(),
                "task_i": _optional_int(parts[0]),
                "task_j": _optional_int(parts[1]),
                "vehicle": None,
            }
    if text.startswith("task_vehicle(") and ")=" in text:
        pair, state = text[len("task_vehicle(") :].split(")=", 1)
        parts = [part.strip() for part in pair.split(",")]
        if len(parts) == 2:
            return {
                "kind": f"task_vehicle_{state.strip()}",
                "task_i": _optional_int(parts[0]),
                "task_j": None,
                "vehicle": _optional_int(parts[1]),
            }
    return None


def _optional_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _cut_payloads(event: dict[str, Any]) -> list[dict[str, Any]]:
    raw_cuts = event.get("cuts")
    if not isinstance(raw_cuts, list):
        return []
    result: list[dict[str, Any]] = []
    for raw in raw_cuts:
        if not isinstance(raw, dict):
            continue
        payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
        kind = str(raw.get("kind") or payload.get("kind") or "")
        merged = dict(payload)
        merged.update(raw)
        merged["kind"] = kind
        result.append(merged)
    return result


def _candidate_cut_coefficient(
    cut: dict[str, Any],
    journey: dict[str, Any],
    *,
    task_set: set[int],
) -> float:
    kind = str(cut.get("kind") or "")
    if kind == "subset_row":
        cut_tasks = _task_set(cut.get("tasks"))
        k = max(1, int(_finite_float(cut.get("k"), 2.0)))
        return float(len(cut_tasks & task_set) // k)
    if kind in {"fleet_lower_bound", "fleet_upper_bound"}:
        return 1.0
    if kind == "sortie_lower_bound":
        return -float(len(_journey_trip_dicts(journey)) or 1)
    return 0.0


def _cut_dual(event: dict[str, Any], index: int) -> float:
    cut_duals = event.get("cut_duals")
    if isinstance(cut_duals, list) and 0 <= int(index) < len(cut_duals):
        return _finite_float(cut_duals[int(index)])
    if isinstance(cut_duals, dict):
        for key in (int(index), str(index)):
            if key in cut_duals:
                return _finite_float(cut_duals.get(key))
    return 0.0


def _journey_task_time_window_slacks(
    journey: dict[str, Any],
    *,
    task_time_windows: dict[int, tuple[float, float]],
) -> list[tuple[float, float]]:
    service_start_by_task = _journey_service_start_by_task(journey)
    values: list[tuple[float, float]] = []
    for task_id, start_time in sorted(service_start_by_task.items()):
        if task_id not in task_time_windows:
            continue
        ready, due = task_time_windows[task_id]
        values.append((float(start_time - ready), float(due - start_time)))
    return values


def _journey_trip_dicts(journey: dict[str, Any]) -> list[dict[str, Any]]:
    trips = journey.get("trips")
    if not isinstance(trips, list):
        return []
    return [trip for trip in trips if isinstance(trip, dict)]


def _journey_arc_option_ids(journey: dict[str, Any]) -> list[str]:
    arc_ids: list[str] = []
    for trip in _journey_trip_dicts(journey):
        arc_ids.extend(str(value) for value in (trip.get("arc_option_ids") or []))
    return arc_ids


def _journey_service_start_times(journey: dict[str, Any]) -> list[float]:
    values: list[float] = []
    for trip in _journey_trip_dicts(journey):
        service_start = trip.get("service_start")
        if isinstance(service_start, dict):
            values.extend(
                _finite_float(value)
                for value in service_start.values()
                if _has_finite_number(value)
            )
    return values


def _journey_service_start_by_task(journey: dict[str, Any]) -> dict[int, float]:
    values: dict[int, float] = {}
    for trip in _journey_trip_dicts(journey):
        service_start = trip.get("service_start")
        if not isinstance(service_start, dict):
            continue
        for task_id, value in service_start.items():
            if _has_finite_number(value):
                values[int(task_id)] = _finite_float(value)
    return values


def _candidate_arc_option_ids(journey: dict[str, Any]) -> list[str]:
    arc_ids = _journey_arc_option_ids(journey)
    if arc_ids:
        return arc_ids
    signature = journey.get("signature")
    if not isinstance(signature, list):
        return []
    result: list[str] = []
    for item in signature:
        if isinstance(item, (list, tuple)) and len(item) >= 2 and isinstance(item[1], list):
            result.extend(str(arc) for arc in item[1])
    return result


def _candidate_path_token_rows(journey: dict[str, Any]) -> tuple[list[int], list[int], list[int]]:
    token_ids: list[int] = []
    pair_ids: list[int] = []
    type_ids: list[int] = []
    for arc_id in _candidate_arc_option_ids(journey):
        parsed = _parse_arc_option_id(arc_id)
        token_ids.append(_hash_bucket(str(arc_id), PATH_TOKEN_HASH_BUCKET_COUNT))
        pair_ids.append(
            _hash_bucket(
                f"{parsed.get('src', '')}->{parsed.get('dst', '')}",
                PATH_PAIR_HASH_BUCKET_COUNT,
            )
        )
        type_ids.append(int(PATH_TYPE_TO_ID.get(str(parsed.get("path_type", "")), 0)))
    return token_ids, pair_ids, type_ids


def _parse_arc_option_id(arc_id: str) -> dict[str, str]:
    text = str(arc_id)
    if "->" not in text:
        return {"src": "", "dst": "", "path_type": "", "rank": ""}
    src, tail = text.split("->", 1)
    parts = tail.split(":")
    return {
        "src": src,
        "dst": parts[0] if parts else "",
        "path_type": parts[1] if len(parts) >= 2 else "",
        "rank": parts[2] if len(parts) >= 3 else "",
    }


def _hash_bucket(value: str, bucket_count: int) -> int:
    if int(bucket_count) <= 0:
        raise ValueError("bucket_count must be positive")
    digest = hashlib.sha1(str(value).encode("utf-8")).hexdigest()
    return 1 + (int(digest[:16], 16) % int(bucket_count))


def _padded_long_tensor(rows: list[list[int]]) -> torch.Tensor:
    width = max(1, max((len(row) for row in rows), default=0))
    padded = [row + [0] * (width - len(row)) for row in rows]
    return torch.tensor(padded, dtype=torch.long)


def _padded_bool_mask(rows: list[list[int]]) -> torch.Tensor:
    width = max(1, max((len(row) for row in rows), default=0))
    mask = [[idx < len(row) for idx in range(width)] for row in rows]
    return torch.tensor(mask, dtype=torch.bool)


def _graph_task_time_windows(graph: Any) -> dict[int, tuple[float, float]]:
    schema = list(getattr(graph, "node_feature_schema", []) or [])
    if "time_window_start" not in schema or "time_window_end" not in schema:
        return {}
    start_idx = schema.index("time_window_start")
    end_idx = schema.index("time_window_end")
    task_ids = {int(value) for value in graph.task_ids.tolist()}
    windows: dict[int, tuple[float, float]] = {}
    for node_idx, node_id in enumerate(graph.node_ids.tolist()):
        task_id = int(node_id)
        if task_id not in task_ids:
            continue
        windows[task_id] = (
            float(graph.x[node_idx, start_idx].item()),
            float(graph.x[node_idx, end_idx].item()),
        )
    return windows


def _sum_trip_numeric_field(trips: list[dict[str, Any]], field: str) -> float:
    return float(
        sum(
            _finite_float(trip.get(field))
            for trip in trips
            if _has_finite_number(trip.get(field))
        )
    )


def _arc_option_has_type(arc_id: str, path_type: str) -> bool:
    text = str(arc_id)
    return f":{path_type}:" in text or text.endswith(f":{path_type}")


def _has_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _max_or_zero(values: Iterable[float]) -> float:
    values = list(values)
    return max(values) if values else 0.0


def _min_or_zero(values: Iterable[float]) -> float:
    values = list(values)
    return min(values) if values else 0.0


def _context_feature(event: dict[str, Any], row: dict[str, Any], field: str) -> float:
    aliases = {
        "column_pool_size_before": "pool_journey_count",
        "active_basis_size_before": "active_basis_journey_count",
        "active_basis_unique_task_set_count_before": "active_task_set_count",
        "lambda_active_count_before": "active_basis_journey_count",
        "lambda_fractional_count_before": "active_basis_fractional_journey_count",
        "rmp_objective_before": "objective_before",
        "pricing_tail_retry_count_before": "state_t_final_judge_retry_count",
        "final_judge_retry_count": "state_t_final_judge_retry_count",
    }
    if field == "cg_iter":
        return _finite_float(row.get("cg_iter", event.get("cg_iter")))
    if field == "node_id":
        return _finite_float(row.get("node_id", event.get("node_id")))
    if field == "depth":
        return _finite_float(row.get("depth", event.get("depth")))
    if field == "dual_l1_norm_before":
        dual = event.get("true_dual_vector")
        if isinstance(dual, list):
            return float(sum(abs(_finite_float(value)) for value in dual))
    if field == "dual_linf_norm_before":
        dual = event.get("true_dual_vector")
        if isinstance(dual, list) and dual:
            return float(max(abs(_finite_float(value)) for value in dual))
    if field == "fleet_dual":
        duals = event.get("true_duals")
        if isinstance(duals, dict):
            return _finite_float(duals.get("fleet_limit"))
    if field == "cut_dual_l1_norm":
        cut_duals = event.get("cut_duals")
        if isinstance(cut_duals, dict):
            return float(sum(abs(_finite_float(value)) for value in cut_duals.values()))
        if isinstance(cut_duals, list):
            return float(sum(abs(_finite_float(value)) for value in cut_duals))
    if field == "branch_constraint_count":
        constraints = event.get("branch_constraints")
        return float(len(constraints)) if isinstance(constraints, list) else _finite_float(event.get(field))
    if field == "recent_objective_delta_before":
        # Do not alias this to objective_delta: objective_delta is the current
        # batch outcome and would make same-context pairs carry label leakage.
        if field in row:
            return _finite_float(row.get(field))
        return _finite_float(event.get(field))
    if field in row:
        return _finite_float(row.get(field))
    alias = aliases.get(field)
    if alias and alias in row:
        return _finite_float(row.get(alias))
    if alias and alias in event:
        return _finite_float(event.get(alias))
    return _finite_float(event.get(field))


def _batch_features(row: dict[str, Any], journeys: list[dict[str, Any]]) -> list[float]:
    rc_values = [_true_reduced_cost(journey) for journey in journeys]
    finite_rc = [value for value in rc_values if math.isfinite(value)]
    negative_count = sum(1 for value in finite_rc if value < 0.0)
    nonnegative_count = len(finite_rc) - negative_count
    returned_count = _finite_float(row.get("returned_journey_count"), float(len(journeys)))
    replacement_journeys = _finite_float(row.get("replacement_journeys"))
    new_task_set_count = _finite_float(row.get("new_task_set_count"))
    active_changed_count = _finite_float(row.get("active_changed_task_set_count"))
    added_journeys = _finite_float(row.get("added_journeys"))
    replacement_ratio = replacement_journeys / max(1.0, added_journeys)
    support_changing_ratio = active_changed_count / max(1.0, added_journeys)
    best_rc = min(finite_rc) if finite_rc else 0.0
    mean_rc = sum(finite_rc) / float(len(finite_rc)) if finite_rc else 0.0
    replacement_heavy = replacement_ratio >= 0.5
    new_task_set = new_task_set_count > 0.0
    active_support_overlap = active_changed_count > 0.0
    best_rc_batch = best_rc < 0.0 and negative_count > 0
    random_unknown = not (replacement_heavy or new_task_set or active_support_overlap or best_rc_batch)
    values = {
        "returned_journey_count": returned_count,
        "added_journeys": added_journeys,
        "new_journeys": _finite_float(row.get("new_journeys")),
        "replacement_journeys": replacement_journeys,
        "new_task_set_count": new_task_set_count,
        "replacement_task_set_count": _finite_float(row.get("replacement_task_set_count")),
        "active_changed_task_set_count": active_changed_count,
        "negative_candidate_count": float(negative_count),
        "nonnegative_candidate_count": float(nonnegative_count),
        "best_true_reduced_cost": _finite_float(row.get("best_true_reduced_cost"), best_rc),
        "mean_true_reduced_cost": mean_rc,
        "replacement_ratio": replacement_ratio,
        "support_changing_ratio": support_changing_ratio,
        "batch_type_best_rc": 1.0 if best_rc_batch else 0.0,
        "batch_type_replacement_heavy": 1.0 if replacement_heavy else 0.0,
        "batch_type_new_task_set": 1.0 if new_task_set else 0.0,
        "batch_type_active_support_overlap": 1.0 if active_support_overlap else 0.0,
        "batch_type_random_or_unknown": 1.0 if random_unknown else 0.0,
    }
    return [float(values[field]) for field in BATCH_IMPACT_BATCH_FEATURE_SCHEMA]


def _batch_type_name(batch_features: list[float]) -> str:
    values = dict(zip(BATCH_IMPACT_BATCH_FEATURE_SCHEMA, batch_features))
    for key, name in (
        ("batch_type_replacement_heavy", "replacement_heavy"),
        ("batch_type_new_task_set", "new_task_set"),
        ("batch_type_active_support_overlap", "active_support_overlap"),
        ("batch_type_best_rc", "best_rc"),
    ):
        if values.get(key, 0.0) > 0.5:
            return name
    return "random_or_unknown"


def _task_set_in_payload(task_set: set[int], payload: Any) -> bool:
    return _task_set_count(task_set, payload) > 0


def _task_set_count(task_set: set[int], payload: Any) -> int:
    if not task_set or not isinstance(payload, list):
        return 0
    target = tuple(sorted(task_set))
    count = 0
    for item in payload:
        parsed = tuple(sorted(_task_set(item)))
        if parsed == target:
            count += 1
    return count


def _signature_in_payload(signature: Any, payload: Any) -> bool:
    return _signature_count(signature, payload) > 0


def _signature_count(signature: Any, payload: Any) -> int:
    if signature is None or not isinstance(payload, list):
        return 0
    target = json.dumps(signature, sort_keys=True)
    return sum(1 for item in payload if json.dumps(item, sort_keys=True) == target)


def _true_reduced_cost(journey: dict[str, Any]) -> float:
    for key in ("true_reduced_cost", "manual_true_reduced_cost", "reduced_cost"):
        if key in journey:
            return _finite_float(journey.get(key))
    return 0.0


def _finite_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in {None, ""}:
            return float(default)
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    if math.isnan(result) or math.isinf(result):
        return float(default)
    return float(result)


def _row_bool_label(row: dict[str, Any], key: str, *, default: bool) -> bool:
    value = row.get(key)
    if key not in row or value is None or value == "":
        return bool(default)
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "y"}:
            return True
        if lowered in {"false", "no", "n"}:
            return False
    return bool(_finite_float(value, 1.0 if default else 0.0) > 0.5)


def _first_finite(row: dict[str, Any], keys: tuple[str, ...], *, default: float) -> float:
    for key in keys:
        if key in row:
            return _finite_float(row.get(key), default)
    return float(default)


def _feature_stats(sample_dir: Path, field: str) -> tuple[list[float], list[float]]:
    tensors: list[torch.Tensor] = []
    for path in sorted(sample_dir.glob("sample_*.pt")):
        sample = torch.load(path, map_location="cpu", weights_only=False)
        tensor = getattr(sample, field).to(dtype=torch.float32)
        if tensor.dim() == 1:
            tensor = tensor.unsqueeze(0)
        tensors.append(tensor)
    if not tensors:
        return [], []
    stacked = torch.cat(tensors, dim=0)
    mean = stacked.mean(dim=0)
    std = stacked.std(dim=0, unbiased=False)
    std = torch.where(std > 1.0e-12, std, torch.ones_like(std))
    return [float(value) for value in mean.tolist()], [float(value) for value in std.tolist()]


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Batch Impact Dataset 构建报告",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把 same-context intervention rows 转换成 `GATBatchImpactModel` 可直接读取的",
        "batch-impact 图样本。该脚本只做离线数据转换，不运行 BPC / pricing / RMP / worker，",
        "不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_batch_impact_dataset = current",
        f"status = {summary['status']}",
        f"sample_count = {summary['sample_count']}",
        f"candidate_count = {summary['candidate_count']}",
        f"context_match_rate = {summary['context_match_rate']}",
        f"batch_label_counts = {summary['batch_label_counts']}",
        f"candidate_label_counts = {summary['candidate_label_counts']}",
        f"batch_type_counts = {summary['batch_type_counts']}",
        f"pairwise_context_stats = {summary['pairwise_context_stats']}",
        f"ranking_ready = {str(summary['ranking_ready']).lower()}",
        f"ranking_blockers = {summary['ranking_blockers']}",
        f"family_counts = {summary['family_counts']}",
        f"task_count_counts = {summary['task_count_counts']}",
        f"instance_count = {summary['instance_count']}",
        f"region_count = {summary['region_count']}",
        f"training_ready = {str(summary['training_ready']).lower()}",
        f"training_blockers = {summary['training_blockers']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 标签语义",
        "",
        "- `y_candidate_high_priority`：true-RC negative 且显式 longer-horizon ROI 为正，",
        "  并且不是 `label_bad_mode_switch`；",
        "- `y_candidate_delay_risk`：true-RC negative 但 ROI 非正、bad-mode，",
        "  或缺少可证明改善 RMP trajectory 的 admission 标签；",
        "- `y_batch_roi_positive` / `y_accepted_batch_roi`：batch-level longer-horizon ROI 标签；",
        "- `y_bad_mode_switch`：候选列虽然 true-RC negative，但会增加 RMP / pricing / exact workload",
        "  或触发拖尾的硬负标签；",
        "- `y_delta_v` / `y_barrier_slack`：trajectory/CBF head 的离线监督目标；",
        "- 所有标签都只允许训练 admission scheduling，不能作为 pricing certificate。",
        "",
        "## Pairwise Ranking Readiness",
        "",
        "`training_ready=true` 只表示可以做离线 diagnostic classification / regression；",
        "`ranking_ready=true` 才表示同一 RMP context 下至少存在多个 batch 样本，",
        "可以合法训练 pairwise ranking loss。没有 same-context batch pair 时，",
        "不能跨 context 伪造 `score(high-ROI) > score(low-ROI)` 监督。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
