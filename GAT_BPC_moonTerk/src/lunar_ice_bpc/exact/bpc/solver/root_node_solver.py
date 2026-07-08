"""B1 root-only true-dual BPC baseline."""

from __future__ import annotations

from types import SimpleNamespace
from time import perf_counter
from typing import Iterable

from lunar_ice_bpc.domain.scenario import PATH_TYPES
from lunar_ice_bpc.exact.bpc.certificates.certificate_ledger import CertificateLedger
from lunar_ice_bpc.exact.bpc.certificates.proof_debt_queue import ProofDebtQueue
from lunar_ice_bpc.exact.bpc.core.column_pool import BpcColumn, ColumnPool
from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.bpc.core.master_column_view import MasterColumnView
from lunar_ice_bpc.exact.bpc.master.journey_master import solve_root_journey_master
from lunar_ice_bpc.exact.bpc.pricing.final_judge import run_true_dual_root_final_judge
from lunar_ice_bpc.exact.bpc.pricing.status import AlgorithmStatus, CertificateScope, PricingState
from lunar_ice_bpc.exact.core.columns import build_timed_sortie
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn, build_journey_column
from lunar_ice_bpc.exact.master.journey_rmp import manual_journey_reduced_cost
from lunar_ice_bpc.exact.pricing.journey_pricing import DirectPricingCache
from lunar_ice_bpc.exact.solver.journey_driver import (
    enumerate_canonical_journey_columns,
    enumerate_direct_journey_columns,
    _reference_solution_upper_bound,
    solve_direct_journey_baseline,
)


DEFAULT_DENSE_RMP_TABLEAU_CELL_LIMIT = 50_000_000


def representative_universe_column_count(task_count: int) -> int:
    """Return the task-subset representative universe size, excluding empty set."""

    task_count = int(task_count)
    if task_count < 0:
        raise ValueError("task_count must be nonnegative")
    return (1 << task_count) - 1


def dense_rmp_memory_precheck(
    data: LunarIceData,
    *,
    active_column_count: int,
    cut_count: int = 0,
    cell_limit: int = DEFAULT_DENSE_RMP_TABLEAU_CELL_LIMIT,
    stage: str = "root_active_column_rmp",
) -> dict:
    """Estimate whether the current dense dual-simplex tableau is admissible.

    The current RMP solver builds a Python-list dense tableau with one
    constraint row per active journey column.  Full-universe audit modes can
    therefore become quadratic in active columns.  This precheck is a
    fail-closed guard; it never certifies a bound.
    """

    column_count = max(0, int(active_column_count))
    dual_variable_count = 2 * len(data.task_ids) + 1 + max(0, int(cut_count))
    tableau_width = dual_variable_count + column_count + 1
    tableau_row_count = column_count + 1
    cells = tableau_row_count * tableau_width
    limit = max(1, int(cell_limit))
    failed = cells > limit
    reason = (
        "dense RMP tableau precheck failed before loading active columns: "
        f"estimated_cells={cells} exceeds limit={limit}"
        if failed
        else ""
    )
    return {
        "rmp_memory_precheck_failed": bool(failed),
        "rmp_memory_precheck_stage": str(stage),
        "rmp_memory_precheck_reason": reason,
        "rmp_memory_precheck_estimated_column_count": column_count,
        "rmp_memory_precheck_dual_variable_count": dual_variable_count,
        "rmp_memory_precheck_tableau_width": tableau_width,
        "rmp_memory_precheck_tableau_row_count": tableau_row_count,
        "rmp_memory_precheck_estimated_tableau_cells": cells,
        "rmp_memory_precheck_cell_limit": limit,
        "rmp_memory_precheck_estimated_numeric_bytes": cells * 8,
    }


