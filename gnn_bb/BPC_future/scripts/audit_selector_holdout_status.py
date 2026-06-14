#!/usr/bin/env python3
"""Audit selector holdout status for the BPC_future root-cause work.

This script is read-only. It summarizes existing selector/calibration summaries
and states whether the current addition-before selector evidence is production
ready.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_holdout_status_20260613"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260613_bpc_future_root_cause_selector_holdout_status_zh.md"
)

REPLAY_SELECTOR_SUMMARY = Path(
    "BPC_future/results/root_cause_replay_calibrated_selector_candidate_20260613/"
    "summary.json"
)
EXACT_SINGLE_GATE_SUMMARY = Path(
    "BPC_future/results/"
    "root_cause_counterfactual_replay_selector_gate_with_target002_pt03_20260613/"
    "summary.json"
)
EXACT_PAIR_GATE_SUMMARY = Path(
    "BPC_future/results/"
    "root_cause_counterfactual_replay_pair_selector_gate_with_target002_pt03_20260613/"
    "summary.json"
)
EXACT_MODEL_GATE_SUMMARY = Path(
    "BPC_future/results/"
    "root_cause_counterfactual_replay_model_selector_gate_with_target002_pt03_20260613/"
    "summary.json"
)
BROAD_MODEL_SUMMARY = Path(
    "BPC_future/results/root_cause_candidate_selector_models_20260613/summary.json"
)
TRAJECTORY_LADDER_SUMMARY = Path(
    "BPC_future/results/root_cause_trajectory_signal_ladder_20260613/summary.json"
)
SELECTOR_CONTEXT_COLLISION_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_context_collision_20260613/summary.json"
)
SELECTOR_LOCAL_FEATURE_DIRECTION_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_local_feature_direction_20260613/"
    "summary.json"
)
SELECTED20_REPEAT_AB_CSV = Path(
    "BPC_future/results/root_cause_calibrated_selector_selected20_repeat_ab_20260613/"
    "summary.csv"
)
EVIDENCE_LEDGER_SUMMARY = Path(
    "BPC_future/results/root_cause_evidence_ledger_20260613/summary.json"
)

STRICT_PRECISION_MIN = 0.75
STRICT_RECALL_MIN = 0.5


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(value)


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _passes_strict(metrics: dict[str, Any]) -> bool:
    precision = metrics.get("precision")
    recall = metrics.get("recall")
    return (
        precision is not None
        and recall is not None
        and float(precision) >= STRICT_PRECISION_MIN
        and float(recall) >= STRICT_RECALL_MIN
    )


def _model_pass_count(summary: dict[str, Any], holdout_key: str) -> int:
    models = summary.get(holdout_key, {}).get("models", {})
    return sum(1 for metrics in models.values() if _passes_strict(metrics))


def _best_model(summary: dict[str, Any], holdout_key: str) -> dict[str, Any]:
    models = summary.get(holdout_key, {}).get("models", {})
    if not models:
        return {}
    name, metrics = max(
        models.items(),
        key=lambda item: (
            -1.0 if item[1].get("precision") is None else float(item[1]["precision"]),
            -1.0 if item[1].get("recall") is None else float(item[1]["recall"]),
        ),
    )
    return {"model": name, **metrics, "passes_strict": _passes_strict(metrics)}


def _profile_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("profile") != "baseline"]


def _baseline_primal_by_run(rows: list[dict[str, str]]) -> dict[tuple[str, str], float]:
    result: dict[tuple[str, str], float] = {}
    for row in rows:
        if row.get("profile") != "baseline":
            continue
        primal = _as_float(row.get("primal"))
        if primal is None:
            continue
        result[(row.get("instance", ""), row.get("repeat_index", ""))] = primal
    return result


def build_summary() -> dict[str, Any]:
    replay = _read_json(REPLAY_SELECTOR_SUMMARY)
    exact_single = _read_json(EXACT_SINGLE_GATE_SUMMARY)
    exact_pair = _read_json(EXACT_PAIR_GATE_SUMMARY)
    exact_model = _read_json(EXACT_MODEL_GATE_SUMMARY)
    broad_model = _read_json(BROAD_MODEL_SUMMARY)
    ladder = _read_json(TRAJECTORY_LADDER_SUMMARY)
    context_collision = _read_json(SELECTOR_CONTEXT_COLLISION_SUMMARY)
    local_direction = _read_json(SELECTOR_LOCAL_FEATURE_DIRECTION_SUMMARY)
    selected20_rows = _read_csv(SELECTED20_REPEAT_AB_CSV)
    ledger = _read_json(EVIDENCE_LEDGER_SUMMARY)

    profile_rows = _profile_rows(selected20_rows)
    baseline_primal = _baseline_primal_by_run(selected20_rows)
    profile_pricing_states = sorted({row.get("pricing_state", "") for row in profile_rows})
    profile_statuses = sorted({row.get("status", "") for row in profile_rows})
    worker_added = [
        _as_int(row.get("pulse_worker_added_journeys")) for row in profile_rows
    ]
    primal_deltas: list[float] = []
    for row in profile_rows:
        primal = _as_float(row.get("primal"))
        baseline = baseline_primal.get(
            (row.get("instance", ""), row.get("repeat_index", ""))
        )
        if primal is not None and baseline is not None:
            primal_deltas.append(round(primal - baseline, 6))
    ladder_layers = ladder.get("layer_summary", {})
    pre_batch = ladder_layers.get("pre_batch", {}).get("leave_one_dataset", {})
    immediate = ladder_layers.get("immediate_addition", {}).get(
        "leave_one_dataset", {}
    )
    next_rmp = ladder_layers.get("next_rmp_movement", {}).get(
        "leave_one_dataset", {}
    )
    hindsight = ladder_layers.get("hindsight_trajectory", {}).get(
        "leave_one_dataset", {}
    )
    broad_dataset_pass_count = _model_pass_count(broad_model, "leave_one_dataset")
    broad_instance_pass_count = _model_pass_count(broad_model, "leave_one_instance")
    collision_groups = context_collision.get("group_summaries", {})
    collision_task_set = collision_groups.get("task_set", {})
    collision_task_sequence = collision_groups.get("task_sequence", {})
    collision_online_flags = collision_groups.get("online_flags", {})
    local_groups = local_direction.get("group_summaries", {})
    local_task_set_true_rc = (
        local_groups.get("task_set", {})
        .get("feature_stats", {})
        .get("true_reduced_cost", {})
        .get("direction_counts", {})
    )
    local_task_sequence_true_rc = (
        local_groups.get("task_sequence", {})
        .get("feature_stats", {})
        .get("true_reduced_cost", {})
        .get("direction_counts", {})
    )
    checks = {
        "exact_replay_candidate_exists": (
            replay.get("recommended_selector_candidate") is not None
            and _as_int(replay.get("row_count")) >= 280
        ),
        "exact_replay_candidate_has_errors": (
            _as_int(replay.get("recommended_selector_false_positive_count")) > 0
            and _as_int(replay.get("recommended_selector_false_negative_count")) > 0
        ),
        "exact_replay_selector_not_production": (
            replay.get("production_validation", {}).get(
                "production_validated_selector"
            )
            is False
        ),
        "pair_rule_not_all_holdout": exact_pair.get("checks", {}).get(
            "no_pair_rule_passes_all_holdout_gates"
        )
        is True,
        "broad_models_fail_dataset_holdout": broad_dataset_pass_count == 0,
        "context_collision_blocks_column_local_selector": (
            context_collision.get("all_checks_pass") is True
            and _as_int(collision_task_set.get("mixed_group_count")) == 6
            and _as_int(collision_task_sequence.get("mixed_group_count")) == 5
            and _as_int(collision_online_flags.get("mixed_row_count")) == 278
        ),
        "local_feature_direction_blocks_monotone_selector": (
            local_direction.get("all_checks_pass") is True
            and _as_int(local_task_set_true_rc.get("improved_lower_mean")) == 2
            and _as_int(local_task_set_true_rc.get("noop_lower_mean")) == 4
            and _as_int(local_task_sequence_true_rc.get("improved_lower_mean"))
            == 2
            and _as_int(local_task_sequence_true_rc.get("noop_lower_mean")) == 3
        ),
        "trajectory_pre_batch_precision_low": (
            (pre_batch.get("precision") or 0.0) < STRICT_PRECISION_MIN
        ),
        "trajectory_immediate_precision_low": (
            (immediate.get("precision") or 0.0) < STRICT_PRECISION_MIN
        ),
        "trajectory_next_rmp_precision_low": (
            (next_rmp.get("precision") or 0.0) < STRICT_PRECISION_MIN
        ),
        "selected20_repeat_ab_not_production": (
            profile_rows
            and set(profile_statuses) == {"TIME_LIMIT"}
            and "INCOMPLETE_LIMIT" in profile_pricing_states
        ),
        "goal_still_not_complete": (
            ledger.get("goal_status", {}).get("goal_complete") is False
        ),
    }
    return {
        "schema_version": "selector_holdout_status_v1",
        "sources": {
            "replay_selector_summary": str(REPLAY_SELECTOR_SUMMARY),
            "exact_single_gate_summary": str(EXACT_SINGLE_GATE_SUMMARY),
            "exact_pair_gate_summary": str(EXACT_PAIR_GATE_SUMMARY),
            "exact_model_gate_summary": str(EXACT_MODEL_GATE_SUMMARY),
            "broad_model_summary": str(BROAD_MODEL_SUMMARY),
            "trajectory_ladder_summary": str(TRAJECTORY_LADDER_SUMMARY),
            "selector_context_collision_summary": str(
                SELECTOR_CONTEXT_COLLISION_SUMMARY
            ),
            "selector_local_feature_direction_summary": str(
                SELECTOR_LOCAL_FEATURE_DIRECTION_SUMMARY
            ),
            "selected20_repeat_ab_csv": str(SELECTED20_REPEAT_AB_CSV),
            "evidence_ledger": str(EVIDENCE_LEDGER_SUMMARY),
        },
        "exact_replay_selector": {
            "row_count": _as_int(replay.get("row_count")),
            "label_counts": replay.get("label_counts", {}),
            "recommended_selector_candidate": replay.get(
                "recommended_selector_candidate"
            ),
            "false_positive_count": _as_int(
                replay.get("recommended_selector_false_positive_count")
            ),
            "false_negative_count": _as_int(
                replay.get("recommended_selector_false_negative_count")
            ),
            "passing_features_all_holdouts": exact_single.get(
                "passing_features_all_holdouts", []
            ),
            "single_gate_all_checks_pass": exact_single.get("all_checks_pass"),
            "pair_gate_all_checks_pass": exact_pair.get("all_checks_pass"),
            "model_gate_all_checks_pass": exact_model.get("all_checks_pass"),
            "production_validated_selector": replay.get(
                "production_validation", {}
            ).get("production_validated_selector"),
        },
        "broad_candidate_selector": {
            "row_count": _as_int(broad_model.get("rows")),
            "label_counts": broad_model.get("label_counts", {}),
            "dataset_holdout_pass_count": broad_dataset_pass_count,
            "instance_holdout_pass_count": broad_instance_pass_count,
            "best_dataset_model": _best_model(broad_model, "leave_one_dataset"),
            "best_instance_model": _best_model(broad_model, "leave_one_instance"),
        },
        "column_local_selector_blockers": {
            "task_set_mixed_group_count": _as_int(
                collision_task_set.get("mixed_group_count")
            ),
            "task_sequence_mixed_group_count": _as_int(
                collision_task_sequence.get("mixed_group_count")
            ),
            "online_flags_mixed_row_count": _as_int(
                collision_online_flags.get("mixed_row_count")
            ),
            "task_set_true_rc_direction_counts": dict(local_task_set_true_rc),
            "task_sequence_true_rc_direction_counts": dict(
                local_task_sequence_true_rc
            ),
        },
        "trajectory_ladder": {
            "pre_batch_leave_one_dataset": pre_batch,
            "immediate_addition_leave_one_dataset": immediate,
            "next_rmp_movement_leave_one_dataset": next_rmp,
            "hindsight_trajectory_leave_one_dataset": hindsight,
        },
        "selected20_repeat_ab": {
            "profile_row_count": len(profile_rows),
            "profile_statuses": profile_statuses,
            "profile_pricing_states": profile_pricing_states,
            "worker_added_journeys": worker_added,
            "primal_deltas_vs_baseline": primal_deltas,
        },
        "status": {
            "exact_replay_candidate": "available_with_errors",
            "selector_holdout": "not_production_validated",
            "production_candidate_ab": "blocked",
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "Selector evidence has useful calibration signal, but it is not a "
            "production selector: the recommended exact-replay threshold still has "
            "false positives and false negatives, broader candidate/trajectory "
            "holdouts remain weak, column-local selectors have context collisions "
            "and direction flips, and selected 20 repeat A/B has not proven speedup."
        ),
    }


def _write_report(summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    exact = summary["exact_replay_selector"]
    broad = summary["broad_candidate_selector"]
    blockers = summary["column_local_selector_blockers"]
    ladder = summary["trajectory_ladder"]
    selected20 = summary["selected20_repeat_ab"]
    text = f"""# BPC_future Selector Holdout Status 审计

