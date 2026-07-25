from __future__ import annotations

from copy import deepcopy

import pytest

from lunar_ice_bpc.guidance.proof_tail_gate import (
    audit_static_proof_tail_scale_rule,
    build_proof_tail_gate_dataset,
    build_proof_tail_policy_pair,
)


def _arm(policy: str, wall: float) -> dict:
    return {
        "proof_queue_policy_id": policy,
        "fresh_process_arm": True,
        "engine_status": "COMPLETE",
        "search_exhaustive": True,
        "frontier_empty": True,
        "labels_dropped": False,
        "certificate_blockers": [],
        "can_enter_certificate_audit": True,
        "global_min_rc": None,
        "global_min_rc_is_exact": False,
        "proved_no_rc_below": -1.0e-6,
        "total_fresh_process_wall_sec": wall + 0.1,
        "scale": 30,
        "completion_bound_enabled": False,
        "subset_dominance_enabled": True,
        "negative_eps": 1.0e-6,
        "dominance_eps": 1.0e-12,
        "resource_eps": 1.0e-9,
        "wall_time_limit_sec": 120.0,
        "memory_limit_gb": 10.0,
        "same_mathematical_request_as_source": {
            "instance": True,
            "objective_mode": True,
            "mathematical_dual": True,
            "branch_context": True,
            "full_cut_context": True,
        },
        "pre_call_features": {
            "feature_schema_version": (
                "lunar_ice_bpc.proof_tail_pre_call_features.v1"
            ),
            "scale": 30,
            "task_count": 30,
        },
        "replay_binding": {
            "instance_hash": "instance",
            "pricing_mode": "exact_proof",
            "phase": "phase_two",
            "objective_mode": "official",
            "mathematical_dual_hash": "dual",
            "branch_context_hash": "branch",
            "full_cut_context_hash": "cuts",
            "projected_pricing_cut_context_hash": "pricing-cuts",
            "cut_lineage_hash": "lineage",
            "live_cut_policy_hash": "live",
            "separator_policy_version": "separator",
            "cut_state_schema_version": "cut-state",
        },
        "proof_telemetry": {
            "wall_time_seconds": wall,
            "extended_labels": 100,
            "dominance_wall_time_seconds": wall * 0.7,
            "native_engine_build_hash": "engine",
        },
    }


def test_proof_tail_pair_uses_net_wall_not_label_count() -> None:
    qc0 = _arm("QC0", 10.0)
    qd1 = _arm("QD1", 9.0)
    qd1["proof_telemetry"]["extended_labels"] = 120
    pair = build_proof_tail_policy_pair(
        qc0,
        qd1,
        replicate_id="rep-1",
        pair_run_order="QD1_THEN_QC0",
        gate_wall_sec_upper_bound=0.2,
        promotion_margin_sec=0.1,
    )

    assert pair["target_policy_id"] == "QD1"
    assert pair["net_delta_qd1_minus_qc0_sec"] == pytest.approx(-0.8)
    assert pair["qd1_extended_labels"] > pair["qc0_extended_labels"]


def test_proof_tail_pair_rejects_binding_or_exact_result_mismatch() -> None:
    qc0 = _arm("QC0", 10.0)
    qd1 = _arm("QD1", 9.0)
    qd1["replay_binding"]["mathematical_dual_hash"] = "other"
    with pytest.raises(ValueError, match="context binding mismatch"):
        build_proof_tail_policy_pair(
            qc0,
            qd1,
            replicate_id="rep-1",
            pair_run_order="QC0_THEN_QD1",
        )

    qd1 = _arm("QD1", 9.0)
    qd1["proved_no_rc_below"] = None
    qd1["global_min_rc"] = -0.1
    qd1["global_min_rc_is_exact"] = True
    with pytest.raises(ValueError, match="threshold outcomes differ"):
        build_proof_tail_policy_pair(
            qc0,
            qd1,
            replicate_id="rep-1",
            pair_run_order="QC0_THEN_QD1",
        )


def test_repetitions_do_not_inflate_independent_context_count() -> None:
    pair_one = build_proof_tail_policy_pair(
        _arm("QC0", 10.0),
        _arm("QD1", 9.0),
        replicate_id="rep-1",
        pair_run_order="QC0_THEN_QD1",
    )
    pair_two = deepcopy(pair_one)
    pair_two["replicate_id"] = "rep-2"
    dataset = build_proof_tail_gate_dataset((pair_one, pair_two))

    assert dataset["pair_count"] == 2
    assert dataset["independent_context_count"] == 1
    assert dataset["contexts"][0]["replicate_count"] == 2
    assert dataset["contexts"][0]["pre_call_features"] == (
        pair_one["pre_call_features"]
    )
    assert not dataset["repeat_rows_count_as_independent_contexts"]


def test_static_scale_rule_stays_non_promotable_below_context_quota() -> None:
    scale20 = build_proof_tail_policy_pair(
        {**_arm("QC0", 1.0), "scale": 20},
        {**_arm("QD1", 1.2), "scale": 20},
        replicate_id="scale20",
        pair_run_order="QC0_THEN_QD1",
    )
    scale20["context"]["scale"] = 20
    scale30 = build_proof_tail_policy_pair(
        _arm("QC0", 10.0),
        _arm("QD1", 9.0),
        replicate_id="scale30",
        pair_run_order="QD1_THEN_QC0",
        gate_wall_sec_upper_bound=0.1,
    )
    dataset = build_proof_tail_gate_dataset((scale20, scale30))
    audit = audit_static_proof_tail_scale_rule(
        dataset,
        minimum_contexts_per_scale=2,
        bootstrap_samples=100,
    )

    assert audit["wall_ratio_selected_over_qc0"] < 1.0
    assert audit["by_scale"]["20"]["selected_policy_id"] == "QC0"
    assert audit["by_scale"]["30"]["selected_policy_id"] == "QD1"
    assert audit["safety_gate_passed"]
    assert audit["statistical_benefit_passed"]
    assert (
        audit["by_scale"]["30"][
            "bootstrap_mean_saving_lcb95_sec"
        ]
        > 0.0
    )
    assert not audit["minimum_context_quota_met"]
    assert not audit["promotion_evaluable"]
    assert not audit["promotion_passed"]
