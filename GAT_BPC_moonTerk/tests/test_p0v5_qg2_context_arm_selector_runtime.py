from __future__ import annotations

from copy import deepcopy

import pytest
import torch

from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
    QG2_CONTEXT_FEATURES,
)
from lunar_ice_bpc.guidance.qg2_context_arm_selector import (
    QG2_CONTEXT_ARM_SELECTOR_ARMS,
    QG2_CONTEXT_ARM_SELECTOR_CHECKPOINT_V1,
    QG2ContextArmPrediction,
    QG2ContextArmSelector,
    choose_qg2_secondary_arm,
    load_qg2_context_arm_selector,
    predict_qg2_context_arms,
    qg2_context_arm_is_ood,
)


def _checkpoint(model: QG2ContextArmSelector) -> dict:
    dimension = len(QG2_CONTEXT_FEATURES)
    return {
        "schema_version": QG2_CONTEXT_ARM_SELECTOR_CHECKPOINT_V1,
        "arms": list(QG2_CONTEXT_ARM_SELECTOR_ARMS),
        "feature_dimension": dimension,
        "normalization": {
            "mean": [0.0] * dimension,
            "std": [1.0] * dimension,
            "fit_partition": "train_instances_only",
        },
        "state_dict": model.state_dict(),
        "fallback_action": "Q0",
        "deployment_authorized": False,
    }


def test_checkpoint_round_trip_and_finite_predictions(tmp_path) -> None:
    dimension = len(QG2_CONTEXT_FEATURES)
    model = QG2ContextArmSelector(dimension)
    path = tmp_path / "selector.pt"
    torch.save(_checkpoint(model), path)

    loaded, payload = load_qg2_context_arm_selector(path)
    predictions = predict_qg2_context_arms(
        loaded, payload, [0.0] * dimension
    )

    assert tuple(predictions) == QG2_CONTEXT_ARM_SELECTOR_ARMS
    assert all(
        0.0 <= row.benefit_probability <= 1.0
        and row.conditional_positive_gain >= 0.0
        for row in predictions.values()
    )


@pytest.mark.parametrize(
    "mutation",
    (
        lambda row: row.update({"fallback_action": "QB1"}),
        lambda row: row.update({"deployment_authorized": True}),
        lambda row: row.update({"arms": ["QB1", "QD1"]}),
        lambda row: row["normalization"].update(
            {"fit_partition": "calibration"}
        ),
    ),
)
def test_checkpoint_contract_fails_closed(tmp_path, mutation) -> None:
    model = QG2ContextArmSelector(len(QG2_CONTEXT_FEATURES))
    payload = deepcopy(_checkpoint(model))
    mutation(payload)
    path = tmp_path / "selector.pt"
    torch.save(payload, path)

    with pytest.raises(ValueError, match="validation failed"):
        load_qg2_context_arm_selector(path)


def test_secondary_arm_exists_only_after_qg2_declines() -> None:
    predictions = {
        "QD1": QG2ContextArmPrediction(0.90, 0.40),
        "QB1": QG2ContextArmPrediction(0.95, 0.50),
    }

    assert choose_qg2_secondary_arm(
        predictions,
        benefit_probability_threshold=0.80,
        expected_gain_threshold=0.20,
        qg2_declined=False,
    ) == "Q0"
    assert choose_qg2_secondary_arm(
        predictions,
        benefit_probability_threshold=0.80,
        expected_gain_threshold=0.20,
        qg2_declined=True,
    ) == "QB1"
    assert choose_qg2_secondary_arm(
        predictions,
        benefit_probability_threshold=0.99,
        expected_gain_threshold=0.20,
        qg2_declined=True,
    ) == "Q0"
    assert choose_qg2_secondary_arm(
        predictions,
        benefit_probability_threshold=0.80,
        expected_gain_threshold=0.20,
        qg2_declined=True,
        ood=True,
    ) == "Q0"


def test_context_ood_uses_train_only_envelope() -> None:
    dimension = len(QG2_CONTEXT_FEATURES)
    envelope = {
        "context_min": [-1.0] * dimension,
        "context_max": [1.0] * dimension,
        "relative_margin": 0.05,
    }
    assert not qg2_context_arm_is_ood([0.0] * dimension, envelope)
    outside = [0.0] * dimension
    outside[3] = 2.0
    assert qg2_context_arm_is_ood(outside, envelope)
    assert qg2_context_arm_is_ood([0.0] * (dimension - 1), envelope)
