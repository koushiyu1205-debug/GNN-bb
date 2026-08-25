"""GAT-first V3 rankers for exact-safe P0V5 proof-tail ordering.

The models in this module emit ordering potentials only.  They deliberately do
not emit or own runtime activation decisions: those decisions must be trained
from the selected arm's own fresh-process outcomes.  Native still compares the
potentials only after terminal class and reduced-cost bucket, so these models
cannot filter labels, alter dominance, provide a bound, or issue a certificate.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite, sqrt
from typing import Iterable, Mapping, Sequence

import torch
from torch import nn
from torch.nn import functional as F

from lunar_ice_bpc.guidance.models import EdgeAttentionLayer
from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
    QG2Features,
    QG2_CONTEXT_FEATURES,
    QG2_FEATURE_SCHEMA_V1,
    QG2_LABEL_STATE_FEATURE_COUNT,
    QG2_NODE_DYNAMIC_FEATURES,
)
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.objective import objective_references
from lunar_ice_bpc.guidance.tensorization import (
    EDGE_STATIC_FEATURES,
    NODE_STATIC_FEATURES,
)


QG2_V3_INPUT_FEATURE_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_features.objective_normalized_risk.v3_1"
)
QG2_V3_FEATURE_ENVELOPE_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_feature_envelope.per_feature.v3_1"
)
QG2_V3_NORMALIZATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_train_normalization.v2"
QG2_V3_CHECKPOINT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_ranker_checkpoint.v3_1"
QG2_V3_RANKER_SCHEMA = "lunar_ice_bpc.p0v5_qg2_admission_ranker.v3_1"
QG2_V3_MODEL_ORDER = ("gat", "mlp", "linear")
QG2_V3_MODEL_IDS = {
    "gat": "proof_queue_admission_gat_residual_2x32x2_v3",
    "mlp": "proof_queue_admission_mlp_2x32_v3",
    "linear": "proof_queue_admission_linear_meanmax_v4",
}

_NODE_FEATURE_NAMES = (*NODE_STATIC_FEATURES, *QG2_NODE_DYNAMIC_FEATURES)
_EDGE_FEATURE_NAMES = tuple(
    "risk_over_objective_reference" if name == "risk" else name
    for name in EDGE_STATIC_FEATURES
)
_CONTEXT_FEATURE_NAMES = tuple(QG2_CONTEXT_FEATURES)


def normalize_qg2_v3_features(
    data: LunarIceData,
    features: QG2Features,
) -> QG2Features:
    """Make edge risk comparable across instance generators and scales.

    The legacy static graph exposes raw ``risk_integral`` while every other
    resource-like edge feature is normalized.  V3.1 divides that value by the
    immutable objective reference used by Exact itself.  This uses instance
    data only, preserves all within-instance risk ordering, and cannot leak a
    pricing outcome or selector action.
    """

    if features.schema_version == QG2_V3_INPUT_FEATURE_SCHEMA:
        return features
    if features.schema_version != QG2_FEATURE_SCHEMA_V1:
        raise ValueError("QG2 V3.1 input feature schema mismatch")
    if features.instance_content_hash != data.instance_content_hash:
        raise ValueError("QG2 V3.1 instance binding mismatch")
    risk_index = tuple(EDGE_STATIC_FEATURES).index("risk")
    denominator = float(objective_references(data).reference_risk)
    if not isfinite(denominator) or denominator <= 0.0:
        raise ValueError("QG2 V3.1 objective risk reference is invalid")
    edge_rows: list[tuple[float, ...]] = []
    for row in features.edge_features:
        if len(row) != len(EDGE_STATIC_FEATURES):
            raise ValueError("QG2 V3.1 edge feature dimension mismatch")
        values = [float(value) for value in row]
        raw_risk = values[risk_index]
        if not isfinite(raw_risk) or raw_risk < 0.0:
            raise ValueError("QG2 V3.1 raw edge risk is invalid")
        values[risk_index] = raw_risk / denominator
        edge_rows.append(tuple(values))
    return replace(
        features,
        edge_features=tuple(edge_rows),
        schema_version=QG2_V3_INPUT_FEATURE_SCHEMA,
    )


def qg2_v3_is_ood(
    features: QG2Features,
    envelope: Mapping[str, object],
) -> tuple[bool, str]:
    """Apply a train-only, per-feature envelope to one pre-action graph.

    V3 previously compared every node/edge value with a single group maximum.
    That made the largest raw feature silently define OOD for unrelated
    dimensions.  V3.1 binds every dimension by name and fails closed on any
    schema or range drift.
    """

    if features.schema_version != QG2_V3_INPUT_FEATURE_SCHEMA:
        return True, "input_feature_schema_mismatch"
    if str(envelope.get("schema_version") or "") != (
        QG2_V3_FEATURE_ENVELOPE_SCHEMA
    ):
        return True, "feature_envelope_schema_mismatch"
    if str(envelope.get("fit_partition") or "") != "train_instances_only":
        return True, "feature_envelope_partition_mismatch"
    margin = max(0.0, float(envelope.get("relative_margin") or 0.0))
    groups = (
        ("context", (features.context_features,), _CONTEXT_FEATURE_NAMES),
        ("node", features.node_features, _NODE_FEATURE_NAMES),
        ("edge", features.edge_features, _EDGE_FEATURE_NAMES),
    )
    for group, rows, names in groups:
        if not rows or any(len(row) != len(names) for row in rows):
            return True, f"{group}_feature_dimension_mismatch"
        recorded_names = tuple(envelope.get(f"{group}_feature_names") or ())
        lower = tuple(float(value) for value in envelope.get(f"{group}_min") or ())
        upper = tuple(float(value) for value in envelope.get(f"{group}_max") or ())
        if recorded_names != tuple(names) or len(lower) != len(names) or len(upper) != len(names):
            return True, f"{group}_feature_envelope_dimension_mismatch"
        for row in rows:
            for name, value, lo, hi in zip(
                names, row, lower, upper, strict=True
            ):
                numeric = float(value)
                if any(not isfinite(item) for item in (numeric, lo, hi)) or lo > hi:
                    return True, f"{group}_feature_envelope_invalid"
                width = max(1.0e-9, hi - lo)
                if numeric < lo - margin * width or numeric > hi + margin * width:
                    return True, f"{group}_feature_outside_envelope:{name}"
    return False, ""


def _passthrough_feature(name: str) -> bool:
    return bool(
        name.startswith("is_")
        or name.startswith("mode_")
        or name.endswith("_present")
        or name.endswith("_positive")
        or name == "root_lifecycle_scope"
    )


def _group_statistics(
    rows: Iterable[Sequence[float]], names: Sequence[str]
) -> dict[str, object]:
    materialized = [tuple(float(value) for value in row) for row in rows]
    if not materialized or any(len(row) != len(names) for row in materialized):
        raise ValueError("QG2 V3 normalization group is empty or dimension-drifted")
    if any(not isfinite(value) for row in materialized for value in row):
        raise ValueError("QG2 V3 normalization input contains NaN/Inf")
    means: list[float] = []
    stds: list[float] = []
    passthrough: list[int] = []
    for index, name in enumerate(names):
        values = [row[index] for row in materialized]
        if _passthrough_feature(str(name)):
            means.append(0.0)
            stds.append(1.0)
            passthrough.append(index)
            continue
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        means.append(float(mean))
        stds.append(max(1.0e-6, sqrt(variance)))
    return {
        "feature_names": list(names),
        "mean": means,
        "std": stds,
        "passthrough_indices": passthrough,
    }


def fit_qg2_v3_normalization(
    feature_rows: Sequence[QG2Features],
) -> dict[str, object]:
    """Fit immutable statistics from training-instance features only."""

    if not feature_rows:
        raise ValueError("QG2 V3 normalization requires training features")
    if any(
        row.schema_version != QG2_V3_INPUT_FEATURE_SCHEMA
        for row in feature_rows
    ):
        raise ValueError("QG2 V3.1 normalization requires normalized edge risk")
    payload = {
        "schema_version": QG2_V3_NORMALIZATION_SCHEMA,
        "fit_partition": "train_instances_only",
        "node": _group_statistics(
            (row for features in feature_rows for row in features.node_features),
            _NODE_FEATURE_NAMES,
        ),
        "edge": _group_statistics(
            (row for features in feature_rows for row in features.edge_features),
            _EDGE_FEATURE_NAMES,
        ),
        "context": _group_statistics(
            (features.context_features for features in feature_rows),
            _CONTEXT_FEATURE_NAMES,
        ),
    }
    validate_qg2_v3_normalization(payload)
    return payload


def validate_qg2_v3_normalization(payload: Mapping[str, object]) -> None:
    if str(payload.get("schema_version") or "") != QG2_V3_NORMALIZATION_SCHEMA:
        raise ValueError("QG2 V3 normalization schema mismatch")
    if str(payload.get("fit_partition") or "") != "train_instances_only":
        raise ValueError("QG2 V3 normalization leaked outside train instances")
    for group, names in (
        ("node", _NODE_FEATURE_NAMES),
        ("edge", _EDGE_FEATURE_NAMES),
        ("context", _CONTEXT_FEATURE_NAMES),
    ):
        values = dict(payload.get(group) or {})
        if tuple(values.get("feature_names") or ()) != tuple(names):
            raise ValueError(f"QG2 V3 {group} feature-name drift")
        means = tuple(float(value) for value in values.get("mean") or ())
        stds = tuple(float(value) for value in values.get("std") or ())
        if (
            len(means) != len(names)
            or len(stds) != len(names)
            or any(not isfinite(value) for value in (*means, *stds))
            or any(value <= 0.0 for value in stds)
        ):
            raise ValueError(f"QG2 V3 {group} normalization is invalid")


class _TrainOnlyNormalizer(nn.Module):
    def __init__(self, payload: Mapping[str, object]) -> None:
        super().__init__()
        validate_qg2_v3_normalization(payload)
        for group in ("node", "edge", "context"):
            values = dict(payload[group])
            self.register_buffer(
                f"{group}_mean",
                torch.tensor(values["mean"], dtype=torch.float32),
            )
            self.register_buffer(
                f"{group}_std",
                torch.tensor(values["std"], dtype=torch.float32),
            )

    def forward(
        self,
        node: torch.Tensor,
        edge: torch.Tensor,
        context: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return (
            (node - self.node_mean) / self.node_std,
            (edge - self.edge_mean) / self.edge_std,
            (context - self.context_mean) / self.context_std,
        )


class _RankHeads(nn.Module):
    def __init__(self, hidden_dim: int, *, linear: bool = False) -> None:
        super().__init__()
        self.linear = bool(linear)
        self.node_head = nn.Linear(hidden_dim, 1)
        self.arc_head = (
            nn.Linear(hidden_dim * 4, 1)
            if linear
            else nn.Sequential(
                nn.Linear(hidden_dim * 4, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, 1),
            )
        )
        self.state_head = nn.Linear(
            hidden_dim * 3, QG2_LABEL_STATE_FEATURE_COUNT
        )

    def forward(
        self,
        node_embedding: torch.Tensor,
        edge_embedding: torch.Tensor,
        edge_index: torch.Tensor,
        context_embedding: torch.Tensor,
        *,
        use_max_pool: bool,
    ) -> dict[str, torch.Tensor]:
        edge_count = int(edge_index.shape[1])
        context_rows = context_embedding.expand(edge_count, -1)
        arc_input = torch.cat(
            (
                node_embedding[edge_index[0]],
                node_embedding[edge_index[1]],
                edge_embedding,
                context_rows,
            ),
            dim=-1,
        )
        mean_pool = node_embedding.mean(dim=0)
        max_pool = (
            node_embedding.max(dim=0).values if use_max_pool else mean_pool
        )
        global_input = torch.cat(
            (mean_pool, max_pool, context_embedding), dim=-1
        )
        state = self.state_head(global_input)
        if not self.linear:
            state = torch.tanh(state)
        return {
            "node_scores": self.node_head(node_embedding).squeeze(-1),
            "arc_scores": self.arc_head(arc_input).squeeze(-1),
            "label_state_coefficients": state,
        }


class _QG2V3Ranker(nn.Module):
    model_kind = ""

    def __init__(
        self,
        normalization: Mapping[str, object],
        *,
        hidden_dim: int = 32,
        heads: int = 2,
    ) -> None:
        super().__init__()
        self.hidden_dim = int(hidden_dim)
        self.head_count = int(heads)
        self.normalizer = _TrainOnlyNormalizer(normalization)

    def _normalize(self, node_features, edge_features, context_features):
        if (
            node_features.ndim != 2
            or edge_features.ndim != 2
            or context_features.ndim != 1
        ):
            raise ValueError("QG2 V3 feature tensor rank mismatch")
        return self.normalizer(node_features, edge_features, context_features)


class QG2V3TinyGAT(_QG2V3Ranker):
    model_kind = "gat"

    def __init__(
        self,
        normalization: Mapping[str, object],
        *,
        hidden_dim: int = 32,
        heads: int = 2,
    ) -> None:
        super().__init__(normalization, hidden_dim=hidden_dim, heads=heads)
        self.node_encoder = nn.Sequential(
            nn.Linear(len(_NODE_FEATURE_NAMES), hidden_dim), nn.ReLU()
        )
        self.edge_encoder = nn.Sequential(
            nn.Linear(len(_EDGE_FEATURE_NAMES), hidden_dim), nn.ReLU()
        )
        self.context_encoder = nn.Sequential(
            nn.Linear(len(_CONTEXT_FEATURE_NAMES), hidden_dim), nn.ReLU()
        )
        self.attention_layers = nn.ModuleList(
            EdgeAttentionLayer(hidden_dim, hidden_dim, heads) for _ in range(2)
        )
        self.heads_module = _RankHeads(hidden_dim)

    def forward(
        self,
        *,
        node_features,
        edge_index,
        edge_features,
        context_features,
        message_edge_index=None,
        disable_message_passing: bool = False,
    ):
        node, edge, context = self._normalize(
            node_features, edge_features, context_features
        )
        node_embedding = self.node_encoder(node)
        edge_embedding = self.edge_encoder(edge)
        message_index = (
            edge_index if message_edge_index is None else message_edge_index
        )
        if not disable_message_passing:
            for layer in self.attention_layers:
                node_embedding = layer(
                    node_embedding, message_index, edge_embedding
                )
        context_embedding = self.context_encoder(context)
        return self.heads_module(
            node_embedding,
            edge_embedding,
            edge_index,
            context_embedding,
            use_max_pool=True,
        )


class QG2V3MLP(_QG2V3Ranker):
    model_kind = "mlp"

    def __init__(
        self,
        normalization: Mapping[str, object],
        *,
        hidden_dim: int = 32,
        heads: int = 1,
    ) -> None:
        super().__init__(normalization, hidden_dim=hidden_dim, heads=heads)
        self.node_encoder = nn.Sequential(
            nn.Linear(len(_NODE_FEATURE_NAMES), hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        self.edge_encoder = nn.Sequential(
            nn.Linear(len(_EDGE_FEATURE_NAMES), hidden_dim), nn.ReLU()
        )
        self.context_encoder = nn.Sequential(
            nn.Linear(len(_CONTEXT_FEATURE_NAMES), hidden_dim), nn.ReLU()
        )
        self.heads_module = _RankHeads(hidden_dim)

    def forward(self, *, node_features, edge_index, edge_features, context_features):
        node, edge, context = self._normalize(
            node_features, edge_features, context_features
        )
        return self.heads_module(
            self.node_encoder(node),
            self.edge_encoder(edge),
            edge_index,
            self.context_encoder(context),
            use_max_pool=True,
        )


class QG2V3Linear(_QG2V3Ranker):
    """Linear no-message control with the same mean/max graph summaries."""

    model_kind = "linear"

    def __init__(
        self,
        normalization: Mapping[str, object],
        *,
        hidden_dim: int = 32,
        heads: int = 1,
    ) -> None:
        super().__init__(normalization, hidden_dim=hidden_dim, heads=heads)
        self.node_encoder = nn.Linear(len(_NODE_FEATURE_NAMES), hidden_dim)
        self.edge_encoder = nn.Linear(len(_EDGE_FEATURE_NAMES), hidden_dim)
        self.context_encoder = nn.Linear(len(_CONTEXT_FEATURE_NAMES), hidden_dim)
        self.heads_module = _RankHeads(hidden_dim, linear=True)

    def forward(self, *, node_features, edge_index, edge_features, context_features):
        node, edge, context = self._normalize(
            node_features, edge_features, context_features
        )
        return self.heads_module(
            self.node_encoder(node),
            self.edge_encoder(edge),
            edge_index,
            self.context_encoder(context),
            use_max_pool=True,
        )


def qg2_v3_weighted_rank_loss(
    preferred_scores: torch.Tensor,
    other_scores: torch.Tensor,
    weights: torch.Tensor,
) -> torch.Tensor:
    if preferred_scores.shape != other_scores.shape or weights.shape != preferred_scores.shape:
        raise ValueError("QG2 V3 rank-loss tensor shape mismatch")
    if preferred_scores.numel() == 0:
        raise ValueError("QG2 V3 rank loss requires pairs")
    if not bool(torch.isfinite(weights).all()) or bool((weights < 0.0).any()):
        raise ValueError("QG2 V3 pair weights are invalid")
    total = weights.sum()
    if float(total.detach()) <= 0.0:
        raise ValueError("QG2 V3 pair weights have zero mass")
    return (F.softplus(-(preferred_scores - other_scores)) * weights).sum() / total


def qg2_v3_checkpoint_payload(
    model: nn.Module,
    *,
    normalization: Mapping[str, object],
    metadata: Mapping[str, object],
) -> dict[str, object]:
    validate_qg2_v3_normalization(normalization)
    kind = str(getattr(model, "model_kind", ""))
    if kind not in QG2_V3_MODEL_IDS:
        raise ValueError("unsupported QG2 V3 model kind")
    return {
        "schema_version": QG2_V3_CHECKPOINT_SCHEMA,
        "ranker_schema_version": QG2_V3_RANKER_SCHEMA,
        "model_kind": kind,
        "model_id": QG2_V3_MODEL_IDS[kind],
        "hidden_dim": int(getattr(model, "hidden_dim", 32)),
        "heads": int(getattr(model, "head_count", 1)),
        "normalization": dict(normalization),
        "metadata": dict(metadata),
        "state_dict": model.state_dict(),
    }


def load_qg2_v3_checkpoint(path: str, *, map_location: str = "cpu"):
    payload = torch.load(path, map_location=map_location, weights_only=False)
    if not isinstance(payload, Mapping):
        raise ValueError("QG2 V3 checkpoint payload is invalid")
    payload = dict(payload)
    if str(payload.get("schema_version") or "") != QG2_V3_CHECKPOINT_SCHEMA:
        raise ValueError("QG2 V3 checkpoint schema mismatch")
    if str(payload.get("ranker_schema_version") or "") != QG2_V3_RANKER_SCHEMA:
        raise ValueError("QG2 V3 ranker schema mismatch")
    kind = str(payload.get("model_kind") or "")
    model_class = {
        "gat": QG2V3TinyGAT,
        "mlp": QG2V3MLP,
        "linear": QG2V3Linear,
    }.get(kind)
    if model_class is None or str(payload.get("model_id") or "") != QG2_V3_MODEL_IDS.get(kind):
        raise ValueError("QG2 V3 model identity mismatch")
    normalization = dict(payload.get("normalization") or {})
    validate_qg2_v3_normalization(normalization)
    model = model_class(
        normalization,
        hidden_dim=int(payload.get("hidden_dim") or 32),
        heads=int(payload.get("heads") or 1),
    )
    model.load_state_dict(payload["state_dict"], strict=True)
    model.eval()
    return model, dict(payload.get("metadata") or {}), normalization
