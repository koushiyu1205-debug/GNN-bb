"""Live SRI separation loop around the exact B2B-R3 node engine."""

from __future__ import annotations

from dataclasses import replace
from time import perf_counter
from typing import Iterable

from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.bpc.cuts.live_sri import (
    LIVE_SRI_SEPARATOR_VERSION,
    LiveSriPolicy,
    activate_separated_cuts,
    separate_live_sri,
)
from lunar_ice_bpc.exact.bpc.master.journey_master import solve_root_journey_master
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import solve_node_pricing_with_b2b_r3
from lunar_ice_bpc.exact.core.branching import BranchContext
from lunar_ice_bpc.exact.core.cuts import CutContext, CutLineage
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn


def solve_node_pricing_with_live_sri(
    data: LunarIceData,
    *,
    policy: LiveSriPolicy,
    depth: int,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
    cut_lineage: CutLineage | None = None,
    node_id: str = "root",
    ancestor_path: Iterable[str] = tuple(),
    initial_columns: Iterable[JourneyColumn] | None = None,
    wall_time_limit_sec: float | None = None,
    **node_kwargs,
) -> dict:
    """Close pricing and separation under one immutable branch+cut context.

    A node certificate is returned only after the exact pricing engine has
    closed the current active-cut RMP and a final complete separator pass has
    either found no new violation or reached an explicit policy cap.
    """

    if not policy.enabled:
        return solve_node_pricing_with_b2b_r3(
            data,
            branch_context=branch_context,
            cut_context=cut_context,
            cut_lineage=cut_lineage,
            node_id=node_id,
            initial_columns=initial_columns,
            wall_time_limit_sec=wall_time_limit_sec,
            **node_kwargs,
        )

    subset_sizes = policy.subset_sizes_for_depth(depth)
    if not subset_sizes:
        result = solve_node_pricing_with_b2b_r3(
            data,
            branch_context=branch_context,
            cut_context=cut_context,
            cut_lineage=cut_lineage,
            live_cut_policy_hash=policy.policy_hash,
            separator_policy_version=LIVE_SRI_SEPARATOR_VERSION,
            node_id=node_id,
            initial_columns=initial_columns,
            wall_time_limit_sec=wall_time_limit_sec,
            **node_kwargs,
        )
        return _bind_live_state(
            result,
            policy=policy,
            context=cut_context or CutContext(),
            lineage=cut_lineage or CutLineage(policy_version=policy.version),
            separation_history=[],
            all_priced_columns=tuple(result.get("_all_priced_columns") or tuple()),
            terminal_reason="NODE_SEPARATION_DISABLED_BY_POLICY",
        )

    started_at = perf_counter()
    context = cut_context or CutContext()
    lineage = cut_lineage or CutLineage(policy_version=policy.version)
    lineage_issues = lineage.validate_context(context)
    if lineage_issues:
        raise ValueError(",".join(lineage_issues))
    current_columns = tuple(initial_columns or tuple())
    all_priced: dict[tuple, JourneyColumn] = {}
    separation_history: list[dict] = []
    sparse_tail_deviation_used = False

    for separation_round in range(1, max(1, int(policy.max_separation_rounds)) + 2):
        remaining = _remaining(wall_time_limit_sec, started_at)
        if remaining is not None and remaining <= 0.0:
            return _incomplete_live_payload(
                data,
                policy=policy,
                context=context,
                lineage=lineage,
                history=separation_history,
                all_priced_columns=tuple(all_priced.values()),
                reason="LIVE_SRI_NODE_DEADLINE_BEFORE_PRICING",
            )
        round_node_kwargs = dict(node_kwargs)
        if sparse_tail_deviation_used:
            round_node_kwargs["one_deviation_sparse_tail_policy"] = None
        engine = solve_node_pricing_with_b2b_r3(
            data,
            branch_context=branch_context,
            cut_context=context,
            cut_lineage=lineage,
            live_cut_policy_hash=policy.policy_hash,
            separator_policy_version=LIVE_SRI_SEPARATOR_VERSION,
            node_id=node_id,
            initial_columns=current_columns or None,
            wall_time_limit_sec=remaining,
            return_active_columns_payload=True,
            **round_node_kwargs,
        )
        if any(
            bool(
                row.get("one_deviation_sparse_tail_attempted")
            )
            for row in engine.get("history") or []
            if isinstance(row, dict)
        ):
            sparse_tail_deviation_used = True
        for column in engine.get("_all_priced_columns") or tuple():
            signature = column_signature_from_journey(column)
            previous = all_priced.get(signature)
            if previous is None or column.objective < previous.objective - 1.0e-12:
                all_priced[signature] = column
        if str(engine.get("node_status")) != "NODE_LP_CERTIFIED":
            return _bind_live_state(
                engine,
                policy=policy,
                context=context,
                lineage=lineage,
                separation_history=separation_history,
                all_priced_columns=tuple(all_priced.values()),
                terminal_reason="PRICING_NOT_CERTIFIED_BEFORE_SEPARATION",
            )

        master = engine.get("_master")
        if master is None or master.rmp.status != "RESTRICTED_RMP_OPTIMAL":
            return _bind_live_state(
                engine,
                policy=policy,
                context=context,
                lineage=lineage,
                separation_history=separation_history,
                all_priced_columns=tuple(all_priced.values()),
                terminal_reason="RMP_NOT_AVAILABLE_FOR_SEPARATION",
            )

        global_count = sum(1 for row in lineage.entries if row.scope == "global")
        local_count = sum(1 for row in lineage.entries if row.scope == "local")
        scope_remaining = (
            int(policy.global_cap) - global_count
            if int(depth) == 0
            else int(policy.lineage_local_cap) - local_count
        )
        selection_capacity = max(
            0,
            min(scope_remaining, int(policy.active_cap) - len(context.cuts)),
        )
        candidate_group_count = (
            int(policy.candidate_group_count)
            if policy.candidate_group_screening_enabled
            else 1
        )
        separated_pool = separate_live_sri(
            data.task_ids,
            master.rmp.primal_columns,
            subset_sizes=subset_sizes,
            selection_capacity=(
                selection_capacity * candidate_group_count
            ),
            existing_cut_context=context,
            violation_eps=policy.violation_eps,
        )
        before_bound = master.rmp.objective_bound
        candidate_groups = _candidate_group_separations(
            separated_pool,
            group_size=selection_capacity,
            max_group_count=candidate_group_count,
        )
        if not candidate_groups:
            separated = replace(
                separated_pool,
                selected=tuple(),
                selection_capacity=selection_capacity,
            )
            next_context, next_lineage, activation = (
                activate_separated_cuts(
                    context,
                    lineage,
                    separated,
                    policy=policy,
                    node_id=node_id,
                    depth=depth,
                    ancestor_path=ancestor_path,
                )
            )
            row = {
                "separation_round": separation_round,
                "node_id": str(node_id),
                "depth": int(depth),
                "rmp_bound_before": before_bound,
                **separated.to_payload(),
                "activation": activation,
            }
            activation["committed"] = False
            separation_history.append(row)
            terminal_reason = (
                "POLICY_CAP_REACHED_WITH_UNSELECTED_VIOLATIONS"
                if separated_pool.violated_candidate_count > 0
                else "COMPLETE_ENUMERATION_NO_NEW_VIOLATED_SRI"
            )
            row["terminal_separation"] = True
            row["terminal_reason"] = terminal_reason
            return _bind_live_state(
                engine,
                policy=policy,
                context=context,
                lineage=lineage,
                separation_history=separation_history,
                all_priced_columns=tuple(all_priced.values()),
                terminal_reason=terminal_reason,
            )

        active_columns = tuple(engine.get("_active_columns") or tuple())
        group_attempts: list[dict] = []
        selected_group = candidate_groups[0]
        next_context = context
        next_lineage = lineage
        activation: dict = {}
        commit = False
        for group_index, separated in enumerate(candidate_groups, start=1):
            (
                attempted_context,
                attempted_lineage,
                attempted_activation,
            ) = activate_separated_cuts(
                context,
                lineage,
                separated,
                policy=policy,
                node_id=node_id,
                depth=depth,
                ancestor_path=ancestor_path,
            )
            pre_activation_master = solve_root_journey_master(
                data,
                active_columns,
                negative_eps=float(
                    node_kwargs.get("negative_eps", 1.0e-6)
                ),
                rmp_iteration_id=(
                    (
                        f"live-sri-precommit-{node_id}-"
                        f"{separation_round}-group-{group_index}"
                    )
                    if policy.candidate_group_screening_enabled
                    else (
                        f"live-sri-precommit-{node_id}-"
                        f"{separation_round}"
                    )
                ),
                branch_context=branch_context,
                cut_context=attempted_context,
                cut_lineage=attempted_lineage,
                live_cut_policy_hash=policy.policy_hash,
                separator_policy_version=LIVE_SRI_SEPARATOR_VERSION,
            )
            after_bound = pre_activation_master.rmp.objective_bound
            bound_gain = (
                None
                if before_bound is None or after_bound is None
                else float(after_bound) - float(before_bound)
            )
            restricted_primal_integral = _primal_lambdas_integral(
                pre_activation_master.rmp.primal_columns
            )
            attempt_commit = bool(
                pre_activation_master.rmp.status
                == "RESTRICTED_RMP_OPTIMAL"
                and (
                    restricted_primal_integral
                    or (
                        bound_gain is not None
                        and bound_gain + 1.0e-12
                        >= float(policy.min_restricted_rmp_gain)
                    )
                )
            )
            attempt = {
                "group_index_1based": group_index,
                "candidate_rank_start_1based": (
                    (group_index - 1) * selection_capacity + 1
                ),
                "candidate_rank_end_1based": (
                    (group_index - 1) * selection_capacity
                    + len(separated.selected)
                ),
                "cut_ids": [
                    row.cut.cut_id for row in separated.selected
                ],
                "status": pre_activation_master.rmp.status,
                "rmp_bound_after_proposed_cuts": after_bound,
                "restricted_rmp_bound_gain": bound_gain,
                "restricted_primal_integral": (
                    restricted_primal_integral
                ),
                "min_restricted_rmp_gain": float(
                    policy.min_restricted_rmp_gain
                ),
                "commit": attempt_commit,
                "certificate_role": (
                    "heuristic_cut_commit_gate_only"
                ),
                "mutates_official_bound": False,
            }
            group_attempts.append(attempt)
            if attempt_commit:
                selected_group = separated
                next_context = attempted_context
                next_lineage = attempted_lineage
                activation = attempted_activation
                commit = True
                break
            if group_index == 1:
                selected_group = separated
                next_context = attempted_context
                next_lineage = attempted_lineage
                activation = attempted_activation

        selected_attempt = next(
            (
                attempt
                for attempt in group_attempts
                if int(attempt["group_index_1based"])
                == (
                    candidate_groups.index(selected_group) + 1
                )
            ),
            group_attempts[0],
        )
        row = {
            "separation_round": separation_round,
            "node_id": str(node_id),
            "depth": int(depth),
            "rmp_bound_before": before_bound,
            **selected_group.to_payload(),
            "activation": activation,
            "pre_activation_screen": {
                key: value
                for key, value in selected_attempt.items()
                if key
                not in {
                    "group_index_1based",
                    "candidate_rank_start_1based",
                    "candidate_rank_end_1based",
                    "cut_ids",
                }
            },
        }
        if policy.candidate_group_screening_enabled:
            row["candidate_group_screening"] = {
                "enabled": True,
                "policy_version": policy.version,
                "group_size": selection_capacity,
                "group_count_limit": candidate_group_count,
                "candidate_window_capacity": (
                    selection_capacity * candidate_group_count
                ),
                "retained_candidate_count": len(
                    separated_pool.selected
                ),
                "attempted_group_count": len(group_attempts),
                "selected_group_index_1based": (
                    candidate_groups.index(selected_group) + 1
                ),
                "acceptance_policy": (
                    "first_integral_or_min_restricted_rmp_gain"
                ),
                "attempts": group_attempts,
            }
        activation["committed"] = commit
        separation_history.append(row)
        if not commit:
            terminal_reason = "RESTRICTED_RMP_GAIN_BELOW_POLICY_THRESHOLD"
            row["terminal_separation"] = True
            row["terminal_reason"] = terminal_reason
            return _bind_live_state(
                engine,
                policy=policy,
                context=context,
                lineage=lineage,
                separation_history=separation_history,
                all_priced_columns=tuple(all_priced.values()),
                terminal_reason=terminal_reason,
            )

        if separation_round > int(policy.max_separation_rounds):
            return _mark_existing_engine_incomplete(
                engine,
                policy=policy,
                context=context,
                lineage=lineage,
                history=separation_history,
                all_priced_columns=tuple(all_priced.values()),
                reason="LIVE_SRI_MAX_SEPARATION_ROUNDS_BEFORE_REOPTIMIZATION",
            )
        context, lineage = next_context, next_lineage
        current_columns = active_columns

    raise AssertionError("unreachable live SRI separation loop")


