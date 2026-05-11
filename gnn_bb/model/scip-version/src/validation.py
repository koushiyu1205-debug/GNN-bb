"""中文摘要：本文件负责校验路径 MILP 的解，包括任务覆盖、路径资源限制和车辆总工作时长。"""

from collections import Counter, defaultdict


def validate_solution(instance, routes, solution):
    tasks = sorted(int(key) for key in instance["tasks"])
    route_by_id = {route["id"]: route for route in routes}
    vehicles = instance["vehicles"]
    q_limit = float(vehicles["Q"])
    b_limit = float(vehicles["B_use"])
    horizon = float(vehicles["H"])

    coverage = Counter()
    vehicle_cycle_time = defaultdict(float)
    violations = []

    for task_id in solution.get("artificial_tasks", []):
        violations.append(f"任务 {task_id} 由 Phase-I 人工列覆盖，不能视为原问题可行覆盖")

    for sortie in solution.get("sorties", []):
        route = route_by_id.get(sortie["route_id"])
        if route is None:
            violations.append(f"未知 route_id：{sortie['route_id']}")
            continue
        for task_id in route["task_set"]:
            coverage[task_id] += 1
        vehicle_cycle_time[sortie["vehicle"]] += float(route["cycle_time"])
        if float(route["load"]) > q_limit + 1.0e-6:
            violations.append(f"路径 {route['id']} 超出载重限制")
        if float(route["energy"]) > b_limit + 1.0e-6:
            violations.append(f"路径 {route['id']} 超出能量限制")
        if float(route["return_time"]) > horizon + 1.0e-6:
            violations.append(f"路径 {route['id']} 超出时间域限制")

    for task_id in tasks:
        if coverage[task_id] != 1:
            violations.append(f"任务 {task_id} 覆盖次数为 {coverage[task_id]}，期望为 1")

    for vehicle, cycle_time in vehicle_cycle_time.items():
        if cycle_time > horizon + 1.0e-6:
            violations.append(f"车辆 {vehicle} 总工作时长 {cycle_time:.6f} 超出时间域限制")

    return {
        "is_valid": not violations,
        "violations": violations,
        "covered_tasks": dict(sorted(coverage.items())),
        "vehicle_cycle_time": {str(vehicle): round(time, 6) for vehicle, time in sorted(vehicle_cycle_time.items())},
    }
