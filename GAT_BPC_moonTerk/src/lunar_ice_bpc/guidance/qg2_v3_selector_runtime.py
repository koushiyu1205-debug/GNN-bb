"""Fail-closed runtime for the QG2 V4 Q0/QG2/QD1/QB1 selector.

The runtime chooses one exact-safe queue ordering before the P0V4 fallback
starts.  A manifest may hard-veto QG2; otherwise a selected QG2 action loads
the separately frozen label-GAT ranker and installs ordering-only potentials.
It cannot filter labels, change dominance, stop pricing, or issue a
certificate.  Any missing authority, binding drift, OOD input, invalid model
output, or rejected arm returns the literal incoming Q0 request.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from math import isfinite
import os
from pathlib import Path
from threading import RLock
from time import perf_counter
from typing import Any, Mapping


QG2_V3_SELECTOR_MANIFEST_ENV = "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_MANIFEST"
QG2_V3_SELECTOR_EVALUATION_ENV = (
    "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_EVALUATION_MODE"
)
QG2_V3_SELECTOR_MANIFEST_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_v3_selector_runtime_manifest.v1"
)
QG2_V3_SELECTOR_RUNTIME_POLICY_ID = (
    "p0v5_qg2_v4_q0_qg2_qd1_qb1_fail_closed.v2"
)
QG2_V3_BASE_ACTIONS = frozenset({"Q0", "QD1", "QB1"})
QG2_V3_FULL_ACTIONS = frozenset({"Q0", "QG2", "QD1", "QB1"})
QG2_V3_ALLOWED_SCALES = frozenset({30, 50})
_LOCK = RLock()
_MANIFEST_CACHE: dict[str, dict[str, Any]] = {}
_MODEL_CACHE: dict[str, tuple[Any, dict[str, Any], str]] = {}
_RANKER_CACHE: dict[str, tuple[Any, dict[str, Any], str]] = {}


def prepare_qg2_v3_selector_request_from_environment(request):
    """Select one exact-safe queue policy or return the unmodified Q0 request."""

    scale = int(request.data.scale)
    if scale not in QG2_V3_ALLOWED_SCALES:
        return request, _noop("scale_bypasses_selector", enabled=False)
    if not bool(request.exact_proof_mode):
        return request, _noop("not_exact_proof")
    if str(request.objective_mode) != "official":
        return request, _noop("nonofficial_objective")
    if not bool(request.proof_tail_fallback_context):
        return request, _noop("not_v5_fallback_context")
    if str(request.proof_queue_policy_id) != "Q0":
        return request, _noop("incoming_policy_is_not_literal_q0")
    if request.proof_tail_active_task_sets is None:
        return request, _noop("active_task_sets_missing")
    if request.proof_tail_active_column_signature_hashes is None:
        return request, _noop("active_column_signatures_missing")
    if request.guidance_hints is not None or request.guidance_mode != "off":
        return request, _noop("preexisting_guidance_bundle")
    if bool(request.dssr_enabled):
        return request, _noop("dssr_not_supported")

    manifest_value = str(os.getenv(QG2_V3_SELECTOR_MANIFEST_ENV, "")).strip()
    if not manifest_value:
        return request, _noop("manifest_not_configured", enabled=False)
    started = perf_counter()
    manifest_path = Path(manifest_value).resolve()
    manifest = _load_manifest(manifest_path)
    _validate_manifest(request, manifest_path, manifest)
    if scale not in {int(value) for value in manifest["allowed_scales"]}:
        return request, _noop("scale_outside_manifest")

    evaluation = str(
        os.getenv(QG2_V3_SELECTOR_EVALUATION_ENV, "0")
    ).strip().lower() in {"1", "true", "yes", "on"}
    if evaluation:
        if not bool(manifest.get("development_e2e_authorized")):
            return request, _noop("development_e2e_not_authorized")
    elif not bool(manifest.get("deployment_authorized")):
        return request, _noop("deployment_not_authorized")

    exact_action_policy_hash = _exact_action_policy_hash(request)
    allowed_engines = {
        str(value) for value in manifest.get("allowed_exact_engine_hashes") or ()
    }
    if allowed_engines and str(request.engine_hash) not in allowed_engines:
        return request, _noop("exact_engine_hash_mismatch")
    allowed_policies = {
        str(value)
        for value in manifest.get("allowed_exact_action_policy_hashes") or ()
    }
    if exact_action_policy_hash not in allowed_policies:
        return request, _noop("exact_action_policy_hash_mismatch")

    tensor_started = perf_counter()
    from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
        build_qg2_features,
    )
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
        normalize_qg2_v3_features,
        qg2_v3_is_ood,
    )

    features = normalize_qg2_v3_features(request.data, build_qg2_features(
        request.data,
        cover_duals=request.true_duals.cover,
        fleet_dual=float(request.true_duals.fleet_limit),
        active_column_count=request.proof_tail_active_column_count,
        active_task_sets=request.proof_tail_active_task_sets,
        round_index=request.proof_tail_round_index,
        previous_proof_wall_sec=request.proof_tail_previous_proof_wall_sec,
        previous_processed_labels=request.proof_tail_previous_processed_labels,
        dual_l1_delta_from_previous=request.proof_tail_dual_delta_l1,
        branch_decisions=tuple(request.branch_context.pair_decisions),
        cut_duals=dict(request.true_duals.cuts or {}),
        v5_midpoint_wall_sec=request.proof_tail_v5_midpoint_wall_sec,
        root_lifecycle_scope=(request.pricing_lifecycle_scope == "root_cg"),
    ))
    feature_payload = {
        "schema_version": features.schema_version,
        "instance_content_hash": features.instance_content_hash,
        "task_ids": list(features.task_ids),
        "arc_candidate_ids": list(features.arc_candidate_ids),
        "node_features": [list(row) for row in features.node_features],
        "edge_index": [list(row) for row in features.edge_index],
        "edge_features": [list(row) for row in features.edge_features],
        "context_features": list(features.context_features),
    }
    feature_hash = stable_payload_hash(feature_payload)
    ood, reason = qg2_v3_is_ood(
        features, dict(manifest["feature_envelope"])
    )
    if ood:
        return request, {
            **_noop(reason),
            "proof_tail_selector_ood": True,
            "proof_tail_selector_feature_hash": feature_hash,
        }
    tensors = features.to_tensors()
    tensor_wall = perf_counter() - tensor_started

    load_started = perf_counter()
    model, checkpoint, checkpoint_hash = _load_model(manifest_path, manifest)
    load_wall = perf_counter() - load_started
    import torch
    torch.set_num_threads(max(1, int(manifest.get("torch_num_threads") or 1)))
    inference_started = perf_counter()
    with torch.inference_mode():
        output = model(**tensors)
    inference_wall = perf_counter() - inference_started
    if any(not bool(value.isfinite().all()) for value in output.values()):
        return request, _noop("nonfinite_model_output")

    predictions = _predictions(output)
    action, selection_reason = _choose_action(predictions, manifest)
    telemetry = {
        "proof_tail_selector_runtime_enabled": True,
        "proof_tail_selector_action": action,
        "proof_tail_selector_decision_reason": selection_reason,
        "proof_tail_selector_model_kind": str(checkpoint["model_kind"]),
        "proof_tail_selector_ood": False,
        "proof_tail_selector_predictions": predictions,
        "proof_tail_selector_tensorization_wall_ms": tensor_wall * 1000.0,
        "proof_tail_selector_checkpoint_load_wall_ms": load_wall * 1000.0,
        "proof_tail_selector_inference_wall_ms": inference_wall * 1000.0,
        "proof_tail_selector_total_prepare_wall_ms": (
            perf_counter() - started
        ) * 1000.0,
        "proof_tail_selector_feature_hash": feature_hash,
        "proof_tail_selector_manifest_sha256": _sha256(manifest_path),
        "proof_tail_selector_checkpoint_sha256": checkpoint_hash,
        "proof_tail_selector_exact_action_policy_hash": (
            exact_action_policy_hash
        ),
    }
    if action == "Q0":
        return request, telemetry
    if action == "QG2":
        return _install_qg2_ranker_action(
            request,
            manifest_path=manifest_path,
            manifest=manifest,
            features=features,
            tensors=tensors,
            feature_hash=feature_hash,
            exact_action_policy_hash=exact_action_policy_hash,
            selector_checkpoint_hash=checkpoint_hash,
            selector_inference_wall=inference_wall,
            telemetry=telemetry,
        )

    selector_config_hash = stable_payload_hash({
        "schema_version": "lunar_ice_bpc.p0v5_qg2_v3_selector_config.v1",
        "source_exact_config_hash": str(request.config_hash),
        "exact_action_policy_hash": exact_action_policy_hash,
        "manifest_sha256": _sha256(manifest_path),
        "checkpoint_sha256": checkpoint_hash,
        "input_feature_hash": feature_hash,
        "proof_queue_policy_id": action,
    })
    return replace(
        request,
        config_hash=selector_config_hash,
        proof_queue_policy_id=action,
        proof_tail_gat_enabled=False,
        guidance_mode="off",
        guidance_hints=None,
        guidance_lifecycle_telemetry=(
            ("proof_tail_selector_action", action),
            ("proof_tail_selector_model_kind", str(checkpoint["model_kind"])),
            ("proof_tail_selector_manifest_sha256", _sha256(manifest_path)),
            ("proof_tail_selector_checkpoint_sha256", checkpoint_hash),
            ("proof_tail_selector_feature_hash", feature_hash),
            ("proof_tail_selector_inference_sec", inference_wall),
        ),
    ), {**telemetry, "proof_tail_selector_config_hash": selector_config_hash}


def qg2_v3_selector_runtime_implementation_hash() -> str:
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in (
        Path(__file__).resolve(),
        root / "qg2_unified_arm_selector_v3.py",
        root / "proof_queue_label_state_gat.py",
        root / "proof_queue_label_state_gat_v3.py",
    ):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _install_qg2_ranker_action(
    request,
    *,
    manifest_path,
    manifest,
    features,
    tensors,
    feature_hash,
    exact_action_policy_hash,
    selector_checkpoint_hash,
    selector_inference_wall,
    telemetry,
):
    """Install ordering-only label-GAT potentials after selector approval."""

    import torch
    from lunar_ice_bpc.exact.bpc.guidance.contracts import (
        CanonicalSolveBindingV2,
        GUIDANCE_MODE_TASK_ARC,
        PricingOrderingHintsV2,
    )
    from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
        QG2_FEATURE_SCHEMA_V1,
        QG2_LABEL_STATE_SCHEMA_V1,
        normalize_qg2_potential_groups,
    )

    if str(manifest.get("qg2_label_state_schema_version") or "") != (
        QG2_LABEL_STATE_SCHEMA_V1
    ):
        return request, _after_inference_noop(
            telemetry, "qg2_label_state_schema_mismatch"
        )
    load_started = perf_counter()
    try:
        ranker, metadata, ranker_hash = _load_ranker(
            manifest_path, manifest
        )
    except Exception as exc:
        return request, _after_inference_noop(
            telemetry,
            f"qg2_ranker_load_failed:{type(exc).__name__}",
        )
    ranker_load_wall = perf_counter() - load_started
    if str(getattr(ranker, "model_kind", "")) != "gat":
        return request, _after_inference_noop(
            telemetry, "qg2_ranker_is_not_gat"
        )
    inference_started = perf_counter()
    with torch.inference_mode():
        output = ranker(**tensors)
        coefficients = output["label_state_coefficients"].reshape(-1)
    ranker_inference_wall = perf_counter() - inference_started
    raw = (output["node_scores"], output["arc_scores"], coefficients)
    if any(not bool(value.isfinite().all()) for value in raw):
        return request, _after_inference_noop(
            telemetry, "qg2_ranker_nonfinite_output",
            proof_tail_selector_qg2_ranker_inference_wall_ms=(
                ranker_inference_wall * 1000.0
            ),
        )
    if coefficients.numel() != 15:
        return request, _after_inference_noop(
            telemetry, "qg2_ranker_state_dimension"
        )
    node, arc, coefficients = normalize_qg2_potential_groups(
        output["node_scores"][1:].reshape(-1),
        output["arc_scores"].reshape(-1),
        coefficients,
    )
    values = (*node.tolist(), *arc.tolist(), *coefficients.tolist())
    if not values or any(not isfinite(float(value)) for value in values):
        return request, _after_inference_noop(
            telemetry, "qg2_ranker_invalid_output"
        )
    if max(abs(float(value)) for value in values) <= 1.0e-12:
        return request, _after_inference_noop(
            telemetry, "qg2_ranker_zero_potential"
        )

    bucket = float(manifest.get("qg2_guidance_bucket_width") or 0.0)
    if bucket not in {1.0e-4, 3.0e-4, 1.0e-3}:
        return request, _after_inference_noop(
            telemetry, "qg2_bucket_invalid"
        )
    manifest_hash = _sha256(manifest_path)
    source_config_hash = str(request.config_hash)
    config_hash = stable_payload_hash({
        "schema_version": "lunar_ice_bpc.p0v5_qg2_v4_selector_config.v2",
        "source_exact_config_hash": source_config_hash,
        "exact_action_policy_hash": exact_action_policy_hash,
        "manifest_sha256": manifest_hash,
        "selector_checkpoint_sha256": selector_checkpoint_hash,
        "ranker_checkpoint_sha256": ranker_hash,
        "input_feature_hash": feature_hash,
        "proof_queue_policy_id": "QG2",
        "guidance_bucket_width": bucket,
    })
    enriched = replace(
        request,
        config_hash=config_hash,
        proof_queue_policy_id="QG2",
        proof_queue_guidance_bucket_width=bucket,
        proof_tail_gat_enabled=True,
        proof_tail_label_state_schema_version=QG2_LABEL_STATE_SCHEMA_V1,
        proof_tail_gat_manifest_path=str(manifest_path),
        guidance_mode=GUIDANCE_MODE_TASK_ARC,
        guidance_feature_schema_version=QG2_FEATURE_SCHEMA_V1,
        guidance_normalization_version=(
            "train_zscore_input_global_maxabs_output.v3_1"
        ),
        guidance_checkpoint_id=ranker_hash,
        guidance_ood_policy_version="per_feature_train_envelope.v3_1",
        guidance_lifecycle_telemetry=(
            ("proof_tail_selector_action", "QG2"),
            ("proof_tail_selector_manifest_sha256", manifest_hash),
            ("proof_tail_selector_checkpoint_sha256", selector_checkpoint_hash),
            ("proof_tail_selector_feature_hash", feature_hash),
            ("proof_tail_selector_inference_sec", selector_inference_wall),
            ("proof_tail_selector_qg2_ranker_checkpoint_sha256", ranker_hash),
            ("proof_tail_selector_qg2_ranker_load_sec", ranker_load_wall),
            ("proof_tail_selector_qg2_ranker_inference_sec", ranker_inference_wall),
            ("proof_tail_selector_qg2_source_exact_config_hash", source_config_hash),
            ("proof_tail_selector_exact_action_policy_hash", exact_action_policy_hash),
        ),
    )
    binding = CanonicalSolveBindingV2.from_backend_request(enriched)
    hints = PricingOrderingHintsV2(
        binding_hash=binding.binding_hash,
        task_priorities=tuple(
            (task_id, float(value))
            for task_id, value in zip(
                features.task_ids, node.tolist(), strict=True
            )
        ),
        arc_priorities=tuple(
            (arc_id, float(value))
            for arc_id, value in zip(
                features.arc_candidate_ids, arc.tolist(), strict=True
            )
        ),
        label_state_coefficients=tuple(
            float(value) for value in coefficients.tolist()
        ),
        label_state_schema_version=QG2_LABEL_STATE_SCHEMA_V1,
        queue_policy_id="Q0",
        uncertainty=0.0,
        ood=False,
        source="p0v5_qg2_v4_context_selected_label_gat",
        diagnostic_only=True,
    )
    total = dict(telemetry)
    total.update({
        "proof_tail_selector_action": "QG2",
        "proof_tail_selector_decision_reason": (
            "risk_adjusted_selector_label_gat"
        ),
        "proof_tail_selector_qg2_ranker_checkpoint_sha256": ranker_hash,
        "proof_tail_selector_qg2_ranker_load_wall_ms": (
            ranker_load_wall * 1000.0
        ),
        "proof_tail_selector_qg2_ranker_inference_wall_ms": (
            ranker_inference_wall * 1000.0
        ),
        "proof_tail_selector_config_hash": config_hash,
    })
    return replace(enriched, guidance_hints=hints), total


def _predictions(output):
    arms = ("QG2", "QD1", "QB1")
    result = {}
    for index, arm in enumerate(arms):
        probability = float(output["benefit_probability"][0, index])
        gain = float(output["conditional_positive_gain"][0, index])
        adverse = float(output["adverse_probability"][0, index])
        values = (probability, gain, adverse)
        if any(not isfinite(value) for value in values):
            raise ValueError("selector emitted nonfinite prediction")
        result[arm] = {
            "benefit_probability": probability,
            "conditional_positive_gain": gain,
            "expected_gain": probability * gain,
            "adverse_probability": adverse,
        }
    return result


def _choose_action(predictions, manifest):
    thresholds = dict(manifest.get("thresholds") or {})
    probability = float(thresholds.get("minimum_benefit_probability", 2.0))
    gain = float(thresholds.get("minimum_expected_gain", float("inf")))
    adverse = float(thresholds.get("maximum_adverse_probability", 0.0))
    penalty = float(thresholds.get("risk_penalty", 1.0))
    if any(not isfinite(value) for value in (probability, gain, adverse, penalty)):
        return "Q0", "invalid_thresholds"
    if not (
        0.0 <= probability <= 1.0
        and gain >= 0.0
        and 0.0 <= adverse <= 1.0
        and penalty >= 0.0
    ):
        return "Q0", "invalid_thresholds"
    eligible = []
    action_universe = frozenset(manifest.get("action_universe") or ())
    forced_veto = set(manifest.get("forced_veto_arms") or ())
    for arm in ("QG2", "QD1", "QB1"):
        if arm not in action_universe or arm in forced_veto:
            continue
        row = predictions[arm]
        if (
            row["benefit_probability"] < probability
            or row["expected_gain"] < gain
            or row["adverse_probability"] > adverse
        ):
            continue
        score = row["expected_gain"] - penalty * row["adverse_probability"]
        if score > 0.0:
            eligible.append((score, arm))
    if not eligible:
        return "Q0", "all_arms_rejected"
    return max(eligible, key=lambda row: (row[0], row[1]))[1], "risk_adjusted_selector"


def _validate_manifest(request, path, manifest):
    errors = []
    if manifest.get("schema_version") != QG2_V3_SELECTOR_MANIFEST_SCHEMA:
        errors.append("manifest_schema_mismatch")
    if manifest.get("runtime_policy_id") != QG2_V3_SELECTOR_RUNTIME_POLICY_ID:
        errors.append("runtime_policy_mismatch")
    if manifest.get("runtime_implementation_hash") != (
        qg2_v3_selector_runtime_implementation_hash()
    ):
        errors.append("runtime_implementation_drift")
    action_universe = frozenset(manifest.get("action_universe") or ())
    if action_universe not in {QG2_V3_BASE_ACTIONS, QG2_V3_FULL_ACTIONS}:
        errors.append("action_universe_mismatch")
    if str(manifest.get("fallback_action") or "") != "Q0":
        errors.append("literal_q0_fallback_missing")
    forced_veto = set(manifest.get("forced_veto_arms") or ())
    if forced_veto not in ({"QG2"}, set()):
        errors.append("qg2_force_veto_invalid")
    if ("QG2" in action_universe) == ("QG2" in forced_veto):
        errors.append("qg2_action_veto_inconsistent")
    if not set(int(value) for value in manifest.get("allowed_scales") or ()).issubset(
        QG2_V3_ALLOWED_SCALES
    ):
        errors.append("allowed_scales_invalid")
    if not request.instance_hash or not request.config_hash or not request.engine_hash:
        errors.append("exact_request_binding_incomplete")
    for field in ("checkpoint_path", "checkpoint_sha256", "feature_envelope"):
        if not manifest.get(field):
            errors.append(f"{field}_missing")
    if "QG2" in action_universe:
        for field in (
            "qg2_ranker_checkpoint_path", "qg2_ranker_checkpoint_sha256",
            "qg2_guidance_bucket_width", "qg2_label_state_schema_version",
        ):
            if not manifest.get(field):
                errors.append(f"{field}_missing")
    if errors:
        raise ValueError("QG2 V3 selector manifest invalid:" + ",".join(errors))


def _load_manifest(path):
    if not path.is_file():
        raise ValueError("QG2 V3 selector manifest missing")
    key = f"{path}:{path.stat().st_mtime_ns}:{path.stat().st_size}"
    with _LOCK:
        if key not in _MANIFEST_CACHE:
            _MANIFEST_CACHE.clear()
            _MANIFEST_CACHE[key] = json.loads(path.read_text(encoding="utf-8"))
        return _MANIFEST_CACHE[key]


def _load_model(manifest_path, manifest):
    checkpoint_path = Path(str(manifest["checkpoint_path"]))
    if not checkpoint_path.is_absolute():
        checkpoint_path = (manifest_path.parent / checkpoint_path).resolve()
    checkpoint_hash = _sha256(checkpoint_path)
    if checkpoint_hash != str(manifest["checkpoint_sha256"]):
        raise ValueError("QG2 V3 selector checkpoint hash mismatch")
    key = f"{checkpoint_path}:{checkpoint_hash}"
    with _LOCK:
        if key in _MODEL_CACHE:
            return _MODEL_CACHE[key]
        import torch
        from lunar_ice_bpc.guidance.qg2_unified_arm_selector_v3 import (
            QG2V3GraphArmSelector,
            QG2V3LinearGraphArmSelector,
            QG2V3MLPArmSelector,
            QG2_V4_SELECTOR_CHECKPOINT_SCHEMA,
        )
        checkpoint = torch.load(
            checkpoint_path, map_location="cpu", weights_only=False
        )
        if checkpoint.get("schema_version") != QG2_V4_SELECTOR_CHECKPOINT_SCHEMA:
            raise ValueError("QG2 V3 selector checkpoint schema mismatch")
        if str(checkpoint.get("input_parity_contract") or "") != (
            "node_edge_context_identical_gat_topology_only_difference.v1"
        ):
            raise ValueError("QG2 V4 selector input-parity contract mismatch")
        kind = str(checkpoint.get("model_kind") or "")
        model_class = {
            "gat": QG2V3GraphArmSelector,
            "mlp": QG2V3MLPArmSelector,
            "linear": QG2V3LinearGraphArmSelector,
        }.get(kind)
        if model_class is None or kind != str(manifest.get("model_kind") or ""):
            raise ValueError("QG2 V3 selector model kind mismatch")
        if tuple(checkpoint.get("action_universe") or ()) != (
            "Q0", "QG2", "QD1", "QB1"
        ):
            raise ValueError("QG2 V3 checkpoint action universe mismatch")
        if set(checkpoint.get("forced_veto_arms") or ()) != set(
            manifest.get("forced_veto_arms") or ()
        ):
            raise ValueError("QG2 V3 checkpoint force veto mismatch")
        model = model_class(checkpoint["normalization"])
        model.load_state_dict(checkpoint["state_dict"], strict=True)
        model.eval()
        _MODEL_CACHE.clear()
        _MODEL_CACHE[key] = (model, checkpoint, checkpoint_hash)
        return _MODEL_CACHE[key]


def _load_ranker(manifest_path, manifest):
    checkpoint_path = Path(str(manifest["qg2_ranker_checkpoint_path"]))
    if not checkpoint_path.is_absolute():
        checkpoint_path = (manifest_path.parent / checkpoint_path).resolve()
    checkpoint_hash = _sha256(checkpoint_path)
    if checkpoint_hash != str(manifest["qg2_ranker_checkpoint_sha256"]):
        raise ValueError("QG2 V4 ranker checkpoint hash mismatch")
    key = f"{checkpoint_path}:{checkpoint_hash}"
    with _LOCK:
        if key in _RANKER_CACHE:
            return _RANKER_CACHE[key]
        from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
            load_qg2_v3_checkpoint,
        )
        from lunar_ice_bpc.guidance.qg2_admission_supervision import (
            QG2_QUEUE_ACTION_SURFACE_V1,
        )
        from lunar_ice_bpc.guidance.qg2_admission_supervision_v3 import (
            QG2_V3_SUPERVISION_SCHEMA,
        )

        model, metadata, _normalization = load_qg2_v3_checkpoint(
            str(checkpoint_path)
        )
        if (
            str(getattr(model, "model_kind", "")) != "gat"
            or bool(metadata.get("activation_authority"))
            or metadata.get("supervision_schema_version")
            != QG2_V3_SUPERVISION_SCHEMA
            or metadata.get("queue_action_surface")
            != QG2_QUEUE_ACTION_SURFACE_V1
        ):
            raise ValueError("QG2 V4 ranker ordering-only contract mismatch")
        _RANKER_CACHE.clear()
        _RANKER_CACHE[key] = (model, metadata, checkpoint_hash)
        return _RANKER_CACHE[key]


def _exact_action_policy_hash(request):
    from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
        qg2_exact_action_policy_hash_from_request,
    )
    return qg2_exact_action_policy_hash_from_request(request)


def _noop(reason, *, enabled=True):
    return {
        "proof_tail_selector_runtime_enabled": bool(enabled),
        "proof_tail_selector_action": "Q0",
        "proof_tail_selector_decision_reason": str(reason),
        "proof_tail_selector_ood": False,
        "proof_tail_selector_inference_wall_ms": 0.0,
    }


def _after_inference_noop(telemetry, reason, **extra):
    result = dict(telemetry)
    result.update({
        "proof_tail_selector_runtime_enabled": True,
        "proof_tail_selector_action": "Q0",
        "proof_tail_selector_decision_reason": str(reason),
        "proof_tail_selector_ood": False,
        **extra,
    })
    return result


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
