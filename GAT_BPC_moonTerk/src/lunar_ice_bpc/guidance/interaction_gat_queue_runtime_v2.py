"""Fail-closed root-only runtime for the P0V5 Interaction-GAT selector.

This module is framework-free.  Torch and graph/model modules are imported
only after scale, lifecycle, exact-mode, request-identity, manifest, and
authority checks have passed.  Every rejected or exceptional path returns the
identical incoming literal-Q0 request object.
"""

from __future__ import annotations

from dataclasses import replace
from math import exp, isfinite, log
import hashlib
import json
import os
from pathlib import Path
import sys
from threading import RLock
from time import perf_counter
from typing import Any, Mapping


INTERACTION_GAT_MANIFEST_ENV = (
    "LUNAR_ICE_P0V5_ROOT_INTERACTION_GAT_SELECTOR_V2_MANIFEST"
)
INTERACTION_GAT_EVALUATION_ENV = (
    "LUNAR_ICE_P0V5_ROOT_INTERACTION_GAT_SELECTOR_V2_EVALUATION_MODE"
)
INTERACTION_GAT_MANIFEST_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_root_interaction_gat_runtime_manifest.v1"
)
INTERACTION_GAT_RUNTIME_POLICY_V2 = (
    "P0V5_ROOT_INTERACTION_GAT_SELECTOR_V2"
)
INTERACTION_GAT_ALLOWED_SCALES = frozenset({30, 50})
INTERACTION_GAT_ACTION_UNIVERSE = ("Q0", "QGR1", "QD1", "QB1")
QGR1_BUCKET_WIDTH = 1.0e-4
MAXIMUM_PARAMETER_COUNT = 50_000

_LOCK = RLock()
_MANIFEST_CACHE: dict[str, dict[str, Any]] = {}
_MODEL_CACHE: dict[str, tuple[Any, dict[str, Any], str]] = {}
_RANKER_CACHE: dict[str, tuple[Any, dict[str, Any], str]] = {}


def prepare_root_interaction_gat_request_from_environment(request):
    """Install at most one exact-safe queue arm, otherwise literal Q0."""

    scale = int(request.data.scale)
    if scale not in INTERACTION_GAT_ALLOWED_SCALES:
        return request, _noop("scale_bypasses_before_manifest_torch_graph", enabled=False)
    # Root-only authority is deliberately the second cheap guard so tree
    # requests cannot read the manifest or import graph/Torch code.
    if str(request.pricing_lifecycle_scope) != "root_cg":
        return request, _noop("non_root_lifecycle_bypasses_before_manifest_torch_graph", enabled=False)
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
    if request.guidance_hints is not None or str(request.guidance_mode) != "off":
        return request, _noop("preexisting_guidance_bundle")
    if bool(request.dssr_enabled):
        return request, _noop("dssr_not_supported")

    started = perf_counter()
    try:
        return _prepare_after_cheap_guards(request, started)
    except Exception as exc:
        return request, {
            **_noop(f"interaction_gat_fail_closed:{type(exc).__name__}"),
            "proof_tail_interaction_gat_total_prepare_wall_ms": (
                perf_counter() - started
            ) * 1000.0,
        }


