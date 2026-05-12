#!/usr/bin/env python3
"""中文摘要：本脚本运行根目录 bpc/ 下的 clean Branch-Price-and-Cut 主线，并输出 CSV、JSONL 日志和解文件。"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bpc.data import load_bpc_data
from bpc.solver import BPCResult, solve_bpc_clean
from gnn_bb.baseline.config import load_config
from gnn_bb.data.io_utils import ensure_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行根目录 bpc/ clean Branch-Price-and-Cut。")
    parser.add_argument("--config", default="configs/bpc_clean.yaml")
    parser.add_argument("--instances", nargs="*", help="覆盖配置中的实例列表")
    parser.add_argument("--time-limit", type=float, help="覆盖配置时间限制")
    parser.add_argument("--max-nodes", type=int, help="覆盖最大处理节点数")
    parser.add_argument("--results-csv", default="results/bpc_clean.csv")
    parser.add_argument("--log-dir", default="results/logs/bpc_clean")
    parser.add_argument("--solution-dir", default="results/solutions/bpc_clean")
    parser.add_argument("--quiet", action="store_true", help="关闭 clean BPC 控制台进度")
    return parser.parse_args()


def _write_rows(path: Path, rows: list[dict]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(BPCResult.__dataclass_fields__.keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    instances = args.instances or config.get("instances", ["very_small"])
    time_limit = float(args.time_limit if args.time_limit is not None else config.get("time_limit", 3600))
    max_nodes = int(args.max_nodes if args.max_nodes is not None else config.get("max_nodes", 100000))
    rows = []
    for name in instances:
        data = load_bpc_data(str(name), instance_dir=config.get("instance_dir", "json/instances"))
        log_path = ROOT / args.log_dir / f"{data.name}.jsonl"
        solution_path = ROOT / args.solution_dir / f"solution_{data.name}.json"
        print(
            f"开始 clean BPC: instance={data.name}, tasks={len(data.tasks)}, vehicles={len(data.vehicles)}, "
            f"time_limit={time_limit:g}s, max_nodes={max_nodes}, log={log_path}",
            flush=True,
        )
        result = solve_bpc_clean(
            data,
            time_limit=time_limit,
            max_nodes=max_nodes,
            pricing_eps=float(config.get("pricing_eps", 1.0e-6)),
            integer_tol=float(config.get("integer_tol", 1.0e-6)),
            max_routes_per_pricing=int(config.get("max_routes_per_pricing", 200)),
            max_labels_per_pricing=int(config.get("max_labels_per_pricing", 0) or 0),
            rmp_params=dict(config.get("rmp_params", {})),
            log_path=log_path,
            solution_path=solution_path,
            seed=int(config["random_seed"]) if config.get("random_seed") is not None else None,
            quiet=bool(args.quiet or config.get("log_level", "progress") == "quiet"),
            branching_strategy=str(config.get("branching_strategy", "3pb")),
            three_pb_pseudocost_candidates=int(config.get("three_pb_pseudocost_candidates", 6)),
            three_pb_fractional_candidates=int(config.get("three_pb_fractional_candidates", 6)),
            three_pb_lp_candidates=int(config.get("three_pb_lp_candidates", 3)),
            three_pb_heuristic_cg_iterations=int(config.get("three_pb_heuristic_cg_iterations", 3)),
            three_pb_heuristic_routes_per_iter=int(config.get("three_pb_heuristic_routes_per_iter", 50)),
            three_pb_heuristic_max_labels=int(config.get("three_pb_heuristic_max_labels", 800)),
        )
        rows.append(result.to_row())
        print(
            f"{result.instance}: status={result.status}, primal={result.primal_bound}, dual={result.dual_bound}, "
            f"gap={result.gap}, time={result.solving_time}s, nodes={result.node_count}, "
            f"rmp={result.rmp_solves}, pricing={result.pricing_calls}, routes={result.generated_routes}, cuts={result.cuts_added}",
            flush=True,
        )
    output = ROOT / args.results_csv
    _write_rows(output, rows)
    print(f"clean BPC CSV 已写入：{output}", flush=True)


if __name__ == "__main__":
    main()
