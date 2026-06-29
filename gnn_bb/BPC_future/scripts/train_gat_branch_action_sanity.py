#!/usr/bin/env python3
"""Sanity-train the offline GAT branch/action model.

This training entry is deliberately not production-ready. It verifies that the
branch/action graph dataset can drive the branch-impact GAT heads using
wall-time gain as the main branch-priority label. The produced checkpoint is an
offline study artifact only and is not loaded by the solver by default.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import random
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch
import torch.nn.functional as F

from BPC_future.learning.branch_impact_model import (
    GATBranchImpactModel,
    branch_impact_exactness_contract,
)


DEFAULT_DATASET_DIR = Path("BPC_future/data/gat_branch_action_sanity/v430_randomtw60_branch_replay_20260626")
DEFAULT_CHECKPOINT = Path(
    "BPC_future/data/gat_branch_action_sanity/v430_randomtw60_branch_replay_20260626/"
    "gat_branch_action_v430.pt"
)
DEFAULT_METRICS = Path("BPC_future/results/gat_branch_action_v430_randomtw60_20260626/summary.json")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260626_bpc_future_gat_branch_action_v430_randomtw60_zh.md"
)


@dataclass(frozen=True)
class TrainBranchActionSanityArgs:
    dataset_dir: Path = DEFAULT_DATASET_DIR
    checkpoint_out: Path = DEFAULT_CHECKPOINT
    metrics_out: Path = DEFAULT_METRICS
    report: Path = DEFAULT_REPORT
    device: str = "cpu"
    epochs: int = 12
    lr: float = 1.0e-3
    weight_decay: float = 1.0e-5
    hidden_dim: int = 32
    option_hidden_dim: int = 32
    pair_edge_dim: int = 32
    num_gnn_layers: int = 1
    heads: int = 4
    dropout: float = 0.05
    branch_hidden_dim: int = 32
    context_hidden_dim: int = 16
    impact_hidden_dim: int = 32
    validation_fraction: float = 0.25
    seed: int = 244
    min_samples: int = 10
    min_walltime_positive: int = 3
    min_target_positive: int | None = None
    min_hard_negative: int = 3
    branch_priority_loss_multiplier: float = 1.0
    branch_positive_loss_multiplier: float = 1.0
    tail_aux_loss_multiplier: float = 0.25
    walltime_gain_loss_multiplier: float = 1.0
    child_proof_cpu_loss_multiplier: float = 0.10
    time_to_certificate_loss_multiplier: float = 0.10
    gap_improvement_loss_multiplier: float = 0.10
    primal_improvement_loss_multiplier: float = 0.05
    dual_bound_gain_loss_multiplier: float = 0.05
    fathom_gain_loss_multiplier: float = 0.05
    branch_count_delta_loss_multiplier: float = 0.05
    completion_bound_retry_gain_loss_multiplier: float = 0.05
    tree_policy_loss_multiplier: float = 0.25
    tree_policy_pairwise_loss_multiplier: float = 0.25
    tree_policy_pairwise_margin: float = 0.50
    checkpoint_selection: str = "validation_total"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_sample(path: Path) -> Any:
    return torch.load(path, map_location="cpu", weights_only=False)


def _split_items(
    manifest: dict[str, Any],
    *,
    validation_fraction: float,
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    items = list(manifest.get("samples") or [])
    if float(validation_fraction) <= 0.0:
        return items, []
    rng = random.Random(int(seed))
    by_instance: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        by_instance.setdefault(str(item.get("instance") or ""), []).append(item)
    instance_keys = sorted(by_instance)
    rng.shuffle(instance_keys)
    if len(instance_keys) >= 2:
        validation_instance_count = max(1, int(round(len(instance_keys) * float(validation_fraction))))
        validation_instances = set(instance_keys[:validation_instance_count])
        validation = [item for key in validation_instances for item in by_instance[key]]
        train = [item for key in instance_keys if key not in validation_instances for item in by_instance[key]]
        if train and validation:
            return train, validation
    shuffled = list(items)
    rng.shuffle(shuffled)
    validation_count = max(1, int(round(len(shuffled) * float(validation_fraction)))) if len(shuffled) > 1 else 0
    validation = shuffled[:validation_count]
    train = shuffled[validation_count:]
    if not train and validation:
        train, validation = validation, []
    return train, validation


def _make_model(first_sample: Any, manifest: dict[str, Any], args: argparse.Namespace | TrainBranchActionSanityArgs) -> GATBranchImpactModel:
    return GATBranchImpactModel(
        node_dim=int(first_sample.x.size(1)),
        option_dim=int(first_sample.option_feat.size(1)),
        branch_feature_dim=len(manifest["branch_feature_schema"]),
        context_feature_dim=len(manifest["context_feature_schema"]),
        hidden_dim=int(args.hidden_dim),
        option_hidden_dim=int(args.option_hidden_dim),
        pair_edge_dim=int(args.pair_edge_dim),
        num_gnn_layers=int(args.num_gnn_layers),
        heads=int(args.heads),
        dropout=float(args.dropout),
        branch_hidden_dim=int(args.branch_hidden_dim),
        context_hidden_dim=int(args.context_hidden_dim),
        impact_hidden_dim=int(args.impact_hidden_dim),
    )


def _sample_loss(
    model: GATBranchImpactModel,
    sample: Any,
    device: torch.device,
    *,
    branch_priority_loss_multiplier: float,
    branch_positive_loss_multiplier: float,
    tail_aux_loss_multiplier: float,
    walltime_gain_loss_multiplier: float,
    child_proof_cpu_loss_multiplier: float,
    time_to_certificate_loss_multiplier: float,
    gap_improvement_loss_multiplier: float,
    primal_improvement_loss_multiplier: float,
    dual_bound_gain_loss_multiplier: float,
    fathom_gain_loss_multiplier: float,
    branch_count_delta_loss_multiplier: float,
    completion_bound_retry_gain_loss_multiplier: float,
    tree_policy_loss_multiplier: float,
) -> tuple[torch.Tensor, dict[str, float]]:
    sample = sample.to(device)
    output = model(
        sample,
        sample.branch_pair_indices,
        sample.branch_pair_features,
        sample.context_features,
    )
    branch_logit = output["branch_priority_logit"].view(-1)
    branch_target = sample.y_branch_priority.to(device=device, dtype=branch_logit.dtype).view(-1)
    branch_weight = sample.branch_priority_loss_weight.to(device=device, dtype=branch_logit.dtype).view(-1)
    branch_loss_vec = F.binary_cross_entropy_with_logits(
        branch_logit,
        branch_target,
        reduction="none",
    )
    if float(branch_weight.sum().detach().cpu()) > 0.0:
        branch_loss = (branch_loss_vec * branch_weight).sum() / branch_weight.sum().clamp_min(1.0e-6)
    else:
        branch_loss = branch_loss_vec.sum() * 0.0
    if float(branch_target.max().detach().cpu()) > 0.5:
        branch_loss = branch_loss * float(branch_positive_loss_multiplier)

    tail_logit = output["tail_improved_logit"].view(-1)
    tail_target = sample.y_tail_improved.to(device=device, dtype=tail_logit.dtype).view(-1)
    tail_weight = sample.tail_improved_loss_weight.to(device=device, dtype=tail_logit.dtype).view(-1)
    tail_loss_vec = F.binary_cross_entropy_with_logits(
        tail_logit,
        tail_target,
        reduction="none",
    )
    if float(tail_weight.sum().detach().cpu()) > 0.0:
        tail_loss = (tail_loss_vec * tail_weight).sum() / tail_weight.sum().clamp_min(1.0e-6)
    else:
        tail_loss = tail_loss_vec.sum() * 0.0
    zero = branch_loss * 0.0
    walltime_loss = _optional_weighted_smooth_l1(
        output.get("predicted_walltime_gain"),
        getattr(sample, "y_walltime_gain", None),
        getattr(sample, "walltime_gain_loss_weight", None),
        device=device,
        fallback=zero,
    )
    child_proof_cpu_loss = _optional_weighted_smooth_l1(
        output.get("predicted_child_proof_cpu"),
        getattr(sample, "y_child_proof_cpu", None),
        getattr(sample, "child_proof_cpu_loss_weight", None),
        device=device,
        fallback=zero,
    )
    time_to_certificate_loss = _optional_weighted_smooth_l1(
        output.get("predicted_time_to_certificate"),
        getattr(sample, "y_time_to_certificate", None),
        getattr(sample, "time_to_certificate_loss_weight", None),
        device=device,
        fallback=zero,
    )
    gap_improvement_loss = _optional_weighted_smooth_l1(
        output.get("predicted_gap_improvement"),
        getattr(sample, "y_gap_improvement", None),
        getattr(sample, "gap_improvement_loss_weight", None),
        device=device,
        fallback=zero,
    )
    primal_improvement_loss = _optional_weighted_smooth_l1(
        output.get("predicted_primal_improvement"),
        getattr(sample, "y_primal_improvement", None),
        getattr(sample, "primal_improvement_loss_weight", None),
        device=device,
        fallback=zero,
    )
    dual_bound_gain_loss = _optional_weighted_smooth_l1(
        output.get("predicted_dual_bound_gain"),
        getattr(sample, "y_dual_bound_gain", None),
        getattr(sample, "dual_bound_gain_loss_weight", None),
        device=device,
        fallback=zero,
    )
    fathom_gain_loss = _optional_weighted_smooth_l1(
        output.get("predicted_fathom_gain"),
        getattr(sample, "y_fathom_gain", None),
        getattr(sample, "fathom_gain_loss_weight", None),
        device=device,
        fallback=zero,
    )
    branch_count_delta_loss = _optional_weighted_smooth_l1(
        output.get("predicted_branch_count_delta"),
        getattr(sample, "y_branch_count_delta", None),
        getattr(sample, "branch_count_delta_loss_weight", None),
        device=device,
        fallback=zero,
    )
    completion_bound_retry_gain_loss = _optional_weighted_smooth_l1(
        output.get("predicted_completion_bound_retry_gain"),
        getattr(sample, "y_completion_bound_retry_gain", None),
        getattr(sample, "completion_bound_retry_gain_loss_weight", None),
        device=device,
        fallback=zero,
    )
    tree_policy_loss = _optional_weighted_bce_with_logits(
        output.get("tree_policy_logit"),
        getattr(sample, "y_tree_policy", None),
        getattr(sample, "tree_policy_loss_weight", None),
        device=device,
        fallback=zero,
    )
    total_loss = (
        float(branch_priority_loss_multiplier) * branch_loss
        + float(tail_aux_loss_multiplier) * tail_loss
        + float(walltime_gain_loss_multiplier) * walltime_loss
        + float(child_proof_cpu_loss_multiplier) * child_proof_cpu_loss
        + float(time_to_certificate_loss_multiplier) * time_to_certificate_loss
        + float(gap_improvement_loss_multiplier) * gap_improvement_loss
        + float(primal_improvement_loss_multiplier) * primal_improvement_loss
        + float(dual_bound_gain_loss_multiplier) * dual_bound_gain_loss
        + float(fathom_gain_loss_multiplier) * fathom_gain_loss
        + float(branch_count_delta_loss_multiplier) * branch_count_delta_loss
        + float(completion_bound_retry_gain_loss_multiplier) * completion_bound_retry_gain_loss
        + float(tree_policy_loss_multiplier) * tree_policy_loss
    )
    return total_loss, {
        "branch_loss": float(branch_loss.detach().cpu()),
        "tail_loss": float(tail_loss.detach().cpu()),
        "walltime_gain_loss": float(walltime_loss.detach().cpu()),
        "child_proof_cpu_loss": float(child_proof_cpu_loss.detach().cpu()),
        "time_to_certificate_loss": float(time_to_certificate_loss.detach().cpu()),
        "gap_improvement_loss": float(gap_improvement_loss.detach().cpu()),
        "primal_improvement_loss": float(primal_improvement_loss.detach().cpu()),
        "dual_bound_gain_loss": float(dual_bound_gain_loss.detach().cpu()),
        "fathom_gain_loss": float(fathom_gain_loss.detach().cpu()),
        "branch_count_delta_loss": float(branch_count_delta_loss.detach().cpu()),
        "completion_bound_retry_gain_loss": float(completion_bound_retry_gain_loss.detach().cpu()),
        "tree_policy_loss": float(tree_policy_loss.detach().cpu()),
        "total_loss": float(total_loss.detach().cpu()),
    }


def _optional_weighted_smooth_l1(
    prediction: torch.Tensor | None,
    target: Any,
    weight: Any,
    *,
    device: torch.device,
    fallback: torch.Tensor,
) -> torch.Tensor:
    if prediction is None or target is None or weight is None:
        return fallback
    pred = prediction.view(-1)
    target_tensor = target.to(device=device, dtype=pred.dtype).view(-1)
    weight_tensor = weight.to(device=device, dtype=pred.dtype).view(-1)
    if float(weight_tensor.sum().detach().cpu()) <= 0.0:
        return fallback
    loss_vec = F.smooth_l1_loss(pred, target_tensor, reduction="none")
    return (loss_vec * weight_tensor).sum() / weight_tensor.sum().clamp_min(1.0e-6)


def _optional_weighted_bce_with_logits(
    prediction: torch.Tensor | None,
    target: Any,
    weight: Any,
    *,
    device: torch.device,
    fallback: torch.Tensor,
) -> torch.Tensor:
    if prediction is None or target is None or weight is None:
        return fallback
    pred = prediction.view(-1)
    target_tensor = target.to(device=device, dtype=pred.dtype).view(-1)
    weight_tensor = weight.to(device=device, dtype=pred.dtype).view(-1)
    if float(weight_tensor.sum().detach().cpu()) <= 0.0:
        return fallback
    loss_vec = F.binary_cross_entropy_with_logits(pred, target_tensor, reduction="none")
    return (loss_vec * weight_tensor).sum() / weight_tensor.sum().clamp_min(1.0e-6)


def _tree_policy_node_context_key(sample: Any) -> str:
    key = getattr(sample, "branch_action_node_context_key", None)
    if key:
        return str(key)
    return str(getattr(sample, "branch_action_context_key", ""))


def _tree_policy_pairwise_group_loss(
    model: GATBranchImpactModel,
    samples: list[Any],
    device: torch.device,
    *,
    margin: float,
) -> tuple[torch.Tensor | None, int]:
    positives: list[tuple[torch.Tensor, torch.Tensor]] = []
    negatives: list[tuple[torch.Tensor, torch.Tensor]] = []
    for sample in samples:
        if not hasattr(sample, "y_tree_policy") or not hasattr(sample, "tree_policy_loss_weight"):
            continue
        label_value = float(sample.y_tree_policy.view(-1)[0].detach().cpu())
        weight_value = float(sample.tree_policy_loss_weight.view(-1)[0].detach().cpu())
        if weight_value <= 0.0:
            continue
        sample = sample.to(device)
        output = model(
            sample,
            sample.branch_pair_indices,
            sample.branch_pair_features,
            sample.context_features,
        )
        logit = output.get("tree_policy_logit")
        if logit is None:
            continue
        score = logit.view(-1)[0]
        weight = torch.tensor(weight_value, dtype=score.dtype, device=device)
        if label_value > 0.5:
            positives.append((score, weight))
        else:
            negatives.append((score, weight))
    if not positives or not negatives:
        return None, 0
    losses: list[torch.Tensor] = []
    weights: list[torch.Tensor] = []
    margin_tensor = torch.tensor(float(margin), dtype=positives[0][0].dtype, device=device)
    for positive_score, positive_weight in positives:
        for negative_score, negative_weight in negatives:
            pair_weight = torch.sqrt((positive_weight * negative_weight).clamp_min(1.0e-6))
            losses.append(F.relu(margin_tensor - (positive_score - negative_score)) * pair_weight)
            weights.append(pair_weight)
    if not losses:
        return None, 0
    return torch.stack(losses).sum() / torch.stack(weights).sum().clamp_min(1.0e-6), len(losses)


def _run_tree_policy_pairwise_epoch(
    model: GATBranchImpactModel,
    samples: list[Any],
    device: torch.device,
    optimizer: torch.optim.Optimizer | None,
    *,
    margin: float,
) -> dict[str, float]:
    groups: dict[str, list[Any]] = {}
    for sample in samples:
        key = _tree_policy_node_context_key(sample)
        if key:
            groups.setdefault(key, []).append(sample)
    total_loss = 0.0
    total_pairs = 0
    group_count = 0
    for group_samples in groups.values():
        if len(group_samples) < 2:
            continue
        if optimizer is not None:
            optimizer.zero_grad(set_to_none=True)
            loss, pair_count = _tree_policy_pairwise_group_loss(
                model,
                group_samples,
                device,
                margin=float(margin),
            )
            if loss is None or pair_count <= 0:
                continue
            loss.backward()
            optimizer.step()
        else:
            with torch.no_grad():
                loss, pair_count = _tree_policy_pairwise_group_loss(
                    model,
                    group_samples,
                    device,
                    margin=float(margin),
                )
            if loss is None or pair_count <= 0:
                continue
        total_loss += float(loss.detach().cpu())
        total_pairs += int(pair_count)
        group_count += 1
    return {
        "tree_policy_pairwise_loss": total_loss / float(group_count) if group_count else 0.0,
        "tree_policy_pairwise_group_count": float(group_count),
        "tree_policy_pairwise_pair_count": float(total_pairs),
    }


def _run_epoch(
    model: GATBranchImpactModel,
    samples: list[Any],
    device: torch.device,
    optimizer: torch.optim.Optimizer | None,
    *,
    branch_priority_loss_multiplier: float,
    branch_positive_loss_multiplier: float,
    tail_aux_loss_multiplier: float,
    walltime_gain_loss_multiplier: float,
    child_proof_cpu_loss_multiplier: float,
    time_to_certificate_loss_multiplier: float,
    gap_improvement_loss_multiplier: float,
    primal_improvement_loss_multiplier: float,
    dual_bound_gain_loss_multiplier: float,
    fathom_gain_loss_multiplier: float,
    branch_count_delta_loss_multiplier: float,
    completion_bound_retry_gain_loss_multiplier: float,
    tree_policy_loss_multiplier: float,
    tree_policy_pairwise_loss_multiplier: float,
    tree_policy_pairwise_margin: float,
) -> dict[str, float]:
    if optimizer is None:
        model.eval()
    else:
        model.train()
    totals = {
        "branch_loss": 0.0,
        "tail_loss": 0.0,
        "walltime_gain_loss": 0.0,
        "child_proof_cpu_loss": 0.0,
        "time_to_certificate_loss": 0.0,
        "gap_improvement_loss": 0.0,
        "primal_improvement_loss": 0.0,
        "dual_bound_gain_loss": 0.0,
        "fathom_gain_loss": 0.0,
        "branch_count_delta_loss": 0.0,
        "completion_bound_retry_gain_loss": 0.0,
        "tree_policy_loss": 0.0,
        "tree_policy_pairwise_loss": 0.0,
        "tree_policy_pairwise_group_count": 0.0,
        "tree_policy_pairwise_pair_count": 0.0,
        "total_loss": 0.0,
    }
    count = 0
    for sample in samples:
        if optimizer is not None:
            optimizer.zero_grad(set_to_none=True)
            loss, parts = _sample_loss(
                model,
                sample,
                device,
                branch_priority_loss_multiplier=branch_priority_loss_multiplier,
                branch_positive_loss_multiplier=branch_positive_loss_multiplier,
                tail_aux_loss_multiplier=tail_aux_loss_multiplier,
                walltime_gain_loss_multiplier=walltime_gain_loss_multiplier,
                child_proof_cpu_loss_multiplier=child_proof_cpu_loss_multiplier,
                time_to_certificate_loss_multiplier=time_to_certificate_loss_multiplier,
                gap_improvement_loss_multiplier=gap_improvement_loss_multiplier,
                primal_improvement_loss_multiplier=primal_improvement_loss_multiplier,
                dual_bound_gain_loss_multiplier=dual_bound_gain_loss_multiplier,
                fathom_gain_loss_multiplier=fathom_gain_loss_multiplier,
                branch_count_delta_loss_multiplier=branch_count_delta_loss_multiplier,
                completion_bound_retry_gain_loss_multiplier=completion_bound_retry_gain_loss_multiplier,
                tree_policy_loss_multiplier=tree_policy_loss_multiplier,
            )
            loss.backward()
            optimizer.step()
        else:
            with torch.no_grad():
                _, parts = _sample_loss(
                    model,
                    sample,
                    device,
                    branch_priority_loss_multiplier=branch_priority_loss_multiplier,
                    branch_positive_loss_multiplier=branch_positive_loss_multiplier,
                    tail_aux_loss_multiplier=tail_aux_loss_multiplier,
                    walltime_gain_loss_multiplier=walltime_gain_loss_multiplier,
                    child_proof_cpu_loss_multiplier=child_proof_cpu_loss_multiplier,
                    time_to_certificate_loss_multiplier=time_to_certificate_loss_multiplier,
                    gap_improvement_loss_multiplier=gap_improvement_loss_multiplier,
                    primal_improvement_loss_multiplier=primal_improvement_loss_multiplier,
                    dual_bound_gain_loss_multiplier=dual_bound_gain_loss_multiplier,
                    fathom_gain_loss_multiplier=fathom_gain_loss_multiplier,
                    branch_count_delta_loss_multiplier=branch_count_delta_loss_multiplier,
                    completion_bound_retry_gain_loss_multiplier=completion_bound_retry_gain_loss_multiplier,
                    tree_policy_loss_multiplier=tree_policy_loss_multiplier,
                )
        for key in (
            "branch_loss",
            "tail_loss",
            "walltime_gain_loss",
            "child_proof_cpu_loss",
            "time_to_certificate_loss",
            "gap_improvement_loss",
            "primal_improvement_loss",
            "dual_bound_gain_loss",
            "fathom_gain_loss",
            "branch_count_delta_loss",
            "completion_bound_retry_gain_loss",
            "tree_policy_loss",
            "total_loss",
        ):
            totals[key] += parts[key]
        count += 1
    averages = {key: 0.0 for key in totals}
    if count > 0:
        for key in (
            "branch_loss",
            "tail_loss",
            "walltime_gain_loss",
            "child_proof_cpu_loss",
            "time_to_certificate_loss",
            "gap_improvement_loss",
            "primal_improvement_loss",
            "dual_bound_gain_loss",
            "fathom_gain_loss",
            "branch_count_delta_loss",
            "completion_bound_retry_gain_loss",
            "tree_policy_loss",
            "total_loss",
        ):
            averages[key] = totals[key] / float(count)
    pairwise = _run_tree_policy_pairwise_epoch(
        model,
        samples,
        device,
        optimizer,
        margin=float(tree_policy_pairwise_margin),
    )
    averages.update(pairwise)
    averages["total_loss"] += float(tree_policy_pairwise_loss_multiplier) * float(
        pairwise["tree_policy_pairwise_loss"]
    )
    return averages


def _branch_priority_metrics(model: GATBranchImpactModel, samples: list[Any], device: torch.device) -> dict[str, float]:
    model.eval()
    labels: list[int] = []
    predictions: list[int] = []
    scores: list[float] = []
    with torch.no_grad():
        for sample in samples:
            sample = sample.to(device)
            if float(sample.branch_priority_loss_weight.sum().detach().cpu()) <= 0.0:
                continue
            output = model(
                sample,
                sample.branch_pair_indices,
                sample.branch_pair_features,
                sample.context_features,
            )
            probability = float(output["branch_priority_probability"].view(-1)[0].detach().cpu())
            label = int(float(sample.y_branch_priority.view(-1)[0].detach().cpu()) > 0.5)
            labels.append(label)
            predictions.append(1 if probability >= 0.5 else 0)
            scores.append(probability)
    tp = sum(1 for label, pred in zip(labels, predictions) if label == 1 and pred == 1)
    fp = sum(1 for label, pred in zip(labels, predictions) if label == 0 and pred == 1)
    fn = sum(1 for label, pred in zip(labels, predictions) if label == 1 and pred == 0)
    tn = sum(1 for label, pred in zip(labels, predictions) if label == 0 and pred == 0)
    precision = tp / float(tp + fp) if tp + fp else 0.0
    recall = tp / float(tp + fn) if tp + fn else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "weighted_row_count": float(len(labels)),
        "positive_count": float(sum(labels)),
        "negative_count": float(len(labels) - sum(labels)),
        "tp": float(tp),
        "fp": float(fp),
        "fn": float(fn),
        "tn": float(tn),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "mean_score": sum(scores) / float(len(scores)) if scores else 0.0,
    }


def train_branch_action_sanity(args: argparse.Namespace | TrainBranchActionSanityArgs) -> dict[str, Any]:
    random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    dataset_dir = Path(args.dataset_dir)
    manifest = _load_json(dataset_dir / "manifest.json")
    _assert_manifest(manifest, args)
    train_items, validation_items = _split_items(
        manifest,
        validation_fraction=float(args.validation_fraction),
        seed=int(args.seed),
    )
    train_samples = [_load_sample(dataset_dir / item["path"]) for item in train_items]
    validation_samples = [_load_sample(dataset_dir / item["path"]) for item in validation_items]
    if not train_samples:
        raise SystemExit("empty branch/action training split")
    first = train_samples[0]
    device = torch.device(str(args.device))
    model = _make_model(first, manifest, args).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(args.lr),
        weight_decay=float(args.weight_decay),
    )
    best_state: dict[str, torch.Tensor] | None = None
    best_selection_loss = float("inf")
    history: list[dict[str, float]] = []
    for epoch in range(1, int(args.epochs) + 1):
        train_loss = _run_epoch(
            model,
            train_samples,
            device,
            optimizer,
            branch_priority_loss_multiplier=float(args.branch_priority_loss_multiplier),
            branch_positive_loss_multiplier=float(args.branch_positive_loss_multiplier),
            tail_aux_loss_multiplier=float(args.tail_aux_loss_multiplier),
            walltime_gain_loss_multiplier=float(args.walltime_gain_loss_multiplier),
            child_proof_cpu_loss_multiplier=float(args.child_proof_cpu_loss_multiplier),
            time_to_certificate_loss_multiplier=float(args.time_to_certificate_loss_multiplier),
            gap_improvement_loss_multiplier=float(args.gap_improvement_loss_multiplier),
            primal_improvement_loss_multiplier=float(args.primal_improvement_loss_multiplier),
            dual_bound_gain_loss_multiplier=float(args.dual_bound_gain_loss_multiplier),
            fathom_gain_loss_multiplier=float(args.fathom_gain_loss_multiplier),
            branch_count_delta_loss_multiplier=float(args.branch_count_delta_loss_multiplier),
            completion_bound_retry_gain_loss_multiplier=float(args.completion_bound_retry_gain_loss_multiplier),
            tree_policy_loss_multiplier=float(args.tree_policy_loss_multiplier),
            tree_policy_pairwise_loss_multiplier=float(args.tree_policy_pairwise_loss_multiplier),
            tree_policy_pairwise_margin=float(args.tree_policy_pairwise_margin),
        )
        validation_loss = _run_epoch(
            model,
            validation_samples,
            device,
            None,
            branch_priority_loss_multiplier=float(args.branch_priority_loss_multiplier),
            branch_positive_loss_multiplier=float(args.branch_positive_loss_multiplier),
            tail_aux_loss_multiplier=float(args.tail_aux_loss_multiplier),
            walltime_gain_loss_multiplier=float(args.walltime_gain_loss_multiplier),
            child_proof_cpu_loss_multiplier=float(args.child_proof_cpu_loss_multiplier),
            time_to_certificate_loss_multiplier=float(args.time_to_certificate_loss_multiplier),
            gap_improvement_loss_multiplier=float(args.gap_improvement_loss_multiplier),
            primal_improvement_loss_multiplier=float(args.primal_improvement_loss_multiplier),
            dual_bound_gain_loss_multiplier=float(args.dual_bound_gain_loss_multiplier),
            fathom_gain_loss_multiplier=float(args.fathom_gain_loss_multiplier),
            branch_count_delta_loss_multiplier=float(args.branch_count_delta_loss_multiplier),
            completion_bound_retry_gain_loss_multiplier=float(args.completion_bound_retry_gain_loss_multiplier),
            tree_policy_loss_multiplier=float(args.tree_policy_loss_multiplier),
            tree_policy_pairwise_loss_multiplier=float(args.tree_policy_pairwise_loss_multiplier),
            tree_policy_pairwise_margin=float(args.tree_policy_pairwise_margin),
        )
        history_row = {
            "epoch": float(epoch),
            "train_total_loss": train_loss["total_loss"],
            "train_branch_loss": train_loss["branch_loss"],
            "train_tail_loss": train_loss["tail_loss"],
            "train_walltime_gain_loss": train_loss["walltime_gain_loss"],
            "train_child_proof_cpu_loss": train_loss["child_proof_cpu_loss"],
            "train_time_to_certificate_loss": train_loss["time_to_certificate_loss"],
            "train_gap_improvement_loss": train_loss["gap_improvement_loss"],
            "train_primal_improvement_loss": train_loss["primal_improvement_loss"],
            "train_dual_bound_gain_loss": train_loss["dual_bound_gain_loss"],
            "train_fathom_gain_loss": train_loss["fathom_gain_loss"],
            "train_branch_count_delta_loss": train_loss["branch_count_delta_loss"],
            "train_completion_bound_retry_gain_loss": train_loss["completion_bound_retry_gain_loss"],
            "train_tree_policy_loss": train_loss["tree_policy_loss"],
            "train_tree_policy_pairwise_loss": train_loss["tree_policy_pairwise_loss"],
            "train_tree_policy_pairwise_group_count": train_loss["tree_policy_pairwise_group_count"],
            "train_tree_policy_pairwise_pair_count": train_loss["tree_policy_pairwise_pair_count"],
            "validation_total_loss": validation_loss["total_loss"],
            "validation_branch_loss": validation_loss["branch_loss"],
            "validation_tail_loss": validation_loss["tail_loss"],
            "validation_walltime_gain_loss": validation_loss["walltime_gain_loss"],
            "validation_child_proof_cpu_loss": validation_loss["child_proof_cpu_loss"],
            "validation_time_to_certificate_loss": validation_loss["time_to_certificate_loss"],
            "validation_gap_improvement_loss": validation_loss["gap_improvement_loss"],
            "validation_primal_improvement_loss": validation_loss["primal_improvement_loss"],
            "validation_dual_bound_gain_loss": validation_loss["dual_bound_gain_loss"],
            "validation_fathom_gain_loss": validation_loss["fathom_gain_loss"],
            "validation_branch_count_delta_loss": validation_loss["branch_count_delta_loss"],
            "validation_completion_bound_retry_gain_loss": validation_loss["completion_bound_retry_gain_loss"],
            "validation_tree_policy_loss": validation_loss["tree_policy_loss"],
            "validation_tree_policy_pairwise_loss": validation_loss["tree_policy_pairwise_loss"],
            "validation_tree_policy_pairwise_group_count": validation_loss[
                "tree_policy_pairwise_group_count"
            ],
            "validation_tree_policy_pairwise_pair_count": validation_loss["tree_policy_pairwise_pair_count"],
        }
        history.append(history_row)
        selection_mode = str(getattr(args, "checkpoint_selection", "validation_total"))
        if selection_mode == "last":
            selection_loss = float(epoch)
        elif selection_mode == "train_total":
            selection_loss = float(train_loss["total_loss"])
        else:
            selection_loss = float(validation_loss["total_loss"])
        should_save = True if selection_mode == "last" else selection_loss <= best_selection_loss
        if should_save:
            best_selection_loss = selection_loss
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        print(
            "epoch="
            f"{epoch} train_total_loss={train_loss['total_loss']:.6f} "
            f"validation_total_loss={validation_loss['total_loss']:.6f}",
            flush=True,
        )
    if best_state is not None:
        model.load_state_dict(best_state)
    train_metrics = _branch_priority_metrics(model, train_samples, device)
    validation_metrics = _branch_priority_metrics(model, validation_samples, device)
    checkpoint = {
        "version": "gat_branch_action_sanity_v3_structural_aux",
        "model_state_dict": model.state_dict(),
        "model_config": {
            "node_dim": int(first.x.size(1)),
            "option_dim": int(first.option_feat.size(1)),
            "branch_feature_dim": len(manifest["branch_feature_schema"]),
            "context_feature_dim": len(manifest["context_feature_schema"]),
            "hidden_dim": int(args.hidden_dim),
            "option_hidden_dim": int(args.option_hidden_dim),
            "pair_edge_dim": int(args.pair_edge_dim),
            "num_gnn_layers": int(args.num_gnn_layers),
            "heads": int(args.heads),
            "dropout": float(args.dropout),
            "branch_hidden_dim": int(args.branch_hidden_dim),
            "context_hidden_dim": int(args.context_hidden_dim),
            "impact_hidden_dim": int(args.impact_hidden_dim),
        },
        "branch_feature_schema": list(manifest["branch_feature_schema"]),
        "context_feature_schema": list(manifest["context_feature_schema"]),
        "label_schema": list(manifest["label_schema"]),
        "target_wall": float(manifest.get("target_wall") or 200.0),
        "exactness_contract": branch_impact_exactness_contract(),
        "training_boundary": {
            "sanity_only": True,
            "production_ready": False,
            "solver_default_effect": False,
            "score_map_exported": False,
            "target_label": "walltime_gain_vs_full_run_regression",
            "target_wall_is_acceptance_metric_only": True,
            "has_walltime_gain_regression_head": True,
            "has_child_proof_cpu_regression_head": True,
            "has_time_to_certificate_regression_head": True,
            "has_gap_improvement_regression_head": True,
            "has_primal_improvement_regression_head": True,
            "has_dual_bound_gain_regression_head": True,
            "has_fathom_gain_regression_head": True,
            "has_branch_count_delta_regression_head": True,
            "has_completion_bound_retry_gain_regression_head": True,
            "has_tree_policy_head": True,
        },
    }
    checkpoint_path = Path(args.checkpoint_out)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, checkpoint_path)
    summary = {
        "schema_version": "gat_branch_action_sanity_training_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "production_ready": False,
        "solver_default_effect": False,
        "score_map_exported": False,
        "dataset_dir": str(dataset_dir),
        "checkpoint_out": str(checkpoint_path),
        "metrics_out": str(args.metrics_out),
        "sample_count": int(manifest.get("sample_count") or 0),
        "train_sample_count": len(train_samples),
        "validation_sample_count": len(validation_samples),
        "branch_priority_label_counts": dict(manifest.get("branch_priority_label_counts") or {}),
        "row_kind_counts": dict(manifest.get("row_kind_counts") or {}),
        "epochs": int(args.epochs),
        "loss_multipliers": {
            "branch_priority": float(args.branch_priority_loss_multiplier),
            "branch_positive": float(args.branch_positive_loss_multiplier),
            "tail_aux": float(args.tail_aux_loss_multiplier),
            "walltime_gain": float(args.walltime_gain_loss_multiplier),
            "child_proof_cpu": float(args.child_proof_cpu_loss_multiplier),
            "time_to_certificate": float(args.time_to_certificate_loss_multiplier),
            "gap_improvement": float(args.gap_improvement_loss_multiplier),
            "primal_improvement": float(args.primal_improvement_loss_multiplier),
            "dual_bound_gain": float(args.dual_bound_gain_loss_multiplier),
            "fathom_gain": float(args.fathom_gain_loss_multiplier),
            "branch_count_delta": float(args.branch_count_delta_loss_multiplier),
            "completion_bound_retry_gain": float(args.completion_bound_retry_gain_loss_multiplier),
            "tree_policy": float(args.tree_policy_loss_multiplier),
            "tree_policy_pairwise": float(args.tree_policy_pairwise_loss_multiplier),
            "tree_policy_pairwise_margin": float(args.tree_policy_pairwise_margin),
        },
        "checkpoint_selection": str(getattr(args, "checkpoint_selection", "validation_total")),
        "history": history,
        "train_branch_priority_metrics": train_metrics,
        "validation_branch_priority_metrics": validation_metrics,
        "sanity_training_completed": True,
        "serious_training_ready": False,
        "optin_training_ready": False,
        "all_checks_pass": True,
    }
    metrics_path = Path(args.metrics_out)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(args.report), summary)
    return summary


def _assert_manifest(manifest: dict[str, Any], args: argparse.Namespace | TrainBranchActionSanityArgs) -> None:
    if manifest.get("schema_version") != "gat_branch_action_sanity_dataset_manifest_v1":
        raise SystemExit("unsupported branch/action sanity dataset manifest")
    if not manifest.get("diagnostic_only") or manifest.get("official_bound_effect"):
        raise SystemExit("branch/action sanity dataset violates diagnostic-only contract")
    if int(manifest.get("sample_count") or 0) < int(args.min_samples):
        raise SystemExit("not enough branch/action sanity samples")
    label_counts = manifest.get("branch_priority_label_counts")
    if not isinstance(label_counts, dict):
        raise SystemExit("manifest missing branch_priority_label_counts")
    legacy_min_target_positive = getattr(args, "min_target_positive", None)
    min_walltime_positive = int(
        legacy_min_target_positive
        if legacy_min_target_positive is not None
        else getattr(args, "min_walltime_positive", 3)
    )
    if int(label_counts.get("walltime_gain_positive") or 0) < min_walltime_positive:
        raise SystemExit("not enough wall-time gain positives for sanity training")
    if int(label_counts.get("not_walltime_gain") or 0) < int(args.min_hard_negative):
        raise SystemExit("not enough hard-negative regressions for sanity training")


def _write_report(report: Path, summary: dict[str, Any]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Branch/Action Sanity Training",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "用 v430 random-TW branch/action dataset 做一次离线训练，验证 GAT branch/action head 的数据、loss 和 checkpoint 链路。该 checkpoint 不接入 solver 默认行为，score map 只能显式 opt-in 导出和使用。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"dataset_dir = {summary['dataset_dir']}",
        f"checkpoint_out = {summary['checkpoint_out']}",
        f"sample_count = {summary['sample_count']}",
        f"train_sample_count = {summary['train_sample_count']}",
        f"validation_sample_count = {summary['validation_sample_count']}",
        f"branch_priority_label_counts = {summary['branch_priority_label_counts']}",
        f"row_kind_counts = {summary['row_kind_counts']}",
        f"epochs = {summary['epochs']}",
        f"loss_multipliers = {summary['loss_multipliers']}",
        f"train_branch_priority_metrics = {summary['train_branch_priority_metrics']}",
        f"validation_branch_priority_metrics = {summary['validation_branch_priority_metrics']}",
        f"sanity_training_completed = {str(summary['sanity_training_completed']).lower()}",
        f"serious_training_ready = {str(summary['serious_training_ready']).lower()}",
        f"optin_training_ready = {str(summary['optin_training_ready']).lower()}",
        "score_map_exported = false",
        "solver_default_effect = false",
        "runs_bpc_or_pricing = false",
        "official_bound_effect = false",
        "certificate_effect = false",
        "```",
        "",
        "## 边界",
        "",
        "这次训练只证明链路能跑通，不证明模型可泛化，也不证明能加速 20 规模。当前 wall-time gain 正例和 hard negative 数量仍未达到正式训练门槛。",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--checkpoint-out", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--metrics-out", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--lr", type=float, default=1.0e-3)
    parser.add_argument("--weight-decay", type=float, default=1.0e-5)
    parser.add_argument("--hidden-dim", type=int, default=32)
    parser.add_argument("--option-hidden-dim", type=int, default=32)
    parser.add_argument("--pair-edge-dim", type=int, default=32)
    parser.add_argument("--num-gnn-layers", type=int, default=1)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.05)
    parser.add_argument("--branch-hidden-dim", type=int, default=32)
    parser.add_argument("--context-hidden-dim", type=int, default=16)
    parser.add_argument("--impact-hidden-dim", type=int, default=32)
    parser.add_argument("--validation-fraction", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=244)
    parser.add_argument("--min-samples", type=int, default=10)
    parser.add_argument("--min-walltime-positive", type=int, default=3)
    parser.add_argument("--min-hard-negative", type=int, default=3)
    parser.add_argument("--branch-priority-loss-multiplier", type=float, default=1.0)
    parser.add_argument("--branch-positive-loss-multiplier", type=float, default=1.0)
    parser.add_argument("--tail-aux-loss-multiplier", type=float, default=0.25)
    parser.add_argument("--walltime-gain-loss-multiplier", type=float, default=1.0)
    parser.add_argument("--child-proof-cpu-loss-multiplier", type=float, default=0.10)
    parser.add_argument("--time-to-certificate-loss-multiplier", type=float, default=0.10)
    parser.add_argument("--gap-improvement-loss-multiplier", type=float, default=0.10)
    parser.add_argument("--primal-improvement-loss-multiplier", type=float, default=0.05)
    parser.add_argument("--dual-bound-gain-loss-multiplier", type=float, default=0.05)
    parser.add_argument("--fathom-gain-loss-multiplier", type=float, default=0.05)
    parser.add_argument("--branch-count-delta-loss-multiplier", type=float, default=0.05)
    parser.add_argument("--completion-bound-retry-gain-loss-multiplier", type=float, default=0.05)
    parser.add_argument("--tree-policy-loss-multiplier", type=float, default=0.25)
    parser.add_argument("--tree-policy-pairwise-loss-multiplier", type=float, default=0.25)
    parser.add_argument("--tree-policy-pairwise-margin", type=float, default=0.50)
    parser.add_argument(
        "--checkpoint-selection",
        choices=("validation_total", "train_total", "last"),
        default="validation_total",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    summary = train_branch_action_sanity(args)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
