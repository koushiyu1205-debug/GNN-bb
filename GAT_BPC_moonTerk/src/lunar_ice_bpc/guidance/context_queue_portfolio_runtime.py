"""Fail-closed runtime for P0V5 Context Queue Portfolio V1.

The public entry point deliberately imports neither Torch nor any tensor/model
module until a scale30/50 literal-Q0 V5 fallback request has passed the cheap
guards and its frozen manifest has been validated.  The selector may install
exactly one ordering-only arm.  Every failure returns the identical incoming
Q0 request object.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from math import exp, isfinite, log
import os
from pathlib import Path
import sys
from threading import RLock
from time import perf_counter
from typing import Any, Mapping


PORTFOLIO_MANIFEST_ENV = (
    "LUNAR_ICE_P0V5_CONTEXT_QUEUE_PORTFOLIO_V1_MANIFEST"
)
PORTFOLIO_EVALUATION_ENV = (
    "LUNAR_ICE_P0V5_CONTEXT_QUEUE_PORTFOLIO_V1_EVALUATION_MODE"
)
PORTFOLIO_MANIFEST_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_context_queue_portfolio_runtime_manifest.v1"
)
PORTFOLIO_RUNTIME_POLICY_V1 = (
    "p0v5_context_queue_portfolio_q0_qgr1_qd1_qb1_fail_closed.v1"
)
PORTFOLIO_ALLOWED_SCALES = frozenset({30, 50})
PORTFOLIO_ACTION_UNIVERSE = ("Q0", "QGR1", "QD1", "QB1")
QGR1_BUCKET_WIDTH = 1.0e-4
MAXIMUM_PARAMETER_COUNT = 50_000

_LOCK = RLock()
_MANIFEST_CACHE: dict[str, dict[str, Any]] = {}
_MODEL_CACHE: dict[str, tuple[Any, dict[str, Any], str]] = {}
_RANKER_CACHE: dict[str, tuple[Any, dict[str, Any], str]] = {}


def prepare_context_queue_portfolio_request_from_environment(request):
    """Return one selected action, or the identical incoming Q0 request.

    In particular, the first branch is the scale bypass.  It precedes even
    reading the manifest environment variable and is safe to exercise with an
    import spy for scale5/10/20.
    """

    scale = int(request.data.scale)
    if scale not in PORTFOLIO_ALLOWED_SCALES:
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
    if request.guidance_hints is not None or str(request.guidance_mode) != "off":
        return request, _noop("preexisting_guidance_bundle")
    if bool(request.dssr_enabled):
        return request, _noop("dssr_not_supported")

    started = perf_counter()
    try:
        return _prepare_after_cheap_guards(request, started=started)
    except Exception as exc:
        # A selector is never allowed to make the exact request unusable.
        # Preserve identity, not merely equality, so callers can audit literal
        # Q0 fallback without reconstructing a request.
        return request, {
            **_noop(f"portfolio_fail_closed:{type(exc).__name__}"),
            "proof_tail_portfolio_total_prepare_wall_ms": (
                perf_counter() - started
            ) * 1000.0,
        }


def _prepare_after_cheap_guards(request, *, started: float):
    manifest_value = str(os.getenv(PORTFOLIO_MANIFEST_ENV, "")).strip()
    if not manifest_value:
        return request, _noop("manifest_not_configured", enabled=False)
    manifest_path = Path(manifest_value).resolve()
    manifest = _load_manifest(manifest_path)
    _validate_manifest(request, manifest, manifest_path)
    scale = int(request.data.scale)
    if scale not in {int(value) for value in manifest["allowed_scales"]}:
        return request, _noop("scale_outside_manifest")

    evaluation = str(os.getenv(PORTFOLIO_EVALUATION_ENV, "0")).strip().lower()
    evaluation = evaluation in {"1", "true", "yes", "on"}
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

    # context_queue_portfolio_v1 imports Torch.  Measure and delay that import
    # until every cheap guard and immutable request/manifest binding has passed.
    torch_was_loaded = "torch" in sys.modules
    import_started = perf_counter()
    from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
    from lunar_ice_bpc.guidance.context_queue_portfolio_v1 import (
        PORTFOLIO_FEATURE_SCHEMA_V1,
        build_portfolio_features,
        portfolio_is_ood,
    )
    import_wall = perf_counter() - import_started
    first_import_wall = 0.0 if torch_was_loaded else import_wall

    tensor_started = perf_counter()
    features = build_portfolio_features(request)
    if str(features.schema_version) != str(manifest["feature_schema_version"]):
        return request, _noop("portfolio_feature_schema_drift")
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
    ood, ood_reason = portfolio_is_ood(
        features, dict(manifest["feature_envelope"])
    )
    if ood:
        return request, {
            **_noop(ood_reason),
            "proof_tail_portfolio_ood": True,
            "proof_tail_portfolio_feature_hash": feature_hash,
            "proof_tail_portfolio_torch_first_import_wall_ms": (
                first_import_wall * 1000.0
            ),
        }
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
        return request, _after_inference_noop(
            {}, "nonfinite_selector_output"
        )
    predictions = _predictions(
        output, checkpoint.get("probability_calibration")
    )
    action, decision_reason = _choose_action(
        predictions, manifest, scale=scale
    )
    manifest_hash = _sha256(manifest_path)
    telemetry = {
        "proof_tail_portfolio_runtime_enabled": True,
        "proof_tail_portfolio_action": action,
        "proof_tail_portfolio_decision_reason": decision_reason,
        "proof_tail_portfolio_model_kind": str(checkpoint["model_kind"]),
        "proof_tail_portfolio_ood": False,
        "proof_tail_portfolio_predictions": predictions,
        "proof_tail_portfolio_tensorization_wall_ms": tensor_wall * 1000.0,
        "proof_tail_portfolio_checkpoint_load_wall_ms": load_wall * 1000.0,
        "proof_tail_portfolio_torch_first_import_wall_ms": (
            first_import_wall * 1000.0
        ),
        "proof_tail_portfolio_inference_wall_ms": inference_wall * 1000.0,
        "proof_tail_portfolio_total_prepare_wall_ms": (
            perf_counter() - started
        ) * 1000.0,
        "proof_tail_portfolio_feature_hash": feature_hash,
        "proof_tail_portfolio_manifest_sha256": manifest_hash,
        "proof_tail_portfolio_checkpoint_sha256": checkpoint_hash,
        "proof_tail_portfolio_exact_action_policy_hash": (
            exact_action_policy_hash
        ),
    }
    if action == "Q0":
        return request, telemetry
    if action == "QGR1":
        return _install_qgr1_action(
            request,
            manifest_path=manifest_path,
            manifest=manifest,
            portfolio_features=features,
            feature_hash=feature_hash,
            exact_action_policy_hash=exact_action_policy_hash,
            selector_checkpoint_hash=checkpoint_hash,
            selector_inference_wall=inference_wall,
            telemetry=telemetry,
        )

    config_hash = stable_payload_hash({
        "schema_version": (
            "lunar_ice_bpc.p0v5_context_queue_portfolio_config.v1"
        ),
        "source_exact_config_hash": str(request.config_hash),
        "exact_action_policy_hash": exact_action_policy_hash,
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
            ("proof_tail_portfolio_action", action),
            ("proof_tail_portfolio_manifest_sha256", manifest_hash),
            ("proof_tail_portfolio_checkpoint_sha256", checkpoint_hash),
            ("proof_tail_portfolio_feature_hash", feature_hash),
            ("proof_tail_portfolio_inference_sec", inference_wall),
        ),
    )
    return selected, {
        **telemetry,
        "proof_tail_portfolio_config_hash": config_hash,
    }


def _install_qgr1_action(
    request,
    *,
    manifest_path,
    manifest,
    portfolio_features,
    feature_hash,
    exact_action_policy_hash,
    selector_checkpoint_hash,
    selector_inference_wall,
    telemetry,
):
    """Load the label ranker only after QGR1 wins every selector gate."""

    import torch
    from lunar_ice_bpc.exact.bpc.guidance.contracts import (
        CanonicalSolveBindingV2,
        GUIDANCE_MODE_TASK_ARC,
        PricingOrderingHintsV2,
    )
    from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
        QG2Features,
        QG2_FEATURE_SCHEMA_V1,
        QG2_LABEL_STATE_SCHEMA_V1,
        QG2_CONTEXT_FEATURES,
        normalize_qg2_potential_groups,
    )
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
        QG2_V3_INPUT_FEATURE_SCHEMA,
    )
    from lunar_ice_bpc.guidance.qgr1_supervision import (
        QGR1_ACTION_SURFACE_V1,
        QGR1_SUPERVISION_SCHEMA_V1,
    )

    if str(manifest.get("qgr1_label_state_schema_version") or "") != (
        QG2_LABEL_STATE_SCHEMA_V1
    ):
        return request, _after_inference_noop(
            telemetry, "qgr1_label_state_schema_mismatch"
        )
    if float(manifest.get("qgr1_guidance_bucket_width") or 0.0) != (
        QGR1_BUCKET_WIDTH
    ):
        return request, _after_inference_noop(
            telemetry, "qgr1_bucket_is_not_frozen_1e-4"
        )
    load_started = perf_counter()
    try:
        ranker, metadata, ranker_hash = _load_ranker(
            manifest_path, manifest
        )
    except Exception as exc:
        return request, _after_inference_noop(
            telemetry, f"qgr1_ranker_load_failed:{type(exc).__name__}"
        )
    ranker_load_wall = perf_counter() - load_started
    if (
        str(getattr(ranker, "model_kind", "")) != "gat"
        or bool(metadata.get("activation_authority"))
        or metadata.get("supervision_schema_version")
        != QGR1_SUPERVISION_SCHEMA_V1
        or metadata.get("queue_action_surface") != QGR1_ACTION_SURFACE_V1
    ):
        return request, _after_inference_noop(
            telemetry, "qgr1_ranker_ordering_only_contract_mismatch"
        )

    # The QGR1 ranker deliberately reuses the pre-existing node/arc/15-state
    # architecture.  It receives the original 27 context dimensions, while
    # the context selector receives the six new Q0-only pressure features.
    ranker_features = QG2Features(
        instance_content_hash=portfolio_features.instance_content_hash,
        task_ids=portfolio_features.task_ids,
        arc_candidate_ids=portfolio_features.arc_candidate_ids,
        node_features=portfolio_features.node_features,
        edge_index=portfolio_features.edge_index,
        edge_features=portfolio_features.edge_features,
        context_features=tuple(portfolio_features.context_features[
            :len(QG2_CONTEXT_FEATURES)
        ]),
        schema_version=QG2_V3_INPUT_FEATURE_SCHEMA,
    )
    ranker_tensors = ranker_features.to_tensors()
    inference_started = perf_counter()
    with torch.inference_mode():
        output = ranker(**ranker_tensors)
        coefficients = output["label_state_coefficients"].reshape(-1)
    ranker_inference_wall = perf_counter() - inference_started
    raw = (output["node_scores"], output["arc_scores"], coefficients)
    if any(not bool(value.isfinite().all()) for value in raw):
        return request, _after_inference_noop(
            telemetry, "qgr1_ranker_nonfinite_output"
        )
    if int(coefficients.numel()) != 15:
        return request, _after_inference_noop(
            telemetry, "qgr1_ranker_state_dimension"
        )
    node, arc, coefficients = normalize_qg2_potential_groups(
        output["node_scores"][1:].reshape(-1),
        output["arc_scores"].reshape(-1),
        coefficients,
    )
    values = (*node.tolist(), *arc.tolist(), *coefficients.tolist())
    if (
        not values
        or any(not isfinite(float(value)) for value in values)
        or max(abs(float(value)) for value in values) <= 1.0e-12
    ):
        return request, _after_inference_noop(
            telemetry, "qgr1_ranker_zero_or_invalid_potential"
        )

    manifest_hash = _sha256(manifest_path)
    source_config_hash = str(request.config_hash)
    config_hash = stable_payload_hash({
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_selector_config.v1",
        "source_exact_config_hash": source_config_hash,
        "exact_action_policy_hash": exact_action_policy_hash,
        "manifest_sha256": manifest_hash,
        "selector_checkpoint_sha256": selector_checkpoint_hash,
        "ranker_checkpoint_sha256": ranker_hash,
        "input_feature_hash": feature_hash,
        "proof_queue_policy_id": "QGR1",
        "guidance_bucket_width": QGR1_BUCKET_WIDTH,
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
        guidance_normalization_version=(
            "train_zscore_input_global_maxabs_output.qgr1.v1"
        ),
        guidance_checkpoint_id=ranker_hash,
        guidance_ood_policy_version="per_feature_train_envelope.5pct.v1",
        guidance_lifecycle_telemetry=(
            ("proof_tail_portfolio_action", "QGR1"),
            ("proof_tail_portfolio_manifest_sha256", manifest_hash),
            ("proof_tail_portfolio_checkpoint_sha256", selector_checkpoint_hash),
            ("proof_tail_portfolio_feature_hash", feature_hash),
            ("proof_tail_portfolio_inference_sec", selector_inference_wall),
            ("proof_tail_portfolio_qgr1_ranker_checkpoint_sha256", ranker_hash),
            ("proof_tail_portfolio_qgr1_ranker_load_sec", ranker_load_wall),
            ("proof_tail_portfolio_qgr1_ranker_inference_sec", ranker_inference_wall),
            ("proof_tail_portfolio_exact_action_policy_hash", exact_action_policy_hash),
        ),
    )
    binding = CanonicalSolveBindingV2.from_backend_request(enriched)
    hints = PricingOrderingHintsV2(
        binding_hash=binding.binding_hash,
        task_priorities=tuple(
            (task_id, float(value))
            for task_id, value in zip(
                portfolio_features.task_ids, node.tolist(), strict=True
            )
        ),
        arc_priorities=tuple(
            (arc_id, float(value))
            for arc_id, value in zip(
                portfolio_features.arc_candidate_ids, arc.tolist(), strict=True
            )
        ),
        label_state_coefficients=tuple(
            float(value) for value in coefficients.tolist()
        ),
        label_state_schema_version=QG2_LABEL_STATE_SCHEMA_V1,
        queue_policy_id="Q0",
        uncertainty=0.0,
        ood=False,
        source="p0v5_context_queue_portfolio_qgr1_depth_residual_gat",
        diagnostic_only=True,
    )
    total = dict(telemetry)
    total.update({
        "proof_tail_portfolio_action": "QGR1",
        "proof_tail_portfolio_decision_reason": (
            "risk_adjusted_selector_qgr1_ranker"
        ),
        "proof_tail_portfolio_qgr1_ranker_checkpoint_sha256": ranker_hash,
        "proof_tail_portfolio_qgr1_ranker_load_wall_ms": (
            ranker_load_wall * 1000.0
        ),
        "proof_tail_portfolio_qgr1_ranker_inference_wall_ms": (
            ranker_inference_wall * 1000.0
        ),
        "proof_tail_portfolio_config_hash": config_hash,
    })
    return replace(enriched, guidance_hints=hints), total


def context_queue_portfolio_runtime_implementation_hash() -> str:
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in (
        Path(__file__).resolve(),
        root / "context_queue_portfolio_v1.py",
        root / "qgr1_supervision.py",
        root / "proof_queue_label_state_gat.py",
        root / "proof_queue_label_state_gat_v3.py",
    ):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _predictions(
    output: Mapping[str, Any], calibration: Mapping[str, object] | None = None
) -> dict[str, dict[str, float]]:
    calibration = dict(calibration or {})
    benefit_calibration = dict(calibration.get("benefit") or {})
    adverse_calibration = dict(calibration.get("adverse") or {})
    gain_scale = dict(calibration.get("positive_gain_scale") or {})
    result = {}
    for index, arm in enumerate(("QGR1", "QD1", "QB1")):
        probability = _calibrated_probability(
            float(output["benefit_probability"][0, index]),
            benefit_calibration.get(arm),
        )
        gain = float(output["conditional_positive_gain"][0, index]) * float(
            gain_scale.get(arm, 1.0)
        )
        adverse = _calibrated_probability(
            float(output["adverse_probability"][0, index]),
            adverse_calibration.get(arm),
        )
        if any(not isfinite(value) for value in (probability, gain, adverse)):
            raise ValueError("portfolio selector emitted NaN/Inf")
        result[arm] = {
            "benefit_probability": probability,
            "conditional_positive_gain": gain,
            "expected_gain": probability * gain,
            "adverse_probability": adverse,
        }
    return result


def _calibrated_probability(value: float, row: object) -> float:
    probability = min(1.0 - 1.0e-7, max(1.0e-7, float(value)))
    if not row:
        return probability
    values = dict(row)
    slope = float(values.get("slope", 1.0))
    intercept = float(values.get("intercept", 0.0))
    if not isfinite(slope) or not isfinite(intercept) or slope < 0.0:
        raise ValueError("portfolio probability calibration is invalid")
    logit = log(probability / (1.0 - probability))
    calibrated_logit = max(-40.0, min(40.0, slope * logit + intercept))
    return 1.0 / (1.0 + exp(-calibrated_logit))


def _choose_action(predictions, manifest, *, scale: int):
    thresholds = dict(manifest.get("thresholds") or {})
    probability = float(thresholds.get("minimum_benefit_probability", 2.0))
    expected_gain = float(thresholds.get("minimum_expected_gain", float("inf")))
    adverse = float(thresholds.get("maximum_adverse_probability", -1.0))
    penalty = float(thresholds.get("risk_penalty", -1.0))
    if (
        any(not isfinite(v) for v in (probability, expected_gain, adverse, penalty))
        or not 0.0 <= probability <= 1.0
        or expected_gain < 0.0
        or not 0.0 <= adverse <= 1.0
        or penalty < 0.0
    ):
        return "Q0", "invalid_thresholds"
    masks = {
        str(arm): {int(value) for value in scales}
        for arm, scales in dict(manifest.get("arm_scale_mask") or {}).items()
    }
    veto = set(manifest.get("forced_veto_arms") or ())
    veto.update(
        dict(manifest.get("forced_veto_arms_by_scale") or {}).get(
            str(int(scale)), ()
        )
    )
    eligible = []
    action_universe = tuple(manifest.get("action_universe") or ())
    for arm in ("QGR1", "QD1", "QB1"):
        row = predictions[arm]
        if (
            arm not in action_universe
            or arm in veto
            or scale not in masks.get(arm, set())
            or row["benefit_probability"] < probability
            or row["expected_gain"] < expected_gain
            or row["adverse_probability"] > adverse
        ):
            continue
        score = row["expected_gain"] - penalty * row["adverse_probability"]
        if score > 0.0:
            eligible.append((score, arm))
    if not eligible:
        return "Q0", "all_arms_rejected"
    return max(eligible, key=lambda row: (row[0], row[1]))[1], (
        "risk_adjusted_selector"
    )


def _validate_manifest(request, manifest, path):
    errors = []
    if manifest.get("schema_version") != PORTFOLIO_MANIFEST_SCHEMA_V1:
        errors.append("manifest_schema_mismatch")
    if manifest.get("runtime_policy_id") != PORTFOLIO_RUNTIME_POLICY_V1:
        errors.append("runtime_policy_mismatch")
    if manifest.get("runtime_implementation_hash") != (
        context_queue_portfolio_runtime_implementation_hash()
    ):
        errors.append("runtime_implementation_drift")
    if tuple(manifest.get("action_universe") or ()) != PORTFOLIO_ACTION_UNIVERSE:
        errors.append("action_universe_mismatch")
    if str(manifest.get("fallback_action") or "") != "Q0":
        errors.append("literal_q0_fallback_missing")
    allowed = {int(value) for value in manifest.get("allowed_scales") or ()}
    if not allowed or not allowed.issubset(PORTFOLIO_ALLOWED_SCALES):
        errors.append("allowed_scales_invalid")
    masks = dict(manifest.get("arm_scale_mask") or {})
    if set(masks) != {"QGR1", "QD1", "QB1"}:
        errors.append("arm_scale_mask_invalid")
    elif any(
        not {int(value) for value in values}.issubset(allowed)
        for values in masks.values()
    ):
        errors.append("arm_scale_mask_outside_allowed_scales")
    if not all((request.instance_hash, request.config_hash, request.engine_hash)):
        errors.append("exact_request_binding_incomplete")
    for field in (
        "selector_checkpoint_path",
        "selector_checkpoint_sha256",
        "feature_schema_version",
        "feature_envelope",
    ):
        if not manifest.get(field):
            errors.append(f"{field}_missing")
    if "QGR1" not in set(manifest.get("forced_veto_arms") or ()) and any(
        30 in {int(v) for v in masks.get("QGR1", ())}
        or 50 in {int(v) for v in masks.get("QGR1", ())}
        for _ in (0,)
    ):
        for field in (
            "qgr1_ranker_checkpoint_path",
            "qgr1_ranker_checkpoint_sha256",
            "qgr1_guidance_bucket_width",
            "qgr1_label_state_schema_version",
        ):
            if not manifest.get(field):
                errors.append(f"{field}_missing")
    if errors:
        raise ValueError(
            "Context Queue Portfolio manifest invalid:" + ",".join(errors)
        )


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError("Context Queue Portfolio manifest missing")
    key = f"{path}:{path.stat().st_mtime_ns}:{path.stat().st_size}"
    with _LOCK:
        if key not in _MANIFEST_CACHE:
            _MANIFEST_CACHE.clear()
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("portfolio manifest is not an object")
            _MANIFEST_CACHE[key] = payload
        return _MANIFEST_CACHE[key]


def _load_model(manifest_path, manifest):
    checkpoint_path = _resolve_checkpoint(
        manifest_path, manifest["selector_checkpoint_path"]
    )
    checkpoint_hash = _sha256(checkpoint_path)
    if checkpoint_hash != str(manifest["selector_checkpoint_sha256"]):
        raise ValueError("portfolio selector checkpoint hash mismatch")
    key = f"{checkpoint_path}:{checkpoint_hash}"
    with _LOCK:
        if key in _MODEL_CACHE:
            return _MODEL_CACHE[key]
        import torch
        from lunar_ice_bpc.guidance.context_queue_portfolio_v1 import (
            PORTFOLIO_ACTION_UNIVERSE,
            PORTFOLIO_CHECKPOINT_SCHEMA_V1,
            PORTFOLIO_FEATURE_SCHEMA_V1,
            PORTFOLIO_INPUT_PARITY_CONTRACT_V1,
            PortfolioGATSelector,
            PortfolioLinearSelector,
            PortfolioMLPSelector,
            portfolio_parameter_count,
        )
        checkpoint = torch.load(
            checkpoint_path, map_location="cpu", weights_only=False
        )
        if checkpoint.get("schema_version") != PORTFOLIO_CHECKPOINT_SCHEMA_V1:
            raise ValueError("portfolio checkpoint schema mismatch")
        if checkpoint.get("feature_schema_version") != PORTFOLIO_FEATURE_SCHEMA_V1:
            raise ValueError("portfolio checkpoint feature schema mismatch")
        if checkpoint.get("input_parity_contract") != (
            PORTFOLIO_INPUT_PARITY_CONTRACT_V1
        ):
            raise ValueError("portfolio input parity mismatch")
        if tuple(checkpoint.get("action_universe") or ()) != (
            PORTFOLIO_ACTION_UNIVERSE
        ):
            raise ValueError("portfolio checkpoint action universe mismatch")
        kind = str(checkpoint.get("model_kind") or "")
        model_class = {
            "gat": PortfolioGATSelector,
            "mlp": PortfolioMLPSelector,
            "linear": PortfolioLinearSelector,
        }.get(kind)
        if model_class is None or kind != str(manifest.get("model_kind") or ""):
            raise ValueError("portfolio selector model kind mismatch")
        model = model_class(dict(checkpoint["normalization"]))
        model.load_state_dict(checkpoint["state_dict"], strict=True)
        if portfolio_parameter_count(model) > MAXIMUM_PARAMETER_COUNT:
            raise ValueError("portfolio selector exceeds 50k parameters")
        model.eval()
        _MODEL_CACHE.clear()
        _MODEL_CACHE[key] = (model, dict(checkpoint), checkpoint_hash)
        return _MODEL_CACHE[key]


def _load_ranker(manifest_path, manifest):
    checkpoint_path = _resolve_checkpoint(
        manifest_path, manifest["qgr1_ranker_checkpoint_path"]
    )
    checkpoint_hash = _sha256(checkpoint_path)
    if checkpoint_hash != str(manifest["qgr1_ranker_checkpoint_sha256"]):
        raise ValueError("QGR1 ranker checkpoint hash mismatch")
    key = f"{checkpoint_path}:{checkpoint_hash}"
    with _LOCK:
        if key in _RANKER_CACHE:
            return _RANKER_CACHE[key]
        from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
            load_qg2_v3_checkpoint,
        )
        model, metadata, _normalization = load_qg2_v3_checkpoint(
            str(checkpoint_path)
        )
        _RANKER_CACHE.clear()
        _RANKER_CACHE[key] = (model, metadata, checkpoint_hash)
        return _RANKER_CACHE[key]


def _resolve_checkpoint(manifest_path, value) -> Path:
    path = Path(str(value))
    if not path.is_absolute():
        path = (Path(manifest_path).parent / path).resolve()
    if not path.is_file():
        raise ValueError("portfolio checkpoint missing")
    return path


def _exact_action_policy_hash(request):
    from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
        qg2_exact_action_policy_hash_from_request,
    )
    return qg2_exact_action_policy_hash_from_request(request)


def _noop(reason, *, enabled=True):
    return {
        "proof_tail_portfolio_runtime_enabled": bool(enabled),
        "proof_tail_portfolio_action": "Q0",
        "proof_tail_portfolio_decision_reason": str(reason),
        "proof_tail_portfolio_ood": False,
        "proof_tail_portfolio_tensorization_wall_ms": 0.0,
        "proof_tail_portfolio_checkpoint_load_wall_ms": 0.0,
        "proof_tail_portfolio_torch_first_import_wall_ms": 0.0,
        "proof_tail_portfolio_inference_wall_ms": 0.0,
        "proof_tail_portfolio_total_prepare_wall_ms": 0.0,
    }


def _after_inference_noop(telemetry, reason, **extra):
    result = dict(telemetry)
    result.update({
        "proof_tail_portfolio_runtime_enabled": True,
        "proof_tail_portfolio_action": "Q0",
        "proof_tail_portfolio_decision_reason": str(reason),
        "proof_tail_portfolio_ood": False,
        **extra,
    })
    return result


def _sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
