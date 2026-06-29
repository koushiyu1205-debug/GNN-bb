#!/usr/bin/env python3
"""Build branch-score timeout evidence rows from full-run JSONL logs.

This script is offline and diagnostic-only.  It reads completed or externally
timed-out result CSVs plus flushed JSONL branch logs, then exports:

- root score-gated branch changes that did not close within the time limit;
- deep branch contexts where score lookup was missing.

It does not run BPC, pricing, RMP, or certificates, and it must not be used as
an official bound source.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DEFAULT_BASELINE_DIR = Path("BPC_future/results/20260628_v568_retry_gate_cap_profile_trigger_fix_smoke4_tasks20")
DEFAULT_ALTERNATIVE_DIR = Path("BPC_future/results/20260628_v569_v543_root035_strict_state_smoke4_tasks20")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/20260628_v569_branch_timeout_evidence")


def _read_csv(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    return {Path(str(row.get("instance", ""))).name: row for row in rows if row.get("instance")}


def _finite_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return float(parsed)


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    try:
        handle = path.open(encoding="utf-8")
    except OSError:
        return
    with handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                yield payload


def _iter_branch_events(log_dir: Path) -> Iterable[dict[str, Any]]:
    for path in sorted(log_dir.rglob("*.jsonl")):
        instance = path.name[: -len(".jsonl")] if path.name.endswith(".jsonl") else path.name
        for payload in _iter_jsonl(path):
            if payload.get("event") != "journey_branch":
                continue
            row = dict(payload)
            row["_log_file"] = str(path)
            row["_instance"] = instance
            yield row


def _as_depth(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _result_status(row: dict[str, str]) -> str:
    return str(row.get("status") or "")


def _result_wall(row: dict[str, str]) -> float | None:
    return _finite_float(row.get("wall_time")) or _finite_float(row.get("solving_time"))


def _gap_available(row: dict[str, str]) -> bool:
    return str(row.get("gap_available") or "").strip().lower() == "true"


def _root_hard_negative_row(
    event: dict[str, Any],
    *,
    baseline_row: dict[str, str],
    alternative_row: dict[str, str],
    baseline_label: str,
    alternative_label: str,
) -> dict[str, Any]:
    baseline_gap = _finite_float(baseline_row.get("gap"))
    alternative_gap = _finite_float(alternative_row.get("gap"))
    gap_delta = None
    if baseline_gap is not None and alternative_gap is not None:
        gap_delta = float(baseline_gap) - float(alternative_gap)
    changed = _as_bool(event.get("selected_pair_changed"))
    alternative_nonoptimal = _result_status(alternative_row) != "OPTIMAL"
    return {
        "schema_version": "journey_branch_root_timeout_hard_negative_v1",
        "source_experiment": alternative_label,
        "baseline_experiment": baseline_label,
        "instance": event.get("_instance"),
        "log_file": event.get("_log_file"),
        "node_id": event.get("node_id"),
        "depth": event.get("depth"),
        "branch_state_key": event.get("branch_state_key"),
        "candidate_count": event.get("candidate_count"),
        "baseline_pair": event.get("baseline_pair"),
        "baseline_rank": event.get("baseline_rank"),
        "selected_pair": event.get("selected_pair"),
        "selected_pair_changed": changed,
        "selected_score": event.get("selected_score"),
        "selected_score_source": event.get("selected_score_source"),
        "score_gate_passed": _as_bool(event.get("branch_score_selection_gate_passed")),
        "score_gate_reason": event.get("branch_score_selection_gate_reason"),
        "baseline_status": _result_status(baseline_row),
        "baseline_wall_time": _result_wall(baseline_row),
        "baseline_gap": baseline_gap,
        "baseline_primal_bound": _finite_float(baseline_row.get("primal_bound")),
        "baseline_dual_bound": _finite_float(baseline_row.get("dual_bound")),
        "alternative_status": _result_status(alternative_row),
        "alternative_wall_time": _result_wall(alternative_row),
        "alternative_gap": alternative_gap,
        "alternative_primal_bound": _finite_float(alternative_row.get("primal_bound")),
        "alternative_dual_bound": _finite_float(alternative_row.get("dual_bound")),
        "gap_delta_vs_baseline": gap_delta,
        "label_type": "root_score_timeout_no_effect_hard_negative"
        if changed and alternative_nonoptimal
        else "root_score_timeout_observation",
        "y_branch_score_hard_negative": 1.0 if changed and alternative_nonoptimal else 0.0,
        "reason": "changed root pair under score gate but full run did not close within the time limit",
    }


def _missing_context_row(
    event: dict[str, Any],
    *,
    experiment: str,
    result_row: dict[str, str],
) -> dict[str, Any]:
    return {
        "schema_version": "journey_branch_deep_missing_context_v1",
        "source_experiment": experiment,
        "instance": event.get("_instance"),
        "log_file": event.get("_log_file"),
        "log_path": event.get("_log_file"),
        "node_id": event.get("node_id"),
        "depth": event.get("depth"),
        "branch_state_key": event.get("branch_state_key"),
        "branch_constraints": event.get("branch_constraints"),
        "candidate_count": event.get("candidate_count"),
        "baseline_pair": event.get("baseline_pair"),
        "selected_pair": event.get("selected_pair"),
        "selected_pair_changed": _as_bool(event.get("selected_pair_changed")),
        "score_gate_reason": event.get("branch_score_selection_gate_reason"),
        "branch_score_require_state_key": _as_bool(event.get("branch_score_require_state_key")),
        "status": _result_status(result_row),
        "wall_time": _result_wall(result_row),
        "gap": _finite_float(result_row.get("gap")),
        "gap_available": _gap_available(result_row),
        "gap_source": result_row.get("gap_source"),
        "sampling_priority": "DEEP_CONTEXT_SCORE_MISSING",
        "scored_candidate_count": 0,
        "eligible_scored_candidate_count": 0,
        "selected_is_unscored": True,
        "full_logged_candidate_coverage": True,
        "would_change_selected": False,
        "would_change_selected_any_logged": False,
        "best_scored_pair": None,
        "best_scored_required_tie_tolerance": None,
    }


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def _summarize_branch_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    depth_counts: Counter[int] = Counter()
    reasons: Counter[str] = Counter()
    for event in events:
        depth_counts[_as_depth(event.get("depth"))] += 1
        reasons[str(event.get("branch_score_selection_gate_reason") or "")] += 1
    roots = [event for event in events if _as_depth(event.get("depth")) == 0]
    return {
        "branch_events": len(events),
        "root_branch_events": len(roots),
        "selected_pair_changed_count": sum(1 for event in events if _as_bool(event.get("selected_pair_changed"))),
        "root_selected_pair_changed_count": sum(1 for event in roots if _as_bool(event.get("selected_pair_changed"))),
        "score_gate_reasons": dict(sorted(reasons.items())),
        "depth_counts": {str(key): value for key, value in sorted(depth_counts.items())},
    }


def build_timeout_evidence(
    *,
    baseline_dir: Path,
    alternative_dir: Path,
    output_dir: Path,
    baseline_label: str,
    alternative_label: str,
) -> dict[str, Any]:
    baseline_results = _read_csv(baseline_dir / "results.csv")
    alternative_results = _read_csv(alternative_dir / "results.csv")
    baseline_events = list(_iter_branch_events(baseline_dir / "logs"))
    alternative_events = list(_iter_branch_events(alternative_dir / "logs"))

    root_rows: list[dict[str, Any]] = []
    for event in alternative_events:
        if _as_depth(event.get("depth")) != 0:
            continue
        instance = str(event.get("_instance") or "")
        root_rows.append(
            _root_hard_negative_row(
                event,
                baseline_row=baseline_results.get(instance, {}),
                alternative_row=alternative_results.get(instance, {}),
                baseline_label=baseline_label,
                alternative_label=alternative_label,
            )
        )

    missing_rows: list[dict[str, Any]] = []
    for experiment, events, results in (
        (baseline_label, baseline_events, baseline_results),
        (alternative_label, alternative_events, alternative_results),
    ):
        for event in events:
            if _as_depth(event.get("depth")) < 1:
                continue
            if str(event.get("branch_score_selection_gate_reason") or "") != "missing_score_source":
                continue
            instance = str(event.get("_instance") or "")
            missing_rows.append(
                _missing_context_row(
                    event,
                    experiment=experiment,
                    result_row=results.get(instance, {}),
                )
            )

    root_path = output_dir / "root_timeout_hard_negative_rows.jsonl"
    missing_path = output_dir / "deep_missing_context_rows.jsonl"
    root_count = _write_jsonl(root_path, root_rows)
    missing_count = _write_jsonl(missing_path, missing_rows)
    summary = {
        "schema_version": "journey_branch_timeout_evidence_summary_v1",
        "baseline_label": baseline_label,
        "alternative_label": alternative_label,
        "baseline_dir": str(baseline_dir),
        "alternative_dir": str(alternative_dir),
        "output_dir": str(output_dir),
        "root_timeout_hard_negative_path": str(root_path),
        "deep_missing_context_path": str(missing_path),
        "root_hard_negative_rows": root_count,
        "root_hard_negative_label_count": sum(
            1 for row in root_rows if float(row.get("y_branch_score_hard_negative", 0.0)) > 0.5
        ),
        "deep_missing_context_rows": missing_count,
        baseline_label: _summarize_branch_events(baseline_events),
        alternative_label: _summarize_branch_events(alternative_events),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", type=Path, default=DEFAULT_BASELINE_DIR)
    parser.add_argument("--alternative-dir", type=Path, default=DEFAULT_ALTERNATIVE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--baseline-label", default="v568")
    parser.add_argument("--alternative-label", default="v569")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_timeout_evidence(
        baseline_dir=args.baseline_dir,
        alternative_dir=args.alternative_dir,
        output_dir=args.output_dir,
        baseline_label=str(args.baseline_label),
        alternative_label=str(args.alternative_label),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
