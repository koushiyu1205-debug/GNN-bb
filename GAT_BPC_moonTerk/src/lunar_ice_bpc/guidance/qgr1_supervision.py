"""Action-aligned supervision for the QGR1 depth-residual queue policy.

QGR1 may compare learned priorities only after terminal class, visited depth,
and the frozen reduced-cost bucket have tied.  This module removes every pair
that the Native comparator cannot act on and equalizes the three supervision
families used by the label ranker.  It is training-only and has no runtime or
certificate authority.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Mapping

from lunar_ice_bpc.guidance.qg2_admission_supervision_v3 import (
    QG2V3WeightedPair,
    build_qg2_v3_weighted_pairs,
)


QGR1_ACTION_SURFACE_V1 = (
    "same_terminal_class_depth_and_reduced_cost_bucket.v1"
)
QGR1_SUPERVISION_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_qgr1_depth_residual_supervision.v1"
)
QGR1_FAMILIES = (
    "admitted_ancestor",
    "existing_dominator",
    "incoming_dominator",
)


@dataclass(frozen=True)
class QGR1WeightedPair:
    preferred_label_id: int
    other_label_id: int
    kind: str
    family: str
    weight: float
    selected_solution_index: int | None = None


def build_qgr1_weighted_pairs(
    replay: Mapping[str, object],
    labels: Mapping[int, Mapping[str, object]],
    *,
    seed: int,
    maximum: int = 50_000,
) -> tuple[tuple[QGR1WeightedPair, ...], dict[str, object]]:
    """Return only QGR1-actionable, family-balanced preference pairs."""

    maximum = max(1, min(50_000, int(maximum)))
    by_id = {int(key): dict(value) for key, value in labels.items()}
    base, base_metadata = build_qg2_v3_weighted_pairs(
        replay,
        by_id,
        seed=int(seed),
        maximum=50_000,
    )
    rejected: Counter[str] = Counter()
    grouped: dict[str, list[QG2V3WeightedPair]] = defaultdict(list)
    for row in base:
        left = by_id.get(int(row.preferred_label_id))
        right = by_id.get(int(row.other_label_id))
        if left is None or right is None:
            rejected["missing_label"] += 1
            continue
        if _action_class(left) != _action_class(right):
            rejected["outside_qgr1_action_surface"] += 1
            continue
        family = _family(str(row.kind))
        if family is None:
            rejected["unsupported_pair_kind"] += 1
            continue
        grouped[family].append(row)

    expected_routes = {
        int(value)
        for value in dict(replay.get("diversity_milestone_audit") or {}).get(
            "selected_master_ready_native_solution_indices"
        )
        or ()
    }
    retained_routes = {
        int(row.selected_solution_index)
        for row in grouped.get("admitted_ancestor", ())
        if row.selected_solution_index is not None
    }
    if expected_routes and not expected_routes.issubset(retained_routes):
        raise ValueError(
            "QGR1 supervision lacks an actionable pair for every admitted route"
        )
    if not any(grouped.values()):
        raise ValueError("QGR1 supervision produced no actionable pairs")

    # Every non-empty family receives equal total mass.  Within a family the
    # route-aware V3 weights are preserved and renormalized.
    active_families = [name for name in QGR1_FAMILIES if grouped.get(name)]
    family_mass = 1.0 / len(active_families)
    rows: list[QGR1WeightedPair] = []
    for family in active_families:
        values = grouped[family]
        total = sum(max(0.0, float(row.weight)) for row in values)
        if total <= 0.0:
            raise ValueError("QGR1 supervision family has zero mass")
        for row in values:
            rows.append(QGR1WeightedPair(
                preferred_label_id=int(row.preferred_label_id),
                other_label_id=int(row.other_label_id),
                kind=str(row.kind),
                family=family,
                weight=family_mass * max(0.0, float(row.weight)) / total,
                selected_solution_index=row.selected_solution_index,
            ))
    if len(rows) > maximum:
        rows = _family_stratified_cap(rows, maximum)
        rows = _renormalize(rows)
    retained_after_cap = {
        int(row.selected_solution_index)
        for row in rows
        if row.family == "admitted_ancestor"
        and row.selected_solution_index is not None
    }
    if expected_routes and not expected_routes.issubset(retained_after_cap):
        raise ValueError(
            "QGR1 pair cap removed an admitted route's only actionable pair"
        )
    counts = Counter(row.family for row in rows)
    masses = {
        family: sum(row.weight for row in rows if row.family == family)
        for family in active_families
    }
    return tuple(rows), {
        **base_metadata,
        "supervision_schema_version": QGR1_SUPERVISION_SCHEMA_V1,
        "queue_action_surface": QGR1_ACTION_SURFACE_V1,
        "pair_cap": maximum,
        "weighted_pair_count": len(rows),
        "pair_family_counts": dict(sorted(counts.items())),
        "pair_family_weight_mass": dict(sorted(masses.items())),
        "rejected_pair_counts": dict(sorted(rejected.items())),
        "all_admitted_routes_represented": expected_routes.issubset(
            retained_after_cap
        ),
    }


def _action_class(row: Mapping[str, object]) -> tuple[bool, int, int]:
    if row.get("visited_count") is None:
        raise ValueError("QGR1 label trace is missing visited_count")
    return (
        bool(row.get("terminal")),
        int(row["visited_count"]),
        int(row["reduced_cost_bucket"]),
    )


def _family(kind: str) -> str | None:
    if kind == "existing_dominator":
        return "existing_dominator"
    if kind == "incoming_dominator":
        return "incoming_dominator"
    if kind.startswith("admission_") or kind == "proof_terminal_parent_progress":
        return "admitted_ancestor"
    return None


def _family_stratified_cap(
    rows: list[QGR1WeightedPair], maximum: int
) -> list[QGR1WeightedPair]:
    by_family: dict[str, list[QGR1WeightedPair]] = defaultdict(list)
    for row in rows:
        by_family[row.family].append(row)
    families = [name for name in QGR1_FAMILIES if by_family.get(name)]
    if maximum < len(families):
        raise ValueError("QGR1 pair cap cannot retain every supervision family")
    ordered = {
        name: sorted(
            by_family[name],
            key=lambda row: (
                -row.weight,
                row.preferred_label_id,
                row.other_label_id,
                row.kind,
            ),
        )
        for name in families
    }
    retained: list[QGR1WeightedPair] = [ordered[name][0] for name in families]
    # Admission diversity is a hard constraint, not a soft sampler weight.
    # Reserve one actionable pair per admitted route before filling the cap.
    route_rows: dict[int, QGR1WeightedPair] = {}
    for row in ordered.get("admitted_ancestor", ()):
        if row.selected_solution_index is not None:
            route_rows.setdefault(int(row.selected_solution_index), row)
    for row in route_rows.values():
        if row not in retained:
            retained.append(row)
    if len(retained) > maximum:
        raise ValueError("QGR1 pair cap is smaller than mandatory diversity rows")
    cursors = {name: 0 for name in families}
    for name in families:
        while (
            cursors[name] < len(ordered[name])
            and ordered[name][cursors[name]] in retained
        ):
            cursors[name] += 1
    while len(retained) < maximum:
        progressed = False
        for name in families:
            if cursors[name] >= len(ordered[name]):
                continue
            retained.append(ordered[name][cursors[name]])
            cursors[name] += 1
            progressed = True
            if len(retained) == maximum:
                break
        if not progressed:
            break
    return retained


def _renormalize(rows: list[QGR1WeightedPair]) -> list[QGR1WeightedPair]:
    by_family: dict[str, list[QGR1WeightedPair]] = defaultdict(list)
    for row in rows:
        by_family[row.family].append(row)
    family_mass = 1.0 / len(by_family)
    result: list[QGR1WeightedPair] = []
    for family, values in by_family.items():
        total = sum(row.weight for row in values)
        result.extend(QGR1WeightedPair(
            row.preferred_label_id,
            row.other_label_id,
            row.kind,
            row.family,
            family_mass * row.weight / total,
            row.selected_solution_index,
        ) for row in values)
    return result
