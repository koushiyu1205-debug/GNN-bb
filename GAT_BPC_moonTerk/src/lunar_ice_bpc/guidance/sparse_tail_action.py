"""Context-level GAT for one exact-safe sparse-tail action.

The exact solver never imports this module.  A caller may bind
``SparseTailGatPolicy`` as a framework-external callback; every load, hash,
OOD, calibration, or inference failure returns ``NOOP``.  S1/S4 remain
certificate-free discovery actions and the frozen exact proof owns closure.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from math import isfinite, log1p
from pathlib import Path
from time import perf_counter_ns
from typing import Mapping, Sequence

import torch
from torch import nn
from torch.nn import functional as F

from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.guidance.models import EdgeAttentionLayer
from lunar_ice_bpc.guidance.tensorization import (
    EDGE_STATIC_FEATURES,
    NODE_STATIC_FEATURES,
    build_static_graph_features,
)


SPARSE_TAIL_GAT_MODEL_SCHEMA = (
    "lunar_ice_bpc.sparse_tail_action_gat.v1"
)
SPARSE_TAIL_GAT_FEATURE_SCHEMA = (
    "lunar_ice_bpc.sparse_tail_action_features.v1"
)
SPARSE_TAIL_GAT_MANIFEST_SCHEMA = (
    "lunar_ice_bpc.sparse_tail_action_training_manifest.v1"
)
SPARSE_TAIL_NOOP = "NOOP"
SPARSE_TAIL_ACTIONS = ("S1", "S4")
SPARSE_TAIL_ACTION_PARAMETERS = {
    "S1": (1, 1),
    "S4": (4, 4),
}

NODE_DYNAMIC_FEATURES = (
    "true_dual",
    "absolute_true_dual",
    "active_column_support_frequency",
    "active_task_set_frequency",
)
GLOBAL_FEATURES = (
    "log1p_scale",
    "round_over_100",
    "log1p_active_column_count",
    "effective_harvest_target_over_128",
    "sparse_action_cap_over_60",
    "previous_added_over_target",
    "previous_selected_over_target",
    "previous_raw_unique_over_target",
    "previous_best_true_rc",
    "log1p_previous_processed_labels",
    "previous_final_judge_wall_over_300",
    "penultimate_added_over_target",
    "penultimate_selected_over_target",
    "penultimate_raw_unique_over_target",
    "penultimate_best_true_rc",
    "log1p_penultimate_processed_labels",
    "penultimate_final_judge_wall_over_300",
    "dual_l1_delta_from_previous",
    "dual_linf_delta_from_previous",
    "node_lp_bound",
    "node_lp_bound_delta",
    "post_harvest_wall_over_60",
    "log1p_post_harvest_processed_labels",
    "log1p_post_harvest_extended_labels",
    "post_harvest_best_true_rc",
    "post_harvest_search_exhaustive",
    "post_harvest_frontier_empty",
    "post_harvest_can_certify_no_negative",
    "post_harvest_state_incomplete",
)
ACTION_FEATURES = (
    "admission_k_over_4",
    "raw_pool_q_over_4",
    "log1p_k_over_log5",
    "k_over_effective_harvest_target",
)


@dataclass(frozen=True)
class SparseTailActionFeatures:
    instance_content_hash: str
    input_hash: str
    feature_hash: str
    scale: int
    node_features: tuple[tuple[float, ...], ...]
    edge_index: tuple[tuple[int, ...], tuple[int, ...]]
    edge_features: tuple[tuple[float, ...], ...]
    global_features: tuple[float, ...]
    action_ids: tuple[str, ...]
    action_features: tuple[tuple[float, ...], ...]
    schema_version: str = SPARSE_TAIL_GAT_FEATURE_SCHEMA

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "instance_content_hash": self.instance_content_hash,
            "input_hash": self.input_hash,
            "scale": self.scale,
            "node_features": [list(row) for row in self.node_features],
            "edge_index": [list(row) for row in self.edge_index],
            "edge_features": [list(row) for row in self.edge_features],
            "global_features": list(self.global_features),
            "action_ids": list(self.action_ids),
            "action_features": [list(row) for row in self.action_features],
        }


def build_sparse_tail_action_features(
    context: Mapping[str, object],
) -> SparseTailActionFeatures:
    """Build features available after empty harvest and before S1/S4."""

    data = context.get("data")
    if not isinstance(data, LunarIceData):
        raise ValueError("sparse-tail GAT context lacks LunarIceData")
    timing = str(
        context.get("one_deviation_sparse_tail_decision_timing") or ""
    )
    if timing != "after_empty_harvest_before_sparse_pass":
        raise ValueError("sparse-tail GAT decision timing mismatch")
    input_hash = str(
        context.get("one_deviation_sparse_tail_input_hash") or ""
    )
    if not _looks_like_sha256(input_hash):
        raise ValueError("sparse-tail GAT input hash is invalid")
    post_harvest = dict(context.get("post_harvest") or {})
    if int(post_harvest.get("audited_official_negative_column_count") or 0):
        raise ValueError("sparse-tail GAT received nonempty audited harvest")

    static = build_static_graph_features(data)
    dual_context = _dual_context(context)
    task_duals = {
        str(key): float(value)
        for key, value in (dual_context.get("task_duals") or {}).items()
    }
    fleet_dual = float(dual_context.get("fleet_dual") or 0.0)
    master_columns = tuple(context.get("master_columns") or ())
    column_support, task_set_support = _master_support(
        data,
        master_columns,
    )
    node_rows = []
    for node_id, static_row in zip(
        static.node_ids,
        static.node_features,
        strict=True,
    ):
        dual = (
            fleet_dual
            if node_id == "depot"
            else float(task_duals.get(node_id, 0.0))
        )
        node_rows.append(
            (
                *static_row,
                dual,
                abs(dual),
                float(column_support.get(node_id, 0.0)),
                float(task_set_support.get(node_id, 0.0)),
            )
        )

    history = [
        dict(row)
        for row in (context.get("prior_history") or ())
        if isinstance(row, Mapping)
    ]
    previous = history[-1] if history else {}
    penultimate = history[-2] if len(history) >= 2 else {}
    target = max(
        1.0,
        float(context.get("effective_harvest_target") or 1.0),
    )
    current_bound = _current_node_lp_bound(context)
    previous_bound = _optional_float(previous.get("node_lp_bound"), 0.0)
    dual_l1, dual_linf = _dual_delta(
        task_duals,
        dict(previous.get("dual_context") or {}),
    )
    action_cap = max(
        0.0,
        _optional_float(
            context.get("sparse_tail_time_cap_sec"),
            60.0,
        ),
    )
    global_features = (
        log1p(float(data.scale)),
        float(context.get("round") or 0) / 100.0,
        log1p(float(len(master_columns))),
        target / 128.0,
        action_cap / 60.0,
        _count(previous, "added_column_count") / target,
        _count(previous, "selected_diverse_negative_count") / target,
        _count(previous, "raw_unique_negative_count") / target,
        _best_rc(previous),
        log1p(_count(previous, "labeling_final_judge_harvest_pass_processed_labels")),
        _optional_float(previous.get("final_judge_wall_time"), 0.0)
        / 300.0,
        _count(penultimate, "added_column_count") / target,
        _count(penultimate, "selected_diverse_negative_count") / target,
        _count(penultimate, "raw_unique_negative_count") / target,
        _best_rc(penultimate),
        log1p(_count(penultimate, "labeling_final_judge_harvest_pass_processed_labels")),
        _optional_float(penultimate.get("final_judge_wall_time"), 0.0)
        / 300.0,
        dual_l1,
        dual_linf,
        current_bound,
        current_bound - previous_bound,
        _optional_float(
            post_harvest.get("harvest_pass_wall_time_sec"), 0.0
        )
        / 60.0,
        log1p(
            _count(post_harvest, "harvest_pass_processed_labels")
        ),
        log1p(
            _count(post_harvest, "harvest_pass_extended_labels")
        ),
        _optional_float(
            post_harvest.get("harvest_pass_best_true_rc"), 0.0
        ),
        float(bool(post_harvest.get("harvest_pass_search_exhaustive"))),
        float(bool(post_harvest.get("harvest_pass_frontier_empty"))),
        float(
            bool(
                post_harvest.get(
                    "harvest_pass_can_certify_no_negative"
                )
            )
        ),
        float(
            str(post_harvest.get("harvest_pass_pricing_state") or "")
            in {"INCOMPLETE_LIMIT", "LOCAL_NO_COLUMN_UNCERTIFIED"}
        ),
    )
    action_rows = []
    for action_id in SPARSE_TAIL_ACTIONS:
        admission, raw_pool = SPARSE_TAIL_ACTION_PARAMETERS[action_id]
        action_rows.append(
            (
                float(admission) / 4.0,
                float(raw_pool) / 4.0,
                log1p(float(admission)) / log1p(4.0),
                float(admission) / target,
            )
        )
    _require_finite(node_rows, "node")
    _require_finite(static.arc_features, "edge")
    _require_finite((global_features,), "global")
    _require_finite(action_rows, "action")
    payload = {
        "schema_version": SPARSE_TAIL_GAT_FEATURE_SCHEMA,
        "instance_content_hash": data.instance_content_hash,
        "input_hash": input_hash,
        "scale": int(data.scale),
        "node_features": [list(row) for row in node_rows],
        "edge_index": [
            list(static.arc_sources),
            list(static.arc_targets),
        ],
        "edge_features": [list(row) for row in static.arc_features],
        "global_features": list(global_features),
        "action_ids": list(SPARSE_TAIL_ACTIONS),
        "action_features": [list(row) for row in action_rows],
    }
    return SparseTailActionFeatures(
        instance_content_hash=data.instance_content_hash,
        input_hash=input_hash,
        feature_hash=stable_payload_hash(payload),
        scale=int(data.scale),
        node_features=tuple(tuple(row) for row in node_rows),
        edge_index=(
            tuple(static.arc_sources),
            tuple(static.arc_targets),
        ),
        edge_features=tuple(static.arc_features),
        global_features=tuple(global_features),
        action_ids=SPARSE_TAIL_ACTIONS,
        action_features=tuple(action_rows),
    )


class TwoHeadSparseTailActionGAT(nn.Module):
    """Predict P(benefit) and positive conditional gain for S1/S4."""

    def __init__(
        self,
        *,
        node_input_dim: int,
        edge_input_dim: int,
        global_input_dim: int,
        action_input_dim: int,
        hidden_dim: int = 32,
        heads: int = 2,
        layers: int = 2,
    ) -> None:
        super().__init__()
        if min(hidden_dim, heads, layers) <= 0:
            raise ValueError("sparse-tail GAT dimensions must be positive")
        self.schema_version = SPARSE_TAIL_GAT_MODEL_SCHEMA
        self.node_encoder = nn.Sequential(
            nn.Linear(int(node_input_dim), int(hidden_dim)),
            nn.ReLU(),
        )
        self.edge_encoder = nn.Sequential(
            nn.Linear(int(edge_input_dim), int(hidden_dim)),
            nn.ReLU(),
        )
        self.layers = nn.ModuleList(
            EdgeAttentionLayer(hidden_dim, hidden_dim, heads)
            for _ in range(int(layers))
        )
        shared_input = (
            2 * int(hidden_dim)
            + int(global_input_dim)
            + int(action_input_dim)
        )
        self.shared = nn.Sequential(
            nn.Linear(shared_input, int(hidden_dim)),
            nn.ReLU(),
        )
        self.positive_probability_head = nn.Linear(hidden_dim, 1)
        self.positive_magnitude_head = nn.Linear(hidden_dim, 1)

    def forward(
        self,
        *,
        node_features: torch.Tensor,
        edge_index: torch.Tensor,
        edge_features: torch.Tensor,
        global_features: torch.Tensor,
        action_features: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        node_embedding = self.node_encoder(node_features)
        edge_embedding = self.edge_encoder(edge_features)
        for layer in self.layers:
            node_embedding = layer(
                node_embedding,
                edge_index,
                edge_embedding,
            )
        graph_embedding = torch.cat(
            (node_embedding.mean(dim=0), node_embedding.amax(dim=0)),
            dim=-1,
        )
        action_count = int(action_features.shape[0])
        shared = self.shared(
            torch.cat(
                (
                    graph_embedding.reshape(1, -1).expand(
                        action_count, -1
                    ),
                    global_features.reshape(1, -1).expand(
                        action_count, -1
                    ),
                    action_features,
                ),
                dim=-1,
            )
        )
        logits = self.positive_probability_head(shared).squeeze(-1)
        magnitude = F.softplus(
            self.positive_magnitude_head(shared).squeeze(-1)
        )
        probability = torch.sigmoid(logits)
        return {
            "positive_probability_logits": logits,
            "positive_probability": probability,
            "conditional_positive_relative_gain": magnitude,
            "expected_positive_relative_gain": probability * magnitude,
        }


def sparse_tail_two_head_loss(
    outputs: Mapping[str, torch.Tensor],
    *,
    beneficial: torch.Tensor,
    observed_mask: torch.Tensor,
    positive_relative_gain: torch.Tensor,
) -> dict[str, torch.Tensor]:
    logits = outputs["positive_probability_logits"]
    magnitude = outputs[
        "conditional_positive_relative_gain"
    ].clamp_min(1.0e-6)
    observed = observed_mask.bool()
    positive = observed & beneficial.bool()
    probability_loss = (
        F.binary_cross_entropy_with_logits(
            logits[observed], beneficial.to(logits.dtype)[observed]
        )
        if bool(observed.any())
        else logits.sum() * 0.0
    )
    magnitude_loss = (
        F.smooth_l1_loss(
            magnitude[positive],
            positive_relative_gain.to(magnitude.dtype)[positive],
        )
        if bool(positive.any())
        else magnitude.sum() * 0.0
    )
    return {
        "loss": probability_loss + magnitude_loss,
        "positive_probability_loss": probability_loss,
        "positive_magnitude_loss": magnitude_loss,
    }


@dataclass(frozen=True)
class SparseTailActionDecision:
    action: str = SPARSE_TAIL_NOOP
    positive_probability: float = 0.0
    conditional_positive_relative_gain: float = 0.0
    expected_positive_relative_gain: float = 0.0
    abstained: bool = True
    reason: str = "noop"


def choose_sparse_tail_action(
    *,
    action_ids: Sequence[str],
    probabilities: Sequence[float],
    conditional_positive_gains: Sequence[float],
    probability_threshold: float,
    expected_gain_threshold: float,
    context_ood: bool = False,
    calibration_harm_gate_pass: bool = False,
    memory_adverse_event: bool = False,
) -> SparseTailActionDecision:
    if context_ood:
        return SparseTailActionDecision(reason="context_ood")
    if memory_adverse_event:
        return SparseTailActionDecision(reason="memory_risk_veto")
    if not calibration_harm_gate_pass:
        return SparseTailActionDecision(reason="harm_gate_not_passed")
    if not (
        len(action_ids)
        == len(probabilities)
        == len(conditional_positive_gains)
    ):
        raise ValueError("sparse-tail action score length mismatch")
    eligible = []
    for action, probability, magnitude in zip(
        action_ids,
        probabilities,
        conditional_positive_gains,
        strict=True,
    ):
        action_id = str(action)
        if action_id not in SPARSE_TAIL_ACTIONS:
            raise ValueError("unsupported sparse-tail scored action")
        p = float(probability)
        mu = float(magnitude)
        score = p * mu
        if (
            isfinite(p)
            and isfinite(mu)
            and p >= float(probability_threshold)
            and score >= float(expected_gain_threshold)
        ):
            eligible.append((score, p, mu, action_id))
    if not eligible:
        return SparseTailActionDecision(reason="threshold_abstain")
    score, probability, magnitude, action = max(
        eligible,
        key=lambda row: (row[0], row[1], -SPARSE_TAIL_ACTIONS.index(row[3])),
    )
    return SparseTailActionDecision(
        action=action,
        positive_probability=probability,
        conditional_positive_relative_gain=magnitude,
        expected_positive_relative_gain=score,
        abstained=False,
        reason="calibrated_action",
    )


class SparseTailGatPolicy:
    """Lazy fail-closed runtime callback consumed by the exact adapter."""

    def __init__(
        self,
        manifest_path: str | Path,
        *,
        evaluation_mode: bool = False,
    ) -> None:
        self.manifest_path = Path(manifest_path).resolve()
        self.evaluation_mode = bool(evaluation_mode)
        self._loaded: tuple[dict, TwoHeadSparseTailActionGAT] | None = None

    def preload(self, data: LunarIceData | None = None) -> dict[str, object]:
        """Load and warm the model before the timed policy callback."""

        started = perf_counter_ns()
        try:
            _manifest, model = self._load()
            if data is not None:
                static = build_static_graph_features(data)
                node_width = int(model.node_encoder[0].in_features)
                edge_width = int(model.edge_encoder[0].in_features)
                global_width = int(
                    model.shared[0].in_features
                    - 2 * model.node_encoder[0].out_features
                    - len(ACTION_FEATURES)
                )
                with torch.no_grad():
                    model(
                        node_features=torch.zeros(
                            (len(static.node_ids), node_width),
                            dtype=torch.float32,
                        ),
                        edge_index=torch.tensor(
                            (static.arc_sources, static.arc_targets),
                            dtype=torch.long,
                        ),
                        edge_features=torch.zeros(
                            (len(static.arc_features), edge_width),
                            dtype=torch.float32,
                        ),
                        global_features=torch.zeros(
                            global_width,
                            dtype=torch.float32,
                        ),
                        action_features=torch.zeros(
                            (len(SPARSE_TAIL_ACTIONS), len(ACTION_FEATURES)),
                            dtype=torch.float32,
                        ),
                    )
            return {
                "success": True,
                "wall_ms": (
                    perf_counter_ns() - started
                )
                / 1_000_000.0,
                "error": "",
            }
        except Exception as exc:
            return {
                "success": False,
                "wall_ms": (
                    perf_counter_ns() - started
                )
                / 1_000_000.0,
                "error": f"{type(exc).__name__}: {exc}",
            }

    def __call__(self, context: Mapping[str, object]) -> dict[str, object]:
        input_hash = str(
            context.get("one_deviation_sparse_tail_input_hash") or ""
        )
        started = perf_counter_ns()
        try:
            manifest, model = self._load()
            features = build_sparse_tail_action_features(context)
            hash_valid = features.input_hash == input_hash
            ood = not _within_envelope(
                features,
                dict(manifest.get("feature_envelope") or {}),
            )
            if not hash_valid or ood:
                return {
                    "action": SPARSE_TAIL_NOOP,
                    "policy_kind": "gat",
                    "decision_reason": (
                        "context_ood" if ood else "input_hash_mismatch"
                    ),
                    "fallback_to_noop": True,
                    "input_hash": input_hash,
                    "manifest_sha256": _sha256(self.manifest_path),
                    "checkpoint_sha256": str(
                        manifest.get("checkpoint_sha256") or ""
                    ),
                    "hash_valid": hash_valid,
                    "ood": ood,
                    "inference_wall_ms": (
                        perf_counter_ns() - started
                    )
                    / 1_000_000.0,
                    "model_scores": {},
                    "feature_hash": features.feature_hash,
                }
            tensors = tensorize_sparse_tail_action_features(features)
            with torch.no_grad():
                outputs = model(**tensors)
            probabilities = outputs["positive_probability"].tolist()
            magnitudes = outputs[
                "conditional_positive_relative_gain"
            ].tolist()
            calibration = dict(manifest.get("calibration") or {})
            decision = choose_sparse_tail_action(
                action_ids=features.action_ids,
                probabilities=probabilities,
                conditional_positive_gains=magnitudes,
                probability_threshold=float(
                    calibration.get("probability_threshold") or 1.0
                ),
                expected_gain_threshold=float(
                    calibration.get("expected_gain_threshold")
                    or float("inf")
                ),
                context_ood=ood,
                calibration_harm_gate_pass=bool(
                    calibration.get("harm_gate_pass")
                ),
                memory_adverse_event=False,
            )
            evaluation_authorized = bool(
                manifest.get("evaluation_authorized")
            )
            effective_action = (
                decision.action
                if evaluation_authorized and self.evaluation_mode
                else SPARSE_TAIL_NOOP
            )
            reason = decision.reason
            fallback = False
            if not evaluation_authorized:
                reason = "manifest_not_evaluation_authorized"
                fallback = True
            elif not self.evaluation_mode:
                reason = "shadow_mode_noop"
                fallback = True
            return {
                "action": effective_action,
                "policy_kind": "gat",
                "decision_reason": reason,
                "fallback_to_noop": fallback,
                "input_hash": input_hash,
                "manifest_sha256": _sha256(self.manifest_path),
                "checkpoint_sha256": str(
                    manifest.get("checkpoint_sha256") or ""
                ),
                "hash_valid": hash_valid,
                "ood": ood,
                "inference_wall_ms": (
                    perf_counter_ns() - started
                )
                / 1_000_000.0,
                "model_scores": {
                    action: {
                        "positive_probability": float(probability),
                        "conditional_positive_relative_gain": float(
                            magnitude
                        ),
                        "expected_positive_relative_gain": float(
                            probability * magnitude
                        ),
                    }
                    for action, probability, magnitude in zip(
                        features.action_ids,
                        probabilities,
                        magnitudes,
                        strict=True,
                    )
                },
                "feature_hash": features.feature_hash,
            }
        except Exception as exc:
            return {
                "action": SPARSE_TAIL_NOOP,
                "policy_kind": "gat",
                "decision_reason": "gat_runtime_failure",
                "fallback_to_noop": True,
                "runtime_error": f"{type(exc).__name__}: {exc}",
                "input_hash": input_hash,
                "manifest_sha256": (
                    _sha256(self.manifest_path)
                    if self.manifest_path.is_file()
                    else ""
                ),
                "checkpoint_sha256": "",
                "hash_valid": False,
                "ood": True,
                "inference_wall_ms": (
                    perf_counter_ns() - started
                )
                / 1_000_000.0,
                "model_scores": {},
                "feature_hash": "",
            }

    def _load(self) -> tuple[dict, TwoHeadSparseTailActionGAT]:
        if self._loaded is not None:
            return self._loaded
        manifest = json.loads(
            self.manifest_path.read_text(encoding="utf-8")
        )
        if manifest.get("schema_version") != SPARSE_TAIL_GAT_MANIFEST_SCHEMA:
            raise ValueError("sparse-tail GAT manifest schema mismatch")
        if str(manifest.get("feature_schema_hash") or "") != (
            stable_payload_hash(sparse_tail_feature_schema())
        ):
            raise ValueError("sparse-tail GAT feature schema mismatch")
        if tuple(manifest.get("action_ids") or ()) != SPARSE_TAIL_ACTIONS:
            raise ValueError("sparse-tail GAT action space mismatch")
        checkpoint_path = Path(str(manifest.get("checkpoint") or ""))
        if not checkpoint_path.is_absolute():
            checkpoint_path = (
                self.manifest_path.parent / checkpoint_path
            ).resolve()
        if _sha256(checkpoint_path) != str(
            manifest.get("checkpoint_sha256") or ""
        ):
            raise ValueError("sparse-tail GAT checkpoint hash mismatch")
        checkpoint = torch.load(
            checkpoint_path,
            map_location="cpu",
            weights_only=True,
        )
        if checkpoint.get("schema_version") != SPARSE_TAIL_GAT_MODEL_SCHEMA:
            raise ValueError("sparse-tail GAT checkpoint schema mismatch")
        dimensions = dict(checkpoint.get("dimensions") or {})
        model = TwoHeadSparseTailActionGAT(**dimensions)
        model.load_state_dict(checkpoint["state_dict"])
        model.eval()
        self._loaded = (manifest, model)
        return self._loaded


def tensorize_sparse_tail_action_features(
    features: SparseTailActionFeatures,
) -> dict[str, torch.Tensor]:
    return {
        "node_features": torch.tensor(
            features.node_features, dtype=torch.float32
        ),
        "edge_index": torch.tensor(
            features.edge_index, dtype=torch.long
        ),
        "edge_features": torch.tensor(
            features.edge_features, dtype=torch.float32
        ),
        "global_features": torch.tensor(
            features.global_features, dtype=torch.float32
        ),
        "action_features": torch.tensor(
            features.action_features, dtype=torch.float32
        ),
    }


def sparse_tail_feature_schema() -> dict[str, object]:
    return {
        "schema_version": SPARSE_TAIL_GAT_FEATURE_SCHEMA,
        "node_features": [
            *NODE_STATIC_FEATURES,
            *NODE_DYNAMIC_FEATURES,
        ],
        "edge_features": list(EDGE_STATIC_FEATURES),
        "global_features": list(GLOBAL_FEATURES),
        "action_features": list(ACTION_FEATURES),
        "action_ids": list(SPARSE_TAIL_ACTIONS),
    }


def _dual_context(context: Mapping[str, object]) -> dict[str, object]:
    master = context.get("master")
    reduced = getattr(master, "reduced_cost_context", None)
    if reduced is not None:
        return {
            "fleet_dual": float(getattr(reduced, "fleet_dual", 0.0)),
            "task_duals": dict(getattr(reduced, "task_duals", {}) or {}),
        }
    row = dict(context.get("dual_context") or {})
    if not row:
        raise ValueError("sparse-tail GAT context lacks true duals")
    return row


def _master_support(
    data: LunarIceData,
    master_columns: Sequence[object],
) -> tuple[dict[str, float], dict[str, float]]:
    denominator = max(1.0, float(len(master_columns)))
    task_sets = {
        frozenset(str(task_id) for task_id in getattr(column, "task_set", ()))
        for column in master_columns
    }
    task_set_denominator = max(1.0, float(len(task_sets)))
    column_counts = {task_id: 0 for task_id in data.task_ids}
    task_set_counts = {task_id: 0 for task_id in data.task_ids}
    for column in master_columns:
        for task_id in set(
            str(value) for value in getattr(column, "task_set", ())
        ):
            if task_id in column_counts:
                column_counts[task_id] += 1
    for task_set in task_sets:
        for task_id in task_set:
            if task_id in task_set_counts:
                task_set_counts[task_id] += 1
    return (
        {
            task_id: count / denominator
            for task_id, count in column_counts.items()
        },
        {
            task_id: count / task_set_denominator
            for task_id, count in task_set_counts.items()
        },
    )


def _current_node_lp_bound(context: Mapping[str, object]) -> float:
    master = context.get("master")
    for attribute in ("objective", "root_lp_bound", "bound"):
        value = getattr(master, attribute, None)
        if value is not None:
            return _optional_float(value, 0.0)
    return _optional_float(context.get("node_lp_bound"), 0.0)


def _dual_delta(
    current: Mapping[str, float],
    previous_context: Mapping[str, object],
) -> tuple[float, float]:
    previous = {
        str(key): float(value)
        for key, value in (
            previous_context.get("task_duals") or {}
        ).items()
    }
    deltas = [
        abs(float(value) - float(previous.get(task_id, 0.0)))
        for task_id, value in current.items()
    ]
    return sum(deltas), max(deltas, default=0.0)


def _best_rc(row: Mapping[str, object]) -> float:
    for key in (
        "harvest_best_true_rc",
        "final_judge_harvest_best_true_rc",
        "candidate_search_best_reduced_cost",
    ):
        if row.get(key) is not None:
            return _optional_float(row.get(key), 0.0)
    return 0.0


def _count(row: Mapping[str, object], key: str) -> float:
    return max(0.0, _optional_float(row.get(key), 0.0))


def _optional_float(value: object, default: float) -> float:
    if value is None:
        return float(default)
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    return result if isfinite(result) else float(default)


def _require_finite(rows, name: str) -> None:
    if any(
        not isfinite(float(value))
        for row in rows
        for value in row
    ):
        raise ValueError(f"sparse-tail GAT {name} features are non-finite")


def _within_envelope(
    features: SparseTailActionFeatures,
    envelope: Mapping[str, object],
) -> bool:
    if not envelope:
        return False
    if int(features.scale) not in {
        int(value) for value in envelope.get("allowed_scales") or ()
    }:
        return False
    global_min = list(envelope.get("global_min") or ())
    global_max = list(envelope.get("global_max") or ())
    if not (
        len(global_min)
        == len(global_max)
        == len(features.global_features)
    ):
        return False
    return all(
        float(lower) - 1.0e-9
        <= float(value)
        <= float(upper) + 1.0e-9
        for value, lower, upper in zip(
            features.global_features,
            global_min,
            global_max,
            strict=True,
        )
    )


def _looks_like_sha256(value: str) -> bool:
    normalized = str(value).lower()
    return len(normalized) == 64 and all(
        character in "0123456789abcdef"
        for character in normalized
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
