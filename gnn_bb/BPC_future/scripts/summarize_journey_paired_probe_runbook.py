#!/usr/bin/env python3
"""Summarize paired branch child-probe runbook outcomes.

This helper is read-only.  It joins a paired replay runbook with each run's
``results.csv`` and optional audit outputs, then emits per-entry and per-group
relative proof-cost rows.  It does not run BPC/pricing/RMP and does not create
official bounds or certificates.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_paired_probe_summary_20260628")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260628_bpc_future_journey_paired_probe_summary_zh.md"
)
RUNBOOK_ENTRY_PASSTHROUGH_FIELDS = (
    "source_alt_routeopt_bkf_score",
    "source_alt_routeopt_bkf_reason",
    "source_alt_routeopt_bkf_stage",
    "source_alt_routeopt_bkf_dynamic_k",
    "source_alt_routeopt_bkf_stage_rank",
    "source_alt_routeopt_bkf_filtered_count",
    "source_alt_branch_score",
    "source_alt_branch_score_source",
    "source_alt_fractionality",
    "source_alt_required_tie_tolerance",
    "source_alt_pool_max_child_width",
    "source_alt_pool_total_child_width",
    "source_alt_pool_balance_gap",
    "source_alt_phase1_min_child_lp_gain",
    "source_alt_phase1_child_lp_gain_product",
    "source_alt_phase1_child_width_balance",
    "source_alt_phase1_wall_time",
    "source_alt_phase2_negative_child_count",
    "source_alt_phase2_negative_journey_count",
    "source_alt_phase2_worst_negative_severity",
    "source_alt_phase2_wall_time",
    "phased_testing_priority",
    "phased_testing_priority_reason",
    "phased_testing_controller_active",
    "phased_testing_phase1_best_min_child_lp_gain",
    "phased_testing_phase1_best_child_lp_gain_product",
    "phased_testing_phase2_negative_child_count_total",
    "phased_testing_phase2_negative_journey_count_total",
    "phased_testing_phase2_worst_negative_severity_max",
    "phased_testing_official_bound_effect_any",
    "phased_testing_certificate_effect_any",
)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
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


def _float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if parsed != parsed:
        return default
    return float(parsed)


def _int(value: Any, default: int = 0) -> int:
    parsed = _float(value)
    if parsed is None:
        return int(default)
    return int(parsed)


def _bool_text(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _pair_tuple(value: Any) -> tuple[int, int] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    try:
        first = int(value[0])
        second = int(value[1])
    except (TypeError, ValueError):
        return None
    return (min(first, second), max(first, second))


def _experiment_from_path(value: Any) -> str | None:
    text = str(value or "")
    marker = "/runs/"
    if marker not in text:
        marker = "runs/"
    if marker not in text:
        return None
    suffix = text.split(marker, 1)[1]
    return suffix.split("/", 1)[0] or None


def _read_result_row(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return rows[0] if rows else {}


def _completion_records_by_experiment(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    payload = _read_json(path)
    records = payload.get("records")
    if not isinstance(records, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        experiment = _experiment_from_path(record.get("log_file"))
        if experiment:
            out[experiment] = record
    return out


def _child_probe_totals_by_experiment(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    rows_path = path
    if path.is_dir():
        rows_path = path / "child_probe_rows.jsonl"
    rows = list(_iter_jsonl(rows_path))
    totals: dict[str, dict[str, Any]] = {}
    for row in rows:
        experiment = _experiment_from_path(row.get("log_file"))
        if not experiment:
            continue
        bucket = totals.setdefault(
            experiment,
            {
                "child_probe_row_count": 0,
                "child_completion_bound_retry_count": 0.0,
                "child_exact_pricing_event_count": 0.0,
                "child_negative_pricing_event_count": 0.0,
                "child_certificate_event_proxy_count": 0.0,
                "child_proof_cpu": 0.0,
                "child_fathomed_count": 0.0,
                "right_censored_child_probe_count": 0,
            },
        )
        bucket["child_probe_row_count"] += 1
        bucket["child_completion_bound_retry_count"] += float(
            _float(row.get("child_completion_bound_retry_count"), 0.0) or 0.0
        )
        bucket["child_exact_pricing_event_count"] += float(
            _float(row.get("child_exact_pricing_event_count"), 0.0) or 0.0
        )
        bucket["child_negative_pricing_event_count"] += float(
            _float(row.get("child_negative_pricing_event_count"), 0.0) or 0.0
        )
        bucket["child_proof_cpu"] += float(_float(row.get("child_proof_cpu"), 0.0) or 0.0)
        bucket["child_fathomed_count"] += float(_float(row.get("child_fathomed"), 0.0) or 0.0)
        if bool(row.get("right_censored")):
            bucket["right_censored_child_probe_count"] += 1
    return totals


def _target_replay_audit(run_root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    experiment = str(entry.get("experiment") or "")
    source_node = _float(entry.get("source_node_id"))
    source_depth = _float(entry.get("source_depth"))
    forced_pair = _pair_tuple(entry.get("forced_pair"))
    if not experiment or source_node is None or source_depth is None or forced_pair is None:
        return {
            "target_replay_audited": False,
            "target_replay_status": "missing_source_context",
            "target_candidate_event_seen": False,
            "target_branch_event_seen": False,
            "target_pair_selected": False,
            "target_selected_pair": None,
        }

    log_dir = run_root / experiment / "logs"
    log_paths = sorted(log_dir.rglob("*.jsonl")) if log_dir.exists() else []
    if not log_paths:
        return {
            "target_replay_audited": False,
            "target_replay_status": "not_audited",
            "target_candidate_event_seen": False,
            "target_branch_event_seen": False,
            "target_pair_selected": False,
            "target_selected_pair": None,
        }

    candidate_event_seen = False
    branch_event_seen = False
    target_pair_selected = False
    target_selected_pair: list[int] | None = None
    target_event_count = 0
    forced_pair_payload = [forced_pair[0], forced_pair[1]]
    for path in log_paths:
        for record in _iter_jsonl(path):
            if record.get("event") not in {"journey_branch_candidates", "journey_branch"}:
                continue
            node_id = _float(record.get("node_id"))
            depth = _float(record.get("depth"))
            if node_id is None or depth is None:
                continue
            if int(node_id) != int(source_node) or int(depth) != int(source_depth):
                continue
            event = str(record.get("event") or "")
            target_event_count += 1
            if event == "journey_branch_candidates":
                candidate_event_seen = True
            if event == "journey_branch":
                branch_event_seen = True
            selected_pair = _pair_tuple(record.get("selected_pair") or record.get("branch_pair") or record.get("pair"))
            if selected_pair is not None:
                target_selected_pair = [selected_pair[0], selected_pair[1]]
                if selected_pair == forced_pair:
                    target_pair_selected = True

    if target_pair_selected:
        status = "target_pair_selected"
    elif branch_event_seen or candidate_event_seen:
        status = "target_pair_not_selected"
    else:
        status = "target_not_replayed"
    return {
        "target_replay_audited": True,
        "target_replay_status": status,
        "target_candidate_event_seen": candidate_event_seen,
        "target_branch_event_seen": branch_event_seen,
        "target_pair_selected": target_pair_selected,
        "target_selected_pair": target_selected_pair,
        "target_forced_pair": forced_pair_payload,
        "target_event_count": target_event_count,
    }


def _status_rank(status: str | None) -> int:
    text = str(status or "").strip().upper()
    if text == "OPTIMAL":
        return 3
    if text == "TIME_LIMIT":
        return 2
    if text == "EXTERNAL_TIME_LIMIT":
        return 1
    if text:
        return 0
    return -1


def _label_against_baseline(row: dict[str, Any]) -> str:
    wall_gain = float(row.get("paired_wall_time_gain") or 0.0)
    profile_gain = float(row.get("paired_completion_profile_gain") or 0.0)
    retry_gain = float(row.get("paired_child_cb_retry_gain") or 0.0)
    status_delta = int(row.get("paired_status_rank_delta") or 0)
    gap_improvement = _float(row.get("paired_gap_improvement"))
    gap_bad = gap_improvement is not None and gap_improvement < -1.0e-9
    if status_delta > 0 or (wall_gain >= 30.0 and not gap_bad) or profile_gain >= 30.0 or retry_gain >= 10.0:
        return "positive_proxy"
    if status_delta < 0 or wall_gain <= -30.0 or profile_gain <= -30.0 or retry_gain <= -10.0 or gap_bad:
        return "hard_negative_proxy"
    return "neutral_proxy"


def summarize_paired_probe(
    runbook_path: Path,
    output_dir: Path,
    report: Path,
    *,
    completion_tail_summary: Path | None = None,
    child_probe_rows: Path | None = None,
) -> dict[str, Any]:
    runbook = _read_json(runbook_path)
    entries = [entry for entry in runbook.get("entries", []) if isinstance(entry, dict)]
    run_root = runbook_path.parent / "runs"
    completion_by_exp = _completion_records_by_experiment(completion_tail_summary)
    child_totals_by_exp = _child_probe_totals_by_experiment(child_probe_rows)

    rows: list[dict[str, Any]] = []
    for entry in entries:
        experiment = str(entry.get("experiment") or "")
        if not experiment:
            continue
        result = _read_result_row(run_root / experiment / "results.csv")
        completion = completion_by_exp.get(experiment, {})
        child_totals = child_totals_by_exp.get(experiment, {})
        replay_audit = _target_replay_audit(run_root, entry)
        row = {
            "schema_version": "journey_paired_probe_entry_v1",
            "diagnostic_only": True,
            "production_ready": False,
            "certificate_effect": False,
            "official_bound_effect": False,
            "experiment": experiment,
            "result_available": bool(result),
            "pair_group_id": entry.get("pair_group_id"),
            "pair_role": entry.get("pair_role"),
            "instance": entry.get("instance"),
            "source_node_id": entry.get("source_node_id"),
            "source_depth": entry.get("source_depth"),
            "source_selected_pair": entry.get("source_selected_pair"),
            "forced_pair": entry.get("forced_pair"),
            "source_alt_selection_reason": entry.get("source_alt_selection_reason"),
            **replay_audit,
            "status": result.get("status"),
            "wall_time": _float(result.get("wall_time")),
            "gap_available": _bool_text(result.get("gap_available")),
            "gap": _float(result.get("gap")),
            "node_count": _int(result.get("node_count")),
            "columns": _int(result.get("columns")),
            "pricing_calls": _int(result.get("pricing_calls")),
            "exact_pricing_calls": _int(result.get("exact_pricing_calls")),
            "generated_sequences": _int(result.get("generated_sequences")),
            "completion_retry_count": _int(completion.get("completion_retry_count")),
            "completion_retry_total_profile_generation_time": _float(
                completion.get("completion_retry_total_profile_generation_time"), 0.0
            ),
            "completion_retry_total_generated_sequences": _int(
                completion.get("completion_retry_total_generated_sequences")
            ),
            "completion_retry_total_negative_journeys": _int(
                completion.get("completion_retry_total_negative_journeys")
            ),
            "child_probe_row_count": _int(child_totals.get("child_probe_row_count")),
            "child_completion_bound_retry_count": _float(
                child_totals.get("child_completion_bound_retry_count"), 0.0
            ),
            "child_exact_pricing_event_count": _float(
                child_totals.get("child_exact_pricing_event_count"), 0.0
            ),
            "child_negative_pricing_event_count": _float(
                child_totals.get("child_negative_pricing_event_count"), 0.0
            ),
            "child_proof_cpu": _float(child_totals.get("child_proof_cpu"), 0.0),
            "child_fathomed_count": _float(child_totals.get("child_fathomed_count"), 0.0),
            "right_censored_child_probe_count": _int(
                child_totals.get("right_censored_child_probe_count")
            ),
        }
        for field in RUNBOOK_ENTRY_PASSTHROUGH_FIELDS:
            if field in entry:
                row[field] = entry.get(field)
        if "source_alt_phase1_min_child_lp_gain" in row:
            row["phase1_min_child_lp_gain"] = row.get("source_alt_phase1_min_child_lp_gain")
        if "source_alt_phase1_child_lp_gain_product" in row:
            row["phase1_child_lp_gain_product"] = row.get("source_alt_phase1_child_lp_gain_product")
        if "source_alt_phase1_child_width_balance" in row:
            row["phase1_child_width_balance"] = row.get("source_alt_phase1_child_width_balance")
        if "source_alt_phase1_wall_time" in row:
            row["phase1_wall_time"] = row.get("source_alt_phase1_wall_time")
        if "source_alt_phase2_negative_child_count" in row:
            row["phase2_negative_child_count"] = row.get("source_alt_phase2_negative_child_count")
        if "source_alt_phase2_negative_journey_count" in row:
            row["phase2_negative_journey_count"] = row.get("source_alt_phase2_negative_journey_count")
        if "source_alt_phase2_worst_negative_severity" in row:
            row["phase2_worst_negative_severity"] = row.get("source_alt_phase2_worst_negative_severity")
        if "source_alt_phase2_wall_time" in row:
            row["phase2_wall_time"] = row.get("source_alt_phase2_wall_time")
        rows.append(row)

    baseline_by_group: dict[str, dict[str, Any]] = {}
    for row in rows:
        group = str(row.get("pair_group_id") or "")
        if group and row.get("pair_role") == "selected_baseline" and bool(row.get("result_available")):
            baseline_by_group[group] = row

    for row in rows:
        group = str(row.get("pair_group_id") or "")
        baseline = baseline_by_group.get(group)
        if not bool(row.get("result_available")):
            row["paired_has_baseline"] = baseline is not None
            row["paired_label_type"] = "missing_result"
            continue
        if row.get("pair_role") == "selected_baseline":
            row["paired_has_baseline"] = baseline is not None
            row["paired_label_type"] = "baseline"
            continue
        replay_status = str(row.get("target_replay_status") or "")
        if replay_status in {"target_not_replayed", "target_pair_not_selected", "missing_source_context"}:
            row["paired_has_baseline"] = baseline is not None
            row["paired_label_type"] = replay_status
            continue
        if baseline is None:
            row["paired_has_baseline"] = False
            row["paired_label_type"] = "missing_baseline"
            continue
        wall = _float(row.get("wall_time"), 600.0) or 600.0
        base_wall = _float(baseline.get("wall_time"), 600.0) or 600.0
        profile = _float(row.get("completion_retry_total_profile_generation_time"), 0.0) or 0.0
        base_profile = _float(baseline.get("completion_retry_total_profile_generation_time"), 0.0) or 0.0
        cb_retry = _float(row.get("child_completion_bound_retry_count"), 0.0) or 0.0
        base_cb_retry = _float(baseline.get("child_completion_bound_retry_count"), 0.0) or 0.0
        gap = _float(row.get("gap"))
        base_gap = _float(baseline.get("gap"))
        row.update(
            {
                "paired_has_baseline": True,
                "paired_baseline_experiment": baseline.get("experiment"),
                "paired_wall_time_gain": round(base_wall - wall, 6),
                "paired_completion_profile_gain": round(base_profile - profile, 6),
                "paired_child_cb_retry_gain": round(base_cb_retry - cb_retry, 6),
                "paired_status_rank_delta": _status_rank(str(row.get("status"))) - _status_rank(
                    str(baseline.get("status"))
                ),
                "paired_gap_improvement": None
                if gap is None or base_gap is None
                else round(float(base_gap) - float(gap), 9),
            }
        )
        row["paired_label_type"] = _label_against_baseline(row)

    group_rows: list[dict[str, Any]] = []
    groups = sorted({str(row.get("pair_group_id") or "") for row in rows if row.get("pair_group_id")})
    for group in groups:
        group_entries = [row for row in rows if row.get("pair_group_id") == group]
        alternatives = [row for row in group_entries if row.get("pair_role") == "alternative"]
        observed_alternatives = [row for row in alternatives if bool(row.get("result_available"))]
        valid_observed_alternatives = [
            row
            for row in observed_alternatives
            if str(row.get("target_replay_status") or "") in {"target_pair_selected", "not_audited"}
        ]
        labels: dict[str, int] = {}
        for row in alternatives:
            label = str(row.get("paired_label_type") or "")
            labels[label] = labels.get(label, 0) + 1
        best_alt = None
        if valid_observed_alternatives:
            best_alt = max(
                valid_observed_alternatives,
                key=lambda row: (
                    float(row.get("paired_wall_time_gain") or 0.0),
                    float(row.get("paired_completion_profile_gain") or 0.0),
                    float(row.get("paired_child_cb_retry_gain") or 0.0),
                ),
            )
        baseline = baseline_by_group.get(group, {})
        group_rows.append(
            {
                "schema_version": "journey_paired_probe_group_v1",
                "pair_group_id": group,
                "baseline_experiment": baseline.get("experiment"),
                "baseline_forced_pair": baseline.get("forced_pair"),
                "alternative_count": len(alternatives),
                "observed_alternative_count": len(observed_alternatives),
                "valid_observed_alternative_count": len(valid_observed_alternatives),
                "target_hit_count": sum(1 for row in group_entries if row.get("target_pair_selected")),
                "target_not_replayed_count": sum(
                    1 for row in group_entries if row.get("target_replay_status") == "target_not_replayed"
                ),
                "target_pair_not_selected_count": sum(
                    1 for row in group_entries if row.get("target_replay_status") == "target_pair_not_selected"
                ),
                "label_counts": labels,
                "best_alternative_experiment": None if best_alt is None else best_alt.get("experiment"),
                "best_alternative_forced_pair": None if best_alt is None else best_alt.get("forced_pair"),
                "best_wall_time_gain": None if best_alt is None else best_alt.get("paired_wall_time_gain"),
                "best_completion_profile_gain": None
                if best_alt is None
                else best_alt.get("paired_completion_profile_gain"),
                "best_child_cb_retry_gain": None
                if best_alt is None
                else best_alt.get("paired_child_cb_retry_gain"),
            }
        )

    summary = {
        "schema_version": "journey_paired_probe_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "runbook_path": str(runbook_path),
        "completion_tail_summary": None if completion_tail_summary is None else str(completion_tail_summary),
        "child_probe_rows": None if child_probe_rows is None else str(child_probe_rows),
        "entry_count": len(rows),
        "paired_group_count": len(group_rows),
        "baseline_entry_count": sum(1 for row in rows if row.get("pair_role") == "selected_baseline"),
        "alternative_entry_count": sum(1 for row in rows if row.get("pair_role") == "alternative"),
        "result_available_entry_count": sum(1 for row in rows if bool(row.get("result_available"))),
        "missing_result_entry_count": sum(1 for row in rows if not bool(row.get("result_available"))),
        "observed_alternative_entry_count": sum(
            1
            for row in rows
            if row.get("pair_role") == "alternative" and bool(row.get("result_available"))
        ),
        "valid_observed_alternative_entry_count": sum(
            1
            for row in rows
            if row.get("pair_role") == "alternative"
            and bool(row.get("result_available"))
            and str(row.get("target_replay_status") or "") in {"target_pair_selected", "not_audited"}
        ),
        "target_not_replayed_entry_count": sum(
            1 for row in rows if row.get("target_replay_status") == "target_not_replayed"
        ),
        "target_pair_not_selected_entry_count": sum(
            1 for row in rows if row.get("target_replay_status") == "target_pair_not_selected"
        ),
        "label_counts": {},
        "groups": group_rows,
    }
    for row in rows:
        if row.get("pair_role") != "alternative":
            continue
        label = str(row.get("paired_label_type") or "")
        summary["label_counts"][label] = int(summary["label_counts"].get(label, 0)) + 1

    write_outputs(summary, rows, group_rows, output_dir, report)
    return summary


def write_outputs(
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
    group_rows: list[dict[str, Any]],
    output_dir: Path,
    report: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "paired_probe_rows.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    (output_dir / "paired_probe_group_rows.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in group_rows),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_render_report(summary), encoding="utf-8")


def _render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Journey Paired Probe Summary",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## Boundary",
        "",
        "This report only summarizes already completed paired replay probes. It does not run BPC / pricing / RMP, and it does not create official bounds or certificates.",
        "",
        "## Summary",
        "",
        "```text",
        f"entry_count = {summary.get('entry_count')}",
        f"paired_group_count = {summary.get('paired_group_count')}",
        f"baseline_entry_count = {summary.get('baseline_entry_count')}",
        f"alternative_entry_count = {summary.get('alternative_entry_count')}",
        f"result_available_entry_count = {summary.get('result_available_entry_count')}",
        f"missing_result_entry_count = {summary.get('missing_result_entry_count')}",
        f"observed_alternative_entry_count = {summary.get('observed_alternative_entry_count')}",
        f"valid_observed_alternative_entry_count = {summary.get('valid_observed_alternative_entry_count')}",
        f"target_not_replayed_entry_count = {summary.get('target_not_replayed_entry_count')}",
        f"target_pair_not_selected_entry_count = {summary.get('target_pair_not_selected_entry_count')}",
        f"label_counts = {summary.get('label_counts')}",
        "production_ready = false",
        "certificate_effect = false",
        "official_bound_effect = false",
        "```",
        "",
        "## Groups",
        "",
    ]
    for group in summary.get("groups", [])[:40]:
        lines.extend(
            [
                f"- `{group.get('pair_group_id')}`",
                f"  baseline = {group.get('baseline_forced_pair')} / {group.get('baseline_experiment')}",
                f"  best_alt = {group.get('best_alternative_forced_pair')} / {group.get('best_alternative_experiment')}",
                f"  gains = wall {group.get('best_wall_time_gain')}, profile {group.get('best_completion_profile_gain')}, child_cb_retry {group.get('best_child_cb_retry_gain')}",
                f"  target = hit {group.get('target_hit_count')}, not_replayed {group.get('target_not_replayed_count')}, pair_not_selected {group.get('target_pair_not_selected_count')}",
                f"  labels = {group.get('label_counts')}",
            ]
        )
    return "\n".join(lines) + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runbook", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--completion-tail-summary", type=Path, default=None)
    parser.add_argument("--child-probe-rows", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = summarize_paired_probe(
        args.runbook,
        args.output_dir,
        args.report,
        completion_tail_summary=args.completion_tail_summary,
        child_probe_rows=args.child_probe_rows,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
