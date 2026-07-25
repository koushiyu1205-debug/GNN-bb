"""Promotion gates and paired statistics for the staged GAT rollout."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, log
import random
from statistics import mean, median
from typing import Iterable, Mapping


@dataclass(frozen=True)
class SafetyAudit:
    guidance_induced_permanent_drop: int = 0
    binding_mismatch_accepted: int = 0
    nonfinite_hint_accepted: int = 0
    legal_universe_hash_mismatch: int = 0
    labels_dropped: bool = False
    extra_incomplete: int = 0
    objective_mismatch: int = 0
    reduced_cost_mismatch: int = 0
    certificate_mismatch: int = 0

    @property
    def passed(self) -> bool:
        return not any(
            (
                self.guidance_induced_permanent_drop,
                self.binding_mismatch_accepted,
                self.nonfinite_hint_accepted,
                self.legal_universe_hash_mismatch,
                self.labels_dropped,
                self.extra_incomplete,
                self.objective_mismatch,
                self.reduced_cost_mismatch,
                self.certificate_mismatch,
            )
        )


def paired_runtime_summary(
    control_seconds: Iterable[float],
    guided_seconds: Iterable[float],
    *,
    bootstrap_samples: int = 2000,
    seed: int = 20260723,
) -> dict:
    control = tuple(float(value) for value in control_seconds)
    guided = tuple(float(value) for value in guided_seconds)
    if len(control) != len(guided) or not control:
        raise ValueError("paired runtime vectors must have equal nonzero length")
    if any(value <= 0.0 for value in (*control, *guided)):
        raise ValueError("runtime values must be positive")
    ratios = tuple(g / c for c, g in zip(control, guided, strict=True))
    rng = random.Random(seed)
    bootstrap = []
    for _ in range(max(1, int(bootstrap_samples))):
        sampled = [ratios[rng.randrange(len(ratios))] for _ in ratios]
        bootstrap.append(_geometric_mean(sampled))
    bootstrap.sort()
    lower_index = int(0.025 * (len(bootstrap) - 1))
    upper_index = int(0.975 * (len(bootstrap) - 1))
    return {
        "pair_count": len(ratios),
        "p50_ratio": median(ratios),
        "mean_ratio": mean(ratios),
        "paired_geometric_mean_ratio": _geometric_mean(ratios),
        "bootstrap_geometric_mean_ratio_ci95": [
            bootstrap[lower_index],
            bootstrap[upper_index],
        ],
    }


def stage_b_gate(
    *,
    safety: SafetyAudit,
    first_addable_negative_p50_ratio_20_30: float,
    equal_budget_best_rc_improved: bool,
    duplicate_negative_rate_delta: float,
    rmp_bound_gain_per_pricing_second_improved: bool,
    medium_runtime: Mapping[str, float],
    small_runtime: Mapping[str, float],
) -> dict:
    checks = {
        "safety_gate": safety.passed,
        "first_addable_negative_p50_at_least_15pct": (
            float(first_addable_negative_p50_ratio_20_30) <= 0.85
        ),
        "equal_budget_best_rc_trajectory": bool(equal_budget_best_rc_improved),
        "duplicate_negative_rate_nonincrease": (
            float(duplicate_negative_rate_delta) <= 0.0
        ),
        "rmp_bound_gain_per_pricing_second": bool(
            rmp_bound_gain_per_pricing_second_improved
        ),
        "medium_p50": float(medium_runtime["p50_ratio"]) <= 0.90,
        "medium_paired_geometric_mean": float(
            medium_runtime["paired_geometric_mean_ratio"]
        )
        <= 0.90,
        "medium_mean": float(medium_runtime["mean_ratio"]) <= 1.0,
        "small_p50": float(small_runtime["p50_ratio"]) <= 1.02,
        "small_mean": float(small_runtime["mean_ratio"]) <= 1.03,
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "failed_checks": [
            name for name, passed in checks.items() if not passed
        ],
        "on_failure": "fallback_p0_and_do_not_mask_with_later_modules",
    }


def holm_rejections(
    p_values: Mapping[str, float], *, alpha: float = 0.05
) -> dict[str, bool]:
    ordered = sorted(
        ((str(name), float(value)) for name, value in p_values.items()),
        key=lambda row: (row[1], row[0]),
    )
    result = {name: False for name in p_values}
    for index, (name, value) in enumerate(ordered):
        threshold = float(alpha) / (len(ordered) - index)
        if value > threshold:
            break
        result[name] = True
    return result


def large_scale_claim_boundary(
    *,
    scale50_exact_root_closed: bool,
    scale100_exact_root_closed: bool,
) -> str:
    if scale50_exact_root_closed and scale100_exact_root_closed:
        return "exact_root_closure_available_claims_still_require_formal_promotion"
    return "shadow_ordering_and_resource_behavior_only_no_full_bpc_speedup_claim"


def _geometric_mean(values: Iterable[float]) -> float:
    rows = tuple(float(value) for value in values)
    return exp(mean(log(value) for value in rows))
