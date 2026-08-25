from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


def _module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GATE = _module(
    "qg2_training_only_gate_v2_test",
    "scripts/evaluate_p0v5_qg2_training_only_gate_v2.py",
)
CONTROLLER = _module(
    "qg2_training_only_controller_v2_test",
    "scripts/run_p0v5_qg2_training_only_v2_after_oracle.py",
)


def _oracle(tmp_path: Path) -> dict:
    freeze = tmp_path / "freeze.json"
    freeze.write_text("{}\n", encoding="utf-8")
    rows = []
    initial = []
    for scale in (30, 50):
        for index in range(20):
            # Deliberately make the fixed arm poor overall while preserving
            # five strong positive instances and many harmful/no-op labels.
            ratio = 0.94 if index < 5 else 1.20
            instance = f"{scale}-{index}"
            rows.append({
                "scale": scale,
                "instance_hash": instance,
                "state_hash": f"state-{instance}",
                "ratio": ratio,
                "saved_wall_sec": max(0.0, 100.0 * (1.0 - ratio)),
                "outcome_determined": True,
                "all_safe": True,
            })
            initial.append({
                "scale": scale,
                "instance_hash": instance,
                "compliant_context": True,
                "all_initial_arms_safe": True,
            })
    return {
        "schema_version": GATE.ORACLE_SCHEMA,
        "development_only": True,
        "deployable": False,
        "supervision_schema_version": GATE.SUPERVISION_SCHEMA,
        "queue_action_surface": GATE.ACTION_SURFACE,
        "execution_freeze": str(freeze),
        "execution_freeze_sha256": GATE._sha256(freeze),
        "context_rows": rows,
        "initial_rows": initial,
        "oracle_gate": {"passed": False},
    }


def test_training_only_gate_allows_selective_fitting_despite_bad_fixed_arm(
    tmp_path: Path,
) -> None:
    result = GATE.evaluate_training_only_gate_v2(_oracle(tmp_path))

    assert result["training_authorized"]
    for scale in (30, 50):
        metrics = result["gate"][f"scale{scale}"]
        assert metrics["passed"]
        assert metrics["paired_geomean_ratio_report_only"] > 1.0
        assert metrics["instance_bootstrap_95_upper_report_only"] > 1.0
        assert metrics["gain_5pct_context_count"] == 5
        assert metrics["harmful_instance_count"] == 15


def test_training_only_gate_requires_both_positive_and_harmful_support(
    tmp_path: Path,
) -> None:
    no_harm = _oracle(tmp_path)
    for row in no_harm["context_rows"]:
        row["ratio"] = 0.94
        row["saved_wall_sec"] = 6.0
    result = GATE.evaluate_training_only_gate_v2(no_harm)
    assert not result["training_authorized"]
    assert not result["gate"]["scale30"]["passed"]
    assert result["gate"]["scale30"]["harmful_instance_count"] == 0

    no_gain = _oracle(tmp_path)
    for row in no_gain["context_rows"]:
        row["ratio"] = 1.20
        row["saved_wall_sec"] = 0.0
    result = GATE.evaluate_training_only_gate_v2(no_gain)
    assert not result["training_authorized"]
    assert not result["gate"]["scale50"]["passed"]
    assert result["gate"]["scale50"]["gain_5pct_context_count"] == 0


def test_training_only_gate_keeps_exact_safety_and_binding_hard(
    tmp_path: Path,
) -> None:
    unsafe = _oracle(tmp_path)
    unsafe["context_rows"][0]["all_safe"] = False
    result = GATE.evaluate_training_only_gate_v2(unsafe)
    assert not result["training_authorized"]
    assert not result["gate"]["all_exact_safe"]

    drifted = _oracle(tmp_path)
    drifted["execution_freeze_sha256"] = "0" * 64
    result = GATE.evaluate_training_only_gate_v2(drifted)
    assert not result["training_authorized"]
    assert "execution_freeze_hash_mismatch" in result["gate"]["contract_errors"]


def test_training_only_controller_preserves_safety_shell(monkeypatch) -> None:
    freeze = CONTROLLER._validate_freeze()
    oracle = {
        "schema_version": CONTROLLER.ORACLE_SCHEMA,
        "supervision_schema_version": CONTROLLER.SUPERVISION_SCHEMA,
        "queue_action_surface": CONTROLLER.ACTION_SURFACE,
        "execution_freeze_sha256": freeze["oracle_execution_freeze_sha256"],
        "development_only": True,
        "deployable": False,
    }
    assert CONTROLLER._oracle_contract_valid(
        oracle, freeze["oracle_execution_freeze_sha256"]
    )
    oracle["deployable"] = True
    assert not CONTROLLER._oracle_contract_valid(
        oracle, freeze["oracle_execution_freeze_sha256"]
    )

    for key in CONTROLLER.GUIDANCE_ENV_KEYS:
        monkeypatch.setenv(key, "must-not-leak")
    env = CONTROLLER._python_env()
    assert all(key not in env for key in CONTROLLER.GUIDANCE_ENV_KEYS)
    assert str(ROOT / "src") in env["PYTHONPATH"]