def solve_b1_root_node_baseline(
    data: LunarIceData,
    *,
    initial_columns: Iterable[JourneyColumn] | None = None,
    b0_direct=None,
    max_direct_tasks: int = 5,
    max_rounds: int = 8,
    wall_time_limit_sec: float | None = None,
    negative_eps: float = 1.0e-6,
    max_columns_per_round: int = 512,
    seed_mode: str = "full_universe",
    solve_b0_direct_first: bool = True,
    return_active_columns_payload: bool = False,
) -> dict:
    """Solve the root BPC baseline on the fixed logical graph.

    This is root-only. It does not branch, separate cuts, call GAT, or use
    completion-bound pruning in the final pricing judge.
    """

    start = perf_counter()
    if initial_columns is None and str(seed_mode) == "full_universe":
        estimated_columns = representative_universe_column_count(len(data.task_ids))
        precheck = dense_rmp_memory_precheck(
            data,
            active_column_count=estimated_columns,
            stage="b1a_full_universe_active_rmp",
        )
        if len(data.task_ids) <= int(max_direct_tasks) and precheck["rmp_memory_precheck_failed"]:
            return _incomplete_payload(
                data=data,
                b0_direct=b0_direct,
                reason=str(precheck["rmp_memory_precheck_reason"]),
                max_direct_tasks=max_direct_tasks,
                b1_mode="B1A_full_universe_root_audit",
                seed_mode="full_universe",
                full_universe_column_count=estimated_columns,
                extra=precheck,
            )
    if b0_direct is None and bool(solve_b0_direct_first):
        b0_direct = solve_direct_journey_baseline(
            data,
            max_exact_tasks=int(max_direct_tasks),
            wall_time_limit_sec=wall_time_limit_sec,
        )
    elif b0_direct is None:
        b0_direct = _reference_seed_direct_placeholder(data)
    if len(data.task_ids) > int(max_direct_tasks):
        return _incomplete_payload(
            data=data,
            b0_direct=b0_direct,
            reason=f"task_count={len(data.task_ids)} exceeds max_direct_tasks={max_direct_tasks}",
            max_direct_tasks=max_direct_tasks,
        )

    seed_columns, seed_report = build_b1_seed_columns(
        data,
        b0_direct=b0_direct,
        initial_columns=initial_columns,
        seed_mode=seed_mode,
        max_direct_tasks=int(max_direct_tasks),
    )
    seed_report = dict(seed_report)
    seed_report["solve_b0_direct_first"] = bool(solve_b0_direct_first)
    pool = ColumnPool()
    view = MasterColumnView()
    _load_columns(pool, view, seed_columns)
    proof_debt = ProofDebtQueue()
    cache = DirectPricingCache()
    history: list[dict] = []
    added_total = 0
    last_master = None
    last_judge = None
    duplicate_only = False

    for round_index in range(1, int(max_rounds) + 1):
        master_columns = _master_columns(pool, view)
        master = solve_root_journey_master(
            data,
            master_columns,
            negative_eps=negative_eps,
            rmp_iteration_id=f"root-{round_index}",
        )
        last_master = master
        if master.rmp.status != "RESTRICTED_RMP_OPTIMAL":
            return _payload(
                data=data,
                b0_direct=b0_direct,
                pool=pool,
                view=view,
                proof_debt=proof_debt,
                history=history,
                round_count=round_index,
                added_column_count=added_total,
                algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
                certificate_scope=CertificateScope.DIAGNOSTIC_RMP_BOUND,
                pricing_state=PricingState.INCOMPLETE_LIMIT,
                master=master,
                final_judge=None,
                seed_report=seed_report,
                include_active_columns=bool(return_active_columns_payload),
                note="Root RMP did not solve to optimality; fail closed.",
            )
        judge = run_true_dual_root_final_judge(
            data,
            master.reduced_cost_context,
            max_direct_tasks=int(max_direct_tasks),
            negative_eps=negative_eps,
            cache=cache,
            wall_time_limit_sec=_remaining_wall_time_limit(wall_time_limit_sec, started_at=start),
            complete_universe_columns=seed_report.get("_full_universe_columns"),
            complete_universe_counts=seed_report.get("_full_universe_counts"),
        )
        last_judge = judge
        added = _add_negative_columns(
            pool,
            view,
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
                "root_lp_bound": master.rmp.objective_bound,
                "active_column_count": master.rmp.active_column_count,
                "pool_column_count": len(pool.columns_by_signature),
                "dual_context": {
                    "dual_fingerprint": master.reduced_cost_context.dual_fingerprint,
                    "rmp_iteration_id": master.reduced_cost_context.rmp_iteration_id,
                    "fleet_dual": master.reduced_cost_context.fleet_dual,
                    "task_duals": dict(master.reduced_cost_context.task_duals),
                    "cut_duals": dict(master.reduced_cost_context.cut_duals),
                },
                "pricing_state": judge.pricing_state.value,
                "final_judge_status": judge.pricing_payload.get("status"),
                "final_judge_exact_status": judge.pricing_payload.get("exact_status"),
                "final_judge_wall_time": judge.pricing_payload.get("final_judge_wall_time"),
                "best_reduced_cost": judge.pricing_payload.get("best_reduced_cost"),
                "dual_bound": judge.pricing_payload.get("dual_bound", judge.pricing_payload.get("bound")),
                "mip_gap": judge.pricing_payload.get("gap"),
                "solver_backend": judge.pricing_payload.get("solver_backend"),
                "model_status_name": judge.pricing_payload.get("model_status_name"),
                "variable_count": judge.pricing_payload.get("variable_count"),
                "constraint_count": judge.pricing_payload.get("constraint_count"),
                "negative_feasibility_search_enabled": bool(
                    judge.pricing_payload.get("negative_feasibility_search_enabled")
                ),
                "mtz_connectivity_enabled": bool(judge.pricing_payload.get("mtz_connectivity_enabled")),
                "mtz_endpoint_order_cuts_enabled": bool(
                    judge.pricing_payload.get("mtz_endpoint_order_cuts_enabled")
                ),
                "mtz_endpoint_order_cut_count": judge.pricing_payload.get("mtz_endpoint_order_cut_count"),
                "pair_adjacency_cuts_enabled": bool(judge.pricing_payload.get("pair_adjacency_cuts_enabled")),
                "pair_adjacency_cut_count": judge.pricing_payload.get("pair_adjacency_cut_count"),
                "sortie_slots_per_journey": judge.pricing_payload.get("sortie_slots_per_journey"),
                "sortie_slot_bound_source": judge.pricing_payload.get("sortie_slot_bound_source"),
                "sortie_slot_horizon_count_bound": judge.pricing_payload.get("sortie_slot_horizon_count_bound"),
                "sortie_slot_latest_start_count_bound": judge.pricing_payload.get(
                    "sortie_slot_latest_start_count_bound"
                ),
                "time_window_arc_pruning_enabled": bool(
                    judge.pricing_payload.get("time_window_arc_pruning_enabled")
                ),
                "time_window_arc_option_count": judge.pricing_payload.get("time_window_arc_option_count"),
                "time_window_impossible_arc_option_count": judge.pricing_payload.get(
                    "time_window_impossible_arc_option_count"
                ),
                "compact_negative_no_good_scope": judge.pricing_payload.get("compact_negative_no_good_scope"),
                "forbidden_arc_pattern_count": judge.pricing_payload.get("forbidden_arc_pattern_count"),
                "forbidden_task_set_count": judge.pricing_payload.get("forbidden_task_set_count"),
                "negative_column_count": len(judge.negative_columns),
                "added_column_count": added,
                "completion_bound_pruning_enabled": False,
            }
        )
        if judge.pricing_state == PricingState.CERTIFIED_NO_NEGATIVE:
            return _payload(
                data=data,
                b0_direct=b0_direct,
                pool=pool,
                view=view,
                proof_debt=proof_debt,
                history=history,
                round_count=round_index,
                added_column_count=added_total,
                algorithm_status=AlgorithmStatus.BPC_GAP_AVAILABLE,
                certificate_scope=CertificateScope.BPC_NODE_LP_CERTIFIED,
                pricing_state=PricingState.CERTIFIED_NO_NEGATIVE,
                master=master,
                final_judge=judge.pricing_payload,
                seed_report=seed_report,
                include_active_columns=bool(return_active_columns_payload),
                note="Root LP bound is certified by journey RMP plus exhaustive true-dual fixed-graph pricing.",
            )
        if judge.pricing_state == PricingState.INCOMPLETE_LIMIT:
            return _payload(
                data=data,
                b0_direct=b0_direct,
                pool=pool,
                view=view,
                proof_debt=proof_debt,
                history=history,
                round_count=round_index,
                added_column_count=added_total,
                algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
                certificate_scope=CertificateScope.DIAGNOSTIC_PRICING_FRONTIER,
                pricing_state=PricingState.INCOMPLETE_LIMIT,
                master=master,
                final_judge=judge.pricing_payload,
                seed_report=seed_report,
                include_active_columns=bool(return_active_columns_payload),
                note=(
                    "Final judge returned INCOMPLETE_LIMIT before root no-negative proof; "
                    "fail closed with partial pricing telemetry."
                ),
            )
        if judge.pricing_state == PricingState.FOUND_NEGATIVE and added == 0:
            duplicate_only = True
            break

    algorithm_status = AlgorithmStatus.BPC_INCOMPLETE_PRICING
    certificate_scope = CertificateScope.DIAGNOSTIC_PRICING_FRONTIER
    pricing_state = PricingState.DUPLICATE_ONLY if duplicate_only else PricingState.INCOMPLETE_LIMIT
    return _payload(
        data=data,
        b0_direct=b0_direct,
        pool=pool,
        view=view,
        proof_debt=proof_debt,
        history=history,
        round_count=int(max_rounds),
        added_column_count=added_total,
        algorithm_status=algorithm_status,
        certificate_scope=certificate_scope,
        pricing_state=pricing_state,
        master=last_master,
        final_judge=None if last_judge is None else last_judge.pricing_payload,
        seed_report=seed_report,
        include_active_columns=bool(return_active_columns_payload),
        note=(
            "Root pricing found only duplicate negative columns; certificate blocked."
            if duplicate_only
            else f"Stopped after max_rounds={max_rounds}; root no-negative proof is incomplete."
        ),
    )


