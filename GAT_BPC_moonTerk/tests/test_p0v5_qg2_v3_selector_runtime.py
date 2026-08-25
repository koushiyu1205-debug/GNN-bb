from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest
import torch

from lunar_ice_bpc.exact.bpc.pricing.backends.base import BackendPricingRequest
from lunar_ice_bpc.exact.bpc.guidance.contracts import (
    CanonicalSolveBindingV2,
    validate_pricing_ordering_hints,
)
from lunar_ice_bpc.exact.core.branching import (
    BranchContext,
    PairBranchDecision,
    SAME_JOURNEY,
)
from lunar_ice_bpc.exact.core.cuts import CutContext, subset_row_cut
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
    QG2_CONTEXT_FEATURES,
    QG2_NODE_DYNAMIC_FEATURES,
    build_qg2_features,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
    QG2V3TinyGAT,
    QG2_V3_FEATURE_ENVELOPE_SCHEMA,
    fit_qg2_v3_normalization,
    normalize_qg2_v3_features,
    qg2_v3_checkpoint_payload,
)
from lunar_ice_bpc.guidance.qg2_admission_supervision import (
    QG2_QUEUE_ACTION_SURFACE_V1,
)
from lunar_ice_bpc.guidance.qg2_admission_supervision_v3 import (
    QG2_V3_SUPERVISION_SCHEMA,
)
from lunar_ice_bpc.guidance.tensorization import (
    EDGE_STATIC_FEATURES,
    NODE_STATIC_FEATURES,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
    qg2_exact_action_policy_hash_from_request,
)
from lunar_ice_bpc.guidance.qg2_unified_arm_selector_v3 import (
    QG2V3LinearGraphArmSelector,
    QG2_V4_SELECTOR_CHECKPOINT_SCHEMA,
)
from lunar_ice_bpc.guidance.qg2_v3_selector_runtime import (
    QG2_V3_SELECTOR_EVALUATION_ENV,
    QG2_V3_SELECTOR_MANIFEST_ENV,
    QG2_V3_SELECTOR_MANIFEST_SCHEMA,
    QG2_V3_SELECTOR_RUNTIME_POLICY_ID,
    prepare_qg2_v3_selector_request_from_environment,
    qg2_v3_selector_runtime_implementation_hash,
)


ROOT = Path(__file__).resolve().parents[1]


def _request() -> BackendPricingRequest:
    path = (
        ROOT / "data/instances/lunar_ice_sp50_030"
        / "instance_001_logical_graph.json"
    )
    data = load_lunar_ice_data(json.loads(path.read_text(encoding="utf-8")))
    return BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(
            cover={task_id: float(index % 5) for index, task_id in enumerate(data.task_ids)},
            fleet_limit=0.25,
        ),
        mode="exact_proof",
        objective_mode="official",
        pricing_lifecycle_scope="root_cg",
        proof_queue_policy_id="Q0",
        instance_hash=data.instance_content_hash,
        config_hash="exact-config-hash",
        engine_hash="exact-engine-hash",
        proof_tail_fallback_context=True,
        proof_tail_active_column_count=2,
        proof_tail_active_task_sets=(
            (data.task_ids[0],),
            (data.task_ids[1], data.task_ids[2]),
        ),
        proof_tail_active_column_signature_hashes=("0" * 64, "1" * 64),
        proof_tail_round_index=4,
        proof_tail_previous_proof_wall_sec=13.5,
        proof_tail_previous_processed_labels=125_000,
        proof_tail_dual_delta_l1=2.25,
        proof_tail_v5_midpoint_wall_sec=0.4,
        proof_tail_v5_midpoint_reason="midpoint_no_audited_negative",
    )


def _features(request):
    return normalize_qg2_v3_features(request.data, build_qg2_features(
        request.data,
        cover_duals=request.true_duals.cover,
        fleet_dual=request.true_duals.fleet_limit,
        active_column_count=request.proof_tail_active_column_count,
        active_task_sets=request.proof_tail_active_task_sets,
        round_index=request.proof_tail_round_index,
        previous_proof_wall_sec=request.proof_tail_previous_proof_wall_sec,
        previous_processed_labels=request.proof_tail_previous_processed_labels,
        dual_l1_delta_from_previous=request.proof_tail_dual_delta_l1,
        branch_decisions=tuple(request.branch_context.pair_decisions),
        cut_duals=dict(request.true_duals.cuts or {}),
        v5_midpoint_wall_sec=request.proof_tail_v5_midpoint_wall_sec,
        root_lifecycle_scope=(request.pricing_lifecycle_scope == "root_cg"),
    ))


