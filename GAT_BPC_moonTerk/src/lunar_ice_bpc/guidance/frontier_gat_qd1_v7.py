"""Training-side definition for the V7 Native-frontier GAT.

The production pricing loop does not import this module.  Its state-dict names
and forward equations deliberately mirror the portable C++ implementation in
``native_pricer.cpp`` so parity can be audited before a bundle is frozen.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from math import sqrt
from pathlib import Path
from typing import Any, Iterable, Mapping


FRONTIER_FEATURE_SCHEMA_V1 = "lunar_ice_bpc.p0v5_frontier_probe_features.v1"
FRONTIER_GRAPH_SCHEMA_V1 = "lunar_ice_bpc.p0v5_frontier_depth_rc_graph.v1"
FRONTIER_BUNDLE_SCHEMA_V1 = "lunar_ice_bpc.p0v5_frontier_gat_native_bundle.v1"
FRONTIER_CHECKPOINT_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_frontier_gat_qd1_checkpoint.v1"
)
FRONTIER_DATASET_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_frontier_gat_qd1_training_dataset.v1"
)
FRONTIER_MATCHED_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_frontier_probe_matched_outcome.v1"
)
FRONTIER_RUNTIME_POLICY_V7 = "P0V5_ROOT_FRONTIER_GAT_QD1_SELECTOR_V7"

NODE_FEATURE_NAMES = (
    "active_mask",
    "log1p_label_count",
    "frontier_fraction",
    "terminal_fraction",
    "normalized_partial_rc_mean",
    "normalized_partial_rc_min",
    "normalized_partial_rc_max",
    "normalized_partial_rc_std",
    "normalized_visited_count_mean",
    "normalized_visited_count_std",
    "normalized_creation_age_mean",
    "normalized_creation_age_std",
    "unique_last_task_fraction",
    "normalized_last_task_entropy",
    "depth_bin_lower_bound",
    "rc_bin_midpoint",
)
EDGE_FEATURE_NAMES = (
    "self_loop",
    "depth_neighbor",
    "rc_neighbor",
    "parent_forward",
    "parent_reverse",
    "log1p_transition_count",
    "transition_fraction",
    "signed_depth_bin_delta",
    "signed_rc_bin_delta",
    "same_terminal_transition_fraction",
)
CONTEXT_FEATURE_NAMES = (
    "log1p_scale",
    "log1p_frontier_size",
    "terminal_fraction",
    "normalized_partial_rc_mean",
    "normalized_partial_rc_min",
    "normalized_partial_rc_std",
    "normalized_depth_mean",
    "normalized_depth_std",
    "log1p_dominance_checks_per_pop",
    "log1p_extended_labels_per_pop",
    "log1p_dominated_labels_per_pop",
    "log1p_max_visited_bucket_size",
    "max_visited_bucket_frontier_fraction",
    "subset_dominance_checks_per_pop",
    "subset_dominance_reject_fraction",
    "log1p_active_column_count",
    "active_column_count_present",
    "log1p_cg_round",
    "cg_round_present",
    "true_dual_l1_delta",
    "true_dual_l1_delta_present",
    "branch_decision_count",
    "active_cut_count",
    "log1p_active_cut_dual_abs_sum",
    "log1p_v5_midpoint_wall_seconds",
    "v5_midpoint_wall_present",
    "positive_dual_over_absolute_dual",
    "fleet_dual_over_absolute_dual",
)
MODEL_SEEDS = (61635, 91267, 170141)
PROBE_BOUNDARY = 4096


def _torch():
    import torch

    torch.set_num_threads(1)
    return torch


class FrontierGatLayer:
    """Factory wrapper keeping the module import Torch-free."""

    @staticmethod
    def build(hidden_size: int = 16, heads: int = 2):
        torch = _torch()
        nn = torch.nn

        class Layer(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.hidden_size = hidden_size
                self.heads = heads
                self.head_size = hidden_size // heads
                self.q = nn.Linear(hidden_size, hidden_size)
                self.k = nn.Linear(hidden_size, hidden_size)
                self.v = nn.Linear(hidden_size, hidden_size)
                self.edge_attention = nn.Linear(hidden_size, heads)
                self.output = nn.Linear(hidden_size, hidden_size)
                self.layer_norm = nn.LayerNorm(hidden_size, eps=1.0e-5)

            def forward(self, nodes, encoded_edges, edge_index):
                import torch.nn.functional as functional

                queries = self.q(nodes).reshape(-1, self.heads, self.head_size)
                keys = self.k(nodes).reshape(-1, self.heads, self.head_size)
                values = self.v(nodes).reshape(-1, self.heads, self.head_size)
                source, target = edge_index[0].long(), edge_index[1].long()
                logits = (
                    (queries[target] * keys[source]).sum(dim=-1)
                    / sqrt(float(self.head_size))
                    + self.edge_attention(encoded_edges)
                )
                logits = functional.leaky_relu(logits, negative_slope=0.2)
                aggregated = torch.zeros_like(queries)
                for target_index in range(nodes.shape[0]):
                    selected = target == target_index
                    for head in range(self.heads):
                        probabilities = torch.softmax(logits[selected, head], dim=0)
                        aggregated[target_index, head] = (
                            probabilities[:, None] * values[source[selected], head]
                        ).sum(dim=0)
                output = self.output(aggregated.reshape(-1, self.hidden_size))
                return torch.relu(self.layer_norm(output + nodes))

        return Layer()


def build_frontier_gat_model(*, dropout: float = 0.1, no_message: bool = False):
    torch = _torch()
    nn = torch.nn

    class Model(nn.Module):
        model_kind = "no_message" if no_message else "gat"

        def __init__(self) -> None:
            super().__init__()
            self.node_encoder = nn.Linear(len(NODE_FEATURE_NAMES), 16)
            self.edge_encoder = nn.Linear(len(EDGE_FEATURE_NAMES), 16)
            self.layers = nn.ModuleList(
                [FrontierGatLayer.build(), FrontierGatLayer.build()]
            )
            self.attention_pool = nn.Linear(16, 1)
            self.context_encoder = nn.Linear(len(CONTEXT_FEATURE_NAMES), 16)
            self.head = nn.Sequential(nn.Linear(96, 32), nn.ReLU(), nn.Linear(32, 3))
            self.dropout = float(dropout)

        def forward(self, *, node_features, edge_index, edge_features, context_features):
            import torch.nn.functional as functional

            nodes = torch.relu(self.node_encoder(node_features))
            encoded_edges = torch.relu(self.edge_encoder(edge_features))
            if not no_message:
                for layer in self.layers:
                    nodes = layer(nodes, encoded_edges, edge_index)
                    nodes = functional.dropout(
                        nodes, p=self.dropout, training=self.training
                    )
            node_mean = nodes.mean(dim=0)
            node_max = nodes.max(dim=0).values
            attention = torch.softmax(self.attention_pool(nodes).squeeze(-1), dim=0)
            attention_pool = (attention[:, None] * nodes).sum(dim=0)
            edge_mean = encoded_edges.mean(dim=0)
            edge_max = encoded_edges.max(dim=0).values
            context = torch.relu(self.context_encoder(context_features))
            pooled = torch.cat(
                (node_mean, node_max, attention_pool, edge_mean, edge_max, context),
                dim=0,
            )
            hidden = self.head[1](self.head[0](pooled))
            hidden = functional.dropout(hidden, p=self.dropout, training=self.training)
            values = torch.sigmoid(self.head[2](hidden))
            return {
                "p_benefit": values[0],
                "positive_gain": values[1],
                "p_adverse": values[2],
            }

    return Model()


def build_frontier_mlp_model(*, dropout: float = 0.1):
    """Endpoint-free control receiving every numeric node/edge/context value."""

    torch = _torch()
    nn = torch.nn

    class Model(nn.Module):
        model_kind = "mlp"

        def __init__(self) -> None:
            super().__init__()
            self.node_encoder = nn.Linear(len(NODE_FEATURE_NAMES), 16)
            self.edge_encoder = nn.Linear(len(EDGE_FEATURE_NAMES), 16)
            self.context_encoder = nn.Linear(len(CONTEXT_FEATURE_NAMES), 16)
            self.head = nn.Sequential(nn.Linear(80, 32), nn.ReLU(), nn.Linear(32, 3))
            self.dropout = float(dropout)

        def forward(self, *, node_features, edge_index, edge_features, context_features):
            del edge_index
            import torch.nn.functional as functional

            nodes = torch.relu(self.node_encoder(node_features))
            edges = torch.relu(self.edge_encoder(edge_features))
            context = torch.relu(self.context_encoder(context_features))
            pooled = torch.cat(
                (nodes.mean(0), nodes.max(0).values, edges.mean(0), edges.max(0).values, context)
            )
            hidden = functional.dropout(
                self.head[1](self.head[0](pooled)),
                p=self.dropout,
                training=self.training,
            )
            values = torch.sigmoid(self.head[2](hidden))
            return {
                "p_benefit": values[0],
                "positive_gain": values[1],
                "p_adverse": values[2],
            }

    return Model()


def build_frontier_linear_model():
    """Linear control over identical raw node/edge mean-max summaries."""

    torch = _torch()
    nn = torch.nn

    class Model(nn.Module):
        model_kind = "linear"

        def __init__(self) -> None:
            super().__init__()
            width = 2 * len(NODE_FEATURE_NAMES) + 2 * len(EDGE_FEATURE_NAMES) + len(
                CONTEXT_FEATURE_NAMES
            )
            self.output = nn.Linear(width, 3)

        def forward(self, *, node_features, edge_index, edge_features, context_features):
            del edge_index
            pooled = torch.cat((
                node_features.mean(0), node_features.max(0).values,
                edge_features.mean(0), edge_features.max(0).values,
                context_features,
            ))
            values = torch.sigmoid(self.output(pooled))
            return {
                "p_benefit": values[0],
                "positive_gain": values[1],
                "p_adverse": values[2],
            }

    return Model()


def parameter_count(model) -> int:
    return sum(int(parameter.numel()) for parameter in model.parameters())


def shuffled_topology(edge_index, *, state_hash: str):
    torch = _torch()
    shifted = edge_index.clone()
    offset = 1 + int(hashlib.sha256(state_hash.encode()).hexdigest()[:8], 16) % 63
    shifted[1] = (shifted[1] + offset) % 64
    return shifted


def _tensor_payload(tensor) -> dict[str, Any]:
    values = tensor.detach().cpu().double().contiguous()
    return {
        "shape": [int(value) for value in values.shape],
        "values": values.reshape(-1).tolist(),
    }


def portable_seed_payload(model, *, seed: int) -> dict[str, Any]:
    if getattr(model, "model_kind", "") != "gat":
        raise ValueError("only the full GAT may be exported to Native")
    state = model.state_dict()
    expected = {
        "node_encoder.weight",
        "node_encoder.bias",
        "edge_encoder.weight",
        "edge_encoder.bias",
        "context_encoder.weight",
        "context_encoder.bias",
        "attention_pool.weight",
        "attention_pool.bias",
        "head.0.weight",
        "head.0.bias",
        "head.2.weight",
        "head.2.bias",
        *(
            f"layers.{layer}.{name}"
            for layer in range(2)
            for name in (
                "q.weight",
                "q.bias",
                "k.weight",
                "k.bias",
                "v.weight",
                "v.bias",
                "edge_attention.weight",
                "edge_attention.bias",
                "output.weight",
                "output.bias",
                "layer_norm.weight",
                "layer_norm.bias",
            )
        ),
    }
    if set(state) != expected:
        raise ValueError("frontier GAT state-dict contract drift")
    return {
        "seed": int(seed),
        "tensors": {name: _tensor_payload(state[name]) for name in sorted(state)},
    }


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def bundle_sha256(payload: Mapping[str, Any]) -> str:
    normalized = dict(payload)
    normalized.pop("bundle_sha256", None)
    return hashlib.sha256(canonical_json_bytes(normalized)).hexdigest()


def export_portable_bundle(
    *,
    models: Iterable[tuple[int, Any]],
    normalization: Mapping[str, Mapping[str, Iterable[float]]],
    calibration_by_scale: Mapping[str, Mapping[str, Any]],
    thresholds_by_scale: Mapping[str, Mapping[str, float]],
    bindings: Mapping[str, Any],
    output_path: str | Path,
) -> dict[str, Any]:
    model_rows = [portable_seed_payload(model, seed=seed) for seed, model in models]
    if [row["seed"] for row in model_rows] != list(MODEL_SEEDS):
        raise ValueError("portable ensemble must use the three frozen V7 seeds")
    payload: dict[str, Any] = {
        "schema_version": FRONTIER_BUNDLE_SCHEMA_V1,
        "graph_schema_version": FRONTIER_GRAPH_SCHEMA_V1,
        "feature_schema_version": FRONTIER_FEATURE_SCHEMA_V1,
        "feature_names": {
            "node": list(NODE_FEATURE_NAMES),
            "edge": list(EDGE_FEATURE_NAMES),
            "context": list(CONTEXT_FEATURE_NAMES),
        },
        "normalization": {
            group: {
                "mean": [float(value) for value in row["mean"]],
                "scale": [float(value) for value in row["scale"]],
                "minimum": [float(value) for value in row["minimum"]],
                "maximum": [float(value) for value in row["maximum"]],
            } for group, row in normalization.items()
        },
        "calibration_by_scale": {
            str(scale): dict(row) for scale, row in calibration_by_scale.items()
        },
        "thresholds_by_scale": {
            str(scale): {name: float(value) for name, value in row.items()}
            for scale, row in thresholds_by_scale.items()
        },
        "layer_norm_epsilon": 1.0e-5,
        "models": model_rows,
        "bindings": dict(bindings),
    }
    payload["bundle_sha256"] = bundle_sha256(payload)
    output = Path(output_path)
    output.write_bytes(canonical_json_bytes(payload) + b"\n")
    return payload


@dataclass(frozen=True)
class FrontierGraph:
    node_features: tuple[tuple[float, ...], ...]
    edge_index: tuple[tuple[int, ...], tuple[int, ...]]
    edge_features: tuple[tuple[float, ...], ...]
    context_features: tuple[float, ...]
    graph_hash: str

    @classmethod
    def from_native_telemetry(cls, telemetry: Mapping[str, Any]) -> "FrontierGraph":
        rows = tuple(dict(row) for row in telemetry["edges"])
        graph = cls(
            node_features=tuple(tuple(map(float, row)) for row in telemetry["node_features"]),
            edge_index=(
                tuple(int(row["source"]) for row in rows),
                tuple(int(row["target"]) for row in rows),
            ),
            edge_features=tuple(tuple(map(float, row["features"])) for row in rows),
            context_features=tuple(map(float, telemetry["context_features"])),
            graph_hash=str(telemetry["graph_hash"]),
        )
        graph.validate()
        return graph

    def validate(self) -> None:
        if len(self.node_features) != 64 or any(
            len(row) != len(NODE_FEATURE_NAMES) for row in self.node_features
        ):
            raise ValueError("frontier graph node shape mismatch")
        if len(self.edge_index) != 2 or len(self.edge_index[0]) != len(self.edge_features):
            raise ValueError("frontier graph edge-index shape mismatch")
        if any(len(row) != len(EDGE_FEATURE_NAMES) for row in self.edge_features):
            raise ValueError("frontier graph edge-feature shape mismatch")
        if len(self.context_features) != len(CONTEXT_FEATURE_NAMES):
            raise ValueError("frontier graph context shape mismatch")

    def tensors(self, normalization: Mapping[str, Mapping[str, Iterable[float]]]):
        torch = _torch()

        def normalized(rows, group: str):
            value = torch.tensor(rows, dtype=torch.float64)
            mean = torch.tensor(tuple(normalization[group]["mean"]), dtype=torch.float64)
            scale = torch.tensor(tuple(normalization[group]["scale"]), dtype=torch.float64)
            return (value - mean) / scale

        return {
            "node_features": normalized(self.node_features, "node"),
            "edge_index": torch.tensor(self.edge_index, dtype=torch.long),
            "edge_features": normalized(self.edge_features, "edge"),
            "context_features": normalized(self.context_features, "context"),
        }
