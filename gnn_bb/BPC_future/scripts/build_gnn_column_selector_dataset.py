#!/usr/bin/env python3
"""Build a supervised dataset for the context-aware GNN column selector.

The dataset is offline-only.  It converts existing no-certificate-effect replay
rows into PyTorch/PyG samples consumed by
``BPC_future.learning.column_selector.ContextAwareColumnSelector``.
It does not run BPC, pricing, RMP, Pulse, workers, or certificates.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
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


DEFAULT_INPUT = Path(
    "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/"
    "combined/combined_candidate_impact_rows.csv"
)
DEFAULT_LOGICAL_ROOT = Path("BPC_future/logical_graph")
DEFAULT_OUTPUT_DIR = Path("BPC_future/data/column_selector/v1")

CANDIDATE_FEATURE_SCHEMA: tuple[str, ...] = (
    "true_reduced_cost",
    "cost",
    "task_count",
    "vehicle_count",
    "new_task_set",
    "strict_replacement_by_cost",
    "weak_replacement_or_duplicate",
    "duplicate_signature",
    "duplicate_signature_pool_count_before",
    "task_set_pool_count_before",
)

CONTEXT_FEATURE_SCHEMA: tuple[str, ...] = (
    "cg_iter",
    "column_pool_size_before",
    "active_basis_size_before",
    "active_basis_unique_task_set_count_before",
    "active_basis_churn_count_before",
    "active_basis_hash_churn_count_before",
    "active_basis_hash_unique_count_before",
    "lambda_active_count_before",
    "lambda_fractional_count_before",
    "recent_added_column_acceptance_rate_before",
    "recent_dual_l1_delta_before",
    "recent_objective_delta_before",
    "rmp_degeneracy_proxy_score_before",
    "rmp_objective_before",
    "dual_l1_norm_before",
    "dual_linf_norm_before",
    "pricing_tail_retry_count_before",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--logical-root", type=Path, default=DEFAULT_LOGICAL_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--include-abstain",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Keep rows without an improved/noop label as abstain samples.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=0,
        help="Optional row cap for smoke builds. 0 means no cap.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_dataset(
        input_csv=args.input,
        logical_root=args.logical_root,
        output_dir=args.output_dir,
        include_abstain=bool(args.include_abstain),
        max_rows=max(0, int(args.max_rows)),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def build_dataset(
    *,
    input_csv: Path,
    logical_root: Path,
    output_dir: Path,
    include_abstain: bool = True,
    max_rows: int = 0,
) -> dict[str, Any]:
    rows = _read_csv(input_csv)
    graph_paths = _logical_graph_path_map(logical_root)
    sample_dir = output_dir / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    builder = FutureGraphBuilder()

    samples: list[dict[str, Any]] = []
    skipped = Counter()
    label_counts: Counter[str] = Counter()
    instance_counts: Counter[str] = Counter()
    graph_cache: dict[str, Any] = {}

    for row_index, row in enumerate(rows):
        if max_rows and len(samples) >= max_rows:
            break
        instance = str(row.get("instance") or "")
        graph_path = graph_paths.get(instance)
        if graph_path is None:
            skipped["missing_logical_graph"] += 1
            continue
        label = _selector_label(row)
        if label == SELECTOR_CLASS_ABSTAIN and not include_abstain:
            skipped["abstain_label"] += 1
            continue
        task_set = _parse_task_set(row.get("task_set") or row.get("candidate_task_set"))
        if not task_set:
            skipped["empty_task_set"] += 1
            continue

        cache_key = str(graph_path)
        graph = graph_cache.get(cache_key)
        if graph is None:
            graph = builder.build_from_json(graph_path)
            graph_cache[cache_key] = graph
        task_ids = [int(value) for value in graph.task_ids.tolist()]
        membership = [1.0 if task_id in task_set else 0.0 for task_id in task_ids]
        if sum(membership) <= 0:
            skipped["task_set_not_in_graph"] += 1
            continue

        sample = graph.clone()
        sample.candidate_task_membership = torch.tensor(
            [membership], dtype=torch.float32
        )
        sample.candidate_features = torch.tensor(
            [[_feature_value(row, field) for field in CANDIDATE_FEATURE_SCHEMA]],
            dtype=torch.float32,
        )
        sample.context_features = torch.tensor(
            [_feature_value(row, field) for field in CONTEXT_FEATURE_SCHEMA],
            dtype=torch.float32,
        )
        sample.y_selector = torch.tensor([label], dtype=torch.long)
        sample.selector_instance = instance
        sample.selector_context_hash = str(row.get("context_hash") or "")
        sample.selector_case_id = str(row.get("case_id") or "")
        sample.selector_candidate_id = str(row.get("candidate_id") or row_index)
        sample.selector_source_csv = str(input_csv)

        sample_name = f"sample_{len(samples):06d}.pt"
        torch.save(sample, sample_dir / sample_name)
        samples.append(
            {
                "path": f"samples/{sample_name}",
                "instance": instance,
                "context_hash": sample.selector_context_hash,
                "case_id": sample.selector_case_id,
                "candidate_id": sample.selector_candidate_id,
                "label": SELECTOR_CLASS_NAMES[label],
                "row_index": row_index,
            }
        )
        label_counts[SELECTOR_CLASS_NAMES[label]] += 1
        instance_counts[instance] += 1

    candidate_feature_mean, candidate_feature_std = _feature_stats(
        sample_dir,
        "candidate_features",
        len(samples),
    )
    context_feature_mean, context_feature_std = _feature_stats(
        sample_dir,
        "context_features",
        len(samples),
    )

    manifest = {
        "schema_version": "gnn_column_selector_dataset_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "source_csv": str(input_csv),
        "logical_root": str(logical_root),
        "sample_count": len(samples),
        "skipped_counts": dict(sorted(skipped.items())),
        "label_counts": dict(sorted(label_counts.items())),
        "instance_counts": dict(sorted(instance_counts.items())),
        "candidate_feature_schema": list(CANDIDATE_FEATURE_SCHEMA),
        "context_feature_schema": list(CONTEXT_FEATURE_SCHEMA),
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
        "schema_version": "gnn_column_selector_dataset_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "gnn_column_selector_dataset_built",
        "source_csv": str(input_csv),
        "output_dir": str(output_dir),
        "sample_count": len(samples),
        "label_counts": dict(sorted(label_counts.items())),
        "instance_count": len(instance_counts),
        "skipped_counts": dict(sorted(skipped.items())),
        "has_add_and_skip_labels": bool(
            label_counts.get("add", 0) > 0 and label_counts.get("skip", 0) > 0
        ),
        "all_checks_pass": bool(len(samples) > 0 and label_counts.get("add", 0) > 0),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _logical_graph_path_map(root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in root.rglob("*_logical_graph.json"):
        key = path.name.removesuffix("_logical_graph.json")
        result.setdefault(key, path)
    return result


def _selector_label(row: dict[str, str]) -> int:
    label = str(row.get("single_impact_class") or row.get("run_improvement_class") or "").strip().lower()
    if label == "improved":
        return SELECTOR_CLASS_ADD
    if label in {"noop", "worsened", "baseline"}:
        return SELECTOR_CLASS_SKIP
    return SELECTOR_CLASS_ABSTAIN


def _parse_task_set(value: Any) -> set[int]:
    text = str(value or "").strip()
    if not text:
        return set()
    normalized = text.replace(";", ",").replace("|", ",")
    tasks: set[int] = set()
    for item in normalized.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            tasks.add(int(item))
        except ValueError:
            return set()
    return tasks


def _feature_value(row: dict[str, str], field: str) -> float:
    value = row.get(field)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return 1.0
        if lowered == "false":
            return 0.0
    try:
        result = float(value) if value not in {None, ""} else 0.0
    except (TypeError, ValueError):
        result = 0.0
    if math.isnan(result) or math.isinf(result):
        return 0.0
    return float(result)


def _feature_stats(sample_dir: Path, field: str, sample_count: int) -> tuple[list[float], list[float]]:
    if sample_count <= 0:
        return [], []
    values: list[torch.Tensor] = []
    for path in sorted(sample_dir.glob("sample_*.pt")):
        sample = torch.load(path, map_location="cpu", weights_only=False)
        tensor = getattr(sample, field).to(dtype=torch.float32)
        if tensor.dim() == 2:
            tensor = tensor.squeeze(0)
        values.append(tensor)
    stacked = torch.stack(values, dim=0)
    mean = stacked.mean(dim=0)
    std = stacked.std(dim=0, unbiased=False)
    std = torch.where(std > 1.0e-12, std, torch.ones_like(std))
    return [float(value) for value in mean.tolist()], [float(value) for value in std.tolist()]


if __name__ == "__main__":
    raise SystemExit(main())
