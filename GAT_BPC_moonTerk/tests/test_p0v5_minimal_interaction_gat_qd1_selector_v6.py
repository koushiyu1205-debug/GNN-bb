from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

import pytest
import torch

from lunar_ice_bpc.exact.bpc.pricing.backends.base import BackendPricingRequest
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v6 import (
    INTERACTION_GAT_ACTION_UNIVERSE_V6,
    INTERACTION_GAT_EVALUATION_ENV_V6,
    INTERACTION_GAT_MANIFEST_ENV_V6,
    INTERACTION_GAT_RUNTIME_POLICY_V6,
    _choose_action_v6,
    interaction_gat_runtime_implementation_hash_v6,
    prepare_root_interaction_gat_qd1_request_v6_from_environment,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (
    INTERACTION_FEATURE_SCHEMA_V2,
    INTERACTION_GRAPH_SCHEMA_V1,
    INTERACTION_INPUT_PARITY_CONTRACT_V1,
    build_interaction_graph,
    fit_interaction_envelope,
    fit_interaction_normalization,
    interaction_graph_builder_hash,
    interaction_parameter_count,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v6 import (
    INTERACTION_CHECKPOINT_SCHEMA_V6,
    INTERACTION_DATASET_SCHEMA_V6,
    INTERACTION_MANIFEST_SCHEMA_V6,
    V6_ACTION_UNIVERSE,
    V6_ARMS,
    V6_MODEL_KINDS,
    build_model_v6,
    interaction_training_loss_v6,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
    qg2_exact_action_policy_hash_from_request,
)


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _request(scale: int = 30, lifecycle: str = "root_cg") -> BackendPricingRequest:
    path = ROOT / (
        f"data/instances/lunar_ice_sp50_{scale:03d}/"
        "instance_001_logical_graph.json"
    )
    data = load_lunar_ice_data(json.loads(path.read_text(encoding="utf-8")))
    active = tuple((task_id,) for task_id in data.task_ids[:4])
    return BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}),
        mode="exact_proof",
        objective_mode="official",
        pricing_lifecycle_scope=lifecycle,
        proof_queue_policy_id="Q0",
        proof_tail_fallback_context=True,
        proof_tail_active_column_count=len(active),
        proof_tail_active_task_sets=active,
        proof_tail_active_column_signature_hashes=tuple(
            f"{index:064x}" for index in range(len(active))
        ),
        proof_tail_round_index=1,
        instance_hash=data.instance_content_hash,
        config_hash="config-v6-test",
        engine_hash="engine-v6-test",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_sha256(payload) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")).hexdigest()


def _write_bound_json(tmp_path: Path, stem: str, payload: dict) -> tuple[str, str]:
    path = tmp_path / f"{stem}.json"
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return str(path), _sha256(path)