def build_b1_seed_columns(
    data: LunarIceData,
    *,
    b0_direct,
    initial_columns: Iterable[JourneyColumn] | None = None,
    seed_mode: str = "full_universe",
    max_direct_tasks: int = 5,
) -> tuple[tuple[JourneyColumn, ...], dict]:
    """Build B1 root seed columns without conflating audit and CG modes."""

    full_universe_result = None
    full_universe: tuple[JourneyColumn, ...] = tuple()
    incumbent_seed_columns: tuple[JourneyColumn, ...] = tuple()
    incumbent_seed_source = ""
    if initial_columns is not None:
        resolved_mode = "custom_initial_columns"
        columns = tuple(initial_columns)
    else:
        resolved_mode = str(seed_mode)
        if resolved_mode == "full_universe":
            full_universe_result = enumerate_direct_journey_columns(data, max_exact_tasks=int(max_direct_tasks))
            full_universe = full_universe_result.columns
            columns = full_universe
        elif resolved_mode == "b0_incumbent":
            incumbent_seed_columns = tuple(getattr(b0_direct, "journeys", tuple()) or tuple())
            incumbent_seed_source = "B0_DIRECT_DP_FEASIBLE_INCUMBENT" if incumbent_seed_columns else ""
            columns = incumbent_seed_columns
        elif resolved_mode == "b0_incumbent_plus_singletons":
            incumbent_seed_columns, incumbent_seed_source = _incumbent_seed_columns(data, b0_direct)
            if len(data.task_ids) <= 10:
                full_universe_result = enumerate_direct_journey_columns(data, max_exact_tasks=int(max_direct_tasks))
                full_universe = full_universe_result.columns
                singleton_columns = tuple(column for column in full_universe if len(column.task_set) == 1)
            else:
                singleton_columns = _direct_singleton_seed_columns(data)
            columns = _dedupe_columns(
                tuple(incumbent_seed_columns)
                + tuple(singleton_columns)
            )
        elif resolved_mode == "canonical":
            columns = enumerate_canonical_journey_columns(data, max_exact_tasks=int(max_direct_tasks)).columns
        elif resolved_mode == "canonical_plus_b0_incumbent":
            canonical = enumerate_canonical_journey_columns(data, max_exact_tasks=int(max_direct_tasks)).columns
            incumbent_seed_columns, incumbent_seed_source = _incumbent_seed_columns(data, b0_direct)
            columns = _dedupe_columns(tuple(incumbent_seed_columns) + tuple(canonical))
        else:
            raise ValueError(f"unsupported B1 seed_mode={seed_mode!r}")

    full_universe_signatures = {column_signature_from_journey(column) for column in full_universe}
    seed_signatures = {column_signature_from_journey(column) for column in columns}
    incumbent_seed_signatures = {column_signature_from_journey(column) for column in incumbent_seed_columns}
    full_universe_preloaded = bool(
        full_universe
        and seed_signatures == full_universe_signatures
        and len(columns) == len(full_universe)
    )
    b1_mode = "B1A_full_universe_root_audit" if full_universe_preloaded else "B1B_seeded_root_CG"
    full_counts = (
        {
            "generated_sortie_count": full_universe_result.generated_sortie_count,
            "route_template_count": full_universe_result.route_template_count,
            "pareto_label_count": full_universe_result.pareto_label_count,
        }
        if full_universe_result is not None
        else None
    )
    return tuple(columns), {
        "b1_mode": b1_mode,
        "seed_mode": resolved_mode,
        "initial_column_count": len(columns),
        "feasible_incumbent_seed_source": incumbent_seed_source,
        "feasible_incumbent_seed_column_count": sum(
            1 for column in columns if column_signature_from_journey(column) in incumbent_seed_signatures
        ),
        "feasible_incumbent_seed_used_as_certificate": False,
        "full_universe_column_count": len(full_universe) if full_universe_result is not None else None,
        "full_universe_preloaded": full_universe_preloaded,
        "_full_universe_columns": tuple(full_universe) if full_universe_result is not None else None,
        "_full_universe_counts": full_counts,
    }


