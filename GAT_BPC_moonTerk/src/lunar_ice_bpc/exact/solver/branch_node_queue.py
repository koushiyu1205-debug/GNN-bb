"""Diagnostic restricted branch-node queue for the journey BPC scaffold."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from lunar_ice_bpc.exact.certificates.node_bound import build_node_bound_certificate
from lunar_ice_bpc.exact.certificates.pricing_certificate import build_pricing_certificate
from lunar_ice_bpc.exact.core.branching import (
    BranchContext,
    branch_context_from_payload,
    filter_journey_columns_by_branch_context,
)
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.master.journey_rmp import manual_journey_reduced_cost, solve_restricted_journey_rmp
from lunar_ice_bpc.exact.pricing.journey_pricing import DirectPricingCache, price_direct_journey_columns
from lunar_ice_bpc.exact.solver.branch_probe import build_branch_probe, build_fractional_branch_probe


@dataclass(frozen=True)
class _QueuedBranchNode:
    node_id: str
    parent_node_id: str | None
    depth: int
    context: BranchContext
    branch_pair: dict | None
    branch_sense: str | None


def run_restricted_branch_node_queue(
    task_ids: Iterable[str],
    columns: Iterable[JourneyColumn],
    *,
    fleet_size: int,
    max_nodes: int = 7,
    max_depth: int = 2,
    max_candidates_per_node: int = 1,
    root_context: BranchContext | dict | None = None,
    data: LunarIceData | None = None,
    direct_pricing_probe_enabled: bool = False,
    direct_pricing_max_tasks: int = 5,
    direct_pricing_max_candidate_sets: int = 2,
    max_pricing_probe_nodes: int = 3,
) -> dict:
    """Evaluate a deterministic branch-node queue over a supplied column pool.

    This is a scaffold for the future journey branch-and-price driver. It only
    solves restricted RMPs over the provided columns and uses support-based
    branch probes, so every bound it reports is diagnostic rather than official.
    """

    ordered_tasks = tuple(str(task_id) for task_id in task_ids)
    pool = tuple(columns)
    root = _coerce_context(root_context)
    max_node_count = max(1, int(max_nodes))
    max_tree_depth = max(0, int(max_depth))
    candidate_limit = max(0, int(max_candidates_per_node))
    pricing_probe_enabled = bool(direct_pricing_probe_enabled and data is not None)
    pricing_probe_nodes_remaining = max(0, int(max_pricing_probe_nodes))
    direct_cache = DirectPricingCache() if pricing_probe_enabled else None
    queue: list[_QueuedBranchNode] = [
        _QueuedBranchNode(
            node_id="node_000",
            parent_node_id=None,
            depth=0,
            context=root,
            branch_pair=None,
            branch_sense=None,
        )
    ]
    seen_contexts = {_context_key(root)}
    next_node_index = 1
    created_node_count = 1
    evaluated_nodes: list[dict] = []
    expanded_node_count = 0
    candidate_total = 0
    node_limit_hit = False

    while queue and len(evaluated_nodes) < max_node_count:
        node = queue.pop(0)
        payload = _evaluate_node(
            node,
            ordered_tasks=ordered_tasks,
            columns=pool,
            fleet_size=int(fleet_size),
            max_candidates=candidate_limit,
            max_depth=max_tree_depth,
            data=data,
            direct_pricing_probe_enabled=pricing_probe_enabled and pricing_probe_nodes_remaining > 0,
            direct_pricing_cache=direct_cache,
            direct_pricing_max_tasks=int(direct_pricing_max_tasks),
            direct_pricing_max_candidate_sets=int(direct_pricing_max_candidate_sets),
        )
        if payload.get("direct_pricing_probe", {}).get("enabled"):
            pricing_probe_nodes_remaining -= 1
        candidate_total += int(payload["branch_probe_reported_candidate_count"] or 0)
        if payload["can_branch"]:
            for child_context, branch_pair, branch_sense in _child_contexts(
                payload["selected_branch_candidate"],
                node.context,
            ):
                key = _context_key(child_context)
                if key in seen_contexts:
                    continue
                if created_node_count >= max_node_count:
                    node_limit_hit = True
                    continue
                child_id = f"node_{next_node_index:03d}"
                next_node_index += 1
                created_node_count += 1
                seen_contexts.add(key)
                queue.append(
                    _QueuedBranchNode(
                        node_id=child_id,
                        parent_node_id=node.node_id,
                        depth=node.depth + 1,
                        context=child_context,
                        branch_pair=branch_pair,
                        branch_sense=branch_sense,
                    )
                )
                payload["child_node_ids"].append(child_id)
            if payload["child_node_ids"]:
                expanded_node_count += 1
        evaluated_nodes.append(payload)

    objective_values = [
        float(node["restricted_rmp_objective_bound"])
        for node in evaluated_nodes
        if node.get("restricted_rmp_objective_bound") is not None
    ]
    pricing_probe_nodes = [node for node in evaluated_nodes if node.get("direct_pricing_probe", {}).get("enabled")]
    branch_feasible_negative_count = sum(
        1 for node in pricing_probe_nodes if node.get("direct_pricing_probe", {}).get("branch_feasible_negative_found")
    )
    post_pricing_nodes = [
        node for node in evaluated_nodes if node.get("post_pricing_restricted_rmp", {}).get("evaluated")
    ]
    post_pricing_added_column_count = sum(
        int(node["post_pricing_restricted_rmp"].get("added_column_count") or 0) for node in post_pricing_nodes
    )
    branch_feasible_rc_values = [
        float(node["direct_pricing_probe"]["best_branch_feasible_reduced_cost"])
        for node in pricing_probe_nodes
        if node.get("direct_pricing_probe", {}).get("best_branch_feasible_reduced_cost") is not None
    ]
    post_pricing_values = [
        float(node["post_pricing_restricted_rmp"]["objective_bound"])
        for node in post_pricing_nodes
        if node.get("post_pricing_restricted_rmp", {}).get("objective_bound") is not None
    ]
    node_pricing_certificate_status_counts = _status_counts(
        node.get("pricing_certificate", {}).get("status") for node in evaluated_nodes
    )
    node_bound_certificate_status_counts = _status_counts(
        node.get("node_bound_certificate", {}).get("status") for node in evaluated_nodes
    )
    max_depth_reached = max((int(node["depth"]) for node in evaluated_nodes), default=0)
    return {
        "schema_version": "lunar_ice_bpc.branch_node_queue.v1",
        "status": "RESTRICTED_BRANCH_NODE_QUEUE_EVALUATED" if evaluated_nodes else "NO_BRANCH_QUEUE_NODE",
        "evaluation_scope": "supplied_column_pool_only",
        "node_count": len(evaluated_nodes),
        "evaluated_node_count": len(evaluated_nodes),
        "created_node_count": created_node_count,
        "expanded_node_count": expanded_node_count,
        "open_node_count": len(queue),
        "max_nodes": max_node_count,
        "max_depth": max_tree_depth,
        "max_depth_reached": max_depth_reached,
        "node_limit_hit": bool(node_limit_hit or bool(queue)),
        "branch_candidate_total": candidate_total,
        "restricted_rmp_value_count": len(objective_values),
        "best_restricted_rmp_value": round(min(objective_values), 6) if objective_values else None,
        "direct_pricing_probe_enabled": pricing_probe_enabled,
        "direct_pricing_probe_node_count": len(pricing_probe_nodes),
        "direct_pricing_probe_node_limit": max(0, int(max_pricing_probe_nodes)),
        "branch_feasible_negative_count": branch_feasible_negative_count,
        "best_branch_feasible_reduced_cost": (
            round(min(branch_feasible_rc_values), 9) if branch_feasible_rc_values else None
        ),
        "direct_pricing_probe_can_certify_no_negative": False,
        "post_pricing_restricted_rmp_node_count": len(post_pricing_nodes),
        "post_pricing_added_column_count": post_pricing_added_column_count,
        "post_pricing_restricted_rmp_value_count": len(post_pricing_values),
        "best_post_pricing_restricted_rmp_value": round(min(post_pricing_values), 6) if post_pricing_values else None,
        "post_pricing_lower_bound_official": False,
        "node_pricing_certificate_status_counts": node_pricing_certificate_status_counts,
        "node_pricing_certificate_can_certify_count": sum(
            1 for node in evaluated_nodes if node.get("pricing_certificate", {}).get("can_certify_no_negative")
        ),
        "node_bound_certificate_status_counts": node_bound_certificate_status_counts,
        "node_bound_fail_closed_count": sum(
            1
            for node in evaluated_nodes
            if node.get("node_bound_certificate", {}).get("status") == "NODE_BOUND_FAIL_CLOSED"
        ),
        "node_bound_can_fathom_count": sum(
            1 for node in evaluated_nodes if node.get("node_bound_certificate", {}).get("can_fathom_by_bound")
        ),
        "nodes": evaluated_nodes,
        "exact_status_effect": "none",
        "lower_bound_official": False,
        "mutates_solver": False,
        "can_certify": False,
        "can_fathom_by_bound": False,
        "note": (
            "Diagnostic branch-node queue over a supplied journey-column pool. "
            "It does not run full exact pricing and cannot certify a BPC bound."
        ),
    }


def attach_incumbent_to_branch_node_queue(branch_node_queue: dict, *, incumbent_objective: float | None) -> dict:
    """Refresh node-bound certificates after the incumbent is known.

    The restricted branch-node queue is built before the runner has selected
    the final incumbent. This helper only fills that incumbent into fail-closed
    node-bound artifacts; it does not change node RMP values, pricing evidence,
    or any official-bound status.
    """

    if not isinstance(branch_node_queue, dict) or not branch_node_queue.get("nodes"):
        return branch_node_queue
    payload = dict(branch_node_queue)
    nodes: list[dict] = []
    for node_payload in branch_node_queue.get("nodes", []) or []:
        node_copy = dict(node_payload)
        node_copy["node_bound_certificate"] = _node_bound_certificate_payload_from_payload(
            node_copy,
            incumbent_objective=incumbent_objective,
        )
        nodes.append(node_copy)
    payload["nodes"] = nodes
    payload["incumbent_objective_for_node_bounds"] = _float_or_none(incumbent_objective)
    payload["node_bound_incumbent_attached_count"] = sum(
        1 for node in nodes if node.get("node_bound_certificate", {}).get("incumbent_objective") is not None
    )
    payload["node_bound_incumbent_missing_count"] = sum(
        1 for node in nodes if node.get("node_bound_certificate", {}).get("incumbent_objective") is None
    )
    payload["node_bound_certificate_status_counts"] = _status_counts(
        node.get("node_bound_certificate", {}).get("status") for node in nodes
    )
    payload["node_bound_fail_closed_count"] = sum(
        1 for node in nodes if node.get("node_bound_certificate", {}).get("status") == "NODE_BOUND_FAIL_CLOSED"
    )
    payload["node_bound_can_fathom_count"] = sum(
        1 for node in nodes if node.get("node_bound_certificate", {}).get("can_fathom_by_bound")
    )
    payload["can_fathom_by_bound"] = False
    return payload


def _evaluate_node(
    node: _QueuedBranchNode,
    *,
    ordered_tasks: tuple[str, ...],
    columns: tuple[JourneyColumn, ...],
    fleet_size: int,
    max_candidates: int,
    max_depth: int,
    data: LunarIceData | None,
    direct_pricing_probe_enabled: bool,
    direct_pricing_cache: DirectPricingCache | None,
    direct_pricing_max_tasks: int,
    direct_pricing_max_candidate_sets: int,
) -> dict:
    rmp = solve_restricted_journey_rmp(ordered_tasks, columns, fleet_size=fleet_size, branch_context=node.context)
    filtered_columns = filter_journey_columns_by_branch_context(columns, node.context)
    probe = build_branch_probe(ordered_tasks, filtered_columns, max_candidates=max_candidates)
    fractional_probe = build_fractional_branch_probe(
        ordered_tasks,
        rmp.primal_columns,
        filtered_columns,
        max_candidates=max_candidates,
    )
    fractional_candidates = list(fractional_probe.get("candidates") or [])
    support_candidates = list(probe.get("candidates") or [])
    selected = (
        (fractional_candidates or support_candidates)[0]
        if node.depth < int(max_depth) and (fractional_candidates or support_candidates)
        else None
    )
    selected_source = (
        "fractional_rmp_primal" if node.depth < int(max_depth) and fractional_candidates else "support_pool"
    ) if selected else None
    direct_pricing_probe, returned_columns = _direct_pricing_probe(
        data=data,
        duals=rmp.duals,
        context=node.context,
        enabled=bool(direct_pricing_probe_enabled),
        cache=direct_pricing_cache,
        max_direct_tasks=direct_pricing_max_tasks,
        max_candidate_sets=direct_pricing_max_candidate_sets,
        base_columns=columns,
    )
    post_pricing_rmp = _post_pricing_restricted_rmp_payload(
        task_ids=ordered_tasks,
        base_columns=columns,
        returned_columns=returned_columns,
        fleet_size=fleet_size,
        context=node.context,
        pre_objective_bound=rmp.objective_bound,
    )
    pricing_certificate = _node_pricing_certificate_payload(direct_pricing_probe, rmp.min_reduced_cost)
    node_bound_certificate = _node_bound_certificate_payload(
        node=node,
        context=node.context,
        rmp_objective_bound=rmp.objective_bound,
        pricing_certificate=pricing_certificate,
    )
    return {
        "schema_version": "lunar_ice_bpc.branch_node_queue_node.v1",
        "node_id": node.node_id,
        "parent_node_id": node.parent_node_id,
        "depth": int(node.depth),
        "branch_pair": node.branch_pair,
        "branch_sense": node.branch_sense,
        "branch_context": node.context.to_payload(),
        "column_pool_size": len(filtered_columns),
        "context_filtered_column_count": len(columns) - len(filtered_columns),
        "solve_status": rmp.status,
        "exact_status": rmp.exact_status,
        "restricted_rmp_objective_bound": rmp.objective_bound,
        "active_column_count": rmp.active_column_count,
        "universe_column_count": rmp.universe_column_count,
        "iteration_count": rmp.iteration_count,
        "added_column_count": rmp.added_column_count,
        "min_reduced_cost": rmp.min_reduced_cost,
        "branch_probe_status": probe.get("status"),
        "branch_probe_candidate_count": probe.get("candidate_count"),
        "branch_probe_reported_candidate_count": probe.get("reported_candidate_count"),
        "fractional_branch_probe": fractional_probe,
        "fractional_branch_probe_status": fractional_probe.get("status"),
        "fractional_branch_probe_candidate_count": fractional_probe.get("candidate_count"),
        "fractional_branch_probe_reported_candidate_count": fractional_probe.get("reported_candidate_count"),
        "selected_branch_candidate": selected,
        "selected_branch_candidate_source": selected_source,
        "child_node_ids": [],
        "can_branch": bool(selected),
        "direct_pricing_probe": direct_pricing_probe,
        "post_pricing_restricted_rmp": post_pricing_rmp,
        "pricing_certificate": pricing_certificate,
        "node_bound_certificate": node_bound_certificate,
        "integrality_status": "UNKNOWN_NO_PRIMAL_RMP_SOLUTION",
        "bound_status": (
            "DIAGNOSTIC_RESTRICTED_RMP_VALUE" if rmp.objective_bound is not None else "NO_DIAGNOSTIC_RMP_VALUE"
        ),
        "evaluation_scope": "supplied_column_pool_only",
        "lower_bound_official": False,
        "can_certify": False,
        "can_fathom_by_bound": False,
        "mutates_solver": False,
    }


def _node_pricing_certificate_payload(pricing_probe: dict, rmp_min_reduced_cost: float | None) -> dict:
    pricing_payload = {
        "best_reduced_cost": pricing_probe.get("best_branch_feasible_reduced_cost"),
        "negative_found": pricing_probe.get("branch_feasible_negative_found"),
    }
    rmp_payload = {"min_reduced_cost": rmp_min_reduced_cost}
    return build_pricing_certificate(
        source="branch_node_direct_pricing_probe",
        pricing_payload=pricing_payload,
        rmp_payload=rmp_payload,
        uses_true_dual_bpc_certificate=False,
        pricing_complete=False,
        coverage_complete=False,
        certificate_scope="branch_node_direct_pricing_probe",
    ).to_payload()


def _node_bound_certificate_payload(
    *,
    node: _QueuedBranchNode,
    context: BranchContext,
    rmp_objective_bound: float | None,
    pricing_certificate: dict,
) -> dict:
    bound_ledger = {
        "schema_version": "lunar_ice_bpc.branch_node_bound_ledger.v1",
        "records": [
            {
                "name": "branch_node_restricted_rmp",
                "value": rmp_objective_bound,
                "scope": "supplied_column_pool_only",
                "official_lower_bound": False,
                "certificate_status": "RESTRICTED_POOL_DIAGNOSTIC",
                "note": "Diagnostic restricted node RMP value; not an official BPC node bound.",
            }
        ],
    }
    restricted_rmp = {
        "branch_context": context.to_payload(),
        "cut_context": {"cut_count": 0},
    }
    return build_node_bound_certificate(
        incumbent_objective=None,
        bound_ledger=bound_ledger,
        pricing_certificate=pricing_certificate,
        restricted_rmp=restricted_rmp,
        node_id=node.node_id,
        node_depth=node.depth,
    ).to_payload()


def _node_bound_certificate_payload_from_payload(
    node_payload: dict,
    *,
    incumbent_objective: float | None,
) -> dict:
    bound_ledger = {
        "schema_version": "lunar_ice_bpc.branch_node_bound_ledger.v1",
        "records": [
            {
                "name": "branch_node_restricted_rmp",
                "value": node_payload.get("restricted_rmp_objective_bound"),
                "scope": "supplied_column_pool_only",
                "official_lower_bound": False,
                "certificate_status": "RESTRICTED_POOL_DIAGNOSTIC",
                "note": "Diagnostic restricted node RMP value; not an official BPC node bound.",
            }
        ],
    }
    restricted_rmp = {
        "branch_context": node_payload.get("branch_context") or {},
        "cut_context": {"cut_count": 0},
    }
    return build_node_bound_certificate(
        incumbent_objective=incumbent_objective,
        bound_ledger=bound_ledger,
        pricing_certificate=node_payload.get("pricing_certificate") or {},
        restricted_rmp=restricted_rmp,
        node_id=str(node_payload.get("node_id") or "missing"),
        node_depth=int(node_payload.get("depth") or 0),
    ).to_payload()


def _direct_pricing_probe(
    *,
    data: LunarIceData | None,
    duals,
    context: BranchContext,
    enabled: bool,
    cache: DirectPricingCache | None,
    max_direct_tasks: int,
    max_candidate_sets: int,
    base_columns: tuple[JourneyColumn, ...],
) -> tuple[dict, tuple[JourneyColumn, ...]]:
    if not enabled or data is None:
        return {
            "enabled": False,
            "can_certify_no_negative": False,
            "lower_bound_official": False,
        }, tuple()
    pricing, priced_columns = price_direct_journey_columns(
        data,
        duals,
        max_direct_tasks=int(max_direct_tasks),
        max_candidate_sets=max(0, int(max_candidate_sets)),
        cache=cache,
        branch_context=context,
    )
    branch_feasible = filter_journey_columns_by_branch_context(priced_columns, context)
    base_signatures = {_column_signature(column) for column in base_columns}
    rc_by_column = tuple((manual_journey_reduced_cost(column, duals), column) for column in branch_feasible)
    rc_values = [rc for rc, _ in rc_by_column]
    negative_rc_values = [rc for rc in rc_values if rc < -1.0e-6]
    new_negative_columns = tuple(
        column
        for rc, column in rc_by_column
        if rc < -1.0e-6 and _column_signature(column) not in base_signatures
    )
    return {
        "enabled": True,
        "schema_version": "lunar_ice_bpc.branch_node_direct_pricing_probe.v1",
        "status": "BRANCH_NODE_DIRECT_PRICING_PROBED",
        "pricing_status": pricing.get("status"),
        "pricing_exact_status": pricing.get("exact_status"),
        "pricing_complete_for_all_tasks": pricing.get("pricing_complete_for_all_tasks"),
        "pricing_best_reduced_cost": pricing.get("best_reduced_cost"),
        "pricing_negative_found": pricing.get("negative_found"),
        "priced_column_count": len(priced_columns),
        "branch_feasible_priced_column_count": len(branch_feasible),
        "best_branch_feasible_reduced_cost": round(min(rc_values), 9) if rc_values else None,
        "branch_feasible_negative_found": bool(negative_rc_values),
        "branch_feasible_negative_count": len(negative_rc_values),
        "branch_feasible_new_negative_column_count": len(new_negative_columns),
        "max_direct_tasks": int(max_direct_tasks),
        "max_candidate_sets": int(max_candidate_sets),
        "evaluation_scope": "direct_label_probe_filtered_by_branch_context",
        "can_certify_no_negative": False,
        "lower_bound_official": False,
        "note": (
            "Node-level direct pricing probe filtered by BranchContext. Returned columns can reveal "
            "negative reduced cost, but absence of a returned negative column is not a no-negative certificate."
        ),
    }, new_negative_columns


def _post_pricing_restricted_rmp_payload(
    *,
    task_ids: tuple[str, ...],
    base_columns: tuple[JourneyColumn, ...],
    returned_columns: tuple[JourneyColumn, ...],
    fleet_size: int,
    context: BranchContext,
    pre_objective_bound: float | None,
) -> dict:
    if not returned_columns:
        return {
            "enabled": True,
            "evaluated": False,
            "status": "NO_BRANCH_FEASIBLE_NEW_NEGATIVE_COLUMN",
            "added_column_count": 0,
            "objective_bound": None,
            "bound_delta": None,
            "lower_bound_official": False,
            "can_certify": False,
            "can_fathom_by_bound": False,
        }
    augmented_columns = tuple(base_columns) + tuple(returned_columns)
    rmp = solve_restricted_journey_rmp(task_ids, augmented_columns, fleet_size=fleet_size, branch_context=context)
    bound_delta = (
        round(float(rmp.objective_bound) - float(pre_objective_bound), 9)
        if rmp.objective_bound is not None and pre_objective_bound is not None
        else None
    )
    return {
        "enabled": True,
        "evaluated": True,
        "schema_version": "lunar_ice_bpc.branch_node_post_pricing_rmp.v1",
        "status": "POST_PRICING_RESTRICTED_RMP_EVALUATED",
        "solve_status": rmp.status,
        "exact_status": rmp.exact_status,
        "added_column_count": len(returned_columns),
        "objective_bound": rmp.objective_bound,
        "bound_delta": bound_delta,
        "active_column_count": rmp.active_column_count,
        "universe_column_count": rmp.universe_column_count,
        "iteration_count": rmp.iteration_count,
        "min_reduced_cost": rmp.min_reduced_cost,
        "evaluation_scope": "supplied_pool_plus_branch_feasible_direct_negative_columns",
        "lower_bound_official": False,
        "can_certify": False,
        "can_fathom_by_bound": False,
        "note": (
            "Diagnostic one-step node column-generation re-solve. Added columns come from capped "
            "direct pricing and do not prove full no-negative coverage."
        ),
    }


def _child_contexts(candidate: dict | None, parent: BranchContext) -> tuple[tuple[BranchContext, dict, str], ...]:
    if not candidate:
        return tuple()
    task_a = str(candidate["task_a"])
    task_b = str(candidate["task_b"])
    rows: list[tuple[BranchContext, dict, str]] = []
    for sense, key in (("same_journey", "same_child_context"), ("different_journey", "different_child_context")):
        child = branch_context_from_payload(candidate.get(key) or {})
        context = BranchContext(tuple(parent.pair_decisions) + tuple(child.pair_decisions))
        rows.append((context, {"task_a": task_a, "task_b": task_b}, sense))
    return tuple(rows)


def _coerce_context(context: BranchContext | dict | None) -> BranchContext:
    if isinstance(context, BranchContext):
        return context
    if isinstance(context, dict):
        return branch_context_from_payload(context)
    return BranchContext()


def _context_key(context: BranchContext) -> tuple[tuple[str, str, str], ...]:
    return tuple(sorted(decision.key for decision in context.pair_decisions))


def _column_signature(column: JourneyColumn) -> tuple:
    return tuple(
        tuple((leg.source, leg.target, leg.path_type) for leg in sortie.legs)
        for sortie in column.sorties
    )


def _status_counts(values: Iterable[object]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "missing")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None
