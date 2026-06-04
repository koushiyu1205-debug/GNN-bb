#!/usr/bin/env python3
"""Diagnose task-cover dual-anchor quality for a learning checkpoint."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.learning.dual_stabilizer import DualStabilizer, DualStabilizerConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose GNN dual-anchor prediction quality.")
    parser.add_argument("--dataset-dir", required=True, help="Directory containing manifest.json and sample .pt files.")
    parser.add_argument("--checkpoint", required=True, help="HierarchicalOptionGAT checkpoint to evaluate.")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--zero-tol",
        type=float,
        default=1.0e-8,
        help="Treat |true dual| <= zero-tol as a zero-dual/dead task for bias diagnostics.",
    )
    parser.add_argument("--output-json", default="", help="Optional JSON summary output.")
    parser.add_argument("--output-csv", default="", help="Optional per-sample CSV output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    samples = _load_samples(dataset_dir, manifest)
    if not samples:
        raise SystemExit("empty dataset")

    stabilizer = DualStabilizer(
        DualStabilizerConfig(
            checkpoint_path=str(args.checkpoint),
            device=str(args.device),
            debug_checks=True,
        )
    )
    sample_rows: list[dict[str, Any]] = []
    pred_values: list[torch.Tensor] = []
    true_values: list[torch.Tensor] = []
    for sample_index, sample in enumerate(samples):
        row, pred, truth = _evaluate_sample(
            stabilizer,
            sample,
            sample_index=sample_index,
            top_k=max(1, int(args.top_k)),
            zero_tol=float(args.zero_tol),
        )
        sample_rows.append(row)
        pred_values.append(pred)
        true_values.append(truth)

    pred_all = torch.cat(pred_values)
    true_all = torch.cat(true_values)
    summary = {
        "dataset_dir": str(dataset_dir),
        "checkpoint": str(args.checkpoint),
        "checkpoint_label_mean": float(stabilizer.label_mean),
        "checkpoint_label_std": float(stabilizer.label_std),
        "zero_tol": float(args.zero_tol),
        "sample_count": len(sample_rows),
        "task_count": int(true_all.numel()),
        "overall": _metrics(pred_all, true_all, top_k=max(1, int(args.top_k)), zero_tol=float(args.zero_tol)),
        "by_task_count": _group_metrics(
            sample_rows,
            pred_values,
            true_values,
            key="task_count",
            top_k=max(1, int(args.top_k)),
            zero_tol=float(args.zero_tol),
        ),
    }

    if args.output_csv:
        _write_csv(Path(args.output_csv), sample_rows)
    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print(json.dumps(summary, indent=2, sort_keys=True))


def _load_samples(dataset_dir: Path, manifest: dict[str, Any]) -> list[Any]:
    samples = []
    for item in manifest.get("samples", []):
        sample_path = dataset_dir / str(item["path"])
        samples.append(torch.load(sample_path, map_location="cpu", weights_only=False))
    return samples


def _evaluate_sample(
    stabilizer: DualStabilizer,
    sample: Any,
    *,
    sample_index: int,
    top_k: int,
    zero_tol: float,
) -> tuple[dict[str, Any], torch.Tensor, torch.Tensor]:
    anchor = stabilizer.predict_anchor(sample)
    task_ids = _int_list(getattr(sample, "task_ids"))
    pred = torch.tensor([float(anchor[int(task_id)]) for task_id in task_ids], dtype=torch.float32)
    truth = getattr(sample, "y_task").detach().cpu().to(dtype=torch.float32).view(-1)
    if pred.numel() != truth.numel():
        raise ValueError(f"sample {sample_index} prediction length {pred.numel()} != truth length {truth.numel()}")
    metrics = _metrics(pred, truth, top_k=top_k, zero_tol=zero_tol)
    row = {
        "sample_index": int(sample_index),
        "instance_name": str(getattr(sample, "learning_instance_name", "")),
        "instance_path": str(getattr(sample, "learning_instance_path", "")),
        "log_path": str(getattr(sample, "learning_log_path", "")),
        "task_count": int(truth.numel()),
        "tail_window": int(getattr(sample, "learning_tail_window", 0)),
        **metrics,
    }
    return row, pred, truth


def _metrics(pred: torch.Tensor, truth: torch.Tensor, *, top_k: int, zero_tol: float) -> dict[str, Any]:
    pred = pred.detach().cpu().to(dtype=torch.float64).view(-1)
    truth = truth.detach().cpu().to(dtype=torch.float64).view(-1)
    if pred.numel() != truth.numel() or pred.numel() == 0:
        raise ValueError("pred and truth must be non-empty vectors with equal length")
    error = pred - truth
    abs_error = torch.abs(error)
    baseline = torch.full_like(truth, float(torch.mean(truth).item()))
    baseline_error = baseline - truth
    k = min(max(1, int(top_k)), int(truth.numel()))
    pred_top = set(int(index) for index in torch.topk(pred, k=k).indices.tolist())
    true_top = set(int(index) for index in torch.topk(truth, k=k).indices.tolist())
    zero_mask = torch.abs(truth) <= abs(float(zero_tol))
    nonzero_mask = ~zero_mask
    abs_truth = torch.abs(truth)
    q95_abs_label = _quantile(abs_truth, 0.95)
    q99_abs_label = _quantile(abs_truth, 0.99)
    non_outlier_95 = abs_truth <= float(q95_abs_label)
    non_outlier_99 = abs_truth <= float(q99_abs_label)
    return {
        "mae": float(torch.mean(abs_error).item()),
        "rmse": float(torch.sqrt(torch.mean(error * error)).item()),
        "max_abs_error": float(torch.max(abs_error).item()),
        "median_abs_error": _quantile(abs_error, 0.5),
        "p90_abs_error": _quantile(abs_error, 0.9),
        "mae_without_top5pct_abs_label": _masked_mean(abs_error, non_outlier_95),
        "mae_without_top1pct_abs_label": _masked_mean(abs_error, non_outlier_99),
        "bias": float(torch.mean(error).item()),
        "label_min": float(torch.min(truth).item()),
        "label_q01": _quantile(truth, 0.01),
        "label_q05": _quantile(truth, 0.05),
        "label_q50": _quantile(truth, 0.5),
        "label_q95": _quantile(truth, 0.95),
        "label_q99": _quantile(truth, 0.99),
        "label_max": float(torch.max(truth).item()),
        "abs_label_q95": q95_abs_label,
        "abs_label_q99": q99_abs_label,
        "label_mean": float(torch.mean(truth).item()),
        "label_std": _std(truth),
        "pred_mean": float(torch.mean(pred).item()),
        "pred_std": _std(pred),
        "baseline_instance_mean_mae": float(torch.mean(torch.abs(baseline_error)).item()),
        "pearson": _corr(pred, truth),
        "spearman": _corr(_rank(pred), _rank(truth)),
        "top_k": int(k),
        "top_k_overlap": len(pred_top & true_top) / float(k),
        "sign_accuracy": _sign_accuracy(pred, truth),
        "zero_tol": abs(float(zero_tol)),
        "zero_dual_count": int(torch.sum(zero_mask).item()),
        "zero_dual_fraction": float(torch.mean(zero_mask.to(dtype=torch.float64)).item()),
        "zero_dual_pred_mean": _masked_mean(pred, zero_mask),
        "zero_dual_pred_abs_mean": _masked_mean(torch.abs(pred), zero_mask),
        "zero_dual_pred_p90_abs": _masked_quantile(torch.abs(pred), zero_mask, 0.9),
        "zero_dual_pred_gt_1_count": _masked_count(torch.abs(pred) > 1.0, zero_mask),
        "zero_dual_pred_gt_5_count": _masked_count(torch.abs(pred) > 5.0, zero_mask),
        "zero_dual_pred_gt_10_count": _masked_count(torch.abs(pred) > 10.0, zero_mask),
        "nonzero_dual_count": int(torch.sum(nonzero_mask).item()),
        "nonzero_mae": _masked_mean(abs_error, nonzero_mask),
    }


def _group_metrics(
    rows: list[dict[str, Any]],
    pred_values: list[torch.Tensor],
    true_values: list[torch.Tensor],
    *,
    key: str,
    top_k: int,
    zero_tol: float,
) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        groups.setdefault(str(row[key]), []).append(index)
    result: dict[str, dict[str, Any]] = {}
    for group_key, indices in sorted(groups.items()):
        pred = torch.cat([pred_values[index] for index in indices])
        truth = torch.cat([true_values[index] for index in indices])
        result[group_key] = {
            "sample_count": len(indices),
            "task_count": int(truth.numel()),
            **_metrics(pred, truth, top_k=top_k, zero_tol=zero_tol),
        }
    return result


def _rank(values: torch.Tensor) -> torch.Tensor:
    order = torch.argsort(values)
    ranks = torch.empty_like(values, dtype=torch.float64)
    ranks[order] = torch.arange(values.numel(), dtype=torch.float64, device=values.device)
    return ranks


def _corr(left: torch.Tensor, right: torch.Tensor) -> float | None:
    left = left.to(dtype=torch.float64)
    right = right.to(dtype=torch.float64)
    left_centered = left - torch.mean(left)
    right_centered = right - torch.mean(right)
    denom = torch.sqrt(torch.sum(left_centered * left_centered) * torch.sum(right_centered * right_centered))
    if float(denom.item()) <= 1.0e-12:
        return None
    value = float(torch.sum(left_centered * right_centered).item() / float(denom.item()))
    if not math.isfinite(value):
        return None
    return value


def _std(values: torch.Tensor) -> float:
    return float(torch.std(values, unbiased=False).item()) if values.numel() > 1 else 0.0


def _quantile(values: torch.Tensor, q: float) -> float:
    return float(torch.quantile(values.to(dtype=torch.float64), float(q)).item())


def _masked_mean(values: torch.Tensor, mask: torch.Tensor) -> float | None:
    selected = values[mask]
    if selected.numel() <= 0:
        return None
    return float(torch.mean(selected.to(dtype=torch.float64)).item())


def _masked_quantile(values: torch.Tensor, mask: torch.Tensor, q: float) -> float | None:
    selected = values[mask]
    if selected.numel() <= 0:
        return None
    return _quantile(selected, q)


def _masked_count(mask: torch.Tensor, group_mask: torch.Tensor) -> int:
    return int(torch.sum(mask & group_mask).item())


def _sign_accuracy(pred: torch.Tensor, truth: torch.Tensor) -> float:
    pred_sign = torch.sign(pred)
    truth_sign = torch.sign(truth)
    return float(torch.mean((pred_sign == truth_sign).to(dtype=torch.float64)).item())


def _int_list(value: Any) -> list[int]:
    if isinstance(value, torch.Tensor):
        return [int(item) for item in value.detach().cpu().tolist()]
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return [int(item) for item in value]
    raise ValueError("task_ids must be a tensor or iterable of ints")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
