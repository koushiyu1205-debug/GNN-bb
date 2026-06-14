#!/usr/bin/env python3
"""Train a trajectory-labeled GAT CBF impact/barrier selector.

The checkpoint predicts H-step trajectory CBF labels for a batch of returned
journeys.  It is diagnostic-only: it is not a pricing oracle, cannot certify
no-negative, and cannot create official bounds.
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
from BPC_future.scripts.train_gnn_column_selector import (
    _classification_metrics,
    _class_weights,
    _evaluate_loss,
    _load_sample,
    _normalize_sample,
    _run_epoch,
    _split_samples,
)


DEFAULT_DATASET_DIR = Path("BPC_future/data/gat_trajectory_cbf/v1")
DEFAULT_CHECKPOINT = Path(
    "BPC_future/data/gat_trajectory_cbf/v1/context_aware_trajectory_cbf_gat.pt"
)
DEFAULT_METRICS = Path("BPC_future/results/gat_trajectory_cbf_training_20260614/summary.json")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_gat_trajectory_cbf_training_zh.md"
)


@dataclass(frozen=True)
class TrainTrajectoryArgs:
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
    selector_hidden_dim: int = 32
    num_gnn_layers: int = 1
    heads: int = 4
    dropout: float = 0.05
    validation_fraction: float = 0.25
    seed: int = 23


def parse_args() -> argparse.Namespace:
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
    parser.add_argument("--selector-hidden-dim", type=int, default=32)
    parser.add_argument("--num-gnn-layers", type=int, default=1)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.05)
    parser.add_argument("--validation-fraction", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=23)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = train_trajectory_cbf(args)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def train_trajectory_cbf(args: argparse.Namespace | TrainTrajectoryArgs) -> dict[str, Any]:
    random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    dataset_dir = Path(args.dataset_dir)
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    if "label_horizon_cbf_feasible" not in set(manifest.get("label_schema") or []):
        raise ValueError("trajectory GAT dataset must include label_horizon_cbf_feasible")
    samples = [_load_sample(dataset_dir / item["path"]) for item in manifest.get("samples", [])]
    if not samples:
        raise SystemExit("empty trajectory GAT dataset")
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
        "version": "context_aware_trajectory_cbf_gat_v1",
        "target_label": "label_horizon_cbf_feasible",
        "label_schema": list(manifest.get("label_schema") or []),
        "trajectory_contract": {
            "horizon_label": "label_horizon_cbf_feasible",
            "unsafe_negative_action": "delay_queue_not_discard",
            "certificate_source": False,
            "pricing_oracle": False,
            "official_bound_effect": False,
        },
        "exactness_contract": (
            "Trajectory CBF impact predictor only; never a pricing oracle, "
            "certificate source, official lower-bound source, or permanent "
            "filter for true-RC negative columns."
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
    Path(args.checkpoint_out).parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, args.checkpoint_out)
    summary = {
        "schema_version": "gat_trajectory_cbf_training_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "gat_trajectory_cbf_trained",
        "dataset_dir": str(dataset_dir),
        "checkpoint_out": str(args.checkpoint_out),
        "sample_count": len(samples),
        "candidate_count": int(manifest.get("candidate_count") or 0),
        "train_count": len(split.train),
        "validation_count": len(split.validation),
        "split": split.info,
        "train_metrics": train_metrics,
        "validation_metrics": validation_metrics,
        "best_validation_loss": best_val_loss,
        "target_label": "label_horizon_cbf_feasible",
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "production_ready": False,
        "all_checks_pass": bool(
            train_metrics.get("total", 0) > 0
            and validation_metrics.get("total", 0) > 0
            and checkpoint["selector_class_names"] == list(SELECTOR_CLASS_NAMES)
            and checkpoint["target_label"] == "label_horizon_cbf_feasible"
            and not checkpoint["trajectory_contract"]["certificate_source"]
        ),
    }
    Path(args.metrics_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.metrics_out).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _write_report(Path(args.report), summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Trajectory CBF Training 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "训练 trajectory-labeled GAT CBF impact/barrier checkpoint。该 checkpoint",
        "只用于离线表示学习和后续 kNN/OOD safety-shell 验证，不运行 BPC / pricing /",
        "RMP，不生成 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_trajectory_cbf_training = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"sample_count = {summary['sample_count']}",
        f"candidate_count = {summary['candidate_count']}",
        f"target_label = {summary['target_label']}",
        f"selector_can_certificate = {str(summary['selector_can_certificate']).lower()}",
        f"selector_is_pricing_oracle = {str(summary['selector_is_pricing_oracle']).lower()}",
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
                "best_validation_loss": summary["best_validation_loss"],
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
        "- unsafe true-RC negative 只能进入 delay queue，不能永久丢弃；",
        "- 后续必须接 kNN/OOD safety shell 并做独立 sector-wave / 5/10 / 20 ROI 验证。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
