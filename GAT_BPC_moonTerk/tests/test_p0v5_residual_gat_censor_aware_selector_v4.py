from __future__ import annotations

import builtins
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest
import torch

import sys

from lunar_ice_bpc.exact.bpc.pricing.backends.base import BackendPricingRequest
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.guidance.interaction_gat_queue_gates_v4 import (
    CENSOR_AWARE_MATCHED_SCHEMA_V1,
    assess_v4_qd1_admission,
    collapse_censor_aware_matrix,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v4 import (
    INTERACTION_GAT_ACTION_UNIVERSE_V4,
    INTERACTION_GAT_EVALUATION_ENV_V4,
    INTERACTION_GAT_MANIFEST_ENV_V4,
    INTERACTION_GAT_RUNTIME_POLICY_V4,
    _choose_action_v4,
    interaction_gat_runtime_implementation_hash_v4,
    prepare_root_interaction_gat_request_v4_from_environment,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (
    INTERACTION_INPUT_PARITY_CONTRACT_V1,
    build_interaction_graph,
    fit_interaction_envelope,
    fit_interaction_normalization,
    interaction_graph_builder_hash,
    interaction_parameter_count,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v4 import (
    INTERACTION_CHECKPOINT_SCHEMA_V3,
    INTERACTION_CORPUS_SCHEMA_V4,
    INTERACTION_DATASET_SCHEMA_V4,
    INTERACTION_MANIFEST_SCHEMA_V3,
    V4_ACTION_UNIVERSE,
    V4_ARMS,
    V4_MODEL_KINDS,
    build_model_v4,
    interaction_training_loss_v4,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
    qg2_exact_action_policy_hash_from_request,
)


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import scripts.train_p0v5_residual_interaction_gat_selector_v4 as trainer_v4  # noqa: E402


def _request(scale=30, lifecycle="root_cg"):
    path = ROOT / f"data/instances/lunar_ice_sp50_{scale:03d}/instance_001_logical_graph.json"
    data = load_lunar_ice_data(json.loads(path.read_text(encoding="utf-8")))
    sets = tuple((task_id,) for task_id in data.task_ids[:4])
    return BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}),
        mode="exact_proof", objective_mode="official",
        pricing_lifecycle_scope=lifecycle, proof_queue_policy_id="Q0",
        proof_tail_fallback_context=True,
        proof_tail_active_column_count=len(sets),
        proof_tail_active_task_sets=sets,
        proof_tail_active_column_signature_hashes=tuple(
            f"{index:064x}" for index in range(len(sets))
        ),
        proof_tail_round_index=1,
        instance_hash=data.instance_content_hash,
        config_hash="config", engine_hash="engine",
    )


def _row(context, instance, scale, arm, block, status, wall, *, reached=True):
    return {
        "schema_version": CENSOR_AWARE_MATCHED_SCHEMA_V1,
        "context_id": context, "instance_hash": instance, "scale": scale,
        "partition": "train", "arm": arm, "block": block,
        "status": status, "wall_sec": wall, "milestone_reached": reached,
        "correctness_redlines": [],
    }


