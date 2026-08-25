from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_p0v5_qg2_supplemental_calibration.py"
SPEC = importlib.util.spec_from_file_location("qg2_supplement_runner", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sources(tmp_path: Path):
    split = tmp_path / "split.json"
    _write(split, {
        "schema_version": MODULE.SPLIT_SCHEMA,
        "assignments": {"train": "train", "cal": "calibration"},
    })
    oracle = tmp_path / "oracle.json"
    _write(oracle, {
        "schema_version": MODULE.ORACLE_SCHEMA,
        "development_only": True,
        "deployable": False,
        "oracle_gate": {"passed": True},
        "initial_rows": [],
        "context_rows": [{
            "scale": 30,
            "instance_hash": "cal",
            "state_hash": "base",
        }],
    })
    training = tmp_path / "training.json"
    _write(training, {
        "schema_version": MODULE.TRAINING_SCHEMA,
        "development_only": True,
        "deployable": False,
        "oracle_gate_passed": True,
        "oracle_summary": str(oracle),
        "oracle_summary_sha256": _sha(oracle),
        "split_path": str(split),
        "split_sha256": _sha(split),
    })
    supplement = tmp_path / "supplement.json"
    _write(supplement, {
        "schema_version": MODULE.SUPPLEMENT_SCHEMA,
        "development_only": True,
        "deployable": False,
        "sufficient": True,
        "training_rows_added": 0,
        "training_report_sha256": _sha(training),
        "oracle_summary_sha256": _sha(oracle),
        "split_sha256": _sha(split),
        "rows": [{
            "scale": 50,
            "instance_hash": "new-cal",
            "state_hash": "supplemental-state",
            "partition": "calibration",
            "instance_path": "/tmp/instance.json",
            "snapshot_path": "/tmp/snapshot.json",
            "source_backend_id": "backend",
            "source_engine_hash": "engine",
            "source_config_hash": "config",
            "source_exact_action_policy_hash": "policy",
        }],
    })
    return training, oracle, split, supplement


def test_materialized_views_extend_only_evaluation_partitions(
    tmp_path: Path,
) -> None:
    training, oracle, _split, supplement = _sources(tmp_path)
    views = MODULE._materialize_views(
        training_path=training,
        oracle_path=oracle,
        supplement_path=supplement,
        output_dir=tmp_path / "views",
    )
    training_view = json.loads(views["training_view"].read_text())
    oracle_view = json.loads(views["oracle_view"].read_text())
    split_view = json.loads(views["split_view"].read_text())

    assert training_view["training_rows_added"] == 0
    assert training_view["source_training_report_sha256"] == _sha(training)
    assert split_view["assignments"]["train"] == "train"
    assert split_view["assignments"]["new-cal"] == "calibration"
    assert len(oracle_view["context_rows"]) == 2
    assert oracle_view["context_rows"][-1]["calibration_view_only"]
    assert oracle_view["context_rows"][-1]["outcome_determined"] is False


def test_materialized_views_fail_closed_on_partition_conflict(
    tmp_path: Path,
) -> None:
    training, oracle, _split, supplement = _sources(tmp_path)
    payload = json.loads(supplement.read_text())
    payload["rows"][0]["instance_hash"] = "train"
    _write(supplement, payload)

    with pytest.raises(ValueError, match="partition_conflict"):
        MODULE._materialize_views(
            training_path=training,
            oracle_path=oracle,
            supplement_path=supplement,
            output_dir=tmp_path / "views",
        )