日期：2026-06-13

## 目标

本报告只审计 selector 是否已经具备 production 资格。它不运行 BPC，不改变求解路径，
不更新 certificate，也不把任何 selector 上线。

## 结论

```text
exact_replay_candidate = {summary['status']['exact_replay_candidate']}
selector_holdout = {summary['status']['selector_holdout']}
production_candidate_ab = {summary['status']['production_candidate_ab']}
```

解释：

- exact replay 中已有 calibrated selector candidate；
- 该 candidate 仍有 false positive / false negative；
- broader candidate / trajectory holdout 仍不足以 production；
- selected 20 repeat A/B 没有证明 wall-time / status / pricing-state 改善。

## Exact Replay Selector

```text
row_count = {exact['row_count']}
label_counts = {exact['label_counts']}
recommended_selector_candidate = {exact['recommended_selector_candidate']}
false_positive_count = {exact['false_positive_count']}
false_negative_count = {exact['false_negative_count']}
passing_features_all_holdouts = {exact['passing_features_all_holdouts']}
production_validated_selector = {exact['production_validated_selector']}
```

## Broader Candidate Selector

```text
row_count = {broad['row_count']}
label_counts = {broad['label_counts']}
dataset_holdout_pass_count = {broad['dataset_holdout_pass_count']}
instance_holdout_pass_count = {broad['instance_holdout_pass_count']}
best_dataset_model = {broad['best_dataset_model'].get('model')}
best_dataset_precision = {broad['best_dataset_model'].get('precision')}
best_dataset_recall = {broad['best_dataset_model'].get('recall')}
```

