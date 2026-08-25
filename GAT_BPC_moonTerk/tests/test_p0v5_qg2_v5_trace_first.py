from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


collector = _load_script("collect_p0v5_qg2_v5_trace_corpus.py")
bucket_screen = _load_script(
    "screen_p0v5_qg2_v5_tinygat_bucket_arms.py"
)
matched_view = _load_script(
    "prepare_p0v5_qg2_v5_matched_arm_view.py"
)
matched_runner = _load_script(
    "run_p0v5_qg2_v5_matched_arms.py"
)


def _coverage():
    return {
        "30": {
            "context_count": 33,
            "instance_count": 10,
            "label_trace_count": 100,
            "partition_context_counts": {
                "train": 13, "calibration": 12, "heldout": 8,
            },
            "partition_instance_counts": {
                "train": 5, "calibration": 3, "heldout": 2,
            },
        },
        "50": {
            "context_count": 20,
            "instance_count": 15,
            "label_trace_count": 100,
            "partition_context_counts": {
                "train": 8, "calibration": 7, "heldout": 5,
            },
            "partition_instance_counts": {
                "train": 7, "calibration": 4, "heldout": 4,
            },
        },
    }


def test_trace_supervision_gate_is_data_only():
    gate = collector._supervision_gate(_coverage())
    assert gate["passed"]
    assert not gate["performance_deployment_authority"]
    assert gate["fresh_process_force_on_required"]


def test_trace_supervision_gate_requires_scale_and_partition_instances():
    coverage = _coverage()
    coverage["50"]["partition_instance_counts"]["heldout"] = 1
    gate = collector._supervision_gate(coverage)
    assert not gate["passed"]
    assert "scale50_heldout_instances" in gate["errors"]


def test_trace_replay_rejects_guidance_drop():
    row = {
        "state_hash": "state",
        "source_engine_hash": "engine",
        "source_config_hash": "config",
        "source_exact_action_policy_hash": "policy-hash",
    }
    replay = {
        "schema_version": collector.REPLAY_SCHEMA,
        "source_state_hash": "state",
        "source_engine_hash": "engine",
        "source_config_hash": "config",
        "source_exact_action_policy_hash": "policy-hash",
        "policy": "Q0",
        "repeat_index": 1,
        "guidance_bucket_width": collector.BUCKET,
        "requested_wall_time_limit_sec": 300.0,
        "requested_memory_limit_gb": 10.867,
        "requested_label_trace": True,
        "milestone_reached": True,
        "labels_dropped": False,
        "proof_telemetry": {
            "proof_queue_label_trace_enabled": True,
            "proof_queue_label_state_trace": [{"label_id": 1}],
            "guidance_filter_count": 1,
        },
    }
    with pytest.raises(SystemExit, match="guidance_drop"):
        collector._validate_trace(
            replay, row=row, wall_sec=300.0, memory_limit_gb=10.867
        )


def test_selection_freeze_is_immutable(tmp_path):
    path = tmp_path / "freeze.json"
    collector._freeze_or_validate(path, {"a": 1})
    collector._freeze_or_validate(path, {"a": 1})
    with pytest.raises(SystemExit, match="selection freeze drift"):
        collector._freeze_or_validate(path, {"a": 2})


def test_training_wrapper_declares_gat_only_stage():
    source = (
        ROOT / "scripts" / "train_p0v5_qg2_v5_label_gat.py"
    ).read_text(encoding="utf-8")
    assert '"--models", "gat"' in source
    assert '"mlp_or_linear_control_started": False' in source
    assert '"performance_oracle_gate_used": False' in source


def test_trace_view_cannot_claim_deployment():
    source = (
        ROOT / "scripts" / "collect_p0v5_qg2_v5_trace_corpus.py"
    ).read_text(encoding="utf-8")
    assert '"performance_oracle": False' in source
    assert '"production_switch_authorized": False' in source
    assert '"random_or_leaked_qo2_outcomes_used": False' in source


def test_bucket_screen_aggregate_keeps_censored_arm_unmatched():
    records = [{
        "scale": 30,
        "state_hash": "state",
        "q0_median_wall_sec": 10.0,
        "milestone_kind": "EXACT_PROOF_COMPLETION",
    }]
    arms = [{
        "scale": 30,
        "state_hash": "state",
        "bucket_width": 0.0001,
        "result": {
            "milestone_reached": False,
            "milestone_kind": "RIGHT_CENSORED",
            "wall_sec": 30.0,
        },
    }]
    report = bucket_screen._aggregate(arms, records)
    row = report["rows"][0]
    assert not row["all_matched_milestone"]
    assert row["ratio"] is None
    assert report["aggregate"]["by_bucket_width"]["0.0001"][
        "matched_context_count"
    ] == 0


def test_bucket_screen_rejects_any_exact_boundary_change():
    arm = {"state_hash": "state"}
    replay = {
        "policy": "QG2",
        "source_state_hash": "state",
        "ordering_only": True,
        "can_filter": False,
        "can_prune": True,
        "can_change_reduced_cost": False,
        "can_certify_from_guidance": False,
        "labels_dropped": False,
        "certificate_blockers": [],
        "proof_telemetry": {"rc_mismatch_count": 0},
    }
    with pytest.raises(SystemExit, match="exact-safe boundary"):
        bucket_screen._validate_replay(arm, replay)


def test_matched_arm_selection_balances_scale_and_partition():
    rows = []
    for scale in (30, 50):
        for partition in matched_view.PARTITIONS:
            for index in range(4):
                rows.append({
                    "scale": scale,
                    "partition": partition,
                    "state_hash": f"{scale}-{partition}-{index}",
                    "compliant_context": True,
                    "all_initial_arms_safe": True,
                })
    selected = matched_view._select(
        rows,
        requested={"train": 2, "calibration": 2, "heldout": 1},
    )
    assert matched_view._counts(selected) == {
        "30": {"train": 2, "calibration": 2, "heldout": 1},
        "50": {"train": 2, "calibration": 2, "heldout": 1},
    }


def test_instance_balanced_order_takes_one_context_per_instance_first():
    rows = [
        {
            "instance_hash": instance,
            "state_hash": f"{instance}-{index}",
            "q0_milestone_kind": "EXACT_PROOF_COMPLETION",
        }
        for instance in ("a", "b", "c")
        for index in range(2)
    ]
    ordered = matched_view._instance_balanced(rows)
    assert len({row["instance_hash"] for row in ordered[:3]}) == 3


def test_v5_matched_arm_selection_must_be_parent_subset(tmp_path):
    parent_path = tmp_path / "parent.json"
    parent = {
        "schema_version": matched_runner.ORACLE_SCHEMA,
        "initial_rows": [{"state_hash": "a"}],
    }
    parent_path.write_text(json.dumps(parent), encoding="utf-8")
    selection_path = tmp_path / "selection.json"
    selection = {
        "schema_version": matched_runner.ORACLE_SCHEMA,
        "selection_view_schema_version": matched_runner.SELECTION_SCHEMA,
        "source_training_view": str(parent_path),
        "source_training_view_sha256": matched_runner._sha256(parent_path),
        "selection_uses_action_outcomes": False,
        "deployable": False,
        "selected_context_count": 1,
        "initial_rows": [{"state_hash": "outside"}],
    }
    selection_path.write_text(json.dumps(selection), encoding="utf-8")
    with pytest.raises(SystemExit, match="strict parent subset"):
        matched_runner._validate_selection(
            parent_path=parent_path,
            parent=parent,
            selection_path=selection_path,
            selection=selection,
        )
