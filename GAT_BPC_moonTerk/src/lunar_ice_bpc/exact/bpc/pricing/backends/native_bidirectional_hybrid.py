"""Exact-safe all-scale bidirectional negative-column prepasses.

The midpoint meet has no certificate authority.  The v1 backend accepts only
exhaustive midpoint witness pools.  The v2 backend also accepts negative
witnesses retained by a limited midpoint search.  Both variants re-audit every
route under the true dual and fall back to the unchanged P0V4 backend whenever
there is no usable witness or any audit fails.
"""

from __future__ import annotations

from dataclasses import replace
import importlib
from math import isfinite
from time import perf_counter

from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
    BACKEND_MODE_EXACT_PROOF,
    BACKEND_MODE_NEGATIVE_HARVEST,
    BACKEND_OBJECTIVE_OFFICIAL,
    PRICING_LIFECYCLE_SCOPE_ROOT_CG,
    BackendPricingRequest,
    BackendResult,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
    NATIVE_HOST_BACKEND_ID,
    NATIVE_INPROCESS_BACKEND_ID,
    NativeRcsppHostBackend,
    NativeRcsppInprocessBackend,
    _binding_blockers,
    _capability_blockers,
    _manual_backend_reduced_cost,
    _native_request_payload,
    _reconstruct_column,
)
from lunar_ice_bpc.exact.core.branching import (
    journey_satisfies_branch_context,
)
from lunar_ice_bpc.guidance.bidirectional_gate_runtime import (
    BidirectionalGateDecision,
    decide_bidirectional_prepass_from_environment,
    record_bidirectional_prepass_outcome,
)


NATIVE_BIDIRECTIONAL_MIDPOINT_HYBRID_BACKEND_ID = (
    "native_rcspp_bidirectional_midpoint_hybrid_v1"
)
NATIVE_BIDIRECTIONAL_MIDPOINT_PARTIAL_HYBRID_BACKEND_ID = (
    "native_rcspp_bidirectional_midpoint_partial_hybrid_v2"
)
NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID = (
    "native_rcspp_bidirectional_root_partial_hybrid_v3"
)
MIDPOINT_POLICY_ID = "p0v4_frozen_dual_depot_midpoint_meet_v1"
MIDPOINT_EXHAUSTIVE_HYBRID_POLICY_ID = (
    "p0v4_midpoint_exhaustive_witness_hybrid_v1"
)
MIDPOINT_PARTIAL_HYBRID_POLICY_ID = (
    "p0v4_midpoint_partial_witness_hybrid_v2"
)
MIDPOINT_ROOT_PARTIAL_HYBRID_POLICY_ID = (
    "p0v4_root_partial_tree_conservative_hybrid_v3"
)
MIDPOINT_CERTIFICATE_AUTHORITY = "none"
MIDPOINT_SUPPORTED_SCALES = frozenset({5, 10, 20, 30, 50})
P0V4_INPROCESS_SCALES = frozenset({5, 10, 20, 30})