def _prepare_after_cheap_guards(request, started):
    manifest_value = str(os.getenv(INTERACTION_GAT_MANIFEST_ENV, "")).strip()
    if not manifest_value:
        return request, _noop("manifest_not_configured", enabled=False)
    manifest_path = Path(manifest_value).resolve()
    manifest = _load_manifest(manifest_path)
    _validate_manifest(request, manifest)

    evaluation = str(os.getenv(INTERACTION_GAT_EVALUATION_ENV, "0")).lower()
    evaluation = evaluation in {"1", "true", "yes", "on"}
    if evaluation:
        if not bool(manifest.get("development_e2e_authorized")):
            return request, _noop("development_e2e_not_authorized")
    elif not bool(manifest.get("deployment_authorized")):
        return request, _noop("deployment_not_authorized")

    scale = int(request.data.scale)
    if scale not in {int(v) for v in manifest["allowed_scales"]}:
        return request, _noop("scale_outside_manifest")
    exact_policy_hash = _exact_action_policy_hash(request)
    if str(request.engine_hash) not in {
        str(value) for value in manifest["allowed_exact_engine_hashes"]
    }:
        return request, _noop("exact_engine_hash_mismatch")
    if exact_policy_hash not in {
        str(value) for value in manifest["allowed_exact_action_policy_hashes"]
    }:
        return request, _noop("exact_action_policy_hash_mismatch")
    if str(request.config_hash) not in {
        str(value) for value in manifest["allowed_exact_config_hashes"]
    }:
        return request, _noop("exact_config_hash_mismatch")

    torch_was_loaded = "torch" in sys.modules
    import_started = perf_counter()
    from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
    from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (
        INTERACTION_FEATURE_SCHEMA_V2,
        INTERACTION_GRAPH_SCHEMA_V1,
        build_interaction_graph,
        interaction_is_ood,
    )
    import_wall = perf_counter() - import_started
    first_import_wall = 0.0 if torch_was_loaded else import_wall

    graph_started = perf_counter()
    features = build_interaction_graph(request)
    if features.schema_version != INTERACTION_FEATURE_SCHEMA_V2:
        return request, _noop("interaction_feature_schema_drift")
    if features.graph_schema_version != INTERACTION_GRAPH_SCHEMA_V1:
        return request, _noop("interaction_graph_schema_drift")
    feature_hash = stable_payload_hash(features.audit_payload())
    ood, reason = interaction_is_ood(features, dict(manifest["feature_envelope"]))
    graph_wall = perf_counter() - graph_started
    if ood:
        return request, {
            **_noop(reason),
            "proof_tail_interaction_gat_manifest_read": True,
            "proof_tail_interaction_gat_graph_build_calls": 1,
            "proof_tail_interaction_gat_ood": True,
            "proof_tail_interaction_gat_feature_hash": feature_hash,
            "proof_tail_interaction_gat_graph_build_wall_ms": graph_wall * 1000.0,
            "proof_tail_interaction_gat_torch_first_import_wall_ms": first_import_wall * 1000.0,
            "proof_tail_interaction_gat_total_prepare_wall_ms": (
                perf_counter() - started
            ) * 1000.0,
        }
    tensor_started = perf_counter()
    tensors = features.to_tensors()
    tensor_wall = perf_counter() - tensor_started

    load_started = perf_counter()
    model, checkpoint, checkpoint_hash = _load_model(manifest_path, manifest)
    load_wall = perf_counter() - load_started
    import torch
    torch.set_num_threads(1)
    inference_started = perf_counter()
    with torch.inference_mode():
        output = model(**tensors)
    inference_wall = perf_counter() - inference_started
    if any(not bool(value.isfinite().all()) for value in output.values()):
        return request, {
            **_noop("nonfinite_selector_output"),
            "proof_tail_interaction_gat_manifest_read": True,
            "proof_tail_interaction_gat_graph_build_calls": 1,
            "proof_tail_interaction_gat_model_calls": 1,
            "proof_tail_interaction_gat_graph_build_wall_ms": graph_wall * 1000.0,
            "proof_tail_interaction_gat_tensorization_wall_ms": tensor_wall * 1000.0,
            "proof_tail_interaction_gat_checkpoint_load_wall_ms": load_wall * 1000.0,
            "proof_tail_interaction_gat_torch_first_import_wall_ms": first_import_wall * 1000.0,
            "proof_tail_interaction_gat_inference_wall_ms": inference_wall * 1000.0,
            "proof_tail_interaction_gat_total_prepare_wall_ms": (
                perf_counter() - started
            ) * 1000.0,
        }
    predictions = _predictions(output, checkpoint.get("probability_calibration"))
    action, reason = _choose_action(predictions, manifest, scale)
    manifest_hash = _sha256(manifest_path)
    telemetry = {
        "proof_tail_interaction_gat_runtime_enabled": True,
        "proof_tail_interaction_gat_manifest_read": True,
        "proof_tail_interaction_gat_graph_build_calls": 1,
        "proof_tail_interaction_gat_model_calls": 1,
        "proof_tail_interaction_gat_ranker_calls": 0,
        "proof_tail_interaction_gat_action": action,
        "proof_tail_interaction_gat_decision_reason": reason,
        "proof_tail_interaction_gat_model_kind": "gat",
        "proof_tail_interaction_gat_message_passing_required": True,
        "proof_tail_interaction_gat_ood": False,
        "proof_tail_interaction_gat_predictions": predictions,
        "proof_tail_interaction_gat_graph_build_wall_ms": graph_wall * 1000.0,
        "proof_tail_interaction_gat_tensorization_wall_ms": tensor_wall * 1000.0,
        "proof_tail_interaction_gat_checkpoint_load_wall_ms": load_wall * 1000.0,
        "proof_tail_interaction_gat_torch_first_import_wall_ms": first_import_wall * 1000.0,
        "proof_tail_interaction_gat_inference_wall_ms": inference_wall * 1000.0,
        "proof_tail_interaction_gat_total_prepare_wall_ms": (perf_counter() - started) * 1000.0,
        "proof_tail_interaction_gat_feature_hash": feature_hash,
        "proof_tail_interaction_gat_manifest_sha256": manifest_hash,
        "proof_tail_interaction_gat_checkpoint_sha256": checkpoint_hash,
        "proof_tail_interaction_gat_exact_action_policy_hash": exact_policy_hash,
    }
    if action == "Q0":
        return request, telemetry
    if action == "QGR1":
        return _install_qgr1(
            request, manifest_path, manifest, feature_hash, exact_policy_hash,
            checkpoint_hash, telemetry, started=started,
        )

    config_hash = stable_payload_hash({
        "schema_version": "lunar_ice_bpc.p0v5_root_interaction_gat_action_config.v1",
        "source_exact_config_hash": str(request.config_hash),
        "exact_action_policy_hash": exact_policy_hash,
        "manifest_sha256": manifest_hash,
        "selector_checkpoint_sha256": checkpoint_hash,
        "input_feature_hash": feature_hash,
        "proof_queue_policy_id": action,
    })
    selected = replace(
        request,
        config_hash=config_hash,
        proof_queue_policy_id=action,
        proof_tail_gat_enabled=False,
        guidance_mode="off",
        guidance_hints=None,
        guidance_lifecycle_telemetry=(
            ("proof_tail_interaction_gat_action", action),
            ("proof_tail_interaction_gat_manifest_sha256", manifest_hash),
            ("proof_tail_interaction_gat_checkpoint_sha256", checkpoint_hash),
            ("proof_tail_interaction_gat_feature_hash", feature_hash),
            ("proof_tail_interaction_gat_inference_sec", inference_wall),
        ),
    )
    telemetry["proof_tail_interaction_gat_config_hash"] = config_hash
    return selected, telemetry


