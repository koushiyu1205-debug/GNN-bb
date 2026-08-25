from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from lunar_ice_bpc.guidance.instance_balanced_learning import (
    INSTANCE_BALANCING_POLICY_V1,
    instance_balanced_epoch_order,
    instance_balanced_geomean,
    instance_balanced_metric,
)
from lunar_ice_bpc.guidance.qg2_v4_training_freeze import (
    create_training_freeze,
    validate_training_freeze,
)


ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "qg2_v4_instance_balanced_ranker_wrapper_test",
    ROOT / "scripts/train_p0v5_qg2_v4_instance_balanced_rankers.py",
)
assert _SPEC is not None and _SPEC.loader is not None
RANKER_WRAPPER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(RANKER_WRAPPER)
_SELECTOR_SPEC = importlib.util.spec_from_file_location(
    "qg2_v4_instance_balanced_selector_wrapper_test",
    ROOT / "scripts/train_p0v5_qg2_v4_instance_balanced_arm_selector.py",
)
assert _SELECTOR_SPEC is not None and _SELECTOR_SPEC.loader is not None
SELECTOR_WRAPPER = importlib.util.module_from_spec(_SELECTOR_SPEC)
_SELECTOR_SPEC.loader.exec_module(SELECTOR_WRAPPER)
_CONTROLS_SPEC = importlib.util.spec_from_file_location(
    "qg2_v4_instance_balanced_controls_test",
    ROOT / "scripts/run_p0v5_qg2_realmap_v4_instance_balanced_controls.py",
)
assert _CONTROLS_SPEC is not None and _CONTROLS_SPEC.loader is not None
CONTROLS_WRAPPER = importlib.util.module_from_spec(_CONTROLS_SPEC)
_CONTROLS_SPEC.loader.exec_module(CONTROLS_WRAPPER)
_PIPELINE_SPEC = importlib.util.spec_from_file_location(
    "qg2_v4_instance_balanced_pipeline_test",
    ROOT / "scripts/run_p0v5_qg2_realmap_v4_instance_balanced_gat_first.py",
)
assert _PIPELINE_SPEC is not None and _PIPELINE_SPEC.loader is not None
PIPELINE_WRAPPER = importlib.util.module_from_spec(_PIPELINE_SPEC)
_PIPELINE_SPEC.loader.exec_module(PIPELINE_WRAPPER)
_SMOKE_SPEC = importlib.util.spec_from_file_location(
    "qg2_v4_instance_balanced_smoke_test",
    ROOT / "scripts/smoke_p0v5_qg2_v4_instance_balanced_training.py",
)
assert _SMOKE_SPEC is not None and _SMOKE_SPEC.loader is not None
SMOKE = importlib.util.module_from_spec(_SMOKE_SPEC)
_SMOKE_SPEC.loader.exec_module(SMOKE)
_HANDOFF_SPEC = importlib.util.spec_from_file_location(
    "qg2_v4_instance_balanced_handoff_test",
    ROOT / "scripts/watch_p0v5_qg2_v4_instance_balanced_gat_first.py",
)
assert _HANDOFF_SPEC is not None and _HANDOFF_SPEC.loader is not None
HANDOFF = importlib.util.module_from_spec(_HANDOFF_SPEC)
_HANDOFF_SPEC.loader.exec_module(HANDOFF)
_LABEL_ATTRIBUTION_SPEC = importlib.util.spec_from_file_location(
    "qg2_v4_instance_balanced_label_attribution_test",
    ROOT / "scripts/analyze_p0v5_qg2_v4_instance_balanced_gat_attribution.py",
)
assert (
    _LABEL_ATTRIBUTION_SPEC is not None
    and _LABEL_ATTRIBUTION_SPEC.loader is not None
)
LABEL_ATTRIBUTION = importlib.util.module_from_spec(_LABEL_ATTRIBUTION_SPEC)
_LABEL_ATTRIBUTION_SPEC.loader.exec_module(LABEL_ATTRIBUTION)
_SELECTOR_ATTRIBUTION_SPEC = importlib.util.spec_from_file_location(
    "qg2_v4_instance_balanced_selector_attribution_test",
    ROOT
    / "scripts/analyze_p0v5_qg2_v4_instance_balanced_selector_attribution.py",
)
assert (
    _SELECTOR_ATTRIBUTION_SPEC is not None
    and _SELECTOR_ATTRIBUTION_SPEC.loader is not None
)
SELECTOR_ATTRIBUTION = importlib.util.module_from_spec(
    _SELECTOR_ATTRIBUTION_SPEC
)
_SELECTOR_ATTRIBUTION_SPEC.loader.exec_module(SELECTOR_ATTRIBUTION)
_FRESH_SPEC = importlib.util.spec_from_file_location(
    "qg2_v4_instance_balanced_fresh_test",
    ROOT
    / "scripts/evaluate_p0v5_qg2_v4_instance_balanced_selector_fresh.py",
)
assert _FRESH_SPEC is not None and _FRESH_SPEC.loader is not None
FRESH = importlib.util.module_from_spec(_FRESH_SPEC)
_FRESH_SPEC.loader.exec_module(FRESH)
_FORCE_SPEC = importlib.util.spec_from_file_location(
    "qg2_v4_instance_balanced_force_on_test",
    ROOT
    / "scripts/calibrate_p0v5_qg2_v4_instance_balanced_gat_force_on.py",
)
assert _FORCE_SPEC is not None and _FORCE_SPEC.loader is not None
FORCE_ON = importlib.util.module_from_spec(_FORCE_SPEC)
_FORCE_SPEC.loader.exec_module(FORCE_ON)
_AUDIT_SPEC = importlib.util.spec_from_file_location(
    "qg2_v4_instance_balanced_completion_audit_test",
    ROOT / "scripts/audit_p0v5_qg2_v4_instance_balanced_completion.py",
)
assert _AUDIT_SPEC is not None and _AUDIT_SPEC.loader is not None
INSTANCE_AUDIT = importlib.util.module_from_spec(_AUDIT_SPEC)
_AUDIT_SPEC.loader.exec_module(INSTANCE_AUDIT)
_AUTH_SPEC = importlib.util.spec_from_file_location(
    "qg2_v4_instance_balanced_authorizer_test",
    ROOT
    / "scripts/authorize_p0v5_qg2_realmap_v4_instance_balanced_training.py",
)
assert _AUTH_SPEC is not None and _AUTH_SPEC.loader is not None
TRAINING_AUTHORIZER = importlib.util.module_from_spec(_AUTH_SPEC)
_AUTH_SPEC.loader.exec_module(TRAINING_AUTHORIZER)


