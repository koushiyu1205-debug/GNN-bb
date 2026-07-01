"""B1 root-only true-dual BPC baseline."""

from __future__ import annotations

from typing import Iterable

from lunar_ice_bpc.exact.bpc.certificates.certificate_ledger import CertificateLedger
from lunar_ice_bpc.exact.bpc.certificates.proof_debt_queue import ProofDebtQueue
from lunar_ice_bpc.exact.bpc.core.column_pool import BpcColumn, ColumnPool
from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.bpc.core.master_column_view import MasterColumnView
from lunar_ice_bpc.exact.bpc.master.journey_master import solve_root_journey_master
from lunar_ice_bpc.exact.bpc.pricing.final_judge import run_true_dual_root_final_judge
from lunar_ice_bpc.exact.bpc.pricing.status import AlgorithmStatus, CertificateScope, PricingState
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.master.journey_rmp import manual_journey_reduced_cost
from lunar_ice_bpc.exact.pricing.journey_pricing import DirectPricingCache
from lunar_ice_bpc.exact.solver.journey_driver import (
    enumerate_canonical_journey_columns,
    enumerate_direct_journey_columns,
    solve_direct_journey_baseline,
)


def solve_b1_root_node_baseline(
    data: LunarIceData,
    *,
    initial_columns: Iterable[JourneyColumn] | None = None,
    max_direct_tasks: int = 5,
    max_rounds: int = 8,
    negative_eps: float = 1.0e-6,
    max_columns_per_round: int = 64,
    seed_mode: str = "full_universe",
) -> dict:
    """Solve the root BPC baseline on the fixed logical graph.

    This is root-only. It does not branch, separate cuts, call GAT, or use
    completion-bound pruning in the final pricing judge.
    """

    b0_direct = solve_direct_journey_baseline(data, max_exact_tasks=int(max_direct_tasks))
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
                note="Root RMP did not solve to optimality; fail closed.",
            )
        judge = run_true_dual_root_final_judge(
            data,
            master.reduced_cost_context,
            max_direct_tasks=int(max_direct_tasks),
            negative_eps=negative_eps,
            cache=cache,
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
                "pricing_state": judge.pricing_state.value,
                "best_reduced_cost": judge.pricing_payload.get("best_reduced_cost"),
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
                note="Root LP bound is certified by journey RMP plus exhaustive true-dual fixed-graph pricing.",
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

    full_universe = enumerate_direct_journey_columns(data, max_exact_tasks=int(max_direct_tasks)).columns
    if initial_columns is not None:
        resolved_mode = "custom_initial_columns"
        columns = tuple(initial_columns)
    else:
        resolved_mode = str(seed_mode)
        if resolved_mode == "full_universe":
            columns = full_universe
        elif resolved_mode == "b0_incumbent":
            columns = tuple(b0_direct.journeys)
        elif resolved_mode == "b0_incumbent_plus_singletons":
            columns = _dedupe_columns(
                tuple(b0_direct.journeys)
                + tuple(column for column in full_universe if len(column.task_set) == 1)
            )
        elif resolved_mode == "canonical":
            columns = enumerate_canonical_journey_columns(data, max_exact_tasks=int(max_direct_tasks)).columns
        elif resolved_mode == "canonical_plus_b0_incumbent":
            canonical = enumerate_canonical_journey_columns(data, max_exact_tasks=int(max_direct_tasks)).columns
            columns = _dedupe_columns(tuple(b0_direct.journeys) + tuple(canonical))
        else:
            raise ValueError(f"unsupported B1 seed_mode={seed_mode!r}")

    full_universe_signatures = {column_signature_from_journey(column) for column in full_universe}
    seed_signatures = {column_signature_from_journey(column) for column in columns}
    full_universe_preloaded = bool(seed_signatures == full_universe_signatures and len(columns) == len(full_universe))
    b1_mode = "B1A_full_universe_root_audit" if full_universe_preloaded else "B1B_seeded_root_CG"
    return tuple(columns), {
        "b1_mode": b1_mode,
        "seed_mode": resolved_mode,
        "initial_column_count": len(columns),
        "full_universe_column_count": len(full_universe),
        "full_universe_preloaded": full_universe_preloaded,
    }


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
) -> dict:
    root_bound = master.rmp.objective_bound if master is not None else None
    b0_objective = b0_direct.objective
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
    return {
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
        "initial_column_count": seed_report["initial_column_count"],
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
        "manual_rc_audit_pass": manual_rc_audit_pass,
        "pricing_rc_audit_pass": pricing_rc_audit_pass,
        "proof_debt_unreleased_count": len(proof_debt.unreleased),
        "history": list(history),
        "b0_ablation": {
            "baseline": "B0_DIRECT_DP_FIXED_GRAPH_ORACLE",
            "direct_dp_status": b0_direct.status,
            "direct_dp_certificate_scope": b0_direct.certificate_scope,
            "direct_dp_objective": b0_objective,
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


def _incomplete_payload(
    *,
    data: LunarIceData,
    b0_direct,
    reason: str,
    max_direct_tasks: int,
) -> dict:
    proof_debt = ProofDebtQueue()
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
        "b1_mode": "B1_fail_closed_over_task_limit",
        "seed_mode": "none_over_task_limit",
        "initial_column_count": 0,
        "full_universe_column_count": None,
        "full_universe_preloaded": False,
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
            "direct_dp_status": b0_direct.status,
            "direct_dp_certificate_scope": b0_direct.certificate_scope,
            "direct_dp_objective": b0_direct.objective,
            "root_lp_bound": None,
            "root_lp_vs_direct_dp_gap": None,
            "integral_root": None,
            "root_bound_le_direct_dp_integer_objective": None,
        },
        "exact_status": "NOT_SOLVED",
        "note": reason,
    }
