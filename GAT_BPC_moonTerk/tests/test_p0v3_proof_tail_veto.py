from __future__ import annotations

import os
import subprocess
import sys

import pytest

from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.guidance.proof_tail_veto_features import (
    build_harvest_dynamics_features,
    build_proof_tail_veto_features,
    proof_tail_veto_feature_dimensions,
)


def _snapshot(data, *, strikes: int = 2) -> dict:
    return {
        "instance_content_hash": data.instance_content_hash,
        "state_hash": "test-state",
        "source_pass_strategy": "proof_only",
        "required_sparse_harvest_strikes": 2,
        "sparse_harvest_strike_count": strikes,
        "round": 7,
        "active_column_count": 0,
        "active_column_ids": [],
        "effective_harvest_target": 16,
        "node_lp_bound": 2.5,
        "true_duals": {
            "fleet_dual": -0.25,
            "task_duals": {
                task_id: 0.1 for task_id in data.task_ids
            },
        },
        "rmp_primal": [],
        "trajectory_features": {
            "previous_added_column_count": 3,
            "previous_harvest_column_count": 3,
            "previous_harvest_processed_labels": 10000,
            "previous_best_true_rc": -1.0e-4,
            "dual_l1_delta_from_previous": 0.2,
            "dual_linf_delta_from_previous": 0.05,
            "node_lp_bound_delta": 0.01,
            "rmp_primal_nonzero_count": 0,
            "rmp_primal_fractional_count": 0,
        },
    }


def test_features_require_the_exact_two_strike_pre_call_state() -> None:
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    catalog = {
        "instance_content_hash": data.instance_content_hash,
        "columns": {},
    }
    features = build_proof_tail_veto_features(
        data,
        _snapshot(data),
        column_catalog=catalog,
    )
    assert features.state_hash == "test-state"
    assert len(features.node_features[0]) == (
        proof_tail_veto_feature_dimensions()[0]
    )
    assert len(features.edge_features[0]) == (
        proof_tail_veto_feature_dimensions()[1]
    )
    assert len(features.global_features) == (
        proof_tail_veto_feature_dimensions()[2]
    )
    with pytest.raises(ValueError, match="two-strike"):
        build_proof_tail_veto_features(
            data,
            _snapshot(data, strikes=0),
            column_catalog=catalog,
        )
    harvest_snapshot = {
        **_snapshot(data, strikes=0),
        "source_pass_strategy": "harvest_then_proof",
    }
    harvest_features = build_harvest_dynamics_features(
        data,
        harvest_snapshot,
        column_catalog=catalog,
    )
    assert harvest_features.state_hash == "test-state"


def test_framework_free_feature_gate_does_not_import_torch() -> None:
    root = os.path.dirname(os.path.dirname(__file__))
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import lunar_ice_bpc.guidance.proof_tail_veto_features; "
                "assert 'torch' not in sys.modules"
            ),
        ],
        env={**os.environ, "PYTHONPATH": os.path.join(root, "src")},
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_model_ladder_shapes_and_selective_loss_backpropagates() -> None:
    torch = pytest.importorskip("torch")
    from lunar_ice_bpc.guidance.proof_tail_veto_model import (
        PROOF_TAIL_VETO_MODEL_LADDER,
        ProofTailVetoModel,
        harvest_dynamics_loss,
        proof_tail_veto_loss,
    )

    node_dim, edge_dim, global_dim = (
        proof_tail_veto_feature_dimensions()
    )
    common = {
        "node_features": torch.randn(6, node_dim),
        "edge_index": torch.tensor(
            [[0, 1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 0]],
            dtype=torch.long,
        ),
        "edge_features": torch.randn(6, edge_dim),
        "global_features": torch.randn(global_dim),
    }
    for kind in PROOF_TAIL_VETO_MODEL_LADDER:
        model = ProofTailVetoModel(
            kind=kind,
            node_input_dim=node_dim,
            edge_input_dim=edge_dim,
            global_input_dim=global_dim,
        )
        output = model(**common)
        assert output["veto_probability"].shape == ()
        assert (
            0.0
            <= float(output["veto_probability"].detach())
            <= 1.0
        )
        losses = proof_tail_veto_loss(
            output,
            harvest_log_cost=torch.tensor(1.0),
            proof_log_cost=torch.tensor(1.2),
            instance_weight=torch.tensor(1.0),
            raw_advantage_sec=torch.tensor(0.5),
            deadband_sec=torch.tensor(0.05),
            veto_target=torch.tensor(1.0),
        )
        assert {
            "total",
            "cost",
            "advantage",
            "ranking",
            "selective_classification",
            "expected_regret",
        } == set(losses)
        losses["total"].backward()
        assert any(
            parameter.grad is not None
            for parameter in model.parameters()
        )
        model.zero_grad(set_to_none=True)
        dynamics = harvest_dynamics_loss(
            model(**common),
            yield_fraction=torch.tensor(0.25),
            added_fraction=torch.tensor(0.2),
            best_rc_log_magnitude=torch.tensor(2.0),
            log_wall_sec=torch.tensor(0.1),
            sparse_target=torch.tensor(1.0),
            sparse_positive_weight=torch.tensor(3.0),
            instance_weight=torch.tensor(1.0),
        )
        assert set(dynamics) == {
            "total",
            "yield",
            "added",
            "best_rc",
            "wall",
            "sparse",
        }
        dynamics["total"].backward()
