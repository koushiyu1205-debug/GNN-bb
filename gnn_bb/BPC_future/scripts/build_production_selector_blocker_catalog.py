"""Build a production-selector blocker catalog for root-cause evidence.

This is a diagnostic-only aggregation over existing selector audits.  It makes
the current production selector gap explicit: replay-local calibration exists,
but no addition-before selector has passed the required context, instance, and
dataset evidence gates.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_COUNTEREXAMPLE_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_counterexample_catalog_20260614/"
    "summary.json"
)
DEFAULT_MICRO_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_micro_vs_fold_gate_20260614/"
    "summary.json"
)
DEFAULT_MODEL_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_model_micro_vs_fold_gate_20260614/"
    "summary.json"
)
DEFAULT_RULE_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_rule_family_search_20260614/"
    "summary.json"
)
DEFAULT_RULE_20ONLY_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_rule_family_search_20only_20260614/"
    "summary.json"
)
DEFAULT_TRAIN_HOLDOUT_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_rule_family_train_holdout_20260614/"
    "summary.json"
)
DEFAULT_TRAIN_HOLDOUT_20ONLY_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_rule_family_train_holdout_20only_20260614/"
    "summary.json"
)
DEFAULT_CONTEXT_FOLD_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_context_fold_anatomy_20260614/"
    "summary.json"
)
DEFAULT_CONTEXT_FEATURE_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_context_feature_anatomy_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_production_selector_blocker_catalog_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_production_selector_blocker_catalog_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fold_fraction(summary: dict[str, Any], holdout: str) -> str:
    holdout_summaries = summary.get("holdout_summaries", {})
    item = holdout_summaries.get(holdout, {})
    passing = item.get("material_passing_fold_count")
    total = item.get("fold_count")
    if passing is None or total is None:
        return "unknown"
    return f"{passing}/{total}"


def build_catalog(paths: dict[str, Path]) -> dict[str, Any]:
    counter = _read_json(paths["counterexample"])
    micro = _read_json(paths["micro"])
    model = _read_json(paths["model"])
    rule = _read_json(paths["rule"])
    rule_20 = _read_json(paths["rule_20only"])
    train = _read_json(paths["train_holdout"])
    train_20 = _read_json(paths["train_holdout_20only"])
    context_fold = _read_json(paths["context_fold"])
    context_feature = _read_json(paths["context_feature"])

    blockers = [
        {
            "blocker_id": "concrete_false_positive_and_false_negative_examples",
            "status": "blocking",
            "evidence": {
                "false_positive_count": counter.get("false_positive_count"),
                "false_negative_count": counter.get("false_negative_count"),
                "false_positive_new_task_set_noop_count": counter.get(
                    "false_positive_new_task_set_noop_count"
                ),
                "false_negative_new_task_set_improved_count": counter.get(
                    "false_negative_new_task_set_improved_count"
                ),
            },
        },
        {
            "blocker_id": "micro_average_gate_not_fold_stable",
            "status": "blocking",
            "evidence": {
                "micro_passing_features": micro.get("micro_passing_features"),
                "robust_all_fold_passing_features": micro.get(
                    "robust_all_fold_passing_features"
                ),
                "checks": micro.get("checks"),
            },
        },
        {
            "blocker_id": "aggregate_model_gate_not_fold_stable",
            "status": "blocking",
            "evidence": {
                "aggregate_all_holdout_models": model.get(
                    "aggregate_all_holdout_models"
                ),
                "robust_all_fold_passing_models": model.get(
                    "robust_all_fold_passing_models"
                ),
                "checks": model.get("checks"),
            },
        },
        {
            "blocker_id": "simple_rule_family_has_no_all_fold_rule",
            "status": "blocking",
            "evidence": {
                "rule_count": rule.get("rule_count"),
                "material_all_fold_passing_rule_count": rule.get(
                    "material_all_fold_passing_rule_count"
                ),
                "rule_count_20only": rule_20.get("rule_count"),
                "material_all_fold_passing_rule_count_20only": rule_20.get(
                    "material_all_fold_passing_rule_count"
                ),
            },
        },
        {
            "blocker_id": "train_holdout_rules_not_context_stable",
            "status": "blocking",
            "evidence": {
                "context_material_passing_folds": _fold_fraction(
                    train, "context_hash"
                ),
                "context_material_passing_folds_20only": _fold_fraction(
                    train_20, "context_hash"
                ),
                "checks": train.get("checks"),
                "checks_20only": train_20.get("checks"),
            },
        },
        {
            "blocker_id": "context_anatomy_has_opposite_failure_modes",
            "status": "blocking",
            "evidence": {
                "twenty_false_positive_no_positive_context_count": context_fold.get(
                    "twenty_only", {}
                ).get("context_failure_kind_counts", {}).get(
                    "false_positive_no_positive_context"
                ),
                "twenty_missed_positive_context_count": context_fold.get(
                    "twenty_only", {}
                ).get("context_failure_kind_counts", {}).get(
                    "missed_positive_context"
                ),
                "mixed_instance_group_count": context_feature.get(
                    "mixed_instance_group_count"
                ),
                "mixed_dataset_group_count": context_feature.get(
                    "mixed_dataset_group_count"
                ),
            },
        },
    ]
    checks = {
        "counterexample_catalog_passed": counter.get("all_checks_pass") is True,
        "micro_has_no_robust_all_fold_feature": (
            micro.get("robust_all_fold_passing_features") == []
        ),
        "model_has_no_robust_all_fold_model": (
            model.get("robust_all_fold_passing_models") == []
        ),
        "rule_family_has_no_material_all_fold_rule": (
            rule.get("material_all_fold_passing_rule_count") == 0
            and rule_20.get("material_all_fold_passing_rule_count") == 0
        ),
        "train_holdout_context_not_all_passing": (
            _fold_fraction(train, "context_hash") == "17/28"
            and _fold_fraction(train_20, "context_hash") == "17/27"
        ),
        "context_anatomy_has_both_failure_modes": (
            context_fold.get("twenty_only", {})
            .get("context_failure_kind_counts", {})
            .get("false_positive_no_positive_context")
            == 4
            and context_fold.get("twenty_only", {})
            .get("context_failure_kind_counts", {})
            .get("missed_positive_context")
            == 3
        ),
        "context_feature_mixed_within_instance_and_dataset": (
            context_feature.get("mixed_instance_group_count") == 2
            and context_feature.get("mixed_dataset_group_count") == 2
        ),
    }
    return {
        "schema_version": "production_selector_blocker_catalog_v1",
        "status": "production_selector_not_validated",
        "feature_scope": "addition_before_only",
        "required_holdouts": ["context", "instance", "dataset"],
        "blockers": blockers,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "当前 selector 证据已经有 calibration signal，但具体反例、fold gate、"
            "模型 gate、规则族搜索、train-holdout 和 context anatomy 都说明它还"
            "不是 production selector。下一步必须继续 selector holdout，而不是"
            "打开 worker default 或 certificate gate。"
        ),
        "sources": {name: str(path) for name, path in paths.items()},
    }


def _get_blocker(catalog: dict[str, Any], blocker_id: str) -> dict[str, Any]:
    for blocker in catalog["blockers"]:
        if blocker["blocker_id"] == blocker_id:
            return blocker
    return {}


def write_report(catalog: dict[str, Any], path: Path) -> None:
    counter = _get_blocker(
        catalog, "concrete_false_positive_and_false_negative_examples"
    )["evidence"]
    micro = _get_blocker(catalog, "micro_average_gate_not_fold_stable")["evidence"]
    model = _get_blocker(catalog, "aggregate_model_gate_not_fold_stable")["evidence"]
    rule = _get_blocker(catalog, "simple_rule_family_has_no_all_fold_rule")[
        "evidence"
    ]
    train = _get_blocker(catalog, "train_holdout_rules_not_context_stable")[
        "evidence"
    ]
    context = _get_blocker(catalog, "context_anatomy_has_opposite_failure_modes")[
        "evidence"
    ]
    text = f"""# Production Selector Blocker Catalog 报告

