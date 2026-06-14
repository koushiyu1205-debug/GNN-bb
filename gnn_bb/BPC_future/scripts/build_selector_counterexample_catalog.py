"""Build a small catalog of selector counterexamples for root-cause evidence.

This script is diagnostic-only.  It reads existing exact-context replay selector
artifacts and writes a compact JSON/Markdown catalog showing why the current
replay-calibrated addition-before selector is not production validated.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_SELECTOR_SUMMARY = Path(
    "BPC_future/results/root_cause_replay_calibrated_selector_candidate_20260613/"
    "summary.json"
)
DEFAULT_ERROR_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_error_anatomy_20260613/summary.json"
)
DEFAULT_FP_EXAMPLES = Path(
    "BPC_future/results/root_cause_selector_error_anatomy_20260613/"
    "false_positive_examples.csv"
)
DEFAULT_FN_EXAMPLES = Path(
    "BPC_future/results/root_cause_selector_error_anatomy_20260613/"
    "false_negative_examples.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_counterexample_catalog_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_counterexample_catalog_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return None


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compact_example(row: dict[str, str]) -> dict[str, Any]:
    return {
        "impact_dataset": row.get("impact_dataset"),
        "case_id": row.get("case_id"),
        "candidate_id": row.get("candidate_id"),
        "instance": row.get("instance"),
        "context_hash": row.get("context_hash"),
        "task_set": row.get("task_set"),
        "sequence": row.get("sequence"),
        "true_reduced_cost": _as_float(row.get("true_reduced_cost")),
        "new_task_set": _as_bool(row.get("new_task_set")),
        "strict_replacement_by_cost": _as_bool(row.get("strict_replacement_by_cost")),
        "active_support_changing": _as_bool(row.get("active_support_changing")),
        "single_objective_delta": _as_float(row.get("single_objective_delta")),
        "single_impact_class": row.get("single_impact_class"),
    }


def _first_matching(
    rows: list[dict[str, str]],
    *,
    new_task_set: bool | None = None,
    impact_class: str | None = None,
) -> dict[str, Any] | None:
    for row in rows:
        if new_task_set is not None and _as_bool(row.get("new_task_set")) is not new_task_set:
            continue
        if impact_class is not None and row.get("single_impact_class") != impact_class:
            continue
        return _compact_example(row)
    return None


def build_catalog(
    selector_summary_path: Path,
    error_summary_path: Path,
    fp_examples_path: Path,
    fn_examples_path: Path,
) -> dict[str, Any]:
    selector_summary = _read_json(selector_summary_path)
    error_summary = _read_json(error_summary_path)
    fp_rows = _read_csv(fp_examples_path)
    fn_rows = _read_csv(fn_examples_path)
    recommended_full_sample = selector_summary.get("recommended_selector_full_sample", {})
    checks = {
        "selector_summary_exists": selector_summary_path.exists(),
        "error_summary_exists": error_summary_path.exists(),
        "false_positive_examples_exist": bool(fp_rows),
        "false_negative_examples_exist": bool(fn_rows),
        "has_false_positive_count": (
            int(error_summary.get("anatomy", {}).get("false_positive_count", 0)) > 0
        ),
        "has_false_negative_count": (
            int(error_summary.get("anatomy", {}).get("false_negative_count", 0)) > 0
        ),
        "new_task_set_false_positive_exists": (
            _first_matching(fp_rows, new_task_set=True, impact_class="noop")
            is not None
        ),
        "new_task_set_false_negative_exists": (
            _first_matching(fn_rows, new_task_set=True, impact_class="improved")
            is not None
        ),
        "production_validated_selector_is_false": (
            selector_summary.get("production_validation", {}).get(
                "production_validated_selector"
            )
            is False
        ),
    }
    return {
        "schema_version": "selector_counterexample_catalog_v1",
        "selector_summary": str(selector_summary_path),
        "error_summary": str(error_summary_path),
        "recommended_selector_candidate": selector_summary.get(
            "recommended_selector_candidate"
        ),
        "recommended_selector_rule": selector_summary.get("recommended_selector_rule"),
        "row_count": selector_summary.get("row_count"),
        "label_counts": selector_summary.get("label_counts"),
        "recommended_selector_full_sample": recommended_full_sample,
        "false_positive_count": error_summary.get("anatomy", {}).get(
            "false_positive_count"
        ),
        "false_negative_count": error_summary.get("anatomy", {}).get(
            "false_negative_count"
        ),
        "false_positive_new_task_set_noop_count": error_summary.get(
            "anatomy", {}
        ).get("false_positive_new_task_set_noop_count"),
        "false_negative_new_task_set_improved_count": error_summary.get(
            "anatomy", {}
        ).get("false_negative_new_task_set_improved_count"),
        "key_counterexamples": {
            "new_task_set_noop_false_positive": _first_matching(
                fp_rows, new_task_set=True, impact_class="noop"
            ),
            "new_task_set_improved_false_negative": _first_matching(
                fn_rows, new_task_set=True, impact_class="improved"
            ),
            "duplicate_or_replacement_noop_false_positive": _first_matching(
                fp_rows, new_task_set=False, impact_class="noop"
            ),
        },
        "false_positive_examples": [_compact_example(row) for row in fp_rows[:5]],
        "false_negative_examples": [_compact_example(row) for row in fn_rows[:5]],
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "当前 replay-calibrated selector 有具体 false positive 和 false "
            "negative 反例。有些 new-task-set 负列在 exact replay 中是 no-op，"
            "同时也有 true-RC 较弱的 new-task-set 列能改善 RMP objective。"
            "因此 true-RC 与 new-task-set 信号不足以作为 production "
            "addition-before selector。"
        ),
    }


def _fmt_example(example: dict[str, Any] | None) -> str:
    if not example:
        return "无"
    return (
        f"`{example.get('impact_dataset')} / {example.get('case_id')} / "
        f"{example.get('candidate_id')}`: task_set=`{example.get('task_set')}`, "
        f"sequence=`{example.get('sequence')}`, true_rc={example.get('true_reduced_cost')}, "
        f"delta={example.get('single_objective_delta')}, "
        f"class=`{example.get('single_impact_class')}`"
    )


def write_report(catalog: dict[str, Any], path: Path) -> None:
    key = catalog["key_counterexamples"]
    text = f"""# Selector Counterexample Catalog 报告

