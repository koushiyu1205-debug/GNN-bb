"""中文摘要：本文件是严格分支定价模型的主入口，负责串联实例生成、地形闭包、SCIP 求解、校验和结果输出。"""

import argparse
import time

from src.instance_data import build_instance
from src.branch_price import solve_branch_price
from src.io_utils import ensure_dir, log, project_path, write_json
from src.terrain import build_task_closure
from src.validation import validate_solution


def parse_args():
    parser = argparse.ArgumentParser(description="地形 CVRPTW 的严格分支定价模型。")
    parser.add_argument("--instance", default="very_small", choices=["very_small", "medium", "30", "40", "50", "100"])
    parser.add_argument("--time-limit", type=float, default=3600.0)
    parser.add_argument("--pricing-eps", type=float, default=1.0e-6, help="判断负 reduced cost 的容差")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--plot", action="store_true", help="求解后输出任务层路径图和底层地形路径图")
    parser.add_argument("--no-warm-start", dest="warm_start", action="store_false", help="关闭贪心 warm start 初始化")
    parser.set_defaults(warm_start=True)
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument("--verbose", dest="verbose", action="store_true", default=True, help="显示 SCIP 求解日志（默认）")
    verbosity.add_argument("--quiet", dest="verbose", action="store_false", help="隐藏 SCIP 求解日志")
    return parser.parse_args()


def timed(label, func):
    started = time.perf_counter()
    result = func()
    elapsed = time.perf_counter() - started
    log(f"{label}: {elapsed:.3f}s")
    return result


def main():
    args = parse_args()
    output_dir = ensure_dir(project_path(args.output_dir))

    instance = timed("生成实例", lambda: build_instance(args.instance))
    instance_path = output_dir / f"instance_{args.instance}.json"
    write_json(instance_path, instance)
    log(f"实例文件已写入 {instance_path}")

    pairwise = timed("计算任务点最短路闭包", lambda: build_task_closure(instance, weight="cost"))
    routes, route_report, solution = timed(
        "严格分支定价求解",
        lambda: solve_branch_price(
            instance,
            pairwise,
            time_limit=args.time_limit,
            verbose=args.verbose,
            eps=args.pricing_eps,
            warm_start=args.warm_start,
        ),
    )

    route_path = output_dir / f"routes_{args.instance}.json"
    write_json(route_path, {"report": route_report, "routes": routes})
    log(f"列文件已写入 {route_path}")
    log(f"列生成摘要：{route_report}")
    validation = validate_solution(instance, routes, solution)
    solution["route_generation"] = route_report
    solution["validation"] = validation

    solution_path = output_dir / f"solution_{args.instance}.json"
    write_json(solution_path, solution)
    log(f"解文件已写入 {solution_path}")

    if args.plot and solution["summary"]["solution_count"] > 0:
        from src.plotting import plot_task_routes, plot_terrain_routes

        task_plot_path = output_dir / f"task_routes_{args.instance}.png"
        terrain_plot_path = output_dir / f"terrain_routes_{args.instance}.png"
        plot_task_routes(instance, routes, solution, task_plot_path)
        plot_terrain_routes(instance, routes, solution, terrain_plot_path)
        log(f"任务层路径图已写入 {task_plot_path}")
        log(f"底层地形路径图已写入 {terrain_plot_path}")

    log(f"SCIP 摘要：{solution['summary']}")
    log(f"校验结果：{validation}")


if __name__ == "__main__":
    main()
