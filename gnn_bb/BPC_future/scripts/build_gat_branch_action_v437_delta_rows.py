#!/usr/bin/env python3
"""Build v437 branch/action delta rows from the v436 selection-gate smoke.

This helper turns completed branch-score opt-in smoke evidence into
``branch_counterfactual_delta_rows.jsonl`` rows compatible with
``build_gat_branch_action_sanity_dataset.py``.  It only reads finished CSV,
analysis JSON, and JSONL logs.  It does not run BPC, pricing, RMP, or produce
official bounds/certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.scripts.export_gat_branch_action_score_map import (
    _branch_feature_vector,
    _candidate_union,
    _pair,
    _rank_map,
)


DEFAULT_ANALYSIS = Path(
    "BPC_future/results/20260626_v436_branch_score_selection_gate062_smoke20_topscore12/"
    "analysis_summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/journey_branch_counterfactual_delta_v437_from_v436_selection_gate062_20260626"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260626_bpc_future_journey_branch_counterfactual_delta_v437_from_v436_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def _log_path(run_dir: Path, instance: str) -> Path:
    return run_dir / "logs" / f"{instance}.jsonl"


def _first_branch_event(run_dir: Path, instance: str) -> dict[str, Any] | None:
    for record in _iter_jsonl(_log_path(run_dir, instance)):
        if record.get("event") == "journey_branch_candidates":
            return record
    return None


def _pair_tuple(value: Any) -> tuple[int, int] | None:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            left = int(value[0])
            right = int(value[1])
        except (TypeError, ValueError):
            return None
        if left > 0 and right > 0 and left != right:
            return tuple(sorted((left, right)))
    return None


def _candidate_for_pair(event: dict[str, Any], pair: tuple[int, int]) -> dict[str, Any] | None:
    for candidate in _candidate_union(event):
        if _pair(candidate) == pair:
            return candidate
    selected = event.get("selected")
    if isinstance(selected, dict) and _pair(selected) == pair:
        return selected
    return None


def _float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _rank(value: int | None) -> int | None:
    return None if value is None else int(value)


def _counterfactual_type(
    item: dict[str, Any],
    *,
    min_wall_improvement: float,
) -> tuple[str, dict[str, float], bool, float]:
    baseline_status = str(item.get("baseline_status") or "")
    alternative_status = str(item.get("status") or "")
    baseline_wall = _float(item.get("baseline_wall"), default=600.0)
    alternative_wall = _float(item.get("wall"), default=600.0)
    gain = baseline_wall - alternative_wall
    timeout_resolved = bool(baseline_status != "OPTIMAL" and alternative_status == "OPTIMAL")
    timeout_regression = bool(baseline_status == "OPTIMAL" and alternative_status != "OPTIMAL")
    wall_improved = bool(
        baseline_status == "OPTIMAL"
        and alternative_status == "OPTIMAL"
        and gain >= float(min_wall_improvement)
    )
    wall_regression = bool(
        baseline_status == "OPTIMAL"
        and alternative_status == "OPTIMAL"
        and gain <= -float(min_wall_improvement)
    )
    no_effect_negative = bool(
        item.get("root_changed")
        and alternative_status != "OPTIMAL"
        and not timeout_regression
    )
    if timeout_resolved or wall_improved:
        label_type = "strong_positive"
    elif timeout_regression or wall_regression:
        label_type = "regression"
    elif no_effect_negative:
        label_type = "changed_timeout_no_effect_hard_negative"
    else:
        label_type = "observed_neutral"
    labels = {
        "y_counterfactual_wall_improved": 1.0 if wall_improved else 0.0,
        "y_counterfactual_timeout_resolved": 1.0 if timeout_resolved else 0.0,
        "y_counterfactual_regression": 1.0
        if timeout_regression or wall_regression
        else 0.0,
        "y_counterfactual_timeout_regression": 1.0 if timeout_regression else 0.0,
        "y_counterfactual_no_effect_hard_negative": 1.0 if no_effect_negative else 0.0,
    }
    right_censored = bool(label_type == "observed_neutral")
    return label_type, labels, right_censored, gain


def _branch_labels(item: dict[str, Any], candidate: dict[str, Any]) -> dict[str, float]:
    status = str(item.get("status") or "")
    timeout = status != "OPTIMAL"
    return {
        "y_tail_improved": 1.0 if status == "OPTIMAL" else 0.0,
        "y_completion_bound_tail": 1.0 if timeout else 0.0,
        "y_early_branch_continues": 0.0,
        "y_negative_chain_continues": 1.0 if timeout else 0.0,
        "y_active_touch": 1.0,
        "y_inactive_only": 0.0,
        "y_child_negative_pricing_events": _float(item.get("exact_pricing_calls"), default=0.0),
        "y_child_exact_pricing_events": _float(item.get("exact_pricing_calls"), default=0.0),
        "y_child_completion_bound_retries": 1.0 if timeout else 0.0,
        "y_child_early_branch_triggers": 0.0,
        "y_child_fathom_events": _float(item.get("fathom_events"), default=0.0),
        "y_child_max_safe_bound_gain": 0.0,
        "y_child_max_corrected_bound_gain": 0.0,
        "pool_total_child_width": _float(candidate.get("pool_total_child_width"), default=0.0),
        "pool_balance_gap": _float(candidate.get("pool_balance_gap"), default=0.0),
        "pool_max_child_width": _float(candidate.get("pool_max_child_width"), default=0.0),
    }


def _candidate_raw_row(
    *,
    event: dict[str, Any] | None,
    candidate: dict[str, Any] | None,
    rank_in_top: int | None = None,
    rank_in_priority_top: int | None = None,
    feature_vector: list[float] | None = None,
) -> dict[str, Any]:
    event_payload = event if isinstance(event, dict) else {}
    candidate_payload = candidate if isinstance(candidate, dict) else {}
    return {
        "branch_feature_vector": feature_vector,
        "branch_time": _float(event_payload.get("time"), default=0.0),
        "candidate_count": event_payload.get("candidate_count"),
        "eligible_count": event_payload.get("eligible_count"),
        "branch_rank_in_top": rank_in_top,
        "branch_rank_in_priority_top": rank_in_priority_top,
        "selected_score": candidate_payload.get("branch_score"),
        "selected_score_source": candidate_payload.get("branch_score_source"),
        "branch_score_selection_gate_reason": event_payload.get("branch_score_selection_gate_reason"),
        "branch_score_selection_gate_passed": event_payload.get("branch_score_selection_gate_passed"),
        "phased_testing_stage": candidate_payload.get("phased_testing_stage"),
        "phased_testing_decision": candidate_payload.get("phased_testing_decision"),
        "phased_testing_reason": candidate_payload.get("phased_testing_reason"),
        "phased_testing_elimination_reason": candidate_payload.get("phased_testing_elimination_reason"),
        "phased_testing_phase0_passed": candidate_payload.get("phased_testing_phase0_passed"),
        "phased_testing_phase1_lp_complete": candidate_payload.get("phased_testing_phase1_lp_complete"),
        "phased_testing_phase2_heuristic_complete": candidate_payload.get(
            "phased_testing_phase2_heuristic_complete"
        ),
        "phase1_min_child_lp_gain": candidate_payload.get("phase1_min_child_lp_gain"),
        "phase1_child_lp_gain_product": candidate_payload.get("phase1_child_lp_gain_product"),
        "phase1_child_width_balance": candidate_payload.get("phase1_child_width_balance"),
        "phase1_wall_time": candidate_payload.get("phase1_wall_time"),
        "phase1_dynamic_k_probe_count": candidate_payload.get("phase1_dynamic_k_probe_count"),
        "phase2_negative_child_count": candidate_payload.get("phase2_negative_child_count"),
        "phase2_negative_journey_count": candidate_payload.get("phase2_negative_journey_count"),
        "phase2_negative_journey_balance_gap": candidate_payload.get(
            "phase2_negative_journey_balance_gap"
        ),
        "phase2_best_reduced_cost": candidate_payload.get("phase2_best_reduced_cost"),
        "phase2_worst_negative_severity": candidate_payload.get("phase2_worst_negative_severity"),
        "phase2_same_child_negative_severity": candidate_payload.get(
            "phase2_same_child_negative_severity"
        ),
        "phase2_separate_child_negative_severity": candidate_payload.get(
            "phase2_separate_child_negative_severity"
        ),
        "phase2_negative_severity_sum": candidate_payload.get("phase2_negative_severity_sum"),
        "phase2_negative_severity_gap": candidate_payload.get("phase2_negative_severity_gap"),
        "phase2_negative_severity_balance_ratio": candidate_payload.get(
            "phase2_negative_severity_balance_ratio"
        ),
        "phase2_negative_child_presence_balance_gap": candidate_payload.get(
            "phase2_negative_child_presence_balance_gap"
        ),
        "phase2_child_wall_time_balance_gap": candidate_payload.get("phase2_child_wall_time_balance_gap"),
        "phase2_child_status_mismatch": candidate_payload.get("phase2_child_status_mismatch"),
        "phase2_wall_time": candidate_payload.get("phase2_wall_time"),
        "phase2_dynamic_k_probe_count": candidate_payload.get("phase2_dynamic_k_probe_count"),
        "pool_total_child_width": candidate_payload.get("pool_total_child_width"),
        "pool_balance_gap": candidate_payload.get("pool_balance_gap"),
        "pool_max_child_width": candidate_payload.get("pool_max_child_width"),
    }


def _delta_row(
    *,
    item: dict[str, Any],
    event: dict[str, Any],
    candidate: dict[str, Any],
    min_wall_improvement: float,
) -> dict[str, Any] | None:
    baseline_pair = _pair_tuple(item.get("root_baseline_pair"))
    alternative_pair = _pair_tuple(item.get("root_selected_pair"))
    if baseline_pair is None or alternative_pair is None:
        return None
    top_rank = _rank_map(event.get("top"))
    priority_rank = _rank_map(event.get("priority_top"))
    key = f"{alternative_pair[0]},{alternative_pair[1]}"
    rank_in_top = _rank(top_rank.get(key))
    rank_in_priority_top = _rank(priority_rank.get(key))
    baseline_key = f"{baseline_pair[0]},{baseline_pair[1]}"
    baseline_rank_in_top = _rank(top_rank.get(baseline_key))
    baseline_rank_in_priority_top = _rank(priority_rank.get(baseline_key))
    baseline_candidate = _candidate_for_pair(event, baseline_pair) or {}
    label_type, labels, right_censored, gain = _counterfactual_type(
        item,
        min_wall_improvement=min_wall_improvement,
    )
    if label_type == "observed_neutral":
        return None
    branch_labels = _branch_labels(item, candidate)
    feature_vector = _branch_feature_vector(
        event,
        candidate,
        rank_in_top=rank_in_top,
        rank_in_priority_top=rank_in_priority_top,
    )
    baseline_feature_vector = (
        _branch_feature_vector(
            event,
            baseline_candidate,
            rank_in_top=baseline_rank_in_top,
            rank_in_priority_top=baseline_rank_in_priority_top,
        )
        if baseline_candidate
        else []
    )
    baseline_wall = _float(item.get("baseline_wall"), default=600.0)
    alternative_wall = _float(item.get("wall"), default=600.0)
    baseline_raw_row = _candidate_raw_row(
        event=event,
        candidate=baseline_candidate,
        rank_in_top=baseline_rank_in_top,
        rank_in_priority_top=baseline_rank_in_priority_top,
        feature_vector=baseline_feature_vector,
    )
    baseline_raw_row.update(
        {
            "status": item.get("baseline_status"),
            "wall_time": baseline_wall,
            "solving_time": baseline_wall,
            "node_count": item.get("max_node"),
            "exact_pricing_calls": None,
        }
    )
    alternative_raw_row = _candidate_raw_row(
        event=event,
        candidate=candidate,
        rank_in_top=rank_in_top,
        rank_in_priority_top=rank_in_priority_top,
        feature_vector=feature_vector,
    )
    alternative_raw_row.update(
        {
            "status": item.get("status"),
            "wall_time": alternative_wall,
            "solving_time": alternative_wall,
            "node_count": item.get("max_node"),
            "exact_pricing_calls": item.get("exact_pricing_calls"),
            "selected_score": item.get("root_score"),
            "selected_score_source": item.get("root_score_source"),
            "branch_score_selection_gate_reason": item.get("root_gate_reason"),
            "branch_score_selection_gate_passed": item.get("root_gate_passed"),
        }
    )
    return {
        "schema_version": "journey_branch_counterfactual_delta_v437_from_selection_gate",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "experiment": "v437_from_v436_selection_gate062",
        "instance": str(item.get("instance") or ""),
        "node_id": int(event.get("node_id") or 0),
        "depth": int(event.get("depth") or 0),
        "baseline_pair": list(baseline_pair),
        "alternative_pair": list(alternative_pair),
        "alternative_forced_pair_matched": True,
        "selected_pair_changed": bool(item.get("root_changed")),
        "baseline_status": item.get("baseline_status"),
        "alternative_status": item.get("status"),
        "both_optimal": bool(item.get("baseline_status") == "OPTIMAL" and item.get("status") == "OPTIMAL"),
        "both_nonoptimal": bool(item.get("baseline_status") != "OPTIMAL" and item.get("status") != "OPTIMAL"),
        "timeout_resolved": bool(item.get("baseline_status") != "OPTIMAL" and item.get("status") == "OPTIMAL"),
        "timeout_regression": bool(item.get("baseline_status") == "OPTIMAL" and item.get("status") != "OPTIMAL"),
        "right_censored_counterfactual": right_censored,
        "usable_for_counterfactual_training": not right_censored,
        "counterfactual_label_type": label_type,
        "hard_negative_loss_weight": 1.0,
        "baseline_wall_time": baseline_wall,
        "alternative_wall_time": alternative_wall,
        "baseline_solving_time": baseline_wall,
        "alternative_solving_time": alternative_wall,
        "baseline_node_count": item.get("max_node"),
        "alternative_node_count": item.get("max_node"),
        "baseline_exact_pricing_calls": None,
        "alternative_exact_pricing_calls": None,
        "child_proof_cpu": alternative_wall,
        "child_time_to_certificate": alternative_wall,
        "deltas": {
            "wall_time_delta": round(alternative_wall - baseline_wall, 9),
            "wall_time_gain": round(gain, 9),
            "node_count_delta": 0.0,
        },
        "labels": labels,
        "alternative_branch_labels": branch_labels,
        "baseline_raw_row": baseline_raw_row,
        "alternative_raw_row": alternative_raw_row,
    }


def build_v437_delta_rows(
    *,
    analysis: Path,
    output_dir: Path,
    report: Path,
    min_wall_improvement: float = 30.0,
) -> dict[str, Any]:
    payload = _read_json(analysis)
    run_dir = Path(str(payload.get("run_dir") or analysis.parent))
    rows: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    for item in payload.get("items") or []:
        if not isinstance(item, dict):
            continue
        if not bool(item.get("root_changed")):
            skipped["root_not_changed"] += 1
            continue
        instance = str(item.get("instance") or "")
        event = _first_branch_event(run_dir, instance)
        if event is None:
            skipped["missing_branch_candidate_event"] += 1
            continue
        pair = _pair_tuple(item.get("root_selected_pair"))
        if pair is None:
            skipped["missing_selected_pair"] += 1
            continue
        candidate = _candidate_for_pair(event, pair)
        if candidate is None:
            skipped["missing_selected_candidate"] += 1
            continue
        row = _delta_row(
            item=item,
            event=event,
            candidate=candidate,
            min_wall_improvement=min_wall_improvement,
        )
        if row is None:
            skipped["observed_neutral"] += 1
            continue
        rows.append(row)

    label_counts = Counter(str(row.get("counterfactual_label_type") or "") for row in rows)
    status_pairs = Counter(
        f"{row.get('baseline_status')}->{row.get('alternative_status')}" for row in rows
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "branch_counterfactual_delta_rows.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    summary = {
        "schema_version": "v437_from_v436_selection_gate_delta_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "analysis": str(analysis),
        "run_dir": str(run_dir),
        "output_dir": str(output_dir),
        "min_wall_improvement": float(min_wall_improvement),
        "row_count": len(rows),
        "label_type_counts": dict(sorted(label_counts.items())),
        "status_pair_counts": dict(sorted(status_pairs.items())),
        "skipped_counts": dict(sorted(skipped.items())),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(report: Path, summary: dict[str, Any]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Branch Counterfactual Delta v437 from v436",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把 v436 selection-gate smoke 的真实整实例结果转成 branch/action 训练 row。该脚本只读完成的结果和日志，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"analysis = {summary['analysis']}",
        f"output_dir = {summary['output_dir']}",
        f"row_count = {summary['row_count']}",
        f"label_type_counts = {summary['label_type_counts']}",
        f"status_pair_counts = {summary['status_pair_counts']}",
        f"skipped_counts = {summary['skipped_counts']}",
        "production_ready = false",
        "official_bound_effect = false",
        "certificate_effect = false",
        "```",
        "",
        "## 边界",
        "",
        "这些 row 只用于训练 branch 候选排序和 gate；不能作为剪枝依据，不能替代 exact pricing closure。",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, default=DEFAULT_ANALYSIS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-wall-improvement", type=float, default=30.0)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    summary = build_v437_delta_rows(
        analysis=args.analysis,
        output_dir=args.output_dir,
        report=args.report,
        min_wall_improvement=float(args.min_wall_improvement),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if int(summary["row_count"]) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
