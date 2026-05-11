"""中文摘要：本文件负责构建路径选择 MILP，用二进制变量选择可行路径并覆盖所有任务。"""

def build_path_milp(instance, routes):
    from pyscipopt import Model, quicksum

    vehicles = instance["vehicles"]
    tasks = sorted(int(key) for key in instance["tasks"])
    R = list(range(1, int(vehicles["R_bar"]) + 1))
    S = list(range(1, int(vehicles["S_bar"]) + 1))
    fixed_vehicle_cost = float(vehicles["F"])
    horizon = float(vehicles["H"])

    model = Model("path_generation_cvrptw_scip")
    route_ids = [route["id"] for route in routes]
    route_by_id = {route["id"]: route for route in routes}

    x = {}
    for route_id in route_ids:
        for r in R:
            for s in S:
                x[route_id, r, s] = model.addVar(vtype="B", name=f"x[{route_id},{r},{s}]")

    z = {}
    for r in R:
        for s in S:
            z[r, s] = model.addVar(vtype="B", name=f"z[{r},{s}]")

    y = {r: model.addVar(vtype="B", name=f"y[{r}]") for r in R}

    model.setObjective(
        fixed_vehicle_cost * quicksum(y[r] for r in R)
        + quicksum(float(route_by_id[route_id]["cost"]) * x[route_id, r, s] for route_id in route_ids for r in R for s in S),
        sense="minimize",
    )

    for task_id in tasks:
        covering_routes = [route["id"] for route in routes if task_id in route["task_set"]]
        model.addCons(
            quicksum(x[route_id, r, s] for route_id in covering_routes for r in R for s in S) == 1,
            name=f"cover[{task_id}]",
        )

    for r in R:
        for s in S:
            model.addCons(quicksum(x[route_id, r, s] for route_id in route_ids) == z[r, s], name=f"slot[{r},{s}]")
            model.addCons(z[r, s] <= y[r], name=f"slot_requires_vehicle[{r},{s}]")

    for r in R:
        model.addCons(
            quicksum(float(route_by_id[route_id]["cycle_time"]) * x[route_id, r, s] for route_id in route_ids for s in S)
            <= horizon * y[r],
            name=f"vehicle_cycle_time[{r}]",
        )

    for r in R:
        for s in S[:-1]:
            model.addCons(z[r, s + 1] <= z[r, s], name=f"sortie_sequence[{r},{s}]")
    for r in R[:-1]:
        model.addCons(y[r + 1] <= y[r], name=f"vehicle_sequence[{r}]")

    variables = {"x": x, "y": y, "z": z}
    metadata = {"R": R, "S": S, "route_ids": route_ids, "route_by_id": route_by_id, "tasks": tasks}
    return model, variables, metadata
