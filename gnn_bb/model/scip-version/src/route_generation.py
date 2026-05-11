"""中文摘要：本文件提供路径可行性评估工具，用于分支定价初始化单任务路径。"""

from .io_utils import round_float
from .terrain import arc_key


def task_ids(instance):
    return sorted(int(key) for key in instance["tasks"])


def _task(instance, task_id, field):
    return float(instance["tasks"][str(task_id)][field])


def evaluate_route(instance, pairwise, sequence):
    vehicles = instance["vehicles"]
    q_limit = float(vehicles["Q"])
    b_limit = float(vehicles["B_use"])
    horizon = float(vehicles["H"])
    rho = float(vehicles["rho"])

    load = sum(_task(instance, task, "d") for task in sequence)
    if load > q_limit:
        return None

    travel_time = 0.0
    travel_energy = 0.0
    travel_cost = 0.0
    service_energy = 0.0
    service_cost = 0.0
    service_start = {}
    current = 0
    current_time = 0.0
    physical_paths = []

    for task_id in sequence:
        segment = pairwise[arc_key(current, task_id)]
        travel_time += float(segment["tau"])
        travel_energy += float(segment["energy"])
        travel_cost += float(segment["cost"])
        physical_paths.append({"from": current, "to": task_id, "path": segment["path"]})

        arrival = current_time + float(segment["tau"])
        start = max(_task(instance, task_id, "r"), arrival)
        if start + _task(instance, task_id, "sigma") > _task(instance, task_id, "D"):
            return None

        service_start[task_id] = start
        current_time = start + _task(instance, task_id, "sigma")
        service_energy += _task(instance, task_id, "g")
        service_cost += _task(instance, task_id, "c_srv")
        current = task_id

    back = pairwise[arc_key(current, 0)]
    travel_time += float(back["tau"])
    travel_energy += float(back["energy"])
    travel_cost += float(back["cost"])
    physical_paths.append({"from": current, "to": 0, "path": back["path"]})

    return_time = current_time + float(back["tau"])
    total_energy = travel_energy + service_energy
    total_cost = travel_cost + service_cost
    if total_energy > b_limit or return_time > horizon:
        return None

    return {
        "tasks": list(sequence),
        "task_set": sorted(sequence),
        "task_count": len(sequence),
        "load": round_float(load),
        "travel_time": round_float(travel_time),
        "return_time": round_float(return_time),
        "energy": round_float(total_energy),
        "cost": round_float(total_cost),
        "cycle_time": round_float(return_time + total_energy / rho),
        "service_start": {str(task): round_float(time) for task, time in service_start.items()},
        "physical_paths": physical_paths,
    }
