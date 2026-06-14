"""Build a compact causal-chain audit for the current root-cause diagnosis.

This script is diagnostic-only.  It reads existing root-cause summaries and
does not run BPC, pricing, RMP, Pulse, workers, certificates, or benchmarks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_LEDGER = Path("BPC_future/results/root_cause_evidence_ledger_20260613/summary.json")
DEFAULT_CURRENT_ANSWER = Path(
    "BPC_future/results/root_cause_current_answer_20260614/summary.json"
)
DEFAULT_WHY = Path(
    "BPC_future/results/root_cause_why_many_attempts_failed_20260614/summary.json"
)
DEFAULT_DIRECTION = Path(
    "BPC_future/results/root_cause_direction_readiness_matrix_20260614/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_causal_chain_audit_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_causal_chain_audit_zh.md"
)


EXPECTED_CAUSE_IDS = [
    "small_scale_fixed_overhead_sensitivity",
    "twenty_returned_batch_rmp_trajectory_coupling",
    "addition_before_selector_not_production_validated",
]
EXPECTED_MISSING_REQUIREMENTS = [
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
    current_answer_path: Path,
    why_path: Path,
    direction_path: Path,
) -> dict[str, Any]:
    ledger = _read_json(ledger_path)
    current_answer = _read_json(current_answer_path)
    why = _read_json(why_path)
    direction = _read_json(direction_path)

    small = _cause_by_id(why, "small_scale_fixed_overhead_sensitivity")
    twenty = _cause_by_id(why, "twenty_returned_batch_rmp_trajectory_coupling")
    selector = _cause_by_id(why, "addition_before_selector_not_production_validated")
    small_ev = small.get("evidence", {})
    twenty_ev = twenty.get("evidence", {})
    selector_ev = selector.get("evidence", {})

    ledger_missing = (
        ledger.get("completion_decision", {}).get("missing_requirement_names", [])
    )

    causal_chain = [
        {
            "node_id": "observed_requirements_not_met",
            "claim": (
                "目标仍未满足：还缺 5/10 full no-regression、production selector "
                "和 selected 20 wall-time speedup。"
            ),
            "evidence": {
                "goal_complete": ledger.get("goal_status", {}).get("goal_complete"),
                "completion_decision": ledger.get("completion_decision", {}).get(
                    "status"
                ),
                "missing_requirements": ledger_missing,
            },
        },
        {
            "node_id": "small_scale_fixed_overhead",
            "claim": (
                "5/10 的主要失败机制是触发式 worker/audit/probe 固定开销吃掉收益，"
                "不是缺少负列。"
            ),
            "evidence": {
                "triggered_rows": small_ev.get("triggered_rows"),
                "triggered_worse_count": small_ev.get("triggered_worse_count"),
                "triggered_better_count": small_ev.get("triggered_better_count"),
                "nontriggered_official_changed": small_ev.get(
                    "nontriggered_official_changed"
                ),
            },
        },
        {
            "node_id": "negative_columns_not_sufficient",
            "claim": (
                "20-task 上能找到和加入 true-RC negative columns，但这不是稳定加速的充分条件。"
            ),
            "evidence": {
                "phase8q_added_journeys": twenty_ev.get(
                    "negative_columns_route_evidence", {}
                ).get("phase8q_added_journeys"),
                "phase8q_added_new_task_sets": twenty_ev.get(
                    "negative_columns_route_evidence", {}
                ).get("phase8q_added_new_task_sets"),
                "phase8q_all_time_limit": twenty_ev.get(
                    "negative_columns_route_evidence", {}
                ).get("phase8q_all_time_limit"),
                "has_20_walltime_speedup_evidence": twenty_ev.get(
                    "has_20_walltime_speedup_evidence"
                ),
            },
        },
        {
            "node_id": "returned_batch_context_coupling",
            "claim": (
                "负列是否有用取决于 returned-batch composition 与当前 RMP active-basis/"
                "dual trajectory 的耦合。"
            ),
            "evidence": {
                "task20_label_counts": twenty_ev.get(
                    "active_basis_counterexample_task20_label_counts"
                ),
                "task20_new_task_sets": twenty_ev.get(
                    "active_basis_counterexample_task20_new_task_sets"
                ),
                "strongest_noop_true_rc": twenty_ev.get(
                    "active_basis_counterexample_strongest_noop_true_rc"
                ),
                "weaker_improved_than_strongest_noop_count": twenty_ev.get(
                    "weaker_improved_than_strongest_noop_count"
                ),
            },
        },
        {
            "node_id": "selector_not_validated",
            "claim": (
                "现有 addition-before selector 信号还没有通过 context/instance/dataset "
                "holdout，因此不能进入 production A/B 或默认 worker。"
            ),
            "evidence": {
                "selector_status": selector_ev.get("selector_status"),
                "robust_single_features": selector_ev.get("robust_single_features"),
                "robust_models": selector_ev.get("robust_models"),
                "component_payload_extension_combined_robust_features": (
                    selector_ev.get(
                        "component_payload_extension_combined_robust_features"
                    )
                ),
                "component_payload_extension_combined_robust_models": (
                    selector_ev.get(
                        "component_payload_extension_combined_robust_models"
                    )
                ),
                "selector_holdout_gap_complete_snapshot_label_counts": (
                    selector_ev.get(
                        "selector_holdout_gap_complete_snapshot_label_counts"
                    )
                ),
                "selector_holdout_gap_mixed_context_count": (
                    selector_ev.get("selector_holdout_gap_mixed_context_count")
                ),
            },
        },
        {
            "node_id": "exact_context_not_recoverable_by_shortcut",
            "claim": (
                "source profile 重跑和 active-hash-only 匹配不能补齐 selector holdout；"
                "必须捕获完整 context 组件。"
            ),
            "evidence": {
                "priority_capture_miss_expected_context_count": selector_ev.get(
                    "priority_capture_miss_expected_context_count"
                ),
                "priority_capture_miss_exact_hit_context_count": selector_ev.get(
                    "priority_capture_miss_exact_hit_context_count"
                ),
                "priority_capture_miss_source_active_hash_missing_context_count": (
                    selector_ev.get(
                        "priority_capture_miss_source_active_hash_missing_context_count"
                    )
                ),
                "priority_capture_miss_same_active_component_drift_context_count": (
                    selector_ev.get(
                        "priority_capture_miss_same_active_component_drift_context_count"
                    )
                ),
                "context_trajectory_exact_component_count": selector_ev.get(
                    "context_trajectory_exact_component_count"
                ),
                "context_trajectory_required_payload_count": selector_ev.get(
                    "context_trajectory_required_payload_count"
                ),
                "source_profile_rerun_is_not_sufficient": selector_ev.get(
                    "source_profile_rerun_is_not_sufficient"
                ),
                "same_active_hash_is_not_sufficient": selector_ev.get(
                    "same_active_hash_is_not_sufficient"
                ),
            },
        },
        {
            "node_id": "allowed_next_stage",
            "claim": (
                "下一步只能做 calibration-only selector holdout 数据扩展；production "
                "A/B、默认 worker、certificate gate 仍被阻塞。"
            ),
            "evidence": {
                "direction_status": direction.get("status"),
                "approved_production_direction_count": direction.get(
                    "approved_production_direction_count"
                ),
                "production_direction_approved": direction.get(
                    "production_direction_approved"
                ),
                "recommended_next_stage": direction.get("recommended_next_stage"),
                "completion_blockers": direction.get("completion_blockers"),
            },
        },
    ]

    checks = {
        "ledger_passed_and_goal_active": (
            ledger.get("all_checks_pass") is True
            and ledger.get("goal_status", {}).get("goal_complete") is False
            and ledger.get("completion_decision", {}).get("status")
            == "keep_goal_active"
            and ledger_missing == EXPECTED_MISSING_REQUIREMENTS
        ),
        "current_answer_passed": (
            current_answer.get("all_checks_pass") is True
            and current_answer.get("status")
            == "root_cause_supported_but_optimization_direction_unproven"
            and current_answer.get("goal_complete") is False
        ),
        "why_passed": (
            why.get("all_checks_pass") is True
            and why.get("status") == "supported_but_optimization_direction_unproven"
            and [cause.get("cause_id") for cause in why.get("causes", [])]
            == EXPECTED_CAUSE_IDS
        ),
        "direction_not_approved": (
            direction.get("all_checks_pass") is True
            and direction.get("status") == "direction_not_approved"
            and direction.get("production_direction_approved") is False
            and _as_int(direction.get("approved_production_direction_count")) == 0
        ),
        "small_cause_supported": (
            _as_int(small_ev.get("triggered_rows")) == 220
            and _as_int(small_ev.get("triggered_worse_count")) == 220
            and _as_int(small_ev.get("triggered_better_count")) == 0
            and _as_int(small_ev.get("nontriggered_official_changed")) == 0
        ),
        "negative_columns_not_sufficient": (
            twenty_ev.get("negative_columns_route_status")
            == "ruled_out_as_sufficient_condition"
            and twenty_ev.get("has_20_walltime_speedup_evidence") is False
            and twenty_ev.get("negative_columns_route_evidence", {}).get(
                "phase8q_all_time_limit"
            )
            is True
            and _as_int(
                twenty_ev.get("negative_columns_route_evidence", {}).get(
                    "phase8q_added_journeys"
                )
            )
            == 10
        ),
        "batch_context_coupling_supported": (
            (twenty_ev.get("active_basis_counterexample_task20_label_counts") or {})
            == {"improved": 10, "noop": 2}
            and _as_int(twenty_ev.get("active_basis_counterexample_task20_new_task_sets"))
            == 12
            and float(
                twenty_ev.get("active_basis_counterexample_strongest_noop_true_rc")
            )
            == -128.547499
            and _as_int(twenty_ev.get("weaker_improved_than_strongest_noop_count"))
            == 8
        ),
        "selector_not_validated": (
            selector_ev.get("selector_status") == "production_selector_not_validated"
            and not selector_ev.get("robust_single_features")
            and not selector_ev.get("robust_models")
            and _as_int(
                selector_ev.get(
                    "component_payload_extension_combined_robust_features"
                )
            )
            == 0
            and _as_int(
                selector_ev.get(
                    "component_payload_extension_combined_robust_models"
                )
            )
            == 0
        ),
        "exact_context_shortcut_ruled_out": (
            _as_int(selector_ev.get("priority_capture_miss_expected_context_count"))
            == 3
            and _as_int(selector_ev.get("priority_capture_miss_exact_hit_context_count"))
            == 0
            and _as_int(
                selector_ev.get(
                    "priority_capture_miss_source_active_hash_missing_context_count"
                )
            )
            == 2
            and _as_int(
                selector_ev.get(
                    "priority_capture_miss_same_active_component_drift_context_count"
                )
            )
            == 1
            and _as_int(selector_ev.get("context_trajectory_exact_component_count"))
            == 9
            and _as_int(selector_ev.get("context_trajectory_required_payload_count"))
            == 9
            and selector_ev.get("source_profile_rerun_is_not_sufficient") is True
            and selector_ev.get("same_active_hash_is_not_sufficient") is True
        ),
    }

    return {
        "schema_version": "root_cause_causal_chain_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "sources": {
            "ledger": str(ledger_path),
            "current_answer": str(current_answer_path),
            "why": str(why_path),
            "direction": str(direction_path),
        },
        "status": "causal_chain_supported_but_direction_unapproved",
        "causal_chain": causal_chain,
        "missing_requirements": ledger_missing,
        "production_direction_approved": direction.get("production_direction_approved"),
        "goal_complete": ledger.get("goal_status", {}).get("goal_complete"),
        "completion_decision": ledger.get("completion_decision", {}).get("status"),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# BPC_future Root Cause Causal Chain Audit 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告把当前根因判断整理成一条可复查因果链。它只读已有 summary，",
        "不运行 BPC / pricing / RMP / Pulse，也不改变 worker 或 certificate 行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_causal_chain_audit = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"causal_chain_node_count = {len(summary['causal_chain'])}",
        f"goal_complete = {str(summary['goal_complete']).lower()}",
        f"completion_decision = {summary['completion_decision']}",
        "missing_requirements = " + ",".join(summary["missing_requirements"]),
        f"production_direction_approved = {str(summary['production_direction_approved']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 因果链",
        "",
    ]
    for node in summary["causal_chain"]:
        lines.extend(
            [
                f"### {node['node_id']}",
                "",
                node["claim"],
                "",
                "```json",
                json.dumps(node["evidence"], ensure_ascii=False, indent=2, sort_keys=True),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## 结论",
            "",
            "当前根因解释已由证据链支持，但 production optimization direction 仍未获批。",
            "因此不能默认启用 worker、不能打开 official certificate gate，也不能把当前",
            "calibration signal 当作 5/10 不退化和 20 大幅加速的证明。",
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
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--current-answer", default=str(DEFAULT_CURRENT_ANSWER))
    parser.add_argument("--why", default=str(DEFAULT_WHY))
    parser.add_argument("--direction", default=str(DEFAULT_DIRECTION))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = build_summary(
        ledger_path=Path(args.ledger),
        current_answer_path=Path(args.current_answer),
        why_path=Path(args.why),
        direction_path=Path(args.direction),
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
