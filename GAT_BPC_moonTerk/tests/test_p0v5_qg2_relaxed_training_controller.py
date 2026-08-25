from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def _module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ENTRY = _module(
    "qg2_relaxed_training_entry_test",
    "scripts/run_p0v5_qg2_relaxed_training_entry.py",
)
CONTROLLER = _module(
    "qg2_relaxed_training_controller_test",
    "scripts/run_p0v5_qg2_relaxed_training_after_oracle.py",
)


def test_relaxed_entry_only_overrides_training_sample_reachability(
    monkeypatch,
) -> None:
    globals_dict = {
        "MINIMUM_CALIBRATION_CONTEXTS_FOR_HARMFUL_GATE": 52,
    }
    exec(
        "def main():\n"
        "    return MINIMUM_CALIBRATION_CONTEXTS_FOR_HARMFUL_GATE\n",
        globals_dict,
    )
    frozen_main = globals_dict["main"]
    monkeypatch.setattr(
        ENTRY.runpy,
        "run_path",
        lambda *_args, **_kwargs: {"main": frozen_main},
    )
    monkeypatch.setattr(sys, "argv", ["relaxed-entry", "--sentinel"])

    assert ENTRY.main() == 1
    assert globals_dict["MINIMUM_CALIBRATION_CONTEXTS_FOR_HARMFUL_GATE"] == 1
    assert sys.argv == [str(ENTRY.TRAINER), "--sentinel"]


def test_relaxed_controller_validates_frozen_contract() -> None:
    freeze = CONTROLLER._validate_freeze()
    assert freeze["development_only"]
    assert not freeze["deployable"]
    oracle = {
        "schema_version": CONTROLLER.ORACLE_SCHEMA,
        "supervision_schema_version": CONTROLLER.SUPERVISION_SCHEMA,
        "queue_action_surface": CONTROLLER.ACTION_SURFACE,
        "execution_freeze_sha256": freeze["oracle_execution_freeze_sha256"],
        "development_only": True,
        "deployable": False,
    }
    assert CONTROLLER._oracle_contract_valid(
        oracle,
        freeze["oracle_execution_freeze_sha256"],
    )
    oracle["queue_action_surface"] = "unreachable_action_surface"
    assert not CONTROLLER._oracle_contract_valid(
        oracle,
        freeze["oracle_execution_freeze_sha256"],
    )


def test_relaxed_controller_strips_all_guidance_environment(monkeypatch) -> None:
    for key in CONTROLLER.GUIDANCE_ENV_KEYS:
        monkeypatch.setenv(key, "must-not-leak")
    env = CONTROLLER._python_env()
    assert all(key not in env for key in CONTROLLER.GUIDANCE_ENV_KEYS)
    assert str(ROOT / "src") in env["PYTHONPATH"]
    assert str(CONTROLLER.BUILD) in env["PYTHONPATH"]


def test_relaxed_controller_does_not_weaken_calibration_sample_gate() -> None:
    assert not CONTROLLER._strict_calibration_sample_reachable({
        "calibration_context_count": 51,
    })
    assert CONTROLLER._strict_calibration_sample_reachable({
        "calibration_context_count": 52,
    })
