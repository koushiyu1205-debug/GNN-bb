"""Trajectory- and reduced-cost-aware objectives for root dual centers.

Coordinate MSE to an arbitrary final dual is deliberately not the primary
objective.  The main signal asks whether the predicted center ranks observed
future-useful columns ahead under the same early root context.  A set-valued
dual-face loss is only a regularizer because the final RMP may have many
equivalent optimal dual vectors.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import torch
from torch.nn import functional as F


ROOT_DUAL_CENTER_TRAINING_OBJECTIVE = (
    "root_dual_center.counterfactual_route_rc_trajectory.v1"
)


@dataclass(frozen=True)
class DualCenterLossWeights:
    """Loss weights, distinct from any solver/objective cost coefficients."""

    route_trajectory: float = 1.0
    dual_face_regularizer: float = 0.1
    active_column_feasibility: float = 0.05

    def __post_init__(self) -> None:
        values = (
            self.route_trajectory,
            self.dual_face_regularizer,
            self.active_column_feasibility,
        )
        if any(not isfinite(float(value)) or value < 0.0 for value in values):
            raise ValueError("dual-center loss weights must be finite and nonnegative")
        if float(self.route_trajectory) <= 0.0:
            raise ValueError("route trajectory must remain the primary loss")


def reconstructed_dual_center(
    initial_task_duals: torch.Tensor,
    normalized_residual: torch.Tensor,
    *,
    residual_location: torch.Tensor | float,
    residual_scale: torch.Tensor | float,
) -> torch.Tensor:
    """Undo fold-fitted target normalization without hard-coded cost scales."""

    location = torch.as_tensor(
        residual_location,
        dtype=normalized_residual.dtype,
        device=normalized_residual.device,
    )
    scale = torch.as_tensor(
        residual_scale,
        dtype=normalized_residual.dtype,
        device=normalized_residual.device,
    )
    if bool((scale <= 0.0).any()) or not bool(
        torch.isfinite(scale).all()
    ):
        raise ValueError("residual normalization scale must be finite and positive")
    center = initial_task_duals + (
        normalized_residual * scale + location
    )
    if not bool(torch.isfinite(center).all()):
        raise ValueError("reconstructed dual center contains NaN/Inf")
    return center


def counterfactual_route_trajectory_loss(
    predicted_center: torch.Tensor,
    *,
    route_task_incidence: torch.Tensor,
    route_objective: torch.Tensor,
    observed_route_value: torch.Tensor,
    observed_mask: torch.Tensor,
    temperature: float = 1.0,
) -> torch.Tensor:
    """Rank routes by measured future value using center-induced reduced cost.

    ``observed_route_value`` must be materialized from matched trajectories
    (for example bound-gain per measured discovery second).  The loss never
    fabricates values for unobserved routes and never treats them as negatives.
    """

    if route_task_incidence.ndim != 2:
        raise ValueError("route incidence must have shape [route, task]")
    center = predicted_center.reshape(-1)
    objective = route_objective.reshape(-1)
    value = observed_route_value.reshape(-1)
    mask = observed_mask.reshape(-1).bool()
    route_count, task_count = route_task_incidence.shape
    if task_count != center.numel():
        raise ValueError("route incidence task dimension mismatch")
    if not (
        route_count
        == objective.numel()
        == value.numel()
        == mask.numel()
    ):
        raise ValueError("route trajectory tensor length mismatch")
    if int(mask.sum()) < 2:
        return center.sum() * 0.0
    selected_value = value[mask]
    if not bool(torch.isfinite(selected_value).all()):
        raise ValueError("observed route values must be finite")
    tau = float(temperature)
    if not isfinite(tau) or tau <= 0.0:
        raise ValueError("route trajectory temperature must be positive")
    # Higher score means a more negative reduced cost under the predicted
    # task-cover center. Fleet/cut terms stay official and are constant or
    # separately audited at the root discovery boundary.
    predicted_score = (
        route_task_incidence @ center - objective
    )[mask]
    if bool((selected_value < 0.0).any()):
        raise ValueError(
            "observed route value must be nonnegative measured utility"
        )
    value_mass = selected_value.sum()
    if float(value_mass.detach()) <= 0.0:
        return center.sum() * 0.0
    # Direct normalization prevents thousands of observed zero-gain routes
    # from receiving artificial probability mass. Temperature controls only
    # the center-induced ranking sharpness.
    target_probability = selected_value / value_mass
    return -(
        target_probability
        * F.log_softmax(predicted_score / tau, dim=0)
    ).sum()


def set_valued_dual_face_loss(
    predicted_center: torch.Tensor,
    predicted_log_variance: torch.Tensor,
    *,
    admissible_dual_centers: torch.Tensor,
    face_temperature: float = 0.05,
) -> torch.Tensor:
    """Robust heteroscedastic distance to a set of equivalent dual targets."""

    prediction = predicted_center.reshape(-1)
    log_variance = torch.clamp(
        predicted_log_variance.reshape(-1), min=-8.0, max=6.0
    )
    targets = admissible_dual_centers
    if targets.ndim != 2 or targets.shape[1] != prediction.numel():
        raise ValueError(
            "admissible dual centers must have shape [face, task]"
        )
    if targets.shape[0] < 1:
        raise ValueError("dual face target set cannot be empty")
    if not bool(torch.isfinite(targets).all()):
        raise ValueError("dual face targets must be finite")
    tau = float(face_temperature)
    if not isfinite(tau) or tau <= 0.0:
        raise ValueError("dual face temperature must be positive")
    residual = prediction[None, :] - targets
    robust = F.smooth_l1_loss(
        prediction[None, :].expand_as(targets),
        targets,
        reduction="none",
    )
    per_face = (
        torch.exp(-log_variance)[None, :] * robust
        + 0.5 * log_variance[None, :]
    ).mean(dim=1)
    # Normalizing by the face count keeps the zero-distance reference at zero
    # and avoids rewarding duplicated representations of the same dual face.
    return -tau * (
        torch.logsumexp(-per_face / tau, dim=0)
        - torch.log(
            torch.tensor(
                float(targets.shape[0]),
                dtype=targets.dtype,
                device=targets.device,
            )
        )
    )


def active_column_feasibility_hinge(
    predicted_center: torch.Tensor,
    *,
    active_route_task_incidence: torch.Tensor,
    active_route_objective: torch.Tensor,
    official_fleet_dual: float | torch.Tensor,
    tolerance: float = 1.0e-6,
) -> torch.Tensor:
    """Regularize obvious dual infeasibility before sidecar projection."""

    if active_route_task_incidence.ndim != 2:
        raise ValueError(
            "active route incidence must have shape [route, task]"
        )
    center = predicted_center.reshape(-1)
    if active_route_task_incidence.shape[1] != center.numel():
        raise ValueError("active route incidence task dimension mismatch")
    objective = active_route_objective.reshape(-1)
    if objective.numel() != active_route_task_incidence.shape[0]:
        raise ValueError("active route objective length mismatch")
    fleet = torch.as_tensor(
        official_fleet_dual,
        dtype=center.dtype,
        device=center.device,
    )
    violation = (
        active_route_task_incidence @ center
        + fleet
        - objective
        - abs(float(tolerance))
    )
    return F.relu(violation).mean() if violation.numel() else center.sum() * 0.0


def dual_center_trajectory_objective(
    predicted_center: torch.Tensor,
    predicted_log_variance: torch.Tensor,
    *,
    route_task_incidence: torch.Tensor,
    route_objective: torch.Tensor,
    observed_route_value: torch.Tensor,
    observed_mask: torch.Tensor,
    admissible_dual_centers: torch.Tensor,
    active_route_task_incidence: torch.Tensor,
    active_route_objective: torch.Tensor,
    official_fleet_dual: float | torch.Tensor,
    weights: DualCenterLossWeights = DualCenterLossWeights(),
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    route_loss = counterfactual_route_trajectory_loss(
        predicted_center,
        route_task_incidence=route_task_incidence,
        route_objective=route_objective,
        observed_route_value=observed_route_value,
        observed_mask=observed_mask,
    )
    face_loss = set_valued_dual_face_loss(
        predicted_center,
        predicted_log_variance,
        admissible_dual_centers=admissible_dual_centers,
    )
    feasibility_loss = active_column_feasibility_hinge(
        predicted_center,
        active_route_task_incidence=active_route_task_incidence,
        active_route_objective=active_route_objective,
        official_fleet_dual=official_fleet_dual,
    )
    components = {
        "route_trajectory": route_loss,
        "dual_face_regularizer": face_loss,
        "active_column_feasibility": feasibility_loss,
    }
    total = (
        float(weights.route_trajectory) * route_loss
        + float(weights.dual_face_regularizer) * face_loss
        + float(weights.active_column_feasibility) * feasibility_loss
    )
    return total, components
