"""中文摘要：本文件负责生成不同任务规模的测试实例，包括底层地形图、任务参数和车辆参数。"""

import math
import random

from .terrain import build_terrain


def _edge(u, v, speed, energy_rate, cost_rate, time_factor=1.0, energy_factor=1.0, cost_factor=1.0):
    return {
        "u": u,
        "v": v,
        "speed": speed,
        "energy_rate": energy_rate,
        "cost_rate": cost_rate,
        "time_factor": time_factor,
        "energy_factor": energy_factor,
        "cost_factor": cost_factor,
    }


def _demo_terrain():
    node_coords = {
        "p0": (0.0, 0.0),
        "p1": (1.2, 0.7),
        "p2": (2.6, 0.4),
        "p3": (0.8, 2.0),
        "p4": (2.1, 1.8),
        "p5": (3.8, 1.4),
        "p6": (1.4, 3.4),
        "p7": (3.2, 3.0),
        "p8": (4.7, 3.7),
        "p9": (0.2, 4.4),
    }
    edge_specs = [
        _edge("p0", "p1", 1.20, 1.00, 1.00, 1.00, 1.05, 1.00),
        _edge("p0", "p3", 1.00, 1.10, 1.05, 1.10, 1.10, 1.05),
        _edge("p1", "p2", 1.15, 1.05, 1.10, 1.00, 1.00, 1.05),
        _edge("p1", "p4", 0.95, 1.25, 1.15, 1.15, 1.15, 1.10),
        _edge("p2", "p5", 1.10, 1.15, 1.15, 1.05, 1.05, 1.05),
        _edge("p2", "p4", 1.05, 1.10, 1.05, 1.00, 1.00, 1.00),
        _edge("p3", "p4", 1.20, 1.00, 1.00, 1.00, 1.00, 1.00),
        _edge("p3", "p6", 1.00, 1.15, 1.10, 1.10, 1.10, 1.05),
        _edge("p4", "p5", 1.05, 1.10, 1.10, 1.05, 1.05, 1.05),
        _edge("p4", "p7", 0.90, 1.25, 1.20, 1.20, 1.20, 1.15),
        _edge("p5", "p7", 1.10, 1.10, 1.05, 1.00, 1.00, 1.00),
        _edge("p5", "p8", 1.00, 1.20, 1.15, 1.10, 1.10, 1.10),
        _edge("p6", "p7", 1.15, 1.05, 1.05, 1.00, 1.00, 1.00),
        _edge("p6", "p9", 0.95, 1.20, 1.10, 1.10, 1.10, 1.05),
        _edge("p7", "p8", 1.20, 1.00, 1.05, 1.00, 1.00, 1.00),
        _edge("p7", "p9", 1.00, 1.15, 1.10, 1.05, 1.05, 1.05),
    ]
    return build_terrain(node_coords, edge_specs)


def _medium_terrain(seed=20260510):
    rng = random.Random(seed)
    node_coords = {"p0": (0.0, 0.0)}
    for idx in range(1, 100):
        angle = 0.73 * idx + 0.17 * (idx % 7)
        radius = 2.0 + 0.18 * idx + 1.4 * rng.random()
        x = radius * math.cos(angle) + 0.45 * rng.random()
        y = radius * math.sin(angle) + 0.45 * rng.random()
        node_coords[f"p{idx}"] = (round(x, 4), round(y, 4))

    edge_pairs = set()
    node_ids = list(node_coords.keys())
    for idx in range(99):
        edge_pairs.add((f"p{idx}", f"p{idx + 1}"))
    for u in node_ids:
        ux, uy = node_coords[u]
        neighbors = []
        for v in node_ids:
            if u == v:
                continue
            vx, vy = node_coords[v]
            neighbors.append((math.hypot(ux - vx, uy - vy), v))
        neighbors.sort()
        for _, v in neighbors[:4]:
            edge_pairs.add(tuple(sorted((u, v))))

    edge_specs = []
    for order, (u, v) in enumerate(sorted(edge_pairs)):
        speed = 1.0 + 0.35 * ((order % 5) / 4.0)
        energy_rate = 0.55 + 0.18 * ((order + 2) % 7) / 6.0
        cost_rate = 0.75 + 0.20 * ((order + 3) % 6) / 5.0
        time_factor = 1.0 + 0.10 * ((order + 1) % 4)
        energy_factor = 1.0 + 0.08 * ((order + 2) % 5)
        cost_factor = 1.0 + 0.06 * ((order + 3) % 5)
        edge_specs.append(_edge(u, v, speed, energy_rate, cost_rate, time_factor, energy_factor, cost_factor))

    return build_terrain(node_coords, edge_specs)


