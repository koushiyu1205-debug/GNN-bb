"""Fail-closed runtime for Q0-anchored QG2 proof-tail guidance."""

from __future__ import annotations

from dataclasses import replace
import fcntl
import hashlib
import json
from pathlib import Path
import os
from threading import RLock
from time import perf_counter
from typing import Any, Mapping

from lunar_ice_bpc.guidance.qg2_runtime_oracle_authority import (
    validate_qg2_runtime_oracle_authority,
)


QG2_MANIFEST_ENV = "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST"
QG2_EVALUATION_ENV = "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE"
QG2_FALLBACK_SNAPSHOT_ENV = "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR"
QG2_SNAPSHOT_GLOBAL_STORAGE_CAP_ENV = (
    "LUNAR_ICE_P0V5_QG2_SNAPSHOT_GLOBAL_STORAGE_CAP"
)
QG2_SNAPSHOT_PER_SCALE_STORAGE_CAP_ENV = (
    "LUNAR_ICE_P0V5_QG2_SNAPSHOT_PER_SCALE_STORAGE_CAP"
)
QG2_SNAPSHOT_DEFAULT_GLOBAL_STORAGE_CAP = 300
QG2_SNAPSHOT_DEFAULT_PER_SCALE_STORAGE_CAP = 150
QG2_SNAPSHOT_HARD_GLOBAL_STORAGE_CAP = 450
QG2_SNAPSHOT_HARD_PER_SCALE_STORAGE_CAP = 225
QG2_RUNTIME_POLICY_ID = "p0v5_q0_anchored_qg2_label_state_v1"
QG2_EXACT_ACTION_POLICY_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_qg2_exact_action_policy.v1"
)
QG2_TRAJECTORY_FEATURE_SEMANTICS_V2 = (
    "p0v5_qg2_preaction_trajectory_missingness.v2"
)
QG2_ALLOWED_SCALES = frozenset({30, 50})
QG2_ALLOWED_BUCKET_WIDTHS = frozenset({1.0e-4, 3.0e-4, 1.0e-3})
QG2_POSITIVE_NET_EVALUATION_GATE_V1 = "positive_net_exact_safe.v1"
_LOCK = RLock()
_MANIFEST_CACHE: dict[str, dict[str, Any]] = {}
_MODEL_CACHE: dict[str, tuple[Any, dict[str, Any], str]] = {}


def qg2_exact_action_policy_payload(
    *,
    pricing_mode: str,
    objective_mode: str,
    exact_negative_escape_enabled: bool,
    exact_admission_batch_size: int,
    exact_raw_negative_pool_size: int,
    exact_negative_escape_policy_id: str,
    base_proof_queue_policy_id: str = "Q0",
) -> dict[str, Any]:
    """Return the instance-invariant policy surface that QG2 may reorder.

    The ordinary request ``config_hash`` deliberately remains a full,
    per-request canonical binding.  It contains dynamic RMP/round state and is
    therefore not a deployable allowlist key.  This narrower hash only binds
    the exact action/milestone contract shared by training and held-out runs.
    """

    return {
        "schema_version": QG2_EXACT_ACTION_POLICY_SCHEMA_V1,
        "pricing_mode": str(pricing_mode),
        "objective_mode": str(objective_mode),
        "exact_negative_escape_enabled": bool(
            exact_negative_escape_enabled
        ),
        "exact_admission_batch_size": int(exact_admission_batch_size),
        "exact_raw_negative_pool_size": int(exact_raw_negative_pool_size),
        "exact_negative_escape_policy_id": str(
            exact_negative_escape_policy_id
        ),
        "base_proof_queue_policy_id": str(base_proof_queue_policy_id),
    }


def qg2_exact_action_policy_hash_from_request(request) -> str:
    return _stable_payload_hash(qg2_exact_action_policy_payload(
        pricing_mode=str(request.mode),
        objective_mode=str(request.objective_mode),
        exact_negative_escape_enabled=bool(
            request.exact_negative_escape_enabled
        ),
        exact_admission_batch_size=int(
            request.exact_admission_batch_size
        ),
        exact_raw_negative_pool_size=int(
            request.exact_raw_negative_pool_size
        ),
        exact_negative_escape_policy_id=str(
            request.exact_negative_escape_policy_id
        ),
        base_proof_queue_policy_id=str(request.proof_queue_policy_id),
    ))


