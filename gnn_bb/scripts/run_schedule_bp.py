#!/usr/bin/env python3
"""中文摘要：本脚本运行真实 vehicle schedule column master 的 no-ML 分支定价，用于和 route-vehicle baseline 比较求解难度。"""

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
from gnn_bb.bp.vehicle_schedule_branch_price import BPResult, solve_bp_no_ml
from gnn_bb.data.instances import load_or_build_instance
from gnn_bb.data.io_utils import ensure_dir
from gnn_bb.data.terrain import build_task_closure


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行真实 vehicle schedule column master 分支定价。")
    parser.add_argument("--config", default="configs/bp_no_ml.yaml")
    parser.add_argument("--instances", nargs="*", help="覆盖配置中的实例列表")
    parser.add_argument("--time-limit", type=float, help="覆盖配置中的时间限制")
    parser.add_argument("--results-csv", default="results/bp_schedule.csv", help="CSV 输出路径")
    parser.add_argument("--log-dir", default="results/logs/bp_schedule", help="日志输出目录")
    parser.add_argument("--solution-dir", default="results/solutions/bp_schedule", help="解文件输出目录")
    parser.add_argument("--max-nodes", type=int, help="覆盖配置中的最大搜索节点数")
    parser.add_argument("--max-columns-per-pricing", type=int, help="每次 schedule pricing 最多返回的负 reduced-cost 日程列数")
    parser.add_argument("--column-pool-size", type=int, help="schedule column pool 最大保存列数；0 表示关闭 pool")
    parser.add_argument("--column-pool-rc-margin", type=float, help="只缓存 reduced cost 不超过该阈值的候选 schedule")
    parser.add_argument("--disable-stabilized-pricing", action="store_true", help="关闭 heuristic stabilized pricing，只保留 exact pricing")
    parser.add_argument("--stabilization-alpha", type=float, help="初始 pi_stab = alpha*pi_current + (1-alpha)*pi_center 的 alpha")
    parser.add_argument("--stabilization-label-limit", type=int, help="stabilized heuristic pricing 的标签弹出上限")
    parser.add_argument("--disable-pricing-preprocess", action="store_true", help="关闭 pricing 前的确定性连接预处理，用于 ablation")
    parser.add_argument("--memory-limit-mb", type=float, help="覆盖求解进程内存保护阈值，单位 MB")
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
    max_columns_per_pricing = int(
        args.max_columns_per_pricing
        if args.max_columns_per_pricing is not None
        else config.get("schedule_max_columns_per_pricing", 20)
    )
    column_pool_size = int(
        args.column_pool_size if args.column_pool_size is not None else config.get("schedule_column_pool_size", 200)
    )
    column_pool_rc_margin = float(
        args.column_pool_rc_margin
        if args.column_pool_rc_margin is not None
        else config.get("schedule_column_pool_rc_margin", 50.0)
    )
    stabilized_pricing = bool(config.get("schedule_stabilized_pricing", True)) and not args.disable_stabilized_pricing
    pricing_preprocess = bool(config.get("schedule_pricing_preprocess", True)) and not args.disable_pricing_preprocess
    stabilization_alpha = float(
        args.stabilization_alpha
        if args.stabilization_alpha is not None
        else config.get("schedule_stabilization_alpha", 0.7)
    )
    stabilization_label_limit = int(
        args.stabilization_label_limit
        if args.stabilization_label_limit is not None
        else config.get("schedule_stabilization_label_limit", 20000)
    )
    memory_limit_mb = (
        float(args.memory_limit_mb)
        if args.memory_limit_mb is not None
        else (float(config["memory_limit_mb"]) if config.get("memory_limit_mb") is not None else None)
    )
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
            f"开始 schedule B&P: instance={instance['name']}, tasks={len(instance['tasks'])}, "
            f"time_limit={time_limit:g}s, max_columns_per_pricing={max_columns_per_pricing}, "
            f"column_pool_size={column_pool_size}, column_pool_rc_margin={column_pool_rc_margin:g}, "
            f"stabilized_pricing={stabilized_pricing}, stabilization_alpha={stabilization_alpha:g}, "
            f"stabilization_label_limit={stabilization_label_limit}, "
            f"pricing_preprocess={pricing_preprocess}, "
            f"memory_limit_mb={memory_limit_mb}, log={log_path}",
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
            max_nodes=max_nodes,
            max_columns_per_pricing=max_columns_per_pricing,
            max_pool_size=column_pool_size,
            pool_score_margin=column_pool_rc_margin,
            stabilized_pricing=stabilized_pricing,
            stabilization_alpha=stabilization_alpha,
            stabilization_min_alpha=float(config.get("schedule_stabilization_min_alpha", 0.2)),
            stabilization_max_alpha=float(config.get("schedule_stabilization_max_alpha", 0.95)),
            stabilization_label_limit=stabilization_label_limit,
            stabilization_volatility_threshold=float(config.get("schedule_stabilization_volatility_threshold", 0.25)),
            pricing_preprocess=pricing_preprocess,
            memory_limit_mb=memory_limit_mb,
            rmp_params=dict(config.get("rmp_params", {})),
            seed=int(config["random_seed"]) if config.get("random_seed") is not None else None,
            log_level="quiet" if args.quiet else str(config.get("log_level", "progress")),
        )
        rows.append(result.to_row())
        print(
            f"{result.instance}: status={result.status}, primal={result.primal_bound}, "
            f"dual={result.dual_bound}, gap={result.gap}, time={result.solving_time}s, "
            f"nodes={result.node_count}, columns={result.generated_columns}"
        )
    output = ROOT / args.results_csv
    _write_rows(output, rows)
    print(f"schedule B&P CSV 已写入：{output}")


if __name__ == "__main__":
    main()
