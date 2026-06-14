"""Build the next actionable root-cause plan from verified evidence.

This helper is diagnostic-only.  It reads existing summaries and writes a
machine-checkable action plan for the next allowed stage.  It does not run BPC,
pricing, RMP, Pulse, workers, certificates, or benchmarks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_CURRENT_ANSWER = Path(
    "BPC_future/results/root_cause_current_answer_20260614/summary.json"
)
DEFAULT_WORKER_NEGATIVE_ROI_BLOCKER = Path(
    "BPC_future/results/root_cause_worker_negative_column_roi_blocker_20260614/"
    "summary.json"
)
DEFAULT_NEXT_PROTOCOL = Path(
    "BPC_future/results/root_cause_next_evidence_protocol_catalog_20260614/"
    "summary.json"
)
DEFAULT_REGISTRY = Path(
    "BPC_future/results/root_cause_optimization_direction_candidate_registry_20260614/"
    "summary.json"
)
DEFAULT_SELECTOR_BLOCKER = Path(
    "BPC_future/results/root_cause_production_selector_blocker_catalog_20260614/"
    "summary.json"
)
DEFAULT_OBJECTIVE_AUDIT = Path(
    "BPC_future/results/root_cause_objective_completion_audit_20260614/summary.json"
)
DEFAULT_COUNTEREXAMPLES = Path(
    "BPC_future/results/root_cause_active_basis_snapshot_counterexamples_20260614/"
    "summary.json"
)
DEFAULT_HOLDOUT_GAP_MATRIX = Path(
    "BPC_future/results/root_cause_selector_holdout_gap_matrix_20260614/summary.json"
)
DEFAULT_TARGET_PRIORITY_MATRIX = Path(
    "BPC_future/results/root_cause_selector_holdout_target_priority_matrix_20260614/"
    "summary.json"
)
DEFAULT_PRIORITY_CAPTURE_MISS = Path(
    "BPC_future/results/root_cause_selector_holdout_priority_capture_miss_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/root_cause_next_action_plan_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_next_action_plan_zh.md"
)

EXPECTED_ALLOWED_STAGE = "calibration_only_selector_holdout"
EXPECTED_MISSING_REQUIREMENTS = [
    "five_ten_full_no_regression_ab",
    "production_validated_selector",
    "twenty_walltime_speedup",
]
EXPECTED_REQUIRED_HOLDOUTS = ["context", "instance", "dataset"]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _action(action_id: str, title: str, why: str, required_output: str) -> dict[str, str]:
    return {
        "action_id": action_id,
        "title": title,
        "why": why,
        "required_output": required_output,
    }


def _category_count(summary: dict[str, Any], key: str) -> int:
    categories = summary.get("category_counts", {}) or {}
    return _as_int(categories.get(key, summary.get(f"{key}_context_count")))


def build_plan(
    *,
    current_answer_path: Path,
    worker_negative_roi_blocker_path: Path,
    next_protocol_path: Path,
    registry_path: Path,
    selector_blocker_path: Path,
    objective_audit_path: Path,
    counterexamples_path: Path,
    holdout_gap_matrix_path: Path,
    target_priority_matrix_path: Path,
    priority_capture_miss_path: Path,
) -> dict[str, Any]:
    current_answer = _read_json(current_answer_path)
    worker_negative_roi_blocker = _read_json(worker_negative_roi_blocker_path)
    next_protocol = _read_json(next_protocol_path)
    registry = _read_json(registry_path)
    selector_blocker = _read_json(selector_blocker_path)
    objective_audit = _read_json(objective_audit_path)
    counterexamples = _read_json(counterexamples_path)
    holdout_gap_matrix = _read_json(holdout_gap_matrix_path)
    target_priority_matrix = _read_json(target_priority_matrix_path)
    priority_capture_miss = _read_json(priority_capture_miss_path)
    worker_phase7o = worker_negative_roi_blocker.get("phase7o_expanded", {})
    worker_phase8q = worker_negative_roi_blocker.get("phase8q_validation", {})

    missing_requirements = list(objective_audit.get("missing_requirements", []))
    required_holdouts = list(next_protocol.get("required_selector_holdouts", []))
    blockers = [str(item.get("blocker_id", "")) for item in selector_blocker.get("blockers", [])]

    immediate_actions = [
        _action(
            "extend_no_certificate_effect_exact_context_replay",
            "扩展 no-certificate-effect exact-context replay / active-basis snapshot 数据",
            (
                "现有数据已经能说明 true-RC / new-task-set / 单个 active-basis scalar "
                "不足，但还没有 production selector；gap matrix 进一步显示 complete "
                "full-snapshot rows 的 noop/mixed 覆盖太稀疏，priority capture miss "
                "显示单纯 source profile rerun 不能保证回到目标 context。"
            ),
            (
                "所有 rows 必须保持 official_effect_count=0，并包含 returned batch、"
                "true-RC、task-set、sequence、context hash、active-basis churn、"
                "RMP degeneracy pressure、explicit forbidden signature payload 与 "
                "replay impact label。"
            ),
        ),
        _action(
            "fit_addition_before_selector_only",
            "只用 addition-before 特征校准 selector",
            (
                "hindsight / post-addition 特征不能在线使用；worker 找到负列也不是 "
                "production ROI 证明。"
            ),
            (
                "selector 输入必须排除 post-addition / hindsight 字段，并输出 "
                "context / instance / dataset holdout 指标。"
            ),
        ),
        _action(
            "require_all_holdout_pass_before_ab",
            "通过 context / instance / dataset holdout 后才进入 BPC A/B",
            (
                "当前 blocker catalog 仍有 concrete false positive/false negative、"
                "fold gate 不稳定、rule family 无全 fold 规则等阻塞项。"
            ),
            (
                "必须生成 production_selector_validated=true 的 summary，且 "
                "blocker_count=0。"
            ),
        ),
        _action(
            "run_5_10_no_regression_before_20_speedup",
            "先跑 5/10 full no-regression，再跑 selected 20 hard-repeat speedup",
            (
                "5/10 已证明对触发式固定开销敏感；不能直接把 20-task worker "
                "策略推到 production。"
            ),
            (
                "5/10 full A/B 必须无 official regression；20-task hard-repeat "
                "必须显示 wall-time / gap / status / tail 改善。"
            ),
        ),
    ]

    forbidden_actions = [
        "default_enable_worker_or_audit",
        "increase_worker_budget_without_selector_roi",
        "open_official_certificate_gate",
        "treat_true_rc_or_new_task_set_as_selector",
        "use_post_addition_or_hindsight_features_online",
        "enter_production_ab_before_selector_holdout",
        "claim_goal_complete_without_5_10_and_20_ab",
    ]

    immediate_subactions = [
        {
            "subaction_id": "collect_mixed_noop_full_snapshot_contexts",
            "parent_action_id": "extend_no_certificate_effect_exact_context_replay",
            "why": (
                "priority matrix reports mixed/noop contexts without complete "
                "full-snapshot coverage; these are the rows needed to test selector "
                "false positives and false negatives."
            ),
            "required_output": (
                "complete full-snapshot rows with both improved and noop labels, "
                "not only positive component payload rows."
            ),
        },
        {
            "subaction_id": "collect_explicit_forbidden_payload_for_noop_contexts",
            "parent_action_id": "extend_no_certificate_effect_exact_context_replay",
            "why": (
                "current complete explicit-forbidden rows are positive-only, so they "
                "cannot calibrate a production reject rule."
            ),
            "required_output": (
                "explicit forbidden signature payload for noop and mixed contexts, "
                "with no certificate or official-bound effect."
            ),
        },
        {
            "subaction_id": "replace_source_profile_rerun_with_context_trajectory_protocol",
            "parent_action_id": "extend_no_certificate_effect_exact_context_replay",
            "why": (
                "priority capture miss shows 0 exact hits for 3 expected contexts: "
                "two did not reach the source active hash and one drifted in pool/"
                "forbidden/returned-batch components despite the same active hash."
            ),
            "required_output": (
                "next capture protocol must record and target context components "
                "beyond active hash: pool signature, forbidden signature, returned "
                "batch, RMP objective, and pricing outcome."
            ),
        },
    ]

    pass_to_ab_conditions = [
        "selector_feature_scope == addition_before_only",
        "required_holdouts == context,instance,dataset",
        "production_validated_selector == true",
        "selector_blocker_count == 0",
        "no certificate effect in replay/capture rows",
        "worker default remains disabled before A/B",
        "official certificate gate remains closed before A/B",
    ]

    stop_conditions = [
        {
            "condition": "selector fails any context/instance/dataset holdout",
            "decision": "stay in calibration; do not run production A/B",
        },
        {
            "condition": "5/10 production candidate A/B regresses",
            "decision": "reject selector/gate even if 20-task signal exists",
        },
        {
            "condition": "20 hard-repeat A/B has no wall-time/gap/status/tail improvement",
            "decision": "reject optimization direction as insufficient",
        },
    ]

    checks = {
        "current_answer_passed": current_answer.get("all_checks_pass") is True,
        "next_protocol_passed": next_protocol.get("all_checks_pass") is True,
        "registry_passed": registry.get("all_checks_pass") is True,
        "selector_blocker_passed": selector_blocker.get("all_checks_pass") is True,
        "worker_negative_roi_blocker_passed": (
            worker_negative_roi_blocker.get("all_checks_pass") is True
            and worker_negative_roi_blocker.get("diagnostic_only") is True
            and worker_negative_roi_blocker.get("runs_bpc_or_pricing") is False
            and worker_negative_roi_blocker.get("status")
            == "worker_negative_columns_not_sufficient_for_roi"
            and _as_int(worker_phase7o.get("nonbaseline_rows")) == 96
            and _as_int(worker_phase7o.get("nonbaseline_worsened_rows")) == 96
            and _as_int(worker_phase7o.get("worker_added_journeys")) == 63
            and _as_int(worker_phase8q.get("worker_added_journeys")) == 10
            and _as_int(
                worker_negative_roi_blocker.get(
                    "phase8q_improved_without_worker_added_count"
                )
            )
            == 1
        ),
        "objective_audit_passed": objective_audit.get("all_checks_pass") is True,
        "counterexamples_passed": counterexamples.get("all_checks_pass") is True,
        "allowed_stage_is_calibration_only": registry.get("current_allowed_next_stage")
        == EXPECTED_ALLOWED_STAGE,
        "no_approved_production_direction": _as_int(
            registry.get("approved_production_direction_count")
        )
        == 0,
        "production_direction_not_proven": registry.get("production_direction_proven")
        is False,
        "missing_requirements_match_expected": missing_requirements
        == EXPECTED_MISSING_REQUIREMENTS,
        "required_holdouts_match_expected": required_holdouts
        == EXPECTED_REQUIRED_HOLDOUTS,
        "selector_blockers_still_present": len(blockers) > 0
        and selector_blocker.get("status") == "production_selector_not_validated",
        "counterexample_blocks_simple_true_rc": (
            _as_int(counterexamples.get("task20_row_count")) == 12
            and _as_int(counterexamples.get("task20_new_task_set_row_count")) == 12
            and len(counterexamples.get("false_positive_rows", [])) > 0
            and _as_int(counterexamples.get("weaker_improved_than_strongest_noop_count"))
            > 0
        ),
        "holdout_gap_requires_negative_mixed_contexts": (
            holdout_gap_matrix.get("all_checks_pass") is True
            and holdout_gap_matrix.get("recommended_next_stage")
            == "collect_negative_and_mixed_full_snapshot_contexts"
            and _as_int(
                (
                    holdout_gap_matrix.get("complete_snapshot_total", {}) or {}
                ).get("row_count")
            )
            > 0
        ),
        "target_priority_requires_noop_mixed_full_snapshot": (
            target_priority_matrix.get("all_checks_pass") is True
            and target_priority_matrix.get("recommended_next_stage")
            == "collect_priority_negative_noop_mixed_full_snapshot_contexts"
            and _category_count(target_priority_matrix, "mixed_missing_full_snapshot") > 0
            and _category_count(target_priority_matrix, "noop_missing_full_snapshot") > 0
        ),
        "priority_capture_miss_blocks_source_profile_rerun_shortcut": (
            priority_capture_miss.get("all_checks_pass") is True
            and priority_capture_miss.get("status")
            == "selector_holdout_priority_capture_miss_diagnosed"
            and _as_int(priority_capture_miss.get("expected_context_count")) > 0
            and _as_int(priority_capture_miss.get("exact_hit_context_count")) == 0
            and (
                _as_int(
                    priority_capture_miss.get(
                        "source_active_hash_missing_context_count"
                    )
                )
                + _as_int(
                    priority_capture_miss.get(
                        "same_active_component_drift_context_count"
                    )
                )
                == _as_int(priority_capture_miss.get("expected_context_count"))
            )
        ),
        "action_plan_has_required_items": len(immediate_actions) == 4
        and len(immediate_subactions) == 3
        and len(forbidden_actions) == 7
        and len(pass_to_ab_conditions) == 7
        and len(stop_conditions) == 3,
    }

    return {
        "schema_version": "root_cause_next_action_plan_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "calibration_only_next_action",
        "root_cause_short": current_answer.get("current_answer"),
        "current_allowed_stage": registry.get("current_allowed_next_stage"),
        "production_direction_proven": registry.get("production_direction_proven"),
        "goal_complete": objective_audit.get("goal_complete"),
        "missing_requirements": missing_requirements,
        "required_selector_holdouts": required_holdouts,
        "selector_blocker_ids": blockers,
        "worker_negative_roi_blocker_evidence": {
            "status": worker_negative_roi_blocker.get("status"),
            "phase7o_nonbaseline_rows": worker_phase7o.get("nonbaseline_rows"),
            "phase7o_nonbaseline_worsened_rows": worker_phase7o.get(
                "nonbaseline_worsened_rows"
            ),
            "phase7o_worker_added_journeys": worker_phase7o.get(
                "worker_added_journeys"
            ),
            "phase7o_worker_added_new_task_sets": worker_phase7o.get(
                "worker_added_new_task_sets"
            ),
            "phase7o_worker_added_support_changing": worker_phase7o.get(
                "worker_added_support_changing"
            ),
            "phase8q_worker_added_journeys": worker_phase8q.get(
                "worker_added_journeys"
            ),
            "phase8q_worker_added_rows": worker_phase8q.get("worker_added_rows"),
            "phase8q_improved_without_worker_added_count": (
                worker_negative_roi_blocker.get(
                    "phase8q_improved_without_worker_added_count"
                )
            ),
        },
        "immediate_actions": immediate_actions,
        "immediate_subactions": immediate_subactions,
        "pass_to_production_ab_conditions": pass_to_ab_conditions,
        "stop_conditions": stop_conditions,
        "forbidden_actions": forbidden_actions,
        "holdout_gap_evidence": {
            "recommended_next_stage": holdout_gap_matrix.get("recommended_next_stage"),
            "total_candidate_row_count": holdout_gap_matrix.get(
                "total_candidate_row_count"
            ),
            "complete_snapshot_row_count": (
                holdout_gap_matrix.get("complete_snapshot_total", {}) or {}
            ).get("row_count"),
            "complete_snapshot_label_counts": (
                holdout_gap_matrix.get("complete_snapshot_total", {}) or {}
            ).get("label_counts"),
            "complete_snapshot_mixed_context_count": (
                holdout_gap_matrix.get("complete_snapshot_context_label_mix", {})
                or {}
            ).get("mixed_label_context_count"),
            "complete_snapshot_noop_only_context_count": (
                holdout_gap_matrix.get("complete_snapshot_context_label_mix", {})
                or {}
            ).get("noop_only_context_count"),
            "complete_snapshot_positive_only_context_count": (
                holdout_gap_matrix.get("complete_snapshot_context_label_mix", {})
                or {}
            ).get("positive_only_context_count"),
            "complete_explicit_forbidden_label_counts": (
                holdout_gap_matrix.get("complete_explicit_forbidden_total", {}) or {}
            ).get("label_counts"),
            "complete_explicit_forbidden_row_count": (
                holdout_gap_matrix.get("complete_explicit_forbidden_total", {}) or {}
            ).get("row_count"),
            "complete_explicit_forbidden_mixed_context_count": (
                holdout_gap_matrix.get(
                    "complete_explicit_forbidden_context_label_mix", {}
                )
                or {}
            ).get("mixed_label_context_count"),
            "complete_explicit_forbidden_noop_only_context_count": (
                holdout_gap_matrix.get(
                    "complete_explicit_forbidden_context_label_mix", {}
                )
                or {}
            ).get("noop_only_context_count"),
            "complete_explicit_forbidden_positive_only_context_count": (
                holdout_gap_matrix.get(
                    "complete_explicit_forbidden_context_label_mix", {}
                )
                or {}
            ).get("positive_only_context_count"),
        },
        "target_priority_evidence": {
            "recommended_next_stage": target_priority_matrix.get(
                "recommended_next_stage"
            ),
            "priority_context_count": target_priority_matrix.get(
                "priority_context_count"
            ),
            "mixed_missing_full_snapshot_context_count": _category_count(
                target_priority_matrix, "mixed_missing_full_snapshot"
            ),
            "noop_missing_full_snapshot_context_count": _category_count(
                target_priority_matrix, "noop_missing_full_snapshot"
            ),
            "uncovered_priority_context_count": target_priority_matrix.get(
                "uncovered_priority_context_count"
            ),
            "top_priority_contexts": [
                item.get("context_hash")
                for item in (target_priority_matrix.get("top_priority_targets") or [])[:5]
            ],
        },
        "priority_capture_miss_evidence": {
            "status": priority_capture_miss.get("status"),
            "expected_context_count": priority_capture_miss.get(
                "expected_context_count"
            ),
            "exact_hit_context_count": priority_capture_miss.get(
                "exact_hit_context_count"
            ),
            "source_active_hash_missing_context_count": priority_capture_miss.get(
                "source_active_hash_missing_context_count"
            ),
            "same_active_component_drift_context_count": priority_capture_miss.get(
                "same_active_component_drift_context_count"
            ),
            "observed_event_count": priority_capture_miss.get("observed_event_count"),
        },
        "sources": {
            "current_answer": str(current_answer_path),
            "worker_negative_roi_blocker": str(worker_negative_roi_blocker_path),
            "next_protocol": str(next_protocol_path),
            "registry": str(registry_path),
            "selector_blocker": str(selector_blocker_path),
            "objective_audit": str(objective_audit_path),
            "counterexamples": str(counterexamples_path),
            "holdout_gap_matrix": str(holdout_gap_matrix_path),
            "target_priority_matrix": str(target_priority_matrix_path),
            "priority_capture_miss": str(priority_capture_miss_path),
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Next Action Plan 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告把当前根因结论转成下一步可执行证据门槛。它只读已有",
        "summary，不运行 BPC / pricing / RMP / Pulse，也不改变 worker 或",
        "certificate 默认行为。",
        "",
        "## 当前结论",
        "",
        summary["root_cause_short"],
        "",
        "```text",
        f"root_cause_next_action_plan = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"current_allowed_stage = {summary['current_allowed_stage']}",
        f"production_direction_proven = {str(summary['production_direction_proven']).lower()}",
        f"goal_complete = {str(summary['goal_complete']).lower()}",
        "missing_requirements = " + ",".join(summary["missing_requirements"]),
        "required_selector_holdouts = " + ",".join(summary["required_selector_holdouts"]),
        f"selector_blocker_count = {len(summary['selector_blocker_ids'])}",
        "holdout_gap_recommended_next_stage = "
        f"{summary['holdout_gap_evidence']['recommended_next_stage']}",
        "target_priority_recommended_next_stage = "
        f"{summary['target_priority_evidence']['recommended_next_stage']}",
        "worker_negative_roi_blocker_status = "
        f"{summary['worker_negative_roi_blocker_evidence']['status']}",
        "worker_negative_phase7o_nonbaseline_worsened_rows = "
        f"{summary['worker_negative_roi_blocker_evidence']['phase7o_nonbaseline_worsened_rows']}",
        "priority_capture_miss_status = "
        f"{summary['priority_capture_miss_evidence']['status']}",
        "priority_capture_miss_exact_hit_context_count = "
        f"{summary['priority_capture_miss_evidence']['exact_hit_context_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 现在允许做什么",
        "",
    ]
    for item in summary["immediate_actions"]:
        lines.extend(
            [
                f"### {item['action_id']}",
                "",
                item["title"],
                "",
                f"原因：{item['why']}",
                "",
                f"产物要求：{item['required_output']}",
                "",
            ]
        )

    lines.extend(["## 立即子动作", ""])
    for item in summary["immediate_subactions"]:
        lines.extend(
            [
                f"### {item['subaction_id']}",
                "",
                f"父动作：{item['parent_action_id']}",
                "",
                f"原因：{item['why']}",
                "",
                f"产物要求：{item['required_output']}",
            "",
        ]
    )

    lines.extend(
        [
            "## 最新缺口证据",
            "",
            "### Worker Negative ROI Blocker",
            "",
            "```json",
            json.dumps(
                summary["worker_negative_roi_blocker_evidence"],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            (
                "解释：worker 能加入 true-RC negative columns，但 Phase 7O expanded "
                "仍是全部 non-baseline worsened，Phase 8Q 的 worker-added rows 也没有"
                "成为 improved rows。因此下一步不能简单增加 worker 预算或默认启用 worker。"
            ),
            "",
            "### Holdout Gap",
            "",
            "```json",
            json.dumps(
                summary["holdout_gap_evidence"],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "### Target Priority",
            "",
            "```json",
            json.dumps(
                summary["target_priority_evidence"],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "### Priority Capture Miss",
            "",
            "```json",
            json.dumps(
                summary["priority_capture_miss_evidence"],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
        ]
    )

    lines.extend(["## 进入 production A/B 前必须满足", ""])
    for condition in summary["pass_to_production_ab_conditions"]:
        lines.append(f"- {condition}")

    lines.extend(["", "## 失败即停止条件", ""])
    for item in summary["stop_conditions"]:
        lines.append(f"- {item['condition']} -> {item['decision']}")

    lines.extend(["", "## 现在禁止做什么", ""])
    for action in summary["forbidden_actions"]:
        lines.append(f"- {action}")

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
    parser.add_argument("--current-answer", default=str(DEFAULT_CURRENT_ANSWER))
    parser.add_argument(
        "--worker-negative-roi-blocker",
        default=str(DEFAULT_WORKER_NEGATIVE_ROI_BLOCKER),
    )
    parser.add_argument("--next-protocol", default=str(DEFAULT_NEXT_PROTOCOL))
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--selector-blocker", default=str(DEFAULT_SELECTOR_BLOCKER))
    parser.add_argument("--objective-audit", default=str(DEFAULT_OBJECTIVE_AUDIT))
    parser.add_argument("--counterexamples", default=str(DEFAULT_COUNTEREXAMPLES))
    parser.add_argument("--holdout-gap-matrix", default=str(DEFAULT_HOLDOUT_GAP_MATRIX))
    parser.add_argument(
        "--target-priority-matrix", default=str(DEFAULT_TARGET_PRIORITY_MATRIX)
    )
    parser.add_argument("--priority-capture-miss", default=str(DEFAULT_PRIORITY_CAPTURE_MISS))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = build_plan(
        current_answer_path=Path(args.current_answer),
        worker_negative_roi_blocker_path=Path(args.worker_negative_roi_blocker),
        next_protocol_path=Path(args.next_protocol),
        registry_path=Path(args.registry),
        selector_blocker_path=Path(args.selector_blocker),
        objective_audit_path=Path(args.objective_audit),
        counterexamples_path=Path(args.counterexamples),
        holdout_gap_matrix_path=Path(args.holdout_gap_matrix),
        target_priority_matrix_path=Path(args.target_priority_matrix),
        priority_capture_miss_path=Path(args.priority_capture_miss),
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