def qg2_exact_action_policy_hash_from_snapshot(
    snapshot: Mapping[str, Any],
) -> str:
    scale = int(snapshot.get("scale") or 0)
    admission_target = int(
        snapshot.get("exact_admission_batch_size")
        or (64 if scale == 30 else 128)
    )
    return _stable_payload_hash(qg2_exact_action_policy_payload(
        pricing_mode=str(snapshot.get("pricing_mode") or ""),
        objective_mode=str(snapshot.get("objective_mode") or ""),
        exact_negative_escape_enabled=bool(
            snapshot.get("exact_negative_escape_enabled", True)
        ),
        exact_admission_batch_size=admission_target,
        exact_raw_negative_pool_size=int(
            snapshot.get("exact_raw_negative_pool_size")
            or 4 * admission_target
        ),
        exact_negative_escape_policy_id=str(
            snapshot.get("exact_negative_escape_policy_id")
            or "diverse_raw_4x_then_p0v4_selector_v1"
        ),
        # All snapshots are recorded before any QG2 action.  The immutable
        # safety contract requires the literal P0V4 Q0 container here.
        base_proof_queue_policy_id=str(
            snapshot.get("base_proof_queue_policy_id") or "Q0"
        ),
    ))


def record_qg2_fallback_snapshot(request) -> dict[str, Any]:
    """Persist an opt-in, immutable pre-action V5 fallback context."""

    root_value = str(os.getenv(QG2_FALLBACK_SNAPSHOT_ENV, "")).strip()
    if not root_value:
        return {"proof_tail_qg2_snapshot_written": False,
                "proof_tail_qg2_snapshot_reason": "collection_not_configured"}
    if (
        int(request.data.scale) not in QG2_ALLOWED_SCALES
        or not bool(request.exact_proof_mode)
        or str(request.objective_mode) != "official"
        or not bool(request.proof_tail_fallback_context)
        or request.proof_tail_active_task_sets is None
        or request.proof_tail_active_column_signature_hashes is None
    ):
        return {"proof_tail_qg2_snapshot_written": False,
                "proof_tail_qg2_snapshot_reason": "context_not_eligible"}
    try:
        payload = _qg2_fallback_snapshot_payload(request)
        state_hash = _stable_payload_hash(payload)
        snapshot = {**payload, "state_hash": state_hash}
        root = Path(root_value).resolve()
        target = (
            root / f"scale{int(request.data.scale)}"
            / str(request.data.instance_content_hash)
            / f"{state_hash}.json"
        )
        root.mkdir(parents=True, exist_ok=True)
        lock_path = root / ".qg2_snapshot_collection.lock"
        with lock_path.open("a+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            try:
                if target.exists():
                    return {
                        "proof_tail_qg2_snapshot_written": False,
                        "proof_tail_qg2_snapshot_reason": "duplicate_state",
                        "proof_tail_qg2_snapshot_path": str(target),
                        "proof_tail_qg2_snapshot_state_hash": state_hash,
                    }
                all_snapshots = tuple(root.glob("scale*/*/*.json"))
                scale_snapshots = tuple(
                    root.glob(f"scale{int(request.data.scale)}/*/*.json")
                )
                instance_snapshots = tuple(target.parent.glob("*.json"))
                global_storage_cap, per_scale_storage_cap = (
                    _qg2_snapshot_storage_caps()
                )
                per_instance_limit = max(
                    1,
                    min(
                        50,
                        int(os.getenv(
                            "LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE",
                            "15",
                        )),
                    ),
                )
                if len(all_snapshots) >= global_storage_cap:
                    reason = f"global_{global_storage_cap}_context_cap"
                elif len(scale_snapshots) >= per_scale_storage_cap:
                    reason = (
                        f"per_scale_{per_scale_storage_cap}_context_cap"
                    )
                elif len(instance_snapshots) >= per_instance_limit:
                    reason = "per_instance_context_cap"
                else:
                    reason = ""
                if reason:
                    return {
                        "proof_tail_qg2_snapshot_written": False,
                        "proof_tail_qg2_snapshot_reason": reason,
                        "proof_tail_qg2_snapshot_global_storage_count": (
                            len(all_snapshots)
                        ),
                        "proof_tail_qg2_snapshot_global_storage_cap": (
                            global_storage_cap
                        ),
                        "proof_tail_qg2_snapshot_scale_storage_count": (
                            len(scale_snapshots)
                        ),
                        "proof_tail_qg2_snapshot_scale_storage_cap": (
                            per_scale_storage_cap
                        ),
                    }
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_suffix(
                    f".json.tmp.{os.getpid()}"
                )
                temporary.write_text(
                    json.dumps(
                        snapshot,
                        ensure_ascii=False,
                        indent=2,
                        sort_keys=True,
                    ) + "\n",
                    encoding="utf-8",
                )
                temporary.replace(target)
            finally:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        return {
            "proof_tail_qg2_snapshot_written": True,
            "proof_tail_qg2_snapshot_reason": "eligible_pre_action_context",
            "proof_tail_qg2_snapshot_path": str(target),
            "proof_tail_qg2_snapshot_state_hash": state_hash,
            "proof_tail_qg2_snapshot_can_certify": False,
            "proof_tail_qg2_snapshot_global_storage_count": (
                len(all_snapshots) + 1
            ),
            "proof_tail_qg2_snapshot_global_storage_cap": global_storage_cap,
            "proof_tail_qg2_snapshot_scale_storage_count": (
                len(scale_snapshots) + 1
            ),
            "proof_tail_qg2_snapshot_scale_storage_cap": (
                per_scale_storage_cap
            ),
        }
    except Exception as exc:
        return {
            "proof_tail_qg2_snapshot_written": False,
            "proof_tail_qg2_snapshot_reason": "collection_exception",
            "proof_tail_qg2_snapshot_error": repr(exc),
        }


def _qg2_snapshot_storage_caps() -> tuple[int, int]:
    """Return bounded physical collection caps, independent of Oracle budget."""

    global_cap = _bounded_snapshot_storage_cap(
        QG2_SNAPSHOT_GLOBAL_STORAGE_CAP_ENV,
        default=QG2_SNAPSHOT_DEFAULT_GLOBAL_STORAGE_CAP,
        hard_maximum=QG2_SNAPSHOT_HARD_GLOBAL_STORAGE_CAP,
    )
    per_scale_cap = _bounded_snapshot_storage_cap(
        QG2_SNAPSHOT_PER_SCALE_STORAGE_CAP_ENV,
        default=QG2_SNAPSHOT_DEFAULT_PER_SCALE_STORAGE_CAP,
        hard_maximum=QG2_SNAPSHOT_HARD_PER_SCALE_STORAGE_CAP,
    )
    return global_cap, min(global_cap, per_scale_cap)


def _bounded_snapshot_storage_cap(
    name: str,
    *,
    default: int,
    hard_maximum: int,
) -> int:
    try:
        value = int(str(os.getenv(name, str(default))).strip())
    except (TypeError, ValueError):
        value = default
    return max(1, min(int(hard_maximum), value))


def _qg2_fallback_snapshot_payload(request) -> dict[str, Any]:
    return {
        "schema_version": "lunar_ice_bpc.p0v5_proof_tail_fallback_snapshot.v2",
        "development_only": True,
        "deployable": False,
        "mutates_p0": False,
        "can_certify": False,
        "proof_tail_fallback_context": True,
        "instance_id": str(request.data.instance_id),
        "instance_content_hash": str(request.data.instance_content_hash),
        "scale": int(request.data.scale),
        "pricing_mode": str(request.mode),
        "objective_mode": str(request.objective_mode),
        "exact_negative_escape_enabled": bool(
            request.exact_negative_escape_enabled
        ),
        "exact_admission_batch_size": int(
            request.exact_admission_batch_size
        ),
        "exact_raw_negative_pool_size": int(
            request.exact_raw_negative_pool_size
        ),
        "exact_negative_escape_policy_id": str(
            request.exact_negative_escape_policy_id
        ),
        "base_proof_queue_policy_id": str(request.proof_queue_policy_id),
        "exact_action_policy_hash": (
            qg2_exact_action_policy_hash_from_request(request)
        ),
        "pricing_lifecycle_scope": str(request.pricing_lifecycle_scope),
        "trajectory_feature_semantics_version": (
            QG2_TRAJECTORY_FEATURE_SEMANTICS_V2
        ),
        "round": request.proof_tail_round_index,
        "active_column_count": request.proof_tail_active_column_count,
        "active_task_sets": (
            None
            if request.proof_tail_active_task_sets is None
            else [
                list(task_set)
                for task_set in request.proof_tail_active_task_sets
            ]
        ),
        "active_column_signature_hashes": list(
            request.proof_tail_active_column_signature_hashes or ()
        ),
        "rmp_iteration_id": str(request.rmp_iteration_id),
        "config_hash": str(request.config_hash),
        "engine_hash": str(request.engine_hash),
        "branch_context": request.branch_context.to_payload(),
        "cut_context": request.cut_context.to_payload(),
        "cut_lineage": {"cut_lineage_hash": str(request.cut_lineage_hash)},
        "live_cut_policy_hash": str(request.live_cut_policy_hash),
        "separator_policy_version": str(request.separator_policy_version),
        "true_duals": {
            "task_duals": dict(request.true_duals.cover),
            "fleet_dual": float(request.true_duals.fleet_limit),
            "cut_duals": dict(request.true_duals.cuts or {}),
        },
        "trajectory_features": {
            "previous_proof_pass_wall_time": (
                request.proof_tail_previous_proof_wall_sec
            ),
            "previous_proof_processed_labels": (
                request.proof_tail_previous_processed_labels
            ),
            "dual_l1_delta_from_previous": request.proof_tail_dual_delta_l1,
            "v5_midpoint_wall_sec": request.proof_tail_v5_midpoint_wall_sec,
        },
        "bidirectional_midpoint_prepass_wall_sec": (
            request.proof_tail_v5_midpoint_wall_sec
        ),
        "bidirectional_midpoint_fallback_reason": str(
            request.proof_tail_v5_midpoint_reason
        ),
    }


def _stable_payload_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()


def prepare_qg2_request_from_environment(request):
    """Return QG2 only for an authorized V5-to-P0V4 fallback request."""

    scale = int(request.data.scale)
    if scale not in QG2_ALLOWED_SCALES:
        return request, _noop("scale_bypasses_qg2", enabled=False)
    if not bool(request.exact_proof_mode):
        return request, _noop("not_exact_proof")
    if str(request.objective_mode) != "official":
        return request, _noop("nonofficial_objective")
    if not bool(request.proof_tail_fallback_context):
        return request, _noop("not_v5_fallback_context")
    if request.proof_tail_active_task_sets is None:
        return request, _noop("active_task_sets_missing")
    if request.proof_tail_active_column_signature_hashes is None:
        return request, _noop("active_column_signatures_missing")
    if request.guidance_hints is not None or request.guidance_mode != "off":
        return request, _noop("preexisting_guidance_bundle")
    if bool(request.dssr_enabled):
        return request, _noop("dssr_not_supported")

    manifest_value = str(
        request.proof_tail_gat_manifest_path
        or os.getenv(QG2_MANIFEST_ENV, "")
    ).strip()
    if not manifest_value:
        return request, _noop("manifest_not_configured", enabled=False)
    started = perf_counter()
    manifest_path = Path(manifest_value).resolve()
    manifest = _load_manifest(manifest_path)
    _validate_manifest_before_model_load(request, manifest)
    allowed_scales = {int(value) for value in manifest["allowed_scales"]}
    if scale not in allowed_scales:
        return request, _noop("scale_outside_manifest")

    evaluation_mode = str(
        os.getenv(QG2_EVALUATION_ENV, "0")
    ).strip().lower() in {"1", "true", "yes", "on"}
    if evaluation_mode:
        if not bool(manifest.get("evaluation_authorized")):
            return request, _noop("evaluation_not_authorized")
    elif not bool(manifest.get("deployment_authorized")):
        return request, _noop("deployment_not_authorized")

    source_config_hash = str(request.config_hash)
    exact_action_policy_hash = qg2_exact_action_policy_hash_from_request(
        request
    )
    allowed_engines = {
        str(value) for value in manifest.get("allowed_exact_engine_hashes", ())
    }
    if allowed_engines and str(request.engine_hash) not in allowed_engines:
        return request, _noop("exact_engine_hash_mismatch")
    allowed_action_policies = {
        str(value)
        for value in manifest.get("allowed_exact_action_policy_hashes", ())
    }
    if (
        not allowed_action_policies
        or exact_action_policy_hash not in allowed_action_policies
    ):
        return request, _noop("exact_action_policy_hash_mismatch")

    import_started = perf_counter()
    from lunar_ice_bpc.exact.bpc.guidance.contracts import (
        CanonicalSolveBindingV2,
        GUIDANCE_MODE_TASK_ARC,
        PricingOrderingHintsV2,
    )
    from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
        QG2_FEATURE_SCHEMA_V1,
        QG2_LABEL_STATE_SCHEMA_V1,
        build_qg2_features,
        normalize_qg2_potential_groups,
    )
    import_wall = perf_counter() - import_started

    tensorize_started = perf_counter()
    features = build_qg2_features(
        request.data,
        cover_duals=request.true_duals.cover,
        fleet_dual=float(request.true_duals.fleet_limit),
        active_column_count=request.proof_tail_active_column_count,
        active_task_sets=request.proof_tail_active_task_sets,
        round_index=request.proof_tail_round_index,
        previous_proof_wall_sec=request.proof_tail_previous_proof_wall_sec,
        previous_processed_labels=(
            request.proof_tail_previous_processed_labels
        ),
        dual_l1_delta_from_previous=request.proof_tail_dual_delta_l1,
        branch_decisions=tuple(request.branch_context.pair_decisions),
        cut_duals=dict(request.true_duals.cuts or {}),
        v5_midpoint_wall_sec=request.proof_tail_v5_midpoint_wall_sec,
        root_lifecycle_scope=(request.pricing_lifecycle_scope == "root_cg"),
    )
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
    ood, ood_reason = _is_ood(
        features, dict(manifest.get("feature_envelope") or {})
    )
    if ood:
        return request, {
            **_noop(ood_reason),
            "proof_tail_gat_ood": True,
            "proof_tail_gat_feature_hash": feature_hash,
        }
    tensors = features.to_tensors()
    tensorize_wall = perf_counter() - tensorize_started

    load_started = perf_counter()
    model, metadata, checkpoint_hash = _load_model(
        manifest_path, manifest
    )
    load_wall = perf_counter() - load_started
    if str(getattr(model, "model_kind", "")) != "gat":
        return request, _noop("deployment_model_is_not_gat")

    import torch

    torch.set_num_threads(max(1, int(manifest.get("torch_num_threads") or 1)))
    inference_started = perf_counter()
    with torch.inference_mode():
        output = model(**tensors)
        coefficients = output["label_state_coefficients"].reshape(-1)
    inference_wall = perf_counter() - inference_started
    raw_tensors = (
        output["node_scores"],
        output["arc_scores"],
        coefficients,
        output["benefit_probability"],
        output["conditional_positive_gain"],
    )
    if any(not bool(torch.isfinite(value).all()) for value in raw_tensors):
        return request, {
            **_noop("nonfinite_model_output"),
            "proof_tail_gat_inference_wall_ms": inference_wall * 1000.0,
            "proof_tail_gat_feature_hash": feature_hash,
        }
    if coefficients.numel() != 15 or not bool(torch.isfinite(coefficients).all()):
        return request, _noop("invalid_label_state_coefficients")
    node_potentials, arc_potentials, coefficients = (
        normalize_qg2_potential_groups(
            output["node_scores"][1:].reshape(-1),
            output["arc_scores"].reshape(-1),
            coefficients,
        )
    )
    if max(
        (
            abs(float(value))
            for value in (
                *node_potentials.tolist(),
                *arc_potentials.tolist(),
                *coefficients.tolist(),
            )
        ),
        default=0.0,
    ) <= 1.0e-12:
        return request, {
            **_noop("zero_potential"),
            "proof_tail_gat_inference_wall_ms": inference_wall * 1000.0,
            "proof_tail_gat_feature_hash": feature_hash,
        }
    probability = float(output["benefit_probability"])
    positive_gain = float(output["conditional_positive_gain"])
    expected_gain = probability * positive_gain
    outputs = (
        probability,
        positive_gain,
        expected_gain,
        *node_potentials.tolist(),
        *arc_potentials.tolist(),
        *coefficients.tolist(),
    )
    if any(not _finite(value) for value in outputs):
        return request, _noop("nonfinite_model_output")

    calibration = dict(manifest.get("calibration") or {})
    strict_action_allowed = bool(
        calibration.get("gate_pass")
        and float(calibration.get("harmful_rate_95_upper", 1.0)) <= 0.05
        and float(calibration.get("beneficial_precision_95_lower", 0.0)) >= 0.80
        and float(calibration.get("heldout_tail_ratio", 1.0)) <= 0.90
        and float(calibration.get("gat_vs_best_non_gat_ratio", 1.0)) <= 0.98
        and probability
        >= float(calibration.get("probability_threshold", 1.0))
        and expected_gain
        >= float(calibration.get("expected_gain_threshold", float("inf")))
    )
    positive_net_evaluation_allowed = bool(
        evaluation_mode
        and _positive_net_evaluation_authorized(manifest, calibration)
        and probability
        >= float(calibration.get("probability_threshold", 1.0))
        and expected_gain
        >= float(calibration.get("expected_gain_threshold", float("inf")))
    )
    action_allowed = strict_action_allowed
    if evaluation_mode:
        action_allowed = bool(
            (strict_action_allowed or positive_net_evaluation_allowed)
            and manifest.get("evaluation_force_qg2", True)
        )
    if not action_allowed:
        return request, {
            **_noop("calibration_veto"),
            "proof_tail_gat_probability": probability,
            "proof_tail_gat_conditional_positive_gain": positive_gain,
            "proof_tail_gat_expected_gain": expected_gain,
            "proof_tail_gat_inference_wall_ms": inference_wall * 1000.0,
            "proof_tail_gat_feature_hash": feature_hash,
        }

    bucket_width = float(manifest["guidance_bucket_width"])
    manifest_hash = _sha256(manifest_path)
    qg2_config_hash = stable_payload_hash(
        {
            "schema_version": "lunar_ice_bpc.p0v5_qg2_config.v1",
            "source_exact_config_hash": source_config_hash,
            "exact_action_policy_hash": exact_action_policy_hash,
            "manifest_sha256": manifest_hash,
            "checkpoint_sha256": checkpoint_hash,
            "input_feature_hash": feature_hash,
            "feature_schema_version": QG2_FEATURE_SCHEMA_V1,
            "label_state_schema_version": QG2_LABEL_STATE_SCHEMA_V1,
            "proof_queue_policy_id": "QG2",
            "guidance_bucket_width": bucket_width,
            "allowed_scales": sorted(allowed_scales),
        }
    )
    enriched = replace(
        request,
        config_hash=qg2_config_hash,
        proof_queue_policy_id="QG2",
        proof_queue_guidance_bucket_width=bucket_width,
        proof_tail_gat_enabled=True,
        proof_tail_label_state_schema_version=QG2_LABEL_STATE_SCHEMA_V1,
        proof_tail_gat_manifest_path=str(manifest_path),
        guidance_mode=GUIDANCE_MODE_TASK_ARC,
        guidance_feature_schema_version=QG2_FEATURE_SCHEMA_V1,
        guidance_normalization_version="global_maxabs_rank_preserving.v2",
        guidance_checkpoint_id=checkpoint_hash,
        guidance_ood_policy_version=str(
            manifest.get("ood_policy_version") or "feature_envelope.v1"
        ),
        guidance_lifecycle_telemetry=(
            ("guidance_import_sec", import_wall),
            ("guidance_checkpoint_load_sec", load_wall),
            ("guidance_tensorize_sec", tensorize_wall),
            ("guidance_forward_total_sec", inference_wall),
            ("guidance_call_count", 1),
            ("guidance_binding_validation_sec", 0.0),
            ("guidance_native_install_sec", 0.0),
            ("bypassed_before_import", False),
            ("bypass_reason", ""),
            ("proof_tail_gat_source_exact_config_hash", source_config_hash),
            ("proof_tail_gat_exact_action_policy_hash", exact_action_policy_hash),
            ("proof_tail_gat_feature_hash", feature_hash),
            ("proof_tail_gat_manifest_sha256", manifest_hash),
            ("proof_tail_gat_checkpoint_sha256", checkpoint_hash),
            ("proof_tail_gat_probability", probability),
            ("proof_tail_gat_conditional_positive_gain", positive_gain),
            ("proof_tail_gat_expected_gain", expected_gain),
            ("proof_tail_gat_evaluation_mode", evaluation_mode),
        ),
    )
    binding = CanonicalSolveBindingV2.from_backend_request(enriched)
    hints = PricingOrderingHintsV2(
        binding_hash=binding.binding_hash,
        task_priorities=tuple(
            (task_id, float(value))
            for task_id, value in zip(
                features.task_ids, node_potentials.tolist(), strict=True
            )
        ),
        arc_priorities=tuple(
            (candidate_id, float(value))
            for candidate_id, value in zip(
                features.arc_candidate_ids,
                arc_potentials.tolist(),
                strict=True,
            )
        ),
        label_state_coefficients=tuple(
            float(value) for value in coefficients.tolist()
        ),
        label_state_schema_version=QG2_LABEL_STATE_SCHEMA_V1,
        queue_policy_id="Q0",
        uncertainty=0.0,
        ood=False,
        source="p0v5_qg2_label_state_gat",
        diagnostic_only=True,
    )
    return replace(enriched, guidance_hints=hints), {
        "proof_tail_gat_runtime_enabled": True,
        "proof_tail_gat_action": "QG2",
        "proof_tail_gat_decision_reason": (
            "positive_net_evaluation_qg2"
            if positive_net_evaluation_allowed and not strict_action_allowed
            else "calibrated_qg2"
        ),
        "proof_tail_gat_ood": False,
        "proof_tail_gat_probability": probability,
        "proof_tail_gat_conditional_positive_gain": positive_gain,
        "proof_tail_gat_expected_gain": expected_gain,
        "proof_tail_gat_tensorization_wall_ms": tensorize_wall * 1000.0,
        "proof_tail_gat_inference_wall_ms": inference_wall * 1000.0,
        "proof_tail_gat_total_prepare_wall_ms": (
            perf_counter() - started
        ) * 1000.0,
        "proof_tail_gat_feature_hash": feature_hash,
        "proof_tail_gat_manifest_sha256": manifest_hash,
        "proof_tail_gat_checkpoint_sha256": checkpoint_hash,
        "proof_tail_gat_source_exact_config_hash": source_config_hash,
        "proof_tail_gat_exact_action_policy_hash": exact_action_policy_hash,
        "proof_tail_gat_qg2_config_hash": qg2_config_hash,
    }


