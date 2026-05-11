"""中文摘要：本文件负责读取 json/instances 中的实例，并在缺失时只读调用 legacy 生成器补齐实例。"""

from __future__ import annotations

import importlib.util
import math
import sys
import types
from pathlib import Path
from typing import Any

from .io_utils import project_root, read_json, write_json


DEFAULT_INSTANCE_NAMES = ("very_small", "medium", "30", "40", "50", "100")

SCALABLE_PROFILE_NAME = "medium_like_scaled_v1"
SCALABLE_VEHICLE_PHYSICAL_PARAMETERS = {
    "Q": 9.0,
    "B_max": 50.0,
    "B_surv": 10.0,
    "B_use": 40.0,
    "rho": 5.0,
    "F": 100.0,
    "H": 240.0,
}


def task_ids(instance: dict[str, Any]) -> list[int]:
    return sorted(int(task_id) for task_id in instance["tasks"])


def validate_instance_schema(instance: dict[str, Any]) -> None:
    required = {"name", "terrain", "base", "tasks", "vehicles"}
    missing = sorted(required - set(instance))
    if missing:
        raise ValueError(f"实例缺少字段：{missing}")
    if "positions" not in instance["terrain"] or "edges" not in instance["terrain"]:
        raise ValueError("实例 terrain 必须包含 positions 和 edges")
    vehicle_required = {"R_bar", "S_bar", "Q", "B_use", "rho", "F", "H"}
    vehicle_missing = sorted(vehicle_required - set(instance["vehicles"]))
    if vehicle_missing:
        raise ValueError(f"车辆参数缺少字段：{vehicle_missing}")
    for task_id, task in instance["tasks"].items():
        task_required = {"terrain_node", "r", "D", "sigma", "d", "g", "c_srv"}
        task_missing = sorted(task_required - set(task))
        if task_missing:
            raise ValueError(f"任务 {task_id} 缺少字段：{task_missing}")


def uses_scalable_profile(name: str) -> bool:
    """中文注释：medium 和数字规模实例使用同一个可扩展参数策略，very_small 保持教学小例子。"""
    if name == "medium":
        return True
    return name.isdecimal() and int(name) >= 20


def scalable_task_parameters(task_id: int) -> dict[str, float]:
    """中文注释：所有规模实例使用同一套任务服务与需求公式，只让任务数量和地形位置变化。"""
    return {
        "r": float((task_id % 5) * 2),
        "D": 40.0 + float(task_id) * 8.5,
        "sigma": float(2 + (task_id % 3)),
        "d": float(1 + (task_id % 3)),
        "g": round(0.8 + 0.08 * (task_id % 5), 4),
        "c_srv": round(1.5 + 0.12 * task_id, 4),
    }


def _single_task_sortie_cycle_times(instance: dict[str, Any]) -> dict[int, float]:
    # 中文注释：这里使用和 route pricing 一致的任务层最短路闭包计算单任务 sortie 的 cycle time。
    from .terrain import arc_key, build_task_closure

    pairwise = build_task_closure(instance, weight="cost")
    rho = float(instance["vehicles"]["rho"])
    cycle_times = {}
    for task_id in task_ids(instance):
        outbound = pairwise[arc_key(0, task_id)]
        inbound = pairwise[arc_key(task_id, 0)]
        task = instance["tasks"][str(task_id)]
        start = max(float(task["r"]), float(outbound["tau"]))
        finish = start + float(task["sigma"])
        return_time = finish + float(inbound["tau"])
        energy = float(outbound["energy"]) + float(task["g"]) + float(inbound["energy"])
        cycle_times[task_id] = return_time + energy / rho
    return cycle_times


def _greedy_vehicle_upper_bound(cycle_times: list[float], h_limit: float, s_bar: int) -> int:
    # 中文注释：first-fit decreasing 只用于生成可复现实例上界，不作为求解器剪枝规则。
    bins: list[dict[str, float | int]] = []
    for cycle_time in sorted(cycle_times, reverse=True):
        placed = False
        for vehicle in bins:
            if int(vehicle["count"]) >= s_bar:
                continue
            if float(vehicle["used"]) + cycle_time <= h_limit + 1.0e-9:
                vehicle["used"] = float(vehicle["used"]) + cycle_time
                vehicle["count"] = int(vehicle["count"]) + 1
                placed = True
                break
        if not placed:
            bins.append({"used": cycle_time, "count": 1})
    return max(1, len(bins))


