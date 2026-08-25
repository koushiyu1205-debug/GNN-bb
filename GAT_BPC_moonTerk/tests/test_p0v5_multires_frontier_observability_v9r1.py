from __future__ import annotations

import json
from pathlib import Path

import pytest

from lunar_ice_bpc.guidance.base_frontier_gat_qd1_v9 import BaseFrontierExample
from lunar_ice_bpc.guidance.counterfactual_prefix_gat_qd1_v8 import (
    CONTEXT_FEATURE_NAMES,
    EDGE_FEATURE_NAMES as LABEL_EDGE_FEATURE_NAMES,
    NODE_FEATURE_NAMES as LABEL_NODE_FEATURE_NAMES,
    CounterfactualGraph,
)
from lunar_ice_bpc.guidance.frontier_gat_qd1_v7 import (
    EDGE_FEATURE_NAMES as CELL_EDGE_FEATURE_NAMES,
    NODE_FEATURE_NAMES as CELL_NODE_FEATURE_NAMES,
)
from lunar_ice_bpc.guidance.multires_frontier_gat_qd1_v9 import (
    MODEL_KINDS,
    CellMassGraph,
    MultiResolutionExample,
    build_multires_model,
    multires_tensors,
    parameter_count,
    shuffled_multires_tensors,
)


ROOT = Path(__file__).resolve().parents[1]


def _context():
    return tuple(0.01 * (index + 1) for index in range(len(CONTEXT_FEATURE_NAMES)))


def _label_graph() -> CounterfactualGraph:
    nodes = []
    for row in range(7):
        values = [
            0.001 * (row + 1) * (column + 1)
            for column in range(len(LABEL_NODE_FEATURE_NAMES))
        ]
        values[24] = 1.0 if row < 4 else 0.0
        values[25] = 0.0 if row < 4 else 1.0
        nodes.append(tuple(values))
    source = (0, 1, 2, 3, 4, 5, 6, 0, 2, 4)
    target = (0, 1, 2, 3, 4, 5, 6, 1, 5, 6)
    edges = tuple(
        tuple(0.002 * (index + 1) * (column + 1) for column in range(len(LABEL_EDGE_FEATURE_NAMES)))
        for index in range(len(source))
    )
    graph = CounterfactualGraph(
        node_features=tuple(nodes), edge_index=(source, target),
        edge_features=edges, context_features=_context(), graph_hash="label",
        label_count=4, task_count=3,
    )
    graph.validate()
    return graph


def _cell_graph() -> CellMassGraph:
    nodes = tuple(
        tuple(0.003 * (row + 1) * (column + 1) for column in range(len(CELL_NODE_FEATURE_NAMES)))
        for row in range(64)
    )
    source = tuple(range(64)) + tuple(range(63))
    target = tuple(range(64)) + tuple(range(1, 64))
    edges = tuple(
        tuple(0.004 * (index + 1) * (column + 1) for column in range(len(CELL_EDGE_FEATURE_NAMES)))
        for index in range(len(source))
    )
    value = CellMassGraph(
        node_features=nodes, edge_index=(source, target), edge_features=edges,
        context_features=_context(), graph_hash="cell",
    )
    value.validate()
    return value


def _example() -> MultiResolutionExample:
    label = BaseFrontierExample(
        graph=_label_graph(), context_id="c", instance_hash="i", state_hash="s",
        scale=3, ratio=0.9, benefit=1, positive_gain=0.1, adverse=0,
        qpf0_wall_seconds=2.0, graph_build_wall_seconds=0.001,
    )
    value = MultiResolutionExample(
        label=label, cell=_cell_graph(), cell_graph_build_wall_seconds=0.0015,
    )
    value.validate()
    return value


def _normalization():
    return {
        "label_node": {"mean": [0.0] * len(LABEL_NODE_FEATURE_NAMES), "scale": [1.0] * len(LABEL_NODE_FEATURE_NAMES)},
        "label_edge": {"mean": [0.0] * len(LABEL_EDGE_FEATURE_NAMES), "scale": [1.0] * len(LABEL_EDGE_FEATURE_NAMES)},
        "cell_node": {"mean": [0.0] * len(CELL_NODE_FEATURE_NAMES), "scale": [1.0] * len(CELL_NODE_FEATURE_NAMES)},
        "cell_edge": {"mean": [0.0] * len(CELL_EDGE_FEATURE_NAMES), "scale": [1.0] * len(CELL_EDGE_FEATURE_NAMES)},
        "context": {"mean": [0.0] * len(CONTEXT_FEATURE_NAMES), "scale": [1.0] * len(CONTEXT_FEATURE_NAMES)},
    }


