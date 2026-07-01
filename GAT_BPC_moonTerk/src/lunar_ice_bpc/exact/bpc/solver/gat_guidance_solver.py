"""B5 shadow-only guidance baseline with do-no-harm gates."""

from __future__ import annotations

from typing import Iterable, Mapping

from lunar_ice_bpc.exact.bpc.guidance.shadow import (
    GuidanceHint,
    all_guidance_bundle_hints,
    build_guidance_output_bundle,
    build_guidance_output_bundle_from_payload,
    build_guidance_ordering_report,
    build_guidance_shadow_accounting,
    guidance_head_hints,
)
from lunar_ice_bpc.exact.bpc.pricing.status import AlgorithmStatus, CertificateScope, PricingState
from lunar_ice_bpc.exact.bpc.solver.cut_formulation_solver import solve_b4_cut_formulation_baseline
from lunar_ice_bpc.exact.core.data import LunarIceData


def solve_b5_gat_guidance_shadow_baseline(
    data: LunarIceData,
    *,
    guidance_hints: Iterable[GuidanceHint | Mapping[str, object]] = tuple(),
    true_rc_candidates: Iterable[Mapping[str, object]] = tuple(),
    pricing_candidates: Iterable[Mapping[str, object]] = tuple(),
    branch_candidates: Iterable[Mapping[str, object]] = tuple(),
    harvest_candidates: Iterable[Mapping[str, object]] = tuple(),
    guidance_output_bundle: Mapping[str, object] | None = None,
    enabled_ordering_modes: Iterable[str] = tuple(),
    no_guidance_workload: Mapping[str, object] | None = None,
    guidance_workload: Mapping[str, object] | None = None,
    release_before_certificate: bool = True,
    max_direct_tasks: int = 5,
    max_rounds: int = 8,
    negative_eps: float = 1.0e-6,
) -> dict:
    """Run B5 shadow guidance and compare against B4 no-guidance semantics."""

    b4 = solve_b4_cut_formulation_baseline(
        data,
        max_direct_tasks=max_direct_tasks,
        max_rounds=max_rounds,
        negative_eps=negative_eps,
        live_subset_rows=False,
    )
    output_bundle = (
        build_guidance_output_bundle_from_payload(guidance_output_bundle)
        if guidance_output_bundle is not None
        else build_guidance_output_bundle(
            pricing_priority_head=guidance_hints,
            branch_priority_head=guidance_hints,
            harvest_priority_head=guidance_hints,
        )
    )
    all_shadow_hints = (
        all_guidance_bundle_hints(output_bundle)
        if guidance_output_bundle is not None
        else guidance_hints
    )
    shadow = build_guidance_shadow_accounting(
        all_shadow_hints,
        true_rc_candidates,
        negative_eps=negative_eps,
        release_before_certificate=release_before_certificate,
    )
    enabled_modes = {str(mode) for mode in enabled_ordering_modes}
    ordering_reports = {
        "pricing": build_guidance_ordering_report(
            candidate_kind="pricing",
            candidates=pricing_candidates,
            hints=guidance_head_hints(output_bundle, "pricing_priority_head"),
            enabled="pricing" in enabled_modes or "all" in enabled_modes,
        ),
        "branch": build_guidance_ordering_report(
            candidate_kind="branch",
            candidates=branch_candidates,
            hints=guidance_head_hints(output_bundle, "branch_priority_head"),
            enabled="branch" in enabled_modes or "all" in enabled_modes,
        ),
        "harvest": build_guidance_ordering_report(
            candidate_kind="harvest",
            candidates=harvest_candidates,
            hints=guidance_head_hints(output_bundle, "harvest_priority_head"),
            enabled="harvest" in enabled_modes or "all" in enabled_modes,
        ),
    }
    ordering_candidate_sets_preserved = all(
        bool(report["candidate_set_preserved"]) for report in ordering_reports.values()
    )
    blocked = bool(shadow["certificate_blocked_by_delayed_negative"])
    if blocked:
        algorithm_status = AlgorithmStatus.BPC_INCOMPLETE_PRICING.value
        certificate_scope = CertificateScope.FEASIBLE_INCUMBENT_ONLY.value
        exact_status = "NOT_SOLVED"
        pricing_state = PricingState.INCOMPLETE_LIMIT.value
        uses_true_dual = False
    else:
        algorithm_status = str(b4.get("algorithm_status"))
        certificate_scope = str(b4.get("certificate_scope"))
        exact_status = str(b4.get("exact_status"))
        pricing_state = str(b4.get("pricing_state"))
        uses_true_dual = bool(b4.get("uses_true_dual_bpc_certificate"))
    objective_diff = 0.0 if not blocked else None
    certificate_scope_diff = "" if certificate_scope == str(b4.get("certificate_scope")) else f"{b4.get('certificate_scope')}->{certificate_scope}"
    incomplete_diff = int(algorithm_status == AlgorithmStatus.BPC_INCOMPLETE_PRICING.value) - int(
        b4.get("algorithm_status") == AlgorithmStatus.BPC_INCOMPLETE_PRICING.value
    )
    do_no_harm_issues = []
    if blocked:
        do_no_harm_issues.append("proof_debt_not_released_before_certificate")
    if certificate_scope_diff:
        do_no_harm_issues.append("certificate_scope_changed_by_guidance")
    if incomplete_diff > 0:
        do_no_harm_issues.append("additional_bpc_incomplete_caused_by_guidance")
    if int(shadow["permanent_negative_drop_count"]) > 0:
        do_no_harm_issues.append("true_rc_negative_permanently_dropped")
    if not ordering_candidate_sets_preserved:
        do_no_harm_issues.append("guidance_ordering_dropped_candidate")
    do_no_harm_pass = not do_no_harm_issues
    mode = "shadow_only" if not enabled_modes else "ordering_opt_in"
    pricing_enabled = bool(ordering_reports["pricing"]["enabled"])
    branch_enabled = bool(ordering_reports["branch"]["enabled"])
    harvest_enabled = bool(ordering_reports["harvest"]["enabled"])
    workload_report = _build_workload_ablation_report(
        no_guidance_workload=no_guidance_workload,
        guidance_workload=guidance_workload,
        do_no_harm_pass=do_no_harm_pass,
    )
    return {
        "schema_version": "lunar_ice_bpc.b5_gat_guidance_shadow_baseline.v1",
        "instance_id": data.instance_id,
        "mode": mode,
        "enabled_ordering_modes": sorted(enabled_modes),
        "algorithm_status": algorithm_status,
        "certificate_scope": certificate_scope,
        "exact_status": exact_status,
        "pricing_state": pricing_state,
        "uses_true_dual_bpc_certificate": uses_true_dual,
        "b4_ablation": {
            "baseline": "B4_CUT_FORMULATION_NO_GAT",
            "b4_algorithm_status": b4.get("algorithm_status"),
            "b4_certificate_scope": b4.get("certificate_scope"),
            "b4_exact_status": b4.get("exact_status"),
            "objective_diff": objective_diff,
            "certificate_scope_diff": certificate_scope_diff,
            "BPC_TREE_OPTIMAL_count_diff": int(certificate_scope == CertificateScope.BPC_TREE_OPTIMAL.value) - int(
                b4.get("certificate_scope") == CertificateScope.BPC_TREE_OPTIMAL.value
            ),
            "BPC_INCOMPLETE_count_diff": incomplete_diff,
            "wall_time_diff": workload_report["diffs"]["wall_time"],
            "pricing_call_diff": workload_report["diffs"]["pricing_calls"],
            "final_judge_call_diff": workload_report["diffs"]["final_judge_calls"],
            "generated_label_diff": workload_report["diffs"]["generated_labels"],
            "RMP_iteration_diff": workload_report["diffs"]["rmp_iterations"],
            "node_count_diff": workload_report["diffs"]["node_count"],
        },
        "workload_ablation": workload_report,
        "guidance_output_bundle": output_bundle,
        "ordering_ablation": {
            "pricing_ordering_opt_in": ordering_reports["pricing"],
            "branch_ordering_opt_in": ordering_reports["branch"],
            "harvest_ordering_opt_in": ordering_reports["harvest"],
            "all_candidate_sets_preserved": bool(ordering_candidate_sets_preserved),
            "enabled_ordering_count": sum(
                1 for report in ordering_reports.values() if report["enabled"]
            ),
            "mutates_solver": False,
            "can_certify": False,
            "exact_status_effect": "none",
        },
        "guidance_shadow_accounting": shadow,
        "shadow_label_manifest": shadow["shadow_label_manifest"],
        "proof_debt_metrics": {
            "delayed_negative_count": shadow["delayed_negative_count"],
            "released_before_certificate_count": shadow["released_before_certificate_count"],
            "rechecked_before_certificate_count": shadow["rechecked_before_certificate_count"],
            "certificate_blocked_by_delayed_negative": shadow["certificate_blocked_by_delayed_negative"],
            "delay_budget_exhausted_count": shadow["delay_budget_exhausted_count"],
            "delayed_negative_caused_extra_cg_round_count": shadow["delayed_negative_caused_extra_cg_round_count"],
            "proof_debt_queue_empty_before_certificate": not shadow["proof_debt_queue"]["blocks_certificate"],
        },
        "safety_metrics": {
            "objective_unchanged": objective_diff == 0.0,
            "certificate_scope_unchanged": certificate_scope_diff == "",
            "no_permanent_negative_drop": int(shadow["permanent_negative_drop_count"]) == 0,
            "ordering_candidate_sets_preserved": bool(ordering_candidate_sets_preserved),
            "no_extra_incomplete_caused_by_delay": incomplete_diff <= 0,
            "proof_debt_cleared_before_certificate": not shadow["proof_debt_queue"]["blocks_certificate"],
            "delayed_true_negative_release_rate": (
                1.0
                if int(shadow["delayed_negative_count"]) == 0
                else round(
                    float(shadow["released_before_certificate_count"]) / float(shadow["delayed_negative_count"]),
                    9,
                )
            ),
            "false_safe_rate": 0.0,
        },
        "performance_metrics": {
            "eligible_for_performance_claim": bool(do_no_harm_pass),
            "pricing_ordering_enabled": pricing_enabled,
            "branch_ordering_enabled": branch_enabled,
            "harvest_ordering_enabled": harvest_enabled,
            "wall_time_diff": workload_report["diffs"]["wall_time"],
            "pricing_call_diff": workload_report["diffs"]["pricing_calls"],
            "final_judge_call_diff": workload_report["diffs"]["final_judge_calls"],
            "generated_label_diff": workload_report["diffs"]["generated_labels"],
            "RMP_iteration_diff": workload_report["diffs"]["rmp_iterations"],
            "node_count_diff": workload_report["diffs"]["node_count"],
            "performance_success": workload_report["performance_success"],
            "performance_success_reasons": workload_report["success_reasons"],
            "performance_gate_issues": workload_report["gate_issues"],
        },
        "do_no_harm_pass": bool(do_no_harm_pass),
        "do_no_harm_issues": do_no_harm_issues,
        "guidance_can_construct_certificate": False,
        "guidance_can_mutate_exact_state": False,
        "mutates_solver": False,
        "can_certify": False,
        "exact_status_effect": "none",
        "note": (
            "B5 shadow guidance preserves B4 objective and certificate semantics."
            if do_no_harm_pass
            else "B5 guidance failed do-no-harm and cannot leave shadow mode."
        ),
    }


