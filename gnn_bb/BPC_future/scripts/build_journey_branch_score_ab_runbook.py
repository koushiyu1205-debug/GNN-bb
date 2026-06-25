#!/usr/bin/env python3
"""Build exact-safe Journey branch-score A/B runbooks.

This is an offline planning helper. It reads strict branch score rows and
optional benchmark result CSVs, then emits paired baseline/branch-score-horizon
commands for the same instance. It does not run BPC, pricing, RMP, or produce
official bounds/certificates.
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


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_score_ab_runbook_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_journey_branch_score_ab_runbook_zh.md"
)
DEFAULT_CONFIG = Path("BPC_future/configs/moon_trek_20_smoke.yaml")


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


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _score_row_file(path: Path) -> Path:
    if path.is_dir():
        for name in ("journey_branch_score_rows.json", "journey_branch_score_rows.jsonl"):
            candidate = path / name
            if candidate.exists():
                return candidate
    return path


def _load_score_rows(path: Path) -> list[dict[str, Any]]:
    row_path = _score_row_file(path)
    if not row_path.exists():
        return []
    if row_path.suffix == ".jsonl":
        return _read_jsonl(row_path)
    try:
        payload = json.loads(row_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        rows: list[dict[str, Any]] = []
        for value in payload.values():
            if isinstance(value, dict):
                rows.append(value)
        return rows
    return []


def _load_results(paths: Iterable[Path]) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for path in paths:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                instance = str(row.get("instance") or "")
                if not instance:
                    continue
                results[instance] = dict(row)
    return results


def _pair_from_row(row: dict[str, Any]) -> list[int] | None:
    pair = row.get("pair") or row.get("branch_pair") or row.get("candidate_pair")
    if isinstance(pair, (list, tuple)) and len(pair) == 2:
        try:
            i, j = int(pair[0]), int(pair[1])
        except (TypeError, ValueError):
            return None
        return sorted((i, j))
    if row.get("task_i") is not None and row.get("task_j") is not None:
        try:
            i, j = int(row["task_i"]), int(row["task_j"])
        except (TypeError, ValueError):
            return None
        return sorted((i, j))
    return None


def _score_from_row(row: dict[str, Any]) -> float | None:
    for key in ("branch_score", "score", "impact_score", "predicted_score"):
        if row.get(key) is None:
            continue
        score = _float(row.get(key), default=float("nan"))
        if score == score:
            return float(score)
    return None


def _group_score_rows(rows: Iterable[dict[str, Any]], *, min_score: float) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        instance = str(row.get("instance") or row.get("instance_path") or "")
        if not instance:
            continue
        score = _score_from_row(row)
        if score is None or float(score) <= float(min_score):
            continue
        grouped.setdefault(instance, []).append(row)
    for instance_rows in grouped.values():
        instance_rows.sort(key=lambda item: _score_from_row(item) or float("-inf"), reverse=True)
    return grouped


def _command(
    *,
    config: Path,
    instance: str,
    time_limit: int,
    result_dir: Path,
    python: str,
    max_workers: int,
    candidate_log_top_n: int,
    score_path: Path | None,
    score_horizon_tie_tolerance: float,
    score_horizon_min_score: float,
) -> list[str]:
    command = [
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
        str(int(max_workers)),
        "--quiet",
        "--set",
        f"journey_branch_candidate_log_top_n={int(candidate_log_top_n)}",
        "--set",
        "journey_tail_action_early_branch_enabled=False",
        "--set",
        "journey_tail_action_no_column_early_branch_enabled=False",
        "--set",
        "journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    ]
    if score_path is not None:
        command.extend(
            [
                "--set",
                "journey_branch_candidate_priority=branch_score_horizon",
                "--set",
                f"journey_branch_candidate_score_path={score_path}",
                "--set",
                f"journey_branch_candidate_score_horizon_tie_tolerance={float(score_horizon_tie_tolerance)}",
                "--set",
                f"journey_branch_candidate_score_horizon_min_score={float(score_horizon_min_score)}",
            ]
        )
    return command


def build_runbook(
    *,
    score_path: Path,
    output_dir: Path,
    report: Path,
    results_csv: list[Path] | None = None,
    config: Path = DEFAULT_CONFIG,
    time_limit: int = 600,
    target_wall: float = 200.0,
    min_wall: float | None = None,
    max_wall: float | None = None,
    only_status: tuple[str, ...] = ("OPTIMAL",),
    limit: int = 60,
    python: str = "/home/kai/miniconda3/bin/python",
    max_workers: int = 1,
    candidate_log_top_n: int = 200,
    score_horizon_tie_tolerance: float = 0.2,
    score_horizon_min_score: float = 1.5,
) -> dict[str, Any]:
    score_rows = _load_score_rows(score_path)
    grouped = _group_score_rows(score_rows, min_score=score_horizon_min_score)
    results = _load_results(results_csv or [])
    status_set = {str(status) for status in only_status if str(status)}
    min_wall_threshold = float(target_wall if min_wall is None else min_wall)
    entries: list[dict[str, Any]] = []
    skipped_missing_result = 0
    skipped_status = 0
    skipped_wall = 0

    for instance in sorted(grouped):
        result_row = results.get(instance)
        if results and result_row is None:
            skipped_missing_result += 1
            continue
        status = str(result_row.get("status") or "") if result_row else ""
        wall = _float(result_row.get("wall_time"), 0.0) if result_row else 0.0
        if status_set and result_row is not None and status not in status_set:
            skipped_status += 1
            continue
        if result_row is not None:
            if wall < min_wall_threshold:
                skipped_wall += 1
                continue
            if max_wall is not None and wall > float(max_wall):
                skipped_wall += 1
                continue
        rows = grouped[instance]
        top_row = rows[0]
        top_pair = _pair_from_row(top_row)
        top_score = _score_from_row(top_row)
        slug = _safe_slug(Path(instance).stem)
        run_root = output_dir / "runs" / f"{len(entries) + 1:03d}_{slug}"
        baseline_command = _command(
            config=config,
            instance=instance,
            time_limit=time_limit,
            result_dir=run_root / "baseline",
            python=python,
            max_workers=max_workers,
            candidate_log_top_n=candidate_log_top_n,
            score_path=None,
            score_horizon_tie_tolerance=score_horizon_tie_tolerance,
            score_horizon_min_score=score_horizon_min_score,
        )
        optin_command = _command(
            config=config,
            instance=instance,
            time_limit=time_limit,
            result_dir=run_root / "score_horizon",
            python=python,
            max_workers=max_workers,
            candidate_log_top_n=candidate_log_top_n,
            score_path=score_path,
            score_horizon_tie_tolerance=score_horizon_tie_tolerance,
            score_horizon_min_score=score_horizon_min_score,
        )
        entries.append(
            {
                "instance": instance,
                "status": status,
                "wall_time": wall,
                "score_row_count": len(rows),
                "top_pair": top_pair,
                "top_score": top_score,
                "baseline_command": baseline_command,
                "optin_command": optin_command,
                "run_root": str(run_root),
            }
        )
        if len(entries) >= int(limit):
            break

    summary = {
        "schema_version": "journey_branch_score_ab_runbook_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "score_path": str(score_path),
        "config": str(config),
        "output_dir": str(output_dir),
        "time_limit": int(time_limit),
        "target_wall": float(target_wall),
        "min_wall": min_wall_threshold,
        "max_wall": None if max_wall is None else float(max_wall),
        "only_status": sorted(status_set),
        "candidate_log_top_n": int(candidate_log_top_n),
        "score_horizon_tie_tolerance": float(score_horizon_tie_tolerance),
        "score_horizon_min_score": float(score_horizon_min_score),
        "raw_score_row_count": len(score_rows),
        "score_instance_count": len(grouped),
        "entry_count": len(entries),
        "command_count": len(entries) * 2,
        "skipped_missing_result_count": skipped_missing_result,
        "skipped_status_count": skipped_status,
        "skipped_wall_count": skipped_wall,
        "entries": entries,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "runbook.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines: list[str] = ["#!/usr/bin/env bash", "set -euo pipefail", ""]
    for index, entry in enumerate(entries, start=1):
        lines.append(f"# {index:03d} baseline {entry['instance']}")
        lines.append(_shell_join(entry["baseline_command"]))
        lines.append(f"# {index:03d} branch_score_horizon {entry['instance']}")
        lines.append(_shell_join(entry["optin_command"]))
        lines.append("")
    (output_dir / "commands.sh").write_text("\n".join(lines), encoding="utf-8")
    _write_report(summary, report)
    return summary


def _write_report(summary: dict[str, Any], report: Path) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Branch Score A/B Runbook",
        "",
        "该 runbook 只生成 baseline / branch-score-horizon 成对命令；不运行 BPC，不产生 official bound 或 certificate。",
        "",
        "## Machine Fields",
        "",
        "```text",
        f"output_dir = {summary['output_dir']}",
        f"score_path = {summary['score_path']}",
        f"entry_count = {summary['entry_count']}",
        f"command_count = {summary['command_count']}",
        f"candidate_log_top_n = {summary['candidate_log_top_n']}",
        f"score_horizon_tie_tolerance = {summary['score_horizon_tie_tolerance']}",
        f"score_horizon_min_score = {summary['score_horizon_min_score']}",
        f"raw_score_row_count = {summary['raw_score_row_count']}",
        f"score_instance_count = {summary['score_instance_count']}",
        f"skipped_missing_result_count = {summary['skipped_missing_result_count']}",
        f"skipped_status_count = {summary['skipped_status_count']}",
        f"skipped_wall_count = {summary['skipped_wall_count']}",
        "official_bound_effect = false",
        "certificate_effect = false",
        "```",
        "",
        "## Entries",
        "",
    ]
    for index, entry in enumerate(summary["entries"], start=1):
        lines.extend(
            [
                f"### {index:03d} {entry['instance']}",
                "",
                "```text",
                f"status = {entry['status']}",
                f"wall_time = {entry['wall_time']}",
                f"score_row_count = {entry['score_row_count']}",
                f"top_pair = {entry['top_pair']}",
                f"top_score = {entry['top_score']}",
                "```",
                "",
            ]
        )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score-path", required=True)
    parser.add_argument("--results-csv", action="append", default=[])
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--time-limit", type=int, default=600)
    parser.add_argument("--target-wall", type=float, default=200.0)
    parser.add_argument("--min-wall", type=float, default=None)
    parser.add_argument("--max-wall", type=float, default=None)
    parser.add_argument("--only-status", action="append", default=["OPTIMAL"])
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("--python", default="/home/kai/miniconda3/bin/python")
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--candidate-log-top-n", type=int, default=200)
    parser.add_argument("--score-horizon-tie-tolerance", type=float, default=0.2)
    parser.add_argument("--score-horizon-min-score", type=float, default=1.5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = Path(args.report)
    if str(report) == str(DEFAULT_REPORT):
        report = report.with_name(
            f"{date.today():%Y%m%d}_bpc_future_journey_branch_score_ab_runbook_zh.md"
        )
    build_runbook(
        score_path=Path(args.score_path),
        output_dir=Path(args.output_dir),
        report=report,
        results_csv=[Path(path) for path in args.results_csv],
        config=Path(args.config),
        time_limit=args.time_limit,
        target_wall=args.target_wall,
        min_wall=args.min_wall,
        max_wall=args.max_wall,
        only_status=tuple(args.only_status or []),
        limit=args.limit,
        python=args.python,
        max_workers=args.max_workers,
        candidate_log_top_n=args.candidate_log_top_n,
        score_horizon_tie_tolerance=args.score_horizon_tie_tolerance,
        score_horizon_min_score=args.score_horizon_min_score,
    )


if __name__ == "__main__":
    main()
