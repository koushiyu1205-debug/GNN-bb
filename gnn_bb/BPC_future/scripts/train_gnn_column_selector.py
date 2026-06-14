#!/usr/bin/env python3
"""Train the context-aware GNN column impact selector.

The trained model is a heuristic add/skip/abstain predictor.  It is not a
pricing oracle and must not be used for certificates or official lower bounds.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import random
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.learning.column_selector import (
    SELECTOR_CLASS_ADD,
    SELECTOR_CLASS_NAMES,
    ContextAwareColumnSelector,
    column_selector_loss,
)


DEFAULT_DATASET_DIR = Path("BPC_future/data/column_selector/v1")
DEFAULT_CHECKPOINT = Path("BPC_future/data/column_selector/v1/context_aware_column_selector.pt")
DEFAULT_METRICS = Path("BPC_future/results/gnn_column_selector_training_20260614/summary.json")


@dataclass(frozen=True)
class _Split:
    train: list[Any]
    validation: list[Any]
    info: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--checkpoint-out", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--metrics-out", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--lr", type=float, default=1.0e-3)
    parser.add_argument("--weight-decay", type=float, default=1.0e-5)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--option-hidden-dim", type=int, default=64)
    parser.add_argument("--pair-edge-dim", type=int, default=64)
    parser.add_argument("--selector-hidden-dim", type=int, default=64)
    parser.add_argument("--num-gnn-layers", type=int, default=1)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--validation-fraction", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=17)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = train_selector(args)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def train_selector(args: argparse.Namespace) -> dict[str, Any]:
    random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    dataset_dir = Path(args.dataset_dir)
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    samples = [_load_sample(dataset_dir / item["path"]) for item in manifest.get("samples", [])]
    if not samples:
        raise SystemExit("empty column selector dataset")
    samples = [_normalize_sample(sample, manifest) for sample in samples]
    split = _split_samples(
        samples,
        validation_fraction=float(args.validation_fraction),
        seed=int(args.seed),
    )
    first = samples[0]
    model_config = {
        "node_dim": int(first.x.size(1)),
        "option_dim": int(first.option_feat.size(1)),
        "candidate_feature_dim": len(manifest["candidate_feature_schema"]),
        "context_feature_dim": len(manifest["context_feature_schema"]),
        "hidden_dim": int(args.hidden_dim),
        "option_hidden_dim": int(args.option_hidden_dim),
        "pair_edge_dim": int(args.pair_edge_dim),
        "num_gnn_layers": int(args.num_gnn_layers),
        "heads": int(args.heads),
        "dropout": float(args.dropout),
        "selector_hidden_dim": int(args.selector_hidden_dim),
        "use_layer_norm": True,
    }
    device = torch.device(str(args.device))
    model = ContextAwareColumnSelector(**model_config).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(args.lr),
        weight_decay=float(args.weight_decay),
    )
    class_weights = _class_weights(split.train, device=device)

    best_val_loss = float("inf")
    best_state: dict[str, torch.Tensor] | None = None
    history: list[dict[str, float]] = []
    for epoch in range(1, int(args.epochs) + 1):
        train_loss = _run_epoch(model, split.train, optimizer, device, class_weights)
        validation_loss = _evaluate_loss(model, split.validation, device, class_weights)
        history.append(
            {
                "epoch": float(epoch),
                "train_loss": float(train_loss),
                "validation_loss": float(validation_loss),
            }
        )
        if validation_loss <= best_val_loss:
            best_val_loss = float(validation_loss)
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        print(
            f"epoch={epoch} train_loss={train_loss:.6f} validation_loss={validation_loss:.6f}",
            flush=True,
        )

    if best_state is not None:
        model.load_state_dict(best_state)
    train_metrics = _classification_metrics(model, split.train, device)
    validation_metrics = _classification_metrics(model, split.validation, device)
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "model_config": model_config,
        "candidate_feature_schema": manifest["candidate_feature_schema"],
        "context_feature_schema": manifest["context_feature_schema"],
        "candidate_feature_mean": manifest["candidate_feature_mean"],
        "candidate_feature_std": manifest["candidate_feature_std"],
        "context_feature_mean": manifest["context_feature_mean"],
        "context_feature_std": manifest["context_feature_std"],
        "selector_class_names": list(SELECTOR_CLASS_NAMES),
        "version": "context_aware_column_selector_v1",
        "exactness_contract": (
            "Heuristic RMP-impact predictor only; never a pricing oracle, "
            "certificate source, or official lower-bound source."
        ),
        "training": {
            "epochs": int(args.epochs),
            "lr": float(args.lr),
            "weight_decay": float(args.weight_decay),
            "split": split.info,
            "history": history,
            "train_metrics": train_metrics,
            "validation_metrics": validation_metrics,
        },
    }
    args.checkpoint_out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, args.checkpoint_out)
    summary = {
        "schema_version": "gnn_column_selector_training_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "gnn_column_selector_trained",
        "dataset_dir": str(dataset_dir),
        "checkpoint_out": str(args.checkpoint_out),
        "sample_count": len(samples),
        "train_count": len(split.train),
        "validation_count": len(split.validation),
        "split": split.info,
        "train_metrics": train_metrics,
        "validation_metrics": validation_metrics,
        "best_validation_loss": best_val_loss,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "all_checks_pass": bool(
            train_metrics.get("total", 0) > 0
            and validation_metrics.get("total", 0) > 0
            and checkpoint["selector_class_names"] == list(SELECTOR_CLASS_NAMES)
        ),
    }
    args.metrics_out.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_out.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def _load_sample(path: Path) -> Any:
    return torch.load(path, map_location="cpu", weights_only=False)


def _normalize_sample(sample: Any, manifest: dict[str, Any]) -> Any:
    graph = sample.clone()
    graph.candidate_features = _normalize_tensor(
        graph.candidate_features,
        manifest["candidate_feature_mean"],
        manifest["candidate_feature_std"],
    )
    graph.context_features = _normalize_tensor(
        graph.context_features,
        manifest["context_feature_mean"],
        manifest["context_feature_std"],
    )
    return graph


def _normalize_tensor(tensor: torch.Tensor, mean: list[float], std: list[float]) -> torch.Tensor:
    mean_tensor = torch.tensor(mean, dtype=torch.float32)
    std_tensor = torch.tensor(std, dtype=torch.float32)
    return (tensor.to(dtype=torch.float32) - mean_tensor) / std_tensor


def _split_samples(samples: list[Any], *, validation_fraction: float, seed: int) -> _Split:
    by_instance: dict[str, list[Any]] = {}
    for sample in samples:
        by_instance.setdefault(str(sample.selector_instance), []).append(sample)
    instances = sorted(by_instance)
    rng = random.Random(int(seed))
    rng.shuffle(instances)
    validation_count = max(1 if len(instances) > 1 else 0, int(round(len(instances) * float(validation_fraction))))
    validation_count = min(validation_count, max(0, len(instances) - 1))
    validation_instances = set(instances[:validation_count])
    train = [
        sample
        for instance, instance_samples in by_instance.items()
        if instance not in validation_instances
        for sample in instance_samples
    ]
    validation = [
        sample
        for instance, instance_samples in by_instance.items()
        if instance in validation_instances
        for sample in instance_samples
    ]
    if not validation and len(samples) > 1:
        shuffled = list(samples)
        rng.shuffle(shuffled)
        validation = shuffled[:1]
        train = shuffled[1:]
        return _Split(
            train=train,
            validation=validation,
            info={"mode": "row_fallback", "validation_count": len(validation)},
        )
    return _Split(
        train=train,
        validation=validation,
        info={
            "mode": "instance",
            "train_instances": sorted(set(instances) - validation_instances),
            "validation_instances": sorted(validation_instances),
        },
    )


def _class_weights(samples: list[Any], *, device: torch.device) -> torch.Tensor:
    counts = torch.zeros(len(SELECTOR_CLASS_NAMES), dtype=torch.float32)
    for sample in samples:
        labels = sample.y_selector.to(dtype=torch.long)
        for label in labels.tolist():
            counts[int(label)] += 1.0
    positive = counts > 0
    weights = torch.ones_like(counts)
    if bool(torch.any(positive)):
        weights[positive] = counts[positive].sum() / torch.clamp(counts[positive], min=1.0)
        weights = weights / torch.clamp(weights[positive].mean(), min=1.0e-12)
    return weights.to(device)


def _run_epoch(
    model: ContextAwareColumnSelector,
    samples: list[Any],
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    class_weights: torch.Tensor,
) -> float:
    model.train()
    shuffled = list(samples)
    random.shuffle(shuffled)
    total = 0.0
    count = 0
    for sample in shuffled:
        optimizer.zero_grad(set_to_none=True)
        loss = _sample_loss(model, sample, device, class_weights)
        loss.backward()
        optimizer.step()
        total += float(loss.detach().cpu())
        count += 1
    return total / max(1, count)


def _evaluate_loss(
    model: ContextAwareColumnSelector,
    samples: list[Any],
    device: torch.device,
    class_weights: torch.Tensor,
) -> float:
    if not samples:
        return float("inf")
    model.eval()
    total = 0.0
    with torch.no_grad():
        for sample in samples:
            total += float(_sample_loss(model, sample, device, class_weights).detach().cpu())
    return total / max(1, len(samples))


def _sample_loss(
    model: ContextAwareColumnSelector,
    sample: Any,
    device: torch.device,
    class_weights: torch.Tensor,
) -> torch.Tensor:
    sample = sample.to(device)
    output = model(
        sample,
        sample.candidate_task_membership,
        sample.candidate_features,
        sample.context_features,
    )
    return column_selector_loss(output["logits"], sample.y_selector.to(device), class_weights)


def _classification_metrics(
    model: ContextAwareColumnSelector,
    samples: list[Any],
    device: torch.device,
) -> dict[str, Any]:
    if not samples:
        return {"total": 0}
    model.eval()
    confusion = torch.zeros(
        (len(SELECTOR_CLASS_NAMES), len(SELECTOR_CLASS_NAMES)),
        dtype=torch.long,
    )
    with torch.no_grad():
        for sample in samples:
            sample = sample.to(device)
            output = model(
                sample,
                sample.candidate_task_membership,
                sample.candidate_features,
                sample.context_features,
            )
            pred = output["logits"].argmax(dim=1).cpu()
            actual = sample.y_selector.cpu().long()
            for truth, guess in zip(actual.tolist(), pred.tolist()):
                confusion[int(truth), int(guess)] += 1
    total = int(confusion.sum().item())
    correct = int(confusion.diag().sum().item())
    add_tp = int(confusion[SELECTOR_CLASS_ADD, SELECTOR_CLASS_ADD].item())
    add_pred = int(confusion[:, SELECTOR_CLASS_ADD].sum().item())
    add_actual = int(confusion[SELECTOR_CLASS_ADD, :].sum().item())
    return {
        "total": total,
        "accuracy": None if total <= 0 else correct / float(total),
        "confusion": confusion.tolist(),
        "add_precision": None if add_pred <= 0 else add_tp / float(add_pred),
        "add_recall": None if add_actual <= 0 else add_tp / float(add_actual),
        "class_names": list(SELECTOR_CLASS_NAMES),
    }


if __name__ == "__main__":
    raise SystemExit(main())
