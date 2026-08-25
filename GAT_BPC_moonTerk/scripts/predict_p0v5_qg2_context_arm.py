#!/usr/bin/env python3
"""Materialize one fail-closed QD1/QB1 selector prediction.

This is a development-only pre-call predictor.  It never starts Native and
never changes QG2.  Its output can be consumed only by the combined
fresh-process evaluator where QG2 has first right of action and the terminal
fallback remains literal Q0.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.qg2_context_arm_selector import (  # noqa: E402
    QG2_CONTEXT_ARM_SELECTOR_PREDICTION_V1,
    load_qg2_context_arm_selector,
    predict_qg2_context_arms,
    qg2_context_arm_is_ood,
    qg2_context_features_from_snapshot,
)


SELECTOR_REPORT_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_context_arm_selector_feasibility.v1"
)
TRAINING_REPORT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--selector-report", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    import torch

    torch.set_num_threads(1)
    instance_path = _resolve(args.instance)
    snapshot_path = _resolve(args.snapshot)
    report_path = _resolve(args.selector_report)
    report = _load(report_path)
    checkpoint_path, training_path, training = _validate_report(
        report_path, report
    )
    data = load_lunar_ice_data(_load(instance_path))
    snapshot = _load(snapshot_path)
    _validate_snapshot(snapshot, data)

    tensor_started = perf_counter()
    context_features = qg2_context_features_from_snapshot(data, snapshot)
    tensor_wall_ms = (perf_counter() - tensor_started) * 1000.0
    envelope = dict(training.get("feature_envelope") or {})
    ood = qg2_context_arm_is_ood(context_features, envelope)
    base = {
        "schema_version": QG2_CONTEXT_ARM_SELECTOR_PREDICTION_V1,
        "development_only": True,
        "deployable": False,
        "ordering_only": True,
        "future_leakage": False,
        "hierarchy": ["QG2", "QD1_OR_QB1", "Q0"],
        "fallback_action": "Q0",
        "instance_content_hash": str(data.instance_content_hash),
        "source_state_hash": str(snapshot["state_hash"]),
        "source_engine_hash": str(snapshot["engine_hash"]),
        "source_config_hash": str(snapshot["config_hash"]),
        "source_exact_action_policy_hash": str(
            snapshot["exact_action_policy_hash"]
        ),
        "selector_report": str(report_path),
        "selector_report_sha256": _sha256(report_path),
        "selector_checkpoint": str(checkpoint_path),
        "selector_checkpoint_sha256": _sha256(checkpoint_path),
        "training_report": str(training_path),
        "training_report_sha256": _sha256(training_path),
        "feature_schema_version": str(
            report.get("feature_schema_version") or ""
        ),
        "tensorization_wall_ms": tensor_wall_ms,
        "ood": bool(ood),
        "runtime_prethreshold_veto": bool(ood),
        "runtime_prethreshold_veto_reason": (
            "context_feature_envelope_ood" if ood else ""
        ),
    }
    if ood:
        payload = {
            **base,
            "arms": {},
            "inference_wall_ms": 0.0,
        }
    else:
        model, checkpoint = load_qg2_context_arm_selector(checkpoint_path)
        inference_started = perf_counter()
        predictions = predict_qg2_context_arms(
            model, checkpoint, context_features
        )
        inference_wall_ms = (perf_counter() - inference_started) * 1000.0
        payload = {
            **base,
            "arms": {
                arm: {
                    "benefit_probability": row.benefit_probability,
                    "conditional_positive_gain": (
                        row.conditional_positive_gain
                    ),
                    "expected_gain": row.expected_gain,
                }
                for arm, row in predictions.items()
            },
            "inference_wall_ms": inference_wall_ms,
        }
    payload["prediction_id"] = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()
    target = _resolve(args.output)
    _write(target, payload)
    print(
        json.dumps(
            {
                "output": str(target),
                "ood": bool(ood),
                "inference_wall_ms": payload["inference_wall_ms"],
                "fallback_action": "Q0",
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


def _validate_report(
    report_path: Path, report: dict
) -> tuple[Path, Path, dict]:
    errors = []
    if report.get("schema_version") != SELECTOR_REPORT_SCHEMA:
        errors.append("selector_report_schema_mismatch")
    if not bool(report.get("development_only")) or bool(
        report.get("deployable")
    ):
        errors.append("selector_report_safety_mismatch")
    if bool(report.get("deployment_authorized")):
        errors.append("selector_report_claims_deployment")
    if bool(report.get("starts_solver_process")) or bool(
        report.get("changes_qg2")
    ):
        errors.append("selector_report_authority_exceeded")
    if str(report.get("fallback_action") or "") != "Q0" or str(
        report.get("all_arms_rejected_action") or ""
    ) != "Q0":
        errors.append("selector_report_literal_q0_fallback_missing")
    if tuple(report.get("candidate_arms") or ()) != ("QD1", "QB1"):
        errors.append("selector_report_arm_universe_mismatch")
    checkpoint_path = _resolve(report.get("model_path") or "")
    if not checkpoint_path.is_file() or str(
        report.get("model_sha256") or ""
    ) != _sha256(checkpoint_path):
        errors.append("selector_checkpoint_binding_mismatch")
    training_path = _resolve(report.get("training_report") or "")
    if not training_path.is_file() or str(
        report.get("training_report_sha256") or ""
    ) != _sha256(training_path):
        errors.append("selector_training_binding_mismatch")
        training = {}
    else:
        training = _load(training_path)
        if training.get("schema_version") != TRAINING_REPORT_SCHEMA:
            errors.append("selector_training_schema_mismatch")
        if not bool(training.get("oracle_gate_passed")):
            errors.append("selector_training_oracle_authority_missing")
    if errors:
        raise ValueError(
            "QG2 context-arm selector report validation failed:"
            + ",".join(sorted(set(errors)))
        )
    return checkpoint_path, training_path, training


def _validate_snapshot(snapshot: dict, data) -> None:
    if snapshot.get("schema_version") != (
        "lunar_ice_bpc.p0v5_proof_tail_fallback_snapshot.v2"
    ):
        raise SystemExit(
            "QG2 context-arm predictor requires an admission-bound v2 snapshot"
        )
    if str(snapshot.get("trajectory_feature_semantics_version") or "") != (
        "p0v5_qg2_preaction_trajectory_missingness.v2"
    ):
        raise SystemExit("QG2 context-arm trajectory semantics mismatch")
    if not bool(snapshot.get("development_only")) or bool(
        snapshot.get("deployable")
    ):
        raise SystemExit("QG2 context-arm snapshot safety mismatch")
    if snapshot.get("instance_content_hash") != data.instance_content_hash:
        raise SystemExit("QG2 context-arm instance hash mismatch")
    active_hashes = snapshot.get("active_column_signature_hashes")
    if active_hashes is None or len(active_hashes) != int(
        snapshot.get("active_column_count") or 0
    ):
        raise SystemExit("QG2 context-arm active Master binding is incomplete")
    recorded = str(snapshot.get("state_hash") or "")
    payload = dict(snapshot)
    payload.pop("state_hash", None)
    observed = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()
    if recorded != observed:
        raise SystemExit("QG2 context-arm snapshot state hash mismatch")
    if not snapshot.get("config_hash") or not snapshot.get("engine_hash"):
        raise SystemExit("QG2 context-arm exact binding is incomplete")
    if str(snapshot.get("base_proof_queue_policy_id") or "") != "Q0":
        raise SystemExit("QG2 context-arm snapshot is not Q0-anchored")
    if not str(snapshot.get("exact_action_policy_hash") or ""):
        raise SystemExit("QG2 context-arm action-policy binding is incomplete")


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
