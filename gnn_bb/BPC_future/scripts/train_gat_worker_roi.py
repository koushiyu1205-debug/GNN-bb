#!/usr/bin/env python3
"""Train a GAT scheduler on audited worker trajectory-ROI labels.

This is the production-boundary-safe training entry for the worker ROI dataset
from ``build_gat_worker_roi_graph_dataset.py``.  Labels must come from paired
worker A/B trajectory ROI, not from reduced cost, GAT score, kNN/OOD decisions,
or same-run proxy labels.
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
    SELECTOR_CLASS_ABSTAIN,
    SELECTOR_CLASS_ADD,
    SELECTOR_CLASS_NAMES,
    ContextAwareColumnSelector,
)
from BPC_future.scripts.train_gnn_column_selector import (
    _Split,
    _classification_metrics,
    _load_sample,
    _normalize_sample,
)


DEFAULT_DATASET_DIR = Path("BPC_future/data/gat_worker_roi/v31_source_recovered_20260615")
DEFAULT_CHECKPOINT = Path("BPC_future/data/gat_worker_roi/v31_source_recovered_20260615/gat_worker_roi.pt")
DEFAULT_METRICS = Path("BPC_future/results/gat_worker_roi_training_v31_20260615/summary.json")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260615_bpc_future_gat_worker_roi_training_v31_zh.md"
)


@dataclass(frozen=True)
class TrainWorkerROIArgs:
    dataset_dir: Path = DEFAULT_DATASET_DIR
    checkpoint_out: Path = DEFAULT_CHECKPOINT
    metrics_out: Path = DEFAULT_METRICS
    report: Path = DEFAULT_REPORT
    device: str = "cpu"
    epochs: int = 16
    lr: float = 1.0e-3
    weight_decay: float = 1.0e-5
    hidden_dim: int = 48
    option_hidden_dim: int = 48
    pair_edge_dim: int = 48
    selector_hidden_dim: int = 48
    num_gnn_layers: int = 1
    heads: int = 4
    dropout: float = 0.05
    validation_fraction: float = 0.25
    seed: int = 31
    min_samples: int = 150
    min_positive: int = 50
    min_negative: int = 50
    positive_loss_multiplier: float = 2.0
    loss_mode: str = "bce"
    focal_gamma: float = 2.0
    hard_positive_score_threshold: float = 0.5
    hard_negative_score_threshold: float = 0.5
    hard_positive_loss_multiplier: float = 1.0
    hard_negative_loss_multiplier: float = 1.0
    pairwise_loss_multiplier: float = 0.0
    pairwise_group_key: str = "instance"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--checkpoint-out", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--metrics-out", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--epochs", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1.0e-3)
    parser.add_argument("--weight-decay", type=float, default=1.0e-5)
    parser.add_argument("--hidden-dim", type=int, default=48)
    parser.add_argument("--option-hidden-dim", type=int, default=48)
    parser.add_argument("--pair-edge-dim", type=int, default=48)
    parser.add_argument("--selector-hidden-dim", type=int, default=48)
    parser.add_argument("--num-gnn-layers", type=int, default=1)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.05)
    parser.add_argument("--validation-fraction", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=31)
    parser.add_argument("--min-samples", type=int, default=150)
    parser.add_argument("--min-positive", type=int, default=50)
    parser.add_argument("--min-negative", type=int, default=50)
    parser.add_argument("--positive-loss-multiplier", type=float, default=2.0)
    parser.add_argument(
        "--loss-mode",
        choices=("bce", "focal", "pairwise", "focal_pairwise"),
        default="bce",
    )
    parser.add_argument("--focal-gamma", type=float, default=2.0)
    parser.add_argument("--hard-positive-score-threshold", type=float, default=0.5)
    parser.add_argument("--hard-negative-score-threshold", type=float, default=0.5)
    parser.add_argument("--hard-positive-loss-multiplier", type=float, default=1.0)
    parser.add_argument("--hard-negative-loss-multiplier", type=float, default=1.0)
    parser.add_argument("--pairwise-loss-multiplier", type=float, default=0.0)
    parser.add_argument("--pairwise-group-key", choices=("instance", "family", "all"), default="instance")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = train_worker_roi(args)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def train_worker_roi(args: argparse.Namespace | TrainWorkerROIArgs) -> dict[str, Any]:
    random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    dataset_dir = Path(args.dataset_dir)
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    _assert_worker_roi_manifest(manifest, args)
    samples = [_load_sample(dataset_dir / item["path"]) for item in manifest.get("samples", [])]
    if not samples:
        raise SystemExit("empty worker ROI GAT dataset")
    samples = [_normalize_sample(sample, manifest) for sample in samples]
    split = _split_samples_by_instance_path(
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
    pos_weight = _binary_pos_weight(
        split.train,
        device=device,
        multiplier=float(getattr(args, "positive_loss_multiplier", 2.0)),
    )
    loss_options = _worker_roi_loss_options(args)
    best_val_loss = float("inf")
    best_val_f1 = -1.0
    best_state: dict[str, torch.Tensor] | None = None
    best_threshold = 0.5
    best_epoch = 0
    history: list[dict[str, float]] = []
    for epoch in range(1, int(args.epochs) + 1):
        train_loss = _run_worker_roi_epoch(
            model,
            split.train,
            optimizer,
            device,
            pos_weight,
            loss_options=loss_options,
        )
        pairwise_loss = 0.0
        if float(loss_options["pairwise_loss_multiplier"]) > 0.0:
            pairwise_loss = _run_worker_roi_pairwise_step(
                model,
                split.train,
                optimizer,
                device,
                loss_options=loss_options,
            )
        validation_loss = _evaluate_worker_roi_loss(
            model,
            split.validation,
            device,
            pos_weight,
            loss_options=loss_options,
        )
        validation_probe = _worker_roi_binary_metrics(model, split.validation, device)
        validation_f1 = float(validation_probe.get("best_add_f1") or 0.0)
        history.append(
            {
                "epoch": float(epoch),
                "train_loss": float(train_loss),
                "pairwise_loss": float(pairwise_loss),
                "validation_loss": float(validation_loss),
                "validation_best_add_f1": validation_f1,
                "validation_best_add_precision": float(validation_probe.get("best_add_precision") or 0.0),
                "validation_best_add_recall": float(validation_probe.get("best_add_recall") or 0.0),
            }
        )
        if validation_f1 > best_val_f1 or (
            abs(validation_f1 - best_val_f1) <= 1.0e-12 and validation_loss <= best_val_loss
        ):
            best_val_f1 = validation_f1
            best_val_loss = float(validation_loss)
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
            best_threshold = float(validation_probe.get("best_threshold") or 0.5)
            best_epoch = int(epoch)
        print(
            "epoch="
            f"{epoch} train_loss={train_loss:.6f} validation_loss={validation_loss:.6f} "
            f"pairwise_loss={pairwise_loss:.6f} validation_best_add_f1={validation_f1:.6f}",
            flush=True,
        )
    if best_state is not None:
        model.load_state_dict(best_state)
    train_metrics = _worker_roi_binary_metrics(model, split.train, device, threshold=best_threshold)
    validation_metrics = _worker_roi_binary_metrics(model, split.validation, device, threshold=best_threshold)
    argmax_train_metrics = _classification_metrics(model, split.train, device)
    argmax_validation_metrics = _classification_metrics(model, split.validation, device)
    model_signal_ready = _model_signal_ready(validation_metrics)
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
        "version": "context_aware_worker_roi_gat_v1",
        "target_label": "paired_worker_ab_trajectory_roi",
        "label_semantics": dict(manifest.get("label_semantics") or {}),
        "trajectory_contract": {
            "target": "RMP trajectory objective/retry/tail ROI",
            "positive_action": "HIGH_PRIORITY",
            "unsafe_negative_action": "DELAY_QUEUE_NOT_DISCARD",
            "certificate_source": False,
            "pricing_oracle": False,
            "official_bound_effect": False,
            "labels_from_rc_or_gate": False,
        },
        "exactness_contract": (
            "Worker ROI scheduler only. It may prioritize true-RC negative "
            "columns, but it cannot certify no-negative, create official bounds, "
            "or permanently discard any true-RC negative column."
        ),
        "training": {
            "epochs": int(args.epochs),
            "lr": float(args.lr),
            "weight_decay": float(args.weight_decay),
            "positive_loss_multiplier": float(getattr(args, "positive_loss_multiplier", 2.0)),
            "loss_mode": str(loss_options["loss_mode"]),
            "focal_gamma": float(loss_options["focal_gamma"]),
            "hard_positive_score_threshold": float(loss_options["hard_positive_score_threshold"]),
            "hard_negative_score_threshold": float(loss_options["hard_negative_score_threshold"]),
            "hard_positive_loss_multiplier": float(loss_options["hard_positive_loss_multiplier"]),
            "hard_negative_loss_multiplier": float(loss_options["hard_negative_loss_multiplier"]),
            "pairwise_loss_multiplier": float(loss_options["pairwise_loss_multiplier"]),
            "pairwise_group_key": str(loss_options["pairwise_group_key"]),
            "binary_pos_weight": float(pos_weight.detach().cpu().item()),
            "checkpoint_selection": "validation_best_add_f1_then_loss",
            "best_epoch": best_epoch,
            "calibrated_add_threshold": best_threshold,
            "split": split.info,
            "history": history,
            "train_metrics": train_metrics,
            "validation_metrics": validation_metrics,
            "argmax_train_metrics": argmax_train_metrics,
            "argmax_validation_metrics": argmax_validation_metrics,
            "model_signal_ready": model_signal_ready,
            "priority_scheduler_ready": model_signal_ready,
        },
        "deployment_guard": {
            "model_signal_ready": model_signal_ready,
            "priority_scheduler_ready": model_signal_ready,
            "decision_rule": "sigmoid(add_logit-abstain_logit) >= calibrated_add_threshold",
            "calibrated_add_threshold": best_threshold,
            "requires_knn_ood_shell": True,
            "requires_5_10_no_regression": True,
            "requires_20_roi_ab": True,
            "default_enabled": False,
        },
    }
    Path(args.checkpoint_out).parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, args.checkpoint_out)
    summary = {
        "schema_version": "gat_worker_roi_training_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "gat_worker_roi_trained",
        "dataset_dir": str(dataset_dir),
        "checkpoint_out": str(args.checkpoint_out),
        "sample_count": len(samples),
        "candidate_count": int(manifest.get("candidate_count") or 0),
        "train_count": len(split.train),
        "validation_count": len(split.validation),
        "candidate_label_counts": dict(manifest.get("candidate_label_counts") or {}),
        "split": split.info,
        "train_metrics": train_metrics,
        "validation_metrics": validation_metrics,
        "argmax_train_metrics": argmax_train_metrics,
        "argmax_validation_metrics": argmax_validation_metrics,
        "best_validation_loss": best_val_loss,
        "best_validation_add_f1": best_val_f1,
        "best_epoch": best_epoch,
        "calibrated_add_threshold": best_threshold,
        "checkpoint_selection": "validation_best_add_f1_then_loss",
        "loss_mode": str(loss_options["loss_mode"]),
        "focal_gamma": float(loss_options["focal_gamma"]),
        "hard_positive_loss_multiplier": float(loss_options["hard_positive_loss_multiplier"]),
        "hard_negative_loss_multiplier": float(loss_options["hard_negative_loss_multiplier"]),
        "pairwise_loss_multiplier": float(loss_options["pairwise_loss_multiplier"]),
        "pairwise_group_key": str(loss_options["pairwise_group_key"]),
        "target_label": "paired_worker_ab_trajectory_roi",
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "model_signal_ready": model_signal_ready,
        "priority_scheduler_ready": model_signal_ready,
        "requires_knn_ood_shell": True,
        "requires_5_10_no_regression": True,
        "requires_20_roi_ab": True,
        "production_ready": False,
        "all_checks_pass": bool(
            train_metrics.get("total", 0) > 0
            and validation_metrics.get("total", 0) > 0
            and checkpoint["selector_class_names"] == list(SELECTOR_CLASS_NAMES)
            and checkpoint["target_label"] == "paired_worker_ab_trajectory_roi"
            and not checkpoint["trajectory_contract"]["certificate_source"]
            and _count_label(samples, SELECTOR_CLASS_ADD) >= int(args.min_positive)
            and _count_label(samples, SELECTOR_CLASS_ABSTAIN) >= int(args.min_negative)
        ),
    }
    Path(args.metrics_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.metrics_out).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(args.report), summary)
    return summary


def _assert_worker_roi_manifest(manifest: dict[str, Any], args: argparse.Namespace | TrainWorkerROIArgs) -> None:
    if manifest.get("schema_version") != "gat_worker_roi_graph_dataset_manifest_v1":
        raise ValueError("worker ROI GAT dataset must use gat_worker_roi_graph_dataset_manifest_v1")
    if not bool(manifest.get("diagnostic_only")):
        raise ValueError("worker ROI GAT dataset must be diagnostic_only")
    if bool(manifest.get("runs_bpc_or_pricing")):
        raise ValueError("worker ROI GAT training cannot use a dataset that runs BPC or pricing")
    if "paired" not in str(manifest.get("exactness_contract") or "").lower() and "roi" not in str(
        manifest.get("exactness_contract") or ""
    ).lower():
        raise ValueError("worker ROI dataset contract must mention ROI/exactness semantics")
    label_counts = dict(manifest.get("candidate_label_counts") or {})
    sample_count = int(manifest.get("sample_count") or 0)
    positive = int(label_counts.get("add") or 0)
    negative = int(label_counts.get("abstain") or 0)
    if sample_count < int(args.min_samples):
        raise ValueError(f"worker ROI dataset has {sample_count} samples; requires {int(args.min_samples)}")
    if positive < int(args.min_positive):
        raise ValueError(f"worker ROI dataset has {positive} positive ROI samples; requires {int(args.min_positive)}")
    if negative < int(args.min_negative):
        raise ValueError(f"worker ROI dataset has {negative} negative ROI samples; requires {int(args.min_negative)}")


def _split_samples_by_instance_path(samples: list[Any], *, validation_fraction: float, seed: int) -> _Split:
    by_instance: dict[str, list[Any]] = {}
    for sample in samples:
        instance = str(getattr(sample, "selector_instance_path", "") or getattr(sample, "selector_instance", ""))
        by_instance.setdefault(instance, []).append(sample)
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
    return _Split(
        train=train,
        validation=validation,
        info={
            "mode": "instance_path",
            "train_instances": sorted(set(instances) - validation_instances),
            "validation_instances": sorted(validation_instances),
        },
    )


def _count_label(samples: list[Any], label: int) -> int:
    return sum(int(torch.sum(sample.y_selector.to(dtype=torch.long) == int(label)).item()) for sample in samples)


def _binary_pos_weight(samples: list[Any], *, device: torch.device, multiplier: float = 1.0) -> torch.Tensor:
    positive = 0
    negative = 0
    for sample in samples:
        labels = sample.y_selector.to(dtype=torch.long)
        positive += int(torch.sum(labels == SELECTOR_CLASS_ADD).item())
        negative += int(torch.sum(labels == SELECTOR_CLASS_ABSTAIN).item())
    if positive <= 0:
        weight = 1.0
    else:
        weight = max(1.0, negative / float(positive)) * max(1.0e-6, float(multiplier))
    return torch.tensor(weight, dtype=torch.float32, device=device)


def _worker_roi_loss_options(args: argparse.Namespace | TrainWorkerROIArgs) -> dict[str, Any]:
    loss_mode = str(getattr(args, "loss_mode", "bce") or "bce")
    allowed = {"bce", "focal", "pairwise", "focal_pairwise"}
    if loss_mode not in allowed:
        raise ValueError(f"unsupported worker ROI loss_mode={loss_mode!r}")
    pairwise_multiplier = float(getattr(args, "pairwise_loss_multiplier", 0.0))
    if loss_mode in {"pairwise", "focal_pairwise"} and pairwise_multiplier <= 0.0:
        pairwise_multiplier = 1.0
    return {
        "loss_mode": loss_mode,
        "focal_gamma": max(0.0, float(getattr(args, "focal_gamma", 2.0))),
        "hard_positive_score_threshold": float(getattr(args, "hard_positive_score_threshold", 0.5)),
        "hard_negative_score_threshold": float(getattr(args, "hard_negative_score_threshold", 0.5)),
        "hard_positive_loss_multiplier": max(
            1.0, float(getattr(args, "hard_positive_loss_multiplier", 1.0))
        ),
        "hard_negative_loss_multiplier": max(
            1.0, float(getattr(args, "hard_negative_loss_multiplier", 1.0))
        ),
        "pairwise_loss_multiplier": max(0.0, pairwise_multiplier),
        "pairwise_group_key": str(getattr(args, "pairwise_group_key", "instance") or "instance"),
    }


def _worker_roi_logits(model: ContextAwareColumnSelector, sample: Any) -> torch.Tensor:
    output = model(
        sample,
        sample.candidate_task_membership,
        sample.candidate_features,
        sample.context_features,
    )
    logits = output["logits"]
    return logits[:, SELECTOR_CLASS_ADD] - logits[:, SELECTOR_CLASS_ABSTAIN]


def _worker_roi_targets(sample: Any) -> torch.Tensor:
    labels = sample.y_selector.to(dtype=torch.long)
    return (labels == SELECTOR_CLASS_ADD).to(dtype=torch.float32)


def _worker_roi_sample_loss(
    model: ContextAwareColumnSelector,
    sample: Any,
    device: torch.device,
    pos_weight: torch.Tensor,
    *,
    loss_options: dict[str, Any] | None = None,
) -> torch.Tensor:
    options = loss_options or _worker_roi_loss_options(TrainWorkerROIArgs())
    sample = sample.to(device)
    logits = _worker_roi_logits(model, sample)
    targets = _worker_roi_targets(sample).to(device)
    loss = torch.nn.functional.binary_cross_entropy_with_logits(
        logits,
        targets,
        pos_weight=pos_weight,
        reduction="none",
    )
    scores = torch.sigmoid(logits.detach())
    if str(options["loss_mode"]) in {"focal", "focal_pairwise"}:
        probs = torch.sigmoid(logits)
        pt = torch.where(targets > 0.5, probs, 1.0 - probs)
        loss = loss * torch.pow(torch.clamp(1.0 - pt, min=0.0, max=1.0), float(options["focal_gamma"]))
    weights = torch.ones_like(loss)
    hard_positive = (targets > 0.5) & (scores < float(options["hard_positive_score_threshold"]))
    hard_negative = (targets <= 0.5) & (scores >= float(options["hard_negative_score_threshold"]))
    weights = torch.where(
        hard_positive,
        weights * float(options["hard_positive_loss_multiplier"]),
        weights,
    )
    weights = torch.where(
        hard_negative,
        weights * float(options["hard_negative_loss_multiplier"]),
        weights,
    )
    return (loss * weights).mean()


def _run_worker_roi_epoch(
    model: ContextAwareColumnSelector,
    samples: list[Any],
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    pos_weight: torch.Tensor,
    *,
    loss_options: dict[str, Any] | None = None,
) -> float:
    model.train()
    shuffled = list(samples)
    random.shuffle(shuffled)
    total = 0.0
    count = 0
    for sample in shuffled:
        optimizer.zero_grad(set_to_none=True)
        loss = _worker_roi_sample_loss(model, sample, device, pos_weight, loss_options=loss_options)
        loss.backward()
        optimizer.step()
        total += float(loss.detach().cpu())
        count += 1
    return total / max(1, count)


def _evaluate_worker_roi_loss(
    model: ContextAwareColumnSelector,
    samples: list[Any],
    device: torch.device,
    pos_weight: torch.Tensor,
    *,
    loss_options: dict[str, Any] | None = None,
) -> float:
    if not samples:
        return float("inf")
    model.eval()
    total = 0.0
    with torch.no_grad():
        for sample in samples:
            total += float(
                _worker_roi_sample_loss(
                    model,
                    sample,
                    device,
                    pos_weight,
                    loss_options=loss_options,
                ).detach().cpu()
            )
    return total / max(1, len(samples))


def _run_worker_roi_pairwise_step(
    model: ContextAwareColumnSelector,
    samples: list[Any],
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    *,
    loss_options: dict[str, Any],
) -> float:
    grouped: dict[str, list[tuple[torch.Tensor, torch.Tensor]]] = {}
    model.train()
    optimizer.zero_grad(set_to_none=True)
    for sample in samples:
        sample = sample.to(device)
        logits = _worker_roi_logits(model, sample)
        targets = _worker_roi_targets(sample).to(device)
        group_key = _pairwise_group_key(sample, str(loss_options["pairwise_group_key"]))
        grouped.setdefault(group_key, []).append((logits.reshape(-1), targets.reshape(-1)))
    losses: list[torch.Tensor] = []
    for items in grouped.values():
        logits = torch.cat([item[0] for item in items], dim=0)
        targets = torch.cat([item[1] for item in items], dim=0)
        positive_logits = logits[targets > 0.5]
        negative_logits = logits[targets <= 0.5]
        if positive_logits.numel() <= 0 or negative_logits.numel() <= 0:
            continue
        diff = positive_logits[:, None] - negative_logits[None, :]
        losses.append(torch.nn.functional.softplus(-diff).mean())
    if not losses:
        optimizer.zero_grad(set_to_none=True)
        return 0.0
    loss = torch.stack(losses).mean() * float(loss_options["pairwise_loss_multiplier"])
    loss.backward()
    optimizer.step()
    return float(loss.detach().cpu())


def _pairwise_group_key(sample: Any, mode: str) -> str:
    if mode == "all":
        return "all"
    if mode == "family":
        return str(getattr(sample, "selector_instance_family", "") or "unknown-family")
    return str(getattr(sample, "selector_instance_path", "") or getattr(sample, "selector_instance", "") or "unknown")


def _worker_roi_binary_metrics(
    model: ContextAwareColumnSelector,
    samples: list[Any],
    device: torch.device,
    *,
    threshold: float | None = None,
) -> dict[str, Any]:
    model.eval()
    scores: list[float] = []
    labels: list[int] = []
    with torch.no_grad():
        for sample in samples:
            sample = sample.to(device)
            logits = _worker_roi_logits(model, sample)
            sample_scores = torch.sigmoid(logits).detach().cpu().tolist()
            sample_labels = _worker_roi_targets(sample).detach().cpu().to(dtype=torch.long).tolist()
            scores.extend(float(score) for score in sample_scores)
            labels.extend(int(label) for label in sample_labels)
    if not labels:
        return {"total": 0}
    chosen_threshold = float(threshold) if threshold is not None else _best_add_threshold(scores, labels)
    metrics = _binary_metrics_at_threshold(scores, labels, chosen_threshold)
    best_threshold = _best_add_threshold(scores, labels)
    best_metrics = _binary_metrics_at_threshold(scores, labels, best_threshold)
    metrics.update(
        {
            "best_threshold": best_threshold,
            "best_add_precision": best_metrics["add_precision"],
            "best_add_recall": best_metrics["add_recall"],
            "best_add_f1": best_metrics["add_f1"],
            "score_min": min(scores),
            "score_mean": sum(scores) / float(len(scores)),
            "score_max": max(scores),
        }
    )
    return metrics


def _best_add_threshold(scores: list[float], labels: list[int]) -> float:
    candidates = sorted({0.0, 0.5, 1.0, *scores})
    best_threshold = 0.5
    best_key = (-1.0, -1.0, -1.0)
    for threshold in candidates:
        metrics = _binary_metrics_at_threshold(scores, labels, float(threshold))
        key = (
            float(metrics.get("add_f1") or 0.0),
            float(metrics.get("add_recall") or 0.0),
            float(metrics.get("add_precision") or 0.0),
        )
        if key > best_key:
            best_key = key
            best_threshold = float(threshold)
    return best_threshold


def _binary_metrics_at_threshold(scores: list[float], labels: list[int], threshold: float) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for score, label in zip(scores, labels):
        pred = 1 if float(score) >= float(threshold) else 0
        if pred == 1 and label == 1:
            tp += 1
        elif pred == 1 and label == 0:
            fp += 1
        elif pred == 0 and label == 0:
            tn += 1
        else:
            fn += 1
    total = tp + fp + tn + fn
    precision = None if tp + fp <= 0 else tp / float(tp + fp)
    recall = None if tp + fn <= 0 else tp / float(tp + fn)
    if precision is None or recall is None or precision + recall <= 0.0:
        f1 = 0.0
    else:
        f1 = 2.0 * precision * recall / (precision + recall)
    return {
        "total": total,
        "threshold": float(threshold),
        "accuracy": None if total <= 0 else (tp + tn) / float(total),
        "add_precision": precision,
        "add_recall": recall,
        "add_f1": f1,
        "confusion_binary": {
            "tp_add": tp,
            "fp_add": fp,
            "tn_abstain": tn,
            "fn_add": fn,
        },
    }


def _model_signal_ready(metrics: dict[str, Any]) -> bool:
    """Conservative guard: a scheduler must recover some positive ROI on holdout."""

    return bool(
        metrics.get("total", 0) > 0
        and float(metrics.get("add_recall") or 0.0) > 0.0
        and float(metrics.get("add_precision") or 0.0) > 0.0
    )


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Worker ROI Training 报告",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "训练 worker ROI GAT scheduler。标签只来自 paired worker A/B 后的",
        "trajectory objective / retry / tail ROI，不来自 reduced cost、GAT 分数或",
        "kNN/OOD gate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_worker_roi_training = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"sample_count = {summary['sample_count']}",
        f"candidate_label_counts = {summary['candidate_label_counts']}",
        f"target_label = {summary['target_label']}",
        f"selector_can_certificate = {str(summary['selector_can_certificate']).lower()}",
        f"selector_is_pricing_oracle = {str(summary['selector_is_pricing_oracle']).lower()}",
        f"gate_can_permanently_discard_negative_columns = {str(summary['gate_can_permanently_discard_negative_columns']).lower()}",
        f"model_signal_ready = {str(summary['model_signal_ready']).lower()}",
        f"priority_scheduler_ready = {str(summary['priority_scheduler_ready']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 指标",
        "",
        "```json",
        json.dumps(
            {
                "train_metrics": summary["train_metrics"],
                "validation_metrics": summary["validation_metrics"],
                "argmax_train_metrics": summary["argmax_train_metrics"],
                "argmax_validation_metrics": summary["argmax_validation_metrics"],
                "best_validation_loss": summary["best_validation_loss"],
                "best_validation_add_f1": summary["best_validation_add_f1"],
                "best_epoch": summary["best_epoch"],
                "calibrated_add_threshold": summary["calibrated_add_threshold"],
                "checkpoint_selection": summary["checkpoint_selection"],
                "split": summary["split"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 边界",
        "",
        "- 不可作为 pricing oracle；",
        "- 不可作为 certificate source；",
        "- 不可影响 official lower bound；",
        "- 不通过的 true-RC negative 只能进入 DELAY_QUEUE，不能永久丢弃；",
        "- 只有 validation add precision/recall 都大于 0 时，才允许进入下一步 priority scheduler audit；",
        "- 下一步必须做 kNN/OOD safety shell 与 5/10 no-regression、20 ROI A/B。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
