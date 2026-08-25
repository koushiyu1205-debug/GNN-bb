"""V8 counterfactual-prefix triplet graph and training-side models.

The auxiliary Native requests emit deterministic label samples only.  This
module adds task nodes and static task-interaction edges, constructs the
base/Q0/QD1 triplet, and defines the shared-weight Interaction-GAT.  Runtime
pricing does not import Torch; frozen weights are exported for portable C++
inference after the representation and safety gates pass.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from math import isfinite, log1p, sqrt
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


FEATURE_SCHEMA_V1 = "lunar_ice_bpc.p0v5_counterfactual_frontier_triplet.v1"
LABEL_GRAPH_SCHEMA_V1 = "lunar_ice_bpc.p0v5_frontier_label_sample_graph.v1"
PREFIX_PROBE_SCHEMA_V1 = "lunar_ice_bpc.p0v5_counterfactual_prefix_probe.v1"
PORTABLE_BUNDLE_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_counterfactual_prefix_gat_native_bundle.v1"
)
CHECKPOINT_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_counterfactual_prefix_gat_qd1_checkpoint.v1"
)
DATASET_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_counterfactual_prefix_gat_qd1_training_dataset.v1"
)
RUNTIME_POLICY_V8 = "P0V5_ROOT_COUNTERFACTUAL_PREFIX_GAT_QD1_SELECTOR_V8"

MODEL_SEEDS = (61635, 91267, 170141)
PREFIX_BOUNDARY = 4096
ROLLOUT_CHECKPOINTS = (128, 512, 2048)
LABEL_SAMPLE_CAP = 256

LABEL_FEATURE_NAMES = (
    "visited_fraction",
    "task_visit_fraction",
    "sortie_task_fraction",
    "sortie_count_fraction",
    "at_depot",
    "global_time_fraction",
    "global_slack_fraction",
    "sortie_demand_fraction",
    "sortie_energy_fraction",
    "sortie_shadow_fraction",
    "task_dual_reward_fraction",
    "cut_dual_reward_fraction",
    "positive_dual_reward_fraction",
    "remaining_positive_dual_fraction",
    "signed_log1p_partial_rc",
    "terminal",
    "creation_age",
    "q0_rank_percentile",
    "qd1_rank_percentile",
    "qd1_minus_q0_rank",
    "last_task_normalized",
    "last_task_present",
    "parent_present",
    "branch_terminal_feasible",
)
TASK_FEATURE_NAMES = (
    "node_type_label",
    "node_type_task",
    "task_demand",
    "task_service_time",
    "task_service_energy",
    "task_service_cost",
    "task_ready_time",
    "task_due_time",
    "task_shadow",
    "task_risk",
    "task_true_dual",
    "task_branch_incidence",
    "task_cut_incidence",
    "task_index_normalized",
    "task_static_present",
    "task_dual_present",
)
NODE_FEATURE_NAMES = LABEL_FEATURE_NAMES + TASK_FEATURE_NAMES
EDGE_FEATURE_NAMES = (
    "self_loop",
    "parent_forward",
    "parent_reverse",
    "same_dominance_surface",
    "log1p_multiplicity",
    "signed_depth_delta",
    "signed_rc_delta",
    "same_terminal_class",
    "label_last_task",
    "task_interaction",
)
CONTEXT_FEATURE_NAMES = tuple(
    f"native_context_{index}" for index in range(28)
)
COUNTER_DELTA_NAMES = (
    "processed_delta_q0",
    "processed_delta_qd1",
    "extended_delta_q0",
    "extended_delta_qd1",
    "dominated_delta_q0",
    "dominated_delta_qd1",
    "dominance_checks_delta_q0",
    "dominance_checks_delta_qd1",
    "subset_checks_delta_q0",
    "subset_checks_delta_qd1",
    "subset_reject_delta_q0",
    "subset_reject_delta_qd1",
    "frontier_size_delta_q0",
    "frontier_size_delta_qd1",
    "max_bucket_delta_q0",
    "max_bucket_delta_qd1",
    "negative_events_delta_q0",
    "negative_events_delta_qd1",
    "best_rc_improvement_q0",
    "best_rc_improvement_qd1",
    "base_survival_fraction_q0",
    "base_survival_fraction_qd1",
    "frontier_churn_q0",
    "frontier_churn_qd1",
)


def _torch():
    import torch

    torch.set_num_threads(1)
    return torch


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _finite_tuple(values: Iterable[object], *, size: int, name: str) -> tuple[float, ...]:
    row = tuple(float(value) for value in values)
    if len(row) != size or any(not isfinite(value) for value in row):
        raise ValueError(f"{name} must contain {size} finite values")
    return row


@dataclass(frozen=True)
class CounterfactualGraph:
    node_features: tuple[tuple[float, ...], ...]
    edge_index: tuple[tuple[int, ...], tuple[int, ...]]
    edge_features: tuple[tuple[float, ...], ...]
    context_features: tuple[float, ...]
    graph_hash: str
    label_count: int
    task_count: int

    def validate(self) -> None:
        if not self.node_features:
            raise ValueError("counterfactual graph cannot be empty")
        if any(len(row) != len(NODE_FEATURE_NAMES) for row in self.node_features):
            raise ValueError("counterfactual node-feature shape mismatch")
        if len(self.edge_index) != 2:
            raise ValueError("counterfactual edge-index rank mismatch")
        if len(self.edge_index[0]) != len(self.edge_features):
            raise ValueError("counterfactual edge count mismatch")
        if any(len(row) != len(EDGE_FEATURE_NAMES) for row in self.edge_features):
            raise ValueError("counterfactual edge-feature shape mismatch")
        if len(self.context_features) != len(CONTEXT_FEATURE_NAMES):
            raise ValueError("counterfactual context shape mismatch")
        if any(
            endpoint < 0 or endpoint >= len(self.node_features)
            for side in self.edge_index
            for endpoint in side
        ):
            raise ValueError("counterfactual edge endpoint out of range")

    def tensors(self, normalization: Mapping[str, Mapping[str, Sequence[float]]]):
        torch = _torch()

        def normalize(rows, group: str):
            values = torch.tensor(rows, dtype=torch.float64)
            mean = torch.tensor(normalization[group]["mean"], dtype=torch.float64)
            scale = torch.tensor(normalization[group]["scale"], dtype=torch.float64)
            if bool((scale <= 0).any()):
                raise ValueError("normalization scale must be positive")
            return (values - mean) / scale

        return {
            "node_features": normalize(self.node_features, "node"),
            "edge_index": torch.tensor(self.edge_index, dtype=torch.long),
            "edge_features": normalize(self.edge_features, "edge"),
            "context_features": normalize(self.context_features, "context"),
        }


@dataclass(frozen=True)
class CounterfactualTriplet:
    base: CounterfactualGraph
    q0: CounterfactualGraph
    qd1: CounterfactualGraph
    counter_deltas: tuple[float, ...]
    rollout_budget: int
    state_hash: str

    def validate(self) -> None:
        for graph in (self.base, self.q0, self.qd1):
            graph.validate()
        if len(self.counter_deltas) != len(COUNTER_DELTA_NAMES):
            raise ValueError("counter delta shape mismatch")
        if self.rollout_budget not in ROLLOUT_CHECKPOINTS:
            raise ValueError("counterfactual rollout budget is not frozen")
        if self.base.graph_hash == "":
            raise ValueError("counterfactual base graph hash is missing")


def _task_value(row: Mapping[str, object], *names: str) -> float:
    for name in names:
        if row.get(name) is not None:
            return float(row[name])
    return 0.0


def build_counterfactual_graph(
    native_graph: Mapping[str, Any],
    *,
    tasks: Sequence[Mapping[str, object]],
    arcs: Sequence[Mapping[str, object]],
    true_task_duals: Mapping[str, float],
    branch_pairs: Sequence[tuple[str, str]] = (),
    cut_task_sets: Sequence[Sequence[str]] = (),
) -> CounterfactualGraph:
    """Add deterministic task nodes and interaction edges to a Native sample."""

    if str(native_graph.get("schema_version")) != LABEL_GRAPH_SCHEMA_V1:
        raise ValueError("native label graph schema mismatch")
    label_rows = tuple(dict(row) for row in native_graph.get("label_nodes") or ())
    if len(label_rows) > LABEL_SAMPLE_CAP:
        raise ValueError("native label sample exceeds frozen cap")
    input_task_rows = tuple(dict(row) for row in tasks)
    input_task_ids = tuple(str(row.get("id")) for row in input_task_rows)
    if len(set(input_task_ids)) != len(input_task_ids):
        raise ValueError("task IDs must be unique")
    task_rows = tuple(
        sorted(input_task_rows, key=lambda row: str(row.get("id")))
    )
    task_ids = tuple(str(row.get("id")) for row in task_rows)
    task_index = {task_id: index for index, task_id in enumerate(task_ids)}
    scale = max(1, len(task_rows))
    horizon = max(
        1.0,
        max((_task_value(row, "due_time", "deadline") for row in task_rows), default=1.0),
    )
    demand_scale = max(1.0, max((_task_value(row, "demand") for row in task_rows), default=1.0))
    energy_scale = max(1.0, max((_task_value(row, "service_energy") for row in task_rows), default=1.0))
    cost_scale = max(1.0, max((abs(_task_value(row, "service_cost")) for row in task_rows), default=1.0))
    dual_scale = max(1.0, sum(abs(float(value)) for value in true_task_duals.values()))
    branch_degree = {task_id: 0 for task_id in task_ids}
    for left, right in branch_pairs:
        if left in branch_degree:
            branch_degree[left] += 1
        if right in branch_degree:
            branch_degree[right] += 1
    cut_degree = {task_id: 0 for task_id in task_ids}
    for task_set in cut_task_sets:
        for task_id in task_set:
            if task_id in cut_degree:
                cut_degree[task_id] += 1

    nodes: list[tuple[float, ...]] = []
    last_task_by_label: list[int | None] = []
    for row in label_rows:
        label_values = list(_finite_tuple(
            row.get("features") or (), size=len(LABEL_FEATURE_NAMES), name="label features"
        ))
        last_task = int(row.get("last_task_index", 2**63 - 1))
        if 0 <= last_task < len(input_task_ids):
            canonical_last_task = task_index[input_task_ids[last_task]]
            last_task_by_label.append(canonical_last_task)
            label_values[20] = float(canonical_last_task + 1) / float(scale)
        else:
            last_task_by_label.append(None)
            label_values[20] = 0.0
        nodes.append(
            tuple(label_values)
            + (1.0, 0.0)
            + (0.0,) * (len(TASK_FEATURE_NAMES) - 2)
        )
    label_count = len(nodes)
    for index, row in enumerate(task_rows):
        task_id = task_ids[index]
        task_features = (
            0.0,
            1.0,
            _task_value(row, "demand") / demand_scale,
            _task_value(row, "service_time") / horizon,
            _task_value(row, "service_energy") / energy_scale,
            _task_value(row, "service_cost") / cost_scale,
            _task_value(row, "ready_time", "release_time") / horizon,
            _task_value(row, "due_time", "deadline") / horizon,
            _task_value(row, "local_shadow_score", "shadow") / max(1.0, horizon),
            _task_value(row, "local_thermal_risk", "risk"),
            float(true_task_duals.get(task_id, 0.0)) / dual_scale,
            float(branch_degree[task_id]) / max(1.0, float(len(branch_pairs))),
            float(cut_degree[task_id]) / max(1.0, float(len(cut_task_sets))),
            float(index + 1) / float(scale),
            1.0,
            1.0 if task_id in true_task_duals else 0.0,
        )
        nodes.append((0.0,) * len(LABEL_FEATURE_NAMES) + task_features)

    edge_map: dict[tuple[int, int, int], tuple[float, ...]] = {}
    for row in native_graph.get("label_edges") or ():
        native_features = _finite_tuple(
            row.get("features") or (), size=8, name="native label edge features"
        )
        source, target = int(row["source"]), int(row["target"])
        edge_map[(source, target, 0)] = native_features + (0.0, 0.0)
    for label_index, task in enumerate(last_task_by_label):
        if task is None:
            continue
        task_node = label_count + task
        forward = (0.0,) * 8 + (1.0, 0.0)
        edge_map[(label_index, task_node, 1)] = forward
        edge_map[(task_node, label_index, 1)] = forward

    travel: dict[tuple[int, int], float] = {}
    for row in arcs:
        source = task_index.get(str(row.get("source")))
        target = task_index.get(str(row.get("target")))
        if source is None or target is None or source == target:
            continue
        key = (source, target)
        value = _task_value(row, "travel_time")
        travel[key] = min(value, travel.get(key, float("inf")))
    for source in range(len(task_rows)):
        candidates = sorted(
            (
                (travel.get((source, target), float("inf")), target)
                for target in range(len(task_rows))
                if target != source
            ),
            key=lambda item: (item[0], task_ids[item[1]]),
        )
        candidates = tuple(item for item in candidates if isfinite(item[0]))[:4]
        for _, target in candidates:
            feature = (0.0,) * 9 + (1.0,)
            left, right = label_count + source, label_count + target
            edge_map[(left, right, 2)] = feature
            edge_map[(right, left, 2)] = feature
    for left_id, right_id in branch_pairs:
        if left_id in task_index and right_id in task_index:
            feature = (0.0,) * 9 + (1.0,)
            left = label_count + task_index[left_id]
            right = label_count + task_index[right_id]
            edge_map[(left, right, 2)] = feature
            edge_map[(right, left, 2)] = feature
    for task_set in cut_task_sets:
        members = sorted({task_index[task_id] for task_id in task_set if task_id in task_index})
        for left_offset, left_index in enumerate(members):
            for right_index in members[left_offset + 1:]:
                feature = (0.0,) * 9 + (1.0,)
                left = label_count + left_index
                right = label_count + right_index
                edge_map[(left, right, 2)] = feature
                edge_map[(right, left, 2)] = feature
    for node in range(len(nodes)):
        edge_map.setdefault(
            (node, node, 4), (1.0,) + (0.0,) * (len(EDGE_FEATURE_NAMES) - 1)
        )
    ordered = sorted(edge_map.items())
    edge_index = (
        tuple(key[0] for key, _ in ordered),
        tuple(key[1] for key, _ in ordered),
    )
    edge_features = tuple(value for _, value in ordered)
    context = _finite_tuple(
        native_graph.get("context_features") or (),
        size=len(CONTEXT_FEATURE_NAMES),
        name="native context",
    )
    digest_payload = {
        "schema": FEATURE_SCHEMA_V1,
        "nodes": nodes,
        "edge_index": edge_index,
        "edge_features": edge_features,
        "context": context,
    }
    graph = CounterfactualGraph(
        node_features=tuple(nodes),
        edge_index=edge_index,
        edge_features=edge_features,
        context_features=context,
        graph_hash=hashlib.sha256(_canonical_bytes(digest_payload)).hexdigest(),
        label_count=label_count,
        task_count=len(task_rows),
    )
    graph.validate()
    return graph


def _endpoint(prefix: Mapping[str, Any], budget: int) -> Mapping[str, Any]:
    matches = [
        row
        for row in prefix.get("endpoints") or ()
        if int(row.get("rollout_budget", -1)) == int(budget)
    ]
    if len(matches) != 1:
        raise ValueError("prefix must contain exactly one requested endpoint")
    return matches[0]


def build_triplet(
    q0_prefix: Mapping[str, Any],
    qd1_prefix: Mapping[str, Any],
    *,
    rollout_budget: int,
    state_hash: str,
    tasks: Sequence[Mapping[str, object]],
    arcs: Sequence[Mapping[str, object]],
    true_task_duals: Mapping[str, float],
    branch_pairs: Sequence[tuple[str, str]] = (),
    cut_task_sets: Sequence[Sequence[str]] = (),
) -> CounterfactualTriplet:
    if rollout_budget not in ROLLOUT_CHECKPOINTS:
        raise ValueError("rollout budget is not in the frozen grid")
    for prefix, expected in (
        (q0_prefix, "counterfactual_q0_prefix"),
        (qd1_prefix, "counterfactual_qd1_prefix"),
    ):
        if not bool(prefix.get("complete")) or str(prefix.get("mode")) != expected:
            raise ValueError("counterfactual prefix is incomplete or has wrong mode")
        if bool(prefix.get("exact")) or not bool(prefix.get("truncated_diagnostic")):
            raise ValueError("counterfactual prefix exactness contract drift")
        if not bool(prefix.get("routes_suppressed")) or not bool(
            prefix.get("certificate_suppressed")
        ):
            raise ValueError("counterfactual prefix leaked a public result")
    q0_base_hash = str(q0_prefix.get("base_graph_hash") or "")
    qd1_base_hash = str(qd1_prefix.get("base_graph_hash") or "")
    if not q0_base_hash or q0_base_hash != qd1_base_hash:
        raise ValueError("Q0/QD1 prefix base graphs do not match")
    q0_endpoint = _endpoint(q0_prefix, rollout_budget)
    qd1_endpoint = _endpoint(qd1_prefix, rollout_budget)
    kwargs = {
        "tasks": tasks,
        "arcs": arcs,
        "true_task_duals": true_task_duals,
        "branch_pairs": branch_pairs,
        "cut_task_sets": cut_task_sets,
    }
    base = build_counterfactual_graph(q0_prefix["base_graph"], **kwargs)
    q0_graph = build_counterfactual_graph(q0_endpoint["graph"], **kwargs)
    qd1_graph = build_counterfactual_graph(qd1_endpoint["graph"], **kwargs)

    def delta(name: str, endpoint: Mapping[str, Any]) -> float:
        base_name = {
            "processed_labels": "base_processed_labels",
            "extended_labels": "base_extended_labels",
            "dominated_labels": "base_dominated_labels",
            "dominance_candidate_checks": "base_dominance_candidate_checks",
            "subset_dominance_candidate_checks": (
                "base_subset_dominance_candidate_checks"
            ),
            "subset_dominance_rejected_labels": (
                "base_subset_dominance_rejected_labels"
            ),
            "frontier_size": None,
            "max_visited_bucket_size": "base_max_visited_bucket_size",
            "negative_label_event_count": "base_negative_label_event_count",
        }[name]
        base_value = (
            q0_prefix["base_graph"].get("frontier_size")
            if base_name is None
            else q0_prefix.get(base_name)
        )
        return float(endpoint.get(name) or 0.0) - float(base_value or 0.0)

    base_frontier = max(1.0, float(q0_prefix["base_graph"].get("frontier_size") or 0.0))
    base_rc = float(q0_prefix.get("base_best_true_reduced_cost") or 0.0)
    q0_rc = base_rc - float(q0_endpoint.get("best_true_reduced_cost") or base_rc)
    qd1_rc = base_rc - float(qd1_endpoint.get("best_true_reduced_cost") or base_rc)
    pairs = (
        ("processed_labels", q0_endpoint, qd1_endpoint),
        ("extended_labels", q0_endpoint, qd1_endpoint),
        ("dominated_labels", q0_endpoint, qd1_endpoint),
        ("dominance_candidate_checks", q0_endpoint, qd1_endpoint),
        ("subset_dominance_candidate_checks", q0_endpoint, qd1_endpoint),
        ("subset_dominance_rejected_labels", q0_endpoint, qd1_endpoint),
        ("frontier_size", q0_endpoint, qd1_endpoint),
        ("max_visited_bucket_size", q0_endpoint, qd1_endpoint),
        ("negative_label_event_count", q0_endpoint, qd1_endpoint),
    )
    values: list[float] = []
    for name, q0_row, qd1_row in pairs:
        scale = base_frontier if name == "frontier_size" else max(1.0, float(PREFIX_BOUNDARY))
        values.extend((delta(name, q0_row) / scale, delta(name, qd1_row) / scale))
    values.extend((q0_rc, qd1_rc))
    values.extend(
        (
            float(q0_endpoint.get("base_label_survival_count") or 0.0) / base_frontier,
            float(qd1_endpoint.get("base_label_survival_count") or 0.0) / base_frontier,
            float(q0_endpoint.get("frontier_churn") or 0.0),
            float(qd1_endpoint.get("frontier_churn") or 0.0),
        )
    )
    triplet = CounterfactualTriplet(
        base=base,
        q0=q0_graph,
        qd1=qd1_graph,
        counter_deltas=_finite_tuple(
            values, size=len(COUNTER_DELTA_NAMES), name="counter deltas"
        ),
        rollout_budget=int(rollout_budget),
        state_hash=str(state_hash),
    )
    triplet.validate()
    return triplet


class EdgeAttentionLayer:
    @staticmethod
    def build(hidden: int = 16, heads: int = 2):
        torch = _torch()
        nn = torch.nn

        class Layer(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.hidden = hidden
                self.heads = heads
                self.head_width = hidden // heads
                self.q = nn.Linear(hidden, hidden)
                self.k = nn.Linear(hidden, hidden)
                self.v = nn.Linear(hidden, hidden)
                self.edge_attention = nn.Linear(hidden, heads)
                self.output = nn.Linear(hidden, hidden)
                self.layer_norm = nn.LayerNorm(hidden, eps=1.0e-5)

            def forward(self, nodes, encoded_edges, edge_index):
                import torch.nn.functional as functional

                source, target = edge_index[0].long(), edge_index[1].long()
                query = self.q(nodes).reshape(-1, self.heads, self.head_width)
                key = self.k(nodes).reshape(-1, self.heads, self.head_width)
                value = self.v(nodes).reshape(-1, self.heads, self.head_width)
                logits = (
                    (query[target] * key[source]).sum(-1) / sqrt(self.head_width)
                    + self.edge_attention(encoded_edges)
                )
                logits = functional.leaky_relu(logits, negative_slope=0.2)
                # Segment softmax by (target, head).  The original reference
                # loop is exact but prohibitively slow for the 256-label V8
                # sample and grouped OOF.  scatter_reduce/scatter_add preserve
                # the same message-passing equation and remain differentiable.
                segment = (
                    target[:, None] * self.heads
                    + torch.arange(self.heads, device=target.device)[None, :]
                ).reshape(-1)
                flat_logits = logits.reshape(-1)
                segment_count = int(nodes.shape[0]) * self.heads
                maximum = torch.full(
                    (segment_count,), -torch.inf,
                    dtype=flat_logits.dtype, device=flat_logits.device,
                )
                maximum.scatter_reduce_(
                    0, segment, flat_logits, reduce="amax", include_self=True
                )
                exponent = torch.exp(flat_logits - maximum[segment])
                denominator = torch.zeros(
                    segment_count, dtype=flat_logits.dtype,
                    device=flat_logits.device,
                )
                denominator.scatter_add_(0, segment, exponent)
                probability = (
                    exponent / denominator[segment].clamp_min(1.0e-300)
                ).reshape(-1, self.heads)
                weighted = (
                    probability[:, :, None] * value[source]
                ).reshape(-1, self.head_width)
                output_flat = torch.zeros(
                    (segment_count, self.head_width), dtype=weighted.dtype,
                    device=weighted.device,
                )
                output_flat.scatter_add_(
                    0, segment[:, None].expand(-1, self.head_width), weighted
                )
                output = output_flat.reshape(
                    nodes.shape[0], self.heads, self.head_width
                )
                output = self.output(output.reshape(-1, self.hidden))
                return torch.relu(self.layer_norm(output + nodes))

        return Layer()


def build_counterfactual_model(
    *, kind: str = "gat", dropout: float = 0.1
):
    """Build GAT or a fair independently-trained control."""

    if kind not in {"gat", "mlp", "linear", "no_message", "shuffled_topology"}:
        raise ValueError(f"unsupported V8 model kind {kind!r}")
    torch = _torch()
    nn = torch.nn

    class Model(nn.Module):
        model_kind = kind

        def __init__(self) -> None:
            super().__init__()
            self.node_encoder = nn.Linear(len(NODE_FEATURE_NAMES), 16)
            self.edge_encoder = nn.Linear(len(EDGE_FEATURE_NAMES), 16)
            self.context_encoder = nn.Linear(len(CONTEXT_FEATURE_NAMES), 16)
            self.layers = nn.ModuleList(
                [EdgeAttentionLayer.build(), EdgeAttentionLayer.build()]
            )
            self.attention_pool = nn.Linear(16, 1)
            self.dropout = float(dropout)
            view_width = 96
            combined_width = 5 * view_width + len(COUNTER_DELTA_NAMES)
            if kind == "linear":
                self.head = nn.Linear(combined_width, 3)
            else:
                self.head = nn.Sequential(
                    nn.Linear(combined_width, 32), nn.ReLU(), nn.Linear(32, 3)
                )

        def encode(self, graph):
            import torch.nn.functional as functional

            nodes = torch.relu(self.node_encoder(graph["node_features"]))
            edges = torch.relu(self.edge_encoder(graph["edge_features"]))
            if kind not in {"no_message", "mlp", "linear"}:
                for layer in self.layers:
                    nodes = layer(nodes, edges, graph["edge_index"])
                    nodes = functional.dropout(
                        nodes, p=self.dropout, training=self.training
                    )
            attention = torch.softmax(self.attention_pool(nodes).squeeze(-1), dim=0)
            context = torch.relu(
                self.context_encoder(graph["context_features"])
            )
            return torch.cat(
                (
                    nodes.mean(0),
                    nodes.max(0).values,
                    (attention[:, None] * nodes).sum(0),
                    edges.mean(0),
                    edges.max(0).values,
                    context,
                )
            )

        def forward(self, *, base, q0, qd1, counter_deltas):
            import torch.nn.functional as functional

            embeddings = [self.encode(graph) for graph in (base, q0, qd1)]
            combined = torch.cat(
                (
                    *embeddings,
                    embeddings[2] - embeddings[1],
                    torch.abs(embeddings[2] - embeddings[1]),
                    counter_deltas,
                )
            )
            if kind == "linear":
                logits = self.head(combined)
            else:
                hidden = self.head[1](self.head[0](combined))
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


def shuffled_triplet_tensors(triplet_tensors: Mapping[str, Any], *, state_hash: str):
    output = dict(triplet_tensors)
    for view in ("base", "q0", "qd1"):
        graph = dict(output[view])
        edge_index = graph["edge_index"].clone()
        node_count = int(graph["node_features"].shape[0])
        offset = 1 + int(
            hashlib.sha256(f"{state_hash}:{view}".encode()).hexdigest()[:8], 16
        ) % max(1, node_count - 1)
        edge_index[1] = (edge_index[1] + offset) % node_count
        graph["edge_index"] = edge_index
        output[view] = graph
    return output


def triplet_tensors(
    triplet: CounterfactualTriplet,
    normalization: Mapping[str, Mapping[str, Sequence[float]]],
):
    torch = _torch()
    counter = torch.tensor(triplet.counter_deltas, dtype=torch.float64)
    mean = torch.tensor(normalization["counter"]["mean"], dtype=torch.float64)
    scale = torch.tensor(normalization["counter"]["scale"], dtype=torch.float64)
    return {
        "base": triplet.base.tensors(normalization),
        "q0": triplet.q0.tensors(normalization),
        "qd1": triplet.qd1.tensors(normalization),
        "counter_deltas": (counter - mean) / scale,
    }


def portable_triplet_payload(triplet: CounterfactualTriplet) -> dict[str, Any]:
    def graph_payload(graph: CounterfactualGraph) -> dict[str, Any]:
        return {
            "node_features": [list(row) for row in graph.node_features],
            "edge_index": [list(side) for side in graph.edge_index],
            "edge_features": [list(row) for row in graph.edge_features],
            "context_features": list(graph.context_features),
        }

    return {
        "base": graph_payload(triplet.base),
        "q0": graph_payload(triplet.q0),
        "qd1": graph_payload(triplet.qd1),
        "counter_deltas": list(triplet.counter_deltas),
    }


def _tensor_payload(tensor) -> dict[str, Any]:
    values = tensor.detach().cpu().double().contiguous()
    return {
        "shape": [int(value) for value in values.shape],
        "values": values.reshape(-1).tolist(),
    }


def portable_seed_payload(model, *, seed: int) -> dict[str, Any]:
    if getattr(model, "model_kind", "") != "gat":
        raise ValueError("only the full V8 GAT may be exported")
    return {
        "seed": int(seed),
        "tensors": {
            name: _tensor_payload(value)
            for name, value in sorted(model.state_dict().items())
        },
    }


def export_portable_bundle(
    *,
    models: Iterable[tuple[int, Any]],
    normalization: Mapping[str, Mapping[str, Sequence[float]]],
    calibration_by_scale: Mapping[str, Mapping[str, Any]],
    thresholds_by_scale: Mapping[str, Mapping[str, float]],
    rollout_budget: int,
    bindings: Mapping[str, Any],
    output_path: str | Path,
) -> dict[str, Any]:
    rows = [portable_seed_payload(model, seed=seed) for seed, model in models]
    if tuple(row["seed"] for row in rows) != MODEL_SEEDS:
        raise ValueError("V8 portable bundle requires the frozen three seeds")
    if rollout_budget not in ROLLOUT_CHECKPOINTS:
        raise ValueError("portable bundle rollout budget is not frozen")
    payload: dict[str, Any] = {
        "schema_version": PORTABLE_BUNDLE_SCHEMA_V1,
        "runtime_policy": RUNTIME_POLICY_V8,
        "feature_schema_version": FEATURE_SCHEMA_V1,
        "label_graph_schema_version": LABEL_GRAPH_SCHEMA_V1,
        "prefix_probe_schema_version": PREFIX_PROBE_SCHEMA_V1,
        "feature_names": {
            "node": list(NODE_FEATURE_NAMES),
            "edge": list(EDGE_FEATURE_NAMES),
            "context": list(CONTEXT_FEATURE_NAMES),
            "counter": list(COUNTER_DELTA_NAMES),
        },
        "normalization": {
            group: {name: [float(value) for value in values] for name, values in row.items()}
            for group, row in normalization.items()
        },
        "calibration_by_scale": {
            str(scale): dict(row) for scale, row in calibration_by_scale.items()
        },
        "thresholds_by_scale": {
            str(scale): {name: float(value) for name, value in row.items()}
            for scale, row in thresholds_by_scale.items()
        },
        "processed_label_boundary": PREFIX_BOUNDARY,
        "rollout_budget": int(rollout_budget),
        "layer_norm_epsilon": 1.0e-5,
        "models": rows,
        "bindings": dict(bindings),
        "model_kind": "counterfactual_interaction_gat",
        "message_passing_required": True,
    }
    payload["bundle_sha256"] = hashlib.sha256(_canonical_bytes(payload)).hexdigest()
    path = Path(output_path)
    path.write_bytes(_canonical_bytes(payload) + b"\n")
    return payload