def _install_qgr1(
    request, manifest_path, manifest, feature_hash, exact_policy_hash,
    selector_checkpoint_hash, telemetry,
    *, started,
):
    """Install ordering-only QGR1 after its arm and hard-zero gates pass."""

    import torch
    from lunar_ice_bpc.exact.bpc.guidance.contracts import (
        CanonicalSolveBindingV2,
        GUIDANCE_MODE_TASK_ARC,
        PricingOrderingHintsV2,
    )
    from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
    from lunar_ice_bpc.guidance.context_queue_portfolio_v1 import build_portfolio_features
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
        QG2Features,
        QG2_FEATURE_SCHEMA_V1,
        QG2_LABEL_STATE_SCHEMA_V1,
        QG2_CONTEXT_FEATURES,
        normalize_qg2_potential_groups,
    )
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import QG2_V3_INPUT_FEATURE_SCHEMA
    from lunar_ice_bpc.guidance.qgr1_supervision import (
        QGR1_ACTION_SURFACE_V1,
        QGR1_SUPERVISION_SCHEMA_V1,
    )

    if float(manifest.get("qgr1_guidance_bucket_width") or 0.0) != QGR1_BUCKET_WIDTH:
        return request, _after_noop(telemetry, "qgr1_bucket_not_frozen")
    load_started = perf_counter()
    try:
        ranker, metadata, ranker_hash = _load_ranker(manifest_path, manifest)
    except Exception as exc:
        return request, _after_noop(telemetry, f"qgr1_ranker_load_failed:{type(exc).__name__}")
    ranker_load_wall = perf_counter() - load_started
    if (
        str(getattr(ranker, "model_kind", "")) != "gat"
        or bool(metadata.get("activation_authority"))
        or metadata.get("supervision_schema_version") != QGR1_SUPERVISION_SCHEMA_V1
        or metadata.get("queue_action_surface") != QGR1_ACTION_SURFACE_V1
        or metadata.get("residual_training_contract")
        != "supervised75_neutral25_pressure_weighted.v2"
    ):
        return request, _after_noop(telemetry, "qgr1_ranker_contract_mismatch")
    hard_zero = dict(metadata.get("hard_zero_thresholds") or {})
    if (
        hard_zero.get("quantile") != 0.75
        or not bool(hard_zero.get("frozen_before_wall_outcomes"))
        or any(
            key not in hard_zero or not isfinite(float(hard_zero[key]))
            or float(hard_zero[key]) < 0.0
            for key in ("node", "arc", "state")
        )
    ):
        return request, _after_noop(telemetry, "qgr1_hard_zero_threshold_contract_mismatch")

    portfolio = build_portfolio_features(request)
    ranker_features = QG2Features(
        instance_content_hash=portfolio.instance_content_hash,
        task_ids=portfolio.task_ids,
        arc_candidate_ids=portfolio.arc_candidate_ids,
        node_features=portfolio.node_features,
        edge_index=portfolio.edge_index,
        edge_features=portfolio.edge_features,
        context_features=tuple(portfolio.context_features[:len(QG2_CONTEXT_FEATURES)]),
        schema_version=QG2_V3_INPUT_FEATURE_SCHEMA,
    )
    inference_started = perf_counter()
    with torch.inference_mode():
        output = ranker(**ranker_features.to_tensors())
    ranker_inference_wall = perf_counter() - inference_started
    raw_node = output["node_scores"][1:].reshape(-1)
    raw_arc = output["arc_scores"].reshape(-1)
    raw_state = output["label_state_coefficients"].reshape(-1)
    if raw_state.numel() != 15 or any(
        not bool(value.isfinite().all()) for value in (raw_node, raw_arc, raw_state)
    ):
        return request, _after_noop(telemetry, "qgr1_ranker_nonfinite_or_dimension")
    sparse = tuple(
        torch.where(value.abs() >= float(hard_zero[key]), value, torch.zeros_like(value))
        for key, value in (("node", raw_node), ("arc", raw_arc), ("state", raw_state))
    )
    node, arc, state = normalize_qg2_potential_groups(*sparse)
    values = (*node.tolist(), *arc.tolist(), *state.tolist())
    if not values or max(abs(float(v)) for v in values) <= 1.0e-12:
        return request, _after_noop(telemetry, "qgr1_ranker_zero_after_sparsification")

    manifest_hash = _sha256(manifest_path)
    config_hash = stable_payload_hash({
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qgr1_config.v1",
        "source_exact_config_hash": str(request.config_hash),
        "exact_action_policy_hash": exact_policy_hash,
        "manifest_sha256": manifest_hash,
        "selector_checkpoint_sha256": selector_checkpoint_hash,
        "ranker_checkpoint_sha256": ranker_hash,
        "input_feature_hash": feature_hash,
        "proof_queue_policy_id": "QGR1",
        "guidance_bucket_width": QGR1_BUCKET_WIDTH,
        "hard_zero_thresholds": hard_zero,
    })
    enriched = replace(
        request,
        config_hash=config_hash,
        proof_queue_policy_id="QGR1",
        proof_queue_guidance_bucket_width=QGR1_BUCKET_WIDTH,
        proof_tail_gat_enabled=True,
        proof_tail_queue_policy_id="QGR1",
        proof_tail_label_state_schema_version=QG2_LABEL_STATE_SCHEMA_V1,
        proof_tail_gat_manifest_path=str(manifest_path),
        guidance_mode=GUIDANCE_MODE_TASK_ARC,
        guidance_feature_schema_version=QG2_FEATURE_SCHEMA_V1,
        guidance_normalization_version="train_zscore_group_q75_hardzero_global_maxabs.qgr1.v2",
        guidance_checkpoint_id=ranker_hash,
        guidance_ood_policy_version="per_feature_train_envelope.5pct.v1",
        guidance_lifecycle_telemetry=(
            ("proof_tail_interaction_gat_action", "QGR1"),
            ("proof_tail_interaction_gat_manifest_sha256", manifest_hash),
            ("proof_tail_interaction_gat_checkpoint_sha256", selector_checkpoint_hash),
            ("proof_tail_interaction_gat_feature_hash", feature_hash),
            ("proof_tail_interaction_gat_qgr1_ranker_checkpoint_sha256", ranker_hash),
            ("proof_tail_interaction_gat_qgr1_ranker_load_sec", ranker_load_wall),
            ("proof_tail_interaction_gat_qgr1_ranker_inference_sec", ranker_inference_wall),
        ),
    )
    binding = CanonicalSolveBindingV2.from_backend_request(enriched)
    hints = PricingOrderingHintsV2(
        binding_hash=binding.binding_hash,
        task_priorities=tuple(zip(portfolio.task_ids, map(float, node.tolist()), strict=True)),
        arc_priorities=tuple(zip(portfolio.arc_candidate_ids, map(float, arc.tolist()), strict=True)),
        label_state_coefficients=tuple(map(float, state.tolist())),
        label_state_schema_version=QG2_LABEL_STATE_SCHEMA_V1,
        queue_policy_id="Q0",
        uncertainty=0.0,
        ood=False,
        source="p0v5_root_interaction_gat_qgr1_depth_residual_gat_v2",
        diagnostic_only=True,
    )
    result = dict(telemetry)
    result.update({
        "proof_tail_interaction_gat_action": "QGR1",
        "proof_tail_interaction_gat_decision_reason": "risk_adjusted_gat_qgr1_ranker",
        "proof_tail_interaction_gat_qgr1_ranker_checkpoint_sha256": ranker_hash,
        "proof_tail_interaction_gat_qgr1_ranker_load_wall_ms": ranker_load_wall * 1000.0,
        "proof_tail_interaction_gat_qgr1_ranker_inference_wall_ms": ranker_inference_wall * 1000.0,
        "proof_tail_interaction_gat_qgr1_hard_zero_thresholds": hard_zero,
        "proof_tail_interaction_gat_ranker_calls": 1,
        "proof_tail_interaction_gat_config_hash": config_hash,
        "proof_tail_interaction_gat_total_prepare_wall_ms": (
            perf_counter() - started
        ) * 1000.0,
    })
    return replace(enriched, guidance_hints=hints), result