def _write_manifest(tmp_path: Path, request: BackendPricingRequest) -> Path:
    features = build_interaction_graph(request)
    normalization = fit_interaction_normalization([features])
    envelope = fit_interaction_envelope([features])
    model = build_model_v6("gat", normalization)
    with torch.no_grad():
        model.qd1_head.head.weight.zero_()
        model.qd1_head.head.bias[:] = torch.tensor([10.0, 1.0, -10.0])
    architecture = {
        "hidden_dim": 16,
        "attention_heads": 2,
        "layers": 2,
        "dropout": 0.1,
        "residual": True,
        "layer_norm": True,
    }
    checkpoint = tmp_path / "gat-v6.pt"
    torch.save({
        "schema_version": INTERACTION_CHECKPOINT_SCHEMA_V6,
        "feature_schema_version": INTERACTION_FEATURE_SCHEMA_V2,
        "graph_schema_version": INTERACTION_GRAPH_SCHEMA_V1,
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "model_kind": "gat",
        "message_passing_required": True,
        "independently_trained": True,
        "controls_candidate_authorized": False,
        "action_universe": list(V6_ACTION_UNIVERSE),
        "architecture": architecture,
        "normalization": normalization,
        "probability_calibration": {
            "30": {"benefit": {}, "adverse": {}, "positive_gain_scale": 1.0},
            "50": {"benefit": {}, "adverse": {}, "positive_gain_scale": 1.0},
        },
        "state_dict": model.state_dict(),
        "parameter_count": interaction_parameter_count(model),
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }, checkpoint)
    bound = {}
    for prefix, payload in {
        "evidence_import": {"v5": True},
        "corpus_freeze": {"corpus": True},
        "split_freeze": {"split": True},
        "cv_folds_freeze": {"folds": True},
        "normalization": normalization,
        "ood_envelope": envelope,
    }.items():
        path, digest = _write_bound_json(tmp_path, prefix, payload)
        bound[f"{prefix}_path"] = path
        bound[f"{prefix}_sha256"] = digest
    thresholds = {
        str(scale): {
            "minimum_benefit_probability": 0.60,
            "maximum_adverse_probability": 0.10,
            "minimum_expected_gain": 0.02,
            "risk_penalty": 0.50,
        }
        for scale in (30, 50)
    }
    payload = {
        "schema_version": INTERACTION_MANIFEST_SCHEMA_V6,
        "runtime_policy_id": INTERACTION_GAT_RUNTIME_POLICY_V6,
        "runtime_implementation_hash": interaction_gat_runtime_implementation_hash_v6(),
        "graph_builder_hash": interaction_graph_builder_hash(),
        "graph_schema_version": INTERACTION_GRAPH_SCHEMA_V1,
        "feature_schema_version": INTERACTION_FEATURE_SCHEMA_V2,
        "checkpoint_schema_version": INTERACTION_CHECKPOINT_SCHEMA_V6,
        "dataset_schema_version": INTERACTION_DATASET_SCHEMA_V6,
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "action_universe": list(V6_ACTION_UNIVERSE),
        "fallback_action": "Q0",
        "allowed_scales": [30, 50],
        "lifecycle_authority": ["root_cg"],
        "root_only_authority": True,
        "arm_scale_mask": {"QD1": [30, 50]},
        "forced_veto_arms": [],
        "forced_veto_arms_by_scale": {"30": [], "50": []},
        "permanent_forced_veto_arms": ["QB1", "QGR1"],
        "model_kind": "gat",
        "message_passing_required": True,
        "controls_candidate_authorized": False,
        "architecture": architecture,
        "selector_checkpoint_path": str(checkpoint),
        "selector_checkpoint_sha256": _sha256(checkpoint),
        "feature_envelope": envelope,
        "thresholds_by_scale": thresholds,
        "allowed_exact_engine_hashes": [request.engine_hash],
        "allowed_exact_config_hashes": [request.config_hash],
        "allowed_exact_action_policy_hashes": [
            qg2_exact_action_policy_hash_from_request(request)
        ],
        "normalization_payload_sha256": _json_sha256(normalization),
        "source_freeze_sha256": "test-source",
        "native_binary_sha256": "test-native",
        "torch_num_threads": 1,
        "development_e2e_authorized": True,
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
        **bound,
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    return manifest


def test_v6_action_universe_and_output_contract_exclude_qgr1_qb1_resource():
    assert INTERACTION_GAT_ACTION_UNIVERSE_V6 == V6_ACTION_UNIVERSE
    assert V6_ACTION_UNIVERSE == ("Q0", "QD1")
    assert V6_ARMS == ("QD1",)
    assert "QGR1" not in V6_ACTION_UNIVERSE and "QB1" not in V6_ACTION_UNIVERSE
    features = build_interaction_graph(_request())
    normalization = fit_interaction_normalization([features])
    models = {kind: build_model_v6(kind, normalization) for kind in V6_MODEL_KINDS}
    assert len({id(model) for model in models.values()}) == 5
    assert all(interaction_parameter_count(model) < 20_000 for model in models.values())
    for kind, model in models.items():
        tensor_features = features
        if kind == "shuffled_topology":
            from lunar_ice_bpc.guidance.interaction_gat_queue_v6 import (
                features_for_model_kind_v6,
            )
            tensor_features = features_for_model_kind_v6(
                features, model_kind=kind, state_hash="1" * 64
            )
        with torch.inference_mode():
            output = model(**tensor_features.to_tensors())
        assert set(output) == {
            "benefit_probability", "conditional_positive_gain",
            "adverse_probability",
        }
        assert all(tuple(value.shape) == (1, 1) for value in output.values())


def test_v6_loss_has_three_heads_and_qd1_margin_gradient():
    output = {
        "benefit_probability": torch.tensor([[0.7]], requires_grad=True),
        "conditional_positive_gain": torch.tensor([[0.2]], requires_grad=True),
        "adverse_probability": torch.tensor([[0.1]], requires_grad=True),
    }
    losses = interaction_training_loss_v6(
        output,
        benefit_target=torch.ones(1),
        positive_gain_target=torch.tensor([0.25]),
        adverse_target=torch.zeros(1),
        determined_mask=torch.ones(1),
        positive_mask=torch.ones(1),
        rank_direction=torch.ones(1),
        rank_mask=torch.ones(1),
    )
    assert "resource_censor_bce" not in losses
    assert float(losses["pairwise_rank"].detach()) > 0.0
    losses["loss"].backward()
    assert all(value.grad is not None for value in output.values())


def test_v6_scale_specific_thresholds_can_select_different_actions():
    base = {
        "QD1": {
            "raw_benefit_probability": 0.75,
            "raw_conditional_positive_gain": 0.10,
            "raw_adverse_probability": 0.03,
        },
        "_calibration_by_scale": {},
    }
    manifest = {
        "arm_scale_mask": {"QD1": [30, 50]},
        "forced_veto_arms": [],
        "forced_veto_arms_by_scale": {"30": [], "50": []},
        "thresholds_by_scale": {
            "30": {
                "minimum_benefit_probability": 0.70,
                "minimum_expected_gain": 0.05,
                "maximum_adverse_probability": 0.05,
                "risk_penalty": 0.5,
            },
            "50": {
                "minimum_benefit_probability": 0.90,
                "minimum_expected_gain": 0.10,
                "maximum_adverse_probability": 0.02,
                "risk_penalty": 2.0,
            },
        },
    }
    selected30, _ = _choose_action_v6(json.loads(json.dumps(base)), manifest, 30)
    selected50, _ = _choose_action_v6(json.loads(json.dumps(base)), manifest, 50)
    assert selected30 == "QD1"
    assert selected50 == "Q0"


@pytest.mark.parametrize("scale,lifecycle", ((5, "root_cg"), (30, "tree_node")))
def test_v6_small_scale_and_tree_bypass_return_same_request_before_manifest(
    monkeypatch, scale, lifecycle,
):
    request = _request(scale=scale, lifecycle=lifecycle)
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV_V6, "/must/not/be/read.json")
    selected, telemetry = prepare_root_interaction_gat_qd1_request_v6_from_environment(
        request
    )
    assert selected is request
    assert telemetry["proof_tail_interaction_gat_manifest_read"] is False
    assert telemetry["proof_tail_interaction_gat_graph_build_calls"] == 0
    assert telemetry["proof_tail_interaction_gat_model_calls"] == 0
    assert telemetry["proof_tail_interaction_gat_ranker_calls"] == 0


