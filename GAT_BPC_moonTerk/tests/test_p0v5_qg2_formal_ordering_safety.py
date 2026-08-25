from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_p0v5_qg2_formal_ordering_safety.py"
SPEC = importlib.util.spec_from_file_location("qg2_formal_safety", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_recursive_ordering_safety_accepts_only_ordering_actions() -> None:
    safe = MODULE._scan_payload({
        "nodes": [{
            "proof_tail_gat_action": "QG2",
            "proof_tail_gat_runtime_enabled": True,
            "proof_tail_gat_inference_wall_ms": 1.2,
            "guidance_filter_count": 0,
            "guidance_arc_drop_count": 0,
            "guidance_label_drop_count": 0,
            "guidance_branch_pair_drop_count": 0,
            "labels_dropped": False,
            "guidance_can_filter": False,
            "guidance_can_certify": False,
        }],
    }, role="guided", scale=30)
    assert safe["qg2_action_count"] == 1
    assert safe["inference_event_count"] == 1
    assert safe["drop_count_total"] == 0
    assert safe["forbidden_authority_true_count"] == 0
    assert safe["invalid_action_count"] == 0


def test_recursive_ordering_safety_detects_drop_authority_and_drift() -> None:
    unsafe = MODULE._scan_payload({
        "proof_tail_gat_action": "QG2",
        "proof_tail_gat_runtime_enabled": False,
        "proof_tail_gat_fallback_reason": "checkpoint_hash_mismatch",
        "guidance_filter_count": 1,
        "guidance_label_drop_count": 2,
        "labels_dropped": True,
        "guidance_can_certify": True,
        "guidance_validation_issues": ["bad_binding"],
    }, role="guided", scale=20)
    assert unsafe["drop_count_total"] == 3
    assert unsafe["labels_dropped_true_count"] == 1
    assert unsafe["forbidden_authority_true_count"] == 1
    assert unsafe["guidance_validation_issue_count"] == 1
    assert unsafe["hash_or_checkpoint_drift_count"] == 1
    assert unsafe["qg2_action_runtime_disabled_count"] == 1
    assert unsafe["qg2_action_on_bypassed_scale_count"] == 1


def test_control_can_never_contain_qg2_action() -> None:
    row = MODULE._scan_payload({
        "proof_tail_gat_action": "QG2",
        "proof_tail_gat_runtime_enabled": True,
    }, role="control", scale=30)
    assert row["qg2_action_count"] == 1
    assert row["invalid_action_count"] == 1
