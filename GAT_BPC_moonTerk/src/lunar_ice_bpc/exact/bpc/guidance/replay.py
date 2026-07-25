"""Versioned pricing snapshots and pure ordering replay.

Snapshots capture a frozen RMP/pricing context so deterministic, linear, MLP,
and GAT rankings can be compared without rerunning the whole B&B tree.  Replay
never claims a pricing certificate; it only audits ordering and preserves the
recorded exact/censored outcome.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from lunar_ice_bpc.exact.bpc.guidance.contracts import (
    CanonicalSolveBindingV2,
    canonical_universe_hash,
    reorder_preserving_universe,
)
from lunar_ice_bpc.exact.core.cuts import (
    pricing_cut_context_from_duals,
    stable_payload_hash,
)


PRICING_SNAPSHOT_SCHEMA_V1 = "lunar_ice_bpc.gat_pricing_snapshot.v1"
PRICING_REPLAY_SCHEMA_V1 = "lunar_ice_bpc.gat_pricing_replay.v1"


@dataclass(frozen=True)
class PricingSnapshotV1:
    binding: CanonicalSolveBindingV2
    instance_content_hash: str
    rmp_primal: tuple[dict[str, Any], ...]
    true_duals: dict[str, Any]
    branch_context: dict[str, Any]
    full_cut_context: dict[str, Any]
    projected_pricing_cut_context: dict[str, Any]
    pricing_mode: str
    objective_mode: str
    memory_limit_gb: float
    wall_time_budget_sec: float | None
    queue_policy_id: str
    candidate_rows: tuple[dict[str, Any], ...]
    p0_ordering: tuple[str, ...]
    result_summary: dict[str, Any]
    censored: bool
    censor_reason: str
    schema_version: str = PRICING_SNAPSHOT_SCHEMA_V1

    @property
    def legal_universe_hash(self) -> str:
        return canonical_universe_hash(
            self.p0_ordering,
            universe_kind="pricing_candidate",
        )

    @property
    def snapshot_hash(self) -> str:
        return stable_payload_hash(self.to_payload(include_snapshot_hash=False))

    def to_payload(self, *, include_snapshot_hash: bool = True) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "binding": self.binding.to_payload(),
            "instance_content_hash": self.instance_content_hash,
            "rmp_primal": [_plain(row) for row in self.rmp_primal],
            "true_duals": _plain(self.true_duals),
            "branch_context": _plain(self.branch_context),
            "full_cut_context": _plain(self.full_cut_context),
            "projected_pricing_cut_context": _plain(
                self.projected_pricing_cut_context
            ),
            "pricing_mode": self.pricing_mode,
            "objective_mode": self.objective_mode,
            "memory_limit_gb": self.memory_limit_gb,
            "wall_time_budget_sec": self.wall_time_budget_sec,
            "queue_policy_id": self.queue_policy_id,
            "candidate_rows": [_plain(row) for row in self.candidate_rows],
            "p0_ordering": list(self.p0_ordering),
            "legal_action_universe_hash_before_sort": self.legal_universe_hash,
            "result_summary": _plain(self.result_summary),
            "censored": self.censored,
            "censor_reason": self.censor_reason,
            "can_certify": False,
            "mutates_solver": False,
        }
        if include_snapshot_hash:
            payload["snapshot_hash"] = self.snapshot_hash
        return payload

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "PricingSnapshotV1":
        if str(payload.get("schema_version")) != PRICING_SNAPSHOT_SCHEMA_V1:
            raise ValueError("pricing snapshot schema version mismatch")
        binding_payload = dict(payload["binding"])
        recorded_binding_hash = str(binding_payload.pop("binding_hash", ""))
        binding = CanonicalSolveBindingV2(**binding_payload)
        if recorded_binding_hash and binding.binding_hash != recorded_binding_hash:
            raise ValueError("pricing snapshot binding hash mismatch")
        snapshot = cls(
            binding=binding,
            instance_content_hash=str(payload["instance_content_hash"]),
            rmp_primal=tuple(
                dict(row) for row in payload.get("rmp_primal", ())
            ),
            true_duals=dict(payload.get("true_duals") or {}),
            branch_context=dict(payload.get("branch_context") or {}),
            full_cut_context=dict(payload.get("full_cut_context") or {}),
            projected_pricing_cut_context=dict(
                payload.get("projected_pricing_cut_context") or {}
            ),
            pricing_mode=str(payload["pricing_mode"]),
            objective_mode=str(payload["objective_mode"]),
            memory_limit_gb=float(payload.get("memory_limit_gb") or 0.0),
            wall_time_budget_sec=(
                None
                if payload.get("wall_time_budget_sec") is None
                else float(payload["wall_time_budget_sec"])
            ),
            queue_policy_id=str(payload.get("queue_policy_id") or "Q0"),
            candidate_rows=tuple(
                dict(row) for row in payload.get("candidate_rows", ())
            ),
            p0_ordering=tuple(
                str(value) for value in payload.get("p0_ordering", ())
            ),
            result_summary=dict(payload.get("result_summary") or {}),
            censored=bool(payload.get("censored")),
            censor_reason=str(payload.get("censor_reason") or ""),
        )
        if tuple(
            str(row.get("candidate_id") or f"candidate_{index}")
            for index, row in enumerate(snapshot.candidate_rows)
        ) != snapshot.p0_ordering:
            raise ValueError("pricing snapshot P0 ordering does not match candidates")
        recorded_universe = str(
            payload.get("legal_action_universe_hash_before_sort") or ""
        )
        if recorded_universe and recorded_universe != snapshot.legal_universe_hash:
            raise ValueError("pricing snapshot legal universe hash mismatch")
        recorded_snapshot_hash = str(payload.get("snapshot_hash") or "")
        if recorded_snapshot_hash and recorded_snapshot_hash != snapshot.snapshot_hash:
            raise ValueError("pricing snapshot content hash mismatch")
        return snapshot


def build_pricing_snapshot(
    request: Any,
    *,
    candidates: Iterable[Mapping[str, Any]],
    rmp_primal: Iterable[Mapping[str, Any]] = tuple(),
    result: Any | None = None,
    queue_policy_id: str | None = None,
    engine_hash: str = "",
    feature_schema_version: str = "",
    normalization_version: str = "",
    checkpoint_id: str = "",
    ood_policy_version: str = "",
) -> PricingSnapshotV1:
    candidate_rows = tuple(dict(row) for row in candidates)
    candidate_ids = tuple(
        str(row.get("candidate_id") or f"candidate_{index}")
        for index, row in enumerate(candidate_rows)
    )
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("snapshot candidate ids must be unique")
    binding = CanonicalSolveBindingV2.from_backend_request(
        request,
        engine_hash=engine_hash,
        feature_schema_version=feature_schema_version,
        normalization_version=normalization_version,
        checkpoint_id=checkpoint_id,
        ood_policy_version=ood_policy_version,
    )
    projected = pricing_cut_context_from_duals(
        request.cut_context,
        request.true_duals.cuts,
        enabled=bool(request.cut_dual_projection_enabled),
    )
    summary = _result_summary(result, request=request)
    censored = bool(
        result is not None
        and (
            not bool(getattr(result, "search_exhaustive", False))
            or not bool(getattr(result, "frontier_empty", False))
            or bool(getattr(result, "labels_dropped", False))
        )
    )
    return PricingSnapshotV1(
        binding=binding,
        instance_content_hash=str(request.data.instance_content_hash),
        rmp_primal=tuple(dict(row) for row in rmp_primal),
        true_duals={
            "cover": dict(request.true_duals.cover),
            "fleet_limit": float(request.true_duals.fleet_limit),
            "cuts": dict(request.true_duals.cuts or {}),
        },
        branch_context=request.branch_context.to_payload(),
        full_cut_context=request.cut_context.to_payload(),
        projected_pricing_cut_context=projected.to_payload(),
        pricing_mode=str(request.mode),
        objective_mode=str(request.objective_mode),
        memory_limit_gb=float(request.memory_limit_gb),
        wall_time_budget_sec=(
            None
            if request.wall_time_limit_sec is None
            else float(request.wall_time_limit_sec)
        ),
        queue_policy_id=str(
            queue_policy_id
            if queue_policy_id is not None
            else getattr(request, "proof_queue_policy_id", "Q0")
        ),
        candidate_rows=candidate_rows,
        p0_ordering=candidate_ids,
        result_summary=summary,
        censored=censored,
        censor_reason=_censor_reason(result) if censored else "",
    )


def replay_pricing_ordering(
    snapshot: PricingSnapshotV1,
    *,
    priorities: Mapping[str, float],
    expected_binding_hash: str | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    if (
        expected_binding_hash is not None
        and str(expected_binding_hash) != snapshot.binding.binding_hash
    ):
        return {
            "schema_version": PRICING_REPLAY_SCHEMA_V1,
            "status": "BINDING_MISMATCH",
            "binding_match": False,
            "mutates_solver": False,
            "can_certify": False,
        }
    ordered, audit = reorder_preserving_universe(
        snapshot.candidate_rows,
        priorities=priorities,
        candidate_id_key="candidate_id",
        universe_kind="pricing_candidate",
        enabled=enabled,
    )
    replay_ids = [
        str(row.get("candidate_id") or f"candidate_{index}")
        for index, row in enumerate(ordered)
    ]
    return {
        "schema_version": PRICING_REPLAY_SCHEMA_V1,
        "status": "REPLAY_READY",
        "binding_match": True,
        "snapshot_hash": snapshot.snapshot_hash,
        "binding_hash": snapshot.binding.binding_hash,
        "p0_ordering": list(snapshot.p0_ordering),
        "replay_ordering": replay_ids,
        "ordering_changed": replay_ids != list(snapshot.p0_ordering),
        "ordering_audit": audit,
        "recorded_result_summary": _plain(snapshot.result_summary),
        "censored": snapshot.censored,
        "censor_reason": snapshot.censor_reason,
        "result_semantics_changed": False,
        "mutates_solver": False,
        "can_certify": False,
    }


def save_pricing_snapshot(
    snapshot: PricingSnapshotV1, path: str | Path
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            snapshot.to_payload(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def load_pricing_snapshot(path: str | Path) -> PricingSnapshotV1:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return PricingSnapshotV1.from_payload(payload)


def _result_summary(
    result: Any | None,
    *,
    request: Any | None = None,
) -> dict[str, Any]:
    if result is None:
        return {
            "status": "NOT_OBSERVED",
            "search_exhaustive": False,
            "frontier_empty": False,
            "labels_dropped": False,
        }
    result_telemetry = dict(
        getattr(result, "telemetry", None) or {}
    )
    observed_columns = []
    if request is not None:
        from lunar_ice_bpc.exact.bpc.guidance.contracts import (
            canonical_arc_candidate_id,
        )
        from lunar_ice_bpc.exact.master.journey_rmp import (
            manual_journey_reduced_cost,
            manual_phase_one_journey_reduced_cost,
        )

        for column in tuple(getattr(result, "columns", tuple()) or tuple()):
            if str(getattr(request, "objective_mode", "official")) == "phase_one":
                true_rc = manual_phase_one_journey_reduced_cost(
                    column, request.true_duals
                )
            else:
                true_rc = manual_journey_reduced_cost(
                    column, request.true_duals
                )
            observed_columns.append(
                {
                    "task_ids": sorted(
                        str(value) for value in column.task_set
                    ),
                    "arc_candidate_ids": [
                        canonical_arc_candidate_id(
                            leg.source, leg.target, leg.path_type
                        )
                        for sortie in column.sorties
                        for leg in sortie.legs
                    ],
                    "true_reduced_cost": float(true_rc),
                }
            )
    return {
        "status": str(getattr(result, "engine_status", "")),
        "best_found_rc": getattr(result, "best_found_rc", None),
        "global_min_rc": getattr(result, "global_min_rc", None),
        "global_min_rc_is_exact": bool(
            getattr(result, "global_min_rc_is_exact", False)
        ),
        "proved_no_rc_below": getattr(result, "proved_no_rc_below", None),
        "search_exhaustive": bool(getattr(result, "search_exhaustive", False)),
        "frontier_empty": bool(getattr(result, "frontier_empty", False)),
        "labels_dropped": bool(getattr(result, "labels_dropped", False)),
        "certificate_blockers": list(
            getattr(result, "certificate_blockers", tuple())
        ),
        "observed_column_count": len(observed_columns),
        "observed_columns": observed_columns,
        "best_reduced_cost_event_schema": result_telemetry.get(
            "best_reduced_cost_event_schema"
        ),
        "best_reduced_cost_event_trace_valid": bool(
            result_telemetry.get(
                "best_reduced_cost_event_trace_valid"
            )
        ),
        "best_reduced_cost_event_trace_usable_for_training": bool(
            result_telemetry.get(
                "best_reduced_cost_event_trace_usable_for_training"
            )
        ),
        "best_reduced_cost_events": list(
            result_telemetry.get(
                "best_reduced_cost_events_audited"
            )
            or ()
        ),
        "proof_configuration": (
            {}
            if request is None
            else {
                "completion_bound_enabled": bool(
                    request.completion_bound_enabled
                ),
                "subset_dominance_enabled": bool(
                    request.subset_dominance_enabled
                ),
                "proof_queue_policy_id": str(
                    request.proof_queue_policy_id
                ),
                "negative_eps": float(request.negative_eps),
                "dominance_eps": float(request.dominance_eps),
                "resource_eps": float(request.resource_eps),
                "harvest_target": int(request.harvest_target),
            }
        ),
        "proof_telemetry": {
            key: result_telemetry.get(key)
            for key in (
                "extended_labels",
                "dominated_labels",
                "dominance_candidate_checks",
                "max_visited_bucket_size",
                "solution_count",
                "completion_bound_evaluated_labels",
                "completion_bound_pruned_labels",
                "subset_dominance_rejected_labels",
                "extension_wall_time_seconds",
                "dominance_wall_time_seconds",
                "wall_time_seconds",
                "memory_pressure_triggered",
                "host_timed_out",
                "host_memory_killed",
                "request_payload_bytes",
                "response_payload_bytes",
            )
        },
    }


def _censor_reason(result: Any | None) -> str:
    if result is None:
        return "not_observed"
    blockers = tuple(getattr(result, "certificate_blockers", tuple()) or tuple())
    if blockers:
        return ",".join(str(item) for item in blockers)
    return str(getattr(result, "engine_status", "incomplete")).lower()


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_plain(item) for item in value)
    return value
