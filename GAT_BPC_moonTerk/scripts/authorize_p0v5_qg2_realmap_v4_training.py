#!/usr/bin/env python3
"""Issue training-only authority for the real-map V4 GAT-first corpus.

The strict leaked-QO2 Oracle remains intact and is reported as mechanism
evidence.  It is not a deployment gate for a selective model.  This script
allows fitting only when the bounded corpus is exact-safe, instance-isolated,
and contains useful positive and adverse class support at both scales.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
SPLIT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_realmap_v4_instance_split.v1"
GATE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_realmap_v4_training_gate.v1"
VIEW_SCHEMA = ORACLE_SCHEMA
V4_THRESHOLDS = {
    "minimum_determined_contexts_per_scale": 20,
    "minimum_determined_instances_per_scale": 10,
    "minimum_strict_positive_contexts_per_scale": 3,
    "minimum_strict_positive_instances_per_scale": 3,
    "minimum_nonpositive_contexts_per_scale": 5,
    "minimum_harmful_instances_per_scale": 2,
    "harmful_ratio_threshold": 1.05,
    "maximum_instance_saved_wall_fraction": 0.35,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-summary", required=True)
    parser.add_argument("--instance-split", required=True)
    parser.add_argument("--gate-output", required=True)
    parser.add_argument("--authorized-oracle-output", required=True)
    args = parser.parse_args()

    oracle_path = _resolve(args.oracle_summary)
    split_path = _resolve(args.instance_split)
    gate_path = _resolve(args.gate_output)
    view_path = _resolve(args.authorized_oracle_output)
    if gate_path.exists() or view_path.exists():
        raise SystemExit("real-map V4 training authority refuses overwrite")
    oracle = _load(oracle_path)
    split = _load(split_path)
    _validate_split(oracle, split)

    helper = _training_gate_helpers()
    assessment = _evaluate_v4_training_gate(oracle, helper=helper)
    training_authorized = bool(assessment.get("training_authorized"))
    gate = {
        "schema_version": GATE_SCHEMA,
        "development_only": True,
        "deployable": False,
        "authority": "realmap_v4_exploratory_gat_fitting_only",
        "strict_oracle_performance_gate_is_report_only": True,
        "deployment_authorized": False,
        "paper_claim_authorized": False,
        "oracle_summary": str(oracle_path),
        "oracle_summary_sha256": _sha256(oracle_path),
        "instance_split": str(split_path),
        "instance_split_sha256": _sha256(split_path),
        "formal_benchmark_instances_used": False,
        **assessment,
    }
    _write(gate_path, gate)
    if not training_authorized:
        print(json.dumps(gate["gate"], sort_keys=True), flush=True)
        return 2

    authorized = dict(oracle)
    authorized["strict_oracle_gate"] = dict(oracle.get("oracle_gate") or {})
    authorized["oracle_gate"] = dict(gate["gate"])
    authorized["training_permitted"] = True
    authorized["status"] = "PASSED_REALMAP_V4_TRAINING_ONLY_GATE"
    authorized["deployable"] = False
    authorized["realmap_v4_training_authority"] = {
        "authority": "exploratory_gat_fitting_only",
        "gate_report": str(gate_path),
        "gate_report_sha256": _sha256(gate_path),
        "instance_split": str(split_path),
        "instance_split_sha256": _sha256(split_path),
        "strict_oracle_performance_gate_is_report_only": True,
        "fresh_process_and_e2e_required": True,
        "deployment_authorized": False,
    }
    _write(view_path, authorized)
    print(json.dumps(gate["gate"], sort_keys=True), flush=True)
    return 0


def _validate_split(oracle: dict, split: dict) -> None:
    if oracle.get("schema_version") != ORACLE_SCHEMA:
        raise SystemExit("real-map V4 training authority oracle schema mismatch")
    if split.get("schema_version") != SPLIT_SCHEMA or not bool(
        split.get("frozen_before_matched_outcomes")
    ):
        raise SystemExit("real-map V4 instance split is not pre-outcome frozen")
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
        raise SystemExit("real-map V4 Oracle instances are not split-bound")
    if any(assignments[value] not in {"train", "calibration", "heldout"}
           for value in oracle_instances):
        raise SystemExit("real-map V4 split partition drift")
    for scale in (30, 50):
        rows = [
            row for row in oracle.get("context_rows") or ()
            if int(row.get("scale") or 0) == scale
            and bool(row.get("outcome_determined"))
        ]
        instances = {str(row.get("instance_hash") or "") for row in rows}
        if len(rows) < 20 or len(instances) < 10:
            raise SystemExit(
                f"real-map V4 scale{scale} lacks 20 contexts from 10 instances"
            )


def _training_gate_helpers():
    path = ROOT / "scripts/evaluate_p0v5_qg2_training_only_gate_v2.py"
    spec = importlib.util.spec_from_file_location(
        "p0v5_qg2_realmap_v4_training_gate_helpers", path
    )
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("cannot load QG2 training-only gate helpers")
    spec.loader.exec_module(module)
    return module


def _evaluate_v4_training_gate(oracle: dict, *, helper) -> dict:
    """Authorize fitting from class support, not an arbitrary 5% gain cut."""

    rows = [dict(row) for row in oracle.get("context_rows") or ()]
    initial = [dict(row) for row in oracle.get("initial_rows") or ()]
    contract_errors = helper._contract_errors(oracle)
    all_safe = bool(rows) and all(
        bool(row.get("all_safe")) for row in rows
    ) and all(
        bool(row.get("all_initial_arms_safe"))
        for row in initial if row.get("compliant_context")
    )
    limits = dict(V4_THRESHOLDS)
    per_scale = {}
    for scale in (30, 50):
        determined = [
            row for row in rows
            if int(row.get("scale") or 0) == scale
            and bool(row.get("outcome_determined"))
        ]
        positive = [row for row in determined if float(row["ratio"]) < 1.0]
        nonpositive = [row for row in determined if float(row["ratio"]) >= 1.0]
        harmful = [
            row for row in determined
            if float(row["ratio"]) >= float(limits["harmful_ratio_threshold"])
        ]
        ratios = [float(row["ratio"]) for row in determined]
        metrics = {
            "determined_context_count": len(determined),
            "determined_instance_count": len({
                str(row["instance_hash"]) for row in determined
            }),
            "strict_positive_context_count": len(positive),
            "strict_positive_instance_count": len({
                str(row["instance_hash"]) for row in positive
            }),
            "nonpositive_context_count": len(nonpositive),
            "harmful_context_count": len(harmful),
            "harmful_instance_count": len({
                str(row["instance_hash"]) for row in harmful
            }),
            "paired_geomean_ratio_report_only": (
                helper._geomean_or_none(ratios)
            ),
            "instance_bootstrap_95_upper_report_only": (
                helper._instance_bootstrap_upper(determined)
            ),
            "positive_fraction": len(positive) / max(1, len(determined)),
        }
        metrics["passed"] = bool(
            len(determined)
            >= int(limits["minimum_determined_contexts_per_scale"])
            and metrics["determined_instance_count"]
            >= int(limits["minimum_determined_instances_per_scale"])
            and len(positive)
            >= int(limits["minimum_strict_positive_contexts_per_scale"])
            and metrics["strict_positive_instance_count"]
            >= int(limits["minimum_strict_positive_instances_per_scale"])
            and len(nonpositive)
            >= int(limits["minimum_nonpositive_contexts_per_scale"])
            and metrics["harmful_instance_count"]
            >= int(limits["minimum_harmful_instances_per_scale"])
        )
        per_scale[f"scale{scale}"] = metrics

    saved_by_instance = {}
    for row in rows:
        if not bool(row.get("outcome_determined")):
            continue
        instance = str(row["instance_hash"])
        saved_by_instance[instance] = saved_by_instance.get(instance, 0.0) + max(
            0.0, float(row.get("saved_wall_sec") or 0.0)
        )
    total_saved = sum(saved_by_instance.values())
    maximum_fraction = (
        max(saved_by_instance.values(), default=0.0) / total_saved
        if total_saved > 0.0 else 1.0
    )
    passed = bool(
        not contract_errors
        and all_safe
        and all(per_scale[f"scale{scale}"]["passed"] for scale in (30, 50))
        and maximum_fraction
        <= float(limits["maximum_instance_saved_wall_fraction"])
    )
    return {
        "supervision_schema_version": helper.SUPERVISION_SCHEMA,
        "queue_action_surface": helper.ACTION_SURFACE,
        "thresholds": limits,
        "strict_oracle_gate": dict(oracle.get("oracle_gate") or {}),
        "gate": {
            "passed": passed,
            "reason": (
                "realmap_v4_training_class_support_passed"
                if passed else "realmap_v4_training_class_support_failed"
            ),
            "all_exact_safe": all_safe,
            "contract_errors": contract_errors,
            "maximum_instance_saved_wall_fraction": maximum_fraction,
            **per_scale,
        },
        "training_authorized": passed,
    }


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
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
