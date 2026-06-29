#!/usr/bin/env python3
"""Build branch delta rows from forced-pair full replay runs.

This script is offline and diagnostic-only.  It reads completed full replay
``results.csv`` files and JSONL logs, then emits two classes of labels:

* strict full-replay wall-time labels when both runs prove OPTIMAL with matching
  objective values;
* weak gap/fathom labels for right-censored runs where neither side proved
  optimal.

The rows are training/audit evidence only. They must not be used as official
bounds, certificates, or pruning evidence.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import date
import json
from pathlib import Path
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.scripts.export_gat_branch_action_score_map import (  # noqa: E402
    _branch_feature_vector,
    _candidate_union,
    _pair,
    _rank_map,
)


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "journey_branch_counterfactual_delta_v637_seed61311_root_full_replay_weak_20260628"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260628_bpc_future_journey_branch_counterfactual_delta_v637_seed61311_root_full_replay_weak_zh.md"
)


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


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _pair_tuple(value: Any) -> tuple[int, int] | None:
    if isinstance(value, str):
        pieces = value.replace("[", "").replace("]", "").replace(" ", "").split(",")
        value = pieces
    if isinstance(value, (list, tuple)) and len(value) == 2:
        left = _int(value[0], -1)
        right = _int(value[1], -1)
        if left > 0 and right > 0 and left != right:
            return tuple(sorted((left, right)))
    return None


def _read_csv_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = [dict(row) for row in csv.DictReader(fh)]
    return rows[0] if rows else {}


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


def _first_event(log_path: Path, event: str, *, node_id: int, depth: int) -> dict[str, Any] | None:
    fallback: dict[str, Any] | None = None
    for record in _iter_jsonl(log_path):
        if record.get("event") != event:
            continue
        if fallback is None:
            fallback = record
        if _int(record.get("node_id"), -1) == int(node_id) and _int(record.get("depth"), -1) == int(depth):
            return record
    return fallback


def _candidate_for_pair(event: dict[str, Any] | None, pair: tuple[int, int]) -> dict[str, Any]:
    if not isinstance(event, dict):
        return {}
    for candidate in _candidate_union(event):
        if _pair(candidate) == pair:
            return candidate
    selected = event.get("selected")
    if isinstance(selected, dict) and _pair(selected) == pair:
        return selected
    return {}


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
        "branch_time": _float(event_payload.get("time")),
        "candidate_count": event_payload.get("candidate_count"),
        "eligible_count": event_payload.get("eligible_count"),
        "score_available_count": event_payload.get("score_available_count"),
        "score_missing_count": event_payload.get("score_missing_count"),
        "branch_rank_in_top": rank_in_top,
        "branch_rank_in_priority_top": rank_in_priority_top,
        "selected_score": candidate_payload.get("branch_score"),
        "selected_score_source": candidate_payload.get("branch_score_source"),
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


def _log_stats(path: Path) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for record in _iter_jsonl(path):
        event = str(record.get("event") or "")
        counts[event] += 1
        if event == "journey_exact_pricing_completion_bound_retry":
            retry_class = str(record.get("retry_class") or "completion_bound_final_judge")
            counts[f"retry_class:{retry_class}"] += 1
        elif event == "journey_exact_pricing_retry":
            retry_class = str(record.get("retry_class") or "ordinary_incomplete_no_column")
            counts[f"retry_class:{retry_class}"] += 1
    return {
        "branch_count": int(counts.get("journey_branch", 0)),
        "fathom_count": int(counts.get("journey_fathom", 0)),
        "column_addition_count": int(counts.get("journey_column_addition", 0)),
        "pool_integer_count": int(counts.get("journey_pool_integer", 0)),
        "incumbent_count": int(counts.get("incumbent", 0)),
        "completion_bound_final_judge_retry_count": int(
            counts.get("retry_class:completion_bound_final_judge", 0)
        ),
        "ordinary_incomplete_no_column_retry_count": int(
            counts.get("retry_class:ordinary_incomplete_no_column", 0)
        ),
    }


def _gap_available(row: dict[str, str]) -> bool:
    if str(row.get("gap_available") or "").strip().lower() in {"1", "true", "yes"}:
        return True
    return row.get("gap") not in (None, "")


def _label_type(
    *,
    both_optimal: bool,
    objective_match: bool,
    wall_time_gain: float,
    gap_improvement: float,
    primal_improvement: float,
    fathom_gain: int,
    min_wall_improvement: float,
    min_gap_improvement: float,
    min_primal_improvement: float,
) -> str:
    if both_optimal and objective_match:
        if wall_time_gain >= float(min_wall_improvement):
            return "strong_positive"
        if wall_time_gain <= -float(min_wall_improvement):
            return "regression"
        return "full_replay_neutral"
    if gap_improvement <= -float(min_gap_improvement) or primal_improvement <= -float(min_primal_improvement):
        return "weak_gap_regression"
    gap_good = gap_improvement >= float(min_gap_improvement)
    primal_good = primal_improvement >= float(min_primal_improvement)
    if (gap_good or primal_good) and fathom_gain > 0:
        return "weak_gap_fathom_positive"
    if gap_good or primal_good:
        return "weak_gap_positive"
    return "right_censored_neutral"


def _make_row(
    *,
    experiment: str,
    baseline_results: Path,
    baseline_log: Path,
    baseline_pair: tuple[int, int],
    alternative_results: Path,
    alternative_log: Path,
    alternative_pair: tuple[int, int],
    node_id: int,
    depth: int,
    wall_cap: float,
    min_wall_improvement: float,
    min_gap_improvement: float,
    min_primal_improvement: float,
    objective_tolerance: float,
) -> tuple[dict[str, Any] | None, str | None]:
    baseline_row = _read_csv_one(baseline_results)
    alternative_row = _read_csv_one(alternative_results)
    if not baseline_row:
        return None, "empty_baseline_results"
    if not alternative_row:
        return None, "empty_alternative_results"

    baseline_event = _first_event(baseline_log, "journey_branch_candidates", node_id=node_id, depth=depth)
    alt_event = _first_event(alternative_log, "journey_branch_candidates", node_id=node_id, depth=depth)
    alt_branch = _first_event(alternative_log, "journey_branch", node_id=node_id, depth=depth)
    alt_selected_pair = _pair_tuple(alt_event.get("selected_pair")) if isinstance(alt_event, dict) else None
    branch_selected_pair = _pair_tuple(alt_branch.get("selected_pair")) if isinstance(alt_branch, dict) else None
    forced_matched = bool(
        alt_selected_pair == alternative_pair
        and (branch_selected_pair is None or branch_selected_pair == alternative_pair)
    )
    if not forced_matched:
        return None, "alternative_forced_pair_not_matched"

    rank_top = _rank_map(alt_event.get("top")) if isinstance(alt_event, dict) else {}
    rank_priority = _rank_map(alt_event.get("priority_top")) if isinstance(alt_event, dict) else {}
    key = f"{alternative_pair[0]},{alternative_pair[1]}"
    rank_in_top = rank_top.get(key)
    rank_in_priority_top = rank_priority.get(key)
    candidate = _candidate_for_pair(alt_event, alternative_pair)
    baseline_rank_top = _rank_map(baseline_event.get("top")) if isinstance(baseline_event, dict) else {}
    baseline_rank_priority = (
        _rank_map(baseline_event.get("priority_top")) if isinstance(baseline_event, dict) else {}
    )
    baseline_key = f"{baseline_pair[0]},{baseline_pair[1]}"
    baseline_rank_in_top = baseline_rank_top.get(baseline_key)
    baseline_rank_in_priority_top = baseline_rank_priority.get(baseline_key)
    baseline_candidate = _candidate_for_pair(baseline_event, baseline_pair)
    baseline_feature_vector = (
        _branch_feature_vector(
            baseline_event or {},
            baseline_candidate,
            rank_in_top=baseline_rank_in_top,
            rank_in_priority_top=baseline_rank_in_priority_top,
        )
        if baseline_candidate
        else []
    )
    feature_vector = (
        _branch_feature_vector(alt_event or {}, candidate, rank_in_top=rank_in_top, rank_in_priority_top=rank_in_priority_top)
        if candidate
        else []
    )

    baseline_stats = _log_stats(baseline_log)
    alternative_stats = _log_stats(alternative_log)
    baseline_status = str(baseline_row.get("status") or "")
    alternative_status = str(alternative_row.get("status") or "")
    baseline_wall = min(_float(baseline_row.get("wall_time"), wall_cap), float(wall_cap))
    alternative_wall = min(_float(alternative_row.get("wall_time"), wall_cap), float(wall_cap))
    baseline_gap = _float(baseline_row.get("gap"))
    alternative_gap = _float(alternative_row.get("gap"))
    baseline_primal = _float(baseline_row.get("best_primal_bound") or baseline_row.get("primal_bound"))
    alternative_primal = _float(alternative_row.get("best_primal_bound") or alternative_row.get("primal_bound"))
    baseline_dual = _float(baseline_row.get("best_dual_bound") or baseline_row.get("dual_bound"))
    alternative_dual = _float(alternative_row.get("best_dual_bound") or alternative_row.get("dual_bound"))
    gap_improvement = baseline_gap - alternative_gap
    primal_improvement = baseline_primal - alternative_primal
    dual_bound_gain = alternative_dual - baseline_dual
    fathom_gain = int(alternative_stats["fathom_count"] - baseline_stats["fathom_count"])
    wall_time_gain = baseline_wall - alternative_wall
    retry_gain = int(
        baseline_stats["completion_bound_final_judge_retry_count"]
        - alternative_stats["completion_bound_final_judge_retry_count"]
    )
    both_optimal = bool(baseline_status == "OPTIMAL" and alternative_status == "OPTIMAL")
    objective_match = bool(
        abs(float(baseline_primal) - float(alternative_primal)) <= float(objective_tolerance)
        and abs(float(baseline_dual) - float(alternative_dual)) <= float(objective_tolerance)
    )
    label_type = _label_type(
        both_optimal=both_optimal,
        objective_match=objective_match,
        wall_time_gain=wall_time_gain,
        gap_improvement=gap_improvement,
        primal_improvement=primal_improvement,
        fathom_gain=fathom_gain,
        min_wall_improvement=min_wall_improvement,
        min_gap_improvement=min_gap_improvement,
        min_primal_improvement=min_primal_improvement,
    )
    weak_positive = label_type in {"weak_gap_positive", "weak_gap_fathom_positive"}
    strong_positive = label_type == "strong_positive"
    regression = label_type in {"regression", "weak_gap_regression"}
    baseline_raw_row = _candidate_raw_row(
        event=baseline_event,
        candidate=baseline_candidate,
        rank_in_top=baseline_rank_in_top,
        rank_in_priority_top=baseline_rank_in_priority_top,
        feature_vector=baseline_feature_vector,
    )
    baseline_raw_row.update(
        {
            "status": baseline_status,
            "wall_time": baseline_wall,
            "node_count": _int(baseline_row.get("node_count")),
            "branch_count": baseline_stats["branch_count"],
            "fathom_count": baseline_stats["fathom_count"],
            "completion_bound_final_judge_retry_count": baseline_stats[
                "completion_bound_final_judge_retry_count"
            ],
            "ordinary_incomplete_no_column_retry_count": baseline_stats[
                "ordinary_incomplete_no_column_retry_count"
            ],
        }
    )
    alternative_raw_row = _candidate_raw_row(
        event=alt_event,
        candidate=candidate,
        rank_in_top=rank_in_top,
        rank_in_priority_top=rank_in_priority_top,
        feature_vector=feature_vector,
    )
    alternative_raw_row.update(
        {
            "status": alternative_status,
            "wall_time": alternative_wall,
            "node_count": _int(alternative_row.get("node_count")),
            "branch_count": alternative_stats["branch_count"],
            "fathom_count": alternative_stats["fathom_count"],
            "completion_bound_final_judge_retry_count": alternative_stats[
                "completion_bound_final_judge_retry_count"
            ],
            "ordinary_incomplete_no_column_retry_count": alternative_stats[
                "ordinary_incomplete_no_column_retry_count"
            ],
        }
    )

    return {
        "schema_version": "journey_branch_counterfactual_delta_full_replay_gap_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "experiment": experiment,
        "instance": str(alternative_row.get("instance") or baseline_row.get("instance") or ""),
        "node_id": int(node_id),
        "depth": int(depth),
        "baseline_pair": list(baseline_pair),
        "alternative_pair": list(alternative_pair),
        "alternative_forced_pair_matched": True,
        "selected_pair_changed": bool(baseline_pair != alternative_pair),
        "baseline_status": baseline_status,
        "alternative_status": alternative_status,
        "both_optimal": both_optimal,
        "optimal_objective_match": objective_match,
        "objective_tolerance": float(objective_tolerance),
        "both_nonoptimal": bool(baseline_status != "OPTIMAL" and alternative_status != "OPTIMAL"),
        "timeout_resolved": bool(baseline_status != "OPTIMAL" and alternative_status == "OPTIMAL"),
        "timeout_regression": bool(baseline_status == "OPTIMAL" and alternative_status != "OPTIMAL"),
        "right_censored_counterfactual": bool(not (both_optimal and objective_match)),
        "usable_for_counterfactual_training": bool(strong_positive or label_type == "regression"),
        "usable_for_gap_aux_training": bool(weak_positive or regression),
        "counterfactual_label_type": label_type,
        "hard_negative_loss_weight": 1.0 if regression else 0.0,
        "baseline_wall_time": baseline_wall,
        "alternative_wall_time": alternative_wall,
        "baseline_gap": baseline_gap,
        "alternative_gap": alternative_gap,
        "baseline_gap_available": _gap_available(baseline_row),
        "alternative_gap_available": _gap_available(alternative_row),
        "baseline_gap_source": baseline_row.get("gap_source"),
        "alternative_gap_source": alternative_row.get("gap_source"),
        "baseline_best_primal_bound": baseline_primal,
        "alternative_best_primal_bound": alternative_primal,
        "baseline_best_dual_bound": baseline_dual,
        "alternative_best_dual_bound": alternative_dual,
        "baseline_node_count": _int(baseline_row.get("node_count")),
        "alternative_node_count": _int(alternative_row.get("node_count")),
        "baseline_branch_count": baseline_stats["branch_count"],
        "alternative_branch_count": alternative_stats["branch_count"],
        "baseline_fathom_count": baseline_stats["fathom_count"],
        "alternative_fathom_count": alternative_stats["fathom_count"],
        "baseline_completion_bound_final_judge_retry_count": baseline_stats[
            "completion_bound_final_judge_retry_count"
        ],
        "alternative_completion_bound_final_judge_retry_count": alternative_stats[
            "completion_bound_final_judge_retry_count"
        ],
        "baseline_ordinary_incomplete_no_column_retry_count": baseline_stats[
            "ordinary_incomplete_no_column_retry_count"
        ],
        "alternative_ordinary_incomplete_no_column_retry_count": alternative_stats[
            "ordinary_incomplete_no_column_retry_count"
        ],
        "deltas": {
            "wall_time_delta": round(alternative_wall - baseline_wall, 9),
            "wall_time_gain": round(wall_time_gain, 9),
            "gap_improvement": round(gap_improvement, 9),
            "primal_improvement": round(primal_improvement, 9),
            "dual_bound_gain": round(dual_bound_gain, 9),
            "branch_count_delta": float(alternative_stats["branch_count"] - baseline_stats["branch_count"]),
            "fathom_gain": float(fathom_gain),
            "completion_bound_final_judge_retry_gain": float(retry_gain),
            "ordinary_incomplete_no_column_retry_gain": float(
                baseline_stats["ordinary_incomplete_no_column_retry_count"]
                - alternative_stats["ordinary_incomplete_no_column_retry_count"]
            ),
        },
        "labels": {
            "y_weak_gap_positive": 1.0 if weak_positive else 0.0,
            "y_weak_gap_fathom_positive": 1.0 if label_type == "weak_gap_fathom_positive" else 0.0,
            "y_weak_gap_regression": 1.0 if regression else 0.0,
            "y_counterfactual_wall_improved": 1.0 if strong_positive else 0.0,
            "y_counterfactual_regression": 1.0 if regression else 0.0,
            "y_gap_improvement": float(gap_improvement),
            "y_primal_improvement": float(primal_improvement),
            "y_dual_bound_gain": float(dual_bound_gain),
            "y_fathom_gain": float(fathom_gain),
            "y_completion_bound_final_judge_retry_gain": float(retry_gain),
            "y_walltime_gain": float(wall_time_gain),
        },
        "alternative_branch_labels": {
            "y_child_completion_bound_retries": float(
                alternative_stats["completion_bound_final_judge_retry_count"]
            ),
            "y_child_fathom_events": float(alternative_stats["fathom_count"]),
            "y_child_proof_cpu": alternative_wall,
            "y_time_to_certificate": alternative_wall,
        },
        "baseline_raw_row": baseline_raw_row,
        "alternative_raw_row": alternative_raw_row,
        "source": {
            "baseline_results_csv": str(baseline_results),
            "baseline_log_jsonl": str(baseline_log),
            "alternative_results_csv": str(alternative_results),
            "alternative_log_jsonl": str(alternative_log),
        },
    }, None


def build_gap_delta_rows(
    *,
    baseline_results: Path,
    baseline_log: Path,
    baseline_pair: tuple[int, int],
    alternatives: list[tuple[str, tuple[int, int], Path, Path]],
    output_dir: Path,
    report: Path,
    node_id: int = 0,
    depth: int = 0,
    wall_cap: float = 600.0,
    min_wall_improvement: float = 30.0,
    min_gap_improvement: float = 0.001,
    min_primal_improvement: float = 0.5,
    objective_tolerance: float = 1.0e-5,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    for experiment, alternative_pair, alternative_results, alternative_log in alternatives:
        row, reason = _make_row(
            experiment=experiment,
            baseline_results=baseline_results,
            baseline_log=baseline_log,
            baseline_pair=baseline_pair,
            alternative_results=alternative_results,
            alternative_log=alternative_log,
            alternative_pair=alternative_pair,
            node_id=node_id,
            depth=depth,
            wall_cap=wall_cap,
            min_wall_improvement=min_wall_improvement,
            min_gap_improvement=min_gap_improvement,
            min_primal_improvement=min_primal_improvement,
            objective_tolerance=objective_tolerance,
        )
        if row is None:
            skipped[str(reason or "unknown")] += 1
            continue
        rows.append(row)

    label_counts = Counter(str(row.get("counterfactual_label_type") or "") for row in rows)
    status_pairs = Counter(
        f"{row.get('baseline_status')}->{row.get('alternative_status')}" for row in rows
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    rows_path = output_dir / "branch_counterfactual_delta_rows.jsonl"
    rows_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    summary = {
        "schema_version": "journey_branch_full_replay_gap_delta_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "baseline_results_csv": str(baseline_results),
        "baseline_log_jsonl": str(baseline_log),
        "baseline_pair": list(baseline_pair),
        "output_dir": str(output_dir),
        "rows_path": str(rows_path),
        "row_count": len(rows),
        "alternative_count": len(alternatives),
        "min_wall_improvement": float(min_wall_improvement),
        "min_gap_improvement": float(min_gap_improvement),
        "min_primal_improvement": float(min_primal_improvement),
        "objective_tolerance": float(objective_tolerance),
        "wall_cap": float(wall_cap),
        "label_type_counts": dict(sorted(label_counts.items())),
        "status_pair_counts": dict(sorted(status_pairs.items())),
        "skipped_counts": dict(sorted(skipped.items())),
        "weak_gap_positive_count": int(
            sum(
                1
                for row in rows
                if row.get("counterfactual_label_type") in {"weak_gap_positive", "weak_gap_fathom_positive"}
            )
        ),
        "weak_gap_fathom_positive_count": int(
            sum(1 for row in rows if row.get("counterfactual_label_type") == "weak_gap_fathom_positive")
        ),
        "weak_gap_regression_count": int(
            sum(1 for row in rows if row.get("counterfactual_label_type") == "weak_gap_regression")
        ),
        "strict_full_replay_positive_count": int(
            sum(1 for row in rows if row.get("counterfactual_label_type") == "strong_positive")
        ),
        "strict_full_replay_regression_count": int(
            sum(1 for row in rows if row.get("counterfactual_label_type") == "regression")
        ),
        "counterfactual_training_count": int(
            sum(1 for row in rows if bool(row.get("usable_for_counterfactual_training")))
        ),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary, rows)
    return summary


def _write_report(report: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Branch Full Replay Gap Delta",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把强制 Ryan-Foster pair 的完整 replay 结果转成 branch counterfactual 标签：both-OPTIMAL 且目标值一致时生成严格 wall-time 正/负例；未闭环时只生成弱 gap/fathom 辅助标签。该脚本只读既有 CSV/JSONL，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"baseline_pair = {summary['baseline_pair']}",
        f"row_count = {summary['row_count']}",
        f"label_type_counts = {summary['label_type_counts']}",
        f"status_pair_counts = {summary['status_pair_counts']}",
        f"skipped_counts = {summary['skipped_counts']}",
        f"strict_full_replay_positive_count = {summary['strict_full_replay_positive_count']}",
        f"counterfactual_training_count = {summary['counterfactual_training_count']}",
        "production_ready = false",
        "official_bound_effect = false",
        "certificate_effect = false",
        "```",
        "",
        "## 行级结果",
        "",
        "| alternative_pair | label | gap_improvement | primal_improvement | fathom_gain | CB/final-judge retry gain | wall_gain |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        deltas = row.get("deltas") if isinstance(row.get("deltas"), dict) else {}
        lines.append(
            "| "
            f"{row.get('alternative_pair')} | "
            f"{row.get('counterfactual_label_type')} | "
            f"{_float(deltas.get('gap_improvement')):.6f} | "
            f"{_float(deltas.get('primal_improvement')):.6f} | "
            f"{_float(deltas.get('fathom_gain')):.0f} | "
            f"{_float(deltas.get('completion_bound_final_judge_retry_gain')):.0f} | "
            f"{_float(deltas.get('wall_time_gain')):.6f} |"
        )
    lines.extend(
        [
            "",
            "## 解释",
            "",
            "both-OPTIMAL 且目标值一致的 row 可以作为严格 wall-time counterfactual 训练样本；right-censored row 只能说明在同一截断下 alternative pair 改善了 gap、incumbent 或局部 fathom 结构，不能算 strict full-replay positive。所有 row 都不能用于 official prune/certificate。",
        ]
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_alternative(value: list[str]) -> tuple[str, tuple[int, int], Path, Path]:
    if len(value) != 4:
        raise argparse.ArgumentTypeError("--alternative needs EXPERIMENT PAIR RESULTS_CSV LOG_JSONL")
    experiment, pair_text, results_csv, log_jsonl = value
    pair = _pair_tuple(pair_text)
    if pair is None:
        raise argparse.ArgumentTypeError(f"invalid pair: {pair_text}")
    return experiment, pair, Path(results_csv), Path(log_jsonl)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-results-csv", type=Path, required=True)
    parser.add_argument("--baseline-log-jsonl", type=Path, required=True)
    parser.add_argument("--baseline-pair", nargs=2, type=int, required=True)
    parser.add_argument(
        "--alternative",
        nargs=4,
        action="append",
        required=True,
        metavar=("EXPERIMENT", "PAIR", "RESULTS_CSV", "LOG_JSONL"),
    )
    parser.add_argument("--node-id", type=int, default=0)
    parser.add_argument("--depth", type=int, default=0)
    parser.add_argument("--wall-cap", type=float, default=600.0)
    parser.add_argument("--min-wall-improvement", type=float, default=30.0)
    parser.add_argument("--min-gap-improvement", type=float, default=0.001)
    parser.add_argument("--min-primal-improvement", type=float, default=0.5)
    parser.add_argument("--objective-tolerance", type=float, default=1.0e-5)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    baseline_pair = _pair_tuple(args.baseline_pair)
    if baseline_pair is None:
        raise SystemExit("invalid --baseline-pair")
    alternatives = [_parse_alternative(value) for value in args.alternative]
    summary = build_gap_delta_rows(
        baseline_results=args.baseline_results_csv,
        baseline_log=args.baseline_log_jsonl,
        baseline_pair=baseline_pair,
        alternatives=alternatives,
        output_dir=args.output_dir,
        report=args.report,
        node_id=args.node_id,
        depth=args.depth,
        wall_cap=args.wall_cap,
        min_wall_improvement=args.min_wall_improvement,
        min_gap_improvement=args.min_gap_improvement,
        min_primal_improvement=args.min_primal_improvement,
        objective_tolerance=args.objective_tolerance,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
