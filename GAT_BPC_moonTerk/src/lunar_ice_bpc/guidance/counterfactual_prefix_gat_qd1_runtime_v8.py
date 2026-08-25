"""Fail-closed V8 counterfactual-prefix runtime.

All lifecycle/scale checks happen before manifest I/O.  The two auxiliary
requests are telemetry-only; the returned request is always a fresh exact Q0
request, optionally with the frozen QD1-at-4096 switch enabled.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import importlib
import json
from math import exp, isfinite, log
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping

from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
    BACKEND_MODE_EXACT_PROOF,
    BACKEND_OBJECTIVE_OFFICIAL,
    COUNTERFACTUAL_PREFIX_MODE_Q0,
    COUNTERFACTUAL_PREFIX_MODE_QD1,
    FRONTIER_PROBE_MODE_FORCE_QD1,
    PRICING_LIFECYCLE_SCOPE_ROOT_CG,
    PROOF_QUEUE_POLICY_Q0,
    BackendPricingRequest,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
    _native_request_payload,
    run_native_counterfactual_prefix_raw,
)
from lunar_ice_bpc.guidance.counterfactual_prefix_gat_qd1_v8 import (
    PORTABLE_BUNDLE_SCHEMA_V1,
    RUNTIME_POLICY_V8,
    build_triplet,
    portable_triplet_payload,
)


MANIFEST_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_counterfactual_prefix_gat_qd1_runtime_manifest.v1"
)


@dataclass(frozen=True)
class CounterfactualRuntimeDecision:
    request: BackendPricingRequest
    action: str
    reason: str
    probes_started: bool
    prefix_wall_seconds: float
    graph_wall_seconds: float
    inference_wall_seconds: float
    p_benefit: float = 0.0
    positive_gain: float = 0.0
    p_adverse: float = 1.0
    disagreement: float = 1.0


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    normalized = dict(payload)
    normalized.pop("manifest_sha256", None)
    return hashlib.sha256(json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def _precheck_reason(request: BackendPricingRequest) -> str | None:
    if int(request.data.scale) not in {30, 50}:
        return "scale_bypass"
    if request.pricing_lifecycle_scope != PRICING_LIFECYCLE_SCOPE_ROOT_CG:
        return "lifecycle_bypass"
    if request.mode != BACKEND_MODE_EXACT_PROOF:
        return "non_exact_bypass"
    if request.objective_mode != BACKEND_OBJECTIVE_OFFICIAL:
        return "non_official_bypass"
    if request.proof_queue_policy_id != PROOF_QUEUE_POLICY_Q0:
        return "incoming_non_q0_bypass"
    if not bool(request.proof_tail_fallback_context):
        return "non_v5_fallback_bypass"
    return None


def _load_manifest(request: BackendPricingRequest, path: Path) -> tuple[dict, dict]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if (
        manifest.get("schema_version") != MANIFEST_SCHEMA_V1
        or manifest.get("runtime_policy") != RUNTIME_POLICY_V8
        or manifest.get("model_kind") != "counterfactual_interaction_gat"
        or not bool(manifest.get("message_passing_required"))
        or manifest.get("action_universe") != ["CONTINUE_Q0", "SWITCH_QD1_AT_4096"]
        or sorted(manifest.get("forced_veto_arms") or ()) != ["QB1", "QGR1"]
        or not bool(manifest.get("development_only"))
        or bool(manifest.get("deployment_authorized"))
        or bool(manifest.get("production_switch_authorized"))
        or int(manifest.get("processed_label_boundary") or 0) != 4096
        or int(manifest.get("rollout_budget") or 0) not in {128, 512, 2048}
        or manifest.get("manifest_sha256") != _canonical_hash(manifest)
        or str(manifest.get("engine_hash")) != str(request.engine_hash)
        or str(manifest.get("config_hash")) != str(request.config_hash)
    ):
        raise ValueError("V8 manifest contract mismatch")
    bundle_path = Path(str(manifest["bundle_path"])).resolve()
    if _sha256(bundle_path) != str(manifest["bundle_file_sha256"]):
        raise ValueError("V8 portable bundle hash mismatch")
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    if (
        bundle.get("schema_version") != PORTABLE_BUNDLE_SCHEMA_V1
        or bundle.get("bundle_sha256") != str(manifest["bundle_internal_sha256"])
        or len(bundle.get("models") or ()) != 3
    ):
        raise ValueError("V8 portable bundle contract mismatch")
    return manifest, bundle


def _platt(value: float, row: Mapping[str, object]) -> float:
    if str(row.get("kind")) == "constant":
        return float(row["probability"])
    bounded = min(1.0 - 1.0e-7, max(1.0e-7, value))
    logit = log(bounded / (1.0 - bounded))
    return 1.0 / (1.0 + exp(-(
        float(row.get("a", 1.0)) * logit + float(row.get("b", 0.0))
    )))


def _static_graph_inputs(request: BackendPricingRequest) -> dict[str, Any]:
    payload = _native_request_payload(request)
    branch_pairs = tuple(
        (str(row["task_a"]), str(row["task_b"]))
        for row in payload.get("branch_decisions") or ()
    )
    cut_task_sets = tuple(
        tuple(map(str, row.get("tasks") or ()))
        for row in payload.get("cuts") or ()
    )
    return {
        "tasks": tuple(dict(row) for row in payload["tasks"]),
        "arcs": tuple(dict(row) for row in payload["arcs"]),
        "true_task_duals": {
            str(row["id"]): float(row["dual"]) for row in payload["tasks"]
        },
        "branch_pairs": branch_pairs,
        "cut_task_sets": cut_task_sets,
    }


def _prefix_context_features(request: BackendPricingRequest) -> tuple[float, ...]:
    """Action-previsible lifecycle features shared by both prefix requests."""

    from math import log1p

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


def _triplet_is_ood(triplet, bundle: Mapping[str, Any]) -> bool:
    normalization = dict(bundle["normalization"])

    def outside(rows, group: str) -> bool:
        limits = dict(normalization[group])
        minimum = tuple(map(float, limits["minimum"]))
        maximum = tuple(map(float, limits["maximum"]))
        return any(
            not isfinite(float(value))
            or index >= len(minimum)
            or float(value) < minimum[index]
            or float(value) > maximum[index]
            for row in rows
            for index, value in enumerate(row)
        )

    for graph in (triplet.base, triplet.q0, triplet.qd1):
        if (
            outside(graph.node_features, "node")
            or outside(graph.edge_features, "edge")
            or outside((graph.context_features,), "context")
        ):
            return True
    return outside((triplet.counter_deltas,), "counter")


def _fresh_exact_q0_request(
    request: BackendPricingRequest,
) -> BackendPricingRequest:
    """Construct the independent formal request required after V8 probes."""

    return replace(
        request,
        proof_tail_counterfactual_prefix_mode="disabled",
        proof_tail_frontier_probe_mode="disabled",
        proof_tail_frontier_gat_bundle=None,
    )


def select_counterfactual_prefix_request(
    request: BackendPricingRequest,
    *,
    manifest_path: str | Path,
) -> CounterfactualRuntimeDecision:
    """Return a Q0 or QD1-at-4096 exact request under the frozen V8 gate."""

    reason = _precheck_reason(request)
    if reason is not None:
        return CounterfactualRuntimeDecision(
            request=request,
            action="CONTINUE_Q0",
            reason=reason,
            probes_started=False,
            prefix_wall_seconds=0.0,
            graph_wall_seconds=0.0,
            inference_wall_seconds=0.0,
        )
    try:
        manifest, bundle = _load_manifest(request, Path(manifest_path).resolve())
    except Exception as exc:
        return CounterfactualRuntimeDecision(
            request=request,
            action="CONTINUE_Q0",
            reason=f"manifest_fail_closed:{type(exc).__name__}",
            probes_started=False,
            prefix_wall_seconds=0.0,
            graph_wall_seconds=0.0,
            inference_wall_seconds=0.0,
        )

    started = perf_counter()
    try:
        common = {
            "proof_tail_frontier_probe_mode": "disabled",
            "proof_tail_frontier_gat_bundle": None,
            "exact_negative_escape_enabled": False,
            "proof_tail_counterfactual_max_rollout_budget": int(
                manifest["rollout_budget"]
            ),
            "proof_tail_frontier_context_features": (
                _prefix_context_features(request)
            ),
        }
        q0_request = replace(
            request,
            **common,
            proof_tail_counterfactual_prefix_mode=(
                COUNTERFACTUAL_PREFIX_MODE_Q0
            ),
        )
        qd1_request = replace(
            request,
            **common,
            proof_tail_counterfactual_prefix_mode=(
                COUNTERFACTUAL_PREFIX_MODE_QD1
            ),
        )
        q0_raw = run_native_counterfactual_prefix_raw(q0_request)
        qd1_raw = run_native_counterfactual_prefix_raw(qd1_request)
        prefix_wall = perf_counter() - started
        q0_prefix = dict(
            q0_raw["telemetry"]["proof_queue_counterfactual_prefix"]
        )
        qd1_prefix = dict(
            qd1_raw["telemetry"]["proof_queue_counterfactual_prefix"]
        )
        graph_started = perf_counter()
        triplet = build_triplet(
            q0_prefix,
            qd1_prefix,
            rollout_budget=int(manifest["rollout_budget"]),
            state_hash=str(request.dual_binding_hash or request.instance_hash),
            **_static_graph_inputs(request),
        )
        if _triplet_is_ood(triplet, bundle):
            raise ValueError("V8 triplet outside frozen OOD envelope")
        graph_wall = perf_counter() - graph_started
        inference_started = perf_counter()
        native = importlib.import_module("lunar_spprc_native")
        rows = [
            tuple(native.counterfactual_gat_forward(
                bundle, portable_triplet_payload(triplet), index
            ))
            for index in range(3)
        ]
        inference_wall = perf_counter() - inference_started
        if any(not isfinite(float(value)) for row in rows for value in row):
            raise ValueError("nonfinite V8 portable output")
        scale = str(int(request.data.scale))
        calibration = dict(bundle["calibration_by_scale"][scale])
        threshold = dict(bundle["thresholds_by_scale"][scale])
        raw_benefit = sum(float(row[0]) for row in rows) / len(rows)
        raw_gain = min(float(row[1]) for row in rows)
        raw_adverse = max(float(row[2]) for row in rows)
        p_benefit = _platt(raw_benefit, calibration["benefit"])
        p_adverse = _platt(raw_adverse, calibration["adverse"])
        gain = min(1.0, max(0.0, raw_gain * float(calibration["gain_scale"])))
        disagreement = max(float(row[0]) for row in rows) - min(
            float(row[0]) for row in rows
        )
        expected_gain = p_benefit * gain
        risk = expected_gain - float(threshold["adverse_penalty"]) * p_adverse
        selected = (
            p_benefit >= float(threshold["minimum_benefit_probability"])
            and p_adverse <= float(threshold["maximum_adverse_probability"])
            and expected_gain >= float(threshold["minimum_expected_gain"])
            and risk > 0.0
            and disagreement <= float(threshold["maximum_disagreement"])
        )
        fresh_q0 = _fresh_exact_q0_request(request)
        final_request = (
            replace(
                fresh_q0,
                proof_tail_frontier_probe_mode=FRONTIER_PROBE_MODE_FORCE_QD1,
                proof_tail_frontier_probe_boundary=4096,
            )
            if selected
            else fresh_q0
        )
        return CounterfactualRuntimeDecision(
            request=final_request,
            action="SWITCH_QD1_AT_4096" if selected else "CONTINUE_Q0",
            reason="threshold_accept" if selected else "threshold_reject",
            probes_started=True,
            prefix_wall_seconds=prefix_wall,
            graph_wall_seconds=graph_wall,
            inference_wall_seconds=inference_wall,
            p_benefit=p_benefit,
            positive_gain=gain,
            p_adverse=p_adverse,
            disagreement=disagreement,
        )
    except Exception as exc:
        return CounterfactualRuntimeDecision(
            request=_fresh_exact_q0_request(request),
            action="CONTINUE_Q0",
            reason=f"post_probe_fail_closed:{type(exc).__name__}",
            probes_started=True,
            prefix_wall_seconds=perf_counter() - started,
            graph_wall_seconds=0.0,
            inference_wall_seconds=0.0,
        )
