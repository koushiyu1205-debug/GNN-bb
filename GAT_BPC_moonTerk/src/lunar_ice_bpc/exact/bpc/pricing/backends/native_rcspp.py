"""Project-local adapters for the pinned lab-core/rcspp extension."""

from __future__ import annotations

import atexit
from collections import OrderedDict
from dataclasses import fields, replace
import hashlib
import importlib
import json
from math import isfinite
import multiprocessing
import os
from pathlib import Path
import threading
from time import monotonic, sleep
from typing import Any

from lunar_ice_bpc.domain.scenario import PATH_TYPES
from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
    BACKEND_MODE_EXACT_PROOF,
    BACKEND_OBJECTIVE_PHASE_ONE,
    DSSR_POLICY_VERSION_V1,
    DSSR_POLICY_VERSION_V2,
    DSSR_POLICY_VERSION_NG_V3,
    PROOF_QUEUE_POLICY_Q0,
    BackendPricingRequest,
    BackendResult,
)
from lunar_ice_bpc.exact.bpc.guidance.contracts import (
    CanonicalSolveBindingV2,
    GUIDANCE_MODE_OFF,
    GUIDANCE_MODE_TASK_ARC,
    PricingOrderingHintsV2,
    canonical_arc_candidate_id,
    canonical_universe_hash,
    validate_pricing_ordering_hints,
)
from lunar_ice_bpc.exact.bpc.core.column_signature import (
    column_semantic_signature_hash,
    column_signature_from_journey,
)
from lunar_ice_bpc.exact.core.branching import branch_context_from_payload
from lunar_ice_bpc.exact.core.cuts import (
    CUT_DUAL_PROJECTION_SCHEMA_VERSION,
    CUT_STATE_SCHEMA_VERSION,
    MAX_NATIVE_ACTIVE_CUTS,
    CutContext,
    cut_context_from_payload,
    pricing_cut_context_from_duals,
    stable_payload_hash,
    true_dual_binding_hash,
    validate_live_sri_context,
)
from lunar_ice_bpc.domain.scenario import SERVICE_TIMING_POLICY_ID
from lunar_ice_bpc.exact.core.columns import build_timed_sortie
from lunar_ice_bpc.exact.core.journey import build_journey_column
from lunar_ice_bpc.exact.core.objective import objective_references
from lunar_ice_bpc.exact.master.journey_rmp import (
    JourneyDuals,
    manual_journey_reduced_cost,
    manual_phase_one_journey_reduced_cost,
)


NATIVE_INPROCESS_BACKEND_ID = "native_rcspp_inprocess"
NATIVE_HOST_BACKEND_ID = "native_rcspp_host"
NATIVE_DSSR_INPROCESS_BACKEND_ID = "native_rcspp_dssr_inprocess"
NATIVE_DSSR_HOST_BACKEND_ID = "native_rcspp_dssr_host"
NATIVE_DSSR_V2_INPROCESS_BACKEND_ID = (
    "native_rcspp_dssr_v2_inprocess"
)
NATIVE_DSSR_V2_HOST_BACKEND_ID = "native_rcspp_dssr_v2_host"
NATIVE_NG_DSSR_V3_INPROCESS_BACKEND_ID = (
    "native_rcspp_ng_dssr_v3_inprocess"
)
NATIVE_NG_DSSR_V3_HOST_BACKEND_ID = (
    "native_rcspp_ng_dssr_v3_host"
)
NATIVE_HOST_PROTOCOL = "lunar_spprc_host.v3"
DSSR_POLICY_VERSION = DSSR_POLICY_VERSION_V1
DSSR_V2_POLICY_VERSION = DSSR_POLICY_VERSION_V2
NG_DSSR_V3_POLICY_VERSION = DSSR_POLICY_VERSION_NG_V3
_GIB = 1024**3
_MIB = 1024**2
# The request limit is enforced cooperatively inside the native labeling loop,
# which can then return an audited MEMORY_LIMIT result.  The host-side RSS
# check is only a last-resort guard for a wedged or incompatible native
# extension.  Giving it bounded headroom prevents it from racing the native
# check and killing the process before the legal incomplete result is sent.
_HOST_MEMORY_WATCHDOG_MIN_HEADROOM_BYTES = 128 * _MIB
_HOST_MEMORY_WATCHDOG_MAX_HEADROOM_BYTES = 2 * _GIB
_HOST_MEMORY_WATCHDOG_HEADROOM_FRACTION = 0.25
_HOST_RUNTIME_MEMORY_POLICY_ID = (
    "parent_aware_memavailable_hard_guard_v1"
)
_HOST_RUNTIME_AVAILABLE_RESERVE_BYTES = 2 * _GIB
_HOST_RUNTIME_MIN_NATIVE_BUDGET_BYTES = 256 * _MIB
# Large exact-pricing calls can leave several GiB of freed label arenas mapped
# in a persistent host.  Reusing that high-RSS process makes the next call hit
# the cooperative memory limit before it has built a meaningful frontier.
# Recycle only large-scale hosts after a genuinely heavy call; scale <= 30
# keeps the existing same-instance delta fast path unchanged.
_HOST_RECYCLE_POLICY_ID = "large_scale_heavy_response_v1"
_HOST_RECYCLE_MIN_TASK_COUNT = 50
_HOST_RECYCLE_MIN_PEAK_BYTES = 1 * _GIB
_HOST_RECYCLE_LIMIT_FRACTION = 0.25
_NATIVE_CUT_STATE_BUILD_SCHEMA = (
    "packed_exact_overlap_u64_sri3_2bit_sri5_3bit_v2"
)
_STATIC_PAYLOAD_CACHE_LOCK = threading.RLock()
_STATIC_PAYLOAD_CACHE: OrderedDict[str, dict] = OrderedDict()
_STATIC_PAYLOAD_CACHE_MAX_ENTRIES = 16
_SNAPSHOT_LOCK = threading.RLock()
_SNAPSHOT_COUNT = 0
_SNAPSHOT_COUNT_BY_INSTANCE: dict[str, int] = {}
DEVELOPMENT_ORACLE_TASK_PRIORITY_ENV = (
    "LUNAR_ICE_DEVELOPMENT_ORACLE_TASK_PRIORITY_JSON"
)
_DEVELOPMENT_ORACLE_PRIORITY_CACHE: dict[
    tuple[str, int], dict[str, Any]
] = {}


class NativeRcsppInprocessBackend:
    backend_id = NATIVE_INPROCESS_BACKEND_ID

    def solve(self, request: BackendPricingRequest) -> BackendResult:
        request = _maybe_attach_environment_guidance(request)
        capability_blockers = _capability_blockers(request)
        if capability_blockers:
            return _empty_result(
                self.backend_id,
                "UNSUPPORTED_FEATURE",
                blockers=capability_blockers,
            )
        binding_blockers = _binding_blockers(request)
        if binding_blockers:
            return _empty_result(self.backend_id, "HASH_MISMATCH", blockers=binding_blockers)
        _maybe_record_pre_solve_exact_snapshot(request)
        try:
            native = importlib.import_module("lunar_spprc_native")
        except Exception as exc:
            return _empty_result(
                self.backend_id,
                "BACKEND_UNAVAILABLE",
                blockers=("native_extension_unavailable",),
                telemetry={"error": repr(exc)},
            )

        build_blockers = _native_build_capability_blockers(
            request,
            native,
        )
        if build_blockers:
            return _empty_result(
                self.backend_id,
                "UNSUPPORTED_FEATURE",
                blockers=build_blockers,
            )
        try:
            raw = dict(native.solve(_native_request_payload(request)))
        except Exception as exc:
            return _empty_result(
                self.backend_id,
                "BACKEND_ERROR",
                blockers=("native_backend_exception",),
                telemetry={"error": repr(exc)},
            )
        return _audit_native_result(request, raw, backend_id=self.backend_id)


def run_native_counterfactual_prefix_raw(
    request: BackendPricingRequest,
) -> dict[str, Any]:
    """Execute one V8 telemetry-only prefix without exact-result auditing.

    Prefix requests deliberately use the exact pricing trajectory but are not
    exact results.  Feeding them through :func:`_audit_native_result` would
    correctly create certificate blockers; this narrow entry point instead
    validates the route/certificate suppression contract and returns the raw
    diagnostic payload to the V8 experiment controller.
    """

    mode = str(request.proof_tail_counterfactual_prefix_mode)
    if mode not in {
        "counterfactual_q0_prefix",
        "counterfactual_qd1_prefix",
    }:
        raise ValueError("request is not an active V8 counterfactual prefix")
    capability_blockers = _capability_blockers(request)
    if capability_blockers:
        raise RuntimeError(
            "counterfactual prefix capability blockers: "
            + ",".join(capability_blockers)
        )
    binding_blockers = _binding_blockers(request)
    if binding_blockers:
        raise RuntimeError(
            "counterfactual prefix binding blockers: "
            + ",".join(binding_blockers)
        )
    native = importlib.import_module("lunar_spprc_native")
    build_blockers = _native_build_capability_blockers(request, native)
    if build_blockers:
        raise RuntimeError(
            "counterfactual prefix build blockers: "
            + ",".join(build_blockers)
        )
    raw = dict(native.solve(_native_request_payload(request)))
    telemetry = dict(raw.get("telemetry") or {}).get(
        "proof_queue_counterfactual_prefix"
    )
    prefix = dict(telemetry or {})
    if (
        raw.get("routes")
        or raw.get("certificate") is not None
        or bool(raw.get("search_exhaustive"))
        or bool(raw.get("frontier_empty"))
        or not bool(raw.get("truncated_diagnostic"))
        or bool(raw.get("exact"))
        or not bool(prefix.get("routes_suppressed"))
        or not bool(prefix.get("certificate_suppressed"))
    ):
        raise RuntimeError("counterfactual prefix public-result redline")
    return raw


class NativeRcsppHostBackend:
    """Persistent crash/RSS-isolated host with same-instance delta IPC."""

    backend_id = NATIVE_HOST_BACKEND_ID
    _runtime: _PersistentHostRuntime | None = None
    _lock = threading.RLock()

    def solve(self, request: BackendPricingRequest) -> BackendResult:
        request = _maybe_attach_environment_guidance(request)
        capability_blockers = _capability_blockers(request)
        if capability_blockers:
            return _empty_result(
                self.backend_id,
                "UNSUPPORTED_FEATURE",
                blockers=capability_blockers,
            )
        binding_blockers = _binding_blockers(request)
        if binding_blockers:
            return _empty_result(
                self.backend_id,
                "HASH_MISMATCH",
                blockers=binding_blockers,
            )
        _maybe_record_pre_solve_exact_snapshot(request)
        with self._lock:
            if self.__class__._runtime is None:
                self.__class__._runtime = _PersistentHostRuntime(
                    backend_id=self.backend_id
                )
            return self.__class__._runtime.solve(request)

    @classmethod
    def close(cls) -> None:
        with cls._lock:
            if cls._runtime is not None:
                cls._runtime.close()
                cls._runtime = None


def _dssr_request(request: BackendPricingRequest) -> BackendPricingRequest:
    dssr_eligible = bool(request.exact_proof_mode)
    return replace(
        request,
        dssr_enabled=dssr_eligible,
        exact_negative_escape_enabled=False,
        dssr_policy_version=(
            DSSR_POLICY_VERSION if dssr_eligible else ""
        ),
        completion_bound_enabled=(
            False
            if request.exact_proof_mode
            else request.completion_bound_enabled
        ),
        subset_dominance_enabled=(
            False
            if request.exact_proof_mode
            else request.subset_dominance_enabled
        ),
    )


def _dssr_v2_request(
    request: BackendPricingRequest,
) -> BackendPricingRequest:
    dssr_eligible = bool(request.exact_proof_mode)
    if not dssr_eligible:
        return replace(
            request,
            dssr_enabled=False,
            dssr_policy_version="",
        )
    batch_target = max(
        1,
        min(int(request.dssr_negative_batch_target), 64),
    )
    pressure_bucket = int(request.dssr_pressure_max_bucket_size)
    pressure_checks = int(
        request.dssr_pressure_max_candidate_checks
    )
    source_config_hash = str(request.config_hash)
    dssr_config_hash = stable_payload_hash(
        {
            "schema_version": (
                "lunar_ice_bpc.dssr_v2_backend_config.v1"
            ),
            "source_config_hash": source_config_hash,
            "dssr_policy_version": DSSR_V2_POLICY_VERSION,
            "dssr_negative_batch_target": batch_target,
            "dssr_pressure_refinement_enabled": True,
            "dssr_pressure_max_bucket_size": pressure_bucket,
            "dssr_pressure_max_candidate_checks": pressure_checks,
        }
    )
    return replace(
        request,
        dssr_enabled=True,
        exact_negative_escape_enabled=False,
        dssr_policy_version=DSSR_V2_POLICY_VERSION,
        dssr_negative_batch_target=batch_target,
        dssr_pressure_refinement_enabled=True,
        dssr_pressure_max_bucket_size=pressure_bucket,
        dssr_pressure_max_candidate_checks=pressure_checks,
        config_hash=dssr_config_hash,
        completion_bound_enabled=False,
        subset_dominance_enabled=False,
    )