class NativeBidirectionalMidpointHybridBackend:
    """Return audited midpoint negatives, otherwise run frozen P0V4."""

    backend_id = NATIVE_BIDIRECTIONAL_MIDPOINT_HYBRID_BACKEND_ID
    hybrid_policy_id = MIDPOINT_EXHAUSTIVE_HYBRID_POLICY_ID
    allow_partial_witnesses = False

    def solve(self, request: BackendPricingRequest) -> BackendResult:
        eligibility_reason = self._eligibility_reason(request)
        if eligibility_reason:
            return self._fallback(
                request,
                attempted=False,
                reason=eligibility_reason,
            )
        gate_decision = decide_bidirectional_prepass_from_environment(
            request
        )
        gate_telemetry = self._gate_telemetry(gate_decision)
        if gate_decision.skips_prepass:
            record_bidirectional_prepass_outcome(
                request, accepted=None, skipped=True
            )
            return self._fallback(
                request,
                attempted=False,
                reason="gat_predicted_midpoint_failure",
                prepass_telemetry=gate_telemetry,
            )
        started = perf_counter()
        try:
            native = importlib.import_module("lunar_spprc_native")
            build_info = dict(native.build_info())
            build_reason = self._build_reason(native, build_info)
            if build_reason:
                return self._fallback(
                    request,
                    attempted=False,
                    reason=build_reason,
                    prepass_telemetry=gate_telemetry,
                )
            payload = _native_request_payload(request)
            payload.update(self._midpoint_parameters(request))
            raw = dict(
                native.bidirectional_midpoint_journey_meet(payload)
            )
            audited = self._audit_midpoint_result(
                request,
                raw,
                build_info=build_info,
                elapsed_sec=perf_counter() - started,
            )
        except Exception as exc:
            record_bidirectional_prepass_outcome(
                request, accepted=False
            )
            return self._fallback(
                request,
                attempted=True,
                reason="midpoint_exception",
                detail=repr(exc),
                prepass_wall_sec=perf_counter() - started,
                prepass_telemetry=gate_telemetry,
            )
        if audited is None:
            record_bidirectional_prepass_outcome(
                request, accepted=False
            )
            return self._fallback(
                request,
                attempted=True,
                reason="midpoint_no_audited_negative",
                prepass_wall_sec=perf_counter() - started,
                prepass_telemetry={
                    **self._fallback_prepass_telemetry(raw),
                    **gate_telemetry,
                },
            )
        record_bidirectional_prepass_outcome(request, accepted=True)
        return replace(
            audited,
            telemetry={**audited.telemetry, **gate_telemetry},
        )

    @staticmethod
    def _eligibility_reason(request: BackendPricingRequest) -> str:
        if request.mode not in {
            BACKEND_MODE_EXACT_PROOF,
            BACKEND_MODE_NEGATIVE_HARVEST,
        }:
            return "unsupported_backend_mode"
        if request.objective_mode != BACKEND_OBJECTIVE_OFFICIAL:
            return "nonofficial_objective"
        if (
            len(request.data.task_ids)
            not in MIDPOINT_SUPPORTED_SCALES
        ):
            return "scale_not_enabled"
        blockers = (
            *_capability_blockers(request),
            *_binding_blockers(request),
        )
        if blockers:
            return "request_precheck_failed:" + ",".join(blockers)
        return ""

    @staticmethod
    def _build_reason(native, build_info: dict) -> str:
        if not hasattr(
            native,
            "bidirectional_midpoint_journey_meet",
        ):
            return "midpoint_callable_missing"
        if (
            str(
                build_info.get(
                    "bidirectional_feasibility_compiled"
                )
            )
            != "true"
        ):
            return "midpoint_not_compiled"
        if (
            str(
                build_info.get(
                    "bidirectional_midpoint_meet_policy"
                )
            )
            != MIDPOINT_POLICY_ID
        ):
            return "midpoint_policy_mismatch"
        if (
            str(
                build_info.get(
                    "bidirectional_feasibility_certificate_authority"
                )
            )
            != MIDPOINT_CERTIFICATE_AUTHORITY
        ):
            return "midpoint_certificate_authority_mismatch"
        return ""

    @staticmethod
    def _midpoint_parameters(
        request: BackendPricingRequest,
    ) -> dict:
        requested_wall_limit = request.wall_time_limit_sec
        if (
            requested_wall_limit is None
            or not isfinite(float(requested_wall_limit))
        ):
            requested_wall_limit = 30.0
        wall_limit = min(
            30.0,
            max(0.001, float(requested_wall_limit)),
        )
        return {
            "bidirectional_max_partial_states_per_direction": 1_000_000,
            "bidirectional_max_join_checks": 200_000_000,
            "bidirectional_sortie_wall_time_limit_sec": wall_limit,
            "bidirectional_midpoint_split_fraction": 0.1,
            "bidirectional_midpoint_max_forward_labels": 250_000,
            "bidirectional_midpoint_max_backward_labels": 250_000,
            "bidirectional_midpoint_max_crossing_labels": 250_000,
            "bidirectional_midpoint_max_extension_checks": 200_000_000,
            "bidirectional_midpoint_max_join_checks": 200_000_000,
            "bidirectional_midpoint_max_returned_negative_routes": max(
                1,
                min(
                    4_096,
                    int(request.exact_raw_negative_pool_size),
                ),
            ),
            "bidirectional_midpoint_wall_time_limit_sec": wall_limit,
        }

    def _audit_midpoint_result(
        self,
        request: BackendPricingRequest,
        raw: dict,
        *,
        build_info: dict,
        elapsed_sec: float,
    ) -> BackendResult | None:
        if bool(raw.get("can_certify_no_negative")):
            raise ValueError("midpoint certificate authority leaked")
        if str(raw.get("policy_id") or "") != MIDPOINT_POLICY_ID:
            raise ValueError("midpoint result policy mismatch")
        search_exhaustive = bool(raw.get("search_exhaustive"))
        if (
            not search_exhaustive
            and not self._partial_witnesses_allowed(request)
        ):
            return None
        if search_exhaustive:
            for field in (
                "forward_exhaustive",
                "backward_exhaustive",
                "crossing_exhaustive",
                "join_exhaustive",
            ):
                if not bool(raw.get(field)):
                    raise ValueError(
                        f"midpoint exhaustive flag mismatch: {field}"
                    )
        raw_routes = tuple(raw.get("routes") or ())
        if not raw_routes:
            return None
        best_raw_value = raw.get("best_true_reduced_cost")
        if best_raw_value is None:
            raise ValueError(
                "midpoint returned witnesses without a best value"
            )
        best_raw = float(best_raw_value)
        if not isfinite(best_raw):
            raise ValueError(
                "midpoint returned witnesses with a nonfinite best value"
            )
        if best_raw >= -request.negative_eps:
            raise ValueError(
                "midpoint returned witnesses without a negative best value"
            )

        audited_rows = []
        task_sets: set[frozenset[str]] = set()
        max_rc_delta = 0.0
        for route in raw_routes:
            column = _reconstruct_column(request, route)
            task_set = frozenset(str(x) for x in column.task_set)
            if task_set in task_sets:
                raise ValueError(
                    "midpoint returned duplicate task-set witness"
                )
            task_sets.add(task_set)
            if not journey_satisfies_branch_context(
                column,
                request.branch_context,
            ):
                raise ValueError(
                    "midpoint returned branch-infeasible witness"
                )
            manual_rc = float(
                _manual_backend_reduced_cost(column, request)
            )
            native_rc = float(route["reduced_cost"])
            rc_delta = abs(native_rc - manual_rc)
            max_rc_delta = max(max_rc_delta, rc_delta)
            if rc_delta > request.reconstruction_eps:
                raise ValueError(
                    "midpoint native/Python reduced-cost mismatch"
                )
            if manual_rc >= -request.negative_eps:
                raise ValueError(
                    "midpoint returned nonnegative witness"
                )
            audited_rows.append((manual_rc, column))
        audited_rows.sort(key=lambda row: row[0])
        best_found = float(audited_rows[0][0])
        if abs(best_found - best_raw) > request.reconstruction_eps:
            raise ValueError(
                "midpoint best witness does not match exact best value"
            )

        telemetry = {
            key: value
            for key, value in raw.items()
            if key not in {"routes", "build_info"}
        }
        telemetry.update(
            {
                "bidirectional_midpoint_hybrid_attempted": True,
                "bidirectional_midpoint_hybrid_accepted": True,
                "bidirectional_midpoint_hybrid_fallback_used": False,
                "bidirectional_midpoint_hybrid_policy_id": (
                    self.hybrid_policy_id
                ),
                "pricing_lifecycle_scope": (
                    request.pricing_lifecycle_scope
                ),
                "bidirectional_midpoint_partial_scope_policy": (
                    self._partial_scope_policy_id()
                ),
                "bidirectional_midpoint_partial_allowed_for_scope": (
                    self._partial_witnesses_allowed(request)
                ),
                "bidirectional_midpoint_native_policy_id": (
                    MIDPOINT_POLICY_ID
                ),
                "bidirectional_midpoint_certificate_authority": (
                    MIDPOINT_CERTIFICATE_AUTHORITY
                ),
                "bidirectional_midpoint_partial_witness_accepted": (
                    not search_exhaustive
                ),
                "bidirectional_midpoint_raw_search_exhaustive": (
                    search_exhaustive
                ),
                "bidirectional_midpoint_raw_status": str(
                    raw.get("status") or ""
                ),
                "bidirectional_midpoint_raw_route_count": len(
                    raw_routes
                ),
                "bidirectional_midpoint_prepass_wall_sec": round(
                    float(elapsed_sec),
                    9,
                ),
                "bidirectional_midpoint_max_rc_delta": max_rc_delta,
                "bidirectional_midpoint_native_build_info": (
                    build_info
                ),
                "negative_escape_triggered": True,
                "negative_escape_termination_reason": (
                    "BIDIRECTIONAL_MIDPOINT_EXHAUSTIVE_NEGATIVE_POOL"
                    if search_exhaustive
                    else "BIDIRECTIONAL_MIDPOINT_PARTIAL_NEGATIVE_POOL"
                ),
                "raw_unique_negative_count": len(audited_rows),
                "dssr_enabled": False,
                "wall_time_seconds": float(
                    raw.get("wall_time_seconds") or elapsed_sec
                ),
            }
        )
        return BackendResult(
            backend_id=self.backend_id,
            engine_status="FOUND_NEGATIVE_PARTIAL",
            best_found_rc=best_found,
            global_min_rc=None,
            global_min_rc_is_exact=False,
            proved_no_rc_below=None,
            unexplored_rc_lower_bound=None,
            search_exhaustive=False,
            frontier_empty=False,
            labels_dropped=False,
            partial_columns_valid=True,
            columns=tuple(row[1] for row in audited_rows),
            certificate_blockers=(
                "native_exact_search_incomplete",
                "native_frontier_not_empty",
                "native_exact_negative_escape_partial",
            ),
            telemetry=telemetry,
        )

    def _fallback(
        self,
        request: BackendPricingRequest,
        *,
        attempted: bool,
        reason: str,
        detail: str = "",
        prepass_wall_sec: float = 0.0,
        prepass_telemetry: dict | None = None,
    ) -> BackendResult:
        fallback_backend, fallback_backend_id = (
            self._p0v4_fallback_backend(request)
        )
        fallback = fallback_backend.solve(request)
        telemetry = dict(fallback.telemetry)
        telemetry.update(
            {
                "bidirectional_midpoint_hybrid_attempted": (
                    bool(attempted)
                ),
                "bidirectional_midpoint_hybrid_accepted": False,
                "bidirectional_midpoint_hybrid_fallback_used": True,
                "bidirectional_midpoint_hybrid_policy_id": (
                    self.hybrid_policy_id
                ),
                "pricing_lifecycle_scope": (
                    request.pricing_lifecycle_scope
                ),
                "bidirectional_midpoint_partial_scope_policy": (
                    self._partial_scope_policy_id()
                ),
                "bidirectional_midpoint_partial_allowed_for_scope": (
                    self._partial_witnesses_allowed(request)
                ),
                "bidirectional_midpoint_native_policy_id": (
                    MIDPOINT_POLICY_ID
                ),
                "bidirectional_midpoint_hybrid_fallback_reason": (
                    str(reason)
                ),
                "bidirectional_midpoint_hybrid_fallback_detail": (
                    str(detail)
                ),
                "bidirectional_midpoint_prepass_wall_sec": round(
                    float(prepass_wall_sec),
                    9,
                ),
                "bidirectional_midpoint_fallback_backend_id": (
                    fallback_backend_id
                ),
            }
        )
        telemetry.update(dict(prepass_telemetry or {}))
        return replace(
            fallback,
            backend_id=self.backend_id,
            telemetry=telemetry,
        )

    def _partial_witnesses_allowed(
        self,
        request: BackendPricingRequest,
    ) -> bool:
        return bool(self.allow_partial_witnesses)

    @staticmethod
    def _partial_scope_policy_id() -> str:
        return "exhaustive_only"

    @staticmethod
    def _fallback_prepass_telemetry(raw: dict) -> dict:
        """Retain bounded failure evidence without persisting route payloads."""

        keys = (
            "status",
            "search_exhaustive",
            "forward_exhaustive",
            "backward_exhaustive",
            "crossing_exhaustive",
            "join_exhaustive",
            "sortie_pool_size",
            "forward_generated_labels",
            "forward_processed_labels",
            "backward_generated_labels",
            "backward_processed_labels",
            "crossing_generated_labels",
            "extension_checks",
            "join_checks",
            "terminal_route_count",
            "negative_terminal_route_count",
            "best_true_reduced_cost",
            "wall_time_seconds",
        )
        telemetry = {
            f"bidirectional_midpoint_raw_{key}": raw.get(key)
            for key in keys
            if key in raw
        }
        telemetry["bidirectional_midpoint_raw_route_count"] = len(
            tuple(raw.get("routes") or ())
        )
        return telemetry

    @staticmethod
    def _gate_telemetry(
        decision: BidirectionalGateDecision,
    ) -> dict:
        return {
            "bidirectional_gate_gat_action": decision.action,
            "bidirectional_gate_gat_reason": decision.reason,
            "bidirectional_gate_gat_failure_probability": (
                decision.failure_probability
            ),
            "bidirectional_gate_gat_expected_wasted_time_sec": (
                decision.expected_wasted_time_sec
            ),
            "bidirectional_gate_gat_inference_wall_ms": round(
                float(decision.inference_wall_ms), 6
            ),
            "bidirectional_gate_gat_ood": bool(decision.ood),
            "bidirectional_gate_gat_manifest_sha256": (
                decision.manifest_sha256
            ),
            "bidirectional_gate_gat_checkpoint_sha256": (
                decision.checkpoint_sha256
            ),
        }

    @staticmethod
    def _p0v4_fallback_backend(
        request: BackendPricingRequest,
    ):
        if len(request.data.task_ids) in P0V4_INPROCESS_SCALES:
            return (
                NativeRcsppInprocessBackend(),
                NATIVE_INPROCESS_BACKEND_ID,
            )
        return NativeRcsppHostBackend(), NATIVE_HOST_BACKEND_ID


