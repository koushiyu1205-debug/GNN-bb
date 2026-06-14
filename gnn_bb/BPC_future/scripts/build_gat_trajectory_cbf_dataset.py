#!/usr/bin/env python3
"""Build a trajectory-labeled GAT dataset from CBF capture rows.

This converts H-step trajectory CBF rows plus their source
``journey_counterfactual_replay_capture`` events into graph samples with a batch
of returned candidate journeys.  It is offline-only: it does not run BPC,
pricing, RMP, workers, or certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.learning.column_selector import (
    SELECTOR_CLASS_ADD,
    SELECTOR_CLASS_NAMES,
    SELECTOR_CLASS_SKIP,
)
from BPC_future.learning.graph_builder import FutureGraphBuilder
from BPC_future.scripts.build_gnn_column_selector_dataset import (
    CANDIDATE_FEATURE_SCHEMA,
    CONTEXT_FEATURE_SCHEMA,
)


DEFAULT_TRAJECTORY_JSONL = Path(
    "BPC_future/results/cbf_trajectory_gate_dataset_global_all_h2_20260614/"
    "cbf_trajectory_gate_transitions.jsonl"
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/data/gat_trajectory_cbf/v1")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trajectory-jsonl", type=Path, default=DEFAULT_TRAJECTORY_JSONL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--max-candidates-per-row", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_dataset(
        trajectory_jsonl=args.trajectory_jsonl,
        output_dir=args.output_dir,
        max_rows=max(0, int(args.max_rows)),
        max_candidates_per_row=max(0, int(args.max_candidates_per_row)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def build_dataset(
    *,
    trajectory_jsonl: Path,
    output_dir: Path,
    max_rows: int = 0,
    max_candidates_per_row: int = 0,
) -> dict[str, Any]:
    rows = _read_jsonl(trajectory_jsonl)
    sample_dir = output_dir / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    for stale in sample_dir.glob("sample_*.pt"):
        stale.unlink()
    builder = FutureGraphBuilder()
    graph_cache: dict[str, Any] = {}
    capture_cache: dict[str, dict[tuple[str, int], dict[str, Any]]] = {}

    samples: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    instance_counts: Counter[str] = Counter()
    candidate_count_total = 0

    for row_index, row in enumerate(rows):
        if max_rows and len(samples) >= max_rows:
            break
        if row.get("schema_version") != "cbf_trajectory_gate_dataset_row_v1":
            skipped["unsupported_row_schema"] += 1
            continue
        if not row.get("diagnostic_only") or row.get("official_bound_effect"):
            skipped["non_diagnostic_or_official_effect"] += 1
            continue
        source_file = Path(str(row.get("source_file") or ""))
        if not source_file.exists():
            skipped["missing_source_file"] += 1
            continue
        events = capture_cache.get(str(source_file))
        if events is None:
            events = _load_capture_events(source_file)
            capture_cache[str(source_file)] = events
        event = events.get((str(row.get("context_hash") or ""), int(row.get("cg_iter") or -1)))
        if event is None:
            skipped["missing_capture_event"] += 1
            continue
        returned = list(event.get("returned_journeys") or [])
        if not returned:
            skipped["empty_returned_batch"] += 1
            continue
        if max_candidates_per_row:
            returned = returned[: int(max_candidates_per_row)]

        graph_path = Path(str(event.get("instance_path") or ""))
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
        task_ids = [int(value) for value in graph.task_ids.tolist()]
        candidate_membership: list[list[float]] = []
        candidate_features: list[list[float]] = []
        kept_journeys: list[dict[str, Any]] = []
        for journey in returned:
            task_set = _task_set(journey.get("task_set"))
            if not task_set:
                continue
            membership = [1.0 if task_id in task_set else 0.0 for task_id in task_ids]
            if sum(membership) <= 0:
                continue
            candidate_membership.append(membership)
            candidate_features.append([_candidate_feature(event, journey, field) for field in CANDIDATE_FEATURE_SCHEMA])
            kept_journeys.append(journey)
        if not candidate_membership:
            skipped["no_candidate_tasks_in_graph"] += 1
            continue

        label = SELECTOR_CLASS_ADD if int(row.get("label_horizon_cbf_feasible") or 0) else SELECTOR_CLASS_SKIP
        sample = graph.clone()
        sample.candidate_task_membership = torch.tensor(candidate_membership, dtype=torch.float32)
        sample.candidate_features = torch.tensor(candidate_features, dtype=torch.float32)
        sample.context_features = torch.tensor(
            [_context_feature(event, row, field) for field in CONTEXT_FEATURE_SCHEMA],
            dtype=torch.float32,
        )
        sample.y_selector = torch.full((len(candidate_membership),), label, dtype=torch.long)
        sample.trajectory_label_horizon_cbf_feasible = int(row.get("label_horizon_cbf_feasible") or 0)
        sample.trajectory_horizon_delta_v = float(row.get("horizon_delta_v") or 0.0)
        sample.trajectory_horizon_barrier_slack = float(row.get("horizon_barrier_slack") or 0.0)
        sample.selector_instance = str(row.get("instance") or event.get("instance") or "")
        sample.selector_context_hash = str(row.get("context_hash") or "")
        sample.selector_source_jsonl = str(source_file)
        sample.selector_source_row_index = row_index
        sample.selector_candidate_ids = [str(journey.get("id", idx)) for idx, journey in enumerate(kept_journeys)]

        sample_name = f"sample_{len(samples):06d}.pt"
        torch.save(sample, sample_dir / sample_name)
        samples.append(
            {
                "path": f"samples/{sample_name}",
                "instance": sample.selector_instance,
                "context_hash": sample.selector_context_hash,
                "source_file": str(source_file),
                "row_index": row_index,
                "candidate_count": len(candidate_membership),
                "label_horizon_cbf_feasible": int(row.get("label_horizon_cbf_feasible") or 0),
                "label": SELECTOR_CLASS_NAMES[label],
            }
        )
        candidate_count_total += len(candidate_membership)
        label_counts[SELECTOR_CLASS_NAMES[label]] += 1
        instance_counts[sample.selector_instance] += 1

    candidate_feature_mean, candidate_feature_std = _feature_stats(sample_dir, "candidate_features")
    context_feature_mean, context_feature_std = _feature_stats(sample_dir, "context_features")
    manifest = {
        "schema_version": "gat_trajectory_cbf_dataset_manifest_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "source_jsonl": str(trajectory_jsonl),
        "sample_count": len(samples),
        "candidate_count": candidate_count_total,
        "skipped_counts": dict(sorted(skipped.items())),
        "label_counts": dict(sorted(label_counts.items())),
        "instance_counts": dict(sorted(instance_counts.items())),
        "candidate_feature_schema": list(CANDIDATE_FEATURE_SCHEMA),
        "context_feature_schema": list(CONTEXT_FEATURE_SCHEMA),
        "label_schema": ["label_horizon_cbf_feasible"],
        "label_semantics": "batch_horizon_cbf_feasible_broadcast_to_returned_candidates",
        "candidate_feature_mean": candidate_feature_mean,
        "candidate_feature_std": candidate_feature_std,
        "context_feature_mean": context_feature_mean,
        "context_feature_std": context_feature_std,
        "selector_class_names": list(SELECTOR_CLASS_NAMES),
        "samples": samples,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    summary = {
        "schema_version": "gat_trajectory_cbf_dataset_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "gat_trajectory_cbf_dataset_built",
        "source_jsonl": str(trajectory_jsonl),
        "output_dir": str(output_dir),
        "sample_count": len(samples),
        "candidate_count": candidate_count_total,
        "label_counts": dict(sorted(label_counts.items())),
        "instance_count": len(instance_counts),
        "skipped_counts": dict(sorted(skipped.items())),
        "has_mixed_horizon_labels": bool(label_counts.get("add", 0) > 0 and label_counts.get("skip", 0) > 0),
        "all_checks_pass": bool(len(samples) > 0 and candidate_count_total > 0),
        "production_ready": False,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _load_capture_events(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    events: dict[tuple[str, int], dict[str, Any]] = {}
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            event = json.loads(line)
            if event.get("event") != "journey_counterfactual_replay_capture":
                continue
            key = (str(event.get("context_hash") or ""), int(event.get("cg_iter") or -1))
            events[key] = event
    return events


def _task_set(value: Any) -> set[int]:
    result: set[int] = set()
    if isinstance(value, list):
        for item in value:
            try:
                result.add(int(item))
            except (TypeError, ValueError):
                return set()
    return result


def _candidate_feature(event: dict[str, Any], journey: dict[str, Any], field: str) -> float:
    task_set = _task_set(journey.get("task_set"))
    if field == "true_reduced_cost":
        return _finite_float(journey.get("true_reduced_cost"))
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
    return 0.0


def _context_feature(event: dict[str, Any], row: dict[str, Any], field: str) -> float:
    aliases = {
        "column_pool_size_before": "pool_journey_count",
        "active_basis_size_before": "active_basis_journey_count",
        "active_basis_unique_task_set_count_before": "active_task_set_count",
        "lambda_active_count_before": "active_basis_journey_count",
        "lambda_fractional_count_before": "active_basis_fractional_journey_count",
        "rmp_objective_before": "rmp_objective_before",
        "pricing_tail_retry_count_before": "state_t_final_judge_retry_count",
    }
    if field == "dual_l1_norm_before":
        dual = event.get("true_dual_vector")
        if isinstance(dual, list):
            return float(sum(abs(_finite_float(value)) for value in dual))
    if field == "dual_linf_norm_before":
        dual = event.get("true_dual_vector")
        if isinstance(dual, list) and dual:
            return float(max(abs(_finite_float(value)) for value in dual))
    if field in row:
        return _finite_float(row.get(field))
    alias = aliases.get(field)
    if alias and alias in event:
        return _finite_float(event.get(alias))
    if alias and alias in row:
        return _finite_float(row.get(alias))
    return _finite_float(event.get(field))


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


def _finite_float(value: Any) -> float:
    try:
        result = float(value) if value not in {None, ""} else 0.0
    except (TypeError, ValueError):
        result = 0.0
    if math.isnan(result) or math.isinf(result):
        return 0.0
    return float(result)


def _feature_stats(sample_dir: Path, field: str) -> tuple[list[float], list[float]]:
    tensors: list[torch.Tensor] = []
    for path in sorted(sample_dir.glob("sample_*.pt")):
        sample = torch.load(path, map_location="cpu", weights_only=False)
        tensor = getattr(sample, field).to(dtype=torch.float32)
        if tensor.dim() == 1:
            tensor = tensor.unsqueeze(0)
        if field == "candidate_features":
            tensors.append(tensor)
        else:
            tensors.append(tensor.unsqueeze(0) if tensor.dim() == 1 else tensor)
    if not tensors:
        return [], []
    stacked = torch.cat(tensors, dim=0)
    mean = stacked.mean(dim=0)
    std = stacked.std(dim=0, unbiased=False)
    std = torch.where(std > 1.0e-12, std, torch.ones_like(std))
    return [float(value) for value in mean.tolist()], [float(value) for value in std.tolist()]


if __name__ == "__main__":
    raise SystemExit(main())
