"""Fail-closed runtime for the exact-safe QG1 proof-queue GAT."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import os
from threading import RLock
from time import perf_counter
from typing import Any, Mapping


PROOF_QUEUE_GAT_MANIFEST_ENV = "LUNAR_ICE_PROOF_QUEUE_GAT_MANIFEST"
PROOF_QUEUE_GAT_EVALUATION_ENV = (
    "LUNAR_ICE_PROOF_QUEUE_GAT_EVALUATION_MODE"
)
PROOF_QUEUE_GAT_RUNTIME_POLICY_ID = (
    "exact_qg1_arc_order_only_fail_closed_v1"
)
_LOCK = RLock()
_CACHE: dict[str, tuple[dict[str, Any], Any, str]] = {}


def prepare_proof_queue_gat_request_from_environment(request):
    """Return an enriched exact request or the byte-for-byte P0 request.

    Any missing authorization, binding drift, OOD input, non-finite output,
    or calibration veto is a no-op.  Exceptions are intentionally allowed to
    reach the caller, which records a fail-closed lifecycle reason.
    """

    manifest_value = str(
        os.getenv(PROOF_QUEUE_GAT_MANIFEST_ENV, "")
    ).strip()
    if not manifest_value or not bool(request.exact_proof_mode):
        return request, {
            "proof_queue_gat_runtime_enabled": False,
            "proof_queue_gat_action": "NOOP",
        }
    if request.guidance_hints is not None or request.guidance_mode != "off":
        return request, {
            "proof_queue_gat_runtime_enabled": True,
            "proof_queue_gat_action": "NOOP",
            "proof_queue_gat_fallback_reason": (
                "preexisting_guidance_bundle"
            ),
        }

    started = perf_counter()
    manifest_path = Path(manifest_value).resolve()
    manifest, model, checkpoint_hash = _load(manifest_path)
    if str(manifest.get("runtime_policy_id") or "") != (
        PROOF_QUEUE_GAT_RUNTIME_POLICY_ID
    ):
        raise ValueError("proof-queue GAT runtime policy mismatch")
    if str(manifest.get("runtime_implementation_hash") or "") != (
        proof_queue_gat_runtime_implementation_hash()
    ):
        raise ValueError("proof-queue GAT runtime implementation drift")
    scale = int(request.data.scale)
    if scale not in {int(value) for value in manifest.get("allowed_scales", ())}:
        raise ValueError("proof-queue GAT scale is outside manifest scope")
    allowed_engines = {
        str(value) for value in manifest.get("allowed_exact_engine_hashes", ())
    }
    if allowed_engines and str(request.engine_hash or "") not in allowed_engines:
        raise ValueError("proof-queue GAT exact engine hash mismatch")
    allowed_configs = {
        str(value) for value in manifest.get("allowed_exact_config_hashes", ())
    }
    if allowed_configs and str(request.config_hash or "") not in allowed_configs:
        raise ValueError("proof-queue GAT exact config hash mismatch")

    evaluation_mode = str(
        os.getenv(PROOF_QUEUE_GAT_EVALUATION_ENV, "0")
    ).strip().lower() in {"1", "true", "yes", "on"}
    if evaluation_mode:
        if not bool(manifest.get("evaluation_authorized")):
            raise ValueError("proof-queue GAT evaluation is not authorized")
    elif not bool(manifest.get("deployment_authorized")):
        return request, {
            "proof_queue_gat_runtime_enabled": True,
            "proof_queue_gat_action": "NOOP",
            "proof_queue_gat_fallback_reason": "deployment_not_authorized",
        }

    from lunar_ice_bpc.exact.bpc.guidance.contracts import (
        CanonicalSolveBindingV2,
        GUIDANCE_MODE_TASK_ARC,
        PricingOrderingHintsV2,
    )
    from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
    from lunar_ice_bpc.guidance.proof_queue_gat import (
        PROOF_QUEUE_GAT_FEATURE_SCHEMA_V1,
        build_proof_queue_gat_features,
        normalized_arc_potentials,
    )

    features = build_proof_queue_gat_features(
        request.data,
        cover_duals=request.true_duals.cover,
        fleet_dual=float(request.true_duals.fleet_limit),
    )
    feature_payload = {
        "schema_version": features.schema_version,
        "instance_content_hash": features.instance_content_hash,
        "arc_candidate_ids": list(features.arc_candidate_ids),
        "node_features": [list(row) for row in features.node_features],
        "edge_index": [list(row) for row in features.edge_index],
        "edge_features": [list(row) for row in features.edge_features],
        "context_features": list(features.context_features),
    }
    feature_hash = stable_payload_hash(feature_payload)
    ood, ood_reason = _is_ood(
        features, dict(manifest.get("feature_envelope") or {})
    )
    if ood:
        return request, {
            "proof_queue_gat_runtime_enabled": True,
            "proof_queue_gat_action": "NOOP",
            "proof_queue_gat_ood": True,
            "proof_queue_gat_fallback_reason": ood_reason,
            "proof_queue_gat_feature_hash": feature_hash,
        }

    import torch

    torch.set_num_threads(max(1, int(manifest.get("torch_num_threads") or 1)))
    tensors = features.to_tensors()
    inference_started = perf_counter()
    with torch.inference_mode():
        output = model(**tensors)
        potentials = normalized_arc_potentials(output["arc_scores"])
    inference_ms = (perf_counter() - inference_started) * 1000.0
    probability = float(output["benefit_probability"])
    positive_gain = float(output["conditional_positive_gain"])
    expected_gain = probability * positive_gain
    calibration = dict(manifest.get("calibration") or {})
    if evaluation_mode:
        action_allowed = bool(manifest.get("evaluation_force_qg1", True))
        reason = "evaluation_authorized"
    else:
        action_allowed = bool(
            calibration.get("gate_pass")
            and probability
            >= float(calibration.get("probability_threshold") or 1.0)
            and expected_gain
            >= float(calibration.get("expected_gain_threshold") or 1.0)
        )
        reason = (
            "calibrated_qg1" if action_allowed else "calibration_veto"
        )
    if not action_allowed:
        return request, {
            "proof_queue_gat_runtime_enabled": True,
            "proof_queue_gat_action": "NOOP",
            "proof_queue_gat_fallback_reason": reason,
            "proof_queue_gat_probability": probability,
            "proof_queue_gat_expected_gain": expected_gain,
            "proof_queue_gat_inference_wall_ms": inference_ms,
            "proof_queue_gat_feature_hash": feature_hash,
        }

    enriched = replace(
        request,
        proof_queue_policy_id="QG1",
        guidance_mode=GUIDANCE_MODE_TASK_ARC,
        guidance_feature_schema_version=PROOF_QUEUE_GAT_FEATURE_SCHEMA_V1,
        guidance_normalization_version=(
            "centered_maxabs_arc_potential.v1"
        ),
        guidance_checkpoint_id=checkpoint_hash,
        guidance_ood_policy_version=str(
            manifest.get("ood_policy_version") or "feature_envelope.v1"
        ),
        guidance_lifecycle_telemetry=(
            ("guidance_import_sec", 0.0),
            ("guidance_checkpoint_load_sec", 0.0),
            ("guidance_tensorize_sec", 0.0),
            ("guidance_forward_total_sec", inference_ms / 1000.0),
            ("guidance_call_count", 1),
            ("guidance_binding_validation_sec", 0.0),
            ("guidance_native_install_sec", 0.0),
            ("bypassed_before_import", False),
            ("bypass_reason", ""),
            ("proof_queue_gat_feature_hash", feature_hash),
            ("proof_queue_gat_manifest_sha256", _sha256(manifest_path)),
            ("proof_queue_gat_checkpoint_sha256", checkpoint_hash),
            ("proof_queue_gat_probability", probability),
            ("proof_queue_gat_expected_gain", expected_gain),
            ("proof_queue_gat_evaluation_mode", evaluation_mode),
        ),
    )
    binding = CanonicalSolveBindingV2.from_backend_request(enriched)
    hints = PricingOrderingHintsV2(
        binding_hash=binding.binding_hash,
        arc_priorities=tuple(
            (candidate_id, float(value))
            for candidate_id, value in zip(
                features.arc_candidate_ids,
                potentials.tolist(),
                strict=True,
            )
        ),
        queue_policy_id="Q0",
        uncertainty=0.0,
        ood=False,
        source="p0v5_proof_queue_gat",
        diagnostic_only=True,
    )
    return replace(enriched, guidance_hints=hints), {
        "proof_queue_gat_runtime_enabled": True,
        "proof_queue_gat_action": "QG1",
        "proof_queue_gat_decision_reason": reason,
        "proof_queue_gat_ood": False,
        "proof_queue_gat_probability": probability,
        "proof_queue_gat_expected_gain": expected_gain,
        "proof_queue_gat_inference_wall_ms": inference_ms,
        "proof_queue_gat_total_prepare_wall_ms": (
            perf_counter() - started
        )
        * 1000.0,
        "proof_queue_gat_feature_hash": feature_hash,
        "proof_queue_gat_checkpoint_sha256": checkpoint_hash,
    }


def _load(path: Path):
    cache_key = f"{path}:{path.stat().st_mtime_ns}:{path.stat().st_size}"
    with _LOCK:
        cached = _CACHE.get(cache_key)
        if cached is not None:
            return cached
        manifest = json.loads(path.read_text(encoding="utf-8"))
        checkpoint_path = Path(str(manifest["checkpoint_path"]))
        if not checkpoint_path.is_absolute():
            checkpoint_path = (path.parent / checkpoint_path).resolve()
        checkpoint_hash = _sha256(checkpoint_path)
        if checkpoint_hash != str(manifest.get("checkpoint_sha256") or ""):
            raise ValueError("proof-queue GAT checkpoint hash mismatch")
        from lunar_ice_bpc.guidance.proof_queue_gat import load_checkpoint

        model, metadata = load_checkpoint(str(checkpoint_path))
        if str(metadata.get("training_data_hash") or "") != str(
            manifest.get("training_data_hash") or ""
        ):
            raise ValueError("proof-queue GAT training-data hash mismatch")
        _CACHE.clear()
        cached = (manifest, model, checkpoint_hash)
        _CACHE[cache_key] = cached
        return cached


def _is_ood(features, envelope: Mapping[str, Any]) -> tuple[bool, str]:
    if not envelope:
        return True, "missing_feature_envelope"
    context = tuple(float(value) for value in features.context_features)
    lower = tuple(float(value) for value in envelope.get("context_min", ()))
    upper = tuple(float(value) for value in envelope.get("context_max", ()))
    if len(lower) != len(context) or len(upper) != len(context):
        return True, "feature_envelope_dimension_mismatch"
    margin = max(0.0, float(envelope.get("relative_margin") or 0.0))
    for value, lo, hi in zip(context, lower, upper, strict=True):
        width = max(1.0e-9, hi - lo)
        if value < lo - margin * width or value > hi + margin * width:
            return True, "context_outside_feature_envelope"
    node_max = max(abs(value) for row in features.node_features for value in row)
    edge_max = max(abs(value) for row in features.edge_features for value in row)
    if node_max > float(envelope.get("node_max_abs") or 0.0) * (1.0 + margin):
        return True, "node_features_outside_envelope"
    if edge_max > float(envelope.get("edge_max_abs") or 0.0) * (1.0 + margin):
        return True, "edge_features_outside_envelope"
    return False, ""


def proof_queue_gat_runtime_implementation_hash() -> str:
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in (root / "proof_queue_gat.py", Path(__file__).resolve()):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
