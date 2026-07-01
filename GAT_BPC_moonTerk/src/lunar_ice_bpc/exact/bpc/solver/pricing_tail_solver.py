"""B2 root pricing-tail optimization baseline."""

from __future__ import annotations

from lunar_ice_bpc.exact.bpc.certificates.certificate_ledger import CertificateLedger
from lunar_ice_bpc.exact.bpc.certificates.proof_debt_queue import ProofDebtQueue
from lunar_ice_bpc.exact.bpc.core.column_pool import BpcColumn, ColumnPool
from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.bpc.core.master_column_view import MasterColumnView
from lunar_ice_bpc.exact.bpc.master.journey_master import solve_root_journey_master
from lunar_ice_bpc.exact.bpc.pricing.completion_bounds import build_completion_bound_tail_policy
from lunar_ice_bpc.exact.bpc.pricing.duplicate_only_audit import build_duplicate_only_audit
from lunar_ice_bpc.exact.bpc.pricing.harvest import harvest_addable_negative_columns
from lunar_ice_bpc.exact.bpc.pricing.hidden_negative_audit import build_hidden_negative_audit
from lunar_ice_bpc.exact.bpc.pricing.final_judge import run_true_dual_root_final_judge
from lunar_ice_bpc.exact.bpc.pricing.profiling import PruningCounter
from lunar_ice_bpc.exact.bpc.pricing.status import AlgorithmStatus, CertificateScope, PricingState
from lunar_ice_bpc.exact.bpc.pricing.worker_seed_catalog import WorkerSeedCatalog
from lunar_ice_bpc.exact.bpc.solver.root_node_solver import (
    _load_columns,
    _master_columns,
    solve_b1_root_node_baseline,
)
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.master.journey_rmp import manual_journey_reduced_cost
from lunar_ice_bpc.exact.pricing.journey_pricing import DirectPricingCache
from lunar_ice_bpc.exact.solver.journey_driver import enumerate_direct_journey_columns


