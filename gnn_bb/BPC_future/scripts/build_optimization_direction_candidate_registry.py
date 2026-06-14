"""Build the current optimization-direction candidate registry.

This diagnostic-only registry answers why the recent BPC_future optimization
work still has not produced a production-ready direction.  It only reads
existing summary artifacts and writes a compact status table; it does not run
BPC, pricing, RMP, Pulse, or any benchmark.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_FAILURE_MATRIX = Path(
    "BPC_future/results/root_cause_failure_matrix_20260613/summary.json"
)
DEFAULT_OBJECTIVE_AUDIT = Path(
    "BPC_future/results/root_cause_objective_completion_audit_20260614/"
    "summary.json"
)
DEFAULT_NEXT_PROTOCOL = Path(
    "BPC_future/results/root_cause_next_evidence_protocol_catalog_20260614/"
    "summary.json"
)
DEFAULT_SELECTOR_BLOCKER = Path(
    "BPC_future/results/root_cause_production_selector_blocker_catalog_20260614/"
    "summary.json"
)
DEFAULT_PRODUCTION_AB_GATE = Path(
    "BPC_future/results/root_cause_production_ab_entry_gate_catalog_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_optimization_direction_candidate_registry_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_optimization_direction_candidate_registry_zh.md"
)


EXPECTED_MISSING_REQUIREMENTS = [
    "five_ten_full_no_regression_ab",
    "production_validated_selector",
    "twenty_walltime_speedup",
]
EXPECTED_GATE_ORDER = [
    "exact_context_capture_and_replay_dataset",
    "addition_before_selector",
    "production_candidate_ab",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _failure_routes_by_id(failure_matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(route.get("route_id", "")): route
        for route in failure_matrix.get("routes", [])
    }


def _route(
    *,
    direction_id: str,
    title: str,
    status: str,
    allowed_next_action: str,
    why: str,
    evidence: dict[str, Any],
    source: str,
) -> dict[str, Any]:
    return {
        "direction_id": direction_id,
        "title": title,
        "status": status,
        "allowed_next_action": allowed_next_action,
        "why": why,
        "evidence": evidence,
        "source": source,
    }


def build_registry(
    *,
    failure_matrix_path: Path,
    objective_audit_path: Path,
    next_protocol_path: Path,
    selector_blocker_path: Path,
    production_ab_gate_path: Path,
) -> dict[str, Any]:
    failure_matrix = _read_json(failure_matrix_path)
    objective_audit = _read_json(objective_audit_path)
    next_protocol = _read_json(next_protocol_path)
    selector_blocker = _read_json(selector_blocker_path)
    production_ab_gate = _read_json(production_ab_gate_path)
    failure_routes = _failure_routes_by_id(failure_matrix)

    candidates = [
        _route(
            direction_id="pulse_wiring_or_certificate_semantics",
            title="继续修 Pulse 接线、物化或证书状态机",
            status="ruled_out_as_primary_root_cause",
            allowed_next_action="do_not_treat_as_production_speedup_direction",
            why=(
                "证书状态机和列物化已经能安全加入 true-RC negative columns；"
                "剩余失败是 downstream ROI，而不是接线本身。"
            ),
            evidence=failure_routes.get(
                "pulse_wiring_or_certificate_semantics", {}
            ).get("evidence", {}),
            source=str(failure_matrix_path),
        ),
        _route(
            direction_id="more_true_rc_negative_columns",
            title="继续找更多或更负的 true-RC negative columns",
            status="ruled_out_as_sufficient_condition",
            allowed_next_action="only_as_calibration_signal_not_as_completion",
            why=(
                "20-task run 已经能加入 true-RC negative columns 和新 task sets，"
                "但仍没有稳定 wall-time/status/gap 改善。"
            ),
            evidence=failure_routes.get("more_true_rc_negative_columns", {}).get(
                "evidence", {}
            ),
            source=str(failure_matrix_path),
        ),
        _route(
            direction_id="expand_worker_budget_or_default_worker",
            title="扩大 worker 预算或默认启用 worker",
            status="forbidden_for_current_stage",
            allowed_next_action="keep_default_disabled",
            why=(
                "5/10 对固定开销敏感；触发 worker/audit/probe 的行整体变慢，"
                "不触发的 no-op gate 才保持官方结果不变。"
            ),
            evidence=failure_routes.get(
                "expand_worker_budget_or_default_worker", {}
            ).get("evidence", {}),
            source=str(failure_matrix_path),
        ),
        _route(
            direction_id="true_rc_threshold_or_local_column_selector",
            title="用 true-RC 阈值、task-set 或 sequence 局部特征筛列",
            status="not_production_validated",
            allowed_next_action="continue_holdout_only",
            why=(
                "局部阈值有 calibration signal，但存在 false positive 和 false "
                "negative；同一 task-set/sequence 可在不同 context 下相反。"
            ),
            evidence=failure_routes.get(
                "true_rc_threshold_or_local_column_selector", {}
            ).get("evidence", {}),
            source=str(failure_matrix_path),
        ),
        _route(
            direction_id="simple_ml_or_batch_selector",
            title="简单 ML 或 batch-level selector",
            status="not_production_validated",
            allowed_next_action="continue_context_instance_dataset_holdout",
            why=(
                "简单模型与 batch gate 有信号，但没有同时通过 context、instance、"
                "dataset 的生产 holdout。"
            ),
            evidence=failure_routes.get("simple_ml_or_batch_selector", {}).get(
                "evidence", {}
            ),
            source=str(failure_matrix_path),
        ),
        _route(
            direction_id="simple_rmp_trajectory_proxy_selector",
            title="用 active-basis hash churn / RMP degeneracy proxy 做 selector",
            status="not_production_validated",
            allowed_next_action="do_not_promote_proxy_to_production_selector",
            why=(
                "3 个 addition-before RMP proxy 已进入离线 holdout；active-basis "
                "hash proxy 和 degeneracy proxy 仍不能跨 context/instance/dataset "
                "稳定通过，不能当生产 gate。"
            ),
            evidence=failure_routes.get(
                "simple_rmp_trajectory_proxy_selector", {}
            ).get("evidence", {}),
            source=str(failure_matrix_path),
        ),
        _route(
            direction_id="single_context_or_local_replay_success",
            title="把单 context replay 成功当生产证据",
            status="forbidden_shortcut",
            allowed_next_action="require_holdout_and_bpc_ab",
            why=(
                "exact replay 同时包含 high-impact 和 no-op/replacement 样本；"
                "单点成功不能证明泛化 ROI。"
            ),
            evidence=failure_routes.get(
                "single_context_or_local_replay_success", {}
            ).get("evidence", {}),
            source=str(failure_matrix_path),
        ),
        _route(
            direction_id="exact_context_capture_and_replay_dataset",
            title="继续扩 exact-context capture/replay 校准集",
            status="allowed_calibration_only",
            allowed_next_action="build_more_no_certificate_effect_replay_cases",
            why=(
                "该 gate 已可支持 selector calibration attempt，但仍不能直接进入"
                " production A/B 或 certificate effect。"
            ),
            evidence=next_protocol.get("readiness", [{}])[0].get("evidence", {}),
            source=str(next_protocol_path),
        ),
        _route(
            direction_id="addition_before_selector",
            title="训练只使用 addition-before 特征的 selector",
            status="calibration_only_not_production_validated",
            allowed_next_action="must_pass_context_instance_dataset_holdouts",
            why=(
                "存在 replay-calibrated selector 候选，但 blocker catalog 显示"
                "具体反例、fold gate、规则族和 context anatomy 仍阻塞上线。"
            ),
            evidence={
                "blocker_count": len(selector_blocker.get("blockers", [])),
                "blocker_ids": [
                    blocker.get("blocker_id")
                    for blocker in selector_blocker.get("blockers", [])
                ],
                "required_holdouts": selector_blocker.get("required_holdouts", []),
            },
            source=str(selector_blocker_path),
        ),
        _route(
            direction_id="production_candidate_ab",
            title="进入 production candidate BPC A/B",
            status="blocked",
            allowed_next_action="do_not_enter_until_selector_and_5_10_20_gates_pass",
            why=(
                "入口仍被 selector_not_validated、five_ten_full_no_regression_missing、"
                "twenty_speedup_missing 三项同时阻塞。"
            ),
            evidence={
                "entry_gate_blockers": production_ab_gate.get(
                    "entry_gate_blockers", []
                ),
                "forbidden_shortcuts": production_ab_gate.get(
                    "forbidden_shortcuts", []
                ),
            },
            source=str(production_ab_gate_path),
        ),
        _route(
            direction_id="official_certificate_gate",
            title="开放 Pulse official certificate gate",
            status="forbidden_for_current_stage",
            allowed_next_action="keep_certificate_effect_disabled",
            why=(
                "当前正向信号是 calibration/worker 找列，不是完整 proof；"
                "certificate effect 在 production A/B 前仍是 forbidden shortcut。"
            ),
            evidence={
                "must_not_open_certificate_gate": production_ab_gate.get(
                    "must_not_open_certificate_gate"
                ),
                "forbidden_shortcuts": production_ab_gate.get(
                    "forbidden_shortcuts", []
                ),
            },
            source=str(production_ab_gate_path),
        ),
    ]

    approved_statuses = {"production_validated", "approved_for_production_ab"}
    approved = [
        candidate
        for candidate in candidates
        if candidate["status"] in approved_statuses
    ]
    allowed_calibration = [
        candidate
        for candidate in candidates
        if "calibration" in candidate["status"]
        or "holdout" in candidate["allowed_next_action"]
    ]
    forbidden = [
        candidate
        for candidate in candidates
        if candidate["status"].startswith("forbidden")
        or candidate["status"] == "forbidden_shortcut"
    ]
    checks = {
        "failure_matrix_passed": failure_matrix.get("all_checks_pass") is True,
        "objective_audit_passed": objective_audit.get("all_checks_pass") is True,
        "next_protocol_passed": next_protocol.get("all_checks_pass") is True,
        "selector_blocker_passed": selector_blocker.get("all_checks_pass") is True,
        "production_ab_gate_passed": production_ab_gate.get("all_checks_pass")
        is True,
        "goal_not_complete": objective_audit.get("goal_complete") is False,
        "missing_requirements_match_expected": (
            objective_audit.get("missing_requirements")
            == EXPECTED_MISSING_REQUIREMENTS
        ),
        "gate_order_matches_expected": (
            next_protocol.get("gate_order") == EXPECTED_GATE_ORDER
        ),
        "production_ab_blocked": (
            production_ab_gate.get("production_candidate_ab_entry_status")
            == "blocked"
        ),
        "worker_default_forbidden": (
            production_ab_gate.get("must_not_enable_worker_default") is True
        ),
        "certificate_gate_forbidden": (
            production_ab_gate.get("must_not_open_certificate_gate") is True
        ),
        "no_approved_production_direction": not approved,
        "has_allowed_calibration_direction": bool(allowed_calibration),
        "all_failure_routes_accounted": len(failure_routes) >= 6,
    }
    return {
        "schema_version": "optimization_direction_candidate_registry_v1",
        "sources": {
            "failure_matrix": str(failure_matrix_path),
            "objective_audit": str(objective_audit_path),
            "next_protocol": str(next_protocol_path),
            "selector_blocker": str(selector_blocker_path),
            "production_ab_gate": str(production_ab_gate_path),
        },
        "root_cause_short": failure_matrix.get("summary", {}).get(
            "root_cause_short"
        ),
        "answer_short": (
            "不是 Pulse 子模块单点失效；5/10 被固定开销伤害，20 的 true-RC "
            "negative columns 又不足以稳定改变 RMP trajectory。当前缺的是"
            " addition-before、低开销、跨 context/instance/dataset 通过的 selector。"
        ),
        "current_allowed_next_stage": next_protocol.get("current_stage"),
        "production_direction_proven": False,
        "goal_complete": objective_audit.get("goal_complete"),
        "missing_requirements": objective_audit.get("missing_requirements"),
        "candidate_count": len(candidates),
        "approved_production_direction_count": len(approved),
        "forbidden_direction_count": len(forbidden),
        "allowed_calibration_direction_count": len(allowed_calibration),
        "candidates": candidates,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "当前不是没有任何信号，而是信号还停留在 calibration 层："
            "负列能被安全找到和加入，但不能稳定转化为 20-task wall-time/status/gap "
            "改进；同时 5/10 对额外触发开销敏感。因此下一步只能继续 "
            "addition-before selector holdout，不能默认启用 worker，也不能打开 "
            "official certificate gate。"
        ),
    }


def write_report(registry: dict[str, Any], path: Path) -> None:
    lines = [
        "# Optimization Direction Candidate Registry 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告回答“做了这么多工作为什么还不行”。它只汇总已有诊断",
        "summary，不运行 solver，不改变 pricing / worker / certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "optimization_direction_candidate_registry = current",
        f"candidate_count = {registry['candidate_count']}",
        f"approved_production_direction_count = {registry['approved_production_direction_count']}",
        f"forbidden_direction_count = {registry['forbidden_direction_count']}",
        f"allowed_calibration_direction_count = {registry['allowed_calibration_direction_count']}",
        f"production_direction_proven = {str(registry['production_direction_proven']).lower()}",
        f"goal_complete = {str(registry['goal_complete']).lower()}",
        f"missing_requirements = {','.join(registry['missing_requirements'])}",
        f"current_allowed_next_stage = {registry['current_allowed_next_stage']}",
        f"all_checks_pass = {str(registry['all_checks_pass']).lower()}",
        "```",
        "",
        "## 一句话回答",
        "",
        registry["answer_short"],
        "",
        "## 当前方向状态表",
        "",
        "| 方向 | 状态 | 允许的下一步 | 原因 |",
        "|---|---|---|---|",
    ]
    for candidate in registry["candidates"]:
        lines.append(
            "| {title} | `{status}` | `{action}` | {why} |".format(
                title=candidate["title"],
                status=candidate["status"],
                action=candidate["allowed_next_action"],
                why=candidate["why"],
            )
        )
    lines.extend(
        [
            "",
            "## 结论",
            "",
            registry["interpretation"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--failure-matrix", default=str(DEFAULT_FAILURE_MATRIX))
    parser.add_argument("--objective-audit", default=str(DEFAULT_OBJECTIVE_AUDIT))
    parser.add_argument("--next-protocol", default=str(DEFAULT_NEXT_PROTOCOL))
    parser.add_argument("--selector-blocker", default=str(DEFAULT_SELECTOR_BLOCKER))
    parser.add_argument(
        "--production-ab-gate", default=str(DEFAULT_PRODUCTION_AB_GATE)
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    registry = build_registry(
        failure_matrix_path=Path(args.failure_matrix),
        objective_audit_path=Path(args.objective_audit),
        next_protocol_path=Path(args.next_protocol),
        selector_blocker_path=Path(args.selector_blocker),
        production_ab_gate_path=Path(args.production_ab_gate),
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(registry, Path(args.report))
    print(json.dumps(registry, ensure_ascii=False, sort_keys=True))
    return 0 if registry["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
