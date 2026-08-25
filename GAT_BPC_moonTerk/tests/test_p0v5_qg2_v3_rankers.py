from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import sys

import pytest
import torch

from lunar_ice_bpc.guidance.proof_queue_label_state_gat import QG2Features
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.core.objective import objective_references
from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
    QG2V3Linear,
    QG2V3MLP,
    QG2V3TinyGAT,
    QG2_V3_FEATURE_ENVELOPE_SCHEMA,
    QG2_V3_INPUT_FEATURE_SCHEMA,
    fit_qg2_v3_normalization,
    load_qg2_v3_checkpoint,
    normalize_qg2_v3_features,
    qg2_v3_is_ood,
    qg2_v3_checkpoint_payload,
    qg2_v3_weighted_rank_loss,
)
from lunar_ice_bpc.guidance.qg2_admission_supervision_v3 import (
    QG2_V3_SUPERVISION_SCHEMA,
    QG2V3WeightedPair,
    _route_stratified_cap,
    build_qg2_v3_weighted_pairs,
)
from lunar_ice_bpc.guidance.qg2_unified_arm_selector_v3 import (
    QG2V3ArmPrediction,
    QG2V3ArmThreshold,
    QG2V3UnifiedArmSelector,
    QG2V3GraphArmSelector,
    QG2V3MLPArmSelector,
    QG2V3LinearGraphArmSelector,
    choose_qg2_v3_arm,
    qg2_v3_selector_loss,
)


def _features(offset: float = 0.0) -> QG2Features:
    # Current feature contract: 22 node, 8 edge, and 27 context values.
    depot = [offset + index / 10.0 for index in range(22)]
    task = [offset + 1.0 + index / 10.0 for index in range(22)]
    # Keep boolean/presence fields in their legal raw domain.
    for index in (0, 1, 14, 15, 16, 21):
        depot[index] = float(index % 2)
        task[index] = float((index + 1) % 2)
    edge = [offset + index / 7.0 for index in range(8)]
    for index in (5, 6, 7):
        edge[index] = float(index % 2)
    context = [offset + index / 13.0 for index in range(27)]
    for index in (7, 9, 13, 15, 17, 19, 25, 26):
        context[index] = float(index % 2)
    return QG2Features(
        instance_content_hash=f"instance-{offset}",
        task_ids=("task-1",),
        arc_candidate_ids=("arc-1",),
        node_features=(tuple(depot), tuple(task)),
        edge_index=((0,), (1,)),
        edge_features=(tuple(edge),),
        context_features=tuple(context),
        schema_version=QG2_V3_INPUT_FEATURE_SCHEMA,
    )


def test_qg2_v3_edge_risk_uses_exact_objective_reference() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "data/instances/lunar_ice_sp50_050/instance_001_logical_graph.json"
    )
    data = load_lunar_ice_data(json.loads(path.read_text(encoding="utf-8")))
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
        build_qg2_features,
    )

    raw = build_qg2_features(
        data,
        cover_duals={task_id: 0.0 for task_id in data.task_ids},
        fleet_dual=0.0,
        active_column_count=None,
        active_task_sets=None,
        round_index=None,
        previous_proof_wall_sec=None,
        previous_processed_labels=None,
        dual_l1_delta_from_previous=None,
        branch_decisions=(),
        cut_duals={},
        v5_midpoint_wall_sec=None,
        root_lifecycle_scope=True,
    )
    normalized = normalize_qg2_v3_features(data, raw)
    denominator = objective_references(data).reference_risk
    assert normalized.schema_version == QG2_V3_INPUT_FEATURE_SCHEMA
    assert normalized.edge_features[0][2] == pytest.approx(
        raw.edge_features[0][2] / denominator
    )
    assert max(row[2] for row in normalized.edge_features) < 0.1
    assert normalize_qg2_v3_features(data, normalized) is normalized


