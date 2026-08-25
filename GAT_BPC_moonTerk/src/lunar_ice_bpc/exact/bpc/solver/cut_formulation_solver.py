"""B4 cut/formulation baseline layered on the B3 tree contract."""

from __future__ import annotations

from lunar_ice_bpc.exact.bpc.certificates.certificate_ledger import CertificateLedger
from lunar_ice_bpc.exact.bpc.certificates.proof_debt_queue import ProofDebtQueue
from lunar_ice_bpc.exact.bpc.cuts.cut_audit import (
    audit_cut_reduced_cost_consistency,
    build_cut_dominance_compatibility_report,
    cut_aware_column_signature_from_journey,
)
from lunar_ice_bpc.exact.bpc.master.journey_master import solve_root_journey_master
from lunar_ice_bpc.exact.bpc.pricing.completion_bounds import build_completion_bound_tail_policy
from lunar_ice_bpc.exact.bpc.pricing.final_judge import run_true_dual_root_final_judge
from lunar_ice_bpc.exact.bpc.pricing.status import AlgorithmStatus, CertificateScope, PricingState
from lunar_ice_bpc.exact.bpc.solver.branch_tree_solver import solve_b3_branch_price_tree_baseline
from lunar_ice_bpc.exact.bpc.solver.root_node_solver import (
    _reference_seed_direct_placeholder,
    build_b1_seed_columns,
    dense_rmp_memory_precheck,
    representative_universe_column_count,
)
from lunar_ice_bpc.exact.core.cuts import CutContext, cut_context_from_payload
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.pricing.journey_pricing import DirectPricingCache
from lunar_ice_bpc.exact.solver.column_pool import select_journey_column_pool
from lunar_ice_bpc.exact.solver.cut_probe import build_cut_probe
from lunar_ice_bpc.exact.solver.cut_separator import run_restricted_cut_separation_round
from lunar_ice_bpc.exact.solver.journey_driver import enumerate_direct_journey_columns


def solve_b4_cut_formulation_baseline(
    data: LunarIceData,
    *,
    max_direct_tasks: int = 5,
    max_rounds: int = 8,
    negative_eps: float = 1.0e-6,
    live_subset_rows: bool = False,
    max_live_cuts: int = 3,
    add_violated_only: bool = True,
) -> dict:
    """Run B4 = B3 plus subset-row cut diagnostics and opt-in live cuts."""

    fail_closed_b3 = _fail_closed_b3_placeholder()
    if len(data.task_ids) > int(max_direct_tasks):
        return _too_large_payload(data=data, b3=fail_closed_b3, max_direct_tasks=max_direct_tasks)
    estimated_columns = representative_universe_column_count(len(data.task_ids))
    precheck = dense_rmp_memory_precheck(
        data,
        active_column_count=estimated_columns,
        cut_count=max(0, int(max_live_cuts) if live_subset_rows else 0),
        stage="b4_direct_universe_cut_diagnostic_rmp",
    )
    if precheck["rmp_memory_precheck_failed"]:
        return _restricted_pool_cut_diagnostic_payload(
            data=data,
            b3=fail_closed_b3,
            max_direct_tasks=max_direct_tasks,
            max_live_cuts=max_live_cuts,
            negative_eps=negative_eps,
            add_violated_only=add_violated_only,
            estimated_columns=estimated_columns,
            precheck=precheck,
        )

    b3 = solve_b3_branch_price_tree_baseline(
        data,
        max_direct_tasks=max_direct_tasks,
        max_rounds_per_node=max_rounds,
        negative_eps=negative_eps,
    )

    universe = enumerate_direct_journey_columns(data, max_exact_tasks=int(max_direct_tasks)).columns
    root_no_cut = solve_root_journey_master(
        data,
        universe,
        negative_eps=negative_eps,
        rmp_iteration_id="b4-root-no-cut",
    )
    cut_probe = build_cut_probe(
        data.task_ids,
        universe,
        root_no_cut.rmp.primal_columns,
        fleet_size=data.fleet_size,
        violation_eps=negative_eps,
    )
    diagnostic_round = run_restricted_cut_separation_round(
        data.task_ids,
        universe,
        fleet_size=data.fleet_size,
        root_rmp=root_no_cut.rmp,
        cut_probe=cut_probe,
        max_rows=max_live_cuts,
        violation_eps=negative_eps,
        include_fleet_lower_bound=False,
        add_violated_only=add_violated_only,
    )
    selected_payloads = (
        _selected_subset_row_payloads(
            cut_probe,
            max_rows=max_live_cuts,
            violation_eps=negative_eps,
            add_violated_only=add_violated_only,
        )
        if live_subset_rows
        else tuple()
    )
    live_context = cut_context_from_payload({"cuts": selected_payloads})
    completion_policy = build_completion_bound_tail_policy(
        pruning_opt_in=bool(live_subset_rows and not live_context.empty),
        cut_context_active=not live_context.empty,
    )
    dominance_report = build_cut_dominance_compatibility_report(live_context)

    if live_context.empty:
        return _diagnostic_payload(
            data=data,
            b3=b3,
            root_no_cut=root_no_cut,
            cut_probe=cut_probe,
            diagnostic_round=diagnostic_round,
            completion_policy=completion_policy,
            dominance_report=dominance_report,
            live_requested=live_subset_rows,
            note=(
                "B4 subset-row cuts were evaluated in diagnostic mode only; no certificate semantics changed."
                if not live_subset_rows
                else "B4 live subset-row opt-in found no eligible row; fail closed to B3 semantics."
            ),
        )

    return _live_subset_row_payload(
        data=data,
        b3=b3,
        universe=universe,
        root_no_cut=root_no_cut,
        cut_probe=cut_probe,
        diagnostic_round=diagnostic_round,
        live_context=live_context,
        completion_policy=completion_policy,
        dominance_report=dominance_report,
        negative_eps=negative_eps,
        max_direct_tasks=max_direct_tasks,
    )


