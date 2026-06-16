#!/usr/bin/env python3
"""Build workload-aware utility rows from sequential target-materialization runs.

This script is read-only. It converts already-run sequential worker logs into
``gat_same_run_batch_impact_row_v1`` rows with explicit longer-horizon labels.
The labels are intentionally stricter than immediate RMP objective movement:
if a sequential policy increases RMP/pricing/exact workload, its materialized
true-RC negative journeys become delay/bad-mode examples even when they changed
active support locally.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_sequential_target_materialization_utility_rows_20260616"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260616_bpc_future_gat_target_mode_stage3_sequential_utility_rows_zh.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-json", type=Path, action="append", required=True)
    parser.add_argument("--worker-log-dir", type=Path, required=True)
    parser.add_argument("--worker-results-csv", type=Path, required=True)
    parser.add_argument("--baseline-reference-json", type=Path)
    parser.add_argument("--baseline-status", default="TIME_LIMIT")
    parser.add_argument("--baseline-primal-bound", type=float, default=0.0)
    parser.add_argument("--baseline-rmp-solves", type=int, default=0)
    parser.add_argument("--baseline-pricing-calls", type=int, default=0)
    parser.add_argument("--baseline-exact-pricing-calls", type=int, default=0)
    parser.add_argument("--baseline-generated-sequences", type=int, default=0)
    parser.add_argument("--baseline-evaluated-timed-trips", type=int, default=0)
    parser.add_argument("--baseline-columns", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--evaluated-scale", type=float, default=10000.0)
    parser.add_argument("--generated-scale", type=float, default=20000.0)
    parser.add_argument("--rmp-solve-penalty", type=float, default=0.02)
    parser.add_argument("--pricing-call-penalty", type=float, default=0.05)
    parser.add_argument("--exact-call-penalty", type=float, default=0.25)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_rows(
        candidate_jsons=args.candidate_json,
        worker_log_dir=args.worker_log_dir,
        worker_results_csv=args.worker_results_csv,
        baseline_reference_json=args.baseline_reference_json,
        baseline_metrics=_baseline_metrics_from_args(args),
        output_dir=args.output_dir,
        report=args.report,
        evaluated_scale=float(args.evaluated_scale),
        generated_scale=float(args.generated_scale),
        rmp_solve_penalty=float(args.rmp_solve_penalty),
        pricing_call_penalty=float(args.pricing_call_penalty),
        exact_call_penalty=float(args.exact_call_penalty),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


def build_rows(
    *,
    candidate_jsons: Iterable[Path],
    worker_log_dir: Path,
    worker_results_csv: Path,
    baseline_reference_json: Path | None = None,
    baseline_metrics: dict[str, Any] | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    evaluated_scale: float = 10000.0,
    generated_scale: float = 20000.0,
    rmp_solve_penalty: float = 0.02,
    pricing_call_penalty: float = 0.05,
    exact_call_penalty: float = 0.25,
) -> dict[str, Any]:
    candidates = _load_candidates(candidate_jsons)
    worker_events = _read_events(worker_log_dir)
    worker_metrics = _read_single_csv_row(worker_results_csv)
    baseline = _load_baseline_reference(baseline_reference_json, baseline_metrics or {})
    trajectory = _trajectory_utility(
        baseline,
        worker_metrics,
        evaluated_scale=evaluated_scale,
        generated_scale=generated_scale,
        rmp_solve_penalty=rmp_solve_penalty,
        pricing_call_penalty=pricing_call_penalty,
        exact_call_penalty=exact_call_penalty,
    )
    additions = _addition_events(worker_events)
    rmps = _rmp_events(worker_events)

    rows: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    for candidate in candidates:
        worker = _matching_worker_event(worker_events, candidate)
        if worker is None:
            skipped["missing_matching_worker_event"] += 1
            continue
        key = _event_key(worker, pricing_kind="sharded_pulse_hidden_negative_worker")
        addition = additions.get(key)
        if addition is None or _int_value(addition.get("added_journeys")) <= 0:
            skipped["missing_worker_addition"] += 1
            continue
        cg_iter, _kind, node_id, depth = key
        before = rmps.get((cg_iter, node_id, depth), {})
        after = rmps.get((cg_iter + 1, node_id, depth), {})
        rows.append(
            _row_from_candidate(
                candidate,
                worker=worker,
                addition=addition,
                before_rmp=before,
                after_rmp=after,
                trajectory=trajectory,
                worker_log_dir=worker_log_dir,
            )
        )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    row_jsonl = output_dir / "sequential_target_materialization_utility_rows.jsonl"
    row_jsonl.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )
    summary = {
        "schema_version": "gat_sequential_target_materialization_utility_rows_summary_v1",
        "status": "built" if rows else "no_rows",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "candidate_count": len(candidates),
        "row_count": len(rows),
        "positive_utility_row_count": sum(
            int(row.get("label_batch_roi_positive") or 0) for row in rows
        ),
        "negative_utility_row_count": sum(
            int(not bool(row.get("label_batch_roi_positive"))) for row in rows
        ),
        "bad_mode_row_count": sum(int(row.get("label_bad_mode_switch") or 0) for row in rows),
        "trajectory_utility": trajectory,
        "skipped_counts": dict(sorted(skipped.items())),
        "jsonl_path": str(row_jsonl),
        "checks": {
            "diagnostic_only": True,
            "runs_bpc_or_pricing_false": True,
            "has_rows": bool(rows),
            "all_rows_have_explicit_long_horizon_labels": all(
                "accepted_batch_roi_label" in row
                and "label_batch_roi_positive" in row
                and "label_bad_mode_switch" in row
                for row in rows
            ),
            "no_certificate_effect": all(not row["certificate_effect"] for row in rows),
            "no_official_bound_effect": all(not row["official_bound_effect"] for row in rows),
        },
    }
    summary["all_checks_pass"] = all(bool(value) for value in summary["checks"].values())
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _baseline_metrics_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "status": str(args.baseline_status),
        "primal_bound": float(args.baseline_primal_bound),
        "rmp_solves": int(args.baseline_rmp_solves),
        "pricing_calls": int(args.baseline_pricing_calls),
        "exact_pricing_calls": int(args.baseline_exact_pricing_calls),
        "generated_sequences": int(args.baseline_generated_sequences),
        "evaluated_timed_trips": int(args.baseline_evaluated_timed_trips),
        "columns": int(args.baseline_columns),
    }


def _load_baseline_reference(path: Path | None, fallback: dict[str, Any]) -> dict[str, Any]:
    if path is None:
        return dict(fallback)
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("baseline reference must be a JSON object")
    return {**fallback, **payload}


def _load_candidates(paths: Iterable[Path]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for path in paths:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            raw_candidates = payload.get("candidates") or payload.get("selected_candidates")
            if raw_candidates is None:
                raw_candidates = [payload]
        else:
            raw_candidates = payload
        if not isinstance(raw_candidates, list):
            raise ValueError(f"candidate file is not a list: {path}")
        for raw in raw_candidates:
            if not isinstance(raw, dict):
                raise ValueError(f"candidate entry is not an object: {path}")
            candidate = dict(raw)
            candidate.setdefault("candidate_file", str(path))
            candidates.append(candidate)
    return candidates


def _read_single_csv_row(path: Path) -> dict[str, Any]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1:
        raise ValueError(f"expected exactly one row in {path}, got {len(rows)}")
    return rows[0]


def _read_events(path: Path) -> list[dict[str, Any]]:
    files = [Path(path)] if Path(path).is_file() else sorted(Path(path).rglob("*.jsonl"))
    events: list[dict[str, Any]] = []
    for file in files:
        with file.open(encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                text = line.strip()
                if not text:
                    continue
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    events.append(payload)
    return events


def _matching_worker_event(
    events: Iterable[dict[str, Any]],
    candidate: dict[str, Any],
) -> dict[str, Any] | None:
    expected_context = str(candidate.get("expected_context_hash") or "")
    target_sequence = tuple(int(task) for task in (candidate.get("target_sequence") or []))
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
        event_sequence = tuple(int(task) for task in (event.get("pulse_worker_target_sequence") or []))
        if target_sequence and event_sequence and event_sequence != target_sequence:
            continue
        matches.append(event)
    if not matches:
        return None
    matches.sort(key=lambda item: (_int_value(item.get("cg_iter")), _int_value(item.get("node_id")), _int_value(item.get("depth"))))
    return matches[0]


def _addition_events(events: Iterable[dict[str, Any]]) -> dict[tuple[int, str, int, int], dict[str, Any]]:
    result: dict[tuple[int, str, int, int], dict[str, Any]] = {}
    for event in events:
        if event.get("event") == "journey_column_addition":
            result[_event_key(event)] = event
    return result


def _rmp_events(events: Iterable[dict[str, Any]]) -> dict[tuple[int, int, int], dict[str, Any]]:
    result: dict[tuple[int, int, int], dict[str, Any]] = {}
    for event in events:
        if event.get("event") == "journey_rmp":
            result[(
                _int_value(event.get("cg_iter"), -1),
                _int_value(event.get("node_id"), 0),
                _int_value(event.get("depth"), 0),
            )] = event
    return result


def _event_key(event: dict[str, Any], *, pricing_kind: str | None = None) -> tuple[int, str, int, int]:
    return (
        _int_value(event.get("cg_iter"), -1),
        str(pricing_kind if pricing_kind is not None else event.get("pricing_kind") or ""),
        _int_value(event.get("node_id"), 0),
        _int_value(event.get("depth"), 0),
    )


def _trajectory_utility(
    baseline: dict[str, Any],
    worker: dict[str, Any],
    *,
    evaluated_scale: float,
    generated_scale: float,
    rmp_solve_penalty: float,
    pricing_call_penalty: float,
    exact_call_penalty: float,
) -> dict[str, Any]:
    baseline_eval = _float_value(baseline.get("evaluated_timed_trips"))
    worker_eval = _float_value(worker.get("evaluated_timed_trips"))
    baseline_generated = _float_value(baseline.get("generated_sequences"))
    worker_generated = _float_value(worker.get("generated_sequences"))
    rmp_delta = _int_value(worker.get("rmp_solves")) - _int_value(baseline.get("rmp_solves"))
    pricing_delta = _int_value(worker.get("pricing_calls")) - _int_value(baseline.get("pricing_calls"))
    exact_delta = _int_value(worker.get("exact_pricing_calls")) - _int_value(
        baseline.get("exact_pricing_calls")
    )
    evaluated_component = (baseline_eval - worker_eval) / max(1.0, float(evaluated_scale))
    generated_component = (baseline_generated - worker_generated) / max(1.0, float(generated_scale))
    utility = (
        evaluated_component
        + generated_component
        - float(rmp_solve_penalty) * max(0, rmp_delta)
        - float(pricing_call_penalty) * max(0, pricing_delta)
        - float(exact_call_penalty) * max(0, exact_delta)
    )
    return {
        "accepted_batch_roi_label": float(utility),
        "label_batch_roi_positive": int(utility > 0.0),
        "workload_worse": bool(
            rmp_delta > 0
            or pricing_delta > 0
            or exact_delta > 0
            or worker_eval > baseline_eval
            or worker_generated > baseline_generated
        ),
        "rmp_solves_delta": int(rmp_delta),
        "pricing_calls_delta": int(pricing_delta),
        "exact_pricing_calls_delta": int(exact_delta),
        "generated_sequences_delta": int(worker_generated - baseline_generated),
        "evaluated_timed_trips_delta": int(worker_eval - baseline_eval),
        "evaluated_component": float(evaluated_component),
        "generated_component": float(generated_component),
    }


def _row_from_candidate(
    candidate: dict[str, Any],
    *,
    worker: dict[str, Any],
    addition: dict[str, Any],
    before_rmp: dict[str, Any],
    after_rmp: dict[str, Any],
    trajectory: dict[str, Any],
    worker_log_dir: Path,
) -> dict[str, Any]:
    objective_before = _float_value(before_rmp.get("objective"))
    objective_after = _float_value(after_rmp.get("objective"), objective_before)
    objective_improvement = objective_before - objective_after
    active_changed = _int_value(addition.get("active_changed_task_set_count"))
    row_positive = int(trajectory["label_batch_roi_positive"])
    bad_mode = int((not bool(row_positive)) and active_changed > 0)
    instance_path = str(candidate.get("instance") or "")
    return {
        "schema_version": "gat_same_run_batch_impact_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "source_file": str(candidate.get("source_file") or ""),
        "worker_source_files": [str(path) for path in sorted(Path(worker_log_dir).rglob("*.jsonl"))],
        "instance": Path(instance_path).stem,
        "instance_path": instance_path,
        "instance_region": str(candidate.get("instance_region") or candidate.get("region") or ""),
        "cg_iter": _int_value(candidate.get("cg_iter"), _int_value(worker.get("cg_iter"))),
        "node_id": _int_value(worker.get("node_id"), 0),
        "depth": _int_value(worker.get("depth"), 0),
        "pricing_kind": str(candidate.get("capture_pricing_kind") or "exact"),
        "context_hash": str(candidate.get("expected_context_hash") or ""),
        "true_dual_hash": str(candidate.get("true_dual_hash") or ""),
        "cut_hash": str(candidate.get("cut_hash") or ""),
        "branch_hash": str(candidate.get("branch_hash") or ""),
        "forbidden_signature_hash": str(candidate.get("forbidden_signature_hash") or ""),
        "returned_journey_count": 1,
        "added_journeys": _int_value(addition.get("added_journeys"), 1),
        "new_journeys": _int_value(addition.get("new_journeys"), 0),
        "replacement_journeys": _int_value(addition.get("replacement_journeys"), 0),
        "new_task_set_count": _int_value(addition.get("new_task_set_count"), 0),
        "replacement_task_set_count": _int_value(addition.get("replacement_task_set_count"), 0),
        "active_changed_task_set_count": active_changed,
        "addition_productivity_class": str(addition.get("addition_productivity_class") or ""),
        "best_true_reduced_cost": _float_value(worker.get("pulse_worker_best_rc")),
        "objective_before": objective_before,
        "objective_after": objective_after,
        "objective_delta": objective_after - objective_before,
        "objective_improvement": objective_improvement,
        "label_objective_improved": int(objective_improvement > 1.0e-9),
        "label_batch_roi_positive": row_positive,
        "accepted_batch_roi_label": float(trajectory["accepted_batch_roi_label"]),
        "label_bad_mode_switch": bad_mode,
        "label_support_changed_good": int(bool(row_positive) and active_changed > 0 and not bad_mode),
        "label_tail_improved": int(
            _int_value(trajectory.get("exact_pricing_calls_delta")) < 0
            or _int_value(trajectory.get("evaluated_timed_trips_delta")) < 0
        ),
        "delta_v_label": -float(trajectory["accepted_batch_roi_label"]),
        "barrier_slack_label": float(trajectory["accepted_batch_roi_label"]),
        "same_run_intervention_observed": False,
        "same_context_target_intervention_observed": True,
        "worker_target_causal_match": True,
        "training_label_allowed": True,
        "training_label_scope": "sequential_target_materialization_workload_utility",
        "target_candidate_name": str(candidate.get("name") or ""),
        "target_sequence": list(candidate.get("target_sequence") or []),
        "target_sortie_traces": list(candidate.get("target_sortie_traces") or []),
        "target_arc_option_sequence": list(candidate.get("target_arc_option_sequence") or []),
        "worker_cg_iter": _int_value(worker.get("cg_iter"), -1),
        "worker_pricing_kind": "sharded_pulse_hidden_negative_worker",
        "worker_context_hash": str(worker.get("pulse_worker_context_hash") or ""),
        "worker_target_sequence_materialized": bool(worker.get("pulse_worker_target_sequence_materialized")),
        "worker_target_sequence_negative": bool(worker.get("pulse_worker_target_sequence_negative")),
        **trajectory,
    }


def _int_value(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _float_value(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    trajectory = summary["trajectory_utility"]
    lines = [
        "# GAT Sequential Target-materialization Utility Rows 报告",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把 sequential target-materialization run 的结果转成 longer-horizon workload-aware",
        "batch-impact rows。该脚本只读已有日志和 CSV，不运行 BPC / pricing / RMP。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"status = {summary['status']}",
        f"candidate_count = {summary['candidate_count']}",
        f"row_count = {summary['row_count']}",
        f"positive_utility_row_count = {summary['positive_utility_row_count']}",
        f"negative_utility_row_count = {summary['negative_utility_row_count']}",
        f"bad_mode_row_count = {summary['bad_mode_row_count']}",
        f"accepted_batch_roi_label = {trajectory['accepted_batch_roi_label']}",
        f"rmp_solves_delta = {trajectory['rmp_solves_delta']}",
        f"pricing_calls_delta = {trajectory['pricing_calls_delta']}",
        f"exact_pricing_calls_delta = {trajectory['exact_pricing_calls_delta']}",
        f"generated_sequences_delta = {trajectory['generated_sequences_delta']}",
        f"evaluated_timed_trips_delta = {trajectory['evaluated_timed_trips_delta']}",
        f"workload_worse = {str(trajectory['workload_worse']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 判定",
        "",
        "如果 workload 变重，即使 worker 物化了 true-RC negative active replacement，",
        "也必须作为 bad-mode / DELAY_QUEUE 训练信号，不能标成 Stage 4 HIGH_PRIORITY 正例。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