def test_qg2_v3_ood_is_bound_per_named_feature() -> None:
    feature = _features()
    node_names = [
        *(
            "node_" + str(index)
            for index in range(len(feature.node_features[0]))
        )
    ]
    # The real contract uses canonical names; import the exact fitted layout.
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
        QG2_CONTEXT_FEATURES,
        QG2_NODE_DYNAMIC_FEATURES,
    )
    from lunar_ice_bpc.guidance.tensorization import (
        EDGE_STATIC_FEATURES,
        NODE_STATIC_FEATURES,
    )

    node_names = [*NODE_STATIC_FEATURES, *QG2_NODE_DYNAMIC_FEATURES]
    edge_names = [
        "risk_over_objective_reference" if value == "risk" else value
        for value in EDGE_STATIC_FEATURES
    ]
    envelope = {
        "schema_version": QG2_V3_FEATURE_ENVELOPE_SCHEMA,
        "fit_partition": "train_instances_only",
        "relative_margin": 0.05,
        "context_feature_names": list(QG2_CONTEXT_FEATURES),
        "context_min": list(feature.context_features),
        "context_max": list(feature.context_features),
        "node_feature_names": node_names,
        "node_min": [min(row[i] for row in feature.node_features) for i in range(len(node_names))],
        "node_max": [max(row[i] for row in feature.node_features) for i in range(len(node_names))],
        "edge_feature_names": edge_names,
        "edge_min": list(feature.edge_features[0]),
        "edge_max": list(feature.edge_features[0]),
    }
    assert qg2_v3_is_ood(feature, envelope) == (False, "")
    shifted = QG2Features(
        **{
            **feature.__dict__,
            "edge_features": (
                tuple(
                    value + 1.0 if index == 1 else value
                    for index, value in enumerate(feature.edge_features[0])
                ),
            ),
        }
    )
    assert qg2_v3_is_ood(shifted, envelope) == (
        True,
        "edge_feature_outside_envelope:energy_over_limit",
    )


def test_qg2_v3_normalization_is_train_only_and_preserves_masks() -> None:
    payload = fit_qg2_v3_normalization([_features(0.0), _features(2.0)])
    assert payload["fit_partition"] == "train_instances_only"
    context = payload["context"]
    assert context["feature_names"][7] == "active_column_count_present"
    assert context["mean"][7] == 0.0
    assert context["std"][7] == 1.0
    assert context["mean"][0] != 0.0


@pytest.mark.parametrize(
    "model_class", (QG2V3TinyGAT, QG2V3MLP, QG2V3Linear)
)
def test_qg2_v3_rankers_emit_only_ordering_potentials(model_class) -> None:
    feature = _features()
    normalization = fit_qg2_v3_normalization([feature, _features(1.0)])
    model = model_class(normalization)
    output = model(**feature.to_tensors())
    assert set(output) == {
        "node_scores", "arc_scores", "label_state_coefficients"
    }
    assert output["node_scores"].shape == (2,)
    assert output["arc_scores"].shape == (1,)
    assert output["label_state_coefficients"].shape == (15,)
    assert all(torch.isfinite(value).all() for value in output.values())


def test_qg2_v3_checkpoint_roundtrip_binds_normalization(tmp_path) -> None:
    feature = _features()
    normalization = fit_qg2_v3_normalization([feature, _features(1.0)])
    model = QG2V3TinyGAT(normalization)
    path = tmp_path / "gat.pt"
    torch.save(
        qg2_v3_checkpoint_payload(
            model,
            normalization=normalization,
            metadata={"activation_authority": False},
        ),
        path,
    )
    loaded, metadata, loaded_normalization = load_qg2_v3_checkpoint(str(path))
    assert metadata["activation_authority"] is False
    assert loaded_normalization == normalization
    with torch.inference_mode():
        expected = model(**feature.to_tensors())
        actual = loaded(**feature.to_tensors())
    for key in expected:
        assert torch.equal(expected[key], actual[key])


def test_qg2_v3_gat_has_explicit_no_message_ablation() -> None:
    feature = _features()
    normalization = fit_qg2_v3_normalization([feature, _features(1.0)])
    model = QG2V3TinyGAT(normalization)
    tensors = feature.to_tensors()
    ordinary = model(**tensors)
    no_message = model(**tensors, disable_message_passing=True)
    assert not torch.equal(ordinary["node_scores"], no_message["node_scores"])
    assert ordinary["arc_scores"].shape == no_message["arc_scores"].shape


