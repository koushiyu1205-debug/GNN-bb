from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lunar_ice_bpc.exact.bpc.pricing.backends.base import BackendPricingRequest
from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
    _native_request_payload,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from scripts.freeze_p0v5_temporal_frontier_late_switch_pilot_v10 import (
    _schedule,
)
from scripts.initialize_p0v5_temporal_frontier_late_switch_oracle_v10 import (
    _select_rows,
)
from scripts.run_p0v5_temporal_frontier_late_switch_matrix_v10 import _gate


def _request(scale: int = 30) -> BackendPricingRequest:
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
        pricing_lifecycle_scope="root_cg",
        proof_queue_policy_id="Q0",
        proof_tail_fallback_context=True,
        instance_hash=data.instance_content_hash,
        config_hash="config-v10-test",
        engine_hash="engine-v10-test",
    )


def test_temporal_frontier_boundaries_reach_native_payload() -> None:
    request = replace(
        _request(scale=50),
        proof_tail_frontier_probe_mode="force_qd1",
        proof_tail_frontier_probe_boundary=16_384,
        proof_tail_frontier_observation_boundaries=(4096, 8192, 16_384),
    )
    payload = _native_request_payload(request)
    assert payload["proof_queue_policy_id"] == "Q0"
    assert payload["proof_queue_frontier_probe_mode"] == "force_qd1"
    assert payload["proof_queue_frontier_probe_boundary"] == 16_384
    assert payload["proof_queue_frontier_observation_boundaries"] == [
        4096,
        8192,
        16_384,
    ]


@pytest.mark.parametrize(
    "scale,boundary,k",
    ((30, 4096, 128), (50, 16_384, 512)),
)
def test_reversible_trial_contract_reaches_native_payload(
    scale: int, boundary: int, k: int,
) -> None:
    request = replace(
        _request(scale=scale),
        proof_tail_frontier_probe_mode="force_trial_revert",
        proof_tail_frontier_probe_boundary=boundary,
        proof_tail_frontier_trial_pop_budget=k,
    )
    payload = _native_request_payload(request)
    assert payload["proof_queue_policy_id"] == "Q0"
    assert payload["proof_queue_frontier_probe_mode"] == "force_trial_revert"
    assert payload["proof_queue_frontier_trial_pop_budget"] == k
    assert payload["proof_queue_frontier_problem_scale"] == scale
    assert payload["proof_queue_frontier_pricing_lifecycle"] == "root_cg"


def test_reversible_trial_rejects_wrong_scope_boundary_and_k() -> None:
    with pytest.raises(ValueError, match="temporal trial boundary"):
        replace(
            _request(scale=50),
            proof_tail_frontier_probe_mode="collect_trial",
            proof_tail_frontier_probe_boundary=4096,
            proof_tail_frontier_trial_pop_budget=128,
        )
    with pytest.raises(ValueError, match="128/512/2048"):
        replace(
            _request(scale=30),
            proof_tail_frontier_probe_mode="collect_trial",
            proof_tail_frontier_trial_pop_budget=64,
        )
    with pytest.raises(ValueError, match="root-CG only"):
        replace(
            _request(scale=30),
            pricing_lifecycle_scope="tree_node",
            proof_tail_frontier_probe_mode="collect_trial",
            proof_tail_frontier_trial_pop_budget=128,
        )


@pytest.mark.parametrize(
    "mode,boundary,observations",
    (
        ("disabled", 4096, (4096,)),
        ("collect_force_q0", 8192, (8192,)),
        ("collect_force_q0", 8192, (4096, 16_384)),
        ("collect_force_q0", 16_384, (4096, 16_384)),
        ("force_qd1", 4096, (4096, 4096)),
    ),
)
def test_temporal_frontier_rejects_noncanonical_boundaries(
    mode: str,
    boundary: int,
    observations: tuple[int, ...],
) -> None:
    with pytest.raises(ValueError, match="temporal frontier observations"):
        replace(
            _request(scale=50),
            proof_tail_frontier_probe_mode=mode,
            proof_tail_frontier_probe_boundary=boundary,
            proof_tail_frontier_observation_boundaries=observations,
        )


def test_legacy_v7_probe_remains_exactly_4096_without_observations() -> None:
    legacy = replace(
        _request(),
        proof_tail_frontier_probe_mode="collect_force_q0",
    )
    assert legacy.proof_tail_frontier_probe_boundary == 4096
    assert legacy.proof_tail_frontier_observation_boundaries == ()
    with pytest.raises(ValueError, match="legacy frontier probe boundary"):
        replace(legacy, proof_tail_frontier_probe_boundary=8192)


