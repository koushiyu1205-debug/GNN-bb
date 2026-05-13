#!/usr/bin/env python3
"""中文摘要：诊断 clean BPC 根节点 LP 的 fractional 结构。脚本只跑 root column generation，然后分析 split、branching 候选和 cut violation。"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from itertools import combinations
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bpc.branching import generate_branch_candidates
from bpc.columns import RouteColumn, RoutePool, evaluate_route, route_work_time_lower_bound
from bpc.cuts import CrossingCut, capacity_route_lower_bound, rounded_capacity_rhs
from bpc.data import BPCData, load_bpc_data
from bpc.pricing import exact_pricing
from bpc.rmp import RMPSolution, solve_rmp_lp
from bpc.logger import BPCLogger
from bpc.tree import CleanBPCTree
from gnn_bb.baseline.config import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="诊断 clean BPC 根节点 LP fractional 结构。")
    parser.add_argument("--instance", default="medium")
    parser.add_argument("--config", default="configs/bpc_clean.yaml")
    parser.add_argument("--subset-max-size", type=int, default=6)
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--output", help="输出 JSON 路径；默认写入 results/root_diagnostics。")
    return parser.parse_args()


def _round(value: Any, digits: int = 6) -> Any:
    if value is None:
        return None
    if isinstance(value, float):
        return round(value, digits)
    return value


def _route_json(route: RouteColumn, vehicle: int, value: float) -> dict[str, Any]:
    return {
        "route_id": route.id,
        "vehicle": int(vehicle),
        "value": _round(value, 9),
        "tasks": list(route.tasks),
        "cost": _round(route.cost),
        "load": _round(route.load),
        "work_time_lb": _round(route_work_time_lower_bound(_DATA_FOR_ROUTE_JSON, route)) if _DATA_FOR_ROUTE_JSON else None,
    }


_DATA_FOR_ROUTE_JSON: BPCData | None = None


def build_initial_pool(data: BPCData, config: dict[str, Any]) -> RoutePool:
    # 中文注释：复用正式 solver 的初始化逻辑，包含 singleton routes 和 greedy warm-start routes。
    logger = BPCLogger(None, console=False)
    try:
        tree = CleanBPCTree(
            data,
            time_limit=1.0e9,
            max_nodes=1,
            eps=float(config.get("pricing_eps", 1.0e-6)),
            integer_tol=float(config.get("integer_tol", 1.0e-6)),
            max_routes_per_pricing=int(config.get("max_routes_per_pricing", 200)),
            max_labels_per_pricing=int(config.get("max_labels_per_pricing", 0) or 0),
            rmp_params=dict(config.get("rmp_params", {})),
            logger=logger,
            branching_strategy=str(config.get("branching_strategy", "3pb")),
        )
        tree.initialize()
        return tree.pool
    finally:
        logger.close()


def run_root_column_generation(data: BPCData, config: dict[str, Any]) -> tuple[RoutePool, RMPSolution, list[dict[str, Any]]]:
    pool = build_initial_pool(data, config)

    phase = "phase1"
    iterations: list[dict[str, Any]] = []
    eps = float(config.get("pricing_eps", 1.0e-6))
    max_routes = int(config.get("max_routes_per_pricing", 200))
    max_labels = int(config.get("max_labels_per_pricing", 0) or 0)
    rmp_params = dict(config.get("rmp_params", {}))
    solution: RMPSolution | None = None

    for cg_iter in range(1, 100000):
        solution = solve_rmp_lp(
            data,
            pool.routes,
            cuts=[],
            branch_constraints=tuple(),
            phase=phase,
            rmp_params=rmp_params,
            verbose=False,
        )
        if not solution.optimal or solution.duals is None:
            raise RuntimeError(f"root RMP 未能最优求解: phase={phase}, status={solution.status}")
        iterations.append(
            {
                "iteration": cg_iter,
                "phase": phase,
                "rmp_objective": _round(solution.objective),
                "artificial_sum": _round(solution.artificial_sum),
                "route_pool_size": len(pool.routes),
            }
        )

        if phase == "phase1" and solution.artificial_sum <= float(config.get("integer_tol", 1.0e-6)):
            phase = "phase2"
            continue

        pricing = exact_pricing(
            data,
            pool.routes,
            solution.duals,
            cuts=[],
            branch_constraints=tuple(),
            phase=phase,
            eps=eps,
            max_routes_to_return=max_routes,
            max_labels=max_labels,
        )
        added = 0
        for route in pricing.routes:
            before = len(pool.routes)
            pool.add(route)
            if len(pool.routes) > before:
                added += 1
        iterations[-1].update(
            {
                "best_reduced_cost": None if pricing.best_reduced_cost is None else _round(pricing.best_reduced_cost, 9),
                "negative_routes": pricing.negative_routes,
                "added_routes": added,
                "exhausted": pricing.exhausted,
                "label_pops": pricing.label_pops,
                "generated_labels": pricing.generated_labels,
            }
        )
        if added:
            continue
        if not pricing.exhausted:
            raise RuntimeError("root pricing 未完整结束，不能诊断 full root LP。")
        if phase == "phase1":
            raise RuntimeError("Phase-I 完整 pricing 后仍不可行。")
        assert solution is not None
        return pool, solution, iterations

    raise RuntimeError("root column generation 迭代数异常。")


def route_crossing_activity(cut, solution: RMPSolution) -> float:
    return sum(cut.coefficient(route, vehicle) * value for route, vehicle, value in solution.route_values)


def pair_route_compatible(data: BPCData, left: int, right: int) -> bool:
    return evaluate_route(data, (left, right)) is not None or evaluate_route(data, (right, left)) is not None


def build_pair_incompatibilities(data: BPCData) -> set[tuple[int, int]]:
    incompatible = set()
    for index, left in enumerate(data.tasks):
        for right in data.tasks[index + 1 :]:
            if not pair_route_compatible(data, int(left), int(right)):
                incompatible.add((int(left), int(right)))
    return incompatible


def clique_lower_bound(adjacency: list[int]) -> int:
    n = len(adjacency)
    best = 1 if n else 0
    for mask in range(1, 1 << n):
        size = mask.bit_count()
        if size <= best:
            continue
        if all((mask & ~(1 << i)) & ~adjacency[i] == 0 for i in range(n) if mask & (1 << i)):
            best = size
    return best


def can_color(order: list[int], adjacency: list[int], color_count: int) -> bool:
    color_masks = [0 for _ in range(color_count)]

    def search(position: int) -> bool:
        if position == len(order):
            return True
        vertex = order[position]
        tried_empty = False
        for color in range(color_count):
            if color_masks[color] == 0:
                if tried_empty:
                    continue
                tried_empty = True
            if adjacency[vertex] & color_masks[color]:
                continue
            color_masks[color] |= 1 << vertex
            if search(position + 1):
                return True
            color_masks[color] &= ~(1 << vertex)
        return False

    return search(0)


def exact_chromatic_bound(tasks: tuple[int, ...], incompatible: set[tuple[int, int]]) -> int:
    tasks = tuple(sorted(tasks))
    index_of = {task: index for index, task in enumerate(tasks)}
    adjacency = [0 for _ in tasks]
    for left, right in incompatible:
        if left not in index_of or right not in index_of:
            continue
        i = index_of[left]
        j = index_of[right]
        adjacency[i] |= 1 << j
        adjacency[j] |= 1 << i
    degrees = [adjacency[index].bit_count() for index in range(len(tasks))]
    order = sorted(range(len(tasks)), key=lambda index: (-degrees[index], tasks[index]))
    for color_count in range(max(1, clique_lower_bound(adjacency)), len(tasks) + 1):
        if can_color(order, adjacency, color_count):
            return color_count
    return len(tasks)


def diagnose_cut_violations(data: BPCData, solution: RMPSolution, subset_max_size: int, top: int) -> dict[str, Any]:
    max_size = min(subset_max_size, len(data.tasks))
    rci_positive = []
    rci_best = None
    incompatible = build_pair_incompatibilities(data)
    k_positive = []
    k_best = None
    stronger_k_subsets = 0

    for size in range(2, max_size + 1):
        for subset in combinations(data.tasks, size):
            tasks = tuple(sorted(int(task) for task in subset))
            demand = sum(data.task_value(task, "d") for task in tasks)
            capacity_bound = capacity_route_lower_bound(data, tasks)

            if demand > data.capacity + 1.0e-9:
                rhs = rounded_capacity_rhs(data, tasks)
                cut = CrossingCut(
                    id=-1,
                    tasks=tasks,
                    rhs=rhs,
                    k_bound=int(rhs // 2),
                    capacity_bound=capacity_bound,
                    resource_bound=1,
                    demand=demand,
                    capacity=data.capacity,
                )
                activity = route_crossing_activity(cut, solution)
                violation = rhs - activity
                item = {
                    "tasks": list(tasks),
                    "size": len(tasks),
                    "demand": _round(demand),
                    "rhs": _round(rhs),
                    "activity": _round(activity, 9),
                    "violation": _round(violation, 9),
                }
                if rci_best is None or violation > rci_best["violation_raw"]:
                    rci_best = {**item, "violation_raw": violation}
                if violation > 1.0e-6:
                    rci_positive.append(item)

            chromatic_bound = exact_chromatic_bound(tasks, incompatible)
            k_bound = max(capacity_bound, chromatic_bound)
            if k_bound <= capacity_bound:
                continue
            stronger_k_subsets += 1
            rhs = float(2 * k_bound)
            cut = CrossingCut(
                id=-1,
                tasks=tasks,
                rhs=rhs,
                k_bound=k_bound,
                capacity_bound=capacity_bound,
                resource_bound=chromatic_bound,
                demand=demand,
                capacity=data.capacity,
            )
            activity = route_crossing_activity(cut, solution)
            violation = rhs - activity
            item = {
                "tasks": list(tasks),
                "size": len(tasks),
                "demand": _round(demand),
                "capacity_bound": capacity_bound,
                "chromatic_bound": chromatic_bound,
                "k_bound": k_bound,
                "rhs": _round(rhs),
                "activity": _round(activity, 9),
                "violation": _round(violation, 9),
            }
            if k_best is None or violation > k_best["violation_raw"]:
                k_best = {**item, "violation_raw": violation}
            if violation > 1.0e-6:
                k_positive.append(item)

    rci_positive.sort(key=lambda item: (-item["violation"], item["size"], item["tasks"]))
    k_positive.sort(key=lambda item: (-item["violation"], item["size"], item["tasks"]))
    if rci_best is not None:
        rci_best.pop("violation_raw", None)
    if k_best is not None:
        k_best.pop("violation_raw", None)
    return {
        "pair_incompatibility_edges": len(incompatible),
        "pair_possible_edges": len(data.tasks) * (len(data.tasks) - 1) // 2,
        "rci": {
            "violated_count": len(rci_positive),
            "best_candidate": rci_best,
            "top_violated": rci_positive[:top],
        },
        "k_path_resource": {
            "stronger_than_capacity_subset_count": stronger_k_subsets,
            "violated_count": len(k_positive),
            "best_candidate": k_best,
            "top_violated": k_positive[:top],
        },
    }


def diagnose_fractional_structure(data: BPCData, pool: RoutePool, solution: RMPSolution, top: int) -> dict[str, Any]:
    tol = 1.0e-6
    route_values = solution.route_values
    fractional_routes = [
        _route_json(route, vehicle, value)
        for route, vehicle, value in sorted(route_values, key=lambda item: (-min(item[2], 1 - item[2]), -item[2]))
        if tol < value < 1.0 - tol
    ]

    vehicle_rows = []
    for vehicle in data.vehicles:
        used_routes = [(route, value) for route, route_vehicle, value in route_values if int(route_vehicle) == int(vehicle)]
        sortie_mass = sum(value for _route, value in used_routes)
        work_mass = sum(route_work_time_lower_bound(data, route) * value for route, value in used_routes)
        vehicle_rows.append(
            {
                "vehicle": int(vehicle),
                "y": _round(solution.y_values.get(vehicle, 0.0), 9),
                "sortie_mass": _round(sortie_mass, 9),
                "sortie_limit_rhs": _round(data.sortie_limit * solution.y_values.get(vehicle, 0.0), 9),
                "work_mass": _round(work_mass, 9),
                "work_limit_rhs": _round(data.horizon * solution.y_values.get(vehicle, 0.0), 9),
                "nonzero_route_count": len(used_routes),
            }
        )

    task_splits = []
    max_link_violation = -float("inf")
    for task in data.tasks:
        values = {}
        for vehicle in data.vehicles:
            value = sum(
                route_value
                for route, route_vehicle, route_value in route_values
                if int(route_vehicle) == int(vehicle) and int(task) in route.task_set
            )
            values[str(vehicle)] = value
            max_link_violation = max(max_link_violation, value - solution.y_values.get(vehicle, 0.0))
        sorted_values = sorted(values.items(), key=lambda item: -item[1])
        positive = [(vehicle, value) for vehicle, value in sorted_values if value > tol]
        entropy = -sum(value * math.log(max(value, 1.0e-12)) for _vehicle, value in positive)
        task_splits.append(
            {
                "task": int(task),
                "vehicle_values": {vehicle: _round(value, 9) for vehicle, value in sorted_values},
                "positive_vehicle_count": len(positive),
                "max_vehicle_value": _round(sorted_values[0][1], 9),
                "entropy": _round(entropy, 9),
            }
        )
    task_splits.sort(key=lambda item: (-item["positive_vehicle_count"], item["max_vehicle_value"], -item["entropy"], item["task"]))

    pair_values = {}
    for left, right in combinations(data.tasks, 2):
        pair_values[(int(left), int(right))] = 0.0
    for route, _vehicle, value in route_values:
        for pair in combinations(sorted(route.task_set), 2):
            pair_values[pair] = pair_values.get(pair, 0.0) + value
    fractional_pairs = [
        {
            "pair": list(pair),
            "value": _round(value, 9),
            "fractionality": _round(0.5 - abs(value - 0.5), 9),
        }
        for pair, value in pair_values.items()
        if tol < value < 1.0 - tol
    ]
    fractional_pairs.sort(key=lambda item: (-item["fractionality"], item["pair"]))

    arc_values = {}
    for route, _vehicle, value in route_values:
        for tail, head in zip(route.tasks[:-1], route.tasks[1:]):
            key = (int(tail), int(head))
            arc_values[key] = arc_values.get(key, 0.0) + value
    fractional_arcs = [
        {
            "arc": list(arc),
            "value": _round(value, 9),
            "fractionality": _round(0.5 - abs(value - 0.5), 9),
        }
        for arc, value in arc_values.items()
        if tol < value < 1.0 - tol
    ]
    fractional_arcs.sort(key=lambda item: (-item["fractionality"], item["arc"]))

    candidates = generate_branch_candidates(
        data,
        solution.route_values,
        solution.y_values,
        constraints=tuple(),
        tol=tol,
    )
    candidate_counts = {}
    for candidate in candidates:
        candidate_counts[candidate.kind] = candidate_counts.get(candidate.kind, 0) + 1

    return {
        "objective": _round(solution.objective),
        "route_pool_size": len(pool.routes),
        "support_route_vehicle_variables": len(route_values),
        "fractional_route_vehicle_variables": len(fractional_routes),
        "fractional_y_count": sum(1 for value in solution.y_values.values() if tol < value < 1.0 - tol),
        "max_task_vehicle_link_violation": _round(max_link_violation, 12),
        "vehicles": vehicle_rows,
        "top_fractional_routes": fractional_routes[:top],
        "top_task_vehicle_splits": task_splits[:top],
        "fractional_pair_count": len(fractional_pairs),
        "top_fractional_pairs": fractional_pairs[:top],
        "fractional_arc_count": len(fractional_arcs),
        "top_fractional_arcs": fractional_arcs[:top],
        "branch_candidate_counts": dict(sorted(candidate_counts.items())),
    }


def interpretation(diagnostic: dict[str, Any]) -> list[str]:
    messages = []
    cuts = diagnostic["cut_violations"]
    frac = diagnostic["fractional_structure"]
    if cuts["rci"]["violated_count"] == 0:
        messages.append("RCI/RCC 没有起作用的直接原因：当前 root LP 解在枚举范围内没有违反 x(delta(S)) >= 2 ceil(d(S)/Q)。")
    if cuts["k_path_resource"]["violated_count"] == 0:
        messages.append("k-path/resource cut 没有起作用的直接原因：虽然存在资源不兼容 pair，但当前 root LP 解没有违反 x(delta(S)) >= 2 k(S)。")
    if frac["fractional_pair_count"] > 0 or frac["fractional_arc_count"] > 0:
        messages.append("当前 root LP 的主要 fractional 结构集中在任务配对/任务弧选择上，更像 branching 结构问题，而不是容量子集 cut violation。")
    if frac["fractional_route_vehicle_variables"] > 0:
        messages.append("RMP 根节点仍由多个 fractional route-vehicle column 混合覆盖任务；schedule no-good cut 只在整数 route 集不可排程时触发，不能切这类 fractional 解。")
    if frac["max_task_vehicle_link_violation"] <= 1.0e-7:
        messages.append("task-vehicle linking 约束在 root LP 中满足，但没有改变 root bound，说明 fixed vehicle cost 稀释不是当前 root bound 的主要瓶颈。")
    return messages


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    data = load_bpc_data(args.instance, instance_dir=config.get("instance_dir", "json/instances"))

    global _DATA_FOR_ROUTE_JSON
    _DATA_FOR_ROUTE_JSON = data

    pool, solution, iterations = run_root_column_generation(data, config)
    fractional = diagnose_fractional_structure(data, pool, solution, args.top)
    cuts = diagnose_cut_violations(data, solution, args.subset_max_size, args.top)
    diagnostic = {
        "instance": data.name,
        "task_count": len(data.tasks),
        "vehicle_count": len(data.vehicles),
        "sortie_limit": data.sortie_limit,
        "subset_max_size": args.subset_max_size,
        "root_cg_iterations": iterations,
        "fractional_structure": fractional,
        "cut_violations": cuts,
    }
    diagnostic["interpretation"] = interpretation(diagnostic)

    if args.output:
        output = Path(args.output)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = ROOT / "results" / "root_diagnostics" / f"{stamp}_{data.name}_root_fractional.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(diagnostic, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"root diagnostic written: {output}", flush=True)
    print(
        "summary: "
        f"obj={fractional['objective']}, "
        f"routes={fractional['route_pool_size']}, "
        f"support={fractional['support_route_vehicle_variables']}, "
        f"frac_routes={fractional['fractional_route_vehicle_variables']}, "
        f"frac_pairs={fractional['fractional_pair_count']}, "
        f"frac_arcs={fractional['fractional_arc_count']}, "
        f"rci_violated={cuts['rci']['violated_count']}, "
        f"kpath_violated={cuts['k_path_resource']['violated_count']}",
        flush=True,
    )
    for item in diagnostic["interpretation"]:
        print(f"- {item}", flush=True)


if __name__ == "__main__":
    main()
