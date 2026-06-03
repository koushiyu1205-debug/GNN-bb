"""Self-contained instance loading and path-option closure for BPC_future."""

from __future__ import annotations

from dataclasses import dataclass
import heapq
import json
import statistics
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ArcData:
    tau: float
    energy: float
    cost: float
    path: tuple[str, ...]


@dataclass(frozen=True)
class ArcOption:
    """A fixed physical path option for one directed logical edge."""

    option_id: str
    path_type: str
    aliases: tuple[str, ...]
    tau: float
    energy: float
    risk: float
    distance: float
    cost: float
    path_cells: tuple[tuple[int, int], ...] = ()
    path_xy: tuple[tuple[float, float], ...] = ()

    @property
    def arc_data(self) -> ArcData:
        return ArcData(
            tau=self.tau,
            energy=self.energy,
            cost=self.cost,
            path=tuple(f"{row},{col}" for row, col in self.path_cells),
        )


@dataclass(frozen=True)
class FutureData:
    instance: dict[str, Any]
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
    task_nodes: dict[int, str]
    closure: dict[tuple[int, int], ArcData]
    arc_options: dict[tuple[int, int], tuple[ArcOption, ...]]
    usable_battery_capacity: float
    reserve_energy_proxy: float
    survival_energy_rate: float
    task_name_to_id: dict[str, int]
    task_id_to_name: dict[int, str]
    objective_refs: dict[str, float]
    objective_weights: dict[str, float]

    def task_value(self, task_id: int, field: str) -> float:
        return float(self.instance["tasks"][str(int(task_id))][field])

    def arc(self, i: int, j: int) -> ArcData:
        return self.closure[(int(i), int(j))]

    def options(self, i: int, j: int) -> tuple[ArcOption, ...]:
        return self.arc_options[(int(i), int(j))]


def _candidate_paths(name: str, instance_dir: str | Path) -> list[Path]:
    root = Path(instance_dir)
    direct = Path(name)
    candidates = [
        root / f"instance_{name}.json",
        root / f"{name}.json",
        direct,
    ]
    if direct.exists():
        return candidates
    if root.exists():
        stem = Path(name).stem
        suffixes = {
            f"instance_{name}.json",
            f"{name}.json",
            f"{stem}.json",
            f"{stem}_logical_graph.json",
        }
        for suffix in suffixes:
            if not Path(suffix).is_absolute():
                candidates.extend(root.rglob(suffix))
    return candidates


def load_future_data(name: str, instance_dir: str | Path = "json/instances") -> FutureData:
    path = next((candidate for candidate in _candidate_paths(name, instance_dir) if candidate.exists()), None)
    if path is None:
        searched = ", ".join(str(candidate) for candidate in _candidate_paths(name, instance_dir))
        raise FileNotFoundError(f"instance {name!r} not found; searched: {searched}")
    instance = json.loads(path.read_text(encoding="utf-8"))
    if "logical_graph" in instance:
        return _load_logical_graph_future_data(instance, path, name)
    task_ids = tuple(sorted(int(task) for task in instance["tasks"].keys()))
    vehicles = instance["vehicles"]
    task_nodes = {int(task): str(payload["terrain_node"]) for task, payload in instance["tasks"].items()}
    task_nodes[0] = str(instance["base"]["terrain_node"])
    closure = _build_task_closure(instance, task_ids, task_nodes)
    arc_options = {
        key: (
            ArcOption(
                option_id=f"{key[0]}->{key[1]}:legacy",
                path_type="legacy",
                aliases=("legacy",),
                tau=value.tau,
                energy=value.energy,
                risk=0.0,
                distance=value.cost,
                cost=value.cost,
                path_cells=(),
                path_xy=(),
            ),
        )
        for key, value in closure.items()
    }
    battery = float(vehicles["B_use"])
    energy_limit = float(vehicles["B_use"])
    return FutureData(
        instance=instance,
        instance_path=path,
        name=str(instance.get("name", name)),
        tasks=task_ids,
        vehicles=tuple(range(1, int(vehicles["R_bar"]) + 1)),
        sortie_limit=int(vehicles["S_bar"]),
        capacity=float(vehicles["Q"]),
        energy_limit=energy_limit,
        rho=float(vehicles["rho"]),
        fixed_vehicle_cost=float(vehicles["F"]),
        horizon=float(vehicles["H"]),
        task_nodes=task_nodes,
        closure=closure,
        arc_options=arc_options,
        usable_battery_capacity=battery,
        reserve_energy_proxy=max(0.0, battery - energy_limit),
        survival_energy_rate=0.0,
        task_name_to_id={str(task): int(task) for task in task_ids},
        task_id_to_name={int(task): str(task) for task in task_ids},
        objective_refs={"distance": 1.0, "energy": 1.0, "risk": 1.0},
        objective_weights={"distance": 1.0, "energy": 0.0, "risk": 0.0},
    )