def test_training_only_controller_waits_only_for_expected_old_controllers(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        CONTROLLER,
        "_command_line",
        lambda _pid: (
            "python scripts/run_p0v5_qg2_relaxed_training_after_oracle.py"
        ),
    )
    assert CONTROLLER._matching_old_controller_alive(123)
    monkeypatch.setattr(
        CONTROLLER,
        "_command_line",
        lambda _pid: "python unrelated.py",
    )
    assert not CONTROLLER._matching_old_controller_alive(123)


def test_training_only_controller_runs_fitting_only_after_old_paths_finish(
    monkeypatch,
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run"
    oracle_path = run_root / "oracle.json"
    gate_path = run_root / "gate.json"
    authorized_path = run_root / "authorized.json"
    training_dir = run_root / "training"
    training_report = training_dir / "training_report.json"
    state_path = run_root / "state.json"
    expected_freeze_sha = "f" * 64
    oracle = {
        "schema_version": CONTROLLER.ORACLE_SCHEMA,
        "supervision_schema_version": CONTROLLER.SUPERVISION_SCHEMA,
        "queue_action_surface": CONTROLLER.ACTION_SURFACE,
        "execution_freeze_sha256": expected_freeze_sha,
        "development_only": True,
        "deployable": False,
        "oracle_gate": {"passed": False},
    }
    run_root.mkdir()
    oracle_path.write_text(json.dumps(oracle), encoding="utf-8")

    monkeypatch.setattr(CONTROLLER, "ORACLE_SUMMARY", oracle_path)
    monkeypatch.setattr(CONTROLLER, "GATE_REPORT", gate_path)
    monkeypatch.setattr(CONTROLLER, "AUTHORIZED_ORACLE", authorized_path)
    monkeypatch.setattr(CONTROLLER, "TRAINING_DIR", training_dir)
    monkeypatch.setattr(CONTROLLER, "TRAINING_REPORT", training_report)
    monkeypatch.setattr(CONTROLLER, "STATE", state_path)
    monkeypatch.setattr(CONTROLLER, "STRICT_TRAINING_DIR", run_root / "strict")
    monkeypatch.setattr(CONTROLLER, "RELAXED_TRAINING_DIR", run_root / "relaxed")
    monkeypatch.setattr(
        CONTROLLER,
        "_validate_freeze",
        lambda: {"oracle_execution_freeze_sha256": expected_freeze_sha},
    )
    monkeypatch.setattr(CONTROLLER, "_matching_oracle_alive", lambda _pid: False)
    monkeypatch.setattr(
        CONTROLLER, "_matching_old_controller_alive", lambda _pid: False
    )

    calls = []

    def fake_run(command, **_kwargs):
        calls.append(command)
        if "evaluate_p0v5_qg2_training_only_gate_v2.py" in command[1]:
            CONTROLLER._write(gate_path, {
                "schema_version": CONTROLLER.GATE_SCHEMA,
                "supervision_schema_version": CONTROLLER.SUPERVISION_SCHEMA,
                "queue_action_surface": CONTROLLER.ACTION_SURFACE,
                "oracle_summary_sha256": CONTROLLER._sha256(oracle_path),
                "gate": {"passed": True},
                "training_authorized": True,
                "deployment_authorized": False,
                "point_geomean_is_report_only": True,
                "instance_bootstrap_is_report_only": True,
            })
        else:
            CONTROLLER._write(training_report, {
                "schema_version": CONTROLLER.TRAINING_SCHEMA,
                "supervision_schema_version": CONTROLLER.SUPERVISION_SCHEMA,
                "queue_action_surface": CONTROLLER.ACTION_SURFACE,
                "oracle_gate_passed": True,
                "calibration_context_count": 7,
            })
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(CONTROLLER.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "training-only-v2",
            "--wait-for-pid", "11",
            "--wait-for-controller-pid", "12",
            "--wait-for-controller-pid", "13",
        ],
    )

    assert CONTROLLER.main() == 0
    assert len(calls) == 2
    authorized = json.loads(authorized_path.read_text(encoding="utf-8"))
    assert authorized["training_permitted"]
    assert not authorized["deployable"]
    assert not authorized["training_only_v2_authority"][
        "deployment_authorized"
    ]
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["status"] == (
        "TRAINING_ONLY_V2_COMPLETE_PENDING_STRICT_CALIBRATION"
    )
