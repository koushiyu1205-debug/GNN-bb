from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/evaluate_p0v5_qg2_context_arm_selector.py"
SPEC = importlib.util.spec_from_file_location("qg2_context_arm_selector", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

CONTROLLER_SCRIPT = (
    ROOT / "scripts/run_p0v5_qg2_context_arm_selector_after_training.py"
)
CONTROLLER_SPEC = importlib.util.spec_from_file_location(
    "qg2_context_arm_selector_controller", CONTROLLER_SCRIPT
)
assert CONTROLLER_SPEC is not None and CONTROLLER_SPEC.loader is not None
CONTROLLER = importlib.util.module_from_spec(CONTROLLER_SPEC)
sys.modules[CONTROLLER_SPEC.name] = CONTROLLER
CONTROLLER_SPEC.loader.exec_module(CONTROLLER)


def _replay(
    *,
    wall: float,
    reached: bool = True,
    milestone: str = "ADMISSION_BATCH_READY",
    budget: float = 300.0,
) -> dict:
    return {
        "milestone_kind": milestone if reached else "RIGHT_CENSORED",
        "milestone_reached": reached,
        "milestone_wall_sec": wall,
        "admission_milestone_wall_sec": wall if reached else None,
        "total_fresh_process_wall_sec": wall,
        "requested_wall_time_limit_sec": budget,
    }


def _outcome(
    ratio: float,
    *,
    beneficial: bool | None = None,
    harmful: bool | None = None,
) -> MODULE.ArmOutcome:
    return MODULE.ArmOutcome(
        wall_sec=100.0 * ratio,
        ratio=ratio,
        milestone_matched=True,
        right_censored=False,
        beneficial=(ratio <= 0.95 if beneficial is None else beneficial),
        harmful=(ratio >= 1.05 if harmful is None else harmful),
        positive_gain_fraction=max(0.0, 1.0 - ratio),
    )


def _prediction(
    index: int,
    *,
    qd1_probability: float,
    qd1_score: float,
    qd1_outcome: MODULE.ArmOutcome,
    qb1_probability: float = 0.1,
    qb1_score: float = 0.01,
    qb1_outcome: MODULE.ArmOutcome | None = None,
) -> dict:
    return {
        "state_hash": f"state-{index}",
        "instance_hash": f"instance-{index}",
        "scale": 30 if index % 2 == 0 else 50,
        "q0_wall_sec": 100.0,
        "arms": {
            "QD1": {
                "benefit_probability": qd1_probability,
                "conditional_positive_gain": (
                    qd1_score / max(1.0e-9, qd1_probability)
                ),
                "expected_gain": qd1_score,
                "outcome": qd1_outcome,
            },
            "QB1": {
                "benefit_probability": qb1_probability,
                "conditional_positive_gain": (
                    qb1_score / max(1.0e-9, qb1_probability)
                ),
                "expected_gain": qb1_score,
                "outcome": qb1_outcome or _outcome(2.0),
            },
        },
    }


def test_right_censored_arm_is_a_known_harmful_action() -> None:
    q0 = _replay(wall=100.0)
    arm = _replay(wall=10.0, reached=False, budget=300.0)

    outcome = MODULE.arm_outcome(q0, arm, q0_wall=100.0)

    assert outcome.right_censored
    assert not outcome.milestone_matched
    assert outcome.wall_sec == 300.0
    assert outcome.ratio == 3.0
    assert not outcome.beneficial
    assert outcome.harmful


def test_all_rejected_actions_are_literal_q0() -> None:
    predictions = [
        _prediction(
            index,
            qd1_probability=0.2,
            qd1_score=0.01,
            qd1_outcome=_outcome(0.5),
        )
        for index in range(8)
    ]

    report = MODULE.evaluate_policy(
        predictions,
        {"benefit_probability": 0.9, "expected_gain": 0.2},
    )

    assert report["activated_count"] == 0
    assert report["no_op_count"] == 8
    assert report["net_geomean_ratio"] == 1.0
    assert report["harmful_action_count"] == 0
    assert report["fallback_action"] == "Q0"


def test_threshold_search_can_authorize_only_a_large_clean_calibration_set() -> None:
    clean = [
        _prediction(
            index,
            qd1_probability=0.99,
            qd1_score=0.5,
            qd1_outcome=_outcome(0.5),
        )
        for index in range(60)
    ]

    thresholds = MODULE.choose_thresholds(clean)

    assert thresholds["calibration_gate_passed"]
    assert thresholds["strict_deployment_risk_gate_passed"]
    report = thresholds["calibration_report"]
    assert report["activated_count"] == 60
    assert report["harmful_rate_95_upper"] <= 0.05
    assert report["beneficial_precision_95_lower"] >= 0.80


def test_small_clean_sample_allows_diagnostic_but_not_deployment_claim() -> None:
    clean = [
        _prediction(
            index,
            qd1_probability=0.99,
            qd1_score=0.5,
            qd1_outcome=_outcome(0.5),
        )
        for index in range(10)
    ]

    thresholds = MODULE.choose_thresholds(clean)

    assert thresholds["calibration_gate_passed"]
    assert not thresholds["strict_deployment_risk_gate_passed"]
    assert thresholds["reason"] == (
        "best_development_only_zero_observed_harm_geomean"
    )
    report = thresholds["calibration_report"]
    assert report["harmful_action_count"] == 0
    assert report["harmful_rate_95_upper"] > 0.05


def test_harmful_calibration_actions_force_noop_thresholds() -> None:
    harmful = [
        _prediction(
            index,
            qd1_probability=0.99,
            qd1_score=0.5,
            qd1_outcome=_outcome(2.0),
        )
        for index in range(60)
    ]

    thresholds = MODULE.choose_thresholds(harmful)

    assert not thresholds["calibration_gate_passed"]
    assert thresholds["benefit_probability"] > 1.0
    report = MODULE.evaluate_policy(harmful, thresholds)
    assert report["activated_count"] == 0
    assert report["net_geomean_ratio"] == 1.0


def test_neutral_selected_action_is_still_counted_as_activation() -> None:
    predictions = [
        _prediction(
            0,
            qd1_probability=0.99,
            qd1_score=0.5,
            qd1_outcome=_outcome(1.0, beneficial=False, harmful=False),
        )
    ]

    report = MODULE.evaluate_policy(
        predictions,
        {"benefit_probability": 0.9, "expected_gain": 0.2},
    )

    assert report["activated_count"] == 1
    assert report["beneficial_action_count"] == 0
    assert report["harmful_action_count"] == 0
    assert report["per_scale"]["30"]["activated_count"] == 1


def test_controller_freeze_preserves_offline_q0_fallback_contract() -> None:
    CONTROLLER._validate_freeze()
    freeze = json.loads(CONTROLLER.FREEZE.read_text(encoding="utf-8"))
    assert freeze["starts_solver_process"] is False
    assert freeze["changes_qg2"] is False
    assert freeze["fallback_action"] == "Q0"
    assert freeze["all_arms_rejected_action"] == "Q0"


def test_controller_runs_only_after_training_and_never_authorizes_deployment(
    monkeypatch,
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run"
    training_dir = run_root / "training"
    training_path = training_dir / "training_report.json"
    oracle_path = run_root / "oracle.json"
    output_dir = run_root / "selector"
    output = output_dir / "selector_report.json"
    state = run_root / "state.json"
    run_root.mkdir()
    oracle_path.write_text("{}\n", encoding="utf-8")
    training_dir.mkdir()
    training_path.write_text(json.dumps({
        "schema_version": CONTROLLER.TRAINING_SCHEMA,
        "oracle_gate_passed": True,
        "deployable": False,
        "oracle_summary": str(oracle_path),
        "oracle_summary_sha256": CONTROLLER._sha256(oracle_path),
    }), encoding="utf-8")

    monkeypatch.setattr(CONTROLLER, "TRAINING_CANDIDATES", (training_path,))
    monkeypatch.setattr(CONTROLLER, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(CONTROLLER, "OUTPUT", output)
    monkeypatch.setattr(CONTROLLER, "STATE", state)
    monkeypatch.setattr(CONTROLLER, "_validate_freeze", lambda: None)
    monkeypatch.setattr(
        CONTROLLER, "_matching_training_controller_alive", lambda _pid: False
    )

    def fake_run(command, **_kwargs):
        assert "evaluate_p0v5_qg2_context_arm_selector.py" in command[1]
        CONTROLLER._write(output, {
            "schema_version": CONTROLLER.SELECTOR_SCHEMA,
            "deployable": False,
            "starts_solver_process": False,
            "changes_qg2": False,
            "fallback_action": "Q0",
            "all_arms_rejected_action": "Q0",
            "training_report_sha256": CONTROLLER._sha256(training_path),
            "oracle_summary_sha256": CONTROLLER._sha256(oracle_path),
            "continued_development_recommended": False,
        })
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(CONTROLLER.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["selector-controller", "--wait-for-pid", "123"],
    )

    assert CONTROLLER.main() == 0
    payload = json.loads(state.read_text(encoding="utf-8"))
    assert payload["status"] == "COMPLETE_RETAIN_QG2_ONLY_WITH_Q0_FALLBACK"
    assert payload["deployment_authorized"] is False
    assert payload["fallback_action"] == "Q0"
