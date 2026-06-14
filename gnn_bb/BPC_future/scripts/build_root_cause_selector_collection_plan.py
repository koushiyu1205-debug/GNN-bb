"""Build a calibration-only selector data collection plan.

The root-cause evidence says the next allowed work is not production A/B, but
more no-certificate-effect exact-context replay data for an addition-before
selector holdout.  This diagnostic-only helper turns existing selector failure
summaries into a concrete collection plan.  It does not run BPC, pricing, RMP,
Pulse, workers, certificates, or benchmarks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_NEXT_ACTION = Path(
    "BPC_future/results/root_cause_next_action_plan_20260614/summary.json"
)
DEFAULT_CONTEXT_FOLD = Path(
    "BPC_future/results/root_cause_selector_context_fold_anatomy_20260614/"
    "summary.json"
)
DEFAULT_CONTEXT_FEATURE = Path(
    "BPC_future/results/root_cause_selector_context_feature_anatomy_20260614/"
    "summary.json"
)
DEFAULT_COUNTEREXAMPLE_CATALOG = Path(
    "BPC_future/results/root_cause_selector_counterexample_catalog_20260614/"
    "summary.json"
)
DEFAULT_ACTIVE_BASIS_COUNTEREXAMPLES = Path(
    "BPC_future/results/root_cause_active_basis_snapshot_counterexamples_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_collection_plan_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_collection_plan_zh.md"
)

EXPECTED_FAILURE_KINDS = [
    "false_positive_no_positive_context",
    "missed_positive_context",
    "mixed_low_precision_or_recall_context",
]
REQUIRED_CAPTURE_FIELDS = [
    "context_hash",
    "instance",
    "task_count",
    "cg_iter",
    "true_dual_hash",
    "returned_journeys",
    "task_set",
    "sequence",
    "signature",
    "true_reduced_cost",
    "active_basis_churn_count_before",
    "rmp_degeneracy_pressure_before",
    "control_objective",
    "column_pool_size_before",
    "single_impact_class",
    "single_objective_delta",
    "official_effect_count",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _sample_contexts(samples: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in samples[:limit]:
        result.append(
            {
                "context_hash": item.get("holdout") or item.get("context_hash"),
                "failure_kind": item.get("failure_kind"),
                "positive_rate": item.get("positive_rate"),
                "positive_count": item.get("positive_count"),
                "noop_count": item.get("noop_count"),
                "total": item.get("total"),
                "selected_rule": item.get("selected_rule"),
            }
        )
    return result


def _contexts_by_failure_kind(samples: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_kind = {kind: [] for kind in EXPECTED_FAILURE_KINDS}
    for item in samples:
        kind = str(item.get("failure_kind", ""))
        if kind in by_kind:
            by_kind[kind].append(item)
    return by_kind


def _counterexample_rows(rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows[:limit]:
        result.append(
            {
                "snapshot_dataset": row.get("snapshot_dataset"),
                "instance": row.get("instance"),
                "cg_iter": row.get("cg_iter"),
                "task_set": row.get("task_set"),
                "sequence": row.get("sequence"),
                "true_reduced_cost": row.get("true_reduced_cost"),
                "single_impact_class": row.get("single_impact_class"),
                "single_objective_delta": row.get("single_objective_delta"),
                "new_task_set": row.get("new_task_set"),
                "active_basis_churn_count_before": row.get(
                    "active_basis_churn_count_before"
                ),
                "rmp_degeneracy_pressure_before": row.get(
                    "rmp_degeneracy_pressure_before"
                ),
                "context_hash": row.get("context_hash"),
            }
        )
    return result


def build_plan(
    *,
    next_action_path: Path,
    context_fold_path: Path,
    context_feature_path: Path,
    counterexample_catalog_path: Path,
    active_basis_counterexamples_path: Path,
) -> dict[str, Any]:
    next_action = _read_json(next_action_path)
    context_fold = _read_json(context_fold_path)
    context_feature = _read_json(context_feature_path)
    counterexample_catalog = _read_json(counterexample_catalog_path)
    active_basis_counterexamples = _read_json(active_basis_counterexamples_path)

    twenty = context_fold.get("twenty_only", {})
    failed_samples = list(twenty.get("failed_context_samples", []))
    by_kind = _contexts_by_failure_kind(failed_samples)

    priority_context_targets = [
        {
            "target_id": kind,
            "current_context_count": _as_int(
                twenty.get("context_failure_kind_counts", {}).get(kind)
            ),
            "why": {
                "false_positive_no_positive_context": (
                    "当前 selector 会在没有 positive 的 context 中误加列。"
                ),
                "missed_positive_context": (
                    "当前 selector 会漏掉有 positive 的 context。"
                ),
                "mixed_low_precision_or_recall_context": (
                    "当前 selector 在同一 context 内 precision/recall 同时不稳。"
                ),
            }[kind],
            "sample_contexts": _sample_contexts(by_kind[kind]),
            "required_label_mix": {
                "false_positive_no_positive_context": (
                    "至少保留 no-op/low-impact returned rows，并寻找相邻 context 中"
                    "同类候选是否能变成 improved。"
                ),
                "missed_positive_context": (
                    "至少保留 improved rows，并确认现有 selector 为什么没有选中。"
                ),
                "mixed_low_precision_or_recall_context": (
                    "同时保留 improved 与 noop rows，用于训练 context-sensitive gate。"
                ),
            }[kind],
        }
        for kind in EXPECTED_FAILURE_KINDS
    ]

    mixed_instance_targets = [
        {
            "instance": item.get("instance"),
            "context_count": item.get("context_count"),
            "high_context_count": item.get("high_context_count"),
            "low_context_count": item.get("low_context_count"),
            "min_positive_rate": item.get("min_positive_rate"),
            "max_positive_rate": item.get("max_positive_rate"),
        }
        for item in context_feature.get("mixed_by_instance", [])
    ]
    mixed_dataset_targets = [
        {
            "impact_dataset": item.get("impact_dataset"),
            "context_count": item.get("context_count"),
            "high_context_count": item.get("high_context_count"),
            "low_context_count": item.get("low_context_count"),
            "min_positive_rate": item.get("min_positive_rate"),
            "max_positive_rate": item.get("max_positive_rate"),
        }
        for item in context_feature.get("mixed_by_dataset", [])
    ]

    active_basis_counterexample_targets = {
        "false_positive_rows": _counterexample_rows(
            active_basis_counterexamples.get("false_positive_rows", [])
        ),
        "weaker_improved_than_strongest_noop_examples": _counterexample_rows(
            active_basis_counterexamples.get(
                "weaker_improved_than_strongest_noop_examples", []
            )
        ),
        "strongest_noop": _counterexample_rows(
            [active_basis_counterexamples.get("strongest_noop", {})]
        )[0],
    }

    collection_requirements = [
        {
            "requirement_id": "no_certificate_effect",
            "requirement": "所有采集行必须保持 official_effect_count=0。",
        },
        {
            "requirement_id": "addition_before_features_only",
            "requirement": (
                "selector 训练输入只能用加列前字段；impact label 只用于离线评估。"
            ),
        },
        {
            "requirement_id": "full_active_basis_snapshot",
            "requirement": (
                "必须记录 active-basis churn 和 RMP degeneracy pressure 所需的完整"
                " active journey/lambda snapshot。"
            ),
        },
        {
            "requirement_id": "context_instance_dataset_holdouts",
            "requirement": "补采后仍必须按 context / instance / dataset 三类 holdout 验证。",
        },
        {
            "requirement_id": "no_production_ab_before_selector_pass",
            "requirement": "selector 未通过前不得进入 production BPC A/B。",
        },
    ]

    checks = {
        "next_action_passed": next_action.get("all_checks_pass") is True,
        "context_fold_passed": context_fold.get("all_checks_pass") is True,
        "context_feature_passed": context_feature.get("all_checks_pass") is True,
        "counterexample_catalog_passed": counterexample_catalog.get("all_checks_pass")
        is True,
        "active_basis_counterexamples_passed": active_basis_counterexamples.get(
            "all_checks_pass"
        )
        is True,
        "status_is_collection_only": True,
        "twenty_failure_kinds_present": all(
            _as_int(twenty.get("context_failure_kind_counts", {}).get(kind)) > 0
            for kind in EXPECTED_FAILURE_KINDS
        ),
        "priority_targets_have_samples": all(
            target["sample_contexts"] for target in priority_context_targets
        ),
        "mixed_instance_targets_present": len(mixed_instance_targets) >= 2,
        "mixed_dataset_targets_present": len(mixed_dataset_targets) >= 2,
        "active_basis_counterexamples_present": (
            len(active_basis_counterexample_targets["false_positive_rows"]) >= 2
            and len(
                active_basis_counterexample_targets[
                    "weaker_improved_than_strongest_noop_examples"
                ]
            )
            > 0
        ),
        "required_fields_include_active_basis": (
            "active_basis_churn_count_before" in REQUIRED_CAPTURE_FIELDS
            and "rmp_degeneracy_pressure_before" in REQUIRED_CAPTURE_FIELDS
        ),
        "next_action_forbids_production_shortcuts": all(
            item in next_action.get("forbidden_actions", [])
            for item in [
                "default_enable_worker_or_audit",
                "open_official_certificate_gate",
                "enter_production_ab_before_selector_holdout",
            ]
        ),
    }

    return {
        "schema_version": "root_cause_selector_collection_plan_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "collect_no_certificate_effect_selector_holdout_data",
        "current_stage": "calibration_only_selector_holdout",
        "production_direction_proven": False,
        "priority_context_targets": priority_context_targets,
        "mixed_instance_targets": mixed_instance_targets,
        "mixed_dataset_targets": mixed_dataset_targets,
        "active_basis_counterexample_targets": active_basis_counterexample_targets,
        "required_capture_fields": REQUIRED_CAPTURE_FIELDS,
        "collection_requirements": collection_requirements,
        "pass_to_next_gate": [
            "new rows have official_effect_count=0",
            "candidate rows include full active-basis snapshot-derived fields",
            "selector using only addition-before features passes context holdout",
            "selector using only addition-before features passes instance holdout",
            "selector using only addition-before features passes dataset holdout",
        ],
        "still_forbidden": [
            "default worker/audit/probe enable",
            "official certificate gate",
            "production BPC A/B before selector holdout pass",
            "post-addition or hindsight features in online selector",
        ],
        "sources": {
            "next_action": str(next_action_path),
            "context_fold": str(context_fold_path),
            "context_feature": str(context_feature_path),
            "counterexample_catalog": str(counterexample_catalog_path),
            "active_basis_counterexamples": str(active_basis_counterexamples_path),
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Selector Collection Plan 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告把当前 selector failure evidence 转成补采目标。它只读已有",
        "summary，不运行 BPC / pricing / RMP / Pulse，也不改变 worker、",
        "certificate 或 solver 默认行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_selector_collection_plan = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"current_stage = {summary['current_stage']}",
        f"production_direction_proven = {str(summary['production_direction_proven']).lower()}",
        f"priority_context_target_count = {len(summary['priority_context_targets'])}",
        f"mixed_instance_target_count = {len(summary['mixed_instance_targets'])}",
        f"mixed_dataset_target_count = {len(summary['mixed_dataset_targets'])}",
        f"required_capture_field_count = {len(summary['required_capture_fields'])}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 优先补采的 context failure 类型",
        "",
    ]
    for target in summary["priority_context_targets"]:
        lines.extend(
            [
                f"### {target['target_id']}",
                "",
                f"当前 context 数：{target['current_context_count']}",
                "",
                f"原因：{target['why']}",
                "",
                f"标签要求：{target['required_label_mix']}",
                "",
                "样例 context：",
                "",
                "```json",
                json.dumps(target["sample_contexts"], ensure_ascii=False, indent=2, sort_keys=True),
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## 同 instance / dataset 混合目标",
            "",
            "这些目标证明 instance 或 dataset 身份不能解释 selector 成败，补采时应保留同一组内的 high 与 low/noop context。",
            "",
            "```json",
            json.dumps(
                {
                    "mixed_instance_targets": summary["mixed_instance_targets"],
                    "mixed_dataset_targets": summary["mixed_dataset_targets"],
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## Active-basis 反例目标",
            "",
            "这些行证明更负 true-RC / new-task-set / 单个 active-basis scalar 都不能单独作为 production selector。",
            "",
            "```json",
            json.dumps(
                summary["active_basis_counterexample_targets"],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## 必须采集字段",
            "",
        ]
    )
    for field in summary["required_capture_fields"]:
        lines.append(f"- `{field}`")

    lines.extend(["", "## 进入下一关前必须满足", ""])
    for item in summary["pass_to_next_gate"]:
        lines.append(f"- {item}")

    lines.extend(["", "## 仍然禁止", ""])
    for item in summary["still_forbidden"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## 检查项",
            "",
            "```json",
            json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--next-action", default=str(DEFAULT_NEXT_ACTION))
    parser.add_argument("--context-fold", default=str(DEFAULT_CONTEXT_FOLD))
    parser.add_argument("--context-feature", default=str(DEFAULT_CONTEXT_FEATURE))
    parser.add_argument(
        "--counterexample-catalog", default=str(DEFAULT_COUNTEREXAMPLE_CATALOG)
    )
    parser.add_argument(
        "--active-basis-counterexamples",
        default=str(DEFAULT_ACTIVE_BASIS_COUNTEREXAMPLES),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = build_plan(
        next_action_path=Path(args.next_action),
        context_fold_path=Path(args.context_fold),
        context_feature_path=Path(args.context_feature),
        counterexample_catalog_path=Path(args.counterexample_catalog),
        active_basis_counterexamples_path=Path(args.active_basis_counterexamples),
    )
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
