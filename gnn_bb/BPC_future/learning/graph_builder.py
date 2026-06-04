"""Build PyG graphs for learning-based dual stabilization.

This module is the translation boundary between the optimization code and the
learning stack.  It accepts either the current in-memory ``FutureData`` object or
a raw Moon Trek logical-graph payload, then emits a PyG ``Data`` object with a
flattened path-option representation:

``option_feat[o]`` belongs to directed pair edge ``option_pair_id[o]``.

Assumptions for V1:
- node id ``0`` is the depot;
- task ids are integer ids used by ``FutureData.tasks`` and RMP cover rows;
- the logical graph is directed and complete over depot + task nodes;
- every directed non-self pair has at least one physical path option.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union
import warnings

try:  # pragma: no cover - exercised in environments with the learning stack.
    import torch
    from torch import Tensor
    from torch_geometric.data import Data
except Exception as exc:  # pragma: no cover - current CI may not install PyG.
    raise ImportError(
        "BPC_future.learning.graph_builder requires torch and torch_geometric. "
        "Install the PyTorch/PyG stack before using learning graph builders."
    ) from exc

from BPC_future.core.data import ArcOption, FutureData


DEFAULT_NODE_FEATURE_SCHEMA: tuple[str, ...] = (
    "demand",
    "service_time",
    "time_window_start",
    "time_window_end",
    "x_coord",
    "y_coord",
    "is_depot",
    "service_energy",
    "local_risk",
)

DEFAULT_OPTION_FEATURE_SCHEMA: tuple[str, ...] = (
    "distance",
    "travel_time",
    "energy",
    "risk",
    "generalized_cost",
    "is_low_time",
    "is_low_energy",
    "is_low_risk",
    "option_rank",
    "option_count_for_pair",
)

CORE_OPTION_FIELDS: frozenset[str] = frozenset({"distance", "travel_time", "energy", "risk"})
DERIVED_OPTION_FIELDS: frozenset[str] = frozenset(DEFAULT_OPTION_FEATURE_SCHEMA) - CORE_OPTION_FIELDS


class FutureGraphData(Data):
    """PyG ``Data`` subclass with correct batching increments for option ids."""

    def __inc__(self, key: str, value: Any, *args: Any, **kwargs: Any) -> Any:
        if key == "pair_edge_index":
            return int(self.x.size(0))
        if key == "option_pair_id":
            return int(self.pair_edge_index.size(1))
        if key in {"task_ids", "node_ids"}:
            return 0
        return super().__inc__(key, value, *args, **kwargs)


@dataclass(frozen=True)
class _NodeRecord:
    node_id: int
    task_id: int | None
    payload: Mapping[str, Any]
    is_depot: bool


@dataclass(frozen=True)
class _OptionRecord:
    payload: Mapping[str, Any] | ArcOption
    rank: int
    count_for_pair: int


class FutureGraphBuilder:
    """Construct flattened PyG graph tensors for ``HierarchicalOptionGAT``.

    ``node_feature_schema`` and ``option_feature_schema`` must match the V1
    schema exactly unless a future checkpoint version explicitly changes them.
    When ``normalize=True``, ``normalizer`` must contain the flat checkpoint keys
    ``node_feature_mean/std`` and ``option_feature_mean/std``.
    """

    def __init__(
        self,
        node_feature_schema: Optional[Sequence[str]] = None,
        option_feature_schema: Optional[Sequence[str]] = None,
        include_depot: bool = True,
        normalize: bool = False,
        normalizer: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.node_feature_schema = tuple(node_feature_schema or DEFAULT_NODE_FEATURE_SCHEMA)
        self.option_feature_schema = tuple(option_feature_schema or DEFAULT_OPTION_FEATURE_SCHEMA)
        self.include_depot = bool(include_depot)
        self.normalize = bool(normalize)
        self.normalizer = dict(normalizer or {})
        self._validate_schema()
        if self.normalize:
            self._validate_normalizer()

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint: Mapping[str, Any],
        *,
        include_depot: bool = True,
        normalize: bool = True,
    ) -> "FutureGraphBuilder":
        """Create a builder that uses schema and normalizers from a checkpoint."""

        feature_schema = checkpoint.get("feature_schema")
        if not isinstance(feature_schema, Mapping):
            raise ValueError("checkpoint missing required mapping field 'feature_schema'")
        node_schema = _as_str_tuple(feature_schema.get("node"), field_name="feature_schema.node")
        option_schema = _as_str_tuple(feature_schema.get("option"), field_name="feature_schema.option")
        return cls(
            node_feature_schema=node_schema,
            option_feature_schema=option_schema,
            include_depot=include_depot,
            normalize=normalize,
            normalizer=checkpoint,
        )

    def build_from_logical_graph(
        self,
        logical_graph: Any,
        tasks: Any = None,
        depot: Any = None,
        config: Optional[Mapping[str, Any]] = None,
    ) -> Data:
        """Build a PyG graph from ``FutureData`` or a raw logical graph object.

        ``logical_graph`` may be:
        - a ``FutureData`` instance;
        - a full payload containing ``{"logical_graph": ..., "scenario": ...}``;
        - the inner ``logical_graph`` mapping, with ``tasks`` and ``depot``
          supplied separately from the scenario.
        """

        if isinstance(logical_graph, FutureData):
            return self.build_from_future_data(logical_graph)

        if isinstance(logical_graph, Mapping) and "logical_graph" in logical_graph:
            payload = dict(logical_graph)
            logical = _require_mapping(payload["logical_graph"], "logical_graph")
            scenario = payload.get("scenario")
            tasks_payload = tasks
            depot_payload = depot
            if isinstance(scenario, Mapping):
                tasks_payload = tasks_payload if tasks_payload is not None else scenario.get("tasks")
                depot_payload = depot_payload if depot_payload is not None else scenario.get("depot")
                scenario_vehicle = scenario.get("vehicle")
                scenario_scheduling = scenario.get("scheduling")
            else:
                scenario_vehicle = None
                scenario_scheduling = None
            merged_config = dict(config or {})
            if isinstance(scenario_vehicle, Mapping):
                merged_config.setdefault("horizon", scenario_vehicle.get("H"))
            if isinstance(scenario_scheduling, Mapping):
                merged_config.setdefault("horizon", scenario_scheduling.get("horizon_min"))
            return self._build_from_raw_logical(logical, tasks_payload, depot_payload, merged_config)

        if isinstance(logical_graph, Mapping):
            return self._build_from_raw_logical(logical_graph, tasks, depot, dict(config or {}))

        raise TypeError(
            "logical_graph must be a FutureData instance, a payload mapping, or a logical_graph mapping"
        )

    def build_from_future_data(self, data: FutureData) -> Data:
        """Build from the solver's current in-memory ``FutureData`` object."""

        nodes = self._future_data_nodes(data)
        pair_edge_index, option_records = self._future_data_pairs(data, nodes)
        return self._assemble_data(
            nodes=nodes,
            pair_edge_index=pair_edge_index,
            option_records=option_records,
            horizon=float(data.horizon),
        )

    def build_from_json(self, json_path: Union[str, Path]) -> Data:
        """Build from a Moon Trek logical graph JSON file."""

        path = Path(json_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "logical_graph" not in payload:
            raise ValueError(f"{path} does not contain a top-level 'logical_graph' object")
        payload = _payload_with_referenced_scenario(payload, path)
        return self.build_from_logical_graph(payload)

    def _validate_schema(self) -> None:
        if self.node_feature_schema != DEFAULT_NODE_FEATURE_SCHEMA:
            raise ValueError(
                "V1 node feature schema mismatch: "
                f"expected {list(DEFAULT_NODE_FEATURE_SCHEMA)}, got {list(self.node_feature_schema)}"
            )
        if self.option_feature_schema != DEFAULT_OPTION_FEATURE_SCHEMA:
            raise ValueError(
                "V1 option feature schema mismatch: "
                f"expected {list(DEFAULT_OPTION_FEATURE_SCHEMA)}, got {list(self.option_feature_schema)}"
            )

    def _validate_normalizer(self) -> None:
        for key, expected_dim in (
            ("node_feature_mean", len(self.node_feature_schema)),
            ("node_feature_std", len(self.node_feature_schema)),
            ("option_feature_mean", len(self.option_feature_schema)),
            ("option_feature_std", len(self.option_feature_schema)),
        ):
            if key not in self.normalizer:
                raise ValueError(f"normalizer missing required checkpoint field {key!r}")
            values = list(self.normalizer[key])
            if len(values) != expected_dim:
                raise ValueError(f"{key} length {len(values)} does not match expected dim {expected_dim}")
        feature_schema = self.normalizer.get("feature_schema")
        if feature_schema is not None:
            if not isinstance(feature_schema, Mapping):
                raise ValueError("normalizer feature_schema must be a mapping when present")
            node_schema = _as_str_tuple(feature_schema.get("node"), field_name="feature_schema.node")
            option_schema = _as_str_tuple(feature_schema.get("option"), field_name="feature_schema.option")
            if node_schema != self.node_feature_schema or option_schema != self.option_feature_schema:
                raise ValueError("checkpoint feature_schema does not match builder schema")

    def _future_data_nodes(self, data: FutureData) -> list[_NodeRecord]:
        if not self.include_depot:
            raise ValueError("V1 HierarchicalOptionGAT requires include_depot=True")
        records: list[_NodeRecord] = [
            _NodeRecord(
                node_id=0,
                task_id=None,
                payload=_future_depot_payload(data),
                is_depot=True,
            )
        ]
        for task_id in sorted(int(task) for task in data.tasks):
            task_payload = _require_mapping(data.instance.get("tasks", {}).get(str(task_id)), f"task {task_id}")
            records.append(
                _NodeRecord(
                    node_id=task_id,
                    task_id=task_id,
                    payload=task_payload,
                    is_depot=False,
                )
            )
        return records

    def _future_data_pairs(
        self,
        data: FutureData,
        nodes: Sequence[_NodeRecord],
    ) -> tuple[list[tuple[int, int]], list[list[_OptionRecord]]]:
        node_ids = [record.node_id for record in nodes]
        pair_edge_index: list[tuple[int, int]] = []
        option_records: list[list[_OptionRecord]] = []
        for src_pos, src_id in enumerate(node_ids):
            for dst_pos, dst_id in enumerate(node_ids):
                if src_id == dst_id:
                    continue
                key = (int(src_id), int(dst_id))
                options = tuple(data.arc_options.get(key, ()))
                if not options:
                    raise ValueError(f"FutureData arc_options missing directed pair {key}")
                pair_edge_index.append((src_pos, dst_pos))
                option_records.append(
                    [
                        _OptionRecord(payload=option, rank=rank, count_for_pair=len(options))
                        for rank, option in enumerate(options)
                    ]
                )
        return pair_edge_index, option_records

    def _build_from_raw_logical(
        self,
        logical: Mapping[str, Any],
        tasks: Any,
        depot: Any,
        config: Mapping[str, Any],
    ) -> Data:
        if not self.include_depot:
            raise ValueError("V1 HierarchicalOptionGAT requires include_depot=True")
        node_payloads = _raw_node_payloads(logical)
        task_payloads = _raw_task_payloads(tasks)
        depot_payload = _raw_depot_payload(depot, node_payloads)
        nodes = _raw_node_records(node_payloads, task_payloads, depot_payload)
        horizon = _coerce_optional_float(config.get("horizon"))
        if horizon is None:
            horizon = _infer_horizon(task_payloads, default=720.0)
        pair_edge_index, option_records = _raw_pair_options(logical, nodes)
        return self._assemble_data(
            nodes=nodes,
            pair_edge_index=pair_edge_index,
            option_records=option_records,
            horizon=horizon,
        )

    def _assemble_data(
        self,
        *,
        nodes: Sequence[_NodeRecord],
        pair_edge_index: Sequence[tuple[int, int]],
        option_records: Sequence[Sequence[_OptionRecord]],
        horizon: float,
    ) -> Data:
        if not nodes or not nodes[0].is_depot:
            raise ValueError("first node must be the depot in V1 graph construction")
        if len(pair_edge_index) != len(option_records):
            raise ValueError("pair_edge_index and option_records length mismatch")

        node_features = [
            self._node_features(record, horizon=horizon)
            for record in nodes
        ]
        option_features: list[list[float]] = []
        option_pair_id: list[int] = []
        for pair_id, records in enumerate(option_records):
            if not records:
                raise ValueError(f"directed pair id {pair_id} has no path options")
            for record in records:
                option_features.append(self._option_features(record))
                option_pair_id.append(pair_id)

        x = torch.tensor(node_features, dtype=torch.float32)
        pair_tensor = torch.tensor(pair_edge_index, dtype=torch.long).t().contiguous()
        option_feat = torch.tensor(option_features, dtype=torch.float32)
        option_pair_tensor = torch.tensor(option_pair_id, dtype=torch.long)
        task_ids = torch.tensor([int(record.task_id) for record in nodes if record.task_id is not None], dtype=torch.long)
        task_mask = torch.tensor([record.task_id is not None for record in nodes], dtype=torch.bool)
        node_ids = torch.tensor([int(record.node_id) for record in nodes], dtype=torch.long)

        graph = FutureGraphData(
            x=x,
            pair_edge_index=pair_tensor,
            option_feat=option_feat,
            option_pair_id=option_pair_tensor,
            task_ids=task_ids,
            task_mask=task_mask,
            node_ids=node_ids,
        )
        graph.node_feature_schema = list(self.node_feature_schema)
        graph.option_feature_schema = list(self.option_feature_schema)
        graph.learning_features_normalized = False
        if self.normalize:
            self._apply_normalizer(graph)
        return graph

    def _node_features(self, record: _NodeRecord, *, horizon: float) -> list[float]:
        if record.is_depot:
            x_coord, y_coord = _xy_from_payload(record.payload, "depot")
            values = {
                "demand": 0.0,
                "service_time": 0.0,
                "time_window_start": 0.0,
                "time_window_end": float(horizon),
                "x_coord": x_coord,
                "y_coord": y_coord,
                "is_depot": 1.0,
                "service_energy": 0.0,
                "local_risk": 0.0,
            }
            return [values[name] for name in self.node_feature_schema]

        task_label = f"task {record.task_id}"
        x_coord, y_coord = _xy_from_payload(record.payload, task_label)
        values = {
            "demand": _required_numeric(
                record.payload,
                ("demand", "d", "quantity"),
                task_label,
            ),
            "service_time": _required_numeric(
                record.payload,
                ("service_time", "service_time_min", "sigma"),
                task_label,
            ),
            "time_window_start": _required_numeric(
                record.payload,
                ("time_window_start", "ready_time", "ready_time_min", "r"),
                task_label,
            ),
            "time_window_end": _required_numeric(
                record.payload,
                ("time_window_end", "due_time", "due_time_min", "D"),
                task_label,
            ),
            "x_coord": x_coord,
            "y_coord": y_coord,
            "is_depot": 0.0,
            "service_energy": _required_numeric(
                record.payload,
                ("service_energy", "service_energy_proxy", "g"),
                task_label,
            ),
            "local_risk": _required_numeric(
                record.payload,
                ("local_risk", "risk"),
                task_label,
            ),
        }
        return [values[name] for name in self.node_feature_schema]

    def _option_features(self, record: _OptionRecord) -> list[float]:
        payload = record.payload
        if isinstance(payload, ArcOption):
            values = {
                "distance": float(payload.distance),
                "travel_time": float(payload.tau),
                "energy": float(payload.energy),
                "risk": float(payload.risk),
                "generalized_cost": float(payload.cost),
                "is_low_time": _path_type_flag(payload.path_type, payload.aliases, "low_time"),
                "is_low_energy": _path_type_flag(payload.path_type, payload.aliases, "low_energy"),
                "is_low_risk": _path_type_flag(payload.path_type, payload.aliases, "low_risk"),
                "option_rank": float(record.rank),
                "option_count_for_pair": float(record.count_for_pair),
            }
            return [values[name] for name in self.option_feature_schema]

        label = f"path option rank {record.rank}"
        values = {
            "distance": _required_numeric(payload, ("distance", "distance_km", "path_distance_km"), label),
            "travel_time": _required_numeric(payload, ("travel_time", "travel_time_min", "time_min", "tau"), label),
            "energy": _required_numeric(payload, ("energy", "energy_proxy"), label),
            "risk": _required_numeric(payload, ("risk", "risk_integral"), label),
            "generalized_cost": _optional_numeric_with_warning(
                payload,
                ("generalized_cost", "option_cost", "cost"),
                default=0.0,
                label=label,
                feature="generalized_cost",
            ),
            "is_low_time": _derived_flag(payload, "is_low_time", "low_time"),
            "is_low_energy": _derived_flag(payload, "is_low_energy", "low_energy"),
            "is_low_risk": _derived_flag(payload, "is_low_risk", "low_risk"),
            "option_rank": float(_optional_numeric(payload, ("option_rank", "rank"), default=float(record.rank))),
            "option_count_for_pair": float(
                _optional_numeric(payload, ("option_count_for_pair", "option_count"), default=float(record.count_for_pair))
            ),
        }
        return [values[name] for name in self.option_feature_schema]

    def _apply_normalizer(self, graph: Data) -> None:
        node_mean = torch.tensor(list(self.normalizer["node_feature_mean"]), dtype=graph.x.dtype, device=graph.x.device)
        node_std = torch.tensor(list(self.normalizer["node_feature_std"]), dtype=graph.x.dtype, device=graph.x.device)
        option_mean = torch.tensor(
            list(self.normalizer["option_feature_mean"]),
            dtype=graph.option_feat.dtype,
            device=graph.option_feat.device,
        )
        option_std = torch.tensor(
            list(self.normalizer["option_feature_std"]),
            dtype=graph.option_feat.dtype,
            device=graph.option_feat.device,
        )
        _assert_positive_std(node_std, "node_feature_std")
        _assert_positive_std(option_std, "option_feature_std")
        graph.x = (graph.x - node_mean) / node_std
        graph.option_feat = (graph.option_feat - option_mean) / option_std
        graph.learning_features_normalized = True


def _future_depot_payload(data: FutureData) -> Mapping[str, Any]:
    base = data.instance.get("base", {})
    if not isinstance(base, Mapping):
        raise ValueError("FutureData.instance['base'] must be a mapping")
    return base


def _raw_node_payloads(logical: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    nodes = logical.get("nodes")
    if not isinstance(nodes, Sequence):
        raise ValueError("logical_graph.nodes must be a sequence")
    payloads: dict[str, Mapping[str, Any]] = {}
    for raw in nodes:
        node = _require_mapping(raw, "logical_graph node")
        node_id = str(node.get("id"))
        if not node_id:
            raise ValueError("logical_graph node missing nonempty 'id'")
        payloads[node_id] = node
    if "depot" not in payloads:
        raise ValueError("logical_graph.nodes must contain a 'depot' node")
    return payloads


def _payload_with_referenced_scenario(payload: Mapping[str, Any], path: Path) -> dict[str, Any]:
    result = dict(payload)
    scenario = result.get("scenario")
    if isinstance(scenario, Mapping) and "tasks" in scenario and "depot" in scenario:
        return result
    scenario_path = _referenced_scenario_path(result, path)
    if scenario_path is None:
        return result
    result["scenario"] = json.loads(scenario_path.read_text(encoding="utf-8"))
    return result


def _referenced_scenario_path(payload: Mapping[str, Any], path: Path) -> Path | None:
    candidates: list[Path] = []
    terrain = payload.get("terrain")
    if isinstance(terrain, Mapping) and terrain.get("scenario_path"):
        candidates.append(Path(str(terrain["scenario_path"])))
    scenario = payload.get("scenario")
    if isinstance(scenario, Mapping):
        for key in ("path", "scenario_path", "source_path"):
            if scenario.get(key):
                candidates.append(Path(str(scenario[key])))
    for candidate in candidates:
        if candidate.exists():
            return candidate
        relative = path.parent / candidate
        if relative.exists():
            return relative
    return None


def _raw_task_payloads(tasks: Any) -> dict[str, Mapping[str, Any]]:
    if tasks is None:
        raise ValueError("raw logical graph construction requires scenario tasks")
    payloads: dict[str, Mapping[str, Any]] = {}
    if isinstance(tasks, Mapping):
        iterator = tasks.items()
        for key, value in iterator:
            payload = dict(_require_mapping(value, f"task {key}"))
            payload.setdefault("id", f"task_{key}")
            payloads[str(payload["id"])] = payload
        return payloads
    if isinstance(tasks, Sequence) and not isinstance(tasks, (str, bytes)):
        for raw in tasks:
            payload = _require_mapping(raw, "scenario task")
            task_id = str(payload.get("id", ""))
            if not task_id:
                raise ValueError("scenario task missing nonempty 'id'")
            payloads[task_id] = payload
        return payloads
    raise ValueError("scenario tasks must be a mapping or sequence of mappings")


def _raw_depot_payload(depot: Any, node_payloads: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any]:
    if depot is None:
        return node_payloads["depot"]
    depot_payload = dict(_require_mapping(depot, "depot"))
    logical_depot = node_payloads.get("depot", {})
    merged = {**logical_depot, **depot_payload}
    return merged


def _raw_node_records(
    node_payloads: Mapping[str, Mapping[str, Any]],
    task_payloads: Mapping[str, Mapping[str, Any]],
    depot_payload: Mapping[str, Any],
) -> list[_NodeRecord]:
    records = [
        _NodeRecord(
            node_id=0,
            task_id=None,
            payload=depot_payload,
            is_depot=True,
        )
    ]
    task_items: list[tuple[int, str, Mapping[str, Any]]] = []
    for node_id, logical_node in node_payloads.items():
        if node_id == "depot":
            continue
        task_id = _task_id_from_node_id(node_id)
        scenario_task = task_payloads.get(node_id)
        if scenario_task is None:
            raise ValueError(f"scenario tasks missing logical node {node_id!r}")
        merged = {**logical_node, **scenario_task}
        task_items.append((task_id, node_id, merged))
    for task_id, _node_name, payload in sorted(task_items, key=lambda item: item[0]):
        records.append(_NodeRecord(node_id=task_id, task_id=task_id, payload=payload, is_depot=False))
    return records


def _raw_pair_options(
    logical: Mapping[str, Any],
    nodes: Sequence[_NodeRecord],
) -> tuple[list[tuple[int, int]], list[list[_OptionRecord]]]:
    node_name_by_task_id = {0: "depot"}
    for record in nodes:
        if record.task_id is not None:
            node_name_by_task_id[int(record.task_id)] = _node_name_from_payload(record.payload, int(record.task_id))
    position_by_node_name = {name: pos for pos, name in enumerate(node_name_by_task_id.values())}

    edge_map: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    edges = logical.get("edges")
    if not isinstance(edges, Sequence):
        raise ValueError("logical_graph.edges must be a sequence")
    for raw_edge in edges:
        edge = _require_mapping(raw_edge, "logical_graph edge")
        if not bool(edge.get("feasible", True)):
            continue
        src = str(edge.get("from", edge.get("source", "")))
        dst = str(edge.get("to", edge.get("target", "")))
        if not src or not dst:
            raise ValueError("logical_graph edge missing 'from'/'to'")
        options = edge.get("path_options")
        if options is None:
            options = [edge]
        if not isinstance(options, Sequence) or isinstance(options, (str, bytes)) or not options:
            raise ValueError(f"directed logical edge {src}->{dst} has no path_options")
        edge_map[(src, dst)] = [_require_mapping(option, f"path option {src}->{dst}") for option in options]

    pair_edge_index: list[tuple[int, int]] = []
    option_records: list[list[_OptionRecord]] = []
    ordered_names = [node_name_by_task_id[int(record.node_id)] for record in nodes]
    for src_pos, src_name in enumerate(ordered_names):
        for dst_pos, dst_name in enumerate(ordered_names):
            if src_pos == dst_pos:
                continue
            options = edge_map.get((src_name, dst_name))
            if not options:
                raise ValueError(f"logical graph missing feasible directed edge {src_name}->{dst_name}")
            pair_edge_index.append((position_by_node_name[src_name], position_by_node_name[dst_name]))
            option_records.append(
                [
                    _OptionRecord(payload=option, rank=rank, count_for_pair=len(options))
                    for rank, option in enumerate(options)
                ]
            )
    return pair_edge_index, option_records


def _node_name_from_payload(payload: Mapping[str, Any], task_id: int) -> str:
    return str(payload.get("id", f"task_{task_id}"))


def _task_id_from_node_id(node_id: str) -> int:
    if node_id.startswith("task_"):
        return int(node_id.split("_", 1)[1])
    digits = "".join(ch for ch in node_id if ch.isdigit())
    if not digits:
        raise ValueError(f"cannot map logical task node id {node_id!r} to integer task id")
    return int(digits)


def _xy_from_payload(payload: Mapping[str, Any], label: str) -> tuple[float, float]:
    if "xy_km" in payload:
        xy = payload["xy_km"]
    elif "xy" in payload:
        xy = payload["xy"]
    elif "coord" in payload:
        xy = payload["coord"]
    elif "x_coord" in payload and "y_coord" in payload:
        return float(payload["x_coord"]), float(payload["y_coord"])
    elif "x" in payload and "y" in payload:
        return float(payload["x"]), float(payload["y"])
    else:
        raise ValueError(f"{label} missing required coordinates (xy_km or x/y)")
    if not isinstance(xy, Sequence) or len(xy) != 2:
        raise ValueError(f"{label} coordinate field must contain exactly two values")
    return float(xy[0]), float(xy[1])


def _required_numeric(payload: Mapping[str, Any], aliases: Sequence[str], label: str) -> float:
    for key in aliases:
        if key in payload and payload[key] is not None:
            value = float(payload[key])
            if not math.isfinite(value):
                raise ValueError(f"{label} field {key!r} is not finite: {value}")
            return value
    raise ValueError(f"{label} missing required numeric field; accepted aliases: {list(aliases)}")


def _optional_numeric(payload: Mapping[str, Any], aliases: Sequence[str], *, default: float) -> float:
    for key in aliases:
        if key in payload and payload[key] is not None:
            value = float(payload[key])
            if not math.isfinite(value):
                raise ValueError(f"optional field {key!r} is not finite: {value}")
            return value
    return float(default)


def _optional_numeric_with_warning(
    payload: Mapping[str, Any],
    aliases: Sequence[str],
    *,
    default: float,
    label: str,
    feature: str,
) -> float:
    for key in aliases:
        if key in payload and payload[key] is not None:
            value = float(payload[key])
            if not math.isfinite(value):
                raise ValueError(f"{label} field {key!r} is not finite: {value}")
            return value
    warnings.warn(
        f"{label} missing derived feature {feature!r}; defaulting to {default}",
        RuntimeWarning,
        stacklevel=3,
    )
    return float(default)


def _derived_flag(payload: Mapping[str, Any], explicit_key: str, alias: str) -> float:
    if explicit_key in payload:
        return float(bool(payload[explicit_key]))
    path_type = str(payload.get("path_type", ""))
    aliases = payload.get("aliases", ())
    if isinstance(aliases, str):
        aliases = (aliases,)
    aliases_tuple = tuple(str(item) for item in aliases) if isinstance(aliases, Sequence) else ()
    return _path_type_flag(path_type, aliases_tuple, alias)


def _path_type_flag(path_type: str, aliases: Sequence[str], target: str) -> float:
    tokens = {str(path_type)}
    tokens.update(str(alias) for alias in aliases)
    return 1.0 if target in tokens else 0.0


def _coerce_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    result = float(value)
    if not math.isfinite(result):
        return None
    return result


def _infer_horizon(task_payloads: Mapping[str, Mapping[str, Any]], *, default: float) -> float:
    due_values: list[float] = []
    for task in task_payloads.values():
        try:
            due_values.append(_required_numeric(task, ("time_window_end", "due_time", "due_time_min", "D"), "task"))
        except ValueError:
            continue
    return max(due_values) if due_values else float(default)


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return value


def _as_str_tuple(value: Any, *, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence of strings")
    return tuple(str(item) for item in value)


def _assert_positive_std(std: Tensor, name: str) -> None:
    if bool(torch.any(~torch.isfinite(std))):
        raise ValueError(f"{name} contains NaN or Inf")
    if bool(torch.any(std <= 0)):
        raise ValueError(f"{name} must be strictly positive")
