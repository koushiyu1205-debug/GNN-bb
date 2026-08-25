"""Fail-closed root-only runtime for the minimal Q0/QD1 V6 selector."""

from __future__ import annotations

from math import exp, isfinite, log
import hashlib
import json
import os
from pathlib import Path
from threading import RLock


INTERACTION_GAT_MANIFEST_ENV_V6 = (
    "LUNAR_ICE_P0V5_ROOT_INTERACTION_GAT_QD1_SELECTOR_V6_MANIFEST"
)
INTERACTION_GAT_EVALUATION_ENV_V6 = (
    "LUNAR_ICE_P0V5_ROOT_INTERACTION_GAT_QD1_SELECTOR_V6_EVALUATION_MODE"
)
INTERACTION_GAT_MANIFEST_SCHEMA_V6 = (
    "lunar_ice_bpc.p0v5_root_interaction_gat_qd1_runtime_manifest.v1"
)
INTERACTION_GAT_RUNTIME_POLICY_V6 = "P0V5_ROOT_INTERACTION_GAT_QD1_SELECTOR_V6"
INTERACTION_GAT_ACTION_UNIVERSE_V6 = ("Q0", "QD1")
INTERACTION_GAT_ARMS_V6 = ("QD1",)
INTERACTION_GAT_ALLOWED_SCALES = frozenset({30, 50})
MAXIMUM_PARAMETER_COUNT_V6 = 20_000

_PATCH_LOCK = RLock()
_MODEL_LOCK = RLock()
_MODEL_CACHE = {}


def prepare_root_interaction_gat_qd1_request_v6_from_environment(request):
    """Return one exact-safe QD1 request or the identical incoming Q0 object."""

    scale = int(request.data.scale)
    if scale not in INTERACTION_GAT_ALLOWED_SCALES:
        return request, _noop("scale_bypasses_before_manifest_torch_graph", enabled=False)
    if str(request.pricing_lifecycle_scope) != "root_cg":
        return request, _noop(
            "non_root_lifecycle_bypasses_before_manifest_torch_graph", enabled=False
        )

    # V2 is framework-free and imports graph/Torch only after its cheap exact,
    # objective, Q0-identity and manifest guards.  V6 parameterizes that audited
    # installer under a lock and restores every global in a finally block.
    from lunar_ice_bpc.guidance import interaction_gat_queue_runtime_v2 as v2

    with _PATCH_LOCK:
        original = {
            "manifest_env": v2.INTERACTION_GAT_MANIFEST_ENV,
            "evaluation_env": v2.INTERACTION_GAT_EVALUATION_ENV,
            "manifest_schema": v2.INTERACTION_GAT_MANIFEST_SCHEMA_V1,
            "runtime_policy": v2.INTERACTION_GAT_RUNTIME_POLICY_V2,
            "action_universe": v2.INTERACTION_GAT_ACTION_UNIVERSE,
            "parameter_cap": v2.MAXIMUM_PARAMETER_COUNT,
            "implementation_hash": v2.interaction_gat_runtime_implementation_hash,
            "load_model": v2._load_model,
            "validate_manifest": v2._validate_manifest,
            "predictions": v2._predictions,
            "choose_action": v2._choose_action,
        }
        v2.INTERACTION_GAT_MANIFEST_ENV = INTERACTION_GAT_MANIFEST_ENV_V6
        v2.INTERACTION_GAT_EVALUATION_ENV = INTERACTION_GAT_EVALUATION_ENV_V6
        v2.INTERACTION_GAT_MANIFEST_SCHEMA_V1 = INTERACTION_GAT_MANIFEST_SCHEMA_V6
        v2.INTERACTION_GAT_RUNTIME_POLICY_V2 = INTERACTION_GAT_RUNTIME_POLICY_V6
        v2.INTERACTION_GAT_ACTION_UNIVERSE = INTERACTION_GAT_ACTION_UNIVERSE_V6
        v2.MAXIMUM_PARAMETER_COUNT = MAXIMUM_PARAMETER_COUNT_V6
        v2.interaction_gat_runtime_implementation_hash = (
            interaction_gat_runtime_implementation_hash_v6
        )
        v2._load_model = _load_model_v6
        v2._validate_manifest = _validate_v6_manifest
        v2._predictions = _predictions_v6
        v2._choose_action = _choose_action_v6
        try:
            selected, telemetry = v2.prepare_root_interaction_gat_request_from_environment(
                request
            )
        finally:
            v2.INTERACTION_GAT_MANIFEST_ENV = original["manifest_env"]
            v2.INTERACTION_GAT_EVALUATION_ENV = original["evaluation_env"]
            v2.INTERACTION_GAT_MANIFEST_SCHEMA_V1 = original["manifest_schema"]
            v2.INTERACTION_GAT_RUNTIME_POLICY_V2 = original["runtime_policy"]
            v2.INTERACTION_GAT_ACTION_UNIVERSE = original["action_universe"]
            v2.MAXIMUM_PARAMETER_COUNT = original["parameter_cap"]
            v2.interaction_gat_runtime_implementation_hash = original[
                "implementation_hash"
            ]
            v2._load_model = original["load_model"]
            v2._validate_manifest = original["validate_manifest"]
            v2._predictions = original["predictions"]
            v2._choose_action = original["choose_action"]
    result = dict(telemetry)
    result["proof_tail_interaction_gat_runtime_policy"] = (
        INTERACTION_GAT_RUNTIME_POLICY_V6
    )
    result["proof_tail_interaction_gat_qd1_only"] = True
    result["proof_tail_interaction_gat_ranker_calls"] = 0
    return selected, result


