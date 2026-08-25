from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import random
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
    BackendPricingRequest,
    COUNTERFACTUAL_PREFIX_CHECKPOINTS_V8,
    COUNTERFACTUAL_PREFIX_MODE_Q0,
    COUNTERFACTUAL_PREFIX_MODE_QD1,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.guidance.counterfactual_prefix_gat_qd1_v8 import (
    CONTEXT_FEATURE_NAMES,
    COUNTER_DELTA_NAMES,
    EDGE_FEATURE_NAMES,
    LABEL_FEATURE_NAMES,
    MODEL_SEEDS,
    NODE_FEATURE_NAMES,
    CounterfactualGraph,
    CounterfactualTriplet,
    build_counterfactual_graph,
    build_counterfactual_model,
    build_triplet,
    export_portable_bundle,
    parameter_count,
    portable_triplet_payload,
    triplet_tensors,
)
from lunar_ice_bpc.guidance.counterfactual_prefix_gat_qd1_runtime_v8 import (
    select_counterfactual_prefix_request,
)
from scripts.train_p0v5_counterfactual_representation_v8 import _cost_gate


def _native_graph(*, last_tasks=(0, 1), suffix="base"):
    nodes = []
    for index, last_task in enumerate(last_tasks):
        features = [0.0] * len(LABEL_FEATURE_NAMES)
        features[0] = 0.2 + 0.1 * index
        features[14] = -0.3 + 0.2 * index
        features[15] = float(index == 1)
        features[17] = float(index)
        features[18] = float(1 - index)
        features[19] = features[18] - features[17]
        features[20] = float(last_task + 1) / 2.0
        features[21] = 1.0
        features[23] = 1.0
        nodes.append({
            "creation_sequence_id": 10 + index,
            "parent_creation_sequence_id": 10 if index else 2**64 - 1,
            "last_task_index": last_task,
            "dominance_surface_hash": 100 + index,
            "features": features,
        })
    return {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_label_sample_graph.v1",
        "graph_hash": f"native-{suffix}",
        "frontier_size": 2,
        "sampled_label_count": 2,
        "label_nodes": nodes,
        "label_edges": [
            {"source": 0, "target": 0, "features": [1.0] + [0.0] * 7},
            {"source": 1, "target": 1, "features": [1.0] + [0.0] * 7},
            {"source": 0, "target": 1, "features": [0.0, 1.0] + [0.0] * 6},
        ],
        "context_features": [0.01 * index for index in range(28)],
    }


TASKS = (
    {
        "id": "a", "demand": 1.0, "service_time": 2.0,
        "service_energy": 3.0, "service_cost": 4.0,
        "ready_time": 0.0, "due_time": 20.0,
        "local_shadow_score": 0.1, "local_thermal_risk": 0.2,
    },
    {
        "id": "b", "demand": 2.0, "service_time": 3.0,
        "service_energy": 4.0, "service_cost": 5.0,
        "ready_time": 1.0, "due_time": 25.0,
        "local_shadow_score": 0.2, "local_thermal_risk": 0.3,
    },
)
ARCS = (
    {"source": "a", "target": "b", "travel_time": 3.0},
    {"source": "b", "target": "a", "travel_time": 4.0},
)


def _prefix(mode: str, endpoint_graph):
    return {
        "mode": mode,
        "complete": True,
        "truncated_diagnostic": True,
        "exact": False,
        "routes_suppressed": True,
        "certificate_suppressed": True,
        "base_graph_hash": "same-base",
        "base_graph": _native_graph(),
        "base_processed_labels": 4096,
        "base_extended_labels": 5000,
        "base_dominated_labels": 100,
        "base_dominance_candidate_checks": 9000,
        "base_subset_dominance_candidate_checks": 20,
        "base_subset_dominance_rejected_labels": 2,
        "base_max_visited_bucket_size": 40,
        "base_negative_label_event_count": 1,
        "base_best_true_reduced_cost": -1.0,
        "endpoints": [
            {
                "rollout_budget": budget,
                "processed_labels": 4096 + budget,
                "extended_labels": 5000 + 2 * budget,
                "dominated_labels": 100 + budget // 8,
                "dominance_candidate_checks": 9000 + 3 * budget,
                "subset_dominance_candidate_checks": 20 + budget // 16,
                "subset_dominance_rejected_labels": 2 + budget // 128,
                "frontier_size": 2 + budget // 128,
                "max_visited_bucket_size": 40 + budget // 128,
                "negative_label_event_count": 1 + budget // 512,
                "best_true_reduced_cost": -1.0 - budget / 10000.0,
                "base_label_survival_count": 1,
                "new_label_count": 1,
                "frontier_churn": 0.25,
                "graph": endpoint_graph,
            }
            for budget in COUNTERFACTUAL_PREFIX_CHECKPOINTS_V8
        ],
    }