def solve_b2_pricing_tail_baseline(
    data: LunarIceData,
    *,
    max_direct_tasks: int = 5,
    max_rounds: int = 8,
    negative_eps: float = 1.0e-6,
    max_columns_per_round: int = 64,
    worker_payload: dict | None = None,
) -> dict:
    """Run B2 = B1 root closure plus addability-aware pricing-tail handling."""

    b1 = solve_b1_root_node_baseline(
        data,
        max_direct_tasks=max_direct_tasks,
        max_rounds=max_rounds,
        negative_eps=negative_eps,
        max_columns_per_round=max_columns_per_round,
    )
    completion_policy = build_completion_bound_tail_policy(pruning_opt_in=False)
    if len(data.task_ids) > int(max_direct_tasks):
        return _incomplete_payload(data=data, b1=b1, completion_policy=completion_policy)

    seed_columns = enumerate_direct_journey_columns(data, max_exact_tasks=int(max_direct_tasks)).columns
    pool = ColumnPool()
    view = MasterColumnView()
    _load_columns(pool, view, seed_columns)
    proof_debt = ProofDebtQueue()
    cache = DirectPricingCache()
    profiling = PruningCounter()
    seed_catalog = WorkerSeedCatalog()
    history: list[dict] = []
    harvest_totals = _empty_harvest_totals()
    final_judge_call_count = 0
    found_negative_count = 0
    duplicate_only_count = 0
    replacement_only_round_count = 0
    hidden_negative_count = 0
    last_master = None
    last_judge_payload: dict | None = None
    last_duplicate_audit: dict | None = None
    last_hidden_audit: dict | None = None
    added_total = 0

    for round_index in range(1, int(max_rounds) + 1):
        master_columns = _master_columns(pool, view)
        master = solve_root_journey_master(
            data,
            master_columns,
            negative_eps=negative_eps,
            rmp_iteration_id=f"b2-root-{round_index}",
        )
        last_master = master
        if master.rmp.status != "RESTRICTED_RMP_OPTIMAL":
            return _payload(
                data=data,
                b1=b1,
                proof_debt=proof_debt,
                completion_policy=completion_policy,
                profiling=profiling,
                history=history,
                harvest_totals=harvest_totals,
                final_judge_call_count=final_judge_call_count,
                found_negative_count=found_negative_count,
                duplicate_only_count=duplicate_only_count,
                replacement_only_round_count=replacement_only_round_count,
                hidden_negative_count=hidden_negative_count,
                master=master,
                final_judge=last_judge_payload,
                duplicate_audit=last_duplicate_audit,
                hidden_audit=last_hidden_audit,
                seed_catalog=seed_catalog,
                algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
                certificate_scope=CertificateScope.DIAGNOSTIC_RMP_BOUND,
                pricing_state=PricingState.INCOMPLETE_LIMIT,
                note="B2 root RMP did not solve to optimality; fail closed.",
            )
        judge = run_true_dual_root_final_judge(
            data,
            master.reduced_cost_context,
            max_direct_tasks=int(max_direct_tasks),
            negative_eps=negative_eps,
            cache=cache,
        )
        final_judge_call_count += 1
        last_judge_payload = judge.pricing_payload
        profiling.merge_completion_payload(judge.pricing_payload)
        candidate_pairs = tuple(
            (manual_journey_reduced_cost(column, master.rmp.duals), column)
            for column in judge.all_priced_columns
        )
        negative_pairs = tuple(
            (true_rc, column)
            for true_rc, column in candidate_pairs
            if true_rc < -abs(float(negative_eps))
        )
        if negative_pairs:
            found_negative_count += 1
        hidden_audit = build_hidden_negative_audit(
            worker_payload=worker_payload,
            final_judge_payload=judge.pricing_payload,
            negative_candidates=negative_pairs,
            node_id="root",
            cg_iter=round_index,
        )
        last_hidden_audit = hidden_audit
        hidden_negative_count += int(hidden_audit.get("hidden_negative_count") or 0)
        seed_catalog.record_hidden_negative_audit(hidden_audit)
        selected, harvest_payload = harvest_addable_negative_columns(
            negative_pairs,
            pool=pool,
            view=view,
            node_id="root",
            negative_eps=negative_eps,
            max_selected=max_columns_per_round,
            active_task_sets={frozenset(column.task_set) for column in master_columns},
            profiling=profiling,
        )
        _accumulate_harvest_totals(harvest_totals, harvest_payload)
        added = _add_selected_to_pool_and_master(pool, view, selected)
        added_total += added
        duplicate_audit = None
        if negative_pairs and not selected:
            duplicate_only_count += 1
            replacement_only_round_count += 1
            duplicate_audit = build_duplicate_only_audit(
                negative_pairs,
                pool=pool,
                view=view,
                duals=master.rmp.duals,
                negative_eps=negative_eps,
            )
            last_duplicate_audit = duplicate_audit
        history.append(
            {
                "round": round_index,
                "root_lp_bound": master.rmp.objective_bound,
                "pricing_state": judge.pricing_state.value,
                "negative_candidate_count": len(negative_pairs),
                "harvest_selected_count": len(selected),
                "added_column_count": added,
                "duplicate_only_audit_status": None if duplicate_audit is None else duplicate_audit.get("status"),
                "completion_bound_pruning_enabled": False,
            }
        )
        if judge.pricing_state == PricingState.CERTIFIED_NO_NEGATIVE:
            return _payload(
                data=data,
                b1=b1,
                proof_debt=proof_debt,
                completion_policy=completion_policy,
                profiling=profiling,
                history=history,
                harvest_totals=harvest_totals,
                final_judge_call_count=final_judge_call_count,
                found_negative_count=found_negative_count,
                duplicate_only_count=duplicate_only_count,
                replacement_only_round_count=replacement_only_round_count,
                hidden_negative_count=hidden_negative_count,
                master=master,
                final_judge=judge.pricing_payload,
                duplicate_audit=last_duplicate_audit,
                hidden_audit=last_hidden_audit,
                seed_catalog=seed_catalog,
                algorithm_status=AlgorithmStatus.BPC_GAP_AVAILABLE,
                certificate_scope=CertificateScope.BPC_NODE_LP_CERTIFIED,
                pricing_state=PricingState.CERTIFIED_NO_NEGATIVE,
                note="B2 root LP certificate matches B1 while reporting pricing-tail harvest diagnostics.",
            )
        if negative_pairs and not selected:
            break

    return _payload(
        data=data,
        b1=b1,
        proof_debt=proof_debt,
        completion_policy=completion_policy,
        profiling=profiling,
        history=history,
        harvest_totals=harvest_totals,
        final_judge_call_count=final_judge_call_count,
        found_negative_count=found_negative_count,
        duplicate_only_count=duplicate_only_count,
        replacement_only_round_count=replacement_only_round_count,
        hidden_negative_count=hidden_negative_count,
        master=last_master,
        final_judge=last_judge_payload,
        duplicate_audit=last_duplicate_audit,
        hidden_audit=last_hidden_audit,
        seed_catalog=seed_catalog,
        algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
        certificate_scope=CertificateScope.DIAGNOSTIC_PRICING_FRONTIER,
        pricing_state=PricingState.DUPLICATE_ONLY if duplicate_only_count else PricingState.INCOMPLETE_LIMIT,
        note="B2 pricing tail did not close root no-negative proof; fail closed.",
    )


