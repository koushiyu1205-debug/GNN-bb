#!/usr/bin/env python3
"""Run BPC_future instances one by one with an OS-level per-instance timeout."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


BASE_FIELDS = [
    "instance",
    "status",
    "solving_time",
    "primal_bound",
    "dual_bound",
    "gap",
    "node_count",
    "rmp_solves",
    "pricing_calls",
    "exact_pricing_calls",
    "generated_sequences",
    "evaluated_timed_trips",
    "columns",
    "computed_R_bar",
    "fleet_bound_heuristic_R",
    "fleet_bound_UB",
    "cuts_added",
    "subset_row_cuts_added",
    "sortie_lb_cut_added",
    "fleet_lb_cut_added",
]

EXTRA_FIELDS = [
    "external_timeout",
    "return_code",
    "wall_time",
    "run_log",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--instances", nargs="+", required=True)
    parser.add_argument("--time-limit", type=float, required=True)
    parser.add_argument("--results-csv", required=True)
    parser.add_argument("--log-dir", required=True)
    parser.add_argument("--solution-dir", required=True)
    parser.add_argument("--run-log-dir", required=True)
    parser.add_argument("--set", dest="overrides", action="append", default=[])
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--timeout-kill-after", default="30s")
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument(
        "--force-child-exit-after-run",
        action="store_true",
        help="Pass --force-exit-after-run to each isolated run_bpc_future.py child.",
    )
    return parser.parse_args()


def read_done(path: Path) -> tuple[list[dict[str, str]], set[str]]:
    if not path.exists():
        return [], set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
    return rows, {str(row.get("instance", "")) for row in rows if row.get("instance")}


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=BASE_FIELDS + EXTRA_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in BASE_FIELDS + EXTRA_FIELDS})


def read_single_result(path: Path) -> dict[str, str] | None:
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return dict(rows[0]) if rows else None


def timeout_row(instance: str, elapsed: float, return_code: int, run_log: Path) -> dict[str, object]:
    return {
        "instance": instance,
        "status": "EXTERNAL_TIME_LIMIT",
        "solving_time": "",
        "primal_bound": "",
        "dual_bound": "",
        "gap": "",
        "node_count": "",
        "rmp_solves": "",
        "pricing_calls": "",
        "exact_pricing_calls": "",
        "generated_sequences": "",
        "evaluated_timed_trips": "",
        "columns": "",
        "computed_R_bar": "",
        "fleet_bound_heuristic_R": "",
        "fleet_bound_UB": "",
        "cuts_added": "",
        "subset_row_cuts_added": "",
        "sortie_lb_cut_added": "",
        "fleet_lb_cut_added": "",
        "external_timeout": "true",
        "return_code": return_code,
        "wall_time": round(float(elapsed), 6),
        "run_log": str(run_log),
    }


def run_instance(
    *,
    args: argparse.Namespace,
    env: dict[str, str],
    index: int,
    total: int,
    instance: str,
    log_dir: Path,
    solution_dir: Path,
    run_log_dir: Path,
) -> tuple[int, dict[str, object], int, float]:
    stem = Path(instance).name.replace(".json", "")
    run_log = run_log_dir / f"{index:03d}_{stem}.log"
    with tempfile.TemporaryDirectory(prefix="bpc_future_single_") as tmp:
        temp_csv = Path(tmp) / "result.csv"
        cmd = [
            "timeout",
            "--kill-after",
            str(args.timeout_kill_after),
            f"{float(args.time_limit):.6f}s",
            args.python,
            "BPC_future/scripts/run_bpc_future.py",
            "--config",
            args.config,
            "--instances",
            instance,
            "--time-limit",
            str(float(args.time_limit)),
            "--results-csv",
            str(temp_csv),
            "--log-dir",
            str(log_dir),
            "--solution-dir",
            str(solution_dir),
        ]
        if args.quiet:
            cmd.append("--quiet")
        if args.force_child_exit_after_run:
            cmd.append("--force-exit-after-run")
        for override in args.overrides:
            cmd.extend(["--set", override])
        print(f"[{index}/{total}] run {instance}", flush=True)
        started = time.perf_counter()
        with run_log.open("w", encoding="utf-8") as handle:
            completed = subprocess.run(cmd, stdout=handle, stderr=subprocess.STDOUT, env=env)
        elapsed = time.perf_counter() - started
        row = read_single_result(temp_csv)
        if row is not None:
            row["external_timeout"] = "false"
            row["return_code"] = completed.returncode
            row["wall_time"] = round(float(elapsed), 6)
            row["run_log"] = str(run_log)
        else:
            row = timeout_row(instance, elapsed, completed.returncode, run_log)
        return index, row, completed.returncode, elapsed


def main() -> None:
    args = parse_args()
    if int(args.max_workers) < 1:
        raise ValueError("--max-workers must be >= 1")
    results_csv = Path(args.results_csv)
    log_dir = Path(args.log_dir)
    solution_dir = Path(args.solution_dir)
    run_log_dir = Path(args.run_log_dir)
    run_log_dir.mkdir(parents=True, exist_ok=True)
    rows, done = read_done(results_csv)
    write_rows(results_csv, rows)

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = "."

    total = len(args.instances)
    instance_order = {str(instance): index for index, instance in enumerate(args.instances, start=1)}
    pending: list[tuple[int, str]] = []
    for index, instance in enumerate(args.instances, start=1):
        if instance in done:
            print(f"[{index}/{total}] skip existing {instance}", flush=True)
            continue
        pending.append((index, instance))

    def record(index: int, row: dict[str, object], return_code: int, elapsed: float) -> None:
        rows.append(row)
        done.add(str(row.get("instance", "")))
        ordered_rows = sorted(
            rows,
            key=lambda item: instance_order.get(str(item.get("instance", "")), total + 1),
        )
        write_rows(results_csv, ordered_rows)
        print(
            f"[{index}/{total}] status={row.get('status')} "
            f"return_code={return_code} wall={elapsed:.2f}s",
            flush=True,
        )

    if int(args.max_workers) == 1:
        for index, instance in pending:
            index, row, return_code, elapsed = run_instance(
                args=args,
                env=env,
                index=index,
                total=total,
                instance=instance,
                log_dir=log_dir,
                solution_dir=solution_dir,
                run_log_dir=run_log_dir,
            )
            record(index, row, return_code, elapsed)
    else:
        print(f"running {len(pending)} pending instances with max_workers={int(args.max_workers)}", flush=True)
        with ThreadPoolExecutor(max_workers=int(args.max_workers)) as executor:
            futures = [
                executor.submit(
                    run_instance,
                    args=args,
                    env=env,
                    index=index,
                    total=total,
                    instance=instance,
                    log_dir=log_dir,
                    solution_dir=solution_dir,
                    run_log_dir=run_log_dir,
                )
                for index, instance in pending
            ]
            for future in as_completed(futures):
                index, row, return_code, elapsed = future.result()
                record(index, row, return_code, elapsed)


if __name__ == "__main__":
    main()