def _write_manifest(tmp_path, request):
    features = build_interaction_graph(request)
    normalization = fit_interaction_normalization([features])
    envelope = fit_interaction_envelope([features])
    model = build_model_v4("gat", normalization)
    selected = V4_ARMS.index("QD1")
    with torch.no_grad():
        model.arm_heads.head.weight.zero_()
        model.arm_heads.head.bias.zero_()
        for index in range(len(V4_ARMS)):
            model.arm_heads.head.bias[4 * index:4 * index + 4] = torch.tensor(
                [-10.0, -10.0, 10.0, 10.0]
            )
        model.arm_heads.head.bias[4 * selected:4 * selected + 4] = torch.tensor(
            [10.0, 1.0, -10.0, -10.0]
        )
    architecture = {
        "hidden_dim": 16, "attention_heads": 2, "layers": 2,
        "dropout": 0.1, "residual": True, "layer_norm": True,
    }
    checkpoint = tmp_path / "gat-v4.pt"
    torch.save({
        "schema_version": INTERACTION_CHECKPOINT_SCHEMA_V3,
        "feature_schema_version": "lunar_ice_bpc.p0v5_interaction_gat_queue_features.v2",
        "graph_schema_version": "lunar_ice_bpc.p0v5_root_interaction_graph.v1",
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "model_kind": "gat", "message_passing_required": True,
        "independently_trained": True, "controls_candidate_authorized": False,
        "action_universe": list(V4_ACTION_UNIVERSE), "architecture": architecture,
        "normalization": normalization, "probability_calibration": {},
        "state_dict": model.state_dict(),
        "parameter_count": interaction_parameter_count(model),
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }, checkpoint)
    bound = {}
    for name, payload in {
        "corpus_freeze": {"corpus": True}, "split_freeze": {"split": True},
        "cv_folds_freeze": {"folds": True}, "normalization": normalization,
        "ood_envelope": envelope,
    }.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        bound[f"{name}_path"] = str(path)
        bound[f"{name}_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    payload = {
        "schema_version": INTERACTION_MANIFEST_SCHEMA_V3,
        "runtime_policy_id": INTERACTION_GAT_RUNTIME_POLICY_V4,
        "runtime_implementation_hash": interaction_gat_runtime_implementation_hash_v4(),
        "graph_builder_hash": interaction_graph_builder_hash(),
        "graph_schema_version": "lunar_ice_bpc.p0v5_root_interaction_graph.v1",
        "feature_schema_version": "lunar_ice_bpc.p0v5_interaction_gat_queue_features.v2",
        "checkpoint_schema_version": INTERACTION_CHECKPOINT_SCHEMA_V3,
        "dataset_schema_version": INTERACTION_DATASET_SCHEMA_V4,
        "corpus_schema_version": INTERACTION_CORPUS_SCHEMA_V4,
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "action_universe": list(V4_ACTION_UNIVERSE), "fallback_action": "Q0",
        "allowed_scales": [30, 50], "lifecycle_authority": ["root_cg"],
        "root_only_authority": True,
        "arm_scale_mask": {"QGR1": [], "QD1": [30, 50]},
        "forced_veto_arms": ["QGR1"], "permanent_forced_veto_arms": ["QB1"],
        "forced_veto_arms_by_scale": {"30": [], "50": []},
        "model_kind": "gat", "message_passing_required": True,
        "controls_candidate_authorized": False, "architecture": architecture,
        "selector_checkpoint_path": str(checkpoint),
        "selector_checkpoint_sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        "feature_envelope": envelope,
        "thresholds": {
            "minimum_benefit_probability": 0.8,
            "minimum_expected_gain": 0.01,
            "maximum_adverse_probability": 0.1, "risk_penalty": 0.5,
            "maximum_resource_probability": 0.1,
            "resource_risk_penalty": 0.5,
        },
        "allowed_exact_engine_hashes": [request.engine_hash],
        "allowed_exact_config_hashes": [request.config_hash],
        "allowed_exact_action_policy_hashes": [
            qg2_exact_action_policy_hash_from_request(request)
        ],
        "normalization_payload_sha256": hashlib.sha256(json.dumps(
            normalization, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False,
        ).encode()).hexdigest(),
        "source_freeze_sha256": "test-source", "native_binary_sha256": "test-native",
        "torch_num_threads": 1, "development_e2e_authorized": True,
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
        **bound,
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    return manifest


def test_v4_interfaces_remove_qb1_and_add_resource_head():
    assert INTERACTION_GAT_ACTION_UNIVERSE_V4 == V4_ACTION_UNIVERSE
    assert V4_ACTION_UNIVERSE == ("Q0", "QGR1", "QD1")
    assert "QB1" not in V4_ACTION_UNIVERSE
    assert INTERACTION_CHECKPOINT_SCHEMA_V3.endswith("checkpoint.v3")
    assert INTERACTION_DATASET_SCHEMA_V4.endswith("dataset.v4")
    assert INTERACTION_CORPUS_SCHEMA_V4.endswith("freeze.v4")


def test_v4_backend_request_freezes_reservoir_contract_and_rejects_bad_caps():
    request = replace(
        _request(), proof_tail_label_trace_enabled=True,
        proof_tail_label_trace_max_rows=100_000,
        proof_tail_label_trace_sampling_mode="qgr1_stratified_reservoir_v1",
        proof_tail_label_trace_seed=0x260815,
        proof_tail_preference_cap_per_family=12_500,
        proof_tail_surface_reservoir_count=3_125,
        proof_tail_surface_labels_per_bucket=8,
        proof_tail_witness_route_cap=512,
        proof_tail_witness_ancestor_cap=25_000,
    )
    assert request.proof_tail_label_trace_max_rows == 100_000
    assert request.proof_tail_label_trace_sampling_mode.endswith("reservoir_v1")
    with pytest.raises(ValueError, match="at least two"):
        replace(request, proof_tail_surface_labels_per_bucket=1)


def test_v4_all_models_are_independent_below_cap_and_have_four_outputs():
    features = build_interaction_graph(_request())
    normalization = fit_interaction_normalization([features])
    models = {kind: build_model_v4(kind, normalization) for kind in V4_MODEL_KINDS}
    assert len({id(model) for model in models.values()}) == 5
    assert all(interaction_parameter_count(model) < 20_000 for model in models.values())
    with torch.inference_mode():
        output = models["gat"](**features.to_tensors())
    assert set(output) == {
        "benefit_probability", "conditional_positive_gain",
        "adverse_probability", "resource_censor_probability",
    }
    assert all(tuple(value.shape) == (1, 2) for value in output.values())


def test_v4_loss_uses_double_censored_rows_only_for_resource_target():
    output = {
        "benefit_probability": torch.tensor([[0.6, 0.6]], requires_grad=True),
        "conditional_positive_gain": torch.tensor([[0.1, 0.1]], requires_grad=True),
        "adverse_probability": torch.tensor([[0.1, 0.1]], requires_grad=True),
        "resource_censor_probability": torch.tensor([[0.8, 0.2]], requires_grad=True),
    }
    losses = interaction_training_loss_v4(
        output, benefit_target=torch.zeros(2), positive_gain_target=torch.zeros(2),
        adverse_target=torch.zeros(2), resource_censor_target=torch.tensor([1.0, 0.0]),
        determined_mask=torch.zeros(2), positive_mask=torch.zeros(2),
        resource_mask=torch.ones(2), pairwise_preferences=(),
    )
    assert float(losses["benefit_bce"].detach()) == pytest.approx(0.0)
    assert float(losses["adverse_bce"].detach()) == pytest.approx(0.0)
    assert float(losses["resource_censor_bce"].detach()) > 0.0
    losses["loss"].backward()
    assert output["resource_censor_probability"].grad is not None


def test_v4_mixed_and_double_censor_collapse_requires_two_comparable_blocks():
    rows = []
    for block, (q0_status, arm_status) in enumerate((
        ("MILESTONE_REACHED", "MILESTONE_REACHED"),
        ("MILESTONE_REACHED", "TIMEOUT"),
        ("TIMEOUT", "TIMEOUT"),
    )):
        rows.append(_row("c", "i", 30, "Q0", block, q0_status, 100.0,
                         reached=q0_status == "MILESTONE_REACHED"))
        rows.append(_row("c", "i", 30, "QD1", block, arm_status, 80.0,
                         reached=arm_status == "MILESTONE_REACHED"))
    outcome = collapse_censor_aware_matrix(rows, caps_by_scale={30: 300.0})[0]
    assert outcome.determined
    assert outcome.comparable_blocks == 2
    assert outcome.double_censored_blocks == 1
    assert outcome.resource_censor_positive
    assert outcome.adverse


def test_v4_single_undetermined_context_does_not_raise_or_terminate():
    rows = []
    for block in range(3):
        rows.append(_row("c", "i", 50, "Q0", block, "TIMEOUT", 600.0, reached=False))
        rows.append(_row("c", "i", 50, "QD1", block, "TIMEOUT", 600.0, reached=False))
    outcome = collapse_censor_aware_matrix(rows, caps_by_scale={50: 600.0})[0]
    assert not outcome.determined
    assert outcome.resource_censor_positive
    decision = assess_v4_qd1_admission((outcome,), scale=50)
    assert not decision["admitted"]
    assert decision["mode"] == "forced_veto"


def test_v4_risk_rule_rejects_resource_risk_and_never_sees_qb1():
    predictions = {
        "QGR1": {"benefit_probability": 0.9, "expected_gain": 0.2,
                  "adverse_probability": 0.01, "resource_censor_probability": 0.2},
        "QD1": {"benefit_probability": 0.9, "expected_gain": 0.1,
                "adverse_probability": 0.01, "resource_censor_probability": 0.01},
    }
    manifest = {
        "thresholds": {"minimum_benefit_probability": 0.8,
                       "minimum_expected_gain": 0.02,
                       "maximum_adverse_probability": 0.05,
                       "risk_penalty": 1.0,
                       "maximum_resource_probability": 0.05,
                       "resource_risk_penalty": 1.0},
        "arm_scale_mask": {"QGR1": [30], "QD1": [30]},
        "forced_veto_arms": [], "forced_veto_arms_by_scale": {},
    }
    assert _choose_action_v4(predictions, manifest, 30)[0] == "QD1"


def test_v4_training_threshold_gate_counts_resource_activation_as_unsafe():
    predictions = []
    for scale in (30, 50):
        for index in range(2):
            targets = {
                arm: {
                    "determined": True, "ratio": 0.9, "benefit": True,
                    "positive_gain": 0.1, "adverse": False,
                    "resource_censor": arm == "QD1", "resource_observed": True,
                } for arm in V4_ARMS
            }
            predictions.append({
                "context_id": f"{scale}-{index}", "instance_hash": f"{scale}-i{index}",
                "scale": scale, "context_weight": 1.0, "targets": targets,
                "benefit": {"QGR1": 0.01, "QD1": 0.99},
                "gain": {"QGR1": 0.01, "QD1": 0.2},
                "adverse": {"QGR1": 0.01, "QD1": 0.01},
                "resource_censor": {"QGR1": 0.01, "QD1": 0.01},
            })
    identity = {"slope": 1.0, "intercept": 0.0}
    calibration = {
        "benefit": {arm: identity for arm in V4_ARMS},
        "adverse": {arm: identity for arm in V4_ARMS},
        "resource_censor": {arm: identity for arm in V4_ARMS},
        "positive_gain_scale": {arm: 1.0 for arm in V4_ARMS},
    }
    grid = {
        "minimum_benefit_probability": [0.8],
        "maximum_adverse_probability": [0.05],
        "minimum_expected_gain": [0.05], "risk_penalty": [1.0],
        "maximum_resource_probability": [0.05], "resource_risk_penalty": [1.0],
    }
    result = trainer_v4._threshold_results(
        predictions, calibration, grid, {30: ["QD1"], 50: ["QD1"]}, [1.0]
    )[0]
    assert result["resource_censor_activations"] == 4
    assert result["calibration_gate_eligible"] is False


@pytest.mark.parametrize("scale", (5, 10, 20))
def test_v4_small_scale_is_literal_identity_before_manifest_graph_torch(
    scale, monkeypatch,
):
    request = _request(scale)
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV_V4, "/must/not/be/read.json")
    imported = []
    original = builtins.__import__

    def spy(name, *args, **kwargs):
        imported.append(str(name))
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", spy)
    selected, telemetry = prepare_root_interaction_gat_request_v4_from_environment(request)
    assert selected is request
    assert telemetry["proof_tail_interaction_gat_manifest_read"] is False
    assert telemetry["proof_tail_interaction_gat_graph_build_calls"] == 0
    assert telemetry["proof_tail_interaction_gat_model_calls"] == 0
    assert not any("interaction_gat_queue_runtime_v2" in name for name in imported)