def _manifest(tmp_path, request):
    features = _features(request)
    normalization = fit_qg2_v3_normalization([features])
    model = QG2V3LinearGraphArmSelector(normalization)
    with torch.no_grad():
        model.head.weight.zero_()
        model.head.bias.zero_()
        # Flattened triples are benefit, positive gain, adverse per arm.
        model.head.bias[3:6] = torch.tensor([10.0, 1.0, -10.0])
        model.head.bias[6:9] = torch.tensor([-10.0, -10.0, 10.0])
    checkpoint = tmp_path / "linear_selector.pt"
    torch.save({
        "schema_version": QG2_V4_SELECTOR_CHECKPOINT_SCHEMA,
        "input_parity_contract": (
            "node_edge_context_identical_gat_topology_only_difference.v1"
        ),
        "model_kind": "linear",
        "action_universe": ["Q0", "QG2", "QD1", "QB1"],
        "trainable_arms": ["QD1", "QB1"],
        "forced_veto_arms": ["QG2"],
        "fallback_action": "Q0",
        "normalization": normalization,
        "state_dict": model.state_dict(),
        "activation_authority": False,
        "deployment_authorized": False,
    }, checkpoint)
    context = list(features.context_features)
    node_names = (*NODE_STATIC_FEATURES, *QG2_NODE_DYNAMIC_FEATURES)
    edge_names = tuple(
        "risk_over_objective_reference" if value == "risk" else value
        for value in EDGE_STATIC_FEATURES
    )
    payload = {
        "schema_version": QG2_V3_SELECTOR_MANIFEST_SCHEMA,
        "runtime_policy_id": QG2_V3_SELECTOR_RUNTIME_POLICY_ID,
        "runtime_implementation_hash": qg2_v3_selector_runtime_implementation_hash(),
        "action_universe": ["Q0", "QD1", "QB1"],
        "forced_veto_arms": ["QG2"],
        "fallback_action": "Q0",
        "model_kind": "linear",
        "checkpoint_path": str(checkpoint),
        "checkpoint_sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        "feature_envelope": {
            "schema_version": QG2_V3_FEATURE_ENVELOPE_SCHEMA,
            "fit_partition": "train_instances_only",
            "context_feature_names": list(QG2_CONTEXT_FEATURES),
            "context_min": context,
            "context_max": context,
            "node_feature_names": list(node_names),
            "node_min": [
                min(row[index] for row in features.node_features)
                for index in range(len(node_names))
            ],
            "node_max": [
                max(row[index] for row in features.node_features)
                for index in range(len(node_names))
            ],
            "edge_feature_names": list(edge_names),
            "edge_min": [
                min(row[index] for row in features.edge_features)
                for index in range(len(edge_names))
            ],
            "edge_max": [
                max(row[index] for row in features.edge_features)
                for index in range(len(edge_names))
            ],
            "relative_margin": 0.1,
        },
        "thresholds": {
            "minimum_benefit_probability": 0.8,
            "minimum_expected_gain": 0.01,
            "maximum_adverse_probability": 0.1,
            "risk_penalty": 0.5,
        },
        "allowed_scales": [30, 50],
        "allowed_exact_engine_hashes": [request.engine_hash],
        "allowed_exact_action_policy_hashes": [
            qg2_exact_action_policy_hash_from_request(request)
        ],
        "development_e2e_authorized": True,
        "deployment_authorized": False,
        "torch_num_threads": 1,
    }
    manifest = tmp_path / "selector_manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    return manifest


