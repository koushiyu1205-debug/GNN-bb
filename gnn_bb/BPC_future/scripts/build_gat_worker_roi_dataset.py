#!/usr/bin/env python3
"""Build ROI labels for GAT target-priority worker candidates.

This is an offline bridge from audited target-priority worker A/B runs to a
second-stage GAT productivity dataset.  It is read-only: it consumes existing
audit/candidate JSON, writes labels, and never runs BPC, pricing, RMP, workers,
or certificates.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


DEFAULT_AUDIT_SUMMARY = Path(
    "BPC_future/results/gat_target_priority_worker_ab_audit_20260614/summary.json"
)
DEFAULT_CANDIDATE_SUMMARIES = (
    Path("BPC_future/results/gat_target_priority_candidates_20260614/summary.json"),
    Path("BPC_future/results/gat_target_priority_candidates_20roi_smoke_20260614/summary.json"),
    Path("BPC_future/results/gat_target_priority_candidates_family_20260614/summary.json"),
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_worker_roi_dataset_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_gat_worker_roi_dataset_zh.md"
)


POSITIVE_ROI_CLASSES = {
    "positive_exact_roi",
    "positive_primal_roi",
    "positive_status_roi",
    "positive_retry_roi",
    "positive_pricing_roi",
}
TRAINING_NEGATIVE_ROI_CLASSES = {
    "negative_exact_roi",
    "negative_walltime_roi",
    "no_observed_roi",
    "negative_primal_roi",
    "negative_status_roi",
    "negative_retry_roi",
}
TRAINABLE_ROI_CLASSES = POSITIVE_ROI_CLASSES | TRAINING_NEGATIVE_ROI_CLASSES


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _seq_key(value: Any) -> tuple[int, ...]:
    if not isinstance(value, list):
        return tuple()
    result: list[int] = []
    for item in value:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            return tuple()
    return tuple(result)


def _arc_key(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return tuple()
    return tuple(str(item) for item in value)


def _candidate_key(item: dict[str, Any]) -> tuple[str, str, tuple[int, ...], tuple[str, ...]]:
    return (
        str(item.get("instance") or ""),
        str(item.get("expected_context_hash") or ""),
        _seq_key(item.get("target_sequence")),
        _arc_key(item.get("target_arc_option_sequence")),
    )


def _candidate_sequence_key(item: dict[str, Any]) -> tuple[str, str, tuple[int, ...]]:
    return (
        str(item.get("instance") or ""),
        str(item.get("expected_context_hash") or ""),
        _seq_key(item.get("target_sequence")),
    )


def _candidate_key_string(item: dict[str, Any]) -> str:
    instance, context_hash, sequence, arcs = _candidate_key(item)
    return "|".join(
        (
            instance,
            context_hash,
            ",".join(str(task) for task in sequence),
            ",".join(arcs),
        )
    )


def _instance_family(instance: str) -> str:
    parts = Path(str(instance)).parts
    for idx, part in enumerate(parts):
        if part.startswith("tasks_") and idx + 1 < len(parts):
            return str(parts[idx + 1])
    return "unknown"


def _instance_region(instance: str) -> str:
    parts = Path(str(instance)).parts
    for idx, part in enumerate(parts):
        if part.startswith("tasks_") and idx + 2 < len(parts):
            return str(parts[idx + 2])
    return "unknown"


def _max_group_fraction(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    counts = Counter(str(row.get(key) or "") for row in rows)
    return max(counts.values()) / float(len(rows))


def _threshold_gap(name: str, observed: int | float, required: int | float) -> dict[str, Any] | None:
    if observed >= required:
        return None
    return {
        "name": name,
        "observed": observed,
        "required": required,
        "missing": required - observed,
    }


def _fraction_gap(name: str, observed: float, required_max: float) -> dict[str, Any] | None:
    if observed <= required_max:
        return None
    return {
        "name": name,
        "observed": observed,
        "required_max": required_max,
        "excess": observed - required_max,
    }


def _load_candidate_features(
    paths: Iterable[Path],
) -> dict[str, dict[tuple[Any, ...], dict[str, Any]]]:
    features: dict[tuple[str, str, tuple[int, ...], tuple[str, ...]], dict[str, Any]] = {}
    sequence_features: dict[tuple[str, str, tuple[int, ...]], dict[str, Any]] = {}
    for source in paths:
        path = Path(source)
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        candidates = payload.get("candidates") or payload.get("candidate_runs")
        if candidates is None and (path.parent / "candidates.json").exists():
            candidates = json.loads((path.parent / "candidates.json").read_text(encoding="utf-8")).get("candidates")
        for candidate in candidates or []:
            if not isinstance(candidate, dict):
                continue
            key = _candidate_key(candidate)
            if key[0] and key[1] and key[2]:
                features.setdefault(key, dict(candidate))
                sequence_features.setdefault(_candidate_sequence_key(candidate), dict(candidate))
    return {"exact": features, "sequence": sequence_features}


def _candidate_lookup(
    record: dict[str, Any],
    candidate_features: dict[str, dict[tuple[Any, ...], dict[str, Any]]],
) -> dict[str, Any]:
    exact = candidate_features.get("exact", {})
    sequence = candidate_features.get("sequence", {})
    candidate = exact.get(_candidate_key(record))
    if candidate is not None:
        return candidate
    candidate = sequence.get(_candidate_sequence_key(record))
    if candidate is not None:
        return candidate
    for target_sequence in _target_sequence_candidates(record):
        key = (
            str(record.get("instance") or ""),
            str(record.get("expected_context_hash") or ""),
            _seq_key(target_sequence),
        )
        candidate = sequence.get(key)
        if candidate is not None:
            return candidate
    return {}


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _result_csv_exists(record: dict[str, Any], flag_key: str, path_key: str) -> bool:
    if bool(record.get(flag_key)):
        return True
    path_text = str(record.get(path_key) or "").strip()
    return bool(path_text and Path(path_text).exists())


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _sequence_tuple(value: Any) -> tuple[int, ...]:
    if not isinstance(value, list):
        return tuple()
    try:
        return tuple(int(item) for item in value)
    except (TypeError, ValueError):
        return tuple()


def _target_sequence_candidates(record: dict[str, Any]) -> list[list[Any]]:
    candidates: list[list[Any]] = []
    primary = record.get("target_sequence")
    if isinstance(primary, list):
        candidates.append(primary)
    for key in ("candidate_batch_target_sequences", "target_sequences"):
        value = record.get(key)
        if not isinstance(value, list):
            continue
        for sequence in value:
            if isinstance(sequence, list):
                candidates.append(sequence)
    unique: list[list[Any]] = []
    seen: set[tuple[int, ...]] = set()
    for sequence in candidates:
        seq_key = _sequence_tuple(sequence)
        if not seq_key or seq_key in seen:
            continue
        seen.add(seq_key)
        unique.append(sequence)
    return unique


def _sequence_sample_matches_target(samples: Any, target: tuple[int, ...]) -> bool:
    if not target or not isinstance(samples, list):
        return False
    for sample in samples:
        if isinstance(sample, list) and sample and all(isinstance(item, list) for item in sample):
            flattened: list[int] = []
            for sortie in sample:
                for task in sortie:
                    try:
                        flattened.append(int(task))
                    except (TypeError, ValueError):
                        flattened = []
                        break
                if not flattened and sortie:
                    break
            if tuple(flattened) == target:
                return True
        elif _sequence_tuple(sample) == target:
            return True
    return False


def _worker_target_diagnostics(
    worker_csv: Any,
    *,
    expected_context_hash: Any = "",
) -> dict[str, Any]:
    worker_csv_text = str(worker_csv or "").strip()
    if not worker_csv_text:
        return {}
    path = Path(worker_csv_text)
    log_dir = path.parent / "logs"
    if not log_dir.exists():
        return {}
    events: list[dict[str, Any]] = []
    for log_path in sorted(log_dir.glob("**/*.jsonl")):
        with log_path.open(encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                text = line.strip()
                if not text or "pulse_worker_" not in text:
                    continue
                try:
                    event = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict) or not event.get("pulse_worker_enabled"):
                    continue
                events.append(event)
    if not events:
        return {}
    expected = str(expected_context_hash or "").strip()
    best = events[-1]
    if expected:
        for event in events:
            if str(event.get("pulse_worker_context_hash") or "").strip() == expected:
                best = event
                break
    keys = [
        "pulse_worker_target_first_task_priority_enabled",
        "pulse_worker_enabled",
        "pulse_worker_skipped",
        "pulse_worker_skip_reason",
        "pulse_worker_status",
        "pulse_worker_signal_source",
        "pulse_worker_target_first_task_priority_sequence",
        "pulse_worker_target_transition_priority_enabled",
        "pulse_worker_target_transition_priority_sequence",
        "pulse_worker_target_arc_option_priority_enabled",
        "pulse_worker_target_arc_option_priority_sequence",
        "pulse_worker_target_sequence_completed",
        "pulse_worker_target_sequence_materialized",
        "pulse_worker_target_sequence_negative",
        "pulse_worker_target_sequence_reached_prefix_len",
        "pulse_worker_target_sequence_blocked_reason",
        "pulse_worker_harvested_sequence_samples",
        "pulse_worker_returned_candidate_sequence_samples",
        "pulse_worker_harvested_task_set_samples",
        "pulse_worker_returned_journeys",
        "pulse_worker_best_rc",
        "pulse_worker_context_hash",
    ]
    return {key: best.get(key) for key in keys if key in best}


def _target_causal_match(
    *,
    target_sequence: list[Any],
    target_sequences: list[list[Any]] | None = None,
    worker_diag: dict[str, Any],
) -> bool:
    targets = [_sequence_tuple(sequence) for sequence in (target_sequences or [target_sequence])]
    targets = [target for target in targets if target]
    if not targets or not worker_diag:
        return False
    for target in targets:
        configured_target_match = any(
            _sequence_tuple(worker_diag.get(key)) == target
            for key in (
                "pulse_worker_target_first_task_priority_sequence",
                "pulse_worker_target_transition_priority_sequence",
                "pulse_worker_target_arc_option_priority_sequence",
            )
        )
        if configured_target_match and bool(worker_diag.get("pulse_worker_target_sequence_materialized")):
            return True
        if (
            _sequence_sample_matches_target(
                worker_diag.get("pulse_worker_returned_candidate_sequence_samples"),
                target,
            )
            or _sequence_sample_matches_target(
                worker_diag.get("pulse_worker_harvested_sequence_samples"),
                target,
            )
        ):
            return True
    return False


def _worker_target_intervention_observed(worker_diag: dict[str, Any]) -> bool:
    if not worker_diag:
        return False
    if bool(worker_diag.get("pulse_worker_skipped", False)):
        return False
    return bool(worker_diag.get("pulse_worker_enabled", True))


def _worker_context_match(
    *,
    expected_context_hash: Any,
    worker_diag: dict[str, Any],
) -> bool:
    expected = str(expected_context_hash or "").strip()
    observed = str(worker_diag.get("pulse_worker_context_hash") or "").strip()
    return bool(expected and observed and expected == observed)


def _worker_context_mismatch(
    *,
    expected_context_hash: Any,
    worker_diag: dict[str, Any],
) -> bool:
    expected = str(expected_context_hash or "").strip()
    observed = str(worker_diag.get("pulse_worker_context_hash") or "").strip()
    skip_reason = str(worker_diag.get("pulse_worker_skip_reason") or "").strip()
    if skip_reason == "residual_target_context_mismatch":
        return True
    return bool(expected and observed and expected != observed)


def _post_injection_guard_value(record: dict[str, Any], key: str) -> float | None:
    return _float_or_none(record.get(key))


def _post_injection_guard_present(record: dict[str, Any]) -> bool:
    return any(
        key in record
        for key in (
            "target_active_changed_task_set_count",
            "worker_next_objective_vs_baseline_same_iter_delta",
        )
    )


def _guarded_positive_trajectory_roi(
    record: dict[str, Any],
    *,
    roi_class: str,
) -> tuple[bool, str]:
    if roi_class not in POSITIVE_ROI_CLASSES:
        return False, "not_positive_roi_class"
    if not _post_injection_guard_present(record):
        return True, "legacy_roi_class_positive_no_post_injection_guard"

    active_changed = _post_injection_guard_value(
        record, "target_active_changed_task_set_count"
    )
    if active_changed is not None and active_changed <= 0.0:
        return False, "target_columns_inactive_only"

    same_iter_delta = _post_injection_guard_value(
        record, "worker_next_objective_vs_baseline_same_iter_delta"
    )
    if same_iter_delta is not None and same_iter_delta > 1.0e-9:
        return False, "worse_than_baseline_same_iter_objective"

    return True, "post_injection_guard_positive"


def _label_row(record: dict[str, Any], candidate: dict[str, Any] | None) -> dict[str, Any]:
    roi_class = str(record.get("roi_class") or record.get("final_roi_class") or "unknown")
    primal_improvement = _float_or_none(record.get("primal_improvement"))
    columns_delta = _float_or_none(record.get("columns_delta"))
    exact_delta = _float_or_none(record.get("exact_pricing_calls_delta"))
    generated_delta = _float_or_none(record.get("generated_sequences_delta"))
    target_active_changed = _float_or_none(record.get("target_active_changed_task_set_count"))
    target_inactive_changed = _float_or_none(record.get("target_inactive_changed_task_set_count"))
    worker_next_objective_delta = _float_or_none(record.get("worker_next_objective_delta"))
    worker_next_dual_l1_delta = _float_or_none(record.get("worker_next_dual_l1_delta"))
    worker_next_objective_vs_baseline = _float_or_none(
        record.get("worker_next_objective_vs_baseline_same_iter_delta")
    )
    worker_next_dual_l1_vs_baseline = _float_or_none(
        record.get("worker_next_dual_l1_vs_baseline_same_iter_delta")
    )
    followup_pricing_events = _float_or_none(record.get("worker_followup_pricing_events"))
    followup_exact_events = _float_or_none(record.get("worker_followup_exact_pricing_events"))
    followup_retry_events = _float_or_none(record.get("worker_followup_completion_retry_events"))
    context_mismatch_skips = _float_or_none(
        record.get("worker_context_mismatch_skips_after_injection")
    )
    target_sequence = list(record.get("target_sequence") or [])
    target_sequence_candidates = _target_sequence_candidates(record)
    arcs = list(record.get("target_arc_option_sequence") or [])
    baseline_result_exists = _result_csv_exists(record, "baseline_csv_exists", "baseline_csv")
    worker_result_exists = _result_csv_exists(record, "worker_csv_exists", "worker_csv")
    worker_columns_added = bool(columns_delta is not None and columns_delta > 0)
    positive_primal_roi = bool(primal_improvement is not None and primal_improvement > 1.0e-9)
    positive_trajectory_roi, positive_trajectory_roi_guard_reason = (
        _guarded_positive_trajectory_roi(record, roi_class=roi_class)
    )
    negative_primal_roi = bool(primal_improvement is not None and primal_improvement < -1.0e-9)
    trainable = bool(
        roi_class in TRAINABLE_ROI_CLASSES
        and baseline_result_exists
        and worker_result_exists
        and not record.get("official_bound_effect")
        and not record.get("certificate_effect")
    )
    worker_diag = _worker_target_diagnostics(
        record.get("worker_csv"),
        expected_context_hash=record.get("expected_context_hash"),
    )
    worker_context_match = _worker_context_match(
        expected_context_hash=record.get("expected_context_hash"),
        worker_diag=worker_diag,
    )
    worker_context_mismatch = _worker_context_mismatch(
        expected_context_hash=record.get("expected_context_hash"),
        worker_diag=worker_diag,
    )
    target_causal_match = _target_causal_match(
        target_sequence=target_sequence,
        target_sequences=target_sequence_candidates,
        worker_diag=worker_diag,
    )
    target_intervention_observed = _worker_target_intervention_observed(worker_diag)
    if trainable and not worker_context_match:
        trainable = False
    if trainable and not positive_trajectory_roi and not target_intervention_observed:
        trainable = False
    if trainable and not target_causal_match:
        trainable = False
    label = None
    if trainable:
        label = 1 if positive_trajectory_roi else 0
    candidate = candidate or {}
    return {
        "schema_version": "gat_worker_roi_dataset_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "instance": str(record.get("instance") or ""),
        "instance_family": _instance_family(str(record.get("instance") or "")),
        "instance_region": _instance_region(str(record.get("instance") or "")),
        "name": str(record.get("name") or ""),
        "expected_context_hash": str(record.get("expected_context_hash") or ""),
        "roi_candidate_key": _candidate_key_string(record),
        "target_sequence": target_sequence,
        "candidate_batch_target_sequences": target_sequence_candidates,
        "target_arc_option_sequence": arcs,
        "target_length": len(target_sequence),
        "target_arc_count": len(arcs),
        "decision_name": str(candidate.get("decision_name") or ""),
        "decision_probability": _float_or_none(candidate.get("decision_probability")),
        "decision_reason": str(candidate.get("decision_reason") or ""),
        "best_true_reduced_cost": _float_or_none(candidate.get("best_true_reduced_cost")),
        "capture_cg_iter": _int_or_zero(candidate.get("capture_cg_iter")),
        "capture_returned_journey_count": _int_or_zero(candidate.get("capture_returned_journey_count")),
        "source_file": str(candidate.get("source_file") or ""),
        "candidate_feature_joined": bool(candidate),
        "worker_target_diag_available": bool(worker_diag),
        "worker_context_hash": str(worker_diag.get("pulse_worker_context_hash") or ""),
        "worker_context_match": bool(worker_context_match),
        "worker_context_mismatch": bool(worker_context_mismatch),
        "worker_target_intervention_observed": bool(target_intervention_observed),
        "worker_target_skipped": bool(worker_diag.get("pulse_worker_skipped", False)),
        "worker_target_skip_reason": str(worker_diag.get("pulse_worker_skip_reason") or ""),
        "worker_target_status": str(worker_diag.get("pulse_worker_status") or ""),
        "worker_target_causal_match": bool(target_causal_match),
        "worker_target_sequence_materialized": bool(
            worker_diag.get("pulse_worker_target_sequence_materialized", False)
        ),
        "worker_target_sequence_negative": bool(
            worker_diag.get("pulse_worker_target_sequence_negative", False)
        ),
        "worker_target_sequence_reached_prefix_len": _int_or_zero(
            worker_diag.get("pulse_worker_target_sequence_reached_prefix_len")
        ),
        "worker_harvested_sequence_samples": worker_diag.get(
            "pulse_worker_harvested_sequence_samples", []
        ),
        "worker_returned_candidate_sequence_samples": worker_diag.get(
            "pulse_worker_returned_candidate_sequence_samples", []
        ),
        "baseline_status": str(record.get("baseline_status") or ""),
        "worker_status": str(record.get("worker_status") or ""),
        "baseline_primal": _float_or_none(record.get("baseline_primal")),
        "worker_primal": _float_or_none(record.get("worker_primal")),
        "primal_improvement": primal_improvement,
        "baseline_columns": _float_or_none(record.get("baseline_columns")),
        "worker_columns": _float_or_none(record.get("worker_columns")),
        "columns_delta": columns_delta,
        "exact_pricing_calls_delta": exact_delta,
        "generated_sequences_delta": generated_delta,
        "target_active_changed_task_set_count": target_active_changed,
        "target_inactive_changed_task_set_count": target_inactive_changed,
        "worker_next_objective_delta": worker_next_objective_delta,
        "worker_next_dual_l1_delta": worker_next_dual_l1_delta,
        "worker_next_objective_vs_baseline_same_iter_delta": (
            worker_next_objective_vs_baseline
        ),
        "worker_next_dual_l1_vs_baseline_same_iter_delta": (
            worker_next_dual_l1_vs_baseline
        ),
        "worker_followup_pricing_events": followup_pricing_events,
        "worker_followup_exact_pricing_events": followup_exact_events,
        "worker_followup_completion_retry_events": followup_retry_events,
        "worker_context_mismatch_skips_after_injection": context_mismatch_skips,
        "roi_class": roi_class,
        "label_worker_roi_positive": None if label is None else int(label),
        "label_worker_adds_columns": int(worker_columns_added),
        "label_positive_primal_roi": int(positive_primal_roi),
        "label_positive_trajectory_roi": int(positive_trajectory_roi),
        "positive_trajectory_roi_guard_reason": positive_trajectory_roi_guard_reason,
        "post_injection_guard_present": bool(_post_injection_guard_present(record)),
        "label_negative_primal_roi": int(negative_primal_roi),
        "training_eligible": bool(trainable),
        "training_exclusion_reason": ""
        if trainable
        else _exclusion_reason(
            record,
            roi_class,
            positive_primal_roi=positive_primal_roi,
            positive_trajectory_roi=positive_trajectory_roi,
            worker_context_match=worker_context_match,
            worker_context_mismatch=worker_context_mismatch,
            target_causal_match=target_causal_match,
            target_intervention_observed=target_intervention_observed,
            baseline_result_exists=baseline_result_exists,
            worker_result_exists=worker_result_exists,
        ),
    }


def _exclusion_reason(
    record: dict[str, Any],
    roi_class: str,
    *,
    positive_primal_roi: bool = False,
    positive_trajectory_roi: bool = False,
    worker_context_match: bool = False,
    worker_context_mismatch: bool = False,
    target_causal_match: bool = False,
    target_intervention_observed: bool = False,
    baseline_result_exists: bool = False,
    worker_result_exists: bool = False,
) -> str:
    if record.get("official_bound_effect") or record.get("certificate_effect"):
        return "forbidden_certificate_or_bound_effect"
    if not baseline_result_exists or not worker_result_exists:
        return "missing_ab_result"
    if roi_class not in TRAINABLE_ROI_CLASSES:
        return f"unsupported_roi_class:{roi_class}"
    if worker_context_mismatch:
        return "worker_context_mismatch"
    if not positive_primal_roi and not target_intervention_observed:
        return "no_worker_target_intervention_observed"
    if not worker_context_match:
        return "worker_context_mismatch"
    if positive_trajectory_roi and not target_causal_match:
        return "positive_roi_without_target_causal_match"
    if not target_causal_match:
        return "roi_without_target_causal_match"
    return "not_training_eligible"


def build_roi_dataset(
    *,
    audit_summary_path: Path = DEFAULT_AUDIT_SUMMARY,
    candidate_summary_paths: Iterable[Path] = DEFAULT_CANDIDATE_SUMMARIES,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    min_positive_for_training: int = 5,
    min_negative_for_training: int = 5,
    min_positive_instances_for_training: int = 2,
    min_negative_instances_for_training: int = 2,
    min_positive_families_for_training: int = 2,
    min_negative_families_for_training: int = 2,
    min_positive_regions_for_training: int = 2,
    min_negative_regions_for_training: int = 2,
    max_label_instance_fraction: float = 0.75,
) -> dict[str, Any]:
    audit_path = Path(audit_summary_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("official_bound_effect") or audit.get("certificate_ready"):
        raise ValueError(f"audit summary has forbidden certificate/bound effect: {audit_path}")
    candidate_features = _load_candidate_features(candidate_summary_paths)
    rows: list[dict[str, Any]] = []
    for record in audit.get("records") or []:
        if not isinstance(record, dict):
            continue
        rows.append(_label_row(record, _candidate_lookup(record, candidate_features)))

    duplicate_counts = Counter(row["roi_candidate_key"] for row in rows)
    for row in rows:
        row["duplicate_group_size"] = int(duplicate_counts[row["roi_candidate_key"]])
    training_rows = [row for row in rows if row["training_eligible"]]
    unique_training_rows: dict[str, dict[str, Any]] = {}
    for row in training_rows:
        unique_training_rows.setdefault(str(row["roi_candidate_key"]), row)
    unique_training_values = list(unique_training_rows.values())
    label_counts = Counter(
        str(row["label_worker_roi_positive"]) for row in training_rows if row["label_worker_roi_positive"] is not None
    )
    unique_label_counts = Counter(
        str(row["label_worker_roi_positive"])
        for row in unique_training_values
        if row["label_worker_roi_positive"] is not None
    )
    roi_counts = Counter(str(row["roi_class"]) for row in rows)
    joined_count = sum(1 for row in rows if row["candidate_feature_joined"])
    target_diag_available_count = sum(1 for row in rows if row["worker_target_diag_available"])
    worker_context_match_count = sum(1 for row in rows if row["worker_context_match"])
    target_causal_match_count = sum(1 for row in rows if row["worker_target_causal_match"])
    target_intervention_observed_count = sum(
        1 for row in rows if row["worker_target_intervention_observed"]
    )
    positive_roi_without_target_causal_match_count = sum(
        1
        for row in rows
        if row["training_exclusion_reason"] == "positive_roi_without_target_causal_match"
    )
    roi_without_target_causal_match_count = sum(
        1
        for row in rows
        if row["training_exclusion_reason"] == "roi_without_target_causal_match"
    )
    worker_context_mismatch_count = sum(
        1
        for row in rows
        if row["training_exclusion_reason"] == "worker_context_mismatch"
    )
    no_worker_target_intervention_count = sum(
        1
        for row in rows
        if row["training_exclusion_reason"] == "no_worker_target_intervention_observed"
    )
    positive_count = int(unique_label_counts.get("1", 0))
    negative_count = int(unique_label_counts.get("0", 0))
    unique_positive_rows = [
        row for row in unique_training_values if row["label_worker_roi_positive"] == 1
    ]
    unique_negative_rows = [
        row for row in unique_training_values if row["label_worker_roi_positive"] == 0
    ]
    positive_instance_count = len({str(row["instance"]) for row in unique_positive_rows})
    negative_instance_count = len({str(row["instance"]) for row in unique_negative_rows})
    positive_family_count = len({str(row["instance_family"]) for row in unique_positive_rows})
    negative_family_count = len({str(row["instance_family"]) for row in unique_negative_rows})
    positive_region_count = len({str(row["instance_region"]) for row in unique_positive_rows})
    negative_region_count = len({str(row["instance_region"]) for row in unique_negative_rows})
    positive_max_instance_fraction = _max_group_fraction(unique_positive_rows, "instance")
    negative_max_instance_fraction = _max_group_fraction(unique_negative_rows, "instance")
    positive_max_region_fraction = _max_group_fraction(unique_positive_rows, "instance_region")
    negative_max_region_fraction = _max_group_fraction(unique_negative_rows, "instance_region")
    training_exclusion_counts = Counter(
        str(row["training_exclusion_reason"])
        for row in rows
        if not row["training_eligible"] and row["training_exclusion_reason"]
    )
    positive_guard_reason_counts = Counter(
        str(row.get("positive_trajectory_roi_guard_reason") or "") for row in rows
    )
    post_injection_guard_present_count = sum(
        1 for row in rows if row.get("post_injection_guard_present")
    )
    post_injection_positive_downgraded_count = sum(
        1
        for row in rows
        if str(row.get("roi_class") or "") in POSITIVE_ROI_CLASSES
        and row.get("post_injection_guard_present")
        and row.get("label_positive_trajectory_roi") == 0
    )
    label_distribution_ready_details = {
        "positive_instances_ready": positive_instance_count >= int(min_positive_instances_for_training),
        "negative_instances_ready": negative_instance_count >= int(min_negative_instances_for_training),
        "positive_families_ready": positive_family_count >= int(min_positive_families_for_training),
        "negative_families_ready": negative_family_count >= int(min_negative_families_for_training),
        "positive_regions_ready": positive_region_count >= int(min_positive_regions_for_training),
        "negative_regions_ready": negative_region_count >= int(min_negative_regions_for_training),
        "positive_instance_fraction_ready": positive_max_instance_fraction <= float(max_label_instance_fraction),
        "negative_instance_fraction_ready": negative_max_instance_fraction <= float(max_label_instance_fraction),
    }
    label_distribution_ready = bool(
        positive_instance_count >= int(min_positive_instances_for_training)
        and negative_instance_count >= int(min_negative_instances_for_training)
        and positive_family_count >= int(min_positive_families_for_training)
        and negative_family_count >= int(min_negative_families_for_training)
        and positive_region_count >= int(min_positive_regions_for_training)
        and negative_region_count >= int(min_negative_regions_for_training)
        and positive_max_instance_fraction <= float(max_label_instance_fraction)
        and negative_max_instance_fraction <= float(max_label_instance_fraction)
    )
    training_ready = bool(
        positive_count >= int(min_positive_for_training)
        and negative_count >= int(min_negative_for_training)
        and label_distribution_ready
    )
    sample_collection_gaps = [
        gap
        for gap in (
            _threshold_gap("positive_training_label_count", positive_count, int(min_positive_for_training)),
            _threshold_gap("negative_training_label_count", negative_count, int(min_negative_for_training)),
            _threshold_gap("positive_instance_count", positive_instance_count, int(min_positive_instances_for_training)),
            _threshold_gap("negative_instance_count", negative_instance_count, int(min_negative_instances_for_training)),
            _threshold_gap("positive_family_count", positive_family_count, int(min_positive_families_for_training)),
            _threshold_gap("negative_family_count", negative_family_count, int(min_negative_families_for_training)),
            _threshold_gap("positive_region_count", positive_region_count, int(min_positive_regions_for_training)),
            _threshold_gap("negative_region_count", negative_region_count, int(min_negative_regions_for_training)),
            _fraction_gap("positive_max_instance_fraction", positive_max_instance_fraction, float(max_label_instance_fraction)),
            _fraction_gap("negative_max_instance_fraction", negative_max_instance_fraction, float(max_label_instance_fraction)),
        )
        if gap is not None
    ]
    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "no_certificate_effect": all(not row["certificate_effect"] for row in rows),
        "no_official_bound_effect": all(not row["official_bound_effect"] for row in rows),
        "has_rows": bool(rows),
        "has_training_rows": bool(training_rows),
        "has_positive_and_negative_training_labels": bool(positive_count > 0 and negative_count > 0),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "gat_worker_roi_rows.jsonl"
    csv_path = output_dir / "gat_worker_roi_rows.csv"
    _write_jsonl(jsonl_path, rows)
    _write_csv(csv_path, rows)
    summary = {
        "schema_version": "gat_worker_roi_dataset_summary_v1",
        "status": "built" if rows else "no_rows",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "audit_summary_path": str(audit_summary_path),
        "candidate_summary_paths": [str(path) for path in candidate_summary_paths],
        "jsonl_path": str(jsonl_path),
        "csv_path": str(csv_path),
        "row_count": len(rows),
        "training_row_count": len(training_rows),
        "unique_training_row_count": len(unique_training_values),
        "candidate_feature_joined_count": joined_count,
        "duplicate_candidate_count": sum(1 for count in duplicate_counts.values() if count > 1),
        "target_diag_available_count": target_diag_available_count,
        "worker_context_match_count": worker_context_match_count,
        "target_causal_match_count": target_causal_match_count,
        "target_intervention_observed_count": target_intervention_observed_count,
        "positive_roi_without_target_causal_match_count": positive_roi_without_target_causal_match_count,
        "roi_without_target_causal_match_count": roi_without_target_causal_match_count,
        "worker_context_mismatch_count": worker_context_mismatch_count,
        "no_worker_target_intervention_count": no_worker_target_intervention_count,
        "training_exclusion_reason_counts": dict(sorted(training_exclusion_counts.items())),
        "positive_trajectory_roi_guard_reason_counts": dict(
            sorted(positive_guard_reason_counts.items())
        ),
        "post_injection_guard_present_count": int(post_injection_guard_present_count),
        "post_injection_positive_downgraded_count": int(
            post_injection_positive_downgraded_count
        ),
        "label_counts": dict(sorted(label_counts.items())),
        "unique_label_counts": dict(sorted(unique_label_counts.items())),
        "roi_class_counts": dict(sorted(roi_counts.items())),
        "positive_training_label_count": positive_count,
        "negative_training_label_count": negative_count,
        "min_positive_for_training": int(min_positive_for_training),
        "min_negative_for_training": int(min_negative_for_training),
        "min_positive_instances_for_training": int(min_positive_instances_for_training),
        "min_negative_instances_for_training": int(min_negative_instances_for_training),
        "min_positive_families_for_training": int(min_positive_families_for_training),
        "min_negative_families_for_training": int(min_negative_families_for_training),
        "min_positive_regions_for_training": int(min_positive_regions_for_training),
        "min_negative_regions_for_training": int(min_negative_regions_for_training),
        "max_label_instance_fraction": float(max_label_instance_fraction),
        "positive_instance_count": positive_instance_count,
        "negative_instance_count": negative_instance_count,
        "positive_family_count": positive_family_count,
        "negative_family_count": negative_family_count,
        "positive_region_count": positive_region_count,
        "negative_region_count": negative_region_count,
        "positive_max_instance_fraction": positive_max_instance_fraction,
        "negative_max_instance_fraction": negative_max_instance_fraction,
        "positive_max_region_fraction": positive_max_region_fraction,
        "negative_max_region_fraction": negative_max_region_fraction,
        "positive_region_counts": dict(
            sorted(Counter(str(row["instance_region"]) for row in unique_positive_rows).items())
        ),
        "negative_region_counts": dict(
            sorted(Counter(str(row["instance_region"]) for row in unique_negative_rows).items())
        ),
        "label_distribution_ready_details": label_distribution_ready_details,
        "sample_collection_gaps": sample_collection_gaps,
        "label_distribution_ready": label_distribution_ready,
        "training_ready": training_ready,
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "next_decision": "train_roi_gate" if training_ready else "collect_more_roi_labels",
    }
    _json_dump(output_dir / "summary.json", summary)
    _write_report(report, summary, rows)
    return summary


def _write_report(path: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    examples = [
        {
            "name": row["name"],
            "roi_class": row["roi_class"],
            "label_worker_roi_positive": row["label_worker_roi_positive"],
            "primal_improvement": row["primal_improvement"],
            "columns_delta": row["columns_delta"],
            "decision_probability": row["decision_probability"],
            "best_true_reduced_cost": row["best_true_reduced_cost"],
        }
        for row in rows[:12]
    ]
    lines = [
        "# GAT Worker ROI Dataset 报告",
        "",
        "日期：2026-06-15",
        "",
        "## 目的",
        "",
        "把 target-priority worker A/B 审计结果转成第二阶段 GAT ROI 标签。",
        "该数据集用于学习“候选是否真的改变 RMP / primal 轨迹”，不是 pricing oracle，",
        "不运行 BPC / pricing / RMP / worker，也不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_worker_roi_dataset = current",
        f"status = {summary['status']}",
        f"row_count = {summary['row_count']}",
        f"training_row_count = {summary['training_row_count']}",
        f"unique_training_row_count = {summary['unique_training_row_count']}",
        f"target_diag_available_count = {summary['target_diag_available_count']}",
        f"worker_context_match_count = {summary['worker_context_match_count']}",
        f"target_causal_match_count = {summary['target_causal_match_count']}",
        f"target_intervention_observed_count = {summary['target_intervention_observed_count']}",
        "positive_roi_without_target_causal_match_count = "
        f"{summary['positive_roi_without_target_causal_match_count']}",
        "roi_without_target_causal_match_count = "
        f"{summary['roi_without_target_causal_match_count']}",
        f"worker_context_mismatch_count = {summary['worker_context_mismatch_count']}",
        f"no_worker_target_intervention_count = {summary['no_worker_target_intervention_count']}",
        f"training_exclusion_reason_counts = {summary['training_exclusion_reason_counts']}",
        "positive_trajectory_roi_guard_reason_counts = "
        f"{summary['positive_trajectory_roi_guard_reason_counts']}",
        "post_injection_guard_present_count = "
        f"{summary['post_injection_guard_present_count']}",
        "post_injection_positive_downgraded_count = "
        f"{summary['post_injection_positive_downgraded_count']}",
        f"label_counts = {summary['label_counts']}",
        f"unique_label_counts = {summary['unique_label_counts']}",
        f"roi_class_counts = {summary['roi_class_counts']}",
        f"positive_training_label_count = {summary['positive_training_label_count']}",
        f"negative_training_label_count = {summary['negative_training_label_count']}",
        f"positive_instance_count = {summary['positive_instance_count']}",
        f"negative_instance_count = {summary['negative_instance_count']}",
        f"positive_family_count = {summary['positive_family_count']}",
        f"negative_family_count = {summary['negative_family_count']}",
        f"positive_region_count = {summary['positive_region_count']}",
        f"negative_region_count = {summary['negative_region_count']}",
        f"positive_region_counts = {summary['positive_region_counts']}",
        f"negative_region_counts = {summary['negative_region_counts']}",
        f"label_distribution_ready_details = {summary['label_distribution_ready_details']}",
        f"sample_collection_gaps = {summary['sample_collection_gaps']}",
        f"label_distribution_ready = {str(summary['label_distribution_ready']).lower()}",
        f"training_ready = {str(summary['training_ready']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 样例",
        "",
        "```json",
        json.dumps(examples, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 结论",
        "",
    ]
    if summary["training_ready"]:
        lines.append("- 当前 positive / negative ROI 标签数量达到训练门槛，可进入 ROI gate 训练。")
    else:
        lines.append(
            "- 当前 ROI 标签数量或分布仍不足以训练可靠 gate；应继续扩充 20-task A/B 标签。"
        )
    lines.extend(
        [
            "- `positive_primal_roi` / `positive_retry_roi` / `positive_status_roi` 等作为 trajectory 正样本；",
            "- `no_observed_roi` / `negative_primal_roi` / `negative_retry_roi` 等作为负样本；",
            "- `columns_only_roi` 暂不作为主训练标签，可作为辅助分析；",
            "- 若存在 post-injection 后效字段，positive ROI 必须通过 active-support / baseline-same-iter guard，否则降为 DELAY 标签；",
            "- missing / certificate-effect / official-bound-effect 样本不进入训练；",
            "- 所有 ROI 训练标签都必须在同一个 expected context hash 下发生，否则排除训练；",
            "- 所有 ROI 训练标签都必须能在 worker 日志中因果匹配 target，否则排除训练；",
            "- no-observed ROI 还必须有实际 worker target intervention 证据，避免把 context mismatch 当负样本；",
            "- `training_ready` 同时要求 unique 标签数量和实例/family 分布达标，避免小样本或单实例标签把 GAT 带偏；",
            "- 该数据集只能用于离线校准，不能参与证书或官方下界。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-summary", type=Path, default=DEFAULT_AUDIT_SUMMARY)
    parser.add_argument("--candidate-summary", type=Path, action="append", default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-positive-for-training", type=int, default=5)
    parser.add_argument("--min-negative-for-training", type=int, default=5)
    parser.add_argument("--min-positive-instances-for-training", type=int, default=2)
    parser.add_argument("--min-negative-instances-for-training", type=int, default=2)
    parser.add_argument("--min-positive-families-for-training", type=int, default=2)
    parser.add_argument("--min-negative-families-for-training", type=int, default=2)
    parser.add_argument("--min-positive-regions-for-training", type=int, default=2)
    parser.add_argument("--min-negative-regions-for-training", type=int, default=2)
    parser.add_argument("--max-label-instance-fraction", type=float, default=0.75)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_roi_dataset(
        audit_summary_path=args.audit_summary,
        candidate_summary_paths=args.candidate_summary or list(DEFAULT_CANDIDATE_SUMMARIES),
        output_dir=args.output_dir,
        report=args.report,
        min_positive_for_training=max(1, int(args.min_positive_for_training)),
        min_negative_for_training=max(1, int(args.min_negative_for_training)),
        min_positive_instances_for_training=max(1, int(args.min_positive_instances_for_training)),
        min_negative_instances_for_training=max(1, int(args.min_negative_instances_for_training)),
        min_positive_families_for_training=max(1, int(args.min_positive_families_for_training)),
        min_negative_families_for_training=max(1, int(args.min_negative_families_for_training)),
        min_positive_regions_for_training=max(1, int(args.min_positive_regions_for_training)),
        min_negative_regions_for_training=max(1, int(args.min_negative_regions_for_training)),
        max_label_instance_fraction=float(args.max_label_instance_fraction),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