def _load_logical_graph_future_data(payload: dict[str, Any], path: Path, name: str) -> FutureData:
    logical = payload["logical_graph"]
    scenario = _load_scenario_for_logical_graph(payload, path)
    task_name_to_id = _logical_task_name_map(logical)
    task_ids = tuple(sorted(task_name_to_id.values()))
    task_id_to_name = {value: key for key, value in task_name_to_id.items()}
    tasks_payload = _logical_tasks_payload(scenario, task_name_to_id)
    vehicle = dict(scenario.get("vehicle", {}))
    scheduling = dict(scenario.get("scheduling", {}))
    objective = dict(scheduling.get("objective", {}))
    objective_weights = {
        "distance": float(objective.get("travel_cost_weight", 1.0)),
        "energy": float(objective.get("energy_cost_weight", 0.25)),
        "risk": float(objective.get("risk_cost_weight", 8.0)),
    }
    raw_options = _raw_arc_options(logical)
    refs = _objective_refs(raw_options)
    arc_options = _build_logical_arc_options(raw_options, refs, objective_weights)
    closure = {
        key: min(options, key=lambda option: (option.cost, option.tau, option.energy)).arc_data
        for key, options in arc_options.items()
    }
    battery = float(vehicle.get("usable_battery_capacity_proxy", vehicle.get("B_use", 80.0)))
    reserve = float(vehicle.get("survival_energy_reserve_proxy", max(0.0, battery - float(vehicle.get("max_roundtrip_energy_proxy", battery)))))
    energy_limit = float(vehicle.get("max_roundtrip_energy_proxy", max(0.0, battery - reserve)))
    if energy_limit > battery - reserve + 1.0e-9:
        energy_limit = max(0.0, battery - reserve)
    instance = {
        "name": str(scenario.get("id", scenario.get("instance_id", path.stem.replace("_logical_graph", "")))),
        "tasks": tasks_payload,
        "base": {"terrain_node": "depot", "xy_km": scenario.get("depot", {}).get("xy_km", [10.0, 10.0])},
        "vehicles": {
            "R_bar": int(vehicle.get("R_bar", vehicle.get("fleet_size", 1))),
            "S_bar": int(vehicle.get("S_bar", vehicle.get("max_sorties_per_vehicle", 8))),
            "Q": float(vehicle.get("Q", vehicle.get("capacity_task_units", 6.0))),
            "B_use": energy_limit,
            "rho": float(vehicle.get("rho", vehicle.get("recharge_power_proxy_per_min", 2.0))),
            "F": float(vehicle.get("F", vehicle.get("fixed_vehicle_cost", 50.0))),
            "H": float(vehicle.get("H", scheduling.get("horizon_min", 720.0))),
            "usable_battery_capacity_proxy": battery,
            "survival_energy_reserve_proxy": reserve,
        },
        "scheduling": scheduling,
        "terrain": {"logical_graph_path": str(path), "scenario_path": str(_scenario_path_from_payload(payload, path) or "")},
        "source_payload": {"logical_graph": True, "terrain": payload.get("terrain", {})},
    }
    return FutureData(
        instance=instance,
        instance_path=path,
        name=instance["name"],
        tasks=task_ids,
        vehicles=tuple(range(1, int(instance["vehicles"]["R_bar"]) + 1)),
        sortie_limit=int(instance["vehicles"]["S_bar"]),
        capacity=float(instance["vehicles"]["Q"]),
        energy_limit=energy_limit,
        rho=float(instance["vehicles"]["rho"]),
        fixed_vehicle_cost=float(instance["vehicles"]["F"]),
        horizon=float(instance["vehicles"]["H"]),
        task_nodes={0: "depot", **{task_id: task_id_to_name[task_id] for task_id in task_ids}},
        closure=closure,
        arc_options=arc_options,
        usable_battery_capacity=battery,
        reserve_energy_proxy=reserve,
        survival_energy_rate=float(vehicle.get("survival_energy_proxy_per_min", 0.0)),
        task_name_to_id=task_name_to_id,
        task_id_to_name=task_id_to_name,
        objective_refs=refs,
        objective_weights=objective_weights,
    )


