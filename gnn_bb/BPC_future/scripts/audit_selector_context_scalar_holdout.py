#!/usr/bin/env python3
"""Audit holdout behavior for control-objective selector candidates.

This script is read-only with respect to solver state. It uses exact replay
candidate rows and tests whether addition-before context scalar candidates can
generalize across dataset, instance, and context-hash holdouts.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_context_scalar_holdout_20260613"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_selector_context_scalar_holdout_zh.md"
)

DEFAULT_INPUTS = (
    Path(
        "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/"
        "duplicate_noop_smoke/candidate_impact_rows.csv"
    ),
    Path(
        "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/"
        "real_capture_mt20_apollo/candidate_impact_rows.csv"
    ),
    Path(
        "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/"
        "impact/candidate_impact_rows.csv"
    ),
    Path(
        "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/"
        "impact/candidate_impact_rows.csv"
    ),
    Path(
        "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/"
        "impact/candidate_impact_rows.csv"
    ),
)

BASE_FIELDS = (
    "task_set",
    "sequence",
    "new_task_set",
    "strict_replacement_by_cost",
    "active_support_changing",
)
HOLDOUT_FIELDS = ("impact_dataset", "instance", "context_hash")
STRICT_PRECISION_MIN = 0.75
STRICT_RECALL_MIN = 0.5


def _dataset_name(path: Path) -> str:
    if path.name == "candidate_impact_rows.csv":
        if path.parent.name == "impact":
            return path.parent.parent.name
        return path.parent.name
    return path.stem


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_rows(paths: tuple[Path, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        dataset = _dataset_name(path)
        with path.open(newline="", encoding="utf-8") as handle:
            for raw in csv.DictReader(handle):
                if raw.get("single_impact_class") not in {"improved", "noop"}:
                    continue
                if not _as_bool(raw.get("single_treatment_found")):
                    continue
                row: dict[str, Any] = dict(raw)
                row["impact_dataset"] = dataset
                row["impact_source"] = str(path)
                row["label"] = (
                    1 if raw.get("single_impact_class") == "improved" else 0
                )
                row["control_objective_value"] = _as_float(
                    raw.get("control_objective")
                )
                rows.append(row)
    return rows


def _objective_bin(value: Any, width: float = 100.0) -> str:
    parsed = _as_float(value)
    if parsed is None:
        return "missing"
    return str(int(math.floor(parsed / width) * width))


def _metrics(predictions: list[bool], rows: list[dict[str, Any]]) -> dict[str, Any]:
    tp = sum(1 for pred, row in zip(predictions, rows) if pred and row["label"] == 1)
    fp = sum(1 for pred, row in zip(predictions, rows) if pred and row["label"] == 0)
    tn = sum(
        1 for pred, row in zip(predictions, rows) if not pred and row["label"] == 0
    )
    fn = sum(
        1 for pred, row in zip(predictions, rows) if not pred and row["label"] == 1
    )
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    accuracy = (tp + tn) / len(rows) if rows else None
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
    }


def _passes_strict(metrics: dict[str, Any]) -> bool:
    precision = metrics.get("precision")
    recall = metrics.get("recall")
    return (
        precision is not None
        and recall is not None
        and float(precision) >= STRICT_PRECISION_MIN
        and float(recall) >= STRICT_RECALL_MIN
    )


def _train_threshold_rule(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = sorted(
        {
            row["control_objective_value"]
            for row in rows
            if row["control_objective_value"] is not None
        }
    )
    candidates: list[tuple[float, float, float, str, float, dict[str, Any]]] = []
    for threshold in values:
        for direction in (">=", "<="):
            predictions = [
                row["control_objective_value"] is not None
                and (
                    row["control_objective_value"] >= threshold
                    if direction == ">="
                    else row["control_objective_value"] <= threshold
                )
                for row in rows
            ]
            metrics = _metrics(predictions, rows)
            precision = metrics["precision"]
            recall = metrics["recall"] or 0.0
            accuracy = metrics["accuracy"] or 0.0
            if precision is not None and precision >= STRICT_PRECISION_MIN:
                candidates.append(
                    (recall, float(precision), accuracy, direction, threshold, metrics)
                )
    if not candidates:
        return {
            "rule_type": "threshold",
            "available": False,
            "direction": None,
            "threshold": None,
            "train_metrics": _metrics([False] * len(rows), rows),
        }
    recall, precision, accuracy, direction, threshold, metrics = max(candidates)
    return {
        "rule_type": "threshold",
        "available": True,
        "direction": direction,
        "threshold": threshold,
        "train_metrics": metrics,
        "selection_key": [recall, precision, accuracy],
    }


def _predict_threshold(rule: dict[str, Any], rows: list[dict[str, Any]]) -> list[bool]:
    if not rule.get("available"):
        return [False] * len(rows)
    threshold = float(rule["threshold"])
    direction = rule["direction"]
    return [
        row["control_objective_value"] is not None
        and (
            row["control_objective_value"] >= threshold
            if direction == ">="
            else row["control_objective_value"] <= threshold
        )
        for row in rows
    ]


def _majority_key(row: dict[str, Any], model_name: str) -> tuple[str, ...]:
    if model_name == "bin100_majority75":
        return (_objective_bin(row.get("control_objective")),)
    if model_name == "shape_bin100_majority75":
        return tuple(str(row.get(field, "")) for field in BASE_FIELDS) + (
            _objective_bin(row.get("control_objective")),
        )
    if model_name == "shape_majority75":
        return tuple(str(row.get(field, "")) for field in BASE_FIELDS)
    raise ValueError(f"Unknown majority model: {model_name}")


def _train_majority_rule(
    rows: list[dict[str, Any]], model_name: str
) -> dict[str, Any]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[_majority_key(row, model_name)].append(row)
    selected_keys: list[tuple[str, ...]] = []
    for key, group_rows in groups.items():
        positive = sum(int(row["label"]) for row in group_rows)
        positive_rate = positive / len(group_rows)
        if positive_rate >= STRICT_PRECISION_MIN:
            selected_keys.append(key)
    selected_set = set(selected_keys)
    predictions = [
        _majority_key(row, model_name) in selected_set for row in rows
    ]
    return {
        "rule_type": "majority_key",
        "available": True,
        "selected_key_count": len(selected_keys),
        "selected_keys": [list(key) for key in sorted(selected_keys)[:20]],
        "train_metrics": _metrics(predictions, rows),
    }


def _predict_majority(
    rule: dict[str, Any], model_name: str, rows: list[dict[str, Any]]
) -> list[bool]:
    selected = {tuple(item) for item in rule.get("selected_keys_full", [])}
    if not selected:
        selected = {tuple(item) for item in rule.get("selected_keys", [])}
    return [_majority_key(row, model_name) in selected for row in rows]


def _train_rule(rows: list[dict[str, Any]], model_name: str) -> dict[str, Any]:
    if model_name == "threshold_precision75":
        return _train_threshold_rule(rows)
    rule = _train_majority_rule(rows, model_name)
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[_majority_key(row, model_name)].append(row)
    full_keys = []
    for key, group_rows in groups.items():
        positive = sum(int(row["label"]) for row in group_rows)
        if positive / len(group_rows) >= STRICT_PRECISION_MIN:
            full_keys.append(list(key))
    rule["selected_keys_full"] = full_keys
    return rule


def _predict(
    rule: dict[str, Any], model_name: str, rows: list[dict[str, Any]]
) -> list[bool]:
    if model_name == "threshold_precision75":
        return _predict_threshold(rule, rows)
    return _predict_majority(rule, model_name, rows)


def _evaluate_model(rows: list[dict[str, Any]], model_name: str) -> dict[str, Any]:
    holdout_results: dict[str, Any] = {}
    for holdout_field in HOLDOUT_FIELDS:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            groups[str(row.get(holdout_field, ""))].append(row)
        all_test_rows: list[dict[str, Any]] = []
        all_predictions: list[bool] = []
        per_group: list[dict[str, Any]] = []
        for group_name, test_rows in sorted(groups.items()):
            train_rows = [
                row for row in rows if str(row.get(holdout_field, "")) != group_name
            ]
            rule = _train_rule(train_rows, model_name)
            predictions = _predict(rule, model_name, test_rows)
            test_metrics = _metrics(predictions, test_rows)
            per_group.append(
                {
                    "group": group_name,
                    "row_count": len(test_rows),
                    "label_counts": dict(
                        Counter(
                            "improved" if row["label"] == 1 else "noop"
                            for row in test_rows
                        )
                    ),
                    "prediction_count": sum(1 for pred in predictions if pred),
                    "test_metrics": test_metrics,
                    "passes_strict": _passes_strict(test_metrics),
                    "trained_rule": {
                        key: value
                        for key, value in rule.items()
                        if key != "selected_keys_full"
                    },
                }
            )
            all_test_rows.extend(test_rows)
            all_predictions.extend(predictions)
        aggregate = _metrics(all_predictions, all_test_rows)
        holdout_results[holdout_field] = {
            "aggregate_metrics": aggregate,
            "passes_strict": _passes_strict(aggregate),
            "predicted_group_count": sum(
                1 for item in per_group if item["prediction_count"] > 0
            ),
            "low_precision_predicted_group_count": sum(
                1
                for item in per_group
                if item["prediction_count"] > 0
                and item["test_metrics"]["precision"] is not None
                and item["test_metrics"]["precision"] < STRICT_PRECISION_MIN
            ),
            "zero_recall_positive_group_count": sum(
                1
                for item in per_group
                if item["label_counts"].get("improved", 0) > 0
                and item["test_metrics"]["recall"] == 0.0
            ),
            "per_group": per_group,
        }
    passes_all = all(
        holdout_results[field]["passes_strict"] for field in HOLDOUT_FIELDS
    )
    return {
        "model": model_name,
        "holdouts": holdout_results,
        "passes_all_holdouts": passes_all,
    }


def build_summary(inputs: tuple[Path, ...]) -> dict[str, Any]:
    rows = _read_rows(inputs)
    label_counts = Counter(
        "improved" if row["label"] == 1 else "noop" for row in rows
    )
    models = (
        "threshold_precision75",
        "bin100_majority75",
        "shape_bin100_majority75",
        "shape_majority75",
    )
    model_results = {name: _evaluate_model(rows, name) for name in models}
    passing_models = [
        name for name, result in model_results.items() if result["passes_all_holdouts"]
    ]
    threshold_context = model_results["threshold_precision75"]["holdouts"][
        "context_hash"
    ]["aggregate_metrics"]
    bin100_instance = model_results["bin100_majority75"]["holdouts"]["instance"][
        "aggregate_metrics"
    ]
    bin100_context = model_results["bin100_majority75"]["holdouts"]["context_hash"][
        "aggregate_metrics"
    ]
    checks = {
        "has_expected_rows": len(rows) == 280,
        "threshold_high_recall_but_context_precision_fails": (
            (threshold_context["recall"] or 0.0) >= STRICT_RECALL_MIN
            and (threshold_context["precision"] or 0.0) < STRICT_PRECISION_MIN
        ),
        "bin100_high_precision_but_instance_recall_fails": (
            (bin100_instance["precision"] or 0.0) >= STRICT_PRECISION_MIN
            and (bin100_instance["recall"] or 0.0) < STRICT_RECALL_MIN
        ),
        "bin100_high_precision_but_context_recall_fails": (
            (bin100_context["precision"] or 0.0) >= STRICT_PRECISION_MIN
            and (bin100_context["recall"] or 0.0) < STRICT_RECALL_MIN
        ),
        "no_model_passes_all_holdout_gates": not passing_models,
    }
    return {
        "schema_version": "selector_context_scalar_holdout_v1",
        "inputs": [str(path) for path in inputs],
        "row_count": len(rows),
        "label_counts": dict(label_counts),
        "strict_precision_min": STRICT_PRECISION_MIN,
        "strict_recall_min": STRICT_RECALL_MIN,
        "model_results": model_results,
        "passing_models": passing_models,
        "production_validated_selector": False,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "control_objective has real calibration signal, but simple "
            "addition-before scalar rules do not pass dataset, instance, and "
            "context holdout gates together. It remains a calibration lead, "
            "not a production selector."
        ),
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    models = summary["model_results"]
    lines = [
        "# Selector Context Scalar Holdout 审计",
        "",
        "日期：2026-06-13",
        "",
        "## 目标",
        "",
        "`control_objective` 在当前 replay 样本中能消除 mixed labels；本审计检查它",
        "是否能跨 dataset / instance / context_hash 留出稳定泛化。",
        "本脚本只读 candidate replay rows，不运行 BPC，不改变 production path。",
        "",
        "## 结论",
        "",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "selector_context_scalar_holdout = current",
        f"row_count = {summary['row_count']}",
        f"label_counts = {summary['label_counts']}",
        f"strict_precision_min = {summary['strict_precision_min']}",
        f"strict_recall_min = {summary['strict_recall_min']}",
        f"control_objective_holdout_passing_model_count = {len(summary['passing_models'])}",
        "control_objective_holdout_production_validated_selector = false",
        "",
        "核心判断：`control_objective` 有 calibration signal，但还不是 production selector。",
        "激进 threshold 在 context holdout 下 precision 不稳；保守 100-bin majority",
        "precision 高但 instance/context recall 太低，不足以支撑 20 大幅加速。",
        "",
        "## Holdout 汇总",
        "",
        "| Model | Dataset P/R | Dataset Pass | Instance P/R | Instance Pass | Context P/R | Context Pass | All Pass |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model_name, result in models.items():
        holdouts = result["holdouts"]
        cells = []
        for field in HOLDOUT_FIELDS:
            metrics = holdouts[field]["aggregate_metrics"]
            cells.extend(
                [
                    f"{_fmt(metrics['precision'])}/{_fmt(metrics['recall'])}",
                    str(holdouts[field]["passes_strict"]).lower(),
                ]
            )
        lines.append(
            "| "
            + " | ".join(
                [
                    model_name,
                    cells[0],
                    cells[1],
                    cells[2],
                    cells[3],
                    cells[4],
                    cells[5],
                    str(result["passes_all_holdouts"]).lower(),
                ]
            )
            + " |"
        )
    threshold_context = models["threshold_precision75"]["holdouts"]["context_hash"][
        "aggregate_metrics"
    ]
    bin100_instance = models["bin100_majority75"]["holdouts"]["instance"][
        "aggregate_metrics"
    ]
    bin100_context = models["bin100_majority75"]["holdouts"]["context_hash"][
        "aggregate_metrics"
    ]
    lines.extend(
        [
            "",
            "## 关键失败模式",
            "",
            "```text",
            "threshold_context_precision = "
            f"{_fmt(threshold_context['precision'])}",
            f"threshold_context_recall = {_fmt(threshold_context['recall'])}",
            "bin100_instance_precision = "
            f"{_fmt(bin100_instance['precision'])}",
            f"bin100_instance_recall = {_fmt(bin100_instance['recall'])}",
            f"bin100_context_precision = {_fmt(bin100_context['precision'])}",
            f"bin100_context_recall = {_fmt(bin100_context['recall'])}",
            "control_objective_holdout_passing_model_count = "
            f"{len(summary['passing_models'])}",
            "production_validated_selector = false",
            "```",
            "",
            "解释：当前样本中 `control_objective_bin_100_mixed_group_count = 0` 只能说明",
            "它能分开已见 replay labels。留出后，简单规则不能同时满足 precision 和 recall。",
            "因此它支持“RMP/context coupling 是根因”，但不能直接变成优化主线。",
            "",
            "## 下一步含义",
            "",
            "在没有 full BPC A/B 前，不应把该 selector 接入 production worker 或 certificate gate。",
            "若继续推进，应先扩大 capture/replay 数据，或者寻找更稳定的 addition-before",
            "RMP trajectory 特征，再重复 dataset / instance / context holdout。",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = build_summary(DEFAULT_INPUTS)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    write_report(summary, args.report)
    compact = {
        "all_checks_pass": summary["all_checks_pass"],
        "row_count": summary["row_count"],
        "passing_models": summary["passing_models"],
        "production_validated_selector": summary["production_validated_selector"],
        "checks": summary["checks"],
        "report": str(args.report),
        "summary": str(args.output_dir / "summary.json"),
    }
    print(json.dumps(compact, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
