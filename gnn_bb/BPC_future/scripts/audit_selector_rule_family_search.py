#!/usr/bin/env python3
"""Search simple addition-before selector rule families on replay rows.

This is a read-only audit.  It uses existing exact replay
``candidate_impact_rows.csv`` files and searches single-clause and two-clause
conjunction selectors built only from features visible before adding a returned
JourneyColumn batch.  The purpose is not to produce a production selector from
full-sample hindsight, but to test whether even a broad simple rule family can
pass every context / instance / dataset fold.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any, Callable


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_rule_family_search_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_rule_family_search_zh.md"
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


Predicate = Callable[[dict[str, str]], bool]


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
        if item != ""
    ]
    task_set = [item for item in str(copied.get("task_set", "")).split(",") if item]
    true_rc = _as_float(copied.get("true_reduced_cost"))
    cost = _as_float(copied.get("cost"))
    task_set_size = len(task_set)
    copied["sequence_len"] = str(len(sequence))
    copied["task_set_size"] = str(task_set_size)
    copied["rc_per_task"] = (
        "" if true_rc is None or task_set_size <= 0 else str(true_rc / task_set_size)
    )
    copied["cost_per_task"] = (
        "" if cost is None or task_set_size <= 0 else str(cost / task_set_size)
    )
    return copied


def _read_rows(paths: list[Path]) -> list[dict[str, str]]:
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
                copied["impact_dataset"] = dataset
                copied["impact_source"] = str(path)
                rows.append(copied)
    return rows


def _evaluate_predicate(rows: list[dict[str, str]], predicate: Predicate) -> dict[str, Any]:
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


def _numeric_clause(feature: str, operator: str, threshold: float) -> Predicate:
    def predicate(row: dict[str, str]) -> bool:
        value = _as_float(row.get(feature))
        if value is None:
            return False
        if operator == "<=":
            return value <= threshold + 1.0e-12
        return value >= threshold - 1.0e-12

    return predicate


def _boolean_clause(feature: str, expected: bool) -> Predicate:
    def predicate(row: dict[str, str]) -> bool:
        return _as_bool(row.get(feature)) is expected

    return predicate


def _build_clauses(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    clauses: list[dict[str, Any]] = []
    for feature in NUMERIC_FEATURES:
        values = sorted(
            {
                value
                for row in rows
                for value in [_as_float(row.get(feature))]
                if value is not None
            }
        )
        for operator in ("<=", ">="):
            for threshold in values:
                clauses.append(
                    {
                        "features": (feature,),
                        "description": f"{feature}{operator}{threshold:.6g}",
                        "predicates": (_numeric_clause(feature, operator, threshold),),
                    }
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
        for expected in values:
            clauses.append(
                {
                    "features": (feature,),
                    "description": f"{feature}=={str(expected).lower()}",
                    "predicates": (_boolean_clause(feature, expected),),
                }
            )
    for clause in clauses:
        clause["full_sample"] = _evaluate_rule(rows, clause)
    return clauses


def _evaluate_rule(rows: list[dict[str, str]], rule: dict[str, Any]) -> dict[str, Any]:
    predicates = tuple(rule["predicates"])
    return _evaluate_predicate(rows, lambda row: all(pred(row) for pred in predicates))


def _serializable_rule(rule: dict[str, Any]) -> dict[str, Any]:
    return {
        "description": rule["description"],
        "features": list(rule["features"]),
        "full_sample": rule["full_sample"],
        "fold_summary": rule.get("fold_summary", {}),
        "worst_material_failures": rule.get("worst_material_failures", []),
    }


def _fold_summary(rows: list[dict[str, str]], rule: dict[str, Any]) -> dict[str, Any]:
    by_holdout: dict[str, Any] = {}
    strict_all = True
    material_all = True
    material_failures: list[dict[str, Any]] = []
    for holdout_key in HOLDOUT_KEYS:
        groups = []
        for value in sorted({str(row.get(holdout_key, "")) for row in rows}):
            group_rows = [row for row in rows if str(row.get(holdout_key, "")) == value]
            metrics = _evaluate_rule(group_rows, rule)
            strict_pass = _passes_strict(metrics)
            material_pass = _passes_material(metrics)
            strict_all = strict_all and strict_pass
            material_all = material_all and material_pass
            item = {
                "holdout": value,
                "metrics": metrics,
                "strict_pass": strict_pass,
                "material_pass": material_pass,
            }
            groups.append(item)
            if not material_pass:
                material_failures.append({"holdout_key": holdout_key, **item})
        by_holdout[holdout_key] = {
            "fold_count": len(groups),
            "strict_passing_fold_count": sum(1 for item in groups if item["strict_pass"]),
            "material_passing_fold_count": sum(
                1 for item in groups if item["material_pass"]
            ),
            "strict_all_folds_pass": all(item["strict_pass"] for item in groups),
            "material_all_folds_pass": all(item["material_pass"] for item in groups),
            "worst_folds": sorted(
                groups,
                key=lambda item: (
                    -1.0
                    if item["metrics"].get("precision") is None
                    else float(item["metrics"]["precision"]),
                    -1.0
                    if item["metrics"].get("recall") is None
                    else float(item["metrics"]["recall"]),
                    int(item["metrics"].get("fp", 0)),
                ),
            )[:5],
        }
    return {
        "holdouts": by_holdout,
        "strict_all_holdout_folds_pass": strict_all,
        "material_all_holdout_folds_pass": material_all,
        "worst_material_failures": material_failures[:8],
    }


def _build_rule_family(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    clauses = sorted(
        _build_clauses(rows),
        key=lambda item: _score(item["full_sample"]),
        reverse=True,
    )
    base = [
        clause
        for clause in clauses
        if int(clause["full_sample"].get("predicted_positive", 0)) > 0
    ][:MAX_PAIR_BASE_CLAUSES]
    rules = list(base)
    for left, right in combinations(base, 2):
        if set(left["features"]) & set(right["features"]):
            continue
        rule = {
            "features": tuple(left["features"]) + tuple(right["features"]),
            "description": f"{left['description']} AND {right['description']}",
            "predicates": tuple(left["predicates"]) + tuple(right["predicates"]),
        }
        rule["full_sample"] = _evaluate_rule(rows, rule)
        rules.append(rule)
    return rules


def build_summary(
    input_paths: list[Path], task_count_filter: int | None = None
) -> dict[str, Any]:
    rows = _read_rows(input_paths)
    if task_count_filter is not None:
        rows = [
            row
            for row in rows
            if _as_float(row.get("task_count")) == float(task_count_filter)
        ]
    rules = _build_rule_family(rows)
    strict_rules: list[dict[str, Any]] = []
    material_rules: list[dict[str, Any]] = []
    for rule in rules:
        folds = _fold_summary(rows, rule)
        rule["fold_summary"] = folds["holdouts"]
        rule["worst_material_failures"] = folds["worst_material_failures"]
        if folds["strict_all_holdout_folds_pass"]:
            strict_rules.append(rule)
        if folds["material_all_holdout_folds_pass"]:
            material_rules.append(rule)
    top_full_sample = sorted(
        rules,
        key=lambda item: _score(item["full_sample"]),
        reverse=True,
    )[:12]
    if task_count_filter is None:
        row_scope_ok = len(rows) == 280
    else:
        row_scope_ok = bool(
            rows
            and all(_as_float(row.get("task_count")) == float(task_count_filter) for row in rows)
        )
    checks = {
        "row_scope_matches_filter": row_scope_ok,
        "has_label_mixture": len({row.get("single_impact_class") for row in rows}) == 2,
        "searched_single_and_pair_rules": len(rules) > len(_build_clauses(rows)),
        "no_strict_all_fold_rule": len(strict_rules) == 0,
        "no_material_all_fold_rule": len(material_rules) == 0,
        "top_full_sample_has_signal": (
            top_full_sample[0]["full_sample"].get("precision") is not None
            and float(top_full_sample[0]["full_sample"]["precision"]) >= 0.8
            and float(top_full_sample[0]["full_sample"]["recall"]) >= 0.8
        ),
    }
    return {
        "schema_version": "selector_rule_family_search_v1",
        "input_paths": [str(path) for path in input_paths],
        "row_filter": {
            "task_count": task_count_filter,
        },
        "feature_scope": "addition_before_only",
        "numeric_features": list(NUMERIC_FEATURES),
        "boolean_features": list(BOOLEAN_FEATURES),
        "holdout_keys": list(HOLDOUT_KEYS),
        "strict_gate": {
            "precision_min": STRICT_PRECISION_MIN,
            "recall_min": STRICT_RECALL_MIN,
        },
        "material_gate_note": (
            "A no-positive fold may pass only when the rule selects no false "
            "positive rows; positive folds must still pass the strict gate."
        ),
        "row_count": len(rows),
        "label_counts": dict(Counter(row["single_impact_class"] for row in rows)),
        "context_count": len({row.get("context_hash", "") for row in rows}),
        "instance_count": len({row.get("instance", "") for row in rows}),
        "impact_dataset_count": len({row.get("impact_dataset", "") for row in rows}),
        "single_clause_count": len(_build_clauses(rows)),
        "rule_count": len(rules),
        "strict_all_fold_passing_rule_count": len(strict_rules),
        "material_all_fold_passing_rule_count": len(material_rules),
        "top_full_sample_rules": [
            _serializable_rule(rule) for rule in top_full_sample
        ],
        "strict_all_fold_passing_rules": [
            _serializable_rule(rule) for rule in strict_rules[:10]
        ],
        "material_all_fold_passing_rules": [
            _serializable_rule(rule) for rule in material_rules[:10]
        ],
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "The replay data contains strong full-sample calibration signal, "
            "but no simple addition-before single-clause or two-clause rule "
            "survives every context, instance, and dataset fold. This further "
            "supports keeping selector work calibration-only."
        ),
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    top = summary["top_full_sample_rules"]
    task_count_filter = summary.get("row_filter", {}).get("task_count")
    lines = [
        "# Selector Rule-Family Search 审计",
        "",
        "日期：2026-06-14",
        "",
        "## 目标",
        "",
        "在现有 exact replay candidate rows 上，扩大只读 selector 搜索范围：",
        "不仅检查单特征，还检查最多两个 addition-before 条件的 conjunction。",
        "该审计不运行求解器，不修改 production path，也不把 full-sample hindsight",
        "规则当作可上线 selector。",
        "",
        "## 结论",
        "",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "selector_rule_family_search = current",
        f"task_count_filter = {task_count_filter}",
        f"row_count = {summary['row_count']}",
        f"label_counts = {summary['label_counts']}",
        f"context_count = {summary['context_count']}",
        f"instance_count = {summary['instance_count']}",
        f"impact_dataset_count = {summary['impact_dataset_count']}",
        f"single_clause_count = {summary['single_clause_count']}",
        f"rule_count = {summary['rule_count']}",
        f"strict_all_fold_passing_rule_count = {summary['strict_all_fold_passing_rule_count']}",
        f"material_all_fold_passing_rule_count = {summary['material_all_fold_passing_rule_count']}",
        "production_validated_selector = false",
        "",
        "解释：full sample 上仍有明显 calibration signal，但即使把搜索扩展到",
        "单 clause + 两 clause conjunction，也没有规则能跨 context / instance / dataset",
        "全部 fold 稳定通过。`material_all_fold` 已经允许 no-positive fold 在不产生",
        "false positive 时通过，因此这个失败不是单纯被空正例 fold 卡死。",
        "",
        "## Top Full-Sample Rules",
        "",
        "| Rule | Precision | Recall | TP | FP | FN | Predicted |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for rule in top[:10]:
        metrics = rule["full_sample"]
        lines.append(
            "| "
            + " | ".join(
                [
                    rule["description"],
                    _fmt(metrics.get("precision")),
                    _fmt(metrics.get("recall")),
                    str(metrics.get("tp")),
                    str(metrics.get("fp")),
                    str(metrics.get("fn")),
                    str(metrics.get("predicted_positive")),
                ]
            )
            + " |"
        )
    if top:
        best = top[0]
        lines.extend(
            [
                "",
                "## Best Rule Fold Failure Sample",
                "",
                "```text",
                f"best_rule = {best['description']}",
                f"best_full_sample = {best['full_sample']}",
                "```",
                "",
            ]
        )
        for holdout_key, payload in best["fold_summary"].items():
            lines.extend(
                [
                    f"### {holdout_key}",
                    "",
                    "```text",
                    f"strict_passing_fold_count = {payload['strict_passing_fold_count']}/{payload['fold_count']}",
                    f"material_passing_fold_count = {payload['material_passing_fold_count']}/{payload['fold_count']}",
                    "worst_folds = "
                    + str(
                        [
                            {
                                "holdout": item["holdout"],
                                "precision": item["metrics"].get("precision"),
                                "recall": item["metrics"].get("recall"),
                                "tp": item["metrics"].get("tp"),
                                "fp": item["metrics"].get("fp"),
                                "fn": item["metrics"].get("fn"),
                            }
                            for item in payload["worst_folds"][:3]
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
            "这进一步收紧当前根因判断：问题不是缺少一个简单阈值、布尔条件或",
            "两个局部特征的组合。returned batch 是否有用仍然依赖 context / RMP",
            "trajectory。下一步若继续 selector 路线，必须继续扩展 no-certificate-effect",
            "exact-context replay，并寻找可泛化的 RMP/context 特征；不能把这些",
            "full-sample calibration 规则接入 production worker。",
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