def _validate_manifest(request, manifest):
    from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (
        INTERACTION_FEATURE_SCHEMA_V2,
        INTERACTION_GRAPH_SCHEMA_V1,
        INTERACTION_INPUT_PARITY_CONTRACT_V1,
        interaction_graph_builder_hash,
    )
    errors = []
    expected = {
        "schema_version": INTERACTION_GAT_MANIFEST_SCHEMA_V1,
        "runtime_policy_id": INTERACTION_GAT_RUNTIME_POLICY_V2,
        "runtime_implementation_hash": interaction_gat_runtime_implementation_hash(),
        "graph_schema_version": INTERACTION_GRAPH_SCHEMA_V1,
        "feature_schema_version": INTERACTION_FEATURE_SCHEMA_V2,
        "graph_builder_hash": interaction_graph_builder_hash(),
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "model_kind": "gat",
    }
    for field, value in expected.items():
        if manifest.get(field) != value:
            errors.append(f"{field}_mismatch")
    if tuple(manifest.get("action_universe") or ()) != INTERACTION_GAT_ACTION_UNIVERSE:
        errors.append("action_universe_mismatch")
    if str(manifest.get("fallback_action") or "") != "Q0":
        errors.append("literal_q0_fallback_missing")
    if manifest.get("lifecycle_authority") != ["root_cg"]:
        errors.append("root_only_authority_missing")
    if not bool(manifest.get("message_passing_required")):
        errors.append("message_passing_not_required")
    if bool(manifest.get("controls_candidate_authorized")):
        errors.append("controls_must_not_be_candidate_authorized")
    if bool(manifest.get("deployment_authorized")):
        errors.append("v2_deployment_authority_forbidden")
    if not bool(manifest.get("development_only")):
        errors.append("development_only_missing")
    if bool(manifest.get("production_switch_authorized")):
        errors.append("production_switch_authority_forbidden")
    allowed = {int(value) for value in manifest.get("allowed_scales") or ()}
    if not allowed or not allowed.issubset(INTERACTION_GAT_ALLOWED_SCALES):
        errors.append("allowed_scales_invalid")
    masks = dict(manifest.get("arm_scale_mask") or {})
    if set(masks) != {"QGR1", "QD1", "QB1"}:
        errors.append("arm_scale_mask_invalid")
    elif any(not {int(v) for v in values}.issubset(allowed) for values in masks.values()):
        errors.append("arm_scale_mask_outside_allowed_scales")
    if not all((request.instance_hash, request.config_hash, request.engine_hash)):
        errors.append("exact_request_binding_incomplete")
    for field in (
        "selector_checkpoint_path", "selector_checkpoint_sha256",
        "feature_envelope", "allowed_exact_engine_hashes",
        "allowed_exact_action_policy_hashes", "allowed_exact_config_hashes",
        "thresholds", "source_freeze_sha256", "native_binary_sha256",
    ):
        if not manifest.get(field):
            errors.append(f"{field}_missing")
    if int(manifest.get("torch_num_threads") or 0) != 1:
        errors.append("torch_num_threads_must_equal_one")
    qgr1_veto = "QGR1" in set(manifest.get("forced_veto_arms") or ())
    qgr1_active = any(int(v) in allowed for v in masks.get("QGR1", ()))
    if qgr1_active and not qgr1_veto:
        for field in (
            "qgr1_ranker_checkpoint_path", "qgr1_ranker_checkpoint_sha256",
            "qgr1_guidance_bucket_width", "qgr1_label_state_schema_version",
        ):
            if not manifest.get(field):
                errors.append(f"{field}_missing")
    if errors:
        raise ValueError("Interaction-GAT manifest invalid:" + ",".join(errors))


