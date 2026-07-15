"""B3 branch-and-price tree baseline with certificate-gated closure."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from time import perf_counter
from typing import Iterable

from lunar_ice_bpc.exact.bpc.certificates.certificate_ledger import CertificateLedger
from lunar_ice_bpc.exact.bpc.certificates.proof_debt_queue import ProofDebtQueue
from lunar_ice_bpc.exact.bpc.core.column_pool import BpcColumn, ColumnPool
from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.bpc.core.master_column_view import MasterColumnView
from lunar_ice_bpc.exact.bpc.core.task_index import TaskIndexMap
from lunar_ice_bpc.exact.bpc.master.journey_master import solve_root_journey_master
from lunar_ice_bpc.exact.bpc.pricing.final_judge import run_true_dual_root_final_judge
from lunar_ice_bpc.exact.bpc.pricing.status import AlgorithmStatus, CertificateScope, PricingState
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (
    B2B_R3_MODE,
    DIRECT_LABEL_WORKER,
    solve_b2_pricing_tail_baseline,
    solve_node_pricing_with_b2b_r3,
)
from lunar_ice_bpc.exact.core.branching import (
    DIFFERENT_JOURNEY,
    SAME_JOURNEY,
    BranchContext,
    PairBranchDecision,
    journey_satisfies_branch_context,
)
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.core.objective import aggregate_journey_objective_breakdown
from lunar_ice_bpc.exact.master.journey_rmp import manual_journey_reduced_cost
from lunar_ice_bpc.exact.pricing.journey_pricing import DirectPricingCache
from lunar_ice_bpc.exact.solver.branch_probe import build_fractional_branch_probe
from lunar_ice_bpc.exact.solver.column_pool import select_journey_column_pool
from lunar_ice_bpc.exact.solver.journey_driver import (
    DirectBaselineTimeLimitExceeded,
    enumerate_direct_journey_columns,
    _reference_solution_upper_bound,
    solve_direct_journey_baseline,
)


B3_COMPLETE_UNIVERSE_NODE_MODE = "B3_complete_universe_branch_rc_audit"
TASK_SUBSET_REPRESENTATIVE_UNIVERSE_SEMANTICS = "best_task_subset_representative_fixed_graph_columns"
TREE_OBJECTIVE_TOLERANCE = 5.0e-6
CERTIFYING_PRICING_PROOF_KINDS = frozenset(
    {
        "EXHAUSTIVE_NO_NEGATIVE",
        "FRONTIER_BOUND_NO_NEGATIVE",
    }
)


@dataclass(frozen=True)
class _QueuedNode:
    node_id: str
    parent_node_id: str | None
    depth: int
    context: BranchContext
    branch_pair: dict | None = None
    branch_sense: str | None = None
    # A certified parent LP bound remains a valid lower bound for every child,
    # including a child that has not yet been processed or whose own pricing
    # search ends incomplete.
    inherited_lower_bound: float | None = None


def solve_b3_branch_price_tree_baseline(
    data: LunarIceData,
    *,
    initial_columns: Iterable[JourneyColumn] | None = None,
    b0_direct=None,
    max_direct_tasks: int = 5,
    max_rounds_per_node: int = 16,
    wall_time_limit_sec: float | None = None,
    max_tree_nodes: int = 31,
    max_branch_depth: int = 4,
    negative_eps: float = 1.0e-6,
    max_columns_per_round: int = 512,
    use_complete_universe_audit: bool = True,
    run_b2_root_diagnostic: bool | None = None,
    solve_b0_direct_first: bool = True,
    tail_dual_stabilization_enabled: bool = False,
    tail_dual_stabilization_alpha: float = 0.7,
    tail_dual_stabilization_window: int = 5,
    worker_pricer_kind: str = DIRECT_LABEL_WORKER,
    labeling_final_judge_enabled: bool | None = None,
    labeling_final_judge_max_exact_tasks: int | None = None,
    labeling_final_judge_exact_harvest_target: int | None = None,
) -> dict:
    """Run B3 = B2 plus a proof-gated branch-and-price tree.

    The first B3 version uses Ryan-Foster same/different-journey branching only.
    Direct DP may supply a feasible incumbent for pruning, but never supplies a
    BPC certificate or tree-closure proof.

    ``complete_universe`` is a compatibility name. The audited column set is the
    objective-best fixed-graph representative for every nonempty task subset,
    not every route variant for that subset. That representation is exact here
    because B3 has no route-dependent cuts or route-order branching.
    """

    tree_started_at = perf_counter()
    tree_deadline = (
        None
        if wall_time_limit_sec is None
        else tree_started_at + max(0.0, float(wall_time_limit_sec))
    )

    def remaining_tree_time() -> float | None:
        if tree_deadline is None:
            return None
        return max(0.0, tree_deadline - perf_counter())

    if run_b2_root_diagnostic is None:
        run_b2_root_diagnostic = len(data.task_ids) <= 10
    if run_b2_root_diagnostic:
        b2 = solve_b2_pricing_tail_baseline(
            data,
            max_direct_tasks=max_direct_tasks,
            max_rounds=max_rounds_per_node,
            wall_time_limit_sec=remaining_tree_time(),
            negative_eps=negative_eps,
            max_columns_per_round=max_columns_per_round,
            mode=B2B_R3_MODE,
            tail_dual_stabilization_enabled=tail_dual_stabilization_enabled,
            tail_dual_stabilization_alpha=tail_dual_stabilization_alpha,
            tail_dual_stabilization_window=tail_dual_stabilization_window,
            worker_pricer_kind=worker_pricer_kind,
            labeling_final_judge_enabled=labeling_final_judge_enabled,
            labeling_final_judge_max_exact_tasks=labeling_final_judge_max_exact_tasks,
            labeling_final_judge_exact_harvest_target=labeling_final_judge_exact_harvest_target,
        )
    else:
        b2 = _b2_not_run_payload(data, max_direct_tasks=max_direct_tasks)
    provided_initial_columns = tuple(initial_columns or tuple())
    if b0_direct is None and bool(solve_b0_direct_first):
        b0_direct = solve_direct_journey_baseline(
            data,
            max_exact_tasks=int(max_direct_tasks),
            wall_time_limit_sec=remaining_tree_time(),
        )
    elif b0_direct is None:
        b0_direct = _bpc_tree_placeholder_direct(data)
    if len(data.task_ids) > int(max_direct_tasks):
        return _too_large_payload(
            data=data,
            b2=b2,
            b0_direct=b0_direct,
            max_direct_tasks=max_direct_tasks,
            negative_eps=negative_eps,
            issue="task_count_exceeds_exhaustive_pricing_limit",
            note=f"task_count={len(data.task_ids)} exceeds max_direct_tasks={max_direct_tasks}; B3 fails closed.",
        )
    if not provided_initial_columns and _float_or_none(b0_direct.objective) is None:
        return _too_large_payload(
            data=data,
            b2=b2,
            b0_direct=b0_direct,
            max_direct_tasks=max_direct_tasks,
            negative_eps=negative_eps,
            issue="direct_dp_incumbent_missing",
            note=(
                "B3 fails closed before representative-universe enumeration because "
                f"direct DP did not produce a fixed-graph incumbent: {getattr(b0_direct, 'note', '')}"
            ),
        )

    complete_universe_columns: tuple[JourneyColumn, ...] = tuple()
    complete_universe_counts: dict | None = None
    if provided_initial_columns:
        complete_universe_columns = provided_initial_columns
        complete_universe_counts = {
            "provided_initial_column_count": len(provided_initial_columns),
            "column_universe_semantics": "provided_bpc_tree_initial_columns",
        }
        use_complete_universe_audit = False
    elif use_complete_universe_audit:
        deadline = None
        if wall_time_limit_sec is not None:
            deadline = perf_counter() + max(0.001, float(remaining_tree_time() or 0.0))
        try:
            complete_universe = enumerate_direct_journey_columns(
                data,
                max_exact_tasks=int(max_direct_tasks),
                deadline=deadline,
            )
        except DirectBaselineTimeLimitExceeded as exc:
            return _too_large_payload(
                data=data,
                b2=b2,
                b0_direct=b0_direct,
                max_direct_tasks=max_direct_tasks,
                negative_eps=negative_eps,
                issue="representative_universe_enumeration_time_limit",
                note=(
                    "B3 fails closed because representative-universe enumeration exceeded "
                    f"wall_time_limit_sec={wall_time_limit_sec} during {exc.stage}; "
                    f"generated_journey_count={exc.generated_journey_count}, "
                    f"generated_sortie_count={exc.generated_sortie_count}, "
                    f"route_template_count={exc.route_template_count}, "
                    f"pareto_label_count={exc.pareto_label_count}."
                ),
            )
        complete_universe_columns = tuple(complete_universe.columns)
        complete_universe_counts = {
            "generated_sortie_count": complete_universe.generated_sortie_count,
            "route_template_count": complete_universe.route_template_count,
            "pareto_label_count": complete_universe.pareto_label_count,
        }

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
    tree_deadline_hit = False
    global_columns_by_signature = {
        column_signature_from_journey(column): column
        for column in complete_universe_columns
    }
    globally_shared_column_count = 0
    restricted_mip = _restricted_column_mip_incumbent(
        data,
        tuple(global_columns_by_signature.values()),
        wall_time_limit_sec=(
            10.0
            if remaining_tree_time() is None
            else min(10.0, float(remaining_tree_time()))
        ),
    )
    restricted_mip_objective = _float_or_none(restricted_mip.get("objective"))
    if restricted_mip_objective is not None and (
        incumbent_objective is None
        or restricted_mip_objective < incumbent_objective - abs(float(negative_eps))
    ):
        incumbent_objective = restricted_mip_objective
        incumbent_source = "RESTRICTED_COLUMN_MIP_FEASIBLE_INCUMBENT"
        incumbent_columns = tuple(restricted_mip.get("_columns") or tuple())
    restricted_mip_attempts: list[dict] = [
        {
            "trigger": "initial_pool",
            **{key: value for key, value in restricted_mip.items() if key != "_columns"},
            "improved_incumbent": bool(
                restricted_mip_objective is not None
                and incumbent_source == "RESTRICTED_COLUMN_MIP_FEASIBLE_INCUMBENT"
            ),
        }
    ]

    while queue and len(nodes) < max(1, int(max_tree_nodes)):
        remaining = remaining_tree_time()
        if remaining is not None and remaining <= 1.0e-6:
            tree_deadline_hit = True
            break
        # Process the subtree with the smallest certified inherited bound.
        # This is the standard proof-oriented best-bound policy: an incumbent
        # is already supplied/refreshed by the restricted-column MIP, so
        # spending the whole deadline down one higher-bound DFS branch can
        # leave the true global lower-bound subtree untouched.  Prefer depth
        # only when bounds tie; insertion order then keeps same/different child
        # ordering deterministic.
        queue_index = min(
            range(len(queue)),
            key=lambda index: (
                float("-inf")
                if queue[index].inherited_lower_bound is None
                else float(queue[index].inherited_lower_bound),
                -int(queue[index].depth),
                index,
            ),
        )
        queued = queue.pop(queue_index)
        node_started_at = perf_counter()
        global_count_before = len(global_columns_by_signature)
        node = _solve_b3_node(
            data,
            tuple(global_columns_by_signature.values()),
            queued,
            b0_direct=b0_direct,
            complete_universe_counts=complete_universe_counts,
            use_complete_universe_audit=bool(use_complete_universe_audit and complete_universe_columns),
            incumbent_objective_at_entry=incumbent_objective,
            max_direct_tasks=max_direct_tasks,
            max_rounds=max_rounds_per_node,
            wall_time_limit_sec=remaining,
            negative_eps=negative_eps,
            max_columns_per_round=max_columns_per_round,
            tail_dual_stabilization_enabled=tail_dual_stabilization_enabled,
            tail_dual_stabilization_alpha=tail_dual_stabilization_alpha,
            tail_dual_stabilization_window=tail_dual_stabilization_window,
            worker_pricer_kind=worker_pricer_kind,
            labeling_final_judge_enabled=labeling_final_judge_enabled,
            labeling_final_judge_max_exact_tasks=labeling_final_judge_max_exact_tasks,
            labeling_final_judge_exact_harvest_target=labeling_final_judge_exact_harvest_target,
        )
        node_priced_columns = tuple(node.pop("_all_priced_columns", tuple()) or tuple())
        shared_from_node = 0
        for column in node_priced_columns:
            signature = column_signature_from_journey(column)
            current = global_columns_by_signature.get(signature)
            if current is None:
                global_columns_by_signature[signature] = column
                shared_from_node += 1
            elif column.objective < current.objective - 1.0e-12:
                global_columns_by_signature[signature] = column
        globally_shared_column_count += shared_from_node
        if shared_from_node:
            # Every reconstructed/audited pricing column is a globally feasible
            # physical journey even when it was discovered below a branch node.
            # Re-solving the small restricted set-partition MIP can therefore
            # improve the global upper bound early.  It remains upper-bound
            # only and never participates in node LP or certificate logic.
            mip_remaining = remaining_tree_time()
            periodic_mip = _restricted_column_mip_incumbent(
                data,
                tuple(global_columns_by_signature.values()),
                wall_time_limit_sec=(
                    2.0
                    if mip_remaining is None
                    else min(2.0, float(mip_remaining))
                ),
            )
            periodic_objective = _float_or_none(periodic_mip.get("objective"))
            mip_improved = bool(
                periodic_objective is not None
                and (
                    incumbent_objective is None
                    or periodic_objective
                    < incumbent_objective - abs(float(negative_eps))
                )
            )
            if mip_improved:
                incumbent_objective = periodic_objective
                incumbent_source = f"RESTRICTED_COLUMN_MIP_FEASIBLE_INCUMBENT:{queued.node_id}"
                incumbent_columns = tuple(periodic_mip.get("_columns") or tuple())
            restricted_mip_attempts.append(
                {
                    "trigger": f"after_node:{queued.node_id}",
                    **{
                        key: value
                        for key, value in periodic_mip.items()
                        if key != "_columns"
                    },
                    "improved_incumbent": mip_improved,
                }
            )
        node["tree_node_wall_time_sec"] = round(perf_counter() - node_started_at, 6)
        node["tree_elapsed_sec_at_exit"] = round(perf_counter() - tree_started_at, 6)
        node["tree_global_column_count_at_entry"] = global_count_before
        node["tree_global_column_count_at_exit"] = len(global_columns_by_signature)
        node["tree_globally_shared_new_column_count"] = shared_from_node
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
                                inherited_lower_bound=node_bound,
                            )
                        )
                        node["child_node_ids"].append(child_id)
                    node["selected_branch_candidate_source"] = "ryan_foster_fractional_mass"
        # The pricing-tail engine uses NODE_INCOMPLETE while the tree payload
        # uses INCOMPLETE.  Normalize it here so incomplete-node accounting and
        # certificate telemetry cannot silently omit a timed-out leaf.
        if status == "NODE_INCOMPLETE":
            status = "INCOMPLETE"
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

    if queue and not tree_deadline_hit:
        node_limit_hit = True

    payload = _tree_payload(
        data=data,
        b2=b2,
        b0_direct=b0_direct,
        nodes=nodes,
        open_nodes=tuple(queue),
        incumbent_objective=incumbent_objective,
        incumbent_source=incumbent_source,
        incumbent_columns=incumbent_columns,
        proof_debt=proof_debt,
        node_limit_hit=node_limit_hit,
        max_tree_nodes=max_tree_nodes,
        max_branch_depth=max_branch_depth,
        negative_eps=negative_eps,
    )
    payload["worker_pricer_kind"] = str(worker_pricer_kind)
    payload["tail_dual_stabilization_enabled"] = bool(tail_dual_stabilization_enabled)
    payload["tail_dual_stabilization_alpha"] = float(tail_dual_stabilization_alpha)
    payload["tail_dual_stabilization_window"] = int(tail_dual_stabilization_window)
    payload["labeling_final_judge_enabled"] = labeling_final_judge_enabled
    payload["labeling_final_judge_max_exact_tasks"] = labeling_final_judge_max_exact_tasks
    payload["labeling_final_judge_exact_harvest_target"] = labeling_final_judge_exact_harvest_target
    payload["initial_tree_seed_column_count"] = len(provided_initial_columns)
    payload["tree_seed_source"] = "provided_initial_columns" if provided_initial_columns else "b3_internal_seed"
    payload["solve_b0_direct_first"] = bool(solve_b0_direct_first)
    payload["tree_deadline_hit"] = bool(tree_deadline_hit)
    payload["tree_wall_time_sec"] = round(perf_counter() - tree_started_at, 6)
    payload["tree_global_initial_column_count"] = len(complete_universe_columns)
    payload["tree_global_final_column_count"] = len(global_columns_by_signature)
    payload["tree_globally_shared_new_column_count"] = int(globally_shared_column_count)
    payload["tree_node_selection"] = "best_bound_depth_tiebreak"
    payload["restricted_column_mip"] = {
        key: value for key, value in restricted_mip.items() if key != "_columns"
    }
    payload["restricted_column_mip_attempts"] = restricted_mip_attempts
    payload["restricted_column_mip_attempt_count"] = len(restricted_mip_attempts)
    return payload


def _restricted_column_mip_incumbent(
    data: LunarIceData,
    columns: tuple[JourneyColumn, ...],
    *,
    wall_time_limit_sec: float,
) -> dict:
    """Find an audited feasible set-partition incumbent over known columns.

    This MIP is only an upper-bound heuristic.  It never contributes a lower
    bound or certificate, and every returned selection is rechecked against
    exact task-cover and fleet constraints before it can prune a B&B node.
    """

    started_at = perf_counter()
    if not columns or wall_time_limit_sec <= 0.0:
        return {
            "status": "NOT_RUN",
            "objective": None,
            "selected_column_count": 0,
            "wall_time_sec": round(perf_counter() - started_at, 6),
            "note": "No columns or time remained for the incumbent MIP.",
            "_columns": tuple(),
        }
    try:
        import highspy  # type: ignore[import-not-found]
    except Exception as exc:
        return {
            "status": "BACKEND_UNAVAILABLE",
            "objective": None,
            "selected_column_count": 0,
            "wall_time_sec": round(perf_counter() - started_at, 6),
            "note": repr(exc),
            "_columns": tuple(),
        }

    try:
        task_ids = tuple(str(task_id) for task_id in data.task_ids)
        task_index = {task_id: index for index, task_id in enumerate(task_ids)}
        supports: list[list[int]] = [[] for _ in task_ids]
        for column_index, column in enumerate(columns):
            for task_id in column.task_set:
                supports[task_index[str(task_id)]].append(column_index)
        if any(not support for support in supports):
            return {
                "status": "INFEASIBLE_KNOWN_COLUMN_UNIVERSE",
                "objective": None,
                "selected_column_count": 0,
                "wall_time_sec": round(perf_counter() - started_at, 6),
                "note": "At least one task has no known supporting column.",
                "_columns": tuple(),
            }

        solver = highspy.Highs()
        solver.setOptionValue("output_flag", False)
        solver.setOptionValue("threads", 1)
        solver.setOptionValue("time_limit", max(0.05, float(wall_time_limit_sec)))
        solver.setOptionValue("mip_rel_gap", 0.0)
        column_count = len(columns)
        indices = list(range(column_count))
        status = solver.addCols(
            column_count,
            [float(column.objective) for column in columns],
            [0.0 for _ in columns],
            [1.0 for _ in columns],
            0,
            [],
            [],
            [],
        )
        if str(status) != "HighsStatus.kOk":
            raise RuntimeError(f"addCols failed: {status}")
        status = solver.changeColsIntegrality(
            column_count,
            indices,
            [highspy.HighsVarType.kInteger for _ in columns],
        )
        if str(status) != "HighsStatus.kOk":
            raise RuntimeError(f"changeColsIntegrality failed: {status}")
        for support in supports:
            status = solver.addRow(
                1.0,
                1.0,
                len(support),
                support,
                [1.0 for _ in support],
            )
            if str(status) != "HighsStatus.kOk":
                raise RuntimeError(f"task-cover addRow failed: {status}")
        status = solver.addRow(
            -solver.getInfinity(),
            float(data.fleet_size),
            column_count,
            indices,
            [1.0 for _ in columns],
        )
        if str(status) != "HighsStatus.kOk":
            raise RuntimeError(f"fleet addRow failed: {status}")
        solver.run()
        model_status = solver.modelStatusToString(solver.getModelStatus()).upper()
        values = tuple(float(value) for value in solver.getSolution().col_value[:column_count])
        selected_indices = tuple(index for index, value in enumerate(values) if value >= 0.5)
        selected = tuple(columns[index] for index in selected_indices)

        cover = {task_id: 0 for task_id in task_ids}
        for column in selected:
            for task_id in column.task_set:
                cover[str(task_id)] += 1
        feasible = bool(
            selected
            and len(selected) <= int(data.fleet_size)
            and all(value == 1 for value in cover.values())
            and all(abs(values[index] - 1.0) <= 1.0e-6 for index in selected_indices)
            and all(
                abs(value) <= 1.0e-6 or abs(value - 1.0) <= 1.0e-6
                for value in values
            )
        )
        objective = (
            round(sum(float(column.objective) for column in selected), 9)
            if feasible
            else None
        )
        return {
            "status": f"{model_status}_FEASIBLE" if feasible else model_status,
            "objective": objective,
            "selected_column_count": len(selected) if feasible else 0,
            "known_column_count": column_count,
            "wall_time_sec": round(perf_counter() - started_at, 6),
            "used_as_upper_bound_only": True,
            "_columns": selected if feasible else tuple(),
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "objective": None,
            "selected_column_count": 0,
            "wall_time_sec": round(perf_counter() - started_at, 6),
            "note": repr(exc),
            "_columns": tuple(),
        }


def _solve_b3_node(
    data: LunarIceData,
    universe: tuple[JourneyColumn, ...],
    queued: _QueuedNode,
    *,
    b0_direct=None,
    complete_universe_counts: dict | None = None,
    use_complete_universe_audit: bool = False,
    incumbent_objective_at_entry: float | None,
    max_direct_tasks: int,
    max_rounds: int,
    wall_time_limit_sec: float | None,
    negative_eps: float,
    max_columns_per_round: int,
    tail_dual_stabilization_enabled: bool = False,
    tail_dual_stabilization_alpha: float = 0.7,
    tail_dual_stabilization_window: int = 5,
    worker_pricer_kind: str = DIRECT_LABEL_WORKER,
    labeling_final_judge_enabled: bool | None = None,
    labeling_final_judge_max_exact_tasks: int | None = None,
    labeling_final_judge_exact_harvest_target: int | None = None,
) -> dict:
    if use_complete_universe_audit and universe:
        return _solve_b3_node_with_complete_universe_audit(
            data,
            universe,
            queued,
            b0_direct=b0_direct,
            complete_universe_counts=complete_universe_counts,
            incumbent_objective_at_entry=incumbent_objective_at_entry,
            max_direct_tasks=max_direct_tasks,
            max_rounds=max_rounds,
            negative_eps=negative_eps,
            max_columns_per_round=max_columns_per_round,
            labeling_final_judge_enabled=labeling_final_judge_enabled,
            labeling_final_judge_max_exact_tasks=labeling_final_judge_max_exact_tasks,
            labeling_final_judge_exact_harvest_target=labeling_final_judge_exact_harvest_target,
        )
    initial_columns = tuple(universe) if universe else None
    engine = solve_node_pricing_with_b2b_r3(
        data,
        branch_context=queued.context,
        node_id=queued.node_id,
        initial_columns=initial_columns,
        incumbent_objective=incumbent_objective_at_entry,
        max_direct_tasks=max_direct_tasks,
        max_rounds=max_rounds,
        wall_time_limit_sec=wall_time_limit_sec,
        negative_eps=negative_eps,
        max_columns_per_round=max_columns_per_round,
        b0_direct=b0_direct,
        tail_dual_stabilization_enabled=tail_dual_stabilization_enabled,
        tail_dual_stabilization_alpha=tail_dual_stabilization_alpha,
        tail_dual_stabilization_window=tail_dual_stabilization_window,
        worker_pricer_kind=worker_pricer_kind,
        labeling_final_judge_enabled=labeling_final_judge_enabled,
        labeling_final_judge_max_exact_tasks=labeling_final_judge_max_exact_tasks,
        labeling_final_judge_exact_harvest_target=labeling_final_judge_exact_harvest_target,
    )
    node = _node_payload(
        data=data,
        queued=queued,
        loaded_count=int(engine.get("loaded_column_count") or 0),
        filtered_count=int(engine.get("branch_filtered_column_count") or 0),
        history=list(engine.get("history") or []),
        round_count=int(engine.get("pricing_round_count") or 0),
        added_column_count=int(engine.get("added_column_count") or 0),
        master=engine.get("_master"),
        final_judge=engine.get("final_judge") or {},
        final_judge_columns=tuple(engine.get("_all_priced_columns") or tuple()),
        incumbent_objective_at_entry=incumbent_objective_at_entry,
        certificate_scope=CertificateScope(str(engine.get("certificate_scope"))),
        pricing_state=PricingState(str(engine.get("pricing_state"))),
        node_status=str(engine.get("node_status") or "INCOMPLETE"),
        note=str(engine.get("note") or "B2B_R3 node pricing did not close; fail closed."),
        integer_candidate_columns=None,
    )
    node["_all_priced_columns"] = tuple(engine.get("_all_priced_columns") or tuple())
    return node


def _solve_b3_node_with_complete_universe_audit(
    data: LunarIceData,
    complete_universe_columns: tuple[JourneyColumn, ...],
    queued: _QueuedNode,
    *,
    b0_direct,
    complete_universe_counts: dict | None,
    incumbent_objective_at_entry: float | None,
    max_direct_tasks: int,
    max_rounds: int,
    negative_eps: float,
    max_columns_per_round: int,
    labeling_final_judge_enabled: bool | None,
    labeling_final_judge_max_exact_tasks: int | None,
    labeling_final_judge_exact_harvest_target: int | None,
) -> dict:
    """Close a branch node by RMP plus RC audit over task-subset representatives."""

    pool = ColumnPool()
    view = MasterColumnView()
    seed_columns = _seed_columns_for_complete_universe_node(data, complete_universe_columns, queued, b0_direct)
    loaded_count, filtered_count = _load_context_columns(pool, view, seed_columns, queued)
    history: list[dict] = []
    added_total = 0
    cache = DirectPricingCache()
    last_master = None
    last_judge = None
    last_final_judge_columns: tuple[JourneyColumn, ...] = tuple()
    feasible_seed_repaired = False

    for round_index in range(1, max(1, int(max_rounds)) + 1):
        master_columns = _master_columns_for_node(pool, view, queued.node_id)
        master = solve_root_journey_master(
            data,
            master_columns,
            negative_eps=negative_eps,
            rmp_iteration_id=f"{B3_COMPLETE_UNIVERSE_NODE_MODE}-{queued.node_id}-{round_index}",
            branch_context=queued.context,
        )
        last_master = master
        if master.rmp.status != "RESTRICTED_RMP_OPTIMAL":
            if not feasible_seed_repaired:
                repair = _exact_cover_seed_columns_for_context(data, complete_universe_columns, queued.context)
                feasible_seed_repaired = True
                if repair["status"] == "NO_EXACT_COVER_IN_COLUMN_POOL":
                    return _infeasible_node_payload(
                        data=data,
                        queued=queued,
                        loaded_count=loaded_count,
                        filtered_count=filtered_count,
                        incumbent_objective_at_entry=incumbent_objective_at_entry,
                        complete_universe_columns=complete_universe_columns,
                        master=master,
                        note=(
                            "Branch-filtered task-subset representative universe has no exact cover; "
                            "node is fathomed as infeasible."
                        ),
                    )
                repair_columns = tuple(repair.get("columns") or tuple())
                if not repair_columns:
                    history.append(
                        {
                            "round": round_index,
                            "rmp_status": master.rmp.status,
                            "node_lp_bound": None,
                            "pricing_state": PricingState.INCOMPLETE_LIMIT.value,
                            "final_judge_called": False,
                            "negative_column_count": 0,
                            "added_column_count": 0,
                            "feasible_seed_repair": False,
                            "feasible_seed_repair_status": repair["status"],
                            "branch_context_active": not queued.context.empty,
                            "completion_bound_pruning_enabled": False,
                        }
                    )
                    break
                repaired_loaded, repaired_filtered = _load_context_columns(pool, view, repair_columns, queued)
                loaded_count += repaired_loaded
                filtered_count += repaired_filtered
                history.append(
                    {
                        "round": round_index,
                        "rmp_status": master.rmp.status,
                        "node_lp_bound": None,
                        "pricing_state": PricingState.LOCAL_NO_COLUMN_UNCERTIFIED.value,
                        "final_judge_called": False,
                        "negative_column_count": 0,
                        "added_column_count": repaired_loaded,
                        "feasible_seed_repair": True,
                        "branch_context_active": not queued.context.empty,
                        "completion_bound_pruning_enabled": False,
                    }
                )
                continue
            break
        judge = run_true_dual_root_final_judge(
            data,
            master.reduced_cost_context,
            max_direct_tasks=max_direct_tasks,
            negative_eps=negative_eps,
            cache=cache,
            branch_context=queued.context,
            complete_universe_columns=complete_universe_columns,
            complete_universe_counts=complete_universe_counts,
            column_pool=pool,
            master_view=view,
            node_id=queued.node_id,
            active_task_sets={frozenset(column.task_set) for column in master_columns},
            labeling_final_judge_enabled=labeling_final_judge_enabled,
            labeling_final_judge_max_exact_tasks=labeling_final_judge_max_exact_tasks,
            labeling_final_judge_exact_harvest_target=labeling_final_judge_exact_harvest_target,
        )
        last_judge = judge
        last_final_judge_columns = judge.all_priced_columns
        added = _negative_columns_to_add(
            pool,
            view,
            queued,
            judge.negative_columns,
            master.rmp.duals,
            negative_eps=negative_eps,
            max_columns=max_columns_per_round,
        )
        added_total += added
        history.append(
            {
                "round": round_index,
                "rmp_status": master.rmp.status,
                "node_lp_bound": master.rmp.objective_bound,
                "pricing_state": judge.pricing_state.value,
                "final_judge_called": True,
                "final_judge_source": judge.pricing_payload.get("complete_universe_source"),
                "final_judge_wall_time": judge.pricing_payload.get("final_judge_wall_time"),
                "negative_column_count": len(judge.negative_columns),
                "added_column_count": added,
                "branch_context_active": not queued.context.empty,
                "branch_filtered_column_count": int(judge.pricing_payload.get("branch_filtered_column_count") or 0),
                "complete_universe_raw_column_count": len(complete_universe_columns),
                "column_universe_semantics": TASK_SUBSET_REPRESENTATIVE_UNIVERSE_SEMANTICS,
                "completion_bound_pruning_enabled": False,
            }
        )
        if judge.pricing_state == PricingState.CERTIFIED_NO_NEGATIVE:
            node = _node_payload(
                data=data,
                queued=queued,
                loaded_count=loaded_count,
                filtered_count=max(filtered_count, int(judge.pricing_payload.get("branch_filtered_column_count") or 0)),
                history=history,
                round_count=round_index,
                added_column_count=added_total,
                master=master,
                final_judge=judge.pricing_payload,
                final_judge_columns=judge.all_priced_columns,
                incumbent_objective_at_entry=incumbent_objective_at_entry,
                certificate_scope=CertificateScope.BPC_NODE_LP_CERTIFIED,
                pricing_state=PricingState.CERTIFIED_NO_NEGATIVE,
                node_status="NODE_LP_CERTIFIED",
                note="Node LP bound is certified by task-subset representative membership RC audit under branch context.",
                integer_candidate_columns=_incumbent_columns_for_context(b0_direct, queued.context),
            )
            node["node_pricing_mode"] = B3_COMPLETE_UNIVERSE_NODE_MODE
            node["node_certificate_source"] = "complete_universe_branch_membership_rc_audit"
            node["complete_universe_raw_column_count"] = len(complete_universe_columns)
            node["complete_universe_source"] = judge.pricing_payload.get("complete_universe_source")
            node["column_universe_semantics"] = TASK_SUBSET_REPRESENTATIVE_UNIVERSE_SEMANTICS
            node["complete_universe_contains_all_route_variants"] = False
            node["full_universe_preloaded"] = False
            node["initial_seed_column_count"] = len(seed_columns)
            return node
        if judge.pricing_state == PricingState.FOUND_NEGATIVE and added == 0:
            break

    node = _node_payload(
        data=data,
        queued=queued,
        loaded_count=loaded_count,
        filtered_count=filtered_count,
        history=history,
        round_count=len(history),
        added_column_count=added_total,
        master=last_master,
        final_judge=None if last_judge is None else last_judge.pricing_payload,
        final_judge_columns=last_final_judge_columns,
        incumbent_objective_at_entry=incumbent_objective_at_entry,
        certificate_scope=CertificateScope.DIAGNOSTIC_PRICING_FRONTIER,
        pricing_state=PricingState.INCOMPLETE_LIMIT if last_judge is None else last_judge.pricing_state,
        node_status="INCOMPLETE",
        note="Complete fixed-universe membership RC audit did not certify this node; fail closed.",
        integer_candidate_columns=_incumbent_columns_for_context(b0_direct, queued.context),
    )
    node["node_pricing_mode"] = B3_COMPLETE_UNIVERSE_NODE_MODE
    node["node_certificate_source"] = "complete_universe_branch_membership_rc_audit"
    node["complete_universe_raw_column_count"] = len(complete_universe_columns)
    node["complete_universe_source"] = None if last_judge is None else last_judge.pricing_payload.get("complete_universe_source")
    node["column_universe_semantics"] = TASK_SUBSET_REPRESENTATIVE_UNIVERSE_SEMANTICS
    node["complete_universe_contains_all_route_variants"] = False
    node["full_universe_preloaded"] = False
    node["initial_seed_column_count"] = len(seed_columns)
    return node


def _seed_columns_for_complete_universe_node(
    data: LunarIceData,
    complete_universe_columns: tuple[JourneyColumn, ...],
    queued: _QueuedNode,
    b0_direct,
) -> tuple[JourneyColumn, ...]:
    candidates: list[JourneyColumn] = []
    candidates.extend(tuple(getattr(b0_direct, "journeys", tuple()) or tuple()))
    candidates.extend(column for column in complete_universe_columns if len(column.task_set) == 1)
    unique: list[JourneyColumn] = []
    seen = set()
    for column in candidates:
        if not journey_satisfies_branch_context(column, queued.context):
            continue
        signature = column_signature_from_journey(column)
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(column)
    return tuple(unique)


def _incumbent_columns_for_context(b0_direct, context: BranchContext) -> tuple[JourneyColumn, ...] | None:
    columns = tuple(getattr(b0_direct, "journeys", tuple()) or tuple())
    if not columns:
        return None
    if all(journey_satisfies_branch_context(column, context) for column in columns):
        return columns
    return None


def _exact_cover_seed_columns_for_context(
    data: LunarIceData,
    complete_universe_columns: tuple[JourneyColumn, ...],
    context: BranchContext,
) -> dict:
    selection = _find_feasible_cover_seed_columns(
        data,
        complete_universe_columns,
        context,
        max_expansions=500_000,
    )
    if selection["status"] == "COLUMN_POOL_EXACT_COVER":
        return {
            "status": selection["status"],
            "columns": tuple(selection["columns"]),
            "state_count": int(selection["state_count"]),
            "candidate_column_count": int(selection["candidate_column_count"]),
        }
    if selection["status"] == "NO_EXACT_COVER_IN_COLUMN_POOL":
        return {
            "status": selection["status"],
            "columns": tuple(),
            "state_count": int(selection["state_count"]),
            "candidate_column_count": int(selection["candidate_column_count"]),
        }
    return {
        "status": selection["status"],
        "columns": tuple(),
        "state_count": int(selection["state_count"]),
        "candidate_column_count": int(selection["candidate_column_count"]),
    }


def _find_feasible_cover_seed_columns(
    data: LunarIceData,
    complete_universe_columns: tuple[JourneyColumn, ...],
    context: BranchContext,
    *,
    max_expansions: int,
) -> dict:
    """Find any exact cover under a branch context, without optimizing cost."""

    task_index = TaskIndexMap(data.task_ids)
    full_mask = task_index.full_mask
    best_by_mask: dict[int, JourneyColumn] = {}
    for column in complete_universe_columns:
        if not journey_satisfies_branch_context(column, context):
            continue
        mask = 0
        valid = True
        for task_id in column.task_set:
            try:
                mask |= task_index.mask_of(str(task_id))
            except KeyError:
                valid = False
                break
        if not valid or mask == 0:
            continue
        old = best_by_mask.get(mask)
        if old is None or column.objective < old.objective - 1.0e-9:
            best_by_mask[mask] = column

    entries = tuple(
        sorted(
            best_by_mask.items(),
            key=lambda item: (-int(item[0]).bit_count(), item[1].objective, tuple(sorted(item[1].task_set))),
        )
    )
    by_bit: dict[int, list[tuple[int, JourneyColumn]]] = {}
    for mask, column in entries:
        bit = 1
        while bit <= full_mask:
            if mask & bit:
                by_bit.setdefault(bit, []).append((mask, column))
            bit <<= 1

    expansions = 0
    failed: set[tuple[int, int]] = set()

    def first_uncovered_bit(covered: int) -> int:
        remaining = full_mask ^ covered
        return remaining & -remaining

    def dfs(covered: int, chosen: tuple[JourneyColumn, ...]) -> tuple[JourneyColumn, ...] | None:
        nonlocal expansions
        if covered == full_mask:
            return chosen
        if len(chosen) >= int(data.fleet_size):
            return None
        key = (covered, len(chosen))
        if key in failed:
            return None
        expansions += 1
        if expansions > int(max_expansions):
            raise _CoverSearchLimit()
        bit = first_uncovered_bit(covered)
        for mask, column in by_bit.get(bit, []):
            if mask & covered:
                continue
            result = dfs(covered | mask, (*chosen, column))
            if result is not None:
                return result
        failed.add(key)
        return None

    try:
        columns = dfs(0, tuple())
    except _CoverSearchLimit:
        return {
            "status": "COLUMN_POOL_STATE_LIMIT",
            "columns": tuple(),
            "state_count": expansions,
            "candidate_column_count": len(best_by_mask),
        }
    if columns is None:
        return {
            "status": "NO_EXACT_COVER_IN_COLUMN_POOL",
            "columns": tuple(),
            "state_count": expansions,
            "candidate_column_count": len(best_by_mask),
        }
    return {
        "status": "COLUMN_POOL_EXACT_COVER",
        "columns": tuple(columns),
        "state_count": expansions,
        "candidate_column_count": len(best_by_mask),
    }


class _CoverSearchLimit(RuntimeError):
    pass


def _infeasible_node_payload(
    *,
    data: LunarIceData,
    queued: _QueuedNode,
    loaded_count: int,
    filtered_count: int,
    incumbent_objective_at_entry: float | None,
    complete_universe_columns: tuple[JourneyColumn, ...],
    master,
    note: str,
) -> dict:
    node_debt = ProofDebtQueue()
    ledger = CertificateLedger(
        algorithm_status=AlgorithmStatus.BPC_INFEASIBLE,
        certificate_scope=CertificateScope.BPC_INFEASIBLE_CERTIFIED,
        pricing_state=PricingState.CERTIFIED_NO_NEGATIVE,
        uses_true_dual_bpc_certificate=False,
    ).validate(proof_debt_queue=node_debt)
    return {
        "schema_version": "lunar_ice_bpc.b3_branch_node.v1",
        "node_id": queued.node_id,
        "parent_node_id": queued.parent_node_id,
        "depth": int(queued.depth),
        "branch_pair": queued.branch_pair,
        "branch_sense": queued.branch_sense,
        "branch_context": queued.context.to_payload(),
        "node_pricing_mode": B3_COMPLETE_UNIVERSE_NODE_MODE,
        "node_certificate_source": "complete_universe_branch_no_cover_audit",
        "node_status": "INFEASIBLE_CERTIFIED",
        "rmp_status": None if master is None else master.rmp.status,
        "pricing_state": PricingState.CERTIFIED_NO_NEGATIVE.value,
        "certificate_scope": CertificateScope.BPC_INFEASIBLE_CERTIFIED.value,
        "uses_true_dual_bpc_certificate": False,
        "certificate_ledger": ledger,
        "proof_debt_queue": node_debt.audit(),
        "loaded_column_count": int(loaded_count),
        "branch_filtered_column_count": int(filtered_count),
        "node_lp_bound": None,
        "node_lp_bound_official": False,
        "round_count": 0,
        "pricing_round_count": 0,
        "added_column_count": 0,
        "rmp_iteration_count": None if master is None else master.rmp.iteration_count,
        "primal_columns": tuple(),
        "primal_integral": False,
        "integer_incumbent": {
            "status": "NODE_INFEASIBLE_NO_INTEGER_INCUMBENT",
            "objective": None,
            "journey_count": 0,
            "candidate_column_count": 0,
            "unique_task_set_count": 0,
            "state_count": 0,
            "matches_node_lp_bound": False,
            "source": "COMPLETE_UNIVERSE_NO_EXACT_COVER",
            "note": note,
        },
        "final_judge": {
            "status": "COMPLETE_UNIVERSE_NO_EXACT_COVER",
            "pricing_state": PricingState.CERTIFIED_NO_NEGATIVE.value,
            "can_certify_no_negative": True,
            "complete_universe_raw_column_count": len(complete_universe_columns),
            "column_universe_semantics": TASK_SUBSET_REPRESENTATIVE_UNIVERSE_SEMANTICS,
            "complete_universe_contains_all_route_variants": False,
            "branch_context": queued.context.to_payload(),
            "note": note,
        },
        "final_judge_status": "COMPLETE_UNIVERSE_NO_EXACT_COVER",
        "final_judge_min_reduced_cost": None,
        "manual_rc_audit_pass": True,
        "pricing_rc_audit_pass": True,
        "all_priced_columns_satisfy_branch_context": True,
        "fractional_branch_probe": {"status": "NOT_EVALUATED_INFEASIBLE_NODE", "candidates": []},
        "fractional_branch_probe_status": "NOT_EVALUATED_INFEASIBLE_NODE",
        "child_node_ids": [],
        "incumbent_objective_at_entry": incumbent_objective_at_entry,
        "incumbent_objective_at_exit": incumbent_objective_at_entry,
        "history": [
            {
                "round": 0,
                "rmp_status": None if master is None else master.rmp.status,
                "pricing_state": PricingState.CERTIFIED_NO_NEGATIVE.value,
                "complete_universe_no_cover_audit": True,
                "branch_context_active": not queued.context.empty,
                "completion_bound_pruning_enabled": False,
            }
        ],
        "completion_bound_pruning_enabled": False,
        "complete_universe_raw_column_count": len(complete_universe_columns),
        "column_universe_semantics": TASK_SUBSET_REPRESENTATIVE_UNIVERSE_SEMANTICS,
        "complete_universe_contains_all_route_variants": False,
        "full_universe_preloaded": False,
        "note": note,
    }


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
    integer_candidate_columns: Iterable[JourneyColumn] | None = None,
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
    final_judge_certifying_proof_kind = _final_judge_has_certifying_proof_kind(final_judge)
    branch_pricing_pass = bool(
        final_judge is None
        or final_judge.get("all_priced_columns_satisfy_branch_context") is True
    )
    issues: list[str] = []
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and not manual_rc_audit_pass:
        issues.append("manual_reduced_cost_audit_failed")
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and not pricing_rc_audit_pass:
        issues.append("pricing_reduced_cost_audit_failed")
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and not final_judge_certifying_proof_kind:
        issues.append("pricing_proof_kind_not_certifying")
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and not branch_pricing_pass:
        issues.append("branch_filtered_pricing_audit_failed")
    requested_certificate_scope = certificate_scope
    requested_pricing_state = pricing_state
    requested_node_status = str(node_status)
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and issues:
        certificate_scope = CertificateScope.DIAGNOSTIC_PRICING_FRONTIER
        pricing_state = PricingState.INCOMPLETE_LIMIT
        node_status = "INCOMPLETE"
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
    primal_context_columns = (
        tuple()
        if master is None
        else _columns_from_primal_context(data, final_judge_columns, master.rmp.primal_columns)
    )
    candidate_columns_for_integer = (
        tuple(integer_candidate_columns)
        if integer_candidate_columns is not None
        else primal_context_columns
    )
    integer_incumbent = _integer_incumbent_payload(
        data,
        candidate_columns_for_integer,
        node_bound=root_bound,
        negative_eps=1.0e-6,
        primal_columns=tuple() if master is None else master.rmp.primal_columns,
        allow_pool_search=integer_candidate_columns is not None,
    )
    fractional_probe = (
        {"status": "NOT_EVALUATED_INTEGER_NODE", "candidates": []}
        if master is None or bool(integer_incumbent.get("matches_node_lp_bound"))
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
        "node_pricing_mode": B2B_R3_MODE,
        "node_status": str(node_status),
        "requested_node_status": requested_node_status,
        "rmp_status": None if master is None else master.rmp.status,
        "pricing_state": pricing_state.value,
        "certificate_scope": certificate_scope.value,
        "requested_certificate_scope": requested_certificate_scope.value,
        "requested_pricing_state": requested_pricing_state.value,
        "uses_true_dual_bpc_certificate": bool(ledger["uses_true_dual_bpc_certificate"]),
        "certificate_ledger": ledger,
        "proof_debt_queue": node_debt.audit(),
        "loaded_column_count": int(loaded_count),
        "branch_filtered_column_count": int(filtered_count),
        "node_lp_bound": root_bound,
        "node_lp_bound_official": node_bound_official,
        "inherited_parent_lower_bound": queued.inherited_lower_bound,
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
        "pricing_proof_kind": "" if not final_judge else str(final_judge.get("pricing_proof_kind") or ""),
        "underlying_pricing_proof_kind": ""
        if not final_judge
        else str(final_judge.get("underlying_pricing_proof_kind") or ""),
        "final_judge_can_certify_no_negative": bool(
            final_judge and final_judge.get("can_certify_no_negative") is True
        ),
        "final_judge_uses_true_dual_bpc_certificate": bool(
            final_judge and final_judge.get("uses_true_dual_bpc_certificate") is True
        ),
        "final_judge_certifying_proof_kind": bool(final_judge_certifying_proof_kind),
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
    open_nodes: tuple[_QueuedNode, ...] = tuple(),
    open_node_count: int | None = None,
    incumbent_objective: float | None,
    incumbent_source: str,
    incumbent_columns: tuple[JourneyColumn, ...],
    proof_debt: ProofDebtQueue,
    node_limit_hit: bool,
    max_tree_nodes: int,
    max_branch_depth: int,
    negative_eps: float,
) -> dict:
    if open_node_count is None:
        open_node_count = len(open_nodes)
    elif open_nodes and int(open_node_count) != len(open_nodes):
        raise ValueError(
            "open_node_count does not match the supplied open_nodes payload: "
            f"{open_node_count} != {len(open_nodes)}"
        )
    open_node_count = max(0, int(open_node_count))
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
    all_node_pricing_proofs_certifying = bool(nodes) and all(
        bool(node.get("final_judge_certifying_proof_kind"))
        for node in nodes
        if node.get("node_status") not in {"INFEASIBLE_CERTIFIED"}
    )
    leaf_bounds = [
        float(node["node_lp_bound"])
        for node in leaf_nodes
        if node.get("node_lp_bound_official") and node.get("node_lp_bound") is not None
    ]
    unresolved_inherited_bounds = [
        float(node["inherited_parent_lower_bound"])
        for node in incomplete_nodes
        if not node.get("node_lp_bound_official")
        and node.get("inherited_parent_lower_bound") is not None
    ] + [
        float(queued.inherited_lower_bound)
        for queued in open_nodes
        if queued.inherited_lower_bound is not None
    ]
    unresolved_bound_missing = any(
        not node.get("node_lp_bound_official")
        and node.get("inherited_parent_lower_bound") is None
        for node in incomplete_nodes
    ) or any(queued.inherited_lower_bound is None for queued in open_nodes)
    all_valid_bounds = leaf_bounds + unresolved_inherited_bounds
    global_lower_bound = (
        None
        if unresolved_bound_missing or not all_valid_bounds
        else round(min(all_valid_bounds), 9)
    )
    if incumbent_objective is None or global_lower_bound is None:
        global_gap = None
    else:
        raw_gap = float(incumbent_objective) - float(global_lower_bound)
        global_gap = 0.0 if raw_gap <= TREE_OBJECTIVE_TOLERANCE else round(max(0.0, raw_gap), 9)
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
        all_node_pricing_proofs_certifying=all_node_pricing_proofs_certifying,
        node_ledgers_valid=node_ledgers_valid,
        proof_debt=proof_debt,
        negative_eps=negative_eps,
    )
    tree_optimal = not tree_gate_issues
    if tree_optimal:
        algorithm_status = AlgorithmStatus.BPC_OPTIMAL
        certificate_scope = CertificateScope.BPC_TREE_OPTIMAL
        pricing_state = PricingState.CERTIFIED_NO_NEGATIVE
    elif root.get("node_lp_bound_official") and root.get("final_judge_certifying_proof_kind"):
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
        for issue in ledger["issues"]:
            if issue not in tree_gate_issues:
                tree_gate_issues.append(issue)
        tree_optimal = False
        if root.get("node_lp_bound_official") and root.get("final_judge_certifying_proof_kind"):
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
            uses_true_dual_bpc_certificate=certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED,
        ).validate(proof_debt_queue=proof_debt)
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
        "b3_mode": "B3B_seeded_branch_price_tree",
        "node_pricing_mode": root.get("node_pricing_mode") or B2B_R3_MODE,
        "node_pricing_modes": sorted({str(node.get("node_pricing_mode") or "") for node in nodes if node.get("node_pricing_mode")}),
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
        "all_node_pricing_proofs_certifying": bool(all_node_pricing_proofs_certifying),
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
            "direct_dp_objective_breakdown": getattr(b0_direct, "objective_breakdown", None),
            "reference_solution_upper_bound": getattr(b0_direct, "reference_solution_upper_bound", None),
            "reference_solution_upper_bound_source": getattr(
                b0_direct, "reference_solution_upper_bound_source", ""
            ),
            "direct_bound_pruning_root_bound": getattr(b0_direct, "direct_bound_pruning_root_bound", None),
            "direct_bound_pruning_active": getattr(b0_direct, "direct_bound_pruning_active", False),
            "journey_label_bound_pruned_count": getattr(b0_direct, "journey_label_bound_pruned_count", 0),
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
    primal_columns: Iterable[dict] = tuple(),
    allow_pool_search: bool = True,
) -> dict:
    primal_rows = tuple(primal_columns)
    if _primal_lambdas_integral(primal_rows):
        objective = round(sum(float(row.get("objective") or 0.0) * float(row.get("lambda_value") or 0.0) for row in primal_rows), 6)
        matches_bound = bool(
            node_bound is not None
            and abs(float(objective) - float(node_bound)) <= max(abs(float(negative_eps)), TREE_OBJECTIVE_TOLERANCE)
        )
        return {
            "status": "RMP_PRIMAL_INTEGER_EXACT_COVER",
            "objective": objective,
            "journey_count": len(primal_rows),
            "candidate_column_count": len(primal_rows),
            "unique_task_set_count": len({tuple(row.get("tasks", []) or []) for row in primal_rows}),
            "state_count": 0,
            "matches_node_lp_bound": matches_bound,
            "source": "NODE_RMP_PRIMAL_INTEGRAL" if matches_bound else "NODE_RMP_PRIMAL_INTEGRAL_MISMATCH",
            "note": "RMP primal lambdas are integral; no integer column-pool DP was needed.",
            "_columns": tuple(columns),
        }
    if not allow_pool_search:
        return {
            "status": "NODE_LP_FRACTIONAL_NO_INTEGER_POOL_SEARCH",
            "objective": None,
            "journey_count": 0,
            "candidate_column_count": len(tuple(columns)),
            "unique_task_set_count": 0,
            "state_count": 0,
            "matches_node_lp_bound": False,
            "source": "FRACTIONAL_RMP_PRIMAL",
            "note": "RMP primal is fractional; B3 branches instead of running expensive integer DP over the priced universe.",
            "_columns": tuple(),
        }
    candidate_columns = tuple(columns)
    selection = select_journey_column_pool(data.task_ids, candidate_columns, fleet_size=data.fleet_size)
    objective = _float_or_none(selection.objective)
    matches_bound = bool(
        objective is not None
        and node_bound is not None
        and abs(float(objective) - float(node_bound)) <= max(abs(float(negative_eps)), TREE_OBJECTIVE_TOLERANCE)
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
    primal_task_sets = {
        tuple(row.get("tasks", []) or [])
        for row in primal_columns
        if float(row.get("lambda_value") or 0.0) > 1.0e-9
    }
    if not primal_task_sets:
        return tuple()
    if not priced_columns:
        return tuple()
    universe = priced_columns
    selected = []
    seen: set[tuple[str, ...]] = set()
    for column in universe:
        key = tuple(sorted(str(task_id) for task_id in column.task_set))
        if key in primal_task_sets and key not in seen:
            selected.append(column)
            seen.add(key)
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


def _final_judge_has_certifying_proof_kind(final_judge: dict | None) -> bool:
    payload = final_judge or {}
    return bool(
        payload.get("can_certify_no_negative") is True
        and payload.get("uses_true_dual_bpc_certificate") is True
        and payload.get("pricing_rc_audit_pass") is True
        and str(payload.get("pricing_proof_kind") or "") in CERTIFYING_PRICING_PROOF_KINDS
    )


def _tree_gate_issues(
    *,
    tree_closed: bool,
    incumbent_objective: float | None,
    global_lower_bound: float | None,
    all_node_lower_bounds_official: bool,
    all_node_pricing_proofs_certifying: bool,
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
    if not all_node_pricing_proofs_certifying:
        issues.append("node_pricing_proof_kind_not_certifying")
    if global_lower_bound is None:
        issues.append("global_lower_bound_missing")
    elif incumbent_objective is not None and global_lower_bound < incumbent_objective - max(abs(float(negative_eps)), TREE_OBJECTIVE_TOLERANCE):
        issues.append("global_gap_positive")
    if not node_ledgers_valid:
        issues.append("node_certificate_ledger_invalid")
    if proof_debt.block_certificate_if_unreleased():
        issues.append("unreleased_true_rc_negative_proof_debt")
    return issues


def _bpc_tree_placeholder_direct(data: LunarIceData) -> SimpleNamespace:
    """Return a non-certifying direct-baseline placeholder for warm-start trees."""

    return SimpleNamespace(
        status="NOT_RUN",
        exact_status="NOT_RUN",
        objective=None,
        journeys=tuple(),
        generated_journey_count=0,
        generated_sortie_count=0,
        route_template_count=0,
        pareto_label_count=0,
        set_partition_state_count=0,
        note=(
            "Direct DP was intentionally not run; B3 tree was warm-started from "
            "provided active columns."
        ),
        certificate_scope=CertificateScope.FEASIBLE_INCUMBENT_ONLY.value,
        objective_breakdown=None,
        reference_solution_upper_bound=None,
        reference_solution_upper_bound_source="",
        journey_label_bound_pruned_count=0,
        direct_bound_pruning_root_bound=None,
        direct_bound_pruning_active=False,
        instance_id=data.instance_id,
    )


def _b2_not_run_payload(data: LunarIceData, *, max_direct_tasks: int) -> dict:
    return {
        "algorithm_status": "B2_ROOT_DIAGNOSTIC_NOT_RUN",
        "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
        "pricing_state": "NOT_RUN",
        "root_rmp_objective": None,
        "root_lp_bound": None,
        "root_lp_bound_official": False,
        "task_count": len(data.task_ids),
        "max_direct_tasks": int(max_direct_tasks),
        "note": "B2B_R3 root diagnostic was skipped inside B3; B3 node certificates are solved and audited directly.",
    }


def _too_large_payload(
    *,
    data: LunarIceData,
    b2: dict,
    b0_direct,
    max_direct_tasks: int,
    negative_eps: float,
    issue: str = "task_count_exceeds_exhaustive_pricing_limit",
    note: str | None = None,
) -> dict:
    proof_debt = ProofDebtQueue()
    ledger = CertificateLedger(
        algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
        certificate_scope=CertificateScope.FEASIBLE_INCUMBENT_ONLY,
        pricing_state=PricingState.INCOMPLETE_LIMIT,
        uses_true_dual_bpc_certificate=False,
    ).validate(proof_debt_queue=proof_debt)
    direct_objective = _float_or_none(getattr(b0_direct, "objective", None))
    incumbent_objective = direct_objective
    incumbent_source = "B0_DIRECT_DP_FEASIBLE_INCUMBENT" if direct_objective is not None else ""
    incumbent_journey_count = len(tuple(getattr(b0_direct, "journeys", tuple()) or tuple()))
    incumbent_breakdown = getattr(b0_direct, "objective_breakdown", None)
    reference_incumbent = _reference_solution_upper_bound(data)
    if incumbent_objective is None and reference_incumbent is not None:
        incumbent_objective = float(reference_incumbent.objective)
        incumbent_source = f"REFERENCE_FEASIBLE_INCUMBENT:{reference_incumbent.source}"
        incumbent_journey_count = len(tuple(reference_incumbent.journeys))
        incumbent_breakdown = aggregate_journey_objective_breakdown(data, reference_incumbent.journeys)
    reference_upper_bound = (
        float(reference_incumbent.objective)
        if reference_incumbent is not None
        else getattr(b0_direct, "reference_solution_upper_bound", None)
    )
    reference_upper_bound_source = (
        str(reference_incumbent.source)
        if reference_incumbent is not None
        else getattr(b0_direct, "reference_solution_upper_bound_source", "")
    )
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
        "tree_certificate_gate_issues": [str(issue)],
        "task_count": len(data.task_ids),
        "max_direct_tasks": int(max_direct_tasks),
        "node_count": 0,
        "open_node_count": 0,
        "tree_closed": False,
        "all_nodes_fathomed": False,
        "global_lower_bound": None,
        "global_ub": incumbent_objective,
        "incumbent_objective": incumbent_objective,
        "objective_breakdown": incumbent_breakdown,
        "reference_solution_upper_bound": reference_upper_bound,
        "reference_solution_upper_bound_source": reference_upper_bound_source,
        "feasible_incumbent_source": incumbent_source,
        "feasible_incumbent_objective": incumbent_objective,
        "feasible_incumbent_journey_count": incumbent_journey_count,
        "feasible_incumbent_used_as_bpc_certificate": False,
        "integer_incumbent_source": incumbent_source,
        "integer_incumbent_journey_count": incumbent_journey_count,
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
            "direct_dp_objective": direct_objective,
            "direct_dp_objective_breakdown": getattr(b0_direct, "objective_breakdown", None),
            "reference_solution_upper_bound": reference_upper_bound,
            "reference_solution_upper_bound_source": reference_upper_bound_source,
            "direct_bound_pruning_root_bound": getattr(b0_direct, "direct_bound_pruning_root_bound", None),
            "direct_bound_pruning_active": getattr(b0_direct, "direct_bound_pruning_active", False),
            "journey_label_bound_pruned_count": getattr(b0_direct, "journey_label_bound_pruned_count", 0),
            "direct_dp_used_as_bpc_certificate": False,
        },
        "nodes": [],
        "note": note or f"task_count={len(data.task_ids)} exceeds max_direct_tasks={max_direct_tasks}; B3 fails closed.",
        "negative_eps": float(negative_eps),
    }


def _branch_signature(context: BranchContext) -> tuple[str, ...]:
    return tuple(f"{a}:{b}:{sense}" for a, b, sense in (decision.key for decision in context.pair_decisions))


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
