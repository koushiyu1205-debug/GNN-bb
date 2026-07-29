from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from lunar_ice_bpc.exact.bpc.cuts.live_sri import LiveSriPolicy
from lunar_ice_bpc.exact.bpc.guidance.contracts import (
    canonical_universe_hash,
)
from lunar_ice_bpc.guidance.branch_counterfactual_tree_solver import (
    _branch_candidate_id,
    _development_certified_node_continuation,
    _development_certified_root_continuation,
    _selected_fractional_candidate,
)
from lunar_ice_bpc.exact.core.cuts import CutContext, CutLineage


ROOT = Path(__file__).resolve().parents[1]
DEEP_RUNNER = (
    ROOT / "scripts/run_p0v3_branch_deep_snapshot_e2e_oracle.py"
)
SPEC = importlib.util.spec_from_file_location(
    "p0v3_branch_deep_snapshot_e2e_oracle",
    DEEP_RUNNER,
)
assert SPEC is not None and SPEC.loader is not None
DEEP_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DEEP_MODULE)


def _node(candidate_count: int) -> dict:
    return {
        "fractional_branch_probe": {
            "candidates": [
                {
                    "task_a": f"task_{index:02d}",
                    "task_b": f"task_{index + 1:02d}",
                }
                for index in range(candidate_count)
            ]
        }
    }


def test_development_branch_rank_selects_only_inside_existing_shortlist() -> None:
    candidate, selected_rank, fallback = _selected_fractional_candidate(
        _node(3),
        requested_rank_index=2,
    )
    assert candidate == {"task_a": "task_02", "task_b": "task_03"}
    assert selected_rank == 2
    assert fallback is False


def test_development_branch_rank_falls_back_to_p0_when_rank_is_missing() -> None:
    candidate, selected_rank, fallback = _selected_fractional_candidate(
        _node(1),
        requested_rank_index=2,
    )
    assert candidate == {"task_a": "task_00", "task_b": "task_01"}
    assert selected_rank == 0
    assert fallback is True

    missing, missing_rank, missing_fallback = (
        _selected_fractional_candidate(
            _node(0),
            requested_rank_index=2,
        )
    )
    assert missing is None
    assert missing_rank is None
    assert missing_fallback is False


def test_development_branch_rank_rejects_out_of_universe_rank() -> None:
    with pytest.raises(ValueError, match="one of 0, 1, or 2"):
        _selected_fractional_candidate(
            _node(3),
            requested_rank_index=3,
        )


def test_branch_candidate_id_is_pair_symmetric() -> None:
    assert _branch_candidate_id(
        {"task_a": "right", "task_b": "left"}
    ) == _branch_candidate_id(
        {"task_a": "left", "task_b": "right"}
    )
    with pytest.raises(ValueError, match="invalid task pair"):
        _branch_candidate_id({"task_a": "same", "task_b": "same"})


def _certified_root_node() -> dict:
    candidates = list(
        (_node(3)["fractional_branch_probe"] or {})["candidates"]
    )
    candidate_ids = [
        _branch_candidate_id(candidate) for candidate in candidates
    ]
    universe_hash = canonical_universe_hash(
        candidate_ids,
        universe_kind="p0_branch_shortlist",
    )
    cut_context = CutContext()
    cut_lineage = CutLineage()
    return {
        "node_id": "node_000",
        "parent_node_id": None,
        "depth": 0,
        "requested_node_status": "NODE_LP_CERTIFIED",
        "certificate_scope": "BPC_NODE_LP_CERTIFIED",
        "pricing_state": "CERTIFIED_NO_NEGATIVE",
        "node_lp_bound": 1.25,
        "node_lp_bound_official": True,
        "uses_true_dual_bpc_certificate": True,
        "manual_rc_audit_pass": True,
        "pricing_rc_audit_pass": True,
        "final_judge_certifying_proof_kind": True,
        "certificate_ledger": {"valid": True},
        "proof_debt_unreleased_count": 0,
        "live_cut_policy_hash": LiveSriPolicy.named("P0").policy_hash,
        "branch_context": {
            "schema_version": "lunar_ice_bpc.branch_context.v1",
            "pair_decision_count": 0,
            "pair_decisions": [],
        },
        "cut_context": cut_context.to_payload(),
        "active_cut_context_hash": cut_context.active_cut_context_hash,
        "cut_lineage": cut_lineage.to_payload(),
        "fractional_branch_probe": {"candidates": candidates},
        "legal_branch_shortlist_hash_before_sort": universe_hash,
        "legal_branch_shortlist_hash_after_sort": universe_hash,
        "guidance_branch_pair_drop_count": 0,
        "guidance_filter_count": 0,
    }


def test_certified_root_continuation_selects_rank_without_filtering() -> None:
    root, children = _development_certified_root_continuation(
        node=_certified_root_node(),
        requested_rank_index=2,
        active_live_policy=LiveSriPolicy.named("P0"),
    )
    assert root["node_status"] == "BRANCHED"
    assert root["development_branch_selected_rank_index"] == 2
    assert root["guidance_branch_pair_drop_count"] == 0
    assert root["child_node_ids"] == ["node_001", "node_002"]
    assert len(children) == 2
    assert {
        child.branch_sense for child in children
    } == {"same_journey", "different_journey"}
    assert all(
        child.inherited_lower_bound == 1.25 for child in children
    )


def test_certified_root_continuation_rejects_universe_drift() -> None:
    node = _certified_root_node()
    node["legal_branch_shortlist_hash_after_sort"] = "drift"
    with pytest.raises(ValueError, match="legal universe mismatch"):
        _development_certified_root_continuation(
            node=node,
            requested_rank_index=1,
            active_live_policy=LiveSriPolicy.named("P0"),
        )


