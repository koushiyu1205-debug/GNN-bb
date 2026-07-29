#!/usr/bin/env python3
"""Collect bounded, matched child trajectories for a frozen P0 top-3 state.

This is a development-only, multi-fidelity label collector.  It never changes
the online branch universe or solver policy.  Every candidate reuses the same
persisted root column pool and the exact parent branch/cut context, then probes
both Ryan-Foster children under explicit wall-time budgets.

The training target is deliberately expressed in seconds:

    pair work = SAME child wall time + DIFFERENT child wall time

Incomplete probes are right-censored.  No normalized legacy four-coefficient
cost and no fixed timeout penalty is produced.  Full end-to-end one-deviation
oracles remain a separate sparse gold label.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from run_p0_no_task_wait_v3_branch_state_oracle import (  # noqa: E402
    BASELINE_ID,
    PROFILE_BY_SCALE,
    _candidate_id,
    _configure_environment,
    _development_hashes,
    _json_safe_top_level,
    _load_json,
    _node_lp_exact_safe,
    _path_hash,
    _root_exact_safe,
    _sha256_json,
    _solver_binding,
    _write_json,
)
from lunar_ice_bpc.domain.scenario import SERVICE_TIMING_POLICY_ID  # noqa: E402
from lunar_ice_bpc.exact.bpc.cuts.live_sri import LiveSriPolicy  # noqa: E402
from lunar_ice_bpc.exact.bpc.solver.live_sri_solver import (  # noqa: E402
    solve_node_pricing_with_live_sri,
)
from lunar_ice_bpc.exact.bpc.core.column_signature import (  # noqa: E402
    column_signature_from_journey,
)
from lunar_ice_bpc.exact.bpc.guidance.contracts import (  # noqa: E402
    canonical_universe_hash,
)
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (  # noqa: E402
    RELAXED_LABELING_WORKER,
)
from lunar_ice_bpc.exact.core.branching import (  # noqa: E402
    BranchContext,
    branch_context_from_payload,
)
from lunar_ice_bpc.exact.core.cuts import (  # noqa: E402
    CutContext,
    CutDefinition,
    CutLineage,
    CutLineageEntry,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.core.journey import (  # noqa: E402
    journey_column_from_solution_payload,
)
from lunar_ice_bpc.exact.solver.branch_probe import (  # noqa: E402
    build_fractional_branch_probe,
)
from lunar_ice_bpc.runners.b4_1_true_dual_proof_tail import (  # noqa: E402
    _diagnostic_b0_placeholder,
)
from lunar_ice_bpc.guidance.branch_counterfactual_snapshot import (  # noqa: E402
    deep_target_node_exact_safe,
)


SCHEMA_VERSION = (
    "lunar_ice_bpc.no_task_wait_v3_branch_child_trajectory.v2"
)
PAIR_COST_SEMANTICS = "same_child_wall_sec_plus_different_child_wall_sec"
PAIR_TARGET_KIND = "right_censored_wall_time_listwise"
PROBE_SUMMARY_SEMANTICS_VERSION = (
    "b2b_r3_official_node_certificate_gates_v1"
)


def _cut_context_from_payload(payload: dict | None) -> CutContext:
    rows = list((payload or {}).get("cuts") or ())
    context = CutContext(
        tuple(
            CutDefinition(
                cut_id=str(row["cut_id"]),
                cut_type=str(row["cut_type"]),
                tasks=tuple(str(value) for value in row.get("tasks") or ()),
                divisor=int(row.get("divisor") or 2),
                rhs=float(row.get("rhs") or 0.0),
            )
            for row in rows
        )
    )
    expected_count = int((payload or {}).get("cut_count") or len(rows))
    if len(context.cuts) != expected_count:
        raise ValueError("cut context count mismatch")
    return context


def _cut_lineage_from_payload(payload: dict | None) -> CutLineage:
    rows = list((payload or {}).get("entries") or ())
    lineage = CutLineage(
        entries=tuple(
            CutLineageEntry(
                cut_id=str(row["cut_id"]),
                scope=str(row["scope"]),
                origin_node_id=str(row["origin_node_id"]),
                ancestor_path=tuple(
                    str(value) for value in row.get("ancestor_path") or ()
                ),
                policy_version=str(
                    row.get("policy_version") or "native_live_sri_bpc_v1"
                ),
            )
            for row in rows
        ),
        policy_version=str(
            (payload or {}).get("policy_version")
            or "native_live_sri_bpc_v1"
        ),
    )
    expected_count = int((payload or {}).get("entry_count") or len(rows))
    if len(lineage.entries) != expected_count:
        raise ValueError("cut lineage count mismatch")
    return lineage


def _extend_branch_context(
    parent_payload: dict | None,
    child_payload: dict | None,
) -> BranchContext:
    parent = branch_context_from_payload(parent_payload)
    child = branch_context_from_payload(child_payload)
    return BranchContext(
        tuple(parent.pair_decisions) + tuple(child.pair_decisions)
    )


def _actionable_state_rows(control: dict) -> list[dict]:
    rows: list[dict] = []
    for node in control.get("nodes") or ():
        probe = node.get("fractional_branch_probe") or {}
        candidates = list(probe.get("candidates") or ())
        before = node.get("legal_branch_shortlist_hash_before_sort")
        after = node.get("legal_branch_shortlist_hash_after_sort")
        if (
            (
                node.get("node_status") != "BRANCHED"
                and not bool(
                    node.get(
                        "opportunity_parent_snapshot_eligible"
                    )
                )
            )
            or not (
                _node_lp_exact_safe(node)
                or _node_probe_exact_safe(node)
            )
            or len(candidates) < 3
            or before != after
            or int(node.get("guidance_branch_pair_drop_count") or 0) != 0
            or int(node.get("development_branch_selected_rank_index") or 0)
            != 0
        ):
            continue
        path = tuple(
            str(value)
            for value in node.get("development_branch_path_signature") or ()
        )
        rows.append(
            {
                "node_id": str(node["node_id"]),
                "depth": int(node.get("depth") or 0),
                "path_signature": list(path),
                "path_hash": _path_hash(path),
                "parent_branch_context": node.get("branch_context") or {},
                "node_lp_bound": node.get("node_lp_bound"),
                "cut_context": node.get("cut_context") or {},
                "cut_lineage": node.get("cut_lineage") or {},
                "active_cut_context_hash": str(
                    node.get("active_cut_context_hash") or ""
                ),
                "cut_lineage_hash": str(
                    node.get("cut_lineage_hash") or ""
                ),
                "legal_branch_shortlist_hash_before_sort": before,
                "legal_branch_shortlist_hash_after_sort": after,
                "guidance_branch_pair_drop_count": 0,
                "candidates": candidates[:3],
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            int(row["depth"]),
            str(row["path_hash"]),
            str(row["node_id"]),
        ),
    )


def _bind_exact_opportunity_control(
    control: dict,
    opportunity: dict | None,
) -> tuple[dict, bool]:
    """Expose an exact root parent state from an intentionally truncated tree."""

    if (
        str(control.get("algorithm_status") or "") == "BPC_OPTIMAL"
        and int(control.get("incomplete_node_count") or 0) == 0
    ):
        return control, False
    if not opportunity:
        return control, False
    original_hash = _sha256_json(control)
    if (
        str(opportunity.get("opportunity_status") or "")
        != "EXACT_ACTIONABLE_ROOT"
        or not bool(opportunity.get("p0_root_node_exact_safe"))
        or int(opportunity.get("candidate_count") or 0) < 3
        or str(opportunity.get("tree_result_sha256") or "")
        != original_hash
    ):
        return control, False
    nodes = list(control.get("nodes") or ())
    if len(nodes) != 1 or not (
        _node_lp_exact_safe(nodes[0])
        or _node_probe_exact_safe(nodes[0])
    ):
        raise ValueError(
            "exact opportunity report does not bind one exact root node"
        )
    before = str(
        opportunity.get(
            "legal_branch_shortlist_hash_before_sort"
        )
        or ""
    )
    after = str(
        opportunity.get(
            "legal_branch_shortlist_hash_after_sort"
        )
        or ""
    )
    if not before or before != after:
        raise ValueError("exact opportunity universe hash mismatch")
    root = {
        **nodes[0],
        "development_branch_path_signature": [],
        "development_branch_requested_rank_index": 0,
        "development_branch_selected_rank_index": 0,
        "development_branch_rank_fallback_to_p0": False,
        "legal_branch_shortlist_hash_before_sort": before,
        "legal_branch_shortlist_hash_after_sort": after,
        "guidance_branch_pair_drop_count": 0,
        "opportunity_parent_snapshot_eligible": True,
    }
    return {**control, "nodes": [root]}, True


def _finite_nonnegative(value: object, *, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    if not math.isfinite(result) or result < 0.0:
        return float(default)
    return result


def _compact_history(payload: dict) -> list[dict]:
    allowed = (
        "round",
        "rmp_status",
        "node_lp_bound",
        "pricing_state",
        "added_column_count",
        "addable_negative_count",
        "duplicate_negative_count",
        "hidden_negative_count",
        "final_judge_status",
        "final_judge_wall_time",
        "labeling_final_judge_harvest_pass_wall_time",
        "labeling_final_judge_proof_pass_wall_time",
    )
    result = []
    for row in payload.get("history") or ():
        compact = {
            key: row.get(key)
            for key in allowed
            if key in row
        }
        if compact:
            result.append(compact)
    return result


def _node_probe_exact_safe(payload: dict) -> bool:
    ledger = payload.get("certificate_ledger") or {}
    return bool(
        payload.get("node_status") == "NODE_LP_CERTIFIED"
        and payload.get("certificate_scope") == "BPC_NODE_LP_CERTIFIED"
        and payload.get("pricing_state") == "CERTIFIED_NO_NEGATIVE"
        and payload.get("node_lp_bound_official")
        and payload.get("uses_true_dual_bpc_certificate")
        and ledger.get("valid")
        and payload.get("manual_rc_audit_pass")
        and payload.get("pricing_rc_audit_pass")
        and payload.get("final_judge_certifying_proof_kind")
        and payload.get("branch_pricing_audit_pass")
        and payload.get("cut_pricing_audit_pass")
    )


def _node_probe_summary(
    *,
    payload: dict,
    wall_sec: float,
    budget_sec: float,
    rank_index: int,
    branch_sense: str,
    candidate_id: str,
) -> dict:
    exact = _node_probe_exact_safe(payload)
    observed = min(
        max(0.0, float(wall_sec)),
        max(0.0, float(budget_sec)),
    )
    return {
        "probe_summary_semantics_version": (
            PROBE_SUMMARY_SEMANTICS_VERSION
        ),
        "candidate_id": str(candidate_id),
        "rank_index": int(rank_index),
        "branch_sense": str(branch_sense),
        "budget_sec": round(float(budget_sec), 6),
        "observed_wall_sec": round(observed, 6),
        "event_observed": exact,
        "right_censored": not exact,
        "node_lp_exact_safe": exact,
        "node_status": payload.get("node_status"),
        "pricing_state": payload.get("pricing_state"),
        "certificate_scope": payload.get("certificate_scope"),
        "node_lp_bound": payload.get("node_lp_bound"),
        "round_count": int(payload.get("pricing_round_count") or 0),
        "added_column_count": int(payload.get("added_column_count") or 0),
        "branch_filtered_column_count": int(
            payload.get("branch_filtered_column_count") or 0
        ),
        "node_lp_bound_official": bool(
            payload.get("node_lp_bound_official")
        ),
        "manual_rc_audit_pass": bool(
            payload.get("manual_rc_audit_pass")
        ),
        "pricing_rc_audit_pass": bool(
            payload.get("pricing_rc_audit_pass")
        ),
        "final_judge_certifying_proof_kind": bool(
            payload.get("final_judge_certifying_proof_kind")
        ),
        "branch_pricing_audit_pass": bool(
            payload.get("branch_pricing_audit_pass")
        ),
        "cut_pricing_audit_pass": bool(
            payload.get("cut_pricing_audit_pass")
        ),
        "active_cut_context_hash": str(
            payload.get("active_cut_context_hash") or ""
        ),
        "cut_lineage_hash": str(payload.get("cut_lineage_hash") or ""),
        "history": _compact_history(payload),
        "raw_result_sha256": _sha256_json(
            {
                key: value
                for key, value in payload.items()
                if not str(key).startswith("_")
            }
        ),
    }


def _not_run_child_summary(
    *,
    rank_index: int,
    branch_sense: str,
    candidate_id: str,
    reason: str,
) -> dict:
    return {
        "probe_summary_semantics_version": (
            PROBE_SUMMARY_SEMANTICS_VERSION
        ),
        "candidate_id": str(candidate_id),
        "rank_index": int(rank_index),
        "branch_sense": str(branch_sense),
        "budget_sec": 0.0,
        "observed_wall_sec": 0.0,
        "event_observed": False,
        "right_censored": True,
        "node_lp_exact_safe": False,
        "node_status": "NOT_RUN",
        "pricing_state": "NOT_RUN",
        "certificate_scope": "NONE",
        "node_lp_bound": None,
        "round_count": 0,
        "added_column_count": 0,
        "branch_filtered_column_count": 0,
        "node_lp_bound_official": False,
        "manual_rc_audit_pass": False,
        "pricing_rc_audit_pass": False,
        "final_judge_certifying_proof_kind": False,
        "branch_pricing_audit_pass": False,
        "cut_pricing_audit_pass": False,
        "active_cut_context_hash": "",
        "cut_lineage_hash": "",
        "history": [],
        "raw_result_sha256": None,
        "not_run_reason": str(reason),
    }


def _pair_summary(
    *,
    rank_index: int,
    candidate_id: str,
    children: list[dict],
    lifecycle_overhead_sec: float,
) -> dict:
    observed_child_work = sum(
        _finite_nonnegative(row.get("observed_wall_sec"))
        for row in children
    )
    both_run = len(children) == 2 and all(
        row.get("node_status") != "NOT_RUN" for row in children
    )
    both_exact = both_run and all(
        bool(row.get("event_observed")) for row in children
    )
    overhead = (
        0.0
        if int(rank_index) == 0
        else _finite_nonnegative(lifecycle_overhead_sec)
    )
    lower_bound = observed_child_work + overhead
    return {
        "candidate_id": str(candidate_id),
        "rank_index": int(rank_index),
        "children": children,
        "both_children_run": both_run,
        "both_children_exact": both_exact,
        "right_censored": not both_exact,
        "pair_observed_work_lower_bound_sec": round(lower_bound, 6),
        "pair_exact_work_sec": (
            round(lower_bound, 6) if both_exact else None
        ),
        "guidance_lifecycle_overhead_sec": round(overhead, 6),
        "pair_cost_semantics": PAIR_COST_SEMANTICS,
        "target_kind": PAIR_TARGET_KIND,
        "legacy_normalized_cost_present": False,
        "fixed_timeout_penalty_present": False,
    }


def _strict_preference(
    left: dict,
    right: dict,
    *,
    margin_sec: float,
) -> dict | None:
    """Return a sound observed-time preference, or None when censored/unclear."""

    margin = max(0.0, float(margin_sec))
    left_exact = left.get("pair_exact_work_sec")
    right_exact = right.get("pair_exact_work_sec")
    left_lb = float(left["pair_observed_work_lower_bound_sec"])
    right_lb = float(right["pair_observed_work_lower_bound_sec"])
    if left_exact is not None and right_exact is not None:
        difference = float(right_exact) - float(left_exact)
        if abs(difference) <= margin:
            return None
        winner, loser = (
            (left, right) if difference > 0.0 else (right, left)
        )
        evidence = "BOTH_EXACT_PAIR_WORK"
    elif left_exact is not None and right_lb > float(left_exact) + margin:
        winner, loser = left, right
        evidence = "EXACT_BEATS_CENSORED_LOWER_BOUND"
    elif right_exact is not None and left_lb > float(right_exact) + margin:
        winner, loser = right, left
        evidence = "EXACT_BEATS_CENSORED_LOWER_BOUND"
    else:
        return None
    return {
        "winner_rank_index": int(winner["rank_index"]),
        "loser_rank_index": int(loser["rank_index"]),
        "winner_candidate_id": str(winner["candidate_id"]),
        "loser_candidate_id": str(loser["candidate_id"]),
        "evidence": evidence,
        "margin_sec": round(margin, 6),
    }


def _preference_rows(
    pairs: list[dict],
    *,
    margin_sec: float,
) -> list[dict]:
    rows = []
    for left_index, left in enumerate(pairs):
        for right in pairs[left_index + 1 :]:
            preference = _strict_preference(
                left,
                right,
                margin_sec=margin_sec,
            )
            if preference is not None:
                rows.append(preference)
    return rows


def _survival_training_rows(
    *,
    instance_content_hash: str,
    scale: int,
    path_hash: str,
    pairs: list[dict],
) -> list[dict]:
    group_id = (
        f"{str(instance_content_hash)}:"
        f"{str(path_hash)}"
    )
    rows = []
    for pair in pairs:
        for child in pair.get("children") or ():
            observed = _finite_nonnegative(
                child.get("observed_wall_sec")
            )
            event = bool(child.get("event_observed"))
            rows.append(
                {
                    "survival_group_id": group_id,
                    "instance_content_hash": str(
                        instance_content_hash
                    ),
                    "scale": int(scale),
                    "path_hash": str(path_hash),
                    "candidate_id": str(pair["candidate_id"]),
                    "rank_index": int(pair["rank_index"]),
                    "branch_sense": str(child["branch_sense"]),
                    "observed_time_sec": round(observed, 6),
                    "event_observed": event,
                    "event_time_sec": (
                        round(observed, 6) if event else None
                    ),
                    "censoring_time_sec": (
                        None if event else round(observed, 6)
                    ),
                    "loss_semantics": (
                        "event:negative_log_density;"
                        "censored:negative_log_survival"
                    ),
                    "strong_pairwise_label": False,
                    "unexplored_candidate_negative": False,
                }
            )
    return rows


def _diagnostic_lower_bound_order(
    pairs: list[dict],
) -> list[int]:
    """Return a diagnostic order that is never a strong censored label."""

    return [
        int(row["rank_index"])
        for row in sorted(
            pairs,
            key=lambda row: (
                float(row["pair_observed_work_lower_bound_sec"]),
                int(row["rank_index"]),
            ),
        )
    ]


def _replay_pair_at_horizon(
    pair: dict,
    *,
    horizon_sec: float,
) -> dict | None:
    horizon = max(0.0, float(horizon_sec))
    if horizon <= 0.0:
        return None
    replayed_children = []
    for child in pair.get("children") or ():
        observed = _finite_nonnegative(
            child.get("observed_wall_sec")
        )
        event = bool(child.get("event_observed"))
        if not event and observed + 1.0e-9 < horizon:
            return None
        event_before_horizon = bool(event and observed <= horizon)
        replayed_children.append(
            {
                **child,
                "budget_sec": round(horizon, 6),
                "observed_wall_sec": round(
                    observed if event_before_horizon else horizon,
                    6,
                ),
                "event_observed": event_before_horizon,
                "right_censored": not event_before_horizon,
                "node_lp_exact_safe": event_before_horizon,
                "horizon_replayed": True,
            }
        )
    return _pair_summary(
        rank_index=int(pair["rank_index"]),
        candidate_id=str(pair["candidate_id"]),
        children=replayed_children,
        lifecycle_overhead_sec=float(
            pair.get("guidance_lifecycle_overhead_sec") or 0.0
        ),
    )


def _diagnostic_horizon_replays(
    pairs: list[dict],
    *,
    gold_label: dict | None,
    horizons_sec: tuple[float, ...] = (15.0, 30.0, 60.0, 90.0),
) -> list[dict]:
    rows = []
    for horizon in horizons_sec:
        replayed = [
            _replay_pair_at_horizon(pair, horizon_sec=horizon)
            for pair in pairs
        ]
        if any(pair is None for pair in replayed):
            continue
        valid_pairs = [pair for pair in replayed if pair is not None]
        order = _diagnostic_lower_bound_order(valid_pairs)
        rows.append(
            {
                "horizon_sec": float(horizon),
                "pair_lower_bound_sec_by_rank": {
                    str(pair["rank_index"]): pair[
                        "pair_observed_work_lower_bound_sec"
                    ]
                    for pair in valid_pairs
                },
                "diagnostic_pair_lower_bound_order": order,
                "event_count": sum(
                    int(child.get("event_observed") is True)
                    for pair in valid_pairs
                    for child in pair.get("children") or ()
                ),
                "censored_count": sum(
                    int(child.get("event_observed") is not True)
                    for pair in valid_pairs
                    for child in pair.get("children") or ()
                ),
                "diagnostic_proxy_top1_matches_gold": (
                    None
                    if gold_label is None
                    else int(order[0])
                    == int(
                        gold_label["oracle_selected_rank_index"]
                    )
                ),
                "is_training_label": False,
            }
        )
    return rows


def _race_budget(
    *,
    base_budget_sec: float,
    p0_exact_pair_work_sec: float | None,
    accumulated_alt_work_sec: float,
    lifecycle_overhead_sec: float,
    margin_sec: float,
) -> float:
    base = max(0.0, float(base_budget_sec))
    if p0_exact_pair_work_sec is None:
        return base
    remaining_to_possible_win = (
        float(p0_exact_pair_work_sec)
        + max(0.0, float(margin_sec))
        - max(0.0, float(accumulated_alt_work_sec))
        - max(0.0, float(lifecycle_overhead_sec))
    )
    return min(base, max(0.0, remaining_to_possible_win))


def _gold_label_for_state(
    gold_report: dict | None,
    *,
    path_hash: str,
    candidate_ids: list[str],
) -> dict | None:
    if not gold_report:
        return None
    matches = [
        row
        for row in gold_report.get("state_reports") or ()
        if str(row.get("path_hash") or "") == str(path_hash)
    ]
    if len(matches) != 1:
        return None
    row = matches[0]
    if (
        str(gold_report.get("schema_version") or "")
        != "lunar_ice_bpc.no_task_wait_v3_branch_state_oracle.v2"
        or not bool(row.get("complete_matched_e2e_gold"))
        or list(row.get("top3_candidate_ids") or ())
        != list(candidate_ids)
        or int(row.get("eligible_alternative_count") or 0) != 2
        or any(
            not bool(
                arm.get(
                    "counterfactual_universe_matches_control"
                )
            )
            for arm in row.get("arms") or ()
        )
    ):
        return None
    control_wall = float(
        (gold_report.get("control") or {}).get(
            "matched_end_to_end_wall_sec"
        )
        or 0.0
    )
    wall_by_rank = {"0": control_wall}
    for arm in row.get("arms") or ():
        rank = int(arm.get("requested_rank_index") or -1)
        if rank in {1, 2} and bool(arm.get("exact_safe")):
            wall_by_rank[str(rank)] = float(
                arm["matched_end_to_end_wall_sec"]
            )
    return {
        "schema_version": str(gold_report.get("schema_version") or ""),
        "oracle_selected_rank_index": row.get(
            "oracle_selected_rank_index"
        ),
        "oracle_net_gain_sec": row.get("oracle_net_gain_sec"),
        "oracle_net_gain_ratio": row.get("oracle_net_gain_ratio"),
        "matched_end_to_end_wall_sec_by_rank": wall_by_rank,
        "source_report_sha256": _sha256_json(gold_report),
    }


def _probe_child(
    *,
    data,
    profile: dict,
    initial_columns: tuple,
    branch_context: BranchContext,
    cut_context: CutContext,
    cut_lineage: CutLineage,
    depth: int,
    ancestor_path: tuple[str, ...],
    node_id: str,
    incumbent_objective: float | None,
    budget_sec: float,
    max_rounds: int,
    max_columns_per_round: int,
) -> tuple[dict, float]:
    started = perf_counter()
    payload = solve_node_pricing_with_live_sri(
        data,
        policy=LiveSriPolicy.named("P0"),
        depth=int(depth),
        branch_context=branch_context,
        cut_context=cut_context,
        cut_lineage=cut_lineage,
        node_id=str(node_id),
        ancestor_path=ancestor_path,
        initial_columns=initial_columns,
        incumbent_objective=incumbent_objective,
        max_direct_tasks=len(data.task_ids),
        max_rounds=int(max_rounds),
        wall_time_limit_sec=float(budget_sec),
        max_columns_per_round=int(max_columns_per_round),
        b0_direct=_diagnostic_b0_placeholder(data),
        tail_dual_stabilization_enabled=True,
        tail_dual_stabilization_alpha=0.7,
        tail_dual_stabilization_window=5,
        worker_pricer_kind=RELAXED_LABELING_WORKER,
        labeling_final_judge_enabled=True,
        labeling_final_judge_max_exact_tasks=len(data.task_ids),
        labeling_final_judge_exact_harvest_target=int(
            profile["root_harvest_target"]
        ),
    )
    return payload, perf_counter() - started


def _latest_true_dual_context(payload: dict) -> dict:
    for history in reversed(list(payload.get("history") or ())):
        context = history.get("dual_context")
        if (
            isinstance(context, dict)
            and str(context.get("dual_source") or "")
            == "master.reduced_cost_context"
        ):
            return context
    raise ValueError("reconstructed parent has no true-RMP dual context")


def _node_primal_columns(payload: dict) -> tuple[dict, ...]:
    """Read primal rows from the live master before it is JSON-stripped."""

    master = payload.get("_master")
    if (
        master is not None
        and getattr(master, "rmp", None) is not None
    ):
        return tuple(master.rmp.primal_columns)
    return tuple(payload.get("primal_columns") or ())


def _reconstruct_parent_state(
    *,
    data,
    profile: dict,
    initial_columns: tuple,
    state: dict,
    branch_context: BranchContext,
    cut_context: CutContext,
    cut_lineage: CutLineage,
    budget_sec: float,
    max_rounds: int,
    max_columns_per_round: int,
    mismatch_diagnostic_path: Path | None = None,
    accept_fresh_reconstructed_shortlist: bool = False,
) -> tuple[dict, tuple, dict]:
    started = perf_counter()
    payload = solve_node_pricing_with_live_sri(
        data,
        policy=LiveSriPolicy.named("P0"),
        depth=int(state["depth"]),
        branch_context=branch_context,
        cut_context=cut_context,
        cut_lineage=cut_lineage,
        node_id=f"parent_reconstruction_{state['path_hash'][:12]}",
        ancestor_path=tuple(
            str(value) for value in state["path_signature"]
        ),
        initial_columns=initial_columns,
        incumbent_objective=None,
        max_direct_tasks=len(data.task_ids),
        max_rounds=int(max_rounds),
        wall_time_limit_sec=float(budget_sec),
        max_columns_per_round=int(max_columns_per_round),
        b0_direct=_diagnostic_b0_placeholder(data),
        tail_dual_stabilization_enabled=True,
        tail_dual_stabilization_alpha=0.7,
        tail_dual_stabilization_window=5,
        worker_pricer_kind=RELAXED_LABELING_WORKER,
        labeling_final_judge_enabled=True,
        labeling_final_judge_max_exact_tasks=len(data.task_ids),
        labeling_final_judge_exact_harvest_target=int(
            profile["root_harvest_target"]
        ),
    )
    wall_sec = perf_counter() - started
    if not _node_probe_exact_safe(payload):
        raise RuntimeError(
            "parent state reconstruction did not close exact-safe"
        )
    if (
        str(payload.get("active_cut_context_hash") or "")
        != str(state["active_cut_context_hash"])
        or str(payload.get("cut_lineage_hash") or "")
        != str(state["cut_lineage_hash"])
    ):
        raise RuntimeError(
            "parent reconstruction changed cut context or lineage"
        )
    expected_bound = state.get("node_lp_bound")
    observed_bound = payload.get("node_lp_bound")
    if (
        expected_bound is None
        or observed_bound is None
        or abs(float(expected_bound) - float(observed_bound)) > 1.0e-6
    ):
        raise RuntimeError("parent reconstruction LP bound mismatch")
    active_columns = tuple(payload.get("_active_columns") or ())
    if not active_columns:
        active_columns = tuple(
            journey_column_from_solution_payload(data, row)
            for row in payload.get("active_columns") or ()
        )
    if not active_columns:
        raise RuntimeError(
            "parent reconstruction contains no active columns"
        )
    primal_columns = _node_primal_columns(payload)
    if not primal_columns:
        raise RuntimeError(
            "parent reconstruction contains no solved RMP primal"
        )
    payload["primal_columns"] = primal_columns
    probe = build_fractional_branch_probe(
        data.task_ids,
        primal_columns,
        active_columns,
        max_candidates=3,
    )
    reconstructed_candidates = list(probe.get("candidates") or ())
    expected_ids = [
        _candidate_id(candidate)
        for candidate in state["candidates"][:3]
    ]
    observed_ids = [
        _candidate_id(candidate)
        for candidate in reconstructed_candidates[:3]
    ]
    universe_matches_control = expected_ids == observed_ids
    if not universe_matches_control:
        if mismatch_diagnostic_path is not None:
            _write_json(
                mismatch_diagnostic_path,
                {
                    "schema_version": (
                        "lunar_ice_bpc.branch_parent_snapshot_mismatch.v1"
                    ),
                    "development_only": True,
                    "deployable": False,
                    "training_authorized": False,
                    "formal_branch_label": False,
                    "instance_content_hash": (
                        data.instance_content_hash
                    ),
                    "path_hash": state["path_hash"],
                    "expected_top3_candidate_ids": expected_ids,
                    "observed_top3_candidate_ids": observed_ids,
                    "node_lp_bound": float(observed_bound),
                    "active_column_count": len(active_columns),
                    "active_cut_context_hash": str(
                        payload.get("active_cut_context_hash") or ""
                    ),
                    "cut_lineage_hash": str(
                        payload.get("cut_lineage_hash") or ""
                    ),
                    "failure_reason": (
                        "EXACT_PARENT_TOP3_NOT_REPRODUCIBLE"
                    ),
                    "result": _json_safe_top_level(payload),
                },
            )
        if not accept_fresh_reconstructed_shortlist:
            raise RuntimeError(
                "parent reconstruction top-3 universe/order mismatch: "
                f"expected={expected_ids!r}, observed={observed_ids!r}"
            )
    summary = {
        "schema_version": (
            "lunar_ice_bpc.branch_parent_snapshot.v1"
        ),
        "exact_safe": True,
        "wall_sec": round(float(wall_sec), 6),
        "active_column_count": len(active_columns),
        "node_lp_bound": float(observed_bound),
        "active_cut_context_hash": str(
            payload.get("active_cut_context_hash") or ""
        ),
        "cut_lineage_hash": str(
            payload.get("cut_lineage_hash") or ""
        ),
        "top3_candidate_ids": observed_ids,
        "top3_universe_matches_control": universe_matches_control,
        "fresh_reconstructed_shortlist_bound": bool(
            not universe_matches_control
            and accept_fresh_reconstructed_shortlist
        ),
        "historical_end_to_end_gold_binding_valid": (
            universe_matches_control
        ),
        "reconstructed_top3_candidates": reconstructed_candidates[:3],
        "true_dual_context": _latest_true_dual_context(payload),
        "certificate_reused": False,
        "columns_reconstructed_exactly": True,
    }
    return payload, active_columns, summary


def _validated_parent_source(
    *,
    data,
    state: dict,
    source: dict,
) -> tuple[dict, tuple, dict]:
    payload = source.get("result") or {}
    source_summary = source.get("summary") or {}
    source_is_deep = (
        str(source_summary.get("snapshot_origin") or "")
        == "exact_p0_deep_parent_snapshot"
    )
    if not (
        deep_target_node_exact_safe(payload)
        if source_is_deep
        else _node_probe_exact_safe(payload)
    ):
        raise RuntimeError("P0 parent source is not exact-safe")
    if (
        str(payload.get("active_cut_context_hash") or "")
        != str(state["active_cut_context_hash"])
        or str(payload.get("cut_lineage_hash") or "")
        != str(state["cut_lineage_hash"])
    ):
        raise RuntimeError("P0 parent source cut binding mismatch")
    expected_bound = state.get("node_lp_bound")
    observed_bound = payload.get("node_lp_bound")
    if (
        expected_bound is None
        or observed_bound is None
        or abs(float(expected_bound) - float(observed_bound)) > 1.0e-6
    ):
        raise RuntimeError("P0 parent source LP bound mismatch")
    active_columns = tuple(
        journey_column_from_solution_payload(data, row)
        for row in payload.get("active_columns") or ()
    )
    if not active_columns:
        raise RuntimeError("P0 parent source has no active columns")
    primal_columns = _node_primal_columns(payload)
    if not primal_columns:
        raise RuntimeError("P0 parent source has no solved RMP primal")
    probe = build_fractional_branch_probe(
        data.task_ids,
        primal_columns,
        active_columns,
        max_candidates=3,
    )
    expected_ids = [
        _candidate_id(candidate)
        for candidate in state["candidates"][:3]
    ]
    observed_ids = [
        _candidate_id(candidate)
        for candidate in list(probe.get("candidates") or ())[:3]
    ]
    if expected_ids != observed_ids:
        raise RuntimeError(
            "P0 parent source top-3 mismatch: "
            f"expected={expected_ids!r}, observed={observed_ids!r}"
        )
    source_is_fresh = bool(
        source_summary.get("fresh_reconstructed_shortlist_bound")
    )
    summary = {
        "schema_version": "lunar_ice_bpc.branch_parent_snapshot.v1",
        "exact_safe": True,
        "wall_sec": round(
            float(
                source.get("root_wall_sec")
                or (source.get("summary") or {}).get("wall_sec")
                or 0.0
            ),
            6,
        ),
        "active_column_count": len(active_columns),
        "node_lp_bound": float(observed_bound),
        "active_cut_context_hash": str(
            payload.get("active_cut_context_hash") or ""
        ),
        "cut_lineage_hash": str(
            payload.get("cut_lineage_hash") or ""
        ),
        "top3_candidate_ids": observed_ids,
        "top3_universe_matches_control": not source_is_fresh,
        "fresh_reconstructed_shortlist_bound": source_is_fresh,
        "historical_end_to_end_gold_binding_valid": (
            not source_is_fresh
        ),
        "reconstructed_top3_candidates": (
            list(
                source_summary.get(
                    "reconstructed_top3_candidates"
                )
                or ()
            )
            if source_is_fresh
            else list(probe.get("candidates") or ())[:3]
        ),
        "true_dual_context": _latest_true_dual_context(payload),
        "certificate_reused": False,
        "columns_reconstructed_exactly": True,
        "snapshot_origin": str(
            source_summary.get("snapshot_origin")
            or "exact_p0_parent_source"
        ),
        "source_sha256": str(
            source_summary.get("source_sha256")
            or _sha256_json(source)
        ),
        "incumbent_objective": source_summary.get(
            "incumbent_objective"
        ),
        "processed_node_count": int(
            source_summary.get("processed_node_count") or 0
        ),
        "open_node_count": int(
            source_summary.get("open_node_count") or 0
        ),
        "global_column_count": int(
            source_summary.get("global_column_count")
            or len(active_columns)
        ),
    }
    return payload, active_columns, summary


def _probe_key(
    *,
    path_hash: str,
    rank_index: int,
    branch_sense: str,
) -> str:
    return (
        f"{str(path_hash)}:rank={int(rank_index)}:"
        f"sense={str(branch_sense)}"
    )


def _persist_child_continuation_snapshot(
    *,
    output_dir: Path,
    data,
    raw: dict,
    initial_columns: tuple,
    probe_key: str,
    path_hash: str,
    candidate_id: str,
    rank_index: int,
    branch_sense: str,
    branch_context: BranchContext,
    cut_context: CutContext,
    cut_lineage: CutLineage,
    observed_wall_sec: float,
    budget_sec: float,
) -> dict | None:
    """Persist columns only for a later matched horizon continuation."""

    active_payload = list(raw.get("active_columns") or ())
    if not active_payload:
        active_columns = tuple(raw.get("_active_columns") or ())
        if not active_columns:
            by_signature = {}
            for column in (
                *tuple(initial_columns),
                *tuple(raw.get("_all_priced_columns") or ()),
            ):
                by_signature[column_signature_from_journey(column)] = column
            active_columns = tuple(by_signature.values())
        active_payload = [
            column.to_solution_payload(
                vehicle_id=f"continuation_column_{index:06d}"
            )
            for index, column in enumerate(active_columns)
        ]
    if not active_payload:
        return None
    snapshot_path = (
        output_dir
        / (
            "child_continuation_"
            f"{hashlib.sha256(probe_key.encode('utf-8')).hexdigest()[:16]}"
            ".json"
        )
    )
    payload = {
        "schema_version": (
            "lunar_ice_bpc.branch_child_continuation_columns.v1"
        ),
        "development_only": True,
        "deployable": False,
        "training_authorized": False,
        "columns_only": True,
        "certificate_reused_for_pricing": False,
        "instance_content_hash": data.instance_content_hash,
        "path_hash": str(path_hash),
        "probe_key": str(probe_key),
        "candidate_id": str(candidate_id),
        "rank_index": int(rank_index),
        "branch_sense": str(branch_sense),
        "branch_context_hash": _sha256_json(
            branch_context.to_payload()
        ),
        "active_cut_context_hash": (
            cut_context.active_cut_context_hash
        ),
        "cut_lineage_hash": cut_lineage.cut_lineage_hash,
        "source_observed_wall_sec": round(
            float(observed_wall_sec), 6
        ),
        "source_budget_sec": round(float(budget_sec), 6),
        "source_node_status": raw.get("node_status"),
        "source_pricing_state": raw.get("pricing_state"),
        "source_certificate_scope": raw.get("certificate_scope"),
        "source_exact_safe": _node_probe_exact_safe(raw),
        "active_column_count": len(active_payload),
        "active_columns": active_payload,
    }
    _write_json(snapshot_path, payload)
    return {
        "path": str(snapshot_path),
        "sha256": _sha256_json(payload),
        "active_column_count": len(active_payload),
        "columns_only": True,
        "certificate_reused_for_pricing": False,
    }


def _continuation_child_map(report: dict) -> dict[str, dict]:
    result = {}
    for state in report.get("state_reports") or ():
        path_hash = str(state.get("path_hash") or "")
        for pair in state.get("pair_reports") or ():
            rank_index = int(pair["rank_index"])
            for child in pair.get("children") or ():
                key = _probe_key(
                    path_hash=path_hash,
                    rank_index=rank_index,
                    branch_sense=str(child["branch_sense"]),
                )
                if key in result:
                    raise ValueError(
                        f"duplicate continuation child {key}"
                    )
                result[key] = dict(child)
    return result


def _load_continuation_columns(
    *,
    data,
    prior_child: dict,
    probe_key: str,
    path_hash: str,
    candidate_id: str,
    rank_index: int,
    branch_sense: str,
    branch_context: BranchContext,
    cut_context: CutContext,
    cut_lineage: CutLineage,
) -> tuple[tuple, dict]:
    binding = prior_child.get("continuation_column_source") or {}
    source_path = Path(str(binding.get("path") or "")).resolve()
    if not source_path.is_file():
        raise ValueError(
            f"continuation column source missing for {probe_key}"
        )
    source = _load_json(source_path)
    if (
        str(binding.get("sha256") or "") != _sha256_json(source)
        or not bool(source.get("columns_only"))
        or bool(source.get("certificate_reused_for_pricing"))
        or str(source.get("instance_content_hash") or "")
        != data.instance_content_hash
        or str(source.get("path_hash") or "") != str(path_hash)
        or str(source.get("probe_key") or "") != str(probe_key)
        or str(source.get("candidate_id") or "")
        != str(candidate_id)
        or int(source.get("rank_index") or 0) != int(rank_index)
        or str(source.get("branch_sense") or "")
        != str(branch_sense)
        or str(source.get("branch_context_hash") or "")
        != _sha256_json(branch_context.to_payload())
        or str(source.get("active_cut_context_hash") or "")
        != cut_context.active_cut_context_hash
        or str(source.get("cut_lineage_hash") or "")
        != cut_lineage.cut_lineage_hash
    ):
        raise ValueError(
            f"continuation column source binding mismatch for {probe_key}"
        )
    columns = tuple(
        journey_column_from_solution_payload(data, row)
        for row in source.get("active_columns") or ()
    )
    if len(columns) != int(source.get("active_column_count") or 0):
        raise ValueError(
            f"continuation column count mismatch for {probe_key}"
        )
    return columns, source


def _progress_binding(
    *,
    data,
    split_manifest_hash: str,
    root_payload: dict,
    control: dict,
    probe_budget_sec: float,
    preference_margin_sec: float,
    lifecycle_overhead_sec: float,
    parent_reconstruction_budget_sec: float = 600.0,
    p0_parent_source_sha256: str = "",
    accept_fresh_reconstructed_shortlist: bool = False,
    continuation_report_sha256: str = "",
) -> dict:
    payload = {
        "schema_version": (
            "lunar_ice_bpc.no_task_wait_v3_branch_child_trajectory_progress.v1"
        ),
        "instance_content_hash": data.instance_content_hash,
        "split_manifest_hash": str(split_manifest_hash),
        "root_source_sha256": _sha256_json(root_payload),
        "control_tree_sha256": _sha256_json(control),
        "probe_budget_sec": float(probe_budget_sec),
        "preference_margin_sec": float(preference_margin_sec),
        "lifecycle_overhead_sec": float(lifecycle_overhead_sec),
        "parent_reconstruction_budget_sec": float(
            parent_reconstruction_budget_sec
        ),
        "parent_snapshot_policy": (
            "exact_reconstruct_bound_top3_before_child_v1"
        ),
        "p0_parent_source_sha256": str(p0_parent_source_sha256),
    }
    if accept_fresh_reconstructed_shortlist:
        payload["accept_fresh_reconstructed_shortlist"] = True
    if continuation_report_sha256:
        payload["continuation_report_sha256"] = str(
            continuation_report_sha256
        )
    return {**payload, "progress_binding_hash": _sha256_json(payload)}


def _load_completed_probes(
    path: Path,
    *,
    expected_binding: dict,
    resume: bool,
) -> dict[str, dict]:
    if not resume or not path.is_file():
        return {}
    payload = _load_json(path)
    if (
        str(payload.get("progress_binding_hash") or "")
        != str(expected_binding["progress_binding_hash"])
    ):
        raise SystemExit("persisted child trajectory progress binding mismatch")
    completed = payload.get("completed_probes") or {}
    if not isinstance(completed, dict):
        raise SystemExit("persisted completed_probes must be a mapping")
    accepted: dict[str, dict] = {}
    for key, value in completed.items():
        if not isinstance(value, dict):
            continue
        summary = dict(value)
        semantics = str(
            summary.get("probe_summary_semantics_version") or ""
        )
        if (
            semantics != PROBE_SUMMARY_SEMANTICS_VERSION
            and summary.get("node_status") == "NODE_LP_CERTIFIED"
        ):
            # Older summaries used an absent top-level convenience field and
            # could misclassify a valid official node certificate.  Re-run
            # only those potentially exact probes; old incomplete/censored
            # observations remain sound lower bounds.
            continue
        accepted[str(key)] = summary
    return accepted


def _write_progress(
    path: Path,
    *,
    binding: dict,
    completed_probes: dict[str, dict],
    planned_probe_count: int,
    status: str,
) -> None:
    _write_json(
        path,
        {
            **binding,
            "development_only": True,
            "deployable": False,
            "training_authorized": False,
            "status": str(status),
            "planned_probe_count": int(planned_probe_count),
            "completed_probe_count": len(completed_probes),
            "completed_probes": completed_probes,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--oracle-dir", required=True)
    parser.add_argument(
        "--split-manifest",
        default=(
            "data/gat_p0v2/"
            "p0_no_task_wait_v3_gat_split_rebind_manifest.json"
        ),
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--probe-budget-sec", type=float, default=60.0)
    parser.add_argument(
        "--parent-reconstruction-budget-sec",
        type=float,
        default=600.0,
    )
    parser.add_argument("--max-states", type=int, default=3)
    parser.add_argument("--max-rounds", type=int, default=16)
    parser.add_argument("--max-columns-per-round", type=int, default=128)
    parser.add_argument("--preference-margin-sec", type=float, default=2.0)
    parser.add_argument(
        "--emulated-guidance-lifecycle-overhead-sec",
        type=float,
        default=0.02,
    )
    parser.add_argument(
        "--disable-race-against-p0",
        action="store_true",
    )
    parser.add_argument(
        "--accept-fresh-reconstructed-shortlist",
        action="store_true",
        help=(
            "If an exact reconstructed parent has a different P0 top-3, "
            "freeze that observed shortlist for matched child survival only. "
            "Historical end-to-end gold is then invalidated."
        ),
    )
    parser.add_argument(
        "--exact-parent-snapshot-source",
        default=None,
        help=(
            "A previously persisted exact branch_parent_snapshot_file. "
            "Its bound parent columns/primal may be reused so a new matched "
            "child horizon does not rerun parent pricing."
        ),
    )
    parser.add_argument(
        "--deep-parent-snapshot",
        default=None,
        help=(
            "A p0v3_branch_deep_parent_snapshot.v1 captured before a "
            "certified non-root P0 branch. It replaces the control state and "
            "binds child probes to that exact node-specific column snapshot."
        ),
    )
    parser.add_argument(
        "--continuation-child-dir",
        default=None,
        help=(
            "Earlier completed child-trajectory directory at a shorter "
            "matched horizon. Exact children are carried forward; censored "
            "children reuse columns only and receive the remaining budget."
        ),
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help=(
            "Validate every parent/snapshot binding and exit before any "
            "child pricing call."
        ),
    )
    parser.add_argument(
        "--max-new-probes-per-process",
        type=int,
        default=0,
        help=(
            "Exit cleanly after this many newly completed child probes. "
            "Zero means unlimited. Use one on large scale so process exit "
            "reclaims Native allocator/cache memory between children."
        ),
    )
    args = parser.parse_args()

    if float(args.probe_budget_sec) <= 0.0:
        raise SystemExit("probe budget must be positive")
    instance_path = (ROOT / args.instance).resolve()
    oracle_dir = (ROOT / args.oracle_dir).resolve()
    split_path = (ROOT / args.split_manifest).resolve()
    output_dir = (ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    data = load_lunar_ice_data(_load_json(instance_path))
    split_manifest = _load_json(split_path)
    split_manifest_hash = str(
        split_manifest.get("manifest_hash") or _sha256_json(split_manifest)
    )
    if data.instance_content_hash not in _development_hashes(split_manifest):
        raise SystemExit("child trajectory accepts V3 development only")
    if data.service_timing_policy_id != SERVICE_TIMING_POLICY_ID:
        raise SystemExit("instance service-timing policy mismatch")
    profile = PROFILE_BY_SCALE.get(int(data.scale))
    if profile is None:
        raise SystemExit("child trajectory currently accepts scale20/30")
    _configure_environment(scale=int(data.scale), profile=profile)
    solver_binding = _solver_binding(
        data=data,
        profile=profile,
        tree_max_rounds=int(args.max_rounds),
        tree_max_columns_per_round=int(
            args.max_columns_per_round
        ),
    )

    root_payload = _load_json(oracle_dir / "root_source.json")
    control = _load_json(oracle_dir / "control_rank0_tree.json")
    deep_snapshot = None
    deep_snapshot_sha256 = ""
    if args.deep_parent_snapshot:
        deep_snapshot = _load_json(
            (ROOT / args.deep_parent_snapshot).resolve()
        )
        snapshot_without_hash = {
            key: value
            for key, value in deep_snapshot.items()
            if key != "snapshot_sha256"
        }
        deep_snapshot_sha256 = str(
            deep_snapshot.get("snapshot_sha256") or ""
        )
        target_node = dict(deep_snapshot.get("target_node") or {})
        target_active_columns = list(
            deep_snapshot.get("target_active_columns") or ()
        )
        if (
            str(deep_snapshot.get("schema_version") or "")
            != "lunar_ice_bpc.p0v3_branch_deep_parent_snapshot.v1"
            or deep_snapshot.get("instance_content_hash")
            != data.instance_content_hash
            or str(deep_snapshot.get("baseline_id") or "")
            != BASELINE_ID
            or str(deep_snapshot.get("split_manifest_hash") or "")
            != split_manifest_hash
            or str(deep_snapshot.get("solver_binding_hash") or "")
            != str(solver_binding["binding_hash"])
            or deep_snapshot_sha256
            != _sha256_json(snapshot_without_hash)
            or int(deep_snapshot.get("target_depth") or 0) <= 0
            or not deep_target_node_exact_safe(target_node)
            or len(target_active_columns)
            != int(
                deep_snapshot.get("target_active_column_count") or -1
            )
            or str(
                deep_snapshot.get("target_active_columns_sha256") or ""
            )
            != _sha256_json(target_active_columns)
        ):
            raise SystemExit(
                "deep parent snapshot binding/exactness mismatch"
            )
        target_node.update(
            {
                "node_status": "BRANCHED",
                "development_branch_requested_rank_index": 0,
                "development_branch_selected_rank_index": 0,
                "development_branch_rank_fallback_to_p0": False,
                "guidance_branch_pair_drop_count": 0,
                "guidance_filter_count": 0,
            }
        )
        control = {
            "schema_version": (
                "lunar_ice_bpc.p0v3_deep_branch_control.v1"
            ),
            "algorithm_status": "BPC_OPTIMAL",
            "incomplete_node_count": 0,
            "tree_closed": True,
            "tree_result_is_exact_bpc": True,
            "objective": deep_snapshot.get("incumbent_objective"),
            "nodes": [target_node],
            "development_only": True,
            "deployable": False,
        }
        _write_json(
            output_dir / "deep_control_rank0_tree.json",
            control,
        )
    control_file_sha256 = _sha256_json(control)
    opportunity_path = oracle_dir / "branch_opportunity_report.json"
    opportunity = (
        _load_json(opportunity_path)
        if opportunity_path.is_file() and deep_snapshot is None
        else None
    )
    try:
        control, opportunity_parent_bound = (
            _bind_exact_opportunity_control(control, opportunity)
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    control_summary = (
        {
            "exact_safe": True,
            "objective": deep_snapshot.get("incumbent_objective"),
        }
        if deep_snapshot is not None
        else _load_json(oracle_dir / "control_rank0_summary.json")
    )
    continuation_report = None
    continuation_children: dict[str, dict] = {}
    continuation_report_sha256 = ""
    if args.continuation_child_dir:
        if not args.disable_race_against_p0:
            raise SystemExit(
                "matched continuation requires --disable-race-against-p0"
            )
        continuation_dir = (
            ROOT / args.continuation_child_dir
        ).resolve()
        continuation_report = _load_json(
            continuation_dir / "child_trajectory_report.json"
        )
        continuation_report_sha256 = _sha256_json(
            continuation_report
        )
        if (
            str(
                continuation_report.get("instance_content_hash")
                or ""
            )
            != data.instance_content_hash
            or str(
                continuation_report.get("split_manifest_hash") or ""
            )
            != split_manifest_hash
            or str(
                continuation_report.get("control_tree_sha256") or ""
            )
            != control_file_sha256
            or bool(
                continuation_report.get(
                    "sequential_race_against_exact_p0"
                )
            )
            or float(
                continuation_report.get("probe_budget_sec") or 0.0
            )
            >= float(args.probe_budget_sec) - 1.0e-9
        ):
            raise SystemExit(
                "continuation child report binding/horizon mismatch"
            )
        try:
            continuation_children = _continuation_child_map(
                continuation_report
            )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    if deep_snapshot is not None:
        target_node = dict(deep_snapshot["target_node"])
        target_node["active_columns"] = list(
            deep_snapshot.get("target_active_columns") or ()
        )
        source_summary = {
            "schema_version": (
                "lunar_ice_bpc.branch_parent_snapshot.v1"
            ),
            "exact_safe": True,
            "wall_sec": 0.0,
            "active_column_count": len(
                target_node["active_columns"]
            ),
            "node_lp_bound": float(target_node["node_lp_bound"]),
            "active_cut_context_hash": str(
                target_node.get("active_cut_context_hash") or ""
            ),
            "cut_lineage_hash": str(
                target_node.get("cut_lineage_hash") or ""
            ),
            "top3_candidate_ids": [
                _candidate_id(candidate)
                for candidate in (
                    target_node.get("fractional_branch_probe") or {}
                ).get("candidates")
                or ()
            ][:3],
            "top3_universe_matches_control": True,
            "fresh_reconstructed_shortlist_bound": False,
            "historical_end_to_end_gold_binding_valid": True,
            "reconstructed_top3_candidates": list(
                (
                    target_node.get("fractional_branch_probe") or {}
                ).get("candidates")
                or ()
            )[:3],
            "true_dual_context": _latest_true_dual_context(
                target_node
            ),
            "certificate_reused": False,
            "columns_reconstructed_exactly": True,
            "snapshot_origin": (
                "exact_p0_deep_parent_snapshot"
            ),
            "source_sha256": deep_snapshot_sha256,
            "incumbent_objective": deep_snapshot.get(
                "incumbent_objective"
            ),
            "processed_node_count": len(
                deep_snapshot.get("processed_nodes") or ()
            ),
            "open_node_count": len(
                deep_snapshot.get("open_nodes_before_target_branch")
                or ()
            ),
            "global_column_count": int(
                deep_snapshot.get("global_column_count") or 0
            ),
        }
        p0_parent_source = {
            "schema_version": (
                "lunar_ice_bpc.branch_parent_snapshot_file.v1"
            ),
            "development_only": True,
            "deployable": False,
            "training_authorized": False,
            "instance_content_hash": data.instance_content_hash,
            "path_hash": deep_snapshot["target_path_hash"],
            "root_source_sha256": _sha256_json(root_payload),
            "control_tree_sha256": control_file_sha256,
            "summary": source_summary,
            "result": target_node,
        }
        p0_parent_source_path = (
            output_dir / "deep_parent_source_adapter.json"
        )
        _write_json(p0_parent_source_path, p0_parent_source)
    else:
        reported_parent_source = str(
            args.exact_parent_snapshot_source
            or (opportunity or {}).get("p0_parent_source_path")
            or ""
        )
        p0_parent_source_path = (
            Path(reported_parent_source).resolve()
            if reported_parent_source
            else oracle_dir / "p0_parent_source.json"
        )
        p0_parent_source = (
            _load_json(p0_parent_source_path)
            if p0_parent_source_path.is_file()
            else None
        )
    parent_source_is_snapshot = bool(
        p0_parent_source
        and str(p0_parent_source.get("schema_version") or "")
        == "lunar_ice_bpc.branch_parent_snapshot_file.v1"
    )
    p0_parent_exact = bool(
        p0_parent_source
        and p0_parent_source.get("instance_content_hash")
        == data.instance_content_hash
        and (
            (
                parent_source_is_snapshot
                and str(
                    p0_parent_source.get("root_source_sha256") or ""
                )
                == _sha256_json(root_payload)
                and str(
                    p0_parent_source.get("control_tree_sha256") or ""
                )
                == _sha256_json(control)
                and bool(
                    (p0_parent_source.get("summary") or {}).get(
                        "exact_safe"
                    )
                )
            )
            or (
                not parent_source_is_snapshot
                and str(
                    p0_parent_source.get("split_manifest_hash") or ""
                )
                == split_manifest_hash
                and bool(p0_parent_source.get("root_exact_safe"))
            )
        )
        and (
            deep_target_node_exact_safe(
                p0_parent_source.get("result") or {}
            )
            if deep_snapshot is not None
            else _node_probe_exact_safe(
                p0_parent_source.get("result") or {}
            )
        )
    )
    p0_parent_binding_sha256 = (
        deep_snapshot_sha256
        if deep_snapshot is not None
        else (
            ""
            if p0_parent_source is None
            else _sha256_json(p0_parent_source)
        )
    )
    root_exact = bool(
        root_payload.get("instance_content_hash")
        == data.instance_content_hash
        and str(root_payload.get("split_manifest_hash") or "")
        == split_manifest_hash
        and bool(root_payload.get("root_exact_safe"))
        and _root_exact_safe(root_payload.get("result") or {})
    )
    if (
        root_payload.get("instance_content_hash")
        != data.instance_content_hash
        or str(root_payload.get("split_manifest_hash") or "")
        != split_manifest_hash
        or not (root_exact or p0_parent_exact)
    ):
        raise SystemExit(
            "neither common root nor P0 parent source is exact-safe"
        )
    binding = root_payload.get("solver_binding") or {}
    if (
        str(binding.get("baseline_id") or "") != BASELINE_ID
        or str(binding.get("instance_content_hash") or "")
        != data.instance_content_hash
    ):
        raise SystemExit("persisted root source baseline binding mismatch")
    if (
        deep_snapshot is not None
        and str(deep_snapshot.get("solver_binding_hash") or "")
        != str(binding.get("binding_hash") or "")
    ):
        raise SystemExit("deep parent snapshot solver binding mismatch")

    root_result = root_payload.get("result") or {}
    active_columns = tuple(
        journey_column_from_solution_payload(data, row)
        for row in root_result.get("active_columns") or ()
    )
    if not active_columns and not p0_parent_exact:
        raise SystemExit("root source contains no active columns")
    states = _actionable_state_rows(control)
    selected_states = states[: max(0, int(args.max_states))]
    if args.validate_only:
        if not selected_states:
            raise SystemExit("validation found no actionable state")
        if not p0_parent_exact or p0_parent_source is None:
            raise SystemExit(
                "validation-only requires an exact persisted parent"
            )
        validated = []
        for state in selected_states:
            try:
                _, columns, summary = _validated_parent_source(
                    data=data,
                    state=state,
                    source=p0_parent_source,
                )
            except RuntimeError as exc:
                raise SystemExit(str(exc)) from exc
            validated.append(
                {
                    "node_id": state["node_id"],
                    "path_hash": state["path_hash"],
                    "active_column_count": len(columns),
                    "top3_candidate_ids": summary[
                        "top3_candidate_ids"
                    ],
                    "snapshot_origin": summary["snapshot_origin"],
                }
            )
        status = {
            "schema_version": SCHEMA_VERSION,
            "development_only": True,
            "deployable": False,
            "training_authorized": False,
            "status": "VALIDATION_ONLY_COMPLETE",
            "instance_id": data.instance_id,
            "instance_content_hash": data.instance_content_hash,
            "validated_state_count": len(validated),
            "states": validated,
            "child_pricing_call_count": 0,
        }
        _write_json(
            output_dir / "validation_only_status.json",
            status,
        )
        print(json.dumps(status, ensure_ascii=False, sort_keys=True))
        return 0
    gold_path = oracle_dir / "state_oracle_report.json"
    gold_report = _load_json(gold_path) if gold_path.is_file() else None
    progress_path = output_dir / "child_trajectory_progress.json"
    progress_binding = _progress_binding(
        data=data,
        split_manifest_hash=split_manifest_hash,
        root_payload=root_payload,
        control=control,
        probe_budget_sec=float(args.probe_budget_sec),
        preference_margin_sec=float(args.preference_margin_sec),
        lifecycle_overhead_sec=float(
            args.emulated_guidance_lifecycle_overhead_sec
        ),
        parent_reconstruction_budget_sec=float(
            args.parent_reconstruction_budget_sec
        ),
        p0_parent_source_sha256=(
            p0_parent_binding_sha256
        ),
        accept_fresh_reconstructed_shortlist=bool(
            args.accept_fresh_reconstructed_shortlist
        ),
        continuation_report_sha256=continuation_report_sha256,
    )
    completed_probes = _load_completed_probes(
        progress_path,
        expected_binding=progress_binding,
        resume=bool(args.resume),
    )
    planned_probe_count = len(selected_states) * 3 * 2
    _write_progress(
        progress_path,
        binding=progress_binding,
        completed_probes=completed_probes,
        planned_probe_count=planned_probe_count,
        status="RUNNING",
    )

    state_reports = []
    new_probe_count = 0
    for state_index, state in enumerate(selected_states):
        source_parent_summary = (
            (p0_parent_source or {}).get("summary") or {}
        )
        if bool(
            source_parent_summary.get(
                "fresh_reconstructed_shortlist_bound"
            )
        ):
            fresh_candidates = list(
                source_parent_summary.get(
                    "reconstructed_top3_candidates"
                )
                or ()
            )
            if len(fresh_candidates) != 3:
                raise SystemExit(
                    "exact parent source fresh shortlist is incomplete"
                )
            fresh_ids = [
                _candidate_id(row) for row in fresh_candidates
            ]
            fresh_hash = canonical_universe_hash(
                fresh_ids,
                universe_kind="p0_branch_shortlist",
            )
            state = {
                **state,
                "candidates": fresh_candidates,
                "legal_branch_shortlist_hash_before_sort": fresh_hash,
                "legal_branch_shortlist_hash_after_sort": fresh_hash,
                "fresh_reconstructed_shortlist_bound": True,
            }
        cut_context = _cut_context_from_payload(state["cut_context"])
        cut_lineage = _cut_lineage_from_payload(state["cut_lineage"])
        lineage_issues = cut_lineage.validate_context(cut_context)
        if lineage_issues:
            raise SystemExit(",".join(lineage_issues))
        if (
            state["active_cut_context_hash"]
            and cut_context.active_cut_context_hash
            != state["active_cut_context_hash"]
        ):
            raise SystemExit("active cut context hash mismatch")
        if (
            state["cut_lineage_hash"]
            and cut_lineage.cut_lineage_hash
            != state["cut_lineage_hash"]
        ):
            raise SystemExit("cut lineage hash mismatch")

        parent_snapshot_path = (
            output_dir
            / f"parent_snapshot_{state['path_hash'][:12]}.json"
        )
        if args.resume and parent_snapshot_path.is_file():
            persisted_parent = _load_json(parent_snapshot_path)
            parent_payload = persisted_parent.get("result") or {}
            parent_summary = persisted_parent.get("summary") or {}
            if (
                not bool(parent_summary.get("exact_safe"))
                or not (
                    bool(
                        parent_summary.get(
                            "top3_universe_matches_control"
                        )
                    )
                    or bool(
                        parent_summary.get(
                            "fresh_reconstructed_shortlist_bound"
                        )
                    )
                )
                or str(
                    parent_summary.get(
                        "active_cut_context_hash"
                    )
                    or ""
                )
                != state["active_cut_context_hash"]
                or str(
                    parent_summary.get("cut_lineage_hash") or ""
                )
                != state["cut_lineage_hash"]
            ):
                raise SystemExit(
                    "persisted parent snapshot binding mismatch"
                )
            parent_columns = tuple(
                journey_column_from_solution_payload(data, row)
                for row in parent_payload.get("active_columns") or ()
            )
            if len(parent_columns) != int(
                parent_summary.get("active_column_count") or 0
            ):
                raise SystemExit(
                    "persisted parent snapshot column mismatch"
                )
            if bool(
                parent_summary.get(
                    "fresh_reconstructed_shortlist_bound"
                )
            ):
                fresh_candidates = list(
                    parent_summary.get(
                        "reconstructed_top3_candidates"
                    )
                    or ()
                )
                if len(fresh_candidates) != 3:
                    raise SystemExit(
                        "persisted fresh shortlist is incomplete"
                    )
                fresh_ids = [
                    _candidate_id(row) for row in fresh_candidates
                ]
                fresh_hash = canonical_universe_hash(
                    fresh_ids,
                    universe_kind="p0_branch_shortlist",
                )
                state = {
                    **state,
                    "candidates": fresh_candidates,
                    "legal_branch_shortlist_hash_before_sort": (
                        fresh_hash
                    ),
                    "legal_branch_shortlist_hash_after_sort": fresh_hash,
                    "fresh_reconstructed_shortlist_bound": True,
                }
        elif p0_parent_exact:
            try:
                (
                    parent_payload,
                    parent_columns,
                    parent_summary,
                ) = _validated_parent_source(
                    data=data,
                    state=state,
                    source=p0_parent_source,
                )
            except RuntimeError as exc:
                raise SystemExit(str(exc)) from exc
            _write_json(
                parent_snapshot_path,
                {
                    "schema_version": (
                        "lunar_ice_bpc.branch_parent_snapshot_file.v1"
                    ),
                    "development_only": True,
                    "deployable": False,
                    "training_authorized": False,
                    "instance_content_hash": (
                        data.instance_content_hash
                    ),
                    "path_hash": state["path_hash"],
                    "root_source_sha256": _sha256_json(root_payload),
                    "control_tree_sha256": _sha256_json(control),
                    "summary": parent_summary,
                    "result": parent_payload,
                },
            )
        else:
            try:
                (
                    raw_parent,
                    parent_columns,
                    parent_summary,
                ) = _reconstruct_parent_state(
                    data=data,
                    profile=profile,
                    initial_columns=active_columns,
                    state=state,
                    branch_context=branch_context_from_payload(
                        state["parent_branch_context"]
                    ),
                    cut_context=cut_context,
                    cut_lineage=cut_lineage,
                    budget_sec=float(
                        args.parent_reconstruction_budget_sec
                    ),
                    max_rounds=int(args.max_rounds),
                    max_columns_per_round=int(
                        args.max_columns_per_round
                    ),
                    mismatch_diagnostic_path=(
                        output_dir
                        / (
                            "parent_snapshot_mismatch_"
                            f"{state['path_hash'][:12]}.json"
                        )
                    ),
                    accept_fresh_reconstructed_shortlist=bool(
                        args.accept_fresh_reconstructed_shortlist
                    ),
                )
            except RuntimeError as exc:
                raise SystemExit(str(exc)) from exc
            if bool(
                parent_summary.get(
                    "fresh_reconstructed_shortlist_bound"
                )
            ):
                fresh_candidates = list(
                    parent_summary.get(
                        "reconstructed_top3_candidates"
                    )
                    or ()
                )
                fresh_ids = [
                    _candidate_id(row) for row in fresh_candidates
                ]
                fresh_hash = canonical_universe_hash(
                    fresh_ids,
                    universe_kind="p0_branch_shortlist",
                )
                state = {
                    **state,
                    "candidates": fresh_candidates,
                    "legal_branch_shortlist_hash_before_sort": (
                        fresh_hash
                    ),
                    "legal_branch_shortlist_hash_after_sort": fresh_hash,
                    "fresh_reconstructed_shortlist_bound": True,
                }
            parent_payload = _json_safe_top_level(raw_parent)
            _write_json(
                parent_snapshot_path,
                {
                    "schema_version": (
                        "lunar_ice_bpc.branch_parent_snapshot_file.v1"
                    ),
                    "development_only": True,
                    "deployable": False,
                    "training_authorized": False,
                    "instance_content_hash": (
                        data.instance_content_hash
                    ),
                    "path_hash": state["path_hash"],
                    "root_source_sha256": _sha256_json(root_payload),
                    "control_tree_sha256": _sha256_json(control),
                    "summary": parent_summary,
                    "result": parent_payload,
                },
            )

        pair_reports = []
        p0_exact_work: float | None = None
        for rank_index, candidate in enumerate(state["candidates"]):
            candidate_id = _candidate_id(candidate)
            children = []
            accumulated = 0.0
            for branch_sense, context_key in (
                ("same_journey", "same_child_context"),
                ("different_journey", "different_child_context"),
            ):
                probe_key = _probe_key(
                    path_hash=state["path_hash"],
                    rank_index=rank_index,
                    branch_sense=branch_sense,
                )
                lifecycle = float(
                    args.emulated_guidance_lifecycle_overhead_sec
                    if rank_index > 0
                    else 0.0
                )
                child_budget = float(args.probe_budget_sec)
                if rank_index > 0 and not args.disable_race_against_p0:
                    child_budget = _race_budget(
                        base_budget_sec=float(args.probe_budget_sec),
                        p0_exact_pair_work_sec=p0_exact_work,
                        accumulated_alt_work_sec=accumulated,
                        lifecycle_overhead_sec=lifecycle,
                        margin_sec=float(args.preference_margin_sec),
                    )
                persisted_child = completed_probes.get(probe_key)
                prior_child = continuation_children.get(probe_key)
                if (
                    continuation_report is not None
                    and prior_child is None
                ):
                    raise SystemExit(
                        f"continuation report missing {probe_key}"
                    )
                if persisted_child is not None:
                    child = dict(persisted_child)
                elif prior_child is not None and bool(
                    prior_child.get("event_observed")
                ):
                    child = {
                        **prior_child,
                        "budget_sec": float(args.probe_budget_sec),
                        "continuation_carried_exact_event": True,
                        "continuation_source_report_sha256": (
                            continuation_report_sha256
                        ),
                    }
                elif child_budget <= 1.0e-9:
                    child = _not_run_child_summary(
                        rank_index=rank_index,
                        branch_sense=branch_sense,
                        candidate_id=candidate_id,
                        reason="SEQUENTIAL_RACE_CANNOT_BEAT_P0",
                    )
                else:
                    child_context = _extend_branch_context(
                        state["parent_branch_context"],
                        candidate.get(context_key) or {},
                    )
                    probe_initial_columns = parent_columns
                    prior_observed_wall = 0.0
                    prior_budget = 0.0
                    if prior_child is not None:
                        if (
                            not bool(prior_child.get("right_censored"))
                            or bool(prior_child.get("event_observed"))
                        ):
                            raise SystemExit(
                                f"invalid censored continuation {probe_key}"
                            )
                        try:
                            (
                                probe_initial_columns,
                                continuation_source,
                            ) = _load_continuation_columns(
                                data=data,
                                prior_child=prior_child,
                                probe_key=probe_key,
                                path_hash=state["path_hash"],
                                candidate_id=candidate_id,
                                rank_index=rank_index,
                                branch_sense=branch_sense,
                                branch_context=child_context,
                                cut_context=cut_context,
                                cut_lineage=cut_lineage,
                            )
                        except ValueError as exc:
                            raise SystemExit(str(exc)) from exc
                        prior_observed_wall = float(
                            prior_child.get("observed_wall_sec")
                            or 0.0
                        )
                        prior_budget = float(
                            prior_child.get("budget_sec") or 0.0
                        )
                        child_budget = max(
                            0.0,
                            float(args.probe_budget_sec)
                            - prior_observed_wall,
                        )
                    raw, wall_sec = _probe_child(
                        data=data,
                        profile=profile,
                        initial_columns=probe_initial_columns,
                        branch_context=child_context,
                        cut_context=cut_context,
                        cut_lineage=cut_lineage,
                        depth=int(state["depth"]) + 1,
                        ancestor_path=(str(state["node_id"]),),
                        node_id=(
                            f"trajectory_s{state_index:03d}_r"
                            f"{rank_index}_{branch_sense}"
                        ),
                        incumbent_objective=(
                            control_summary.get("objective")
                            if bool(
                                control_summary.get("exact_safe")
                            )
                            else None
                        ),
                        budget_sec=child_budget,
                        max_rounds=int(args.max_rounds),
                        max_columns_per_round=int(
                            args.max_columns_per_round
                        ),
                    )
                    child = _node_probe_summary(
                        payload=raw,
                        wall_sec=wall_sec,
                        budget_sec=child_budget,
                        rank_index=rank_index,
                        branch_sense=branch_sense,
                        candidate_id=candidate_id,
                    )
                    if prior_child is not None:
                        stage_wall = float(
                            child["observed_wall_sec"]
                        )
                        child["observed_wall_sec"] = round(
                            min(
                                float(args.probe_budget_sec),
                                prior_observed_wall + stage_wall,
                            ),
                            6,
                        )
                        child["budget_sec"] = float(
                            args.probe_budget_sec
                        )
                        child["round_count"] = int(
                            prior_child.get("round_count") or 0
                        ) + int(child.get("round_count") or 0)
                        child["added_column_count"] = int(
                            prior_child.get("added_column_count") or 0
                        ) + int(
                            child.get("added_column_count") or 0
                        )
                        child["history"] = [
                            *list(prior_child.get("history") or ()),
                            *list(child.get("history") or ()),
                        ]
                        child["continuation_columns_only"] = True
                        child[
                            "continuation_certificate_reused_for_pricing"
                        ] = False
                        child["continuation_source_report_sha256"] = (
                            continuation_report_sha256
                        )
                        child["continuation_source_budget_sec"] = (
                            prior_budget
                        )
                        child["continuation_incremental_budget_sec"] = (
                            child_budget
                        )
                        child["continuation_stage_observed_wall_sec"] = (
                            round(stage_wall, 6)
                        )
                        child["continuation_source_columns_sha256"] = (
                            _sha256_json(continuation_source)
                        )
                    continuation = _persist_child_continuation_snapshot(
                        output_dir=output_dir,
                        data=data,
                        raw=raw,
                        initial_columns=probe_initial_columns,
                        probe_key=probe_key,
                        path_hash=state["path_hash"],
                        candidate_id=candidate_id,
                        rank_index=rank_index,
                        branch_sense=branch_sense,
                        branch_context=child_context,
                        cut_context=cut_context,
                        cut_lineage=cut_lineage,
                        observed_wall_sec=float(
                            child["observed_wall_sec"]
                        ),
                        budget_sec=float(child["budget_sec"]),
                    )
                    if continuation is not None:
                        child["continuation_column_source"] = continuation
                if persisted_child is None:
                    completed_probes[probe_key] = child
                    _write_progress(
                        progress_path,
                        binding=progress_binding,
                        completed_probes=completed_probes,
                        planned_probe_count=planned_probe_count,
                        status="RUNNING",
                    )
                    new_probe_count += 1
                    if (
                        int(args.max_new_probes_per_process) > 0
                        and new_probe_count
                        >= int(args.max_new_probes_per_process)
                        and len(completed_probes)
                        < planned_probe_count
                    ):
                        _write_progress(
                            progress_path,
                            binding=progress_binding,
                            completed_probes=completed_probes,
                            planned_probe_count=planned_probe_count,
                            status="PAUSED_PROCESS_PROBE_BUDGET",
                        )
                        print(
                            json.dumps(
                                {
                                    "instance_id": data.instance_id,
                                    "scale": int(data.scale),
                                    "status": (
                                        "PAUSED_PROCESS_PROBE_BUDGET"
                                    ),
                                    "completed_probe_count": len(
                                        completed_probes
                                    ),
                                    "planned_probe_count": (
                                        planned_probe_count
                                    ),
                                    "resume_required": True,
                                    "training_authorized": False,
                                },
                                ensure_ascii=False,
                                sort_keys=True,
                            )
                        )
                        return 0
                children.append(child)
                accumulated += float(child["observed_wall_sec"])
            pair = _pair_summary(
                rank_index=rank_index,
                candidate_id=candidate_id,
                children=children,
                lifecycle_overhead_sec=float(
                    args.emulated_guidance_lifecycle_overhead_sec
                ),
            )
            pair_reports.append(pair)
            if rank_index == 0:
                p0_exact_work = pair.get("pair_exact_work_sec")

        preferences = _preference_rows(
            pair_reports,
            margin_sec=float(args.preference_margin_sec),
        )
        survival_rows = _survival_training_rows(
            instance_content_hash=data.instance_content_hash,
            scale=int(data.scale),
            path_hash=state["path_hash"],
            pairs=pair_reports,
        )
        diagnostic_order = _diagnostic_lower_bound_order(pair_reports)
        gold_label = (
            None
            if bool(
                state.get("fresh_reconstructed_shortlist_bound")
            )
            else _gold_label_for_state(
                gold_report,
                path_hash=state["path_hash"],
                candidate_ids=[
                    str(pair["candidate_id"])
                    for pair in pair_reports
                ],
            )
        )
        horizon_replays = _diagnostic_horizon_replays(
            pair_reports,
            gold_label=gold_label,
        )
        p0_wins = {
            int(row["loser_rank_index"])
            for row in preferences
            if int(row["winner_rank_index"]) == 0
        }
        alt_wins = {
            int(row["winner_rank_index"])
            for row in preferences
            if int(row["loser_rank_index"]) == 0
            and int(row["winner_rank_index"]) > 0
        }
        state_reports.append(
            {
                "node_id": state["node_id"],
                "depth": state["depth"],
                "path_signature": state["path_signature"],
                "path_hash": state["path_hash"],
                "legal_branch_shortlist_hash_before_sort": state[
                    "legal_branch_shortlist_hash_before_sort"
                ],
                "legal_branch_shortlist_hash_after_sort": state[
                    "legal_branch_shortlist_hash_after_sort"
                ],
                "guidance_branch_pair_drop_count": 0,
                "pair_reports": pair_reports,
                "parent_state_reconstructed": True,
                "parent_snapshot": parent_summary,
                "parent_snapshot_path": str(parent_snapshot_path),
                "fresh_reconstructed_shortlist_bound": bool(
                    state.get("fresh_reconstructed_shortlist_bound")
                ),
                "historical_end_to_end_gold_binding_valid": not bool(
                    state.get("fresh_reconstructed_shortlist_bound")
                ),
                "strong_preference_rows": preferences,
                "strong_preference_count": len(preferences),
                "survival_training_rows": survival_rows,
                "survival_training_row_count": len(survival_rows),
                "survival_event_count": sum(
                    bool(row["event_observed"])
                    for row in survival_rows
                ),
                "survival_censored_count": sum(
                    not bool(row["event_observed"])
                    for row in survival_rows
                ),
                "diagnostic_pair_lower_bound_order": diagnostic_order,
                "diagnostic_pair_lower_bound_order_is_training_label": False,
                "diagnostic_proxy_top1_matches_gold": (
                    None
                    if gold_label is None
                    else int(diagnostic_order[0])
                    == int(gold_label["oracle_selected_rank_index"])
                ),
                "diagnostic_horizon_replays": horizon_replays,
                "alternative_beats_p0_rank_indices": sorted(alt_wins),
                "p0_beats_alternative_rank_indices": sorted(p0_wins),
                "gold_end_to_end_label": gold_label,
            }
        )

    report = {
        "schema_version": SCHEMA_VERSION,
        "development_only": True,
        "deployable": False,
        "training_authorized": False,
        "instance_id": data.instance_id,
        "instance_content_hash": data.instance_content_hash,
        "scale": int(data.scale),
        "service_timing_policy_id": data.service_timing_policy_id,
        "baseline_id": BASELINE_ID,
        "solver_binding": binding,
        "split_manifest_hash": split_manifest_hash,
        "root_source_sha256": _sha256_json(root_payload),
        "p0_parent_source_sha256": (
            None
            if p0_parent_source is None
            else p0_parent_binding_sha256
        ),
        "deep_parent_snapshot_sha256": (
            deep_snapshot_sha256 or None
        ),
        "p0_parent_source_exact_safe": p0_parent_exact,
        "control_tree_sha256": control_file_sha256,
        "effective_control_state_sha256": _sha256_json(control),
        "opportunity_parent_state_bound": opportunity_parent_bound,
        "probe_budget_sec": float(args.probe_budget_sec),
        "continuation_source_report_sha256": (
            continuation_report_sha256 or None
        ),
        "continuation_source_horizon_sec": (
            None
            if continuation_report is None
            else float(continuation_report["probe_budget_sec"])
        ),
        "continuation_reuses_columns_only": bool(
            continuation_report is not None
        ),
        "continuation_reuses_certificate_for_pricing": False,
        "formal_one_shot_survival_label": bool(
            continuation_report is None
        ),
        "continuation_for_horizon_discovery_only": bool(
            continuation_report is not None
        ),
        "preference_margin_sec": float(args.preference_margin_sec),
        "pair_cost_semantics": PAIR_COST_SEMANTICS,
        "target_kind": PAIR_TARGET_KIND,
        "censoring_semantics": (
            "Incomplete child wall time is an observed lower bound; no fixed "
            "timeout penalty is added."
        ),
        "legacy_normalized_cost_present": False,
        "legacy_four_coefficient_cost_present": False,
        "fixed_timeout_penalty_present": False,
        "state_count_available": len(states),
        "state_count_collected": len(state_reports),
        "effective_independent_sample_unit": "instance_state",
        "same_and_different_children_required": True,
        "formal_parent_snapshot_required": True,
        "parent_state_reconstructed_count": sum(
            bool(row["parent_state_reconstructed"])
            for row in state_reports
        ),
        "sequential_race_against_exact_p0": not bool(
            args.disable_race_against_p0
        ),
        "guidance_filter_count": 0,
        "guidance_branch_pair_drop_count": 0,
        "state_reports": state_reports,
        "strong_preference_count": sum(
            int(row["strong_preference_count"])
            for row in state_reports
        ),
        "survival_training_row_count": sum(
            int(row["survival_training_row_count"])
            for row in state_reports
        ),
        "survival_event_count": sum(
            int(row["survival_event_count"])
            for row in state_reports
        ),
        "survival_censored_count": sum(
            int(row["survival_censored_count"])
            for row in state_reports
        ),
        "survival_training_state_count": sum(
            int(row["survival_training_row_count"]) == 6
            for row in state_reports
        ),
        "diagnostic_proxy_gold_match_count": sum(
            row["diagnostic_proxy_top1_matches_gold"] is True
            for row in state_reports
        ),
        "diagnostic_proxy_gold_mismatch_count": sum(
            row["diagnostic_proxy_top1_matches_gold"] is False
            for row in state_reports
        ),
        "diagnostic_proxy_is_training_target": False,
        "alternative_beats_p0_state_count": sum(
            bool(row["alternative_beats_p0_rank_indices"])
            for row in state_reports
        ),
        "gold_end_to_end_linked_state_count": sum(
            row["gold_end_to_end_label"] is not None
            for row in state_reports
        ),
        "fresh_reconstructed_shortlist_state_count": sum(
            bool(
                row.get("fresh_reconstructed_shortlist_bound")
            )
            for row in state_reports
        ),
    }
    _write_json(output_dir / "child_trajectory_report.json", report)
    _write_progress(
        progress_path,
        binding=progress_binding,
        completed_probes=completed_probes,
        planned_probe_count=planned_probe_count,
        status="COMPLETED",
    )
    print(
        json.dumps(
            {
                "instance_id": report["instance_id"],
                "scale": report["scale"],
                "state_count_collected": report[
                    "state_count_collected"
                ],
                "strong_preference_count": report[
                    "strong_preference_count"
                ],
                "alternative_beats_p0_state_count": report[
                    "alternative_beats_p0_state_count"
                ],
                "training_authorized": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
