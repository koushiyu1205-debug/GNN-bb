#!/usr/bin/env python3
"""Train-on-fold audit for simple addition-before selector rule families.

This read-only audit is stricter than a full-sample rule search: for each
held-out context / instance / dataset fold, it selects the best single-clause
or two-clause conjunction on the remaining rows and evaluates that selected
rule on the held-out fold.  It uses only addition-before features and never
runs the solver.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_rule_family_train_holdout_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_rule_family_train_holdout_zh.md"
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

HOLDOUT_KEYS = ("context_hash", "instance", "impact_dataset")
STRICT_PRECISION_MIN = 0.75
STRICT_RECALL_MIN = 0.5
MAX_PAIR_BASE_CLAUSES = 220

NUMERIC_FEATURES = (
    "true_reduced_cost",
    "cost",
    "control_objective",
    "cg_iter",
    "task_count",
    "vehicle_count",
    "sequence_len",
    "task_set_size",
    "rc_per_task",
    "cost_per_task",
)
BOOLEAN_FEATURES = (
    "new_task_set",
    "duplicate_signature",
    "active_support_changing",
    "strict_replacement_by_cost",
    "weak_replacement_or_duplicate",
)


def _dataset_name(path: Path) -> str:
    if path.name == "candidate_impact_rows.csv":
        if path.parent.name == "impact":
            return path.parent.parent.name
        return path.parent.name
    return path.stem


def _candidate_csv(path: Path) -> Path:
    if path.is_dir():
        return path / "candidate_impact_rows.csv"
    return path


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool | None:
    if value in (None, ""):
        return None
    text = str(value).strip().lower()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no"}:
        return False
    return None


def _enrich_row(row: dict[str, str]) -> dict[str, str]:
    copied = dict(row)
    sequence = [
        item
        for item in str(copied.get("sequence", "")).replace(",", "-").split("-")
        if item
    ]
    task_set = [item for item in str(copied.get("task_set", "")).split(",") if item]
    true_rc = _as_float(copied.get("true_reduced_cost"))
    cost = _as_float(copied.get("cost"))
    copied["sequence_len"] = str(len(sequence))
    copied["task_set_size"] = str(len(task_set))
    copied["rc_per_task"] = (
        "" if true_rc is None or not task_set else str(true_rc / len(task_set))
    )
    copied["cost_per_task"] = (
        "" if cost is None or not task_set else str(cost / len(task_set))
    )
    return copied


def _read_rows(paths: list[Path], task_count_filter: int | None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw_path in paths:
        path = _candidate_csv(raw_path)
        dataset = _dataset_name(path)
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("single_impact_class") not in {"improved", "noop"}:
                    continue
                if _as_bool(row.get("single_treatment_found")) is not True:
                    continue
                copied = _enrich_row(row)
                if task_count_filter is not None and _as_float(
                    copied.get("task_count")
                ) != float(task_count_filter):
                    continue
                copied["impact_dataset"] = dataset
                copied["impact_source"] = str(path)
                rows.append(copied)
    return rows


def _mask_for_indices(indices: list[int]) -> int:
    mask = 0
    for index in indices:
        mask |= 1 << index
    return mask


def _evaluate_mask(rule_mask: int, sample_mask: int, positive_mask: int, all_mask: int) -> dict[str, Any]:
    pred = rule_mask & sample_mask
    positive = positive_mask & sample_mask
    negative = (all_mask ^ positive_mask) & sample_mask
    tp = (pred & positive).bit_count()
    fp = (pred & negative).bit_count()
    fn = ((sample_mask ^ pred) & positive).bit_count()
    tn = ((sample_mask ^ pred) & negative).bit_count()
    total = tp + fp + tn + fn
    precision = None if tp + fp <= 0 else tp / float(tp + fp)
    recall = None if tp + fn <= 0 else tp / float(tp + fn)
    accuracy = None if total <= 0 else (tp + tn) / float(total)
    return {
        "total": total,
        "predicted_positive": tp + fp,
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


def _passes_material(metrics: dict[str, Any]) -> bool:
    positive_count = int(metrics.get("tp", 0)) + int(metrics.get("fn", 0))
    if positive_count <= 0:
        return int(metrics.get("fp", 0)) == 0
    return _passes_strict(metrics)


def _score(metrics: dict[str, Any]) -> tuple[Any, ...]:
    precision = metrics.get("precision") or 0.0
    recall = metrics.get("recall") or 0.0
    f1 = 0.0 if precision + recall <= 0.0 else 2.0 * precision * recall / (precision + recall)
    return (
        _passes_strict(metrics),
        f1,
        precision,
        recall,
        int(metrics.get("tp", 0)),
        -int(metrics.get("fp", 0)),
        -int(metrics.get("predicted_positive", 0)),
    )


def _build_clause_masks(rows: list[dict[str, str]], train_mask: int) -> list[dict[str, Any]]:
    train_indices = [index for index in range(len(rows)) if train_mask & (1 << index)]
    clauses: list[dict[str, Any]] = []
    for feature in NUMERIC_FEATURES:
        values = sorted(
            {
                value
                for index in train_indices
                for value in [_as_float(rows[index].get(feature))]
                if value is not None
            }
        )
        for operator in ("<=", ">="):
            for threshold in values:
                mask = 0
                for index, row in enumerate(rows):
                    value = _as_float(row.get(feature))
                    if value is None:
                        continue
                    if operator == "<=" and value <= threshold + 1.0e-12:
                        mask |= 1 << index
                    elif operator == ">=" and value >= threshold - 1.0e-12:
                        mask |= 1 << index
                clauses.append(
                    {
                        "features": (feature,),
                        "description": f"{feature}{operator}{threshold:.6g}",
                        "mask": mask,
                    }
                )
    for feature in BOOLEAN_FEATURES:
        values = sorted(
            {
                value
                for index in train_indices
                for value in [_as_bool(rows[index].get(feature))]
                if value is not None
            }
        )
        for expected in values:
            mask = 0
            for index, row in enumerate(rows):
                if _as_bool(row.get(feature)) is expected:
                    mask |= 1 << index
            clauses.append(
                {
                    "features": (feature,),
                    "description": f"{feature}=={str(expected).lower()}",
                    "mask": mask,
                }
            )
    return clauses


def _select_best_rule(
    rows: list[dict[str, str]],
    train_mask: int,
    positive_mask: int,
    all_mask: int,
) -> dict[str, Any]:
    clauses = _build_clause_masks(rows, train_mask)
    for clause in clauses:
        clause["train"] = _evaluate_mask(clause["mask"], train_mask, positive_mask, all_mask)
    base = sorted(
        [
            clause
            for clause in clauses
            if int(clause["train"].get("predicted_positive", 0)) > 0
        ],
        key=lambda item: _score(item["train"]),
        reverse=True,
    )[:MAX_PAIR_BASE_CLAUSES]
    best: dict[str, Any] | None = None
    candidates = list(base)
    for left, right in combinations(base, 2):
        if set(left["features"]) & set(right["features"]):
            continue
        mask = left["mask"] & right["mask"]
        candidates.append(
            {
                "features": tuple(left["features"]) + tuple(right["features"]),
                "description": f"{left['description']} AND {right['description']}",
                "mask": mask,
                "train": _evaluate_mask(mask, train_mask, positive_mask, all_mask),
            }
        )
    for candidate in candidates:
        if best is None or _score(candidate["train"]) > _score(best["train"]):
            best = candidate
    if best is None:
        return {
            "description": "<no_rule>",
            "features": (),
            "mask": 0,
            "train": _evaluate_mask(0, train_mask, positive_mask, all_mask),
        }
    best["candidate_count"] = len(candidates)
    best["single_clause_count"] = len(clauses)
    return best


def _combine_counts(metrics_list: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {
        "tp": sum(int(item.get("tp", 0)) for item in metrics_list),
        "fp": sum(int(item.get("fp", 0)) for item in metrics_list),
        "tn": sum(int(item.get("tn", 0)) for item in metrics_list),
        "fn": sum(int(item.get("fn", 0)) for item in metrics_list),
    }
    total = counts["tp"] + counts["fp"] + counts["tn"] + counts["fn"]
    precision = None if counts["tp"] + counts["fp"] <= 0 else counts["tp"] / float(counts["tp"] + counts["fp"])
    recall = None if counts["tp"] + counts["fn"] <= 0 else counts["tp"] / float(counts["tp"] + counts["fn"])
    accuracy = None if total <= 0 else (counts["tp"] + counts["tn"]) / float(total)
    return {
        **counts,
        "total": total,
        "predicted_positive": counts["tp"] + counts["fp"],
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
    }


def build_summary(
    input_paths: list[Path], task_count_filter: int | None = None
) -> dict[str, Any]:
    rows = _read_rows(input_paths, task_count_filter)
    all_mask = (1 << len(rows)) - 1
    positive_mask = _mask_for_indices(
        [
            index
            for index, row in enumerate(rows)
            if row.get("single_impact_class") == "improved"
        ]
    )
    holdout_summaries: dict[str, Any] = {}
    for holdout_key in HOLDOUT_KEYS:
        folds = []
        for value in sorted({str(row.get(holdout_key, "")) for row in rows}):
            test_indices = [
                index
                for index, row in enumerate(rows)
                if str(row.get(holdout_key, "")) == value
            ]
            test_mask = _mask_for_indices(test_indices)
            train_mask = all_mask ^ test_mask
            best = _select_best_rule(rows, train_mask, positive_mask, all_mask)
            test_metrics = _evaluate_mask(
                best["mask"], test_mask, positive_mask, all_mask
            )
            folds.append(
                {
                    "holdout": value,
                    "selected_rule": best["description"],
                    "train": best["train"],
                    "test": test_metrics,
                    "strict_pass": _passes_strict(test_metrics),
                    "material_pass": _passes_material(test_metrics),
                    "candidate_count": best.get("candidate_count", 0),
                    "single_clause_count": best.get("single_clause_count", 0),
                }
            )
        holdout_summaries[holdout_key] = {
            "fold_count": len(folds),
            "strict_passing_fold_count": sum(1 for fold in folds if fold["strict_pass"]),
            "material_passing_fold_count": sum(
                1 for fold in folds if fold["material_pass"]
            ),
            "all_strict_folds_pass": all(fold["strict_pass"] for fold in folds),
            "all_material_folds_pass": all(fold["material_pass"] for fold in folds),
            "micro": _combine_counts([fold["test"] for fold in folds]),
            "folds": folds,
            "worst_folds": sorted(
                folds,
                key=lambda fold: (
                    -1.0
                    if fold["test"].get("precision") is None
                    else float(fold["test"]["precision"]),
                    -1.0
                    if fold["test"].get("recall") is None
                    else float(fold["test"]["recall"]),
                    int(fold["test"].get("fp", 0)),
                ),
            )[:8],
        }
    checks = {
        "row_scope_matches_filter": bool(
            (task_count_filter is None and len(rows) == 280)
            or (
                task_count_filter is not None
                and rows
                and all(
                    _as_float(row.get("task_count")) == float(task_count_filter)
                    for row in rows
                )
            )
        ),
        "has_label_mixture": len({row.get("single_impact_class") for row in rows}) == 2,
        "no_all_holdout_families_material_pass": not all(
            holdout_summaries[key]["all_material_folds_pass"] for key in HOLDOUT_KEYS
        ),
        "context_train_holdout_not_all_material": not holdout_summaries[
            "context_hash"
        ]["all_material_folds_pass"],
    }
    return {
        "schema_version": "selector_rule_family_train_holdout_v1",
        "input_paths": [str(path) for path in input_paths],
        "row_filter": {"task_count": task_count_filter},
        "feature_scope": "addition_before_only",
        "numeric_features": list(NUMERIC_FEATURES),
        "boolean_features": list(BOOLEAN_FEATURES),
        "holdout_keys": list(HOLDOUT_KEYS),
        "strict_gate": {
            "precision_min": STRICT_PRECISION_MIN,
            "recall_min": STRICT_RECALL_MIN,
        },
        "row_count": len(rows),
        "label_counts": dict(Counter(row["single_impact_class"] for row in rows)),
        "context_count": len({row.get("context_hash", "") for row in rows}),
        "instance_count": len({row.get("instance", "") for row in rows}),
        "impact_dataset_count": len({row.get("impact_dataset", "") for row in rows}),
        "holdout_summaries": holdout_summaries,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "Even when a best rule is selected on each training split, simple "
            "addition-before rule families do not pass every held-out context, "
            "instance, and dataset fold."
        ),
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    task_count_filter = summary.get("row_filter", {}).get("task_count")
    lines = [
        "# Selector Rule-Family Train-Holdout 审计",
        "",
        "日期：2026-06-14",
        "",
        "## 目标",
        "",
        "对每个 held-out context / instance / dataset fold，只在训练折上选择",
        "最优单条件或两条件 addition-before 规则，再评估该规则在测试折上的表现。",
        "该审计只读已有 exact replay rows，不运行求解器，不接 production path。",
        "",
        "## 结论",
        "",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "selector_rule_family_train_holdout = current",
        f"task_count_filter = {task_count_filter}",
        f"row_count = {summary['row_count']}",
        f"label_counts = {summary['label_counts']}",
        f"context_count = {summary['context_count']}",
        f"instance_count = {summary['instance_count']}",
        f"impact_dataset_count = {summary['impact_dataset_count']}",
        "production_validated_selector = false",
        "",
        "## Holdout Summary",
        "",
        "| Holdout | Strict Passing Folds | Material Passing Folds | Micro P/R |",
        "|---|---:|---:|---:|",
    ]
    for holdout_key in HOLDOUT_KEYS:
        payload = summary["holdout_summaries"][holdout_key]
        micro = payload["micro"]
        lines.append(
            "| "
            + " | ".join(
                [
                    holdout_key,
                    f"{payload['strict_passing_fold_count']}/{payload['fold_count']}",
                    f"{payload['material_passing_fold_count']}/{payload['fold_count']}",
                    f"{_fmt(micro.get('precision'))}/{_fmt(micro.get('recall'))}",
                ]
            )
            + " |"
        )
    lines.extend(["", "## Worst Fold Samples", ""])
    for holdout_key in HOLDOUT_KEYS:
        payload = summary["holdout_summaries"][holdout_key]
        lines.extend(
            [
                f"### {holdout_key}",
                "",
                "```text",
                f"material_passing_fold_count = {payload['material_passing_fold_count']}/{payload['fold_count']}",
                "worst_folds = "
                + str(
                    [
                        {
                            "holdout": fold["holdout"],
                            "selected_rule": fold["selected_rule"],
                            "precision": fold["test"].get("precision"),
                            "recall": fold["test"].get("recall"),
                            "tp": fold["test"].get("tp"),
                            "fp": fold["test"].get("fp"),
                            "fn": fold["test"].get("fn"),
                        }
                        for fold in payload["worst_folds"][:3]
                    ]
                ),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## 解释",
            "",
            "这排除了另一个可能解释：不是因为 full-sample 规则选择方式不符合",
            "训练流程才导致 selector 不稳。即使每个 fold 都重新用训练集选择规则，",
            "测试 fold 仍不能全部通过。当前 selector 路线仍必须停留在 calibration-only。",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputs",
        nargs="*",
        type=Path,
        default=list(DEFAULT_INPUTS),
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--task-count-filter", type=int, default=None)
    args = parser.parse_args()

    summary = build_summary(
        list(args.inputs), task_count_filter=args.task_count_filter
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, args.report)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