def _ng_dssr_v3_request(
    request: BackendPricingRequest,
) -> BackendPricingRequest:
    dssr_eligible = bool(request.exact_proof_mode)
    if not dssr_eligible:
        return replace(
            request,
            dssr_enabled=False,
            dssr_policy_version="",
        )
    batch_target = max(
        1,
        min(int(request.dssr_negative_batch_target), 64),
    )
    neighborhood_size = max(
        1,
        min(
            int(request.ng_dssr_initial_neighborhood_size),
            int(request.data.scale),
        ),
    )
    source_config_hash = str(request.config_hash)
    ng_config_hash = stable_payload_hash(
        {
            "schema_version": (
                "lunar_ice_bpc.ng_dssr_v3_backend_config.v1"
            ),
            "source_config_hash": source_config_hash,
            "dssr_policy_version": NG_DSSR_V3_POLICY_VERSION,
            "dssr_negative_batch_target": batch_target,
            "ng_dssr_initial_neighborhood_size": neighborhood_size,
            "ng_memory_update": (
                "pi_intersect_gamma_target_union_target_v1"
            ),
            "elementarity_audit": (
                "all_raw_negative_routes_all_adjacent_cycles_v1"
            ),
        }
    )
    return replace(
        request,
        dssr_enabled=True,
        exact_negative_escape_enabled=False,
        dssr_policy_version=NG_DSSR_V3_POLICY_VERSION,
        dssr_negative_batch_target=batch_target,
        dssr_pressure_refinement_enabled=False,
        ng_dssr_initial_neighborhood_size=neighborhood_size,
        config_hash=ng_config_hash,
        completion_bound_enabled=False,
        subset_dominance_enabled=False,
        proof_queue_policy_id=PROOF_QUEUE_POLICY_Q0,
        guidance_mode=GUIDANCE_MODE_OFF,
        guidance_hints=None,
    )


def _with_dssr_policy_telemetry(
    result: BackendResult,
    *,
    exact_proof_mode: bool,
    boundary_fallback_used: bool = False,
    dssr_attempt: BackendResult | None = None,
) -> BackendResult:
    telemetry = dict(result.telemetry or {})
    telemetry.update(
        {
            "dssr_exact_proof_eligible": bool(exact_proof_mode),
            "dssr_policy_attempted": bool(exact_proof_mode),
            "dssr_non_exact_bypassed": bool(not exact_proof_mode),
            "dssr_bypass_reason": (
                "negative_harvest_preserves_p0"
                if not exact_proof_mode
                else ""
            ),
            "dssr_boundary_audit_fallback_used": bool(
                boundary_fallback_used
            ),
        }
    )
    if dssr_attempt is not None:
        attempt_telemetry = dict(dssr_attempt.telemetry or {})
        telemetry["dssr_boundary_attempt"] = {
            "engine_status": dssr_attempt.engine_status,
            "search_exhaustive": dssr_attempt.search_exhaustive,
            "frontier_empty": dssr_attempt.frontier_empty,
            "labels_dropped": dssr_attempt.labels_dropped,
            "public_column_count": len(dssr_attempt.columns),
            "native_raw_best_found_rc": attempt_telemetry.get(
                "native_raw_best_found_rc"
            ),
            "processed_labels": attempt_telemetry.get(
                "processed_labels"
            ),
            "extended_labels": attempt_telemetry.get(
                "extended_labels"
            ),
            "wall_time_seconds": attempt_telemetry.get(
                "wall_time_seconds"
            ),
            "reconstruction_audit": attempt_telemetry.get(
                "reconstruction_audit"
            )
            or [],
        }
    return replace(result, telemetry=telemetry)


def _dssr_boundary_audit_requires_elementary_fallback(
    result: BackendResult,
) -> bool:
    telemetry = dict(result.telemetry or {})
    reconstruction_rows = list(
        telemetry.get("reconstruction_audit") or []
    )
    return bool(
        result.engine_status == "MAX_SOLUTIONS"
        and not result.columns
        and not result.labels_dropped
        and bool(telemetry.get("dssr_elementary_witness_returned"))
        and reconstruction_rows
        and all(bool(row.get("accepted")) for row in reconstruction_rows)
    )


class NativeDssrInprocessBackend(NativeRcsppInprocessBackend):
    """In-process exact-safe DSSR backend for scales whose P0 is in-process."""

    backend_id = NATIVE_DSSR_INPROCESS_BACKEND_ID

    def solve(self, request: BackendPricingRequest) -> BackendResult:
        exact_proof_mode = bool(request.exact_proof_mode)
        result = super().solve(_dssr_request(request))
        if _dssr_boundary_audit_requires_elementary_fallback(result):
            fallback = super().solve(request)
            return _with_dssr_policy_telemetry(
                fallback,
                exact_proof_mode=exact_proof_mode,
                boundary_fallback_used=True,
                dssr_attempt=result,
            )
        return _with_dssr_policy_telemetry(
            result,
            exact_proof_mode=exact_proof_mode,
        )


class NativeDssrHostBackend(NativeRcsppHostBackend):
    """Host-isolated exact-safe DSSR backend for every supported scale.

    Harvest calls deliberately retain the ordinary Native implementation.
    Every exact-proof call uses the same counterexample-guided state-space
    relaxation, irrespective of instance scale.  The distinct backend ID is
    part of the engine hash, so P0 and DSSR evidence cannot share a solve
    binding accidentally.
    """

    backend_id = NATIVE_DSSR_HOST_BACKEND_ID
    _runtime: _PersistentHostRuntime | None = None
    _lock = threading.RLock()

    def solve(self, request: BackendPricingRequest) -> BackendResult:
        exact_proof_mode = bool(request.exact_proof_mode)
        result = super().solve(_dssr_request(request))
        if _dssr_boundary_audit_requires_elementary_fallback(result):
            fallback = super().solve(request)
            return _with_dssr_policy_telemetry(
                fallback,
                exact_proof_mode=exact_proof_mode,
                boundary_fallback_used=True,
                dssr_attempt=result,
            )
        return _with_dssr_policy_telemetry(
            result,
            exact_proof_mode=exact_proof_mode,
        )


class NativeDssrV2InprocessBackend(NativeRcsppInprocessBackend):
    """In-process deterministic DSSR V2 backend."""

    backend_id = NATIVE_DSSR_V2_INPROCESS_BACKEND_ID

    def solve(self, request: BackendPricingRequest) -> BackendResult:
        exact_proof_mode = bool(request.exact_proof_mode)
        result = super().solve(_dssr_v2_request(request))
        return _with_dssr_policy_telemetry(
            result,
            exact_proof_mode=exact_proof_mode,
        )


class NativeDssrV2HostBackend(NativeRcsppHostBackend):
    """Host-isolated deterministic DSSR V2 backend."""

    backend_id = NATIVE_DSSR_V2_HOST_BACKEND_ID
    _runtime: _PersistentHostRuntime | None = None
    _lock = threading.RLock()

    def solve(self, request: BackendPricingRequest) -> BackendResult:
        exact_proof_mode = bool(request.exact_proof_mode)
        result = super().solve(_dssr_v2_request(request))
        return _with_dssr_policy_telemetry(
            result,
            exact_proof_mode=exact_proof_mode,
        )


class NativeNgDssrV3InprocessBackend(NativeRcsppInprocessBackend):
    """In-process elementary-safe ng-memory DSSR V3 backend."""

    backend_id = NATIVE_NG_DSSR_V3_INPROCESS_BACKEND_ID

    def solve(self, request: BackendPricingRequest) -> BackendResult:
        exact_proof_mode = bool(request.exact_proof_mode)
        result = super().solve(_ng_dssr_v3_request(request))
        return _with_dssr_policy_telemetry(
            result,
            exact_proof_mode=exact_proof_mode,
        )


class NativeNgDssrV3HostBackend(NativeRcsppHostBackend):
    """Host-isolated elementary-safe ng-memory DSSR V3 backend."""

    backend_id = NATIVE_NG_DSSR_V3_HOST_BACKEND_ID
    _runtime: _PersistentHostRuntime | None = None
    _lock = threading.RLock()

    def solve(self, request: BackendPricingRequest) -> BackendResult:
        exact_proof_mode = bool(request.exact_proof_mode)
        result = super().solve(_ng_dssr_v3_request(request))
        return _with_dssr_policy_telemetry(
            result,
            exact_proof_mode=exact_proof_mode,
        )


