#!/usr/bin/env python3
"""Merge offline GAT worker-ROI graph datasets.

This utility only copies existing graph samples and rewrites manifests.  It does
not run BPC, pricing, RMP, workers, or certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import shutil
from pathlib import Path
from typing import Any

import torch


DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260615_bpc_future_gat_worker_roi_graph_dataset_merged_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dataset", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = merge_datasets(
        input_datasets=[Path(path) for path in args.input_dataset],
        output_dir=Path(args.output_dir),
        report=Path(args.report),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def merge_datasets(
    *,
    input_datasets: list[Path],
    output_dir: Path,
    report: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    if not input_datasets:
        raise ValueError("at least one input dataset is required")
    sample_dir = output_dir / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    for stale in sample_dir.glob("sample_*.pt"):
        stale.unlink()

    samples: list[dict[str, Any]] = []
    label_counts: Counter[str] = Counter()
    roi_class_counts: Counter[str] = Counter()
    instance_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    region_counts: Counter[str] = Counter()
    skipped: Counter[str] = Counter()
    input_summaries: list[dict[str, Any]] = []
    source_jsonl: list[str] = []
    sample_index = 0
    schema_reference: dict[str, Any] | None = None

    for dataset_dir in input_datasets:
        manifest_path = dataset_dir / "manifest.json"
        if not manifest_path.exists():
            skipped[f"missing_manifest:{dataset_dir}"] += 1
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema_version") != "gat_worker_roi_graph_dataset_manifest_v1":
            skipped[f"unsupported_schema:{dataset_dir}"] += 1
            continue
        if not manifest.get("diagnostic_only") or manifest.get("runs_bpc_or_pricing"):
            skipped[f"unsafe_manifest:{dataset_dir}"] += 1
            continue
        if manifest.get("official_bound_effect"):
            skipped[f"official_bound_effect:{dataset_dir}"] += 1
            continue
        if schema_reference is None:
            schema_reference = manifest
        elif (
            manifest.get("candidate_feature_schema")
            != schema_reference.get("candidate_feature_schema")
            or manifest.get("context_feature_schema")
            != schema_reference.get("context_feature_schema")
            or manifest.get("selector_class_names")
            != schema_reference.get("selector_class_names")
        ):
            skipped[f"incompatible_feature_schema:{dataset_dir}"] += 1
            continue
        source_jsonl.append(str(manifest.get("source_jsonl") or ""))
        input_summaries.append(
            {
                "dataset": str(dataset_dir),
                "sample_count": int(manifest.get("sample_count") or 0),
                "candidate_label_counts": manifest.get("candidate_label_counts") or {},
            }
        )
        for item in manifest.get("samples") or []:
            if not isinstance(item, dict):
                skipped[f"invalid_sample_item:{dataset_dir}"] += 1
                continue
            source_sample = dataset_dir / str(item.get("path") or "")
            if not source_sample.exists():
                skipped[f"missing_sample:{dataset_dir}"] += 1
                continue
            sample_name = f"sample_{sample_index:06d}.pt"
            shutil.copy2(source_sample, sample_dir / sample_name)
            copied = dict(item)
            copied["path"] = f"samples/{sample_name}"
            copied["selector_source_dataset"] = str(dataset_dir)
            samples.append(copied)
            label_counts[str(item.get("selector_label") or "")] += 1
            roi_class_counts[str(item.get("roi_class") or "")] += 1
            instance_counts[str(item.get("instance") or "")] += 1
            family_counts[str(item.get("instance_family") or "")] += 1
            region_counts[str(item.get("instance_region") or "")] += 1
            sample_index += 1

    candidate_feature_mean, candidate_feature_std = _feature_stats(sample_dir, "candidate_features")
    context_feature_mean, context_feature_std = _feature_stats(sample_dir, "context_features")
    schema_reference = schema_reference or {}
    manifest = {
        "schema_version": "gat_worker_roi_graph_dataset_manifest_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "source_jsonl": source_jsonl,
        "source_datasets": [str(path) for path in input_datasets],
        "sample_count": len(samples),
        "candidate_count": len(samples),
        "skipped_counts": dict(sorted(skipped.items())),
        "candidate_label_counts": dict(sorted(label_counts.items())),
        "roi_class_counts": dict(sorted(roi_class_counts.items())),
        "instance_counts": dict(sorted(instance_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "region_counts": dict(sorted(region_counts.items())),
        "candidate_feature_schema": list(schema_reference.get("candidate_feature_schema") or []),
        "context_feature_schema": list(schema_reference.get("context_feature_schema") or []),
        "candidate_feature_mean": candidate_feature_mean,
        "candidate_feature_std": candidate_feature_std,
        "context_feature_mean": context_feature_mean,
        "context_feature_std": context_feature_std,
        "selector_class_names": list(schema_reference.get("selector_class_names") or []),
        "label_semantics": schema_reference.get("label_semantics") or {},
        "exactness_contract": (
            "Merged offline GAT worker-ROI graph dataset. True-RC negative "
            "candidates with no/negative ROI remain delay-queue labels, not "
            "permanent reject labels."
        ),
        "samples": samples,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "manifest.json", manifest)
    summary = {
        "schema_version": "gat_worker_roi_graph_dataset_merge_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "gat_worker_roi_graph_datasets_merged",
        "output_dir": str(output_dir),
        "source_datasets": [str(path) for path in input_datasets],
        "input_summaries": input_summaries,
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
            and not skipped
        ),
    }
    _write_json(output_dir / "summary.json", summary)
    _write_report(Path(report), summary)
    return summary


def _feature_stats(sample_dir: Path, attr: str) -> tuple[list[float], list[float]]:
    values = []
    for sample_path in sorted(sample_dir.glob("sample_*.pt")):
        sample = torch.load(sample_path, map_location="cpu", weights_only=False)
        tensor = getattr(sample, attr, None)
        if tensor is None:
            continue
        values.append(tensor.float().reshape(-1, tensor.shape[-1]))
    if not values:
        return [], []
    stacked = torch.cat(values, dim=0)
    mean = stacked.mean(dim=0)
    std = stacked.std(dim=0, unbiased=False).clamp_min(1.0e-6)
    return [float(value) for value in mean.tolist()], [float(value) for value in std.tolist()]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Worker ROI Graph Dataset Merge 报告",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "合并离线 GAT worker-ROI 图数据集。该流程只复制已有样本，不运行 BPC / pricing / RMP / worker，也不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_worker_roi_graph_dataset_merge = current",
        f"status = {summary['status']}",
        f"sample_count = {summary['sample_count']}",
        f"candidate_label_counts = {summary['candidate_label_counts']}",
        f"roi_class_counts = {summary['roi_class_counts']}",
        f"delay_queue_label_count = {summary['delay_queue_label_count']}",
        f"source_datasets = {summary['source_datasets']}",
        f"skipped_counts = {summary['skipped_counts']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        "- 合并数据仍为离线诊断数据；",
        "- `abstain` 表示 DELAY_QUEUE，不是永久丢弃；",
        "- 该合并不改变默认求解路径和证书逻辑。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
