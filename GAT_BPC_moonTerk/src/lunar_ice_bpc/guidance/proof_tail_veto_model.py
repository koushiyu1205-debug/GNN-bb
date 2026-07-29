"""Smallest-first model ladder for the P0 V3 one-shot proof-tail veto."""

from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F

from lunar_ice_bpc.guidance.models import EdgeAttentionLayer


PROOF_TAIL_VETO_MODEL_SCHEMA = (
    "lunar_ice_bpc.p0v3_proof_tail_veto_model.v1"
)
PROOF_TAIL_VETO_MODEL_LADDER = (
    "linear",
    "mlp2x32",
    "gat1x32x1",
)


class ProofTailVetoModel(nn.Module):
    """Predict log cost-to-closure for harvest and proof from one graph state."""

    def __init__(
        self,
        *,
        kind: str,
        node_input_dim: int,
        edge_input_dim: int,
        global_input_dim: int,
    ) -> None:
        super().__init__()
        if kind not in PROOF_TAIL_VETO_MODEL_LADDER:
            raise ValueError(f"unsupported proof-tail model kind {kind!r}")
        self.kind = str(kind)
        self.node_input_dim = int(node_input_dim)
        self.edge_input_dim = int(edge_input_dim)
        self.global_input_dim = int(global_input_dim)
        hidden = 32
        if self.kind == "linear":
            self.node_encoder = nn.Identity()
            self.edge_encoder = nn.Identity()
            encoded_dim = self.node_input_dim
            self.attention = nn.ModuleList()
            head_input = 2 * encoded_dim + self.global_input_dim
            self.cost_head = nn.Linear(head_input, 2)
            self.veto_head = nn.Linear(head_input, 1)
            self.harvest_dynamics_head = nn.Linear(
                head_input,
                5,
            )
        else:
            self.node_encoder = nn.Sequential(
                nn.Linear(self.node_input_dim, hidden),
                nn.ReLU(),
                nn.Linear(hidden, hidden),
                nn.ReLU(),
            )
            self.edge_encoder = nn.Sequential(
                nn.Linear(self.edge_input_dim, hidden),
                nn.ReLU(),
            )
            encoded_dim = hidden
            self.attention = nn.ModuleList(
                [EdgeAttentionLayer(hidden, hidden, heads=1)]
                if self.kind == "gat1x32x1"
                else []
            )
            head_input = 2 * encoded_dim + self.global_input_dim
            self.cost_head = nn.Sequential(
                nn.Linear(head_input, hidden),
                nn.ReLU(),
                nn.Linear(hidden, 2),
            )
            self.veto_head = nn.Sequential(
                nn.Linear(head_input, hidden),
                nn.ReLU(),
                nn.Linear(hidden, 1),
            )
            self.harvest_dynamics_head = nn.Sequential(
                nn.Linear(head_input, hidden),
                nn.ReLU(),
                nn.Linear(hidden, 5),
            )

    def forward(
        self,
        *,
        node_features: torch.Tensor,
        edge_index: torch.Tensor,
        edge_features: torch.Tensor,
        global_features: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        node_embedding = self.node_encoder(node_features)
        edge_embedding = self.edge_encoder(edge_features)
        for layer in self.attention:
            node_embedding = layer(
                node_embedding,
                edge_index,
                edge_embedding,
            )
        graph_embedding = torch.cat(
            (
                node_embedding.mean(dim=0),
                node_embedding.amax(dim=0),
                global_features,
            ),
            dim=-1,
        )
        log_costs = F.softplus(self.cost_head(graph_embedding))
        veto_logit = self.veto_head(graph_embedding).squeeze(-1)
        raw_dynamics = self.harvest_dynamics_head(
            graph_embedding
        )
        return {
            "harvest_log_cost": log_costs[0],
            "proof_log_cost": log_costs[1],
            "log_advantage_proof_minus_harvest": (
                log_costs[1] - log_costs[0]
            ),
            "veto_logit": veto_logit,
            "veto_probability": torch.sigmoid(veto_logit),
            "harvest_yield_fraction": torch.sigmoid(
                raw_dynamics[0]
            ),
            "harvest_added_fraction": torch.sigmoid(
                raw_dynamics[1]
            ),
            "harvest_best_rc_log_magnitude": F.softplus(
                raw_dynamics[2]
            ),
            "harvest_log_wall_sec": F.softplus(
                raw_dynamics[3]
            ),
            "harvest_sparse_logit": raw_dynamics[4],
            "harvest_sparse_probability": torch.sigmoid(
                raw_dynamics[4]
            ),
            "graph_embedding": graph_embedding,
        }


def proof_tail_veto_loss(
    output: dict[str, torch.Tensor],
    *,
    harvest_log_cost: torch.Tensor,
    proof_log_cost: torch.Tensor,
    instance_weight: torch.Tensor,
    raw_advantage_sec: torch.Tensor,
    deadband_sec: torch.Tensor,
    veto_target: torch.Tensor,
) -> dict[str, torch.Tensor]:
    predicted = torch.stack(
        (
            output["harvest_log_cost"],
            output["proof_log_cost"],
        )
    )
    target = torch.stack((harvest_log_cost, proof_log_cost))
    cost_loss = F.smooth_l1_loss(
        predicted,
        target,
        reduction="mean",
    )
    predicted_advantage = (
        output["log_advantage_proof_minus_harvest"]
    )
    target_advantage = proof_log_cost - harvest_log_cost
    advantage_loss = F.smooth_l1_loss(
        predicted_advantage,
        target_advantage,
        reduction="mean",
    )
    comparable = torch.abs(raw_advantage_sec) > deadband_sec
    if bool(comparable):
        direction = torch.sign(raw_advantage_sec)
        regret_weight = 1.0 + torch.log1p(
            torch.abs(raw_advantage_sec)
        )
        ranking_loss = (
            F.softplus(-direction * predicted_advantage)
            * regret_weight
        )
    else:
        ranking_loss = predicted_advantage.square()
    classification_weight = 1.0 + torch.log1p(
        torch.abs(raw_advantage_sec)
    )
    selective_classification_loss = (
        F.binary_cross_entropy_with_logits(
            output["veto_logit"],
            veto_target,
            reduction="mean",
        )
        * classification_weight
    )
    veto_probability = output["veto_probability"]
    false_veto_regret = torch.relu(-raw_advantage_sec)
    missed_veto_regret = torch.relu(
        raw_advantage_sec - deadband_sec
    )
    expected_regret_loss = (
        veto_probability * false_veto_regret
        + (1.0 - veto_probability) * missed_veto_regret
    )
    total = instance_weight * (
        cost_loss
        + advantage_loss
        + ranking_loss
        + selective_classification_loss
        + expected_regret_loss
    )
    return {
        "total": total,
        "cost": instance_weight * cost_loss,
        "advantage": instance_weight * advantage_loss,
        "ranking": instance_weight * ranking_loss,
        "selective_classification": (
            instance_weight * selective_classification_loss
        ),
        "expected_regret": (
            instance_weight * expected_regret_loss
        ),
    }


def harvest_dynamics_loss(
    output: dict[str, torch.Tensor],
    *,
    yield_fraction: torch.Tensor,
    added_fraction: torch.Tensor,
    best_rc_log_magnitude: torch.Tensor,
    log_wall_sec: torch.Tensor,
    sparse_target: torch.Tensor,
    sparse_positive_weight: torch.Tensor,
    instance_weight: torch.Tensor,
) -> dict[str, torch.Tensor]:
    """Dense auxiliary objective observed after each bounded harvest."""

    components = {
        "yield": F.smooth_l1_loss(
            output["harvest_yield_fraction"],
            yield_fraction,
            reduction="mean",
        ),
        "added": F.smooth_l1_loss(
            output["harvest_added_fraction"],
            added_fraction,
            reduction="mean",
        ),
        "best_rc": F.smooth_l1_loss(
            output["harvest_best_rc_log_magnitude"],
            best_rc_log_magnitude,
            reduction="mean",
        ),
        "wall": F.smooth_l1_loss(
            output["harvest_log_wall_sec"],
            log_wall_sec,
            reduction="mean",
        ),
        "sparse": (
            F.binary_cross_entropy_with_logits(
                output["harvest_sparse_logit"],
                sparse_target,
                reduction="mean",
            )
            * torch.where(
                sparse_target > 0.5,
                sparse_positive_weight,
                torch.ones_like(sparse_positive_weight),
            )
        ),
    }
    weighted_total = (
        components["yield"]
        + components["added"]
        + 0.25 * components["best_rc"]
        + 0.25 * components["wall"]
        + 0.5 * components["sparse"]
    )
    return {
        "total": instance_weight * weighted_total,
        **{
            key: instance_weight * value
            for key, value in components.items()
        },
    }