def _live_subset_row_payload(
    *,
    data: LunarIceData,
    b3: dict,
    universe,
    root_no_cut,
    cut_probe: dict,
    diagnostic_round: dict,
    live_context: CutContext,
    completion_policy: dict,
    dominance_report: dict,
    negative_eps: float,
    max_direct_tasks: int,
) -> dict:
    master = solve_root_journey_master(
        data,
        universe,
        negative_eps=negative_eps,
        rmp_iteration_id="b4-root-live-subset-row",
        cut_context=live_context,
    )
    judge = None
    if master.rmp.status == "RESTRICTED_RMP_OPTIMAL":
        judge = run_true_dual_root_final_judge(
            data,
            master.reduced_cost_context,
            max_direct_tasks=max_direct_tasks,
            negative_eps=negative_eps,
            cache=DirectPricingCache(),
            cut_context=live_context,
            active_task_sets={
                frozenset(column.task_set) for column in universe
            },
            proof_tail_active_column_count=len(universe),
            proof_tail_round_index=0,
        )
    final_judge = {} if judge is None else judge.pricing_payload
    priced_columns = tuple() if judge is None else judge.all_priced_columns
    cut_audit = audit_cut_reduced_cost_consistency(
        priced_columns,
        master.rmp.duals,
        live_context,
        final_judge,
        negative_eps=negative_eps,
    )
    incumbent = select_journey_column_pool(data.task_ids, universe, fleet_size=data.fleet_size)
    root_bound = _float_or_none(master.rmp.objective_bound)
    incumbent_objective = _float_or_none(incumbent.objective)
    integer_matches = bool(
        root_bound is not None
        and incumbent_objective is not None
        and abs(float(root_bound) - float(incumbent_objective)) <= abs(float(negative_eps))
    )
    node_official = bool(
        master.rmp.status == "RESTRICTED_RMP_OPTIMAL"
        and judge is not None
        and judge.pricing_state == PricingState.CERTIFIED_NO_NEGATIVE
        and cut_audit["manual_rc_cut_consistency_pass"]
        and dominance_report["valid"]
        and completion_policy["pruning_enabled"] is False
    )
    if node_official and integer_matches:
        algorithm_status = AlgorithmStatus.BPC_OPTIMAL
        certificate_scope = CertificateScope.BPC_TREE_OPTIMAL
        exact_status = "BPC_TREE_OPTIMAL"
    elif node_official:
        algorithm_status = AlgorithmStatus.BPC_GAP_AVAILABLE
        certificate_scope = CertificateScope.BPC_NODE_LP_CERTIFIED
        exact_status = "BPC_NODE_LP_CERTIFIED"
    else:
        algorithm_status = AlgorithmStatus.BPC_INCOMPLETE_PRICING
        certificate_scope = CertificateScope.DIAGNOSTIC_PRICING_FRONTIER
        exact_status = "NOT_SOLVED"
    issues = []
    if live_context.empty:
        issues.append("live_cut_context_empty")
    if completion_policy["pruning_enabled"] is not False:
        issues.append("completion_bound_pruning_not_fail_closed_under_cut_context")
    if not dominance_report["valid"]:
        issues.extend(dominance_report["issues"])
    if not cut_audit["manual_rc_cut_consistency_pass"]:
        issues.append("manual_rc_cut_consistency_failed")
    if node_official and not integer_matches and certificate_scope == CertificateScope.BPC_TREE_OPTIMAL:
        issues.append("tree_scope_without_integer_root")
    ledger = CertificateLedger(
        algorithm_status=algorithm_status,
        certificate_scope=certificate_scope,
        pricing_state=(
            PricingState.CERTIFIED_NO_NEGATIVE
            if node_official
            else PricingState.INCOMPLETE_LIMIT
        ),
        uses_true_dual_bpc_certificate=node_official,
        issues=issues,
    ).validate(proof_debt_queue=ProofDebtQueue())
    lp_bound_delta = _bound_delta(_float_or_none(b3.get("root_lp_bound")), root_bound)
    b3_gap = _float_or_none(b3.get("global_gap"))
    b4_gap = None if incumbent_objective is None or root_bound is None else round(incumbent_objective - root_bound, 9)
    root_gap_delta = _bound_delta(b3_gap, b4_gap)
    cut_effective_claim = bool(
        lp_bound_delta is not None
        and lp_bound_delta > abs(float(negative_eps))
        and root_gap_delta is not None
        and root_gap_delta < -abs(float(negative_eps))
    )
    return {
        "schema_version": "lunar_ice_bpc.b4_cut_formulation_baseline.v1",
        "instance_id": data.instance_id,
        "algorithm_status": algorithm_status.value,
        "certificate_scope": certificate_scope.value,
        "exact_status": exact_status if ledger["valid"] else "NOT_SOLVED",
        "pricing_state": str(ledger["pricing_state"]),
        "uses_true_dual_bpc_certificate": ledger["uses_true_dual_bpc_certificate"],
        "certificate_ledger": ledger,
        "task_count": len(data.task_ids),
        "live_subset_rows": True,
        "fleet_lower_bound_live_enabled": False,
        "cut_rows_active": True,
        "cut_context": live_context.to_payload(),
        "cut_probe": cut_probe,
        "diagnostic_cut_separation_round": diagnostic_round,
        "completion_bound_policy": completion_policy,
        "cut_dominance_compatibility_report": dominance_report,
        "cut_aware_signature_summary": _cut_aware_signature_summary(universe, live_context),
        "cut_reduced_cost_audit": cut_audit,
        "root_rmp_status": master.rmp.status,
        "root_lp_bound": root_bound,
        "root_lp_bound_official": bool(node_official),
        "root_no_cut_lp_bound": _float_or_none(root_no_cut.rmp.objective_bound),
        "incumbent_objective": incumbent_objective,
        "final_integer_optimum_unchanged_vs_B3": _objectives_match(incumbent_objective, b3.get("incumbent_objective")),
        "final_judge": final_judge,
        "final_judge_status": final_judge.get("status"),
        "final_judge_min_reduced_cost": final_judge.get("best_reduced_cost"),
        "manual_rc_cut_consistency_pass_count": int(cut_audit["manual_rc_cut_consistency_pass"]),
        "cut_dual_nonzero_count": sum(
            1 for value in (master.rmp.duals.cuts or {}).values() if abs(float(value)) > abs(float(negative_eps))
        ),
        "cut_violation_count": int(cut_probe.get("violated_subset_candidate_count") or 0),
        "cut_added_count": len(live_context.cuts),
        "cut_pricing_supported_count": int(dominance_report["pricing_supported_count"]),
        "cut_completion_bound_fail_closed_count": int(dominance_report["cut_completion_bound_fail_closed_count"]),
        "lp_bound_delta": lp_bound_delta,
        "root_gap_delta": root_gap_delta,
        "node_gap_delta": root_gap_delta,
        "branch_node_count_delta": 0 - int(b3.get("branch_node_count") or 0),
        "pricing_round_delta": 1 - int(b3.get("node_count") or 0),
        "final_judge_time_delta": None,
        "bpc_tree_optimal_count_delta": int(certificate_scope == CertificateScope.BPC_TREE_OPTIMAL) - int(b3.get("bpc_tree_optimal_count") or 0),
        "cut_effective_claim": cut_effective_claim,
        "b3_ablation": _b3_ablation_payload(b3, root_bound=root_bound, certificate_scope=certificate_scope.value),
        "note": (
            "B4 live subset-row cut path is exact-safe and closes the root tree."
            if certificate_scope == CertificateScope.BPC_TREE_OPTIMAL and ledger["valid"]
            else "B4 live subset-row cut path did not close a full tree; certificate scope remains gated."
        ),
    }