def _order(rows, *, epoch=1, steps=None):
    return instance_balanced_epoch_order(
        rows,
        instance_key=lambda row: row["instance_hash"],
        context_key=lambda row: row["state_hash"],
        seed=20260807,
        epoch=epoch,
        steps=steps,
    )


def test_instance_balanced_epoch_does_not_follow_context_concentration() -> None:
    rows = [
        {"instance_hash": "heavy", "state_hash": f"h{index:02d}"}
        for index in range(14)
    ] + [
        {"instance_hash": "light_a", "state_hash": "a00"},
        {"instance_hash": "light_b", "state_hash": "b00"},
    ]
    selected = _order(rows)
    counts = Counter(row["instance_hash"] for row in selected)
    assert len(selected) == len(rows)
    assert max(counts.values()) - min(counts.values()) <= 1
    assert counts["heavy"] < 14


def test_instance_balanced_epoch_is_deterministic_and_rotates_contexts() -> None:
    rows = [
        {"instance_hash": "heavy", "state_hash": f"h{index:02d}"}
        for index in range(8)
    ] + [
        {"instance_hash": "light", "state_hash": "l00"},
    ]
    first = _order(rows, epoch=1)
    assert first == _order(rows, epoch=1)
    second = _order(rows, epoch=2)
    assert first != second
    first_heavy = {
        row["state_hash"] for row in first
        if row["instance_hash"] == "heavy"
    }
    second_heavy = {
        row["state_hash"] for row in second
        if row["instance_hash"] == "heavy"
    }
    assert first_heavy != second_heavy


def test_instance_balanced_epoch_rejects_missing_instance_identity() -> None:
    with pytest.raises(ValueError, match="requires instance ids"):
        _order([{"instance_hash": "", "state_hash": "s"}])


def test_instance_balanced_metric_reports_context_and_instance_views() -> None:
    result = instance_balanced_metric([
        {"instance_hash": "heavy", "accuracy": 1.0},
        {"instance_hash": "heavy", "accuracy": 1.0},
        {"instance_hash": "heavy", "accuracy": 1.0},
        {"instance_hash": "light", "accuracy": 0.0},
    ], value_key="accuracy")
    assert result["mean_context_value"] == pytest.approx(0.75)
    assert result["mean_instance_value"] == pytest.approx(0.5)
    assert result["maximum_context_fraction_by_instance"] == pytest.approx(0.75)
    assert result["per_instance_context_count"] == {"heavy": 3, "light": 1}


def test_instance_balanced_metric_handles_empty_and_nonfinite_rows() -> None:
    assert instance_balanced_metric([], value_key="accuracy") == {
        "context_count": 0,
        "instance_count": 0,
        "mean_context_value": None,
        "mean_instance_value": None,
        "maximum_context_fraction_by_instance": None,
        "per_instance_mean": {},
        "per_instance_context_count": {},
    }
    with pytest.raises(ValueError, match="lacks finite accuracy"):
        instance_balanced_metric([
            {"instance_hash": "i", "accuracy": float("nan")},
        ], value_key="accuracy")


def test_instance_balanced_geomean_prevents_context_rich_instance_bias() -> None:
    rows = [
        {"instance_hash": "fast_many", "ratio": 0.5}
        for _ in range(3)
    ] + [{"instance_hash": "slow_one", "ratio": 2.0}]
    result = instance_balanced_geomean(rows, ratio_key="ratio")
    assert result["context_geomean_ratio"] == pytest.approx(2.0 ** -0.5)
    assert result["instance_balanced_geomean_ratio"] == pytest.approx(1.0)
    assert result["per_instance_geomean_ratio"] == pytest.approx({
        "fast_many": 0.5,
        "slow_one": 2.0,
    })


def test_instance_balanced_geomean_rejects_nonpositive_ratio() -> None:
    with pytest.raises(ValueError, match="lacks positive ratio"):
        instance_balanced_geomean([
            {"instance_hash": "i", "ratio": 0.0},
        ], ratio_key="ratio")


def test_ranker_wrapper_random_shuffle_balances_training_instances() -> None:
    rows = [
        {"instance_hash": "heavy", "state_hash": f"h{index}"}
        for index in range(10)
    ] + [
        {"instance_hash": "light", "state_hash": "l0"},
    ]
    RANKER_WRAPPER._InstanceBalancedRandom(61635).shuffle(rows)
    counts = Counter(row["instance_hash"] for row in rows)
    assert max(counts.values()) - min(counts.values()) <= 1