class _PersistentHostRuntime:
    def __init__(self, *, backend_id: str = NATIVE_HOST_BACKEND_ID) -> None:
        self.backend_id = str(backend_id)
        self.context = multiprocessing.get_context("spawn")
        self.process = None
        self.connection = None
        self.build_hash = ""
        self.loaded_instance_hash = ""
        self.request_count = 0
        self.next_request_id = 1

    def solve(self, request: BackendPricingRequest) -> BackendResult:
        expected_hash = _host_build_hash(self.backend_id)
        stale_restarted = False
        if not self._ready() or self.build_hash != expected_hash:
            stale = bool(self._ready() and self.build_hash != expected_hash)
            stale_restarted = stale
            self.close()
            start_error = self._start(expected_hash)
            if start_error:
                return _empty_result(
                    self.backend_id,
                    "HASH_MISMATCH" if stale else "BACKEND_UNAVAILABLE",
                    blockers=(
                        "stale_host_build_hash" if stale else "host_startup_failed",
                    ),
                    telemetry={"error": start_error},
                )

        from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_instance_hash

        instance_hash = request.instance_hash or spprc_instance_hash(request.data)
        request_id = self.next_request_id
        self.next_request_id += 1
        reused = self.request_count > 0
        same_instance = bool(self.loaded_instance_hash == instance_hash)
        request_kind = "solve_delta" if same_instance else "load_solve"
        configured_native_memory_limit_bytes = int(
            float(request.memory_limit_gb) * _GIB
        )
        host_rss_at_request_start_bytes = _process_rss_bytes(
            self.process.pid
        )
        available_memory_at_request_start_bytes = (
            _available_memory_bytes()
        )
        memory_budget = _dynamic_host_memory_budget(
            configured_native_limit_bytes=(
                configured_native_memory_limit_bytes
            ),
            host_rss_bytes=host_rss_at_request_start_bytes,
            available_memory_bytes=(
                available_memory_at_request_start_bytes
            ),
        )
        native_memory_limit_bytes = int(
            memory_budget["native_limit_bytes"]
        )
        rss_limit_bytes = int(
            memory_budget["watchdog_limit_bytes"]
        )
        if bool(memory_budget["preflight_rejected"]):
            self.close()
            return _empty_result(
                self.backend_id,
                "MEMORY_LIMIT",
                blockers=("host_runtime_memory_preflight",),
                telemetry={
                    "host_partial_result_received": False,
                    "host_proof_state_discarded": True,
                    "host_runtime_memory_policy_id": (
                        _HOST_RUNTIME_MEMORY_POLICY_ID
                    ),
                    "configured_native_memory_limit_bytes": (
                        configured_native_memory_limit_bytes
                    ),
                    "native_memory_limit_bytes": (
                        native_memory_limit_bytes
                    ),
                    "host_memory_watchdog_limit_bytes": (
                        rss_limit_bytes
                    ),
                    "host_rss_at_request_start_bytes": (
                        host_rss_at_request_start_bytes
                    ),
                    "available_memory_at_request_start_bytes": (
                        available_memory_at_request_start_bytes
                    ),
                    "host_runtime_available_reserve_bytes": (
                        _HOST_RUNTIME_AVAILABLE_RESERVE_BYTES
                    ),
                    "host_runtime_memory_budget_clamped": bool(
                        memory_budget["clamped"]
                    ),
                },
            )
        effective_request = replace(
            request,
            memory_limit_gb=(
                float(native_memory_limit_bytes) / float(_GIB)
            ),
        )
        message = {
            "protocol": NATIVE_HOST_PROTOCOL,
            "kind": request_kind,
            "request_id": request_id,
            "expected_build_hash": expected_hash,
            "instance_hash": instance_hash,
            "request": _request_ipc_payload(
                effective_request,
                include_data=not same_instance,
            ),
        }
        try:
            self.connection.send(message)
        except (BrokenPipeError, EOFError, OSError, TypeError) as exc:
            exitcode = None if self.process is None else self.process.exitcode
            self.close()
            return _empty_result(
                self.backend_id,
                "BACKEND_CRASH",
                blockers=("host_send_failed",),
                telemetry={"error": repr(exc), "host_exitcode": exitcode},
            )

        deadline = (
            monotonic() + float(effective_request.wall_time_limit_sec) + 1.0
            if effective_request.wall_time_limit_sec is not None
            else None
        )
        peak_rss = 0
        minimum_available_memory_bytes = (
            available_memory_at_request_start_bytes
        )
        stop_reason = ""
        memory_guard_trigger = ""
        try:
            while self._ready() and not self.connection.poll(0.05):
                rss = _process_rss_bytes(self.process.pid)
                peak_rss = max(peak_rss, rss)
                available_memory_bytes = _available_memory_bytes()
                if available_memory_bytes is not None:
                    if minimum_available_memory_bytes is None:
                        minimum_available_memory_bytes = (
                            available_memory_bytes
                        )
                    else:
                        minimum_available_memory_bytes = min(
                            minimum_available_memory_bytes,
                            available_memory_bytes,
                        )
                if deadline is not None and monotonic() >= deadline:
                    stop_reason = "TIMEOUT"
                    break
                if rss_limit_bytes > 0 and rss >= rss_limit_bytes:
                    stop_reason = "MEMORY_LIMIT"
                    memory_guard_trigger = "host_rss_watchdog"
                    break
                if (
                    available_memory_bytes is not None
                    and available_memory_bytes
                    < _HOST_RUNTIME_AVAILABLE_RESERVE_BYTES
                ):
                    stop_reason = "MEMORY_LIMIT"
                    memory_guard_trigger = "host_memavailable_reserve"
                    break
                sleep(0.01)
        except KeyboardInterrupt:
            self.close()
            raise
        if stop_reason:
            exitcode = self._terminate()
            return _empty_result(
                self.backend_id,
                stop_reason,
                blockers=(f"host_{stop_reason.lower()}",),
                telemetry={
                    "host_exitcode": exitcode,
                    "host_peak_rss_bytes": peak_rss,
                    "configured_native_memory_limit_bytes": (
                        configured_native_memory_limit_bytes
                    ),
                    "native_memory_limit_bytes": native_memory_limit_bytes,
                    "host_memory_watchdog_limit_bytes": rss_limit_bytes,
                    "host_runtime_memory_policy_id": (
                        _HOST_RUNTIME_MEMORY_POLICY_ID
                    ),
                    "host_runtime_memory_guard_trigger": (
                        memory_guard_trigger
                    ),
                    "host_rss_at_request_start_bytes": (
                        host_rss_at_request_start_bytes
                    ),
                    "available_memory_at_request_start_bytes": (
                        available_memory_at_request_start_bytes
                    ),
                    "minimum_available_memory_bytes": (
                        minimum_available_memory_bytes
                    ),
                    "host_runtime_available_reserve_bytes": (
                        _HOST_RUNTIME_AVAILABLE_RESERVE_BYTES
                    ),
                    "host_runtime_memory_budget_clamped": bool(
                        memory_budget["clamped"]
                    ),
                    "host_partial_result_received": False,
                    "host_proof_state_discarded": True,
                },
            )
        if not self._ready() and not self.connection.poll(0.1):
            exitcode = None if self.process is None else self.process.exitcode
            self.close()
            return _empty_result(
                self.backend_id,
                "BACKEND_CRASH",
                blockers=("host_crashed_without_result",),
                telemetry={
                    "host_exitcode": exitcode,
                    "host_peak_rss_bytes": peak_rss,
                    "host_partial_result_received": False,
                },
            )
        try:
            response = self.connection.recv()
        except (EOFError, OSError) as exc:
            exitcode = None if self.process is None else self.process.exitcode
            self.close()
            return _empty_result(
                self.backend_id,
                "BACKEND_CRASH",
                blockers=("host_response_failed",),
                telemetry={"error": repr(exc), "host_exitcode": exitcode},
            )
        if (
            response.get("protocol") != NATIVE_HOST_PROTOCOL
            or int(response.get("request_id") or -1) != request_id
            or response.get("build_hash") != expected_hash
            or response.get("instance_hash") != instance_hash
        ):
            self.close()
            return _empty_result(
                self.backend_id,
                "HASH_MISMATCH",
                blockers=("stale_host_response_binding",),
                telemetry={"response": repr(response)[:1000]},
            )
        if response.get("kind") != "ok":
            return _empty_result(
                self.backend_id,
                "BACKEND_ERROR",
                blockers=("host_backend_exception",),
                telemetry={"error": response.get("error")},
            )
        self.loaded_instance_hash = instance_hash
        self.request_count += 1
        result = response["result"]
        host_pid = self.process.pid
        task_count = len(request.data.task_ids)
        recycle_threshold_bytes = _host_recycle_threshold_bytes(
            native_memory_limit_bytes
        )
        recycle_after_response = _should_recycle_host_after_response(
            task_count=task_count,
            peak_rss_bytes=peak_rss,
            native_memory_limit_bytes=native_memory_limit_bytes,
        )
        telemetry = dict(result.telemetry or {})
        telemetry.update(
            {
                "host_protocol": NATIVE_HOST_PROTOCOL,
                "host_pid": host_pid,
                "host_reused": reused,
                "host_same_instance_delta": same_instance,
                "host_request_kind": request_kind,
                "host_request_count": self.request_count,
                "host_peak_rss_bytes": peak_rss,
                "configured_native_memory_limit_bytes": (
                    configured_native_memory_limit_bytes
                ),
                "native_memory_limit_bytes": native_memory_limit_bytes,
                "host_memory_watchdog_limit_bytes": rss_limit_bytes,
                "host_runtime_memory_policy_id": (
                    _HOST_RUNTIME_MEMORY_POLICY_ID
                ),
                "host_runtime_memory_guard_trigger": "",
                "host_rss_at_request_start_bytes": (
                    host_rss_at_request_start_bytes
                ),
                "available_memory_at_request_start_bytes": (
                    available_memory_at_request_start_bytes
                ),
                "minimum_available_memory_bytes": (
                    minimum_available_memory_bytes
                ),
                "host_runtime_available_reserve_bytes": (
                    _HOST_RUNTIME_AVAILABLE_RESERVE_BYTES
                ),
                "host_runtime_memory_budget_clamped": bool(
                    memory_budget["clamped"]
                ),
                "host_build_hash": expected_hash,
                "host_stale_restarted": stale_restarted,
                "host_partial_result_received": bool(result.columns),
                "host_proof_state_discarded": not result.search_exhaustive,
                "host_recycle_policy_id": _HOST_RECYCLE_POLICY_ID,
                "host_recycle_threshold_bytes": recycle_threshold_bytes,
                "host_recycled_after_response": recycle_after_response,
            }
        )
        audited_result = replace(
            result,
            backend_id=self.backend_id,
            telemetry=telemetry,
        )
        if recycle_after_response:
            self.close()
        return audited_result

    def _start(self, expected_hash: str) -> str:
        parent, child = self.context.Pipe(duplex=True)
        process = self.context.Process(
            target=_persistent_host_main,
            args=(child, self.backend_id),
            daemon=True,
        )
        process.start()
        child.close()
        self.process = process
        self.connection = parent
        if not parent.poll(10.0):
            self.close()
            return "host handshake timed out"
        try:
            response = parent.recv()
        except (EOFError, OSError) as exc:
            self.close()
            return repr(exc)
        if (
            response.get("protocol") != NATIVE_HOST_PROTOCOL
            or response.get("kind") != "ready"
            or response.get("build_hash") != expected_hash
        ):
            self.close()
            return f"invalid host handshake: {response!r}"
        self.build_hash = expected_hash
        self.loaded_instance_hash = ""
        self.request_count = 0
        return ""

    def _ready(self) -> bool:
        return bool(
            self.process is not None
            and self.connection is not None
            and self.process.is_alive()
        )

    def _terminate(self):
        process = self.process
        if process is None:
            self.close()
            return None
        process.terminate()
        process.join(timeout=2.0)
        if process.is_alive():
            process.kill()
            process.join(timeout=1.0)
        exitcode = process.exitcode
        self.close()
        return exitcode

    def close(self) -> None:
        process = self.process
        connection = self.connection
        if process is not None and process.is_alive() and connection is not None:
            try:
                connection.send({"protocol": NATIVE_HOST_PROTOCOL, "kind": "shutdown"})
            except (BrokenPipeError, EOFError, OSError):
                pass
            process.join(timeout=1.0)
            if process.is_alive():
                process.terminate()
                process.join(timeout=1.0)
        if connection is not None:
            connection.close()
        self.process = None
        self.connection = None
        self.build_hash = ""
        self.loaded_instance_hash = ""
        self.request_count = 0


def _host_recycle_threshold_bytes(native_memory_limit_bytes: int) -> int:
    if native_memory_limit_bytes <= 0:
        return 0
    return max(
        _HOST_RECYCLE_MIN_PEAK_BYTES,
        int(native_memory_limit_bytes * _HOST_RECYCLE_LIMIT_FRACTION),
    )


def _should_recycle_host_after_response(
    *,
    task_count: int,
    peak_rss_bytes: int,
    native_memory_limit_bytes: int,
) -> bool:
    threshold = _host_recycle_threshold_bytes(native_memory_limit_bytes)
    return bool(
        int(task_count) >= _HOST_RECYCLE_MIN_TASK_COUNT
        and threshold > 0
        and int(peak_rss_bytes) >= threshold
    )


def _request_ipc_payload(
    request: BackendPricingRequest,
    *,
    include_data: bool,
) -> dict:
    """Return the versioned, pickle-safe host request schema.

    HiGHS exposes some dual maps as ``mappingproxy`` objects.  Passing the
    domain request directly through ``multiprocessing`` therefore depends on
    an implementation detail that is not pickleable.  Normalize every mutable
    request component here and reconstruct the typed request in the host.
    The immutable instance graph is sent only on ``load_solve``; subsequent
    same-instance calls carry a small delta.
    """

    payload = {
        field.name: getattr(request, field.name)
        for field in fields(BackendPricingRequest)
        if field.name
        not in {"data", "true_duals", "branch_context", "cut_context"}
    }
    payload.update(
        {
            "schema_version": NATIVE_HOST_PROTOCOL,
            "true_duals": {
                "cover": {
                    str(key): float(value)
                    for key, value in request.true_duals.cover.items()
                },
                "fleet_limit": float(request.true_duals.fleet_limit),
                "cuts": {
                    str(key): float(value)
                    for key, value in (request.true_duals.cuts or {}).items()
                },
            },
            "branch_context": request.branch_context.to_payload(),
            "cut_context": request.cut_context.to_payload(),
        }
    )
    if include_data:
        payload["data"] = request.data
    return payload


def _request_from_ipc_payload(
    payload: dict,
    *,
    base_request: BackendPricingRequest | None = None,
) -> BackendPricingRequest:
    if payload.get("schema_version") != NATIVE_HOST_PROTOCOL:
        raise RuntimeError("host request schema version mismatch")
    data = payload.get("data") if "data" in payload else None
    if data is None:
        if base_request is None:
            raise RuntimeError("host delta request has no loaded instance")
        data = base_request.data
    dual_payload = dict(payload.get("true_duals") or {})
    values = {
        field.name: payload[field.name]
        for field in fields(BackendPricingRequest)
        if field.name
        not in {"data", "true_duals", "branch_context", "cut_context"}
        and field.name in payload
    }
    values.update(
        {
            "data": data,
            "true_duals": JourneyDuals(
                cover=dict(dual_payload.get("cover") or {}),
                fleet_limit=float(dual_payload.get("fleet_limit", 0.0)),
                cuts=dict(dual_payload.get("cuts") or {}),
            ),
            "branch_context": branch_context_from_payload(
                payload.get("branch_context")
            ),
            "cut_context": cut_context_from_payload(payload.get("cut_context")),
        }
    )
    if base_request is not None:
        return replace(base_request, **values)
    return BackendPricingRequest(**values)


def _host_build_hash(
    backend_id: str = NATIVE_HOST_BACKEND_ID,
) -> str:
    from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_engine_build_hash

    return spprc_engine_build_hash(backend_id)


def _native_build_capability_blockers(
    request: BackendPricingRequest,
    native,
) -> tuple[str, ...]:
    if (
        request.dssr_policy_version
        != NG_DSSR_V3_POLICY_VERSION
    ):
        return tuple()
    build_info = dict(native.build_info())
    if str(build_info.get("ng_dssr_v3_compiled")) == "true":
        return tuple()
    return ("native_ng_dssr_v3_not_compiled",)


def _persistent_host_main(
    connection,
    backend_id: str = NATIVE_HOST_BACKEND_ID,
) -> None:
    build_hash = _host_build_hash(backend_id)
    base_request = None
    loaded_instance_hash = ""
    connection.send(
        {
            "protocol": NATIVE_HOST_PROTOCOL,
            "kind": "ready",
            "build_hash": build_hash,
            "pid": os.getpid(),
        }
    )
    while True:
        try:
            message = connection.recv()
        except EOFError:
            break
        if message.get("protocol") != NATIVE_HOST_PROTOCOL:
            break
        if message.get("kind") == "shutdown":
            break
        request_id = int(message.get("request_id") or 0)
        instance_hash = str(message.get("instance_hash") or "")
        response = {
            "protocol": NATIVE_HOST_PROTOCOL,
            "request_id": request_id,
            "build_hash": build_hash,
            "instance_hash": instance_hash,
        }
        try:
            if message.get("expected_build_hash") != build_hash:
                raise RuntimeError("host build hash is stale")
            if message.get("kind") == "load_solve":
                base_request = _request_from_ipc_payload(message["request"])
                loaded_instance_hash = instance_hash
            elif message.get("kind") == "solve_delta":
                if base_request is None or loaded_instance_hash != instance_hash:
                    raise RuntimeError("host delta request does not match loaded instance")
                base_request = _request_from_ipc_payload(
                    message["request"],
                    base_request=base_request,
                )
            else:
                raise RuntimeError(f"unsupported host request kind {message.get('kind')!r}")
            capability_blockers = _capability_blockers(base_request)
            if capability_blockers:
                result = _empty_result(
                    backend_id,
                    "UNSUPPORTED_FEATURE",
                    blockers=capability_blockers,
                )
            else:
                binding_blockers = _binding_blockers(base_request)
                if binding_blockers:
                    result = _empty_result(
                        backend_id,
                        "HASH_MISMATCH",
                        blockers=binding_blockers,
                    )
                else:
                    native = importlib.import_module("lunar_spprc_native")
                    build_blockers = (
                        _native_build_capability_blockers(
                            base_request,
                            native,
                        )
                    )
                    if build_blockers:
                        result = _empty_result(
                            backend_id,
                            "UNSUPPORTED_FEATURE",
                            blockers=build_blockers,
                        )
                    else:
                        raw = dict(
                            native.solve(
                                _native_request_payload(base_request)
                            )
                        )
                        result = _audit_native_result(
                            base_request,
                            raw,
                            backend_id=backend_id,
                        )
            response.update({"kind": "ok", "result": result})
        except BaseException as exc:  # pragma: no cover - protects the parent process
            response.update({"kind": "error", "error": repr(exc)})
        connection.send(response)
    connection.close()


