from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "scripts/audit_p0v5_qg2_training_only_v2_formal_ordering_safety.py"
)
SPEC = importlib.util.spec_from_file_location(
    "qg2_training_only_v2_formal_safety",
    SCRIPT,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _root(*, qg2_actions: int = 0, inference_events: int = 0) -> dict:
    return {
        "tree_count": 100,
        "drop_count_total": 0,
        "labels_dropped_true_count": 0,
        "forbidden_authority_true_count": 0,
        "guidance_validation_issue_count": 0,
        "hash_or_checkpoint_drift_count": 0,
        "invalid_action_count": 0,
        "qg2_action_runtime_disabled_count": 0,
        "qg2_action_on_bypassed_scale_count": 0,
        "qg2_action_count": qg2_actions,
        "inference_event_count": inference_events,
        "by_scale": {
            str(scale): {
                "tree_count": 20,
                "qg2_action_count": 0,
                "inference_event_count": 0,
            }
            for scale in MODULE.SCALES
        },
    }


def test_runtime_contract_accepts_literal_q0_on_bypassed_scales() -> None:
    rows = {
        "control": _root(),
        "guided": _root(qg2_actions=4, inference_events=4),
    }
    rows["guided"]["by_scale"]["30"].update({
        "qg2_action_count": 2,
        "inference_event_count": 2,
    })
    rows["guided"]["by_scale"]["50"].update({
        "qg2_action_count": 2,
        "inference_event_count": 2,
    })
    assert MODULE._runtime_violations(rows) == []


def test_runtime_contract_rejects_bypassed_scale_action_or_inference() -> None:
    rows = {"control": _root(), "guided": _root()}
    rows["guided"]["by_scale"]["10"].update({
        "qg2_action_count": 1,
        "inference_event_count": 1,
    })
    violations = MODULE._runtime_violations(rows)
    assert "guided_scale10_qg2_action_count_nonzero" in violations
    assert "guided_scale10_qg2_inference_event_count_nonzero" in violations


def test_runtime_contract_rejects_any_control_guidance() -> None:
    rows = {
        "control": _root(qg2_actions=1, inference_events=1),
        "guided": _root(),
    }
    violations = MODULE._runtime_violations(rows)
    assert "control_qg2_action_count_nonzero" in violations
    assert "control_qg2_inference_event_count_nonzero" in violations


def test_runtime_contract_requires_full20_for_every_scale() -> None:
    rows = {"control": _root(), "guided": _root()}
    rows["guided"]["by_scale"]["50"]["tree_count"] = 19
    assert (
        "guided_scale50_tree_count_mismatch:19"
        in MODULE._runtime_violations(rows)
    )


def test_formal_safety_freeze_is_valid() -> None:
    MODULE._validate_freeze()
