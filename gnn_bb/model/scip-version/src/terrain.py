"""中文摘要：本文件负责构建底层地形图，并计算基地和任务点之间的最短路径及时间、能耗、成本聚合值。"""

import math


def arc_key(i, j):
    return f"{i}->{j}"


def _euclidean_distance(a, b):
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def _edge_value(edge_spec, key, default):
    return float(edge_spec[key]) if key in edge_spec else float(default)


def build_terrain(node_coords, edge_specs):
    positions = {node: [float(coord[0]), float(coord[1])] for node, coord in node_coords.items()}
    edges = []
    for spec in edge_specs:
        u = spec["u"]
        v = spec["v"]
        distance = _edge_value(spec, "distance", _euclidean_distance(positions[u], positions[v]))
        speed = _edge_value(spec, "speed", 1.0)
        energy_rate = _edge_value(spec, "energy_rate", 1.0)
        cost_rate = _edge_value(spec, "cost_rate", 1.0)
        time_factor = _edge_value(spec, "time_factor", 1.0)
        energy_factor = _edge_value(spec, "energy_factor", 1.0)
        cost_factor = _edge_value(spec, "cost_factor", 1.0)
        edges.append(
            {
                "u": u,
                "v": v,
                "distance": round(distance, 6),
                "time": round(_edge_value(spec, "time", distance / speed * time_factor), 6),
                "energy": round(_edge_value(spec, "energy", distance * energy_rate * energy_factor), 6),
                "cost": round(_edge_value(spec, "cost", distance * cost_rate * cost_factor), 6),
            }
        )
    return {"positions": positions, "edges": edges}


def graph_from_terrain(terrain):
    import networkx as nx

    graph = nx.Graph()
    for node, pos in terrain["positions"].items():
        graph.add_node(node, pos=(float(pos[0]), float(pos[1])))
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


def shortest_path_with_aggregate(graph, source, target, weight="cost"):
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


def build_task_closure(instance, weight="cost"):
    graph = graph_from_terrain(instance["terrain"])
    base_node = instance["base"]["terrain_node"]
    task_nodes = {int(key): value["terrain_node"] for key, value in instance["tasks"].items()}
    logical_nodes = {0: base_node, **task_nodes}

    pairwise = {}
    for i, source in logical_nodes.items():
        for j, target in logical_nodes.items():
            if i == j:
                continue
            pairwise[arc_key(i, j)] = shortest_path_with_aggregate(graph, source, target, weight=weight)

    return pairwise
