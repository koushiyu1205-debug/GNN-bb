#!/usr/bin/env python3
"""Build hard-negative evidence from failed branch-score opt-in full runs.

This script is offline and diagnostic-only.  It reads completed result CSVs and
their JSONL branch logs, then exports:

- overlay-compatible timeout hard-negative rows for scored branch choices;
- tree-policy event rows that can train the auxiliary proof-tail risk head.

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
from typing import Any, Iterable


DEFAULT_RUN_ROOT = Path("BPC_future/results/journey_branch_score_ab_runbook_v609_v608_highscore_external_20260628/runs")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_score_failure_evidence_v610_v609_v608_highscore_external_20260628")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260628_bpc_future_journey_branch_score_failure_evidence_v610_zh.md"
)


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


def _float(value: Any, default: float = 0.0) -> float:
    parsed = _finite_float(value)
    return float(default) if parsed is None else float(parsed)


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _pair(value: Any) -> list[int] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    left = _int(value[0], -1)
    right = _int(value[1], -1)
    if left <= 0 or right <= 0 or left == right:
        return None
    return [min(left, right), max(left, right)]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
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


def _instance_from_log(path: Path) -> str:
    text = str(path).replace("\\", "/")
    marker = "/logs/"
    if marker in text:
        text = text.split(marker, 1)[1]
    if text.endswith(".jsonl"):
        text = text[: -len(".jsonl")]
    return text


def _result_instance_key(row: dict[str, str]) -> str:
    return Path(str(row.get("instance") or "")).name


def _result_status(row: dict[str, str]) -> str:
    return str(row.get("status") or "")


def _result_wall(row: dict[str, str]) -> float | None:
    return _finite_float(row.get("wall_time")) or _finite_float(row.get("solving_time"))


def _gap_available(row: dict[str, str]) -> bool:
    return str(row.get("gap_available") or "").strip().lower() == "true"


def _candidate_key(event: dict[str, Any]) -> tuple[int, int]:
    return (_int(event.get("node_id")), _int(event.get("depth")))


def _result_files(run_root: Path) -> list[Path]:
    files: list[Path] = []
    flat = run_root / "results.csv"
    if flat.exists():
        files.append(flat)
    files.extend(sorted(run_root.glob("*/score_horizon/results.csv")))
    return files


def _log_files(run_root: Path) -> list[Path]:
    files: dict[str, Path] = {}
    flat_logs = run_root / "logs"
    if flat_logs.exists():
        for path in sorted(flat_logs.glob("**/*.jsonl")):
            files[str(path)] = path
    for path in sorted(run_root.glob("*/score_horizon/logs/**/*.jsonl")):
        files[str(path)] = path
    return [files[key] for key in sorted(files)]


def _selected_candidate(candidates_event: dict[str, Any] | None, selected_pair: list[int]) -> dict[str, Any]:
    if not candidates_event:
        return {}
    for key in ("top", "priority_top"):
        rows = candidates_event.get(key)
        if not isinstance(rows, list):
            continue
        for candidate in rows:
            if not isinstance(candidate, dict):
                continue
            pair = _pair([candidate.get("task_i"), candidate.get("task_j")])
            if pair == selected_pair:
                return dict(candidate)
    selected = candidates_event.get("selected")
    if isinstance(selected, dict):
        pair = _pair([selected.get("task_i"), selected.get("task_j")])
        if pair == selected_pair:
            return dict(selected)
    return {}


def _branch_feature_vector(row: dict[str, Any], selected_raw: dict[str, Any]) -> list[float]:
    vector = selected_raw.get("branch_feature_vector")
    if isinstance(vector, list):
        return [_float(value) for value in vector]
    incumbent_relation = selected_raw.get("incumbent_relation")
    relation_known = 0.0 if incumbent_relation is None else 1.0
    relation_same = 1.0 if incumbent_relation is True else 0.0
    values = [
        _float(row.get("depth")),
        _float(row.get("candidate_count")),
        _float(row.get("eligible_count"), _float(row.get("candidate_count"))),
        1.0,
        0.0,
        0.0,
        _float(selected_raw.get("same_mass")),
        _float(selected_raw.get("fractionality")),
        _float(selected_raw.get("support_count")),
        relation_known,
        relation_same,
        _float(selected_raw.get("incumbent_disagreement")),
        _float(selected_raw.get("pool_same_allowed")),
        _float(selected_raw.get("pool_separate_allowed")),
        _float(selected_raw.get("pool_max_child_width")),
        _float(selected_raw.get("pool_total_child_width")),
        _float(selected_raw.get("pool_balance_gap")),
    ]
    return [float(value) for value in values]


def _event_loss_weight(event: dict[str, Any], *, selected_pair_changed: bool) -> float:
    score = _finite_float(event.get("selected_score"))
    base = 0.25
    if selected_pair_changed:
        base = 0.5
    if score is not None:
        base = max(base, min(0.75, float(score)))
    return float(base)


def _timeout_hard_negative_row(
    event: dict[str, Any],
    *,
    result_row: dict[str, str],
    instance: str,
    log_file: Path,
    source_experiment: str,
    completion_bound_retry_count: int,
    ordinary_retry_count: int,
) -> dict[str, Any]:
    status = _result_status(result_row)
    selected_pair = _pair(event.get("selected_pair")) or []
    selected_pair_changed = _as_bool(event.get("selected_pair_changed"))
    return {
        "schema_version": "journey_branch_score_failure_hard_negative_v1",
        "source_experiment": source_experiment,
        "baseline_experiment": "",
        "instance": instance,
        "log_file": str(log_file),
        "node_id": event.get("node_id"),
        "depth": event.get("depth"),
        "branch_state_key": event.get("branch_state_key"),
        "branch_constraints": event.get("branch_constraints"),
        "candidate_count": event.get("candidate_count"),
        "eligible_count": event.get("eligible_count"),
        "score_available_count": event.get("score_available_count"),
        "score_missing_count": event.get("score_missing_count"),
        "score_map_context_allowed": event.get("score_map_context_allowed"),
        "baseline_pair": _pair(event.get("baseline_pair")) or event.get("baseline_pair"),
        "baseline_rank": event.get("baseline_rank"),
        "selected_pair": selected_pair,
        "selected_pair_changed": selected_pair_changed,
        "selected_score": event.get("selected_score"),
        "selected_score_source": event.get("selected_score_source"),
        "score_gate_passed": _as_bool(event.get("branch_score_selection_gate_passed")),
        "score_gate_reason": event.get("branch_score_selection_gate_reason"),
        "baseline_status": "",
        "baseline_wall_time": None,
        "baseline_gap": None,
        "alternative_status": status,
        "alternative_wall_time": _result_wall(result_row),
        "alternative_gap": _finite_float(result_row.get("gap")),
        "alternative_primal_bound": _finite_float(result_row.get("primal_bound")),
        "alternative_dual_bound": _finite_float(result_row.get("dual_bound")),
        "alternative_gap_available": _gap_available(result_row),
        "gap_source": result_row.get("gap_source"),
        "run_completion_bound_retry_count": int(completion_bound_retry_count),
        "run_ordinary_retry_count": int(ordinary_retry_count),
        "label_type": "score_selected_full_run_timeout_hard_negative",
        "y_branch_score_hard_negative": 1.0 if status != "OPTIMAL" and selected_pair else 0.0,
        "reason": "score-selected branch choice appeared in a non-optimal full run; diagnostic hard negative only",
    }


def _tree_policy_row(
    event: dict[str, Any],
    candidates_event: dict[str, Any] | None,
    *,
    result_row: dict[str, str],
    instance: str,
    log_file: Path,
    source_experiment: str,
    completion_bound_retry_count: int,
) -> dict[str, Any]:
    selected_pair = _pair(event.get("selected_pair")) or []
    selected_raw = _selected_candidate(candidates_event, selected_pair) if selected_pair else {}
    row = {
        "schema_version": "journey_tree_policy_event_row_v1",
        "source_schema_version": "journey_branch_score_failure_hard_negative_v1",
        "policy_run": source_experiment,
        "instance": instance,
        "log_file": str(log_file),
        "node_id": event.get("node_id"),
        "depth": event.get("depth"),
        "branch_time": event.get("time"),
        "branch_state_key": event.get("branch_state_key"),
        "branch_constraints": event.get("branch_constraints"),
        "candidate_count": event.get("candidate_count"),
        "eligible_count": event.get("eligible_count"),
        "baseline_pair": _pair(event.get("baseline_pair")) or event.get("baseline_pair"),
        "selected_pair": selected_pair,
        "selected_pair_changed": _as_bool(event.get("selected_pair_changed")),
        "selected_score": event.get("selected_score"),
        "selected_score_source": event.get("selected_score_source"),
        "selected_raw": selected_raw,
        "top": [] if candidates_event is None else candidates_event.get("top", []),
        "priority_top": [] if candidates_event is None else candidates_event.get("priority_top", []),
        "branch_feature_vector": _branch_feature_vector(event, selected_raw),
        "tree_policy_label_type": "proof_tail_full_run_timeout_hard_negative",
        "y_tree_policy_positive": 0.0,
        "y_tree_policy_hard_negative": 1.0,
        "event_loss_weight": _event_loss_weight(
            event,
            selected_pair_changed=_as_bool(event.get("selected_pair_changed")),
        ),
        "right_censored": True,
        "proof_tail_risk": True,
        "status": _result_status(result_row),
        "wall_time": _result_wall(result_row),
        "gap": _finite_float(result_row.get("gap")),
        "gap_available": _gap_available(result_row),
        "gap_source": result_row.get("gap_source"),
        "run_completion_bound_retry_count": int(completion_bound_retry_count),
        "child_proof_cpu": 0.0,
        "child_proof_cpu_loss_weight": 0.0,
        "child_time_to_certificate": 0.0,
        "time_to_certificate_loss_weight": 0.0,
    }
    return row


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def _write_report(report: Path, summary: dict[str, Any]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# V610 Branch Score Failure Evidence",
        "",
        f"source_experiment = `{summary['source_experiment']}`",
        f"run_root = `{summary['run_root']}`",
        f"output_dir = `{summary['output_dir']}`",
        "",
        "## 结论",
        "",
        "本脚本把已完成且未最优的 branch-score opt-in full run 转成 diagnostic hard-negative evidence。输出只用于训练/overlay 调度，不能产生 official bound、certificate 或剪枝依据。",
        "",
        "## 汇总",
        "",
        "```text",
        f"result_rows = {summary['result_rows']}",
        f"nonoptimal_result_rows = {summary['nonoptimal_result_rows']}",
        f"branch_events = {summary['branch_events']}",
        f"scored_branch_events = {summary['scored_branch_events']}",
        f"hard_negative_rows = {summary['hard_negative_rows']}",
        f"tree_policy_rows = {summary['tree_policy_rows']}",
        f"status_counts = {summary['status_counts']}",
        f"depth_counts = {summary['depth_counts']}",
        f"selected_pair_changed_count = {summary['selected_pair_changed_count']}",
        f"completion_bound_retry_count = {summary['completion_bound_retry_count']}",
        "official_bound_effect = false",
        "certificate_effect = false",
        "production_ready = false",
        "```",
        "",
        "## 输出",
        "",
        f"- timeout hard-negative: `{summary['timeout_hard_negative_path']}`",
        f"- tree-policy event rows: `{summary['tree_policy_event_path']}`",
        f"- summary: `{Path(summary['output_dir']) / 'summary.json'}`",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_failure_evidence(
    *,
    run_root: Path,
    output_dir: Path,
    report: Path,
    source_experiment: str,
    min_selected_score: float = 0.0,
) -> dict[str, Any]:
    results: dict[str, dict[str, str]] = {}
    for result_path in _result_files(run_root):
        for row in _read_csv(result_path):
            if row.get("instance"):
                results[_result_instance_key(row)] = row

    hard_negative_rows: list[dict[str, Any]] = []
    tree_policy_rows: list[dict[str, Any]] = []
    branch_events = 0
    scored_branch_events = 0
    selected_pair_changed_count = 0
    completion_bound_retry_count = 0
    ordinary_retry_count = 0
    depth_counts: Counter[int] = Counter()
    status_counts: Counter[str] = Counter()

    for result in results.values():
        status_counts[_result_status(result)] += 1

    for log_file in _log_files(run_root):
        instance = _instance_from_log(log_file)
        result_row = results.get(Path(instance).name, {})
        status = _result_status(result_row)
        if status == "OPTIMAL":
            continue
        candidates_by_key: dict[tuple[int, int], dict[str, Any]] = {}
        events = list(_iter_jsonl(log_file))
        log_completion_bound_retry_count = sum(
            1
            for event in events
            if event.get("event")
            in {"journey_exact_pricing_completion_bound_retry", "journey_exact_pricing_completion_bound_escalation_retry"}
        )
        log_ordinary_retry_count = sum(1 for event in events if event.get("event") == "journey_exact_pricing_retry")
        completion_bound_retry_count += int(log_completion_bound_retry_count)
        ordinary_retry_count += int(log_ordinary_retry_count)
        for event in events:
            if event.get("event") == "journey_branch_candidates":
                candidates_by_key[_candidate_key(event)] = event
        for event in events:
            if event.get("event") != "journey_branch":
                continue
            branch_events += 1
            depth_counts[_int(event.get("depth"))] += 1
            selected_score = _finite_float(event.get("selected_score"))
            if selected_score is None or selected_score < float(min_selected_score):
                continue
            selected_pair = _pair(event.get("selected_pair"))
            if selected_pair is None:
                continue
            scored_branch_events += 1
            if _as_bool(event.get("selected_pair_changed")):
                selected_pair_changed_count += 1
            candidates_event = candidates_by_key.get(_candidate_key(event))
            hard_negative_rows.append(
                _timeout_hard_negative_row(
                    event,
                    result_row=result_row,
                    instance=instance,
                    log_file=log_file,
                    source_experiment=source_experiment,
                    completion_bound_retry_count=int(log_completion_bound_retry_count),
                    ordinary_retry_count=int(log_ordinary_retry_count),
                )
            )
            tree_policy_rows.append(
                _tree_policy_row(
                    event,
                    candidates_event,
                    result_row=result_row,
                    instance=instance,
                    log_file=log_file,
                    source_experiment=source_experiment,
                    completion_bound_retry_count=int(log_completion_bound_retry_count),
                )
            )

    timeout_path = output_dir / "score_timeout_hard_negative_rows.jsonl"
    tree_path = output_dir / "tree_policy_event_rows.jsonl"
    hard_count = _write_jsonl(timeout_path, hard_negative_rows)
    tree_count = _write_jsonl(tree_path, tree_policy_rows)
    summary = {
        "schema_version": "journey_branch_score_failure_evidence_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "production_ready": False,
        "source_experiment": source_experiment,
        "run_root": str(run_root),
        "output_dir": str(output_dir),
        "timeout_hard_negative_path": str(timeout_path),
        "tree_policy_event_path": str(tree_path),
        "min_selected_score": float(min_selected_score),
        "result_rows": len(results),
        "nonoptimal_result_rows": sum(1 for row in results.values() if _result_status(row) != "OPTIMAL"),
        "branch_events": int(branch_events),
        "scored_branch_events": int(scored_branch_events),
        "hard_negative_rows": int(hard_count),
        "tree_policy_rows": int(tree_count),
        "selected_pair_changed_count": int(selected_pair_changed_count),
        "completion_bound_retry_count": int(completion_bound_retry_count),
        "ordinary_retry_count": int(ordinary_retry_count),
        "status_counts": dict(sorted(status_counts.items())),
        "depth_counts": {str(key): value for key, value in sorted(depth_counts.items())},
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--source-experiment", default="v609_v608_highscore_external")
    parser.add_argument("--min-selected-score", type=float, default=0.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_failure_evidence(
        run_root=args.run_root,
        output_dir=args.output_dir,
        report=args.report,
        source_experiment=str(args.source_experiment),
        min_selected_score=float(args.min_selected_score),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if int(summary["hard_negative_rows"]) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
