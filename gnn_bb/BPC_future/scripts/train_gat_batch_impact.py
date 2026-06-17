#!/usr/bin/env python3
"""Train the offline GAT batch-impact admission model.

This trainer targets deployment-facing metrics instead of F1-only selection.
It is diagnostic-only: the checkpoint may be used for offline ranking and
threshold audit, but it is not a pricing oracle, certificate source, official
bound source, or permission to permanently discard true-RC negative columns.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
import json
import math
from pathlib import Path
import random
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch
import torch.nn.functional as F

from BPC_future.learning.batch_impact_model import (
    BATCH_IMPACT_EXACTNESS_CONTRACT,
    GATBatchImpactModel,
    batch_impact_exactness_contract,
)


DEFAULT_DATASET_DIR = Path("BPC_future/data/gat_batch_impact/v1")
DEFAULT_CHECKPOINT = Path("BPC_future/data/gat_batch_impact/v1/gat_batch_impact.pt")
DEFAULT_METRICS = Path("BPC_future/results/gat_batch_impact_training_20260615/summary.json")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260615_bpc_future_gat_batch_impact_training_zh.md"
)
CHECKPOINT_SELECTION_POLICY = "deployment_gate_first_then_roi_ci_baseline_utility_loss"


@dataclass(frozen=True)
class _Split:
    train: list[Any]
    validation: list[Any]
    info: dict[str, Any]


@dataclass(frozen=True)
class TrainBatchImpactArgs:
    dataset_dir: Path = DEFAULT_DATASET_DIR
    checkpoint_out: Path = DEFAULT_CHECKPOINT
    metrics_out: Path = DEFAULT_METRICS
    report: Path = DEFAULT_REPORT
    device: str = "cpu"
    epochs: int = 8
    lr: float = 1.0e-3
    weight_decay: float = 1.0e-5
    hidden_dim: int = 32
    option_hidden_dim: int = 32
    pair_edge_dim: int = 32
    candidate_hidden_dim: int = 32
    context_hidden_dim: int = 24
    batch_hidden_dim: int = 32
    impact_hidden_dim: int = 32
    path_token_dim: int = 16
    path_hidden_dim: int = 32
    num_gnn_layers: int = 1
    heads: int = 4
    dropout: float = 0.05
    validation_fraction: float = 0.25
    seed: int = 41
    min_samples: int = 1
    stage3_min_samples: int = 200
    min_roi_positive_batches: int = 5
    min_delay_candidates: int = 5
    min_major_families: int = 2
    min_validation_high_priority_precision: float = 0.90
    min_validation_high_priority_precision_ci_low: float | None = None
    min_validation_safe_precision: float = 0.90
    min_validation_safe_precision_ci_low: float | None = None
    confidence_z: float = 1.96
    max_false_high_priority_on_delay: float = 0.01
    max_false_safe_union_rate: float = 0.02
    max_accepted_bad_mode_count: int = 0
    min_accepted_batch_count: int = 1
    min_accepted_batch_rate: float = 0.02
    min_accepted_batch_roi: float = 0.65
    min_accepted_batch_roi_ci_low: float | None = None
    baseline_accepted_batch_roi: float = 0.0
    random_baseline_accepted_batch_roi: float | None = None
    best_rc_baseline_accepted_batch_roi: float | None = None
    old_gat_baseline_accepted_batch_roi: float | None = None
    min_roi_margin_over_baseline: float = 0.20
    min_family_holdout_precision: float = 0.80
    min_family_holdout_accepted_roi: float | None = None
    min_family_accepted_high_roi_count: int = 0
    min_family_high_roi_capture_rate: float = 0.0
    false_high_priority_loss_multiplier: float = 4.0
    bad_mode_loss_multiplier: float = 2.0
    regression_loss_multiplier: float = 0.15
    hard_roi_loss_multiplier: float = 1.0
    hard_roi_candidate_loss_multiplier: float = 0.5
    hard_roi_positive_candidate_loss_multiplier: float = 0.0
    hard_roi_positive_group_balance: str = "none"
    hard_roi_positive_group_weight_power: float = 0.5
    max_hard_roi_positive_group_weight: float = 4.0
    hard_roi_threshold: float | None = None
    candidate_delay_loss_multiplier: float = 0.5
    hard_roi_negative_delay_loss_multiplier: float = 0.0
    hard_roi_safe_delay_loss_multiplier: float = 0.0
    candidate_admission_score_mode: str = "high_priority"
    candidate_delay_score_penalty: float = 0.0
    candidate_delay_gate_enabled: bool = False
    candidate_delay_risk_threshold: float = 0.5
    candidate_rescue_raw_score_threshold: float = 1.0
    candidate_rescue_delay_risk_threshold: float = 1.0
    candidate_rescue_delay_score_penalty: float = 0.0
    pairwise_ranking_loss_multiplier: float = 1.0
    pairwise_candidate_ranking_loss_multiplier: float = 0.75
    pairwise_false_delay_contrast_loss_multiplier: float = 0.5
    pairwise_delay_risk_contrast_loss_multiplier: float = 0.0
    focused_pair_loss_multiplier: float = 0.0
    focused_pair_candidate_loss_multiplier: float = 0.0
    focused_pair_admission_loss_multiplier: float = 0.0
    focused_pair_delay_risk_loss_multiplier: float = 0.0
    focused_pair_batch_loss_multiplier: float = 0.0
    pairwise_roi_margin: float = 0.05
    min_pairwise_roi_delta: float = 1.0e-6
    focused_pair_gate_row_index_min: int | None = None
    focused_pair_row_indices_file: Path | None = None
    min_focused_pair_count: int = 1
    min_focused_raw_pair_pass_rate: float = 1.0
    min_focused_admission_pair_pass_rate: float = 1.0
    min_focused_delay_risk_pair_pass_rate: float = 1.0
    min_focused_strict_pair_pass_rate: float = 1.0
    require_positive_candidate_threshold: bool = True
    max_grad_norm: float = 5.0
    max_nonfinite_skipped_update_rate: float = 0.02


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--checkpoint-out", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--metrics-out", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1.0e-3)
    parser.add_argument("--weight-decay", type=float, default=1.0e-5)
    parser.add_argument("--hidden-dim", type=int, default=32)
    parser.add_argument("--option-hidden-dim", type=int, default=32)
    parser.add_argument("--pair-edge-dim", type=int, default=32)
    parser.add_argument("--candidate-hidden-dim", type=int, default=32)
    parser.add_argument("--context-hidden-dim", type=int, default=24)
    parser.add_argument("--batch-hidden-dim", type=int, default=32)
    parser.add_argument("--impact-hidden-dim", type=int, default=32)
    parser.add_argument("--path-token-dim", type=int, default=16)
    parser.add_argument("--path-hidden-dim", type=int, default=32)
    parser.add_argument("--num-gnn-layers", type=int, default=1)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.05)
    parser.add_argument("--validation-fraction", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=41)
    parser.add_argument("--min-samples", type=int, default=1)
    parser.add_argument("--stage3-min-samples", type=int, default=200)
    parser.add_argument("--min-roi-positive-batches", type=int, default=5)
    parser.add_argument("--min-delay-candidates", type=int, default=5)
    parser.add_argument("--min-major-families", type=int, default=2)
    parser.add_argument("--min-validation-high-priority-precision", type=float, default=0.90)
    parser.add_argument("--min-validation-high-priority-precision-ci-low", type=float, default=None)
    parser.add_argument("--min-validation-safe-precision", type=float, default=0.90)
    parser.add_argument("--min-validation-safe-precision-ci-low", type=float, default=None)
    parser.add_argument("--confidence-z", type=float, default=1.96)
    parser.add_argument("--max-false-high-priority-on-delay", type=float, default=0.01)
    parser.add_argument("--max-false-safe-union-rate", type=float, default=0.02)
    parser.add_argument(
        "--max-accepted-bad-mode-count",
        type=int,
        default=0,
        help=(
            "Maximum accepted batches with label_bad_mode_switch=1. Default 0 "
            "makes accepted bad-mode a hard Stage 3 rejection instead of a "
            "rate that can be averaged away."
        ),
    )
    parser.add_argument("--min-accepted-batch-count", type=int, default=1)
    parser.add_argument("--min-accepted-batch-rate", type=float, default=0.02)
    parser.add_argument("--min-accepted-batch-roi", type=float, default=0.65)
    parser.add_argument("--min-accepted-batch-roi-ci-low", type=float, default=None)
    parser.add_argument("--baseline-accepted-batch-roi", type=float, default=0.0)
    parser.add_argument("--random-baseline-accepted-batch-roi", type=float, default=None)
    parser.add_argument("--best-rc-baseline-accepted-batch-roi", type=float, default=None)
    parser.add_argument("--old-gat-baseline-accepted-batch-roi", type=float, default=None)
    parser.add_argument("--min-roi-margin-over-baseline", type=float, default=0.20)
    parser.add_argument("--min-family-holdout-precision", type=float, default=0.80)
    parser.add_argument(
        "--min-family-holdout-accepted-roi",
        type=float,
        default=None,
        help=(
            "Minimum per-family accepted ROI. Defaults to the same hard ROI "
            "threshold as accepted batches: max(min_accepted_batch_roi, "
            "baseline_accepted_batch_roi + min_roi_margin_over_baseline)."
        ),
    )
    parser.add_argument(
        "--min-family-accepted-high-roi-count",
        type=int,
        default=0,
        help=(
            "Minimum accepted high-ROI batch count for each family that has "
            "oracle high-ROI opportunities. Default 0 preserves legacy behavior."
        ),
    )
    parser.add_argument(
        "--min-family-high-roi-capture-rate",
        type=float,
        default=0.0,
        help=(
            "Minimum accepted/oracle high-ROI capture rate for each family with "
            "oracle high-ROI opportunities. Default 0 preserves legacy behavior."
        ),
    )
    parser.add_argument("--false-high-priority-loss-multiplier", type=float, default=4.0)
    parser.add_argument("--bad-mode-loss-multiplier", type=float, default=2.0)
    parser.add_argument("--regression-loss-multiplier", type=float, default=0.15)
    parser.add_argument(
        "--hard-roi-loss-multiplier",
        type=float,
        default=1.0,
        help=(
            "Additional batch-level admission loss weight. This target treats "
            "a batch as positive only when accepted_batch_roi reaches the same "
            "hard ROI threshold used by the deployment gate."
        ),
    )
    parser.add_argument(
        "--hard-roi-candidate-loss-multiplier",
        type=float,
        default=0.5,
        help=(
            "Additional candidate-level loss weight that suppresses HIGH_PRIORITY "
            "candidate scores for batches below the hard ROI gate."
        ),
    )
    parser.add_argument(
        "--hard-roi-positive-candidate-loss-multiplier",
        type=float,
        default=0.0,
        help=(
            "Extra candidate-head recall pressure for labeled HIGH_PRIORITY "
            "candidates inside non-bad batches whose accepted_batch_roi reaches "
            "the hard ROI gate. Default 0 preserves legacy training behavior."
        ),
    )
    parser.add_argument(
        "--hard-roi-positive-group-balance",
        choices=("none", "family", "task_count", "family_task"),
        default="none",
        help=(
            "Optional group-balanced multiplier for hard-ROI positive candidate "
            "boost loss. Use family_task when high-ROI validation misses cluster "
            "by family and scale. Default none preserves legacy behavior."
        ),
    )
    parser.add_argument(
        "--hard-roi-positive-group-weight-power",
        type=float,
        default=0.5,
        help=(
            "Exponent for inverse hard-ROI group frequency weighting. 0.5 uses "
            "sqrt balancing; 1.0 uses full inverse-frequency balancing."
        ),
    )
    parser.add_argument(
        "--max-hard-roi-positive-group-weight",
        type=float,
        default=4.0,
        help="Upper clip for hard-ROI positive group-balanced loss weights.",
    )
    parser.add_argument(
        "--hard-roi-threshold",
        type=float,
        default=None,
        help=(
            "Optional hard ROI admission threshold for loss shaping. Defaults "
            "to max(min_accepted_batch_roi, baseline_accepted_batch_roi + "
            "min_roi_margin_over_baseline)."
        ),
    )
    parser.add_argument(
        "--candidate-delay-loss-multiplier",
        type=float,
        default=0.5,
        help="Weight for the candidate delay-risk BCE head. Default preserves legacy 0.5 weighting.",
    )
    parser.add_argument(
        "--hard-roi-negative-delay-loss-multiplier",
        type=float,
        default=0.0,
        help=(
            "Extra delay-risk calibration loss for candidates in batches below "
            "the hard ROI gate or in bad-mode batches. Target is delay-risk=1."
        ),
    )
    parser.add_argument(
        "--hard-roi-safe-delay-loss-multiplier",
        type=float,
        default=0.0,
        help=(
            "Extra delay-risk suppression loss for labeled HIGH_PRIORITY "
            "candidates inside hard-ROI positive non-bad batches. Target is delay-risk=0."
        ),
    )
    parser.add_argument(
        "--candidate-admission-score-mode",
        choices=("high_priority", "risk_adjusted_product", "risk_adjusted_rescue_window"),
        default="high_priority",
        help=(
            "Score used by candidate threshold search. high_priority uses the "
            "candidate HIGH_PRIORITY probability. risk_adjusted_product uses "
            "HIGH_PRIORITY * (1 - delay_risk) ** candidate_delay_score_penalty. "
            "risk_adjusted_rescue_window uses the risk-adjusted score, but can "
            "rescue high-raw-score candidates inside a configured delay-risk window."
        ),
    )
    parser.add_argument(
        "--candidate-delay-score-penalty",
        type=float,
        default=0.0,
        help=(
            "Delay-risk penalty exponent for risk_adjusted_product admission "
            "scores and pairwise candidate ranking."
        ),
    )
    parser.add_argument(
        "--candidate-delay-gate-enabled",
        action="store_true",
        help=(
            "Enable the deployment-facing dual gate in offline threshold search: "
            "a candidate is HIGH_PRIORITY only when the high-priority score "
            "passes and the predicted delay-risk score is below threshold."
        ),
    )
    parser.add_argument(
        "--candidate-delay-risk-threshold",
        type=float,
        default=0.5,
        help="Maximum predicted delay-risk probability allowed for HIGH_PRIORITY when the delay gate is enabled.",
    )
    parser.add_argument(
        "--candidate-rescue-raw-score-threshold",
        type=float,
        default=1.0,
        help=(
            "Minimum raw HIGH_PRIORITY probability required for "
            "risk_adjusted_rescue_window eligibility."
        ),
    )
    parser.add_argument(
        "--candidate-rescue-delay-risk-threshold",
        type=float,
        default=1.0,
        help=(
            "Maximum predicted delay-risk probability allowed for "
            "risk_adjusted_rescue_window eligibility."
        ),
    )
    parser.add_argument(
        "--candidate-rescue-delay-score-penalty",
        type=float,
        default=0.0,
        help=(
            "Delay-risk penalty exponent used for rescued admission scores in "
            "risk_adjusted_rescue_window."
        ),
    )
    parser.add_argument(
        "--pairwise-ranking-loss-multiplier",
        type=float,
        default=1.0,
        help=(
            "Same-context ROI pairwise ranking loss weight. Active only when "
            "the training split has comparable same-context batches."
        ),
    )
    parser.add_argument(
        "--pairwise-roi-margin",
        type=float,
        default=0.05,
        help="Margin for ranking higher-ROI same-context batches above lower-ROI batches.",
    )
    parser.add_argument(
        "--pairwise-candidate-ranking-loss-multiplier",
        type=float,
        default=0.75,
        help=(
            "Same-context candidate-head ranking weight. For a higher-ROI "
            "batch, the best labeled safe candidate logit is trained above "
            "the best candidate logit in a lower-ROI batch."
        ),
    )
    parser.add_argument(
        "--pairwise-false-delay-contrast-loss-multiplier",
        type=float,
        default=0.5,
        help=(
            "Same-context hard-negative weight that separates high-ROI safe "
            "candidates from lower-ROI delay candidates in both the "
            "candidate-head and delay-risk heads."
        ),
    )
    parser.add_argument(
        "--pairwise-delay-risk-contrast-loss-multiplier",
        type=float,
        default=0.0,
        help=(
            "Additional same-context delay-risk head ranking weight. This "
            "separately trains positive high-ROI safe candidates to have lower "
            "delay-risk logits than lower-ROI delay / hard-negative candidates."
        ),
    )
    parser.add_argument(
        "--focused-pair-loss-multiplier",
        type=float,
        default=0.0,
        help=(
            "Extra training weight for the fixed focused same-context "
            "positive-vs-hard-negative regression tranche selected by "
            "--focused-pair-gate-row-index-min. Default 0 preserves legacy "
            "training behavior."
        ),
    )
    parser.add_argument(
        "--focused-pair-candidate-loss-multiplier",
        type=float,
        default=0.0,
        help=(
            "Focused tranche raw HIGH_PRIORITY head ranking weight. It trains "
            "labeled positive candidates above labeled delay/hard-negative "
            "candidates. Default 0 preserves legacy behavior."
        ),
    )
    parser.add_argument(
        "--focused-pair-admission-loss-multiplier",
        type=float,
        default=0.0,
        help=(
            "Focused tranche admission-score ranking weight using the same "
            "candidate_admission_score_mode as threshold search. Default 0 "
            "preserves legacy behavior."
        ),
    )
    parser.add_argument(
        "--focused-pair-delay-risk-loss-multiplier",
        type=float,
        default=0.0,
        help=(
            "Focused tranche delay-risk head ranking weight. It trains labeled "
            "delay/hard-negative candidates to have higher delay-risk logits "
            "than labeled positive candidates. Default 0 preserves legacy behavior."
        ),
    )
    parser.add_argument(
        "--focused-pair-batch-loss-multiplier",
        type=float,
        default=0.0,
        help=(
            "Focused tranche batch ROI head ranking weight. Default 0 preserves "
            "legacy behavior."
        ),
    )
    parser.add_argument(
        "--min-pairwise-roi-delta",
        type=float,
        default=1.0e-6,
        help="Minimum accepted ROI difference required to form a same-context ranking pair.",
    )
    parser.add_argument(
        "--focused-pair-gate-row-index-min",
        type=int,
        default=None,
        help=(
            "Optional fixed regression tranche for same-context positive-vs-hard-negative "
            "focused pair gate. Use 383 for the current v77/v80/v82 focused rows."
        ),
    )
    parser.add_argument(
        "--focused-pair-row-indices-file",
        type=Path,
        default=None,
        help=(
            "Optional JSON file containing explicit focused row indices. This "
            "is preferred when a mined tranche is non-contiguous and row_index_min "
            "would include unrelated rows."
        ),
    )
    parser.add_argument(
        "--min-focused-pair-count",
        type=int,
        default=1,
        help="Minimum focused same-context positive-vs-negative pair count.",
    )
    parser.add_argument(
        "--min-focused-raw-pair-pass-rate",
        type=float,
        default=1.0,
        help="Minimum raw candidate-head focused pair pass rate.",
    )
    parser.add_argument(
        "--min-focused-admission-pair-pass-rate",
        type=float,
        default=1.0,
        help="Minimum admission-score focused pair pass rate.",
    )
    parser.add_argument(
        "--min-focused-delay-risk-pair-pass-rate",
        type=float,
        default=1.0,
        help="Minimum delay-risk focused pair pass rate.",
    )
    parser.add_argument(
        "--min-focused-strict-pair-pass-rate",
        type=float,
        default=1.0,
        help="Minimum all-head focused strict pair pass rate.",
    )
    parser.add_argument(
        "--allow-zero-candidate-threshold",
        dest="require_positive_candidate_threshold",
        action="store_false",
        default=True,
        help=(
            "Audit/debug escape hatch. By default Stage 3 rejects candidate_threshold=0 "
            "because it disables the candidate-head admission filter."
        ),
    )
    parser.add_argument("--max-grad-norm", type=float, default=5.0)
    parser.add_argument("--max-nonfinite-skipped-update-rate", type=float, default=0.02)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = train_batch_impact(args)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def train_batch_impact(args: argparse.Namespace | TrainBatchImpactArgs) -> dict[str, Any]:
    random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    dataset_dir = Path(args.dataset_dir)
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    _assert_batch_impact_manifest(manifest, args)

    samples = [_load_sample(dataset_dir / item["path"]) for item in manifest.get("samples", [])]
    if not samples:
        raise SystemExit("empty GAT batch-impact dataset")
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
        "batch_feature_dim": len(manifest["batch_feature_schema"]),
        **_path_token_model_config(manifest, args),
        "hidden_dim": int(args.hidden_dim),
        "option_hidden_dim": int(args.option_hidden_dim),
        "pair_edge_dim": int(args.pair_edge_dim),
        "num_gnn_layers": int(args.num_gnn_layers),
        "heads": int(args.heads),
        "dropout": float(args.dropout),
        "candidate_hidden_dim": int(args.candidate_hidden_dim),
        "context_hidden_dim": int(args.context_hidden_dim),
        "batch_hidden_dim": int(args.batch_hidden_dim),
        "impact_hidden_dim": int(args.impact_hidden_dim),
        "use_layer_norm": True,
    }
    device = torch.device(str(args.device))
    model = GATBatchImpactModel(**model_config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(args.lr), weight_decay=float(args.weight_decay))
    loss_options = _loss_options(args)
    context_pair_stats = {
        "all": _context_pair_stats(samples),
        "train": _context_pair_stats(split.train),
        "validation": _context_pair_stats(split.validation),
    }
    loss_options = _with_hard_roi_positive_group_balance(
        loss_options,
        split.train,
    )
    pairwise_ranking_loss_active = bool(
        _pairwise_loss_enabled(loss_options)
        and int(context_pair_stats["train"]["same_context_comparable_pair_count"]) > 0
    )
    pairwise_ranking_status = _pairwise_ranking_status(
        context_pair_stats,
        loss_options=loss_options,
    )

    best_state: dict[str, torch.Tensor] | None = None
    best_selection_key: tuple[float, float, float, float] | None = None
    best_validation_loss = float("inf")
    selected_validation_loss = float("inf")
    best_epoch = 0
    best_loss_epoch = 0
    best_loss_epoch_gate_pass = False
    best_threshold_metrics: dict[str, Any] = {}
    history: list[dict[str, Any]] = []
    nonfinite_skipped_update_count = 0
    attempted_update_count = 0
    for epoch in range(1, int(args.epochs) + 1):
        train_epoch = _run_epoch(model, split.train, optimizer, device, loss_options=loss_options)
        train_loss = float(train_epoch["loss"])
        nonfinite_skipped_update_count += int(train_epoch["skipped_update_count"])
        attempted_update_count += int(train_epoch["attempted_update_count"])
        validation_loss = _evaluate_loss(model, split.validation, device, loss_options=loss_options)
        threshold_metrics = _threshold_search(
            _prediction_records(model, split.validation, device),
            gate_config=_gate_config(args, manifest),
        )
        selected_metrics = threshold_metrics["selected_metrics"]
        if float(validation_loss) < float(best_validation_loss):
            best_validation_loss = float(validation_loss)
            best_loss_epoch = int(epoch)
            best_loss_epoch_gate_pass = bool(selected_metrics["threshold_local_gate_pass"])
        local_gate_pass_score = 1.0 if selected_metrics["threshold_local_gate_pass"] else 0.0
        selection_key = _checkpoint_selection_key(
            selected_metrics,
            local_gate_pass_score=local_gate_pass_score,
            validation_loss=float(validation_loss),
        )
        history.append(
            {
                "epoch": int(epoch),
                "train_loss": float(train_loss),
                "skipped_update_count": int(train_epoch["skipped_update_count"]),
                "attempted_update_count": int(train_epoch["attempted_update_count"]),
                "nonfinite_skipped_update_rate": (
                    float(train_epoch["skipped_update_count"]) / float(train_epoch["attempted_update_count"])
                    if int(train_epoch["attempted_update_count"]) > 0
                    else 0.0
                ),
                "validation_loss": float(validation_loss),
                "selected_threshold": float(selected_metrics["threshold"]),
                "selected_batch_threshold": float(selected_metrics["batch_threshold"]),
                "selected_candidate_threshold": float(selected_metrics["candidate_threshold"]),
                "checkpoint_gate_pass": bool(selected_metrics["checkpoint_gate_pass"]),
                "threshold_local_gate_pass": bool(selected_metrics["threshold_local_gate_pass"]),
                "accepted_batch_count": int(selected_metrics["accepted_batch_count"]),
                "high_priority_precision": selected_metrics["high_priority_precision"],
                "safe_precision": selected_metrics["safe_precision"],
                "accepted_batch_roi": selected_metrics["accepted_batch_roi"],
                "false_high_priority_on_delay": selected_metrics["false_high_priority_on_delay"],
                "expected_trajectory_utility": selected_metrics["expected_trajectory_utility"],
            }
        )
        if best_selection_key is None or selection_key > best_selection_key:
            best_selection_key = selection_key
            selected_validation_loss = float(validation_loss)
            best_epoch = int(epoch)
            best_threshold_metrics = threshold_metrics
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        print(
            "epoch="
            f"{epoch} train_loss={train_loss:.6f} validation_loss={validation_loss:.6f} "
            f"batch_threshold={selected_metrics['batch_threshold']:.6f} "
            f"candidate_threshold={selected_metrics['candidate_threshold']:.6f} "
            f"gate_pass={str(selected_metrics['checkpoint_gate_pass']).lower()} "
            f"accepted={selected_metrics['accepted_batch_count']} "
            f"precision={selected_metrics['high_priority_precision']}",
            flush=True,
        )

    if best_state is not None:
        model.load_state_dict(best_state)
    gate_config = _gate_config(args, manifest)
    selected_threshold_metrics = best_threshold_metrics.get("selected_metrics", {})
    selected_batch_thresholds_by_family = dict(
        selected_threshold_metrics.get("batch_thresholds_by_family") or {}
    )
    selected_delay_fallback_families = list(
        selected_threshold_metrics.get("family_delay_fallback_families") or []
    )
    selected_context_delay_fallback_contexts = list(
        selected_threshold_metrics.get("context_delay_fallback_contexts") or []
    )
    train_deployment_metrics = _threshold_search(
        _prediction_records(model, split.train, device),
        gate_config=gate_config,
        fixed_batch_threshold=float(selected_threshold_metrics.get("batch_threshold", 0.9)),
        fixed_candidate_threshold=float(
            selected_threshold_metrics.get("candidate_threshold", 0.9)
        ),
        fixed_batch_thresholds_by_family=selected_batch_thresholds_by_family,
        fixed_delay_fallback_families=selected_delay_fallback_families,
        fixed_context_delay_fallback_contexts=selected_context_delay_fallback_contexts,
    )["selected_metrics"]
    validation_threshold_search = _threshold_search(
        _prediction_records(model, split.validation, device),
        gate_config=gate_config,
        fixed_batch_threshold=float(selected_threshold_metrics.get("batch_threshold", 0.9)),
        fixed_candidate_threshold=float(
            selected_threshold_metrics.get("candidate_threshold", 0.9)
        ),
        fixed_batch_thresholds_by_family=selected_batch_thresholds_by_family,
        fixed_delay_fallback_families=selected_delay_fallback_families,
        fixed_context_delay_fallback_contexts=selected_context_delay_fallback_contexts,
    )
    validation_deployment_metrics = validation_threshold_search["selected_metrics"]
    family_holdout_metrics = _family_holdout_metrics(
        _prediction_records(model, split.validation, device),
        batch_threshold=float(validation_deployment_metrics["batch_threshold"]),
        candidate_threshold=float(validation_deployment_metrics["candidate_threshold"]),
        gate_config=gate_config,
        batch_thresholds_by_family=selected_batch_thresholds_by_family,
        delay_fallback_families=selected_delay_fallback_families,
        context_delay_fallback_contexts=selected_context_delay_fallback_contexts,
        min_accepted_batch_roi=float(gate_config["min_family_holdout_accepted_roi"]),
    )
    focused_pair_gate_metrics = _focused_pair_gate_metrics(
        manifest_items=list(manifest.get("samples", [])),
        prediction_records=_prediction_records(model, samples, device),
        gate_config=gate_config,
        args=args,
    )
    focused_pair_gate_reject_reasons = _focused_pair_gate_reject_reasons(
        focused_pair_gate_metrics
    )
    training_run_config = _training_run_config(
        args,
        model_config=model_config,
        gate_config=gate_config,
        loss_options=loss_options,
    )
    nonfinite_skipped_update_rate = (
        float(nonfinite_skipped_update_count) / float(attempted_update_count)
        if attempted_update_count > 0
        else 0.0
    )
    training_stability_reject_reasons = _training_stability_reject_reasons(
        nonfinite_skipped_update_rate=nonfinite_skipped_update_rate,
        max_nonfinite_skipped_update_rate=float(getattr(args, "max_nonfinite_skipped_update_rate", 0.02)),
    )
    checkpoint_extra_reject_reasons = (
        list(training_stability_reject_reasons) + list(focused_pair_gate_reject_reasons)
    )
    checkpoint_gate_pass = bool(
        validation_deployment_metrics["checkpoint_gate_pass"] and not checkpoint_extra_reject_reasons
    )
    stage4_candidate_ready = bool(
        checkpoint_gate_pass
        and False  # kNN/OOD audit is mandatory and not run by this trainer.
    )
    stage4_blockers = sorted(
        set(
            _stage4_blockers(
                validation_deployment_metrics,
                family_holdout_metrics,
                manifest=manifest,
                training_stability_reject_reasons=training_stability_reject_reasons,
            )
            + focused_pair_gate_reject_reasons
        )
    )

    checkpoint = {
        "model_state_dict": model.state_dict(),
        "model_config": model_config,
        "candidate_feature_schema": manifest["candidate_feature_schema"],
        "context_feature_schema": manifest["context_feature_schema"],
        "batch_feature_schema": manifest["batch_feature_schema"],
        "candidate_path_token_schema": manifest.get("candidate_path_token_schema", {}),
        "candidate_feature_mean": manifest["candidate_feature_mean"],
        "candidate_feature_std": manifest["candidate_feature_std"],
        "context_feature_mean": manifest["context_feature_mean"],
        "context_feature_std": manifest["context_feature_std"],
        "batch_feature_mean": manifest["batch_feature_mean"],
        "batch_feature_std": manifest["batch_feature_std"],
        "version": "gat_batch_impact_v1",
        "target_label": "same_context_batch_trajectory_roi",
        "label_schema": list(manifest.get("label_schema") or []),
        "exactness_contract": batch_impact_exactness_contract(),
        "training_contract": {
            "training_objective": "precision_constrained_roi_maximization",
            "checkpoint_selection": CHECKPOINT_SELECTION_POLICY,
            "main_split": split.info,
            "uses_random_row_split": False,
            "uses_post_addition_features_as_inputs": False,
            "hard_roi_threshold": loss_options["hard_roi_threshold"],
            "hard_roi_loss_multiplier": loss_options["hard_roi_loss_multiplier"],
            "hard_roi_candidate_loss_multiplier": loss_options["hard_roi_candidate_loss_multiplier"],
            "hard_roi_positive_candidate_loss_multiplier": loss_options[
                "hard_roi_positive_candidate_loss_multiplier"
            ],
            "hard_roi_positive_group_balance": loss_options["hard_roi_positive_group_balance"],
            "hard_roi_positive_group_weight_power": loss_options[
                "hard_roi_positive_group_weight_power"
            ],
            "max_hard_roi_positive_group_weight": loss_options[
                "max_hard_roi_positive_group_weight"
            ],
            "hard_roi_positive_group_counts": loss_options[
                "hard_roi_positive_group_counts"
            ],
            "hard_roi_positive_group_weights": loss_options[
                "hard_roi_positive_group_weights"
            ],
            "candidate_delay_loss_multiplier": loss_options[
                "candidate_delay_loss_multiplier"
            ],
            "hard_roi_negative_delay_loss_multiplier": loss_options[
                "hard_roi_negative_delay_loss_multiplier"
            ],
            "hard_roi_safe_delay_loss_multiplier": loss_options[
                "hard_roi_safe_delay_loss_multiplier"
            ],
            "candidate_admission_score_mode": loss_options["candidate_admission_score_mode"],
            "candidate_delay_score_penalty": loss_options["candidate_delay_score_penalty"],
            "candidate_delay_gate_enabled": bool(
                getattr(args, "candidate_delay_gate_enabled", False)
            ),
            "candidate_delay_risk_threshold": float(
                getattr(args, "candidate_delay_risk_threshold", 0.5)
            ),
            "candidate_rescue_raw_score_threshold": loss_options[
                "candidate_rescue_raw_score_threshold"
            ],
            "candidate_rescue_delay_risk_threshold": loss_options[
                "candidate_rescue_delay_risk_threshold"
            ],
            "candidate_rescue_delay_score_penalty": loss_options[
                "candidate_rescue_delay_score_penalty"
            ],
            "pairwise_ranking_loss_active": pairwise_ranking_loss_active,
            "pairwise_candidate_ranking_loss_multiplier": loss_options[
                "pairwise_candidate_ranking_loss_multiplier"
            ],
            "pairwise_false_delay_contrast_loss_multiplier": loss_options[
                "pairwise_false_delay_contrast_loss_multiplier"
            ],
            "pairwise_delay_risk_contrast_loss_multiplier": loss_options[
                "pairwise_delay_risk_contrast_loss_multiplier"
            ],
            "focused_pair_loss_multiplier": loss_options["focused_pair_loss_multiplier"],
            "focused_pair_candidate_loss_multiplier": loss_options[
                "focused_pair_candidate_loss_multiplier"
            ],
            "focused_pair_admission_loss_multiplier": loss_options[
                "focused_pair_admission_loss_multiplier"
            ],
            "focused_pair_delay_risk_loss_multiplier": loss_options[
                "focused_pair_delay_risk_loss_multiplier"
            ],
            "focused_pair_batch_loss_multiplier": loss_options[
                "focused_pair_batch_loss_multiplier"
            ],
            "focused_pair_row_index_min": loss_options["focused_pair_row_index_min"],
            "focused_pair_row_indices_file": loss_options[
                "focused_pair_row_indices_file"
            ],
            "focused_pair_row_indices_count": len(
                loss_options.get("focused_pair_row_indices") or []
            ),
            "pairwise_ranking_status": pairwise_ranking_status,
            "context_pair_stats": context_pair_stats,
            "focused_pair_gate": focused_pair_gate_metrics,
            "training_run_config": training_run_config,
            "requires_knn_ood_shell_before_stage4": True,
            "requires_5_10_no_regression_before_stage4": True,
            "requires_20_wall_time_roi_before_stage4": True,
            "production_ready": False,
            "default_enabled": False,
        },
        "deployment_gate": {
            "gate_config": gate_config,
            "checkpoint_gate_pass": checkpoint_gate_pass,
            "stage4_candidate_ready": stage4_candidate_ready,
            "training_stability_reject_reasons": training_stability_reject_reasons,
            "hard_reject_reason_categories": _hard_reject_reason_categories(
                _rejected_checkpoint_reasons(
                    validation_deployment_metrics,
                    training_stability_reject_reasons=training_stability_reject_reasons,
                    focused_pair_gate_reject_reasons=focused_pair_gate_reject_reasons,
                )
            ),
            "stage4_blockers": stage4_blockers,
        },
        "training": {
            "epochs": int(args.epochs),
            "lr": float(args.lr),
            "weight_decay": float(args.weight_decay),
            "loss_options": loss_options,
            "attempted_update_count": int(attempted_update_count),
            "nonfinite_skipped_update_count": int(nonfinite_skipped_update_count),
            "nonfinite_skipped_update_rate": float(nonfinite_skipped_update_rate),
            "best_epoch": best_epoch,
            "best_validation_loss": best_validation_loss,
            "selected_validation_loss": selected_validation_loss,
            "best_loss_epoch": best_loss_epoch,
            "best_loss_epoch_gate_pass": bool(best_loss_epoch_gate_pass),
            "selected_checkpoint_reason": _selected_checkpoint_reason(
                validation_deployment_metrics,
                best_epoch=best_epoch,
                best_loss_epoch=best_loss_epoch,
            ),
            "rejected_checkpoint_reasons": _rejected_checkpoint_reasons(
                validation_deployment_metrics,
                training_stability_reject_reasons=training_stability_reject_reasons,
                focused_pair_gate_reject_reasons=focused_pair_gate_reject_reasons,
            ),
            "rejected_checkpoint_reason_categories": _hard_reject_reason_categories(
                _rejected_checkpoint_reasons(
                    validation_deployment_metrics,
                    training_stability_reject_reasons=training_stability_reject_reasons,
                    focused_pair_gate_reject_reasons=focused_pair_gate_reject_reasons,
                )
            ),
            "history": history,
            "train_deployment_metrics": train_deployment_metrics,
            "validation_deployment_metrics": validation_deployment_metrics,
            "family_holdout_metrics": family_holdout_metrics,
            "focused_pair_gate": focused_pair_gate_metrics,
            "training_run_config": training_run_config,
        },
    }
    Path(args.checkpoint_out).parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, args.checkpoint_out)

    summary = {
        "schema_version": "gat_batch_impact_training_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "gat_batch_impact_trained",
        "dataset_dir": str(dataset_dir),
        "checkpoint_out": str(args.checkpoint_out),
        "training_objective": "precision_constrained_roi_maximization",
        "loss_options": loss_options,
        "hard_roi_threshold": loss_options["hard_roi_threshold"],
        "pairwise_ranking_loss_active": pairwise_ranking_loss_active,
        "pairwise_ranking_status": pairwise_ranking_status,
        "context_pair_stats": context_pair_stats,
        "sample_count": len(samples),
        "candidate_count": int(manifest.get("candidate_count") or 0),
        "train_count": len(split.train),
        "validation_count": len(split.validation),
        "split": split.info,
        "candidate_label_counts": dict(manifest.get("candidate_label_counts") or {}),
        "batch_label_counts": dict(manifest.get("batch_label_counts") or {}),
        "family_counts": dict(manifest.get("family_counts") or {}),
        "task_count_counts": dict(manifest.get("task_count_counts") or {}),
        "best_epoch": best_epoch,
        "best_validation_loss": best_validation_loss,
        "selected_validation_loss": selected_validation_loss,
        "best_loss_epoch": best_loss_epoch,
        "best_loss_epoch_gate_pass": bool(best_loss_epoch_gate_pass),
        "selected_checkpoint_reason": _selected_checkpoint_reason(
            validation_deployment_metrics,
            best_epoch=best_epoch,
            best_loss_epoch=best_loss_epoch,
        ),
        "rejected_checkpoint_reasons": _rejected_checkpoint_reasons(
            validation_deployment_metrics,
            training_stability_reject_reasons=training_stability_reject_reasons,
            focused_pair_gate_reject_reasons=focused_pair_gate_reject_reasons,
        ),
        "rejected_checkpoint_reason_categories": _hard_reject_reason_categories(
            _rejected_checkpoint_reasons(
                validation_deployment_metrics,
                training_stability_reject_reasons=training_stability_reject_reasons,
                focused_pair_gate_reject_reasons=focused_pair_gate_reject_reasons,
            )
        ),
        "attempted_update_count": int(attempted_update_count),
        "nonfinite_skipped_update_count": int(nonfinite_skipped_update_count),
        "nonfinite_skipped_update_rate": float(nonfinite_skipped_update_rate),
        "training_stability_reject_reasons": training_stability_reject_reasons,
        "checkpoint_selection": CHECKPOINT_SELECTION_POLICY,
        "history": history,
        "train_deployment_metrics": train_deployment_metrics,
        "validation_deployment_metrics": validation_deployment_metrics,
        "threshold_search": validation_threshold_search,
        "family_holdout_metrics": family_holdout_metrics,
        "focused_pair_gate": focused_pair_gate_metrics,
        "focused_pair_gate_reject_reasons": focused_pair_gate_reject_reasons,
        "training_run_config": training_run_config,
        "checkpoint_gate_pass": checkpoint_gate_pass,
        "stage4_candidate_ready": stage4_candidate_ready,
        "stage4_blockers": stage4_blockers,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "gate_can_permanently_discard_negative_columns": False,
        "requires_knn_ood_shell": True,
        "requires_5_10_no_regression": True,
        "requires_20_roi_ab": True,
        "production_ready": False,
        "default_enabled": False,
        "all_checks_pass": bool(
            train_deployment_metrics.get("total_batches", 0) > 0
            and validation_deployment_metrics.get("total_batches", 0) > 0
            and checkpoint["target_label"] == "same_context_batch_trajectory_roi"
            and checkpoint["exactness_contract"] == BATCH_IMPACT_EXACTNESS_CONTRACT
            and not checkpoint["training_contract"]["uses_random_row_split"]
            and not checkpoint["training_contract"]["production_ready"]
        ),
    }
    Path(args.metrics_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.metrics_out).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(args.report), summary)
    return summary


def _assert_batch_impact_manifest(
    manifest: dict[str, Any],
    args: argparse.Namespace | TrainBatchImpactArgs,
) -> None:
    if manifest.get("schema_version") != "gat_batch_impact_dataset_manifest_v1":
        raise ValueError("batch-impact dataset must use gat_batch_impact_dataset_manifest_v1")
    if not bool(manifest.get("diagnostic_only")):
        raise ValueError("batch-impact dataset must be diagnostic_only")
    if bool(manifest.get("runs_bpc_or_pricing")):
        raise ValueError("batch-impact training cannot use a dataset that runs BPC or pricing")
    contract = dict(manifest.get("exactness_contract") or {})
    for key, expected in BATCH_IMPACT_EXACTNESS_CONTRACT.items():
        if bool(contract.get(key)) != bool(expected):
            raise ValueError(f"batch-impact exactness contract mismatch for {key}")
    sample_count = int(manifest.get("sample_count") or 0)
    if sample_count < int(args.min_samples):
        raise ValueError(f"batch-impact dataset has {sample_count} samples; requires {int(args.min_samples)}")
    batch_counts = dict(manifest.get("batch_label_counts") or {})
    candidate_counts = dict(manifest.get("candidate_label_counts") or {})
    if int(batch_counts.get("roi_positive") or 0) < int(args.min_roi_positive_batches):
        raise ValueError("batch-impact dataset does not have enough ROI-positive batches")
    if int(candidate_counts.get("delay_queue") or 0) < int(args.min_delay_candidates):
        raise ValueError("batch-impact dataset does not have enough delay-queue negative candidates")


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
    graph.batch_features = _normalize_tensor(
        graph.batch_features,
        manifest["batch_feature_mean"],
        manifest["batch_feature_std"],
    )
    return graph


def _path_token_model_config(
    manifest: dict[str, Any],
    args: argparse.Namespace | TrainBatchImpactArgs,
) -> dict[str, Any]:
    schema = dict(manifest.get("candidate_path_token_schema") or {})
    token_bucket_count = int(schema.get("token_hash_bucket_count") or 0)
    pair_bucket_count = int(schema.get("pair_hash_bucket_count") or 0)
    if token_bucket_count <= 0 or pair_bucket_count <= 0:
        return {
            "path_token_vocab_size": 0,
            "path_pair_vocab_size": 0,
            "path_type_vocab_size": 3,
            "path_token_dim": int(getattr(args, "path_token_dim", 16)),
            "path_hidden_dim": int(getattr(args, "path_hidden_dim", 32)),
        }
    type_ids = dict(schema.get("type_ids") or {})
    type_vocab_size = max([int(value) for value in type_ids.values()] + [3])
    return {
        "path_token_vocab_size": token_bucket_count,
        "path_pair_vocab_size": pair_bucket_count,
        "path_type_vocab_size": int(type_vocab_size),
        "path_token_dim": int(getattr(args, "path_token_dim", 16)),
        "path_hidden_dim": int(getattr(args, "path_hidden_dim", 32)),
    }


def _normalize_tensor(tensor: torch.Tensor, mean: list[float], std: list[float]) -> torch.Tensor:
    mean_tensor = torch.tensor(mean, dtype=torch.float32)
    std_tensor = torch.tensor(std, dtype=torch.float32)
    return (tensor.to(dtype=torch.float32) - mean_tensor) / std_tensor


def _split_samples_by_instance_path(samples: list[Any], *, validation_fraction: float, seed: int) -> _Split:
    by_instance: dict[str, list[Any]] = {}
    for sample in samples:
        instance = _sample_instance_path(sample)
        by_instance.setdefault(instance, []).append(sample)
    instances = sorted(by_instance)
    rng = random.Random(int(seed))
    rng.shuffle(instances)
    validation_count = max(1 if len(instances) > 1 else 0, int(round(len(instances) * float(validation_fraction))))
    validation_count = min(validation_count, max(0, len(instances) - 1))
    validation_instances = set(instances[:validation_count])
    pairwise_adjustment = _preserve_train_pairwise_context(
        by_instance,
        validation_instances=validation_instances,
    )
    validation_instances = pairwise_adjustment["validation_instances"]
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
            "train_family_counts": _sample_family_counts(train),
            "validation_family_counts": _sample_family_counts(validation),
            "train_context_count": len({str(getattr(sample, "batch_impact_context_hash", "")) for sample in train}),
            "validation_context_count": len({str(getattr(sample, "batch_impact_context_hash", "")) for sample in validation}),
            "pairwise_train_preserved": bool(pairwise_adjustment["pairwise_train_preserved"]),
            "pairwise_split_adjustment": pairwise_adjustment["pairwise_split_adjustment"],
        },
    )


def _sample_family_counts(samples: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for sample in samples:
        family = str(getattr(sample, "batch_impact_instance_family", "") or "unknown")
        counts[family] = counts.get(family, 0) + 1
    return dict(sorted(counts.items()))


def _sample_instance_path(sample: Any) -> str:
    return str(
        getattr(sample, "batch_impact_instance_path", "")
        or getattr(sample, "batch_impact_instance", "")
    )


def _sample_context_hash(sample: Any) -> str:
    return str(getattr(sample, "batch_impact_context_hash", "") or "unknown")


def _sample_float_attr(sample: Any, name: str) -> float | None:
    value = getattr(sample, name, None)
    if value is None:
        return None
    if torch.is_tensor(value):
        if int(value.numel()) <= 0:
            return None
        return float(value.detach().cpu().reshape(-1)[0].item())
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sample_int_attr(sample: Any, name: str) -> int | None:
    value = getattr(sample, name, None)
    if value is None:
        return None
    if torch.is_tensor(value):
        if int(value.numel()) <= 0:
            return None
        return int(value.detach().cpu().reshape(-1)[0].item())
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _same_context_roi_pairs(
    samples: list[Any],
    *,
    min_roi_delta: float = 1.0e-6,
) -> list[tuple[Any, Any, float]]:
    by_context: dict[str, list[Any]] = {}
    for sample in samples:
        by_context.setdefault(_sample_context_hash(sample), []).append(sample)
    pairs: list[tuple[Any, Any, float]] = []
    for group in by_context.values():
        if len(group) < 2:
            continue
        for left_idx, left in enumerate(group):
            left_roi = _sample_float_attr(left, "y_accepted_batch_roi")
            if left_roi is None:
                continue
            for right in group[left_idx + 1 :]:
                right_roi = _sample_float_attr(right, "y_accepted_batch_roi")
                if right_roi is None:
                    continue
                delta = float(left_roi) - float(right_roi)
                if abs(delta) <= float(min_roi_delta):
                    continue
                if delta > 0.0:
                    pairs.append((left, right, float(delta)))
                else:
                    pairs.append((right, left, float(-delta)))
    return pairs


def _focused_training_pairs(
    samples: list[Any],
    *,
    focus_row_index_min: int | None,
    focus_row_indices: list[int] | None = None,
) -> list[tuple[Any, Any, float]]:
    focused_index_set = {int(value) for value in (focus_row_indices or [])}
    if focus_row_index_min is None and not focused_index_set:
        return []
    rows: list[Any] = []
    for sample in samples:
        row_index = _sample_int_attr(sample, "batch_impact_source_row_index")
        if row_index is None:
            continue
        if focused_index_set:
            if int(row_index) in focused_index_set:
                rows.append(sample)
        elif row_index >= int(focus_row_index_min):
            rows.append(sample)
    by_context: dict[str, list[Any]] = {}
    for sample in rows:
        by_context.setdefault(_sample_context_hash(sample), []).append(sample)
    pairs: list[tuple[Any, Any, float]] = []
    for group in by_context.values():
        positives = [
            sample
            for sample in group
            if _sample_focused_label_class(sample) == "positive_high_priority"
        ]
        negatives = [
            sample
            for sample in group
            if _sample_focused_label_class(sample) == "delay_or_hard_negative"
        ]
        for positive in positives:
            positive_roi = _sample_float_attr(positive, "y_accepted_batch_roi")
            for negative in negatives:
                negative_roi = _sample_float_attr(negative, "y_accepted_batch_roi")
                if positive_roi is None or negative_roi is None:
                    roi_delta = 1.0
                else:
                    roi_delta = max(
                        float(abs(float(positive_roi) - float(negative_roi))),
                        1.0e-6,
                    )
                pairs.append((positive, negative, roi_delta))
    return pairs


def _sample_focused_label_class(sample: Any) -> str:
    high_priority = _sample_tensor_any(sample, "y_candidate_high_priority")
    delay = _sample_tensor_any(sample, "y_candidate_delay_risk")
    roi_positive = (_sample_float_attr(sample, "y_batch_roi_positive") or 0.0) > 0.5
    bad_mode = (_sample_float_attr(sample, "y_bad_mode_switch") or 0.0) > 0.5
    if high_priority and roi_positive and not bad_mode:
        return "positive_high_priority"
    if delay or bad_mode or not roi_positive:
        return "delay_or_hard_negative"
    return "ambiguous"


def _sample_tensor_any(sample: Any, name: str) -> bool:
    value = getattr(sample, name, None)
    if value is None:
        return False
    if torch.is_tensor(value):
        return bool(torch.any(value.detach().cpu().reshape(-1) > 0.5))
    try:
        return bool(value)
    except (TypeError, ValueError):
        return False


def _preserve_train_pairwise_context(
    by_instance: dict[str, list[Any]],
    *,
    validation_instances: set[str],
) -> dict[str, Any]:
    all_samples = [sample for samples in by_instance.values() for sample in samples]
    if not _same_context_roi_pairs(all_samples):
        return {
            "validation_instances": validation_instances,
            "pairwise_train_preserved": False,
            "pairwise_split_adjustment": "not_needed_no_comparable_pairs",
        }
    train_samples = [
        sample
        for instance, samples in by_instance.items()
        if instance not in validation_instances
        for sample in samples
    ]
    if _same_context_roi_pairs(train_samples):
        return {
            "validation_instances": validation_instances,
            "pairwise_train_preserved": True,
            "pairwise_split_adjustment": "not_needed_train_has_comparable_pairs",
        }
    validation_samples = [
        sample
        for instance, samples in by_instance.items()
        if instance in validation_instances
        for sample in samples
    ]
    if not _same_context_roi_pairs(validation_samples) or len(validation_instances) <= 1:
        return {
            "validation_instances": validation_instances,
            "pairwise_train_preserved": False,
            "pairwise_split_adjustment": "unable_to_preserve_train_pairs",
        }

    paired_validation_instances = sorted(
        instance
        for instance in validation_instances
        if _same_context_roi_pairs(by_instance.get(instance, []))
    )
    train_instances = sorted(instance for instance in by_instance if instance not in validation_instances)
    for paired_instance in paired_validation_instances:
        adjusted_validation = set(validation_instances)
        adjusted_validation.remove(paired_instance)
        if train_instances:
            adjusted_validation.add(train_instances[0])
        adjusted_train_samples = [
            sample
            for instance, samples in by_instance.items()
            if instance not in adjusted_validation
            for sample in samples
        ]
        if _same_context_roi_pairs(adjusted_train_samples):
            return {
                "validation_instances": adjusted_validation,
                "pairwise_train_preserved": True,
                "pairwise_split_adjustment": (
                    "moved_validation_pair_instance_to_train:"
                    f"{paired_instance}"
                ),
            }
    return {
        "validation_instances": validation_instances,
        "pairwise_train_preserved": False,
        "pairwise_split_adjustment": "unable_to_preserve_train_pairs",
    }


def _context_pair_stats(samples: list[Any]) -> dict[str, int]:
    groups: dict[str, list[Any]] = {}
    for sample in samples:
        groups.setdefault(_sample_context_hash(sample), []).append(sample)
    same_context_pair_count = 0
    same_context_comparable_pair_count = 0
    positive_negative_label_pair_count = 0
    roi_diverse_context_count = 0
    multi_context_count = 0
    largest_context_size = 0
    for group in groups.values():
        count = len(group)
        largest_context_size = max(largest_context_size, count)
        if count >= 2:
            multi_context_count += 1
            same_context_pair_count += count * (count - 1) // 2
        comparable_before = same_context_comparable_pair_count
        for left_idx, left in enumerate(group):
            left_roi = _sample_float_attr(left, "y_accepted_batch_roi")
            left_positive = _sample_float_attr(left, "y_batch_roi_positive")
            for right in group[left_idx + 1 :]:
                right_roi = _sample_float_attr(right, "y_accepted_batch_roi")
                right_positive = _sample_float_attr(right, "y_batch_roi_positive")
                if left_roi is not None and right_roi is not None and abs(left_roi - right_roi) > 1.0e-12:
                    same_context_comparable_pair_count += 1
                if (
                    left_positive is not None
                    and right_positive is not None
                    and int(left_positive > 0.5) != int(right_positive > 0.5)
                ):
                    positive_negative_label_pair_count += 1
        if same_context_comparable_pair_count > comparable_before:
            roi_diverse_context_count += 1
    return {
        "sample_count": len(samples),
        "context_count": len(groups),
        "multi_context_count": multi_context_count,
        "same_context_pair_count": same_context_pair_count,
        "same_context_comparable_pair_count": same_context_comparable_pair_count,
        "positive_negative_label_pair_count": positive_negative_label_pair_count,
        "roi_diverse_context_count": roi_diverse_context_count,
        "largest_context_size": largest_context_size,
    }


def _pairwise_ranking_status(
    context_pair_stats: dict[str, dict[str, int]],
    *,
    loss_options: dict[str, Any],
) -> str:
    if int(context_pair_stats["all"]["same_context_pair_count"]) <= 0:
        return "inactive_no_same_context_pairs"
    if int(context_pair_stats["all"]["same_context_comparable_pair_count"]) <= 0:
        return "inactive_no_roi_diverse_same_context_pairs"
    if not _pairwise_loss_enabled(loss_options):
        return "inactive_disabled_by_zero_multiplier"
    if int(context_pair_stats["train"]["same_context_comparable_pair_count"]) <= 0:
        return "inactive_no_train_same_context_roi_pairs"
    return "active_same_context_roi_margin_ranking"


def _pairwise_loss_enabled(loss_options: dict[str, Any]) -> bool:
    return (
        float(loss_options.get("pairwise_ranking_loss_multiplier", 0.0)) > 0.0
        or float(loss_options.get("pairwise_candidate_ranking_loss_multiplier", 0.0)) > 0.0
        or float(loss_options.get("pairwise_false_delay_contrast_loss_multiplier", 0.0)) > 0.0
        or float(loss_options.get("pairwise_delay_risk_contrast_loss_multiplier", 0.0)) > 0.0
    )


def _focused_pair_loss_enabled(loss_options: dict[str, Any]) -> bool:
    return (
        float(loss_options.get("focused_pair_loss_multiplier", 0.0)) > 0.0
        and (
            loss_options.get("focused_pair_row_index_min") is not None
            or bool(loss_options.get("focused_pair_row_indices") or [])
        )
    )


def _focused_pair_head_loss_enabled(loss_options: dict[str, Any]) -> bool:
    return (
        (
            loss_options.get("focused_pair_row_index_min") is not None
            or bool(loss_options.get("focused_pair_row_indices") or [])
        )
        and (
            float(loss_options.get("focused_pair_candidate_loss_multiplier", 0.0)) > 0.0
            or (
                float(loss_options.get("focused_pair_admission_loss_multiplier", 0.0))
                > 0.0
            )
            or (
                float(loss_options.get("focused_pair_delay_risk_loss_multiplier", 0.0))
                > 0.0
            )
            or float(loss_options.get("focused_pair_batch_loss_multiplier", 0.0)) > 0.0
        )
    )


def _focused_pair_row_indices(args: argparse.Namespace | TrainBatchImpactArgs) -> list[int]:
    path = getattr(args, "focused_pair_row_indices_file", None)
    if path is None:
        return []
    return _read_focused_pair_row_indices_file(Path(path))


def _read_focused_pair_row_indices_file(path: Path) -> list[int]:
    def append_index(value: Any, indices: list[int]) -> None:
        if value is None:
            return
        indices.append(int(value))

    indices: list[int] = []
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                payload = json.loads(stripped)
                if isinstance(payload, dict):
                    append_index(payload.get("row_index"), indices)
                else:
                    append_index(payload, indices)
    else:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            for key in ("focused_row_indices", "row_indices", "indices"):
                if key in payload:
                    payload = payload[key]
                    break
            else:
                append_index(payload.get("row_index"), indices)
                payload = []
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    append_index(item.get("row_index"), indices)
                else:
                    append_index(item, indices)
        elif payload:
            append_index(payload, indices)
    return sorted(set(indices))


def _loss_options(args: argparse.Namespace | TrainBatchImpactArgs) -> dict[str, Any]:
    explicit_hard_roi = getattr(args, "hard_roi_threshold", None)
    baseline_selection_roi = _baseline_selection_roi(args)
    default_hard_roi = max(
        float(getattr(args, "min_accepted_batch_roi", 0.65)),
        baseline_selection_roi + float(getattr(args, "min_roi_margin_over_baseline", 0.20)),
    )
    return {
        "false_high_priority_loss_multiplier": max(
            1.0,
            float(getattr(args, "false_high_priority_loss_multiplier", 4.0)),
        ),
        "bad_mode_loss_multiplier": max(1.0, float(getattr(args, "bad_mode_loss_multiplier", 2.0))),
        "regression_loss_multiplier": max(0.0, float(getattr(args, "regression_loss_multiplier", 0.15))),
        "hard_roi_loss_multiplier": max(0.0, float(getattr(args, "hard_roi_loss_multiplier", 1.0))),
        "hard_roi_candidate_loss_multiplier": max(
            0.0,
            float(getattr(args, "hard_roi_candidate_loss_multiplier", 0.5)),
        ),
        "hard_roi_positive_candidate_loss_multiplier": max(
            0.0,
            float(getattr(args, "hard_roi_positive_candidate_loss_multiplier", 0.0)),
        ),
        "hard_roi_positive_group_balance": str(
            getattr(args, "hard_roi_positive_group_balance", "none") or "none"
        ),
        "hard_roi_positive_group_weight_power": max(
            0.0,
            float(getattr(args, "hard_roi_positive_group_weight_power", 0.5)),
        ),
        "max_hard_roi_positive_group_weight": max(
            1.0,
            float(getattr(args, "max_hard_roi_positive_group_weight", 4.0)),
        ),
        "hard_roi_positive_group_counts": {},
        "hard_roi_positive_group_weights": {},
        "candidate_delay_loss_multiplier": max(
            0.0,
            float(getattr(args, "candidate_delay_loss_multiplier", 0.5)),
        ),
        "hard_roi_negative_delay_loss_multiplier": max(
            0.0,
            float(getattr(args, "hard_roi_negative_delay_loss_multiplier", 0.0)),
        ),
        "hard_roi_safe_delay_loss_multiplier": max(
            0.0,
            float(getattr(args, "hard_roi_safe_delay_loss_multiplier", 0.0)),
        ),
        "candidate_admission_score_mode": str(
            getattr(args, "candidate_admission_score_mode", "high_priority")
            or "high_priority"
        ),
        "candidate_delay_score_penalty": max(
            0.0,
            float(getattr(args, "candidate_delay_score_penalty", 0.0)),
        ),
        "candidate_rescue_raw_score_threshold": min(
            1.0,
            max(
                0.0,
                float(getattr(args, "candidate_rescue_raw_score_threshold", 1.0)),
            ),
        ),
        "candidate_rescue_delay_risk_threshold": min(
            1.0,
            max(
                0.0,
                float(getattr(args, "candidate_rescue_delay_risk_threshold", 1.0)),
            ),
        ),
        "candidate_rescue_delay_score_penalty": max(
            0.0,
            float(getattr(args, "candidate_rescue_delay_score_penalty", 0.0)),
        ),
        "hard_roi_threshold": float(default_hard_roi if explicit_hard_roi is None else explicit_hard_roi),
        "pairwise_ranking_loss_multiplier": max(
            0.0,
            float(getattr(args, "pairwise_ranking_loss_multiplier", 1.0)),
        ),
        "pairwise_candidate_ranking_loss_multiplier": max(
            0.0,
            float(getattr(args, "pairwise_candidate_ranking_loss_multiplier", 0.75)),
        ),
        "pairwise_false_delay_contrast_loss_multiplier": max(
            0.0,
            float(getattr(args, "pairwise_false_delay_contrast_loss_multiplier", 0.5)),
        ),
        "pairwise_delay_risk_contrast_loss_multiplier": max(
            0.0,
            float(getattr(args, "pairwise_delay_risk_contrast_loss_multiplier", 0.0)),
        ),
        "focused_pair_loss_multiplier": max(
            0.0,
            float(getattr(args, "focused_pair_loss_multiplier", 0.0)),
        ),
        "focused_pair_candidate_loss_multiplier": max(
            0.0,
            float(getattr(args, "focused_pair_candidate_loss_multiplier", 0.0)),
        ),
        "focused_pair_admission_loss_multiplier": max(
            0.0,
            float(getattr(args, "focused_pair_admission_loss_multiplier", 0.0)),
        ),
        "focused_pair_delay_risk_loss_multiplier": max(
            0.0,
            float(getattr(args, "focused_pair_delay_risk_loss_multiplier", 0.0)),
        ),
        "focused_pair_batch_loss_multiplier": max(
            0.0,
            float(getattr(args, "focused_pair_batch_loss_multiplier", 0.0)),
        ),
        "focused_pair_row_index_min": getattr(args, "focused_pair_gate_row_index_min", None),
        "focused_pair_row_indices_file": (
            None
            if getattr(args, "focused_pair_row_indices_file", None) is None
            else str(getattr(args, "focused_pair_row_indices_file"))
        ),
        "focused_pair_row_indices": _focused_pair_row_indices(args),
        "pairwise_roi_margin": max(0.0, float(getattr(args, "pairwise_roi_margin", 0.05))),
        "min_pairwise_roi_delta": max(
            0.0,
            float(getattr(args, "min_pairwise_roi_delta", 1.0e-6)),
        ),
        "max_grad_norm": max(0.0, float(getattr(args, "max_grad_norm", 5.0))),
    }


def _training_run_config(
    args: argparse.Namespace | TrainBatchImpactArgs,
    *,
    model_config: dict[str, Any],
    gate_config: dict[str, Any],
    loss_options: dict[str, Any],
) -> dict[str, Any]:
    return {
        "seed": int(getattr(args, "seed", 41)),
        "validation_fraction": float(getattr(args, "validation_fraction", 0.25)),
        "epochs": int(getattr(args, "epochs", 8)),
        "device": str(getattr(args, "device", "cpu")),
        "lr": float(getattr(args, "lr", 1.0e-3)),
        "weight_decay": float(getattr(args, "weight_decay", 1.0e-5)),
        "max_grad_norm": float(loss_options.get("max_grad_norm", 5.0)),
        "model_config": dict(model_config),
        "loss_options": dict(loss_options),
        "gate_config": dict(gate_config),
        "focused_pair_gate_config": {
            "focused_pair_gate_row_index_min": getattr(
                args,
                "focused_pair_gate_row_index_min",
                None,
            ),
            "focused_pair_row_indices_file": (
                None
                if getattr(args, "focused_pair_row_indices_file", None) is None
                else str(getattr(args, "focused_pair_row_indices_file"))
            ),
            "focused_pair_row_indices_count": len(
                loss_options.get("focused_pair_row_indices") or []
            ),
            "focused_pair_selector": (
                "explicit_row_indices"
                if loss_options.get("focused_pair_row_indices")
                else (
                    "row_index_min"
                    if getattr(args, "focused_pair_gate_row_index_min", None) is not None
                    else None
                )
            ),
            "min_focused_pair_count": int(getattr(args, "min_focused_pair_count", 1)),
            "min_focused_raw_pair_pass_rate": _clamped_rate(
                getattr(args, "min_focused_raw_pair_pass_rate", 1.0)
            ),
            "min_focused_admission_pair_pass_rate": _clamped_rate(
                getattr(args, "min_focused_admission_pair_pass_rate", 1.0)
            ),
            "min_focused_delay_risk_pair_pass_rate": _clamped_rate(
                getattr(args, "min_focused_delay_risk_pair_pass_rate", 1.0)
            ),
            "min_focused_strict_pair_pass_rate": _clamped_rate(
                getattr(args, "min_focused_strict_pair_pass_rate", 1.0)
            ),
        },
        "checkpoint_selection": CHECKPOINT_SELECTION_POLICY,
    }


def _with_hard_roi_positive_group_balance(
    loss_options: dict[str, Any],
    samples: list[Any],
) -> dict[str, Any]:
    mode = str(loss_options.get("hard_roi_positive_group_balance", "none") or "none")
    if mode == "none":
        return dict(loss_options)
    hard_roi_threshold = float(loss_options["hard_roi_threshold"])
    counts: dict[str, int] = {}
    for sample in samples:
        if not _sample_is_hard_roi_positive(sample, hard_roi_threshold=hard_roi_threshold):
            continue
        key = _sample_group_key(sample, mode=mode)
        counts[key] = counts.get(key, 0) + 1
    updated = dict(loss_options)
    updated["hard_roi_positive_group_counts"] = dict(sorted(counts.items()))
    if not counts:
        updated["hard_roi_positive_group_weights"] = {}
        return updated
    mean_count = sum(counts.values()) / float(len(counts))
    power = float(loss_options.get("hard_roi_positive_group_weight_power", 0.5))
    max_weight = float(loss_options.get("max_hard_roi_positive_group_weight", 4.0))
    weights: dict[str, float] = {}
    for key, count in sorted(counts.items()):
        if count <= 0:
            continue
        raw_weight = (mean_count / float(count)) ** power if power > 0.0 else 1.0
        weights[key] = max(1.0, min(max_weight, float(raw_weight)))
    updated["hard_roi_positive_group_weights"] = weights
    return updated


def _sample_is_hard_roi_positive(sample: Any, *, hard_roi_threshold: float) -> bool:
    roi = _sample_float_attr(sample, "y_accepted_batch_roi")
    bad_mode = _sample_float_attr(sample, "y_bad_mode_switch")
    return bool(
        roi is not None
        and float(roi) >= float(hard_roi_threshold)
        and (bad_mode is None or float(bad_mode) <= 0.5)
    )


def _sample_group_key(sample: Any, *, mode: str) -> str:
    family = str(getattr(sample, "batch_impact_instance_family", "") or "unknown")
    task_count = str(getattr(sample, "batch_impact_task_count", "") or "unknown")
    if mode == "family":
        return family
    if mode == "task_count":
        return task_count
    if mode == "family_task":
        return f"{family}|{task_count}"
    return "all"


def _hard_roi_positive_group_weight(sample: Any, *, loss_options: dict[str, Any]) -> float:
    mode = str(loss_options.get("hard_roi_positive_group_balance", "none") or "none")
    if mode == "none":
        return 1.0
    weights = dict(loss_options.get("hard_roi_positive_group_weights") or {})
    if not weights:
        return 1.0
    return float(weights.get(_sample_group_key(sample, mode=mode), 1.0))


def _run_epoch(
    model: GATBatchImpactModel,
    samples: list[Any],
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    *,
    loss_options: dict[str, Any],
) -> dict[str, float | int]:
    model.train()
    shuffled = list(samples)
    random.shuffle(shuffled)
    total = 0.0
    count = 0
    skipped = 0
    for sample in shuffled:
        optimizer.zero_grad(set_to_none=True)
        loss = _sample_loss(model, sample, device, loss_options=loss_options)
        if not bool(torch.isfinite(loss)):
            skipped += 1
            optimizer.zero_grad(set_to_none=True)
            continue
        loss.backward()
        if not _gradients_are_finite(model):
            skipped += 1
            optimizer.zero_grad(set_to_none=True)
            continue
        if float(loss_options["max_grad_norm"]) > 0.0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), float(loss_options["max_grad_norm"]))
        if not _gradients_are_finite(model):
            skipped += 1
            optimizer.zero_grad(set_to_none=True)
            continue
        optimizer.step()
        for param in model.parameters():
            if param.grad is not None and not bool(torch.isfinite(param).all()):
                raise ValueError("batch-impact model parameter became NaN or Inf after optimizer step")
        total += float(loss.detach().cpu())
        count += 1
    pairwise_pairs = _same_context_roi_pairs(
        shuffled,
        min_roi_delta=float(loss_options["min_pairwise_roi_delta"]),
    )
    if not _pairwise_loss_enabled(loss_options):
        pairwise_pairs = []
    for better, worse, roi_delta in pairwise_pairs:
        optimizer.zero_grad(set_to_none=True)
        loss = _pairwise_ranking_loss(
            model,
            better,
            worse,
            device,
            roi_delta=roi_delta,
            loss_options=loss_options,
        )
        if not bool(torch.isfinite(loss)):
            skipped += 1
            optimizer.zero_grad(set_to_none=True)
            continue
        loss.backward()
        if not _gradients_are_finite(model):
            skipped += 1
            optimizer.zero_grad(set_to_none=True)
            continue
        if float(loss_options["max_grad_norm"]) > 0.0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), float(loss_options["max_grad_norm"]))
        if not _gradients_are_finite(model):
            skipped += 1
            optimizer.zero_grad(set_to_none=True)
            continue
        optimizer.step()
        for param in model.parameters():
            if param.grad is not None and not bool(torch.isfinite(param).all()):
                raise ValueError("batch-impact model parameter became NaN or Inf after optimizer step")
        total += float(loss.detach().cpu())
        count += 1
    focused_pairs = _focused_training_pairs(
        shuffled,
        focus_row_index_min=loss_options.get("focused_pair_row_index_min"),
        focus_row_indices=loss_options.get("focused_pair_row_indices"),
    )
    if not _focused_pair_loss_enabled(loss_options):
        focused_pairs = []
    focused_multiplier = float(loss_options.get("focused_pair_loss_multiplier", 0.0))
    for better, worse, roi_delta in focused_pairs:
        optimizer.zero_grad(set_to_none=True)
        loss = focused_multiplier * _pairwise_ranking_loss(
            model,
            better,
            worse,
            device,
            roi_delta=roi_delta,
            loss_options=loss_options,
        )
        if not bool(torch.isfinite(loss)):
            skipped += 1
            optimizer.zero_grad(set_to_none=True)
            continue
        loss.backward()
        if not _gradients_are_finite(model):
            skipped += 1
            optimizer.zero_grad(set_to_none=True)
            continue
        if float(loss_options["max_grad_norm"]) > 0.0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), float(loss_options["max_grad_norm"]))
        if not _gradients_are_finite(model):
            skipped += 1
            optimizer.zero_grad(set_to_none=True)
            continue
        optimizer.step()
        for param in model.parameters():
            if param.grad is not None and not bool(torch.isfinite(param).all()):
                raise ValueError("batch-impact model parameter became NaN or Inf after optimizer step")
        total += float(loss.detach().cpu())
        count += 1
    focused_head_pairs = _focused_training_pairs(
        shuffled,
        focus_row_index_min=loss_options.get("focused_pair_row_index_min"),
        focus_row_indices=loss_options.get("focused_pair_row_indices"),
    )
    if not _focused_pair_head_loss_enabled(loss_options):
        focused_head_pairs = []
    for better, worse, roi_delta in focused_head_pairs:
        optimizer.zero_grad(set_to_none=True)
        loss = _focused_pair_head_loss(
            model,
            better,
            worse,
            device,
            roi_delta=roi_delta,
            loss_options=loss_options,
        )
        if not bool(torch.isfinite(loss)):
            skipped += 1
            optimizer.zero_grad(set_to_none=True)
            continue
        loss.backward()
        if not _gradients_are_finite(model):
            skipped += 1
            optimizer.zero_grad(set_to_none=True)
            continue
        if float(loss_options["max_grad_norm"]) > 0.0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), float(loss_options["max_grad_norm"]))
        if not _gradients_are_finite(model):
            skipped += 1
            optimizer.zero_grad(set_to_none=True)
            continue
        optimizer.step()
        for param in model.parameters():
            if param.grad is not None and not bool(torch.isfinite(param).all()):
                raise ValueError("batch-impact model parameter became NaN or Inf after optimizer step")
        total += float(loss.detach().cpu())
        count += 1
    return {
        "loss": total / max(1, count),
        "skipped_update_count": skipped,
        "attempted_update_count": (
            len(shuffled) + len(pairwise_pairs) + len(focused_pairs) + len(focused_head_pairs)
        ),
    }


def _gradients_are_finite(model: GATBatchImpactModel) -> bool:
    for param in model.parameters():
        if param.grad is not None and not bool(torch.isfinite(param.grad).all()):
            return False
    return True


def _evaluate_loss(
    model: GATBatchImpactModel,
    samples: list[Any],
    device: torch.device,
    *,
    loss_options: dict[str, Any],
) -> float:
    if not samples:
        return float("inf")
    model.eval()
    total = 0.0
    count = 0
    with torch.no_grad():
        for sample in samples:
            total += float(_sample_loss(model, sample, device, loss_options=loss_options).detach().cpu())
            count += 1
        pairwise_pairs = _same_context_roi_pairs(
            samples,
            min_roi_delta=float(loss_options["min_pairwise_roi_delta"]),
        )
        if not _pairwise_loss_enabled(loss_options):
            pairwise_pairs = []
        for better, worse, roi_delta in pairwise_pairs:
            total += float(
                _pairwise_ranking_loss(
                    model,
                    better,
                    worse,
                    device,
                    roi_delta=roi_delta,
                    loss_options=loss_options,
                )
                .detach()
                .cpu()
            )
            count += 1
        focused_pairs = _focused_training_pairs(
            samples,
            focus_row_index_min=loss_options.get("focused_pair_row_index_min"),
            focus_row_indices=loss_options.get("focused_pair_row_indices"),
        )
        if not _focused_pair_loss_enabled(loss_options):
            focused_pairs = []
        focused_multiplier = float(loss_options.get("focused_pair_loss_multiplier", 0.0))
        for better, worse, roi_delta in focused_pairs:
            total += float(
                (
                    focused_multiplier
                    * _pairwise_ranking_loss(
                        model,
                        better,
                        worse,
                        device,
                        roi_delta=roi_delta,
                        loss_options=loss_options,
                    )
                )
                .detach()
                .cpu()
            )
            count += 1
        focused_head_pairs = _focused_training_pairs(
            samples,
            focus_row_index_min=loss_options.get("focused_pair_row_index_min"),
            focus_row_indices=loss_options.get("focused_pair_row_indices"),
        )
        if not _focused_pair_head_loss_enabled(loss_options):
            focused_head_pairs = []
        for better, worse, roi_delta in focused_head_pairs:
            total += float(
                _focused_pair_head_loss(
                    model,
                    better,
                    worse,
                    device,
                    roi_delta=roi_delta,
                    loss_options=loss_options,
                )
                .detach()
                .cpu()
            )
            count += 1
    return total / max(1, count)


def _sample_loss(
    model: GATBatchImpactModel,
    sample: Any,
    device: torch.device,
    *,
    loss_options: dict[str, Any],
) -> torch.Tensor:
    sample, output = _sample_model_output(model, sample, device)
    hp_target = sample.y_candidate_high_priority.to(dtype=torch.float32)
    delay_target = sample.y_candidate_delay_risk.to(dtype=torch.float32)
    false_hp_weights = torch.ones_like(hp_target)
    false_hp_weights = torch.where(
        delay_target > 0.5,
        false_hp_weights * float(loss_options["false_high_priority_loss_multiplier"]),
        false_hp_weights,
    )
    high_priority_loss = F.binary_cross_entropy_with_logits(
        output["high_priority_logit"],
        hp_target,
        weight=false_hp_weights,
    )
    delay_loss = F.binary_cross_entropy_with_logits(output["delay_risk_logit"], delay_target)
    batch_roi_loss = F.binary_cross_entropy_with_logits(
        output["batch_roi_positive_logit"],
        sample.y_batch_roi_positive.to(dtype=torch.float32),
    )
    hard_roi_target = (
        (sample.y_accepted_batch_roi.to(dtype=torch.float32) >= float(loss_options["hard_roi_threshold"]))
        & (sample.y_bad_mode_switch.to(dtype=torch.float32) <= 0.5)
    ).to(dtype=torch.float32)
    hard_roi_loss = F.binary_cross_entropy_with_logits(
        output["batch_roi_positive_logit"],
        hard_roi_target,
    )
    hard_roi_candidate_target = hp_target * hard_roi_target.reshape(())
    hard_roi_candidate_loss = F.binary_cross_entropy_with_logits(
        output["high_priority_logit"],
        hard_roi_candidate_target,
        weight=false_hp_weights,
    )
    hard_roi_positive_candidate_loss = _hard_roi_positive_candidate_boost_loss(
        output["high_priority_logit"],
        hp_target,
        hard_roi_target,
        positive_weight=_hard_roi_positive_group_weight(sample, loss_options=loss_options),
    )
    hard_roi_negative_delay_loss = _hard_roi_negative_delay_risk_loss(
        output["delay_risk_logit"],
        hard_roi_target,
    )
    hard_roi_safe_delay_loss = _hard_roi_safe_delay_risk_loss(
        output["delay_risk_logit"],
        hp_target,
        hard_roi_target,
    )
    objective_loss = F.binary_cross_entropy_with_logits(
        output["objective_progress_logit"],
        sample.y_objective_progress.to(dtype=torch.float32),
    )
    tail_loss = F.binary_cross_entropy_with_logits(
        output["tail_improved_logit"],
        sample.y_tail_improved.to(dtype=torch.float32),
    )
    bad_loss = F.binary_cross_entropy_with_logits(
        output["bad_mode_switch_logit"],
        sample.y_bad_mode_switch.to(dtype=torch.float32),
    )
    support_loss = F.binary_cross_entropy_with_logits(
        output["support_changed_good_logit"],
        sample.y_support_changed_good.to(dtype=torch.float32),
    )
    regression_loss = (
        F.huber_loss(output["predicted_delta_v"], sample.y_delta_v.to(dtype=torch.float32), delta=1.0)
        + F.huber_loss(
            output["predicted_barrier_slack"],
            sample.y_barrier_slack.to(dtype=torch.float32),
            delta=1.0,
        )
        + F.huber_loss(
            output["predicted_accepted_batch_roi"],
            sample.y_accepted_batch_roi.to(dtype=torch.float32),
            delta=1.0,
        )
    )
    return (
        high_priority_loss
        + float(loss_options["candidate_delay_loss_multiplier"]) * delay_loss
        + batch_roi_loss
        + float(loss_options["hard_roi_loss_multiplier"]) * hard_roi_loss
        + float(loss_options["hard_roi_candidate_loss_multiplier"]) * hard_roi_candidate_loss
        + float(loss_options["hard_roi_positive_candidate_loss_multiplier"])
        * hard_roi_positive_candidate_loss
        + float(loss_options["hard_roi_negative_delay_loss_multiplier"])
        * hard_roi_negative_delay_loss
        + float(loss_options["hard_roi_safe_delay_loss_multiplier"])
        * hard_roi_safe_delay_loss
        + 0.5 * objective_loss
        + 0.25 * tail_loss
        + float(loss_options["bad_mode_loss_multiplier"]) * bad_loss
        + 0.25 * support_loss
        + float(loss_options["regression_loss_multiplier"]) * regression_loss
    )


def _hard_roi_positive_candidate_boost_loss(
    high_priority_logit: torch.Tensor,
    hp_target: torch.Tensor,
    hard_roi_target: torch.Tensor,
    *,
    positive_weight: float = 1.0,
) -> torch.Tensor:
    positive_mask = (hard_roi_target.reshape(()) > 0.5) & (hp_target > 0.5)
    positive_logits = high_priority_logit[positive_mask]
    if int(positive_logits.numel()) <= 0:
        return high_priority_logit.new_tensor(0.0)
    return float(positive_weight) * F.binary_cross_entropy_with_logits(
        positive_logits,
        torch.ones_like(positive_logits),
    )


def _hard_roi_negative_delay_risk_loss(
    delay_risk_logit: torch.Tensor,
    hard_roi_target: torch.Tensor,
) -> torch.Tensor:
    if bool(hard_roi_target.reshape(()) > 0.5):
        return delay_risk_logit.new_tensor(0.0)
    return F.binary_cross_entropy_with_logits(
        delay_risk_logit.reshape(-1),
        torch.ones_like(delay_risk_logit.reshape(-1)),
    )


def _hard_roi_safe_delay_risk_loss(
    delay_risk_logit: torch.Tensor,
    hp_target: torch.Tensor,
    hard_roi_target: torch.Tensor,
) -> torch.Tensor:
    safe_mask = (hard_roi_target.reshape(()) > 0.5) & (hp_target > 0.5)
    safe_logits = delay_risk_logit.reshape(-1)[safe_mask.reshape(-1)]
    if int(safe_logits.numel()) <= 0:
        return delay_risk_logit.new_tensor(0.0)
    return F.binary_cross_entropy_with_logits(
        safe_logits,
        torch.zeros_like(safe_logits),
    )


def _batch_score_logit(
    model: GATBatchImpactModel,
    sample: Any,
    device: torch.device,
) -> torch.Tensor:
    _, output = _sample_model_output(model, sample, device)
    return output["batch_roi_positive_logit"].reshape(1)


def _candidate_acceptance_logit(
    model: GATBatchImpactModel,
    sample: Any,
    device: torch.device,
    *,
    labeled_safe_only: bool,
    loss_options: dict[str, Any] | None = None,
) -> torch.Tensor:
    sample, output = _sample_model_output(model, sample, device)
    return _candidate_acceptance_logit_from_output(
        sample,
        output,
        labeled_safe_only=labeled_safe_only,
        loss_options=loss_options,
    )


def _sample_model_output(
    model: GATBatchImpactModel,
    sample: Any,
    device: torch.device,
) -> tuple[Any, dict[str, torch.Tensor]]:
    sample = sample.to(device)
    kwargs = _sample_model_kwargs(model, sample)
    output = model(
        sample,
        sample.candidate_task_membership,
        sample.candidate_sequence_positions,
        sample.candidate_features,
        sample.context_features,
        **kwargs,
    )
    return sample, output


def _sample_model_kwargs(model: GATBatchImpactModel, sample: Any) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"batch_features": sample.batch_features}
    if getattr(model, "path_token_encoder", None) is not None:
        kwargs.update(
            {
                "candidate_path_token_ids": sample.candidate_path_token_ids,
                "candidate_path_pair_ids": sample.candidate_path_pair_ids,
                "candidate_path_type_ids": sample.candidate_path_type_ids,
                "candidate_path_token_mask": sample.candidate_path_token_mask,
            }
        )
    return kwargs


def _candidate_acceptance_logit_from_output(
    sample: Any,
    output: dict[str, torch.Tensor],
    *,
    labeled_safe_only: bool,
    loss_options: dict[str, Any] | None = None,
) -> torch.Tensor:
    logits = output["high_priority_logit"].reshape(-1)
    loss_options = dict(loss_options or {})
    if str(loss_options.get("candidate_admission_score_mode", "high_priority")) in {
        "risk_adjusted_product",
        "risk_adjusted_rescue_window",
    }:
        delay_logits = output["delay_risk_logit"].reshape(-1)
        if delay_logits.numel() != logits.numel():
            raise ValueError("candidate delay-risk logits must match high-priority logits")
        logits = logits - float(loss_options.get("candidate_delay_score_penalty", 0.0)) * delay_logits
    if logits.numel() <= 0:
        raise ValueError("candidate ranking requires at least one candidate logit")
    if labeled_safe_only:
        labels = sample.y_candidate_high_priority.to(device=logits.device).reshape(-1) > 0.5
        if labels.numel() != logits.numel():
            raise ValueError("candidate high-priority labels must match candidate logits")
        if bool(torch.any(labels)):
            logits = logits[labels]
    return logits.max().reshape(1)


def _pairwise_ranking_loss(
    model: GATBatchImpactModel,
    better: Any,
    worse: Any,
    device: torch.device,
    *,
    roi_delta: float,
    loss_options: dict[str, Any],
) -> torch.Tensor:
    better, better_output = _sample_model_output(model, better, device)
    worse, worse_output = _sample_model_output(model, worse, device)
    better_score = better_output["batch_roi_positive_logit"].reshape(1)
    worse_score = worse_output["batch_roi_positive_logit"].reshape(1)
    target = torch.ones_like(better_score)
    margin = float(loss_options["pairwise_roi_margin"])
    ranking_loss = F.margin_ranking_loss(
        better_score,
        worse_score,
        target,
        margin=margin,
    )
    candidate_ranking_loss = better_score.new_tensor(0.0)
    if float(loss_options["pairwise_candidate_ranking_loss_multiplier"]) > 0.0:
        better_candidate_score = _candidate_acceptance_logit_from_output(
            better,
            better_output,
            labeled_safe_only=True,
            loss_options=loss_options,
        )
        worse_candidate_score = _candidate_acceptance_logit_from_output(
            worse,
            worse_output,
            labeled_safe_only=False,
            loss_options=loss_options,
        )
        candidate_ranking_loss = F.margin_ranking_loss(
            better_candidate_score,
            worse_candidate_score,
            torch.ones_like(better_candidate_score),
            margin=margin,
        )
    false_delay_contrast_loss = _pairwise_false_delay_contrast_loss(
        better,
        better_output,
        worse,
        worse_output,
        margin=margin,
        base_tensor=better_score,
        loss_options=loss_options,
    )
    delay_risk_contrast_loss = _pairwise_delay_risk_contrast_loss(
        better,
        better_output,
        worse,
        worse_output,
        margin=margin,
        base_tensor=better_score,
        loss_options=loss_options,
    )
    roi_weight = min(5.0, max(1.0, float(abs(roi_delta))))
    return (
        roi_weight
        * (
            float(loss_options["pairwise_ranking_loss_multiplier"]) * ranking_loss
            + float(loss_options["pairwise_candidate_ranking_loss_multiplier"])
            * candidate_ranking_loss
            + float(loss_options.get("pairwise_false_delay_contrast_loss_multiplier", 0.0))
            * false_delay_contrast_loss
            + float(loss_options.get("pairwise_delay_risk_contrast_loss_multiplier", 0.0))
            * delay_risk_contrast_loss
        )
    )


def _focused_pair_head_loss(
    model: GATBatchImpactModel,
    better: Any,
    worse: Any,
    device: torch.device,
    *,
    roi_delta: float,
    loss_options: dict[str, Any],
) -> torch.Tensor:
    better, better_output = _sample_model_output(model, better, device)
    worse, worse_output = _sample_model_output(model, worse, device)
    better_batch_score = better_output["batch_roi_positive_logit"].reshape(1)
    worse_batch_score = worse_output["batch_roi_positive_logit"].reshape(1)
    margin = float(loss_options["pairwise_roi_margin"])
    total = better_batch_score.sum() * 0.0
    better_safe = _candidate_labeled_head_and_delay_logits(
        better,
        better_output,
        label_attr="y_candidate_high_priority",
    )
    worse_delay = _candidate_labeled_head_and_delay_logits(
        worse,
        worse_output,
        label_attr="y_candidate_delay_risk",
    )
    if (
        float(loss_options.get("focused_pair_candidate_loss_multiplier", 0.0)) > 0.0
        and better_safe is not None
        and worse_delay is not None
    ):
        better_hp, _ = better_safe
        worse_hp, _ = worse_delay
        total = total + float(
            loss_options["focused_pair_candidate_loss_multiplier"]
        ) * F.margin_ranking_loss(
            better_hp,
            worse_hp,
            torch.ones_like(better_hp),
            margin=margin,
        )
    if float(loss_options.get("focused_pair_admission_loss_multiplier", 0.0)) > 0.0:
        better_admission_score = _candidate_acceptance_logit_from_output(
            better,
            better_output,
            labeled_safe_only=True,
            loss_options=loss_options,
        )
        worse_admission_score = _candidate_acceptance_logit_from_output(
            worse,
            worse_output,
            labeled_safe_only=False,
            loss_options=loss_options,
        )
        total = total + float(
            loss_options["focused_pair_admission_loss_multiplier"]
        ) * F.margin_ranking_loss(
            better_admission_score,
            worse_admission_score,
            torch.ones_like(better_admission_score),
            margin=margin,
        )
    if (
        float(loss_options.get("focused_pair_delay_risk_loss_multiplier", 0.0)) > 0.0
        and better_safe is not None
        and worse_delay is not None
    ):
        _, better_delay = better_safe
        _, worse_delay_logit = worse_delay
        total = total + float(
            loss_options["focused_pair_delay_risk_loss_multiplier"]
        ) * F.margin_ranking_loss(
            worse_delay_logit,
            better_delay,
            torch.ones_like(worse_delay_logit),
            margin=margin,
        )
    if float(loss_options.get("focused_pair_batch_loss_multiplier", 0.0)) > 0.0:
        total = total + float(
            loss_options["focused_pair_batch_loss_multiplier"]
        ) * F.margin_ranking_loss(
            better_batch_score,
            worse_batch_score,
            torch.ones_like(better_batch_score),
            margin=margin,
        )
    roi_weight = min(5.0, max(1.0, float(abs(roi_delta))))
    return roi_weight * total


def _pairwise_false_delay_contrast_loss(
    better: Any,
    better_output: dict[str, torch.Tensor],
    worse: Any,
    worse_output: dict[str, torch.Tensor],
    *,
    margin: float,
    base_tensor: torch.Tensor,
    loss_options: dict[str, Any],
) -> torch.Tensor:
    if float(loss_options.get("pairwise_false_delay_contrast_loss_multiplier", 0.0)) <= 0.0:
        return base_tensor.new_tensor(0.0)
    better_safe = _candidate_labeled_head_and_delay_logits(
        better,
        better_output,
        label_attr="y_candidate_high_priority",
    )
    worse_delay = _candidate_labeled_head_and_delay_logits(
        worse,
        worse_output,
        label_attr="y_candidate_delay_risk",
    )
    if better_safe is None or worse_delay is None:
        return base_tensor.new_tensor(0.0)
    better_hp, better_delay = better_safe
    worse_hp, worse_delay_logit = worse_delay
    target = torch.ones_like(better_hp)
    candidate_head_loss = F.margin_ranking_loss(
        better_hp,
        worse_hp,
        target,
        margin=margin,
    )
    delay_head_loss = F.margin_ranking_loss(
        worse_delay_logit,
        better_delay,
        torch.ones_like(worse_delay_logit),
        margin=margin,
    )
    return 0.5 * (candidate_head_loss + delay_head_loss)


def _pairwise_delay_risk_contrast_loss(
    better: Any,
    better_output: dict[str, torch.Tensor],
    worse: Any,
    worse_output: dict[str, torch.Tensor],
    *,
    margin: float,
    base_tensor: torch.Tensor,
    loss_options: dict[str, Any],
) -> torch.Tensor:
    if float(loss_options.get("pairwise_delay_risk_contrast_loss_multiplier", 0.0)) <= 0.0:
        return base_tensor.new_tensor(0.0)
    better_safe = _candidate_labeled_head_and_delay_logits(
        better,
        better_output,
        label_attr="y_candidate_high_priority",
    )
    worse_delay = _candidate_labeled_head_and_delay_logits(
        worse,
        worse_output,
        label_attr="y_candidate_delay_risk",
    )
    if better_safe is None or worse_delay is None:
        return base_tensor.new_tensor(0.0)
    _, better_delay = better_safe
    _, worse_delay_logit = worse_delay
    return F.margin_ranking_loss(
        worse_delay_logit,
        better_delay,
        torch.ones_like(worse_delay_logit),
        margin=margin,
    )


def _candidate_labeled_head_and_delay_logits(
    sample: Any,
    output: dict[str, torch.Tensor],
    *,
    label_attr: str,
) -> tuple[torch.Tensor, torch.Tensor] | None:
    head_logits = output["high_priority_logit"].reshape(-1)
    delay_logits = output["delay_risk_logit"].reshape(-1)
    labels = getattr(sample, label_attr).to(device=head_logits.device).reshape(-1) > 0.5
    if labels.numel() != head_logits.numel() or labels.numel() != delay_logits.numel():
        raise ValueError(f"{label_attr} labels must match candidate logits")
    if not bool(torch.any(labels)):
        return None
    return head_logits[labels].max().reshape(1), delay_logits[labels].max().reshape(1)


def _prediction_records(
    model: GATBatchImpactModel,
    samples: list[Any],
    device: torch.device,
) -> list[dict[str, Any]]:
    model.eval()
    records: list[dict[str, Any]] = []
    with torch.no_grad():
        for sample in samples:
            sample = sample.to(device)
            output = model(
                sample,
                sample.candidate_task_membership,
                sample.candidate_sequence_positions,
                sample.candidate_features,
                sample.context_features,
                **_sample_model_kwargs(model, sample),
            )
            records.append(
                {
                    "family": str(getattr(sample, "batch_impact_instance_family", "") or "unknown"),
                    "context_hash": str(getattr(sample, "batch_impact_context_hash", "") or ""),
                    "batch_score": float(output["batch_roi_positive_probability"].detach().cpu().item()),
                    "candidate_scores": [
                        float(value)
                        for value in output["high_priority_probability"].detach().cpu().reshape(-1).tolist()
                    ],
                    "candidate_delay_scores": [
                        float(value)
                        for value in output["delay_risk_probability"].detach().cpu().reshape(-1).tolist()
                    ],
                    "candidate_high_priority_labels": [
                        int(value)
                        for value in sample.y_candidate_high_priority.detach().cpu().reshape(-1).to(dtype=torch.long).tolist()
                    ],
                    "candidate_delay_labels": [
                        int(value)
                        for value in sample.y_candidate_delay_risk.detach().cpu().reshape(-1).to(dtype=torch.long).tolist()
                    ],
                    "batch_roi_positive": int(sample.y_batch_roi_positive.detach().cpu().item() > 0.5),
                    "bad_mode_switch": int(sample.y_bad_mode_switch.detach().cpu().item() > 0.5),
                    "tail_improved": int(sample.y_tail_improved.detach().cpu().item() > 0.5),
                    "support_changed_good": int(sample.y_support_changed_good.detach().cpu().item() > 0.5),
                    "accepted_batch_roi_label": float(sample.y_accepted_batch_roi.detach().cpu().item()),
                }
            )
    return records


def _gate_config(
    args: argparse.Namespace | TrainBatchImpactArgs,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    specific_baselines = {
        "random_baseline_accepted_batch_roi": getattr(args, "random_baseline_accepted_batch_roi", None),
        "best_rc_baseline_accepted_batch_roi": getattr(args, "best_rc_baseline_accepted_batch_roi", None),
        "old_gat_baseline_accepted_batch_roi": getattr(args, "old_gat_baseline_accepted_batch_roi", None),
    }
    baseline_selection_roi = _baseline_selection_roi(args)
    hard_min_accepted_roi = max(
        float(args.min_accepted_batch_roi),
        baseline_selection_roi + float(args.min_roi_margin_over_baseline),
    )
    min_hp_precision = float(args.min_validation_high_priority_precision)
    min_safe_precision = float(args.min_validation_safe_precision)
    explicit_hp_ci = getattr(args, "min_validation_high_priority_precision_ci_low", None)
    explicit_safe_ci = getattr(args, "min_validation_safe_precision_ci_low", None)
    explicit_roi_ci = getattr(args, "min_accepted_batch_roi_ci_low", None)
    explicit_family_roi = getattr(args, "min_family_holdout_accepted_roi", None)
    if explicit_family_roi is None:
        min_family_holdout_accepted_roi = hard_min_accepted_roi
    else:
        min_family_holdout_accepted_roi = float(explicit_family_roi)
    return {
        "min_high_priority_precision": min_hp_precision,
        "min_high_priority_precision_ci_low": (
            min_hp_precision if explicit_hp_ci is None else float(explicit_hp_ci)
        ),
        "min_safe_precision": min_safe_precision,
        "min_safe_precision_ci_low": (
            min_safe_precision if explicit_safe_ci is None else float(explicit_safe_ci)
        ),
        "confidence_z": float(getattr(args, "confidence_z", 1.96)),
        "max_false_high_priority_on_delay": float(args.max_false_high_priority_on_delay),
        "max_false_safe_union_rate": float(args.max_false_safe_union_rate),
        "max_accepted_bad_mode_count": max(
            0,
            int(getattr(args, "max_accepted_bad_mode_count", 0)),
        ),
        "min_accepted_batch_count": int(args.min_accepted_batch_count),
        "min_accepted_batch_rate": float(getattr(args, "min_accepted_batch_rate", 0.02)),
        "min_accepted_batch_roi": hard_min_accepted_roi,
        "min_accepted_batch_roi_ci_low": (
            hard_min_accepted_roi if explicit_roi_ci is None else float(explicit_roi_ci)
        ),
        "baseline_accepted_batch_roi": float(baseline_selection_roi),
        "baseline_selection_roi": float(baseline_selection_roi),
        "baseline_roi_ci_high": float(baseline_selection_roi),
        "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
        "random_baseline_accepted_batch_roi": (
            float(specific_baselines["random_baseline_accepted_batch_roi"])
            if specific_baselines["random_baseline_accepted_batch_roi"] is not None
            else float(baseline_selection_roi)
        ),
        "best_rc_baseline_accepted_batch_roi": (
            float(specific_baselines["best_rc_baseline_accepted_batch_roi"])
            if specific_baselines["best_rc_baseline_accepted_batch_roi"] is not None
            else float(baseline_selection_roi)
        ),
        "old_gat_baseline_accepted_batch_roi": (
            float(specific_baselines["old_gat_baseline_accepted_batch_roi"])
            if specific_baselines["old_gat_baseline_accepted_batch_roi"] is not None
            else float(baseline_selection_roi)
        ),
        "min_roi_margin_over_baseline": float(args.min_roi_margin_over_baseline),
        "min_family_holdout_precision": float(getattr(args, "min_family_holdout_precision", 0.80)),
        "min_family_holdout_accepted_roi": float(min_family_holdout_accepted_roi),
        "min_family_accepted_high_roi_count": max(
            0,
            int(getattr(args, "min_family_accepted_high_roi_count", 0)),
        ),
        "min_family_high_roi_capture_rate": max(
            0.0,
            float(getattr(args, "min_family_high_roi_capture_rate", 0.0)),
        ),
        "candidate_admission_score_mode": str(
            getattr(args, "candidate_admission_score_mode", "high_priority")
            or "high_priority"
        ),
        "candidate_delay_score_penalty": max(
            0.0,
            float(getattr(args, "candidate_delay_score_penalty", 0.0)),
        ),
        "candidate_rescue_raw_score_threshold": min(
            1.0,
            max(
                0.0,
                float(getattr(args, "candidate_rescue_raw_score_threshold", 1.0)),
            ),
        ),
        "candidate_rescue_delay_risk_threshold": min(
            1.0,
            max(
                0.0,
                float(getattr(args, "candidate_rescue_delay_risk_threshold", 1.0)),
            ),
        ),
        "candidate_rescue_delay_score_penalty": max(
            0.0,
            float(getattr(args, "candidate_rescue_delay_score_penalty", 0.0)),
        ),
        "min_major_families": int(args.min_major_families),
        "observed_family_count": len(dict(manifest.get("family_counts") or {})),
        "stage3_min_samples": int(getattr(args, "stage3_min_samples", 200)),
        "actual_sample_count": int(manifest.get("sample_count") or 0),
        "knn_ood_audit_completed": False,
        "candidate_delay_gate_enabled": bool(
            getattr(args, "candidate_delay_gate_enabled", False)
        ),
        "candidate_delay_risk_threshold": min(
            1.0,
            max(0.0, float(getattr(args, "candidate_delay_risk_threshold", 0.5))),
        ),
        "require_positive_candidate_threshold": bool(
            getattr(args, "require_positive_candidate_threshold", True)
        ),
    }


def _baseline_selection_roi(args: argparse.Namespace | TrainBatchImpactArgs) -> float:
    baseline_values = [
        float(getattr(args, "baseline_accepted_batch_roi", 0.0)),
    ]
    for name in (
        "random_baseline_accepted_batch_roi",
        "best_rc_baseline_accepted_batch_roi",
        "old_gat_baseline_accepted_batch_roi",
    ):
        value = getattr(args, name, None)
        if value is not None:
            baseline_values.append(float(value))
    return max(baseline_values)


def _threshold_search(
    records: list[dict[str, Any]],
    *,
    gate_config: dict[str, Any],
    fixed_threshold: float | None = None,
    fixed_batch_threshold: float | None = None,
    fixed_candidate_threshold: float | None = None,
    fixed_batch_thresholds_by_family: dict[str, float] | None = None,
    fixed_delay_fallback_families: list[str] | None = None,
    fixed_context_delay_fallback_contexts: list[str] | None = None,
) -> dict[str, Any]:
    if fixed_threshold is not None:
        fixed_batch_threshold = float(fixed_threshold)
        fixed_candidate_threshold = float(fixed_threshold)
    if fixed_batch_threshold is None or fixed_candidate_threshold is None:
        grid = {0.0, 0.5, 0.65, 0.75, 0.85, 0.9, 0.95, 0.99, 1.0}
        batch_scores: list[float] = []
        candidate_scores: list[float] = []
        for record in records:
            batch_scores.append(float(record["batch_score"]))
            candidate_scores.extend(
                float(score) for score in _candidate_admission_scores(record, gate_config=gate_config)
            )
        batch_thresholds = _threshold_values(batch_scores, grid=grid, max_dynamic=128)
        candidate_thresholds = _threshold_values(candidate_scores, grid=grid, max_dynamic=128)
        thresholds = [
            (batch_threshold, candidate_threshold)
            for batch_threshold in batch_thresholds
            for candidate_threshold in candidate_thresholds
        ]
    else:
        thresholds = [(float(fixed_batch_threshold), float(fixed_candidate_threshold))]
    evaluated = [
        _deployment_metrics(
            records,
            batch_threshold=batch_threshold,
            candidate_threshold=candidate_threshold,
            gate_config=gate_config,
            batch_thresholds_by_family=fixed_batch_thresholds_by_family,
            delay_fallback_families=fixed_delay_fallback_families,
            context_delay_fallback_contexts=fixed_context_delay_fallback_contexts,
        )
        for batch_threshold, candidate_threshold in thresholds
    ]
    if fixed_delay_fallback_families is None and fixed_context_delay_fallback_contexts is None:
        evaluated.extend(
            _family_delay_fallback_threshold_metrics(
                records,
                evaluated=evaluated,
                gate_config=gate_config,
            )
        )
    if fixed_batch_thresholds_by_family is None and fixed_batch_threshold is None:
        evaluated.extend(
            _family_local_threshold_metrics(
                records,
                candidate_thresholds=candidate_thresholds,
                gate_config=gate_config,
            )
        )
    feasible = [item for item in evaluated if item["threshold_local_gate_pass"]]
    if feasible:
        selected = max(
            feasible,
            key=_threshold_feasible_selection_key,
        )
    else:
        selected = max(
            evaluated,
            key=_threshold_diagnostic_selection_key,
        ) if evaluated else _deployment_metrics(
            [],
            batch_threshold=0.9,
            candidate_threshold=0.9,
            gate_config=gate_config,
        )
    return {
        "selected_metrics": selected,
        "candidate_count": len(evaluated),
        "feasible_threshold_count": len(feasible),
        "best_rejected_reasons": selected.get("checkpoint_gate_reject_reasons", []),
        "best_local_rejected_reasons": selected.get("threshold_local_reject_reasons", []),
    }


def _threshold_values(scores: list[float], *, grid: set[float], max_dynamic: int) -> list[float]:
    values = sorted({float(value) for value in scores if value == value})
    if len(values) > int(max_dynamic):
        if int(max_dynamic) <= 1:
            values = [values[-1]]
        else:
            last_index = len(values) - 1
            values = [
                values[int(round(last_index * rank / float(int(max_dynamic) - 1)))]
                for rank in range(int(max_dynamic))
            ]
    return sorted(set(float(value) for value in grid).union(values))


def _metric_float(value: Any, *, default: float = float("-inf")) -> float:
    if value is None:
        return float(default)
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return float(default)
    if not math.isfinite(numeric):
        return float(default)
    return numeric


def _gate_baseline(gate_config: dict[str, Any], key: str) -> float:
    return float(gate_config.get(key, gate_config.get("baseline_accepted_batch_roi", 0.0)))


def _threshold_feasible_selection_key(metrics: dict[str, Any]) -> tuple[float, ...]:
    return (
        _metric_float(metrics.get("accepted_batch_roi_ci_low")),
        _metric_float(metrics.get("accepted_batch_roi_over_baseline_ci_low")),
        _metric_float(metrics.get("accepted_batch_roi_over_baseline")),
        _metric_float(metrics.get("family_holdout_min_high_roi_capture_rate"), default=0.0),
        _metric_float(metrics.get("family_holdout_min_accepted_high_roi_count"), default=0.0),
        _metric_float(metrics.get("expected_trajectory_utility"), default=0.0),
        _metric_float(metrics.get("accepted_batch_roi")),
        float(int(metrics.get("accepted_batch_count") or 0)),
        -float(len(metrics.get("family_delay_fallback_families") or [])),
        -float(len(metrics.get("context_delay_fallback_contexts") or [])),
        _metric_float(metrics.get("batch_threshold"), default=0.0),
        _metric_float(metrics.get("candidate_threshold"), default=0.0),
    )


def _threshold_diagnostic_selection_key(metrics: dict[str, Any]) -> tuple[float, ...]:
    return (
        -float(len(metrics.get("threshold_local_reject_reasons") or [])),
        _metric_float(metrics.get("high_priority_precision_ci_low")),
        _metric_float(metrics.get("safe_precision_ci_low")),
        _metric_float(metrics.get("accepted_batch_roi_ci_low")),
        _metric_float(metrics.get("accepted_batch_roi_over_baseline_ci_low")),
        _metric_float(metrics.get("family_holdout_min_high_roi_capture_rate"), default=0.0),
        _metric_float(metrics.get("family_holdout_min_accepted_high_roi_count"), default=0.0),
        _metric_float(metrics.get("high_priority_precision"), default=0.0),
        _metric_float(metrics.get("safe_precision"), default=0.0),
        _metric_float(metrics.get("accepted_batch_roi_over_baseline")),
        _metric_float(metrics.get("expected_trajectory_utility"), default=0.0),
        _metric_float(metrics.get("accepted_batch_roi")),
        float(int(metrics.get("accepted_batch_count") or 0)),
        -float(len(metrics.get("family_delay_fallback_families") or [])),
        -float(len(metrics.get("context_delay_fallback_contexts") or [])),
        -_metric_float(metrics.get("false_safe_rate_union"), default=1.0),
        _metric_float(metrics.get("batch_threshold"), default=0.0),
        _metric_float(metrics.get("candidate_threshold"), default=0.0),
    )


def _checkpoint_selection_key(
    metrics: dict[str, Any],
    *,
    local_gate_pass_score: float,
    validation_loss: float,
) -> tuple[float, ...]:
    return (
        float(local_gate_pass_score),
        *_threshold_feasible_selection_key(metrics),
        -float(validation_loss),
    )


def _wilson_ci_low(successes: int, total: int, *, z: float = 1.96) -> float | None:
    if int(total) <= 0:
        return None
    n = float(total)
    p_hat = float(successes) / n
    z2 = float(z) * float(z)
    denominator = 1.0 + z2 / n
    center = p_hat + z2 / (2.0 * n)
    margin = float(z) * math.sqrt((p_hat * (1.0 - p_hat) + z2 / (4.0 * n)) / n)
    return max(0.0, (center - margin) / denominator)


def _mean_ci_low(values: list[float], *, z: float = 1.96) -> float | None:
    if not values:
        return None
    if len(values) < 2:
        return None
    mean = sum(float(value) for value in values) / float(len(values))
    variance = sum((float(value) - mean) ** 2 for value in values) / float(len(values) - 1)
    return mean - float(z) * math.sqrt(variance / float(len(values)))


def _deployment_metrics(
    records: list[dict[str, Any]],
    *,
    batch_threshold: float,
    candidate_threshold: float,
    gate_config: dict[str, Any],
    batch_thresholds_by_family: dict[str, float] | None = None,
    delay_fallback_families: list[str] | None = None,
    context_delay_fallback_contexts: list[str] | None = None,
) -> dict[str, Any]:
    total_batches = len(records)
    fallback_families = {str(family) for family in (delay_fallback_families or [])}
    fallback_contexts = {str(context) for context in (context_delay_fallback_contexts or [])}
    accepted = [
        record
        for record in records
        if not _record_is_delay_fallback(
            record,
            fallback_families=fallback_families,
            fallback_contexts=fallback_contexts,
        )
        if _record_is_batch_accepted(
            record,
            batch_threshold=batch_threshold,
            candidate_threshold=candidate_threshold,
            gate_config=gate_config,
            batch_thresholds_by_family=batch_thresholds_by_family,
        )
    ]
    accepted_count = len(accepted)
    accepted_positive = sum(int(record["batch_roi_positive"]) for record in accepted)
    accepted_bad = sum(int(record["bad_mode_switch"]) for record in accepted)
    accepted_roi_values = [float(record["accepted_batch_roi_label"]) for record in accepted]
    accepted_batch_roi = (
        sum(accepted_roi_values) / float(len(accepted_roi_values)) if accepted_roi_values else 0.0
    )
    safe_precision = None if accepted_count <= 0 else accepted_positive / float(accepted_count)
    confidence_z = float(gate_config.get("confidence_z", 1.96))
    safe_precision_ci_low = _wilson_ci_low(
        accepted_positive,
        accepted_count,
        z=confidence_z,
    )
    accepted_batch_roi_ci_low = _mean_ci_low(accepted_roi_values, z=confidence_z)
    accepted_batch_rate = accepted_count / float(total_batches) if total_batches else 0.0
    delay_rate = 1.0 - accepted_batch_rate
    total_unsafe_batches = sum(int(record["bad_mode_switch"]) for record in records)
    false_safe_rate_label_unsafe = (
        accepted_bad / float(total_unsafe_batches) if total_unsafe_batches > 0 else 0.0
    )

    pred_hp = true_hp = false_hp_delay = delay_label_count = delay_gate_blocked = 0
    candidate_count = score_threshold_blocked = 0
    risk_adjusted_suppressed = 0
    rescue_window_eligible = 0
    rescue_window_promoted = 0
    for record in records:
        if _record_is_delay_fallback(
            record,
            fallback_families=fallback_families,
            fallback_contexts=fallback_contexts,
        ):
            continue
        (
            candidate_prediction_indices,
            blocked_count,
            score_blocked_count,
            suppressed_count,
            rescue_eligible_count,
            rescue_promoted_count,
        ) = _record_candidate_prediction_indices(
            record,
            candidate_threshold=candidate_threshold,
            gate_config=gate_config,
        )
        candidate_count += len(record.get("candidate_scores", []))
        delay_gate_blocked += int(blocked_count)
        score_threshold_blocked += int(score_blocked_count)
        risk_adjusted_suppressed += int(suppressed_count)
        rescue_window_eligible += int(rescue_eligible_count)
        rescue_window_promoted += int(rescue_promoted_count)
        predicted_set = set(candidate_prediction_indices)
        for idx, (hp_label, delay_label) in enumerate(
            zip(
                record["candidate_high_priority_labels"],
                record["candidate_delay_labels"],
            )
        ):
            if int(delay_label):
                delay_label_count += 1
            if idx in predicted_set:
                pred_hp += 1
                if int(hp_label):
                    true_hp += 1
                if int(delay_label):
                    false_hp_delay += 1
    high_priority_precision = None if pred_hp <= 0 else true_hp / float(pred_hp)
    high_priority_precision_ci_low = _wilson_ci_low(true_hp, pred_hp, z=confidence_z)
    false_high_priority_on_delay = (
        false_hp_delay / float(delay_label_count) if delay_label_count > 0 else 0.0
    )
    false_safe_rate_union = max(false_high_priority_on_delay, false_safe_rate_label_unsafe)
    expected_trajectory_utility = 0.0
    if accepted:
        utilities = [
            float(record["accepted_batch_roi_label"])
            + 0.1 * float(record["tail_improved"])
            + 0.05 * float(record["support_changed_good"])
            - 0.5 * float(record["bad_mode_switch"])
            for record in accepted
        ]
        expected_trajectory_utility = sum(utilities) / float(len(utilities))
    family_metrics = _family_holdout_metrics(
        records,
        batch_threshold=batch_threshold,
        candidate_threshold=candidate_threshold,
        gate_config=gate_config,
        batch_thresholds_by_family=batch_thresholds_by_family,
        delay_fallback_families=sorted(fallback_families),
        context_delay_fallback_contexts=sorted(fallback_contexts),
        min_accepted_batch_roi=float(gate_config["min_family_holdout_accepted_roi"]),
    )
    reject_reasons = _checkpoint_gate_reject_reasons(
        {
            "high_priority_precision": high_priority_precision,
            "high_priority_precision_ci_low": high_priority_precision_ci_low,
            "safe_precision": safe_precision,
            "safe_precision_ci_low": safe_precision_ci_low,
            "accepted_batch_count": accepted_count,
            "accepted_batch_rate": accepted_batch_rate,
            "accepted_bad_mode_count": accepted_bad,
            "accepted_batch_roi": accepted_batch_roi,
            "accepted_batch_roi_ci_low": accepted_batch_roi_ci_low,
            "expected_trajectory_utility": expected_trajectory_utility,
            "candidate_threshold": candidate_threshold,
            "evaluated_candidate_count": candidate_count,
            "candidate_score_threshold_blocked_count": score_threshold_blocked,
            "false_high_priority_on_delay": false_high_priority_on_delay,
            "false_safe_rate_union": false_safe_rate_union,
            "family_holdout_min_precision": family_metrics["family_holdout_min_precision"],
            "family_holdout_min_accepted_roi": family_metrics["family_holdout_min_accepted_roi"],
            "family_holdout_missing_accepted_families": family_metrics[
                "family_holdout_missing_accepted_families"
            ],
            "family_holdout_missing_accepted_opportunity_families": family_metrics[
                "family_holdout_missing_accepted_opportunity_families"
            ],
            "family_holdout_min_accepted_high_roi_count": family_metrics[
                "family_holdout_min_accepted_high_roi_count"
            ],
            "family_holdout_min_high_roi_capture_rate": family_metrics[
                "family_holdout_min_high_roi_capture_rate"
            ],
        },
        gate_config=gate_config,
    )
    local_reject_reasons = _threshold_local_reject_reasons(reject_reasons)
    return {
        "threshold": float(batch_threshold),
        "batch_threshold": float(batch_threshold),
        "batch_thresholds_by_family": {
            str(key): float(value) for key, value in sorted((batch_thresholds_by_family or {}).items())
        },
        "family_delay_fallback_families": sorted(fallback_families),
        "context_delay_fallback_contexts": sorted(fallback_contexts),
        "candidate_threshold": float(candidate_threshold),
        "candidate_admission_score_mode": _candidate_admission_score_mode(gate_config),
        "candidate_delay_score_penalty": _candidate_delay_score_penalty(gate_config),
        "candidate_rescue_raw_score_threshold": _candidate_rescue_raw_score_threshold(gate_config),
        "candidate_rescue_delay_risk_threshold": _candidate_rescue_delay_risk_threshold(gate_config),
        "candidate_rescue_delay_score_penalty": _candidate_rescue_delay_score_penalty(gate_config),
        "candidate_delay_gate_enabled": bool(
            gate_config.get("candidate_delay_gate_enabled", False)
        ),
        "candidate_delay_risk_threshold": float(
            gate_config.get("candidate_delay_risk_threshold", 1.0)
        ),
        "threshold_mode": (
            "family_context_delay_fallback"
            if fallback_families and fallback_contexts
            else (
                "context_delay_fallback"
                if fallback_contexts and not batch_thresholds_by_family
                else (
                    "family_delay_fallback"
                    if fallback_families and not batch_thresholds_by_family
                    else (
                        "family_local_batch_candidate_with_delay_fallback"
                        if (fallback_families or fallback_contexts) and batch_thresholds_by_family
                        else (
                            "family_local_batch_candidate"
                            if batch_thresholds_by_family
                            else "separate_batch_candidate"
                        )
                    )
                )
            )
        ),
        "total_batches": int(total_batches),
        "accepted_batch_count": int(accepted_count),
        "accepted_batch_rate": float(accepted_batch_rate),
        "accepted_bad_mode_count": int(accepted_bad),
        "max_accepted_bad_mode_count": int(gate_config.get("max_accepted_bad_mode_count", 0)),
        "accepted_batch_roi": float(accepted_batch_roi),
        "accepted_batch_roi_ci_low": accepted_batch_roi_ci_low,
        "accepted_batch_roi_over_baseline": float(
            accepted_batch_roi - float(gate_config["baseline_accepted_batch_roi"])
        ),
        "accepted_batch_roi_over_random_baseline": float(
            accepted_batch_roi - _gate_baseline(gate_config, "random_baseline_accepted_batch_roi")
        ),
        "accepted_batch_roi_over_best_rc_baseline": float(
            accepted_batch_roi - _gate_baseline(gate_config, "best_rc_baseline_accepted_batch_roi")
        ),
        "accepted_batch_roi_over_old_gat_baseline": float(
            accepted_batch_roi - _gate_baseline(gate_config, "old_gat_baseline_accepted_batch_roi")
        ),
        "accepted_batch_roi_over_baseline_ci_low": (
            None
            if accepted_batch_roi_ci_low is None
            else float(accepted_batch_roi_ci_low - float(gate_config["baseline_accepted_batch_roi"]))
        ),
        "accepted_batch_roi_over_random_baseline_ci_low": (
            None
            if accepted_batch_roi_ci_low is None
            else float(
                accepted_batch_roi_ci_low - _gate_baseline(gate_config, "random_baseline_accepted_batch_roi")
            )
        ),
        "accepted_batch_roi_over_best_rc_baseline_ci_low": (
            None
            if accepted_batch_roi_ci_low is None
            else float(
                accepted_batch_roi_ci_low - _gate_baseline(gate_config, "best_rc_baseline_accepted_batch_roi")
            )
        ),
        "accepted_batch_roi_over_old_gat_baseline_ci_low": (
            None
            if accepted_batch_roi_ci_low is None
            else float(
                accepted_batch_roi_ci_low - _gate_baseline(gate_config, "old_gat_baseline_accepted_batch_roi")
            )
        ),
        "min_family_accepted_high_roi_count": int(
            gate_config.get("min_family_accepted_high_roi_count", 0) or 0
        ),
        "min_family_high_roi_capture_rate": float(
            gate_config.get("min_family_high_roi_capture_rate", 0.0) or 0.0
        ),
        "baseline_selection_roi": _gate_baseline(gate_config, "baseline_selection_roi"),
        "baseline_roi_ci_high": _gate_baseline(gate_config, "baseline_roi_ci_high"),
        "baseline_roi_ci_high_source": str(
            gate_config.get("baseline_roi_ci_high_source", "configured_point_estimate_no_baseline_distribution")
        ),
        "random_baseline_accepted_batch_roi": _gate_baseline(gate_config, "random_baseline_accepted_batch_roi"),
        "best_rc_baseline_accepted_batch_roi": _gate_baseline(gate_config, "best_rc_baseline_accepted_batch_roi"),
        "old_gat_baseline_accepted_batch_roi": _gate_baseline(gate_config, "old_gat_baseline_accepted_batch_roi"),
        "accepted_batch_precision": safe_precision,
        "safe_precision": safe_precision,
        "safe_precision_ci_low": safe_precision_ci_low,
        "high_priority_prediction_count": int(pred_hp),
        "high_priority_true_positive_count": int(true_hp),
        "high_priority_precision": high_priority_precision,
        "high_priority_precision_ci_low": high_priority_precision_ci_low,
        "evaluated_candidate_count": int(candidate_count),
        "candidate_score_threshold_blocked_count": int(score_threshold_blocked),
        "candidate_delay_gate_blocked_count": int(delay_gate_blocked),
        "candidate_risk_adjusted_suppressed_count": int(risk_adjusted_suppressed),
        "candidate_rescue_window_eligible_count": int(rescue_window_eligible),
        "candidate_rescue_window_promoted_count": int(rescue_window_promoted),
        "false_high_priority_on_delay_count": int(false_hp_delay),
        "delay_label_count": int(delay_label_count),
        "false_high_priority_on_delay": float(false_high_priority_on_delay),
        "false_safe_rate_label_unsafe": float(false_safe_rate_label_unsafe),
        "false_safe_rate_union": float(false_safe_rate_union),
        "coverage_non_ood": 1.0,
        "delay_rate": float(delay_rate),
        "expected_trajectory_utility": float(expected_trajectory_utility),
        "family_holdout_min_precision": family_metrics["family_holdout_min_precision"],
        "family_holdout_min_accepted_roi": family_metrics["family_holdout_min_accepted_roi"],
        "family_holdout_per_family": family_metrics["family_holdout_per_family"],
        "family_holdout_missing_accepted_families": family_metrics[
            "family_holdout_missing_accepted_families"
        ],
        "family_holdout_missing_accepted_opportunity_families": family_metrics[
            "family_holdout_missing_accepted_opportunity_families"
        ],
        "family_specific_delay_fallback_families": family_metrics[
            "family_specific_delay_fallback_families"
        ],
        "family_holdout_oracle_high_roi_families": family_metrics[
            "family_holdout_oracle_high_roi_families"
        ],
        "family_holdout_min_accepted_high_roi_count": family_metrics[
            "family_holdout_min_accepted_high_roi_count"
        ],
        "family_holdout_min_high_roi_capture_rate": family_metrics[
            "family_holdout_min_high_roi_capture_rate"
        ],
        "checkpoint_gate_pass": not reject_reasons,
        "checkpoint_gate_reject_reasons": reject_reasons,
        "hard_reject_reason_categories": _hard_reject_reason_categories(reject_reasons),
        "threshold_local_gate_pass": not local_reject_reasons,
        "threshold_local_reject_reasons": local_reject_reasons,
        "threshold_local_hard_reject_reason_categories": _hard_reject_reason_categories(
            local_reject_reasons
        ),
    }


def _record_batch_threshold(
    record: dict[str, Any],
    *,
    batch_threshold: float,
    batch_thresholds_by_family: dict[str, float] | None = None,
) -> float:
    if not batch_thresholds_by_family:
        return float(batch_threshold)
    family = str(record.get("family") or record.get("instance_family") or "unknown")
    return float(batch_thresholds_by_family.get(family, batch_threshold))


def _candidate_delay_gate_enabled(gate_config: dict[str, Any] | None) -> bool:
    return bool((gate_config or {}).get("candidate_delay_gate_enabled", False))


def _candidate_delay_risk_threshold(gate_config: dict[str, Any] | None) -> float:
    return min(1.0, max(0.0, float((gate_config or {}).get("candidate_delay_risk_threshold", 1.0))))


def _candidate_admission_score_mode(gate_config: dict[str, Any] | None) -> str:
    mode = str((gate_config or {}).get("candidate_admission_score_mode", "high_priority") or "high_priority")
    if mode not in {"high_priority", "risk_adjusted_product", "risk_adjusted_rescue_window"}:
        return "high_priority"
    return mode


def _candidate_delay_score_penalty(gate_config: dict[str, Any] | None) -> float:
    return max(0.0, float((gate_config or {}).get("candidate_delay_score_penalty", 0.0)))


def _candidate_rescue_raw_score_threshold(gate_config: dict[str, Any] | None) -> float:
    return min(
        1.0,
        max(0.0, float((gate_config or {}).get("candidate_rescue_raw_score_threshold", 1.0))),
    )


def _candidate_rescue_delay_risk_threshold(gate_config: dict[str, Any] | None) -> float:
    return min(
        1.0,
        max(0.0, float((gate_config or {}).get("candidate_rescue_delay_risk_threshold", 1.0))),
    )


def _candidate_rescue_delay_score_penalty(gate_config: dict[str, Any] | None) -> float:
    return max(0.0, float((gate_config or {}).get("candidate_rescue_delay_score_penalty", 0.0)))


def _candidate_delay_scores(record: dict[str, Any], *, gate_config: dict[str, Any] | None) -> list[float]:
    candidate_scores = [float(score) for score in record.get("candidate_scores", [])]
    delay_scores = [float(score) for score in record.get("candidate_delay_scores", [])]
    if len(delay_scores) == len(candidate_scores):
        return delay_scores
    default_score = 1.0 if _candidate_delay_gate_enabled(gate_config) else 0.0
    return [float(default_score) for _ in candidate_scores]


def _candidate_risk_adjusted_scores(
    candidate_scores: list[float],
    delay_scores: list[float],
    *,
    penalty: float,
) -> list[float]:
    adjusted: list[float] = []
    for candidate_score, delay_score in zip(candidate_scores, delay_scores):
        risk_factor = max(0.0, min(1.0, 1.0 - float(delay_score)))
        adjusted.append(max(0.0, min(1.0, float(candidate_score) * (risk_factor ** max(0.0, float(penalty))))))
    return adjusted


def _candidate_rescue_window_eligible(
    raw_score: float,
    delay_score: float,
    *,
    gate_config: dict[str, Any] | None,
) -> bool:
    if _candidate_admission_score_mode(gate_config) != "risk_adjusted_rescue_window":
        return False
    return (
        float(raw_score) >= _candidate_rescue_raw_score_threshold(gate_config)
        and float(delay_score) <= _candidate_rescue_delay_risk_threshold(gate_config)
    )


def _candidate_admission_scores(record: dict[str, Any], *, gate_config: dict[str, Any] | None) -> list[float]:
    candidate_scores = [float(score) for score in record.get("candidate_scores", [])]
    mode = _candidate_admission_score_mode(gate_config)
    if mode == "high_priority":
        return candidate_scores
    delay_scores = _candidate_delay_scores(record, gate_config=gate_config)
    base_scores = _candidate_risk_adjusted_scores(
        candidate_scores,
        delay_scores,
        penalty=_candidate_delay_score_penalty(gate_config),
    )
    if mode != "risk_adjusted_rescue_window":
        return base_scores
    rescue_scores = _candidate_risk_adjusted_scores(
        candidate_scores,
        delay_scores,
        penalty=_candidate_rescue_delay_score_penalty(gate_config),
    )
    adjusted: list[float] = []
    for idx, base_score in enumerate(base_scores):
        if idx < len(rescue_scores) and _candidate_rescue_window_eligible(
            candidate_scores[idx],
            delay_scores[idx],
            gate_config=gate_config,
        ):
            adjusted.append(max(float(base_score), float(rescue_scores[idx])))
        else:
            adjusted.append(float(base_score))
    return adjusted


def _focused_pair_gate_metrics(
    *,
    manifest_items: list[dict[str, Any]],
    prediction_records: list[dict[str, Any]],
    gate_config: dict[str, Any],
    args: argparse.Namespace | TrainBatchImpactArgs,
) -> dict[str, Any]:
    focus_row_index_min = getattr(args, "focused_pair_gate_row_index_min", None)
    focus_row_indices = _focused_pair_row_indices(args)
    focus_row_index_set = set(focus_row_indices)
    active = focus_row_index_min is not None or bool(focus_row_index_set)
    focus_selector = "explicit_row_indices" if focus_row_index_set else "row_index_min"
    thresholds = {
        "min_focused_pair_count": max(0, int(getattr(args, "min_focused_pair_count", 1))),
        "min_raw_pair_pass_rate": _clamped_rate(
            getattr(args, "min_focused_raw_pair_pass_rate", 1.0)
        ),
        "min_admission_pair_pass_rate": _clamped_rate(
            getattr(args, "min_focused_admission_pair_pass_rate", 1.0)
        ),
        "min_delay_risk_pair_pass_rate": _clamped_rate(
            getattr(args, "min_focused_delay_risk_pair_pass_rate", 1.0)
        ),
        "min_strict_pair_pass_rate": _clamped_rate(
            getattr(args, "min_focused_strict_pair_pass_rate", 1.0)
        ),
    }
    if not active:
        return {
            "active": False,
            "focus_row_index_min": None,
            "focus_row_indices_file": (
                None
                if getattr(args, "focused_pair_row_indices_file", None) is None
                else str(getattr(args, "focused_pair_row_indices_file"))
            ),
            "focus_row_indices_count": 0,
            "focus_selector": None,
            "thresholds": thresholds,
            "summary": {
                "focused_row_count": 0,
                "context_count": 0,
                "contexts_with_positive_and_negative": 0,
                "pair_count": 0,
                "raw_pair_pass_rate": None,
                "admission_pair_pass_rate": None,
                "delay_risk_pair_pass_rate": None,
                "strict_pair_pass_rate": None,
                "primary": "focused_pair_gate_not_run",
            },
            "gate": {
                "gate_name": "focused_same_context_positive_negative_pair_gate",
                "gate_pass": False,
                "reject_reasons": ["focused_pair_gate_not_run"],
                "thresholds": thresholds,
                "observed": {},
                "blocking_primary": "focused_pair_gate_not_run",
                "diagnostic_only": True,
                "production_ready": False,
                "selector_can_certificate": False,
            },
            "diagnostic_only": True,
            "runs_bpc_or_pricing": False,
            "production_ready": False,
        }

    rows = [
        _focused_pair_row(item, record, gate_config=gate_config)
        for item, record in zip(manifest_items, prediction_records)
        if (
            _int_or_default(item.get("row_index"), -1) in focus_row_index_set
            if focus_row_index_set
            else _int_or_default(item.get("row_index"), -1) >= int(focus_row_index_min)
        )
    ]
    context_rows, pair_rows = _focused_context_and_pair_rows(rows)
    summary = _focused_pair_summary(rows, context_rows, pair_rows)
    gate = _focused_pair_gate(summary, thresholds=thresholds)
    return {
        "active": True,
        "focus_row_index_min": (
            None if focus_row_index_min is None else int(focus_row_index_min)
        ),
        "focus_row_indices_file": (
            None
            if getattr(args, "focused_pair_row_indices_file", None) is None
            else str(getattr(args, "focused_pair_row_indices_file"))
        ),
        "focus_row_indices_count": len(focus_row_indices),
        "focus_selector": focus_selector,
        "thresholds": thresholds,
        "summary": summary,
        "context_rows": context_rows,
        "pair_rows": pair_rows,
        "gate": gate,
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
    }


def _focused_pair_gate_reject_reasons(metrics: dict[str, Any]) -> list[str]:
    gate = dict(metrics.get("gate") or {})
    return [str(reason) for reason in gate.get("reject_reasons", [])]


def _focused_pair_row(
    manifest_item: dict[str, Any],
    prediction: dict[str, Any],
    *,
    gate_config: dict[str, Any],
) -> dict[str, Any]:
    candidate_scores = [float(value) for value in prediction.get("candidate_scores", [])]
    delay_scores = _candidate_delay_scores(prediction, gate_config=gate_config)
    admission_scores = _candidate_admission_scores(prediction, gate_config=gate_config)
    high_priority_labels = [int(value) for value in prediction.get("candidate_high_priority_labels", [])]
    delay_labels = [int(value) for value in prediction.get("candidate_delay_labels", [])]
    label_class = _focused_label_class(prediction)
    return {
        "row_index": _int_or_default(manifest_item.get("row_index"), -1),
        "context_key": _focused_context_key(manifest_item, prediction),
        "context_hash": str(manifest_item.get("context_hash") or prediction.get("context_hash") or ""),
        "family": str(manifest_item.get("instance_family") or prediction.get("family") or "unknown"),
        "candidate_signature_ids": list(manifest_item.get("candidate_signature_ids") or []),
        "label_class": label_class,
        "accepted_batch_roi_label": float(
            manifest_item.get("accepted_batch_roi")
            if manifest_item.get("accepted_batch_roi") is not None
            else prediction.get("accepted_batch_roi_label") or 0.0
        ),
        "bad_mode_switch": int(prediction.get("bad_mode_switch") or 0),
        "batch_score": float(prediction.get("batch_score") or 0.0),
        "max_raw_candidate_score": max(candidate_scores) if candidate_scores else 0.0,
        "max_admission_score": max(admission_scores) if admission_scores else 0.0,
        "max_delay_risk_score": max(delay_scores) if delay_scores else 0.0,
        "high_priority_label_count": int(sum(high_priority_labels)),
        "delay_label_count": int(sum(delay_labels)),
    }


def _focused_label_class(record: dict[str, Any]) -> str:
    high_priority = any(int(value) for value in record.get("candidate_high_priority_labels", []))
    delay = any(int(value) for value in record.get("candidate_delay_labels", []))
    roi_positive = bool(int(record.get("batch_roi_positive") or 0))
    bad_mode = bool(int(record.get("bad_mode_switch") or 0))
    if high_priority and roi_positive and not bad_mode:
        return "positive_high_priority"
    if delay or bad_mode or not roi_positive:
        return "delay_or_hard_negative"
    return "ambiguous"


def _focused_context_key(manifest_item: dict[str, Any], prediction: dict[str, Any]) -> str:
    instance = str(
        manifest_item.get("instance_path")
        or manifest_item.get("instance")
        or prediction.get("instance")
        or ""
    )
    context_hash = str(manifest_item.get("context_hash") or prediction.get("context_hash") or "")
    return "|".join([instance, context_hash])


def _focused_context_and_pair_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_context: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        key = str(row["context_key"])
        by_context.setdefault(key, []).append(row)
    context_rows: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    for key, group in sorted(by_context.items()):
        positives = [row for row in group if row["label_class"] == "positive_high_priority"]
        negatives = [row for row in group if row["label_class"] == "delay_or_hard_negative"]
        pairs = [
            _focused_pair_compare(positive, negative)
            for positive in positives
            for negative in negatives
        ]
        pair_rows.extend(pairs)
        context_rows.append(
            {
                "context_key": key,
                "context_hash": str(group[0].get("context_hash") or ""),
                "family": str(group[0].get("family") or "unknown"),
                "row_count": len(group),
                "positive_count": len(positives),
                "negative_count": len(negatives),
                "pair_count": len(pairs),
                "raw_pair_pass_rate": _focused_rate(pairs, "raw_positive_above_negative"),
                "admission_pair_pass_rate": _focused_rate(
                    pairs,
                    "admission_positive_above_negative",
                ),
                "delay_risk_pair_pass_rate": _focused_rate(
                    pairs,
                    "positive_lower_delay_risk",
                ),
                "strict_pair_pass_rate": _focused_rate(pairs, "pair_pass"),
            }
        )
    return context_rows, pair_rows


def _focused_pair_compare(
    positive: dict[str, Any],
    negative: dict[str, Any],
) -> dict[str, Any]:
    raw_margin = float(positive["max_raw_candidate_score"]) - float(
        negative["max_raw_candidate_score"]
    )
    admission_margin = float(positive["max_admission_score"]) - float(
        negative["max_admission_score"]
    )
    delay_margin = float(negative["max_delay_risk_score"]) - float(
        positive["max_delay_risk_score"]
    )
    return {
        "context_key": str(positive["context_key"]),
        "context_hash": str(positive["context_hash"]),
        "family": str(positive["family"]),
        "positive_row_index": int(positive["row_index"]),
        "negative_row_index": int(negative["row_index"]),
        "positive_roi": float(positive["accepted_batch_roi_label"]),
        "negative_roi": float(negative["accepted_batch_roi_label"]),
        "positive_signature_ids": list(positive.get("candidate_signature_ids") or []),
        "negative_signature_ids": list(negative.get("candidate_signature_ids") or []),
        "raw_margin": raw_margin,
        "admission_margin": admission_margin,
        "delay_risk_margin": delay_margin,
        "raw_positive_above_negative": raw_margin > 0.0,
        "admission_positive_above_negative": admission_margin > 0.0,
        "positive_lower_delay_risk": delay_margin > 0.0,
        "pair_pass": raw_margin > 0.0 and admission_margin > 0.0 and delay_margin > 0.0,
    }


def _focused_pair_summary(
    rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    label_counts: dict[str, int] = {}
    family_counts: dict[str, int] = {}
    for row in rows:
        label = str(row.get("label_class") or "unknown")
        family = str(row.get("family") or "unknown")
        label_counts[label] = label_counts.get(label, 0) + 1
        family_counts[family] = family_counts.get(family, 0) + 1
    return {
        "focused_row_count": len(rows),
        "context_count": len(context_rows),
        "contexts_with_positive_and_negative": sum(
            int(row["positive_count"] > 0 and row["negative_count"] > 0)
            for row in context_rows
        ),
        "positive_row_count": int(label_counts.get("positive_high_priority", 0)),
        "negative_row_count": int(label_counts.get("delay_or_hard_negative", 0)),
        "ambiguous_row_count": int(label_counts.get("ambiguous", 0)),
        "pair_count": len(pair_rows),
        "raw_pair_pass_count": _focused_count_true(pair_rows, "raw_positive_above_negative"),
        "admission_pair_pass_count": _focused_count_true(
            pair_rows,
            "admission_positive_above_negative",
        ),
        "delay_risk_pair_pass_count": _focused_count_true(
            pair_rows,
            "positive_lower_delay_risk",
        ),
        "strict_pair_pass_count": _focused_count_true(pair_rows, "pair_pass"),
        "raw_pair_pass_rate": _focused_rate(pair_rows, "raw_positive_above_negative"),
        "admission_pair_pass_rate": _focused_rate(
            pair_rows,
            "admission_positive_above_negative",
        ),
        "delay_risk_pair_pass_rate": _focused_rate(pair_rows, "positive_lower_delay_risk"),
        "strict_pair_pass_rate": _focused_rate(pair_rows, "pair_pass"),
        "label_counts": dict(sorted(label_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "primary": _focused_primary_diagnosis(pair_rows, context_rows),
    }


def _focused_pair_gate(
    summary: dict[str, Any],
    *,
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    reject_reasons: list[str] = []
    pair_count = int(summary.get("pair_count") or 0)
    if pair_count < int(thresholds["min_focused_pair_count"]):
        reject_reasons.append("not_enough_focused_positive_negative_pairs")
    _append_focused_rate_reject(
        reject_reasons,
        summary.get("raw_pair_pass_rate"),
        float(thresholds["min_raw_pair_pass_rate"]),
        "raw_pair_pass_rate_below_threshold",
    )
    _append_focused_rate_reject(
        reject_reasons,
        summary.get("admission_pair_pass_rate"),
        float(thresholds["min_admission_pair_pass_rate"]),
        "admission_pair_pass_rate_below_threshold",
    )
    _append_focused_rate_reject(
        reject_reasons,
        summary.get("delay_risk_pair_pass_rate"),
        float(thresholds["min_delay_risk_pair_pass_rate"]),
        "delay_risk_pair_pass_rate_below_threshold",
    )
    _append_focused_rate_reject(
        reject_reasons,
        summary.get("strict_pair_pass_rate"),
        float(thresholds["min_strict_pair_pass_rate"]),
        "strict_pair_pass_rate_below_threshold",
    )
    gate_pass = not reject_reasons
    return {
        "gate_name": "focused_same_context_positive_negative_pair_gate",
        "gate_pass": gate_pass,
        "reject_reasons": reject_reasons,
        "thresholds": thresholds,
        "observed": {
            "pair_count": pair_count,
            "raw_pair_pass_rate": summary.get("raw_pair_pass_rate"),
            "admission_pair_pass_rate": summary.get("admission_pair_pass_rate"),
            "delay_risk_pair_pass_rate": summary.get("delay_risk_pair_pass_rate"),
            "strict_pair_pass_rate": summary.get("strict_pair_pass_rate"),
        },
        "blocking_primary": (
            "focused_context_pair_gate_passed"
            if gate_pass
            else str(summary.get("primary") or "focused_pair_gate_failed")
        ),
        "diagnostic_only": True,
        "production_ready": False,
        "selector_can_certificate": False,
    }


def _focused_primary_diagnosis(
    pair_rows: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
) -> str:
    if not pair_rows:
        if any(int(row.get("positive_count") or 0) == 0 for row in context_rows):
            return "positive_counterpart_missing_in_some_contexts"
        return "no_pairwise_contrast_available"
    if any(not pair["raw_positive_above_negative"] for pair in pair_rows):
        return "candidate_head_context_ranking_failure"
    if any(not pair["positive_lower_delay_risk"] for pair in pair_rows):
        return "delay_risk_head_context_ranking_failure"
    if any(not pair["admission_positive_above_negative"] for pair in pair_rows):
        return "risk_adjusted_admission_ranking_failure"
    return "focused_context_ranking_passes"


def _append_focused_rate_reject(
    reject_reasons: list[str],
    observed: Any,
    threshold: float,
    reason: str,
) -> None:
    if observed is None or float(observed) < float(threshold):
        reject_reasons.append(reason)


def _focused_rate(rows: list[dict[str, Any]], field: str) -> float | None:
    if not rows:
        return None
    return float(_focused_count_true(rows, field)) / float(len(rows))


def _focused_count_true(rows: list[dict[str, Any]], field: str) -> int:
    return sum(int(bool(row.get(field))) for row in rows)


def _clamped_rate(value: Any) -> float:
    return min(1.0, max(0.0, float(value)))


def _int_or_default(value: Any, default: int) -> int:
    try:
        if value is None or value == "":
            return int(default)
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _record_candidate_prediction_indices(
    record: dict[str, Any],
    *,
    candidate_threshold: float,
    gate_config: dict[str, Any] | None = None,
) -> tuple[list[int], int, int, int, int, int]:
    delay_gate_enabled = _candidate_delay_gate_enabled(gate_config)
    delay_threshold = _candidate_delay_risk_threshold(gate_config)
    raw_scores = [float(score) for score in record.get("candidate_scores", [])]
    admission_scores = _candidate_admission_scores(record, gate_config=gate_config)
    delay_scores = _candidate_delay_scores(record, gate_config=gate_config)
    mode = _candidate_admission_score_mode(gate_config)
    base_scores = (
        raw_scores
        if mode == "high_priority"
        else _candidate_risk_adjusted_scores(
            raw_scores,
            delay_scores,
            penalty=_candidate_delay_score_penalty(gate_config),
        )
    )
    predicted: list[int] = []
    blocked = 0
    score_blocked = 0
    suppressed = 0
    rescue_eligible = 0
    rescue_promoted = 0
    for idx, score in enumerate(admission_scores):
        if idx >= len(raw_scores) or idx >= len(delay_scores):
            continue
        eligible = _candidate_rescue_window_eligible(
            raw_scores[idx],
            delay_scores[idx],
            gate_config=gate_config,
        )
        if eligible:
            rescue_eligible += 1
        base_score = float(base_scores[idx]) if idx < len(base_scores) else float(score)
        if (
            mode != "high_priority"
            and float(raw_scores[idx]) >= float(candidate_threshold)
            and base_score < float(candidate_threshold)
        ):
            suppressed += 1
        if float(score) < float(candidate_threshold):
            score_blocked += 1
            continue
        bypass_delay_gate = bool(eligible and mode == "risk_adjusted_rescue_window")
        if delay_gate_enabled and float(delay_scores[idx]) > float(delay_threshold) and not bypass_delay_gate:
            blocked += 1
            continue
        if mode == "risk_adjusted_rescue_window" and eligible and (
            base_score < float(candidate_threshold)
            or (delay_gate_enabled and float(delay_scores[idx]) > float(delay_threshold))
        ):
            rescue_promoted += 1
        predicted.append(int(idx))
    return predicted, blocked, score_blocked, suppressed, rescue_eligible, rescue_promoted


def _record_candidate_decision_counts(
    record: dict[str, Any],
    *,
    candidate_threshold: float,
    gate_config: dict[str, Any] | None = None,
) -> tuple[int, int, int, int, int, int, int]:
    (
        predicted_indices,
        blocked,
        score_blocked,
        suppressed,
        rescue_eligible,
        rescue_promoted,
    ) = _record_candidate_prediction_indices(
        record,
        candidate_threshold=candidate_threshold,
        gate_config=gate_config,
    )
    false_delay = sum(
        int(record["candidate_delay_labels"][idx])
        for idx in predicted_indices
        if idx < len(record["candidate_delay_labels"])
    )
    return (
        len(predicted_indices),
        int(false_delay),
        int(blocked),
        int(score_blocked),
        int(suppressed),
        int(rescue_eligible),
        int(rescue_promoted),
    )


def _record_is_batch_accepted(
    record: dict[str, Any],
    *,
    batch_threshold: float,
    candidate_threshold: float,
    gate_config: dict[str, Any] | None = None,
    batch_thresholds_by_family: dict[str, float] | None = None,
) -> bool:
    if float(record["batch_score"]) < _record_batch_threshold(
        record,
        batch_threshold=batch_threshold,
        batch_thresholds_by_family=batch_thresholds_by_family,
    ):
        return False
    predicted, false_delay, _, _, _, _, _ = _record_candidate_decision_counts(
        record,
        candidate_threshold=candidate_threshold,
        gate_config=gate_config,
    )
    return predicted > 0 and false_delay == 0


def _record_is_delay_fallback(
    record: dict[str, Any],
    *,
    fallback_families: set[str],
    fallback_contexts: set[str],
) -> bool:
    return (
        str(record.get("family") or record.get("instance_family") or "unknown") in fallback_families
        or str(record.get("context_hash") or "") in fallback_contexts
    )


def _family_delay_fallback_threshold_metrics(
    records: list[dict[str, Any]],
    *,
    evaluated: list[dict[str, Any]],
    gate_config: dict[str, Any],
) -> list[dict[str, Any]]:
    fallback_metrics: list[dict[str, Any]] = []
    seen: set[tuple[float, float, tuple[tuple[str, float], ...], tuple[str, ...]]] = set()
    min_family_roi = float(gate_config["min_family_holdout_accepted_roi"])
    for metrics in evaluated:
        fallback_families = _low_roi_fallback_families(
            metrics,
            min_family_roi=min_family_roi,
        )
        fallback_contexts = _low_roi_fallback_contexts(
            records,
            metrics,
            min_context_roi=min_family_roi,
        )
        fallback_options: list[tuple[list[str], list[str]]] = []
        if fallback_contexts:
            fallback_options.append(([], fallback_contexts))
        if fallback_families:
            fallback_options.append((fallback_families, []))
        if fallback_families and fallback_contexts:
            fallback_options.append((fallback_families, fallback_contexts))
        if not fallback_options:
            continue
        batch_thresholds_by_family = {
            str(key): float(value)
            for key, value in dict(metrics.get("batch_thresholds_by_family") or {}).items()
        }
        for fallback_families, fallback_contexts in fallback_options:
            key = (
                float(metrics["batch_threshold"]),
                float(metrics["candidate_threshold"]),
                tuple(sorted(batch_thresholds_by_family.items())),
                tuple(fallback_families),
                tuple(fallback_contexts),
            )
            if key in seen:
                continue
            seen.add(key)
            fallback_metrics.append(
                _deployment_metrics(
                    records,
                    batch_threshold=float(metrics["batch_threshold"]),
                    candidate_threshold=float(metrics["candidate_threshold"]),
                    gate_config=gate_config,
                    batch_thresholds_by_family=batch_thresholds_by_family or None,
                    delay_fallback_families=list(fallback_families),
                    context_delay_fallback_contexts=list(fallback_contexts),
                )
            )
    return fallback_metrics


def _low_roi_fallback_families(
    metrics: dict[str, Any],
    *,
    min_family_roi: float,
) -> list[str]:
    per_family = dict(metrics.get("family_holdout_per_family") or {})
    fallback: list[str] = []
    for family, family_metrics in sorted(per_family.items()):
        accepted_count = int(family_metrics.get("accepted_batch_count") or 0)
        accepted_roi = float(family_metrics.get("accepted_batch_roi") or 0.0)
        if accepted_count > 0 and accepted_roi < float(min_family_roi):
            fallback.append(str(family))
    return fallback


def _low_roi_fallback_contexts(
    records: list[dict[str, Any]],
    metrics: dict[str, Any],
    *,
    min_context_roi: float,
) -> list[str]:
    fallback_families = {str(family) for family in (metrics.get("family_delay_fallback_families") or [])}
    fallback_contexts = {str(context) for context in (metrics.get("context_delay_fallback_contexts") or [])}
    batch_thresholds_by_family = {
        str(key): float(value)
        for key, value in dict(metrics.get("batch_thresholds_by_family") or {}).items()
    }
    by_family_context: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for record in records:
        if _record_is_delay_fallback(
            record,
            fallback_families=fallback_families,
            fallback_contexts=fallback_contexts,
        ):
            continue
        if not _record_is_batch_accepted(
            record,
            batch_threshold=float(metrics["batch_threshold"]),
            candidate_threshold=float(metrics["candidate_threshold"]),
            gate_config=metrics,
            batch_thresholds_by_family=batch_thresholds_by_family or None,
        ):
            continue
        context = str(record.get("context_hash") or "")
        if not context:
            continue
        family = str(record.get("family") or record.get("instance_family") or "unknown")
        by_family_context.setdefault(family, {}).setdefault(context, []).append(record)
    fallback: list[str] = []
    for _, contexts in sorted(by_family_context.items()):
        context_summaries: list[tuple[float, str, int, float]] = []
        total_count = 0
        total_roi = 0.0
        for context, context_records in sorted(contexts.items()):
            roi_values = [float(record["accepted_batch_roi_label"]) for record in context_records]
            if not roi_values:
                continue
            count = len(roi_values)
            roi_sum = sum(roi_values)
            total_count += count
            total_roi += roi_sum
            context_summaries.append((roi_sum / float(count), str(context), count, roi_sum))
        if total_count <= 0 or total_roi / float(total_count) >= float(min_context_roi):
            continue
        removed_count = 0
        removed_roi = 0.0
        chosen: list[str] = []
        for _, context, count, roi_sum in sorted(context_summaries):
            remaining_count = total_count - removed_count
            if remaining_count > 0 and (total_roi - removed_roi) / float(remaining_count) >= float(min_context_roi):
                break
            chosen.append(str(context))
            removed_count += int(count)
            removed_roi += float(roi_sum)
        remaining_count = total_count - removed_count
        if remaining_count > 0 and (total_roi - removed_roi) / float(remaining_count) >= float(min_context_roi):
            fallback.extend(chosen)
    return fallback


def _family_local_threshold_metrics(
    records: list[dict[str, Any]],
    *,
    candidate_thresholds: list[float],
    gate_config: dict[str, Any],
) -> list[dict[str, Any]]:
    by_family: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_family.setdefault(str(record.get("family") or "unknown"), []).append(record)
    if len(by_family) <= 1:
        return []

    grid = {0.0, 0.5, 0.65, 0.75, 0.85, 0.9, 0.95, 0.99, 1.0}
    evaluated: list[dict[str, Any]] = []
    for candidate_threshold in candidate_thresholds:
        family_options: dict[str, list[dict[str, Any]]] = {}
        missing_required_family = False
        for family, family_records in sorted(by_family.items()):
            batch_scores = [float(record["batch_score"]) for record in family_records]
            thresholds = _threshold_values(batch_scores, grid=grid, max_dynamic=32)
            options: list[dict[str, Any]] = []
            seen_accept_sets: set[tuple[str, ...]] = set()
            for threshold in thresholds:
                metrics = _deployment_metrics(
                    family_records,
                    batch_threshold=float(threshold),
                    candidate_threshold=float(candidate_threshold),
                    gate_config=gate_config,
                )
                accepted_contexts = tuple(
                    sorted(
                        str(record.get("context_hash") or "")
                        for record in family_records
                        if _record_is_batch_accepted(
                            record,
                            batch_threshold=float(threshold),
                            candidate_threshold=float(candidate_threshold),
                            gate_config=gate_config,
                        )
                    )
                )
                if accepted_contexts in seen_accept_sets:
                    continue
                seen_accept_sets.add(accepted_contexts)
                if int(metrics["accepted_batch_count"]) <= 0:
                    continue
                if metrics["safe_precision"] is None or float(metrics["safe_precision"]) < float(
                    gate_config["min_family_holdout_precision"]
                ):
                    continue
                if float(metrics["accepted_batch_roi"]) < float(
                    gate_config["min_family_holdout_accepted_roi"]
                ):
                    continue
                if float(metrics["false_high_priority_on_delay"]) > float(
                    gate_config["max_false_high_priority_on_delay"]
                ):
                    continue
                options.append(
                    {
                        "family": family,
                        "batch_threshold": float(threshold),
                        "accepted_batch_count": int(metrics["accepted_batch_count"]),
                        "accepted_batch_roi": float(metrics["accepted_batch_roi"]),
                        "accepted_batch_roi_ci_low": metrics.get("accepted_batch_roi_ci_low"),
                        "accepted_batch_roi_over_baseline": float(
                            metrics.get("accepted_batch_roi_over_baseline") or 0.0
                        ),
                        "accepted_batch_roi_over_baseline_ci_low": metrics.get(
                            "accepted_batch_roi_over_baseline_ci_low"
                        ),
                        "safe_precision": float(metrics["safe_precision"]),
                        "expected_trajectory_utility": float(metrics["expected_trajectory_utility"]),
                    }
                )
            options.sort(
                key=lambda item: (
                    _metric_float(item.get("accepted_batch_roi_ci_low")),
                    _metric_float(item.get("accepted_batch_roi_over_baseline_ci_low")),
                    _metric_float(item.get("accepted_batch_roi_over_baseline")),
                    float(item["expected_trajectory_utility"]),
                    float(item["accepted_batch_roi"]),
                    int(item["accepted_batch_count"]),
                    -float(item["batch_threshold"]),
                ),
                reverse=True,
            )
            if options:
                family_options[family] = options[:12]
            elif _family_oracle_high_roi_count(
                family_records,
                min_accepted_batch_roi=float(gate_config["min_family_holdout_accepted_roi"]),
            ) > 0:
                missing_required_family = True
                break
        if missing_required_family or not family_options:
            continue
        for combo in _limited_family_threshold_products(family_options):
            thresholds_by_family = {
                str(item["family"]): float(item["batch_threshold"]) for item in combo
            }
            evaluated.append(
                _deployment_metrics(
                    records,
                    batch_threshold=max(thresholds_by_family.values()),
                    candidate_threshold=float(candidate_threshold),
                    gate_config=gate_config,
                    batch_thresholds_by_family=thresholds_by_family,
                )
            )
    return evaluated


def _limited_family_threshold_products(
    family_options: dict[str, list[dict[str, Any]]],
    *,
    max_products: int = 4096,
) -> list[tuple[dict[str, Any], ...]]:
    families = sorted(family_options)
    products: list[tuple[dict[str, Any], ...]] = [()]
    for family in families:
        next_products: list[tuple[dict[str, Any], ...]] = []
        for prefix in products:
            for option in family_options[family]:
                next_products.append((*prefix, option))
        next_products.sort(
            key=lambda combo: (
                sum(_metric_float(item.get("accepted_batch_roi_ci_low")) for item in combo),
                sum(_metric_float(item.get("accepted_batch_roi_over_baseline_ci_low")) for item in combo),
                sum(_metric_float(item.get("accepted_batch_roi_over_baseline")) for item in combo),
                sum(float(item["expected_trajectory_utility"]) for item in combo),
                sum(float(item["accepted_batch_roi"]) for item in combo),
                -sum(int(item["accepted_batch_count"]) for item in combo),
            ),
            reverse=True,
        )
        products = next_products[: int(max_products)]
    return products


def _checkpoint_gate_reject_reasons(metrics: dict[str, Any], *, gate_config: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if metrics["high_priority_precision"] is None or float(metrics["high_priority_precision"]) < float(
        gate_config["min_high_priority_precision"]
    ):
        reasons.append("high_priority_precision_below_threshold_or_no_predictions")
    hp_ci_low = metrics.get("high_priority_precision_ci_low")
    min_hp_ci_low = gate_config.get("min_high_priority_precision_ci_low")
    if min_hp_ci_low is not None:
        if hp_ci_low is None or float(hp_ci_low) < float(min_hp_ci_low):
            reasons.append("high_priority_precision_ci_low_below_threshold_or_not_measurable")
    if metrics["safe_precision"] is None or float(metrics["safe_precision"]) < float(gate_config["min_safe_precision"]):
        reasons.append("safe_precision_below_threshold_or_no_accepted_batches")
    safe_ci_low = metrics.get("safe_precision_ci_low")
    min_safe_ci_low = gate_config.get("min_safe_precision_ci_low")
    if min_safe_ci_low is not None:
        if safe_ci_low is None or float(safe_ci_low) < float(min_safe_ci_low):
            reasons.append("safe_precision_ci_low_below_threshold_or_not_measurable")
    if int(metrics["accepted_batch_count"]) < int(gate_config["min_accepted_batch_count"]):
        reasons.append("accepted_batch_count_too_low")
    if float(metrics["accepted_batch_rate"]) < float(gate_config["min_accepted_batch_rate"]):
        reasons.append("accepted_batch_rate_too_low")
    if int(metrics.get("accepted_bad_mode_count", 0)) > int(
        gate_config.get("max_accepted_bad_mode_count", 0)
    ):
        reasons.append("accepted_bad_mode_count_above_limit")
    if float(metrics["accepted_batch_roi"]) < float(gate_config["min_accepted_batch_roi"]):
        reasons.append("accepted_batch_roi_below_baseline_margin")
    roi_ci_low = metrics.get("accepted_batch_roi_ci_low")
    min_roi_ci_low = gate_config.get("min_accepted_batch_roi_ci_low")
    if min_roi_ci_low is not None:
        if roi_ci_low is None or float(roi_ci_low) < float(min_roi_ci_low):
            reasons.append("accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable")
    if float(metrics["expected_trajectory_utility"]) <= 0.0:
        reasons.append("expected_trajectory_utility_not_positive")
    if bool(gate_config.get("require_positive_candidate_threshold", True)):
        candidate_threshold = float(metrics.get("candidate_threshold", 0.0) or 0.0)
        evaluated_candidates = int(metrics.get("evaluated_candidate_count", 0) or 0)
        if candidate_threshold <= 0.0 and evaluated_candidates > 0:
            reasons.append("candidate_threshold_zero_disables_candidate_head_filter")
    if float(metrics["false_high_priority_on_delay"]) > float(gate_config["max_false_high_priority_on_delay"]):
        reasons.append("false_high_priority_on_delay_too_high")
    if float(metrics["false_safe_rate_union"]) > float(gate_config["max_false_safe_union_rate"]):
        reasons.append("false_safe_rate_union_too_high")
    if int(gate_config["observed_family_count"]) < int(gate_config["min_major_families"]):
        reasons.append("major_family_coverage_incomplete")
    if metrics.get("family_holdout_missing_accepted_opportunity_families"):
        reasons.append("family_holdout_accepted_batch_missing")
    min_family_high_roi_count = int(gate_config.get("min_family_accepted_high_roi_count", 0) or 0)
    if min_family_high_roi_count > 0:
        observed_min_count = metrics.get("family_holdout_min_accepted_high_roi_count")
        if observed_min_count is None or int(observed_min_count) < min_family_high_roi_count:
            reasons.append("family_accepted_high_roi_count_below_threshold")
    min_family_capture_rate = float(gate_config.get("min_family_high_roi_capture_rate", 0.0) or 0.0)
    if min_family_capture_rate > 0.0:
        observed_min_rate = metrics.get("family_holdout_min_high_roi_capture_rate")
        if observed_min_rate is None or float(observed_min_rate) < min_family_capture_rate:
            reasons.append("family_high_roi_capture_rate_below_threshold")
    if metrics["family_holdout_min_precision"] is None:
        reasons.append("family_holdout_precision_not_measurable")
    elif float(metrics["family_holdout_min_precision"]) < float(gate_config["min_family_holdout_precision"]):
        reasons.append("family_holdout_precision_below_threshold")
    if metrics["family_holdout_min_accepted_roi"] is None:
        reasons.append("family_holdout_accepted_roi_not_measurable")
    elif float(metrics["family_holdout_min_accepted_roi"]) < float(gate_config["min_family_holdout_accepted_roi"]):
        reasons.append("family_holdout_accepted_roi_below_threshold")
    if int(gate_config["actual_sample_count"]) < int(gate_config["stage3_min_samples"]):
        reasons.append("stage3_effective_sample_count_below_200")
    if not bool(gate_config["knn_ood_audit_completed"]):
        reasons.append("knn_ood_audit_missing")
    return reasons


def _threshold_local_reject_reasons(reject_reasons: list[str]) -> list[str]:
    external_audit_reasons = {"knn_ood_audit_missing"}
    return [reason for reason in reject_reasons if reason not in external_audit_reasons]


def _hard_reject_reason_categories(reject_reasons: list[str]) -> list[str]:
    categories: set[str] = set()
    for reason in reject_reasons:
        reason_text = str(reason)
        if "precision_ci_low" in reason_text:
            categories.add("precision_ci_below_gate")
        if "precision_below" in reason_text or "precision_not_measurable" in reason_text:
            categories.add("precision_below_gate")
        if reason_text == "accepted_batch_roi_below_baseline_margin":
            categories.add("roi_below_baseline")
        if "accepted_batch_roi_ci_low" in reason_text:
            categories.add("roi_ci_below_baseline")
        if reason_text in {"accepted_batch_count_too_low", "accepted_batch_rate_too_low"}:
            categories.add("zero_accepted_coverage")
        if reason_text == "accepted_bad_mode_count_above_limit":
            categories.add("accepted_bad_mode")
        if reason_text == "false_safe_rate_union_too_high":
            categories.add("false_safe_too_high")
        if reason_text == "false_high_priority_on_delay_too_high":
            categories.add("false_high_priority_on_delay_too_high")
        if (
            reason_text.startswith("family_holdout")
            or reason_text.startswith("family_accepted_high_roi")
            or reason_text.startswith("family_high_roi_capture")
            or reason_text == "major_family_coverage_incomplete"
        ):
            categories.add("holdout_family_collapse")
        if reason_text == "expected_trajectory_utility_not_positive":
            categories.add("trajectory_utility_not_positive")
        if reason_text == "candidate_threshold_zero_disables_candidate_head_filter":
            categories.add("candidate_head_filter_inactive")
        if reason_text == "stage3_effective_sample_count_below_200":
            categories.add("sample_count_below_gate")
        if reason_text == "knn_ood_audit_missing":
            categories.add("knn_ood_audit_missing")
        if reason_text == "nonfinite_training_update_rate_too_high":
            categories.add("training_stability_failed")
        if (
            reason_text == "focused_pair_gate_not_run"
            or reason_text == "not_enough_focused_positive_negative_pairs"
            or reason_text.endswith("_pair_pass_rate_below_threshold")
        ):
            categories.add("focused_pair_gate_failed")
    return sorted(categories)


def _family_holdout_metrics(
    records: list[dict[str, Any]],
    *,
    batch_threshold: float,
    candidate_threshold: float,
    gate_config: dict[str, Any] | None = None,
    batch_thresholds_by_family: dict[str, float] | None = None,
    delay_fallback_families: list[str] | None = None,
    context_delay_fallback_contexts: list[str] | None = None,
    min_accepted_batch_roi: float | None = None,
) -> dict[str, Any]:
    by_family: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_family.setdefault(str(record["family"]), []).append(record)
    per_family: dict[str, dict[str, Any]] = {}
    precision_values: list[float] = []
    roi_values: list[float] = []
    accepted_high_roi_count_values: list[int] = []
    high_roi_capture_rate_values: list[float] = []
    missing_accepted_families: list[str] = []
    missing_accepted_opportunity_families: list[str] = []
    delay_fallback_family_names: list[str] = []
    oracle_high_roi_families: list[str] = []
    min_roi = float(min_accepted_batch_roi) if min_accepted_batch_roi is not None else None
    configured_delay_fallback = {str(family) for family in (delay_fallback_families or [])}
    configured_context_fallback = {str(context) for context in (context_delay_fallback_contexts or [])}
    for family, family_records in sorted(by_family.items()):
        metrics = _deployment_metrics_without_family(
            family_records,
            batch_threshold=batch_threshold,
            candidate_threshold=candidate_threshold,
            gate_config=gate_config,
            batch_thresholds_by_family=batch_thresholds_by_family,
            delay_fallback_families=sorted(configured_delay_fallback),
            context_delay_fallback_contexts=sorted(configured_context_fallback),
        )
        oracle_high_roi_count = (
            _family_oracle_high_roi_count(
                family_records,
                min_accepted_batch_roi=float(min_roi),
            )
            if min_roi is not None
            else 0
        )
        accepted_high_roi_count = (
            _family_accepted_high_roi_count(
                family_records,
                batch_threshold=batch_threshold,
                candidate_threshold=candidate_threshold,
                gate_config=gate_config,
                batch_thresholds_by_family=batch_thresholds_by_family,
                delay_fallback_families=sorted(configured_delay_fallback),
                context_delay_fallback_contexts=sorted(configured_context_fallback),
                min_accepted_batch_roi=float(min_roi),
            )
            if min_roi is not None
            else 0
        )
        high_roi_capture_rate = (
            float(accepted_high_roi_count) / float(oracle_high_roi_count)
            if int(oracle_high_roi_count) > 0
            else None
        )
        max_roi_label = max(
            (float(record["accepted_batch_roi_label"]) for record in family_records),
            default=0.0,
        )
        metrics["oracle_high_roi_count"] = int(oracle_high_roi_count)
        metrics["accepted_high_roi_count"] = int(accepted_high_roi_count)
        metrics["high_roi_capture_rate"] = high_roi_capture_rate
        metrics["max_accepted_batch_roi_label"] = float(max_roi_label)
        per_family[family] = metrics
        if int(oracle_high_roi_count) > 0:
            oracle_high_roi_families.append(str(family))
            accepted_high_roi_count_values.append(int(accepted_high_roi_count))
            high_roi_capture_rate_values.append(float(high_roi_capture_rate or 0.0))
        if metrics["safe_precision"] is not None:
            precision_values.append(float(metrics["safe_precision"]))
        if str(family) in configured_delay_fallback:
            missing_accepted_families.append(str(family))
            delay_fallback_family_names.append(str(family))
        elif metrics["accepted_batch_count"] > 0:
            roi_values.append(float(metrics["accepted_batch_roi"]))
        else:
            missing_accepted_families.append(str(family))
            if int(oracle_high_roi_count) > 0:
                missing_accepted_opportunity_families.append(str(family))
            else:
                delay_fallback_family_names.append(str(family))
    return {
        "family_count": len(by_family),
        "per_family": per_family,
        "family_holdout_measured_family_count": len(by_family) - len(missing_accepted_families),
        "family_holdout_per_family": per_family,
        "family_holdout_missing_accepted_families": missing_accepted_families,
        "family_holdout_missing_accepted_opportunity_families": missing_accepted_opportunity_families,
        "family_specific_delay_fallback_families": delay_fallback_family_names,
        "family_holdout_oracle_high_roi_families": oracle_high_roi_families,
        "family_holdout_min_precision": min(precision_values) if precision_values else None,
        "family_holdout_min_accepted_roi": min(roi_values) if roi_values else None,
        "family_holdout_min_accepted_high_roi_count": (
            min(accepted_high_roi_count_values) if accepted_high_roi_count_values else None
        ),
        "family_holdout_min_high_roi_capture_rate": (
            min(high_roi_capture_rate_values) if high_roi_capture_rate_values else None
        ),
    }


def _family_oracle_high_roi_count(
    records: list[dict[str, Any]],
    *,
    min_accepted_batch_roi: float,
) -> int:
    return sum(
        1
        for record in records
        if float(record["accepted_batch_roi_label"]) >= float(min_accepted_batch_roi)
        and int(record["bad_mode_switch"]) == 0
    )


def _family_accepted_high_roi_count(
    records: list[dict[str, Any]],
    *,
    batch_threshold: float,
    candidate_threshold: float,
    gate_config: dict[str, Any] | None = None,
    batch_thresholds_by_family: dict[str, float] | None = None,
    delay_fallback_families: list[str] | None = None,
    context_delay_fallback_contexts: list[str] | None = None,
    min_accepted_batch_roi: float,
) -> int:
    fallback_families = {str(family) for family in (delay_fallback_families or [])}
    fallback_contexts = {str(context) for context in (context_delay_fallback_contexts or [])}
    return sum(
        1
        for record in records
        if not _record_is_delay_fallback(
            record,
            fallback_families=fallback_families,
            fallback_contexts=fallback_contexts,
        )
        if _record_is_batch_accepted(
            record,
            batch_threshold=batch_threshold,
            candidate_threshold=candidate_threshold,
            gate_config=gate_config,
            batch_thresholds_by_family=batch_thresholds_by_family,
        )
        if float(record["accepted_batch_roi_label"]) >= float(min_accepted_batch_roi)
        and int(record["bad_mode_switch"]) == 0
    )


def _deployment_metrics_without_family(
    records: list[dict[str, Any]],
    *,
    batch_threshold: float,
    candidate_threshold: float,
    gate_config: dict[str, Any] | None = None,
    batch_thresholds_by_family: dict[str, float] | None = None,
    delay_fallback_families: list[str] | None = None,
    context_delay_fallback_contexts: list[str] | None = None,
) -> dict[str, Any]:
    fallback_families = {str(family) for family in (delay_fallback_families or [])}
    fallback_contexts = {str(context) for context in (context_delay_fallback_contexts or [])}
    accepted = [
        record
        for record in records
        if not _record_is_delay_fallback(
            record,
            fallback_families=fallback_families,
            fallback_contexts=fallback_contexts,
        )
        if _record_is_batch_accepted(
            record,
            batch_threshold=batch_threshold,
            candidate_threshold=candidate_threshold,
            gate_config=gate_config,
            batch_thresholds_by_family=batch_thresholds_by_family,
        )
    ]
    accepted_count = len(accepted)
    accepted_positive = sum(int(record["batch_roi_positive"]) for record in accepted)
    precision = None if accepted_count <= 0 else accepted_positive / float(accepted_count)
    roi_values = [float(record["accepted_batch_roi_label"]) for record in accepted]
    return {
        "total_batches": len(records),
        "accepted_batch_count": accepted_count,
        "safe_precision": precision,
        "accepted_batch_roi": sum(roi_values) / float(len(roi_values)) if roi_values else 0.0,
    }


def _stage4_blockers(
    validation_metrics: dict[str, Any],
    family_holdout_metrics: dict[str, Any],
    *,
    manifest: dict[str, Any],
    training_stability_reject_reasons: list[str],
) -> list[str]:
    blockers = list(validation_metrics.get("checkpoint_gate_reject_reasons", []))
    blockers.extend(training_stability_reject_reasons)
    if len(dict(manifest.get("family_counts") or {})) < 2:
        blockers.append("stage2_family_coverage_missing_random_wave_or_greedy_anchor")
    if family_holdout_metrics.get("family_holdout_min_precision") is None:
        blockers.append("family_holdout_precision_not_measurable")
    min_family_high_roi_count = int(validation_metrics.get("min_family_accepted_high_roi_count", 0) or 0)
    if min_family_high_roi_count > 0:
        observed_min_count = family_holdout_metrics.get("family_holdout_min_accepted_high_roi_count")
        if observed_min_count is None or int(observed_min_count) < min_family_high_roi_count:
            blockers.append("family_accepted_high_roi_count_below_threshold")
    min_family_capture_rate = float(validation_metrics.get("min_family_high_roi_capture_rate", 0.0) or 0.0)
    if min_family_capture_rate > 0.0:
        observed_min_rate = family_holdout_metrics.get("family_holdout_min_high_roi_capture_rate")
        if observed_min_rate is None or float(observed_min_rate) < min_family_capture_rate:
            blockers.append("family_high_roi_capture_rate_below_threshold")
    blockers.append("knn_ood_holdout_audit_not_run")
    blockers.append("online_shadow_and_opt_in_ab_not_run")
    return sorted(set(blockers))


def _training_stability_reject_reasons(
    *,
    nonfinite_skipped_update_rate: float,
    max_nonfinite_skipped_update_rate: float,
) -> list[str]:
    if float(nonfinite_skipped_update_rate) > float(max_nonfinite_skipped_update_rate):
        return ["nonfinite_training_update_rate_too_high"]
    return []


def _selected_checkpoint_reason(
    validation_metrics: dict[str, Any],
    *,
    best_epoch: int,
    best_loss_epoch: int,
) -> str:
    local_gate = bool(validation_metrics.get("threshold_local_gate_pass"))
    if local_gate and int(best_epoch) == int(best_loss_epoch):
        return "local_deployment_gate_passed_roi_ci_baseline_then_validation_loss_tiebreaker"
    if local_gate:
        return "local_deployment_gate_passed_then_ranked_by_roi_ci_baseline_utility_loss"
    return "no_local_deployment_gate_passed_selected_best_diagnostic_by_reject_reasons_precision_roi_ci"


def _rejected_checkpoint_reasons(
    validation_metrics: dict[str, Any],
    *,
    training_stability_reject_reasons: list[str],
    focused_pair_gate_reject_reasons: list[str] | None = None,
) -> list[str]:
    reasons = list(validation_metrics.get("checkpoint_gate_reject_reasons", []))
    reasons.extend(training_stability_reject_reasons)
    reasons.extend(list(focused_pair_gate_reject_reasons or []))
    return sorted(set(str(reason) for reason in reasons))


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Batch Impact Training 报告",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "训练 offline batch-impact GAT checkpoint，目标是 high-precision / high-ROI",
        "admission scheduling，而不是普通分类 F1。该训练不运行 BPC / pricing / RMP，",
        "不生成 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_batch_impact_training = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"sample_count = {summary['sample_count']}",
        f"candidate_count = {summary['candidate_count']}",
        f"family_counts = {summary['family_counts']}",
        f"task_count_counts = {summary['task_count_counts']}",
        f"training_objective = {summary['training_objective']}",
        f"training_run_config = {summary['training_run_config']}",
        f"hard_roi_threshold = {summary['hard_roi_threshold']}",
        "candidate_delay_gate_enabled = "
        f"{str(summary['validation_deployment_metrics'].get('candidate_delay_gate_enabled', False)).lower()}",
        "candidate_delay_risk_threshold = "
        f"{summary['validation_deployment_metrics'].get('candidate_delay_risk_threshold')}",
        "candidate_admission_score_mode = "
        f"{summary['validation_deployment_metrics'].get('candidate_admission_score_mode')}",
        "candidate_delay_score_penalty = "
        f"{summary['validation_deployment_metrics'].get('candidate_delay_score_penalty')}",
        "candidate_rescue_raw_score_threshold = "
        f"{summary['validation_deployment_metrics'].get('candidate_rescue_raw_score_threshold')}",
        "candidate_rescue_delay_risk_threshold = "
        f"{summary['validation_deployment_metrics'].get('candidate_rescue_delay_risk_threshold')}",
        "candidate_rescue_delay_score_penalty = "
        f"{summary['validation_deployment_metrics'].get('candidate_rescue_delay_score_penalty')}",
        f"loss_options = {summary['loss_options']}",
        f"pairwise_ranking_loss_active = {str(summary['pairwise_ranking_loss_active']).lower()}",
        "pairwise_candidate_ranking_loss_multiplier = "
        f"{summary['loss_options']['pairwise_candidate_ranking_loss_multiplier']}",
        "pairwise_false_delay_contrast_loss_multiplier = "
        f"{summary['loss_options']['pairwise_false_delay_contrast_loss_multiplier']}",
        "pairwise_delay_risk_contrast_loss_multiplier = "
        f"{summary['loss_options']['pairwise_delay_risk_contrast_loss_multiplier']}",
        "focused_pair_loss_multiplier = "
        f"{summary['loss_options']['focused_pair_loss_multiplier']}",
        "focused_pair_candidate_loss_multiplier = "
        f"{summary['loss_options']['focused_pair_candidate_loss_multiplier']}",
        "focused_pair_admission_loss_multiplier = "
        f"{summary['loss_options']['focused_pair_admission_loss_multiplier']}",
        "focused_pair_delay_risk_loss_multiplier = "
        f"{summary['loss_options']['focused_pair_delay_risk_loss_multiplier']}",
        "focused_pair_batch_loss_multiplier = "
        f"{summary['loss_options']['focused_pair_batch_loss_multiplier']}",
        "focused_pair_row_index_min = "
        f"{summary['loss_options'].get('focused_pair_row_index_min')}",
        "focused_pair_row_indices_file = "
        f"{summary['loss_options'].get('focused_pair_row_indices_file')}",
        "focused_pair_row_indices_count = "
        f"{len(summary['loss_options'].get('focused_pair_row_indices') or [])}",
        f"pairwise_ranking_status = {summary['pairwise_ranking_status']}",
        f"context_pair_stats = {summary['context_pair_stats']}",
        "focused_pair_gate_active = "
        f"{str(summary['focused_pair_gate'].get('active', False)).lower()}",
        "focused_pair_gate_summary = "
        f"{summary['focused_pair_gate'].get('summary')}",
        "focused_pair_gate_reject_reasons = "
        f"{summary['focused_pair_gate_reject_reasons']}",
        f"checkpoint_selection = {summary['checkpoint_selection']}",
        f"selected_checkpoint_reason = {summary['selected_checkpoint_reason']}",
        f"rejected_checkpoint_reasons = {summary['rejected_checkpoint_reasons']}",
        f"rejected_checkpoint_reason_categories = {summary['rejected_checkpoint_reason_categories']}",
        f"best_epoch = {summary['best_epoch']}",
        f"selected_validation_loss = {summary['selected_validation_loss']}",
        f"best_loss_epoch = {summary['best_loss_epoch']}",
        f"best_validation_loss = {summary['best_validation_loss']}",
        f"best_loss_epoch_gate_pass = {str(summary['best_loss_epoch_gate_pass']).lower()}",
        f"checkpoint_gate_pass = {str(summary['checkpoint_gate_pass']).lower()}",
        f"stage4_candidate_ready = {str(summary['stage4_candidate_ready']).lower()}",
        f"stage4_blockers = {summary['stage4_blockers']}",
        f"attempted_update_count = {summary['attempted_update_count']}",
        f"nonfinite_skipped_update_count = {summary['nonfinite_skipped_update_count']}",
        f"nonfinite_skipped_update_rate = {summary['nonfinite_skipped_update_rate']}",
        f"training_stability_reject_reasons = {summary['training_stability_reject_reasons']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## Deployment Metrics",
        "",
        "```json",
        json.dumps(
            {
                "validation_deployment_metrics": summary["validation_deployment_metrics"],
                "train_deployment_metrics": summary["train_deployment_metrics"],
                "family_holdout_metrics": summary["family_holdout_metrics"],
                "focused_pair_gate": summary["focused_pair_gate"],
                "threshold_search": summary["threshold_search"],
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
        "- checkpoint selection 先看 deployment gate，再看 utility / ROI / loss；",
        "- HIGH_PRIORITY precision、safe precision、accepted batch ROI、false-safe、accepted count 都是硬门槛；",
        "- 当前 checkpoint 仍 `production_ready=false`；",
        "- kNN/OOD holdout、5/10 no-regression、20-task wall-time ROI、online opt-in A/B 通过前，不能进入 Stage 4；",
        "- DELAY_QUEUE 只能延迟 true-RC negative，不能替代 final exact pricing certificate。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
