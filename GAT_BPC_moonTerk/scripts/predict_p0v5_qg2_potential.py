#!/usr/bin/env python3
"""Materialize one pre-call Linear/MLP/GAT QG2 potential for replay."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.scenario import PATH_TYPES  # noqa: E402
from lunar_ice_bpc.exact.bpc.guidance.contracts import canonical_arc_candidate_id  # noqa: E402
from lunar_ice_bpc.exact.core.branching import branch_context_from_payload  # noqa: E402
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (  # noqa: E402
    build_qg2_features,
    load_checkpoint,
    normalize_qg2_potential_groups,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (  # noqa: E402
    _is_ood,
)
from lunar_ice_bpc.guidance.qg2_admission_supervision import (  # noqa: E402
    QG2_QUEUE_ACTION_SURFACE_V1,
    QG2_SUPERVISION_SCHEMA_V2,
)


OUTPUT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_label_state_potential.v2"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--feature-envelope", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    import torch

    torch.set_num_threads(1)
    data = load_lunar_ice_data(_load(_resolve(args.instance)))
    snapshot_path = _resolve(args.snapshot)
    snapshot = _load(snapshot_path)
    _validate_snapshot(snapshot, data)
    checkpoint_path = _resolve(args.checkpoint)
    feature_envelope_path = _resolve(args.feature_envelope)
    feature_envelope = _load(feature_envelope_path)
    true_duals = dict(snapshot.get("true_duals") or {})
    trajectory = dict(snapshot.get("trajectory_features") or {})
    tensor_started = perf_counter()
    features = build_qg2_features(
        data,
        cover_duals=dict(true_duals.get("task_duals") or true_duals.get("cover") or {}),
        fleet_dual=float(true_duals.get("fleet_dual") or true_duals.get("fleet_limit") or 0.0),
        active_column_count=_optional_int(snapshot.get("active_column_count")),
        active_task_sets=_active_task_sets(snapshot.get("active_task_sets")),
        round_index=_optional_int(snapshot.get("round")),
        previous_proof_wall_sec=_optional_float(trajectory.get("previous_proof_pass_wall_time")),
        previous_processed_labels=_optional_int(
            trajectory.get("previous_proof_processed_labels")
            if trajectory.get("previous_proof_processed_labels") is not None
            else trajectory.get("previous_harvest_processed_labels")
        ),
        dual_l1_delta_from_previous=_optional_float(trajectory.get("dual_l1_delta_from_previous")),
        branch_decisions=tuple(
            branch_context_from_payload(snapshot.get("branch_context") or {}).pair_decisions
        ),
        cut_duals=dict(true_duals.get("cut_duals") or true_duals.get("cuts") or {}),
        v5_midpoint_wall_sec=_optional_float(
            snapshot.get("bidirectional_midpoint_prepass_wall_sec")
            if snapshot.get("bidirectional_midpoint_prepass_wall_sec") is not None
            else trajectory.get("v5_midpoint_wall_sec")
        ),
        root_lifecycle_scope=str(snapshot.get("pricing_lifecycle_scope") or "root_cg") == "root_cg",
    )
    tensor_wall = perf_counter() - tensor_started
    ood, ood_reason = _is_ood(features, feature_envelope)
    base_payload = {
        "schema_version": OUTPUT_SCHEMA,
        "development_only": True,
        "deployable": False,
        "ordering_only": True,
        "future_leakage": False,
        "supervision_schema_version": QG2_SUPERVISION_SCHEMA_V2,
        "queue_action_surface": QG2_QUEUE_ACTION_SURFACE_V1,
        "instance_content_hash": data.instance_content_hash,
        "source_state_hash": str(snapshot["state_hash"]),
        "source_engine_hash": str(snapshot["engine_hash"]),
        "source_config_hash": str(snapshot["config_hash"]),
        "source_exact_action_policy_hash": str(
            snapshot["exact_action_policy_hash"]
        ),
        "feature_schema_version": features.schema_version,
        "label_state_schema_version": "lunar_spprc.qg2_label_state.v1",
        "normalization_version": "global_maxabs_rank_preserving.v2",
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": _sha256(checkpoint_path),
        "feature_envelope_path": str(feature_envelope_path),
        "feature_envelope_sha256": _sha256(feature_envelope_path),
        "tensorization_wall_ms": tensor_wall * 1000.0,
        "ood": bool(ood),
        "runtime_prethreshold_veto": bool(ood),
        "runtime_prethreshold_veto_reason": str(ood_reason if ood else ""),
    }
    if ood:
        payload = {
            **base_payload,
            "source_kind": "precall_ood_literal_q0",
            "training_data_hash": "",
            "task_potentials": {},
            "arc_potentials": {},
            "label_state_coefficients": [],
            "benefit_probability": None,
            "conditional_positive_gain": None,
            "expected_gain": None,
            "inference_wall_ms": 0.0,
        }
        payload["potential_id"] = hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode()
        ).hexdigest()
        _write_output(_resolve(args.output), payload)
        print(json.dumps({
            "output": str(_resolve(args.output)),
            "model_kind": "not_loaded_ood",
            "runtime_prethreshold_veto": True,
            "veto_reason": ood_reason,
            "inference_wall_ms": 0.0,
        }, sort_keys=True))
        return 0

    tensors = features.to_tensors()
    tensor_wall = perf_counter() - tensor_started
    base_payload["tensorization_wall_ms"] = tensor_wall * 1000.0
    model, metadata = load_checkpoint(str(checkpoint_path))
    if (
        metadata.get("supervision_schema_version")
        != QG2_SUPERVISION_SCHEMA_V2
        or metadata.get("queue_action_surface")
        != QG2_QUEUE_ACTION_SURFACE_V1
    ):
        raise SystemExit("QG2 checkpoint action-surface contract mismatch")
    inference_started = perf_counter()
    with torch.inference_mode():
        output = model(**tensors)
        state = output["label_state_coefficients"].reshape(-1)
    inference_wall = perf_counter() - inference_started
    raw_outputs = (
        output["node_scores"],
        output["arc_scores"],
        state,
        output["benefit_probability"],
        output["conditional_positive_gain"],
    )
    if any(not bool(torch.isfinite(value).all()) for value in raw_outputs):
        payload = {
            **base_payload,
            "source_kind": "precall_nonfinite_literal_q0",
            "training_data_hash": str(metadata.get("training_data_hash") or ""),
            "task_potentials": {},
            "arc_potentials": {},
            "label_state_coefficients": [],
            "benefit_probability": None,
            "conditional_positive_gain": None,
            "expected_gain": None,
            "inference_wall_ms": inference_wall * 1000.0,
            "runtime_prethreshold_veto": True,
            "runtime_prethreshold_veto_reason": "nonfinite_model_output",
        }
        payload["potential_id"] = hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode()
        ).hexdigest()
        _write_output(_resolve(args.output), payload)
        return 0
    task, arc, state = normalize_qg2_potential_groups(
        output["node_scores"][1:].reshape(-1),
        output["arc_scores"].reshape(-1),
        state,
    )
    arc_ids = tuple(
        canonical_arc_candidate_id(source, target, path_type)
        for (source, target), by_type in sorted(data.arcs.items())
        for path_type in PATH_TYPES
        if path_type in by_type
    )
    if tuple(features.arc_candidate_ids) != arc_ids:
        raise SystemExit("QG2 predictor arc order mismatch")
    probability = float(output["benefit_probability"])
    conditional_gain = float(output["conditional_positive_gain"])
    zero_potential = max(
        (
            abs(float(value))
            for value in (*task.tolist(), *arc.tolist(), *state.tolist())
        ),
        default=0.0,
    ) <= 1.0e-12
    payload = {
        **base_payload,
        "source_kind": f"precall_{getattr(model, 'model_kind', 'unknown')}_qg2",
        "training_data_hash": str(metadata.get("training_data_hash") or ""),
        "task_potentials": {
            task_id: float(value)
            for task_id, value in zip(data.task_ids, task.tolist(), strict=True)
        },
        "arc_potentials": {
            arc_id: float(value)
            for arc_id, value in zip(arc_ids, arc.tolist(), strict=True)
        },
        "label_state_coefficients": [float(value) for value in state.tolist()],
        "benefit_probability": probability,
        "conditional_positive_gain": conditional_gain,
        "expected_gain": probability * conditional_gain,
        "inference_wall_ms": inference_wall * 1000.0,
        "runtime_prethreshold_veto": bool(zero_potential),
        "runtime_prethreshold_veto_reason": (
            "zero_potential" if zero_potential else ""
        ),
    }
    payload["potential_id"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()
    target = _resolve(args.output)
    _write_output(target, payload)
    print(json.dumps({
        "output": str(target),
        "model_kind": getattr(model, "model_kind", ""),
        "probability": probability,
        "expected_gain": probability * conditional_gain,
        "inference_wall_ms": inference_wall * 1000.0,
    }, sort_keys=True))
    return 0


def _write_output(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def _optional_int(value):
    return None if value is None else max(0, int(value))


def _optional_float(value):
    return None if value is None else max(0.0, float(value))


def _active_task_sets(value):
    if value is None:
        return None
    return tuple(tuple(str(task_id) for task_id in row) for row in value)


def _validate_snapshot(snapshot: dict, data) -> None:
    if snapshot.get("schema_version") != (
        "lunar_ice_bpc.p0v5_proof_tail_fallback_snapshot.v2"
    ):
        raise SystemExit("QG2 predictor requires an admission-bound v2 snapshot")
    if str(snapshot.get("trajectory_feature_semantics_version") or "") != (
        "p0v5_qg2_preaction_trajectory_missingness.v2"
    ):
        raise SystemExit("QG2 predictor trajectory feature semantics mismatch")
    if not bool(snapshot.get("development_only")) or bool(
        snapshot.get("deployable")
    ):
        raise SystemExit("QG2 predictor snapshot safety contract mismatch")
    if snapshot.get("instance_content_hash") != data.instance_content_hash:
        raise SystemExit("QG2 predictor instance hash mismatch")
    active_hashes = snapshot.get("active_column_signature_hashes")
    if active_hashes is None or len(active_hashes) != int(
        snapshot.get("active_column_count") or 0
    ):
        raise SystemExit("QG2 predictor active Master binding is incomplete")
    recorded = str(snapshot.get("state_hash") or "")
    payload = dict(snapshot)
    payload.pop("state_hash", None)
    if recorded != hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest():
        raise SystemExit("QG2 predictor snapshot state hash mismatch")
    if not snapshot.get("config_hash") or not snapshot.get("engine_hash"):
        raise SystemExit("QG2 predictor exact binding is incomplete")
    if str(snapshot.get("base_proof_queue_policy_id") or "") != "Q0":
        raise SystemExit("QG2 predictor snapshot is not Q0-anchored")
    if not str(snapshot.get("exact_action_policy_hash") or ""):
        raise SystemExit("QG2 predictor action-policy binding is incomplete")


def _resolve(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
