#!/usr/bin/env python3
"""Execute commands from a GAT target-priority worker A/B runbook.

This is an execution helper only.  It does not build candidates, classify ROI,
or alter solver/certificate semantics.  It runs the explicit commands already
recorded in a runbook summary and writes a JSONL execution log plus a compact
summary.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import subprocess
import threading
import time
from typing import Any


DEFAULT_RUNBOOK_SUMMARY = Path(
    "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/"
    "worker_ab_runbook/summary.json"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _tail(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _results_csv_from_command(command: str) -> str:
    try:
        parts = shlex.split(command)
    except ValueError:
        return ""
    for index, part in enumerate(parts):
        if part == "--results-csv" and index + 1 < len(parts):
            return parts[index + 1]
    return ""


def _matches_any_fragment(command_type: str, fragments: set[str]) -> bool:
    return any(fragment in command_type for fragment in fragments)


def _command_allowed(
    command_type: str,
    include: set[str],
    exclude: set[str],
    include_contains: set[str],
    exclude_contains: set[str],
) -> bool:
    if include and command_type not in include:
        return False
    if include_contains and not _matches_any_fragment(command_type, include_contains):
        return False
    if exclude and command_type in exclude:
        return False
    if exclude_contains and _matches_any_fragment(command_type, exclude_contains):
        return False
    return True


def _run_one(
    command: dict[str, Any],
    *,
    cwd: Path,
    dry_run: bool,
    skip_existing: bool,
) -> dict[str, Any]:
    command_type = str(command.get("command_type") or "")
    command_text = str(command.get("command") or "")
    results_csv = _results_csv_from_command(command_text)
    results_path = Path(results_csv) if results_csv else None
    exists_before = bool(results_path and results_path.exists())
    if skip_existing and exists_before:
        return {
            "schema_version": "gat_target_priority_worker_ab_runbook_execution_record_v1",
            "command_type": command_type,
            "command": command_text,
            "results_csv": results_csv,
            "status": "skipped_existing_result",
            "returncode": 0,
            "started_at": _utc_now(),
            "ended_at": _utc_now(),
            "elapsed_s": 0.0,
            "results_csv_exists_before": exists_before,
            "results_csv_exists_after": True,
            "stdout_tail": "",
            "stderr_tail": "",
        }
    if dry_run:
        return {
            "schema_version": "gat_target_priority_worker_ab_runbook_execution_record_v1",
            "command_type": command_type,
            "command": command_text,
            "results_csv": results_csv,
            "status": "dry_run",
            "returncode": 0,
            "started_at": _utc_now(),
            "ended_at": _utc_now(),
            "elapsed_s": 0.0,
            "results_csv_exists_before": exists_before,
            "results_csv_exists_after": exists_before,
            "stdout_tail": "",
            "stderr_tail": "",
        }
    started = _utc_now()
    start = time.monotonic()
    completed = subprocess.run(
        command_text,
        cwd=str(cwd),
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    elapsed = time.monotonic() - start
    exists_after = bool(results_path and results_path.exists())
    status = "success" if completed.returncode == 0 and (not results_path or exists_after) else "failed"
    return {
        "schema_version": "gat_target_priority_worker_ab_runbook_execution_record_v1",
        "command_type": command_type,
        "command": command_text,
        "results_csv": results_csv,
        "status": status,
        "returncode": int(completed.returncode),
        "started_at": started,
        "ended_at": _utc_now(),
        "elapsed_s": elapsed,
        "results_csv_exists_before": exists_before,
        "results_csv_exists_after": exists_after,
        "stdout_tail": _tail(completed.stdout or ""),
        "stderr_tail": _tail(completed.stderr or ""),
    }


def execute_runbook(
    *,
    runbook_summary: Path,
    execution_log: Path | None = None,
    execution_summary: Path | None = None,
    max_workers: int = 1,
    dry_run: bool = False,
    skip_existing: bool = True,
    include_command_types: set[str] | None = None,
    exclude_command_types: set[str] | None = None,
    include_command_type_contains: set[str] | None = None,
    exclude_command_type_contains: set[str] | None = None,
    cwd: Path = Path("."),
) -> dict[str, Any]:
    runbook = _read_json(runbook_summary)
    commands = [
        dict(command)
        for command in runbook.get("commands") or []
        if isinstance(command, dict)
        and _command_allowed(
            str(command.get("command_type") or ""),
            include_command_types or set(),
            exclude_command_types or set(),
            include_command_type_contains or set(),
            exclude_command_type_contains or set(),
        )
    ]
    if execution_log is None:
        execution_log = Path(runbook_summary).with_name("runbook_execution_log.jsonl")
    if execution_summary is None:
        execution_summary = Path(runbook_summary).with_name("runbook_execution_summary.json")
    execution_log.parent.mkdir(parents=True, exist_ok=True)
    execution_summary.parent.mkdir(parents=True, exist_ok=True)
    log_lock = threading.Lock()
    records: list[dict[str, Any]] = []

    def run_and_log(command: dict[str, Any]) -> dict[str, Any]:
        record = _run_one(
            command,
            cwd=cwd,
            dry_run=dry_run,
            skip_existing=skip_existing,
        )
        with log_lock:
            with execution_log.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return record

    started_at = _utc_now()
    start = time.monotonic()
    workers = max(1, int(max_workers))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(run_and_log, command) for command in commands]
        for future in as_completed(futures):
            records.append(future.result())
    records.sort(key=lambda item: str(item.get("command_type") or ""))
    elapsed = time.monotonic() - start
    failed = [record for record in records if record["status"] == "failed"]
    summary = {
        "schema_version": "gat_target_priority_worker_ab_runbook_execution_summary_v1",
        "status": "executed" if records else "no_commands",
        "runbook_summary": str(runbook_summary),
        "execution_log": str(execution_log),
        "command_count": len(commands),
        "executed_count": sum(1 for record in records if record["status"] == "success"),
        "skipped_existing_count": sum(
            1 for record in records if record["status"] == "skipped_existing_result"
        ),
        "dry_run_count": sum(1 for record in records if record["status"] == "dry_run"),
        "failed_command_count": len(failed),
        "max_workers": workers,
        "dry_run": bool(dry_run),
        "skip_existing": bool(skip_existing),
        "started_at": started_at,
        "ended_at": _utc_now(),
        "elapsed_s": elapsed,
        "failed_commands": [
            {
                "command_type": record["command_type"],
                "returncode": record["returncode"],
                "results_csv": record["results_csv"],
                "stderr_tail": record["stderr_tail"],
            }
            for record in failed
        ],
        "records": records,
        "runs_bpc_or_pricing": not bool(dry_run),
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "all_checks_pass": bool(records) and not failed,
    }
    execution_summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _parse_types(values: list[str]) -> set[str]:
    parsed: set[str] = set()
    for value in values:
        for part in str(value).split(","):
            item = part.strip()
            if item:
                parsed.add(item)
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runbook-summary", type=Path, default=DEFAULT_RUNBOOK_SUMMARY)
    parser.add_argument("--execution-log", type=Path, default=None)
    parser.add_argument("--execution-summary", type=Path, default=None)
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-skip-existing", action="store_true")
    parser.add_argument("--include-command-type", action="append", default=[])
    parser.add_argument("--exclude-command-type", action="append", default=[])
    parser.add_argument("--include-command-type-contains", action="append", default=[])
    parser.add_argument("--exclude-command-type-contains", action="append", default=[])
    parser.add_argument("--cwd", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    summary = execute_runbook(
        runbook_summary=args.runbook_summary,
        execution_log=args.execution_log,
        execution_summary=args.execution_summary,
        max_workers=max(1, int(args.max_workers)),
        dry_run=bool(args.dry_run),
        skip_existing=not bool(args.no_skip_existing),
        include_command_types=_parse_types(args.include_command_type),
        exclude_command_types=_parse_types(args.exclude_command_type),
        include_command_type_contains=_parse_types(args.include_command_type_contains),
        exclude_command_type_contains=_parse_types(args.exclude_command_type_contains),
        cwd=args.cwd,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
