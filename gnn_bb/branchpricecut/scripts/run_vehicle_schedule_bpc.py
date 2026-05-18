#!/usr/bin/env python3
"""中文摘要：运行 branchpricecut vehicle-schedule BPC，并把结果写入 branchpricecut/results。"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
BRANCHPRICECUT_ROOT = SCRIPT.parents[1]
REPO_ROOT = SCRIPT.parents[2]
SRC = REPO_ROOT / "src"
for path in (REPO_ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from branchpricecut.data import load_instance
from branchpricecut.solver import SolverResult, solve_vehicle_schedule_bpc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 vehicle-schedule Branch-Price-and-Cut。")
    parser.add_argument("--config", default=str(BRANCHPRICECUT_ROOT / "config" / "default.json"))
    parser.add_argument("--instances", nargs="*", help="覆盖 config 中的实例列表")
    parser.add_argument("--time-limit", type=float, help="覆盖时间限制")
    parser.add_argument("--max-nodes", type=int, help="覆盖最大节点数")
    parser.add_argument("--run-id", default=None, help="输出 run id；默认使用当前时间戳")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> None:
    from datetime import datetime

    args = parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if args.time_limit is not None:
        config["time_limit"] = float(args.time_limit)
    if args.max_nodes is not None:
        config["max_nodes"] = int(args.max_nodes)
    master_type = str(config.get("master_type", "hybrid_route"))
    instances = args.instances or config.get("instances", ["very_small"])
    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S_vehicle_schedule_bpc")
    run_root = BRANCHPRICECUT_ROOT / "results" / run_id
    log_dir = run_root / "logs"
    solution_dir = run_root / "solutions"
    summary_path = run_root / "summary.csv"
    run_root.mkdir(parents=True, exist_ok=True)

    rows = []
    for instance_name in instances:
        data = load_instance(str(instance_name), instance_dir=config.get("instance_dir", "json/instances"))
        log_path = log_dir / f"{data.name}.jsonl"
        solution_path = solution_dir / f"solution_{data.name}.json"
        print(
            f"开始 branchpricecut BPC: master_type={master_type}, instance={data.name}, tasks={len(data.tasks)}, "
            f"vehicles={data.vehicle_count}, time_limit={config['time_limit']}s, log={log_path}",
            flush=True,
        )
        result = solve_vehicle_schedule_bpc(data, config=config, log_path=log_path, solution_path=solution_path, quiet=args.quiet)
        rows.append(result.to_row())
        print(
            f"{result.instance}: status={result.status}, primal={result.primal_bound}, dual={result.dual_bound}, "
            f"gap={result.gap}, time={result.solving_time}s, nodes={result.node_count}, "
            f"rmp={result.rmp_solves}, pricing={result.pricing_calls}, labels={result.label_pops}, "
            f"generated_labels={result.generated_labels}, queue_peak={result.pricing_queue_peak}",
            flush=True,
        )

    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SolverResult.__dataclass_fields__.keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"summary 已写入：{summary_path}", flush=True)


if __name__ == "__main__":
    main()