def _triplet():
    return build_triplet(
        _prefix(COUNTERFACTUAL_PREFIX_MODE_Q0, _native_graph(suffix="q0")),
        _prefix(COUNTERFACTUAL_PREFIX_MODE_QD1, _native_graph(suffix="qd1")),
        rollout_budget=128,
        state_hash="ab" * 32,
        tasks=TASKS,
        arcs=ARCS,
        true_task_duals={"a": 2.0, "b": -1.0},
        branch_pairs=(("a", "b"),),
        cut_task_sets=(("a", "b"),),
    )


def _normalization():
    return {
        "node": {"mean": [0.0] * len(NODE_FEATURE_NAMES), "scale": [1.0] * len(NODE_FEATURE_NAMES), "minimum": [-10.0] * len(NODE_FEATURE_NAMES), "maximum": [10.0] * len(NODE_FEATURE_NAMES)},
        "edge": {"mean": [0.0] * len(EDGE_FEATURE_NAMES), "scale": [1.0] * len(EDGE_FEATURE_NAMES), "minimum": [-10.0] * len(EDGE_FEATURE_NAMES), "maximum": [10.0] * len(EDGE_FEATURE_NAMES)},
        "context": {"mean": [0.0] * len(CONTEXT_FEATURE_NAMES), "scale": [1.0] * len(CONTEXT_FEATURE_NAMES), "minimum": [-10.0] * len(CONTEXT_FEATURE_NAMES), "maximum": [10.0] * len(CONTEXT_FEATURE_NAMES)},
        "counter": {"mean": [0.0] * len(COUNTER_DELTA_NAMES), "scale": [1.0] * len(COUNTER_DELTA_NAMES), "minimum": [-10.0] * len(COUNTER_DELTA_NAMES), "maximum": [10.0] * len(COUNTER_DELTA_NAMES)},
    }


def _request(scale: int = 30) -> BackendPricingRequest:
    root = Path(__file__).resolve().parents[1]
    instance = root / (
        f"data/instances/lunar_ice_sp50_{scale:03d}/"
        "instance_001_logical_graph.json"
    )
    data = load_lunar_ice_data(json.loads(instance.read_text(encoding="utf-8")))
    return BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}),
        mode="exact_proof",
        objective_mode="official",
        pricing_lifecycle_scope="root_cg",
        proof_queue_policy_id="Q0",
        proof_tail_fallback_context=True,
        proof_tail_active_column_count=4,
        proof_tail_round_index=2,
        proof_tail_dual_delta_l1=0.25,
        proof_tail_v5_midpoint_wall_sec=0.5,
        instance_hash=data.instance_content_hash,
        config_hash="config-v8-test",
        engine_hash="engine-v8-test",
    )


def test_graph_is_deterministic_and_task_id_permutation_equivariant():
    first = build_counterfactual_graph(
        _native_graph(), tasks=TASKS, arcs=ARCS,
        true_task_duals={"a": 2.0, "b": -1.0},
    )
    permuted_native = _native_graph(last_tasks=(1, 0))
    permuted = build_counterfactual_graph(
        permuted_native, tasks=tuple(reversed(TASKS)), arcs=tuple(reversed(ARCS)),
        true_task_duals={"a": 2.0, "b": -1.0},
    )
    assert first.graph_hash == permuted.graph_hash
    assert first.node_features == permuted.node_features
    assert first.edge_index == permuted.edge_index
    assert first.edge_features == permuted.edge_features
    assert first.label_count == 2 and first.task_count == 2