atexit.register(NativeRcsppHostBackend.close)
atexit.register(NativeDssrHostBackend.close)
atexit.register(NativeDssrV2HostBackend.close)
atexit.register(NativeNgDssrV3HostBackend.close)


def _maybe_attach_environment_guidance(
    request: BackendPricingRequest,
) -> BackendPricingRequest:
    """Run the optional task/arc predictor before Native imports/IPC."""

    if request.exact_proof_mode:
        manifest_path = str(
            os.getenv("LUNAR_ICE_PROOF_QUEUE_GAT_MANIFEST", "")
        ).strip()
        if not manifest_path:
            return request
        try:
            from lunar_ice_bpc.guidance.proof_queue_gat_runtime import (
                prepare_proof_queue_gat_request_from_environment,
            )

            prepared, _diagnostics = (
                prepare_proof_queue_gat_request_from_environment(
                    request
                )
            )
            return prepared
        except Exception as exc:
            # Proof guidance is optional ordering only.  Any runtime,
            # checkpoint, hash, OOD, or inference error restores the exact
            # request without changing its queue, bounds, or certificate.
            lifecycle = {
                "guidance_import_sec": 0.0,
                "guidance_checkpoint_load_sec": 0.0,
                "guidance_tensorize_sec": 0.0,
                "guidance_forward_total_sec": 0.0,
                "guidance_call_count": 0,
                "guidance_binding_validation_sec": 0.0,
                "guidance_native_install_sec": 0.0,
                "guidance_total_wall_sec": 0.0,
                "guidance_total_wall_ratio": None,
                "bypassed_before_import": True,
                "bypass_reason": (
                    "proof_queue_gat_fail_closed:" f"{exc!r}"
                ),
            }
            return replace(
                request,
                guidance_mode=GUIDANCE_MODE_OFF,
                guidance_hints=None,
                guidance_lifecycle_telemetry=tuple(
                    lifecycle.items()
                ),
            )
    if (
        request.guidance_mode != GUIDANCE_MODE_OFF
        or request.guidance_hints is not None
    ):
        return request
    oracle_path = str(
        os.getenv(DEVELOPMENT_ORACLE_TASK_PRIORITY_ENV, "")
    ).strip()
    if oracle_path:
        try:
            return _attach_development_oracle_task_priorities(
                request, oracle_path
            )
        except Exception as exc:
            lifecycle = {
                "guidance_import_sec": 0.0,
                "guidance_checkpoint_load_sec": 0.0,
                "guidance_tensorize_sec": 0.0,
                "guidance_forward_total_sec": 0.0,
                "guidance_call_count": 0,
                "guidance_binding_validation_sec": 0.0,
                "guidance_native_install_sec": 0.0,
                "guidance_total_wall_sec": 0.0,
                "guidance_total_wall_ratio": None,
                "bypassed_before_import": True,
                "bypass_reason": (
                    "development_oracle_task_priority_rejected:"
                    f"{exc!r}"
                ),
            }
            return replace(
                request,
                guidance_mode=GUIDANCE_MODE_OFF,
                guidance_hints=None,
                guidance_lifecycle_telemetry=tuple(
                    lifecycle.items()
                ),
            )
    try:
        from lunar_ice_bpc.guidance.runtime import (
            prepare_guidance_request_from_environment,
        )

        prepared = prepare_guidance_request_from_environment(
            request,
            stage="task_arc",
        )
    except Exception as exc:
        lifecycle = {
            "guidance_import_sec": 0.0,
            "guidance_checkpoint_load_sec": 0.0,
            "guidance_tensorize_sec": 0.0,
            "guidance_forward_total_sec": 0.0,
            "guidance_call_count": 0,
            "guidance_binding_validation_sec": 0.0,
            "guidance_native_install_sec": 0.0,
            "guidance_total_wall_sec": 0.0,
            "guidance_total_wall_ratio": None,
            "bypassed_before_import": True,
            "bypass_reason": f"environment_guidance_hook_failed:{exc!r}",
        }
        return replace(
            request,
            guidance_mode="off",
            guidance_hints=None,
            guidance_lifecycle_telemetry=tuple(lifecycle.items()),
        )
    return request if prepared is None else prepared.request


def _attach_development_oracle_task_priorities(
    request: BackendPricingRequest,
    path: str,
) -> BackendPricingRequest:
    """Bind one development-only static task-priority oracle to this request."""

    resolved = Path(path).resolve()
    stat = resolved.stat()
    cache_key = (str(resolved), int(stat.st_mtime_ns))
    payload = _DEVELOPMENT_ORACLE_PRIORITY_CACHE.get(cache_key)
    if payload is None:
        outer = json.loads(resolved.read_text(encoding="utf-8"))
        candidate = (
            outer.get("task_priority_oracle")
            or outer.get("prefix_priority_oracle")
        )
        if not isinstance(candidate, dict):
            candidate = outer
        payload = dict(candidate)
        _DEVELOPMENT_ORACLE_PRIORITY_CACHE.clear()
        _DEVELOPMENT_ORACLE_PRIORITY_CACHE[cache_key] = payload
    schema = str(payload.get("schema_version") or "")
    supported_schemas = {
        "lunar_ice_bpc.development_trajectory_task_priority_oracle.v1",
        "lunar_ice_bpc.development_native_prefix_priority_oracle.v1",
    }
    if schema not in supported_schemas:
        raise ValueError("development task-priority schema mismatch")
    if str(payload.get("source_partition") or "") != "development":
        raise ValueError("development task-priority partition mismatch")
    if bool(payload.get("deployable")):
        raise ValueError("development task-priority cannot be deployable")
    if str(payload.get("instance_content_hash") or "") != (
        request.data.instance_content_hash
    ):
        raise ValueError("development task-priority instance mismatch")
    selected_context: dict[str, Any] = {}
    if schema == (
        "lunar_ice_bpc.development_native_prefix_priority_oracle.v1"
    ):
        selected_context = _select_development_prefix_context(
            request, payload
        )
    raw_task_priorities = (
        selected_context.get("task_priorities")
        if selected_context
        else payload.get("task_priorities")
    )
    raw_arc_priorities = (
        selected_context.get("arc_priorities")
        if selected_context
        else payload.get("arc_priorities")
    ) or {}
    if not isinstance(raw_task_priorities, dict) or not isinstance(
        raw_arc_priorities, dict
    ):
        raise ValueError("development task/arc priorities must be mappings")
    task_priorities = {
        str(task_id): float(value)
        for task_id, value in raw_task_priorities.items()
    }
    expected_tasks = set(request.data.task_ids)
    if not set(task_priorities).issubset(expected_tasks):
        raise ValueError("development task-priority universe mismatch")
    task_priorities = {
        task_id: float(task_priorities.get(task_id, 0.0))
        for task_id in request.data.task_ids
    }
    if any(not isfinite(value) for value in task_priorities.values()):
        raise ValueError("development task priority contains NaN/Inf")
    arc_priorities = {
        str(arc_id): float(value)
        for arc_id, value in raw_arc_priorities.items()
    }
    expected_arcs = {
        canonical_arc_candidate_id(source, target, path_type)
        for (source, target), by_type in request.data.arcs.items()
        for path_type in by_type
    }
    if not set(arc_priorities).issubset(expected_arcs):
        raise ValueError("development arc-priority universe mismatch")
    if any(not isfinite(value) for value in arc_priorities.values()):
        raise ValueError("development arc priority contains NaN/Inf")
    enriched = replace(
        request,
        guidance_mode=GUIDANCE_MODE_TASK_ARC,
        guidance_feature_schema_version=(
            "development_trajectory_task_priority.v1"
        ),
        guidance_normalization_version=(
            "development_oracle_centered_maxabs.v1"
        ),
        guidance_checkpoint_id=str(
            payload.get("source_artifact_sha256") or ""
        ),
        guidance_ood_policy_version="development_exact_hash_only.v1",
        guidance_lifecycle_telemetry=tuple(
            {
                "guidance_import_sec": 0.0,
                "guidance_checkpoint_load_sec": 0.0,
                "guidance_tensorize_sec": 0.0,
                "guidance_forward_total_sec": 0.0,
                "guidance_call_count": 0,
                "guidance_binding_validation_sec": 0.0,
                "guidance_native_install_sec": 0.0,
                "guidance_total_wall_sec": 0.0,
                "guidance_total_wall_ratio": None,
                "bypassed_before_import": False,
                "bypass_reason": "",
                "development_oracle_task_priority": True,
                "development_oracle_schema": schema,
                "development_oracle_selected_context": str(
                    selected_context.get("rmp_iteration_id") or ""
                ),
            }.items()
        ),
    )
    binding = CanonicalSolveBindingV2.from_backend_request(enriched)
    hints = PricingOrderingHintsV2(
        binding_hash=binding.binding_hash,
        task_priorities=tuple(sorted(task_priorities.items())),
        arc_priorities=tuple(sorted(arc_priorities.items())),
        source="development_trajectory_task_priority_oracle",
        diagnostic_only=True,
    )
    return replace(enriched, guidance_hints=hints)


def _select_development_prefix_context(
    request: BackendPricingRequest,
    payload: dict[str, Any],
) -> dict[str, Any]:
    contexts = payload.get("contexts")
    if not isinstance(contexts, list) or not contexts:
        raise ValueError("development prefix contexts are missing")
    current_hash = true_dual_binding_hash(
        request.true_duals.cover,
        fleet_limit=request.true_duals.fleet_limit,
        cuts=request.true_duals.cuts,
    )
    for context in contexts:
        if (
            isinstance(context, dict)
            and str(context.get("mathematical_dual_hash") or "")
            == current_hash
        ):
            return dict(context)
    if str(payload.get("context_selection") or "") == (
        "exact_dual_hash_only"
    ):
        raise ValueError(
            "development prefix oracle has no exact dual-hash context"
        )
    task_ids = tuple(request.data.task_ids)

    def distance(context: object) -> tuple[float, int]:
        if not isinstance(context, dict):
            return float("inf"), 2**31 - 1
        cover = context.get("task_duals")
        if not isinstance(cover, dict) or set(cover) != set(task_ids):
            return float("inf"), int(
                context.get("round_index") or 2**31 - 1
            )
        scale = max(
            1.0e-6,
            max(
                abs(float(value))
                for value in (
                    *cover.values(),
                    *request.true_duals.cover.values(),
                )
            ),
        )
        squared = sum(
            (
                (
                    float(request.true_duals.cover[task_id])
                    - float(cover[task_id])
                )
                / scale
            )
            ** 2
            for task_id in task_ids
        )
        return squared / max(1, len(task_ids)), int(
            context.get("round_index") or 2**31 - 1
        )

    selected = min(contexts, key=distance)
    if not isinstance(selected, dict) or not isfinite(
        distance(selected)[0]
    ):
        raise ValueError("no compatible development prefix context")
    return dict(selected)


def _capability_blockers(request: BackendPricingRequest) -> tuple[str, ...]:
    blockers: list[str] = []
    if request.cut_state_required and not request.cut_state_enabled:
        blockers.append("native_required_cut_state_disabled")
    if request.cut_state_required and request.cut_state_schema_version != CUT_STATE_SCHEMA_VERSION:
        blockers.append("native_cut_state_schema_mismatch")
    blockers.extend(validate_live_sri_context(request.cut_context))
    active_ids = {cut.cut_id for cut in request.cut_context.cuts}
    for cut_id, raw_dual in (request.true_duals.cuts or {}).items():
        dual = float(raw_dual)
        if not isfinite(dual):
            blockers.append(f"native_nonfinite_cut_dual:{cut_id}")
        elif dual != 0.0 and str(cut_id) not in active_ids:
            blockers.append(f"native_nonzero_cut_dual_without_active_cut:{cut_id}")
    if len(request.cut_context.cuts) > MAX_NATIVE_ACTIVE_CUTS:
        blockers.append("native_active_cut_count_above_16")
    if len(request.data.task_ids) > 100:
        blockers.append("native_v1_task_count_above_100")
    return tuple(dict.fromkeys(blockers))


def _binding_blockers(request: BackendPricingRequest) -> tuple[str, ...]:
    from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_instance_hash

    blockers = []
    if request.instance_hash and request.instance_hash != spprc_instance_hash(request.data):
        blockers.append("native_instance_hash_mismatch")
    dual_payload = {
        "cover": sorted(
            (str(key), float(value)) for key, value in request.true_duals.cover.items()
        ),
        "fleet_limit": float(request.true_duals.fleet_limit),
        "cuts": sorted(
            (str(key), float(value))
            for key, value in (request.true_duals.cuts or {}).items()
        ),
    }
    expected_dual_hashes = {
        _stable_hash(dual_payload),
        true_dual_binding_hash(
            request.true_duals.cover,
            fleet_limit=request.true_duals.fleet_limit,
            cuts=request.true_duals.cuts,
        ),
    }
    if request.dual_binding_hash and request.dual_binding_hash not in expected_dual_hashes:
        blockers.append("native_dual_binding_hash_mismatch")
    branch_payload = request.branch_context.to_payload()
    expected_branch_hashes = {
        _stable_hash(branch_payload),
        stable_payload_hash(branch_payload),
    }
    if (
        request.branch_context_hash not in {"", "empty"}
        and request.branch_context_hash not in expected_branch_hashes
    ):
        blockers.append("native_branch_context_hash_mismatch")
    if request.cut_context_hash not in {"", "empty"} and request.cut_context_hash != _stable_hash(
        request.cut_context.to_payload()
    ) and request.cut_context_hash != request.cut_context.active_cut_context_hash:
        blockers.append("native_cut_context_hash_mismatch")
    return tuple(blockers)


