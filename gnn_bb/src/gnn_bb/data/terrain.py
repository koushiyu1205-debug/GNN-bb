"""中文摘要：本文件把实例中的底层地形图压缩为任务层完全有向图，供 MILP 和 pricing 使用。"""

from __future__ import annotations

from typing import Any


def arc_key(i: int, j: int) -> str:
    return f"{i}->{j}"


def graph_from_terrain(terrain: dict[str, Any]):
    import networkx as nx

    graph = nx.Graph()
    for node, position in terrain["positions"].items():
        graph.add_node(node, pos=(float(position[0]), float(position[1])))
    for edge in terrain["edges"]:
        graph.add_edge(
            edge["u"],
            edge["v"],
            distance=float(edge["distance"]),
            time=float(edge["time"]),
            energy=float(edge["energy"]),
            cost=float(edge["cost"]),
        )
    return graph


def shortest_path_with_aggregate(graph, source: str, target: str, weight: str = "cost") -> dict[str, Any]:
    import networkx as nx

    path = nx.shortest_path(graph, source=source, target=target, weight=weight)
    totals = {"distance": 0.0, "time": 0.0, "energy": 0.0, "cost": 0.0}
    for u, v in zip(path[:-1], path[1:]):
        attrs = graph[u][v]
        for key in totals:
            totals[key] += float(attrs[key])
    return {
        "path": path,
        "distance": round(totals["distance"], 6),
        "tau": round(totals["time"], 6),
        "energy": round(totals["energy"], 6),
        "cost": round(totals["cost"], 6),
    }


def build_task_closure(instance: dict[str, Any], weight: str = "cost") -> dict[str, dict[str, Any]]:
    graph = graph_from_terrain(instance["terrain"])
    base_node = instance["base"]["terrain_node"]
    logical_nodes = {0: base_node}
    logical_nodes.update({int(task_id): task["terrain_node"] for task_id, task in instance["tasks"].items()})

    pairwise = {}
    for i, source in logical_nodes.items():
        for j, target in logical_nodes.items():
            if i == j:
                continue
            pairwise[arc_key(i, j)] = shortest_path_with_aggregate(graph, source, target, weight=weight)
    return pairwise