def test_cut_membership_adds_deterministic_task_interaction_edges():
    without_cut = build_counterfactual_graph(
        _native_graph(), tasks=TASKS, arcs=(),
        true_task_duals={"a": 2.0, "b": -1.0},
    )
    with_cut = build_counterfactual_graph(
        _native_graph(), tasks=TASKS, arcs=(),
        true_task_duals={"a": 2.0, "b": -1.0},
        cut_task_sets=(("b", "a"),),
    )
    task_pair = (2, 3)
    assert task_pair not in set(zip(*without_cut.edge_index))
    assert task_pair in set(zip(*with_cut.edge_index))
    assert (3, 2) in set(zip(*with_cut.edge_index))


def test_graph_builder_ignores_full_outcome_fields():
    clean = _native_graph()
    contaminated = dict(clean)
    contaminated.update({
        "full_run_wall": 999.0,
        "winner": "QD1",
        "certificate": {"negative": False},
        "final_processed_labels": 999_999,
    })
    kwargs = dict(
        tasks=TASKS, arcs=ARCS,
        true_task_duals={"a": 2.0, "b": -1.0},
    )
    assert build_counterfactual_graph(clean, **kwargs).graph_hash == (
        build_counterfactual_graph(contaminated, **kwargs).graph_hash
    )


def test_triplet_contract_and_shared_gat_shapes():
    triplet = _triplet()
    assert len(triplet.counter_deltas) == len(COUNTER_DELTA_NAMES)
    model = build_counterfactual_model(kind="gat").double().eval()
    assert parameter_count(model) < 30_000
    outputs = model(**triplet_tensors(triplet, _normalization()))
    assert set(outputs) == {"p_benefit", "positive_gain", "p_adverse"}
    assert all(0.0 <= float(value) <= 1.0 for value in outputs.values())
    for kind in ("mlp", "linear", "no_message", "shuffled_topology"):
        control = build_counterfactual_model(kind=kind).double().eval()
        assert control is not model
        assert len(control.state_dict()) > 0


def test_graph_pooling_is_invariant_to_node_and_edge_permutation():
    torch = pytest.importorskip("torch")
    triplet = _triplet()

    def permute(graph: CounterfactualGraph) -> CounterfactualGraph:
        order = tuple(reversed(range(len(graph.node_features))))
        old_to_new = {old: new for new, old in enumerate(order)}
        edge_order = tuple(reversed(range(len(graph.edge_features))))
        return CounterfactualGraph(
            node_features=tuple(graph.node_features[index] for index in order),
            edge_index=(
                tuple(old_to_new[graph.edge_index[0][index]] for index in edge_order),
                tuple(old_to_new[graph.edge_index[1][index]] for index in edge_order),
            ),
            edge_features=tuple(graph.edge_features[index] for index in edge_order),
            context_features=graph.context_features,
            graph_hash="permuted-for-pooling-test",
            label_count=graph.label_count,
            task_count=graph.task_count,
        )

    permuted = CounterfactualTriplet(
        base=permute(triplet.base), q0=permute(triplet.q0),
        qd1=permute(triplet.qd1), counter_deltas=triplet.counter_deltas,
        rollout_budget=triplet.rollout_budget, state_hash=triplet.state_hash,
    )
    torch.manual_seed(260818)
    model = build_counterfactual_model(kind="gat").double().eval()
    with torch.no_grad():
        expected = model(**triplet_tensors(triplet, _normalization()))
        actual = model(**triplet_tensors(permuted, _normalization()))
    for name in expected:
        assert torch.allclose(expected[name], actual[name], atol=1e-10, rtol=1e-10)


def test_python_cpp_portable_forward_parity(tmp_path):
    torch = pytest.importorskip("torch")
    native = pytest.importorskip("lunar_spprc_native")
    triplet = _triplet()
    normalization = _normalization()
    models = []
    python_rows = []
    for seed in MODEL_SEEDS:
        torch.manual_seed(seed)
        model = build_counterfactual_model(kind="gat").double().eval()
        models.append((seed, model))
        output = model(**triplet_tensors(triplet, normalization))
        python_rows.append(tuple(float(output[name]) for name in (
            "p_benefit", "positive_gain", "p_adverse"
        )))
    path = tmp_path / "bundle.json"
    bundle = export_portable_bundle(
        models=models,
        normalization=normalization,
        calibration_by_scale={"30": {}, "50": {}},
        thresholds_by_scale={"30": {}, "50": {}},
        rollout_budget=128,
        bindings={"development_only": True},
        output_path=path,
    )
    assert json.loads(path.read_text())["bundle_sha256"] == bundle["bundle_sha256"]
    for index, expected in enumerate(python_rows):
        actual = tuple(native.counterfactual_gat_forward(
            bundle, portable_triplet_payload(triplet), index
        ))
        assert max(abs(left - right) for left, right in zip(actual, expected)) <= 1e-5