def test_ranker_wrapper_postprocess_binds_instance_authority(
    tmp_path: Path,
) -> None:
    split = tmp_path / "split.json"
    split.write_text(json.dumps({
        "assignments": {"i1": "train", "i2": "calibration"},
    }), encoding="utf-8")
    output = tmp_path / "ranker"
    output.mkdir()
    report = output / "training_report.json"
    report.write_text(json.dumps({
        "split_path": str(split),
        "models": [{"model_kind": "gat"}],
    }), encoding="utf-8")
    RANKER_WRAPPER._EXAMPLES[:] = [
        {"instance_hash": "i1", "state_hash": "a"},
        {"instance_hash": "i1", "state_hash": "b"},
        {"instance_hash": "i2", "state_hash": "c"},
    ]
    RANKER_WRAPPER._postprocess_report(output)
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["instance_balancing_policy"] == (
        INSTANCE_BALANCING_POLICY_V1
    )
    assert payload["checkpoint_selection_metric"] == (
        "mean_instance_pair_accuracy"
    )
    assert payload["models"][0]["checkpoint_selection_metric"] == (
        "mean_instance_pair_accuracy"
    )
    assert payload["partition_instance_balance"]["train"][
        "maximum_context_fraction_by_instance"
    ] == pytest.approx(1.0)


def test_ranker_curve_names_instance_and_raw_context_calibration() -> None:
    RANKER_WRAPPER._LAST_CALIBRATION_METRICS.clear()
    RANKER_WRAPPER._LAST_CALIBRATION_METRICS.update({
        "raw_mean_context_pair_accuracy": 0.9,
    })
    row = RANKER_WRAPPER._ranker_curve_row({
        "calibration_mean_context_pair_accuracy": 0.7,
    })
    assert row["calibration_metric_unit"] == "instance"
    assert row["calibration_mean_instance_pair_accuracy"] == pytest.approx(0.7)
    assert row["calibration_raw_mean_context_pair_accuracy"] == pytest.approx(0.9)


def test_selector_wrapper_random_shuffle_balances_training_instances() -> None:
    rows = [
        {"instance_hash": "heavy", "state_hash": f"h{index}"}
        for index in range(12)
    ] + [
        {"instance_hash": "light", "state_hash": "l0"},
    ]
    SELECTOR_WRAPPER._InstanceBalancedRandom(91267).shuffle(rows)
    counts = Counter(row["instance_hash"] for row in rows)
    assert max(counts.values()) - min(counts.values()) <= 1


def test_selector_class_weights_use_instance_not_context_mass() -> None:
    trainer = SimpleNamespace(ARMS=("QD1", "QB1", "QG2"))
    rows = [
        {
            "instance_hash": "many_positive",
            "outcomes": {
                "QD1": SimpleNamespace(beneficial=True, harmful=False),
            },
        }
        for _ in range(3)
    ] + [{
        "instance_hash": "one_negative",
        "outcomes": {
            "QD1": SimpleNamespace(beneficial=False, harmful=False),
        },
    }]
    result = SELECTOR_WRAPPER._instance_balanced_class_weights(
        trainer, rows, trainable_arms=("QD1",),
    )
    assert result["benefit_positive_weight"][0] == pytest.approx(1.0)
    assert result["adverse_positive_weight"][0] == pytest.approx(1.0)


def test_selector_policy_uses_instance_balanced_geomean() -> None:
    trainer = SimpleNamespace(
        _selected_arm=lambda _row, _thresholds: "QD1",
    )
    rows = [
        {
            "instance_hash": "many_fast",
            "scale": 30,
            "arms": {"QD1": {"outcome": SimpleNamespace(
                ratio=0.5, harmful=False, beneficial=True,
            )}},
        }
        for _ in range(3)
    ] + [{
        "instance_hash": "one_slow",
        "scale": 30,
        "arms": {"QD1": {"outcome": SimpleNamespace(
            ratio=2.0, harmful=True, beneficial=False,
        )}},
    }]
    result = SELECTOR_WRAPPER._instance_balanced_policy(
        trainer, rows, thresholds={},
    )
    assert result["context_weighted_net_geomean_ratio"] == pytest.approx(
        2.0 ** -0.5
    )
    assert result["net_geomean_ratio"] == pytest.approx(1.0)
    assert result["activated_instance_count"] == 2
    assert result["harmful_instance_count"] == 1


def test_selector_bootstrap_aggregates_within_instance_first() -> None:
    result = SELECTOR_WRAPPER._instance_balanced_bootstrap_geomean(
        {"many_fast": [0.5, 0.5, 0.5], "one_slow": [2.0]},
        seed=170141,
        replicates=2001,
    )
    assert result["median"] == pytest.approx(1.0)


def test_selector_wrapper_postprocess_rehashes_checkpoint(
    tmp_path: Path,
) -> None:
    torch = pytest.importorskip("torch")
    output = tmp_path / "selector"
    output.mkdir()
    checkpoint = output / "selector.pt"
    torch.save({"schema_version": "compatible", "state_dict": {}}, checkpoint)
    report = output / "training_report.json"
    report.write_text(json.dumps({
        "checkpoint_path": str(checkpoint),
        "checkpoint_sha256": "stale",
    }), encoding="utf-8")
    SELECTOR_WRAPPER._postprocess_report(output)
    payload = json.loads(report.read_text(encoding="utf-8"))
    stored = torch.load(checkpoint, map_location="cpu", weights_only=False)
    assert stored["instance_balancing_policy"] == (
        INSTANCE_BALANCING_POLICY_V1
    )
    assert payload["checkpoint_selection_metric"] == (
        "instance_balanced_total_loss"
    )
    assert payload["checkpoint_sha256"] != "stale"


def test_selector_curve_names_instance_and_raw_context_calibration() -> None:
    SELECTOR_WRAPPER._LAST_CALIBRATION_LOSS.clear()
    SELECTOR_WRAPPER._LAST_CALIBRATION_LOSS.update({
        "raw_context_total_loss": 1.3,
    })
    row = SELECTOR_WRAPPER._selector_curve_row({
        "calibration_total_loss": 1.1,
    })
    assert row["calibration_metric_unit"] == "instance"
    assert row["calibration_instance_balanced_total_loss"] == pytest.approx(1.1)
    assert row["calibration_raw_context_total_loss"] == pytest.approx(1.3)


