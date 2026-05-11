#!/usr/bin/env python3
"""中文摘要：本脚本运行 no-ML branch-and-price baseline，输出 results/bp_no_ml.csv。"""

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
from gnn_bb.bp.route_vehicle_branch_price import BPResult, solve_bp_no_ml
from gnn_bb.data.instances import load_or_build_instance
from gnn_bb.data.io_utils import ensure_dir
from gnn_bb.data.terrain import build_task_closure


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 no-ML branch-and-price baseline。")
    parser.add_argument("--config", default="configs/bp_no_ml.yaml")
    parser.add_argument("--instances", nargs="*", help="覆盖配置中的实例列表")
    parser.add_argument("--time-limit", type=float, help="覆盖配置中的时间限制")
    parser.add_argument("--results-csv", help="覆盖配置中的 CSV 输出路径")
    parser.add_argument("--log-dir", help="覆盖日志输出目录")
    parser.add_argument("--solution-dir", help="覆盖解文件输出目录")
    parser.add_argument("--max-nodes", type=int, help="覆盖配置中的最大搜索节点数")
    parser.add_argument("--max-columns-per-pricing", type=int, help="覆盖每次 pricing 最多加入的列数")
    parser.add_argument("--memory-limit-mb", type=float, help="覆盖求解进程内存保护阈值，单位 MB")
    parser.add_argument("--quiet", action="store_true", help="关闭 B&P 进度日志和 RMP SCIP 控制台日志")
    parser.add_argument("--scip-log", action="store_true", help="在终端显示每个 RMP 的 SCIP 原始日志")
    return parser.parse_args()


def _write_rows(path: Path, rows: list[dict]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(BPResult.__dataclass_fields__.keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    instances = args.instances or config.get("instances", ["very_small"])
    time_limit = float(args.time_limit if args.time_limit is not None else config.get("time_limit", 3600))
    max_nodes = int(args.max_nodes if args.max_nodes is not None else config.get("max_nodes", 100000))
    max_columns_per_pricing = int(
        args.max_columns_per_pricing
        if args.max_columns_per_pricing is not None
        else config.get("max_columns_per_pricing", 200)
    )
    memory_limit_mb = (
        float(args.memory_limit_mb)
        if args.memory_limit_mb is not None
        else (float(config["memory_limit_mb"]) if config.get("memory_limit_mb") is not None else None)
    )
    results_csv = ROOT / (args.results_csv or config.get("results_csv", "results/bp_no_ml.csv"))
    log_dir = ROOT / (args.log_dir or config.get("log_dir", "results/logs/bp_no_ml"))
    solution_dir = ROOT / (args.solution_dir or "results/solutions/bp_no_ml")
    instance_dir = config.get("instance_dir", "json/instances")
    seed = config.get("random_seed")
    if args.quiet:
        log_level = "quiet"
    elif args.scip_log:
        log_level = "scip"
    else:
        log_level = str(config.get("log_level", "progress"))
    rows = []

    for name in instances:
        instance, instance_path = load_or_build_instance(
            str(name),
            instance_dir=instance_dir,
            write_if_missing=bool(config.get("write_instance_json", True)),
        )
        pairwise = build_task_closure(instance, weight="cost")
        log_path = log_dir / f"{instance['name']}.log"
        solution_path = solution_dir / f"solution_{instance['name']}.json"
        print(
            f"开始 no-ML B&P: instance={instance['name']}, tasks={len(instance['tasks'])}, "
            f"time_limit={time_limit:g}s, memory_limit_mb={memory_limit_mb}, log={log_path}",
            flush=True,
        )
        result = solve_bp_no_ml(
            instance,
            pairwise,
            instance_path=instance_path,
            time_limit=time_limit,
            log_path=log_path,
            solution_path=solution_path,
            pricing_eps=float(config.get("pricing_eps", 1.0e-6)),
            integer_tol=float(config.get("integer_tol", 1.0e-6)),
            max_nodes=max_nodes,
            max_cg_iterations_per_node=int(config.get("max_cg_iterations_per_node", 200)),
            max_columns_per_pricing=max_columns_per_pricing,
            memory_limit_mb=memory_limit_mb,
            artificial_penalty=float(config.get("artificial_penalty", 1.0e6)),
            rmp_params=dict(config.get("rmp_params", {})),
            seed=int(seed) if seed is not None else None,
            log_level=log_level,
        )
        rows.append(result.to_row())
        print(
            f"{result.instance}: status={result.status}, primal={result.primal_bound}, "
            f"dual={result.dual_bound}, gap={result.gap}, time={result.solving_time}s, "
            f"nodes={result.node_count}, columns={result.generated_columns}"
        )

    _write_rows(results_csv, rows)
    print(f"no-ML B&P CSV 已写入：{results_csv}")


if __name__ == "__main__":
    main()
