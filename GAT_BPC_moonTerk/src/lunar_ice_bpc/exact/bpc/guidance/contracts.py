"""Exact-side immutable contracts for learning-guided work ordering.

This module deliberately has no ML-framework imports. It accepts already
computed hints, binds them to the canonical exact request, and offers pure
ordering helpers that cannot filter the legal universe.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from math import isfinite
from time import perf_counter
from typing import Any

from lunar_ice_bpc.exact.core.cuts import (
    pricing_cut_context_from_duals,
    raw_ieee_dual_hash,
    stable_payload_hash,
    true_dual_binding_hash,
)


CANONICAL_SOLVE_BINDING_SCHEMA_V2 = "lunar_ice_bpc.canonical_solve_binding.v2"
PRICING_ORDERING_HINTS_SCHEMA_V2 = "lunar_ice_bpc.pricing_ordering_hints.v2"
GUIDANCE_LIFECYCLE_TELEMETRY_SCHEMA_V2 = (
    "lunar_ice_bpc.guidance_lifecycle_telemetry.v2"
)
# Backward-compatible symbol for callers that imported the original name.
GUIDANCE_LIFECYCLE_TELEMETRY_SCHEMA_V1 = (
    GUIDANCE_LIFECYCLE_TELEMETRY_SCHEMA_V2
)
GUIDANCE_MODE_OFF = "off"
GUIDANCE_MODE_SHADOW = "shadow"
GUIDANCE_MODE_HARVEST = "harvest"
GUIDANCE_MODE_TASK_ARC = "task_arc"
GUIDANCE_MODES = frozenset(
    {
        GUIDANCE_MODE_OFF,
        GUIDANCE_MODE_SHADOW,
        GUIDANCE_MODE_HARVEST,
        GUIDANCE_MODE_TASK_ARC,
    }
)


@dataclass(frozen=True)
class CanonicalSolveBindingV2:
    instance_hash: str
    config_hash: str
    engine_hash: str
    pricing_mode: str
    phase: str
    objective_mode: str
    rmp_iteration_id: str
    mathematical_dual_hash: str
    raw_ieee_dual_hash: str
    request_dual_hash: str
    branch_context_hash: str
    full_cut_context_hash: str
    projected_pricing_cut_context_hash: str
    cut_lineage_hash: str
    live_cut_policy_hash: str
    separator_policy_version: str
    cut_state_schema_version: str
    feature_schema_version: str = ""
    normalization_version: str = ""
    checkpoint_id: str = ""
    ood_policy_version: str = ""
    schema_version: str = CANONICAL_SOLVE_BINDING_SCHEMA_V2

    @classmethod
    def from_backend_request(
        cls,
        request: Any,
        *,
        engine_hash: str = "",
        feature_schema_version: str = "",
        normalization_version: str = "",
        checkpoint_id: str = "",
        ood_policy_version: str = "",
    ) -> "CanonicalSolveBindingV2":
        duals = request.true_duals
        full_cut_context = request.cut_context
        projected_cut_context = pricing_cut_context_from_duals(
            full_cut_context,
            duals.cuts,
            enabled=bool(request.cut_dual_projection_enabled),
        )
        instance_hash = str(
            request.instance_hash
            or getattr(request.data, "instance_content_hash", "")
        )
        return cls(
            instance_hash=instance_hash,
            config_hash=str(request.config_hash),
            engine_hash=str(
                engine_hash or getattr(request, "engine_hash", "")
            ),
            pricing_mode=str(request.mode),
            phase=(
                "phase_one"
                if str(request.objective_mode) == "phase_one"
                else "phase_two"
            ),
            objective_mode=str(request.objective_mode),
            rmp_iteration_id=str(request.rmp_iteration_id),
            mathematical_dual_hash=true_dual_binding_hash(
                duals.cover,
                fleet_limit=duals.fleet_limit,
                cuts=duals.cuts,
            ),
            raw_ieee_dual_hash=raw_ieee_dual_hash(
                duals.cover,
                fleet_limit=duals.fleet_limit,
                cuts=duals.cuts,
            ),
            request_dual_hash=str(request.dual_binding_hash),
            branch_context_hash=stable_payload_hash(
                request.branch_context.to_payload()
            ),
            full_cut_context_hash=str(
                full_cut_context.active_cut_context_hash
            ),
            projected_pricing_cut_context_hash=str(
                projected_cut_context.active_cut_context_hash
            ),
            cut_lineage_hash=str(request.cut_lineage_hash),
            live_cut_policy_hash=str(request.live_cut_policy_hash),
            separator_policy_version=str(request.separator_policy_version),
            cut_state_schema_version=str(request.cut_state_schema_version),
            feature_schema_version=str(
                feature_schema_version
                or getattr(request, "guidance_feature_schema_version", "")
            ),
            normalization_version=str(
                normalization_version
                or getattr(request, "guidance_normalization_version", "")
            ),
            checkpoint_id=str(
                checkpoint_id
                or getattr(request, "guidance_checkpoint_id", "")
            ),
            ood_policy_version=str(
                ood_policy_version
                or getattr(request, "guidance_ood_policy_version", "")
            ),
        )

    @property
    def binding_hash(self) -> str:
        return stable_payload_hash(self.to_payload(include_binding_hash=False))

    def to_payload(self, *, include_binding_hash: bool = True) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "instance_hash": self.instance_hash,
            "config_hash": self.config_hash,
            "engine_hash": self.engine_hash,
            "pricing_mode": self.pricing_mode,
            "phase": self.phase,
            "objective_mode": self.objective_mode,
            "rmp_iteration_id": self.rmp_iteration_id,
            "mathematical_dual_hash": self.mathematical_dual_hash,
            "raw_ieee_dual_hash": self.raw_ieee_dual_hash,
            "request_dual_hash": self.request_dual_hash,
            "branch_context_hash": self.branch_context_hash,
            "full_cut_context_hash": self.full_cut_context_hash,
            "projected_pricing_cut_context_hash": self.projected_pricing_cut_context_hash,
            "cut_lineage_hash": self.cut_lineage_hash,
            "live_cut_policy_hash": self.live_cut_policy_hash,
            "separator_policy_version": self.separator_policy_version,
            "cut_state_schema_version": self.cut_state_schema_version,
            "feature_schema_version": self.feature_schema_version,
            "normalization_version": self.normalization_version,
            "checkpoint_id": self.checkpoint_id,
            "ood_policy_version": self.ood_policy_version,
        }
        if include_binding_hash:
            payload["binding_hash"] = self.binding_hash
        return payload

    @staticmethod
    def request_consistency_issues(request: Any) -> tuple[str, ...]:
        """Audit redundant request hashes against the exact request objects."""

        issues: list[str] = []
        actual_instance = str(
            getattr(request.data, "instance_content_hash", "")
        )
        if request.instance_hash and str(request.instance_hash) != actual_instance:
            issues.append("request_instance_hash_mismatch")
        actual_dual = true_dual_binding_hash(
            request.true_duals.cover,
            fleet_limit=request.true_duals.fleet_limit,
            cuts=request.true_duals.cuts,
        )
        if request.dual_binding_hash and str(request.dual_binding_hash) != actual_dual:
            issues.append("request_mathematical_dual_hash_mismatch")
        actual_branch = stable_payload_hash(request.branch_context.to_payload())
        if (
            request.branch_context_hash not in {"", "empty"}
            and str(request.branch_context_hash) != actual_branch
        ):
            issues.append("request_branch_context_hash_mismatch")
        actual_cut = request.cut_context.active_cut_context_hash
        if (
            request.cut_context_hash not in {"", "empty"}
            and str(request.cut_context_hash) != actual_cut
        ):
            issues.append("request_cut_context_hash_mismatch")
        return tuple(issues)


@dataclass(frozen=True)
class PricingOrderingHintsV2:
    binding_hash: str
    task_priorities: tuple[tuple[str, float], ...] = tuple()
    arc_priorities: tuple[tuple[str, float], ...] = tuple()
    harvest_priorities: tuple[tuple[str, float], ...] = tuple()
    proof_tail_risk: float | None = None
    queue_policy_id: str = "Q0"
    uncertainty: float = 0.0
    ood: bool = False
    source: str = "shadow"
    diagnostic_only: bool = True
    schema_version: str = PRICING_ORDERING_HINTS_SCHEMA_V2

    def __post_init__(self) -> None:
        if not self.binding_hash:
            raise ValueError("binding_hash must be non-empty")
        if self.queue_policy_id not in {"Q0", "Q1", "Q2", "Q3", "Q4"}:
            raise ValueError("unsupported queue_policy_id")
        values = [
            *[value for _, value in self.task_priorities],
            *[value for _, value in self.arc_priorities],
            *[value for _, value in self.harvest_priorities],
            self.uncertainty,
        ]
        if self.proof_tail_risk is not None:
            values.append(self.proof_tail_risk)
        if any(not isfinite(float(value)) for value in values):
            raise ValueError("guidance scores must be finite")
        for name, rows in (
            ("task", self.task_priorities),
            ("arc", self.arc_priorities),
            ("harvest", self.harvest_priorities),
        ):
            ids = [str(candidate_id) for candidate_id, _ in rows]
            if len(ids) != len(set(ids)):
                raise ValueError(f"duplicate {name} guidance candidate id")

    def priorities_for(self, kind: str) -> dict[str, float]:
        rows = {
            "task": self.task_priorities,
            "arc": self.arc_priorities,
            "harvest": self.harvest_priorities,
        }.get(str(kind), tuple())
        return {str(candidate_id): float(priority) for candidate_id, priority in rows}

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "binding_hash": self.binding_hash,
            "task_priorities": [list(row) for row in self.task_priorities],
            "arc_priorities": [list(row) for row in self.arc_priorities],
            "harvest_priorities": [list(row) for row in self.harvest_priorities],
            "proof_tail_risk": self.proof_tail_risk,
            "queue_policy_id": self.queue_policy_id,
            "uncertainty": self.uncertainty,
            "ood": self.ood,
            "source": self.source,
            "diagnostic_only": self.diagnostic_only,
        }


@dataclass
class GuidanceLifecycleTelemetry:
    guidance_cheap_gate_sec: float = 0.0
    guidance_import_sec: float = 0.0
    guidance_checkpoint_load_sec: float = 0.0
    guidance_tensorize_sec: float = 0.0
    guidance_forward_total_sec: float = 0.0
    guidance_call_count: int = 0
    guidance_binding_validation_sec: float = 0.0
    guidance_native_install_sec: float = 0.0
    baseline_total_wall_sec: float | None = None
    bypassed_before_import: bool = False
    bypass_reason: str = ""
    cheap_gate_eligible: bool | None = None
    cheap_gate_candidate_count: int = 0
    cheap_gate_negative_mass: float = 0.0

    @property
    def guidance_total_wall_sec(self) -> float:
        return float(
            self.guidance_cheap_gate_sec
            + self.guidance_import_sec
            + self.guidance_checkpoint_load_sec
            + self.guidance_tensorize_sec
            + self.guidance_forward_total_sec
            + self.guidance_binding_validation_sec
            + self.guidance_native_install_sec
        )

    def to_payload(self) -> dict[str, Any]:
        total = self.guidance_total_wall_sec
        baseline = self.baseline_total_wall_sec
        return {
            "schema_version": GUIDANCE_LIFECYCLE_TELEMETRY_SCHEMA_V1,
            "guidance_cheap_gate_sec": round(
                self.guidance_cheap_gate_sec, 9
            ),
            "guidance_import_sec": round(self.guidance_import_sec, 9),
            "guidance_checkpoint_load_sec": round(
                self.guidance_checkpoint_load_sec, 9
            ),
            "guidance_tensorize_sec": round(self.guidance_tensorize_sec, 9),
            "guidance_forward_total_sec": round(
                self.guidance_forward_total_sec, 9
            ),
            "guidance_call_count": int(self.guidance_call_count),
            "guidance_binding_validation_sec": round(
                self.guidance_binding_validation_sec, 9
            ),
            "guidance_native_install_sec": round(
                self.guidance_native_install_sec, 9
            ),
            "guidance_total_wall_sec": round(total, 9),
            "guidance_total_wall_ratio": (
                None
                if baseline is None or float(baseline) <= 0.0
                else round(total / float(baseline), 9)
            ),
            "bypassed_before_import": bool(self.bypassed_before_import),
            "bypass_reason": str(self.bypass_reason),
            "cheap_gate_eligible": self.cheap_gate_eligible,
            "cheap_gate_candidate_count": int(
                self.cheap_gate_candidate_count
            ),
            "cheap_gate_negative_mass": round(
                float(self.cheap_gate_negative_mass), 9
            ),
        }


def canonical_universe_hash(
    candidate_ids: Iterable[str],
    *,
    universe_kind: str,
) -> str:
    ordered = tuple(sorted(str(candidate_id) for candidate_id in candidate_ids))
    return stable_payload_hash(
        {
            "schema_version": "lunar_ice_bpc.guidance_universe.v1",
            "universe_kind": str(universe_kind),
            "candidate_ids": ordered,
        }
    )


def canonical_arc_candidate_id(
    source: str,
    target: str,
    path_type: str,
) -> str:
    return f"arc:{str(source)}|{str(target)}|{str(path_type)}"


def canonical_harvest_candidate_id(signature: object) -> str:
    return "harvest:" + stable_payload_hash(
        {
            "schema_version": "lunar_ice_bpc.harvest_candidate_id.v1",
            "signature": repr(signature),
        }
    )


def reorder_preserving_universe(
    rows: Iterable[Mapping[str, Any]],
    *,
    priorities: Mapping[str, float],
    candidate_id_key: str = "candidate_id",
    universe_kind: str = "candidate",
    enabled: bool,
) -> tuple[tuple[dict[str, Any], ...], dict[str, Any]]:
    """Reorder rows without admitting any filtering operation."""

    started = perf_counter()
    materialized = tuple(dict(row) for row in rows)
    before_ids = tuple(
        str(row.get(candidate_id_key) or f"candidate_{index}")
        for index, row in enumerate(materialized)
    )
    if len(before_ids) != len(set(before_ids)):
        raise ValueError("legal ordering universe contains duplicate candidate ids")
    indexed = tuple(enumerate(materialized))
    if enabled:
        ordered = tuple(
            row
            for _, row in sorted(
                indexed,
                key=lambda item: (
                    -float(
                        priorities.get(
                            str(
                                item[1].get(candidate_id_key)
                                or f"candidate_{item[0]}"
                            ),
                            0.0,
                        )
                    ),
                    item[0],
                ),
            )
        )
    else:
        ordered = materialized
    after_ids = tuple(
        str(row.get(candidate_id_key) or f"candidate_{index}")
        for index, row in enumerate(ordered)
    )
    before_hash = canonical_universe_hash(before_ids, universe_kind=universe_kind)
    after_hash = canonical_universe_hash(after_ids, universe_kind=universe_kind)
    if before_hash != after_hash:
        raise RuntimeError("guidance ordering changed the legal candidate universe")
    return ordered, {
        "schema_version": "lunar_ice_bpc.guidance_ordering_audit.v2",
        "enabled": bool(enabled),
        "candidate_count": len(materialized),
        "legal_action_universe_hash_before_sort": before_hash,
        "legal_action_universe_hash_after_sort": after_hash,
        "guidance_filter_count": 0,
        "guidance_arc_drop_count": 0,
        "guidance_label_drop_count": 0,
        "guidance_branch_pair_drop_count": 0,
        "missing_hint_count": sum(
            1 for candidate_id in before_ids if candidate_id not in priorities
        ),
        "ordering_wall_sec": round(perf_counter() - started, 9),
    }


def validate_pricing_ordering_hints(
    request: Any,
) -> tuple[PricingOrderingHintsV2 | None, dict[str, Any]]:
    """Validate an entire hint bundle and otherwise fall back to P0."""

    started = perf_counter()
    mode = str(getattr(request, "guidance_mode", GUIDANCE_MODE_OFF))
    hints = getattr(request, "guidance_hints", None)
    issues: list[str] = []
    if mode == GUIDANCE_MODE_OFF:
        issues.append("guidance_mode_off")
    if hints is None:
        issues.append("guidance_hints_missing")
    expected_binding = CanonicalSolveBindingV2.from_backend_request(
        request,
        engine_hash=str(getattr(request, "engine_hash", "")),
        feature_schema_version=str(
            getattr(request, "guidance_feature_schema_version", "")
        ),
        normalization_version=str(
            getattr(request, "guidance_normalization_version", "")
        ),
        checkpoint_id=str(getattr(request, "guidance_checkpoint_id", "")),
        ood_policy_version=str(
            getattr(request, "guidance_ood_policy_version", "")
        ),
    )
    if hints is not None:
        if hints.binding_hash != expected_binding.binding_hash:
            issues.append("guidance_binding_hash_mismatch")
        if hints.ood:
            issues.append("guidance_ood")
        if hints.queue_policy_id != "Q0":
            issues.append("proof_queue_online_not_enabled")
    issues.extend(CanonicalSolveBindingV2.request_consistency_issues(request))
    accepted = hints if not issues else None
    return accepted, {
        "schema_version": "lunar_ice_bpc.guidance_validation.v1",
        "guidance_mode": mode,
        "guidance_present": hints is not None,
        "guidance_accepted": accepted is not None,
        "guidance_fallback_to_p0": accepted is None,
        "guidance_validation_issues": issues,
        "expected_binding": expected_binding.to_payload(),
        "guidance_binding_validation_sec": round(
            perf_counter() - started, 9
        ),
        "guidance_can_certify": False,
        "guidance_can_filter": False,
    }