def _stable_hash(payload) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _pricing_cut_context(request: BackendPricingRequest) -> CutContext:
    """Return the exact cut subset that can affect this pricing objective.

    The full RMP context remains on ``request.cut_context`` and is always bound
    into the certificate.  Projection removes only IEEE values equal to zero;
    no tolerance is permitted because an arbitrarily small nonzero dual still
    contributes to reduced cost.
    """

    return pricing_cut_context_from_duals(
        request.cut_context,
        request.true_duals.cuts,
        enabled=request.cut_dual_projection_enabled,
    )


def _native_request_payload(request: BackendPricingRequest) -> dict:
    data = request.data
    static = _native_static_payload(data)
    pricing_cut_context = _pricing_cut_context(request)
    install_started = monotonic()
    accepted_guidance, guidance_validation = validate_pricing_ordering_hints(
        request
    )
    canonical_binding = CanonicalSolveBindingV2.from_backend_request(request)
    guidance_effective = bool(
        accepted_guidance is not None
        and request.guidance_mode == GUIDANCE_MODE_TASK_ARC
        and (
            not request.exact_proof_mode
            or request.proof_queue_policy_id in {"QG1", "QG2", "QGR1"}
        )
    )
    label_state_effective = bool(
        guidance_effective
        and request.proof_queue_policy_id in {"QG2", "QGR1"}
        and accepted_guidance is not None
        and accepted_guidance.label_state_coefficients
    )
    task_priorities = (
        accepted_guidance.priorities_for("task")
        if guidance_effective
        else {}
    )
    arc_priorities = (
        accepted_guidance.priorities_for("arc")
        if guidance_effective
        else {}
    )
    tasks = [
        {
            **row,
            "dual": float(request.true_duals.cover.get(row["id"], 0.0)),
            "guidance_priority": float(task_priorities.get(row["id"], 0.0)),
        }
        for row in static["tasks"]
    ]
    arcs = [
        {
            **row,
            "guidance_priority": float(
                arc_priorities.get(
                    canonical_arc_candidate_id(
                        row["source"],
                        row["target"],
                        row["path_type"],
                    ),
                    0.0,
                )
            ),
        }
        for row in static["arcs"]
    ]
    task_universe_hash = canonical_universe_hash(
        (row["id"] for row in tasks),
        universe_kind="task",
    )
    arc_universe_hash = canonical_universe_hash(
        (
            canonical_arc_candidate_id(
                row["source"],
                row["target"],
                row["path_type"],
            )
            for row in arcs
        ),
        universe_kind="arc",
    )
    guidance_install_sec = monotonic() - install_started
    return {
        **static,
        "tasks": tasks,
        "arcs": arcs,
        "branch_decisions": [
            decision.to_payload() for decision in request.branch_context.pair_decisions
        ],
        "cuts": [
            {
                **cut.to_payload(),
                "dual": float((request.true_duals.cuts or {}).get(cut.cut_id, 0.0)),
            }
            for cut in pricing_cut_context.cuts
        ],
        "weight_cost": (
            0.0
            if request.objective_mode == BACKEND_OBJECTIVE_PHASE_ONE
            else data.objective.weight_operating_cost
        ),
        "weight_risk": (
            0.0
            if request.objective_mode == BACKEND_OBJECTIVE_PHASE_ONE
            else data.objective.weight_risk
        ),
        "weight_completion": (
            0.0
            if request.objective_mode == BACKEND_OBJECTIVE_PHASE_ONE
            else data.objective.weight_completion
        ),
        "fleet_dual": request.true_duals.fleet_limit,
        "mode": request.mode,
        "objective_mode": request.objective_mode,
        "harvest_target": request.harvest_target,
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
        "harvest_max_processed_labels": (
            request.harvest_max_processed_labels
        ),
        "wall_time_limit_sec": request.wall_time_limit_sec,
        "memory_limit_gb": request.memory_limit_gb,
        "negative_eps": request.negative_eps,
        "dominance_eps": request.dominance_eps,
        "resource_eps": request.resource_eps,
        "instance_hash": request.instance_hash or static["instance_hash"],
        "graph_cache_entries": max(
            0,
            int(os.getenv("LUNAR_ICE_SPPRC_GRAPH_CACHE_ENTRIES", "1")),
        ),
        "completion_bound_enabled": bool(
            request.completion_bound_enabled
            and request.cut_context.empty
            and not request.dssr_enabled
        ),
        # Preserve the candidate-column surface in negative-harvest calls.
        # Subset dominance is a proof accelerator: it preserves the optimum
        # and no-negative result, but can intentionally omit dominated
        # negative task-set variants.
        "subset_dominance_enabled": bool(
            request.subset_dominance_enabled
            and request.exact_proof_mode
            and not request.dssr_enabled
        ),
        "proof_queue_potential_trace_enabled": bool(
            request.exact_proof_mode
            and str(
                os.getenv(
                    "LUNAR_ICE_PROOF_QUEUE_POTENTIAL_TRACE",
                    "0",
                )
            ).strip().lower()
            in {"1", "true", "yes", "on"}
        ),
        "proof_queue_label_trace_enabled": bool(
            request.exact_proof_mode
            and request.proof_tail_label_trace_enabled
        ),
        "proof_queue_label_trace_max_rows": int(
            request.proof_tail_label_trace_max_rows
        ),
        "proof_queue_label_trace_sampling_mode": str(
            request.proof_tail_label_trace_sampling_mode
        ),
        "proof_queue_label_trace_seed": int(
            request.proof_tail_label_trace_seed
        ),
        "proof_queue_preference_cap_per_family": int(
            request.proof_tail_preference_cap_per_family
        ),
        "proof_queue_surface_reservoir_count": int(
            request.proof_tail_surface_reservoir_count
        ),
        "proof_queue_surface_labels_per_bucket": int(
            request.proof_tail_surface_labels_per_bucket
        ),
        "proof_queue_witness_route_cap": int(
            request.proof_tail_witness_route_cap
        ),
        "proof_queue_witness_ancestor_cap": int(
            request.proof_tail_witness_ancestor_cap
        ),
        "proof_queue_guidance_bucket_width": float(
            request.proof_queue_guidance_bucket_width
        ),
        "proof_queue_policy_id": request.proof_queue_policy_id,
        "proof_queue_frontier_probe_mode": str(
            request.proof_tail_frontier_probe_mode
        ),
        "proof_queue_frontier_probe_boundary": int(
            request.proof_tail_frontier_probe_boundary
        ),
        "proof_queue_frontier_trial_pop_budget": int(
            request.proof_tail_frontier_trial_pop_budget
        ),
        "proof_queue_frontier_problem_scale": int(request.data.scale),
        "proof_queue_frontier_pricing_lifecycle": str(
            request.pricing_lifecycle_scope
        ),
        "proof_queue_frontier_require_root_cg": bool(
            request.proof_tail_frontier_require_root_cg
        ),
        "proof_queue_frontier_fail_closed_on_ood": bool(
            request.proof_tail_frontier_fail_closed_on_ood
        ),
        "proof_queue_frontier_observation_boundaries": list(
            request.proof_tail_frontier_observation_boundaries
        ),
        "proof_queue_frontier_context_features": list(
            request.proof_tail_frontier_context_features
        ),
        "proof_queue_frontier_gat_bundle": (
            None
            if request.proof_tail_frontier_gat_bundle is None
            else dict(request.proof_tail_frontier_gat_bundle)
        ),
        "proof_queue_frontier_manifest_sha256": str(
            request.proof_tail_frontier_manifest_sha256
        ),
        "proof_queue_frontier_bundle_sha256": str(
            request.proof_tail_frontier_bundle_sha256
        ),
        "proof_queue_counterfactual_prefix_mode": str(
            request.proof_tail_counterfactual_prefix_mode
        ),
        "proof_queue_counterfactual_prefix_boundary": int(
            request.proof_tail_counterfactual_prefix_boundary
        ),
        "proof_queue_counterfactual_rollout_checkpoints": list(
            request.proof_tail_counterfactual_rollout_checkpoints
        ),
        "proof_queue_counterfactual_max_rollout_budget": int(
            request.proof_tail_counterfactual_max_rollout_budget
        ),
        "proof_queue_counterfactual_label_sample_cap": int(
            request.proof_tail_counterfactual_label_sample_cap
        ),
        "proof_queue_counterfactual_sampling_seed": int(
            request.proof_tail_counterfactual_sampling_seed
        ),
        "proof_queue_counterfactual_telemetry_only": bool(
            request.proof_tail_counterfactual_telemetry_only
        ),
        "proof_queue_counterfactual_public_routes_forbidden": bool(
            request.proof_tail_counterfactual_public_routes_forbidden
        ),
        "proof_queue_counterfactual_certificate_forbidden": bool(
            request.proof_tail_counterfactual_certificate_forbidden
        ),
        "dssr_enabled": bool(request.dssr_enabled),
        "dssr_policy_version": str(request.dssr_policy_version),
        "dssr_negative_batch_target": int(
            request.dssr_negative_batch_target
        ),
        "dssr_pressure_refinement_enabled": bool(
            request.dssr_pressure_refinement_enabled
        ),
        "dssr_pressure_max_bucket_size": int(
            request.dssr_pressure_max_bucket_size
        ),
        "dssr_pressure_max_candidate_checks": int(
            request.dssr_pressure_max_candidate_checks
        ),
        "ng_dssr_initial_neighborhood_size": int(
            request.ng_dssr_initial_neighborhood_size
        ),
        "config_hash": request.config_hash,
        "engine_hash": request.engine_hash,
        "service_timing_policy_id": SERVICE_TIMING_POLICY_ID,
        "canonical_solve_binding_v2": canonical_binding.to_payload(),
        "canonical_solve_binding_v2_schema": canonical_binding.schema_version,
        "canonical_solve_binding_v2_hash": canonical_binding.binding_hash,
        "dual_binding_hash": request.dual_binding_hash,
        "branch_context_hash": request.branch_context_hash,
        "cut_state_schema_version": request.cut_state_schema_version,
        "active_cut_context_hash": request.cut_context.active_cut_context_hash,
        "active_cut_count": len(request.cut_context.cuts),
        "pricing_cut_context_hash": pricing_cut_context.active_cut_context_hash,
        "pricing_cut_count": len(pricing_cut_context.cuts),
        "cut_dual_projection_enabled": bool(request.cut_dual_projection_enabled),
        "cut_dual_projection_schema_version": CUT_DUAL_PROJECTION_SCHEMA_VERSION,
        "cut_lineage_hash": request.cut_lineage_hash,
        "live_cut_policy_hash": request.live_cut_policy_hash,
        "rmp_iteration_id": request.rmp_iteration_id,
        "separator_policy_version": request.separator_policy_version,
        "guidance_mode": request.guidance_mode,
        "guidance_effective_mode": (
            GUIDANCE_MODE_TASK_ARC if guidance_effective else "off"
        ),
        "guidance_binding_hash": (
            ""
            if accepted_guidance is None
            else accepted_guidance.binding_hash
        ),
        "guidance_task_arc_enabled": guidance_effective,
        "guidance_label_state_enabled": label_state_effective,
        "guidance_label_state_coefficients": (
            list(accepted_guidance.label_state_coefficients)
            if label_state_effective and accepted_guidance is not None
            else [0.0] * 15
        ),
        "guidance_label_state_schema_version": (
            accepted_guidance.label_state_schema_version
            if label_state_effective and accepted_guidance is not None
            else ""
        ),
        "legal_task_universe_hash_before_sort": task_universe_hash,
        "legal_arc_universe_hash_before_sort": arc_universe_hash,
        "guidance_native_install_sec": guidance_install_sec,
        "guidance_validation_issues": guidance_validation[
            "guidance_validation_issues"
        ],
    }