def _incumbent_seed_columns(data: LunarIceData, b0_direct) -> tuple[tuple[JourneyColumn, ...], str]:
    b0_columns = tuple(getattr(b0_direct, "journeys", tuple()) or tuple())
    if b0_columns:
        return b0_columns, "B0_DIRECT_DP_FEASIBLE_INCUMBENT"
    reference = _reference_solution_upper_bound(data)
    if reference is None:
        return tuple(), ""
    return tuple(reference.journeys), f"REFERENCE_FEASIBLE_INCUMBENT:{reference.source}"


def _reference_seed_direct_placeholder(data: LunarIceData):
    reference = _reference_solution_upper_bound(data)
    return SimpleNamespace(
        status="REFERENCE_FEASIBLE_INCUMBENT_SEED_ONLY",
        exact_status="NOT_SOLVED",
        objective=None,
        journeys=tuple(),
        generated_journey_count=0,
        generated_sortie_count=0,
        route_template_count=0,
        pareto_label_count=0,
        set_partition_state_count=0,
        note=(
            "B0 direct-DP was intentionally not run before B1; reference feasible incumbent "
            "may seed the RMP but cannot certify any bound."
        ),
        wall_time_sec=0.0,
        certificate_scope=CertificateScope.FEASIBLE_INCUMBENT_ONLY.value,
        objective_breakdown=None,
        reference_solution_upper_bound=None if reference is None else float(reference.objective),
        reference_solution_upper_bound_source="" if reference is None else str(reference.source),
        journey_label_bound_pruned_count=0,
        direct_bound_pruning_root_bound=None,
        direct_bound_pruning_active=False,
    )


