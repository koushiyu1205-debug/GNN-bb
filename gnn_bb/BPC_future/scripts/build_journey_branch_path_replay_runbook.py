#!/usr/bin/env python3
"""Build path-level Journey branch replay commands from successful logs.

This diagnostic helper reads existing JSONL solver logs, reconstructs branch
ancestor paths and observed child processing order, then emits replay commands
that force the same Ryan-Foster pair on a matching ancestor path and prioritize
the observed child kind at each depth. It does not run BPC, pricing, or RMP.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shlex
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_path_replay_runbook_20260627")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260627_bpc_future_journey_branch_path_replay_runbook_zh.md"
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
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            yield record


def _safe_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")
    return slug[:160] or "instance"


def _parse_rf(text: Any) -> dict[str, Any] | None:
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


def _pair(parsed: dict[str, Any]) -> tuple[int, int]:
    return tuple(sorted((int(parsed["task_i"]), int(parsed["task_j"]))))


def _instance_from_log_path(log_path: Path, instance_root: Path) -> str | None:
    text = str(log_path)
    marker = f"{instance_root.as_posix().rstrip('/')}/"
    if marker in text:
        instance = marker + text.split(marker, 1)[1]
        if instance.endswith(".jsonl"):
            instance = instance[: -len(".jsonl")]
        return instance
    stem = log_path.name
    if stem.endswith(".json.jsonl"):
        return str(instance_root / (stem[: -len(".jsonl")]))
    return None


def _node_parent_path(events: list[dict[str, Any]], node_id: int) -> list[dict[str, Any]]:
    parent_by_child: dict[int, dict[str, Any]] = {}
    for record in events:
        if record.get("event") != "journey_child_queued":
            continue
        parsed = _parse_rf(record.get("constraint"))
        if parsed is None:
            continue
        try:
            child_id = int(record["child_node_id"])
            parent_id = int(record["parent_node_id"])
            child_depth = int(record["depth"])
        except (KeyError, TypeError, ValueError):
            continue
        parent_by_child[child_id] = {
            "parent_node_id": parent_id,
            "child_node_id": child_id,
            "parent_depth": child_depth - 1,
            "child_depth": child_depth,
            "task_i": _pair(parsed)[0],
            "task_j": _pair(parsed)[1],
            "kind": parsed["kind"],
            "constraint": record.get("constraint"),
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
    return path


def _first_started_child_kind(events: list[dict[str, Any]], parent_node_id: int) -> str | None:
    children: dict[int, str] = {}
    for record in events:
        if record.get("event") != "journey_child_queued":
            continue
        try:
            if int(record.get("parent_node_id")) != int(parent_node_id):
                continue
            child_id = int(record["child_node_id"])
        except (TypeError, ValueError, KeyError):
            continue
        parsed = _parse_rf(record.get("constraint"))
        if parsed is not None:
            children[child_id] = str(parsed["kind"])
    if not children:
        return None
    starts: list[tuple[float, int]] = []
    for record in events:
        if record.get("event") != "journey_node_start":
            continue
        try:
            node_id = int(record["node_id"])
        except (TypeError, ValueError, KeyError):
            continue
        if node_id not in children:
            continue
        try:
            time_value = float(record.get("time") or 0.0)
        except (TypeError, ValueError):
            time_value = 0.0
        starts.append((time_value, node_id))
    if starts:
        _time, child_id = min(starts)
        return children.get(child_id)
    first_child_id = next(iter(children))
    return children[first_child_id]


def _force_pair_path_rule(path_edges: list[dict[str, Any]], target_depth: int, pair: tuple[int, int]) -> str:
    pieces: list[str] = []
    for edge in path_edges:
        pieces.append(
            f"{int(edge['parent_depth'])}:{int(edge['task_i'])},{int(edge['task_j'])}={edge['kind']}"
        )
    pieces.append(f"{int(target_depth)}:{int(pair[0])},{int(pair[1])}")
    return "force_pair_path:" + ";".join(pieces)


def _force_child_kind_rule(
    path_edges: list[dict[str, Any]],
    *,
    target_depth: int,
    target_child_kind: str | None,
) -> str | None:
    pieces: list[str] = [
        f"{int(edge['parent_depth'])}:{edge['kind']}"
        for edge in path_edges
        if edge.get("kind") in {"same_vehicle", "separate_vehicle"}
    ]
    if target_child_kind in {"same_vehicle", "separate_vehicle"}:
        pieces.append(f"{int(target_depth)}:{target_child_kind}")
    if not pieces:
        return None
    return "force_child_kind_depth:" + ";".join(pieces)


def _command(
    *,
    config: Path,
    instance: str,
    time_limit: int,
    result_dir: Path,
    force_pair_path_rule: str,
    force_child_kind_rule: str | None,
    candidate_log_top_n: int,
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
        "--force-child-exit-after-run",
        "--set",
        f"journey_branch_candidate_priority={force_pair_path_rule}",
        "--set",
        f"journey_branch_candidate_log_top_n={int(candidate_log_top_n)}",
        "--set",
        "journey_child_priority_by_width_enabled=False",
        "--set",
        "journey_tail_action_audit_enabled=True",
        "--set",
        "journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True",
        "--set",
        "journey_early_branching_enabled=False",
        "--set",
        "journey_early_branching_after_incomplete_no_column_enabled=False",
        "--set",
        "journey_tail_action_early_branch_enabled=False",
        "--set",
        "journey_tail_action_no_column_early_branch_enabled=False",
        "--set",
        "journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
        "--set",
        "journey_gat_admission_scheduler_enabled=False",
    ]
    if force_child_kind_rule:
        command.extend(["--set", f"journey_child_priority_mode={force_child_kind_rule}"])
    return command


def build_runbook(
    log_paths: list[Path],
    output_dir: Path,
    report: Path,
    *,
    config: Path = DEFAULT_CONFIG,
    instance_root: Path = DEFAULT_INSTANCE_ROOT,
    time_limit: int = 600,
    limit: int = 20,
    min_depth: int = 0,
    max_depth: int = 4,
    max_source_event_time: float | None = None,
    candidate_log_top_n: int = 200,
    require_optimal_source: bool = True,
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    run_root = output_dir / "runs"
    source_log_count = 0
    skipped_nonoptimal = 0
    skipped_no_instance = 0
    skipped_no_pair = 0
    seen: set[tuple[str, str, str | None]] = set()

    for log_path in _iter_jsonl_paths(log_paths):
        source_log_count += 1
        events = list(_iter_jsonl(log_path))
        finish = next((record for record in reversed(events) if record.get("event") == "finish"), None)
        if require_optimal_source and (finish is None or finish.get("status") != "OPTIMAL"):
            skipped_nonoptimal += 1
            continue
        instance = _instance_from_log_path(log_path, instance_root)
        if instance is None:
            skipped_no_instance += 1
            continue
        for record in events:
            if record.get("event") != "journey_branch":
                continue
            try:
                node_id = int(record["node_id"])
                depth = int(record["depth"])
            except (TypeError, ValueError, KeyError):
                continue
            if depth < int(min_depth) or depth > int(max_depth):
                continue
            if max_source_event_time is not None:
                try:
                    if float(record.get("time") or 0.0) > float(max_source_event_time):
                        continue
                except (TypeError, ValueError):
                    continue
            parsed = _parse_rf(record.get("left")) or _parse_rf(record.get("right"))
            if parsed is None:
                skipped_no_pair += 1
                continue
            pair = _pair(parsed)
            path_edges = _node_parent_path(events, node_id)
            force_pair_rule = _force_pair_path_rule(path_edges, depth, pair)
            target_child_kind = _first_started_child_kind(events, node_id)
            child_kind_rule = _force_child_kind_rule(
                path_edges,
                target_depth=depth,
                target_child_kind=target_child_kind,
            )
            key = (instance, force_pair_rule, child_kind_rule)
            if key in seen:
                continue
            seen.add(key)
            experiment = (
                f"{len(entries) + 1:03d}_path_d{depth}_n{node_id}_"
                f"{pair[0]}_{pair[1]}_{_safe_slug(Path(instance).stem)}"
            )
            result_dir = run_root / experiment
            command = _command(
                config=config,
                instance=instance,
                time_limit=time_limit,
                result_dir=result_dir,
                force_pair_path_rule=force_pair_rule,
                force_child_kind_rule=child_kind_rule,
                candidate_log_top_n=candidate_log_top_n,
            )
            entries.append(
                {
                    "experiment": experiment,
                    "instance": instance,
                    "source_log_file": str(log_path),
                    "source_status": None if finish is None else finish.get("status"),
                    "source_solving_time": None if finish is None else finish.get("solving_time"),
                    "source_node_id": node_id,
                    "source_depth": depth,
                    "source_time": record.get("time"),
                    "source_pair": [pair[0], pair[1]],
                    "source_first_child_kind": target_child_kind,
                    "source_path_edges": path_edges,
                    "forced_pair_path_rule": force_pair_rule,
                    "forced_child_kind_depth_rule": child_kind_rule,
                    "command": command,
                    "shell_command": shlex.join(command),
                    "expected_label_source": "rerun_then_compare_wall_time_and_status",
                }
            )
            if len(entries) >= int(limit):
                break
        if len(entries) >= int(limit):
            break

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "runbook.json").write_text(
        json.dumps(
            {
                "schema_version": "journey_branch_path_replay_runbook_v1",
                "runs_bpc_or_pricing": False,
                "diagnostic_only": True,
                "official_bound_effect": False,
                "certificate_effect": False,
                "source_log_count": source_log_count,
                "entry_count": len(entries),
                "command_count": len(entries),
                "config": str(config),
                "time_limit": int(time_limit),
                "min_depth": int(min_depth),
                "max_depth": int(max_depth),
                "max_source_event_time": max_source_event_time,
                "candidate_log_top_n": int(candidate_log_top_n),
                "require_optimal_source": bool(require_optimal_source),
                "skipped_nonoptimal": skipped_nonoptimal,
                "skipped_no_instance": skipped_no_instance,
                "skipped_no_pair": skipped_no_pair,
                "entries": entries,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "commands.sh").write_text(
        "\n".join(entry["shell_command"] for entry in entries) + ("\n" if entries else ""),
        encoding="utf-8",
    )
    _write_report(report, output_dir / "runbook.json")
    return json.loads((output_dir / "runbook.json").read_text(encoding="utf-8"))


def _write_report(report: Path, runbook_path: Path) -> None:
    runbook = json.loads(runbook_path.read_text(encoding="utf-8"))
    lines = [
        "# Journey Branch Path Replay Runbook",
        "",
        "该 runbook 只从已有 JSONL 日志抽取分支路径，不运行 BPC / pricing / RMP；不产生 official bound 或 certificate。",
        "",
        "## Summary",
        "",
        f"- source_log_count: `{runbook['source_log_count']}`",
        f"- entry_count: `{runbook['entry_count']}`",
        f"- time_limit: `{runbook['time_limit']}`",
        f"- depth range: `{runbook['min_depth']}..{runbook['max_depth']}`",
        "",
        "## Entries",
        "",
    ]
    for entry in runbook.get("entries", [])[:20]:
        lines.extend(
            [
                f"### {entry['experiment']}",
                "",
                f"- instance: `{entry['instance']}`",
                f"- source depth/node: `{entry['source_depth']}` / `{entry['source_node_id']}`",
                f"- source pair: `{entry['source_pair']}`",
                f"- source first child kind: `{entry.get('source_first_child_kind')}`",
                f"- forced_pair_path_rule: `{entry['forced_pair_path_rule']}`",
                f"- forced_child_kind_depth_rule: `{entry.get('forced_child_kind_depth_rule')}`",
                "",
            ]
        )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_path", nargs="+", type=Path)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path)
    parser.add_argument("--report", default=DEFAULT_REPORT, type=Path)
    parser.add_argument("--config", default=DEFAULT_CONFIG, type=Path)
    parser.add_argument("--instance-root", default=DEFAULT_INSTANCE_ROOT, type=Path)
    parser.add_argument("--time-limit", default=600, type=int)
    parser.add_argument("--limit", default=20, type=int)
    parser.add_argument("--min-depth", default=0, type=int)
    parser.add_argument("--max-depth", default=4, type=int)
    parser.add_argument("--max-source-event-time", type=float)
    parser.add_argument("--candidate-log-top-n", default=200, type=int)
    parser.add_argument("--allow-nonoptimal-source", action="store_true")
    args = parser.parse_args()

    runbook = build_runbook(
        args.log_path,
        args.output_dir,
        args.report,
        config=args.config,
        instance_root=args.instance_root,
        time_limit=args.time_limit,
        limit=args.limit,
        min_depth=args.min_depth,
        max_depth=args.max_depth,
        max_source_event_time=args.max_source_event_time,
        candidate_log_top_n=args.candidate_log_top_n,
        require_optimal_source=not args.allow_nonoptimal_source,
    )
    print(json.dumps({k: v for k, v in runbook.items() if k != "entries"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