def test_v4_tree_is_literal_identity_before_manifest_graph_torch(monkeypatch):
    request = _request(lifecycle="tree_node")
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV_V4, "/must/not/be/read.json")
    selected, telemetry = prepare_root_interaction_gat_request_v4_from_environment(request)
    assert selected is request
    assert telemetry["proof_tail_interaction_gat_manifest_read"] is False
    assert telemetry["proof_tail_interaction_gat_model_calls"] == 0


def test_v4_runtime_selects_only_qd1_from_valid_gat_manifest(tmp_path, monkeypatch):
    request = _request()
    manifest = _write_manifest(tmp_path, request)
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV_V4, str(manifest))
    monkeypatch.setenv(INTERACTION_GAT_EVALUATION_ENV_V4, "1")
    selected, telemetry = prepare_root_interaction_gat_request_v4_from_environment(request)
    assert selected is not request
    assert selected.proof_queue_policy_id == "QD1"
    assert selected.guidance_hints is None
    assert telemetry["proof_tail_interaction_gat_action"] == "QD1"
    assert telemetry["proof_tail_interaction_gat_runtime_policy"] == (
        INTERACTION_GAT_RUNTIME_POLICY_V4
    )
    assert "QB1" not in telemetry["proof_tail_interaction_gat_predictions"]