def _diagnostic_payload(
    *,
    data: LunarIceData,
    b3: dict,
    root_no_cut,
    cut_probe: dict,
    diagnostic_round: dict,
    completion_policy: dict,
    dominance_report: dict,
    live_requested: bool,
    note: str,
) -> dict:
    return {
        "schema_version": "lunar_ice_bpc.b4_cut_formulation_baseline.v1",
        "instance_id": data.instance_id,
        "algorithm_status": b3.get("algorithm_status"),
        "certificate_scope": b3.get("certificate_scope"),
        "exact_status": b3.get("exact_status"),
        "pricing_state": b3.get("pricing_state"),
        "uses_true_dual_bpc_certificate": b3.get("uses_true_dual_bpc_certificate"),
        "certificate_ledger": b3.get("certificate_ledger"),
        "task_count": len(data.task_ids),
        "live_subset_rows": bool(live_requested),
        "fleet_lower_bound_live_enabled": False,
        "cut_rows_active": False,
        "cut_context": CutContext().to_payload(),
        "cut_probe": cut_probe,
        "diagnostic_cut_separation_round": diagnostic_round,
        "completion_bound_policy": completion_policy,
        "cut_dominance_compatibility_report": dominance_report,
        "cut_aware_signature_summary": _cut_aware_signature_summary(tuple(), CutContext()),
        "cut_reduced_cost_audit": {},
        "root_rmp_status": root_no_cut.rmp.status,
        "root_lp_bound": b3.get("root_lp_bound"),
        "root_lp_bound_official": b3.get("root_lp_bound_official"),
        "root_no_cut_lp_bound": root_no_cut.rmp.objective_bound,
        "incumbent_objective": b3.get("incumbent_objective"),
        "final_integer_optimum_unchanged_vs_B3": True,
        "manual_rc_cut_consistency_pass_count": 0,
        "cut_dual_nonzero_count": 0,
        "cut_violation_count": int(cut_probe.get("violated_subset_candidate_count") or 0),
        "cut_added_count": 0,
        "cut_pricing_supported_count": 0,
        "cut_completion_bound_fail_closed_count": 0,
        "lp_bound_delta": 0.0,
        "root_gap_delta": 0.0,
        "node_gap_delta": 0.0,
        "branch_node_count_delta": 0,
        "pricing_round_delta": 0,
        "final_judge_time_delta": None,
        "bpc_tree_optimal_count_delta": 0,
        "cut_effective_claim": False,
        "b3_ablation": _b3_ablation_payload(
            b3,
            root_bound=_float_or_none(b3.get("root_lp_bound")),
            certificate_scope=str(b3.get("certificate_scope")),
        ),
        "note": note,
    }


