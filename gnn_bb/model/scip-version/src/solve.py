"""中文摘要：本文件负责设置 SCIP 求解参数、执行优化，并把求解器变量值整理成可写入 JSON 的解。"""

from math import isfinite

from .io_utils import round_float


def _safe_call(func, default=None):
    try:
        value = func()
    except Exception:
        return default
    if isinstance(value, float) and not isfinite(value):
        return value
    return value


def _status_name(status):
    text = str(status).lower()
    status_map = {
        "optimal": "OPTIMAL",
        "infeasible": "INFEASIBLE",
        "unbounded": "UNBOUNDED",
        "inforunbd": "INF_OR_UNBD",
        "timelimit": "TIME_LIMIT",
        "nodelimit": "NODE_LIMIT",
        "gaplimit": "GAP_LIMIT",
        "memlimit": "MEMORY_LIMIT",
        "userinterrupt": "INTERRUPTED",
        "solutionlimit": "SOLUTION_LIMIT",
    }
    return status_map.get(text, text.upper())


def solve_path_model(model, variables, metadata, time_limit=None, verbose=True):
    if time_limit is not None:
        model.setParam("limits/time", float(time_limit))
    model.setParam("display/verblevel", 4 if verbose else 0)

    model.optimize()

    solution_count = int(_safe_call(model.getNSols, 0) or 0)
    has_solution = solution_count > 0
    raw_status = str(_safe_call(model.getStatus, "unknown"))

    summary = {
        "status": _status_name(raw_status),
        "status_code": raw_status,
        "objective": round_float(_safe_call(model.getObjVal)) if has_solution else None,
        "runtime": round_float(_safe_call(model.getSolvingTime, 0.0)),
        "best_bound": round_float(_safe_call(model.getDualbound)) if has_solution else None,
        "mip_gap": round_float(_safe_call(model.getGap)) if has_solution else None,
        "node_count": round_float(_safe_call(model.getNNodes, 0.0)),
        "solution_count": solution_count,
    }

    solution = {"summary": summary, "vehicles": {}, "sorties": [], "selected_route_ids": []}
    if not has_solution:
        return solution

    x = variables["x"]
    y = variables["y"]
    z = variables["z"]
    route_by_id = metadata["route_by_id"]

    for r in metadata["R"]:
        solution["vehicles"][str(r)] = round_float(model.getVal(y[r]))
        for s in metadata["S"]:
            z_value = model.getVal(z[r, s])
            if z_value <= 0.5:
                continue
            for route_id in metadata["route_ids"]:
                value = model.getVal(x[route_id, r, s])
                if value <= 0.5:
                    continue
                route = route_by_id[route_id]
                solution["selected_route_ids"].append(route_id)
                solution["sorties"].append(
                    {
                        "vehicle": r,
                        "sortie": s,
                        "route_id": route_id,
                        "tasks": route["tasks"],
                        "cost": route["cost"],
                        "load": route["load"],
                        "energy": route["energy"],
                        "return_time": route["return_time"],
                        "cycle_time": route["cycle_time"],
                        "service_start": route["service_start"],
                    }
                )

    return solution
