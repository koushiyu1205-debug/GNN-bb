#!/usr/bin/env python3
"""中文摘要：本脚本运行最小 route-vehicle branch-price-and-cut。它在 route-vehicle 分支定价外层加入真实车辆日程可行性 cut，并输出 CSV、日志和解文件。"""

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
from gnn_bb.bp.route_vehicle_bpc import BPResult, solve_bpc_no_ml
from gnn_bb.data.instances import load_or_build_instance
from gnn_bb.data.io_utils import ensure_dir
from gnn_bb.data.terrain import build_task_closure


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 route-vehicle branch-price-and-cut baseline。")
    parser.add_argument("--config", default="configs/bp_no_ml.yaml")
    parser.add_argument("--instances", nargs="*", help="覆盖配置中的实例列表")
    parser.add_argument("--time-limit", type=float, help="覆盖配置中的时间限制")
    parser.add_argument("--results-csv", default="results/bpc_no_ml.csv", help="CSV 输出路径")
    parser.add_argument("--log-dir", default="results/logs/bpc_no_ml", help="日志输出目录")
    parser.add_argument("--solution-dir", default="results/solutions/bpc_no_ml", help="解文件输出目录")
    parser.add_argument("--max-nodes", type=int, help="覆盖每轮 B&P 的最大搜索节点数")
    parser.add_argument("--max-cut-rounds", type=int, default=20, help="最多执行多少轮 cut-and-resolve")
    parser.add_argument("--memory-limit-mb", type=float, help="覆盖求解进程内存保护阈值，单位 MB")
    parser.add_argument("--pricing-time-budget", type=float, default=None, help="单次 Python pricing 回调预算，单位秒；超时会安全中断并清空 dual/gap")
    parser.add_argument("--pricing-progress-interval", type=int, default=None, help="pricing 每弹出多少个 label 打印一次进度；0 表示关闭")
    parser.add_argument("--disable-schedule-start", action="store_true", help="关闭 schedule-aware 初始可行解启发式")
    parser.add_argument("--enable-tree-cuts", action="store_true", help="启用 SCIP 树内 lazy schedule cuts；当前仍是实验选项")
    parser.add_argument("--disable-tree-cuts", action="store_true", help="兼容旧命令：关闭 SCIP 树内 lazy schedule cuts")
    parser.add_argument("--quiet", action="store_true", help="关闭 SCIP 控制台日志")
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
    memory_limit_mb = (
        float(args.memory_limit_mb)
        if args.memory_limit_mb is not None
        else (float(config["memory_limit_mb"]) if config.get("memory_limit_mb") is not None else None)
    )
    pricing_time_budget = (
        float(args.pricing_time_budget)
        if args.pricing_time_budget is not None
        else float(config.get("bpc_pricing_time_budget_sec", 0.0) or 0.0)
    )
    pricing_progress_interval = (
        int(args.pricing_progress_interval)
        if args.pricing_progress_interval is not None
        else int(config.get("bpc_pricing_progress_interval", 0) or 0)
    )
    tree_schedule_cuts = bool(args.enable_tree_cuts) and not bool(args.disable_tree_cuts)
    rows = []
    for name in instances:
        instance, instance_path = load_or_build_instance(
            str(name),
            instance_dir=config.get("instance_dir", "json/instances"),
            write_if_missing=bool(config.get("write_instance_json", True)),
        )
        pairwise = build_task_closure(instance, weight="cost")
        log_path = ROOT / args.log_dir / f"{instance['name']}.log"
        solution_path = ROOT / args.solution_dir / f"solution_{instance['name']}.json"
        print(
            f"开始 route-vehicle BPC: instance={instance['name']}, tasks={len(instance['tasks'])}, "
            f"time_limit={time_limit:g}s, max_cut_rounds={args.max_cut_rounds}, "
            f"memory_limit_mb={memory_limit_mb}, pricing_time_budget={pricing_time_budget:g}, "
            f"pricing_progress_interval={pricing_progress_interval}, tree_schedule_cuts={tree_schedule_cuts}, log={log_path}",
            flush=True,
        )
        result = solve_bpc_no_ml(
            instance,
            pairwise,
            instance_path=instance_path,
            time_limit=time_limit,
            log_path=log_path,
            solution_path=solution_path,
            pricing_eps=float(config.get("pricing_eps", 1.0e-6)),
            integer_tol=float(config.get("integer_tol", 1.0e-6)),
            max_nodes=max_nodes,
            max_cut_rounds=int(args.max_cut_rounds),
            memory_limit_mb=memory_limit_mb,
            artificial_penalty=float(config.get("artificial_penalty", 1.0e6)),
            rmp_params=dict(config.get("rmp_params", {})),
            seed=int(config["random_seed"]) if config.get("random_seed") is not None else None,
            log_level="quiet" if args.quiet else str(config.get("log_level", "progress")),
            tree_schedule_cuts=tree_schedule_cuts,
            pricing_time_budget=pricing_time_budget,
            pricing_progress_interval=pricing_progress_interval,
            schedule_start=not args.disable_schedule_start,
        )
        rows.append(result.to_row())
        print(
            f"{result.instance}: status={result.status}, primal={result.primal_bound}, "
            f"dual={result.dual_bound}, gap={result.gap}, time={result.solving_time}s, "
            f"rounds={result.rmp_solves}, columns={result.generated_columns}"
        )
    output = ROOT / args.results_csv
    _write_rows(output, rows)
    print(f"route-vehicle BPC CSV 已写入：{output}")


if __name__ == "__main__":
    main()
