#!/usr/bin/env python3
"""Audit holdout robustness of enriched RMP trajectory selector features.

The candidate impact rows now include several addition-before RMP/context
features derived from exact-context replay manifests.  This read-only audit
checks whether those enriched fields are already sufficient to produce a simple
production selector across context, instance, and dataset folds.

It does not run BPC, pricing, RMP, Pulse, replay, or benchmarks.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_enriched_rmp_feature_holdout_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_enriched_rmp_feature_holdout_zh.md"
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

HOLDOUT_KEYS = ("context_hash", "instance", "impact_dataset")
STRICT_PRECISION_MIN = 0.75
STRICT_RECALL_MIN = 0.5
ENRICHED_RMP_FEATURES = (
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
REFERENCE_FEATURES = (
    "true_reduced_cost",
    "cost",
    "control_objective",
    "rmp_objective_before",
)
IDENTITY_DIAGNOSTIC_FEATURES = (
    "active_hash_before",
    "dual_hash_before",
)
ALL_NUMERIC_FEATURES = REFERENCE_FEATURES + ENRICHED_RMP_FEATURES

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
                rows.append(copied)
    return rows


def _metrics(rows: list[dict[str, str]], predicate: Predicate) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row in rows:
        predicted = bool(predicate(row))
        positive = row.get("single_impact_class") == "improved"
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


def _passes_fold(metrics: dict[str, Any]) -> bool:
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
        if operator == "<=":
            return value <= threshold + 1.0e-12
        return value >= threshold - 1.0e-12

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


def _train_threshold_rule(
    rows: list[dict[str, str]], feature: str
) -> dict[str, Any]:
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


def _feature_holdout_summary(
    rows: list[dict[str, str]], feature: str, holdout_key: str
) -> dict[str, Any]:
    folds = sorted({str(row.get(holdout_key, "")) for row in rows})
    fold_results: list[dict[str, Any]] = []
    for fold in folds:
        train_rows = [row for row in rows if str(row.get(holdout_key, "")) != fold]
        test_rows = [row for row in rows if str(row.get(holdout_key, "")) == fold]
        rule = _train_threshold_rule(train_rows, feature)
        metrics = _metrics(test_rows, lambda row, rule=rule: _predict(rule, row))
        fold_results.append(
            {
                "fold": fold,
                "test_row_count": len(test_rows),
                "rule": rule,
                "test": metrics,
                "passes": _passes_fold(metrics),
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
    )[:5]
    full_rule = _train_threshold_rule(rows, feature)
    full_metrics = _metrics(rows, lambda row, rule=full_rule: _predict(rule, row))
    return {
        "feature": feature,
        "holdout_key": holdout_key,
        "fold_count": len(folds),
        "passing_fold_count": passing,
        "failing_fold_count": max(0, len(folds) - passing),
        "all_folds_pass": bool(folds and passing == len(folds)),
        "full_sample_rule": full_rule,
        "full_sample_metrics": full_metrics,
        "worst_folds": worst,
    }


def build_audit(input_paths: list[Path]) -> dict[str, Any]:
    rows = _read_rows(input_paths)
    label_counts = dict(Counter(row.get("single_impact_class", "") for row in rows))
    feature_non_empty_counts = {
        feature: sum(1 for row in rows if str(row.get(feature, "")).strip())
        for feature in ALL_NUMERIC_FEATURES + IDENTITY_DIAGNOSTIC_FEATURES
    }
    holdout_by_feature: dict[str, Any] = {}
    robust_features: list[str] = []
    for feature in ALL_NUMERIC_FEATURES:
        per_holdout = {
            holdout_key: _feature_holdout_summary(rows, feature, holdout_key)
            for holdout_key in HOLDOUT_KEYS
        }
        holdout_by_feature[feature] = per_holdout
        if all(per_holdout[key]["all_folds_pass"] for key in HOLDOUT_KEYS):
            robust_features.append(feature)
    enriched_robust = [feature for feature in robust_features if feature in ENRICHED_RMP_FEATURES]
    best_by_feature = {
        feature: {
            holdout_key: {
                "passing_fold_count": payload["passing_fold_count"],
                "fold_count": payload["fold_count"],
                "all_folds_pass": payload["all_folds_pass"],
            }
            for holdout_key, payload in holdouts.items()
        }
        for feature, holdouts in holdout_by_feature.items()
    }
    checks = {
        "has_rows": bool(rows),
        "expected_row_count": len(rows) == 280,
        "has_improved_and_noop": (
            label_counts.get("improved", 0) > 0 and label_counts.get("noop", 0) > 0
        ),
        "enriched_numeric_fields_present": all(
            feature_non_empty_counts.get(feature, 0) > 0
            for feature in ENRICHED_RMP_FEATURES
        ),
        "identity_fields_present_but_diagnostic_only": all(
            feature_non_empty_counts.get(feature, 0) > 0
            for feature in IDENTITY_DIAGNOSTIC_FEATURES
        ),
        "no_enriched_feature_passes_all_holdouts": not enriched_robust,
        "no_numeric_feature_passes_all_holdouts": not robust_features,
        "control_objective_still_fails_context_folds": (
            holdout_by_feature.get("control_objective", {})
            .get("context_hash", {})
            .get("all_folds_pass")
            is False
        ),
        "rmp_objective_before_still_fails_context_folds": (
            holdout_by_feature.get("rmp_objective_before", {})
            .get("context_hash", {})
            .get("all_folds_pass")
            is False
        ),
    }
    return {
        "schema_version": "selector_enriched_rmp_feature_holdout_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "input_paths": [str(path) for path in input_paths],
        "row_count": len(rows),
        "label_counts": label_counts,
        "holdout_keys": list(HOLDOUT_KEYS),
        "reference_features": list(REFERENCE_FEATURES),
        "enriched_rmp_features": list(ENRICHED_RMP_FEATURES),
        "identity_diagnostic_features": list(IDENTITY_DIAGNOSTIC_FEATURES),
        "feature_non_empty_counts": feature_non_empty_counts,
        "holdout_by_feature": holdout_by_feature,
        "best_by_feature": best_by_feature,
        "robust_all_holdout_numeric_features": robust_features,
        "robust_all_holdout_enriched_features": enriched_robust,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "The newly available RMP/context trajectory fields are valid "
            "addition-before calibration signals, but simple single-feature "
            "train-on-fold threshold rules still fail held-out contexts or "
            "instances. The selector remains calibration-only and is not a "
            "production optimization direction."
        ),
    }


def _fmt_metric(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def write_report(audit: dict[str, Any], path: Path) -> None:
    lines = [
        "# Enriched RMP Feature Holdout 审计",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告检查新进入 candidate rows 的 RMP/context trajectory 字段是否已经足以",
        "形成 production selector。审计只读 `candidate_impact_rows.csv`，不运行 BPC /",
        "pricing / RMP / Pulse。",
        "",
        "## 机器字段",
        "",
        "```text",
        "selector_enriched_rmp_feature_holdout = current",
        f"diagnostic_only = {str(audit['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(audit['runs_bpc_or_pricing']).lower()}",
        f"row_count = {audit['row_count']}",
        f"label_counts = {audit['label_counts']}",
        "enriched_rmp_features = " + ",".join(audit["enriched_rmp_features"]),
        f"robust_all_holdout_enriched_feature_count = {len(audit['robust_all_holdout_enriched_features'])}",
        f"robust_all_holdout_numeric_feature_count = {len(audit['robust_all_holdout_numeric_features'])}",
        f"all_checks_pass = {str(audit['all_checks_pass']).lower()}",
        "```",
        "",
        "## Holdout Summary",
        "",
        "| Feature | Type | Context folds | Instance folds | Dataset folds |",
        "|---|---|---:|---:|---:|",
    ]
    for feature in audit["reference_features"] + audit["enriched_rmp_features"]:
        feature_type = "reference" if feature in audit["reference_features"] else "enriched"
        per = audit["best_by_feature"][feature]
        lines.append(
            "| "
            + " | ".join(
                [
                    feature,
                    feature_type,
                    f"{per['context_hash']['passing_fold_count']}/{per['context_hash']['fold_count']}",
                    f"{per['instance']['passing_fold_count']}/{per['instance']['fold_count']}",
                    f"{per['impact_dataset']['passing_fold_count']}/{per['impact_dataset']['fold_count']}",
                ]
            )
            + " |"
        )
    control_context = audit["holdout_by_feature"]["control_objective"]["context_hash"]
    rmp_context = audit["holdout_by_feature"]["rmp_objective_before"]["context_hash"]
    best_enriched = max(
        audit["enriched_rmp_features"],
        key=lambda feature: (
            audit["best_by_feature"][feature]["context_hash"]["passing_fold_count"],
            audit["best_by_feature"][feature]["instance"]["passing_fold_count"],
            audit["best_by_feature"][feature]["impact_dataset"]["passing_fold_count"],
        ),
    )
    best_enriched_context = audit["holdout_by_feature"][best_enriched]["context_hash"]
    lines.extend(
        [
            "",
            "## 关键数字",
            "",
            "```text",
            "control_objective_context_folds = "
            f"{control_context['passing_fold_count']}/{control_context['fold_count']}",
            "rmp_objective_before_context_folds = "
            f"{rmp_context['passing_fold_count']}/{rmp_context['fold_count']}",
            f"best_enriched_feature = {best_enriched}",
            "best_enriched_context_folds = "
            f"{best_enriched_context['passing_fold_count']}/{best_enriched_context['fold_count']}",
            "robust_all_holdout_enriched_features = "
            + ",".join(audit["robust_all_holdout_enriched_features"]),
            "robust_all_holdout_numeric_features = "
            + ",".join(audit["robust_all_holdout_numeric_features"]),
            "```",
            "",
            "## 结论",
            "",
            audit["interpretation"],
            "",
            "这说明当前 15 个已补 RMP trajectory 字段，加上 3 个 addition-before",
            "diagnostic proxy，仍不能形成 production selector。",
            "proxy 可以解释一部分 RMP 轨迹压力，但还不足以跨 context / instance /",
            "dataset 稳定泛化。",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="*", default=[str(path) for path in DEFAULT_INPUTS])
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    audit = build_audit([Path(path) for path in args.inputs])
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(audit, Path(args.report))
    print(json.dumps(audit, ensure_ascii=False, sort_keys=True))
    return 0 if audit["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
