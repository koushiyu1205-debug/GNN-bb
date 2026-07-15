"""B2 root pricing-tail optimization layer.

B2 is a candidate layer over the accepted B0/B1 proof core.  It never changes
certificate scope or official-bound semantics; it only changes root pricing-tail
handling and records addability, duplicate-only, hidden-negative, and harvesting
diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import combinations
from math import isfinite
import os
import signal
import threading
from time import perf_counter
from typing import Iterable, Mapping

from lunar_ice_bpc.exact.bpc.certificates.certificate_ledger import CertificateLedger
from lunar_ice_bpc.exact.bpc.certificates.proof_debt_queue import ProofDebtQueue
from lunar_ice_bpc.exact.bpc.core.column_pool import BpcColumn, ColumnPool
from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.bpc.cuts.cut_audit import cut_aware_column_signature_from_journey
from lunar_ice_bpc.exact.bpc.core.master_column_view import MasterColumnView
from lunar_ice_bpc.exact.bpc.master.journey_master import solve_root_journey_master
from lunar_ice_bpc.exact.bpc.pricing.completion_bounds import build_completion_bound_tail_policy
from lunar_ice_bpc.exact.bpc.pricing.backends import (
    BACKEND_MODE_EXACT_PROOF,
    BACKEND_OBJECTIVE_PHASE_ONE,
    BackendPricingRequest,
    BackendRegistry,
)
from lunar_ice_bpc.exact.bpc.pricing.duplicate_only_audit import build_duplicate_only_audit
from lunar_ice_bpc.exact.bpc.pricing.dual_stabilization import (
    build_tail_dual_center,
    build_worker_duals_with_tail_center,
)
from lunar_ice_bpc.exact.bpc.pricing.final_judge import (
    LABELING_FINAL_JUDGE_PASS_HARVEST_THEN_PROOF,
    LABELING_FINAL_JUDGE_PASS_PROOF_ONLY,
    run_true_dual_root_final_judge,
)
from lunar_ice_bpc.exact.bpc.pricing.harvest import harvest_addable_negative_columns
from lunar_ice_bpc.exact.bpc.pricing.hidden_negative_audit import build_hidden_negative_audit
from lunar_ice_bpc.exact.bpc.pricing.labeling_pricer import (
    DEFAULT_EXACT_BACKEND_ID,
    RELAXED_NG_ROUTE_MODE,
    LabelingPricingConfig,
    run_bpc_labeling_pricer,
)
from lunar_ice_bpc.exact.bpc.pricing.resource_label_core import (
    CORE_DIRECT_SELECTED_SET_WORKER,
    ResourceLabelCoreConfig,
    run_resource_label_core,
)
from lunar_ice_bpc.exact.bpc.pricing.profiling import PruningCounter
from lunar_ice_bpc.exact.bpc.pricing.status import AlgorithmStatus, CertificateScope, PricingState
from lunar_ice_bpc.exact.bpc.pricing.worker_seed_catalog import WorkerSeedCatalog
from lunar_ice_bpc.exact.bpc.solver.root_node_solver import (
    build_b1_seed_columns,
    dense_rmp_memory_precheck,
    representative_universe_column_count,
)
from lunar_ice_bpc.exact.core.branching import (
    SAME_JOURNEY,
    BranchContext,
    journey_satisfies_branch_context,
)
from lunar_ice_bpc.exact.core.columns import build_timed_sortie
from lunar_ice_bpc.exact.core.cuts import CutContext
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn, build_journey_column
from lunar_ice_bpc.exact.master.journey_rmp import (
    JourneyDuals,
    manual_journey_reduced_cost,
    solve_phase_one_journey_rmp,
)
from lunar_ice_bpc.exact.pricing.journey_pricing import (
    DirectPricingCache,
    price_direct_journey_columns,
    price_direct_journey_columns_incremental,
)
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
DIRECT_LABEL_WORKER = "direct_label"
RELAXED_LABELING_WORKER = "relaxed_labeling"
NEGATIVE_SEARCH_WORKER_KINDS = (DIRECT_LABEL_WORKER, RELAXED_LABELING_WORKER)
LABELING_SUPPORT_CONTINUATION_SEED_ENV = "LUNAR_ICE_LABELING_SUPPORT_CONTINUATION_SEED"
LABELING_SUPPORT_CONTINUATION_MAX_SEED_SETS_ENV = "LUNAR_ICE_LABELING_SUPPORT_CONTINUATION_MAX_SEED_SETS"
LABELING_SUPPORT_CONTINUATION_MAX_NEIGHBORS_ENV = "LUNAR_ICE_LABELING_SUPPORT_CONTINUATION_MAX_NEIGHBORS"
LABELING_SUPPORT_CONTINUATION_PROTECTED_SEED_COUNT_ENV = (
    "LUNAR_ICE_LABELING_SUPPORT_CONTINUATION_PROTECTED_SEED_COUNT"
)
LABELING_WORKER_MAX_TASK_CAP_ENV = "LUNAR_ICE_LABELING_WORKER_MAX_TASK_CAP"
LABELING_WORKER_NG_SIZES_ENV = "LUNAR_ICE_LABELING_WORKER_NG_SIZES"
LABELING_WORKER_NEGATIVE_BATCH_EARLY_STOP_ENV = (
    "LUNAR_ICE_LABELING_WORKER_NEGATIVE_BATCH_EARLY_STOP"
)
LABELING_WORKER_NEGATIVE_BATCH_TARGET_ENV = (
    "LUNAR_ICE_LABELING_WORKER_NEGATIVE_BATCH_TARGET"
)
LABELING_WORKER_RESOURCE_EXTENSION_SEED_ENV = (
    "LUNAR_ICE_LABELING_WORKER_RESOURCE_EXTENSION_SEED"
)
LABELING_WORKER_HARD_TIME_CAP_SEC_ENV = (
    "LUNAR_ICE_LABELING_WORKER_HARD_TIME_CAP_SEC"
)
LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE_ENV = (
    "LUNAR_ICE_LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE"
)
EXACT_FINAL_JUDGE_FIRST_ENV = "LUNAR_ICE_EXACT_FINAL_JUDGE_FIRST"
LABELING_FINAL_JUDGE_PASS_POLICY_ENV = "LUNAR_ICE_LABELING_FINAL_JUDGE_PASS_POLICY"
LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_CAP_SEC_ENV = (
    "LUNAR_ICE_LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_CAP_SEC"
)
LABELING_FINAL_JUDGE_PASS_POLICY_LEGACY = "harvest_then_proof"
LABELING_FINAL_JUDGE_PASS_POLICY_ADAPTIVE = "adaptive_sparse_harvest_v1"
LABELING_FINAL_JUDGE_PASS_POLICY_BRANCH_ADAPTIVE = "branch_adaptive_sparse_harvest_v1"
LABELING_FINAL_JUDGE_PASS_POLICY_PROOF_ONLY = "proof_only"
LABELING_FINAL_JUDGE_PASS_POLICIES = frozenset(
    {
        LABELING_FINAL_JUDGE_PASS_POLICY_LEGACY,
        LABELING_FINAL_JUDGE_PASS_POLICY_ADAPTIVE,
        LABELING_FINAL_JUDGE_PASS_POLICY_BRANCH_ADAPTIVE,
        LABELING_FINAL_JUDGE_PASS_POLICY_PROOF_ONLY,
    }
)
LARGE_TASK_DIRECT_WORKER_ENV = "LUNAR_ICE_LARGE_TASK_DIRECT_WORKER"
LARGE_TASK_DIRECT_WORKER_MAX_TASKS_ENV = "LUNAR_ICE_LARGE_TASK_DIRECT_WORKER_MAX_TASKS"
LARGE_TASK_DIRECT_WORKER_MAX_CANDIDATE_SETS_ENV = (
    "LUNAR_ICE_LARGE_TASK_DIRECT_WORKER_MAX_CANDIDATE_SETS"
)
LARGE_TASK_DIRECT_WORKER_TIME_CAP_SEC_ENV = "LUNAR_ICE_LARGE_TASK_DIRECT_WORKER_TIME_CAP_SEC"
LARGE_TASK_DIRECT_WORKER_NEIGHBORHOOD_WIDTH_ENV = (
    "LUNAR_ICE_LARGE_TASK_DIRECT_WORKER_NEIGHBORHOOD_WIDTH"
)
CERTIFYING_PRICING_PROOF_KINDS = frozenset(
    {
        "EXHAUSTIVE_NO_NEGATIVE",
        "FRONTIER_BOUND_NO_NEGATIVE",
    }
)


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
    b0_direct=None,
    max_direct_tasks: int = 5,
    max_rounds: int = 8,
    wall_time_limit_sec: float | None = None,
    negative_eps: float = 1.0e-6,
    max_columns_per_round: int = 64,
    worker_payload: dict | None = None,
    mode: str = B2B_MODE,
    seed_mode: str = "b0_incumbent_plus_singletons",
    previous_baseline: dict | None = None,
    tail_dual_stabilization_enabled: bool = False,
    tail_dual_stabilization_alpha: float = 0.7,
    tail_dual_stabilization_window: int = 5,
    worker_pricer_kind: str = DIRECT_LABEL_WORKER,
    labeling_final_judge_enabled: bool | None = None,
    labeling_final_judge_max_exact_tasks: int | None = None,
    labeling_final_judge_exact_harvest_target: int | None = None,
) -> dict:
    """Run a B2 root pricing-tail candidate without pre-running B1.

    ``mode=B2B_seeded_tail_CG`` is the default and starts from the B1B-style
    non-full seed pool.  ``B2A_full_universe_rc_audit_fast_path`` is explicit
    and may certify only when the full fixed pricing universe is proven loaded
    into the current master and a full-universe manual RC audit passes.
    """

    if mode == B2_PRODUCT_MODE:
        if b0_direct is not None:
            return _product_payload_from_direct(data, b0_direct)
        return solve_b2_product_exact_solver(
            data,
            max_direct_tasks=int(max_direct_tasks),
            wall_time_limit_sec=wall_time_limit_sec,
        )
    if mode in {B2C_MODE, B2D_MODE}:
        diagnostic_b0 = b0_direct or solve_direct_journey_baseline(
            data,
            max_exact_tasks=min(int(max_direct_tasks), 10),
            wall_time_limit_sec=wall_time_limit_sec,
        )
        return _solve_limited_pricing_diagnostic(
            data,
            b0_direct=diagnostic_b0,
            mode=str(mode),
            max_candidate_sets=max_columns_per_round,
            negative_eps=negative_eps,
            kernel_profile=(mode == B2D_MODE),
        )

    completion_policy = build_completion_bound_tail_policy(pruning_opt_in=False)
    if len(data.task_ids) > int(max_direct_tasks):
        b0_direct = b0_direct or solve_direct_journey_baseline(
            data,
            max_exact_tasks=int(max_direct_tasks),
            wall_time_limit_sec=wall_time_limit_sec,
        )
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
            wall_time_limit_sec=wall_time_limit_sec,
            negative_eps=negative_eps,
        )
    b0_direct = b0_direct or solve_direct_journey_baseline(
        data,
        max_exact_tasks=int(max_direct_tasks),
        wall_time_limit_sec=wall_time_limit_sec,
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
            wall_time_limit_sec=wall_time_limit_sec,
            mode=str(mode),
            tail_dual_stabilization_enabled=tail_dual_stabilization_enabled,
            tail_dual_stabilization_alpha=tail_dual_stabilization_alpha,
            tail_dual_stabilization_window=tail_dual_stabilization_window,
            worker_pricer_kind=worker_pricer_kind,
            labeling_final_judge_enabled=labeling_final_judge_enabled,
            labeling_final_judge_max_exact_tasks=labeling_final_judge_max_exact_tasks,
            labeling_final_judge_exact_harvest_target=labeling_final_judge_exact_harvest_target,
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
        labeling_final_judge_enabled=labeling_final_judge_enabled,
        labeling_final_judge_max_exact_tasks=labeling_final_judge_max_exact_tasks,
        labeling_final_judge_exact_harvest_target=labeling_final_judge_exact_harvest_target,
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
    return _product_payload_from_direct(data, direct)


def _product_payload_from_direct(data: LunarIceData, direct) -> dict:
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
        "objective_breakdown": getattr(direct, "objective_breakdown", None),
        "reference_solution_upper_bound": getattr(direct, "reference_solution_upper_bound", None),
        "reference_solution_upper_bound_source": getattr(direct, "reference_solution_upper_bound_source", ""),
        "direct_bound_pruning_root_bound": getattr(direct, "direct_bound_pruning_root_bound", None),
        "direct_bound_pruning_active": getattr(direct, "direct_bound_pruning_active", False),
        "journey_label_bound_pruned_count": getattr(direct, "journey_label_bound_pruned_count", 0),
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


def solve_node_pricing_with_b2b_r3(
    data: LunarIceData,
    *,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
    node_id: str = "root",
    initial_columns: Iterable[JourneyColumn] | None = None,
    incumbent_objective: float | None = None,
    max_direct_tasks: int = 5,
    max_rounds: int = 8,
    wall_time_limit_sec: float | None = None,
    negative_eps: float = 1.0e-6,
    max_columns_per_round: int = 64,
    b0_direct=None,
    seed_mode: str = "b0_incumbent_plus_singletons",
    tail_dual_stabilization_enabled: bool = False,
    tail_dual_stabilization_alpha: float = 0.7,
    tail_dual_stabilization_window: int = 5,
    worker_pricer_kind: str = DIRECT_LABEL_WORKER,
    labeling_final_judge_enabled: bool | None = None,
    labeling_final_judge_max_exact_tasks: int | None = None,
    labeling_final_judge_exact_harvest_target: int | None = None,
    return_active_columns_payload: bool = False,
) -> dict:
    """Solve one B3 branch node with the accepted B2B_R3 pricing order."""

    active_context = branch_context or BranchContext()
    active_cut_context = cut_context or CutContext()
    active_node_id = str(node_id)
    started_at = perf_counter()
    completion_policy = build_completion_bound_tail_policy(
        pruning_opt_in=False,
        branch_context_active=not active_context.empty,
        cut_context_active=not active_cut_context.empty,
    )
    proof_debt = ProofDebtQueue()
    profiling = PruningCounter()
    if b0_direct is None and initial_columns is None:
        b0_direct = solve_direct_journey_baseline(
            data,
            max_exact_tasks=int(max_direct_tasks),
            wall_time_limit_sec=wall_time_limit_sec,
        )
    if len(data.task_ids) > int(max_direct_tasks):
        return _node_engine_payload(
            data=data,
            node_id=active_node_id,
            branch_context=active_context,
            cut_context=active_cut_context,
            incumbent_objective=incumbent_objective,
            completion_policy=completion_policy,
            proof_debt=proof_debt,
            profiling=profiling,
            history=[],
            harvest_totals=_empty_harvest_totals(),
            profile_totals=_empty_profile_totals(),
            seed_report=_seed_report(
                mode=B2B_R3_MODE,
                seed_mode="none_over_task_limit",
                initial_column_count=0,
                full_universe_column_count=0,
                full_universe_preloaded=False,
            ),
            loaded_column_count=0,
            seed_branch_filtered_column_count=0,
            master=None,
            final_judge=None,
            final_judge_columns=tuple(),
            final_judge_call_count=0,
            duplicate_only_count=0,
            hidden_negative_count=0,
            replacement_only_round_count=0,
            added_to_master_count=0,
            algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
            certificate_scope=CertificateScope.FEASIBLE_INCUMBENT_ONLY,
            pricing_state=PricingState.INCOMPLETE_LIMIT,
            node_status="NODE_INCOMPLETE",
            note=f"task_count={len(data.task_ids)} exceeds B2B_R3 node max_direct_tasks={max_direct_tasks}; fail closed.",
            active_columns=tuple() if return_active_columns_payload else None,
        )

    if initial_columns is None:
        seed_columns, seed_report = _build_b2b_r2_lightweight_seed_columns(
            data,
            b0_direct=b0_direct,
            seed_mode=seed_mode,
            max_direct_tasks=max_direct_tasks,
            mode=B2B_R3_MODE,
        )
    else:
        seed_columns = tuple(initial_columns)
        seed_report = {
            "b1_mode": "B1B_seeded_root_CG",
            "b2_mode": B2B_R3_MODE,
            "seed_mode": "provided_node_initial_columns",
            "seed_builder": "b3_node_inherited_seed_columns",
            "initial_column_count": len(seed_columns),
            "full_universe_column_count": None,
            "full_universe_preloaded": False,
        }

    branch_seed_columns, branch_seed_report = _build_same_journey_seed_columns(
        data,
        branch_context=active_context,
        max_direct_tasks=max_direct_tasks,
        wall_time_limit_sec=_remaining_wall_time_limit(
            wall_time_limit_sec,
            started_at=started_at,
        ),
    )
    if branch_seed_columns:
        seed_columns = tuple(seed_columns) + tuple(branch_seed_columns)
    seed_report = {
        **seed_report,
        "same_journey_seed": branch_seed_report,
        "same_journey_seed_column_count": len(branch_seed_columns),
    }

    pool = ColumnPool()
    view = MasterColumnView()
    loaded_count, seed_branch_filtered_count = _load_columns_for_node(
        pool,
        view,
        seed_columns,
        node_id=active_node_id,
        branch_context=active_context,
        cut_context=active_cut_context,
    )
    cache = DirectPricingCache()
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
    # Journey columns are globally valid objects; branch contexts only decide
    # whether a column is admitted at a particular node.  Preserve every
    # audited column discovered across rounds so the tree can share them with
    # sibling and descendant nodes instead of rediscovering them.
    all_final_judge_columns: dict[tuple, JourneyColumn] = {}
    last_final_judge_columns: tuple[JourneyColumn, ...] = tuple()
    last_duplicate_audit: dict | None = None
    last_hidden_audit: dict | None = None
    worker_only_success_count = 0
    tail_dual_history: list[JourneyDuals] = []
    exact_final_judge_first = _env_bool(EXACT_FINAL_JUDGE_FIRST_ENV, default=False)
    configured_final_judge_pass_policy = _labeling_final_judge_pass_policy()
    final_judge_pass_policy = _effective_labeling_final_judge_pass_policy(
        configured_final_judge_pass_policy,
        branch_context_active=not active_context.empty,
    )
    next_final_judge_pass_strategy = _initial_labeling_final_judge_pass_strategy(
        final_judge_pass_policy
    )
    final_judge_harvest_time_cap_sec = _adaptive_final_judge_harvest_cap_sec(
        final_judge_pass_policy
    )

    def export_active_columns() -> tuple[JourneyColumn, ...] | None:
        if not return_active_columns_payload:
            return None
        return _master_columns(pool, view, node_id=active_node_id)

    for round_index in range(1, max(1, int(max_rounds)) + 1):
        if _wall_time_limit_exceeded(wall_time_limit_sec, started_at=started_at):
            profile_totals["exit_reason"] = "ROW_TIME_LIMIT_BEFORE_ROUND"
            return _node_engine_payload(
                data=data,
                node_id=active_node_id,
                branch_context=active_context,
                cut_context=active_cut_context,
                incumbent_objective=incumbent_objective,
                completion_policy=completion_policy,
                proof_debt=proof_debt,
                profiling=profiling,
                history=history,
                harvest_totals=harvest_totals,
                profile_totals=profile_totals,
                seed_report=seed_report,
                loaded_column_count=loaded_count,
                seed_branch_filtered_column_count=seed_branch_filtered_count,
                master=last_master,
                final_judge=last_judge_payload,
                final_judge_columns=last_final_judge_columns,
                final_judge_call_count=final_judge_call_count,
                duplicate_only_count=duplicate_only_count,
                hidden_negative_count=hidden_negative_count,
                replacement_only_round_count=replacement_only_round_count,
                added_to_master_count=added_total,
                algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
                certificate_scope=CertificateScope.DIAGNOSTIC_PRICING_FRONTIER,
                pricing_state=PricingState.INCOMPLETE_LIMIT,
                node_status="NODE_INCOMPLETE",
                note=f"{B2B_R3_MODE} node stopped before round {round_index}: wall_time_limit_sec={wall_time_limit_sec} exhausted.",
                active_columns=export_active_columns(),
                hidden_audit=last_hidden_audit,
                seed_catalog=seed_catalog,
            )
        master_columns = _master_columns(pool, view, node_id=active_node_id)
        rmp_start = perf_counter()
        master = solve_root_journey_master(
            data,
            master_columns,
            negative_eps=negative_eps,
            rmp_iteration_id=f"{B2B_R3_MODE}-{active_node_id}-{round_index}",
            branch_context=active_context,
            cut_context=active_cut_context,
        )
        profile_totals["rmp_wall_time"] += perf_counter() - rmp_start
        last_master = master
        if master.rmp.status != "RESTRICTED_RMP_OPTIMAL":
            phase_one = _recover_branch_rmp_with_phase_one(
                data,
                pool=pool,
                view=view,
                node_id=active_node_id,
                branch_context=active_context,
                cut_context=active_cut_context,
                max_rounds=max_rounds,
                max_columns_per_round=max_columns_per_round,
                negative_eps=negative_eps,
                wall_time_limit_sec=_remaining_wall_time_limit(
                    wall_time_limit_sec,
                    started_at=started_at,
                ),
            )
            phase_added = sum(
                int(row.get("added_column_count") or 0)
                for row in phase_one.get("history", [])
            )
            added_total += phase_added
            profile_totals["phase_one_wall_time"] = round(
                sum(
                    float((row.get("telemetry") or {}).get("wall_time_seconds") or 0.0)
                    for row in phase_one.get("history", [])
                ),
                6,
            )
            profile_totals["phase_one_added_column_count"] = phase_added
            history.append(
                {
                    "round": round_index,
                    "node_id": active_node_id,
                    "pricing_state": (
                        PricingState.CERTIFIED_NO_NEGATIVE.value
                        if phase_one.get("status") == "NODE_INFEASIBLE_CERTIFIED"
                        else PricingState.FOUND_NEGATIVE.value
                        if phase_one.get("status") == "RMP_FEASIBILITY_RESTORED"
                        else PricingState.INCOMPLETE_LIMIT.value
                    ),
                    "phase_one": phase_one,
                    "branch_context_active": not active_context.empty,
                    "added_column_count": phase_added,
                }
            )
            if phase_one.get("status") == "RMP_FEASIBILITY_RESTORED":
                profile_totals["exit_reason"] = "PHASE_ONE_RMP_FEASIBILITY_RESTORED"
                continue
            if phase_one.get("status") == "NODE_INFEASIBLE_CERTIFIED":
                profile_totals["exit_reason"] = "PHASE_ONE_NODE_INFEASIBLE_CERTIFIED"
                phase_final_judge = {
                    "status": "PHASE_ONE_NODE_INFEASIBLE_CERTIFIED",
                    "pricing_state": PricingState.CERTIFIED_NO_NEGATIVE.value,
                    "pricing_proof_kind": "EXHAUSTIVE_NO_NEGATIVE",
                    "can_certify_no_negative": True,
                    "uses_true_dual_bpc_certificate": True,
                    "pricing_rc_audit_pass": True,
                    "manual_rc_audit_pass": True,
                    "all_priced_columns_satisfy_branch_context": True,
                    "pricing_complete_for_branch_context": True,
                    "branch_context_active": not active_context.empty,
                    "branch_context": active_context.to_payload(),
                    "phase_one": phase_one,
                    "note": phase_one.get("note"),
                }
                return _node_engine_payload(
                    data=data,
                    node_id=active_node_id,
                    branch_context=active_context,
                    cut_context=active_cut_context,
                    incumbent_objective=incumbent_objective,
                    completion_policy=completion_policy,
                    proof_debt=proof_debt,
                    profiling=profiling,
                    history=history,
                    harvest_totals=harvest_totals,
                    profile_totals=profile_totals,
                    seed_report=seed_report,
                    loaded_column_count=loaded_count,
                    seed_branch_filtered_column_count=seed_branch_filtered_count,
                    master=master,
                    final_judge=phase_final_judge,
                    final_judge_columns=tuple(),
                    final_judge_call_count=final_judge_call_count + 1,
                    duplicate_only_count=duplicate_only_count,
                    hidden_negative_count=hidden_negative_count,
                    replacement_only_round_count=replacement_only_round_count,
                    added_to_master_count=added_total,
                    algorithm_status=AlgorithmStatus.BPC_INFEASIBLE,
                    certificate_scope=CertificateScope.BPC_INFEASIBLE_CERTIFIED,
                    pricing_state=PricingState.CERTIFIED_NO_NEGATIVE,
                    node_status="INFEASIBLE_CERTIFIED",
                    note=str(phase_one.get("note") or "Phase-I certified node infeasibility."),
                    active_columns=export_active_columns(),
                    hidden_audit=last_hidden_audit,
                    seed_catalog=seed_catalog,
                )
            profile_totals["exit_reason"] = "RMP_NOT_OPTIMAL"
            return _node_engine_payload(
                data=data,
                node_id=active_node_id,
                branch_context=active_context,
                cut_context=active_cut_context,
                incumbent_objective=incumbent_objective,
                completion_policy=completion_policy,
                proof_debt=proof_debt,
                profiling=profiling,
                history=history,
                harvest_totals=harvest_totals,
                profile_totals=profile_totals,
                seed_report=seed_report,
                loaded_column_count=loaded_count,
                seed_branch_filtered_column_count=seed_branch_filtered_count,
                master=master,
                final_judge=last_judge_payload,
                final_judge_columns=last_final_judge_columns,
                final_judge_call_count=final_judge_call_count,
                duplicate_only_count=duplicate_only_count,
                hidden_negative_count=hidden_negative_count,
                replacement_only_round_count=replacement_only_round_count,
                added_to_master_count=added_total,
                algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
                certificate_scope=CertificateScope.DIAGNOSTIC_RMP_BOUND,
                pricing_state=PricingState.INCOMPLETE_LIMIT,
                node_status="NODE_RMP_INFEASIBLE_UNCERTIFIED",
                note=(
                    "Node RMP did not solve to optimality and Phase-I did not close the proof: "
                    f"{phase_one.get('status')} - {phase_one.get('note')}"
                ),
                active_columns=export_active_columns(),
                hidden_audit=last_hidden_audit,
                seed_catalog=seed_catalog,
            )

        remaining_for_worker = _remaining_wall_time_limit(wall_time_limit_sec, started_at=started_at)
        if exact_final_judge_first:
            worker = _exact_final_judge_first_skipped_worker_result(
                worker_pricer_kind=worker_pricer_kind,
                remaining_wall_time_sec=remaining_for_worker,
            )
            profile_totals["exit_reason"] = "EXACT_FINAL_JUDGE_FIRST_WORKER_SKIPPED"
        else:
            worker_hard_cap = _worker_hard_time_cap_sec(remaining_for_worker)
            worker_started = perf_counter()
            try:
                with _worker_hard_timeout(worker_hard_cap):
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
                        node_id=active_node_id,
                        branch_context=active_context,
                        tail_dual_history=_tail_dual_history_with_current(
                            tail_dual_history,
                            master.reduced_cost_context,
                            window=tail_dual_stabilization_window,
                        ),
                        tail_dual_stabilization_enabled=tail_dual_stabilization_enabled,
                        tail_dual_stabilization_alpha=tail_dual_stabilization_alpha,
                        tail_dual_stabilization_window=tail_dual_stabilization_window,
                        worker_pricer_kind=worker_pricer_kind,
                        cut_context=active_cut_context,
                        wall_time_limit_sec=remaining_for_worker,
                    )
            except _WorkerHardTimeLimitExceeded:
                worker = _worker_hard_timeout_result(
                    worker_pricer_kind=worker_pricer_kind,
                    elapsed_sec=perf_counter() - worker_started,
                    hard_time_cap_sec=worker_hard_cap,
                    remaining_wall_time_sec=remaining_for_worker,
                )
        tail_dual_history.append(_duals_from_reduced_cost_context(master.reduced_cost_context))
        if not exact_final_judge_first:
            _accumulate_worker_profile(profile_totals, worker.payload)
        if worker.status == PricingState.FOUND_NEGATIVE and worker.selected_columns:
            added = _add_selected_to_pool_and_master(
                pool,
                view,
                worker.selected_columns,
                node_id=active_node_id,
                branch_context=active_context,
                cut_context=active_cut_context,
            )
            harvest_payload = dict(worker.harvest_payload)
            harvest_payload["added_to_master_count"] = int(added)
            _accumulate_harvest_totals(harvest_totals, harvest_payload)
            added_total += added
            if added > 0:
                worker_only_success_count += 1
            defer_final_judge = bool(
                added > 0
                and (
                    int(max_rounds) <= 1
                    or (
                        worker_only_success_count < _b2b_r2_worker_only_round_limit(max_rounds)
                        and round_index < int(max_rounds)
                    )
                )
            )
            if defer_final_judge:
                history.append(
                    {
                        "round": round_index,
                        "node_id": active_node_id,
                        "node_lp_bound": master.rmp.objective_bound,
                        "dual_context": _dual_context_payload(master.reduced_cost_context),
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
                        "branch_context_active": not active_context.empty,
                        "branch_filtered_count": int(harvest_payload.get("branch_filtered_count") or 0),
                        "completion_bound_pruning_scope": "worker_candidate_search_only",
                    }
                )
                profile_totals["final_judge_saved_by_worker_count"] += 1
                profile_totals["exit_reason"] = "WORKER_FOUND_ADDABLE_NEGATIVE"
                continue

        worker_only_success_count = 0
        if not exact_final_judge_first:
            master_columns = _master_columns(pool, view, node_id=active_node_id)
            rmp_start = perf_counter()
            master = solve_root_journey_master(
                data,
                master_columns,
                negative_eps=negative_eps,
                rmp_iteration_id=f"{B2B_R3_MODE}-{active_node_id}-{round_index}-closure",
                branch_context=active_context,
                cut_context=active_cut_context,
            )
            profile_totals["rmp_wall_time"] += perf_counter() - rmp_start
            last_master = master
            if master.rmp.status != "RESTRICTED_RMP_OPTIMAL":
                profile_totals["exit_reason"] = "RMP_NOT_OPTIMAL_BEFORE_FINAL_JUDGE"
                continue

        remaining_for_judge = _remaining_wall_time_limit(wall_time_limit_sec, started_at=started_at)
        if remaining_for_judge is not None and remaining_for_judge <= 0.0:
            profile_totals["exit_reason"] = "ROW_TIME_LIMIT_BEFORE_FINAL_JUDGE"
            return _node_engine_payload(
                data=data,
                node_id=active_node_id,
                branch_context=active_context,
                cut_context=active_cut_context,
                incumbent_objective=incumbent_objective,
                completion_policy=completion_policy,
                proof_debt=proof_debt,
                profiling=profiling,
                history=history,
                harvest_totals=harvest_totals,
                profile_totals=profile_totals,
                seed_report=seed_report,
                loaded_column_count=loaded_count,
                seed_branch_filtered_column_count=seed_branch_filtered_count,
                master=last_master,
                final_judge=last_judge_payload,
                final_judge_columns=last_final_judge_columns,
                final_judge_call_count=final_judge_call_count,
                duplicate_only_count=duplicate_only_count,
                hidden_negative_count=hidden_negative_count,
                replacement_only_round_count=replacement_only_round_count,
                added_to_master_count=added_total,
                algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
                certificate_scope=CertificateScope.DIAGNOSTIC_PRICING_FRONTIER,
                pricing_state=PricingState.INCOMPLETE_LIMIT,
                node_status="NODE_INCOMPLETE",
                note=f"{B2B_R3_MODE} node stopped before final judge: wall_time_limit_sec={wall_time_limit_sec} exhausted.",
                active_columns=export_active_columns(),
                hidden_audit=last_hidden_audit,
                seed_catalog=seed_catalog,
            )
        active_task_sets_for_judge = {frozenset(column.task_set) for column in master_columns}
        effective_exact_harvest_target = _adaptive_labeling_final_judge_exact_harvest_target(
            labeling_final_judge_exact_harvest_target,
            active_task_set_count=len(active_task_sets_for_judge),
        )
        judge_start = perf_counter()
        judge = run_true_dual_root_final_judge(
            data,
            master.reduced_cost_context,
            max_direct_tasks=max_direct_tasks,
            negative_eps=negative_eps,
            wall_time_limit_sec=remaining_for_judge,
            cache=cache,
            branch_context=active_context,
            cut_context=active_cut_context,
            column_pool=pool,
            master_view=view,
            node_id=active_node_id,
            active_task_sets=active_task_sets_for_judge,
            labeling_final_judge_enabled=labeling_final_judge_enabled,
            labeling_final_judge_max_exact_tasks=labeling_final_judge_max_exact_tasks,
            labeling_final_judge_exact_harvest_target=effective_exact_harvest_target,
            labeling_final_judge_pass_strategy=next_final_judge_pass_strategy,
            labeling_final_judge_harvest_time_cap_sec=final_judge_harvest_time_cap_sec,
        )
        judge_wall_time = perf_counter() - judge_start
        profile_totals["final_judge_wall_time"] += judge_wall_time
        profile_totals["final_judge_call_count_profiled"] += 1
        final_judge_call_count += 1
        last_judge_payload = judge.pricing_payload
        current_final_judge_pass_strategy = next_final_judge_pass_strategy
        next_final_judge_pass_strategy = _next_labeling_final_judge_pass_strategy(
            final_judge_pass_policy,
            judge.pricing_payload,
            max_columns_per_round=max_columns_per_round,
            effective_harvest_target=effective_exact_harvest_target,
        )
        for column in judge.all_priced_columns:
            signature = column_signature_from_journey(column)
            current = all_final_judge_columns.get(signature)
            if current is None or column.objective < current.objective - 1.0e-12:
                all_final_judge_columns[signature] = column
        last_final_judge_columns = tuple(all_final_judge_columns.values())
        profiling.merge_completion_payload(judge.pricing_payload)
        _accumulate_pricing_profile(profile_totals, judge.pricing_payload)
        negative_pairs = _manual_negative_pairs(
            judge.all_priced_columns,
            duals=master.rmp.duals,
            negative_eps=negative_eps,
            branch_context=active_context,
            cut_context=active_cut_context,
        )
        hidden_audit = build_hidden_negative_audit(
            worker_payload=worker.payload,
            final_judge_payload=judge.pricing_payload,
            negative_candidates=negative_pairs,
            node_id=active_node_id,
            cg_iter=round_index,
        )
        last_hidden_audit = hidden_audit
        hidden_negative_count += int(hidden_audit.get("hidden_negative_count") or 0)
        seed_catalog.record_hidden_negative_audit(hidden_audit)
        selected, harvest_payload = harvest_addable_negative_columns(
            negative_pairs,
            pool=pool,
            view=view,
            node_id=active_node_id,
            negative_eps=negative_eps,
            max_selected=max_columns_per_round,
            active_task_sets={frozenset(column.task_set) for column in master_columns},
            branch_context=active_context,
            cut_context=active_cut_context,
            profiling=profiling,
            source_phase="b3_node_post_final_judge_addability_harvest",
        )
        added = _add_selected_to_pool_and_master(
            pool,
            view,
            selected,
            node_id=active_node_id,
            branch_context=active_context,
            cut_context=active_cut_context,
        )
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
                node_id=active_node_id,
                negative_eps=negative_eps,
                branch_context=active_context,
                cut_context=active_cut_context,
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
                "node_id": active_node_id,
                "node_lp_bound": master.rmp.objective_bound,
                "dual_context": _dual_context_payload(master.reduced_cost_context),
                "pricing_state": judge.pricing_state.value,
                "worker_status": worker.status.value,
                "worker_exit_reason": worker.payload.get("exit_reason"),
                "worker_wall_time": worker.payload.get("worker_wall_time"),
                "exact_final_judge_first_enabled": bool(exact_final_judge_first),
                **_worker_round_diagnostic_fields(worker.payload),
                "final_judge_called": True,
                "final_judge_status": judge.pricing_payload.get("status"),
                "compact_pricing_phase": judge.pricing_payload.get("compact_pricing_phase"),
                "final_judge_wall_time": round(judge_wall_time, 6),
                "negative_column_count": int(
                    judge.pricing_payload.get("negative_column_count")
                    or len(getattr(judge, "negative_columns", tuple()))
                ),
                "candidate_negative_count": int(harvest_payload["candidate_negative_count"]),
                "addable_negative_count": int(harvest_payload["addable_negative_count"]),
                "selected_count": int(harvest_payload["selected_count"]),
                "added_to_master_count": int(added),
                "added_column_count": int(added),
                "harvest_source_phase": harvest_payload.get("harvest_source_phase"),
                "harvest_selected_count": harvest_payload.get("harvest_selected_count"),
                "harvest_candidate_negative_count": harvest_payload.get("harvest_candidate_negative_count"),
                "harvest_selected_new_task_set_count": harvest_payload.get(
                    "harvest_selected_new_task_set_count"
                ),
                "harvest_selected_replacement_task_set_count": harvest_payload.get(
                    "harvest_selected_replacement_task_set_count"
                ),
                "harvest_rejected_duplicate_count": harvest_payload.get(
                    "harvest_rejected_duplicate_count"
                ),
                "harvest_rejected_not_addable_count": harvest_payload.get(
                    "harvest_rejected_not_addable_count"
                ),
                "harvest_best_true_rc": harvest_payload.get("harvest_best_true_rc"),
                "final_judge_harvest_source_phase": judge.pricing_payload.get("harvest_source_phase"),
                "final_judge_harvest_selected_count": judge.pricing_payload.get("harvest_selected_count"),
                "final_judge_harvest_candidate_negative_count": judge.pricing_payload.get(
                    "harvest_candidate_negative_count"
                ),
                "final_judge_harvest_best_true_rc": judge.pricing_payload.get("harvest_best_true_rc"),
                "exact_negative_harvest_active_task_set_count": judge.pricing_payload.get(
                    "exact_negative_harvest_active_task_set_count"
                ),
                "exact_negative_harvest_non_active_task_set_count": judge.pricing_payload.get(
                    "exact_negative_harvest_non_active_task_set_count"
                ),
                "exact_negative_harvest_active_task_set_reference_count": judge.pricing_payload.get(
                    "exact_negative_harvest_active_task_set_reference_count"
                ),
                "labeling_final_judge_effective_exact_harvest_target": effective_exact_harvest_target,
                "labeling_final_judge_active_task_sets_for_harvest_count": judge.pricing_payload.get(
                    "labeling_final_judge_active_task_sets_for_harvest_count"
                ),
                "labeling_final_judge_two_phase_enabled": judge.pricing_payload.get(
                    "labeling_final_judge_two_phase_enabled"
                ),
                "labeling_final_judge_pass_policy": final_judge_pass_policy,
                "labeling_final_judge_configured_pass_policy": configured_final_judge_pass_policy,
                "labeling_final_judge_pass_strategy": current_final_judge_pass_strategy,
                "labeling_final_judge_next_pass_strategy": next_final_judge_pass_strategy,
                "labeling_final_judge_harvest_time_cap_sec": judge.pricing_payload.get(
                    "labeling_final_judge_harvest_time_cap_sec"
                ),
                "labeling_final_judge_harvest_pass_attempted": judge.pricing_payload.get(
                    "labeling_final_judge_harvest_pass_attempted"
                ),
                "labeling_final_judge_harvest_pass_wall_time": judge.pricing_payload.get(
                    "labeling_final_judge_harvest_pass_wall_time"
                ),
                "labeling_final_judge_harvest_pass_column_count": judge.pricing_payload.get(
                    "labeling_final_judge_harvest_pass_column_count"
                ),
                "labeling_final_judge_proof_pass_attempted": judge.pricing_payload.get(
                    "labeling_final_judge_proof_pass_attempted"
                ),
                "labeling_final_judge_proof_pass_pricing_state": judge.pricing_payload.get(
                    "labeling_final_judge_proof_pass_pricing_state"
                ),
                "labeling_final_judge_proof_pass_pricing_proof_kind": judge.pricing_payload.get(
                    "labeling_final_judge_proof_pass_pricing_proof_kind"
                ),
                "labeling_final_judge_proof_pass_wall_time": judge.pricing_payload.get(
                    "labeling_final_judge_proof_pass_wall_time"
                ),
                "labeling_final_judge_harvest_pass_pricing_proof_kind": judge.pricing_payload.get(
                    "labeling_final_judge_harvest_pass_pricing_proof_kind"
                ),
                "route_template_pre_harvest_enabled": bool(
                    judge.pricing_payload.get("route_template_pre_harvest_enabled")
                ),
                "route_template_pre_harvest_status": judge.pricing_payload.get(
                    "route_template_pre_harvest_status"
                ),
                "route_template_pre_harvest_target": judge.pricing_payload.get(
                    "route_template_pre_harvest_target"
                ),
                "route_template_pre_harvest_seed_strategy": judge.pricing_payload.get(
                    "route_template_pre_harvest_seed_strategy"
                ),
                "route_template_pre_harvest_neighborhood_enabled": judge.pricing_payload.get(
                    "route_template_pre_harvest_neighborhood_enabled"
                ),
                "route_template_pre_harvest_max_neighborhood_seeds": judge.pricing_payload.get(
                    "route_template_pre_harvest_max_neighborhood_seeds"
                ),
                "route_template_pre_harvest_seed_count": judge.pricing_payload.get(
                    "route_template_pre_harvest_seed_count"
                ),
                "route_template_pre_harvest_candidate_round_count": judge.pricing_payload.get(
                    "route_template_pre_harvest_candidate_round_count"
                ),
                "route_template_pre_harvest_selected_count": judge.pricing_payload.get(
                    "route_template_pre_harvest_selected_count"
                ),
                "route_template_pre_harvest_selected_new_task_set_count": judge.pricing_payload.get(
                    "route_template_pre_harvest_selected_new_task_set_count"
                ),
                "route_template_pre_harvest_pricing_wall_time_sec": judge.pricing_payload.get(
                    "route_template_pre_harvest_pricing_wall_time_sec"
                ),
                "route_template_pre_harvest_fallback_enabled": judge.pricing_payload.get(
                    "route_template_pre_harvest_fallback_enabled"
                ),
                "duplicate_only_audit_status": None if duplicate_audit is None else duplicate_audit.get("status"),
                "branch_context_active": not active_context.empty,
                "branch_filtered_count": int(harvest_payload.get("branch_filtered_count") or 0),
                "completion_bound_pruning_enabled": False,
            }
        )
        if judge.pricing_state == PricingState.CERTIFIED_NO_NEGATIVE:
            return _node_engine_payload(
                data=data,
                node_id=active_node_id,
                branch_context=active_context,
                cut_context=active_cut_context,
                incumbent_objective=incumbent_objective,
                completion_policy=completion_policy,
                proof_debt=proof_debt,
                profiling=profiling,
                history=history,
                harvest_totals=harvest_totals,
                profile_totals=profile_totals,
                seed_report=seed_report,
                loaded_column_count=loaded_count,
                seed_branch_filtered_column_count=seed_branch_filtered_count,
                master=master,
                final_judge=judge.pricing_payload,
                final_judge_columns=last_final_judge_columns,
                final_judge_call_count=final_judge_call_count,
                duplicate_only_count=duplicate_only_count,
                hidden_negative_count=hidden_negative_count,
                replacement_only_round_count=replacement_only_round_count,
                added_to_master_count=added_total,
                algorithm_status=AlgorithmStatus.BPC_GAP_AVAILABLE,
                certificate_scope=CertificateScope.BPC_NODE_LP_CERTIFIED,
                pricing_state=PricingState.CERTIFIED_NO_NEGATIVE,
                node_status="NODE_LP_CERTIFIED",
                note="B2B_R3 node LP certificate came only from the branch-aware true-dual final judge.",
                active_columns=export_active_columns(),
                hidden_audit=last_hidden_audit,
                seed_catalog=seed_catalog,
            )
        if duplicate_only_round:
            profile_totals["exit_reason"] = "DUPLICATE_ONLY"
            return _node_engine_payload(
                data=data,
                node_id=active_node_id,
                branch_context=active_context,
                cut_context=active_cut_context,
                incumbent_objective=incumbent_objective,
                completion_policy=completion_policy,
                proof_debt=proof_debt,
                profiling=profiling,
                history=history,
                harvest_totals=harvest_totals,
                profile_totals=profile_totals,
                seed_report=seed_report,
                loaded_column_count=loaded_count,
                seed_branch_filtered_column_count=seed_branch_filtered_count,
                master=master,
                final_judge=judge.pricing_payload,
                final_judge_columns=last_final_judge_columns,
                final_judge_call_count=final_judge_call_count,
                duplicate_only_count=duplicate_only_count,
                hidden_negative_count=hidden_negative_count,
                replacement_only_round_count=replacement_only_round_count,
                added_to_master_count=added_total,
                algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
                certificate_scope=CertificateScope.DIAGNOSTIC_PRICING_FRONTIER,
                pricing_state=PricingState.DUPLICATE_ONLY,
                node_status="DUPLICATE_ONLY",
                note="DUPLICATE_ONLY: branch-aware true-RC negative candidates were found but none entered the node master.",
                active_columns=export_active_columns(),
                hidden_audit=last_hidden_audit,
                seed_catalog=seed_catalog,
            )
        if judge.pricing_state != PricingState.FOUND_NEGATIVE and added == 0:
            return _node_engine_payload(
                data=data,
                node_id=active_node_id,
                branch_context=active_context,
                cut_context=active_cut_context,
                incumbent_objective=incumbent_objective,
                completion_policy=completion_policy,
                proof_debt=proof_debt,
                profiling=profiling,
                history=history,
                harvest_totals=harvest_totals,
                profile_totals=profile_totals,
                seed_report=seed_report,
                loaded_column_count=loaded_count,
                seed_branch_filtered_column_count=seed_branch_filtered_count,
                master=master,
                final_judge=judge.pricing_payload,
                final_judge_columns=last_final_judge_columns,
                final_judge_call_count=final_judge_call_count,
                duplicate_only_count=duplicate_only_count,
                hidden_negative_count=hidden_negative_count,
                replacement_only_round_count=replacement_only_round_count,
                added_to_master_count=added_total,
                algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
                certificate_scope=CertificateScope.DIAGNOSTIC_PRICING_FRONTIER,
                pricing_state=judge.pricing_state,
                node_status="NODE_INCOMPLETE",
                note=(
                    "B2B_R3 final judge did not certify no-negative and did not return an "
                    "addable negative column; stopping this node fail-closed."
                ),
                active_columns=export_active_columns(),
                hidden_audit=last_hidden_audit,
                seed_catalog=seed_catalog,
            )

    profile_totals["exit_reason"] = str(profile_totals.get("exit_reason") or "WORKER_INCOMPLETE_LIMIT")
    return _node_engine_payload(
        data=data,
        node_id=active_node_id,
        branch_context=active_context,
        cut_context=active_cut_context,
        incumbent_objective=incumbent_objective,
        completion_policy=completion_policy,
        proof_debt=proof_debt,
        profiling=profiling,
        history=history,
        harvest_totals=harvest_totals,
        profile_totals=profile_totals,
        seed_report=seed_report,
        loaded_column_count=loaded_count,
        seed_branch_filtered_column_count=seed_branch_filtered_count,
        master=last_master,
        final_judge=last_judge_payload,
        final_judge_columns=last_final_judge_columns,
        final_judge_call_count=final_judge_call_count,
        duplicate_only_count=duplicate_only_count,
        hidden_negative_count=hidden_negative_count,
        replacement_only_round_count=replacement_only_round_count,
        added_to_master_count=added_total,
        algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
        certificate_scope=CertificateScope.DIAGNOSTIC_PRICING_FRONTIER,
        pricing_state=PricingState.INCOMPLETE_LIMIT,
        node_status="NODE_INCOMPLETE",
        note=f"Stopped after max_rounds={max_rounds}; B2B_R3 node proof is incomplete.",
        active_columns=export_active_columns(),
        hidden_audit=last_hidden_audit,
        seed_catalog=seed_catalog,
    )


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
        "objective_breakdown": getattr(b0_direct, "objective_breakdown", None),
        "reference_solution_upper_bound": getattr(b0_direct, "reference_solution_upper_bound", None),
        "reference_solution_upper_bound_source": getattr(b0_direct, "reference_solution_upper_bound_source", ""),
        "direct_bound_pruning_root_bound": getattr(b0_direct, "direct_bound_pruning_root_bound", None),
        "direct_bound_pruning_active": getattr(b0_direct, "direct_bound_pruning_active", False),
        "journey_label_bound_pruned_count": getattr(b0_direct, "journey_label_bound_pruned_count", 0),
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
    wall_time_limit_sec: float | None,
    negative_eps: float,
) -> dict:
    estimated_columns = representative_universe_column_count(len(data.task_ids))
    precheck = dense_rmp_memory_precheck(
        data,
        active_column_count=estimated_columns,
        stage="b2a_full_universe_active_rmp",
    )
    if precheck["rmp_memory_precheck_failed"]:
        proof_debt = ProofDebtQueue()
        return _payload(
            data=data,
            b0_direct=b0_direct,
            previous_baseline=previous_baseline,
            proof_debt=proof_debt,
            completion_policy=completion_policy,
            profiling=PruningCounter(),
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
            mode=B2A_MODE,
            seed_report=_seed_report(
                mode=B2A_MODE,
                seed_mode="full_universe",
                initial_column_count=0,
                full_universe_column_count=estimated_columns,
                full_universe_preloaded=False,
            ),
            algorithm_status=AlgorithmStatus.BPC_INCOMPLETE_PRICING,
            certificate_scope=CertificateScope.FEASIBLE_INCUMBENT_ONLY,
            pricing_state=PricingState.INCOMPLETE_LIMIT,
            note=str(precheck["rmp_memory_precheck_reason"]),
            extra=precheck,
        )
    b0_direct = b0_direct or solve_direct_journey_baseline(
        data,
        max_exact_tasks=int(max_direct_tasks),
        wall_time_limit_sec=wall_time_limit_sec,
    )
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
            "dual_context": _dual_context_payload(master.reduced_cost_context),
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
        "pricing_proof_kind": (
            "EXHAUSTIVE_NO_NEGATIVE" if certified else "EXHAUSTIVE_INCOMPLETE"
        ),
        "underlying_pricing_proof_kind": (
            "EXHAUSTIVE_NO_NEGATIVE" if certified else "EXHAUSTIVE_INCOMPLETE"
        ),
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
    labeling_final_judge_enabled: bool | None = None,
    labeling_final_judge_max_exact_tasks: int | None = None,
    labeling_final_judge_exact_harvest_target: int | None = None,
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
    configured_final_judge_pass_policy = _labeling_final_judge_pass_policy()
    final_judge_pass_policy = _effective_labeling_final_judge_pass_policy(
        configured_final_judge_pass_policy,
        branch_context_active=False,
    )
    next_final_judge_pass_strategy = _initial_labeling_final_judge_pass_strategy(
        final_judge_pass_policy
    )
    final_judge_harvest_time_cap_sec = _adaptive_final_judge_harvest_cap_sec(
        final_judge_pass_policy
    )

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

        active_task_sets_for_judge = {frozenset(column.task_set) for column in master_columns}
        effective_exact_harvest_target = _adaptive_labeling_final_judge_exact_harvest_target(
            labeling_final_judge_exact_harvest_target,
            active_task_set_count=len(active_task_sets_for_judge),
        )
        judge = run_true_dual_root_final_judge(
            data,
            master.reduced_cost_context,
            max_direct_tasks=max_direct_tasks,
            negative_eps=negative_eps,
            cache=cache,
            column_pool=pool,
            master_view=view,
            node_id="root",
            active_task_sets=active_task_sets_for_judge,
            labeling_final_judge_enabled=labeling_final_judge_enabled,
            labeling_final_judge_max_exact_tasks=labeling_final_judge_max_exact_tasks,
            labeling_final_judge_exact_harvest_target=effective_exact_harvest_target,
            labeling_final_judge_pass_strategy=next_final_judge_pass_strategy,
            labeling_final_judge_harvest_time_cap_sec=final_judge_harvest_time_cap_sec,
        )
        final_judge_call_count += 1
        last_judge_payload = judge.pricing_payload
        current_final_judge_pass_strategy = next_final_judge_pass_strategy
        next_final_judge_pass_strategy = _next_labeling_final_judge_pass_strategy(
            final_judge_pass_policy,
            judge.pricing_payload,
            max_columns_per_round=max_columns_per_round,
            effective_harvest_target=effective_exact_harvest_target,
        )
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
            source_phase="b2_seeded_tail_post_final_judge_addability_harvest",
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
    wall_time_limit_sec: float | None = None,
    mode: str = B2B_R2_MODE,
    tail_dual_stabilization_enabled: bool = False,
    tail_dual_stabilization_alpha: float = 0.7,
    tail_dual_stabilization_window: int = 5,
    worker_pricer_kind: str = DIRECT_LABEL_WORKER,
    labeling_final_judge_enabled: bool | None = None,
    labeling_final_judge_max_exact_tasks: int | None = None,
    labeling_final_judge_exact_harvest_target: int | None = None,
) -> dict:
    started_at = perf_counter()
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
    tail_dual_history: list[JourneyDuals] = []
    exact_final_judge_first = _env_bool(EXACT_FINAL_JUDGE_FIRST_ENV, default=False)
    configured_final_judge_pass_policy = _labeling_final_judge_pass_policy()
    final_judge_pass_policy = _effective_labeling_final_judge_pass_policy(
        configured_final_judge_pass_policy,
        branch_context_active=False,
    )
    next_final_judge_pass_strategy = _initial_labeling_final_judge_pass_strategy(
        final_judge_pass_policy
    )
    final_judge_harvest_time_cap_sec = _adaptive_final_judge_harvest_cap_sec(
        final_judge_pass_policy
    )

    for round_index in range(1, max(1, int(max_rounds)) + 1):
        if _wall_time_limit_exceeded(wall_time_limit_sec, started_at=started_at):
            profile_totals["exit_reason"] = "ROW_TIME_LIMIT_BEFORE_ROUND"
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
                note=f"{active_mode} stopped before round {round_index}: wall_time_limit_sec={wall_time_limit_sec} exhausted.",
                profile_totals=profile_totals,
            )
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

        remaining_for_worker = _remaining_wall_time_limit(wall_time_limit_sec, started_at=started_at)
        if exact_final_judge_first:
            worker = _exact_final_judge_first_skipped_worker_result(
                worker_pricer_kind=worker_pricer_kind,
                remaining_wall_time_sec=remaining_for_worker,
            )
            profile_totals["exit_reason"] = "EXACT_FINAL_JUDGE_FIRST_WORKER_SKIPPED"
        else:
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
                tail_dual_history=_tail_dual_history_with_current(
                    tail_dual_history,
                    master.reduced_cost_context,
                    window=tail_dual_stabilization_window,
                ),
                tail_dual_stabilization_enabled=tail_dual_stabilization_enabled,
                tail_dual_stabilization_alpha=tail_dual_stabilization_alpha,
                tail_dual_stabilization_window=tail_dual_stabilization_window,
                worker_pricer_kind=worker_pricer_kind,
                wall_time_limit_sec=remaining_for_worker,
            )
        tail_dual_history.append(_duals_from_reduced_cost_context(master.reduced_cost_context))
        if not exact_final_judge_first:
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
                            "dual_context": _dual_context_payload(master.reduced_cost_context),
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
                            "completion_bound_pruning_scope": "worker_candidate_search_only",
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
        remaining_for_judge = _remaining_wall_time_limit(wall_time_limit_sec, started_at=started_at)
        if remaining_for_judge is not None and remaining_for_judge <= 0.0:
            profile_totals["exit_reason"] = "ROW_TIME_LIMIT_BEFORE_FINAL_JUDGE"
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
                note=f"{active_mode} stopped before final judge: wall_time_limit_sec={wall_time_limit_sec} exhausted.",
                profile_totals=profile_totals,
            )
        active_task_sets_for_judge = {frozenset(column.task_set) for column in master_columns}
        effective_exact_harvest_target = _adaptive_labeling_final_judge_exact_harvest_target(
            labeling_final_judge_exact_harvest_target,
            active_task_set_count=len(active_task_sets_for_judge),
        )
        judge_start = perf_counter()
        judge = run_true_dual_root_final_judge(
            data,
            master.reduced_cost_context,
            max_direct_tasks=max_direct_tasks,
            negative_eps=negative_eps,
            wall_time_limit_sec=remaining_for_judge,
            cache=cache,
            column_pool=pool,
            master_view=view,
            node_id="root",
            active_task_sets=active_task_sets_for_judge,
            labeling_final_judge_enabled=labeling_final_judge_enabled,
            labeling_final_judge_max_exact_tasks=labeling_final_judge_max_exact_tasks,
            labeling_final_judge_exact_harvest_target=effective_exact_harvest_target,
            labeling_final_judge_pass_strategy=next_final_judge_pass_strategy,
            labeling_final_judge_harvest_time_cap_sec=final_judge_harvest_time_cap_sec,
        )
        judge_wall_time = perf_counter() - judge_start
        profile_totals["final_judge_wall_time"] += judge_wall_time
        profile_totals["final_judge_call_count_profiled"] += 1
        final_judge_call_count += 1
        last_judge_payload = judge.pricing_payload
        current_final_judge_pass_strategy = next_final_judge_pass_strategy
        next_final_judge_pass_strategy = _next_labeling_final_judge_pass_strategy(
            final_judge_pass_policy,
            judge.pricing_payload,
            max_columns_per_round=max_columns_per_round,
            effective_harvest_target=effective_exact_harvest_target,
        )
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
            source_phase="b2b_r2_post_final_judge_addability_harvest",
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
                "dual_context": _dual_context_payload(master.reduced_cost_context),
                "pricing_state": judge.pricing_state.value,
                "worker_status": worker.status.value,
                "worker_exit_reason": worker.payload.get("exit_reason"),
                "worker_wall_time": worker.payload.get("worker_wall_time"),
                "exact_final_judge_first_enabled": bool(exact_final_judge_first),
                **_worker_round_diagnostic_fields(worker.payload),
                "final_judge_called": True,
                "final_judge_status": judge.pricing_payload.get("status"),
                "compact_pricing_phase": judge.pricing_payload.get("compact_pricing_phase"),
                "final_judge_wall_time": round(judge_wall_time, 6),
                "negative_column_count": int(
                    judge.pricing_payload.get("negative_column_count")
                    or len(getattr(judge, "negative_columns", tuple()))
                ),
                "candidate_negative_count": int(harvest_payload["candidate_negative_count"]),
                "addable_negative_count": int(harvest_payload["addable_negative_count"]),
                "selected_count": int(harvest_payload["selected_count"]),
                "added_to_master_count": int(added),
                "added_column_count": int(added),
                "harvest_source_phase": harvest_payload.get("harvest_source_phase"),
                "harvest_selected_count": harvest_payload.get("harvest_selected_count"),
                "harvest_candidate_negative_count": harvest_payload.get("harvest_candidate_negative_count"),
                "harvest_selected_new_task_set_count": harvest_payload.get(
                    "harvest_selected_new_task_set_count"
                ),
                "harvest_selected_replacement_task_set_count": harvest_payload.get(
                    "harvest_selected_replacement_task_set_count"
                ),
                "harvest_rejected_duplicate_count": harvest_payload.get(
                    "harvest_rejected_duplicate_count"
                ),
                "harvest_rejected_not_addable_count": harvest_payload.get(
                    "harvest_rejected_not_addable_count"
                ),
                "harvest_best_true_rc": harvest_payload.get("harvest_best_true_rc"),
                "final_judge_harvest_source_phase": judge.pricing_payload.get("harvest_source_phase"),
                "final_judge_harvest_selected_count": judge.pricing_payload.get("harvest_selected_count"),
                "final_judge_harvest_candidate_negative_count": judge.pricing_payload.get(
                    "harvest_candidate_negative_count"
                ),
                "final_judge_harvest_best_true_rc": judge.pricing_payload.get("harvest_best_true_rc"),
                "exact_negative_harvest_active_task_set_count": judge.pricing_payload.get(
                    "exact_negative_harvest_active_task_set_count"
                ),
                "exact_negative_harvest_non_active_task_set_count": judge.pricing_payload.get(
                    "exact_negative_harvest_non_active_task_set_count"
                ),
                "exact_negative_harvest_active_task_set_reference_count": judge.pricing_payload.get(
                    "exact_negative_harvest_active_task_set_reference_count"
                ),
                "labeling_final_judge_effective_exact_harvest_target": effective_exact_harvest_target,
                "labeling_final_judge_active_task_sets_for_harvest_count": judge.pricing_payload.get(
                    "labeling_final_judge_active_task_sets_for_harvest_count"
                ),
                "labeling_final_judge_two_phase_enabled": judge.pricing_payload.get(
                    "labeling_final_judge_two_phase_enabled"
                ),
                "labeling_final_judge_pass_policy": final_judge_pass_policy,
                "labeling_final_judge_configured_pass_policy": configured_final_judge_pass_policy,
                "labeling_final_judge_pass_strategy": current_final_judge_pass_strategy,
                "labeling_final_judge_next_pass_strategy": next_final_judge_pass_strategy,
                "labeling_final_judge_harvest_time_cap_sec": judge.pricing_payload.get(
                    "labeling_final_judge_harvest_time_cap_sec"
                ),
                "labeling_final_judge_harvest_pass_attempted": judge.pricing_payload.get(
                    "labeling_final_judge_harvest_pass_attempted"
                ),
                "labeling_final_judge_harvest_pass_wall_time": judge.pricing_payload.get(
                    "labeling_final_judge_harvest_pass_wall_time"
                ),
                "labeling_final_judge_harvest_pass_column_count": judge.pricing_payload.get(
                    "labeling_final_judge_harvest_pass_column_count"
                ),
                "labeling_final_judge_proof_pass_attempted": judge.pricing_payload.get(
                    "labeling_final_judge_proof_pass_attempted"
                ),
                "labeling_final_judge_proof_pass_pricing_state": judge.pricing_payload.get(
                    "labeling_final_judge_proof_pass_pricing_state"
                ),
                "labeling_final_judge_proof_pass_pricing_proof_kind": judge.pricing_payload.get(
                    "labeling_final_judge_proof_pass_pricing_proof_kind"
                ),
                "labeling_final_judge_proof_pass_wall_time": judge.pricing_payload.get(
                    "labeling_final_judge_proof_pass_wall_time"
                ),
                "labeling_final_judge_harvest_pass_pricing_proof_kind": judge.pricing_payload.get(
                    "labeling_final_judge_harvest_pass_pricing_proof_kind"
                ),
                "route_template_pre_harvest_enabled": bool(
                    judge.pricing_payload.get("route_template_pre_harvest_enabled")
                ),
                "route_template_pre_harvest_status": judge.pricing_payload.get(
                    "route_template_pre_harvest_status"
                ),
                "route_template_pre_harvest_target": judge.pricing_payload.get(
                    "route_template_pre_harvest_target"
                ),
                "route_template_pre_harvest_seed_strategy": judge.pricing_payload.get(
                    "route_template_pre_harvest_seed_strategy"
                ),
                "route_template_pre_harvest_neighborhood_enabled": judge.pricing_payload.get(
                    "route_template_pre_harvest_neighborhood_enabled"
                ),
                "route_template_pre_harvest_max_neighborhood_seeds": judge.pricing_payload.get(
                    "route_template_pre_harvest_max_neighborhood_seeds"
                ),
                "route_template_pre_harvest_seed_count": judge.pricing_payload.get(
                    "route_template_pre_harvest_seed_count"
                ),
                "route_template_pre_harvest_candidate_round_count": judge.pricing_payload.get(
                    "route_template_pre_harvest_candidate_round_count"
                ),
                "route_template_pre_harvest_selected_count": judge.pricing_payload.get(
                    "route_template_pre_harvest_selected_count"
                ),
                "route_template_pre_harvest_selected_new_task_set_count": judge.pricing_payload.get(
                    "route_template_pre_harvest_selected_new_task_set_count"
                ),
                "route_template_pre_harvest_pricing_wall_time_sec": judge.pricing_payload.get(
                    "route_template_pre_harvest_pricing_wall_time_sec"
                ),
                "route_template_pre_harvest_fallback_enabled": judge.pricing_payload.get(
                    "route_template_pre_harvest_fallback_enabled"
                ),
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
        if judge.pricing_state != PricingState.FOUND_NEGATIVE and added == 0:
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
                pricing_state=judge.pricing_state,
                note=(
                    f"{active_mode} final judge did not certify no-negative and did not "
                    "return an addable negative column; stopping fail-closed."
                ),
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
    candidate_rc_recomputed = bool(payload.get("candidate_search_rc_recomputed_under_true_dual"))
    branch_audit_pass = bool(payload.get("branch_context_audit_pass"))
    worker_candidate_audit_pass = bool(
        payload.get("worker_true_dual_candidate_audit_pass")
        if payload.get("worker_true_dual_candidate_audit_pass") is not None
        else candidate_rc_recomputed and branch_audit_pass
    )
    return {
        "worker_pricer_kind": payload.get("worker_pricer_kind") or DIRECT_LABEL_WORKER,
        "labeling_worker_enabled": bool(payload.get("labeling_worker_enabled")),
        "labeling_algorithm": payload.get("labeling_algorithm") or "",
        "resource_label_algorithm": payload.get("resource_label_algorithm") or "",
        "resource_label_core_mode": payload.get("resource_label_core_mode") or "",
        "pricing_engine_role": payload.get("pricing_engine_role") or "",
        "candidate_search_only": bool(payload.get("candidate_search_only")),
        "relaxed_candidate_search_can_certify_no_negative": bool(
            payload.get("relaxed_candidate_search_can_certify_no_negative")
        ),
        "no_column_certificate_allowed": bool(payload.get("no_column_certificate_allowed")),
        "ng_route_relaxation_kind": payload.get("ng_route_relaxation_kind") or "",
        "ng_route_relaxation_is_certificate_relaxation": bool(
            payload.get("ng_route_relaxation_is_certificate_relaxation")
        ),
        "relaxed_route_elementarity_proof_supported": bool(
            payload.get("relaxed_route_elementarity_proof_supported")
        ),
        "dssr_refinement_status": payload.get("dssr_refinement_status") or "",
        "exact_final_proof_required_after_worker": bool(
            payload.get("exact_final_proof_required_after_worker")
        ),
        "exact_final_proof_expected_mode": payload.get("exact_final_proof_expected_mode") or "",
        "resource_dimensions": payload.get("resource_dimensions") or [],
        "dominance_policy": payload.get("dominance_policy") or "",
        "elementarity_policy": payload.get("elementarity_policy") or "",
        "worker_underlying_incomplete": bool(payload.get("worker_underlying_incomplete")),
        "worker_underlying_pricing_state": str(payload.get("worker_underlying_pricing_state") or ""),
        "worker_underlying_status": str(payload.get("worker_underlying_status") or ""),
        "labeling_seed_task_set_count": int(payload.get("labeling_seed_task_set_count") or 0),
        "ng_seed_task_set_count": int(payload.get("ng_seed_task_set_count") or 0),
        "resource_extension_seed_enabled": bool(payload.get("resource_extension_seed_enabled")),
        "resource_extension_seed_task_set_count": int(
            payload.get("resource_extension_seed_task_set_count") or 0
        ),
        "active_resource_extension_seed_task_set_count": int(
            payload.get("active_resource_extension_seed_task_set_count") or 0
        ),
        "resource_extension_seed_task_set_count_by_size": payload.get(
            "resource_extension_seed_task_set_count_by_size"
        )
        or {},
        "resource_extension_label_column_worker_enabled": bool(
            payload.get("resource_extension_label_column_worker_enabled")
        ),
        "resource_extension_label_column_count": int(
            payload.get("resource_extension_label_column_count") or 0
        ),
        "resource_extension_label_column_task_set_count": int(
            payload.get("resource_extension_label_column_task_set_count") or 0
        ),
        "resource_extension_label_column_task_sets": payload.get(
            "resource_extension_label_column_task_sets"
        )
        or [],
        "resource_extension_label_column_policy": payload.get(
            "resource_extension_label_column_policy"
        )
        or "",
        "resource_extension_label_columns_can_certify_no_negative": bool(
            payload.get("resource_extension_label_columns_can_certify_no_negative")
        ),
        "resource_extension_label_stats": payload.get("resource_extension_label_stats") or {},
        "resource_extension_label_attempt_count": int(
            payload.get("resource_extension_label_attempt_count") or 0
        ),
        "resource_extension_label_dominance_rejected_count": int(
            payload.get("resource_extension_label_dominance_rejected_count") or 0
        ),
        "resource_extension_label_capacity_truncated_count": int(
            payload.get("resource_extension_label_capacity_truncated_count") or 0
        ),
        "resource_extension_label_path_variant_candidate_count": int(
            payload.get("resource_extension_label_path_variant_candidate_count") or 0
        ),
        "resource_extension_label_path_variant_duplicate_count": int(
            payload.get("resource_extension_label_path_variant_duplicate_count") or 0
        ),
        "resource_extension_label_path_variant_feasible_count": int(
            payload.get("resource_extension_label_path_variant_feasible_count") or 0
        ),
        "resource_extension_label_path_variant_infeasible_count": int(
            payload.get("resource_extension_label_path_variant_infeasible_count") or 0
        ),
        "resource_extension_proxy_profiles": payload.get("resource_extension_proxy_profiles") or [],
        "resource_extension_proxy_profile_count": int(payload.get("resource_extension_proxy_profile_count") or 0),
        "active_seed_task_set_source_counts": payload.get("active_seed_task_set_source_counts") or {},
        "active_seed_task_set_source_task_count_counts": payload.get(
            "active_seed_task_set_source_task_count_counts"
        )
        or {},
        "active_seed_task_set_sources": payload.get("active_seed_task_set_sources") or [],
        "active_seed_selection_policy": payload.get("active_seed_selection_policy") or "",
        "protected_refinement_seed_task_set_count": int(
            payload.get("protected_refinement_seed_task_set_count") or 0
        ),
        "active_protected_refinement_seed_task_set_count": int(
            payload.get("active_protected_refinement_seed_task_set_count") or 0
        ),
        "protected_refinement_seed_task_set_count_by_size": payload.get(
            "protected_refinement_seed_task_set_count_by_size"
        )
        or {},
        "protected_refinement_seed_budget_truncated_count": int(
            payload.get("protected_refinement_seed_budget_truncated_count") or 0
        ),
        "protected_support_continuation_seed_budget": int(
            payload.get("protected_support_continuation_seed_budget") or 0
        ),
        "protected_support_continuation_seed_task_set_count": int(
            payload.get("protected_support_continuation_seed_task_set_count") or 0
        ),
        "active_protected_support_continuation_seed_task_set_count": int(
            payload.get("active_protected_support_continuation_seed_task_set_count") or 0
        ),
        "protected_support_continuation_seed_task_set_count_by_size": payload.get(
            "protected_support_continuation_seed_task_set_count_by_size"
        )
        or {},
        "protected_support_continuation_seed_budget_truncated_count": int(
            payload.get("protected_support_continuation_seed_budget_truncated_count") or 0
        ),
        "active_seed_task_set_count_by_size": payload.get("active_seed_task_set_count_by_size") or {},
        "branch_seed_filter_enabled": bool(payload.get("branch_seed_filter_enabled")),
        "branch_seed_filtered_input_count": int(payload.get("branch_seed_filtered_input_count") or 0),
        "branch_seed_filtered_ng_count": int(payload.get("branch_seed_filtered_ng_count") or 0),
        "branch_seed_filtered_resource_extension_count": int(
            payload.get("branch_seed_filtered_resource_extension_count") or 0
        ),
        "priced_candidate_task_set_source_counts": payload.get(
            "priced_candidate_task_set_source_counts"
        )
        or {},
        "priced_candidate_task_set_source_task_count_counts": payload.get(
            "priced_candidate_task_set_source_task_count_counts"
        )
        or {},
        "priced_candidate_task_set_sources": payload.get("priced_candidate_task_set_sources") or [],
        "direct_candidate_task_set_count": int(payload.get("direct_candidate_task_set_count") or 0),
        "candidate_seed_source_precedence": payload.get("candidate_seed_source_precedence") or [],
        "input_seed_task_set_count": int(payload.get("input_seed_task_set_count") or 0),
        "merged_seed_task_set_count": int(payload.get("merged_seed_task_set_count") or 0),
        "active_seed_task_set_count": int(payload.get("active_seed_task_set_count") or 0),
        "active_ng_seed_task_set_count": int(payload.get("active_ng_seed_task_set_count") or 0),
        "active_input_seed_task_set_count": int(payload.get("active_input_seed_task_set_count") or 0),
        "ng_neighborhood_size": int(payload.get("ng_neighborhood_size") or 0),
        "ng_neighborhood_sizes": payload.get("ng_neighborhood_sizes") or [],
        "ng_neighborhood_stage_count": int(payload.get("ng_neighborhood_stage_count") or 0),
        "ng_seed_task_set_count_by_size": payload.get("ng_seed_task_set_count_by_size") or {},
        "labeling_no_column_uncertified": bool(payload.get("labeling_no_column_uncertified")),
        "worker_task_cap": payload.get("worker_task_cap"),
        "pricing_proof_kind": payload.get("pricing_proof_kind") or "",
        "completion_bound_pruning_enabled": bool(payload.get("completion_bound_pruning_enabled")),
        "completion_bound_evaluated_label_count": int(
            payload.get("completion_bound_evaluated_label_count") or 0
        ),
        "completion_bound_pruned_label_count": int(payload.get("completion_bound_pruned_label_count") or 0),
        "completion_bound_can_certify_no_negative": bool(payload.get("completion_bound_can_certify_no_negative")),
        "bound_prune_count": int(payload.get("bound_prune_count") or 0),
        "generated_task_sets": payload.get("generated_task_sets") or [],
        "worker_seen_task_sets": payload.get("worker_seen_task_sets") or [],
        "worker_candidate_universe_task_sets": payload.get("worker_candidate_universe_task_sets") or [],
        "worker_generated_column_task_sets": payload.get("worker_generated_column_task_sets") or [],
        "worker_generated_column_task_set_count": int(
            payload.get("worker_generated_column_task_set_count") or 0
        ),
        "labeling_harvest_candidate_negative_count": int(
            payload.get("harvest_candidate_negative_count")
            if payload.get("harvest_candidate_negative_count") is not None
            else payload.get("labeling_harvest_candidate_negative_count") or 0
        ),
        "labeling_harvest_candidate_new_task_set_count": int(
            payload.get("harvest_candidate_new_task_set_count")
            if payload.get("harvest_candidate_new_task_set_count") is not None
            else payload.get("labeling_harvest_candidate_new_task_set_count") or 0
        ),
        "labeling_harvest_candidate_replacement_task_set_count": int(
            payload.get("harvest_candidate_replacement_task_set_count")
            if payload.get("harvest_candidate_replacement_task_set_count") is not None
            else payload.get("labeling_harvest_candidate_replacement_task_set_count") or 0
        ),
        "labeling_harvest_selected_count": int(
            payload.get("harvest_selected_count")
            if payload.get("harvest_selected_count") is not None
            else payload.get("labeling_harvest_selected_count") or 0
        ),
        "labeling_harvest_selected_new_task_set_count": int(
            payload.get("harvest_selected_new_task_set_count")
            if payload.get("harvest_selected_new_task_set_count") is not None
            else payload.get("labeling_harvest_selected_new_task_set_count") or 0
        ),
        "labeling_harvest_selected_replacement_task_set_count": int(
            payload.get("harvest_selected_replacement_task_set_count")
            if payload.get("harvest_selected_replacement_task_set_count") is not None
            else payload.get("labeling_harvest_selected_replacement_task_set_count") or 0
        ),
        "labeling_harvest_candidate_support_changing_count": int(
            payload.get("harvest_candidate_support_changing_count")
            if payload.get("harvest_candidate_support_changing_count") is not None
            else payload.get("labeling_harvest_candidate_support_changing_count") or 0
        ),
        "labeling_harvest_candidate_strong_replacement_count": int(
            payload.get("harvest_candidate_strong_replacement_count")
            if payload.get("harvest_candidate_strong_replacement_count") is not None
            else payload.get("labeling_harvest_candidate_strong_replacement_count") or 0
        ),
        "labeling_harvest_candidate_weak_replacement_count": int(
            payload.get("harvest_candidate_weak_replacement_count")
            if payload.get("harvest_candidate_weak_replacement_count") is not None
            else payload.get("labeling_harvest_candidate_weak_replacement_count") or 0
        ),
        "labeling_harvest_selected_support_changing_count": int(
            payload.get("harvest_selected_support_changing_count")
            if payload.get("harvest_selected_support_changing_count") is not None
            else payload.get("labeling_harvest_selected_support_changing_count") or 0
        ),
        "labeling_harvest_selected_strong_replacement_count": int(
            payload.get("harvest_selected_strong_replacement_count")
            if payload.get("harvest_selected_strong_replacement_count") is not None
            else payload.get("labeling_harvest_selected_strong_replacement_count") or 0
        ),
        "labeling_harvest_selected_weak_replacement_count": int(
            payload.get("harvest_selected_weak_replacement_count")
            if payload.get("harvest_selected_weak_replacement_count") is not None
            else payload.get("labeling_harvest_selected_weak_replacement_count") or 0
        ),
        "labeling_harvest_selected_distinct_task_set_count": int(
            payload.get("harvest_selected_distinct_task_set_count")
            if payload.get("harvest_selected_distinct_task_set_count") is not None
            else payload.get("labeling_harvest_selected_distinct_task_set_count") or 0
        ),
        "labeling_harvest_selected_duplicate_task_set_count": int(
            payload.get("harvest_selected_duplicate_task_set_count")
            if payload.get("harvest_selected_duplicate_task_set_count") is not None
            else payload.get("labeling_harvest_selected_duplicate_task_set_count") or 0
        ),
        "labeling_harvest_existing_master_task_set_count": int(
            payload.get("harvest_existing_master_task_set_count")
            if payload.get("harvest_existing_master_task_set_count") is not None
            else payload.get("labeling_harvest_existing_master_task_set_count") or 0
        ),
        "labeling_harvest_support_task_set_count": int(
            payload.get("harvest_support_task_set_count")
            if payload.get("harvest_support_task_set_count") is not None
            else payload.get("labeling_harvest_support_task_set_count") or 0
        ),
        "labeling_harvest_support_aware_enabled": bool(
            payload.get("harvest_support_aware_enabled")
            if payload.get("harvest_support_aware_enabled") is not None
            else payload.get("labeling_harvest_support_aware_enabled")
        ),
        "labeling_harvest_weak_replacement_cap": int(
            payload.get("harvest_weak_replacement_cap")
            if payload.get("harvest_weak_replacement_cap") is not None
            else payload.get("labeling_harvest_weak_replacement_cap") or 0
        ),
        "labeling_harvest_selection_policy": (
            payload.get("harvest_selection_policy")
            or payload.get("labeling_harvest_selection_policy")
            or ""
        ),
        "labeling_harvest_avg_pairwise_jaccard": (
            payload.get("harvest_avg_pairwise_jaccard")
            if payload.get("harvest_avg_pairwise_jaccard") is not None
            else payload.get("labeling_harvest_avg_pairwise_jaccard")
        ),
        "labeling_harvest_max_pairwise_jaccard": (
            payload.get("harvest_max_pairwise_jaccard")
            if payload.get("harvest_max_pairwise_jaccard") is not None
            else payload.get("labeling_harvest_max_pairwise_jaccard")
        ),
        "labeling_harvest_candidate_seed_source_counts": (
            payload.get("harvest_candidate_seed_source_counts")
            or payload.get("labeling_harvest_candidate_seed_source_counts")
            or {}
        ),
        "labeling_harvest_selected_seed_source_counts": (
            payload.get("harvest_selected_seed_source_counts")
            or payload.get("labeling_harvest_selected_seed_source_counts")
            or {}
        ),
        "worker_generated_count": int(payload.get("worker_generated_count") or 0),
        "worker_candidate_budget": int(payload.get("worker_candidate_budget") or 0),
        "worker_harvest_selected_new_task_set_count": int(
            payload.get("worker_harvest_selected_new_task_set_count") or 0
        ),
        "worker_harvest_selected_replacement_task_set_count": int(
            payload.get("worker_harvest_selected_replacement_task_set_count") or 0
        ),
        "worker_harvest_avg_pairwise_jaccard": payload.get("worker_harvest_avg_pairwise_jaccard"),
        "worker_harvest_priority": payload.get("worker_harvest_priority") or "",
        "worker_harvest_best_true_rc": payload.get("worker_harvest_best_true_rc"),
        "worker_harvest_worst_selected_true_rc": payload.get(
            "worker_harvest_worst_selected_true_rc"
        ),
        "task_bound_pruned_count": int(payload.get("task_bound_pruned_count") or 0),
        "resource_bound_pruned_count": int(payload.get("resource_bound_pruned_count") or 0),
        "dominance_filtered_count": int(payload.get("dominance_filtered_count") or 0),
        "duplicate_filtered_count": int(payload.get("duplicate_filtered_count") or 0),
        "pricing_timeout": bool(payload.get("pricing_timeout")),
        "refinement_seed_count": int(payload.get("refinement_seed_count") or 0),
        "active_refinement_seed_count": int(payload.get("active_refinement_seed_count") or 0),
        "refinement_seed_task_sets": payload.get("refinement_seed_task_sets") or [],
        "refinement_seed_task_count_counts": payload.get("refinement_seed_task_count_counts") or {},
        "refinement_expanded_seed_count": int(payload.get("refinement_expanded_seed_count") or 0),
        "active_refinement_expanded_seed_count": int(
            payload.get("active_refinement_expanded_seed_count") or 0
        ),
        "refinement_expanded_seed_task_sets": payload.get("refinement_expanded_seed_task_sets") or [],
        "refinement_expanded_seed_task_count_counts": payload.get(
            "refinement_expanded_seed_task_count_counts"
        )
        or {},
        "refinement_seed_source": payload.get("refinement_seed_source") or "",
        "refinement_seed_source_rows": payload.get("refinement_seed_source_rows") or [],
        "refinement_seed_policy": payload.get("refinement_seed_policy") or "",
        "refinement_seed_budget_limit": int(payload.get("refinement_seed_budget_limit") or 0),
        "refinement_seed_budget_reserves_first_expansion": bool(
            payload.get("refinement_seed_budget_reserves_first_expansion")
        ),
        "refinement_seed_source_match_counts": payload.get("refinement_seed_source_match_counts") or {},
        "refinement_seed_catalog_payload": payload.get("refinement_seed_catalog_payload") or {},
        "refinement_seed_mutates_certificate": bool(payload.get("refinement_seed_mutates_certificate")),
        "global_remaining_rc_lb": payload.get("global_remaining_rc_lb"),
        "global_remaining_rc_lb_valid": bool(payload.get("global_remaining_rc_lb_valid")),
        "global_remaining_rc_lb_coverage_complete": bool(payload.get("global_remaining_rc_lb_coverage_complete")),
        "frontier_region_count": payload.get("frontier_region_count"),
        "frontier_unsupported_region_count": payload.get("frontier_unsupported_region_count"),
        "frontier_unsupported_task_count_regions": payload.get(
            "frontier_unsupported_task_count_regions"
        )
        or [],
        "branch_context_audit_pass": bool(payload.get("branch_context_audit_pass")),
        "branch_invalid_column_count": int(payload.get("branch_invalid_column_count") or 0),
        "true_dual_audited_column_count": int(payload.get("true_dual_audited_column_count") or 0),
        "true_dual_selected_negative_count": int(payload.get("true_dual_selected_negative_count") or 0),
        "candidate_search_best_reduced_cost": payload.get("candidate_search_best_reduced_cost"),
        "candidate_search_negative_column_count": int(
            payload.get("candidate_search_negative_column_count") or 0
        ),
        "candidate_search_negative_true_negative_count": int(
            payload.get("candidate_search_negative_true_negative_count") or 0
        ),
        "candidate_search_negative_true_nonnegative_count": int(
            payload.get("candidate_search_negative_true_nonnegative_count") or 0
        ),
        "true_negative_candidate_search_nonnegative_count": int(
            payload.get("true_negative_candidate_search_nonnegative_count") or 0
        ),
        "candidate_search_false_positive_rate": payload.get("candidate_search_false_positive_rate"),
        "true_negative_candidate_search_miss_rate": payload.get(
            "true_negative_candidate_search_miss_rate"
        ),
        "candidate_search_false_positive_rows": payload.get("candidate_search_false_positive_rows") or [],
        "true_negative_candidate_search_miss_rows": payload.get(
            "true_negative_candidate_search_miss_rows"
        )
        or [],
        "candidate_search_dual_matches_true_dual": bool(
            payload.get("candidate_search_dual_matches_true_dual")
        ),
        "candidate_search_rc_recomputed_under_true_dual": bool(
            candidate_rc_recomputed
        ),
        "worker_true_dual_candidate_audit_pass": worker_candidate_audit_pass,
        "selected_column_entry_audit_available": bool(
            payload.get("selected_column_entry_audit_available")
        ),
        "selected_column_entry_audit_pass": bool(
            payload.get("selected_column_entry_audit_pass")
        ),
        "selected_column_true_dual_rc_audit_pass": bool(
            payload.get("selected_column_true_dual_rc_audit_pass")
        ),
        "selected_column_branch_audit_pass": bool(
            payload.get("selected_column_branch_audit_pass")
        ),
        "selected_column_cut_audit_pass": bool(
            payload.get("selected_column_cut_audit_pass")
        ),
        "selected_column_addability_audit_pass": bool(
            payload.get("selected_column_addability_audit_pass")
        ),
        "selected_column_audited_count": int(payload.get("selected_column_audited_count") or 0),
        "selected_column_entry_audit_rejected_count": int(
            payload.get("selected_column_entry_audit_rejected_count") or 0
        ),
        "selected_count_before_entry_audit": int(
            payload.get("selected_count_before_entry_audit")
            if payload.get("selected_count_before_entry_audit") is not None
            else payload.get("selected_count")
            or 0
        ),
        "entry_audit_rejected_selected_count": int(
            payload.get("entry_audit_rejected_selected_count") or 0
        ),
        "selected_would_enter_master_count": int(
            payload.get("selected_would_enter_master_count") or 0
        ),
        "selected_all_would_enter_master": bool(
            payload.get("selected_all_would_enter_master")
        ),
        "worker_selected_columns_audit_pass": bool(
            payload.get("worker_selected_columns_audit_pass")
        ),
        "worker_selected_columns_true_dual_audit_pass": bool(
            payload.get("worker_selected_columns_true_dual_audit_pass")
        ),
        "worker_selected_columns_branch_audit_pass": bool(
            payload.get("worker_selected_columns_branch_audit_pass")
        ),
        "worker_selected_columns_cut_audit_pass": bool(
            payload.get("worker_selected_columns_cut_audit_pass")
        ),
        "worker_selected_columns_addability_audit_pass": bool(
            payload.get("worker_selected_columns_addability_audit_pass")
        ),
        "labeling_harvest_candidate_negative_count": int(
            payload.get("labeling_harvest_candidate_negative_count") or 0
        ),
        "labeling_harvest_candidate_new_task_set_count": int(
            payload.get("labeling_harvest_candidate_new_task_set_count") or 0
        ),
        "labeling_harvest_candidate_replacement_task_set_count": int(
            payload.get("labeling_harvest_candidate_replacement_task_set_count") or 0
        ),
        "labeling_harvest_selected_count": int(payload.get("labeling_harvest_selected_count") or 0),
        "labeling_harvest_selected_new_task_set_count": int(
            payload.get("labeling_harvest_selected_new_task_set_count") or 0
        ),
        "labeling_harvest_selected_replacement_task_set_count": int(
            payload.get("labeling_harvest_selected_replacement_task_set_count") or 0
        ),
        "labeling_harvest_selected_distinct_task_set_count": int(
            payload.get("labeling_harvest_selected_distinct_task_set_count") or 0
        ),
        "labeling_harvest_selected_duplicate_task_set_count": int(
            payload.get("labeling_harvest_selected_duplicate_task_set_count") or 0
        ),
        "labeling_harvest_existing_master_task_set_count": int(
            payload.get("labeling_harvest_existing_master_task_set_count") or 0
        ),
        "labeling_harvest_selection_policy": payload.get("labeling_harvest_selection_policy") or "",
        "labeling_harvest_avg_pairwise_jaccard": payload.get("labeling_harvest_avg_pairwise_jaccard"),
        "labeling_harvest_max_pairwise_jaccard": payload.get("labeling_harvest_max_pairwise_jaccard"),
        "labeling_harvest_candidate_seed_source_counts": payload.get(
            "labeling_harvest_candidate_seed_source_counts"
        )
        or {},
        "labeling_harvest_selected_seed_source_counts": payload.get(
            "labeling_harvest_selected_seed_source_counts"
        )
        or {},
        "candidate_task_set_count": int(payload.get("candidate_task_set_count") or 0),
        "candidate_sequence_count": int(payload.get("candidate_sequence_count") or payload.get("candidate_sequences") or 0),
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
        "tail_dual_stabilization": payload.get("tail_dual_stabilization") or {},
        "worker_dual_source": payload.get("worker_dual_source") or "",
        "official_dual_source": payload.get("official_dual_source") or "",
        "worker_dual_only": bool(payload.get("worker_dual_only")),
        "true_dual_rc_recomputed": bool(payload.get("true_dual_rc_recomputed")),
        "tail_dual_no_column_can_certify": bool(payload.get("tail_dual_no_column_can_certify")),
        "rmp_dual_diagnostic": payload.get("rmp_dual_diagnostic") or {},
    }


def _exact_final_judge_first_skipped_worker_result(
    *,
    worker_pricer_kind: str,
    remaining_wall_time_sec: float | None,
) -> _NegativeSearchWorkerResult:
    """Return an explicit worker-skipped result for exact-pricer-first runs.

    This keeps the BPC proof boundary simple: no skipped or worker no-column
    state can certify anything; the following true-dual final judge must either
    add audited negative columns or produce the no-negative certificate.
    """

    payload = {
        "worker_status": PricingState.LOCAL_NO_COLUMN_UNCERTIFIED.value,
        "pricing_state": PricingState.LOCAL_NO_COLUMN_UNCERTIFIED.value,
        "exit_reason": "EXACT_FINAL_JUDGE_FIRST_WORKER_SKIPPED",
        "worker_wall_time": 0.0,
        "worker_pricer_kind": str(worker_pricer_kind),
        "exact_final_judge_first_enabled": True,
        "exact_final_judge_first_worker_skipped": True,
        "exact_final_judge_first_remaining_wall_time_sec": (
            None
            if remaining_wall_time_sec is None
            else round(float(remaining_wall_time_sec), 6)
        ),
        "candidate_search_only": True,
        "can_certify_no_negative": False,
        "uses_true_dual_bpc_certificate": False,
        "worker_dual_used_for_candidate_search": False,
        # Safety-redline consumers require candidate workers to be marked as
        # worker-only.  A skipped worker is the degenerate worker-only case;
        # it contributes neither a dual nor a certificate.
        "worker_dual_only": True,
        "official_dual_source": "current_true_rmp_dual",
        "candidate_search_rc_recomputed_under_true_dual": True,
        "candidate_search_dual_matches_true_dual": True,
        "pricing_proof_kind": "WORKER_SKIPPED_FOR_EXACT_FINAL_JUDGE_FIRST",
        "no_column_uncertified": True,
        "worker_no_column_can_certify": False,
        "worker_uses_true_dual_bpc_certificate": False,
        "worker_root_lp_bound_official": False,
        "worker_certificate_leak": False,
        "worker_true_dual_candidate_audit_pass": True,
        "true_dual_rc_recomputed": True,
        "tail_dual_no_column_can_certify": False,
        "tail_dual_certificate_leak": False,
        "candidate_negative_count": 0,
        "addable_negative_count": 0,
        "harvest_candidate_negative_count": 0,
        "harvest_selected_count": 0,
        "harvest_selected_new_task_set_count": 0,
        "harvest_selected_replacement_task_set_count": 0,
        "selected_count": 0,
        "selected_column_entry_audit_pass": True,
        "selected_column_true_dual_rc_audit_pass": True,
        "selected_column_branch_audit_pass": True,
        "selected_column_cut_audit_pass": True,
        "selected_column_addability_audit_pass": True,
        "selected_column_audited_count": 0,
        "selected_would_enter_master_count": 0,
        "selected_all_would_enter_master": True,
        "worker_selected_columns_audit_pass": True,
        "worker_selected_columns_true_dual_audit_pass": True,
        "worker_selected_columns_branch_audit_pass": True,
        "worker_selected_columns_cut_audit_pass": True,
        "worker_selected_columns_addability_audit_pass": True,
        "worker_seen_task_sets": [],
        "worker_generated_column_task_sets": [],
        "worker_generated_column_task_set_count": 0,
        "worker_candidate_universe_task_sets": [],
    }
    return _NegativeSearchWorkerResult(
        status=PricingState.LOCAL_NO_COLUMN_UNCERTIFIED,
        selected_columns=tuple(),
        negative_pairs=tuple(),
        harvest_payload={},
        payload=payload,
    )


class _WorkerHardTimeLimitExceeded(TimeoutError):
    pass


class _worker_hard_timeout:
    def __init__(self, seconds: float | None) -> None:
        self.seconds = None if seconds is None else float(seconds)
        self.enabled = False
        self.previous_handler = None
        self.previous_timer = (0.0, 0.0)

    def __enter__(self):
        if self.seconds is None or self.seconds <= 0.0:
            return self
        if threading.current_thread() is not threading.main_thread():
            return self
        if not hasattr(signal, "setitimer"):
            return self
        self.enabled = True
        self.previous_handler = signal.getsignal(signal.SIGALRM)
        self.previous_timer = signal.getitimer(signal.ITIMER_REAL)

        def _raise_timeout(_signum, _frame):
            raise _WorkerHardTimeLimitExceeded()

        signal.signal(signal.SIGALRM, _raise_timeout)
        signal.setitimer(signal.ITIMER_REAL, max(0.001, float(self.seconds)))
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self.enabled:
            signal.setitimer(signal.ITIMER_REAL, 0.0)
            signal.signal(signal.SIGALRM, self.previous_handler)
            previous_delay, previous_interval = self.previous_timer
            if previous_delay > 0.0:
                signal.setitimer(signal.ITIMER_REAL, previous_delay, previous_interval)
        return False


def _worker_hard_time_cap_sec(remaining_wall_time_sec: float | None) -> float | None:
    cap = _env_float(
        LABELING_WORKER_HARD_TIME_CAP_SEC_ENV,
        default=0.0,
        minimum=0.0,
        maximum=3600.0,
    )
    if cap <= 0.0:
        return None
    if remaining_wall_time_sec is None:
        return float(cap)
    return max(0.0, min(float(cap), float(remaining_wall_time_sec)))


def _worker_hard_timeout_result(
    *,
    worker_pricer_kind: str,
    elapsed_sec: float,
    hard_time_cap_sec: float | None,
    remaining_wall_time_sec: float | None,
) -> _NegativeSearchWorkerResult:
    payload = _exact_final_judge_first_skipped_worker_result(
        worker_pricer_kind=worker_pricer_kind,
        remaining_wall_time_sec=remaining_wall_time_sec,
    ).payload
    payload = dict(payload)
    payload.update(
        {
            "worker_status": PricingState.INCOMPLETE_LIMIT.value,
            "pricing_state": PricingState.INCOMPLETE_LIMIT.value,
            "exit_reason": "WORKER_HARD_TIME_LIMIT",
            "worker_wall_time": round(float(elapsed_sec), 6),
            "exact_final_judge_first_enabled": False,
            "exact_final_judge_first_worker_skipped": False,
            "worker_hard_time_limit_triggered": True,
            "worker_hard_time_cap_sec": (
                None if hard_time_cap_sec is None else round(float(hard_time_cap_sec), 6)
            ),
            "pricing_proof_kind": "WORKER_HARD_TIME_LIMIT_UNCERTIFIED",
            "note": (
                "Worker candidate search hit its hard time cap and was safely "
                "downgraded; only the following true-dual final judge may certify."
            ),
        }
    )
    return _NegativeSearchWorkerResult(
        status=PricingState.INCOMPLETE_LIMIT,
        selected_columns=tuple(),
        negative_pairs=tuple(),
        harvest_payload={},
        payload=payload,
    )


def _normalize_worker_pricer_kind(value: str) -> str:
    normalized = str(value or DIRECT_LABEL_WORKER).strip().lower()
    aliases = {
        "": DIRECT_LABEL_WORKER,
        "direct": DIRECT_LABEL_WORKER,
        "direct_label": DIRECT_LABEL_WORKER,
        "route_template": DIRECT_LABEL_WORKER,
        "label": RELAXED_LABELING_WORKER,
        "labeling": RELAXED_LABELING_WORKER,
        "relaxed_labeling": RELAXED_LABELING_WORKER,
        "ng": RELAXED_LABELING_WORKER,
        "ng_route": RELAXED_LABELING_WORKER,
        "relaxed_ng_route": RELAXED_LABELING_WORKER,
    }
    resolved = aliases.get(normalized)
    if resolved is None or resolved not in NEGATIVE_SEARCH_WORKER_KINDS:
        raise ValueError(f"unsupported worker_pricer_kind={value!r}")
    return resolved


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
    node_id: str = "root",
    branch_context: BranchContext | None = None,
    tail_dual_history: tuple[JourneyDuals, ...] = tuple(),
    tail_dual_stabilization_enabled: bool = False,
    tail_dual_stabilization_alpha: float = 0.7,
    tail_dual_stabilization_window: int = 5,
    worker_pricer_kind: str = DIRECT_LABEL_WORKER,
    cut_context: CutContext | None = None,
    wall_time_limit_sec: float | None = None,
) -> _NegativeSearchWorkerResult:
    worker_start = perf_counter()
    active_worker_kind = _normalize_worker_pricer_kind(worker_pricer_kind)
    active_cut_context = cut_context or CutContext()
    true_duals = _duals_from_reduced_cost_context(reduced_cost_context)
    worker_deadline = (
        None
        if wall_time_limit_sec is None
        else worker_start + max(0.0, float(wall_time_limit_sec))
    )
    tail_center = build_tail_dual_center(
        tail_dual_history or (true_duals,),
        window=tail_dual_stabilization_window,
    )
    worker_duals, tail_dual_payload = build_worker_duals_with_tail_center(
        true_duals,
        tail_dual_center=tail_center,
        enabled=tail_dual_stabilization_enabled,
        alpha=tail_dual_stabilization_alpha,
        window=tail_dual_stabilization_window,
    )
    worker_task_cap = _worker_task_cap(data, max_direct_tasks)
    seed_task_sets = _negative_worker_seed_task_sets(
        data,
        duals=worker_duals,
        master_columns=master_columns,
        b0_direct=b0_direct,
        seed_catalog=seed_catalog,
        max_direct_tasks=worker_task_cap,
        max_seed_sets=max(1, int(max_candidate_sets)),
    )
    refinement_seed_task_sets = _catalog_refinement_seed_task_sets(
        data,
        seed_catalog=seed_catalog,
        max_direct_tasks=worker_task_cap,
    )
    refinement_expanded_seed_task_sets = _catalog_refinement_neighborhood_seed_task_sets(
        data,
        duals=worker_duals,
        seed_catalog=seed_catalog,
        max_direct_tasks=worker_task_cap,
    )
    active_refinement_seed_count = _count_task_set_intersection(seed_task_sets, refinement_seed_task_sets)
    active_refinement_expanded_seed_count = _count_task_set_intersection(
        seed_task_sets,
        refinement_expanded_seed_task_sets,
    )
    refinement_seed_source_rows = _refinement_seed_source_rows(
        refinement_seed_task_sets=refinement_seed_task_sets,
        refinement_expanded_seed_task_sets=refinement_expanded_seed_task_sets,
    )
    physical_seed_columns, physical_seed_payload = _catalog_physical_seed_columns(
        data,
        seed_catalog=seed_catalog,
        branch_context=branch_context,
        max_columns=max(1, int(max_candidate_sets)),
    )
    if active_worker_kind == RELAXED_LABELING_WORKER:
        ng_sizes = _worker_ng_sizes(worker_task_cap)
        worker_batch_early_stop = _env_bool(
            LABELING_WORKER_NEGATIVE_BATCH_EARLY_STOP_ENV,
            default=False,
        )
        worker_harvest_target = (
            _env_int(
                LABELING_WORKER_NEGATIVE_BATCH_TARGET_ENV,
                default=max_selected,
                minimum=1,
                maximum=max(1, int(max_selected)),
            )
            if worker_batch_early_stop
            else max_selected
        )
        pricing, priced_columns = run_bpc_labeling_pricer(
            data,
            true_duals,
            config=LabelingPricingConfig(
                mode=RELAXED_NG_ROUTE_MODE,
                max_label_task_count=worker_task_cap,
                max_candidate_sets=max(1, int(max_candidate_sets)),
                harvest_target=worker_harvest_target,
                negative_eps=negative_eps,
                ng_neighborhood_size=ng_sizes[-1],
                ng_neighborhood_sizes=ng_sizes,
                dual_stabilization_enabled=tail_dual_stabilization_enabled,
                dual_stabilization_alpha=tail_dual_stabilization_alpha,
                dual_stabilization_window=tail_dual_stabilization_window,
                support_continuation_seed_enabled=_env_bool(
                    LABELING_SUPPORT_CONTINUATION_SEED_ENV,
                    default=True,
                ),
                support_continuation_max_seed_sets=_env_int(
                    LABELING_SUPPORT_CONTINUATION_MAX_SEED_SETS_ENV,
                    default=240,
                    minimum=0,
                    maximum=5000,
                ),
                support_continuation_max_neighbors=_env_int(
                    LABELING_SUPPORT_CONTINUATION_MAX_NEIGHBORS_ENV,
                    default=4,
                    minimum=1,
                    maximum=100,
                ),
                support_continuation_protected_seed_count=_env_int(
                    LABELING_SUPPORT_CONTINUATION_PROTECTED_SEED_COUNT_ENV,
                    default=8,
                    minimum=0,
                    maximum=5000,
                ),
                resource_extension_seed_enabled=_env_bool(
                    LABELING_WORKER_RESOURCE_EXTENSION_SEED_ENV,
                    default=True,
                ),
                stop_at_first_negative=bool(worker_batch_early_stop),
                wall_time_limit_sec=wall_time_limit_sec,
            ),
            branch_context=branch_context,
            cut_context=active_cut_context,
            seed_task_sets=seed_task_sets,
            seed_source_rows=refinement_seed_source_rows,
            existing_task_sets=tuple(tuple(str(task_id) for task_id in column.task_set) for column in master_columns),
            support_task_sets=_rmp_support_task_sets(master),
            dual_history=tail_dual_history or (true_duals,),
        )
        pricing["worker_negative_batch_early_stop_enabled"] = bool(worker_batch_early_stop)
        pricing["worker_negative_batch_target"] = int(worker_harvest_target)
    else:
        pricing, priced_columns = run_resource_label_core(
            data,
            worker_duals,
            config=ResourceLabelCoreConfig(
                mode=CORE_DIRECT_SELECTED_SET_WORKER,
                max_task_count=worker_task_cap,
                max_candidate_sets=max(1, int(max_candidate_sets)),
                negative_eps=negative_eps,
                wall_time_limit_sec=wall_time_limit_sec,
            ),
            seed_task_sets=seed_task_sets,
            seed_source_rows=refinement_seed_source_rows,
            branch_context=branch_context,
            cut_context=active_cut_context,
            cache=cache,
        )
    large_direct_payload, large_direct_columns = _run_large_task_direct_worker(
        data,
        worker_duals=worker_duals,
        true_duals=true_duals,
        master_columns=master_columns,
        b0_direct=b0_direct,
        support_task_sets=_rmp_support_task_sets(master),
        worker_task_cap=worker_task_cap,
        max_direct_tasks=max_direct_tasks,
        max_candidate_sets=max_candidate_sets,
        negative_eps=negative_eps,
        branch_context=branch_context,
        cut_context=active_cut_context,
        deadline=worker_deadline,
    )
    priced_columns = _dedupe_journey_columns(
        (*physical_seed_columns, *priced_columns, *large_direct_columns)
    )
    negative_pairs = _manual_negative_pairs(
        priced_columns,
        duals=true_duals,
        negative_eps=negative_eps,
        branch_context=branch_context,
        cut_context=active_cut_context,
    )
    candidate_audit_payload = _candidate_search_true_dual_audit_payload(
        priced_columns,
        search_duals=worker_duals,
        true_duals=true_duals,
        negative_eps=negative_eps,
        branch_context=branch_context,
        cut_context=active_cut_context,
    )
    candidate_search_dual_matches_true_dual = pricing.get("candidate_search_dual_matches_true_dual")
    if candidate_search_dual_matches_true_dual is None:
        candidate_search_dual_matches_true_dual = _journey_duals_match(worker_duals, true_duals)
    candidate_search_rc_recomputed_under_true_dual = pricing.get(
        "candidate_search_rc_recomputed_under_true_dual"
    )
    if candidate_search_rc_recomputed_under_true_dual is None:
        candidate_search_rc_recomputed_under_true_dual = True
    selected, harvest_payload = harvest_addable_negative_columns(
        negative_pairs,
        pool=pool,
        view=view,
        node_id=node_id,
        negative_eps=negative_eps,
        max_selected=max_selected,
        active_task_sets={frozenset(column.task_set) for column in master_columns},
        branch_context=branch_context,
        cut_context=active_cut_context,
        profiling=profiling,
        source_phase="worker_candidate_search_addability_harvest",
    )
    selected_audit_payload = _audit_selected_columns_for_master_entry(
        selected,
        duals=true_duals,
        pool=pool,
        view=view,
        node_id=node_id,
        negative_eps=negative_eps,
        active_task_sets={frozenset(column.task_set) for column in master_columns},
        branch_context=branch_context,
        cut_context=active_cut_context,
    )
    harvest_payload = dict(harvest_payload)
    harvest_payload.update(selected_audit_payload)
    if selected and not selected_audit_payload["selected_column_entry_audit_pass"]:
        harvest_payload["selected_count_before_entry_audit"] = int(len(selected))
        harvest_payload["entry_audit_rejected_selected_count"] = int(len(selected))
        harvest_payload["selected_count"] = 0
        harvest_payload["selected_would_enter_master_count"] = 0
        harvest_payload["selected_all_would_enter_master"] = False
        harvest_payload["harvest_selected_count"] = 0
        selected = tuple()
    worker_wall_time = perf_counter() - worker_start
    cache_stats = cache.stats()
    completion_payload = pricing.get("completion_bound") if isinstance(pricing.get("completion_bound"), dict) else {}
    labels_generated = int(pricing.get("pareto_label_count") or 0)
    generated_task_sets = _worker_generated_task_sets(pricing)
    worker_seen_task_sets = _worker_seen_task_sets(pricing, priced_columns)
    branch_invalid_column_count = int(
        pricing.get("branch_invalid_column_count")
        if pricing.get("branch_invalid_column_count") is not None
        else sum(
            1 for column in priced_columns if not journey_satisfies_branch_context(column, branch_context)
        )
    )
    branch_context_audit_pass = bool(
        pricing.get("branch_context_audit_pass")
        if pricing.get("branch_context_audit_pass") is not None
        else branch_invalid_column_count == 0
    )
    worker_true_dual_candidate_audit_pass = bool(
        candidate_search_rc_recomputed_under_true_dual
        and branch_context_audit_pass
    )
    task_bound_pruned_count = int(completion_payload.get("pruned_label_count") or 0)
    resource_bound_pruned_count = int(
        pricing.get("resource_bound_pruned_count")
        or pricing.get("resource_prune_count")
        or 0
    )
    dominance_filtered_count = int(
        harvest_payload.get("harvest_dominance_filtered_count")
        or pricing.get("dominance_filtered_count")
        or pricing.get("dominance_prune_count")
        or 0
    )
    duplicate_filtered_count = int(
        harvest_payload.get("duplicate_in_current_master_count")
        or harvest_payload.get("harvest_duplicate_in_current_master_count")
        or pricing.get("duplicate_filtered_count")
        or 0
    )
    pricing_timeout = bool(
        pricing.get("pricing_timeout")
        or str(pricing.get("status") or "").endswith("TIME_LIMIT")
        or str(pricing.get("status") or "").endswith("_TIME_LIMIT")
    )
    underlying_incomplete = bool(
        pricing_timeout
        or pricing.get("pricing_state") == PricingState.INCOMPLETE_LIMIT.value
        or str(pricing.get("status") or "").startswith("SKIPPED")
    )
    status = (
        PricingState.FOUND_NEGATIVE
        if negative_pairs
        else PricingState.INCOMPLETE_LIMIT
        if underlying_incomplete
        else PricingState.LOCAL_NO_COLUMN_UNCERTIFIED
    )
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
        "worker_pricer_kind": active_worker_kind,
        "labeling_worker_enabled": active_worker_kind == RELAXED_LABELING_WORKER,
        "labeling_algorithm": pricing.get("labeling_algorithm"),
        "resource_label_algorithm": pricing.get("resource_label_algorithm"),
        "resource_label_core_mode": pricing.get("resource_label_core_mode"),
        "pricing_engine_role": pricing.get("pricing_engine_role") or "",
        "candidate_search_only": bool(pricing.get("candidate_search_only")),
        "relaxed_candidate_search_can_certify_no_negative": bool(
            pricing.get("relaxed_candidate_search_can_certify_no_negative")
        ),
        "no_column_certificate_allowed": bool(pricing.get("no_column_certificate_allowed")),
        "ng_route_relaxation_kind": pricing.get("ng_route_relaxation_kind") or "",
        "ng_route_relaxation_is_certificate_relaxation": bool(
            pricing.get("ng_route_relaxation_is_certificate_relaxation")
        ),
        "relaxed_route_elementarity_proof_supported": bool(
            pricing.get("relaxed_route_elementarity_proof_supported")
        ),
        "dssr_refinement_status": pricing.get("dssr_refinement_status") or "",
        "exact_final_proof_required_after_worker": bool(
            pricing.get("exact_final_proof_required_after_worker")
        ),
        "exact_final_proof_expected_mode": pricing.get("exact_final_proof_expected_mode") or "",
        "resource_dimensions": pricing.get("resource_dimensions") or [],
        "dominance_policy": pricing.get("dominance_policy"),
        "elementarity_policy": pricing.get("elementarity_policy"),
        "round": int(round_index),
        "worker_status": status.value,
        "pricing_state": status.value,
        "exit_reason": exit_reason,
        "worker_underlying_incomplete": bool(underlying_incomplete),
        "worker_underlying_pricing_state": str(pricing.get("pricing_state") or ""),
        "worker_underlying_status": str(pricing.get("status") or ""),
        "pricing_proof_kind": pricing.get("pricing_proof_kind") or (
            "DIRECT_WORKER_UNCERTIFIED"
            if active_worker_kind == DIRECT_LABEL_WORKER
            else "RELAXED_WORKER_UNCERTIFIED"
        ),
        "global_remaining_rc_lb": pricing.get("global_remaining_rc_lb"),
        "global_remaining_rc_lb_valid": bool(pricing.get("global_remaining_rc_lb_valid")),
        "global_remaining_rc_lb_coverage_complete": bool(
            pricing.get("global_remaining_rc_lb_coverage_complete")
        ),
        "frontier_region_count": pricing.get("frontier_region_count"),
        "frontier_unsupported_region_count": pricing.get("frontier_unsupported_region_count"),
        "frontier_unsupported_task_count_regions": pricing.get(
            "frontier_unsupported_task_count_regions"
        )
        or [],
        "branch_context_audit_pass": branch_context_audit_pass,
        "branch_invalid_column_count": branch_invalid_column_count,
        "cut_context_active": not active_cut_context.empty,
        "cut_count": len(active_cut_context.cuts),
        "can_certify_no_negative": False,
        "uses_true_dual_bpc_certificate": False,
        "root_lp_bound_official": False,
        "dual_source": "master.reduced_cost_context",
        "diagnostic_dual_source": (
            "tail_dual_stabilized_worker_dual"
            if tail_dual_payload.get("tail_dual_stabilization_enabled")
            else "master.reduced_cost_context"
        ),
        "worker_dual_source": tail_dual_payload.get("worker_dual_source"),
        "official_dual_source": tail_dual_payload.get("official_dual_source"),
        "worker_dual_only": True,
        "requires_true_dual_rc_recompute": True,
        "true_dual_rc_recomputed": True,
        "selected_column_entry_audit_available": True,
        "selected_column_entry_audit_pass": bool(
            selected_audit_payload["selected_column_entry_audit_pass"]
        ),
        "selected_column_true_dual_rc_audit_pass": bool(
            selected_audit_payload["selected_column_true_dual_rc_audit_pass"]
        ),
        "selected_column_branch_audit_pass": bool(
            selected_audit_payload["selected_column_branch_audit_pass"]
        ),
        "selected_column_cut_audit_pass": bool(
            selected_audit_payload["selected_column_cut_audit_pass"]
        ),
        "selected_column_addability_audit_pass": bool(
            selected_audit_payload["selected_column_addability_audit_pass"]
        ),
        "selected_column_audited_count": int(
            selected_audit_payload["selected_column_audited_count"]
        ),
        "selected_column_entry_audit_rejected_count": int(
            selected_audit_payload["selected_column_entry_audit_rejected_count"]
        ),
        "worker_selected_columns_audit_pass": bool(
            selected_audit_payload["selected_column_entry_audit_pass"]
        ),
        "worker_selected_columns_true_dual_audit_pass": bool(
            selected_audit_payload["selected_column_true_dual_rc_audit_pass"]
        ),
        "worker_selected_columns_branch_audit_pass": bool(
            selected_audit_payload["selected_column_branch_audit_pass"]
        ),
        "worker_selected_columns_cut_audit_pass": bool(
            selected_audit_payload["selected_column_cut_audit_pass"]
        ),
        "worker_selected_columns_addability_audit_pass": bool(
            selected_audit_payload["selected_column_addability_audit_pass"]
        ),
        "tail_dual_no_column_can_certify": False,
        "tail_dual_stabilization": tail_dual_payload,
        "diagnostic_rmp_iteration_id": str(getattr(reduced_cost_context, "rmp_iteration_id", "") or ""),
        "diagnostic_dual_fingerprint": str(getattr(reduced_cost_context, "dual_fingerprint", "") or ""),
        "completion_bound_pruning_enabled": bool(completion_payload.get("enabled")),
        "completion_bound": completion_payload,
        "completion_bound_evaluated_label_count": int(completion_payload.get("evaluated_label_count") or 0),
        "completion_bound_pruned_label_count": int(completion_payload.get("pruned_label_count") or 0),
        "completion_bound_can_certify_no_negative": bool(
            completion_payload.get("can_certify_no_negative")
        ),
        "worker_wall_time": round(worker_wall_time, 6),
        "worker_wall_time_limit_sec": wall_time_limit_sec,
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
        "generated_task_sets": generated_task_sets,
        "worker_seen_task_sets": worker_seen_task_sets,
        "worker_candidate_universe_task_sets": pricing.get("worker_candidate_universe_task_sets")
        or pricing.get("active_seed_task_sets")
        or [],
        "worker_generated_column_task_sets": pricing.get("worker_generated_column_task_sets")
        or worker_seen_task_sets,
        "worker_generated_column_task_set_count": int(
            pricing.get("worker_generated_column_task_set_count") or len(worker_seen_task_sets)
        ),
        "worker_generated_count": len(generated_task_sets),
        "worker_candidate_budget": int(max_candidate_sets),
        "task_bound_pruned_count": task_bound_pruned_count,
        "resource_bound_pruned_count": resource_bound_pruned_count,
        "dominance_filtered_count": dominance_filtered_count,
        "duplicate_filtered_count": duplicate_filtered_count,
        "pricing_timeout": pricing_timeout,
        "resource_prune_count": resource_bound_pruned_count,
        "time_window_prune_count": 0,
        "dominance_prune_count": dominance_filtered_count,
        "bound_prune_count": task_bound_pruned_count,
        "cache_hit_count": int(cache_stats.get("hit_count") or 0),
        "cache_miss_count": int(cache_stats.get("miss_count") or 0),
        "candidate_negative_count": int(harvest_payload.get("candidate_negative_count") or 0),
        "addable_negative_count": int(harvest_payload.get("addable_negative_count") or 0),
        "duplicate_negative_count": int(harvest_payload.get("duplicate_in_current_master_count") or 0),
        "selected_count": int(harvest_payload.get("selected_count") or 0),
        "selected_count_before_entry_audit": int(
            harvest_payload.get("selected_count_before_entry_audit")
            if harvest_payload.get("selected_count_before_entry_audit") is not None
            else harvest_payload.get("selected_count")
            or 0
        ),
        "entry_audit_rejected_selected_count": int(
            harvest_payload.get("entry_audit_rejected_selected_count") or 0
        ),
        "selected_would_enter_master_count": int(
            harvest_payload.get("selected_would_enter_master_count") or 0
        ),
        "selected_all_would_enter_master": bool(
            harvest_payload.get("selected_all_would_enter_master")
        ),
        "worker_harvest_selected_new_task_set_count": int(
            harvest_payload.get("harvest_selected_new_task_set_count") or 0
        ),
        "worker_harvest_selected_replacement_task_set_count": int(
            harvest_payload.get("harvest_selected_replacement_task_set_count") or 0
        ),
        "worker_harvest_avg_pairwise_jaccard": harvest_payload.get("harvest_avg_pairwise_jaccard"),
        "worker_harvest_priority": harvest_payload.get("harvest_priority") or "",
        "worker_harvest_best_true_rc": harvest_payload.get("harvest_best_true_rc"),
        "worker_harvest_worst_selected_true_rc": harvest_payload.get("harvest_worst_selected_true_rc"),
        "manual_rc_validated_negative_count": len(negative_pairs),
        "seed_task_set_count": len(seed_task_sets),
        "refinement_seed_count": len(refinement_seed_task_sets),
        "active_refinement_seed_count": active_refinement_seed_count,
        "refinement_seed_task_sets": [list(row) for row in refinement_seed_task_sets],
        "refinement_seed_task_count_counts": _task_set_count_by_size(refinement_seed_task_sets),
        "refinement_expanded_seed_count": len(refinement_expanded_seed_task_sets),
        "active_refinement_expanded_seed_count": active_refinement_expanded_seed_count,
        "refinement_expanded_seed_task_sets": [list(row) for row in refinement_expanded_seed_task_sets],
        "refinement_expanded_seed_task_count_counts": _task_set_count_by_size(
            refinement_expanded_seed_task_sets
        ),
        "refinement_seed_source": "hidden_negative_audit_catalog",
        "refinement_seed_source_rows": refinement_seed_source_rows,
        "refinement_seed_policy": (
            "hidden_negative_unseen_first_then_superset_then_exact_with_first_expansion_reserve"
        ),
        "refinement_seed_budget_limit": int(max_candidate_sets),
        "refinement_seed_budget_reserves_first_expansion": True,
        "refinement_seed_source_match_counts": _catalog_refinement_source_match_counts(seed_catalog),
        "refinement_seed_catalog_payload": seed_catalog.to_payload(),
        "refinement_seed_mutates_certificate": False,
        **large_direct_payload,
        **physical_seed_payload,
        "labeling_seed_task_set_count": int(pricing.get("merged_seed_task_set_count") or len(seed_task_sets)),
        "ng_seed_task_set_count": int(pricing.get("ng_seed_task_set_count") or 0),
        "resource_extension_seed_enabled": bool(pricing.get("resource_extension_seed_enabled")),
        "resource_extension_seed_task_set_count": int(
            pricing.get("resource_extension_seed_task_set_count") or 0
        ),
        "active_resource_extension_seed_task_set_count": int(
            pricing.get("active_resource_extension_seed_task_set_count") or 0
        ),
        "resource_extension_seed_task_set_count_by_size": pricing.get(
            "resource_extension_seed_task_set_count_by_size"
        )
        or {},
        "resource_extension_label_column_worker_enabled": bool(
            pricing.get("resource_extension_label_column_worker_enabled")
        ),
        "resource_extension_label_column_count": int(
            pricing.get("resource_extension_label_column_count") or 0
        ),
        "resource_extension_label_column_task_set_count": int(
            pricing.get("resource_extension_label_column_task_set_count") or 0
        ),
        "resource_extension_label_column_task_sets": pricing.get(
            "resource_extension_label_column_task_sets"
        )
        or [],
        "resource_extension_label_column_policy": pricing.get(
            "resource_extension_label_column_policy"
        )
        or "",
        "resource_extension_label_columns_can_certify_no_negative": bool(
            pricing.get("resource_extension_label_columns_can_certify_no_negative")
        ),
        "resource_extension_label_stats": pricing.get("resource_extension_label_stats") or {},
        "resource_extension_label_attempt_count": int(
            pricing.get("resource_extension_label_attempt_count") or 0
        ),
        "resource_extension_label_dominance_rejected_count": int(
            pricing.get("resource_extension_label_dominance_rejected_count") or 0
        ),
        "resource_extension_label_capacity_truncated_count": int(
            pricing.get("resource_extension_label_capacity_truncated_count") or 0
        ),
        "resource_extension_label_path_variant_candidate_count": int(
            pricing.get("resource_extension_label_path_variant_candidate_count") or 0
        ),
        "resource_extension_label_path_variant_duplicate_count": int(
            pricing.get("resource_extension_label_path_variant_duplicate_count") or 0
        ),
        "resource_extension_label_path_variant_feasible_count": int(
            pricing.get("resource_extension_label_path_variant_feasible_count") or 0
        ),
        "resource_extension_label_path_variant_infeasible_count": int(
            pricing.get("resource_extension_label_path_variant_infeasible_count") or 0
        ),
        "resource_extension_proxy_profiles": pricing.get("resource_extension_proxy_profiles") or [],
        "resource_extension_proxy_profile_count": int(pricing.get("resource_extension_proxy_profile_count") or 0),
        "active_seed_task_set_source_counts": pricing.get("active_seed_task_set_source_counts") or {},
        "active_seed_task_set_source_task_count_counts": pricing.get(
            "active_seed_task_set_source_task_count_counts"
        )
        or {},
        "active_seed_task_set_sources": pricing.get("active_seed_task_set_sources") or [],
        "active_seed_selection_policy": pricing.get("active_seed_selection_policy") or "",
        "protected_refinement_seed_task_set_count": int(
            pricing.get("protected_refinement_seed_task_set_count") or 0
        ),
        "active_protected_refinement_seed_task_set_count": int(
            pricing.get("active_protected_refinement_seed_task_set_count") or 0
        ),
        "protected_refinement_seed_task_set_count_by_size": pricing.get(
            "protected_refinement_seed_task_set_count_by_size"
        )
        or {},
        "protected_refinement_seed_budget_truncated_count": int(
            pricing.get("protected_refinement_seed_budget_truncated_count") or 0
        ),
        "protected_support_continuation_seed_budget": int(
            pricing.get("protected_support_continuation_seed_budget") or 0
        ),
        "protected_support_continuation_seed_task_set_count": int(
            pricing.get("protected_support_continuation_seed_task_set_count") or 0
        ),
        "active_protected_support_continuation_seed_task_set_count": int(
            pricing.get("active_protected_support_continuation_seed_task_set_count") or 0
        ),
        "protected_support_continuation_seed_task_set_count_by_size": pricing.get(
            "protected_support_continuation_seed_task_set_count_by_size"
        )
        or {},
        "protected_support_continuation_seed_budget_truncated_count": int(
            pricing.get("protected_support_continuation_seed_budget_truncated_count") or 0
        ),
        "active_seed_task_set_count_by_size": pricing.get("active_seed_task_set_count_by_size") or {},
        "branch_seed_filter_enabled": bool(pricing.get("branch_seed_filter_enabled")),
        "branch_seed_filtered_input_count": int(pricing.get("branch_seed_filtered_input_count") or 0),
        "branch_seed_filtered_ng_count": int(pricing.get("branch_seed_filtered_ng_count") or 0),
        "branch_seed_filtered_resource_extension_count": int(
            pricing.get("branch_seed_filtered_resource_extension_count") or 0
        ),
        "priced_candidate_task_set_source_counts": pricing.get(
            "priced_candidate_task_set_source_counts"
        )
        or {},
        "priced_candidate_task_set_source_task_count_counts": pricing.get(
            "priced_candidate_task_set_source_task_count_counts"
        )
        or {},
        "priced_candidate_task_set_sources": pricing.get("priced_candidate_task_set_sources") or [],
        "direct_candidate_task_set_count": int(pricing.get("direct_candidate_task_set_count") or 0),
        "candidate_seed_source_precedence": pricing.get("candidate_seed_source_precedence") or [],
        "input_seed_task_set_count": int(pricing.get("seed_task_set_count") or len(seed_task_sets)),
        "merged_seed_task_set_count": int(pricing.get("merged_seed_task_set_count") or len(seed_task_sets)),
        "active_seed_task_set_count": int(pricing.get("active_seed_task_set_count") or 0),
        "active_ng_seed_task_set_count": int(pricing.get("active_ng_seed_task_set_count") or 0),
        "active_input_seed_task_set_count": int(pricing.get("active_input_seed_task_set_count") or 0),
        "ng_neighborhood_size": int(pricing.get("ng_neighborhood_size") or 0),
        "ng_neighborhood_sizes": pricing.get("ng_neighborhood_sizes") or [],
        "ng_neighborhood_stage_count": int(pricing.get("ng_neighborhood_stage_count") or 0),
        "ng_seed_task_set_count_by_size": pricing.get("ng_seed_task_set_count_by_size") or {},
        "true_dual_audited_column_count": int(pricing.get("true_audited_column_count") or len(priced_columns)),
        "true_dual_selected_negative_count": int(pricing.get("true_selected_negative_count") or 0),
        "candidate_search_best_reduced_cost": _payload_or_fallback(
            pricing,
            "candidate_search_best_reduced_cost",
            candidate_audit_payload,
        ),
        "candidate_search_negative_column_count": int(
            _payload_or_fallback(
                pricing,
                "candidate_search_negative_column_count",
                candidate_audit_payload,
            )
            or 0
        ),
        "candidate_search_negative_true_negative_count": int(
            _payload_or_fallback(
                pricing,
                "candidate_search_negative_true_negative_count",
                candidate_audit_payload,
            )
            or 0
        ),
        "candidate_search_negative_true_nonnegative_count": int(
            _payload_or_fallback(
                pricing,
                "candidate_search_negative_true_nonnegative_count",
                candidate_audit_payload,
            )
            or 0
        ),
        "true_negative_candidate_search_nonnegative_count": int(
            _payload_or_fallback(
                pricing,
                "true_negative_candidate_search_nonnegative_count",
                candidate_audit_payload,
            )
            or 0
        ),
        "candidate_search_false_positive_rate": _payload_or_fallback(
            pricing,
            "candidate_search_false_positive_rate",
            candidate_audit_payload,
        ),
        "true_negative_candidate_search_miss_rate": _payload_or_fallback(
            pricing,
            "true_negative_candidate_search_miss_rate",
            candidate_audit_payload,
        ),
        "candidate_search_false_positive_rows": _payload_or_fallback(
            pricing,
            "candidate_search_false_positive_rows",
            candidate_audit_payload,
        )
        or [],
        "true_negative_candidate_search_miss_rows": _payload_or_fallback(
            pricing,
            "true_negative_candidate_search_miss_rows",
            candidate_audit_payload,
        )
        or [],
        "candidate_search_dual_matches_true_dual": bool(candidate_search_dual_matches_true_dual),
        "candidate_search_rc_recomputed_under_true_dual": bool(
            candidate_search_rc_recomputed_under_true_dual
        ),
        "worker_true_dual_candidate_audit_pass": bool(worker_true_dual_candidate_audit_pass),
        "labeling_harvest_candidate_negative_count": int(pricing.get("harvest_candidate_negative_count") or 0),
        "labeling_harvest_candidate_new_task_set_count": int(
            pricing.get("harvest_candidate_new_task_set_count") or 0
        ),
        "labeling_harvest_candidate_replacement_task_set_count": int(
            pricing.get("harvest_candidate_replacement_task_set_count") or 0
        ),
        "labeling_harvest_selected_count": int(pricing.get("harvest_selected_count") or 0),
        "labeling_harvest_selected_new_task_set_count": int(
            pricing.get("harvest_selected_new_task_set_count") or 0
        ),
        "labeling_harvest_selected_replacement_task_set_count": int(
            pricing.get("harvest_selected_replacement_task_set_count") or 0
        ),
        "labeling_harvest_candidate_support_changing_count": int(
            pricing.get("harvest_candidate_support_changing_count") or 0
        ),
        "labeling_harvest_candidate_strong_replacement_count": int(
            pricing.get("harvest_candidate_strong_replacement_count") or 0
        ),
        "labeling_harvest_candidate_weak_replacement_count": int(
            pricing.get("harvest_candidate_weak_replacement_count") or 0
        ),
        "labeling_harvest_selected_support_changing_count": int(
            pricing.get("harvest_selected_support_changing_count") or 0
        ),
        "labeling_harvest_selected_strong_replacement_count": int(
            pricing.get("harvest_selected_strong_replacement_count") or 0
        ),
        "labeling_harvest_selected_weak_replacement_count": int(
            pricing.get("harvest_selected_weak_replacement_count") or 0
        ),
        "labeling_harvest_selected_distinct_task_set_count": int(
            pricing.get("harvest_selected_distinct_task_set_count") or 0
        ),
        "labeling_harvest_selected_duplicate_task_set_count": int(
            pricing.get("harvest_selected_duplicate_task_set_count") or 0
        ),
        "labeling_harvest_existing_master_task_set_count": int(
            pricing.get("harvest_existing_master_task_set_count") or 0
        ),
        "labeling_harvest_support_task_set_count": int(
            pricing.get("harvest_support_task_set_count") or 0
        ),
        "labeling_harvest_support_aware_enabled": bool(
            pricing.get("harvest_support_aware_enabled")
        ),
        "labeling_harvest_weak_replacement_cap": int(
            pricing.get("harvest_weak_replacement_cap") or 0
        ),
        "labeling_harvest_selection_policy": pricing.get("harvest_selection_policy") or "",
        "labeling_harvest_avg_pairwise_jaccard": pricing.get("harvest_avg_pairwise_jaccard"),
        "labeling_harvest_max_pairwise_jaccard": pricing.get("harvest_max_pairwise_jaccard"),
        "labeling_harvest_candidate_seed_source_counts": pricing.get(
            "harvest_candidate_seed_source_counts"
        )
        or {},
        "labeling_harvest_selected_seed_source_counts": pricing.get(
            "harvest_selected_seed_source_counts"
        )
        or {},
        "labeling_no_column_uncertified": bool(pricing.get("no_column_uncertified")),
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
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
) -> tuple[tuple[float, JourneyColumn], ...]:
    pairs: list[tuple[float, JourneyColumn]] = []
    threshold = -abs(float(negative_eps))
    context = cut_context or CutContext()
    for column in columns:
        if not journey_satisfies_branch_context(column, branch_context):
            continue
        rc = manual_journey_reduced_cost(
            column,
            duals,
            cut_coefficients=context.coefficients_for(column),
        )
        if rc < threshold:
            pairs.append((rc, column))
    return tuple(pairs)


def _payload_or_fallback(primary: Mapping[str, object], key: str, fallback: Mapping[str, object]) -> object:
    value = primary.get(key)
    return fallback.get(key) if value is None else value


def _journey_duals_match(left: JourneyDuals, right: JourneyDuals, *, eps: float = 1.0e-9) -> bool:
    if abs(float(left.fleet_limit) - float(right.fleet_limit)) > eps:
        return False
    cover_keys = {str(key) for key in left.cover} | {str(key) for key in right.cover}
    for key in cover_keys:
        if abs(float(left.cover.get(key, 0.0)) - float(right.cover.get(key, 0.0))) > eps:
            return False
    left_cuts = left.cuts or {}
    right_cuts = right.cuts or {}
    cut_keys = {str(key) for key in left_cuts} | {str(key) for key in right_cuts}
    for key in cut_keys:
        if abs(float(left_cuts.get(key, 0.0)) - float(right_cuts.get(key, 0.0))) > eps:
            return False
    return True


def _candidate_search_true_dual_audit_payload(
    columns: Iterable[JourneyColumn],
    *,
    search_duals: JourneyDuals,
    true_duals: JourneyDuals,
    negative_eps: float,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
) -> dict:
    threshold = -abs(float(negative_eps))
    context = cut_context or CutContext()
    best_search_rc: float | None = None
    search_negative_count = 0
    search_negative_true_negative_count = 0
    search_negative_true_nonnegative_count = 0
    true_negative_count = 0
    true_negative_search_nonnegative_count = 0
    false_positive_rows: list[dict] = []
    miss_rows: list[dict] = []
    for column in columns:
        if not journey_satisfies_branch_context(column, branch_context):
            continue
        cut_coefficients = context.coefficients_for(column)
        search_rc = manual_journey_reduced_cost(
            column,
            search_duals,
            cut_coefficients=cut_coefficients,
        )
        true_rc = manual_journey_reduced_cost(
            column,
            true_duals,
            cut_coefficients=cut_coefficients,
        )
        best_search_rc = (
            float(search_rc)
            if best_search_rc is None
            else min(float(best_search_rc), float(search_rc))
        )
        search_negative = float(search_rc) < threshold
        true_negative = float(true_rc) < threshold
        if search_negative:
            search_negative_count += 1
            if true_negative:
                search_negative_true_negative_count += 1
            else:
                search_negative_true_nonnegative_count += 1
                if len(false_positive_rows) < 20:
                    false_positive_rows.append(
                        {
                            "task_set": sorted(str(task_id) for task_id in column.task_set),
                            "candidate_search_rc": round(float(search_rc), 9),
                            "true_rc": round(float(true_rc), 9),
                        }
                    )
        if true_negative:
            true_negative_count += 1
            if not search_negative:
                true_negative_search_nonnegative_count += 1
                if len(miss_rows) < 20:
                    miss_rows.append(
                        {
                            "task_set": sorted(str(task_id) for task_id in column.task_set),
                            "candidate_search_rc": round(float(search_rc), 9),
                            "true_rc": round(float(true_rc), 9),
                        }
                    )
    return {
        "candidate_search_best_reduced_cost": (
            None if best_search_rc is None else round(float(best_search_rc), 9)
        ),
        "candidate_search_negative_column_count": int(search_negative_count),
        "candidate_search_negative_true_negative_count": int(search_negative_true_negative_count),
        "candidate_search_negative_true_nonnegative_count": int(
            search_negative_true_nonnegative_count
        ),
        "true_negative_candidate_search_nonnegative_count": int(
            true_negative_search_nonnegative_count
        ),
        "candidate_search_false_positive_rate": (
            0.0
            if search_negative_count == 0
            else round(float(search_negative_true_nonnegative_count) / float(search_negative_count), 9)
        ),
        "true_negative_candidate_search_miss_rate": (
            0.0
            if true_negative_count == 0
            else round(float(true_negative_search_nonnegative_count) / float(true_negative_count), 9)
        ),
        "candidate_search_false_positive_rows": false_positive_rows,
        "true_negative_candidate_search_miss_rows": miss_rows,
    }


def _catalog_physical_seed_columns(
    data: LunarIceData,
    *,
    seed_catalog: WorkerSeedCatalog,
    branch_context: BranchContext | None = None,
    max_columns: int,
) -> tuple[tuple[JourneyColumn, ...], dict]:
    """Rebuild worker-only candidate columns from prior hidden-negative paths."""

    max_columns = max(0, int(max_columns))
    valid_tasks = {str(task_id) for task_id in data.task_ids}
    active_branch = branch_context or BranchContext()
    rows = sorted(
        enumerate(seed_catalog.rows),
        key=lambda item: _catalog_refinement_sort_key(item[1], item[0]),
    )
    columns: list[JourneyColumn] = []
    invalid_count = 0
    infeasible_count = 0
    branch_filtered_count = 0
    duplicate_count = 0
    seen_signatures = set()
    seen_task_sets: set[tuple[str, ...]] = set()

    for _index, row in rows:
        if len(columns) >= max_columns:
            break
        raw_sequences = row.get("ordered_task_sequences") or row.get("hidden_sequence") or tuple()
        raw_path_signature = row.get("path_signature") or row.get("hidden_path_signature") or tuple()
        sequences = tuple(
            tuple(str(task_id) for task_id in sequence)
            for sequence in raw_sequences
        )
        path_signature = tuple(
            tuple(str(path_type) for path_type in path_types)
            for path_types in raw_path_signature
        )
        if not sequences or len(sequences) != len(path_signature):
            invalid_count += 1
            continue

        task_seen: set[str] = set()
        sorties = []
        invalid_row = False
        infeasible_row = False
        for sequence, path_types in zip(sequences, path_signature):
            if (
                not sequence
                or len(path_types) != len(sequence) + 1
                or any(task_id not in valid_tasks for task_id in sequence)
                or bool(task_seen.intersection(sequence))
            ):
                invalid_row = True
                break
            task_seen.update(sequence)
            try:
                sortie = build_timed_sortie(
                    data,
                    sequence,
                    path_types,
                    start_time=0.0,
                )
            except (KeyError, ValueError):
                invalid_row = True
                break
            if not sortie.feasible:
                infeasible_row = True
                break
            sorties.append(sortie)

        if invalid_row:
            invalid_count += 1
            continue
        if infeasible_row or not sorties:
            infeasible_count += 1
            continue
        try:
            column = build_journey_column(data, tuple(sorties))
        except ValueError:
            invalid_count += 1
            continue
        if not journey_satisfies_branch_context(column, active_branch):
            branch_filtered_count += 1
            continue
        signature = column_signature_from_journey(column)
        if signature in seen_signatures:
            duplicate_count += 1
            continue
        seen_signatures.add(signature)
        task_set = tuple(sorted(str(task_id) for task_id in column.task_set))
        seen_task_sets.add(task_set)
        columns.append(column)

    payload = {
        "hidden_negative_physical_seed_enabled": True,
        "hidden_negative_physical_seed_catalog_row_count": len(seed_catalog.rows),
        "hidden_negative_physical_seed_column_count": len(columns),
        "hidden_negative_physical_seed_invalid_count": invalid_count,
        "hidden_negative_physical_seed_infeasible_count": infeasible_count,
        "hidden_negative_physical_seed_branch_filtered_count": branch_filtered_count,
        "hidden_negative_physical_seed_duplicate_count": duplicate_count,
        "hidden_negative_physical_seed_task_sets": [list(row) for row in sorted(seen_task_sets)],
        "hidden_negative_physical_seed_start_time_assumption": 0.0,
        "hidden_negative_physical_seed_mutates_certificate": False,
        "hidden_negative_physical_seed_certificate_role": "worker_candidate_search_only",
        "hidden_negative_physical_seed_can_certify_no_negative": False,
    }
    return tuple(columns), payload


def _worker_generated_task_sets(pricing_payload: dict) -> list[list[str]]:
    rows: list[tuple[str, ...]] = []
    actual_keys = (
        "worker_generated_column_task_sets",
        "worker_seen_task_sets",
        "seen_task_sets",
    )
    for key in actual_keys:
        raw_rows = pricing_payload.get(key) or ()
        for raw in raw_rows:
            normalized = _normalize_task_set_row(raw)
            if normalized:
                rows.append(normalized)
    if rows:
        return [list(row) for row in _dedupe_task_set_rows(rows)]

    # Backward-compatible fallback for older payloads that did not separate
    # actual generated column task sets from candidate universes.
    for key in ("generated_task_sets", "active_seed_task_sets", "candidate_sets"):
        raw_rows = pricing_payload.get(key) or ()
        for raw in raw_rows:
            normalized = _normalize_task_set_row(raw)
            if normalized:
                rows.append(normalized)
    for summary in pricing_payload.get("candidate_summaries") or ():
        if isinstance(summary, dict):
            normalized = _normalize_task_set_row(summary.get("candidate_task_ids") or ())
            if normalized:
                rows.append(normalized)
    return [list(row) for row in _dedupe_task_set_rows(rows)]


def _worker_seen_task_sets(pricing_payload: dict, priced_columns: Iterable[JourneyColumn]) -> list[list[str]]:
    rows = [tuple(row) for row in _worker_generated_task_sets(pricing_payload)]
    for column in priced_columns:
        normalized = _normalize_task_set_row(column.task_set)
        if normalized:
            rows.append(normalized)
    return [list(row) for row in _dedupe_task_set_rows(rows)]


def _normalize_task_set_row(raw: object) -> tuple[str, ...]:
    if raw is None:
        return tuple()
    try:
        return tuple(sorted({str(task_id) for task_id in raw if str(task_id)}))
    except TypeError:
        return tuple()


def _dedupe_task_set_rows(rows: Iterable[Iterable[str]]) -> tuple[tuple[str, ...], ...]:
    seen: set[tuple[str, ...]] = set()
    result: list[tuple[str, ...]] = []
    for row in rows:
        normalized = _normalize_task_set_row(row)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return tuple(result)


def _task_set_count_by_size(rows: Iterable[Iterable[str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in _dedupe_task_set_rows(rows):
        key = str(len(row))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _duals_from_reduced_cost_context(context) -> JourneyDuals:
    return JourneyDuals(
        cover={str(key): float(value) for key, value in getattr(context, "task_duals", {}).items()},
        fleet_limit=float(getattr(context, "fleet_dual", 0.0)),
        cuts={str(key): float(value) for key, value in getattr(context, "cut_duals", {}).items()},
    )


def _dual_context_payload(context) -> dict:
    """Serialize current true RMP duals for downstream exact proof probes."""

    if context is None:
        return {}
    return {
        "dual_source": "master.reduced_cost_context",
        "dual_fingerprint": str(getattr(context, "dual_fingerprint", "") or ""),
        "rmp_iteration_id": str(getattr(context, "rmp_iteration_id", "") or ""),
        "fleet_dual": float(getattr(context, "fleet_dual", 0.0)),
        "task_duals": {
            str(key): float(value)
            for key, value in getattr(context, "task_duals", {}).items()
        },
        "cut_duals": {
            str(key): float(value)
            for key, value in getattr(context, "cut_duals", {}).items()
        },
    }


def _tail_dual_history_with_current(
    history: list[JourneyDuals],
    context,
    *,
    window: int,
) -> tuple[JourneyDuals, ...]:
    current = _duals_from_reduced_cost_context(context)
    return tuple((list(history) + [current])[-max(1, int(window)) :])


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
    configured_cap = _env_int(
        LABELING_WORKER_MAX_TASK_CAP_ENV,
        default=3,
        minimum=1,
        maximum=max(1, int(data.max_tasks_per_trip)),
    )
    return max(
        1,
        min(
            int(max_direct_tasks),
            int(data.max_tasks_per_trip),
            int(configured_cap),
            len(data.task_ids) - 1,
        ),
    )


def _adaptive_labeling_final_judge_exact_harvest_target(
    target: int | None,
    *,
    active_task_set_count: int,
) -> int | None:
    """Use large early harvests, then shrink batches as distinct new sets get sparse."""

    if target is None:
        raw_target = os.environ.get("LUNAR_ICE_LABELING_FINAL_JUDGE_EXACT_HARVEST_TARGET")
        if raw_target in (None, ""):
            return None
        try:
            target = int(str(raw_target))
        except ValueError:
            return None
    value = max(1, int(target))
    active_count = max(0, int(active_task_set_count))
    for threshold, cap in _labeling_final_judge_adaptive_harvest_schedule():
        if active_count >= threshold:
            return min(value, cap)
    return value


def _labeling_final_judge_pass_policy() -> str:
    value = str(
        os.environ.get(
            LABELING_FINAL_JUDGE_PASS_POLICY_ENV,
            LABELING_FINAL_JUDGE_PASS_POLICY_LEGACY,
        )
        or ""
    ).strip().lower()
    if value not in LABELING_FINAL_JUDGE_PASS_POLICIES:
        raise ValueError(
            f"unsupported {LABELING_FINAL_JUDGE_PASS_POLICY_ENV}={value!r}; "
            f"expected one of {sorted(LABELING_FINAL_JUDGE_PASS_POLICIES)!r}"
        )
    return value


def _effective_labeling_final_judge_pass_policy(
    configured_policy: str,
    *,
    branch_context_active: bool,
) -> str:
    if str(configured_policy) == LABELING_FINAL_JUDGE_PASS_POLICY_BRANCH_ADAPTIVE:
        return (
            LABELING_FINAL_JUDGE_PASS_POLICY_ADAPTIVE
            if branch_context_active
            else LABELING_FINAL_JUDGE_PASS_POLICY_LEGACY
        )
    return str(configured_policy)


def _initial_labeling_final_judge_pass_strategy(policy: str) -> str:
    if str(policy) == LABELING_FINAL_JUDGE_PASS_POLICY_PROOF_ONLY:
        return LABELING_FINAL_JUDGE_PASS_PROOF_ONLY
    return LABELING_FINAL_JUDGE_PASS_HARVEST_THEN_PROOF


def _adaptive_final_judge_harvest_cap_sec(policy: str) -> float | None:
    if str(policy) != LABELING_FINAL_JUDGE_PASS_POLICY_ADAPTIVE:
        return None
    raw = os.environ.get(LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_CAP_SEC_ENV)
    if raw is None or not str(raw).strip():
        return None
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(
            f"invalid {LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_CAP_SEC_ENV}={raw!r}"
        ) from exc
    if not isfinite(value) or value <= 0.0:
        raise ValueError(
            f"{LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_CAP_SEC_ENV} "
            "must be a finite positive number"
        )
    return value


def _next_labeling_final_judge_pass_strategy(
    policy: str,
    judge_payload: Mapping[str, object],
    *,
    max_columns_per_round: int,
    effective_harvest_target: int | None,
) -> str:
    """Choose the next pass without changing proof or column-audit semantics.

    The native harvest pass is valuable while it fills its requested batch.
    Once it returns a sparse batch, the next RMP dual is sent directly to the
    exhaustive proof pass, avoiding another bounded harvest that is unlikely
    to fill.  A proof pass that exposes at least one full master batch switches
    back to harvest for the next dual; a sparse proof stays proof-only.
    """

    normalized_policy = str(policy)
    if normalized_policy == LABELING_FINAL_JUDGE_PASS_POLICY_PROOF_ONLY:
        return LABELING_FINAL_JUDGE_PASS_PROOF_ONLY
    if normalized_policy != LABELING_FINAL_JUDGE_PASS_POLICY_ADAPTIVE:
        return LABELING_FINAL_JUDGE_PASS_HARVEST_THEN_PROOF

    proof_attempted = bool(judge_payload.get("labeling_final_judge_proof_pass_attempted"))
    negative_count = int(
        judge_payload.get("manual_branch_feasible_negative_count")
        or judge_payload.get("true_negative_column_count")
        or 0
    )
    if proof_attempted:
        return (
            LABELING_FINAL_JUDGE_PASS_HARVEST_THEN_PROOF
            if negative_count >= max(1, int(max_columns_per_round))
            else LABELING_FINAL_JUDGE_PASS_PROOF_ONLY
        )

    harvest_count = int(
        judge_payload.get("labeling_final_judge_harvest_pass_column_count") or 0
    )
    target = max(
        1,
        int(
            effective_harvest_target
            if effective_harvest_target is not None
            else judge_payload.get("labeling_final_judge_exact_harvest_target")
            or 1
        ),
    )
    return (
        LABELING_FINAL_JUDGE_PASS_HARVEST_THEN_PROOF
        if harvest_count >= target
        else LABELING_FINAL_JUDGE_PASS_PROOF_ONLY
    )


def _labeling_final_judge_adaptive_harvest_schedule() -> tuple[tuple[int, int], ...]:
    raw = os.environ.get(LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE_ENV)
    if raw is not None:
        raw_text = str(raw).strip()
        if raw_text.lower() in {"", "0", "off", "none", "disabled", "false"}:
            return tuple()
        rows: list[tuple[int, int]] = []
        for piece in raw_text.split(","):
            text = piece.strip()
            if not text or ":" not in text:
                continue
            threshold_text, cap_text = text.split(":", 1)
            try:
                threshold = max(0, int(threshold_text.strip()))
                cap = max(1, int(cap_text.strip()))
            except ValueError:
                continue
            rows.append((threshold, cap))
        if rows:
            return tuple(sorted(rows, key=lambda row: row[0], reverse=True))
        return tuple()
    return ((4000, 128), (3000, 256))


def _worker_ng_sizes(worker_task_cap: int) -> tuple[int, ...]:
    cap = max(1, int(worker_task_cap))
    raw = os.environ.get(LABELING_WORKER_NG_SIZES_ENV)
    if not raw:
        return (3, 5, 8)
    sizes: list[int] = []
    seen: set[int] = set()
    for piece in str(raw).split(","):
        text = piece.strip()
        if not text:
            continue
        try:
            value = int(text)
        except ValueError:
            continue
        value = max(1, min(cap, value))
        if value in seen:
            continue
        seen.add(value)
        sizes.append(value)
    if not sizes:
        sizes = [cap]
    if sizes[-1] != cap and cap not in seen:
        sizes.append(cap)
    return tuple(sizes)


def _run_large_task_direct_worker(
    data: LunarIceData,
    *,
    worker_duals: JourneyDuals,
    true_duals: JourneyDuals,
    master_columns: tuple[JourneyColumn, ...],
    b0_direct,
    support_task_sets: tuple[tuple[str, ...], ...],
    worker_task_cap: int,
    max_direct_tasks: int,
    max_candidate_sets: int,
    negative_eps: float,
    branch_context: BranchContext | None,
    cut_context: CutContext,
    deadline: float | None,
) -> tuple[dict, tuple[JourneyColumn, ...]]:
    enabled = _env_bool(LARGE_TASK_DIRECT_WORKER_ENV, default=False)
    large_cap = _env_int(
        LARGE_TASK_DIRECT_WORKER_MAX_TASKS_ENV,
        default=min(12, int(max_direct_tasks), int(data.max_tasks_per_trip)),
        minimum=1,
        maximum=max(1, min(int(max_direct_tasks), int(data.max_tasks_per_trip), len(data.task_ids))),
    )
    candidate_cap = _env_int(
        LARGE_TASK_DIRECT_WORKER_MAX_CANDIDATE_SETS_ENV,
        default=160,
        minimum=0,
        maximum=10000,
    )
    time_cap = _env_float(
        LARGE_TASK_DIRECT_WORKER_TIME_CAP_SEC_ENV,
        default=0.0,
        minimum=0.0,
        maximum=3600.0,
    )
    neighborhood_width = _env_int(
        LARGE_TASK_DIRECT_WORKER_NEIGHBORHOOD_WIDTH_ENV,
        default=4,
        minimum=1,
        maximum=100,
    )
    min_task_count = max(1, int(worker_task_cap) + 1)
    base_payload = {
        "large_task_direct_worker_enabled": bool(enabled),
        "large_task_direct_worker_can_certify_no_negative": False,
        "large_task_direct_worker_no_column_can_certify": False,
        "large_task_direct_worker_mutates_certificate": False,
        "large_task_direct_worker_pricing_proof_kind": "DIRECT_LARGE_TASK_WORKER_UNCERTIFIED",
        "large_task_direct_worker_min_tasks": int(min_task_count),
        "large_task_direct_worker_max_tasks": int(large_cap),
        "large_task_direct_worker_max_candidate_sets": int(candidate_cap),
        "large_task_direct_worker_time_cap_sec": float(time_cap),
        "large_task_direct_worker_neighborhood_width": int(neighborhood_width),
    }
    if not enabled:
        return {**base_payload, "large_task_direct_worker_skip_reason": "disabled"}, tuple()
    if large_cap < min_task_count:
        return {**base_payload, "large_task_direct_worker_skip_reason": "cap_not_above_labeling_worker"}, tuple()
    remaining = None if deadline is None else max(0.0, float(deadline) - perf_counter())
    if remaining is not None and remaining <= 1.0:
        return {**base_payload, "large_task_direct_worker_skip_reason": "worker_deadline_exhausted"}, tuple()
    if time_cap <= 0.0 or candidate_cap <= 0:
        return {**base_payload, "large_task_direct_worker_skip_reason": "nonpositive_budget"}, tuple()

    seeds, source_rows = _large_task_direct_worker_seed_task_sets(
        data,
        duals=worker_duals,
        master_columns=master_columns,
        b0_direct=b0_direct,
        support_task_sets=support_task_sets,
        min_task_count=min_task_count,
        max_task_count=large_cap,
        max_seed_sets=candidate_cap,
        neighborhood_width=neighborhood_width,
    )
    if not seeds:
        return {**base_payload, "large_task_direct_worker_skip_reason": "no_seed_task_sets"}, tuple()
    run_time_cap = min(float(time_cap), remaining) if remaining is not None else float(time_cap)
    start = perf_counter()
    pricing, columns = price_direct_journey_columns_incremental(
        data,
        worker_duals,
        negative_eps=negative_eps,
        max_direct_tasks=large_cap,
        seed_task_sets=seeds,
        max_candidate_sets=len(seeds),
        wall_time_limit_sec=run_time_cap,
        stop_at_first_negative=False,
        completion_bound_enabled=True,
        branch_context=branch_context,
        cut_context=cut_context,
    )
    true_negative_count = 0
    for column in columns:
        if (
            manual_journey_reduced_cost(
                column,
                true_duals,
                cut_coefficients=cut_context.coefficients_for(column),
            )
            < -abs(float(negative_eps))
        ):
            true_negative_count += 1
    payload = {
        **base_payload,
        "large_task_direct_worker_skip_reason": "",
        "large_task_direct_worker_wall_time": round(perf_counter() - start, 6),
        "large_task_direct_worker_dual_source": "tail_dual_stabilized_worker_dual_or_true_worker_dual",
        "large_task_direct_worker_official_dual_source": "current_true_rmp_dual_reaudit_required",
        "large_task_direct_worker_seed_count": len(seeds),
        "large_task_direct_worker_seed_task_count_counts": _task_set_count_by_size(seeds),
        "large_task_direct_worker_seed_task_sets": [list(row) for row in seeds],
        "large_task_direct_worker_seed_source_rows": source_rows,
        "large_task_direct_worker_status": pricing.get("status") or "",
        "large_task_direct_worker_pricing_state": pricing.get("pricing_state") or "",
        "large_task_direct_worker_candidate_round_count": int(pricing.get("candidate_round_count") or 0),
        "large_task_direct_worker_candidate_round_limit": int(pricing.get("candidate_round_limit") or len(seeds)),
        "large_task_direct_worker_sortie_template_count": int(
            pricing.get("feasible_sortie_template_count") or 0
        ),
        "large_task_direct_worker_pareto_label_count": int(pricing.get("pareto_label_count") or 0),
        "large_task_direct_worker_column_count": len(columns),
        "large_task_direct_worker_true_negative_count": int(true_negative_count),
        "large_task_direct_worker_candidate_search_best_reduced_cost": pricing.get("best_reduced_cost"),
        "large_task_direct_worker_candidate_search_negative_count": int(
            pricing.get("negative_column_count") or 0
        ),
        "large_task_direct_worker_timeout_stage": pricing.get("timeout_stage") or "",
        "large_task_direct_worker_pricing_timeout": str(pricing.get("status") or "").endswith("TIME_LIMIT"),
    }
    return payload, tuple(columns)


def _large_task_direct_worker_seed_task_sets(
    data: LunarIceData,
    *,
    duals: JourneyDuals,
    master_columns: tuple[JourneyColumn, ...],
    b0_direct,
    support_task_sets: Iterable[Iterable[str]],
    min_task_count: int,
    max_task_count: int,
    max_seed_sets: int,
    neighborhood_width: int,
) -> tuple[tuple[tuple[str, ...], ...], list[dict]]:
    valid_tasks = {str(task_id) for task_id in data.task_ids}
    if not valid_tasks or int(max_seed_sets) <= 0:
        return tuple(), []
    min_size = max(1, int(min_task_count))
    max_size = max(min_size, min(int(max_task_count), int(data.max_tasks_per_trip), len(valid_tasks)))
    width = max(1, int(neighborhood_width))
    scored: dict[tuple[str, ...], tuple[tuple, set[str]]] = {}

    def add(row: Iterable[str], *, source: str, priority: int) -> None:
        normalized = tuple(sorted({str(task_id) for task_id in row if str(task_id) in valid_tasks}))
        if len(normalized) < min_size or len(normalized) > max_size:
            return
        score = (
            int(priority),
            -sum(float(duals.cover.get(task_id, 0.0)) for task_id in normalized),
            -len(normalized),
            _task_set_spread(data, normalized),
            normalized,
        )
        old = scored.get(normalized)
        if old is None or score < old[0]:
            scored[normalized] = (score, {str(source)})
        else:
            old[1].add(str(source))

    def add_projected(row: Iterable[str], *, source: str, priority: int) -> None:
        normalized = tuple(sorted({str(task_id) for task_id in row if str(task_id) in valid_tasks}))
        if not normalized:
            return
        if len(normalized) <= max_size:
            add(normalized, source=source, priority=priority)
            return
        for projection in _project_large_task_set_for_direct_worker(
            data,
            duals,
            normalized,
            max_task_count=max_size,
            neighborhood_width=width,
        ):
            add(projection, source=f"{source}_projection", priority=priority)

    ranked_tasks = tuple(
        task_id
        for task_id in sorted(
            valid_tasks,
            key=lambda task_id: (
                -float(duals.cover.get(task_id, 0.0)),
                -float(data.tasks[task_id].science_weight),
                task_id,
            ),
        )
    )
    support_rows = _dedupe_task_set_rows(
        tuple(str(task_id) for task_id in row)
        for row in (
            *tuple(column.task_set for column in master_columns),
            *tuple(getattr(column, "task_set", tuple()) for column in getattr(b0_direct, "journeys", tuple()) or tuple()),
            *tuple(support_task_sets or tuple()),
        )
    )
    for row in support_rows:
        add_projected(row, source="large_task_support", priority=0)
        _add_large_task_neighbors(
            data,
            duals,
            row,
            add=add,
            source="large_task_support_neighborhood",
            priority=1,
            min_task_count=min_size,
            max_task_count=max_size,
            neighborhood_width=width,
        )

    for size in range(min_size, max_size + 1):
        add(ranked_tasks[:size], source="large_task_dual_prefix", priority=2)
    for start in range(0, len(ranked_tasks), max(1, max_size)):
        for size in range(min_size, max_size + 1):
            chunk = ranked_tasks[start : start + size]
            if len(chunk) == size:
                add(chunk, source="large_task_dual_chunk", priority=3)

    anchor_count = min(len(ranked_tasks), max(width * 2, max_size))
    for anchor in ranked_tasks[:anchor_count]:
        nearest = tuple(
            task_id
            for task_id in sorted(
                (task_id for task_id in valid_tasks if task_id != anchor),
                key=lambda task_id: (
                    _task_xy_distance_for_solver(data, anchor, task_id),
                    -float(duals.cover.get(task_id, 0.0)),
                    -float(data.tasks[task_id].science_weight),
                    task_id,
                ),
            )
        )
        for size in range(min_size, max_size + 1):
            add((anchor, *nearest[: size - 1]), source="large_task_spatial_cluster", priority=4)

    ordered = tuple(row for row, _value in sorted(scored.items(), key=lambda item: item[1][0]))
    selected = ordered[: max(0, int(max_seed_sets))]
    source_rows = [
        {"task_set": list(row), "sources": sorted(scored[row][1])}
        for row in selected
    ]
    return selected, source_rows


def _add_large_task_neighbors(
    data: LunarIceData,
    duals: JourneyDuals,
    base: Iterable[str],
    *,
    add,
    source: str,
    priority: int,
    min_task_count: int,
    max_task_count: int,
    neighborhood_width: int,
) -> None:
    base_tuple = _normalize_task_set_row(base)
    if not base_tuple:
        return
    base_set = set(base_tuple)
    inside_by_low_dual = sorted(
        base_tuple,
        key=lambda task_id: (
            float(duals.cover.get(task_id, 0.0)),
            float(data.tasks[task_id].science_weight),
            task_id,
        ),
    )
    outside = tuple(
        task_id
        for task_id in sorted(
            (str(task_id) for task_id in data.task_ids if str(task_id) not in base_set),
            key=lambda task_id: (
                _min_distance_to_task_set(data, task_id, base_set),
                -float(duals.cover.get(task_id, 0.0)),
                -float(data.tasks[task_id].science_weight),
                task_id,
            ),
        )
    )[: max(1, int(neighborhood_width))]
    if len(base_tuple) > int(min_task_count):
        for removed in inside_by_low_dual[: max(1, int(neighborhood_width))]:
            add((task_id for task_id in base_tuple if task_id != removed), source=source, priority=priority)
    if len(base_tuple) < int(max_task_count):
        for task_id in outside:
            add((*base_tuple, task_id), source=source, priority=priority)
    for removed in inside_by_low_dual[: max(1, int(neighborhood_width))]:
        reduced = tuple(task_id for task_id in base_tuple if task_id != removed)
        for task_id in outside:
            add((*reduced, task_id), source=source, priority=priority)


def _project_large_task_set_for_direct_worker(
    data: LunarIceData,
    duals: JourneyDuals,
    task_set: Iterable[str],
    *,
    max_task_count: int,
    neighborhood_width: int,
) -> tuple[tuple[str, ...], ...]:
    row = _normalize_task_set_row(task_set)
    if not row:
        return tuple()
    cap = max(1, min(int(max_task_count), len(row)))
    if len(row) <= cap:
        return (row,)
    ranked = tuple(
        task_id
        for task_id in sorted(
            row,
            key=lambda task_id: (
                -float(duals.cover.get(task_id, 0.0)),
                -float(data.tasks[task_id].science_weight),
                task_id,
            ),
        )
    )
    projections: list[tuple[str, ...]] = [tuple(sorted(ranked[:cap]))]
    for anchor in ranked[: max(1, int(neighborhood_width))]:
        nearest = tuple(
            task_id
            for task_id in sorted(
                (task_id for task_id in row if task_id != anchor),
                key=lambda task_id: (
                    _task_xy_distance_for_solver(data, anchor, task_id),
                    -float(duals.cover.get(task_id, 0.0)),
                    -float(data.tasks[task_id].science_weight),
                    task_id,
                ),
            )
        )
        projections.append(tuple(sorted((anchor, *nearest[: cap - 1]))))
    return _dedupe_task_set_rows(projections)


def _task_xy_distance_for_solver(data: LunarIceData, left: str, right: str) -> float:
    left_xy = data.tasks[str(left)].xy_km
    right_xy = data.tasks[str(right)].xy_km
    return ((left_xy[0] - right_xy[0]) ** 2 + (left_xy[1] - right_xy[1]) ** 2) ** 0.5


def _task_set_spread(data: LunarIceData, row: Iterable[str]) -> float:
    tasks = tuple(str(task_id) for task_id in row)
    if len(tasks) <= 1:
        return 0.0
    total = 0.0
    count = 0
    for index, left in enumerate(tasks):
        for right in tasks[index + 1 :]:
            total += _task_xy_distance_for_solver(data, left, right)
            count += 1
    return total / max(1, count)


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

    # DSSR-style refinement seeds from prior hidden-negative audits must survive
    # the bounded worker budget. They are worker-only candidate search hints.
    for row in _catalog_refinement_seed_portfolio(
        data,
        duals=duals,
        seed_catalog=seed_catalog,
        max_direct_tasks=max_direct_tasks,
        max_seed_sets=max_seed_sets,
    ):
        add(row)
    if len(data.task_ids) <= 5:
        add(tuple(ranked[: min(int(max_direct_tasks), len(ranked))]))
    for column in tuple(getattr(b0_direct, "journeys", tuple()) or tuple()):
        add(tuple(sorted(column.task_set)))
    for column in master_columns:
        add(tuple(sorted(column.task_set)))
    for size in range(1, max_size + 1):
        for combo in combinations(ranked[: max(int(max_direct_tasks) + 3, max_size)], size):
            add(combo)
    return tuple(rows[: max(1, int(max_seed_sets))])


def _catalog_refinement_seed_task_sets(
    data: LunarIceData,
    *,
    seed_catalog: WorkerSeedCatalog,
    max_direct_tasks: int,
) -> tuple[tuple[str, ...], ...]:
    all_tasks = {str(task_id) for task_id in data.task_ids}
    rows: list[tuple[tuple, tuple[str, ...]]] = []
    for index, row in enumerate(seed_catalog.rows):
        raw = row.get("task_set") or tuple()
        normalized = tuple(sorted(str(task_id) for task_id in raw if str(task_id) in all_tasks))
        if normalized and len(normalized) <= int(max_direct_tasks):
            rows.append((_catalog_refinement_sort_key(row, index), normalized))
    rows.sort(key=lambda item: item[0])
    return _dedupe_task_set_rows(row for _key, row in rows)


def _catalog_refinement_seed_portfolio(
    data: LunarIceData,
    *,
    duals: JourneyDuals,
    seed_catalog: WorkerSeedCatalog,
    max_direct_tasks: int,
    max_seed_sets: int,
) -> tuple[tuple[str, ...], ...]:
    limit = max(0, int(max_seed_sets))
    if limit == 0:
        return tuple()
    base_rows = _catalog_refinement_seed_task_sets(
        data,
        seed_catalog=seed_catalog,
        max_direct_tasks=max_direct_tasks,
    )
    expanded_rows = _catalog_refinement_neighborhood_seed_task_sets(
        data,
        duals=duals,
        seed_catalog=seed_catalog,
        max_direct_tasks=max_direct_tasks,
    )
    if not base_rows:
        return tuple(expanded_rows[:limit])

    result: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()

    def add(row: tuple[str, ...]) -> bool:
        if not row or row in seen or len(result) >= limit:
            return False
        seen.add(row)
        result.append(row)
        return True

    first_base = base_rows[0]
    add(first_base)
    if len(result) < limit:
        first_expansion = _first_refinement_expansion_for_base(first_base, expanded_rows)
        if first_expansion is not None:
            add(first_expansion)

    for row in base_rows:
        add(row)
        if len(result) >= limit:
            return tuple(result)
    for row in expanded_rows:
        add(row)
        if len(result) >= limit:
            return tuple(result)
    return tuple(result)


def _first_refinement_expansion_for_base(
    base: tuple[str, ...],
    expanded_rows: Iterable[tuple[str, ...]],
) -> tuple[str, ...] | None:
    base_set = set(base)
    for row in expanded_rows:
        if base_set.issubset(set(row)) and tuple(row) != tuple(base):
            return tuple(row)
    return None


def _catalog_refinement_sort_key(row: dict, index: int) -> tuple:
    match = str(row.get("worker_priced_candidate_source_match") or "none")
    match_priority = {
        "none": 0,
        "superset": 1,
        "exact": 2,
    }.get(match, 3)
    miss_reason = str(row.get("miss_reason") or "unknown")
    miss_priority = {
        "worker_not_generated": 0,
        "pricing_timeout_only": 1,
        "pruned_by_task_bound": 2,
        "pruned_by_resource_bound": 3,
        "pruned_by_dominance": 4,
        "duplicate_filtered": 5,
        "reduced_cost_mismatch": 6,
        "unknown": 7,
    }.get(miss_reason, 8)
    try:
        true_rc = float(row.get("true_reduced_cost"))
    except (TypeError, ValueError):
        true_rc = 0.0
    return (match_priority, miss_priority, true_rc, int(index))


def _catalog_refinement_source_match_counts(seed_catalog: WorkerSeedCatalog) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in seed_catalog.rows:
        key = str(row.get("worker_priced_candidate_source_match") or "none")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _hidden_negative_refinement_summary(
    hidden_audit: dict | None,
    seed_catalog: WorkerSeedCatalog | None,
) -> dict:
    audit = hidden_audit or {}
    catalog = seed_catalog or WorkerSeedCatalog()
    catalog_counts = _catalog_refinement_coverage_counts(catalog)
    catalog_exact = int(catalog_counts.get("exact") or 0)
    catalog_superset = int(catalog_counts.get("superset") or 0)
    catalog_uncovered = int(catalog_counts.get("uncovered") or 0)
    return {
        "hidden_negative_refinement_coverage_counts": audit.get(
            "hidden_negative_refinement_coverage_counts"
        )
        or {},
        "hidden_negative_refinement_exact_count": int(
            audit.get("hidden_negative_refinement_exact_count") or 0
        ),
        "hidden_negative_refinement_superset_count": int(
            audit.get("hidden_negative_refinement_superset_count") or 0
        ),
        "hidden_negative_refinement_covered_count": int(
            audit.get("hidden_negative_refinement_covered_count") or 0
        ),
        "hidden_negative_refinement_uncovered_count": int(
            audit.get("hidden_negative_refinement_uncovered_count") or 0
        ),
        "hidden_negative_refinement_catalog_coverage_counts": catalog_counts,
        "hidden_negative_refinement_catalog_exact_count": catalog_exact,
        "hidden_negative_refinement_catalog_superset_count": catalog_superset,
        "hidden_negative_refinement_catalog_covered_count": catalog_exact + catalog_superset,
        "hidden_negative_refinement_catalog_uncovered_count": catalog_uncovered,
        "hidden_negative_refinement_catalog_seed_count": len(catalog.rows),
        "hidden_negative_refinement_coverage_diagnostic_only": True,
    }


def _catalog_refinement_coverage_counts(seed_catalog: WorkerSeedCatalog) -> dict[str, int]:
    counts = {"exact": 0, "superset": 0, "uncovered": 0}
    for row in seed_catalog.rows:
        match = str(row.get("worker_priced_candidate_source_match") or "none")
        sources = tuple(str(source) for source in row.get("worker_priced_candidate_seed_sources") or tuple())
        from_refinement = any(source.startswith("hidden_negative_refinement") for source in sources)
        if from_refinement and match in {"exact", "superset"}:
            counts[match] += 1
        else:
            counts["uncovered"] += 1
    return {key: value for key, value in counts.items() if value > 0}


def _catalog_refinement_neighborhood_seed_task_sets(
    data: LunarIceData,
    *,
    duals: JourneyDuals,
    seed_catalog: WorkerSeedCatalog,
    max_direct_tasks: int,
    expansion_width: int = 2,
) -> tuple[tuple[str, ...], ...]:
    base_rows = _catalog_refinement_seed_task_sets(
        data,
        seed_catalog=seed_catalog,
        max_direct_tasks=max_direct_tasks,
    )
    if not base_rows:
        return tuple()
    all_tasks = tuple(sorted(str(task_id) for task_id in data.task_ids))
    rows: list[tuple[str, ...]] = []
    for base in base_rows:
        base_set = set(base)
        if len(base_set) >= int(max_direct_tasks):
            continue
        candidates = sorted(
            (task_id for task_id in all_tasks if task_id not in base_set),
            key=lambda task_id: (
                _min_distance_to_task_set(data, task_id, base_set),
                -float(duals.cover.get(task_id, 0.0)),
                -float(data.tasks[task_id].science_weight),
                task_id,
            ),
        )
        for task_id in candidates[: max(0, int(expansion_width))]:
            expanded = tuple(sorted((*base, task_id)))
            if len(expanded) <= int(max_direct_tasks):
                rows.append(expanded)
    return _dedupe_task_set_rows(rows)


def _refinement_seed_source_rows(
    *,
    refinement_seed_task_sets: Iterable[Iterable[str]],
    refinement_expanded_seed_task_sets: Iterable[Iterable[str]],
) -> tuple[dict, ...]:
    rows: dict[tuple[str, ...], list[str]] = {}
    for task_set in _dedupe_task_set_rows(refinement_seed_task_sets):
        rows.setdefault(task_set, []).append("hidden_negative_refinement")
    for task_set in _dedupe_task_set_rows(refinement_expanded_seed_task_sets):
        sources = rows.setdefault(task_set, [])
        if "hidden_negative_refinement_expansion" not in sources:
            sources.append("hidden_negative_refinement_expansion")
    return tuple(
        {"task_set": list(task_set), "sources": sources}
        for task_set, sources in sorted(rows.items())
    )


def _min_distance_to_task_set(data: LunarIceData, task_id: str, task_set: set[str]) -> float:
    if not task_set:
        return 0.0
    xy = data.tasks[str(task_id)].xy_km
    return min(
        ((xy[0] - data.tasks[str(other)].xy_km[0]) ** 2 + (xy[1] - data.tasks[str(other)].xy_km[1]) ** 2) ** 0.5
        for other in task_set
    )


def _count_task_set_intersection(
    left: Iterable[Iterable[str]],
    right: Iterable[Iterable[str]],
) -> int:
    right_set = set(_dedupe_task_set_rows(right))
    return sum(1 for row in _dedupe_task_set_rows(left) if row in right_set)


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


def _load_columns(
    pool: ColumnPool,
    view: MasterColumnView,
    columns: Iterable[JourneyColumn],
    *,
    cut_context: CutContext | None = None,
) -> None:
    _load_columns_for_node(pool, view, columns, node_id="root", branch_context=None, cut_context=cut_context)


def _recover_branch_rmp_with_phase_one(
    data: LunarIceData,
    *,
    pool: ColumnPool,
    view: MasterColumnView,
    node_id: str,
    branch_context: BranchContext,
    cut_context: CutContext,
    max_rounds: int,
    max_columns_per_round: int,
    negative_eps: float,
    wall_time_limit_sec: float | None,
) -> dict:
    """Restore a branch RMP basis or prove full-master infeasibility."""

    started_at = perf_counter()
    history: list[dict] = []
    backend_id = str(
        os.getenv("LUNAR_ICE_SPPRC_EXACT_BACKEND", DEFAULT_EXACT_BACKEND_ID)
    )
    if backend_id == "python_reference":
        return {
            "status": "UNSUPPORTED_BACKEND",
            "backend_id": backend_id,
            "history": history,
            "certificate_valid": False,
            "note": "Python reference Phase-I objective is not implemented; fail closed.",
        }
    if not cut_context.empty:
        return {
            "status": "UNSUPPORTED_CUT_CONTEXT",
            "backend_id": backend_id,
            "history": history,
            "certificate_valid": False,
            "note": "Native Phase-I v1 requires empty CutContext.",
        }

    last_phase = None
    phase_one_negative_eps = min(abs(float(negative_eps)), 1.0e-9)
    for phase_round in range(1, max(1, int(max_rounds)) + 1):
        remaining = _remaining_wall_time_limit(
            wall_time_limit_sec,
            started_at=started_at,
        )
        if remaining is not None and remaining <= 0.0:
            return {
                "status": "TIME_LIMIT",
                "backend_id": backend_id,
                "history": history,
                "certificate_valid": False,
                "note": "Phase-I exhausted the node wall-time budget.",
            }
        master_columns = _master_columns(pool, view, node_id=node_id)
        phase = solve_phase_one_journey_rmp(
            data.task_ids,
            master_columns,
            fleet_size=data.fleet_size,
            branch_context=branch_context,
            cut_context=cut_context,
        )
        last_phase = phase
        phase_row = {
            "round": phase_round,
            "phase_one_status": phase.status,
            "artificial_objective": phase.artificial_objective,
            "artificial_positive_count": phase.artificial_positive_count,
            "active_column_count": len(master_columns),
            "pricing_called": False,
            "added_column_count": 0,
        }
        if phase.status != "PHASE_ONE_OPTIMAL":
            history.append(phase_row)
            return {
                "status": "RMP_NOT_OPTIMAL",
                "backend_id": backend_id,
                "history": history,
                "certificate_valid": False,
                "note": phase.note,
            }
        if phase.feasible_without_artificials:
            history.append(phase_row)
            return {
                "status": "RMP_FEASIBILITY_RESTORED",
                "backend_id": backend_id,
                "history": history,
                "certificate_valid": False,
                "artificial_objective": phase.artificial_objective,
                "note": "Phase-I artificial objective reached zero; solve the official RMP next.",
            }

        result = BackendRegistry.create(backend_id).solve(
            BackendPricingRequest(
                data=data,
                true_duals=phase.duals,
                mode=BACKEND_MODE_EXACT_PROOF,
                objective_mode=BACKEND_OBJECTIVE_PHASE_ONE,
                branch_context=branch_context,
                cut_context=cut_context,
                harvest_target=max(1, int(max_columns_per_round)),
                wall_time_limit_sec=remaining,
                negative_eps=phase_one_negative_eps,
            )
        )
        phase_row.update(
            {
                "pricing_called": True,
                "engine_status": result.engine_status,
                "search_exhaustive": result.search_exhaustive,
                "frontier_empty": result.frontier_empty,
                "labels_dropped": result.labels_dropped,
                "best_found_rc": result.best_found_rc,
                "proved_no_rc_below": result.proved_no_rc_below,
                "certificate_blockers": list(result.certificate_blockers),
                "candidate_column_count": len(result.columns),
                "telemetry": result.telemetry,
            }
        )
        if result.columns:
            priced = sorted(
                (
                    (
                        -float(phase.duals.fleet_limit)
                        - sum(
                            float(phase.duals.cover.get(str(task_id), 0.0))
                            for task_id in column.task_set
                        ),
                        column,
                    )
                    for column in result.columns
                ),
                key=lambda row: (row[0], row[1].objective, tuple(sorted(row[1].task_set))),
            )
            selected = tuple(
                column
                for rc, column in priced
                if rc < -phase_one_negative_eps
            )[: max(1, int(max_columns_per_round))]
            added = _add_selected_to_pool_and_master(
                pool,
                view,
                selected,
                node_id=node_id,
                branch_context=branch_context,
                cut_context=cut_context,
            )
            phase_row["selected_column_count"] = len(selected)
            phase_row["added_column_count"] = int(added)
            history.append(phase_row)
            if added > 0:
                continue
            return {
                "status": "DUPLICATE_ONLY_INCOMPLETE",
                "backend_id": backend_id,
                "history": history,
                "certificate_valid": False,
                "note": "Phase-I found negative real columns but none were addable; fail closed.",
            }
        history.append(phase_row)
        if result.proved_no_rc_below is not None and result.can_enter_certificate_audit:
            return {
                "status": "NODE_INFEASIBLE_CERTIFIED",
                "backend_id": backend_id,
                "history": history,
                "certificate_valid": True,
                "artificial_objective": phase.artificial_objective,
                "artificial_positive_count": phase.artificial_positive_count,
                "phase_one_negative_eps": phase_one_negative_eps,
                "pricing_result": result.to_payload(),
                "note": (
                    "Positive Phase-I artificial objective remains and exhaustive branch-aware "
                    "pricing proved no negative real column."
                ),
            }
        return {
            "status": "PRICING_INCOMPLETE",
            "backend_id": backend_id,
            "history": history,
            "certificate_valid": False,
            "pricing_result": result.to_payload(),
            "note": "Phase-I pricing did not produce a valid no-negative certificate.",
        }

    return {
        "status": "ROUND_LIMIT",
        "backend_id": backend_id,
        "history": history,
        "certificate_valid": False,
        "artificial_objective": (
            None if last_phase is None else last_phase.artificial_objective
        ),
        "note": "Phase-I reached its round limit before restoring feasibility or proving infeasibility.",
    }


def _build_same_journey_seed_columns(
    data: LunarIceData,
    *,
    branch_context: BranchContext,
    max_direct_tasks: int,
    wall_time_limit_sec: float | None,
) -> tuple[tuple[JourneyColumn, ...], dict]:
    """Build real, audited seed columns for Ryan--Foster same components.

    A child RMP can become temporarily infeasible after inherited singleton
    columns are filtered by a same-journey decision.  This helper restores only
    a starting basis.  It never certifies feasibility or infeasibility; the
    regular branch-aware exact pricer remains the sole certificate source.
    """

    started_at = perf_counter()
    components: list[set[str]] = []
    for decision in branch_context.pair_decisions:
        if decision.sense != SAME_JOURNEY:
            continue
        merged = {str(decision.task_a), str(decision.task_b)}
        remaining: list[set[str]] = []
        for component in components:
            if component & merged:
                merged.update(component)
            else:
                remaining.append(component)
        remaining.append(merged)
        components = remaining

    normalized_components = tuple(
        sorted((tuple(sorted(component)) for component in components), key=lambda row: row)
    )
    structurally_conflicting = []
    for component in normalized_components:
        task_set = set(component)
        for decision in branch_context.pair_decisions:
            if (
                decision.sense != SAME_JOURNEY
                and str(decision.task_a) in task_set
                and str(decision.task_b) in task_set
            ):
                structurally_conflicting.append(component)
                break

    columns: list[JourneyColumn] = []
    component_rows: list[dict] = []
    for component in normalized_components:
        if component in structurally_conflicting:
            component_rows.append(
                {
                    "tasks": list(component),
                    "status": "STRUCTURAL_BRANCH_CONFLICT",
                    "column_count": 0,
                }
            )
            continue
        known_tasks = tuple(task_id for task_id in component if task_id in data.tasks)
        if len(known_tasks) != len(component) or len(known_tasks) < 2:
            component_rows.append(
                {
                    "tasks": list(component),
                    "status": "UNKNOWN_OR_DEGENERATE_COMPONENT",
                    "column_count": 0,
                }
            )
            continue
        if len(known_tasks) > int(max_direct_tasks):
            component_rows.append(
                {
                    "tasks": list(component),
                    "status": "COMPONENT_ABOVE_DIRECT_LIMIT",
                    "column_count": 0,
                }
            )
            continue
        remaining = _remaining_wall_time_limit(
            wall_time_limit_sec,
            started_at=started_at,
        )
        if remaining is not None and remaining <= 0.0:
            component_rows.append(
                {
                    "tasks": list(component),
                    "status": "TIME_LIMIT",
                    "column_count": 0,
                }
            )
            continue
        restricted_data = replace(
            data,
            scale=len(known_tasks),
            tasks={task_id: data.tasks[task_id] for task_id in known_tasks},
        )
        pricing_payload, candidates = price_direct_journey_columns(
            restricted_data,
            JourneyDuals(cover={}),
            negative_eps=1.0e-6,
            max_direct_tasks=len(known_tasks),
            allow_partial=False,
            max_candidate_sets=1,
            wall_time_limit_sec=remaining,
            completion_bound_enabled=False,
            branch_context=branch_context,
        )
        rebuilt = []
        required = frozenset(known_tasks)
        for candidate in candidates:
            if frozenset(candidate.task_set) != required:
                continue
            column = build_journey_column(data, candidate.sorties)
            if journey_satisfies_branch_context(column, branch_context):
                rebuilt.append(column)
        if rebuilt:
            best = min(rebuilt, key=lambda column: (column.objective, column.end_time))
            columns.append(best)
        component_rows.append(
            {
                "tasks": list(component),
                "status": pricing_payload.get("status"),
                "column_count": int(bool(rebuilt)),
                "candidate_count": len(candidates),
            }
        )

    return tuple(columns), {
        "status": (
            "SAME_JOURNEY_SEEDS_READY"
            if columns
            else "NO_SAME_JOURNEY_SEED_REQUIRED"
            if not normalized_components
            else "SAME_JOURNEY_SEED_INCOMPLETE"
        ),
        "component_count": len(normalized_components),
        "seed_column_count": len(columns),
        "structural_conflict_count": len(structurally_conflicting),
        "components": component_rows,
        "wall_time_sec": round(perf_counter() - started_at, 6),
        "certificate_role": "starting_basis_only",
    }


def _load_columns_for_node(
    pool: ColumnPool,
    view: MasterColumnView,
    columns: Iterable[JourneyColumn],
    *,
    node_id: str = "root",
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
) -> tuple[int, int]:
    loaded = 0
    branch_filtered = 0
    context = cut_context or CutContext()
    for column in columns:
        allowed = journey_satisfies_branch_context(column, branch_context)
        if not allowed:
            branch_filtered += 1
            continue
        signature = _column_signature_for_active_context(
            column,
            branch_context=branch_context,
            cut_context=context,
        )
        bpc_column = BpcColumn(signature=signature, objective=column.objective, payload=column)
        pool.add(
            bpc_column,
            {
                "master_view": view,
                "node_id": node_id,
                "is_allowed_by_branch": allowed,
                "cut_coefficients": context.coefficients_for(column),
                "branch_signature": signature.branch_signature,
                "dominance_key": _column_dominance_key_for_active_context(signature),
            },
        )
        stored = pool.get(signature)
        if stored is not None and _activate_column_in_master_view(
            pool,
            view,
            stored,
            node_id=node_id,
            branch_context=branch_context,
            cut_context=context,
        ):
            loaded += 1
    return loaded, branch_filtered


def _master_columns(pool: ColumnPool, view: MasterColumnView, *, node_id: str = "root") -> tuple[JourneyColumn, ...]:
    signatures = view.signatures_by_node.get(str(node_id), set())
    columns = []
    for signature in sorted(signatures, key=repr):
        column = pool.get(signature)
        if column is not None and isinstance(column.payload, JourneyColumn):
            columns.append(column.payload)
    return tuple(columns)


def _rmp_support_task_sets(master) -> tuple[tuple[str, ...], ...]:
    """Return task sets with positive lambda in the current RMP solution."""

    rmp = getattr(master, "rmp", None)
    rows = getattr(rmp, "primal_columns", tuple()) or tuple()
    support: set[tuple[str, ...]] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            lambda_value = float(row.get("lambda_value") or 0.0)
        except (TypeError, ValueError):
            lambda_value = 0.0
        if lambda_value <= 1.0e-9:
            continue
        task_set = tuple(sorted(str(task_id) for task_id in (row.get("tasks") or tuple())))
        if task_set:
            support.add(task_set)
    return tuple(sorted(support))


def _audit_selected_columns_for_master_entry(
    columns: tuple[JourneyColumn, ...],
    *,
    duals: JourneyDuals,
    pool: ColumnPool,
    view: MasterColumnView,
    node_id: str = "root",
    negative_eps: float = 1.0e-6,
    active_task_sets: set[frozenset[str]] | None = None,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
) -> dict:
    """Audit selected worker columns immediately before master insertion."""

    context = cut_context or CutContext()
    active_task_set_lookup = {
        frozenset(str(task_id) for task_id in row)
        for row in (active_task_sets or set())
    }
    threshold = -abs(float(negative_eps))
    reports: list[dict] = []
    seen_signatures: set[object] = set()
    duplicate_signature_count = 0
    min_rc: float | None = None
    max_rc: float | None = None
    true_dual_pass = True
    branch_pass = True
    cut_pass = True
    addability_pass = True
    for column in columns:
        signature = _column_signature_for_active_context(
            column,
            branch_context=branch_context,
            cut_context=context,
        )
        duplicate_selected_signature = signature in seen_signatures
        if duplicate_selected_signature:
            duplicate_signature_count += 1
        seen_signatures.add(signature)
        cut_coefficients = context.coefficients_for(column)
        rc = manual_journey_reduced_cost(
            column,
            duals,
            cut_coefficients=cut_coefficients,
        )
        min_rc = float(rc) if min_rc is None else min(float(min_rc), float(rc))
        max_rc = float(rc) if max_rc is None else max(float(max_rc), float(rc))
        is_negative = float(rc) < threshold
        branch_allowed = journey_satisfies_branch_context(column, branch_context)
        bpc_column = BpcColumn(signature=signature, objective=column.objective, payload=column)
        addability = pool.addability_check(
            bpc_column,
            {
                "master_view": view,
                "node_id": node_id,
                "active_task_sets": active_task_set_lookup,
                "is_allowed_by_branch": branch_allowed,
                "cut_coefficients": cut_coefficients,
                "branch_signature": getattr(signature, "branch_signature", tuple()),
                "dominance_key": _column_dominance_key_for_active_context(signature),
            },
        )
        would_enter = bool(addability.would_enter_master and not duplicate_selected_signature)
        true_dual_pass = true_dual_pass and is_negative
        branch_pass = branch_pass and bool(addability.is_allowed_by_branch)
        cut_pass = cut_pass and bool(addability.is_allowed_by_cut_context)
        addability_pass = addability_pass and would_enter
        reports.append(
            {
                "task_set": sorted(str(task_id) for task_id in column.task_set),
                "true_reduced_cost": round(float(rc), 9),
                "is_true_negative": bool(is_negative),
                "would_enter_master": would_enter,
                "addability_reason": (
                    "duplicate_selected_signature"
                    if duplicate_selected_signature
                    else addability.reason
                ),
                "reject_reason": (
                    "duplicate_selected_signature"
                    if duplicate_selected_signature
                    else addability.reject_reason
                ),
                "pool_contains_signature": bool(addability.pool_contains_signature),
                "current_master_contains_signature": bool(addability.current_master_contains_signature),
                "is_allowed_by_branch": bool(addability.is_allowed_by_branch),
                "is_allowed_by_cut_context": bool(addability.is_allowed_by_cut_context),
                "would_change_active_support": bool(addability.would_change_active_support),
                "duplicate_selected_signature": bool(duplicate_selected_signature),
            }
        )
    audited_count = len(columns)
    audit_pass = bool(
        true_dual_pass
        and branch_pass
        and cut_pass
        and addability_pass
        and duplicate_signature_count == 0
    )
    return {
        "selected_column_entry_audit_available": True,
        "selected_column_entry_audit_pass": audit_pass,
        "selected_column_true_dual_rc_audit_pass": bool(true_dual_pass),
        "selected_column_branch_audit_pass": bool(branch_pass),
        "selected_column_cut_audit_pass": bool(cut_pass),
        "selected_column_addability_audit_pass": bool(addability_pass),
        "selected_column_audited_count": int(audited_count),
        "selected_column_entry_audit_rejected_count": 0 if audit_pass else int(audited_count),
        "selected_column_duplicate_signature_count": int(duplicate_signature_count),
        "selected_column_min_true_rc": None if min_rc is None else round(float(min_rc), 9),
        "selected_column_max_true_rc": None if max_rc is None else round(float(max_rc), 9),
        "selected_column_entry_audit_reports": reports,
    }


def _add_selected_to_pool_and_master(
    pool: ColumnPool,
    view: MasterColumnView,
    columns: tuple[JourneyColumn, ...],
    *,
    node_id: str = "root",
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
) -> int:
    added = 0
    context = cut_context or CutContext()
    for column in columns:
        allowed = journey_satisfies_branch_context(column, branch_context)
        if not allowed:
            continue
        signature = _column_signature_for_active_context(
            column,
            branch_context=branch_context,
            cut_context=context,
        )
        bpc_column = BpcColumn(signature=signature, objective=column.objective, payload=column)
        pool.add(
            bpc_column,
            {
                "master_view": view,
                "node_id": node_id,
                "is_allowed_by_branch": allowed,
                "cut_coefficients": context.coefficients_for(column),
                "branch_signature": signature.branch_signature,
                "dominance_key": _column_dominance_key_for_active_context(signature),
            },
        )
        stored = pool.get(signature)
        if stored is not None and _activate_column_in_master_view(
            pool,
            view,
            stored,
            node_id=node_id,
            branch_context=branch_context,
            cut_context=context,
        ):
            added += 1
    return added


def _activate_column_in_master_view(
    pool: ColumnPool,
    view: MasterColumnView,
    column: BpcColumn,
    *,
    node_id: str = "root",
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
) -> bool:
    context = cut_context or CutContext()
    if not _root_representative_view_enabled(node_id=node_id, branch_context=branch_context, cut_context=context):
        return view.add_from_pool(column, node_id=node_id, pool=pool)
    return _activate_root_best_task_set_representative(pool, view, column, node_id=node_id)


def _root_representative_view_enabled(
    *,
    node_id: str,
    branch_context: BranchContext | None,
    cut_context: CutContext,
) -> bool:
    branch = branch_context or BranchContext()
    return str(node_id) == "root" and branch.empty and cut_context.empty


def _activate_root_best_task_set_representative(
    pool: ColumnPool,
    view: MasterColumnView,
    column: BpcColumn,
    *,
    node_id: str = "root",
    objective_eps: float = 1.0e-9,
) -> bool:
    """Activate only the best root RMP representative for a task set.

    The root master constraints depend on task coverage and fleet usage.  When
    branch/cut rows are inactive, two columns with the same task set have the
    same root coefficients, so the higher-objective one is root-dominated.  The
    pool still keeps all semantic signatures for later branch/cut contexts.
    """

    key = str(node_id)
    signatures = view.signatures_by_node.setdefault(key, set())
    if column.signature in signatures:
        return False
    task_set = tuple(column.signature.task_set)
    same_task_signatures = [
        signature
        for signature in signatures
        if tuple(signature.task_set) == task_set
    ]
    if not same_task_signatures:
        return view.add_from_pool(column, node_id=node_id, pool=pool)
    incumbent_rows = [
        (signature, pool.get(signature))
        for signature in same_task_signatures
    ]
    incumbent_rows = [
        (signature, stored)
        for signature, stored in incumbent_rows
        if stored is not None
    ]
    if not incumbent_rows:
        return view.add_from_pool(column, node_id=node_id, pool=pool)
    incumbent_best = min(float(stored.objective) for _signature, stored in incumbent_rows)
    if float(column.objective) >= incumbent_best - abs(float(objective_eps)):
        return False
    for signature, stored in incumbent_rows:
        if float(stored.objective) >= float(column.objective) - abs(float(objective_eps)):
            view.remove_signature(signature, node_id=node_id)
    return view.add_from_pool(column, node_id=node_id, pool=pool)


def _column_signature_for_active_context(
    column: JourneyColumn,
    *,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
):
    context = cut_context or CutContext()
    if context.empty and (branch_context is None or branch_context.empty):
        return column_signature_from_journey(column)
    return cut_aware_column_signature_from_journey(
        column,
        cut_context=context,
        branch_context=branch_context,
    )


def _column_dominance_key_for_active_context(signature) -> tuple:
    key = tuple(signature.task_set)
    if signature.branch_signature or signature.cut_coefficient_vector_hash:
        return (
            tuple(signature.task_set),
            tuple(signature.branch_signature),
            str(signature.cut_coefficient_vector_hash),
        )
    return key


def _node_engine_payload(
    *,
    data: LunarIceData,
    node_id: str,
    branch_context: BranchContext,
    incumbent_objective: float | None,
    cut_context: CutContext | None = None,
    completion_policy: dict,
    proof_debt: ProofDebtQueue,
    profiling: PruningCounter,
    history: list[dict],
    harvest_totals: dict[str, int],
    profile_totals: dict,
    seed_report: dict,
    loaded_column_count: int,
    seed_branch_filtered_column_count: int,
    master,
    final_judge: dict | None,
    final_judge_columns: tuple[JourneyColumn, ...],
    final_judge_call_count: int,
    duplicate_only_count: int,
    hidden_negative_count: int,
    replacement_only_round_count: int,
    added_to_master_count: int,
    algorithm_status: AlgorithmStatus,
    certificate_scope: CertificateScope,
    pricing_state: PricingState,
    node_status: str,
    note: str,
    active_columns: Iterable[JourneyColumn] | None = None,
    hidden_audit: dict | None = None,
    seed_catalog: WorkerSeedCatalog | None = None,
) -> dict:
    active_cut_context = cut_context or CutContext()
    node_bound = None if master is None else master.rmp.objective_bound
    manual_rc_audit_pass = _manual_rc_audit_pass(master, None)
    pricing_rc_audit_pass = bool(final_judge and final_judge.get("pricing_rc_audit_pass") is True)
    final_judge_certifying_proof_kind = _final_judge_has_certifying_proof_kind(final_judge)
    branch_pricing_audit_pass = bool(
        final_judge is None
        or final_judge.get("all_priced_columns_satisfy_branch_context") is True
    )
    cut_pricing_audit_pass = bool(
        active_cut_context.empty
        or (
            final_judge is not None
            and final_judge.get("cut_context_active") is True
            and final_judge.get("live_cut_certificate_supported") is True
        )
    )
    gate_issues: list[str] = []
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and not manual_rc_audit_pass:
        gate_issues.append("manual_reduced_cost_audit_failed")
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and not pricing_rc_audit_pass:
        gate_issues.append("pricing_reduced_cost_audit_failed")
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and not final_judge_certifying_proof_kind:
        gate_issues.append("pricing_proof_kind_not_certifying")
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and not branch_pricing_audit_pass:
        gate_issues.append("branch_filtered_pricing_audit_failed")
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and not cut_pricing_audit_pass:
        gate_issues.append("cut_context_pricing_audit_failed")
    requested_algorithm_status = algorithm_status
    requested_certificate_scope = certificate_scope
    requested_pricing_state = pricing_state
    requested_node_status = str(node_status)
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and gate_issues:
        algorithm_status = AlgorithmStatus.BPC_INCOMPLETE_PRICING
        certificate_scope = CertificateScope.DIAGNOSTIC_PRICING_FRONTIER
        pricing_state = PricingState.INCOMPLETE_LIMIT
        node_status = "NODE_INCOMPLETE"
    ledger = CertificateLedger(
        algorithm_status=algorithm_status,
        certificate_scope=certificate_scope,
        pricing_state=pricing_state,
        uses_true_dual_bpc_certificate=certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED,
        issues=gate_issues,
    ).validate(proof_debt_queue=proof_debt)
    node_lp_bound_official = bool(
        certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED
        and pricing_state == PricingState.CERTIFIED_NO_NEGATIVE
        and ledger["valid"]
    )
    candidate_negative_count = int(harvest_totals.get("candidate_negative_count") or 0)
    addable_negative_count = int(harvest_totals.get("addable_negative_count") or 0)
    selected_count = int(harvest_totals.get("selected_count") or 0)
    selected_would_enter_master_count = int(harvest_totals.get("selected_would_enter_master_count") or 0)
    profile_payload = _profile_payload(profile_totals, profiling, final_judge)
    hidden_refinement_payload = _hidden_negative_refinement_summary(hidden_audit, seed_catalog)
    branch_filtered_count = max(
        int(seed_branch_filtered_column_count),
        int((final_judge or {}).get("branch_filtered_column_count") or 0),
        int(harvest_totals.get("branch_filtered_count") or 0),
    )
    payload = {
        "schema_version": "lunar_ice_bpc.b2b_r3_node_pricing_engine.v1",
        "node_id": str(node_id),
        "node_pricing_mode": B2B_R3_MODE,
        "b2_mode": B2B_R3_MODE,
        "task_count": len(data.task_ids),
        "branch_context": branch_context.to_payload(),
        "branch_context_active": not branch_context.empty,
        "branch_decision_count": len(branch_context.pair_decisions),
        "cut_context": active_cut_context.to_payload(),
        "cut_context_active": not active_cut_context.empty,
        "cut_count": len(active_cut_context.cuts),
        "incumbent_objective_at_entry": incumbent_objective,
        "algorithm_status": algorithm_status.value,
        "certificate_scope": certificate_scope.value,
        "pricing_state": pricing_state.value,
        "requested_algorithm_status": requested_algorithm_status.value,
        "requested_certificate_scope": requested_certificate_scope.value,
        "requested_pricing_state": requested_pricing_state.value,
        "node_status": str(node_status),
        "requested_node_status": requested_node_status,
        "uses_true_dual_bpc_certificate": ledger["uses_true_dual_bpc_certificate"],
        "certificate_ledger": ledger,
        "proof_debt_queue": proof_debt.audit(),
        "proof_debt_unreleased_count": len(proof_debt.unreleased),
        "completion_bound_policy": completion_policy,
        "completion_bound_pruning_enabled": False,
        "seed_mode": seed_report.get("seed_mode"),
        "seed_builder": seed_report.get("seed_builder") or "",
        "initial_column_count": int(seed_report.get("initial_column_count") or 0),
        "full_universe_preloaded": bool(seed_report.get("full_universe_preloaded")),
        "loaded_column_count": int(loaded_column_count),
        "branch_filtered_column_count": int(branch_filtered_count),
        "seed_branch_filtered_column_count": int(seed_branch_filtered_column_count),
        "rmp_status": None if master is None else master.rmp.status,
        "node_lp_bound": node_bound,
        "node_lp_bound_official": node_lp_bound_official,
        "rmp_iteration_count": 0 if master is None else master.rmp.iteration_count,
        "dual_context": {} if master is None else _dual_context_payload(master.reduced_cost_context),
        "pricing_round_count": len(history),
        "final_judge_call_count": int(final_judge_call_count),
        "final_judge": final_judge or {},
        **_final_judge_summary_fields(final_judge),
        "final_judge_certifying_proof_kind": bool(final_judge_certifying_proof_kind),
        "history": list(history),
        "manual_rc_audit_pass": manual_rc_audit_pass,
        "pricing_rc_audit_pass": pricing_rc_audit_pass,
        "branch_pricing_audit_pass": branch_pricing_audit_pass,
        "cut_pricing_audit_pass": cut_pricing_audit_pass,
        "candidate_negative_count": candidate_negative_count,
        "addable_negative_count": addable_negative_count,
        "selected_count": selected_count,
        "selected_would_enter_master_count": selected_would_enter_master_count,
        "selected_all_would_enter_master": selected_would_enter_master_count == selected_count,
        "selected_harvest_addability_fail_count": 0 if selected_would_enter_master_count == selected_count else 1,
        "added_to_master_count": int(added_to_master_count),
        "added_column_count": int(added_to_master_count),
        "duplicate_only_count": int(duplicate_only_count),
        "hidden_negative_count": int(hidden_negative_count),
        **hidden_refinement_payload,
        "replacement_only_round_count": int(replacement_only_round_count),
        **profile_payload,
        **harvest_totals,
        "exact_status": (
            "BPC_NODE_LP_CERTIFIED"
            if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and ledger["valid"]
            else "NOT_SOLVED"
        ),
        "fail_closed_reason": "" if node_lp_bound_official else note,
        "note": note,
        "_master": master,
        "_all_priced_columns": tuple(final_judge_columns),
    }
    if active_columns is not None:
        active_columns_tuple = tuple(active_columns)
        payload["active_columns_payload_version"] = "journey_solution_payload.v1"
        payload["active_columns"] = [
            column.to_solution_payload(vehicle_id=f"active_column_{index:06d}")
            for index, column in enumerate(active_columns_tuple, start=1)
        ]
    return payload


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
    extra: dict | None = None,
) -> dict:
    root_objective = None if master is None else master.rmp.objective_bound
    b0_objective = None if b0_direct is None else b0_direct.objective
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
    final_judge_certifying_proof_kind = _final_judge_has_certifying_proof_kind(final_judge)
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
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and not final_judge_certifying_proof_kind:
        gate_issues.append("pricing_proof_kind_not_certifying")
    requested_algorithm_status = algorithm_status
    requested_certificate_scope = certificate_scope
    requested_pricing_state = pricing_state
    if certificate_scope == CertificateScope.BPC_NODE_LP_CERTIFIED and gate_issues:
        algorithm_status = AlgorithmStatus.BPC_INCOMPLETE_PRICING
        certificate_scope = CertificateScope.DIAGNOSTIC_PRICING_FRONTIER
        pricing_state = PricingState.INCOMPLETE_LIMIT
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
    hidden_refinement_payload = _hidden_negative_refinement_summary(hidden_audit, seed_catalog)
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
        "requested_algorithm_status": requested_algorithm_status.value,
        "requested_certificate_scope": requested_certificate_scope.value,
        "requested_pricing_state": requested_pricing_state.value,
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
        "dual_context": {} if master is None else _dual_context_payload(master.reduced_cost_context),
        "pricing_round_count": len(history),
        "final_judge_call_count": int(final_judge_call_count),
        "final_judge": final_judge or {},
        **_final_judge_summary_fields(final_judge),
        "final_judge_certifying_proof_kind": bool(final_judge_certifying_proof_kind),
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
        **hidden_refinement_payload,
        "replacement_only_round_count": int(replacement_only_round_count),
        **profile_payload,
        **harvest_totals,
        "b0_ablation": {
            "baseline": "B0_DIRECT_DP_FIXED_GRAPH_ORACLE",
            "direct_dp_status": None if b0_direct is None else b0_direct.status,
            "direct_dp_certificate_scope": None if b0_direct is None else b0_direct.certificate_scope,
            "direct_dp_objective": b0_objective,
            "direct_dp_objective_breakdown": None if b0_direct is None else getattr(b0_direct, "objective_breakdown", None),
            "reference_solution_upper_bound": None
            if b0_direct is None
            else getattr(b0_direct, "reference_solution_upper_bound", None),
            "reference_solution_upper_bound_source": ""
            if b0_direct is None
            else getattr(b0_direct, "reference_solution_upper_bound_source", ""),
            "direct_bound_pruning_root_bound": None
            if b0_direct is None
            else getattr(b0_direct, "direct_bound_pruning_root_bound", None),
            "direct_bound_pruning_active": False
            if b0_direct is None
            else getattr(b0_direct, "direct_bound_pruning_active", False),
            "journey_label_bound_pruned_count": 0
            if b0_direct is None
            else getattr(b0_direct, "journey_label_bound_pruned_count", 0),
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
        **(extra or {}),
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


def _final_judge_summary_fields(final_judge: dict | None) -> dict:
    payload = final_judge or {}
    return {
        "final_judge_status": payload.get("status") or "",
        "final_judge_exact_status": payload.get("exact_status") or "",
        "pricing_proof_kind": payload.get("pricing_proof_kind") or "",
        "underlying_pricing_proof_kind": payload.get("underlying_pricing_proof_kind") or "",
        "final_judge_can_certify_no_negative": bool(payload.get("can_certify_no_negative")),
        "final_judge_uses_true_dual_bpc_certificate": bool(
            payload.get("uses_true_dual_bpc_certificate")
        ),
        "final_judge_pricing_rc_audit_pass": payload.get("pricing_rc_audit_pass"),
        "final_judge_manual_rc_audit_pass": payload.get("manual_rc_audit_pass"),
        "final_judge_cut_context_active": bool(payload.get("cut_context_active")),
        "final_judge_cut_count": payload.get("cut_count"),
        "final_judge_live_cut_certificate_supported": bool(
            payload.get("live_cut_certificate_supported")
        ),
        "labeling_final_judge_enabled": bool(payload.get("labeling_final_judge_enabled")),
        "labeling_final_judge_auto_mode": bool(payload.get("labeling_final_judge_auto_mode")),
        "labeling_final_judge_auto_selected": bool(payload.get("labeling_final_judge_auto_selected")),
        "labeling_final_judge_auto_skip_reason": payload.get("labeling_final_judge_auto_skip_reason") or "",
        "labeling_final_judge_opt_in_source": payload.get("labeling_final_judge_opt_in_source") or "",
        "labeling_final_judge_selection_reason": payload.get(
            "labeling_final_judge_selection_reason"
        )
        or "",
        "labeling_final_judge_certificate_role": payload.get(
            "labeling_final_judge_certificate_role"
        )
        or "",
        "labeling_final_judge_can_certify": bool(payload.get("labeling_final_judge_can_certify")),
        "labeling_final_judge_downgrade_reason": payload.get(
            "labeling_final_judge_downgrade_reason"
        )
        or "",
        "labeling_final_judge_task_count": payload.get("labeling_final_judge_task_count"),
        "labeling_final_judge_max_exact_tasks": payload.get("labeling_final_judge_max_exact_tasks"),
        "labeling_final_judge_max_exact_tasks_source": payload.get(
            "labeling_final_judge_max_exact_tasks_source"
        )
        or "",
        "labeling_final_judge_exact_harvest_target": payload.get(
            "labeling_final_judge_exact_harvest_target"
        ),
        "labeling_final_judge_exact_harvest_target_source": payload.get(
            "labeling_final_judge_exact_harvest_target_source"
        )
        or "",
        "exact_negative_harvest_target": payload.get("exact_negative_harvest_target"),
        "exact_negative_harvest_candidate_count": payload.get(
            "exact_negative_harvest_candidate_count"
        ),
        "exact_negative_harvest_selected_count": payload.get(
            "exact_negative_harvest_selected_count"
        ),
        "exact_negative_harvest_selected_new_task_set_count": payload.get(
            "exact_negative_harvest_selected_new_task_set_count"
        ),
        "exact_negative_harvest_selected_replacement_task_set_count": payload.get(
            "exact_negative_harvest_selected_replacement_task_set_count"
        ),
        "exact_negative_harvest_selection_policy": payload.get(
            "exact_negative_harvest_selection_policy"
        )
        or "",
        "exact_negative_harvest_active_task_set_count": payload.get(
            "exact_negative_harvest_active_task_set_count"
        ),
        "exact_negative_harvest_non_active_task_set_count": payload.get(
            "exact_negative_harvest_non_active_task_set_count"
        ),
        "exact_negative_harvest_active_task_set_reference_count": payload.get(
            "exact_negative_harvest_active_task_set_reference_count"
        ),
        "labeling_final_judge_active_task_sets_for_harvest_count": payload.get(
            "labeling_final_judge_active_task_sets_for_harvest_count"
        ),
        "sortie_candidate_cache_enabled": bool(payload.get("sortie_candidate_cache_enabled")),
        "sortie_candidate_cache_limit": payload.get("sortie_candidate_cache_limit"),
        "sortie_candidate_cache_entry_count": payload.get("sortie_candidate_cache_entry_count"),
        "sortie_candidate_cache_hit_count": payload.get("sortie_candidate_cache_hit_count"),
        "sortie_candidate_cache_miss_count": payload.get("sortie_candidate_cache_miss_count"),
        "sortie_candidate_cache_reused_candidate_count": payload.get(
            "sortie_candidate_cache_reused_candidate_count"
        ),
    }


def _final_judge_has_certifying_proof_kind(final_judge: dict | None) -> bool:
    payload = final_judge or {}
    return bool(
        payload.get("can_certify_no_negative") is True
        and payload.get("uses_true_dual_bpc_certificate") is True
        and payload.get("pricing_rc_audit_pass") is True
        and str(payload.get("pricing_proof_kind") or "") in CERTIFYING_PRICING_PROOF_KINDS
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


def _empty_harvest_totals() -> dict:
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
        "harvest_selected_new_task_set_count": 0,
        "harvest_selected_replacement_task_set_count": 0,
        "harvest_rejected_duplicate_count": 0,
        "harvest_rejected_not_addable_count": 0,
        "harvest_duplicate_signature_count": 0,
        "harvest_forbidden_signature_count": 0,
        "harvest_branch_filtered_count": 0,
        "harvest_cut_filtered_count": 0,
        "harvest_duplicate_in_current_master_count": 0,
        "harvest_in_pool_not_master_count": 0,
        "harvest_dominance_filtered_count": 0,
        "harvest_best_true_rc": None,
        "harvest_worst_selected_true_rc": None,
        "harvest_avg_pairwise_jaccard": None,
    }


def _accumulate_harvest_totals(totals: dict, payload: dict) -> None:
    previous_selected_count = int(totals.get("harvest_selected_count") or 0)
    for key in list(totals):
        if key in {
            "harvest_best_true_rc",
            "harvest_worst_selected_true_rc",
            "harvest_avg_pairwise_jaccard",
        }:
            continue
        totals[key] += int(payload.get(key) or 0)
    best_rc = _optional_float(payload.get("harvest_best_true_rc"))
    if best_rc is not None:
        totals["harvest_best_true_rc"] = (
            best_rc
            if totals["harvest_best_true_rc"] is None
            else min(float(totals["harvest_best_true_rc"]), best_rc)
        )
    worst_rc = _optional_float(payload.get("harvest_worst_selected_true_rc"))
    if worst_rc is not None:
        totals["harvest_worst_selected_true_rc"] = (
            worst_rc
            if totals["harvest_worst_selected_true_rc"] is None
            else max(float(totals["harvest_worst_selected_true_rc"]), worst_rc)
        )
    avg_jaccard = _optional_float(payload.get("harvest_avg_pairwise_jaccard"))
    selected_count = int(payload.get("harvest_selected_count") or payload.get("selected_count") or 0)
    if avg_jaccard is not None and selected_count > 0:
        previous_avg = _optional_float(totals.get("harvest_avg_pairwise_jaccard"))
        previous_weight = previous_selected_count if previous_avg is not None else 0
        total_weight = previous_weight + selected_count
        totals["harvest_avg_pairwise_jaccard"] = (
            None
            if total_weight <= 0
            else round(((previous_avg or 0.0) * previous_weight + avg_jaccard * selected_count) / total_weight, 9)
        )


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def _remaining_wall_time_limit(wall_time_limit_sec: float | None, *, started_at: float) -> float | None:
    if wall_time_limit_sec is None:
        return None
    return float(wall_time_limit_sec) - (perf_counter() - float(started_at))


def _wall_time_limit_exceeded(wall_time_limit_sec: float | None, *, started_at: float) -> bool:
    remaining = _remaining_wall_time_limit(wall_time_limit_sec, started_at=started_at)
    return bool(remaining is not None and remaining <= 0.0)


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.environ.get(str(name))
    if raw is None:
        return bool(default)
    return str(raw).strip().lower() not in {"", "0", "false", "off", "no"}


def _env_int(name: str, *, default: int, minimum: int, maximum: int) -> int:
    raw = os.environ.get(str(name))
    if raw is None:
        value = int(default)
    else:
        try:
            value = int(raw)
        except (TypeError, ValueError):
            value = int(default)
    return max(int(minimum), min(int(maximum), value))


def _env_float(name: str, *, default: float, minimum: float, maximum: float) -> float:
    raw = os.environ.get(str(name))
    if raw is None:
        value = float(default)
    else:
        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = float(default)
    return max(float(minimum), min(float(maximum), value))


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
