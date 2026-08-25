from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/evaluate_p0v5_qg2_positive_net_calibration.py"
SPEC = importlib.util.spec_from_file_location(
    "qg2_positive_net_calibration", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _row(index: int, *, ratio: float = 0.9, **extra) -> dict:
    return {
        "state_hash": f"state-{index}",
        "instance_hash": f"instance-{index}",
        "scale": 30 if index % 2 == 0 else 50,
        "action_eligible": True,
        "benefit_probability": 0.9,
        "expected_gain": 1.0,
        "ratio": ratio,
        "outcome_determined": True,
        "right_censored": False,
        "safe": True,
        **extra,
    }


def test_positive_net_threshold_has_no_five_percent_sample_gate() -> None:
    rows = [_row(index, ratio=0.99) for index in range(10)]

    thresholds = MODULE.choose_positive_net_thresholds(rows)
    metrics = MODULE.activation_metrics(rows, thresholds)

    assert thresholds["gate_passed"]
    assert metrics["activation_count"] == 10
    assert metrics["net_geomean_ratio"] < 1.0
    assert metrics["selected_right_censored_count"] == 0
    assert metrics["selected_unsafe_count"] == 0


def test_censored_or_unsafe_selected_action_remains_hard_veto() -> None:
    censored = [
        _row(
            index,
            ratio=0.5,
            outcome_determined=False,
            right_censored=True,
        )
        for index in range(10)
    ]
    unsafe = [_row(index, ratio=0.5, safe=False) for index in range(10)]

    assert not MODULE.choose_positive_net_thresholds(censored)["gate_passed"]
    assert not MODULE.choose_positive_net_thresholds(unsafe)["gate_passed"]


def test_ood_or_low_confidence_rows_are_literal_noop() -> None:
    rows = [
        _row(0, action_eligible=False, ratio=0.1),
        _row(1, benefit_probability=0.1, expected_gain=0.01, ratio=2.0),
        _row(2, ratio=0.9),
    ]
    thresholds = {
        "probability_threshold": 0.8,
        "expected_gain_threshold": 0.5,
    }

    metrics = MODULE.activation_metrics(rows, thresholds)

    assert metrics["activation_count"] == 1
    assert metrics["no_op_count"] == 2
    assert metrics["net_geomean_ratio"] < 1.0
    assert metrics["selected_state_hashes"] == ["state-2"]
