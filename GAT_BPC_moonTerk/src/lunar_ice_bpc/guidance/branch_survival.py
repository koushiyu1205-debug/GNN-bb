"""Experimental Ryan--Foster child-survival ranker outside the P0 V3 freeze.

The frozen P0 V3 control still owns the legal top-3 shortlist and every exact
decision.  This module predicts only the two child closure-time distributions
for each already-legal pair.  It deliberately has no scalar legacy
``branch_cost`` output.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, isfinite
from typing import Any

import torch
from torch import nn

from lunar_ice_bpc.guidance.models import (
    EdgeAttentionLayer,
    symmetric_pair_features,
)
from lunar_ice_bpc.guidance.survival_losses import (
    discrete_time_survival_nll,
)
from lunar_ice_bpc.guidance.branch_e2e_costs import (
    BRANCH_GUIDED_E2E_COST_SEMANTICS_V1,
)


BRANCH_SURVIVAL_MODEL_LADDER = (
    "linear",
    "mlp2x32",
    "gat1x32x1",
    "gat2x32x2",
    "gat3x64x4",
)
BRANCH_CHILD_SURVIVAL_RMST_OBJECTIVE_V1 = (
    "branch_child_survival_rmst.v1"
)
BRANCH_E2E_REGRET_LISTWISE_OBJECTIVE_V2 = (
    "branch_e2e_regret_listwise_with_child_survival_aux.v2"
)
BRANCH_SURVIVAL_ARCHITECTURE_VERSION = (
    "lunar_ice_bpc.branch_survival_ranker.v2"
)
BRANCH_SURVIVAL_CHECKPOINT_SCHEMA_V2 = (
    "lunar_ice_bpc.branch_survival_checkpoint.v2"
)
BRANCH_PAIR_CONTEXT_SCHEMA_V1 = (
    "fractionality.same_fraction.log1p_support.normalized_pool_imbalance.v1"
)
SYNTHETIC_POLAR_GRID_DOMAIN = "synthetic_polar_resource_grid_v1"
REAL_MAP_SP50_DOMAIN = "real_lunar_south_pole_sp50_benchmark_v1"
BRANCH_INSTANCE_GENERATOR_DOMAINS = (
    SYNTHETIC_POLAR_GRID_DOMAIN,
    REAL_MAP_SP50_DOMAIN,
)
BRANCH_NODE_FEATURE_SCHEMA_V2 = (
    "static17.cover_dual.log_scale_memory_horizon.pricing_mode2."
    "cut_dual_signed_abs.parent_same_diff_degree.log_depth."
    "normalized_incumbent_gap.incumbent_available."
    "log_processed_open_global_columns.v2"
)
SURVIVAL_HAZARD_BINS = 4


def restricted_mean_survival_fraction(
    hazard_logits: torch.Tensor,
) -> torch.Tensor:
    """Return discrete restricted mean survival in horizon fractions."""

    if hazard_logits.ndim < 2:
        raise ValueError("hazard logits must end in a bin axis")
    bin_count = int(hazard_logits.shape[-1])
    if bin_count <= 0:
        raise ValueError("hazard logits require at least one bin")
    survival_probability = torch.sigmoid(-hazard_logits)
    survival_before = torch.cat(
        (
            torch.ones_like(survival_probability[..., :1]),
            torch.cumprod(
                survival_probability[..., :-1],
                dim=-1,
            ),
        ),
        dim=-1,
    )
    return survival_before.mean(dim=-1)


def validate_branch_survival_row(row: dict[str, Any]) -> None:
    """Reject legacy costs, incomplete universes, and malformed censoring."""

    if str(row.get("instance_generator_domain") or "") not in (
        BRANCH_INSTANCE_GENERATOR_DOMAINS
    ):
        raise ValueError(
            "branch row has no recognized instance-generator domain"
        )
    if str(row.get("branch_training_objective") or "") != (
        BRANCH_CHILD_SURVIVAL_RMST_OBJECTIVE_V1
    ):
        raise ValueError("branch child-survival objective ID mismatch")
    if str(row.get("branch_primary_training_objective") or "") != (
        BRANCH_E2E_REGRET_LISTWISE_OBJECTIVE_V2
    ):
        raise ValueError("branch E2E primary objective ID mismatch")
    node_phase = str(row.get("node_phase") or "")
    if node_phase not in {
        "root_fractional_exact_node",
        "deep_fractional_exact_node",
    }:
        raise ValueError(
            "formal branch survival requires an exact root/deep state"
        )
    if (
        node_phase == "deep_fractional_exact_node"
        and str(row.get("parent_snapshot_origin") or "")
        != "exact_p0_deep_parent_snapshot"
    ):
        raise ValueError(
            "deep branch row requires an exact node-specific P0 snapshot"
        )
    forbidden = (
        "branch_cost",
        "normalized_branch_cost",
        "branch_observed_lower_bounds",
        "branch_exact_mask",
        "exact_branch_cost",
    )
    present = [key for key in forbidden if row.get(key) is not None]
    if present:
        raise ValueError(
            f"legacy scalar branch target fields rejected: {present}"
        )
    pairs = list(row.get("branch_pairs") or ())
    contexts = list(row.get("branch_context") or ())
    times = list(row.get("branch_child_observed_time_fractions") or ())
    events = list(row.get("branch_child_event_observed") or ())
    masks = list(row.get("branch_child_observed_mask") or ())
    if not pairs or not (
        len(pairs) == len(contexts) == len(times) == len(events) == len(masks)
    ):
        raise ValueError("branch candidate tensor row count mismatch")
    if len(pairs) != 3:
        raise ValueError("formal branch rows require the unchanged P0 top-3")
    for index in range(len(pairs)):
        if len(pairs[index]) != 2 or len(contexts[index]) != 4:
            raise ValueError("branch pair/context shape mismatch")
        if not (
            len(times[index]) == len(events[index]) == len(masks[index]) == 2
        ):
            raise ValueError("each branch pair requires SAME and DIFFERENT rows")
        for observed_time, observed in zip(times[index], masks[index], strict=True):
            if bool(observed) and not (0.0 < float(observed_time) <= 1.0):
                raise ValueError(
                    "observed child time fractions must lie in (0, 1]"
                )
    if int(row.get("guidance_branch_pair_drop_count") or 0) != 0:
        raise ValueError("branch training row reports a dropped legal pair")
    if (
        row.get("legal_branch_shortlist_hash_before_sort")
        != row.get("legal_branch_shortlist_hash_after_sort")
    ):
        raise ValueError("branch shortlist universe changed")
    preferences = list(
        row.get("branch_e2e_trusted_pairwise_preferences") or ()
    )
    directed = set()
    for preference in preferences:
        if (
            not isinstance(preference, (list, tuple))
            or len(preference) != 2
        ):
            raise ValueError(
                "E2E pairwise preference must be [winner, loser]"
            )
        winner, loser = map(int, preference)
        if (
            winner == loser
            or winner not in {0, 1, 2}
            or loser not in {0, 1, 2}
            or (winner, loser) in directed
            or (loser, winner) in directed
        ):
            raise ValueError(
                "invalid or contradictory E2E preference"
            )
        directed.add((winner, loser))
    gold_rank = row.get("branch_e2e_gold_rank_index")
    if gold_rank is not None:
        walls = row.get("branch_e2e_wall_sec_by_rank") or {}
        p0_wall = row.get("branch_e2e_p0_control_wall_sec")
        overhead = row.get(
            "branch_guidance_lifecycle_overhead_sec"
        )
        net_gain = row.get("branch_e2e_gold_net_gain_sec")
        if (
            str(row.get("branch_e2e_cost_semantics") or "")
            != BRANCH_GUIDED_E2E_COST_SEMANTICS_V1
            or set(walls) != {"0", "1", "2"}
            or p0_wall is None
            or overhead is None
            or net_gain is None
            or not isfinite(float(p0_wall))
            or float(p0_wall) <= 0.0
            or not isfinite(float(overhead))
            or float(overhead) < 0.0
            or any(
                not isfinite(float(value)) or float(value) <= 0.0
                for value in walls.values()
            )
        ):
            raise ValueError("branch guided E2E cost semantics invalid")
        expected_rank = min(
            range(3),
            key=lambda rank: (float(walls[str(rank)]), rank),
        )
        expected_gain = float(p0_wall) - float(
            walls[str(expected_rank)]
        )
        if (
            int(gold_rank) != expected_rank
            or not isclose(
                float(net_gain),
                expected_gain,
                rel_tol=0.0,
                abs_tol=1.0e-6,
            )
        ):
            raise ValueError("branch guided E2E label is inconsistent")
    elif any(
        row.get(key) is not None
        for key in (
            "branch_e2e_gold_net_gain_sec",
            "branch_e2e_p0_control_wall_sec",
            "branch_guidance_lifecycle_overhead_sec",
            "branch_e2e_cost_semantics",
            "branch_e2e_wall_sec_by_rank",
        )
    ):
        raise ValueError("branch E2E costs cannot be supplied without gold rank")


def branch_survival_losses(
    output: dict[str, torch.Tensor],
    *,
    observed_time_fractions: torch.Tensor,
    event_observed: torch.Tensor,
    observed_mask: torch.Tensor,
    e2e_gold_rank_index: torch.Tensor | None = None,
    e2e_wall_sec_by_rank: torch.Tensor | None = None,
    e2e_p0_control_wall_sec: torch.Tensor | None = None,
    e2e_trusted_pairwise_preferences: torch.Tensor | None = None,
) -> dict[str, torch.Tensor]:
    """Sparse action-aligned E2E loss plus child-survival auxiliary loss."""

    hazard = output["branch_child_hazard_logits"]
    expected_shape = hazard.shape[:2]
    if (
        observed_time_fractions.shape != expected_shape
        or event_observed.shape != expected_shape
        or observed_mask.shape != expected_shape
    ):
        raise ValueError(
            "branch child observations must have shape [candidate, 2]"
        )
    flat_hazard = hazard.reshape(-1, hazard.shape[-1])
    flat_times = observed_time_fractions.reshape(-1)
    flat_events = event_observed.reshape(-1)
    selected = torch.nonzero(
        observed_mask.reshape(-1).bool(),
        as_tuple=False,
    ).reshape(-1)
    losses = {
        "branch_child_survival_nll": discrete_time_survival_nll(
            flat_hazard,
            selected,
            flat_times[selected],
            flat_events[selected],
        )
    }
    if e2e_gold_rank_index is not None:
        target = e2e_gold_rank_index.reshape(-1).long()
        if target.numel() != 1:
            raise ValueError("E2E gold rank index must be scalar")
        if int(target.item()) < 0 or int(target.item()) >= int(
            output["branch_scores"].numel()
        ):
            raise ValueError("E2E gold rank index is out of range")
        losses["branch_e2e_gold_listwise"] = nn.functional.cross_entropy(
            output["branch_scores"].reshape(1, -1),
            target,
        )
        if e2e_wall_sec_by_rank is None:
            raise ValueError(
                "E2E gold requires matched wall seconds by rank"
            )
        walls = e2e_wall_sec_by_rank.reshape(-1).to(
            output["branch_scores"]
        )
        if (
            walls.numel() != output["branch_scores"].numel()
            or not bool(torch.isfinite(walls).all())
            or bool((walls <= 0.0).any())
        ):
            raise ValueError(
                "matched E2E wall seconds must be finite and positive"
            )
        if e2e_p0_control_wall_sec is None:
            p0_control_wall = walls[0]
        else:
            p0_control_values = e2e_p0_control_wall_sec.reshape(-1).to(
                walls
            )
            if (
                p0_control_values.numel() != 1
                or not bool(torch.isfinite(p0_control_values).all())
                or bool((p0_control_values <= 0.0).any())
            ):
                raise ValueError(
                    "P0 control wall seconds must be scalar/finite/positive"
                )
            p0_control_wall = p0_control_values[0]
        normalized_regret = (
            walls - torch.min(walls)
        ) / p0_control_wall.clamp_min(1.0e-8)
        selection_probability = torch.softmax(
            output["branch_scores"].reshape(-1),
            dim=0,
        )
        losses["branch_e2e_expected_normalized_regret"] = torch.sum(
            selection_probability * normalized_regret
        )
    elif (
        e2e_wall_sec_by_rank is not None
        or e2e_p0_control_wall_sec is not None
    ):
        raise ValueError("E2E costs cannot be supplied without gold rank")
    if (
        e2e_trusted_pairwise_preferences is not None
        and e2e_trusted_pairwise_preferences.numel() > 0
    ):
        preferences = (
            e2e_trusted_pairwise_preferences.reshape(-1, 2).long()
        )
        scores = output["branch_scores"].reshape(-1)
        if (
            bool((preferences < 0).any())
            or bool((preferences >= scores.numel()).any())
            or bool(
                (
                    preferences[:, 0] == preferences[:, 1]
                ).any()
            )
        ):
            raise ValueError("E2E pairwise preference index invalid")
        winner_scores = scores[preferences[:, 0]]
        loser_scores = scores[preferences[:, 1]]
        losses["branch_e2e_trusted_censored_pairwise"] = (
            nn.functional.softplus(
                loser_scores - winner_scores
            ).mean()
        )
    return losses


@dataclass(frozen=True)
class BranchSurvivalDimensions:
    node_input_dim: int
    edge_input_dim: int
    pair_context_dim: int = 4


class BranchSurvivalRanker(nn.Module):
    """Smallest-first graph encoder with one child-hazard head."""

    def __init__(
        self,
        dimensions: BranchSurvivalDimensions,
        *,
        kind: str,
    ) -> None:
        super().__init__()
        if kind not in BRANCH_SURVIVAL_MODEL_LADDER:
            raise ValueError(f"unsupported branch model kind {kind!r}")
        self.kind = str(kind)
        self.node_input_dim = int(dimensions.node_input_dim)
        self.edge_input_dim = int(dimensions.edge_input_dim)
        self.pair_context_dim = int(dimensions.pair_context_dim)
        hidden_dim, layer_count, head_count = _model_shape(kind)
        if kind == "linear":
            self.node_encoder = nn.Identity()
            self.edge_encoder = nn.Identity()
            encoded_dim = self.node_input_dim
            encoded_edge_dim = self.edge_input_dim
        else:
            self.node_encoder = nn.Sequential(
                nn.Linear(self.node_input_dim, hidden_dim),
                nn.ReLU(),
            )
            self.edge_encoder = nn.Sequential(
                nn.Linear(self.edge_input_dim, hidden_dim),
                nn.ReLU(),
            )
            encoded_dim = hidden_dim
            encoded_edge_dim = hidden_dim
        self.attention_layers = nn.ModuleList(
            EdgeAttentionLayer(
                encoded_dim,
                encoded_edge_dim,
                head_count,
            )
            for _ in range(layer_count)
        )
        pair_input_dim = encoded_dim * 4 + self.pair_context_dim
        self.branch_child_hazard_head = _multi_output_head(
            kind,
            pair_input_dim,
            hidden_dim,
            2 * SURVIVAL_HAZARD_BINS,
        )
        self.branch_e2e_score_head = _multi_output_head(
            kind,
            pair_input_dim,
            hidden_dim,
            1,
        )

    def forward(
        self,
        *,
        node_features: torch.Tensor,
        edge_index: torch.Tensor,
        edge_features: torch.Tensor,
        branch_pairs: torch.Tensor,
        branch_context: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        node_embedding = self.node_encoder(node_features)
        edge_embedding = self.edge_encoder(edge_features)
        for layer in self.attention_layers:
            node_embedding = layer(
                node_embedding,
                edge_index,
                edge_embedding,
            )
        global_embedding = node_embedding.mean(dim=0)
        global_rows = global_embedding.expand(branch_pairs.shape[0], -1)
        pair_features = symmetric_pair_features(
            node_embedding[branch_pairs[:, 0]],
            node_embedding[branch_pairs[:, 1]],
            global_rows,
            branch_context,
        )
        child_hazard_logits = self.branch_child_hazard_head(
            pair_features
        ).reshape(
            branch_pairs.shape[0],
            2,
            SURVIVAL_HAZARD_BINS,
        )
        child_rmst = restricted_mean_survival_fraction(
            child_hazard_logits
        )
        pair_rmst = child_rmst.sum(dim=-1)
        e2e_scores = self.branch_e2e_score_head(
            pair_features
        ).reshape(-1)
        return {
            "branch_child_hazard_logits": child_hazard_logits,
            "branch_child_rmst_fractions": child_rmst,
            "branch_pair_rmst_fractions": pair_rmst,
            "branch_survival_aux_scores": -pair_rmst,
            "branch_scores": e2e_scores,
            "node_embedding": node_embedding,
            "global_embedding": global_embedding,
        }


def build_branch_survival_model(
    kind: str,
    *,
    node_input_dim: int,
    edge_input_dim: int,
    pair_context_dim: int = 4,
) -> BranchSurvivalRanker:
    return BranchSurvivalRanker(
        BranchSurvivalDimensions(
            node_input_dim=int(node_input_dim),
            edge_input_dim=int(edge_input_dim),
            pair_context_dim=int(pair_context_dim),
        ),
        kind=str(kind),
    )


def branch_survival_checkpoint_payload(
    model: BranchSurvivalRanker,
    *,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": BRANCH_SURVIVAL_CHECKPOINT_SCHEMA_V2,
        "model_architecture_version": (
            BRANCH_SURVIVAL_ARCHITECTURE_VERSION
        ),
        "model_kind": model.kind,
        "node_input_dim": model.node_input_dim,
        "edge_input_dim": model.edge_input_dim,
        "pair_context_dim": model.pair_context_dim,
        "metadata": dict(metadata),
        "state_dict": model.state_dict(),
    }


def _model_shape(kind: str) -> tuple[int, int, int]:
    return {
        "linear": (0, 0, 0),
        "mlp2x32": (32, 0, 0),
        "gat1x32x1": (32, 1, 1),
        "gat2x32x2": (32, 2, 2),
        "gat3x64x4": (64, 3, 4),
    }[kind]


def _multi_output_head(
    kind: str,
    input_dim: int,
    hidden_dim: int,
    output_dim: int,
) -> nn.Module:
    if kind == "linear":
        return nn.Linear(input_dim, output_dim)
    return nn.Sequential(
        nn.Linear(input_dim, hidden_dim),
        nn.ReLU(),
        nn.Linear(hidden_dim, output_dim),
    )
