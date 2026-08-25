"""Fail-closed installer for the V7 Native-frontier GAT bundle.

This module imports neither Torch nor the training model.  It validates and
attaches a portable numeric bundle; Native builds the frontier graph and makes
the sole queue-switch decision after 4096 literal-Q0 pops.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from math import isfinite, log1p
import os
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping

from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
    BACKEND_OBJECTIVE_OFFICIAL,
    FRONTIER_PROBE_BOUNDARY_V7,
    FRONTIER_PROBE_MODE_LEARNED,
    PRICING_LIFECYCLE_SCOPE_ROOT_CG,
    PROOF_QUEUE_POLICY_Q0,
)


MANIFEST_ENV = "LUNAR_ICE_P0V5_FRONTIER_GAT_QD1_V7_MANIFEST"
EVALUATION_ENV = "LUNAR_ICE_P0V5_FRONTIER_GAT_QD1_V7_EVALUATION_MODE"
MANIFEST_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_frontier_gat_qd1_runtime_manifest.v1"
)
RUNTIME_POLICY_V7 = "P0V5_ROOT_FRONTIER_GAT_QD1_SELECTOR_V7"
BUNDLE_SCHEMA_V1 = "lunar_ice_bpc.p0v5_frontier_gat_native_bundle.v1"
GRAPH_SCHEMA_V1 = "lunar_ice_bpc.p0v5_frontier_depth_rc_graph.v1"
FEATURE_SCHEMA_V1 = "lunar_ice_bpc.p0v5_frontier_probe_features.v1"
ALLOWED_SCALES = frozenset({30, 50})
FROZEN_SEEDS = (61635, 91267, 170141)


def prepare_frontier_gat_qd1_request_from_environment(request):
    """Attach one validated portable bundle, or return the identical Q0 request."""

    scale = int(request.data.scale)
    if scale not in ALLOWED_SCALES:
        return request, _noop("scale_bypasses_frontier_selector", enabled=False)
    if request.pricing_lifecycle_scope != PRICING_LIFECYCLE_SCOPE_ROOT_CG:
        return request, _noop("tree_bypasses_frontier_selector", enabled=False)
    if not bool(request.exact_proof_mode):
        return request, _noop("not_exact_proof")
    if str(request.objective_mode) != BACKEND_OBJECTIVE_OFFICIAL:
        return request, _noop("nonofficial_objective")
    if not bool(request.proof_tail_fallback_context):
        return request, _noop("not_v5_fallback_context")
    if str(request.proof_queue_policy_id) != PROOF_QUEUE_POLICY_Q0:
        return request, _noop("incoming_policy_is_not_literal_q0")
    if str(request.guidance_mode) != "off" or request.guidance_hints is not None:
        return request, _noop("preexisting_guidance_bundle")
    if bool(request.dssr_enabled):
        return request, _noop("dssr_not_supported")

    started = perf_counter()
    try:
        manifest_value = str(os.getenv(MANIFEST_ENV, "")).strip()
        if not manifest_value:
            return request, _noop("manifest_not_configured", enabled=False)
        manifest_path = Path(manifest_value).resolve()
        manifest = _load_json(manifest_path)
        _validate_manifest(request, manifest, manifest_path)
        evaluation = str(os.getenv(EVALUATION_ENV, "0")).lower() in {
            "1", "true", "yes", "on"
        }
        if evaluation:
            if not bool(manifest.get("development_e2e_authorized")):
                return request, _noop("development_e2e_not_authorized")
        elif not bool(manifest.get("deployment_authorized")):
            return request, _noop("deployment_not_authorized")

        bundle_path = _resolve_artifact(
            manifest_path, manifest["portable_bundle_path"]
        )
        bundle_file_hash = _sha256(bundle_path)
        if bundle_file_hash != str(manifest["portable_bundle_file_sha256"]):
            raise ValueError("portable bundle file hash drift")
        bundle = _load_json(bundle_path)
        _validate_bundle(
            request, bundle, bundle_file_hash,
            expected_selected_config_sha256=str(
                manifest["selected_exact_config_sha256"]
            ),
        )
        selected_bundle = dict(bundle)
        selected_bundle["thresholds"] = dict(
            bundle["thresholds_by_scale"][str(scale)]
        )
        selected_bundle["calibration"] = dict(
            bundle["calibration_by_scale"][str(scale)]
        )
        context = _context_features(request)
        return replace(
            request,
            proof_tail_frontier_probe_mode=FRONTIER_PROBE_MODE_LEARNED,
            proof_tail_frontier_probe_boundary=FRONTIER_PROBE_BOUNDARY_V7,
            proof_tail_frontier_context_features=context,
            proof_tail_frontier_gat_bundle=selected_bundle,
            proof_tail_frontier_manifest_path=str(manifest_path),
            proof_tail_frontier_manifest_sha256=_sha256(manifest_path),
            proof_tail_frontier_bundle_sha256=bundle_file_hash,
        ), {
            "proof_tail_frontier_runtime_enabled": True,
            "proof_tail_frontier_runtime_action": "DEFER_TO_NATIVE_PROBE",
            "proof_tail_frontier_runtime_reason": "portable_bundle_attached",
            "proof_tail_frontier_manifest_sha256": _sha256(manifest_path),
            "proof_tail_frontier_bundle_sha256": bundle_file_hash,
            "proof_tail_frontier_bundle_load_wall_ms": (
                perf_counter() - started
            ) * 1000.0,
            "proof_tail_frontier_bypassed_before_manifest": False,
            "proof_tail_frontier_torch_import_count": 0,
            "proof_tail_frontier_graph_build_count": 0,
            "proof_tail_frontier_model_call_count": 0,
        }
    except Exception as exc:
        return request, {
            **_noop(f"frontier_fail_closed:{type(exc).__name__}"),
            "proof_tail_frontier_runtime_detail": repr(exc),
            "proof_tail_frontier_bundle_load_wall_ms": (
                perf_counter() - started
            ) * 1000.0,
        }


def _validate_manifest(request, manifest: Mapping[str, Any], path: Path) -> None:
    required = {
        "schema_version",
        "runtime_policy",
        "action_universe",
        "forced_veto_actions",
        "probe_boundary",
        "allowed_scales",
        "model_kind",
        "message_passing_required",
        "pricing_lifecycle_authority",
        "portable_bundle_path",
        "portable_bundle_file_sha256",
        "allowed_exact_engine_hashes",
        "selected_exact_config_sha256",
        "allowed_exact_action_policy_hashes",
        "development_only",
        "deployment_authorized",
        "production_switch_authorized",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise ValueError(f"manifest fields missing: {missing}")
    if manifest["schema_version"] != MANIFEST_SCHEMA_V1:
        raise ValueError("manifest schema drift")
    if manifest["runtime_policy"] != RUNTIME_POLICY_V7:
        raise ValueError("runtime policy drift")
    if list(manifest["action_universe"]) != ["CONTINUE_Q0", "SWITCH_QD1"]:
        raise ValueError("action universe drift")
    if set(manifest["forced_veto_actions"]) != {"QB1", "QGR1"}:
        raise ValueError("forced veto drift")
    if int(manifest["probe_boundary"]) != FRONTIER_PROBE_BOUNDARY_V7:
        raise ValueError("probe boundary drift")
    if {int(value) for value in manifest["allowed_scales"]} != ALLOWED_SCALES:
        raise ValueError("allowed scales drift")
    if manifest["model_kind"] != "frontier_interaction_gat":
        raise ValueError("candidate is not the frontier GAT")
    if not bool(manifest["message_passing_required"]):
        raise ValueError("message passing is not required")
    if manifest["pricing_lifecycle_authority"] != "root_cg_only":
        raise ValueError("root-only authority drift")
    if not bool(manifest["development_only"]):
        raise ValueError("candidate must remain development-only")
    if bool(manifest["deployment_authorized"]):
        raise ValueError("V7 cannot authorize deployment")
    if bool(manifest["production_switch_authorized"]):
        raise ValueError("V7 cannot authorize production switching")
    if str(request.engine_hash) not in {
        str(value) for value in manifest["allowed_exact_engine_hashes"]
    }:
        raise ValueError("exact engine hash mismatch")
    selected_config_sha = str(manifest["selected_exact_config_sha256"])
    if len(selected_config_sha) != 64:
        raise ValueError("selected exact config hash drift")
    from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
        qg2_exact_action_policy_hash_from_request,
    )

    action_hash = qg2_exact_action_policy_hash_from_request(request)
    if action_hash not in {
        str(value) for value in manifest["allowed_exact_action_policy_hashes"]
    }:
        raise ValueError("exact action-policy hash mismatch")
    artifact = _resolve_artifact(path, manifest["portable_bundle_path"])
    if not artifact.is_file():
        raise ValueError("portable bundle is missing")


def _validate_bundle(
    request,
    bundle: Mapping[str, Any],
    bundle_file_hash: str,
    *,
    expected_selected_config_sha256: str,
) -> None:
    if bundle.get("schema_version") != BUNDLE_SCHEMA_V1:
        raise ValueError("bundle schema drift")
    if bundle.get("graph_schema_version") != GRAPH_SCHEMA_V1:
        raise ValueError("graph schema drift")
    if bundle.get("feature_schema_version") != FEATURE_SCHEMA_V1:
        raise ValueError("feature schema drift")
    normalized = dict(bundle)
    internal_hash = str(normalized.pop("bundle_sha256", ""))
    if hashlib.sha256(_canonical_bytes(normalized)).hexdigest() != internal_hash:
        raise ValueError("bundle canonical hash drift")
    models = list(bundle.get("models") or ())
    if [int(row["seed"]) for row in models] != list(FROZEN_SEEDS):
        raise ValueError("ensemble seed drift")
    total = 0
    for row in models:
        count = sum(len(tensor["values"]) for tensor in row["tensors"].values())
        if count >= 15_000:
            raise ValueError("per-seed parameter limit exceeded")
        total += count
    if total >= 45_000:
        raise ValueError("ensemble parameter limit exceeded")
    thresholds = dict(bundle.get("thresholds_by_scale") or {})
    if set(thresholds) != {"30", "50"}:
        raise ValueError("scale-specific thresholds missing")
    for row in thresholds.values():
        values = {
            "minimum_benefit_probability": float(row["minimum_benefit_probability"]),
            "maximum_adverse_probability": float(row["maximum_adverse_probability"]),
            "minimum_expected_gain": float(row["minimum_expected_gain"]),
            "adverse_penalty": float(row["adverse_penalty"]),
            "maximum_disagreement": float(row["maximum_disagreement"]),
        }
        if any(not isfinite(value) for value in values.values()):
            raise ValueError("nonfinite threshold")
    calibrations = dict(bundle.get("calibration_by_scale") or {})
    if set(calibrations) != {"30", "50"}:
        raise ValueError("scale-specific calibration missing")
    for row in calibrations.values():
        if set(row) != {"benefit", "adverse", "gain_scale"}:
            raise ValueError("probability calibration schema drift")
        if not isfinite(float(row["gain_scale"])) or float(row["gain_scale"]) < 0.0:
            raise ValueError("gain calibration is invalid")
    bindings = dict(bundle.get("bindings") or {})
    engine_hashes = bindings.get("engine_hashes") or (bindings.get("engine_hash"),)
    action_hashes = bindings.get("action_policy_hashes") or ()
    if str(request.engine_hash) not in {str(value) for value in engine_hashes}:
        raise ValueError("bundle engine binding mismatch")
    if str(bindings.get("selected_exact_config_sha256")) != str(
        expected_selected_config_sha256
    ):
        raise ValueError("bundle selected exact config binding mismatch")
    if action_hashes:
        from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
            qg2_exact_action_policy_hash_from_request,
        )
        if qg2_exact_action_policy_hash_from_request(request) not in {
            str(value) for value in action_hashes
        }:
            raise ValueError("bundle action-policy binding mismatch")
    if str(bindings.get("bundle_file_sha256", bundle_file_hash)) not in {
        "", bundle_file_hash
    }:
        raise ValueError("bundle file self-binding mismatch")


def _context_features(request) -> tuple[float, ...]:
    values = [0.0] * 28
    if request.proof_tail_active_column_count is not None:
        values[15] = log1p(float(request.proof_tail_active_column_count))
        values[16] = 1.0
    if request.proof_tail_round_index is not None:
        values[17] = log1p(float(request.proof_tail_round_index))
        values[18] = 1.0
    if request.proof_tail_dual_delta_l1 is not None:
        values[19] = float(request.proof_tail_dual_delta_l1)
        values[20] = 1.0
    if request.proof_tail_v5_midpoint_wall_sec is not None:
        values[24] = log1p(float(request.proof_tail_v5_midpoint_wall_sec))
        values[25] = 1.0
    return tuple(values)


def _load_json(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _resolve_artifact(manifest_path: Path, value: object) -> Path:
    path = Path(str(value))
    if not path.is_absolute():
        path = manifest_path.parent / path
    return path.resolve()


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _noop(reason: str, *, enabled: bool = True) -> dict[str, Any]:
    return {
        "proof_tail_frontier_runtime_enabled": bool(enabled),
        "proof_tail_frontier_runtime_action": "CONTINUE_Q0",
        "proof_tail_frontier_runtime_reason": str(reason),
        "proof_tail_frontier_manifest_sha256": "",
        "proof_tail_frontier_bundle_sha256": "",
        "proof_tail_frontier_bundle_load_wall_ms": 0.0,
        "proof_tail_frontier_bypassed_before_manifest": not enabled,
        "proof_tail_frontier_torch_import_count": 0,
        "proof_tail_frontier_graph_build_count": 0,
        "proof_tail_frontier_model_call_count": 0,
    }