def test_v6_valid_manifest_installs_only_qd1(monkeypatch, tmp_path):
    request = _request()
    manifest = _write_manifest(tmp_path, request)
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV_V6, str(manifest))
    monkeypatch.setenv(INTERACTION_GAT_EVALUATION_ENV_V6, "1")
    selected, telemetry = prepare_root_interaction_gat_qd1_request_v6_from_environment(
        request
    )
    assert selected is not request
    assert selected.proof_queue_policy_id == "QD1"
    assert selected.guidance_hints is None
    assert telemetry["proof_tail_interaction_gat_action"] == "QD1"
    assert telemetry["proof_tail_interaction_gat_model_calls"] == 1
    assert telemetry["proof_tail_interaction_gat_ranker_calls"] == 0


def test_v6_ranker_or_qgr1_manifest_field_fails_closed(monkeypatch, tmp_path):
    request = _request()
    manifest = _write_manifest(tmp_path, request)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["qgr1_ranker_checkpoint_path"] = "/forbidden"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV_V6, str(manifest))
    monkeypatch.setenv(INTERACTION_GAT_EVALUATION_ENV_V6, "1")
    selected, telemetry = prepare_root_interaction_gat_qd1_request_v6_from_environment(
        request
    )
    assert selected is request
    assert telemetry["proof_tail_interaction_gat_action"] == "Q0"
    assert telemetry["proof_tail_interaction_gat_ranker_calls"] == 0
    assert "fail_closed" in telemetry["proof_tail_interaction_gat_decision_reason"]


def test_v6_v5_evidence_import_has_exact_frozen_counts():
    from scripts.p0v5_minimal_interaction_gat_qd1_v6_common import (
        CONFIG, load, validate_v5_import,
    )

    imported = validate_v5_import(load(CONFIG))
    assert len(imported["raw"]["rows"]) == 444
    assert len(imported["collapsed"]["rows"]) == 74
    assert imported["terminal"]["reason"] == (
        "QGR1_TRACE_MANDATORY_WITNESS_INCOMPLETE"
    )
    assert imported["calibration_oracle"]["30"]["instance_count"] == 3
    assert imported["calibration_oracle"]["50"]["instance_count"] == 4
    failures = [
        row for row in imported["collapsed"]["rows"]
        if row.get("resource_censor_positive")
    ]
    assert len(failures) == 1
    assert failures[0]["adverse"] is True
    assert failures[0]["q0_complete_arm_censored_blocks"] == 3


def test_v6_non_q0_incoming_request_always_preserves_identity(monkeypatch):
    request = replace(_request(), proof_queue_policy_id="QD1")
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV_V6, "/must/not/be/read.json")
    selected, telemetry = prepare_root_interaction_gat_qd1_request_v6_from_environment(
        request
    )
    assert selected is request
    assert telemetry["proof_tail_interaction_gat_action"] == "Q0"
    assert telemetry["proof_tail_interaction_gat_model_calls"] == 0
