"""Worker-only tail dual stabilization helpers.

These helpers intentionally do not produce official bounds.  They only build a
candidate-search dual vector; every returned column must still be audited under
the current true RMP dual before it can enter the master or a certificate.
"""

from __future__ import annotations

from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals


TAIL_DUAL_STABILIZATION_DEFAULT_ENABLED = False
TAIL_DUAL_STABILIZATION_DEFAULT_ALPHA = 0.7
TAIL_DUAL_STABILIZATION_DEFAULT_WINDOW = 5


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
