"""Conservative supervised/neutral pair construction for QGR1 V2."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
import hashlib
from math import ceil, sqrt
from typing import Mapping

from lunar_ice_bpc.guidance.qgr1_supervision import (
    QGR1_FAMILIES,
    QGR1WeightedPair,
    build_qgr1_weighted_pairs,
)


QGR1_RESIDUAL_SUPERVISION_SCHEMA_V2 = (
    "lunar_ice_bpc.p0v5_qgr1_conservative_residual_supervision.v2"
)


@dataclass(frozen=True)
class QGR1NeutralPair:
    left_label_id: int
    right_label_id: int
    family: str = "neutral"
    kind: str = "same_surface_no_known_preference"
    weight: float = 0.0
    action_surface_group_size: int = 0


def build_qgr1_residual_pairs(
    replay: Mapping[str, object],
    labels: Mapping[int, Mapping[str, object]],
    *,
    seed: int,
    maximum: int = 50_000,
):
    """Return 75 percent supervised and 25 percent neutral pair mass.

    Neutral pairs are generated only inside the exact QGR1 action surface and
    never reuse a known directed or reversed supervised pair.  Candidate order
    is content-addressed, making selection independent of dictionary order.
    """

    maximum = max(4, min(50_000, int(maximum)))
    supervised_limit = max(3, min(maximum, int(ceil(maximum * 0.75))))
    supervised, metadata = build_qgr1_weighted_pairs(
        replay, labels, seed=int(seed), maximum=supervised_limit
    )
    by_id = {int(key): dict(value) for key, value in labels.items()}
    group_size = {
        label_id: size
        for values in _surface_groups(by_id).values()
        for size in (len(values),)
        for label_id in values
    }
    pressure_rows = []
    for row in supervised:
        pressure = min(8.0, sqrt(1.0 + float(group_size[row.preferred_label_id])))
        pressure_rows.append(replace(row, weight=float(row.weight) * pressure))
    supervised = _normalize_supervised(tuple(pressure_rows), total_mass=0.75)

    prohibited = {
        frozenset((int(row.preferred_label_id), int(row.other_label_id)))
        for row in supervised
    }
    neutral_candidates = []
    for action_class, values in _surface_groups(by_id).items():
        ordered = sorted(values, key=lambda label_id: _order(seed, action_class, label_id))
        if len(ordered) < 2:
            continue
        # Adjacent and half-rotation pairs give O(n) coverage without ever
        # materializing the quadratic within-bucket universe.
        offsets = (1, max(1, len(ordered) // 2))
        seen = set()
        for offset in offsets:
            for index, left in enumerate(ordered):
                right = ordered[(index + offset) % len(ordered)]
                key = frozenset((left, right))
                if left == right or key in seen or key in prohibited:
                    continue
                seen.add(key)
                neutral_candidates.append(QGR1NeutralPair(
                    left_label_id=left,
                    right_label_id=right,
                    action_surface_group_size=len(ordered),
                ))
    neutral_candidates.sort(key=lambda row: _order(
        seed, "neutral", row.left_label_id, row.right_label_id
    ))
    # The plan freezes a 75/25 *pair* split as well as a 75/25 loss-mass
    # split.  If a trace yields fewer supervised pairs than the nominal cap,
    # do not fill the remaining budget with neutral pairs: at most one neutral
    # pair is retained per three supervised pairs.
    neutral_limit = min(
        max(0, maximum - len(supervised)),
        max(0, len(supervised) // 3),
    )
    neutral = tuple(neutral_candidates[:neutral_limit])
    if neutral:
        neutral = tuple(replace(row, weight=0.25 / len(neutral)) for row in neutral)
    # When the trace has fewer neutral pairs than requested, keep the explicit
    # 75/25 loss coefficients in the trainer; never relabel a supervised pair.
    return supervised, neutral, {
        **metadata,
        "schema_version": QGR1_RESIDUAL_SUPERVISION_SCHEMA_V2,
        "supervised_pair_fraction": 0.75,
        "neutral_pair_fraction": 0.25,
        "supervised_pair_count": len(supervised),
        "neutral_pair_count": len(neutral),
        "observed_supervised_pair_fraction": (
            len(supervised) / (len(supervised) + len(neutral))
            if supervised or neutral else 0.0
        ),
        "pressure_weight": "sqrt(1+action_surface_group_size)_clipped_at_8",
        "neutral_overlap_with_supervised": 0,
        "pair_cap": maximum,
    }


def _surface_groups(labels):
    result = defaultdict(list)
    for label_id, row in labels.items():
        if row.get("visited_count") is None or row.get("reduced_cost_bucket") is None:
            raise ValueError("QGR1 V2 label trace lacks action-surface fields")
        result[(
            bool(row.get("terminal")),
            int(row["visited_count"]),
            int(row["reduced_cost_bucket"]),
        )].append(int(label_id))
    return result


def _normalize_supervised(rows, total_mass):
    by_family = defaultdict(list)
    for row in rows:
        by_family[row.family].append(row)
    active = [family for family in QGR1_FAMILIES if by_family.get(family)]
    if not active:
        raise ValueError("QGR1 V2 has no supervised family")
    result = []
    family_mass = float(total_mass) / len(active)
    for family in active:
        values = by_family[family]
        denominator = sum(max(0.0, float(row.weight)) for row in values)
        if denominator <= 0.0:
            raise ValueError("QGR1 V2 supervised family has zero mass")
        result.extend(replace(
            row, weight=family_mass * max(0.0, float(row.weight)) / denominator
        ) for row in values)
    return tuple(result)


def _order(seed, *values):
    raw = ":".join((str(int(seed)), *(str(value) for value in values)))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
