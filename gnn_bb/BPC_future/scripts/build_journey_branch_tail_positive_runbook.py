#!/usr/bin/env python3
"""Build an audit-only runbook for collecting Journey branch-tail positives."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shlex
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_tail_positive_runbook_20260623")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260623_bpc_future_journey_branch_tail_positive_runbook_zh.md"
)
DEFAULT_CONFIG = Path("BPC_future/configs/moon_trek_20_smoke.yaml")
_RF_RE = re.compile(r"RF\((?P<i>\d+),(?P<j>\d+)\)=(?P<kind>same_vehicle|separate_vehicle)")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            yield record


def _instance_from_log_file(log_file: Any) -> str | None:
    text = str(log_file or "")
    direct_marker = "BPC_future/logical_graph/"
    if direct_marker in text:
        instance = direct_marker + text.split(direct_marker, 1)[1]
        if instance.endswith(".jsonl"):
            instance = instance[: -len(".jsonl")]
        return instance or None
    marker = "/logs/"
    if marker not in text:
        return None
    instance = text.split(marker, 1)[1]
    if instance.endswith(".jsonl"):
        instance = instance[: -len(".jsonl")]
    return instance or None


def _parse_rf_constraint(text: Any) -> dict[str, Any] | None:
    if not isinstance(text, str):
        return None
    match = _RF_RE.search(text)
    if match is None:
        return None
    return {
        "task_i": int(match.group("i")),
        "task_j": int(match.group("j")),
        "kind": str(match.group("kind")),
    }


def _safe_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")
    return slug[:160] or "instance"


def _finite_float(value: Any, default: float = 1.0e30) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _optional_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return float(parsed)


def _load_tail_impact_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_iter_jsonl(path / "tail_impact_training_rows.jsonl"))
            continue
        if path.name == "summary.json":
            rows.extend(_iter_jsonl(path.parent / "tail_impact_training_rows.jsonl"))
            continue
        if path.suffix == ".jsonl":
            rows.extend(_iter_jsonl(path))
            continue
        payload = _read_json(path)
        raw_rows = payload.get("rows")
        if isinstance(raw_rows, list):
            rows.extend(row for row in raw_rows if isinstance(row, dict))
    return rows


def _unique_root_pairs(rows: Iterable[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    for row in rows:
        if str(row.get("source_type") or "") != "branch_impact":
            continue
        if int(row.get("depth") or 0) != 0:
            continue
        instance = _instance_from_log_file(row.get("log_file"))
        if instance is None:
            continue
        task_i = row.get("task_i")
        task_j = row.get("task_j")
        if task_i is None or task_j is None:
            continue
        pair = tuple(sorted((int(task_i), int(task_j))))
        key = (instance, pair[0], pair[1])
        if key in seen:
            continue
        seen.add(key)
        selected.append({**row, "instance": instance, "task_i": pair[0], "task_j": pair[1]})
        if len(selected) >= int(limit):
            break
    return selected


def _read_log_events(log_file: Any) -> list[dict[str, Any]]:
    path = Path(str(log_file or ""))
    if not path.exists():
        return []
    return list(_iter_jsonl(path))


def _node_parent_path(events: list[dict[str, Any]], node_id: int) -> list[dict[str, Any]]:
    parent_by_child: dict[int, dict[str, Any]] = {}
    depth_by_node: dict[int, int] = {}
    for record in events:
        if record.get("event") == "journey_node_start" and record.get("node_id") is not None:
            try:
                depth_by_node[int(record["node_id"])] = int(record.get("depth", 0))
            except (TypeError, ValueError):
                pass
        if record.get("event") != "journey_child_queued":
            continue
        if record.get("child_node_id") is None or record.get("parent_node_id") is None:
            continue
        parsed = _parse_rf_constraint(record.get("constraint"))
        if parsed is None:
            continue
        try:
            child_id = int(record["child_node_id"])
            parent_id = int(record["parent_node_id"])
            child_depth = int(record.get("depth", 0))
        except (TypeError, ValueError):
            continue
        parent_by_child[child_id] = {
            "child_node_id": child_id,
            "parent_node_id": parent_id,
            "parent_depth": child_depth - 1,
            "task_i": min(int(parsed["task_i"]), int(parsed["task_j"])),
            "task_j": max(int(parsed["task_i"]), int(parsed["task_j"])),
            "kind": parsed["kind"],
        }
    path: list[dict[str, Any]] = []
    current = int(node_id)
    seen: set[int] = set()
    while current in parent_by_child and current not in seen:
        seen.add(current)
        edge = parent_by_child[current]
        path.append(edge)
        current = int(edge["parent_node_id"])
    path.reverse()
    for edge in path:
        parent_id = int(edge["parent_node_id"])
        if parent_id in depth_by_node:
            edge["parent_depth"] = int(depth_by_node[parent_id])
    return path


def _preferred_unstarted_child_kind(events: list[dict[str, Any]], parent_node_id: int) -> str | None:
    children: list[dict[str, Any]] = []
    for record in events:
        if record.get("event") != "journey_child_queued":
            continue
        try:
            if int(record.get("parent_node_id")) != int(parent_node_id):
                continue
        except (TypeError, ValueError):
            continue
        parsed = _parse_rf_constraint(record.get("constraint"))
        if parsed is None:
            continue
        child_id = record.get("child_node_id")
        if child_id is None:
            continue
        try:
            children.append({"child_node_id": int(child_id), "kind": parsed["kind"]})
        except (TypeError, ValueError):
            pass
    started = {
        int(record.get("node_id"))
        for record in events
        if record.get("event") == "journey_node_start" and record.get("node_id") is not None
    }
    for child in children:
        if int(child["child_node_id"]) not in started:
            return str(child["kind"])
    return None if not children else ("separate_vehicle" if children[0]["kind"] == "same_vehicle" else "same_vehicle")


def _branch_candidate_event_for_node(
    events: list[dict[str, Any]],
    *,
    node_id: int,
    depth: int,
) -> dict[str, Any] | None:
    for record in events:
        if record.get("event") != "journey_branch_candidates":
            continue
        try:
            if int(record.get("node_id")) != int(node_id):
                continue
            if int(record.get("depth")) != int(depth):
                continue
        except (TypeError, ValueError):
            continue
        return record
    return None


def _tail_action_alternative_branch_pairs(
    events: list[dict[str, Any]],
    *,
    node_id: int,
    depth: int,
    selected_task_i: int,
    selected_task_j: int,
    limit: int,
) -> list[dict[str, Any]]:
    if int(limit) <= 0:
        return []
    record = _branch_candidate_event_for_node(events, node_id=node_id, depth=depth)
    if record is None:
        return []
    priority_top = record.get("priority_top")
    if not isinstance(priority_top, list):
        return []
    selected_pair = tuple(sorted((int(selected_task_i), int(selected_task_j))))
    selected_payload = record.get("selected") if isinstance(record.get("selected"), dict) else {}
    selected_fractionality = _optional_float(selected_payload.get("fractionality"))
    alternatives: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = {selected_pair}
    for rank, candidate in enumerate(priority_top):
        if not isinstance(candidate, dict):
            continue
        task_i = candidate.get("task_i")
        task_j = candidate.get("task_j")
        if task_i is None or task_j is None:
            continue
        try:
            pair = tuple(sorted((int(task_i), int(task_j))))
        except (TypeError, ValueError):
            continue
        if pair in seen:
            continue
        seen.add(pair)
        alt_fractionality = _optional_float(candidate.get("fractionality"))
        fractionality_gap = (
            None
            if selected_fractionality is None or alt_fractionality is None
            else max(0.0, selected_fractionality - alt_fractionality)
        )
        alternatives.append(
            {
                "task_i": pair[0],
                "task_j": pair[1],
                "source_alt_rank": int(rank),
                "source_alt_fractionality": candidate.get("fractionality"),
                "source_selected_fractionality": selected_payload.get("fractionality"),
                "source_alt_fractionality_gap_to_selected": (
                    None if fractionality_gap is None else round(float(fractionality_gap), 9)
                ),
                "source_alt_required_tie_tolerance": (
                    None if fractionality_gap is None else round(float(fractionality_gap), 9)
                ),
                "source_alt_pool_max_child_width": candidate.get("pool_max_child_width"),
                "source_alt_pool_total_child_width": candidate.get("pool_total_child_width"),
                "source_alt_pool_balance_gap": candidate.get("pool_balance_gap"),
                "source_alt_same_mass": candidate.get("same_mass"),
                "source_alt_support_count": candidate.get("support_count"),
                "source_alt_incumbent_disagreement": candidate.get("incumbent_disagreement"),
                "source_selected_rank": 0,
                "source_selected_pool_max_child_width": selected_payload.get("pool_max_child_width"),
                "source_selected_pool_total_child_width": selected_payload.get("pool_total_child_width"),
                "source_selected_pool_balance_gap": selected_payload.get("pool_balance_gap"),
                "source_selected_same_mass": selected_payload.get("same_mass"),
                "source_selected_support_count": selected_payload.get("support_count"),
                "source_selected_incumbent_disagreement": selected_payload.get("incumbent_disagreement"),
                "source_branch_selected": record.get("selected"),
            }
        )
    alternatives.sort(
        key=lambda item: (
            _finite_float(item.get("source_alt_pool_max_child_width")),
            _finite_float(item.get("source_alt_pool_total_child_width")),
            _finite_float(item.get("source_alt_pool_balance_gap")),
            int(item.get("source_alt_rank") or 0),
        )
    )
    return alternatives[: int(limit)]


def _force_pair_depth_rule(path_edges: list[dict[str, Any]], target_depth: int, task_i: int, task_j: int) -> str:
    rules: list[str] = []
    for edge in path_edges:
        rules.append(f"{int(edge['parent_depth'])}:{int(edge['task_i'])},{int(edge['task_j'])}")
    rules.append(f"{int(target_depth)}:{int(task_i)},{int(task_j)}")
    return "force_pair_depth:" + ";".join(rules)


def _force_pair_path_rule(path_edges: list[dict[str, Any]], target_depth: int, task_i: int, task_j: int) -> str:
    rules: list[str] = []
    for edge in path_edges:
        rules.append(
            f"{int(edge['parent_depth'])}:{int(edge['task_i'])},{int(edge['task_j'])}={edge['kind']}"
        )
    rules.append(f"{int(target_depth)}:{int(task_i)},{int(task_j)}")
    return "force_pair_path:" + ";".join(rules)


def _force_child_kind_depth_rule(
    path_edges: list[dict[str, Any]],
    target_depth: int,
    target_kind: str | None,
) -> str:
    rules = [f"{int(edge['parent_depth'])}:{edge['kind']}" for edge in path_edges]
    if target_kind in {"same_vehicle", "separate_vehicle"}:
        rules.append(f"{int(target_depth)}:{target_kind}")
    return "force_child_kind_depth:" + ";".join(rules)


def _tail_action_child_order_candidates(rows: Iterable[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int, int]] = set()
    for row in rows:
        if str(row.get("source_type") or "") != "tail_action_proof_cost":
            continue
        labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
        if float(labels.get("y_tail_risk") or 0.0) <= 0.5:
            continue
        instance = _instance_from_log_file(row.get("log_file"))
        if instance is None:
            continue
        task_i = row.get("task_i")
        task_j = row.get("task_j")
        if task_i is None or task_j is None:
            continue
        node_id = row.get("node_id")
        depth = row.get("depth")
        if node_id is None or depth is None:
            continue
        key = (instance, int(node_id), min(int(task_i), int(task_j)), max(int(task_i), int(task_j)))
        if key in seen:
            continue
        seen.add(key)
        selected.append(
            {
                **row,
                "instance": instance,
                "node_id": int(node_id),
                "depth": int(depth),
                "task_i": min(int(task_i), int(task_j)),
                "task_j": max(int(task_i), int(task_j)),
            }
        )
        if len(selected) >= int(limit):
            break
    return selected


def build_runbook(
    positive_gap_summary: Path,
    output_dir: Path,
    report: Path,
    *,
    config: Path = DEFAULT_CONFIG,
    time_limit: int = 200,
    limit: int = 8,
    tail_impact_inputs: list[Path] | None = None,
    tail_alt_pairs_per_node: int = 0,
) -> dict[str, Any]:
    summary = _read_json(positive_gap_summary)
    rows = summary.get("near_positive_rows")
    if not isinstance(rows, list):
        rows = []
    root_rows = _unique_root_pairs((row for row in rows if isinstance(row, dict)), limit)
    run_root = output_dir / "runs"
    entries: list[dict[str, Any]] = []
    for index, row in enumerate(root_rows, start=1):
        instance = str(row["instance"])
        task_i = int(row["task_i"])
        task_j = int(row["task_j"])
        experiment = f"{index:02d}_force_pair_{task_i}_{task_j}_{_safe_slug(Path(instance).stem)}"
        result_dir = run_root / experiment
        command = [
            "/home/kai/miniconda3/bin/python",
            "BPC_future/scripts/run_bpc_future_external_timeout_batch.py",
            "--config",
            str(config),
            "--instances",
            instance,
            "--time-limit",
            str(int(time_limit)),
            "--results-csv",
            str(result_dir / "results.csv"),
            "--log-dir",
            str(result_dir / "logs"),
            "--solution-dir",
            str(result_dir / "solutions"),
            "--run-log-dir",
            str(result_dir / "run_logs"),
            "--python",
            "/home/kai/miniconda3/bin/python",
            "--timeout-kill-after",
            "30s",
            "--max-workers",
            "1",
            "--quiet",
            "--set",
            "journey_early_branching_enabled=True",
            "--set",
            "journey_early_branching_min_cg_iter=56",
            "--set",
            "journey_early_branching_child_min_cg_iter=3",
            "--set",
            "journey_early_branching_max_depth=1",
            "--set",
            "journey_child_priority_by_width_enabled=True",
            "--set",
            "journey_early_branching_after_incomplete_no_column_enabled=True",
            "--set",
            "journey_early_branching_after_incomplete_no_column_min_remaining=20.0",
            "--set",
            "journey_branch_fractionality_tie_tolerance=0.05",
            "--set",
            f"journey_branch_candidate_priority=force_pair:{task_i},{task_j}",
            "--set",
            "journey_branch_candidate_log_top_n=12",
        ]
        entries.append(
            {
                "experiment": experiment,
                "instance": instance,
                "forced_pair": [task_i, task_j],
                "source_log_file": row.get("log_file"),
                "source_tail_class": row.get("tail_class"),
                "source_tail_badness_score": row.get("tail_badness_score"),
                "source_child_negative_pricing_events": row.get("y_child_negative_pricing_events"),
                "command": command,
                "shell_command": shlex.join(command),
                "expected_label_source": "rerun_then_audit_branch_impact",
            }
        )
    tail_rows = _load_tail_impact_rows(tail_impact_inputs or [])
    for row in _tail_action_child_order_candidates(tail_rows, limit):
        instance = str(row["instance"])
        task_i = int(row["task_i"])
        task_j = int(row["task_j"])
        node_id = int(row["node_id"])
        depth = int(row["depth"])
        events = _read_log_events(row.get("log_file"))
        path_edges = _node_parent_path(events, node_id)
        preferred_kind = _preferred_unstarted_child_kind(events, node_id)
        force_pair_rule = _force_pair_path_rule(path_edges, depth, task_i, task_j)
        force_kind_rule = _force_child_kind_depth_rule(path_edges, depth, preferred_kind)
        entry_index = len(entries) + 1
        experiment = (
            f"{entry_index:02d}_tail_action_child_order_d{depth}_n{node_id}_"
            f"{task_i}_{task_j}_{preferred_kind or 'default'}_{_safe_slug(Path(instance).stem)}"
        )
        result_dir = run_root / experiment
        command = [
            "/home/kai/miniconda3/bin/python",
            "BPC_future/scripts/run_bpc_future_external_timeout_batch.py",
            "--config",
            str(config),
            "--instances",
            instance,
            "--time-limit",
            str(int(time_limit)),
            "--results-csv",
            str(result_dir / "results.csv"),
            "--log-dir",
            str(result_dir / "logs"),
            "--solution-dir",
            str(result_dir / "solutions"),
            "--run-log-dir",
            str(result_dir / "run_logs"),
            "--python",
            "/home/kai/miniconda3/bin/python",
            "--timeout-kill-after",
            "30s",
            "--max-workers",
            "1",
            "--quiet",
            "--set",
            "journey_early_branching_enabled=False",
            "--set",
            "journey_tail_action_early_branch_enabled=True",
            "--set",
            "journey_tail_action_early_branch_min_cg_iter=35",
            "--set",
            "journey_tail_action_early_branch_child_min_cg_iter=2",
            "--set",
            "journey_tail_action_early_branch_max_depth=1",
            "--set",
            "journey_tail_action_early_branch_min_true_rc_productivity=1",
            "--set",
            "journey_tail_action_child_priority_enabled=True",
            "--set",
            "journey_tail_action_child_priority_width=-1",
            "--set",
            "journey_tail_action_no_column_early_branch_enabled=True",
            "--set",
            "journey_tail_action_no_column_early_branch_min_depth=2",
            "--set",
            "journey_tail_action_no_column_early_branch_max_depth=2",
            "--set",
            "journey_tail_action_no_column_early_branch_child_min_cg_iter=1",
            "--set",
            "journey_tail_action_no_column_early_branch_min_true_rc_productivity=0",
            "--set",
            "journey_tail_action_no_column_early_branch_require_complete_productivity_signals=False",
            "--set",
            "journey_tail_action_no_column_early_branch_max_pool_child_width=180",
            "--set",
            "journey_tail_action_no_column_early_branch_max_pool_total_child_width=360",
            "--set",
            "journey_tail_action_no_column_early_branch_max_pool_balance_gap=180",
            "--set",
            "journey_branch_fractionality_tie_tolerance=0.05",
            "--set",
            f"journey_branch_candidate_priority={force_pair_rule}",
            "--set",
            f"journey_child_priority_mode={force_kind_rule}",
            "--set",
            "journey_branch_candidate_log_top_n=12",
        ]
        entries.append(
            {
                "experiment": experiment,
                "instance": instance,
                "forced_pair": [task_i, task_j],
                "forced_pair_depth_rule": force_pair_rule,
                "forced_pair_path_rule": force_pair_rule,
                "forced_child_kind_depth_rule": force_kind_rule,
                "preferred_target_child_kind": preferred_kind,
                "source_type": "tail_action_proof_cost",
                "source_log_file": row.get("log_file"),
                "source_node_id": node_id,
                "source_depth": depth,
                "source_tail_class": row.get("tail_class"),
                "source_labels": row.get("labels"),
                "source_path_edges": path_edges,
                "command": command,
                "shell_command": shlex.join(command),
                "expected_label_source": "rerun_then_audit_tail_action_and_build_tail_impact",
            }
        )
        for alt in _tail_action_alternative_branch_pairs(
            events,
            node_id=node_id,
            depth=depth,
            selected_task_i=task_i,
            selected_task_j=task_j,
            limit=int(tail_alt_pairs_per_node),
        ):
            alt_task_i = int(alt["task_i"])
            alt_task_j = int(alt["task_j"])
            alt_pair_rule = _force_pair_path_rule(path_edges, depth, alt_task_i, alt_task_j)
            ancestor_kind_rule = _force_child_kind_depth_rule(path_edges, depth, None)
            alt_experiment = (
                f"{len(entries) + 1:02d}_tail_action_alt_pair_d{depth}_n{node_id}_"
                f"r{int(alt['source_alt_rank'])}_{alt_task_i}_{alt_task_j}_{_safe_slug(Path(instance).stem)}"
            )
            alt_result_dir = run_root / alt_experiment
            alt_command = [
                "/home/kai/miniconda3/bin/python",
                "BPC_future/scripts/run_bpc_future_external_timeout_batch.py",
                "--config",
                str(config),
                "--instances",
                instance,
                "--time-limit",
                str(int(time_limit)),
                "--results-csv",
                str(alt_result_dir / "results.csv"),
                "--log-dir",
                str(alt_result_dir / "logs"),
                "--solution-dir",
                str(alt_result_dir / "solutions"),
                "--run-log-dir",
                str(alt_result_dir / "run_logs"),
                "--python",
                "/home/kai/miniconda3/bin/python",
                "--timeout-kill-after",
                "30s",
                "--max-workers",
                "1",
                "--quiet",
                "--set",
                "journey_early_branching_enabled=False",
                "--set",
                "journey_tail_action_early_branch_enabled=True",
                "--set",
                "journey_tail_action_early_branch_min_cg_iter=35",
                "--set",
                "journey_tail_action_early_branch_child_min_cg_iter=2",
                "--set",
                "journey_tail_action_early_branch_max_depth=1",
                "--set",
                "journey_tail_action_early_branch_min_true_rc_productivity=1",
                "--set",
                "journey_tail_action_child_priority_enabled=True",
                "--set",
                "journey_tail_action_child_priority_width=-1",
                "--set",
                "journey_tail_action_no_column_early_branch_enabled=True",
                "--set",
                "journey_tail_action_no_column_early_branch_min_depth=2",
                "--set",
                "journey_tail_action_no_column_early_branch_max_depth=2",
                "--set",
                "journey_tail_action_no_column_early_branch_child_min_cg_iter=1",
                "--set",
                "journey_tail_action_no_column_early_branch_min_true_rc_productivity=0",
                "--set",
                "journey_tail_action_no_column_early_branch_require_complete_productivity_signals=False",
                "--set",
                "journey_tail_action_no_column_early_branch_max_pool_child_width=180",
                "--set",
                "journey_tail_action_no_column_early_branch_max_pool_total_child_width=360",
                "--set",
                "journey_tail_action_no_column_early_branch_max_pool_balance_gap=180",
                "--set",
                "journey_branch_fractionality_tie_tolerance=0.05",
                "--set",
                f"journey_branch_candidate_priority={alt_pair_rule}",
                "--set",
                f"journey_child_priority_mode={ancestor_kind_rule}",
                "--set",
                "journey_branch_candidate_log_top_n=12",
            ]
            entries.append(
                {
                    "experiment": alt_experiment,
                    "instance": instance,
                    "forced_pair": [alt_task_i, alt_task_j],
                    "forced_pair_depth_rule": alt_pair_rule,
                    "forced_pair_path_rule": alt_pair_rule,
                    "forced_child_kind_depth_rule": ancestor_kind_rule,
                    "preferred_target_child_kind": None,
                    "source_type": "tail_action_alt_pair",
                    "source_log_file": row.get("log_file"),
                    "source_node_id": node_id,
                    "source_depth": depth,
                    "source_original_forced_pair": [task_i, task_j],
                    "source_tail_class": row.get("tail_class"),
                    "source_labels": row.get("labels"),
                    "source_path_edges": path_edges,
                    "command": alt_command,
                    "shell_command": shlex.join(alt_command),
                    "expected_label_source": "rerun_then_audit_tail_action_alt_pair_and_build_tail_impact",
                    **alt,
                }
            )
    runbook = {
        "schema_version": "journey_branch_tail_positive_runbook_v2",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "stage4_candidate_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "base_sample_strategy": "extend_existing_5000_with_branch_tail_interventions",
        "positive_gap_summary": str(positive_gap_summary),
        "tail_impact_input_paths": [str(path) for path in (tail_impact_inputs or [])],
        "tail_alt_pairs_per_node": int(tail_alt_pairs_per_node),
        "config": str(config),
        "time_limit": int(time_limit),
        "candidate_source": "root_level_near_positive_rows_tail_action_proof_cost_rows_and_optional_priority_top_alt_pairs",
        "entry_count": len(entries),
        "entries": entries,
        "notes": (
            "These commands are opt-in positive collection probes.  They force a "
            "legal fractional Ryan-Foster pair if present, but exact pricing and "
            "certificate semantics remain unchanged.  Tail-action entries also "
            "force ancestor depth pairs and child-kind ordering when the source "
            "log provides enough path information. Optional alternative-pair "
            "entries replace the target-depth pair with a priority_top branch "
            "candidate from the same log while keeping certificate semantics "
            "unchanged. This is still a replay heuristic, not a certificate or "
            "bound source."
        ),
    }
    write_outputs(runbook, output_dir, report)
    return runbook


def write_outputs(runbook: dict[str, Any], output_dir: Path, report: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "runbook.json").write_text(
        json.dumps(runbook, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "commands.sh").write_text(
        "\n".join(entry["shell_command"] for entry in runbook.get("entries", [])) + "\n",
        encoding="utf-8",
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_render_report(runbook, output_dir), encoding="utf-8")


def _render_report(runbook: dict[str, Any], output_dir: Path) -> str:
    lines = [
        "# Journey Branch-Tail Positive Collection Runbook",
        "",
        "日期：2026-06-23",
        "",
        "## 目的",
        "",
        "在已有 5000 个 Stage 3 样本基础上追加 branch-tail intervention 样本，而不是重新生成全部样本。runbook 只生成 opt-in 命令，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "journey_branch_tail_positive_runbook = current",
        f"output_dir = {output_dir}",
        f"entry_count = {runbook.get('entry_count')}",
        f"base_sample_strategy = {runbook.get('base_sample_strategy')}",
        f"candidate_source = {runbook.get('candidate_source')}",
        f"tail_impact_input_paths = {runbook.get('tail_impact_input_paths')}",
        f"tail_alt_pairs_per_node = {runbook.get('tail_alt_pairs_per_node')}",
        "production_ready = false",
        "stage4_candidate_ready = false",
        "certificate_effect = false",
        "official_bound_effect = false",
        "```",
        "",
        "## 条目",
        "",
    ]
    for entry in runbook.get("entries", []):
        lines.extend(
            [
                f"### {entry['experiment']}",
                "",
                "```text",
                f"instance = {entry['instance']}",
                f"forced_pair = {entry['forced_pair']}",
                f"forced_pair_depth_rule = {entry.get('forced_pair_depth_rule')}",
                f"forced_pair_path_rule = {entry.get('forced_pair_path_rule')}",
                f"forced_child_kind_depth_rule = {entry.get('forced_child_kind_depth_rule')}",
                f"preferred_target_child_kind = {entry.get('preferred_target_child_kind')}",
                f"source_tail_class = {entry.get('source_tail_class')}",
                f"source_tail_badness_score = {entry.get('source_tail_badness_score')}",
                f"source_type = {entry.get('source_type')}",
                f"source_original_forced_pair = {entry.get('source_original_forced_pair')}",
                f"source_alt_rank = {entry.get('source_alt_rank')}",
                f"source_selected_fractionality = {entry.get('source_selected_fractionality')}",
                f"source_alt_fractionality = {entry.get('source_alt_fractionality')}",
                f"source_alt_fractionality_gap_to_selected = {entry.get('source_alt_fractionality_gap_to_selected')}",
                f"source_alt_required_tie_tolerance = {entry.get('source_alt_required_tie_tolerance')}",
                f"source_alt_pool_max_child_width = {entry.get('source_alt_pool_max_child_width')}",
                f"source_alt_pool_total_child_width = {entry.get('source_alt_pool_total_child_width')}",
                "```",
                "",
                "```bash",
                entry["shell_command"],
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## 边界",
            "",
            "这些命令只改变 Ryan-Foster 候选选择顺序和可选的 child queue 顺序；如果 forced pair 不是当前合法 fractional candidate，会回退到默认 fractionality 选择。最终 no-negative closure 仍只来自 exact pricing。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("positive_gap_summary", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--time-limit", type=int, default=200)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--tail-impact-input", nargs="*", type=Path, default=[])
    parser.add_argument("--tail-alt-pairs-per-node", type=int, default=0)
    args = parser.parse_args()

    runbook = build_runbook(
        args.positive_gap_summary,
        args.output_dir,
        args.report,
        config=args.config,
        time_limit=args.time_limit,
        limit=args.limit,
        tail_impact_inputs=args.tail_impact_input,
        tail_alt_pairs_per_node=args.tail_alt_pairs_per_node,
    )
    print(json.dumps(runbook, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
