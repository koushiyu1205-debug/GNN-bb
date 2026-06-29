#!/usr/bin/env python3
"""Build GAT samples for the auxiliary Journey tree-policy head.

The input is ``tree_policy_event_rows.jsonl``.  Samples produced here set the
legacy branch-priority/wall-time loss weights to zero and only train
``y_tree_policy`` when used with ``train_gat_branch_action_sanity.py``.
When ``--include-walltime-labels`` is explicitly enabled, strict tree-policy
rows carrying full-replay capped wall-time gain also populate the legacy
branch-priority and wall-time regression heads.

This is offline and diagnostic-only: it does not run BPC, pricing, RMP, or
certificates, and it does not make pruning decisions.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.learning.graph_builder import FutureGraphBuilder
from BPC_future.scripts.audit_journey_branch_impact import BRANCH_IMPACT_FEATURE_SCHEMA
from BPC_future.scripts.build_gat_branch_action_sanity_dataset import (
    BRANCH_ACTION_CONTEXT_FEATURE_SCHEMA,
    BRANCH_ACTION_LABEL_SCHEMA,
)


DEFAULT_OUTPUT_DIR = Path("BPC_future/data/gat_branch_action_sanity/v487_tree_policy_event_dataset_20260627")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/20260627_bpc_future_gat_tree_policy_event_dataset_zh.md"
)


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if path.is_dir():
        path = path / "tree_policy_event_rows.jsonl"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            normalized = _normalize_input_row(row)
            if normalized is not None:
                yield normalized


def _instance_from_log_file(log_file: Any) -> str:
    text = str(log_file or "").replace("\\", "/")
    marker = "/logs/"
    if marker in text:
        return text.split(marker, 1)[1].removesuffix(".jsonl")
    return text.removesuffix(".jsonl")


def _sum_child_time_span(row: dict[str, Any]) -> float:
    children = row.get("children")
    if not isinstance(children, list):
        return 0.0
    total = 0.0
    for child in children:
        if not isinstance(child, dict):
            continue
        total += max(0.0, _float(child.get("time_span")))
    return float(total)


def _min_child_time_to_certificate(row: dict[str, Any]) -> float:
    children = row.get("children")
    if not isinstance(children, list):
        return 0.0
    values: list[float] = []
    for child in children:
        if not isinstance(child, dict):
            continue
        value = child.get("time_to_first_certificate")
        if value in (None, ""):
            continue
        parsed = _float(value, default=-1.0)
        if parsed >= 0.0:
            values.append(float(parsed))
    return min(values) if values else 0.0


def _normalize_branch_impact_row(row: dict[str, Any]) -> dict[str, Any] | None:
    schema_version = str(row.get("schema_version") or "")
    labels = row.get("branch_labels") if isinstance(row.get("branch_labels"), dict) else {}
    looks_like_branch_impact = bool(labels) and row.get("branch_node_id") is not None
    if schema_version not in {
        "journey_branch_impact_row_v1",
        "journey_branch_impact_training_row_v1",
    } and not looks_like_branch_impact:
        return None
    tail_class = str(row.get("tail_class") or "")
    completion_retries = _float(labels.get("y_child_completion_bound_retries"))
    exact_events = _float(labels.get("y_child_exact_pricing_events"))
    negative_events = _float(labels.get("y_child_negative_pricing_events"))
    is_completion_tail = (
        tail_class == "completion_bound_tail"
        or _float(labels.get("y_completion_bound_tail")) > 0.0
        or completion_retries > 0.0
    )
    if not is_completion_tail:
        return None
    pair = _pair([row.get("task_i"), row.get("task_j")])
    if pair is None:
        return None
    instance = row.get("instance") or _instance_from_log_file(row.get("log_file"))
    branch_features = row.get("branch_feature_vector")
    if not isinstance(branch_features, list):
        branch_features = row.get("branch_features")
    proof_cpu = _sum_child_time_span(row)
    if proof_cpu <= 0.0:
        proof_cpu = max(0.0, completion_retries)
    time_to_certificate = _min_child_time_to_certificate(row)
    if time_to_certificate <= 0.0:
        time_to_certificate = proof_cpu
    loss_weight = min(0.5, max(0.10, completion_retries / 20.0))
    normalized = dict(row)
    normalized.update(
        {
            "schema_version": "tree_policy_event_from_branch_impact_v1",
            "instance": str(instance),
            "node_id": row.get("branch_node_id", row.get("node_id")),
            "selected_pair": list(pair),
            "baseline_pair": row.get("baseline_pair") or [],
            "branch_feature_vector": branch_features,
            "candidate_count": row.get("candidate_count"),
            "eligible_count": row.get("eligible_count", row.get("candidate_count")),
            "policy_run": "v562_retry_cap_branch_impact",
            "tree_policy_label_type": "proof_tail_right_censored_hard_negative",
            "y_tree_policy_positive": 0.0,
            "y_tree_policy_hard_negative": 1.0,
            "event_loss_weight": float(loss_weight),
            "child_proof_cpu": float(proof_cpu),
            "child_proof_cpu_loss_weight": 1.0,
            "child_time_to_certificate": float(time_to_certificate),
            "time_to_certificate_loss_weight": 1.0 if time_to_certificate > 0.0 else 0.0,
            "right_censored": bool(row.get("right_censored", True)),
            "proof_tail_risk": True,
            "proof_tail_completion_retry_count": float(completion_retries),
            "proof_tail_exact_pricing_event_count": float(exact_events),
            "proof_tail_negative_pricing_event_count": float(negative_events),
        }
    )
    return normalized


def _normalize_input_row(row: dict[str, Any]) -> dict[str, Any] | None:
    normalized = _normalize_branch_impact_row(row)
    if normalized is not None:
        return normalized
    return row


def _float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return float(parsed)


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _pair(value: Any) -> tuple[int, int] | None:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        left = _int(value[0], -1)
        right = _int(value[1], -1)
        if left > 0 and right > 0 and left != right:
            return tuple(sorted((left, right)))
    return None


def _candidate_for_selected(row: dict[str, Any]) -> dict[str, Any]:
    selected = _pair(row.get("selected_pair"))
    if selected is None:
        return {}
    for key in ("top", "priority_top"):
        candidates = row.get(key)
        if not isinstance(candidates, list):
            continue
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            pair = _pair([candidate.get("task_i"), candidate.get("task_j")])
            if pair == selected:
                return dict(candidate)
    return {}


def _raw(row: dict[str, Any]) -> dict[str, Any]:
    raw = _candidate_for_selected(row)
    selected = row.get("selected_raw")
    if isinstance(selected, dict):
        raw.update({key: value for key, value in selected.items() if value is not None})
    return raw


def _branch_rank(row: dict[str, Any], key: str) -> float:
    selected = _pair(row.get("selected_pair"))
    if selected is None:
        return 0.0
    raw_rows = row.get(key)
    if not isinstance(raw_rows, list):
        return 0.0
    for index, candidate in enumerate(raw_rows, start=1):
        if not isinstance(candidate, dict):
            continue
        pair = _pair([candidate.get("task_i"), candidate.get("task_j")])
        if pair == selected:
            return float(index)
    return 0.0


def _branch_feature_vector(row: dict[str, Any]) -> list[float]:
    vector = row.get("branch_feature_vector")
    if not isinstance(vector, list):
        vector = row.get("branch_features")
    if isinstance(vector, list) and len(vector) == len(BRANCH_IMPACT_FEATURE_SCHEMA):
        return [_float(value) for value in vector]
    raw = _raw(row)
    vector = raw.get("branch_feature_vector")
    if isinstance(vector, list) and len(vector) == len(BRANCH_IMPACT_FEATURE_SCHEMA):
        return [_float(value) for value in vector]
    incumbent_relation = raw.get("incumbent_relation")
    relation_known = 0.0 if incumbent_relation is None else 1.0
    relation_same = 1.0 if incumbent_relation is True else 0.0
    values = {
        "depth": _float(row.get("depth")),
        "candidate_count": _float(row.get("candidate_count")),
        "eligible_count": _float(row.get("eligible_count")),
        "has_candidate_log": 1.0,
        "branch_rank_in_top": 0.0,
        "branch_rank_in_priority_top": 0.0,
        "same_mass": _float(raw.get("same_mass")),
        "fractionality": _float(raw.get("fractionality")),
        "support_count": _float(raw.get("support_count")),
        "incumbent_relation_known": relation_known,
        "incumbent_relation_same": relation_same,
        "incumbent_disagreement": _float(raw.get("incumbent_disagreement")),
        "pool_same_allowed": _float(raw.get("pool_same_allowed")),
        "pool_separate_allowed": _float(raw.get("pool_separate_allowed")),
        "pool_max_child_width": _float(raw.get("pool_max_child_width")),
        "pool_total_child_width": _float(raw.get("pool_total_child_width")),
        "pool_balance_gap": _float(raw.get("pool_balance_gap")),
    }
    return [float(values.get(name, 0.0)) for name in BRANCH_IMPACT_FEATURE_SCHEMA]


def _context_feature_vector(row: dict[str, Any]) -> list[float]:
    baseline_pair = _pair(row.get("baseline_pair")) or (0, 0)
    selected_pair = _pair(row.get("selected_pair")) or (0, 0)
    return [
        _float(row.get("node_id")),
        _float(row.get("depth")),
        _float(row.get("branch_time")),
        _float(row.get("candidate_count")),
        _float(row.get("eligible_count")),
        0.0,
        0.0,
        float(baseline_pair[0]),
        float(baseline_pair[1]),
        float(selected_pair[0]),
        float(selected_pair[1]),
    ]


def _walltime_gain_from_row(row: dict[str, Any]) -> float | None:
    for key in ("capped_wall_time_gain", "walltime_gain"):
        parsed = _optional_float(row.get(key))
        if parsed is not None:
            return parsed
    baseline = _optional_float(row.get("baseline_wall_time"))
    alternative = _optional_float(row.get("alternative_wall_time"))
    if baseline is not None and alternative is not None:
        return float(baseline - alternative)
    return None


def _tree_policy_action_labels(
    row: dict[str, Any],
    *,
    include_walltime_labels: bool,
    tree_label: float,
    target_wall: float,
    wall_cap: float,
    min_wall_improvement: float,
    min_wall_regression: float,
    max_delta_weight: float,
) -> dict[str, float]:
    gain = _walltime_gain_from_row(row)
    row_labels = row.get("labels")
    if not isinstance(row_labels, dict):
        row_labels = {}
    row_deltas = row.get("deltas")
    if not isinstance(row_deltas, dict):
        row_deltas = {}

    def label_value(*names: str) -> float:
        for name in names:
            if name in row:
                return _float(row.get(name))
            if name in row_labels:
                return _float(row_labels.get(name))
            if name in row_deltas:
                return _float(row_deltas.get(name))
        return 0.0

    positive = bool(tree_label > 0.5)
    label_type = str(row.get("tree_policy_label_type") or "")
    strict_label = label_type in {
        "strong_positive",
        "controlled_replay_positive",
    }
    hard_negative_label = label_type in {
        "hard_negative",
        "controlled_replay_hard_negative",
    }
    main_weight = 0.0
    branch_positive = 0.0
    regression = 0.0
    if include_walltime_labels and gain is not None:
        magnitude = min(
            float(max_delta_weight),
            max(1.0, abs(float(gain)) / max(float(min_wall_improvement), 1.0)),
        )
        if positive and strict_label and gain >= float(min_wall_improvement):
            branch_positive = 1.0
            main_weight = magnitude
        elif hard_negative_label and gain <= -float(min_wall_regression):
            regression = 1.0
            main_weight = magnitude
    baseline_wall = _optional_float(row.get("baseline_wall_time"))
    alternative_wall = _optional_float(row.get("alternative_wall_time"))
    target_crossing = bool(
        alternative_wall is not None
        and baseline_wall is not None
        and alternative_wall <= float(target_wall)
        and baseline_wall > float(target_wall)
    )
    if gain is None:
        gain = 0.0
    delta = -float(gain)
    child_proof_cpu = max(0.0, _float(row.get("child_proof_cpu")))
    child_time_to_certificate = max(0.0, _float(row.get("child_time_to_certificate")))
    gap_improvement = label_value("y_gap_improvement", "gap_improvement")
    primal_improvement = label_value("y_primal_improvement", "primal_improvement")
    dual_bound_gain = label_value("y_dual_bound_gain", "dual_bound_gain")
    fathom_gain = label_value("y_fathom_gain", "fathom_gain")
    branch_count_delta = label_value("y_branch_count_delta", "branch_count_delta")
    completion_retry_gain = label_value(
        "y_completion_bound_retry_gain",
        "y_completion_bound_final_judge_retry_gain",
        "completion_bound_retry_gain",
        "completion_bound_final_judge_retry_gain",
    )
    structural_weight = 1.0 if any(
        abs(float(value)) > 0.0
        for value in (
            gap_improvement,
            primal_improvement,
            dual_bound_gain,
            fathom_gain,
            branch_count_delta,
            completion_retry_gain,
        )
    ) else 0.0
    return {
        "y_branch_priority_walltime_gain": branch_positive,
        "branch_priority_loss_weight": float(main_weight),
        "capped_wall_time_delta": float(delta),
        "capped_wall_time_delta_ratio": float(delta) / max(float(wall_cap), 1.0e-6),
        "y_target_wall_crossing_positive": 1.0 if target_crossing else 0.0,
        "y_strict_full_replay_positive": 1.0 if positive and strict_label else 0.0,
        "y_weak_positive_not_target": 1.0
        if positive and strict_label and not target_crossing
        else 0.0,
        "y_counterfactual_regression": regression,
        "y_timeout_regression": 0.0,
        "y_timeout_resolved": 0.0,
        "y_tail_improved_aux": 1.0 if positive and strict_label else 0.0,
        "tail_improved_loss_weight": 1.0 if positive and strict_label else 0.0,
        "y_walltime_gain": float(gain),
        "walltime_gain_loss_weight": float(main_weight),
        "y_child_proof_cpu": child_proof_cpu,
        "child_proof_cpu_loss_weight": max(0.0, _float(row.get("child_proof_cpu_loss_weight"))),
        "y_time_to_certificate": child_time_to_certificate,
        "time_to_certificate_loss_weight": max(
            0.0,
            _float(row.get("time_to_certificate_loss_weight")),
        ),
        "y_gap_improvement": float(gap_improvement),
        "gap_improvement_loss_weight": max(
            float(structural_weight),
            _float(row.get("gap_improvement_loss_weight")),
        ),
        "y_primal_improvement": float(primal_improvement),
        "primal_improvement_loss_weight": max(
            float(structural_weight),
            _float(row.get("primal_improvement_loss_weight")),
        ),
        "y_dual_bound_gain": float(dual_bound_gain),
        "dual_bound_gain_loss_weight": max(
            float(structural_weight),
            _float(row.get("dual_bound_gain_loss_weight")),
        ),
        "y_fathom_gain": float(fathom_gain),
        "fathom_gain_loss_weight": max(
            float(structural_weight),
            _float(row.get("fathom_gain_loss_weight")),
        ),
        "y_branch_count_delta": float(branch_count_delta),
        "branch_count_delta_loss_weight": max(
            float(structural_weight),
            _float(row.get("branch_count_delta_loss_weight")),
        ),
        "y_completion_bound_retry_gain": float(completion_retry_gain),
        "completion_bound_retry_gain_loss_weight": max(
            float(structural_weight),
            _float(row.get("completion_bound_retry_gain_loss_weight")),
        ),
    }


def build_tree_policy_event_dataset(
    inputs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    max_rows: int = 0,
    include_walltime_labels: bool = False,
    target_wall: float = 200.0,
    wall_cap: float = 600.0,
    min_wall_improvement: float = 30.0,
    min_wall_regression: float = 30.0,
    max_delta_weight: float = 4.0,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in inputs:
        rows.extend(_iter_jsonl(path))

    sample_dir = output_dir / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    for stale in sample_dir.glob("sample_*.pt"):
        stale.unlink()

    builder = FutureGraphBuilder()
    graph_cache: dict[str, Any] = {}
    samples: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    branch_priority_counts: Counter[str] = Counter()
    target_wall_counts: Counter[str] = Counter()
    tail_aux_counts: Counter[str] = Counter()
    instance_counts: Counter[str] = Counter()

    for row_index, row in enumerate(rows):
        if max_rows and len(samples) >= int(max_rows):
            skipped["max_rows_reached"] += 1
            break
        instance_path = Path(str(row.get("instance") or ""))
        if not instance_path.is_file():
            skipped["missing_instance_file"] += 1
            continue
        pair = _pair(row.get("selected_pair"))
        if pair is None:
            skipped["invalid_selected_pair"] += 1
            continue
        graph = graph_cache.get(str(instance_path))
        if graph is None:
            try:
                graph = builder.build_from_json(instance_path)
            except Exception:
                skipped["invalid_logical_graph"] += 1
                continue
            graph_cache[str(instance_path)] = graph
        task_ids = [int(value) for value in graph.task_ids.tolist()]
        task_to_index = {task_id: index for index, task_id in enumerate(task_ids)}
        if pair[0] not in task_to_index or pair[1] not in task_to_index:
            skipped["pair_task_missing_from_graph"] += 1
            continue

        positive = float(row.get("y_tree_policy_positive") or 0.0)
        hard_negative = float(row.get("y_tree_policy_hard_negative") or 0.0)
        if positive <= 0.0 and hard_negative <= 0.0:
            skipped["missing_tree_policy_label"] += 1
            continue
        label = 1.0 if positive > 0.5 else 0.0
        weight = max(0.0, _float(row.get("event_loss_weight"), default=1.0))
        if weight <= 0.0:
            skipped["zero_tree_policy_weight"] += 1
            continue
        action_labels = _tree_policy_action_labels(
            row,
            include_walltime_labels=include_walltime_labels,
            tree_label=label,
            target_wall=target_wall,
            wall_cap=wall_cap,
            min_wall_improvement=min_wall_improvement,
            min_wall_regression=min_wall_regression,
            max_delta_weight=max_delta_weight,
        )

        sample = graph.clone()
        sample.branch_pair_indices = torch.tensor(
            [[task_to_index[pair[0]], task_to_index[pair[1]]]],
            dtype=torch.long,
        )
        sample.branch_pair_task_ids = torch.tensor([list(pair)], dtype=torch.long)
        sample.branch_pair_features = torch.tensor([_branch_feature_vector(row)], dtype=torch.float32)
        sample.branch_action_context_features = torch.tensor(_context_feature_vector(row), dtype=torch.float32)
        sample.context_features = sample.branch_action_context_features

        sample.y_branch_priority = torch.tensor(
            [action_labels["y_branch_priority_walltime_gain"]],
            dtype=torch.float32,
        )
        sample.branch_priority_loss_weight = torch.tensor(
            [action_labels["branch_priority_loss_weight"]],
            dtype=torch.float32,
        )
        sample.y_tail_improved = torch.tensor(
            [action_labels["y_tail_improved_aux"]],
            dtype=torch.float32,
        )
        sample.tail_improved_loss_weight = torch.tensor(
            [action_labels["tail_improved_loss_weight"]],
            dtype=torch.float32,
        )
        sample.y_walltime_gain = torch.tensor([action_labels["y_walltime_gain"]], dtype=torch.float32)
        sample.walltime_gain_loss_weight = torch.tensor(
            [action_labels["walltime_gain_loss_weight"]],
            dtype=torch.float32,
        )
        sample.y_child_proof_cpu = torch.tensor([max(0.0, _float(row.get("child_proof_cpu")))], dtype=torch.float32)
        sample.child_proof_cpu_loss_weight = torch.tensor(
            [max(0.0, _float(row.get("child_proof_cpu_loss_weight")))],
            dtype=torch.float32,
        )
        sample.y_time_to_certificate = torch.tensor(
            [max(0.0, _float(row.get("child_time_to_certificate")))],
            dtype=torch.float32,
        )
        sample.time_to_certificate_loss_weight = torch.tensor(
            [max(0.0, _float(row.get("time_to_certificate_loss_weight")))],
            dtype=torch.float32,
        )
        sample.y_gap_improvement = torch.tensor([action_labels["y_gap_improvement"]], dtype=torch.float32)
        sample.gap_improvement_loss_weight = torch.tensor(
            [action_labels["gap_improvement_loss_weight"]],
            dtype=torch.float32,
        )
        sample.y_primal_improvement = torch.tensor([action_labels["y_primal_improvement"]], dtype=torch.float32)
        sample.primal_improvement_loss_weight = torch.tensor(
            [action_labels["primal_improvement_loss_weight"]],
            dtype=torch.float32,
        )
        sample.y_dual_bound_gain = torch.tensor([action_labels["y_dual_bound_gain"]], dtype=torch.float32)
        sample.dual_bound_gain_loss_weight = torch.tensor(
            [action_labels["dual_bound_gain_loss_weight"]],
            dtype=torch.float32,
        )
        sample.y_fathom_gain = torch.tensor([action_labels["y_fathom_gain"]], dtype=torch.float32)
        sample.fathom_gain_loss_weight = torch.tensor(
            [action_labels["fathom_gain_loss_weight"]],
            dtype=torch.float32,
        )
        sample.y_branch_count_delta = torch.tensor([action_labels["y_branch_count_delta"]], dtype=torch.float32)
        sample.branch_count_delta_loss_weight = torch.tensor(
            [action_labels["branch_count_delta_loss_weight"]],
            dtype=torch.float32,
        )
        sample.y_completion_bound_retry_gain = torch.tensor(
            [action_labels["y_completion_bound_retry_gain"]],
            dtype=torch.float32,
        )
        sample.completion_bound_retry_gain_loss_weight = torch.tensor(
            [action_labels["completion_bound_retry_gain_loss_weight"]],
            dtype=torch.float32,
        )
        sample.y_tree_policy = torch.tensor([label], dtype=torch.float32)
        sample.tree_policy_loss_weight = torch.tensor([float(weight)], dtype=torch.float32)
        sample.branch_action_labels = torch.tensor(
            [[action_labels[name] for name in BRANCH_ACTION_LABEL_SCHEMA]],
            dtype=torch.float32,
        )
        sample.branch_action_row_kind = str(row.get("tree_policy_label_type") or "")
        sample.branch_action_instance = str(instance_path)
        sample.branch_action_experiment = str(row.get("policy_run") or "")
        sample.branch_action_context_key = "|".join(
            [
                str(instance_path),
                str(row.get("node_id") if row.get("node_id") is not None else ""),
                str(row.get("depth") if row.get("depth") is not None else ""),
                str(row.get("baseline_pair") or ""),
                str(row.get("selected_pair") or ""),
            ]
        )
        sample.branch_action_node_context_key = "|".join(
            [
                str(instance_path),
                str(row.get("node_id") if row.get("node_id") is not None else ""),
                str(row.get("depth") if row.get("depth") is not None else ""),
                str(row.get("baseline_pair") or ""),
            ]
        )

        sample_name = f"sample_{len(samples):06d}.pt"
        torch.save(sample, sample_dir / sample_name)
        label_key = "tree_policy_positive" if label > 0.5 else "tree_policy_hard_negative"
        if bool(row.get("proof_tail_risk")) and label <= 0.5:
            label_key = "tree_policy_proof_tail_hard_negative"
        label_counts[label_key] += 1
        if action_labels["branch_priority_loss_weight"] <= 0.0:
            branch_priority_counts["aux_only_tree_policy"] += 1
        elif action_labels["y_branch_priority_walltime_gain"] > 0.5:
            branch_priority_counts["walltime_gain_positive"] += 1
        else:
            branch_priority_counts["not_walltime_gain"] += 1
        target_wall_counts[
            "target_wall_crossing_positive"
            if action_labels["y_target_wall_crossing_positive"] > 0.5
            else "not_target_wall_crossing"
        ] += 1
        tail_aux_counts[
            "tail_improved" if action_labels["y_tail_improved_aux"] > 0.5 else "tail_not_improved"
        ] += 1
        instance_counts[str(instance_path)] += 1
        samples.append(
            {
                "path": f"samples/{sample_name}",
                "source_row_index": int(row_index),
                "row_kind": label_key,
                "instance": str(instance_path),
                "policy_run": str(row.get("policy_run") or ""),
                "tree_policy_label_type": str(row.get("tree_policy_label_type") or ""),
                "tree_policy_loss_weight": float(weight),
                "right_censored": bool(row.get("right_censored", False)),
                "proof_tail_risk": bool(row.get("proof_tail_risk", False)),
                "child_proof_cpu": max(0.0, _float(row.get("child_proof_cpu"))),
                "child_proof_cpu_loss_weight": max(0.0, _float(row.get("child_proof_cpu_loss_weight"))),
                "child_time_to_certificate": max(0.0, _float(row.get("child_time_to_certificate"))),
                "time_to_certificate_loss_weight": max(0.0, _float(row.get("time_to_certificate_loss_weight"))),
                "branch_priority_label": (
                    "walltime_gain_positive"
                    if action_labels["y_branch_priority_walltime_gain"] > 0.5
                    else "not_walltime_gain"
                ),
                "branch_priority_loss_weight": action_labels["branch_priority_loss_weight"],
                "walltime_gain": action_labels["y_walltime_gain"],
                "walltime_gain_loss_weight": action_labels["walltime_gain_loss_weight"],
                "node_context_key": str(sample.branch_action_node_context_key),
            }
        )

    manifest = {
        "schema_version": "gat_branch_action_sanity_dataset_manifest_v1",
        "dataset_variant": "tree_policy_event_auxiliary",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "production_ready": False,
        "sample_count": len(samples),
        "sample_dir": str(sample_dir),
        "include_walltime_labels": bool(include_walltime_labels),
        "target_wall": float(target_wall),
        "wall_cap": float(wall_cap),
        "min_wall_improvement": float(min_wall_improvement),
        "min_wall_regression": float(min_wall_regression),
        "max_delta_weight": float(max_delta_weight),
        "samples": samples,
        "branch_feature_schema": list(BRANCH_IMPACT_FEATURE_SCHEMA),
        "context_feature_schema": list(BRANCH_ACTION_CONTEXT_FEATURE_SCHEMA),
        "label_schema": list(BRANCH_ACTION_LABEL_SCHEMA) + ["y_tree_policy", "tree_policy_loss_weight"],
        "branch_priority_label_counts": dict(branch_priority_counts),
        "target_wall_crossing_label_counts": dict(target_wall_counts),
        "tail_improved_aux_label_counts": dict(tail_aux_counts),
        "tree_policy_label_counts": dict(label_counts),
        "row_kind_counts": dict(label_counts),
        "proof_tail_risk_sample_count": int(label_counts.get("tree_policy_proof_tail_hard_negative", 0)),
        "right_censored_sample_count": sum(1 for sample in samples if bool(sample.get("right_censored"))),
        "instance_counts": dict(instance_counts),
        "skipped_counts": dict(skipped),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, manifest)
    return manifest


def _write_report(report: Path, manifest: dict[str, Any]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Tree-Policy Event Dataset",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把 tree-policy event rows 转成 GAT graph samples。默认只训练 tree_policy 辅助 head；显式 include_walltime_labels 时，带 capped wall-time gain 的严格 replay row 也会训练 branch-priority / wall-time head。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"sample_count = {manifest['sample_count']}",
        f"include_walltime_labels = {manifest['include_walltime_labels']}",
        f"branch_priority_label_counts = {manifest['branch_priority_label_counts']}",
        f"tree_policy_label_counts = {manifest['tree_policy_label_counts']}",
        f"target_wall_crossing_label_counts = {manifest['target_wall_crossing_label_counts']}",
        f"tail_improved_aux_label_counts = {manifest['tail_improved_aux_label_counts']}",
        f"instance_counts = {manifest['instance_counts']}",
        f"skipped_counts = {manifest['skipped_counts']}",
        "runs_bpc_or_pricing = false",
        "official_bound_effect = false",
        "certificate_effect = false",
        "production_ready = false",
        "```",
        "",
        "## 边界",
        "",
        "该数据集不能单独证明模型可泛化；它只生成离线训练样本，不运行 BPC/pricing/RMP，也不影响 official bound、certificate 或剪枝。wall-time 标签仅来自已完成 strict replay / controlled replay 的观测字段。",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--include-walltime-labels", action="store_true")
    parser.add_argument("--target-wall", type=float, default=200.0)
    parser.add_argument("--wall-cap", type=float, default=600.0)
    parser.add_argument("--min-wall-improvement", type=float, default=30.0)
    parser.add_argument("--min-wall-regression", type=float, default=30.0)
    parser.add_argument("--max-delta-weight", type=float, default=4.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_tree_policy_event_dataset(
        list(args.inputs),
        args.output_dir,
        args.report,
        max_rows=max(0, int(args.max_rows)),
        include_walltime_labels=bool(args.include_walltime_labels),
        target_wall=float(args.target_wall),
        wall_cap=float(args.wall_cap),
        min_wall_improvement=float(args.min_wall_improvement),
        min_wall_regression=float(args.min_wall_regression),
        max_delta_weight=float(args.max_delta_weight),
    )
    print(json.dumps(manifest, sort_keys=True))
    return 0 if int(manifest["sample_count"]) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