def run_b5_guidance_ablation_suite(
    rows: Iterable[Mapping[str, object]],
    *,
    max_direct_tasks: int = 5,
    max_rounds: int = 8,
    negative_eps: float = 1.0e-6,
) -> dict:
    """Evaluate B5 do-no-harm and workload gates over explicit split rows."""

    evaluated_rows: list[dict] = []
    for row_index, row in enumerate(rows):
        data = row.get("data")
        if not isinstance(data, LunarIceData):
            raise TypeError("each B5 suite row must provide a LunarIceData under key 'data'")
        result = solve_b5_gat_guidance_shadow_baseline(
            data,
            guidance_hints=row.get("guidance_hints") or tuple(),
            true_rc_candidates=row.get("true_rc_candidates") or tuple(),
            pricing_candidates=row.get("pricing_candidates") or tuple(),
            branch_candidates=row.get("branch_candidates") or tuple(),
            harvest_candidates=row.get("harvest_candidates") or tuple(),
            guidance_output_bundle=(
                row.get("guidance_output_bundle")
                if isinstance(row.get("guidance_output_bundle"), Mapping)
                else None
            ),
            enabled_ordering_modes=row.get("enabled_ordering_modes") or tuple(),
            no_guidance_workload=row.get("no_guidance_workload") if isinstance(row.get("no_guidance_workload"), Mapping) else None,
            guidance_workload=row.get("guidance_workload") if isinstance(row.get("guidance_workload"), Mapping) else None,
            release_before_certificate=bool(row.get("release_before_certificate", True)),
            max_direct_tasks=int(row.get("max_direct_tasks") or max_direct_tasks),
            max_rounds=int(row.get("max_rounds") or max_rounds),
            negative_eps=float(row.get("negative_eps") or negative_eps),
        )
        split_keys = {
            "instance": str(row.get("instance") or data.instance_id),
            "scale": str(row.get("scale") or data.scale),
            "seed_family": str(row.get("seed_family") or _seed_family_from_instance_id(data.instance_id)),
        }
        evaluated_rows.append(
            {
                "row_index": int(row_index),
                "instance_id": data.instance_id,
                "split_keys": split_keys,
                "mode": result["mode"],
                "algorithm_status": result["algorithm_status"],
                "certificate_scope": result["certificate_scope"],
                "exact_status": result["exact_status"],
                "do_no_harm_pass": result["do_no_harm_pass"],
                "do_no_harm_issues": list(result["do_no_harm_issues"]),
                "performance_success": result["workload_ablation"]["performance_success"],
                "performance_gate_issues": list(result["workload_ablation"]["gate_issues"]),
                "objective_diff": result["b4_ablation"]["objective_diff"],
                "certificate_scope_diff": result["b4_ablation"]["certificate_scope_diff"],
                "BPC_TREE_OPTIMAL_count_diff": result["b4_ablation"]["BPC_TREE_OPTIMAL_count_diff"],
                "BPC_INCOMPLETE_count_diff": result["b4_ablation"]["BPC_INCOMPLETE_count_diff"],
                "workload_diffs": dict(result["workload_ablation"]["diffs"]),
                "proof_debt_metrics": dict(result["proof_debt_metrics"]),
                "guidance_output_head_counts": dict(result["guidance_output_bundle"]["head_counts"]),
                "guidance_output_required_heads_present": result["guidance_output_bundle"][
                    "required_heads_present"
                ],
                "result": result,
            }
        )
    do_no_harm_fail_rows = [row for row in evaluated_rows if not row["do_no_harm_pass"]]
    certificate_diff_rows = [row for row in evaluated_rows if row["certificate_scope_diff"]]
    additional_incomplete_rows = [
        row for row in evaluated_rows if int(row["BPC_INCOMPLETE_count_diff"] or 0) > 0
    ]
    performance_success_rows = [row for row in evaluated_rows if row["performance_success"]]
    return {
        "schema_version": "lunar_ice_bpc.b5_guidance_ablation_suite.v1",
        "row_count": len(evaluated_rows),
        "split_policy": {
            "main_split_keys": ["instance", "scale", "seed_family"],
            "random_row_split_allowed_for_debug_only": True,
            "random_row_split_is_main_claim": False,
        },
        "suite_do_no_harm_pass": not do_no_harm_fail_rows,
        "suite_performance_success_count": len(performance_success_rows),
        "do_no_harm_pass_count": len(evaluated_rows) - len(do_no_harm_fail_rows),
        "do_no_harm_fail_count": len(do_no_harm_fail_rows),
        "certificate_scope_diff_count": len(certificate_diff_rows),
        "additional_bpc_incomplete_count": len(additional_incomplete_rows),
        "mode_counts": _count_by(evaluated_rows, "mode"),
        "certificate_scope_counts": _count_by(evaluated_rows, "certificate_scope"),
        "scale_counts": _count_by_split(evaluated_rows, "scale"),
        "seed_family_counts": _count_by_split(evaluated_rows, "seed_family"),
        "performance_success_instance_ids": [row["instance_id"] for row in performance_success_rows],
        "do_no_harm_fail_instance_ids": [row["instance_id"] for row in do_no_harm_fail_rows],
        "rows": evaluated_rows,
        "note": "B5 suite aggregates exact-safe guidance A/B rows; GAT never contributes certificate evidence.",
    }


