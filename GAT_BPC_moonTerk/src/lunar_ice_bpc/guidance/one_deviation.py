"""Two-head, abstaining one-deviation route policy.

Torch is intentionally isolated in this module.  The exact solver may import
the framework-free guidance package without importing torch.  Every deployment
failure returns the frozen Exact no-op action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp, inf, isfinite, log, sqrt
from threading import Lock
from typing import Mapping, Sequence

import torch
from torch import nn
from torch.nn import functional as F

from lunar_ice_bpc.guidance.models import EdgeAttentionLayer


ONE_DEVIATION_MODEL_SCHEMA_V1 = (
    "lunar_ice_bpc.two_head_one_deviation_gat.v1"
)
ONE_DEVIATION_CALIBRATION_SCHEMA_V1 = (
    "lunar_ice_bpc.one_deviation_harm_calibration.v1"
)
NOOP_ACTION_ID = "ONE_DEVIATION_NOOP"


ONE_DEVIATION_RELATIONAL_CONTEXT_SCHEMA = (
    "rank_offset_div_32",
    "true_rc_gap_to_rank_k",
    "task_jaccard_to_rank_k",
    "mean_task_jaccard_to_selected_batch",
    "max_task_jaccard_to_selected_batch",
    "exact_task_set_match_in_selected_batch",
    "support_change_delta_to_rank_k",
    "new_task_set_delta_to_rank_k",
)


def augment_one_deviation_candidate_contexts(
    *,
    candidate_task_masks: Sequence[Sequence[float]],
    candidate_contexts: Sequence[Sequence[float]],
    candidate_rank_offsets: Sequence[int],
    selected_task_masks: Sequence[Sequence[float]],
    selected_contexts: Sequence[Sequence[float]],
) -> list[list[float]]:
    """Add action-relative features shared by training and deployment.

    A promotion's effect is defined relative to the rank-K route it replaces
    and to the already selected batch. Candidate-only features cannot identify
    that counterfactual and are therefore insufficient for one-deviation
    learning.
    """

    candidates = [list(row) for row in candidate_task_masks]
    contexts = [list(row) for row in candidate_contexts]
    offsets = [int(value) for value in candidate_rank_offsets]
    selected_masks = [list(row) for row in selected_task_masks]
    selected_rows = [list(row) for row in selected_contexts]
    if not candidates or not selected_masks:
        raise ValueError("one-deviation relational context is empty")
    if not (
        len(candidates) == len(contexts) == len(offsets)
        and len(selected_masks) == len(selected_rows)
    ):
        raise ValueError("one-deviation relational context length mismatch")
    width = len(candidates[0])
    if width <= 0 or any(len(row) != width for row in (*candidates, *selected_masks)):
        raise ValueError("one-deviation task-mask width mismatch")
    if any(len(row) < 3 for row in (*contexts, *selected_rows)):
        raise ValueError("one-deviation base context is incomplete")
    if any(value < 1 or value > 32 for value in offsets):
        raise ValueError("one-deviation rank offset is outside [1,32]")

    selected_sets = [_mask_support(row) for row in selected_masks]
    dropped_set = selected_sets[-1]
    dropped_context = selected_rows[-1]
    result = []
    for mask, context, offset in zip(
        candidates, contexts, offsets, strict=True
    ):
        candidate_set = _mask_support(mask)
        similarities = [
            _jaccard(candidate_set, selected_set)
            for selected_set in selected_sets
        ]
        result.append(
            [
                *[float(value) for value in context],
                float(offset) / 32.0,
                float(context[0]) - float(dropped_context[0]),
                _jaccard(candidate_set, dropped_set),
                sum(similarities) / len(similarities),
                max(similarities),
                1.0 if candidate_set in selected_sets else 0.0,
                float(context[1]) - float(dropped_context[1]),
                float(context[2]) - float(dropped_context[2]),
            ]
        )
    return result


def _mask_support(mask: Sequence[float]) -> frozenset[int]:
    return frozenset(
        index for index, value in enumerate(mask) if float(value) > 0.5
    )


def _jaccard(left: frozenset[int], right: frozenset[int]) -> float:
    union = left | right
    return 1.0 if not union else len(left & right) / len(union)


@dataclass
class OneDeviationLedger:
    """Process-local safety ledger: at most one promotion for each root."""

    consumed_root_keys: set[str] = field(default_factory=set)
    lock: Lock = field(default_factory=Lock, repr=False)

    def consumed(self, root_key: str) -> bool:
        with self.lock:
            return str(root_key) in self.consumed_root_keys

    def claim(self, root_key: str) -> bool:
        key = str(root_key)
        with self.lock:
            if key in self.consumed_root_keys:
                return False
            self.consumed_root_keys.add(key)
            return True


@dataclass(frozen=True)
class OneDeviationDecision:
    action_id: str = NOOP_ACTION_ID
    promoted_candidate_id: str | None = None
    promoted_from_rank: int | None = None
    probability_positive: float = 0.0
    conditional_positive_relative_gain: float = 0.0
    expected_positive_relative_gain: float = 0.0
    abstained: bool = True
    reason: str = "p0_noop"

    @property
    def promotes(self) -> bool:
        return self.promoted_candidate_id is not None

    @property
    def conditional_positive_gain_sec(self) -> float:
        """Deprecated alias retained only for pre-training test callers."""

        return self.conditional_positive_relative_gain

    @property
    def expected_positive_gain_sec(self) -> float:
        """Deprecated alias retained only for pre-training test callers."""

        return self.expected_positive_relative_gain


class TwoHeadOneDeviationGAT(nn.Module):
    """One fixed GAT with benefit-probability and positive-magnitude heads."""

    def __init__(
        self,
        *,
        node_input_dim: int,
        edge_input_dim: int,
        candidate_context_dim: int,
        global_context_dim: int,
        hidden_dim: int = 24,
        heads: int = 2,
        layers: int = 2,
    ) -> None:
        super().__init__()
        if hidden_dim <= 0 or heads <= 0 or layers <= 0:
            raise ValueError("GAT dimensions must be positive")
        self.schema_version = ONE_DEVIATION_MODEL_SCHEMA_V1
        self.node_encoder = nn.Sequential(
            nn.Linear(int(node_input_dim), int(hidden_dim)),
            nn.ReLU(),
        )
        self.edge_encoder = nn.Sequential(
            nn.Linear(int(edge_input_dim), int(hidden_dim)),
            nn.ReLU(),
        )
        self.layers = nn.ModuleList(
            EdgeAttentionLayer(
                int(hidden_dim), int(hidden_dim), int(heads)
            )
            for _ in range(int(layers))
        )
        action_dim = (
            2 * int(hidden_dim)
            + int(candidate_context_dim)
            + int(global_context_dim)
        )
        self.shared_action = nn.Sequential(
            nn.Linear(action_dim, int(hidden_dim)),
            nn.ReLU(),
        )
        self.positive_probability_head = nn.Linear(
            int(hidden_dim), 1
        )
        self.positive_magnitude_head = nn.Linear(
            int(hidden_dim), 1
        )

    def forward(
        self,
        *,
        node_features: torch.Tensor,
        edge_index: torch.Tensor,
        edge_features: torch.Tensor,
        candidate_task_masks: torch.Tensor,
        candidate_context: torch.Tensor,
        global_context: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        node_embedding = self.node_encoder(node_features)
        edge_embedding = self.edge_encoder(edge_features)
        for layer in self.layers:
            node_embedding = layer(
                node_embedding, edge_index, edge_embedding
            )
        masks = candidate_task_masks.to(node_embedding.dtype)
        denominators = masks.sum(dim=1, keepdim=True).clamp_min(1.0)
        route_embedding = masks @ node_embedding / denominators
        graph_embedding = node_embedding.mean(dim=0)
        candidate_count = int(route_embedding.shape[0])
        global_row = global_context.reshape(1, -1).expand(
            candidate_count, -1
        )
        graph_rows = graph_embedding.reshape(1, -1).expand(
            candidate_count, -1
        )
        action_embedding = self.shared_action(
            torch.cat(
                (
                    route_embedding,
                    graph_rows,
                    candidate_context,
                    global_row,
                ),
                dim=-1,
            )
        )
        probability_logits = self.positive_probability_head(
            action_embedding
        ).squeeze(-1)
        positive_relative_gain = F.softplus(
            self.positive_magnitude_head(action_embedding).squeeze(-1)
        )
        positive_probability = torch.sigmoid(probability_logits)
        return {
            "positive_probability_logits": probability_logits,
            "positive_probability": positive_probability,
            "conditional_positive_relative_gain": positive_relative_gain,
            "expected_positive_relative_gain": (
                positive_probability * positive_relative_gain
            ),
            # Read-only compatibility aliases. New training and runtime paths
            # consume the explicit relative-gain keys above.
            "conditional_positive_gain_sec": positive_relative_gain,
            "expected_positive_gain_sec": (
                positive_probability * positive_relative_gain
            ),
        }


def one_deviation_hurdle_loss(
    outputs: Mapping[str, torch.Tensor],
    *,
    beneficial: torch.Tensor,
    observed_mask: torch.Tensor,
    positive_relative_gain: torch.Tensor | None = None,
    right_censored_positive_mask: torch.Tensor | None = None,
    censor_lower_bound_relative: torch.Tensor | None = None,
    positive_gain_sec: torch.Tensor | None = None,
    censor_lower_bound_sec: torch.Tensor | None = None,
    probability_weight: float = 1.0,
    magnitude_weight: float = 1.0,
    survival_weight: float = 1.0,
) -> dict[str, torch.Tensor]:
    """Hurdle loss with masked outcomes and optional censor likelihood."""

    logits = outputs["positive_probability_logits"]
    magnitude = outputs["conditional_positive_relative_gain"].clamp_min(
        1.0e-6
    )
    magnitude_target = (
        positive_relative_gain
        if positive_relative_gain is not None
        else positive_gain_sec
    )
    if magnitude_target is None:
        raise ValueError("positive relative-gain target is required")
    observed = observed_mask.bool()
    labels = beneficial.to(logits.dtype)
    probability_loss = (
        F.binary_cross_entropy_with_logits(
            logits[observed], labels[observed]
        )
        if bool(observed.any())
        else logits.sum() * 0.0
    )
    positive_observed = observed & beneficial.bool()
    magnitude_loss = (
        F.smooth_l1_loss(
            magnitude[positive_observed],
            magnitude_target.to(magnitude.dtype)[positive_observed],
        )
        if bool(positive_observed.any())
        else magnitude.sum() * 0.0
    )
    survival_loss = magnitude.sum() * 0.0
    if (
        right_censored_positive_mask is not None
        and (
            censor_lower_bound_relative is not None
            or censor_lower_bound_sec is not None
        )
    ):
        censored = right_censored_positive_mask.bool()
        if bool(censored.any()):
            probability = torch.sigmoid(logits[censored]).clamp(
                1.0e-6, 1.0 - 1.0e-6
            )
            censor_target = (
                censor_lower_bound_relative
                if censor_lower_bound_relative is not None
                else censor_lower_bound_sec
            )
            assert censor_target is not None
            delay_lower = censor_target.to(
                magnitude.dtype
            )[censored].clamp_min(0.0)
            # The P0 milestone is observed while the promotion milestone is
            # right-censored at the matched budget.  Hence the promotion is
            # at least ``delay_lower`` seconds behind P0.  The positive-gain
            # component has support only above zero, so this censor event is
            # carried by the hurdle's non-beneficial mass (1 - p).  It is not
            # inserted into the ordinary BCE labels and no fake negative
            # delta-time target is created.
            censor_likelihood = (1.0 - probability).clamp_min(
                1.0e-9
            )
            informative = (delay_lower >= 0.0).to(
                censor_likelihood.dtype
            )
            survival_loss = (
                -torch.log(censor_likelihood) * informative
            ).sum() / informative.sum().clamp_min(1.0)
    total = (
        float(probability_weight) * probability_loss
        + float(magnitude_weight) * magnitude_loss
        + float(survival_weight) * survival_loss
    )
    return {
        "loss": total,
        "positive_probability_loss": probability_loss,
        "positive_magnitude_loss": magnitude_loss,
        "censored_survival_loss": survival_loss,
    }


def calibrate_one_deviation_thresholds(
    rows: Sequence[Mapping[str, object]],
    *,
    harmful_rate_upper_bound: float = 0.05,
    beneficial_precision_lower_bound: float = 0.80,
    confidence_z: float = 1.959963984540054,
) -> dict[str, object]:
    """Choose thresholds on the action that deployment selects per context.

    Counting every candidate that passes a threshold is optimistic because
    runtime promotes only the maximum-score candidate in a context.  A harmful
    winner must not be diluted by many lower-scored beneficial candidates from
    the same context.
    """

    normalized = []
    for index, row in enumerate(rows):
        probability = float(row["positive_probability"])
        gain = float(
            row.get(
                "expected_positive_relative_gain",
                row.get("expected_positive_gain_sec"),
            )
        )
        outcome = str(row["outcome"])
        if (
            not isfinite(probability)
            or not isfinite(gain)
            or not 0.0 <= probability <= 1.0
            or gain < 0.0
            or outcome
            not in {"beneficial", "harmful", "neutral", "unknown"}
        ):
            raise ValueError("invalid calibration row")
        normalized.append(
            {
                "probability": probability,
                "gain": gain,
                "outcome": outcome,
                "context_hash": str(
                    row.get("context_hash") or f"row-{index:09d}"
                ),
                "candidate_rank": int(
                    row.get("candidate_rank") or index + 1
                ),
                "action_id": str(
                    row.get("action_id") or f"row-{index:09d}"
                ),
            }
        )
    probability_thresholds = sorted(
        {value["probability"] for value in normalized}, reverse=True
    )
    gain_thresholds = sorted(
        {value["gain"] for value in normalized}, reverse=True
    )
    feasible = []
    for probability_threshold in probability_thresholds:
        for gain_threshold in gain_thresholds:
            eligible_by_context: dict[str, list[dict[str, object]]] = {}
            for row in normalized:
                if (
                    float(row["probability"])
                    < probability_threshold
                    or float(row["gain"]) < gain_threshold
                ):
                    continue
                eligible_by_context.setdefault(
                    str(row["context_hash"]), []
                ).append(row)
            selected = [
                min(
                    context_rows,
                    key=lambda row: (
                        -float(row["gain"]),
                        -float(row["probability"]),
                        int(row["candidate_rank"]),
                        str(row["action_id"]),
                    ),
                )
                for context_rows in eligible_by_context.values()
            ]
            if not selected:
                continue
            harmful = sum(
                row["outcome"] == "harmful" for row in selected
            )
            beneficial = sum(
                row["outcome"] == "beneficial" for row in selected
            )
            unknown = sum(
                row["outcome"] == "unknown" for row in selected
            )
            harm_upper = _wilson_bound(
                harmful, len(selected), confidence_z, upper=True
            )
            precision_lower = _wilson_bound(
                beneficial, len(selected), confidence_z, upper=False
            )
            if (
                unknown == 0
                and harm_upper <= float(harmful_rate_upper_bound)
                and precision_lower
                >= float(beneficial_precision_lower_bound)
            ):
                feasible.append(
                    (
                        -len(selected),
                        probability_threshold,
                        gain_threshold,
                        harm_upper,
                        precision_lower,
                        unknown,
                    )
                )
    if not feasible:
        return {
            "schema_version": ONE_DEVIATION_CALIBRATION_SCHEMA_V1,
            "gate_pass": False,
            "probability_threshold": inf,
            "expected_relative_gain_threshold": inf,
            "expected_gain_threshold_sec": inf,
            "selected_count": 0,
            "calibration_candidate_count": len(normalized),
            "calibration_context_count": len(
                {str(row["context_hash"]) for row in normalized}
            ),
            "calibration_unit": "deployed_winner_per_context",
            "failure_policy": "always_noop",
        }
    chosen = min(feasible)
    selected_count = -int(chosen[0])
    return {
        "schema_version": ONE_DEVIATION_CALIBRATION_SCHEMA_V1,
        "gate_pass": True,
        "probability_threshold": float(chosen[1]),
        "expected_relative_gain_threshold": float(chosen[2]),
        "expected_gain_threshold_sec": float(chosen[2]),
        "selected_count": selected_count,
        "calibration_candidate_count": len(normalized),
        "calibration_context_count": len(
            {str(row["context_hash"]) for row in normalized}
        ),
        "calibration_unit": "deployed_winner_per_context",
        "harmful_rate_95_upper": float(chosen[3]),
        "beneficial_precision_95_lower": float(chosen[4]),
        "unknown_selected_count": int(chosen[5]),
        "failure_policy": "always_noop",
    }


def select_one_deviation(
    *,
    candidate_ids: Sequence[str],
    candidate_ranks: Sequence[int],
    positive_probabilities: Sequence[float],
    conditional_positive_relative_gains: Sequence[float] | None = None,
    conditional_positive_gains_sec: Sequence[float] | None = None,
    batch_size: int,
    probability_threshold: float,
    expected_relative_gain_threshold: float | None = None,
    expected_gain_threshold_sec: float | None = None,
    root_key: str,
    ledger: OneDeviationLedger,
    context_hash: str,
    expected_context_hash: str,
    model_hash: str,
    expected_model_hash: str,
    calibration_gate_pass: bool,
    ood: bool = False,
    adverse_memory_event: bool = False,
) -> OneDeviationDecision:
    """Select one legal promotion or fail closed to the Exact P0 no-op."""

    gain_values = (
        conditional_positive_relative_gains
        if conditional_positive_relative_gains is not None
        else conditional_positive_gains_sec
    )
    gain_threshold = (
        expected_relative_gain_threshold
        if expected_relative_gain_threshold is not None
        else expected_gain_threshold_sec
    )
    if gain_values is None or gain_threshold is None:
        return OneDeviationDecision(reason="relative_gain_contract_missing")
    rows = tuple(
        zip(
            candidate_ids,
            candidate_ranks,
            positive_probabilities,
            gain_values,
            strict=True,
        )
    )
    if ledger.consumed(root_key):
        return OneDeviationDecision(reason="root_intervention_already_used")
    if not calibration_gate_pass:
        return OneDeviationDecision(reason="calibration_gate_failed")
    if str(context_hash) != str(expected_context_hash):
        return OneDeviationDecision(reason="context_hash_mismatch")
    if str(model_hash) != str(expected_model_hash):
        return OneDeviationDecision(reason="model_hash_mismatch")
    if ood:
        return OneDeviationDecision(reason="context_ood")
    if adverse_memory_event:
        return OneDeviationDecision(reason="memory_adverse_event_veto")
    legal = []
    for candidate_id, rank, probability, magnitude in rows:
        rank_value = int(rank)
        p_value = float(probability)
        mu_value = float(magnitude)
        if (
            not isfinite(p_value)
            or not isfinite(mu_value)
            or not 0.0 <= p_value <= 1.0
            or mu_value < 0.0
        ):
            return OneDeviationDecision(reason="invalid_model_output")
        score = p_value * mu_value
        if (
            int(batch_size) + 1
            <= rank_value
            <= int(batch_size) + 32
            and p_value >= float(probability_threshold)
            and score >= float(gain_threshold)
        ):
            legal.append(
                (
                    -score,
                    -p_value,
                    rank_value,
                    str(candidate_id),
                    p_value,
                    mu_value,
                )
            )
    if not legal:
        return OneDeviationDecision(reason="no_candidate_passed_thresholds")
    best = min(legal)
    if not ledger.claim(root_key):
        return OneDeviationDecision(reason="root_intervention_already_used")
    return OneDeviationDecision(
        action_id=f"PROMOTE_{best[3]}",
        promoted_candidate_id=best[3],
        promoted_from_rank=best[2],
        probability_positive=best[4],
        conditional_positive_relative_gain=best[5],
        expected_positive_relative_gain=-best[0],
        abstained=False,
        reason="calibrated_one_deviation",
    )


def _wilson_bound(
    successes: int,
    total: int,
    z: float,
    *,
    upper: bool,
) -> float:
    if total <= 0:
        return 1.0 if upper else 0.0
    n = float(total)
    p = float(successes) / n
    z2 = float(z) ** 2
    center = (p + z2 / (2.0 * n)) / (1.0 + z2 / n)
    radius = (
        float(z)
        * sqrt(
            (p * (1.0 - p) + z2 / (4.0 * n)) / n
        )
        / (1.0 + z2 / n)
    )
    return min(1.0, center + radius) if upper else max(
        0.0, center - radius
    )