日期：2026-06-14

## 目的

本报告汇总 selector 为什么还不能进入 production BPC A/B。它只读已有
exact-context replay 和 selector audit 结果，不改变 solver。

## 机器字段

```text
production_selector_blocker_catalog = current
production_selector_status = {catalog['status']}
selector_feature_scope = {catalog['feature_scope']}
required_selector_holdouts = context / instance / dataset
all_checks_pass = {str(catalog['all_checks_pass']).lower()}
```

## 阻塞点

### 1. 具体 false positive / false negative 反例仍存在

```text
false_positive_count = {counter['false_positive_count']}
false_negative_count = {counter['false_negative_count']}
false_positive_new_task_set_noop_count = {counter['false_positive_new_task_set_noop_count']}
false_negative_new_task_set_improved_count = {counter['false_negative_new_task_set_improved_count']}
```

### 2. micro-average 通过不等于每个 fold 通过

```text
micro_passing_features = {micro['micro_passing_features']}
robust_all_fold_passing_features = {micro['robust_all_fold_passing_features']}
```

### 3. 简单模型 aggregate 有信号，但没有 robust all-fold 模型

```text
aggregate_all_holdout_models = {model['aggregate_all_holdout_models']}
robust_all_fold_passing_models = {model['robust_all_fold_passing_models']}
```