def _validate_v6_manifest(request, manifest):
    from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (
        INTERACTION_FEATURE_SCHEMA_V2,
        INTERACTION_GRAPH_SCHEMA_V1,
        INTERACTION_INPUT_PARITY_CONTRACT_V1,
        interaction_graph_builder_hash,
    )

    expected = {
        "schema_version": INTERACTION_GAT_MANIFEST_SCHEMA_V6,
        "runtime_policy_id": INTERACTION_GAT_RUNTIME_POLICY_V6,
        "runtime_implementation_hash": interaction_gat_runtime_implementation_hash_v6(),
        "graph_schema_version": INTERACTION_GRAPH_SCHEMA_V1,
        "feature_schema_version": INTERACTION_FEATURE_SCHEMA_V2,
        "graph_builder_hash": interaction_graph_builder_hash(),
        "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
        "checkpoint_schema_version": (
            "lunar_ice_bpc.p0v5_interaction_gat_qd1_checkpoint.v1"
        ),
        "dataset_schema_version": (
            "lunar_ice_bpc.p0v5_interaction_gat_qd1_training_dataset.v1"
        ),
        "model_kind": "gat",
        "message_passing_required": True,
        "controls_candidate_authorized": False,
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
        "root_only_authority": True,
        "fallback_action": "Q0",
    }
    errors = [
        f"{key}_mismatch" for key, value in expected.items()
        if manifest.get(key) != value
    ]
    if tuple(manifest.get("action_universe") or ()) != INTERACTION_GAT_ACTION_UNIVERSE_V6:
        errors.append("action_universe_mismatch")
    if manifest.get("lifecycle_authority") != ["root_cg"]:
        errors.append("root_only_lifecycle_authority_missing")
    if set(manifest.get("permanent_forced_veto_arms") or ()) != {"QB1", "QGR1"}:
        errors.append("non_v6_arms_not_permanently_vetoed")
    if any("qgr1" in str(key).lower() or "ranker" in str(key).lower()
           for key in manifest):
        errors.append("ranker_field_forbidden")
    allowed = {int(value) for value in manifest.get("allowed_scales") or ()}
    if not allowed or not allowed.issubset(INTERACTION_GAT_ALLOWED_SCALES):
        errors.append("allowed_scales_invalid")
    masks = {
        str(arm): {int(value) for value in scales}
        for arm, scales in dict(manifest.get("arm_scale_mask") or {}).items()
    }
    if set(masks) != {"QD1"} or not masks["QD1"].issubset(allowed):
        errors.append("arm_scale_mask_invalid")
    if not all((request.instance_hash, request.config_hash, request.engine_hash)):
        errors.append("exact_request_binding_incomplete")
    for field in (
        "selector_checkpoint_path", "selector_checkpoint_sha256",
        "feature_envelope", "allowed_exact_engine_hashes",
        "allowed_exact_action_policy_hashes", "allowed_exact_config_hashes",
        "thresholds_by_scale", "evidence_import_path", "evidence_import_sha256",
        "native_binary_sha256",
    ):
        if not manifest.get(field):
            errors.append(f"{field}_missing")
    if int(manifest.get("torch_num_threads") or 0) != 1:
        errors.append("torch_num_threads_must_equal_one")
    architecture = dict(manifest.get("architecture") or {})
    if architecture != {
        "hidden_dim": 16, "attention_heads": 2, "layers": 2,
        "dropout": 0.1, "residual": True, "layer_norm": True,
    }:
        errors.append("v6_architecture_mismatch")
    thresholds = dict(manifest.get("thresholds_by_scale") or {})
    for scale in allowed:
        row = dict(thresholds.get(str(scale)) or {})
        if not all(field in row for field in (
            "minimum_benefit_probability", "minimum_expected_gain",
            "maximum_adverse_probability", "risk_penalty",
        )):
            errors.append(f"scale_{scale}_thresholds_missing")
    for prefix in (
        "evidence_import", "corpus_freeze", "split_freeze",
        "cv_folds_freeze", "normalization", "ood_envelope",
    ):
        path_value = manifest.get(f"{prefix}_path")
        digest = manifest.get(f"{prefix}_sha256")
        if not path_value or not digest:
            errors.append(f"{prefix}_binding_missing")
            continue
        path = Path(str(path_value)).resolve()
        if not path.is_file() or _sha256(path) != str(digest):
            errors.append(f"{prefix}_hash_drift")
    if errors:
        raise ValueError("Interaction-GAT V6 manifest invalid:" + ",".join(errors))


