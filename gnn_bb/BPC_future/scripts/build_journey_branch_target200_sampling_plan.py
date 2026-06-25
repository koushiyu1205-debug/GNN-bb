#!/usr/bin/env python3
"""Build a target-200-oriented Journey branch sampling plan.

The plan reads canonical 20-scale benchmark CSVs, known strict replay labels,
and optional solver JSONL logs. It emits the next diagnostic commands that are
most likely to add target-200 positives or hard negatives for branch/action GAT
training. It does not run BPC, pricing, RMP, or produce official
bounds/certificates.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
import shlex
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_target200_sampling_plan_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_journey_branch_target200_sampling_plan_zh.md"
)
DEFAULT_CONFIG = Path("BPC_future/configs/moon_trek_20_smoke.yaml")
DEFAULT_INSTANCE_ROOT = Path("BPC_future/logical_graph")


def _float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return int(default)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _safe_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")
    return slug[:180] or "context"


def _shell_join(items: Iterable[Any]) -> str:
    return " ".join(shlex.quote(str(item)) for item in items)


def _time_window_family(instance: str) -> str:
    for token in ("greedy-anchor", "random-wave", "sector-wave"):
        if token in instance:
            return token
    return ""


def _terrain(instance: str) -> str:
    parts = Path(instance).parts
    for index, part in enumerate(parts):
        if part in {"greedy-anchor", "random-wave", "sector-wave"} and index + 1 < len(parts):
            return parts[index + 1]
    return ""


def _seed(instance: str) -> str:
    match = re.search(r"_seed(\d+)_", instance)
    return match.group(1) if match else ""


def _read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
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


def _iter_jsonl_paths(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.suffix == ".jsonl":
            yield path
        elif path.is_dir():
            yield from sorted(path.rglob("*.jsonl"))


def _load_results(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                instance = str(row.get("instance") or "")
                if instance:
                    rows.append(dict(row))
    return rows


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
    matches = sorted(instance_root.rglob(stem))
    return str(matches[0]) if matches else None


def _load_log_index(paths: Iterable[Path], *, instance_root: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for log_path in _iter_jsonl_paths(paths):
        fallback_instance = _instance_from_log_path(log_path, instance_root)
        by_instance: dict[str, dict[str, int]] = {}
        for record in _read_jsonl(log_path):
            instance = str(record.get("instance") or fallback_instance or "")
            if not instance:
                continue
            payload = by_instance.setdefault(
                instance,
                {
                    "branch_candidate_event_count": 0,
                    "root_branch_candidate_event_count": 0,
                    "branch_event_count": 0,
                    "max_logged_candidate_count": 0,
                    "max_candidate_count": 0,
                },
            )
            if record.get("event") == "journey_branch":
                payload["branch_event_count"] += 1
            if record.get("event") != "journey_branch_candidates":
                continue
            payload["branch_candidate_event_count"] += 1
            if _int(record.get("depth"), -1) == 0:
                payload["root_branch_candidate_event_count"] += 1
            payload["max_logged_candidate_count"] = max(
                payload["max_logged_candidate_count"],
                _int(record.get("logged_top_count"), 0),
                len(record.get("priority_top") or []),
                len(record.get("top") or []),
            )
            payload["max_candidate_count"] = max(
                payload["max_candidate_count"],
                _int(record.get("candidate_count"), 0),
            )
        for instance, payload in by_instance.items():
            candidate = dict(payload)
            candidate["log_path"] = str(log_path)
            current = index.get(instance)
            if current is None or int(candidate["branch_candidate_event_count"]) > int(
                current.get("branch_candidate_event_count", 0)
            ):
                index[instance] = candidate
    return index


def _candidate_row_files(path: Path) -> list[Path]:
    if path.is_dir():
        candidates = [
            path / "branch_training_readiness_rows.jsonl",
            path / "branch_counterfactual_delta_rows.jsonl",
        ]
        return [candidate for candidate in candidates if candidate.exists()]
    if path.name == "summary.json":
        return _candidate_row_files(path.parent)
    return [path] if path.exists() else []


def _attempted_instance_files(path: Path) -> list[Path]:
    if path.is_dir():
        candidates = [
            path / "branch_counterfactual_delta_rows.jsonl",
            path / "branch_impact_rows.jsonl",
            path / "branch_training_rows.jsonl",
            path / "child_probe_rows.jsonl",
            path / "target200_sampling_selected_rows.jsonl",
            path / "holdout_sampling_rows.jsonl",
        ]
        return [candidate for candidate in candidates if candidate.exists()]
    if path.name == "summary.json":
        return _attempted_instance_files(path.parent)
    return [path] if path.exists() else []


def _runbook_json_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    if path.is_file():
        return [path] if path.name == "runbook.json" else []
    direct = path / "runbook.json"
    files: list[Path] = []
    if direct.exists():
        files.append(direct)
    files.extend(
        candidate
        for candidate in sorted(path.rglob("runbook.json"))
        if candidate != direct
    )
    return files


def _instance_from_text(text: str) -> str:
    marker = "BPC_future/logical_graph/"
    if marker not in text:
        return ""
    instance = marker + text.split(marker, 1)[1]
    if instance.endswith(".jsonl"):
        instance = instance[: -len(".jsonl")]
    return instance


def _attempted_instances(paths: Iterable[Path]) -> set[str]:
    return set(_attempted_instance_counts(paths).keys())


def _attempted_instance_counts(paths: Iterable[Path]) -> Counter[str]:
    counts: Counter[str] = Counter()
    instances: set[str] = set()
    for path in paths:
        for runbook_path in _runbook_json_files(path):
            runbook_payload = _read_json(runbook_path)
            entries = runbook_payload.get("entries")
            if isinstance(entries, list):
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    instance = str(entry.get("instance") or "")
                    if instance:
                        counts[instance] += 1
                        instances.add(instance)
        for row_file in _attempted_instance_files(path):
            if row_file.suffix == ".csv":
                for row in _load_results([row_file]):
                    instance = str(row.get("instance") or "")
                    if instance:
                        counts[instance] += 1
                        instances.add(instance)
                continue
            for row in _read_jsonl(row_file):
                instance = str(row.get("instance") or row.get("baseline_instance") or "")
                if not instance:
                    instance = _instance_from_text(str(row.get("log_file") or ""))
                if instance:
                    counts[instance] += 1
                    instances.add(instance)
    for instance in instances:
        counts.setdefault(instance, 0)
    return counts


def _known_target200_contexts(paths: Iterable[Path], *, target_wall: float) -> tuple[set[str], set[str], set[str]]:
    instances: set[str] = set()
    families: set[str] = set()
    terrains: set[str] = set()
    for path in paths:
        for row_file in _candidate_row_files(path):
            for row in _read_jsonl(row_file):
                instance = str(row.get("instance") or "")
                if not instance:
                    continue
                is_target = bool(row.get("target_200_positive"))
                if not is_target:
                    is_target = bool(
                        str(row.get("alternative_status") or "") == "OPTIMAL"
                        and _float(row.get("alternative_wall_time")) <= float(target_wall)
                        and _float(row.get("baseline_wall_time")) > float(target_wall)
                    )
                if not is_target:
                    continue
                instances.add(instance)
                family = _time_window_family(instance)
                terrain = _terrain(instance)
                if family:
                    families.add(family)
                if terrain:
                    terrains.add(terrain)
    return instances, families, terrains


def _diag_command(
    *,
    python: str,
    config: Path,
    instance: str,
    output_dir: Path,
    time_limit: int,
    candidate_log_top_n: int,
    max_workers: int,
) -> str:
    slug = _safe_slug(Path(instance).stem)
    result_dir = output_dir / "diag_runs" / slug
    return _shell_join(
        [
            python,
            "BPC_future/scripts/run_bpc_future_external_timeout_batch.py",
            "--config",
            config,
            "--instances",
            instance,
            "--time-limit",
            int(time_limit),
            "--results-csv",
            result_dir / "results.csv",
            "--log-dir",
            result_dir / "logs",
            "--solution-dir",
            result_dir / "solutions",
            "--run-log-dir",
            result_dir / "run_logs",
            "--python",
            python,
            "--timeout-kill-after",
            "30s",
            "--max-workers",
            int(max_workers),
            "--quiet",
            "--set",
            "journey_tail_action_audit_enabled=True",
            "--set",
            f"journey_branch_candidate_log_top_n={int(candidate_log_top_n)}",
            "--set",
            "journey_tail_action_early_branch_enabled=False",
            "--set",
            "journey_tail_action_no_column_early_branch_enabled=False",
        ]
    )


def _child_probe_command(
    *,
    python: str,
    config: Path,
    log_path: str,
    output_dir: Path,
    time_limit: int,
    candidate_log_top_n: int,
    alt_pairs_per_event: int,
    limit: int,
    max_source_depth: int,
    probe_max_cg_iterations: int,
    exclude_runbooks: list[Path] | None = None,
) -> str:
    command = [
        python,
        "BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py",
        log_path,
        "--config",
        config,
        "--time-limit",
        int(time_limit),
        "--candidate-selection",
        "layered",
        "--candidate-source",
        "both",
        "--alt-pairs-per-event",
        int(alt_pairs_per_event),
        "--candidate-log-top-n",
        int(candidate_log_top_n),
        "--max-source-depth",
        int(max_source_depth),
        "--probe-mode",
        "child_probe",
        "--probe-max-cg-iterations",
        int(probe_max_cg_iterations),
        "--limit",
        int(limit),
        "--output-dir",
        output_dir,
        "--report",
        output_dir / "report.md",
    ]
    if exclude_runbooks:
        command.append("--exclude-runbook")
        command.extend(str(path) for path in exclude_runbooks)
    return _shell_join(command)


def _action_for_context(
    *,
    result: dict[str, Any],
    log_payload: dict[str, Any] | None,
    known_target_instance: bool,
    attempted_instance: bool,
    family_gap: bool,
    target_wall: float,
    near_wall: float,
) -> tuple[str, str]:
    wall = _float(result.get("wall_time") or result.get("solving_time"))
    status = str(result.get("status") or "")
    has_candidates = bool(log_payload and int(log_payload.get("branch_candidate_event_count", 0)) > 0)
    has_branch_events = bool(log_payload and int(log_payload.get("branch_event_count", 0)) > 0)
    node_count = _int(result.get("node_count"), 0)
    if known_target_instance:
        return "SKIP_KNOWN_TARGET200_INSTANCE", "instance_already_has_target_200_positive"
    if attempted_instance:
        return "SKIP_ALREADY_ATTEMPTED_CONTEXT", "already_attempted_without_target200_positive"
    if wall <= float(target_wall):
        return "SKIP_ALREADY_WITHIN_TARGET", "wall_already_within_target"
    if has_candidates:
        return "BUILD_CHILD_PROBE_RUNBOOK", "candidate_log_available"
    if log_payload is not None and has_branch_events and not has_candidates:
        return "COLLECT_BRANCH_CANDIDATE_DIAG_LOG", "branch_events_without_candidate_log"
    if log_payload is not None and not has_candidates and not has_branch_events:
        if node_count <= 1:
            return "ROUTE_TO_ROOT_PRICING_TAIL", "top200_log_has_no_branch_events_root_tail"
        return "ROUTE_TO_PRICING_TAIL", "top200_log_has_no_branch_events"
    if status == "OPTIMAL" and wall <= float(near_wall):
        return "COLLECT_TOP200_DIAG_LOG", "near_target_optimal_missing_candidate_log"
    if status in {"TIME_LIMIT", "EXTERNAL_TIME_LIMIT"} and wall <= float(near_wall):
        return "COLLECT_TOP200_DIAG_LOG", "near_target_nonoptimal_missing_candidate_log"
    if family_gap:
        return "COLLECT_FAMILY_GAP_TOP200_DIAG_LOG", "missing_target_200_family"
    if status == "OPTIMAL":
        return "COLLECT_LONG_TOP200_DIAG_LOG", "slow_optimal_missing_candidate_log"
    return "DEFER_HARD_TIMEOUT_CONTEXT", "hard_timeout_low_target200_yield"


def _priority_score(
    *,
    result: dict[str, Any],
    action: str,
    family_gap: bool,
    terrain_gap: bool,
    target_wall: float,
    near_wall: float,
) -> float:
    wall = _float(result.get("wall_time") or result.get("solving_time"))
    status = str(result.get("status") or "")
    node_count = _int(result.get("node_count"), 0)
    instance = str(result.get("instance") or "")
    score = 0.0
    if action == "BUILD_CHILD_PROBE_RUNBOOK":
        score += 110.0
    elif action == "COLLECT_BRANCH_CANDIDATE_DIAG_LOG":
        score += 82.0
    elif action == "COLLECT_TOP200_DIAG_LOG":
        score += 90.0
    elif action == "COLLECT_FAMILY_GAP_TOP200_DIAG_LOG":
        score += 70.0
    elif action == "COLLECT_LONG_TOP200_DIAG_LOG":
        score += 55.0
    else:
        score -= 100.0
    if family_gap:
        score += 45.0
    if terrain_gap:
        score += 8.0
    if _time_window_family(instance) == "random-wave":
        score += 20.0
    if status == "OPTIMAL":
        score += 20.0
    elif status == "TIME_LIMIT":
        score += 10.0
    if wall > float(target_wall):
        score += max(0.0, 50.0 - abs(wall - float(target_wall)) / 4.0)
    if wall <= float(near_wall):
        score += 15.0
    if node_count > 1:
        score += min(20.0, float(node_count))
    return round(score, 6)


def build_target200_sampling_plan(
    *,
    results_csv: list[Path],
    output_dir: Path,
    report: Path,
    known_label_inputs: list[Path] | None = None,
    attempted_inputs: list[Path] | None = None,
    log_paths: list[Path] | None = None,
    config: Path = DEFAULT_CONFIG,
    instance_root: Path = DEFAULT_INSTANCE_ROOT,
    target_wall: float = 200.0,
    near_wall: float = 360.0,
    diagnostic_time_limit: int = 260,
    family_gap_time_limit: int = 600,
    child_probe_time_limit: int = 120,
    candidate_log_top_n: int = 200,
    alt_pairs_per_event: int = 4,
    child_probe_limit: int = 16,
    max_source_depth: int = 0,
    probe_max_cg_iterations: int = 20,
    max_attempted_probe_entries_per_instance: int = 0,
    selected_limit: int = 12,
    python: str = "/home/kai/miniconda3/bin/python",
    max_workers: int = 1,
) -> dict[str, Any]:
    results = _load_results(results_csv)
    known_instances, known_families, known_terrains = _known_target200_contexts(
        known_label_inputs or [],
        target_wall=target_wall,
    )
    attempted_counts = _attempted_instance_counts(attempted_inputs or [])
    attempted = set(attempted_counts.keys()) - known_instances
    log_index = _load_log_index(log_paths or [], instance_root=instance_root)
    all_rows: list[dict[str, Any]] = []
    for result in results:
        instance = str(result.get("instance") or "")
        if "tasks_020" not in instance:
            continue
        family = _time_window_family(instance)
        terrain = _terrain(instance)
        family_gap = bool(family and family not in known_families)
        terrain_gap = bool(terrain and terrain not in known_terrains)
        known_instance = instance in known_instances
        attempted_entry_count = int(attempted_counts.get(instance, 0))
        if int(max_attempted_probe_entries_per_instance) > 0:
            attempted_instance = bool(
                instance in attempted
                and attempted_entry_count >= int(max_attempted_probe_entries_per_instance)
            )
        else:
            attempted_instance = instance in attempted
        log_payload = log_index.get(instance)
        action, reason = _action_for_context(
            result=result,
            log_payload=log_payload,
            known_target_instance=known_instance,
            attempted_instance=attempted_instance,
            family_gap=family_gap,
            target_wall=target_wall,
            near_wall=near_wall,
        )
        priority = _priority_score(
            result=result,
            action=action,
            family_gap=family_gap,
            terrain_gap=terrain_gap,
            target_wall=target_wall,
            near_wall=near_wall,
        )
        command = ""
        if action == "BUILD_CHILD_PROBE_RUNBOOK" and log_payload is not None:
            command = _child_probe_command(
                python=python,
                config=config,
                log_path=str(log_payload.get("log_path") or ""),
                output_dir=output_dir / "child_probe_runbooks" / _safe_slug(Path(instance).stem),
                time_limit=child_probe_time_limit,
                candidate_log_top_n=candidate_log_top_n,
                alt_pairs_per_event=alt_pairs_per_event,
                limit=child_probe_limit,
                max_source_depth=max_source_depth,
                probe_max_cg_iterations=probe_max_cg_iterations,
                exclude_runbooks=attempted_inputs or [],
            )
        elif action in {
            "COLLECT_BRANCH_CANDIDATE_DIAG_LOG",
            "COLLECT_TOP200_DIAG_LOG",
            "COLLECT_FAMILY_GAP_TOP200_DIAG_LOG",
            "COLLECT_LONG_TOP200_DIAG_LOG",
        }:
            time_limit = diagnostic_time_limit
            if action in {"COLLECT_FAMILY_GAP_TOP200_DIAG_LOG", "COLLECT_LONG_TOP200_DIAG_LOG"}:
                time_limit = family_gap_time_limit
            command = _diag_command(
                python=python,
                config=config,
                instance=instance,
                output_dir=output_dir,
                time_limit=time_limit,
                candidate_log_top_n=candidate_log_top_n,
                max_workers=max_workers,
            )
        all_rows.append(
            {
                "schema_version": "journey_branch_target200_sampling_row_v1",
                "diagnostic_only": True,
                "runs_bpc_or_pricing": False,
                "official_bound_effect": False,
                "certificate_effect": False,
                "instance": instance,
                "status": result.get("status"),
                "wall_time": _float(result.get("wall_time") or result.get("solving_time")),
                "node_count": _int(result.get("node_count"), 0),
                "pricing_calls": _int(result.get("pricing_calls"), 0),
                "exact_pricing_calls": _int(result.get("exact_pricing_calls"), 0),
                "time_window_family": family,
                "terrain": terrain,
                "seed": _seed(instance),
                "family_gap": family_gap,
                "terrain_gap": terrain_gap,
                "known_target200_instance": known_instance,
                "attempted_context": attempted_instance,
                "attempted_probe_entry_count": attempted_entry_count,
                "max_attempted_probe_entries_per_instance": int(
                    max_attempted_probe_entries_per_instance
                ),
                "branch_candidate_event_count": 0
                if log_payload is None
                else int(log_payload.get("branch_candidate_event_count", 0)),
                "root_branch_candidate_event_count": 0
                if log_payload is None
                else int(log_payload.get("root_branch_candidate_event_count", 0)),
                "branch_event_count": 0
                if log_payload is None
                else int(log_payload.get("branch_event_count", 0)),
                "max_logged_candidate_count": 0
                if log_payload is None
                else int(log_payload.get("max_logged_candidate_count", 0)),
                "recommended_action": action,
                "recommended_reason": reason,
                "priority_score": priority,
                "recommended_command": command,
            }
        )
    actionable = [
        row
        for row in all_rows
        if str(row.get("recommended_action") or "").startswith(("COLLECT", "BUILD"))
    ]
    actionable.sort(key=lambda row: (-float(row["priority_score"]), float(row["wall_time"]), row["instance"]))
    selected = actionable[: max(0, int(selected_limit))]
    action_counts = Counter(str(row["recommended_action"]) for row in selected)
    family_counts = Counter(str(row["time_window_family"]) for row in selected)
    all_action_counts = Counter(str(row["recommended_action"]) for row in all_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "target200_sampling_all_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in all_rows),
        encoding="utf-8",
    )
    (output_dir / "target200_sampling_selected_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in selected),
        encoding="utf-8",
    )
    commands = ["#!/usr/bin/env bash", "set -euo pipefail", ""]
    for index, row in enumerate(selected, start=1):
        command = str(row.get("recommended_command") or "")
        if not command:
            continue
        commands.append(
            f"# {index:03d} {row['recommended_action']} {row['time_window_family']} "
            f"wall={row['wall_time']} seed={row['seed']}"
        )
        commands.append(command)
        commands.append("")
    (output_dir / "commands.sh").write_text("\n".join(commands), encoding="utf-8")
    summary = {
        "schema_version": "journey_branch_target200_sampling_plan_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "production_ready": False,
        "results_csv": [str(path) for path in results_csv],
        "known_label_inputs": [str(path) for path in (known_label_inputs or [])],
        "attempted_inputs": [str(path) for path in (attempted_inputs or [])],
        "log_paths": [str(path) for path in (log_paths or [])],
        "output_dir": str(output_dir),
        "target_wall": float(target_wall),
        "near_wall": float(near_wall),
        "candidate_log_top_n": int(candidate_log_top_n),
        "known_target200_instance_count": len(known_instances),
        "known_target200_family_count": len(known_families),
        "known_target200_families": sorted(known_families),
        "known_target200_terrain_count": len(known_terrains),
        "attempted_context_count": len(attempted),
        "max_attempted_probe_entries_per_instance": int(max_attempted_probe_entries_per_instance),
        "raw_result_count": len(results),
        "all_context_count": len(all_rows),
        "actionable_context_count": len(actionable),
        "selected_context_count": len(selected),
        "all_action_counts": dict(sorted(all_action_counts.items())),
        "selected_action_counts": dict(sorted(action_counts.items())),
        "selected_family_counts": dict(sorted(family_counts.items())),
        "commands_path": str(output_dir / "commands.sh"),
        "all_rows_path": str(output_dir / "target200_sampling_all_rows.jsonl"),
        "selected_rows_path": str(output_dir / "target200_sampling_selected_rows.jsonl"),
        "rows": selected,
    }
    (output_dir / "summary.json").write_text(
        json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(report: Path, summary: dict[str, Any]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Branch Target-200 Sampling Plan",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "按 V244 readiness 缺口为 branch/action GAT 选择下一批 target-200 正例采样 context。该计划只生成命令，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
    ]
    for key in [
        "raw_result_count",
        "all_context_count",
        "actionable_context_count",
        "selected_context_count",
        "target_wall",
        "near_wall",
        "known_target200_instance_count",
        "known_target200_family_count",
        "known_target200_families",
        "known_target200_terrain_count",
        "attempted_context_count",
        "max_attempted_probe_entries_per_instance",
        "all_action_counts",
        "selected_action_counts",
        "selected_family_counts",
        "commands_path",
        "runs_bpc_or_pricing",
        "official_bound_effect",
        "certificate_effect",
    ]:
        lines.append(f"{key} = {summary.get(key)}")
    lines.extend(["```", "", "## 推荐 context", ""])
    for row in summary["rows"]:
        lines.append(
            "- "
            f"action={row['recommended_action']}, reason={row['recommended_reason']}, "
            f"priority={row['priority_score']}, family={row['time_window_family']}, "
            f"terrain={row['terrain']}, seed={row['seed']}, status={row['status']}, "
            f"wall={row['wall_time']}, nodes={row['node_count']}, "
            f"candidate_events={row['branch_candidate_event_count']}, "
            f"branch_events={row['branch_event_count']}, "
            f"instance={Path(row['instance']).name}"
        )
    lines.extend(["", "## 边界", ""])
    lines.append(
        "推荐 context 只是采样入口；只有后续 child-probe / full replay / counterfactual delta 闭环后，才能产生 target-200 positive 或 hard negative 训练标签。"
    )
    lines.append(
        "`ROUTE_TO_ROOT_PRICING_TAIL` / `ROUTE_TO_PRICING_TAIL` 表示已有 top200 日志没有 branch event，"
        "该实例不应继续占用 branch-pair 采样预算。"
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-csv", action="append", required=True)
    parser.add_argument("--known-label-input", action="append", default=[])
    parser.add_argument("--attempted-input", action="append", default=[])
    parser.add_argument("--log", action="append", default=[])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--instance-root", type=Path, default=DEFAULT_INSTANCE_ROOT)
    parser.add_argument("--target-wall", type=float, default=200.0)
    parser.add_argument("--near-wall", type=float, default=360.0)
    parser.add_argument("--diagnostic-time-limit", type=int, default=260)
    parser.add_argument("--family-gap-time-limit", type=int, default=600)
    parser.add_argument("--child-probe-time-limit", type=int, default=120)
    parser.add_argument("--candidate-log-top-n", type=int, default=200)
    parser.add_argument("--alt-pairs-per-event", type=int, default=4)
    parser.add_argument("--child-probe-limit", type=int, default=16)
    parser.add_argument("--max-source-depth", type=int, default=0)
    parser.add_argument("--probe-max-cg-iterations", type=int, default=20)
    parser.add_argument(
        "--max-attempted-probe-entries-per-instance",
        type=int,
        default=0,
        help=(
            "Default 0 preserves the old behavior: any attempted instance is skipped. "
            "When >0, keep sampling an attempted instance until its counted probe/replay "
            "entries reach this per-instance budget; attempted runbooks are still passed "
            "down as exclude-runbook inputs to avoid repeating the same pair."
        ),
    )
    parser.add_argument("--selected-limit", type=int, default=12)
    parser.add_argument("--python", default="/home/kai/miniconda3/bin/python")
    parser.add_argument("--max-workers", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = build_target200_sampling_plan(
        results_csv=[Path(path) for path in args.results_csv],
        output_dir=args.output_dir,
        report=args.report,
        known_label_inputs=[Path(path) for path in args.known_label_input],
        attempted_inputs=[Path(path) for path in args.attempted_input],
        log_paths=[Path(path) for path in args.log],
        config=args.config,
        instance_root=args.instance_root,
        target_wall=args.target_wall,
        near_wall=args.near_wall,
        diagnostic_time_limit=args.diagnostic_time_limit,
        family_gap_time_limit=args.family_gap_time_limit,
        child_probe_time_limit=args.child_probe_time_limit,
        candidate_log_top_n=args.candidate_log_top_n,
        alt_pairs_per_event=args.alt_pairs_per_event,
        child_probe_limit=args.child_probe_limit,
        max_source_depth=args.max_source_depth,
        probe_max_cg_iterations=args.probe_max_cg_iterations,
        max_attempted_probe_entries_per_instance=args.max_attempted_probe_entries_per_instance,
        selected_limit=args.selected_limit,
        python=args.python,
        max_workers=args.max_workers,
    )
    printable = {key: value for key, value in summary.items() if key != "rows"}
    print(json.dumps(printable, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
