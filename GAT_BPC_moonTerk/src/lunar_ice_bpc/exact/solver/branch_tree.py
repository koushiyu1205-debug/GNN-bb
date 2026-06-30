"""Diagnostic branch-tree materialization for future journey BPC nodes."""

from __future__ import annotations

from typing import Iterable

from lunar_ice_bpc.exact.core.branching import (
    BranchContext,
    branch_context_from_payload,
    filter_journey_columns_by_branch_context,
)
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.master.journey_rmp import solve_restricted_journey_rmp


def build_branch_tree_probe(
    columns: Iterable[JourneyColumn],
    branch_probe: dict,
    *,
    root_context: BranchContext | dict | None = None,
    max_branch_pairs: int = 1,
    task_ids: Iterable[str] | None = None,
    fleet_size: int | None = None,
    evaluate_restricted_rmp: bool = False,
    max_child_evaluations: int = 2,
) -> dict:
    """Return root/child branch-node contexts with optional restricted RMP probes.

    The payload is intentionally diagnostic-only. It records the exact
    BranchContext objects that a future branch-and-price node queue would carry,
    and can re-solve child restricted RMPs over the supplied column pool. It
    does not mutate the current solve, price the full journey space, or certify
    a bound.
    """

    pool = tuple(columns)
    root = _coerce_context(root_context)
    candidates = list(branch_probe.get("candidates") or [])[: max(0, int(max_branch_pairs))]
    ordered_tasks = tuple(str(task_id) for task_id in (task_ids or ()))
    evaluation_enabled = bool(evaluate_restricted_rmp and ordered_tasks and fleet_size is not None)
    root_node = _node_payload(
        node_id="root",
        parent_node_id=None,
        depth=0,
        context=root,
        columns=pool,
        branch_pair=None,
        branch_sense=None,
        task_ids=ordered_tasks,
        fleet_size=fleet_size,
        evaluate_restricted_rmp=evaluation_enabled,
    )
    child_nodes: list[dict] = []
    child_evaluations_remaining = max(0, int(max_child_evaluations))
    for pair_index, candidate in enumerate(candidates, start=1):
        task_a = str(candidate["task_a"])
        task_b = str(candidate["task_b"])
        for sense_name, context_key in (
            ("same_journey", "same_child_context"),
            ("different_journey", "different_child_context"),
        ):
            child_context_payload = candidate.get(context_key) or {}
            try:
                child_context = _extend_context(root, branch_context_from_payload(child_context_payload))
                evaluate_child = evaluation_enabled and child_evaluations_remaining > 0
                if evaluate_child:
                    child_evaluations_remaining -= 1
                child_nodes.append(
                    _node_payload(
                        node_id=f"root.{pair_index}.{sense_name}",
                        parent_node_id="root",
                        depth=1,
                        context=child_context,
                        columns=pool,
                        branch_pair={"task_a": task_a, "task_b": task_b},
                        branch_sense=sense_name,
                        task_ids=ordered_tasks,
                        fleet_size=fleet_size,
                        evaluate_restricted_rmp=evaluate_child,
                    )
                )
            except ValueError as exc:
                child_nodes.append(
                    {
                        "schema_version": "lunar_ice_bpc.branch_tree_node.v1",
                        "node_id": f"root.{pair_index}.{sense_name}",
                        "parent_node_id": "root",
                        "depth": 1,
                        "status": "INFEASIBLE_BRANCH_CONTEXT",
                        "branch_pair": {"task_a": task_a, "task_b": task_b},
                        "branch_sense": sense_name,
                        "branch_context": None,
                        "column_pool_size": 0,
                        "context_filtered_column_count": len(pool),
                        "restricted_rmp_evaluated": False,
                        "solve_status": "NOT_SOLVED",
                        "exact_status": "NOT_SOLVED",
                        "bound_status": "NOT_EVALUATED",
                        "restricted_rmp_objective_bound": None,
                        "min_reduced_cost": None,
                        "can_fathom_by_bound": False,
                        "can_certify": False,
                        "mutates_solver": False,
                        "issue": f"{type(exc).__name__}: {exc}",
                    }
                )

    all_nodes = (root_node, *child_nodes)
    evaluated_nodes = [node for node in all_nodes if node.get("restricted_rmp_evaluated")]
    evaluated_children = [node for node in child_nodes if node.get("restricted_rmp_evaluated")]
    child_values = [
        float(node["restricted_rmp_objective_bound"])
        for node in evaluated_children
        if node.get("restricted_rmp_objective_bound") is not None
    ]
    if evaluated_nodes:
        status = "BRANCH_TREE_RESTRICTED_RMP_EVALUATED"
    else:
        status = "BRANCH_TREE_PROBE_READY" if child_nodes else "NO_BRANCH_TREE_CHILD"
    return {
        "schema_version": "lunar_ice_bpc.branch_tree_probe.v1",
        "status": status,
        "node_count": 1 + len(child_nodes),
        "child_count": len(child_nodes),
        "reported_branch_pair_count": len(candidates),
        "restricted_rmp_evaluation_enabled": evaluation_enabled,
        "evaluated_node_count": len(evaluated_nodes),
        "child_evaluated_count": len(evaluated_children),
        "child_restricted_rmp_value_count": len(child_values),
        "best_child_restricted_rmp_value": round(min(child_values), 6) if child_values else None,
        "root_node": root_node,
        "child_nodes": child_nodes,
        "exact_status_effect": "none",
        "mutates_solver": False,
        "can_certify": False,
        "can_fathom_by_bound": False,
        "note": (
            "Diagnostic branch-node context ledger only. Optional child RMP evaluations use "
            "only the supplied column pool and cannot certify bounds or optimality."
        ),
    }


