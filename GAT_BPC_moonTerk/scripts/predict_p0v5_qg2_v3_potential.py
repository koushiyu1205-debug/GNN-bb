#!/usr/bin/env python3
"""Materialize one activation-free QG2 V3 ordering potential."""

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
from lunar_ice_bpc.exact.bpc.guidance.contracts import (  # noqa: E402
    canonical_arc_candidate_id,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (  # noqa: E402
    normalize_qg2_potential_groups,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (  # noqa: E402
    QG2_V3_RANKER_SCHEMA,
    load_qg2_v3_checkpoint,
    normalize_qg2_v3_features,
    qg2_v3_is_ood,
)
from lunar_ice_bpc.guidance.qg2_admission_supervision import (  # noqa: E402
    QG2_QUEUE_ACTION_SURFACE_V1,
)
from lunar_ice_bpc.guidance.qg2_admission_supervision_v3 import (  # noqa: E402
    QG2_V3_SUPERVISION_SCHEMA,
)
from lunar_ice_bpc.guidance.qg2_context_arm_selector import (  # noqa: E402
    qg2_features_from_snapshot,
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
    snapshot = _load(_resolve(args.snapshot))
    _validate_snapshot(snapshot, data)
    checkpoint_path = _resolve(args.checkpoint)
    feature_envelope_path = _resolve(args.feature_envelope)
    feature_envelope = _load(feature_envelope_path)
    tensor_started = perf_counter()
    features = normalize_qg2_v3_features(
        data, qg2_features_from_snapshot(data, snapshot)
    )
    tensors = features.to_tensors()
    tensor_wall = perf_counter() - tensor_started
    ood, ood_reason = qg2_v3_is_ood(features, feature_envelope)
    base = {
        "schema_version": OUTPUT_SCHEMA,
        "development_only": True,
        "deployable": False,
        "ordering_only": True,
        "ranker_activation_authority": False,
        "future_leakage": False,
        "supervision_schema_version": QG2_V3_SUPERVISION_SCHEMA,
        "queue_action_surface": QG2_QUEUE_ACTION_SURFACE_V1,
        "ranker_schema_version": QG2_V3_RANKER_SCHEMA,
        "instance_content_hash": data.instance_content_hash,
        "source_state_hash": str(snapshot["state_hash"]),
        "source_engine_hash": str(snapshot["engine_hash"]),
        "source_config_hash": str(snapshot["config_hash"]),
        "source_exact_action_policy_hash": str(
            snapshot["exact_action_policy_hash"]
        ),
        "feature_schema_version": features.schema_version,
        "label_state_schema_version": "lunar_spprc.qg2_label_state.v1",
        "normalization_version": "train_zscore_input_global_maxabs_output.v3",
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": _sha256(checkpoint_path),
        "feature_envelope_path": str(feature_envelope_path),
        "feature_envelope_sha256": _sha256(feature_envelope_path),
        "tensorization_wall_ms": tensor_wall * 1000.0,
        "ood": bool(ood),
        "runtime_prethreshold_veto": bool(ood),
        "runtime_prethreshold_veto_reason": str(ood_reason if ood else ""),
        "benefit_probability": None,
        "conditional_positive_gain": None,
        "expected_gain": None,
    }
    if ood:
        payload = {
            **base,
            "source_kind": "precall_v3_ood_literal_q0",
            "training_data_hash": "",
            "task_potentials": {},
            "arc_potentials": {},
            "label_state_coefficients": [],
            "inference_wall_ms": 0.0,
        }
        return _finish(args.output, payload, model_kind="not_loaded_ood")

    model, metadata, normalization = load_qg2_v3_checkpoint(
        str(checkpoint_path)
    )
    if (
        metadata.get("supervision_schema_version")
        != QG2_V3_SUPERVISION_SCHEMA
        or metadata.get("queue_action_surface")
        != QG2_QUEUE_ACTION_SURFACE_V1
        or bool(metadata.get("activation_authority"))
    ):
        raise SystemExit("QG2 V3 checkpoint ranker-only contract mismatch")
    inference_started = perf_counter()
    with torch.inference_mode():
        output = model(**tensors)
        state = output["label_state_coefficients"].reshape(-1)
    inference_wall = perf_counter() - inference_started
    raw = (output["node_scores"], output["arc_scores"], state)
    if any(not bool(value.isfinite().all()) for value in raw):
        payload = {
            **base,
            "source_kind": "precall_v3_nonfinite_literal_q0",
            "training_data_hash": str(metadata.get("training_data_hash") or ""),
            "task_potentials": {},
            "arc_potentials": {},
            "label_state_coefficients": [],
            "inference_wall_ms": inference_wall * 1000.0,
            "runtime_prethreshold_veto": True,
            "runtime_prethreshold_veto_reason": "nonfinite_model_output",
        }
        return _finish(args.output, payload, model_kind="nonfinite")
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
        raise SystemExit("QG2 V3 predictor arc order mismatch")
    zero = max(
        (
            abs(float(value))
            for value in (*task.tolist(), *arc.tolist(), *state.tolist())
        ),
        default=0.0,
    ) <= 1.0e-12
    payload = {
        **base,
        "source_kind": f"precall_v3_{model.model_kind}_ranker_only",
        "training_data_hash": str(metadata.get("training_data_hash") or ""),
        "normalization_sha256": str(
            metadata.get("normalization_sha256") or ""
        ),
        "normalization_fit_partition": str(
            normalization.get("fit_partition") or ""
        ),
        "task_potentials": {
            task_id: float(value)
            for task_id, value in zip(data.task_ids, task.tolist(), strict=True)
        },
        "arc_potentials": {
            arc_id: float(value)
            for arc_id, value in zip(arc_ids, arc.tolist(), strict=True)
        },
        "label_state_coefficients": [float(value) for value in state.tolist()],
        "inference_wall_ms": inference_wall * 1000.0,
        "runtime_prethreshold_veto": bool(zero),
        "runtime_prethreshold_veto_reason": "zero_potential" if zero else "",
    }
    return _finish(args.output, payload, model_kind=model.model_kind)


def _finish(output, payload: dict, *, model_kind: str) -> int:
    payload["potential_id"] = hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode()
    ).hexdigest()
    target = _resolve(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(target),
        "model_kind": model_kind,
        "runtime_prethreshold_veto": bool(
            payload.get("runtime_prethreshold_veto")
        ),
        "inference_wall_ms": float(payload.get("inference_wall_ms") or 0.0),
    }, sort_keys=True))
    return 0


