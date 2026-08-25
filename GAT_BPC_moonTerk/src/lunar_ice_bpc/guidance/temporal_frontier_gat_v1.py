"""Training-side shared-encoder Temporal-GAT for reversible QD1 trials.

The production pricing loop never imports Torch from this module.  Native
telemetry is converted into two cell graphs and two deterministic label-sample
graphs; encoder weights are shared across time and scale, while scale30/50 use
separate calibrated output heads.
"""

from __future__ import annotations

import hashlib
import json
from math import isfinite, sqrt
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


DATASET_SCHEMA = "lunar_ice_bpc.p0v5_temporal_frontier_gat_dataset.v1"
CHECKPOINT_SCHEMA = "lunar_ice_bpc.p0v5_temporal_frontier_gat_checkpoint.v1"
BUNDLE_SCHEMA = "lunar_ice_bpc.p0v5_temporal_frontier_gat_bundle.v2"
CELL_NODE_WIDTH = 16
CELL_EDGE_WIDTH = 10
LABEL_NODE_WIDTH = 40
LABEL_EDGE_WIDTH = 11
COUNTER_WIDTH = 24
CONTEXT_WIDTH = 28
HIDDEN = 32
HEADS = 4
SEEDS = (61635, 91267, 170141)
from lunar_ice_bpc.guidance.frontier_gat_qd1_v7 import (  # noqa: E402
    EDGE_FEATURE_NAMES as CELL_EDGE_FEATURE_NAMES,
    NODE_FEATURE_NAMES as CELL_NODE_FEATURE_NAMES,
)
COUNTER_FEATURE_NAMES = tuple(
    name for base in (
        "processed_labels", "extended_labels", "dominated_labels",
        "dominance_candidate_checks", "subset_dominance_candidate_checks",
        "subset_dominance_rejected_labels", "frontier_size",
        "max_visited_bucket_size", "negative_label_events",
    ) for name in (f"{base}_delta", f"{base}_ratio")
) + (
    "best_true_rc_delta", "best_true_rc_abs_delta",
    "frontier_survival_fraction", "frontier_churn",
    "new_label_fraction", "reserved_zero_no_wall_time",
)
CONTEXT_FEATURE_NAMES = (
    "log1p_true_task_dual_count", "true_task_dual_mean",
    "true_task_dual_abs_mean", "true_task_dual_min", "true_task_dual_max",
    "fleet_dual", "log1p_cut_dual_count", "cut_dual_abs_sum",
    "log1p_active_cut_count", "log1p_branch_decision_count",
    "cut_state_enabled", "cut_dual_projection_enabled",
    "log1p_harvest_target", "log1p_admission_batch_size",
    "log1p_raw_negative_pool_size", "log1p_active_column_count",
    "active_column_count_present", "log1p_root_cg_round",
    "root_cg_round_present", "true_dual_l1_delta",
    "true_dual_l1_delta_present", "log1p_memory_limit_gb",
    "log1p_wall_limit_seconds", "exact_negative_escape_enabled",
    "log1p_v5_midpoint_wall_seconds", "v5_midpoint_wall_present",
    "active_cut_context", "active_branch_context",
)

# The first 24/8 entries are Native label features/edges.  The remaining
# entries are deterministic task-node and label-task/task-interaction fields,
# matching the counterfactual V8 materializer used by corpus construction.
from lunar_ice_bpc.guidance.counterfactual_prefix_gat_qd1_v8 import (  # noqa: E402
    EDGE_FEATURE_NAMES as _COUNTERFACTUAL_EDGE_FEATURE_NAMES,
    NODE_FEATURE_NAMES as LABEL_TASK_NODE_FEATURE_NAMES,
)
LABEL_TASK_EDGE_FEATURE_NAMES = (
    *_COUNTERFACTUAL_EDGE_FEATURE_NAMES,
    "same_depth_rc_cell_membership",
)


def _torch():
    import torch

    torch.set_num_threads(1)
    return torch


