from __future__ import annotations

from dataclasses import replace
import builtins
import hashlib
import json
from pathlib import Path
import sys

import pytest
import torch

from lunar_ice_bpc.exact.bpc.pricing.backends.base import BackendPricingRequest
from lunar_ice_bpc.exact.core.branching import (
    BranchContext,
    PairBranchDecision,
)
from lunar_ice_bpc.exact.core.cuts import CutContext, canonical_subset_row_cut
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.guidance.interaction_gat_queue_gates_v2 import (
    assess_gat_calibration,
    assess_gat_heldout_advantage,
    assess_v2_arm_scale_admission,
    measured_v2_portfolio_oracle,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v2 import (
    INTERACTION_GAT_EVALUATION_ENV,
    INTERACTION_GAT_MANIFEST_ENV,
    INTERACTION_GAT_MANIFEST_SCHEMA_V1,
    INTERACTION_GAT_RUNTIME_POLICY_V2,
    interaction_gat_runtime_implementation_hash,
    prepare_root_interaction_gat_request_from_environment,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (
    INTERACTION_CHECKPOINT_SCHEMA_V1,
    INTERACTION_CONTEXT_DIM,
    INTERACTION_EDGE_DIM,
    INTERACTION_ENVELOPE_SCHEMA_V1,
    INTERACTION_FEATURE_SCHEMA_V2,
    INTERACTION_GRAPH_SCHEMA_V1,
    INTERACTION_INPUT_PARITY_CONTRACT_V1,
    INTERACTION_NODE_DIM,
    InteractionGATSelector,
    InteractionLinearControl,
    InteractionMLPControl,
    build_interaction_graph,
    fit_interaction_envelope,
    fit_interaction_normalization,
    interaction_graph_builder_hash,
    interaction_parameter_count,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (
    MatchedContextOutcome,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_v1 import (
    PORTFOLIO_ACTION_UNIVERSE,
    PORTFOLIO_ARMS,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
    qg2_exact_action_policy_hash_from_request,
)
from lunar_ice_bpc.guidance.qgr1_supervision import QGR1WeightedPair
import lunar_ice_bpc.guidance.qgr1_residual_supervision_v2 as residual


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _request(scale: int = 30, *, lifecycle: str = "root_cg"):
    path = (
        ROOT / f"data/instances/lunar_ice_sp50_{scale:03d}"
        / "instance_001_logical_graph.json"
    )
    data = load_lunar_ice_data(json.loads(path.read_text(encoding="utf-8")))
    sets = (
        (data.task_ids[0], data.task_ids[1], data.task_ids[2]),
        (data.task_ids[0], data.task_ids[1]),
        (data.task_ids[0], data.task_ids[3]),
        (data.task_ids[2], data.task_ids[3]),
    )
    return BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(
            cover={task_id: float(index % 7) for index, task_id in enumerate(data.task_ids)},
            fleet_limit=0.25,
        ),
        mode="exact_proof", objective_mode="official",
        pricing_lifecycle_scope=lifecycle,
        proof_queue_policy_id="Q0",
        proof_tail_fallback_context=True,
        proof_tail_active_column_count=len(sets),
        proof_tail_active_task_sets=sets,
        proof_tail_active_column_signature_hashes=tuple(
            f"{index:064x}" for index in range(len(sets))
        ),
        proof_tail_round_index=12,
        proof_tail_previous_queue_policy_id="Q0",
        proof_tail_previous_proof_wall_sec=13.5,
        proof_tail_previous_processed_labels=125_000,
        proof_tail_previous_dominance_candidate_checks=2_000_000,
        proof_tail_previous_dominance_wall_sec=4.25,
        proof_tail_previous_max_visited_bucket_size=31_000,
        proof_tail_dual_delta_l1=2.25,
        proof_tail_v5_midpoint_wall_sec=0.4,
        proof_tail_v5_midpoint_reason="midpoint_no_audited_negative",
        instance_hash=data.instance_content_hash,
        config_hash="exact-config-hash",
        engine_hash="exact-engine-hash",
    )


def _write_manifest(tmp_path, request, *, selected="QD1", model_kind="gat"):
    features = build_interaction_graph(request)
    normalization = fit_interaction_normalization([features])
    model = InteractionGATSelector(normalization)
    selected_index = PORTFOLIO_ARMS.index(selected)
    with torch.no_grad():
        model.arm_heads.head.weight.zero_()
        model.arm_heads.head.bias.zero_()
        for index in range(len(PORTFOLIO_ARMS)):
            offset = 3 * index
            model.arm_heads.head.bias[offset:offset + 3] = torch.tensor([-10.0, -10.0, 10.0])
        offset = 3 * selected_index
        model.arm_heads.head.bias[offset:offset + 3] = torch.tensor([10.0, 1.0, -10.0])
    checkpoint = tmp_path / "interaction_gat.pt"
    torch.save({
        "schema_version": INTERACTION_CHECKPOINT_SCHEMA_V1,
        "feature_schema_version": INTERACTION_FEATURE_SCHEMA_V2,
        "graph_schema_version": INTERACTION_GRAPH_SCHEMA_V1,
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "model_kind": model_kind,
        "message_passing_required": True,
        "controls_candidate_authorized": False,
        "candidate_authorized": True,
        "action_universe": list(PORTFOLIO_ACTION_UNIVERSE),
        "normalization": normalization,
        "state_dict": model.state_dict(),
        "activation_authority": False,
        "deployment_authorized": False,
    }, checkpoint)
    payload = {
        "schema_version": INTERACTION_GAT_MANIFEST_SCHEMA_V1,
        "runtime_policy_id": INTERACTION_GAT_RUNTIME_POLICY_V2,
        "runtime_implementation_hash": interaction_gat_runtime_implementation_hash(),
        "graph_builder_hash": interaction_graph_builder_hash(),
        "graph_schema_version": INTERACTION_GRAPH_SCHEMA_V1,
        "feature_schema_version": INTERACTION_FEATURE_SCHEMA_V2,
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "action_universe": list(PORTFOLIO_ACTION_UNIVERSE),
        "fallback_action": "Q0",
        "allowed_scales": [30, 50],
        "lifecycle_authority": ["root_cg"],
        "arm_scale_mask": {"QGR1": [], "QD1": [30, 50], "QB1": [30, 50]},
        "forced_veto_arms": ["QGR1"],
        "forced_veto_arms_by_scale": {"30": [], "50": []},
        "model_kind": model_kind,
        "message_passing_required": True,
        "controls_candidate_authorized": False,
        "selector_checkpoint_path": str(checkpoint),
        "selector_checkpoint_sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        "feature_envelope": fit_interaction_envelope([features]),
        "thresholds": {
            "minimum_benefit_probability": 0.8,
            "minimum_expected_gain": 0.01,
            "maximum_adverse_probability": 0.1,
            "risk_penalty": 0.5,
        },
        "allowed_exact_engine_hashes": [request.engine_hash],
        "allowed_exact_config_hashes": [request.config_hash],
        "allowed_exact_action_policy_hashes": [qg2_exact_action_policy_hash_from_request(request)],
        "source_freeze_sha256": "test-source-freeze",
        "native_binary_sha256": "test-native-binary",
        "torch_num_threads": 1,
        "development_e2e_authorized": True,
        "deployment_authorized": False,
        "development_only": True,
        "production_switch_authorized": False,
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    return manifest


def test_interaction_graph_is_sparse_deterministic_bidirectional_and_self_loop():
    request = _request()
    left = build_interaction_graph(request)
    right = build_interaction_graph(request)
    assert left == right
    assert left.schema_version == INTERACTION_FEATURE_SCHEMA_V2
    assert left.graph_schema_version == INTERACTION_GRAPH_SCHEMA_V1
    assert len(left.node_features) == request.data.scale
    assert all(len(row) == INTERACTION_NODE_DIM for row in left.node_features)
    assert all(len(row) == INTERACTION_EDGE_DIM for row in left.edge_features)
    assert len(left.context_features) == INTERACTION_CONTEXT_DIM
    edges = set(zip(*left.edge_index, strict=True))
    assert all((index, index) in edges for index in range(request.data.scale))
    assert all((target, source) in edges for source, target in edges)
    assert len(edges) < request.data.scale * request.data.scale


def test_interaction_cooccurrence_matches_naive_reference():
    request = _request()
    features = build_interaction_graph(request)
    index = {task_id: i for i, task_id in enumerate(features.task_ids)}
    by_edge = {
        (source, target): row
        for source, target, row in zip(
            features.edge_index[0], features.edge_index[1], features.edge_features,
            strict=True,
        )
    }
    left, right = request.data.task_ids[:2]
    naive = sum(
        left in task_set and right in task_set
        for task_set in request.proof_tail_active_task_sets
    )
    assert by_edge[(index[left], index[right])][0] == pytest.approx(torch.log1p(torch.tensor(float(naive))).item())


def test_forced_branch_and_cut_edges_and_flags():
    request = _request()
    a, b, c = request.data.task_ids[:3]
    cut = canonical_subset_row_cut((a, b, c))
    request = replace(
        request,
        branch_context=BranchContext((PairBranchDecision(a, b, "same_journey"),)),
        cut_context=CutContext((cut,)),
        true_duals=replace(request.true_duals, cuts={cut.cut_id: 0.75}),
    )
    features = build_interaction_graph(request)
    node = {task_id: index for index, task_id in enumerate(features.task_ids)}
    rows = {
        (source, target): values
        for source, target, values in zip(*features.edge_index, features.edge_features, strict=True)
    }
    assert (node[a], node[b]) in rows and (node[b], node[a]) in rows
    assert rows[(node[a], node[b])][10] == 1.0
    assert rows[(node[a], node[b])][12] > 0.0
    assert rows[(node[a], node[b])][13] == pytest.approx(0.75)


def test_non_q0_previous_trajectory_is_missing():
    request = replace(_request(), proof_tail_previous_queue_policy_id="QD1")
    features = build_interaction_graph(request)
    # Last six V1 context values are the three Q0-only values and masks.
    assert features.context_features[-6:] == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


def test_model_parameter_cap_controls_and_permutation_invariance():
    features = build_interaction_graph(_request())
    normalization = fit_interaction_normalization([features])
    gat = InteractionGATSelector(normalization).eval()
    assert interaction_parameter_count(gat) < 50_000
    assert InteractionMLPControl(normalization).model_kind == "mlp"
    assert InteractionLinearControl(normalization).model_kind == "linear"
    tensors = features.to_tensors()
    permutation = torch.randperm(tensors["node_features"].shape[0], generator=torch.Generator().manual_seed(9))
    inverse = torch.empty_like(permutation)
    inverse[permutation] = torch.arange(permutation.numel())
    permuted = {
        **tensors,
        "node_features": tensors["node_features"][permutation],
        "edge_index": inverse[tensors["edge_index"]],
    }
    with torch.inference_mode():
        original = gat(**tensors)
        changed = gat(**permuted)
    for key in original:
        assert torch.allclose(original[key], changed[key], atol=2e-6, rtol=2e-6)


@pytest.mark.parametrize("scale", (5, 10, 20))
def test_small_scale_bypasses_before_manifest_graph_and_torch(
    scale, monkeypatch: pytest.MonkeyPatch,
):
    request = _request(scale)
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV, "/must/not/be/read.json")
    imported = []
    original = builtins.__import__

    def spy(name, *args, **kwargs):
        imported.append(str(name))
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", spy)
    selected, telemetry = prepare_root_interaction_gat_request_from_environment(request)
    assert selected is request
    assert telemetry["proof_tail_interaction_gat_decision_reason"].startswith("scale_bypasses")
    assert telemetry["proof_tail_interaction_gat_manifest_read"] is False
    assert telemetry["proof_tail_interaction_gat_graph_build_calls"] == 0
    assert telemetry["proof_tail_interaction_gat_model_calls"] == 0
    assert telemetry["proof_tail_interaction_gat_ranker_calls"] == 0
    assert not any("interaction_gat_queue_v2" in name for name in imported)


def test_tree_bypasses_before_manifest_graph_and_torch(monkeypatch: pytest.MonkeyPatch):
    request = _request(lifecycle="tree_node")
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV, "/must/not/be/read.json")
    imported = []
    original = builtins.__import__

    def spy(name, *args, **kwargs):
        imported.append(str(name))
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", spy)
    selected, telemetry = prepare_root_interaction_gat_request_from_environment(request)
    assert selected is request
    assert telemetry["proof_tail_interaction_gat_decision_reason"].startswith("non_root")
    assert telemetry["proof_tail_interaction_gat_manifest_read"] is False
    assert telemetry["proof_tail_interaction_gat_model_calls"] == 0
    assert not any("interaction_gat_queue_v2" in name for name in imported)


def test_runtime_accepts_only_gat_and_selects_one_exact_safe_arm(tmp_path, monkeypatch):
    request = _request()
    manifest = _write_manifest(tmp_path, request, selected="QD1")
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(INTERACTION_GAT_EVALUATION_ENV, "1")
    selected, telemetry = prepare_root_interaction_gat_request_from_environment(request)
    assert selected is not request
    assert selected.proof_queue_policy_id == "QD1"
    assert selected.guidance_hints is None
    assert telemetry["proof_tail_interaction_gat_action"] == "QD1"
    assert telemetry["proof_tail_interaction_gat_message_passing_required"] is True


def test_runtime_rejects_simple_model_manifest_by_literal_identity(tmp_path, monkeypatch):
    request = _request()
    manifest = _write_manifest(tmp_path, request, model_kind="linear")
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(INTERACTION_GAT_EVALUATION_ENV, "1")
    selected, telemetry = prepare_root_interaction_gat_request_from_environment(request)
    assert selected is request
    assert "fail_closed" in telemetry["proof_tail_interaction_gat_decision_reason"]


def test_runtime_exact_config_drift_is_literal_q0(tmp_path, monkeypatch):
    request = _request()
    manifest = _write_manifest(tmp_path, request, selected="QD1")
    drifted = replace(request, config_hash="different-exact-config")
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(INTERACTION_GAT_EVALUATION_ENV, "1")
    selected, telemetry = prepare_root_interaction_gat_request_from_environment(drifted)
    assert selected is drifted
    assert telemetry["proof_tail_interaction_gat_decision_reason"] == "exact_config_hash_mismatch"


def test_qgr1_veto_never_requires_or_opens_ranker(tmp_path, monkeypatch):
    request = _request()
    manifest = _write_manifest(tmp_path, request, selected="QD1")
    payload = json.loads(manifest.read_text())
    payload["qgr1_ranker_checkpoint_path"] = "/must/not/open.pt"
    manifest.write_text(json.dumps(payload))
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(INTERACTION_GAT_EVALUATION_ENV, "1")
    original = Path.read_bytes

    def spy(path):
        assert str(path) != "/must/not/open.pt"
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", spy)
    selected, _ = prepare_root_interaction_gat_request_from_environment(request)
    assert selected.proof_queue_policy_id == "QD1"


def _outcome(instance, context, scale, arm, ratio, partition="train"):
    return MatchedContextOutcome(
        context_id=context, instance_hash=instance, scale=scale,
        partition=partition, arm=arm, determined=True, ratio=ratio,
        beneficial=ratio <= 0.98, strong_benefit=ratio <= 0.95,
        harmful=ratio >= 1.05, adverse=ratio >= 1.05,
        q0_complete_arm_censored=False, q0_censored_arm_completed=False,
        correctness_redlines=(),
    )


def test_v2_arm_admission_uses_stricter_18_9_3_4_gate():
    rows = []
    for index in range(18):
        ratio = 0.94 if index < 3 else 1.0
        rows.append(_outcome(f"i{index % 9}", f"c{index}", 30, "QD1", ratio))
    decision = assess_v2_arm_scale_admission(rows, arm="QD1", scale=30)
    assert decision["admitted"]
    assert decision["determined_contexts"] == 18
    assert decision["strong_benefit_instances"] == 3


def test_v2_oracle_requires_five_winner_instances_and_all_outcome_categories():
    rows = []
    for scale in (30, 50):
        ratios = (0.80, 0.85, 0.90, 0.92, 0.94, 1.0, 1.08)
        rows.extend(
            _outcome(f"{scale}-i{i}", f"{scale}-c{i}", scale, "QD1", ratio)
            for i, ratio in enumerate(ratios)
        )
    decision = measured_v2_portfolio_oracle(
        rows, admitted_arms_by_scale={30: ["QD1"], 50: ["QD1"]}
    )
    assert decision["selector_training_authorized"]
    assert decision["scales"]["30"]["non_q0_winner_instances"] >= 5


def test_gat_calibration_and_heldout_require_graph_and_simple_control_advantage():
    full = {
        "harmful_activations": 0, "rank_accuracy": 0.82, "combined_gm": 0.94,
        "correctness_redlines": [],
        "scales": {
            "30": {"activation_instances": 2, "selected_action_gm": 0.95},
            "50": {"activation_instances": 2, "selected_action_gm": 0.96},
        },
    }
    gate = assess_gat_calibration(
        full=full,
        no_message={"rank_accuracy": 0.78, "combined_gm": 0.95},
        shuffled_topology={"rank_accuracy": 0.81, "combined_gm": 0.94},
    )
    assert gate["passed"]
    summaries = {
        "gat": {
            "worst_scale_gm": 0.97, "combined_gm": 0.95,
            "correctness_redlines": [],
            "scales": {
                "30": {"activation_instances": 2, "net_gm": 0.95},
                "50": {"activation_instances": 2, "net_gm": 0.97},
            },
        },
        "mlp": {"worst_scale_gm": 0.99, "combined_gm": 0.98},
        "linear": {"worst_scale_gm": 1.00, "combined_gm": 0.99},
        "no_message": {"worst_scale_gm": 0.98, "combined_gm": 0.96},
        "shuffled_topology": {"worst_scale_gm": 0.97, "combined_gm": 0.95},
    }
    heldout = assess_gat_heldout_advantage(summaries, preparation_p99_ms=9.0)
    assert heldout["passed"]


def test_qgr1_residual_pairs_are_75_25_pressure_weighted_and_nonoverlapping(monkeypatch):
    labels = {
        index: {
            "terminal": False, "visited_count": 5,
            "reduced_cost_bucket": 7,
        }
        for index in range(10)
    }
    base = (
        QGR1WeightedPair(0, 1, "admission_x", "admitted_ancestor", 1.0, 0),
        QGR1WeightedPair(2, 3, "existing_dominator", "existing_dominator", 1.0),
        QGR1WeightedPair(4, 5, "incoming_dominator", "incoming_dominator", 1.0),
    )
    monkeypatch.setattr(
        residual, "build_qgr1_weighted_pairs",
        lambda *args, **kwargs: (base, {"all_admitted_routes_represented": True}),
    )
    supervised, neutral, metadata = residual.build_qgr1_residual_pairs(
        {}, labels, seed=61635, maximum=12
    )
    assert sum(row.weight for row in supervised) == pytest.approx(0.75)
    assert sum(row.weight for row in neutral) == pytest.approx(0.25)
    assert len(supervised) == 3 and len(neutral) == 1
    assert metadata["observed_supervised_pair_fraction"] == pytest.approx(0.75)
    supervised_pairs = {
        frozenset((row.preferred_label_id, row.other_label_id)) for row in supervised
    }
    assert not any(
        frozenset((row.left_label_id, row.right_label_id)) in supervised_pairs
        for row in neutral
    )
    assert metadata["pressure_weight"].endswith("clipped_at_8")


def test_acceptance_bootstrap_rebinds_only_the_optional_python_dispatch(monkeypatch):
    import lunar_ice_bpc.guidance.context_queue_portfolio_runtime as dispatch
    from scripts.run_lunar_ice_interaction_gat_acceptance_v2 import (
        V1_DISPATCH_ENV,
        install_v2_dispatch,
    )

    original = dispatch.prepare_context_queue_portfolio_request_from_environment
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV, "/frozen/v2/manifest.json")
    try:
        install_v2_dispatch()
        assert dispatch.prepare_context_queue_portfolio_request_from_environment is (
            prepare_root_interaction_gat_request_from_environment
        )
        assert __import__("os").environ[V1_DISPATCH_ENV] == "/frozen/v2/manifest.json"
    finally:
        dispatch.prepare_context_queue_portfolio_request_from_environment = original


def test_full_bpc_telemetry_counts_small_scale_and_tree_bypasses_as_zero_calls():
    from scripts.run_p0v5_interaction_gat_full_bpc_v2 import _interaction_telemetry

    payload = {
        "small": {
            "proof_tail_interaction_gat_action": "Q0",
            "proof_tail_interaction_gat_decision_reason": "scale_bypasses_before_manifest_torch_graph",
            "proof_tail_interaction_gat_runtime_enabled": False,
            "proof_tail_interaction_gat_manifest_read": False,
            "proof_tail_interaction_gat_graph_build_calls": 0,
            "proof_tail_interaction_gat_model_calls": 0,
            "proof_tail_interaction_gat_ranker_calls": 0,
        },
        "tree": {
            "proof_tail_interaction_gat_action": "Q0",
            "proof_tail_interaction_gat_decision_reason": "non_root_lifecycle_bypasses_before_manifest_torch_graph",
            "proof_tail_interaction_gat_runtime_enabled": False,
            "proof_tail_interaction_gat_manifest_read": False,
            "proof_tail_interaction_gat_model_calls": 0,
        },
    }
    telemetry = _interaction_telemetry(payload)
    assert telemetry["manifest_reads"] == 0
    assert telemetry["model_calls"] == 0
    assert telemetry["ranker_calls"] == 0
    assert telemetry["tree_model_calls"] == 0


def test_r1_terminal_decision_remains_original_negative():
    terminal = json.loads((
        ROOT / "runs/p0v5_context_queue_portfolio_v1_20260807_r1/terminal_decision.json"
    ).read_text(encoding="utf-8"))
    assert terminal["decision"] == "FAIL"
    assert terminal["reason"] == "INSUFFICIENT_CONTEXT_COVERAGE"
