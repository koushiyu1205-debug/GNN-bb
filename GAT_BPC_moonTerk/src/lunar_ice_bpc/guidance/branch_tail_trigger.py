"""Torch-free admission policy for one tail-only branch guidance call.

The policy is intentionally deterministic and label-free.  It can inspect
only information already available after an exact node LP closes and before
the frozen P0 rank-0 branch is taken.  It never changes the legal shortlist.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


FIRST_EXACT_TOP3_ELAPSED_PER_TASK_V1 = (
    "first_exact_legal_top3_elapsed_per_task_ge_1s.v1"
)
TAIL_TRIGGER_POLICY_IDS = (FIRST_EXACT_TOP3_ELAPSED_PER_TASK_V1,)
TAIL_TRIGGER_MIN_ELAPSED_SEC_PER_TASK = 1.0


@dataclass(frozen=True)
class BranchTailTriggerDecision:
    policy_id: str
    eligible: bool
    triggered: bool
    reason: str
    event_elapsed_sec: float
    elapsed_sec_per_task: float

    def to_payload(self) -> dict[str, Any]:
        return {
            "tail_trigger_policy_id": self.policy_id,
            "tail_trigger_eligible": self.eligible,
            "tail_triggered": self.triggered,
            "tail_trigger_reason": self.reason,
            "tail_event_elapsed_sec": self.event_elapsed_sec,
            "tail_elapsed_sec_per_task": self.elapsed_sec_per_task,
            "tail_trigger_min_elapsed_sec_per_task": (
                TAIL_TRIGGER_MIN_ELAPSED_SEC_PER_TASK
            ),
        }


def _legal_exact_top3(node: dict[str, Any]) -> tuple[bool, str]:
    probe = node.get("fractional_branch_probe") or {}
    candidates = list(probe.get("candidates") or ())
    before = str(
        node.get("legal_branch_shortlist_hash_before_sort") or ""
    )
    after = str(
        node.get("legal_branch_shortlist_hash_after_sort") or ""
    )
    if str(node.get("node_status") or "") != "BRANCHED":
        return False, "NODE_NOT_BRANCHED"
    if str(node.get("pricing_state") or "") != "CERTIFIED_NO_NEGATIVE":
        return False, "NODE_PRICING_NOT_EXACT_CERTIFIED"
    if node.get("node_lp_bound_official") is not True:
        return False, "NODE_LP_BOUND_NOT_OFFICIAL"
    if len(candidates) < 3:
        return False, "LEGAL_TOP3_ABSENT"
    if not before or before != after:
        return False, "LEGAL_SHORTLIST_HASH_MISMATCH"
    if int(node.get("guidance_branch_pair_drop_count") or 0) != 0:
        return False, "GUIDANCE_PAIR_DROP_NONZERO"
    if int(node.get("guidance_filter_count") or 0) != 0:
        return False, "GUIDANCE_FILTER_NONZERO"
    if int(node.get("development_branch_selected_rank_index") or 0) != 0:
        return False, "CONTROL_DID_NOT_SELECT_P0_RANK0"
    if bool(node.get("development_branch_rank_fallback_to_p0")):
        return False, "CONTROL_REPORTED_RANK_FALLBACK"
    return True, "EXACT_LEGAL_TOP3"


def evaluate_branch_tail_trigger(
    *,
    node: dict[str, Any],
    root_wall_sec: float,
    scale: int,
    already_triggered: bool,
    policy_id: str = FIRST_EXACT_TOP3_ELAPSED_PER_TASK_V1,
) -> BranchTailTriggerDecision:
    """Evaluate the fixed one-call admission rule without importing Torch."""

    if policy_id not in TAIL_TRIGGER_POLICY_IDS:
        raise ValueError(f"unknown branch tail trigger policy {policy_id!r}")
    event_elapsed = max(0.0, float(root_wall_sec)) + max(
        0.0,
        float(node.get("tree_elapsed_sec_at_exit") or 0.0),
    )
    normalized = event_elapsed / max(1, int(scale))
    legal, reason = _legal_exact_top3(node)
    if not legal:
        return BranchTailTriggerDecision(
            policy_id,
            False,
            False,
            reason,
            event_elapsed,
            normalized,
        )
    if already_triggered:
        return BranchTailTriggerDecision(
            policy_id,
            True,
            False,
            "ONE_SHOT_ALREADY_CONSUMED",
            event_elapsed,
            normalized,
        )
    if normalized < TAIL_TRIGGER_MIN_ELAPSED_SEC_PER_TASK:
        return BranchTailTriggerDecision(
            policy_id,
            True,
            False,
            "BELOW_FIXED_TAIL_THRESHOLD",
            event_elapsed,
            normalized,
        )
    return BranchTailTriggerDecision(
        policy_id,
        True,
        True,
        "FIRST_EXACT_LEGAL_TOP3_IN_TAIL",
        event_elapsed,
        normalized,
    )


def annotate_branch_tail_events(
    *,
    nodes: Iterable[dict[str, Any]],
    root_wall_sec: float,
    scale: int,
    policy_id: str = FIRST_EXACT_TOP3_ELAPSED_PER_TASK_V1,
) -> list[dict[str, Any]]:
    """Return immutable-style annotations in processing/elapsed order."""

    rows: list[dict[str, Any]] = []
    triggered = False
    for node in nodes:
        decision = evaluate_branch_tail_trigger(
            node=node,
            root_wall_sec=root_wall_sec,
            scale=scale,
            already_triggered=triggered,
            policy_id=policy_id,
        )
        triggered = triggered or decision.triggered
        rows.append(
            {
                "node_id": str(node.get("node_id") or ""),
                "depth": int(node.get("depth") or 0),
                **decision.to_payload(),
            }
        )
    return rows
