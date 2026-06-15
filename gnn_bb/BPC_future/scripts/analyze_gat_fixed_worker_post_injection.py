#!/usr/bin/env python3
"""Analyze trajectory after fixed target-materialization worker injection.

This is a read-only post-run analyzer.  It does not run BPC, pricing, workers,
or certificates.  It reads the JSONL logs from a fixed-worker A/B runbook and
extracts what happens immediately after the worker injects target columns:

* next RMP objective delta;
* next dual L1 movement;
* target-column active-support productivity;
* follow-up pricing/exact pressure;
* context-mismatch skips after injection.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


DEFAULT_RUNBOOK_SUMMARY = Path(
    "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/"
    "scale_family_task020_fixed_materialization_batch_k4_worker_ab_runbook/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/"
    "scale_family_task020_fixed_materialization_batch_k4_worker_ab_runbook/"
    "post_injection_trajectory_audit"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260615_bpc_future_gat_fixed_worker_batch_k4_post_injection_trajectory_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runbook-summary", type=Path, default=DEFAULT_RUNBOOK_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help=(
            "Audit only completed baseline+worker pairs. The default remains strict "
            "and requires all runbook rows to have logs."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = analyze_post_injection(
        runbook_summary=args.runbook_summary,
        output_dir=args.output_dir,
        report=args.report,
        allow_partial=bool(args.allow_partial),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def analyze_post_injection(
    *,
    runbook_summary: Path = DEFAULT_RUNBOOK_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    allow_partial: bool = False,
) -> dict[str, Any]:
    runbook = json.loads(Path(runbook_summary).read_text(encoding="utf-8"))
    all_rows = [
        _analyze_candidate(candidate)
        for candidate in runbook.get("candidate_runs") or []
    ]
    if allow_partial:
        rows = [
            row
            for row in all_rows
            if bool(row.get("baseline_jsonl_exists"))
            and bool(row.get("worker_jsonl_exists"))
        ]
    else:
        rows = all_rows
    skipped_rows = [row for row in all_rows if row not in rows]
    target_success_rows = [row for row in rows if row["target_injection_success"]]
    immediate_objective_improved = [
        row
        for row in target_success_rows
        if _is_negative(row.get("worker_next_objective_delta"))
    ]
    immediate_vs_baseline_improved = [
        row
        for row in target_success_rows
        if _is_negative(row.get("worker_next_objective_vs_baseline_same_iter_delta"))
    ]
    long_horizon_positive = [
        row
        for row in rows
        if str(row.get("final_roi_class", "")).startswith("positive_")
    ]
    long_horizon_negative = [
        row
        for row in rows
        if str(row.get("final_roi_class", "")).startswith("negative_")
    ]
    strict_positive = [
        row for row in rows if int(row.get("strict_trajectory_roi_label") or 0) == 1
    ]
    strict_negative = [
        row for row in rows if int(row.get("strict_trajectory_roi_label") or 0) == 0
    ]
    strict_uncertain = [
        row for row in rows if row.get("strict_trajectory_roi_label") is None
    ]
    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "runbook_checks_pass": bool(runbook.get("all_checks_pass")),
        "rows_present": bool(rows),
        "jsonl_logs_present": all(
            row["baseline_jsonl_exists"] and row["worker_jsonl_exists"] for row in rows
        ),
        "no_official_bound_effect": all(not row["official_bound_effect"] for row in rows),
        "worker_method_fixed": runbook.get("candidate_policy", {}).get("worker_method")
        == "target_materialization_fixed",
    }
    summary = {
        "schema_version": "gat_fixed_worker_post_injection_trajectory_audit_v1",
        "status": "audited" if rows else "no_records",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "runbook_summary": str(runbook_summary),
        "allow_partial": bool(allow_partial),
        "runbook_candidate_count": len(all_rows),
        "record_count": len(rows),
        "skipped_missing_log_count": len(skipped_rows),
        "target_injection_success_count": len(target_success_rows),
        "target_returned_journeys_sum": _sum_number(
            row.get("target_returned_journeys") for row in rows
        ),
        "target_active_changed_task_set_sum": _sum_number(
            row.get("target_active_changed_task_set_count") for row in rows
        ),
        "target_inactive_changed_task_set_sum": _sum_number(
            row.get("target_inactive_changed_task_set_count") for row in rows
        ),
        "immediate_objective_improved_count": len(immediate_objective_improved),
        "immediate_vs_baseline_same_iter_improved_count": len(
            immediate_vs_baseline_improved
        ),
        "worker_next_objective_delta_sum": _sum_number(
            row.get("worker_next_objective_delta") for row in target_success_rows
        ),
        "worker_next_dual_l1_delta_mean": _mean_number(
            row.get("worker_next_dual_l1_delta") for row in target_success_rows
        ),
        "worker_next_objective_vs_baseline_same_iter_delta_sum": _sum_number(
            row.get("worker_next_objective_vs_baseline_same_iter_delta")
            for row in target_success_rows
        ),
        "followup_pricing_event_sum": _sum_number(
            row.get("worker_followup_pricing_events") for row in rows
        ),
        "followup_exact_event_sum": _sum_number(
            row.get("worker_followup_exact_pricing_events") for row in rows
        ),
        "followup_completion_retry_event_sum": _sum_number(
            row.get("worker_followup_completion_retry_events") for row in rows
        ),
        "context_mismatch_skip_sum": _sum_number(
            row.get("worker_context_mismatch_skips_after_injection") for row in rows
        ),
        "final_positive_roi_count": len(long_horizon_positive),
        "final_negative_roi_count": len(long_horizon_negative),
        "strict_trajectory_positive_count": len(strict_positive),
        "strict_trajectory_negative_count": len(strict_negative),
        "strict_trajectory_uncertain_count": len(strict_uncertain),
        "records": rows,
        "skipped_records": skipped_rows,
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "next_decision": _next_decision(
            rows=rows,
            target_success_rows=target_success_rows,
            long_horizon_positive=strict_positive,
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "records.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _analyze_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    baseline_csv = Path(str(candidate.get("baseline_csv") or ""))
    worker_csv = Path(str(candidate.get("worker_csv") or ""))
    baseline_events = _read_jsonl_for_csv(baseline_csv)
    worker_events = _read_jsonl_for_csv(worker_csv)
    baseline_by_iter = _rmp_dual_by_iter(baseline_events)
    worker_success = _first_success_worker_event(worker_events)
    target_cg_iter = _int_value(worker_success, "cg_iter")
    target_time = _float_value(worker_success, "time")
    target_addition = _first_event_after(
        worker_events,
        event="journey_column_addition",
        min_time=target_time,
        cg_iter=target_cg_iter,
        predicate=lambda rec: rec.get("pricing_kind")
        == "sharded_pulse_hidden_negative_worker",
    )
    worker_next_dual = _first_rmp_dual_after(worker_events, target_cg_iter)
    baseline_same_iter = (
        baseline_by_iter.get(int(worker_next_dual["cg_iter"]))
        if worker_next_dual and worker_next_dual.get("cg_iter") is not None
        else None
    )
    worker_finish = _last_event(worker_events, "finish")
    baseline_finish = _last_event(baseline_events, "finish")
    baseline_csv_row = _read_first_csv_row(baseline_csv)
    worker_csv_row = _read_first_csv_row(worker_csv)
    followup_events = [
        rec
        for rec in worker_events
        if target_cg_iter is not None and _int_value(rec, "cg_iter") is not None
        and int(_int_value(rec, "cg_iter") or 0) > int(target_cg_iter)
    ]
    worker_followup_workers = [
        rec
        for rec in followup_events
        if rec.get("event") == "journey_sharded_pulse_hidden_negative_worker"
    ]
    target_sortie_traces = list(candidate.get("target_sortie_traces") or [])
    primary_trace = target_sortie_traces[0] if target_sortie_traces else {}
    candidate_batch_target_sequences = list(
        candidate.get("candidate_batch_target_sequences") or []
    )
    candidate_batch_target_arc_option_sequences = list(
        candidate.get("candidate_batch_target_arc_option_sequences") or []
    )
    primary_target_sequence = (
        list(candidate_batch_target_sequences[0])
        if candidate_batch_target_sequences
        else list(primary_trace.get("sequence") or candidate.get("target_sequence") or [])
    )
    primary_target_arcs = (
        list(candidate_batch_target_arc_option_sequences[0])
        if candidate_batch_target_arc_option_sequences
        else list(
            primary_trace.get("arc_option_sequence")
            or candidate.get("target_arc_option_sequence")
            or []
        )
    )
    record = {
        "name": str(candidate.get("name") or ""),
        "instance": str(candidate.get("instance") or ""),
        "expected_context_hash": str(candidate.get("expected_context_hash") or ""),
        "candidate_batch_count": int(candidate.get("candidate_batch_count") or 1),
        "candidate_batch_target_sequences": candidate_batch_target_sequences,
        "candidate_batch_target_arc_option_sequences": (
            candidate_batch_target_arc_option_sequences
        ),
        "target_sequence": primary_target_sequence,
        "target_arc_option_sequence": primary_target_arcs,
        "baseline_csv": str(baseline_csv),
        "worker_csv": str(worker_csv),
        "baseline_csv_exists": baseline_csv.exists(),
        "worker_csv_exists": worker_csv.exists(),
        "baseline_jsonl_exists": bool(baseline_events),
        "worker_jsonl_exists": bool(worker_events),
        "certificate_effect": False,
        "target_injection_success": worker_success is not None,
        "target_cg_iter": target_cg_iter,
        "target_context_hash": None
        if worker_success is None
        else worker_success.get("pulse_worker_context_hash"),
        "target_signal_source": None
        if worker_success is None
        else worker_success.get("pulse_worker_signal_source"),
        "target_returned_journeys": _int_value(worker_success, "pulse_worker_returned_journeys"),
        "target_best_rc": _float_value(worker_success, "pulse_worker_best_rc"),
        "target_addition_productivity_class": None
        if target_addition is None
        else target_addition.get("addition_productivity_class"),
        "target_added_journeys": _int_value(target_addition, "added_journeys"),
        "target_new_journeys": _int_value(target_addition, "new_journeys"),
        "target_replacement_journeys": _int_value(target_addition, "replacement_journeys"),
        "target_active_changed_task_set_count": _int_value(
            target_addition, "active_changed_task_set_count"
        ),
        "target_inactive_changed_task_set_count": _int_value(
            target_addition, "inactive_changed_task_set_count"
        ),
        "worker_next_cg_iter": _int_value(worker_next_dual, "cg_iter"),
        "worker_next_objective": _float_value(worker_next_dual, "objective"),
        "worker_next_objective_delta": _float_value(worker_next_dual, "objective_delta"),
        "worker_next_dual_l1_delta": _float_value(worker_next_dual, "dual_l1_delta"),
        "worker_next_active_support_hash": None
        if worker_next_dual is None
        else worker_next_dual.get("active_support_hash"),
        "baseline_same_iter_objective": _float_value(baseline_same_iter, "objective"),
        "baseline_same_iter_objective_delta": _float_value(
            baseline_same_iter, "objective_delta"
        ),
        "baseline_same_iter_dual_l1_delta": _float_value(
            baseline_same_iter, "dual_l1_delta"
        ),
        "worker_next_objective_vs_baseline_same_iter_delta": _subtract(
            _float_value(worker_next_dual, "objective"),
            _float_value(baseline_same_iter, "objective"),
        ),
        "worker_next_dual_l1_vs_baseline_same_iter_delta": _subtract(
            _float_value(worker_next_dual, "dual_l1_delta"),
            _float_value(baseline_same_iter, "dual_l1_delta"),
        ),
        "worker_followup_pricing_events": sum(
            1 for rec in followup_events if rec.get("event") == "journey_pricing"
        ),
        "worker_followup_exact_pricing_events": sum(
            1
            for rec in followup_events
            if rec.get("event") == "journey_pricing"
            and "exact" in str(rec.get("pricing_kind") or "")
        ),
        "worker_followup_completion_retry_events": sum(
            1
            for rec in followup_events
            if rec.get("event") == "journey_exact_pricing_completion_bound_retry"
            or (
                rec.get("event") == "journey_pricing"
                and str(rec.get("pricing_kind") or "") == "exact_completion_bound_retry"
            )
        ),
        "worker_context_mismatch_skips_after_injection": sum(
            1
            for rec in worker_followup_workers
            if rec.get("pulse_worker_skip_reason") == "residual_target_context_mismatch"
        ),
        "worker_followup_worker_events": len(worker_followup_workers),
        "baseline_status": _status(baseline_csv_row, baseline_finish),
        "worker_status": _status(worker_csv_row, worker_finish),
        "baseline_solving_time": _first_number(
            _float_value(baseline_csv_row, "solving_time"),
            _float_value(baseline_finish, "solving_time"),
            _float_value(baseline_finish, "time"),
        ),
        "worker_solving_time": _first_number(
            _float_value(worker_csv_row, "solving_time"),
            _float_value(worker_finish, "solving_time"),
            _float_value(worker_finish, "time"),
        ),
        "baseline_rmp_solves": _first_number(
            _int_value(baseline_csv_row, "rmp_solves"),
            _int_value(baseline_finish, "rmp_solves"),
        ),
        "worker_rmp_solves": _first_number(
            _int_value(worker_csv_row, "rmp_solves"),
            _int_value(worker_finish, "rmp_solves"),
        ),
        "baseline_pricing_calls": _first_number(
            _int_value(baseline_csv_row, "pricing_calls"),
            _int_value(baseline_finish, "pricing_calls"),
        ),
        "worker_pricing_calls": _first_number(
            _int_value(worker_csv_row, "pricing_calls"),
            _int_value(worker_finish, "pricing_calls"),
        ),
        "baseline_exact_pricing_calls": _first_number(
            _int_value(baseline_csv_row, "exact_pricing_calls"),
            _int_value(baseline_finish, "exact_pricing_calls"),
        ),
        "worker_exact_pricing_calls": _first_number(
            _int_value(worker_csv_row, "exact_pricing_calls"),
            _int_value(worker_finish, "exact_pricing_calls"),
        ),
        "official_bound_effect": _official_bound_effect(baseline_csv_row, worker_csv_row),
    }
    record["solving_time_delta"] = _subtract(
        record.get("worker_solving_time"), record.get("baseline_solving_time")
    )
    record["rmp_solves_delta"] = _subtract(
        record.get("worker_rmp_solves"), record.get("baseline_rmp_solves")
    )
    record["pricing_calls_delta"] = _subtract(
        record.get("worker_pricing_calls"), record.get("baseline_pricing_calls")
    )
    record["exact_pricing_calls_delta"] = _subtract(
        record.get("worker_exact_pricing_calls"), record.get("baseline_exact_pricing_calls")
    )
    record["final_roi_class"] = _final_roi_class(record)
    strict_label, strict_class, strict_reason = _strict_trajectory_roi(record)
    record["strict_trajectory_roi_label"] = strict_label
    record["strict_trajectory_roi_class"] = strict_class
    record["strict_trajectory_roi_reason"] = strict_reason
    return record


def _read_jsonl_for_csv(csv_path: Path) -> list[dict[str, Any]]:
    log_dir = Path(csv_path).parent / "logs"
    if not log_dir.exists():
        return []
    candidates = sorted(log_dir.rglob("*.jsonl"))
    if not candidates:
        return []
    events: list[dict[str, Any]] = []
    with candidates[0].open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def _first_success_worker_event(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for rec in events:
        if rec.get("event") != "journey_sharded_pulse_hidden_negative_worker":
            continue
        if int(_int_value(rec, "pulse_worker_returned_journeys") or 0) <= 0:
            continue
        if rec.get("pulse_worker_status") != "FOUND_NEGATIVE":
            continue
        return rec
    return None


def _first_event_after(
    events: list[dict[str, Any]],
    *,
    event: str,
    min_time: float | None,
    cg_iter: int | None,
    predicate: Any | None = None,
) -> dict[str, Any] | None:
    for rec in events:
        if rec.get("event") != event:
            continue
        if min_time is not None and (_float_value(rec, "time") or -math.inf) < min_time:
            continue
        if cg_iter is not None and _int_value(rec, "cg_iter") != cg_iter:
            continue
        if predicate is not None and not predicate(rec):
            continue
        return rec
    return None


def _first_rmp_dual_after(
    events: list[dict[str, Any]], cg_iter: int | None
) -> dict[str, Any] | None:
    if cg_iter is None:
        return None
    for rec in events:
        if rec.get("event") != "journey_rmp_dual_diagnostics":
            continue
        rec_iter = _int_value(rec, "cg_iter")
        if rec_iter is not None and rec_iter > cg_iter:
            return rec
    return None


def _last_event(events: list[dict[str, Any]], event: str) -> dict[str, Any] | None:
    result = None
    for rec in events:
        if rec.get("event") == event:
            result = rec
    return result


def _rmp_dual_by_iter(events: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for rec in events:
        if rec.get("event") != "journey_rmp_dual_diagnostics":
            continue
        cg_iter = _int_value(rec, "cg_iter")
        if cg_iter is not None:
            result[int(cg_iter)] = rec
    return result


def _read_first_csv_row(path: Path) -> dict[str, Any] | None:
    if not Path(path).exists():
        return None
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            return dict(row)
    return None


def _float_value(row: dict[str, Any] | None, key: str) -> float | None:
    if not row:
        return None
    value = row.get(key)
    if value is None or str(value).strip() == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(result) or math.isinf(result) else result


def _int_value(row: dict[str, Any] | None, key: str) -> int | None:
    value = _float_value(row, key)
    return None if value is None else int(value)


def _status(csv_row: dict[str, Any] | None, finish: dict[str, Any] | None) -> str | None:
    if csv_row and csv_row.get("status"):
        return str(csv_row.get("status"))
    if finish and finish.get("status"):
        return str(finish.get("status"))
    return None


def _subtract(left: Any, right: Any) -> float | None:
    if left is None or right is None:
        return None
    try:
        return float(left) - float(right)
    except (TypeError, ValueError):
        return None


def _first_number(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _sum_number(values: Any) -> float:
    total = 0.0
    for value in values:
        if value is None:
            continue
        total += float(value)
    return total


def _mean_number(values: Any) -> float | None:
    cleaned = [float(value) for value in values if value is not None]
    if not cleaned:
        return None
    return sum(cleaned) / float(len(cleaned))


def _is_negative(value: Any) -> bool:
    return value is not None and float(value) < -1.0e-9


def _official_bound_effect(
    baseline_csv_row: dict[str, Any] | None, worker_csv_row: dict[str, Any] | None
) -> bool:
    baseline_dual = _float_value(baseline_csv_row, "dual_bound")
    worker_dual = _float_value(worker_csv_row, "dual_bound")
    return worker_dual is not None and baseline_dual != worker_dual


def _final_roi_class(record: dict[str, Any]) -> str:
    if record.get("worker_status") == "OPTIMAL" and record.get("baseline_status") != "OPTIMAL":
        return "positive_status_roi"
    if record.get("baseline_status") == "OPTIMAL" and record.get("worker_status") != "OPTIMAL":
        return "negative_status_roi"
    exact_delta = record.get("exact_pricing_calls_delta")
    pricing_delta = record.get("pricing_calls_delta")
    time_delta = record.get("solving_time_delta")
    if exact_delta is not None and float(exact_delta) < 0:
        return "positive_exact_roi"
    if pricing_delta is not None and float(pricing_delta) < 0 and (
        exact_delta is None or float(exact_delta) <= 0
    ):
        return "positive_pricing_roi"
    if time_delta is not None and float(time_delta) < -1.0:
        return "positive_walltime_roi"
    if exact_delta is not None and float(exact_delta) > 0:
        return "negative_exact_roi"
    if time_delta is not None and float(time_delta) > 1.0:
        return "negative_walltime_roi"
    return "no_observed_roi"


def _strict_trajectory_roi(record: dict[str, Any]) -> tuple[int | None, str, str]:
    """Label trajectory ROI for training.

    This deliberately differs from the coarse final ROI class.  A candidate that
    reduces later exact/pricing calls is not a usable positive for the GAT gate
    if it worsens the next RMP trajectory against the same baseline iteration.
    """

    if not record.get("target_injection_success"):
        return 0, "negative_no_target_injection", "target_worker_did_not_inject"
    if record.get("official_bound_effect") or record.get("certificate_effect"):
        return None, "uncertain_certificate_effect", "certificate_or_bound_side_effect"
    active_changed = record.get("target_active_changed_task_set_count")
    if active_changed is not None and float(active_changed) <= 0.0:
        return 0, "negative_inactive_only", "target_columns_inactive_only"
    same_iter_delta = record.get("worker_next_objective_vs_baseline_same_iter_delta")
    if same_iter_delta is None:
        return None, "uncertain_missing_same_iter_objective", "missing_baseline_same_iter"
    if float(same_iter_delta) > 1.0e-9:
        return (
            0,
            "negative_worse_than_baseline_same_iter",
            "worse_than_baseline_same_iter_objective",
        )
    if record.get("worker_status") == "OPTIMAL" and record.get("baseline_status") != "OPTIMAL":
        return 1, "positive_status_roi", "worker_reaches_optimal_before_baseline"
    time_delta = record.get("solving_time_delta")
    if time_delta is not None and float(time_delta) < -1.0:
        return 1, "positive_walltime_roi", "wall_time_improved"
    exact_delta = record.get("exact_pricing_calls_delta")
    if exact_delta is not None and float(exact_delta) < 0.0:
        return 1, "positive_exact_roi", "same_iter_safe_exact_calls_reduced"
    pricing_delta = record.get("pricing_calls_delta")
    if pricing_delta is not None and float(pricing_delta) < 0.0:
        return 1, "positive_pricing_roi", "same_iter_safe_pricing_calls_reduced"
    return 0, "negative_no_observed_roi", "same_iter_safe_but_no_downstream_roi"


def _next_decision(
    *,
    rows: list[dict[str, Any]],
    target_success_rows: list[dict[str, Any]],
    long_horizon_positive: list[dict[str, Any]],
) -> str:
    if not rows:
        return "missing_post_injection_data"
    if not target_success_rows:
        return "target_materialization_not_reached"
    if long_horizon_positive:
        return "fit_trajectory_gate_on_positive_long_horizon_cases"
    return "retune_labels_from_long_horizon_trajectory_not_true_rc"


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Fixed Worker Post-Injection Trajectory Audit 报告",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "只读分析固定 worker 注入目标列之后的 trajectory 后效。该脚本不运行 BPC、pricing 或 worker，",
        "只读取已有 JSONL/CSV。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_fixed_worker_post_injection_trajectory_audit = current",
        f"status = {summary['status']}",
        f"allow_partial = {str(summary.get('allow_partial', False)).lower()}",
        f"runbook_candidate_count = {summary.get('runbook_candidate_count')}",
        f"record_count = {summary['record_count']}",
        f"skipped_missing_log_count = {summary.get('skipped_missing_log_count')}",
        f"target_injection_success_count = {summary['target_injection_success_count']}",
        f"target_returned_journeys_sum = {summary['target_returned_journeys_sum']}",
        f"target_active_changed_task_set_sum = {summary['target_active_changed_task_set_sum']}",
        f"target_inactive_changed_task_set_sum = {summary['target_inactive_changed_task_set_sum']}",
        f"immediate_objective_improved_count = {summary['immediate_objective_improved_count']}",
        "immediate_vs_baseline_same_iter_improved_count = "
        f"{summary['immediate_vs_baseline_same_iter_improved_count']}",
        f"worker_next_objective_delta_sum = {summary['worker_next_objective_delta_sum']}",
        f"worker_next_dual_l1_delta_mean = {summary['worker_next_dual_l1_delta_mean']}",
        "worker_next_objective_vs_baseline_same_iter_delta_sum = "
        f"{summary['worker_next_objective_vs_baseline_same_iter_delta_sum']}",
        f"followup_pricing_event_sum = {summary['followup_pricing_event_sum']}",
        f"followup_exact_event_sum = {summary['followup_exact_event_sum']}",
        f"followup_completion_retry_event_sum = {summary['followup_completion_retry_event_sum']}",
        f"context_mismatch_skip_sum = {summary['context_mismatch_skip_sum']}",
        f"final_positive_roi_count = {summary['final_positive_roi_count']}",
        f"final_negative_roi_count = {summary['final_negative_roi_count']}",
        f"strict_trajectory_positive_count = {summary['strict_trajectory_positive_count']}",
        f"strict_trajectory_negative_count = {summary['strict_trajectory_negative_count']}",
        f"strict_trajectory_uncertain_count = {summary['strict_trajectory_uncertain_count']}",
        f"next_decision = {summary['next_decision']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 核心发现",
        "",
        _finding_line(summary),
        "",
        "## 结论",
        "",
        "- `target_returned_journeys_sum` 衡量 GAT/worker 是否真的注入了 true-RC negative 列；",
        "- `target_active_changed_task_set_sum` 衡量这些列是否立刻进入 active support；",
        "- `worker_next_objective_delta_sum` 衡量注入后一轮 RMP 目标改善；",
        "- `worker_next_dual_l1_delta_mean` 衡量注入后 dual 震荡；",
        "- `context_mismatch_skip_sum` 衡量注入后 context 是否快速漂移；",
        "- `final_*_roi_count` 是粗粒度长程统计；",
        "- `strict_trajectory_*_count` 才是 GAT 训练更应使用的 ROI 标签口径："
        "active 改变且相对 baseline 同迭代 objective 不变差。",
        "",
        "## Records",
        "",
        "```json",
        json.dumps(summary["records"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 边界",
        "",
        "- 该分析不产生 certificate；",
        "- 该分析不改变任何求解结果；",
        "- 后续训练标签应优先使用 long-horizon trajectory ROI，而不是仅使用 true-RC negative。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _finding_line(summary: dict[str, Any]) -> str:
    if summary.get("target_injection_success_count", 0) <= 0:
        return "没有成功 target materialization，优先检查 worker 是否到达目标 context。"
    if (
        float(summary.get("target_returned_journeys_sum") or 0.0) > 0.0
        and float(summary.get("target_active_changed_task_set_sum") or 0.0) <= 0.0
    ):
        return (
            "所有 target 列都能作为 true-RC negative 注入，但没有立刻进入 active support；"
            "当前 GAT 学到的是可加列/真负列，不等于长程 trajectory ROI。"
        )
    if int(summary.get("immediate_vs_baseline_same_iter_improved_count") or 0) <= 0:
        return (
            "注入后一轮 RMP 虽可能本地下降，但相对 baseline 同迭代没有优势，"
            "需要把标签改成 post-injection trajectory impact。"
        )
    return "存在可用的 post-injection 正向信号，可优先抽取这些 case 做 trajectory gate 训练。"


if __name__ == "__main__":
    raise SystemExit(main())
