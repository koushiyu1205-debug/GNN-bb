from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import torch

from lunar_ice_bpc.exact.bpc.guidance.contracts import (
    validate_pricing_ordering_hints,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
    BackendPricingRequest,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
    _maybe_attach_environment_guidance,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.guidance.proof_queue_gat import (
    ProofQueuePotentialGAT,
    build_proof_queue_gat_features,
    checkpoint_payload,
    normalized_arc_potentials,
    proof_queue_arc_ranking_loss,
)
from lunar_ice_bpc.guidance.proof_queue_gat_runtime import (
    PROOF_QUEUE_GAT_RUNTIME_POLICY_ID,
    prepare_proof_queue_gat_request_from_environment,
    proof_queue_gat_runtime_implementation_hash,
)


ROOT = Path(__file__).resolve().parents[1]


def _data():
    path = (
        ROOT
        / "data/instances/lunar_ice_sp50_005/"
        "instance_001_logical_graph.json"
    )
    return load_lunar_ice_data(json.loads(path.read_text(encoding="utf-8")))


def _request():
    data = _data()
    return BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(
            cover={
                task_id: float(index + 1)
                for index, task_id in enumerate(data.task_ids)
            },
            fleet_limit=0.25,
        ),
        mode="exact_proof",
        objective_mode="official",
        proof_queue_policy_id="Q0",
        instance_hash=data.instance_content_hash,
        config_hash="config-hash",
        engine_hash="engine-hash",
    )


def _manifest(tmp_path: Path, request) -> Path:
    model = ProofQueuePotentialGAT()
    checkpoint = tmp_path / "model.pt"
    torch.save(
        checkpoint_payload(
            model,
            metadata={"training_data_hash": "training-hash"},
        ),
        checkpoint,
    )
    features = build_proof_queue_gat_features(
        request.data,
        cover_duals=request.true_duals.cover,
        fleet_dual=request.true_duals.fleet_limit,
    )
    context = features.context_features
    payload = {
        "runtime_policy_id": PROOF_QUEUE_GAT_RUNTIME_POLICY_ID,
        "runtime_implementation_hash": (
            proof_queue_gat_runtime_implementation_hash()
        ),
        "checkpoint_path": str(checkpoint),
        "checkpoint_sha256": hashlib.sha256(
            checkpoint.read_bytes()
        ).hexdigest(),
        "training_data_hash": "training-hash",
        "allowed_scales": [int(request.data.scale)],
        "allowed_exact_engine_hashes": [request.engine_hash],
        "allowed_exact_config_hashes": [request.config_hash],
        "evaluation_authorized": True,
        "evaluation_force_qg1": True,
        "deployment_authorized": False,
        "torch_num_threads": 1,
        "feature_envelope": {
            "context_min": list(context),
            "context_max": list(context),
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
        "calibration": {"gate_pass": False},
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_proof_queue_gat_tensorization_and_loss_are_finite() -> None:
    request = _request()
    features = build_proof_queue_gat_features(
        request.data,
        cover_duals=request.true_duals.cover,
        fleet_dual=request.true_duals.fleet_limit,
    )
    model = ProofQueuePotentialGAT()
    output = model(**features.to_tensors())
    assert output["arc_scores"].shape == (
        len(features.arc_candidate_ids),
    )
    normalized = normalized_arc_potentials(output["arc_scores"])
    assert torch.isfinite(normalized).all()
    assert float(normalized.abs().max().detach().item()) == pytest.approx(1.0)
    loss = proof_queue_arc_ranking_loss(
        output["arc_scores"], torch.linspace(-1.0, 1.0, len(normalized))
    )
    assert torch.isfinite(loss)


def test_evaluation_runtime_installs_only_qg1_ordering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    monkeypatch.setenv(
        "LUNAR_ICE_PROOF_QUEUE_GAT_MANIFEST", str(manifest)
    )
    monkeypatch.setenv(
        "LUNAR_ICE_PROOF_QUEUE_GAT_EVALUATION_MODE", "1"
    )
    enriched, diagnostics = (
        prepare_proof_queue_gat_request_from_environment(request)
    )
    accepted, audit = validate_pricing_ordering_hints(enriched)
    assert diagnostics["proof_queue_gat_action"] == "QG1"
    assert enriched.proof_queue_policy_id == "QG1"
    assert enriched.guidance_mode == "task_arc"
    assert accepted is not None
    assert audit["guidance_accepted"]
    assert len(accepted.arc_priorities) > 0
    assert not accepted.task_priorities
    assert request.proof_queue_policy_id == "Q0"
    assert request.guidance_hints is None


def test_runtime_ood_and_bad_hash_fall_back_to_exact_p0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["feature_envelope"]["node_max_abs"] = 0.0
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(
        "LUNAR_ICE_PROOF_QUEUE_GAT_MANIFEST", str(manifest)
    )
    monkeypatch.setenv(
        "LUNAR_ICE_PROOF_QUEUE_GAT_EVALUATION_MODE", "1"
    )
    unchanged, diagnostics = (
        prepare_proof_queue_gat_request_from_environment(request)
    )
    assert unchanged is request
    assert diagnostics["proof_queue_gat_action"] == "NOOP"
    assert diagnostics["proof_queue_gat_ood"]

    payload["runtime_implementation_hash"] = "bad"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    fallback = _maybe_attach_environment_guidance(request)
    assert fallback.proof_queue_policy_id == "Q0"
    assert fallback.guidance_hints is None
    lifecycle = dict(fallback.guidance_lifecycle_telemetry)
    assert lifecycle["bypassed_before_import"]
    assert "fail_closed" in lifecycle["bypass_reason"]
