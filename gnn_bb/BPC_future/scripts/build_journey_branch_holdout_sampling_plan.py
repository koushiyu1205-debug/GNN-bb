#!/usr/bin/env python3
"""Build a holdout-oriented Journey branch sampling plan.

This is an offline planning helper. It reads canonical benchmark result CSVs,
known counterfactual labels, and optional JSONL logs, then recommends the next
cheap sampling action for contexts that could add strict branch positives or
holdout coverage. It does not run BPC, pricing, RMP, or produce official
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


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_holdout_sampling_plan_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_journey_branch_holdout_sampling_plan_zh.md"
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
    return slug[:180] or "instance"


def _shell_join(items: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(item)) for item in items)


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
                if instance:
                    rows.append(dict(row))
    return rows


def _is_target_wall_positive(row: dict[str, Any], *, target_wall: float) -> bool:
    if row.get("alternative_forced_pair_matched") is False:
        return False
    if bool(row.get("right_censored_counterfactual")):
        return False
    return bool(
        str(row.get("alternative_status") or "") == "OPTIMAL"
        and _float(row.get("alternative_wall_time")) <= float(target_wall)
        and _float(row.get("baseline_wall_time")) > float(target_wall)
    )


def _known_positive_contexts(
    paths: Iterable[Path],
    *,
    target_wall: float,
) -> tuple[set[str], set[str], set[str], set[str]]:
    strict_instances: set[str] = set()
    strict_families: set[str] = set()
    target_instances: set[str] = set()
    target_families: set[str] = set()
    for path in paths:
        row_path = path
        if path.is_dir():
            row_path = path / "branch_counterfactual_delta_rows.jsonl"
        if not row_path.exists():
            continue
        for row in _iter_jsonl(row_path):
            if str(row.get("counterfactual_label_type") or "") != "strong_positive":
                continue
            instance = str(row.get("instance") or "")
            if not instance:
                continue
            strict_instances.add(instance)
            family = _time_window_family(instance)
            if family:
                strict_families.add(family)
            if _is_target_wall_positive(row, target_wall=target_wall):
                target_instances.add(instance)
                if family:
                    target_families.add(family)
    return strict_instances, strict_families, target_instances, target_families


def _instance_from_log_path(log_path: Path, instance_root: Path) -> str | None:
    text = str(log_path)
    marker = "BPC_future/logical_graph/"
    if marker in text:
        instance = marker + text.split(marker, 1)[1]
        if instance.endswith(".jsonl"):
            instance = instance[: -len(".jsonl")]
        return instance
    stem = log_path.name
    if stem.endswith(".jsonl"):
        stem = stem[: -len(".jsonl")]
    matches = sorted(instance_root.rglob(stem))
    return str(matches[0]) if matches else None


def _load_log_index(paths: Iterable[Path], *, instance_root: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for log_path in _iter_jsonl_paths(paths):
        instance = _instance_from_log_path(log_path, instance_root)
        if not instance:
            continue
        candidate_events = 0
        root_candidate_events = 0
        branch_events = 0
        max_logged = 0
        max_candidate_count = 0
        cg_iterations_before_first_branch = 0
        pricing_events_before_first_branch = 0
        seen_branch_signal = False
        for record in _iter_jsonl(log_path):
            event = record.get("event")
            if event == "journey_pricing" and not seen_branch_signal:
                pricing_events_before_first_branch += 1
                cg_iterations_before_first_branch = max(
                    cg_iterations_before_first_branch,
                    _int(record.get("cg_iter"), pricing_events_before_first_branch),
                    pricing_events_before_first_branch,
                )
            if event in {"journey_branch_candidates", "journey_branch"}:
                seen_branch_signal = True
            if event == "journey_branch":
                branch_events += 1
            if event != "journey_branch_candidates":
                continue
            candidate_events += 1
            if _int(record.get("depth"), -1) == 0:
                root_candidate_events += 1
            max_logged = max(
                max_logged,
                _int(record.get("logged_top_count"), 0),
                len(record.get("priority_top") or []),
                len(record.get("top") or []),
            )
            max_candidate_count = max(max_candidate_count, _int(record.get("candidate_count"), 0))
        current = index.get(instance)
        payload = {
            "log_path": str(log_path),
            "branch_candidate_event_count": candidate_events,
            "root_branch_candidate_event_count": root_candidate_events,
            "branch_event_count": branch_events,
            "max_logged_candidate_count": max_logged,
            "max_candidate_count": max_candidate_count,
            "cg_iterations_before_first_branch": cg_iterations_before_first_branch,
            "pricing_events_before_first_branch": pricing_events_before_first_branch,
        }
        if current is None or candidate_events > int(current.get("branch_candidate_event_count", 0)):
            index[instance] = payload
    return index


def _diag_command(
    *,
    python: str,
    config: Path,
    instance: str,
    time_limit: int,
    output_dir: Path,
    candidate_log_top_n: int,
) -> str:
    slug = _safe_slug(Path(instance).stem)
    result_dir = output_dir / "diag_runs" / slug
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
            str(result_dir / "results.csv"),
            "--log-dir",
            str(result_dir / "logs"),
            "--solution-dir",
            str(result_dir / "solutions"),
            "--run-log-dir",
            str(result_dir / "run_logs"),
            "--python",
            python,
            "--timeout-kill-after",
            "30s",
            "--max-workers",
            "1",
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
    candidate_log_top_n: int,
    time_limit: int,
    probe_max_cg_iterations: int,
) -> str:
    return _shell_join(
        [
            python,
            "BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py",
            log_path,
            "--output-dir",
            str(output_dir),
            "--report",
            str(output_dir / "runbook_report.md"),
            "--config",
            str(config),
            "--time-limit",
            str(int(time_limit)),
            "--limit",
            "8",
            "--alt-pairs-per-event",
            "4",
            "--candidate-selection",
            "layered",
            "--candidate-log-top-n",
            str(int(candidate_log_top_n)),
            "--probe-mode",
            "child_probe",
            "--probe-max-cg-iterations",
            str(int(probe_max_cg_iterations)),
            "--max-source-depth",
            "0",
        ]
    )


def _probe_cg_iterations_from_log(log_payload: dict[str, Any] | None) -> int:
    if not log_payload:
        return 20
    before_branch = _int(log_payload.get("cg_iterations_before_first_branch"), 0)
    # Add a small margin so replay reaches the candidate/branch event even when
    # forced-pair ordering changes the local CG sequence slightly.
    return min(80, max(20, before_branch + 8))


def _action_for_row(
    *,
    row: dict[str, Any],
    known_target200_instances: set[str],
    log_payload: dict[str, Any] | None,
    target_wall: float,
    near_wall: float,
) -> tuple[str, str]:
    instance = str(row.get("instance") or "")
    if instance in known_target200_instances:
        return "ALREADY_HAS_TARGET200_POSITIVE", "instance_already_has_target_200_positive"
    status = str(row.get("status") or "")
    wall = _float(row.get("wall_time"), 0.0)
    node_count = _int(row.get("node_count"), 0)
    if status != "OPTIMAL":
        return "DEFER_NONOPTIMAL_CONTEXT", "full600_not_optimal"
    if wall <= float(target_wall):
        return "SKIP_ALREADY_WITHIN_TARGET", "wall_already_within_target"
    has_candidates = bool(log_payload and int(log_payload.get("branch_candidate_event_count", 0)) > 0)
    has_branch_events = bool(log_payload and int(log_payload.get("branch_event_count", 0)) > 0)
    if has_candidates and node_count > 1:
        return "BUILD_CHILD_PROBE_RUNBOOK", "candidate_log_available"
    if log_payload is not None and not has_candidates and not has_branch_events:
        if node_count <= 1:
            return "ROUTE_TO_ROOT_PRICING_TAIL", "top200_log_has_no_branch_events_root_tail"
        return "ROUTE_TO_PRICING_TAIL", "top200_log_has_no_branch_events"
    if node_count <= 1:
        return "COLLECT_ROOT_TAIL_TOP200_DIAG_LOG", "near_threshold_root_tail_no_branch_candidates"
    if wall <= float(near_wall):
        return "COLLECT_TOP200_DIAG_LOG", "near_threshold_missing_candidate_log"
    return "COLLECT_LONG_TOP200_DIAG_LOG", "slow_optimal_missing_candidate_log"


def _priority_score(
    *,
    row: dict[str, Any],
    action: str,
    known_target200_families: set[str],
    target_wall: float,
    near_wall: float,
) -> float:
    instance = str(row.get("instance") or "")
    wall = _float(row.get("wall_time"), 0.0)
    node_count = _int(row.get("node_count"), 0)
    family = _time_window_family(instance)
    score = 0.0
    if action in {"COLLECT_TOP200_DIAG_LOG", "BUILD_CHILD_PROBE_RUNBOOK"}:
        score += 100.0
    if action == "COLLECT_LONG_TOP200_DIAG_LOG":
        score += 80.0
    if action == "COLLECT_ROOT_TAIL_TOP200_DIAG_LOG":
        score += 60.0
    if action in {"ROUTE_TO_ROOT_PRICING_TAIL", "ROUTE_TO_PRICING_TAIL"}:
        score += 5.0
    if wall > float(target_wall):
        score += max(0.0, 40.0 - abs(wall - float(near_wall)) / 10.0)
    if node_count > 1:
        score += min(20.0, float(node_count))
    if family and family not in known_target200_families:
        score += 15.0
    return round(score, 6)


def build_holdout_sampling_plan(
    *,
    results_csv: list[Path],
    output_dir: Path,
    report: Path,
    positive_inputs: list[Path] | None = None,
    log_paths: list[Path] | None = None,
    config: Path = DEFAULT_CONFIG,
    instance_root: Path = DEFAULT_INSTANCE_ROOT,
    target_wall: float = 200.0,
    near_wall: float = 360.0,
    time_limit: int = 600,
    candidate_log_top_n: int = 200,
    limit: int = 12,
    python: str = "/home/kai/miniconda3/bin/python",
) -> dict[str, Any]:
    results = _load_results(results_csv)
    (
        known_strict_positive_instances,
        known_strict_positive_families,
        known_target200_positive_instances,
        known_target200_positive_families,
    ) = _known_positive_contexts(positive_inputs or [], target_wall=target_wall)
    log_index = _load_log_index(log_paths or [], instance_root=instance_root)
    rows: list[dict[str, Any]] = []
    for result in results:
        instance = str(result.get("instance") or "")
        if not instance or "tasks_020" not in instance:
            continue
        wall = _float(result.get("wall_time"), 0.0)
        if wall <= float(target_wall):
            continue
        log_payload = log_index.get(instance)
        action, reason = _action_for_row(
            row=result,
            known_target200_instances=known_target200_positive_instances,
            log_payload=log_payload,
            target_wall=target_wall,
            near_wall=near_wall,
        )
        command = ""
        if action in {"COLLECT_TOP200_DIAG_LOG", "COLLECT_ROOT_TAIL_TOP200_DIAG_LOG", "COLLECT_LONG_TOP200_DIAG_LOG"}:
            command = _diag_command(
                python=python,
                config=config,
                instance=instance,
                time_limit=time_limit,
                output_dir=output_dir,
                candidate_log_top_n=candidate_log_top_n,
            )
        elif action == "BUILD_CHILD_PROBE_RUNBOOK" and log_payload is not None:
            command = _child_probe_command(
                python=python,
                config=config,
                log_path=str(log_payload.get("log_path") or ""),
                output_dir=output_dir / "child_probe_runbooks" / _safe_slug(Path(instance).stem),
                candidate_log_top_n=candidate_log_top_n,
                time_limit=min(int(time_limit), 180),
                probe_max_cg_iterations=_probe_cg_iterations_from_log(log_payload),
            )
        row = {
            "schema_version": "journey_branch_holdout_sampling_row_v1",
            "instance": instance,
            "status": result.get("status"),
            "wall_time": wall,
            "node_count": _int(result.get("node_count"), 0),
            "exact_pricing_calls": _int(result.get("exact_pricing_calls"), 0),
            "time_window_family": _time_window_family(instance),
            "terrain": _terrain(instance),
            "seed": _seed(instance),
            "known_strict_positive_instance": instance in known_strict_positive_instances,
            "known_target200_positive_instance": instance in known_target200_positive_instances,
            "family_has_strict_positive": _time_window_family(instance)
            in known_strict_positive_families,
            "family_has_target200_positive": _time_window_family(instance)
            in known_target200_positive_families,
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
            "cg_iterations_before_first_branch": 0
            if log_payload is None
            else int(log_payload.get("cg_iterations_before_first_branch", 0)),
            "probe_max_cg_iterations": 0
            if log_payload is None
            else _probe_cg_iterations_from_log(log_payload),
            "recommended_action": action,
            "recommended_reason": reason,
            "priority_score": _priority_score(
                row=result,
                action=action,
                known_target200_families=known_target200_positive_families,
                target_wall=target_wall,
                near_wall=near_wall,
            ),
            "recommended_command": command,
            "diagnostic_only": True,
            "runs_bpc_or_pricing": False,
            "official_bound_effect": False,
            "certificate_effect": False,
        }
        rows.append(row)
    rows.sort(key=lambda item: (-float(item["priority_score"]), float(item["wall_time"]), item["instance"]))
    actionable_rows = [row for row in rows if row.get("recommended_command")]
    selected = actionable_rows[: max(0, int(limit))]
    all_action_counts: dict[str, int] = {}
    selected_action_counts: dict[str, int] = {}
    for row in rows:
        all_action_counts[str(row["recommended_action"])] = all_action_counts.get(
            str(row["recommended_action"]), 0
        ) + 1
    for row in selected:
        selected_action_counts[str(row["recommended_action"])] = selected_action_counts.get(
            str(row["recommended_action"]), 0
        ) + 1
    summary = {
        "schema_version": "journey_branch_holdout_sampling_plan_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "production_ready": False,
        "results_csv": [str(path) for path in results_csv],
        "positive_inputs": [str(path) for path in (positive_inputs or [])],
        "log_paths": [str(path) for path in (log_paths or [])],
        "output_dir": str(output_dir),
        "target_wall": float(target_wall),
        "near_wall": float(near_wall),
        "candidate_log_top_n": int(candidate_log_top_n),
        "known_strict_positive_instance_count": len(known_strict_positive_instances),
        "known_strict_positive_family_count": len(known_strict_positive_families),
        "known_target200_positive_instance_count": len(known_target200_positive_instances),
        "known_target200_positive_family_count": len(known_target200_positive_families),
        "candidate_context_count": len(rows),
        "actionable_context_count": len(actionable_rows),
        "selected_context_count": len(selected),
        "action_counts": selected_action_counts,
        "all_action_counts": all_action_counts,
        "rows": selected,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "holdout_sampling_all_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    (output_dir / "holdout_sampling_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in selected),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    commands = ["#!/usr/bin/env bash", "set -euo pipefail", ""]
    for index, row in enumerate(selected, start=1):
        if not row.get("recommended_command"):
            continue
        commands.append(f"# {index:03d} {row['recommended_action']} {row['instance']}")
        commands.append(str(row["recommended_command"]))
        commands.append("")
    (output_dir / "commands.sh").write_text("\n".join(commands), encoding="utf-8")
    _write_report(summary, report)
    return summary


def _write_report(summary: dict[str, Any], report: Path) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Branch Holdout Sampling Plan",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "该计划只读 benchmark / label / log 文件，生成下一批 holdout-oriented 采样建议；不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。",
        "",
        "## Machine Fields",
        "",
        "```text",
        f"candidate_context_count = {summary['candidate_context_count']}",
        f"actionable_context_count = {summary['actionable_context_count']}",
        f"selected_context_count = {summary['selected_context_count']}",
        f"known_strict_positive_instance_count = {summary['known_strict_positive_instance_count']}",
        f"known_strict_positive_family_count = {summary['known_strict_positive_family_count']}",
        f"known_target200_positive_instance_count = {summary['known_target200_positive_instance_count']}",
        f"known_target200_positive_family_count = {summary['known_target200_positive_family_count']}",
        f"candidate_log_top_n = {summary['candidate_log_top_n']}",
        f"selected_action_counts = {summary['action_counts']}",
        f"all_action_counts = {summary['all_action_counts']}",
        "official_bound_effect = false",
        "certificate_effect = false",
        "```",
        "",
        "## Rows",
        "",
    ]
    for row in summary["rows"]:
        lines.append(
            "- "
            f"action={row['recommended_action']}, reason={row['recommended_reason']}, "
            f"priority={row['priority_score']}, wall={row['wall_time']}, "
            f"nodes={row['node_count']}, family={row['time_window_family']}, "
            f"seed={row['seed']}, known_strict={row['known_strict_positive_instance']}, "
            f"known_target200={row['known_target200_positive_instance']}, "
            f"candidates={row['branch_candidate_event_count']}, "
            f"branch_events={row['branch_event_count']}, "
            f"cg_before_branch={row['cg_iterations_before_first_branch']}, "
            f"probe_cg={row['probe_max_cg_iterations']}, "
            f"instance={Path(row['instance']).name}"
        )
    lines.extend(["", "## 边界", ""])
    lines.append(
        "该计划用于减少盲扫；只有已产生 target-200 positive 的实例会被视为覆盖完成，"
        "普通 strict positive 但未进入 200 秒的实例仍会继续采样。推荐命令仍需实际运行并"
        "通过 strict counterfactual delta 才能产生训练正例。"
    )
    lines.append(
        "`ROUTE_TO_ROOT_PRICING_TAIL` / `ROUTE_TO_PRICING_TAIL` 表示已有日志显示没有可采 branch event，"
        "该实例应转到 pricing/final-probe/Tail Action Controller 线，不应继续生成 branch-pair replay。"
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-csv", action="append", required=True)
    parser.add_argument("--positive-input", action="append", default=[])
    parser.add_argument("--log", action="append", default=[])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--instance-root", type=Path, default=DEFAULT_INSTANCE_ROOT)
    parser.add_argument("--target-wall", type=float, default=200.0)
    parser.add_argument("--near-wall", type=float, default=360.0)
    parser.add_argument("--time-limit", type=int, default=600)
    parser.add_argument("--candidate-log-top-n", type=int, default=200)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--python", default="/home/kai/miniconda3/bin/python")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    build_holdout_sampling_plan(
        results_csv=[Path(path) for path in args.results_csv],
        output_dir=args.output_dir,
        report=args.report,
        positive_inputs=[Path(path) for path in args.positive_input],
        log_paths=[Path(path) for path in args.log],
        config=args.config,
        instance_root=args.instance_root,
        target_wall=args.target_wall,
        near_wall=args.near_wall,
        time_limit=args.time_limit,
        candidate_log_top_n=args.candidate_log_top_n,
        limit=args.limit,
        python=args.python,
    )


if __name__ == "__main__":
    main()
