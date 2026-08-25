from __future__ import annotations

from dataclasses import replace
import hashlib
import importlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lunar_ice_bpc.exact.bpc.pricing.backends.base import BackendPricingRequest
from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import _native_request_payload
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.guidance.frontier_gat_qd1_runtime_v7 import (
    EVALUATION_ENV,
    MANIFEST_ENV,
    MANIFEST_SCHEMA_V1,
    RUNTIME_POLICY_V7,
    prepare_frontier_gat_qd1_request_from_environment,
)
from lunar_ice_bpc.guidance.frontier_gat_qd1_v7 import (
    CONTEXT_FEATURE_NAMES,
    EDGE_FEATURE_NAMES,
    FRONTIER_BUNDLE_SCHEMA_V1,
    FRONTIER_FEATURE_SCHEMA_V1,
    FRONTIER_GRAPH_SCHEMA_V1,
    MODEL_SEEDS,
    NODE_FEATURE_NAMES,
    build_frontier_gat_model,
    bundle_sha256,
    canonical_json_bytes,
    parameter_count,
    portable_seed_payload,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
    qg2_exact_action_policy_hash_from_request,
)
from scripts.p0v5_native_frontier_gat_qd1_v7_common import (
    collapse_matched_blocks,
    deterministic_seed,
)
def _request(scale: int = 30, lifecycle: str = "root_cg") -> BackendPricingRequest:
    path = ROOT / (
        f"data/instances/lunar_ice_sp50_{scale:03d}/"
        "instance_001_logical_graph.json"
    )
    data = load_lunar_ice_data(json.loads(path.read_text(encoding="utf-8")))
    return BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(
            cover={task_id: 0.0 for task_id in data.task_ids}
        ),
        mode="exact_proof",
        objective_mode="official",
        pricing_lifecycle_scope=lifecycle,
        proof_queue_policy_id="Q0",
        proof_tail_fallback_context=True,
        proof_tail_active_column_count=4,
        proof_tail_round_index=2,
        proof_tail_dual_delta_l1=0.25,
        proof_tail_v5_midpoint_wall_sec=0.5,
        instance_hash=data.instance_content_hash,
        config_hash="config-v7-test",
        engine_hash="engine-v7-test",
    )


def _normalization():
    return {
        "node": {
            "mean": [0.0] * len(NODE_FEATURE_NAMES),
            "scale": [1.0] * len(NODE_FEATURE_NAMES),
            "minimum": [-1.0e6] * len(NODE_FEATURE_NAMES),
            "maximum": [1.0e6] * len(NODE_FEATURE_NAMES),
        },
        "edge": {
            "mean": [0.0] * len(EDGE_FEATURE_NAMES),
            "scale": [1.0] * len(EDGE_FEATURE_NAMES),
            "minimum": [-1.0e6] * len(EDGE_FEATURE_NAMES),
            "maximum": [1.0e6] * len(EDGE_FEATURE_NAMES),
        },
        "context": {
            "mean": [0.0] * len(CONTEXT_FEATURE_NAMES),
            "scale": [1.0] * len(CONTEXT_FEATURE_NAMES),
            "minimum": [-1.0e6] * len(CONTEXT_FEATURE_NAMES),
            "maximum": [1.0e6] * len(CONTEXT_FEATURE_NAMES),
        },
    }


def _models():
    import torch

    rows = []
    for seed in MODEL_SEEDS:
        torch.manual_seed(seed)
        model = build_frontier_gat_model().double().eval()
        assert parameter_count(model) < 15_000
        rows.append((seed, model))
    return rows


def _bundle(request: BackendPricingRequest) -> dict:
    payload = {
        "schema_version": FRONTIER_BUNDLE_SCHEMA_V1,
        "graph_schema_version": FRONTIER_GRAPH_SCHEMA_V1,
        "feature_schema_version": FRONTIER_FEATURE_SCHEMA_V1,
        "feature_names": {
            "node": list(NODE_FEATURE_NAMES),
            "edge": list(EDGE_FEATURE_NAMES),
            "context": list(CONTEXT_FEATURE_NAMES),
        },
        "normalization": _normalization(),
        "thresholds_by_scale": {
            str(scale): {
                "minimum_benefit_probability": 0.6,
                "maximum_adverse_probability": 0.1,
                "minimum_expected_gain": 0.02,
                "adverse_penalty": 0.5,
                "maximum_disagreement": 0.15,
            }
            for scale in (30, 50)
        },
        "calibration_by_scale": {
            str(scale): {
                "benefit": {"kind": "platt", "a": 1.0, "b": 0.0},
                "adverse": {"kind": "platt", "a": 1.0, "b": 0.0},
                "gain_scale": 1.0,
            }
            for scale in (30, 50)
        },
        "layer_norm_epsilon": 1.0e-5,
        "models": [
            portable_seed_payload(model, seed=seed)
            for seed, model in _models()
        ],
        "bindings": {
            "engine_hashes": [request.engine_hash],
            "selected_exact_config_sha256": "a" * 64,
            "action_policy_hashes": [
                qg2_exact_action_policy_hash_from_request(request)
            ],
        },
    }
    payload["bundle_sha256"] = bundle_sha256(payload)
    return payload