def test_certified_deep_node_continuation_preserves_identity_and_ids() -> None:
    node = _certified_root_node()
    node.update(
        {
            "node_id": "node_007",
            "parent_node_id": "node_003",
            "depth": 2,
        }
    )
    branched, children = _development_certified_node_continuation(
        node=node,
        requested_rank_index=1,
        active_live_policy=LiveSriPolicy.named("P0"),
        first_child_index=11,
    )
    assert branched["node_id"] == "node_007"
    assert branched["child_node_ids"] == ["node_011", "node_012"]
    assert branched["development_branch_selected_rank_index"] == 1
    assert [child.node_id for child in children] == [
        "node_011",
        "node_012",
    ]
    assert all(child.parent_node_id == "node_007" for child in children)
    assert all(child.depth == 3 for child in children)


def _legacy_deep_snapshot_node() -> dict:
    node = _certified_root_node()
    node.update(
        {
            "node_status": "NODE_LP_CERTIFIED",
            "fractional_branch_probe_status": (
                "FRACTIONAL_BRANCH_PROBE_READY"
            ),
            "cut_count": 0,
            "all_priced_columns_satisfy_branch_context": True,
            "final_judge": {
                "all_priced_columns_satisfy_branch_context": True,
                "cut_context_active": False,
                "live_cut_certificate_supported": True,
                "pricing_cut_context_hash": node[
                    "active_cut_context_hash"
                ],
            },
        }
    )
    return node


def test_legacy_deep_snapshot_node_uses_bound_branch_and_cut_audits() -> None:
    assert (
        DEEP_MODULE._deep_target_node_exact_safe(
            _legacy_deep_snapshot_node()
        )
        is True
    )


def test_deep_snapshot_node_rejects_explicit_failed_audit() -> None:
    node = _legacy_deep_snapshot_node()
    node["branch_pricing_audit_pass"] = False
    node["cut_pricing_audit_pass"] = True

    assert DEEP_MODULE._deep_target_node_exact_safe(node) is False


def test_deep_snapshot_node_rejects_unbound_active_cut_proof() -> None:
    node = _legacy_deep_snapshot_node()
    node["cut_count"] = 1
    node["final_judge"]["cut_context_active"] = True
    node["final_judge"]["pricing_cut_context_hash"] = "wrong"

    assert DEEP_MODULE._deep_target_node_exact_safe(node) is False


def test_zero_arm_budget_is_validation_only() -> None:
    assert (
        DEEP_MODULE._may_launch_new_arm(
            new_arm_count=0,
            max_new_arms_per_process=0,
        )
        is False
    )
    assert (
        DEEP_MODULE._may_launch_new_arm(
            new_arm_count=0,
            max_new_arms_per_process=1,
        )
        is True
    )
    assert (
        DEEP_MODULE._may_launch_new_arm(
            new_arm_count=1,
            max_new_arms_per_process=1,
        )
        is False
    )
    with pytest.raises(ValueError, match="cannot be negative"):
        DEEP_MODULE._may_launch_new_arm(
            new_arm_count=0,
            max_new_arms_per_process=-1,
        )


def _e2e_arm(rank: int, *, exact: bool, wall: float) -> dict:
    return {
        "requested_rank_index": rank,
        "exact_safe": exact,
        "objective": 1.25,
        "matched_end_to_end_wall_sec": wall,
        "universe_safe": True,
        "target_top3_candidate_ids": ["p0", "p1", "p2"],
        "target_legal_branch_shortlist_hash_before_sort": "same",
        "target_legal_branch_shortlist_hash_after_sort": "same",
        "target_path_reached_once": True,
        "target_fallback_to_p0": False,
        "target_path_hash": "path",
    }


def test_exact_arm_before_control_censor_is_trusted_pairwise_only() -> None:
    report = DEEP_MODULE._build_gold_report(
        data=SimpleNamespace(
            instance_id="instance",
            instance_content_hash="hash",
            service_timing_policy_id="policy",
            scale=30,
        ),
        split_manifest_hash="split",
        parent_source_sha256="parent",
        control_tree_sha256="control",
        summaries={
            0: _e2e_arm(0, exact=False, wall=3604.0),
            2: _e2e_arm(2, exact=True, wall=2000.0),
        },
    )
    state = report["state_reports"][0]

    assert state["complete_matched_e2e_gold"] is False
    assert state["missing_rank_indices"] == [1]
    assert state["trusted_censored_pairwise_preferences"] == [
        {
            "winner_rank_index": 2,
            "loser_rank_index": 0,
            "evidence": "EXACT_BEFORE_OTHER_CENSOR_HORIZON",
            "winner_observed_wall_sec": 2000.0,
            "loser_observed_or_censor_wall_sec": 3604.0,
            "same_parent_snapshot": True,
            "unexplored_arm_used_as_negative": False,
        }
    ]


def test_censored_pairwise_rejects_universe_mismatch() -> None:
    control = _e2e_arm(0, exact=False, wall=3604.0)
    alternative = _e2e_arm(2, exact=True, wall=2000.0)
    alternative[
        "target_legal_branch_shortlist_hash_after_sort"
    ] = "drift"
    report = DEEP_MODULE._build_gold_report(
        data=SimpleNamespace(
            instance_id="instance",
            instance_content_hash="hash",
            service_timing_policy_id="policy",
            scale=30,
        ),
        split_manifest_hash="split",
        parent_source_sha256="parent",
        control_tree_sha256="control",
        summaries={0: control, 2: alternative},
    )

    assert report["state_reports"][0][
        "trusted_censored_pairwise_preferences"
    ] == []