def test_qg2_v4_linear_label_control_sees_true_max_summary() -> None:
    normalization = fit_qg2_v3_normalization([_features(), _features(1.0)])
    model = QG2V3Linear(normalization)
    with torch.no_grad():
        model.normalizer.node_mean.zero_()
        model.normalizer.node_std.fill_(1.0)
        model.normalizer.edge_mean.zero_()
        model.normalizer.edge_std.fill_(1.0)
        model.normalizer.context_mean.zero_()
        model.normalizer.context_std.fill_(1.0)
        for parameter in model.parameters():
            parameter.zero_()
        model.node_encoder.weight[0, 0] = 1.0
        # state input is [node mean, node max, context]; select max feature 0.
        model.heads_module.state_head.weight[0, model.hidden_dim] = 1.0
    common = {
        "edge_index": torch.tensor([[0], [1]], dtype=torch.long),
        "edge_features": torch.zeros((1, 8), dtype=torch.float32),
        "context_features": torch.zeros(27, dtype=torch.float32),
    }
    first = torch.zeros((3, 22), dtype=torch.float32)
    second = torch.zeros((3, 22), dtype=torch.float32)
    first[:, 0] = torch.tensor([-1.0, 0.0, 1.0])
    second[:, 0] = torch.tensor([-1.0, -1.0, 2.0])
    assert first[:, 0].mean() == second[:, 0].mean()
    left = model(node_features=first, **common)
    right = model(node_features=second, **common)
    assert float(left["label_state_coefficients"][0].detach()) == pytest.approx(1.0)
    assert float(right["label_state_coefficients"][0].detach()) == pytest.approx(2.0)


def test_qg2_v3_weighted_rank_loss_respects_pair_mass() -> None:
    preferred = torch.tensor([2.0, -2.0])
    other = torch.zeros(2)
    mostly_first = qg2_v3_weighted_rank_loss(
        preferred, other, torch.tensor([0.99, 0.01])
    )
    mostly_second = qg2_v3_weighted_rank_loss(
        preferred, other, torch.tensor([0.01, 0.99])
    )
    assert float(mostly_first) < float(mostly_second)


def test_qg2_v3_admission_pairs_are_route_and_diversity_bound() -> None:
    labels = {
        label_id: {
            "label_id": label_id,
            "terminal": False,
            "reduced_cost_bucket": 7,
        }
        for label_id in range(1, 9)
    }
    replay = {
        "milestone_kind": "ADMISSION_BATCH_READY",
        "diversity_milestone_audit": {
            "label_supervision_target_scope": "master_admission",
            "selected_route_mapping_complete": True,
            "selected_witness_mapping_complete": True,
            "admission_target": 2,
            "selected_master_ready_native_solution_indices": [10, 11],
            "selected_admission_witnesses": [
                {
                    "native_solution_index": 10,
                    "selected_rank": 1,
                    "task_set": ["a", "b"],
                    "task_set_harvest_bucket": "new_task_set",
                    "would_enter_master": True,
                },
                {
                    "native_solution_index": 11,
                    "selected_rank": 2,
                    "task_set": ["c", "d"],
                    "task_set_harvest_bucket": "support_changing",
                    "would_enter_master": True,
                },
            ],
        },
        "proof_telemetry": {
            "proof_queue_negative_witness_trace": [
                {"solution_index": 10, "ancestor_label_ids": [1, 2]},
                {"solution_index": 11, "ancestor_label_ids": [1, 3]},
                {"solution_index": 12, "ancestor_label_ids": [4, 5, 6]},
            ],
            "proof_queue_label_preference_trace": [
                {
                    "preferred_label_id": 7,
                    "other_label_id": 8,
                    "kind": "existing_dominator",
                }
            ],
        },
    }
    pairs, metadata = build_qg2_v3_weighted_pairs(
        replay, labels, seed=3
    )
    assert metadata["supervision_schema_version"] == QG2_V3_SUPERVISION_SCHEMA
    assert metadata["selected_route_count"] == 2
    assert metadata["maximum_selected_ancestor_route_multiplicity"] == 2
    assert math.isclose(sum(row.weight for row in pairs), 1.0)
    assert {row.selected_solution_index for row in pairs if row.selected_solution_index} == {10, 11}
    hard_mass = sum(
        row.weight for row in pairs
        if row.kind == "admission_selected_vs_omitted"
    )
    background_mass = sum(
        row.weight for row in pairs if row.kind == "existing_dominator"
    )
    assert hard_mass > background_mass


