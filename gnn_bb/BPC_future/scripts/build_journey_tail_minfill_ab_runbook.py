#!/usr/bin/env python3
"""Build paired A/B runbooks for Journey tail low-min-fill candidates.

The script reads diagnostic completion-tail profile summaries and emits paired
baseline/opt-in commands for candidates where low min-fill was structurally
eligible but disabled.  It only writes a runbook; it does not run BPC, pricing,
RMP, or produce certificates.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import shlex
from collections import Counter
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_tail_minfill_ab_runbook_20260625")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260625_bpc_future_journey_tail_minfill_ab_runbook_zh.md"
)
DEFAULT_CONFIG = Path("BPC_future/configs/moon_trek_20_smoke.yaml")


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
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def _summary_file(path: Path) -> Path:
    if path.is_dir():
        return path / "summary.json"
    return path


def _load_records(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        payload = _read_json(_summary_file(Path(path)))
        records = payload.get("records")
        if isinstance(records, list):
            rows.extend(row for row in records if isinstance(row, dict))
    return rows


def _tail_action_class_from_action(action: Any) -> str:
    return {
        "FRONTIER_REFINEMENT": "A_FRONTIER_REFINEMENT",
        "BROAD_PLATEAU_FALLBACK": "B_BROAD_PLATEAU",
        "CONTINUE_COLUMN_GENERATION": "C_CONTINUE_CG",
        "EARLY_BRANCH": "D_EARLY_BRANCH",
    }.get(str(action or ""), "UNKNOWN")


def _tail_action_class(row: dict[str, Any]) -> str:
    raw = str(row.get("tail_action_class") or "")
    return raw if raw else _tail_action_class_from_action(row.get("tail_action"))


def _tail_action_productivity_class(row: dict[str, Any]) -> str:
    return str(row.get("tail_action_productivity_class") or "unknown")


def _load_tail_action_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        path = Path(path)
        if path.is_dir():
            for name in (
                "tail_action_rows.jsonl",
                "no_column_gate_rows.jsonl",
                "early_branch_trigger_rows.jsonl",
            ):
                rows.extend(_iter_jsonl(path / name))
            continue
        if path.name == "summary.json":
            parent = path.parent
            for name in (
                "tail_action_rows.jsonl",
                "no_column_gate_rows.jsonl",
                "early_branch_trigger_rows.jsonl",
            ):
                rows.extend(_iter_jsonl(parent / name))
            continue
        if path.suffix == ".jsonl":
            rows.extend(_iter_jsonl(path))
            continue
        payload = _read_json(path)
        for key in ("rows", "sample_rows", "sample_no_column_gate_rows", "sample_early_branch_rows"):
            raw_rows = payload.get(key)
            if isinstance(raw_rows, list):
                rows.extend(row for row in raw_rows if isinstance(row, dict))
    return rows


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


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _safe_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")
    return slug[:180] or "instance"


def _shell_join(items: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(item)) for item in items)


def _instance_from_log_file(log_file: Any) -> str | None:
    text = str(log_file or "")
    marker = "BPC_future/logical_graph/"
    if marker in text:
        instance = marker + text.split(marker, 1)[1]
        if instance.endswith(".jsonl"):
            instance = instance[: -len(".jsonl")]
        return instance or None
    return None


def _instance_from_record(row: dict[str, Any]) -> str | None:
    for key in ("instance", "instance_path"):
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return _instance_from_log_file(row.get("log_file"))


def _tail_action_match_keys(row: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    instance = _instance_from_record(row)
    if instance:
        keys.add(f"instance:{instance}")
    log_file = str(row.get("log_file") or "")
    if log_file:
        keys.add(f"log:{log_file}")
    return keys


def _tail_action_filter_index(
    rows: Iterable[dict[str, Any]],
    *,
    required_classes: set[str],
    required_productivity_classes: set[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, int], dict[str, int]]:
    index: dict[str, dict[str, Any]] = {}
    class_counts: Counter[str] = Counter()
    productivity_counts: Counter[str] = Counter()
    for row in rows:
        action_class = _tail_action_class(row)
        productivity_class = _tail_action_productivity_class(row)
        class_counts[action_class] += 1
        productivity_counts[productivity_class] += 1
        if required_classes and action_class not in required_classes:
            continue
        if required_productivity_classes and productivity_class not in required_productivity_classes:
            continue
        for key in _tail_action_match_keys(row):
            entry = index.setdefault(
                key,
                {
                    "matched_tail_action_count": 0,
                    "tail_action_class_counts": Counter(),
                    "tail_action_productivity_class_counts": Counter(),
                },
            )
            entry["matched_tail_action_count"] = int(entry["matched_tail_action_count"]) + 1
            entry["tail_action_class_counts"][action_class] += 1
            entry["tail_action_productivity_class_counts"][productivity_class] += 1
    materialized: dict[str, dict[str, Any]] = {}
    for key, entry in index.items():
        materialized[key] = {
            "matched_tail_action_count": int(entry["matched_tail_action_count"]),
            "tail_action_class_counts": dict(sorted(entry["tail_action_class_counts"].items())),
            "tail_action_productivity_class_counts": dict(
                sorted(entry["tail_action_productivity_class_counts"].items())
            ),
        }
    return materialized, dict(sorted(class_counts.items())), dict(sorted(productivity_counts.items()))


def _tail_action_filter_match(
    row: dict[str, Any],
    index: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    for key in sorted(_tail_action_match_keys(row)):
        if key in index:
            return index[key]
    return None


def _tail_min_fill_last(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("completion_retry_tail_min_fill_last")
    return value if isinstance(value, dict) else {}


def _is_tail_min_fill_candidate(row: dict[str, Any]) -> bool:
    if _int(row.get("completion_retry_tail_min_fill_candidate_count")) > 0:
        return True
    return _bool(
        _tail_min_fill_last(row).get("completion_bound_diverse_harvest_tail_min_fill_candidate")
    )


def _is_optin_disabled_candidate(row: dict[str, Any]) -> bool:
    if _int(row.get("completion_retry_tail_min_fill_optin_disabled_count")) > 0:
        return True
    return (
        str(
            _tail_min_fill_last(row).get(
                "completion_bound_diverse_harvest_tail_min_fill_reason",
                "",
            )
        )
        == "optin_disabled"
    )


def _candidate_priority(row: dict[str, Any]) -> tuple[int, int, int, float, str]:
    completion_class = str(row.get("completion_retry_class") or "")
    class_rank = {
        "completion_bound_time_limit_no_column_uncertified": 0,
        "completion_bound_incomplete_time_limit": 1,
        "completion_bound_found_negative": 2,
        "completion_bound_certified_no_negative": 3,
        "no_completion_bound_retry": 4,
    }.get(completion_class, 5)
    status = str(row.get("finish_status") or "")
    status_rank = 0 if status in {"TIME_LIMIT", "EXTERNAL_TIME_LIMIT"} else 1
    candidate_count = _int(row.get("completion_retry_tail_min_fill_candidate_count"))
    solving_time = _float(row.get("finish_solving_time"))
    return (class_rank, status_rank, -candidate_count, -solving_time, str(row.get("log_file") or ""))


def _is_source_target_optimal(row: dict[str, Any], *, target_wall: float) -> bool:
    status = str(row.get("finish_status") or "")
    solving_time = _float(row.get("finish_solving_time"), default=-1.0)
    return status == "OPTIMAL" and 0.0 <= solving_time <= float(target_wall)


def _select_candidates(
    rows: Iterable[dict[str, Any]],
    *,
    limit: int,
    tail_action_filter_index: dict[str, dict[str, Any]] | None = None,
    require_source_outside_target_wall: bool = False,
    target_wall: float = 200.0,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    by_instance: dict[str, dict[str, Any]] = {}
    stats = Counter()
    for row in rows:
        if not _is_tail_min_fill_candidate(row):
            stats["skip_not_tail_min_fill_candidate"] += 1
            continue
        if not _is_optin_disabled_candidate(row):
            stats["skip_not_optin_disabled_candidate"] += 1
            continue
        if require_source_outside_target_wall and _is_source_target_optimal(
            row,
            target_wall=target_wall,
        ):
            stats["skip_source_target_optimal"] += 1
            continue
        instance = _instance_from_record(row)
        if not instance:
            stats["skip_missing_instance"] += 1
            continue
        tail_action_match = None
        if tail_action_filter_index is not None:
            tail_action_match = _tail_action_filter_match(row, tail_action_filter_index)
            if tail_action_match is None:
                stats["skip_tail_action_filter_no_match"] += 1
                continue
        candidate = {**row, "instance": instance}
        if tail_action_match is not None:
            candidate["tail_action_filter_match"] = tail_action_match
        current = by_instance.get(instance)
        if current is None or _candidate_priority(candidate) < _candidate_priority(current):
            by_instance[instance] = candidate
        else:
            stats["skip_deduplicated_lower_priority"] += 1
    selected = sorted(by_instance.values(), key=_candidate_priority)
    stats["candidate_instance_count_before_limit"] = len(selected)
    return selected[: max(0, int(limit))], dict(sorted(stats.items()))


def _command(
    *,
    config: Path,
    instance: str,
    profile: str,
    result_dir: Path,
    time_limit: int,
    python: str,
    max_workers: int,
    timeout_kill_after: str,
    tail_min_fill_enabled: bool,
    tail_min_fill: int,
    max_depth: int,
    final_probe_only: bool,
) -> list[str]:
    command = [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        python,
        "BPC_future/scripts/run_bpc_future_external_timeout_batch.py",
        "--config",
        str(config),
        "--instances",
        str(instance),
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
        str(python),
        "--timeout-kill-after",
        str(timeout_kill_after),
        "--max-workers",
        str(int(max_workers)),
        "--quiet",
        "--set",
        "journey_tail_action_audit_enabled=True",
        "--set",
        "journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True",
        "--set",
        f"journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled={tail_min_fill_enabled}",
        "--set",
        f"journey_certificate_completion_bound_diverse_harvest_tail_min_fill={int(tail_min_fill)}",
        "--set",
        f"journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth={int(max_depth)}",
        "--set",
        (
            "journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only="
            f"{bool(final_probe_only)}"
        ),
        "--set",
        "journey_tail_action_early_branch_enabled=False",
        "--set",
        "journey_tail_action_no_column_early_branch_enabled=False",
        "--set",
        "journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    ]
    return command


def build_runbook(
    *,
    profile_summaries: list[Path],
    tail_action_audits: list[Path] | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    config: Path = DEFAULT_CONFIG,
    time_limit: int = 600,
    limit: int = 60,
    python: str = "/home/kai/miniconda3/bin/python",
    max_workers: int = 1,
    timeout_kill_after: str = "30s",
    tail_min_fill: int = 4,
    tail_min_fill_max_depth: int = 0,
    tail_min_fill_final_probe_only: bool = True,
    require_tail_action_class: tuple[str, ...] = ("D_EARLY_BRANCH",),
    require_tail_action_productivity_class: tuple[str, ...] = tuple(),
    require_source_outside_target_wall: bool = False,
    target_wall: float = 200.0,
) -> dict[str, Any]:
    raw_rows = _load_records(profile_summaries)
    tail_action_rows = _load_tail_action_rows(tail_action_audits or [])
    required_classes = {str(value) for value in require_tail_action_class if str(value)}
    required_productivity_classes = {
        str(value) for value in require_tail_action_productivity_class if str(value)
    }
    tail_action_index: dict[str, dict[str, Any]] | None = None
    tail_action_class_counts: dict[str, int] = {}
    tail_action_productivity_counts: dict[str, int] = {}
    if tail_action_audits:
        tail_action_index, tail_action_class_counts, tail_action_productivity_counts = _tail_action_filter_index(
            tail_action_rows,
            required_classes=required_classes,
            required_productivity_classes=required_productivity_classes,
        )
    candidates, selection_stats = _select_candidates(
        raw_rows,
        limit=limit,
        tail_action_filter_index=tail_action_index,
        require_source_outside_target_wall=require_source_outside_target_wall,
        target_wall=target_wall,
    )
    entries: list[dict[str, Any]] = []
    commands: list[dict[str, str]] = []
    for index, row in enumerate(candidates, start=1):
        instance = str(row["instance"])
        slug = _safe_slug(Path(instance).stem)
        base_dir = output_dir / f"{index:03d}_{slug}"
        baseline_dir = base_dir / "baseline"
        optin_dir = base_dir / "tail_minfill_optin"
        baseline_command = _command(
            config=config,
            instance=instance,
            profile="baseline",
            result_dir=baseline_dir,
            time_limit=time_limit,
            python=python,
            max_workers=max_workers,
            timeout_kill_after=timeout_kill_after,
            tail_min_fill_enabled=False,
            tail_min_fill=tail_min_fill,
            max_depth=tail_min_fill_max_depth,
            final_probe_only=tail_min_fill_final_probe_only,
        )
        optin_command = _command(
            config=config,
            instance=instance,
            profile="tail_minfill_optin",
            result_dir=optin_dir,
            time_limit=time_limit,
            python=python,
            max_workers=max_workers,
            timeout_kill_after=timeout_kill_after,
            tail_min_fill_enabled=True,
            tail_min_fill=tail_min_fill,
            max_depth=tail_min_fill_max_depth,
            final_probe_only=tail_min_fill_final_probe_only,
        )
        entry = {
            "entry_id": index,
            "instance": instance,
            "source_log_file": row.get("log_file"),
            "source_finish_status": row.get("finish_status"),
            "source_finish_solving_time": row.get("finish_solving_time"),
            "source_completion_retry_class": row.get("completion_retry_class"),
            "source_tail_min_fill_candidate_count": row.get(
                "completion_retry_tail_min_fill_candidate_count"
            ),
            "source_tail_min_fill_reason_counts": row.get(
                "completion_retry_tail_min_fill_reason_counts"
            ),
            "tail_action_filter_match": row.get("tail_action_filter_match"),
            "baseline_result_dir": str(baseline_dir),
            "optin_result_dir": str(optin_dir),
            "baseline_command": _shell_join(baseline_command),
            "optin_command": _shell_join(optin_command),
        }
        entries.append(entry)
        commands.append(
            {
                "entry_id": str(index),
                "profile": "baseline",
                "instance": instance,
                "command": entry["baseline_command"],
            }
        )
        commands.append(
            {
                "entry_id": str(index),
                "profile": "tail_minfill_optin",
                "instance": instance,
                "command": entry["optin_command"],
            }
        )
    summary = {
        "schema_version": "journey_tail_minfill_ab_runbook_v1",
        "status": "ready" if entries else "empty",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "input_profile_summaries": [str(path) for path in profile_summaries],
        "input_tail_action_audits": [str(path) for path in (tail_action_audits or [])],
        "raw_record_count": len(raw_rows),
        "tail_action_filter_enabled": bool(tail_action_audits),
        "tail_action_filter_required_classes": sorted(required_classes),
        "tail_action_filter_required_productivity_classes": sorted(required_productivity_classes),
        "tail_action_filter_row_count": len(tail_action_rows),
        "tail_action_filter_match_key_count": 0 if tail_action_index is None else len(tail_action_index),
        "tail_action_filter_class_counts": tail_action_class_counts,
        "tail_action_filter_productivity_class_counts": tail_action_productivity_counts,
        "require_source_outside_target_wall": bool(require_source_outside_target_wall),
        "target_wall": float(target_wall),
        "selection_stats": selection_stats,
        "candidate_instance_count": len(candidates),
        "entry_count": len(entries),
        "command_count": len(commands),
        "config": str(config),
        "time_limit": int(time_limit),
        "tail_min_fill": int(tail_min_fill),
        "tail_min_fill_max_depth": int(tail_min_fill_max_depth),
        "tail_min_fill_final_probe_only": bool(tail_min_fill_final_probe_only),
        "entries": entries,
        "commands": commands,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "runbook.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "commands.sh").write_text(
        "\n".join(command["command"] for command in commands) + ("\n" if commands else ""),
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Journey Tail Min-Fill A/B Runbook",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把 completion-tail profile 中的低 min-fill audit-only 候选转成 paired replay 命令。"
        "该脚本只生成 runbook，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "journey_tail_minfill_ab_runbook = current",
        f"status = {summary['status']}",
        f"raw_record_count = {summary['raw_record_count']}",
        f"tail_action_filter_enabled = {summary['tail_action_filter_enabled']}",
        f"tail_action_filter_row_count = {summary['tail_action_filter_row_count']}",
        f"tail_action_filter_match_key_count = {summary['tail_action_filter_match_key_count']}",
        f"tail_action_filter_required_classes = {summary['tail_action_filter_required_classes']}",
        "tail_action_filter_required_productivity_classes = "
        f"{summary['tail_action_filter_required_productivity_classes']}",
        f"require_source_outside_target_wall = {summary['require_source_outside_target_wall']}",
        f"target_wall = {summary['target_wall']}",
        f"selection_stats = {summary['selection_stats']}",
        f"candidate_instance_count = {summary['candidate_instance_count']}",
        f"entry_count = {summary['entry_count']}",
        f"command_count = {summary['command_count']}",
        f"time_limit = {summary['time_limit']}",
        f"tail_min_fill = {summary['tail_min_fill']}",
        f"tail_min_fill_max_depth = {summary['tail_min_fill_max_depth']}",
        f"tail_min_fill_final_probe_only = {summary['tail_min_fill_final_probe_only']}",
        "runs_bpc_or_pricing = false",
        "certificate_effect = false",
        "official_bound_effect = false",
        "```",
        "",
        "## 说明",
        "",
        "每个 entry 有 baseline 与 tail_minfill_optin 两条命令。baseline 强制保持低 min-fill 关闭，"
        "opt-in 只打开低 min-fill 调度；两者都保持 exact oracle 负责 RC 与证书。",
        "",
        "## Entries",
        "",
        "```json",
        json.dumps(summary["entries"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile-summary", type=Path, action="append", required=True)
    parser.add_argument("--tail-action-audit", type=Path, action="append", default=[])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--time-limit", type=int, default=600)
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("--python", default="/home/kai/miniconda3/bin/python")
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--timeout-kill-after", default="30s")
    parser.add_argument("--tail-min-fill", type=int, default=4)
    parser.add_argument("--tail-min-fill-max-depth", type=int, default=0)
    parser.add_argument("--tail-min-fill-final-probe-only", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument(
        "--require-source-outside-target-wall",
        action="store_true",
        help=(
            "Skip source/profile rows that are already OPTIMAL within --target-wall. "
            "This keeps opt-in A/B candidates focused on unresolved or slow contexts."
        ),
    )
    parser.add_argument("--target-wall", type=float, default=200.0)
    parser.add_argument(
        "--require-tail-action-class",
        action="append",
        default=None,
        help=(
            "When --tail-action-audit is provided, keep only candidates whose "
            "instance/log has at least one matching tail_action_class. Repeat "
            "to allow multiple classes; pass an empty string to disable class filtering."
        ),
    )
    parser.add_argument(
        "--require-tail-action-productivity-class",
        action="append",
        default=[],
        help=(
            "Optional productivity-class filter for --tail-action-audit, for example "
            "pricing_unproductive_no_negative_columns."
        ),
    )
    args = parser.parse_args()
    build_runbook(
        profile_summaries=list(args.profile_summary),
        tail_action_audits=list(args.tail_action_audit or []),
        output_dir=args.output_dir,
        report=args.report,
        config=args.config,
        time_limit=args.time_limit,
        limit=args.limit,
        python=args.python,
        max_workers=args.max_workers,
        timeout_kill_after=args.timeout_kill_after,
        tail_min_fill=args.tail_min_fill,
        tail_min_fill_max_depth=args.tail_min_fill_max_depth,
        tail_min_fill_final_probe_only=args.tail_min_fill_final_probe_only,
        require_tail_action_class=tuple(args.require_tail_action_class)
        if args.require_tail_action_class is not None
        else ("D_EARLY_BRANCH",),
        require_tail_action_productivity_class=tuple(
            args.require_tail_action_productivity_class or ()
        ),
        require_source_outside_target_wall=bool(args.require_source_outside_target_wall),
        target_wall=float(args.target_wall),
    )


if __name__ == "__main__":
    main()
