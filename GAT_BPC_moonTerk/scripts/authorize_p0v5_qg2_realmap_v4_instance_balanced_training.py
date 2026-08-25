#!/usr/bin/env python3
"""Issue a bounded instance-supported fitting authority for V4 real-map GAT.

This wrapper is frozen before any scale50 Oracle outcome.  It relaxes only the
amount of class support required to fit a model; fresh-process and E2E gates
remain unchanged and retain all deployment authority.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.instance_balanced_learning import (  # noqa: E402
    INSTANCE_BALANCING_POLICY_V1,
)


FROZEN_AUTHORIZER = ROOT / "scripts/authorize_p0v5_qg2_realmap_v4_training.py"
GATE_FREEZE = (
    ROOT
    / "runs/p0v5_qg2_v4_realmap_gat_first_20260806/"
    "realmap_v4_instance_balanced_fitting_gate_freeze.json"
)
ORACLE_EXECUTION_FREEZE = (
    ROOT
    / "runs/p0v5_qg2_v4_realmap_gat_first_20260806/"
    "realmap_v4_oracle_execution_freeze.json"
)
GATE_PROFILE = "bounded_instance_supported_fitting_only.v2"
FITTING_THRESHOLDS = {
    "minimum_determined_contexts_per_scale": 12,
    "minimum_determined_instances_per_scale": 6,
    "minimum_strict_positive_contexts_per_scale": 2,
    "minimum_strict_positive_instances_per_scale": 2,
    "minimum_nonpositive_contexts_per_scale": 4,
    "minimum_harmful_instances_per_scale": 1,
    "harmful_ratio_threshold": 1.05,
    "maximum_instance_saved_wall_fraction": 0.50,
}
PARTITION_MINIMUMS = {
    "train": {"contexts": 4, "instances": 2},
    "calibration": {"contexts": 2, "instances": 2},
    "heldout": {"contexts": 2, "instances": 2},
}


def main() -> int:
    _validate_gate_freeze()
    module = _load_frozen_authorizer()
    module.V4_THRESHOLDS = dict(FITTING_THRESHOLDS)
    module._validate_split = _validate_split
    returncode = int(module.main())
    gate_path = _argument_path("--gate-output")
    view_path = _argument_path("--authorized-oracle-output")
    if gate_path.is_file():
        gate = _load(gate_path)
        gate.update({
            "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
            "fitting_gate_profile": GATE_PROFILE,
            "thresholds_frozen_before_scale50_oracle_outcomes": True,
            "deployment_authority_unchanged": True,
        })
        _write(gate_path, gate)
    if view_path.is_file():
        view = _load(view_path)
        authority = dict(view.get("realmap_v4_training_authority") or {})
        authority.update({
            "gate_report_sha256": _sha256(gate_path),
            "fitting_gate_profile": GATE_PROFILE,
            "deployment_authority_unchanged": True,
        })
        view.update({
            "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
            "fitting_gate_profile": GATE_PROFILE,
            "realmap_v4_training_authority": authority,
        })
        _write(view_path, view)
    return returncode


def _validate_gate_freeze() -> dict:
    payload = _load(GATE_FREEZE)
    expected_sources = {
        str(Path(__file__).resolve()): _sha256(Path(__file__).resolve()),
        str(FROZEN_AUTHORIZER.resolve()): _sha256(FROZEN_AUTHORIZER),
    }
    if (
        str(payload.get("schema_version") or "")
        != "lunar_ice_bpc.p0v5_qg2_v4_fitting_gate_freeze.v1"
        or str(payload.get("fitting_gate_profile") or "") != GATE_PROFILE
        or dict(payload.get("thresholds") or {}) != FITTING_THRESHOLDS
        or dict(payload.get("partition_minimums") or {})
        != PARTITION_MINIMUMS
        or not bool(payload.get("frozen_before_scale50_oracle_outcomes"))
        or int(payload.get("observed_scale50_context_directories") or 0) != 0
        or str(payload.get("oracle_execution_freeze_sha256") or "")
        != _sha256(ORACLE_EXECUTION_FREEZE)
        or dict(payload.get("source_sha256") or {}) != expected_sources
    ):
        raise SystemExit("instance-balanced fitting gate freeze drift")
    return payload


def _validate_split(oracle: dict, split: dict) -> None:
    module = _load_frozen_authorizer()
    if oracle.get("schema_version") != module.ORACLE_SCHEMA:
        raise SystemExit("instance-balanced fitting Oracle schema mismatch")
    if split.get("schema_version") != module.SPLIT_SCHEMA or not bool(
        split.get("frozen_before_matched_outcomes")
    ):
        raise SystemExit("instance-balanced fitting split is not frozen")
    assignments = {
        str(key): str(value)
        for key, value in dict(split.get("assignments") or {}).items()
    }
    oracle_instances = {
        str(row.get("instance_hash") or "")
        for row in oracle.get("initial_rows") or ()
        if row.get("compliant_context")
    }
    if not oracle_instances or not oracle_instances.issubset(assignments):
        raise SystemExit("instance-balanced fitting instances are not split-bound")
    if any(
        assignments[value] not in {"train", "calibration", "heldout"}
        for value in oracle_instances
    ):
        raise SystemExit("instance-balanced fitting partition drift")
    for scale in (30, 50):
        rows = [
            row for row in oracle.get("context_rows") or ()
            if int(row.get("scale") or 0) == scale
            and bool(row.get("outcome_determined"))
        ]
        instances = {str(row.get("instance_hash") or "") for row in rows}
        if (
            len(rows)
            < FITTING_THRESHOLDS["minimum_determined_contexts_per_scale"]
            or len(instances)
            < FITTING_THRESHOLDS["minimum_determined_instances_per_scale"]
        ):
            raise SystemExit(
                f"instance-balanced fitting scale{scale} lacks bounded support"
            )
        scale_rows = [
            row for row in oracle.get("context_rows") or ()
            if int(row.get("scale") or 0) == scale
        ]
        for partition, minimum in PARTITION_MINIMUMS.items():
            partition_rows = [
                row for row in scale_rows
                if assignments.get(str(row.get("instance_hash") or ""))
                == partition
            ]
            partition_instances = {
                str(row.get("instance_hash") or "")
                for row in partition_rows
            }
            if (
                len(partition_rows) < int(minimum["contexts"])
                or len(partition_instances) < int(minimum["instances"])
            ):
                raise SystemExit(
                    "instance-balanced fitting "
                    f"scale{scale} {partition} partition support missing"
                )


def _load_frozen_authorizer():
    spec = importlib.util.spec_from_file_location(
        "p0v5_qg2_v4_frozen_training_authorizer", FROZEN_AUTHORIZER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen real-map training authorizer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _argument_path(flag: str) -> Path:
    try:
        value = sys.argv[sys.argv.index(flag) + 1]
    except (ValueError, IndexError) as exc:
        raise SystemExit(f"missing required argument {flag}") from exc
    path = Path(value).expanduser()
    return path if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
