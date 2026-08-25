"""Single-timepoint multi-resolution frontier GAT for Q0/QD1 observability.

The model fuses two deterministic views of the same 4096-pop Q0 frontier:
the complete 8x8 depth/RC mass graph and a local graph containing at most 256
sampled labels plus task nodes.  It performs no auxiliary rollout and creates
no additional label pop.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from math import isfinite
from typing import Any, Mapping, Sequence

from lunar_ice_bpc.guidance.base_frontier_gat_qd1_v9 import (
    BaseFrontierExample,
    pooled_numeric_signature as label_pooled_numeric_signature,
)
from lunar_ice_bpc.guidance.counterfactual_prefix_gat_qd1_v8 import (
    CONTEXT_FEATURE_NAMES,
    EDGE_FEATURE_NAMES as LABEL_EDGE_FEATURE_NAMES,
    NODE_FEATURE_NAMES as LABEL_NODE_FEATURE_NAMES,
    CounterfactualGraph,
    EdgeAttentionLayer,
)
from lunar_ice_bpc.guidance.frontier_gat_qd1_v7 import (
    EDGE_FEATURE_NAMES as CELL_EDGE_FEATURE_NAMES,
    NODE_FEATURE_NAMES as CELL_NODE_FEATURE_NAMES,
)


FEATURE_SCHEMA_V1 = "lunar_ice_bpc.p0v5_multires_frontier_features.v1"
GRAPH_SCHEMA_V1 = "lunar_ice_bpc.p0v5_multires_frontier_graph.v1"
CHECKPOINT_SCHEMA_V1 = "lunar_ice_bpc.p0v5_multires_frontier_gat_checkpoint.v1"
RUNTIME_POLICY_V1 = "P0V5_ROOT_MULTIRES_FRONTIER_GAT_QD1_SELECTOR_V1"
MODEL_KINDS = ("gat", "mlp", "linear", "no_message", "shuffled_topology")
MODEL_SEEDS = (61635, 91267, 170141)


def _torch():
    import torch

    torch.set_num_threads(1)
    return torch


@dataclass(frozen=True)
class CellMassGraph:
    node_features: tuple[tuple[float, ...], ...]
    edge_index: tuple[tuple[int, ...], tuple[int, ...]]
    edge_features: tuple[tuple[float, ...], ...]
    context_features: tuple[float, ...]
    graph_hash: str

    def validate(self) -> None:
        if len(self.node_features) != 64:
            raise ValueError("cell-mass graph must preserve all 64 cells")
        if any(len(row) != len(CELL_NODE_FEATURE_NAMES) for row in self.node_features):
            raise ValueError("cell-mass node-feature width drift")
        if len(self.edge_index) != 2 or len(self.edge_index[0]) != len(self.edge_index[1]):
            raise ValueError("cell-mass edge-index shape drift")
        if len(self.edge_index[0]) != len(self.edge_features):
            raise ValueError("cell-mass edge count drift")
        if any(len(row) != len(CELL_EDGE_FEATURE_NAMES) for row in self.edge_features):
            raise ValueError("cell-mass edge-feature width drift")
        if len(self.context_features) != len(CONTEXT_FEATURE_NAMES):
            raise ValueError("cell-mass context width drift")
        if any(
            endpoint < 0 or endpoint >= 64
            for side in self.edge_index for endpoint in side
        ):
            raise ValueError("cell-mass endpoint out of range")
        if not self.graph_hash:
            raise ValueError("cell-mass graph hash missing")
        for rows in (self.node_features, self.edge_features, (self.context_features,)):
            if any(not isfinite(float(value)) for row in rows for value in row):
                raise ValueError("cell-mass graph contains non-finite value")


@dataclass(frozen=True)
class MultiResolutionExample:
    label: BaseFrontierExample
    cell: CellMassGraph
    cell_graph_build_wall_seconds: float

    def validate(self) -> None:
        self.label.validate()
        self.cell.validate()
        if tuple(self.label.graph.context_features) != tuple(self.cell.context_features):
            raise ValueError("multi-resolution context binding mismatch")
        if self.cell_graph_build_wall_seconds <= 0.0:
            raise ValueError("cell graph build wall must be positive")


def cell_graph_from_payload(payload: Mapping[str, Any]) -> CellMassGraph:
    edges = tuple(dict(row) for row in payload.get("edges") or ())
    value = CellMassGraph(
        node_features=tuple(
            tuple(float(item) for item in row)
            for row in payload.get("node_features") or ()
        ),
        edge_index=(
            tuple(int(row["source"]) for row in edges),
            tuple(int(row["target"]) for row in edges),
        ),
        edge_features=tuple(
            tuple(float(item) for item in row["features"]) for row in edges
        ),
        context_features=tuple(
            float(item) for item in payload.get("context_features") or ()
        ),
        graph_hash=str(payload.get("graph_hash") or ""),
    )
    value.validate()
    return value


def _normalized_tensor(
    rows: Sequence[Sequence[float]] | Sequence[float],
    group: Mapping[str, Sequence[float]],
):
    torch = _torch()
    values = torch.tensor(rows, dtype=torch.float64)
    mean = torch.tensor(group["mean"], dtype=torch.float64)
    scale = torch.tensor(group["scale"], dtype=torch.float64)
    if bool((scale <= 0.0).any()):
        raise ValueError("normalization scale must be positive")
    return (values - mean) / scale


def multires_tensors(
    example: MultiResolutionExample,
    normalization: Mapping[str, Mapping[str, Sequence[float]]],
) -> dict[str, Any]:
    example.validate()
    torch = _torch()
    label = example.label.graph
    cell = example.cell
    return {
        "label": {
            "node_features": _normalized_tensor(
                label.node_features, normalization["label_node"]
            ),
            "edge_index": torch.tensor(label.edge_index, dtype=torch.long),
            "edge_features": _normalized_tensor(
                label.edge_features, normalization["label_edge"]
            ),
            "label_count": int(label.label_count),
        },
        "cell": {
            "node_features": _normalized_tensor(
                cell.node_features, normalization["cell_node"]
            ),
            "edge_index": torch.tensor(cell.edge_index, dtype=torch.long),
            "edge_features": _normalized_tensor(
                cell.edge_features, normalization["cell_edge"]
            ),
        },
        "context_features": _normalized_tensor(
            label.context_features, normalization["context"]
        ),
    }


def shuffled_multires_tensors(
    tensors: Mapping[str, Any], *, state_hash: str
) -> dict[str, Any]:
    output = {
        "label": dict(tensors["label"]),
        "cell": dict(tensors["cell"]),
        "context_features": tensors["context_features"],
    }
    for view in ("label", "cell"):
        edge_index = output[view]["edge_index"].clone()
        node_count = int(output[view]["node_features"].shape[0])
        offset = 1 + int(hashlib.sha256(
            f"multires:{state_hash}:{view}".encode()
        ).hexdigest()[:8], 16) % max(1, node_count - 1)
        edge_index[1] = (edge_index[1] + offset) % node_count
        output[view]["edge_index"] = edge_index
    return output


def build_multires_model(*, kind: str = "gat", dropout: float = 0.1):
    if kind not in MODEL_KINDS:
        raise ValueError(f"unsupported multi-resolution model kind {kind!r}")
    torch = _torch()
    nn = torch.nn

    class Model(nn.Module):
        model_kind = kind

        def __init__(self) -> None:
            super().__init__()
            hidden = 16
            self.label_node_encoder = nn.Linear(len(LABEL_NODE_FEATURE_NAMES), hidden)
            self.label_edge_encoder = nn.Linear(len(LABEL_EDGE_FEATURE_NAMES), hidden)
            self.cell_node_encoder = nn.Linear(len(CELL_NODE_FEATURE_NAMES), hidden)
            self.cell_edge_encoder = nn.Linear(len(CELL_EDGE_FEATURE_NAMES), hidden)
            self.label_layers = nn.ModuleList(
                [EdgeAttentionLayer.build(hidden, 2), EdgeAttentionLayer.build(hidden, 2)]
            )
            self.cell_layers = nn.ModuleList(
                [EdgeAttentionLayer.build(hidden, 2), EdgeAttentionLayer.build(hidden, 2)]
            )
            self.label_attention = nn.Linear(hidden, 1)
            self.task_attention = nn.Linear(hidden, 1)
            self.cell_attention = nn.Linear(hidden, 1)
            self.label_projection = nn.Linear(128, 32)
            self.cell_projection = nn.Linear(80, 32)
            self.context_encoder = nn.Linear(len(CONTEXT_FEATURE_NAMES), 16)
            self.head = nn.Sequential(
                nn.Linear(144, 32), nn.ReLU(), nn.Linear(32, 3)
            )
            linear_width = (
                4 * len(LABEL_NODE_FEATURE_NAMES)
                + 2 * len(LABEL_EDGE_FEATURE_NAMES)
                + 2 * len(CELL_NODE_FEATURE_NAMES)
                + 2 * len(CELL_EDGE_FEATURE_NAMES)
                + len(CONTEXT_FEATURE_NAMES)
            )
            self.linear_head = nn.Linear(linear_width, 3)
            self.dropout = float(dropout)

        @staticmethod
        def _attention_pool(nodes, layer):
            weights = torch.softmax(layer(nodes).squeeze(-1), dim=0)
            return (weights[:, None] * nodes).sum(0)

        def _message(self, nodes, edges, edge_index, layers):
            import torch.nn.functional as functional

            if kind not in {"gat", "shuffled_topology"}:
                return nodes
            for layer in layers:
                nodes = layer(nodes, edges, edge_index)
                nodes = functional.dropout(
                    nodes, p=self.dropout, training=self.training
                )
            return nodes

        def _label_embedding(self, graph):
            nodes = torch.relu(self.label_node_encoder(graph["node_features"]))
            edges = torch.relu(self.label_edge_encoder(graph["edge_features"]))
            nodes = self._message(
                nodes, edges, graph["edge_index"], self.label_layers
            )
            count = int(graph["label_count"])
            label_nodes = nodes[:count]
            task_nodes = nodes[count:]
            return torch.cat((
                label_nodes.mean(0), label_nodes.max(0).values,
                self._attention_pool(label_nodes, self.label_attention),
                task_nodes.mean(0), task_nodes.max(0).values,
                self._attention_pool(task_nodes, self.task_attention),
                edges.mean(0), edges.max(0).values,
            ))

        def _cell_embedding(self, graph):
            nodes = torch.relu(self.cell_node_encoder(graph["node_features"]))
            edges = torch.relu(self.cell_edge_encoder(graph["edge_features"]))
            nodes = self._message(
                nodes, edges, graph["edge_index"], self.cell_layers
            )
            return torch.cat((
                nodes.mean(0), nodes.max(0).values,
                self._attention_pool(nodes, self.cell_attention),
                edges.mean(0), edges.max(0).values,
            ))

        def forward(self, *, graph):
            import torch.nn.functional as functional

            if kind == "linear":
                label_nodes = graph["label"]["node_features"]
                count = int(graph["label"]["label_count"])
                label_edges = graph["label"]["edge_features"]
                cell_nodes = graph["cell"]["node_features"]
                cell_edges = graph["cell"]["edge_features"]
                raw = torch.cat((
                    label_nodes[:count].mean(0), label_nodes[:count].max(0).values,
                    label_nodes[count:].mean(0), label_nodes[count:].max(0).values,
                    label_edges.mean(0), label_edges.max(0).values,
                    cell_nodes.mean(0), cell_nodes.max(0).values,
                    cell_edges.mean(0), cell_edges.max(0).values,
                    graph["context_features"],
                ))
                logits = self.linear_head(raw)
            else:
                label = torch.relu(self.label_projection(
                    self._label_embedding(graph["label"])
                ))
                cell = torch.relu(self.cell_projection(
                    self._cell_embedding(graph["cell"])
                ))
                context = torch.relu(self.context_encoder(graph["context_features"]))
                fused = torch.cat((
                    label, cell, torch.abs(label - cell), label * cell, context
                ))
                hidden = self.head[1](self.head[0](fused))
                hidden = functional.dropout(
                    hidden, p=self.dropout, training=self.training
                )
                logits = self.head[2](hidden)
            values = torch.sigmoid(logits)
            return {
                "p_benefit": values[0],
                "positive_gain": values[1],
                "p_adverse": values[2],
            }

    return Model()


def parameter_count(model) -> int:
    return sum(int(parameter.numel()) for parameter in model.parameters())


def pooled_numeric_signature(example: MultiResolutionExample) -> tuple[float, ...]:
    def moments(rows: Sequence[Sequence[float]]) -> list[float]:
        output: list[float] = []
        for column in zip(*rows):
            values = [float(value) for value in column]
            output.extend((sum(values) / len(values), min(values), max(values)))
        return output

    return tuple(
        label_pooled_numeric_signature(example.label)
        + tuple(moments(example.cell.node_features))
        + tuple(moments(example.cell.edge_features))
    )