def _gat_layer(*, no_message: bool = False):
    torch = _torch()
    nn = torch.nn

    class Layer(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.q = nn.Linear(HIDDEN, HIDDEN)
            self.k = nn.Linear(HIDDEN, HIDDEN)
            self.v = nn.Linear(HIDDEN, HIDDEN)
            self.edge_attention = nn.Linear(HIDDEN, HEADS)
            self.output = nn.Linear(HIDDEN, HIDDEN)
            self.norm = nn.LayerNorm(HIDDEN, eps=1.0e-5)

        def forward(self, nodes, encoded_edges, edge_index):
            if no_message:
                return nodes
            import torch.nn.functional as F

            source, target = edge_index[0].long(), edge_index[1].long()
            head_width = HIDDEN // HEADS
            q = self.q(nodes).reshape(-1, HEADS, head_width)
            k = self.k(nodes).reshape(-1, HEADS, head_width)
            v = self.v(nodes).reshape(-1, HEADS, head_width)
            logits = (q[target] * k[source]).sum(-1) / sqrt(head_width)
            logits = F.leaky_relu(
                logits + self.edge_attention(encoded_edges), 0.2
            )
            aggregate = torch.zeros_like(q)
            expanded_target = target[:, None].expand(-1, HEADS)
            maximum = torch.full(
                (nodes.shape[0], HEADS), -torch.inf,
                dtype=logits.dtype, device=logits.device,
            )
            maximum.scatter_reduce_(
                0, expanded_target, logits, reduce="amax", include_self=True
            )
            exponent = torch.exp(logits - maximum[target])
            denominator = torch.zeros(
                (nodes.shape[0], HEADS), dtype=logits.dtype,
                device=logits.device,
            )
            denominator.index_add_(0, target, exponent)
            for head in range(HEADS):
                aggregate[:, head].index_add_(
                    0, target,
                    exponent[:, head, None] * v[source, head],
                )
            has_incoming = denominator[:, 0] > 0
            aggregate[has_incoming] /= denominator[has_incoming, :, None]
            aggregate[~has_incoming] = q[~has_incoming]
            update = self.output(aggregate.reshape(-1, HIDDEN))
            return torch.relu(self.norm(nodes + update))

    return Layer()


def build_temporal_gat_model(*, dropout: float = 0.1, no_message: bool = False):
    torch = _torch()
    nn = torch.nn

    class Model(nn.Module):
        model_kind = "no_message" if no_message else "temporal_gat"

        def __init__(self) -> None:
            super().__init__()
            self.cell_node = nn.Linear(CELL_NODE_WIDTH, HIDDEN)
            self.cell_edge = nn.Linear(CELL_EDGE_WIDTH, HIDDEN)
            self.label_node = nn.Linear(LABEL_NODE_WIDTH, HIDDEN)
            self.label_edge = nn.Linear(LABEL_EDGE_WIDTH, HIDDEN)
            # The node/edge adapters are modality-specific because the raw
            # feature widths differ.  Both resolutions, both time points, and
            # both production scales then share one two-layer message encoder.
            self.shared_layers = nn.ModuleList(
                [_gat_layer(no_message=no_message) for _ in range(2)]
            )
            self.cell_attention = nn.Linear(HIDDEN, 1)
            self.label_attention = nn.Linear(HIDDEN, 1)
            self.task_attention = nn.Linear(HIDDEN, 1)
            # Cell graphs have one node type (96 pooled values); the sampled
            # label/task graph pools label and task nodes independently (192).
            # Each resolution then contributes h0, hK, signed delta, and
            # absolute delta.
            fusion_width = (
                4 * 3 * HIDDEN + 4 * 2 * 3 * HIDDEN +
                COUNTER_WIDTH + CONTEXT_WIDTH + 2
            )
            self.trunk = nn.Sequential(
                nn.Linear(fusion_width, 128), nn.ReLU(),
                nn.Linear(128, 64), nn.ReLU(),
            )
            self.scale_heads = nn.ModuleDict({
                "30": nn.Linear(64, 3),
                "50": nn.Linear(64, 3),
            })
            self.dropout = float(dropout)

        @staticmethod
        def _pool(nodes, attention, selected=None):
            if selected is not None:
                nodes = nodes[selected]
            if nodes.shape[0] == 0:
                raise ValueError("Temporal-GAT type-wise pool is empty")
            weights = torch.softmax(attention(nodes).squeeze(-1), dim=0)
            return torch.cat((
                nodes.mean(0), nodes.max(0).values,
                (weights[:, None] * nodes).sum(0),
            ))

        def _encode(self, graph, *, node_encoder, edge_encoder,
                    type_wise: bool):
            import torch.nn.functional as F

            nodes = torch.relu(node_encoder(graph["node_features"]))
            edges = torch.relu(edge_encoder(graph["edge_features"]))
            for layer in self.shared_layers:
                nodes = layer(nodes, edges, graph["edge_index"])
                nodes = F.dropout(nodes, p=self.dropout, training=self.training)
            if not type_wise:
                return self._pool(nodes, self.cell_attention)
            node_types = graph["node_types"].long()
            return torch.cat((
                self._pool(nodes, self.label_attention, node_types == 0),
                self._pool(nodes, self.task_attention, node_types == 1),
            ))

        @staticmethod
        def _temporal(left, right):
            return torch.cat((left, right, right - left, (right - left).abs()))

        def forward(self, *, cell_t0, cell_tk, label_t0, label_tk,
                    counter_features, context_features, scale: int):
            if int(scale) not in {30, 50}:
                raise ValueError("Temporal-GAT head is restricted to scale30/50")
            c0 = self._encode(
                cell_t0, node_encoder=self.cell_node, edge_encoder=self.cell_edge,
                type_wise=False,
            )
            ck = self._encode(
                cell_tk, node_encoder=self.cell_node, edge_encoder=self.cell_edge,
                type_wise=False,
            )
            l0 = self._encode(
                label_t0, node_encoder=self.label_node, edge_encoder=self.label_edge,
                type_wise=True,
            )
            lk = self._encode(
                label_tk, node_encoder=self.label_node, edge_encoder=self.label_edge,
                type_wise=True,
            )
            scale_one_hot = torch.tensor(
                [float(int(scale) == 30), float(int(scale) == 50)],
                dtype=counter_features.dtype,
                device=counter_features.device,
            )
            fused = torch.cat((
                self._temporal(c0, ck), self._temporal(l0, lk),
                counter_features, context_features, scale_one_hot,
            ))
            hidden = self.trunk(fused)
            values = torch.sigmoid(self.scale_heads[str(int(scale))](hidden))
            return {
                "p_benefit": values[0],
                "positive_gain": values[1],
                "p_adverse": values[2],
            }

    return Model()


def temporal_counter_features(
    start: Mapping[str, Any], end: Mapping[str, Any], *,
    survival_fraction: float = 0.0,
    frontier_churn: float = 0.0,
    new_label_fraction: float = 0.0,
) -> tuple[float, ...]:
    """Return the frozen 24-value signed response vector."""

    names = (
        "processed_labels", "extended_labels", "dominated_labels",
        "dominance_candidate_checks", "subset_dominance_candidate_checks",
        "subset_dominance_rejected_labels", "frontier_size",
        "max_visited_bucket_size", "negative_label_event_count",
    )
    values = []
    for name in names:
        left = float(start.get(name) or 0.0)
        right = float(end.get(name) or 0.0)
        values.extend((right - left, (right + 1.0) / (left + 1.0)))
    left_rc = start.get("best_true_reduced_cost")
    right_rc = end.get("best_true_reduced_cost")
    left_rc = 0.0 if left_rc is None else float(left_rc)
    right_rc = 0.0 if right_rc is None else float(right_rc)
    values.extend((right_rc - left_rc, abs(right_rc - left_rc)))
    values.extend((
        float(survival_fraction), float(frontier_churn),
        float(new_label_fraction), 0.0,
    ))
    if len(values) != COUNTER_WIDTH:
        raise AssertionError(len(values))
    return tuple(values)


def canonical_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def _tensor_payload(tensor) -> dict[str, Any]:
    values = tensor.detach().cpu().double().contiguous()
    return {
        "shape": [int(value) for value in values.shape],
        "values": values.reshape(-1).tolist(),
    }


def temporal_seed_payload(model, *, seed: int) -> dict[str, Any]:
    if getattr(model, "model_kind", "") != "temporal_gat":
        raise ValueError("only the full Temporal-GAT may be exported")
    state = model.state_dict()
    expected = {
        "cell_node.weight", "cell_node.bias",
        "cell_edge.weight", "cell_edge.bias",
        "label_node.weight", "label_node.bias",
        "label_edge.weight", "label_edge.bias",
        "cell_attention.weight", "cell_attention.bias",
        "label_attention.weight", "label_attention.bias",
        "task_attention.weight", "task_attention.bias",
        "trunk.0.weight", "trunk.0.bias",
        "trunk.2.weight", "trunk.2.bias",
        "scale_heads.30.weight", "scale_heads.30.bias",
        "scale_heads.50.weight", "scale_heads.50.bias",
        *(
            f"shared_layers.{layer}.{name}"
            for layer in range(2)
            for name in (
                "q.weight", "q.bias", "k.weight", "k.bias",
                "v.weight", "v.bias", "edge_attention.weight",
                "edge_attention.bias", "output.weight", "output.bias",
                "norm.weight", "norm.bias",
            )
        ),
    }
    if set(state) != expected:
        raise ValueError("Temporal-GAT state-dict contract drift")
    return {
        "seed": int(seed),
        "tensors": {name: _tensor_payload(state[name]) for name in sorted(state)},
    }


def temporal_simple_seed_payload(model, *, seed: int, kind: str) -> dict[str, Any]:
    if kind not in {"linear", "mlp", "no_message"}:
        raise ValueError("unsupported Temporal-GAT simple control")
    if kind == "no_message":
        if getattr(model, "model_kind", "") != "no_message":
            raise ValueError("no-message control/model mismatch")
        state = model.state_dict()
    else:
        state = model.state_dict()
        expected = (
            {"weight", "bias"} if kind == "linear"
            else {"0.weight", "0.bias", "2.weight", "2.bias"}
        )
        if set(state) != expected:
            raise ValueError(f"{kind} control state-dict drift")
    return {
        "seed": int(seed),
        "tensors": {name: _tensor_payload(state[name]) for name in sorted(state)},
    }


def _finite_group(
    source: Mapping[str, Iterable[float]], *, width: int, name: str
) -> dict[str, list[float]]:
    output = {}
    for key in ("mean", "scale", "minimum", "maximum"):
        values = [float(value) for value in source[key]]
        if len(values) != width or any(not isfinite(value) for value in values):
            raise ValueError(f"invalid {name} normalization {key}")
        output[key] = values
    if any(value <= 0.0 for value in output["scale"]):
        raise ValueError(f"nonpositive {name} normalization scale")
    return output


def export_temporal_bundle(
    *,
    models: Iterable[tuple[int, Any]],
    normalization: Mapping[str, Mapping[str, Iterable[float]]],
    calibration_by_scale: Mapping[str, Mapping[str, Any]],
    thresholds_by_scale: Mapping[str, Mapping[str, float]],
    trial_pop_budget_by_scale: Mapping[str, int],
    boundary_by_scale: Mapping[str, int],
    bindings: Mapping[str, Any],
    evaluation_controls: Mapping[str, Iterable[tuple[int, Any]]] | None = None,
    output_path: str | Path,
) -> dict[str, Any]:
    model_rows = [temporal_seed_payload(model, seed=seed) for seed, model in models]
    if [row["seed"] for row in model_rows] != list(SEEDS):
        raise ValueError("Temporal-GAT bundle requires the frozen three seeds")
    widths = {
        "cell_node": CELL_NODE_WIDTH, "cell_edge": CELL_EDGE_WIDTH,
        "node": LABEL_NODE_WIDTH, "edge": LABEL_EDGE_WIDTH,
        "counter": COUNTER_WIDTH, "context": CONTEXT_WIDTH,
    }
    payload: dict[str, Any] = {
        "schema_version": BUNDLE_SCHEMA,
        "graph_schema_version": (
            "lunar_ice_bpc.p0v5_temporal_multires_frontier_graph.v2"
        ),
        "feature_schema_version": (
            "lunar_ice_bpc.p0v5_temporal_multires_features.v2"
        ),
        "feature_names": {
            "cell_node": list(CELL_NODE_FEATURE_NAMES),
            "cell_edge": list(CELL_EDGE_FEATURE_NAMES),
            "node": list(LABEL_TASK_NODE_FEATURE_NAMES),
            "edge": list(LABEL_TASK_EDGE_FEATURE_NAMES),
            "counter": list(COUNTER_FEATURE_NAMES),
            "context": list(CONTEXT_FEATURE_NAMES),
        },
        "normalization": {
            name: _finite_group(normalization[name], width=width, name=name)
            for name, width in widths.items()
        },
        "calibration_by_scale": {
            str(scale): dict(value)
            for scale, value in calibration_by_scale.items()
        },
        "thresholds_by_scale": {
            str(scale): {name: float(value) for name, value in row.items()}
            for scale, row in thresholds_by_scale.items()
        },
        "boundary_by_scale": {
            str(scale): int(value) for scale, value in boundary_by_scale.items()
        },
        "trial_pop_budget_by_scale": {
            str(scale): int(value)
            for scale, value in trial_pop_budget_by_scale.items()
        },
        "models": model_rows,
        "controller_kind": "temporal_gat",
        "ood_policy": {
            "kind": "per_feature_fold_train_mean_std_envelope_v1",
            "standard_deviation_radius": 8.0,
            "zero_variance_epsilon": 1.0e-12,
            "action": "MIGRATE_BACK_TO_Q0",
        },
        "architecture_contract": {
            "hidden_size": HIDDEN,
            "attention_heads": HEADS,
            "message_layers": 2,
            "message_encoder_shared_across_resolution_time_and_scale": True,
            "pooling": "type_wise_mean_max_attention_v1",
            "trunk": [128, 64],
            "dropout": 0.1,
        },
        "evaluation_controls": {
            kind: {
                "development_only": True,
                "models": [
                    temporal_simple_seed_payload(model, seed=seed, kind=kind)
                    for seed, model in values
                ],
            }
            for kind, values in sorted((evaluation_controls or {}).items())
        },
        "bindings": dict(bindings),
        "layer_norm_epsilon": 1.0e-5,
    }
    payload["schema_hashes"] = {
        "graph_schema_sha256": hashlib.sha256(
            payload["graph_schema_version"].encode("utf-8")
        ).hexdigest(),
        "feature_schema_sha256": canonical_hash({
            "feature_schema_version": payload["feature_schema_version"],
            "feature_names": payload["feature_names"],
        }),
    }
    payload["bundle_sha256"] = canonical_hash(payload)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ) + "\n"
    if output.exists() and output.read_text(encoding="utf-8") != encoded:
        raise ValueError("immutable Temporal-GAT bundle drift")
    if not output.exists():
        output.write_text(encoded, encoding="utf-8")
    return payload


