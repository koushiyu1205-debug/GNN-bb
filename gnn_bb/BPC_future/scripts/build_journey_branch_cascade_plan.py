#!/usr/bin/env python3
"""Build a near-threshold Journey branch sampling cascade.

The cascade is an offline planning helper. It reads existing benchmark result
CSVs and optional JSONL logs, then emits the next cheap action for each
near-threshold context. It does not run BPC, pricing, RMP, or produce official
bounds/certificates.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
import json
from pathlib import Path
import re
import shlex
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_cascade_plan_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_journey_branch_cascade_plan_zh.md"
)
DEFAULT_CONFIG = Path("BPC_future/configs/moon_trek_20_smoke.yaml")
DEFAULT_INSTANCE_ROOT = Path("BPC_future/logical_graph")


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


def _safe_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")
    return slug[:160] or "context"


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


def _load_results(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                instance = str(row.get("instance") or "")
                if not instance:
                    continue
                rows.append(dict(row))
    return rows


def _load_log_index(
    log_paths: Iterable[Path],
    *,
    instance_root: Path,
) -> dict[str, dict[str, Any]]:
    by_instance: dict[str, dict[str, Any]] = {}
    for log_path in _iter_jsonl_paths(log_paths):
        instance = _instance_from_log_path(log_path, instance_root)
        if not instance:
            continue
        branch_events = 0
        root_branch_events = 0
        max_logged_candidates = 0
        for record in _iter_jsonl(log_path):
            if record.get("event") != "journey_branch_candidates":
                continue
            branch_events += 1
            if _int(record.get("depth"), -1) == 0:
                root_branch_events += 1
            max_logged_candidates = max(
                max_logged_candidates,
                _int(record.get("candidate_count"), 0),
                _int(record.get("logged_top_count"), 0),
            )
        if branch_events <= 0:
            continue
        current = by_instance.get(instance)
        candidate = {
            "log_path": str(log_path),
            "branch_candidate_event_count": branch_events,
            "root_branch_candidate_event_count": root_branch_events,
            "max_logged_candidate_count": max_logged_candidates,
        }
        if current is None or root_branch_events > int(
            current.get("root_branch_candidate_event_count", 0)
        ):
            by_instance[instance] = candidate
    return by_instance


def _shell_join(items: list[str]) -> str:
    return " ".join(shlex.quote(str(item)) for item in items)


def _diag_command(
    *,
    python: str,
    config: Path,
    instance: str,
    time_limit: int,
    output_dir: Path,
    slug: str,
    max_workers: int,
) -> str:
    return _shell_join(
        [
            python,
            "BPC_future/scripts/run_bpc_future_external_timeout_batch.py",
            "--config",
            str(config),
            "--instances",
            instance,
            "--time-limit",
            str(int(time_limit)),
            "--results-csv",
            str(output_dir / "diag_runs" / slug / "results.csv"),
            "--log-dir",
            str(output_dir / "diag_runs" / slug / "logs"),
            "--solution-dir",
            str(output_dir / "diag_runs" / slug / "solutions"),
            "--run-log-dir",
            str(output_dir / "diag_runs" / slug / "run_logs"),
            "--python",
            python,
            "--timeout-kill-after",
            "30s",
            "--max-workers",
            str(int(max_workers)),
            "--quiet",
            "--set",
            "journey_branch_candidate_log_top_n=200",
        ]
    )


def _child_probe_runbook_command(
    *,
    python: str,
    config: Path,
    log_path: str,
    output_dir: Path,
    slug: str,
    time_limit: int,
    alt_pairs_per_event: int,
    max_source_depth: int,
    probe_extra_nodes_after_branch: int,
) -> str:
    return _shell_join(
        [
            python,
            "BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py",
            log_path,
            "--config",
            str(config),
            "--time-limit",
            str(int(time_limit)),
            "--candidate-selection",
            "layered",
            "--candidate-source",
            "both",
            "--alt-pairs-per-event",
            str(int(alt_pairs_per_event)),
            "--candidate-log-top-n",
            "200",
            "--max-source-depth",
            str(int(max_source_depth)),
            "--probe-mode",
            "child_probe",
            "--probe-extra-nodes-after-branch",
            str(int(probe_extra_nodes_after_branch)),
            "--output-dir",
            str(output_dir / "child_probe_runbooks" / slug),
            "--report",
            str(output_dir / "child_probe_runbooks" / slug / "report.md"),
        ]
    )


def build_cascade_plan(
    result_paths: list[Path],
    output_dir: Path,
    report: Path,
    *,
    log_paths: list[Path] | None = None,
    target_wall: float = 200.0,
    near_threshold_max_wall: float = 360.0,
    max_contexts: int = 12,
    config: Path = DEFAULT_CONFIG,
    instance_root: Path = DEFAULT_INSTANCE_ROOT,
    diagnostic_time_limit: int = 260,
    child_probe_time_limit: int = 90,
    alt_pairs_per_event: int = 4,
    max_source_depth: int = 0,
    probe_extra_nodes_after_branch: int = 2,
    python: str = "python3",
    max_workers: int = 1,
) -> dict[str, Any]:
    log_index = _load_log_index(log_paths or [], instance_root=instance_root)
    rows: list[dict[str, Any]] = []
    for result_row in _load_results(result_paths):
        instance = str(result_row.get("instance") or "")
        status = str(result_row.get("status") or "")
        wall = _float(result_row.get("wall_time") or result_row.get("solving_time"))
        if status != "OPTIMAL":
            continue
        if wall <= float(target_wall) or wall > float(near_threshold_max_wall):
            continue
        family = _time_window_family(instance)
        terrain = _terrain(instance)
        seed = _seed(instance)
        slug = _safe_slug(Path(instance).stem)
        log_info = log_index.get(instance)
        if log_info is None:
            action = "COLLECT_TOP200_DIAG_LOG"
            command = _diag_command(
                python=python,
                config=config,
                instance=instance,
                time_limit=diagnostic_time_limit,
                output_dir=output_dir,
                slug=slug,
                max_workers=max_workers,
            )
        else:
            action = "BUILD_CHILD_PROBE_RUNBOOK"
            command = _child_probe_runbook_command(
                python=python,
                config=config,
                log_path=str(log_info["log_path"]),
                output_dir=output_dir,
                slug=slug,
                time_limit=child_probe_time_limit,
                alt_pairs_per_event=alt_pairs_per_event,
                max_source_depth=max_source_depth,
                probe_extra_nodes_after_branch=probe_extra_nodes_after_branch,
            )
        rows.append(
            {
                "schema_version": "journey_branch_cascade_context_v1",
                "diagnostic_only": True,
                "runs_bpc_or_pricing": False,
                "production_ready": False,
                "certificate_effect": False,
                "official_bound_effect": False,
                "instance": instance,
                "status": status,
                "wall_time": round(wall, 9),
                "target_wall": float(target_wall),
                "wall_over_target": round(wall - float(target_wall), 9),
                "time_window_family": family,
                "terrain": terrain,
                "seed": seed,
                "node_count": _int(result_row.get("node_count"), 0),
                "pricing_calls": _int(result_row.get("pricing_calls"), 0),
                "exact_pricing_calls": _int(result_row.get("exact_pricing_calls"), 0),
                "has_candidate_log": log_info is not None,
                "candidate_log_path": None if log_info is None else log_info.get("log_path"),
                "branch_candidate_event_count": 0
                if log_info is None
                else log_info.get("branch_candidate_event_count", 0),
                "root_branch_candidate_event_count": 0
                if log_info is None
                else log_info.get("root_branch_candidate_event_count", 0),
                "recommended_action": action,
                "recommended_command": command,
                "priority_reason": (
                    "near_threshold_optimal;prefer_child_probe_before_full_replay"
                    if log_info is not None
                    else "near_threshold_optimal;missing_candidate_log"
                ),
            }
        )
    rows.sort(key=lambda row: (float(row["wall_over_target"]), str(row["instance"])))
    if int(max_contexts) > 0:
        rows = rows[: int(max_contexts)]

    output_dir.mkdir(parents=True, exist_ok=True)
    contexts_path = output_dir / "cascade_context_rows.jsonl"
    contexts_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    commands_path = output_dir / "commands.sh"
    commands_path.write_text(
        "\n".join(str(row["recommended_command"]) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )
    action_counts: dict[str, int] = {}
    family_counts: dict[str, int] = {}
    for row in rows:
        action_counts[str(row["recommended_action"])] = action_counts.get(
            str(row["recommended_action"]), 0
        ) + 1
        family = str(row.get("time_window_family") or "")
        family_counts[family] = family_counts.get(family, 0) + 1
    summary = {
        "schema_version": "journey_branch_cascade_plan_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "result_paths": [str(path) for path in result_paths],
        "log_paths": [str(path) for path in (log_paths or [])],
        "output_dir": str(output_dir),
        "target_wall": float(target_wall),
        "near_threshold_max_wall": float(near_threshold_max_wall),
        "context_count": len(rows),
        "action_counts": dict(sorted(action_counts.items())),
        "time_window_family_counts": dict(sorted(family_counts.items())),
        "commands_path": str(commands_path),
        "contexts_path": str(contexts_path),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    _write_report(report, summary, rows)
    return dict(summary, rows=rows)


def _write_report(report: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Branch Cascade Plan",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "从 canonical benchmark 结果中筛选 near-threshold OPTIMAL 实例，优先生成便宜的 child-probe / limited-strong-branching 计划，避免用完整 forced replay 盲扫正例。",
        "",
        "## 机器字段",
        "",
        "```text",
    ]
    for key in [
        "context_count",
        "target_wall",
        "near_threshold_max_wall",
        "action_counts",
        "time_window_family_counts",
        "runs_bpc_or_pricing",
        "official_bound_effect",
        "certificate_effect",
        "production_ready",
    ]:
        lines.append(f"{key} = {summary.get(key)}")
    lines.extend(["```", "", "## 推荐 context", ""])
    for row in rows[:20]:
        lines.append(
            "- "
            f"{row['time_window_family']}/{row['terrain']} seed={row['seed']} "
            f"wall={row['wall_time']} over={row['wall_over_target']} "
            f"action={row['recommended_action']} "
            f"root_events={row['root_branch_candidate_event_count']}"
        )
    lines.extend(["", "## 边界", ""])
    lines.append(
        "该计划只生成下一步采样命令，不运行 solver，不产生 official bound/certificate，也不能作为性能达标证据。"
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-csv", nargs="+", type=Path, required=True)
    parser.add_argument("--log-path", nargs="*", type=Path, default=[])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--target-wall", type=float, default=200.0)
    parser.add_argument("--near-threshold-max-wall", type=float, default=360.0)
    parser.add_argument("--max-contexts", type=int, default=12)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--instance-root", type=Path, default=DEFAULT_INSTANCE_ROOT)
    parser.add_argument("--diagnostic-time-limit", type=int, default=260)
    parser.add_argument("--child-probe-time-limit", type=int, default=90)
    parser.add_argument("--alt-pairs-per-event", type=int, default=4)
    parser.add_argument("--max-source-depth", type=int, default=0)
    parser.add_argument("--probe-extra-nodes-after-branch", type=int, default=2)
    parser.add_argument("--python", default="python3")
    parser.add_argument("--max-workers", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = build_cascade_plan(
        list(args.results_csv),
        args.output_dir,
        args.report,
        log_paths=list(args.log_path),
        target_wall=args.target_wall,
        near_threshold_max_wall=args.near_threshold_max_wall,
        max_contexts=args.max_contexts,
        config=args.config,
        instance_root=args.instance_root,
        diagnostic_time_limit=args.diagnostic_time_limit,
        child_probe_time_limit=args.child_probe_time_limit,
        alt_pairs_per_event=args.alt_pairs_per_event,
        max_source_depth=args.max_source_depth,
        probe_extra_nodes_after_branch=args.probe_extra_nodes_after_branch,
        python=args.python,
        max_workers=args.max_workers,
    )
    printable = {key: value for key, value in summary.items() if key != "rows"}
    print(json.dumps(printable, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
