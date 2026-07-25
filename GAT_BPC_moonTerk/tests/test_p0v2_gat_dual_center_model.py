from __future__ import annotations

import torch

from lunar_ice_bpc.guidance.dual_center_model import (
    ROOT_DUAL_CENTER_MODEL_KINDS,
    build_root_dual_center_model,
)
from lunar_ice_bpc.guidance.dual_center_training import (
    active_column_feasibility_hinge,
    counterfactual_route_trajectory_loss,
    reconstructed_dual_center,
    set_valued_dual_face_loss,
)


def _model_inputs() -> dict[str, torch.Tensor]:
    return {
        "node_features": torch.tensor(
            [
                [1.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.2, 0.1, 0.3],
                [0.0, 1.0, 0.8, 0.2, 0.4],
            ]
        ),
        "edge_index": torch.tensor(
            [[0, 1, 0, 2], [1, 0, 2, 0]], dtype=torch.long
        ),
        "edge_features": torch.tensor(
            [
                [0.1, 0.2],
                [0.1, 0.2],
                [0.3, 0.4],
                [0.3, 0.4],
            ]
        ),
        "task_node_indices": torch.tensor([1, 2], dtype=torch.long),
        "resource_context": torch.tensor([1.0, 2.0, 3.0, -0.1]),
    }


def test_root_dual_center_model_ladder_is_small_and_shape_stable() -> None:
    inputs = _model_inputs()
    for kind in ROOT_DUAL_CENTER_MODEL_KINDS:
        model = build_root_dual_center_model(
            kind,
            node_input_dim=5,
            edge_input_dim=2,
        )
        output = model(**inputs)
        assert output["normalized_residual"].shape == (2,)
        assert output["log_variance"].shape == (2,)
        assert bool(torch.isfinite(output["normalized_residual"]).all())
        assert bool(torch.isfinite(output["log_variance"]).all())
        assert sum(parameter.numel() for parameter in model.parameters()) < 100_000


def test_route_trajectory_loss_prefers_center_exposing_high_value_route() -> None:
    incidence = torch.eye(2)
    objective = torch.zeros(2)
    values = torch.tensor([3.0, 0.0])
    observed = torch.tensor([True, True])
    good = counterfactual_route_trajectory_loss(
        torch.tensor([2.0, 0.0]),
        route_task_incidence=incidence,
        route_objective=objective,
        observed_route_value=values,
        observed_mask=observed,
    )
    bad = counterfactual_route_trajectory_loss(
        torch.tensor([0.0, 2.0]),
        route_task_incidence=incidence,
        route_objective=objective,
        observed_route_value=values,
        observed_mask=observed,
    )
    assert float(good) < float(bad)


def test_unobserved_route_is_not_implicitly_used_as_negative() -> None:
    center = torch.tensor([1.0, 0.0], requires_grad=True)
    loss = counterfactual_route_trajectory_loss(
        center,
        route_task_incidence=torch.eye(2),
        route_objective=torch.zeros(2),
        observed_route_value=torch.tensor([1.0, -1000.0]),
        observed_mask=torch.tensor([True, False]),
    )
    assert float(loss.detach()) == 0.0


def test_set_valued_face_loss_and_reconstruction_are_finite() -> None:
    center = reconstructed_dual_center(
        torch.tensor([0.1, 0.2]),
        torch.tensor([1.0, -1.0]),
        residual_location=0.0,
        residual_scale=0.05,
    )
    assert torch.allclose(center, torch.tensor([0.15, 0.15]))
    loss = set_valued_dual_face_loss(
        center,
        torch.zeros(2),
        admissible_dual_centers=torch.tensor(
            [[0.15, 0.15], [0.14, 0.16]]
        ),
    )
    assert bool(torch.isfinite(loss))


def test_active_column_hinge_uses_rmp_dual_feasibility_sign() -> None:
    incidence = torch.tensor([[1.0, 1.0]])
    objective = torch.tensor([1.0])
    feasible = active_column_feasibility_hinge(
        torch.tensor([0.4, 0.4]),
        active_route_task_incidence=incidence,
        active_route_objective=objective,
        official_fleet_dual=0.0,
    )
    infeasible = active_column_feasibility_hinge(
        torch.tensor([0.8, 0.8]),
        active_route_task_incidence=incidence,
        active_route_objective=objective,
        official_fleet_dual=0.0,
    )
    assert float(feasible) == 0.0
    assert float(infeasible) > 0.0
