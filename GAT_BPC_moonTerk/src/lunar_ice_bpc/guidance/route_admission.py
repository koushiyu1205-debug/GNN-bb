"""Leakage-safe supervision for route-admission ordering.

The intervention is the batch that the current P0 harvest policy admits, not
an artificial single-column extension.  Candidate contest sets are used only
to decide which boundary swaps to measure; they never redefine or filter the
legal addable universe.

This module deliberately has no torch dependency.
"""

from __future__ import annotations

from math import isfinite
from typing import Any, Mapping, Sequence

from lunar_ice_bpc.exact.bpc.guidance.contracts import (
    canonical_universe_hash,
)
from lunar_ice_bpc.exact.core.cuts import stable_payload_hash


ROUTE_ADMISSION_SNAPSHOT_SCHEMA_V1 = (
    "lunar_ice_bpc.route_admission_snapshot.v1"
)
ROUTE_ADMISSION_ACTION_SCHEMA_V1 = (
    "lunar_ice_bpc.route_admission_boundary_swap_action.v1"
)
ROUTE_ADMISSION_LOOKAHEAD_SCHEMA_V1 = (
    "lunar_ice_bpc.route_admission_lookahead.v1"
)
ROUTE_ADMISSION_TARGET_SCHEMA_V1 = (
    "lunar_ice_bpc.route_admission_pairwise_target.v1"
)
ROUTE_ADMISSION_OBJECTIVE_SPEC_V1 = (
    "next_rmp_objective.within_context.raw_difference.v1"
)
ROUTE_ADMISSION_LEXICOGRAPHIC_OBJECTIVE_SPEC_V2 = (
    "next_rmp_then_deferred_negative_count_mass_best_rc."
    "within_context.lexicographic.v2"
)
P0_KEEP_BATCH_ACTION_ID = "P0_KEEP_BATCH"


def build_route_admission_snapshot(
    *,
    canonical_solve_binding: Mapping[str, Any],
    instance_content_hash: str,
    scale: int,
    node_id: str,
    candidate_rows: Sequence[Mapping[str, Any]],
    p0_ordered_candidate_ids: Sequence[str],
    p0_selected_candidate_ids: Sequence[str],
    selection_limit: int,
    active_column_payloads: Sequence[Mapping[str, Any]],
    branch_context: Mapping[str, Any],
    full_cut_context: Mapping[str, Any],
    source_phase: str,
    executed_objective_spec_id: str,
    live_cut_policy_hash: str = "",
    separator_policy_version: str = "",
) -> dict[str, Any]:
    """Build an immutable, replayable snapshot for a real P0 batch boundary."""

    normalized_candidates = [
        {
            **dict(row),
            "candidate_id": str(row["candidate_id"]),
            "true_reduced_cost": float(row["true_reduced_cost"]),
            "task_set": sorted(str(value) for value in row["task_set"]),
            "column_payload": dict(row["column_payload"]),
        }
        for row in candidate_rows
    ]
    candidate_ids = tuple(
        str(row["candidate_id"]) for row in normalized_candidates
    )
    ordered_ids = tuple(str(value) for value in p0_ordered_candidate_ids)
    selected_ids = tuple(str(value) for value in p0_selected_candidate_ids)
    limit = int(selection_limit)
    if limit <= 0:
        raise ValueError("route-admission selection limit must be positive")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("route-admission candidate ids must be unique")
    if set(ordered_ids) != set(candidate_ids) or len(ordered_ids) != len(
        candidate_ids
    ):
        raise ValueError("P0 ordering must cover the exact legal universe")
    if selected_ids != ordered_ids[: min(limit, len(ordered_ids))]:
        raise ValueError("P0 selected batch must be the P0 ordering prefix")
    if len(candidate_ids) <= limit:
        raise ValueError(
            "route-admission snapshot is only valid at an active boundary"
        )
    binding = dict(canonical_solve_binding)
    if str(binding.get("instance_hash") or "") != str(instance_content_hash):
        raise ValueError("binding/route-admission instance hash mismatch")
    universe_hash = canonical_universe_hash(
        candidate_ids,
        universe_kind="addable_harvest",
    )
    payload = {
        "schema_version": ROUTE_ADMISSION_SNAPSHOT_SCHEMA_V1,
        "route_admission_objective_spec_id": (
            ROUTE_ADMISSION_OBJECTIVE_SPEC_V1
        ),
        "executed_objective_spec_id": str(executed_objective_spec_id),
        "canonical_solve_binding": binding,
        "binding_hash": str(binding.get("binding_hash") or ""),
        "instance_content_hash": str(instance_content_hash),
        "scale": int(scale),
        "node_id": str(node_id),
        "source_phase": str(source_phase),
        "legal_action_universe_hash_before_sort": universe_hash,
        "legal_candidate_ids": list(candidate_ids),
        "p0_ordered_candidate_ids": list(ordered_ids),
        "p0_selected_candidate_ids": list(selected_ids),
        "selection_limit": limit,
        "candidate_rows": normalized_candidates,
        "active_column_payloads": [
            dict(value) for value in active_column_payloads
        ],
        "branch_context": dict(branch_context),
        "full_cut_context": dict(full_cut_context),
        "live_cut_policy_hash": str(live_cut_policy_hash),
        "separator_policy_version": str(separator_policy_version),
        "guidance_filter_count": 0,
        "guidance_arc_drop_count": 0,
        "guidance_label_drop_count": 0,
        "guidance_branch_pair_drop_count": 0,
        "mutates_solver": False,
        "can_certify": False,
        "outcome_status": "UNMEASURED",
    }
    payload["snapshot_hash"] = stable_payload_hash(payload)
    return validate_route_admission_snapshot(payload)