## Column-local Selector Blockers

```text
task_set_mixed_group_count = {blockers['task_set_mixed_group_count']}
task_sequence_mixed_group_count = {blockers['task_sequence_mixed_group_count']}
online_flags_mixed_row_count = {blockers['online_flags_mixed_row_count']}
task_set_true_rc_direction_counts = {blockers['task_set_true_rc_direction_counts']}
task_sequence_true_rc_direction_counts = {blockers['task_sequence_true_rc_direction_counts']}
```

这些 blockers 表示：同一 task-set / sequence / 在线 flags 在不同 context 下会混合
improved 与 noop；在 mixed groups 内，true-RC 更负的方向也会反转。因此不能用
列局部形态或简单单调 true-RC/cost 规则作为 production selector。

## Trajectory Signal Ladder

```text
pre_batch_lod_precision = {ladder['pre_batch_leave_one_dataset'].get('precision')}
immediate_addition_lod_precision = {ladder['immediate_addition_leave_one_dataset'].get('precision')}
next_rmp_movement_lod_precision = {ladder['next_rmp_movement_leave_one_dataset'].get('precision')}
hindsight_trajectory_lod_precision = {ladder['hindsight_trajectory_leave_one_dataset'].get('precision')}
```

## Selected 20 Repeat A/B

```text
profile_row_count = {selected20['profile_row_count']}
profile_statuses = {selected20['profile_statuses']}
profile_pricing_states = {selected20['profile_pricing_states']}
worker_added_journeys = {selected20['worker_added_journeys']}
primal_deltas_vs_baseline = {selected20['primal_deltas_vs_baseline']}
```

## 当前边界

```text
production_validated_selector = false
has_20_walltime_speedup_evidence = false
```

下一步仍只能是 calibration-only：selector 必须只使用 addition-before features，
并同时通过 context / instance / dataset holdout，之后才允许 full BPC A/B。
"""
    report_path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = build_summary()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(summary, Path(args.report_path))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
