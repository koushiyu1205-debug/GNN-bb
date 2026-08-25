"""Fail-closed V3 root Interaction-GAT runtime.

The scale and lifecycle checks execute before manifest access, graph building,
or Torch/model imports.  V3 reuses the audited V2 request installation path,
but temporarily binds its immutable V3 schemas and independently trained
hidden-16 GAT loader under a process lock.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
from threading import RLock


INTERACTION_GAT_MANIFEST_ENV_V3 = (
    "LUNAR_ICE_P0V5_ROOT_INTERACTION_GAT_SELECTOR_V3_MANIFEST"
)
INTERACTION_GAT_EVALUATION_ENV_V3 = (
    "LUNAR_ICE_P0V5_ROOT_INTERACTION_GAT_SELECTOR_V3_EVALUATION_MODE"
)
INTERACTION_GAT_MANIFEST_SCHEMA_V2 = (
    "lunar_ice_bpc.p0v5_root_interaction_gat_runtime_manifest.v2"
)
INTERACTION_GAT_RUNTIME_POLICY_V3 = "P0V5_ROOT_INTERACTION_GAT_SELECTOR_V3"
INTERACTION_GAT_ALLOWED_SCALES = frozenset({30, 50})
INTERACTION_GAT_ACTION_UNIVERSE = ("Q0", "QGR1", "QD1", "QB1")
MAXIMUM_PARAMETER_COUNT_V3 = 20_000

_PATCH_LOCK = RLock()
_MODEL_LOCK = RLock()
_MODEL_CACHE = {}


def prepare_root_interaction_gat_request_v3_from_environment(request):
    """Return one exact-safe V3 action or the identical incoming Q0 object."""

    scale = int(request.data.scale)
    if scale not in INTERACTION_GAT_ALLOWED_SCALES:
        return request, _noop("scale_bypasses_before_manifest_torch_graph", enabled=False)
    if str(request.pricing_lifecycle_scope) != "root_cg":
        return request, _noop(
            "non_root_lifecycle_bypasses_before_manifest_torch_graph", enabled=False
        )
    # Importing V2 is framework-free.  The V3 model module, and therefore
    # Torch, is imported only by _load_model_v3 after all fail-closed checks.
    from lunar_ice_bpc.guidance import interaction_gat_queue_runtime_v2 as v2

    with _PATCH_LOCK:
        original = {
            "manifest_env": v2.INTERACTION_GAT_MANIFEST_ENV,
            "evaluation_env": v2.INTERACTION_GAT_EVALUATION_ENV,
            "manifest_schema": v2.INTERACTION_GAT_MANIFEST_SCHEMA_V1,
            "runtime_policy": v2.INTERACTION_GAT_RUNTIME_POLICY_V2,
            "parameter_cap": v2.MAXIMUM_PARAMETER_COUNT,
            "implementation_hash": v2.interaction_gat_runtime_implementation_hash,
            "load_model": v2._load_model,
            "validate_manifest": v2._validate_manifest,
        }
        v2.INTERACTION_GAT_MANIFEST_ENV = INTERACTION_GAT_MANIFEST_ENV_V3
        v2.INTERACTION_GAT_EVALUATION_ENV = INTERACTION_GAT_EVALUATION_ENV_V3
        v2.INTERACTION_GAT_MANIFEST_SCHEMA_V1 = INTERACTION_GAT_MANIFEST_SCHEMA_V2
        v2.INTERACTION_GAT_RUNTIME_POLICY_V2 = INTERACTION_GAT_RUNTIME_POLICY_V3
        v2.MAXIMUM_PARAMETER_COUNT = MAXIMUM_PARAMETER_COUNT_V3
        v2.interaction_gat_runtime_implementation_hash = (
            interaction_gat_runtime_implementation_hash_v3
        )
        v2._load_model = _load_model_v3

        def validate(request_value, manifest):
            original["validate_manifest"](request_value, manifest)
            _validate_v3_extensions(manifest)

        v2._validate_manifest = validate
        try:
            selected, telemetry = v2.prepare_root_interaction_gat_request_from_environment(
                request
            )
        finally:
            v2.INTERACTION_GAT_MANIFEST_ENV = original["manifest_env"]
            v2.INTERACTION_GAT_EVALUATION_ENV = original["evaluation_env"]
            v2.INTERACTION_GAT_MANIFEST_SCHEMA_V1 = original["manifest_schema"]
            v2.INTERACTION_GAT_RUNTIME_POLICY_V2 = original["runtime_policy"]
            v2.MAXIMUM_PARAMETER_COUNT = original["parameter_cap"]
            v2.interaction_gat_runtime_implementation_hash = original["implementation_hash"]
            v2._load_model = original["load_model"]
            v2._validate_manifest = original["validate_manifest"]
    result = dict(telemetry)
    result["proof_tail_interaction_gat_runtime_policy"] = INTERACTION_GAT_RUNTIME_POLICY_V3
    return selected, result


def _validate_v3_extensions(manifest):
    required = {
        "checkpoint_schema_version": "lunar_ice_bpc.p0v5_interaction_gat_checkpoint.v2",
        "dataset_schema_version": "lunar_ice_bpc.p0v5_interaction_gat_training_dataset.v3",
        "corpus_schema_version": "lunar_ice_bpc.p0v5_interaction_gat_corpus_freeze.v3",
        "model_kind": "gat",
        "message_passing_required": True,
        "controls_candidate_authorized": False,
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
        "root_only_authority": True,
    }
    errors = [
        f"{key}_mismatch" for key, value in required.items()
        if manifest.get(key) != value
    ]
    architecture = dict(manifest.get("architecture") or {})
    if architecture != {
        "hidden_dim": 16, "attention_heads": 2, "layers": 2, "dropout": 0.1
    }:
        errors.append("v3_architecture_mismatch")
    for prefix in (
        "source_freeze", "corpus_freeze", "split_freeze", "cv_folds_freeze",
        "normalization", "ood_envelope",
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
        raise ValueError("Interaction-GAT V3 manifest invalid:" + ",".join(errors))


def _load_model_v3(manifest_path, manifest):
    path = Path(str(manifest["selector_checkpoint_path"]))
    if not path.is_absolute():
        path = (Path(manifest_path).parent / path).resolve()
    if not path.is_file():
        raise ValueError("V3 selector checkpoint missing")
    digest = _sha256(path)
    if digest != str(manifest["selector_checkpoint_sha256"]):
        raise ValueError("V3 selector checkpoint hash mismatch")
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
        from lunar_ice_bpc.guidance.interaction_gat_queue_v3 import (
            INTERACTION_CHECKPOINT_SCHEMA_V2,
            InteractionGATSelectorV3,
        )

        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
        requirements = {
            "schema_version": INTERACTION_CHECKPOINT_SCHEMA_V2,
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
            raise ValueError("V3 selector checkpoint contract mismatch")
        if tuple(checkpoint.get("action_universe") or ()) != INTERACTION_GAT_ACTION_UNIVERSE:
            raise ValueError("V3 checkpoint action universe mismatch")
        if dict(checkpoint.get("architecture") or {}) != {
            "hidden_dim": 16, "attention_heads": 2, "layers": 2, "dropout": 0.1
        }:
            raise ValueError("V3 checkpoint architecture mismatch")
        if _json_sha256(checkpoint["normalization"]) != str(
            manifest["normalization_payload_sha256"]
        ):
            raise ValueError("V3 checkpoint normalization binding drift")
        model = InteractionGATSelectorV3(dict(checkpoint["normalization"]))
        model.load_state_dict(checkpoint["state_dict"], strict=True)
        parameter_count = interaction_parameter_count(model)
        if parameter_count >= MAXIMUM_PARAMETER_COUNT_V3:
            raise ValueError("V3 selector exceeds parameter cap")
        if int(checkpoint.get("parameter_count") or -1) != parameter_count:
            raise ValueError("V3 checkpoint parameter-count binding drift")
        torch.set_num_threads(1)
        model.eval()
        _MODEL_CACHE.clear()
        _MODEL_CACHE[key] = (model, dict(checkpoint), digest)
        return _MODEL_CACHE[key]


def interaction_gat_runtime_implementation_hash_v3() -> str:
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for path in (
        Path(__file__).resolve(), root / "interaction_gat_queue_v3.py",
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
        "proof_tail_interaction_gat_ood": False,
        "proof_tail_interaction_gat_graph_build_wall_ms": 0.0,
        "proof_tail_interaction_gat_tensorization_wall_ms": 0.0,
        "proof_tail_interaction_gat_checkpoint_load_wall_ms": 0.0,
        "proof_tail_interaction_gat_torch_first_import_wall_ms": 0.0,
        "proof_tail_interaction_gat_inference_wall_ms": 0.0,
        "proof_tail_interaction_gat_total_prepare_wall_ms": 0.0,
        "proof_tail_interaction_gat_runtime_policy": INTERACTION_GAT_RUNTIME_POLICY_V3,
    }


def _json_sha256(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")).hexdigest()


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


__all__ = [
    "INTERACTION_GAT_EVALUATION_ENV_V3",
    "INTERACTION_GAT_MANIFEST_ENV_V3",
    "INTERACTION_GAT_MANIFEST_SCHEMA_V2",
    "INTERACTION_GAT_RUNTIME_POLICY_V3",
    "interaction_gat_runtime_implementation_hash_v3",
    "prepare_root_interaction_gat_request_v3_from_environment",
]