def test_python_cpp_portable_forward_100_random_graphs_and_actions(tmp_path):
    torch = pytest.importorskip("torch")
    native = pytest.importorskip("lunar_spprc_native")
    normalization = _normalization()
    models = []
    for seed in MODEL_SEEDS:
        torch.manual_seed(seed)
        models.append((seed, build_counterfactual_model(kind="gat").double().eval()))
    bundle = export_portable_bundle(
        models=models,
        normalization=normalization,
        calibration_by_scale={"30": {}, "50": {}},
        thresholds_by_scale={"30": {}, "50": {}},
        rollout_budget=128,
        bindings={"development_only": True},
        output_path=tmp_path / "random_bundle.json",
    )
    base_triplet = _triplet()
    generator = random.Random(260818100)

    def perturbed_graph(graph, trial, view):
        rows = []
        for node_index, row in enumerate(graph.node_features):
            rows.append(tuple(
                float(value) + generator.uniform(-0.01, 0.01)
                for value in row
            ))
        context = tuple(
            float(value) + generator.uniform(-0.01, 0.01)
            for value in graph.context_features
        )
        return CounterfactualGraph(
            node_features=tuple(rows), edge_index=graph.edge_index,
            edge_features=graph.edge_features, context_features=context,
            graph_hash=f"random-{trial}-{view}",
            label_count=graph.label_count, task_count=graph.task_count,
        )

    for trial in range(100):
        triplet = CounterfactualTriplet(
            base=perturbed_graph(base_triplet.base, trial, "base"),
            q0=perturbed_graph(base_triplet.q0, trial, "q0"),
            qd1=perturbed_graph(base_triplet.qd1, trial, "qd1"),
            counter_deltas=tuple(
                value + generator.uniform(-0.01, 0.01)
                for value in base_triplet.counter_deltas
            ),
            rollout_budget=128, state_hash=f"random-state-{trial}",
        )
        triplet.validate()
        python_rows = []
        for _, model in models:
            with torch.no_grad():
                output = model(**triplet_tensors(triplet, normalization))
            python_rows.append(tuple(float(output[name]) for name in (
                "p_benefit", "positive_gain", "p_adverse"
            )))
        native_rows = [
            tuple(native.counterfactual_gat_forward(
                bundle, portable_triplet_payload(triplet), seed_index
            ))
            for seed_index in range(3)
        ]
        assert max(
            abs(left - right)
            for expected, actual in zip(python_rows, native_rows)
            for left, right in zip(expected, actual)
        ) <= 1e-5

        def action(rows):
            benefit = sum(row[0] for row in rows) / 3.0
            gain = min(row[1] for row in rows)
            adverse = max(row[2] for row in rows)
            disagreement = max(row[0] for row in rows) - min(row[0] for row in rows)
            expected_gain = benefit * gain
            return (
                benefit >= 0.50 and adverse <= 0.80
                and expected_gain >= 0.05
                and expected_gain - adverse > 0.0
                and disagreement <= 0.25
            )

        assert action(python_rows) == action(native_rows)


def test_prefix_base_hash_mismatch_fails_closed():
    q0 = _prefix(COUNTERFACTUAL_PREFIX_MODE_Q0, _native_graph(suffix="q0"))
    qd1 = _prefix(COUNTERFACTUAL_PREFIX_MODE_QD1, _native_graph(suffix="qd1"))
    qd1["base_graph_hash"] = "different"
    with pytest.raises(ValueError, match="base graphs"):
        build_triplet(
            q0, qd1, rollout_budget=128, state_hash="x",
            tasks=TASKS, arcs=ARCS, true_task_duals={"a": 1.0, "b": 1.0},
        )


