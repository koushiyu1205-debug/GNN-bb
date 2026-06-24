#!/usr/bin/env python3
"""Audit tail-action counterfactual replays.

This is an offline diagnostic.  It compares tail-action proof-cost rows from a
baseline run against alternative replay rows generated from a runbook.  It does
not run BPC, pricing, RMP, or produce official bounds/certificates.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_tail_action_counterfactual_delta_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_journey_tail_action_counterfactual_delta_zh.md"
)


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


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_tail_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_iter_jsonl(path / "tail_impact_training_rows.jsonl"))
            continue
        if path.name == "summary.json":
            rows.extend(_iter_jsonl(path.parent / "tail_impact_training_rows.jsonl"))
            continue
        if path.name == "tail_impact_training_rows.jsonl" or path.suffix == ".jsonl":
            rows.extend(_iter_jsonl(path))
    return rows


def _load_results(paths: Iterable[Path]) -> dict[str, dict[str, Any]]:
    by_instance: dict[str, dict[str, Any]] = {}
    for path in paths:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                instance = str(row.get("instance") or "")
                if instance:
                    by_instance[instance] = dict(row)
    return by_instance


def _load_result_row(path: Path | None, instance: str) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if str(row.get("instance") or "") == str(instance):
                return dict(row)
    return None


def _float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return int(default)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _pair(value: Any) -> tuple[int, int] | None:
    if isinstance(value, str):
        pieces = [piece.strip() for piece in value.replace(";", ",").split(",") if piece.strip()]
        if len(pieces) != 2:
            return None
        try:
            i, j = int(pieces[0]), int(pieces[1])
        except ValueError:
            return None
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            i, j = int(value[0]), int(value[1])
        except (TypeError, ValueError):
            return None
    else:
        return None
    if i == j:
        return None
    return tuple(sorted((i, j)))


def _row_pair(row: dict[str, Any]) -> tuple[int, int] | None:
    raw = row.get("raw_source")
    raw = raw if isinstance(raw, dict) else {}
    if raw.get("no_column_branch_task_i") is not None and raw.get("no_column_branch_task_j") is not None:
        return _pair([raw.get("no_column_branch_task_i"), raw.get("no_column_branch_task_j")])
    if row.get("task_i") is not None and row.get("task_j") is not None:
        return _pair([row.get("task_i"), row.get("task_j")])
    return None


def _instance_from_log_file(log_file: Any) -> str | None:
    text = str(log_file or "")
    marker = "BPC_future/logical_graph/"
    if marker not in text:
        return None
    instance = marker + text.split(marker, 1)[1]
    if instance.endswith(".jsonl"):
        instance = instance[: -len(".jsonl")]
    return instance or None


def _row_instance(row: dict[str, Any]) -> str | None:
    return _instance_from_log_file(row.get("log_file"))


def _command_value(command: Any, flag: str) -> str | None:
    if not isinstance(command, list):
        return None
    for index, item in enumerate(command):
        if str(item) == flag and index + 1 < len(command):
            return str(command[index + 1])
    return None


def _result_path_for_entry(entry: dict[str, Any]) -> Path | None:
    value = _command_value(entry.get("command"), "--results-csv")
    return None if value is None else Path(value)


def _find_tail_row(
    rows: list[dict[str, Any]],
    *,
    instance: str,
    node_id: int,
    depth: int,
    pair: tuple[int, int],
) -> dict[str, Any] | None:
    for row in rows:
        if str(row.get("source_type") or "") != "tail_action_proof_cost":
            continue
        if _row_instance(row) != instance:
            continue
        if _int(row.get("node_id"), -1) != int(node_id):
            continue
        if _int(row.get("depth"), -1) != int(depth):
            continue
        if _row_pair(row) != pair:
            continue
        return row
    return None


def _raw(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get("raw_source")
    return raw if isinstance(raw, dict) else {}


def _labels(row: dict[str, Any]) -> dict[str, Any]:
    labels = row.get("labels")
    return labels if isinstance(labels, dict) else {}


def _metric(row: dict[str, Any], raw_key: str, label_key: str | None = None) -> float:
    raw = _raw(row)
    if raw_key in raw:
        return _float(raw.get(raw_key))
    if label_key is not None:
        return _float(_labels(row).get(label_key))
    return 0.0


def _tail_cost(row: dict[str, Any]) -> float:
    pricing = _metric(row, "child_subtree_pricing_event_count")
    negative = _metric(row, "child_subtree_negative_pricing_event_count", "y_child_negative_pricing_events")
    retries = _metric(row, "child_subtree_completion_retry_count", "y_child_completion_bound_retries")
    early = _metric(row, "child_subtree_early_branch_trigger_count", "y_child_early_branch_triggers")
    no_column = _metric(row, "child_subtree_no_column_early_branch_trigger_count", "y_subtree_no_column_chain")
    unstarted = _metric(row, "child_direct_unstarted_count", "y_child_unstarted")
    return float(negative + retries + no_column + 0.25 * early + 0.05 * pricing + 5.0 * unstarted)


def _compact_tail(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_id": _int(row.get("node_id"), -1),
        "depth": _int(row.get("depth"), -1),
        "pair": list(_row_pair(row) or (-1, -1)),
        "tail_cost": round(_tail_cost(row), 9),
        "pricing_events": round(_metric(row, "child_subtree_pricing_event_count"), 9),
        "negative_pricing_events": round(
            _metric(row, "child_subtree_negative_pricing_event_count", "y_child_negative_pricing_events"),
            9,
        ),
        "completion_retries": round(
            _metric(row, "child_subtree_completion_retry_count", "y_child_completion_bound_retries"),
            9,
        ),
        "early_branch_triggers": round(
            _metric(row, "child_subtree_early_branch_trigger_count", "y_child_early_branch_triggers"),
            9,
        ),
        "no_column_chain": round(
            _metric(row, "child_subtree_no_column_early_branch_trigger_count", "y_subtree_no_column_chain"),
            9,
        ),
        "observed_wall_span": round(_metric(row, "child_subtree_observed_wall_span"), 9),
    }


def _status(row: dict[str, Any] | None) -> str:
    if not row:
        return ""
    return str(row.get("status") or "")


def _counterfactual_row(
    entry: dict[str, Any],
    *,
    baseline_tail_rows: list[dict[str, Any]],
    alternative_tail_rows: list[dict[str, Any]],
    baseline_results: dict[str, dict[str, Any]],
    min_wall_improvement: float,
    min_local_cost_improvement: float,
) -> dict[str, Any] | None:
    if str(entry.get("source_type") or "") != "tail_action_alt_pair":
        return None
    instance = str(entry.get("instance") or "")
    baseline_pair = _pair(entry.get("source_original_forced_pair"))
    alternative_pair = _pair(entry.get("forced_pair"))
    if not instance or baseline_pair is None or alternative_pair is None:
        return None
    try:
        node_id = int(entry["source_node_id"])
        depth = int(entry["source_depth"])
    except (KeyError, TypeError, ValueError):
        return None
    baseline_tail = _find_tail_row(
        baseline_tail_rows,
        instance=instance,
        node_id=node_id,
        depth=depth,
        pair=baseline_pair,
    )
    alternative_tail = _find_tail_row(
        alternative_tail_rows,
        instance=instance,
        node_id=node_id,
        depth=depth,
        pair=alternative_pair,
    )
    baseline_result = baseline_results.get(instance)
    alternative_result = _load_result_row(_result_path_for_entry(entry), instance)
    if baseline_tail is None or alternative_tail is None or baseline_result is None or alternative_result is None:
        return None

    baseline_tail_cost = _tail_cost(baseline_tail)
    alternative_tail_cost = _tail_cost(alternative_tail)
    local_tail_cost_delta = alternative_tail_cost - baseline_tail_cost
    local_improved = bool(local_tail_cost_delta <= -float(min_local_cost_improvement))

    baseline_wall = _float(baseline_result.get("wall_time"))
    alternative_wall = _float(alternative_result.get("wall_time"))
    baseline_optimal = _status(baseline_result) == "OPTIMAL"
    alternative_optimal = _status(alternative_result) == "OPTIMAL"
    both_optimal = bool(baseline_optimal and alternative_optimal)
    timeout_resolved = bool((not baseline_optimal) and alternative_optimal)
    timeout_regression = bool(baseline_optimal and not alternative_optimal)
    both_nonoptimal = bool((not baseline_optimal) and not alternative_optimal)
    wall_improved = bool(both_optimal and (alternative_wall - baseline_wall) <= -float(min_wall_improvement))
    whole_run_improved = bool(timeout_resolved or wall_improved)
    right_censored = bool(both_nonoptimal)
    local_only = bool(local_improved and not whole_run_improved)

    deltas = {
        "local_tail_cost_delta": local_tail_cost_delta,
        "local_pricing_events_delta": _metric(alternative_tail, "child_subtree_pricing_event_count")
        - _metric(baseline_tail, "child_subtree_pricing_event_count"),
        "local_negative_pricing_events_delta": _metric(
            alternative_tail,
            "child_subtree_negative_pricing_event_count",
            "y_child_negative_pricing_events",
        )
        - _metric(
            baseline_tail,
            "child_subtree_negative_pricing_event_count",
            "y_child_negative_pricing_events",
        ),
        "local_completion_retries_delta": _metric(
            alternative_tail,
            "child_subtree_completion_retry_count",
            "y_child_completion_bound_retries",
        )
        - _metric(
            baseline_tail,
            "child_subtree_completion_retry_count",
            "y_child_completion_bound_retries",
        ),
        "local_no_column_chain_delta": _metric(
            alternative_tail,
            "child_subtree_no_column_early_branch_trigger_count",
            "y_subtree_no_column_chain",
        )
        - _metric(
            baseline_tail,
            "child_subtree_no_column_early_branch_trigger_count",
            "y_subtree_no_column_chain",
        ),
        "wall_time_delta": alternative_wall - baseline_wall,
    }
    return {
        "schema_version": "journey_tail_action_counterfactual_delta_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "experiment": entry.get("experiment"),
        "instance": instance,
        "node_id": node_id,
        "depth": depth,
        "baseline_pair": list(baseline_pair),
        "alternative_pair": list(alternative_pair),
        "baseline_status": _status(baseline_result),
        "alternative_status": _status(alternative_result),
        "baseline_wall_time": baseline_wall,
        "alternative_wall_time": alternative_wall,
        "both_optimal": both_optimal,
        "both_nonoptimal": both_nonoptimal,
        "timeout_resolved": timeout_resolved,
        "timeout_regression": timeout_regression,
        "right_censored_counterfactual": right_censored,
        "baseline_tail": _compact_tail(baseline_tail),
        "alternative_tail": _compact_tail(alternative_tail),
        "deltas": {key: round(float(value), 9) for key, value in deltas.items()},
        "labels": {
            "y_local_tail_improved": 1.0 if local_improved else 0.0,
            "y_whole_run_improved": 1.0 if whole_run_improved else 0.0,
            "y_local_improved_but_whole_run_not": 1.0 if local_only else 0.0,
            "y_timeout_resolved": 1.0 if timeout_resolved else 0.0,
            "y_timeout_regression": 1.0 if timeout_regression else 0.0,
            "y_right_censored_counterfactual": 1.0 if right_censored else 0.0,
        },
    }


def audit_tail_action_counterfactual_delta(
    runbook_path: Path,
    baseline_tail_inputs: list[Path],
    alternative_tail_inputs: list[Path],
    baseline_result_paths: list[Path],
    output_dir: Path,
    report: Path,
    *,
    min_wall_improvement: float = 1.0,
    min_local_cost_improvement: float = 1.0,
) -> dict[str, Any]:
    runbook = _read_json(runbook_path)
    entries = runbook.get("entries") if isinstance(runbook.get("entries"), list) else []
    baseline_tail_rows = _load_tail_rows(baseline_tail_inputs)
    alternative_tail_rows = _load_tail_rows(alternative_tail_inputs)
    baseline_results = _load_results(baseline_result_paths)
    rows = [
        row
        for entry in entries
        if isinstance(entry, dict)
        for row in [
            _counterfactual_row(
                entry,
                baseline_tail_rows=baseline_tail_rows,
                alternative_tail_rows=alternative_tail_rows,
                baseline_results=baseline_results,
                min_wall_improvement=min_wall_improvement,
                min_local_cost_improvement=min_local_cost_improvement,
            )
        ]
        if row is not None
    ]
    label_counts: Counter[str] = Counter()
    status_pairs: Counter[str] = Counter()
    for row in rows:
        labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
        for key, value in labels.items():
            if _float(value) > 0.5:
                label_counts[str(key)] += 1
        status_pairs[f"{row.get('baseline_status')}->{row.get('alternative_status')}"] += 1

    summary = {
        "schema_version": "journey_tail_action_counterfactual_delta_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "stage4_candidate_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "runbook": str(runbook_path),
        "baseline_tail_input_paths": [str(path) for path in baseline_tail_inputs],
        "alternative_tail_input_paths": [str(path) for path in alternative_tail_inputs],
        "baseline_result_paths": [str(path) for path in baseline_result_paths],
        "runbook_entry_count": len(entries),
        "matched_counterfactual_count": len(rows),
        "min_wall_improvement": float(min_wall_improvement),
        "min_local_cost_improvement": float(min_local_cost_improvement),
        "label_positive_counts": dict(sorted(label_counts.items())),
        "status_pair_counts": dict(sorted(status_pairs.items())),
        "local_tail_improved_count": int(label_counts.get("y_local_tail_improved", 0)),
        "whole_run_improved_count": int(label_counts.get("y_whole_run_improved", 0)),
        "local_improved_but_whole_run_not_count": int(
            label_counts.get("y_local_improved_but_whole_run_not", 0)
        ),
        "right_censored_counterfactual_count": int(
            label_counts.get("y_right_censored_counterfactual", 0)
        ),
        "whole_run_training_ready": bool(label_counts.get("y_whole_run_improved", 0) > 0),
        "hard_negative_catalog_ready": bool(rows),
        "rows": rows,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "tail_action_counterfactual_delta_rows.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_render_report(summary), encoding="utf-8")
    return summary


def _render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Journey Tail-Action Counterfactual Delta",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 机器字段",
        "",
        "```text",
        "journey_tail_action_counterfactual_delta = current",
        f"matched_counterfactual_count = {summary.get('matched_counterfactual_count')}",
        f"local_tail_improved_count = {summary.get('local_tail_improved_count')}",
        f"whole_run_improved_count = {summary.get('whole_run_improved_count')}",
        "production_ready = false",
        "certificate_effect = false",
        "official_bound_effect = false",
        "```",
        "",
        "## Label Counts",
        "",
    ]
    for key, value in sorted((summary.get("label_positive_counts") or {}).items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Rows", ""])
    for row in summary.get("rows", [])[:10]:
        lines.append(
            "- "
            f"{row.get('experiment')}: pair {row.get('baseline_pair')} -> {row.get('alternative_pair')}, "
            f"status {row.get('baseline_status')} -> {row.get('alternative_status')}, "
            f"local_delta={row.get('deltas', {}).get('local_tail_cost_delta')}, "
            f"wall_delta={row.get('deltas', {}).get('wall_time_delta')}, "
            f"labels={row.get('labels')}"
        )
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "这些 rows 只用于离线反事实诊断和 hard-negative/positive gap 标注；不能作为 branch oracle、pricing oracle、official bound 或 certificate。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runbook", type=Path)
    parser.add_argument("--baseline-tail-input", nargs="+", type=Path, required=True)
    parser.add_argument("--alternative-tail-input", nargs="+", type=Path, required=True)
    parser.add_argument("--baseline-results", nargs="+", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-wall-improvement", type=float, default=1.0)
    parser.add_argument("--min-local-cost-improvement", type=float, default=1.0)
    args = parser.parse_args()
    summary = audit_tail_action_counterfactual_delta(
        args.runbook,
        args.baseline_tail_input,
        args.alternative_tail_input,
        args.baseline_results,
        args.output_dir,
        args.report,
        min_wall_improvement=args.min_wall_improvement,
        min_local_cost_improvement=args.min_local_cost_improvement,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
