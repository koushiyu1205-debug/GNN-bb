from __future__ import annotations

from math import comb
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.analyze_p0v5_frontier_coverage_v7r3 import (
    stable_binomial_tail_at_least,
    stable_candidate_cap,
)


def _reference(trials: int, target: int, probability: float) -> float:
    return sum(
        comb(trials, k) * probability ** k * (1.0 - probability) ** (trials - k)
        for k in range(target, trials + 1)
    )


def test_stable_tail_matches_small_exact_reference() -> None:
    for trials, target, probability in ((20, 4, 0.2), (37, 8, 0.1), (50, 12, 0.35)):
        assert abs(
            stable_binomial_tail_at_least(trials, target, probability)
            - _reference(trials, target, probability)
        ) <= 1.0e-12


def test_v7_scale30_wilson_lower_cap_is_finite_and_bounded() -> None:
    probability = 0.08065766257979806
    assert stable_candidate_cap(37, probability, 0.95) == 584
    assert stable_binomial_tail_at_least(584, 37, probability) >= 0.95