def _enable_qg2(
    manifest: Path,
    request: BackendPricingRequest,
    *,
    zero_ranker: bool = False,
) -> tuple[Path, Path]:
    """Make the test selector choose a separately frozen QG2 ranker."""

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    selector_path = Path(payload["checkpoint_path"])
    selector = torch.load(selector_path, map_location="cpu", weights_only=False)
    bias = selector["state_dict"]["head.bias"]
    bias.zero_()
    bias[0:3] = torch.tensor([10.0, 1.0, -10.0])
    bias[3:6] = torch.tensor([-10.0, -10.0, 10.0])
    bias[6:9] = torch.tensor([-10.0, -10.0, 10.0])
    selector["forced_veto_arms"] = []
    torch.save(selector, selector_path)

    features = _features(request)
    normalization = fit_qg2_v3_normalization([features])
    torch.manual_seed(260806)
    ranker_model = QG2V3TinyGAT(normalization)
    if zero_ranker:
        with torch.no_grad():
            for parameter in ranker_model.parameters():
                parameter.zero_()
    ranker_path = manifest.parent / "label_gat.pt"
    torch.save(qg2_v3_checkpoint_payload(
        ranker_model,
        normalization=normalization,
        metadata={
            "activation_authority": False,
            "supervision_schema_version": QG2_V3_SUPERVISION_SCHEMA,
            "queue_action_surface": QG2_QUEUE_ACTION_SURFACE_V1,
        },
    ), ranker_path)
    payload.update({
        "action_universe": ["Q0", "QG2", "QD1", "QB1"],
        "forced_veto_arms": [],
        "checkpoint_sha256": hashlib.sha256(
            selector_path.read_bytes()
        ).hexdigest(),
        "qg2_ranker_checkpoint_path": str(ranker_path),
        "qg2_ranker_checkpoint_sha256": hashlib.sha256(
            ranker_path.read_bytes()
        ).hexdigest(),
        "qg2_guidance_bucket_width": 0.001,
        "qg2_label_state_schema_version": "lunar_spprc.qg2_label_state.v1",
    })
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    return selector_path, ranker_path


def test_qg2_v3_selector_absent_manifest_is_literal_noop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(QG2_V3_SELECTOR_MANIFEST_ENV, raising=False)
    request = _request()
    unchanged, telemetry = prepare_qg2_v3_selector_request_from_environment(request)
    assert unchanged is request
    assert telemetry["proof_tail_selector_action"] == "Q0"
    assert not telemetry["proof_tail_selector_runtime_enabled"]


