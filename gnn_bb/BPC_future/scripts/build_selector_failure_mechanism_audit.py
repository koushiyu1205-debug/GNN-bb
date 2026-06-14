"""Build a selector-failure mechanism audit from existing root-cause artifacts.

This diagnostic-only script explains why the current addition-before selector
work is still not production-ready.  It reads existing JSON summaries and
writes a compact mechanism audit; it does not run BPC, pricing, RMP, Pulse, or
any benchmark.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_CONTEXT_FOLD = Path(
    "BPC_future/results/root_cause_selector_context_fold_anatomy_20260614/"
    "summary.json"
)
DEFAULT_CONTEXT_FEATURE = Path(
    "BPC_future/results/root_cause_selector_context_feature_anatomy_20260614/"
    "summary.json"
)
DEFAULT_CONTEXT_DISAMBIGUATION = Path(
    "BPC_future/results/root_cause_selector_context_disambiguation_20260613/"
    "summary.json"
)
DEFAULT_CONTEXT_SCALAR_HOLDOUT = Path(
    "BPC_future/results/root_cause_selector_context_scalar_holdout_20260613/"
    "summary.json"
)
DEFAULT_MICRO_VS_FOLD = Path(
    "BPC_future/results/root_cause_selector_micro_vs_fold_gate_20260614/"
    "summary.json"
)
DEFAULT_RULE_TRAIN_HOLDOUT = Path(
    "BPC_future/results/root_cause_selector_rule_family_train_holdout_20260614/"
    "summary.json"
)
DEFAULT_RULE_TRAIN_HOLDOUT_20ONLY = Path(
    "BPC_future/results/"
    "root_cause_selector_rule_family_train_holdout_20only_20260614/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_failure_mechanism_audit_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_failure_mechanism_audit_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _holdout_summary_counts(summary: dict[str, Any], holdout_key: str) -> dict[str, Any]:
    holdout = summary.get("holdout_summaries", {}).get(holdout_key, {})
    return {
        "fold_count": holdout.get("fold_count"),
        "all_material_folds_pass": holdout.get("all_material_folds_pass"),
        "all_strict_folds_pass": holdout.get("all_strict_folds_pass"),
        "passing_material_fold_count": sum(
            1 for fold in holdout.get("folds", []) if fold.get("material_pass")
        ),
        "passing_strict_fold_count": sum(
            1 for fold in holdout.get("folds", []) if fold.get("strict_pass")
        ),
    }


def build_audit(
    *,
    context_fold_path: Path,
    context_feature_path: Path,
    context_disambiguation_path: Path,
    context_scalar_holdout_path: Path,
    micro_vs_fold_path: Path,
    rule_train_holdout_path: Path,
    rule_train_holdout_20only_path: Path,
) -> dict[str, Any]:
    context_fold = _read_json(context_fold_path)
    context_feature = _read_json(context_feature_path)
    context_disambiguation = _read_json(context_disambiguation_path)
    context_scalar = _read_json(context_scalar_holdout_path)
    micro_vs_fold = _read_json(micro_vs_fold_path)
    rule_train = _read_json(rule_train_holdout_path)
    rule_train_20 = _read_json(rule_train_holdout_20only_path)

    twenty_context = context_fold.get("twenty_only", {})
    twenty_failure_counts = twenty_context.get("context_failure_kind_counts", {})
    local_ladder = context_disambiguation.get("ladder", {})
    local_sequence = local_ladder.get("local_sequence", {})
    context_hash = local_ladder.get("local_sequence_online_context_hash", {})
    model_results = context_scalar.get("model_results", {})
    mechanisms = [
        {
            "mechanism_id": "opposite_context_failure_modes",
            "status": "proved",
            "evidence": {
                "twenty_context_failure_count": twenty_context.get(
                    "context_failure_count"
                ),
                "false_positive_no_positive_context": twenty_failure_counts.get(
                    "false_positive_no_positive_context"
                ),
                "missed_positive_context": twenty_failure_counts.get(
                    "missed_positive_context"
                ),
                "mixed_low_precision_or_recall_context": twenty_failure_counts.get(
                    "mixed_low_precision_or_recall_context"
                ),
            },
            "interpretation": (
                "同一 selector family 在不同 context 下既会全错报，也会漏掉"
                "正例，还会 precision/recall 同时不稳；这不是简单阈值偏松或"
                "偏紧。"
            ),
        },
        {
            "mechanism_id": "local_column_shape_insufficient",
            "status": "proved",
            "evidence": {
                "local_sequence_mixed_group_count": local_sequence.get(
                    "mixed_group_count"
                ),
                "local_sequence_mixed_row_count": local_sequence.get(
                    "mixed_row_count"
                ),
                "context_hash_mixed_group_count": context_hash.get(
                    "mixed_group_count"
                ),
                "context_hash_mixed_row_count": context_hash.get("mixed_row_count"),
            },
            "interpretation": (
                "task-set / sequence 级别的局部列形态仍有混合标签；当前样本里"
                "context hash 可以消除混合，但 hash 本身太具体，不能直接当"
                "生产 selector。"
            ),
        },
        {
            "mechanism_id": "instance_and_dataset_do_not_explain_context",
            "status": "proved",
            "evidence": {
                "mixed_instance_group_count": context_feature.get(
                    "mixed_instance_group_count"
                ),
                "mixed_dataset_group_count": context_feature.get(
                    "mixed_dataset_group_count"
                ),
                "high_positive_context_count": context_feature.get(
                    "high_positive_context_count"
                ),
                "low_positive_context_count": context_feature.get(
                    "low_positive_context_count"
                ),
            },
            "interpretation": (
                "同一 instance 和同一 dataset 内都同时存在 high-impact 与 low/noop "
                "context；不能用实例族或数据集族整体解释。"
            ),
        },
        {
            "mechanism_id": "micro_average_hides_fold_failures",
            "status": "proved",
            "evidence": {
                "micro_passing_features": micro_vs_fold.get(
                    "micro_passing_features", []
                ),
                "robust_all_fold_passing_features": micro_vs_fold.get(
                    "robust_all_fold_passing_features", []
                ),
                "true_rc_context_passing_folds": (
                    micro_vs_fold.get("feature_summaries", {})
                    .get("true_reduced_cost", {})
                    .get("holdouts", {})
                    .get("context_hash", {})
                    .get("passing_fold_count")
                ),
                "true_rc_context_fold_count": (
                    micro_vs_fold.get("feature_summaries", {})
                    .get("true_reduced_cost", {})
                    .get("holdouts", {})
                    .get("context_hash", {})
                    .get("fold_count")
                ),
            },
            "interpretation": (
                "micro-average 上通过的局部特征，在 context/instance/dataset fold "
                "上不稳定；不能用整体 precision/recall 代替 holdout。"
            ),
        },
        {
            "mechanism_id": "simple_context_scalars_not_enough",
            "status": "proved",
            "evidence": {
                "production_validated_selector": context_scalar.get(
                    "production_validated_selector"
                ),
                "passing_models": context_scalar.get("passing_models", []),
                "model_count": len(model_results),
                "checks": context_scalar.get("checks", {}),
            },
            "interpretation": (
                "control objective 等 addition-before scalar 有校准信号，但没有"
                "模型同时通过 dataset / instance / context holdout。"
            ),
        },
        {
            "mechanism_id": "train_holdout_rule_family_not_stable",
            "status": "proved",
            "evidence": {
                "all_rows_context": _holdout_summary_counts(
                    rule_train, "context_hash"
                ),
                "twenty_only_context": _holdout_summary_counts(
                    rule_train_20, "context_hash"
                ),
                "feature_scope": rule_train.get("feature_scope"),
                "row_count": rule_train.get("row_count"),
                "twenty_only_row_count": rule_train_20.get("row_count"),
            },
            "interpretation": (
                "即使每个训练 split 都重新选择 best rule family，context holdout "
                "仍不是 all-pass；说明不是固定一条规则选错，而是现有特征族不够。"
            ),
        },
    ]

    required_next_tests = [
        {
            "test_id": "addition_before_only_feature_scope",
            "requirement": (
                "selector 只能使用加列前可观测特征，不能使用 post-addition "
                "objective delta、active basis change 或 hindsight 标签。"
            ),
        },
        {
            "test_id": "context_instance_dataset_holdout",
            "requirement": (
                "必须同时通过 context、instance、dataset holdout，不能只看 micro "
                "average 或单 context replay。"
            ),
        },
        {
            "test_id": "opposite_failure_mode_coverage",
            "requirement": (
                "必须同时压住 false-positive-only context 和 missed-positive "
                "context；只调阈值不能作为生产方向。"
            ),
        },
        {
            "test_id": "exact_context_replay_no_certificate_effect",
            "requirement": (
                "训练与验证样本必须来自 no-certificate-effect exact-context replay，"
                "避免 certificate 或 worker side effect 污染标签。"
            ),
        },
        {
            "test_id": "production_bpc_ab_after_selector",
            "requirement": (
                "selector 通过 holdout 后，仍必须跑 full BPC A/B：5/10 不退化，"
                "selected 20 hard repeat 有 wall-time/gap/status/tail 改善。"
            ),
        },
    ]

    checks = {
        "sources_pass": all(
            item.get("all_checks_pass") is True
            for item in [
                context_fold,
                context_feature,
                context_disambiguation,
                context_scalar,
                micro_vs_fold,
                rule_train,
                rule_train_20,
            ]
        ),
        "twenty_has_opposite_failure_modes": (
            int(twenty_failure_counts.get("false_positive_no_positive_context", 0))
            > 0
            and int(twenty_failure_counts.get("missed_positive_context", 0)) > 0
            and int(twenty_failure_counts.get("mixed_low_precision_or_recall_context", 0))
            > 0
        ),
        "local_sequence_still_mixed": (
            int(local_sequence.get("mixed_group_count", 0)) > 0
        ),
        "context_hash_disambiguates_current_sample": (
            int(context_hash.get("mixed_group_count", 1)) == 0
        ),
        "same_instance_and_dataset_mixed": (
            int(context_feature.get("mixed_instance_group_count", 0)) > 0
            and int(context_feature.get("mixed_dataset_group_count", 0)) > 0
        ),
        "micro_features_exist_but_no_robust_fold_feature": (
            bool(micro_vs_fold.get("micro_passing_features"))
            and not micro_vs_fold.get("robust_all_fold_passing_features")
        ),
        "context_scalar_not_production_selector": (
            context_scalar.get("production_validated_selector") is False
            and not context_scalar.get("passing_models")
        ),
        "rule_family_not_all_context_holdout": (
            rule_train.get("holdout_summaries", {})
            .get("context_hash", {})
            .get("all_material_folds_pass")
            is False
            and rule_train_20.get("holdout_summaries", {})
            .get("context_hash", {})
            .get("all_material_folds_pass")
            is False
        ),
    }
    return {
        "schema_version": "selector_failure_mechanism_audit_v1",
        "sources": {
            "context_fold": str(context_fold_path),
            "context_feature": str(context_feature_path),
            "context_disambiguation": str(context_disambiguation_path),
            "context_scalar_holdout": str(context_scalar_holdout_path),
            "micro_vs_fold": str(micro_vs_fold_path),
            "rule_train_holdout": str(rule_train_holdout_path),
            "rule_train_holdout_20only": str(rule_train_holdout_20only_path),
        },
        "mechanism_count": len(mechanisms),
        "mechanisms": mechanisms,
        "required_next_tests": required_next_tests,
        "current_production_selector_status": "not_validated",
        "current_allowed_work": "calibration_only_selector_holdout",
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "当前 selector 卡住不是因为某个单阈值没调好，而是局部列特征与"
            "下游 RMP 影响之间存在 context 依赖。下一步必须构造只用"
            " addition-before 特征、但能解释 context/RMP trajectory 的 selector，"
            "并通过 context / instance / dataset holdout。"
        ),
    }


def write_report(audit: dict[str, Any], path: Path) -> None:
    lines = [
        "# Selector Failure Mechanism Audit 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告进一步回答 selector 为什么还不能生产化。它只读既有诊断",
        "summary，不运行 solver，不改变 pricing / worker / certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "selector_failure_mechanism_audit = current",
        f"mechanism_count = {audit['mechanism_count']}",
        f"current_production_selector_status = {audit['current_production_selector_status']}",
        f"current_allowed_work = {audit['current_allowed_work']}",
        f"all_checks_pass = {str(audit['all_checks_pass']).lower()}",
        "```",
        "",
        "## 机制结论",
        "",
    ]
    for item in audit["mechanisms"]:
        lines.extend(
            [
                f"### {item['mechanism_id']}",
                "",
                "```text",
                f"status = {item['status']}",
                "```",
                "",
                item["interpretation"],
                "",
            ]
        )
    lines.extend(
        [
            "## 下一步必须通过的测试",
            "",
        ]
    )
    for item in audit["required_next_tests"]:
        lines.append(f"- `{item['test_id']}`：{item['requirement']}")
    lines.extend(["", "## 结论", "", audit["interpretation"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context-fold", default=str(DEFAULT_CONTEXT_FOLD))
    parser.add_argument("--context-feature", default=str(DEFAULT_CONTEXT_FEATURE))
    parser.add_argument(
        "--context-disambiguation", default=str(DEFAULT_CONTEXT_DISAMBIGUATION)
    )
    parser.add_argument(
        "--context-scalar-holdout", default=str(DEFAULT_CONTEXT_SCALAR_HOLDOUT)
    )
    parser.add_argument("--micro-vs-fold", default=str(DEFAULT_MICRO_VS_FOLD))
    parser.add_argument(
        "--rule-train-holdout", default=str(DEFAULT_RULE_TRAIN_HOLDOUT)
    )
    parser.add_argument(
        "--rule-train-holdout-20only",
        default=str(DEFAULT_RULE_TRAIN_HOLDOUT_20ONLY),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    audit = build_audit(
        context_fold_path=Path(args.context_fold),
        context_feature_path=Path(args.context_feature),
        context_disambiguation_path=Path(args.context_disambiguation),
        context_scalar_holdout_path=Path(args.context_scalar_holdout),
        micro_vs_fold_path=Path(args.micro_vs_fold),
        rule_train_holdout_path=Path(args.rule_train_holdout),
        rule_train_holdout_20only_path=Path(args.rule_train_holdout_20only),
    )
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
