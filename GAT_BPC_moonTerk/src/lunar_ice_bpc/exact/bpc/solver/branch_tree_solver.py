"""B3 branch-and-price tree baseline with certificate-gated closure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from lunar_ice_bpc.exact.bpc.certificates.certificate_ledger import CertificateLedger
from lunar_ice_bpc.exact.bpc.certificates.proof_debt_queue import ProofDebtQueue
from lunar_ice_bpc.exact.bpc.core.column_pool import BpcColumn, ColumnPool
from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.bpc.core.master_column_view import MasterColumnView
from lunar_ice_bpc.exact.bpc.master.journey_master import solve_root_journey_master
from lunar_ice_bpc.exact.bpc.pricing.final_judge import run_true_dual_root_final_judge
from lunar_ice_bpc.exact.bpc.pricing.status import AlgorithmStatus, CertificateScope, PricingState
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import solve_b2_pricing_tail_baseline
from lunar_ice_bpc.exact.core.branching import (
    DIFFERENT_JOURNEY,
    SAME_JOURNEY,
    BranchContext,
    PairBranchDecision,
    journey_satisfies_branch_context,
)
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.master.journey_rmp import manual_journey_reduced_cost
from lunar_ice_bpc.exact.pricing.journey_pricing import DirectPricingCache
from lunar_ice_bpc.exact.solver.branch_probe import build_fractional_branch_probe
from lunar_ice_bpc.exact.solver.column_pool import select_journey_column_pool
from lunar_ice_bpc.exact.solver.journey_driver import (
    enumerate_direct_journey_columns,
    solve_direct_journey_baseline,
)


@dataclass(frozen=True)
class _QueuedNode:
    node_id: str
    parent_node_id: str | None
    depth: int
    context: BranchContext
    branch_pair: dict | None = None
    branch_sense: str | None = None


def solve_b3_branch_price_tree_baseline(
    data: LunarIceData,
    *,
    max_direct_tasks: int = 5,
    max_rounds_per_node: int = 8,
    max_tree_nodes: int = 31,
    max_branch_depth: int = 4,
    negative_eps: float = 1.0e-6,
    max_columns_per_round: int = 64,
) -> dict:
    """Run B3 = B2 plus a proof-gated branch-and-price tree.

    The first B3 version uses Ryan-Foster same/different-journey branching only.
    Direct DP may supply a feasible incumbent for pruning, but never supplies a
    BPC certificate or tree-closure proof.
    """

    b2 = solve_b2_pricing_tail_baseline(
        data,
        max_direct_tasks=max_direct_tasks,
        max_rounds=max_rounds_per_node,
        negative_eps=negative_eps,
        max_columns_per_round=max_columns_per_round,
    )
    b0_direct = solve_direct_journey_baseline(data, max_exact_tasks=int(max_direct_tasks))
    if len(data.task_ids) > int(max_direct_tasks):
        return _too_large_payload(
            data=data,
            b2=b2,
            b0_direct=b0_direct,
            max_direct_tasks=max_direct_tasks,
            negative_eps=negative_eps,
        )

    universe = enumerate_direct_journey_columns(data, max_exact_tasks=int(max_direct_tasks)).columns
    proof_debt = ProofDebtQueue()
    queue: list[_QueuedNode] = [
        _QueuedNode(
            node_id="node_000",
            parent_node_id=None,
            depth=0,
            context=BranchContext(),
        )
    ]
    nodes: list[dict] = []
    next_node_index = 1
    incumbent_objective = _float_or_none(b0_direct.objective)
    incumbent_source = "B0_DIRECT_DP_FEASIBLE_INCUMBENT" if incumbent_objective is not None else ""
    incumbent_columns: tuple[JourneyColumn, ...] = tuple(b0_direct.journeys)
    node_limit_hit = False

    while queue and len(nodes) < max(1, int(max_tree_nodes)):
        queued = queue.pop(0)
        node = _solve_b3_node(
            data,
            universe,
            queued,
            incumbent_objective_at_entry=incumbent_objective,
            max_direct_tasks=max_direct_tasks,
            max_rounds=max_rounds_per_node,
            negative_eps=negative_eps,
            max_columns_per_round=max_columns_per_round,
        )
        status = str(node["node_status"])
        if status == "NODE_LP_CERTIFIED":
            integer_candidate = node.get("integer_incumbent") or {}
            node_bound = _float_or_none(node.get("node_lp_bound"))
            if bool(integer_candidate.get("matches_node_lp_bound")):
                candidate_objective = _float_or_none(integer_candidate.get("objective"))
                if candidate_objective is not None and (
                    incumbent_objective is None
                    or candidate_objective < incumbent_objective - abs(float(negative_eps))
                    or not incumbent_source.startswith("B3_")
                ):
                    incumbent_objective = candidate_objective
                    incumbent_source = f"B3_INTEGER_NODE:{queued.node_id}"
                    incumbent_columns = tuple(integer_candidate.get("_columns") or tuple())
                status = "INTEGER_INCUMBENT"
            elif (
                queued.depth > 0
                and incumbent_objective is not None
                and node_bound is not None
                and node_bound >= incumbent_objective - abs(float(negative_eps))
            ):
                status = "PRUNED_BY_BOUND"
            elif queued.depth >= max(0, int(max_branch_depth)):
                status = "INCOMPLETE"
                node["incomplete_reason"] = "BRANCH_DEPTH_LIMIT"
            else:
                candidate = _selected_fractional_candidate(node)
                if candidate is None:
                    status = "INCOMPLETE"
                    node["incomplete_reason"] = "NO_FRACTIONAL_RF_PAIR"
                    node["no_fractional_rf_pair_is_integrality_proof"] = False
                elif len(nodes) + len(queue) + 2 >= max(1, int(max_tree_nodes)):
                    status = "INCOMPLETE"
                    node["incomplete_reason"] = "TREE_NODE_LIMIT"
                    node_limit_hit = True
                else:
                    status = "BRANCHED"
                    for child_context, branch_sense in _child_contexts(queued.context, candidate):
                        child_id = f"node_{next_node_index:03d}"
                        next_node_index += 1
                        queue.append(
                            _QueuedNode(
                                node_id=child_id,
                                parent_node_id=queued.node_id,
                                depth=queued.depth + 1,
                                context=child_context,
                                branch_pair={
                                    "task_a": str(candidate["task_a"]),
                                    "task_b": str(candidate["task_b"]),
                                },
                                branch_sense=branch_sense,
                            )
                        )
                        node["child_node_ids"].append(child_id)
                    node["selected_branch_candidate_source"] = "ryan_foster_fractional_mass"
        node["node_status"] = status
        node["incumbent_objective_at_exit"] = incumbent_objective
        node["integer_incumbent_source_at_exit"] = incumbent_source
        if "_columns" in (node.get("integer_incumbent") or {}):
            node["integer_incumbent"] = {
                key: value
                for key, value in node["integer_incumbent"].items()
                if key != "_columns"
            }
        nodes.append(node)

    if queue:
        node_limit_hit = True

    return _tree_payload(
        data=data,
        b2=b2,
        b0_direct=b0_direct,
        nodes=nodes,
        open_node_count=len(queue),
        incumbent_objective=incumbent_objective,
        incumbent_source=incumbent_source,
        incumbent_columns=incumbent_columns,
        proof_debt=proof_debt,
        node_limit_hit=node_limit_hit,
        max_tree_nodes=max_tree_nodes,
        max_branch_depth=max_branch_depth,
        negative_eps=negative_eps,
    )


def _solve_b3_node(
    data: LunarIceData,
    universe: tuple[JourneyColumn, ...],
    queued: _QueuedNode,
    *,
    incumbent_objective_at_entry: float | None,
    max_direct_tasks: int,
    max_rounds: int,
    negative_eps: float,
    max_columns_per_round: int,
) -> dict:
    pool = ColumnPool()
    view = MasterColumnView()
    loaded_count, filtered_count = _load_context_columns(pool, view, universe, queued)
    cache = DirectPricingCache()
    history: list[dict] = []
    final_judge_payload: dict | None = None
    last_master = None
    added_total = 0

    for round_index in range(1, int(max_rounds) + 1):
        master_columns = _master_columns_for_node(pool, view, queued.node_id)
        master = solve_root_journey_master(
            data,
            master_columns,
            negative_eps=negative_eps,
            rmp_iteration_id=f"{queued.node_id}-{round_index}",
            branch_context=queued.context,
        )
        last_master = master
        if master.rmp.status != "RESTRICTED_RMP_OPTIMAL":
            return _node_payload(
                data=data,
                queued=queued,
                loaded_count=loaded_count,
                filtered_count=filtered_count,
                history=history,
                round_count=round_index,
                added_column_count=added_total,
                master=master,
                final_judge=None,
                final_judge_columns=tuple(),
                incumbent_objective_at_entry=incumbent_objective_at_entry,
                certificate_scope=CertificateScope.DIAGNOSTIC_RMP_BOUND,
                pricing_state=PricingState.INCOMPLETE_LIMIT,
                node_status="NODE_RMP_INFEASIBLE_UNCERTIFIED",
                note="Node RMP did not solve to optimality; restricted-pool no-cover is not an infeasibility certificate.",
            )
        judge = run_true_dual_root_final_judge(
            data,
            master.reduced_cost_context,
            max_direct_tasks=int(max_direct_tasks),
            negative_eps=negative_eps,
            cache=cache,
            branch_context=queued.context,
        )
        final_judge_payload = judge.pricing_payload
        selected = _negative_columns_to_add(
            pool,
            view,
            queued,
            judge.negative_columns,
            master.rmp.duals,
            negative_eps=negative_eps,
            max_columns=max_columns_per_round,
        )
        added_total += selected
        history.append(
            {
                "round": round_index,
                "rmp_status": master.rmp.status,
                "node_lp_bound": master.rmp.objective_bound,
                "pricing_state": judge.pricing_state.value,
                "negative_column_count": len(judge.negative_columns),
                "added_column_count": selected,
                "branch_context_active": not queued.context.empty,
                "completion_bound_pruning_enabled": False,
            }
        )
        if judge.pricing_state == PricingState.CERTIFIED_NO_NEGATIVE:
            return _node_payload(
                data=data,
                queued=queued,
                loaded_count=loaded_count,
                filtered_count=filtered_count,
                history=history,
                round_count=round_index,
                added_column_count=added_total,
                master=master,
                final_judge=final_judge_payload,
                final_judge_columns=judge.all_priced_columns,
                incumbent_objective_at_entry=incumbent_objective_at_entry,
                certificate_scope=CertificateScope.BPC_NODE_LP_CERTIFIED,
                pricing_state=PricingState.CERTIFIED_NO_NEGATIVE,
                node_status="NODE_LP_CERTIFIED",
                note="Node LP bound is certified by RMP duals plus branch-filtered exhaustive true-dual pricing.",
            )
        if judge.pricing_state == PricingState.FOUND_NEGATIVE and selected == 0:
            break

    return _node_payload(
        data=data,
        queued=queued,
        loaded_count=loaded_count,
        filtered_count=filtered_count,
        history=history,
        round_count=int(max_rounds),
        added_column_count=added_total,
        master=last_master,
        final_judge=final_judge_payload,
        final_judge_columns=tuple(),
        incumbent_objective_at_entry=incumbent_objective_at_entry,
        certificate_scope=CertificateScope.DIAGNOSTIC_PRICING_FRONTIER,
        pricing_state=PricingState.INCOMPLETE_LIMIT,
        node_status="INCOMPLETE",
        note=f"Node pricing did not close after max_rounds={max_rounds}; fail closed.",
    )


def _node_payload(
    *,
    data: LunarIceData,
    queued: _QueuedNode,
    loaded_count: int,
    filtered_count: int,
    history: list[dict],
    round_count: int,
    added_column_count: int,
    master,
    final_judge: dict | None,
    final_judge_columns: tuple[JourneyColumn, ...],
    incumbent_objective_at_entry: float | None,
    certificate_scope: CertificateScope,
    pricing_state: PricingState,
    node_status: str,
    note: str,
) -> dict:
    root_bound = None if master is None else master.rmp.objective_bound
    manual_rc_audit_pass = bool(
        master is not None
        and master.reduced_cost_audit.get("dual_fingerprint_bound_to_rmp") is True
        and (
            master.reduced_cost_audit.get("min_reduced_cost") is None
            or float(master.reduced_cost_audit["min_reduced_cost"]) >= -1.0e-6
        )
    )
    pricing_rc_audit_pass = bool(final_judge and final_judge.get("pricing_rc_audit_pass") is True)
    branch_pricing_pass = bool(
        final_judge is None
        or final_judge.get("all_priced_columns_satisfy_branch_context") is True
    )
    issues: list[str] = []
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and not manual_rc_audit_pass:
        issues.append("manual_reduced_cost_audit_failed")
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and not pricing_rc_audit_pass:
        issues.append("pricing_reduced_cost_audit_failed")
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and not branch_pricing_pass:
        issues.append("branch_filtered_pricing_audit_failed")
    node_debt = ProofDebtQueue()
    ledger = CertificateLedger(
        algorithm_status=AlgorithmStatus.BPC_GAP_AVAILABLE,
        certificate_scope=certificate_scope,
        pricing_state=pricing_state,
        uses_true_dual_bpc_certificate=certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED,
        issues=issues,
    ).validate(proof_debt_queue=node_debt)
    node_bound_official = bool(
        certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED
        and pricing_state == PricingState.CERTIFIED_NO_NEGATIVE
        and ledger["valid"]
    )
    master_columns = tuple() if master is None else _columns_from_primal_context(data, final_judge_columns, master.rmp.primal_columns)
    integer_incumbent = _integer_incumbent_payload(
        data,
        final_judge_columns if final_judge_columns else master_columns,
        node_bound=root_bound,
        negative_eps=1.0e-6,
    )
    fractional_probe = (
        {"status": "NOT_EVALUATED", "candidates": []}
        if master is None
        else build_fractional_branch_probe(
            data.task_ids,
            master.rmp.primal_columns,
            final_judge_columns,
            max_candidates=3,
        )
    )
    return {
        "schema_version": "lunar_ice_bpc.b3_branch_node.v1",
        "node_id": queued.node_id,
        "parent_node_id": queued.parent_node_id,
        "depth": int(queued.depth),
        "branch_pair": queued.branch_pair,
        "branch_sense": queued.branch_sense,
        "branch_context": queued.context.to_payload(),
        "node_status": str(node_status),
        "rmp_status": None if master is None else master.rmp.status,
        "pricing_state": pricing_state.value,
        "certificate_scope": certificate_scope.value,
        "uses_true_dual_bpc_certificate": bool(ledger["uses_true_dual_bpc_certificate"]),
        "certificate_ledger": ledger,
        "proof_debt_queue": node_debt.audit(),
        "loaded_column_count": int(loaded_count),
        "branch_filtered_column_count": int(filtered_count),
        "node_lp_bound": root_bound,
        "node_lp_bound_official": node_bound_official,
        "round_count": int(round_count),
        "pricing_round_count": int(round_count),
        "added_column_count": int(added_column_count),
        "rmp_iteration_count": None if master is None else master.rmp.iteration_count,
        "primal_columns": tuple() if master is None else master.rmp.primal_columns,
        "primal_integral": False if master is None else _primal_lambdas_integral(master.rmp.primal_columns),
        "integer_incumbent": integer_incumbent,
        "final_judge": final_judge or {},
        "final_judge_status": None if not final_judge else final_judge.get("status"),
        "final_judge_min_reduced_cost": None if not final_judge else final_judge.get("best_reduced_cost"),
        "manual_rc_audit_pass": manual_rc_audit_pass,
        "pricing_rc_audit_pass": pricing_rc_audit_pass,
        "all_priced_columns_satisfy_branch_context": branch_pricing_pass,
        "fractional_branch_probe": fractional_probe,
        "fractional_branch_probe_status": fractional_probe.get("status"),
        "child_node_ids": [],
        "incumbent_objective_at_entry": incumbent_objective_at_entry,
        "incumbent_objective_at_exit": incumbent_objective_at_entry,
        "history": list(history),
        "completion_bound_pruning_enabled": False,
        "note": note,
    }


def _tree_payload(
    *,
    data: LunarIceData,
    b2: dict,
    b0_direct,
    nodes: list[dict],
    open_node_count: int,
    incumbent_objective: float | None,
    incumbent_source: str,
    incumbent_columns: tuple[JourneyColumn, ...],
    proof_debt: ProofDebtQueue,
    node_limit_hit: bool,
    max_tree_nodes: int,
    max_branch_depth: int,
    negative_eps: float,
) -> dict:
    root = nodes[0] if nodes else {}
    leaf_nodes = _leaf_nodes(nodes)
    incomplete_nodes = [node for node in nodes if node.get("node_status") == "INCOMPLETE"]
    official_node_count = sum(1 for node in nodes if node.get("node_lp_bound_official"))
    node_ledgers_valid = all(bool(node.get("certificate_ledger", {}).get("valid")) for node in nodes)
    all_node_lower_bounds_official = bool(nodes) and all(
        bool(node.get("node_lp_bound_official"))
        for node in nodes
        if node.get("node_status") not in {"INFEASIBLE_CERTIFIED"}
    )
    leaf_bounds = [
        float(node["node_lp_bound"])
        for node in leaf_nodes
        if node.get("node_lp_bound_official") and node.get("node_lp_bound") is not None
    ]
    global_lower_bound = round(min(leaf_bounds), 9) if leaf_bounds else None
    global_gap = (
        None
        if incumbent_objective is None or global_lower_bound is None
        else round(max(0.0, float(incumbent_objective) - float(global_lower_bound)), 9)
    )
    all_nodes_closed = bool(nodes) and all(
        node.get("node_status") in {"BRANCHED", "INTEGER_INCUMBENT", "PRUNED_BY_BOUND", "INFEASIBLE_CERTIFIED"}
        for node in nodes
    )
    tree_closed = bool(
        nodes
        and not open_node_count
        and not incomplete_nodes
        and all_nodes_closed
        and leaf_nodes
        and all(node.get("node_status") in {"INTEGER_INCUMBENT", "PRUNED_BY_BOUND", "INFEASIBLE_CERTIFIED"} for node in leaf_nodes)
    )
    tree_gate_issues = _tree_gate_issues(
        tree_closed=tree_closed,
        incumbent_objective=incumbent_objective,
        global_lower_bound=global_lower_bound,
        all_node_lower_bounds_official=all_node_lower_bounds_official,
        node_ledgers_valid=node_ledgers_valid,
        proof_debt=proof_debt,
        negative_eps=negative_eps,
    )
    tree_optimal = not tree_gate_issues
    if tree_optimal:
        algorithm_status = AlgorithmStatus.BPC_OPTIMAL
        certificate_scope = CertificateScope.BPC_TREE_OPTIMAL
        pricing_state = PricingState.CERTIFIED_NO_NEGATIVE
    elif root.get("node_lp_bound_official"):
        algorithm_status = AlgorithmStatus.BPC_GAP_AVAILABLE
        certificate_scope = CertificateScope.BPC_NODE_LP_CERTIFIED
        pricing_state = PricingState.CERTIFIED_NO_NEGATIVE
    else:
        algorithm_status = AlgorithmStatus.BPC_INCOMPLETE_PRICING
        certificate_scope = CertificateScope.DIAGNOSTIC_PRICING_FRONTIER
        pricing_state = PricingState.INCOMPLETE_LIMIT
    ledger = CertificateLedger(
        algorithm_status=algorithm_status,
        certificate_scope=certificate_scope,
        pricing_state=pricing_state,
        uses_true_dual_bpc_certificate=certificate_scope in {
            CertificateScope.BPC_NODE_LP_CERTIFIED,
            CertificateScope.BPC_TREE_OPTIMAL,
        },
        issues=[] if tree_optimal else [],
    ).validate(proof_debt_queue=proof_debt)
    if tree_optimal and not ledger["valid"]:
        tree_gate_issues.extend(ledger["issues"])
    root_objective = _float_or_none(root.get("node_lp_bound"))
    b2_objective = _float_or_none(b2.get("root_rmp_objective"))
    direct_objective = _float_or_none(b0_direct.objective)
    objective_diff_vs_b2 = (
        None if root_objective is None or b2_objective is None else round(root_objective - b2_objective, 9)
    )
    incumbent_vs_direct_gap = (
        None
        if incumbent_objective is None or direct_objective is None
        else round(float(incumbent_objective) - float(direct_objective), 9)
    )
    return {
        "schema_version": "lunar_ice_bpc.b3_branch_price_tree_baseline.v1",
        "instance_id": data.instance_id,
        "algorithm_status": algorithm_status.value,
        "certificate_scope": certificate_scope.value,
        "pricing_state": pricing_state.value,
        "exact_status": (
            "BPC_TREE_OPTIMAL"
            if certificate_scope == CertificateScope.BPC_TREE_OPTIMAL and ledger["valid"]
            else (
                "BPC_NODE_LP_CERTIFIED"
                if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and ledger["valid"]
                else "NOT_SOLVED"
            )
        ),
        "uses_true_dual_bpc_certificate": ledger["uses_true_dual_bpc_certificate"],
        "certificate_ledger": ledger,
        "proof_debt_queue": proof_debt.audit(),
        "tree_certificate_gate_issues": tree_gate_issues,
        "task_count": len(data.task_ids),
        "max_tree_nodes": int(max_tree_nodes),
        "max_branch_depth": int(max_branch_depth),
        "node_count": len(nodes),
        "evaluated_node_count": len(nodes),
        "open_node_count": int(open_node_count),
        "closed_node_count": sum(
            1 for node in nodes if node.get("node_status") in {"INTEGER_INCUMBENT", "PRUNED_BY_BOUND", "INFEASIBLE_CERTIFIED"}
        ),
        "expanded_node_count": sum(1 for node in nodes if node.get("node_status") == "BRANCHED"),
        "branch_node_count": sum(1 for node in nodes if node.get("parent_node_id") is not None),
        "branch_count": sum(len(node.get("child_node_ids") or []) for node in nodes),
        "node_limit_hit": bool(node_limit_hit),
        "tree_closed": bool(tree_closed),
        "all_nodes_fathomed": bool(tree_closed),
        "all_node_lower_bounds_official": bool(all_node_lower_bounds_official),
        "all_certificate_ledgers_valid": bool(node_ledgers_valid and ledger["valid"]),
        "global_lb": global_lower_bound,
        "global_lower_bound": global_lower_bound,
        "global_ub": incumbent_objective,
        "incumbent_objective": incumbent_objective,
        "global_gap": global_gap,
        "integer_incumbent_source": incumbent_source,
        "integer_incumbent_journey_count": len(incumbent_columns),
        "root_lp_bound": root_objective,
        "root_lp_bound_official": bool(root.get("node_lp_bound_official")),
        "root_node_status": root.get("node_status"),
        "root_integral": bool(root.get("integer_incumbent", {}).get("matches_node_lp_bound")),
        "root_integral_count": int(bool(root.get("integer_incumbent", {}).get("matches_node_lp_bound"))),
        "root_fractional_count": int(bool(root) and not bool(root.get("integer_incumbent", {}).get("matches_node_lp_bound"))),
        "node_lp_certified_count": official_node_count,
        "integer_incumbent_count": sum(1 for node in nodes if node.get("node_status") == "INTEGER_INCUMBENT"),
        "pruned_by_bound_count": sum(1 for node in nodes if node.get("node_status") == "PRUNED_BY_BOUND"),
        "incomplete_node_count": len(incomplete_nodes),
        "no_fractional_rf_pair_count": sum(
            1 for node in nodes if node.get("incomplete_reason") == "NO_FRACTIONAL_RF_PAIR"
        ),
        "fallback_branch_count": 0,
        "bpc_tree_optimal_count": int(tree_optimal),
        "bpc_node_lp_certified_count": official_node_count,
        "objective_match_direct_dp_count": int(
            incumbent_vs_direct_gap is not None and abs(float(incumbent_vs_direct_gap)) <= abs(float(negative_eps))
        ),
        "completion_bound_pruning_enabled": False,
        "branching_modes": {
            "ryan_foster_same_different_journey": True,
            "signature_forbid_fallback": False,
            "route_order_branch": False,
            "gat_branch_score": False,
            "cuts": False,
        },
        "b2_ablation": {
            "baseline": "B2_ROOT_PRICING_TAIL",
            "b2_algorithm_status": b2.get("algorithm_status"),
            "b2_certificate_scope": b2.get("certificate_scope"),
            "b2_root_rmp_objective": b2_objective,
            "b3_root_lp_bound": root_objective,
            "objective_diff_vs_B2": objective_diff_vs_b2,
            "certificate_scope_diff_vs_B2": (
                ""
                if str(b2.get("certificate_scope")) == certificate_scope.value
                else f"{b2.get('certificate_scope')}->{certificate_scope.value}"
            ),
            "root_integral_instance_result_consistency": bool(
                root.get("integer_incumbent", {}).get("matches_node_lp_bound")
                and objective_diff_vs_b2 == 0.0
            ),
        },
        "b0_ablation": {
            "baseline": "B0_DIRECT_DP_FIXED_GRAPH_ORACLE",
            "direct_dp_status": b0_direct.status,
            "direct_dp_certificate_scope": b0_direct.certificate_scope,
            "direct_dp_objective": direct_objective,
            "direct_dp_used_as_bpc_certificate": False,
            "incumbent_vs_direct_dp_gap": incumbent_vs_direct_gap,
            "objective_match_direct_dp": bool(
                incumbent_vs_direct_gap is not None and abs(float(incumbent_vs_direct_gap)) <= abs(float(negative_eps))
            ),
        },
        "nodes": nodes,
        "note": (
            "B3 tree is closed by official node LP certificates and an integer incumbent."
            if tree_optimal
            else "B3 tree is not closed; node LP certificates remain valid only at their recorded scope."
        ),
    }


def _load_context_columns(
    pool: ColumnPool,
    view: MasterColumnView,
    columns: Iterable[JourneyColumn],
    queued: _QueuedNode,
) -> tuple[int, int]:
    loaded = 0
    filtered = 0
    for column in columns:
        allowed = journey_satisfies_branch_context(column, queued.context)
        if not allowed:
            filtered += 1
            continue
        signature = column_signature_from_journey(column)
        bpc_column = BpcColumn(signature=signature, objective=column.objective, payload=column)
        pool.add(
            bpc_column,
            {
                "is_allowed_by_branch": True,
                "branch_signature": _branch_signature(queued.context),
            },
        )
        stored = pool.get(signature)
        if stored is not None and view.add_from_pool(stored, node_id=queued.node_id, pool=pool):
            loaded += 1
    return loaded, filtered


def _master_columns_for_node(pool: ColumnPool, view: MasterColumnView, node_id: str) -> tuple[JourneyColumn, ...]:
    signatures = view.signatures_by_node.get(str(node_id), set())
    columns: list[JourneyColumn] = []
    for signature in sorted(signatures, key=repr):
        column = pool.get(signature)
        if column is not None and isinstance(column.payload, JourneyColumn):
            columns.append(column.payload)
    return tuple(columns)


def _negative_columns_to_add(
    pool: ColumnPool,
    view: MasterColumnView,
    queued: _QueuedNode,
    columns: Iterable[JourneyColumn],
    duals,
    *,
    negative_eps: float,
    max_columns: int,
) -> int:
    added = 0
    for column in columns:
        if manual_journey_reduced_cost(column, duals) >= -abs(float(negative_eps)):
            continue
        allowed = journey_satisfies_branch_context(column, queued.context)
        signature = column_signature_from_journey(column)
        bpc_column = BpcColumn(signature=signature, objective=column.objective, payload=column)
        node_context = {
            "master_view": view,
            "node_id": queued.node_id,
            "is_allowed_by_branch": allowed,
            "branch_signature": _branch_signature(queued.context),
        }
        report = pool.addability_check(bpc_column, node_context)
        pool.add(bpc_column, node_context)
        stored = pool.get(signature)
        if report.addable and stored is not None and view.add_from_pool(stored, node_id=queued.node_id, pool=pool):
            added += 1
        if added >= max(1, int(max_columns)):
            break
    return added


def _integer_incumbent_payload(
    data: LunarIceData,
    columns: Iterable[JourneyColumn],
    *,
    node_bound: float | None,
    negative_eps: float,
) -> dict:
    candidate_columns = tuple(columns)
    selection = select_journey_column_pool(data.task_ids, candidate_columns, fleet_size=data.fleet_size)
    objective = _float_or_none(selection.objective)
    matches_bound = bool(
        objective is not None
        and node_bound is not None
        and abs(float(objective) - float(node_bound)) <= abs(float(negative_eps))
    )
    return {
        "status": selection.status,
        "objective": objective,
        "journey_count": len(selection.columns),
        "candidate_column_count": selection.candidate_column_count,
        "unique_task_set_count": selection.unique_task_set_count,
        "state_count": selection.state_count,
        "matches_node_lp_bound": matches_bound,
        "source": "NODE_MASTER_COLUMNS" if matches_bound else "NODE_INTEGER_HEURISTIC_ONLY",
        "note": selection.note,
        "_columns": tuple(selection.columns),
    }


def _columns_from_primal_context(
    data: LunarIceData,
    priced_columns: tuple[JourneyColumn, ...],
    primal_columns: tuple[dict, ...],
) -> tuple[JourneyColumn, ...]:
    if priced_columns:
        return priced_columns
    primal_task_sets = {
        tuple(row.get("tasks", []) or [])
        for row in primal_columns
        if float(row.get("lambda_value") or 0.0) > 1.0e-9
    }
    if not primal_task_sets:
        return tuple()
    universe = enumerate_direct_journey_columns(data, max_exact_tasks=len(data.task_ids)).columns
    selected = []
    for column in universe:
        if tuple(sorted(column.task_set)) in primal_task_sets:
            selected.append(column)
    return tuple(selected)


def _primal_lambdas_integral(primal_columns: tuple[dict, ...], *, eps: float = 1.0e-6) -> bool:
    if not primal_columns:
        return False
    for row in primal_columns:
        value = float(row.get("lambda_value") or 0.0)
        if abs(value - round(value)) > abs(float(eps)):
            return False
    return True


def _selected_fractional_candidate(node: dict) -> dict | None:
    candidates = list((node.get("fractional_branch_probe") or {}).get("candidates") or [])
    return candidates[0] if candidates else None


def _child_contexts(root: BranchContext, candidate: dict) -> tuple[tuple[BranchContext, str], ...]:
    task_a = str(candidate["task_a"])
    task_b = str(candidate["task_b"])
    return (
        (
            BranchContext((*root.pair_decisions, PairBranchDecision(task_a, task_b, SAME_JOURNEY))),
            SAME_JOURNEY,
        ),
        (
            BranchContext((*root.pair_decisions, PairBranchDecision(task_a, task_b, DIFFERENT_JOURNEY))),
            DIFFERENT_JOURNEY,
        ),
    )


def _leaf_nodes(nodes: list[dict]) -> list[dict]:
    return [node for node in nodes if not node.get("child_node_ids")]


def _tree_gate_issues(
    *,
    tree_closed: bool,
    incumbent_objective: float | None,
    global_lower_bound: float | None,
    all_node_lower_bounds_official: bool,
    node_ledgers_valid: bool,
    proof_debt: ProofDebtQueue,
    negative_eps: float,
) -> list[str]:
    issues: list[str] = []
    if incumbent_objective is None:
        issues.append("integer_incumbent_missing")
    if not tree_closed:
        issues.append("tree_not_closed")
    if not all_node_lower_bounds_official:
        issues.append("node_lower_bound_not_official")
    if global_lower_bound is None:
        issues.append("global_lower_bound_missing")
    elif incumbent_objective is not None and global_lower_bound < incumbent_objective - abs(float(negative_eps)):
        issues.append("global_gap_positive")
    if not node_ledgers_valid:
        issues.append("node_certificate_ledger_invalid")
    if proof_debt.block_certificate_if_unreleased():
        issues.append("unreleased_true_rc_negative_proof_debt")
    return issues


def _too_large_payload(
    *,
    data: LunarIceData,
    b2: dict,
    b0_direct,
    max_direct_tasks: int,
    negative_eps: float,
) -> dict:
    proof_debt = ProofDebtQueue()
    ledger = CertificateLedger(
        algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
        certificate_scope=CertificateScope.FEASIBLE_INCUMBENT_ONLY,
        pricing_state=PricingState.INCOMPLETE_LIMIT,
        uses_true_dual_bpc_certificate=False,
    ).validate(proof_debt_queue=proof_debt)
    return {
        "schema_version": "lunar_ice_bpc.b3_branch_price_tree_baseline.v1",
        "instance_id": data.instance_id,
        "algorithm_status": AlgorithmStatus.BPC_INCOMPLETE_PRICING.value,
        "certificate_scope": CertificateScope.FEASIBLE_INCUMBENT_ONLY.value,
        "pricing_state": PricingState.INCOMPLETE_LIMIT.value,
        "exact_status": "NOT_SOLVED",
        "uses_true_dual_bpc_certificate": False,
        "certificate_ledger": ledger,
        "proof_debt_queue": proof_debt.audit(),
        "tree_certificate_gate_issues": ["task_count_exceeds_exhaustive_pricing_limit"],
        "task_count": len(data.task_ids),
        "max_direct_tasks": int(max_direct_tasks),
        "node_count": 0,
        "open_node_count": 0,
        "tree_closed": False,
        "all_nodes_fathomed": False,
        "global_lower_bound": None,
        "global_ub": _float_or_none(b0_direct.objective),
        "incumbent_objective": _float_or_none(b0_direct.objective),
        "global_gap": None,
        "root_lp_bound": None,
        "root_lp_bound_official": False,
        "b2_ablation": {
            "baseline": "B2_ROOT_PRICING_TAIL",
            "b2_algorithm_status": b2.get("algorithm_status"),
            "b2_certificate_scope": b2.get("certificate_scope"),
            "objective_diff_vs_B2": None,
        },
        "b0_ablation": {
            "baseline": "B0_DIRECT_DP_FIXED_GRAPH_ORACLE",
            "direct_dp_status": b0_direct.status,
            "direct_dp_certificate_scope": b0_direct.certificate_scope,
            "direct_dp_objective": _float_or_none(b0_direct.objective),
            "direct_dp_used_as_bpc_certificate": False,
        },
        "nodes": [],
        "note": f"task_count={len(data.task_ids)} exceeds max_direct_tasks={max_direct_tasks}; B3 fails closed.",
        "negative_eps": float(negative_eps),
    }


def _branch_signature(context: BranchContext) -> tuple[str, ...]:
    return tuple(f"{a}:{b}:{sense}" for a, b, sense in (decision.key for decision in context.pair_decisions))


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