def test_qg2_v3_rejects_selector_route_not_bound_as_master_ready() -> None:
    labels = {
        label_id: {
            "label_id": label_id,
            "terminal": False,
            "reduced_cost_bucket": 7,
        }
        for label_id in range(1, 5)
    }
    replay = {
        "milestone_kind": "ADMISSION_BATCH_READY",
        "diversity_milestone_audit": {
            "label_supervision_target_scope": "master_admission",
            "selected_route_mapping_complete": True,
            "selected_witness_mapping_complete": True,
            "admission_target": 1,
            "selected_master_ready_native_solution_indices": [11],
            "selected_admission_witnesses": [
                {
                    "native_solution_index": 10,
                    "selected_rank": 1,
                    "task_set": ["a"],
                    "task_set_harvest_bucket": "new_task_set",
                    "would_enter_master": False,
                },
            ],
        },
        "proof_telemetry": {
            "proof_queue_negative_witness_trace": [
                {"solution_index": 10, "ancestor_label_ids": [1, 2]},
                {"solution_index": 11, "ancestor_label_ids": [3, 4]},
            ],
        },
    }
    with pytest.raises(
        ValueError,
        match="Master-ready indices disagree with admission witnesses",
    ):
        build_qg2_v3_weighted_pairs(replay, labels, seed=3)


def test_qg2_v3_pair_cap_retains_every_admitted_route_and_mass() -> None:
    rows = [
        QG2V3WeightedPair(
            preferred_label_id=route * 10 + index,
            other_label_id=1000 + route * 10 + index,
            kind="admission_selected_vs_omitted",
            weight=float(route + 1) / 4.0,
            selected_solution_index=route,
        )
        for route in (10, 11, 12)
        for index in range(4)
    ]
    capped = _route_stratified_cap(rows, maximum=5)
    assert len(capped) == 5
    assert {row.selected_solution_index for row in capped} == {10, 11, 12}
    before = {
        route: sum(row.weight for row in rows if row.selected_solution_index == route)
        for route in (10, 11, 12)
    }
    after = {
        route: sum(row.weight for row in capped if row.selected_solution_index == route)
        for route in (10, 11, 12)
    }
    assert after == pytest.approx(before)


def test_qg2_v3_pair_cap_fails_if_route_coverage_is_impossible() -> None:
    rows = [
        QG2V3WeightedPair(index, index + 10, "admission", 1.0, index)
        for index in range(3)
    ]
    with pytest.raises(ValueError, match="retain every selected admission route"):
        _route_stratified_cap(rows, maximum=2)