def _load_model(manifest_path, manifest):
    path = _resolve_checkpoint(manifest_path, manifest["selector_checkpoint_path"])
    digest = _sha256(path)
    if digest != str(manifest["selector_checkpoint_sha256"]):
        raise ValueError("interaction GAT checkpoint hash mismatch")
    key = f"{path}:{digest}"
    with _LOCK:
        if key in _MODEL_CACHE:
            return _MODEL_CACHE[key]
        import torch
        from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (
            INTERACTION_CHECKPOINT_SCHEMA_V1,
            INTERACTION_FEATURE_SCHEMA_V2,
            INTERACTION_GRAPH_SCHEMA_V1,
            INTERACTION_INPUT_PARITY_CONTRACT_V1,
            InteractionGATSelector,
            interaction_parameter_count,
        )
        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
        requirements = {
            "schema_version": INTERACTION_CHECKPOINT_SCHEMA_V1,
            "feature_schema_version": INTERACTION_FEATURE_SCHEMA_V2,
            "graph_schema_version": INTERACTION_GRAPH_SCHEMA_V1,
            "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
            "model_kind": "gat",
            "message_passing_required": True,
            "controls_candidate_authorized": False,
        }
        if any(checkpoint.get(k) != v for k, v in requirements.items()):
            raise ValueError("interaction GAT checkpoint contract mismatch")
        if tuple(checkpoint.get("action_universe") or ()) != INTERACTION_GAT_ACTION_UNIVERSE:
            raise ValueError("interaction GAT checkpoint action universe mismatch")
        model = InteractionGATSelector(dict(checkpoint["normalization"]))
        model.load_state_dict(checkpoint["state_dict"], strict=True)
        if interaction_parameter_count(model) >= MAXIMUM_PARAMETER_COUNT:
            raise ValueError("interaction GAT exceeds parameter cap")
        model.eval()
        _MODEL_CACHE.clear()
        _MODEL_CACHE[key] = (model, dict(checkpoint), digest)
        return _MODEL_CACHE[key]