def _training_freeze_fixture(tmp_path: Path, *, smoke_passed: bool = True):
    source = tmp_path / "trainer.py"
    source.write_text("version = 1\n", encoding="utf-8")
    upstream = tmp_path / "oracle_freeze.json"
    upstream.write_text(json.dumps({
        "frozen_file_sha256": {
            str(source): hashlib.sha256(source.read_bytes()).hexdigest(),
        },
    }), encoding="utf-8")
    split = tmp_path / "split.json"
    split.write_text(json.dumps({
        "assignments": {"instance": "train"},
    }), encoding="utf-8")
    gate = tmp_path / "gate.json"
    gate.write_text(json.dumps({
        "training_authorized": True,
        "gate": {"passed": True},
    }), encoding="utf-8")
    oracle = tmp_path / "authorized_oracle.json"
    oracle.write_text(json.dumps({
        "initial_rows": [{"state_hash": "s"}],
        "context_rows": [{"state_hash": "s"}],
        "training_permitted": True,
        "oracle_gate": {"passed": True},
        "realmap_v4_training_authority": {
            "gate_report": str(gate),
            "gate_report_sha256": hashlib.sha256(
                gate.read_bytes()
            ).hexdigest(),
            "instance_split": str(split),
            "instance_split_sha256": hashlib.sha256(
                split.read_bytes()
            ).hexdigest(),
        },
    }), encoding="utf-8")
    view = tmp_path / "smoke_view.json"
    view.write_text("{}\n", encoding="utf-8")
    report = tmp_path / "smoke_training_report.json"
    report.write_text("{}\n", encoding="utf-8")
    checkpoint = tmp_path / "smoke_checkpoint.pt"
    checkpoint.write_bytes(b"smoke-checkpoint")
    smoke = tmp_path / "smoke.json"
    smoke.write_text(json.dumps({
        "passed": smoke_passed,
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "source_authorized_oracle_summary": str(oracle),
        "source_authorized_oracle_summary_sha256": hashlib.sha256(
            oracle.read_bytes()
        ).hexdigest(),
        "instance_split": str(split),
        "instance_split_sha256": hashlib.sha256(
            split.read_bytes()
        ).hexdigest(),
        "smoke_oracle_view": str(view),
        "smoke_oracle_view_sha256": hashlib.sha256(
            view.read_bytes()
        ).hexdigest(),
        "ranker_training_report": str(report),
        "ranker_training_report_sha256": hashlib.sha256(
            report.read_bytes()
        ).hexdigest(),
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": hashlib.sha256(
            checkpoint.read_bytes()
        ).hexdigest(),
    }), encoding="utf-8")
    return {
        "source": source,
        "upstream": upstream,
        "split": split,
        "gate": gate,
        "oracle": oracle,
        "smoke": smoke,
        "smoke_checkpoint": checkpoint,
    }


