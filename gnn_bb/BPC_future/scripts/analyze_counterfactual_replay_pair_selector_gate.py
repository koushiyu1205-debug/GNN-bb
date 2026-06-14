#!/usr/bin/env python3
"""Audit two-rule addition-before selector gates on exact replay impact rows.

This script is read-only with respect to solver state.  It uses the same exact
replay impact rows as ``analyze_counterfactual_replay_selector_gate.py`` but
checks whether simple two-rule AND/OR gates can form a stable selector under
context / instance / dataset holdouts.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from BPC_future.scripts.analyze_counterfactual_replay_selector_gate import (
    BOOLEAN_FEATURES,
    DEFAULT_INPUTS,
    HOLDOUT_KEYS,
    NUMERIC_FEATURES,
    _as_bool,
    _as_float,
    _evaluate_counts,
    _passes_strict_gate,
    _read_rows,
)


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_counterfactual_replay_pair_selector_gate_20260613"
)


@dataclass(frozen=True)
class _AtomicRule:
    rule: dict[str, Any]
    feature: str
    mask: int


def _positive_mask(rows: list[dict[str, str]]) -> int:
    mask = 0
    for idx, row in enumerate(rows):
        if row.get("single_impact_class") == "improved":
            mask |= 1 << idx
    return mask


def _rule_mask(rows: list[dict[str, str]], rule: dict[str, Any]) -> int:
    mask = 0
    feature = str(rule["feature"])
    for idx, row in enumerate(rows):
        if rule["type"] == "numeric":
            value = _as_float(row.get(feature))
            if value is None:
                continue
            threshold = float(rule["threshold"])
            if rule["operator"] == "<=" and value <= threshold:
                mask |= 1 << idx
            elif rule["operator"] == ">=" and value >= threshold:
                mask |= 1 << idx
        else:
            value = _as_bool(row.get(feature))
            if value is not None and value is bool(rule["value"]):
                mask |= 1 << idx
    return mask


def _candidate_atomic_rules(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for feature in NUMERIC_FEATURES:
        values = sorted(
            {
                value
                for row in rows
                for value in [_as_float(row.get(feature))]
                if value is not None
            }
        )
        rules.extend(
            {
                "type": "numeric",
                "feature": feature,
                "operator": operator,
                "threshold": value,
            }
            for value in values
            for operator in ("<=", ">=")
        )
    for feature in BOOLEAN_FEATURES:
        values = sorted(
            {
                value
                for row in rows
                for value in [_as_bool(row.get(feature))]
                if value is not None
            }
        )
        rules.extend(
            {
                "type": "boolean",
                "feature": feature,
                "operator": "==",
                "value": value,
            }
            for value in values
        )
    return rules


def _dedupe_atomic_rules(
    rows: list[dict[str, str]],
    rules: list[dict[str, Any]],
) -> list[_AtomicRule]:
    seen: set[tuple[str, int]] = set()
    result: list[_AtomicRule] = []
    for rule in rules:
        mask = _rule_mask(rows, rule)
        # Empty and full rules rarely help selector gating and create many
        # degenerate equivalent pairs; keep the audit focused on real gates.
        if mask == 0 or mask == (1 << len(rows)) - 1:
            continue
        key = (str(rule["feature"]), mask)
        if key in seen:
            continue
        seen.add(key)
        result.append(_AtomicRule(rule=rule, feature=str(rule["feature"]), mask=mask))
    return result


def _metrics_for_mask(mask: int, total_rows: int, positives: int) -> dict[str, Any]:
    tp = (mask & positives).bit_count()
    fp = (mask & ~positives).bit_count()
    fn = positives.bit_count() - tp
    tn = total_rows - tp - fp - fn
    return _evaluate_counts({"tp": tp, "fp": fp, "tn": tn, "fn": fn})


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


def _best_pair_rule(rows: list[dict[str, str]]) -> dict[str, Any] | None:
    atomics = _dedupe_atomic_rules(rows, _candidate_atomic_rules(rows))
    positives = _positive_mask(rows)
    all_mask = (1 << len(rows)) - 1
    best: tuple[tuple[Any, ...], dict[str, Any], dict[str, Any]] | None = None
    pair_count = 0
    for left_index, left in enumerate(atomics):
        for right in atomics[left_index + 1 :]:
            if left.feature == right.feature:
                continue
            for logic, mask in (
                ("and", left.mask & right.mask),
                ("or", left.mask | right.mask),
            ):
                if mask == 0 or mask == all_mask:
                    continue
                pair_count += 1
                metrics = _metrics_for_mask(mask, len(rows), positives)
                key = _rule_sort_key(metrics)
                if best is None or key > best[0]:
                    best = (
                        key,
                        {"type": "pair", "logic": logic, "rules": [left.rule, right.rule]},
                        metrics,
                    )
    if best is None:
        return None
    return {
        "atomic_rule_count": len(atomics),
        "pair_rule_count": pair_count,
        "rule": best[1],
        "metrics": best[2],
    }


def _predict_pair(row: dict[str, str], rule: dict[str, Any]) -> bool:
    values: list[bool] = []
    for atomic in rule["rules"]:
        feature = str(atomic["feature"])
        if atomic["type"] == "numeric":
            value = _as_float(row.get(feature))
            if value is None:
                values.append(False)
                continue
            threshold = float(atomic["threshold"])
            if atomic["operator"] == "<=":
                values.append(value <= threshold)
            else:
                values.append(value >= threshold)
        else:
            value = _as_bool(row.get(feature))
            values.append(value is not None and value is bool(atomic["value"]))
    if rule["logic"] == "and":
        return all(values)
    return any(values)


def _evaluate_pair_rule(rows: list[dict[str, str]], rule: dict[str, Any]) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row in rows:
        pred = _predict_pair(row, rule)
        positive = row.get("single_impact_class") == "improved"
        if pred and positive:
            tp += 1
        elif pred and not positive:
            fp += 1
        elif not pred and positive:
            fn += 1
        else:
            tn += 1
    return _evaluate_counts({"tp": tp, "fp": fp, "tn": tn, "fn": fn})


def _micro_average(metrics_list: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {
        "tp": sum(int(metrics.get("tp", 0)) for metrics in metrics_list),
        "fp": sum(int(metrics.get("fp", 0)) for metrics in metrics_list),
        "tn": sum(int(metrics.get("tn", 0)) for metrics in metrics_list),
        "fn": sum(int(metrics.get("fn", 0)) for metrics in metrics_list),
    }
    return _evaluate_counts(counts)


def _holdout_pair_metrics(
    rows: list[dict[str, str]],
    *,
    holdout_key: str,
) -> dict[str, Any]:
    groups = sorted({str(row.get(holdout_key, "")) for row in rows})
    folds: list[dict[str, Any]] = []
    for group in groups:
        train = [row for row in rows if str(row.get(holdout_key, "")) != group]
        test = [row for row in rows if str(row.get(holdout_key, "")) == group]
        best = _best_pair_rule(train)
        if best is None:
            continue
        test_metrics = _evaluate_pair_rule(test, best["rule"])
        folds.append(
            {
                "holdout": group,
                "rule": best["rule"],
                "train": best["metrics"],
                "test": test_metrics,
                "atomic_rule_count": best["atomic_rule_count"],
                "pair_rule_count": best["pair_rule_count"],
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
        "logic_choices": _count_rule_choices(folds, "logic"),
        "feature_pair_choices": _count_feature_pairs(folds),
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


def _count_rule_choices(folds: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for fold in folds:
        value = str(fold["rule"].get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return counts


def _count_feature_pairs(folds: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for fold in folds:
        features = sorted(str(rule["feature"]) for rule in fold["rule"]["rules"])
        key = "+".join(features)
        counts[key] = counts.get(key, 0) + 1
    return counts


def analyze_pair_selector_gate(paths: list[Path]) -> dict[str, Any]:
    rows = _read_rows(paths)
    full_best = _best_pair_rule(rows)
    holdouts = {
        holdout_key: _holdout_pair_metrics(rows, holdout_key=holdout_key)
        for holdout_key in HOLDOUT_KEYS
    }
    label_counts: dict[str, int] = {}
    for row in rows:
        label = str(row["single_impact_class"])
        label_counts[label] = label_counts.get(label, 0) + 1
    full_metrics = dict(full_best.get("metrics", {})) if full_best else {}
    dataset_micro = holdouts["impact_dataset"]["micro"]
    instance_micro = holdouts["instance"]["micro"]
    context_micro = holdouts["context_hash"]["micro"]
    result = {
        "schema_version": "counterfactual_replay_pair_selector_gate_v1",
        "input_paths": [str(path) for path in paths],
        "row_count": len(rows),
        "label_counts": label_counts,
        "context_count": len({row["context_hash"] for row in rows}),
        "instance_count": len({row["instance"] for row in rows}),
        "impact_dataset_count": len({row["impact_dataset"] for row in rows}),
        "strict_gate": {"precision_min": 0.75, "recall_min": 0.5},
        "features": {
            "numeric": list(NUMERIC_FEATURES),
            "boolean": list(BOOLEAN_FEATURES),
            "excluded_post_treatment": [
                "single_objective_delta",
                "single_dual_l1_delta",
                "single_changed_journey_count",
            ],
        },
        "full_sample_best_pair": full_best,
        "holdout_train_best_pair": holdouts,
    }
    result["checks"] = {
        "has_exact_replay_rows": len(rows) >= 200,
        "has_improved_and_noop_labels": (
            int(label_counts.get("improved", 0)) > 0
            and int(label_counts.get("noop", 0)) > 0
        ),
        "full_sample_pair_rule_looks_promising": _passes_strict_gate(full_metrics),
        "context_holdout_pair_rule_fails": not _passes_strict_gate(context_micro),
        "dataset_holdout_pair_rule_fails": not _passes_strict_gate(dataset_micro),
        "instance_holdout_pair_rule_fails": not _passes_strict_gate(instance_micro),
        "no_pair_rule_passes_all_holdout_gates": not all(
            holdouts[holdout_key]["passes_strict_gate"] for holdout_key in HOLDOUT_KEYS
        ),
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

    result = analyze_pair_selector_gate(list(args.inputs or DEFAULT_INPUTS))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