def test_qg2_v3_selector_installs_only_exact_safe_queue_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    monkeypatch.setenv(QG2_V3_SELECTOR_MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(QG2_V3_SELECTOR_EVALUATION_ENV, "1")
    selected, telemetry = prepare_qg2_v3_selector_request_from_environment(request)
    assert telemetry["proof_tail_selector_action"] == "QD1"
    assert selected.proof_queue_policy_id == "QD1"
    assert selected.config_hash != request.config_hash
    assert selected.guidance_mode == "off"
    assert selected.guidance_hints is None
    assert not selected.proof_tail_gat_enabled


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("minimum_benefit_probability", -0.1),
        ("minimum_benefit_probability", 1.1),
        ("minimum_expected_gain", -0.1),
        ("maximum_adverse_probability", -0.1),
        ("maximum_adverse_probability", 1.1),
        ("risk_penalty", -0.1),
    ),
)
def test_qg2_v4_invalid_threshold_range_returns_literal_q0(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: float,
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["thresholds"][field] = value
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(QG2_V3_SELECTOR_MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(QG2_V3_SELECTOR_EVALUATION_ENV, "1")

    selected, telemetry = prepare_qg2_v3_selector_request_from_environment(
        request
    )

    assert selected is request
    assert telemetry["proof_tail_selector_action"] == "Q0"
    assert telemetry["proof_tail_selector_decision_reason"] == (
        "invalid_thresholds"
    )


def test_qg2_v4_selector_can_install_separately_frozen_label_gat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    _enable_qg2(manifest, request)
    monkeypatch.setenv(QG2_V3_SELECTOR_MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(QG2_V3_SELECTOR_EVALUATION_ENV, "1")
    selected, telemetry = prepare_qg2_v3_selector_request_from_environment(
        request
    )
    assert telemetry["proof_tail_selector_action"] == "QG2"
    assert selected.proof_queue_policy_id == "QG2"
    assert selected.proof_tail_gat_enabled
    assert selected.guidance_hints is not None
    assert len(selected.guidance_hints.label_state_coefficients) == 15
    assert selected.config_hash != request.config_hash


def test_qg2_v4_selector_binds_tree_branch_and_cut_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = _request()
    tasks = base.data.task_ids
    cut_id = "qg2_v4_sri_001"
    request = replace(
        base,
        true_duals=JourneyDuals(
            cover=base.true_duals.cover,
            fleet_limit=base.true_duals.fleet_limit,
            cuts={cut_id: 0.75},
        ),
        pricing_lifecycle_scope="tree_node",
        branch_context=BranchContext((
            PairBranchDecision(tasks[0], tasks[1], SAME_JOURNEY),
        )),
        cut_context=CutContext((
            subset_row_cut(cut_id, tasks[:3], divisor=2),
        )),
    )
    manifest = _manifest(tmp_path, request)
    _enable_qg2(manifest, request)
    monkeypatch.setenv(QG2_V3_SELECTOR_MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(QG2_V3_SELECTOR_EVALUATION_ENV, "1")

    selected, telemetry = prepare_qg2_v3_selector_request_from_environment(
        request
    )
    accepted, audit = validate_pricing_ordering_hints(selected)

    assert telemetry["proof_tail_selector_action"] == "QG2"
    assert accepted is not None and audit["guidance_accepted"]
    expected = CanonicalSolveBindingV2.from_backend_request(selected)
    assert accepted.binding_hash == expected.binding_hash
    assert expected.branch_context_hash != CanonicalSolveBindingV2.from_backend_request(
        base
    ).branch_context_hash
    assert expected.full_cut_context_hash != CanonicalSolveBindingV2.from_backend_request(
        base
    ).full_cut_context_hash


def test_qg2_v4_ranker_hash_drift_returns_literal_q0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    _selector_path, ranker_path = _enable_qg2(manifest, request)
    with ranker_path.open("ab") as stream:
        stream.write(b"hash-drift")
    monkeypatch.setenv(QG2_V3_SELECTOR_MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(QG2_V3_SELECTOR_EVALUATION_ENV, "1")

    selected, telemetry = prepare_qg2_v3_selector_request_from_environment(
        request
    )

    assert selected is request
    assert telemetry["proof_tail_selector_action"] == "Q0"
    assert telemetry["proof_tail_selector_decision_reason"].startswith(
        "qg2_ranker_load_failed:"
    )
    assert request.proof_queue_policy_id == "Q0"
    assert request.guidance_hints is None


def test_qg2_v4_zero_ranker_potential_returns_literal_q0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    _enable_qg2(manifest, request, zero_ranker=True)
    monkeypatch.setenv(QG2_V3_SELECTOR_MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(QG2_V3_SELECTOR_EVALUATION_ENV, "1")

    selected, telemetry = prepare_qg2_v3_selector_request_from_environment(
        request
    )

    assert selected is request
    assert telemetry["proof_tail_selector_action"] == "Q0"
    assert telemetry["proof_tail_selector_decision_reason"] == (
        "qg2_ranker_zero_potential"
    )
    assert request.proof_queue_policy_id == "Q0"
    assert request.guidance_hints is None


def test_qg2_v4_ood_returns_q0_before_loading_any_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["checkpoint_path"] = str(tmp_path / "missing_selector.pt")
    payload["checkpoint_sha256"] = "f" * 64
    payload["feature_envelope"]["context_min"] = [
        0.0 for _ in payload["feature_envelope"]["context_min"]
    ]
    payload["feature_envelope"]["context_max"] = [
        0.0 for _ in payload["feature_envelope"]["context_max"]
    ]
    payload["feature_envelope"]["relative_margin"] = 0.0
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(QG2_V3_SELECTOR_MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(QG2_V3_SELECTOR_EVALUATION_ENV, "1")

    selected, telemetry = prepare_qg2_v3_selector_request_from_environment(
        request
    )

    assert selected is request
    assert telemetry["proof_tail_selector_action"] == "Q0"
    assert telemetry["proof_tail_selector_ood"]
    assert "outside_envelope" in telemetry[
        "proof_tail_selector_decision_reason"
    ]


def test_qg2_v3_selector_hash_drift_fails_before_inference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["runtime_implementation_hash"] = "drift"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(QG2_V3_SELECTOR_MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(QG2_V3_SELECTOR_EVALUATION_ENV, "1")
    with pytest.raises(ValueError, match="runtime_implementation_drift"):
        prepare_qg2_v3_selector_request_from_environment(request)