def temporal_graph_tensors(
    graph: Mapping[str, Any],
    normalization: Mapping[str, Mapping[str, Sequence[float]]],
    *,
    node_group: str,
    edge_group: str,
):
    torch = _torch()

    def normalized(rows, group):
        values = torch.tensor(rows, dtype=torch.float64)
        mean = torch.tensor(normalization[group]["mean"], dtype=torch.float64)
        scale = torch.tensor(normalization[group]["scale"], dtype=torch.float64)
        return (values - mean) / scale

    edge_index = graph.get("edge_index")
    if edge_index is None:
        edges = tuple(graph.get("edges") or ())
        edge_index = (
            [int(row["source"]) for row in edges],
            [int(row["target"]) for row in edges],
        )
        edge_features = [row["features"] for row in edges]
    else:
        edge_features = graph["edge_features"]
    raw_nodes = graph["node_features"]
    node_types = []
    if node_group == "node":
        for row in raw_nodes:
            is_label = float(row[24]) > 0.5
            is_task = float(row[25]) > 0.5
            if is_label == is_task:
                raise ValueError("Temporal-GAT node type is not one-hot")
            node_types.append(0 if is_label else 1)
    else:
        node_types = [0] * len(raw_nodes)
    return {
        "node_features": normalized(raw_nodes, node_group),
        "edge_index": torch.tensor(edge_index, dtype=torch.long),
        "edge_features": normalized(edge_features, edge_group),
        "node_types": torch.tensor(node_types, dtype=torch.long),
    }