def _coerce_context(context: BranchContext | dict | None) -> BranchContext:
    if isinstance(context, BranchContext):
        return context
    if isinstance(context, dict):
        return branch_context_from_payload(context)
    return BranchContext()


def _extend_context(root: BranchContext, child: BranchContext) -> BranchContext:
    return BranchContext(tuple(root.pair_decisions) + tuple(child.pair_decisions))


def _node_payload(
    *,
    node_id: str,
    parent_node_id: str | None,
    depth: int,
    context: BranchContext,
    columns: tuple[JourneyColumn, ...],
    branch_pair: dict | None,
    branch_sense: str | None,
    task_ids: tuple[str, ...],
    fleet_size: int | None,
    evaluate_restricted_rmp: bool,
) -> dict:
    filtered = filter_journey_columns_by_branch_context(columns, context)
    payload = {
        "schema_version": "lunar_ice_bpc.branch_tree_node.v1",
        "node_id": node_id,
        "parent_node_id": parent_node_id,
        "depth": int(depth),
        "branch_pair": branch_pair,
        "branch_sense": branch_sense,
        "branch_context": context.to_payload(),
        "column_pool_size": len(filtered),
        "context_filtered_column_count": len(columns) - len(filtered),
        "restricted_rmp_evaluated": False,
        "solve_status": "NOT_SOLVED",
        "exact_status": "NOT_SOLVED",
        "bound_status": "NOT_EVALUATED",
        "restricted_rmp_objective_bound": None,
        "active_column_count": None,
        "universe_column_count": len(filtered),
        "iteration_count": None,
        "added_column_count": None,
        "min_reduced_cost": None,
        "evaluation_scope": "supplied_column_pool_only",
        "lower_bound_official": False,
        "can_fathom_by_bound": False,
        "can_certify": False,
        "mutates_solver": False,
    }
    if not evaluate_restricted_rmp:
        payload["status"] = "BRANCH_NODE_CONTEXT_ONLY"
        return payload

    rmp = solve_restricted_journey_rmp(task_ids, columns, fleet_size=int(fleet_size), branch_context=context)
    payload.update(
        {
            "status": "BRANCH_NODE_RESTRICTED_RMP_EVALUATED",
            "restricted_rmp_evaluated": True,
            "solve_status": rmp.status,
            "exact_status": rmp.exact_status,
            "bound_status": (
                "DIAGNOSTIC_RESTRICTED_RMP_VALUE" if rmp.objective_bound is not None else "NO_DIAGNOSTIC_RMP_VALUE"
            ),
            "restricted_rmp_objective_bound": rmp.objective_bound,
            "active_column_count": rmp.active_column_count,
            "universe_column_count": rmp.universe_column_count,
            "iteration_count": rmp.iteration_count,
            "added_column_count": rmp.added_column_count,
            "min_reduced_cost": rmp.min_reduced_cost,
            "context_filtered_column_count": rmp.branch_filtered_column_count,
        }
    )
    return payload