def _validate_manifest_before_model_load(request, manifest: Mapping[str, Any]) -> None:
    if str(manifest.get("runtime_policy_id") or "") != QG2_RUNTIME_POLICY_ID:
        raise ValueError("QG2 runtime policy mismatch")
    if str(manifest.get("runtime_implementation_hash") or "") != (
        qg2_runtime_implementation_hash()
    ):
        raise ValueError("QG2 runtime implementation drift")
    if str(manifest.get("feature_schema_version") or "") != (
        "lunar_ice_bpc.p0v5_qg2_features.v1"
    ):
        raise ValueError("QG2 manifest feature schema mismatch")
    if str(manifest.get("label_state_schema_version") or "") != (
        "lunar_spprc.qg2_label_state.v1"
    ):
        raise ValueError("QG2 manifest label-state schema mismatch")
    bucket = float(manifest.get("guidance_bucket_width") or 0.0)
    if not any(abs(bucket - value) <= 1.0e-15 for value in QG2_ALLOWED_BUCKET_WIDTHS):
        raise ValueError("QG2 manifest bucket width was not oracle-frozen")
    validate_qg2_runtime_oracle_authority(manifest)
    if str(manifest.get("evaluation_gate_policy") or "") == (
        QG2_POSITIVE_NET_EVALUATION_GATE_V1
    ):
        if bool(manifest.get("deployment_authorized")):
            raise ValueError(
                "positive-net QG2 manifest cannot authorize deployment"
            )
        if not _positive_net_evaluation_authorized(
            manifest, dict(manifest.get("calibration") or {})
        ):
            raise ValueError(
                "positive-net QG2 evaluation authority is incomplete"
            )
    if not request.instance_hash or not request.config_hash or not request.engine_hash:
        raise ValueError("QG2 exact request binding is incomplete")