def test_small_scale_and_tree_bypass_before_manifest(monkeypatch):
    import lunar_ice_bpc.guidance.counterfactual_prefix_gat_qd1_runtime_v8 as runtime

    monkeypatch.setattr(
        runtime,
        "_load_manifest",
        lambda *_: pytest.fail("manifest must not be read on an early bypass"),
    )
    base = dict(
        mode="exact_proof",
        objective_mode="official",
        proof_queue_policy_id="Q0",
        proof_tail_fallback_context=True,
    )
    small = SimpleNamespace(
        **base,
        data=SimpleNamespace(scale=20),
        pricing_lifecycle_scope="root_cg",
    )
    small_decision = select_counterfactual_prefix_request(
        small, manifest_path="missing.json"
    )
    assert small_decision.request is small
    assert not small_decision.probes_started
    tree = SimpleNamespace(
        **base,
        data=SimpleNamespace(scale=30),
        pricing_lifecycle_scope="tree_node",
    )
    tree_decision = select_counterfactual_prefix_request(
        tree, manifest_path="missing.json"
    )
    assert tree_decision.request is tree
    assert not tree_decision.probes_started


def test_post_probe_reject_and_error_construct_independent_exact_q0(monkeypatch):
    import lunar_ice_bpc.guidance.counterfactual_prefix_gat_qd1_runtime_v8 as runtime

    request = _request()
    bundle = {
        "calibration_by_scale": {
            "30": {
                "benefit": {"kind": "constant", "probability": 0.1},
                "adverse": {"kind": "constant", "probability": 0.9},
                "gain_scale": 1.0,
            }
        },
        "thresholds_by_scale": {
            "30": {
                "minimum_benefit_probability": 0.9,
                "maximum_adverse_probability": 0.02,
                "minimum_expected_gain": 0.1,
                "adverse_penalty": 2.0,
                "maximum_disagreement": 0.05,
            }
        },
    }
    monkeypatch.setattr(runtime, "_load_manifest", lambda *_: ({"rollout_budget": 128}, bundle))
    monkeypatch.setattr(runtime, "run_native_counterfactual_prefix_raw", lambda *_: {
        "telemetry": {"proof_queue_counterfactual_prefix": {}}
    })
    monkeypatch.setattr(runtime, "build_triplet", lambda *_args, **_kwargs: _triplet())
    monkeypatch.setattr(runtime, "_triplet_is_ood", lambda *_: False)
    monkeypatch.setattr(runtime, "_static_graph_inputs", lambda *_: {})
    monkeypatch.setattr(runtime.importlib, "import_module", lambda *_: SimpleNamespace(
        counterfactual_gat_forward=lambda *_: (0.1, 0.1, 0.9)
    ))
    rejected = select_counterfactual_prefix_request(request, manifest_path="ignored")
    assert rejected.probes_started and rejected.reason == "threshold_reject"
    assert rejected.request is not request
    assert rejected.request.proof_tail_counterfactual_prefix_mode == "disabled"
    assert rejected.request.proof_tail_frontier_probe_mode == "disabled"

    monkeypatch.setattr(
        runtime, "run_native_counterfactual_prefix_raw",
        lambda *_: (_ for _ in ()).throw(RuntimeError("probe failed")),
    )
    failed = select_counterfactual_prefix_request(request, manifest_path="ignored")
    assert failed.probes_started and failed.reason.startswith("post_probe_fail_closed")
    assert failed.request is not request
    assert failed.request.proof_tail_counterfactual_prefix_mode == "disabled"
    assert failed.request.proof_tail_frontier_probe_mode == "disabled"


def test_representation_cost_gate_uses_per_checkpoint_native_wall():
    rows = []
    for scale in (30, 50):
        for index in range(3):
            rows.append({
                "instance_hash": f"s{scale}-{index}",
                "scale": scale,
                "paired_prefix_native_warm_wall_seconds": 0.10,
                "q0_prefix_cold_fresh_process_wall_seconds": 20.0,
                "qd1_prefix_cold_fresh_process_wall_seconds": 20.0,
                "qpf0_reference_wall_seconds": 10.0,
                "target": {"ratio": 0.90},
            })
    result = _cost_gate(rows)
    assert result["paired_prefix_p99_ms"] == pytest.approx(100.0)
    assert result["maximum_paired_prefix_fraction_of_qpf0"] == pytest.approx(0.01)
    assert result["cost_gate_passed"]
