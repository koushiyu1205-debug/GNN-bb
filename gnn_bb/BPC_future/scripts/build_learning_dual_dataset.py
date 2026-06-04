#!/usr/bin/env python3
"""Build GNN dual-anchor training samples from journey dual trace logs."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any

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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    sample_dir = output_dir / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    traces = _collect_traces(
        [Path(item) for item in args.logs],
        require_finish_status=str(args.require_finish_status or ""),
        max_depth=int(args.max_depth),
    )
    if not traces:
        raise SystemExit("no journey_learning_dual_trace events found")

    builder = FutureGraphBuilder()
    node_stats = _RunningStats(len(DEFAULT_NODE_FEATURE_SCHEMA))
    option_stats = _RunningStats(len(DEFAULT_OPTION_FEATURE_SCHEMA))
    label_stats = _RunningStats(1)
    samples: list[dict[str, Any]] = []
    total_bytes = 0

    for sample_index, group in enumerate(
        sorted(traces, key=lambda item: (str(item.instance_path), str(item.log_path)))
    ):
        if len(group.records) < int(args.min_traces):
            continue
        selected = group.records[-max(1, int(args.tail_window)) :]
        label_by_task = _average_cover_duals(selected)
        data = load_future_data(str(group.instance_path), instance_dir=args.instance_dir)
        graph = builder.build_from_future_data(data)
        y_task = torch.tensor([float(label_by_task[int(task)]) for task in graph.task_ids.tolist()], dtype=torch.float32)
        graph.y_task = y_task
        graph.learning_instance_name = str(data.name)
        graph.learning_instance_path = str(data.instance_path)
        graph.learning_log_path = str(group.log_path)
        graph.learning_label_source = "tail_average_rmp_cover_dual"
        graph.learning_tail_window = int(len(selected))

        node_stats.update(graph.x)
        option_stats.update(graph.option_feat)
        label_stats.update(y_task.view(-1, 1))

        sample_path = sample_dir / f"sample_{sample_index:05d}.pt"
        torch.save(graph, sample_path)
        size = sample_path.stat().st_size
        total_bytes += int(size)
        if total_bytes > int(args.max_bytes):
            raise SystemExit(
                f"dataset size limit exceeded: {total_bytes} bytes > {int(args.max_bytes)} bytes"
            )
        samples.append(
            {
                "path": str(sample_path.relative_to(output_dir)),
                "instance_path": str(data.instance_path),
                "log_path": str(group.log_path),
                "instance_name": str(data.name),
                "task_count": int(graph.task_ids.numel()),
                "node_count": int(graph.x.size(0)),
                "pair_count": int(graph.pair_edge_index.size(1)),
                "option_count": int(graph.option_feat.size(0)),
                "trace_count": int(len(group.records)),
                "tail_window": int(len(selected)),
                "bytes": int(size),
            }
        )

    if not samples:
        raise SystemExit("no samples written; check min-traces and log inputs")

    manifest = {
        "version": "v1",
        "sample_count": len(samples),
        "total_bytes": int(total_bytes),
        "node_feature_schema": list(DEFAULT_NODE_FEATURE_SCHEMA),
        "option_feature_schema": list(DEFAULT_OPTION_FEATURE_SCHEMA),
        "node_feature_mean": node_stats.mean(),
        "node_feature_std": node_stats.std(),
        "option_feature_mean": option_stats.mean(),
        "option_feature_std": option_stats.std(),
        "label_mean": label_stats.mean()[0],
        "label_std": label_stats.std()[0],
        "samples": samples,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {len(samples)} samples to {output_dir} ({total_bytes} bytes)")


def _collect_traces(
    paths: list[Path],
    *,
    require_finish_status: str = "",
    max_depth: int | None = 0,
) -> list[_TraceGroup]:
    result: list[_TraceGroup] = []
    for path in paths:
        files = sorted(path.rglob("*.jsonl")) if path.is_dir() else [path]
        for file_path in files:
            records = [json.loads(raw) for raw in file_path.read_text(encoding="utf-8").splitlines() if raw.strip()]
            if require_finish_status:
                finish = next((record for record in reversed(records) if record.get("event") == "finish"), None)
                if finish is None or str(finish.get("status", "")) != str(require_finish_status):
                    continue
            records_by_instance: dict[Path, list[dict[str, Any]]] = {}
            for record in records:
                if record.get("event") != "journey_learning_dual_trace":
                    continue
                if max_depth is not None and int(max_depth) >= 0:
                    if int(record.get("depth", 0)) > int(max_depth):
                        continue
                instance_path = Path(str(record["instance_path"]))
                records_by_instance.setdefault(instance_path, []).append(record)
            for instance_path, trace_records in records_by_instance.items():
                trace_records.sort(
                    key=lambda item: (
                        int(item.get("node_id", 0)),
                        int(item.get("cg_iter", 0)),
                        float(item.get("time", 0.0)),
                    )
                )
                result.append(
                    _TraceGroup(
                        instance_path=instance_path,
                        log_path=file_path,
                        records=trace_records,
                    )
                )
    return result


def _average_cover_duals(records: list[dict[str, Any]]) -> dict[int, float]:
    sums: dict[int, float] = {}
    counts: dict[int, int] = {}
    for record in records:
        cover = record.get("cover", {})
        if not isinstance(cover, dict):
            raise ValueError("dual trace cover field must be a dict")
        for raw_task, raw_value in cover.items():
            task = int(raw_task)
            sums[task] = sums.get(task, 0.0) + float(raw_value)
            counts[task] = counts.get(task, 0) + 1
    return {task: sums[task] / float(counts[task]) for task in sums}


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
