#!/usr/bin/env python3
"""Build branch counterfactual delta rows from forced-pair replays.

This is an offline audit.  It reads baseline/alternative CSV and branch-impact
audit artifacts only.  It does not run BPC, pricing, RMP, or produce official
bounds/certificates.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_counterfactual_delta_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_journey_branch_counterfactual_delta_zh.md"
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


def _load_branch_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_iter_jsonl(path / "branch_impact_rows.jsonl"))
            continue
        if path.name == "summary.json":
            rows.extend(_iter_jsonl(path.parent / "branch_impact_rows.jsonl"))
            payload = _read_json(path)
            raw_rows = payload.get("records")
            if isinstance(raw_rows, list):
                rows.extend(row for row in raw_rows if isinstance(row, dict))
            continue
        if path.suffix == ".jsonl":
            rows.extend(_iter_jsonl(path))
            continue
        payload = _read_json(path)
        raw_rows = payload.get("records")
        if isinstance(raw_rows, list):
            rows.extend(row for row in raw_rows if isinstance(row, dict))
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


def _instance_from_log_file(log_file: Any) -> str | None:
    text = str(log_file or "")
    marker = "BPC_future/logical_graph/"
    if marker not in text:
        return None
    instance = marker + text.split(marker, 1)[1]
    if instance.endswith(".jsonl"):
        instance = instance[: -len(".jsonl")]
    return instance or None


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
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    try:
        i = int(value[0])
        j = int(value[1])
    except (TypeError, ValueError):
        return None
    if i == j:
        return None
    return tuple(sorted((i, j)))


def _row_pair(row: dict[str, Any]) -> tuple[int, int] | None:
    if row.get("task_i") is None or row.get("task_j") is None:
        return None
    try:
        return tuple(sorted((int(row["task_i"]), int(row["task_j"]))))
    except (TypeError, ValueError):
        return None


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


def _labels(row: dict[str, Any]) -> dict[str, Any]:
    labels = row.get("branch_labels")
    return labels if isinstance(labels, dict) else {}


def _branch_metric(row: dict[str, Any], label_name: str) -> float:
    return _float(_labels(row).get(label_name))


def _find_baseline_row(
    rows: list[dict[str, Any]],
    *,
    instance: str,
    node_id: int,
    depth: int,
    selected_pair: tuple[int, int],
) -> dict[str, Any] | None:
    for row in rows:
        if _instance_from_log_file(row.get("log_file")) != instance:
            continue
        if _int(row.get("branch_node_id"), -1) != int(node_id):
            continue
        if _int(row.get("depth"), -1) != int(depth):
            continue
        if _row_pair(row) != selected_pair:
            continue
        return row
    return None


def _find_alt_row(
    rows: list[dict[str, Any]],
    *,
    instance: str,
    node_id: int,
    depth: int,
    forced_pair: tuple[int, int],
) -> dict[str, Any] | None:
    exact_matches: list[dict[str, Any]] = []
    fallback_matches: list[dict[str, Any]] = []
    for row in rows:
        if _instance_from_log_file(row.get("log_file")) != instance:
            continue
        if _int(row.get("branch_node_id"), -1) != int(node_id):
            continue
        if _int(row.get("depth"), -1) != int(depth):
            continue
        if _row_pair(row) != forced_pair:
            continue
        fallback_matches.append(row)
        if _pair(row.get("forced_pair")) == forced_pair and row.get("forced_pair_matched") is True:
            exact_matches.append(row)
    return exact_matches[0] if exact_matches else (fallback_matches[0] if fallback_matches else None)


def _counterfactual_row(
    entry: dict[str, Any],
    *,
    baseline_branch_rows: list[dict[str, Any]],
    alt_branch_rows: list[dict[str, Any]],
    baseline_results: dict[str, dict[str, Any]],
    min_wall_improvement: float,
) -> dict[str, Any] | None:
    instance = str(entry.get("instance") or "")
    selected_pair = _pair(entry.get("source_selected_pair"))
    forced_pair = _pair(entry.get("forced_pair"))
    if not instance or selected_pair is None or forced_pair is None:
        return None
    try:
        node_id = int(entry["source_node_id"])
        depth = int(entry["source_depth"])
    except (KeyError, TypeError, ValueError):
        return None
    baseline_row = _find_baseline_row(
        baseline_branch_rows,
        instance=instance,
        node_id=node_id,
        depth=depth,
        selected_pair=selected_pair,
    )
    alt_row = _find_alt_row(
        alt_branch_rows,
        instance=instance,
        node_id=node_id,
        depth=depth,
        forced_pair=forced_pair,
    )
    baseline_result = baseline_results.get(instance)
    alt_result = _load_result_row(_result_path_for_entry(entry), instance)
    if baseline_row is None or alt_row is None or baseline_result is None or alt_result is None:
        return None
    baseline_wall = _float(baseline_result.get("wall_time"))
    alt_wall = _float(alt_result.get("wall_time"))
    wall_delta = alt_wall - baseline_wall
    baseline_optimal = str(baseline_result.get("status") or "") == "OPTIMAL"
    alt_optimal = str(alt_result.get("status") or "") == "OPTIMAL"
    baseline_branch_count = _int(baseline_result.get("node_count"))
    alt_branch_count = _int(alt_result.get("node_count"))
    deltas = {
        "wall_time_delta": wall_delta,
        "solving_time_delta": _float(alt_result.get("solving_time")) - _float(baseline_result.get("solving_time")),
        "pricing_calls_delta": _int(alt_result.get("pricing_calls")) - _int(baseline_result.get("pricing_calls")),
        "exact_pricing_calls_delta": _int(alt_result.get("exact_pricing_calls"))
        - _int(baseline_result.get("exact_pricing_calls")),
        "node_count_delta": alt_branch_count - baseline_branch_count,
        "child_negative_pricing_events_delta": _branch_metric(alt_row, "y_child_negative_pricing_events")
        - _branch_metric(baseline_row, "y_child_negative_pricing_events"),
        "child_completion_bound_retries_delta": _branch_metric(alt_row, "y_child_completion_bound_retries")
        - _branch_metric(baseline_row, "y_child_completion_bound_retries"),
        "child_early_branch_triggers_delta": _branch_metric(alt_row, "y_child_early_branch_triggers")
        - _branch_metric(baseline_row, "y_child_early_branch_triggers"),
    }
    both_optimal = bool(baseline_optimal and alt_optimal)
    timeout_resolved = bool((not baseline_optimal) and alt_optimal)
    timeout_regression = bool(baseline_optimal and not alt_optimal)
    both_nonoptimal = bool((not baseline_optimal) and not alt_optimal)
    wall_improved = bool(both_optimal and float(wall_delta) <= -float(min_wall_improvement))
    proof_cost_proxy_improved = bool(
        deltas["exact_pricing_calls_delta"] < 0
        or deltas["child_completion_bound_retries_delta"] < 0
        or deltas["child_negative_pricing_events_delta"] < 0
        or deltas["node_count_delta"] < 0
    )
    proof_cost_improved = bool(both_optimal and proof_cost_proxy_improved)
    regression = bool(
        timeout_regression
        or (both_optimal and float(wall_delta) > float(min_wall_improvement))
    )
    usable_for_counterfactual_training = bool(both_optimal or timeout_resolved or timeout_regression)
    return {
        "schema_version": "journey_branch_counterfactual_delta_v2",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "experiment": entry.get("experiment"),
        "instance": instance,
        "node_id": node_id,
        "depth": depth,
        "baseline_pair": list(selected_pair),
        "alternative_pair": list(forced_pair),
        "alternative_forced_pair_matched": bool(alt_row.get("forced_pair_matched")),
        "baseline_status": baseline_result.get("status"),
        "alternative_status": alt_result.get("status"),
        "both_optimal": both_optimal,
        "both_nonoptimal": both_nonoptimal,
        "timeout_resolved": timeout_resolved,
        "timeout_regression": timeout_regression,
        "right_censored_counterfactual": bool(not usable_for_counterfactual_training),
        "usable_for_counterfactual_training": usable_for_counterfactual_training,
        "baseline_wall_time": baseline_wall,
        "alternative_wall_time": alt_wall,
        "baseline_solving_time": _float(baseline_result.get("solving_time")),
        "alternative_solving_time": _float(alt_result.get("solving_time")),
        "baseline_node_count": baseline_branch_count,
        "alternative_node_count": alt_branch_count,
        "baseline_pricing_calls": _int(baseline_result.get("pricing_calls")),
        "alternative_pricing_calls": _int(alt_result.get("pricing_calls")),
        "baseline_exact_pricing_calls": _int(baseline_result.get("exact_pricing_calls")),
        "alternative_exact_pricing_calls": _int(alt_result.get("exact_pricing_calls")),
        "baseline_tail_class": baseline_row.get("tail_class"),
        "alternative_tail_class": alt_row.get("tail_class"),
        "baseline_branch_labels": baseline_row.get("branch_labels"),
        "alternative_branch_labels": alt_row.get("branch_labels"),
        "deltas": {key: round(float(value), 9) for key, value in deltas.items()},
        "labels": {
            "y_counterfactual_wall_improved": 1.0 if wall_improved else 0.0,
            "y_counterfactual_proof_cost_improved": 1.0 if proof_cost_improved else 0.0,
            "y_counterfactual_proof_cost_proxy_improved": 1.0
            if proof_cost_proxy_improved
            else 0.0,
            "y_counterfactual_timeout_resolved": 1.0 if timeout_resolved else 0.0,
            "y_counterfactual_timeout_regression": 1.0 if timeout_regression else 0.0,
            "y_counterfactual_right_censored": 1.0
            if not usable_for_counterfactual_training
            else 0.0,
            "y_counterfactual_regression": 1.0 if regression else 0.0,
        },
        "baseline_raw_row": baseline_row,
        "alternative_raw_row": alt_row,
    }


def build_counterfactual_delta(
    runbook_path: Path,
    baseline_result_paths: list[Path],
    baseline_branch_inputs: list[Path],
    alt_branch_inputs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    min_wall_improvement: float = 1.0,
) -> dict[str, Any]:
    runbook = _read_json(runbook_path)
    entries = runbook.get("entries") if isinstance(runbook.get("entries"), list) else []
    baseline_branch_rows = _load_branch_rows(baseline_branch_inputs)
    alt_branch_rows = _load_branch_rows(alt_branch_inputs)
    baseline_results = _load_results(baseline_result_paths)
    rows = [
        row
        for entry in entries
        if isinstance(entry, dict)
        for row in [
            _counterfactual_row(
                entry,
                baseline_branch_rows=baseline_branch_rows,
                alt_branch_rows=alt_branch_rows,
                baseline_results=baseline_results,
                min_wall_improvement=min_wall_improvement,
            )
        ]
        if row is not None
    ]
    label_counts = Counter()
    for row in rows:
        labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
        for key, value in labels.items():
            if _float(value) > 0.5:
                label_counts[str(key)] += 1
    status_pairs = Counter(
        f"{row.get('baseline_status')}->{row.get('alternative_status')}" for row in rows
    )
    summary = {
        "schema_version": "journey_branch_counterfactual_delta_audit_v2",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "stage4_candidate_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "runbook": str(runbook_path),
        "baseline_result_paths": [str(path) for path in baseline_result_paths],
        "baseline_branch_input_paths": [str(path) for path in baseline_branch_inputs],
        "alt_branch_input_paths": [str(path) for path in alt_branch_inputs],
        "min_wall_improvement": float(min_wall_improvement),
        "runbook_entry_count": len(entries),
        "matched_counterfactual_count": len(rows),
        "forced_pair_matched_count": int(sum(1 for row in rows if row.get("alternative_forced_pair_matched"))),
        "usable_counterfactual_training_count": int(
            sum(1 for row in rows if row.get("usable_for_counterfactual_training"))
        ),
        "right_censored_counterfactual_count": int(
            sum(1 for row in rows if row.get("right_censored_counterfactual"))
        ),
        "timeout_resolved_count": int(sum(1 for row in rows if row.get("timeout_resolved"))),
        "timeout_regression_count": int(sum(1 for row in rows if row.get("timeout_regression"))),
        "label_positive_counts": dict(sorted(label_counts.items())),
        "status_pair_counts": dict(sorted(status_pairs.items())),
        "wall_improvement_positive_count": int(label_counts.get("y_counterfactual_wall_improved", 0)),
        "counterfactual_training_ready": bool(
            (
                label_counts.get("y_counterfactual_wall_improved", 0)
                + label_counts.get("y_counterfactual_timeout_resolved", 0)
            )
            > 0
            and label_counts.get("y_counterfactual_regression", 0) > 0
        ),
        "rows": rows,
    }
    write_outputs(summary, output_dir, report)
    return summary


def write_outputs(summary: dict[str, Any], output_dir: Path, report: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = list(summary.get("rows", []))
    summary_without_rows = dict(summary)
    summary_without_rows.pop("rows", None)
    (output_dir / "summary.json").write_text(
        json.dumps(summary_without_rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "branch_counterfactual_delta_rows.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_render_report(summary_without_rows, output_dir), encoding="utf-8")


def _render_report(summary: dict[str, Any], output_dir: Path) -> str:
    return "\n".join(
        [
            "# Journey Branch Counterfactual Delta Audit",
            "",
            f"日期：{date.today().isoformat()}",
            "",
            "## 目的",
            "",
            "把 baseline branch 选择与 forced-pair alternative replay 按同实例、同节点、同 depth 对齐，生成 wall/proof-cost delta 标签。该脚本只读既有 CSV 和审计产物，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
            "",
            "## 机器字段",
            "",
            "```text",
            "journey_branch_counterfactual_delta = current",
            f"output_dir = {output_dir}",
            f"runbook_entry_count = {summary.get('runbook_entry_count')}",
            f"matched_counterfactual_count = {summary.get('matched_counterfactual_count')}",
            f"forced_pair_matched_count = {summary.get('forced_pair_matched_count')}",
            f"usable_counterfactual_training_count = {summary.get('usable_counterfactual_training_count')}",
            f"right_censored_counterfactual_count = {summary.get('right_censored_counterfactual_count')}",
            f"timeout_resolved_count = {summary.get('timeout_resolved_count')}",
            f"timeout_regression_count = {summary.get('timeout_regression_count')}",
            f"label_positive_counts = {summary.get('label_positive_counts')}",
            f"status_pair_counts = {summary.get('status_pair_counts')}",
            f"wall_improvement_positive_count = {summary.get('wall_improvement_positive_count')}",
            f"counterfactual_training_ready = {str(summary.get('counterfactual_training_ready')).lower()}",
            "production_ready = false",
            "stage4_candidate_ready = false",
            "certificate_effect = false",
            "official_bound_effect = false",
            "```",
            "",
            "## 边界",
            "",
            "这些 delta row 只能训练或评估 branch 候选排序；不能作为剪枝依据、no-negative certificate、official bound 或 exact pricing 替代品。",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runbook", type=Path, required=True)
    parser.add_argument("--baseline-result", nargs="+", type=Path, required=True)
    parser.add_argument("--baseline-branch-input", nargs="+", type=Path, required=True)
    parser.add_argument("--alt-branch-input", nargs="+", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-wall-improvement", type=float, default=1.0)
    args = parser.parse_args()
    summary = build_counterfactual_delta(
        args.runbook,
        args.baseline_result,
        args.baseline_branch_input,
        args.alt_branch_input,
        args.output_dir,
        args.report,
        min_wall_improvement=args.min_wall_improvement,
    )
    printable = dict(summary)
    printable.pop("rows", None)
    print(json.dumps(printable, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