def portable_temporal_forward(
    model,
    *,
    payload: Mapping[str, Any],
    bundle: Mapping[str, Any],
    scale: int,
) -> dict[str, float]:
    torch = _torch()
    normalization = bundle["normalization"]
    counter = torch.tensor(payload["counter_features"], dtype=torch.float64)
    context = torch.tensor(payload["context_features"], dtype=torch.float64)
    counter = (
        counter - torch.tensor(normalization["counter"]["mean"], dtype=torch.float64)
    ) / torch.tensor(normalization["counter"]["scale"], dtype=torch.float64)
    context = (
        context - torch.tensor(normalization["context"]["mean"], dtype=torch.float64)
    ) / torch.tensor(normalization["context"]["scale"], dtype=torch.float64)
    kwargs = {
        "cell_t0": temporal_graph_tensors(
            payload["cell_t0"], normalization,
            node_group="cell_node", edge_group="cell_edge",
        ),
        "cell_tk": temporal_graph_tensors(
            payload["cell_tk"], normalization,
            node_group="cell_node", edge_group="cell_edge",
        ),
        "label_t0": temporal_graph_tensors(
            payload["graph_t0"], normalization,
            node_group="node", edge_group="edge",
        ),
        "label_tk": temporal_graph_tensors(
            payload["graph_tk"], normalization,
            node_group="node", edge_group="edge",
        ),
        "counter_features": counter,
        "context_features": context,
        "scale": int(scale),
    }
    model = model.double().eval()
    with torch.inference_mode():
        values = model(**kwargs)
    return {name: float(value) for name, value in values.items()}