def scalable_vehicle_parameters(instance: dict[str, Any]) -> tuple[dict[str, float | int], dict[str, Any]]:
    """中文注释：S_bar 由 H/最短单任务 sortie cycle time 自动计算，R_bar 由单任务 sortie 装箱上界自动计算。"""
    task_count = len(instance["tasks"])
    vehicles = {**SCALABLE_VEHICLE_PHYSICAL_PARAMETERS}
    temporary_instance = {**instance, "vehicles": {**dict(instance["vehicles"]), **vehicles}}
    cycle_time_by_task = _single_task_sortie_cycle_times(temporary_instance)
    feasible_cycle_times = [cycle for cycle in cycle_time_by_task.values() if cycle <= float(vehicles["H"]) + 1.0e-9]
    if not feasible_cycle_times:
        s_bar = 1
        r_bar = task_count
        min_cycle_time = None
    else:
        min_cycle_time = min(feasible_cycle_times)
        s_bar = max(1, min(task_count, int(math.floor(float(vehicles["H"]) / min_cycle_time))))
        r_bar = _greedy_vehicle_upper_bound(feasible_cycle_times, float(vehicles["H"]), s_bar)
        if len(feasible_cycle_times) < task_count:
            r_bar += task_count - len(feasible_cycle_times)
    vehicles["S_bar"] = int(s_bar)
    vehicles["R_bar"] = int(r_bar)
    metadata = {
        "profile": SCALABLE_PROFILE_NAME,
        "s_bar_formula": "floor(H / min_single_task_sortie_cycle_time)",
        "r_bar_formula": "first_fit_decreasing(single_task_sortie_cycle_times, H, S_bar)",
        "single_task_cycle_weight": "cost",
        "min_single_task_sortie_cycle_time": round(min_cycle_time, 6) if min_cycle_time is not None else None,
        "max_single_task_sortie_cycle_time": round(max(cycle_time_by_task.values()), 6) if cycle_time_by_task else None,
        "single_task_infeasible_count": task_count - len(feasible_cycle_times),
    }
    return vehicles, metadata


def standardize_scalable_parameters(instance: dict[str, Any]) -> dict[str, Any]:
    """中文注释：统一 medium/数字规模的参数生成策略，使 30/50/100 不需要人工调 R_bar/S_bar。"""
    if not uses_scalable_profile(str(instance.get("name"))):
        return instance

    standardized = dict(instance)
    standardized["tasks"] = {
        str(task_id): {**dict(task), **scalable_task_parameters(int(task_id))}
        for task_id, task in instance["tasks"].items()
    }
    standardized["vehicles"], scaling_metadata = scalable_vehicle_parameters(standardized)
    standardized["parameter_profile"] = SCALABLE_PROFILE_NAME
    standardized["scaling_policy"] = scaling_metadata
    description = str(standardized.get("description", "")).split(" 参数配置：", 1)[0]
    standardized["description"] = (
        f"{description} 参数配置：{SCALABLE_PROFILE_NAME}，物理车辆参数固定，"
        "S_bar=floor(H/最短单任务 sortie cycle time)，R_bar 由单任务 sortie 装箱上界生成。"
    ).strip()
    return standardized


def _load_legacy_builder():
    root = project_root()
    legacy_src = root / "model" / "scip-version" / "src"
    package_name = "_gnn_bb_legacy_scip_src"
    if package_name not in sys.modules:
        package = types.ModuleType(package_name)
        package.__path__ = [str(legacy_src)]
        sys.modules[package_name] = package

    for module_name in ("terrain", "instance_data"):
        full_name = f"{package_name}.{module_name}"
        if full_name in sys.modules:
            continue
        module_path = legacy_src / f"{module_name}.py"
        spec = importlib.util.spec_from_file_location(full_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"无法加载 legacy 模块：{module_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[full_name] = module
        spec.loader.exec_module(module)
    return sys.modules[f"{package_name}.instance_data"].build_instance


def build_instance_from_legacy(name: str) -> dict[str, Any]:
    builder = _load_legacy_builder()
    instance = standardize_scalable_parameters(builder(name))
    validate_instance_schema(instance)
    return instance


def instance_json_path(name: str, instance_dir: str | Path = "json/instances") -> Path:
    return project_root() / instance_dir / f"instance_{name}.json"


def load_or_build_instance(
    name: str,
    instance_dir: str | Path = "json/instances",
    write_if_missing: bool = True,
) -> tuple[dict[str, Any], Path]:
    path = instance_json_path(name, instance_dir)
    if path.exists():
        instance = standardize_scalable_parameters(read_json(path))
        validate_instance_schema(instance)
        return instance, path

    legacy_output = project_root() / "model" / "scip-version" / "outputs" / f"instance_{name}.json"
    if legacy_output.exists():
        instance = standardize_scalable_parameters(read_json(legacy_output))
        validate_instance_schema(instance)
    else:
        instance = build_instance_from_legacy(name)

    if write_if_missing:
        write_json(path, instance)
        return instance, path
    return instance, legacy_output if legacy_output.exists() else path
