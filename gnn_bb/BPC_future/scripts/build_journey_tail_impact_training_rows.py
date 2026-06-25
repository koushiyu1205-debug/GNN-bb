#!/usr/bin/env python3
"""Build audit-only Journey tail-impact training rows.

This script fuses diagnostic sources:

* weak rough-negative pricing rows that were filtered by true-RC materialization;
* branch-impact rows that describe whether a branch reduces or moves proof tail.
* tail-action proof-cost rows;
* tail-action counterfactual delta rows;
* late true-negative / weak-filtered pricing tail rows.

It is intentionally offline.  It reads existing audit artifacts only and does
not run BPC, pricing, RMP, or produce certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_tail_impact_training_rows_20260623")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260623_bpc_future_journey_tail_impact_training_rows_zh.md"
)

TAIL_IMPACT_FEATURE_SCHEMA: tuple[str, ...] = (
    "source_is_branch",
    "source_is_weak_negative",
    "source_is_tail_action",
    "source_is_tail_action_counterfactual",
    "source_is_late_negative",
    "depth",
    "time",
    "cg_iter",
    "pricing_time_limit",
    "profile_generation_time",
    "profile_dp_time",
    "dp_state_count",
    "negative_journeys",
    "selected_trips",
    "weak_negative_journeys_filtered",
    "profile_weak_filtered_materialized_count",
    "weak_best_rough_rc",
    "weak_best_true_rc",
    "weak_max_true_minus_rough",
    "branch_candidate_count",
    "branch_eligible_count",
    "branch_rank_in_priority_top",
    "branch_pool_max_child_width",
    "branch_pool_total_child_width",
    "branch_pool_balance_gap",
    "tail_action_no_column",
    "tail_action_pool_max_child_width",
    "tail_action_pool_total_child_width",
    "tail_action_pool_balance_gap",
    "late_has_true_negative",
    "late_has_weak_filtered",
    "late_active_changed_task_sets",
    "late_inactive_changed_task_sets",
    "late_added_journeys",
    "late_new_task_sets",
    "late_replacement_task_sets",
)

TAIL_IMPACT_OUTCOME_SCHEMA: tuple[str, ...] = (
    "branch_child_negative_pricing_events",
    "branch_child_completion_bound_retries",
    "branch_child_early_branch_triggers",
    "tail_action_direct_started_count",
    "tail_action_direct_unstarted_count",
    "tail_action_subtree_node_count",
    "tail_action_subtree_pricing_events",
    "tail_action_subtree_negative_pricing_events",
    "tail_action_subtree_completion_retries",
    "tail_action_subtree_completion_retry_pricing_events",
    "tail_action_subtree_completion_retry_low_min_fill",
    "tail_action_subtree_completion_retry_min_harvest_min_fill",
    "tail_action_subtree_completion_retry_max_harvest_min_fill",
    "tail_action_subtree_completion_retry_found_negative",
    "tail_action_subtree_completion_retry_certified_no_negative",
    "tail_action_subtree_completion_retry_incomplete",
    "tail_action_subtree_early_branch_triggers",
    "tail_action_subtree_no_column_triggers",
    "tail_action_subtree_observed_wall_span",
    "tail_counterfactual_local_tail_cost_delta",
    "tail_counterfactual_wall_time_delta",
    "tail_counterfactual_pricing_calls_delta",
    "tail_counterfactual_exact_pricing_calls_delta",
    "tail_counterfactual_node_count_delta",
    "tail_counterfactual_solving_time_delta",
    "tail_counterfactual_primal_bound_delta",
    "tail_counterfactual_dual_bound_delta",
    "tail_counterfactual_gap_delta",
    "tail_counterfactual_completion_retry_trigger_count_delta",
    "tail_counterfactual_completion_retry_pricing_count_delta",
    "tail_counterfactual_completion_retry_work_time_proxy_delta",
    "tail_counterfactual_completion_retry_generated_sequences_delta",
    "tail_counterfactual_completion_retry_evaluated_timed_trips_delta",
    "tail_counterfactual_negative_pricing_delta",
    "tail_counterfactual_completion_retry_delta",
    "tail_counterfactual_no_column_chain_delta",
)

TAIL_IMPACT_LABEL_SCHEMA: tuple[str, ...] = (
    "y_useful_tail_reduction",
    "y_tail_risk",
    "y_weak_negative_filtered",
    "y_completion_bound_tail",
    "y_early_branch_continues",
    "y_negative_chain_continues",
    "y_active_touch",
    "y_inactive_only",
    "y_child_negative_pricing_events",
    "y_child_completion_bound_retries",
    "y_child_early_branch_triggers",
    "y_tail_action_no_column",
    "y_tail_action_counterfactual",
    "y_local_tail_improved",
    "y_whole_run_improved",
    "y_budget_dominant_improvement",
    "y_local_improved_but_whole_run_not",
    "y_timeout_resolved",
    "y_timeout_regression",
    "y_right_censored_counterfactual",
    "y_child_unstarted",
    "y_subtree_no_column_chain",
    "y_tail_min_fill_completion_retry",
    "y_tail_min_fill_found_negative",
    "y_tail_min_fill_certified_no_negative",
    "y_late_true_negative",
    "y_late_active_support_changing",
    "y_late_inactive_only",
    "y_late_weak_filtered",
)


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            yield record


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_weak_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_iter_jsonl(path / "weak_negative_tail_rows.jsonl"))
            continue
        if path.name == "summary.json":
            rows.extend(_iter_jsonl(path.parent / "weak_negative_tail_rows.jsonl"))
            continue
        if path.suffix == ".jsonl":
            rows.extend(_iter_jsonl(path))
            continue
        payload = _read_json(path)
        raw_rows = payload.get("rows")
        if isinstance(raw_rows, list):
            rows.extend(row for row in raw_rows if isinstance(row, dict))
    return rows


def _load_branch_training_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_iter_jsonl(path / "branch_training_rows.jsonl"))
            continue
        if path.name == "summary.json":
            rows.extend(_iter_jsonl(path.parent / "branch_training_rows.jsonl"))
            payload = _read_json(path)
            raw_rows = payload.get("branch_training_rows")
            if isinstance(raw_rows, list):
                rows.extend(row for row in raw_rows if isinstance(row, dict))
            continue
        if path.suffix == ".jsonl":
            rows.extend(_iter_jsonl(path))
            continue
        payload = _read_json(path)
        raw_rows = payload.get("branch_training_rows")
        if isinstance(raw_rows, list):
            rows.extend(row for row in raw_rows if isinstance(row, dict))
    return rows


def _load_tail_action_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_iter_jsonl(path / "early_branch_trigger_rows.jsonl"))
            continue
        if path.name == "summary.json":
            rows.extend(_iter_jsonl(path.parent / "early_branch_trigger_rows.jsonl"))
            raw_rows = _read_json(path).get("sample_early_branch_rows")
            if isinstance(raw_rows, list):
                rows.extend(row for row in raw_rows if isinstance(row, dict))
            continue
        if path.suffix == ".jsonl":
            rows.extend(_iter_jsonl(path))
            continue
        payload = _read_json(path)
        raw_rows = payload.get("sample_early_branch_rows")
        if isinstance(raw_rows, list):
            rows.extend(row for row in raw_rows if isinstance(row, dict))
    return rows


def _load_tail_action_counterfactual_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_iter_jsonl(path / "tail_action_counterfactual_delta_rows.jsonl"))
            continue
        if path.name == "summary.json":
            rows.extend(_iter_jsonl(path.parent / "tail_action_counterfactual_delta_rows.jsonl"))
            raw_rows = _read_json(path).get("rows")
            if isinstance(raw_rows, list):
                rows.extend(row for row in raw_rows if isinstance(row, dict))
            continue
        if path.suffix == ".jsonl":
            rows.extend(_iter_jsonl(path))
            continue
        payload = _read_json(path)
        raw_rows = payload.get("rows")
        if isinstance(raw_rows, list):
            rows.extend(row for row in raw_rows if isinstance(row, dict))
    return rows


def _load_late_negative_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_iter_jsonl(path / "late_negative_tail_rows.jsonl"))
            continue
        if path.name == "summary.json":
            rows.extend(_iter_jsonl(path.parent / "late_negative_tail_rows.jsonl"))
            raw_rows = _read_json(path).get("rows")
            if isinstance(raw_rows, list):
                rows.extend(row for row in raw_rows if isinstance(row, dict))
            continue
        if path.suffix == ".jsonl":
            rows.extend(_iter_jsonl(path))
            continue
        payload = _read_json(path)
        raw_rows = payload.get("rows")
        if isinstance(raw_rows, list):
            rows.extend(row for row in raw_rows if isinstance(row, dict))
    return rows


def _float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return float(default)
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    if result != result:
        return float(default)
    return float(result)


def _int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return int(default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _pair(value: Any) -> tuple[int | None, int | None]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None, None
    try:
        return int(float(value[0])), int(float(value[1]))
    except (TypeError, ValueError):
        return None, None


def _time_window_family(value: Any) -> str:
    text = str(value or "")
    for token in ("greedy-anchor", "random-wave", "sector-wave"):
        if token in text:
            return token
    return ""


def _tail_action_class_from_action(action: Any) -> str:
    return {
        "FRONTIER_REFINEMENT": "A_FRONTIER_REFINEMENT",
        "BROAD_PLATEAU_FALLBACK": "B_BROAD_PLATEAU",
        "CONTINUE_COLUMN_GENERATION": "C_CONTINUE_CG",
        "EARLY_BRANCH": "D_EARLY_BRANCH",
    }.get(str(action or ""), "UNKNOWN")


def _tail_action_class(row: dict[str, Any]) -> str:
    raw = str(row.get("tail_action_class") or "")
    if raw:
        return raw
    return _tail_action_class_from_action(row.get("tail_action"))


def _tail_action_productivity_class(row: dict[str, Any]) -> str:
    return str(row.get("tail_action_productivity_class") or "unknown")


def _row_context_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("source_type"),
        row.get("log_file"),
        row.get("node_id"),
        row.get("depth"),
        json.dumps(row.get("baseline_pair"), sort_keys=True),
        row.get("task_i"),
        row.get("task_j"),
    )


def _duplicate_context_action_count(rows: list[dict[str, Any]]) -> int:
    seen: set[tuple[Any, ...]] = set()
    duplicates = 0
    for row in rows:
        key = _row_context_key(row)
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
    return duplicates


def _has_holdout_positive(row: dict[str, Any]) -> bool:
    if _float(row.get("labels", {}).get("y_whole_run_improved")) <= 0.5:
        return False
    raw = row.get("raw_source") if isinstance(row.get("raw_source"), dict) else {}
    return bool(
        row.get("holdout_context")
        or row.get("is_holdout")
        or raw.get("holdout_context")
        or raw.get("is_holdout")
        or raw.get("positive_holdout_context")
    )


def _branch_feature_map(row: dict[str, Any]) -> dict[str, float]:
    schema = row.get("branch_feature_schema") or []
    values = row.get("branch_features") or []
    if not isinstance(schema, list) or not isinstance(values, list):
        return {}
    return {
        str(name): _float(value)
        for name, value in zip(schema, values, strict=False)
    }


def _feature_vector(values: dict[str, Any]) -> list[float]:
    return [float(_float(values.get(name))) for name in TAIL_IMPACT_FEATURE_SCHEMA]


def _outcome_vector(values: dict[str, Any]) -> list[float]:
    return [float(_float(values.get(name))) for name in TAIL_IMPACT_OUTCOME_SCHEMA]


def _label_vector(labels: dict[str, Any]) -> dict[str, float]:
    return {name: float(_float(labels.get(name))) for name in TAIL_IMPACT_LABEL_SCHEMA}


def _weak_training_row(row: dict[str, Any]) -> dict[str, Any]:
    labels = _label_vector(
        {
            "y_useful_tail_reduction": 0.0,
            "y_tail_risk": 1.0,
            "y_weak_negative_filtered": 1.0,
        }
    )
    features = _feature_vector(
        {
            "source_is_weak_negative": 1.0,
            "depth": row.get("depth"),
            "time": row.get("time"),
            "cg_iter": row.get("cg_iter"),
            "pricing_time_limit": row.get("pricing_time_limit"),
            "profile_generation_time": row.get("profile_generation_time"),
            "profile_dp_time": row.get("profile_dp_time"),
            "dp_state_count": row.get("dp_state_count"),
            "negative_journeys": row.get("negative_journeys"),
            "selected_trips": row.get("selected_trips"),
            "weak_negative_journeys_filtered": row.get("weak_negative_journeys_filtered"),
            "profile_weak_filtered_materialized_count": row.get(
                "profile_weak_filtered_materialized_count"
            ),
            "weak_best_rough_rc": row.get("profile_weak_filtered_best_rough_rc"),
            "weak_best_true_rc": row.get("profile_weak_filtered_best_true_rc"),
            "weak_max_true_minus_rough": row.get(
                "profile_weak_filtered_max_true_minus_rough"
            ),
        }
    )
    outcomes = _outcome_vector({})
    return {
        "schema_version": "journey_tail_impact_training_row_v1",
        "source_type": "weak_negative_tail",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "log_file": row.get("log_file"),
        "node_id": row.get("node_id"),
        "depth": row.get("depth"),
        "cg_iter": row.get("cg_iter"),
        "time": row.get("time"),
        "task_i": None,
        "task_j": None,
        "tail_class": "weak_negative_filtered",
        "feature_schema": list(TAIL_IMPACT_FEATURE_SCHEMA),
        "features": features,
        "decision_feature_schema": list(TAIL_IMPACT_FEATURE_SCHEMA),
        "decision_features": features,
        "outcome_schema": list(TAIL_IMPACT_OUTCOME_SCHEMA),
        "outcomes": outcomes,
        "label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "labels": labels,
        "outcome_label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "outcome_labels": labels,
        "raw_source": row,
    }


def _branch_training_row(row: dict[str, Any]) -> dict[str, Any]:
    branch_features = _branch_feature_map(row)
    branch_labels = row.get("branch_labels") if isinstance(row.get("branch_labels"), dict) else {}
    child_negative_events = _float(branch_labels.get("y_child_negative_pricing_events"))
    child_cb_retries = _float(branch_labels.get("y_child_completion_bound_retries"))
    child_early_branches = _float(branch_labels.get("y_child_early_branch_triggers"))
    tail_improved = _float(branch_labels.get("y_tail_improved"))
    tail_risk = 1.0 if (
        tail_improved < 0.5
        or _float(branch_labels.get("y_completion_bound_tail")) > 0.5
        or _float(branch_labels.get("y_early_branch_continues")) > 0.5
        or _float(branch_labels.get("y_negative_chain_continues")) > 0.5
        or _float(branch_labels.get("y_inactive_only")) > 0.5
    ) else 0.0
    labels = _label_vector(
        {
            "y_useful_tail_reduction": tail_improved,
            "y_tail_risk": tail_risk,
            "y_completion_bound_tail": branch_labels.get("y_completion_bound_tail"),
            "y_early_branch_continues": branch_labels.get("y_early_branch_continues"),
            "y_negative_chain_continues": branch_labels.get("y_negative_chain_continues"),
            "y_active_touch": branch_labels.get("y_active_touch"),
            "y_inactive_only": branch_labels.get("y_inactive_only"),
            "y_child_negative_pricing_events": child_negative_events,
            "y_child_completion_bound_retries": child_cb_retries,
            "y_child_early_branch_triggers": child_early_branches,
        }
    )
    features = _feature_vector(
        {
            "source_is_branch": 1.0,
            "depth": row.get("depth"),
            "branch_candidate_count": branch_features.get("candidate_count"),
            "branch_eligible_count": branch_features.get("eligible_count"),
            "branch_rank_in_priority_top": branch_features.get("branch_rank_in_priority_top"),
            "branch_pool_max_child_width": branch_features.get("pool_max_child_width"),
            "branch_pool_total_child_width": branch_features.get("pool_total_child_width"),
            "branch_pool_balance_gap": branch_features.get("pool_balance_gap"),
        }
    )
    outcomes = _outcome_vector(
        {
            "branch_child_negative_pricing_events": child_negative_events,
            "branch_child_completion_bound_retries": child_cb_retries,
            "branch_child_early_branch_triggers": child_early_branches,
        }
    )
    return {
        "schema_version": "journey_tail_impact_training_row_v1",
        "source_type": "branch_impact",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "log_file": row.get("log_file"),
        "node_id": row.get("branch_node_id"),
        "depth": row.get("depth"),
        "cg_iter": None,
        "task_i": row.get("task_i"),
        "task_j": row.get("task_j"),
        "tail_class": row.get("tail_class"),
        "feature_schema": list(TAIL_IMPACT_FEATURE_SCHEMA),
        "features": features,
        "decision_feature_schema": list(TAIL_IMPACT_FEATURE_SCHEMA),
        "decision_features": features,
        "outcome_schema": list(TAIL_IMPACT_OUTCOME_SCHEMA),
        "outcomes": outcomes,
        "label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "labels": labels,
        "outcome_label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "outcome_labels": labels,
        "raw_source": row,
    }


def _tail_action_training_row(row: dict[str, Any]) -> dict[str, Any]:
    tail_action_class = _tail_action_class(row)
    tail_action_productivity_class = _tail_action_productivity_class(row)
    negative_events = _float(row.get("child_subtree_negative_pricing_event_count"))
    completion_retries = _float(row.get("child_subtree_completion_retry_count"))
    low_min_fill_retries = _float(row.get("child_subtree_completion_retry_low_min_fill_count"))
    low_min_fill_found_negative = _float(
        row.get("child_subtree_completion_retry_found_negative_count")
    )
    low_min_fill_certified = _float(
        row.get("child_subtree_completion_retry_certified_no_negative_count")
    )
    early_branches = _float(row.get("child_subtree_early_branch_trigger_count"))
    no_column_chain = _float(row.get("child_subtree_no_column_early_branch_trigger_count"))
    unstarted = _float(row.get("child_direct_unstarted_count"))
    tail_risk = 1.0 if (
        negative_events > 0.0
        or completion_retries > 0.0
        or early_branches > 0.0
        or no_column_chain > 0.0
        or unstarted > 0.0
    ) else 0.0
    labels = _label_vector(
        {
            "y_useful_tail_reduction": 0.0,
            "y_tail_risk": tail_risk,
            "y_completion_bound_tail": 1.0 if completion_retries > 0.0 else 0.0,
            "y_early_branch_continues": 1.0 if early_branches > 0.0 else 0.0,
            "y_negative_chain_continues": 1.0 if negative_events > 0.0 else 0.0,
            "y_child_negative_pricing_events": negative_events,
            "y_child_completion_bound_retries": completion_retries,
            "y_child_early_branch_triggers": early_branches,
            "y_tail_action_no_column": 1.0 if bool(row.get("tail_action_no_column")) else 0.0,
            "y_child_unstarted": unstarted,
            "y_subtree_no_column_chain": no_column_chain,
            "y_tail_min_fill_completion_retry": 1.0 if low_min_fill_retries > 0.0 else 0.0,
            "y_tail_min_fill_found_negative": 1.0 if low_min_fill_found_negative > 0.0 else 0.0,
            "y_tail_min_fill_certified_no_negative": 1.0 if low_min_fill_certified > 0.0 else 0.0,
        }
    )
    features = _feature_vector(
        {
            "source_is_tail_action": 1.0,
            "depth": row.get("depth"),
            "time": row.get("time"),
            "cg_iter": row.get("cg_iter"),
            "branch_pool_max_child_width": row.get("no_column_branch_pool_max_child_width"),
            "branch_pool_total_child_width": row.get("no_column_branch_pool_total_child_width"),
            "branch_pool_balance_gap": row.get("no_column_branch_pool_balance_gap"),
            "branch_child_negative_pricing_events": negative_events,
            "branch_child_completion_bound_retries": completion_retries,
            "branch_child_early_branch_triggers": early_branches,
            "tail_action_no_column": 1.0 if bool(row.get("tail_action_no_column")) else 0.0,
            "tail_action_pool_max_child_width": row.get("no_column_branch_pool_max_child_width"),
            "tail_action_pool_total_child_width": row.get("no_column_branch_pool_total_child_width"),
            "tail_action_pool_balance_gap": row.get("no_column_branch_pool_balance_gap"),
        }
    )
    outcomes = _outcome_vector(
        {
            "branch_child_negative_pricing_events": negative_events,
            "branch_child_completion_bound_retries": completion_retries,
            "branch_child_early_branch_triggers": early_branches,
            "tail_action_direct_started_count": row.get("child_direct_started_count"),
            "tail_action_direct_unstarted_count": row.get("child_direct_unstarted_count"),
            "tail_action_subtree_node_count": row.get("child_subtree_node_count"),
            "tail_action_subtree_pricing_events": row.get("child_subtree_pricing_event_count"),
            "tail_action_subtree_negative_pricing_events": negative_events,
            "tail_action_subtree_completion_retries": completion_retries,
            "tail_action_subtree_completion_retry_pricing_events": row.get(
                "child_subtree_completion_retry_pricing_event_count"
            ),
            "tail_action_subtree_completion_retry_low_min_fill": low_min_fill_retries,
            "tail_action_subtree_completion_retry_min_harvest_min_fill": row.get(
                "child_subtree_completion_retry_min_harvest_min_fill"
            ),
            "tail_action_subtree_completion_retry_max_harvest_min_fill": row.get(
                "child_subtree_completion_retry_max_harvest_min_fill"
            ),
            "tail_action_subtree_completion_retry_found_negative": low_min_fill_found_negative,
            "tail_action_subtree_completion_retry_certified_no_negative": low_min_fill_certified,
            "tail_action_subtree_completion_retry_incomplete": row.get(
                "child_subtree_completion_retry_incomplete_count"
            ),
            "tail_action_subtree_early_branch_triggers": early_branches,
            "tail_action_subtree_no_column_triggers": no_column_chain,
            "tail_action_subtree_observed_wall_span": row.get("child_subtree_observed_wall_span"),
        }
    )
    return {
        "schema_version": "journey_tail_impact_training_row_v7",
        "source_type": "tail_action_proof_cost",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "log_file": row.get("log_file"),
        "node_id": row.get("node_id"),
        "depth": row.get("depth"),
        "cg_iter": row.get("cg_iter"),
        "time": row.get("time"),
        "task_i": row.get("no_column_branch_task_i"),
        "task_j": row.get("no_column_branch_task_j"),
        "tail_class": "tail_action_no_column" if bool(row.get("tail_action_no_column")) else "tail_action_branch",
        "tail_action": row.get("tail_action"),
        "tail_action_class": tail_action_class,
        "tail_action_reason": row.get("tail_action_reason"),
        "tail_action_productivity_class": tail_action_productivity_class,
        "feature_schema": list(TAIL_IMPACT_FEATURE_SCHEMA),
        "features": features,
        "decision_feature_schema": list(TAIL_IMPACT_FEATURE_SCHEMA),
        "decision_features": features,
        "outcome_schema": list(TAIL_IMPACT_OUTCOME_SCHEMA),
        "outcomes": outcomes,
        "label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "labels": labels,
        "outcome_label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "outcome_labels": labels,
        "raw_source": row,
    }


def _tail_action_counterfactual_training_row(row: dict[str, Any]) -> dict[str, Any]:
    labels_raw = row.get("labels") if isinstance(row.get("labels"), dict) else {}
    deltas = row.get("deltas") if isinstance(row.get("deltas"), dict) else {}
    baseline_tail = row.get("baseline_tail") if isinstance(row.get("baseline_tail"), dict) else {}
    alternative_tail = row.get("alternative_tail") if isinstance(row.get("alternative_tail"), dict) else {}
    local_improved = _float(labels_raw.get("y_local_tail_improved"))
    whole_run_improved = _float(labels_raw.get("y_whole_run_improved"))
    local_only = _float(labels_raw.get("y_local_improved_but_whole_run_not"))
    budget_dominant = _float(labels_raw.get("y_budget_dominant_improvement"))
    timeout_resolved = _float(labels_raw.get("y_timeout_resolved"))
    timeout_regression = _float(labels_raw.get("y_timeout_regression"))
    right_censored = _float(labels_raw.get("y_right_censored_counterfactual"))
    label_type = str(row.get("counterfactual_label_type") or "")
    if not label_type:
        label_type = (
            "strong_positive"
            if whole_run_improved > 0.5
            else "budget_dominant_improvement"
            if budget_dominant > 0.5
            else "local_only_hard_negative"
            if local_only > 0.5
            else "regression"
            if timeout_regression > 0.5
            else "unknown_right_censored"
            if right_censored > 0.5
            else "observed_neutral"
        )
    tail_risk = 1.0 if (
        whole_run_improved < 0.5
        and budget_dominant < 0.5
        or local_only > 0.5
        or timeout_regression > 0.5
        or (right_censored > 0.5 and budget_dominant < 0.5)
    ) else 0.0
    alternative_i, alternative_j = _pair(row.get("alternative_pair"))
    labels = _label_vector(
        {
            "y_useful_tail_reduction": whole_run_improved,
            "y_tail_risk": tail_risk,
            "y_tail_action_counterfactual": 1.0,
            "y_local_tail_improved": local_improved,
            "y_whole_run_improved": whole_run_improved,
            "y_budget_dominant_improvement": budget_dominant,
            "y_local_improved_but_whole_run_not": local_only,
            "y_timeout_resolved": timeout_resolved,
            "y_timeout_regression": timeout_regression,
            "y_right_censored_counterfactual": right_censored,
            "y_child_negative_pricing_events": max(
                0.0,
                _float(alternative_tail.get("negative_pricing_events")),
            ),
            "y_child_completion_bound_retries": max(
                0.0,
                _float(alternative_tail.get("completion_retries")),
            ),
            "y_subtree_no_column_chain": max(0.0, _float(alternative_tail.get("no_column_chain"))),
        }
    )
    features = _feature_vector(
        {
            "source_is_tail_action_counterfactual": 1.0,
            "depth": row.get("depth"),
        }
    )
    outcomes = _outcome_vector(
        {
            "branch_child_negative_pricing_events": alternative_tail.get(
                "negative_pricing_events"
            ),
            "branch_child_completion_bound_retries": alternative_tail.get(
                "completion_retries"
            ),
            "tail_action_subtree_pricing_events": alternative_tail.get("pricing_events"),
            "tail_action_subtree_negative_pricing_events": alternative_tail.get(
                "negative_pricing_events"
            ),
            "tail_action_subtree_completion_retries": alternative_tail.get(
                "completion_retries"
            ),
            "tail_action_subtree_no_column_triggers": alternative_tail.get("no_column_chain"),
            "tail_action_subtree_observed_wall_span": alternative_tail.get(
                "observed_wall_span"
            ),
            "tail_counterfactual_local_tail_cost_delta": deltas.get(
                "local_tail_cost_delta"
            ),
            "tail_counterfactual_wall_time_delta": deltas.get("wall_time_delta"),
            "tail_counterfactual_pricing_calls_delta": deltas.get("pricing_calls_delta"),
            "tail_counterfactual_exact_pricing_calls_delta": deltas.get(
                "exact_pricing_calls_delta"
            ),
            "tail_counterfactual_node_count_delta": deltas.get("node_count_delta"),
            "tail_counterfactual_solving_time_delta": deltas.get("solving_time_delta"),
            "tail_counterfactual_primal_bound_delta": deltas.get("primal_bound_delta"),
            "tail_counterfactual_dual_bound_delta": deltas.get("dual_bound_delta"),
            "tail_counterfactual_gap_delta": deltas.get("gap_delta"),
            "tail_counterfactual_completion_retry_trigger_count_delta": deltas.get(
                "completion_retry_trigger_count_delta"
            ),
            "tail_counterfactual_completion_retry_pricing_count_delta": deltas.get(
                "completion_retry_pricing_count_delta"
            ),
            "tail_counterfactual_completion_retry_work_time_proxy_delta": deltas.get(
                "completion_retry_work_time_proxy_delta"
            ),
            "tail_counterfactual_completion_retry_generated_sequences_delta": (
                deltas.get("completion_retry_generated_sequences_delta")
            ),
            "tail_counterfactual_completion_retry_evaluated_timed_trips_delta": (
                deltas.get("completion_retry_evaluated_timed_trips_delta")
            ),
            "tail_counterfactual_negative_pricing_delta": deltas.get(
                "local_negative_pricing_events_delta"
            ),
            "tail_counterfactual_completion_retry_delta": deltas.get(
                "local_completion_retries_delta"
            ),
            "tail_counterfactual_no_column_chain_delta": deltas.get(
                "local_no_column_chain_delta"
            ),
        }
    )
    return {
        "schema_version": "journey_tail_impact_training_row_v6",
        "source_type": "tail_action_counterfactual_delta",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "log_file": row.get("instance"),
        "node_id": row.get("node_id"),
        "depth": row.get("depth"),
        "cg_iter": None,
        "time": None,
        "task_i": alternative_i,
        "task_j": alternative_j,
        "tail_class": (
            "tail_action_whole_run_improved"
            if whole_run_improved > 0.5
            else "tail_action_budget_dominant_improvement"
            if budget_dominant > 0.5
            else "tail_action_local_only_hard_negative"
            if local_only > 0.5
            else "tail_action_counterfactual_right_censored"
            if right_censored > 0.5
            else "tail_action_counterfactual"
        ),
        "baseline_pair": row.get("baseline_pair"),
        "alternative_pair": row.get("alternative_pair"),
        "baseline_status": row.get("baseline_status"),
        "alternative_status": row.get("alternative_status"),
        "counterfactual_label_type": label_type,
        "outcome_label_type": label_type,
        "baseline_tail_cost": baseline_tail.get("tail_cost"),
        "alternative_tail_cost": alternative_tail.get("tail_cost"),
        "feature_schema": list(TAIL_IMPACT_FEATURE_SCHEMA),
        "features": features,
        "decision_feature_schema": list(TAIL_IMPACT_FEATURE_SCHEMA),
        "decision_features": features,
        "outcome_schema": list(TAIL_IMPACT_OUTCOME_SCHEMA),
        "outcomes": outcomes,
        "label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "labels": labels,
        "outcome_label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "outcome_labels": labels,
        "raw_source": row,
    }


def _late_negative_training_row(row: dict[str, Any]) -> dict[str, Any]:
    has_true_negative = bool(row.get("has_true_negative"))
    has_weak_filtered = bool(row.get("has_weak_filtered"))
    active_changed = _float(row.get("active_changed_task_set_count"))
    inactive_changed = _float(row.get("inactive_changed_task_set_count"))
    weak_filtered = _float(row.get("weak_negative_journeys_filtered"))
    labels = _label_vector(
        {
            "y_useful_tail_reduction": 0.0,
            "y_tail_risk": 1.0,
            "y_weak_negative_filtered": 1.0 if has_weak_filtered else 0.0,
            "y_negative_chain_continues": 1.0 if has_true_negative else 0.0,
            "y_active_touch": 1.0 if active_changed > 0.0 else 0.0,
            "y_inactive_only": 1.0 if inactive_changed > 0.0 and active_changed <= 0.0 else 0.0,
            "y_late_true_negative": 1.0 if has_true_negative else 0.0,
            "y_late_active_support_changing": 1.0 if active_changed > 0.0 else 0.0,
            "y_late_inactive_only": 1.0 if inactive_changed > 0.0 and active_changed <= 0.0 else 0.0,
            "y_late_weak_filtered": 1.0 if has_weak_filtered else 0.0,
        }
    )
    features = _feature_vector(
        {
            "source_is_late_negative": 1.0,
            "depth": row.get("depth"),
            "time": row.get("time"),
            "cg_iter": row.get("cg_iter"),
            "pricing_time_limit": row.get("pricing_time_limit"),
            "profile_generation_time": row.get("profile_generation_time"),
            "profile_dp_time": row.get("profile_dp_time"),
            "dp_state_count": row.get("dp_state_count"),
            "negative_journeys": row.get("negative_journeys"),
            "selected_trips": row.get("selected_trips"),
            "weak_negative_journeys_filtered": weak_filtered,
            "profile_weak_filtered_materialized_count": row.get(
                "profile_weak_filtered_materialized_count"
            ),
            "weak_best_rough_rc": row.get("profile_weak_filtered_best_rough_rc"),
            "weak_best_true_rc": row.get("profile_weak_filtered_best_true_rc"),
            "weak_max_true_minus_rough": row.get("profile_weak_filtered_max_true_minus_rough"),
            "late_has_true_negative": 1.0 if has_true_negative else 0.0,
            "late_has_weak_filtered": 1.0 if has_weak_filtered else 0.0,
            "late_active_changed_task_sets": active_changed,
            "late_inactive_changed_task_sets": inactive_changed,
            "late_added_journeys": row.get("added_journeys"),
            "late_new_task_sets": row.get("new_task_set_count"),
            "late_replacement_task_sets": row.get("replacement_task_set_count"),
        }
    )
    outcomes = _outcome_vector({})
    return {
        "schema_version": "journey_tail_impact_training_row_v3",
        "source_type": "late_negative_tail",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "log_file": row.get("log_file"),
        "node_id": row.get("node_id"),
        "depth": row.get("depth"),
        "cg_iter": row.get("cg_iter"),
        "time": row.get("time"),
        "task_i": None,
        "task_j": None,
        "tail_class": row.get("tail_class"),
        "feature_schema": list(TAIL_IMPACT_FEATURE_SCHEMA),
        "features": features,
        "decision_feature_schema": list(TAIL_IMPACT_FEATURE_SCHEMA),
        "decision_features": features,
        "outcome_schema": list(TAIL_IMPACT_OUTCOME_SCHEMA),
        "outcomes": outcomes,
        "label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "labels": labels,
        "outcome_label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "outcome_labels": labels,
        "raw_source": row,
    }


def build_tail_impact(
    weak_inputs: list[Path],
    branch_inputs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    tail_action_inputs: list[Path] | None = None,
    tail_action_counterfactual_inputs: list[Path] | None = None,
    late_negative_inputs: list[Path] | None = None,
) -> dict[str, Any]:
    weak_rows = _load_weak_rows(weak_inputs)
    branch_rows = _load_branch_training_rows(branch_inputs)
    tail_action_rows = _load_tail_action_rows(tail_action_inputs or [])
    tail_action_counterfactual_rows = _load_tail_action_counterfactual_rows(
        tail_action_counterfactual_inputs or []
    )
    late_negative_rows = _load_late_negative_rows(late_negative_inputs or [])
    rows = [_weak_training_row(row) for row in weak_rows]
    rows.extend(_branch_training_row(row) for row in branch_rows)
    rows.extend(_tail_action_training_row(row) for row in tail_action_rows)
    rows.extend(_tail_action_counterfactual_training_row(row) for row in tail_action_counterfactual_rows)
    rows.extend(_late_negative_training_row(row) for row in late_negative_rows)
    raw_training_row_count = len(rows)
    duplicate_context_action_count = _duplicate_context_action_count(rows)
    source_counts = Counter(str(row.get("source_type") or "") for row in rows)
    tail_class_counts = Counter(str(row.get("tail_class") or "") for row in rows)
    tail_action_class_counts = Counter(
        str(row.get("tail_action_class") or "")
        for row in rows
        if row.get("tail_action_class")
    )
    tail_action_productivity_class_counts = Counter(
        str(row.get("tail_action_productivity_class") or "")
        for row in rows
        if row.get("tail_action_productivity_class")
    )
    counterfactual_label_type_counts = Counter(
        str(row.get("counterfactual_label_type") or "")
        for row in rows
        if row.get("source_type") == "tail_action_counterfactual_delta"
    )
    label_positive_counts = {
        name: int(sum(1 for row in rows if _float(row.get("labels", {}).get(name)) > 0.5))
        for name in TAIL_IMPACT_LABEL_SCHEMA
    }
    useful_positive_count = int(label_positive_counts["y_useful_tail_reduction"])
    tail_risk_positive_count = int(label_positive_counts["y_tail_risk"])
    whole_run_positive_rows = [
        row
        for row in rows
        if _float(row.get("labels", {}).get("y_whole_run_improved")) > 0.5
    ]
    whole_run_positive_count = len(whole_run_positive_rows)
    whole_run_positive_context_count = len(
        {_row_context_key(row) for row in whole_run_positive_rows}
    )
    whole_run_positive_instance_count = len(
        {str(row.get("log_file") or "") for row in whole_run_positive_rows}
    )
    whole_run_positive_time_window_family_count = len(
        {
            family
            for family in (_time_window_family(row.get("log_file")) for row in whole_run_positive_rows)
            if family
        }
    )
    local_only_hard_negative_count = int(
        label_positive_counts["y_local_improved_but_whole_run_not"]
    )
    positive_holdout_context_count = int(sum(1 for row in rows if _has_holdout_positive(row)))
    strict_training_requirements = {
        "whole_run_positive_min": 5,
        "distinct_parent_context_min": 3,
        "distinct_instance_min": 3,
        "distinct_time_window_family_min": 2,
        "local_only_hard_negative_at_least_positive": True,
        "positive_holdout_context_min": 1,
    }
    strict_tail_training_ready = bool(
        whole_run_positive_count >= strict_training_requirements["whole_run_positive_min"]
        and whole_run_positive_context_count
        >= strict_training_requirements["distinct_parent_context_min"]
        and whole_run_positive_instance_count
        >= strict_training_requirements["distinct_instance_min"]
        and whole_run_positive_time_window_family_count
        >= strict_training_requirements["distinct_time_window_family_min"]
        and local_only_hard_negative_count >= whole_run_positive_count
        and positive_holdout_context_count
        >= strict_training_requirements["positive_holdout_context_min"]
    )
    minimal_tail_signal_ready = bool(useful_positive_count > 0 and tail_risk_positive_count > 0)
    regression_totals = {
        "child_negative_pricing_events": int(
            sum(_float(row.get("labels", {}).get("y_child_negative_pricing_events")) for row in rows)
        ),
        "child_completion_bound_retries": int(
            sum(_float(row.get("labels", {}).get("y_child_completion_bound_retries")) for row in rows)
        ),
        "child_early_branch_triggers": int(
            sum(_float(row.get("labels", {}).get("y_child_early_branch_triggers")) for row in rows)
        ),
        "child_unstarted": int(
            sum(_float(row.get("labels", {}).get("y_child_unstarted")) for row in rows)
        ),
        "subtree_no_column_chain": int(
            sum(_float(row.get("labels", {}).get("y_subtree_no_column_chain")) for row in rows)
        ),
        "late_true_negative": int(
            sum(_float(row.get("labels", {}).get("y_late_true_negative")) for row in rows)
        ),
        "late_active_support_changing": int(
            sum(_float(row.get("labels", {}).get("y_late_active_support_changing")) for row in rows)
        ),
        "late_inactive_only": int(
            sum(_float(row.get("labels", {}).get("y_late_inactive_only")) for row in rows)
        ),
        "late_weak_filtered": int(
            sum(_float(row.get("labels", {}).get("y_late_weak_filtered")) for row in rows)
        ),
        "tail_action_counterfactual": int(
            sum(
                _float(row.get("labels", {}).get("y_tail_action_counterfactual"))
                for row in rows
            )
        ),
        "local_tail_improved": int(
            sum(_float(row.get("labels", {}).get("y_local_tail_improved")) for row in rows)
        ),
        "whole_run_improved": int(
            sum(_float(row.get("labels", {}).get("y_whole_run_improved")) for row in rows)
        ),
        "budget_dominant_improvement": int(
            sum(
                _float(row.get("labels", {}).get("y_budget_dominant_improvement"))
                for row in rows
            )
        ),
        "local_improved_but_whole_run_not": int(
            sum(
                _float(row.get("labels", {}).get("y_local_improved_but_whole_run_not"))
                for row in rows
            )
        ),
        "right_censored_counterfactual": int(
            sum(
                _float(row.get("labels", {}).get("y_right_censored_counterfactual"))
                for row in rows
            )
        ),
        "tail_min_fill_completion_retry": int(
            sum(
                _float(row.get("labels", {}).get("y_tail_min_fill_completion_retry"))
                for row in rows
            )
        ),
        "tail_min_fill_found_negative": int(
            sum(
                _float(row.get("labels", {}).get("y_tail_min_fill_found_negative"))
                for row in rows
            )
        ),
        "tail_min_fill_certified_no_negative": int(
            sum(
                _float(row.get("labels", {}).get("y_tail_min_fill_certified_no_negative"))
                for row in rows
            )
        ),
    }
    summary = {
        "schema_version": "journey_tail_impact_training_rows_v7",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "stage4_candidate_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "weak_input_paths": [str(path) for path in weak_inputs],
        "branch_input_paths": [str(path) for path in branch_inputs],
        "tail_action_input_paths": [str(path) for path in (tail_action_inputs or [])],
        "tail_action_counterfactual_input_paths": [
            str(path) for path in (tail_action_counterfactual_inputs or [])
        ],
        "late_negative_input_paths": [str(path) for path in (late_negative_inputs or [])],
        "feature_schema": list(TAIL_IMPACT_FEATURE_SCHEMA),
        "decision_feature_schema": list(TAIL_IMPACT_FEATURE_SCHEMA),
        "outcome_schema": list(TAIL_IMPACT_OUTCOME_SCHEMA),
        "label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "outcome_label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "training_row_count": len(rows),
        "raw_training_row_count": raw_training_row_count,
        "deduplicated_row_count": 0,
        "duplicate_context_action_count": duplicate_context_action_count,
        "weak_row_count": len(weak_rows),
        "branch_row_count": len(branch_rows),
        "tail_action_row_count": len(tail_action_rows),
        "tail_action_counterfactual_row_count": len(tail_action_counterfactual_rows),
        "late_negative_row_count": len(late_negative_rows),
        "source_counts": dict(sorted(source_counts.items())),
        "tail_class_counts": dict(sorted(tail_class_counts.items())),
        "tail_action_class_counts": dict(sorted(tail_action_class_counts.items())),
        "tail_action_productivity_class_counts": dict(
            sorted(tail_action_productivity_class_counts.items())
        ),
        "counterfactual_label_type_counts": dict(
            sorted(counterfactual_label_type_counts.items())
        ),
        "label_positive_counts": label_positive_counts,
        "regression_label_totals": regression_totals,
        "hard_negative_catalog_ready": bool(rows),
        "minimal_tail_signal_ready": minimal_tail_signal_ready,
        "strict_tail_training_requirements": strict_training_requirements,
        "whole_run_positive_context_count": whole_run_positive_context_count,
        "whole_run_positive_instance_count": whole_run_positive_instance_count,
        "whole_run_positive_time_window_family_count": (
            whole_run_positive_time_window_family_count
        ),
        "local_only_hard_negative_count": local_only_hard_negative_count,
        "positive_holdout_context_count": positive_holdout_context_count,
        "strict_tail_training_ready": strict_tail_training_ready,
        "contrastive_tail_training_ready": strict_tail_training_ready,
        "tail_label_training_ready": strict_tail_training_ready,
        "interpretation": (
            "Rows are suitable as an offline hard-negative catalog for GAT "
            "tail-risk / branch-impact experiments. Online decision features are "
            "kept separate from outcome labels to avoid post-action leakage. "
            "Strict tail training requires multiple whole-run positive contexts, "
            "matching hard negatives, and a positive holdout context. These rows "
            "are not a safe source, pricing oracle, branch oracle, official bound "
            "source, or certificate source."
        ),
        "rows": rows,
    }
    write_outputs(summary, output_dir, report)
    return summary


def write_outputs(summary: dict[str, Any], output_dir: Path, report: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = list(summary.get("rows", []))
    summary_without_rows = dict(summary)
    summary_without_rows.pop("rows", None)
    (output_dir / "summary.json").write_text(
        json.dumps(summary_without_rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "tail_impact_training_rows.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_render_report(summary_without_rows, output_dir), encoding="utf-8")


def _dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for row in rows:
        key = (
            row.get("source_type"),
            row.get("log_file"),
            row.get("node_id"),
            row.get("depth"),
            row.get("cg_iter"),
            row.get("time"),
            row.get("task_i"),
            row.get("task_j"),
            row.get("tail_class"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _render_report(summary: dict[str, Any], output_dir: Path) -> str:
    lines = [
        "# Journey Tail-Impact Training Rows",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "合成 weak-negative tail、branch-impact、tail-action proof-cost、tail-action counterfactual delta 与 late-negative tail 离线审计 row，为后续 GAT 学习“哪些候选会制造 proof tail、哪些分支会缩短 proof tail、哪些 true-negative 真的改变 active support”提供统一训练接口。该脚本只读现有审计产物，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "journey_tail_impact_training_rows = current",
        f"output_dir = {output_dir}",
        f"training_row_count = {summary.get('training_row_count')}",
        f"raw_training_row_count = {summary.get('raw_training_row_count')}",
        f"deduplicated_row_count = {summary.get('deduplicated_row_count')}",
        f"weak_row_count = {summary.get('weak_row_count')}",
        f"branch_row_count = {summary.get('branch_row_count')}",
        f"tail_action_row_count = {summary.get('tail_action_row_count')}",
        "tail_action_counterfactual_row_count = "
        f"{summary.get('tail_action_counterfactual_row_count')}",
        f"late_negative_row_count = {summary.get('late_negative_row_count')}",
        f"source_counts = {summary.get('source_counts')}",
        f"tail_class_counts = {summary.get('tail_class_counts')}",
        f"tail_action_class_counts = {summary.get('tail_action_class_counts')}",
        "tail_action_productivity_class_counts = "
        f"{summary.get('tail_action_productivity_class_counts')}",
        f"counterfactual_label_type_counts = {summary.get('counterfactual_label_type_counts')}",
        f"label_positive_counts = {summary.get('label_positive_counts')}",
        f"regression_label_totals = {summary.get('regression_label_totals')}",
        f"hard_negative_catalog_ready = {str(summary.get('hard_negative_catalog_ready')).lower()}",
        f"contrastive_tail_training_ready = {str(summary.get('contrastive_tail_training_ready')).lower()}",
        f"tail_label_training_ready = {str(summary.get('tail_label_training_ready')).lower()}",
        "production_ready = false",
        "stage4_candidate_ready = false",
        "certificate_effect = false",
        "official_bound_effect = false",
        "```",
        "",
        "## 解释",
        "",
        "这一步没有让 20 规模求解变快，也不改变 solver。它把当前失败机制转成统一监督信号：weak-negative row 是 rough/profile 负列信号失效的负例，branch-impact row 是分支后 active-support、negative-chain、completion-bound tail 的结果标签，tail-action row 记录 early branch 后子树的 proof-cost 和 no-column 链条，tail-action counterfactual delta row 区分 local-only improvement 与 whole-run improvement，late-negative row 则区分 true negative 是 active-support-changing 还是 inactive-only。",
        "",
        "如果 `contrastive_tail_training_ready=false`，这批数据只能作为 hard-negative catalog，不能单独训练“选好分支/好候选”的 GAT；下一步必须补能减少 tail 的正例。不能把这些 row 当作剪枝依据或 no-negative certificate。",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weak-input", nargs="*", type=Path, default=[])
    parser.add_argument("--branch-input", nargs="*", type=Path, default=[])
    parser.add_argument("--tail-action-input", nargs="*", type=Path, default=[])
    parser.add_argument("--tail-action-counterfactual-input", nargs="*", type=Path, default=[])
    parser.add_argument("--late-negative-input", nargs="*", type=Path, default=[])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = build_tail_impact(
        args.weak_input,
        args.branch_input,
        args.output_dir,
        args.report,
        tail_action_inputs=args.tail_action_input,
        tail_action_counterfactual_inputs=args.tail_action_counterfactual_input,
        late_negative_inputs=args.late_negative_input,
    )
    printable = dict(summary)
    printable.pop("rows", None)
    print(json.dumps(printable, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