def _too_large_payload(*, data: LunarIceData, b3: dict, max_direct_tasks: int) -> dict:
    return {
        "schema_version": "lunar_ice_bpc.b4_cut_formulation_baseline.v1",
        "instance_id": data.instance_id,
        "algorithm_status": AlgorithmStatus.BPC_INCOMPLETE_PRICING.value,
        "certificate_scope": CertificateScope.FEASIBLE_INCUMBENT_ONLY.value,
        "exact_status": "NOT_SOLVED",
        "pricing_state": PricingState.INCOMPLETE_LIMIT.value,
        "uses_true_dual_bpc_certificate": False,
        "task_count": len(data.task_ids),
        "max_direct_tasks": int(max_direct_tasks),
        "live_subset_rows": False,
        "fleet_lower_bound_live_enabled": False,
        "cut_rows_active": False,
        "cut_context": CutContext().to_payload(),
        "cut_added_count": 0,
        "cut_violation_count": 0,
        "lp_bound_delta": None,
        "root_gap_delta": None,
        "b3_ablation": {
            "baseline": "B3_BRANCH_PRICE_TREE",
            "b3_algorithm_status": b3.get("algorithm_status"),
            "b3_certificate_scope": b3.get("certificate_scope"),
            "objective_diff_vs_B3": None,
            "certificate_scope_diff_vs_B3": f"{b3.get('certificate_scope')}->{CertificateScope.FEASIBLE_INCUMBENT_ONLY.value}",
        },
        "note": f"task_count={len(data.task_ids)} exceeds max_direct_tasks={max_direct_tasks}; B4 fails closed.",
    }