def _load_ranker(manifest_path, manifest):
    path = _resolve_checkpoint(manifest_path, manifest["qgr1_ranker_checkpoint_path"])
    digest = _sha256(path)
    if digest != str(manifest["qgr1_ranker_checkpoint_sha256"]):
        raise ValueError("QGR1 ranker checkpoint hash mismatch")
    key = f"{path}:{digest}"
    with _LOCK:
        if key in _RANKER_CACHE:
            return _RANKER_CACHE[key]
        from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import load_qg2_v3_checkpoint
        model, metadata, _normalization = load_qg2_v3_checkpoint(str(path))
        _RANKER_CACHE.clear()
        _RANKER_CACHE[key] = (model, dict(metadata), digest)
        return _RANKER_CACHE[key]


def _predictions(output: Mapping[str, Any], calibration):
    calibration = dict(calibration or {})
    result = {}
    for index, arm in enumerate(("QGR1", "QD1", "QB1")):
        benefit = _calibrate(
            float(output["benefit_probability"][0, index]),
            dict(calibration.get("benefit") or {}).get(arm),
        )
        gain = float(output["conditional_positive_gain"][0, index]) * float(
            dict(calibration.get("positive_gain_scale") or {}).get(arm, 1.0)
        )
        adverse = _calibrate(
            float(output["adverse_probability"][0, index]),
            dict(calibration.get("adverse") or {}).get(arm),
        )
        result[arm] = {
            "benefit_probability": benefit,
            "conditional_positive_gain": gain,
            "adverse_probability": adverse,
            "expected_gain": benefit * gain,
        }
    return result


