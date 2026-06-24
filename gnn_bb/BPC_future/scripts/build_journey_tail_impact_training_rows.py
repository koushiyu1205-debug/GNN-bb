#!/usr/bin/env python3
"""Build audit-only Journey tail-impact training rows.

This script fuses diagnostic sources:

* weak rough-negative pricing rows that were filtered by true-RC materialization;
* branch-impact rows that describe whether a branch reduces or moves proof tail.
* tail-action proof-cost rows;
* late true-negative / weak-filtered pricing tail rows.

It is intentionally offline.  It reads existing audit artifacts only and does
not run BPC, pricing, RMP, or produce certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter
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
    "branch_child_negative_pricing_events",
    "branch_child_completion_bound_retries",
    "branch_child_early_branch_triggers",
    "tail_action_no_column",
    "tail_action_pool_max_child_width",
    "tail_action_pool_total_child_width",
    "tail_action_pool_balance_gap",
    "tail_action_direct_started_count",
    "tail_action_direct_unstarted_count",
    "tail_action_subtree_node_count",
    "tail_action_subtree_pricing_events",
    "tail_action_subtree_negative_pricing_events",
    "tail_action_subtree_completion_retries",
    "tail_action_subtree_early_branch_triggers",
    "tail_action_subtree_no_column_triggers",
    "tail_action_subtree_observed_wall_span",
    "late_has_true_negative",
    "late_has_weak_filtered",
    "late_active_changed_task_sets",
    "late_inactive_changed_task_sets",
    "late_added_journeys",
    "late_new_task_sets",
    "late_replacement_task_sets",
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
    "y_child_unstarted",
    "y_subtree_no_column_chain",
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
        "label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "labels": labels,
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
        "label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "labels": labels,
        "raw_source": row,
    }


def _tail_action_training_row(row: dict[str, Any]) -> dict[str, Any]:
    negative_events = _float(row.get("child_subtree_negative_pricing_event_count"))
    completion_retries = _float(row.get("child_subtree_completion_retry_count"))
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
            "tail_action_direct_started_count": row.get("child_direct_started_count"),
            "tail_action_direct_unstarted_count": row.get("child_direct_unstarted_count"),
            "tail_action_subtree_node_count": row.get("child_subtree_node_count"),
            "tail_action_subtree_pricing_events": row.get("child_subtree_pricing_event_count"),
            "tail_action_subtree_negative_pricing_events": negative_events,
            "tail_action_subtree_completion_retries": completion_retries,
            "tail_action_subtree_early_branch_triggers": early_branches,
            "tail_action_subtree_no_column_triggers": no_column_chain,
            "tail_action_subtree_observed_wall_span": row.get("child_subtree_observed_wall_span"),
        }
    )
    return {
        "schema_version": "journey_tail_impact_training_row_v2",
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
        "feature_schema": list(TAIL_IMPACT_FEATURE_SCHEMA),
        "features": features,
        "label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "labels": labels,
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
        "label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "labels": labels,
        "raw_source": row,
    }


def build_tail_impact(
    weak_inputs: list[Path],
    branch_inputs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    tail_action_inputs: list[Path] | None = None,
    late_negative_inputs: list[Path] | None = None,
) -> dict[str, Any]:
    weak_rows = _load_weak_rows(weak_inputs)
    branch_rows = _load_branch_training_rows(branch_inputs)
    tail_action_rows = _load_tail_action_rows(tail_action_inputs or [])
    late_negative_rows = _load_late_negative_rows(late_negative_inputs or [])
    rows = [_weak_training_row(row) for row in weak_rows]
    rows.extend(_branch_training_row(row) for row in branch_rows)
    rows.extend(_tail_action_training_row(row) for row in tail_action_rows)
    rows.extend(_late_negative_training_row(row) for row in late_negative_rows)
    raw_training_row_count = len(rows)
    rows = _dedupe_rows(rows)
    source_counts = Counter(str(row.get("source_type") or "") for row in rows)
    tail_class_counts = Counter(str(row.get("tail_class") or "") for row in rows)
    label_positive_counts = {
        name: int(sum(1 for row in rows if _float(row.get("labels", {}).get(name)) > 0.5))
        for name in TAIL_IMPACT_LABEL_SCHEMA
    }
    useful_positive_count = int(label_positive_counts["y_useful_tail_reduction"])
    tail_risk_positive_count = int(label_positive_counts["y_tail_risk"])
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
    }
    summary = {
        "schema_version": "journey_tail_impact_training_rows_v3",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "stage4_candidate_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "weak_input_paths": [str(path) for path in weak_inputs],
        "branch_input_paths": [str(path) for path in branch_inputs],
        "tail_action_input_paths": [str(path) for path in (tail_action_inputs or [])],
        "late_negative_input_paths": [str(path) for path in (late_negative_inputs or [])],
        "feature_schema": list(TAIL_IMPACT_FEATURE_SCHEMA),
        "label_schema": list(TAIL_IMPACT_LABEL_SCHEMA),
        "training_row_count": len(rows),
        "raw_training_row_count": raw_training_row_count,
        "deduplicated_row_count": raw_training_row_count - len(rows),
        "weak_row_count": len(weak_rows),
        "branch_row_count": len(branch_rows),
        "tail_action_row_count": len(tail_action_rows),
        "late_negative_row_count": len(late_negative_rows),
        "source_counts": dict(sorted(source_counts.items())),
        "tail_class_counts": dict(sorted(tail_class_counts.items())),
        "label_positive_counts": label_positive_counts,
        "regression_label_totals": regression_totals,
        "hard_negative_catalog_ready": bool(rows),
        "contrastive_tail_training_ready": bool(
            useful_positive_count > 0 and tail_risk_positive_count > 0
        ),
        "tail_label_training_ready": bool(
            useful_positive_count > 0 and tail_risk_positive_count > 0
        ),
        "interpretation": (
            "Rows are suitable as an offline hard-negative catalog for GAT "
            "tail-risk / branch-impact experiments.  Contrastive tail training "
            "requires at least one useful tail-reduction positive row.  These rows "
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
        "日期：2026-06-23",
        "",
        "## 目的",
        "",
        "合成 weak-negative tail、branch-impact、tail-action proof-cost 与 late-negative tail 离线审计 row，为后续 GAT 学习“哪些候选会制造 proof tail、哪些分支会缩短 proof tail、哪些 true-negative 真的改变 active support”提供统一训练接口。该脚本只读现有审计产物，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
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
        f"late_negative_row_count = {summary.get('late_negative_row_count')}",
        f"source_counts = {summary.get('source_counts')}",
        f"tail_class_counts = {summary.get('tail_class_counts')}",
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
        "这一步没有让 20 规模求解变快，也不改变 solver。它把当前失败机制转成统一监督信号：weak-negative row 是 rough/profile 负列信号失效的负例，branch-impact row 是分支后 active-support、negative-chain、completion-bound tail 的结果标签，tail-action row 记录 early branch 后子树的 proof-cost 和 no-column 链条，late-negative row 则区分 true negative 是 active-support-changing 还是 inactive-only。",
        "",
        "如果 `contrastive_tail_training_ready=false`，这批数据只能作为 hard-negative catalog，不能单独训练“选好分支/好候选”的 GAT；下一步必须补能减少 tail 的正例。不能把这些 row 当作剪枝依据或 no-negative certificate。",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weak-input", nargs="*", type=Path, default=[])
    parser.add_argument("--branch-input", nargs="*", type=Path, default=[])
    parser.add_argument("--tail-action-input", nargs="*", type=Path, default=[])
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
        late_negative_inputs=args.late_negative_input,
    )
    printable = dict(summary)
    printable.pop("rows", None)
    print(json.dumps(printable, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