def _positive_net_evaluation_authorized(
    manifest: Mapping[str, Any], calibration: Mapping[str, Any]
) -> bool:
    """Validate the relaxed E2E gate without granting production authority."""

    per_scale = dict(calibration.get("heldout_per_scale_net_ratio") or {})
    return bool(
        str(manifest.get("evaluation_gate_policy") or "")
        == QG2_POSITIVE_NET_EVALUATION_GATE_V1
        and bool(manifest.get("evaluation_authorized"))
        and bool(manifest.get("development_e2e_authorized"))
        and not bool(manifest.get("deployment_authorized"))
        and bool(calibration.get("positive_net_gate_pass"))
        and 0.0 < float(calibration.get("calibration_net_ratio", 1.0)) < 1.0
        and 0.0 < float(calibration.get("heldout_net_ratio", 1.0)) < 1.0
        and int(calibration.get("calibration_selected_right_censored_count", 1))
        == 0
        and int(calibration.get("heldout_selected_right_censored_count", 1))
        == 0
        and int(calibration.get("calibration_selected_unsafe_count", 1)) == 0
        and int(calibration.get("heldout_selected_unsafe_count", 1)) == 0
        and set(str(key) for key in per_scale) == {"30", "50"}
        and all(0.0 < float(per_scale[str(scale)]) <= 1.03 for scale in (30, 50))
        and float(calibration.get("probability_threshold", 2.0)) <= 1.0
        and _finite(calibration.get("expected_gain_threshold", float("inf")))
    )


