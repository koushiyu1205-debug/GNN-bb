"""Low-cost single-view 256-label frontier GAT for Q0/QD1 observability.

The graph is captured once from the formal Q0 search at 4096 processed labels.
Unlike V8, this model consumes no counterfactual rollout and therefore adds no
duplicate prefix work.  The candidate and every control receive identical
node, edge, context, node-type and pooling inputs; only message endpoints are
removed or shuffled in the topology controls.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from math import sqrt
from typing import Any, Mapping, Sequence

from lunar_ice_bpc.guidance.counterfactual_prefix_gat_qd1_v8 import (
    CONTEXT_FEATURE_NAMES,
    EDGE_FEATURE_NAMES,
    NODE_FEATURE_NAMES,
    CounterfactualGraph,
    EdgeAttentionLayer,
)


FEATURE_SCHEMA_V1 = "lunar_ice_bpc.p0v5_base_label_frontier_features.v1"
GRAPH_SCHEMA_V1 = "lunar_ice_bpc.p0v5_base_label_frontier_graph.v1"
CHECKPOINT_SCHEMA_V1 = "lunar_ice_bpc.p0v5_base_label_frontier_gat_checkpoint.v1"
RUNTIME_POLICY_V1 = "P0V5_ROOT_BASE_LABEL_FRONTIER_GAT_QD1_SELECTOR_V1"
MODEL_KINDS = ("gat", "mlp", "linear", "no_message", "shuffled_topology")
MODEL_SEEDS = (61635, 91267, 170141)


def _torch():
    import torch

    torch.set_num_threads(1)
    return torch


@dataclass(frozen=True)
class BaseFrontierExample:
    graph: CounterfactualGraph
    context_id: str
    instance_hash: str
    state_hash: str
    scale: int
    ratio: float
    benefit: int
    positive_gain: float
    adverse: int
    qpf0_wall_seconds: float
    graph_build_wall_seconds: float

    def validate(self) -> None:
        self.graph.validate()
        if self.graph.label_count <= 0 or self.graph.label_count > 256:
            raise ValueError("base frontier must contain 1..256 sampled labels")
        if self.graph.task_count != self.scale:
            raise ValueError("task-node count must equal scale")
        if self.ratio <= 0.0 or self.qpf0_wall_seconds <= 0.0:
            raise ValueError("ratio and QPF0 wall must be positive")
        if self.benefit != int(self.ratio <= 0.98):
            raise ValueError("benefit target drift")
        if self.adverse != int(self.ratio >= 1.05):
            raise ValueError("adverse target drift")


def graph_from_payload(payload: Mapping[str, Any]) -> CounterfactualGraph:
    graph = CounterfactualGraph(
        node_features=tuple(
            tuple(float(value) for value in row)
            for row in payload["node_features"]
        ),
        edge_index=tuple(
            tuple(int(value) for value in side)
            for side in payload["edge_index"]
        ),
        edge_features=tuple(
            tuple(float(value) for value in row)
            for row in payload["edge_features"]
        ),
        context_features=tuple(float(value) for value in payload["context_features"]),
        graph_hash=str(payload["graph_hash"]),
        label_count=int(payload["label_count"]),
        task_count=int(payload["task_count"]),
    )
    graph.validate()
    return graph


def graph_tensors(
    graph: CounterfactualGraph,
    normalization: Mapping[str, Mapping[str, Sequence[float]]],
) -> dict[str, Any]:
    values = graph.tensors(normalization)
    values["label_count"] = int(graph.label_count)
    return values


def shuffled_graph_tensors(
    tensors: Mapping[str, Any], *, state_hash: str
) -> dict[str, Any]:
    output = dict(tensors)
    edge_index = output["edge_index"].clone()
    node_count = int(output["node_features"].shape[0])
    offset = 1 + int(
        hashlib.sha256(f"base-label:{state_hash}".encode()).hexdigest()[:8], 16
    ) % max(1, node_count - 1)
    edge_index[1] = (edge_index[1] + offset) % node_count
    output["edge_index"] = edge_index
    return output


def build_base_frontier_model(*, kind: str = "gat", dropout: float = 0.1):
    if kind not in MODEL_KINDS:
        raise ValueError(f"unsupported base-frontier model kind {kind!r}")
    torch = _torch()
    nn = torch.nn

    class Model(nn.Module):
        model_kind = kind

        def __init__(self) -> None:
            super().__init__()
            hidden = 16
            self.node_encoder = nn.Linear(len(NODE_FEATURE_NAMES), hidden)
            self.edge_encoder = nn.Linear(len(EDGE_FEATURE_NAMES), hidden)
            self.context_encoder = nn.Linear(len(CONTEXT_FEATURE_NAMES), hidden)
            self.layers = nn.ModuleList(
                [EdgeAttentionLayer.build(hidden, 2), EdgeAttentionLayer.build(hidden, 2)]
            )
            self.label_attention = nn.Linear(hidden, 1)
            self.task_attention = nn.Linear(hidden, 1)
            self.dropout = float(dropout)
            # label mean/max/attention + task mean/max/attention + edge
            # mean/max + context embedding.
            pooled_width = 16 * (3 + 3 + 2 + 1)
            if kind == "linear":
                self.head = nn.Linear(pooled_width, 3)
            else:
                self.head = nn.Sequential(
                    nn.Linear(pooled_width, 32), nn.ReLU(), nn.Linear(32, 3)
                )

        @staticmethod
        def _typed_pool(nodes, attention_layer, start: int, stop: int):
            selected = nodes[start:stop]
            if int(selected.shape[0]) == 0:
                return torch.zeros(
                    3 * int(nodes.shape[1]), dtype=nodes.dtype,
                    device=nodes.device,
                )
            attention = torch.softmax(attention_layer(selected).squeeze(-1), dim=0)
            return torch.cat((
                selected.mean(0), selected.max(0).values,
                (attention[:, None] * selected).sum(0),
            ))

        def forward(self, *, graph):
            import torch.nn.functional as functional

            nodes = torch.relu(self.node_encoder(graph["node_features"]))
            edges = torch.relu(self.edge_encoder(graph["edge_features"]))
            if kind not in {"no_message", "mlp", "linear"}:
                for layer in self.layers:
                    nodes = layer(nodes, edges, graph["edge_index"])
                    nodes = functional.dropout(
                        nodes, p=self.dropout, training=self.training
                    )
            label_count = int(graph["label_count"])
            pooled = torch.cat((
                self._typed_pool(
                    nodes, self.label_attention, 0, label_count
                ),
                self._typed_pool(
                    nodes, self.task_attention, label_count, int(nodes.shape[0])
                ),
                edges.mean(0), edges.max(0).values,
                torch.relu(self.context_encoder(graph["context_features"])),
            ))
            if kind == "linear":
                logits = self.head(pooled)
            else:
                hidden = self.head[1](self.head[0](pooled))
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


def pooled_numeric_signature(example: BaseFrontierExample) -> tuple[float, ...]:
    """Outcome-free signature used only for nearest-pair conflict auditing."""

    graph = example.graph
    labels = graph.node_features[:graph.label_count]
    tasks = graph.node_features[graph.label_count:]

    def moments(rows: Sequence[Sequence[float]]) -> list[float]:
        if not rows:
            return []
        width = len(rows[0])
        output = []
        for index in range(width):
            column = [float(row[index]) for row in rows]
            output.extend((sum(column) / len(column), min(column), max(column)))
        return output

    return tuple(
        moments(labels)
        + moments(tasks)
        + moments(graph.edge_features)
        + list(graph.context_features)
    )

