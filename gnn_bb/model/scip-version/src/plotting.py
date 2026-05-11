"""中文摘要：本文件负责使用 matplotlib 把求解结果画成 PNG 图片，包括任务层路径图和底层地形路径图。"""


def _load_pyplot():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.sans-serif"] = ["SimHei", "Noto Sans CJK SC", "Arial Unicode MS", "DejaVu Sans"]
    return plt


def _logical_positions(instance):
    positions = instance["terrain"]["positions"]
    logical_to_terrain = {0: instance["base"]["terrain_node"]}
    for task_id, task in instance["tasks"].items():
        logical_to_terrain[int(task_id)] = task["terrain_node"]
    return {node: positions[terrain_node] for node, terrain_node in logical_to_terrain.items()}


def _selected_routes(routes, solution):
    route_by_id = {int(route["id"]): route for route in routes}
    selected = []
    for sortie in solution.get("sorties", []):
        route = route_by_id.get(int(sortie["route_id"]))
        if route is not None:
            selected.append((sortie, route))
    return selected


def _color(index):
    palette = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf", "#8c564b", "#e377c2"]
    return palette[index % len(palette)]


def plot_task_routes(instance, routes, solution, output_path):
    plt = _load_pyplot()
    positions = _logical_positions(instance)
    selected = _selected_routes(routes, solution)

    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    base_x, base_y = positions[0]
    ax.scatter([base_x], [base_y], marker="s", s=95, color="#111111", label="基地", zorder=5)
    ax.text(base_x, base_y, " 0", fontsize=10, va="center", zorder=6)

    task_x = []
    task_y = []
    for task_id in sorted(int(key) for key in instance["tasks"]):
        x, y = positions[task_id]
        task_x.append(x)
        task_y.append(y)
        ax.text(x, y, f" {task_id}", fontsize=9, va="center", zorder=6)
    ax.scatter(task_x, task_y, s=60, color="#ffffff", edgecolor="#111111", linewidth=1.2, label="任务", zorder=5)

    for idx, (sortie, route) in enumerate(selected):
        color = _color(idx)
        sequence = [0, *route["tasks"], 0]
        for start, end in zip(sequence[:-1], sequence[1:]):
            x1, y1 = positions[start]
            x2, y2 = positions[end]
            ax.annotate(
                "",
                xy=(x2, y2),
                xytext=(x1, y1),
                arrowprops={"arrowstyle": "->", "color": color, "lw": 2.0, "alpha": 0.85},
                zorder=4,
            )
        ax.plot([], [], color=color, linewidth=2.0, label=f"车{sortie['vehicle']}-架次{sortie['sortie']}: {route['tasks']}")

    ax.set_title("任务层路径图")
    ax.set_xlabel("x 坐标")
    ax.set_ylabel("y 坐标")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.4)
    ax.set_aspect("equal", adjustable="datalim")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_terrain_routes(instance, routes, solution, output_path):
    plt = _load_pyplot()
    terrain = instance["terrain"]
    positions = terrain["positions"]
    selected = _selected_routes(routes, solution)

    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    for edge in terrain["edges"]:
        x1, y1 = positions[edge["u"]]
        x2, y2 = positions[edge["v"]]
        ax.plot([x1, x2], [y1, y2], color="#d4d4d4", linewidth=0.8, zorder=1)

    for _, (x, y) in positions.items():
        ax.scatter([x], [y], s=13, color="#777777", zorder=2)

    for idx, (sortie, route) in enumerate(selected):
        color = _color(idx)
        for segment in route["physical_paths"]:
            path = segment["path"]
            for start, end in zip(path[:-1], path[1:]):
                x1, y1 = positions[start]
                x2, y2 = positions[end]
                ax.plot([x1, x2], [y1, y2], color=color, linewidth=2.6, alpha=0.86, zorder=4)
        ax.plot([], [], color=color, linewidth=2.6, label=f"车{sortie['vehicle']}-架次{sortie['sortie']}: {route['tasks']}")

    base_node = instance["base"]["terrain_node"]
    bx, by = positions[base_node]
    ax.scatter([bx], [by], marker="s", s=95, color="#111111", label="基地", zorder=5)
    ax.text(bx, by, " 0", fontsize=10, va="center", zorder=6)

    for task_id, task in instance["tasks"].items():
        x, y = positions[task["terrain_node"]]
        ax.scatter([x], [y], s=60, color="#ffffff", edgecolor="#111111", linewidth=1.2, zorder=5)
        ax.text(x, y, f" {task_id}", fontsize=9, va="center", zorder=6)

    ax.set_title("底层地形路径图")
    ax.set_xlabel("x 坐标")
    ax.set_ylabel("y 坐标")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.4)
    ax.set_aspect("equal", adjustable="datalim")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