def _memory_precheck_payload(
    *,
    data: LunarIceData,
    b3: dict,
    max_direct_tasks: int,
    estimated_columns: int,
    precheck: dict,
) -> dict:
    payload = _too_large_payload(data=data, b3=b3, max_direct_tasks=max_direct_tasks)
    payload.update(
        {
            "full_universe_column_count": int(estimated_columns),
            "rmp_memory_precheck_failed": bool(precheck.get("rmp_memory_precheck_failed")),
            "rmp_memory_precheck_stage": precheck.get("rmp_memory_precheck_stage"),
            "rmp_memory_precheck_reason": precheck.get("rmp_memory_precheck_reason"),
            "rmp_memory_precheck_estimated_column_count": precheck.get("rmp_memory_precheck_estimated_column_count"),
            "rmp_memory_precheck_estimated_tableau_cells": precheck.get("rmp_memory_precheck_estimated_tableau_cells"),
            "rmp_memory_precheck_cell_limit": precheck.get("rmp_memory_precheck_cell_limit"),
            "note": (
                "B4 direct-universe cut diagnostic failed closed before column enumeration; "
                + str(precheck.get("rmp_memory_precheck_reason") or "")
            ),
        }
    )
    return payload


def _restricted_pool_cut_diagnostic_payload(
    *,
    data: LunarIceData,
    b3: dict,
    max_direct_tasks: int,
    max_live_cuts: int,
    negative_eps: float,
    add_violated_only: bool,
    estimated_columns: int,
    precheck: dict,
) -> dict:
    seed_columns, seed_report = build_b1_seed_columns(
        data,
        b0_direct=_reference_seed_direct_placeholder(data),
        seed_mode="b0_incumbent_plus_singletons",
        max_direct_tasks=int(max_direct_tasks),
    )
    if not seed_columns:
        payload = _memory_precheck_payload(
            data=data,
            b3=b3,
            max_direct_tasks=max_direct_tasks,
            estimated_columns=estimated_columns,
            precheck=precheck,
        )
        payload["restricted_pool_cut_diagnostic"] = {
            "status": "NO_SAFE_RESTRICTED_SEED_POOL",
            "evaluation_scope": "safe_restricted_seed_pool_only",
            "can_certify": False,
        }
        return payload
    root_restricted = solve_root_journey_master(
        data,
        seed_columns,
        negative_eps=negative_eps,
        rmp_iteration_id="b4-memory-guard-restricted-pool-no-cut",
    )
    cut_probe = build_cut_probe(
        data.task_ids,
        seed_columns,
        root_restricted.rmp.primal_columns,
        fleet_size=data.fleet_size,
        violation_eps=negative_eps,
    )
    cut_probe = dict(cut_probe)
    cut_probe["evaluation_scope"] = "safe_restricted_seed_pool_only"
    cut_probe["lower_bound_official"] = False
    cut_probe["can_certify"] = False
    diagnostic_round = run_restricted_cut_separation_round(
        data.task_ids,
        seed_columns,
        fleet_size=data.fleet_size,
        root_rmp=root_restricted.rmp,
        cut_probe=cut_probe,
        max_rows=max_live_cuts,
        violation_eps=negative_eps,
        include_fleet_lower_bound=False,
        add_violated_only=add_violated_only,
    )
    completion_policy = build_completion_bound_tail_policy(
        pruning_opt_in=False,
        cut_context_active=False,
    )
    dominance_report = build_cut_dominance_compatibility_report(CutContext())
    payload = _diagnostic_payload(
        data=data,
        b3=b3,
        root_no_cut=root_restricted,
        cut_probe=cut_probe,
        diagnostic_round=diagnostic_round,
        completion_policy=completion_policy,
        dominance_report=dominance_report,
        live_requested=False,
        note=(
            "B4A used a safe restricted seed-pool cut diagnostic because full direct-universe "
            "diagnostics failed dense RMP memory precheck. This is diagnostic only and cannot certify."
        ),
    )
    payload.update(
        {
            "certificate_scope": CertificateScope.DIAGNOSTIC_PRICING_FRONTIER.value,
            "exact_status": "NOT_SOLVED",
            "uses_true_dual_bpc_certificate": False,
            "root_lp_bound_official": False,
            "restricted_pool_cut_diagnostic": {
                "status": "RESTRICTED_POOL_CUT_DIAGNOSTIC_READY",
                "evaluation_scope": "safe_restricted_seed_pool_only",
                "seed_mode": seed_report.get("seed_mode"),
                "seed_builder": "reference_incumbent_plus_singletons",
                "seed_column_count": len(seed_columns),
                "root_rmp_status": root_restricted.rmp.status,
                "root_restricted_objective_bound": root_restricted.rmp.objective_bound,
                "lower_bound_official": False,
                "can_certify": False,
            },
            "full_universe_column_count": int(estimated_columns),
            "rmp_memory_precheck_failed": bool(precheck.get("rmp_memory_precheck_failed")),
            "rmp_memory_precheck_stage": precheck.get("rmp_memory_precheck_stage"),
            "rmp_memory_precheck_reason": precheck.get("rmp_memory_precheck_reason"),
            "rmp_memory_precheck_estimated_column_count": precheck.get("rmp_memory_precheck_estimated_column_count"),
            "rmp_memory_precheck_estimated_tableau_cells": precheck.get("rmp_memory_precheck_estimated_tableau_cells"),
            "rmp_memory_precheck_cell_limit": precheck.get("rmp_memory_precheck_cell_limit"),
        }
    )
    return payload


