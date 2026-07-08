"""Exact-safe runner scaffold."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

from lunar_ice_bpc.exact.certificates.bound_ledger import build_bound_ledger
from lunar_ice_bpc.exact.certificates.certificate_readiness import build_true_dual_certificate_readiness
from lunar_ice_bpc.exact.certificates.dual_binding import build_rmp_dual_binding_from_payload
from lunar_ice_bpc.exact.certificates.fixed_graph_pricing_proof import build_fixed_graph_pricing_proof
from lunar_ice_bpc.exact.certificates.node_bound import build_node_bound_certificate
from lunar_ice_bpc.exact.certificates.pricing_certificate import (
    build_pricing_certificate,
    select_effective_pricing_certificate,
)
from lunar_ice_bpc.exact.certificates.true_dual_pricing_tail import build_true_dual_pricing_tail
from lunar_ice_bpc.exact.bpc.pricing.status import is_direct_dp_time_limit_status
from lunar_ice_bpc.exact.core.cuts import CutContext
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import solve_restricted_journey_rmp
from lunar_ice_bpc.exact.pricing.journey_pricing import price_direct_journey_labels, run_direct_pricing_column_generation
from lunar_ice_bpc.exact.solver.direct_root_certificate import build_direct_root_certificate
from lunar_ice_bpc.exact.solver.branch_probe import build_branch_probe, build_fractional_branch_probe
from lunar_ice_bpc.exact.solver.branch_node_queue import (
    attach_incumbent_to_branch_node_queue,
    run_restricted_branch_node_queue,
)
from lunar_ice_bpc.exact.solver.branch_tree import build_branch_tree_probe
from lunar_ice_bpc.exact.solver.cut_probe import build_cut_probe
from lunar_ice_bpc.exact.solver.cut_separator import run_restricted_cut_separation_round
from lunar_ice_bpc.exact.solver.fixed_graph_pricing_closure import run_fixed_graph_pricing_closure
from lunar_ice_bpc.exact.solver.journey_driver import (
    JourneyBaselineResult,
    enumerate_canonical_journey_columns,
    solve_direct_journey_baseline,
    solve_small_journey_baseline,
)
from lunar_ice_bpc.exact.solver.lower_bounds import compute_analytic_lower_bound
from lunar_ice_bpc.exact.solver.seed_columns import SeededJourneyPool, build_seeded_journey_pool
from lunar_ice_bpc.exact.solver.column_pool import select_journey_column_pool
from lunar_ice_bpc.io.instance_io import read_json, validate_instance, write_json


def solve_reference(
    instance_path: str | Path,
    solution_path: str | Path,
    *,
    canonical_dp_max_tasks: int = 10,
    direct_baseline_max_tasks: int = 10,
    direct_baseline_time_limit_sec: float | None = None,
    restricted_rmp_enabled: bool = True,
    direct_pricing_enabled: bool = True,
    direct_pricing_max_tasks: int = 5,
    direct_pricing_cg_rounds: int = 1,
) -> dict:
    total_start = perf_counter()
    instance = read_json(instance_path)
    issues = validate_instance(instance)
    if issues:
        result = {
            "schema_version": "lunar_ice_bpc.solution.v1",
            "instance_id": instance.get("instance_id", Path(instance_path).stem),
            "status": "INVALID_INSTANCE",
            "exact_status": "NOT_SOLVED",
            "node_count": 0,
            "issues": issues,
        }
        write_json(solution_path, result)
        return result
    preprocess_start = perf_counter()
    data = load_lunar_ice_data(instance)
    analytic_lower_bound = compute_analytic_lower_bound(data)
    seeded_pool = build_seeded_journey_pool(data, instance.get("reference_solution") or {})
    preprocess_elapsed = perf_counter() - preprocess_start
    exact_start = perf_counter()
    canonical_baseline = solve_small_journey_baseline(data, max_exact_tasks=int(canonical_dp_max_tasks))
    direct_baseline = solve_direct_journey_baseline(
        data,
        max_exact_tasks=int(direct_baseline_max_tasks),
        wall_time_limit_sec=direct_baseline_time_limit_sec,
    )
    direct_root_certificate = build_direct_root_certificate(
        data,
        max_direct_tasks=_direct_root_max_tasks(
            direct_baseline_max_tasks=int(direct_baseline_max_tasks),
            direct_pricing_max_tasks=int(direct_pricing_max_tasks),
        ),
        integer_objective=direct_baseline.objective,
    )
    direct_root_payload = direct_root_certificate.to_payload()
    exact_elapsed = perf_counter() - exact_start
    baseline = direct_baseline if direct_baseline.status == "DIRECT_DP_BASELINE_OPTIMAL" else canonical_baseline
    if baseline.status in {"CANONICAL_DP_BASELINE_OPTIMAL", "DIRECT_DP_BASELINE_OPTIMAL"}:
        restricted_start = perf_counter()
        restricted_rmp = (
            _restricted_rmp_payload(
                data,
                max_exact_tasks=int(canonical_dp_max_tasks),
                direct_pricing_enabled=bool(direct_pricing_enabled),
                direct_pricing_max_tasks=int(direct_pricing_max_tasks),
                direct_pricing_cg_rounds=int(direct_pricing_cg_rounds),
                seeded_pool=None,
            )
            if bool(restricted_rmp_enabled)
            else {"enabled": False}
        )
        restricted_elapsed = perf_counter() - restricted_start
        baseline_journeys = [
            journey.to_solution_payload(vehicle_id=f"rover_{index + 1:02d}")
            for index, journey in enumerate(baseline.journeys)
        ]
        if baseline.status == "DIRECT_DP_BASELINE_OPTIMAL":
            incumbent = _incumbent_from_journeys(
                source="direct_dp_exact_baseline",
                objective=baseline.objective,
                journeys=baseline_journeys,
            )
        else:
            incumbent = _choose_incumbent(
                canonical_objective=baseline.objective,
                canonical_journeys=baseline_journeys,
                restricted_rmp=restricted_rmp,
            )
        _attach_incumbent_to_restricted_branch_queue(restricted_rmp, incumbent["objective"])
        bound_ledger = build_bound_ledger(
            incumbent_objective=incumbent["objective"],
            analytic_lower_bound=analytic_lower_bound,
            direct_root_certificate=direct_root_payload,
            restricted_rmp=restricted_rmp if bool(restricted_rmp_enabled) else None,
        )
        true_dual_pricing_tail = _true_dual_pricing_tail_payload(
            restricted_rmp if isinstance(restricted_rmp, dict) else {},
            direct_root_payload,
        )
        diagnostic_pricing_certificate = _pricing_certificate_payload(
            source="direct_dp_exact_baseline" if baseline.status == "DIRECT_DP_BASELINE_OPTIMAL" else "canonical_dp_baseline",
            restricted_rmp=restricted_rmp if isinstance(restricted_rmp, dict) else {},
        )
        pricing_certificate = select_effective_pricing_certificate(
            diagnostic_certificate=diagnostic_pricing_certificate,
            true_dual_pricing_tail=true_dual_pricing_tail,
        )
        node_bound_certificate = build_node_bound_certificate(
            incumbent_objective=incumbent["objective"],
            bound_ledger=bound_ledger,
            pricing_certificate=pricing_certificate,
            restricted_rmp=restricted_rmp if isinstance(restricted_rmp, dict) else {},
        ).to_payload()
        true_dual_certificate_readiness = build_true_dual_certificate_readiness(
            pricing_certificate=pricing_certificate,
            restricted_rmp=restricted_rmp if isinstance(restricted_rmp, dict) else {},
            node_bound_certificate=node_bound_certificate,
        )
        result = {
            "schema_version": "lunar_ice_bpc.solution.v1",
            "instance_id": instance["instance_id"],
            "status": baseline.status,
            "algorithm_status": baseline.status,
            "exact_status": baseline.exact_status,
            "exact_claim_scope": _exact_claim_scope(baseline.status),
            "certificate_scope": baseline.certificate_scope,
            "path_option_dominance_policy": baseline.path_option_dominance_policy,
            "path_option_dominance_filtered_count": baseline.path_option_dominance_filtered_count,
            "infeasibility_scope_if_any": baseline.infeasibility_scope_if_any,
            "bpc_certificate_status": pricing_certificate["status"],
            "uses_true_dual_bpc_certificate": pricing_certificate["uses_true_dual_bpc_certificate"],
            "pricing_certificate": pricing_certificate,
            "true_dual_pricing_tail": true_dual_pricing_tail,
            "node_bound_certificate": node_bound_certificate,
            "true_dual_certificate_readiness": true_dual_certificate_readiness,
            "objective": incumbent["objective"],
            "lower_bound": bound_ledger["official_lower_bound"],
            "lower_bound_source": bound_ledger["official_lower_bound_source"],
            "lower_bound_scope": bound_ledger["official_lower_bound_scope"],
            "relaxation_gap": bound_ledger["official_gap"],
            "gap_type": _gap_type(bound_ledger),
            "best_diagnostic_bound": bound_ledger["best_diagnostic_bound"],
            "best_diagnostic_bound_source": bound_ledger["best_diagnostic_bound_source"],
            "best_diagnostic_bound_scope": bound_ledger["best_diagnostic_bound_scope"],
            "canonical_objective": canonical_baseline.objective,
            "direct_exact_objective": direct_baseline.objective,
            "incumbent_source": incumbent["source"],
            "makespan_min": incumbent["makespan_min"],
            "covered_task_count": incumbent["covered_task_count"],
            "task_count": len(instance.get("tasks", {})),
            "node_count": 1,
            "journeys": incumbent["journeys"],
            "generated_journey_count": baseline.generated_journey_count,
            "generated_sortie_count": baseline.generated_sortie_count,
            "route_template_count": baseline.route_template_count,
            "pareto_label_count": baseline.pareto_label_count,
            "set_partition_state_count": baseline.set_partition_state_count,
            "solver_options": {
                "canonical_dp_max_tasks": int(canonical_dp_max_tasks),
                "direct_baseline_max_tasks": int(direct_baseline_max_tasks),
                "direct_baseline_time_limit_sec": (
                    None if direct_baseline_time_limit_sec is None else float(direct_baseline_time_limit_sec)
                ),
                "restricted_rmp_enabled": bool(restricted_rmp_enabled),
                "direct_pricing_enabled": bool(direct_pricing_enabled),
                "direct_pricing_max_tasks": int(direct_pricing_max_tasks),
                "direct_pricing_cg_rounds": int(direct_pricing_cg_rounds),
                "uses_true_dual_bpc_certificate": pricing_certificate["uses_true_dual_bpc_certificate"],
            },
            "canonical_baseline": _baseline_payload(canonical_baseline),
            "direct_exact_baseline": _baseline_payload(direct_baseline),
            "direct_root_certificate": direct_root_payload,
            "analytic_lower_bound": analytic_lower_bound.to_payload(),
            "bound_ledger": bound_ledger,
            "seeded_journey_pool": seeded_pool.to_payload(),
            "restricted_rmp": restricted_rmp,
            "timings": _timings_payload(
                preprocess_elapsed=preprocess_elapsed,
                exact_baseline_elapsed=exact_elapsed,
                restricted_rmp_elapsed=restricted_elapsed,
                total_elapsed=perf_counter() - total_start,
                canonical_baseline_elapsed=canonical_baseline.wall_time_sec,
                direct_baseline_elapsed=direct_baseline.wall_time_sec,
            ),
            "note": baseline.note,
        }
        write_json(solution_path, result)
        return result

    reporting_baseline = _fallback_baseline_for_reporting(direct_baseline, canonical_baseline)
    reference = dict(instance.get("reference_solution") or {})
    reference_journeys = list(reference.get("journeys", []))
    seeded_selection_start = perf_counter()
    seeded_selection = _seeded_pool_selection_payload(data, seeded_pool, max_states=50_000)
    seeded_selection_elapsed = perf_counter() - seeded_selection_start
    incumbent = _incumbent_from_journeys(
        source="reference_solution",
        objective=reference.get("objective"),
        journeys=reference_journeys,
    )
    restricted_start = perf_counter()
    restricted_rmp = (
        _restricted_rmp_payload(
            data,
            max_exact_tasks=int(canonical_dp_max_tasks),
            direct_pricing_enabled=bool(direct_pricing_enabled),
            direct_pricing_max_tasks=int(direct_pricing_max_tasks),
            direct_pricing_cg_rounds=int(direct_pricing_cg_rounds),
            seeded_pool=seeded_pool,
        )
        if bool(restricted_rmp_enabled)
        else {"enabled": False, "reason": reporting_baseline.status}
    )
    restricted_elapsed = perf_counter() - restricted_start
    if (
        seeded_selection.get("status") == "COLUMN_POOL_EXACT_COVER"
        and seeded_selection.get("objective") is not None
        and incumbent["objective"] is not None
        and float(seeded_selection["objective"]) < float(incumbent["objective"]) - 1.0e-9
    ):
        incumbent = _incumbent_from_journeys(
            source="seeded_column_pool",
            objective=seeded_selection["objective"],
            journeys=list(seeded_selection.get("journeys") or []),
        )
    _attach_incumbent_to_restricted_branch_queue(restricted_rmp, incumbent["objective"])
    bound_ledger = build_bound_ledger(
        incumbent_objective=incumbent["objective"],
        analytic_lower_bound=analytic_lower_bound,
        direct_root_certificate=direct_root_payload,
        restricted_rmp=restricted_rmp if bool(restricted_rmp_enabled) else None,
    )
    true_dual_pricing_tail = _true_dual_pricing_tail_payload(
        restricted_rmp if isinstance(restricted_rmp, dict) else {},
        direct_root_payload,
    )
    diagnostic_pricing_certificate = _pricing_certificate_payload(
        source="reference_or_seeded_fallback",
        restricted_rmp=restricted_rmp if isinstance(restricted_rmp, dict) else {},
    )
    pricing_certificate = select_effective_pricing_certificate(
        diagnostic_certificate=diagnostic_pricing_certificate,
        true_dual_pricing_tail=true_dual_pricing_tail,
    )
    node_bound_certificate = build_node_bound_certificate(
        incumbent_objective=incumbent["objective"],
        bound_ledger=bound_ledger,
        pricing_certificate=pricing_certificate,
        restricted_rmp=restricted_rmp if isinstance(restricted_rmp, dict) else {},
    ).to_payload()
    true_dual_certificate_readiness = build_true_dual_certificate_readiness(
        pricing_certificate=pricing_certificate,
        restricted_rmp=restricted_rmp if isinstance(restricted_rmp, dict) else {},
        node_bound_certificate=node_bound_certificate,
    )
    result = {
        "schema_version": "lunar_ice_bpc.solution.v1",
        "instance_id": instance["instance_id"],
        "status": reference.get("status", "NO_REFERENCE_SOLUTION"),
        "algorithm_status": reporting_baseline.status,
        "exact_status": reporting_baseline.exact_status,
        "exact_claim_scope": _exact_claim_scope(reporting_baseline.status),
        "certificate_scope": reporting_baseline.certificate_scope,
        "path_option_dominance_policy": reporting_baseline.path_option_dominance_policy,
        "path_option_dominance_filtered_count": reporting_baseline.path_option_dominance_filtered_count,
        "infeasibility_scope_if_any": reporting_baseline.infeasibility_scope_if_any,
        "bpc_certificate_status": pricing_certificate["status"],
        "uses_true_dual_bpc_certificate": pricing_certificate["uses_true_dual_bpc_certificate"],
        "pricing_certificate": pricing_certificate,
        "true_dual_pricing_tail": true_dual_pricing_tail,
        "node_bound_certificate": node_bound_certificate,
        "true_dual_certificate_readiness": true_dual_certificate_readiness,
        "objective": incumbent["objective"],
        "lower_bound": bound_ledger["official_lower_bound"],
        "lower_bound_source": bound_ledger["official_lower_bound_source"],
        "lower_bound_scope": bound_ledger["official_lower_bound_scope"],
        "relaxation_gap": bound_ledger["official_gap"],
        "gap_type": _gap_type(bound_ledger),
        "best_diagnostic_bound": bound_ledger["best_diagnostic_bound"],
        "best_diagnostic_bound_source": bound_ledger["best_diagnostic_bound_source"],
        "best_diagnostic_bound_scope": bound_ledger["best_diagnostic_bound_scope"],
        "incumbent_source": incumbent["source"],
        "canonical_objective": canonical_baseline.objective,
        "direct_exact_objective": direct_baseline.objective,
        "makespan_min": incumbent["makespan_min"],
        "covered_task_count": incumbent["covered_task_count"],
        "task_count": len(instance.get("tasks", {})),
        "node_count": 1,
        "journeys": incumbent["journeys"],
        "generated_journey_count": reporting_baseline.generated_journey_count,
        "generated_sortie_count": reporting_baseline.generated_sortie_count,
        "route_template_count": reporting_baseline.route_template_count,
        "pareto_label_count": reporting_baseline.pareto_label_count,
        "set_partition_state_count": reporting_baseline.set_partition_state_count,
        "solver_options": {
            "canonical_dp_max_tasks": int(canonical_dp_max_tasks),
            "direct_baseline_max_tasks": int(direct_baseline_max_tasks),
            "direct_baseline_time_limit_sec": (
                None if direct_baseline_time_limit_sec is None else float(direct_baseline_time_limit_sec)
            ),
            "restricted_rmp_enabled": bool(restricted_rmp_enabled),
            "direct_pricing_enabled": bool(direct_pricing_enabled),
            "direct_pricing_max_tasks": int(direct_pricing_max_tasks),
            "direct_pricing_cg_rounds": int(direct_pricing_cg_rounds),
            "uses_true_dual_bpc_certificate": pricing_certificate["uses_true_dual_bpc_certificate"],
        },
        "canonical_baseline": _baseline_payload(canonical_baseline),
        "direct_exact_baseline": _baseline_payload(direct_baseline),
        "direct_root_certificate": direct_root_payload,
        "analytic_lower_bound": analytic_lower_bound.to_payload(),
        "bound_ledger": bound_ledger,
        "seeded_journey_pool": seeded_pool.to_payload(),
        "seeded_column_pool_selection": seeded_selection,
        "restricted_rmp": restricted_rmp,
        "timings": _timings_payload(
            preprocess_elapsed=preprocess_elapsed,
            exact_baseline_elapsed=exact_elapsed,
            restricted_rmp_elapsed=restricted_elapsed,
            total_elapsed=perf_counter() - total_start,
            seeded_selection_elapsed=seeded_selection_elapsed,
            canonical_baseline_elapsed=canonical_baseline.wall_time_sec,
            direct_baseline_elapsed=direct_baseline.wall_time_sec,
        ),
        "note": (
            "Fallback incumbent from reference or seeded column pool; no exact BPC lower bound or certificate. "
            + reporting_baseline.note
        ),
    }
    write_json(solution_path, result)
    return result


def _pricing_certificate_payload(*, source: str, restricted_rmp: dict) -> dict:
    direct_pricing = restricted_rmp.get("direct_pricing") if isinstance(restricted_rmp, dict) else {}
    rmp_complete = bool(
        isinstance(restricted_rmp, dict)
        and restricted_rmp.get("status") == "RESTRICTED_RMP_OPTIMAL"
        and restricted_rmp.get("min_reduced_cost") is not None
    )
    pricing_complete = bool(
        isinstance(direct_pricing, dict)
        and direct_pricing.get("pricing_complete_for_all_tasks")
        and direct_pricing.get("status") == "DIRECT_LABEL_PRICED"
    )
    certificate = build_pricing_certificate(
        source=source,
        pricing_payload=direct_pricing if isinstance(direct_pricing, dict) else {},
        rmp_payload=restricted_rmp if isinstance(restricted_rmp, dict) else {},
        uses_true_dual_bpc_certificate=False,
        pricing_complete=pricing_complete,
        coverage_complete=False if not pricing_complete else rmp_complete,
        certificate_scope=str(restricted_rmp.get("pool_type") or "journey_pricing") if isinstance(restricted_rmp, dict) else "journey_pricing",
    )
    return certificate.to_payload()


def _true_dual_pricing_tail_payload(restricted_rmp: dict, direct_root_certificate: dict | None = None) -> dict:
    if not isinstance(restricted_rmp, dict) or not restricted_rmp:
        return build_true_dual_pricing_tail(
            source="no_restricted_rmp",
            pricing_payload={},
            rmp_payload={},
            certificate_scope="branch_price_node",
        )
    closure = restricted_rmp.get("fixed_graph_pricing_closure") or {}
    direct_pricing = restricted_rmp.get("direct_pricing") or {}
    if closure.get("status"):
        dual_binding = closure.get("dual_vector_binding") or {}
        closure_certifies = _fixed_graph_closure_has_true_dual_certificate(closure)
        pricing_payload = {
            "status": closure.get("status"),
            "min_reduced_cost": closure.get("last_best_reduced_cost"),
            "best_reduced_cost": closure.get("last_best_reduced_cost"),
            "pricing_complete_for_all_task_subsets": bool(closure.get("fixed_graph_no_negative_proved")),
            "coverage_complete": bool(closure.get("fixed_graph_no_negative_proved")),
            "uses_true_dual_bpc_certificate": bool(closure_certifies),
            "dual_vector_bound_to_rmp": bool(dual_binding.get("dual_vector_bound_to_rmp")),
            "dual_vector_fingerprint": dual_binding.get("dual_vector_fingerprint"),
        }
        return build_true_dual_pricing_tail(
            source=(
                "true_dual_fixed_graph_pricing_closure"
                if closure_certifies
                else "diagnostic_fixed_graph_pricing_closure"
            ),
            pricing_payload=pricing_payload,
            rmp_payload=restricted_rmp,
            certificate_scope="branch_price_node",
        )
    direct_root_certificate = direct_root_certificate or {}
    if direct_root_certificate.get("enabled"):
        dual_binding = build_rmp_dual_binding_from_payload(
            _direct_root_rmp_binding_payload(direct_root_certificate),
            source="direct_fixed_graph_root_lp",
            binding_scope=str(direct_root_certificate.get("certificate_scope") or "fixed_logical_graph_direct_root"),
            pricing_source=str(direct_root_certificate.get("status") or ""),
        )
        root_certifies = _direct_root_has_true_dual_certificate(direct_root_certificate, dual_binding)
        pricing_payload = {
            "status": direct_root_certificate.get("status"),
            "min_reduced_cost": direct_root_certificate.get("min_reduced_cost"),
            "best_reduced_cost": direct_root_certificate.get("min_reduced_cost"),
            "pricing_complete": root_certifies,
            "coverage_complete": root_certifies,
            "uses_true_dual_bpc_certificate": root_certifies,
            "dual_vector_bound_to_rmp": bool(dual_binding.get("dual_vector_bound_to_rmp")),
            "dual_vector_fingerprint": dual_binding.get("dual_vector_fingerprint"),
        }
        return build_true_dual_pricing_tail(
            source=(
                "true_dual_fixed_graph_root_lp"
                if root_certifies
                else "diagnostic_fixed_graph_root_lp"
            ),
            pricing_payload=pricing_payload,
            rmp_payload=_direct_root_rmp_binding_payload(direct_root_certificate),
            certificate_scope=str(direct_root_certificate.get("certificate_scope") or "fixed_logical_graph_direct_root"),
        )
    dual_binding = build_rmp_dual_binding_from_payload(
        restricted_rmp,
        source="restricted_rmp_direct_pricing",
        binding_scope=str(restricted_rmp.get("pool_type") or "restricted_column_pool"),
        pricing_source=str(direct_pricing.get("status") or ""),
    )
    pricing_payload = {
        "status": direct_pricing.get("status"),
        "min_reduced_cost": direct_pricing.get("best_reduced_cost"),
        "best_reduced_cost": direct_pricing.get("best_reduced_cost"),
        "pricing_complete_for_all_tasks": bool(direct_pricing.get("pricing_complete_for_all_tasks")),
        "uses_true_dual_bpc_certificate": False,
        "dual_vector_bound_to_rmp": bool(dual_binding.get("dual_vector_bound_to_rmp")),
        "dual_vector_fingerprint": dual_binding.get("dual_vector_fingerprint"),
    }
    return build_true_dual_pricing_tail(
        source="diagnostic_direct_pricing",
        pricing_payload=pricing_payload,
        rmp_payload=restricted_rmp,
        certificate_scope="branch_price_node",
    )


def _attach_incumbent_to_restricted_branch_queue(restricted_rmp: dict, incumbent_objective: float | None) -> None:
    if not isinstance(restricted_rmp, dict):
        return
    branch_node_queue = restricted_rmp.get("branch_node_queue")
    if not isinstance(branch_node_queue, dict):
        return
    restricted_rmp["branch_node_queue"] = attach_incumbent_to_branch_node_queue(
        branch_node_queue,
        incumbent_objective=incumbent_objective,
    )


def _exact_claim_scope(status: str) -> str:
    if status == "DIRECT_DP_BASELINE_OPTIMAL":
        return "fixed_logical_graph_exhaustive_direct_dp"
    if status == "CANONICAL_DP_BASELINE_OPTIMAL":
        return "restricted_canonical_path_universe"
    return "none"


def _fallback_baseline_for_reporting(
    direct_baseline: JourneyBaselineResult,
    canonical_baseline: JourneyBaselineResult,
) -> JourneyBaselineResult:
    if is_direct_dp_time_limit_status(direct_baseline.status):
        return direct_baseline
    direct_work = (
        int(direct_baseline.generated_journey_count)
        + int(direct_baseline.generated_sortie_count)
        + int(direct_baseline.route_template_count)
        + int(direct_baseline.pareto_label_count)
        + int(direct_baseline.set_partition_state_count)
    )
    canonical_work = (
        int(canonical_baseline.generated_journey_count)
        + int(canonical_baseline.generated_sortie_count)
        + int(canonical_baseline.route_template_count)
        + int(canonical_baseline.pareto_label_count)
        + int(canonical_baseline.set_partition_state_count)
    )
    if direct_work > canonical_work and direct_baseline.status != "SKIPPED_TOO_LARGE_FOR_DIRECT_DP_BASELINE":
        return direct_baseline
    return canonical_baseline


def _direct_root_max_tasks(*, direct_baseline_max_tasks: int, direct_pricing_max_tasks: int) -> int:
    return max(int(direct_pricing_max_tasks), min(int(direct_baseline_max_tasks), 10))


def _gap_type(bound_ledger: dict) -> str:
    source = bound_ledger.get("official_lower_bound_source")
    for record in bound_ledger.get("records", []) or []:
        if record.get("name") != source:
            continue
        if str(record.get("certificate_status") or "").startswith("BPC_"):
            return "official_bpc_node_bound"
    return "analytic_relaxation_not_bpc_certificate"


def _fixed_graph_closure_has_true_dual_certificate(closure: dict) -> bool:
    dual_binding = closure.get("dual_vector_binding") or {}
    completion_consistency = closure.get("completion_bound_consistency") or {}
    min_reduced_cost = _float_or_none(closure.get("last_best_reduced_cost"))
    return bool(
        closure.get("status") == "FIXED_GRAPH_PRICING_CLOSED"
        and closure.get("fixed_graph_no_negative_proved") is True
        and closure.get("last_pricing_complete_for_all_task_subsets") is True
        and closure.get("final_rmp_status") == "RESTRICTED_RMP_OPTIMAL"
        and dual_binding.get("dual_vector_bound_to_rmp") is True
        and completion_consistency.get("consistent") is True
        and min_reduced_cost is not None
        and min_reduced_cost >= -1.0e-6
    )


def _direct_root_has_true_dual_certificate(direct_root_certificate: dict, dual_binding: dict) -> bool:
    return False


def _direct_root_rmp_binding_payload(direct_root_certificate: dict) -> dict:
    return {
        "status": "RESTRICTED_RMP_OPTIMAL"
        if direct_root_certificate.get("enabled")
        and direct_root_certificate.get("lp_bound") is not None
        else "UNKNOWN",
        "exact_status": direct_root_certificate.get("exact_status"),
        "objective_bound": direct_root_certificate.get("lp_bound"),
        "min_reduced_cost": direct_root_certificate.get("min_reduced_cost"),
        "task_cover_duals": direct_root_certificate.get("task_cover_duals") or {},
        "fleet_dual": direct_root_certificate.get("fleet_dual"),
        "cut_duals": {},
        "branch_context": {},
        "cut_context": {},
        "cut_rows_active": False,
    }


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 9)
    except (TypeError, ValueError):
        return None


def _timings_payload(
    *,
    preprocess_elapsed: float,
    exact_baseline_elapsed: float,
    restricted_rmp_elapsed: float,
    total_elapsed: float,
    seeded_selection_elapsed: float | None = None,
    canonical_baseline_elapsed: float | None = None,
    direct_baseline_elapsed: float | None = None,
) -> dict:
    payload = {
        "preprocess_wall_time_sec": round(float(preprocess_elapsed), 6),
        "exact_baseline_wall_time_sec": round(float(exact_baseline_elapsed), 6),
        "restricted_rmp_wall_time_sec": round(float(restricted_rmp_elapsed), 6),
        "total_solve_wall_time_sec": round(float(total_elapsed), 6),
    }
    if seeded_selection_elapsed is not None:
        payload["seeded_selection_wall_time_sec"] = round(float(seeded_selection_elapsed), 6)
    if canonical_baseline_elapsed is not None:
        payload["canonical_baseline_wall_time_sec"] = round(float(canonical_baseline_elapsed), 6)
    if direct_baseline_elapsed is not None:
        payload["direct_baseline_wall_time_sec"] = round(float(direct_baseline_elapsed), 6)
    return payload


def _baseline_payload(result: JourneyBaselineResult) -> dict:
    return {
        "status": result.status,
        "algorithm_status": result.status,
        "exact_status": result.exact_status,
        "certificate_scope": result.certificate_scope,
        "objective": result.objective,
        "wall_time_sec": result.wall_time_sec,
        "generated_journey_count": result.generated_journey_count,
        "generated_sortie_count": result.generated_sortie_count,
        "route_template_count": result.route_template_count,
        "pareto_label_count": result.pareto_label_count,
        "set_partition_state_count": result.set_partition_state_count,
        "path_option_dominance_policy": result.path_option_dominance_policy,
        "path_option_dominance_filtered_count": result.path_option_dominance_filtered_count,
        "reference_solution_upper_bound": result.reference_solution_upper_bound,
        "reference_solution_upper_bound_source": result.reference_solution_upper_bound_source,
        "direct_bound_pruning_root_bound": result.direct_bound_pruning_root_bound,
        "direct_bound_pruning_active": result.direct_bound_pruning_active,
        "journey_label_bound_pruned_count": result.journey_label_bound_pruned_count,
        "infeasibility_scope_if_any": result.infeasibility_scope_if_any,
        "note": result.note,
    }


def _choose_incumbent(*, canonical_objective: float | None, canonical_journeys: list[dict], restricted_rmp: dict) -> dict:
    source = "canonical_dp_baseline"
    objective = canonical_objective
    journeys = canonical_journeys
    direct_incumbent = (
        (restricted_rmp.get("direct_column_generation") or {}).get("integer_incumbent")
        if isinstance(restricted_rmp, dict)
        else None
    )
    if isinstance(direct_incumbent, dict) and direct_incumbent.get("status") == "COLUMN_POOL_EXACT_COVER":
        direct_objective = direct_incumbent.get("objective")
        if direct_objective is not None and (objective is None or float(direct_objective) < float(objective) - 1.0e-9):
            source = "direct_cg_column_pool"
            objective = float(direct_objective)
            journeys = list(direct_incumbent.get("journeys") or [])
    return {
        "source": source,
        "objective": round(float(objective), 6) if objective is not None else None,
        "journeys": journeys,
        "makespan_min": _journey_payload_makespan(journeys),
        "covered_task_count": len(_journey_payload_tasks(journeys)),
    }


def _incumbent_from_journeys(*, source: str, objective: float | None, journeys: list[dict]) -> dict:
    return {
        "source": source,
        "objective": round(float(objective), 6) if objective is not None else None,
        "journeys": journeys,
        "makespan_min": _journey_payload_makespan(journeys),
        "covered_task_count": len(_journey_payload_tasks(journeys)),
    }


def _seeded_pool_selection_payload(data, seeded_pool: SeededJourneyPool, *, max_states: int) -> dict:
    selection = select_journey_column_pool(
        data.task_ids,
        seeded_pool.columns,
        fleet_size=data.fleet_size,
        max_states=int(max_states),
    )
    return {
        "status": selection.status,
        "objective": selection.objective,
        "journey_count": len(selection.columns),
        "candidate_column_count": selection.candidate_column_count,
        "unique_task_set_count": selection.unique_task_set_count,
        "state_count": selection.state_count,
        "max_states": int(max_states),
        "journeys": [
            column.to_solution_payload(vehicle_id=f"seeded_pool_{index + 1:02d}")
            for index, column in enumerate(selection.columns)
        ],
        "note": selection.note,
    }


def _journey_payload_makespan(journeys: list[dict]) -> float:
    return round(
        max(
            (
                float(sortie.get("end_time", 0.0))
                for journey in journeys
                for sortie in journey.get("sorties", [])
            ),
            default=0.0,
        ),
        6,
    )


def _journey_payload_tasks(journeys: list[dict]) -> set[str]:
    return {
        str(task_id)
        for journey in journeys
        for sortie in journey.get("sorties", [])
        for task_id in sortie.get("tasks", [])
    }


def _restricted_rmp_payload(
    data,
    *,
    max_exact_tasks: int,
    direct_pricing_enabled: bool,
    direct_pricing_max_tasks: int,
    direct_pricing_cg_rounds: int,
    seeded_pool: SeededJourneyPool | None = None,
) -> dict:
    try:
        if len(data.task_ids) <= int(max_exact_tasks):
            universe = enumerate_canonical_journey_columns(data, max_exact_tasks=int(max_exact_tasks))
            columns = universe.columns
            pool_type = "canonical_path_universe"
            pool_payload = {
                "column_count": len(columns),
                "generated_sortie_count": universe.generated_sortie_count,
                "route_template_count": universe.route_template_count,
                "pareto_label_count": universe.pareto_label_count,
            }
            direct_cg_allowed = True
        elif seeded_pool is not None and seeded_pool.columns:
            columns = seeded_pool.columns
            pool_type = "seeded_reference_singleton_pool"
            pool_payload = seeded_pool.to_payload()
            direct_cg_allowed = False
        else:
            return {
                "enabled": True,
                "status": "NO_RESTRICTED_RMP_POOL",
                "exact_status": "NOT_SOLVED",
                "pool_type": "none",
                "note": "No canonical or seeded journey-column pool is available.",
            }
        rmp = solve_restricted_journey_rmp(
            data.task_ids,
            columns,
            fleet_size=data.fleet_size,
        )
        branch_probe = build_branch_probe(data.task_ids, columns, max_candidates=10)
        fractional_branch_probe = build_fractional_branch_probe(
            data.task_ids,
            rmp.primal_columns,
            columns,
            max_candidates=10,
        )
        cut_probe = build_cut_probe(
            data.task_ids,
            columns,
            rmp.primal_columns,
            fleet_size=data.fleet_size,
            max_subset_candidates=10,
        )
        cut_separation_probe = run_restricted_cut_separation_round(
            data.task_ids,
            columns,
            fleet_size=data.fleet_size,
            root_rmp=rmp,
            cut_probe=cut_probe,
            max_rows=3,
            include_fleet_lower_bound=False,
        )
        fixed_graph_pricing_proof = (
            build_fixed_graph_pricing_proof(
                data,
                rmp.duals,
                max_direct_tasks=int(direct_pricing_max_tasks),
                cut_context=CutContext(),
            )
            if bool(direct_pricing_enabled)
            else {"enabled": False, "reason": "direct_pricing_disabled"}
        )
        fixed_graph_pricing_closure = (
            run_fixed_graph_pricing_closure(
                data,
                columns,
                max_direct_tasks=int(direct_pricing_max_tasks),
                max_rounds=3,
                cut_context=CutContext(),
            )
            if bool(direct_pricing_enabled) and len(data.task_ids) <= int(direct_pricing_max_tasks)
            else {"enabled": False, "reason": "task_count_exceeds_direct_pricing_max_tasks_or_disabled"}
        )
        branch_tree_probe = build_branch_tree_probe(
            columns,
            branch_probe,
            root_context=rmp.branch_context,
            max_branch_pairs=1,
            task_ids=data.task_ids,
            fleet_size=data.fleet_size,
            evaluate_restricted_rmp=True,
            max_child_evaluations=2,
        )
        branch_node_queue = run_restricted_branch_node_queue(
            data.task_ids,
            columns,
            fleet_size=data.fleet_size,
            max_nodes=7,
            max_depth=2,
            max_candidates_per_node=1,
            root_context=rmp.branch_context,
            data=data,
            direct_pricing_probe_enabled=bool(direct_pricing_enabled),
            direct_pricing_max_tasks=int(direct_pricing_max_tasks),
            direct_pricing_max_candidate_sets=2,
            max_pricing_probe_nodes=3,
        )
        direct_column_generation = (
            run_direct_pricing_column_generation(
                data,
                columns,
                max_direct_tasks=int(direct_pricing_max_tasks),
                max_rounds=int(direct_pricing_cg_rounds),
            )
            if bool(direct_pricing_enabled) and direct_cg_allowed
            else {
                "enabled": False,
                "reason": "seeded_large_pool_uses_direct_pricing_probe_only" if not direct_cg_allowed else "direct_pricing_disabled",
            }
        )
        direct_pricing = (
            direct_column_generation.get("first_direct_pricing")
            if isinstance(direct_column_generation, dict) and direct_column_generation.get("first_direct_pricing") is not None
            else (
                price_direct_journey_labels(
                    data,
                    rmp.duals,
                    max_direct_tasks=int(direct_pricing_max_tasks),
                    max_candidate_sets=8 if not direct_cg_allowed else None,
                )
                if bool(direct_pricing_enabled)
                else {"enabled": False}
            )
        )
    except Exception as exc:
        return {
            "enabled": True,
            "status": "RESTRICTED_RMP_ERROR",
            "exact_status": "NOT_SOLVED",
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "enabled": True,
        "status": rmp.status,
        "exact_status": rmp.exact_status,
        "pool_type": pool_type,
        "pool": pool_payload,
        "objective_bound": rmp.objective_bound,
        "active_column_count": rmp.active_column_count,
        "universe_column_count": rmp.universe_column_count,
        "iteration_count": rmp.iteration_count,
        "added_column_count": rmp.added_column_count,
        "min_reduced_cost": rmp.min_reduced_cost,
        "fleet_dual": rmp.duals.fleet_limit,
        "task_cover_duals": dict(rmp.duals.cover),
        "primal_columns": list(rmp.primal_columns),
        "primal_active_column_count": len(rmp.primal_columns),
        "primal_cover_residual_max": rmp.primal_cover_residual_max,
        "primal_fleet_usage": rmp.primal_fleet_usage,
        "branch_context": rmp.branch_context,
        "branch_filtered_column_count": rmp.branch_filtered_column_count,
        "cut_context": rmp.cut_context or CutContext().to_payload(),
        "cut_rows_active": rmp.cut_rows_active,
        "cut_duals": dict(rmp.duals.cuts or {}),
        "primal_cut_activities": list(rmp.primal_cut_activities),
        "primal_cut_violation_max": rmp.primal_cut_violation_max,
        "cut_probe": cut_probe,
        "cut_separation_probe": cut_separation_probe,
        "fixed_graph_pricing_proof": fixed_graph_pricing_proof,
        "fixed_graph_pricing_closure": fixed_graph_pricing_closure,
        "branch_probe": branch_probe,
        "fractional_branch_probe": fractional_branch_probe,
        "branch_tree_probe": branch_tree_probe,
        "branch_node_queue": branch_node_queue,
        "pricing_history": list(rmp.pricing_history),
        "direct_pricing": direct_pricing,
        "direct_column_generation": direct_column_generation,
        "note": rmp.note,
    }