def _add_selected_to_pool_and_master(pool: ColumnPool, view: MasterColumnView, columns: tuple[JourneyColumn, ...]) -> int:
    added = 0
    for column in columns:
        signature = column_signature_from_journey(column)
        bpc_column = BpcColumn(signature=signature, objective=column.objective, payload=column)
        pool.add(bpc_column, {"master_view": view, "node_id": "root"})
        stored = pool.get(signature)
        if stored is not None and view.add_from_pool(stored, node_id="root", pool=pool):
            added += 1
    return added


def _payload(
    *,
    data: LunarIceData,
    b1: dict,
    proof_debt: ProofDebtQueue,
    completion_policy: dict,
    profiling: PruningCounter,
    history: list[dict],
    harvest_totals: dict[str, int],
    final_judge_call_count: int,
    found_negative_count: int,
    duplicate_only_count: int,
    replacement_only_round_count: int,
    hidden_negative_count: int,
    master,
    final_judge: dict | None,
    duplicate_audit: dict | None,
    hidden_audit: dict | None,
    seed_catalog: WorkerSeedCatalog,
    algorithm_status: AlgorithmStatus,
    certificate_scope: CertificateScope,
    pricing_state: PricingState,
    note: str,
) -> dict:
    root_objective = None if master is None else master.rmp.objective_bound
    b1_objective = b1.get("root_rmp_objective")
    objective_diff = (
        None
        if root_objective is None or b1_objective is None
        else round(float(root_objective) - float(b1_objective), 9)
    )
    scope_diff = (
        ""
        if str(certificate_scope.value) == str(b1.get("certificate_scope"))
        else f"{b1.get('certificate_scope')}->{certificate_scope.value}"
    )
    gate_issues: list[str] = []
    if objective_diff not in {None, 0.0}:
        gate_issues.append("objective_diff_vs_B1_nonzero")
    if scope_diff:
        gate_issues.append("certificate_scope_diff_vs_B1_nonempty")
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and bool(final_judge and final_judge.get("pricing_rc_audit_pass")) is not True:
        gate_issues.append("pricing_reduced_cost_audit_failed")
    ledger = CertificateLedger(
        algorithm_status=algorithm_status,
        certificate_scope=certificate_scope,
        pricing_state=pricing_state,
        uses_true_dual_bpc_certificate=certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED,
        issues=gate_issues,
    )
    ledger_payload = ledger.validate(proof_debt_queue=proof_debt)
    return {
        "schema_version": "lunar_ice_bpc.b2_pricing_tail_baseline.v1",
        "instance_id": data.instance_id,
        "algorithm_status": algorithm_status.value,
        "certificate_scope": certificate_scope.value,
        "pricing_state": pricing_state.value,
        "uses_true_dual_bpc_certificate": ledger_payload["uses_true_dual_bpc_certificate"],
        "certificate_ledger": ledger_payload,
        "completion_bound_policy": completion_policy,
        "root_rmp_status": None if master is None else master.rmp.status,
        "root_rmp_objective": root_objective,
        "root_lp_bound": root_objective,
        "root_lp_bound_official": bool(certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and ledger_payload["valid"]),
        "rmp_iteration_count": 0 if master is None else master.rmp.iteration_count,
        "pricing_round_count": len(history),
        "final_judge_call_count": int(final_judge_call_count),
        "final_judge": final_judge or {},
        "history": list(history),
        "proof_debt_queue": proof_debt.audit(),
        "proof_debt_unreleased_count": len(proof_debt.unreleased),
        "profiling": profiling.to_payload(),
        "duplicate_only_audit": duplicate_audit or {},
        "hidden_negative_audit": hidden_audit or {"hidden_negative_count": 0, "rows": []},
        "worker_seed_catalog": seed_catalog.to_payload(),
        "b1_ablation": {
            "baseline": "B1_ROOT_ONLY_BPC",
            "b1_algorithm_status": b1.get("algorithm_status"),
            "b1_certificate_scope": b1.get("certificate_scope"),
            "b1_root_rmp_objective": b1_objective,
            "objective_diff_vs_B1": objective_diff,
            "certificate_scope_diff_vs_B1": scope_diff,
            "final_judge_call_count_vs_B1": int(final_judge_call_count) - int(b1.get("pricing_round_count") or 0),
        },
        "objective_diff_vs_B1": objective_diff,
        "certificate_scope_diff_vs_B1": scope_diff,
        "found_negative_count": int(found_negative_count),
        "duplicate_only_count": int(duplicate_only_count),
        "hidden_negative_count": int(hidden_negative_count),
        "replacement_only_round_count": int(replacement_only_round_count),
        **harvest_totals,
        "exact_status": (
            "BPC_NODE_LP_CERTIFIED"
            if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and ledger_payload["valid"]
            else "NOT_SOLVED"
        ),
        "note": note,
    }