def test_two_stage_training_freeze_binds_oracle_and_sources(
    tmp_path: Path,
) -> None:
    fixture = _training_freeze_fixture(tmp_path)
    freeze = tmp_path / "training_freeze.json"
    payload = create_training_freeze(
        output=freeze,
        oracle_summary=fixture["oracle"],
        oracle_execution_freeze=fixture["upstream"],
        instance_split=fixture["split"],
        training_gate=fixture["gate"],
        source_paths=[fixture["source"]],
        pretraining_smoke_report=fixture["smoke"],
    )
    assert payload["created_after_pretraining_smoke"]
    assert payload["created_before_formal_training"]
    assert validate_training_freeze(freeze)["fallback_action"] == "Q0"
    fixture["source"].write_text("version = 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="training_source_drift"):
        validate_training_freeze(freeze)


def test_two_stage_training_freeze_refuses_preexisting_model_output(
    tmp_path: Path,
) -> None:
    fixture = _training_freeze_fixture(tmp_path)
    existing = tmp_path / "checkpoint.pt"
    existing.write_bytes(b"already-trained")
    with pytest.raises(
        ValueError, match="must precede every formal model output"
    ):
        create_training_freeze(
            output=tmp_path / "freeze.json",
            oracle_summary=fixture["oracle"],
            oracle_execution_freeze=fixture["upstream"],
            instance_split=fixture["split"],
            training_gate=fixture["gate"],
            source_paths=[fixture["source"]],
            forbidden_preexisting_outputs=[existing],
            pretraining_smoke_report=fixture["smoke"],
        )


def test_two_stage_training_freeze_requires_passed_smoke(
    tmp_path: Path,
) -> None:
    fixture = _training_freeze_fixture(tmp_path, smoke_passed=False)
    with pytest.raises(ValueError, match="passed pretraining smoke"):
        create_training_freeze(
            output=tmp_path / "freeze.json",
            oracle_summary=fixture["oracle"],
            oracle_execution_freeze=fixture["upstream"],
            instance_split=fixture["split"],
            training_gate=fixture["gate"],
            source_paths=[fixture["source"]],
            pretraining_smoke_report=fixture["smoke"],
        )


def test_training_freeze_detects_smoke_artifact_drift(tmp_path: Path) -> None:
    fixture = _training_freeze_fixture(tmp_path)
    freeze = tmp_path / "freeze.json"
    create_training_freeze(
        output=freeze,
        oracle_summary=fixture["oracle"],
        oracle_execution_freeze=fixture["upstream"],
        instance_split=fixture["split"],
        training_gate=fixture["gate"],
        source_paths=[fixture["source"]],
        pretraining_smoke_report=fixture["smoke"],
    )
    fixture["smoke_checkpoint"].write_bytes(b"drifted-checkpoint")
    with pytest.raises(
        ValueError, match="pretraining_smoke_or_authority_drift"
    ):
        validate_training_freeze(freeze)


def test_training_freeze_detects_training_gate_drift(tmp_path: Path) -> None:
    fixture = _training_freeze_fixture(tmp_path)
    freeze = tmp_path / "freeze.json"
    create_training_freeze(
        output=freeze,
        oracle_summary=fixture["oracle"],
        oracle_execution_freeze=fixture["upstream"],
        instance_split=fixture["split"],
        training_gate=fixture["gate"],
        source_paths=[fixture["source"]],
        pretraining_smoke_report=fixture["smoke"],
    )
    fixture["gate"].write_text(json.dumps({
        "training_authorized": False,
        "gate": {"passed": False},
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="training_gate_drift"):
        validate_training_freeze(freeze)


def test_pretraining_smoke_subset_is_instance_balanced_and_covered() -> None:
    assignments = {}
    initial_rows = []
    context_rows = []
    for scale in (30, 50):
        for partition in ("train", "calibration", "heldout"):
            for index in range(3):
                instance = f"i_{scale}_{partition}_{index}"
                state = f"s_{scale}_{partition}_{index}"
                assignments[instance] = partition
                initial_rows.append({
                    "state_hash": state,
                    "compliant_context": True,
                })
                context_rows.append({
                    "state_hash": state,
                    "instance_hash": instance,
                    "scale": scale,
                })
    selected = SMOKE._balanced_subset({
        "initial_rows": initial_rows,
        "context_rows": context_rows,
    }, assignments, maximum=2)
    assert len(selected) == 8
    assert len({row["instance_hash"] for row in selected}) == 8
    assert {
        (int(row["scale"]), assignments[row["instance_hash"]])
        for row in selected
    } == {
        (scale, partition)
        for scale in (30, 50)
        for partition in ("train", "calibration")
    }


def test_pretraining_smoke_subset_requires_train_and_calibration_coverage() -> None:
    with pytest.raises(SystemExit, match="lacks train/calibration coverage"):
        SMOKE._balanced_subset({
            "initial_rows": [{
                "state_hash": "s30",
                "compliant_context": True,
            }],
            "context_rows": [{
                "state_hash": "s30",
                "instance_hash": "i30",
                "scale": 30,
            }],
        }, {"i30": "train"}, maximum=2)


def test_instance_balanced_handoff_distinguishes_live_and_missing_pid() -> None:
    assert HANDOFF._pid_state(os.getpid()) is not None
    assert HANDOFF._pid_running(os.getpid())
    assert HANDOFF._pid_state(2**31 - 1) is None
    assert not HANDOFF._pid_running(2**31 - 1)


def test_instance_balanced_handoff_refuses_orphan_replay_by_marker() -> None:
    marker = f"definitely_missing_qg2_replay_{os.getpid()}"
    assert HANDOFF._matching_processes(marker) == []


def test_label_attribution_postprocess_preserves_instance_and_raw_views(
    tmp_path: Path,
) -> None:
    output = tmp_path / "attribution.json"
    output.write_text(json.dumps({
        "baseline_weighted_pair_accuracy": 0.7,
        "group_ablations": [{
            "ablation": "node_to_train_mean",
            "weighted_pair_accuracy": 0.6,
            "accuracy_drop": 0.1,
        }],
        "single_feature_ablations": [{
            "group": "node",
            "feature": "dual",
            "weighted_pair_accuracy": 0.65,
            "accuracy_drop": 0.05,
        }],
    }), encoding="utf-8")
    LABEL_ATTRIBUTION._CALLS[:] = [
        {
            "instance_balanced_accuracy": 0.7,
            "raw_context_accuracy": 0.9,
            "context_count": 4,
            "instance_count": 2,
            "maximum_context_fraction_by_instance": 0.75,
        },
        {
            "instance_balanced_accuracy": 0.6,
            "raw_context_accuracy": 0.8,
            "context_count": 4,
            "instance_count": 2,
            "maximum_context_fraction_by_instance": 0.75,
        },
        {
            "instance_balanced_accuracy": 0.65,
            "raw_context_accuracy": 0.85,
            "context_count": 4,
            "instance_count": 2,
            "maximum_context_fraction_by_instance": 0.75,
        },
    ]
    LABEL_ATTRIBUTION._postprocess(output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["headline_accuracy_unit"] == "instance"
    assert payload["baseline_raw_context_pair_accuracy"] == pytest.approx(0.9)
    assert payload["group_ablations"][0][
        "raw_context_accuracy_drop"
    ] == pytest.approx(0.1)
    diagnostic = payload["single_feature_dominance_diagnostic"]
    assert diagnostic["candidate"]["feature"] == "dual"
    assert diagnostic["candidate"][
        "share_of_all_positive_single_feature_drop"
    ] == pytest.approx(1.0)
    assert diagnostic["candidate"][
        "share_of_positive_group_accuracy_drop"
    ] == pytest.approx(0.5)


def test_selector_attribution_disagreement_is_instance_balanced() -> None:
    baseline = {
        "instance_hashes": ["heavy", "heavy", "heavy", "light"],
        "actions": ["Q0", "Q0", "Q0", "Q0"],
        "mean_instance_arm_rank_accuracy": 0.7,
        "raw_context_arm_rank_accuracy": 0.8,
        "mean_classification_accuracy": 0.7,
        "raw_context_classification_accuracy": 0.8,
    }
    metrics = {
        "instance_hashes": ["heavy", "heavy", "heavy", "light"],
        "actions": ["QD1", "QD1", "QD1", "Q0"],
        "mean_instance_arm_rank_accuracy": 0.6,
        "raw_context_arm_rank_accuracy": 0.7,
        "mean_classification_accuracy": 0.6,
        "raw_context_classification_accuracy": 0.7,
        "net_geomean_ratio": 1.0,
        "raw_context_net_geomean_ratio": 1.0,
        "activated_count": 3,
        "activated_instance_count": 1,
        "harmful_count": 0,
        "harmful_instance_count": 0,
    }
    row = SELECTOR_ATTRIBUTION._instance_balanced_ablation_row(
        "node", metrics, baseline
    )
    assert row["selected_action_disagreement_rate"] == pytest.approx(0.5)
    assert row[
        "raw_context_selected_action_disagreement_rate"
    ] == pytest.approx(0.75)


def test_fresh_summary_geomean_is_instance_balanced() -> None:
    records = [
        {
            "instance_hash": "many_fast",
            "scale": 30,
            "selected_action": "QD1",
            "ratio": 0.5,
            "beneficial": True,
            "harmful": False,
            "safe": True,
        }
        for _ in range(3)
    ] + [{
        "instance_hash": "one_slow",
        "scale": 30,
        "selected_action": "QD1",
        "ratio": 2.0,
        "beneficial": False,
        "harmful": True,
        "safe": True,
    }]
    summary = FRESH._instance_balanced_summary(records)["overall"]
    assert summary["context_weighted_net_geomean_ratio"] == pytest.approx(
        2.0 ** -0.5
    )
    assert summary["net_geomean_ratio"] == pytest.approx(1.0)
    assert summary["instance_count"] == 2
    assert summary["activated_instance_count"] == 2


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            "train_p0v5_qg2_v3_rankers.py",
            "train_p0v5_qg2_v4_instance_balanced_rankers.py",
        ),
        (
            "train_p0v5_qg2_v3_gat_arm_selector.py",
            "train_p0v5_qg2_v4_instance_balanced_arm_selector.py",
        ),
        (
            "run_p0v5_qg2_realmap_v4_controls_after_gat.py",
            "run_p0v5_qg2_realmap_v4_instance_balanced_controls.py",
        ),
        (
            "analyze_p0v5_qg2_v3_gat_attribution.py",
            "analyze_p0v5_qg2_v4_instance_balanced_gat_attribution.py",
        ),
        (
            "analyze_p0v5_qg2_v3_selector_attribution.py",
            "analyze_p0v5_qg2_v4_instance_balanced_selector_attribution.py",
        ),
        (
            "evaluate_p0v5_qg2_v3_gat_selector_fresh.py",
            "evaluate_p0v5_qg2_v4_instance_balanced_selector_fresh.py",
        ),
        (
            "calibrate_p0v5_qg2_v3_gat_force_on.py",
            "calibrate_p0v5_qg2_v4_instance_balanced_gat_force_on.py",
        ),
    ],
)
def test_instance_balanced_pipeline_redirects_every_training_stage(
    source: str, expected: str,
) -> None:
    command = ["python", str(ROOT / "scripts" / source), "--flag"]
    redirected = PIPELINE_WRAPPER._redirect(command)
    assert Path(redirected[1]).name == expected
    assert command[1] != redirected[1]


def test_force_on_bounded_screen_uses_distinct_instances_first() -> None:
    rows = [
        {
            "scale": 30,
            "instance_hash": "heavy",
            "state_hash": f"heavy-{index}",
            "q0_milestone_kind": "proof_completion",
        }
        for index in range(7)
    ] + [
        {
            "scale": 30,
            "instance_hash": f"light-{index}",
            "state_hash": f"light-{index}",
            "q0_milestone_kind": "proof_completion",
        }
        for index in range(5)
    ]
    selected = FORCE_ON._instance_balanced_context_order(
        rows, maximum_per_scale=5
    )
    assert len(selected) == 5
    assert len({row["instance_hash"] for row in selected}) == 5


def test_force_on_full_selection_preserves_context_universe() -> None:
    rows = [
        {
            "scale": scale,
            "instance_hash": f"instance-{scale}-{index % 3}",
            "state_hash": f"state-{scale}-{index}",
            "q0_milestone_kind": "proof_completion",
        }
        for scale in (30, 50)
        for index in range(8)
    ]
    selected = FORCE_ON._instance_balanced_context_order(
        rows, maximum_per_scale=0
    )
    assert {row["state_hash"] for row in selected} == {
        row["state_hash"] for row in rows
    }


def test_force_on_support_requires_multiple_independent_instances() -> None:
    def row(instance, scale, beneficial):
        return {
            "partition": "train",
            "instance_hash": instance,
            "scale": scale,
            "safe": True,
            "action_eligible": True,
            "comparison_class": "matched_milestone",
            "beneficial": beneficial,
        }

    concentrated = {
        "records": [row("heavy", 30, index < 2) for index in range(10)]
    }
    assert not PIPELINE_WRAPPER._instance_balanced_qg2_train_support(
        concentrated
    )
    balanced = {"records": [
        row("a", 30, True),
        row("b", 30, False),
        row("c", 50, True),
        row("d", 50, False),
        row("e", 50, False),
    ]}
    assert PIPELINE_WRAPPER._instance_balanced_qg2_train_support(balanced)
    assert INSTANCE_AUDIT._qg2_support(balanced)


def test_completion_audit_rejects_context_concentrated_force_support() -> None:
    records = [{
        "partition": "train",
        "instance_hash": "one-instance",
        "scale": 30 if index % 2 == 0 else 50,
        "safe": True,
        "action_eligible": True,
        "comparison_class": "matched_milestone",
        "beneficial": index < 4,
    } for index in range(12)]
    assert not INSTANCE_AUDIT._qg2_support({"records": records})


def test_completion_audit_requires_force_selection_authority() -> None:
    report = {
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "selection_experimental_unit": "instance",
        "context_selection_policy": (
            "instance_round_robin_then_frozen_state_order.v1"
        ),
    }
    assert INSTANCE_AUDIT._force_report_is_instance_balanced(report)
    report["selection_experimental_unit"] = "context"
    assert not INSTANCE_AUDIT._force_report_is_instance_balanced(report)


def test_bounded_fitting_gate_keeps_instance_and_class_support() -> None:
    thresholds = TRAINING_AUTHORIZER.FITTING_THRESHOLDS
    assert thresholds == {
        "minimum_determined_contexts_per_scale": 12,
        "minimum_determined_instances_per_scale": 6,
        "minimum_strict_positive_contexts_per_scale": 2,
        "minimum_strict_positive_instances_per_scale": 2,
        "minimum_nonpositive_contexts_per_scale": 4,
        "minimum_harmful_instances_per_scale": 1,
        "harmful_ratio_threshold": 1.05,
        "maximum_instance_saved_wall_fraction": 0.50,
    }
    assert TRAINING_AUTHORIZER.PARTITION_MINIMUMS == {
        "train": {"contexts": 4, "instances": 2},
        "calibration": {"contexts": 2, "instances": 2},
        "heldout": {"contexts": 2, "instances": 2},
    }
    assert TRAINING_AUTHORIZER._validate_gate_freeze()[
        "frozen_before_scale50_oracle_outcomes"
    ]


def test_bounded_fitting_split_requires_both_scales_and_six_instances() -> None:
    rows = []
    assignments = {}
    for scale in (30, 50):
        for index in range(12):
            instance = f"i-{scale}-{index % 6}"
            assignments[instance] = (
                "train" if index % 6 < 2
                else "calibration" if index % 6 < 4
                else "heldout"
            )
            rows.append({
                "scale": scale,
                "instance_hash": instance,
                "outcome_determined": True,
            })
    oracle = {
        "schema_version": TRAINING_AUTHORIZER._load_frozen_authorizer().ORACLE_SCHEMA,
        "initial_rows": [{
            "instance_hash": instance,
            "compliant_context": True,
        } for instance in assignments],
        "context_rows": rows,
    }
    split = {
        "schema_version": TRAINING_AUTHORIZER._load_frozen_authorizer().SPLIT_SCHEMA,
        "frozen_before_matched_outcomes": True,
        "assignments": assignments,
    }
    TRAINING_AUTHORIZER._validate_split(oracle, split)
    oracle["context_rows"] = [
        row for row in rows
        if not (row["scale"] == 50 and row["instance_hash"] == "i-50-5")
    ]
    with pytest.raises(SystemExit, match="scale50 lacks bounded support"):
        TRAINING_AUTHORIZER._validate_split(oracle, split)


def test_context_trainer_qg2_gate_uses_independent_instances() -> None:
    def force_outcome(row):
        return (
            None if not row.get("action_eligible")
            else SimpleNamespace(
                beneficial=bool(row.get("beneficial")),
                harmful=False,
                ratio=0.9 if row.get("beneficial") else 1.0,
            )
        )

    trainer = SimpleNamespace(
        _force_outcome=force_outcome,
        _geomean=lambda values: 1.0,
    )
    concentrated = {
        f"s{index}": {
            "partition": "train",
            "instance_hash": "one",
            "scale": 30 if index % 2 == 0 else 50,
            "safe": True,
            "action_eligible": True,
            "beneficial": index < 3,
        }
        for index in range(10)
    }
    screen = SELECTOR_WRAPPER._instance_balanced_qg2_screen(
        trainer, concentrated
    )
    assert not SELECTOR_WRAPPER._instance_balanced_qg2_arm_is_trainable(
        screen
    )
    balanced = {}
    for index, (instance, scale, beneficial) in enumerate((
        ("a", 30, True), ("b", 30, False),
        ("c", 50, True), ("d", 50, False), ("e", 50, False),
    )):
        balanced[f"b{index}"] = {
            "partition": "train",
            "instance_hash": instance,
            "scale": scale,
            "safe": True,
            "action_eligible": True,
            "beneficial": beneficial,
        }
    screen = SELECTOR_WRAPPER._instance_balanced_qg2_screen(
        trainer, balanced
    )
    assert SELECTOR_WRAPPER._instance_balanced_qg2_arm_is_trainable(screen)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            "train_p0v5_qg2_v3_rankers.py",
            "train_p0v5_qg2_v4_instance_balanced_rankers.py",
        ),
        (
            "train_p0v5_qg2_v3_gat_arm_selector.py",
            "train_p0v5_qg2_v4_instance_balanced_arm_selector.py",
        ),
        (
            "evaluate_p0v5_qg2_v3_gat_selector_fresh.py",
            "evaluate_p0v5_qg2_v4_instance_balanced_selector_fresh.py",
        ),
    ],
)
def test_instance_balanced_controls_redirect_mlp_and_linear_trainers(
    source: str, expected: str,
) -> None:
    redirected = CONTROLS_WRAPPER._redirect([
        "python", str(ROOT / "scripts" / source), "--models", "mlp,linear",
    ])
    assert Path(redirected[1]).name == expected


