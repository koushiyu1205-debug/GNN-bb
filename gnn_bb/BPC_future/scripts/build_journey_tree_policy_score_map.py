#!/usr/bin/env python3
"""Build aggregate Journey tree-policy score maps from successful runs.

This script is offline and diagnostic-only. It reads existing solver JSONL
logs, aggregates observed branch pair choices and same/separate child order,
and emits score rows consumable by:

* ``journey_branch_candidate_priority=branch_score_horizon``
* ``journey_child_priority_mode=child_score``

It never runs BPC, pricing, RMP, or creates official bounds/certificates.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
import csv
import json
from pathlib import Path
import re
from typing import Any, Iterable


@dataclass
class _BranchAcc:
    count: int = 0
    ordinal_sum: float = 0.0
    time_sum: float = 0.0
    context_scope: str = ""
    depth: int | None = None
    node_id: int | None = None
    pair: tuple[int, int] = (0, 0)


@dataclass
class _ChildAcc:
    count: int = 0
    rank_sum: float = 0.0
    ordinal_sum: float = 0.0
    context_scope: str = ""
    depth: int | None = None
    node_id: int | None = None
    pair: tuple[int, int] = (0, 0)
    kind: str = ""


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                yield row


def _pair_from_constraint_text(text: Any) -> tuple[int, int] | None:
    match = re.search(r"RF\((\d+)\s*,\s*(\d+)\)=", str(text or ""))
    if match is None:
        return None
    i, j = int(match.group(1)), int(match.group(2))
    if i == j:
        return None
    return tuple(sorted((i, j)))


def _kind_from_constraint_text(text: Any) -> str | None:
    match = re.search(r"=(same_vehicle|separate_vehicle)\b", str(text or ""))
    if match is None:
        return None
    return str(match.group(1))


def _pair_from_event(event: dict[str, Any]) -> tuple[int, int] | None:
    pair = event.get("selected_pair") or event.get("pair")
    if isinstance(pair, (list, tuple)) and len(pair) == 2:
        try:
            i, j = int(pair[0]), int(pair[1])
        except (TypeError, ValueError):
            return None
        if i != j:
            return tuple(sorted((i, j)))
    return _pair_from_constraint_text(event.get("left") or event.get("constraint"))


def _event_time(event: dict[str, Any]) -> float:
    for key in ("time", "elapsed_time", "wall_time", "timestamp"):
        value = event.get(key)
        if value is None:
            continue
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if parsed == parsed:
            return float(parsed)
    return 0.0


def _instance_from_log(path: Path) -> str:
    text = str(path).replace("\\", "/")
    marker = "/logs/"
    if marker in text:
        return text.split(marker, 1)[1].removesuffix(".jsonl")
    return path.name.removesuffix(".jsonl")


def _scope_from_instance(instance: str, context_scope: str) -> str:
    if context_scope == "none":
        return ""
    text = str(instance).replace("\\", "/")
    parts = text.split("/")
    try:
        idx = parts.index("tasks_020")
    except ValueError:
        idx = -1
    if context_scope == "instance":
        return text
    if idx >= 0 and len(parts) > idx + 2:
        family = parts[idx + 1]
        site = parts[idx + 2]
        if context_scope == "family":
            return family
        if context_scope == "family_site":
            return f"{family}/{site}"
    return text if context_scope == "instance" else ""


def _instance_to_log_path(results_csv: Path, instance: str) -> Path:
    return results_csv.parent / "logs" / f"{instance}.jsonl"


def _logs_from_results_csvs(results_csvs: list[Path], only_status: str) -> list[Path]:
    logs: list[Path] = []
    seen: set[str] = set()
    for results_csv in results_csvs:
        if not results_csv.exists():
            continue
        with results_csv.open(newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if row.get("status") != only_status:
                    continue
                instance = row.get("instance")
                if not instance:
                    continue
                log_path = _instance_to_log_path(results_csv, instance)
                if not log_path.exists():
                    continue
                key = str(log_path)
                if key in seen:
                    continue
                seen.add(key)
                logs.append(log_path)
    return logs


def _key_parts(
    *,
    context_scope: str,
    key_scope: str,
    node_id: int,
    depth: int,
    pair: tuple[int, int],
    kind: str | None = None,
) -> tuple[Any, ...]:
    base: list[Any] = [context_scope]
    if key_scope == "node_depth":
        base.extend([node_id, depth])
    elif key_scope == "depth":
        base.append(depth)
    elif key_scope == "pair":
        pass
    else:
        raise ValueError(f"unsupported key_scope: {key_scope}")
    base.extend([int(pair[0]), int(pair[1])])
    if kind is not None:
        base.append(kind)
    return tuple(base)


def build_tree_policy_score_map(
    logs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    key_scope: str = "depth",
    context_scope: str = "family_site",
) -> dict[str, Any]:
    if key_scope not in {"node_depth", "depth", "pair"}:
        raise ValueError(f"unsupported key_scope: {key_scope}")
    if context_scope not in {"none", "family", "family_site", "instance"}:
        raise ValueError(f"unsupported context_scope: {context_scope}")

    branch_accs: dict[tuple[Any, ...], _BranchAcc] = {}
    child_accs: dict[tuple[Any, ...], _ChildAcc] = {}
    skipped_branch_events = 0
    skipped_child_events = 0
    parsed_log_count = 0

    for log_path in logs:
        events = list(_iter_jsonl(log_path))
        if not events:
            continue
        parsed_log_count += 1
        instance = _instance_from_log(log_path)
        scope = _scope_from_instance(instance, context_scope)
        child_rank_by_parent: dict[int, int] = defaultdict(int)
        for ordinal, event in enumerate(events):
            if event.get("event") == "journey_branch":
                pair = _pair_from_event(event)
                try:
                    node_id = int(event.get("node_id"))
                    depth = int(event.get("depth"))
                except (TypeError, ValueError):
                    skipped_branch_events += 1
                    continue
                if pair is None:
                    skipped_branch_events += 1
                    continue
                key = _key_parts(
                    context_scope=scope,
                    key_scope=key_scope,
                    node_id=node_id,
                    depth=depth,
                    pair=pair,
                )
                acc = branch_accs.setdefault(
                    key,
                    _BranchAcc(context_scope=scope, node_id=node_id, depth=depth, pair=pair),
                )
                acc.count += 1
                acc.ordinal_sum += float(ordinal)
                acc.time_sum += _event_time(event)
                continue
            if event.get("event") == "journey_child_queued":
                pair = _pair_from_constraint_text(event.get("constraint"))
                kind = _kind_from_constraint_text(event.get("constraint"))
                try:
                    parent_node_id = int(event.get("parent_node_id"))
                    depth = int(event.get("depth")) - 1
                except (TypeError, ValueError):
                    skipped_child_events += 1
                    continue
                if pair is None or kind is None or depth < 0:
                    skipped_child_events += 1
                    continue
                rank = child_rank_by_parent[parent_node_id]
                child_rank_by_parent[parent_node_id] += 1
                key = _key_parts(
                    context_scope=scope,
                    key_scope=key_scope,
                    node_id=parent_node_id,
                    depth=depth,
                    pair=pair,
                    kind=kind,
                )
                acc = child_accs.setdefault(
                    key,
                    _ChildAcc(
                        context_scope=scope,
                        node_id=parent_node_id,
                        depth=depth,
                        pair=pair,
                        kind=kind,
                    ),
                )
                acc.count += 1
                acc.rank_sum += float(rank)
                acc.ordinal_sum += float(ordinal)

    branch_rows: list[dict[str, Any]] = []
    for acc in branch_accs.values():
        avg_ordinal = acc.ordinal_sum / max(1, acc.count)
        avg_time = acc.time_sum / max(1, acc.count)
        score = float(acc.count) * 1000.0 - avg_ordinal / 1000.0 - avg_time / 10000.0
        row: dict[str, Any] = {
            "schema_version": "journey_tree_policy_branch_score_row_v1",
            "diagnostic_only": True,
            "runs_bpc_or_pricing": False,
            "production_ready": False,
            "certificate_effect": False,
            "official_bound_effect": False,
            "context_scope": context_scope,
            "key_scope": key_scope,
            "scope": acc.context_scope,
            "pair": [int(acc.pair[0]), int(acc.pair[1])],
            "task_i": int(acc.pair[0]),
            "task_j": int(acc.pair[1]),
            "observation_count": int(acc.count),
            "avg_source_event_ordinal": round(float(avg_ordinal), 9),
            "avg_source_time": round(float(avg_time), 9),
            "score": round(float(score), 9),
            "branch_score": round(float(score), 9),
        }
        if key_scope in {"node_depth", "depth"}:
            row["depth"] = acc.depth
        if key_scope == "node_depth":
            row["node_id"] = acc.node_id
        if acc.context_scope:
            row["source_log_file"] = acc.context_scope
        branch_rows.append(row)

    child_rows: list[dict[str, Any]] = []
    for acc in child_accs.values():
        avg_rank = acc.rank_sum / max(1, acc.count)
        avg_ordinal = acc.ordinal_sum / max(1, acc.count)
        score = float(acc.count) * 1000.0 - avg_rank * 100.0 - avg_ordinal / 1000.0
        row = {
            "schema_version": "journey_tree_policy_child_score_row_v1",
            "diagnostic_only": True,
            "runs_bpc_or_pricing": False,
            "production_ready": False,
            "certificate_effect": False,
            "official_bound_effect": False,
            "context_scope": context_scope,
            "key_scope": key_scope,
            "scope": acc.context_scope,
            "pair": [int(acc.pair[0]), int(acc.pair[1])],
            "task_i": int(acc.pair[0]),
            "task_j": int(acc.pair[1]),
            "child_constraint_kind": acc.kind,
            "observation_count": int(acc.count),
            "avg_child_queue_rank": round(float(avg_rank), 9),
            "avg_source_event_ordinal": round(float(avg_ordinal), 9),
            "score": round(float(score), 9),
            "child_score": round(float(score), 9),
        }
        if key_scope in {"node_depth", "depth"}:
            row["depth"] = acc.depth
        if key_scope == "node_depth":
            row["node_id"] = acc.node_id
        if acc.context_scope:
            row["source_log_file"] = acc.context_scope
        child_rows.append(row)

    branch_rows.sort(
        key=lambda row: (
            str(row.get("scope", "")),
            int(row.get("depth", -1)),
            -float(row["score"]),
            int(row["task_i"]),
            int(row["task_j"]),
        )
    )
    child_rows.sort(
        key=lambda row: (
            str(row.get("scope", "")),
            int(row.get("depth", -1)),
            int(row["task_i"]),
            int(row["task_j"]),
            -float(row["score"]),
        )
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    branch_path = output_dir / "journey_branch_tree_policy_score_rows.json"
    child_path = output_dir / "journey_child_tree_policy_score_rows.json"
    branch_path.write_text(json.dumps(branch_rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    child_path.write_text(json.dumps(child_rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "journey_branch_tree_policy_score_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in branch_rows),
        encoding="utf-8",
    )
    (output_dir / "journey_child_tree_policy_score_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in child_rows),
        encoding="utf-8",
    )
    summary = {
        "schema_version": "journey_tree_policy_score_map_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "input_log_count": len(logs),
        "parsed_log_count": int(parsed_log_count),
        "branch_score_row_count": len(branch_rows),
        "child_score_row_count": len(child_rows),
        "skipped_branch_event_count": int(skipped_branch_events),
        "skipped_child_event_count": int(skipped_child_events),
        "key_scope": key_scope,
        "context_scope": context_scope,
        "branch_score_rows_path": str(branch_path),
        "child_score_rows_path": str(child_path),
        "solver_branch_priority": "branch_score_horizon",
        "solver_child_priority_mode": "child_score",
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    _write_report(report, summary, branch_rows, child_rows)
    return summary


def _write_report(
    report: Path,
    summary: dict[str, Any],
    branch_rows: list[dict[str, Any]],
    child_rows: list[dict[str, Any]],
) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Tree Policy Score Map",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "从多个成功日志聚合 branch pair 和 child ordering 偏好，生成 opt-in tree-policy score map。该脚本只读日志，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
    ]
    for key in [
        "input_log_count",
        "parsed_log_count",
        "branch_score_row_count",
        "child_score_row_count",
        "skipped_branch_event_count",
        "skipped_child_event_count",
        "key_scope",
        "context_scope",
        "solver_branch_priority",
        "solver_child_priority_mode",
        "branch_score_rows_path",
        "child_score_rows_path",
        "production_ready",
        "certificate_effect",
        "official_bound_effect",
    ]:
        lines.append(f"{key} = {summary.get(key)}")
    lines.extend(["```", "", "## Top Branch Rows", ""])
    for row in branch_rows[:16]:
        lines.append(
            f"- scope={row.get('scope')} depth={row.get('depth')} pair={row['pair']} "
            f"score={row['score']} obs={row['observation_count']}"
        )
    lines.extend(["", "## Top Child Rows", ""])
    for row in child_rows[:16]:
        lines.append(
            f"- scope={row.get('scope')} depth={row.get('depth')} pair={row['pair']} "
            f"kind={row['child_constraint_kind']} score={row['score']} obs={row['observation_count']}"
        )
    lines.extend(["", "## 使用边界", ""])
    lines.append(
        "`branch_score_horizon` 和 `child_score` 只改变排序/入队顺序；不提供 bound，不剪枝，不替代 exact pricing closure。"
    )
    lines.append(
        "该 map 是跨实例聚合启发式，必须经过 smoke/full replay 才能进入 production-ready 训练或默认配置。"
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs", nargs="*", type=Path, default=[])
    parser.add_argument("--results-csv", action="append", type=Path, default=[])
    parser.add_argument("--only-status", default="OPTIMAL")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--key-scope", choices=("node_depth", "depth", "pair"), default="depth")
    parser.add_argument(
        "--context-scope",
        choices=("none", "family", "family_site", "instance"),
        default="family_site",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    logs = list(args.logs or [])
    logs.extend(_logs_from_results_csvs(list(args.results_csv or []), str(args.only_status)))
    seen: set[str] = set()
    unique_logs = []
    for log in logs:
        key = str(log)
        if key in seen:
            continue
        seen.add(key)
        unique_logs.append(log)
    summary = build_tree_policy_score_map(
        unique_logs,
        args.output_dir,
        args.report,
        key_scope=str(args.key_scope),
        context_scope=str(args.context_scope),
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
