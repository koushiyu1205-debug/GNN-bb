from __future__ import annotations

from dataclasses import replace
import builtins
from collections import Counter
import json
import hashlib
from pathlib import Path
import sys

import pytest
import torch

from lunar_ice_bpc.exact.bpc.pricing.backends.base import BackendPricingRequest
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import MatchedContextOutcome
from lunar_ice_bpc.guidance.interaction_gat_queue_gates_v3 import (
    assess_v3_arm_scale_admission,
    context_weights_by_instance,
    macro_instance_geometric_mean,
    measured_v3_base_portfolio_oracle,
    summarize_selected_actions_instance_first,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_runtime_v3 import (
    INTERACTION_GAT_EVALUATION_ENV_V3,
    INTERACTION_GAT_MANIFEST_ENV_V3,
    interaction_gat_runtime_implementation_hash_v3,
    prepare_root_interaction_gat_request_v3_from_environment,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (
    INTERACTION_CONTEXT_DIM,
    INTERACTION_EDGE_DIM,
    INTERACTION_INPUT_PARITY_CONTRACT_V1,
    INTERACTION_NODE_DIM,
    build_interaction_graph,
    fit_interaction_normalization,
    interaction_parameter_count,
    fit_interaction_envelope,
    interaction_graph_builder_hash,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v3 import (
    INTERACTION_CHECKPOINT_SCHEMA_V2,
    INTERACTION_CORPUS_SCHEMA_V3,
    INTERACTION_DATASET_SCHEMA_V3,
    INTERACTION_MANIFEST_SCHEMA_V2,
    INTERACTION_RUNTIME_POLICY_V3,
    V3_MODEL_KINDS,
    build_model_v3,
    shuffled_topology_features,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_v1 import (
    PORTFOLIO_ACTION_UNIVERSE, PORTFOLIO_ARMS,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
    qg2_exact_action_policy_hash_from_request,
)


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import scripts.initialize_p0v5_interaction_gat_queue_selector_v3 as initializer  # noqa: E402


def _config():
    return json.loads((
        ROOT / "configs/experiments/p0v5_interaction_gat_queue_selector_v3.json"
    ).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def frozen_preview():
    config = _config()
    v2_root = ROOT / config["v2_run_root"]
    combined = initializer._combine_preaction_rows(v2_root, config)
    corpus, split, folds, primary = initializer._freeze_instance_first_corpus(
        combined, config
    )
    return config, combined, corpus, split, folds, primary


def _request(scale=30, lifecycle="root_cg"):
    path = ROOT / f"data/instances/lunar_ice_sp50_{scale:03d}/instance_001_logical_graph.json"
    data = load_lunar_ice_data(json.loads(path.read_text(encoding="utf-8")))
    sets = tuple((task_id,) for task_id in data.task_ids[:4])
    return BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}),
        mode="exact_proof", objective_mode="official", pricing_lifecycle_scope=lifecycle,
        proof_queue_policy_id="Q0", proof_tail_fallback_context=True,
        proof_tail_active_column_count=len(sets), proof_tail_active_task_sets=sets,
        proof_tail_active_column_signature_hashes=tuple(f"{i:064x}" for i in range(len(sets))),
        proof_tail_round_index=1, instance_hash=data.instance_content_hash,
        config_hash="config", engine_hash="engine",
    )


def _outcome(instance, context, scale, ratio, arm="QD1"):
    return MatchedContextOutcome(
        context_id=context, instance_hash=instance, scale=scale,
        partition="train", arm=arm, determined=True, ratio=ratio,
        beneficial=ratio <= 0.98, strong_benefit=ratio <= 0.95,
        harmful=ratio >= 1.05, adverse=ratio >= 1.05,
        q0_complete_arm_censored=False, q0_censored_arm_completed=False,
        correctness_redlines=(),
    )


def _write_v3_manifest(tmp_path, request):
    features = build_interaction_graph(request)
    normalization = fit_interaction_normalization([features])
    envelope = fit_interaction_envelope([features])
    model = build_model_v3("gat", normalization)
    selected = PORTFOLIO_ARMS.index("QD1")
    with torch.no_grad():
        model.arm_heads.head.weight.zero_()
        model.arm_heads.head.bias.zero_()
        for index in range(len(PORTFOLIO_ARMS)):
            model.arm_heads.head.bias[3 * index:3 * index + 3] = torch.tensor([-10.0, -10.0, 10.0])
        model.arm_heads.head.bias[3 * selected:3 * selected + 3] = torch.tensor([10.0, 1.0, -10.0])
    checkpoint = tmp_path / "gat.pt"
    torch.save({
        "schema_version": INTERACTION_CHECKPOINT_SCHEMA_V2,
        "feature_schema_version": "lunar_ice_bpc.p0v5_interaction_gat_queue_features.v2",
        "graph_schema_version": "lunar_ice_bpc.p0v5_root_interaction_graph.v1",
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "model_kind": "gat", "message_passing_required": True,
        "independently_trained": True, "controls_candidate_authorized": False,
        "candidate_authorized": True,
        "action_universe": list(PORTFOLIO_ACTION_UNIVERSE),
        "architecture": {"hidden_dim": 16, "attention_heads": 2, "layers": 2, "dropout": 0.1},
        "normalization": normalization, "probability_calibration": {},
        "state_dict": model.state_dict(),
        "parameter_count": interaction_parameter_count(model),
        "development_only": True, "deployment_authorized": False,
        "production_switch_authorized": False,
    }, checkpoint)
    bound = {}
    for name, payload in {
        "source_freeze": {"source": True}, "corpus_freeze": {"corpus": True},
        "split_freeze": {"split": True}, "cv_folds_freeze": {"folds": True},
        "normalization": normalization, "ood_envelope": envelope,
    }.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        bound[f"{name}_path"] = str(path)
        bound[f"{name}_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    payload = {
        "schema_version": INTERACTION_MANIFEST_SCHEMA_V2,
        "runtime_policy_id": INTERACTION_RUNTIME_POLICY_V3,
        "runtime_implementation_hash": interaction_gat_runtime_implementation_hash_v3(),
        "graph_builder_hash": interaction_graph_builder_hash(),
        "graph_schema_version": "lunar_ice_bpc.p0v5_root_interaction_graph.v1",
        "feature_schema_version": "lunar_ice_bpc.p0v5_interaction_gat_queue_features.v2",
        "checkpoint_schema_version": INTERACTION_CHECKPOINT_SCHEMA_V2,
        "dataset_schema_version": INTERACTION_DATASET_SCHEMA_V3,
        "corpus_schema_version": INTERACTION_CORPUS_SCHEMA_V3,
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "action_universe": list(PORTFOLIO_ACTION_UNIVERSE), "fallback_action": "Q0",
        "allowed_scales": [30, 50], "lifecycle_authority": ["root_cg"],
        "root_only_authority": True,
        "arm_scale_mask": {"QGR1": [], "QD1": [30, 50], "QB1": [30, 50]},
        "forced_veto_arms": ["QGR1"], "forced_veto_arms_by_scale": {"30": [], "50": []},
        "model_kind": "gat", "message_passing_required": True,
        "controls_candidate_authorized": False,
        "architecture": {"hidden_dim": 16, "attention_heads": 2, "layers": 2, "dropout": 0.1},
        "selector_checkpoint_path": str(checkpoint),
        "selector_checkpoint_sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        "feature_envelope": envelope,
        "thresholds": {"minimum_benefit_probability": 0.8,
                       "minimum_expected_gain": 0.01,
                       "maximum_adverse_probability": 0.1, "risk_penalty": 0.5},
        "allowed_exact_engine_hashes": [request.engine_hash],
        "allowed_exact_config_hashes": [request.config_hash],
        "allowed_exact_action_policy_hashes": [qg2_exact_action_policy_hash_from_request(request)],
        "normalization_payload_sha256": hashlib.sha256(json.dumps(
            normalization, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()).hexdigest(),
        "native_binary_sha256": "test-native", "torch_num_threads": 1,
        "development_e2e_authorized": True, "development_only": True,
        "deployment_authorized": False, "production_switch_authorized": False,
        **bound,
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    return manifest


def test_v3_interface_versions_and_authority_are_new_only_where_required():
    assert INTERACTION_RUNTIME_POLICY_V3 == "P0V5_ROOT_INTERACTION_GAT_SELECTOR_V3"
    assert INTERACTION_MANIFEST_SCHEMA_V2.endswith("manifest.v2")
    assert INTERACTION_CHECKPOINT_SCHEMA_V2.endswith("checkpoint.v2")
    assert INTERACTION_DATASET_SCHEMA_V3.endswith("dataset.v3")
    assert INTERACTION_CORPUS_SCHEMA_V3.endswith("freeze.v3")
    config = _config()
    assert config["gat_is_only_candidate"] is True
    assert config["controls_candidate_authorized"] is False
    assert config["deployment_authorized"] is False
    assert config["production_switch_authorized"] is False


def test_combined_import_is_exactly_25_instances_and_39_61_contexts(frozen_preview):
    _config_value, combined, _corpus, _split, _folds, _primary = frozen_preview
    assert combined["arm_outcomes_imported"] == 0
    assert combined["tree_snapshots_imported"] == 0
    assert combined["formal_content_hash_overlap"] == 0
    assert combined["counts_by_scale"] == {
        "30": {"instances": 25, "contexts": 39,
               "multiplicity_histogram": {"1": 12, "2": 12, "3": 1}},
        "50": {"instances": 25, "contexts": 61,
               "multiplicity_histogram": {"1": 1, "2": 12, "3": 12}},
    }
    keys = [(row["instance_content_hash"], row["state_hash"]) for row in combined["rows"]]
    assert len(keys) == len(set(keys)) == 100


def test_instance_first_split_matches_all_hard_multiplicity_quotas(frozen_preview):
    config, _combined, corpus, split, _folds, _primary = frozen_preview
    assert split["context_counts_by_scale_partition"] == {
        "30": {"train": 22, "calibration": 6, "selector_heldout": 6,
               "development_e2e": 5},
        "50": {"train": 33, "calibration": 10, "selector_heldout": 10,
               "development_e2e": 8},
    }
    for scale in (30, 50):
        for partition, quota in config["split"]["multiplicity_quota"][str(scale)].items():
            rows = [row for row in corpus["rows"]
                    if row["scale"] == scale and row["partition"] == partition]
            by_instance = {row["instance_content_hash"]: row for row in rows}
            histogram = Counter(str(row["context_multiplicity"]) for row in by_instance.values())
            assert histogram == Counter({key: value for key, value in quota.items() if value})
            grouped = {}
            for row in rows:
                grouped.setdefault(row["instance_content_hash"], 0.0)
                grouped[row["instance_content_hash"]] += row["context_weight"]
            assert all(value == pytest.approx(1.0) for value in grouped.values())


def test_e2e_instances_have_no_replay_or_training_authority(frozen_preview):
    _config_value, _combined, corpus, _split, _folds, _primary = frozen_preview
    replay = {row["instance_content_hash"] for row in corpus["rows"]
              if row["partition"] != "development_e2e"}
    e2e = {row["instance_content_hash"] for row in corpus["rows"]
           if row["partition"] == "development_e2e"}
    assert replay.isdisjoint(e2e)


def test_grouped_cv_never_splits_instance_and_every_fold_has_both_scales(frozen_preview):
    _config_value, _combined, _corpus, split, folds, _primary = frozen_preview
    assert len(folds["rows"]) == 28
    assert len({row["instance_hash"] for row in folds["rows"]}) == 28
    assert all(split["instance_partition"][row["instance_hash"]] == "train"
               for row in folds["rows"])
    for fold in range(5):
        assert {row["scale"] for row in folds["rows"] if row["fold"] == fold} == {30, 50}


def test_primary_qgr1_context_is_one_per_calibration_instance(frozen_preview):
    _config_value, _combined, _corpus, _split, _folds, primary = frozen_preview
    assert len(primary["rows"]) == 8
    assert len({row["instance_hash"] for row in primary["rows"]}) == 8
    assert Counter(row["scale"] for row in primary["rows"]) == {30: 4, 50: 4}


def test_context_cloning_reweights_only_its_own_instance_total():
    original = [
        {"instance_hash": "a", "context_id": "a1"},
        {"instance_hash": "b", "context_id": "b1"},
    ]
    cloned = [*original, {"instance_hash": "a", "context_id": "a2"}]
    left = context_weights_by_instance(original)
    right = context_weights_by_instance(cloned)
    assert left["b1"] == right["b1"] == 1.0
    assert right["a1"] + right["a2"] == pytest.approx(1.0)


def test_instance_first_gm_is_context_order_invariant_and_not_context_weighted():
    values = [
        ("a", "a1", 0.5), ("a", "a2", 2.0), ("b", "b1", 0.81),
    ]
    expected = (1.0 * 0.81) ** 0.5
    assert macro_instance_geometric_mean(values) == pytest.approx(expected)
    assert macro_instance_geometric_mean(list(reversed(values))) == pytest.approx(expected)


def test_v3_model_controls_are_independent_and_below_20k():
    feature = build_interaction_graph(_request())
    normalization = fit_interaction_normalization([feature])
    models = {kind: build_model_v3(kind, normalization) for kind in V3_MODEL_KINDS}
    assert len({id(model) for model in models.values()}) == 5
    assert all(interaction_parameter_count(model) < 20_000 for model in models.values())
    assert models["gat"].message_passing_required is True
    assert all(models[kind].independently_trained_control for kind in V3_MODEL_KINDS if kind != "gat")


def test_shuffled_topology_is_deterministic_nonzero_and_preserves_all_values():
    feature = build_interaction_graph(_request())
    left = shuffled_topology_features(feature, state_hash="state")
    right = shuffled_topology_features(feature, state_hash="state")
    assert left == right
    assert left.edge_index[0] == feature.edge_index[0]
    assert left.edge_index[1] != feature.edge_index[1]
    assert Counter(left.edge_index[1]) == Counter(feature.edge_index[1])
    assert left.node_features == feature.node_features
    assert left.edge_features == feature.edge_features
    assert left.context_features == feature.context_features


@pytest.mark.parametrize("scale", (5, 10, 20))
def test_v3_small_scale_returns_identical_q0_before_v2_manifest_graph_torch_import(
    scale, monkeypatch,
):
    request = _request(scale)
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV_V3, "/must/not/be/read.json")
    imported = []
    original = builtins.__import__

    def spy(name, *args, **kwargs):
        imported.append(str(name))
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", spy)
    selected, telemetry = prepare_root_interaction_gat_request_v3_from_environment(request)
    assert selected is request
    assert telemetry["proof_tail_interaction_gat_manifest_read"] is False
    assert telemetry["proof_tail_interaction_gat_graph_build_calls"] == 0
    assert telemetry["proof_tail_interaction_gat_model_calls"] == 0
    assert not any("interaction_gat_queue_runtime_v2" in name for name in imported)


def test_v3_tree_returns_identical_q0_before_manifest_graph_torch(monkeypatch):
    request = _request(lifecycle="tree_node")
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV_V3, "/must/not/be/read.json")
    selected, telemetry = prepare_root_interaction_gat_request_v3_from_environment(request)
    assert selected is request
    assert telemetry["proof_tail_interaction_gat_manifest_read"] is False
    assert telemetry["proof_tail_interaction_gat_model_calls"] == 0


def test_v3_runtime_loads_only_true_gat_checkpoint_and_selects_one_arm(tmp_path, monkeypatch):
    request = _request()
    manifest = _write_v3_manifest(tmp_path, request)
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV_V3, str(manifest))
    monkeypatch.setenv(INTERACTION_GAT_EVALUATION_ENV_V3, "1")
    selected, telemetry = prepare_root_interaction_gat_request_v3_from_environment(request)
    assert selected is not request
    assert selected.proof_queue_policy_id == "QD1"
    assert selected.guidance_hints is None
    assert telemetry["proof_tail_interaction_gat_model_kind"] == "gat"
    assert telemetry["proof_tail_interaction_gat_runtime_policy"] == INTERACTION_RUNTIME_POLICY_V3


def test_v3_runtime_hash_drift_fails_to_identical_q0(tmp_path, monkeypatch):
    request = _request()
    manifest = _write_v3_manifest(tmp_path, request)
    payload = json.loads(manifest.read_text())
    payload["split_freeze_sha256"] = "0" * 64
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(INTERACTION_GAT_MANIFEST_ENV_V3, str(manifest))
    monkeypatch.setenv(INTERACTION_GAT_EVALUATION_ENV_V3, "1")
    selected, telemetry = prepare_root_interaction_gat_request_v3_from_environment(request)
    assert selected is request
    assert "fail_closed" in telemetry["proof_tail_interaction_gat_decision_reason"]


def test_v3_arm_admission_uses_fraction_and_instance_diversity():
    rows = []
    for index in range(22):
        ratio = 0.94 if index < 3 else 1.0
        rows.append(_outcome(f"i{index % 14}", f"c{index}", 30, ratio))
    decision = assess_v3_arm_scale_admission(rows, arm="QD1", scale=30)
    assert decision["admitted"]
    assert decision["determined_context_fraction"] == 1.0
    assert decision["determined_instances"] == 14


def test_v3_base_oracle_folds_context_winners_inside_instances_first():
    rows = []
    for scale in (30, 50):
        # Five winning instances, plus one neutral and one harmful instance.
        ratios = (0.80, 0.82, 0.84, 0.86, 0.88, 1.0, 1.08)
        for index, ratio in enumerate(ratios):
            rows.append(_outcome(f"{scale}-i{index}", f"{scale}-c{index}", scale, ratio))
    decision = measured_v3_base_portfolio_oracle(
        rows, admitted_arms_by_scale={30: ["QD1"], 50: ["QD1"]}
    )
    assert decision["selector_training_authorized"]
    assert decision["scales"]["30"]["non_q0_winner_instances"] == 5


def test_selected_action_summary_is_instance_first_and_order_invariant():
    rows = [
        {"instance_hash": "a", "context_id": "a1", "scale": 30,
         "selected_action": "QD1", "net_ratio": 0.5},
        {"instance_hash": "a", "context_id": "a2", "scale": 30,
         "selected_action": "QD1", "net_ratio": 2.0},
        {"instance_hash": "b", "context_id": "b1", "scale": 30,
         "selected_action": "Q0", "net_ratio": 1.0},
        {"instance_hash": "c", "context_id": "c1", "scale": 50,
         "selected_action": "QD1", "net_ratio": 0.9},
    ]
    left = summarize_selected_actions_instance_first(rows)
    right = summarize_selected_actions_instance_first(list(reversed(rows)))
    assert left == right
    assert left["scales"]["30"]["net_gm"] == pytest.approx(1.0)


def test_v2_terminal_remains_read_only_failure():
    terminal = json.loads((
        ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807/terminal_decision.json"
    ).read_text(encoding="utf-8"))
    assert terminal["decision"] == "FAIL"
    assert terminal["reason"] == "INSUFFICIENT_ROOT_GAT_COVERAGE"