def _load_manifest(path: Path) -> dict[str, Any]:
    key = f"{path}:{path.stat().st_mtime_ns}:{path.stat().st_size}"
    with _LOCK:
        if key in _MANIFEST_CACHE:
            return _MANIFEST_CACHE[key]
        payload = json.loads(path.read_text(encoding="utf-8"))
        _MANIFEST_CACHE.clear()
        _MANIFEST_CACHE[key] = payload
        return payload


def _load_model(path: Path, manifest: Mapping[str, Any]):
    checkpoint_path = Path(str(manifest["checkpoint_path"]))
    if not checkpoint_path.is_absolute():
        checkpoint_path = (path.parent / checkpoint_path).resolve()
    checkpoint_hash = _sha256(checkpoint_path)
    if checkpoint_hash != str(manifest.get("checkpoint_sha256") or ""):
        raise ValueError("QG2 checkpoint hash mismatch")
    key = f"{checkpoint_path}:{checkpoint_hash}"
    with _LOCK:
        if key in _MODEL_CACHE:
            return _MODEL_CACHE[key]
        from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
            load_checkpoint,
        )

        model, metadata = load_checkpoint(str(checkpoint_path))
        if str(metadata.get("training_data_hash") or "") != str(
            manifest.get("training_data_hash") or ""
        ):
            raise ValueError("QG2 training-data hash mismatch")
        _MODEL_CACHE.clear()
        cached = (model, metadata, checkpoint_hash)
        _MODEL_CACHE[key] = cached
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
    node_limit = float(envelope.get("node_max_abs") or 0.0)
    edge_limit = float(envelope.get("edge_max_abs") or 0.0)
    node_max = max(abs(value) for row in features.node_features for value in row)
    edge_max = max(abs(value) for row in features.edge_features for value in row)
    if node_limit <= 0.0 or node_max > node_limit * (1.0 + margin):
        return True, "node_features_outside_envelope"
    if edge_limit <= 0.0 or edge_max > edge_limit * (1.0 + margin):
        return True, "edge_features_outside_envelope"
    return False, ""


def qg2_runtime_implementation_hash() -> str:
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for candidate in (
        root / "proof_queue_label_state_gat.py",
        Path(__file__).resolve(),
        root / "qg2_runtime_oracle_authority.py",
        root / "qg2_oracle_evidence.py",
    ):
        digest.update(candidate.name.encode("utf-8"))
        digest.update(candidate.read_bytes())
    return digest.hexdigest()


def _noop(reason: str, *, enabled: bool = True) -> dict[str, Any]:
    return {
        "proof_tail_gat_runtime_enabled": bool(enabled),
        "proof_tail_gat_action": "Q0",
        "proof_tail_gat_fallback_reason": str(reason),
        "proof_tail_gat_ood": False,
        "proof_tail_gat_probability": None,
        "proof_tail_gat_conditional_positive_gain": None,
        "proof_tail_gat_expected_gain": None,
        "proof_tail_gat_inference_wall_ms": 0.0,
        "proof_tail_gat_tensorization_wall_ms": 0.0,
    }


def _finite(value: float) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return numeric == numeric and abs(numeric) != float("inf")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
