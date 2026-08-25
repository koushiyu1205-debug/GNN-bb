from __future__ import annotations

from lunar_ice_bpc.guidance.qg2_combined_policy import (
    ArmOutcome,
    ArmScore,
    CombinedContext,
    choose_combined_action,
    choose_secondary_thresholds,
    choose_secondary_thresholds_for_positive_net_evaluation,
    evaluate_combined_policy,
)


def _context(
    index: int,
    *,
    primary_probability: float = 0.1,
    primary_gain: float = 0.01,
    qd1_probability: float = 0.95,
    qd1_gain: float = 0.50,
    qb1_probability: float = 0.10,
    qb1_gain: float = 0.01,
    qg2_ratio: float = 0.8,
    qd1_ratio: float = 0.5,
    qb1_ratio: float = 1.5,
    ood: bool = False,
) -> CombinedContext:
    return CombinedContext(
        state_hash=f"state-{index}",
        instance_hash=f"instance-{index}",
        scale=30 if index % 2 == 0 else 50,
        primary_score=ArmScore(primary_probability, primary_gain),
        secondary_scores={
            "QD1": ArmScore(qd1_probability, qd1_gain),
            "QB1": ArmScore(qb1_probability, qb1_gain),
        },
        outcomes={
            "QG2": ArmOutcome(qg2_ratio, True, True),
            "QD1": ArmOutcome(qd1_ratio, True, True),
            "QB1": ArmOutcome(qb1_ratio, True, True),
        },
        ood=ood,
    )


def _thresholds() -> dict[str, float]:
    return {
        "primary_probability_threshold": 0.8,
        "primary_expected_gain_threshold": 0.2,
        "secondary_probability_threshold": 0.8,
        "secondary_expected_gain_threshold": 0.2,
    }


def test_primary_qg2_has_first_action_authority() -> None:
    context = _context(
        0,
        primary_probability=0.90,
        primary_gain=0.30,
        qd1_probability=0.99,
        qd1_gain=0.90,
    )
    assert choose_combined_action(context, **_thresholds()) == "QG2"


def test_secondary_arm_exists_only_after_primary_declines() -> None:
    assert choose_combined_action(_context(0), **_thresholds()) == "QD1"
    rejected = _context(
        1,
        qd1_probability=0.2,
        qd1_gain=0.01,
        qb1_probability=0.2,
        qb1_gain=0.01,
    )
    assert choose_combined_action(rejected, **_thresholds()) == "Q0"
    assert choose_combined_action(
        _context(2, ood=True), **_thresholds()
    ) == "Q0"


def test_censored_or_unsafe_selected_action_is_harmful() -> None:
    base = _context(0)
    censored = CombinedContext(
        **{
            **base.__dict__,
            "outcomes": {
                **base.outcomes,
                "QD1": ArmOutcome(0.5, False, True, right_censored=True),
            },
        }
    )
    unsafe = CombinedContext(
        **{
            **base.__dict__,
            "state_hash": "unsafe",
            "outcomes": {
                **base.outcomes,
                "QD1": ArmOutcome(0.5, True, False),
            },
        }
    )

    report = evaluate_combined_policy([censored, unsafe], _thresholds())

    assert report["activation_count"] == 2
    assert report["harmful_count"] == 2
    assert report["right_censored_count"] == 1
    assert report["unsafe_count"] == 1
    assert not report["passes_risk_precision_gate"]


def test_sixty_clean_secondary_actions_can_pass_strict_wilson_gate() -> None:
    contexts = [_context(index) for index in range(60)]

    selected = choose_secondary_thresholds(
        contexts,
        primary_probability_threshold=0.8,
        primary_expected_gain_threshold=0.2,
    )

    assert selected["secondary_gate_passed"]
    assert selected["fallback_action"] == "Q0"
    metrics = selected["calibration_metrics"]
    assert metrics["arm_counts"]["QG2"] == 0
    assert metrics["arm_counts"]["QD1"] == 60
    assert metrics["harmful_rate_95_upper"] <= 0.05
    assert metrics["beneficial_precision_95_lower"] >= 0.80


def test_small_clean_sample_cannot_claim_strict_risk_authority() -> None:
    selected = choose_secondary_thresholds(
        [_context(index) for index in range(10)],
        primary_probability_threshold=0.8,
        primary_expected_gain_threshold=0.2,
    )

    assert not selected["secondary_gate_passed"]
    assert selected["secondary_probability_threshold"] > 1.0
    assert selected["calibration_metrics"]["arm_counts"]["QD1"] == 0
    assert selected["calibration_metrics"]["fallback_action"] == "Q0"


def test_small_positive_net_sample_can_enter_reversible_e2e_trial() -> None:
    selected = choose_secondary_thresholds_for_positive_net_evaluation(
        [_context(index) for index in range(10)],
        primary_probability_threshold=0.8,
        primary_expected_gain_threshold=0.2,
    )

    assert selected["evaluation_gate_passed"]
    assert selected["secondary_enabled"]
    assert selected["calibration_metrics"]["net_geomean_ratio"] < 1.0
    assert not selected["calibration_metrics"]["passes_risk_precision_gate"]
    assert selected["fallback_action"] == "Q0"


def test_relaxed_gate_still_vetoes_censored_or_unsafe_actions() -> None:
    contexts = []
    for index in range(10):
        base = _context(index)
        contexts.append(
            CombinedContext(
                **{
                    **base.__dict__,
                    "outcomes": {
                        **base.outcomes,
                        "QD1": ArmOutcome(
                            0.5,
                            False,
                            True,
                            right_censored=True,
                        ),
                    },
                }
            )
        )

    selected = choose_secondary_thresholds_for_positive_net_evaluation(
        contexts,
        primary_probability_threshold=0.8,
        primary_expected_gain_threshold=0.2,
    )

    assert not selected["evaluation_gate_passed"]
    assert not selected["secondary_enabled"]
    assert selected["fallback_action"] == "Q0"


def test_relaxed_gate_can_retain_positive_qg2_and_disable_secondary() -> None:
    contexts = [
        _context(
            index,
            primary_probability=0.95,
            primary_gain=0.5,
            qg2_ratio=0.9,
            qd1_ratio=1.2,
            qb1_ratio=1.3,
        )
        for index in range(10)
    ]

    selected = choose_secondary_thresholds_for_positive_net_evaluation(
        contexts,
        primary_probability_threshold=0.8,
        primary_expected_gain_threshold=0.2,
    )

    assert selected["evaluation_gate_passed"]
    assert not selected["secondary_enabled"]
    assert selected["calibration_metrics"]["arm_counts"]["QG2"] == 10
    assert selected["calibration_metrics"]["arm_counts"]["QD1"] == 0
