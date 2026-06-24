#!/usr/bin/env python3
"""Build forced-pair replay commands from Journey branch-impact audits.

The output is a runbook only.  It does not run BPC, pricing, RMP, or produce
certificates.  Each command replays the same instance and forces one alternative
Ryan-Foster pair from the logged priority_top list while keeping exact pricing
closure unchanged.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import shlex
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_impact_alt_runbook_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_journey_branch_impact_alt_runbook_zh.md"
)
DEFAULT_CONFIG = Path("BPC_future/configs/moon_trek_20_smoke.yaml")
_RF_RE = re.compile(r"RF\((?P<i>\d+),(?P<j>\d+)\)=(?P<kind>same_vehicle|separate_vehicle)")


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


def _instance_from_log_file(log_file: Any) -> str | None:
    text = str(log_file or "")
    marker = "BPC_future/logical_graph/"
    if marker in text:
        instance = marker + text.split(marker, 1)[1]
        if instance.endswith(".jsonl"):
            instance = instance[: -len(".jsonl")]
        return instance or None
    return None


def _parse_rf_constraint(text: Any) -> dict[str, Any] | None:
    if not isinstance(text, str):
        return None
    match = _RF_RE.search(text)
    if match is None:
        return None
    i = int(match.group("i"))
    j = int(match.group("j"))
    return {"task_i": min(i, j), "task_j": max(i, j), "kind": str(match.group("kind"))}


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


def _force_pair_path_rule(path_edges: list[dict[str, Any]], target_depth: int, task_i: int, task_j: int) -> str:
    pieces: list[str] = []
    for edge in path_edges:
        pieces.append(
            f"{int(edge['parent_depth'])}:{int(edge['task_i'])},{int(edge['task_j'])}={edge['kind']}"
        )
    pieces.append(f"{int(target_depth)}:{int(task_i)},{int(task_j)}")
    return "force_pair_path:" + ";".join(pieces)


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


def _candidate_pair(candidate: dict[str, Any]) -> tuple[int, int] | None:
    try:
        i = int(candidate["task_i"])
        j = int(candidate["task_j"])
    except (KeyError, TypeError, ValueError):
        return None
    if i == j:
        return None
    return tuple(sorted((i, j)))


def _alternative_candidates(row: dict[str, Any], per_node: int) -> list[dict[str, Any]]:
    if int(per_node) <= 0:
        return []
    selected_pair = None
    observed = row.get("observed_branch_candidate")
    if isinstance(observed, dict):
        selected_pair = _candidate_pair(observed)
    if selected_pair is None and row.get("task_i") is not None and row.get("task_j") is not None:
        selected_pair = tuple(sorted((int(row["task_i"]), int(row["task_j"]))))
    priority_top = row.get("priority_top")
    if not isinstance(priority_top, list):
        return []
    seen: set[tuple[int, int]] = set()
    if selected_pair is not None:
        seen.add(selected_pair)
    alternatives: list[dict[str, Any]] = []
    for rank, candidate in enumerate(priority_top):
        if not isinstance(candidate, dict):
            continue
        pair = _candidate_pair(candidate)
        if pair is None or pair in seen:
            continue
        seen.add(pair)
        alternatives.append(
            {
                "task_i": pair[0],
                "task_j": pair[1],
                "source_alt_rank": int(rank),
                "source_alt_fractionality": candidate.get("fractionality"),
                "source_alt_same_mass": candidate.get("same_mass"),
                "source_alt_support_count": candidate.get("support_count"),
                "source_alt_incumbent_relation": candidate.get("incumbent_relation"),
                "source_alt_incumbent_disagreement": candidate.get("incumbent_disagreement"),
                "source_alt_pool_same_allowed": candidate.get("pool_same_allowed"),
                "source_alt_pool_separate_allowed": candidate.get("pool_separate_allowed"),
                "source_alt_pool_max_child_width": candidate.get("pool_max_child_width"),
                "source_alt_pool_total_child_width": candidate.get("pool_total_child_width"),
                "source_alt_pool_balance_gap": candidate.get("pool_balance_gap"),
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
    return alternatives[: int(per_node)]


def build_runbook(
    branch_impact_inputs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    config: Path = DEFAULT_CONFIG,
    time_limit: int = 600,
    limit: int = 24,
    alt_pairs_per_node: int = 2,
) -> dict[str, Any]:
    rows = _load_branch_rows(branch_impact_inputs)
    run_root = output_dir / "runs"
    entries: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int, int, int]] = set()
    for row in rows:
        if len(entries) >= int(limit):
            break
        if not bool(row.get("label_observation_complete")):
            continue
        if not bool(row.get("usable_for_branch_impact_training", True)):
            continue
        if str(row.get("branch_feature_source") or "") != "candidate_log":
            continue
        instance = _instance_from_log_file(row.get("log_file"))
        if instance is None:
            continue
        try:
            node_id = int(row["branch_node_id"])
            depth = int(row["depth"])
        except (KeyError, TypeError, ValueError):
            continue
        events = _read_log_events(row.get("log_file"))
        path_edges = _node_parent_path(events, node_id)
        selected_pair = [int(row.get("task_i")), int(row.get("task_j"))]
        for alt in _alternative_candidates(row, alt_pairs_per_node):
            if len(entries) >= int(limit):
                break
            alt_task_i = int(alt["task_i"])
            alt_task_j = int(alt["task_j"])
            key = (instance, node_id, depth, alt_task_i, alt_task_j)
            if key in seen:
                continue
            seen.add(key)
            force_rule = _force_pair_path_rule(path_edges, depth, alt_task_i, alt_task_j)
            experiment = (
                f"{len(entries) + 1:02d}_branch_alt_pair_d{depth}_n{node_id}_"
                f"r{int(alt['source_alt_rank'])}_{alt_task_i}_{alt_task_j}_{_safe_slug(Path(instance).stem)}"
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
                f"journey_branch_candidate_priority={force_rule}",
                "--set",
                "journey_branch_candidate_log_top_n=12",
            ]
            entries.append(
                {
                    "experiment": experiment,
                    "instance": instance,
                    "source_type": "branch_impact_alt_pair",
                    "source_log_file": row.get("log_file"),
                    "source_node_id": node_id,
                    "source_depth": depth,
                    "source_selected_pair": selected_pair,
                    "source_selected_tail_class": row.get("tail_class"),
                    "source_selected_labels": row.get("branch_labels"),
                    "source_path_edges": path_edges,
                    "forced_pair": [alt_task_i, alt_task_j],
                    "forced_pair_path_rule": force_rule,
                    "command": command,
                    "shell_command": shlex.join(command),
                    "expected_label_source": "rerun_then_audit_branch_impact",
                    **alt,
                }
            )
    runbook = {
        "schema_version": "journey_branch_impact_alt_runbook_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "stage4_candidate_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "branch_impact_input_paths": [str(path) for path in branch_impact_inputs],
        "config": str(config),
        "time_limit": int(time_limit),
        "alt_pairs_per_node": int(alt_pairs_per_node),
        "entry_count": len(entries),
        "candidate_source": "complete_branch_impact_rows_priority_top_alternatives",
        "entries": entries,
        "notes": (
            "Commands force an alternative legal Ryan-Foster pair at the same "
            "node path when that pair is still fractional.  If the pair is not "
            "legal in replay, solver candidate selection falls back according "
            "to existing exact-safe logic.  No command changes official bounds "
            "or certificate semantics."
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
        "# Journey Branch-Impact Alternative Runbook",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "从完整 branch-impact audit 的 `priority_top` 中生成同节点 alternative forced-pair replay 命令，用于补充 branch 候选排序所需的反事实标签。runbook 只生成命令，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "journey_branch_impact_alt_runbook = current",
        f"output_dir = {output_dir}",
        f"entry_count = {runbook.get('entry_count')}",
        f"branch_impact_input_paths = {runbook.get('branch_impact_input_paths')}",
        f"alt_pairs_per_node = {runbook.get('alt_pairs_per_node')}",
        f"time_limit = {runbook.get('time_limit')}",
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
                f"source_node_id = {entry.get('source_node_id')}",
                f"source_depth = {entry.get('source_depth')}",
                f"source_selected_pair = {entry.get('source_selected_pair')}",
                f"forced_pair = {entry.get('forced_pair')}",
                f"forced_pair_path_rule = {entry.get('forced_pair_path_rule')}",
                f"source_alt_rank = {entry.get('source_alt_rank')}",
                f"source_alt_pool_max_child_width = {entry.get('source_alt_pool_max_child_width')}",
                f"source_alt_pool_total_child_width = {entry.get('source_alt_pool_total_child_width')}",
                f"source_selected_tail_class = {entry.get('source_selected_tail_class')}",
                "```",
                "",
                "```bash",
                str(entry["shell_command"]),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## 边界",
            "",
            "这些命令只改变 branch 候选优先级；如果 forced pair 在 replay 时不是当前合法 fractional candidate，会按现有 solver 逻辑回退。最终 no-negative closure、node bound、fathom 仍只来自 exact-safe pricing / certificate。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("branch_impact_input", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--time-limit", type=int, default=600)
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument("--alt-pairs-per-node", type=int, default=2)
    args = parser.parse_args()
    runbook = build_runbook(
        args.branch_impact_input,
        args.output_dir,
        args.report,
        config=args.config,
        time_limit=args.time_limit,
        limit=args.limit,
        alt_pairs_per_node=args.alt_pairs_per_node,
    )
    print(json.dumps(runbook, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
