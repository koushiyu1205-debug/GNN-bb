#!/usr/bin/env python3
"""Build branch counterfactual delta rows from forced-pair full replay runs.

This script is offline and diagnostic-only.  It reads a replay runbook,
completed result CSVs, baseline result CSVs, and JSONL branch logs.  It does
not run BPC, pricing, RMP, or certificates, and it must not be used as a
source of official bounds.
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

from BPC_future.scripts.export_gat_branch_action_score_map import (
    _branch_feature_vector,
    _candidate_union,
    _pair,
    _rank_map,
)


DEFAULT_RUNBOOK = Path(
    "BPC_future/results/"
    "journey_branch_candidate_replay_runbook_v456_v455_failed8_positive_neighbor_full600_20260627/"
    "runbook.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "journey_branch_counterfactual_delta_v456_v455_failed8_positive_neighbor_full600_20260627"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260627_bpc_future_journey_branch_counterfactual_delta_v456_v455_failed8_zh.md"
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


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


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


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


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


def _command_arg(command: Any, flag: str) -> str | None:
    if not isinstance(command, list):
        return None
    for index, token in enumerate(command):
        if str(token) == flag and index + 1 < len(command):
            return str(command[index + 1])
    return None


def _result_csv_for_entry(entry: dict[str, Any]) -> Path | None:
    value = entry.get("results_csv") or _command_arg(entry.get("command"), "--results-csv")
    return Path(value) if value else None


def _log_dir_for_entry(entry: dict[str, Any]) -> Path | None:
    value = entry.get("log_dir") or _command_arg(entry.get("command"), "--log-dir")
    return Path(value) if value else None


def _instance_log_path(log_dir: Path, instance: str) -> Path:
    return log_dir / f"{instance}.jsonl"


def _first_branch_candidate_event(log_path: Path, *, node_id: int, depth: int) -> dict[str, Any] | None:
    fallback: dict[str, Any] | None = None
    for record in _iter_jsonl(log_path):
        if record.get("event") != "journey_branch_candidates":
            continue
        if fallback is None:
            fallback = record
        if _int(record.get("node_id"), -1) == int(node_id) and _int(record.get("depth"), -1) == int(depth):
            return record
    return fallback


def _first_branch_event(log_path: Path, *, node_id: int, depth: int) -> dict[str, Any] | None:
    fallback: dict[str, Any] | None = None
    for record in _iter_jsonl(log_path):
        if record.get("event") != "journey_branch":
            continue
        if fallback is None:
            fallback = record
        if _int(record.get("node_id"), -1) == int(node_id) and _int(record.get("depth"), -1) == int(depth):
            return record
    return fallback


def _candidate_for_pair(event: dict[str, Any], pair: tuple[int, int]) -> dict[str, Any] | None:
    for candidate in _candidate_union(event):
        if _pair(candidate) == pair:
            return candidate
    selected = event.get("selected")
    if isinstance(selected, dict) and _pair(selected) == pair:
        return selected
    return None


def _baseline_rows(paths: list[Path]) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for path in paths:
        for row in _read_csv(path):
            instance = str(row.get("instance") or "")
            if instance and instance not in rows:
                rows[instance] = row
    return rows


def _baseline_pair(entry: dict[str, Any], alt_event: dict[str, Any]) -> tuple[int, int] | None:
    return (
        _pair_tuple(entry.get("source_selected_pair"))
        or _pair_tuple(alt_event.get("baseline_pair"))
        or _pair_tuple(alt_event.get("selected_pair"))
    )


def _counterfactual_type(
    *,
    baseline_status: str,
    alternative_status: str,
    baseline_wall: float,
    alternative_wall: float,
    selected_pair_changed: bool,
    min_wall_improvement: float,
) -> tuple[str, dict[str, float], bool, float]:
    gain = float(baseline_wall) - float(alternative_wall)
    timeout_resolved = baseline_status != "OPTIMAL" and alternative_status == "OPTIMAL"
    timeout_regression = baseline_status == "OPTIMAL" and alternative_status != "OPTIMAL"
    wall_improved = baseline_status == "OPTIMAL" and alternative_status == "OPTIMAL" and gain >= float(min_wall_improvement)
    wall_regression = baseline_status == "OPTIMAL" and alternative_status == "OPTIMAL" and gain <= -float(min_wall_improvement)
    no_effect_negative = bool(selected_pair_changed and alternative_status != "OPTIMAL" and not timeout_regression)

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
        "y_counterfactual_regression": 1.0 if timeout_regression or wall_regression else 0.0,
        "y_counterfactual_timeout_regression": 1.0 if timeout_regression else 0.0,
        "y_counterfactual_no_effect_hard_negative": 1.0 if no_effect_negative else 0.0,
    }
    # Changed full-run timeouts are completed observations for this training
    # purpose: they say this forced root pair did not close the instance.
    right_censored = label_type == "observed_neutral"
    return label_type, labels, right_censored, gain


def _branch_labels(result_row: dict[str, str], candidate: dict[str, Any]) -> dict[str, float]:
    status = str(result_row.get("status") or "")
    timeout = status != "OPTIMAL"
    return {
        "y_tail_improved": 1.0 if status == "OPTIMAL" else 0.0,
        "y_completion_bound_tail": 1.0 if timeout else 0.0,
        "y_early_branch_continues": 0.0,
        "y_negative_chain_continues": 1.0 if timeout else 0.0,
        "y_active_touch": 1.0,
        "y_inactive_only": 0.0,
        "y_child_negative_pricing_events": _float(result_row.get("exact_pricing_calls")),
        "y_child_exact_pricing_events": _float(result_row.get("exact_pricing_calls")),
        "y_child_completion_bound_retries": 1.0 if timeout else 0.0,
        "y_child_early_branch_triggers": 0.0,
        "y_child_fathom_events": 1.0 if status == "OPTIMAL" else 0.0,
        "y_child_max_safe_bound_gain": 0.0,
        "y_child_max_corrected_bound_gain": 0.0,
        "pool_total_child_width": _float(candidate.get("pool_total_child_width")),
        "pool_balance_gap": _float(candidate.get("pool_balance_gap")),
        "pool_max_child_width": _float(candidate.get("pool_max_child_width")),
    }


def _delta_row(
    *,
    entry: dict[str, Any],
    baseline_row: dict[str, str],
    result_row: dict[str, str],
    alt_event: dict[str, Any],
    branch_event: dict[str, Any] | None,
    candidate: dict[str, Any],
    min_wall_improvement: float,
    wall_cap: float,
) -> dict[str, Any] | None:
    forced_pair = _pair_tuple(entry.get("forced_pair"))
    baseline_pair = _baseline_pair(entry, alt_event)
    selected_pair = _pair_tuple(alt_event.get("selected_pair"))
    branch_selected_pair = _pair_tuple(branch_event.get("selected_pair")) if branch_event else None
    if forced_pair is None or baseline_pair is None or selected_pair is None:
        return None
    forced_matched = bool(selected_pair == forced_pair and (branch_selected_pair is None or branch_selected_pair == forced_pair))
    if not forced_matched:
        return None

    rank_top = _rank_map(alt_event.get("top"))
    rank_priority = _rank_map(alt_event.get("priority_top"))
    key = f"{forced_pair[0]},{forced_pair[1]}"
    rank_in_top = rank_top.get(key)
    rank_in_priority_top = rank_priority.get(key)

    baseline_status = str(baseline_row.get("status") or "")
    alternative_status = str(result_row.get("status") or "")
    baseline_wall = min(_float(baseline_row.get("wall_time"), default=wall_cap), float(wall_cap))
    alternative_wall = min(_float(result_row.get("wall_time"), default=wall_cap), float(wall_cap))
    selected_pair_changed = bool(baseline_pair != forced_pair)
    label_type, labels, right_censored, gain = _counterfactual_type(
        baseline_status=baseline_status,
        alternative_status=alternative_status,
        baseline_wall=baseline_wall,
        alternative_wall=alternative_wall,
        selected_pair_changed=selected_pair_changed,
        min_wall_improvement=min_wall_improvement,
    )
    if label_type == "observed_neutral":
        return None

    feature_vector = _branch_feature_vector(
        alt_event,
        candidate,
        rank_in_top=rank_in_top,
        rank_in_priority_top=rank_in_priority_top,
    )
    branch_labels = _branch_labels(result_row, candidate)
    return {
        "schema_version": "journey_branch_counterfactual_delta_forced_replay_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "experiment": str(entry.get("experiment") or ""),
        "instance": str(entry.get("instance") or result_row.get("instance") or ""),
        "node_id": _int(alt_event.get("node_id")),
        "depth": _int(alt_event.get("depth")),
        "baseline_pair": list(baseline_pair),
        "alternative_pair": list(forced_pair),
        "alternative_forced_pair_matched": True,
        "selected_pair_changed": selected_pair_changed,
        "baseline_status": baseline_status,
        "alternative_status": alternative_status,
        "both_optimal": bool(baseline_status == "OPTIMAL" and alternative_status == "OPTIMAL"),
        "both_nonoptimal": bool(baseline_status != "OPTIMAL" and alternative_status != "OPTIMAL"),
        "timeout_resolved": bool(baseline_status != "OPTIMAL" and alternative_status == "OPTIMAL"),
        "timeout_regression": bool(baseline_status == "OPTIMAL" and alternative_status != "OPTIMAL"),
        "right_censored_counterfactual": right_censored,
        "usable_for_counterfactual_training": not right_censored,
        "counterfactual_label_type": label_type,
        "hard_negative_loss_weight": 1.0,
        "baseline_wall_time": baseline_wall,
        "alternative_wall_time": alternative_wall,
        "baseline_solving_time": min(_float(baseline_row.get("solving_time"), default=baseline_wall), float(wall_cap)),
        "alternative_solving_time": min(_float(result_row.get("solving_time"), default=alternative_wall), float(wall_cap)),
        "baseline_node_count": _int(baseline_row.get("node_count")),
        "alternative_node_count": _int(result_row.get("node_count")),
        "baseline_exact_pricing_calls": _int(baseline_row.get("exact_pricing_calls")),
        "alternative_exact_pricing_calls": _int(result_row.get("exact_pricing_calls")),
        "child_proof_cpu": alternative_wall,
        "child_time_to_certificate": alternative_wall,
        "deltas": {
            "wall_time_delta": round(alternative_wall - baseline_wall, 9),
            "wall_time_gain": round(gain, 9),
            "node_count_delta": float(_int(result_row.get("node_count")) - _int(baseline_row.get("node_count"))),
        },
        "labels": labels,
        "alternative_branch_labels": branch_labels,
        "alternative_raw_row": {
            "branch_feature_vector": feature_vector,
            "branch_time": _float(alt_event.get("time")),
            "candidate_count": alt_event.get("candidate_count"),
            "eligible_count": alt_event.get("eligible_count"),
            "branch_rank_in_top": rank_in_top,
            "branch_rank_in_priority_top": rank_in_priority_top,
            "selected_score": candidate.get("branch_score"),
            "selected_score_source": candidate.get("branch_score_source"),
            "branch_score_selection_gate_reason": alt_event.get("branch_score_selection_gate_reason"),
            "branch_score_selection_gate_passed": alt_event.get("branch_score_selection_gate_passed"),
            "phased_testing_stage": candidate.get("phased_testing_stage"),
            "phased_testing_decision": candidate.get("phased_testing_decision"),
            "phased_testing_reason": candidate.get("phased_testing_reason"),
            "phased_testing_elimination_reason": candidate.get("phased_testing_elimination_reason"),
            "phased_testing_phase0_passed": candidate.get("phased_testing_phase0_passed"),
            "phased_testing_phase1_lp_complete": candidate.get("phased_testing_phase1_lp_complete"),
            "phased_testing_phase2_heuristic_complete": candidate.get("phased_testing_phase2_heuristic_complete"),
            "phase1_min_child_lp_gain": candidate.get("phase1_min_child_lp_gain"),
            "phase1_child_lp_gain_product": candidate.get("phase1_child_lp_gain_product"),
            "phase1_child_width_balance": candidate.get("phase1_child_width_balance"),
            "phase1_wall_time": candidate.get("phase1_wall_time"),
            "phase1_dynamic_k_probe_count": candidate.get("phase1_dynamic_k_probe_count"),
            "phase2_negative_child_count": candidate.get("phase2_negative_child_count"),
            "phase2_negative_journey_count": candidate.get("phase2_negative_journey_count"),
            "phase2_best_reduced_cost": candidate.get("phase2_best_reduced_cost"),
            "phase2_worst_negative_severity": candidate.get("phase2_worst_negative_severity"),
            "phase2_wall_time": candidate.get("phase2_wall_time"),
            "phase2_dynamic_k_probe_count": candidate.get("phase2_dynamic_k_probe_count"),
            "pool_total_child_width": candidate.get("pool_total_child_width"),
            "pool_balance_gap": candidate.get("pool_balance_gap"),
            "pool_max_child_width": candidate.get("pool_max_child_width"),
        },
        "source": {
            "runbook": str(entry.get("runbook_path") or ""),
            "source_log_file": str(entry.get("source_log_file") or ""),
            "alternative_log_file": str(entry.get("alternative_log_file") or ""),
            "results_csv": str(entry.get("results_csv") or ""),
            "baseline_csv": str(entry.get("baseline_csv") or ""),
        },
    }


def build_delta_rows(
    *,
    runbook: Path,
    baseline_csvs: list[Path],
    output_dir: Path,
    report: Path,
    min_wall_improvement: float = 30.0,
    wall_cap: float = 600.0,
) -> dict[str, Any]:
    payload = _read_json(runbook)
    baseline_by_instance = _baseline_rows(baseline_csvs)
    rows: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()

    for entry in payload.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        instance = str(entry.get("instance") or "")
        result_csv = _result_csv_for_entry(entry)
        log_dir = _log_dir_for_entry(entry)
        if not instance:
            skipped["missing_instance"] += 1
            continue
        if result_csv is None or not result_csv.exists():
            skipped["missing_results_csv"] += 1
            continue
        result_rows = _read_csv(result_csv)
        if not result_rows:
            skipped["empty_results_csv"] += 1
            continue
        result_row = result_rows[0]
        baseline_row = baseline_by_instance.get(instance)
        if baseline_row is None:
            skipped["missing_baseline_row"] += 1
            continue
        if log_dir is None:
            skipped["missing_log_dir"] += 1
            continue
        alt_log = _instance_log_path(log_dir, instance)
        node_id = _int(entry.get("source_node_id"))
        depth = _int(entry.get("source_depth"))
        alt_event = _first_branch_candidate_event(alt_log, node_id=node_id, depth=depth)
        if alt_event is None:
            skipped["missing_alternative_branch_candidate_event"] += 1
            continue
        forced_pair = _pair_tuple(entry.get("forced_pair"))
        if forced_pair is None:
            skipped["missing_forced_pair"] += 1
            continue
        candidate = _candidate_for_pair(alt_event, forced_pair)
        if candidate is None:
            skipped["missing_forced_candidate"] += 1
            continue
        branch_event = _first_branch_event(alt_log, node_id=node_id, depth=depth)
        enriched_entry = dict(entry)
        enriched_entry["runbook_path"] = str(runbook)
        enriched_entry["alternative_log_file"] = str(alt_log)
        enriched_entry["results_csv"] = str(result_csv)
        enriched_entry["baseline_csv"] = ",".join(str(path) for path in baseline_csvs)
        row = _delta_row(
            entry=enriched_entry,
            baseline_row=baseline_row,
            result_row=result_row,
            alt_event=alt_event,
            branch_event=branch_event,
            candidate=candidate,
            min_wall_improvement=min_wall_improvement,
            wall_cap=wall_cap,
        )
        if row is None:
            skipped["row_not_usable"] += 1
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
        "schema_version": "journey_branch_forced_replay_delta_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "runbook": str(runbook),
        "baseline_csvs": [str(path) for path in baseline_csvs],
        "output_dir": str(output_dir),
        "rows_path": str(rows_path),
        "min_wall_improvement": float(min_wall_improvement),
        "wall_cap": float(wall_cap),
        "entry_count": len(payload.get("entries") or []),
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
        "# Journey Branch Forced Replay Delta",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把强制 Ryan-Foster pair 的完整 600 秒 replay 结果转成 branch/action 训练 row。该脚本只读完成的 runbook、结果 CSV 和 JSONL 日志，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"runbook = {summary['runbook']}",
        f"output_dir = {summary['output_dir']}",
        f"entry_count = {summary['entry_count']}",
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
        "这些 row 只用于训练 branch 候选排序和 score gate；不能作为剪枝依据，不能替代 exact pricing closure。",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runbook", type=Path, default=DEFAULT_RUNBOOK)
    parser.add_argument("--baseline-csv", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-wall-improvement", type=float, default=30.0)
    parser.add_argument("--wall-cap", type=float, default=600.0)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    summary = build_delta_rows(
        runbook=args.runbook,
        baseline_csvs=list(args.baseline_csv),
        output_dir=args.output_dir,
        report=args.report,
        min_wall_improvement=float(args.min_wall_improvement),
        wall_cap=float(args.wall_cap),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if int(summary["row_count"]) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
