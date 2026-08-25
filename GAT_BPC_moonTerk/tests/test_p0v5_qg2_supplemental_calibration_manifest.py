from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_p0v5_qg2_supplemental_calibration_manifest.py"
SPEC = importlib.util.spec_from_file_location("qg2_supplement", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _row(partition: str, scale: int, index: int, instance: int | None = None):
    return {
        "partition": partition,
        "scale": scale,
        "instance_hash": f"i{scale}_{instance if instance is not None else index}",
        "state_hash": f"s{scale}_{index}",
        "preaction_stratum": "root:plain:r30_plus:missing",
    }


def test_stable_partition_is_deterministic_and_instance_scoped() -> None:
    first = MODULE._stable_partition(scale=30, instance_hash="abc")
    assert first in MODULE.PARTITIONS
    assert first == MODULE._stable_partition(scale=30, instance_hash="abc")
    assert MODULE._stable_partition(scale=50, instance_hash="abc") == (
        MODULE._stable_partition(scale=50, instance_hash="abc")
    )


def test_supplement_fills_per_scale_and_total_without_training_rows() -> None:
    base = [
        _row("calibration", 30, index) for index in range(2)
    ] + [
        _row("calibration", 50, 100 + index) for index in range(2)
    ]
    candidates = []
    for scale in (30, 50):
        candidates.extend(
            _row("calibration", scale, scale * 100 + index, index % 8)
            for index in range(30)
        )
        candidates.extend(
            _row("heldout", scale, scale * 1000 + index, index % 5)
            for index in range(12)
        )

    selected = MODULE._select_supplement(
        base_rows=base,
        candidates=candidates,
        minimum_calibration=52,
        minimum_calibration_per_scale=20,
        minimum_heldout_per_scale=10,
    )
    combined = base + selected
    counts = MODULE._counts(combined)

    assert counts["calibration_context_count"] == 52
    assert counts["scale30_calibration_context_count"] >= 20
    assert counts["scale50_calibration_context_count"] >= 20
    assert counts["scale30_heldout_context_count"] == 10
    assert counts["scale50_heldout_context_count"] == 10
    assert all(row["partition"] != "train" for row in selected)
    assert len({row["state_hash"] for row in selected}) == len(selected)


def test_round_robin_does_not_exhaust_one_instance_first() -> None:
    rows = [
        _row("calibration", 30, 1, 1),
        _row("calibration", 30, 2, 1),
        _row("calibration", 30, 3, 2),
    ]
    ordered = MODULE._round_robin_instances(rows)
    assert ordered[0]["instance_hash"] != ordered[1]["instance_hash"]


def test_build_manifest_preserves_split_and_never_adds_training_rows(
    tmp_path: Path,
) -> None:
    def write(path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload), encoding="utf-8")

    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    instance = tmp_path / "instance.json"
    snapshot = tmp_path / "snapshot.json"
    write(instance, {})
    write(snapshot, {})
    rows = []
    assignments = {"base30": "calibration"}
    for scale in (30, 50):
        for partition in ("calibration", "heldout", "train"):
            instance_hash = f"{partition}{scale}"
            assignments[instance_hash] = partition
            rows.append({
                "scale": scale,
                "instance_content_hash": instance_hash,
                "state_hash": f"state-{partition}-{scale}",
                "instance_path": str(instance),
                "snapshot_path": str(snapshot),
                "source_backend_id": "backend",
                "source_engine_hash": "engine",
                "source_config_hash": "config",
                "source_exact_action_policy_hash": "policy",
            })
    index_path = tmp_path / "index.json"
    write(index_path, {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_fallback_snapshot_index.v2"
        ),
        "rows": rows,
    })
    split_path = tmp_path / "split.json"
    write(split_path, {
        "schema_version": MODULE.SPLIT_SCHEMA,
        "assignments": assignments,
    })
    oracle_path = tmp_path / "oracle.json"
    write(oracle_path, {
        "schema_version": MODULE.ORACLE_SCHEMA,
        "development_only": True,
        "deployable": False,
        "oracle_gate": {"passed": True},
        "source_state_index_sha256": sha(index_path),
        "initial_rows": [{
            "compliant_context": True,
            "source_backend_id": "backend",
            "source_engine_hash": "engine",
            "source_exact_action_policy_hash": "policy",
        }],
        "context_rows": [{
            "scale": 30,
            "instance_hash": "base30",
            "state_hash": "base-state",
        }],
    })
    training_path = tmp_path / "training.json"
    write(training_path, {
        "schema_version": MODULE.TRAINING_SCHEMA,
        "development_only": True,
        "deployable": False,
        "oracle_gate_passed": True,
        "oracle_summary_sha256": sha(oracle_path),
        "split_path": str(split_path),
        "split_sha256": sha(split_path),
    })

    manifest = MODULE.build_manifest(
        training_path=training_path,
        oracle_path=oracle_path,
        state_index_path=index_path,
        minimum_calibration=3,
        minimum_calibration_per_scale=1,
        minimum_heldout_per_scale=1,
    )

    assert manifest["sufficient"]
    assert manifest["training_rows_added"] == 0
    assert all(row["partition"] != "train" for row in manifest["rows"])
    assert {
        (row["scale"], row["partition"]) for row in manifest["rows"]
    } >= {
        (30, "calibration"),
        (50, "calibration"),
        (30, "heldout"),
        (50, "heldout"),
    }