def _remaining(limit: float | None, started_at: float) -> float | None:
    if limit is None:
        return None
    return max(0.0, float(limit) - (perf_counter() - started_at))


def _candidate_group_separations(
    separated,
    *,
    group_size: int,
    max_group_count: int,
) -> tuple:
    """Partition the retained SRI ranking into fixed, disjoint groups."""

    size = max(0, int(group_size))
    count = max(1, int(max_group_count))
    if size <= 0:
        return tuple()
    retained = tuple(separated.selected)
    groups = []
    for start in range(0, min(len(retained), size * count), size):
        group = retained[start : start + size]
        if not group:
            break
        groups.append(
            replace(
                separated,
                selected=tuple(group),
                selection_capacity=size,
            )
        )
    return tuple(groups)


def _primal_lambdas_integral(rows: Iterable[dict]) -> bool:
    values = tuple(float(row.get("lambda_value") or 0.0) for row in rows)
    return bool(values) and all(
        abs(value) <= 1.0e-7 or abs(value - 1.0) <= 1.0e-7 for value in values
    )


def _bind_live_state(
    engine: dict,
    *,
    policy: LiveSriPolicy,
    context: CutContext,
    lineage: CutLineage,
    separation_history: list[dict],
    all_priced_columns: tuple[JourneyColumn, ...],
    terminal_reason: str,
) -> dict:
    engine["live_sri"] = {
        "schema_version": "lunar_ice_bpc.live_sri_node_loop.v1",
        "policy": policy.to_payload(),
        "live_cut_policy_hash": policy.policy_hash,
        "separator_policy_version": LIVE_SRI_SEPARATOR_VERSION,
        "separation_round_count": len(separation_history),
        "separation_history": separation_history,
        "terminal_separation_completed": bool(separation_history),
        "terminal_reason": str(terminal_reason),
        "active_cut_count": len(context.cuts),
        "active_cut_context_hash": context.active_cut_context_hash,
        "cut_lineage_hash": lineage.cut_lineage_hash,
        "completion_bound_forced_off": not context.empty,
        "completion_bound_forced_off_reason": (
            "active_live_sri_cuts" if not context.empty else ""
        ),
    }
    engine["cut_context"] = context.to_payload()
    engine["cut_count"] = len(context.cuts)
    engine["active_cut_context_hash"] = context.active_cut_context_hash
    engine["cut_lineage"] = lineage.to_payload()
    engine["cut_lineage_hash"] = lineage.cut_lineage_hash
    engine["live_cut_policy_hash"] = policy.policy_hash
    engine["separator_policy_version"] = LIVE_SRI_SEPARATOR_VERSION
    engine["_active_cut_context"] = context
    engine["_cut_lineage"] = lineage
    engine["_all_priced_columns"] = all_priced_columns
    return engine


