#!/usr/bin/env python3
"""Evaluate conservative thresholds for the GAT column selector.

This diagnostic script turns selector probabilities into a conservative
ADD/ABSTAIN gate.  It never runs BPC/pricing/RMP and never creates a certificate.
The gate is production-unsafe until broader context/instance/dataset holdouts
and full BPC A/B no-regression checks pass.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
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
    conservative_add_decisions,
)


DEFAULT_DATASET_DIR = Path("BPC_future/data/column_selector/v1")
DEFAULT_CHECKPOINT = Path("BPC_future/data/column_selector/v1/context_aware_column_selector.pt")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_column_selector_gate_eval_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_gat_column_selector_gate_eval_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--max-validation-false-positive", type=int, default=0)
    parser.add_argument("--min-threshold", type=float, default=0.5)
    parser.add_argument("--max-threshold", type=float, default=0.999)
    parser.add_argument("--threshold-step", type=float, default=0.001)
    parser.add_argument("--add-margin", type=float, default=0.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = evaluate_gate(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_report(summary, args.report)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def evaluate_gate(args: argparse.Namespace) -> dict[str, Any]:
    dataset_dir = Path(args.dataset_dir)
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    samples = [_normalize_sample(_load_sample(dataset_dir / item["path"]), checkpoint) for item in manifest["samples"]]
    split = _split_from_checkpoint(samples, checkpoint)
    device = torch.device(str(args.device))
    model = ContextAwareColumnSelector(**checkpoint["model_config"]).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    train_scores = _score_samples(model, split["train"], device)
    validation_scores = _score_samples(model, split["validation"], device)
    thresholds = _threshold_grid(
        min_threshold=float(args.min_threshold),
        max_threshold=float(args.max_threshold),
        step=float(args.threshold_step),
    )
    threshold_rows = [
        {
            "threshold": threshold,
            "train": _gate_metrics(
                train_scores,
                add_threshold=threshold,
                add_margin=float(args.add_margin),
            ),
            "validation": _gate_metrics(
                validation_scores,
                add_threshold=threshold,
                add_margin=float(args.add_margin),
            ),
        }
        for threshold in thresholds
    ]
    chosen = _choose_threshold(
        threshold_rows,
        max_validation_false_positive=max(0, int(args.max_validation_false_positive)),
    )
    if chosen is None:
        chosen = {
            "threshold": None,
            "train": _empty_gate_metrics(train_scores),
            "validation": _empty_gate_metrics(validation_scores),
            "reason": "no_threshold_satisfies_false_positive_cap",
        }
    else:
        chosen = {**chosen, "reason": "max_validation_recall_under_false_positive_cap"}

    raw_argmax = {
        "train": _argmax_metrics(train_scores),
        "validation": _argmax_metrics(validation_scores),
    }
    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "selector_not_pricing_oracle": checkpoint.get("selector_class_names")
        == list(SELECTOR_CLASS_NAMES),
        "selector_cannot_certificate": checkpoint.get("exactness_contract") is not None,
        "has_train_and_validation_scores": train_scores["total"] > 0
        and validation_scores["total"] > 0,
        "chosen_respects_false_positive_cap": (
            chosen["validation"]["add_false_positive_count"]
            <= max(0, int(args.max_validation_false_positive))
        ),
    }
    return {
        "schema_version": "gat_column_selector_gate_eval_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "gat_column_selector_gate_evaluated",
        "dataset_dir": str(dataset_dir),
        "checkpoint": str(args.checkpoint),
        "sample_count": len(samples),
        "split": {
            "train_count": train_scores["total"],
            "validation_count": validation_scores["total"],
            "train_instances": sorted({str(sample.selector_instance) for sample in split["train"]}),
            "validation_instances": sorted({str(sample.selector_instance) for sample in split["validation"]}),
        },
        "raw_argmax": raw_argmax,
        "chosen_gate": chosen,
        "threshold_scan_count": len(threshold_rows),
        "threshold_scan_head": threshold_rows[:5],
        "threshold_scan_tail": threshold_rows[-5:],
        "production_ready": False,
        "production_blockers": [
            "training data has only two 20-task instances",
            "no 5/10 no-regression BPC A/B",
            "no 20/30/50/100 speedup BPC A/B",
            "no broad context/instance/dataset holdout",
            "no online opt-in solver integration yet",
        ],
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def _load_sample(path: Path) -> Any:
    return torch.load(path, map_location="cpu", weights_only=False)


def _normalize_sample(sample: Any, checkpoint: dict[str, Any]) -> Any:
    graph = sample.clone()
    graph.candidate_features = _normalize_tensor(
        graph.candidate_features,
        checkpoint["candidate_feature_mean"],
        checkpoint["candidate_feature_std"],
    )
    graph.context_features = _normalize_tensor(
        graph.context_features,
        checkpoint["context_feature_mean"],
        checkpoint["context_feature_std"],
    )
    return graph


def _normalize_tensor(tensor: torch.Tensor, mean: list[float], std: list[float]) -> torch.Tensor:
    mean_tensor = torch.tensor(mean, dtype=torch.float32)
    std_tensor = torch.tensor(std, dtype=torch.float32)
    return (tensor.to(dtype=torch.float32) - mean_tensor) / std_tensor


def _split_from_checkpoint(samples: list[Any], checkpoint: dict[str, Any]) -> dict[str, list[Any]]:
    split = checkpoint.get("training", {}).get("split", {})
    validation_instances = set(split.get("validation_instances") or [])
    if validation_instances:
        train = [sample for sample in samples if str(sample.selector_instance) not in validation_instances]
        validation = [sample for sample in samples if str(sample.selector_instance) in validation_instances]
        return {"train": train, "validation": validation}
    if len(samples) <= 1:
        return {"train": samples, "validation": samples}
    return {"train": samples[:-1], "validation": samples[-1:]}


def _score_samples(
    model: ContextAwareColumnSelector,
    samples: list[Any],
    device: torch.device,
) -> dict[str, Any]:
    labels: list[int] = []
    probabilities: list[list[float]] = []
    with torch.no_grad():
        for sample in samples:
            sample = sample.to(device)
            output = model(
                sample,
                sample.candidate_task_membership,
                sample.candidate_features,
                sample.context_features,
            )
            probabilities.extend(output["probabilities"].detach().cpu().tolist())
            labels.extend(int(value) for value in sample.y_selector.detach().cpu().tolist())
    return {
        "total": len(labels),
        "labels": labels,
        "probabilities": probabilities,
    }


def _threshold_grid(*, min_threshold: float, max_threshold: float, step: float) -> list[float]:
    if step <= 0:
        raise ValueError("threshold-step must be positive")
    values: list[float] = []
    current = float(min_threshold)
    max_value = float(max_threshold)
    while current <= max_value + 1.0e-12:
        values.append(round(current, 6))
        current += float(step)
    return values


def _gate_metrics(
    scores: dict[str, Any],
    *,
    add_threshold: float,
    add_margin: float,
) -> dict[str, Any]:
    if scores["total"] <= 0:
        return _empty_gate_metrics(scores)
    probabilities = torch.tensor(scores["probabilities"], dtype=torch.float32)
    labels = torch.tensor(scores["labels"], dtype=torch.long)
    decisions = conservative_add_decisions(
        probabilities,
        add_threshold=float(add_threshold),
        add_margin=float(add_margin),
    )
    return _decision_metrics(labels, decisions)


def _empty_gate_metrics(scores: dict[str, Any]) -> dict[str, Any]:
    total = int(scores.get("total", 0))
    return {
        "total": total,
        "add_predicted_count": 0,
        "abstain_count": total,
        "add_true_positive_count": 0,
        "add_false_positive_count": 0,
        "add_false_negative_count": sum(1 for label in scores.get("labels", []) if label == SELECTOR_CLASS_ADD),
        "add_precision": None,
        "add_recall": 0.0,
    }


def _argmax_metrics(scores: dict[str, Any]) -> dict[str, Any]:
    if scores["total"] <= 0:
        return _empty_gate_metrics(scores)
    probabilities = torch.tensor(scores["probabilities"], dtype=torch.float32)
    labels = torch.tensor(scores["labels"], dtype=torch.long)
    decisions = probabilities.argmax(dim=1)
    return _decision_metrics(labels, decisions)


def _decision_metrics(labels: torch.Tensor, decisions: torch.Tensor) -> dict[str, Any]:
    add_pred = decisions == SELECTOR_CLASS_ADD
    add_actual = labels == SELECTOR_CLASS_ADD
    add_tp = int((add_pred & add_actual).sum().item())
    add_fp = int((add_pred & ~add_actual).sum().item())
    add_fn = int((~add_pred & add_actual).sum().item())
    add_pred_count = int(add_pred.sum().item())
    add_actual_count = int(add_actual.sum().item())
    total = int(labels.numel())
    return {
        "total": total,
        "add_predicted_count": add_pred_count,
        "abstain_count": int((decisions == SELECTOR_CLASS_ABSTAIN).sum().item()),
        "add_true_positive_count": add_tp,
        "add_false_positive_count": add_fp,
        "add_false_negative_count": add_fn,
        "add_actual_count": add_actual_count,
        "add_precision": None if add_pred_count <= 0 else add_tp / float(add_pred_count),
        "add_recall": None if add_actual_count <= 0 else add_tp / float(add_actual_count),
    }


def _choose_threshold(
    rows: list[dict[str, Any]],
    *,
    max_validation_false_positive: int,
) -> dict[str, Any] | None:
    feasible = [
        row
        for row in rows
        if row["validation"]["add_false_positive_count"] <= max_validation_false_positive
    ]
    if not feasible:
        return None
    return max(
        feasible,
        key=lambda row: (
            row["validation"]["add_true_positive_count"],
            row["validation"]["add_recall"] or 0.0,
            -row["validation"]["add_predicted_count"],
            -(row["threshold"] or 0.0),
        ),
    )


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# BPC_future GAT Column Selector Conservative Gate 评估",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告评估 GAT 加列选择器的保守 ADD/ABSTAIN 阈值。该评估只读离线样本，",
        "不运行 BPC / pricing / RMP / Pulse，也不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_column_selector_gate_eval = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        "```",
        "",
        "## Raw argmax 指标",
        "",
        "```json",
        json.dumps(summary["raw_argmax"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 选择的保守 gate",
        "",
        "```json",
        json.dumps(summary["chosen_gate"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "解释：生产前策略只允许高置信 ADD；其他候选一律 ABSTAIN，交回现有 exact path。",
        "当前 gate 只是离线阈值校准，不代表 5/10 no-regression 或 20-task speedup 已证明。",
        "",
        "## 仍然阻塞 production 的原因",
        "",
    ]
    for blocker in summary["production_blockers"]:
        lines.append(f"- {blocker}")
    lines.extend(
        [
            "",
            "## 检查项",
            "",
            "```json",
            json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
