from __future__ import annotations

import pickle
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from lunar_ice_bpc.exact.bpc.master.reduced_cost import ReducedCostContext
from lunar_ice_bpc.exact.bpc.pricing.final_judge import (
    _run_labeling_pricer_final_judge,
    _validate_harvest_discovery_duals,
)
from lunar_ice_bpc.exact.bpc.pricing.dual_stabilization import (
    DevelopmentOracleDualCenter,
    adaptive_ascg_penalty_from_pricing,
    adaptive_true_dual_weight,
    build_worker_duals_with_development_oracle_center,
)
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (
    ADAPTIVE_TAIL_HARVEST_MAX_ENV,
    ADAPTIVE_TAIL_HARVEST_TRIGGER_SEC_ENV,
    _adaptive_tail_harvest_limit,
    _development_oracle_l1_penalty,
)
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.exact.master.journey_rmp import (
    solve_stabilized_journey_dual_sidecar,
)
from lunar_ice_bpc.exact.core.branching import BranchContext
from lunar_ice_bpc.exact.core.cuts import CutContext


def _center(**overrides) -> DevelopmentOracleDualCenter:
    payload = {
        "instance_content_hash": "instance-hash",
        "task_dual_items": (("t1", 4.0), ("t2", 8.0)),
        "source_rmp_iteration_id": "root-final",
        "source_artifact_sha256": "a" * 64,
        "source_partition": "development",
    }
    payload.update(overrides)
    return DevelopmentOracleDualCenter(**payload)


def test_development_oracle_center_is_immutable_pickle_safe_and_bound() -> None:
    center = _center()
    restored = pickle.loads(pickle.dumps(center))

    assert restored == center
    assert restored.oracle_center_id == center.oracle_center_id
    restored.validate_for(
        instance_content_hash="instance-hash",
        task_ids=["t1", "t2"],
    )
    mutable_copy = restored.task_duals
    mutable_copy["t1"] = 100.0
    assert restored.task_duals["t1"] == 4.0


def test_development_oracle_center_rejects_partition_hash_tasks_and_nonfinite() -> None:
    with pytest.raises(ValueError, match="development partition only"):
        _center(source_partition="calibration").validate_for(
            instance_content_hash="instance-hash",
            task_ids=["t1", "t2"],
        )
    with pytest.raises(ValueError, match="instance hash mismatch"):
        _center().validate_for(
            instance_content_hash="other-hash",
            task_ids=["t1", "t2"],
        )
    with pytest.raises(ValueError, match="task universe mismatch"):
        _center().validate_for(
            instance_content_hash="instance-hash",
            task_ids=["t1"],
        )
    with pytest.raises(ValueError, match="NaN/Inf"):
        _center(task_dual_items=(("t1", float("nan")), ("t2", 8.0)))


def test_oracle_center_id_canonicalizes_signed_zero() -> None:
    positive = _center(task_dual_items=(("t1", 0.0), ("t2", 8.0)))
    negative = _center(task_dual_items=(("t1", -0.0), ("t2", 8.0)))
    assert positive.oracle_center_id == negative.oracle_center_id


def test_adaptive_oracle_weight_releases_monotonically_to_true_dual() -> None:
    weights = [
        adaptive_true_dual_weight(
            round_index=round_index,
            initial_true_dual_weight=0.2,
            release_round=5,
        )
        for round_index in range(1, 8)
    ]
    assert weights == sorted(weights)
    assert weights[0] == 0.2
    assert weights[4:] == [1.0, 1.0, 1.0]


def test_adaptive_ascg_penalty_uses_pricing_feedback_and_fails_closed() -> None:
    penalty, payload = adaptive_ascg_penalty_from_pricing(-0.25)
    assert penalty == pytest.approx(0.2)
    assert payload["minimum_reduced_cost"] == -0.25
    assert payload["release_reason"] == ""
    assert payload["can_certify_no_negative"] is False

    released, released_payload = adaptive_ascg_penalty_from_pricing(0.0)
    assert released == 0.0
    assert (
        released_payload["release_reason"]
        == "stabilized_pricing_nonnegative"
    )

    missing, missing_payload = adaptive_ascg_penalty_from_pricing(None)
    assert missing == 0.0
    assert (
        missing_payload["release_reason"]
        == "pricing_value_unavailable_fail_closed"
    )

    tiny, tiny_payload = adaptive_ascg_penalty_from_pricing(-0.001)
    assert tiny == 0.0
    assert (
        tiny_payload["release_reason"]
        == "penalty_below_release_threshold"
    )


def test_oracle_worker_dual_never_changes_non_task_duals_or_certificate_source() -> None:
    current = JourneyDuals(
        cover={"t1": 0.0, "t2": 10.0},
        fleet_limit=-3.0,
        cuts={"cut": -2.0},
    )
    worker, payload = build_worker_duals_with_development_oracle_center(
        current,
        _center(),
        round_index=1,
        initial_true_dual_weight=0.25,
        release_round=3,
    )
    assert worker.cover == {"t1": 3.0, "t2": 8.5}
    assert worker.fleet_limit == current.fleet_limit
    assert worker.cuts == current.cuts
    assert payload["worker_dual_only"] is True
    assert payload["official_dual_source"] == "current_true_rmp_dual"
    assert payload["can_certify_no_negative"] is False
    assert payload["oracle_deployable"] is False

    released, released_payload = (
        build_worker_duals_with_development_oracle_center(
            current,
            _center(),
            round_index=3,
            initial_true_dual_weight=0.25,
            release_round=3,
        )
    )
    assert released == current
    assert released_payload["oracle_influence"] == 0.0
    assert released_payload["oracle_release_complete"] is True


