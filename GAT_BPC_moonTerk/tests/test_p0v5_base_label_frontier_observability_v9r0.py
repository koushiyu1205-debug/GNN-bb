from __future__ import annotations

import json
from pathlib import Path

import pytest

from lunar_ice_bpc.guidance.base_frontier_gat_qd1_v9 import (
    MODEL_KINDS,
    BaseFrontierExample,
    build_base_frontier_model,
    graph_tensors,
    parameter_count,
    pooled_numeric_signature,
    shuffled_graph_tensors,
)
from lunar_ice_bpc.guidance.counterfactual_prefix_gat_qd1_v8 import (
    CONTEXT_FEATURE_NAMES,
    EDGE_FEATURE_NAMES,
    NODE_FEATURE_NAMES,
    CounterfactualGraph,
)
from scripts.initialize_p0v5_base_label_frontier_observability_v9r0 import (
    assign_folds,
)


ROOT = Path(__file__).resolve().parents[1]


def _graph() -> CounterfactualGraph:
    node_count = 7
    nodes = []
    for row in range(node_count):
        values = [0.01 * (row + 1) * (column + 1) for column in range(len(NODE_FEATURE_NAMES))]
        # Preserve explicit type indicators used by the imported graph schema.
        values[24] = 1.0 if row < 4 else 0.0
        values[25] = 0.0 if row < 4 else 1.0
        nodes.append(tuple(values))
    sources = (0, 1, 2, 3, 4, 5, 6, 0, 1, 4)
    targets = (0, 1, 2, 3, 4, 5, 6, 1, 4, 6)
    edges = tuple(
        tuple(0.02 * (index + 1) * (column + 1) for column in range(len(EDGE_FEATURE_NAMES)))
        for index in range(len(sources))
    )
    context = tuple(0.03 * (index + 1) for index in range(len(CONTEXT_FEATURE_NAMES)))
    value = CounterfactualGraph(
        node_features=tuple(nodes),
        edge_index=(sources, targets),
        edge_features=edges,
        context_features=context,
        graph_hash="synthetic",
        label_count=4,
        task_count=3,
    )
    value.validate()
    return value


def _normalization():
    return {
        "node": {"mean": [0.0] * len(NODE_FEATURE_NAMES), "scale": [1.0] * len(NODE_FEATURE_NAMES)},
        "edge": {"mean": [0.0] * len(EDGE_FEATURE_NAMES), "scale": [1.0] * len(EDGE_FEATURE_NAMES)},
        "context": {"mean": [0.0] * len(CONTEXT_FEATURE_NAMES), "scale": [1.0] * len(CONTEXT_FEATURE_NAMES)},
    }


def _permute_within_types(graph: CounterfactualGraph) -> CounterfactualGraph:
    # Label and task partitions are separately permuted so typed pooling must
    # remain invariant while message endpoints are relabelled consistently.
    order = (3, 1, 0, 2, 6, 4, 5)
    old_to_new = {old: new for new, old in enumerate(order)}
    return CounterfactualGraph(
        node_features=tuple(graph.node_features[index] for index in order),
        edge_index=(
            tuple(old_to_new[index] for index in graph.edge_index[0]),
            tuple(old_to_new[index] for index in graph.edge_index[1]),
        ),
        edge_features=graph.edge_features,
        context_features=graph.context_features,
        graph_hash="permuted",
        label_count=graph.label_count,
        task_count=graph.task_count,
    )


@pytest.mark.parametrize("kind", MODEL_KINDS)
def test_model_shape_and_parameter_cap(kind: str) -> None:
    model = build_base_frontier_model(kind=kind, dropout=0.0).double().eval()
    assert parameter_count(model) < 20_000
    output = model(graph=graph_tensors(_graph(), _normalization()))
    assert set(output) == {"p_benefit", "positive_gain", "p_adverse"}
    assert all(value.ndim == 0 for value in output.values())
    assert all(
        0.0 <= float(value.detach()) <= 1.0 for value in output.values()
    )


def test_gat_is_equivariant_to_within_type_node_permutation() -> None:
    model = build_base_frontier_model(kind="gat", dropout=0.0).double().eval()
    left = model(graph=graph_tensors(_graph(), _normalization()))
    right = model(graph=graph_tensors(_permute_within_types(_graph()), _normalization()))
    for name in left:
        assert float(left[name]) == pytest.approx(float(right[name]), abs=1.0e-12)


def test_shuffled_topology_is_deterministic_and_preserves_values() -> None:
    tensors = graph_tensors(_graph(), _normalization())
    left = shuffled_graph_tensors(tensors, state_hash="abc")
    right = shuffled_graph_tensors(tensors, state_hash="abc")
    assert left["edge_index"].equal(right["edge_index"])
    assert not left["edge_index"].equal(tensors["edge_index"])
    assert left["node_features"].equal(tensors["node_features"])
    assert left["edge_features"].equal(tensors["edge_features"])
    assert left["context_features"].equal(tensors["context_features"])


def test_target_validation_and_signature_are_outcome_safe() -> None:
    common = dict(
        graph=_graph(), context_id="c", instance_hash="i", state_hash="s",
        scale=3, qpf0_wall_seconds=2.0, graph_build_wall_seconds=0.001,
    )
    benefit = BaseFrontierExample(
        **common, ratio=0.9, benefit=1, positive_gain=0.1, adverse=0,
    )
    harm = BaseFrontierExample(
        **common, ratio=1.1, benefit=0, positive_gain=0.0, adverse=1,
    )
    benefit.validate()
    harm.validate()
    assert pooled_numeric_signature(benefit) == pooled_numeric_signature(harm)
    with pytest.raises(ValueError, match="benefit target drift"):
        BaseFrontierExample(
            **common, ratio=0.9, benefit=0, positive_gain=0.1, adverse=0,
        ).validate()


def test_fold_assignment_is_instance_grouped_and_deterministic() -> None:
    rows = []
    for scale in (30, 50):
        for instance in range(11):
            for context in range(1 + (instance % 2)):
                rows.append({
                    "scale": scale,
                    "instance_hash": f"s{scale}-i{instance}",
                    "context_id": f"s{scale}-i{instance}-c{context}",
                })
    left = assign_folds(rows)
    right = assign_folds(list(reversed(rows)))
    assert left == right
    by_instance = {}
    for row in left:
        key = (row["scale"], row["instance_hash"])
        assert key not in by_instance
        by_instance[key] = row["fold"]
    for scale in (30, 50):
        assert {row["fold"] for row in left if row["scale"] == scale} == set(range(5))


def test_config_forbids_counterfactual_prefix_and_non_gat_candidate() -> None:
    config = json.loads((
        ROOT / "configs/experiments/p0v5_base_label_frontier_observability_v9r0.json"
    ).read_text(encoding="utf-8"))
    assert config["model"]["candidate"] == "gat"
    assert config["action_universe"] == ["CONTINUE_Q0", "SWITCH_QD1_AT_4096"]
    assert config["diagnostic_only"] is True
    assert config["performance_authority"] is False