日期：2026-06-14

## 目的

本报告只读现有 exact-context replay selector 输出，列出当前
addition-before selector 为什么不能作为 production selector 的具体反例。

## 当前候选

```text
selector_counterexample_catalog = current
recommended_selector_candidate = {catalog['recommended_selector_candidate']}
row_count = {catalog['row_count']}
false_positive_count = {catalog['false_positive_count']}
false_negative_count = {catalog['false_negative_count']}
false_positive_new_task_set_noop_count = {catalog['false_positive_new_task_set_noop_count']}
false_negative_new_task_set_improved_count = {catalog['false_negative_new_task_set_improved_count']}
production_validated_selector = false
all_checks_pass = {str(catalog['all_checks_pass']).lower()}
```

## 关键反例

### new-task-set 但 replay no-op 的 false positive

{_fmt_example(key['new_task_set_noop_false_positive'])}

这说明 `new_task_set=True` 和负 reduced cost 不能保证会推动当前 RMP。

### true-RC 较弱但 replay improved 的 false negative

{_fmt_example(key['new_task_set_improved_false_negative'])}

这说明简单 true-RC 阈值会漏掉确实改善 RMP 的列。

### duplicate / replacement no-op false positive

{_fmt_example(key['duplicate_or_replacement_noop_false_positive'])}

这说明 replacement / duplicate 类负列不能被直接当成有效优化信号。

## 解释

{catalog['interpretation']}

## 结论

当前 selector 只能作为 calibration signal。进入 production 前仍必须证明：

```text
selector_feature_scope = addition_before_only
required_selector_holdouts = context / instance / dataset
production_validated_selector = false
```

也就是说，下一步仍是 selector holdout，而不是打开 worker default 或
official certificate gate。
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selector-summary", default=str(DEFAULT_SELECTOR_SUMMARY))
    parser.add_argument("--error-summary", default=str(DEFAULT_ERROR_SUMMARY))
    parser.add_argument("--false-positive-examples", default=str(DEFAULT_FP_EXAMPLES))
    parser.add_argument("--false-negative-examples", default=str(DEFAULT_FN_EXAMPLES))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    catalog = build_catalog(
        Path(args.selector_summary),
        Path(args.error_summary),
        Path(args.false_positive_examples),
        Path(args.false_negative_examples),
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(catalog, Path(args.report))
    print(json.dumps(catalog, ensure_ascii=False, sort_keys=True))
    return 0 if catalog["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
