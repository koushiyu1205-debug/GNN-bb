#!/usr/bin/env python3
"""Close the fixed sparse-tail GAT pilot without expanding evidence scope."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCHEMA = "lunar_ice_bpc.sparse_tail_gat_fixed_pilot_audit.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite-manifest", required=True)
    parser.add_argument("--dataset-manifest", required=True)
    parser.add_argument("--training-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    audit = audit_fixed_pilot(
        suite_manifest_path=_resolve(args.suite_manifest),
        dataset_manifest_path=_resolve(args.dataset_manifest),
        training_manifest_path=_resolve(args.training_manifest),
    )
    output = _resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit["artifact_integrity_pass"] else 2


def audit_fixed_pilot(
    *,
    suite_manifest_path: Path,
    dataset_manifest_path: Path,
    training_manifest_path: Path,
) -> dict:
    suite = _load_json(suite_manifest_path)
    dataset_manifest = _load_json(dataset_manifest_path)
    training = _load_json(training_manifest_path)
    dataset_path = Path(str(dataset_manifest.get("dataset") or "")).resolve()
    checkpoint_path = (
        training_manifest_path.parent
        / str(training.get("checkpoint") or "")
    ).resolve()
    rows = _load_jsonl(dataset_path) if dataset_path.is_file() else []

    integrity_issues = []
    _expect(
        suite.get("status") == "COMPLETE",
        "suite_not_complete",
        integrity_issues,
    )
    _expect(
        int(suite.get("failure_count") or 0) == 0,
        "suite_has_failures",
        integrity_issues,
    )
    _expect(
        dataset_path.is_file()
        and _sha256(dataset_path)
        == str(dataset_manifest.get("dataset_sha256") or ""),
        "dataset_hash_mismatch",
        integrity_issues,
    )
    _expect(
        _sha256(suite_manifest_path)
        == str(dataset_manifest.get("suite_manifest_sha256") or ""),
        "suite_binding_mismatch",
        integrity_issues,
    )
    _expect(
        _sha256(dataset_manifest_path)
        == str(training.get("dataset_manifest_sha256") or ""),
        "training_dataset_manifest_binding_mismatch",
        integrity_issues,
    )
    _expect(
        checkpoint_path.is_file()
        and _sha256(checkpoint_path)
        == str(training.get("checkpoint_sha256") or ""),
        "checkpoint_hash_mismatch",
        integrity_issues,
    )
    _expect(
        len(rows) == int(dataset_manifest.get("row_count") or -1),
        "dataset_row_count_mismatch",
        integrity_issues,
    )
    _expect(
        all(not (row.get("safety_issues") or ()) for row in rows),
        "dataset_contains_safety_issues",
        integrity_issues,
    )
    _expect(
        all(row.get("certificate_authority") == "none" for row in rows),
        "dataset_has_certificate_authority",
        integrity_issues,
    )
    train_instances = set(dataset_manifest.get("train_instance_sha256") or ())
    calibration_instances = set(
        dataset_manifest.get("calibration_instance_sha256") or ()
    )
    _expect(
        not (train_instances & calibration_instances),
        "train_calibration_instance_leakage",
        integrity_issues,
    )

    action_count = sum(len(row.get("action_ids") or ()) for row in rows)
    beneficial_count = sum(
        sum(int(value) for value in row.get("beneficial") or ())
        for row in rows
    )
    executable_count = sum(
        sum(
            int(value)
            for value in row.get("executable_partial_return") or ()
        )
        for row in rows
    )
    calibration_positive_count = sum(
        sum(int(value) for value in row.get("beneficial") or ())
        for row in rows
        if row.get("split") == "calibration"
    )
    beneficial_context_count = sum(
        int(any(bool(value) for value in row.get("beneficial") or ()))
        for row in rows
    )
    local_positive_gains = [
        float(delta)
        for row in rows
        for delta, beneficial in zip(
            row.get("delta_time_sec") or (),
            row.get("beneficial") or (),
            strict=True,
        )
        if beneficial
    ]
    reason_codes = []
    if int(dataset_manifest.get("runtime_eligible_row_count") or 0) == 0:
        reason_codes.append("no_runtime_eligible_end_to_end_labels")
    if calibration_positive_count == 0:
        reason_codes.append("zero_beneficial_actions_in_frozen_calibration_split")
    if action_count and beneficial_count / action_count < 0.20:
        reason_codes.append("beneficial_action_is_too_sparse_for_safe_calibration")
    if not bool(training.get("formal_context_gate_pass")):
        reason_codes.append("formal_context_quota_not_met")
    if not bool((training.get("calibration") or {}).get("harm_gate_pass")):
        reason_codes.append("harm_gate_closed")

    artifact_integrity_pass = not integrity_issues
    model_gate_pass = bool(
        artifact_integrity_pass
        and not reason_codes
        and training.get("evaluation_authorized")
        and (training.get("calibration") or {}).get("harm_gate_pass")
    )
    return {
        "schema_version": AUDIT_SCHEMA,
        "status": (
            "READY_FOR_FIXED_END_TO_END_GAT_GATE"
            if model_gate_pass
            else "SHADOW_ONLY_STOP_FIXED_PILOT"
        ),
        "artifact_integrity_pass": artifact_integrity_pass,
        "integrity_issues": integrity_issues,
        "fixed_budget_contract": {
            "requested_context_limit": 12,
            "natural_context_count": int(suite.get("context_count") or 0),
            "expected_action_count": int(
                suite.get("expected_action_count") or 0
            ),
            "completed_action_count": int(
                suite.get("completed_action_count") or 0
            ),
            "failure_count": int(suite.get("failure_count") or 0),
            "evidence_collection_closed": True,
            "additional_context_collection_authorized": False,
        },
        "data_summary": {
            "context_count": len(rows),
            "unique_instance_count": len(train_instances | calibration_instances),
            "scales": sorted({int(row["scale"]) for row in rows}),
            "observed_action_count": action_count,
            "executable_partial_action_count": executable_count,
            "beneficial_action_count": beneficial_count,
            "beneficial_context_count": beneficial_context_count,
            "beneficial_action_rate": (
                beneficial_count / action_count if action_count else 0.0
            ),
            "calibration_beneficial_action_count": calibration_positive_count,
            "local_positive_gain_sec": local_positive_gains,
            "label_semantics": dataset_manifest.get("label_semantics"),
            "runtime_eligible_row_count": int(
                dataset_manifest.get("runtime_eligible_row_count") or 0
            ),
            "instance_disjoint_split": not (
                train_instances & calibration_instances
            ),
        },
        "model_summary": {
            "trained_once": bool(training.get("fixed_single_training_run")),
            "checkpoint_sha256": training.get("checkpoint_sha256"),
            "training_seed": training.get("training_seed"),
            "training_epochs": training.get("training_epochs"),
            "training_run_binding_hash": training.get(
                "training_run_binding_hash"
            ),
            "inference_p99_ms": training.get("inference_p99_ms"),
            "inference_p99_gate_pass": training.get(
                "inference_p99_gate_pass"
            ),
            "evaluation_authorized": bool(
                training.get("evaluation_authorized")
            ),
            "deployment_authorized": bool(
                training.get("deployment_authorized")
            ),
            "runtime_fallback": "NOOP",
        },
        "gat_fixed_end_to_end_gate_pass": model_gate_pass,
        "five_percent_solve_time_gate_evaluable": model_gate_pass,
        "five_percent_solve_time_gate_pass": False,
        "reason_codes": reason_codes,
        "decision": (
            "do_not_run_actionful_end_to_end_GAT; keep the frozen Exact path "
            "and model in shadow NOOP mode"
        ),
        "interpretation": (
            "the fixed suite proves sparse local discovery headroom in a few "
            "contexts, but does not provide an outcome-independent positive "
            "calibration sample or end-to-end solve-time labels"
        ),
        "certificate_or_bound_role": "none",
        "baseline_mutated": False,
        "suite_manifest": str(suite_manifest_path.resolve()),
        "suite_manifest_sha256": _sha256(suite_manifest_path),
        "dataset_manifest": str(dataset_manifest_path.resolve()),
        "dataset_manifest_sha256": _sha256(dataset_manifest_path),
        "training_manifest": str(training_manifest_path.resolve()),
        "training_manifest_sha256": _sha256(training_manifest_path),
    }


def _expect(condition: bool, issue: str, issues: list[str]) -> None:
    if not condition:
        issues.append(issue)


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def _load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
