#!/usr/bin/env python3
"""Run the self-contained BPC_future trip-time solver."""

from __future__ import annotations

import argparse
import ast
import csv
import gc
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.core.data import load_future_data
from BPC_future.core.fleet_bound import apply_fleet_bound_override
from BPC_future.pricing.trip_pricing import _clear_sequence_resource_precheck_cache
from BPC_future.solver.driver import solve_bpc_future, write_solution
from BPC_future.solver.journey_driver import solve_bpc_future_journey
from BPC_future.solver.logger import FutureLogger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run BPC_future trip-time BPC.")
    parser.add_argument("--config", default="BPC_future/configs/very_small.yaml")
    parser.add_argument("--instances", nargs="*")
    parser.add_argument("--time-limit", type=float)
    parser.add_argument("--results-csv")
    parser.add_argument("--log-dir")
    parser.add_argument("--solution-dir")
    parser.add_argument("--set", dest="overrides", action="append", default=[], help="Override config as key=value.")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument(
        "--force-exit-after-run",
        action="store_true",
        help=(
            "Flush outputs and call os._exit(0) after all rows are written. "
            "Use for isolated benchmark subprocesses that can otherwise stay "
            "alive in third-party interpreter shutdown."
        ),
    )
    return parser.parse_args()


def main() -> bool:
    args = parse_args()
    config = load_config(args.config)
    for override in args.overrides:
        if "=" not in override:
            raise ValueError(f"--set override must be key=value, got {override!r}")
        key, value = override.split("=", 1)
        config[key.strip()] = parse_value(value.strip())
    if args.instances:
        config["instances"] = args.instances
    if args.time_limit is not None:
        config["time_limit"] = float(args.time_limit)
    results_csv = Path(args.results_csv or config.get("results_csv", "BPC_future/results/bpc_future.csv"))
    log_dir = Path(args.log_dir or config.get("log_dir", "BPC_future/results/logs"))
    solution_dir = Path(args.solution_dir or config.get("solution_dir", "BPC_future/results/solutions"))
    results_csv.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in config.get("instances", ["very_small"]):
        _clear_sequence_resource_precheck_cache()
        data = load_future_data(str(name), instance_dir=config.get("instance_dir", "json/instances"))
        data, fleet_diag = apply_fleet_bound_override(data, config)
        logger = FutureLogger(log_dir / f"{name}.jsonl", console=not args.quiet)
        try:
            if bool(config.get("fleet_bound_log", True)):
                logger.log("fleet_bound_diagnostics", **fleet_diag.payload())
            if str(config.get("master_mode", "trip_time")) == "journey":
                result = solve_bpc_future_journey(data, config, logger=logger)
            else:
                result = solve_bpc_future(data, config, logger=logger)
        finally:
            logger.close()
        write_solution(solution_dir / f"solution_{name}.json", result)
        row = {
            "instance": name,
            "status": result.status,
            "solving_time": result.solving_time,
            "primal_bound": result.primal_bound,
            "dual_bound": result.dual_bound,
            "gap": result.gap,
            "node_count": result.node_count,
            "rmp_solves": result.rmp_solves,
            "pricing_calls": result.pricing_calls,
            "exact_pricing_calls": result.exact_pricing_calls,
            "generated_sequences": result.generated_sequences,
            "evaluated_timed_trips": result.evaluated_timed_trips,
            "columns": result.columns,
            "computed_R_bar": fleet_diag.new_R_bar,
            "fleet_bound_heuristic_R": fleet_diag.heuristic_R,
            "fleet_bound_UB": None if fleet_diag.heuristic_UB is None else round(float(fleet_diag.heuristic_UB), 6),
            "cuts_added": result.cuts_added,
            "subset_row_cuts_added": result.subset_row_cuts_added,
            "sortie_lb_cut_added": result.sortie_lb_cut_added,
            "fleet_lb_cut_added": result.fleet_lb_cut_added,
        }
        rows.append(row)
        print(
            f"{name}: status={result.status}, primal={result.primal_bound}, dual={result.dual_bound}, "
            f"gap={result.gap}, time={result.solving_time}s, nodes={result.node_count}, cols={result.columns}",
            flush=True,
        )
        _clear_sequence_resource_precheck_cache()
        gc.collect()
        torch_module = sys.modules.get("torch")
        if torch_module is not None:
            try:
                cuda = getattr(torch_module, "cuda", None)
                if cuda is not None and bool(cuda.is_available()):
                    cuda.empty_cache()
            except Exception:
                pass
    with results_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["instance"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"BPC_future CSV written: {results_csv}")
    return bool(args.force_exit_after_run)


def load_config(path: str | Path) -> dict:
    config = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        config[key.strip()] = parse_value(value.strip())
    return config


def parse_value(text: str):
    if text == "":
        return ""
    lower = text.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if lower in {"none", "null"}:
        return None
    try:
        return ast.literal_eval(text)
    except Exception:
        pass
    try:
        if any(ch in text for ch in ".eE"):
            return float(text)
        return int(text)
    except ValueError:
        return text


if __name__ == "__main__":
    _force_exit = main()
    if _force_exit:
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)
