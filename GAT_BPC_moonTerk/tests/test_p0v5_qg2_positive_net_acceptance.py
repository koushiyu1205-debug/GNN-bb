from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/analyze_p0v5_qg2_positive_net_acceptance.py"
SPEC = importlib.util.spec_from_file_location("qg2_positive_net_acceptance", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _metrics(scale: int) -> dict:
    exact = 15 if scale == 50 else 20
    return {
        "instance_count": 20,
        "control_exact_count": exact,
        "guided_exact_count": exact,
        "common_exact_count": exact,
        "paired_geomean_wall_ratio": (
            1.01 if scale in {5, 10, 20} else (1.02 if scale == 30 else 0.97)
        ),
        "guided_qg2_inference_event_count": 0 if scale < 30 else 2,
        "guided_qg2_action_count": 0 if scale < 30 else 1,
    }


def _pairs() -> list[dict]:
    return [
        {
            "scale": 30,
            "common_exact": True,
            "wall_ratio": 1.01,
            "objective_match": True,
            "control": {"redlines_zero": True},
            "guided": {"redlines_zero": True},
        },
        {
            "scale": 50,
            "common_exact": True,
            "wall_ratio": 0.98,
            "objective_match": True,
            "control": {"redlines_zero": True},
            "guided": {"redlines_zero": True},
        },
    ]


def test_positive_net_formal_accepts_compensated_small_high_scale_effect() -> None:
    by_scale = {str(scale): _metrics(scale) for scale in (5, 10, 20, 30, 50)}
    assert MODULE._positive_net_violations(
        mode="formal", pairs=_pairs(), by_scale=by_scale
    ) == []


def test_positive_net_formal_keeps_small_scale_and_exact_hard_gates() -> None:
    by_scale = {str(scale): _metrics(scale) for scale in (5, 10, 20, 30, 50)}
    by_scale["10"]["guided_qg2_inference_event_count"] = 1
    by_scale["50"]["guided_exact_count"] = 14
    violations = MODULE._positive_net_violations(
        mode="formal", pairs=_pairs(), by_scale=by_scale
    )
    assert "scale10_qg2_inference_not_zero" in violations
    assert "scale50_exact_count_regression" in violations
    assert "scale50_exact_below_15" in violations