class NativeBidirectionalMidpointPartialHybridBackend(
    NativeBidirectionalMidpointHybridBackend
):
    """Use audited negative witnesses even when midpoint search is partial."""

    backend_id = (
        NATIVE_BIDIRECTIONAL_MIDPOINT_PARTIAL_HYBRID_BACKEND_ID
    )
    hybrid_policy_id = MIDPOINT_PARTIAL_HYBRID_POLICY_ID
    allow_partial_witnesses = True

    @staticmethod
    def _partial_scope_policy_id() -> str:
        return "all_pricing_scopes"


class NativeBidirectionalRootPartialHybridBackend(
    NativeBidirectionalMidpointHybridBackend
):
    """Accept partial witnesses only during the pre-tree root CG lifecycle."""

    backend_id = (
        NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID
    )
    hybrid_policy_id = MIDPOINT_ROOT_PARTIAL_HYBRID_POLICY_ID
    allow_partial_witnesses = False

    def _partial_witnesses_allowed(
        self,
        request: BackendPricingRequest,
    ) -> bool:
        return (
            request.pricing_lifecycle_scope
            == PRICING_LIFECYCLE_SCOPE_ROOT_CG
        )

    @staticmethod
    def _partial_scope_policy_id() -> str:
        return "root_cg_only_tree_conservative"
