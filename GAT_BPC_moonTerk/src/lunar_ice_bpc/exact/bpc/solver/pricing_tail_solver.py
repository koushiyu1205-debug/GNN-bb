"""B2 root pricing-tail optimization layer.

B2 is a candidate layer over the accepted B0/B1 proof core.  It never changes
certificate scope or official-bound semantics; it only changes root pricing-tail
handling and records addability, duplicate-only, hidden-negative, and harvesting
diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from time import perf_counter
from typing import Iterable

from lunar_ice_bpc.exact.bpc.certificates.certificate_ledger import CertificateLedger
from lunar_ice_bpc.exact.bpc.certificates.proof_debt_queue import ProofDebtQueue
from lunar_ice_bpc.exact.bpc.core.column_pool import BpcColumn, ColumnPool
from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.bpc.core.master_column_view import MasterColumnView
from lunar_ice_bpc.exact.bpc.master.journey_master import solve_root_journey_master
from lunar_ice_bpc.exact.bpc.pricing.completion_bounds import build_completion_bound_tail_policy
from lunar_ice_bpc.exact.bpc.pricing.duplicate_only_audit import build_duplicate_only_audit
from lunar_ice_bpc.exact.bpc.pricing.final_judge import run_true_dual_root_final_judge
from lunar_ice_bpc.exact.bpc.pricing.harvest import harvest_addable_negative_columns
from lunar_ice_bpc.exact.bpc.pricing.hidden_negative_audit import build_hidden_negative_audit
from lunar_ice_bpc.exact.bpc.pricing.profiling import PruningCounter
from lunar_ice_bpc.exact.bpc.pricing.status import AlgorithmStatus, CertificateScope, PricingState
from lunar_ice_bpc.exact.bpc.pricing.worker_seed_catalog import WorkerSeedCatalog
from lunar_ice_bpc.exact.bpc.solver.root_node_solver import build_b1_seed_columns
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.master.journey_rmp import manual_journey_reduced_cost
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.exact.pricing.journey_pricing import DirectPricingCache, price_direct_journey_columns
from lunar_ice_bpc.exact.solver.journey_driver import (
    enumerate_direct_journey_columns,
    solve_direct_journey_baseline,
)


B2A_MODE = "B2A_full_universe_rc_audit_fast_path"
B2B_MODE = "B2B_seeded_tail_CG"
B2B_R2_MODE = "B2B_R2_worker_before_final_judge"
B2B_R3_MODE = "B2B_R3_true_dual_negative_search_worker"
B2C_MODE = "B2C_limited_pricing_diagnostic"
B2D_MODE = "B2D_proof_tail_kernel_profile"
B2_PRODUCT_MODE = "B2_PRODUCT_EXACT_SOLVER"


@dataclass(frozen=True)
class _ManualRcAudit:
    status: str
    pass_: bool
    min_reduced_cost: float | None
    audited_column_count: int
    full_universe_complete: bool
    all_columns_in_master: bool

    def to_payload(self) -> dict:
        return {
            "status": self.status,
            "pass": bool(self.pass_),
            "min_reduced_cost": self.min_reduced_cost,
            "audited_column_count": int(self.audited_column_count),
            "full_universe_complete": bool(self.full_universe_complete),
            "all_columns_in_master": bool(self.all_columns_in_master),
        }


@dataclass(frozen=True)
class _NegativeSearchWorkerResult:
    status: PricingState
    selected_columns: tuple[JourneyColumn, ...]
    negative_pairs: tuple[tuple[float, JourneyColumn], ...]
    harvest_payload: dict
    payload: dict


def solve_b2_pricing_tail_baseline(
    data: LunarIceData,
    *,
    max_direct_tasks: int = 5,
    max_rounds: int = 8,
    negative_eps: float = 1.0e-6,
    max_columns_per_round: int = 64,
    worker_payload: dict | None = None,
    mode: str = B2B_MODE,
    seed_mode: str = "b0_incumbent_plus_singletons",
    previous_baseline: dict | None = None,
) -> dict:
    """Run a B2 root pricing-tail candidate without pre-running B1.

    ``mode=B2B_seeded_tail_CG`` is the default and starts from the B1B-style
    non-full seed pool.  ``B2A_full_universe_rc_audit_fast_path`` is explicit
    and may certify only when the full fixed pricing universe is proven loaded
    into the current master and a full-universe manual RC audit passes.
    """

    if mode == B2_PRODUCT_MODE:
        return solve_b2_product_exact_solver(data, max_direct_tasks=int(max_direct_tasks))
    if mode in {B2C_MODE, B2D_MODE}:
        diagnostic_b0 = solve_direct_journey_baseline(data, max_exact_tasks=min(int(max_direct_tasks), 10))
        return _solve_limited_pricing_diagnostic(
            data,
            b0_direct=diagnostic_b0,
            mode=str(mode),
            max_candidate_sets=max_columns_per_round,
            negative_eps=negative_eps,
            kernel_profile=(mode == B2D_MODE),
        )

    completion_policy = build_completion_bound_tail_policy(pruning_opt_in=False)
    b0_direct = solve_direct_journey_baseline(data, max_exact_tasks=int(max_direct_tasks))
    if len(data.task_ids) > int(max_direct_tasks):
        return _incomplete_payload(
            data=data,
            b0_direct=b0_direct,
            previous_baseline=previous_baseline,
            completion_policy=completion_policy,
            mode=str(mode),
            note=f"task_count={len(data.task_ids)} exceeds B2 max_direct_tasks={max_direct_tasks}",
        )

    if mode == B2A_MODE:
        return _solve_b2a_full_universe_audit(
            data,
            b0_direct=b0_direct,
            previous_baseline=previous_baseline,
            completion_policy=completion_policy,
            max_direct_tasks=int(max_direct_tasks),
            negative_eps=negative_eps,
        )
    if mode in {B2B_R2_MODE, B2B_R3_MODE}:
        return _solve_b2b_r2_worker_before_final_judge(
            data,
            b0_direct=b0_direct,
            previous_baseline=previous_baseline,
            completion_policy=completion_policy,
            max_direct_tasks=int(max_direct_tasks),
            max_rounds=int(max_rounds),
            negative_eps=negative_eps,
            max_columns_per_round=int(max_columns_per_round),
            worker_payload=worker_payload,
            seed_mode=seed_mode,
            mode=str(mode),
        )
    if mode != B2B_MODE:
        raise ValueError(f"unsupported B2 mode={mode!r}")
    return _solve_b2b_seeded_tail_cg(
        data,
        b0_direct=b0_direct,
        previous_baseline=previous_baseline,
        completion_policy=completion_policy,
        max_direct_tasks=int(max_direct_tasks),
        max_rounds=int(max_rounds),
        negative_eps=negative_eps,
        max_columns_per_round=int(max_columns_per_round),
        worker_payload=worker_payload,
        seed_mode=seed_mode,
    )


def solve_b2_product_exact_solver(
    data: LunarIceData,
    *,
    max_direct_tasks: int = 20,
    wall_time_limit_sec: float | None = None,
) -> dict:
    """Return the fixed-graph exact product solution without a BPC certificate."""

    direct = solve_direct_journey_baseline(
        data,
        max_exact_tasks=int(max_direct_tasks),
        wall_time_limit_sec=wall_time_limit_sec,
    )
    solved = direct.certificate_scope == CertificateScope.DIRECT_DP_FIXED_GRAPH_OPTIMAL.value
    return {
        "schema_version": "lunar_ice_bpc.b2_product_exact_solver.v1",
        "instance_id": data.instance_id,
        "task_count": len(data.task_ids),
        "b2_mode": B2_PRODUCT_MODE,
        "algorithm_status": direct.status,
        "certificate_scope": direct.certificate_scope,
        "pricing_state": PricingState.NOT_PRICED.value,
        "uses_true_dual_bpc_certificate": False,
        "root_lp_bound": None,
        "root_lp_bound_official": False,
        "root_bound_le_direct_dp_integer_objective": None,
        "B0_direct_objective": direct.objective,
        "product_exact_objective": direct.objective,
        "product_exact_solution_scope": direct.certificate_scope if solved else "",
        "product_exact_solution_count": 1 if solved else 0,
        "direct_dp_fallback_used": True,
        "direct_dp_fallback_count": 1 if solved else 0,
        "generated_journey_count": direct.generated_journey_count,
        "generated_sortie_count": direct.generated_sortie_count,
        "route_template_count": direct.route_template_count,
        "pareto_label_count": direct.pareto_label_count,
        "set_partition_state_count": direct.set_partition_state_count,
        "pricing_round_count": 0,
        "final_judge_call_count": 0,
        "manual_rc_audit_pass": None,
        "pricing_rc_audit_pass": None,
        "proof_debt_unreleased_count": 0,
        "completion_bound_policy": build_completion_bound_tail_policy(pruning_opt_in=False),
        "completion_bound_pruning_enabled": False,
        "exact_status": direct.exact_status,
        "fail_closed_reason": "" if solved else direct.note,
        "note": (
            "B2 product exact solver returned a fixed-graph exact product solution; this is not a BPC root/tree certificate."
            if solved
            else direct.note
        ),
    }


def _solve_limited_pricing_diagnostic(
    data: LunarIceData,
    *,
    b0_direct,
    mode: str,
    max_candidate_sets: int,
    negative_eps: float,
    kernel_profile: bool,
) -> dict:
    """Run a bounded pricing diagnostic without certificate authority."""

    from time import perf_counter

    cache = DirectPricingCache()
    limited_task_cap = (
        len(data.task_ids)
        if len(data.task_ids) <= 5
        else max(1, min(5, int(data.max_tasks_per_trip), int(len(data.task_ids) - 1)))
    )
    seed_columns, _seed_report = _build_b2b_r2_lightweight_seed_columns(
        data,
        b0_direct=b0_direct,
        seed_mode="b0_incumbent_plus_singletons",
        max_direct_tasks=max(1, min(int(len(data.task_ids)), int(max(1, max_candidate_sets)))),
        mode=mode,
    )
    rmp_start = perf_counter()
    master = solve_root_journey_master(
        data,
        seed_columns,
        negative_eps=negative_eps,
        rmp_iteration_id=f"{mode}-diagnostic-root",
    )
    rmp_wall_time = perf_counter() - rmp_start
    if master.rmp.status == "RESTRICTED_RMP_OPTIMAL":
        context = master.reduced_cost_context
        duals = _duals_from_reduced_cost_context(context)
        diagnostic_dual_source = "master.reduced_cost_context"
        diagnostic_rmp_iteration_id = context.rmp_iteration_id
        diagnostic_dual_fingerprint = context.dual_fingerprint
    else:
        context = None
        duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)
        diagnostic_dual_source = "zero_dual_fallback_rmp_not_optimal"
        diagnostic_rmp_iteration_id = ""
        diagnostic_dual_fingerprint = ""
    start = perf_counter()
    pricing, columns = price_direct_journey_columns(
        data,
        duals,
        negative_eps=negative_eps,
        max_direct_tasks=limited_task_cap,
        allow_partial=True,
        cache=cache,
        max_candidate_sets=max(1, min(8, int(max_candidate_sets))),
        completion_bound_enabled=False,
    )
    elapsed = perf_counter() - start
    negative = bool(pricing.get("negative_found"))
    cache_stats = cache.stats()
    labels_generated = int(pricing.get("pareto_label_count") or 0)
    diagnostic_scope = CertificateScope.DIAGNOSTIC_PRICING_FRONTIER
    pricing_state = PricingState.FOUND_NEGATIVE if negative else PricingState.LOCAL_NO_COLUMN_UNCERTIFIED
    return {
        "schema_version": "lunar_ice_bpc.b2_limited_pricing_diagnostic.v1",
        "instance_id": data.instance_id,
        "task_count": len(data.task_ids),
        "b2_mode": mode,
        "algorithm_status": AlgorithmStatus.BPC_INCOMPLETE_PRICING.value,
        "certificate_scope": diagnostic_scope.value,
        "pricing_state": pricing_state.value,
        "uses_true_dual_bpc_certificate": False,
        "root_lp_bound": None,
        "root_lp_bound_official": False,
        "root_bound_le_direct_dp_integer_objective": None,
        "B0_direct_objective": b0_direct.objective,
        "pricing_round_count": 0,
        "final_judge_call_count": 0,
        "candidate_negative_count": int(pricing.get("negative_column_count") or 0),
        "addable_negative_count": 0,
        "selected_count": 0,
        "added_to_master_count": 0,
        "added_column_count": 0,
        "duplicate_only_count": 0,
        "hidden_negative_count": 0,
        "replacement_only_round_count": 0,
        "manual_rc_audit_pass": None,
        "pricing_rc_audit_pass": None,
        "proof_debt_unreleased_count": 0,
        "completion_bound_policy": build_completion_bound_tail_policy(pruning_opt_in=False),
        "completion_bound_pruning_enabled": False,
        "limited_pricing": pricing,
        "rmp_wall_time": round(rmp_wall_time, 6),
        "diagnostic_dual_source": diagnostic_dual_source,
        "diagnostic_rmp_iteration_id": diagnostic_rmp_iteration_id,
        "diagnostic_dual_fingerprint": diagnostic_dual_fingerprint,
        "rmp_dual_diagnostic": _rmp_dual_diagnostic_payload(
            context=context,
            pricing_payload=pricing,
            harvest_payload=None,
            status=pricing_state,
            exit_reason=pricing_state.value,
        ),
        "worker_wall_time": round(elapsed, 6),
        "final_judge_wall_time": 0.0,
        "time_to_first_negative": round(elapsed, 6) if negative else None,
        "time_to_first_addable_negative": None,
        "labels_generated": labels_generated,
        "labels_generated_before_first_negative": labels_generated if negative else None,
        "labels_generated_total": labels_generated,
        "sortie_templates": int(pricing.get("feasible_sortie_template_count") or 0),
        "journey_labels": len(columns),
        "candidate_sequences": int(pricing.get("candidate_round_count") or 0),
        "path_option_assignments": int(pricing.get("sortie_attempt_count") or 0),
        "cache_hit_count": int(cache_stats.get("hit_count") or 0),
        "cache_miss_count": int(cache_stats.get("miss_count") or 0),
        "proof_tail_kernel_profile": {
            "enabled": bool(kernel_profile),
            "pruning_enabled": False,
            "positive_dual_ordering_profiled": bool(kernel_profile),
            "addable_negative_early_stop_enabled": False,
            "changes_certificate_semantics": False,
        },
        "exit_reason": pricing_state.value,
        "exact_status": "DIAGNOSTIC_ONLY",
        "fail_closed_reason": f"{mode}: limited pricing diagnostic cannot certify no-negative or provide an official bound.",
        "note": f"{mode} recorded bounded pricing/proof-tail diagnostics only; no certificate semantics changed.",
    }


def _solve_b2a_full_universe_audit(
    data: LunarIceData,
    *,
    b0_direct,
    previous_baseline: dict | None,
    completion_policy: dict,
    max_direct_tasks: int,
    negative_eps: float,
) -> dict:
    full_universe = enumerate_direct_journey_columns(data, max_exact_tasks=int(max_direct_tasks)).columns
    pool = ColumnPool()
    view = MasterColumnView()
    _load_columns(pool, view, full_universe)
    proof_debt = ProofDebtQueue()
    profiling = PruningCounter()
    seed_catalog = WorkerSeedCatalog()
    master = solve_root_journey_master(
        data,
        _master_columns(pool, view),
        negative_eps=negative_eps,
        rmp_iteration_id="b2a-full-universe-audit",
    )
    history: list[dict] = []
    if master.rmp.status != "RESTRICTED_RMP_OPTIMAL":
        return _payload(
            data=data,
            b0_direct=b0_direct,
            previous_baseline=previous_baseline,
            proof_debt=proof_debt,
            completion_policy=completion_policy,
            profiling=profiling,
            history=history,
            harvest_totals=_empty_harvest_totals(),
            final_judge_call_count=0,
            duplicate_only_count=0,
            hidden_negative_count=0,
            replacement_only_round_count=0,
            added_to_master_count=0,
            master=master,
            final_judge=None,
            duplicate_audit=None,
            hidden_audit=None,
            seed_catalog=seed_catalog,
            manual_rc_audit=None,
            mode=B2A_MODE,
            seed_report=_seed_report(
                mode=B2A_MODE,
                seed_mode="full_universe",
                initial_column_count=len(full_universe),
                full_universe_column_count=len(full_universe),
                full_universe_preloaded=True,
            ),
            algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
            certificate_scope=CertificateScope.DIAGNOSTIC_RMP_BOUND,
            pricing_state=PricingState.INCOMPLETE_LIMIT,
            note="B2A full-universe RMP did not solve to optimality; fail closed.",
        )

    audit = _manual_full_universe_rc_audit(
        full_universe,
        master=master,
        view=view,
        negative_eps=negative_eps,
    )
    history.append(
        {
            "round": 1,
            "root_lp_bound": master.rmp.objective_bound,
            "pricing_state": PricingState.CERTIFIED_NO_NEGATIVE.value if audit.pass_ else PricingState.INCOMPLETE_LIMIT.value,
            "full_universe_membership_rc_audit_status": audit.status,
            "full_universe_manual_min_reduced_cost": audit.min_reduced_cost,
            "full_universe_column_count": len(full_universe),
            "completion_bound_pruning_enabled": False,
        }
    )
    certified = bool(audit.pass_ and proof_debt.block_certificate_if_unreleased() is False)
    final_judge_payload = {
        "status": "FULL_UNIVERSE_MEMBERSHIP_RC_AUDIT",
        "pricing_state": PricingState.CERTIFIED_NO_NEGATIVE.value if certified else PricingState.INCOMPLETE_LIMIT.value,
        "can_certify_no_negative": bool(certified),
        "uses_true_dual_bpc_certificate": bool(certified),
        "pricing_rc_audit_pass": bool(certified),
        "manual_best_reduced_cost": audit.min_reduced_cost,
        "pricing_best_reduced_cost": audit.min_reduced_cost,
        "manual_priced_column_count": int(audit.audited_column_count),
        "completion_bound_pruning_enabled": False,
    }
    return _payload(
        data=data,
        b0_direct=b0_direct,
        previous_baseline=previous_baseline,
        proof_debt=proof_debt,
        completion_policy=completion_policy,
        profiling=profiling,
        history=history,
        harvest_totals=_empty_harvest_totals(),
        final_judge_call_count=0,
        duplicate_only_count=0,
        hidden_negative_count=0,
        replacement_only_round_count=0,
        added_to_master_count=0,
        master=master,
        final_judge=final_judge_payload,
        duplicate_audit=None,
        hidden_audit=None,
        seed_catalog=seed_catalog,
        manual_rc_audit=audit,
        mode=B2A_MODE,
        seed_report=_seed_report(
            mode=B2A_MODE,
            seed_mode="full_universe",
            initial_column_count=len(full_universe),
            full_universe_column_count=len(full_universe),
            full_universe_preloaded=True,
        ),
        algorithm_status=AlgorithmStatus.BPC_GAP_AVAILABLE if certified else AlgorithmStatus.BPC_INCOMPLETE_PRICING,
        certificate_scope=CertificateScope.BPC_NODE_LP_CERTIFIED if certified else CertificateScope.DIAGNOSTIC_RMP_BOUND,
        pricing_state=PricingState.CERTIFIED_NO_NEGATIVE if certified else PricingState.INCOMPLETE_LIMIT,
        note=(
            "B2A certified fixed-graph root LP by complete full-universe membership RC audit."
            if certified
            else "B2A full-universe audit failed; true-dual closure remains incomplete."
        ),
    )


def _solve_b2b_seeded_tail_cg(
    data: LunarIceData,
    *,
    b0_direct,
    previous_baseline: dict | None,
    completion_policy: dict,
    max_direct_tasks: int,
    max_rounds: int,
    negative_eps: float,
    max_columns_per_round: int,
    worker_payload: dict | None,
    seed_mode: str,
) -> dict:
    seed_columns, seed_report = build_b1_seed_columns(
        data,
        b0_direct=b0_direct,
        seed_mode=seed_mode,
        max_direct_tasks=max_direct_tasks,
    )
    seed_report = dict(seed_report)
    seed_report["b2_mode"] = B2B_MODE
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
    duplicate_only_count = 0
    replacement_only_round_count = 0
    hidden_negative_count = 0
    added_total = 0
    last_master = None
    last_judge_payload: dict | None = None
    last_duplicate_audit: dict | None = None
    last_hidden_audit: dict | None = None

    for round_index in range(1, max(1, int(max_rounds)) + 1):
        master_columns = _master_columns(pool, view)
        master = solve_root_journey_master(
            data,
            master_columns,
            negative_eps=negative_eps,
            rmp_iteration_id=f"b2b-root-{round_index}",
        )
        last_master = master
        if master.rmp.status != "RESTRICTED_RMP_OPTIMAL":
            return _payload(
                data=data,
                b0_direct=b0_direct,
                previous_baseline=previous_baseline,
                proof_debt=proof_debt,
                completion_policy=completion_policy,
                profiling=profiling,
                history=history,
                harvest_totals=harvest_totals,
                final_judge_call_count=final_judge_call_count,
                duplicate_only_count=duplicate_only_count,
                hidden_negative_count=hidden_negative_count,
                replacement_only_round_count=replacement_only_round_count,
                added_to_master_count=added_total,
                master=master,
                final_judge=last_judge_payload,
                duplicate_audit=last_duplicate_audit,
                hidden_audit=last_hidden_audit,
                seed_catalog=seed_catalog,
                manual_rc_audit=None,
                mode=B2B_MODE,
                seed_report=seed_report,
                algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
                certificate_scope=CertificateScope.DIAGNOSTIC_RMP_BOUND,
                pricing_state=PricingState.INCOMPLETE_LIMIT,
                note="B2B root RMP did not solve to optimality; fail closed.",
            )

        judge = run_true_dual_root_final_judge(
            data,
            master.reduced_cost_context,
            max_direct_tasks=max_direct_tasks,
            negative_eps=negative_eps,
            cache=cache,
        )
        final_judge_call_count += 1
        last_judge_payload = judge.pricing_payload
        profiling.merge_completion_payload(judge.pricing_payload)
        negative_pairs = _manual_negative_pairs(
            judge.all_priced_columns,
            duals=master.rmp.duals,
            negative_eps=negative_eps,
        )
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
        added = _add_selected_to_pool_and_master(pool, view, selected)
        harvest_payload["added_to_master_count"] = int(added)
        _accumulate_harvest_totals(harvest_totals, harvest_payload)
        added_total += added
        duplicate_audit = None
        duplicate_only_round = bool(negative_pairs and added == 0)
        if duplicate_only_round:
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
                "candidate_negative_count": int(harvest_payload["candidate_negative_count"]),
                "addable_negative_count": int(harvest_payload["addable_negative_count"]),
                "selected_count": int(harvest_payload["selected_count"]),
                "added_to_master_count": int(added),
                "added_column_count": int(added),
                "duplicate_only_audit_status": None if duplicate_audit is None else duplicate_audit.get("status"),
                "completion_bound_pruning_enabled": False,
            }
        )
        if judge.pricing_state == PricingState.CERTIFIED_NO_NEGATIVE:
            return _payload(
                data=data,
                b0_direct=b0_direct,
                previous_baseline=previous_baseline,
                proof_debt=proof_debt,
                completion_policy=completion_policy,
                profiling=profiling,
                history=history,
                harvest_totals=harvest_totals,
                final_judge_call_count=final_judge_call_count,
                duplicate_only_count=duplicate_only_count,
                hidden_negative_count=hidden_negative_count,
                replacement_only_round_count=replacement_only_round_count,
                added_to_master_count=added_total,
                master=master,
                final_judge=judge.pricing_payload,
                duplicate_audit=last_duplicate_audit,
                hidden_audit=last_hidden_audit,
                seed_catalog=seed_catalog,
                manual_rc_audit=None,
                mode=B2B_MODE,
                seed_report=seed_report,
                algorithm_status=AlgorithmStatus.BPC_GAP_AVAILABLE,
                certificate_scope=CertificateScope.BPC_NODE_LP_CERTIFIED,
                pricing_state=PricingState.CERTIFIED_NO_NEGATIVE,
                note="B2B root LP certificate preserves B1 semantics with addability-aware pricing-tail diagnostics.",
            )
        if duplicate_only_round:
            return _payload(
                data=data,
                b0_direct=b0_direct,
                previous_baseline=previous_baseline,
                proof_debt=proof_debt,
                completion_policy=completion_policy,
                profiling=profiling,
                history=history,
                harvest_totals=harvest_totals,
                final_judge_call_count=final_judge_call_count,
                duplicate_only_count=duplicate_only_count,
                hidden_negative_count=hidden_negative_count,
                replacement_only_round_count=replacement_only_round_count,
                added_to_master_count=added_total,
                master=master,
                final_judge=judge.pricing_payload,
                duplicate_audit=last_duplicate_audit,
                hidden_audit=last_hidden_audit,
                seed_catalog=seed_catalog,
                manual_rc_audit=None,
                mode=B2B_MODE,
                seed_report=seed_report,
                algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
                certificate_scope=CertificateScope.DIAGNOSTIC_PRICING_FRONTIER,
                pricing_state=PricingState.DUPLICATE_ONLY,
                note="DUPLICATE_ONLY: true-RC negative candidates were found but none entered the current master; certificate blocked.",
            )

    return _payload(
        data=data,
        b0_direct=b0_direct,
        previous_baseline=previous_baseline,
        proof_debt=proof_debt,
        completion_policy=completion_policy,
        profiling=profiling,
        history=history,
        harvest_totals=harvest_totals,
        final_judge_call_count=final_judge_call_count,
        duplicate_only_count=duplicate_only_count,
        hidden_negative_count=hidden_negative_count,
        replacement_only_round_count=replacement_only_round_count,
        added_to_master_count=added_total,
        master=last_master,
        final_judge=last_judge_payload,
        duplicate_audit=last_duplicate_audit,
        hidden_audit=last_hidden_audit,
        seed_catalog=seed_catalog,
        manual_rc_audit=None,
        mode=B2B_MODE,
        seed_report=seed_report,
        algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
        certificate_scope=CertificateScope.DIAGNOSTIC_PRICING_FRONTIER,
        pricing_state=PricingState.INCOMPLETE_LIMIT,
        note=f"Stopped after max_rounds={max_rounds}; B2B root no-negative proof is incomplete.",
    )


def _solve_b2b_r2_worker_before_final_judge(
    data: LunarIceData,
    *,
    b0_direct,
    previous_baseline: dict | None,
    completion_policy: dict,
    max_direct_tasks: int,
    max_rounds: int,
    negative_eps: float,
    max_columns_per_round: int,
    worker_payload: dict | None,
    seed_mode: str,
    mode: str = B2B_R2_MODE,
) -> dict:
    active_mode = str(mode)
    seed_columns, seed_report = _build_b2b_r2_lightweight_seed_columns(
        data,
        b0_direct=b0_direct,
        seed_mode=seed_mode,
        max_direct_tasks=max_direct_tasks,
        mode=active_mode,
    )
    pool = ColumnPool()
    view = MasterColumnView()
    _load_columns(pool, view, seed_columns)
    proof_debt = ProofDebtQueue()
    cache = DirectPricingCache()
    profiling = PruningCounter()
    seed_catalog = WorkerSeedCatalog()
    history: list[dict] = []
    harvest_totals = _empty_harvest_totals()
    profile_totals = _empty_profile_totals()
    final_judge_call_count = 0
    duplicate_only_count = 0
    replacement_only_round_count = 0
    hidden_negative_count = 0
    added_total = 0
    last_master = None
    last_judge_payload: dict | None = None
    last_duplicate_audit: dict | None = None
    last_hidden_audit: dict | None = None
    worker_only_success_count = 0

    for round_index in range(1, max(1, int(max_rounds)) + 1):
        master_columns = _master_columns(pool, view)
        rmp_start = perf_counter()
        master = solve_root_journey_master(
            data,
            master_columns,
            negative_eps=negative_eps,
            rmp_iteration_id=f"{active_mode}-root-{round_index}",
        )
        rmp_wall_time = perf_counter() - rmp_start
        profile_totals["rmp_wall_time"] += rmp_wall_time
        last_master = master
        if master.rmp.status != "RESTRICTED_RMP_OPTIMAL":
            profile_totals["exit_reason"] = "RMP_NOT_OPTIMAL"
            return _payload(
                data=data,
                b0_direct=b0_direct,
                previous_baseline=previous_baseline,
                proof_debt=proof_debt,
                completion_policy=completion_policy,
                profiling=profiling,
                history=history,
                harvest_totals=harvest_totals,
                final_judge_call_count=final_judge_call_count,
                duplicate_only_count=duplicate_only_count,
                hidden_negative_count=hidden_negative_count,
                replacement_only_round_count=replacement_only_round_count,
                added_to_master_count=added_total,
                master=master,
                final_judge=last_judge_payload,
                duplicate_audit=last_duplicate_audit,
                hidden_audit=last_hidden_audit,
                seed_catalog=seed_catalog,
                manual_rc_audit=None,
                mode=active_mode,
                seed_report=seed_report,
                algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
                certificate_scope=CertificateScope.DIAGNOSTIC_RMP_BOUND,
                pricing_state=PricingState.INCOMPLETE_LIMIT,
                note=f"{active_mode} root RMP did not solve to optimality; fail closed.",
                profile_totals=profile_totals,
            )

        worker = _run_negative_search_worker(
            data,
            master=master,
            reduced_cost_context=master.reduced_cost_context,
            master_columns=master_columns,
            b0_direct=b0_direct,
            pool=pool,
            view=view,
            cache=cache,
            seed_catalog=seed_catalog,
            profiling=profiling,
            round_index=round_index,
            max_direct_tasks=max_direct_tasks,
            max_candidate_sets=max_columns_per_round,
            negative_eps=negative_eps,
            max_selected=max_columns_per_round,
        )
        _accumulate_worker_profile(profile_totals, worker.payload)
        if worker.status == PricingState.FOUND_NEGATIVE and worker.selected_columns:
            added = _add_selected_to_pool_and_master(pool, view, worker.selected_columns)
            harvest_payload = dict(worker.harvest_payload)
            harvest_payload["added_to_master_count"] = int(added)
            _accumulate_harvest_totals(harvest_totals, harvest_payload)
            added_total += added
            if added > 0:
                worker_only_success_count += 1
                defer_final_judge = (
                    int(max_rounds) <= 1
                    or (
                        worker_only_success_count < _b2b_r2_worker_only_round_limit(max_rounds)
                        and round_index < int(max_rounds)
                    )
                )
                if defer_final_judge:
                    profile_totals["final_judge_saved_by_worker_count"] += 1
                    profile_totals["exit_reason"] = "WORKER_FOUND_ADDABLE_NEGATIVE"
                    history.append(
                        {
                            "round": round_index,
                            "root_lp_bound": master.rmp.objective_bound,
                            "pricing_state": PricingState.FOUND_NEGATIVE.value,
                            "worker_status": worker.status.value,
                            "worker_exit_reason": worker.payload.get("exit_reason"),
                            "worker_wall_time": worker.payload.get("worker_wall_time"),
                            **_worker_round_diagnostic_fields(worker.payload),
                            "final_judge_called": False,
                            "candidate_negative_count": int(harvest_payload["candidate_negative_count"]),
                            "addable_negative_count": int(harvest_payload["addable_negative_count"]),
                            "selected_count": int(harvest_payload["selected_count"]),
                            "added_to_master_count": int(added),
                            "added_column_count": int(added),
                            "completion_bound_pruning_enabled": False,
                        }
                    )
                    continue

                profile_totals["exit_reason"] = "WORKER_PROGRESS_REQUIRES_FINAL_JUDGE"
                master_columns = _master_columns(pool, view)
                rmp_start = perf_counter()
                master = solve_root_journey_master(
                    data,
                    master_columns,
                    negative_eps=negative_eps,
                    rmp_iteration_id=f"{active_mode}-root-{round_index}-closure",
                )
                rmp_wall_time = perf_counter() - rmp_start
                profile_totals["rmp_wall_time"] += rmp_wall_time
                last_master = master
                if master.rmp.status != "RESTRICTED_RMP_OPTIMAL":
                    profile_totals["exit_reason"] = "RMP_NOT_OPTIMAL_AFTER_WORKER_PROGRESS"
                    return _payload(
                        data=data,
                        b0_direct=b0_direct,
                        previous_baseline=previous_baseline,
                        proof_debt=proof_debt,
                        completion_policy=completion_policy,
                        profiling=profiling,
                        history=history,
                        harvest_totals=harvest_totals,
                        final_judge_call_count=final_judge_call_count,
                        duplicate_only_count=duplicate_only_count,
                        hidden_negative_count=hidden_negative_count,
                        replacement_only_round_count=replacement_only_round_count,
                        added_to_master_count=added_total,
                        master=master,
                        final_judge=last_judge_payload,
                        duplicate_audit=last_duplicate_audit,
                        hidden_audit=last_hidden_audit,
                        seed_catalog=seed_catalog,
                        manual_rc_audit=None,
                        mode=active_mode,
                        seed_report=seed_report,
                        algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
                        certificate_scope=CertificateScope.DIAGNOSTIC_RMP_BOUND,
                        pricing_state=PricingState.INCOMPLETE_LIMIT,
                        note=f"{active_mode} root RMP did not solve after worker progress; fail closed.",
                        profile_totals=profile_totals,
                    )
                worker_only_success_count = 0

        worker_only_success_count = 0
        judge_start = perf_counter()
        judge = run_true_dual_root_final_judge(
            data,
            master.reduced_cost_context,
            max_direct_tasks=max_direct_tasks,
            negative_eps=negative_eps,
            cache=cache,
        )
        judge_wall_time = perf_counter() - judge_start
        profile_totals["final_judge_wall_time"] += judge_wall_time
        profile_totals["final_judge_call_count_profiled"] += 1
        final_judge_call_count += 1
        last_judge_payload = judge.pricing_payload
        profiling.merge_completion_payload(judge.pricing_payload)
        _accumulate_pricing_profile(profile_totals, judge.pricing_payload)
        negative_pairs = _manual_negative_pairs(
            judge.all_priced_columns,
            duals=master.rmp.duals,
            negative_eps=negative_eps,
        )
        hidden_audit = build_hidden_negative_audit(
            worker_payload=worker_payload or worker.payload,
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
        added = _add_selected_to_pool_and_master(pool, view, selected)
        harvest_payload["added_to_master_count"] = int(added)
        _accumulate_harvest_totals(harvest_totals, harvest_payload)
        added_total += added
        duplicate_audit = None
        duplicate_only_round = bool(negative_pairs and added == 0)
        if duplicate_only_round:
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
        profile_totals["exit_reason"] = (
            "FINAL_JUDGE_CERTIFIED_NO_NEGATIVE"
            if judge.pricing_state == PricingState.CERTIFIED_NO_NEGATIVE
            else "FINAL_JUDGE_FOUND_NEGATIVE"
            if judge.pricing_state == PricingState.FOUND_NEGATIVE
            else "FINAL_JUDGE_INCOMPLETE_LIMIT"
        )
        history.append(
            {
                "round": round_index,
                "root_lp_bound": master.rmp.objective_bound,
                "pricing_state": judge.pricing_state.value,
                "worker_status": worker.status.value,
                "worker_exit_reason": worker.payload.get("exit_reason"),
                "worker_wall_time": worker.payload.get("worker_wall_time"),
                **_worker_round_diagnostic_fields(worker.payload),
                "final_judge_called": True,
                "final_judge_wall_time": round(judge_wall_time, 6),
                "candidate_negative_count": int(harvest_payload["candidate_negative_count"]),
                "addable_negative_count": int(harvest_payload["addable_negative_count"]),
                "selected_count": int(harvest_payload["selected_count"]),
                "added_to_master_count": int(added),
                "added_column_count": int(added),
                "duplicate_only_audit_status": None if duplicate_audit is None else duplicate_audit.get("status"),
                "completion_bound_pruning_enabled": False,
            }
        )
        if judge.pricing_state == PricingState.CERTIFIED_NO_NEGATIVE:
            return _payload(
                data=data,
                b0_direct=b0_direct,
                previous_baseline=previous_baseline,
                proof_debt=proof_debt,
                completion_policy=completion_policy,
                profiling=profiling,
                history=history,
                harvest_totals=harvest_totals,
                final_judge_call_count=final_judge_call_count,
                duplicate_only_count=duplicate_only_count,
                hidden_negative_count=hidden_negative_count,
                replacement_only_round_count=replacement_only_round_count,
                added_to_master_count=added_total,
                master=master,
                final_judge=judge.pricing_payload,
                duplicate_audit=last_duplicate_audit,
                hidden_audit=last_hidden_audit,
                seed_catalog=seed_catalog,
                manual_rc_audit=None,
                mode=active_mode,
                seed_report=seed_report,
                algorithm_status=AlgorithmStatus.BPC_GAP_AVAILABLE,
                certificate_scope=CertificateScope.BPC_NODE_LP_CERTIFIED,
                pricing_state=PricingState.CERTIFIED_NO_NEGATIVE,
                note=f"{active_mode} root LP certificate came only from the true-dual final judge after worker-before-final-judge rounds.",
                profile_totals=profile_totals,
            )
        if duplicate_only_round:
            profile_totals["exit_reason"] = "DUPLICATE_ONLY"
            return _payload(
                data=data,
                b0_direct=b0_direct,
                previous_baseline=previous_baseline,
                proof_debt=proof_debt,
                completion_policy=completion_policy,
                profiling=profiling,
                history=history,
                harvest_totals=harvest_totals,
                final_judge_call_count=final_judge_call_count,
                duplicate_only_count=duplicate_only_count,
                hidden_negative_count=hidden_negative_count,
                replacement_only_round_count=replacement_only_round_count,
                added_to_master_count=added_total,
                master=master,
                final_judge=judge.pricing_payload,
                duplicate_audit=last_duplicate_audit,
                hidden_audit=last_hidden_audit,
                seed_catalog=seed_catalog,
                manual_rc_audit=None,
                mode=active_mode,
                seed_report=seed_report,
                algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
                certificate_scope=CertificateScope.DIAGNOSTIC_PRICING_FRONTIER,
                pricing_state=PricingState.DUPLICATE_ONLY,
                note="DUPLICATE_ONLY: true-RC negative candidates were found but none entered the current master; certificate blocked.",
                profile_totals=profile_totals,
            )

    profile_totals["exit_reason"] = "ROW_TIME_LIMIT" if not history else "WORKER_INCOMPLETE_LIMIT"
    return _payload(
        data=data,
        b0_direct=b0_direct,
        previous_baseline=previous_baseline,
        proof_debt=proof_debt,
        completion_policy=completion_policy,
        profiling=profiling,
        history=history,
        harvest_totals=harvest_totals,
        final_judge_call_count=final_judge_call_count,
        duplicate_only_count=duplicate_only_count,
        hidden_negative_count=hidden_negative_count,
        replacement_only_round_count=replacement_only_round_count,
        added_to_master_count=added_total,
        master=last_master,
        final_judge=last_judge_payload,
        duplicate_audit=last_duplicate_audit,
        hidden_audit=last_hidden_audit,
        seed_catalog=seed_catalog,
        manual_rc_audit=None,
        mode=active_mode,
        seed_report=seed_report,
        algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
        certificate_scope=CertificateScope.DIAGNOSTIC_PRICING_FRONTIER,
        pricing_state=PricingState.INCOMPLETE_LIMIT,
        note=f"Stopped after max_rounds={max_rounds}; {active_mode} worker/final-judge root proof is incomplete.",
        profile_totals=profile_totals,
    )


def _worker_round_diagnostic_fields(payload: dict) -> dict:
    return {
        "diagnostic_dual_source": payload.get("diagnostic_dual_source") or "",
        "diagnostic_rmp_iteration_id": payload.get("diagnostic_rmp_iteration_id") or "",
        "diagnostic_dual_fingerprint": payload.get("diagnostic_dual_fingerprint") or "",
        "time_to_first_negative": payload.get("time_to_first_negative"),
        "time_to_first_addable_negative": payload.get("time_to_first_addable_negative"),
        "labels_generated": int(payload.get("labels_generated") or 0),
        "labels_generated_before_first_negative": payload.get("labels_generated_before_first_negative"),
        "labels_generated_total": int(payload.get("labels_generated_total") or payload.get("labels_generated") or 0),
        "labels_extended": int(payload.get("labels_extended") or 0),
        "sortie_templates": int(payload.get("sortie_templates") or 0),
        "journey_labels": int(payload.get("journey_labels") or 0),
        "candidate_sequences": int(payload.get("candidate_sequence_count") or payload.get("candidate_sequences") or 0),
        "path_option_assignments": int(payload.get("path_option_assignments") or 0),
        "cache_hit_count": int(payload.get("cache_hit_count") or 0),
        "cache_miss_count": int(payload.get("cache_miss_count") or 0),
        "rmp_dual_diagnostic": payload.get("rmp_dual_diagnostic") or {},
    }


def _run_negative_search_worker(
    data: LunarIceData,
    *,
    master,
    reduced_cost_context,
    master_columns: tuple[JourneyColumn, ...],
    b0_direct,
    pool: ColumnPool,
    view: MasterColumnView,
    cache: DirectPricingCache,
    seed_catalog: WorkerSeedCatalog,
    profiling: PruningCounter,
    round_index: int,
    max_direct_tasks: int,
    max_candidate_sets: int,
    negative_eps: float,
    max_selected: int,
) -> _NegativeSearchWorkerResult:
    worker_start = perf_counter()
    duals = _duals_from_reduced_cost_context(reduced_cost_context)
    worker_task_cap = _worker_task_cap(data, max_direct_tasks)
    seed_task_sets = _negative_worker_seed_task_sets(
        data,
        duals=duals,
        master_columns=master_columns,
        b0_direct=b0_direct,
        seed_catalog=seed_catalog,
        max_direct_tasks=worker_task_cap,
        max_seed_sets=max(1, int(max_candidate_sets)),
    )
    pricing, priced_columns = price_direct_journey_columns(
        data,
        duals,
        negative_eps=negative_eps,
        max_direct_tasks=worker_task_cap,
        allow_partial=True,
        seed_task_sets=seed_task_sets,
        cache=cache,
        max_candidate_sets=max(1, int(max_candidate_sets)),
        completion_bound_enabled=False,
    )
    negative_pairs = _manual_negative_pairs(
        priced_columns,
        duals=duals,
        negative_eps=negative_eps,
    )
    selected, harvest_payload = harvest_addable_negative_columns(
        negative_pairs,
        pool=pool,
        view=view,
        node_id="root",
        negative_eps=negative_eps,
        max_selected=max_selected,
        active_task_sets={frozenset(column.task_set) for column in master_columns},
        profiling=profiling,
    )
    worker_wall_time = perf_counter() - worker_start
    cache_stats = cache.stats()
    completion_payload = pricing.get("completion_bound") if isinstance(pricing.get("completion_bound"), dict) else {}
    labels_generated = int(pricing.get("pareto_label_count") or 0)
    status = PricingState.FOUND_NEGATIVE if negative_pairs else PricingState.LOCAL_NO_COLUMN_UNCERTIFIED
    if str(pricing.get("status") or "").startswith("SKIPPED"):
        status = PricingState.INCOMPLETE_LIMIT
    exit_reason = (
        "WORKER_FOUND_ADDABLE_NEGATIVE"
        if selected
        else "WORKER_FOUND_NEGATIVE_NOT_ADDABLE"
        if negative_pairs
        else "WORKER_INCOMPLETE_LIMIT"
        if status == PricingState.INCOMPLETE_LIMIT
        else "WORKER_NO_COLUMN_UNCERTIFIED"
    )
    payload = {
        "schema_version": "lunar_ice_bpc.b2e_negative_search_worker.v1",
        "worker_kind": "B2E_negative_search_worker",
        "round": int(round_index),
        "worker_status": status.value,
        "pricing_state": status.value,
        "exit_reason": exit_reason,
        "can_certify_no_negative": False,
        "uses_true_dual_bpc_certificate": False,
        "root_lp_bound_official": False,
        "dual_source": "master.reduced_cost_context",
        "diagnostic_dual_source": "master.reduced_cost_context",
        "diagnostic_rmp_iteration_id": str(getattr(reduced_cost_context, "rmp_iteration_id", "") or ""),
        "diagnostic_dual_fingerprint": str(getattr(reduced_cost_context, "dual_fingerprint", "") or ""),
        "completion_bound_pruning_enabled": False,
        "worker_wall_time": round(worker_wall_time, 6),
        "time_to_first_negative": round(worker_wall_time, 6) if negative_pairs else None,
        "time_to_first_addable_negative": round(worker_wall_time, 6) if selected else None,
        "candidate_task_set_count": int(pricing.get("candidate_round_count") or 0),
        "candidate_sequence_count": int(pricing.get("candidate_round_count") or 0),
        "labels_generated": labels_generated,
        "labels_generated_before_first_negative": labels_generated if negative_pairs else None,
        "labels_generated_total": labels_generated,
        "labels_extended": int(pricing.get("sortie_attempt_count") or 0),
        "sortie_templates": int(pricing.get("feasible_sortie_template_count") or 0),
        "journey_labels": len(priced_columns),
        "candidate_sequences": int(pricing.get("candidate_round_count") or 0),
        "path_option_assignments": int(pricing.get("sortie_attempt_count") or 0),
        "resource_prune_count": 0,
        "time_window_prune_count": 0,
        "dominance_prune_count": int((harvest_payload.get("harvest_dominance_filtered_count") or 0)),
        "bound_prune_count": int(completion_payload.get("pruned_label_count") or 0),
        "cache_hit_count": int(cache_stats.get("hit_count") or 0),
        "cache_miss_count": int(cache_stats.get("miss_count") or 0),
        "candidate_negative_count": int(harvest_payload.get("candidate_negative_count") or 0),
        "addable_negative_count": int(harvest_payload.get("addable_negative_count") or 0),
        "duplicate_negative_count": int(harvest_payload.get("duplicate_in_current_master_count") or 0),
        "selected_count": int(harvest_payload.get("selected_count") or 0),
        "manual_rc_validated_negative_count": len(negative_pairs),
        "seed_task_set_count": len(seed_task_sets),
        "worker_task_cap": int(worker_task_cap),
        "pricing_payload": pricing,
        "harvest_payload": harvest_payload,
        "rmp_dual_diagnostic": _rmp_dual_diagnostic_payload(
            context=reduced_cost_context,
            pricing_payload=pricing,
            harvest_payload=harvest_payload,
            status=status,
            exit_reason=exit_reason,
        ),
        "feasibility_cache": _feasibility_cache_payload(cache_stats),
        "exact_first_step_bound_profile": _exact_first_step_bound_profile(completion_payload),
        "note": "B2E worker is a negative-search worker only; local no-column is not a no-negative certificate.",
    }
    return _NegativeSearchWorkerResult(
        status=status,
        selected_columns=tuple(selected),
        negative_pairs=negative_pairs,
        harvest_payload=harvest_payload,
        payload=payload,
    )


def _build_b2b_r2_lightweight_seed_columns(
    data: LunarIceData,
    *,
    b0_direct,
    seed_mode: str,
    max_direct_tasks: int,
    mode: str = B2B_R2_MODE,
) -> tuple[tuple[JourneyColumn, ...], dict]:
    """Build B2B_R2 seeds without full-universe enumeration.

    B1/B2B keep their proof-audit seed builder.  Round2's worker path must avoid
    paying that full-universe cost before it can even start negative search.
    """

    resolved_mode = str(seed_mode)
    if resolved_mode not in {"b0_incumbent_plus_singletons", "b0_incumbent"}:
        seed_columns, seed_report = build_b1_seed_columns(
            data,
            b0_direct=b0_direct,
            seed_mode=seed_mode,
            max_direct_tasks=max_direct_tasks,
        )
        seed_report = dict(seed_report)
        seed_report["b2_mode"] = str(mode)
        seed_report["seed_builder"] = "b1_seed_builder_fallback"
        return seed_columns, seed_report

    columns: list[JourneyColumn] = list(tuple(getattr(b0_direct, "journeys", tuple()) or tuple()))
    if resolved_mode == "b0_incumbent_plus_singletons":
        columns.extend(_price_singleton_seed_columns(data))
    seed_columns = _dedupe_journey_columns(columns)
    return seed_columns, {
        "b1_mode": "B1B_seeded_root_CG",
        "b2_mode": str(mode),
        "seed_mode": resolved_mode,
        "seed_builder": (
            "b2b_r3_lightweight_no_full_universe_enumeration"
            if str(mode) == B2B_R3_MODE
            else "b2b_r2_lightweight_no_full_universe_enumeration"
        ),
        "initial_column_count": len(seed_columns),
        "full_universe_column_count": None,
        "full_universe_preloaded": False,
    }


def _price_singleton_seed_columns(data: LunarIceData) -> tuple[JourneyColumn, ...]:
    if not data.task_ids:
        return tuple()
    zero_duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)
    seed_task_sets = tuple((str(task_id),) for task_id in data.task_ids)
    _pricing, columns = price_direct_journey_columns(
        data,
        zero_duals,
        negative_eps=1.0e-12,
        max_direct_tasks=1,
        allow_partial=True,
        seed_task_sets=seed_task_sets,
        cache=DirectPricingCache(),
        max_candidate_sets=len(seed_task_sets),
        completion_bound_enabled=False,
    )
    return tuple(column for column in columns if len(column.task_set) == 1)


def _dedupe_journey_columns(columns: Iterable[JourneyColumn]) -> tuple[JourneyColumn, ...]:
    unique: list[JourneyColumn] = []
    seen = set()
    for column in columns:
        signature = column_signature_from_journey(column)
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(column)
    return tuple(unique)


def _manual_negative_pairs(
    columns: Iterable[JourneyColumn],
    *,
    duals: JourneyDuals,
    negative_eps: float,
) -> tuple[tuple[float, JourneyColumn], ...]:
    pairs: list[tuple[float, JourneyColumn]] = []
    threshold = -abs(float(negative_eps))
    for column in columns:
        rc = manual_journey_reduced_cost(column, duals)
        if rc < threshold:
            pairs.append((rc, column))
    return tuple(pairs)


def _duals_from_reduced_cost_context(context) -> JourneyDuals:
    return JourneyDuals(
        cover={str(key): float(value) for key, value in getattr(context, "task_duals", {}).items()},
        fleet_limit=float(getattr(context, "fleet_dual", 0.0)),
        cuts={str(key): float(value) for key, value in getattr(context, "cut_duals", {}).items()},
    )


def _rmp_dual_diagnostic_payload(
    *,
    context,
    pricing_payload: dict,
    harvest_payload: dict | None,
    status: PricingState,
    exit_reason: str,
) -> dict:
    harvest_payload = harvest_payload or {}
    if context is None:
        return {
            "schema_version": "lunar_ice_bpc.b2_rmp_dual_pricing_diagnostic.v1",
            "dual_source": "zero_dual_fallback_rmp_not_optimal",
            "rmp_iteration_id": "",
            "dual_fingerprint": "",
            "pricing_state": status.value,
            "exit_reason": str(exit_reason),
            "can_certify_no_negative": False,
            "uses_true_dual_bpc_certificate": False,
        }
    labels_generated = int(pricing_payload.get("pareto_label_count") or pricing_payload.get("labels_generated") or 0)
    return {
        "schema_version": "lunar_ice_bpc.b2_rmp_dual_pricing_diagnostic.v1",
        "dual_source": "master.reduced_cost_context",
        "rmp_iteration_id": str(getattr(context, "rmp_iteration_id", "") or ""),
        "dual_fingerprint": str(getattr(context, "dual_fingerprint", "") or ""),
        "pricing_state": status.value,
        "exit_reason": str(exit_reason),
        "time_to_first_negative": None,
        "time_to_first_addable_negative": None,
        "labels_generated_before_first_negative": labels_generated if int(harvest_payload.get("candidate_negative_count") or 0) > 0 else None,
        "labels_generated_total": labels_generated,
        "labels_generated": labels_generated,
        "sortie_templates": int(pricing_payload.get("feasible_sortie_template_count") or pricing_payload.get("sortie_templates") or 0),
        "journey_labels": int(pricing_payload.get("negative_column_count") or pricing_payload.get("journey_labels") or 0),
        "candidate_sequences": int(pricing_payload.get("candidate_round_count") or pricing_payload.get("candidate_sequences") or 0),
        "path_option_assignments": int(pricing_payload.get("sortie_attempt_count") or pricing_payload.get("path_option_assignments") or 0),
        "cache_hit_count": int((pricing_payload.get("sortie_template_cache") or {}).get("hit_count") or 0),
        "cache_miss_count": int((pricing_payload.get("sortie_template_cache") or {}).get("miss_count") or 0),
        "candidate_negative_count": int(harvest_payload.get("candidate_negative_count") or 0),
        "addable_negative_count": int(harvest_payload.get("addable_negative_count") or 0),
        "can_certify_no_negative": False,
        "uses_true_dual_bpc_certificate": False,
        "root_lp_bound_official": False,
    }


def _worker_task_cap(data: LunarIceData, max_direct_tasks: int) -> int:
    if len(data.task_ids) <= 5:
        return min(len(data.task_ids), int(max_direct_tasks))
    return max(1, min(int(max_direct_tasks), int(data.max_tasks_per_trip), 3, len(data.task_ids) - 1))


def _b2b_r2_worker_only_round_limit(max_rounds: int) -> int:
    return max(1, min(4, max(1, int(max_rounds) - 1)))


def _negative_worker_seed_task_sets(
    data: LunarIceData,
    *,
    duals: JourneyDuals,
    master_columns: tuple[JourneyColumn, ...],
    b0_direct,
    seed_catalog: WorkerSeedCatalog,
    max_direct_tasks: int,
    max_seed_sets: int,
) -> tuple[tuple[str, ...], ...]:
    all_tasks = {str(task_id) for task_id in data.task_ids}
    ranked = sorted(
        all_tasks,
        key=lambda task_id: (
            -float(duals.cover.get(task_id, 0.0)),
            -float(data.tasks[task_id].science_weight),
            task_id,
        ),
    )
    max_size = max(1, min(3, int(max_direct_tasks), int(data.max_tasks_per_trip)))
    rows: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()

    def add(row: Iterable[str]) -> None:
        cleaned = tuple(str(task_id) for task_id in row if str(task_id) in all_tasks)
        normalized = tuple(sorted(cleaned))
        if not normalized or len(normalized) > int(max_direct_tasks) or normalized in seen:
            return
        seen.add(normalized)
        rows.append(normalized)

    if len(data.task_ids) <= 5:
        add(tuple(ranked[: min(int(max_direct_tasks), len(ranked))]))
    for column in tuple(getattr(b0_direct, "journeys", tuple()) or tuple()):
        add(tuple(sorted(column.task_set)))
    for column in master_columns:
        add(tuple(sorted(column.task_set)))
    for row in seed_catalog.rows:
        add(tuple(row.get("task_set") or tuple()))
    for size in range(1, max_size + 1):
        for combo in combinations(ranked[: max(int(max_direct_tasks) + 3, max_size)], size):
            add(combo)
    return tuple(rows[: max(1, int(max_seed_sets))])


def _manual_full_universe_rc_audit(
    full_universe: Iterable[JourneyColumn],
    *,
    master,
    view: MasterColumnView,
    negative_eps: float,
) -> _ManualRcAudit:
    columns = tuple(full_universe)
    values = tuple(manual_journey_reduced_cost(column, master.rmp.duals) for column in columns)
    min_rc = min(values) if values else None
    signatures = {column_signature_from_journey(column) for column in columns}
    master_signatures = view.signatures_by_node.get("root", set())
    all_in_master = signatures.issubset(master_signatures) and len(signatures) == len(master_signatures)
    passed = bool(
        columns
        and all_in_master
        and min_rc is not None
        and float(min_rc) >= -abs(float(negative_eps))
        and master.reduced_cost_audit.get("dual_fingerprint_bound_to_rmp") is True
    )
    return _ManualRcAudit(
        status="FULL_UNIVERSE_RC_AUDIT_PASS" if passed else "FULL_UNIVERSE_RC_AUDIT_FAIL",
        pass_=passed,
        min_reduced_cost=min_rc,
        audited_column_count=len(columns),
        full_universe_complete=True,
        all_columns_in_master=all_in_master,
    )


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
    b0_direct,
    previous_baseline: dict | None,
    proof_debt: ProofDebtQueue,
    completion_policy: dict,
    profiling: PruningCounter,
    history: list[dict],
    harvest_totals: dict[str, int],
    final_judge_call_count: int,
    duplicate_only_count: int,
    hidden_negative_count: int,
    replacement_only_round_count: int,
    added_to_master_count: int,
    master,
    final_judge: dict | None,
    duplicate_audit: dict | None,
    hidden_audit: dict | None,
    seed_catalog: WorkerSeedCatalog,
    manual_rc_audit: _ManualRcAudit | None,
    mode: str,
    seed_report: dict,
    algorithm_status: AlgorithmStatus,
    certificate_scope: CertificateScope,
    pricing_state: PricingState,
    note: str,
    profile_totals: dict | None = None,
) -> dict:
    root_objective = None if master is None else master.rmp.objective_bound
    b0_objective = b0_direct.objective
    root_le_b0 = (
        None
        if root_objective is None or b0_objective is None
        else float(root_objective) <= float(b0_objective) + 1.0e-6
    )
    root_gap = (
        None
        if root_objective is None or b0_objective is None
        else round(float(b0_objective) - float(root_objective), 9)
    )
    manual_rc_audit_pass = _manual_rc_audit_pass(master, manual_rc_audit)
    pricing_rc_audit_pass = bool(final_judge and final_judge.get("pricing_rc_audit_pass") is True)
    previous_diff = _previous_baseline_diff(previous_baseline, root_objective, certificate_scope)
    gate_issues: list[str] = []
    if root_le_b0 is False:
        gate_issues.append("root_lp_bound_exceeds_direct_dp_integer_objective")
    if previous_diff["objective_diff_vs_previous"] not in {None, 0.0}:
        gate_issues.append("objective_diff_vs_previous_nonzero")
    if previous_diff["certificate_scope_diff_vs_previous"]:
        gate_issues.append("certificate_scope_diff_vs_previous_nonempty")
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
    duplicate_audit = duplicate_audit or {}
    hidden_audit = hidden_audit or {"hidden_negative_count": 0, "rows": []}
    candidate_negative_count = int(harvest_totals.get("candidate_negative_count") or 0)
    addable_negative_count = int(harvest_totals.get("addable_negative_count") or 0)
    selected_count = int(harvest_totals.get("selected_count") or 0)
    selected_would_enter_master_count = int(harvest_totals.get("selected_would_enter_master_count") or 0)
    profile_payload = _profile_payload(profile_totals, profiling, final_judge)
    return {
        "schema_version": "lunar_ice_bpc.b2_pricing_tail_baseline.v2",
        "instance_id": data.instance_id,
        "task_count": len(data.task_ids),
        "b2_mode": str(mode),
        "seed_mode": seed_report.get("seed_mode"),
        "seed_builder": seed_report.get("seed_builder") or "",
        "initial_column_count": int(seed_report.get("initial_column_count") or 0),
        "full_universe_column_count": seed_report.get("full_universe_column_count"),
        "full_universe_preloaded": bool(seed_report.get("full_universe_preloaded")),
        "completion_bound_pruning_enabled": bool(completion_policy.get("pruning_enabled")),
        "algorithm_status": algorithm_status.value,
        "certificate_scope": certificate_scope.value,
        "pricing_state": pricing_state.value,
        "uses_true_dual_bpc_certificate": ledger_payload["uses_true_dual_bpc_certificate"],
        "certificate_ledger": ledger_payload,
        "completion_bound_policy": completion_policy,
        "root_rmp_status": None if master is None else master.rmp.status,
        "root_rmp_objective": root_objective,
        "root_lp_bound": root_objective,
        "root_lp_bound_official": root_lp_bound_official,
        "root_bound_le_direct_dp_integer_objective": root_le_b0,
        "root_lp_vs_direct_dp_gap": root_gap,
        "integral_root": None if root_gap is None else abs(float(root_gap)) <= 1.0e-6,
        "rmp_iteration_count": 0 if master is None else master.rmp.iteration_count,
        "pricing_round_count": len(history),
        "final_judge_call_count": int(final_judge_call_count),
        "final_judge": final_judge or {},
        "history": list(history),
        "proof_debt_queue": proof_debt.audit(),
        "proof_debt_unreleased_count": len(proof_debt.unreleased),
        "profiling": profiling.to_payload(),
        "manual_rc_audit": None if manual_rc_audit is None else manual_rc_audit.to_payload(),
        "manual_rc_audit_pass": manual_rc_audit_pass,
        "pricing_rc_audit_pass": pricing_rc_audit_pass,
        "duplicate_only_audit": duplicate_audit,
        "duplicate_only_audit_status": duplicate_audit.get("status"),
        "hidden_negative_audit": hidden_audit,
        "worker_seed_catalog": seed_catalog.to_payload(),
        "previous_baseline": previous_diff,
        "b1_ablation": {
            "baseline": previous_diff["previous_baseline_name"],
            "previous_algorithm_status": previous_diff["previous_algorithm_status"],
            "previous_certificate_scope": previous_diff["previous_certificate_scope"],
            "previous_root_lp_bound": previous_diff["previous_root_lp_bound"],
            "objective_diff_vs_B1": previous_diff["objective_diff_vs_previous"],
            "certificate_scope_diff_vs_B1": previous_diff["certificate_scope_diff_vs_previous"],
            "final_judge_call_count_vs_B1": (
                None
                if previous_diff["previous_final_judge_call_count"] is None
                else int(final_judge_call_count) - int(previous_diff["previous_final_judge_call_count"])
            ),
        },
        "objective_diff_vs_B1": previous_diff["objective_diff_vs_previous"],
        "certificate_scope_diff_vs_B1": previous_diff["certificate_scope_diff_vs_previous"],
        "candidate_negative_count": candidate_negative_count,
        "addable_negative_count": addable_negative_count,
        "duplicate_in_current_master_count": int(harvest_totals.get("duplicate_in_current_master_count") or 0),
        "in_pool_not_master_count": int(harvest_totals.get("in_pool_not_master_count") or 0),
        "forbidden_signature_count": int(harvest_totals.get("forbidden_signature_count") or 0),
        "branch_filtered_count": int(harvest_totals.get("branch_filtered_count") or 0),
        "cut_filtered_count": int(harvest_totals.get("cut_filtered_count") or 0),
        "selected_count": selected_count,
        "selected_would_enter_master_count": selected_would_enter_master_count,
        "selected_all_would_enter_master": selected_would_enter_master_count == selected_count,
        "added_to_master_count": int(added_to_master_count),
        "added_column_count": int(added_to_master_count),
        "candidate_addable_ratio": (
            None if candidate_negative_count == 0 else round(addable_negative_count / candidate_negative_count, 9)
        ),
        "duplicate_only_count": int(duplicate_only_count),
        "hidden_negative_count": int(hidden_negative_count),
        "replacement_only_round_count": int(replacement_only_round_count),
        **profile_payload,
        **harvest_totals,
        "b0_ablation": {
            "baseline": "B0_DIRECT_DP_FIXED_GRAPH_ORACLE",
            "direct_dp_status": b0_direct.status,
            "direct_dp_certificate_scope": b0_direct.certificate_scope,
            "direct_dp_objective": b0_objective,
            "root_lp_bound": root_objective,
            "root_lp_vs_direct_dp_gap": root_gap,
            "root_bound_le_direct_dp_integer_objective": root_le_b0,
        },
        "exact_status": (
            "BPC_NODE_LP_CERTIFIED"
            if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and ledger_payload["valid"]
            else "NOT_SOLVED"
        ),
        "fail_closed_reason": "" if root_lp_bound_official else note,
        "note": note,
    }


def _manual_rc_audit_pass(master, manual_rc_audit: _ManualRcAudit | None) -> bool:
    if manual_rc_audit is not None:
        return bool(manual_rc_audit.pass_)
    return bool(
        master is not None
        and master.reduced_cost_audit.get("dual_fingerprint_bound_to_rmp") is True
        and (
            master.reduced_cost_audit.get("min_reduced_cost") is None
            or float(master.reduced_cost_audit["min_reduced_cost"]) >= -1.0e-6
        )
    )


def _previous_baseline_diff(
    previous_baseline: dict | None,
    root_objective: float | None,
    certificate_scope: CertificateScope,
) -> dict:
    previous_baseline = previous_baseline or {}
    previous_root = previous_baseline.get("root_lp_bound") or previous_baseline.get("root_rmp_objective")
    objective_diff = (
        None
        if root_objective is None or previous_root is None
        else round(float(root_objective) - float(previous_root), 9)
    )
    previous_scope = previous_baseline.get("certificate_scope")
    scope_diff = "" if not previous_scope or str(previous_scope) == certificate_scope.value else f"{previous_scope}->{certificate_scope.value}"
    return {
        "previous_baseline_name": previous_baseline.get("b1_mode") or previous_baseline.get("mode") or "",
        "previous_algorithm_status": previous_baseline.get("algorithm_status"),
        "previous_certificate_scope": previous_scope,
        "previous_root_lp_bound": previous_root,
        "previous_final_judge_call_count": previous_baseline.get("final_judge_call_count")
        or previous_baseline.get("pricing_round_count"),
        "objective_diff_vs_previous": objective_diff,
        "certificate_scope_diff_vs_previous": scope_diff,
    }


def _seed_report(
    *,
    mode: str,
    seed_mode: str,
    initial_column_count: int,
    full_universe_column_count: int,
    full_universe_preloaded: bool,
) -> dict:
    return {
        "b2_mode": mode,
        "seed_mode": seed_mode,
        "initial_column_count": int(initial_column_count),
        "full_universe_column_count": int(full_universe_column_count),
        "full_universe_preloaded": bool(full_universe_preloaded),
    }


def _incomplete_payload(
    *,
    data: LunarIceData,
    b0_direct,
    previous_baseline: dict | None,
    completion_policy: dict,
    mode: str,
    note: str,
) -> dict:
    proof_debt = ProofDebtQueue()
    profiling = PruningCounter()
    return _payload(
        data=data,
        b0_direct=b0_direct,
        previous_baseline=previous_baseline,
        proof_debt=proof_debt,
        completion_policy=completion_policy,
        profiling=profiling,
        history=[],
        harvest_totals=_empty_harvest_totals(),
        final_judge_call_count=0,
        duplicate_only_count=0,
        hidden_negative_count=0,
        replacement_only_round_count=0,
        added_to_master_count=0,
        master=None,
        final_judge=None,
        duplicate_audit=None,
        hidden_audit=None,
        seed_catalog=WorkerSeedCatalog(),
        manual_rc_audit=None,
        mode=str(mode),
        seed_report=_seed_report(
            mode=str(mode),
            seed_mode="none_over_task_limit",
            initial_column_count=0,
            full_universe_column_count=0,
            full_universe_preloaded=False,
        ),
        algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
        certificate_scope=CertificateScope.FEASIBLE_INCUMBENT_ONLY,
        pricing_state=PricingState.INCOMPLETE_LIMIT,
        note=note,
    )


def _empty_harvest_totals() -> dict[str, int]:
    return {
        "candidate_negative_count": 0,
        "addable_negative_count": 0,
        "duplicate_in_current_master_count": 0,
        "in_pool_not_master_count": 0,
        "forbidden_signature_count": 0,
        "branch_filtered_count": 0,
        "cut_filtered_count": 0,
        "selected_count": 0,
        "selected_would_enter_master_count": 0,
        "added_to_master_count": 0,
        "harvest_candidate_negative_count": 0,
        "harvest_addable_candidate_count": 0,
        "harvest_selected_count": 0,
        "harvest_duplicate_signature_count": 0,
        "harvest_forbidden_signature_count": 0,
        "harvest_branch_filtered_count": 0,
        "harvest_cut_filtered_count": 0,
        "harvest_duplicate_in_current_master_count": 0,
        "harvest_in_pool_not_master_count": 0,
        "harvest_dominance_filtered_count": 0,
    }


def _accumulate_harvest_totals(totals: dict[str, int], payload: dict) -> None:
    for key in list(totals):
        totals[key] += int(payload.get(key) or 0)


def _empty_profile_totals() -> dict:
    return {
        "rmp_wall_time": 0.0,
        "worker_wall_time": 0.0,
        "final_judge_wall_time": 0.0,
        "time_to_first_negative": None,
        "time_to_first_addable_negative": None,
        "labels_generated": 0,
        "labels_generated_before_first_negative": None,
        "labels_generated_total": 0,
        "labels_extended": 0,
        "sortie_templates": 0,
        "journey_labels": 0,
        "candidate_sequences": 0,
        "path_option_assignments": 0,
        "resource_prune_count": 0,
        "time_window_prune_count": 0,
        "dominance_prune_count": 0,
        "bound_prune_count": 0,
        "bound_check_time": 0.0,
        "dominance_time": 0.0,
        "cache_hit_count": 0,
        "cache_miss_count": 0,
        "max_queue_size": 0,
        "peak_label_count": 0,
        "worker_call_count": 0,
        "worker_found_negative_count": 0,
        "worker_found_addable_negative_count": 0,
        "worker_no_column_uncertified_count": 0,
        "worker_incomplete_count": 0,
        "final_judge_call_count_profiled": 0,
        "final_judge_saved_by_worker_count": 0,
        "exit_reason": "",
        "last_worker_status": "",
        "diagnostic_dual_source": "",
        "diagnostic_rmp_iteration_id": "",
        "diagnostic_dual_fingerprint": "",
    }


def _accumulate_worker_profile(totals: dict, payload: dict) -> None:
    totals["worker_call_count"] += 1
    totals["last_worker_status"] = str(payload.get("worker_status") or "")
    if payload.get("worker_status") == PricingState.FOUND_NEGATIVE.value:
        totals["worker_found_negative_count"] += 1
    elif payload.get("worker_status") == PricingState.LOCAL_NO_COLUMN_UNCERTIFIED.value:
        totals["worker_no_column_uncertified_count"] += 1
    elif payload.get("worker_status") == PricingState.INCOMPLETE_LIMIT.value:
        totals["worker_incomplete_count"] += 1
    if int(payload.get("addable_negative_count") or 0) > 0:
        totals["worker_found_addable_negative_count"] += 1
    _accumulate_pricing_profile(totals, payload)
    totals["worker_wall_time"] += float(payload.get("worker_wall_time") or 0.0)
    totals["exit_reason"] = str(payload.get("exit_reason") or totals.get("exit_reason") or "")
    if payload.get("diagnostic_dual_source"):
        totals["diagnostic_dual_source"] = str(payload.get("diagnostic_dual_source") or "")
        totals["diagnostic_rmp_iteration_id"] = str(payload.get("diagnostic_rmp_iteration_id") or "")
        totals["diagnostic_dual_fingerprint"] = str(payload.get("diagnostic_dual_fingerprint") or "")
    _set_first_time(totals, "time_to_first_negative", payload.get("time_to_first_negative"))
    _set_first_time(totals, "time_to_first_addable_negative", payload.get("time_to_first_addable_negative"))
    _set_first_int(totals, "labels_generated_before_first_negative", payload.get("labels_generated_before_first_negative"))


def _accumulate_pricing_profile(totals: dict, payload: dict) -> None:
    labels = int(payload.get("labels_generated") or payload.get("pareto_label_count") or 0)
    totals["labels_generated"] += labels
    totals["labels_generated_total"] += int(payload.get("labels_generated_total") or labels)
    totals["labels_extended"] += int(payload.get("labels_extended") or payload.get("sortie_attempt_count") or 0)
    totals["sortie_templates"] += int(payload.get("sortie_templates") or payload.get("feasible_sortie_template_count") or 0)
    totals["journey_labels"] += int(payload.get("journey_labels") or payload.get("negative_column_count") or 0)
    totals["candidate_sequences"] += int(payload.get("candidate_sequences") or payload.get("candidate_round_count") or 0)
    totals["path_option_assignments"] += int(payload.get("path_option_assignments") or payload.get("sortie_attempt_count") or 0)
    totals["resource_prune_count"] += int(payload.get("resource_prune_count") or 0)
    totals["time_window_prune_count"] += int(payload.get("time_window_prune_count") or 0)
    totals["dominance_prune_count"] += int(payload.get("dominance_prune_count") or 0)
    completion = payload.get("completion_bound") if isinstance(payload.get("completion_bound"), dict) else {}
    totals["bound_prune_count"] += int(payload.get("bound_prune_count") or completion.get("pruned_label_count") or 0)
    totals["cache_hit_count"] = max(int(totals["cache_hit_count"]), int(payload.get("cache_hit_count") or 0))
    totals["cache_miss_count"] = max(int(totals["cache_miss_count"]), int(payload.get("cache_miss_count") or 0))
    totals["max_queue_size"] = max(int(totals["max_queue_size"]), int(payload.get("max_queue_size") or 0))
    totals["peak_label_count"] = max(int(totals["peak_label_count"]), int(payload.get("labels_generated") or payload.get("pareto_label_count") or 0))


def _set_first_time(totals: dict, key: str, value) -> None:
    if value is None:
        return
    value = float(value)
    old = totals.get(key)
    totals[key] = value if old is None else min(float(old), value)


def _set_first_int(totals: dict, key: str, value) -> None:
    if value is None:
        return
    value = int(value)
    old = totals.get(key)
    totals[key] = value if old is None else min(int(old), value)


def _profile_payload(profile_totals: dict | None, profiling: PruningCounter, final_judge: dict | None) -> dict:
    totals = _empty_profile_totals()
    if profile_totals:
        totals.update(profile_totals)
    final_judge = final_judge or {}
    if not totals["final_judge_wall_time"] and final_judge.get("final_judge_wall_time") is not None:
        totals["final_judge_wall_time"] = float(final_judge.get("final_judge_wall_time") or 0.0)
    pruning = profiling.to_payload()
    labels_generated = int(totals["labels_generated"] or pruning.get("labels_generated") or 0)
    labels_generated_total = int(totals["labels_generated_total"] or labels_generated)
    labels_extended = int(totals["labels_extended"] or pruning.get("labels_extended") or 0)
    bound_prune_count = int(totals["bound_prune_count"] or pruning.get("labels_pruned_by_completion_bound") or 0)
    payload = {
        "rmp_wall_time": round(float(totals["rmp_wall_time"]), 6),
        "worker_wall_time": round(float(totals["worker_wall_time"]), 6),
        "final_judge_wall_time": round(float(totals["final_judge_wall_time"]), 6),
        "time_to_first_negative": totals["time_to_first_negative"],
        "time_to_first_addable_negative": totals["time_to_first_addable_negative"],
        "labels_generated": labels_generated,
        "labels_generated_before_first_negative": totals["labels_generated_before_first_negative"],
        "labels_generated_total": labels_generated_total,
        "labels_extended": labels_extended,
        "sortie_templates": int(totals["sortie_templates"]),
        "journey_labels": int(totals["journey_labels"]),
        "candidate_sequences": int(totals["candidate_sequences"]),
        "path_option_assignments": int(totals["path_option_assignments"]),
        "resource_prune_count": int(totals["resource_prune_count"] or pruning.get("labels_pruned_by_resource") or 0),
        "time_window_prune_count": int(totals["time_window_prune_count"] or pruning.get("labels_pruned_by_time_window") or 0),
        "dominance_prune_count": int(totals["dominance_prune_count"] or pruning.get("labels_pruned_by_dominance") or 0),
        "bound_prune_count": bound_prune_count,
        "bound_check_time": round(float(totals["bound_check_time"] or pruning.get("bound_time") or 0.0), 6),
        "dominance_time": round(float(totals["dominance_time"] or pruning.get("dominance_time") or 0.0), 6),
        "cache_hit_count": int(totals["cache_hit_count"]),
        "cache_miss_count": int(totals["cache_miss_count"]),
        "max_queue_size": int(totals["max_queue_size"]),
        "peak_label_count": int(totals["peak_label_count"]),
        "worker_call_count": int(totals["worker_call_count"]),
        "worker_found_negative_count": int(totals["worker_found_negative_count"]),
        "worker_found_addable_negative_count": int(totals["worker_found_addable_negative_count"]),
        "worker_no_column_uncertified_count": int(totals["worker_no_column_uncertified_count"]),
        "worker_incomplete_count": int(totals["worker_incomplete_count"]),
        "final_judge_saved_by_worker_count": int(totals["final_judge_saved_by_worker_count"]),
        "worker_status": str(totals["last_worker_status"]),
        "diagnostic_dual_source": str(totals["diagnostic_dual_source"]),
        "diagnostic_rmp_iteration_id": str(totals["diagnostic_rmp_iteration_id"]),
        "diagnostic_dual_fingerprint": str(totals["diagnostic_dual_fingerprint"]),
        "exit_reason": str(totals["exit_reason"]),
        "proof_tail_kernel_profile": {
            "enabled": bool(profile_totals),
            "pruning_enabled": False,
            "positive_dual_ordering_profiled": bool(profile_totals),
            "addable_negative_early_stop_enabled": bool(profile_totals),
            "changes_certificate_semantics": False,
        },
        "feasibility_cache": _feasibility_cache_payload(
            {
                "hit_count": int(totals["cache_hit_count"]),
                "miss_count": int(totals["cache_miss_count"]),
            }
        ),
        "exact_first_step_bound_profile": _exact_first_step_bound_profile(
            {"evaluated_label_count": labels_generated, "pruned_label_count": bound_prune_count}
        ),
    }
    return payload


def _feasibility_cache_payload(cache_stats: dict) -> dict:
    return {
        "enabled": True,
        "cached_structures": [
            "sortie_feasibility_templates",
            "task_sequence_feasibility",
            "path_option_signature_feasibility",
            "resource_feasibility_payload",
        ],
        "dual_dependent_reduced_cost_cached": False,
        "no_negative_conclusion_cached": False,
        "cache_hit_count": int(cache_stats.get("hit_count") or 0),
        "cache_miss_count": int(cache_stats.get("miss_count") or 0),
    }


def _exact_first_step_bound_profile(completion_payload: dict) -> dict:
    return {
        "enabled": True,
        "ordering_profile_only": True,
        "pruning_enabled": False,
        "exact_first_step_bound_enabled": True,
        "exact_first_step_bound_pruning_enabled": False,
        "exact_first_step_bound_evaluated_count": int(completion_payload.get("evaluated_label_count") or 0),
        "exact_first_step_bound_tightened_count": 0,
        "exact_first_step_bound_time": 0.0,
        "would_prune_count_if_enabled": int(completion_payload.get("pruned_label_count") or 0),
        "consistency_status": "PROFILE_ONLY_PRUNING_DISABLED",
        "can_certify_no_negative": False,
    }