def _load_model_v6(manifest_path, manifest):
    path = Path(str(manifest["selector_checkpoint_path"]))
    if not path.is_absolute():
        path = (Path(manifest_path).parent / path).resolve()
    if not path.is_file():
        raise ValueError("V6 selector checkpoint missing")
    digest = _sha256(path)
    if digest != str(manifest["selector_checkpoint_sha256"]):
        raise ValueError("V6 selector checkpoint hash mismatch")
    key = f"{path}:{digest}"
    with _MODEL_LOCK:
        if key in _MODEL_CACHE:
            return _MODEL_CACHE[key]
        import torch
        from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (
            INTERACTION_FEATURE_SCHEMA_V2,
            INTERACTION_GRAPH_SCHEMA_V1,
            INTERACTION_INPUT_PARITY_CONTRACT_V1,
            interaction_parameter_count,
        )
        from lunar_ice_bpc.guidance.interaction_gat_queue_v6 import (
            INTERACTION_CHECKPOINT_SCHEMA_V6,
            InteractionGATQD1SelectorV6,
        )

        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
        requirements = {
            "schema_version": INTERACTION_CHECKPOINT_SCHEMA_V6,
            "feature_schema_version": INTERACTION_FEATURE_SCHEMA_V2,
            "graph_schema_version": INTERACTION_GRAPH_SCHEMA_V1,
            "input_parity_contract": INTERACTION_INPUT_PARITY_CONTRACT_V1,
            "model_kind": "gat",
            "message_passing_required": True,
            "independently_trained": True,
            "controls_candidate_authorized": False,
            "development_only": True,
            "deployment_authorized": False,
            "production_switch_authorized": False,
        }
        if any(checkpoint.get(key) != value for key, value in requirements.items()):
            raise ValueError("V6 selector checkpoint contract mismatch")
        if tuple(checkpoint.get("action_universe") or ()) != INTERACTION_GAT_ACTION_UNIVERSE_V6:
            raise ValueError("V6 checkpoint action universe mismatch")
        if dict(checkpoint.get("architecture") or {}) != dict(
            manifest.get("architecture") or {}
        ):
            raise ValueError("V6 checkpoint architecture mismatch")
        if _json_sha256(checkpoint["normalization"]) != str(
            manifest["normalization_payload_sha256"]
        ):
            raise ValueError("V6 checkpoint normalization binding drift")
        model = InteractionGATQD1SelectorV6(dict(checkpoint["normalization"]))
        model.load_state_dict(checkpoint["state_dict"], strict=True)
        parameter_count = interaction_parameter_count(model)
        if parameter_count >= MAXIMUM_PARAMETER_COUNT_V6:
            raise ValueError("V6 selector exceeds parameter cap")
        if int(checkpoint.get("parameter_count") or -1) != parameter_count:
            raise ValueError("V6 checkpoint parameter-count binding drift")
        torch.set_num_threads(1)
        model.eval()
        _MODEL_CACHE.clear()
        _MODEL_CACHE[key] = (model, dict(checkpoint), digest)
        return _MODEL_CACHE[key]


def _predictions_v6(output, calibration):
    values = (
        float(output["benefit_probability"][0, 0]),
        float(output["conditional_positive_gain"][0, 0]),
        float(output["adverse_probability"][0, 0]),
    )
    if not all(isfinite(value) for value in values):
        raise ValueError("V6 selector prediction is nonfinite")
    return {
        "QD1": {
            "raw_benefit_probability": values[0],
            "raw_conditional_positive_gain": values[1],
            "raw_adverse_probability": values[2],
        },
        "_calibration_by_scale": dict(calibration or {}),
    }


