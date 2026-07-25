from __future__ import annotations

from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
    _validate_native_best_rc_events,
)


def test_native_best_rc_event_trace_is_monotone_and_training_usable() -> None:
    audit = _validate_native_best_rc_events(
        [
            {
                "elapsed_seconds": 0.01,
                "extended_labels": 10,
                "solution_count": 1,
                "discovered_reduced_cost": -0.2,
                "best_reduced_cost": -0.2,
            },
            {
                "elapsed_seconds": 0.02,
                "extended_labels": 25,
                "solution_count": 2,
                "discovered_reduced_cost": -0.5,
                "best_reduced_cost": -0.5,
            },
        ],
        exact_proof_mode=False,
        wall_time_seconds=0.03,
        raw_route_reduced_costs=(-0.2, -0.5),
        trace_truncated=False,
    )
    assert audit["best_reduced_cost_event_trace_valid"]
    assert audit["best_reduced_cost_event_trace_usable_for_training"]
    assert audit["best_reduced_cost_events_audited"][-1][
        "best_true_rc"
    ] == -0.5


def test_native_best_rc_event_trace_fails_closed_as_diagnostic_only() -> None:
    audit = _validate_native_best_rc_events(
        [
            {
                "elapsed_seconds": 0.02,
                "extended_labels": 10,
                "solution_count": 1,
                "discovered_reduced_cost": -0.5,
                "best_reduced_cost": -0.5,
            },
            {
                "elapsed_seconds": 0.01,
                "extended_labels": 20,
                "solution_count": 2,
                "discovered_reduced_cost": -0.6,
                "best_reduced_cost": -0.6,
            },
        ],
        exact_proof_mode=False,
        wall_time_seconds=0.03,
        raw_route_reduced_costs=(-0.5, -0.6),
        trace_truncated=False,
    )
    assert not audit["best_reduced_cost_event_trace_valid"]
    assert not audit["best_reduced_cost_event_trace_usable_for_training"]
    assert audit["best_reduced_cost_event_trace_error"] == (
        "invalid_elapsed:1"
    )