def _calibrate(value, row):
    probability = min(1.0 - 1.0e-7, max(1.0e-7, float(value)))
    if not row:
        return probability
    row = dict(row)
    slope = float(row.get("slope", 1.0))
    intercept = float(row.get("intercept", 0.0))
    if not isfinite(slope) or not isfinite(intercept) or slope < 0.0:
        raise ValueError("interaction probability calibration invalid")
    score = slope * log(probability / (1.0 - probability)) + intercept
    return 1.0 / (1.0 + exp(-max(-40.0, min(40.0, score))))


def _choose_action(predictions, manifest, scale):
    thresholds = dict(manifest.get("thresholds") or {})
    values = (
        float(thresholds.get("minimum_benefit_probability", 2.0)),
        float(thresholds.get("minimum_expected_gain", float("inf"))),
        float(thresholds.get("maximum_adverse_probability", -1.0)),
        float(thresholds.get("risk_penalty", -1.0)),
    )
    probability, expected_gain, adverse, penalty = values
    if (
        any(not isfinite(v) for v in values)
        or not 0.0 <= probability <= 1.0 or expected_gain < 0.0
        or not 0.0 <= adverse <= 1.0 or penalty < 0.0
    ):
        return "Q0", "invalid_thresholds"
    masks = {
        str(arm): {int(v) for v in scales}
        for arm, scales in dict(manifest.get("arm_scale_mask") or {}).items()
    }
    veto = set(manifest.get("forced_veto_arms") or ())
    veto.update(dict(manifest.get("forced_veto_arms_by_scale") or {}).get(str(scale), ()))
    eligible = []
    for arm in ("QGR1", "QD1", "QB1"):
        row = predictions[arm]
        score = row["expected_gain"] - penalty * row["adverse_probability"]
        if (
            arm not in veto and scale in masks.get(arm, set())
            and row["benefit_probability"] >= probability
            and row["expected_gain"] >= expected_gain
            and row["adverse_probability"] <= adverse and score > 0.0
        ):
            eligible.append((score, arm))
    return (
        ("Q0", "all_arms_rejected") if not eligible
        else (max(eligible, key=lambda row: (row[0], row[1]))[1], "risk_adjusted_gat_selector")
    )