def test_v4_qgr1_veto_never_opens_ranker_file(tmp_path, monkeypatch):
    request = _request()
    manifest = _write_manifest(tmp_path, request)
    payload = json.loads(manifest.read_text())
    payload["qgr1_ranker_checkpoint_path"] = "/must/not/open-v4-ranker.pt"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV_V4, str(manifest))
    monkeypatch.setenv(INTERACTION_GAT_EVALUATION_ENV_V4, "1")
    original = Path.read_bytes

    def spy(path):
        assert str(path) != "/must/not/open-v4-ranker.pt"
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", spy)
    selected, telemetry = prepare_root_interaction_gat_request_v4_from_environment(request)
    assert selected.proof_queue_policy_id == "QD1"
    assert telemetry["proof_tail_interaction_gat_ranker_calls"] == 0


def test_v4_manifest_drift_fails_to_identical_q0(tmp_path, monkeypatch):
    request = _request()
    manifest = _write_manifest(tmp_path, request)
    payload = json.loads(manifest.read_text())
    payload["permanent_forced_veto_arms"] = []
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV_V4, str(manifest))
    monkeypatch.setenv(INTERACTION_GAT_EVALUATION_ENV_V4, "1")
    selected, telemetry = prepare_root_interaction_gat_request_v4_from_environment(request)
    assert selected is request
    assert "fail_closed" in telemetry["proof_tail_interaction_gat_decision_reason"]


