#!/usr/bin/env python3
"""Audit the next feature gate for a production addition-before selector.

This diagnostic is intentionally read-only with respect to solver behavior.  It
only connects existing selector/context summaries and records which feature
families are blocked, calibration-only, or still missing before any production
worker/default/certificate path can be considered.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_CONTEXT_GAP = Path(
    "BPC_future/results/root_cause_selector_context_sufficiency_gap_20260614/"
    "summary.json"
)
DEFAULT_SNAPSHOT_SIGNAL = Path(
    "BPC_future/results/root_cause_active_basis_snapshot_selector_signal_20260614/"
    "summary.json"
)
DEFAULT_SNAPSHOT_COUNTEREXAMPLES = Path(
    "BPC_future/results/root_cause_active_basis_snapshot_counterexamples_20260614/"
    "summary.json"
)
DEFAULT_ENRICHED_RMP_HOLDOUT = Path(
    "BPC_future/results/root_cause_selector_enriched_rmp_feature_holdout_20260614/"
    "summary.json"
)
DEFAULT_ENRICHED_MODEL_HOLDOUT = Path(
    "BPC_future/results/root_cause_selector_enriched_multifeature_model_holdout_20260614/"
    "summary.json"
)
DEFAULT_COLLECTION_CAPTURE_AUDIT = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_capture_audit_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_next_feature_gate_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_next_feature_gate_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def audit(
    *,
    context_gap_path: Path,
    snapshot_signal_path: Path,
    snapshot_counterexamples_path: Path,
    enriched_rmp_holdout_path: Path,
    enriched_model_holdout_path: Path,
    collection_capture_audit_path: Path,
) -> dict[str, Any]:
    context_gap = _read_json(context_gap_path)
    snapshot_signal = _read_json(snapshot_signal_path)
    snapshot_counterexamples = _read_json(snapshot_counterexamples_path)
    enriched_rmp = _read_json(enriched_rmp_holdout_path)
    enriched_model = _read_json(enriched_model_holdout_path)
    collection_capture = _read_json(collection_capture_audit_path)

    false_positive_rows = list(
        snapshot_counterexamples.get("false_positive_rows", []) or []
    )
    strongest_noop = snapshot_counterexamples.get("strongest_noop") or {}
    required_next_feature_families = list(
        context_gap.get("required_next_feature_families", []) or []
    )
    robust_single_count = int(
        context_gap.get("robust_single_feature_selector_count") or 0
    )
    robust_model_count = int(
        context_gap.get("robust_multifeature_model_count") or 0
    )
    robust_enriched_feature_count = int(
        enriched_rmp.get("robust_all_holdout_enriched_feature_count") or 0
    )
    robust_numeric_feature_count = int(
        enriched_rmp.get("robust_all_holdout_numeric_feature_count") or 0
    )
    robust_multifeature_count = int(
        enriched_model.get("robust_all_holdout_model_count") or 0
    )

    blocked_feature_families = [
        {
            "family": "true_rc_threshold",
            "status": "blocked",
            "reason": (
                "true-RC 阈值在 active-basis snapshot rows 中仍有 false positive，"
                "不能作为 production selector。"
            ),
            "evidence": {
                "task20_true_rc_threshold_fp": snapshot_signal.get(
                    "task20_true_rc_threshold_metrics", {}
                ).get("fp"),
                "strongest_noop_true_reduced_cost": strongest_noop.get(
                    "true_reduced_cost"
                ),
            },
        },
        {
            "family": "new_task_set_only",
            "status": "blocked",
            "reason": (
                "20-task snapshot rows 全部是 new task-set，但仍同时存在 improved "
                "和 noop，new-task-set 本身不能判定 downstream impact。"
            ),
            "evidence": {
                "task20_new_task_set_row_count": snapshot_signal.get(
                    "task20_new_task_set_row_count"
                ),
                "task20_label_counts": snapshot_signal.get("task20_label_counts"),
            },
        },
        {
            "family": "active_basis_scalar_only",
            "status": "blocked",
            "reason": (
                "active-basis churn / degeneracy scalar 有信号但标签混合，"
                "不能单独跨 context/instance/dataset 泛化。"
            ),
            "evidence": {
                "positive_churn_label_counts": snapshot_counterexamples.get(
                    "positive_churn_label_counts"
                ),
                "degeneracy_one_label_counts": snapshot_counterexamples.get(
                    "degeneracy_one_label_counts"
                ),
            },
        },
        {
            "family": "current_enriched_single_or_multifeature_selector",
            "status": "blocked",
            "reason": (
                "当前 enriched single-feature 与 shallow multifeature holdout "
                "没有任何 robust all-holdout selector/model。"
            ),
            "evidence": {
                "robust_single_feature_selector_count": robust_single_count,
                "robust_multifeature_model_count": robust_model_count,
                "robust_enriched_feature_count": robust_enriched_feature_count,
                "robust_numeric_feature_count": robust_numeric_feature_count,
                "robust_multifeature_count": robust_multifeature_count,
            },
        },
    ]
    calibration_only_feature_families = [
        {
            "family": "active_basis_full_snapshot_features",
            "status": "calibration_only",
            "reason": (
                "字段已经能采集并进入 candidate rows，但当前样本和 holdout "
                "仍不足以形成 production selector。"
            ),
        },
        {
            "family": "recent_rmp_trajectory_features",
            "status": "calibration_only",
            "reason": (
                "recent objective/dual/addition trajectory 是 addition-before "
                "可观测信号，但当前 enriched holdout 不稳定。"
            ),
        },
    ]
    missing_or_required_feature_families = [
        {
            "family": family,
            "status": "required_before_production_selector",
            "reason": (
                "当前证据显示 active_hash 和 aggregate/proxy 字段不足以区分 "
                "pool/forbidden/returned-batch 分叉，需要更细的可泛化上下文表示。"
            ),
        }
        for family in required_next_feature_families
    ]
    forbidden_next_actions = [
        "default_worker",
        "official_certificate_gate",
        "production_bpc_ab_before_selector_holdout",
        "selector_using_post_addition_or_hindsight_features",
        "simple_true_rc_or_new_task_set_rule_as_production_gate",
    ]
    allowed_next_actions = [
        "collect_no_certificate_effect_selector_holdout_contexts",
        "add_pool_signature_composition_features",
        "add_forbidden_signature_pressure_features",
        "add_returned_batch_vs_pool_overlap_features",
        "rerun_context_instance_dataset_holdout",
    ]
    checks = {
        "context_gap_current": context_gap.get("all_checks_pass") is True
        and context_gap.get("selector_context_status")
        == "insufficient_for_production_selector",
        "active_basis_snapshot_has_false_positive_rows": len(false_positive_rows) >= 1,
        "snapshot_signal_has_no_perfect_single_feature_rule": int(
            snapshot_signal.get("perfect_single_feature_rule_count") or 0
        )
        == 0,
        "enriched_single_feature_has_no_robust_selector": (
            robust_enriched_feature_count == 0 and robust_numeric_feature_count == 0
        ),
        "enriched_multifeature_has_no_robust_model": robust_multifeature_count == 0,
        "collection_not_ready_for_selector_holdout": collection_capture.get(
            "ready_for_selector_holdout"
        )
        is False,
        "missing_expected_context_remains": int(
            collection_capture.get("missing_expected_context_count") or 0
        )
        == 1,
        "forbidden_actions_block_production_shortcuts": bool(forbidden_next_actions),
    }
    return {
        "schema_version": "root_cause_selector_next_feature_gate_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_next_feature_gate_audited",
        "selector_next_feature_gate_status": (
            "blocked_until_extended_context_features_and_holdout"
        ),
        "context_gap_source": str(context_gap_path),
        "snapshot_signal_source": str(snapshot_signal_path),
        "snapshot_counterexamples_source": str(snapshot_counterexamples_path),
        "enriched_rmp_holdout_source": str(enriched_rmp_holdout_path),
        "enriched_model_holdout_source": str(enriched_model_holdout_path),
        "collection_capture_audit_source": str(collection_capture_audit_path),
        "blocked_feature_families": blocked_feature_families,
        "calibration_only_feature_families": calibration_only_feature_families,
        "missing_or_required_feature_families": missing_or_required_feature_families,
        "allowed_next_actions": allowed_next_actions,
        "forbidden_next_actions": forbidden_next_actions,
        "false_positive_count": len(false_positive_rows),
        "strongest_noop_true_reduced_cost": strongest_noop.get("true_reduced_cost"),
        "robust_single_feature_selector_count": robust_single_count,
        "robust_multifeature_model_count": robust_model_count,
        "collection_ready_for_selector_holdout": collection_capture.get(
            "ready_for_selector_holdout"
        ),
        "collection_missing_expected_context_count": collection_capture.get(
            "missing_expected_context_count"
        ),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "当前证据支持继续做 calibration-only selector holdout 和上下文字段补强，"
            "但不支持把 true-RC 阈值、new-task-set、active-basis scalar 或现有 "
            "enriched multifeature model 作为 production gate。下一步必须补充 "
            "pool/forbidden signature composition 与 returned-batch-vs-pool overlap "
            "等 addition-before 上下文特征，再重新做 context/instance/dataset holdout。"
        ),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Selector Next Feature Gate 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告只读现有 selector / active-basis / context sufficiency summary，",
        "把下一步 production selector 前的特征门槛写成机器可复查字段。",
        "它不运行 BPC / pricing / RMP / Pulse，也不改变 worker、certificate 或 solver 默认行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_selector_next_feature_gate = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        "selector_next_feature_gate_status = "
        f"{summary['selector_next_feature_gate_status']}",
        f"false_positive_count = {summary['false_positive_count']}",
        "strongest_noop_true_reduced_cost = "
        f"{summary['strongest_noop_true_reduced_cost']}",
        "robust_single_feature_selector_count = "
        f"{summary['robust_single_feature_selector_count']}",
        "robust_multifeature_model_count = "
        f"{summary['robust_multifeature_model_count']}",
        "collection_ready_for_selector_holdout = "
        f"{str(summary['collection_ready_for_selector_holdout']).lower()}",
        "collection_missing_expected_context_count = "
        f"{summary['collection_missing_expected_context_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## Blocked Feature Families",
        "",
        "```json",
        json.dumps(
            summary["blocked_feature_families"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Missing Or Required Feature Families",
        "",
        "```json",
        json.dumps(
            summary["missing_or_required_feature_families"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Allowed Next Actions",
        "",
        "```json",
        json.dumps(
            summary["allowed_next_actions"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Forbidden Next Actions",
        "",
        "```json",
        json.dumps(
            summary["forbidden_next_actions"],
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
    parser.add_argument("--context-gap", default=str(DEFAULT_CONTEXT_GAP))
    parser.add_argument("--snapshot-signal", default=str(DEFAULT_SNAPSHOT_SIGNAL))
    parser.add_argument(
        "--snapshot-counterexamples", default=str(DEFAULT_SNAPSHOT_COUNTEREXAMPLES)
    )
    parser.add_argument(
        "--enriched-rmp-holdout", default=str(DEFAULT_ENRICHED_RMP_HOLDOUT)
    )
    parser.add_argument(
        "--enriched-model-holdout", default=str(DEFAULT_ENRICHED_MODEL_HOLDOUT)
    )
    parser.add_argument(
        "--collection-capture-audit",
        default=str(DEFAULT_COLLECTION_CAPTURE_AUDIT),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = audit(
        context_gap_path=Path(args.context_gap),
        snapshot_signal_path=Path(args.snapshot_signal),
        snapshot_counterexamples_path=Path(args.snapshot_counterexamples),
        enriched_rmp_holdout_path=Path(args.enriched_rmp_holdout),
        enriched_model_holdout_path=Path(args.enriched_model_holdout),
        collection_capture_audit_path=Path(args.collection_capture_audit),
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
