"""Admission-aware future labels for the bounded QG2 development oracle.

This module consumes future trace outcomes only while fitting QO2 or training
the learned comparators.  None of its outputs are available to the live exact
solver.  In particular, raw negative witnesses are not positive labels unless
the frozen selector chose them and the current Master view would admit them.
"""

from __future__ import annotations

import random
from collections import Counter
from typing import Mapping


ADMISSION_MILESTONE = "ADMISSION_BATCH_READY"
PROOF_MILESTONE = "EXACT_PROOF_COMPLETION"
QG2_SUPERVISION_SCHEMA_V2 = (
    "lunar_ice_bpc.p0v5_qg2_action_reachable_supervision.v2"
)
QG2_QUEUE_ACTION_SURFACE_V1 = (
    "same_terminal_class_and_reduced_cost_bucket.v1"
)


def build_admission_aware_preference_pairs(
    replay: Mapping[str, object],
    labels: Mapping[int, Mapping[str, object]],
    *,
    seed: int,
    maximum: int = 50_000,
) -> tuple[tuple[tuple[int, int, str], ...], dict[str, object]]:
    """Build same-bucket pairs aligned with time-to-admission/proof progress."""

    maximum = max(1, min(50_000, int(maximum)))
    telemetry = dict(replay.get("proof_telemetry") or {})
    by_id = {int(key): dict(value) for key, value in labels.items()}
    by_action_class: dict[tuple[bool, int], list[int]] = {}
    for label_id, row in by_id.items():
        by_action_class.setdefault(_action_class(row), []).append(label_id)
    for values in by_action_class.values():
        values.sort()

    pairs: list[tuple[int, int, str]] = []
    seen_pairs: set[tuple[int, int, str]] = set()
    rejected: Counter[str] = Counter()

    def add(winner: int, loser: int, kind: str) -> None:
        if len(pairs) >= maximum:
            rejected["pair_budget_exhausted"] += 1
            return
        if winner == loser:
            rejected["self_pair"] += 1
            return
        if winner not in by_id or loser not in by_id:
            rejected["missing_label_state"] += 1
            return
        if int(by_id[winner]["reduced_cost_bucket"]) != int(
            by_id[loser]["reduced_cost_bucket"]
        ):
            rejected["different_reduced_cost_bucket"] += 1
            return
        if bool(by_id[winner].get("terminal")) != bool(
            by_id[loser].get("terminal")
        ):
            # Native QG2 compares terminal eligibility before guidance_score.
            # A cross-class preference is therefore either tautological or
            # impossible for the learned action and must never be supervised.
            rejected["different_terminal_class"] += 1
            return
        row = (int(winner), int(loser), str(kind))
        if row in seen_pairs:
            rejected["duplicate_pair"] += 1
            return
        seen_pairs.add(row)
        pairs.append(row)

    def add_dominance_preferences() -> None:
        for row in telemetry.get("proof_queue_label_preference_trace") or ():
            add(
                int(row["preferred_label_id"]),
                int(row["other_label_id"]),
                str(row.get("kind") or "dominance"),
            )

    milestone = str(replay.get("milestone_kind") or "")
    selected_solution_indices: set[int] = set()
    omitted_negative_solution_indices: set[int] = set()
    selected_ancestor_count = 0
    hard_negative_ancestor_count = 0
    if milestone == ADMISSION_MILESTONE:
        audit = dict(replay.get("diversity_milestone_audit") or {})
        if audit.get("label_supervision_target_scope") != "master_admission":
            raise ValueError(
                "admission-aware supervision requires Master-bound snapshot v2"
            )
        if not bool(audit.get("selected_route_mapping_complete")):
            raise ValueError("selected route-to-Native mapping is incomplete")
        if not bool(audit.get("selected_witness_mapping_complete")):
            raise ValueError("selected route-to-label witness mapping is incomplete")
        selected_solution_indices = {
            int(value)
            for value in audit.get(
                "selected_master_ready_native_solution_indices"
            ) or ()
        }
        admission_target = int(audit.get("admission_target") or 0)
        if len(selected_solution_indices) < admission_target:
            raise ValueError(
                "admission milestone lacks a complete Master-ready batch"
            )
        witnesses = {
            int(row["solution_index"]): dict(row)
            for row in telemetry.get("proof_queue_negative_witness_trace") or ()
            if row.get("solution_index") is not None
        }
        if not selected_solution_indices.issubset(witnesses):
            raise ValueError("selected Master-ready route has no future witness")
        omitted_negative_solution_indices = (
            set(witnesses) - selected_solution_indices
        )
        positive_ancestors = {
            int(label_id)
            for solution_index in selected_solution_indices
            for label_id in witnesses[solution_index].get(
                "ancestor_label_ids"
            ) or ()
            if int(label_id) in by_id
        }
        hard_negative_ancestors = {
            int(label_id)
            for solution_index in omitted_negative_solution_indices
            for label_id in witnesses[solution_index].get(
                "ancestor_label_ids"
            ) or ()
            if int(label_id) in by_id
        } - positive_ancestors
        selected_ancestor_count = len(positive_ancestors)
        hard_negative_ancestor_count = len(hard_negative_ancestors)
        rng = random.Random(int(seed))
        hard_pair_count_by_winner: dict[int, int] = {}
        # Add all reachable selected-vs-omitted route pairs before weaker
        # background comparisons.  Otherwise an early selected ancestor with
        # no same-class hard negative can consume the bounded pair budget and
        # crowd a later, stronger hard-negative comparison out.
        for winner in sorted(positive_ancestors):
            action_class = _action_class(by_id[winner])
            hard = [
                value
                for value in by_action_class.get(action_class, ())
                if value in hard_negative_ancestors
            ]
            rng.shuffle(hard)
            selected_hard = hard[:8]
            hard_pair_count_by_winner[winner] = len(selected_hard)
            for loser in selected_hard:
                add(winner, loser, "admission_ancestor_vs_omitted_negative")
            if len(pairs) >= maximum:
                break
        for winner in sorted(positive_ancestors):
            if len(pairs) >= maximum:
                break
            remaining = 8 - hard_pair_count_by_winner.get(winner, 0)
            if remaining > 0:
                action_class = _action_class(by_id[winner])
                background = [
                    value
                    for value in by_action_class.get(action_class, ())
                    if value not in positive_ancestors
                    and value not in hard_negative_ancestors
                ]
                rng.shuffle(background)
                for loser in background[:remaining]:
                    add(winner, loser, "admission_ancestor")
        # Direct dominance preferences remain useful background supervision,
        # but only after the admission-specific action target has been kept.
        add_dominance_preferences()
    elif milestone == PROOF_MILESTONE:
        # The queue already has a hard terminal-first key before guidance.
        # Direct terminal-vs-nonterminal pairs are action-invariant and used to
        # crowd all useful dominance supervision out of the old 50k budget.
        # Prefer states that actually won a dominance comparison, restricted
        # to the exact action surface, then add creator parents of terminal
        # labels when the bounded trace retained that parent state.
        add_dominance_preferences()
        rng = random.Random(int(seed))
        terminal_parents = {
            int(row.get("parent_label_id"))
            for row in by_id.values()
            if bool(row.get("terminal"))
            and row.get("parent_label_id") is not None
            and int(row.get("parent_label_id")) in by_id
        }
        terminal_parent_pair_count_before = len(pairs)
        for winner in sorted(terminal_parents):
            action_class = _action_class(by_id[winner])
            background = [
                value
                for value in by_action_class.get(action_class, ())
                if value not in terminal_parents
            ]
            rng.shuffle(background)
            for loser in background[:8]:
                add(winner, loser, "proof_terminal_parent_progress")
            if len(pairs) >= maximum:
                break
        terminal_parent_pair_count = (
            len(pairs) - terminal_parent_pair_count_before
        )
    else:
        raise ValueError(
            "QG2 future supervision requires admission or proof completion"
        )

    metadata = {
        "supervision_schema_version": QG2_SUPERVISION_SCHEMA_V2,
        "queue_action_surface": QG2_QUEUE_ACTION_SURFACE_V1,
        "supervision_objective": (
            "min_time_to_master_ready_frozen_batch"
            if milestone == ADMISSION_MILESTONE
            else "min_time_to_exact_proof_completion"
        ),
        "milestone_kind": milestone,
        "selected_master_ready_solution_count": len(
            selected_solution_indices
        ),
        "omitted_raw_negative_solution_count": len(
            omitted_negative_solution_indices
        ),
        "selected_admission_ancestor_count": selected_ancestor_count,
        "hard_negative_ancestor_count": hard_negative_ancestor_count,
        "proof_terminal_parent_count": (
            len(terminal_parents)
            if milestone == PROOF_MILESTONE
            else 0
        ),
        "proof_terminal_parent_pair_count": (
            terminal_parent_pair_count
            if milestone == PROOF_MILESTONE
            else 0
        ),
        "action_reachable_pair_count": len(pairs),
        "rejected_pair_counts": dict(sorted(rejected.items())),
        "pair_kind_counts": _counts(kind for _, _, kind in pairs),
    }
    return tuple(pairs[:maximum]), metadata


def _action_class(row: Mapping[str, object]) -> tuple[bool, int]:
    """Return the two hard keys that precede QG2 guidance_score."""

    return (
        bool(row.get("terminal")),
        int(row["reduced_cost_bucket"]),
    )


def _counts(values) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[str(value)] = result.get(str(value), 0) + 1
    return dict(sorted(result.items()))
