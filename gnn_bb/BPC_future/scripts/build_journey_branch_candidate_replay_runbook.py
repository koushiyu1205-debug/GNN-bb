#!/usr/bin/env python3
"""Build forced-pair replay commands directly from Journey branch-candidate logs.

This is a diagnostic/sample-generation helper only. It reads existing
``journey_branch_candidates`` JSONL events and emits a runbook of replay
commands that force alternative Ryan-Foster pairs at the same branch path. It
does not run BPC, pricing, RMP, or produce official bounds/certificates.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import shlex
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_candidate_replay_runbook_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_journey_branch_candidate_replay_runbook_zh.md"
)
DEFAULT_CONFIG = Path("BPC_future/configs/moon_trek_20_smoke.yaml")
DEFAULT_INSTANCE_ROOT = Path("BPC_future/logical_graph")
_RF_RE = re.compile(r"RF\((?P<i>\d+),(?P<j>\d+)\)=(?P<kind>same_vehicle|separate_vehicle)")


def _iter_jsonl_paths(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.suffix == ".jsonl":
            yield path
        elif path.is_dir():
            yield from sorted(path.rglob("*.jsonl"))


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


def _parse_rf_constraint(text: Any) -> dict[str, Any] | None:
    if not isinstance(text, str):
        return None
    match = _RF_RE.search(text)
    if match is None:
        return None
    i = int(match.group("i"))
    j = int(match.group("j"))
    return {"task_i": min(i, j), "task_j": max(i, j), "kind": str(match.group("kind"))}


def _safe_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")
    return slug[:160] or "instance"


def _float(value: Any, default: float = 1.0e30) -> float:
    if value is None or value == "":
        return float(default)
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


def _int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return int(default)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _candidate_pair(candidate: Any) -> tuple[int, int] | None:
    if not isinstance(candidate, dict):
        return None
    if candidate.get("task_i") is None or candidate.get("task_j") is None:
        return None
    try:
        i, j = int(candidate["task_i"]), int(candidate["task_j"])
    except (TypeError, ValueError):
        return None
    if i == j:
        return None
    return tuple(sorted((i, j)))


def _pair_text(pair: tuple[int, int] | None) -> str | None:
    if pair is None:
        return None
    return f"{int(pair[0])},{int(pair[1])}"


def _pair_from_value(value: Any) -> tuple[int, int] | None:
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


def _load_branch_impact_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
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


def _branch_row_pair(row: dict[str, Any]) -> tuple[int, int] | None:
    if row.get("task_i") is None or row.get("task_j") is None:
        return None
    try:
        i, j = int(row["task_i"]), int(row["task_j"])
    except (TypeError, ValueError):
        return None
    if i == j:
        return None
    return tuple(sorted((i, j)))


def _impact_priority(row: dict[str, Any]) -> tuple[float, str]:
    labels = row.get("branch_labels")
    labels = labels if isinstance(labels, dict) else {}
    active_touch = _float(labels.get("y_active_touch"), default=0.0)
    completion_retries = _float(labels.get("y_child_completion_bound_retries"), default=0.0)
    negative_events = _float(labels.get("y_child_negative_pricing_events"), default=0.0)
    unprocessed = 1.0 if str(row.get("tail_class") or "") == "unprocessed_children" else 0.0
    completion_tail = 1.0 if str(row.get("tail_class") or "") == "completion_bound_tail" else 0.0
    right_censored = 1.0 if bool(row.get("right_censored")) else 0.0
    score = (
        10.0 * active_touch
        + 2.0 * completion_retries
        + negative_events
        + 5.0 * unprocessed
        + 2.0 * completion_tail
        + right_censored
    )
    reason = (
        f"active_touch={active_touch:g};completion_retries={completion_retries:g};"
        f"negative_events={negative_events:g};tail_class={row.get('tail_class')};"
        f"right_censored={bool(row.get('right_censored'))}"
    )
    return score, reason


def _impact_priority_by_context(
    branch_impact_inputs: Iterable[Path],
    *,
    instance_root: Path,
) -> dict[tuple[str, int, int, str], dict[str, Any]]:
    priority: dict[tuple[str, int, int, str], dict[str, Any]] = {}
    for row in _load_branch_impact_rows(branch_impact_inputs):
        instance = _instance_from_log_path(Path(str(row.get("log_file") or "")), instance_root)
        pair = _branch_row_pair(row)
        if instance is None or pair is None:
            continue
        node_id = _int(row.get("branch_node_id"), -1)
        depth = _int(row.get("depth"), -1)
        if node_id < 0 or depth < 0:
            continue
        score, reason = _impact_priority(row)
        key = (instance, node_id, depth, _pair_text(pair) or "")
        current = priority.get(key)
        if current is None or float(score) > float(current.get("branch_impact_priority", -1.0e30)):
            priority[key] = {
                "branch_impact_priority": float(score),
                "branch_impact_priority_reason": reason,
                "branch_impact_tail_class": row.get("tail_class"),
                "branch_impact_labels": row.get("branch_labels"),
                "branch_impact_right_censored": bool(row.get("right_censored")),
                "branch_impact_usable_for_training": bool(row.get("usable_for_branch_impact_training")),
            }
    return priority


def _load_excluded_entry_keys(paths: Iterable[Path]) -> set[tuple[str, int, int, int, int]]:
    excluded: set[tuple[str, int, int, int, int]] = set()
    for path in paths:
        payload = _read_json(path / "runbook.json" if path.is_dir() else path)
        entries = payload.get("entries")
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            pair = entry.get("forced_pair")
            if not isinstance(pair, list) or len(pair) != 2:
                continue
            try:
                i, j = int(pair[0]), int(pair[1])
                node_id = int(entry.get("source_node_id"))
                depth = int(entry.get("source_depth"))
            except (TypeError, ValueError):
                continue
            instance = str(entry.get("instance") or "")
            if not instance or i == j:
                continue
            a, b = sorted((i, j))
            excluded.add((instance, node_id, depth, a, b))
    return excluded


def _load_focus_context_keys(paths: Iterable[Path]) -> set[tuple[str, int, int, str]]:
    focus: set[tuple[str, int, int, str]] = set()
    for path in paths:
        if path.is_dir():
            rows = list(_iter_jsonl(path / "branch_counterfactual_delta_rows.jsonl"))
        elif path.name == "summary.json":
            rows = list(_iter_jsonl(path.parent / "branch_counterfactual_delta_rows.jsonl"))
        elif path.suffix == ".jsonl":
            rows = list(_iter_jsonl(path))
        else:
            rows = []
        for row in rows:
            labels = row.get("labels")
            labels = labels if isinstance(labels, dict) else {}
            if _float(labels.get("y_counterfactual_timeout_resolved"), default=0.0) <= 0.0:
                continue
            instance = str(row.get("instance") or "")
            baseline_pair = _pair_from_value(row.get("baseline_pair"))
            node_id = _int(row.get("node_id"), -1)
            depth = _int(row.get("depth"), -1)
            if not instance or baseline_pair is None or node_id < 0 or depth < 0:
                continue
            focus.add((instance, node_id, depth, _pair_text(baseline_pair) or ""))
    return focus


def _load_score_coverage_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_iter_jsonl(path / "branch_score_candidate_coverage_rows.jsonl"))
            continue
        if path.name == "summary.json":
            rows.extend(_iter_jsonl(path.parent / "branch_score_candidate_coverage_rows.jsonl"))
            payload = _read_json(path)
            raw_rows = payload.get("rows")
            if isinstance(raw_rows, list):
                rows.extend(row for row in raw_rows if isinstance(row, dict))
            continue
        if path.suffix == ".jsonl":
            rows.extend(_iter_jsonl(path))
            continue
        payload = _read_json(path)
        raw_rows = payload.get("rows")
        if isinstance(raw_rows, list):
            rows.extend(row for row in raw_rows if isinstance(row, dict))
    return rows


def _coverage_priority(row: dict[str, Any]) -> tuple[float, str, bool]:
    scored_count = _int(row.get("scored_candidate_count"), 0)
    eligible_scored_count = _int(row.get("eligible_scored_candidate_count"), 0)
    selected_unscored = bool(row.get("selected_is_unscored"))
    would_change = bool(row.get("would_change_selected"))
    would_change_any = bool(row.get("would_change_selected_any_logged"))
    full_logged = bool(row.get("full_logged_candidate_coverage"))
    required_tol = row.get("best_scored_required_tie_tolerance")
    gap = scored_count <= 0 or eligible_scored_count <= 0
    score = 0.0
    if scored_count <= 0:
        score += 100.0
    elif eligible_scored_count <= 0:
        score += 60.0
    if selected_unscored:
        score += 5.0
    if full_logged:
        score += 3.0
    if would_change:
        score += 2.0
    elif would_change_any:
        score += 1.0
    reason = (
        f"scored={scored_count};eligible_scored={eligible_scored_count};"
        f"selected_unscored={selected_unscored};full_logged={full_logged};"
        f"would_change={would_change};would_change_any={would_change_any};"
        f"required_tie_tolerance={required_tol}"
    )
    return score, reason, gap


def _coverage_priority_by_context(
    coverage_inputs: Iterable[Path],
    *,
    instance_root: Path,
) -> dict[tuple[str, int, int, str], dict[str, Any]]:
    priority: dict[tuple[str, int, int, str], dict[str, Any]] = {}
    for row in _load_score_coverage_rows(coverage_inputs):
        instance = _instance_from_log_path(Path(str(row.get("log_path") or "")), instance_root)
        selected_pair = _pair_from_value(row.get("selected_pair"))
        node_id = _int(row.get("node_id"), -1)
        depth = _int(row.get("depth"), -1)
        if instance is None or selected_pair is None or node_id < 0 or depth < 0:
            continue
        score, reason, is_gap = _coverage_priority(row)
        key = (instance, node_id, depth, _pair_text(selected_pair) or "")
        current = priority.get(key)
        if current is None or float(score) > float(current.get("coverage_gap_priority", -1.0e30)):
            priority[key] = {
                "coverage_gap_priority": float(score),
                "coverage_gap_priority_reason": reason,
                "coverage_gap_is_gap": bool(is_gap),
                "coverage_scored_candidate_count": _int(row.get("scored_candidate_count"), 0),
                "coverage_eligible_scored_candidate_count": _int(
                    row.get("eligible_scored_candidate_count"), 0
                ),
                "coverage_would_change_selected": bool(row.get("would_change_selected")),
                "coverage_would_change_selected_any_logged": bool(
                    row.get("would_change_selected_any_logged")
                ),
                "coverage_best_scored_pair": row.get("best_scored_pair"),
                "coverage_best_scored_required_tie_tolerance": row.get(
                    "best_scored_required_tie_tolerance"
                ),
            }
    return priority


def _instance_from_log_path(log_path: Path, instance_root: Path) -> str | None:
    text = str(log_path)
    marker = "BPC_future/logical_graph/"
    if marker in text:
        instance = marker + text.split(marker, 1)[1]
        if instance.endswith(".jsonl"):
            instance = instance[: -len(".jsonl")]
        return instance or None
    stem = log_path.name
    if stem.endswith(".jsonl"):
        stem = stem[: -len(".jsonl")]
    candidates = sorted(instance_root.rglob(stem))
    return str(candidates[0]) if candidates else None


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
        parsed = _parse_rf_constraint(record.get("constraint"))
        if parsed is None:
            continue
        try:
            child_id = int(record["child_node_id"])
            parent_id = int(record["parent_node_id"])
            child_depth = int(record.get("depth", 0))
        except (KeyError, TypeError, ValueError):
            continue
        parent_by_child[child_id] = {
            "child_node_id": child_id,
            "parent_node_id": parent_id,
            "parent_depth": child_depth - 1,
            "task_i": int(parsed["task_i"]),
            "task_j": int(parsed["task_j"]),
            "kind": str(parsed["kind"]),
        }
    path: list[dict[str, Any]] = []
    current = int(node_id)
    seen: set[int] = set()
    while current in parent_by_child and current not in seen:
        seen.add(current)
        edge = dict(parent_by_child[current])
        if int(edge["parent_node_id"]) in depth_by_node:
            edge["parent_depth"] = int(depth_by_node[int(edge["parent_node_id"])])
        path.append(edge)
        current = int(edge["parent_node_id"])
    path.reverse()
    return path


def _force_pair_path_rule(path_edges: list[dict[str, Any]], target_depth: int, pair: tuple[int, int]) -> str:
    pieces: list[str] = []
    for edge in path_edges:
        pieces.append(
            f"{int(edge['parent_depth'])}:{int(edge['task_i'])},{int(edge['task_j'])}={edge['kind']}"
        )
    pieces.append(f"{int(target_depth)}:{int(pair[0])},{int(pair[1])}")
    return "force_pair_path:" + ";".join(pieces)


def _logged_candidates(record: dict[str, Any], candidate_source: str) -> list[dict[str, Any]]:
    fields: tuple[str, ...]
    if candidate_source == "top":
        fields = ("top",)
    elif candidate_source == "both":
        fields = ("priority_top", "top")
    else:
        fields = ("priority_top",)
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for field in fields:
        raw = record.get(field)
        if not isinstance(raw, list):
            continue
        for candidate in raw:
            pair = _candidate_pair(candidate)
            if pair is None or pair in seen:
                continue
            seen.add(pair)
            candidates.append(candidate)
    return candidates


def _alternative_candidates(record: dict[str, Any], *, candidate_source: str) -> list[dict[str, Any]]:
    selected_pair = _candidate_pair(record.get("selected"))
    selected_payload = record.get("selected") if isinstance(record.get("selected"), dict) else {}
    selected_fractionality = _optional_float(selected_payload.get("fractionality"))
    logged_candidates = _logged_candidates(record, candidate_source)
    max_logged_fractionality = None
    if logged_candidates:
        max_logged_fractionality = max(_float(candidate.get("fractionality"), default=0.0) for candidate in logged_candidates)
    seen: set[tuple[int, int]] = set()
    if selected_pair is not None:
        seen.add(selected_pair)
    alternatives: list[dict[str, Any]] = []
    for rank, candidate in enumerate(logged_candidates):
        pair = _candidate_pair(candidate)
        if pair is None or pair in seen:
            continue
        seen.add(pair)
        alt_fractionality = _optional_float(candidate.get("fractionality"))
        gap_to_selected = (
            None
            if selected_fractionality is None or alt_fractionality is None
            else max(0.0, selected_fractionality - alt_fractionality)
        )
        required_tolerance = (
            None
            if max_logged_fractionality is None or alt_fractionality is None
            else max(0.0, float(max_logged_fractionality) - alt_fractionality)
        )
        alternatives.append(
            {
                "task_i": pair[0],
                "task_j": pair[1],
                "source_alt_rank": int(rank),
                "source_alt_fractionality": candidate.get("fractionality"),
                "source_selected_fractionality": selected_payload.get("fractionality"),
                "source_max_logged_fractionality": None
                if max_logged_fractionality is None
                else round(float(max_logged_fractionality), 9),
                "source_alt_fractionality_gap_to_selected": None
                if gap_to_selected is None
                else round(float(gap_to_selected), 9),
                "source_alt_required_tie_tolerance": None
                if required_tolerance is None
                else round(float(required_tolerance), 9),
                "source_alt_same_mass": candidate.get("same_mass"),
                "source_alt_support_count": candidate.get("support_count"),
                "source_alt_incumbent_relation": candidate.get("incumbent_relation"),
                "source_alt_incumbent_disagreement": candidate.get("incumbent_disagreement"),
                "source_alt_pool_same_allowed": candidate.get("pool_same_allowed"),
                "source_alt_pool_separate_allowed": candidate.get("pool_separate_allowed"),
                "source_alt_pool_max_child_width": candidate.get("pool_max_child_width"),
                "source_alt_pool_total_child_width": candidate.get("pool_total_child_width"),
                "source_alt_pool_balance_gap": candidate.get("pool_balance_gap"),
                "source_alt_branch_score": candidate.get("branch_score"),
                "source_alt_branch_score_source": candidate.get("branch_score_source"),
            }
        )
    alternatives.sort(
        key=lambda item: (
            _float(item.get("source_alt_pool_max_child_width")),
            _float(item.get("source_alt_pool_total_child_width")),
            _float(item.get("source_alt_pool_balance_gap")),
            -_float(item.get("source_alt_branch_score"), default=-1.0e30),
            int(item.get("source_alt_rank") or 0),
        )
    )
    return alternatives


def _command(
    *,
    config: Path,
    instance: str,
    time_limit: int,
    result_dir: Path,
    force_rule: str,
    candidate_log_top_n: int,
    probe_mode: str = "full_replay",
    probe_max_nodes: int | None = None,
    probe_max_cg_iterations: int | None = None,
) -> list[str]:
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
        f"journey_branch_candidate_priority={force_rule}",
        "--set",
        f"journey_branch_candidate_log_top_n={int(candidate_log_top_n)}",
    ]
    if probe_mode == "child_probe":
        if probe_max_nodes is not None:
            command.extend(["--set", f"max_nodes={int(probe_max_nodes)}"])
            command.extend(["--set", f"journey_max_nodes={int(probe_max_nodes)}"])
        if probe_max_cg_iterations is not None:
            command.extend(["--set", f"max_cg_iterations={int(probe_max_cg_iterations)}"])
            command.extend(["--set", f"journey_max_cg_iterations={int(probe_max_cg_iterations)}"])
        command.extend(["--set", "journey_tail_action_audit_enabled=True"])
        command.extend(["--set", "journey_corrected_node_bound_audit_enabled=True"])
        command.extend(["--set", "journey_corrected_node_bound_fathom_enabled=False"])
        command.extend(["--set", "journey_tail_action_early_branch_enabled=False"])
        command.extend(["--set", "journey_tail_action_no_column_early_branch_enabled=False"])
    return command


def build_runbook(
    log_paths: list[Path],
    output_dir: Path,
    report: Path,
    *,
    config: Path = DEFAULT_CONFIG,
    instance_root: Path = DEFAULT_INSTANCE_ROOT,
    time_limit: int = 600,
    limit: int = 60,
    alt_pairs_per_event: int = 3,
    candidate_source: str = "priority_top",
    candidate_log_top_n: int = 100,
    min_source_depth: int | None = None,
    max_source_depth: int | None = None,
    max_source_event_time: float | None = None,
    branch_impact_inputs: list[Path] | None = None,
    exclude_runbooks: list[Path] | None = None,
    focus_delta_inputs: list[Path] | None = None,
    coverage_inputs: list[Path] | None = None,
    coverage_gap_only: bool = False,
    probe_mode: str = "full_replay",
    probe_max_nodes: int | None = None,
    probe_extra_nodes_after_branch: int = 2,
    probe_max_cg_iterations: int | None = None,
) -> dict[str, Any]:
    if probe_mode not in {"full_replay", "child_probe"}:
        raise ValueError(f"unsupported probe_mode: {probe_mode}")
    if (
        min_source_depth is not None
        and max_source_depth is not None
        and int(min_source_depth) > int(max_source_depth)
    ):
        raise ValueError("min_source_depth must be <= max_source_depth")
    run_root = output_dir / "runs"
    entries: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int, int, int]] = set()
    excluded_entry_keys = _load_excluded_entry_keys(exclude_runbooks or [])
    excluded_entry_skip_count = 0
    focus_context_keys = _load_focus_context_keys(focus_delta_inputs or [])
    focus_event_skip_count = 0
    coverage_gap_skip_count = 0
    depth_filter_skip_count = 0
    source_event_time_filter_skip_count = 0
    event_count = 0
    event_with_entry_count = 0
    skipped_missing_instance = 0
    impact_priority = _impact_priority_by_context(
        branch_impact_inputs or [],
        instance_root=instance_root,
    )
    coverage_priority = _coverage_priority_by_context(
        coverage_inputs or [],
        instance_root=instance_root,
    )
    candidate_events: list[dict[str, Any]] = []
    for log_path in _iter_jsonl_paths(log_paths):
        events = list(_iter_jsonl(log_path))
        instance = _instance_from_log_path(log_path, instance_root)
        if instance is None:
            skipped_missing_instance += sum(1 for row in events if row.get("event") == "journey_branch_candidates")
            continue
        for record in events:
            if record.get("event") != "journey_branch_candidates":
                continue
            event_count += 1
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
            focus_key = (instance, node_id, depth, _pair_text(selected_pair) or "")
            if focus_context_keys and focus_key not in focus_context_keys:
                focus_event_skip_count += 1
                continue
            impact_key = (instance, node_id, depth, _pair_text(selected_pair) or "")
            impact = impact_priority.get(impact_key, {})
            coverage = coverage_priority.get(impact_key, {})
            if coverage_gap_only and not bool(coverage.get("coverage_gap_is_gap")):
                coverage_gap_skip_count += 1
                continue
            candidate_events.append(
                {
                    "log_path": log_path,
                    "events": events,
                    "instance": instance,
                    "record": record,
                    "source_event_time": source_event_time,
                    "input_order": len(candidate_events),
                    "branch_impact_priority": float(impact.get("branch_impact_priority", 0.0)),
                    "branch_impact_context": impact,
                    "coverage_gap_priority": float(coverage.get("coverage_gap_priority", 0.0)),
                    "coverage_context": coverage,
                }
            )
    candidate_events.sort(
        key=lambda item: (
            -float(item["coverage_gap_priority"]),
            -float(item["branch_impact_priority"]),
            int(item["input_order"]),
        )
    )
    for item in candidate_events:
            if len(entries) >= int(limit):
                continue
            log_path = item["log_path"]
            events = item["events"]
            instance = str(item["instance"])
            record = item["record"]
            node_id = _int(record.get("node_id"), -1)
            depth = _int(record.get("depth"), -1)
            if node_id < 0 or depth < 0:
                continue
            selected_pair = _candidate_pair(record.get("selected"))
            path_edges = _node_parent_path(events, node_id)
            impact_context = item.get("branch_impact_context")
            impact_context = impact_context if isinstance(impact_context, dict) else {}
            coverage_context = item.get("coverage_context")
            coverage_context = coverage_context if isinstance(coverage_context, dict) else {}
            event_added_entry = False
            accepted_for_event = 0
            for alt in _alternative_candidates(
                record,
                candidate_source=candidate_source,
            ):
                if accepted_for_event >= max(0, int(alt_pairs_per_event)):
                    break
                if len(entries) >= int(limit):
                    break
                alt_pair = (int(alt["task_i"]), int(alt["task_j"]))
                key = (instance, node_id, depth, alt_pair[0], alt_pair[1])
                if key in excluded_entry_keys:
                    excluded_entry_skip_count += 1
                    continue
                if key in seen:
                    continue
                seen.add(key)
                force_rule = _force_pair_path_rule(path_edges, depth, alt_pair)
                experiment = (
                    f"{len(entries) + 1:03d}_candidate_alt_d{depth}_n{node_id}_"
                    f"r{int(alt['source_alt_rank'])}_{alt_pair[0]}_{alt_pair[1]}_"
                    f"{_safe_slug(Path(instance).stem)}"
                )
                result_dir = run_root / experiment
                effective_probe_max_nodes = None
                effective_probe_max_cg_iterations = None
                if probe_mode == "child_probe":
                    if probe_max_nodes is None:
                        effective_probe_max_nodes = max(
                            1,
                            int(depth) + 1 + max(0, int(probe_extra_nodes_after_branch)),
                        )
                    else:
                        effective_probe_max_nodes = max(1, int(probe_max_nodes))
                    effective_probe_max_cg_iterations = (
                        None if probe_max_cg_iterations is None else max(1, int(probe_max_cg_iterations))
                    )
                command = _command(
                    config=config,
                    instance=instance,
                    time_limit=time_limit,
                    result_dir=result_dir,
                    force_rule=force_rule,
                    candidate_log_top_n=candidate_log_top_n,
                    probe_mode=probe_mode,
                    probe_max_nodes=effective_probe_max_nodes,
                    probe_max_cg_iterations=effective_probe_max_cg_iterations,
                )
                entries.append(
                    {
                        "experiment": experiment,
                        "instance": instance,
                        "source_type": "branch_candidate_log_alt_pair",
                        "source_log_file": str(log_path),
                        "source_node_id": node_id,
                        "source_depth": depth,
                        "source_priority_mode": record.get("priority_mode"),
                        "source_event_time": item.get("source_event_time"),
                        "source_candidate_count": record.get("candidate_count"),
                        "source_eligible_count": record.get("eligible_count"),
                        "source_logged_priority_count": len(record.get("priority_top") or []),
                        "source_logged_top_count": len(record.get("top") or []),
                        "source_selected_pair": None if selected_pair is None else list(selected_pair),
                        "source_selected": record.get("selected"),
                        "source_path_edges": path_edges,
                        "branch_impact_priority": item.get("branch_impact_priority"),
                        "branch_impact_priority_reason": impact_context.get("branch_impact_priority_reason"),
                        "branch_impact_tail_class": impact_context.get("branch_impact_tail_class"),
                        "branch_impact_labels": impact_context.get("branch_impact_labels"),
                        "branch_impact_right_censored": impact_context.get("branch_impact_right_censored"),
                        "branch_impact_usable_for_training": impact_context.get(
                            "branch_impact_usable_for_training"
                        ),
                        "coverage_gap_priority": item.get("coverage_gap_priority"),
                        "coverage_gap_priority_reason": coverage_context.get(
                            "coverage_gap_priority_reason"
                        ),
                        "coverage_gap_is_gap": coverage_context.get("coverage_gap_is_gap"),
                        "coverage_scored_candidate_count": coverage_context.get(
                            "coverage_scored_candidate_count"
                        ),
                        "coverage_eligible_scored_candidate_count": coverage_context.get(
                            "coverage_eligible_scored_candidate_count"
                        ),
                        "coverage_would_change_selected": coverage_context.get(
                            "coverage_would_change_selected"
                        ),
                        "coverage_would_change_selected_any_logged": coverage_context.get(
                            "coverage_would_change_selected_any_logged"
                        ),
                        "coverage_best_scored_pair": coverage_context.get("coverage_best_scored_pair"),
                        "coverage_best_scored_required_tie_tolerance": coverage_context.get(
                            "coverage_best_scored_required_tie_tolerance"
                        ),
                        "forced_pair": [alt_pair[0], alt_pair[1]],
                        "forced_pair_path_rule": force_rule,
                        "probe_mode": probe_mode,
                        "probe_max_nodes": effective_probe_max_nodes,
                        "probe_max_cg_iterations": effective_probe_max_cg_iterations,
                        "command": command,
                        "shell_command": shlex.join(command),
                        "expected_label_source": "fixed_budget_child_probe_then_audit_child_probe_rows"
                        if probe_mode == "child_probe"
                        else "rerun_then_audit_branch_impact_and_counterfactual_delta",
                        **alt,
                    }
                )
                accepted_for_event += 1
                if not event_added_entry:
                    event_with_entry_count += 1
                    event_added_entry = True
    runbook = {
        "schema_version": "journey_branch_candidate_replay_runbook_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "stage4_candidate_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "log_paths": [str(path) for path in log_paths],
        "config": str(config),
        "instance_root": str(instance_root),
        "time_limit": int(time_limit),
        "limit": int(limit),
        "alt_pairs_per_event": int(alt_pairs_per_event),
        "candidate_source": candidate_source,
        "candidate_log_top_n": int(candidate_log_top_n),
        "min_source_depth": None if min_source_depth is None else int(min_source_depth),
        "max_source_depth": None if max_source_depth is None else int(max_source_depth),
        "max_source_event_time": None
        if max_source_event_time is None
        else float(max_source_event_time),
        "branch_impact_input_paths": [str(path) for path in (branch_impact_inputs or [])],
        "exclude_runbook_paths": [str(path) for path in (exclude_runbooks or [])],
        "focus_delta_input_paths": [str(path) for path in (focus_delta_inputs or [])],
        "coverage_input_paths": [str(path) for path in (coverage_inputs or [])],
        "coverage_gap_only": bool(coverage_gap_only),
        "probe_mode": probe_mode,
        "probe_max_nodes": None if probe_max_nodes is None else int(probe_max_nodes),
        "probe_extra_nodes_after_branch": int(probe_extra_nodes_after_branch),
        "probe_max_cg_iterations": None
        if probe_max_cg_iterations is None
        else int(probe_max_cg_iterations),
        "excluded_entry_key_count": len(excluded_entry_keys),
        "excluded_entry_skip_count": int(excluded_entry_skip_count),
        "focus_context_count": len(focus_context_keys),
        "focus_event_skip_count": int(focus_event_skip_count),
        "coverage_priority_context_count": len(coverage_priority),
        "coverage_gap_skip_count": int(coverage_gap_skip_count),
        "depth_filter_skip_count": int(depth_filter_skip_count),
        "source_event_time_filter_skip_count": int(source_event_time_filter_skip_count),
        "branch_impact_priority_context_count": len(impact_priority),
        "candidate_event_count_seen": int(event_count),
        "candidate_event_count_with_replay_entries": int(event_with_entry_count),
        "skipped_missing_instance_event_count": int(skipped_missing_instance),
        "entry_limit_reached": bool(len(entries) >= int(limit)),
        "entry_count": len(entries),
        "entries": entries,
        "notes": (
            "Runbook entries force alternative legal Ryan-Foster candidates "
            "along the logged ancestor branch path. If a forced pair is not "
            "currently legal in replay, solver candidate selection falls back "
            "under existing exact-safe logic. Official bounds and certificates "
            "remain produced only by exact-safe pricing/proof code. In "
            "child_probe mode, commands intentionally use small node/CG budgets "
            "for censored proof-cost labels rather than full-solve performance "
            "claims."
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
        "\n".join(str(entry["shell_command"]) for entry in runbook.get("entries", [])) + "\n",
        encoding="utf-8",
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_render_report(runbook, output_dir), encoding="utf-8")


def _render_report(runbook: dict[str, Any], output_dir: Path) -> str:
    lines = [
        "# Journey Branch Candidate Replay Runbook",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## Purpose",
        "",
        "Generate forced-pair replay commands from logged `journey_branch_candidates` events. The runbook only creates commands; it does not run BPC / pricing / RMP and does not create certificates or official bounds.",
        "",
        "## Machine Fields",
        "",
        "```text",
        f"output_dir = {output_dir}",
        f"entry_count = {runbook.get('entry_count')}",
        f"candidate_event_count_seen = {runbook.get('candidate_event_count_seen')}",
        f"candidate_event_count_with_replay_entries = {runbook.get('candidate_event_count_with_replay_entries')}",
        f"skipped_missing_instance_event_count = {runbook.get('skipped_missing_instance_event_count')}",
        f"entry_limit_reached = {runbook.get('entry_limit_reached')}",
        f"alt_pairs_per_event = {runbook.get('alt_pairs_per_event')}",
        f"candidate_source = {runbook.get('candidate_source')}",
        f"candidate_log_top_n = {runbook.get('candidate_log_top_n')}",
        f"min_source_depth = {runbook.get('min_source_depth')}",
        f"max_source_depth = {runbook.get('max_source_depth')}",
        f"max_source_event_time = {runbook.get('max_source_event_time')}",
        f"branch_impact_input_paths = {runbook.get('branch_impact_input_paths')}",
        f"exclude_runbook_paths = {runbook.get('exclude_runbook_paths')}",
        f"focus_delta_input_paths = {runbook.get('focus_delta_input_paths')}",
        f"coverage_input_paths = {runbook.get('coverage_input_paths')}",
        f"coverage_gap_only = {runbook.get('coverage_gap_only')}",
        f"probe_mode = {runbook.get('probe_mode')}",
        f"probe_max_nodes = {runbook.get('probe_max_nodes')}",
        f"probe_extra_nodes_after_branch = {runbook.get('probe_extra_nodes_after_branch')}",
        f"probe_max_cg_iterations = {runbook.get('probe_max_cg_iterations')}",
        f"excluded_entry_key_count = {runbook.get('excluded_entry_key_count')}",
        f"excluded_entry_skip_count = {runbook.get('excluded_entry_skip_count')}",
        f"focus_context_count = {runbook.get('focus_context_count')}",
        f"focus_event_skip_count = {runbook.get('focus_event_skip_count')}",
        f"coverage_priority_context_count = {runbook.get('coverage_priority_context_count')}",
        f"coverage_gap_skip_count = {runbook.get('coverage_gap_skip_count')}",
        f"depth_filter_skip_count = {runbook.get('depth_filter_skip_count')}",
        f"source_event_time_filter_skip_count = {runbook.get('source_event_time_filter_skip_count')}",
        f"branch_impact_priority_context_count = {runbook.get('branch_impact_priority_context_count')}",
        "production_ready = false",
        "stage4_candidate_ready = false",
        "certificate_effect = false",
        "official_bound_effect = false",
        "```",
        "",
        "## Entries",
        "",
    ]
    for entry in runbook.get("entries", [])[:30]:
        lines.extend(
            [
                f"### {entry['experiment']}",
                "",
                "```text",
                f"instance = {entry['instance']}",
                f"source_node_id = {entry.get('source_node_id')}",
                f"source_depth = {entry.get('source_depth')}",
                f"source_event_time = {entry.get('source_event_time')}",
                f"source_selected_pair = {entry.get('source_selected_pair')}",
                f"forced_pair = {entry.get('forced_pair')}",
                f"forced_pair_path_rule = {entry.get('forced_pair_path_rule')}",
                f"probe_mode = {entry.get('probe_mode')}",
                f"probe_max_nodes = {entry.get('probe_max_nodes')}",
                f"probe_max_cg_iterations = {entry.get('probe_max_cg_iterations')}",
                f"source_alt_rank = {entry.get('source_alt_rank')}",
                f"source_selected_fractionality = {entry.get('source_selected_fractionality')}",
                f"source_alt_fractionality = {entry.get('source_alt_fractionality')}",
                f"source_alt_required_tie_tolerance = {entry.get('source_alt_required_tie_tolerance')}",
                f"source_alt_pool_max_child_width = {entry.get('source_alt_pool_max_child_width')}",
                f"source_alt_pool_total_child_width = {entry.get('source_alt_pool_total_child_width')}",
                f"source_alt_branch_score = {entry.get('source_alt_branch_score')}",
                f"coverage_gap_priority = {entry.get('coverage_gap_priority')}",
                f"coverage_gap_priority_reason = {entry.get('coverage_gap_priority_reason')}",
                f"coverage_best_scored_pair = {entry.get('coverage_best_scored_pair')}",
                f"coverage_best_scored_required_tie_tolerance = {entry.get('coverage_best_scored_required_tie_tolerance')}",
                f"branch_impact_priority = {entry.get('branch_impact_priority')}",
                f"branch_impact_priority_reason = {entry.get('branch_impact_priority_reason')}",
                "```",
                "",
                "```bash",
                str(entry["shell_command"]),
                "```",
                "",
            ]
        )
    if len(runbook.get("entries", [])) > 30:
        lines.append(f"- Report truncated to first 30 entries; full runbook has {runbook.get('entry_count')} entries.")
        lines.append("")
    lines.extend(
        [
            "## Boundary",
            "",
            "These commands only change branch candidate priority for counterfactual sampling. If replay cannot bind the forced pair, the solver falls back to existing exact-safe logic; final no-negative closure, node bounds, fathom, and certificates still come only from exact-safe pricing/proof.",
        ]
    )
    if runbook.get("probe_mode") == "child_probe":
        lines.extend(
            [
                "",
                "In `child_probe` mode these commands are fixed-budget diagnostic probes. They are intended to be audited with `audit_journey_branch_impact.py` and its `child_probe_rows.jsonl`, not interpreted as full-solve A/B outcomes.",
            ]
        )
    return "\n".join(lines) + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_path", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--instance-root", type=Path, default=DEFAULT_INSTANCE_ROOT)
    parser.add_argument("--time-limit", type=int, default=600)
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("--alt-pairs-per-event", type=int, default=3)
    parser.add_argument(
        "--candidate-source",
        choices=("priority_top", "top", "both"),
        default="priority_top",
    )
    parser.add_argument("--candidate-log-top-n", type=int, default=100)
    parser.add_argument("--min-source-depth", type=int, default=None)
    parser.add_argument("--max-source-depth", type=int, default=None)
    parser.add_argument(
        "--max-source-event-time",
        type=float,
        default=None,
        help="Skip branch-candidate events whose logged event time is greater than this value.",
    )
    parser.add_argument("--branch-impact-input", nargs="*", type=Path, default=[])
    parser.add_argument("--exclude-runbook", nargs="*", type=Path, default=[])
    parser.add_argument("--focus-delta-input", nargs="*", type=Path, default=[])
    parser.add_argument("--coverage-input", nargs="*", type=Path, default=[])
    parser.add_argument(
        "--coverage-gap-only",
        action="store_true",
        help="Keep only branch-candidate events marked as score coverage gaps by coverage input rows.",
    )
    parser.add_argument(
        "--probe-mode",
        choices=("full_replay", "child_probe"),
        default="full_replay",
        help="full_replay emits normal forced-pair runs; child_probe emits fixed-budget proof-cost probes.",
    )
    parser.add_argument(
        "--probe-max-nodes",
        type=int,
        default=None,
        help="Override max_nodes/journey_max_nodes for child_probe entries. Defaults to source_depth + 1 + probe_extra_nodes_after_branch.",
    )
    parser.add_argument(
        "--probe-extra-nodes-after-branch",
        type=int,
        default=2,
        help="Child-probe default node budget after reaching and branching the source node.",
    )
    parser.add_argument(
        "--probe-max-cg-iterations",
        type=int,
        default=None,
        help="Optional max_cg_iterations/journey_max_cg_iterations override for child_probe entries.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    runbook = build_runbook(
        list(args.log_path),
        args.output_dir,
        args.report,
        config=args.config,
        instance_root=args.instance_root,
        time_limit=args.time_limit,
        limit=args.limit,
        alt_pairs_per_event=args.alt_pairs_per_event,
        candidate_source=args.candidate_source,
        candidate_log_top_n=args.candidate_log_top_n,
        min_source_depth=args.min_source_depth,
        max_source_depth=args.max_source_depth,
        max_source_event_time=args.max_source_event_time,
        branch_impact_inputs=list(args.branch_impact_input),
        exclude_runbooks=list(args.exclude_runbook),
        focus_delta_inputs=list(args.focus_delta_input),
        coverage_inputs=list(args.coverage_input),
        coverage_gap_only=bool(args.coverage_gap_only),
        probe_mode=str(args.probe_mode),
        probe_max_nodes=args.probe_max_nodes,
        probe_extra_nodes_after_branch=args.probe_extra_nodes_after_branch,
        probe_max_cg_iterations=args.probe_max_cg_iterations,
    )
    print(json.dumps({key: value for key, value in runbook.items() if key != "entries"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
