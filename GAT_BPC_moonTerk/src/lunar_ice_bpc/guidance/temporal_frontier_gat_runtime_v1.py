"""Fail-closed installer for the root-only P0V4+V5 temporal trial.

The installer is deliberately Torch-free.  It binds an immutable portable
bundle to one in-request Q0 -> QD1 trial; Native owns both queue migrations
and the eventual CONTINUE_QD1/MIGRATE_BACK_TO_Q0 action.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from math import isfinite, log1p
from os import getenv
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping

from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
    BACKEND_OBJECTIVE_OFFICIAL,
    FRONTIER_PROBE_MODE_FORCE_TRIAL_CONTINUE,
    FRONTIER_PROBE_MODE_FORCE_TRIAL_REVERT,
    FRONTIER_PROBE_MODE_LEARNED_AFTER_TRIAL,
    PRICING_LIFECYCLE_SCOPE_ROOT_CG,
    PROOF_QUEUE_POLICY_Q0,
)
from lunar_ice_bpc.guidance.temporal_frontier_gat_v1 import BUNDLE_SCHEMA, SEEDS


MANIFEST_ENV = "LUNAR_ICE_P0V5_TEMPORAL_GAT_V1_MANIFEST"
EVALUATION_ENV = "LUNAR_ICE_P0V5_TEMPORAL_GAT_V1_EVALUATION_MODE"
FORCE_ACTION_ENV = "LUNAR_ICE_P0V5_TEMPORAL_GAT_V1_FORCE_ACTION"
PRODUCTION_REGISTRY_ENV = "LUNAR_ICE_PRODUCTION_POLICY_REGISTRY"
DEFAULT_PRODUCTION_REGISTRY = (
    Path(__file__).resolve().parents[3] / "runs/production_policy_registry_v2.json"
)
MANIFEST_SCHEMA = "lunar_ice_bpc.p0v5_temporal_frontier_runtime_manifest.v1"
RUNTIME_POLICY = "P0V4_V5_ROOT_TEMPORAL_GAT_QD1_REVERSIBLE_V1"
BOUNDARY_BY_SCALE = {30: 4096, 50: 16384}
ALLOWED_K = frozenset({128, 512, 2048})


def prepare_temporal_frontier_request_from_environment(request):
    scale = int(request.data.scale)
    if scale not in BOUNDARY_BY_SCALE:
        return request, _noop("scale_bypasses_temporal_trial", enabled=False)
    if request.pricing_lifecycle_scope != PRICING_LIFECYCLE_SCOPE_ROOT_CG:
        return request, _noop("non_root_lifecycle_bypasses_temporal_trial", enabled=False)
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
        value = _configured_manifest_path()
        if not value:
            return request, _noop("manifest_not_configured", enabled=False)
        manifest_path = Path(value).resolve()
        manifest = _load(manifest_path)
        _validate_manifest(request, manifest, manifest_path)
        evaluation = str(getenv(EVALUATION_ENV, "0")).strip().lower() in {
            "1", "true", "yes", "on",
        }
        if evaluation:
            if not bool(manifest["development_e2e_authorized"]):
                return request, _noop("development_e2e_not_authorized")
        elif not bool(manifest["deployment_authorized"]):
            return request, _noop("deployment_not_authorized")

        forced_action = str(getenv(FORCE_ACTION_ENV, "")).strip().upper()
        if forced_action and not evaluation:
            return request, _noop("force_action_forbidden_outside_evaluation")
        if forced_action not in {
            "", "CONTINUE_QD1", "MIGRATE_BACK_TO_Q0",
        }:
            return request, _noop("unsupported_evaluation_force_action")

        bundle_path = _resolve(manifest_path, manifest["portable_bundle_path"])
        bundle_hash = _sha256(bundle_path)
        if bundle_hash != str(manifest["portable_bundle_file_sha256"]):
            raise ValueError("portable bundle file hash drift")
        bundle = _load(bundle_path)
        controller_kind = str(bundle.get("controller_kind") or "temporal_gat")
        if controller_kind not in {
            "temporal_gat", "no_message", "linear", "mlp",
        }:
            raise ValueError("unsupported temporal controller kind")
        if controller_kind != "temporal_gat" and not evaluation:
            raise ValueError("simple controller is evaluation-only")
        _validate_temporal_bundle(
            request,
            bundle,
            bundle_hash,
            expected_selected_config_sha256=str(
                manifest["selected_exact_config_sha256"]
            ),
            expected_native_binary_sha256=str(
                manifest["native_binary_sha256"]
            ),
            expected_source_freeze_sha256=str(
                manifest["source_freeze_sha256"]
            ),
            expected_experiment_config_sha256=str(
                manifest["experiment_config_sha256"]
            ),
        )
        selected = dict(bundle)
        selected["thresholds"] = dict(
            bundle["thresholds_by_scale"][str(scale)]
        )
        selected["calibration"] = dict(
            bundle["calibration_by_scale"][str(scale)]
        )
        selected["selected_scale"] = scale
        trial_k = int(manifest["trial_pop_budget_by_scale"][str(scale)])
        if int(bundle["trial_pop_budget_by_scale"][str(scale)]) != trial_k:
            raise ValueError("manifest/bundle trial K mismatch")
        probe_mode = {
            "CONTINUE_QD1": FRONTIER_PROBE_MODE_FORCE_TRIAL_CONTINUE,
            "MIGRATE_BACK_TO_Q0": FRONTIER_PROBE_MODE_FORCE_TRIAL_REVERT,
        }.get(forced_action, FRONTIER_PROBE_MODE_LEARNED_AFTER_TRIAL)
        return replace(
            request,
            proof_queue_policy_id=PROOF_QUEUE_POLICY_Q0,
            proof_tail_frontier_probe_mode=probe_mode,
            proof_tail_frontier_probe_boundary=BOUNDARY_BY_SCALE[scale],
            proof_tail_frontier_trial_pop_budget=trial_k,
            proof_tail_frontier_require_root_cg=True,
            proof_tail_frontier_fail_closed_on_ood=True,
            proof_tail_frontier_observation_boundaries=(),
            proof_tail_frontier_context_features=_temporal_context_features(request),
            proof_tail_frontier_gat_bundle=(
                selected
                if probe_mode == FRONTIER_PROBE_MODE_LEARNED_AFTER_TRIAL
                else None
            ),
            proof_tail_frontier_manifest_path=str(manifest_path),
            proof_tail_frontier_manifest_sha256=_sha256(manifest_path),
            proof_tail_frontier_bundle_sha256=bundle_hash,
        ), {
            "proof_tail_frontier_runtime_enabled": True,
            "proof_tail_frontier_runtime_action": (
                "DEFER_TO_NATIVE_TRIAL" if not forced_action else forced_action
            ),
            "proof_tail_frontier_runtime_reason": (
                "temporal_bundle_attached" if not forced_action
                else "evaluation_force_action_attached"
            ),
            "proof_tail_frontier_manifest_sha256": _sha256(manifest_path),
            "proof_tail_frontier_bundle_sha256": bundle_hash,
            "proof_tail_frontier_bundle_load_wall_ms": (
                perf_counter() - started
            ) * 1000.0,
            "proof_tail_frontier_model_call_count": 0,
            "proof_tail_frontier_trial_k": trial_k,
            "proof_tail_frontier_boundary": BOUNDARY_BY_SCALE[scale],
        }
    except Exception as exc:
        return request, {
            **_noop(f"temporal_fail_closed:{type(exc).__name__}"),
            "proof_tail_frontier_runtime_detail": repr(exc),
            "proof_tail_frontier_bundle_load_wall_ms": (
                perf_counter() - started
            ) * 1000.0,
        }


def _validate_manifest(request, manifest: Mapping[str, Any], path: Path) -> None:
    required = {
        "schema_version", "runtime_policy", "action_universe",
        "allowed_scales", "pricing_lifecycle_authority",
        "boundary_by_scale", "trial_pop_budget_by_scale",
        "portable_bundle_path", "portable_bundle_file_sha256",
        "allowed_exact_engine_hashes", "selected_exact_config_sha256",
        "native_binary_sha256", "source_freeze_sha256",
        "experiment_config_sha256",
        "development_e2e_authorized", "deployment_authorized",
        "production_switch_authorized",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise ValueError(f"manifest fields missing: {missing}")
    if manifest["schema_version"] != MANIFEST_SCHEMA:
        raise ValueError("temporal manifest schema drift")
    if manifest["runtime_policy"] != RUNTIME_POLICY:
        raise ValueError("temporal runtime policy drift")
    if list(manifest["action_universe"]) != [
        "CONTINUE_QD1", "MIGRATE_BACK_TO_Q0",
    ]:
        raise ValueError("temporal action universe drift")
    if {int(value) for value in manifest["allowed_scales"]} != {30, 50}:
        raise ValueError("temporal allowed scales drift")
    if manifest["pricing_lifecycle_authority"] != "root_cg_only":
        raise ValueError("temporal lifecycle authority drift")
    if {int(key): int(value) for key, value in
            manifest["boundary_by_scale"].items()} != BOUNDARY_BY_SCALE:
        raise ValueError("temporal boundary drift")
    trial = {
        int(key): int(value)
        for key, value in manifest["trial_pop_budget_by_scale"].items()
    }
    if set(trial) != {30, 50} or any(value not in ALLOWED_K for value in trial.values()):
        raise ValueError("temporal trial K is not frozen to 128/512/2048")
    if str(request.engine_hash) not in {
        str(value) for value in manifest["allowed_exact_engine_hashes"]
    }:
        raise ValueError("temporal exact engine hash mismatch")
    if len(str(manifest["selected_exact_config_sha256"])) != 64:
        raise ValueError("selected exact config hash drift")
    bundle = _resolve(path, manifest["portable_bundle_path"])
    if not bundle.is_file():
        raise ValueError("temporal portable bundle is missing")
    if bool(manifest["production_switch_authorized"]) and not bool(
        manifest["deployment_authorized"]
    ):
        raise ValueError("production authorization requires deployment authorization")


def _temporal_context_features(request) -> tuple[float, ...]:
    """Frozen dual/branch/cut/lifecycle context without hash-derived leakage."""
    values = [0.0] * 28
    cover = [float(value) for value in request.true_duals.cover.values()]
    cuts = [float(value) for value in (request.true_duals.cuts or {}).values()]
    if cover:
        values[0] = log1p(float(len(cover)))
        values[1] = sum(cover) / len(cover)
        values[2] = sum(abs(value) for value in cover) / len(cover)
        values[3] = min(cover)
        values[4] = max(cover)
    values[5] = float(request.true_duals.fleet_limit)
    values[6] = log1p(float(len(cuts)))
    values[7] = sum(abs(value) for value in cuts)
    values[8] = log1p(float(len(request.cut_context.cuts)))
    values[9] = log1p(float(len(request.branch_context.pair_decisions)))
    values[10] = float(bool(request.cut_state_enabled))
    values[11] = float(bool(request.cut_dual_projection_enabled))
    values[12] = log1p(float(request.harvest_target))
    values[13] = log1p(float(request.exact_admission_batch_size))
    values[14] = log1p(float(request.exact_raw_negative_pool_size))
    if request.proof_tail_active_column_count is not None:
        values[15] = log1p(float(request.proof_tail_active_column_count))
        values[16] = 1.0
    if request.proof_tail_round_index is not None:
        values[17] = log1p(float(request.proof_tail_round_index))
        values[18] = 1.0
    if request.proof_tail_dual_delta_l1 is not None:
        values[19] = float(request.proof_tail_dual_delta_l1)
        values[20] = 1.0
    values[21] = log1p(max(0.0, float(request.memory_limit_gb)))
    values[22] = log1p(max(0.0, float(request.wall_time_limit_sec or 0.0)))
    values[23] = float(bool(request.exact_negative_escape_enabled))
    if request.proof_tail_v5_midpoint_wall_sec is not None:
        values[24] = log1p(float(request.proof_tail_v5_midpoint_wall_sec))
        values[25] = 1.0
    values[26] = float(not request.cut_context.empty)
    values[27] = float(not request.branch_context.empty)
    if any(not isfinite(value) for value in values):
        raise ValueError("Temporal-GAT context contains nonfinite values")
    return tuple(values)


def _configured_manifest_path() -> str:
    explicit = str(getenv(MANIFEST_ENV, "")).strip()
    if explicit:
        return explicit
    registry_value = str(getenv(PRODUCTION_REGISTRY_ENV, "")).strip()
    registry_path = (
        Path(registry_value).resolve()
        if registry_value else DEFAULT_PRODUCTION_REGISTRY.resolve()
    )
    if not registry_path.is_file():
        return ""
    registry = _load(registry_path)
    if registry.get("schema_version") != (
        "lunar_ice_bpc.production_policy_registry.v2"
    ):
        raise ValueError("production policy registry schema drift")
    active = str(registry.get("active_policy") or "")
    if active in {"", "no_cut"}:
        return ""
    if active != "P0V4+V5_TEMPORAL_GAT_V1":
        raise ValueError("unknown production policy registry action")
    manifest = Path(str(registry["active_runtime_manifest"])).resolve()
    if not manifest.is_file() or _sha256(manifest) != str(
        registry["active_runtime_manifest_sha256"]
    ):
        raise ValueError("active production runtime manifest hash drift")
    return str(manifest)


def temporal_frontier_runtime_requested() -> bool:
    """Report whether env/production-registry state owns this request path.

    Registry validation errors intentionally propagate here.  The hybrid
    caller then enters the temporal branch, whose installer converts the same
    error into a literal-Q0 fail-closed decision instead of silently falling
    through to an older learned queue policy.
    """

    return bool(_configured_manifest_path())


def _validate_temporal_bundle(
    request,
    bundle: Mapping[str, Any],
    bundle_file_hash: str,
    *,
    expected_selected_config_sha256: str,
    expected_native_binary_sha256: str,
    expected_source_freeze_sha256: str,
    expected_experiment_config_sha256: str,
) -> None:
    if bundle.get("schema_version") != BUNDLE_SCHEMA:
        raise ValueError("Temporal-GAT bundle schema drift")
    if bundle.get("graph_schema_version") != (
        "lunar_ice_bpc.p0v5_temporal_multires_frontier_graph.v2"
    ):
        raise ValueError("Temporal-GAT graph schema drift")
    if bundle.get("feature_schema_version") != (
        "lunar_ice_bpc.p0v5_temporal_multires_features.v2"
    ):
        raise ValueError("Temporal-GAT feature schema drift")
    if dict(bundle.get("architecture_contract") or {}) != {
        "hidden_size": 32,
        "attention_heads": 4,
        "message_layers": 2,
        "message_encoder_shared_across_resolution_time_and_scale": True,
        "pooling": "type_wise_mean_max_attention_v1",
        "trunk": [128, 64],
        "dropout": 0.1,
    }:
        raise ValueError("Temporal-GAT architecture contract drift")
    if dict(bundle.get("ood_policy") or {}) != {
        "kind": "per_feature_fold_train_mean_std_envelope_v1",
        "standard_deviation_radius": 8.0,
        "zero_variance_epsilon": 1.0e-12,
        "action": "MIGRATE_BACK_TO_Q0",
    }:
        raise ValueError("Temporal-GAT OOD policy drift")
    schema_hashes = dict(bundle.get("schema_hashes") or {})
    if schema_hashes.get("graph_schema_sha256") != hashlib.sha256(
        str(bundle["graph_schema_version"]).encode("utf-8")
    ).hexdigest() or schema_hashes.get("feature_schema_sha256") != hashlib.sha256(
        json.dumps({
            "feature_schema_version": bundle["feature_schema_version"],
            "feature_names": bundle.get("feature_names") or {},
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
           allow_nan=False).encode("utf-8")
    ).hexdigest():
        raise ValueError("Temporal-GAT feature/graph schema hash drift")
    normalized = dict(bundle)
    internal_hash = str(normalized.pop("bundle_sha256", ""))
    encoded = json.dumps(
        normalized, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    if hashlib.sha256(encoded).hexdigest() != internal_hash:
        raise ValueError("Temporal-GAT canonical bundle hash drift")
    models = list(bundle.get("models") or ())
    if [int(row["seed"]) for row in models] != list(SEEDS):
        raise ValueError("Temporal-GAT ensemble seed drift")
    for row in models:
        count = sum(
            len(tensor["values"]) for tensor in row["tensors"].values()
        )
        if count <= 0 or count >= 1_000_000:
            raise ValueError("Temporal-GAT parameter-count redline")
    names = dict(bundle.get("feature_names") or {})
    expected_widths = {
        "cell_node": 16, "cell_edge": 10, "node": 40,
        "edge": 11, "counter": 24, "context": 28,
    }
    normalization = dict(bundle.get("normalization") or {})
    for name, width in expected_widths.items():
        if len(names.get(name) or ()) != width:
            raise ValueError(f"Temporal-GAT {name} feature-name drift")
        group = dict(normalization.get(name) or {})
        for key in ("mean", "scale", "minimum", "maximum"):
            values = [float(value) for value in group.get(key) or ()]
            if len(values) != width or any(not isfinite(value) for value in values):
                raise ValueError(f"Temporal-GAT {name}/{key} drift")
        if any(float(value) <= 0.0 for value in group["scale"]):
            raise ValueError(f"Temporal-GAT {name} scale is nonpositive")
        if any(float(left) > float(right) for left, right in zip(
            group["minimum"], group["maximum"]
        )):
            raise ValueError(f"Temporal-GAT {name} OOD range is inverted")
    if {str(key): int(value) for key, value in
            bundle.get("boundary_by_scale", {}).items()} != {
                "30": 4096, "50": 16384,
            }:
        raise ValueError("Temporal-GAT boundary binding drift")
    trial = {
        str(key): int(value)
        for key, value in bundle.get("trial_pop_budget_by_scale", {}).items()
    }
    if set(trial) != {"30", "50"} or any(
        value not in ALLOWED_K for value in trial.values()
    ):
        raise ValueError("Temporal-GAT K binding drift")
    for field in ("calibration_by_scale", "thresholds_by_scale"):
        if set(bundle.get(field) or {}) != {"30", "50"}:
            raise ValueError(f"Temporal-GAT {field} is incomplete")
    bindings = dict(bundle.get("bindings") or {})
    engine_hashes = bindings.get("engine_hashes") or (
        bindings.get("engine_hash"),
    )
    if str(request.engine_hash) not in {str(value) for value in engine_hashes}:
        raise ValueError("Temporal-GAT engine binding mismatch")
    # request.config_hash is a hash of the live SPPRC config dataclass.  It
    # intentionally includes request/RMP-round state and therefore changes on
    # previously unseen production instances.  Training observations remain
    # useful audit evidence, but are not a deployable allowlist.  The immutable
    # selected exact-config file hash below is the production configuration
    # binding.
    observed_config_hashes = bindings.get(
        "source_request_config_hashes_observed_diagnostic_only"
    )
    if not isinstance(observed_config_hashes, list) or not all(
        isinstance(value, str) and value for value in observed_config_hashes
    ):
        raise ValueError("Temporal-GAT diagnostic config-hash binding drift")
    if str(bindings.get("selected_exact_config_sha256")) != str(
        expected_selected_config_sha256
    ):
        raise ValueError("Temporal-GAT exact-config binding mismatch")
    for key, expected in (
        ("native_binary_sha256", expected_native_binary_sha256),
        ("source_freeze_sha256", expected_source_freeze_sha256),
        ("experiment_config_sha256", expected_experiment_config_sha256),
    ):
        if len(str(expected)) != 64 or str(bindings.get(key)) != str(expected):
            raise ValueError(f"Temporal-GAT {key} binding mismatch")
    if str(bindings.get("bundle_file_sha256", bundle_file_hash)) not in {
        "", bundle_file_hash,
    }:
        raise ValueError("Temporal-GAT file self-binding mismatch")


def _load(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _resolve(manifest_path: Path, value: object) -> Path:
    path = Path(str(value))
    if not path.is_absolute():
        path = manifest_path.parent / path
    return path.resolve()


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
        "proof_tail_frontier_model_call_count": 0,
    }
