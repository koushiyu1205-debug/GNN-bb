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

    for sortie in solution.get("sorties", []):
        route = route_by_id.get(sortie["route_id"])
        if route is None:
            violations.append(f"Unknown route_id {sortie['route_id']}")
            continue
        for task_id in route["task_set"]:
            coverage[task_id] += 1
        vehicle_cycle_time[sortie["vehicle"]] += float(route["cycle_time"])
        if float(route["load"]) > q_limit + 1.0e-6:
            violations.append(f"Route {route['id']} exceeds load limit")
        if float(route["energy"]) > b_limit + 1.0e-6:
            violations.append(f"Route {route['id']} exceeds energy limit")
        if float(route["return_time"]) > horizon + 1.0e-6:
            violations.append(f"Route {route['id']} exceeds horizon")

    for task_id in tasks:
        if coverage[task_id] != 1:
            violations.append(f"Task {task_id} coverage is {coverage[task_id]}, expected 1")

    for vehicle, cycle_time in vehicle_cycle_time.items():
        if cycle_time > horizon + 1.0e-6:
            violations.append(f"Vehicle {vehicle} cycle time {cycle_time:.6f} exceeds horizon")

    return {
        "is_valid": not violations,
        "violations": violations,
        "covered_tasks": dict(sorted(coverage.items())),
        "vehicle_cycle_time": {str(vehicle): round(time, 6) for vehicle, time in sorted(vehicle_cycle_time.items())},
    }

