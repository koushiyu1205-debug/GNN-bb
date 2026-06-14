"""Build a strict readiness matrix for the next optimization direction.

This diagnostic-only script does not run BPC, pricing, RMP, Pulse, workers,
certificates, or benchmarks.  It reads existing root-cause summaries and writes
a compact matrix that separates supported diagnosis from an approved production
optimization direction.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_CURRENT_ANSWER = Path(
    "BPC_future/results/root_cause_current_answer_20260614/summary.json"
)
DEFAULT_OBJECTIVE_AUDIT = Path(
    "BPC_future/results/root_cause_objective_completion_audit_20260614/"
    "summary.json"
)
DEFAULT_PRODUCTION_AB_GATE = Path(
    "BPC_future/results/root_cause_production_ab_entry_gate_catalog_20260614/"
    "summary.json"
)
DEFAULT_REGISTRY = Path(
    "BPC_future/results/root_cause_optimization_direction_candidate_registry_20260614/"
    "summary.json"
)
DEFAULT_NEXT_ACTION = Path(
    "BPC_future/results/root_cause_next_action_plan_20260614/summary.json"
)
DEFAULT_SELECTOR_BLOCKER = Path(
    "BPC_future/results/root_cause_production_selector_blocker_catalog_20260614/"
    "summary.json"
)
DEFAULT_COMPONENT_EXTENSION = Path(
    "BPC_future/results/root_cause_component_payload_selector_holdout_extension_20260614/"
    "summary.json"
)
DEFAULT_HOLDOUT_GAP_MATRIX = Path(
    "BPC_future/results/root_cause_selector_holdout_gap_matrix_20260614/"
    "summary.json"
)
DEFAULT_TARGET_PRIORITY_MATRIX = Path(
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
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_direction_readiness_matrix_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_direction_readiness_matrix_zh.md"
)


EXPECTED_MISSING_REQUIREMENTS = [
    "five_ten_full_no_regression_ab",
    "production_validated_selector",
    "twenty_walltime_speedup",
]
EXPECTED_ENTRY_BLOCKERS = [
    "selector_not_validated",
    "five_ten_full_no_regression_missing",
    "twenty_speedup_missing",
]
EXPECTED_HOLDOUTS = ["context", "instance", "dataset"]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _gate(
    *,
    gate_id: str,
    status: str,
    evidence: dict[str, Any],
    conclusion: str,
    required_before_completion: bool = True,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "status": status,
        "required_before_completion": required_before_completion,
        "evidence": evidence,
        "conclusion": conclusion,
    }


def build_matrix(
    *,
    current_answer_path: Path,
    objective_audit_path: Path,
    production_ab_gate_path: Path,
    registry_path: Path,
    next_action_path: Path,
    selector_blocker_path: Path,
    component_extension_path: Path,
    holdout_gap_matrix_path: Path,
    target_priority_matrix_path: Path,
    priority_collection_runbook_path: Path,
    priority_collection_capture_audit_path: Path,
    priority_capture_miss_path: Path,
) -> dict[str, Any]:
    current_answer = _read_json(current_answer_path)
    objective_audit = _read_json(objective_audit_path)
    production_ab_gate = _read_json(production_ab_gate_path)
    registry = _read_json(registry_path)
    next_action = _read_json(next_action_path)
    selector_blocker = _read_json(selector_blocker_path)
    component_extension = _read_json(component_extension_path)
    holdout_gap_matrix = _read_json(holdout_gap_matrix_path)
    target_priority_matrix = _read_json(target_priority_matrix_path)
    priority_collection_runbook = _read_json(priority_collection_runbook_path)
    priority_collection_capture_audit = _read_json(
        priority_collection_capture_audit_path
    )
    priority_capture_miss = _read_json(priority_capture_miss_path)

    current_extension = current_answer.get(
        "component_payload_selector_holdout_extension", {}
    )
    missing_requirements = list(objective_audit.get("missing_requirements", []))
    entry_blockers = list(production_ab_gate.get("entry_gate_blockers", []))
    selector_blocker_ids = [
        str(item.get("blocker_id", ""))
        for item in selector_blocker.get("blockers", [])
        if item.get("blocker_id")
    ]
    component_combined = component_extension.get("combined", {})

    gates = [
        _gate(
            gate_id="root_cause_explanation",
            status="passed",
            required_before_completion=True,
            evidence={
                "current_answer_status": current_answer.get("status"),
                "current_answer_all_checks_pass": current_answer.get(
                    "all_checks_pass"
                ),
                "objective_root_cause_requirement": objective_audit.get(
                    "audit_item_statuses", {}
                ).get("root_cause_explanation_has_evidence"),
            },
            conclusion=(
                "根因解释已有证据支持：问题不是 Pulse 单点接线，而是固定开销、"
                "20-task true-RC 负列 ROI 和 addition-before selector 泛化共同作用。"
            ),
        ),
        _gate(
            gate_id="production_selector",
            status="failed",
            evidence={
                "selector_status": selector_blocker.get("status"),
                "selector_blocker_ids": selector_blocker_ids,
                "component_extension_base_rows": current_extension.get(
                    "base_row_count"
                ),
                "component_extension_component_rows": current_extension.get(
                    "component_row_count"
                ),
                "component_extension_combined_rows": current_extension.get(
                    "combined_row_count"
                ),
                "component_extension_component_positive_only": (
                    current_extension.get("component_positive_only")
                ),
                "component_extension_combined_robust_feature_count": (
                    current_extension.get("combined_robust_feature_count")
                ),
                "component_extension_combined_robust_model_count": (
                    current_extension.get("combined_robust_model_count")
                ),
                "component_extension_combined_context_model_folds": (
                    current_extension.get("combined_best_context_model_context_folds")
                ),
            },
            conclusion=(
                "48 条 component payload 行能降低 schema gap，但它们全是正例；"
                "合并到 328 行后 robust all-holdout feature/model 仍为 0，"
                "不能形成 production selector。"
            ),
        ),
        _gate(
            gate_id="five_ten_full_no_regression_ab",
            status="missing",
            evidence={
                "entry_blocker_present": "five_ten_full_no_regression_missing"
                in entry_blockers,
                "objective_missing_requirement_present": (
                    "five_ten_full_no_regression_ab" in missing_requirements
                ),
            },
            conclusion=(
                "已有证据只能说明 no-op guard 可以保持小实例不被触发；"
                "还没有 full 5/10 production A/B 证明触发策略不退化。"
            ),
        ),
        _gate(
            gate_id="selected_twenty_walltime_speedup",
            status="missing",
            evidence={
                "entry_blocker_present": "twenty_speedup_missing" in entry_blockers,
                "objective_missing_requirement_present": (
                    "twenty_walltime_speedup" in missing_requirements
                ),
                "production_direction_proven": registry.get(
                    "production_direction_proven"
                ),
            },
            conclusion=(
                "20-task 上存在 true-RC negative columns 和局部 RMP impact，"
                "但尚未证明 selected hard 20 的 wall-time/gap/status/tail 改善。"
            ),
        ),
        _gate(
            gate_id="certificate_and_worker_safety_boundary",
            status="passed_as_boundary_not_as_speedup",
            required_before_completion=False,
            evidence={
                "must_not_enable_worker_default": production_ab_gate.get(
                    "must_not_enable_worker_default"
                ),
                "must_not_open_certificate_gate": production_ab_gate.get(
                    "must_not_open_certificate_gate"
                ),
                "forbidden_shortcuts": production_ab_gate.get(
                    "forbidden_shortcuts", []
                ),
            },
            conclusion=(
                "exactness 边界是清楚的：当前不能默认启用 worker，不能打开 "
                "official certificate gate；这只是安全边界，不是优化成功证据。"
            ),
        ),
        _gate(
            gate_id="next_allowed_stage",
            status="calibration_only",
            required_before_completion=False,
            evidence={
                "registry_allowed_stage": registry.get(
                    "current_allowed_next_stage"
                ),
                "next_action_status": next_action.get("status"),
                "next_action_required_holdouts": next_action.get(
                    "required_selector_holdouts"
                ),
                "holdout_gap_status": holdout_gap_matrix.get("status"),
                "holdout_gap_recommended_next_stage": holdout_gap_matrix.get(
                    "recommended_next_stage"
                ),
                "complete_snapshot_label_counts": holdout_gap_matrix.get(
                    "complete_snapshot_total", {}
                ).get("label_counts"),
                "complete_snapshot_mixed_context_count": holdout_gap_matrix.get(
                    "complete_snapshot_context_label_mix", {}
                ).get("mixed_label_context_count"),
                "complete_explicit_forbidden_label_counts": (
                    holdout_gap_matrix.get("complete_explicit_forbidden_total", {})
                    .get("label_counts")
                ),
                "target_priority_status": target_priority_matrix.get("status"),
                "priority_context_count": target_priority_matrix.get(
                    "priority_context_count"
                ),
                "mixed_missing_full_snapshot_context_count": (
                    target_priority_matrix.get("category_counts", {}).get(
                        "mixed_missing_full_snapshot"
                    )
                ),
                "noop_missing_full_snapshot_context_count": (
                    target_priority_matrix.get("category_counts", {}).get(
                        "noop_missing_full_snapshot"
                    )
                ),
                "uncovered_priority_context_count": target_priority_matrix.get(
                    "uncovered_priority_context_count"
                ),
                "priority_runbook_status": priority_collection_runbook.get("status"),
                "priority_runbook_command_count": priority_collection_runbook.get(
                    "command_count"
                ),
                "priority_runbook_commandable_context_count": (
                    priority_collection_runbook.get("commandable_context_count")
                ),
                "priority_runbook_unsupported_context_count": (
                    priority_collection_runbook.get("unsupported_context_count")
                ),
                "priority_capture_status": priority_collection_capture_audit.get(
                    "status"
                ),
                "priority_capture_event_count": priority_collection_capture_audit.get(
                    "capture_event_count"
                ),
                "priority_capture_expected_context_hash_count": (
                    priority_collection_capture_audit.get(
                        "expected_context_hash_count"
                    )
                ),
                "priority_capture_expected_context_hit_count": (
                    priority_collection_capture_audit.get(
                        "expected_context_hit_count"
                    )
                ),
                "priority_capture_missing_expected_context_count": (
                    priority_collection_capture_audit.get(
                        "missing_expected_context_count"
                    )
                ),
                "priority_capture_ready_for_selector_holdout": (
                    priority_collection_capture_audit.get(
                        "ready_for_selector_holdout"
                    )
                ),
                "priority_capture_no_certificate_bad_count": (
                    priority_collection_capture_audit.get(
                        "no_certificate_bad_count"
                    )
                ),
                "priority_capture_active_basis_bad_count": (
                    priority_collection_capture_audit.get(
                        "active_basis_bad_count"
                    )
                ),
                "priority_miss_status": priority_capture_miss.get("status"),
                "priority_miss_expected_context_count": priority_capture_miss.get(
                    "expected_context_count"
                ),
                "priority_miss_exact_hit_context_count": priority_capture_miss.get(
                    "exact_hit_context_count"
                ),
                "priority_miss_source_active_hash_missing_context_count": (
                    priority_capture_miss.get(
                        "source_active_hash_missing_context_count"
                    )
                ),
                "priority_miss_same_active_component_drift_context_count": (
                    priority_capture_miss.get(
                        "same_active_component_drift_context_count"
                    )
                ),
                "approved_production_direction_count": registry.get(
                    "approved_production_direction_count"
                ),
            },
            conclusion=(
                "下一步只能继续 addition-before selector holdout / 数据扩展，"
                "优先补 negative/noop 和 mixed full-snapshot contexts；"
                "最新 priority capture 证明补采链路安全，但没有命中目标 contexts，"
                "miss 诊断显示原因是 active hash 未到达和同 active 下组件漂移，"
                "因此还不能进入 production A/B、默认 worker 或 certificate gate。"
            ),
        ),
    ]

    completion_blockers = [
        gate["gate_id"]
        for gate in gates
        if gate["required_before_completion"]
        and gate["status"] not in {"passed", "approved"}
    ]
    approved_production_direction_count = int(
        registry.get("approved_production_direction_count") or 0
    )
    production_direction_approved = (
        approved_production_direction_count > 0 and not completion_blockers
    )
    recommended_next_stage = "selector_holdout_data_expansion"
    checks = {
        "current_answer_passed": current_answer.get("all_checks_pass") is True,
        "objective_audit_passed": objective_audit.get("all_checks_pass") is True,
        "production_ab_gate_passed": production_ab_gate.get("all_checks_pass")
        is True,
        "registry_passed": registry.get("all_checks_pass") is True,
        "next_action_passed": next_action.get("all_checks_pass") is True,
        "selector_blocker_passed": selector_blocker.get("all_checks_pass") is True,
        "component_extension_passed": component_extension.get("all_checks_pass")
        is True,
        "holdout_gap_matrix_passed": holdout_gap_matrix.get("all_checks_pass")
        is True,
        "target_priority_matrix_passed": target_priority_matrix.get(
            "all_checks_pass"
        )
        is True,
        "priority_collection_runbook_passed": (
            priority_collection_runbook.get("all_checks_pass") is True
            and priority_collection_runbook.get("runs_bpc_or_pricing") is False
            and priority_collection_runbook.get("status")
            == "selector_holdout_priority_collection_runbook_ready"
        ),
        "priority_collection_capture_safe_but_not_ready": (
            priority_collection_capture_audit.get("all_checks_pass") is True
            and priority_collection_capture_audit.get("diagnostic_only") is True
            and priority_collection_capture_audit.get("runs_bpc_or_pricing")
            is False
            and int(priority_collection_capture_audit.get("capture_event_count") or 0)
            == 12
            and int(
                priority_collection_capture_audit.get("expected_context_hash_count")
                or 0
            )
            == 3
            and int(
                priority_collection_capture_audit.get("expected_context_hit_count")
                or 0
            )
            == 0
            and priority_collection_capture_audit.get("ready_for_selector_holdout")
            is False
            and int(
                priority_collection_capture_audit.get("no_certificate_bad_count") or 0
            )
            == 0
            and int(
                priority_collection_capture_audit.get("active_basis_bad_count") or 0
            )
            == 0
        ),
        "priority_capture_miss_explains_context_miss": (
            priority_capture_miss.get("all_checks_pass") is True
            and priority_capture_miss.get("diagnostic_only") is True
            and priority_capture_miss.get("runs_bpc_or_pricing") is False
            and priority_capture_miss.get("status")
            == "selector_holdout_priority_capture_miss_diagnosed"
            and int(priority_capture_miss.get("expected_context_count") or 0) == 3
            and int(priority_capture_miss.get("exact_hit_context_count") or 0) == 0
            and int(
                priority_capture_miss.get(
                    "source_active_hash_missing_context_count"
                )
                or 0
            )
            == 2
            and int(
                priority_capture_miss.get(
                    "same_active_component_drift_context_count"
                )
                or 0
            )
            == 1
        ),
        "missing_requirements_match_expected": (
            missing_requirements == EXPECTED_MISSING_REQUIREMENTS
        ),
        "entry_blockers_match_expected": entry_blockers == EXPECTED_ENTRY_BLOCKERS,
        "required_holdouts_match_expected": (
            production_ab_gate.get("required_selector_holdouts")
            == EXPECTED_HOLDOUTS
        ),
        "component_extension_is_not_selector": (
            component_extension.get("component_positive_only") is True
            and component_combined.get("robust_all_holdout_derived_feature_count")
            == 0
            and component_combined.get("robust_all_holdout_model_count") == 0
        ),
        "holdout_gap_requires_negative_mixed_contexts": (
            holdout_gap_matrix.get("recommended_next_stage")
            == "collect_negative_and_mixed_full_snapshot_contexts"
            and holdout_gap_matrix.get("complete_snapshot_context_label_mix", {}).get(
                "mixed_label_context_count"
            )
            == 0
            and holdout_gap_matrix.get("complete_explicit_forbidden_total", {}).get(
                "label_counts"
            )
            == {"improved": 48}
        ),
        "target_priority_identifies_uncovered_contexts": (
            target_priority_matrix.get("recommended_next_stage")
            == "collect_priority_negative_noop_mixed_full_snapshot_contexts"
            and int(target_priority_matrix.get("priority_context_count") or 0) >= 15
            and int(target_priority_matrix.get("uncovered_priority_context_count") or 0)
            >= 1
        ),
        "priority_runbook_not_selector_validation": (
            int(priority_collection_runbook.get("unsupported_context_count") or 0) >= 1
            and int(priority_collection_runbook.get("command_count") or 0) >= 1
        ),
        "no_approved_production_direction": (
            approved_production_direction_count == 0
            and registry.get("production_direction_proven") is False
        ),
        "completion_blockers_match_expected": completion_blockers
        == [
            "production_selector",
            "five_ten_full_no_regression_ab",
            "selected_twenty_walltime_speedup",
        ],
        "recommended_next_stage_is_selector_data": (
            recommended_next_stage == "selector_holdout_data_expansion"
        ),
        "goal_must_remain_active": (
            objective_audit.get("goal_complete") is False
            and current_answer.get("goal_complete") is False
        ),
    }
    return {
        "schema_version": "root_cause_direction_readiness_matrix_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "direction_not_approved",
        "root_cause_supported": True,
        "production_direction_approved": production_direction_approved,
        "approved_production_direction_count": approved_production_direction_count,
        "goal_complete": False,
        "recommended_next_stage": recommended_next_stage,
        "completion_blockers": completion_blockers,
        "gates": gates,
        "sources": {
            "current_answer": str(current_answer_path),
            "objective_audit": str(objective_audit_path),
            "production_ab_gate": str(production_ab_gate_path),
            "registry": str(registry_path),
            "next_action": str(next_action_path),
            "selector_blocker": str(selector_blocker_path),
            "component_extension": str(component_extension_path),
            "holdout_gap_matrix": str(holdout_gap_matrix_path),
            "target_priority_matrix": str(target_priority_matrix_path),
            "priority_collection_runbook": str(priority_collection_runbook_path),
            "priority_collection_capture_audit": str(
                priority_collection_capture_audit_path
            ),
            "priority_capture_miss": str(priority_capture_miss_path),
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "根因解释已经被当前证据支持，但 production optimization direction "
            "没有获批。真正阻塞项仍是 production selector、5/10 full "
            "no-regression A/B 和 selected 20 wall-time speedup。下一步只允许"
            "扩展 no-certificate-effect addition-before selector holdout 数据，"
            "尤其是 negative/noop 和 mixed full-snapshot contexts；不能把 "
            "component payload calibration signal、worker 负列或局部 RMP impact "
            "当作完成。"
        ),
    }


def write_report(matrix: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Direction Readiness Matrix 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告把当前根因证据转成优化方向 readiness matrix。它只读已有",
        "summary，不运行 BPC / pricing / RMP / Pulse，也不改变 worker 或",
        "certificate 配置。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_direction_readiness_matrix = current",
        f"diagnostic_only = {str(matrix['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(matrix['runs_bpc_or_pricing']).lower()}",
        f"status = {matrix['status']}",
        f"root_cause_supported = {str(matrix['root_cause_supported']).lower()}",
        f"production_direction_approved = {str(matrix['production_direction_approved']).lower()}",
        f"approved_production_direction_count = {matrix['approved_production_direction_count']}",
        f"goal_complete = {str(matrix['goal_complete']).lower()}",
        f"recommended_next_stage = {matrix['recommended_next_stage']}",
        "completion_blockers = " + ",".join(matrix["completion_blockers"]),
        f"all_checks_pass = {str(matrix['all_checks_pass']).lower()}",
        "```",
        "",
        "## Readiness Gates",
        "",
    ]
    for gate in matrix["gates"]:
        lines.extend(
            [
                f"### {gate['gate_id']}",
                "",
                "```text",
                f"status = {gate['status']}",
                f"required_before_completion = {str(gate['required_before_completion']).lower()}",
                "```",
                "",
                gate["conclusion"],
                "",
                "```json",
                json.dumps(
                    gate["evidence"],
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## 检查项",
            "",
            "```json",
            json.dumps(matrix["checks"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## 结论",
            "",
            matrix["interpretation"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-answer", default=str(DEFAULT_CURRENT_ANSWER))
    parser.add_argument("--objective-audit", default=str(DEFAULT_OBJECTIVE_AUDIT))
    parser.add_argument("--production-ab-gate", default=str(DEFAULT_PRODUCTION_AB_GATE))
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--next-action", default=str(DEFAULT_NEXT_ACTION))
    parser.add_argument("--selector-blocker", default=str(DEFAULT_SELECTOR_BLOCKER))
    parser.add_argument("--component-extension", default=str(DEFAULT_COMPONENT_EXTENSION))
    parser.add_argument("--holdout-gap-matrix", default=str(DEFAULT_HOLDOUT_GAP_MATRIX))
    parser.add_argument(
        "--target-priority-matrix", default=str(DEFAULT_TARGET_PRIORITY_MATRIX)
    )
    parser.add_argument(
        "--priority-collection-runbook",
        default=str(DEFAULT_PRIORITY_COLLECTION_RUNBOOK),
    )
    parser.add_argument(
        "--priority-collection-capture-audit",
        default=str(DEFAULT_PRIORITY_COLLECTION_CAPTURE_AUDIT),
    )
    parser.add_argument(
        "--priority-capture-miss",
        default=str(DEFAULT_PRIORITY_CAPTURE_MISS),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    matrix = build_matrix(
        current_answer_path=Path(args.current_answer),
        objective_audit_path=Path(args.objective_audit),
        production_ab_gate_path=Path(args.production_ab_gate),
        registry_path=Path(args.registry),
        next_action_path=Path(args.next_action),
        selector_blocker_path=Path(args.selector_blocker),
        component_extension_path=Path(args.component_extension),
        holdout_gap_matrix_path=Path(args.holdout_gap_matrix),
        target_priority_matrix_path=Path(args.target_priority_matrix),
        priority_collection_runbook_path=Path(args.priority_collection_runbook),
        priority_collection_capture_audit_path=Path(
            args.priority_collection_capture_audit
        ),
        priority_capture_miss_path=Path(args.priority_capture_miss),
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(matrix, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(matrix, Path(args.report))
    print(json.dumps(matrix, ensure_ascii=False, sort_keys=True))
    return 0 if matrix["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