def _native_static_payload(data) -> dict:
    from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_instance_hash

    cache_key = (
        f"{spprc_instance_hash(data)}:{SERVICE_TIMING_POLICY_ID}"
    )
    with _STATIC_PAYLOAD_CACHE_LOCK:
        cached = _STATIC_PAYLOAD_CACHE.get(cache_key)
        if cached is not None:
            _STATIC_PAYLOAD_CACHE.move_to_end(cache_key)
            return cached
    refs = objective_references(data)
    task_index = {task_id: index for index, task_id in enumerate(data.task_ids)}
    tasks = []
    for task_id in data.task_ids:
        task = data.tasks[task_id]
        tasks.append(
            {
                "id": task_id,
                "index": task_index[task_id],
                "science_weight": task.science_weight,
                "demand": task.demand,
                "service_time": task.service_time,
                "service_energy": task.service_energy,
                "service_cost": task.service_cost,
                "ready_time": task.ready_time,
                "due_time": task.due_time,
                "local_shadow_score": task.local_shadow_score,
                "local_thermal_risk": task.local_thermal_risk,
            }
        )
    arcs = []
    for (source, target), by_type in sorted(data.arcs.items()):
        for path_type in PATH_TYPES:
            option = by_type[path_type]
            arcs.append(
                {
                    "source": source,
                    "target": target,
                    "path_type": path_type,
                    "travel_time": option.travel_time_min,
                    "energy": option.energy_proxy,
                    "risk": option.risk_integral,
                    "distance": option.distance_km,
                    "shadow": option.shadow_exposure_min,
                }
            )
    value = {
        "instance_id": data.instance_id,
        "instance_hash": spprc_instance_hash(data),
        "service_timing_policy_id": SERVICE_TIMING_POLICY_ID,
        "tasks": tasks,
        "arcs": arcs,
        "max_tasks_per_trip": data.max_tasks_per_trip,
        "capacity": data.capacity,
        "energy_limit": data.energy_limit,
        "horizon": data.horizon,
        "dock_overhead": data.dock_overhead_min,
        "recharge_power": data.recharge_power_proxy_per_min,
        "shadow_limit": data.max_shadow_exposure_per_sortie,
        "reference_cost": refs.reference_cost,
        "reference_risk": refs.reference_risk,
        "reference_completion": refs.reference_completion,
    }
    with _STATIC_PAYLOAD_CACHE_LOCK:
        _STATIC_PAYLOAD_CACHE[cache_key] = value
        _STATIC_PAYLOAD_CACHE.move_to_end(cache_key)
        while len(_STATIC_PAYLOAD_CACHE) > _STATIC_PAYLOAD_CACHE_MAX_ENTRIES:
            _STATIC_PAYLOAD_CACHE.popitem(last=False)
    return value


def _audit_native_result(
    request: BackendPricingRequest,
    raw: dict[str, Any],
    *,
    backend_id: str,
) -> BackendResult:
    audit_started = monotonic()
    blockers = [str(item) for item in raw.get("certificate_blockers", [])]
    raw_bindings = dict(raw.get("request_bindings") or {})
    pricing_cut_context = _pricing_cut_context(request)
    accepted_guidance, guidance_validation = validate_pricing_ordering_hints(
        request
    )
    canonical_binding = CanonicalSolveBindingV2.from_backend_request(request)
    guidance_effective = bool(
        accepted_guidance is not None
        and request.guidance_mode == GUIDANCE_MODE_TASK_ARC
        and (
            not request.exact_proof_mode
            or request.proof_queue_policy_id in {"QG1", "QG2", "QGR1"}
        )
    )
    label_state_effective = bool(
        guidance_effective
        and request.proof_queue_policy_id in {"QG2", "QGR1"}
        and accepted_guidance is not None
        and accepted_guidance.label_state_coefficients
    )
    legal_task_universe_hash = canonical_universe_hash(
        request.data.task_ids,
        universe_kind="task",
    )
    legal_arc_universe_hash = canonical_universe_hash(
        (
            canonical_arc_candidate_id(source, target, path_type)
            for (source, target), by_type in sorted(request.data.arcs.items())
            for path_type in sorted(by_type)
        ),
        universe_kind="arc",
    )
    expected_bindings = {
        "instance_hash": request.instance_hash or _native_static_payload(request.data)["instance_hash"],
        "config_hash": request.config_hash,
        "engine_hash": request.engine_hash,
        "service_timing_policy_id": SERVICE_TIMING_POLICY_ID,
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
        "canonical_solve_binding_v2": canonical_binding.to_payload(),
        "canonical_solve_binding_v2_schema": canonical_binding.schema_version,
        "canonical_solve_binding_v2_hash": canonical_binding.binding_hash,
        "dual_binding_hash": request.dual_binding_hash,
        "branch_context_hash": request.branch_context_hash,
        "objective_mode": request.objective_mode,
        "rmp_iteration_id": request.rmp_iteration_id,
        "active_cut_context_hash": request.cut_context.active_cut_context_hash,
        "active_cut_count": len(request.cut_context.cuts),
        "pricing_cut_context_hash": pricing_cut_context.active_cut_context_hash,
        "pricing_cut_count": len(pricing_cut_context.cuts),
        "cut_dual_projection_enabled": bool(request.cut_dual_projection_enabled),
        "cut_dual_projection_schema_version": CUT_DUAL_PROJECTION_SCHEMA_VERSION,
        "cut_lineage_hash": request.cut_lineage_hash,
        "live_cut_policy_hash": request.live_cut_policy_hash,
        "cut_state_schema_version": request.cut_state_schema_version,
        "separator_policy_version": request.separator_policy_version,
        "negative_eps": request.negative_eps,
        "guidance_mode": request.guidance_mode,
        "guidance_effective_mode": (
            GUIDANCE_MODE_TASK_ARC if guidance_effective else "off"
        ),
        "guidance_binding_hash": (
            ""
            if accepted_guidance is None
            else accepted_guidance.binding_hash
        ),
        "guidance_task_arc_enabled": guidance_effective,
        "proof_queue_frontier_probe_mode": str(
            request.proof_tail_frontier_probe_mode
        ),
        "proof_queue_frontier_probe_boundary": int(
            request.proof_tail_frontier_probe_boundary
        ),
        "proof_queue_frontier_trial_pop_budget": int(
            request.proof_tail_frontier_trial_pop_budget
        ),
        "proof_queue_frontier_problem_scale": int(request.data.scale),
        "proof_queue_frontier_pricing_lifecycle": str(
            request.pricing_lifecycle_scope
        ),
        "proof_queue_frontier_require_root_cg": bool(
            request.proof_tail_frontier_require_root_cg
        ),
        "proof_queue_frontier_fail_closed_on_ood": bool(
            request.proof_tail_frontier_fail_closed_on_ood
        ),
        "proof_queue_frontier_observation_boundaries": list(
            request.proof_tail_frontier_observation_boundaries
        ),
        "proof_queue_frontier_manifest_sha256": str(
            request.proof_tail_frontier_manifest_sha256
        ),
        "proof_queue_frontier_bundle_sha256": str(
            request.proof_tail_frontier_bundle_sha256
        ),
        "proof_queue_counterfactual_prefix_mode": str(
            request.proof_tail_counterfactual_prefix_mode
        ),
        "proof_queue_counterfactual_prefix_boundary": int(
            request.proof_tail_counterfactual_prefix_boundary
        ),
        "proof_queue_counterfactual_rollout_checkpoints": list(
            request.proof_tail_counterfactual_rollout_checkpoints
        ),
        "proof_queue_counterfactual_label_sample_cap": int(
            request.proof_tail_counterfactual_label_sample_cap
        ),
        "proof_queue_counterfactual_sampling_seed": int(
            request.proof_tail_counterfactual_sampling_seed
        ),
        "legal_task_universe_hash_before_sort": legal_task_universe_hash,
        "legal_arc_universe_hash_before_sort": legal_arc_universe_hash,
    }
    if request.proof_queue_policy_id in {"QG2", "QGR1"}:
        expected_bindings.update(
            {
                "guidance_label_state_enabled": label_state_effective,
                "guidance_label_state_schema_version": (
                    accepted_guidance.label_state_schema_version
                    if label_state_effective
                    and accepted_guidance is not None
                    else ""
                ),
            }
        )
    if request.dssr_enabled:
        expected_bindings.update(
            {
                "dssr_enabled": True,
                "dssr_policy_version": request.dssr_policy_version,
                "dssr_negative_batch_target": (
                    request.dssr_negative_batch_target
                ),
                "dssr_pressure_refinement_enabled": (
                    request.dssr_pressure_refinement_enabled
                ),
                "dssr_pressure_max_bucket_size": (
                    request.dssr_pressure_max_bucket_size
                ),
                "dssr_pressure_max_candidate_checks": (
                    request.dssr_pressure_max_candidate_checks
                ),
                "ng_dssr_initial_neighborhood_size": (
                    request.ng_dssr_initial_neighborhood_size
                ),
            }
        )
    binding_mismatches = []
    for key, expected in expected_bindings.items():
        if key not in raw_bindings or raw_bindings.get(key) != expected:
            binding_mismatches.append(key)
            blockers.append(f"native_result_binding_mismatch:{key}")
    build_info = dict(raw.get("build_info") or {})
    if (
        request.cut_state_required
        and build_info.get("cut_state_schema") != _NATIVE_CUT_STATE_BUILD_SCHEMA
    ):
        blockers.append("native_engine_cut_state_schema_mismatch")
    native_engine_build_hash = _stable_hash(build_info) if build_info else ""
    if not native_engine_build_hash:
        blockers.append("native_engine_build_hash_missing")
    raw_telemetry = dict(raw.get("telemetry") or {})
    if request.dssr_enabled:
        if request.dssr_policy_version == DSSR_V2_POLICY_VERSION:
            build_policy = build_info.get("dssr_v2_policy")
        elif request.dssr_policy_version == NG_DSSR_V3_POLICY_VERSION:
            build_policy = build_info.get("ng_dssr_v3_policy")
        else:
            build_policy = build_info.get("large_scale_exact_pricer")
        if build_policy != request.dssr_policy_version:
            blockers.append("native_dssr_engine_policy_mismatch")
        if not bool(raw_telemetry.get("dssr_enabled")):
            blockers.append("native_dssr_telemetry_disabled")
        if (
            str(raw_telemetry.get("dssr_policy_version") or "")
            != request.dssr_policy_version
        ):
            blockers.append("native_dssr_telemetry_policy_mismatch")
        if int(
            raw_telemetry.get("completion_bound_evaluated_labels") or 0
        ) != 0:
            blockers.append("native_dssr_completion_bound_was_active")
        if int(
            raw_telemetry.get("subset_dominance_candidate_checks") or 0
        ) != 0:
            blockers.append("native_dssr_subset_dominance_was_active")
        if (
            request.dssr_policy_version == NG_DSSR_V3_POLICY_VERSION
            and not bool(raw_telemetry.get("ng_dssr_enabled"))
        ):
            blockers.append("native_ng_dssr_telemetry_disabled")
    columns = []
    audited_rcs = []
    reconstruction_rows = []
    first_audited_true_negative_wall_time_seconds = None
    collect_native_training_routes = str(
        os.getenv(
            "LUNAR_ICE_DUAL_CENTER_TRAJECTORY_COLLECTION",
            "0",
        )
    ).strip().lower() in {"1", "true", "yes", "on"}
    for route_index, route in enumerate(raw.get("routes", []) or []):
        try:
            if request.dssr_enabled:
                raw_task_ids = [
                    str(task_id)
                    for sortie in route.get("sorties", [])
                    for task_id in sortie.get("tasks", [])
                ]
                if len(raw_task_ids) != len(set(raw_task_ids)):
                    blockers.append(
                        "native_dssr_non_elementary_route_leaked"
                    )
                    reconstruction_rows.append(
                        {
                            "accepted": False,
                            "error": (
                                "DSSR returned a non-elementary route "
                                "to the public audit"
                            ),
                        }
                    )
                    continue
            column = _reconstruct_column(request, route)
            manual_rc = float(_manual_backend_reduced_cost(column, request))
            native_rc = float(route["reduced_cost"])
            rc_delta = abs(native_rc - manual_rc)
            signature = column_signature_from_journey(column)
            signature_hash = column_semantic_signature_hash(signature)
            cover_contribution = sum(
                float(request.true_duals.cover.get(str(task_id), 0.0))
                for task_id in column.task_set
            )
            cut_coefficients = request.cut_context.coefficients_for(column)
            cut_contribution = sum(
                float((request.true_duals.cuts or {}).get(str(cut_id), 0.0))
                * float(coefficient)
                for cut_id, coefficient in cut_coefficients.items()
            )
            audit_row = {
                "native_route_index": int(route_index),
                "column_signature": signature_hash,
                "task_set": sorted(str(task_id) for task_id in column.task_set),
                "native_rc": native_rc,
                "python_manual_rc": manual_rc,
                "rmp_real_objective_contribution": (
                    0.0
                    if request.objective_mode == BACKEND_OBJECTIVE_PHASE_ONE
                    else float(column.objective)
                ),
                "rmp_cover_dual_contribution": cover_contribution,
                "rmp_fleet_dual_contribution": float(request.true_duals.fleet_limit),
                "rmp_cut_dual_contribution": cut_contribution,
                "cut_coefficients": dict(sorted(cut_coefficients.items())),
                "absolute_delta": rc_delta,
            }
            if collect_native_training_routes:
                audit_row["native_route_sorties"] = [
                    {
                        "tasks": [
                            str(task_id)
                            for task_id in sortie.get("tasks", [])
                        ],
                        "path_types": [
                            str(path_type)
                            for path_type in sortie.get(
                                "path_types", []
                            )
                        ],
                    }
                    for sortie in route.get("sorties", [])
                ]
            if rc_delta > request.reconstruction_eps:
                blockers.append("native_python_reduced_cost_mismatch")
                reconstruction_rows.append({**audit_row, "accepted": False})
                continue
            reconstruction_rows.append({**audit_row, "accepted": True})
            if manual_rc < -request.negative_eps:
                columns.append(column)
                audited_rcs.append(manual_rc)
                if first_audited_true_negative_wall_time_seconds is None:
                    native_wall = float(
                        (raw.get("telemetry") or {}).get(
                            "wall_time_seconds"
                        )
                        or 0.0
                    )
                    first_audited_true_negative_wall_time_seconds = (
                        native_wall + monotonic() - audit_started
                    )
        except Exception as exc:
            blockers.append("native_route_reconstruction_failed")
            reconstruction_rows.append({"accepted": False, "error": repr(exc)})

    engine_status = str(raw.get("status") or "UNKNOWN").upper()
    exhaustive = bool(raw.get("search_exhaustive")) and engine_status == "COMPLETE"
    frontier_empty = bool(raw.get("frontier_empty")) and exhaustive
    labels_dropped = bool(raw.get("labels_dropped"))
    if labels_dropped:
        blockers.append("native_labels_dropped")
    if request.exact_proof_mode and not exhaustive:
        blockers.append("native_exact_search_incomplete")
    if (
        request.exact_proof_mode
        and bool(raw_telemetry.get("negative_escape_triggered"))
    ):
        blockers.append("native_exact_negative_escape_partial")
    if request.exact_proof_mode and not frontier_empty:
        blockers.append("native_frontier_not_empty")
    if request.dssr_enabled:
        if raw.get("routes") and not bool(
            raw_telemetry.get("dssr_elementary_witness_returned")
        ):
            blockers.append("native_dssr_elementary_witness_flag_missing")
        if (
            exhaustive
            and not raw.get("routes")
            and not bool(
                raw_telemetry.get(
                    "dssr_relaxation_no_negative_certificate"
                )
            )
        ):
            blockers.append("native_dssr_relaxation_certificate_missing")

    if not request.exact_proof_mode and columns:
        best_by_task_set = {}
        for column, manual_rc in zip(columns, audited_rcs):
            key = frozenset(column.task_set)
            current = best_by_task_set.get(key)
            if current is None or manual_rc < current[0]:
                best_by_task_set[key] = (manual_rc, column)
        selected = sorted(best_by_task_set.values(), key=lambda row: row[0])[
            : request.harvest_target
        ]
        audited_rcs = [row[0] for row in selected]
        columns = [row[1] for row in selected]

    best_found = min(audited_rcs) if audited_rcs else None
    # Exhausting the native frontier is not sufficient to claim an exact
    # global value when any returned route failed reconstruction/RC audit (or
    # the engine supplied another certificate blocker).  The accepted
    # negatives remain useful as best-found columns, but the global-min field
    # must fail closed independently of the certificate gate.
    global_min = (
        best_found
        if exhaustive and best_found is not None and not blockers
        else None
    )
    proved_threshold = (
        -request.negative_eps
        if exhaustive and frontier_empty and not audited_rcs and not blockers
        else None
    )
    telemetry = raw_telemetry
    native_event_audit = _validate_native_best_rc_events(
        telemetry.get("best_reduced_cost_events"),
        exact_proof_mode=request.exact_proof_mode,
        wall_time_seconds=float(
            telemetry.get("wall_time_seconds") or 0.0
        ),
        raw_route_reduced_costs=tuple(
            float(row["native_rc"])
            for row in reconstruction_rows
            if bool(row.get("accepted"))
            and _is_finite_number(row.get("native_rc"))
        ),
        trace_truncated=bool(
            telemetry.get("best_reduced_cost_events_truncated")
        ),
    )
    if blockers and native_event_audit[
        "best_reduced_cost_event_trace_usable_for_training"
    ]:
        native_event_audit.update(
            {
                "best_reduced_cost_event_trace_usable_for_training": False,
                "best_reduced_cost_event_trace_error": (
                    "native_result_audit_has_blockers"
                ),
            }
        )
    telemetry.update(native_event_audit)
    lifecycle = dict(request.guidance_lifecycle_telemetry)
    telemetry.update(
        {
            **lifecycle,
            "native_raw_best_found_rc": raw.get("best_found_rc"),
            "native_build_info": raw.get("build_info") or {},
            "reconstruction_audit": reconstruction_rows,
            "rc_mismatch_count": sum(
                not bool(row.get("accepted")) for row in reconstruction_rows
            ),
            "max_abs_rc_delta": max(
                (float(row.get("absolute_delta") or 0.0) for row in reconstruction_rows),
                default=0.0,
            ),
            "cut_state_required": request.cut_state_required,
            "full_cut_context_active": not request.cut_context.empty,
            "pricing_cut_state_required": not pricing_cut_context.empty,
            "cut_state_effective": not pricing_cut_context.empty,
            "cut_state_schema_version": request.cut_state_schema_version,
            "active_cut_count": len(request.cut_context.cuts),
            "active_cut_context_hash": request.cut_context.active_cut_context_hash,
            "pricing_cut_count": len(pricing_cut_context.cuts),
            "pricing_cut_context_hash": pricing_cut_context.active_cut_context_hash,
            "proof_queue_policy_id": request.proof_queue_policy_id,
            "projected_zero_dual_cut_count": (
                len(request.cut_context.cuts) - len(pricing_cut_context.cuts)
            ),
            "cut_dual_projection_enabled": bool(request.cut_dual_projection_enabled),
            "cut_dual_projection_schema_version": CUT_DUAL_PROJECTION_SCHEMA_VERSION,
            "cut_lineage_hash": request.cut_lineage_hash,
            "true_dual_binding_hash": request.dual_binding_hash,
            "objective_mode": request.objective_mode,
            "rmp_iteration_id": request.rmp_iteration_id,
            "completion_bound_requested": request.completion_bound_enabled,
            "dssr_enabled": bool(request.dssr_enabled),
            "dssr_policy_version": request.dssr_policy_version,
            "dssr_negative_batch_target": (
                request.dssr_negative_batch_target
            ),
            "dssr_pressure_refinement_enabled": (
                request.dssr_pressure_refinement_enabled
            ),
            "dssr_pressure_max_bucket_size": (
                request.dssr_pressure_max_bucket_size
            ),
            "dssr_pressure_max_candidate_checks": (
                request.dssr_pressure_max_candidate_checks
            ),
            "ng_dssr_initial_neighborhood_size": (
                request.ng_dssr_initial_neighborhood_size
            ),
            "harvest_max_processed_labels": (
                request.harvest_max_processed_labels
            ),
            "completion_bound_effective": bool(
                request.completion_bound_enabled
                and request.cut_context.empty
                and not request.dssr_enabled
            ),
            "completion_bound_forced_off": bool(
                request.completion_bound_enabled
                and (
                    not request.cut_context.empty
                    or request.dssr_enabled
                )
            ),
            "completion_bound_forced_off_reason": (
                "dssr_relaxation"
                if request.completion_bound_enabled and request.dssr_enabled
                else "active_cut_context"
                if request.completion_bound_enabled
                and not request.cut_context.empty
                else ""
            ),
            "request_bindings": raw_bindings,
            "request_binding_mismatches": binding_mismatches,
            "request_bindings_match": not binding_mismatches,
            "native_engine_build_hash": native_engine_build_hash,
            "guidance_validation": guidance_validation,
            "guidance_mode": request.guidance_mode,
            "guidance_effective_mode": (
                GUIDANCE_MODE_TASK_ARC if guidance_effective else "off"
            ),
            "guidance_label_state_enabled": label_state_effective,
            "guidance_label_state_schema_version": (
                accepted_guidance.label_state_schema_version
                if label_state_effective and accepted_guidance is not None
                else ""
            ),
            "guidance_filter_count": 0,
            "guidance_arc_drop_count": 0,
            "guidance_label_drop_count": 0,
            "guidance_branch_pair_drop_count": 0,
            "legal_action_universe_hash_before_sort": legal_task_universe_hash,
            "legal_arc_universe_hash_before_sort": legal_arc_universe_hash,
            "guidance_binding_validation_sec": guidance_validation[
                "guidance_binding_validation_sec"
            ],
            "guidance_native_install_sec": float(
                raw_bindings.get("guidance_native_install_sec") or 0.0
            ),
            "first_audited_true_negative_wall_time_seconds": (
                first_audited_true_negative_wall_time_seconds
            ),
            "proof_completion_wall_time_seconds": (
                float(raw_telemetry.get("wall_time_seconds") or 0.0)
                if exhaustive and frontier_empty
                else None
            ),
        }
    )
    import_sec = float(telemetry.get("guidance_import_sec") or 0.0)
    load_sec = float(telemetry.get("guidance_checkpoint_load_sec") or 0.0)
    tensorize_sec = float(telemetry.get("guidance_tensorize_sec") or 0.0)
    forward_sec = float(telemetry.get("guidance_forward_total_sec") or 0.0)
    validation_sec = float(
        telemetry.get("guidance_binding_validation_sec") or 0.0
    )
    native_install_sec = float(
        telemetry.get("guidance_native_install_sec") or 0.0
    )
    guidance_total = (
        import_sec
        + load_sec
        + tensorize_sec
        + forward_sec
        + validation_sec
        + native_install_sec
    )
    telemetry["guidance_total_wall_sec"] = round(guidance_total, 9)
    baseline_wall = float(telemetry.get("wall_time_seconds") or 0.0)
    telemetry["guidance_total_wall_ratio"] = (
        None
        if baseline_wall <= 0.0
        else round(guidance_total / baseline_wall, 9)
    )
    result = BackendResult(
        backend_id=backend_id,
        engine_status=engine_status,
        best_found_rc=best_found,
        global_min_rc=global_min,
        global_min_rc_is_exact=bool(global_min is not None),
        proved_no_rc_below=proved_threshold,
        unexplored_rc_lower_bound=_optional_float(raw.get("unexplored_rc_lower_bound")),
        search_exhaustive=exhaustive,
        frontier_empty=frontier_empty,
        labels_dropped=labels_dropped,
        partial_columns_valid=bool(reconstruction_rows and all(row.get("accepted") for row in reconstruction_rows)),
        columns=tuple(columns),
        certificate_blockers=tuple(dict.fromkeys(blockers)),
        telemetry=telemetry,
    )
    return _maybe_record_guidance_snapshot(request, result)