def validate_route_admission_snapshot(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate identity, completeness, and no-filter invariants."""

    row = dict(payload)
    if (
        str(row.get("schema_version") or "")
        != ROUTE_ADMISSION_SNAPSHOT_SCHEMA_V1
    ):
        raise ValueError("route-admission snapshot schema mismatch")
    if (
        str(row.get("route_admission_objective_spec_id") or "")
        != ROUTE_ADMISSION_OBJECTIVE_SPEC_V1
    ):
        raise ValueError("route-admission objective spec mismatch")
    expected_hash = stable_payload_hash(
        {key: value for key, value in row.items() if key != "snapshot_hash"}
    )
    if str(row.get("snapshot_hash") or "") != expected_hash:
        raise ValueError("route-admission snapshot hash mismatch")
    if any(
        int(row.get(key) or 0) != 0
        for key in (
            "guidance_filter_count",
            "guidance_arc_drop_count",
            "guidance_label_drop_count",
            "guidance_branch_pair_drop_count",
        )
    ):
        raise ValueError("route-admission snapshot contains guidance filtering")
    candidate_ids = tuple(
        str(value) for value in row.get("legal_candidate_ids", ())
    )
    if len(candidate_ids) < 2 or len(candidate_ids) != len(
        set(candidate_ids)
    ):
        raise ValueError("route-admission legal universe is invalid")
    candidate_rows = tuple(row.get("candidate_rows", ()))
    row_ids = tuple(str(value.get("candidate_id")) for value in candidate_rows)
    if set(row_ids) != set(candidate_ids) or len(row_ids) != len(candidate_ids):
        raise ValueError("route-admission candidate payload coverage mismatch")
    if any(not value.get("column_payload") for value in candidate_rows):
        raise ValueError("route-admission candidate column payload is missing")
    expected_universe = canonical_universe_hash(
        candidate_ids,
        universe_kind="addable_harvest",
    )
    if (
        str(row.get("legal_action_universe_hash_before_sort") or "")
        != expected_universe
    ):
        raise ValueError("route-admission legal universe hash mismatch")
    ordered = tuple(
        str(value) for value in row.get("p0_ordered_candidate_ids", ())
    )
    if set(ordered) != set(candidate_ids) or len(ordered) != len(candidate_ids):
        raise ValueError("route-admission P0 ordering coverage mismatch")
    limit = int(row.get("selection_limit") or 0)
    selected = tuple(
        str(value) for value in row.get("p0_selected_candidate_ids", ())
    )
    if limit <= 0 or len(candidate_ids) <= limit:
        raise ValueError("route-admission snapshot has no active boundary")
    if selected != ordered[:limit]:
        raise ValueError("route-admission P0 batch is not the ordering prefix")
    binding = dict(row.get("canonical_solve_binding") or {})
    if str(binding.get("binding_hash") or "") != str(
        row.get("binding_hash") or ""
    ):
        raise ValueError("route-admission binding hash mismatch")
    if str(binding.get("instance_hash") or "") != str(
        row.get("instance_content_hash") or ""
    ):
        raise ValueError("route-admission binding instance mismatch")
    if not row.get("active_column_payloads"):
        raise ValueError("route-admission active RMP payload is missing")
    return row


def build_boundary_swap_actions(
    snapshot: Mapping[str, Any],
    *,
    selected_boundary_width: int = 4,
    omitted_contest_cap: int = 8,
    max_swap_actions: int = 24,
) -> dict[str, Any]:
    """Freeze a bounded measurement contest without changing legal actions."""

    row = validate_route_admission_snapshot(snapshot)
    ordered = tuple(str(value) for value in row["p0_ordered_candidate_ids"])
    selected = tuple(str(value) for value in row["p0_selected_candidate_ids"])
    omitted = ordered[len(selected) :]
    boundary = selected[-max(1, int(selected_boundary_width)) :]
    contest_omitted = _evenly_spaced(
        omitted,
        max(1, int(omitted_contest_cap)),
    )
    actions = [
        {
            "schema_version": ROUTE_ADMISSION_ACTION_SCHEMA_V1,
            "action_id": P0_KEEP_BATCH_ACTION_ID,
            "intervention_kind": "control_keep_p0_batch",
            "swap_out_candidate_id": None,
            "swap_in_candidate_id": None,
            "admitted_candidate_ids": list(selected),
        }
    ]
    action_cap = max(0, int(max_swap_actions))
    for swap_in in contest_omitted:
        for swap_out in reversed(boundary):
            if len(actions) - 1 >= action_cap:
                break
            admitted = list(selected)
            admitted[admitted.index(swap_out)] = swap_in
            action_core = {
                "snapshot_hash": row["snapshot_hash"],
                "swap_out_candidate_id": swap_out,
                "swap_in_candidate_id": swap_in,
                "admitted_candidate_ids": admitted,
            }
            actions.append(
                {
                    "schema_version": ROUTE_ADMISSION_ACTION_SCHEMA_V1,
                    "action_id": "SWAP_" + stable_payload_hash(action_core),
                    "intervention_kind": "boundary_swap",
                    "swap_out_candidate_id": swap_out,
                    "swap_in_candidate_id": swap_in,
                    "admitted_candidate_ids": admitted,
                }
            )
        if len(actions) - 1 >= action_cap:
            break
    return {
        "schema_version": ROUTE_ADMISSION_ACTION_SCHEMA_V1,
        "snapshot_hash": row["snapshot_hash"],
        "route_admission_objective_spec_id": (
            ROUTE_ADMISSION_OBJECTIVE_SPEC_V1
        ),
        "legal_action_universe_hash_before_sort": row[
            "legal_action_universe_hash_before_sort"
        ],
        "legal_candidate_count": len(ordered),
        "p0_batch_size": len(selected),
        "omitted_candidate_count": len(omitted),
        "measurement_contest_candidate_ids": list(
            dict.fromkeys((*boundary, *contest_omitted))
        ),
        "measurement_contest_is_legal_universe": False,
        "deferred_candidate_ids": [
            value
            for value in ordered
            if value not in set(selected)
        ],
        "guidance_filter_count": 0,
        "permanent_drop_count": 0,
        "actions": actions,
    }


def materialize_next_rmp_pairwise_targets(
    snapshot: Mapping[str, Any],
    measurements: Sequence[Mapping[str, Any]],
    *,
    practical_improvement: float = 1.0e-9,
) -> dict[str, Any]:
    """Create within-context lexicographic batch-action labels.

    Missing, failed, or censored arms stay masked.  No fixed censoring penalty
    and no cross-context normalization are applied.  RMP objective is the
    first key.  When it ties, the fixed candidate pool is compared by remaining
    negative count, negative mass, then best (most negative) RC.  The keys are
    never collapsed with arbitrary coefficients.
    """

    row = validate_route_admission_snapshot(snapshot)
    by_action: dict[str, list[float]] = {}
    pressure_by_action: dict[str, list[tuple[int, float, float | None]]] = {}
    censored: dict[str, int] = {}
    action_metadata: dict[str, tuple[str | None, str | None]] = {}
    for measurement in measurements:
        if str(measurement.get("snapshot_hash") or "") != str(
            row["snapshot_hash"]
        ):
            raise ValueError("lookahead measurement snapshot mismatch")
        if (
            str(measurement.get("objective_spec_id") or "")
            != ROUTE_ADMISSION_LEXICOGRAPHIC_OBJECTIVE_SPEC_V2
        ):
            raise ValueError("lookahead measurement objective mismatch")
        action_id = str(measurement.get("action_id") or "")
        metadata = (
            (
                None
                if measurement.get("swap_out_candidate_id") is None
                else str(measurement["swap_out_candidate_id"])
            ),
            (
                None
                if measurement.get("swap_in_candidate_id") is None
                else str(measurement["swap_in_candidate_id"])
            ),
        )
        previous_metadata = action_metadata.setdefault(action_id, metadata)
        if previous_metadata != metadata:
            raise ValueError(
                "lookahead action metadata differs across replicates"
            )
        value = measurement.get("next_rmp_objective")
        complete = (
            str(measurement.get("status") or "") == "RMP_OPTIMAL"
            and value is not None
            and isfinite(float(value))
            and not bool(measurement.get("censored"))
        )
        if complete:
            by_action.setdefault(action_id, []).append(float(value))
            negative_count = int(
                measurement["deferred_negative_count"]
            )
            negative_mass = float(
                measurement["deferred_negative_mass"]
            )
            best_rc_raw = measurement.get("deferred_best_true_rc")
            best_rc = (
                None if best_rc_raw is None else float(best_rc_raw)
            )
            if (
                negative_count < 0
                or not isfinite(negative_mass)
                or negative_mass < 0.0
                or (best_rc is not None and not isfinite(best_rc))
            ):
                raise ValueError(
                    "lookahead deferred pressure metric is invalid"
                )
            pressure_by_action.setdefault(action_id, []).append(
                (negative_count, negative_mass, best_rc)
            )
        else:
            censored[action_id] = censored.get(action_id, 0) + 1
    control_values = by_action.get(P0_KEEP_BATCH_ACTION_ID, [])
    control_mean = (
        None
        if not control_values
        else sum(control_values) / len(control_values)
    )
    control_pressure = _mean_pressure(
        pressure_by_action.get(P0_KEEP_BATCH_ACTION_ID, [])
    )
    targets = []
    if control_mean is not None:
        for action_id, values in sorted(by_action.items()):
            if action_id == P0_KEEP_BATCH_ACTION_ID or not values:
                continue
            action_mean = sum(values) / len(values)
            action_pressure = _mean_pressure(
                pressure_by_action.get(action_id, [])
            )
            if action_pressure is None or control_pressure is None:
                continue
            advantage = control_mean - action_mean
            pairwise_label, decisive_key = _lexicographic_pairwise_label(
                control_objective=control_mean,
                action_objective=action_mean,
                control_pressure=control_pressure,
                action_pressure=action_pressure,
                tolerance=abs(float(practical_improvement)),
            )
            targets.append(
                {
                    "action_id": action_id,
                    "control_action_id": P0_KEEP_BATCH_ACTION_ID,
                    "swap_out_candidate_id": action_metadata.get(
                        action_id, (None, None)
                    )[0],
                    "swap_in_candidate_id": action_metadata.get(
                        action_id, (None, None)
                    )[1],
                    "raw_next_rmp_objective_advantage": advantage,
                    "deferred_negative_count_reduction": (
                        control_pressure[0] - action_pressure[0]
                    ),
                    "deferred_negative_mass_reduction": (
                        control_pressure[1] - action_pressure[1]
                    ),
                    "deferred_best_true_rc_improvement": (
                        None
                        if control_pressure[2] is None
                        or action_pressure[2] is None
                        else action_pressure[2] - control_pressure[2]
                    ),
                    "pairwise_label": pairwise_label,
                    "decisive_lexicographic_key": decisive_key,
                    "control_replicate_count": len(control_values),
                    "action_replicate_count": len(values),
                    "censored_replicate_count": censored.get(action_id, 0),
                    "target_mask": True,
                }
            )
    return {
        "schema_version": ROUTE_ADMISSION_TARGET_SCHEMA_V1,
        "snapshot_hash": row["snapshot_hash"],
        "objective_spec_id": (
            ROUTE_ADMISSION_LEXICOGRAPHIC_OBJECTIVE_SPEC_V2
        ),
        "objective_direction": "minimize",
        "target_definition": (
            "lexicographic(next_rmp_objective,"
            "deferred_negative_count,deferred_negative_mass,"
            "-deferred_best_true_rc)"
        ),
        "objective_keys_mixed_into_scalar": False,
        "cross_context_normalization_applied": False,
        "legacy_four_coefficient_cost_used": False,
        "fixed_censoring_penalty_used": False,
        "control_available": control_mean is not None,
        "targets": targets,
        "unlabelled_action_ids": sorted(
            action_id
            for action_id in censored
            if action_id not in by_action
        ),
        # Local lookahead labels are training signal, not a deployment gate.
        "linear_training_authorized": False,
        "linear_training_prerequisite": (
            "matched_end_to_end_perfect_policy_net_gain_lcb_above_zero"
        ),
    }


def _evenly_spaced(values: Sequence[str], limit: int) -> tuple[str, ...]:
    sequence = tuple(str(value) for value in values)
    if len(sequence) <= limit:
        return sequence
    if limit <= 1:
        return (sequence[0],)
    indices = {
        round(index * (len(sequence) - 1) / (limit - 1))
        for index in range(limit)
    }
    return tuple(sequence[index] for index in sorted(indices))


def _mean_pressure(
    values: Sequence[tuple[int, float, float | None]],
) -> tuple[float, float, float | None] | None:
    if not values:
        return None
    best_values = [value[2] for value in values if value[2] is not None]
    return (
        sum(value[0] for value in values) / len(values),
        sum(value[1] for value in values) / len(values),
        (
            None
            if len(best_values) != len(values)
            else sum(float(value) for value in best_values)
            / len(best_values)
        ),
    )


def _lexicographic_pairwise_label(
    *,
    control_objective: float,
    action_objective: float,
    control_pressure: tuple[float, float, float | None],
    action_pressure: tuple[float, float, float | None],
    tolerance: float,
) -> tuple[int, str]:
    comparisons = (
        (
            control_objective - action_objective,
            "next_rmp_objective",
        ),
        (
            control_pressure[0] - action_pressure[0],
            "deferred_negative_count",
        ),
        (
            control_pressure[1] - action_pressure[1],
            "deferred_negative_mass",
        ),
    )
    for improvement, key in comparisons:
        if improvement > tolerance:
            return 1, key
        if improvement < -tolerance:
            return -1, key
    control_best = control_pressure[2]
    action_best = action_pressure[2]
    if control_best is not None and action_best is not None:
        # Less negative is better, so action - control is the improvement.
        improvement = action_best - control_best
        if improvement > tolerance:
            return 1, "deferred_best_true_rc"
        if improvement < -tolerance:
            return -1, "deferred_best_true_rc"
    return 0, "tie"
