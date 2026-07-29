from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "scripts/run_p0_no_task_wait_v3_branch_child_trajectory.py"
)
SPEC = importlib.util.spec_from_file_location(
    "p0_no_task_wait_v3_branch_child_trajectory",
    SCRIPT,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_node_primal_columns_prefers_live_master() -> None:
    master_rows = ({"column_id": "master"},)
    payload = {
        "primal_columns": [{"column_id": "stale"}],
        "_master": SimpleNamespace(
            rmp=SimpleNamespace(primal_columns=master_rows)
        ),
    }

    assert MODULE._node_primal_columns(payload) == master_rows


def test_continuation_child_map_uses_path_rank_and_sense() -> None:
    report = {
        "state_reports": [
            {
                "path_hash": "path",
                "pair_reports": [
                    {
                        "rank_index": 2,
                        "children": [
                            {"branch_sense": "same_journey"},
                            {"branch_sense": "different_journey"},
                        ],
                    }
                ],
            }
        ]
    }

    rows = MODULE._continuation_child_map(report)

    assert set(rows) == {
        "path:rank=2:sense=same_journey",
        "path:rank=2:sense=different_journey",
    }


def test_progress_binding_binds_continuation_report_hash() -> None:
    class Data:
        instance_content_hash = "instance"

    binding = MODULE._progress_binding(
        data=Data(),
        split_manifest_hash="split",
        root_payload={"root": 1},
        control={"control": 1},
        probe_budget_sec=180.0,
        preference_margin_sec=2.0,
        lifecycle_overhead_sec=0.02,
        continuation_report_sha256="prior",
    )

    assert binding["continuation_report_sha256"] == "prior"
    assert binding["progress_binding_hash"]


def test_gold_label_requires_v2_same_counterfactual_universe() -> None:
    report = {
        "schema_version": (
            "lunar_ice_bpc.no_task_wait_v3_branch_state_oracle.v2"
        ),
        "control": {"matched_end_to_end_wall_sec": 10.0},
        "state_reports": [
            {
                "path_hash": "path",
                "top3_candidate_ids": ["a", "b", "c"],
                "complete_matched_e2e_gold": True,
                "eligible_alternative_count": 2,
                "oracle_selected_rank_index": 1,
                "oracle_net_gain_sec": 2.0,
                "oracle_net_gain_ratio": 0.2,
                "arms": [
                    {
                        "requested_rank_index": 1,
                        "exact_safe": True,
                        "counterfactual_universe_matches_control": True,
                        "matched_end_to_end_wall_sec": 8.0,
                    },
                    {
                        "requested_rank_index": 2,
                        "exact_safe": True,
                        "counterfactual_universe_matches_control": True,
                        "matched_end_to_end_wall_sec": 9.0,
                    },
                ],
            }
        ],
    }

    accepted = MODULE._gold_label_for_state(
        report,
        path_hash="path",
        candidate_ids=["a", "b", "c"],
    )
    rejected = MODULE._gold_label_for_state(
        report,
        path_hash="path",
        candidate_ids=["a", "c", "b"],
    )

    assert accepted is not None
    assert accepted["oracle_selected_rank_index"] == 1
    assert rejected is None


def _child(*, exact: bool, wall: float, status: str | None = None) -> dict:
    return {
        "observed_wall_sec": wall,
        "event_observed": exact,
        "node_status": status or (
            "NODE_LP_CERTIFIED" if exact else "NODE_INCOMPLETE"
        ),
    }


def _pair(
    *,
    rank: int,
    exact_cost: float | None,
    lower_bound: float,
) -> dict:
    return {
        "candidate_id": f"branch_pair:a|{rank}",
        "rank_index": rank,
        "pair_exact_work_sec": exact_cost,
        "pair_observed_work_lower_bound_sec": lower_bound,
    }


def test_pair_target_is_seconds_without_legacy_cost_or_timeout_penalty() -> None:
    pair = MODULE._pair_summary(
        rank_index=1,
        candidate_id="branch_pair:a|b",
        children=[
            _child(exact=True, wall=3.0),
            _child(exact=True, wall=5.0),
        ],
        lifecycle_overhead_sec=0.02,
    )

    assert pair["pair_exact_work_sec"] == 8.02
    assert pair["pair_cost_semantics"] == (
        "same_child_wall_sec_plus_different_child_wall_sec"
    )
    assert pair["legacy_normalized_cost_present"] is False
    assert pair["fixed_timeout_penalty_present"] is False


def test_incomplete_pair_is_right_censored_lower_bound() -> None:
    pair = MODULE._pair_summary(
        rank_index=0,
        candidate_id="branch_pair:a|b",
        children=[
            _child(exact=True, wall=3.0),
            _child(exact=False, wall=7.0),
        ],
        lifecycle_overhead_sec=10.0,
    )

    assert pair["pair_exact_work_sec"] is None
    assert pair["pair_observed_work_lower_bound_sec"] == 10.0
    assert pair["right_censored"] is True


def test_node_probe_exact_safe_uses_official_engine_certificate_gates() -> None:
    payload = {
        "node_status": "NODE_LP_CERTIFIED",
        "certificate_scope": "BPC_NODE_LP_CERTIFIED",
        "pricing_state": "CERTIFIED_NO_NEGATIVE",
        "node_lp_bound_official": True,
        "uses_true_dual_bpc_certificate": True,
        "certificate_ledger": {"valid": True},
        "manual_rc_audit_pass": True,
        "pricing_rc_audit_pass": True,
        "final_judge_certifying_proof_kind": True,
        "branch_pricing_audit_pass": True,
        "cut_pricing_audit_pass": True,
    }

    assert MODULE._node_probe_exact_safe(payload)
    payload["branch_pricing_audit_pass"] = False
    assert not MODULE._node_probe_exact_safe(payload)


def test_exact_pair_can_soundly_beat_censored_lower_bound() -> None:
    exact = _pair(rank=0, exact_cost=8.0, lower_bound=8.0)
    censored = _pair(rank=1, exact_cost=None, lower_bound=12.0)

    preference = MODULE._strict_preference(
        exact,
        censored,
        margin_sec=2.0,
    )

    assert preference is not None
    assert preference["winner_rank_index"] == 0
    assert preference["evidence"] == (
        "EXACT_BEATS_CENSORED_LOWER_BOUND"
    )


def test_unclear_censored_pairs_do_not_create_arbitrary_preference() -> None:
    left = _pair(rank=0, exact_cost=None, lower_bound=8.0)
    right = _pair(rank=1, exact_cost=None, lower_bound=12.0)

    assert (
        MODULE._strict_preference(left, right, margin_sec=2.0)
        is None
    )


def test_survival_rows_keep_events_and_censoring_without_fake_negative() -> None:
    pairs = [
        {
            "candidate_id": "branch_pair:a|b",
            "rank_index": 0,
            "children": [
                {
                    "branch_sense": "same_journey",
                    "observed_wall_sec": 3.0,
                    "event_observed": True,
                },
                {
                    "branch_sense": "different_journey",
                    "observed_wall_sec": 7.0,
                    "event_observed": False,
                },
            ],
        }
    ]

    rows = MODULE._survival_training_rows(
        instance_content_hash="content",
        scale=20,
        path_hash="path",
        pairs=pairs,
    )

    assert rows[0]["event_time_sec"] == 3.0
    assert rows[0]["censoring_time_sec"] is None
    assert rows[1]["event_time_sec"] is None
    assert rows[1]["censoring_time_sec"] == 7.0
    assert all(
        row["unexplored_candidate_negative"] is False for row in rows
    )


def test_diagnostic_lower_bound_order_is_deterministic() -> None:
    pairs = [
        _pair(rank=0, exact_cost=None, lower_bound=160.0),
        _pair(rank=1, exact_cost=None, lower_bound=180.0),
        _pair(rank=2, exact_cost=None, lower_bound=143.0),
    ]

    assert MODULE._diagnostic_lower_bound_order(pairs) == [2, 0, 1]


def test_horizon_replay_preserves_early_event_and_censors_late_event() -> None:
    pair = {
        "candidate_id": "branch_pair:a|b",
        "rank_index": 2,
        "guidance_lifecycle_overhead_sec": 0.02,
        "children": [
            {
                "branch_sense": "same_journey",
                "observed_wall_sec": 90.0,
                "event_observed": False,
                "node_status": "NODE_INCOMPLETE",
            },
            {
                "branch_sense": "different_journey",
                "observed_wall_sec": 53.0,
                "event_observed": True,
                "node_status": "NODE_LP_CERTIFIED",
            },
        ],
    }

    replay = MODULE._replay_pair_at_horizon(pair, horizon_sec=60.0)

    assert replay is not None
    assert replay["pair_exact_work_sec"] is None
    assert replay["pair_observed_work_lower_bound_sec"] == 113.02
    assert replay["children"][0]["right_censored"] is True
    assert replay["children"][1]["event_observed"] is True


def test_horizon_replay_rejects_extrapolation_past_earlier_censoring() -> None:
    pair = {
        "candidate_id": "branch_pair:a|b",
        "rank_index": 0,
        "guidance_lifecycle_overhead_sec": 0.0,
        "children": [
            {
                "observed_wall_sec": 30.0,
                "event_observed": False,
            },
            {
                "observed_wall_sec": 30.0,
                "event_observed": False,
            },
        ],
    }

    assert MODULE._replay_pair_at_horizon(
        pair,
        horizon_sec=60.0,
    ) is None


def test_sequential_race_budget_stops_when_alt_cannot_beat_p0() -> None:
    assert MODULE._race_budget(
        base_budget_sec=60.0,
        p0_exact_pair_work_sec=100.0,
        accumulated_alt_work_sec=105.0,
        lifecycle_overhead_sec=0.02,
        margin_sec=2.0,
    ) == 0.0
    assert MODULE._race_budget(
        base_budget_sec=60.0,
        p0_exact_pair_work_sec=None,
        accumulated_alt_work_sec=105.0,
        lifecycle_overhead_sec=0.02,
        margin_sec=2.0,
    ) == 60.0


def test_progress_binding_changes_with_budget_and_probe_key_is_stable() -> None:
    class Data:
        instance_content_hash = "content"

    common = {
        "data": Data(),
        "split_manifest_hash": "split",
        "root_payload": {"root": 1},
        "control": {"tree": 1},
        "preference_margin_sec": 2.0,
        "lifecycle_overhead_sec": 0.02,
    }
    first = MODULE._progress_binding(
        **common,
        probe_budget_sec=30.0,
    )
    second = MODULE._progress_binding(
        **common,
        probe_budget_sec=60.0,
    )

    assert first["progress_binding_hash"] != second[
        "progress_binding_hash"
    ]
    assert MODULE._probe_key(
        path_hash="abc",
        rank_index=2,
        branch_sense="same_journey",
    ) == "abc:rank=2:sense=same_journey"


def test_actionable_state_rejects_universe_change() -> None:
    candidate = {
        "task_a": "a",
        "task_b": "b",
        "same_child_context": {
            "pair_decisions": [
                {"task_a": "a", "task_b": "b", "sense": "same_journey"}
            ]
        },
        "different_child_context": {
            "pair_decisions": [
                {
                    "task_a": "a",
                    "task_b": "b",
                    "sense": "different_journey",
                }
            ]
        },
    }
    base = {
        "node_id": "node_000",
        "node_status": "BRANCHED",
        "requested_node_status": "NODE_LP_CERTIFIED",
        "certificate_scope": "BPC_NODE_LP_CERTIFIED",
        "pricing_state": "CERTIFIED_NO_NEGATIVE",
        "node_lp_bound_official": True,
        "uses_true_dual_bpc_certificate": True,
        "manual_rc_audit_pass": True,
        "pricing_rc_audit_pass": True,
        "final_judge_certifying_proof_kind": True,
        "certificate_ledger": {"valid": True},
        "development_branch_selected_rank_index": 0,
        "development_branch_path_signature": [],
        "legal_branch_shortlist_hash_before_sort": "same",
        "legal_branch_shortlist_hash_after_sort": "different",
        "guidance_branch_pair_drop_count": 0,
        "fractional_branch_probe": {
            "candidates": [candidate, candidate, candidate]
        },
    }

    assert MODULE._actionable_state_rows({"nodes": [base]}) == []


def test_exact_opportunity_root_is_parent_snapshot_eligible() -> None:
    candidate = {
        "task_a": "a",
        "task_b": "b",
        "same_child_context": {"pair_decisions": []},
        "different_child_context": {"pair_decisions": []},
    }
    node = {
        "node_id": "node_000",
        "depth": 0,
        "node_status": "INCOMPLETE",
        "opportunity_parent_snapshot_eligible": True,
        "requested_node_status": "NODE_LP_CERTIFIED",
        "certificate_scope": "BPC_NODE_LP_CERTIFIED",
        "pricing_state": "CERTIFIED_NO_NEGATIVE",
        "node_lp_bound": 1.0,
        "node_lp_bound_official": True,
        "uses_true_dual_bpc_certificate": True,
        "manual_rc_audit_pass": True,
        "pricing_rc_audit_pass": True,
        "final_judge_certifying_proof_kind": True,
        "certificate_ledger": {"valid": True},
        "development_branch_selected_rank_index": 0,
        "development_branch_path_signature": [],
        "legal_branch_shortlist_hash_before_sort": "same",
        "legal_branch_shortlist_hash_after_sort": "same",
        "guidance_branch_pair_drop_count": 0,
        "fractional_branch_probe": {
            "candidates": [candidate, candidate, candidate]
        },
    }

    rows = MODULE._actionable_state_rows({"nodes": [node]})

    assert len(rows) == 1
    assert rows[0]["node_lp_bound"] == 1.0


def test_exact_opportunity_report_can_bind_unannotated_control() -> None:
    node = {
        "node_id": "node_000",
        "depth": 0,
        "node_status": "INCOMPLETE",
        "requested_node_status": "NODE_LP_CERTIFIED",
        "certificate_scope": "BPC_NODE_LP_CERTIFIED",
        "pricing_state": "CERTIFIED_NO_NEGATIVE",
        "node_lp_bound": 1.0,
        "node_lp_bound_official": True,
        "uses_true_dual_bpc_certificate": True,
        "manual_rc_audit_pass": True,
        "pricing_rc_audit_pass": True,
        "final_judge_certifying_proof_kind": True,
        "certificate_ledger": {"valid": True},
        "fractional_branch_probe": {
            "candidates": [
                {"task_a": "a", "task_b": "b"},
                {"task_a": "a", "task_b": "c"},
                {"task_a": "b", "task_b": "c"},
            ]
        },
    }
    control = {"nodes": [node]}
    opportunity = {
        "opportunity_status": "EXACT_ACTIONABLE_ROOT",
        "p0_root_node_exact_safe": True,
        "candidate_count": 3,
        "tree_result_sha256": MODULE._sha256_json(control),
        "legal_branch_shortlist_hash_before_sort": "universe",
        "legal_branch_shortlist_hash_after_sort": "universe",
    }

    bound, applied = MODULE._bind_exact_opportunity_control(
        control,
        opportunity,
    )

    assert applied
    assert bound["nodes"][0]["opportunity_parent_snapshot_eligible"]


def test_cut_context_and_lineage_round_trip_validate() -> None:
    context_payload = {
        "cut_count": 1,
        "cuts": [
            {
                "cut_id": "sri:a,b,c",
                "cut_type": "subset_row",
                "tasks": ["c", "a", "b"],
                "divisor": 2,
                "rhs": 1.0,
            }
        ],
    }
    lineage_payload = {
        "entry_count": 1,
        "policy_version": "native_live_sri_bpc_v1",
        "entries": [
            {
                "cut_id": "sri:a,b,c",
                "scope": "global",
                "origin_node_id": "node_000",
                "ancestor_path": [],
                "policy_version": "native_live_sri_bpc_v1",
            }
        ],
    }

    context = MODULE._cut_context_from_payload(context_payload)
    lineage = MODULE._cut_lineage_from_payload(lineage_payload)

    assert lineage.validate_context(context) == ()
    assert context.cuts[0].tasks == ("a", "b", "c")
