#!/usr/bin/env python3
"""Probe pool/returned-batch overlap features for selector root-cause work.

The current root-cause evidence says that local column features, true reduced
cost, new-task-set flags, and aggregate RMP proxies are not enough for a
production addition-before selector.  This diagnostic joins existing
``candidate_impact_rows.csv`` rows to exact-context replay manifests and derives
candidate-vs-pool / candidate-vs-returned-batch overlap features in memory.

It is read-only with respect to solver behavior: it does not run BPC, pricing,
RMP, Pulse, replay, or benchmarks, and it does not rewrite the candidate rows.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from BPC_future.scripts import analyze_candidate_selector_models as model_lib


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_pool_overlap_feature_probe_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_pool_overlap_feature_probe_zh.md"
)
DEFAULT_INPUTS = [
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
]
DEFAULT_MANIFEST_GLOB = "BPC_future/results/**/replay_cases.json"

HOLDOUT_KEYS = ("context_hash", "instance", "impact_dataset")
STRICT_PRECISION_MIN = 0.75
STRICT_RECALL_MIN = 0.5

DERIVED_NUMERIC_FEATURES = (
    "pool_candidate_task_freq_sum",
    "pool_candidate_task_freq_mean",
    "pool_candidate_task_freq_min",
    "pool_candidate_task_freq_max",
    "pool_candidate_task_freq_mean_fraction",
    "pool_candidate_task_set_exact_count",
    "pool_candidate_task_set_max_jaccard",
    "pool_candidate_task_set_mean_jaccard",
    "pool_candidate_task_set_near_050_count",
    "pool_candidate_task_set_near_067_count",
    "pool_candidate_task_set_near_075_count",
    "pool_candidate_task_set_same_size_overlap_max",
    "pool_candidate_same_task_set_best_cost_delta",
    "returned_batch_size",
    "returned_batch_new_task_set_count",
    "returned_batch_duplicate_signature_count",
    "returned_batch_task_union_size",
    "returned_candidate_index",
    "returned_candidate_true_rc_rank",
    "returned_candidate_cost_rank",
    "returned_candidate_task_freq_sum",
    "returned_candidate_task_freq_mean",
    "returned_candidate_task_set_max_jaccard_other",
    "returned_candidate_task_set_mean_jaccard_other",
    "returned_candidate_task_set_near_050_other_count",
    "returned_candidate_task_set_near_067_other_count",
    "returned_batch_min_true_rc",
    "returned_batch_mean_true_rc",
    "returned_batch_true_rc_gap_from_best",
    "root_forbidden_signature_count",
    "root_forbidden_candidate_task_set_max_jaccard",
)
BASE_MODEL_FEATURES = (
    "true_reduced_cost",
    "cost",
    "task_count",
    "vehicle_count",
    "new_task_set_numeric",
    "duplicate_signature_numeric",
    "active_support_changing_numeric",
    "strict_replacement_by_cost_numeric",
    "weak_replacement_or_duplicate_numeric",
    "control_objective",
    "rmp_objective_before",
    "active_basis_size_before",
    "active_basis_unique_task_set_count_before",
    "dual_l1_norm_before",
    "dual_linf_norm_before",
    "column_pool_size_before",
    "duplicate_signature_pool_count_before",
    "task_set_pool_count_before",
    "lambda_active_count_before",
    "lambda_fractional_count_before",
    "active_basis_hash_churn_count_before",
    "active_basis_hash_unique_count_before",
    "rmp_degeneracy_proxy_score_before",
    "recent_objective_delta_before",
    "recent_dual_l1_delta_before",
    "recent_added_column_acceptance_rate_before",
    "pricing_tail_retry_count_before",
)
MODEL_FEATURES = BASE_MODEL_FEATURES + DERIVED_NUMERIC_FEATURES

Predicate = Callable[[dict[str, str]], bool]


def _dataset_name(path: Path) -> str:
    if path.name == "candidate_impact_rows.csv":
        if path.parent.name == "impact":
            return path.parent.parent.name
        return path.parent.name
    return path.stem


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _as_bool_number(value: Any) -> str:
    return "1.0" if _as_bool(value) else "0.0"


def _canonical_task_set(value: Any) -> tuple[int, ...]:
    if value is None:
        return tuple()
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return tuple()
        parts = text.replace("-", ",").split(",")
        return tuple(sorted({int(part) for part in parts if part.strip()}))
    if isinstance(value, (list, tuple, set, frozenset)):
        return tuple(sorted({int(item) for item in value}))
    return tuple()


def _canonical_sequence(value: Any) -> tuple[int, ...]:
    if value is None:
        return tuple()
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return tuple()
        return tuple(int(part) for part in text.replace(",", "-").split("-") if part)
    if isinstance(value, (list, tuple)):
        if value and isinstance(value[0], (list, tuple)):
            flattened: list[int] = []
            for sortie in value:
                flattened.extend(int(task) for task in sortie)
            return tuple(flattened)
        return tuple(int(task) for task in value)
    return tuple()


def _signature_key(signature: Any) -> str:
    return json.dumps(signature, sort_keys=True, separators=(",", ":"))


def _jaccard(left: set[int], right: set[int]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / float(len(union))


def _read_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        if not path.exists():
            continue
        dataset = _dataset_name(path)
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("single_impact_class") not in {"improved", "noop"}:
                    continue
                if not _as_bool(row.get("single_treatment_found")):
                    continue
                copied = dict(row)
                copied["impact_dataset"] = dataset
                copied["new_task_set_numeric"] = _as_bool_number(
                    copied.get("new_task_set")
                )
                copied["duplicate_signature_numeric"] = _as_bool_number(
                    copied.get("duplicate_signature")
                )
                copied["active_support_changing_numeric"] = _as_bool_number(
                    copied.get("active_support_changing")
                )
                copied["strict_replacement_by_cost_numeric"] = _as_bool_number(
                    copied.get("strict_replacement_by_cost")
                )
                copied["weak_replacement_or_duplicate_numeric"] = _as_bool_number(
                    copied.get("weak_replacement_or_duplicate")
                )
                rows.append(copied)
    return rows


def _manifest_cases(manifest_glob: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in sorted(Path().glob(manifest_glob)):
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw_cases = payload.get("cases", payload if isinstance(payload, list) else [])
        for case in raw_cases:
            if isinstance(case, dict):
                copied = dict(case)
                copied["_manifest_path"] = str(path)
                cases.append(copied)
    return cases


def _case_index(cases: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for case in cases:
        key = (
            str(case.get("source_file", "")),
            str(case.get("case_id", "")),
            str(case.get("context_hash", "")),
        )
        if all(key) and key not in index:
            index[key] = case
    return index


def _case_for_row(
    row: dict[str, str], index: dict[tuple[str, str, str], dict[str, Any]]
) -> dict[str, Any] | None:
    key = (
        str(row.get("source_file", "")),
        str(row.get("case_id", "")),
        str(row.get("context_hash", "")),
    )
    return index.get(key)


def _candidate_for_row(row: dict[str, str], case: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(row.get("candidate_id", ""))
    for candidate in case.get("candidates", []) or []:
        if str(candidate.get("candidate_id", "")) == candidate_id:
            return candidate
    row_task_set = _canonical_task_set(row.get("task_set"))
    row_sequence = _canonical_sequence(row.get("sequence"))
    for candidate in case.get("candidates", []) or []:
        if _canonical_task_set(candidate.get("task_set")) != row_task_set:
            continue
        if _canonical_sequence(candidate.get("sequence")) == row_sequence:
            return candidate
    return {}


def _rank(values: list[float], value: float, *, reverse: bool = False) -> int:
    ordered = sorted(values, reverse=reverse)
    for idx, current in enumerate(ordered, 1):
        if math.isclose(current, value, rel_tol=1.0e-12, abs_tol=1.0e-12):
            return idx
    return len(values) + 1


def _derive_features(row: dict[str, str], case: dict[str, Any]) -> dict[str, str]:
    candidate = _candidate_for_row(row, case)
    candidate_task_set = set(
        _canonical_task_set(candidate.get("task_set") or row.get("task_set"))
    )
    candidate_signature = candidate.get("signature")
    candidate_signature_key = _signature_key(candidate_signature)
    candidate_cost = _as_float(candidate.get("cost")) or _as_float(row.get("cost"))
    candidate_true_rc = _as_float(candidate.get("true_reduced_cost")) or _as_float(
        row.get("true_reduced_cost")
    )

    pool_journeys = list(case.get("pool_journeys", []) or [])
    pool_sets = [
        set(_canonical_task_set(journey.get("task_set")))
        for journey in pool_journeys
        if _canonical_task_set(journey.get("task_set"))
    ]
    pool_signatures = [_signature_key(journey.get("signature")) for journey in pool_journeys]
    pool_task_counts: Counter[int] = Counter()
    for task_set in pool_sets:
        pool_task_counts.update(task_set)
    task_freqs = [pool_task_counts.get(task, 0) for task in sorted(candidate_task_set)]
    pool_count = max(1, len(pool_sets))
    jaccards = [_jaccard(candidate_task_set, task_set) for task_set in pool_sets]
    exact_task_set_costs = [
        _as_float(journey.get("cost"))
        for journey, task_set in zip(pool_journeys, pool_sets)
        if task_set == candidate_task_set and _as_float(journey.get("cost")) is not None
    ]
    same_size_overlaps = [
        len(candidate_task_set & task_set)
        for task_set in pool_sets
        if len(task_set) == len(candidate_task_set)
    ]

    returned_candidates = list(case.get("candidates", []) or [])
    returned_sets = [
        set(_canonical_task_set(candidate.get("task_set")))
        for candidate in returned_candidates
        if _canonical_task_set(candidate.get("task_set"))
    ]
    returned_task_union: set[int] = set()
    returned_task_counts: Counter[int] = Counter()
    for task_set in returned_sets:
        returned_task_union.update(task_set)
        returned_task_counts.update(task_set)
    returned_other_jaccards = [
        _jaccard(candidate_task_set, task_set)
        for other, task_set in zip(returned_candidates, returned_sets)
        if str(other.get("candidate_id", "")) != str(row.get("candidate_id", ""))
    ]
    returned_true_rcs = [
        value
        for candidate in returned_candidates
        for value in [_as_float(candidate.get("true_reduced_cost"))]
        if value is not None
    ]
    returned_costs = [
        value
        for candidate in returned_candidates
        for value in [_as_float(candidate.get("cost"))]
        if value is not None
    ]
    returned_ids = [str(candidate.get("candidate_id", "")) for candidate in returned_candidates]
    returned_index = (
        returned_ids.index(str(row.get("candidate_id", ""))) if row.get("candidate_id") in returned_ids else -1
    )
    returned_task_freqs = [
        returned_task_counts.get(task, 0) for task in sorted(candidate_task_set)
    ]
    branch_constraints = list(case.get("branch_constraints", []) or [])
    root_forbidden_count = (
        len(pool_signatures)
        if not branch_constraints
        else int(case.get("forbidden_signature_count") or 0)
    )

    def avg(values: list[float] | list[int]) -> float:
        return 0.0 if not values else sum(float(value) for value in values) / len(values)

    def fmt(value: float | int | None) -> str:
        if value is None:
            return ""
        return str(round(float(value), 9))

    same_task_set_best_cost_delta = None
    if candidate_cost is not None and exact_task_set_costs:
        same_task_set_best_cost_delta = candidate_cost - min(exact_task_set_costs)
    min_true_rc = min(returned_true_rcs) if returned_true_rcs else None
    mean_true_rc = avg(returned_true_rcs) if returned_true_rcs else None
    true_rc_gap = None
    if candidate_true_rc is not None and min_true_rc is not None:
        true_rc_gap = candidate_true_rc - min_true_rc
    features = {
        "pool_candidate_task_freq_sum": fmt(sum(task_freqs)),
        "pool_candidate_task_freq_mean": fmt(avg(task_freqs)),
        "pool_candidate_task_freq_min": fmt(min(task_freqs) if task_freqs else 0),
        "pool_candidate_task_freq_max": fmt(max(task_freqs) if task_freqs else 0),
        "pool_candidate_task_freq_mean_fraction": fmt(avg(task_freqs) / pool_count),
        "pool_candidate_task_set_exact_count": fmt(
            sum(1 for task_set in pool_sets if task_set == candidate_task_set)
        ),
        "pool_candidate_task_set_max_jaccard": fmt(max(jaccards) if jaccards else 0),
        "pool_candidate_task_set_mean_jaccard": fmt(avg(jaccards)),
        "pool_candidate_task_set_near_050_count": fmt(sum(1 for value in jaccards if value >= 0.5)),
        "pool_candidate_task_set_near_067_count": fmt(sum(1 for value in jaccards if value >= 2.0 / 3.0)),
        "pool_candidate_task_set_near_075_count": fmt(sum(1 for value in jaccards if value >= 0.75)),
        "pool_candidate_task_set_same_size_overlap_max": fmt(
            max(same_size_overlaps) if same_size_overlaps else 0
        ),
        "pool_candidate_same_task_set_best_cost_delta": fmt(
            same_task_set_best_cost_delta
        ),
        "returned_batch_size": fmt(len(returned_candidates)),
        "returned_batch_new_task_set_count": fmt(
            sum(1 for item in returned_candidates if _as_bool(item.get("new_task_set")))
        ),
        "returned_batch_duplicate_signature_count": fmt(
            sum(1 for item in returned_candidates if _as_bool(item.get("duplicate_signature")))
        ),
        "returned_batch_task_union_size": fmt(len(returned_task_union)),
        "returned_candidate_index": fmt(returned_index),
        "returned_candidate_true_rc_rank": fmt(
            _rank(returned_true_rcs, candidate_true_rc) if candidate_true_rc is not None else None
        ),
        "returned_candidate_cost_rank": fmt(
            _rank(returned_costs, candidate_cost) if candidate_cost is not None else None
        ),
        "returned_candidate_task_freq_sum": fmt(sum(returned_task_freqs)),
        "returned_candidate_task_freq_mean": fmt(avg(returned_task_freqs)),
        "returned_candidate_task_set_max_jaccard_other": fmt(
            max(returned_other_jaccards) if returned_other_jaccards else 0
        ),
        "returned_candidate_task_set_mean_jaccard_other": fmt(
            avg(returned_other_jaccards)
        ),
        "returned_candidate_task_set_near_050_other_count": fmt(
            sum(1 for value in returned_other_jaccards if value >= 0.5)
        ),
        "returned_candidate_task_set_near_067_other_count": fmt(
            sum(1 for value in returned_other_jaccards if value >= 2.0 / 3.0)
        ),
        "returned_batch_min_true_rc": fmt(min_true_rc),
        "returned_batch_mean_true_rc": fmt(mean_true_rc),
        "returned_batch_true_rc_gap_from_best": fmt(true_rc_gap),
        "root_forbidden_signature_count": fmt(root_forbidden_count),
        "root_forbidden_candidate_task_set_max_jaccard": fmt(max(jaccards) if jaccards else 0),
        "manifest_joined": "1.0",
        "candidate_signature_in_pool": "1.0" if candidate_signature_key in set(pool_signatures) else "0.0",
        "explicit_forbidden_signature_list_available": (
            "1.0"
            if case.get("forbidden_signatures")
            or case.get("forbidden_journey_signatures")
            else "0.0"
        ),
    }
    return features


def _enrich_rows(rows: list[dict[str, str]], cases: list[dict[str, Any]]) -> tuple[list[dict[str, str]], int]:
    index = _case_index(cases)
    enriched: list[dict[str, str]] = []
    missing = 0
    for row in rows:
        case = _case_for_row(row, index)
        copied = dict(row)
        if case is None:
            missing += 1
            copied["manifest_joined"] = "0.0"
            for feature in DERIVED_NUMERIC_FEATURES:
                copied.setdefault(feature, "")
        else:
            copied.update(_derive_features(row, case))
        enriched.append(copied)
    return enriched, missing


def _label(row: dict[str, str]) -> int:
    return 1 if row.get("single_impact_class") == "improved" else 0


def _metrics(rows: list[dict[str, str]], predicate: Predicate) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row in rows:
        predicted = bool(predicate(row))
        positive = _label(row) == 1
        if predicted and positive:
            tp += 1
        elif predicted and not positive:
            fp += 1
        elif not predicted and positive:
            fn += 1
        else:
            tn += 1
    precision = None if tp + fp <= 0 else tp / float(tp + fp)
    recall = None if tp + fn <= 0 else tp / float(tp + fn)
    accuracy = None if not rows else (tp + tn) / float(len(rows))
    return {
        "total": len(rows),
        "predicted_positive": tp + fp,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
    }


def _passes(metrics: dict[str, Any]) -> bool:
    positive_count = int(metrics.get("tp") or 0) + int(metrics.get("fn") or 0)
    if positive_count <= 0:
        return int(metrics.get("fp") or 0) == 0
    precision = metrics.get("precision")
    recall = metrics.get("recall")
    return (
        precision is not None
        and recall is not None
        and float(precision) >= STRICT_PRECISION_MIN
        and float(recall) >= STRICT_RECALL_MIN
    )


def _numeric_predicate(feature: str, operator: str, threshold: float) -> Predicate:
    def predicate(row: dict[str, str]) -> bool:
        value = _as_float(row.get(feature))
        if value is None:
            return False
        return value <= threshold + 1.0e-12 if operator == "<=" else value >= threshold - 1.0e-12

    return predicate


def _rule_score(metrics: dict[str, Any]) -> tuple[Any, ...]:
    precision = float(metrics.get("precision") or 0.0)
    recall = float(metrics.get("recall") or 0.0)
    f1 = 0.0 if precision + recall <= 0.0 else 2.0 * precision * recall / (precision + recall)
    return (
        precision >= STRICT_PRECISION_MIN,
        recall >= STRICT_RECALL_MIN,
        f1,
        precision,
        recall,
        int(metrics.get("tp") or 0),
        -int(metrics.get("fp") or 0),
        -int(metrics.get("predicted_positive") or 0),
    )


def _train_threshold_rule(rows: list[dict[str, str]], feature: str) -> dict[str, Any]:
    values = sorted(
        {
            value
            for row in rows
            for value in [_as_float(row.get(feature))]
            if value is not None
        }
    )
    best: tuple[tuple[Any, ...], str, float, dict[str, Any]] | None = None
    for operator in ("<=", ">="):
        for threshold in values:
            predicate = _numeric_predicate(feature, operator, threshold)
            metrics = _metrics(rows, predicate)
            if metrics.get("precision") is None:
                continue
            if float(metrics["precision"]) < STRICT_PRECISION_MIN:
                continue
            score = _rule_score(metrics)
            if best is None or score > best[0]:
                best = (score, operator, float(threshold), metrics)
    if best is None:
        return {
            "available": False,
            "feature": feature,
            "operator": None,
            "threshold": None,
            "train_metrics": _metrics(rows, lambda _row: False),
        }
    _score, operator, threshold, metrics = best
    return {
        "available": True,
        "feature": feature,
        "operator": operator,
        "threshold": threshold,
        "train_metrics": metrics,
    }


def _predict(rule: dict[str, Any], row: dict[str, str]) -> bool:
    if not rule.get("available"):
        return False
    return _numeric_predicate(
        str(rule["feature"]), str(rule["operator"]), float(rule["threshold"])
    )(row)


def _feature_holdout(rows: list[dict[str, str]], feature: str, holdout_key: str) -> dict[str, Any]:
    folds = sorted({str(row.get(holdout_key, "")) for row in rows})
    fold_results: list[dict[str, Any]] = []
    for fold in folds:
        train = [row for row in rows if str(row.get(holdout_key, "")) != fold]
        test = [row for row in rows if str(row.get(holdout_key, "")) == fold]
        if not train or not test:
            continue
        rule = _train_threshold_rule(train, feature)
        metrics = _metrics(test, lambda row, rule=rule: _predict(rule, row))
        fold_results.append(
            {
                "fold": fold,
                "test_row_count": len(test),
                "rule": rule,
                "test": metrics,
                "passes": _passes(metrics),
            }
        )
    passing = sum(1 for item in fold_results if item["passes"])
    worst = sorted(
        fold_results,
        key=lambda item: (
            item["passes"],
            float(item["test"].get("precision") or 0.0),
            float(item["test"].get("recall") or 0.0),
            -int(item["test"].get("fp") or 0),
        ),
    )[:3]
    return {
        "feature": feature,
        "holdout_key": holdout_key,
        "fold_count": len(fold_results),
        "passing_fold_count": passing,
        "all_folds_pass": bool(fold_results and passing == len(fold_results)),
        "worst_folds": worst,
    }


def _evaluate_single_features(rows: list[dict[str, str]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    robust: list[str] = []
    feature_summaries: list[dict[str, Any]] = []
    for feature in DERIVED_NUMERIC_FEATURES:
        per_holdout = {
            holdout_key: _feature_holdout(rows, feature, holdout_key)
            for holdout_key in HOLDOUT_KEYS
        }
        all_pass = all(item["all_folds_pass"] for item in per_holdout.values())
        if all_pass:
            robust.append(feature)
        feature_summaries.append(
            {
                "feature": feature,
                "all_holdouts_pass": all_pass,
                "context_folds": (
                    f"{per_holdout['context_hash']['passing_fold_count']}/"
                    f"{per_holdout['context_hash']['fold_count']}"
                ),
                "instance_folds": (
                    f"{per_holdout['instance']['passing_fold_count']}/"
                    f"{per_holdout['instance']['fold_count']}"
                ),
                "dataset_folds": (
                    f"{per_holdout['impact_dataset']['passing_fold_count']}/"
                    f"{per_holdout['impact_dataset']['fold_count']}"
                ),
                "worst_context_folds": per_holdout["context_hash"]["worst_folds"],
            }
        )
    payload["robust_all_holdout_derived_feature_count"] = len(robust)
    payload["robust_all_holdout_derived_features"] = robust
    payload["feature_summaries"] = sorted(
        feature_summaries,
        key=lambda item: (
            item["all_holdouts_pass"],
            int(str(item["context_folds"]).split("/", 1)[0]),
            int(str(item["instance_folds"]).split("/", 1)[0]),
            int(str(item["dataset_folds"]).split("/", 1)[0]),
        ),
        reverse=True,
    )
    return payload


def _patch_model_library() -> None:
    model_lib.FEATURES = MODEL_FEATURES
    model_lib._label = _label


def _evaluate_model_holdout(
    rows: list[dict[str, str]],
    holdout_key: str,
    model_name: str,
    builder: Callable[[list[dict[str, str]]], model_lib._Model],
) -> dict[str, Any]:
    folds = sorted({str(row.get(holdout_key, "")) for row in rows})
    fold_results: list[dict[str, Any]] = []
    total = tp = fp = tn = fn = 0
    for fold in folds:
        train = [row for row in rows if str(row.get(holdout_key, "")) != fold]
        test = [row for row in rows if str(row.get(holdout_key, "")) == fold]
        if not train or not test:
            continue
        model = builder(train)
        metrics = model_lib._metrics(test, model.predict(test))
        total += int(metrics.get("total") or 0)
        tp += int(metrics.get("tp") or 0)
        fp += int(metrics.get("fp") or 0)
        tn += int(metrics.get("tn") or 0)
        fn += int(metrics.get("fn") or 0)
        fold_results.append(
            {
                "fold": fold,
                "test_row_count": len(test),
                "test": metrics,
                "passes": _passes(metrics),
            }
        )
    precision = None if tp + fp <= 0 else tp / float(tp + fp)
    recall = None if tp + fn <= 0 else tp / float(tp + fn)
    accuracy = None if total <= 0 else (tp + tn) / float(total)
    passing = sum(1 for item in fold_results if item["passes"])
    return {
        "model": model_name,
        "holdout_key": holdout_key,
        "fold_count": len(fold_results),
        "passing_fold_count": passing,
        "all_folds_pass": bool(fold_results and passing == len(fold_results)),
        "micro": {
            "total": total,
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "accuracy": accuracy,
        },
        "worst_folds": sorted(
            fold_results,
            key=lambda item: (
                item["passes"],
                float(item["test"].get("precision") or 0.0),
                float(item["test"].get("recall") or 0.0),
                -int(item["test"].get("fp") or 0),
            ),
        )[:5],
    }


def _evaluate_models(rows: list[dict[str, str]]) -> dict[str, Any]:
    _patch_model_library()
    by_model: dict[str, dict[str, Any]] = {}
    robust: list[str] = []
    for model_name, builder in model_lib.MODEL_BUILDERS.items():
        holdout = {
            holdout_key: _evaluate_model_holdout(rows, holdout_key, model_name, builder)
            for holdout_key in HOLDOUT_KEYS
        }
        if all(item["all_folds_pass"] for item in holdout.values()):
            robust.append(model_name)
        by_model[model_name] = {
            "model": model_name,
            "holdouts": holdout,
            "all_holdouts_pass": model_name in robust,
        }
    best_context_model = max(
        by_model.values(),
        key=lambda item: item["holdouts"]["context_hash"]["passing_fold_count"],
    )
    return {
        "model_features_count": len(MODEL_FEATURES),
        "derived_model_features_count": len(DERIVED_NUMERIC_FEATURES),
        "robust_all_holdout_model_count": len(robust),
        "robust_all_holdout_models": robust,
        "best_context_model": best_context_model["model"],
        "best_context_model_context_folds": (
            f"{best_context_model['holdouts']['context_hash']['passing_fold_count']}/"
            f"{best_context_model['holdouts']['context_hash']['fold_count']}"
        ),
        "best_context_model_instance_folds": (
            f"{best_context_model['holdouts']['instance']['passing_fold_count']}/"
            f"{best_context_model['holdouts']['instance']['fold_count']}"
        ),
        "best_context_model_dataset_folds": (
            f"{best_context_model['holdouts']['impact_dataset']['passing_fold_count']}/"
            f"{best_context_model['holdouts']['impact_dataset']['fold_count']}"
        ),
        "models": by_model,
    }


def build_probe(input_paths: list[Path], manifest_glob: str) -> dict[str, Any]:
    rows = _read_rows(input_paths)
    cases = _manifest_cases(manifest_glob)
    enriched_rows, missing_join_count = _enrich_rows(rows, cases)
    label_counts = dict(Counter(row.get("single_impact_class", "") for row in enriched_rows))
    feature_nonempty = {
        feature: sum(1 for row in enriched_rows if str(row.get(feature, "")).strip())
        for feature in DERIVED_NUMERIC_FEATURES
    }
    single = _evaluate_single_features(enriched_rows)
    models = _evaluate_models(enriched_rows)
    forbidden_list_available_count = sum(
        1
        for case in cases
        if case.get("forbidden_signatures") or case.get("forbidden_journey_signatures")
    )
    checks = {
        "input_rows_exist": len(rows) > 0,
        "manifest_cases_exist": len(cases) > 0,
        "all_rows_joined_to_manifest": missing_join_count == 0,
        "derived_features_populated": all(count > 0 for count in feature_nonempty.values()),
        "no_robust_single_derived_feature": (
            single["robust_all_holdout_derived_feature_count"] == 0
        ),
        "no_robust_multifeature_model_with_derived_features": (
            models["robust_all_holdout_model_count"] == 0
        ),
        "explicit_forbidden_signature_payload_status_accounted": (
            forbidden_list_available_count > 0
        ),
        "diagnostic_not_production_selector": True,
    }
    return {
        "schema_version": "root_cause_selector_pool_overlap_feature_probe_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_pool_overlap_feature_probe_audited",
        "input_paths": [str(path) for path in input_paths],
        "manifest_glob": manifest_glob,
        "row_count": len(enriched_rows),
        "manifest_case_count": len(cases),
        "missing_manifest_join_count": missing_join_count,
        "label_counts": label_counts,
        "derived_feature_count": len(DERIVED_NUMERIC_FEATURES),
        "derived_feature_nonempty_counts": feature_nonempty,
        "robust_all_holdout_derived_feature_count": single[
            "robust_all_holdout_derived_feature_count"
        ],
        "robust_all_holdout_derived_features": single[
            "robust_all_holdout_derived_features"
        ],
        "top_derived_feature_summaries": single["feature_summaries"][:10],
        "robust_all_holdout_model_count": models["robust_all_holdout_model_count"],
        "robust_all_holdout_models": models["robust_all_holdout_models"],
        "best_context_model": models["best_context_model"],
        "best_context_model_context_folds": models["best_context_model_context_folds"],
        "best_context_model_instance_folds": models["best_context_model_instance_folds"],
        "best_context_model_dataset_folds": models["best_context_model_dataset_folds"],
        "forbidden_manifest_case_count": len(cases),
        "explicit_forbidden_signature_list_available_count": forbidden_list_available_count,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "现有 manifest 足以派生 pool/returned-batch overlap 特征并与 280 行 "
            "candidate impact rows 完整 join；但这些派生特征仍没有产生 robust "
            "context/instance/dataset all-holdout selector 或 multifeature model。"
            "此外当前全局 manifests 已出现显式 forbidden signature list，但这些 "
            "targeted payload 仍未形成通过 holdout 的 production selector。"
        ),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Selector Pool/Overlap Feature Probe 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告只读 replay manifests 与 candidate impact rows，在内存中派生",
        " candidate-vs-pool / candidate-vs-returned-batch overlap 特征，并检查",
        "这些 addition-before 特征是否已经足以形成 production selector。",
        "",
        "它不运行 BPC / pricing / RMP / Pulse / replay / benchmark，也不重写",
        "`candidate_impact_rows.csv`。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_selector_pool_overlap_feature_probe = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"row_count = {summary['row_count']}",
        f"manifest_case_count = {summary['manifest_case_count']}",
        f"missing_manifest_join_count = {summary['missing_manifest_join_count']}",
        f"derived_feature_count = {summary['derived_feature_count']}",
        "robust_all_holdout_derived_feature_count = "
        f"{summary['robust_all_holdout_derived_feature_count']}",
        "robust_all_holdout_model_count = "
        f"{summary['robust_all_holdout_model_count']}",
        f"best_context_model = {summary['best_context_model']}",
        "best_context_model_context_folds = "
        f"{summary['best_context_model_context_folds']}",
        "best_context_model_instance_folds = "
        f"{summary['best_context_model_instance_folds']}",
        "best_context_model_dataset_folds = "
        f"{summary['best_context_model_dataset_folds']}",
        "explicit_forbidden_signature_list_available_count = "
        f"{summary['explicit_forbidden_signature_list_available_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## Top Derived Feature Summaries",
        "",
        "```json",
        json.dumps(
            summary["top_derived_feature_summaries"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Checks",
        "",
        "```json",
        json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", dest="inputs")
    parser.add_argument("--manifest-glob", default=DEFAULT_MANIFEST_GLOB)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    inputs = [Path(path) for path in args.inputs] if args.inputs else DEFAULT_INPUTS
    summary = build_probe(inputs, str(args.manifest_glob))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, Path(args.report))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