def _remaining_wall_time_limit(wall_time_limit_sec: float | None, *, started_at: float) -> float | None:
    if wall_time_limit_sec is None:
        return None
    remaining = float(wall_time_limit_sec) - (perf_counter() - float(started_at))
    return max(0.001, float(remaining))


def _load_columns(pool: ColumnPool, view: MasterColumnView, columns: Iterable[JourneyColumn]) -> None:
    for column in columns:
        signature = column_signature_from_journey(column)
        bpc_column = BpcColumn(signature=signature, objective=column.objective, payload=column)
        pool.add(bpc_column)
        stored = pool.get(signature)
        if stored is not None:
            view.add_from_pool(stored, node_id="root", pool=pool)


def _master_columns(pool: ColumnPool, view: MasterColumnView) -> tuple[JourneyColumn, ...]:
    signatures = view.signatures_by_node.get("root", set())
    columns = []
    for signature in sorted(signatures, key=repr):
        column = pool.get(signature)
        if column is not None and isinstance(column.payload, JourneyColumn):
            columns.append(column.payload)
    return tuple(columns)


def _dedupe_columns(columns: Iterable[JourneyColumn]) -> tuple[JourneyColumn, ...]:
    unique: list[JourneyColumn] = []
    seen = set()
    for column in columns:
        signature = column_signature_from_journey(column)
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(column)
    return tuple(unique)


