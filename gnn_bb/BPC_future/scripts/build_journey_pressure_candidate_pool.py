#!/usr/bin/env python3
"""Build a pressure-aware Journey branch candidate replay queue.

This is a diagnostic/sample-generation helper only. It scans existing
``journey_branch_candidates`` logs, extracts candidates with nonzero Phase2
pricing-pressure severity, de-duplicates candidates already covered by replay
runbooks or delta rows, and emits a compact queue that can be passed back to
``build_journey_branch_candidate_replay_runbook.py --focus-candidate-input``.
It does not run BPC, pricing, RMP, or produce official bounds/certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
import json
from pathlib import Path
import shlex
import sys
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.scripts.build_journey_branch_candidate_replay_runbook import (
    DEFAULT_INSTANCE_ROOT,
    _candidate_pair,
    _float,
    _instance_from_log_path,
    _int,
    _iter_jsonl,
    _iter_jsonl_paths,
    _logged_candidates,
    _optional_float,
    _pair_from_value,
    _pair_text,
    _runbook_json_files,
)


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_pressure_candidate_pool_20260629")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260629_bpc_future_journey_pressure_candidate_pool_zh.md"
)
PHASE2_FIELDS = (
    "phase2_negative_child_count",
    "phase2_negative_journey_count",
    "phase2_negative_journey_balance_gap",
    "phase2_best_reduced_cost",
    "phase2_worst_negative_severity",
    "phase2_same_child_negative_severity",
    "phase2_separate_child_negative_severity",
    "phase2_negative_severity_sum",
    "phase2_negative_severity_gap",
    "phase2_negative_severity_balance_ratio",
    "phase2_negative_child_presence_balance_gap",
    "phase2_child_wall_time_balance_gap",
    "phase2_child_status_mismatch",
    "phase2_generated_sequences",
    "phase2_evaluated_timed_trips",
    "phase2_wall_time",
)


def _coverage_row_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    if path.is_dir():
        direct = path / "branch_counterfactual_delta_rows.jsonl"
        return [direct] if direct.exists() else []
    if path.name == "summary.json":
        return _coverage_row_files(path.parent)
    if path.suffix == ".jsonl":
        return [path]
    return []


def _coverage_key(row: dict[str, Any]) -> tuple[str, int, int, int, int] | None:
    instance = str(row.get("instance") or "")
    pair = _pair_from_value(
        row.get("candidate_pair") or row.get("alternative_pair") or row.get("forced_pair")
    )
    node_id = _int(row.get("source_node_id", row.get("node_id")), -1)
    depth = _int(row.get("source_depth", row.get("depth")), -1)
    if not instance or pair is None or node_id < 0 or depth < 0:
        return None
    return (instance, node_id, depth, int(pair[0]), int(pair[1]))


def _load_coverage(paths: Iterable[Path]) -> dict[tuple[str, int, int, int, int], list[str]]:
    coverage: dict[tuple[str, int, int, int, int], list[str]] = defaultdict(list)
    for path in paths:
        for row_file in _coverage_row_files(path):
            for row in _iter_jsonl(row_file):
                key = _coverage_key(row)
                if key is not None:
                    coverage[key].append(f"delta:{row_file}")
        for runbook_path in _runbook_json_files(path):
            try:
                payload = json.loads(runbook_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            entries = payload.get("entries")
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                key = _coverage_key(entry)
                if key is not None:
                    coverage[key].append(f"runbook:{runbook_path}")
    return coverage


def _coverage_status(sources: list[str]) -> str:
    if not sources:
        return "uncovered"
    if any(source.startswith("delta:") for source in sources):
        return "delta_observed"
    return "runbook_queued"


def _candidate_priority(row: dict[str, Any]) -> tuple[float, float, float, int, float, int]:
    return (
        -_float(row.get("phase2_negative_severity_sum"), 0.0),
        -_float(row.get("phase2_negative_severity_gap"), 0.0),
        -_float(row.get("phase2_negative_child_presence_balance_gap"), 0.0),
        _int(row.get("source_depth"), 999999),
        _float(row.get("source_event_time"), 1.0e30),
        _int(row.get("source_alt_rank"), 999999),
    )


def _context_key(row: dict[str, Any]) -> tuple[str, int, int, str]:
    return (
        str(row.get("instance") or ""),
        _int(row.get("source_node_id"), -1),
        _int(row.get("source_depth"), -1),
        _pair_text(_pair_from_value(row.get("source_selected_pair"))) or "",
    )


def _append_candidate(
    rows_by_key: dict[tuple[str, int, int, int, int], dict[str, Any]],
    row: dict[str, Any],
) -> bool:
    key = _coverage_key(row)
    if key is None:
        return False
    current = rows_by_key.get(key)
    if current is None or _candidate_priority(row) < _candidate_priority(current):
        rows_by_key[key] = row
        return current is not None
    return True


def build_pressure_candidate_pool(
    log_paths: list[Path],
    output_dir: Path,
    report: Path,
    *,
    instance_root: Path = DEFAULT_INSTANCE_ROOT,
    covered_inputs: list[Path] | None = None,
    candidate_source: str = "both",
    min_source_depth: int | None = None,
    max_source_depth: int | None = None,
    max_source_event_time: float | None = None,
    min_severity_sum: float = 0.0,
    max_queue: int = 12,
    max_per_context: int = 2,
    max_per_instance: int = 4,
) -> dict[str, Any]:
    if candidate_source not in {"priority_top", "top", "both"}:
        raise ValueError(f"unsupported candidate_source: {candidate_source}")
    if (
        min_source_depth is not None
        and max_source_depth is not None
        and int(min_source_depth) > int(max_source_depth)
    ):
        raise ValueError("min_source_depth must be <= max_source_depth")

    coverage = _load_coverage(covered_inputs or [])
    rows_by_key: dict[tuple[str, int, int, int, int], dict[str, Any]] = {}
    source_event_count = 0
    skipped_missing_instance_event_count = 0
    depth_filter_skip_count = 0
    source_event_time_filter_skip_count = 0
    low_pressure_skip_count = 0
    duplicate_candidate_count = 0

    for log_path in _iter_jsonl_paths(log_paths):
        events = list(_iter_jsonl(log_path))
        instance = _instance_from_log_path(log_path, instance_root)
        if instance is None:
            skipped_missing_instance_event_count += sum(
                1 for row in events if row.get("event") == "journey_branch_candidates"
            )
            continue
        for record in events:
            if record.get("event") != "journey_branch_candidates":
                continue
            source_event_count += 1
            node_id = _int(record.get("node_id"), -1)
            depth = _int(record.get("depth"), -1)
            source_event_time = _optional_float(record.get("time"))
            if min_source_depth is not None and depth < int(min_source_depth):
                depth_filter_skip_count += 1
                continue
            if max_source_depth is not None and depth > int(max_source_depth):
                depth_filter_skip_count += 1
                continue
            if (
                max_source_event_time is not None
                and source_event_time is not None
                and source_event_time > float(max_source_event_time)
            ):
                source_event_time_filter_skip_count += 1
                continue
            selected_pair = _candidate_pair(record.get("selected"))
            logged = _logged_candidates(record, candidate_source)
            for rank, candidate in enumerate(logged):
                pair = _candidate_pair(candidate)
                if pair is None or pair == selected_pair:
                    continue
                severity_sum = _float(candidate.get("phase2_negative_severity_sum"), 0.0)
                if severity_sum <= float(min_severity_sum):
                    low_pressure_skip_count += 1
                    continue
                row: dict[str, Any] = {
                    "schema_version": "journey_pressure_candidate_pool_v1",
                    "instance": instance,
                    "source_log_file": str(log_path),
                    "source_node_id": int(node_id),
                    "source_depth": int(depth),
                    "source_event_time": source_event_time,
                    "source_priority_mode": record.get("priority_mode"),
                    "source_candidate_count": record.get("candidate_count"),
                    "source_eligible_count": record.get("eligible_count"),
                    "source_logged_priority_count": len(record.get("priority_top") or []),
                    "source_logged_top_count": len(record.get("top") or []),
                    "source_selected_pair": None
                    if selected_pair is None
                    else [int(selected_pair[0]), int(selected_pair[1])],
                    "source_selected": record.get("selected"),
                    "candidate_pair": [int(pair[0]), int(pair[1])],
                    "source_alt_rank": int(rank),
                    "source_alt_fractionality": candidate.get("fractionality"),
                    "source_alt_pool_max_child_width": candidate.get("pool_max_child_width"),
                    "source_alt_pool_total_child_width": candidate.get("pool_total_child_width"),
                    "source_alt_pool_balance_gap": candidate.get("pool_balance_gap"),
                    "source_alt_branch_score": candidate.get("branch_score"),
                    "source_alt_branch_score_source": candidate.get("branch_score_source"),
                }
                for field in PHASE2_FIELDS:
                    row[field] = candidate.get(field)
                duplicate_candidate_count += int(_append_candidate(rows_by_key, row))

    candidate_rows = sorted(rows_by_key.values(), key=_candidate_priority)
    for row in candidate_rows:
        key = _coverage_key(row)
        sources = coverage.get(key or ("", -1, -1, -1, -1), [])
        row["coverage_status"] = _coverage_status(sources)
        row["coverage_sources"] = sources[:5]

    queue_rows: list[dict[str, Any]] = []
    per_context: Counter[tuple[str, int, int, str]] = Counter()
    per_instance: Counter[str] = Counter()
    for row in candidate_rows:
        if row.get("coverage_status") != "uncovered":
            continue
        context_key = _context_key(row)
        instance = str(row.get("instance") or "")
        if max_per_context >= 0 and per_context[context_key] >= int(max_per_context):
            continue
        if max_per_instance >= 0 and per_instance[instance] >= int(max_per_instance):
            continue
        queue_rows.append({**row, "queue_rank": len(queue_rows) + 1})
        per_context[context_key] += 1
        per_instance[instance] += 1
        if len(queue_rows) >= int(max_queue):
            break

    recommended_command = shlex.join(
        [
            "python",
            "BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py",
            *[str(path) for path in log_paths],
            "--focus-candidate-input",
            str(output_dir / "replay_queue.jsonl"),
            "--candidate-source",
            candidate_source,
            "--candidate-selection",
            "layered",
            "--paired-probe",
        ]
    )
    status_counts = Counter(str(row.get("coverage_status")) for row in candidate_rows)
    depth_counts = Counter(str(row.get("source_depth")) for row in candidate_rows)
    queue_depth_counts = Counter(str(row.get("source_depth")) for row in queue_rows)
    summary = {
        "schema_version": "journey_pressure_candidate_pool_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "production_ready": False,
        "source_log_paths": [str(path) for path in log_paths],
        "covered_input_paths": [str(path) for path in (covered_inputs or [])],
        "candidate_source": candidate_source,
        "min_source_depth": None if min_source_depth is None else int(min_source_depth),
        "max_source_depth": None if max_source_depth is None else int(max_source_depth),
        "max_source_event_time": None
        if max_source_event_time is None
        else float(max_source_event_time),
        "min_severity_sum": float(min_severity_sum),
        "max_queue": int(max_queue),
        "max_per_context": int(max_per_context),
        "max_per_instance": int(max_per_instance),
        "source_event_count": int(source_event_count),
        "candidate_row_count": len(candidate_rows),
        "queue_row_count": len(queue_rows),
        "coverage_key_count": len(coverage),
        "coverage_status_counts": dict(sorted(status_counts.items())),
        "candidate_depth_counts": dict(sorted(depth_counts.items())),
        "queue_depth_counts": dict(sorted(queue_depth_counts.items())),
        "skipped_missing_instance_event_count": int(skipped_missing_instance_event_count),
        "depth_filter_skip_count": int(depth_filter_skip_count),
        "source_event_time_filter_skip_count": int(source_event_time_filter_skip_count),
        "low_pressure_skip_count": int(low_pressure_skip_count),
        "duplicate_candidate_count": int(duplicate_candidate_count),
        "recommended_runbook_command": recommended_command,
        "candidate_pool_path": str(output_dir / "candidate_pool.jsonl"),
        "replay_queue_path": str(output_dir / "replay_queue.jsonl"),
        "top_queue_rows": queue_rows[:10],
    }
    write_outputs(summary, candidate_rows, queue_rows, output_dir, report)
    return summary


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_outputs(
    summary: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    queue_rows: list[dict[str, Any]],
    output_dir: Path,
    report: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(output_dir / "candidate_pool.jsonl", candidate_rows)
    _write_jsonl(output_dir / "replay_queue.jsonl", queue_rows)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Pressure Candidate Pool",
        "",
        f"Date: {date.today().isoformat()}",
        "",
        "## Boundary",
        "",
        (
            "This artifact is diagnostic only. It scans existing branch-candidate logs "
            "and writes a replay queue; it does not run BPC/pricing/RMP and does not "
            "create official lower bounds, certificates, pruning rules, or fathoming decisions."
        ),
        "",
        "## Machine Fields",
        "",
        "```text",
        f"output_dir = {output_dir}",
        f"candidate_pool_path = {summary.get('candidate_pool_path')}",
        f"replay_queue_path = {summary.get('replay_queue_path')}",
        f"source_event_count = {summary.get('source_event_count')}",
        f"candidate_row_count = {summary.get('candidate_row_count')}",
        f"queue_row_count = {summary.get('queue_row_count')}",
        f"coverage_key_count = {summary.get('coverage_key_count')}",
        f"coverage_status_counts = {summary.get('coverage_status_counts')}",
        f"candidate_depth_counts = {summary.get('candidate_depth_counts')}",
        f"queue_depth_counts = {summary.get('queue_depth_counts')}",
        f"low_pressure_skip_count = {summary.get('low_pressure_skip_count')}",
        f"duplicate_candidate_count = {summary.get('duplicate_candidate_count')}",
        f"skipped_missing_instance_event_count = {summary.get('skipped_missing_instance_event_count')}",
        f"depth_filter_skip_count = {summary.get('depth_filter_skip_count')}",
        f"source_event_time_filter_skip_count = {summary.get('source_event_time_filter_skip_count')}",
        "runs_bpc_or_pricing = false",
        "official_bound_effect = false",
        "certificate_effect = false",
        "```",
        "",
        "## Recommended Runbook Command",
        "",
        "```bash",
        str(summary.get("recommended_runbook_command") or ""),
        "```",
        "",
        "## Top Queue Rows",
        "",
    ]
    for row in queue_rows[:20]:
        lines.extend(
            [
                f"### queue_rank = {row.get('queue_rank')}",
                "",
                "```text",
                f"instance = {row.get('instance')}",
                f"source_log_file = {row.get('source_log_file')}",
                f"source_node_id = {row.get('source_node_id')}",
                f"source_depth = {row.get('source_depth')}",
                f"source_selected_pair = {row.get('source_selected_pair')}",
                f"candidate_pair = {row.get('candidate_pair')}",
                f"phase2_negative_severity_sum = {row.get('phase2_negative_severity_sum')}",
                f"phase2_negative_severity_gap = {row.get('phase2_negative_severity_gap')}",
                "phase2_negative_child_presence_balance_gap = "
                f"{row.get('phase2_negative_child_presence_balance_gap')}",
                f"coverage_status = {row.get('coverage_status')}",
                "```",
                "",
            ]
        )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_path", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--instance-root", type=Path, default=DEFAULT_INSTANCE_ROOT)
    parser.add_argument("--covered-input", nargs="*", type=Path, default=[])
    parser.add_argument(
        "--candidate-source",
        choices=("priority_top", "top", "both"),
        default="both",
    )
    parser.add_argument("--min-source-depth", type=int, default=None)
    parser.add_argument("--max-source-depth", type=int, default=None)
    parser.add_argument("--max-source-event-time", type=float, default=None)
    parser.add_argument("--min-severity-sum", type=float, default=0.0)
    parser.add_argument("--max-queue", type=int, default=12)
    parser.add_argument("--max-per-context", type=int, default=2)
    parser.add_argument("--max-per-instance", type=int, default=4)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = build_pressure_candidate_pool(
        list(args.log_path),
        args.output_dir,
        args.report,
        instance_root=args.instance_root,
        covered_inputs=list(args.covered_input),
        candidate_source=args.candidate_source,
        min_source_depth=args.min_source_depth,
        max_source_depth=args.max_source_depth,
        max_source_event_time=args.max_source_event_time,
        min_severity_sum=args.min_severity_sum,
        max_queue=args.max_queue,
        max_per_context=args.max_per_context,
        max_per_instance=args.max_per_instance,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