def _write_manifest(tmp_path: Path, request: BackendPricingRequest) -> Path:
    bundle = _bundle(request)
    bundle_path = tmp_path / "frontier_bundle.json"
    bundle_path.write_bytes(canonical_json_bytes(bundle) + b"\n")
    manifest = {
        "schema_version": MANIFEST_SCHEMA_V1,
        "runtime_policy": RUNTIME_POLICY_V7,
        "action_universe": ["CONTINUE_Q0", "SWITCH_QD1"],
        "forced_veto_actions": ["QB1", "QGR1"],
        "probe_boundary": 4096,
        "allowed_scales": [30, 50],
        "model_kind": "frontier_interaction_gat",
        "message_passing_required": True,
        "pricing_lifecycle_authority": "root_cg_only",
        "portable_bundle_path": bundle_path.name,
        "portable_bundle_file_sha256": hashlib.sha256(
            bundle_path.read_bytes()
        ).hexdigest(),
        "allowed_exact_engine_hashes": [request.engine_hash],
        "selected_exact_config_sha256": "a" * 64,
        "allowed_exact_action_policy_hashes": [
            qg2_exact_action_policy_hash_from_request(request)
        ],
        "development_e2e_authorized": True,
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


@pytest.mark.parametrize("scale,lifecycle", ((5, "root_cg"), (30, "tree_node")))
def test_v7_small_scale_and_tree_return_identical_q0_before_manifest(
    monkeypatch, scale, lifecycle,
):
    request = _request(scale=scale, lifecycle=lifecycle)
    monkeypatch.setenv(MANIFEST_ENV, "/must/not/be/read.json")
    selected, telemetry = prepare_frontier_gat_qd1_request_from_environment(request)
    assert selected is request
    assert telemetry["proof_tail_frontier_bypassed_before_manifest"] is True
    assert telemetry["proof_tail_frontier_graph_build_count"] == 0
    assert telemetry["proof_tail_frontier_model_call_count"] == 0
    assert "torch" not in sys.modules or telemetry["proof_tail_frontier_torch_import_count"] == 0


def test_v7_valid_manifest_installs_portable_bundle_without_torch_inference(
    monkeypatch, tmp_path,
):
    request = _request()
    manifest = _write_manifest(tmp_path, request)
    monkeypatch.setenv(MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(EVALUATION_ENV, "1")
    selected, telemetry = prepare_frontier_gat_qd1_request_from_environment(request)
    assert selected is not request
    assert selected.proof_queue_policy_id == "Q0"
    assert selected.proof_tail_frontier_probe_mode == "learned"
    assert selected.proof_tail_frontier_probe_boundary == 4096
    assert selected.proof_tail_frontier_gat_bundle["thresholds"] == (
        selected.proof_tail_frontier_gat_bundle["thresholds_by_scale"]["30"]
    )
    assert selected.proof_tail_frontier_gat_bundle["calibration"] == (
        selected.proof_tail_frontier_gat_bundle["calibration_by_scale"]["30"]
    )
    assert telemetry["proof_tail_frontier_runtime_action"] == "DEFER_TO_NATIVE_PROBE"
    assert telemetry["proof_tail_frontier_model_call_count"] == 0


def test_v7_manifest_or_bundle_drift_fails_closed_with_identity(monkeypatch, tmp_path):
    request = _request()
    manifest = _write_manifest(tmp_path, request)
    payload = json.loads(manifest.read_text())
    payload["forced_veto_actions"] = ["QGR1"]
    manifest.write_text(json.dumps(payload))
    monkeypatch.setenv(MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(EVALUATION_ENV, "1")
    selected, telemetry = prepare_frontier_gat_qd1_request_from_environment(request)
    assert selected is request
    assert telemetry["proof_tail_frontier_runtime_action"] == "CONTINUE_Q0"
    assert "fail_closed" in telemetry["proof_tail_frontier_runtime_reason"]


def test_v7_dynamic_request_config_hash_is_not_used_as_deployable_allowlist(
    monkeypatch, tmp_path,
):
    request = _request()
    manifest = _write_manifest(tmp_path, request)
    changed = replace(request, config_hash="another-rmp-round-binding")
    monkeypatch.setenv(MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(EVALUATION_ENV, "1")
    selected, _telemetry = prepare_frontier_gat_qd1_request_from_environment(changed)
    assert selected is not changed
    assert selected.proof_tail_frontier_probe_mode == "learned"


def test_v7_force_modes_reach_native_payload_without_qgr1_or_ranker():
    request = replace(
        _request(),
        proof_tail_frontier_probe_mode="force_qd1",
    )
    payload = _native_request_payload(request)
    assert payload["proof_queue_policy_id"] == "Q0"
    assert payload["proof_queue_frontier_probe_mode"] == "force_qd1"
    assert payload["proof_queue_frontier_probe_boundary"] == 4096
    assert payload["proof_queue_frontier_gat_bundle"] is None
    assert "ranker" not in json.dumps(payload).lower()


def test_python_and_cpp_portable_frontier_gat_forward_match():
    import torch

    native_path = ROOT / "build/native-spprc-frontier-gat-v7"
    sys.path.insert(0, str(native_path))
    try:
        native = importlib.import_module("lunar_spprc_native")
    finally:
        sys.path.remove(str(native_path))
    generator = torch.Generator().manual_seed(260817)
    node_features = torch.randn((64, 16), generator=generator, dtype=torch.float64)
    edges = []
    for node in range(64):
        edges.append({"source": node, "target": node, "features": [1.0] + [0.0] * 9})
        if node % 8 != 7:
            edges.append({"source": node, "target": node + 1, "features": [0.0, 0.0, 1.0] + [0.0] * 7})
            edges.append({"source": node + 1, "target": node, "features": [0.0, 0.0, 1.0] + [0.0] * 7})
    edge_features = torch.tensor([row["features"] for row in edges], dtype=torch.float64)
    edge_index = torch.tensor(
        [[row["source"] for row in edges], [row["target"] for row in edges]],
        dtype=torch.long,
    )
    context_features = torch.randn((28,), generator=generator, dtype=torch.float64)
    request = _request()
    bundle = _bundle(request)
    selected_bundle = dict(bundle)
    selected_bundle["thresholds"] = bundle["thresholds_by_scale"]["30"]
    selected_bundle["calibration"] = bundle["calibration_by_scale"]["30"]
    graph = {
        "node_features": node_features.tolist(),
        "edges": edges,
        "context_features": context_features.tolist(),
    }
    models = _models()
    for index, (_seed, model) in enumerate(models):
        with torch.inference_mode():
            output = model(
                node_features=node_features,
                edge_index=edge_index,
                edge_features=edge_features,
                context_features=context_features,
            )
        expected = [float(output[name]) for name in (
            "p_benefit", "positive_gain", "p_adverse"
        )]
        actual = list(native.frontier_gat_forward(selected_bundle, graph, index))
        assert max(abs(lhs - rhs) for lhs, rhs in zip(expected, actual)) <= 1.0e-5


def test_v7_censor_collapse_requires_two_comparable_blocks():
    rows = []
    for block, q0_status, arm_status in (
        (0, "COMPLETE", "COMPLETE"),
        (1, "COMPLETE", "TIMEOUT"),
        (2, "TIMEOUT", "TIMEOUT"),
    ):
        for arm, status, wall in (
            ("QPF0", q0_status, 10.0), ("QPD1", arm_status, 8.0)
        ):
            rows.append({
                "context_id": "ctx", "block_id": f"b{block}", "arm": arm,
                "status": status, "wall_seconds": wall, "cap_seconds": 20.0,
                "correctness_redlines": [],
                "metadata": {"scale": 50, "instance_hash": "instance"},
            })
    value = collapse_matched_blocks(rows)[0]
    assert value["determined"] is True
    assert value["comparable_block_count"] == 2
    assert value["adverse"] is True
    assert value["resource_censor_positive"] is True
    assert deterministic_seed("pilot", 30, 1) == deterministic_seed("pilot", 30, 1)