@pytest.mark.parametrize("kind", MODEL_KINDS)
def test_model_contract_and_parameter_cap(kind: str) -> None:
    model = build_multires_model(kind=kind, dropout=0.0).double().eval()
    assert parameter_count(model) == 18_653
    output = model(graph=multires_tensors(_example(), _normalization()))
    assert set(output) == {"p_benefit", "positive_gain", "p_adverse"}
    assert all(value.ndim == 0 for value in output.values())
    assert all(0.0 <= float(value.detach()) <= 1.0 for value in output.values())


def _permuted(example: MultiResolutionExample) -> MultiResolutionExample:
    label_order = (3, 1, 0, 2, 6, 4, 5)
    label_map = {old: new for new, old in enumerate(label_order)}
    source, target = example.label.graph.edge_index
    label_graph = CounterfactualGraph(
        node_features=tuple(example.label.graph.node_features[index] for index in label_order),
        edge_index=(
            tuple(label_map[index] for index in source),
            tuple(label_map[index] for index in target),
        ),
        edge_features=example.label.graph.edge_features,
        context_features=example.label.graph.context_features,
        graph_hash="label-permuted", label_count=4, task_count=3,
    )
    cell_order = tuple(reversed(range(64)))
    cell_map = {old: new for new, old in enumerate(cell_order)}
    cell_source, cell_target = example.cell.edge_index
    cell_graph = CellMassGraph(
        node_features=tuple(example.cell.node_features[index] for index in cell_order),
        edge_index=(
            tuple(cell_map[index] for index in cell_source),
            tuple(cell_map[index] for index in cell_target),
        ),
        edge_features=example.cell.edge_features,
        context_features=example.cell.context_features, graph_hash="cell-permuted",
    )
    label = BaseFrontierExample(
        **{
            **example.label.__dict__,
            "graph": label_graph,
        }
    )
    value = MultiResolutionExample(
        label=label, cell=cell_graph,
        cell_graph_build_wall_seconds=example.cell_graph_build_wall_seconds,
    )
    value.validate()
    return value


def test_two_view_gat_pooling_is_permutation_invariant() -> None:
    model = build_multires_model(kind="gat", dropout=0.0).double().eval()
    with __import__("torch").no_grad():
        left = model(graph=multires_tensors(_example(), _normalization()))
        right = model(graph=multires_tensors(_permuted(_example()), _normalization()))
    for name in left:
        assert float(left[name]) == pytest.approx(float(right[name]), abs=1.0e-12)


def test_shuffled_topology_changes_both_endpoint_sets_only() -> None:
    tensors = multires_tensors(_example(), _normalization())
    left = shuffled_multires_tensors(tensors, state_hash="abc")
    right = shuffled_multires_tensors(tensors, state_hash="abc")
    for view in ("label", "cell"):
        assert left[view]["edge_index"].equal(right[view]["edge_index"])
        assert not left[view]["edge_index"].equal(tensors[view]["edge_index"])
        assert left[view]["node_features"].equal(tensors[view]["node_features"])
        assert left[view]["edge_features"].equal(tensors[view]["edge_features"])


def test_context_binding_mismatch_is_rejected() -> None:
    example = _example()
    bad_cell = CellMassGraph(
        **{**example.cell.__dict__, "context_features": tuple(value + 1.0 for value in example.cell.context_features)}
    )
    with pytest.raises(ValueError, match="context binding mismatch"):
        MultiResolutionExample(
            label=example.label, cell=bad_cell,
            cell_graph_build_wall_seconds=0.001,
        ).validate()


def test_config_has_no_extra_pop_prefix_or_failed_arms() -> None:
    config = json.loads((
        ROOT / "configs/experiments/p0v5_multires_frontier_observability_v9r1.json"
    ).read_text(encoding="utf-8"))
    assert config["additional_label_pops"] == 0
    assert config["auxiliary_prefix_requests"] == 0
    assert config["forced_veto"] == ["QB1", "QGR1"]
    assert config["model"]["candidate"] == "gat"
    assert config["diagnostic_only"] is True