def _direct_singleton_seed_columns(data: LunarIceData) -> tuple[JourneyColumn, ...]:
    columns: list[JourneyColumn] = []
    for task_id in data.task_ids:
        best: JourneyColumn | None = None
        for out_type in PATH_TYPES:
            for back_type in PATH_TYPES:
                sortie = build_timed_sortie(
                    data,
                    (task_id,),
                    (out_type, back_type),
                    start_time=0.0,
                )
                if not sortie.feasible:
                    continue
                column = build_journey_column(data, (sortie,))
                if best is None or (column.objective, column.end_time) < (best.objective, best.end_time):
                    best = column
        if best is not None:
            columns.append(best)
    return tuple(columns)


def _add_negative_columns(
    pool: ColumnPool,
    view: MasterColumnView,
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
        signature = column_signature_from_journey(column)
        bpc_column = BpcColumn(signature=signature, objective=column.objective, payload=column)
        result = pool.add(bpc_column)
        stored = pool.get(signature)
        if stored is not None:
            loaded = view.add_from_pool(stored, node_id="root", pool=pool)
            if result.added or loaded:
                added += 1
        if added >= max(1, int(max_columns)):
            break
    return added


def _payload(
    *,
    data: LunarIceData,
    b0_direct,
    pool: ColumnPool,
    view: MasterColumnView,
    proof_debt: ProofDebtQueue,
    history: list[dict],
    round_count: int,
    added_column_count: int,
    algorithm_status: AlgorithmStatus,
    certificate_scope: CertificateScope,
    pricing_state: PricingState,
    master,
    final_judge: dict | None,
    seed_report: dict,
    note: str,
    include_active_columns: bool = False,
) -> dict:
    root_bound = master.rmp.objective_bound if master is not None else None
    b0_objective = b0_direct.objective
    final_judge_history = [row for row in history if row.get("final_judge_status") not in {None, ""}]
    final_judge_wall_times = [
        float(row["final_judge_wall_time"])
        for row in final_judge_history
        if row.get("final_judge_wall_time") not in {None, ""}
    ]
    negative_rc_values = [
        float(row["best_reduced_cost"])
        for row in final_judge_history
        if row.get("pricing_state") == PricingState.FOUND_NEGATIVE.value
        and row.get("best_reduced_cost") not in {None, ""}
    ]
    root_le_b0 = (
        None
        if root_bound is None or b0_objective is None
        else float(root_bound) <= float(b0_objective) + 1.0e-6
    )
    root_gap = (
        None
        if root_bound is None or b0_objective is None
        else round(float(b0_objective) - float(root_bound), 9)
    )
    integral_root = (
        None
        if root_gap is None
        else abs(float(root_gap)) <= 1.0e-6
    )
    manual_rc_audit_pass = bool(
        master is not None
        and master.reduced_cost_audit.get("dual_fingerprint_bound_to_rmp") is True
        and (
            master.reduced_cost_audit.get("min_reduced_cost") is None
            or float(master.reduced_cost_audit["min_reduced_cost"]) >= -1.0e-6
        )
    )
    pricing_rc_audit_pass = bool(final_judge and final_judge.get("pricing_rc_audit_pass") is True)
    gate_issues: list[str] = []
    if root_le_b0 is False:
        gate_issues.append("root_lp_bound_exceeds_direct_dp_integer_objective")
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and not manual_rc_audit_pass:
        gate_issues.append("manual_reduced_cost_audit_failed")
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and not pricing_rc_audit_pass:
        gate_issues.append("pricing_reduced_cost_audit_failed")
    ledger = CertificateLedger(
        algorithm_status=algorithm_status,
        certificate_scope=certificate_scope,
        pricing_state=pricing_state,
        uses_true_dual_bpc_certificate=certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED,
        issues=gate_issues,
    )
    ledger_payload = ledger.validate(proof_debt_queue=proof_debt)
    root_lp_bound_official = bool(
        certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED
        and ledger_payload["valid"]
        and pricing_state == PricingState.CERTIFIED_NO_NEGATIVE
    )
    payload = {
        "schema_version": "lunar_ice_bpc.b1_root_baseline.v1",
        "instance_id": data.instance_id,
        "algorithm_status": algorithm_status.value,
        "certificate_scope": certificate_scope.value,
        "pricing_state": pricing_state.value,
        "uses_true_dual_bpc_certificate": ledger_payload["uses_true_dual_bpc_certificate"],
        "certificate_ledger": ledger_payload,
        "proof_debt_queue": proof_debt.audit(),
        "task_count": len(data.task_ids),
        "b1_mode": seed_report["b1_mode"],
        "seed_mode": seed_report["seed_mode"],
        "solve_b0_direct_first": bool(seed_report.get("solve_b0_direct_first", True)),
        "initial_column_count": seed_report["initial_column_count"],
        "feasible_incumbent_seed_source": seed_report.get("feasible_incumbent_seed_source", ""),
        "feasible_incumbent_seed_column_count": seed_report.get("feasible_incumbent_seed_column_count", 0),
        "feasible_incumbent_seed_used_as_certificate": bool(
            seed_report.get("feasible_incumbent_seed_used_as_certificate", False)
        ),
        "full_universe_column_count": seed_report["full_universe_column_count"],
        "full_universe_preloaded": seed_report["full_universe_preloaded"],
        "round_count": int(round_count),
        "pricing_round_count": int(round_count),
        "added_column_count": int(added_column_count),
        "pool_column_count": len(pool.columns_by_signature),
        "master_column_count": len(view.signatures_by_node.get("root", set())),
        "root_rmp_status": None if master is None else master.rmp.status,
        "root_rmp_objective": root_bound,
        "root_lp_bound": root_bound,
        "root_lp_bound_official": root_lp_bound_official,
        "root_lp_vs_direct_dp_gap": root_gap,
        "integral_root": integral_root,
        "rmp_iteration_count": None if master is None else master.rmp.iteration_count,
        "root_min_reduced_cost": None if master is None else master.rmp.min_reduced_cost,
        "dual_fingerprint": None if master is None else master.reduced_cost_context.dual_fingerprint,
        "reduced_cost_audit": None if master is None else master.reduced_cost_audit,
        "final_judge": final_judge or {},
        "final_judge_status": None if not final_judge else final_judge.get("status"),
        "final_judge_min_reduced_cost": None if not final_judge else final_judge.get("best_reduced_cost"),
        "final_judge_call_count": len(final_judge_history),
        "final_judge_total_wall_time": round(sum(final_judge_wall_times), 6) if final_judge_wall_times else 0.0,
        "final_judge_found_negative_count": sum(
            1 for row in final_judge_history if row.get("pricing_state") == PricingState.FOUND_NEGATIVE.value
        ),
        "final_judge_best_negative_reduced_cost": (
            round(min(negative_rc_values), 9) if negative_rc_values else None
        ),
        "final_judge_incomplete_count": sum(
            1 for row in final_judge_history if row.get("pricing_state") == PricingState.INCOMPLETE_LIMIT.value
        ),
        "final_judge_certified_no_negative_count": sum(
            1 for row in final_judge_history if row.get("pricing_state") == PricingState.CERTIFIED_NO_NEGATIVE.value
        ),
        "manual_rc_audit_pass": manual_rc_audit_pass,
        "pricing_rc_audit_pass": pricing_rc_audit_pass,
        "proof_debt_unreleased_count": len(proof_debt.unreleased),
        "history": list(history),
        "b0_ablation": {
            "baseline": "B0_DIRECT_DP_FIXED_GRAPH_ORACLE",
            "direct_dp_status": b0_direct.status,
            "direct_dp_certificate_scope": b0_direct.certificate_scope,
            "direct_dp_objective": b0_objective,
            "direct_dp_objective_breakdown": getattr(b0_direct, "objective_breakdown", None),
            "reference_solution_upper_bound": getattr(b0_direct, "reference_solution_upper_bound", None),
            "reference_solution_upper_bound_source": getattr(
                b0_direct, "reference_solution_upper_bound_source", ""
            ),
            "direct_bound_pruning_root_bound": getattr(b0_direct, "direct_bound_pruning_root_bound", None),
            "direct_bound_pruning_active": getattr(b0_direct, "direct_bound_pruning_active", False),
            "journey_label_bound_pruned_count": getattr(b0_direct, "journey_label_bound_pruned_count", 0),
            "root_lp_bound": root_bound,
            "root_lp_vs_direct_dp_gap": root_gap,
            "integral_root": integral_root,
            "root_bound_le_direct_dp_integer_objective": root_le_b0,
            "marginal_contribution": "B1 adds an official root LP bound proof via RMP duals plus final pricing closure.",
        },
        "exact_status": (
            "BPC_NODE_LP_CERTIFIED"
            if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and ledger_payload["valid"]
            else "NOT_SOLVED"
        ),
        "note": note,
    }
    if include_active_columns:
        active_columns = _master_columns(pool, view)
        payload["active_columns_payload_version"] = "journey_solution_payload.v1"
        payload["active_columns"] = [
            column.to_solution_payload(vehicle_id=f"active_column_{index:06d}")
            for index, column in enumerate(active_columns, start=1)
        ]
    return payload


def _incomplete_payload(
    *,
    data: LunarIceData,
    b0_direct,
    reason: str,
    max_direct_tasks: int,
    b1_mode: str = "B1_fail_closed_over_task_limit",
    seed_mode: str = "none_over_task_limit",
    initial_column_count: int = 0,
    full_universe_column_count: int | None = None,
    full_universe_preloaded: bool = False,
    extra: dict | None = None,
) -> dict:
    proof_debt = ProofDebtQueue()
    direct_status = None if b0_direct is None else b0_direct.status
    direct_scope = None if b0_direct is None else b0_direct.certificate_scope
    direct_objective = None if b0_direct is None else b0_direct.objective
    direct_breakdown = None if b0_direct is None else getattr(b0_direct, "objective_breakdown", None)
    ledger = CertificateLedger(
        algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
        certificate_scope=CertificateScope.FEASIBLE_INCUMBENT_ONLY,
        pricing_state=PricingState.INCOMPLETE_LIMIT,
        uses_true_dual_bpc_certificate=False,
    )
    return {
        "schema_version": "lunar_ice_bpc.b1_root_baseline.v1",
        "instance_id": data.instance_id,
        "algorithm_status": AlgorithmStatus.BPC_INCOMPLETE_PRICING.value,
        "certificate_scope": CertificateScope.FEASIBLE_INCUMBENT_ONLY.value,
        "pricing_state": PricingState.INCOMPLETE_LIMIT.value,
        "uses_true_dual_bpc_certificate": False,
        "certificate_ledger": ledger.validate(proof_debt_queue=proof_debt),
        "proof_debt_queue": proof_debt.audit(),
        "task_count": len(data.task_ids),
        "max_direct_tasks": int(max_direct_tasks),
        "b1_mode": str(b1_mode),
        "seed_mode": str(seed_mode),
        "initial_column_count": int(initial_column_count),
        "full_universe_column_count": full_universe_column_count,
        "full_universe_preloaded": bool(full_universe_preloaded),
        "round_count": 0,
        "pricing_round_count": 0,
        "added_column_count": 0,
        "pool_column_count": 0,
        "master_column_count": 0,
        "root_rmp_status": None,
        "root_rmp_objective": None,
        "root_lp_bound": None,
        "root_lp_bound_official": False,
        "root_lp_vs_direct_dp_gap": None,
        "integral_root": None,
        "rmp_iteration_count": 0,
        "root_min_reduced_cost": None,
        "dual_fingerprint": None,
        "reduced_cost_audit": None,
        "final_judge": {},
        "final_judge_status": None,
        "final_judge_min_reduced_cost": None,
        "manual_rc_audit_pass": False,
        "pricing_rc_audit_pass": False,
        "proof_debt_unreleased_count": 0,
        "history": [],
        "b0_ablation": {
            "baseline": "B0_DIRECT_DP_FIXED_GRAPH_ORACLE",
            "direct_dp_status": direct_status,
            "direct_dp_certificate_scope": direct_scope,
            "direct_dp_objective": direct_objective,
            "direct_dp_objective_breakdown": direct_breakdown,
            "root_lp_bound": None,
            "root_lp_vs_direct_dp_gap": None,
            "integral_root": None,
            "root_bound_le_direct_dp_integer_objective": None,
        },
        "exact_status": "NOT_SOLVED",
        "note": reason,
        **(extra or {}),
    }