### 4. 单条件 / 双条件 addition-before 规则族无全 fold 规则

```text
rule_count = {rule['rule_count']}
material_all_fold_passing_rule_count = {rule['material_all_fold_passing_rule_count']}
rule_count_20only = {rule['rule_count_20only']}
material_all_fold_passing_rule_count_20only = {rule['material_all_fold_passing_rule_count_20only']}
```

### 5. train-on-fold 重新选规则也不稳定

```text
rule_family_train_context_material_passing_folds = {train['context_material_passing_folds']}
rule_family_train_20only_context_material_passing_folds = {train['context_material_passing_folds_20only']}
```

### 6. context fold 同时有相反失败形态

```text
context_fold_anatomy_twenty_false_positive_no_positive_context_count = {context['twenty_false_positive_no_positive_context_count']}
context_fold_anatomy_twenty_missed_positive_context_count = {context['twenty_missed_positive_context_count']}
context_feature_mixed_instance_group_count = {context['mixed_instance_group_count']}
context_feature_mixed_dataset_group_count = {context['mixed_dataset_group_count']}
```

## 结论

{catalog['interpretation']}

当前仍必须保持：

```text
production_validated_selector = false
production_candidate_ab = blocked
```
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    paths = {
        "counterexample": DEFAULT_COUNTEREXAMPLE_SUMMARY,
        "micro": DEFAULT_MICRO_SUMMARY,
        "model": DEFAULT_MODEL_SUMMARY,
        "rule": DEFAULT_RULE_SUMMARY,
        "rule_20only": DEFAULT_RULE_20ONLY_SUMMARY,
        "train_holdout": DEFAULT_TRAIN_HOLDOUT_SUMMARY,
        "train_holdout_20only": DEFAULT_TRAIN_HOLDOUT_20ONLY_SUMMARY,
        "context_fold": DEFAULT_CONTEXT_FOLD_SUMMARY,
        "context_feature": DEFAULT_CONTEXT_FEATURE_SUMMARY,
    }
    catalog = build_catalog(paths)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(catalog, Path(args.report))
    print(json.dumps(catalog, ensure_ascii=False, sort_keys=True))
    return 0 if catalog["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