def _build_task_closure(
    instance: dict[str, Any],
    task_ids: tuple[int, ...],
    task_nodes: dict[int, str],
) -> dict[tuple[int, int], ArcData]:
    graph: dict[str, list[tuple[str, dict[str, float]]]] = {}
    for edge in instance["terrain"]["edges"]:
        u = str(edge["u"])
        v = str(edge["v"])
        payload = {
            "time": float(edge["time"]),
            "energy": float(edge["energy"]),
            "cost": float(edge["cost"]),
        }
        graph.setdefault(u, []).append((v, payload))
        graph.setdefault(v, []).append((u, payload))

    closure: dict[tuple[int, int], ArcData] = {}
    all_ids = (0, *task_ids)
    for source_id in all_ids:
        source_node = task_nodes[int(source_id)]
        distances, parents = _shortest_paths(graph, source_node)
        for target_id in all_ids:
            target_node = task_nodes[int(target_id)]
            if target_node not in distances:
                raise ValueError(f"no terrain path from task {source_id} to {target_id}")
            tau, energy, cost = distances[target_node]
            closure[(int(source_id), int(target_id))] = ArcData(
                tau=round(tau, 6),
                energy=round(energy, 6),
                cost=round(cost, 6),
                path=tuple(_reconstruct_path(parents, source_node, target_node)),
            )
    return closure


def _scenario_path_from_payload(payload: dict[str, Any], path: Path) -> Path | None:
    candidates: list[Path] = []
    scenario = payload.get("scenario")
    if isinstance(scenario, dict):
        for key in ("path", "scenario_path", "source_path"):
            value = scenario.get(key)
            if value:
                candidates.append(Path(str(value)))
    terrain = payload.get("terrain")
    if isinstance(terrain, dict):
        value = terrain.get("scenario_path")
        if value:
            candidates.append(Path(str(value)))
    stem = path.name.replace("_logical_graph.json", ".json")
    candidates.append(path.parents[2] / "scenarios" / path.parent.name / stem) if len(path.parents) > 2 else None
    parts = list(path.parts)
    if "logical_graphs" in parts:
        index = parts.index("logical_graphs")
        inferred = Path(*parts[:index], "scenarios", *parts[index + 1 :])
        candidates.append(Path(str(inferred).replace("_logical_graph.json", ".json")))
    for candidate in candidates:
        if candidate.exists():
            return candidate
        relative = path.parent / candidate
        if relative.exists():
            return relative
    return None


def _load_scenario_for_logical_graph(payload: dict[str, Any], path: Path) -> dict[str, Any]:
    scenario_path = _scenario_path_from_payload(payload, path)
    if scenario_path is not None:
        return json.loads(scenario_path.read_text(encoding="utf-8"))
    scenario = payload.get("scenario")
    if isinstance(scenario, dict) and "tasks" in scenario and "vehicle" in scenario:
        return scenario
    raise ValueError(f"logical graph {path} does not include or reference a scenario JSON")