def _validate_native_best_rc_events(
    raw_events: Any,
    *,
    exact_proof_mode: bool,
    wall_time_seconds: float,
    raw_route_reduced_costs: tuple[float, ...],
    trace_truncated: bool,
) -> dict[str, Any]:
    """Audit event-time telemetry without letting diagnostics affect proof.

    Only harvest calls emit discovery events.  A malformed trace is made
    unusable for training/replay, but never changes exact certificate fields.
    """

    schema = "lunar_spprc.best_reduced_cost_events.v1"
    if raw_events is None:
        return {
            "best_reduced_cost_event_schema": schema,
            "best_reduced_cost_event_trace_valid": False,
            "best_reduced_cost_event_trace_usable_for_training": False,
            "best_reduced_cost_event_trace_error": "trace_missing",
            "best_reduced_cost_event_count": 0,
            "best_reduced_cost_events_audited": [],
        }
    if not isinstance(raw_events, (list, tuple)):
        return {
            "best_reduced_cost_event_schema": schema,
            "best_reduced_cost_event_trace_valid": False,
            "best_reduced_cost_event_trace_usable_for_training": False,
            "best_reduced_cost_event_trace_error": "trace_not_a_sequence",
            "best_reduced_cost_event_count": 0,
            "best_reduced_cost_events_audited": [],
        }
    normalized: list[dict[str, Any]] = []
    previous_elapsed = -1.0
    previous_labels = -1
    previous_solutions = 0
    previous_best = float("inf")
    error = ""
    for index, value in enumerate(raw_events):
        try:
            row = dict(value)
            elapsed = float(row["elapsed_seconds"])
            extended_labels = int(row["extended_labels"])
            solution_count = int(row["solution_count"])
            discovered_rc = float(row["discovered_reduced_cost"])
            best_rc = float(row["best_reduced_cost"])
        except (KeyError, TypeError, ValueError, OverflowError):
            error = f"invalid_event:{index}"
            break
        if (
            not isfinite(elapsed)
            or elapsed < previous_elapsed
            or elapsed < 0.0
            or (
                wall_time_seconds > 0.0
                and elapsed > wall_time_seconds + 1.0e-6
            )
        ):
            error = f"invalid_elapsed:{index}"
            break
        if (
            extended_labels < previous_labels
            or solution_count <= previous_solutions
        ):
            error = f"nonmonotone_counters:{index}"
            break
        if (
            not isfinite(discovered_rc)
            or not isfinite(best_rc)
            or discovered_rc >= 0.0
            or best_rc >= previous_best - 1.0e-12
            or abs(discovered_rc - best_rc) > 1.0e-9
        ):
            error = f"invalid_best_rc:{index}"
            break
        normalized.append(
            {
                "event_index": index,
                "elapsed_sec": elapsed,
                "extended_labels": extended_labels,
                "solution_count": solution_count,
                "discovered_true_rc": discovered_rc,
                "best_true_rc": best_rc,
            }
        )
        previous_elapsed = elapsed
        previous_labels = extended_labels
        previous_solutions = solution_count
        previous_best = best_rc
    if not error and exact_proof_mode and normalized:
        error = "exact_proof_trace_must_be_empty"
    if (
        not error
        and normalized
        and raw_route_reduced_costs
        and not trace_truncated
        and abs(normalized[-1]["best_true_rc"] - min(raw_route_reduced_costs))
        > 1.0e-9
    ):
        error = "trace_final_best_mismatch"
    valid = not bool(error)
    return {
        "best_reduced_cost_event_schema": schema,
        "best_reduced_cost_event_trace_valid": valid,
        "best_reduced_cost_event_trace_usable_for_training": bool(
            valid and not exact_proof_mode and not trace_truncated
        ),
        "best_reduced_cost_event_trace_error": error,
        "best_reduced_cost_event_count": len(normalized),
        "best_reduced_cost_events_audited": normalized if valid else [],
    }


def _is_finite_number(value: Any) -> bool:
    try:
        return isfinite(float(value))
    except (TypeError, ValueError, OverflowError):
        return False