def test_qg2_v3_force_on_marks_q0_reached_gat_timeout_as_adverse() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts/calibrate_p0v5_qg2_v3_gat_force_on.py"
    )
    spec = importlib.util.spec_from_file_location("qg2_v3_force_on", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    universe = {
        "legal_action_universe_hash_before_sort": "actions",
        "legal_arc_universe_hash_before_sort": "arcs",
    }
    q0 = {
        "milestone_reached": True,
        "milestone_kind": "ADMISSION_BATCH_READY",
        "admission_milestone_wall_sec": 20.0,
        "search_exhaustive": False,
        "proof_telemetry": universe,
    }
    gat = {
        "milestone_reached": False,
        "milestone_kind": "",
        "total_fresh_process_wall_sec": 100.0,
        "search_exhaustive": False,
        "labels_dropped": False,
        "proof_telemetry": universe,
    }
    repeat = module._repeat_outcome(
        q0,
        gat,
        budget=100.0,
        inference_sec=0.002,
        repeat=1,
        paths={"Q0": "q0.json", "QG2": "gat.json"},
    )
    assert repeat["comparison_class"] == "gat_adverse_censor"
    record = module._context_outcome(
        context={
            "scale": 50,
            "instance_hash": "instance",
            "state_hash": "state",
            "q0_milestone_kind": "ADMISSION_BATCH_READY",
        },
        partition="calibration",
        potential={"tensorization_wall_ms": 1.0, "inference_wall_ms": 1.0},
        potential_path=Path("potential.json"),
        repeat_rows=[repeat],
    )
    assert record["adverse_target"] is True
    assert record["harmful"] is True
    assert record["ratio"] > 1.0


def _selector_training_module():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts/train_p0v5_qg2_v3_gat_arm_selector.py"
    )
    spec = importlib.util.spec_from_file_location(
        "qg2_v4_selector_training_test", path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_qg2_v4_force_screen_uses_train_support_not_zero_harmful_rule() -> None:
    module = _selector_training_module()
    records = {}
    for index in range(5):
        records[str(index)] = {
            "partition": "train",
            "state_hash": str(index),
            "safe": True,
            "action_eligible": True,
            "comparison_class": "matched_milestone",
            "gat_net_median_wall_sec": 8.0 if index < 2 else 12.0,
            "ratio": 0.8 if index < 2 else 1.2,
            "beneficial": index < 2,
            "harmful": index >= 2,
            "adverse_target": index >= 2,
            "relative_positive_gain": 0.2 if index < 2 else 0.0,
        }
    screen = module._qg2_screen(records)
    assert screen["partitions"]["train"]["harmful_count"] == 3
    assert module._qg2_arm_is_trainable(screen)


def test_qg2_v4_beneficial_censor_trains_probability_not_magnitude() -> None:
    module = _selector_training_module()
    outcome = module._force_outcome({
        "safe": True,
        "action_eligible": True,
        "comparison_class": "gat_beneficial_censor",
        "gat_net_median_wall_sec": 50.0,
        "ratio": 0.5,
        "beneficial": False,
        "harmful": False,
        "adverse_target": False,
        "relative_positive_gain": 0.5,
    })
    assert outcome is not None
    assert outcome.beneficial
    assert outcome.right_censored
    row = {
        "outcomes": {"QG2": outcome, "QD1": None, "QB1": None}
    }
    targets = module._target_tensors(row, trainable_arms=("QG2",))
    assert bool(targets["outcome_mask"][0, 0])
    assert not bool(targets["positive_mask"][0, 0])
    assert not bool(targets["utility_mask"][0, 0])
    assert not bool(targets["adverse_target"][0, 0])


def test_qg2_v4_replicated_arm_outcome_replaces_single_replay_label() -> None:
    module = _selector_training_module()
    record = {
        "safe": True,
        "outcomes": {
            "QD1": {
                "outcome_determined": True,
                "comparison_class": "matched_milestone",
                "arm_median_wall_sec": 80.0,
                "ratio": 0.8,
                "right_censored": False,
                "beneficial": True,
                "harmful": False,
                "positive_gain_fraction": 0.2,
            }
        },
    }
    outcome = module._matched_outcome(record, "QD1")
    assert outcome is not None
    assert outcome.beneficial
    assert not outcome.harmful
    assert outcome.ratio == pytest.approx(0.8)
    targets = module._target_tensors(
        {"outcomes": {"QG2": None, "QD1": outcome, "QB1": None}},
        trainable_arms=("QD1",),
    )
    assert bool(targets["utility_mask"][0, 1])
    assert float(targets["utility_target"][0, 1]) == pytest.approx(0.2)


def test_qg2_v4_matched_arm_aggregate_uses_blocked_median() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts/collect_p0v5_qg2_realmap_v4_matched_arms.py"
    )
    spec = importlib.util.spec_from_file_location(
        "qg2_v4_matched_arm_test", path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    repeats = []
    for qd_wall, qb_wall in ((80.0, 120.0), (82.0, 118.0), (78.0, 122.0)):
        repeats.append({
            "arms": {
                "QD1": {
                    "comparison_class": "matched_milestone",
                    "q0_wall_sec": 100.0,
                    "arm_wall_sec": qd_wall,
                    "safe": True,
                },
                "QB1": {
                    "comparison_class": "matched_milestone",
                    "q0_wall_sec": 100.0,
                    "arm_wall_sec": qb_wall,
                    "safe": True,
                },
            }
        })
    record = module._aggregate(
        {"scale": 50, "instance_hash": "instance", "state_hash": "state"},
        {"instance": "train"},
        repeats,
    )
    assert record["outcomes"]["QD1"]["ratio"] == pytest.approx(0.8)
    assert record["outcomes"]["QD1"]["beneficial"]
    assert record["outcomes"]["QB1"]["ratio"] == pytest.approx(1.2)
    assert record["outcomes"]["QB1"]["harmful"]


def test_qg2_v3_selector_loss_learns_adverse_censor() -> None:
    model = QG2V3UnifiedArmSelector(27)
    predictions = model(torch.zeros((1, 27)))
    losses = qg2_v3_selector_loss(
        predictions=predictions,
        benefit_target=torch.zeros((1, 3)),
        positive_gain_target=torch.zeros((1, 3)),
        adverse_target=torch.tensor([[1.0, 0.0, 0.0]]),
        outcome_mask=torch.tensor([[True, False, False]]),
        positive_mask=torch.zeros((1, 3), dtype=torch.bool),
        adverse_mask=torch.tensor([[True, False, False]]),
    )
    assert float(losses["adverse_loss"].detach()) > 0.0
    assert float(losses["positive_gain_loss"].detach()) == 0.0
    assert float(losses["total_loss"].detach()) > float(
        losses["benefit_loss"].detach()
    )


def test_qg2_v4_selector_rank_loss_prefers_better_matched_arm() -> None:
    common = {
        "benefit_target": torch.tensor([[1.0, 1.0, 0.0]]),
        "positive_gain_target": torch.tensor([[0.2, 0.1, 0.0]]),
        "adverse_target": torch.tensor([[0.0, 0.0, 1.0]]),
        "outcome_mask": torch.tensor([[True, True, True]]),
        "positive_mask": torch.tensor([[True, True, False]]),
        "adverse_mask": torch.tensor([[True, True, True]]),
        "utility_target": torch.tensor([[0.2, 0.1, -0.2]]),
        "utility_mask": torch.tensor([[True, True, True]]),
    }
    correctly_ordered = qg2_v3_selector_loss(
        predictions={
            "benefit_probability": torch.tensor([[0.9, 0.8, 0.1]]),
            "conditional_positive_gain": torch.tensor([[0.4, 0.3, 0.1]]),
            "adverse_probability": torch.tensor([[0.05, 0.10, 0.9]]),
        },
        **common,
    )
    reversed_order = qg2_v3_selector_loss(
        predictions={
            "benefit_probability": torch.tensor([[0.1, 0.8, 0.9]]),
            "conditional_positive_gain": torch.tensor([[0.1, 0.3, 0.4]]),
            "adverse_probability": torch.tensor([[0.9, 0.10, 0.05]]),
        },
        **common,
    )
    assert float(correctly_ordered["rank_loss"]) < float(
        reversed_order["rank_loss"]
    )


def test_qg2_v4_selector_rank_loss_masks_censored_arm() -> None:
    predictions = {
        "benefit_probability": torch.tensor([[0.8, 0.8, 0.8]]),
        "conditional_positive_gain": torch.tensor([[0.2, 0.2, 0.2]]),
        "adverse_probability": torch.tensor([[0.1, 0.1, 0.1]]),
    }
    common = {
        "benefit_target": torch.ones((1, 3)),
        "positive_gain_target": torch.zeros((1, 3)),
        "adverse_target": torch.zeros((1, 3)),
        "outcome_mask": torch.zeros((1, 3), dtype=torch.bool),
        "positive_mask": torch.zeros((1, 3), dtype=torch.bool),
        "adverse_mask": torch.zeros((1, 3), dtype=torch.bool),
        "utility_mask": torch.tensor([[True, False, False]]),
    }
    first = qg2_v3_selector_loss(
        predictions=predictions,
        utility_target=torch.tensor([[0.2, -1.0, 1.0]]),
        **common,
    )
    second = qg2_v3_selector_loss(
        predictions=predictions,
        utility_target=torch.tensor([[0.2, 1.0, -1.0]]),
        **common,
    )
    torch.testing.assert_close(first["rank_loss"], second["rank_loss"])


def test_qg2_v4_arm_rank_metrics_measure_arm_and_q0_ordering() -> None:
    module = _selector_training_module()
    good = module._QG2ForceOutcome(
        wall_sec=80.0,
        ratio=0.8,
        milestone_matched=True,
        right_censored=False,
        beneficial=True,
        harmful=False,
        positive_gain_fraction=0.2,
    )
    bad = module._QG2ForceOutcome(
        wall_sec=120.0,
        ratio=1.2,
        milestone_matched=True,
        right_censored=False,
        beneficial=False,
        harmful=True,
        positive_gain_fraction=0.0,
    )
    metrics = module._arm_rank_metrics([{"arms": {
        "QG2": {"outcome": None},
        "QD1": {
            "outcome": good,
            "expected_gain": 0.2,
            "adverse_probability": 0.01,
        },
        "QB1": {
            "outcome": bad,
            "expected_gain": 0.01,
            "adverse_probability": 0.9,
        },
    }}])
    assert metrics["pair_count"] == 3
    assert metrics["pair_accuracy"] == 1.0
    assert metrics["mean_context_pair_accuracy"] == 1.0


@pytest.mark.parametrize(
    "model_class", (
        QG2V3GraphArmSelector,
        QG2V3MLPArmSelector,
        QG2V3LinearGraphArmSelector,
    )
)
def test_qg2_v3_graph_selectors_predict_all_three_arms(model_class) -> None:
    feature = _features()
    normalization = fit_qg2_v3_normalization([feature, _features(1.0)])
    output = model_class(normalization)(**feature.to_tensors())
    assert output["benefit_probability"].shape == (1, 3)
    assert output["conditional_positive_gain"].shape == (1, 3)
    assert output["adverse_probability"].shape == (1, 3)
    assert all(torch.isfinite(value).all() for value in output.values())


@pytest.mark.parametrize(
    "model_class", (
        QG2V3GraphArmSelector,
        QG2V3MLPArmSelector,
        QG2V3LinearGraphArmSelector,
    )
)
def test_qg2_v4_arm_controls_all_receive_edge_features(model_class) -> None:
    feature = _features()
    normalization = fit_qg2_v3_normalization([feature, _features(1.0)])
    model = model_class(normalization)
    model.eval()
    tensors = feature.to_tensors()
    shifted = dict(tensors)
    shifted["edge_features"] = tensors["edge_features"].clone()
    shifted["edge_features"][0, 1] += 5.0
    with torch.inference_mode():
        ordinary = model(**tensors)
        changed = model(**shifted)
    assert not torch.equal(
        ordinary["benefit_probability"],
        changed["benefit_probability"],
    )


def test_qg2_v3_selector_all_rejected_is_literal_q0() -> None:
    predictions = {
        arm: QG2V3ArmPrediction(0.4, 0.1, 0.8)
        for arm in ("QG2", "QD1", "QB1")
    }
    thresholds = {
        arm: QG2V3ArmThreshold(0.8, 0.05, 0.1)
        for arm in predictions
    }
    assert choose_qg2_v3_arm(
        predictions, thresholds, risk_penalty=1.0
    ) == "Q0"
    assert choose_qg2_v3_arm(
        predictions, thresholds, risk_penalty=1.0, ood=True
    ) == "Q0"


def test_qg2_v3_selector_compares_all_three_non_q0_arms() -> None:
    predictions = {
        "QG2": QG2V3ArmPrediction(0.9, 0.1, 0.04),
        "QD1": QG2V3ArmPrediction(0.8, 0.2, 0.02),
        "QB1": QG2V3ArmPrediction(0.7, 0.3, 0.01),
    }
    thresholds = {
        arm: QG2V3ArmThreshold(0.5, 0.01, 0.1)
        for arm in predictions
    }
    assert choose_qg2_v3_arm(
        predictions, thresholds, risk_penalty=0.5
    ) == "QB1"


def test_qg2_v4_threshold_selection_is_wilson_risk_first() -> None:
    path = Path("scripts/train_p0v5_qg2_v3_gat_arm_selector.py").resolve()
    spec = importlib.util.spec_from_file_location(
        "qg2_v4_threshold_selection_test", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    safe_key, safe_uncertainty = module._threshold_selection_key({
        "activated_count": 8,
        "harmful_count": 0,
        "beneficial_count": 5,
        "net_geomean_ratio": 0.99,
    })
    risky_key, risky_uncertainty = module._threshold_selection_key({
        "activated_count": 8,
        "harmful_count": 1,
        "beneficial_count": 7,
        "net_geomean_ratio": 0.80,
    })
    assert safe_key < risky_key
    assert safe_uncertainty["harmful_rate_wilson_95"]["upper"] < 1.0
    assert risky_uncertainty[
        "beneficial_precision_wilson_95"
    ]["lower"] > 0.0


def test_qg2_v4_no_feasible_threshold_is_valid_explicit_q0_policy() -> None:
    module = _selector_training_module()
    thresholds, report = module._choose_thresholds(
        [], trainable_arms=("QD1", "QB1")
    )
    assert report["selected_noop_only"]
    assert thresholds == {
        "minimum_benefit_probability": 1.0,
        "minimum_expected_gain": 0.0,
        "maximum_adverse_probability": 0.0,
        "risk_penalty": 1.0,
        "forced_veto_arms": ["QG2", "QD1", "QB1"],
    }
