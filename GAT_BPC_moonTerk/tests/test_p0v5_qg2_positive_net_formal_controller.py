from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_p0v5_qg2_positive_net_formal_after_e2e.py"
SPEC = importlib.util.spec_from_file_location("qg2_positive_net_formal", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_positive_net_formal_freeze_preserves_q0_and_full20_scope() -> None:
    MODULE._validate_freeze()
    freeze = json.loads(MODULE.FREEZE.read_text(encoding="utf-8"))
    assert freeze["positive_net_e2e_required"] is True
    assert freeze["minimum_speedup_gate_enabled"] is False
    assert freeze["production_default"] is False
    assert freeze["fallback_action"] == "Q0"


def test_positive_net_formal_environment_keeps_small_scales_q0(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "manifest.json"
    _write(manifest, {})
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", "stale")
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE", "1")

    control = MODULE._environment(manifest=None)
    guided = MODULE._environment(manifest=manifest)

    assert "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST" not in control
    assert "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE" not in control
    assert guided["LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST"] == str(manifest)
    assert guided["LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE"] == "1"


def test_positive_net_formal_runs_full20_only_after_e2e_authority(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    e2e_state = run / "e2e_state.json"
    e2e_result = run / "e2e_result.json"
    manifest = run / "manifest.json"
    output_root = run / "formal"
    control = output_root / "control"
    guided = output_root / "guided"
    result = run / "formal_result.json"
    state = run / "formal_state.json"
    for path in (e2e_state, e2e_result, manifest):
        _write(path, {})
    for name, value in {
        "E2E_STATE": e2e_state,
        "E2E_RESULT": e2e_result,
        "OUTPUT_ROOT": output_root,
        "CONTROL_ROOT": control,
        "GUIDED_ROOT": guided,
        "RESULT": result,
        "STATE": state,
    }.items():
        monkeypatch.setattr(MODULE, name, value)
    monkeypatch.setattr(MODULE, "_validate_freeze", lambda: None)
    monkeypatch.setattr(MODULE, "_matching_e2e_controller", lambda _pid: False)
    monkeypatch.setattr(MODULE, "_validate_e2e_authority", lambda **_kwargs: manifest)
    calls = []
    monkeypatch.setattr(
        MODULE,
        "_run_acceptance",
        lambda **kwargs: calls.append(kwargs) or 0,
    )

    def fake_run(command, **_kwargs):
        assert command[-2:] == ["--mode", "formal"]
        _write(result, {
            "schema_version": MODULE.E2E_ACCEPTANCE_SCHEMA,
            "mode": "positive_net_formal",
            "passed": True,
            "violation_count": 0,
            "violations": [],
            "by_scale": {str(scale): {} for scale in (5, 10, 20, 30, 50)},
            "scale30_50_combined_geomean_wall_ratio": 0.999,
        })
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys, "argv", ["positive-net-formal", "--wait-for-pid", "123"]
    )

    assert MODULE.main() == 0
    assert [row["manifest"] for row in calls] == [None, manifest]
    payload = json.loads(state.read_text(encoding="utf-8"))
    assert payload["status"] == "POSITIVE_NET_FORMAL_FULL20_PASSED"
    assert payload["candidate_freeze_permitted"] is True
    assert payload["production_switch_performed"] is False
    assert payload["fallback_action"] == "Q0"
