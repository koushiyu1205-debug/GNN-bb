from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/evaluate_p0v5_qg2_relaxed_training_gate.py"
SPEC = importlib.util.spec_from_file_location("qg2_relaxed_gate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _oracle(tmp_path: Path, ratio30: float, ratio50: float) -> dict:
    freeze = tmp_path / "freeze.json"
    freeze.write_text("{}\n", encoding="utf-8")
    rows = []
    initial = []
    for scale, ratio in ((30, ratio30), (50, ratio50)):
        for index in range(20):
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
        "schema_version": MODULE.ORACLE_SCHEMA,
        "development_only": True,
        "deployable": False,
        "supervision_schema_version": MODULE.SUPERVISION_SCHEMA,
        "queue_action_surface": MODULE.ACTION_SURFACE,
        "execution_freeze": str(freeze),
        "execution_freeze_sha256": MODULE._sha256(freeze),
        "context_rows": rows,
        "initial_rows": initial,
        "oracle_gate": {"passed": False},
    }


def test_relaxed_gate_allows_training_at_five_percent_oracle_gain(
    tmp_path: Path,
) -> None:
    result = MODULE.evaluate_relaxed_training_gate(
        _oracle(tmp_path, 0.94, 0.94)
    )
    assert result["training_authorized"]
    assert result["gate"]["scale30"]["passed"]
    assert result["gate"]["scale50"]["passed"]
    assert not result["gate"]["contract_errors"]


def test_relaxed_gate_still_rejects_weak_or_unsafe_oracle(
    tmp_path: Path,
) -> None:
    weak = MODULE.evaluate_relaxed_training_gate(
        _oracle(tmp_path, 0.97, 0.94)
    )
    assert not weak["training_authorized"]
    assert not weak["gate"]["scale30"]["passed"]

    unsafe_oracle = _oracle(tmp_path, 0.94, 0.94)
    unsafe_oracle["context_rows"][0]["all_safe"] = False
    unsafe = MODULE.evaluate_relaxed_training_gate(unsafe_oracle)
    assert not unsafe["training_authorized"]
    assert not unsafe["gate"]["all_exact_safe"]


def test_relaxed_gate_does_not_lower_sample_or_instance_coverage(
    tmp_path: Path,
) -> None:
    oracle = _oracle(tmp_path, 0.94, 0.94)
    oracle["context_rows"] = [
        row for row in oracle["context_rows"]
        if row["scale"] != 50 or row["state_hash"].endswith("-0")
    ]
    result = MODULE.evaluate_relaxed_training_gate(oracle)
    assert not result["training_authorized"]
    assert not result["gate"]["scale50"]["passed"]
