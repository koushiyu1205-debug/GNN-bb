#!/usr/bin/env python3
"""中文摘要：本脚本按配置批量运行纯 SCIP compact MILP baseline，并输出 results/scip_baseline.csv。"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gnn_bb.baseline.config import load_config
from gnn_bb.baseline.scip_milp import BaselineResult, solve_scip_baseline
from gnn_bb.data.instances import load_or_build_instance
from gnn_bb.data.io_utils import ensure_dir
from gnn_bb.data.terrain import build_task_closure


def _csv_fieldnames() -> list[str]:
    return list(BaselineResult.__dataclass_fields__.keys())


def _write_rows(path: Path, rows: list[dict]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_csv_fieldnames())
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行纯 SCIP compact MILP baseline。")
    parser.add_argument("--config", default="configs/scip_baseline.yaml")
    parser.add_argument("--instances", nargs="*", help="覆盖配置中的实例列表，例如 very_small medium 30")
    parser.add_argument("--time-limit", type=float, help="覆盖配置中的时间限制")
    parser.add_argument("--results-csv", help="覆盖配置中的 CSV 输出路径")
    parser.add_argument("--quiet", action="store_true", help="隐藏 SCIP 控制台日志")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    instances = args.instances or config.get("instances", ["very_small"])
    time_limit = float(args.time_limit if args.time_limit is not None else config.get("time_limit", 3600))
    results_csv = ROOT / (args.results_csv or config.get("results_csv", "results/scip_baseline.csv"))
    log_dir = ROOT / config.get("log_dir", "results/logs/scip_baseline")
    instance_dir = config.get("instance_dir", "json/instances")
    write_instance_json = bool(config.get("write_instance_json", True))
    verbose = bool(config.get("display_log", True)) and not args.quiet
    seed = config.get("random_seed")
    scip_params = dict(config.get("scip_params", {}))

    rows = []
    for name in instances:
        instance, instance_path = load_or_build_instance(str(name), instance_dir=instance_dir, write_if_missing=write_instance_json)
        pairwise = build_task_closure(instance, weight="cost")
        log_path = log_dir / f"{instance['name']}.log"
        result = solve_scip_baseline(
            instance,
            pairwise,
            instance_path=instance_path,
            time_limit=time_limit,
            log_path=log_path,
            scip_params=scip_params,
            seed=int(seed) if seed is not None else None,
            verbose=verbose,
        )
        rows.append(result.to_row())
        print(
            f"{result.instance}: status={result.status}, primal={result.primal_bound}, "
            f"dual={result.dual_bound}, gap={result.gap}, time={result.solving_time}s"
        )

    _write_rows(results_csv, rows)
    print(f"baseline CSV 已写入：{results_csv}")


if __name__ == "__main__":
    main()

