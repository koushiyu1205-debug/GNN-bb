#!/usr/bin/env python3
"""Train ``HierarchicalOptionGAT`` on dual-center graph samples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch
from torch_geometric.loader import DataLoader

from BPC_future.learning.gnn_model import HierarchicalOptionGAT, dual_prediction_loss


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train learning dual-anchor GAT.")
    parser.add_argument("--dataset-dir", default="BPC_future/data/learning_dual/v1")
    parser.add_argument("--checkpoint-out", default="BPC_future/data/learning_dual/v1/hierarchical_option_gat.pt")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1.0e-3)
    parser.add_argument("--weight-decay", type=float, default=1.0e-5)
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--option-hidden-dim", type=int, default=128)
    parser.add_argument("--pair-edge-dim", type=int, default=128)
    parser.add_argument("--num-gnn-layers", type=int, default=2)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--huber-delta", type=float, default=0.5)
    parser.add_argument("--validation-fraction", type=float, default=0.2)
    parser.add_argument(
        "--split-by-instance",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Keep all solve-level samples from the same instance on the same side of the train/validation split.",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--metrics-out", default="", help="Optional JSON file for final train/validation metrics.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    dataset_dir = Path(args.dataset_dir)
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    samples = _load_samples(dataset_dir, manifest)
    if not samples:
        raise SystemExit("empty training dataset")
    normalizer = _normalizer_from_manifest(manifest)
    samples = [_normalize_sample(sample, normalizer) for sample in samples]

    train_samples, val_samples, split_info = _split_samples(
        samples,
        validation_fraction=float(args.validation_fraction),
        split_by_instance=bool(args.split_by_instance),
    )

    train_loader = DataLoader(train_samples, batch_size=int(args.batch_size), shuffle=True)
    val_loader = DataLoader(val_samples, batch_size=int(args.batch_size), shuffle=False) if val_samples else None

    model_config = {
        "node_dim": len(manifest["node_feature_schema"]),
        "option_dim": len(manifest["option_feature_schema"]),
        "hidden_dim": int(args.hidden_dim),
        "option_hidden_dim": int(args.option_hidden_dim),
        "pair_edge_dim": int(args.pair_edge_dim),
        "num_gnn_layers": int(args.num_gnn_layers),
        "heads": int(args.heads),
        "dropout": float(args.dropout),
        "use_layer_norm": True,
    }
    device = torch.device(str(args.device))
    model = HierarchicalOptionGAT(**model_config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(args.lr), weight_decay=float(args.weight_decay))

    best_val = float("inf")
    best_state: dict[str, Any] | None = None
    for epoch in range(1, int(args.epochs) + 1):
        train_loss = _run_epoch(model, train_loader, optimizer, device, huber_delta=float(args.huber_delta))
        val_loss = _evaluate(model, val_loader, device, huber_delta=float(args.huber_delta)) if val_loader else train_loss
        if val_loss <= best_val:
            best_val = float(val_loss)
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        print(f"epoch={epoch} train_loss={train_loss:.6f} val_loss={val_loss:.6f}", flush=True)

    if best_state is not None:
        model.load_state_dict(best_state)
    metrics = {
        "train": _prediction_metrics(model, train_loader, device, normalizer),
        "validation": _prediction_metrics(model, val_loader, device, normalizer) if val_loader else {},
    }
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "model_config": model_config,
        "node_feature_mean": manifest["node_feature_mean"],
        "node_feature_std": manifest["node_feature_std"],
        "option_feature_mean": manifest["option_feature_mean"],
        "option_feature_std": manifest["option_feature_std"],
        "label_mean": manifest["label_mean"],
        "label_std": manifest["label_std"],
        "feature_schema": {
            "node": manifest["node_feature_schema"],
            "option": manifest["option_feature_schema"],
        },
        "version": "v1",
        "training": {
            "epochs": int(args.epochs),
            "batch_size": int(args.batch_size),
            "lr": float(args.lr),
            "weight_decay": float(args.weight_decay),
            "huber_delta": float(args.huber_delta),
            "split": split_info,
            "sample_count": len(samples),
            "train_count": len(train_samples),
            "val_count": len(val_samples),
            "best_val_loss": float(best_val),
            "metrics": metrics,
        },
    }
    output = Path(args.checkpoint_out)
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, output)
    if args.metrics_out:
        metrics_path = Path(args.metrics_out)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    print(
        "final_metrics "
        f"train_mae={metrics['train'].get('mae', float('nan')):.6f} "
        f"val_mae={metrics['validation'].get('mae', float('nan')):.6f} "
        f"val_baseline_mae={metrics['validation'].get('baseline_mean_mae', float('nan')):.6f}",
        flush=True,
    )
    print(f"checkpoint written: {output}")


def _load_samples(dataset_dir: Path, manifest: dict[str, Any]) -> list[Any]:
    samples = []
    for item in manifest.get("samples", []):
        sample_path = dataset_dir / str(item["path"])
        samples.append(torch.load(sample_path, map_location="cpu", weights_only=False))
    return samples


def _normalizer_from_manifest(manifest: dict[str, Any]) -> dict[str, torch.Tensor]:
    return {
        "node_mean": torch.tensor(manifest["node_feature_mean"], dtype=torch.float32),
        "node_std": torch.tensor(manifest["node_feature_std"], dtype=torch.float32),
        "option_mean": torch.tensor(manifest["option_feature_mean"], dtype=torch.float32),
        "option_std": torch.tensor(manifest["option_feature_std"], dtype=torch.float32),
        "label_mean": torch.tensor(float(manifest["label_mean"]), dtype=torch.float32),
        "label_std": torch.tensor(float(manifest["label_std"]), dtype=torch.float32),
    }


def _normalize_sample(sample: Any, normalizer: dict[str, torch.Tensor]) -> Any:
    graph = sample.clone()
    graph.x = (graph.x - normalizer["node_mean"]) / normalizer["node_std"]
    graph.option_feat = (graph.option_feat - normalizer["option_mean"]) / normalizer["option_std"]
    graph.y_task = (graph.y_task - normalizer["label_mean"]) / normalizer["label_std"]
    graph.learning_features_normalized = True
    return graph


def _split_samples(
    samples: list[Any],
    *,
    validation_fraction: float,
    split_by_instance: bool,
) -> tuple[list[Any], list[Any], dict[str, Any]]:
    if not samples:
        return [], [], {"mode": "empty", "train_instances": 0, "validation_instances": 0}
    if not bool(split_by_instance):
        shuffled = list(samples)
        random.shuffle(shuffled)
        val_count = max(1 if len(shuffled) > 1 else 0, int(round(len(shuffled) * float(validation_fraction))))
        val_count = min(val_count, max(0, len(shuffled) - 1))
        val_samples = shuffled[:val_count]
        train_samples = shuffled[val_count:] or shuffled
        return train_samples, val_samples, {
            "mode": "sample",
            "train_instances": _distinct_instance_count(train_samples),
            "validation_instances": _distinct_instance_count(val_samples),
        }

    groups: dict[str, list[Any]] = {}
    for index, sample in enumerate(samples):
        key = str(getattr(sample, "learning_instance_path", "") or getattr(sample, "learning_instance_name", "") or index)
        groups.setdefault(key, []).append(sample)
    keys = sorted(groups)
    random.shuffle(keys)
    val_group_count = max(1 if len(keys) > 1 else 0, int(round(len(keys) * float(validation_fraction))))
    val_group_count = min(val_group_count, max(0, len(keys) - 1))
    val_keys = set(keys[:val_group_count])
    train_samples = [sample for key in keys if key not in val_keys for sample in groups[key]]
    val_samples = [sample for key in keys if key in val_keys for sample in groups[key]]
    if not train_samples:
        train_samples = list(samples)
        val_samples = []
    return train_samples, val_samples, {
        "mode": "instance",
        "train_instances": len(set(keys) - val_keys),
        "validation_instances": len(val_keys),
    }


def _distinct_instance_count(samples: list[Any]) -> int:
    return len(
        {
            str(getattr(sample, "learning_instance_path", "") or getattr(sample, "learning_instance_name", "") or index)
            for index, sample in enumerate(samples)
        }
    )


def _run_epoch(
    model: HierarchicalOptionGAT,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    *,
    huber_delta: float,
) -> float:
    model.train()
    total_loss = 0.0
    total_tasks = 0
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad(set_to_none=True)
        output = model(batch)
        loss = dual_prediction_loss(output["pred_task"], batch.y_task, huber_delta=huber_delta)
        loss.backward()
        optimizer.step()
        task_count = int(batch.y_task.numel())
        total_loss += float(loss.detach().cpu()) * task_count
        total_tasks += task_count
    return total_loss / max(1, total_tasks)


def _evaluate(
    model: HierarchicalOptionGAT,
    loader: DataLoader | None,
    device: torch.device,
    *,
    huber_delta: float,
) -> float:
    if loader is None:
        return float("inf")
    model.eval()
    total_loss = 0.0
    total_tasks = 0
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            output = model(batch)
            loss = dual_prediction_loss(output["pred_task"], batch.y_task, huber_delta=huber_delta)
            task_count = int(batch.y_task.numel())
            total_loss += float(loss.detach().cpu()) * task_count
            total_tasks += task_count
    return total_loss / max(1, total_tasks)


def _prediction_metrics(
    model: HierarchicalOptionGAT,
    loader: DataLoader | None,
    device: torch.device,
    normalizer: dict[str, torch.Tensor],
) -> dict[str, float | int]:
    if loader is None:
        return {}
    model.eval()
    pred_values: list[torch.Tensor] = []
    true_values: list[torch.Tensor] = []
    label_mean = normalizer["label_mean"].to(device)
    label_std = normalizer["label_std"].to(device)
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            output = model(batch)
            pred = output["pred_task"] * label_std + label_mean
            truth = batch.y_task * label_std + label_mean
            pred_values.append(pred.detach().cpu())
            true_values.append(truth.detach().cpu())
    if not pred_values:
        return {}
    pred_all = torch.cat(pred_values)
    true_all = torch.cat(true_values)
    error = pred_all - true_all
    baseline = torch.full_like(true_all, float(normalizer["label_mean"]))
    baseline_error = baseline - true_all
    return {
        "task_count": int(true_all.numel()),
        "mae": float(torch.mean(torch.abs(error)).item()),
        "rmse": float(torch.sqrt(torch.mean(error * error)).item()),
        "max_abs_error": float(torch.max(torch.abs(error)).item()),
        "label_mean": float(torch.mean(true_all).item()),
        "label_std": float(torch.std(true_all, unbiased=False).item()) if true_all.numel() > 1 else 0.0,
        "baseline_mean_mae": float(torch.mean(torch.abs(baseline_error)).item()),
        "baseline_mean_rmse": float(torch.sqrt(torch.mean(baseline_error * baseline_error)).item()),
    }


if __name__ == "__main__":
    main()