def _maybe_record_guidance_snapshot(
    request: BackendPricingRequest,
    result: BackendResult,
) -> BackendResult:
    """Persist an opt-in request-bound replay snapshot without changing solve state."""

    root_value = str(os.getenv("LUNAR_ICE_GAT_SNAPSHOT_DIR", "")).strip()
    if not root_value:
        return result
    try:
        maximum = max(
            0,
            int(os.getenv("LUNAR_ICE_GAT_SNAPSHOT_MAX_PER_PROCESS", "512")),
        )
        maximum_per_instance = max(
            0,
            int(os.getenv("LUNAR_ICE_GAT_SNAPSHOT_MAX_PER_INSTANCE", "8")),
        )
        global _SNAPSHOT_COUNT, _SNAPSHOT_COUNT_BY_INSTANCE
        instance_key = request.data.instance_content_hash
        with _SNAPSHOT_LOCK:
            if maximum <= 0 or _SNAPSHOT_COUNT >= maximum:
                telemetry = dict(result.telemetry)
                telemetry["guidance_snapshot_skipped"] = "per_process_cap"
                return replace(result, telemetry=telemetry)
            if (
                maximum_per_instance <= 0
                or _SNAPSHOT_COUNT_BY_INSTANCE.get(instance_key, 0)
                >= maximum_per_instance
            ):
                telemetry = dict(result.telemetry)
                telemetry["guidance_snapshot_skipped"] = "per_instance_cap"
                return replace(result, telemetry=telemetry)
            _SNAPSHOT_COUNT += 1
            _SNAPSHOT_COUNT_BY_INSTANCE[instance_key] = (
                _SNAPSHOT_COUNT_BY_INSTANCE.get(instance_key, 0) + 1
            )
        from lunar_ice_bpc.exact.bpc.guidance.replay import (
            build_pricing_snapshot,
            save_pricing_snapshot,
        )

        candidates = _guidance_snapshot_candidates(request)
        _attach_snapshot_training_observations(
            candidates,
            request=request,
            result=result,
        )
        snapshot = build_pricing_snapshot(
            request,
            candidates=candidates,
            result=result,
            queue_policy_id="Q0",
            engine_hash=request.engine_hash,
            feature_schema_version=request.guidance_feature_schema_version,
            normalization_version=request.guidance_normalization_version,
            checkpoint_id=request.guidance_checkpoint_id,
            ood_policy_version=request.guidance_ood_policy_version,
        )
        target = (
            Path(root_value)
            / request.data.instance_content_hash
            / f"{snapshot.snapshot_hash}.json"
        )
        save_pricing_snapshot(snapshot, target)
        telemetry = dict(result.telemetry)
        telemetry.update(
            {
                "guidance_snapshot_written": True,
                "guidance_snapshot_path": str(target.resolve()),
                "guidance_snapshot_hash": snapshot.snapshot_hash,
                "guidance_snapshot_candidate_count": len(candidates),
                "guidance_snapshot_can_certify": False,
            }
        )
        return replace(result, telemetry=telemetry)
    except Exception as exc:
        telemetry = dict(result.telemetry)
        telemetry.update(
            {
                "guidance_snapshot_written": False,
                "guidance_snapshot_error": repr(exc),
            }
        )
        return replace(result, telemetry=telemetry)


def _guidance_snapshot_candidates(
    request: BackendPricingRequest,
) -> list[dict]:
    candidates = [
        {
            "candidate_id": str(task_id),
            "candidate_kind": "task",
            "p0_position": index,
        }
        for index, task_id in enumerate(request.data.task_ids)
    ]
    arc_position_offset = len(candidates)
    candidates.extend(
        {
            "candidate_id": canonical_arc_candidate_id(
                source, target, path_type
            ),
            "candidate_kind": "arc",
            "p0_position": arc_position_offset + index,
        }
        for index, ((source, target), by_type, path_type) in enumerate(
            (
                ((source, target), by_type, path_type)
                for (source, target), by_type in sorted(
                    request.data.arcs.items()
                )
                for path_type in sorted(by_type)
            )
        )
    )
    return candidates


def _maybe_record_pre_solve_exact_snapshot(
    request: BackendPricingRequest,
) -> None:
    exact_root_value = str(
        os.getenv("LUNAR_ICE_PRE_SOLVE_EXACT_SNAPSHOT_DIR", "")
    ).strip()
    pricing_root_value = str(
        os.getenv("LUNAR_ICE_PRE_SOLVE_PRICING_SNAPSHOT_DIR", "")
    ).strip()
    roots = []
    if pricing_root_value:
        roots.append(pricing_root_value)
    if exact_root_value and request.exact_proof_mode:
        roots.append(exact_root_value)
    roots = list(dict.fromkeys(roots))
    if not roots:
        return
    try:
        from lunar_ice_bpc.exact.bpc.guidance.replay import (
            build_pricing_snapshot,
            save_pricing_snapshot,
        )

        snapshot = build_pricing_snapshot(
            request,
            candidates=_guidance_snapshot_candidates(request),
            result=None,
            queue_policy_id=request.proof_queue_policy_id,
            engine_hash=request.engine_hash,
            feature_schema_version=(
                request.guidance_feature_schema_version
            ),
            normalization_version=request.guidance_normalization_version,
            checkpoint_id=request.guidance_checkpoint_id,
            ood_policy_version=request.guidance_ood_policy_version,
        )
        for root_value in roots:
            target = (
                Path(root_value)
                / request.data.instance_content_hash
                / f"{snapshot.snapshot_hash}.json"
            )
            save_pricing_snapshot(snapshot, target)
    except Exception:
        # Snapshot collection is diagnostic-only and must never change exact
        # pricing control flow or certificate semantics.
        return


def _attach_snapshot_training_observations(
    candidates: list[dict],
    *,
    request: BackendPricingRequest,
    result: BackendResult,
) -> None:
    """Attach observed labels without treating unvisited work as negative."""

    from lunar_ice_bpc.exact.master.journey_rmp import (
        manual_journey_reduced_cost,
        manual_phase_one_journey_reduced_cost,
    )

    observations: dict[str, list[float]] = {}
    for column in result.columns:
        if request.objective_mode == BACKEND_OBJECTIVE_PHASE_ONE:
            true_rc = manual_phase_one_journey_reduced_cost(
                column, request.true_duals
            )
        else:
            true_rc = manual_journey_reduced_cost(
                column, request.true_duals
            )
        if float(true_rc) >= -abs(float(request.negative_eps)):
            continue
        candidate_ids = set(str(value) for value in column.task_set)
        candidate_ids.update(
            canonical_arc_candidate_id(
                leg.source, leg.target, leg.path_type
            )
            for sortie in column.sorties
            for leg in sortie.legs
        )
        for candidate_id in candidate_ids:
            observations.setdefault(candidate_id, []).append(float(true_rc))
    exhaustive_no_negative = bool(
        result.search_exhaustive
        and result.frontier_empty
        and not result.labels_dropped
        and not observations
    )
    for row in candidates:
        values = observations.get(str(row["candidate_id"]), [])
        if values:
            row.update(
                {
                    "training_observed": True,
                    "training_label": "negative_route_member",
                    "training_grade": 3.0,
                    "observed_negative_column_count": len(values),
                    "best_observed_true_rc": min(values),
                }
            )
        elif exhaustive_no_negative:
            row.update(
                {
                    "training_observed": True,
                    "training_label": "exact_nonnegative",
                    "training_grade": 0.0,
                    "observed_negative_column_count": 0,
                    "best_observed_true_rc": None,
                }
            )
        else:
            row.update(
                {
                    "training_observed": False,
                    "training_label": "unexplored_not_a_negative",
                    "training_grade": None,
                    "observed_negative_column_count": 0,
                    "best_observed_true_rc": None,
                }
            )


def _reconstruct_column(request: BackendPricingRequest, route: dict):
    start_time = 0.0
    sorties = []
    for row in route.get("sorties", []) or []:
        tasks = tuple(str(task_id) for task_id in row.get("tasks", []))
        path_types = tuple(str(path_type) for path_type in row.get("path_types", []))
        if not tasks or len(path_types) != len(tasks) + 1:
            raise ValueError("native sortie path is incomplete")
        sortie = build_timed_sortie(request.data, tasks, path_types, start_time=start_time)
        if not sortie.feasible:
            raise ValueError(f"native route reconstructed infeasible: {sortie.infeasible_reason}")
        sorties.append(sortie)
        start_time = float(sortie.end_time)
    if not sorties:
        raise ValueError("native route contains no nonempty sortie")
    return build_journey_column(request.data, tuple(sorties))


def _manual_backend_reduced_cost(column, request: BackendPricingRequest) -> float:
    if request.objective_mode != BACKEND_OBJECTIVE_PHASE_ONE:
        return manual_journey_reduced_cost(
            column,
            request.true_duals,
            cut_coefficients=request.cut_context.coefficients_for(column),
        )
    return manual_phase_one_journey_reduced_cost(
        column,
        request.true_duals,
        cut_context=request.cut_context,
    )


def _empty_result(
    backend_id: str,
    status: str,
    *,
    blockers: tuple[str, ...],
    telemetry: dict | None = None,
) -> BackendResult:
    return BackendResult(
        backend_id=backend_id,
        engine_status=status,
        certificate_blockers=tuple(blockers),
        telemetry=dict(telemetry or {}),
    )


def _process_rss_bytes(pid: int | None) -> int:
    if not pid:
        return 0
    try:
        for line in Path(f"/proc/{pid}/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
        return 0
    return 0


def _available_memory_bytes() -> int | None:
    try:
        for line in Path("/proc/meminfo").read_text(
            encoding="utf-8"
        ).splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    except (
        FileNotFoundError,
        PermissionError,
        ValueError,
    ):
        return None
    return None


def _dynamic_host_memory_budget(
    *,
    configured_native_limit_bytes: int,
    host_rss_bytes: int,
    available_memory_bytes: int | None,
) -> dict[str, int | bool]:
    configured_native = max(
        0,
        int(configured_native_limit_bytes),
    )
    configured_watchdog = int(
        host_memory_watchdog_limit_gb(
            float(configured_native) / float(_GIB)
        )
        * _GIB
    )
    if configured_native == 0 or available_memory_bytes is None:
        return {
            "native_limit_bytes": configured_native,
            "watchdog_limit_bytes": configured_watchdog,
            "clamped": False,
            "preflight_rejected": False,
        }

    host_rss = max(0, int(host_rss_bytes))
    available = max(0, int(available_memory_bytes))
    growth_budget = max(
        0,
        available - _HOST_RUNTIME_AVAILABLE_RESERVE_BYTES,
    )
    watchdog_cap = min(
        configured_watchdog,
        host_rss + growth_budget,
    )
    if (
        configured_native >= _HOST_RUNTIME_MIN_NATIVE_BUDGET_BYTES
        and watchdog_cap
        < host_rss + _HOST_RUNTIME_MIN_NATIVE_BUDGET_BYTES
    ):
        return {
            "native_limit_bytes": 0,
            "watchdog_limit_bytes": max(0, watchdog_cap),
            "clamped": True,
            "preflight_rejected": True,
        }

    low = 0
    high = configured_native
    while low < high:
        candidate = (low + high + 1) // 2
        candidate_watchdog = int(
            host_memory_watchdog_limit_gb(
                float(candidate) / float(_GIB)
            )
            * _GIB
        )
        if candidate_watchdog <= watchdog_cap:
            low = candidate
        else:
            high = candidate - 1
    native_limit = int(low)
    watchdog_limit = int(
        host_memory_watchdog_limit_gb(
            float(native_limit) / float(_GIB)
        )
        * _GIB
    )
    preflight_rejected = bool(
        configured_native >= _HOST_RUNTIME_MIN_NATIVE_BUDGET_BYTES
        and watchdog_limit <= host_rss
    )
    return {
        "native_limit_bytes": (
            0 if preflight_rejected else native_limit
        ),
        "watchdog_limit_bytes": watchdog_limit,
        "clamped": bool(
            native_limit < configured_native
            or watchdog_limit < configured_watchdog
        ),
        "preflight_rejected": preflight_rejected,
    }


def host_memory_watchdog_limit_gb(native_limit_gb: float) -> float:
    """Return the emergency host limit above the native cooperative limit.

    A zero native limit keeps both layers disabled.  For a positive limit the
    bounded margin is large enough for the native loop to observe its own
    threshold, construct the partial result, release label memory, and reply.
    It is deliberately capped so a broken native worker still fails closed.
    """

    native_limit_bytes = max(0, int(float(native_limit_gb) * _GIB))
    if native_limit_bytes == 0:
        return 0
    headroom_bytes = int(
        native_limit_bytes * _HOST_MEMORY_WATCHDOG_HEADROOM_FRACTION
    )
    headroom_bytes = max(
        _HOST_MEMORY_WATCHDOG_MIN_HEADROOM_BYTES,
        min(_HOST_MEMORY_WATCHDOG_MAX_HEADROOM_BYTES, headroom_bytes),
    )
    return float(native_limit_bytes + headroom_bytes) / float(_GIB)


def effective_memory_limit_gb(nominal_gb: float) -> float:
    """Return min(profile limit, 70% physical RAM), without optional dependencies."""

    pages = os.sysconf("SC_PHYS_PAGES")
    page_size = os.sysconf("SC_PAGE_SIZE")
    physical_gb = float(pages * page_size) / float(1024**3)
    return min(max(0.0, float(nominal_gb)), 0.70 * physical_gb)


def _optional_float(value) -> float | None:
    return None if value is None else float(value)
