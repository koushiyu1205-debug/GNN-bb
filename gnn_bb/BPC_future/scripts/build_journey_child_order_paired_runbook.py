#!/usr/bin/env python3
"""Build paired same-first/separate-first Journey child-order replay commands.

This diagnostic helper reads existing Journey JSONL logs, reconstructs the
branch path to selected Ryan-Foster branch nodes, and emits paired replay
commands for the same parent/pair with opposite child ordering.  It does not
run BPC, pricing, RMP, or produce official bounds/certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import shlex
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_child_order_paired_runbook_20260628")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260628_bpc_future_journey_child_order_paired_runbook_zh.md"
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
    i = int(match.group("i"))
    j = int(match.group("j"))
    return {"task_i": min(i, j), "task_j": max(i, j), "kind": str(match.group("kind"))}


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


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _children_by_parent(events: list[dict[str, Any]]) -> dict[int, list[int]]:
    children: dict[int, list[int]] = defaultdict(list)
    for record in events:
        if record.get("event") != "journey_child_queued":
            continue
        try:
            parent_id = int(record["parent_node_id"])
            child_id = int(record["child_node_id"])
        except (KeyError, TypeError, ValueError):
            continue
        children[parent_id].append(child_id)
    return children


def _descendants(children: dict[int, list[int]], node_id: int) -> set[int]:
    out: set[int] = set()
    stack = list(children.get(int(node_id), []))
    while stack:
        child = int(stack.pop())
        if child in out:
            continue
        out.add(child)
        stack.extend(children.get(child, []))
    return out


def _node_parent_path(events: list[dict[str, Any]], node_id: int) -> list[dict[str, Any]]:
    parent_by_child: dict[int, dict[str, Any]] = {}
    depth_by_node: dict[int, int] = {}
    for record in events:
        if record.get("event") == "journey_node_start" and record.get("node_id") is not None:
            depth_by_node[int(record["node_id"])] = _int(record.get("depth"), 0)
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
            "task_i": int(parsed["task_i"]),
            "task_j": int(parsed["task_j"]),
            "kind": str(parsed["kind"]),
            "constraint": record.get("constraint"),
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


def _force_child_kind_depth_rule(
    path_edges: list[dict[str, Any]],
    *,
    target_depth: int,
    target_kind: str,
) -> str:
    pieces = [
        f"{int(edge['parent_depth'])}:{edge['kind']}"
        for edge in path_edges
        if edge.get("kind") in {"same_vehicle", "separate_vehicle"}
    ]
    pieces.append(f"{int(target_depth)}:{target_kind}")
    return "force_child_kind_depth:" + ";".join(pieces)


def _branch_pair(record: dict[str, Any]) -> tuple[int, int] | None:
    left = _parse_rf(record.get("left"))
    right = _parse_rf(record.get("right"))
    parsed = left or right
    if parsed is None:
        return None
    pair = _pair(parsed)
    if left is not None and _pair(left) != pair:
        return None
    if right is not None and _pair(right) != pair:
        return None
    return pair


def _first_started_child_kind(events: list[dict[str, Any]], parent_node_id: int) -> str | None:
    children: dict[int, str] = {}
    for record in events:
        if record.get("event") != "journey_child_queued":
            continue
        if _int(record.get("parent_node_id"), -1) != int(parent_node_id):
            continue
        parsed = _parse_rf(record.get("constraint"))
        if parsed is None:
            continue
        children[_int(record.get("child_node_id"), -1)] = str(parsed["kind"])
    starts: list[tuple[float, int]] = []
    for record in events:
        if record.get("event") != "journey_node_start":
            continue
        node_id = _int(record.get("node_id"), -1)
        if node_id in children:
            starts.append((_float(record.get("time"), 0.0), node_id))
    if starts:
        _time, node_id = min(starts)
        return children.get(node_id)
    if children:
        return children[min(children)]
    return None


def _branch_pressure(events: list[dict[str, Any]], branch_record: dict[str, Any]) -> dict[str, Any]:
    node_id = _int(branch_record.get("node_id"), -1)
    depth = _int(branch_record.get("depth"), 0)
    children = _children_by_parent(events)
    subtree_nodes = {node_id, *_descendants(children, node_id)}
    counters: Counter[str] = Counter()
    max_subtree_time = _float(branch_record.get("time"), 0.0)
    for record in events:
        event = str(record.get("event") or "")
        if record.get("node_id") is not None and _int(record.get("node_id"), -999999) not in subtree_nodes:
            continue
        if event in {
            "journey_branch",
            "journey_fathom",
            "journey_exact_pricing_retry",
            "journey_exact_pricing_completion_bound_retry",
            "journey_exact_pricing_completion_bound_pre_reserve",
        }:
            counters[event] += 1
            max_subtree_time = max(max_subtree_time, _float(record.get("time"), max_subtree_time))
    score = (
        5.0 * counters["journey_exact_pricing_completion_bound_retry"]
        + 2.0 * counters["journey_branch"]
        + float(depth)
        - 3.0 * counters["journey_fathom"]
    )
    return {
        "subtree_node_count": len(subtree_nodes),
        "subtree_branch_count": counters["journey_branch"],
        "subtree_completion_bound_retry_count": counters["journey_exact_pricing_completion_bound_retry"],
        "subtree_ordinary_retry_count": counters["journey_exact_pricing_retry"],
        "subtree_fathom_count": counters["journey_fathom"],
        "subtree_last_event_time": round(float(max_subtree_time), 6),
        "priority_score": round(float(score), 6),
    }


def _command(
    *,
    config: Path,
    instance: str,
    time_limit: int,
    result_dir: Path,
    force_pair_path_rule: str,
    force_child_kind_rule: str,
    candidate_log_top_n: int,
    max_nodes: int,
    max_cg_iterations: int | None,
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
        f"journey_child_priority_mode={force_child_kind_rule}",
        "--set",
        f"journey_branch_candidate_log_top_n={int(candidate_log_top_n)}",
        "--set",
        f"max_nodes={int(max_nodes)}",
        "--set",
        f"journey_max_nodes={int(max_nodes)}",
        "--set",
        "journey_child_priority_by_width_enabled=False",
        "--set",
        "journey_tail_action_audit_enabled=True",
        "--set",
        "journey_corrected_node_bound_audit_enabled=True",
        "--set",
        "journey_corrected_node_bound_fathom_enabled=False",
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
    if max_cg_iterations is not None:
        command.extend(
            [
                "--set",
                f"max_cg_iterations={int(max_cg_iterations)}",
                "--set",
                f"journey_max_cg_iterations={int(max_cg_iterations)}",
            ]
        )
    return command


def build_runbook(
    log_paths: list[Path],
    output_dir: Path,
    report: Path,
    *,
    config: Path = DEFAULT_CONFIG,
    instance_root: Path = DEFAULT_INSTANCE_ROOT,
    time_limit: int = 240,
    limit_pairs: int = 8,
    min_depth: int = 0,
    max_depth: int = 12,
    min_source_time: float | None = None,
    max_source_time: float | None = None,
    max_pairs_per_instance: int | None = None,
    candidate_log_top_n: int = 200,
    probe_extra_nodes_after_branch: int = 4,
    probe_max_cg_iterations: int | None = 18,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_root = output_dir / "runs"
    source_events: list[dict[str, Any]] = []
    skipped_no_instance = 0
    skipped_no_pair = 0
    source_log_count = 0

    for log_path in _iter_jsonl_paths(log_paths):
        source_log_count += 1
        events = list(_iter_jsonl(log_path))
        instance = _instance_from_log_path(log_path, instance_root)
        if instance is None:
            skipped_no_instance += 1
            continue
        for record in events:
            if record.get("event") != "journey_branch":
                continue
            node_id = _int(record.get("node_id"), -1)
            depth = _int(record.get("depth"), -1)
            if node_id < 0 or depth < int(min_depth) or depth > int(max_depth):
                continue
            source_time = _float(record.get("time"), 0.0)
            if min_source_time is not None and source_time < float(min_source_time):
                continue
            if max_source_time is not None and source_time > float(max_source_time):
                continue
            pair = _branch_pair(record)
            if pair is None:
                skipped_no_pair += 1
                continue
            path_edges = _node_parent_path(events, node_id)
            pressure = _branch_pressure(events, record)
            source_events.append(
                {
                    "log_path": log_path,
                    "instance": instance,
                    "events": events,
                    "record": record,
                    "node_id": node_id,
                    "depth": depth,
                    "source_time": source_time,
                    "pair": pair,
                    "path_edges": path_edges,
                    "source_first_child_kind": _first_started_child_kind(events, node_id),
                    **pressure,
                }
            )

    source_events.sort(
        key=lambda item: (
            -float(item.get("priority_score", 0.0)),
            -int(item.get("depth", 0)),
            float(item.get("source_time", 0.0)),
            str(item.get("instance", "")),
        )
    )

    entries: list[dict[str, Any]] = []
    selected_pairs = 0
    selected_by_instance: Counter[str] = Counter()
    seen: set[tuple[str, int, int, int, int, str]] = set()
    for item in source_events:
        if selected_pairs >= int(limit_pairs):
            break
        instance = str(item["instance"])
        if (
            max_pairs_per_instance is not None
            and selected_by_instance[instance] >= int(max_pairs_per_instance)
        ):
            continue
        depth = int(item["depth"])
        node_id = int(item["node_id"])
        pair = tuple(item["pair"])
        key = (instance, node_id, depth, int(pair[0]), int(pair[1]), str(item["source_first_child_kind"]))
        if key in seen:
            continue
        seen.add(key)
        selected_pairs += 1
        selected_by_instance[instance] += 1
        pair_group_id = f"{_safe_slug(Path(instance).stem)}__d{depth}__n{node_id}__{pair[0]}_{pair[1]}"
        force_pair_rule = _force_pair_path_rule(item["path_edges"], depth, pair)
        max_nodes = max(1, depth + 1 + max(0, int(probe_extra_nodes_after_branch)))
        for target_kind in ("same_vehicle", "separate_vehicle"):
            force_child_rule = _force_child_kind_depth_rule(
                item["path_edges"],
                target_depth=depth,
                target_kind=target_kind,
            )
            experiment = (
                f"{len(entries) + 1:03d}_child_order_{target_kind}_"
                f"d{depth}_n{node_id}_{pair[0]}_{pair[1]}_{_safe_slug(Path(instance).stem)}"
            )
            result_dir = run_root / experiment
            command = _command(
                config=config,
                instance=instance,
                time_limit=time_limit,
                result_dir=result_dir,
                force_pair_path_rule=force_pair_rule,
                force_child_kind_rule=force_child_rule,
                candidate_log_top_n=candidate_log_top_n,
                max_nodes=max_nodes,
                max_cg_iterations=probe_max_cg_iterations,
            )
            entries.append(
                {
                    "experiment": experiment,
                    "instance": instance,
                    "source_log_file": str(item["log_path"]),
                    "source_node_id": node_id,
                    "source_depth": depth,
                    "source_time": round(float(item["source_time"]), 6),
                    "source_pair": [int(pair[0]), int(pair[1])],
                    "source_first_child_kind": item.get("source_first_child_kind"),
                    "target_child_kind": target_kind,
                    "pair_group_id": pair_group_id,
                    "pair_role": f"{target_kind}_first",
                    "source_path_edges": item["path_edges"],
                    "forced_pair_path_rule": force_pair_rule,
                    "forced_child_kind_depth_rule": force_child_rule,
                    "probe_max_nodes": max_nodes,
                    "probe_max_cg_iterations": probe_max_cg_iterations,
                    "probe_extra_nodes_after_branch": int(probe_extra_nodes_after_branch),
                    "subtree_node_count": item.get("subtree_node_count"),
                    "subtree_branch_count": item.get("subtree_branch_count"),
                    "subtree_completion_bound_retry_count": item.get(
                        "subtree_completion_bound_retry_count"
                    ),
                    "subtree_ordinary_retry_count": item.get("subtree_ordinary_retry_count"),
                    "subtree_fathom_count": item.get("subtree_fathom_count"),
                    "subtree_last_event_time": item.get("subtree_last_event_time"),
                    "priority_score": item.get("priority_score"),
                    "command": command,
                    "shell_command": shlex.join(command),
                    "expected_label_source": "paired_same_first_vs_separate_first_fixed_budget_child_order_probe",
                }
            )

    runbook = {
        "schema_version": "journey_child_order_paired_runbook_v1",
        "runs_bpc_or_pricing": False,
        "diagnostic_only": True,
        "official_bound_effect": False,
        "certificate_effect": False,
        "source_log_count": source_log_count,
        "source_branch_event_count": len(source_events),
        "selected_pair_count": selected_pairs,
        "entry_count": len(entries),
        "command_count": len(entries),
        "config": str(config),
        "time_limit": int(time_limit),
        "min_depth": int(min_depth),
        "max_depth": int(max_depth),
        "min_source_time": min_source_time,
        "max_source_time": max_source_time,
        "max_pairs_per_instance": max_pairs_per_instance,
        "candidate_log_top_n": int(candidate_log_top_n),
        "probe_extra_nodes_after_branch": int(probe_extra_nodes_after_branch),
        "probe_max_cg_iterations": probe_max_cg_iterations,
        "skipped_no_instance": skipped_no_instance,
        "skipped_no_pair": skipped_no_pair,
        "entries": entries,
    }
    (output_dir / "runbook.json").write_text(
        json.dumps(runbook, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "commands.sh").write_text(
        "\n".join(entry["shell_command"] for entry in entries) + ("\n" if entries else ""),
        encoding="utf-8",
    )
    _write_report(report, output_dir / "runbook.json")
    return runbook


def _write_report(report: Path, runbook_path: Path) -> None:
    runbook = json.loads(runbook_path.read_text(encoding="utf-8"))
    lines = [
        "# Journey Child Order Paired Replay Runbook",
        "",
        "该 runbook 只从已有 JSONL 日志抽取 hard-path branch 节点并生成 same-first / separate-first 成对 replay 命令；生成本身不运行 BPC / pricing / RMP。",
        "",
        "## Summary",
        "",
        f"- source_log_count: `{runbook['source_log_count']}`",
        f"- source_branch_event_count: `{runbook['source_branch_event_count']}`",
        f"- selected_pair_count: `{runbook['selected_pair_count']}`",
        f"- entry_count: `{runbook['entry_count']}`",
        f"- time_limit: `{runbook['time_limit']}`",
        f"- probe_extra_nodes_after_branch: `{runbook['probe_extra_nodes_after_branch']}`",
        f"- probe_max_cg_iterations: `{runbook['probe_max_cg_iterations']}`",
        "",
        "## Entries",
        "",
    ]
    for entry in runbook.get("entries", [])[:24]:
        lines.extend(
            [
                f"### {entry['experiment']}",
                "",
                f"- instance: `{entry['instance']}`",
                f"- source depth/node: `{entry['source_depth']}` / `{entry['source_node_id']}`",
                f"- source pair: `{entry['source_pair']}`",
                f"- target_child_kind: `{entry['target_child_kind']}`",
                f"- source_first_child_kind: `{entry.get('source_first_child_kind')}`",
                f"- priority_score: `{entry.get('priority_score')}`",
                f"- subtree CB retry: `{entry.get('subtree_completion_bound_retry_count')}`",
                f"- forced_pair_path_rule: `{entry['forced_pair_path_rule']}`",
                f"- forced_child_kind_depth_rule: `{entry['forced_child_kind_depth_rule']}`",
                "",
            ]
        )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_path", nargs="+", type=Path)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path)
    parser.add_argument("--report", default=DEFAULT_REPORT, type=Path)
    parser.add_argument("--config", default=DEFAULT_CONFIG, type=Path)
    parser.add_argument("--instance-root", default=DEFAULT_INSTANCE_ROOT, type=Path)
    parser.add_argument("--time-limit", default=240, type=int)
    parser.add_argument("--limit-pairs", default=8, type=int)
    parser.add_argument("--min-depth", default=0, type=int)
    parser.add_argument("--max-depth", default=12, type=int)
    parser.add_argument("--min-source-time", type=float)
    parser.add_argument("--max-source-time", type=float)
    parser.add_argument("--max-pairs-per-instance", type=int)
    parser.add_argument("--candidate-log-top-n", default=200, type=int)
    parser.add_argument("--probe-extra-nodes-after-branch", default=4, type=int)
    parser.add_argument("--probe-max-cg-iterations", default=18, type=int)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    runbook = build_runbook(
        list(args.log_path),
        args.output_dir,
        args.report,
        config=args.config,
        instance_root=args.instance_root,
        time_limit=args.time_limit,
        limit_pairs=args.limit_pairs,
        min_depth=args.min_depth,
        max_depth=args.max_depth,
        min_source_time=args.min_source_time,
        max_source_time=args.max_source_time,
        max_pairs_per_instance=args.max_pairs_per_instance,
        candidate_log_top_n=args.candidate_log_top_n,
        probe_extra_nodes_after_branch=args.probe_extra_nodes_after_branch,
        probe_max_cg_iterations=args.probe_max_cg_iterations,
    )
    print(json.dumps({k: v for k, v in runbook.items() if k != "entries"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
