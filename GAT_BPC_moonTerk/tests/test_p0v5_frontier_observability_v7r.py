from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.p0v5_frontier_observability_v7r_common import (
    binomial_tail_at_least,
    candidate_cap,
    wilson_interval,
)
from scripts.run_p0v5_frontier_feature_sufficiency_v7r import _dataset
from scripts.run_p0v5_frontier_switch_matrix_v7r import _schedule


def _graph(tag: str = "g"):
    return {
        "graph_hash": tag,
        "node_features": [[0.0] * 16 for _ in range(64)],
        "edges": [{"source": index, "target": index,
                   "features": [1.0] + [0.0] * 9} for index in range(64)],
        "context_features": [0.0] * 28,
    }


def test_candidate_cap_is_probability_backed():
    cap = candidate_cap(8, 0.2, 0.95)
    assert cap is not None and cap >= 8
    assert binomial_tail_at_least(cap, 8, 0.2) >= 0.95
    assert binomial_tail_at_least(cap - 1, 8, 0.2) < 0.95
    lower, upper = wilson_interval(4, 20)
    assert 0.0 < lower < 0.2 < upper < 1.0


def test_switch_schedule_is_blocked_and_deterministic():
    config = {
        "actions": ["QPF0", "QPD1"],
        "execution": {"replay_caps_sec": {"30": 300, "50": 600}},
    }
    contexts = [{"context_id": "c", "instance_content_hash": "i",
                 "scale": 30, "state_hash": "s"}]
    left = _schedule(config, contexts)
    right = _schedule(config, contexts)
    assert left == right
    assert len(left["tasks"]) == 6
    for block in range(3):
        assert {row["arm"] for row in left["tasks"] if row["block"] == block} == {
            "QPF0", "QPD1"
        }


def test_diagnostic_dataset_keeps_instance_weight_one_and_grouped_fold():
    outcomes = []
    for ordinal in range(2):
        outcomes.append({
            "determined": True, "instance_hash": "same", "scale": 30,
            "context_id": f"c{ordinal}", "state_hash": f"s{ordinal}",
            "ratio": 0.9 + ordinal * 0.01, "adverse": False,
            "qpf0_graph": _graph(f"g{ordinal}"),
        })
    for scale in (30, 50):
        for ordinal in range(6):
            outcomes.append({
                "determined": True, "instance_hash": f"i{scale}_{ordinal}",
                "scale": scale, "context_id": f"c{scale}_{ordinal}",
                "state_hash": f"s{scale}_{ordinal}", "ratio": 1.01,
                "adverse": False, "qpf0_graph": _graph(f"g{scale}_{ordinal}"),
            })
    rows = _dataset(outcomes, 5)
    same = [row for row in rows if row["instance_hash"] == "same"]
    assert sum(row["context_weight"] for row in same) == 1.0
    assert len({row["fold"] for row in same}) == 1


def test_v7_is_terminal_and_v7r_contract_forbids_candidate_training():
    terminal = json.loads((
        ROOT / "runs/p0v5_native_frontier_gat_qd1_selector_v7_20260817/terminal_decision.json"
    ).read_text())
    config = json.loads((
        ROOT / "configs/experiments/p0v5_frontier_observability_root_cause_v7r.json"
    ).read_text())
    assert terminal["decision"] == "FAIL"
    assert terminal["reason"] == "NO_FRONTIER_SWITCH_HEADROOM"
    assert config["candidate_training_forbidden"] is True
    assert config["threshold_search_forbidden"] is True
    assert config["manifest_generation_forbidden"] is True

