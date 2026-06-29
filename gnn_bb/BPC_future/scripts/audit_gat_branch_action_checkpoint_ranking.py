#!/usr/bin/env python3
"""Audit branch/action checkpoint ranking quality on an offline dataset.

This diagnostic only scores saved GAT branch/action samples.  It does not run
BPC, pricing, RMP, branch-and-bound, or any certificate logic.  The output is
intended to decide whether a checkpoint has enough context-local ranking signal
to justify a later score-map export smoke test.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from BPC_future.learning.branch_impact_model import GATBranchImpactModel
from BPC_future.scripts.train_gat_branch_action_sanity import _split_items


DEFAULT_DATASET_DIR = Path(
    "BPC_future/data/gat_branch_action_sanity/v658_all_counterfactual_delta_rows_20260628"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_branch_action_v660_v658_v659_checkpoint_ranking_20260628"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260628_bpc_future_gat_branch_action_v660_v658_v659_checkpoint_ranking_zh.md"
)


@dataclass(frozen=True)
class RunSpec:
    name: str
    checkpoint: Path
    summary: Path | None
    seed: int


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_sample(path: Path) -> Any:
    return torch.load(path, map_location="cpu", weights_only=False)


def _infer_seed(*texts: str) -> int:
    for text in texts:
        match = re.search(r"seed(\d+)", text)
        if match:
            return int(match.group(1))
    return 244


def parse_run_spec(value: str) -> RunSpec:
    parts = value.split(":")
    if len(parts) not in (2, 3, 4):
        raise argparse.ArgumentTypeError(
            "--run must be name:checkpoint[:summary[:seed]]"
        )
    name = parts[0]
    checkpoint = Path(parts[1])
    summary = Path(parts[2]) if len(parts) >= 3 and parts[2] else None
    seed = int(parts[3]) if len(parts) == 4 and parts[3] else _infer_seed(name, str(checkpoint), str(summary or ""))
    if not name:
        raise argparse.ArgumentTypeError("run name must not be empty")
    return RunSpec(name=name, checkpoint=checkpoint, summary=summary, seed=seed)


def _context_key(item: dict[str, Any]) -> str:
    return "|".join(
        [
            str(item.get("instance") or ""),
            str(item.get("node_id") if item.get("node_id") is not None else ""),
            str(item.get("depth") if item.get("depth") is not None else ""),
            json.dumps(item.get("baseline_pair"), sort_keys=True),
        ]
    )


def _float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    if not math.isfinite(result):
        return float(default)
    return result


def _binary_roc_auc(labels: list[int], scores: list[float]) -> float | None:
    positives = [score for label, score in zip(labels, scores) if label == 1]
    negatives = [score for label, score in zip(labels, scores) if label == 0]
    if not positives or not negatives:
        return None
    wins = 0.0
    total = 0
    for pos_score in positives:
        for neg_score in negatives:
            total += 1
            if pos_score > neg_score:
                wins += 1.0
            elif pos_score == neg_score:
                wins += 0.5
    return wins / float(total) if total else None


def _average_precision(labels: list[int], scores: list[float]) -> float | None:
    positive_count = sum(1 for label in labels if label == 1)
    if positive_count <= 0:
        return None
    ranked = sorted(zip(scores, labels), key=lambda row: row[0], reverse=True)
    hit_count = 0
    precision_sum = 0.0
    for rank, (_score, label) in enumerate(ranked, start=1):
        if label != 1:
            continue
        hit_count += 1
        precision_sum += hit_count / float(rank)
    return precision_sum / float(positive_count)


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x = sum(xs) / float(len(xs))
    mean_y = sum(ys) / float(len(ys))
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    denom = denom_x * denom_y
    if denom <= 0.0:
        return None
    return numerator / denom


def _topk_metrics(labels: list[int], scores: list[float], ks: tuple[int, ...] = (1, 5, 10, 20)) -> dict[str, float]:
    ranked = sorted(zip(scores, labels), key=lambda row: row[0], reverse=True)
    positives = sum(1 for label in labels if label == 1)
    metrics: dict[str, float] = {}
    for k in ks:
        selected = ranked[: min(k, len(ranked))]
        hit = sum(1 for _score, label in selected if label == 1)
        denom = len(selected)
        metrics[f"top{k}_precision"] = hit / float(denom) if denom else 0.0
        metrics[f"top{k}_recall"] = hit / float(positives) if positives else 0.0
    return metrics


def _global_metrics(rows: list[dict[str, Any]], score_field: str) -> dict[str, Any]:
    active = [row for row in rows if row["branch_priority_loss_weight"] > 0.0]
    labels = [int(row["label"]) for row in active]
    scores = [_float(row.get(score_field)) for row in active]
    walltime_gains = [_float(row.get("walltime_gain")) for row in active]
    positives = sum(labels)
    negatives = len(labels) - positives
    metrics: dict[str, Any] = {
        "row_count": len(active),
        "positive_count": positives,
        "negative_count": negatives,
        "roc_auc": _binary_roc_auc(labels, scores),
        "average_precision": _average_precision(labels, scores),
        "score_walltime_gain_pearson": _pearson(scores, walltime_gains),
        "mean_score_positive": (
            sum(score for label, score in zip(labels, scores) if label == 1) / float(positives)
            if positives
            else None
        ),
        "mean_score_negative": (
            sum(score for label, score in zip(labels, scores) if label == 0) / float(negatives)
            if negatives
            else None
        ),
    }
    metrics.update(_topk_metrics(labels, scores))
    return metrics


def _group_ranking_metrics(rows: list[dict[str, Any]], score_field: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["branch_priority_loss_weight"] > 0.0:
            groups[row["context_key"]].append(row)

    comparable = [
        group
        for group in groups.values()
        if len(group) >= 2
        and any(row["label"] == 1 for row in group)
        and any(row["label"] == 0 for row in group)
    ]
    pair_count = 0
    pair_score = 0.0
    top1_hits = 0
    top2_hits = 0
    top3_hits = 0
    reciprocal_sum = 0.0
    positive_rank_sum = 0.0
    best_positive_rank_rows: list[dict[str, Any]] = []
    for group in comparable:
        positives = [row for row in group if row["label"] == 1]
        negatives = [row for row in group if row["label"] == 0]
        for positive in positives:
            for negative in negatives:
                pair_count += 1
                pos_score = _float(positive.get(score_field))
                neg_score = _float(negative.get(score_field))
                if pos_score > neg_score:
                    pair_score += 1.0
                elif pos_score == neg_score:
                    pair_score += 0.5
        ranked = sorted(group, key=lambda row: _float(row.get(score_field)), reverse=True)
        labels = [int(row["label"]) for row in ranked]
        if labels and labels[0] == 1:
            top1_hits += 1
        if any(label == 1 for label in labels[:2]):
            top2_hits += 1
        if any(label == 1 for label in labels[:3]):
            top3_hits += 1
        best_rank = next((index + 1 for index, label in enumerate(labels) if label == 1), None)
        if best_rank is not None:
            reciprocal_sum += 1.0 / float(best_rank)
            positive_rank_sum += float(best_rank)
            best_positive_rank_rows.append(
                {
                    "context_key": ranked[0]["context_key"],
                    "best_positive_rank": best_rank,
                    "group_size": len(ranked),
                    "top_score": _float(ranked[0].get(score_field)),
                    "top_label": int(ranked[0]["label"]),
                    "best_positive_score": _float(ranked[best_rank - 1].get(score_field)),
                }
            )
    comparable_count = len(comparable)
    return {
        "context_count": len(groups),
        "comparable_context_count": comparable_count,
        "pair_count": pair_count,
        "pairwise_accuracy": pair_score / float(pair_count) if pair_count else None,
        "top1_positive_context_rate": top1_hits / float(comparable_count) if comparable_count else None,
        "top2_positive_context_rate": top2_hits / float(comparable_count) if comparable_count else None,
        "top3_positive_context_rate": top3_hits / float(comparable_count) if comparable_count else None,
        "mean_reciprocal_rank": reciprocal_sum / float(comparable_count) if comparable_count else None,
        "mean_best_positive_rank": positive_rank_sum / float(comparable_count) if comparable_count else None,
        "worst_positive_rank_examples": sorted(
            best_positive_rank_rows,
            key=lambda row: (row["best_positive_rank"], row["group_size"]),
            reverse=True,
        )[:10],
    }


def _score_sample(
    model: GATBranchImpactModel,
    sample: Any,
    device: torch.device,
) -> dict[str, float]:
    sample = sample.to(device)
    with torch.no_grad():
        output = model(
            sample,
            sample.branch_pair_indices,
            sample.branch_pair_features,
            sample.context_features,
        )
    return {
        "branch_priority_probability": _float(output["branch_priority_probability"].view(-1)[0].detach().cpu()),
        "branch_priority_logit": _float(output["branch_priority_logit"].view(-1)[0].detach().cpu()),
        "predicted_walltime_gain": _float(output["predicted_walltime_gain"].view(-1)[0].detach().cpu()),
        "tail_improved_probability": _float(output["tail_improved_probability"].view(-1)[0].detach().cpu()),
        "tree_policy_probability": _float(output["tree_policy_probability"].view(-1)[0].detach().cpu()),
    }


def _split_name_sets(
    manifest: dict[str, Any],
    *,
    validation_fraction: float,
    seed: int,
) -> tuple[set[str], set[str]]:
    train_items, validation_items = _split_items(
        manifest,
        validation_fraction=float(validation_fraction),
        seed=int(seed),
    )
    train_paths = {str(item.get("path") or "") for item in train_items}
    validation_paths = {str(item.get("path") or "") for item in validation_items}
    return train_paths, validation_paths


def _assert_offline_contract(checkpoint: dict[str, Any], manifest: dict[str, Any]) -> None:
    exactness = dict(checkpoint.get("exactness_contract") or {})
    if exactness.get("pricing_oracle") or exactness.get("certificate_source") or exactness.get("official_bound_effect"):
        raise SystemExit("checkpoint violates offline exactness contract")
    if not manifest.get("diagnostic_only") or manifest.get("official_bound_effect") or manifest.get("certificate_effect"):
        raise SystemExit("dataset violates diagnostic-only exactness contract")


def audit_checkpoint(
    *,
    run: RunSpec,
    dataset_dir: Path,
    manifest: dict[str, Any],
    validation_fraction: float,
    device: torch.device,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    checkpoint = torch.load(run.checkpoint, map_location="cpu", weights_only=False)
    _assert_offline_contract(checkpoint, manifest)
    model = GATBranchImpactModel(**checkpoint["model_config"]).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    train_paths, validation_paths = _split_name_sets(
        manifest,
        validation_fraction=float(validation_fraction),
        seed=int(run.seed),
    )
    rows: list[dict[str, Any]] = []
    for item in manifest.get("samples", []):
        sample = _load_sample(dataset_dir / item["path"])
        scores = _score_sample(model, sample, device)
        path = str(item.get("path") or "")
        if path in validation_paths:
            split = "validation"
        elif path in train_paths:
            split = "train"
        else:
            split = "unknown"
        row = {
            "run_name": run.name,
            "split": split,
            "path": path,
            "instance": str(item.get("instance") or ""),
            "time_window_family": str(item.get("time_window_family") or ""),
            "context_key": _context_key(item),
            "row_kind": str(item.get("row_kind") or ""),
            "baseline_pair": item.get("baseline_pair"),
            "alternative_pair": item.get("alternative_pair"),
            "branch_priority_label": str(item.get("branch_priority_label") or ""),
            "branch_priority_loss_weight": _float(item.get("branch_priority_loss_weight")),
            "label": 1 if str(item.get("branch_priority_label") or "") == "walltime_gain_positive" else 0,
            "walltime_gain": _float(item.get("walltime_gain")),
            "target_wall_crossing_positive": bool(item.get("target_wall_crossing_positive")),
        }
        row.update(scores)
        rows.append(row)

    score_fields = (
        "branch_priority_probability",
        "predicted_walltime_gain",
        "tail_improved_probability",
        "tree_policy_probability",
    )
    split_summaries: dict[str, Any] = {}
    for split in ("all", "train", "validation"):
        split_rows = rows if split == "all" else [row for row in rows if row["split"] == split]
        split_summaries[split] = {
            "row_count": len(split_rows),
            "active_row_count": sum(1 for row in split_rows if row["branch_priority_loss_weight"] > 0.0),
            "positive_count": sum(
                1
                for row in split_rows
                if row["branch_priority_loss_weight"] > 0.0 and row["label"] == 1
            ),
            "negative_count": sum(
                1
                for row in split_rows
                if row["branch_priority_loss_weight"] > 0.0 and row["label"] == 0
            ),
            "score_field_metrics": {
                field: {
                    "global": _global_metrics(split_rows, field),
                    "context_ranking": _group_ranking_metrics(split_rows, field),
                }
                for field in score_fields
            },
        }
    training_summary = _load_json(run.summary) if run.summary and run.summary.exists() else {}
    summary = {
        "run_name": run.name,
        "checkpoint": str(run.checkpoint),
        "training_summary": str(run.summary) if run.summary else None,
        "seed": int(run.seed),
        "split_summaries": split_summaries,
        "training_threshold_metrics": {
            "train_branch_priority_metrics": training_summary.get("train_branch_priority_metrics"),
            "validation_branch_priority_metrics": training_summary.get("validation_branch_priority_metrics"),
        },
    }
    return summary, rows


def _score_field_gate(run_summary: dict[str, Any], score_field: str) -> dict[str, Any]:
    validation = run_summary["split_summaries"]["validation"]
    score_metrics = validation["score_field_metrics"][score_field]
    global_metrics = score_metrics["global"]
    group_metrics = score_metrics["context_ranking"]
    reasons: list[str] = []
    if validation["positive_count"] < 10:
        reasons.append("validation_positive_count_lt_10")
    if group_metrics.get("comparable_context_count", 0) < 5:
        reasons.append("validation_comparable_context_lt_5")
    if (global_metrics.get("roc_auc") or 0.0) < 0.60:
        reasons.append("validation_auc_lt_0_60")
    if (global_metrics.get("average_precision") or 0.0) < 0.35:
        reasons.append("validation_average_precision_lt_0_35")
    if group_metrics.get("comparable_context_count", 0) <= 0:
        reasons.append("no_validation_comparable_context")
    elif (group_metrics.get("pairwise_accuracy") or 0.0) < 0.60:
        reasons.append("validation_context_pairwise_lt_0_60")
    return {
        "score_field": score_field,
        "score_map_export_recommended": not reasons,
        "reject_reasons": reasons,
    }


def _run_gate(run_summary: dict[str, Any]) -> dict[str, Any]:
    field_gates = {
        field: _score_field_gate(run_summary, field)
        for field in (
            "branch_priority_probability",
            "predicted_walltime_gain",
            "tail_improved_probability",
            "tree_policy_probability",
        )
    }
    passing = [field for field, gate in field_gates.items() if gate["score_map_export_recommended"]]
    best_field = _select_best_score_field(run_summary)
    return {
        "score_map_export_recommended": bool(passing),
        "passing_score_fields": passing,
        "best_validation_score_field": best_field,
        "score_field_gates": field_gates,
        "reject_reasons": [] if passing else field_gates[best_field]["reject_reasons"],
    }


def _select_best_score_field(run_summary: dict[str, Any]) -> str:
    validation = run_summary["split_summaries"]["validation"]

    def key(field: str) -> tuple[float, float, float]:
        metrics = validation["score_field_metrics"][field]
        global_metrics = metrics["global"]
        group_metrics = metrics["context_ranking"]
        return (
            float(global_metrics.get("roc_auc") or -1.0),
            float(group_metrics.get("pairwise_accuracy") or -1.0),
            float(global_metrics.get("average_precision") or -1.0),
        )

    return max(validation["score_field_metrics"], key=key)


def audit_checkpoints(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    runs: list[RunSpec],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    device: str = "cpu",
    validation_fraction: float = 0.25,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    output_dir = Path(output_dir)
    report = Path(report)
    manifest = _load_json(dataset_dir / "manifest.json")
    device_obj = torch.device(str(device))
    output_dir.mkdir(parents=True, exist_ok=True)

    run_summaries: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for run in runs:
        run_summary, rows = audit_checkpoint(
            run=run,
            dataset_dir=dataset_dir,
            manifest=manifest,
            validation_fraction=float(validation_fraction),
            device=device_obj,
        )
        run_summary["gate"] = _run_gate(run_summary)
        run_summaries.append(run_summary)
        all_rows.extend(rows)

    rows_path = output_dir / "scored_branch_action_rows.jsonl"
    with rows_path.open("w", encoding="utf-8") as handle:
        for row in all_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    best_run = _select_best_run(run_summaries)
    summary = {
        "schema_version": "gat_branch_action_checkpoint_ranking_audit_v1",
        "date": date.today().isoformat(),
        "dataset_dir": str(dataset_dir),
        "output_dir": str(output_dir),
        "scored_rows_path": str(rows_path),
        "run_count": len(run_summaries),
        "runs": run_summaries,
        "best_run_by_validation_auc": best_run,
        "best_run_by_validation_branch_auc": best_run,
        "score_map_export_recommended": bool(best_run and best_run["gate"]["score_map_export_recommended"]),
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "solver_default_effect": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "all_checks_pass": True,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _select_best_run(run_summaries: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not run_summaries:
        return None

    def key(summary: dict[str, Any]) -> tuple[float, float, float]:
        field = summary["gate"]["best_validation_score_field"]
        metrics = summary["split_summaries"]["validation"]["score_field_metrics"][field]
        global_metrics = metrics["global"]
        group_metrics = metrics["context_ranking"]
        return (
            float(global_metrics.get("roc_auc") or -1.0),
            float(group_metrics.get("pairwise_accuracy") or -1.0),
            float(global_metrics.get("average_precision") or -1.0),
        )

    best = max(run_summaries, key=key)
    return {
        "run_name": best["run_name"],
        "checkpoint": best["checkpoint"],
        "seed": best["seed"],
        "best_validation_score_field": best["gate"]["best_validation_score_field"],
        "validation_best_score_field_metrics": best["split_summaries"]["validation"][
            "score_field_metrics"
        ][best["gate"]["best_validation_score_field"]],
        "gate": best["gate"],
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _write_report(report: Path, summary: dict[str, Any]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Branch/Action Checkpoint Ranking Audit",
        "",
        f"日期：{summary['date']}",
        "",
        "## 目的",
        "",
        "用 context-local ranking 指标审计 v658/v659 branch/action checkpoint。该审计只读离线 dataset 和 checkpoint，不运行 BPC、pricing、RMP，也不产生 official bound 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"dataset_dir = {summary['dataset_dir']}",
        f"output_dir = {summary['output_dir']}",
        f"run_count = {summary['run_count']}",
        f"score_map_export_recommended = {str(summary['score_map_export_recommended']).lower()}",
        "diagnostic_only = true",
        "runs_bpc_or_pricing = false",
        "official_bound_effect = false",
        "certificate_effect = false",
        "solver_default_effect = false",
        "```",
        "",
        "## Validation Ranking",
        "",
        "| run | pos/neg | branch AUC/AP/pair | walltime AUC/AP/pair | walltime top1 ctx | best field | gate |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for run in summary["runs"]:
        validation = run["split_summaries"]["validation"]
        branch = validation["score_field_metrics"]["branch_priority_probability"]
        branch_global = branch["global"]
        branch_group = branch["context_ranking"]
        walltime = validation["score_field_metrics"]["predicted_walltime_gain"]
        walltime_global = walltime["global"]
        walltime_group = walltime["context_ranking"]
        gate = run["gate"]
        gate_text = "pass" if gate["score_map_export_recommended"] else ",".join(gate["reject_reasons"])
        lines.append(
            "| "
            f"{run['run_name']} | "
            f"{validation['positive_count']}/{validation['negative_count']} | "
            f"{_fmt(branch_global['roc_auc'])}/{_fmt(branch_global['average_precision'])}/"
            f"{_fmt(branch_group['pairwise_accuracy'])} | "
            f"{_fmt(walltime_global['roc_auc'])}/{_fmt(walltime_global['average_precision'])}/"
            f"{_fmt(walltime_group['pairwise_accuracy'])} | "
            f"{_fmt(walltime_group['top1_positive_context_rate'])} | "
            f"{gate['best_validation_score_field']} | "
            f"{gate_text} |"
        )
    best = summary.get("best_run_by_validation_auc") or {}
    lines.extend(
        [
            "",
            "## 判断",
            "",
            f"- best_run_by_validation_branch_auc = {best.get('run_name')}",
            f"- best_validation_score_field = {best.get('best_validation_score_field')}",
            f"- score_map_export_recommended = {str(summary['score_map_export_recommended']).lower()}",
            "- 当前最有用的信号可能来自 wall-time regression head，而不是 0.5 分类阈值；但 validation 可比 context 数仍不足，不能直接上线。",
            "- 若 gate 未通过，checkpoint 只能继续作为离线诊断，不能导出生产 score map，也不能接入 solver 默认行为。",
            "- branch score 仍只允许影响排序/测试对象选择；official bound、certificate 和 fathom 仍必须来自合法 RMP + exact pricing closure。",
        ]
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--validation-fraction", type=float, default=0.25)
    parser.add_argument(
        "--run",
        action="append",
        type=parse_run_spec,
        required=True,
        help="Run spec: name:checkpoint[:summary[:seed]]",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = audit_checkpoints(
        dataset_dir=Path(args.dataset_dir),
        runs=list(args.run),
        output_dir=Path(args.output_dir),
        report=Path(args.report),
        device=str(args.device),
        validation_fraction=float(args.validation_fraction),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
