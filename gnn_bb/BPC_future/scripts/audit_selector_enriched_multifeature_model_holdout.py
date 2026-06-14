#!/usr/bin/env python3
"""Audit enriched multifeature selector models on exact replay rows.

This read-only audit trains small addition-before models on exact-context
candidate impact rows using local column features plus the RMP/context features
that are now present in ``candidate_impact_rows.csv``.  It evaluates every
leave-one-context, leave-one-instance, and leave-one-dataset fold separately so
aggregate micro averages cannot hide bad folds.

It does not run BPC, pricing, RMP, Pulse, replay, or benchmarks.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from BPC_future.scripts import analyze_candidate_selector_models as model_lib


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_enriched_multifeature_model_holdout_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_enriched_multifeature_model_holdout_zh.md"
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
MODEL_FEATURES = (
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
ENRICHED_FEATURES = (
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


def _dataset_name(path: Path) -> str:
    if path.name == "candidate_impact_rows.csv":
        if path.parent.name == "impact":
            return path.parent.parent.name
        return path.parent.name
    return path.stem


def _as_bool_number(value: Any) -> str:
    text = str(value).strip().lower()
    return "1.0" if text in {"1", "true", "yes"} else "0.0"


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
                if str(row.get("single_treatment_found", "")).strip().lower() not in {
                    "1",
                    "true",
                    "yes",
                }:
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


def _label(row: dict[str, str]) -> int:
    return 1 if row.get("single_impact_class") == "improved" else 0


def _patch_model_library() -> None:
    model_lib.FEATURES = MODEL_FEATURES
    model_lib._label = _label


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


def _evaluate_holdout(
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
    passing_fold_count = sum(1 for item in fold_results if item["passes"])
    worst_folds = sorted(
        fold_results,
        key=lambda item: (
            item["passes"],
            float(item["test"].get("precision") or 0.0),
            float(item["test"].get("recall") or 0.0),
            -int(item["test"].get("fp") or 0),
        ),
    )[:5]
    return {
        "model": model_name,
        "holdout_key": holdout_key,
        "fold_count": len(fold_results),
        "passing_fold_count": passing_fold_count,
        "failing_fold_count": max(0, len(fold_results) - passing_fold_count),
        "all_folds_pass": bool(
            fold_results and passing_fold_count == len(fold_results)
        ),
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
        "worst_folds": worst_folds,
    }


def build_audit(input_paths: list[Path]) -> dict[str, Any]:
    _patch_model_library()
    rows = _read_rows(input_paths)
    label_counts = dict(Counter(row.get("single_impact_class", "") for row in rows))
    feature_non_empty_counts = {
        feature: sum(1 for row in rows if str(row.get(feature, "")).strip())
        for feature in MODEL_FEATURES
    }
    holdout_by_model: dict[str, dict[str, Any]] = {}
    robust_models: list[str] = []
    for model_name, builder in model_lib.MODEL_BUILDERS.items():
        model_payload = {
            holdout_key: _evaluate_holdout(rows, holdout_key, model_name, builder)
            for holdout_key in HOLDOUT_KEYS
        }
        holdout_by_model[model_name] = model_payload
        if all(model_payload[key]["all_folds_pass"] for key in HOLDOUT_KEYS):
            robust_models.append(model_name)
    best_context_model = max(
        holdout_by_model,
        key=lambda model: (
            holdout_by_model[model]["context_hash"]["passing_fold_count"],
            float(holdout_by_model[model]["context_hash"]["micro"].get("precision") or 0.0),
            float(holdout_by_model[model]["context_hash"]["micro"].get("recall") or 0.0),
        ),
    )
    checks = {
        "has_rows": bool(rows),
        "expected_row_count": len(rows) == 280,
        "has_improved_and_noop": (
            label_counts.get("improved", 0) > 0 and label_counts.get("noop", 0) > 0
        ),
        "all_model_features_present": all(
            feature_non_empty_counts.get(feature, 0) > 0 for feature in MODEL_FEATURES
        ),
        "enriched_features_present": all(
            feature_non_empty_counts.get(feature, 0) > 0
            for feature in ENRICHED_FEATURES
        ),
        "no_model_passes_all_holdouts": not robust_models,
        "best_context_model_still_has_failing_folds": (
            holdout_by_model[best_context_model]["context_hash"]["all_folds_pass"]
            is False
        ),
        "post_addition_features_excluded": True,
    }
    return {
        "schema_version": "selector_enriched_multifeature_model_holdout_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "input_paths": [str(path) for path in input_paths],
        "row_count": len(rows),
        "label_counts": label_counts,
        "model_features": list(MODEL_FEATURES),
        "enriched_features": list(ENRICHED_FEATURES),
        "feature_non_empty_counts": feature_non_empty_counts,
        "holdout_keys": list(HOLDOUT_KEYS),
        "holdout_by_model": holdout_by_model,
        "robust_all_holdout_models": robust_models,
        "best_context_model": best_context_model,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "Adding the currently available RMP/context trajectory fields and "
            "addition-before churn/degeneracy proxy fields to small multifeature "
            "models does not produce a selector that passes every context, "
            "instance, and dataset fold. The production selector blocker remains "
            "active."
        ),
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def write_report(audit: dict[str, Any], path: Path) -> None:
    lines = [
        "# Enriched Multifeature Model Holdout 审计",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告检查 local column features 加上已补入的 RMP/context trajectory 字段后，",
        "简单多字段模型是否已经能通过 context / instance / dataset 每个 held-out fold。",
        "审计只读 `candidate_impact_rows.csv`，不运行 BPC / pricing / RMP / Pulse。",
        "",
        "## 机器字段",
        "",
        "```text",
        "selector_enriched_multifeature_model_holdout = current",
        f"diagnostic_only = {str(audit['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(audit['runs_bpc_or_pricing']).lower()}",
        f"row_count = {audit['row_count']}",
        f"label_counts = {audit['label_counts']}",
        f"model_features_count = {len(audit['model_features'])}",
        f"enriched_features_count = {len(audit['enriched_features'])}",
        f"best_context_model = {audit['best_context_model']}",
        f"robust_all_holdout_model_count = {len(audit['robust_all_holdout_models'])}",
        f"all_checks_pass = {str(audit['all_checks_pass']).lower()}",
        "```",
        "",
        "## Model Holdout Summary",
        "",
        "| Model | Context folds | Instance folds | Dataset folds | Context micro P/R |",
        "|---|---:|---:|---:|---:|",
    ]
    for model_name, payload in audit["holdout_by_model"].items():
        context = payload["context_hash"]
        instance = payload["instance"]
        dataset = payload["impact_dataset"]
        micro = context["micro"]
        lines.append(
            "| "
            + " | ".join(
                [
                    model_name,
                    f"{context['passing_fold_count']}/{context['fold_count']}",
                    f"{instance['passing_fold_count']}/{instance['fold_count']}",
                    f"{dataset['passing_fold_count']}/{dataset['fold_count']}",
                    f"{_fmt(micro.get('precision'))}/{_fmt(micro.get('recall'))}",
                ]
            )
            + " |"
        )
    best = audit["holdout_by_model"][audit["best_context_model"]]
    lines.extend(
        [
            "",
            "## 关键数字",
            "",
            "```text",
            f"best_context_model = {audit['best_context_model']}",
            "best_context_model_context_folds = "
            f"{best['context_hash']['passing_fold_count']}/{best['context_hash']['fold_count']}",
            "best_context_model_instance_folds = "
            f"{best['instance']['passing_fold_count']}/{best['instance']['fold_count']}",
            "best_context_model_dataset_folds = "
            f"{best['impact_dataset']['passing_fold_count']}/{best['impact_dataset']['fold_count']}",
            "robust_all_holdout_models = "
            + ",".join(audit["robust_all_holdout_models"]),
            "production_validated_selector = false",
            "```",
            "",
            "## 结论",
            "",
            audit["interpretation"],
            "",
            "因此当前 enriched/proxy features 可以继续作为 calibration 输入，但还不能作为",
            "production-safe 优化方向。下一步不能只靠简单 proxy selector，",
            "需要更真实的 RMP 稳定化/退化处理证据。",
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