def _scaled_terrain(node_count, seed):
    rng = random.Random(seed)
    node_coords = {"p0": (0.0, 0.0)}
    for idx in range(1, node_count):
        angle = 0.61 * idx + 0.19 * (idx % 11)
        radius = 2.0 + 0.12 * idx + 1.2 * rng.random()
        x = radius * math.cos(angle) + 0.35 * rng.random()
        y = radius * math.sin(angle) + 0.35 * rng.random()
        node_coords[f"p{idx}"] = (round(x, 4), round(y, 4))

    edge_pairs = set()
    node_ids = list(node_coords.keys())
    for idx in range(node_count - 1):
        edge_pairs.add((f"p{idx}", f"p{idx + 1}"))
    for u in node_ids:
        ux, uy = node_coords[u]
        neighbors = []
        for v in node_ids:
            if u == v:
                continue
            vx, vy = node_coords[v]
            neighbors.append((math.hypot(ux - vx, uy - vy), v))
        neighbors.sort()
        for _, v in neighbors[:4]:
            edge_pairs.add(tuple(sorted((u, v))))

    edge_specs = []
    for order, (u, v) in enumerate(sorted(edge_pairs)):
        speed = 1.0 + 0.30 * ((order % 5) / 4.0)
        energy_rate = 0.50 + 0.14 * ((order + 2) % 7) / 6.0
        cost_rate = 0.70 + 0.18 * ((order + 3) % 6) / 5.0
        time_factor = 1.0 + 0.08 * ((order + 1) % 4)
        energy_factor = 1.0 + 0.06 * ((order + 2) % 5)
        cost_factor = 1.0 + 0.05 * ((order + 3) % 5)
        edge_specs.append(_edge(u, v, speed, energy_rate, cost_rate, time_factor, energy_factor, cost_factor))

    return build_terrain(node_coords, edge_specs)


def build_very_small_instance():
    tasks = {
        "1": {"terrain_node": "p2", "r": 0.0, "D": 34.0, "sigma": 2.0, "d": 2.0, "g": 1.0, "c_srv": 2.0},
        "2": {"terrain_node": "p4", "r": 2.0, "D": 48.0, "sigma": 3.0, "d": 2.0, "g": 1.2, "c_srv": 2.5},
        "3": {"terrain_node": "p6", "r": 0.0, "D": 55.0, "sigma": 2.0, "d": 2.0, "g": 0.9, "c_srv": 2.0},
        "4": {"terrain_node": "p8", "r": 5.0, "D": 85.0, "sigma": 3.0, "d": 3.0, "g": 1.4, "c_srv": 3.0},
    }
    vehicles = {"R_bar": 2, "S_bar": 2, "Q": 5.0, "B_max": 34.0, "B_surv": 4.0, "B_use": 30.0, "rho": 2.0, "F": 100.0, "H": 120.0}
    return {
        "name": "very_small",
        "seed": 7,
        "description": "小规模地形 CVRPTW 测试实例。",
        "terrain": _demo_terrain(),
        "base": {"id": 0, "terrain_node": "p0"},
        "tasks": tasks,
        "vehicles": vehicles,
    }


def build_medium_instance():
    task_nodes = [
        "p6",
        "p10",
        "p13",
        "p18",
        "p22",
        "p27",
        "p31",
        "p36",
        "p41",
        "p45",
        "p50",
        "p55",
        "p60",
        "p64",
        "p69",
        "p73",
        "p78",
        "p83",
        "p88",
        "p94",
    ]
    tasks = {}
    for idx, terrain_node in enumerate(task_nodes, start=1):
        tasks[str(idx)] = {
            "terrain_node": terrain_node,
            "r": float((idx % 5) * 2),
            "D": 40.0 + float(idx) * 8.5,
            "sigma": float(2 + (idx % 3)),
            "d": float(1 + (idx % 3)),
            "g": round(0.8 + 0.08 * (idx % 5), 4),
            "c_srv": round(1.5 + 0.12 * idx, 4),
        }
    vehicles = {"R_bar": 5, "S_bar": 4, "Q": 9.0, "B_max": 50.0, "B_surv": 10.0, "B_use": 40.0, "rho": 5.0, "F": 100.0, "H": 240.0}
    return {
        "name": "medium",
        "seed": 20260510,
        "description": "包含 100 个地形点和 20 个任务点的中规模测试实例。",
        "terrain": _medium_terrain(),
        "base": {"id": 0, "terrain_node": "p0"},
        "tasks": tasks,
        "vehicles": vehicles,
    }


def build_scaled_instance(task_count):
    terrain_node_count = max(100, task_count * 3)
    seed = 20260510 + task_count
    terrain = _scaled_terrain(terrain_node_count, seed)

    tasks = {}
    for idx in range(1, task_count + 1):
        terrain_idx = 1 + (idx * (terrain_node_count - 2)) // task_count
        tasks[str(idx)] = {
            "terrain_node": f"p{terrain_idx}",
            "r": 0.0,
            "D": 85.0 + 0.8 * idx,
            "sigma": 1.0,
            "d": 1.0,
            "g": 0.5,
            "c_srv": 1.0,
        }

    # 中文注释：大规模入口不再用载重人为限定每条 sortie 的任务数；
    # Q 给得足够大，路径长度主要由时间窗、地形行驶时间和电池能耗自然限制。
    vehicles = {
        "R_bar": max(1, math.ceil(task_count / 4)),
        "S_bar": 2,
        "Q": float(task_count),
        "B_max": 75.0,
        "B_surv": 10.0,
        "B_use": 65.0,
        "rho": 10.0,
        "F": 100.0,
        "H": 110.0,
    }
    return {
        "name": str(task_count),
        "seed": seed,
        "description": f"包含 {terrain_node_count} 个地形点和 {task_count} 个任务点的分支定价规模测试实例。",
        "terrain": terrain,
        "base": {"id": 0, "terrain_node": "p0"},
        "tasks": tasks,
        "vehicles": vehicles,
    }


def build_instance(name):
    if name == "very_small":
        return build_very_small_instance()
    if name == "medium":
        return build_medium_instance()
    if name in {"30", "40", "50", "100"}:
        return build_scaled_instance(int(name))
    raise ValueError(f"未知实例名称：{name}")