def _fail_closed_b3_placeholder() -> dict:
    return {
        "algorithm_status": AlgorithmStatus.BPC_INCOMPLETE_PRICING.value,
        "certificate_scope": CertificateScope.FEASIBLE_INCUMBENT_ONLY.value,
        "pricing_state": PricingState.INCOMPLETE_LIMIT.value,
        "uses_true_dual_bpc_certificate": False,
        "root_lp_bound": None,
        "incumbent_objective": None,
    }


def _selected_subset_row_payloads(
    cut_probe: dict,
    *,
    max_rows: int,
    violation_eps: float,
    add_violated_only: bool,
) -> tuple[dict, ...]:
    rows: list[dict] = []
    seen: set[str] = set()
    for candidate in cut_probe.get("subset_candidates", []) or []:
        violation = float(candidate.get("violation") or 0.0)
        if add_violated_only and violation <= abs(float(violation_eps)):
            continue
        payload = candidate.get("cut_context")
        if not isinstance(payload, dict):
            continue
        cut_id = str(payload.get("cut_id") or "")
        if not cut_id or cut_id in seen:
            continue
        seen.add(cut_id)
        rows.append(dict(payload))
        if len(rows) >= max(0, int(max_rows)):
            break
    return tuple(rows)


def _b3_ablation_payload(b3: dict, *, root_bound: float | None, certificate_scope: str) -> dict:
    b3_root = _float_or_none(b3.get("root_lp_bound"))
    objective_diff = None if root_bound is None or b3_root is None else round(float(root_bound) - float(b3_root), 9)
    return {
        "baseline": "B3_BRANCH_PRICE_TREE",
        "b3_algorithm_status": b3.get("algorithm_status"),
        "b3_certificate_scope": b3.get("certificate_scope"),
        "b3_root_lp_bound": b3_root,
        "b4_root_lp_bound": root_bound,
        "objective_diff_vs_B3": objective_diff,
        "certificate_scope_diff_vs_B3": (
            ""
            if str(b3.get("certificate_scope")) == str(certificate_scope)
            else f"{b3.get('certificate_scope')}->{certificate_scope}"
        ),
        "marginal_contribution": "B4 adds subset-row cut diagnostics and an opt-in live cut certificate path.",
    }


def _cut_aware_signature_summary(columns, cut_context: CutContext) -> dict:
    signatures = tuple(
        cut_aware_column_signature_from_journey(column, cut_context=cut_context)
        for column in columns
    )
    hashes = {signature.cut_coefficient_vector_hash for signature in signatures if signature.cut_coefficient_vector_hash}
    return {
        "schema_version": "lunar_ice_bpc.b4_cut_aware_signature_summary.v1",
        "column_count": len(signatures),
        "cut_context_active": not cut_context.empty,
        "distinct_cut_coefficient_vector_hash_count": len(hashes),
        "all_active_signatures_include_cut_hash": bool(
            cut_context.empty or all(signature.cut_coefficient_vector_hash for signature in signatures)
        ),
    }


def _bound_delta(before: float | None, after: float | None) -> float | None:
    if before is None or after is None:
        return None
    return round(float(after) - float(before), 9)


def _objectives_match(left: object, right: object, *, eps: float = 1.0e-6) -> bool:
    if left is None or right is None:
        return False
    return abs(float(left) - float(right)) <= abs(float(eps))


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