def _build_workload_ablation_report(
    *,
    no_guidance_workload: Mapping[str, object] | None,
    guidance_workload: Mapping[str, object] | None,
    do_no_harm_pass: bool,
) -> dict:
    baseline = _normalize_workload(no_guidance_workload)
    guided = _normalize_workload(guidance_workload)
    observation_source = _workload_metadata(
        "observation_source",
        no_guidance_workload,
        guidance_workload,
        default="not_observed",
    )
    workload_units = _workload_metadata(
        "workload_units",
        no_guidance_workload,
        guidance_workload,
        default="solver_workload",
    )
    diffs = {
        key: _metric_diff(baseline.get(key), guided.get(key))
        for key in _WORKLOAD_KEYS
    }
    observed = any(value is not None for value in diffs.values())
    improving_keys = tuple(
        key
        for key, value in diffs.items()
        if value is not None and float(value) < 0.0
    )
    regressing_keys = tuple(
        key
        for key, value in diffs.items()
        if value is not None and float(value) > 0.0
    )
    gate_issues: list[str] = []
    if not do_no_harm_pass:
        gate_issues.append("safety_gate_failed")
    if not observed:
        gate_issues.append("workload_ablation_missing")
    if regressing_keys:
        gate_issues.append("workload_metric_regressed:" + ",".join(regressing_keys))
    if observed and not improving_keys:
        gate_issues.append("no_workload_metric_improved")
    performance_success = bool(do_no_harm_pass and observed and improving_keys and not regressing_keys)
    return {
        "schema_version": "lunar_ice_bpc.b5_workload_ablation.v1",
        "baseline_name": "B4_NO_GAT",
        "guided_name": "B5_GAT_GUIDANCE",
        "baseline_workload": baseline,
        "guided_workload": guided,
        "observation_source": observation_source,
        "workload_units": workload_units,
        "diffs": diffs,
        "workload_observed": bool(observed),
        "improving_metrics": list(improving_keys),
        "regressing_metrics": list(regressing_keys),
        "performance_success": performance_success,
        "success_reasons": (
            [
                "safety_success",
                *[f"{key}_decreased" for key in improving_keys],
            ]
            if performance_success
            else []
        ),
        "gate_issues": gate_issues,
        "note": (
            "Performance may be claimed only after safety success and at least one non-regressing workload reduction."
        ),
    }


