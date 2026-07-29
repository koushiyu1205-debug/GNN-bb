"""Canonical end-to-end cost semantics for branch guidance.

The P0 control pays no guidance lifecycle cost.  A deployed guidance policy
does pay that cost even when it selects rank 0.  Counterfactual runners may
have stored different per-arm emulated overheads, so labels are canonicalized
by first recovering raw tree wall time and then adding the same guidance cost
to every legal guided action.
"""

from __future__ import annotations

from math import isfinite
from typing import Any


BRANCH_GUIDED_E2E_COST_SEMANTICS_V1 = (
    "p0_control_raw_wall_vs_all_guided_actions_uniform_lifecycle_overhead.v1"
)


def canonical_guided_e2e_costs(
    *,
    arm_by_rank: dict[int, dict[str, Any]],
    guidance_lifecycle_overhead_sec: float,
) -> dict[str, Any]:
    if set(arm_by_rank) != {0, 1, 2}:
        raise ValueError("canonical branch E2E costs require ranks 0,1,2")
    overhead = float(guidance_lifecycle_overhead_sec)
    if not isfinite(overhead) or overhead < 0.0:
        raise ValueError("guidance lifecycle overhead must be finite/nonnegative")
    raw_walls = {}
    for rank in range(3):
        arm = arm_by_rank[rank]
        matched = float(arm["matched_end_to_end_wall_sec"])
        reported_overhead = float(
            arm.get("guidance_lifecycle_overhead_sec") or 0.0
        )
        raw = matched - reported_overhead
        if (
            not isfinite(matched)
            or not isfinite(reported_overhead)
            or reported_overhead < 0.0
            or not isfinite(raw)
            or raw <= 0.0
        ):
            raise ValueError("branch E2E arm wall semantics are invalid")
        raw_walls[str(rank)] = raw
    p0_control_wall = raw_walls["0"]
    guided_walls = {
        str(rank): raw_walls[str(rank)] + overhead
        for rank in range(3)
    }
    selected_rank = min(
        range(3),
        key=lambda rank: (guided_walls[str(rank)], rank),
    )
    net_gain = (
        p0_control_wall - guided_walls[str(selected_rank)]
    )
    return {
        "cost_semantics": BRANCH_GUIDED_E2E_COST_SEMANTICS_V1,
        "guidance_lifecycle_overhead_sec": overhead,
        "p0_control_wall_sec": p0_control_wall,
        "raw_action_wall_sec_by_rank": raw_walls,
        "guided_action_wall_sec_by_rank": guided_walls,
        "oracle_selected_rank_index": selected_rank,
        "oracle_net_gain_sec": net_gain,
    }


def canonical_selective_guidance_costs(
    canonical_costs: dict[str, Any],
) -> dict[str, Any]:
    """Add post-inference abstention to already-canonical guided actions.

    Abstention preserves P0's rank-0 decision but still pays the complete
    guidance lifecycle cost because the deterministic trigger has already
    admitted and executed the model.
    """

    p0_control = float(canonical_costs["p0_control_wall_sec"])
    overhead = float(
        canonical_costs["guidance_lifecycle_overhead_sec"]
    )
    guided = {
        str(rank): float(
            canonical_costs["guided_action_wall_sec_by_rank"][str(rank)]
        )
        for rank in range(3)
    }
    if (
        not isfinite(p0_control)
        or p0_control <= 0.0
        or not isfinite(overhead)
        or overhead < 0.0
    ):
        raise ValueError("selective guidance cost binding is invalid")
    action_walls = {
        "ABSTAIN_TO_P0": p0_control + overhead,
        **guided,
    }
    action_order = ("ABSTAIN_TO_P0", "0", "1", "2")
    selected = min(
        action_order,
        key=lambda action: (
            action_walls[action],
            action_order.index(action),
        ),
    )
    return {
        **canonical_costs,
        "selective_action_wall_sec": action_walls,
        "selective_oracle_action": selected,
        "selective_oracle_net_gain_sec": (
            p0_control - action_walls[selected]
        ),
        "selective_abstention_pays_lifecycle_overhead": True,
    }
