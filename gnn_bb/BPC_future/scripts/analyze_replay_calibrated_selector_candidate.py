#!/usr/bin/env python3
"""Audit replay-calibrated addition-before selector candidates.

This script is read-only with respect to solver state.  It consumes exact replay
``candidate_impact_rows.csv`` files and the selector-gate summary produced from
the same rows, then reports which selector candidate is strong enough for a
production A/B experiment and why it is still not production evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_replay_calibrated_selector_candidate_20260613"
)
DEFAULT_SELECTOR_GATE = Path(
    "BPC_future/results/root_cause_counterfactual_replay_selector_gate_with_target002_pt03_20260613/"
    "summary.json"
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
STRICT_PRECISION_MIN = 0.75
STRICT_RECALL_MIN = 0.5


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


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _read_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw_path in paths:
        path = _candidate_csv(raw_path)
        dataset = _dataset_name(path)
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("single_impact_class") not in {"improved", "noop"}:
                    continue
                if not _as_bool(row.get("single_treatment_found")):
                    continue
                copied = dict(row)
                copied["impact_dataset"] = dataset
                copied["impact_source"] = str(path)
                rows.append(copied)
    return rows


def _rule_from_gate(gate: dict[str, Any], feature: str) -> dict[str, Any]:
    return dict(gate["full_sample_best_by_feature"][feature]["rule"])


def _rule_name(rule: dict[str, Any]) -> str:
    feature = str(rule["feature"])
    if rule["type"] == "numeric":
        return f"{feature}_{rule['operator']}_{float(rule['threshold']):.6f}"
    return f"{feature}_is_{str(rule['value']).lower()}"


def _predict_rule(row: dict[str, str], rule: dict[str, Any]) -> bool:
    feature = str(rule["feature"])
    if rule["type"] == "numeric":
        value = _as_float(row.get(feature))
        if value is None:
            return False
        threshold = float(rule["threshold"])
        if rule["operator"] == "<=":
            return value <= threshold + 1.0e-12
        return value >= threshold - 1.0e-12
    return _as_bool(row.get(feature)) is bool(rule["value"])


def _evaluate_rows(rows: list[dict[str, str]], predicate: Callable[[dict[str, str]], bool]) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row in rows:
        pred = bool(predicate(row))
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


def _passes_strict(metrics: dict[str, Any]) -> bool:
    precision = metrics.get("precision")
    recall = metrics.get("recall")
    return (
        precision is not None
        and recall is not None
        and float(precision) >= STRICT_PRECISION_MIN
        and float(recall) >= STRICT_RECALL_MIN
    )


def _holdout_micro(
    rows: list[dict[str, str]],
    key: str,
    predicate: Callable[[dict[str, str]], bool],
) -> dict[str, Any]:
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    groups: list[dict[str, Any]] = []
    for value in sorted({str(row.get(key, "")) for row in rows}):
        group_rows = [row for row in rows if str(row.get(key, "")) == value]
        metrics = _evaluate_rows(group_rows, predicate)
        for field in counts:
            counts[field] += int(metrics[field])
        groups.append({"group": value, **metrics, "passes_strict_gate": _passes_strict(metrics)})
    micro = _evaluate_counts(counts)
    return {
        "holdout_key": key,
        "group_count": len(groups),
        "micro": micro,
        "passes_strict_gate": _passes_strict(micro),
        "passing_group_count": sum(1 for item in groups if item["passes_strict_gate"]),
        "worst_groups": sorted(
            groups,
            key=lambda item: (
                -1.0 if item.get("precision") is None else float(item["precision"]),
                -1.0 if item.get("recall") is None else float(item["recall"]),
            ),
        )[:8],
    }


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


def _case_metrics(
    rows: list[dict[str, str]],
    predicate: Callable[[dict[str, str]], bool],
) -> dict[str, Any]:
    by_case: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_case[(str(row.get("impact_dataset", "")), str(row.get("case_id", "")))].append(row)
    selected_only_noop: list[dict[str, Any]] = []
    missed_positive: list[dict[str, Any]] = []
    counts = Counter()
    for (dataset, case_id), case_rows in sorted(by_case.items()):
        selected = [row for row in case_rows if predicate(row)]
        positives = [row for row in case_rows if row.get("single_impact_class") == "improved"]
        selected_positive = [
            row for row in selected if row.get("single_impact_class") == "improved"
        ]
        selected_noop = [row for row in selected if row.get("single_impact_class") == "noop"]
        if positives:
            counts["cases_with_positive"] += 1
        if selected:
            counts["cases_with_selected"] += 1
        if selected_positive:
            counts["cases_with_selected_positive"] += 1
        if selected_noop and not selected_positive:
            counts["selected_only_noop"] += 1
            selected_only_noop.append(
                {
                    "impact_dataset": dataset,
                    "case_id": case_id,
                    "selected_noop_count": len(selected_noop),
                    "positive_count": len(positives),
                }
            )
        if positives and not selected_positive:
            counts["missed_positive_case"] += 1
            missed_positive.append(
                {
                    "impact_dataset": dataset,
                    "case_id": case_id,
                    "positive_count": len(positives),
                    "selected_count": len(selected),
                    "best_positive_true_rc": min(
                        (
                            _as_float(row.get("true_reduced_cost"))
                            for row in positives
                            if _as_float(row.get("true_reduced_cost")) is not None
                        ),
                        default=None,
                    ),
                }
            )
    counts["case_count"] = len(by_case)
    return {
        **dict(counts),
        "selected_only_noop_examples": selected_only_noop[:12],
        "missed_positive_examples": missed_positive[:12],
    }


def _compact_row(row: dict[str, str]) -> dict[str, Any]:
    return {
        "impact_dataset": row.get("impact_dataset"),
        "case_id": row.get("case_id"),
        "candidate_id": row.get("candidate_id"),
        "instance": row.get("instance"),
        "context_hash": row.get("context_hash"),
        "task_set": row.get("task_set"),
        "sequence": row.get("sequence"),
        "true_reduced_cost": _as_float(row.get("true_reduced_cost")),
        "cost": _as_float(row.get("cost")),
        "new_task_set": _as_bool(row.get("new_task_set")),
        "strict_replacement_by_cost": _as_bool(row.get("strict_replacement_by_cost")),
        "active_support_changing": _as_bool(row.get("active_support_changing")),
        "single_objective_delta": _as_float(row.get("single_objective_delta")),
        "single_impact_class": row.get("single_impact_class"),
    }


def _evaluate_candidate(
    rows: list[dict[str, str]],
    *,
    name: str,
    rule: dict[str, Any],
) -> dict[str, Any]:
    predicate = lambda row: _predict_rule(row, rule)
    selected = [row for row in rows if predicate(row)]
    false_positives = [
        row
        for row in selected
        if row.get("single_impact_class") == "noop"
    ]
    false_negatives = [
        row
        for row in rows
        if not predicate(row) and row.get("single_impact_class") == "improved"
    ]
    return {
        "name": name,
        "rule": rule,
        "full_sample": _evaluate_rows(rows, predicate),
        "holdouts": {
            key: _holdout_micro(rows, key, predicate)
            for key in ("context_hash", "instance", "impact_dataset")
        },
        "per_dataset": {
            dataset: _evaluate_rows(
                [row for row in rows if row.get("impact_dataset") == dataset],
                predicate,
            )
            for dataset in sorted({str(row.get("impact_dataset", "")) for row in rows})
        },
        "case_level": _case_metrics(rows, predicate),
        "false_positive_count": len(false_positives),
        "false_negative_count": len(false_negatives),
        "false_positive_examples": [_compact_row(row) for row in false_positives[:12]],
        "false_negative_examples": [_compact_row(row) for row in false_negatives[:12]],
    }


def analyze_selector_candidate(
    inputs: list[Path],
    selector_gate_summary: Path,
) -> dict[str, Any]:
    rows = _read_rows(inputs)
    gate = json.loads(selector_gate_summary.read_text(encoding="utf-8"))
    passing_features = list(gate.get("passing_features_all_holdouts", []) or [])
    rules = {
        feature: _rule_from_gate(gate, feature)
        for feature in passing_features
    }
    candidates = {
        _rule_name(rule): _evaluate_candidate(rows, name=_rule_name(rule), rule=rule)
        for rule in rules.values()
    }
    recommended_name = next(
        (
            name
            for name, payload in candidates.items()
            if payload["rule"].get("feature") == "true_reduced_cost"
        ),
        "",
    )
    recommended = candidates.get(recommended_name, {})
    recommended_holdouts_pass = bool(
        recommended
        and all(
            payload["passes_strict_gate"]
            for payload in recommended.get("holdouts", {}).values()
        )
    )
    label_counts = dict(Counter(row["single_impact_class"] for row in rows))
    result = {
        "schema_version": "replay_calibrated_selector_candidate_v1",
        "input_paths": [str(_candidate_csv(path)) for path in inputs],
        "selector_gate_summary": str(selector_gate_summary),
        "row_count": len(rows),
        "label_counts": label_counts,
        "strict_gate": {
            "precision_min": STRICT_PRECISION_MIN,
            "recall_min": STRICT_RECALL_MIN,
        },
        "passing_features_all_holdouts": passing_features,
        "candidate_rules": candidates,
        "recommended_selector_candidate": recommended_name,
        "recommended_selector_rule": recommended.get("rule"),
        "recommended_selector_full_sample": recommended.get("full_sample"),
        "recommended_selector_case_level": recommended.get("case_level"),
        "recommended_selector_false_positive_count": recommended.get("false_positive_count"),
        "recommended_selector_false_negative_count": recommended.get("false_negative_count"),
        "production_validation": {
            "production_validated_selector": False,
            "required_next_step": (
                "Run full BPC A/B with this addition-before selector: 5/10 no-regression "
                "gate plus selected 20-task hard-repeat wall-time/gap/status/tail gate."
            ),
            "must_not_treat_as_certificate": True,
        },
    }
    result["checks"] = {
        "has_expected_rows": len(rows) == 280,
        "has_expected_labels": label_counts.get("improved") == 209
        and label_counts.get("noop") == 71,
        "has_passing_single_feature_candidates": bool(passing_features),
        "true_rc_candidate_selected": bool(recommended_name),
        "true_rc_candidate_passes_all_micro_holdouts": recommended_holdouts_pass,
        "true_rc_candidate_has_false_positives": int(
            recommended.get("false_positive_count") or 0
        )
        > 0,
        "true_rc_candidate_has_false_negatives": int(
            recommended.get("false_negative_count") or 0
        )
        > 0,
        "production_validation_still_missing": (
            result["production_validation"]["production_validated_selector"] is False
        ),
    }
    result["all_checks_pass"] = all(result["checks"].values())
    return result


def _write_candidate_rows(
    path: Path,
    rows: list[dict[str, Any]],
) -> None:
    fieldnames = [
        "impact_dataset",
        "case_id",
        "candidate_id",
        "instance",
        "context_hash",
        "task_set",
        "sequence",
        "true_reduced_cost",
        "cost",
        "new_task_set",
        "strict_replacement_by_cost",
        "active_support_changing",
        "single_objective_delta",
        "single_impact_class",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="*", type=Path, default=list(DEFAULT_INPUTS))
    parser.add_argument("--selector-gate-summary", type=Path, default=DEFAULT_SELECTOR_GATE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    result = analyze_selector_candidate(
        list(args.inputs or DEFAULT_INPUTS),
        args.selector_gate_summary,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    recommended = result["candidate_rules"].get(result["recommended_selector_candidate"], {})
    _write_candidate_rows(
        args.output_dir / "recommended_false_positive_examples.csv",
        list(recommended.get("false_positive_examples", []) or []),
    )
    _write_candidate_rows(
        args.output_dir / "recommended_false_negative_examples.csv",
        list(recommended.get("false_negative_examples", []) or []),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