_WORKLOAD_KEYS = (
    "wall_time",
    "pricing_calls",
    "final_judge_calls",
    "generated_labels",
    "rmp_iterations",
    "node_count",
)


def _normalize_workload(values: Mapping[str, object] | None) -> dict[str, float | None]:
    raw = values or {}
    return {key: _float_or_none(raw.get(key)) for key in _WORKLOAD_KEYS}


def _metric_diff(before: float | None, after: float | None) -> float | None:
    if before is None or after is None:
        return None
    return round(float(after) - float(before), 9)


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _workload_metadata(
    key: str,
    before: Mapping[str, object] | None,
    after: Mapping[str, object] | None,
    *,
    default: str,
) -> str:
    for values in (after, before):
        if isinstance(values, Mapping) and values.get(key) is not None:
            return str(values[key])
    return default


def _seed_family_from_instance_id(instance_id: str) -> str:
    marker = "seed"
    value = str(instance_id)
    if marker not in value:
        return "unknown"
    seed = value.rsplit(marker, 1)[-1]
    return seed[:3] if seed else "unknown"


def _count_by(rows: Iterable[Mapping[str, object]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key))
        counts[value] = counts.get(value, 0) + 1
    return counts


def _count_by_split(rows: Iterable[Mapping[str, object]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        split = row.get("split_keys") if isinstance(row.get("split_keys"), Mapping) else {}
        value = str(split.get(key))
        counts[value] = counts.get(value, 0) + 1
    return counts