def test_v3_terminal_remains_read_only_resource_censor_failure():
    terminal = json.loads((
        ROOT / "runs/p0v5_interaction_gat_queue_selector_v3_20260814/terminal_decision.json"
    ).read_text(encoding="utf-8"))
    assert terminal["decision"] == "FAIL"
    assert terminal["reason"] == "RESOURCE_CENSOR_UNDETERMINED"


def test_v4_old_new_native_500_case_differential_is_clean():
    report = json.loads((
        ROOT / "output/p0v5_native_telemetry_differential_v4.json"
    ).read_text(encoding="utf-8"))
    assert report["schema_version"] == (
        "lunar_ice_bpc.p0v5_native_telemetry_differential.v4"
    )
    assert report["status"] == "PASS"
    assert report["case_count"] == 500
    assert report["redline_count"] == 0
    assert report["old_result_digest"] == report["new_result_digest"]


def test_v4_heldout_q0_fallback_still_pays_model_preparation_tax():
    from scripts.run_p0v5_residual_gat_heldout_v4 import (
        _net_ratio_with_preparation,
    )

    determined, ratio = _net_ratio_with_preparation(
        action="Q0", outcome=None, preparation_ms=10.0, q0_walls=[2.0, 1.0, 3.0]
    )
    assert determined
    assert ratio == pytest.approx(1.005)


def test_v4_q0_milestone_screen_has_no_trace_authority(tmp_path):
    from scripts.run_p0v5_residual_gat_matrix_v4 import _milestone_row

    raw_path = tmp_path / "screen.json"
    raw_path.write_text("{}", encoding="utf-8")
    row = _milestone_row(
        {"context_id": "ctx"},
        {
            "instance_content_hash": "instance", "scale": 30,
            "partition": "train", "state_hash": "state",
        },
        {
            "engine_status": "complete", "milestone_reached": True,
            "milestone_kind": "EXHAUSTIVE", "milestone_wall_sec": 1.0,
            "labels_dropped": False,
            "proof_telemetry": {"proof_queue_label_trace_final_rows": 99},
        },
        raw_path,
    )
    assert row["replay_eligible"]
    assert row["trace_requested"] is False
    assert row["trace_complete"] is False
    assert row["trace_final_rows"] == 0
    assert "q0_screen_path" in row
