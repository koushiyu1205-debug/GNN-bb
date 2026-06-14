#!/usr/bin/env python3
"""Build the current concise answer for the BPC_future root-cause goal.

This diagnostic-only script reads existing evidence summaries and writes a
short report that answers the user's recurring question: what is currently
known, what has been ruled out, and why the goal is still active.
It does not run BPC, pricing, RMP, Pulse, workers, or certificates.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_LEDGER = Path("BPC_future/results/root_cause_evidence_ledger_20260613/summary.json")
DEFAULT_WHY = Path("BPC_future/results/root_cause_why_many_attempts_failed_20260614/summary.json")
DEFAULT_WORKER_NEGATIVE_ROI_BLOCKER = Path(
    "BPC_future/results/root_cause_worker_negative_column_roi_blocker_20260614/"
    "summary.json"
)
DEFAULT_OBJECTIVE_AUDIT = Path(
    "BPC_future/results/root_cause_objective_completion_audit_20260614/summary.json"
)
DEFAULT_PRODUCTION_GATE = Path(
    "BPC_future/results/root_cause_production_ab_entry_gate_catalog_20260614/summary.json"
)
DEFAULT_COUNTEREXAMPLES = Path(
    "BPC_future/results/root_cause_active_basis_snapshot_counterexamples_20260614/"
    "summary.json"
)
DEFAULT_CONTEXT_SCHEMA_GAP = Path(
    "BPC_future/results/root_cause_selector_context_schema_gap_20260614/summary.json"
)
DEFAULT_SNAPSHOT_SAMPLE_COVERAGE = Path(
    "BPC_future/results/root_cause_selector_snapshot_sample_coverage_20260614/"
    "summary.json"
)
DEFAULT_TARGET002_PROBE_MATRIX = Path(
    "BPC_future/results/root_cause_selector_holdout_target002_probe_matrix_20260614/"
    "summary.json"
)
DEFAULT_TARGET002_TRAJECTORY_BRANCH = Path(
    "BPC_future/results/root_cause_selector_holdout_target002_trajectory_branch_20260614/"
    "summary.json"
)
DEFAULT_COMPONENT_CAPTURE_SCHEMA = Path(
    "BPC_future/results/root_cause_selector_component_capture_schema_contract_20260614/"
    "summary.json"
)
DEFAULT_COMPONENT_PAYLOAD_ROWS = Path(
    "BPC_future/results/root_cause_component_payload_addition_before_rows_20260614/"
    "summary.json"
)
DEFAULT_COMPONENT_PAYLOAD_HOLDOUT_EXTENSION = Path(
    "BPC_future/results/"
    "root_cause_component_payload_selector_holdout_extension_20260614/summary.json"
)
DEFAULT_SELECTOR_HOLDOUT_GAP_MATRIX = Path(
    "BPC_future/results/root_cause_selector_holdout_gap_matrix_20260614/"
    "summary.json"
)
DEFAULT_SELECTOR_TARGET_PRIORITY_MATRIX = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_target_priority_matrix_20260614/summary.json"
)
DEFAULT_PRIORITY_COLLECTION_RUNBOOK = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_priority_collection_runbook_20260614/summary.json"
)
DEFAULT_PRIORITY_COLLECTION_CAPTURE_AUDIT = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_priority_collection_capture_audit_20260614/"
    "summary.json"
)
DEFAULT_PRIORITY_CAPTURE_MISS = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_priority_capture_miss_20260614/summary.json"
)
DEFAULT_SELECTOR_CONTEXT_ACTION_PLAN = Path(
    "BPC_future/results/root_cause_selector_holdout_context_action_plan_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/root_cause_current_answer_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_current_answer_zh.md"
)
EXPECTED_MISSING = [
    "five_ten_full_no_regression_ab",
    "production_validated_selector",
    "twenty_walltime_speedup",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _cause_by_id(summary: dict[str, Any], cause_id: str) -> dict[str, Any]:
    for cause in summary.get("causes", []):
        if cause.get("cause_id") == cause_id:
            return cause
    return {}


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def build_summary(
    *,
    ledger_path: Path,
    why_path: Path,
    worker_negative_roi_blocker_path: Path,
    objective_audit_path: Path,
    production_gate_path: Path,
    counterexamples_path: Path,
    context_schema_gap_path: Path,
    snapshot_sample_coverage_path: Path,
    target002_probe_matrix_path: Path,
    target002_trajectory_branch_path: Path,
    component_capture_schema_path: Path,
    component_payload_rows_path: Path,
    component_payload_holdout_extension_path: Path,
    selector_holdout_gap_matrix_path: Path,
    selector_target_priority_matrix_path: Path,
    priority_collection_runbook_path: Path,
    priority_collection_capture_audit_path: Path,
    priority_capture_miss_path: Path,
    selector_context_action_plan_path: Path,
) -> dict[str, Any]:
    ledger = _read_json(ledger_path)
    why = _read_json(why_path)
    worker_negative_roi_blocker = _read_json(worker_negative_roi_blocker_path)
    objective = _read_json(objective_audit_path)
    production_gate = _read_json(production_gate_path)
    counterexamples = _read_json(counterexamples_path)
    context_schema_gap = _read_json(context_schema_gap_path)
    snapshot_coverage = _read_json(snapshot_sample_coverage_path)
    target002_probe_matrix = _read_json(target002_probe_matrix_path)
    target002_trajectory_branch = _read_json(target002_trajectory_branch_path)
    component_capture_schema = _read_json(component_capture_schema_path)
    component_payload_rows = _read_json(component_payload_rows_path)
    component_payload_holdout_extension = _read_json(
        component_payload_holdout_extension_path
    )
    selector_holdout_gap_matrix = _read_json(selector_holdout_gap_matrix_path)
    selector_target_priority_matrix = _read_json(selector_target_priority_matrix_path)
    priority_collection_runbook = _read_json(priority_collection_runbook_path)
    priority_collection_capture_audit = _read_json(
        priority_collection_capture_audit_path
    )
    priority_capture_miss = _read_json(priority_capture_miss_path)
    selector_context_action_plan = _read_json(selector_context_action_plan_path)

    small = _cause_by_id(why, "small_scale_fixed_overhead_sensitivity")
    twenty = _cause_by_id(why, "twenty_returned_batch_rmp_trajectory_coupling")
    selector = _cause_by_id(why, "addition_before_selector_not_production_validated")
    why_checks = why.get("checks", {})
    worker_phase7o = worker_negative_roi_blocker.get("phase7o_expanded", {})
    worker_phase8q = worker_negative_roi_blocker.get("phase8q_validation", {})
    missing_requirements = list(objective.get("missing_requirements", []))
    completion_status = ledger.get("completion_decision", {}).get("status")
    goal_complete = ledger.get("goal_status", {}).get("goal_complete")
    counterexample_labels = counterexamples.get("task20_label_counts", {})

    confirmed_causes = [
        {
            "cause_id": "small_scale_fixed_overhead_sensitivity",
            "answer": "5/10 规模主要卡在固定开销敏感；触发 worker/audit/probe 会吃掉收益。",
            "evidence": small.get("evidence", {}),
        },
        {
            "cause_id": "twenty_returned_batch_rmp_trajectory_coupling",
            "answer": (
                "20 规模不是没有 true-RC negative columns，而是 returned batch "
                "对当前 RMP active-basis / dual trajectory 的影响不稳定。"
            ),
            "evidence": twenty.get("evidence", {}),
        },
        {
            "cause_id": "addition_before_selector_not_production_validated",
            "answer": (
                "当前缺的是 production-validated addition-before selector；"
                "简单 true-RC / new-task-set / 单个 active-basis scalar 都不够。"
            ),
            "evidence": selector.get("evidence", {}),
        },
    ]

    checks = {
        "diagnostic_only": True,
        "ledger_core_status_consistent": completion_status == "keep_goal_active"
        and goal_complete is False,
        "why_report_passed": why.get("all_checks_pass") is True,
        "objective_audit_passed": objective.get("all_checks_pass") is True,
        "production_gate_passed": production_gate.get("all_checks_pass") is True,
        "counterexamples_passed": counterexamples.get("all_checks_pass") is True,
        "missing_requirements_match_expected": missing_requirements == EXPECTED_MISSING,
        "completion_keeps_goal_active": completion_status == "keep_goal_active"
        and goal_complete is False,
        "production_ab_blocked": production_gate.get(
            "production_candidate_ab_entry_status"
        )
        == "blocked",
        "worker_default_forbidden": production_gate.get(
            "must_not_enable_worker_default"
        )
        is True,
        "certificate_gate_forbidden": production_gate.get(
            "must_not_open_certificate_gate"
        )
        is True,
        "small_fixed_overhead_evidence_present": (
            _as_int(small.get("evidence", {}).get("triggered_worse_count")) == 220
            and _as_int(small.get("evidence", {}).get("triggered_better_count")) == 0
        ),
        "twenty_counterexample_evidence_present": (
            _as_int(counterexamples.get("task20_row_count")) == 12
            and _as_int(counterexamples.get("task20_new_task_set_row_count")) == 12
            and _as_int(counterexample_labels.get("improved")) == 10
            and _as_int(counterexample_labels.get("noop")) == 2
            and _as_int(
                counterexamples.get("weaker_improved_than_strongest_noop_count")
            )
            > 0
        ),
        "worker_negative_roi_blocker_passed": (
            worker_negative_roi_blocker.get("all_checks_pass") is True
            and worker_negative_roi_blocker.get("diagnostic_only") is True
            and worker_negative_roi_blocker.get("runs_bpc_or_pricing") is False
            and worker_negative_roi_blocker.get("status")
            == "worker_negative_columns_not_sufficient_for_roi"
            and _as_int(worker_phase7o.get("nonbaseline_rows")) == 96
            and _as_int(worker_phase7o.get("nonbaseline_worsened_rows")) == 96
            and _as_int(worker_phase7o.get("worker_added_journeys")) == 63
            and _as_int(worker_phase7o.get("worker_added_new_task_sets")) == 30
            and _as_int(worker_phase7o.get("worker_added_support_changing")) == 13
            and _as_int(worker_phase8q.get("worker_added_journeys")) == 10
            and _as_int(worker_phase8q.get("worker_added_rows")) == 3
            and _as_int(
                worker_negative_roi_blocker.get(
                    "phase8q_improved_without_worker_added_count"
                )
            )
            == 1
        ),
        "selector_not_production_validated": (
            why_checks.get("selector_blocker_passed") is True
            and why_checks.get("single_feature_selector_not_robust") is True
            and why_checks.get("multifeature_selector_not_robust") is True
        ),
        "context_schema_gap_passed": context_schema_gap.get("all_checks_pass") is True
        and context_schema_gap.get("status") == "selector_context_schema_gap_audited",
        "snapshot_sample_coverage_passed": snapshot_coverage.get("all_checks_pass")
        is True
        and snapshot_coverage.get("status")
        == "selector_snapshot_sample_coverage_audited",
        "target002_probe_matrix_passed": target002_probe_matrix.get("all_checks_pass")
        is True
        and _as_int(target002_probe_matrix.get("target_recovered_probe_count")) == 0,
        "target002_trajectory_branch_passed": target002_trajectory_branch.get(
            "all_checks_pass"
        )
        is True
        and _as_int(target002_trajectory_branch.get("same_active_event_count")) > 0
        and _as_int(
            target002_trajectory_branch.get("non_source_same_active_event_count")
        )
        > 0,
        "component_capture_schema_passed": (
            component_capture_schema.get("all_checks_pass") is True
            and component_capture_schema.get("status")
            == "component_capture_schema_contract_audited"
            and _as_int(component_capture_schema.get("capture_event_count")) == 78
            and _as_int(component_capture_schema.get("complete_active_basis_events"))
            == 78
            and _as_int(component_capture_schema.get("complete_pool_events")) == 78
            and _as_int(
                component_capture_schema.get("returned_batch_complete_events")
            )
            == 78
            and _as_int(component_capture_schema.get("forbidden_explicit_events"))
            > 0
            and component_capture_schema.get(
                "code_supports_explicit_forbidden_payload"
            )
            is True
            and component_capture_schema.get(
                "holdout_runbook_enables_explicit_forbidden_payload"
            )
            is True
        ),
        "component_payload_rows_passed": (
            component_payload_rows.get("all_checks_pass") is True
            and component_payload_rows.get("diagnostic_only") is True
            and component_payload_rows.get("runs_bpc_or_pricing") is False
            and component_payload_rows.get("runs_local_rmp_replay") is True
            and component_payload_rows.get("status")
            == "component_payload_addition_before_rows_audited"
            and _as_int(component_payload_rows.get("ready_case_count")) == 6
            and _as_int(component_payload_rows.get("candidate_row_count")) == 48
            and _as_int(component_payload_rows.get("explicit_forbidden_true_count"))
            == 48
        ),
        "component_payload_holdout_extension_passed": (
            component_payload_holdout_extension.get("all_checks_pass") is True
            and component_payload_holdout_extension.get("diagnostic_only") is True
            and component_payload_holdout_extension.get("runs_bpc_or_pricing")
            is False
            and component_payload_holdout_extension.get("status")
            == "component_payload_selector_holdout_extension_audited"
            and _as_int(
                component_payload_holdout_extension.get("base", {}).get("row_count")
            )
            == 280
            and _as_int(
                component_payload_holdout_extension.get("component_only", {}).get(
                    "row_count"
                )
            )
            == 48
            and _as_int(
                component_payload_holdout_extension.get("combined", {}).get(
                    "row_count"
                )
            )
            == 328
            and component_payload_holdout_extension.get("component_positive_only")
            is True
            and component_payload_holdout_extension.get(
                "combined_has_no_robust_selector"
            )
            is True
        ),
        "selector_holdout_gap_matrix_passed": (
            selector_holdout_gap_matrix.get("all_checks_pass") is True
            and selector_holdout_gap_matrix.get("diagnostic_only") is True
            and selector_holdout_gap_matrix.get("runs_bpc_or_pricing") is False
            and selector_holdout_gap_matrix.get("status")
            == "selector_holdout_gap_matrix_audited"
            and _as_int(selector_holdout_gap_matrix.get("total_candidate_row_count"))
            == 630
            and _as_int(
                selector_holdout_gap_matrix.get("complete_snapshot_total", {}).get(
                    "row_count"
                )
            )
            == 62
            and selector_holdout_gap_matrix.get(
                "complete_snapshot_context_label_mix", {}
            ).get("mixed_label_context_count")
            == 0
            and selector_holdout_gap_matrix.get(
                "complete_explicit_forbidden_total", {}
            ).get("label_counts")
            == {"improved": 48}
        ),
        "selector_target_priority_matrix_passed": (
            selector_target_priority_matrix.get("all_checks_pass") is True
            and selector_target_priority_matrix.get("diagnostic_only") is True
            and selector_target_priority_matrix.get("runs_bpc_or_pricing") is False
            and selector_target_priority_matrix.get("status")
            == "selector_holdout_target_priority_matrix_audited"
            and _as_int(selector_target_priority_matrix.get("priority_context_count"))
            >= 15
            and _as_int(
                selector_target_priority_matrix.get("category_counts", {}).get(
                    "mixed_missing_full_snapshot"
                )
            )
            >= 7
            and _as_int(
                selector_target_priority_matrix.get(
                    "uncovered_priority_context_count"
                )
            )
            >= 1
        ),
        "priority_collection_runbook_passed": (
            priority_collection_runbook.get("all_checks_pass") is True
            and priority_collection_runbook.get("diagnostic_only") is True
            and priority_collection_runbook.get("runs_bpc_or_pricing") is False
            and priority_collection_runbook.get("status")
            == "selector_holdout_priority_collection_runbook_ready"
            and _as_int(priority_collection_runbook.get("target_context_count")) == 6
            and _as_int(priority_collection_runbook.get("commandable_context_count"))
            == 3
            and _as_int(priority_collection_runbook.get("unsupported_context_count"))
            == 3
            and _as_int(priority_collection_runbook.get("command_count")) == 1
        ),
        "priority_collection_capture_audit_passed": (
            priority_collection_capture_audit.get("all_checks_pass") is True
            and priority_collection_capture_audit.get("diagnostic_only") is True
            and priority_collection_capture_audit.get("runs_bpc_or_pricing")
            is False
            and priority_collection_capture_audit.get("status")
            == "selector_holdout_collection_capture_audited"
            and _as_int(priority_collection_capture_audit.get("capture_event_count"))
            == 12
            and _as_int(
                priority_collection_capture_audit.get("expected_context_hash_count")
            )
            == 3
            and _as_int(
                priority_collection_capture_audit.get("expected_context_hit_count")
            )
            == 0
            and priority_collection_capture_audit.get("ready_for_selector_holdout")
            is False
            and _as_int(
                priority_collection_capture_audit.get("no_certificate_bad_count")
            )
            == 0
            and _as_int(priority_collection_capture_audit.get("active_basis_bad_count"))
            == 0
        ),
        "priority_capture_miss_passed": (
            priority_capture_miss.get("all_checks_pass") is True
            and priority_capture_miss.get("diagnostic_only") is True
            and priority_capture_miss.get("runs_bpc_or_pricing") is False
            and priority_capture_miss.get("status")
            == "selector_holdout_priority_capture_miss_diagnosed"
            and _as_int(priority_capture_miss.get("expected_context_count")) == 3
            and _as_int(priority_capture_miss.get("exact_hit_context_count")) == 0
            and _as_int(
                priority_capture_miss.get("source_active_hash_missing_context_count")
            )
            == 2
            and _as_int(
                priority_capture_miss.get("same_active_component_drift_context_count")
            )
            == 1
            and _as_int(priority_capture_miss.get("observed_event_count")) == 12
        ),
        "selector_context_action_plan_passed": (
            selector_context_action_plan.get("all_checks_pass") is True
            and selector_context_action_plan.get("diagnostic_only") is True
            and selector_context_action_plan.get("runs_bpc_or_pricing") is False
            and selector_context_action_plan.get("status")
            == "selector_holdout_context_action_plan_ready"
            and _as_int(selector_context_action_plan.get("row_count")) == 12
            and _as_int(
                selector_context_action_plan.get("complete_snapshot_action_count")
            )
            == 7
            and _as_int(selector_context_action_plan.get("unresolved_action_count"))
            == 5
            and _as_int(
                selector_context_action_plan.get("unresolved_with_command_count")
            )
            == 4
            and _as_int(
                selector_context_action_plan.get("unresolved_without_command_count")
            )
            == 1
            and selector_context_action_plan.get(
                "unresolved_execution_category_counts", {}
            ).get("trajectory_variant_capture_required")
            == 2
            and selector_context_action_plan.get(
                "unresolved_execution_category_counts", {}
            ).get("full_component_match_required")
            == 1
            and selector_context_action_plan.get(
                "unresolved_execution_category_counts", {}
            ).get("run_or_reaudit_existing_manifest_command")
            == 1
            and selector_context_action_plan.get(
                "unresolved_execution_category_counts", {}
            ).get("source_mapping_recovery_required")
            == 1
        ),
    }
    return {
        "schema_version": "root_cause_current_answer_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "root_cause_supported_but_optimization_direction_unproven",
        "current_answer": (
            "5/10 失败的直接原因是固定开销敏感；20 失败的根因不是找不到负列，"
            "而是 returned batch 对当前 RMP active-basis / dual trajectory 的影响强上下文耦合；"
            "当前还没有 production-validated addition-before selector。"
        ),
        "current_answer_detail": (
            "前面大量工作证明了 Pulse / worker / capture 路径可以安全地产生或记录 "
            "true-RC negative journeys，并且不应误造 official certificate；但这些 "
            "true-RC negative journeys 并不自动等价于求解收益。最新 schema gap "
            "审计显示，当前 280 行 replay selector 数据能完整 join 到 122 个 manifest "
            "case，但 full active-basis snapshot 没有真正填充，pool/returned-batch "
            "composition 只能从 manifest 派生且未持久化进 candidate rows，forbidden "
            "pressure 的旧 hash-only 缺口已被 targeted component payload 部分补上。"
            "全局 candidate rows 里确实另有 62 行 complete snapshot，其中 14 行来自 "
            "active-basis snapshot smoke，48 行来自 targeted component-payload "
            "addition-before rows；但主 280 行 replay selector 数据里 complete snapshot "
            "仍为 0，所以当前不是已有样本未利用，而是还没有足够的、已合入 selector "
            "holdout 的 no-certificate-effect full-snapshot/component-payload 数据。"
            "唯一未命中的 priority context 是 target002 pt0.3；probe matrix 显示当前代码下"
            "复现 probe 数为 0，而 trajectory branch 审计显示同一 active hash 附近仍会发生"
            " pool / forbidden signature / RMP objective / returned-batch composition 分叉。"
            "因此这不是简单重跑 runbook 就能消除的缺口，而是当前 production selector 必须"
            "显式建模的上下文耦合。最新 component capture schema contract 进一步说明："
            "现有 config-matched capture 的 78 个事件已经完整记录 active-basis、pool、"
            "returned-batch 和 forbidden-signature payload，其中 12 个事件包含显式 "
            "forbidden signature list。最新 component-payload 审计已经把其中 target002 "
            "ready payload 转成 6 个 ready local RMP replay case、48 行 addition-before "
            "candidate rows，且 active-basis、pool、returned-batch、显式 forbidden-signature "
            "字段完整。这消除了“rows 能不能构造”的阻塞，但它仍只是单 target context "
            "calibration evidence；还没有证明 production selector、5/10 不退化或 20 wall-time "
            "speedup。最新 component-payload selector holdout extension "
            "已经做了这一步的最小合并检查：base 280 行 + component 48 行 = 328 行，"
            "component-only 是单类正样本，合并后 robust all-holdout feature/model 仍为 0。"
            "所以现在的问题已经不是字段完全不能构造，而是这些字段尚未在足够宽的"
            "负例/上下文分布上产生可泛化选择规则。最新 selector holdout gap "
            "matrix 把缺口进一步钉死：全局 630 条 candidate rows 里只有 62 条"
            " complete full-snapshot rows，其中 label mix 是 improved:59 / noop:3，"
            "mixed-label context 数为 0；48 条 complete explicit-forbidden rows 全是"
            " improved。因此下一步必须补 negative/noop 与 mixed full-snapshot contexts，"
            "不是继续增加单类 positive payload rows。最新 selector holdout target "
            "priority matrix 已把这个缺口落到具体 context：当前有 15 个 priority "
            "contexts，其中 7 个 mixed contexts 缺 complete full-snapshot，12 个 noop "
            "contexts 缺 complete full-snapshot，且仍有 6 个 priority contexts 不在现有"
            " collection manifest 覆盖内。priority collection runbook 进一步显示，"
            "这 6 个未覆盖 context 中有 3 个 Apollo target002 contexts 可用现有 "
            "profile/config 生成补采命令，另外 3 个来自 baseline/smoke source，"
            "当前没有可解析 source profile，必须显式当作 unsupported，而不能当作"
            "已补采。实际执行这条 priority collection command 后，采到 12 个"
            " no-certificate-effect 且 active-basis 完整的 capture events，但 3 个"
            " expected target contexts 命中数为 0，ready_for_selector_holdout=false。"
            "这把问题进一步收紧为：同一实例/配置/profile 重跑能安全采集新上下文，"
            "但不能保证回到 selector 最缺的 mixed/noop target contexts；生产规则必须"
            "建模完整 context/trajectory，而不是假设 source profile rerun 能复原目标点。"
            "priority capture miss 诊断进一步说明，3 个 expected contexts 中有 2 个"
            "没有到达 source active hash，另 1 个虽到达同 active hash，但 pool signature、"
            "forbidden signature、returned task-set batch 和 pricing outcome 均发生漂移。"
            "最新 selector holdout context action plan 把剩余缺口拆成 12 个高优先"
            "context：7 个已经能作为 complete snapshot calibration seed，5 个仍未闭合。"
            "这 5 个里有 2 个必须捕获 trajectory variant 才能回到 source active-basis，"
            "1 个必须完整匹配 pool/forbidden/returned-batch/RMP/pricing 组件，1 个要重跑或"
            "重审既有 manifest command，1 个要先恢复 source profile / instance mapping。"
            "因此当前失败不是因为某个单一 Pulse 开关没打开，而是 production selector 所需的"
            "上下文分布还没有被稳定采到；盲目重跑同 profile 或只看 active hash 都不能闭环。"
        ),
        "component_capture_schema": {
            "capture_event_count": component_capture_schema.get("capture_event_count"),
            "complete_active_basis_events": component_capture_schema.get(
                "complete_active_basis_events"
            ),
            "complete_pool_events": component_capture_schema.get("complete_pool_events"),
            "returned_batch_complete_events": component_capture_schema.get(
                "returned_batch_complete_events"
            ),
            "returned_batch_nonempty_events": component_capture_schema.get(
                "returned_batch_nonempty_events"
            ),
            "forbidden_explicit_events": component_capture_schema.get(
                "forbidden_explicit_events"
            ),
            "code_supports_explicit_forbidden_payload": component_capture_schema.get(
                "code_supports_explicit_forbidden_payload"
            ),
            "holdout_runbook_enables_explicit_forbidden_payload": (
                component_capture_schema.get(
                    "holdout_runbook_enables_explicit_forbidden_payload"
                )
            ),
        },
        "component_payload_addition_before_rows": {
            "raw_capture_case_count": component_payload_rows.get(
                "raw_capture_case_count"
            ),
            "ready_case_count": component_payload_rows.get("ready_case_count"),
            "candidate_row_count": component_payload_rows.get("candidate_row_count"),
            "high_impact_candidate_count": component_payload_rows.get(
                "high_impact_candidate_count"
            ),
            "noop_candidate_count": component_payload_rows.get("noop_candidate_count"),
            "explicit_forbidden_true_count": component_payload_rows.get(
                "explicit_forbidden_true_count"
            ),
            "runs_local_rmp_replay": component_payload_rows.get(
                "runs_local_rmp_replay"
            ),
        },
        "component_payload_selector_holdout_extension": {
            "base_row_count": component_payload_holdout_extension.get(
                "base", {}
            ).get("row_count"),
            "component_row_count": component_payload_holdout_extension.get(
                "component_only", {}
            ).get("row_count"),
            "combined_row_count": component_payload_holdout_extension.get(
                "combined", {}
            ).get("row_count"),
            "component_positive_only": component_payload_holdout_extension.get(
                "component_positive_only"
            ),
            "combined_robust_feature_count": component_payload_holdout_extension.get(
                "combined", {}
            ).get("robust_all_holdout_derived_feature_count"),
            "combined_robust_model_count": component_payload_holdout_extension.get(
                "combined", {}
            ).get("robust_all_holdout_model_count"),
            "combined_best_context_model_context_folds": (
                component_payload_holdout_extension.get("combined", {}).get(
                    "best_context_model_context_folds"
                )
            ),
        },
        "selector_holdout_gap_matrix": {
            "total_candidate_row_count": selector_holdout_gap_matrix.get(
                "total_candidate_row_count"
            ),
            "complete_snapshot_row_count": selector_holdout_gap_matrix.get(
                "complete_snapshot_total", {}
            ).get("row_count"),
            "complete_snapshot_label_counts": selector_holdout_gap_matrix.get(
                "complete_snapshot_total", {}
            ).get("label_counts"),
            "complete_snapshot_mixed_context_count": selector_holdout_gap_matrix.get(
                "complete_snapshot_context_label_mix", {}
            ).get("mixed_label_context_count"),
            "complete_explicit_forbidden_row_count": selector_holdout_gap_matrix.get(
                "complete_explicit_forbidden_total", {}
            ).get("row_count"),
            "complete_explicit_forbidden_label_counts": selector_holdout_gap_matrix.get(
                "complete_explicit_forbidden_total", {}
            ).get("label_counts"),
            "recommended_next_stage": selector_holdout_gap_matrix.get(
                "recommended_next_stage"
            ),
        },
        "selector_holdout_target_priority_matrix": {
            "priority_context_count": selector_target_priority_matrix.get(
                "priority_context_count"
            ),
            "mixed_missing_full_snapshot_context_count": (
                selector_target_priority_matrix.get("category_counts", {}).get(
                    "mixed_missing_full_snapshot"
                )
            ),
            "noop_missing_full_snapshot_context_count": (
                selector_target_priority_matrix.get("category_counts", {}).get(
                    "noop_missing_full_snapshot"
                )
            ),
            "noop_missing_explicit_forbidden_context_count": (
                selector_target_priority_matrix.get("category_counts", {}).get(
                    "noop_missing_explicit_forbidden"
                )
            ),
            "manifest_priority_context_overlap_count": (
                selector_target_priority_matrix.get(
                    "manifest_priority_context_overlap_count"
                )
            ),
            "uncovered_priority_context_count": selector_target_priority_matrix.get(
                "uncovered_priority_context_count"
            ),
            "uncovered_priority_contexts": selector_target_priority_matrix.get(
                "uncovered_priority_contexts"
            ),
            "recommended_next_stage": selector_target_priority_matrix.get(
                "recommended_next_stage"
            ),
        },
        "selector_holdout_priority_collection_runbook": {
            "target_context_count": priority_collection_runbook.get(
                "target_context_count"
            ),
            "commandable_context_count": priority_collection_runbook.get(
                "commandable_context_count"
            ),
            "unsupported_context_count": priority_collection_runbook.get(
                "unsupported_context_count"
            ),
            "command_count": priority_collection_runbook.get("command_count"),
            "commandable_contexts": priority_collection_runbook.get(
                "commandable_contexts"
            ),
            "unsupported_contexts": priority_collection_runbook.get(
                "unsupported_contexts"
            ),
            "status": priority_collection_runbook.get("status"),
        },
        "selector_holdout_priority_collection_capture_audit": {
            "capture_event_count": priority_collection_capture_audit.get(
                "capture_event_count"
            ),
            "expected_context_hash_count": priority_collection_capture_audit.get(
                "expected_context_hash_count"
            ),
            "expected_context_hit_count": priority_collection_capture_audit.get(
                "expected_context_hit_count"
            ),
            "missing_expected_context_count": priority_collection_capture_audit.get(
                "missing_expected_context_count"
            ),
            "expected_context_complete_hit_count": (
                priority_collection_capture_audit.get(
                    "expected_context_complete_hit_count"
                )
            ),
            "ready_for_selector_holdout": priority_collection_capture_audit.get(
                "ready_for_selector_holdout"
            ),
            "no_certificate_bad_count": priority_collection_capture_audit.get(
                "no_certificate_bad_count"
            ),
            "active_basis_bad_count": priority_collection_capture_audit.get(
                "active_basis_bad_count"
            ),
            "status": priority_collection_capture_audit.get("status"),
        },
        "selector_holdout_priority_capture_miss": {
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
            "observed_event_count": priority_capture_miss.get(
                "observed_event_count"
            ),
            "observed_unique_context_count": priority_capture_miss.get(
                "observed_unique_context_count"
            ),
            "status": priority_capture_miss.get("status"),
        },
        "selector_holdout_context_action_plan": {
            "row_count": selector_context_action_plan.get("row_count"),
            "complete_snapshot_action_count": selector_context_action_plan.get(
                "complete_snapshot_action_count"
            ),
            "unresolved_action_count": selector_context_action_plan.get(
                "unresolved_action_count"
            ),
            "unresolved_with_command_count": selector_context_action_plan.get(
                "unresolved_with_command_count"
            ),
            "unresolved_without_command_count": selector_context_action_plan.get(
                "unresolved_without_command_count"
            ),
            "unresolved_execution_category_counts": (
                selector_context_action_plan.get(
                    "unresolved_execution_category_counts"
                )
            ),
            "status": selector_context_action_plan.get("status"),
        },
        "worker_negative_column_roi_blocker": {
            "status": worker_negative_roi_blocker.get("status"),
            "interpretation": worker_negative_roi_blocker.get("interpretation"),
            "phase7o": {
                "row_count": worker_phase7o.get("row_count"),
                "nonbaseline_rows": worker_phase7o.get("nonbaseline_rows"),
                "nonbaseline_worsened_rows": worker_phase7o.get(
                    "nonbaseline_worsened_rows"
                ),
                "worker_added_rows": worker_phase7o.get("worker_added_rows"),
                "worker_added_journeys": worker_phase7o.get(
                    "worker_added_journeys"
                ),
                "worker_added_new_task_sets": worker_phase7o.get(
                    "worker_added_new_task_sets"
                ),
                "worker_added_support_changing": worker_phase7o.get(
                    "worker_added_support_changing"
                ),
                "critical_disagreement_rows": worker_phase7o.get(
                    "critical_disagreement_rows"
                ),
            },
            "phase8q": {
                "row_count": worker_phase8q.get("row_count"),
                "nonbaseline_rows": worker_phase8q.get("nonbaseline_rows"),
                "nonbaseline_improved_rows": worker_phase8q.get(
                    "nonbaseline_improved_rows"
                ),
                "worker_added_rows": worker_phase8q.get("worker_added_rows"),
                "worker_added_journeys": worker_phase8q.get(
                    "worker_added_journeys"
                ),
                "worker_added_new_task_sets": worker_phase8q.get(
                    "worker_added_new_task_sets"
                ),
                "worker_added_support_changing": worker_phase8q.get(
                    "worker_added_support_changing"
                ),
                "critical_disagreement_rows": worker_phase8q.get(
                    "critical_disagreement_rows"
                ),
                "improved_without_worker_added_count": (
                    worker_negative_roi_blocker.get(
                        "phase8q_improved_without_worker_added_count"
                    )
                ),
            },
        },
        "confirmed_causes": confirmed_causes,
        "ruled_out_hypotheses": why.get("ruled_out_hypotheses", []),
        "missing_requirements": missing_requirements,
        "next_required_evidence": why.get("next_required_evidence", []),
        "completion_decision": completion_status,
        "goal_complete": goal_complete,
        "production_ab_entry_gate": production_gate.get(
            "production_candidate_ab_entry_status"
        ),
        "sources": {
            "ledger": str(ledger_path),
            "why": str(why_path),
            "worker_negative_roi_blocker": str(worker_negative_roi_blocker_path),
            "objective_audit": str(objective_audit_path),
            "production_gate": str(production_gate_path),
            "counterexamples": str(counterexamples_path),
            "context_schema_gap": str(context_schema_gap_path),
            "snapshot_sample_coverage": str(snapshot_sample_coverage_path),
            "target002_probe_matrix": str(target002_probe_matrix_path),
            "target002_trajectory_branch": str(target002_trajectory_branch_path),
            "component_capture_schema": str(component_capture_schema_path),
            "component_payload_rows": str(component_payload_rows_path),
            "component_payload_holdout_extension": str(
                component_payload_holdout_extension_path
            ),
            "selector_holdout_gap_matrix": str(selector_holdout_gap_matrix_path),
            "selector_target_priority_matrix": str(
                selector_target_priority_matrix_path
            ),
            "priority_collection_runbook": str(priority_collection_runbook_path),
            "priority_collection_capture_audit": str(
                priority_collection_capture_audit_path
            ),
            "priority_capture_miss": str(priority_capture_miss_path),
            "selector_context_action_plan": str(selector_context_action_plan_path),
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# BPC_future 根因当前答案",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告是当前根因工作的短入口，只回答当前能确定什么、不能确定什么、",
        "以及为什么目标仍不能标记完成。",
        "",
        "它只读已有 evidence summaries，不运行 BPC / pricing / RMP / Pulse，",
        "也不改变 worker、certificate 或 solver 默认行为。",
        "",
        "## 当前答案",
        "",
        summary["current_answer"],
        "",
        summary["current_answer_detail"],
        "",
        "## 最新 worker 负列 ROI 阻塞结论",
        "",
        "```json",
        json.dumps(
            summary["worker_negative_column_roi_blocker"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        (
            "解释：worker 已经能加入 true-RC negative journeys，包括 new task-set "
            "和 support-changing 列；但 Phase 7O expanded 的 non-baseline rows "
            "全部 worsened，Phase 8Q 中 worker-added rows 也没有成为 improved rows。"
            "这直接排除了“继续找更多或更负负列即可优化”的充分性。"
        ),
        "",
        "## 最新 component capture 结论",
        "",
        "```json",
        json.dumps(
            summary["component_capture_schema"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        (
            "解释：active-basis、pool、returned-batch payload 已经在当前 "
            "config-matched capture 中完整可观测；目标补采已经验证 explicit forbidden "
            "signature list 可落盘。"
        ),
        "",
        "## 最新 component payload rows 结论",
        "",
        "```json",
        json.dumps(
            summary["component_payload_addition_before_rows"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        (
            "解释：component payload 已经可以转成 addition-before candidate rows，"
            "且显式 forbidden-signature 字段完整。这只是校准数据构造证据，"
            "不是 production selector、BPC speedup 或 certificate effect。"
        ),
        "",
        "## 最新 component payload selector holdout extension 结论",
        "",
        "```json",
        json.dumps(
            summary["component_payload_selector_holdout_extension"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        (
            "解释：把 48 行 component payload rows 合入现有 280 行 selector rows 后，"
            "合并集仍没有通过 context / instance / dataset all-holdout 的特征或模型。"
            "这说明 payload 字段补齐降低了 schema gap，但还没有形成 production selector。"
        ),
        "",
        "## 最新 selector holdout gap matrix 结论",
        "",
        "```json",
        json.dumps(
            summary["selector_holdout_gap_matrix"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        (
            "解释：当前 full-snapshot 和 explicit-forbidden payload 已经能采到，"
            "但完整样本几乎全是正例，且 mixed-label context 为 0。下一步需要补"
            " negative/noop 与 mixed full-snapshot contexts，而不是把正例 payload "
            "当成 production selector。"
        ),
        "",
        "## 最新 selector holdout target priority matrix 结论",
        "",
        "```json",
        json.dumps(
            summary["selector_holdout_target_priority_matrix"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        (
            "解释：缺口现在已经落到具体 context。现有 manifest 覆盖了一部分高优先"
            "目标，但仍有 priority contexts 未覆盖；这些目标应该优先补采 complete "
            "full-snapshot 与 explicit-forbidden payload，用来验证 production selector "
            "是否能同时拒绝 noop 和保留 improved。"
        ),
        "",
        "## 最新 selector holdout priority collection runbook 结论",
        "",
        "```json",
        json.dumps(
            summary["selector_holdout_priority_collection_runbook"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        (
            "解释：未覆盖 priority contexts 里只有一部分能直接转成 config-matched "
            "采集命令；unsupported contexts 必须另行补 profile/source 解析，不能把 "
            "runbook ready 当作 selector holdout 已完成。"
        ),
        "",
        "## 最新 selector holdout priority collection capture audit 结论",
        "",
        "```json",
        json.dumps(
            summary["selector_holdout_priority_collection_capture_audit"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        (
            "解释：priority collection 实际运行是安全的，采到的 capture event "
            "没有 certificate effect 且 active-basis 完整；但 3 个 expected "
            "target context 一个都没命中，所以它只能证明补采链路安全，不能证明"
            " selector holdout 数据已经补齐。"
        ),
        "",
        "## 最新 selector holdout priority capture miss 诊断",
        "",
        "```json",
        json.dumps(
            summary["selector_holdout_priority_capture_miss"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        (
            "解释：补采没有命中目标 context 的原因不是 capture 不安全，而是轨迹"
            "本身发生分叉。两个目标 context 没到达 source active hash；一个目标"
            "context 到达同 active hash 但 pool / forbidden / returned-batch 组成漂移。"
        ),
        "",
        "## 最新 selector holdout context action plan 结论",
        "",
        "```json",
        json.dumps(
            summary["selector_holdout_context_action_plan"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        (
            "解释：12 个高优先 context 中只有 7 个可直接用作 complete snapshot "
            "calibration seed；剩余 5 个仍需要不同恢复动作。两个要捕获 trajectory "
            "variant 才能到达 source active-basis，一个要完整匹配 pool / forbidden / "
            "returned-batch / RMP / pricing 组件，一个要重跑或重审既有 manifest command，"
            "一个要先恢复 source profile / instance mapping。这说明 selector 数据缺口"
            "不是继续盲跑同 profile 可以闭合的简单采样问题。"
        ),
        "",
        "## 已确定的根因",
        "",
    ]
    for cause in summary["confirmed_causes"]:
        lines.extend(
            [
                f"### {cause['cause_id']}",
                "",
                cause["answer"],
                "",
                "```json",
                json.dumps(cause["evidence"], ensure_ascii=False, indent=2, sort_keys=True),
                "```",
                "",
            ]
        )

    lines.extend(["## 已排除的解释", ""])
    for item in summary["ruled_out_hypotheses"]:
        lines.extend(
            [
                f"- `{item.get('hypothesis')}`：`{item.get('status')}`。",
                f"  {item.get('why')}",
            ]
        )

    lines.extend(
        [
            "",
            "## 为什么仍不能标记完成",
            "",
            "```text",
            f"completion_decision = {summary['completion_decision']}",
            f"goal_complete = {str(summary['goal_complete']).lower()}",
            "missing_requirements = " + ",".join(summary["missing_requirements"]),
            f"production_ab_entry_gate = {summary['production_ab_entry_gate']}",
            "```",
            "",
            "缺失项含义：",
            "",
            "- 还没有 full 5/10 production-candidate no-regression A/B；",
            "- 还没有用 component-payload addition-before rows 通过 context / instance / dataset holdout 的 production selector；",
            "- 还没有 selected 20-task hard-repeat wall-time/gap/status/tail speedup 证据。",
            "",
            "## 下一步证据门槛",
            "",
        ]
    )
    for item in summary["next_required_evidence"]:
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
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--why", type=Path, default=DEFAULT_WHY)
    parser.add_argument(
        "--worker-negative-roi-blocker",
        type=Path,
        default=DEFAULT_WORKER_NEGATIVE_ROI_BLOCKER,
    )
    parser.add_argument("--objective-audit", type=Path, default=DEFAULT_OBJECTIVE_AUDIT)
    parser.add_argument("--production-gate", type=Path, default=DEFAULT_PRODUCTION_GATE)
    parser.add_argument("--counterexamples", type=Path, default=DEFAULT_COUNTEREXAMPLES)
    parser.add_argument(
        "--context-schema-gap", type=Path, default=DEFAULT_CONTEXT_SCHEMA_GAP
    )
    parser.add_argument(
        "--snapshot-sample-coverage",
        type=Path,
        default=DEFAULT_SNAPSHOT_SAMPLE_COVERAGE,
    )
    parser.add_argument(
        "--target002-probe-matrix",
        type=Path,
        default=DEFAULT_TARGET002_PROBE_MATRIX,
    )
    parser.add_argument(
        "--target002-trajectory-branch",
        type=Path,
        default=DEFAULT_TARGET002_TRAJECTORY_BRANCH,
    )
    parser.add_argument(
        "--component-capture-schema",
        type=Path,
        default=DEFAULT_COMPONENT_CAPTURE_SCHEMA,
    )
    parser.add_argument(
        "--component-payload-rows",
        type=Path,
        default=DEFAULT_COMPONENT_PAYLOAD_ROWS,
    )
    parser.add_argument(
        "--component-payload-holdout-extension",
        type=Path,
        default=DEFAULT_COMPONENT_PAYLOAD_HOLDOUT_EXTENSION,
    )
    parser.add_argument(
        "--selector-holdout-gap-matrix",
        type=Path,
        default=DEFAULT_SELECTOR_HOLDOUT_GAP_MATRIX,
    )
    parser.add_argument(
        "--selector-target-priority-matrix",
        type=Path,
        default=DEFAULT_SELECTOR_TARGET_PRIORITY_MATRIX,
    )
    parser.add_argument(
        "--priority-collection-runbook",
        type=Path,
        default=DEFAULT_PRIORITY_COLLECTION_RUNBOOK,
    )
    parser.add_argument(
        "--priority-collection-capture-audit",
        type=Path,
        default=DEFAULT_PRIORITY_COLLECTION_CAPTURE_AUDIT,
    )
    parser.add_argument(
        "--priority-capture-miss",
        type=Path,
        default=DEFAULT_PRIORITY_CAPTURE_MISS,
    )
    parser.add_argument(
        "--selector-context-action-plan",
        type=Path,
        default=DEFAULT_SELECTOR_CONTEXT_ACTION_PLAN,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = build_summary(
        ledger_path=args.ledger,
        why_path=args.why,
        worker_negative_roi_blocker_path=args.worker_negative_roi_blocker,
        objective_audit_path=args.objective_audit,
        production_gate_path=args.production_gate,
        counterexamples_path=args.counterexamples,
        context_schema_gap_path=args.context_schema_gap,
        snapshot_sample_coverage_path=args.snapshot_sample_coverage,
        target002_probe_matrix_path=args.target002_probe_matrix,
        target002_trajectory_branch_path=args.target002_trajectory_branch,
        component_capture_schema_path=args.component_capture_schema,
        component_payload_rows_path=args.component_payload_rows,
        component_payload_holdout_extension_path=(
            args.component_payload_holdout_extension
        ),
        selector_holdout_gap_matrix_path=args.selector_holdout_gap_matrix,
        selector_target_priority_matrix_path=args.selector_target_priority_matrix,
        priority_collection_runbook_path=args.priority_collection_runbook,
        priority_collection_capture_audit_path=args.priority_collection_capture_audit,
        priority_capture_miss_path=args.priority_capture_miss,
        selector_context_action_plan_path=args.selector_context_action_plan,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, args.report)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
