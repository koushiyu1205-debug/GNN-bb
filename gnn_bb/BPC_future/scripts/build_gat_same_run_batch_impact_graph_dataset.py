#!/usr/bin/env python3
"""Build a GAT graph dataset from same-run batch-impact labels.

The input rows are produced by ``build_gat_same_run_batch_impact_dataset.py``.
Each output sample is one solver context with the returned journey batch from
the matching ``journey_counterfactual_replay_capture`` event.

Exactness boundary:
* diagnostic/offline only;
* does not run BPC, pricing, RMP, workers, or certificates;
* true-RC negative candidates from non-improving batches are labelled
  ``abstain`` / delay-queue, not ``skip`` / permanent reject.
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
    SELECTOR_CLASS_ABSTAIN,
    SELECTOR_CLASS_ADD,
    SELECTOR_CLASS_NAMES,
    SELECTOR_CLASS_SKIP,
)
from BPC_future.learning.graph_builder import FutureGraphBuilder
from BPC_future.scripts.build_gnn_column_selector_dataset import (
    CANDIDATE_FEATURE_SCHEMA,
    CONTEXT_FEATURE_SCHEMA,
)


DEFAULT_INPUT = Path(
    "BPC_future/results/gat_same_run_batch_impact_dataset_20260615/"
    "same_run_batch_impact_rows.jsonl"
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/data/gat_same_run_batch_impact/v1")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260615_bpc_future_gat_same_run_batch_impact_graph_dataset_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-jsonl", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--max-candidates-per-row", type=int, default=0)
    parser.add_argument("--true-rc-negative-eps", type=float, default=1.0e-9)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_dataset(
        input_jsonl=args.input_jsonl,
        output_dir=args.output_dir,
        report=args.report,
        max_rows=max(0, int(args.max_rows)),
        max_candidates_per_row=max(0, int(args.max_candidates_per_row)),
        true_rc_negative_eps=float(args.true_rc_negative_eps),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def build_dataset(
    *,
    input_jsonl: Path = DEFAULT_INPUT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    max_rows: int = 0,
    max_candidates_per_row: int = 0,
    true_rc_negative_eps: float = 1.0e-9,
) -> dict[str, Any]:
    rows = _read_jsonl(input_jsonl)
    sample_dir = output_dir / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    for stale in sample_dir.glob("sample_*.pt"):
        stale.unlink()

    builder = FutureGraphBuilder()
    graph_cache: dict[str, Any] = {}
    capture_cache: dict[str, dict[tuple[str, int, str, int, int], dict[str, Any]]] = {}

    samples: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    candidate_label_counts: Counter[str] = Counter()
    instance_counts: Counter[str] = Counter()
    region_counts: Counter[str] = Counter()
    candidate_count_total = 0

    for row_index, row in enumerate(rows):
        if max_rows and len(samples) >= int(max_rows):
            break
        if row.get("schema_version") != "gat_same_run_batch_impact_row_v1":
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
        key = (
            str(row.get("context_hash") or ""),
            int(row.get("cg_iter") or -1),
            str(row.get("pricing_kind") or ""),
            int(row.get("node_id") or 0),
            int(row.get("depth") or 0),
        )
        event = events.get(key)
        if event is None:
            skipped["missing_capture_event"] += 1
            continue
        returned = list(event.get("returned_journeys") or [])
        if max_candidates_per_row:
            returned = returned[: int(max_candidates_per_row)]
        if not returned:
            skipped["empty_returned_batch"] += 1
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

        task_ids = [int(value) for value in graph.task_ids.tolist()]
        candidate_membership: list[list[float]] = []
        candidate_features: list[list[float]] = []
        labels: list[int] = []
        kept_journeys: list[dict[str, Any]] = []
        for journey in returned:
            task_set = _task_set(journey.get("task_set"))
            if not task_set:
                continue
            membership = [1.0 if task_id in task_set else 0.0 for task_id in task_ids]
            if sum(membership) <= 0:
                continue
            label = _candidate_label(
                journey=journey,
                batch_objective_improved=bool(row.get("label_objective_improved")),
                true_rc_negative_eps=float(true_rc_negative_eps),
            )
            candidate_membership.append(membership)
            candidate_features.append(
                [_candidate_feature(event, journey, field) for field in CANDIDATE_FEATURE_SCHEMA]
            )
            labels.append(label)
            kept_journeys.append(journey)
            candidate_label_counts[SELECTOR_CLASS_NAMES[label]] += 1
        if not candidate_membership:
            skipped["no_candidate_tasks_in_graph"] += 1
            continue

        sample = graph.clone()
        sample.candidate_task_membership = torch.tensor(candidate_membership, dtype=torch.float32)
        sample.candidate_features = torch.tensor(candidate_features, dtype=torch.float32)
        sample.context_features = torch.tensor(
            [_context_feature(event, row, field) for field in CONTEXT_FEATURE_SCHEMA],
            dtype=torch.float32,
        )
        sample.y_selector = torch.tensor(labels, dtype=torch.long)
        sample.same_run_label_objective_improved = int(row.get("label_objective_improved") or 0)
        sample.same_run_objective_improvement = float(row.get("objective_improvement") or 0.0)
        sample.same_run_objective_delta = float(row.get("objective_delta") or 0.0)
        sample.selector_instance = str(row.get("instance") or event.get("instance") or "")
        sample.selector_instance_path = str(graph_path)
        sample.selector_instance_region = str(row.get("instance_region") or "")
        sample.selector_context_hash = str(row.get("context_hash") or "")
        sample.selector_source_jsonl = str(source_file)
        sample.selector_source_row_index = int(row_index)
        sample.selector_candidate_ids = [
            str(journey.get("id", idx)) for idx, journey in enumerate(kept_journeys)
        ]

        sample_name = f"sample_{len(samples):06d}.pt"
        torch.save(sample, sample_dir / sample_name)
        sample_label_counter = Counter(SELECTOR_CLASS_NAMES[label] for label in labels)
        samples.append(
            {
                "path": f"samples/{sample_name}",
                "instance": sample.selector_instance,
                "instance_region": sample.selector_instance_region,
                "context_hash": sample.selector_context_hash,
                "source_file": str(source_file),
                "row_index": int(row_index),
                "candidate_count": len(candidate_membership),
                "label_objective_improved": int(row.get("label_objective_improved") or 0),
                "candidate_label_counts": dict(sorted(sample_label_counter.items())),
            }
        )
        candidate_count_total += len(candidate_membership)
        label_counts["objective_improved" if row.get("label_objective_improved") else "non_improving"] += 1
        instance_counts[sample.selector_instance] += 1
        region_counts[sample.selector_instance_region] += 1

    candidate_feature_mean, candidate_feature_std = _feature_stats(sample_dir, "candidate_features")
    context_feature_mean, context_feature_std = _feature_stats(sample_dir, "context_features")
    manifest = {
        "schema_version": "gat_same_run_batch_impact_graph_dataset_manifest_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "source_jsonl": str(input_jsonl),
        "sample_count": len(samples),
        "candidate_count": int(candidate_count_total),
        "skipped_counts": dict(sorted(skipped.items())),
        "batch_label_counts": dict(sorted(label_counts.items())),
        "candidate_label_counts": dict(sorted(candidate_label_counts.items())),
        "instance_counts": dict(sorted(instance_counts.items())),
        "region_counts": dict(sorted(region_counts.items())),
        "candidate_feature_schema": list(CANDIDATE_FEATURE_SCHEMA),
        "context_feature_schema": list(CONTEXT_FEATURE_SCHEMA),
        "candidate_feature_mean": candidate_feature_mean,
        "candidate_feature_std": candidate_feature_std,
        "context_feature_mean": context_feature_mean,
        "context_feature_std": context_feature_std,
        "selector_class_names": list(SELECTOR_CLASS_NAMES),
        "label_semantics": {
            "add": "true_rc_negative_and_batch_objective_improved_high_priority",
            "abstain": "true_rc_negative_and_batch_non_improving_delay_queue",
            "skip": "nonnegative_candidate_only_reject_nonnegative",
        },
        "exactness_contract": (
            "Offline GAT trajectory-impact labels only. Negative candidates in "
            "non-improving batches are delay-queue labels, not permanent reject labels."
        ),
        "samples": samples,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    has_add_and_delay = bool(
        candidate_label_counts.get("add", 0) > 0
        and candidate_label_counts.get("abstain", 0) > 0
    )
    summary = {
        "schema_version": "gat_same_run_batch_impact_graph_dataset_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "gat_same_run_batch_impact_graph_dataset_built",
        "source_jsonl": str(input_jsonl),
        "output_dir": str(output_dir),
        "sample_count": len(samples),
        "candidate_count": int(candidate_count_total),
        "batch_label_counts": dict(sorted(label_counts.items())),
        "candidate_label_counts": dict(sorted(candidate_label_counts.items())),
        "instance_count": len(instance_counts),
        "region_count": len(region_counts),
        "skipped_counts": dict(sorted(skipped.items())),
        "has_high_priority_and_delay_labels": has_add_and_delay,
        "delay_queue_label_count": int(candidate_label_counts.get("abstain", 0)),
        "production_ready": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "all_checks_pass": bool(len(samples) > 0 and candidate_count_total > 0 and has_add_and_delay),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


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


def _candidate_label(
    *,
    journey: dict[str, Any],
    batch_objective_improved: bool,
    true_rc_negative_eps: float,
) -> int:
    true_rc = _finite_float(
        journey.get("true_reduced_cost", journey.get("manual_true_reduced_cost"))
    )
    if true_rc >= -abs(float(true_rc_negative_eps)):
        return SELECTOR_CLASS_SKIP
    if batch_objective_improved:
        return SELECTOR_CLASS_ADD
    return SELECTOR_CLASS_ABSTAIN


def _candidate_feature(event: dict[str, Any], journey: dict[str, Any], field: str) -> float:
    task_set = _task_set(journey.get("task_set"))
    if field == "true_reduced_cost":
        return _finite_float(journey.get("true_reduced_cost", journey.get("manual_true_reduced_cost")))
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
        "recent_objective_delta_before": "objective_delta",
        "rmp_objective_before": "objective_before",
        "pricing_tail_retry_count_before": "state_t_final_judge_retry_count",
    }
    if field == "cg_iter":
        return _finite_float(row.get("cg_iter", event.get("cg_iter")))
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
    if alias and alias in row:
        return _finite_float(row.get(alias))
    if alias and alias in event:
        return _finite_float(event.get(alias))
    return _finite_float(event.get(field))


def _task_set(value: Any) -> set[int]:
    result: set[int] = set()
    if isinstance(value, list):
        for item in value:
            try:
                result.add(int(item))
            except (TypeError, ValueError):
                return set()
    return result


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
        "# GAT Same-Run Batch Impact Graph Dataset 报告",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "把 same-run batch-impact rows 转换为 GAT `ContextAwareColumnSelector`",
        "可读取的图样本。该数据只用于离线 trajectory-impact 诊断训练，不运行",
        "BPC / pricing / RMP / worker，不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_same_run_batch_impact_graph_dataset = current",
        f"status = {summary['status']}",
        f"sample_count = {summary['sample_count']}",
        f"candidate_count = {summary['candidate_count']}",
        f"batch_label_counts = {summary['batch_label_counts']}",
        f"candidate_label_counts = {summary['candidate_label_counts']}",
        f"delay_queue_label_count = {summary['delay_queue_label_count']}",
        f"instance_count = {summary['instance_count']}",
        f"region_count = {summary['region_count']}",
        f"has_high_priority_and_delay_labels = {str(summary['has_high_priority_and_delay_labels']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 标签语义",
        "",
        "- `add`：true-RC negative 且该 batch 真实加入后 RMP objective 改善，作为 HIGH_PRIORITY；",
        "- `abstain`：true-RC negative 但该 batch 加入后 objective 未改善，进入 DELAY_QUEUE；",
        "- `skip`：仅允许用于非负 reduced-cost 候选，不能用于永久丢弃负列。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
