#!/usr/bin/env python3
"""Build a GAT graph dataset from audited worker ROI labels.

The input rows are produced by ``build_gat_worker_roi_dataset.py``.  Each
training sample is one same-context target-intervention candidate with a
causal worker match and an observed ROI label.

Exactness boundary:
* diagnostic/offline only;
* does not run BPC, pricing, RMP, workers, or certificates;
* true-RC negative candidates with no/negative ROI are labelled
  ``abstain`` / delay-queue, not ``skip`` / permanent reject.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
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
)
from BPC_future.learning.graph_builder import FutureGraphBuilder
from BPC_future.scripts.build_gat_same_run_batch_impact_graph_dataset import (
    _candidate_feature,
    _context_feature,
    _feature_stats,
)
from BPC_future.scripts.build_gnn_column_selector_dataset import (
    CANDIDATE_FEATURE_SCHEMA,
    CONTEXT_FEATURE_SCHEMA,
)


DEFAULT_INPUT = Path(
    "BPC_future/results/gat_same_run_combined_plus_seed_cross_family_worker_roi_dataset_20260615/"
    "gat_worker_roi_rows.jsonl"
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/data/gat_worker_roi/v1")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260615_bpc_future_gat_worker_roi_graph_dataset_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-jsonl", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-rows", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_dataset(
        input_jsonl=args.input_jsonl,
        output_dir=args.output_dir,
        report=args.report,
        max_rows=max(0, int(args.max_rows)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def build_dataset(
    *,
    input_jsonl: Path = DEFAULT_INPUT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    max_rows: int = 0,
) -> dict[str, Any]:
    rows = _read_jsonl(input_jsonl)
    sample_dir = output_dir / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    for stale in sample_dir.glob("sample_*.pt"):
        stale.unlink()

    builder = FutureGraphBuilder()
    graph_cache: dict[str, Any] = {}
    event_cache: dict[str, dict[str, dict[str, Any]]] = {}
    samples: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    roi_class_counts: Counter[str] = Counter()
    instance_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    region_counts: Counter[str] = Counter()

    for row_index, row in enumerate(rows):
        if max_rows and len(samples) >= int(max_rows):
            break
        if row.get("schema_version") != "gat_worker_roi_dataset_row_v1":
            skipped["unsupported_row_schema"] += 1
            continue
        if not row.get("diagnostic_only") or row.get("official_bound_effect"):
            skipped["non_diagnostic_or_official_effect"] += 1
            continue
        if not row.get("training_eligible"):
            skipped[f"not_training_eligible:{row.get('training_exclusion_reason') or 'unknown'}"] += 1
            continue
        label = _label_for_row(row)
        if label is None:
            skipped[f"unsupported_roi_class:{row.get('roi_class') or 'unknown'}"] += 1
            continue
        source_file_raw = str(row.get("source_file") or "")
        if not source_file_raw:
            skipped["missing_source_file"] += 1
            continue
        source_file = Path(source_file_raw)
        if not source_file.is_file():
            skipped["missing_source_file"] += 1
            continue
        events = event_cache.get(str(source_file))
        if events is None:
            events = _load_capture_events_by_context(source_file)
            event_cache[str(source_file)] = events
        context_hash = str(row.get("expected_context_hash") or "")
        event = events.get(context_hash)
        if event is None:
            skipped["missing_capture_event"] += 1
            continue
        journey = _match_target_journey(event, row)
        if journey is None:
            skipped["missing_target_journey_in_capture_event"] += 1
            continue
        graph_path = Path(str(row.get("instance") or event.get("instance_path") or ""))
        if not graph_path.exists():
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
        target_task_set = set(_target_sequence(row))
        membership = [1.0 if task_id in target_task_set else 0.0 for task_id in task_ids]
        if sum(membership) <= 0:
            skipped["target_tasks_not_in_graph"] += 1
            continue

        row_for_context = dict(row)
        row_for_context["cg_iter"] = row.get("capture_cg_iter", event.get("cg_iter"))
        sample = graph.clone()
        sample.candidate_task_membership = torch.tensor([membership], dtype=torch.float32)
        sample.candidate_features = torch.tensor(
            [[_candidate_feature(event, journey, field) for field in CANDIDATE_FEATURE_SCHEMA]],
            dtype=torch.float32,
        )
        sample.context_features = torch.tensor(
            [_context_feature(event, row_for_context, field) for field in CONTEXT_FEATURE_SCHEMA],
            dtype=torch.float32,
        )
        sample.y_selector = torch.tensor([label], dtype=torch.long)
        sample.worker_roi_label_positive = int(row.get("label_worker_roi_positive") or 0)
        sample.worker_roi_class = str(row.get("roi_class") or "")
        sample.worker_roi_primal_improvement = float(row.get("primal_improvement") or 0.0)
        sample.selector_instance = str(row.get("name") or event.get("instance") or "")
        sample.selector_instance_path = str(graph_path)
        sample.selector_instance_family = str(row.get("instance_family") or "")
        sample.selector_instance_region = str(row.get("instance_region") or "")
        sample.selector_context_hash = context_hash
        sample.selector_source_jsonl = str(source_file)
        sample.selector_source_row_index = int(row_index)
        sample.selector_candidate_ids = [str(journey.get("id", 0))]

        sample_name = f"sample_{len(samples):06d}.pt"
        torch.save(sample, sample_dir / sample_name)
        label_name = SELECTOR_CLASS_NAMES[label]
        roi_class = str(row.get("roi_class") or "")
        label_counts[label_name] += 1
        roi_class_counts[roi_class] += 1
        instance_counts[str(row.get("instance") or "")] += 1
        family_counts[str(row.get("instance_family") or "")] += 1
        region_counts[str(row.get("instance_region") or "")] += 1
        samples.append(
            {
                "path": f"samples/{sample_name}",
                "name": str(row.get("name") or ""),
                "instance": str(row.get("instance") or ""),
                "instance_family": str(row.get("instance_family") or ""),
                "instance_region": str(row.get("instance_region") or ""),
                "context_hash": context_hash,
                "source_file": str(source_file),
                "row_index": int(row_index),
                "candidate_count": 1,
                "roi_class": roi_class,
                "label_worker_roi_positive": int(row.get("label_worker_roi_positive") or 0),
                "selector_label": label_name,
            }
        )

    candidate_feature_mean, candidate_feature_std = _feature_stats(sample_dir, "candidate_features")
    context_feature_mean, context_feature_std = _feature_stats(sample_dir, "context_features")
    manifest = {
        "schema_version": "gat_worker_roi_graph_dataset_manifest_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "source_jsonl": str(input_jsonl),
        "sample_count": len(samples),
        "candidate_count": len(samples),
        "skipped_counts": dict(sorted(skipped.items())),
        "candidate_label_counts": dict(sorted(label_counts.items())),
        "roi_class_counts": dict(sorted(roi_class_counts.items())),
        "instance_counts": dict(sorted(instance_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "region_counts": dict(sorted(region_counts.items())),
        "candidate_feature_schema": list(CANDIDATE_FEATURE_SCHEMA),
        "context_feature_schema": list(CONTEXT_FEATURE_SCHEMA),
        "candidate_feature_mean": candidate_feature_mean,
        "candidate_feature_std": candidate_feature_std,
        "context_feature_mean": context_feature_mean,
        "context_feature_std": context_feature_std,
        "selector_class_names": list(SELECTOR_CLASS_NAMES),
        "label_semantics": {
            "add": "same_context_target_intervention_positive_primal_roi",
            "abstain": "same_context_target_intervention_no_or_negative_primal_roi_delay_queue",
            "skip": "reserved_for_nonnegative_candidates_only_not_used_for_true_rc_negative_roi_rows",
        },
        "exactness_contract": (
            "Offline GAT worker-ROI labels only. Negative ROI true-RC candidates "
            "are delay-queue labels, not permanent reject labels."
        ),
        "samples": samples,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "manifest.json", manifest)
    summary = {
        "schema_version": "gat_worker_roi_graph_dataset_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "gat_worker_roi_graph_dataset_built",
        "source_jsonl": str(input_jsonl),
        "output_dir": str(output_dir),
        "sample_count": len(samples),
        "candidate_count": len(samples),
        "candidate_label_counts": dict(sorted(label_counts.items())),
        "roi_class_counts": dict(sorted(roi_class_counts.items())),
        "instance_count": len(instance_counts),
        "family_count": len(family_counts),
        "region_count": len(region_counts),
        "skipped_counts": dict(sorted(skipped.items())),
        "has_high_priority_and_delay_labels": bool(
            label_counts.get("add", 0) > 0 and label_counts.get("abstain", 0) > 0
        ),
        "delay_queue_label_count": int(label_counts.get("abstain", 0)),
        "production_ready": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "all_checks_pass": bool(
            len(samples) > 0
            and label_counts.get("add", 0) > 0
            and label_counts.get("abstain", 0) > 0
        ),
    }
    _write_json(output_dir / "summary.json", summary)
    _write_report(Path(report), summary)
    return summary


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for raw in handle:
            text = raw.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_capture_events_by_context(path: Path) -> dict[str, dict[str, Any]]:
    events: dict[str, dict[str, Any]] = {}
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        for raw in handle:
            if "journey_counterfactual_replay_capture" not in raw:
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if event.get("event") != "journey_counterfactual_replay_capture":
                continue
            context_hash = str(event.get("context_hash") or "")
            if context_hash:
                events.setdefault(context_hash, event)
    return events


def _target_sequence(row: dict[str, Any]) -> tuple[int, ...]:
    result: list[int] = []
    for item in row.get("target_sequence") or []:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            return tuple()
    return tuple(result)


def _task_set(value: Any) -> set[int]:
    result: set[int] = set()
    for item in value or []:
        try:
            result.add(int(item))
        except (TypeError, ValueError):
            return set()
    return result


def _match_target_journey(event: dict[str, Any], row: dict[str, Any]) -> dict[str, Any] | None:
    target_set = set(_target_sequence(row))
    if not target_set:
        return None
    candidates: list[dict[str, Any]] = []
    for journey in event.get("returned_journeys") or []:
        if not isinstance(journey, dict):
            continue
        if _task_set(journey.get("task_set")) == target_set:
            candidates.append(journey)
    if not candidates:
        return None
    target_rc = _float_or_none(row.get("best_true_reduced_cost"))
    if target_rc is None:
        return candidates[0]
    return min(
        candidates,
        key=lambda journey: abs(
            float(journey.get("true_reduced_cost", journey.get("manual_true_reduced_cost", 0.0)) or 0.0)
            - target_rc
        ),
    )


def _float_or_none(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result


def _label_for_row(row: dict[str, Any]) -> int | None:
    explicit_label = _explicit_roi_label(row)
    if explicit_label == 1:
        return SELECTOR_CLASS_ADD
    if explicit_label == 0:
        return SELECTOR_CLASS_ABSTAIN
    roi_class = str(row.get("roi_class") or "")
    if roi_class.startswith("positive_"):
        return SELECTOR_CLASS_ADD
    if roi_class in {"no_observed_roi", "negative_primal_roi", "negative_retry_roi"}:
        return SELECTOR_CLASS_ABSTAIN
    return None


def _explicit_roi_label(row: dict[str, Any]) -> int | None:
    for key in (
        "label_positive_trajectory_roi",
        "label_positive_trajectory_roi_merged",
        "label_worker_roi_positive",
    ):
        value = row.get(key)
        if value is None:
            continue
        try:
            return 1 if int(value) == 1 else 0
        except (TypeError, ValueError):
            continue
    return None


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Worker ROI Graph Dataset 报告",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "把 same-context target-intervention ROI rows 转换为现有 GAT",
        "`ContextAwareColumnSelector` 可训练的图样本。该数据只用于离线 ROI gate",
        "校准，不运行 BPC / pricing / RMP / worker，不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_worker_roi_graph_dataset = current",
        f"status = {summary['status']}",
        f"sample_count = {summary['sample_count']}",
        f"candidate_count = {summary['candidate_count']}",
        f"candidate_label_counts = {summary['candidate_label_counts']}",
        f"roi_class_counts = {summary['roi_class_counts']}",
        f"delay_queue_label_count = {summary['delay_queue_label_count']}",
        f"instance_count = {summary['instance_count']}",
        f"family_count = {summary['family_count']}",
        f"region_count = {summary['region_count']}",
        f"skipped_counts = {summary['skipped_counts']}",
        f"has_high_priority_and_delay_labels = {str(summary['has_high_priority_and_delay_labels']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 标签语义",
        "",
        "- `add`：同 context target intervention 后出现 positive primal ROI，作为 HIGH_PRIORITY；",
        "- `abstain`：同 context target intervention 后 no/negative primal ROI，进入 DELAY_QUEUE；",
        "- `skip`：仅保留给非负 reduced-cost 候选，本数据集不使用，不能用于永久丢弃负列。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