def _validate_snapshot(snapshot: dict, data) -> None:
    if snapshot.get("schema_version") != (
        "lunar_ice_bpc.p0v5_proof_tail_fallback_snapshot.v2"
    ):
        raise SystemExit("QG2 V3 predictor requires a Master-bound v2 snapshot")
    if str(snapshot.get("trajectory_feature_semantics_version") or "") != (
        "p0v5_qg2_preaction_trajectory_missingness.v2"
    ):
        raise SystemExit("QG2 V3 trajectory feature semantics mismatch")
    if not bool(snapshot.get("development_only")) or bool(
        snapshot.get("deployable")
    ):
        raise SystemExit("QG2 V3 snapshot safety contract mismatch")
    if snapshot.get("instance_content_hash") != data.instance_content_hash:
        raise SystemExit("QG2 V3 instance hash mismatch")
    active = snapshot.get("active_column_signature_hashes")
    if active is None or len(active) != int(snapshot.get("active_column_count") or 0):
        raise SystemExit("QG2 V3 active Master binding is incomplete")
    recorded = str(snapshot.get("state_hash") or "")
    payload = dict(snapshot)
    payload.pop("state_hash", None)
    if recorded != hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
    ).hexdigest():
        raise SystemExit("QG2 V3 snapshot state hash mismatch")
    if not snapshot.get("config_hash") or not snapshot.get("engine_hash"):
        raise SystemExit("QG2 V3 exact binding is incomplete")
    if str(snapshot.get("base_proof_queue_policy_id") or "") != "Q0":
        raise SystemExit("QG2 V3 snapshot is not Q0-anchored")
    if not str(snapshot.get("exact_action_policy_hash") or ""):
        raise SystemExit("QG2 V3 exact action-policy binding is incomplete")


def _resolve(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