def _incomplete_payload(*, data: LunarIceData, b1: dict, completion_policy: dict) -> dict:
    return {
        "schema_version": "lunar_ice_bpc.b2_pricing_tail_baseline.v1",
        "instance_id": data.instance_id,
        "algorithm_status": AlgorithmStatus.BPC_INCOMPLETE_PRICING.value,
        "certificate_scope": CertificateScope.FEASIBLE_INCUMBENT_ONLY.value,
        "pricing_state": PricingState.INCOMPLETE_LIMIT.value,
        "uses_true_dual_bpc_certificate": False,
        "completion_bound_policy": completion_policy,
        "objective_diff_vs_B1": None,
        "certificate_scope_diff_vs_B1": f"{b1.get('certificate_scope')}->{CertificateScope.FEASIBLE_INCUMBENT_ONLY.value}",
        "b1_ablation": {"baseline": "B1_ROOT_ONLY_BPC", "b1_certificate_scope": b1.get("certificate_scope")},
        **_empty_harvest_totals(),
        "duplicate_only_count": 0,
        "hidden_negative_count": 0,
        "replacement_only_round_count": 0,
        "final_judge_call_count": 0,
        "pricing_round_count": 0,
        "exact_status": "NOT_SOLVED",
        "note": f"task_count={len(data.task_ids)} exceeds B2 max_direct_tasks",
    }


def _empty_harvest_totals() -> dict[str, int]:
    return {
        "harvest_candidate_negative_count": 0,
        "harvest_addable_candidate_count": 0,
        "harvest_selected_count": 0,
        "harvest_duplicate_signature_count": 0,
        "harvest_forbidden_signature_count": 0,
        "harvest_dominance_filtered_count": 0,
    }


def _accumulate_harvest_totals(totals: dict[str, int], payload: dict) -> None:
    for key in list(totals):
        totals[key] += int(payload.get(key) or 0)