def _logical_task_name_map(logical: dict[str, Any]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for node in logical.get("nodes", []):
        node_id = str(node["id"])
        if node_id == "depot":
            continue
        if node_id.startswith("task_"):
            mapping[node_id] = int(node_id.split("_", 1)[1])
        else:
            digits = "".join(ch for ch in node_id if ch.isdigit())
            if not digits:
                raise ValueError(f"cannot map logical task node id {node_id!r} to an integer task id")
            mapping[node_id] = int(digits)
    return mapping


def _logical_tasks_payload(scenario: dict[str, Any], task_name_to_id: dict[str, int]) -> dict[str, dict[str, Any]]:
    payload: dict[str, dict[str, Any]] = {}
    for task in scenario.get("tasks", []):
        task_name = str(task["id"])
        task_id = task_name_to_id[task_name]
        service_time = float(task.get("sigma", task.get("service_time_min", 0.0)))
        service_energy = float(task.get("g", task.get("service_energy_proxy", 0.0)))
        service_cost = float(task.get("c_srv", task.get("service_cost", 0.0)))
        payload[str(task_id)] = {
            **task,
            "terrain_node": task_name,
            "d": float(task.get("d", task.get("demand", 1.0))),
            "sigma": service_time,
            "g": service_energy,
            "c_srv": service_cost,
            "r": float(task.get("r", task.get("ready_time_min", 0.0))),
            "D": float(task.get("D", task.get("due_time_min", 720.0))),
        }
    if set(payload) != {str(task_id) for task_id in task_name_to_id.values()}:
        missing = sorted({str(task_id) for task_id in task_name_to_id.values()} - set(payload))
        raise ValueError(f"scenario task payload missing logical tasks: {missing}")
    return payload


def _raw_arc_options(logical: dict[str, Any]) -> dict[tuple[int, int], list[dict[str, Any]]]:
    task_name_to_id = _logical_task_name_map(logical)

    def node_to_id(node: str) -> int:
        node = str(node)
        return 0 if node == "depot" else task_name_to_id[node]

    raw: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for edge in logical.get("edges", []):
        if not edge.get("feasible", True):
            continue
        key = (node_to_id(edge["from"]), node_to_id(edge["to"]))
        raw[key] = list(edge.get("path_options") or [])
        if not raw[key]:
            raw[key] = [edge]
    return raw


def _objective_refs(raw_options: dict[tuple[int, int], list[dict[str, Any]]]) -> dict[str, float]:
    distances: list[float] = []
    energies: list[float] = []
    risks: list[float] = []
    for options in raw_options.values():
        for option in options:
            distances.append(float(option.get("path_distance_km", option.get("distance_km", 0.0))))
            energies.append(float(option.get("energy_proxy", 0.0)))
            risks.append(float(option.get("risk_integral", 0.0)))
    return {
        "distance": _positive_median(distances),
        "energy": _positive_median(energies),
        "risk": _positive_median(risks),
    }


def _positive_median(values: list[float]) -> float:
    positives = [float(value) for value in values if float(value) > 1.0e-12]
    if not positives:
        return 1.0
    return max(1.0e-9, float(statistics.median(positives)))


def _build_logical_arc_options(
    raw_options: dict[tuple[int, int], list[dict[str, Any]]],
    refs: dict[str, float],
    weights: dict[str, float],
) -> dict[tuple[int, int], tuple[ArcOption, ...]]:
    arc_options: dict[tuple[int, int], tuple[ArcOption, ...]] = {}
    for key, options in raw_options.items():
        candidates = [_arc_option_from_payload(key, index, option, refs, weights) for index, option in enumerate(options)]
        pareto = _pareto_filter_arc_options(candidates)
        pareto.sort(key=lambda option: (option.cost, option.path_type, option.option_id))
        arc_options[key] = tuple(pareto)
    return arc_options


def _arc_option_from_payload(
    key: tuple[int, int],
    index: int,
    payload: dict[str, Any],
    refs: dict[str, float],
    weights: dict[str, float],
) -> ArcOption:
    path_type = str(payload.get("path_type", payload.get("best_option_by_generalized_cost", f"option_{index}")))
    aliases = tuple(str(alias) for alias in payload.get("aliases", (path_type,))) or (path_type,)
    distance = float(payload.get("path_distance_km", payload.get("distance_km", 0.0)))
    energy = float(payload.get("energy_proxy", 0.0))
    risk = float(payload.get("risk_integral", 0.0))
    cost = (
        float(weights.get("distance", 1.0)) * distance / refs["distance"]
        + float(weights.get("energy", 0.0)) * energy / refs["energy"]
        + float(weights.get("risk", 0.0)) * risk / refs["risk"]
    )
    return ArcOption(
        option_id=f"{key[0]}->{key[1]}:{path_type}:{index}",
        path_type=path_type,
        aliases=aliases,
        tau=round(float(payload.get("travel_time_min", payload.get("time_min", 0.0))), 6),
        energy=round(energy, 6),
        risk=round(risk, 6),
        distance=round(distance, 6),
        cost=round(cost, 6),
        path_cells=tuple((int(row), int(col)) for row, col in payload.get("path_cells", [])),
        path_xy=tuple((float(x), float(y)) for x, y in payload.get("path_xy", [])),
    )


def _pareto_filter_arc_options(options: list[ArcOption]) -> list[ArcOption]:
    """Keep only path options not dominated in objective and active resources."""

    kept: list[ArcOption] = []
    for option in options:
        dominated = False
        for other in options:
            if other is option:
                continue
            no_worse = (
                other.cost <= option.cost + 1.0e-9
                and other.tau <= option.tau + 1.0e-9
                and other.energy <= option.energy + 1.0e-9
            )
            strictly_better = (
                other.cost < option.cost - 1.0e-9
                or other.tau < option.tau - 1.0e-9
                or other.energy < option.energy - 1.0e-9
            )
            if no_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            kept.append(option)
    return kept or options[:1]


def _shortest_paths(
    graph: dict[str, list[tuple[str, dict[str, float]]]],
    source: str,
) -> tuple[dict[str, tuple[float, float, float]], dict[str, str]]:
    distances: dict[str, tuple[float, float, float]] = {source: (0.0, 0.0, 0.0)}
    parents: dict[str, str] = {}
    queue: list[tuple[float, str]] = [(0.0, source)]
    while queue:
        cost_so_far, node = heapq.heappop(queue)
        if cost_so_far > distances[node][2] + 1.0e-12:
            continue
        for nxt, payload in graph.get(node, []):
            old = distances.get(nxt)
            candidate = (
                distances[node][0] + payload["time"],
                distances[node][1] + payload["energy"],
                distances[node][2] + payload["cost"],
            )
            if old is None or candidate[2] < old[2] - 1.0e-12:
                distances[nxt] = candidate
                parents[nxt] = node
                heapq.heappush(queue, (candidate[2], nxt))
    return distances, parents


def _reconstruct_path(parents: dict[str, str], source: str, target: str) -> list[str]:
    if source == target:
        return [source]
    path = [target]
    node = target
    while node != source:
        node = parents[node]
        path.append(node)
    path.reverse()
    return path
