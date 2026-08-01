from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest
import torch

from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
    BackendPricingRequest,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.native_bidirectional_hybrid import (
    NativeBidirectionalRootPartialHybridBackend,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
    NativeRcsppInprocessBackend,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.guidance.bidirectional_gate_gat import (
    BIDIRECTIONAL_GATE_GAT_POLICY_ID,
    BidirectionalPrepassGAT,
    build_bidirectional_gate_features,
    checkpoint_payload,
)
from lunar_ice_bpc.guidance.bidirectional_gate_runtime import (
    BidirectionalGateDecision,
    bidirectional_gate_runtime_implementation_hash,
    decide_bidirectional_prepass_from_environment,
    record_bidirectional_prepass_outcome,
)
from lunar_ice_bpc.guidance.proof_queue_gat import (
    build_proof_queue_gat_features,
)


ROOT = Path(__file__).resolve().parents[1]


def _request() -> BackendPricingRequest:
    path = (
        ROOT
        / "data/instances/lunar_ice_sp50_005/"
        "instance_001_logical_graph.json"
    )
    data = load_lunar_ice_data(json.loads(path.read_text(encoding="utf-8")))
    return BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(
            cover={task_id: 0.1 for task_id in data.task_ids}
        ),
        mode="exact_proof",
        objective_mode="official",
        pricing_lifecycle_scope="root_cg",
        rmp_iteration_id="root-1",
        instance_hash=data.instance_content_hash,
        config_hash="config-hash",
        engine_hash="engine-hash",
    )


def _manifest(tmp_path: Path, request: BackendPricingRequest) -> Path:
    features = build_bidirectional_gate_features(
        request.data,
        cover_duals=request.true_duals.cover,
        fleet_dual=request.true_duals.fleet_limit,
        round_index=1,
    )
    model = BidirectionalPrepassGAT(
        node_input_dim=len(features.node_features[0]),
        context_input_dim=len(features.context_features),
    )
    for parameter in model.parameters():
        parameter.data.zero_()
    checkpoint = tmp_path / "gate.pt"
    torch.save(
        checkpoint_payload(
            model,
            metadata={"training_data_hash": "training-hash"},
        ),
        checkpoint,
    )
    manifest = {
        "policy_id": BIDIRECTIONAL_GATE_GAT_POLICY_ID,
        "runtime_implementation_hash": (
            bidirectional_gate_runtime_implementation_hash()
        ),
        "checkpoint_path": str(checkpoint),
        "checkpoint_sha256": hashlib.sha256(
            checkpoint.read_bytes()
        ).hexdigest(),
        "training_data_hash": "training-hash",
        "allowed_scales": [request.data.scale],
        "allowed_exact_engine_hashes": [request.engine_hash],
        "evaluation_authorized": True,
        "deployment_authorized": False,
        "torch_num_threads": 1,
        "feature_envelope": {
            "context_min": list(features.context_features),
            "context_max": list(features.context_features),
            "node_max_abs": max(
                abs(value)
                for row in features.node_features
                for value in row
            ),
            "edge_max_abs": max(
                abs(value)
                for row in features.edge_features
                for value in row
            ),
            "relative_margin": 0.0,
        },
        "calibration": {
            "gate_pass": True,
            "failure_probability_threshold": 0.49,
            "expected_waste_threshold_sec": 0.0,
        },
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_bidirectional_gate_model_outputs_are_finite() -> None:
    request = _request()
    features = build_bidirectional_gate_features(
        request.data,
        cover_duals=request.true_duals.cover,
        round_index=1,
    )
    model = BidirectionalPrepassGAT(
        node_input_dim=len(features.node_features[0]),
        context_input_dim=len(features.context_features),
    )
    output = model(**features.to_tensors())
    assert torch.isfinite(output["failure_probability"])
    assert torch.isfinite(output["conditional_wasted_time_sec"])
    assert 0.0 <= float(output["failure_probability"].detach()) <= 1.0
    assert float(output["conditional_wasted_time_sec"].detach()) >= 0.0


def test_runtime_is_fail_closed_and_valid_manifest_can_skip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _request()
    assert not decide_bidirectional_prepass_from_environment(
        request
    ).skips_prepass
    manifest = _manifest(tmp_path, request)
    monkeypatch.setenv(
        "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT_MANIFEST", str(manifest)
    )
    monkeypatch.setenv(
        "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT_EVALUATION_MODE", "1"
    )
    decision = decide_bidirectional_prepass_from_environment(request)
    assert decision.skips_prepass
    assert decision.reason == "calibrated_skip"
    record_bidirectional_prepass_outcome(
        request, accepted=None, skipped=True
    )
    refresh = decide_bidirectional_prepass_from_environment(
        replace(request, rmp_iteration_id="root-2")
    )
    assert not refresh.skips_prepass
    assert refresh.reason == "refresh_after_skip"

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["runtime_implementation_hash"] = "bad"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    fallback = decide_bidirectional_prepass_from_environment(request)
    assert not fallback.skips_prepass
    assert fallback.reason.startswith("fail_closed:")


def test_hybrid_skip_uses_unchanged_exact_fallback_without_midpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    backend = NativeBidirectionalRootPartialHybridBackend()
    expected = NativeRcsppInprocessBackend().solve(request)
    monkeypatch.setattr(
        "lunar_ice_bpc.exact.bpc.pricing.backends."
        "native_bidirectional_hybrid."
        "decide_bidirectional_prepass_from_environment",
        lambda _request: BidirectionalGateDecision(
            action="SKIP",
            reason="calibrated_skip",
            failure_probability=0.99,
            expected_wasted_time_sec=2.0,
        ),
    )
    monkeypatch.setattr(
        backend,
        "_p0v4_fallback_backend",
        lambda _request: (
            NativeRcsppInprocessBackend(),
            "native_rcspp_inprocess",
        ),
    )
    result = backend.solve(request)
    assert result.engine_status == expected.engine_status
    assert result.proved_no_rc_below == expected.proved_no_rc_below
    assert result.columns == expected.columns
    assert not result.telemetry[
        "bidirectional_midpoint_hybrid_attempted"
    ]
    assert result.telemetry[
        "bidirectional_midpoint_hybrid_fallback_reason"
    ] == "gat_predicted_midpoint_failure"
    assert result.telemetry["bidirectional_gate_gat_action"] == "SKIP"
    assert not result.telemetry.get("can_certify_no_negative", False)
