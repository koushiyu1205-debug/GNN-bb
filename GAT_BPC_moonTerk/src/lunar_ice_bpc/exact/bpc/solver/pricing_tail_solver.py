"""B2 root pricing-tail optimization layer.

B2 is a candidate layer over the accepted B0/B1 proof core.  It never changes
certificate scope or official-bound semantics; it only changes root pricing-tail
handling and records addability, duplicate-only, hidden-negative, and harvesting
diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass
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
from lunar_ice_bpc.exact.pricing.journey_pricing import DirectPricingCache
from lunar_ice_bpc.exact.solver.journey_driver import (
    enumerate_direct_journey_columns,
    solve_direct_journey_baseline,
)


B2A_MODE = "B2A_full_universe_rc_audit_fast_path"
B2B_MODE = "B2B_seeded_tail_CG"


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
        negative_pairs = tuple(
            (manual_journey_reduced_cost(column, master.rmp.duals), column)
            for column in judge.all_priced_columns
            if manual_journey_reduced_cost(column, master.rmp.duals) < -abs(float(negative_eps))
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
    return {
        "schema_version": "lunar_ice_bpc.b2_pricing_tail_baseline.v2",
        "instance_id": data.instance_id,
        "task_count": len(data.task_ids),
        "b2_mode": str(mode),
        "seed_mode": seed_report.get("seed_mode"),
        "initial_column_count": int(seed_report.get("initial_column_count") or 0),
        "full_universe_column_count": seed_report.get("full_universe_column_count"),
        "full_universe_preloaded": bool(seed_report.get("full_universe_preloaded")),
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
        "added_to_master_count": int(added_to_master_count),
        "added_column_count": int(added_to_master_count),
        "candidate_addable_ratio": (
            None if candidate_negative_count == 0 else round(addable_negative_count / candidate_negative_count, 9)
        ),
        "duplicate_only_count": int(duplicate_only_count),
        "hidden_negative_count": int(hidden_negative_count),
        "replacement_only_round_count": int(replacement_only_round_count),
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

