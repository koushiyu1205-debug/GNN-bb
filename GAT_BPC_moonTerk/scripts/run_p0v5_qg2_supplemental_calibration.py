#!/usr/bin/env python3
"""Run QG2 calibration over a leakage-safe supplemental evaluation view.

The frozen trainer remains bound to its original Oracle summary and instance
split.  This runner creates explicit calibration-only views that extend only
the calibration/heldout partitions with rows selected by the supplemental
manifest.  Checkpoints, training data, train-instance assignments, and the
feature envelope are unchanged.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CALIBRATOR = ROOT / "scripts/calibrate_p0v5_qg2_models.py"
TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
SPLIT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_instance_split.v1"
SUPPLEMENT_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_supplemental_calibration_manifest.v1"
)
CALIBRATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
BINDING_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_supplemental_calibration_binding.v1"
)
GUIDANCE_ENV_KEYS = (
    "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
    "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
    "LUNAR_ICE_PROOF_QUEUE_GAT_MANIFEST",
    "LUNAR_ICE_PROOF_QUEUE_GAT_EVALUATION_MODE",
    "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT_MANIFEST",
    "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT_EVALUATION_MODE",
    "LUNAR_ICE_GAT_DEPLOYMENT_MANIFEST",
    "LUNAR_ICE_GAT_GUIDANCE_MODE",
    "LUNAR_ICE_GAT_TRAINING_ROWS_DIR",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-report", required=True)
    parser.add_argument("--oracle-summary", required=True)
    parser.add_argument("--supplemental-manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--scale30-wall-sec", type=float, default=180.0)
    parser.add_argument("--scale50-wall-sec", type=float, default=300.0)
    parser.add_argument("--memory-limit-gb", type=float, default=10.867)
    parser.add_argument("--allowed-engine-hash", action="append", default=[])
    parser.add_argument(
        "--allowed-exact-action-policy-hash", action="append", default=[]
    )
    parser.add_argument(
        "--native-build-dir",
        default="build/native-spprc-bidirectional-feasibility-v1",
    )
    args = parser.parse_args()

    training_path = _resolve(args.training_report)
    oracle_path = _resolve(args.oracle_summary)
    supplement_path = _resolve(args.supplemental_manifest)
    output_dir = _resolve(args.output_dir)
    output_path = _resolve(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    views = _materialize_views(
        training_path=training_path,
        oracle_path=oracle_path,
        supplement_path=supplement_path,
        output_dir=output_dir / "authorized_views",
    )
    command = [
        sys.executable,
        str(CALIBRATOR),
        "--training-report", str(views["training_view"]),
        "--oracle-summary", str(views["oracle_view"]),
        "--output-dir", str(output_dir),
        "--output", str(output_path),
        "--repeats", str(max(3, int(args.repeats))),
        "--scale30-wall-sec", str(float(args.scale30_wall_sec)),
        "--scale50-wall-sec", str(float(args.scale50_wall_sec)),
        "--memory-limit-gb", str(float(args.memory_limit_gb)),
        "--native-build-dir", str(_resolve(args.native_build_dir)),
    ]
    for digest in args.allowed_engine_hash:
        command.extend(("--allowed-engine-hash", str(digest)))
    for digest in args.allowed_exact_action_policy_hash:
        command.extend(("--allowed-exact-action-policy-hash", str(digest)))
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=_clean_environment(args.native_build_dir),
        check=False,
    )
    if not output_path.is_file():
        raise SystemExit(
            "supplemental QG2 calibrator did not emit its declared report"
        )
    report = _load(output_path)
    if report.get("schema_version") != CALIBRATION_SCHEMA:
        raise SystemExit("supplemental QG2 calibration schema mismatch")
    binding = {
        "schema_version": BINDING_SCHEMA,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "development_only": True,
        "deployable": bool(report.get("deployment_authorized")),
        "training_rows_added": 0,
        "training_report": str(training_path),
        "training_report_sha256": _sha256(training_path),
        "oracle_summary": str(oracle_path),
        "oracle_summary_sha256": _sha256(oracle_path),
        "supplemental_manifest": str(supplement_path),
        "supplemental_manifest_sha256": _sha256(supplement_path),
        "training_view": str(views["training_view"]),
        "training_view_sha256": _sha256(views["training_view"]),
        "oracle_view": str(views["oracle_view"]),
        "oracle_view_sha256": _sha256(views["oracle_view"]),
        "split_view": str(views["split_view"]),
        "split_view_sha256": _sha256(views["split_view"]),
        "calibrator": str(CALIBRATOR),
        "calibrator_sha256": _sha256(CALIBRATOR),
        "calibration_report": str(output_path),
        "calibration_report_sha256": _sha256(output_path),
        "calibrator_returncode": int(completed.returncode),
        "gate_pass": bool(report.get("gate_pass")),
        "deployment_authorized": bool(report.get("deployment_authorized")),
        "status": (
            "SUPPLEMENTAL_CALIBRATION_PASSED"
            if report.get("gate_pass")
            else "SUPPLEMENTAL_CALIBRATION_GATE_FAILED"
        ),
    }
    _write(output_dir / "supplemental_calibration_binding.json", binding)
    return 0 if binding["gate_pass"] else 2


def _materialize_views(
    *,
    training_path: Path,
    oracle_path: Path,
    supplement_path: Path,
    output_dir: Path,
) -> dict[str, Path]:
    training = _load(training_path)
    oracle = _load(oracle_path)
    supplement = _load(supplement_path)
    errors = []
    if training.get("schema_version") != TRAINING_SCHEMA:
        errors.append("training_schema_mismatch")
    if oracle.get("schema_version") != ORACLE_SCHEMA:
        errors.append("oracle_schema_mismatch")
    if supplement.get("schema_version") != SUPPLEMENT_SCHEMA:
        errors.append("supplement_schema_mismatch")
    if not bool(training.get("oracle_gate_passed")):
        errors.append("training_not_oracle_authorized")
    if not bool((oracle.get("oracle_gate") or {}).get("passed")):
        errors.append("oracle_gate_not_passed")
    if not bool(supplement.get("sufficient")):
        errors.append("supplement_not_sufficient")
    if int(supplement.get("training_rows_added") or 0) != 0:
        errors.append("supplement_training_leak")
    if str(supplement.get("training_report_sha256") or "") != _sha256(
        training_path
    ):
        errors.append("supplement_training_hash_mismatch")
    if str(supplement.get("oracle_summary_sha256") or "") != _sha256(
        oracle_path
    ):
        errors.append("supplement_oracle_hash_mismatch")
    if str(training.get("oracle_summary_sha256") or "") != _sha256(
        oracle_path
    ):
        errors.append("training_oracle_hash_mismatch")
    split_path = _resolve(training.get("split_path") or "")
    if not split_path.is_file():
        errors.append("split_missing")
        split = {}
    else:
        split = _load(split_path)
        if split.get("schema_version") != SPLIT_SCHEMA:
            errors.append("split_schema_mismatch")
        if str(training.get("split_sha256") or "") != _sha256(split_path):
            errors.append("training_split_hash_mismatch")
        if str(supplement.get("split_sha256") or "") != _sha256(split_path):
            errors.append("supplement_split_hash_mismatch")
    rows = [dict(row) for row in supplement.get("rows") or ()]
    if not rows:
        errors.append("supplement_rows_missing")
    if any(row.get("partition") not in {"calibration", "heldout"} for row in rows):
        errors.append("supplement_partition_leak")
    states = [str(row.get("state_hash") or "") for row in rows]
    if any(not state for state in states) or len(states) != len(set(states)):
        errors.append("supplement_state_identity_invalid")
    original_states = {
        str(row.get("state_hash") or "")
        for row in oracle.get("context_rows") or ()
    }
    if original_states.intersection(states):
        errors.append("supplement_state_overlap")
    assignments = {
        str(key): str(value)
        for key, value in dict(split.get("assignments") or {}).items()
    }
    for row in rows:
        instance = str(row.get("instance_hash") or "")
        partition = str(row.get("partition") or "")
        if not instance:
            errors.append("supplement_instance_identity_missing")
            continue
        frozen = assignments.get(instance)
        if frozen is not None and frozen != partition:
            errors.append("supplement_instance_partition_conflict")
        assignments[instance] = partition
        for key in (
            "instance_path", "snapshot_path", "source_backend_id",
            "source_engine_hash", "source_config_hash",
            "source_exact_action_policy_hash",
        ):
            if not str(row.get(key) or ""):
                errors.append(f"supplement_binding_missing:{key}")
    if errors:
        raise ValueError(
            "supplemental calibration view contract failed: "
            + ",".join(sorted(set(errors)))
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    split_view = output_dir / "instance_split_calibration_view.json"
    split_payload = {
        **split,
        "assignments": assignments,
        "calibration_view_only": True,
        "training_assignments_unchanged": True,
        "source_split": str(split_path),
        "source_split_sha256": _sha256(split_path),
        "supplemental_manifest_sha256": _sha256(supplement_path),
    }
    _write(split_view, split_payload)

    supplemental_initial = []
    supplemental_contexts = []
    for row in rows:
        identity = {
            key: row[key]
            for key in (
                "scale", "instance_hash", "state_hash", "instance_path",
                "snapshot_path", "source_backend_id", "source_engine_hash",
                "source_config_hash", "source_exact_action_policy_hash",
            )
        }
        supplemental_initial.append({
            **identity,
            "compliant_context": True,
            "calibration_view_only": True,
            "oracle_arm_evidence_available": False,
        })
        supplemental_contexts.append({
            **identity,
            "partition": row["partition"],
            "calibration_view_only": True,
            "outcome_determined": False,
            "oracle_arm_evidence_available": False,
        })
    oracle_view = output_dir / "oracle_calibration_view.json"
    oracle_payload = {
        **oracle,
        "initial_rows": [
            *list(oracle.get("initial_rows") or ()),
            *supplemental_initial,
        ],
        "context_rows": [
            *list(oracle.get("context_rows") or ()),
            *supplemental_contexts,
        ],
        "calibration_view_only": True,
        "training_authority": False,
        "training_rows_added": 0,
        "source_oracle_summary": str(oracle_path),
        "source_oracle_summary_sha256": _sha256(oracle_path),
        "supplemental_manifest": str(supplement_path),
        "supplemental_manifest_sha256": _sha256(supplement_path),
    }
    _write(oracle_view, oracle_payload)

    training_view = output_dir / "training_calibration_view.json"
    training_payload = {
        **training,
        "split_path": str(split_view),
        "split_sha256": _sha256(split_view),
        "oracle_summary": str(oracle_view),
        "oracle_summary_sha256": _sha256(oracle_view),
        "calibration_view_only": True,
        "training_rows_added": 0,
        "source_training_report": str(training_path),
        "source_training_report_sha256": _sha256(training_path),
        "source_oracle_summary": str(oracle_path),
        "source_oracle_summary_sha256": _sha256(oracle_path),
        "supplemental_manifest_sha256": _sha256(supplement_path),
    }
    _write(training_view, training_payload)
    return {
        "split_view": split_view,
        "oracle_view": oracle_view,
        "training_view": training_view,
    }


def _clean_environment(native_build_dir: str) -> dict[str, str]:
    env = dict(os.environ)
    for key in GUIDANCE_ENV_KEYS:
        env.pop(key, None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{_resolve(native_build_dir)}"
    return env


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
