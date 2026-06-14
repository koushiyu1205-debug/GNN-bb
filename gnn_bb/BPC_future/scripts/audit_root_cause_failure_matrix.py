#!/usr/bin/env python3
"""Build a route-level failure attribution matrix for BPC_future root cause.

The script is read-only with respect to solver state. It summarizes existing
evidence into a concrete matrix explaining why prior optimization routes are
not production-valid directions yet.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/root_cause_failure_matrix_20260613")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_failure_matrix_zh.md"
)

EVIDENCE_LEDGER = Path("BPC_future/results/root_cause_evidence_ledger_20260613/summary.json")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _check(value: Any) -> bool:
    return bool(value)


def build_summary() -> dict[str, Any]:
    ledger = _read_json(EVIDENCE_LEDGER)
    checks = ledger.get("checks", {})
    goal = ledger.get("goal_status", {})

    small = checks.get("small_scale_overhead", {})
    phase8q = checks.get("phase8q_worker_add_columns", {})
    phase7o = checks.get("phase7o_worker_roi", {})
    selector_holdout = checks.get("selector_holdout_status", {})
    replay_selector = checks.get("replay_calibrated_selector_candidate", {})
    selector_errors = checks.get("selector_error_anatomy", {})
    threshold = checks.get("selector_threshold_frontier", {})
    context_collision = checks.get("selector_context_collision", {})
    local_direction = checks.get("selector_local_feature_direction", {})
    batch_gate = checks.get("batch_gate_stability", {})
    batch_level = checks.get("batch_level_selector", {})
    context_only = checks.get("context_only_baseline", {})
    code_boundary = checks.get("root_cause_code_boundary", {})
    replay_impact = checks.get("counterfactual_replay_impact_dataset", {})
    candidate_models = checks.get("candidate_selector_models", {})
    calibrated_ab = checks.get("calibrated_selector_selected20_repeat_ab", {})
    enriched_single = checks.get("selector_enriched_rmp_feature_holdout", {})
    enriched_model = checks.get("selector_enriched_multifeature_model_holdout", {})

    routes: list[dict[str, Any]] = [
        {
            "route_id": "pulse_wiring_or_certificate_semantics",
            "route": "Pulse wiring / materialization / certificate semantics",
            "status": "ruled_out_as_primary_root_cause",
            "why_not_enough": (
                "Worker/capture paths can safely add or record true-RC negative "
                "journeys without critical disagreement; the remaining failure is ROI."
            ),
            "evidence": {
                "phase8q_added_journeys": phase8q.get("pulse_worker_added_journeys"),
                "phase8q_added_new_task_sets": phase8q.get(
                    "pulse_worker_added_new_task_set_count"
                ),
                "phase8q_all_time_limit": phase8q.get("all_time_limit"),
                "code_boundary_pass": code_boundary.get(
                    "check_code_boundary_no_unvalidated_production_effect"
                ),
            },
            "checks": {
                "can_add_negative_columns": (
                    int(phase8q.get("pulse_worker_added_journeys", 0)) > 0
                ),
                "still_no_walltime_roi": phase8q.get("all_time_limit") is True,
                "no_unvalidated_default_effect": code_boundary.get(
                    "check_code_boundary_no_unvalidated_production_effect"
                )
                is True,
            },
        },
        {
            "route_id": "more_true_rc_negative_columns",
            "route": "Find or return more true-RC negative columns",
            "status": "ruled_out_as_sufficient_condition",
            "why_not_enough": (
                "20-task runs can add true-RC negative journeys, including new "
                "task sets, but Phase 7O/8Q still end in TIME_LIMIT."
            ),
            "evidence": {
                "phase7o_all_time_limit": phase7o.get("all_time_limit"),
                "phase8q_all_time_limit": phase8q.get("all_time_limit"),
                "phase8q_added_journeys": phase8q.get("pulse_worker_added_journeys"),
                "phase8q_added_new_task_sets": phase8q.get(
                    "pulse_worker_added_new_task_set_count"
                ),
                "phase8q_completion_bound_retry_count": phase8q.get(
                    "completion_bound_retry_count"
                ),
            },
            "checks": {
                "negative_columns_exist": (
                    int(phase8q.get("pulse_worker_added_journeys", 0)) > 0
                ),
                "new_task_sets_exist": (
                    int(phase8q.get("pulse_worker_added_new_task_set_count", 0)) > 0
                ),
                "still_time_limit": (
                    phase7o.get("all_time_limit") is True
                    and phase8q.get("all_time_limit") is True
                ),
            },
        },
        {
            "route_id": "expand_worker_budget_or_default_worker",
            "route": "Expand worker budget or enable worker by default",
            "status": "ruled_out_for_5_10_safety",
            "why_not_enough": (
                "5/10 scale is fixed-overhead sensitive: triggered mechanisms "
                "consistently worsen wall time, while non-triggered rows preserve "
                "official results."
            ),
            "evidence": {
                "triggered_rows": small.get("triggered_rows"),
                "triggered_worse_count": small.get("triggered_worse_count"),
                "triggered_better_count": small.get("triggered_better_count"),
                "nontriggered_official_changed": small.get(
                    "nontriggered_official_changed"
                ),
            },
            "checks": {
                "triggered_all_worse": small.get("check_triggered_all_worse") is True,
                "nontriggered_no_official_change": (
                    small.get("check_nontriggered_no_official_change") is True
                ),
            },
        },
        {
            "route_id": "true_rc_threshold_or_local_column_selector",
            "route": "Use true-RC threshold / task-set / sequence local features",
            "status": "not_production_validated",
            "why_not_enough": (
                "Replay-local selector candidates exist, but exact holdout still "
                "has false positives and false negatives; mixed task-set/sequence "
                "groups prove local column shape is insufficient."
            ),
            "evidence": {
                "recommended_selector_candidate": selector_holdout.get(
                    "recommended_selector_candidate"
                )
                or replay_selector.get(
                    "recommended_selector_candidate"
                ),
                "exact_false_positive_count": selector_holdout.get(
                    "exact_false_positive_count"
                ),
                "exact_false_negative_count": selector_holdout.get(
                    "exact_false_negative_count"
                ),
                "false_positive_new_task_set_noop_count": selector_errors.get(
                    "false_positive_new_task_set_noop_count"
                ),
                "false_negative_new_task_set_improved_count": selector_errors.get(
                    "false_negative_new_task_set_improved_count"
                ),
                "perfect_threshold_count": threshold.get("perfect_threshold_count"),
                "task_set_mixed_group_count": context_collision.get(
                    "task_set_mixed_group_count"
                ),
                "task_sequence_mixed_group_count": context_collision.get(
                    "task_sequence_mixed_group_count"
                ),
                "task_set_true_rc_improved_lower_count": local_direction.get(
                    "task_set_true_rc_improved_lower_count"
                ),
                "task_set_true_rc_noop_lower_count": local_direction.get(
                    "task_set_true_rc_noop_lower_count"
                ),
            },
            "checks": {
                "has_false_positives": int(
                    selector_holdout.get("exact_false_positive_count", 0)
                )
                > 0,
                "has_false_negatives": int(
                    selector_holdout.get("exact_false_negative_count", 0)
                )
                > 0,
                "no_perfect_threshold": int(
                    threshold.get("perfect_threshold_count", 0)
                )
                == 0,
                "local_context_collision_exists": int(
                    context_collision.get("task_set_mixed_group_count", 0)
                )
                > 0,
                "true_rc_direction_flips": (
                    int(local_direction.get("task_set_true_rc_improved_lower_count", 0))
                    > 0
                    and int(local_direction.get("task_set_true_rc_noop_lower_count", 0))
                    > 0
                ),
            },
        },
        {
            "route_id": "simple_ml_or_batch_selector",
            "route": "Simple ML / batch-level selector",
            "status": "not_production_validated",
            "why_not_enough": (
                "Simple candidate and batch selectors show local signal, but strict "
                "context/instance/dataset gates do not pass simultaneously."
            ),
            "evidence": {
                "candidate_selector_passing_models": candidate_models.get(
                    "leave_one_dataset", {}
                )
                .get("strict_selector_gate", {})
                .get("passing_models"),
                "batch_level_pre_batch_lod_precision": batch_level.get(
                    "leave_one_dataset", {}
                )
                .get("pre_batch", {})
                .get("precision"),
                "batch_gate_positive_lod_precision": batch_gate.get(
                    "positive_trigger_gate", {}
                )
                .get("leave_one_dataset", {})
                .get("precision"),
                "context_only_dataset_precision": context_only.get(
                    "best_by_holdout", {}
                )
                .get("dataset", {})
                .get("metrics", {})
                .get("precision"),
            },
            "checks": {
                "candidate_models_no_strict_pass": not candidate_models.get(
                    "leave_one_dataset", {}
                )
                .get("strict_selector_gate", {})
                .get("passing_models", []),
                "batch_level_not_stable": batch_level.get(
                    "check_batch_level_selector_still_not_stable"
                )
                is True,
                "batch_gate_not_stable": batch_gate.get(
                    "check_batch_gates_are_not_stable"
                )
                is True,
                "context_only_not_enough": context_only.get(
                    "check_context_only_has_signal_but_not_enough"
                )
                is True,
            },
        },
        {
            "route_id": "simple_rmp_trajectory_proxy_selector",
            "route": "Use simple RMP trajectory proxy selector",
            "status": "not_production_validated",
            "why_not_enough": (
                "Recovered RMP/context fields plus addition-before active-basis "
                "hash churn and degeneracy proxy fields still do not pass "
                "context/instance/dataset holdout."
            ),
            "evidence": {
                "enriched_feature_count": len(
                    enriched_single.get("enriched_rmp_features", [])
                ),
                "active_basis_hash_churn_context_folds": (
                    enriched_single.get(
                        "active_basis_hash_churn_context_passing_folds"
                    )
                ),
                "rmp_degeneracy_proxy_context_folds": (
                    enriched_single.get(
                        "rmp_degeneracy_proxy_context_passing_folds"
                    )
                ),
                "robust_enriched_feature_count": (
                    enriched_single.get("robust_all_holdout_enriched_feature_count")
                ),
                "best_multifeature_model": enriched_model.get("best_context_model"),
                "best_multifeature_context_folds": (
                    enriched_model.get("best_context_model_context_folds")
                ),
                "robust_model_count": enriched_model.get(
                    "robust_all_holdout_model_count"
                ),
            },
            "checks": {
                "proxy_fields_evaluated": len(
                    enriched_single.get("enriched_rmp_features", [])
                )
                >= 16,
                "active_basis_proxy_not_robust": int(
                    enriched_single.get(
                        "active_basis_hash_churn_context_passing_folds", 0
                    )
                )
                < 28,
                "degeneracy_proxy_not_robust": int(
                    enriched_single.get(
                        "rmp_degeneracy_proxy_context_passing_folds", 0
                    )
                )
                < 28,
                "no_enriched_single_feature_passes": int(
                    enriched_single.get(
                        "robust_all_holdout_enriched_feature_count", 0
                    )
                )
                == 0,
                "no_multifeature_model_passes": int(
                    enriched_model.get("robust_all_holdout_model_count", 0)
                )
                == 0,
            },
        },
        {
            "route_id": "single_context_or_local_replay_success",
            "route": "Use single-context local replay success as production proof",
            "status": "forbidden_shortcut",
            "why_not_enough": (
                "Exact replay contains both high-impact and no-op candidates; "
                "single-context movement does not prove holdout-stable production ROI."
            ),
            "evidence": {
                "real_capture_high_impact_candidate_count": replay_impact.get(
                    "real_capture", {}
                ).get("high_impact_candidate_count"),
                "duplicate_noop_candidate_count": replay_impact.get(
                    "duplicate_noop", {}
                ).get("noop_candidate_count"),
                "apollo_primal_deltas": calibrated_ab.get("apollo_primal_deltas"),
                "apollo_wall_deltas": calibrated_ab.get("apollo_wall_deltas"),
                "all_profile_statuses": calibrated_ab.get("all_profile_statuses"),
            },
            "checks": {
                "has_high_impact": int(
                    replay_impact.get("real_capture", {}).get(
                        "high_impact_candidate_count", 0
                    )
                )
                > 0,
                "has_noop_counterexample": int(
                    replay_impact.get("duplicate_noop", {}).get(
                        "noop_candidate_count", 0
                    )
                )
                > 0,
                "selected20_rejects_speedup": calibrated_ab.get(
                    "check_selected20_repeat_ab_rejects_production_speedup"
                )
                is True,
            },
        },
    ]

    for route in routes:
        route["all_route_checks_pass"] = all(_check(value) for value in route["checks"].values())

    production_direction_proven = bool(goal.get("production_direction_proven"))
    all_checks_pass = bool(
        all(route["all_route_checks_pass"] for route in routes)
        and not production_direction_proven
        and "production_validated_selector" in goal.get("missing_requirement_names", [])
        and "twenty_walltime_speedup" in goal.get("missing_requirement_names", [])
    )
    return {
        "schema_version": "root_cause_failure_matrix_v1",
        "source_ledger": str(EVIDENCE_LEDGER),
        "ledger_all_checks_pass": ledger.get("all_checks_pass"),
        "goal_status": goal,
        "routes": routes,
        "all_checks_pass": all_checks_pass,
        "summary": {
            "route_count": len(routes),
            "blocked_or_ruled_out_route_count": sum(
                1
                for route in routes
                if route["status"]
                in {
                    "ruled_out_as_primary_root_cause",
                    "ruled_out_as_sufficient_condition",
                    "ruled_out_for_5_10_safety",
                    "not_production_validated",
                    "forbidden_shortcut",
                }
            ),
            "production_direction_proven": production_direction_proven,
            "missing_requirement_names": goal.get("missing_requirement_names", []),
            "root_cause_short": (
                "5/10 is fixed-overhead sensitive; 20 has true-RC negative "
                "columns but batch impact is trajectory/context coupled; no "
                "production-validated addition-before selector exists."
            ),
        },
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# BPC_future Root Cause Failure Matrix 报告",
        "",
        "日期：2026-06-13",
        "",
        "## 目标",
        "",
        "把“做了很多为什么仍不行”拆成逐路线、逐证据的失败归因矩阵。",
        "本报告只读取现有 evidence ledger，不运行 BPC / pricing / Pulse / RMP。",
        "",
        "## 总结",
        "",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        f"route_count = {summary['summary']['route_count']}",
        f"blocked_or_ruled_out_route_count = {summary['summary']['blocked_or_ruled_out_route_count']}",
        f"production_direction_proven = {str(summary['summary']['production_direction_proven']).lower()}",
        "missing_requirement_names = "
        + ",".join(summary["summary"]["missing_requirement_names"]),
        "",
        "根因短句：",
        "",
        summary["summary"]["root_cause_short"],
        "",
        "## 路线矩阵",
        "",
        "| Route | Status | Why not enough | Key evidence |",
        "|---|---|---|---|",
    ]
    for route in summary["routes"]:
        evidence_bits = []
        for key, value in route["evidence"].items():
            evidence_bits.append(f"{key}={value}")
        lines.append(
            "| "
            + route["route"]
            + " | "
            + route["status"]
            + " | "
            + route["why_not_enough"]
            + " | "
            + "; ".join(evidence_bits)
            + " |"
        )
    lines.extend(
        [
            "",
            "## 结论",
            "",
            "当前已经能解释为什么各条直觉路线不够：",
            "",
            "- 继续扩大 worker / audit / probe 会伤害 5/10；",
            "- 继续找更多 true-RC negative columns 不能自动改善 20；",
            "- true-RC 阈值、task-set、sequence、简单 ML selector 都没有生产 holdout 证据；",
            "- 单 context replay 或局部 RMP movement 只能作为 calibration，不是 production proof。",
            "",
            "因此下一步仍是 calibration-only：扩展 no-certificate-effect exact-context replay，",
            "证明 addition-before selector 同时通过 context / instance / dataset holdout，",
            "之后才能进入 full BPC A/B。",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = build_summary()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    write_report(summary, args.report)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