def test_instance_balanced_controls_require_policy_and_checkpoint_metric(
    tmp_path: Path,
) -> None:
    report = tmp_path / "training_report.json"
    report.write_text(json.dumps({
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "checkpoint_selection_metric": "mean_instance_pair_accuracy",
    }), encoding="utf-8")
    assert CONTROLS_WRAPPER._validated_report(
        report, checkpoint_metric="mean_instance_pair_accuracy"
    )["instance_balancing_policy"] == INSTANCE_BALANCING_POLICY_V1
    with pytest.raises(SystemExit, match="model report invalid"):
        CONTROLS_WRAPPER._validated_report(
            report, checkpoint_metric="instance_balanced_total_loss"
        )


def test_instance_balanced_controls_require_safe_instance_fresh_report(
    tmp_path: Path,
) -> None:
    report = tmp_path / "fresh.json"
    report.write_text(json.dumps({
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "summary_experimental_unit": "instance",
        "summary": {"overall": {"all_safe": True}},
    }), encoding="utf-8")
    assert CONTROLS_WRAPPER._validated_fresh(report)[
        "summary_experimental_unit"
    ] == "instance"
    report.write_text(json.dumps({
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "summary_experimental_unit": "instance",
        "summary": {"overall": {"all_safe": False}},
    }), encoding="utf-8")
    with pytest.raises(SystemExit, match="fresh report invalid"):
        CONTROLS_WRAPPER._validated_fresh(report)


