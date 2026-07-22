from __future__ import annotations

from itertools import combinations
from math import comb, floor
from unittest.mock import patch

import pytest

from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.exact.bpc.cuts.live_sri import (
    LIVE_SRI_SEPARATOR_VERSION,
    LiveSriPolicy,
    activate_separated_cuts,
    separate_live_sri,
)
from lunar_ice_bpc.exact.bpc.pricing.backends import (
    BackendPricingRequest,
    NativeRcsppInprocessBackend,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import _native_request_payload
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_instance_hash
from lunar_ice_bpc.exact.core.branching import BranchContext
from lunar_ice_bpc.exact.core.cuts import (
    CutContext,
    CutLineage,
    canonical_subset_row_cut,
    stable_payload_hash,
    true_dual_binding_hash,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals


def _fractional_pair_rows(task_ids: tuple[str, ...]) -> tuple[dict, ...]:
    return tuple(
        {"tasks": list(pair), "lambda_value": 0.5}
        for pair in combinations(task_ids, 2)
    )


def test_complete_sri3_sri5_enumeration_and_capacity_heap() -> None:
    tasks = tuple(f"t{index}" for index in range(7))
    rows = _fractional_pair_rows(tasks)
    all_rows = separate_live_sri(
        tasks,
        rows,
        subset_sizes=(3, 5),
        selection_capacity=10_000,
    )
    top_three = separate_live_sri(
        tasks,
        rows,
        subset_sizes=(3, 5),
        selection_capacity=3,
    )

    expected = comb(7, 3) + comb(7, 5)
    assert all_rows.full_enumeration_completed
    assert all_rows.enumerated_candidate_count == expected
    assert all_rows.expected_candidate_count == expected
    assert tuple(row.cut.cut_id for row in top_three.selected) == tuple(
        row.cut.cut_id for row in all_rows.selected[:3]
    )
    assert top_three.unselected_violated_count == (
        top_three.violated_candidate_count - 3
    )
    assert top_three.to_payload()["separator_policy_version"] == LIVE_SRI_SEPARATOR_VERSION


def test_sri_integer_validity_for_every_partition_of_five_tasks() -> None:
    """Exhaust the set-partition shapes behind the divisor-two validity proof."""

    tasks = tuple(f"t{index}" for index in range(5))
    sri_sets = tuple(combinations(tasks, 3)) + tuple(combinations(tasks, 5))
    # Every assignment maps each task to exactly one selected journey.  This
    # exhausts all 5^5 labelled partitions (duplicates collapse harmlessly).
    for assignment_number in range(5**5):
        digits = []
        value = assignment_number
        for _ in tasks:
            digits.append(value % 5)
            value //= 5
        selected_sets = [
            {task for task, group in zip(tasks, digits) if group == group_id}
            for group_id in range(5)
        ]
        selected_sets = [task_set for task_set in selected_sets if task_set]
        for subset in sri_sets:
            lhs = sum(floor(len(task_set.intersection(subset)) / 2) for task_set in selected_sets)
            rhs = floor(len(subset) / 2)
            assert lhs <= rhs


def test_canonical_ids_hashes_and_lineage_are_deterministic() -> None:
    cut_a = canonical_subset_row_cut(("t3", "t1", "t2"))
    cut_b = canonical_subset_row_cut(("t2", "t3", "t1"))
    assert cut_a == cut_b
    assert cut_a.cut_id == "sri:d2:n3:t1,t2,t3"

    context = CutContext(cuts=(cut_a,))
    assert context.active_cut_context_hash == CutContext(cuts=(cut_b,)).active_cut_context_hash
    assert stable_payload_hash(BranchContext().to_payload()) != context.active_cut_context_hash
    assert true_dual_binding_hash({"t1": 1.0}) != true_dual_binding_hash({"t1": 1.1})


def test_global_inheritance_and_sibling_local_isolation() -> None:
    tasks = tuple(f"t{index}" for index in range(7))
    rows = _fractional_pair_rows(tasks)
    policy = LiveSriPolicy.named("P2")
    root_result = separate_live_sri(
        tasks,
        rows,
        subset_sizes=policy.root_subset_sizes,
        selection_capacity=4,
    )
    root_context, root_lineage, _ = activate_separated_cuts(
        CutContext(),
        CutLineage(policy_version=policy.version),
        root_result,
        policy=policy,
        node_id="node_000",
        depth=0,
    )
    child_result = separate_live_sri(
        tasks,
        rows,
        subset_sizes=policy.node_subset_sizes,
        selection_capacity=4,
        existing_cut_context=root_context,
    )
    child_one_context, child_one_lineage, _ = activate_separated_cuts(
        root_context,
        root_lineage,
        child_result,
        policy=policy,
        node_id="node_001",
        depth=1,
        ancestor_path=("node_000",),
    )
    child_two_context = root_context
    child_two_lineage = root_lineage

    assert len(root_context.cuts) == 4
    assert len(child_one_context.cuts) == 8
    assert len(child_two_context.cuts) == 4
    assert child_one_lineage.validate_context(child_one_context) == tuple()
    assert child_two_lineage.validate_context(child_two_context) == tuple()
    assert child_one_context.active_cut_context_hash != child_two_context.active_cut_context_hash


def test_native_cut_state_sequence_and_0_1_8_16_17_boundaries() -> None:
    pytest.importorskip("lunar_spprc_native")
    data = load_lunar_ice_data(generate_instance(10, seed=7202201, index=1))
    all_cuts = tuple(
        canonical_subset_row_cut(subset)
        for subset in combinations(data.task_ids, 3)
    )
    backend = NativeRcsppInprocessBackend()

    for count in (0, 1, 8, 16):
        context = CutContext(cuts=all_cuts[:count])
        duals = JourneyDuals(
            cover={},
            cuts={cut.cut_id: -0.01 for cut in context.cuts},
        )
        result = backend.solve(
            BackendPricingRequest(
                data=data,
                true_duals=duals,
                cut_context=context,
                completion_bound_enabled=True,
                instance_hash=spprc_instance_hash(data),
                dual_binding_hash=true_dual_binding_hash(
                    duals.cover,
                    fleet_limit=duals.fleet_limit,
                    cuts=duals.cuts,
                ),
                cut_context_hash=context.active_cut_context_hash,
            )
        )
        assert result.engine_status == "COMPLETE"
        assert result.search_exhaustive
        assert result.frontier_empty
        assert not result.labels_dropped
        assert result.telemetry["active_cut_count"] == count
        assert result.telemetry["cut_state_effective"] is (count > 0)
        assert result.telemetry["rc_mismatch_count"] == 0
        if count:
            assert result.telemetry["completion_bound_forced_off"]

    overflow = backend.solve(
        BackendPricingRequest(
            data=data,
            true_duals=JourneyDuals(cover={}),
            cut_context=CutContext(cuts=all_cuts[:17]),
        )
    )
    assert overflow.engine_status == "UNSUPPORTED_FEATURE"
    assert "active_cut_count_exceeds_native_capability" in overflow.certificate_blockers

    # Reuse the in-process graph cache through the requested transition order;
    # the final no-cut request must not retain B's overlap state.
    contexts = (
        CutContext(),
        CutContext(cuts=(all_cuts[0],)),
        CutContext(cuts=(all_cuts[0], all_cuts[1])),
        CutContext(cuts=(all_cuts[1],)),
        CutContext(),
    )
    observed = []
    for context in contexts:
        result = backend.solve(
            BackendPricingRequest(
                data=data,
                true_duals=JourneyDuals(cover={}),
                cut_context=context,
                cut_context_hash=context.active_cut_context_hash,
            )
        )
        observed.append((result.engine_status, result.telemetry["active_cut_count"]))
    assert observed == [
        ("COMPLETE", 0),
        ("COMPLETE", 1),
        ("COMPLETE", 2),
        ("COMPLETE", 1),
        ("COMPLETE", 0),
    ]


def test_stale_native_certificate_binding_fails_closed_but_keeps_audited_columns() -> None:
    native = pytest.importorskip("lunar_spprc_native")
    data = load_lunar_ice_data(generate_instance(5, seed=7202203, index=1))
    cut = canonical_subset_row_cut(data.task_ids[:3])
    context = CutContext(cuts=(cut,))
    duals = JourneyDuals(
        cover={task_id: 10.0 for task_id in data.task_ids},
        cuts={cut.cut_id: -0.1},
    )
    request = BackendPricingRequest(
        data=data,
        true_duals=duals,
        cut_context=context,
        dual_binding_hash=true_dual_binding_hash(
            duals.cover, cuts=duals.cuts
        ),
        cut_context_hash=context.active_cut_context_hash,
        cut_lineage_hash="lineage-v1",
        live_cut_policy_hash="policy-v1",
        rmp_iteration_id="rmp-1",
        separator_policy_version=LIVE_SRI_SEPARATOR_VERSION,
    )
    raw = dict(native.solve(_native_request_payload(request)))
    raw["request_bindings"] = dict(raw["request_bindings"])
    raw["request_bindings"]["active_cut_context_hash"] = "stale-cut-context"
    with patch("lunar_spprc_native.solve", return_value=raw):
        result = NativeRcsppInprocessBackend().solve(request)

    assert "native_result_binding_mismatch:active_cut_context_hash" in result.certificate_blockers
    assert not result.can_enter_certificate_audit
    assert result.columns
    assert result.telemetry["request_bindings_match"] is False
    assert result.telemetry["rc_mismatch_count"] == 0
