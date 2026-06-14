#!/usr/bin/env python3
"""Audit addition-before selector gates on exact replay impact rows.

This script is read-only with respect to solver state.  It uses existing
``candidate_impact_rows.csv`` files produced by counterfactual replay impact
analysis and checks whether simple addition-before features can form a stable
selector under context / instance / dataset holdouts.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_counterfactual_replay_selector_gate_20260613"
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
)

NUMERIC_FEATURES = (
    "true_reduced_cost",
    "cost",
    "task_count",
    "vehicle_count",
)
BOOLEAN_FEATURES = (
    "new_task_set",
    "duplicate_signature",
    "active_support_changing",
    "strict_replacement_by_cost",
    "weak_replacement_or_duplicate",
)
HOLDOUT_KEYS = ("context_hash", "instance", "impact_dataset")


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


def _read_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw_path in paths:
        path = _candidate_csv(raw_path)
        dataset = _dataset_name(path)
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("single_impact_class") not in {"improved", "noop"}:
                    continue
                if str(row.get("single_treatment_found", "")).lower() not in {
                    "1",
                    "true",
                    "yes",
                }:
                    continue
                row = dict(row)
                row["impact_dataset"] = dataset
                row["impact_source"] = str(path)
                rows.append(row)
    return rows


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


def _rule_predicts(row: dict[str, str], rule: dict[str, Any]) -> bool:
    feature = str(rule["feature"])
    if rule["type"] == "numeric":
        value = _as_float(row.get(feature))
        if value is None:
            return False
        threshold = float(rule["threshold"])
        if rule["operator"] == "<=":
            return value <= threshold
        return value >= threshold
    value = _as_bool(row.get(feature))
    if value is None:
        return False
    return value is bool(rule["value"])


def _evaluate_rule(rows: list[dict[str, str]], rule: dict[str, Any]) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row in rows:
        pred = _rule_predicts(row, rule)
        positive = row.get("single_impact_class") == "improved"
        if pred and positive:
            tp += 1
        elif pred and not positive:
            fp += 1
        elif not pred and positive:
            fn += 1
        else:
            tn += 1
    precision = None if tp + fp <= 0 else tp / float(tp + fp)
    recall = None if tp + fn <= 0 else tp / float(tp + fn)
    accuracy = None if tp + fp + tn + fn <= 0 else (tp + tn) / float(tp + fp + tn + fn)
    return {
        "total": tp + fp + tn + fn,
        "predicted_positive": tp + fp,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
    }


def _candidate_rules(rows: list[dict[str, str]], feature: str) -> list[dict[str, Any]]:
    if feature in NUMERIC_FEATURES:
        values = sorted(
            {
                value
                for row in rows
                for value in [_as_float(row.get(feature))]
                if value is not None
            }
        )
        return [
            {"type": "numeric", "feature": feature, "operator": operator, "threshold": value}
            for value in values
            for operator in ("<=", ">=")
        ]
    values = sorted(
        {
            value
            for row in rows
            for value in [_as_bool(row.get(feature))]
            if value is not None
        }
    )
    return [
        {"type": "boolean", "feature": feature, "operator": "==", "value": value}
        for value in values
    ]


def _rule_sort_key(metrics: dict[str, Any]) -> tuple[Any, ...]:
    precision = metrics.get("precision")
    recall = metrics.get("recall")
    return (
        precision is not None and precision >= 0.75 and recall is not None and recall >= 0.5,
        -1.0 if precision is None else float(precision),
        -1.0 if recall is None else float(recall),
        int(metrics.get("tp", 0)),
        -int(metrics.get("fp", 0)),
        -int(metrics.get("predicted_positive", 0)),
    )


def _best_rule_for_feature(rows: list[dict[str, str]], feature: str) -> dict[str, Any] | None:
    best: tuple[tuple[Any, ...], dict[str, Any], dict[str, Any]] | None = None
    for rule in _candidate_rules(rows, feature):
        metrics = _evaluate_rule(rows, rule)
        key = _rule_sort_key(metrics)
        if best is None or key > best[0]:
            best = (key, rule, metrics)
    if best is None:
        return None
    return {"rule": best[1], "metrics": best[2]}


def _micro_average(metrics_list: list[dict[str, Any]]) -> dict[str, Any]:
    total = {
        "tp": sum(int(m.get("tp", 0)) for m in metrics_list),
        "fp": sum(int(m.get("fp", 0)) for m in metrics_list),
        "tn": sum(int(m.get("tn", 0)) for m in metrics_list),
        "fn": sum(int(m.get("fn", 0)) for m in metrics_list),
    }
    return _evaluate_counts(total)


def _evaluate_counts(counts: dict[str, int]) -> dict[str, Any]:
    tp = int(counts.get("tp", 0))
    fp = int(counts.get("fp", 0))
    tn = int(counts.get("tn", 0))
    fn = int(counts.get("fn", 0))
    precision = None if tp + fp <= 0 else tp / float(tp + fp)
    recall = None if tp + fn <= 0 else tp / float(tp + fn)
    accuracy = None if tp + fp + tn + fn <= 0 else (tp + tn) / float(tp + fp + tn + fn)
    return {
        "total": tp + fp + tn + fn,
        "predicted_positive": tp + fp,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
    }


def _holdout_feature_metrics(
    rows: list[dict[str, str]],
    *,
    holdout_key: str,
    feature: str,
) -> dict[str, Any]:
    groups = sorted({str(row.get(holdout_key, "")) for row in rows})
    folds: list[dict[str, Any]] = []
    for group in groups:
        train = [row for row in rows if str(row.get(holdout_key, "")) != group]
        test = [row for row in rows if str(row.get(holdout_key, "")) == group]
        best = _best_rule_for_feature(train, feature)
        if best is None:
            continue
        test_metrics = _evaluate_rule(test, best["rule"])
        train_metrics = best["metrics"]
        folds.append(
            {
                "holdout": group,
                "rule": best["rule"],
                "train": train_metrics,
                "test": test_metrics,
            }
        )
    micro = _micro_average([fold["test"] for fold in folds])
    return {
        "holdout_key": holdout_key,
        "feature": feature,
        "fold_count": len(folds),
        "micro": micro,
        "passes_strict_gate": _passes_strict_gate(micro),
        "passing_fold_count": sum(
            1 for fold in folds if _passes_strict_gate(fold["test"])
        ),
        "worst_folds": sorted(
            folds,
            key=lambda fold: (
                -1.0
                if fold["test"].get("precision") is None
                else float(fold["test"]["precision"]),
                -1.0 if fold["test"].get("recall") is None else float(fold["test"]["recall"]),
            ),
        )[:5],
    }


def _holdout_train_best_metrics(
    rows: list[dict[str, str]],
    *,
    holdout_key: str,
    features: tuple[str, ...],
) -> dict[str, Any]:
    groups = sorted({str(row.get(holdout_key, "")) for row in rows})
    folds: list[dict[str, Any]] = []
    for group in groups:
        train = [row for row in rows if str(row.get(holdout_key, "")) != group]
        test = [row for row in rows if str(row.get(holdout_key, "")) == group]
        candidates: list[dict[str, Any]] = []
        for feature in features:
            best = _best_rule_for_feature(train, feature)
            if best is None:
                continue
            candidates.append({"feature": feature, **best})
        if not candidates:
            continue
        best = max(candidates, key=lambda item: _rule_sort_key(item["metrics"]))
        test_metrics = _evaluate_rule(test, best["rule"])
        folds.append(
            {
                "holdout": group,
                "feature": best["feature"],
                "rule": best["rule"],
                "train": best["metrics"],
                "test": test_metrics,
            }
        )
    micro = _micro_average([fold["test"] for fold in folds])
    return {
        "holdout_key": holdout_key,
        "fold_count": len(folds),
        "micro": micro,
        "passes_strict_gate": _passes_strict_gate(micro),
        "passing_fold_count": sum(
            1 for fold in folds if _passes_strict_gate(fold["test"])
        ),
        "feature_choices": dict(Counter(fold["feature"] for fold in folds)),
        "worst_folds": sorted(
            folds,
            key=lambda fold: (
                -1.0
                if fold["test"].get("precision") is None
                else float(fold["test"]["precision"]),
                -1.0 if fold["test"].get("recall") is None else float(fold["test"]["recall"]),
            ),
        )[:5],
    }


def _passes_strict_gate(metrics: dict[str, Any]) -> bool:
    precision = metrics.get("precision")
    recall = metrics.get("recall")
    return precision is not None and recall is not None and precision >= 0.75 and recall >= 0.5


def analyze_selector_gate(paths: list[Path]) -> dict[str, Any]:
    rows = _read_rows(paths)
    features = tuple(NUMERIC_FEATURES) + tuple(BOOLEAN_FEATURES)
    full_sample = {
        feature: _best_rule_for_feature(rows, feature)
        for feature in features
    }
    full_sample = {
        feature: payload for feature, payload in full_sample.items() if payload is not None
    }
    holdout_by_feature = {
        holdout_key: {
            feature: _holdout_feature_metrics(rows, holdout_key=holdout_key, feature=feature)
            for feature in features
        }
        for holdout_key in HOLDOUT_KEYS
    }
    holdout_train_best = {
        holdout_key: _holdout_train_best_metrics(
            rows,
            holdout_key=holdout_key,
            features=features,
        )
        for holdout_key in HOLDOUT_KEYS
    }
    passing_features_all_holdouts = []
    for feature in features:
        if all(
            holdout_by_feature[holdout_key][feature]["passes_strict_gate"]
            for holdout_key in HOLDOUT_KEYS
        ):
            passing_features_all_holdouts.append(feature)
    label_counts = dict(Counter(row["single_impact_class"] for row in rows))
    context_counts = dict(Counter(row["context_hash"] for row in rows))
    result = {
        "schema_version": "counterfactual_replay_selector_gate_v1",
        "input_paths": [str(_candidate_csv(path)) for path in paths],
        "row_count": len(rows),
        "label_counts": label_counts,
        "context_count": len(context_counts),
        "instance_count": len({row["instance"] for row in rows}),
        "impact_dataset_count": len({row["impact_dataset"] for row in rows}),
        "features": {
            "numeric": list(NUMERIC_FEATURES),
            "boolean": list(BOOLEAN_FEATURES),
            "excluded_post_treatment": [
                "single_objective_delta",
                "single_dual_l1_delta",
                "single_changed_journey_count",
            ],
        },
        "strict_gate": {
            "precision_min": 0.75,
            "recall_min": 0.5,
        },
        "full_sample_best_by_feature": full_sample,
        "holdout_by_feature": holdout_by_feature,
        "holdout_train_best": holdout_train_best,
        "passing_features_all_holdouts": passing_features_all_holdouts,
    }
    true_rc_full = full_sample.get("true_reduced_cost", {}).get("metrics", {})
    dataset_true_rc = holdout_by_feature["impact_dataset"]["true_reduced_cost"]["micro"]
    context_true_rc = holdout_by_feature["context_hash"]["true_reduced_cost"]["micro"]
    result["checks"] = {
        "has_exact_replay_rows": len(rows) >= 200,
        "has_improved_and_noop_labels": (
            int(label_counts.get("improved", 0)) > 0 and int(label_counts.get("noop", 0)) > 0
        ),
        "full_sample_true_rc_rule_looks_promising": _passes_strict_gate(true_rc_full),
        "context_holdout_true_rc_rule_still_imperfect": (
            _passes_strict_gate(context_true_rc) and int(context_true_rc.get("fp", 0)) > 0
        ),
        "dataset_holdout_true_rc_rule_fails": not _passes_strict_gate(dataset_true_rc),
        "no_single_feature_passes_all_holdout_gates": not passing_features_all_holdouts,
        "train_best_dataset_holdout_fails": not holdout_train_best["impact_dataset"][
            "passes_strict_gate"
        ],
        "post_treatment_features_excluded": True,
    }
    result["all_checks_pass"] = all(result["checks"].values())
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        default=list(DEFAULT_INPUTS),
        help="candidate_impact_rows.csv files or directories containing them.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    result = analyze_selector_gate(list(args.inputs or DEFAULT_INPUTS))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
