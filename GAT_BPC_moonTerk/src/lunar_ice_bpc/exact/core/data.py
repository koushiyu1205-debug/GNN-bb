"""Typed instance adapter for lunar-ice exact routines."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any, Generic, TypeVar

from lunar_ice_bpc.domain.scenario import SERVICE_TIMING_POLICY_ID


_KeyT = TypeVar("_KeyT")
_ValueT = TypeVar("_ValueT")


class FrozenMap(Mapping[_KeyT, _ValueT], Generic[_KeyT, _ValueT]):
    """Small pickle-safe read-only mapping used by exact instance data.

    ``MappingProxyType`` is read-only but is not pickleable, which makes it a
    poor fit for the persistent native host.  ``FrozenMap`` owns a defensive
    copy, exposes only the ``Mapping`` protocol, and round-trips through
    multiprocessing pickle without restoring a mutable public container.
    """

    __slots__ = ("__data",)

    def __init__(
        self,
        values: Mapping[_KeyT, _ValueT] | Iterator[tuple[_KeyT, _ValueT]] = (),
    ) -> None:
        object.__setattr__(self, "_FrozenMap__data", dict(values))

    def __getitem__(self, key: _KeyT) -> _ValueT:
        return self.__data[key]

    def __iter__(self) -> Iterator[_KeyT]:
        return iter(self.__data)

    def __len__(self) -> int:
        return len(self.__data)

    def __repr__(self) -> str:
        return f"FrozenMap({self.__data!r})"

    def __reduce__(self):
        return (type(self), (dict(self.__data),))

    def __hash__(self) -> int:
        return hash(frozenset(self.__data.items()))


def deep_freeze(value: Any) -> Any:
    """Recursively replace mutable containers with pickle-safe immutable ones."""

    if isinstance(value, FrozenMap):
        return value
    if isinstance(value, Mapping):
        return FrozenMap((key, deep_freeze(item)) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return tuple(deep_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(deep_freeze(item) for item in value)
    return value


@dataclass(frozen=True)
class TaskData:
    id: str
    xy_km: tuple[float, float]
    science_weight: float
    operation_mode: str
    demand: float
    service_time: float
    service_energy: float
    service_cost: float
    ready_time: float
    due_time: float
    local_shadow_score: float
    local_thermal_risk: float


@dataclass(frozen=True)
class ArcOptionData:
    path_type: str
    travel_time_min: float
    energy_proxy: float
    risk_integral: float
    distance_km: float
    shadow_exposure_min: float
    thermal_survival_energy_proxy: float
    path_xy: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class ObjectiveWeights:
    # The four fields below are retained solely to preserve the frozen
    # instance-content-hash contract.  The exact objective never reads them;
    # see exact.core.objective.OBJECTIVE_SPEC_ID.  Removing or normalizing
    # them here would silently invalidate the frozen sentinel manifest.
    alpha_discovery_completion: float
    beta_journey_end_time: float
    gamma_lunar_ice_risk: float
    delta_energy: float
    weight_operating_cost: float = 1.0
    weight_risk: float = 1.0
    weight_completion: float = 0.4
    weight_makespan_metric_only: float = 0.3
    mode: str = "normalized_operating_cost_risk_weighted_completion"


@dataclass(frozen=True)
class LunarIceData:
    instance_id: str
    scale: int
    tasks: Mapping[str, TaskData]
    depot_xy_km: tuple[float, float]
    arcs: Mapping[tuple[str, str], Mapping[str, ArcOptionData]]
    fleet_size: int
    max_tasks_per_trip: int
    capacity: float
    energy_limit: float
    horizon: float
    dock_overhead_min: float
    recharge_power_proxy_per_min: float
    max_shadow_exposure_per_sortie: float
    objective: ObjectiveWeights
    path_option_policy_id: str = ""
    service_timing_policy_id: str = SERVICE_TIMING_POLICY_ID
    reference_solution: Mapping[str, Any] | None = None
    instance_content_hash: str = field(init=False)

    def __post_init__(self) -> None:
        if self.service_timing_policy_id != SERVICE_TIMING_POLICY_ID:
            raise ValueError(
                "unsupported service timing policy: "
                f"{self.service_timing_policy_id!r}; expected "
                f"{SERVICE_TIMING_POLICY_ID!r}"
            )
        frozen_tasks = deep_freeze(self.tasks)
        frozen_arcs = deep_freeze(self.arcs)
        frozen_reference = (
            None if self.reference_solution is None else deep_freeze(self.reference_solution)
        )
        object.__setattr__(self, "tasks", frozen_tasks)
        object.__setattr__(self, "arcs", frozen_arcs)
        object.__setattr__(self, "reference_solution", frozen_reference)
        object.__setattr__(
            self,
            "instance_content_hash",
            lunar_ice_content_hash(self),
        )

    @property
    def task_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.tasks))

    def option(self, source: str, target: str, path_type: str) -> ArcOptionData:
        return self.arcs[(str(source), str(target))][str(path_type)]


def lunar_ice_content_payload(data: LunarIceData) -> dict[str, Any]:
    """Return the canonical exact-pricing identity payload.

    Keep this payload compatible with the historical ``spprc_instance_hash``
    contract.  Reference solutions are deliberately excluded because they are
    incumbent hints rather than part of the pricing problem.
    """

    return {
        "instance_id": data.instance_id,
        "scale": data.scale,
        "tasks": [asdict(data.tasks[task_id]) for task_id in data.task_ids],
        "arcs": [
            {
                "source": source,
                "target": target,
                "options": [asdict(by_type[path_type]) for path_type in sorted(by_type)],
            }
            for (source, target), by_type in sorted(data.arcs.items())
        ],
        "fleet_size": data.fleet_size,
        "max_tasks_per_trip": data.max_tasks_per_trip,
        "capacity": data.capacity,
        "energy_limit": data.energy_limit,
        "horizon": data.horizon,
        "path_option_policy_id": data.path_option_policy_id,
        "service_timing_policy_id": data.service_timing_policy_id,
        "dock_overhead_min": data.dock_overhead_min,
        "recharge_power_proxy_per_min": data.recharge_power_proxy_per_min,
        "max_shadow_exposure_per_sortie": data.max_shadow_exposure_per_sortie,
        "objective": asdict(data.objective),
    }


def lunar_ice_content_hash(data: LunarIceData) -> str:
    raw = json.dumps(
        lunar_ice_content_payload(data),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def load_lunar_ice_data(instance: dict[str, Any]) -> LunarIceData:
    scheduling = instance["scheduling"]
    service_timing_policy_id = str(
        scheduling.get(
            "service_timing_policy_id",
            SERVICE_TIMING_POLICY_ID,
        )
    )
    if service_timing_policy_id != SERVICE_TIMING_POLICY_ID:
        raise ValueError(
            "unsupported service timing policy: "
            f"{service_timing_policy_id!r}; expected "
            f"{SERVICE_TIMING_POLICY_ID!r}"
        )
    tasks: dict[str, TaskData] = {}
    for task_id, payload in sorted(instance["tasks"].items()):
        tasks[str(task_id)] = TaskData(
            id=str(task_id),
            xy_km=(float(payload["xy_km"][0]), float(payload["xy_km"][1])),
            science_weight=float(payload["science_weight"]),
            operation_mode=str(payload["operation_mode"]),
            demand=float(payload["d"]),
            service_time=float(payload["sigma"]),
            service_energy=float(payload["g"]),
            service_cost=float(payload["c_srv"]),
            ready_time=float(payload["r"]),
            due_time=float(payload["D"]),
            local_shadow_score=float(payload["local_shadow_score"]),
            local_thermal_risk=float(payload["local_thermal_risk"]),
        )

    arcs: dict[tuple[str, str], dict[str, ArcOptionData]] = {}
    for edge in instance["logical_graph"]["edges"]:
        source = str(edge["from"])
        target = str(edge["to"])
        by_type: dict[str, ArcOptionData] = {}
        for option in edge["path_options"]:
            by_type[str(option["path_type"])] = ArcOptionData(
                path_type=str(option["path_type"]),
                travel_time_min=float(option["travel_time_min"]),
                energy_proxy=float(option["energy_proxy"]),
                risk_integral=float(option["risk_integral"]),
                distance_km=float(option["path_distance_km"]),
                shadow_exposure_min=float(option["shadow_exposure_min"]),
                thermal_survival_energy_proxy=float(option["thermal_survival_energy_proxy"]),
                path_xy=tuple((float(x), float(y)) for x, y in option.get("path_xy", [])),
            )
        arcs[(source, target)] = by_type

    vehicle = instance["vehicle"]
    objective_payload = scheduling["objective"]
    return LunarIceData(
        instance_id=str(instance["instance_id"]),
        scale=int(instance["scale"]),
        tasks=tasks,
        depot_xy_km=(float(instance["depot"]["xy_km"][0]), float(instance["depot"]["xy_km"][1])),
        arcs=arcs,
        fleet_size=int(vehicle["fleet_size"]),
        max_tasks_per_trip=int(vehicle["max_tasks_per_trip"]),
        capacity=float(vehicle["Q_ice"]),
        energy_limit=float(vehicle["B_use"]),
        horizon=float(scheduling["horizon_min"]),
        dock_overhead_min=float(vehicle["dock_overhead_min"]),
        recharge_power_proxy_per_min=float(vehicle["recharge_power_proxy_per_min"]),
        max_shadow_exposure_per_sortie=float(vehicle["max_shadow_exposure_per_sortie"]),
        objective=ObjectiveWeights(
            alpha_discovery_completion=float(objective_payload.get("alpha_discovery_completion", 1.0)),
            beta_journey_end_time=float(objective_payload.get("beta_journey_end_time", 0.05)),
            gamma_lunar_ice_risk=float(objective_payload.get("gamma_lunar_ice_risk", 0.1)),
            delta_energy=float(objective_payload.get("delta_energy", 0.01)),
            weight_operating_cost=float(
                objective_payload.get("weight_operating_cost", objective_payload.get("w_cost", 1.0))
            ),
            weight_risk=float(objective_payload.get("weight_risk", objective_payload.get("w_risk", 1.0))),
            weight_completion=float(
                objective_payload.get("weight_completion", objective_payload.get("w_completion", 0.4))
            ),
            weight_makespan_metric_only=float(
                objective_payload.get(
                    "weight_makespan_metric_only",
                    objective_payload.get("w_makespan_metric_only", objective_payload.get("w_makespan", 0.3)),
                )
            ),
            mode=str(objective_payload.get("mode") or "normalized_operating_cost_risk_weighted_completion"),
        ),
        path_option_policy_id=str(instance.get("logical_graph", {}).get("path_option_policy_id") or ""),
        service_timing_policy_id=service_timing_policy_id,
        reference_solution=instance.get("reference_solution") if isinstance(instance.get("reference_solution"), dict) else None,
    )