def _mark_existing_engine_incomplete(
    engine: dict,
    *,
    policy: LiveSriPolicy,
    context: CutContext,
    lineage: CutLineage,
    history: list[dict],
    all_priced_columns: tuple[JourneyColumn, ...],
    reason: str,
) -> dict:
    engine.update(
        {
            "algorithm_status": "BPC_INCOMPLETE_PRICING",
            "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
            "pricing_state": "INCOMPLETE_LIMIT",
            "node_status": "NODE_INCOMPLETE",
            "node_lp_bound_official": False,
            "exact_status": "NOT_SOLVED",
            "fail_closed_reason": reason,
            "note": reason,
        }
    )
    return _bind_live_state(
        engine,
        policy=policy,
        context=context,
        lineage=lineage,
        separation_history=history,
        all_priced_columns=all_priced_columns,
        terminal_reason=reason,
    )


def _incomplete_live_payload(
    data: LunarIceData,
    *,
    policy: LiveSriPolicy,
    context: CutContext,
    lineage: CutLineage,
    history: list[dict],
    all_priced_columns: tuple[JourneyColumn, ...],
    reason: str,
) -> dict:
    return _bind_live_state(
        {
            "schema_version": "lunar_ice_bpc.live_sri_node_loop.v1",
            "task_count": len(data.task_ids),
            "algorithm_status": "BPC_INCOMPLETE_PRICING",
            "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
            "pricing_state": "INCOMPLETE_LIMIT",
            "node_status": "NODE_INCOMPLETE",
            "node_lp_bound": None,
            "node_lp_bound_official": False,
            "exact_status": "NOT_SOLVED",
            "fail_closed_reason": reason,
            "note": reason,
            "history": [],
            "_master": None,
        },
        policy=policy,
        context=context,
        lineage=lineage,
        separation_history=history,
        all_priced_columns=all_priced_columns,
        terminal_reason=reason,
    )
