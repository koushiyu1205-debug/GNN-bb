"""中文摘要：本文件读取实例 JSON 并整理 clean BPC 使用的数据视图。它只做数据加载、字段访问和基础维度检查。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BPCData:
    instance: dict[str, Any]
    pairwise: dict[str, dict[str, Any]]
    instance_path: Path
    name: str
    tasks: tuple[int, ...]
    vehicles: tuple[int, ...]
    sortie_limit: int
    capacity: float
    energy_limit: float
    rho: float
    fixed_vehicle_cost: float
    horizon: float

    def task_value(self, task_id: int, field: str) -> float:
        return float(self.instance["tasks"][str(int(task_id))][field])

    def arc(self, i: int, j: int) -> dict[str, Any]:
        return self.pairwise[f"{int(i)}->{int(j)}"]


def load_bpc_data(name: str, instance_dir: str | Path = "json/instances") -> BPCData:
    # 中文注释：数据加载复用根目录已有的实例管理与地形闭包；clean BPC 不复用旧 bp 求解逻辑。
    from gnn_bb.data.instances import load_or_build_instance, task_ids
    from gnn_bb.data.terrain import build_task_closure

    instance, instance_path = load_or_build_instance(name, instance_dir=instance_dir, write_if_missing=True)
    pairwise = build_task_closure(instance, weight="cost")
    vehicles = instance["vehicles"]
    task_tuple = tuple(task_ids(instance))
    vehicle_tuple = tuple(range(1, int(vehicles["R_bar"]) + 1))
    return BPCData(
        instance=instance,
        pairwise=pairwise,
        instance_path=Path(instance_path),
        name=str(instance.get("name", name)),
        tasks=task_tuple,
        vehicles=vehicle_tuple,
        sortie_limit=int(vehicles["S_bar"]),
        capacity=float(vehicles["Q"]),
        energy_limit=float(vehicles["B_use"]),
        rho=float(vehicles["rho"]),
        fixed_vehicle_cost=float(vehicles["F"]),
        horizon=float(vehicles["H"]),
    )
