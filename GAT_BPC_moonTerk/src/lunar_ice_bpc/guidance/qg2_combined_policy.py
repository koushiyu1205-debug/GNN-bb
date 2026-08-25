"""Numerical policy logic for QG2-first multi-arm calibration.

The action hierarchy is intentionally asymmetric:

``QG2 accepted -> QG2``
``QG2 declined and selector accepted -> QD1 or QB1``
``all learned/deterministic arms declined -> literal Q0``

Keeping the hierarchy fixed avoids comparing QG2's predicted saved seconds
with the context selector's predicted fractional gain.  This module is pure
decision/measurement logic; it has no solver or certificate authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import statistics
from typing import Any, Iterable, Mapping, Sequence


QG2_COMBINED_ACTION_HIERARCHY_V1 = "qg2_then_qd1_qb1_then_literal_q0.v1"
QG2_POSITIVE_NET_EVALUATION_GATE_V1 = "positive_net_exact_safe.v1"
QG2_PRIMARY_ARM = "QG2"
QG2_SECONDARY_ARMS = ("QD1", "QB1")
QG2_NOOP_ARM = "Q0"
ONE_SIDED_95_Z = 1.6448536269514722


@dataclass(frozen=True)
class ArmScore:
    benefit_probability: float
    expected_gain: float
    eligible: bool = True


@dataclass(frozen=True)
class ArmOutcome:
    ratio: float
    matched_milestone: bool
    exact_safe: bool
    right_censored: bool = False

    @property
    def beneficial(self) -> bool:
        return bool(
            self.matched_milestone
            and self.exact_safe
            and not self.right_censored
            and self.ratio < 1.0
        )

    @property
    def harmful(self) -> bool:
        return bool(
            self.right_censored
            or not self.matched_milestone
            or not self.exact_safe
            or self.ratio > 1.0
        )


@dataclass(frozen=True)
class CombinedContext:
    state_hash: str
    instance_hash: str
    scale: int
    primary_score: ArmScore
    secondary_scores: Mapping[str, ArmScore]
    outcomes: Mapping[str, ArmOutcome]
    ood: bool = False


def choose_combined_action(
    context: CombinedContext,
    *,
    primary_probability_threshold: float,
    primary_expected_gain_threshold: float,
    secondary_probability_threshold: float,
    secondary_expected_gain_threshold: float,
) -> str:
    """Apply the frozen hierarchy; every veto and empty set returns Q0."""

    if context.ood:
        return QG2_NOOP_ARM
    primary = context.primary_score
    if (
        primary.eligible
        and _finite(primary.benefit_probability)
        and _finite(primary.expected_gain)
        and primary.benefit_probability >= float(primary_probability_threshold)
        and primary.expected_gain >= float(primary_expected_gain_threshold)
    ):
        return QG2_PRIMARY_ARM
    eligible = [
        (score.expected_gain, arm)
        for arm, score in context.secondary_scores.items()
        if arm in QG2_SECONDARY_ARMS
        and score.eligible
        and _finite(score.benefit_probability)
        and _finite(score.expected_gain)
        and score.benefit_probability
        >= float(secondary_probability_threshold)
        and score.expected_gain >= float(secondary_expected_gain_threshold)
    ]
    if not eligible:
        return QG2_NOOP_ARM
    return max(eligible, key=lambda row: (row[0], row[1]))[1]


def evaluate_combined_policy(
    contexts: Sequence[CombinedContext],
    thresholds: Mapping[str, float],
) -> dict[str, Any]:
    """Evaluate selected-arm risk and net ratio, counting censoring as harm."""

    action_rows = []
    net_ratios = []
    per_scale: dict[int, list[tuple[str, ArmOutcome]]] = {30: [], 50: []}
    for context in contexts:
        action = choose_combined_action(
            context,
            primary_probability_threshold=float(
                thresholds.get("primary_probability_threshold", math.inf)
            ),
            primary_expected_gain_threshold=float(
                thresholds.get("primary_expected_gain_threshold", math.inf)
            ),
            secondary_probability_threshold=float(
                thresholds.get("secondary_probability_threshold", math.inf)
            ),
            secondary_expected_gain_threshold=float(
                thresholds.get("secondary_expected_gain_threshold", math.inf)
            ),
        )
        if action == QG2_NOOP_ARM:
            outcome = ArmOutcome(
                ratio=1.0,
                matched_milestone=True,
                exact_safe=True,
                right_censored=False,
            )
        else:
            outcome = context.outcomes[action]
            action_rows.append((context, action, outcome))
        net_ratios.append(float(outcome.ratio))
        per_scale.setdefault(int(context.scale), []).append((action, outcome))
    harmful = sum(outcome.harmful for _context, _arm, outcome in action_rows)
    beneficial = sum(
        outcome.beneficial for _context, _arm, outcome in action_rows
    )
    activated = len(action_rows)
    harmful_upper = wilson_bound(harmful, activated, upper=True)
    precision_lower = wilson_bound(beneficial, activated, upper=False)
    return {
        "context_count": len(contexts),
        "instance_count": len({row.instance_hash for row in contexts}),
        "activation_count": activated,
        "no_op_count": len(contexts) - activated,
        "arm_counts": {
            arm: sum(action == arm for _row, action, _outcome in action_rows)
            for arm in (QG2_PRIMARY_ARM, *QG2_SECONDARY_ARMS)
        },
        "beneficial_count": beneficial,
        "harmful_count": harmful,
        "right_censored_count": sum(
            outcome.right_censored
            for _context, _arm, outcome in action_rows
        ),
        "unsafe_count": sum(
            not outcome.exact_safe
            for _context, _arm, outcome in action_rows
        ),
        "harmful_rate_95_upper": harmful_upper,
        "beneficial_precision_95_lower": precision_lower,
        "net_geomean_ratio": _geomean(net_ratios),
        "passes_risk_precision_gate": bool(
            activated
            and harmful_upper <= 0.05
            and precision_lower >= 0.80
            and all(outcome.exact_safe for _row, _arm, outcome in action_rows)
            and all(
                outcome.matched_milestone and not outcome.right_censored
                for _row, _arm, outcome in action_rows
            )
        ),
        "fallback_action": QG2_NOOP_ARM,
        "hierarchy": QG2_COMBINED_ACTION_HIERARCHY_V1,
        "per_scale": {
            str(scale): _scale_metrics(rows)
            for scale, rows in sorted(per_scale.items())
        },
        "selected_actions": [
            {
                "state_hash": context.state_hash,
                "instance_hash": context.instance_hash,
                "scale": int(context.scale),
                "arm": arm,
                "ratio": float(outcome.ratio),
                "beneficial": outcome.beneficial,
                "harmful": outcome.harmful,
                "right_censored": bool(outcome.right_censored),
                "exact_safe": bool(outcome.exact_safe),
            }
            for context, arm, outcome in action_rows
        ],
    }


def choose_secondary_thresholds(
    contexts: Sequence[CombinedContext],
    *,
    primary_probability_threshold: float,
    primary_expected_gain_threshold: float,
) -> dict[str, Any]:
    """Calibrate secondary thresholds after freezing the primary QG2 gate."""

    probabilities = sorted(
        {
            float(score.benefit_probability)
            for context in contexts
            for score in context.secondary_scores.values()
            if score.eligible and _finite(score.benefit_probability)
        }
    )
    gains = sorted(
        {
            float(score.expected_gain)
            for context in contexts
            for score in context.secondary_scores.values()
            if score.eligible and _finite(score.expected_gain)
        }
    )
    candidates = []
    for probability in probabilities:
        for gain in gains:
            thresholds = {
                "primary_probability_threshold": float(
                    primary_probability_threshold
                ),
                "primary_expected_gain_threshold": float(
                    primary_expected_gain_threshold
                ),
                "secondary_probability_threshold": probability,
                "secondary_expected_gain_threshold": gain,
            }
            metrics = evaluate_combined_policy(contexts, thresholds)
            if not metrics["passes_risk_precision_gate"]:
                continue
            candidates.append(
                (
                    float(metrics["net_geomean_ratio"]),
                    -int(metrics["activation_count"]),
                    -probability,
                    -gain,
                    thresholds,
                    metrics,
                )
            )
    if not candidates:
        thresholds = {
            "primary_probability_threshold": float(
                primary_probability_threshold
            ),
            "primary_expected_gain_threshold": float(
                primary_expected_gain_threshold
            ),
            "secondary_probability_threshold": 2.0,
            "secondary_expected_gain_threshold": 1.0e30,
        }
        return {
            **thresholds,
            "secondary_gate_passed": False,
            "fallback_action": QG2_NOOP_ARM,
            "reason": "no_secondary_threshold_satisfies_strict_combined_risk_gate",
            "calibration_metrics": evaluate_combined_policy(
                contexts, thresholds
            ),
        }
    selected = min(candidates)
    return {
        **selected[4],
        "secondary_gate_passed": True,
        "fallback_action": QG2_NOOP_ARM,
        "reason": "best_strict_combined_calibration_geomean",
        "calibration_metrics": selected[5],
    }


def choose_secondary_thresholds_for_positive_net_evaluation(
    contexts: Sequence[CombinedContext],
    *,
    primary_probability_threshold: float,
    primary_expected_gain_threshold: float,
) -> dict[str, Any]:
    """Choose a development-E2E policy without a minimum effect-size gate.

    The statistical 5% harmful-rate bound and 5% speedup are retained as
    diagnostics, but no longer block a reversible formal-instance trial.
    Exact-unsafe and right-censored selected actions remain hard vetoes.  A
    secondary-disabled candidate is always evaluated so QD1/QB1 cannot be
    forced into an otherwise useful QG2 policy.
    """

    probabilities = sorted(
        {
            float(score.benefit_probability)
            for context in contexts
            for score in context.secondary_scores.values()
            if score.eligible and _finite(score.benefit_probability)
        }
    )
    gains = sorted(
        {
            float(score.expected_gain)
            for context in contexts
            for score in context.secondary_scores.values()
            if score.eligible and _finite(score.expected_gain)
        }
    )
    pairs = [(2.0, 1.0e30), *(
        (probability, gain)
        for probability in probabilities
        for gain in gains
    )]
    candidates = []
    for probability, gain in pairs:
        thresholds = {
            "primary_probability_threshold": float(
                primary_probability_threshold
            ),
            "primary_expected_gain_threshold": float(
                primary_expected_gain_threshold
            ),
            "secondary_probability_threshold": float(probability),
            "secondary_expected_gain_threshold": float(gain),
        }
        metrics = evaluate_combined_policy(contexts, thresholds)
        if not (
            int(metrics["activation_count"]) > 0
            and int(metrics["right_censored_count"]) == 0
            and int(metrics["unsafe_count"]) == 0
            and float(metrics["net_geomean_ratio"]) < 1.0
        ):
            continue
        secondary_count = sum(
            int(metrics["arm_counts"].get(arm, 0))
            for arm in QG2_SECONDARY_ARMS
        )
        candidates.append(
            (
                float(metrics["net_geomean_ratio"]),
                -int(metrics["activation_count"]),
                secondary_count,
                -float(probability),
                -float(gain),
                thresholds,
                metrics,
            )
        )
    if not candidates:
        thresholds = {
            "primary_probability_threshold": float(
                primary_probability_threshold
            ),
            "primary_expected_gain_threshold": float(
                primary_expected_gain_threshold
            ),
            "secondary_probability_threshold": 2.0,
            "secondary_expected_gain_threshold": 1.0e30,
        }
        return {
            **thresholds,
            "evaluation_gate_policy": QG2_POSITIVE_NET_EVALUATION_GATE_V1,
            "evaluation_gate_passed": False,
            "secondary_enabled": False,
            "fallback_action": QG2_NOOP_ARM,
            "reason": "no_exact_safe_uncensored_positive_net_calibration_policy",
            "calibration_metrics": evaluate_combined_policy(
                contexts, thresholds
            ),
        }
    selected = min(candidates)
    metrics = selected[6]
    secondary_enabled = any(
        int(metrics["arm_counts"].get(arm, 0)) > 0
        for arm in QG2_SECONDARY_ARMS
    )
    return {
        **selected[5],
        "evaluation_gate_policy": QG2_POSITIVE_NET_EVALUATION_GATE_V1,
        "evaluation_gate_passed": True,
        "secondary_enabled": secondary_enabled,
        "fallback_action": QG2_NOOP_ARM,
        "reason": (
            "best_exact_safe_uncensored_positive_net_combined_policy"
            if secondary_enabled
            else "positive_net_qg2_primary_secondary_disabled"
        ),
        "calibration_metrics": metrics,
    }


def wilson_bound(successes: int, trials: int, *, upper: bool) -> float:
    if trials <= 0:
        return 1.0 if upper else 0.0
    p = float(successes) / float(trials)
    z = ONE_SIDED_95_Z
    denominator = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denominator
    radius = z * math.sqrt(
        p * (1.0 - p) / trials + z * z / (4.0 * trials * trials)
    ) / denominator
    return min(1.0, center + radius) if upper else max(0.0, center - radius)


def _scale_metrics(rows: Sequence[tuple[str, ArmOutcome]]) -> dict[str, Any]:
    actions = [(arm, outcome) for arm, outcome in rows if arm != QG2_NOOP_ARM]
    return {
        "context_count": len(rows),
        "activation_count": len(actions),
        "arm_counts": {
            arm: sum(selected == arm for selected, _outcome in actions)
            for arm in (QG2_PRIMARY_ARM, *QG2_SECONDARY_ARMS)
        },
        "harmful_count": sum(outcome.harmful for _arm, outcome in actions),
        "net_geomean_ratio": _geomean(
            outcome.ratio if arm != QG2_NOOP_ARM else 1.0
            for arm, outcome in rows
        ),
    }


def _geomean(values: Iterable[float]) -> float:
    rows = [max(1.0e-12, float(value)) for value in values]
    return 1.0 if not rows else math.exp(statistics.fmean(math.log(v) for v in rows))


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False
