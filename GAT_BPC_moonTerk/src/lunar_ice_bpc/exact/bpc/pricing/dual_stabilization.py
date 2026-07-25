"""Worker-only tail dual stabilization helpers.

These helpers intentionally do not produce official bounds.  They only build a
candidate-search dual vector; every returned column must still be audited under
the current true RMP dual before it can enter the master or a certificate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from math import isfinite
from typing import Mapping

from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals


TAIL_DUAL_STABILIZATION_DEFAULT_ENABLED = False
TAIL_DUAL_STABILIZATION_DEFAULT_ALPHA = 0.7
TAIL_DUAL_STABILIZATION_DEFAULT_WINDOW = 5
ORACLE_DUAL_CENTER_SCHEMA_VERSION = (
    "lunar_ice_bpc.development_oracle_dual_center.v1"
)
ORACLE_DUAL_CENTER_ALLOWED_PARTITION = "development"
ASCG_ADAPTIVE_PENALTY_RELEASE_THRESHOLD = 1.0e-2


@dataclass(frozen=True)
class DevelopmentOracleDualCenter:
    """Immutable, development-only upper-bound diagnostic target.

    This deliberately leaked center is allowed only for deciding whether
    dual-center stabilization has enough algorithmic headroom to justify
    training.  It is not a checkpoint, a deployable hint, an official dual, or
    a source of bounds/certificates.
    """

    instance_content_hash: str
    task_dual_items: tuple[tuple[str, float], ...]
    source_rmp_iteration_id: str
    source_artifact_sha256: str
    source_partition: str = ORACLE_DUAL_CENTER_ALLOWED_PARTITION
    schema_version: str = ORACLE_DUAL_CENTER_SCHEMA_VERSION
    oracle_center_id: str = field(init=False)

    def __post_init__(self) -> None:
        normalized = tuple(
            sorted(
                (str(task_id), float(value))
                for task_id, value in self.task_dual_items
            )
        )
        if len({task_id for task_id, _ in normalized}) != len(normalized):
            raise ValueError("oracle dual center contains duplicate task IDs")
        object.__setattr__(self, "task_dual_items", normalized)
        payload = {
            "schema_version": str(self.schema_version),
            "instance_content_hash": str(self.instance_content_hash),
            "task_duals": {
                task_id: _canonical_float(value)
                for task_id, value in normalized
            },
            "source_rmp_iteration_id": str(self.source_rmp_iteration_id),
            "source_artifact_sha256": str(self.source_artifact_sha256),
            "source_partition": str(self.source_partition),
        }
        object.__setattr__(
            self,
            "oracle_center_id",
            hashlib.sha256(
                json.dumps(
                    payload,
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
        )

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "DevelopmentOracleDualCenter":
        task_duals = payload.get("task_duals")
        if not isinstance(task_duals, Mapping):
            raise ValueError("oracle dual center task_duals must be a mapping")
        center = cls(
            instance_content_hash=str(
                payload.get("instance_content_hash") or ""
            ),
            task_dual_items=tuple(
                (str(task_id), float(value))
                for task_id, value in task_duals.items()
            ),
            source_rmp_iteration_id=str(
                payload.get("source_rmp_iteration_id") or ""
            ),
            source_artifact_sha256=str(
                payload.get("source_artifact_sha256") or ""
            ),
            source_partition=str(payload.get("source_partition") or ""),
            schema_version=str(payload.get("schema_version") or ""),
        )
        supplied_id = str(payload.get("oracle_center_id") or "")
        if supplied_id and supplied_id != center.oracle_center_id:
            raise ValueError("oracle dual center ID mismatch")
        return center

    @property
    def task_duals(self) -> dict[str, float]:
        return dict(self.task_dual_items)

    def validate_for(
        self,
        *,
        instance_content_hash: str,
        task_ids: tuple[str, ...] | list[str],
    ) -> None:
        if self.schema_version != ORACLE_DUAL_CENTER_SCHEMA_VERSION:
            raise ValueError("unsupported oracle dual center schema")
        if self.source_partition != ORACLE_DUAL_CENTER_ALLOWED_PARTITION:
            raise ValueError(
                "oracle dual center accepts development partition only"
            )
        if not self.instance_content_hash:
            raise ValueError("oracle dual center has no instance content hash")
        if self.instance_content_hash != str(instance_content_hash):
            raise ValueError("oracle dual center instance hash mismatch")
        expected_tasks = {str(task_id) for task_id in task_ids}
        observed_tasks = {task_id for task_id, _ in self.task_dual_items}
        if observed_tasks != expected_tasks:
            raise ValueError("oracle dual center task universe mismatch")
        if not self.source_rmp_iteration_id:
            raise ValueError("oracle dual center has no source RMP iteration")
        if len(self.source_artifact_sha256) != 64:
            raise ValueError("oracle dual center source SHA256 is invalid")
        if any(
            not isfinite(float(value))
            for _, value in self.task_dual_items
        ):
            raise ValueError("oracle dual center contains NaN/Inf")

    def to_payload(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "oracle_center_id": self.oracle_center_id,
            "instance_content_hash": self.instance_content_hash,
            "task_duals": self.task_duals,
            "source_rmp_iteration_id": self.source_rmp_iteration_id,
            "source_artifact_sha256": self.source_artifact_sha256,
            "source_partition": self.source_partition,
            "development_only": True,
            "deployable": False,
            "official_dual_source": False,
            "can_certify_no_negative": False,
        }


def adaptive_ascg_penalty_from_pricing(
    minimum_reduced_cost: float | None,
    *,
    release_threshold: float = ASCG_ADAPTIVE_PENALTY_RELEASE_THRESHOLD,
) -> tuple[float, dict]:
    """Update the development ASCG penalty from stabilized-dual pricing.

    This mirrors the adaptive rule used by the ICML 2024 ASCG reference
    implementation: for a negative pricing value ``c*``, the next penalty is
    ``c* / (c* - 1)``; a nonnegative or unavailable pricing value releases the
    stabilization.  The rule is diagnostic-only because the formula assumes
    the normalized column-cost scale used by the current Moon Trek model.

    The returned penalty can guide candidate discovery only.  It is never an
    official dual, bound, stopping condition, or certificate.
    """

    threshold = float(release_threshold)
    if not isfinite(threshold) or threshold < 0.0:
        raise ValueError(
            "ASCG adaptive release threshold must be finite and nonnegative"
        )
    if minimum_reduced_cost is None:
        return 0.0, {
            "minimum_reduced_cost": None,
            "raw_next_penalty": 0.0,
            "next_penalty": 0.0,
            "release_threshold": threshold,
            "release_reason": "pricing_value_unavailable_fail_closed",
            "can_certify_no_negative": False,
        }
    reduced_cost = float(minimum_reduced_cost)
    if not isfinite(reduced_cost):
        raise ValueError(
            "ASCG adaptive pricing value must be finite when present"
        )
    if reduced_cost >= 0.0:
        raw_penalty = 0.0
        release_reason = "stabilized_pricing_nonnegative"
    else:
        raw_penalty = reduced_cost / (reduced_cost - 1.0)
        release_reason = (
            "penalty_below_release_threshold"
            if raw_penalty < threshold
            else ""
        )
    next_penalty = (
        0.0 if raw_penalty < threshold else min(1.0, raw_penalty)
    )
    return round(float(next_penalty), 12), {
        "minimum_reduced_cost": reduced_cost,
        "raw_next_penalty": round(float(raw_penalty), 12),
        "next_penalty": round(float(next_penalty), 12),
        "release_threshold": threshold,
        "release_reason": release_reason,
        "can_certify_no_negative": False,
    }


def build_tail_dual_center(
    dual_history: tuple[JourneyDuals, ...] | list[JourneyDuals],
    *,
    window: int = TAIL_DUAL_STABILIZATION_DEFAULT_WINDOW,
) -> dict[str, float]:
    """Return a moving average over recent task-cover duals."""

    recent = tuple(dual_history)[-max(1, int(window)) :]
    task_ids = sorted({str(task_id) for duals in recent for task_id in duals.cover})
    if not recent:
        return {}
    center: dict[str, float] = {}
    for task_id in task_ids:
        values = [float(duals.cover.get(task_id, 0.0)) for duals in recent]
        center[task_id] = sum(values) / len(values)
    return center


def build_worker_duals_with_tail_center(
    current_duals: JourneyDuals,
    *,
    tail_dual_center: dict[str, float] | None = None,
    enabled: bool = TAIL_DUAL_STABILIZATION_DEFAULT_ENABLED,
    alpha: float = TAIL_DUAL_STABILIZATION_DEFAULT_ALPHA,
    window: int = TAIL_DUAL_STABILIZATION_DEFAULT_WINDOW,
) -> tuple[JourneyDuals, dict]:
    """Blend task-cover duals for candidate search while preserving proof safety."""

    if not enabled:
        return current_duals, _payload(
            enabled=False,
            alpha=alpha,
            window=window,
            center_size=0,
            current_size=len(current_duals.cover),
        )
    center = tail_dual_center or {}
    bounded_alpha = max(0.0, min(1.0, float(alpha)))
    task_ids = sorted({str(task_id) for task_id in current_duals.cover} | {str(task_id) for task_id in center})
    blended_cover = {
        task_id: bounded_alpha * float(current_duals.cover.get(task_id, 0.0))
        + (1.0 - bounded_alpha) * float(center.get(task_id, current_duals.cover.get(task_id, 0.0)))
        for task_id in task_ids
    }
    worker_duals = JourneyDuals(
        cover=blended_cover,
        fleet_limit=current_duals.fleet_limit,
        cuts=current_duals.cuts,
    )
    return worker_duals, _payload(
        enabled=True,
        alpha=bounded_alpha,
        window=window,
        center_size=len(center),
        current_size=len(current_duals.cover),
    )


def build_worker_duals_with_development_oracle_center(
    current_duals: JourneyDuals,
    oracle_center: DevelopmentOracleDualCenter,
    *,
    round_index: int,
    initial_true_dual_weight: float = 0.15,
    release_round: int = 8,
) -> tuple[JourneyDuals, dict]:
    """Blend toward a leaked optimal center, then deterministically release it.

    ``alpha`` is the current true-dual weight.  It increases monotonically to
    one, so the oracle influence becomes exactly zero at ``release_round``.
    The returned vector remains worker-only even before release.
    """

    alpha = adaptive_true_dual_weight(
        round_index=round_index,
        initial_true_dual_weight=initial_true_dual_weight,
        release_round=release_round,
    )
    worker_duals, payload = build_worker_duals_with_tail_center(
        current_duals,
        tail_dual_center=oracle_center.task_duals,
        enabled=alpha < 1.0,
        alpha=alpha,
        window=1,
    )
    payload.update(
        {
            "schema_version": (
                "lunar_ice_bpc.development_oracle_dual_stabilization.v1"
            ),
            "tail_dual_center_source": "development_final_true_dual_oracle",
            "oracle_center_id": oracle_center.oracle_center_id,
            "oracle_source_partition": oracle_center.source_partition,
            "oracle_source_rmp_iteration_id": (
                oracle_center.source_rmp_iteration_id
            ),
            "oracle_source_artifact_sha256": (
                oracle_center.source_artifact_sha256
            ),
            "oracle_development_only": True,
            "oracle_deployable": False,
            "oracle_round_index": int(round_index),
            "oracle_initial_true_dual_weight": round(
                max(0.0, min(1.0, float(initial_true_dual_weight))),
                9,
            ),
            "oracle_release_round": max(1, int(release_round)),
            "oracle_influence": round(1.0 - float(alpha), 9),
            "oracle_release_complete": bool(alpha >= 1.0),
            "worker_dual_source": (
                "development_oracle_stabilized_worker_dual"
                if alpha < 1.0
                else "current_true_rmp_dual"
            ),
            "official_dual_source": "current_true_rmp_dual",
            "worker_dual_only": True,
            "requires_true_dual_rc_recompute": True,
            "can_certify_no_negative": False,
            "official_bound_safe": False,
        }
    )
    return worker_duals, payload


def adaptive_true_dual_weight(
    *,
    round_index: int,
    initial_true_dual_weight: float = 0.15,
    release_round: int = 8,
) -> float:
    """Return a monotone schedule from the initial weight to exact release."""

    initial = max(0.0, min(1.0, float(initial_true_dual_weight)))
    release = max(1, int(release_round))
    current_round = max(1, int(round_index))
    if release <= 1 or current_round >= release:
        return 1.0
    progress = float(current_round - 1) / float(release - 1)
    return round(initial + (1.0 - initial) * progress, 9)


def _payload(
    *,
    enabled: bool,
    alpha: float,
    window: int,
    center_size: int,
    current_size: int,
) -> dict:
    worker_dual_source = "tail_dual_stabilized_worker_dual" if enabled else "current_true_rmp_dual"
    return {
        "schema_version": "lunar_ice_bpc.b4_1_tail_dual_stabilization.v1",
        "tail_dual_stabilization_enabled": bool(enabled),
        "tail_dual_stabilization_alpha": round(float(alpha), 9),
        "tail_dual_stabilization_window": int(window),
        "tail_dual_center_task_count": int(center_size),
        "tail_dual_current_task_count": int(current_size),
        "worker_dual_source": worker_dual_source,
        "official_dual_source": "current_true_rmp_dual",
        "worker_dual_only": True,
        "requires_true_dual_rc_recompute": True,
        "true_dual_rc_recomputed": True,
        "tail_dual_no_column_can_certify": False,
        "can_certify_no_negative": False,
        "official_bound_safe": False,
    }


def _canonical_float(value: float) -> float:
    numeric = float(value)
    if not isfinite(numeric):
        raise ValueError("oracle dual center contains NaN/Inf")
    return 0.0 if numeric == 0.0 else round(numeric, 12)