def test_native_disabled_mode_accepts_empty_observation_vector() -> None:
    native = pytest.importorskip("lunar_spprc_native")
    if "frontier_temporal_observation_policy" not in native.build_info():
        pytest.skip("V10 Native binary is not active")
    raw = dict(native.solve(_native_request_payload(_request(scale=5))))
    assert str(raw["status"]).lower() in {"exhaustive", "complete"}
    telemetry = dict(raw.get("telemetry") or {})
    frontier = dict(telemetry.get("proof_queue_frontier_probe") or {})
    assert frontier.get("enabled") is False
    assert frontier.get("observation_boundaries") == []


def test_pilot_selection_is_instance_first_and_outcome_blind() -> None:
    rows = []
    for scale in (30, 50):
        for instance in range(10):
            for context in range(2):
                rows.append({
                    "scale": scale,
                    "instance_content_hash": f"s{scale}-i{instance}",
                    "context_id": f"s{scale}-i{instance}-c{context}",
                    "state_hash": f"state-{scale}-{instance}-{context}",
                })
    selected = _select_rows(rows, 8)
    assert len(selected) == 16
    for scale in (30, 50):
        scale_rows = [row for row in selected if row["scale"] == scale]
        assert len(scale_rows) == 8
        assert len({row["instance_content_hash"] for row in scale_rows}) == 8
    assert selected == _select_rows(list(reversed(rows)), 8)


def test_frozen_schedule_has_240_single_process_tasks() -> None:
    contexts = []
    for scale in (30, 50):
        for index in range(8):
            contexts.append({
                "context_id": f"s{scale}-c{index}",
                "instance_content_hash": f"s{scale}-i{index}",
                "scale": scale,
                "state_hash": f"state-{scale}-{index}",
            })
    config = {
        "execution": {
            "blocked_fresh_process_repeats": 3,
            "replay_caps_sec": {"30": 300, "50": 600},
        },
        "decision_boundaries": {"30": [4096], "50": [4096, 8192, 16384]},
        "observation_prefixes": {
            "4096": [4096],
            "8192": [4096, 8192],
            "16384": [4096, 8192, 16384],
        },
    }
    schedule = _schedule(config, contexts)
    assert schedule["task_count"] == 240
    assert schedule["single_native_process"] is True
    assert sum(row["arm_id"] == "Q0" for row in schedule["tasks"]) == 48


def _collapsed(scale: int, boundary: int, ratios: tuple[float, ...]):
    return [{
        "context_id": f"s{scale}-b{boundary}-c{index}",
        "scale": scale,
        "instance_hash": f"s{scale}-i{index}",
        "decision_boundary": boundary,
        "determined": True,
        "probe_ratio": 1.001,
        "switch_ratio": ratio / 1.001,
        "net_ratio": ratio,
        "resource_censor_positive": False,
        "correctness_redlines": [],
    } for index, ratio in enumerate(ratios)]


def test_gate_selects_best_passing_late_scale50_boundary() -> None:
    config = {
        "decision_boundaries": {"30": [4096], "50": [4096, 8192, 16384]},
        "probe_overhead_gate": {"gm_at_most": 1.01, "worst_ratio_at_most": 1.05},
        "scale30_gate": {
            "minimum_determined_instances": 7,
            "minimum_qpd1_winner_instances": 5,
            "net_oracle_gm_at_most": 0.95,
            "fixed_qpd1_net_gm_at_most": 0.98,
        },
        "scale50_boundary_gate": {
            "minimum_determined_instances": 7,
            "minimum_qpd1_winner_instances": 3,
            "minimum_strong_benefit_instances": 2,
            "minimum_neutral_or_harm_instances": 2,
            "net_oracle_gm_at_most": 0.95,
        },
    }
    rows = _collapsed(30, 4096, (0.8, 0.82, 0.84, 0.86, 0.88, 0.9, 0.92, 1.0))
    rows += _collapsed(50, 4096, (0.6, 0.7, 0.9, 1.0, 1.02, 1.1, 1.2, 1.3))
    rows += _collapsed(50, 8192, (0.65, 0.75, 0.85, 0.9, 0.99, 1.0, 1.05, 1.08))
    rows += _collapsed(50, 16384, (0.7, 0.8, 0.9, 0.99, 1.0, 1.02, 1.05, 1.08))
    decision = _gate(config, rows)
    assert decision["decision"] == "PASS"
    assert decision["selected_scale30_boundary"] == 4096
    assert decision["selected_scale50_boundary"] in {4096, 8192, 16384}
    passing = decision["passing_boundaries"]["50"]
    assert decision["selected_scale50_boundary"] == min(
        passing,
        key=lambda boundary: (
            decision["boundary_metrics"]["50"][str(boundary)]["net_oracle_gm"],
            boundary,
        ),
    )
