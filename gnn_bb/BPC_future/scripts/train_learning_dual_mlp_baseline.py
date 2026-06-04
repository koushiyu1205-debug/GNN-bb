#!/usr/bin/env python3
"""Train a node-only MLP baseline for dual-anchor ablation diagnostics."""

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
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
import torch.nn.functional as F


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train node-only MLP dual-anchor baseline.")
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--metrics-out", required=True)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--lr", type=float, default=1.0e-3)
    parser.add_argument("--weight-decay", type=float, default=1.0e-5)
    parser.add_argument("--huber-delta", type=float, default=0.5)
    parser.add_argument("--validation-fraction", type=float, default=0.2)
    parser.add_argument("--split-by-instance", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    dataset_dir = Path(args.dataset_dir)
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    records = _load_task_records(dataset_dir, manifest)
    train_records, val_records, split = _split_records(
        records,
        validation_fraction=float(args.validation_fraction),
        split_by_instance=bool(args.split_by_instance),
    )
    normalizer = _normalizer_from_manifest(manifest)
    train_x, train_y = _records_to_tensors(train_records, normalizer)
    val_x, val_y = _records_to_tensors(val_records, normalizer) if val_records else (torch.empty(0), torch.empty(0))

    device = torch.device(str(args.device))
    model = _NodeOnlyMLP(
        input_dim=int(train_x.size(1)),
        hidden_dim=int(args.hidden_dim),
        dropout=float(args.dropout),
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(args.lr), weight_decay=float(args.weight_decay))
    loader = DataLoader(
        TensorDataset(train_x, train_y),
        batch_size=max(1, int(args.batch_size)),
        shuffle=True,
    )

    best_val = float("inf")
    best_state: dict[str, torch.Tensor] | None = None
    for epoch in range(1, int(args.epochs) + 1):
        train_loss = _run_epoch(model, loader, optimizer, device, huber_delta=float(args.huber_delta))
        val_loss = _loss_on_tensors(model, val_x, val_y, device, huber_delta=float(args.huber_delta)) if val_records else train_loss
        if val_loss <= best_val:
            best_val = float(val_loss)
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        if epoch == 1 or epoch == int(args.epochs) or epoch % 25 == 0:
            print(f"epoch={epoch} train_loss={train_loss:.6f} val_loss={val_loss:.6f}", flush=True)

    if best_state is not None:
        model.load_state_dict(best_state)
    metrics = {
        "dataset_dir": str(dataset_dir),
        "model": "node_only_mlp",
        "split": split,
        "training": {
            "epochs": int(args.epochs),
            "batch_size": int(args.batch_size),
            "hidden_dim": int(args.hidden_dim),
            "dropout": float(args.dropout),
            "lr": float(args.lr),
            "weight_decay": float(args.weight_decay),
            "huber_delta": float(args.huber_delta),
            "best_val_loss": float(best_val),
        },
        "train": _prediction_metrics(model, train_x, train_y, device, normalizer),
        "validation": _prediction_metrics(model, val_x, val_y, device, normalizer) if val_records else {},
    }
    output = Path(args.metrics_out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(metrics, indent=2, sort_keys=True))


class _NodeOnlyMLP(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(int(input_dim), int(hidden_dim)),
            nn.ReLU(),
            nn.Dropout(float(dropout)),
            nn.Linear(int(hidden_dim), int(hidden_dim)),
            nn.ReLU(),
            nn.Dropout(float(dropout)),
            nn.Linear(int(hidden_dim), 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def _load_task_records(dataset_dir: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, item in enumerate(manifest.get("samples", [])):
        sample = torch.load(dataset_dir / str(item["path"]), map_location="cpu", weights_only=False)
        x_task = sample.x[sample.task_mask].detach().cpu().to(dtype=torch.float32)
        y_task = sample.y_task.detach().cpu().to(dtype=torch.float32).view(-1)
        instance = str(getattr(sample, "learning_instance_path", "") or getattr(sample, "learning_instance_name", "") or index)
        for task_index in range(int(y_task.numel())):
            records.append(
                {
                    "instance": instance,
                    "x": x_task[task_index],
                    "y": y_task[task_index],
                }
            )
    if not records:
        raise SystemExit("empty task dataset")
    return records


def _normalizer_from_manifest(manifest: dict[str, Any]) -> dict[str, torch.Tensor]:
    return {
        "node_mean": torch.tensor(manifest["node_feature_mean"], dtype=torch.float32),
        "node_std": torch.tensor(manifest["node_feature_std"], dtype=torch.float32),
        "label_mean": torch.tensor(float(manifest["label_mean"]), dtype=torch.float32),
        "label_std": torch.tensor(float(manifest["label_std"]), dtype=torch.float32),
    }


def _records_to_tensors(records: list[dict[str, Any]], normalizer: dict[str, torch.Tensor]) -> tuple[torch.Tensor, torch.Tensor]:
    x = torch.stack([record["x"] for record in records]).to(dtype=torch.float32)
    y = torch.stack([record["y"] for record in records]).to(dtype=torch.float32).view(-1)
    x = (x - normalizer["node_mean"]) / normalizer["node_std"]
    y = (y - normalizer["label_mean"]) / normalizer["label_std"]
    return x, y


def _split_records(
    records: list[dict[str, Any]],
    *,
    validation_fraction: float,
    split_by_instance: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if not split_by_instance:
        shuffled = list(records)
        random.shuffle(shuffled)
        val_count = min(max(1, int(round(len(shuffled) * float(validation_fraction)))), len(shuffled) - 1)
        return shuffled[val_count:], shuffled[:val_count], {"mode": "task", "validation_tasks": val_count}
    groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        groups.setdefault(str(record["instance"]), []).append(record)
    keys = sorted(groups)
    random.shuffle(keys)
    val_count = min(max(1, int(round(len(keys) * float(validation_fraction)))), max(0, len(keys) - 1))
    val_keys = set(keys[:val_count])
    train = [record for key in keys if key not in val_keys for record in groups[key]]
    val = [record for key in keys if key in val_keys for record in groups[key]]
    return train, val, {"mode": "instance", "train_instances": len(set(keys) - val_keys), "validation_instances": len(val_keys)}


def _run_epoch(
    model: _NodeOnlyMLP,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    *,
    huber_delta: float,
) -> float:
    model.train()
    total = 0.0
    count = 0
    for x, y in loader:
        x = x.to(device)
        y = y.to(device)
        optimizer.zero_grad(set_to_none=True)
        pred = model(x)
        loss = F.huber_loss(pred, y, delta=float(huber_delta))
        loss.backward()
        optimizer.step()
        total += float(loss.detach().cpu()) * int(y.numel())
        count += int(y.numel())
    return total / max(1, count)


def _loss_on_tensors(
    model: _NodeOnlyMLP,
    x: torch.Tensor,
    y: torch.Tensor,
    device: torch.device,
    *,
    huber_delta: float,
) -> float:
    if y.numel() <= 0:
        return float("inf")
    model.eval()
    with torch.no_grad():
        pred = model(x.to(device))
        loss = F.huber_loss(pred, y.to(device), delta=float(huber_delta))
    return float(loss.detach().cpu())


def _prediction_metrics(
    model: _NodeOnlyMLP,
    x: torch.Tensor,
    y: torch.Tensor,
    device: torch.device,
    normalizer: dict[str, torch.Tensor],
) -> dict[str, float | int | None]:
    if y.numel() <= 0:
        return {}
    model.eval()
    with torch.no_grad():
        pred_norm = model(x.to(device)).detach().cpu()
    pred = pred_norm * normalizer["label_std"] + normalizer["label_mean"]
    truth = y.detach().cpu() * normalizer["label_std"] + normalizer["label_mean"]
    error = pred - truth
    abs_error = torch.abs(error)
    baseline = torch.full_like(truth, float(normalizer["label_mean"]))
    baseline_error = baseline - truth
    return {
        "task_count": int(truth.numel()),
        "mae": float(torch.mean(abs_error).item()),
        "rmse": float(torch.sqrt(torch.mean(error * error)).item()),
        "max_abs_error": float(torch.max(abs_error).item()),
        "label_mean": float(torch.mean(truth).item()),
        "label_std": float(torch.std(truth, unbiased=False).item()) if truth.numel() > 1 else 0.0,
        "baseline_mean_mae": float(torch.mean(torch.abs(baseline_error)).item()),
        "pearson": _corr(pred, truth),
        "spearman": _corr(_rank(pred), _rank(truth)),
    }


def _rank(values: torch.Tensor) -> torch.Tensor:
    order = torch.argsort(values)
    ranks = torch.empty_like(values, dtype=torch.float64)
    ranks[order] = torch.arange(values.numel(), dtype=torch.float64)
    return ranks


def _corr(left: torch.Tensor, right: torch.Tensor) -> float | None:
    left = left.to(dtype=torch.float64)
    right = right.to(dtype=torch.float64)
    left_centered = left - torch.mean(left)
    right_centered = right - torch.mean(right)
    denom = torch.sqrt(torch.sum(left_centered * left_centered) * torch.sum(right_centered * right_centered))
    if float(denom.item()) <= 1.0e-12:
        return None
    return float(torch.sum(left_centered * right_centered).item() / float(denom.item()))


if __name__ == "__main__":
    main()
