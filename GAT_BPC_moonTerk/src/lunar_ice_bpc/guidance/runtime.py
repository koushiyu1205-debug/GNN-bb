"""Lazy, fail-closed runtime that produces exact-side ordering hints."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, replace
import hashlib
from math import isfinite, log1p
from pathlib import Path
import os
import sys
from threading import RLock
from time import perf_counter
from typing import Any, Iterable, Mapping

from lunar_ice_bpc.exact.bpc.guidance.contracts import (
    CanonicalSolveBindingV2,
    GuidanceLifecycleTelemetry,
    PricingOrderingHintsV2,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.base import BackendPricingRequest
from lunar_ice_bpc.guidance.deployment import (
    DeploymentEligibilityManifest,
    GuidanceEntryDecision,
    ROUTE_HARVEST_SINGLE_PROMOTION_SCOPE,
    decide_guidance_entry,
)
from lunar_ice_bpc.guidance.trajectory_targets import (
    COUNTERFACTUAL_TRAINING_OBJECTIVE_V2,
    FIXED_POOL_PRICING_PRESSURE_OBJECTIVE_SPEC_V1,
)
from lunar_ice_bpc.guidance.tensorization import (
    DYNAMIC_NODE_FEATURES,
    EDGE_STATIC_FEATURES,
    HARVEST_MODEL_CONTEXT_SCHEMA_V2,
    NODE_STATIC_FEATURES,
    build_static_graph_features,
    dynamic_node_features,
    encode_queue_policy_id,
    learned_harvest_context,
)


@dataclass(frozen=True)
class GuidancePreparation:
    request: BackendPricingRequest
    decision: GuidanceEntryDecision
    telemetry: dict[str, Any]
    diagnostics: dict[str, Any]


_MODEL_CACHE: dict[tuple[str, int, int, str], tuple[Any, dict[str, Any]]] = {}
_TENSOR_CACHE_LOCK = RLock()
_TENSOR_CACHE: OrderedDict[tuple[str, str, str], dict[str, Any]] = (
    OrderedDict()
)
_TENSOR_CACHE_MAX_ENTRIES = 32
DEPLOYMENT_MANIFEST_ENV = "LUNAR_ICE_GAT_DEPLOYMENT_MANIFEST"
GUIDANCE_MODE_ENV = "LUNAR_ICE_GAT_GUIDANCE_MODE"


def prepare_guidance_request_from_environment(
    request: BackendPricingRequest,
    *,
    stage: str,
    harvest_candidates: Iterable[Mapping[str, Any]] = tuple(),
) -> GuidancePreparation | None:
    """Apply the explicit experiment manifest, or leave P0 untouched.

    Merely installing a checkpoint never enables guidance. Both environment
    variables are required, and exact-proof requests are never routed through
    the learning runtime. The task/arc hook accepts ``task_arc`` or ``shadow``;
    the harvest hook accepts ``harvest``, ``task_arc`` (HA), or ``shadow``.
    """

    manifest_path = str(os.getenv(DEPLOYMENT_MANIFEST_ENV, "")).strip()
    requested = str(os.getenv(GUIDANCE_MODE_ENV, "")).strip()
    normalized_stage = str(stage)
    if not manifest_path or not requested:
        return None
    if request.exact_proof_mode:
        return None
    if request.guidance_hints is not None or request.guidance_mode != "off":
        return None
    allowed = {
        "task_arc": {"task_arc", "shadow"},
        "harvest": {"harvest", "task_arc", "shadow"},
    }
    if normalized_stage not in allowed:
        raise ValueError(f"unsupported guidance runtime stage {stage!r}")
    if requested not in allowed[normalized_stage]:
        return None
    effective_request_mode = (
        "harvest"
        if normalized_stage == "harvest" and requested == "task_arc"
        else requested
    )
    try:
        manifest = DeploymentEligibilityManifest.load(manifest_path)
    except Exception as exc:
        telemetry = GuidanceLifecycleTelemetry(
            bypassed_before_import=True,
            bypass_reason="deployment_manifest_load_failed",
        )
        decision = GuidanceEntryDecision(
            status="CHECKPOINT_AVAILABLE_BUT_GUIDANCE_BYPASSED",
            requested_mode=effective_request_mode,
            effective_mode="off",
            scale=request.data.scale,
            import_learning_runtime=False,
            reason="deployment_manifest_load_failed",
        )
        payload = telemetry.to_payload()
        return GuidancePreparation(
            request=replace(
                request,
                guidance_lifecycle_telemetry=tuple(payload.items()),
            ),
            decision=decision,
            telemetry=payload,
            diagnostics={
                "guidance_fallback_to_p0": True,
                "reason": "deployment_manifest_load_failed",
                "error": repr(exc),
                "torch_imported": "torch" in sys.modules,
            },
        )
    return prepare_guidance_request(
        request,
        manifest=manifest,
        requested_mode=effective_request_mode,
        harvest_candidates=harvest_candidates,
    )


def prepare_guidance_request(
    request: BackendPricingRequest,
    *,
    manifest: DeploymentEligibilityManifest,
    requested_mode: str,
    harvest_candidates: Iterable[Mapping[str, Any]] = tuple(),
) -> GuidancePreparation:
    """Attach a bound hint bundle or return an unchanged P0 request.

    The deployment decision happens before the first import of torch or the
    model module.  Any load, schema, OOD, NaN, or inference failure falls back
    to P0 as one atomic bundle.
    """

    telemetry = GuidanceLifecycleTelemetry()
    candidate_rows = tuple(dict(row) for row in harvest_candidates)
    decision = decide_guidance_entry(
        manifest,
        scale=request.data.scale,
        requested_mode=requested_mode,
    )
    if not decision.import_learning_runtime:
        telemetry.bypassed_before_import = True
        telemetry.bypass_reason = decision.reason
        return GuidancePreparation(
            request=replace(
                request,
                guidance_mode="off",
                guidance_hints=None,
                guidance_lifecycle_telemetry=tuple(
                    telemetry.to_payload().items()
                ),
            ),
            decision=decision,
            telemetry=telemetry.to_payload(),
            diagnostics={
                "checkpoint_available_but_guidance_bypassed": True,
                "torch_imported": "torch" in sys.modules,
                "reason": decision.reason,
            },
        )

    binding_validation_started = perf_counter()
    if (
        not request.engine_hash
        or str(request.engine_hash)
        != manifest.expected_engine_hash(request.data.scale)
    ):
        telemetry.guidance_binding_validation_sec = (
            perf_counter() - binding_validation_started
        )
        telemetry.bypassed_before_import = True
        telemetry.bypass_reason = "exact_engine_hash_mismatch"
        payload = telemetry.to_payload()
        return GuidancePreparation(
            request=replace(
                request,
                guidance_mode="off",
                guidance_hints=None,
                guidance_lifecycle_telemetry=tuple(payload.items()),
            ),
            decision=GuidanceEntryDecision(
                status="CHECKPOINT_AVAILABLE_BUT_GUIDANCE_BYPASSED",
                requested_mode=str(requested_mode),
                effective_mode="off",
                scale=request.data.scale,
                import_learning_runtime=False,
                reason="exact_engine_hash_mismatch",
            ),
            telemetry=payload,
            diagnostics={
                "checkpoint_available_but_guidance_bypassed": True,
                "torch_imported": "torch" in sys.modules,
                "reason": "exact_engine_hash_mismatch",
            },
        )
    telemetry.guidance_binding_validation_sec = (
        perf_counter() - binding_validation_started
    )

    if requested_mode == "harvest":
        cheap_gate_started = perf_counter()
        try:
            candidate_count = len(candidate_rows)
            negative_mass = sum(
                max(
                    0.0,
                    -float(tuple(row.get("context") or (0.0,))[0]),
                )
                for row in candidate_rows
            )
            if not isfinite(negative_mass):
                raise ValueError("cheap-gate negative mass is non-finite")
            minimum_count = manifest.minimum_harvest_candidates(
                request.data.scale
            )
            minimum_mass = manifest.minimum_harvest_negative_mass(
                request.data.scale
            )
            cheap_gate_eligible = bool(
                candidate_count >= minimum_count
                and negative_mass >= minimum_mass
            )
        except Exception as exc:
            telemetry.guidance_cheap_gate_sec = (
                perf_counter() - cheap_gate_started
            )
            telemetry.cheap_gate_eligible = False
            telemetry.bypassed_before_import = True
            telemetry.bypass_reason = "cheap_gate_input_invalid"
            payload = telemetry.to_payload()
            return GuidancePreparation(
                request=replace(
                    request,
                    guidance_mode="off",
                    guidance_hints=None,
                    guidance_lifecycle_telemetry=tuple(payload.items()),
                ),
                decision=GuidanceEntryDecision(
                    status="CHECKPOINT_AVAILABLE_BUT_GUIDANCE_BYPASSED",
                    requested_mode=str(requested_mode),
                    effective_mode="off",
                    scale=request.data.scale,
                    import_learning_runtime=False,
                    reason="cheap_gate_input_invalid",
                ),
                telemetry=payload,
                diagnostics={
                    "checkpoint_available_but_guidance_bypassed": True,
                    "torch_imported": "torch" in sys.modules,
                    "reason": "cheap_gate_input_invalid",
                    "error": repr(exc),
                },
            )
        telemetry.guidance_cheap_gate_sec = (
            perf_counter() - cheap_gate_started
        )
        telemetry.cheap_gate_eligible = cheap_gate_eligible
        telemetry.cheap_gate_candidate_count = candidate_count
        telemetry.cheap_gate_negative_mass = negative_mass
        if not cheap_gate_eligible:
            reason = (
                "cheap_gate_too_few_legal_harvest_candidates"
                if candidate_count < minimum_count
                else "cheap_gate_insufficient_negative_mass"
            )
            telemetry.bypassed_before_import = True
            telemetry.bypass_reason = reason
            payload = telemetry.to_payload()
            return GuidancePreparation(
                request=replace(
                    request,
                    guidance_mode="off",
                    guidance_hints=None,
                    guidance_lifecycle_telemetry=tuple(payload.items()),
                ),
                decision=GuidanceEntryDecision(
                    status="CHECKPOINT_AVAILABLE_BUT_GUIDANCE_BYPASSED",
                    requested_mode=str(requested_mode),
                    effective_mode="off",
                    scale=request.data.scale,
                    import_learning_runtime=False,
                    reason=reason,
                ),
                telemetry=payload,
                diagnostics={
                    "checkpoint_available_but_guidance_bypassed": True,
                    "torch_imported": "torch" in sys.modules,
                    "reason": reason,
                    "cheap_gate_policy_version": (
                        manifest.cheap_gate_policy_version
                    ),
                    "minimum_harvest_candidate_count": minimum_count,
                    "minimum_harvest_negative_mass": minimum_mass,
                },
            )

    import_started = perf_counter()
    try:
        import torch

        torch.set_num_threads(int(manifest.torch_num_threads))
        torch.use_deterministic_algorithms(
            bool(manifest.deterministic_inference)
        )
        from lunar_ice_bpc.guidance.models import load_checkpoint
    except Exception as exc:
        telemetry.guidance_import_sec = perf_counter() - import_started
        telemetry.bypassed_before_import = False
        telemetry.bypass_reason = "learning_runtime_import_failed"
        return _failed_preparation(
            request,
            decision,
            telemetry,
            reason="learning_runtime_import_failed",
            error=repr(exc),
        )
    telemetry.guidance_import_sec = perf_counter() - import_started

    enriched = replace(
        request,
        guidance_mode=str(requested_mode),
        guidance_feature_schema_version=manifest.feature_schema_version,
        guidance_normalization_version=manifest.normalization_version,
        guidance_checkpoint_id=manifest.checkpoint_id,
        guidance_ood_policy_version=manifest.ood_policy_version,
    )
    load_started = perf_counter()
    try:
        checkpoint_path = Path(manifest.checkpoint_path).resolve()
        stat = checkpoint_path.stat()
        cache_key = (
            str(checkpoint_path),
            int(stat.st_mtime_ns),
            int(stat.st_size),
            manifest.checkpoint_id,
        )
        cached = _MODEL_CACHE.get(cache_key)
        if cached is None:
            if manifest.checkpoint_sha256:
                actual_checkpoint_hash = _sha256_file(checkpoint_path)
                if actual_checkpoint_hash != manifest.checkpoint_sha256:
                    raise ValueError("checkpoint content hash mismatch")
            cached = load_checkpoint(str(checkpoint_path), map_location="cpu")
            _MODEL_CACHE.clear()
            _MODEL_CACHE[cache_key] = cached
        model, metadata = cached
        if str(getattr(model, "kind", "")) != manifest.model_kind:
            raise ValueError("checkpoint model kind mismatch")
        _validate_checkpoint_metadata(metadata, manifest)
    except Exception as exc:
        telemetry.guidance_checkpoint_load_sec = (
            perf_counter() - load_started
        )
        return _failed_preparation(
            enriched,
            decision,
            telemetry,
            reason="checkpoint_load_or_metadata_failed",
            error=repr(exc),
        )
    telemetry.guidance_checkpoint_load_sec = perf_counter() - load_started

    tensor_started = perf_counter()
    try:
        static = build_static_graph_features(request.data)
        (
            node_tensor,
            edge_tensor,
            edge_index,
            task_indices,
            ood,
            ood_diagnostics,
        ) = _cached_request_tensors(
            request,
            static=static,
            metadata=metadata,
            manifest=manifest,
            torch=torch,
        )
        resource_context = torch.tensor(
            (
                log1p(max(0.0, request.memory_limit_gb) * (1024.0**3)),
                log1p(
                    0.0
                    if request.wall_time_limit_sec is None
                    else max(0.0, request.wall_time_limit_sec)
                ),
                1.0 if request.mode == "exact_proof" else 0.0,
                encode_queue_policy_id("Q0"),
            ),
            dtype=torch.float32,
        )
        harvest_masks, harvest_context = _harvest_tensors(
            candidate_rows,
            static.node_ids,
            torch=torch,
        )
    except Exception as exc:
        telemetry.guidance_tensorize_sec = perf_counter() - tensor_started
        return _failed_preparation(
            enriched,
            decision,
            telemetry,
            reason="tensorization_or_ood_failed",
            error=repr(exc),
        )
    telemetry.guidance_tensorize_sec = perf_counter() - tensor_started

    forward_started = perf_counter()
    try:
        with torch.inference_mode():
            output = model(
                node_features=node_tensor,
                edge_index=edge_index,
                edge_features=edge_tensor,
                task_node_indices=task_indices,
                resource_context=resource_context,
                harvest_task_masks=harvest_masks,
                harvest_context=harvest_context,
            )
        task_scores = tuple(float(value) for value in output["task_scores"])
        arc_scores = tuple(float(value) for value in output["arc_scores"])
        trained_shadow_heads = {
            str(value)
            for value in metadata.get("trained_shadow_heads", ())
        }
        proof_tail_risk = (
            float(output["proof_tail_risk"])
            if "proof_risk" in trained_shadow_heads
            else None
        )
        harvest_scores = tuple(
            float(value) for value in output.get("harvest_scores", ())
        )
        harvest_noop_score = float(output["harvest_noop_score"])
        all_scores = (
            *task_scores,
            *arc_scores,
            *harvest_scores,
            harvest_noop_score,
            *(() if proof_tail_risk is None else (proof_tail_risk,)),
        )
        if any(not isfinite(value) for value in all_scores):
            raise ValueError("model emitted NaN/Inf guidance")
    except Exception as exc:
        telemetry.guidance_forward_total_sec = (
            perf_counter() - forward_started
        )
        return _failed_preparation(
            enriched,
            decision,
            telemetry,
            reason="forward_failed_or_nonfinite",
            error=repr(exc),
        )
    telemetry.guidance_forward_total_sec = perf_counter() - forward_started
    telemetry.guidance_call_count = 1

    binding_started = perf_counter()
    binding = CanonicalSolveBindingV2.from_backend_request(
        enriched,
        feature_schema_version=manifest.feature_schema_version,
        normalization_version=manifest.normalization_version,
        checkpoint_id=manifest.checkpoint_id,
        ood_policy_version=manifest.ood_policy_version,
    )
    telemetry.guidance_binding_validation_sec += perf_counter() - binding_started
    online_harvest = requested_mode == "harvest"
    selected_harvest_id: str | None = None
    abstention_reason = ""
    harvest_priorities: tuple[tuple[str, float], ...]
    if online_harvest:
        scored_candidates = tuple(
            (str(row["candidate_id"]), float(score))
            for row, score in zip(
                candidate_rows, harvest_scores, strict=True
            )
        )
        if not scored_candidates:
            harvest_priorities = tuple()
            abstention_reason = "no_legal_harvest_candidates"
        else:
            best_candidate_id, best_candidate_score = min(
                scored_candidates,
                key=lambda item: (-item[1], item[0]),
            )
            if best_candidate_score <= harvest_noop_score:
                harvest_priorities = tuple()
                abstention_reason = (
                    "p0_noop_score_not_lower_than_best_promotion"
                )
            else:
                selected_harvest_id = best_candidate_id
                # Only the selected route receives a positive priority.  The
                # exact selector retains every legal route and its P0
                # deterministic tie-break for all remaining candidates.
                harvest_priorities = (
                    (
                        best_candidate_id,
                        best_candidate_score - harvest_noop_score,
                    ),
                )
    else:
        # Shadow mode records full predictions but cannot change the solver.
        harvest_priorities = tuple(
            (
                str(row["candidate_id"]),
                score,
            )
            for row, score in zip(
                candidate_rows, harvest_scores, strict=True
            )
        )
    hints = PricingOrderingHintsV2(
        binding_hash=binding.binding_hash,
        task_priorities=(
            tuple()
            if online_harvest
            else tuple(
                zip(static.node_ids[1:], task_scores, strict=True)
            )
        ),
        arc_priorities=(
            tuple()
            if online_harvest
            else tuple(
                zip(static.arc_candidate_ids, arc_scores, strict=True)
            )
        ),
        harvest_priorities=harvest_priorities,
        proof_tail_risk=proof_tail_risk,
        queue_policy_id="Q0",
        uncertainty=float(ood_diagnostics.get("max_abs_z") or 0.0),
        ood=bool(ood),
        source=manifest.model_kind,
        diagnostic_only=(requested_mode == "shadow"),
    )
    lifecycle_payload = telemetry.to_payload()
    prepared = replace(
        enriched,
        guidance_hints=hints,
        guidance_lifecycle_telemetry=tuple(lifecycle_payload.items()),
    )
    return GuidancePreparation(
        request=prepared,
        decision=decision,
        telemetry=lifecycle_payload,
        diagnostics={
            "torch_imported": True,
            "checkpoint_metadata_valid": True,
            "ood": ood,
            "ood_diagnostics": ood_diagnostics,
            "nonfinite_hint_accepted": False,
            "binding_hash": binding.binding_hash,
            "instance_content_hash": static.instance_content_hash,
            "torch_num_threads": int(torch.get_num_threads()),
            "deterministic_inference": bool(
                torch.are_deterministic_algorithms_enabled()
            ),
            "guidance_action_scope": manifest.guidance_action_scope,
            "p0_noop_available": True,
            "p0_noop_score": harvest_noop_score,
            "learned_action_selected": selected_harvest_id,
            "abstained_to_p0": bool(
                online_harvest and selected_harvest_id is None
            ),
            "abstention_reason": abstention_reason,
            "max_learned_promotions_per_context": 1,
        },
    )


def _failed_preparation(
    request: BackendPricingRequest,
    decision: GuidanceEntryDecision,
    telemetry: GuidanceLifecycleTelemetry,
    *,
    reason: str,
    error: str,
) -> GuidancePreparation:
    telemetry.bypass_reason = reason
    payload = telemetry.to_payload()
    return GuidancePreparation(
        request=replace(
            request,
            guidance_mode="off",
            guidance_hints=None,
            guidance_lifecycle_telemetry=tuple(payload.items()),
        ),
        decision=decision,
        telemetry=payload,
        diagnostics={
            "guidance_fallback_to_p0": True,
            "reason": reason,
            "error": error,
            "nonfinite_hint_accepted": False,
        },
    )


def _validate_checkpoint_metadata(
    metadata: Mapping[str, Any],
    manifest: DeploymentEligibilityManifest,
) -> None:
    expected = {
        "checkpoint_id": manifest.checkpoint_id,
        "source_baseline_id": manifest.source_baseline_id,
        "feature_schema_version": manifest.feature_schema_version,
        "normalization_version": manifest.normalization_version,
        "ood_policy_version": manifest.ood_policy_version,
    }
    mismatches = [
        key
        for key, value in expected.items()
        if str(metadata.get(key) or "") != str(value)
    ]
    if mismatches:
        raise ValueError(
            "checkpoint metadata mismatch: " + ",".join(mismatches)
        )
    if str(
        metadata.get("harvest_model_context_schema_version") or ""
    ) != HARVEST_MODEL_CONTEXT_SCHEMA_V2:
        raise ValueError(
            "checkpoint harvest model-context schema mismatch"
        )
    if not bool(metadata.get("ood_calibrated")):
        raise ValueError("checkpoint OOD policy is not calibrated")
    if str(metadata.get("training_objective") or "") != (
        COUNTERFACTUAL_TRAINING_OBJECTIVE_V2
    ):
        raise ValueError(
            "checkpoint does not use the reviewed counterfactual objective"
        )
    if str(metadata.get("trajectory_objective_spec_id") or "") != (
        FIXED_POOL_PRICING_PRESSURE_OBJECTIVE_SPEC_V1
    ):
        raise ValueError(
            "checkpoint trajectory objective spec mismatch"
        )
    if str(metadata.get("counterfactual_main_scope") or "") != (
        "harvest_only"
    ):
        raise ValueError(
            "first-stage checkpoint must train route harvest as the sole "
            "main ranking head"
        )
    if "harvest" not in {
        str(value) for value in metadata.get("trained_main_heads", ())
    }:
        raise ValueError("checkpoint did not train the harvest main head")
    if not bool(metadata.get("p0_noop_trained")):
        raise ValueError("checkpoint did not train the P0_KEEP_ORDER action")
    if manifest.guidance_action_scope != (
        ROUTE_HARVEST_SINGLE_PROMOTION_SCOPE
    ):
        raise ValueError("manifest/checkpoint guidance action scope mismatch")
    thresholds = dict(metadata.get("ood_max_abs_z_by_scale") or {})
    enabled_scales = set(manifest.eligible_online_scales).union(
        manifest.shadow_only_scales
    )
    missing_ood_scales = sorted(
        scale for scale in enabled_scales if str(scale) not in thresholds
    )
    if missing_ood_scales:
        raise ValueError(
            "checkpoint OOD thresholds missing enabled scales: "
            + ",".join(str(scale) for scale in missing_ood_scales)
        )
    compatible = {
        str(value)
        for value in metadata.get("compatible_engine_hashes", ())
    }
    required_engines = {
        manifest.expected_engine_hash(scale)
        for scale in set(manifest.eligible_online_scales).union(
            manifest.shadow_only_scales
        )
    }
    if compatible:
        missing_engines = sorted(required_engines.difference(compatible))
        if missing_engines:
            raise ValueError(
                "checkpoint incompatible with exact engines: "
                + ",".join(missing_engines)
            )
    elif str(metadata.get("engine_hash") or "") != str(manifest.engine_hash):
        raise ValueError("checkpoint metadata mismatch: engine_hash")


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            hasher.update(block)
    return hasher.hexdigest()


def _harvest_tensors(
    candidates: tuple[dict[str, Any], ...],
    node_ids: tuple[str, ...],
    *,
    torch,
):
    if not candidates:
        return None, None
    index = {node_id: position for position, node_id in enumerate(node_ids)}
    masks = []
    contexts = []
    for row in candidates:
        if not row.get("candidate_id"):
            raise ValueError("harvest candidate_id is required")
        mask = [0.0] * len(node_ids)
        for task_id in row.get("task_ids", ()):
            mask[index[str(task_id)]] = 1.0
        masks.append(mask)
        contexts.append(
            learned_harvest_context(row.get("context", ()))
        )
    return (
        torch.tensor(masks, dtype=torch.float32),
        torch.tensor(contexts, dtype=torch.float32),
    )


def _normalize_and_check_ood(
    raw_node_tensor,
    raw_edge_tensor,
    metadata: Mapping[str, Any],
    *,
    scale: int,
    torch,
):
    required = (
        "node_feature_mean",
        "node_feature_std",
        "edge_feature_mean",
        "edge_feature_std",
        "ood_max_abs_z",
    )
    missing = [key for key in required if metadata.get(key) is None]
    if missing:
        raise ValueError(
            "checkpoint normalization/OOD metadata missing: "
            + ",".join(missing)
        )
    node_mean = torch.tensor(
        metadata["node_feature_mean"], dtype=raw_node_tensor.dtype
    )
    node_std = torch.tensor(
        metadata["node_feature_std"], dtype=raw_node_tensor.dtype
    ).clamp_min(1.0e-8)
    edge_mean = torch.tensor(
        metadata["edge_feature_mean"], dtype=raw_edge_tensor.dtype
    )
    edge_std = torch.tensor(
        metadata["edge_feature_std"], dtype=raw_edge_tensor.dtype
    ).clamp_min(1.0e-8)
    if (
        node_mean.numel() != raw_node_tensor.shape[1]
        or node_std.numel() != raw_node_tensor.shape[1]
    ):
        raise ValueError("node normalization width mismatch")
    if (
        edge_mean.numel() != raw_edge_tensor.shape[1]
        or edge_std.numel() != raw_edge_tensor.shape[1]
    ):
        raise ValueError("edge normalization width mismatch")
    node_tensor = (raw_node_tensor - node_mean) / node_std
    edge_tensor = (raw_edge_tensor - edge_mean) / edge_std
    max_abs_node_z = (
        float(node_tensor.abs().max()) if node_tensor.numel() else 0.0
    )
    max_abs_edge_z = (
        float(edge_tensor.abs().max()) if edge_tensor.numel() else 0.0
    )
    max_abs_z = max(max_abs_node_z, max_abs_edge_z)
    by_scale = metadata.get("ood_max_abs_z_by_scale") or {}
    if str(int(scale)) not in by_scale:
        raise ValueError(f"OOD threshold missing for scale {int(scale)}")
    limit = float(by_scale[str(int(scale))])
    return node_tensor, edge_tensor, max_abs_z > limit, {
        "policy": "fold_training_zscore_with_calibration_threshold",
        "max_abs_z": max_abs_z,
        "max_abs_node_z": max_abs_node_z,
        "max_abs_edge_z": max_abs_edge_z,
        "limit": limit,
        "scale": int(scale),
        "scale_specific_threshold": str(int(scale)) in by_scale,
    }


def _cached_request_tensors(
    request: BackendPricingRequest,
    *,
    static,
    metadata: Mapping[str, Any],
    manifest: DeploymentEligibilityManifest,
    torch,
):
    node_mean = torch.tensor(
        metadata["node_feature_mean"], dtype=torch.float32
    )
    node_std = torch.tensor(
        metadata["node_feature_std"], dtype=torch.float32
    ).clamp_min(1.0e-8)
    edge_mean = torch.tensor(
        metadata["edge_feature_mean"], dtype=torch.float32
    )
    edge_std = torch.tensor(
        metadata["edge_feature_std"], dtype=torch.float32
    ).clamp_min(1.0e-8)
    static_width = len(NODE_STATIC_FEATURES)
    dynamic_width = len(DYNAMIC_NODE_FEATURES)
    if node_mean.numel() != static_width + dynamic_width:
        raise ValueError("node normalization width mismatch")
    if edge_mean.numel() != len(EDGE_STATIC_FEATURES):
        raise ValueError("edge normalization width mismatch")
    cache_key = (
        str(static.instance_content_hash),
        str(manifest.checkpoint_sha256 or manifest.checkpoint_id),
        str(manifest.normalization_version),
    )
    with _TENSOR_CACHE_LOCK:
        cached = _TENSOR_CACHE.get(cache_key)
        if cached is not None:
            _TENSOR_CACHE.move_to_end(cache_key)
    cache_hit = cached is not None
    if cached is None:
        raw_static_node = torch.tensor(
            static.node_features, dtype=torch.float32
        )
        raw_edge = torch.tensor(
            static.arc_features, dtype=torch.float32
        )
        cached = {
            "normalized_static_node": (
                raw_static_node - node_mean[:static_width]
            )
            / node_std[:static_width],
            "normalized_edge": (raw_edge - edge_mean) / edge_std,
            "edge_index": torch.tensor(
                (static.arc_sources, static.arc_targets),
                dtype=torch.long,
            ),
            "task_indices": torch.arange(
                1, len(static.node_ids), dtype=torch.long
            ),
        }
        with _TENSOR_CACHE_LOCK:
            existing = _TENSOR_CACHE.get(cache_key)
            if existing is not None:
                cached = existing
                cache_hit = True
            else:
                _TENSOR_CACHE[cache_key] = cached
                _TENSOR_CACHE.move_to_end(cache_key)
                while len(_TENSOR_CACHE) > _TENSOR_CACHE_MAX_ENTRIES:
                    _TENSOR_CACHE.popitem(last=False)
    raw_dynamic = torch.tensor(
        dynamic_node_features(request), dtype=torch.float32
    )
    normalized_dynamic = (
        raw_dynamic - node_mean[static_width:]
    ) / node_std[static_width:]
    node_tensor = torch.cat(
        (cached["normalized_static_node"], normalized_dynamic),
        dim=1,
    )
    edge_tensor = cached["normalized_edge"]
    max_abs_node_z = (
        float(node_tensor.abs().max()) if node_tensor.numel() else 0.0
    )
    max_abs_edge_z = (
        float(edge_tensor.abs().max()) if edge_tensor.numel() else 0.0
    )
    max_abs_z = max(max_abs_node_z, max_abs_edge_z)
    by_scale = dict(metadata.get("ood_max_abs_z_by_scale") or {})
    scale_key = str(int(request.data.scale))
    if scale_key not in by_scale:
        raise ValueError(
            f"OOD threshold missing for scale {request.data.scale}"
        )
    limit = float(by_scale[scale_key])
    diagnostics = {
        "policy": "fold_training_zscore_with_calibration_threshold",
        "max_abs_z": max_abs_z,
        "max_abs_node_z": max_abs_node_z,
        "max_abs_edge_z": max_abs_edge_z,
        "limit": limit,
        "scale": int(request.data.scale),
        "scale_specific_threshold": True,
        "static_tensor_cache_hit": cache_hit,
        "static_tensor_cache_key": list(cache_key),
    }
    return (
        node_tensor,
        edge_tensor,
        cached["edge_index"],
        cached["task_indices"],
        max_abs_z > limit,
        diagnostics,
    )


def expected_model_dimensions() -> tuple[int, int]:
    return (
        len(NODE_STATIC_FEATURES) + len(DYNAMIC_NODE_FEATURES),
        len(EDGE_STATIC_FEATURES),
    )