def test_harvest_discovery_dual_rejects_non_task_changes() -> None:
    official = JourneyDuals(
        cover={"t1": 1.0},
        fleet_limit=-2.0,
        cuts={"c1": -1.0},
    )
    with pytest.raises(ValueError, match="task-cover duals only"):
        _validate_harvest_discovery_duals(
            JourneyDuals(
                cover={"t1": 2.0},
                fleet_limit=-3.0,
                cuts={"c1": -1.0},
            ),
            official_duals=official,
            task_ids=("t1",),
        )
    with pytest.raises(ValueError, match="may not change cut duals"):
        _validate_harvest_discovery_duals(
            JourneyDuals(
                cover={"t1": 2.0},
                fleet_limit=-2.0,
                cuts={"c1": -2.0},
            ),
            official_duals=official,
            task_ids=("t1",),
        )


def test_l1_stabilized_rmp_sidecar_hits_feasible_center_but_cannot_certify() -> None:
    columns = (
        SimpleNamespace(task_set=frozenset({"t1"}), objective=1.0),
        SimpleNamespace(task_set=frozenset({"t2"}), objective=1.0),
        SimpleNamespace(
            task_set=frozenset({"t1", "t2"}), objective=1.5
        ),
    )
    result = solve_stabilized_journey_dual_sidecar(
        ("t1", "t2"),
        columns,
        fleet_size=2,
        task_dual_center={"t1": 0.75, "t2": 0.75},
        penalty=1.0,
    )

    assert result.status == "STABILIZED_RMP_OPTIMAL"
    assert result.duals.cover == {"t1": 0.75, "t2": 0.75}
    assert result.center_l1_distance == 0.0
    assert result.worker_dual_only is True
    assert result.can_certify_no_negative is False
    assert result.official_bound_safe is False


def test_l1_stabilized_rmp_sidecar_rejects_bad_center_or_penalty() -> None:
    column = SimpleNamespace(task_set=frozenset({"t1"}), objective=1.0)
    with pytest.raises(ValueError, match="task universe mismatch"):
        solve_stabilized_journey_dual_sidecar(
            ("t1",),
            (column,),
            fleet_size=1,
            task_dual_center={"other": 1.0},
            penalty=1.0,
        )
    with pytest.raises(ValueError, match="finite and nonnegative"):
        solve_stabilized_journey_dual_sidecar(
            ("t1",),
            (column,),
            fleet_size=1,
            task_dual_center={"t1": 1.0},
            penalty=-1.0,
        )


def test_l1_sidecar_penalty_has_delayed_bounded_activation_window() -> None:
    penalties = [
        _development_oracle_l1_penalty(
            round_index=round_index,
            initial_penalty=1.0,
            activation_round=4,
            release_round=8,
        )
        for round_index in range(1, 10)
    ]
    assert penalties[:3] == [0.0, 0.0, 0.0]
    assert penalties[3:8] == [1.0, 0.75, 0.5, 0.25, 0.0]
    assert penalties[8] == 0.0


def test_adaptive_tail_harvest_is_off_by_default_and_post_event_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert _adaptive_tail_harvest_limit(
        base_limit=64,
        previous_final_judge_wall_sec=100.0,
    ) == 64
    monkeypatch.setenv(ADAPTIVE_TAIL_HARVEST_MAX_ENV, "256")
    monkeypatch.setenv(
        ADAPTIVE_TAIL_HARVEST_TRIGGER_SEC_ENV, "1.0"
    )
    assert _adaptive_tail_harvest_limit(
        base_limit=64,
        previous_final_judge_wall_sec=0.9,
    ) == 64
    assert _adaptive_tail_harvest_limit(
        base_limit=64,
        previous_final_judge_wall_sec=1.0,
    ) == 256


def test_discovery_harvest_certificate_is_ignored_and_true_dual_proof_runs() -> None:
    official = JourneyDuals(cover={"t1": 1.0}, fleet_limit=0.0)
    discovery = JourneyDuals(cover={"t1": 2.0}, fleet_limit=0.0)
    context = ReducedCostContext(
        task_duals=official.cover,
        fleet_dual=official.fleet_limit,
        dual_fingerprint="true",
        rmp_iteration_id="root-1",
    )
    seen_duals: list[JourneyDuals] = []

    def fake_pricer(_data, duals, **_kwargs):
        seen_duals.append(duals)
        return (
            {
                "status": "EXACT_NO_NEGATIVE",
                "pricing_state": "CERTIFIED_NO_NEGATIVE",
                "pricing_proof_kind": "EXHAUSTIVE_NO_NEGATIVE",
                "can_certify_no_negative": True,
                "true_best_reduced_cost": None,
                "true_audited_column_count": 0,
            },
            tuple(),
        )

    with patch(
        "lunar_ice_bpc.exact.bpc.pricing.final_judge."
        "run_bpc_labeling_pricer",
        side_effect=fake_pricer,
    ):
        result = _run_labeling_pricer_final_judge(
            SimpleNamespace(task_ids=("t1",)),
            official,
            context=context,
            branch_context=BranchContext(),
            cut_context=CutContext(),
            max_direct_tasks=1,
            negative_eps=1.0e-6,
            cache=None,
            wall_time_limit_sec=1.0,
            harvest_discovery_duals=discovery,
            harvest_discovery_metadata={
                "worker_dual_source": "test_discovery"
            },
        )

    assert seen_duals == [discovery, official]
    assert result.pricing_payload[
        "labeling_final_judge_proof_pass_attempted"
    ] is True
    assert result.pricing_payload["harvest_discovery_dual_used"] is True
    assert result.pricing_payload[
        "harvest_discovery_dual_can_certify"
    ] is False
    assert result.pricing_payload[
        "proof_pass_official_dual_source"
    ] == "current_true_rmp_dual"