def interaction_gat_runtime_implementation_hash() -> str:
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in (
        Path(__file__).resolve(), root / "interaction_gat_queue_v2.py",
        root / "qgr1_supervision.py", root / "proof_queue_label_state_gat.py",
        root / "proof_queue_label_state_gat_v3.py",
    ):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _exact_action_policy_hash(request):
    from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import qg2_exact_action_policy_hash_from_request
    return qg2_exact_action_policy_hash_from_request(request)


def _load_manifest(path):
    if not path.is_file():
        raise ValueError("Interaction-GAT manifest missing")
    key = f"{path}:{path.stat().st_mtime_ns}:{path.stat().st_size}"
    with _LOCK:
        if key not in _MANIFEST_CACHE:
            _MANIFEST_CACHE.clear()
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Interaction-GAT manifest is not an object")
            _MANIFEST_CACHE[key] = payload
        return _MANIFEST_CACHE[key]


def _resolve_checkpoint(manifest_path, value):
    path = Path(str(value))
    if not path.is_absolute():
        path = (manifest_path.parent / path).resolve()
    if not path.is_file():
        raise ValueError("checkpoint missing")
    return path


def _noop(reason, *, enabled=True):
    return {
        "proof_tail_interaction_gat_runtime_enabled": bool(enabled),
        "proof_tail_interaction_gat_manifest_read": False,
        "proof_tail_interaction_gat_graph_build_calls": 0,
        "proof_tail_interaction_gat_model_calls": 0,
        "proof_tail_interaction_gat_ranker_calls": 0,
        "proof_tail_interaction_gat_action": "Q0",
        "proof_tail_interaction_gat_decision_reason": str(reason),
        "proof_tail_interaction_gat_ood": False,
        "proof_tail_interaction_gat_graph_build_wall_ms": 0.0,
        "proof_tail_interaction_gat_tensorization_wall_ms": 0.0,
        "proof_tail_interaction_gat_checkpoint_load_wall_ms": 0.0,
        "proof_tail_interaction_gat_torch_first_import_wall_ms": 0.0,
        "proof_tail_interaction_gat_inference_wall_ms": 0.0,
        "proof_tail_interaction_gat_total_prepare_wall_ms": 0.0,
    }


def _after_noop(telemetry, reason):
    result = dict(telemetry)
    result.update({
        "proof_tail_interaction_gat_action": "Q0",
        "proof_tail_interaction_gat_decision_reason": str(reason),
    })
    return result


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