def _choose_action_v6(predictions, manifest, scale):
    calibration = dict(predictions.pop("_calibration_by_scale", {}) or {})
    calibration_row = dict(calibration.get(str(scale)) or {})
    raw = dict(predictions["QD1"])
    benefit = _calibrate(
        raw["raw_benefit_probability"], calibration_row.get("benefit")
    )
    gain = raw["raw_conditional_positive_gain"] * float(
        calibration_row.get("positive_gain_scale", 1.0)
    )
    adverse = _calibrate(
        raw["raw_adverse_probability"], calibration_row.get("adverse")
    )
    expected = benefit * gain
    row = {
        "benefit_probability": benefit,
        "conditional_positive_gain": gain,
        "adverse_probability": adverse,
        "expected_gain": expected,
    }
    predictions["QD1"] = row
    if not all(isfinite(value) for value in row.values()):
        return "Q0", "nonfinite_scale_calibrated_prediction"
    threshold = dict(
        dict(manifest.get("thresholds_by_scale") or {}).get(str(scale)) or {}
    )
    values = (
        float(threshold.get("minimum_benefit_probability", 2.0)),
        float(threshold.get("minimum_expected_gain", float("inf"))),
        float(threshold.get("maximum_adverse_probability", -1.0)),
        float(threshold.get("risk_penalty", -1.0)),
    )
    benefit_min, gain_min, adverse_max, adverse_lambda = values
    if (
        any(not isfinite(value) for value in values)
        or not 0.0 <= benefit_min <= 1.0 or gain_min < 0.0
        or not 0.0 <= adverse_max <= 1.0 or adverse_lambda < 0.0
    ):
        return "Q0", "invalid_scale_specific_thresholds"
    masks = {
        str(arm): {int(value) for value in scales}
        for arm, scales in dict(manifest.get("arm_scale_mask") or {}).items()
    }
    veto = set(manifest.get("forced_veto_arms") or ())
    veto.update(dict(manifest.get("forced_veto_arms_by_scale") or {}).get(
        str(scale), ()
    ))
    veto.update({"QB1", "QGR1"})
    score = expected - adverse_lambda * adverse
    if (
        "QD1" not in veto and int(scale) in masks.get("QD1", set())
        and benefit >= benefit_min and expected >= gain_min
        and adverse <= adverse_max and score > 0.0
    ):
        return "QD1", "scale_specific_risk_adjusted_gat_selector"
    return "Q0", "qd1_rejected_by_scale_specific_gate"


def _calibrate(value, row):
    probability = min(1.0 - 1.0e-7, max(1.0e-7, float(value)))
    if not row:
        return probability
    row = dict(row)
    slope = float(row.get("slope", 1.0))
    intercept = float(row.get("intercept", 0.0))
    if not isfinite(slope) or not isfinite(intercept) or slope < 0.0:
        raise ValueError("V6 probability calibration invalid")
    score = slope * log(probability / (1.0 - probability)) + intercept
    return 1.0 / (1.0 + exp(-max(-40.0, min(40.0, score))))


def interaction_gat_runtime_implementation_hash_v6() -> str:
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in (
        Path(__file__).resolve(), root / "interaction_gat_queue_v6.py",
        root / "interaction_gat_queue_runtime_v2.py",
        root / "interaction_gat_queue_v2.py",
    ):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _noop(reason, *, enabled=True):
    return {
        "proof_tail_interaction_gat_runtime_enabled": bool(enabled),
        "proof_tail_interaction_gat_manifest_read": False,
        "proof_tail_interaction_gat_graph_build_calls": 0,
        "proof_tail_interaction_gat_model_calls": 0,
        "proof_tail_interaction_gat_ranker_calls": 0,
        "proof_tail_interaction_gat_action": "Q0",
        "proof_tail_interaction_gat_decision_reason": str(reason),
        "proof_tail_interaction_gat_qd1_only": True,
        "proof_tail_interaction_gat_runtime_policy": INTERACTION_GAT_RUNTIME_POLICY_V6,
    }


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _json_sha256(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")).hexdigest()


__all__ = [
    "INTERACTION_GAT_ACTION_UNIVERSE_V6", "INTERACTION_GAT_ARMS_V6",
    "INTERACTION_GAT_MANIFEST_ENV_V6", "INTERACTION_GAT_RUNTIME_POLICY_V6",
    "interaction_gat_runtime_implementation_hash_v6",
    "prepare_root_interaction_gat_qd1_request_v6_from_environment",
]
