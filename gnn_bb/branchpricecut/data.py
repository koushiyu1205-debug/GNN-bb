"""中文摘要：读取 JSON 实例并转成 vehicle-schedule BPC 使用的数据视图。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class InstanceData:
    instance: dict[str, Any]
    pairwise: dict[str, dict[str, Any]]
    instance_path: Path
    name: str
    tasks: tuple[int, ...]
    vehicle_count: int
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


def load_instance(name: str, instance_dir: str | Path = "json/instances") -> InstanceData:
    # 中文注释：只复用根目录已有的数据生成/地形闭包工具，不复用旧 bpc 求解逻辑。
    from gnn_bb.data.instances import load_or_build_instance, task_ids
    from gnn_bb.data.terrain import build_task_closure

    instance, instance_path = load_or_build_instance(name, instance_dir=instance_dir, write_if_missing=True)
    pairwise = build_task_closure(instance, weight="cost")
    vehicles = instance["vehicles"]
    return InstanceData(
        instance=instance,
        pairwise=pairwise,
        instance_path=Path(instance_path),
        name=str(instance.get("name", name)),
        tasks=tuple(task_ids(instance)),
        vehicle_count=int(vehicles["R_bar"]),
        sortie_limit=int(vehicles["S_bar"]),
        capacity=float(vehicles["Q"]),
        energy_limit=float(vehicles["B_use"]),
        rho=float(vehicles["rho"]),
        fixed_vehicle_cost=float(vehicles["F"]),
        horizon=float(vehicles["H"]),
    )

