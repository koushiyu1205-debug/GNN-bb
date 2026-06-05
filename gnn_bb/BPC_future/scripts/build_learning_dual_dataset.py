#!/usr/bin/env python3
"""Build GNN dual-anchor training samples from journey dual trace logs."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import heapq
import json
from pathlib import Path
import random
import sys
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.core.data import load_future_data
from BPC_future.learning.graph_builder import (
    DEFAULT_NODE_FEATURE_SCHEMA,
    DEFAULT_OPTION_FEATURE_SCHEMA,
    FutureGraphBuilder,
)


@dataclass(frozen=True)
class _TraceGroup:
    instance_path: Path
    log_path: Path
    records: list[dict[str, Any]]
    trace_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build learning dual-center dataset from BPC_future JSONL logs.")
    parser.add_argument("--logs", nargs="+", required=True, help="JSONL log files or directories containing logs.")
    parser.add_argument("--output-dir", default="BPC_future/data/learning_dual/v1")
    parser.add_argument("--instance-dir", default=".")
    parser.add_argument("--tail-window", type=int, default=10)
    parser.add_argument("--max-bytes", type=int, default=200 * 1024**3)
    parser.add_argument("--min-traces", type=int, default=1)
    parser.add_argument("--require-finish-status", default="", help="Skip log files whose finish status differs.")
    parser.add_argument(
        "--max-depth",
        type=int,
        default=0,
        help="Maximum branch depth to include in labels. Default 0 keeps root-node dual centers only; use -1 to include all depths.",
    )
    parser.add_argument(
        "--zero-label-tol",
        type=float,
        default=1.0e-8,
        help="Manifest diagnostic tolerance for exact-zero task-cover dual labels.",
    )
    parser.add_argument(
        "--near-zero-label-tol",
        type=float,
        default=1.0,
        help="Manifest diagnostic tolerance for near-zero task-cover dual labels.",
    )
    parser.add_argument(
        "--synthetic-zero-sample-fraction",
        type=float,
        default=0.0,
        help=(
            "Optional experimental zero-anchor coverage. For this fraction of real graphs, "
            "write a low-weight clone whose task labels are all zero. Defaults to disabled."
        ),
    )
    parser.add_argument(
        "--synthetic-zero-sample-weight",
        type=float,
        default=0.05,
        help="Per-task loss weight stored on synthetic zero-anchor clones.",
    )
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(int(args.seed))
    output_dir = Path(args.output_dir)
    sample_dir = output_dir / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    traces = _collect_traces(
        [Path(item) for item in args.logs],
        require_finish_status=str(args.require_finish_status or ""),
        max_depth=int(args.max_depth),
        tail_window=max(1, int(args.tail_window)),
    )
    if not traces:
        raise SystemExit("no journey_learning_dual_trace events found")

    builder = FutureGraphBuilder()
    node_stats = _RunningStats(len(DEFAULT_NODE_FEATURE_SCHEMA))
    option_stats = _RunningStats(len(DEFAULT_OPTION_FEATURE_SCHEMA))
    label_stats = _RunningStats(1)
    samples: list[dict[str, Any]] = []
    total_bytes = 0
    next_sample_index = 0
    real_sample_count = 0
    synthetic_zero_sample_count = 0
    zero_label_count = 0
    near_zero_label_count = 0
    total_label_count = 0

    for group in sorted(traces, key=lambda item: (str(item.instance_path), str(item.log_path))):
        if group.trace_count < int(args.min_traces):
            continue
        selected = group.records[-max(1, int(args.tail_window)) :]
        data = load_future_data(str(group.instance_path), instance_dir=args.instance_dir)
        graph = builder.build_from_future_data(data)
        task_ids = [int(task) for task in graph.task_ids.tolist()]
        label_by_task = _average_cover_duals(selected, task_ids)
        y_task = torch.tensor([float(label_by_task[int(task)]) for task in graph.task_ids.tolist()], dtype=torch.float32)
        graph.y_task = y_task
        graph.y_task_weight = torch.ones_like(y_task)
        graph.learning_instance_name = str(data.name)
        graph.learning_instance_path = str(data.instance_path)
        graph.learning_log_path = str(group.log_path)
        graph.learning_label_source = "tail_average_rmp_cover_dual"
        graph.learning_tail_window = int(len(selected))

        node_stats.update(graph.x)
        option_stats.update(graph.option_feat)
        label_stats.update(y_task.view(-1, 1))
        real_sample_count += 1
        zero_label_count += int(torch.sum(torch.abs(y_task) <= abs(float(args.zero_label_tol))).item())
        near_zero_label_count += int(torch.sum(torch.abs(y_task) <= abs(float(args.near_zero_label_tol))).item())
        total_label_count += int(y_task.numel())

        total_bytes, next_sample_index = _write_sample(
            graph,
            samples,
            sample_dir=sample_dir,
            output_dir=output_dir,
            sample_index=next_sample_index,
            total_bytes=total_bytes,
            max_bytes=int(args.max_bytes),
            instance_path=str(data.instance_path),
            log_path=str(group.log_path),
            instance_name=str(data.name),
            trace_count=int(group.trace_count),
            tail_window=int(len(selected)),
            is_synthetic=False,
        )
        if _include_synthetic_zero_sample(float(args.synthetic_zero_sample_fraction), rng):
            synthetic = graph.clone()
            synthetic.y_task = torch.zeros_like(y_task)
            synthetic.y_task_weight = torch.full_like(y_task, max(0.0, float(args.synthetic_zero_sample_weight)))
            synthetic.learning_label_source = "synthetic_zero_dual_regularizer"
            total_bytes, next_sample_index = _write_sample(
                synthetic,
                samples,
                sample_dir=sample_dir,
                output_dir=output_dir,
                sample_index=next_sample_index,
                total_bytes=total_bytes,
                max_bytes=int(args.max_bytes),
                instance_path=str(data.instance_path),
                log_path=str(group.log_path),
                instance_name=str(data.name),
                trace_count=int(group.trace_count),
                tail_window=int(len(selected)),
                is_synthetic=True,
            )
            synthetic_zero_sample_count += 1

    if not samples:
        raise SystemExit("no samples written; check min-traces and log inputs")

    manifest = {
        "version": "v1",
        "sample_count": len(samples),
        "real_sample_count": int(real_sample_count),
        "synthetic_zero_sample_count": int(synthetic_zero_sample_count),
        "total_bytes": int(total_bytes),
        "node_feature_schema": list(DEFAULT_NODE_FEATURE_SCHEMA),
        "option_feature_schema": list(DEFAULT_OPTION_FEATURE_SCHEMA),
        "node_feature_mean": node_stats.mean(),
        "node_feature_std": node_stats.std(),
        "option_feature_mean": option_stats.mean(),
        "option_feature_std": option_stats.std(),
        "label_mean": label_stats.mean()[0],
        "label_std": label_stats.std()[0],
        "label_zero_tol": abs(float(args.zero_label_tol)),
        "label_near_zero_tol": abs(float(args.near_zero_label_tol)),
        "label_count": int(total_label_count),
        "zero_label_count": int(zero_label_count),
        "near_zero_label_count": int(near_zero_label_count),
        "zero_label_fraction": float(zero_label_count) / float(max(1, total_label_count)),
        "near_zero_label_fraction": float(near_zero_label_count) / float(max(1, total_label_count)),
        "synthetic_zero_sample_fraction": max(0.0, min(1.0, float(args.synthetic_zero_sample_fraction))),
        "synthetic_zero_sample_weight": max(0.0, float(args.synthetic_zero_sample_weight)),
        "samples": samples,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {len(samples)} samples to {output_dir} ({total_bytes} bytes)")


def _collect_traces(
    paths: list[Path],
    *,
    require_finish_status: str = "",
    max_depth: int | None = 0,
    tail_window: int | None = None,
) -> list[_TraceGroup]:
    result: list[_TraceGroup] = []
    max_records = None if tail_window is None else max(1, int(tail_window))
    for path in paths:
        files = sorted(path.rglob("*.jsonl")) if path.is_dir() else [path]
        for file_path in files:
            records_by_instance: dict[Path, list[Any]] = {}
            trace_counts: dict[Path, int] = {}
            finish: dict[str, Any] | None = None
            sequence = 0
            for record in _iter_jsonl_records(file_path):
                event = record.get("event")
                if event == "finish":
                    finish = record
                    continue
                if event != "journey_learning_dual_trace":
                    continue
                if max_depth is not None and int(max_depth) >= 0:
                    if int(record.get("depth", 0)) > int(max_depth):
                        continue
                instance_path = Path(str(record["instance_path"]))
                trace_counts[instance_path] = trace_counts.get(instance_path, 0) + 1
                if max_records is None:
                    records_by_instance.setdefault(instance_path, []).append(record)
                else:
                    heap = records_by_instance.setdefault(instance_path, [])
                    # 只保留排序意义上的最后 tail_window 条 trace，避免大日志把内存吃满。
                    entry = (_trace_sort_key(record), sequence, record)
                    if len(heap) < max_records:
                        heapq.heappush(heap, entry)
                    elif entry[:2] > heap[0][:2]:
                        heapq.heapreplace(heap, entry)
                sequence += 1
            if require_finish_status:
                if finish is None or str(finish.get("status", "")) != str(require_finish_status):
                    continue
            for instance_path, stored_records in records_by_instance.items():
                if max_records is None:
                    trace_records = list(stored_records)
                else:
                    trace_records = [entry[2] for entry in stored_records]
                trace_records.sort(
                    key=_trace_sort_key
                )
                result.append(
                    _TraceGroup(
                        instance_path=instance_path,
                        log_path=file_path,
                        records=trace_records,
                        trace_count=int(trace_counts.get(instance_path, len(trace_records))),
                    )
                )
    return result


def _trace_sort_key(record: dict[str, Any]) -> tuple[int, int, float]:
    return (
        int(record.get("node_id", 0)),
        int(record.get("cg_iter", 0)),
        float(record.get("time", 0.0)),
    )


def _iter_jsonl_records(file_path: Path) -> Iterator[dict[str, Any]]:
    with file_path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            if raw.strip():
                yield json.loads(raw)


def _average_cover_duals(records: list[dict[str, Any]], task_ids: list[int] | None = None) -> dict[int, float]:
    sums: dict[int, float] = {}
    counts: dict[int, int] = {}
    if task_ids is None:
        inferred: set[int] = set()
        for record in records:
            cover = record.get("cover", {})
            if not isinstance(cover, dict):
                raise ValueError("dual trace cover field must be a dict")
            inferred.update(int(raw_task) for raw_task in cover)
        task_ids = sorted(inferred)
    for task in task_ids:
        sums[int(task)] = 0.0
        counts[int(task)] = 0
    for record in records:
        cover = record.get("cover", {})
        if not isinstance(cover, dict):
            raise ValueError("dual trace cover field must be a dict")
        for task in task_ids:
            # 有些日志格式会省略值为 0 的 cover dual。这里按“缺失即 0”
            # 处理，避免把死节点标签从训练集里系统性删掉。
            sums[int(task)] = sums.get(int(task), 0.0) + float(cover.get(str(int(task)), cover.get(int(task), 0.0)))
            counts[int(task)] = counts.get(int(task), 0) + 1
    return {task: sums[task] / float(counts[task]) for task in sums if counts[task] > 0}


def _include_synthetic_zero_sample(fraction: float, rng: random.Random) -> bool:
    clipped = max(0.0, min(1.0, float(fraction)))
    return clipped > 0.0 and rng.random() < clipped


def _write_sample(
    graph: Any,
    samples: list[dict[str, Any]],
    *,
    sample_dir: Path,
    output_dir: Path,
    sample_index: int,
    total_bytes: int,
    max_bytes: int,
    instance_path: str,
    log_path: str,
    instance_name: str,
    trace_count: int,
    tail_window: int,
    is_synthetic: bool,
) -> tuple[int, int]:
    sample_path = sample_dir / f"sample_{sample_index:05d}.pt"
    torch.save(graph, sample_path)
    size = sample_path.stat().st_size
    updated_bytes = int(total_bytes) + int(size)
    if updated_bytes > int(max_bytes):
        raise SystemExit(f"dataset size limit exceeded: {updated_bytes} bytes > {int(max_bytes)} bytes")
    samples.append(
        {
            "path": str(sample_path.relative_to(output_dir)),
            "instance_path": instance_path,
            "log_path": log_path,
            "instance_name": instance_name,
            "task_count": int(graph.task_ids.numel()),
            "node_count": int(graph.x.size(0)),
            "pair_count": int(graph.pair_edge_index.size(1)),
            "option_count": int(graph.option_feat.size(0)),
            "trace_count": int(trace_count),
            "tail_window": int(tail_window),
            "label_source": str(getattr(graph, "learning_label_source", "")),
            "synthetic": bool(is_synthetic),
            "bytes": int(size),
        }
    )
    return updated_bytes, int(sample_index) + 1


class _RunningStats:
    def __init__(self, dim: int) -> None:
        self.count = 0
        self.sum = torch.zeros(dim, dtype=torch.float64)
        self.sumsq = torch.zeros(dim, dtype=torch.float64)

    def update(self, tensor: torch.Tensor) -> None:
        values = tensor.detach().cpu().to(dtype=torch.float64)
        if values.dim() == 1:
            values = values.view(-1, self.sum.numel())
        self.count += int(values.size(0))
        self.sum += values.sum(dim=0)
        self.sumsq += (values * values).sum(dim=0)

    def mean(self) -> list[float]:
        if self.count <= 0:
            raise ValueError("cannot compute mean with zero observations")
        return [float(value) for value in (self.sum / float(self.count)).tolist()]

    def std(self) -> list[float]:
        if self.count <= 0:
            raise ValueError("cannot compute std with zero observations")
        mean = self.sum / float(self.count)
        var = torch.clamp(self.sumsq / float(self.count) - mean * mean, min=1.0e-12)
        return [float(value) for value in torch.sqrt(var).tolist()]


if __name__ == "__main__":
    main()
