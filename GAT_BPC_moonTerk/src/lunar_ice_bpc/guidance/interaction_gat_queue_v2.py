"""Pre-action interaction graph and models for the P0V5 GAT-only selector.

The graph is deliberately built from the current RMP support, immutable
instance data, true duals, and active branch/cut context.  It has no access to
queue-arm outcomes or post-action pricing telemetry.  The public runtime that
uses this module imports it only after the small-scale and root-only bypasses.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from itertools import combinations
from math import isfinite, log1p, sqrt
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import torch
from torch import nn
from torch.nn import functional as F

from lunar_ice_bpc.guidance.context_queue_portfolio_v1 import (
    PORTFOLIO_ACTION_UNIVERSE,
    PORTFOLIO_ARMS,
    PORTFOLIO_CONTEXT_FEATURES,
    build_portfolio_features,
)
from lunar_ice_bpc.guidance.models import EdgeAttentionLayer
from lunar_ice_bpc.guidance.tensorization import NODE_STATIC_FEATURES


INTERACTION_FEATURE_SCHEMA_V2 = (
    "lunar_ice_bpc.p0v5_interaction_gat_queue_features.v2"
)
INTERACTION_GRAPH_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_root_interaction_graph.v1"
)
INTERACTION_NORMALIZATION_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_interaction_gat_normalization.v1"
)
INTERACTION_ENVELOPE_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_interaction_gat_envelope.v1"
)
INTERACTION_CHECKPOINT_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_interaction_gat_checkpoint.v1"
)
INTERACTION_INPUT_PARITY_CONTRACT_V1 = (
    "same_node_edge_context_values_endpoint_message_passing_only.v1"
)
INTERACTION_TOP_K_COOCCURRENCE = 4
INTERACTION_TOP_K_TRAVEL = 4

INTERACTION_NODE_EXTRA_FEATURES = (
    "active_column_incidence_frequency",
    "active_route_mean_cardinality_fraction",
    "active_route_max_cardinality_fraction",
    "branch_incidence_count",
    "branch_together_fraction",
    "branch_separate_fraction",
    "cut_incidence_count",
    "cut_dual_abs_incidence",
)
INTERACTION_NODE_FEATURES = (
    *NODE_STATIC_FEATURES,
    "cover_dual",
    "cover_dual_z_within_request",
    "cover_dual_over_maxabs_within_request",
    "cover_dual_rank_within_request",
    "cover_dual_positive",
    *INTERACTION_NODE_EXTRA_FEATURES,
)
INTERACTION_EDGE_FEATURES = (
    "log1p_active_route_cooccurrence_count",
    "cooccurrence_given_source",
    "cooccurrence_given_target",
    "minimum_travel_time_over_horizon",
    "mean_travel_time_over_horizon",
    "minimum_energy_over_limit",
    "mean_energy_over_limit",
    "minimum_risk_over_request_max",
    "mean_risk_over_request_max",
    "time_window_compatibility_slack",
    "branch_together",
    "branch_separate",
    "log1p_cut_comembership_count",
    "cut_dual_abs_comembership",
)
INTERACTION_CONTEXT_FEATURES = PORTFOLIO_CONTEXT_FEATURES
INTERACTION_NODE_DIM = len(INTERACTION_NODE_FEATURES)
INTERACTION_EDGE_DIM = len(INTERACTION_EDGE_FEATURES)
INTERACTION_CONTEXT_DIM = len(INTERACTION_CONTEXT_FEATURES)


@dataclass(frozen=True)
class InteractionGraphFeatures:
    instance_content_hash: str
    task_ids: tuple[str, ...]
    node_features: tuple[tuple[float, ...], ...]
    edge_index: tuple[tuple[int, ...], tuple[int, ...]]
    edge_features: tuple[tuple[float, ...], ...]
    context_features: tuple[float, ...]
    graph_schema_version: str = INTERACTION_GRAPH_SCHEMA_V1
    schema_version: str = INTERACTION_FEATURE_SCHEMA_V2

    def to_tensors(self) -> dict[str, torch.Tensor]:
        return {
            "node_features": torch.tensor(
                self.node_features, dtype=torch.float32
            ),
            "edge_index": torch.tensor(self.edge_index, dtype=torch.long),
            "edge_features": torch.tensor(
                self.edge_features, dtype=torch.float32
            ),
            "context_features": torch.tensor(
                self.context_features, dtype=torch.float32
            ),
        }

    def audit_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "graph_schema_version": self.graph_schema_version,
            "instance_content_hash": self.instance_content_hash,
            "task_ids": list(self.task_ids),
            "node_features": [list(row) for row in self.node_features],
            "edge_index": [list(row) for row in self.edge_index],
            "edge_features": [list(row) for row in self.edge_features],
            "context_features": list(self.context_features),
        }


def build_interaction_graph(request) -> InteractionGraphFeatures:
    """Build the frozen sparse task-interaction graph from pre-action facts."""

    if str(request.pricing_lifecycle_scope) != "root_cg":
        raise ValueError("interaction graph is root-CG only")
    active_sets_raw = request.proof_tail_active_task_sets
    if active_sets_raw is None:
        raise ValueError("interaction graph requires active task sets")
    task_ids = tuple(request.data.task_ids)
    legal = set(task_ids)
    active_sets = tuple(
        tuple(sorted({str(task_id) for task_id in task_set}))
        for task_set in active_sets_raw
    )
    if any(not row or not set(row).issubset(legal) for row in active_sets):
        raise ValueError("interaction graph active task-set universe mismatch")

    # Reuse the already-audited V1 scalar features, but discard its complete
    # directed topology.  Node row zero is the depot; this graph is task-only.
    base = build_portfolio_features(request)
    if tuple(base.task_ids) != task_ids:
        raise ValueError("interaction graph canonical task order drift")
    base_task_rows = tuple(base.node_features[1:])
    if len(base_task_rows) != len(task_ids):
        raise ValueError("interaction graph base node count mismatch")

    incidence = {task_id: 0 for task_id in task_ids}
    cardinality_sum = {task_id: 0 for task_id in task_ids}
    cardinality_max = {task_id: 0 for task_id in task_ids}
    cooccurrence: dict[tuple[str, str], int] = {}
    for task_set in active_sets:
        size = len(task_set)
        for task_id in task_set:
            incidence[task_id] += 1
            cardinality_sum[task_id] += size
            cardinality_max[task_id] = max(cardinality_max[task_id], size)
        for left, right in combinations(task_set, 2):
            key = (left, right)
            cooccurrence[key] = cooccurrence.get(key, 0) + 1

    branch = _branch_facts(request, task_ids)
    cuts = _cut_facts(request, task_ids)
    active_count = max(1, len(active_sets))
    task_count = max(1, len(task_ids))
    node_rows = []
    for task_id, base_row in zip(task_ids, base_task_rows, strict=True):
        count = incidence[task_id]
        branch_count = branch["incidence"][task_id]
        node_rows.append((*base_row,
            count / active_count,
            (cardinality_sum[task_id] / max(1, count)) / task_count,
            cardinality_max[task_id] / task_count,
            float(branch_count),
            branch["together_incidence"][task_id] / max(1, branch_count),
            branch["separate_incidence"][task_id] / max(1, branch_count),
            float(cuts["incidence"][task_id]),
            float(cuts["dual_abs_incidence"][task_id]),
        ))

    directed_pairs: set[tuple[str, str]] = set()
    for source in task_ids:
        others = [target for target in task_ids if target != source]
        cooc_neighbors = sorted(
            others,
            key=lambda target: (
                -_cooccurrence(cooccurrence, source, target), target
            ),
        )[:INTERACTION_TOP_K_COOCCURRENCE]
        travel_neighbors = sorted(
            others,
            key=lambda target: (
                _path_summary(request.data, source, target)[0], target
            ),
        )[:INTERACTION_TOP_K_TRAVEL]
        for target in (*cooc_neighbors, *travel_neighbors):
            directed_pairs.add((source, target))
        directed_pairs.add((source, source))
    for left, right in branch["forced_pairs"] | cuts["forced_pairs"]:
        directed_pairs.add((left, right))
        directed_pairs.add((right, left))
    # Every selected relation is represented bidirectionally, including one
    # direction that was selected only by the source task's local top-k.
    directed_pairs |= {(right, left) for left, right in tuple(directed_pairs)}

    node_index = {task_id: index for index, task_id in enumerate(task_ids)}
    ordered_pairs = sorted(
        directed_pairs,
        key=lambda pair: (node_index[pair[0]], node_index[pair[1]]),
    )
    risk_scale = max(
        1.0e-12,
        *(
            abs(float(option.risk_integral))
            for by_type in request.data.arcs.values()
            for option in by_type.values()
        ),
    )
    edge_rows = tuple(
        _edge_row(
            request, source, target, incidence, cooccurrence,
            branch, cuts, risk_scale,
        )
        for source, target in ordered_pairs
    )
    features = InteractionGraphFeatures(
        instance_content_hash=str(request.data.instance_content_hash),
        task_ids=task_ids,
        node_features=tuple(tuple(float(v) for v in row) for row in node_rows),
        edge_index=(
            tuple(node_index[source] for source, _target in ordered_pairs),
            tuple(node_index[target] for _source, target in ordered_pairs),
        ),
        edge_features=edge_rows,
        context_features=tuple(float(v) for v in base.context_features),
    )
    _validate_features(features)
    return features


def _branch_facts(request, task_ids):
    incidence = {task_id: 0 for task_id in task_ids}
    together = {task_id: 0 for task_id in task_ids}
    separate = {task_id: 0 for task_id in task_ids}
    pair_flags: dict[tuple[str, str], tuple[float, float]] = {}
    forced = set()
    for decision in request.branch_context.pair_decisions:
        left, right = sorted((str(decision.task_a), str(decision.task_b)))
        if left not in incidence or right not in incidence:
            raise ValueError("interaction graph branch task universe mismatch")
        same = 1.0 if str(decision.sense) == "same_journey" else 0.0
        different = 1.0 - same
        pair_flags[(left, right)] = (same, different)
        forced.add((left, right))
        for task_id in (left, right):
            incidence[task_id] += 1
            together[task_id] += int(same)
            separate[task_id] += int(different)
    return {
        "incidence": incidence,
        "together_incidence": together,
        "separate_incidence": separate,
        "pair_flags": pair_flags,
        "forced_pairs": forced,
    }


def _cut_facts(request, task_ids):
    incidence = {task_id: 0 for task_id in task_ids}
    dual_abs = {task_id: 0.0 for task_id in task_ids}
    pair_count: dict[tuple[str, str], int] = {}
    pair_dual: dict[tuple[str, str], float] = {}
    forced = set()
    cut_duals = dict(request.true_duals.cuts or {})
    for cut in request.cut_context.cuts:
        members = tuple(task_id for task_id in cut.tasks if task_id in incidence)
        if len(members) != len(cut.tasks):
            raise ValueError("interaction graph cut task universe mismatch")
        magnitude = abs(float(cut_duals.get(cut.cut_id, 0.0)))
        for task_id in members:
            incidence[task_id] += 1
            dual_abs[task_id] += magnitude
        for left, right in combinations(sorted(members), 2):
            key = (left, right)
            pair_count[key] = pair_count.get(key, 0) + 1
            pair_dual[key] = pair_dual.get(key, 0.0) + magnitude
            forced.add(key)
    return {
        "incidence": incidence,
        "dual_abs_incidence": dual_abs,
        "pair_count": pair_count,
        "pair_dual": pair_dual,
        "forced_pairs": forced,
    }


def _cooccurrence(counts, left, right) -> int:
    if left == right:
        return 0
    return int(counts.get(tuple(sorted((left, right))), 0))


def _path_summary(data, source: str, target: str):
    if source == target:
        return (0.0,) * 6
    options = tuple(data.arcs[(source, target)].values())
    if len(options) != 3:
        raise ValueError("interaction graph requires three fixed path options")
    times = tuple(float(row.travel_time_min) for row in options)
    energies = tuple(float(row.energy_proxy) for row in options)
    risks = tuple(float(row.risk_integral) for row in options)
    return (
        min(times), sum(times) / 3.0,
        min(energies), sum(energies) / 3.0,
        min(risks), sum(risks) / 3.0,
    )


def _edge_row(
    request, source, target, incidence, cooccurrence, branch, cuts, risk_scale,
):
    count = _cooccurrence(cooccurrence, source, target)
    pair = tuple(sorted((source, target)))
    same, different = branch["pair_flags"].get(pair, (0.0, 0.0))
    cut_count = cuts["pair_count"].get(pair, 0) if source != target else 0
    cut_dual = cuts["pair_dual"].get(pair, 0.0) if source != target else 0.0
    if source == target:
        summary = (0.0,) * 6
        compatibility = 1.0
    else:
        summary = _path_summary(request.data, source, target)
        source_task = request.data.tasks[source]
        target_task = request.data.tasks[target]
        earliest_completion = (
            float(source_task.ready_time)
            + float(source_task.service_time)
            + summary[0]
            + float(target_task.service_time)
        )
        compatibility = max(-1.0, min(
            1.0,
            (float(target_task.due_time) - earliest_completion)
            / max(1.0, float(request.data.horizon)),
        ))
    min_time, mean_time, min_energy, mean_energy, min_risk, mean_risk = summary
    return tuple(float(v) for v in (
        log1p(count),
        count / max(1, incidence[source]),
        count / max(1, incidence[target]),
        min_time / max(1.0, float(request.data.horizon)),
        mean_time / max(1.0, float(request.data.horizon)),
        min_energy / max(1.0, float(request.data.energy_limit)),
        mean_energy / max(1.0, float(request.data.energy_limit)),
        min_risk / risk_scale,
        mean_risk / risk_scale,
        compatibility,
        same,
        different,
        log1p(cut_count),
        cut_dual,
    ))


def _validate_features(features: InteractionGraphFeatures) -> None:
    if features.schema_version != INTERACTION_FEATURE_SCHEMA_V2:
        raise ValueError("interaction feature schema mismatch")
    if features.graph_schema_version != INTERACTION_GRAPH_SCHEMA_V1:
        raise ValueError("interaction graph schema mismatch")
    if not features.task_ids or len(features.node_features) != len(features.task_ids):
        raise ValueError("interaction graph node count mismatch")
    if any(len(row) != INTERACTION_NODE_DIM for row in features.node_features):
        raise ValueError("interaction graph node dimension mismatch")
    if len(features.edge_index) != 2:
        raise ValueError("interaction graph edge index invalid")
    if len(features.edge_index[0]) != len(features.edge_features) or (
        len(features.edge_index[1]) != len(features.edge_features)
    ):
        raise ValueError("interaction graph edge count mismatch")
    if any(len(row) != INTERACTION_EDGE_DIM for row in features.edge_features):
        raise ValueError("interaction graph edge dimension mismatch")
    if len(features.context_features) != INTERACTION_CONTEXT_DIM:
        raise ValueError("interaction graph context dimension mismatch")
    flat = (
        *(value for row in features.node_features for value in row),
        *(value for row in features.edge_features for value in row),
        *features.context_features,
    )
    if any(not isfinite(float(value)) for value in flat):
        raise ValueError("interaction graph contains NaN/Inf")
    edge_pairs = set(zip(*features.edge_index, strict=True))
    node_count = len(features.task_ids)
    if any((index, index) not in edge_pairs for index in range(node_count)):
        raise ValueError("interaction graph self-loop missing")
    if any((target, source) not in edge_pairs for source, target in edge_pairs):
        raise ValueError("interaction graph is not bidirectional")


def interaction_graph_builder_hash() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _statistics(rows: Iterable[Sequence[float]], dimension: int):
    values = [tuple(float(value) for value in row) for row in rows]
    if not values or any(len(row) != dimension for row in values):
        raise ValueError("interaction normalization dimension mismatch")
    means = [sum(row[i] for row in values) / len(values) for i in range(dimension)]
    stds = []
    for index, mean in enumerate(means):
        variance = sum((row[index] - mean) ** 2 for row in values) / len(values)
        stds.append(max(1.0e-6, sqrt(variance)))
    return {"mean": means, "std": stds}


def fit_interaction_normalization(rows: Sequence[InteractionGraphFeatures]):
    if not rows or any(row.schema_version != INTERACTION_FEATURE_SCHEMA_V2 for row in rows):
        raise ValueError("interaction normalization requires V2 training rows")
    payload = {
        "schema_version": INTERACTION_NORMALIZATION_SCHEMA_V1,
        "fit_partition": "train_instances_only",
        "node": _statistics(
            (value for row in rows for value in row.node_features),
            INTERACTION_NODE_DIM,
        ),
        "edge": _statistics(
            (value for row in rows for value in row.edge_features),
            INTERACTION_EDGE_DIM,
        ),
        "context": _statistics(
            (row.context_features for row in rows), INTERACTION_CONTEXT_DIM
        ),
    }
    validate_interaction_normalization(payload)
    return payload


def validate_interaction_normalization(payload: Mapping[str, object]) -> None:
    if payload.get("schema_version") != INTERACTION_NORMALIZATION_SCHEMA_V1:
        raise ValueError("interaction normalization schema mismatch")
    if payload.get("fit_partition") != "train_instances_only":
        raise ValueError("interaction normalization is not train-only")
    for group, dimension in (
        ("node", INTERACTION_NODE_DIM),
        ("edge", INTERACTION_EDGE_DIM),
        ("context", INTERACTION_CONTEXT_DIM),
    ):
        values = dict(payload.get(group) or {})
        mean = tuple(float(v) for v in values.get("mean") or ())
        std = tuple(float(v) for v in values.get("std") or ())
        if (
            len(mean) != dimension or len(std) != dimension
            or any(not isfinite(v) for v in (*mean, *std))
            or any(v <= 0.0 for v in std)
        ):
            raise ValueError(f"interaction {group} normalization invalid")


def fit_interaction_envelope(
    rows: Sequence[InteractionGraphFeatures], *, relative_margin: float = 0.05
):
    if not rows or any(row.schema_version != INTERACTION_FEATURE_SCHEMA_V2 for row in rows):
        raise ValueError("interaction envelope requires V2 training rows")
    if float(relative_margin) != 0.05:
        raise ValueError("interaction OOD margin is frozen at five percent")
    groups = {
        "node": [value for row in rows for value in row.node_features],
        "edge": [value for row in rows for value in row.edge_features],
        "context": [row.context_features for row in rows],
    }
    payload: dict[str, object] = {
        "schema_version": INTERACTION_ENVELOPE_SCHEMA_V1,
        "fit_partition": "train_instances_only",
        "relative_margin": 0.05,
    }
    for group, values in groups.items():
        dimension = len(values[0])
        payload[f"{group}_min"] = [min(row[i] for row in values) for i in range(dimension)]
        payload[f"{group}_max"] = [max(row[i] for row in values) for i in range(dimension)]
    return payload


def interaction_is_ood(features, envelope) -> tuple[bool, str]:
    if features.schema_version != INTERACTION_FEATURE_SCHEMA_V2:
        return True, "interaction_feature_schema_mismatch"
    if envelope.get("schema_version") != INTERACTION_ENVELOPE_SCHEMA_V1:
        return True, "interaction_envelope_schema_mismatch"
    if envelope.get("fit_partition") != "train_instances_only":
        return True, "interaction_envelope_partition_mismatch"
    if float(envelope.get("relative_margin") or 0.0) != 0.05:
        return True, "interaction_envelope_margin_mismatch"
    for group, values in (
        ("node", features.node_features),
        ("edge", features.edge_features),
        ("context", (features.context_features,)),
    ):
        lower = tuple(float(v) for v in envelope.get(f"{group}_min") or ())
        upper = tuple(float(v) for v in envelope.get(f"{group}_max") or ())
        if not values or len(lower) != len(values[0]) or len(upper) != len(values[0]):
            return True, f"interaction_{group}_envelope_dimension_mismatch"
        for row in values:
            for value, low, high in zip(row, lower, upper, strict=True):
                width = max(1.0e-9, high - low)
                if (
                    not all(isfinite(float(v)) for v in (value, low, high))
                    or low > high or value < low - 0.05 * width
                    or value > high + 0.05 * width
                ):
                    return True, f"interaction_{group}_feature_outside_envelope"
    return False, ""


class _InteractionNormalizer(nn.Module):
    def __init__(self, normalization):
        super().__init__()
        validate_interaction_normalization(normalization)
        for group in ("node", "edge", "context"):
            values = dict(normalization[group])
            self.register_buffer(f"{group}_mean", torch.tensor(values["mean"], dtype=torch.float32))
            self.register_buffer(f"{group}_std", torch.tensor(values["std"], dtype=torch.float32))

    def forward(self, node, edge, context):
        return (
            (node - self.node_mean) / self.node_std,
            (edge - self.edge_mean) / self.edge_std,
            (context - self.context_mean) / self.context_std,
        )


class _InteractionArmHeads(nn.Module):
    def __init__(self, hidden_dim):
        super().__init__()
        self.head = nn.Linear(hidden_dim * 6, len(PORTFOLIO_ARMS) * 3)

    def forward(self, node, edge, context, attention_pool):
        values = self.head(torch.cat((
            node.mean(0), node.max(0).values, attention_pool,
            edge.mean(0), edge.max(0).values, context,
        ), dim=-1)).reshape(1, len(PORTFOLIO_ARMS), 3)
        return {
            "benefit_probability": torch.sigmoid(values[..., 0]),
            "conditional_positive_gain": F.softplus(values[..., 1]),
            "adverse_probability": torch.sigmoid(values[..., 2]),
        }


class InteractionGATSelector(nn.Module):
    model_kind = "gat"
    message_passing_required = True

    def __init__(self, normalization, *, hidden_dim=32, heads=2):
        super().__init__()
        self.normalizer = _InteractionNormalizer(normalization)
        self.node_encoder = nn.Sequential(nn.Linear(INTERACTION_NODE_DIM, hidden_dim), nn.ReLU())
        self.edge_encoder = nn.Sequential(nn.Linear(INTERACTION_EDGE_DIM, hidden_dim), nn.ReLU())
        self.context_encoder = nn.Sequential(
            nn.Linear(INTERACTION_CONTEXT_DIM, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
        )
        self.attention_layers = nn.ModuleList(
            EdgeAttentionLayer(hidden_dim, hidden_dim, heads) for _ in range(2)
        )
        self.pool_gate = nn.Linear(hidden_dim, 1)
        self.arm_heads = _InteractionArmHeads(hidden_dim)

    def forward(
        self, *, node_features, edge_index, edge_features, context_features,
        message_edge_index=None, disable_message_passing=False,
    ):
        node, edge, context = self.normalizer(node_features, edge_features, context_features)
        node = self.node_encoder(node)
        edge = self.edge_encoder(edge)
        topology = edge_index if message_edge_index is None else message_edge_index
        if not disable_message_passing:
            for layer in self.attention_layers:
                node = F.relu(layer(node, topology, edge))
        weights = torch.softmax(self.pool_gate(node).squeeze(-1), dim=0)
        attention_pool = (weights[:, None] * node).sum(0)
        return self.arm_heads(node, edge, self.context_encoder(context), attention_pool)


class InteractionMLPControl(nn.Module):
    model_kind = "mlp"
    message_passing_required = False

    def __init__(self, normalization, *, hidden_dim=32):
        super().__init__()
        self.normalizer = _InteractionNormalizer(normalization)
        self.node_encoder = nn.Sequential(
            nn.Linear(INTERACTION_NODE_DIM, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
        )
        self.edge_encoder = nn.Sequential(nn.Linear(INTERACTION_EDGE_DIM, hidden_dim), nn.ReLU())
        self.context_encoder = nn.Sequential(
            nn.Linear(INTERACTION_CONTEXT_DIM, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
        )
        self.pool_gate = nn.Linear(hidden_dim, 1)
        self.arm_heads = _InteractionArmHeads(hidden_dim)

    def forward(self, *, node_features, edge_index, edge_features, context_features):
        node, edge, context = self.normalizer(node_features, edge_features, context_features)
        node = self.node_encoder(node)
        edge = self.edge_encoder(edge)
        weights = torch.softmax(self.pool_gate(node).squeeze(-1), dim=0)
        return self.arm_heads(
            node, edge, self.context_encoder(context),
            (weights[:, None] * node).sum(0),
        )


class InteractionLinearControl(nn.Module):
    model_kind = "linear"
    message_passing_required = False

    def __init__(self, normalization):
        super().__init__()
        self.normalizer = _InteractionNormalizer(normalization)
        self.head = nn.Linear(
            INTERACTION_NODE_DIM * 2 + INTERACTION_EDGE_DIM * 2 + INTERACTION_CONTEXT_DIM,
            len(PORTFOLIO_ARMS) * 3,
        )

    def forward(self, *, node_features, edge_index, edge_features, context_features):
        node, edge, context = self.normalizer(node_features, edge_features, context_features)
        values = self.head(torch.cat((
            node.mean(0), node.max(0).values,
            edge.mean(0), edge.max(0).values, context,
        ), dim=-1)).reshape(1, len(PORTFOLIO_ARMS), 3)
        return {
            "benefit_probability": torch.sigmoid(values[..., 0]),
            "conditional_positive_gain": F.softplus(values[..., 1]),
            "adverse_probability": torch.sigmoid(values[..., 2]),
        }


def interaction_parameter_count(model) -> int:
    return sum(parameter.numel() for parameter in model.parameters())


def interaction_training_loss(*args, **kwargs):
    # The loss contract is intentionally identical to V1; only the topology
    # and candidate-selection authority changed.
    from lunar_ice_bpc.guidance.context_queue_portfolio_v1 import portfolio_training_loss
    return portfolio_training_loss(*args, **kwargs)

