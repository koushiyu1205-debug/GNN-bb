#!/usr/bin/env python3
"""Build batch-impact rows from guarded multi-batch worker A/B logs.

The output rows are compatible with ``build_gat_batch_impact_dataset.py`` but
are stricter than plain CSV ROI: a row is emitted only when the worker log
reaches the expected context, materializes the configured target sequence,
adds a column in that same pricing stage, and has the next RMP state available.

This script is read-only.  It never runs BPC, pricing, RMP, workers, or
certificates, and it does not treat GAT or worker evidence as a no-negative
certificate.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_RUNBOOK_SUMMARY = Path(
    "BPC_future/results/"
    "gat_batch_impact_multibatch_intervention_plan_v3_signature_hard_roi_20260616/"
    "worker_ab_runbook/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "gat_multibatch_worker_batch_impact_rows_v3_signature_hard_roi_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage3_multibatch_worker_rows_zh.md"
)
DEFAULT_AB_AUDIT_SUMMARY: Path | None = None
DEFAULT_REACHABILITY_SUMMARY: Path | None = None
REQUIRED_WORKER_CONTEXT_FIELDS = (
    "expected_context_hash",
    "true_dual_hash",
    "cut_hash",
    "branch_hash",
    "forbidden_signature_hash",
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                rows.append(event)
    return rows


def _jsonl_files(root: Path) -> list[Path]:
    path = Path(root)
    if path.is_file() and path.suffix == ".jsonl":
        return [path]
    if path.exists():
        return sorted(path.glob("**/*.jsonl"))
    return []


def _int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _float_value(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _finite_record_float(record: dict[str, Any] | None, key: str, default: float = 0.0) -> float:
    if not record:
        return float(default)
    try:
        value = float(record.get(key))
    except (TypeError, ValueError):
        return float(default)
    if value != value or value in (float("inf"), float("-inf")):
        return float(default)
    return float(value)


def _event_key(event: dict[str, Any], *, pricing_kind: str | None = None) -> tuple[int, str, int, int]:
    return (
        _int_value(event.get("cg_iter"), -1),
        str(pricing_kind if pricing_kind is not None else event.get("pricing_kind") or ""),
        _int_value(event.get("node_id"), 0),
        _int_value(event.get("depth"), 0),
    )


def _target_sequence(value: Any) -> tuple[int, ...]:
    if not isinstance(value, list):
        return tuple()
    result: list[int] = []
    for item in value:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            return tuple()
    return tuple(result)


def _load_ab_audit_records(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    audit_path = Path(path)
    if not audit_path.exists():
        return {}
    summary = json.loads(audit_path.read_text(encoding="utf-8"))
    if summary.get("certificate_ready") or summary.get("official_bound_effect"):
        raise ValueError(f"A/B audit summary has forbidden certificate effect: {audit_path}")
    records: dict[str, dict[str, Any]] = {}
    for record in summary.get("records") or []:
        if not isinstance(record, dict):
            continue
        name = str(record.get("name") or "")
        worker_csv = str(record.get("worker_csv") or "")
        if name:
            records[name] = record
        if worker_csv:
            records[worker_csv] = record
    return records


def _ab_audit_record_for_candidate(
    candidate: dict[str, Any],
    records: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    for key in (str(candidate.get("name") or ""), str(candidate.get("worker_csv") or "")):
        record = records.get(key)
        if record is not None:
            return record
    return None


def _load_reachability_records(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    reachability_path = Path(path)
    if not reachability_path.exists():
        return {}
    summary = json.loads(reachability_path.read_text(encoding="utf-8"))
    if summary.get("certificate_ready") or summary.get("official_bound_effect"):
        raise ValueError(
            f"reachability summary has forbidden certificate effect: {reachability_path}"
        )
    records: dict[str, dict[str, Any]] = {}
    for record in summary.get("records") or []:
        if not isinstance(record, dict):
            continue
        name = str(record.get("name") or "")
        worker_csv = str(record.get("worker_csv") or "")
        if name:
            records[name] = record
        if worker_csv:
            records[worker_csv] = record
    return records


def _reachability_record_for_candidate(
    candidate: dict[str, Any],
    records: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    for key in (str(candidate.get("name") or ""), str(candidate.get("worker_csv") or "")):
        record = records.get(key)
        if record is not None:
            return record
    return None


def _trajectory_roi_label(record: dict[str, Any]) -> float:
    roi_class = str(record.get("roi_class") or "")
    if roi_class == "no_observed_roi":
        return 0.0
    primal = _finite_record_float(record, "primal_improvement")
    exact_delta = _finite_record_float(record, "exact_pricing_calls_delta")
    pricing_delta = _finite_record_float(record, "pricing_calls_delta")
    rmp_delta = _finite_record_float(record, "rmp_solves_delta")
    generated_delta = _finite_record_float(record, "generated_sequences_delta")
    time_delta = _finite_record_float(record, "solving_time_delta")
    value = float(primal)
    value += max(0.0, -exact_delta) * 1.0 - max(0.0, exact_delta) * 1.0
    value += max(0.0, -pricing_delta) * 0.25 - max(0.0, pricing_delta) * 0.25
    value += max(0.0, -rmp_delta) * 0.25 - max(0.0, rmp_delta) * 0.25
    value += max(0.0, -generated_delta) / 10000.0 - max(0.0, generated_delta) / 10000.0
    value += max(0.0, -time_delta) * 0.05 - max(0.0, time_delta) * 0.05
    if roi_class.startswith("positive_") and value <= 0.0:
        return 1.0
    if roi_class.startswith("negative_") and value >= 0.0:
        return -1.0
    return float(value)


def _capture_events_by_context(path: Path) -> dict[str, dict[str, Any]]:
    events: dict[str, dict[str, Any]] = {}
    for event in _read_jsonl(path):
        if event.get("event") != "journey_counterfactual_replay_capture":
            continue
        context_hash = str(event.get("context_hash") or "")
        if context_hash:
            events[context_hash] = event
    return events


def _worker_log_dir(candidate: dict[str, Any]) -> Path:
    worker_csv = Path(str(candidate.get("worker_csv") or ""))
    if worker_csv.name:
        return worker_csv.parent / "logs"
    return Path("")


def _load_worker_events(candidate: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    log_dir = _worker_log_dir(candidate)
    files = _jsonl_files(log_dir)
    events: list[dict[str, Any]] = []
    for path in files:
        events.extend(_read_jsonl(path))
    return events, [str(path) for path in files]


def _matching_worker_event(
    events: Iterable[dict[str, Any]],
    candidate: dict[str, Any],
) -> dict[str, Any] | None:
    expected_context = str(candidate.get("expected_context_hash") or "")
    target_sequence = _target_sequence(candidate.get("target_sequence") or [])
    matches: list[dict[str, Any]] = []
    for event in events:
        if event.get("event") != "journey_sharded_pulse_hidden_negative_worker":
            continue
        if bool(event.get("pulse_worker_skipped")):
            continue
        if str(event.get("pulse_worker_context_hash") or "") != expected_context:
            continue
        if not bool(event.get("pulse_worker_target_sequence_materialized")):
            continue
        if not bool(event.get("pulse_worker_target_sequence_negative")):
            continue
        if _int_value(event.get("pulse_worker_returned_journeys")) <= 0:
            continue
        event_sequence = _target_sequence(event.get("pulse_worker_target_sequence") or [])
        if target_sequence and event_sequence and event_sequence != target_sequence:
            continue
        matches.append(event)
    if not matches:
        return None
    matches.sort(key=lambda item: (_int_value(item.get("cg_iter")), _int_value(item.get("node_id")), _int_value(item.get("depth"))))
    return matches[0]


def _rmp_events(events: Iterable[dict[str, Any]]) -> dict[tuple[int, int, int], dict[str, Any]]:
    result: dict[tuple[int, int, int], dict[str, Any]] = {}
    for event in events:
        if event.get("event") != "journey_rmp":
            continue
        result[(
            _int_value(event.get("cg_iter"), -1),
            _int_value(event.get("node_id"), 0),
            _int_value(event.get("depth"), 0),
        )] = event
    return result


def _addition_events(events: Iterable[dict[str, Any]]) -> dict[tuple[int, str, int, int], dict[str, Any]]:
    result: dict[tuple[int, str, int, int], dict[str, Any]] = {}
    for event in events:
        if event.get("event") != "journey_column_addition":
            continue
        result[_event_key(event)] = event
    return result


def _instance_region(instance_path: str, instance: str) -> str:
    text = str(instance_path or instance or "")
    lowered = text.lower()
    if "tranquillitatis" in lowered:
        return "tranquillitatis_balmer_like_20km"
    if "apollo" in lowered:
        return "apollo15_20km"
    return "unknown"


def _row_from_candidate(
    candidate: dict[str, Any],
    *,
    capture: dict[str, Any],
    worker: dict[str, Any],
    addition: dict[str, Any],
    before_rmp: dict[str, Any],
    after_rmp: dict[str, Any],
    worker_log_files: list[str],
    ab_audit_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    objective_before = _float_value(before_rmp.get("objective"))
    objective_after = _float_value(after_rmp.get("objective"))
    objective_delta = objective_after - objective_before
    objective_improvement = objective_before - objective_after
    added = _int_value(addition.get("added_journeys"), 0)
    source_file = str(candidate.get("source_file") or "")
    instance_path = str(capture.get("instance_path") or candidate.get("instance") or "")
    signature_samples = [
        str(sample)
        for sample in (worker.get("pulse_worker_returned_candidate_signature_samples") or [])
        if str(sample)
    ]
    sequence_samples = list(worker.get("pulse_worker_returned_candidate_sequence_samples") or [])
    task_set_samples = list(worker.get("pulse_worker_returned_candidate_task_set_samples") or [])
    row = {
        "schema_version": "gat_same_run_batch_impact_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "source_file": source_file,
        "worker_source_files": worker_log_files,
        "instance": str(capture.get("instance") or Path(instance_path).stem),
        "instance_path": instance_path,
        "instance_region": _instance_region(instance_path, str(capture.get("instance") or "")),
        "cg_iter": _int_value(capture.get("cg_iter"), -1),
        "node_id": _int_value(capture.get("node_id"), 0),
        "depth": _int_value(capture.get("depth"), 0),
        "pricing_kind": str(capture.get("pricing_kind") or ""),
        "context_hash": str(candidate.get("expected_context_hash") or capture.get("context_hash") or ""),
        "true_dual_hash": str(capture.get("true_dual_hash") or ""),
        "cut_hash": str(capture.get("cut_hash") or ""),
        "branch_hash": str(capture.get("branch_hash") or ""),
        "forbidden_signature_hash": str(capture.get("forbidden_signature_hash") or ""),
        "returned_journey_count": int(len(signature_samples) or _int_value(worker.get("pulse_worker_returned_journeys"), 1)),
        "added_journeys": int(added),
        "new_journeys": _int_value(addition.get("new_journeys"), added),
        "replacement_journeys": _int_value(addition.get("replacement_journeys"), 0),
        "new_task_set_count": _int_value(addition.get("new_task_set_count"), 0),
        "replacement_task_set_count": _int_value(addition.get("replacement_task_set_count"), 0),
        "active_changed_task_set_count": _int_value(addition.get("active_changed_task_set_count"), 0),
        "addition_productivity_class": str(addition.get("addition_productivity_class") or ""),
        "best_true_reduced_cost": _float_value(
            worker.get("pulse_worker_best_rc"),
            _float_value(candidate.get("best_true_reduced_cost")),
        ),
        "objective_before": objective_before,
        "objective_after": objective_after,
        "objective_delta": objective_delta,
        "objective_improvement": objective_improvement,
        "label_objective_improved": int(objective_improvement > 1.0e-9),
        "label_active_support_changing": int(_int_value(addition.get("active_changed_task_set_count")) > 0),
        "label_new_task_set_added": int(_int_value(addition.get("new_task_set_count")) > 0),
        "same_run_intervention_observed": False,
        "same_context_target_intervention_observed": True,
        "worker_target_causal_match": True,
        "training_label_allowed": True,
        "training_label_scope": "same_context_target_materialization_worker",
        "target_candidate_name": str(candidate.get("name") or ""),
        "target_sequence": list(candidate.get("target_sequence") or []),
        "target_batch_sequences": list(candidate.get("candidate_batch_target_sequences") or []),
        "target_sortie_traces": list(candidate.get("target_sortie_traces") or []),
        "target_arc_option_sequence": list(candidate.get("target_arc_option_sequence") or []),
        "target_signature_samples": signature_samples,
        "worker_returned_candidate_signature_samples": signature_samples,
        "worker_returned_candidate_sequence_samples": sequence_samples,
        "worker_returned_candidate_task_set_samples": task_set_samples,
        "worker_cg_iter": _int_value(worker.get("cg_iter"), -1),
        "worker_pricing_kind": "sharded_pulse_hidden_negative_worker",
        "worker_context_hash": str(worker.get("pulse_worker_context_hash") or ""),
        "worker_target_sequence_materialized": bool(worker.get("pulse_worker_target_sequence_materialized")),
        "worker_target_sequence_negative": bool(worker.get("pulse_worker_target_sequence_negative")),
    }
    if ab_audit_record is not None:
        roi_class = str(ab_audit_record.get("roi_class") or "")
        trajectory_roi = _trajectory_roi_label(ab_audit_record)
        exact_delta = _finite_record_float(ab_audit_record, "exact_pricing_calls_delta")
        pricing_delta = _finite_record_float(ab_audit_record, "pricing_calls_delta")
        rmp_delta = _finite_record_float(ab_audit_record, "rmp_solves_delta")
        generated_delta = _finite_record_float(ab_audit_record, "generated_sequences_delta")
        time_delta = _finite_record_float(ab_audit_record, "solving_time_delta")
        label_positive = int(roi_class.startswith("positive_") and trajectory_roi > 0.0)
        label_bad_mode = int(
            roi_class.startswith("negative_")
            or (
                roi_class == "no_observed_roi"
                and (exact_delta > 0.0 or pricing_delta > 0.0 or rmp_delta > 0.0)
            )
        )
        row.update(
            {
                "ab_audit_summary_used": True,
                "ab_audit_roi_class": roi_class,
                "accepted_batch_roi_label": trajectory_roi,
                "trajectory_accepted_batch_roi": trajectory_roi,
                "label_batch_roi_positive": label_positive,
                "label_bad_mode_switch": label_bad_mode,
                "label_tail_improved": int(exact_delta < 0.0 or pricing_delta < 0.0),
                "final_judge_retry_delta": exact_delta,
                "pricing_tail_retry_delta": pricing_delta,
                "pricing_calls_delta": pricing_delta,
                "rmp_solves_delta": rmp_delta,
                "generated_sequences_delta": generated_delta,
                "solving_time_delta": time_delta,
                "delta_v_label": -trajectory_roi,
                "barrier_slack_label": trajectory_roi,
            }
        )
    else:
        row["ab_audit_summary_used"] = False
    return row


def build_rows(
    *,
    runbook_summary: Path = DEFAULT_RUNBOOK_SUMMARY,
    ab_audit_summary: Path | None = DEFAULT_AB_AUDIT_SUMMARY,
    reachability_summary: Path | None = DEFAULT_REACHABILITY_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = json.loads(Path(runbook_summary).read_text(encoding="utf-8"))
    if summary.get("certificate_ready") or summary.get("official_bound_effect"):
        raise ValueError(f"runbook summary has forbidden certificate effect: {runbook_summary}")
    candidates = [dict(item) for item in (summary.get("candidate_runs") or [])]
    ab_audit_records = _load_ab_audit_records(ab_audit_summary)
    reachability_records = _load_reachability_records(reachability_summary)
    capture_cache: dict[str, dict[str, dict[str, Any]]] = {}
    rows: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    ab_audit_matched = 0
    reachability_allowed = 0

    for candidate in candidates:
        reachability_record = _reachability_record_for_candidate(candidate, reachability_records)
        if reachability_records and reachability_record is None:
            skipped["missing_reachability_record"] += 1
            continue
        if reachability_record is not None and not bool(
            reachability_record.get("training_label_allowed")
        ):
            skipped["reachability_not_training_label"] += 1
            continue
        if reachability_record is not None:
            reachability_allowed += 1
        ab_audit_record = _ab_audit_record_for_candidate(candidate, ab_audit_records)
        if ab_audit_records and ab_audit_record is None:
            skipped["missing_ab_audit_record"] += 1
            continue
        if ab_audit_record is not None:
            ab_audit_matched += 1
        source_file = Path(str(candidate.get("source_file") or ""))
        context_hash = str(candidate.get("expected_context_hash") or "")
        if not source_file.exists():
            skipped["missing_original_capture_source"] += 1
            continue
        captures = capture_cache.get(str(source_file))
        if captures is None:
            captures = _capture_events_by_context(source_file)
            capture_cache[str(source_file)] = captures
        capture = captures.get(context_hash)
        if capture is None:
            skipped["missing_original_capture_context"] += 1
            continue
        events, worker_log_files = _load_worker_events(candidate)
        if not events:
            skipped["missing_worker_logs"] += 1
            continue
        worker = _matching_worker_event(events, candidate)
        if worker is None:
            skipped["missing_target_materialized_worker_event"] += 1
            continue
        missing_context = [
            field
            for field in REQUIRED_WORKER_CONTEXT_FIELDS
            if field != "expected_context_hash"
            and str(candidate.get(field) or "")
            and str(worker.get(f"pulse_worker_{field.replace('_hash', '')}_hash") or "")
            and str(candidate.get(field) or "") != str(worker.get(f"pulse_worker_{field.replace('_hash', '')}_hash") or "")
        ]
        if missing_context:
            skipped["worker_context_hash_mismatch"] += 1
            continue
        additions = _addition_events(events)
        worker_key = _event_key(worker, pricing_kind="sharded_pulse_hidden_negative_worker")
        addition = additions.get(worker_key)
        if addition is None or _int_value(addition.get("added_journeys")) <= 0:
            skipped["missing_positive_worker_column_addition"] += 1
            continue
        rmps = _rmp_events(events)
        cg_iter, _, node_id, depth = worker_key
        before = rmps.get((cg_iter, node_id, depth))
        after = rmps.get((cg_iter + 1, node_id, depth))
        if before is None or after is None:
            skipped["missing_worker_before_or_after_rmp"] += 1
            continue
        rows.append(
            _row_from_candidate(
                candidate,
                capture=capture,
                worker=worker,
                addition=addition,
                before_rmp=before,
                after_rmp=after,
                worker_log_files=worker_log_files,
                ab_audit_record=ab_audit_record,
            )
        )

    row_jsonl = output_dir / "same_context_target_worker_batch_impact_rows.jsonl"
    row_jsonl.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )
    context_counts = Counter(str(row.get("context_hash") or "") for row in rows)
    positive_count = sum(1 for row in rows if int(row.get("label_objective_improved") or 0))
    nonpositive_count = len(rows) - positive_count
    trajectory_positive_count = sum(
        1
        for row in rows
        if int(row.get("label_batch_roi_positive", row.get("label_objective_improved")) or 0)
    )
    trajectory_nonpositive_count = len(rows) - trajectory_positive_count
    roi_class_counts = Counter(str(row.get("ab_audit_roi_class") or "not_audited") for row in rows)
    signature_sample_rows = sum(1 for row in rows if row.get("target_signature_samples"))
    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "no_certificate_effect": all(not row["certificate_effect"] for row in rows),
        "no_official_bound_effect": all(not row["official_bound_effect"] for row in rows),
        "has_rows": bool(rows),
        "all_rows_have_worker_target_causal_match": all(row["worker_target_causal_match"] for row in rows),
        "has_same_context_pairs": any(count >= 2 for count in context_counts.values()),
        "ab_audit_records_match_rows": (
            True if not ab_audit_records else ab_audit_matched == len(rows) and len(rows) > 0
        ),
    }
    result = {
        "schema_version": "gat_multibatch_worker_batch_impact_rows_summary_v1",
        "status": "built" if rows else "no_rows",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "runbook_summary": str(runbook_summary),
        "ab_audit_summary": str(ab_audit_summary) if ab_audit_summary else "",
        "reachability_summary": str(reachability_summary) if reachability_summary else "",
        "ab_audit_record_count": len({id(record) for record in ab_audit_records.values()}) if ab_audit_records else 0,
        "ab_audit_matched_row_count": int(ab_audit_matched),
        "reachability_record_count": len({id(record) for record in reachability_records.values()}) if reachability_records else 0,
        "reachability_allowed_candidate_count": int(reachability_allowed),
        "candidate_count": len(candidates),
        "row_count": len(rows),
        "positive_objective_improvement_count": int(positive_count),
        "non_improving_objective_count": int(nonpositive_count),
        "positive_trajectory_roi_count": int(trajectory_positive_count),
        "nonpositive_trajectory_roi_count": int(trajectory_nonpositive_count),
        "roi_class_counts": dict(sorted(roi_class_counts.items())),
        "signature_sample_row_count": int(signature_sample_rows),
        "context_count": len(context_counts),
        "pairwise_context_count": sum(1 for count in context_counts.values() if count >= 2),
        "largest_context_size": max(context_counts.values()) if context_counts else 0,
        "skipped_counts": dict(sorted(skipped.items())),
        "jsonl_path": str(row_jsonl),
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), result)
    return result


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Multi-Batch Worker Batch-Impact Rows 报告",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把 guarded target-materialization worker A/B 的日志转换成 Stage 3 可用的",
        "same-context target intervention rows。只有 expected context 命中、target materialized、",
        "同 stage 发生 column addition、并且下一轮 RMP 可见时，才允许输出训练 row。",
        "",
        "该脚本只读日志，不运行 BPC / pricing / RMP / worker，不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_multibatch_worker_batch_impact_rows = current",
        f"status = {summary['status']}",
        f"candidate_count = {summary['candidate_count']}",
        f"row_count = {summary['row_count']}",
        f"positive_objective_improvement_count = {summary['positive_objective_improvement_count']}",
        f"non_improving_objective_count = {summary['non_improving_objective_count']}",
        f"positive_trajectory_roi_count = {summary['positive_trajectory_roi_count']}",
        f"nonpositive_trajectory_roi_count = {summary['nonpositive_trajectory_roi_count']}",
        f"roi_class_counts = {summary['roi_class_counts']}",
        f"signature_sample_row_count = {summary['signature_sample_row_count']}",
        f"context_count = {summary['context_count']}",
        f"pairwise_context_count = {summary['pairwise_context_count']}",
        f"largest_context_size = {summary['largest_context_size']}",
        f"reachability_record_count = {summary['reachability_record_count']}",
        f"reachability_allowed_candidate_count = {summary['reachability_allowed_candidate_count']}",
        f"skipped_counts = {summary['skipped_counts']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 边界",
        "",
        "- CSV-level ROI 不能直接变成训练标签；必须有 worker target causal match；",
        "- 如果提供 A/B audit summary，最终 trajectory ROI 覆盖即时 RMP objective 标签；",
        "- batch target row 必须带 worker returned signature samples，避免把 batch8 退化成单列标签；",
        "- target materialization 只说明该负列被找到并加入，不说明 no-negative closure；",
        "- 输出 row 仍是 diagnostic-only，后续 dataset/training/checkpoint 也必须保持 production_ready=false；",
        "- 最终 certificate 仍只能来自当前 branch/cut/dual 的 full exact pricing closure。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runbook-summary", type=Path, default=DEFAULT_RUNBOOK_SUMMARY)
    parser.add_argument("--ab-audit-summary", type=Path, default=DEFAULT_AB_AUDIT_SUMMARY)
    parser.add_argument("--reachability-summary", type=Path, default=DEFAULT_REACHABILITY_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = build_rows(
        runbook_summary=args.runbook_summary,
        ab_audit_summary=args.ab_audit_summary,
        reachability_summary=args.reachability_summary,
        output_dir=args.output_dir,
        report=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