def test_final_candidate_binds_all_instance_balanced_model_reports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(PIPELINE_WRAPPER, "ROOT", tmp_path)
    monkeypatch.setattr(PIPELINE_WRAPPER, "RUN", tmp_path)
    monkeypatch.setattr(
        PIPELINE_WRAPPER, "validate_training_freeze", lambda _path: {}
    )
    upstream = tmp_path / "upstream_candidate.json"
    upstream.write_text("{}\n", encoding="utf-8")
    training_freeze = tmp_path / "training_freeze.json"
    training_freeze.write_text("{}\n", encoding="utf-8")
    comparison = tmp_path / "gat_mlp_linear_comparison_v4.json"
    comparison.write_text("{}\n", encoding="utf-8")
    final = tmp_path / "final_candidate.json"
    addendum = tmp_path / "comparison_addendum.json"
    audit = tmp_path / "instance_balanced_completion_audit.json"
    monkeypatch.setattr(PIPELINE_WRAPPER, "UPSTREAM_CANDIDATE", upstream)
    monkeypatch.setattr(PIPELINE_WRAPPER, "TRAINING_FREEZE", training_freeze)
    monkeypatch.setattr(PIPELINE_WRAPPER, "UPSTREAM_COMPARISON", comparison)
    monkeypatch.setattr(PIPELINE_WRAPPER, "COMPARISON_ADDENDUM", addendum)
    monkeypatch.setattr(PIPELINE_WRAPPER, "INSTANCE_BALANCED_AUDIT", audit)
    monkeypatch.setattr(PIPELINE_WRAPPER, "FINAL_CANDIDATE", final)
    report_paths = (
        tmp_path / "ranker_gat_v4/training_report.json",
        tmp_path / "selector_gat_v4/training_report.json",
        tmp_path / "ranker_controls_v4/training_report.json",
        tmp_path / "selector_mlp_control_v4/training_report.json",
        tmp_path / "selector_linear_control_v4/training_report.json",
    )
    for path in report_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        }), encoding="utf-8")
    attribution_paths = (
        tmp_path / "ranker_gat_v4_attribution.json",
        tmp_path / "selector_gat_v4_attribution.json",
    )
    for path in attribution_paths:
        path.write_text(json.dumps({
            "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        }), encoding="utf-8")
    fresh_paths = {
        f"fresh_{kind}_{partition}": (
            tmp_path / f"selector_{kind}_fresh_{partition}_v4"
            / f"fresh_{partition}.json"
        )
        for kind in ("gat", "mlp", "linear")
        for partition in ("calibration", "heldout")
    }
    for path in fresh_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
            "summary_experimental_unit": "instance",
        }), encoding="utf-8")
    addendum.write_text(json.dumps({
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "deployable": False,
        "production_switch_authorized": False,
        "artifact_sha256": {
            "label_gat": PIPELINE_WRAPPER.sha256(report_paths[0]),
            "context_gat": PIPELINE_WRAPPER.sha256(report_paths[1]),
            "label_controls": PIPELINE_WRAPPER.sha256(report_paths[2]),
            "context_mlp": PIPELINE_WRAPPER.sha256(report_paths[3]),
            "context_linear": PIPELINE_WRAPPER.sha256(report_paths[4]),
            "upstream_comparison": PIPELINE_WRAPPER.sha256(comparison),
            "training_freeze": PIPELINE_WRAPPER.sha256(training_freeze),
            **{
                key: PIPELINE_WRAPPER.sha256(path)
                for key, path in fresh_paths.items()
            },
        },
    }), encoding="utf-8")
    audit.write_text(json.dumps({
        "passed": True,
        "error_count": 0,
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "audited_artifact_sha256": {
            "training_freeze.json": PIPELINE_WRAPPER.sha256(training_freeze),
        },
    }), encoding="utf-8")
    PIPELINE_WRAPPER._freeze_instance_balanced_candidate()
    payload = json.loads(final.read_text(encoding="utf-8"))
    assert len(payload["training_report_sha256"]) == 5
    assert len(payload["attribution_sha256"]) == 2
    assert len(payload["fresh_report_sha256"]) == 6
    assert payload["comparison_addendum_sha256"] == (
        PIPELINE_WRAPPER.sha256(addendum)
    )
    assert payload["instance_balanced_completion_audit_sha256"] == (
        PIPELINE_WRAPPER.sha256(audit)
    )


def test_final_candidate_rejects_instance_audit_artifact_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(PIPELINE_WRAPPER, "ROOT", tmp_path)
    audit = tmp_path / "audit.json"
    source = tmp_path / "source.txt"
    source.write_text("before", encoding="utf-8")
    audit.write_text(json.dumps({
        "passed": True,
        "error_count": 0,
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "audited_artifact_sha256": {
            "source.txt": PIPELINE_WRAPPER.sha256(source),
        },
    }), encoding="utf-8")
    monkeypatch.setattr(PIPELINE_WRAPPER, "INSTANCE_BALANCED_AUDIT", audit)
    source.write_text("after", encoding="utf-8")
    with pytest.raises(SystemExit, match="audited artifact drift"):
        PIPELINE_WRAPPER._validate_instance_balanced_completion_audit()
