#!/usr/bin/env python3
"""Build branch/child score maps that replay an observed Journey branch tree.

The script is diagnostic-only. It reads existing solver JSONL logs and writes
opt-in score maps for ``journey_branch_candidate_priority=branch_score_horizon``
and ``journey_child_priority_mode=child_score``. It never runs BPC, pricing,
RMP, or creates official bounds/certificates.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import shlex
from typing import Any, Iterable


DEFAULT_CONFIG = Path("BPC_future/configs/moon_trek_20_smoke.yaml")


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                yield payload


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


def _event_time(event: dict[str, Any], fallback: int) -> float:
    for key in ("time", "elapsed_time", "wall_time", "timestamp"):
        value = event.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return float(fallback)


def _instance_from_log(path: Path) -> str:
    text = str(path).replace("\\", "/")
    marker = "/logs/"
    if marker in text:
        return text.split(marker, 1)[1].removesuffix(".jsonl")
    return path.name.removesuffix(".jsonl")


def _run_instance_from_log(path: Path) -> str:
    return _instance_from_log(path)


def build_tree_replay_score_map(
    logs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    config: Path,
    time_limit: float,
    candidate_log_top_n: int,
) -> dict[str, Any]:
    branch_rows: list[dict[str, Any]] = []
    child_rows: list[dict[str, Any]] = []
    commands: list[list[str]] = []
    skipped_branch_events = 0
    skipped_child_events = 0

    for log_path in logs:
        events = list(_iter_jsonl(log_path))
        instance = _run_instance_from_log(log_path)
        child_event_rank_by_parent: dict[int, int] = {}
        branch_count_for_log = 0
        child_count_for_log = 0
        for ordinal, event in enumerate(events):
            if event.get("event") == "journey_branch":
                pair = _pair_from_event(event)
                node_id = event.get("node_id")
                depth = event.get("depth")
                try:
                    node_id = int(node_id)
                    depth = int(depth)
                except (TypeError, ValueError):
                    skipped_branch_events += 1
                    continue
                if pair is None:
                    skipped_branch_events += 1
                    continue
                score = 1000.0 - min(999.0, _event_time(event, ordinal) / 10.0)
                branch_rows.append(
                    {
                        "schema_version": "journey_tree_replay_branch_score_row_v1",
                        "diagnostic_only": True,
                        "runs_bpc_or_pricing": False,
                        "production_ready": False,
                        "certificate_effect": False,
                        "official_bound_effect": False,
                        "instance": instance,
                        "source_log_file": str(log_path),
                        "node_id": node_id,
                        "depth": depth,
                        "pair": [int(pair[0]), int(pair[1])],
                        "task_i": int(pair[0]),
                        "task_j": int(pair[1]),
                        "score": round(float(score), 9),
                        "branch_score": round(float(score), 9),
                        "source_event_ordinal": int(ordinal),
                    }
                )
                branch_count_for_log += 1
                continue
            if event.get("event") == "journey_child_queued":
                pair = _pair_from_constraint_text(event.get("constraint"))
                kind = _kind_from_constraint_text(event.get("constraint"))
                parent_node_id = event.get("parent_node_id")
                child_depth = event.get("depth")
                try:
                    parent_node_id = int(parent_node_id)
                    branch_depth = int(child_depth) - 1
                except (TypeError, ValueError):
                    skipped_child_events += 1
                    continue
                if pair is None or kind is None or branch_depth < 0:
                    skipped_child_events += 1
                    continue
                rank = child_event_rank_by_parent.get(parent_node_id, 0)
                child_event_rank_by_parent[parent_node_id] = rank + 1
                score = 100.0 - float(rank)
                child_rows.append(
                    {
                        "schema_version": "journey_tree_replay_child_score_row_v1",
                        "diagnostic_only": True,
                        "runs_bpc_or_pricing": False,
                        "production_ready": False,
                        "certificate_effect": False,
                        "official_bound_effect": False,
                        "instance": instance,
                        "source_log_file": str(log_path),
                        "node_id": int(parent_node_id),
                        "depth": int(branch_depth),
                        "pair": [int(pair[0]), int(pair[1])],
                        "task_i": int(pair[0]),
                        "task_j": int(pair[1]),
                        "child_constraint_kind": kind,
                        "score": round(float(score), 9),
                        "child_score": round(float(score), 9),
                        "source_event_ordinal": int(ordinal),
                        "source_child_queue_rank": int(rank),
                    }
                )
                child_count_for_log += 1
        if branch_count_for_log > 0:
            run_dir = output_dir / "runs" / Path(instance).stem
            command = [
                "/home/kai/miniconda3/bin/python",
                "BPC_future/scripts/run_bpc_future_external_timeout_batch.py",
                "--config",
                str(config),
                "--instances",
                instance,
                "--time-limit",
                str(float(time_limit)),
                "--results-csv",
                str(run_dir / "results.csv"),
                "--log-dir",
                str(run_dir / "logs"),
                "--solution-dir",
                str(run_dir / "solutions"),
                "--run-log-dir",
                str(run_dir / "run_logs"),
                "--python",
                "/home/kai/miniconda3/bin/python",
                "--timeout-kill-after",
                "30s",
                "--max-workers",
                "1",
                "--quiet",
                "--force-child-exit-after-run",
                "--set",
                "journey_branch_candidate_priority=branch_score_horizon",
                "--set",
                f"journey_branch_candidate_score_path={output_dir / 'journey_branch_tree_score_rows.json'}",
                "--set",
                "journey_branch_candidate_score_horizon_tie_tolerance=1.0",
                "--set",
                "journey_branch_candidate_score_horizon_min_score=0.0",
                "--set",
                "journey_child_priority_mode=child_score",
                "--set",
                f"journey_child_priority_score_path={output_dir / 'journey_child_tree_score_rows.json'}",
                "--set",
                "journey_child_priority_by_width_enabled=False",
                "--set",
                f"journey_branch_candidate_log_top_n={int(candidate_log_top_n)}",
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
            commands.append(command)

    output_dir.mkdir(parents=True, exist_ok=True)
    branch_rows.sort(key=lambda row: (str(row["instance"]), int(row["node_id"]), int(row["depth"])))
    child_rows.sort(
        key=lambda row: (
            str(row["instance"]),
            int(row["node_id"]),
            int(row["depth"]),
            -float(row["score"]),
        )
    )
    (output_dir / "journey_branch_tree_score_rows.json").write_text(
        json.dumps(branch_rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "journey_branch_tree_score_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in branch_rows),
        encoding="utf-8",
    )
    (output_dir / "journey_child_tree_score_rows.json").write_text(
        json.dumps(child_rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "journey_child_tree_score_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in child_rows),
        encoding="utf-8",
    )
    (output_dir / "commands.sh").write_text(
        "\n".join(shlex.join(command) for command in commands) + ("\n" if commands else ""),
        encoding="utf-8",
    )
    summary = {
        "schema_version": "journey_tree_replay_score_map_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "input_log_count": len(logs),
        "branch_score_row_count": len(branch_rows),
        "child_score_row_count": len(child_rows),
        "command_count": len(commands),
        "skipped_branch_event_count": int(skipped_branch_events),
        "skipped_child_event_count": int(skipped_child_events),
        "output_dir": str(output_dir),
        "branch_score_rows_path": str(output_dir / "journey_branch_tree_score_rows.json"),
        "child_score_rows_path": str(output_dir / "journey_child_tree_score_rows.json"),
        "commands_path": str(output_dir / "commands.sh"),
        "solver_branch_priority": "branch_score_horizon",
        "solver_child_priority_mode": "child_score",
        "time_limit": float(time_limit),
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
        "# Journey Tree Replay Score Map",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "从已成功的 Journey JSONL 日志导出 tree-level branch score 和 child score，用于 opt-in replay。该过程只读日志，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
    ]
    for key in [
        "input_log_count",
        "branch_score_row_count",
        "child_score_row_count",
        "command_count",
        "skipped_branch_event_count",
        "skipped_child_event_count",
        "solver_branch_priority",
        "solver_child_priority_mode",
        "branch_score_rows_path",
        "child_score_rows_path",
        "commands_path",
        "production_ready",
        "certificate_effect",
        "official_bound_effect",
    ]:
        lines.append(f"{key} = {summary.get(key)}")
    lines.extend(["```", "", "## Branch Rows Preview", ""])
    for row in branch_rows[:12]:
        lines.append(
            f"- node={row['node_id']} depth={row['depth']} pair={row['pair']} score={row['score']}"
        )
    lines.extend(["", "## Child Rows Preview", ""])
    for row in child_rows[:12]:
        lines.append(
            f"- node={row['node_id']} depth={row['depth']} pair={row['pair']} kind={row['child_constraint_kind']} score={row['score']}"
        )
    lines.extend(["", "## 使用边界", ""])
    lines.append(
        "`branch_score_horizon` 和 `child_score` 只改变 branch pair 与 child 入队顺序；它们不提供 bound，不剪枝，不替代 exact pricing closure。"
    )
    lines.append(
        "如果 replay 不能复现旧成功，说明旧成功依赖更广的 tree policy、不同列池轨迹或代码/配置漂移，不应把单个 pair/path 当作强正例。"
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--time-limit", type=float, default=600.0)
    parser.add_argument("--candidate-log-top-n", type=int, default=200)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = build_tree_replay_score_map(
        [Path(path) for path in args.logs],
        args.output_dir,
        args.report,
        config=args.config,
        time_limit=float(args.time_limit),
        candidate_log_top_n=int(args.candidate_log_top_n),
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
