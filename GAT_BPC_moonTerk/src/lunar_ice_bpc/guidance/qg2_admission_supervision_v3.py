"""Route-balanced, diversity-aware preference weights for QG2 V3."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import random
from typing import Mapping

from lunar_ice_bpc.guidance.qg2_admission_supervision import (
    ADMISSION_MILESTONE,
    PROOF_MILESTONE,
    QG2_QUEUE_ACTION_SURFACE_V1,
    build_admission_aware_preference_pairs,
)


QG2_V3_SUPERVISION_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_route_balanced_admission_supervision.v3"
)


@dataclass(frozen=True)
class QG2V3WeightedPair:
    preferred_label_id: int
    other_label_id: int
    kind: str
    weight: float
    selected_solution_index: int | None = None


def build_qg2_v3_weighted_pairs(
    replay: Mapping[str, object],
    labels: Mapping[int, Mapping[str, object]],
    *,
    seed: int,
    maximum: int = 50_000,
) -> tuple[tuple[QG2V3WeightedPair, ...], dict[str, object]]:
    """Build action-reachable preferences with equal mass per selected route."""

    maximum = max(1, min(50_000, int(maximum)))
    by_id = {int(key): dict(value) for key, value in labels.items()}
    milestone = str(replay.get("milestone_kind") or "")
    if milestone != ADMISSION_MILESTONE:
        base, metadata = build_admission_aware_preference_pairs(
            replay, by_id, seed=seed, maximum=maximum
        )
        kind_factor = {
            "proof_terminal_parent_progress": 1.0,
            "existing_dominator": 0.35,
            "incoming_dominator": 0.35,
        }
        raw = [
            QG2V3WeightedPair(
                int(winner), int(loser), str(kind),
                float(kind_factor.get(str(kind), 0.25)), None,
            )
            for winner, loser, kind in base
        ]
        result = _normalize_weights(raw)
        return result, {
            **metadata,
            "supervision_schema_version": QG2_V3_SUPERVISION_SCHEMA,
            "weighting_policy": "proof_progress_low_background.v1",
            "weighted_pair_count": len(result),
            "pair_weight_sum": sum(row.weight for row in result),
        }

    telemetry = dict(replay.get("proof_telemetry") or {})
    audit = dict(replay.get("diversity_milestone_audit") or {})
    if (
        audit.get("label_supervision_target_scope") != "master_admission"
        or not bool(audit.get("selected_route_mapping_complete"))
        or not bool(audit.get("selected_witness_mapping_complete"))
    ):
        raise ValueError("QG2 V3 requires complete Master-ready witness binding")
    admission_target = int(audit.get("admission_target") or 0)
    selector_rows = sorted(
        (dict(row) for row in audit.get("selected_admission_witnesses") or ()),
        key=lambda row: int(row.get("selected_rank") or 2**31),
    )
    master_ready_indices = {
        int(value)
        for value in audit.get(
            "selected_master_ready_native_solution_indices"
        ) or ()
    }
    if admission_target <= 0 or len(master_ready_indices) < admission_target:
        raise ValueError("QG2 V3 admission batch is incomplete")
    selected_rows = [
        row
        for row in selector_rows
        if row.get("native_solution_index") is not None
        and int(row["native_solution_index"]) in master_ready_indices
        and row.get("would_enter_master") is True
    ]
    if len(selected_rows) < admission_target:
        raise ValueError(
            "QG2 V3 Master-ready indices disagree with admission witnesses"
        )
    selected_rows = selected_rows[:admission_target]
    selected_indices = {
        int(row["native_solution_index"]) for row in selected_rows
    }
    if len(selected_indices) != admission_target:
        raise ValueError("QG2 V3 Master-ready admission routes are not unique")
    witnesses = {
        int(row["solution_index"]): dict(row)
        for row in telemetry.get("proof_queue_negative_witness_trace") or ()
        if row.get("solution_index") is not None
    }
    if not selected_indices.issubset(witnesses):
        raise ValueError("QG2 V3 selected route lacks an ancestor witness")

    action_class: dict[tuple[bool, int], list[int]] = defaultdict(list)
    for label_id, row in by_id.items():
        action_class[_class(row)].append(label_id)
    for values in action_class.values():
        values.sort()

    selected_ancestor_union = {
        int(label_id)
        for solution_index in selected_indices
        for label_id in witnesses[solution_index].get("ancestor_label_ids") or ()
        if int(label_id) in by_id
    }
    omitted_indices = set(witnesses) - selected_indices
    omitted_ancestors = {
        int(label_id)
        for solution_index in omitted_indices
        for label_id in witnesses[solution_index].get("ancestor_label_ids") or ()
        if int(label_id) in by_id
    } - selected_ancestor_union
    selected_membership: dict[int, int] = defaultdict(int)
    for solution_index in selected_indices:
        for label_id in set(
            int(value)
            for value in witnesses[solution_index].get("ancestor_label_ids") or ()
            if int(value) in by_id
        ):
            selected_membership[label_id] += 1

    rng = random.Random(int(seed))
    weighted: list[QG2V3WeightedPair] = []
    prior_task_sets: list[frozenset[str]] = []
    route_masses: dict[int, float] = {}
    route_pair_counts: dict[int, int] = {}
    for selected in selected_rows:
        solution_index = int(selected["native_solution_index"])
        task_set = frozenset(str(value) for value in selected.get("task_set") or ())
        if not task_set:
            raise ValueError("QG2 V3 selected route task set is empty")
        prior_union = set().union(*prior_task_sets) if prior_task_sets else set()
        new_coverage = len(task_set - prior_union) / max(1, len(task_set))
        max_jaccard = max(
            (_jaccard(task_set, previous) for previous in prior_task_sets),
            default=0.0,
        )
        bucket = str(selected.get("task_set_harvest_bucket") or "")
        bucket_factor = {
            "new_task_set": 1.25,
            "support_changing": 1.15,
            "strong_replacement": 1.0,
            "weak_replacement": 0.65,
        }.get(bucket, 0.9)
        diversity = bucket_factor * (
            0.5 + 0.25 * new_coverage + 0.25 * (1.0 - max_jaccard)
        )
        route_masses[solution_index] = max(0.1, float(diversity))
        prior_task_sets.append(task_set)

        route_pairs: list[QG2V3WeightedPair] = []
        ancestors = sorted({
            int(value)
            for value in witnesses[solution_index].get("ancestor_label_ids") or ()
            if int(value) in by_id
        })
        for winner in ancestors:
            candidates = [
                value for value in action_class.get(_class(by_id[winner]), ())
                if value in omitted_ancestors
            ]
            rng.shuffle(candidates)
            for loser in candidates[:4]:
                route_pairs.append(QG2V3WeightedPair(
                    winner, loser, "admission_selected_vs_omitted", 1.0,
                    solution_index,
                ))
            if not candidates:
                background = [
                    value for value in action_class.get(_class(by_id[winner]), ())
                    if value not in selected_ancestor_union
                    and value not in omitted_ancestors
                ]
                rng.shuffle(background)
                for loser in background[:2]:
                    route_pairs.append(QG2V3WeightedPair(
                        winner, loser, "admission_selected_vs_background", 1.0,
                        solution_index,
                    ))
        route_pairs = _deduplicate(route_pairs)
        route_pair_counts[solution_index] = len(route_pairs)
        if route_pairs:
            # Depot/root and long shared prefixes occur in many selected
            # routes but carry little information about which diverse route
            # will enter the batch.  Allocate each route equal total mass,
            # then discount a pair by the selected-route multiplicity of its
            # winner before renormalizing within that route.
            inverse_membership = [
                1.0 / max(1, selected_membership[row.preferred_label_id])
                for row in route_pairs
            ]
            inverse_total = sum(inverse_membership)
            weighted.extend(
                QG2V3WeightedPair(
                    row.preferred_label_id,
                    row.other_label_id,
                    row.kind,
                    route_masses[solution_index]
                    * inverse
                    / inverse_total,
                    row.selected_solution_index,
                )
                for row, inverse in zip(
                    route_pairs, inverse_membership, strict=True
                )
            )

    # Dominance is deliberately bounded background; it can never consume more
    # than ten percent of admission-specific supervision mass.
    background_rows: list[QG2V3WeightedPair] = []
    for row in telemetry.get("proof_queue_label_preference_trace") or ():
        winner = int(row["preferred_label_id"])
        loser = int(row["other_label_id"])
        if winner in by_id and loser in by_id and _class(by_id[winner]) == _class(by_id[loser]):
            background_rows.append(QG2V3WeightedPair(
                winner, loser, str(row.get("kind") or "dominance"), 1.0, None
            ))
        if len(background_rows) >= max(1, maximum // 10):
            break
    background_rows = _deduplicate(background_rows)
    admission_mass = sum(row.weight for row in weighted)
    if background_rows and admission_mass > 0.0:
        background_weight = 0.1 * admission_mass / len(background_rows)
        weighted.extend(
            QG2V3WeightedPair(
                row.preferred_label_id,
                row.other_label_id,
                row.kind,
                background_weight,
                None,
            )
            for row in background_rows
        )
    if not weighted:
        raise ValueError("QG2 V3 produced no action-reachable admission pairs")
    pre_cap_count = len(weighted)
    weighted = _route_stratified_cap(weighted, maximum=maximum)
    result = _normalize_weights(weighted)
    kind_counts: dict[str, int] = defaultdict(int)
    kind_mass: dict[str, float] = defaultdict(float)
    for row in result:
        kind_counts[row.kind] += 1
        kind_mass[row.kind] += row.weight
    return result, {
        "supervision_schema_version": QG2_V3_SUPERVISION_SCHEMA,
        "queue_action_surface": QG2_QUEUE_ACTION_SURFACE_V1,
        "supervision_objective": "min_time_to_master_ready_frozen_diverse_batch",
        "milestone_kind": milestone,
        "admission_target": admission_target,
        "selected_route_count": len(selected_rows),
        "selected_route_pair_counts": {
            str(key): value for key, value in sorted(route_pair_counts.items())
        },
        "selected_route_pre_normalization_mass": {
            str(key): value for key, value in sorted(route_masses.items())
        },
        "maximum_selected_ancestor_route_multiplicity": max(
            selected_membership.values(), default=0
        ),
        "weighted_pair_count": len(result),
        "pre_cap_weighted_pair_count": pre_cap_count,
        "pair_cap_policy": "route_mass_stratified_distinctive_first.v1",
        "pair_weight_sum": sum(row.weight for row in result),
        "pair_kind_counts": dict(sorted(kind_counts.items())),
        "pair_kind_weight_mass": dict(sorted(kind_mass.items())),
        "weighting_policy": "equal_route_mass_x_selector_diversity.v1",
    }


def _class(row: Mapping[str, object]) -> tuple[bool, int]:
    return bool(row.get("terminal")), int(row["reduced_cost_bucket"])


def _jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    return len(left & right) / max(1, len(left | right))


def _deduplicate(rows: list[QG2V3WeightedPair]) -> list[QG2V3WeightedPair]:
    seen: set[tuple[int, int, str, int | None]] = set()
    result: list[QG2V3WeightedPair] = []
    for row in rows:
        key = (
            row.preferred_label_id,
            row.other_label_id,
            row.kind,
            row.selected_solution_index,
        )
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result


def _normalize_weights(
    rows: list[QG2V3WeightedPair],
) -> tuple[QG2V3WeightedPair, ...]:
    total = sum(max(0.0, float(row.weight)) for row in rows)
    if total <= 0.0:
        raise ValueError("QG2 V3 supervision has zero weight")
    return tuple(
        QG2V3WeightedPair(
            row.preferred_label_id,
            row.other_label_id,
            row.kind,
            max(0.0, float(row.weight)) / total,
            row.selected_solution_index,
        )
        for row in rows
        if row.weight > 0.0
    )


def _route_stratified_cap(
    rows: list[QG2V3WeightedPair], *, maximum: int
) -> list[QG2V3WeightedPair]:
    if len(rows) <= maximum:
        return rows
    by_route: dict[int | None, list[QG2V3WeightedPair]] = defaultdict(list)
    for row in rows:
        by_route[row.selected_solution_index].append(row)
    selected_routes = sorted(key for key in by_route if key is not None)
    if maximum < len(selected_routes):
        raise ValueError(
            "QG2 V3 pair cap cannot retain every selected admission route"
        )
    quotas = {key: 1 for key in selected_routes}
    if None in by_route:
        quotas[None] = 0
    remaining = maximum - sum(quotas.values())
    group_mass = {
        key: sum(max(0.0, row.weight) for row in values)
        for key, values in by_route.items()
    }
    while remaining > 0:
        candidates = [
            key for key, values in by_route.items()
            if quotas.get(key, 0) < len(values)
        ]
        if not candidates:
            break
        # Greedily minimize quota-to-mass distortion.  Stable route ids make
        # the cap deterministic; background (None) loses ties to real routes.
        key = min(candidates, key=lambda value: (
            quotas.get(value, 0) / max(1.0e-15, group_mass[value]),
            value is None,
            -1 if value is None else int(value),
        ))
        quotas[key] = quotas.get(key, 0) + 1
        remaining -= 1

    retained = []
    for key, values in by_route.items():
        quota = quotas.get(key, 0)
        if quota <= 0:
            continue
        chosen = sorted(values, key=lambda row: (
            -float(row.weight),
            row.preferred_label_id,
            row.other_label_id,
            row.kind,
        ))[:quota]
        original_mass = group_mass[key]
        chosen_mass = sum(row.weight for row in chosen)
        scale = original_mass / max(1.0e-15, chosen_mass)
        retained.extend(QG2V3WeightedPair(
            row.preferred_label_id,
            row.other_label_id,
            row.kind,
            row.weight * scale,
            row.selected_solution_index,
        ) for row in chosen)
    return retained
