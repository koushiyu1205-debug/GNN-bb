"""B4C/B4D compact-pricing formulation diagnostic artifact builder."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean
from typing import Iterable, Iterator

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.core.journey import journey_column_from_solution_payload
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals, solve_restricted_journey_rmp
from lunar_ice_bpc.exact.solver.gurobi_compact import solve_highs_compact_single_journey_pricing
from lunar_ice_bpc.exact.solver.cut_probe import build_cut_probe


CSV_COLUMNS = (
    "matrix_group",
    "source_json",
    "instance_id",
    "phase",
    "round",
    "variant",
    "formulation_kind",
    "row_count_added",
    "var_count_before",
    "var_count_after",
    "constraint_count_before",
    "constraint_count_after",
    "arc_options_removed",
    "slot_count_before",
    "slot_count_after",
    "compact_pricing_status",
    "compact_pricing_exact_status",
    "compact_pricing_best_rc",
    "compact_pricing_dual_bound",
    "compact_pricing_gap",
    "mip_nodes",
    "simplex_iterations",
    "wall_time",
    "negative_found",
    "negative_rc",
    "negative_column_count",
    "new_negative_columns_found",
    "cut_candidate_count",
    "cut_violated_count",
    "max_violation",
    "active_column_count",
    "pool_column_count",
    "columns_added",
    "active_columns_after_merge",
    "can_certify_no_negative",
    "certificate_scope",
    "global_remaining_rc_lb",
    "frontier_coverage_complete",
    "frontier_region_count",
    "frontier_unsupported_region_count",
    "pending_complete_min_rc",
    "pricing_proof_kind",
    "compact_final_judge_profile",
    "compact_final_judge_formulation_profile",
    "compact_final_judge_phase_mode",
    "compact_optimization_harvest_enabled",
    "compact_optimization_harvest_target",
    "compact_optimization_harvest_no_good_scope",
    "compact_optimization_harvest_found_count",
    "compact_optimization_harvest_search_call_count",
    "negative_feasibility_skipped_for_proof_only",
    "negative_feasibility_full_space_proof_attempted",
    "negative_feasibility_full_space_proof_can_certify",
    "phase_budget_sec",
    "negative_feasibility_budget_sec",
    "optimization_proof_budget_sec",
    "negative_discovery_budget_exhausted",
    "feasibility_proof_budget_exhausted",
    "optimization_proof_missing",
    "pricing_complete_by_compact_milp",
    "negative_feasibility_search_enabled",
    "mtz_endpoint_order_cuts_enabled",
    "mtz_endpoint_order_cut_count",
    "pair_adjacency_cuts_enabled",
    "pair_adjacency_cut_count",
    "sortie_slots_per_journey",
    "sortie_slot_bound_source",
    "latest_service_start_slot_bound_enabled",
    "sortie_slot_horizon_count_bound",
    "sortie_slot_latest_start_count_bound",
    "service_start_depot_travel_lb_enabled",
    "service_start_depot_travel_lb_count",
    "task_to_depot_return_travel_lb_enabled",
    "task_to_depot_return_travel_lb_count",
    "pair_route_duration_lb_enabled",
    "pair_route_duration_lb_count",
    "sortie_slot_position_bounds_enabled",
    "sortie_slot_position_bound_count",
    "demand_cover_cut_enabled",
    "demand_cover_cut_count",
    "demand_cover_subset_count",
    "single_task_energy_lb_enabled",
    "single_task_energy_lb_count",
    "single_task_shadow_lb_enabled",
    "single_task_shadow_lb_count",
    "pair_energy_lb_enabled",
    "pair_energy_lb_count",
    "pair_energy_lb_exceeds_limit_count",
    "pair_energy_infeasible_cut_enabled",
    "pair_energy_infeasible_cut_count",
    "pair_energy_infeasible_pair_count",
    "pair_shadow_infeasible_cut_enabled",
    "pair_shadow_infeasible_cut_count",
    "pair_shadow_infeasible_pair_count",
    "triple_shadow_infeasible_cut_enabled",
    "triple_shadow_infeasible_cut_count",
    "triple_shadow_infeasible_triple_count",
    "triple_energy_infeasible_cut_enabled",
    "triple_energy_infeasible_cut_count",
    "triple_energy_infeasible_triple_count",
    "time_window_arc_pruning_enabled",
    "time_window_arc_option_count",
    "time_window_impossible_arc_option_count",
    "restricted_negative_feasibility_claimed_certificate",
    "positive_incumbent_rc_claimed_certificate",
)

EXPECTED_VARIANTS = (
    "V0_current_compact_pricing",
    "V1_endpoint_order_plus_pair_adjacency",
    "V2_latest_service_start_slot_bound",
    "V3_time_window_arc_pruning",
    "V4_combined_endpoint_pair_latest_start_time_window",
    "V5_subset_row_master_diagnostic_only",
)

B4D_VARIANT_CONFIGS = {
    "V0_current_compact_pricing": {
        "formulation_kind": "baseline_no_endpoint_pair_latest_timewindow",
        "mtz_connectivity": False,
        "mtz_endpoint_order_cuts": False,
        "pair_adjacency_cuts": False,
        "latest_service_start_slot_bound": False,
        "time_window_arc_pruning": False,
    },
    "V1_endpoint_order_plus_pair_adjacency": {
        "formulation_kind": "endpoint_order+pair_adjacency",
        "mtz_connectivity": True,
        "mtz_endpoint_order_cuts": True,
        "pair_adjacency_cuts": True,
        "latest_service_start_slot_bound": False,
        "time_window_arc_pruning": False,
    },
    "V2_latest_service_start_slot_bound": {
        "formulation_kind": "latest_service_start_slot_bound",
        "mtz_connectivity": False,
        "mtz_endpoint_order_cuts": False,
        "pair_adjacency_cuts": False,
        "latest_service_start_slot_bound": True,
        "time_window_arc_pruning": False,
    },
    "V3_time_window_arc_pruning": {
        "formulation_kind": "time_window_arc_pruning",
        "mtz_connectivity": False,
        "mtz_endpoint_order_cuts": False,
        "pair_adjacency_cuts": False,
        "latest_service_start_slot_bound": False,
        "time_window_arc_pruning": True,
    },
    "V4_combined_endpoint_pair_latest_start_time_window": {
        "formulation_kind": "endpoint_order+pair_adjacency+latest_service_start_slot_bound+time_window_arc_pruning",
        "mtz_connectivity": True,
        "mtz_endpoint_order_cuts": True,
        "pair_adjacency_cuts": True,
        "latest_service_start_slot_bound": True,
        "time_window_arc_pruning": True,
    },
}


def run_b4_pricing_formulation_diagnostic_from_json(
    probe_jsons: Iterable[str | Path],
    *,
    matrix_group: str = "30-scale staged frontier formulation diagnostic",
) -> dict:
    rows: list[dict] = []
    for path in probe_jsons:
        source = Path(path)
        payload = json.loads(source.read_text(encoding="utf-8"))
        rows.extend(_rows_from_payload(payload, source_json=source, matrix_group=matrix_group))
    return _report_from_rows(rows)


def run_b4_pricing_formulation_matrix_from_probe(
    source_probe_json: str | Path,
    *,
    variants: Iterable[str] = EXPECTED_VARIANTS,
    history_round: int = -1,
    negative_feasibility_time_limit_sec: float = 600.0,
    optimization_proof_time_limit_sec: float = 900.0,
    threads: int = 1,
    negative_eps: float = 1.0e-6,
    matrix_group: str = "30-scale staged frontier formulation matrix",
) -> dict:
    rows = list(
        iter_b4_pricing_formulation_matrix_rows_from_probe(
            source_probe_json,
            variants=variants,
            history_round=history_round,
            negative_feasibility_time_limit_sec=negative_feasibility_time_limit_sec,
            optimization_proof_time_limit_sec=optimization_proof_time_limit_sec,
            threads=threads,
            negative_eps=negative_eps,
            matrix_group=matrix_group,
        )
    )
    return _report_from_rows(rows)


def iter_b4_pricing_formulation_matrix_rows_from_probe(
    source_probe_json: str | Path,
    *,
    variants: Iterable[str] = EXPECTED_VARIANTS,
    history_round: int = -1,
    negative_feasibility_time_limit_sec: float = 600.0,
    optimization_proof_time_limit_sec: float = 900.0,
    threads: int = 1,
    negative_eps: float = 1.0e-6,
    matrix_group: str = "30-scale staged frontier formulation matrix",
    skip_keys: Iterable[tuple[str, str, str, str]] = (),
) -> Iterator[dict]:
    """Run B4D formulation variants from a saved staged frontier probe.

    Negative-feasibility rows are discovery diagnostics only in the B4 report.
    Optimization-proof rows may certify only when the unrestricted compact MILP
    itself proves no negative column.
    """

    source = Path(source_probe_json)
    payload = json.loads(source.read_text(encoding="utf-8"))
    instance_path = payload.get("instance_path")
    if not instance_path:
        raise ValueError(f"source probe has no instance_path: {source}")
    data = load_lunar_ice_data(json.loads(Path(instance_path).read_text(encoding="utf-8")))
    history = payload.get("history") if isinstance(payload.get("history"), list) else []
    history_row = _select_history_row(history, int(history_round))
    dual_context = history_row.get("dual_context")
    if not isinstance(dual_context, dict):
        raise ValueError("selected history row has no dual_context")
    duals = JourneyDuals(
        cover={str(key): float(value) for key, value in (dual_context.get("task_duals") or {}).items()},
        fleet_limit=float(dual_context.get("fleet_dual") or 0.0),
        cuts={str(key): float(value) for key, value in (dual_context.get("cut_duals") or {}).items()},
    )
    skip_lookup = set(skip_keys)
    requested = tuple(str(variant) for variant in variants)
    for variant in requested:
        if variant == "V5_subset_row_master_diagnostic_only":
            for row in _v5_subset_row_rows_from_active_columns(payload, source_json=source, matrix_group=matrix_group):
                if b4_pricing_matrix_row_key(row) not in skip_lookup:
                    yield row
            continue
        config = B4D_VARIANT_CONFIGS.get(variant)
        if not config:
            raise ValueError(f"unknown B4D variant: {variant}")
        for phase, time_limit, negative_feasibility in (
            ("negative_feasibility", negative_feasibility_time_limit_sec, True),
            ("optimization_proof", optimization_proof_time_limit_sec, False),
        ):
            if float(time_limit) <= 0.0:
                continue
            planned_key = (str(source), str(history_row.get("round") or ""), variant, phase)
            if planned_key in skip_lookup:
                continue
            result = solve_highs_compact_single_journey_pricing(
                data,
                duals,
                time_limit_sec=float(time_limit),
                threads=int(threads),
                mip_gap=0.0,
                negative_eps=float(negative_eps),
                flow_connectivity=False,
                mtz_connectivity=bool(config["mtz_connectivity"]),
                mtz_endpoint_order_cuts=bool(config["mtz_endpoint_order_cuts"]),
                pair_adjacency_cuts=bool(config["pair_adjacency_cuts"]),
                latest_service_start_slot_bound=bool(config["latest_service_start_slot_bound"]),
                time_window_arc_pruning=bool(config["time_window_arc_pruning"]),
                negative_feasibility_search=bool(negative_feasibility),
            )
            result = dict(result)
            result["b4_variant"] = variant
            result["b4_formulation_kind"] = config["formulation_kind"]
            result["phase_budget_sec"] = float(time_limit)
            result["negative_feasibility_budget_sec"] = float(negative_feasibility_time_limit_sec)
            result["optimization_proof_budget_sec"] = float(optimization_proof_time_limit_sec)
            if negative_feasibility:
                result["can_certify_no_negative"] = False
                result["b4_negative_feasibility_certificate_suppressed"] = True
            yield _row_from_pricing_payload(
                result,
                matrix_group=matrix_group,
                source_json=source,
                instance_id=str(payload.get("instance_id") or data.instance_id),
                phase=phase,
                round_id=history_row.get("round"),
                active_columns_after_merge=(
                    len(payload.get("active_columns") or [])
                    if isinstance(payload.get("active_columns"), list)
                    else None
                ),
            )


def build_b4_pricing_formulation_report_from_rows(rows: Iterable[dict]) -> dict:
    return _report_from_rows(list(rows))


def b4_pricing_matrix_row_key(row: dict) -> tuple[str, str, str, str]:
    return (
        str(row.get("source_json") or ""),
        str(row.get("round") or ""),
        str(row.get("variant") or ""),
        str(row.get("phase") or ""),
    )


def latest_compact_frontier_probe_jsons(
    root: str | Path,
    *,
    limit: int = 1,
) -> list[Path]:
    root = Path(root)
    candidates = sorted(
        root.glob("compact_pricing_replay_plus*_stage001_*/*plus*_stage001_plus_replay_probe.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[: max(0, int(limit))]


def write_b4_pricing_formulation_artifacts(
    report: dict,
    *,
    rows_csv: str | Path,
    summary_json: str | Path,
    report_md: str | Path,
) -> None:
    rows_csv = Path(rows_csv)
    summary_json = Path(summary_json)
    report_md = Path(report_md)
    rows_csv.parent.mkdir(parents=True, exist_ok=True)
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    report_md.parent.mkdir(parents=True, exist_ok=True)
    with rows_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow({key: _csv_value(row.get(key)) for key in CSV_COLUMNS})
    summary_json.write_text(
        json.dumps({key: value for key, value in report.items() if key != "rows"}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    report_md.write_text(render_b4_pricing_formulation_markdown(report, rows_csv=rows_csv, summary_json=summary_json), encoding="utf-8")


def render_b4_pricing_formulation_markdown(report: dict, *, rows_csv: str | Path, summary_json: str | Path) -> str:
    lines = [
        "# B4C/B4D Pricing Formulation 诊断报告",
        "",
        "## Certificate Boundary",
        "",
        "- 本报告只诊断 compact pricing formulation 对 proof-tail 的影响。",
        "- negative-feasibility 可以找负列，但不能证明 no-negative。",
        "- 只有 unrestricted exact pricing proof 且 dual bound 非负时，才允许 `can_certify_no_negative=True`。",
        "",
        "## Artifacts",
        "",
        f"- CSV rows: `{rows_csv}`",
        f"- JSON summary: `{summary_json}`",
        "",
        "## Redlines",
        "",
        "| metric | value | required |",
        "| --- | ---: | ---: |",
    ]
    for key, value in report["redlines"].items():
        lines.append(f"| {key} | {value} | 0 |")
    lines.extend(["", "## Summary", ""])
    lines.append("| variant | rows | negatives | cut violations | best RC | best dual bound | certified | mean wall |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in report["summary_rows"]:
        lines.append(
            "| {variant} | {rows} | {neg} | {cuts} | {rc} | {bound} | {cert} | {wall} |".format(
                variant=row["variant"],
                rows=row["row_count"],
                neg=row["negative_column_count"],
                cuts=row["cut_violated_count"],
                rc=row["best_negative_rc"],
                bound=row["best_dual_bound"],
                cert=row["can_certify_no_negative_count"],
                wall=row["mean_wall_time"],
            )
        )
    acceptance = report["acceptance"]
    any_diagnostic_claim = any(int(value or 0) > 0 for value in report["redlines"].values())
    best_bounds = [
        _float_or_none(row.get("compact_pricing_dual_bound"))
        for row in report["rows"]
        if _float_or_none(row.get("compact_pricing_dual_bound")) is not None
    ]
    baseline_bounds = [
        _float_or_none(row.get("compact_pricing_dual_bound"))
        for row in report["rows"]
        if str(row.get("variant") or "") == "V0_current_compact_pricing"
        and _float_or_none(row.get("compact_pricing_dual_bound")) is not None
    ]
    missing_text = ", ".join(acceptance["missing_variants"]) if acceptance["missing_variants"] else "none"
    if acceptance["missing_variants"]:
        next_target = "run missing variants under the same staged frontier dual before claiming formulation improvement."
    elif not baseline_bounds:
        next_target = "rerun V0 with enough time to obtain a baseline proof bound, then compare V1-V4 against it."
    elif not acceptance["b4e_pricing_formulation_accepted"]:
        next_target = "extend the most promising non-V0 variants only if they improve dual bound or negative discovery vs V0."
    else:
        next_target = "freeze the accepted B4E pricing-formulation candidate and run regression scales."
    lines.extend(
        [
            "",
            "## B4D Frontier Readout",
            "",
            f"- Pricing formulation diagnostic accepted: `{acceptance['b4_pricing_formulation_diagnostic_accepted']}`。",
            f"- B4E pricing-formulation accepted: `{acceptance['b4e_pricing_formulation_accepted']}`。",
            f"- Measurable proof-tail progress rows: `{acceptance['measurable_progress_row_count']}`。",
            f"- Measurable improvement vs V0 rows: `{acceptance.get('measurable_improvement_row_count', 0)}`。",
            f"- No-negative certified rows: `{acceptance['no_negative_certified_row_count']}`。",
            f"- Negative-discovery budget exhausted rows: `{acceptance.get('negative_discovery_budget_exhausted_count', 0)}`。",
            f"- Feasibility-proof budget exhausted rows: `{acceptance.get('feasibility_proof_budget_exhausted_count', 0)}`。",
            f"- Missing optimization-proof rows: `{acceptance.get('optimization_proof_missing_count', 0)}`。",
            f"- Tested variants: `{', '.join(acceptance['tested_variants'])}`。",
            f"- Missing variants: `{missing_text}`。",
            "",
            "## Plan Questions",
            "",
            "- Previous accepted baseline: B3B is accepted for 5/10/20; 30-scale remains diagnostic frontier.",
            f"- Formulation modes tested: `{', '.join(acceptance['tested_variants'])}`。",
            "- Cut violation/binding: V5 subset-row active-pool diagnostic reports this through `cut_violated_count`; it does not add rows.",
            "- Live cut audit: not part of B4C/B4D; live subset-row is gated in the cut report.",
            "- Root/tree bound movement: not certified here; this report only measures compact pricing/frontier diagnostics.",
            "- Node count / certificate time improvement: not claimed.",
            f"- Compact pricing best observed dual bound: `{round(max(best_bounds), 9) if best_bounds else None}`。",
            f"- Diagnostic accidentally claimed certificate: `{any_diagnostic_claim}`。",
            f"- B4E accepted: `{acceptance['b4e_pricing_formulation_accepted']}`。",
            f"- Next target: {next_target}",
        ]
    )
    return "\n".join(lines) + "\n"


def _rows_from_payload(payload: dict, *, source_json: Path, matrix_group: str) -> list[dict]:
    if str(payload.get("schema_version") or "") == "lunar_ice_bpc.compact_pricing_replay.v1":
        return _rows_from_replay(payload, source_json=source_json, matrix_group=matrix_group)
    return _rows_from_probe(payload, source_json=source_json, matrix_group=matrix_group)


def _rows_from_replay(payload: dict, *, source_json: Path, matrix_group: str) -> list[dict]:
    result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
    if not result:
        return []
    replay_config = payload.get("replay_config") if isinstance(payload.get("replay_config"), dict) else {}
    merged = dict(result)
    merged.setdefault("b4_variant", payload.get("b4_variant") or replay_config.get("b4_variant"))
    merged.setdefault("b4_formulation_kind", payload.get("b4_formulation_kind") or replay_config.get("b4_formulation_kind"))
    return [
        _row_from_pricing_payload(
            merged,
            matrix_group=matrix_group,
            source_json=source_json,
            instance_id=str(payload.get("instance_id") or ""),
            phase="compact_pricing_replay",
            round_id=payload.get("selected_history_round"),
            active_columns_after_merge=None,
        )
    ]


def _rows_from_probe(payload: dict, *, source_json: Path, matrix_group: str) -> list[dict]:
    rows: list[dict] = []
    instance_id = str(payload.get("instance_id") or "")
    history = payload.get("history") if isinstance(payload.get("history"), list) else []
    for item in history:
        if isinstance(item, dict):
            rows.append(
                _row_from_pricing_payload(
                    item,
                    matrix_group=matrix_group,
                    source_json=source_json,
                    instance_id=instance_id,
                    phase="history",
                    round_id=item.get("round"),
                    active_columns_after_merge=payload.get("merged_replay_column", {}).get("after_active_column_count")
                    if isinstance(payload.get("merged_replay_column"), dict)
                    else None,
                )
            )
    final_judge = payload.get("final_judge")
    if isinstance(final_judge, dict):
        rows.append(
            _row_from_pricing_payload(
                final_judge,
                matrix_group=matrix_group,
                source_json=source_json,
                instance_id=instance_id,
                phase="final_judge",
                round_id=payload.get("pricing_round_count"),
                active_columns_after_merge=(
                    len(payload.get("active_columns") or [])
                    if isinstance(payload.get("active_columns"), list)
                    else None
                ),
            )
        )
    merged = payload.get("merged_replay_column")
    if isinstance(merged, dict):
        rows.append(
            {
                "matrix_group": matrix_group,
                "source_json": str(source_json),
                "instance_id": instance_id,
                "phase": "staged_frontier_merge",
                "round": "",
                "variant": "V4_combined_endpoint_pair_latest_start_time_window",
                "formulation_kind": "staged_frontier_replay_merge",
                "row_count_added": "",
                "compact_pricing_best_rc": merged.get("replay_best_reduced_cost"),
                "compact_pricing_dual_bound": merged.get("replay_dual_bound"),
                "negative_found": bool(merged.get("added")),
                "negative_rc": merged.get("replay_best_reduced_cost"),
                "negative_column_count": int(bool(merged.get("added"))),
                "new_negative_columns_found": int(bool(merged.get("added"))),
                "columns_added": int(bool(merged.get("added"))),
                "active_columns_after_merge": merged.get("after_active_column_count"),
                "can_certify_no_negative": False,
                "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                "restricted_negative_feasibility_claimed_certificate": False,
                "positive_incumbent_rc_claimed_certificate": False,
            }
        )
    rows.extend(_v5_subset_row_rows_from_active_columns(payload, source_json=source_json, matrix_group=matrix_group))
    return rows


def _v5_subset_row_rows_from_active_columns(payload: dict, *, source_json: Path, matrix_group: str) -> list[dict]:
    active_payloads = payload.get("active_columns")
    instance_path = payload.get("instance_path")
    if not isinstance(active_payloads, list) or not active_payloads or not instance_path:
        return []
    try:
        data = load_lunar_ice_data(json.loads(Path(instance_path).read_text(encoding="utf-8")))
        columns = tuple(journey_column_from_solution_payload(data, row) for row in active_payloads)
        rmp = solve_restricted_journey_rmp(data.task_ids, columns, fleet_size=data.fleet_size)
        probe = build_cut_probe(data.task_ids, columns, rmp.primal_columns, fleet_size=data.fleet_size)
        return [
            {
                "matrix_group": matrix_group,
                "source_json": str(source_json),
                "instance_id": str(payload.get("instance_id") or data.instance_id),
                "phase": "staged_frontier_active_pool_subset_row_probe",
                "round": "",
                "variant": "V5_subset_row_master_diagnostic_only",
                "formulation_kind": "master_subset_row_restricted_active_pool",
                "row_count_added": 0,
                "cut_candidate_count": int(probe.get("subset_candidate_count") or 0),
                "cut_violated_count": int(probe.get("violated_subset_candidate_count") or 0),
                "max_violation": probe.get("max_violation"),
                "active_column_count": len(columns),
                "pool_column_count": len(columns),
                "columns_added": 0,
                "active_columns_after_merge": len(columns),
                "can_certify_no_negative": False,
                "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                "pricing_complete_by_compact_milp": False,
                "negative_found": False,
                "negative_column_count": 0,
                "new_negative_columns_found": 0,
                "restricted_negative_feasibility_claimed_certificate": False,
                "positive_incumbent_rc_claimed_certificate": False,
            }
        ]
    except Exception as exc:
        return [
            {
                "matrix_group": matrix_group,
                "source_json": str(source_json),
                "instance_id": str(payload.get("instance_id") or ""),
                "phase": "staged_frontier_active_pool_subset_row_probe",
                "round": "",
                "variant": "V5_subset_row_master_diagnostic_only",
                "formulation_kind": "master_subset_row_restricted_active_pool",
                "compact_pricing_status": f"V5_SUBSET_ROW_DIAGNOSTIC_FAILED:{type(exc).__name__}",
                "can_certify_no_negative": False,
                "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                "restricted_negative_feasibility_claimed_certificate": False,
                "positive_incumbent_rc_claimed_certificate": False,
            }
        ]


def _row_from_pricing_payload(
    payload: dict,
    *,
    matrix_group: str,
    source_json: Path,
    instance_id: str,
    phase: str,
    round_id,
    active_columns_after_merge,
) -> dict:
    variant, formulation_kind = _variant(payload)
    dual_bound = _float_or_none(payload.get("dual_bound", payload.get("bound")))
    best_rc = _float_or_none(payload.get("best_reduced_cost"))
    can_certify = bool(payload.get("can_certify_no_negative"))
    negative_feasibility = bool(payload.get("negative_feasibility_search_enabled"))
    restricted_negative_cert = bool(can_certify and negative_feasibility and not payload.get("forbidden_arc_patterns_can_certify_full_space", True))
    positive_claim = bool(can_certify and dual_bound is not None and dual_bound < -1.0e-6)
    endpoint_count = int(payload.get("mtz_endpoint_order_cut_count") or 0)
    pair_count = int(payload.get("pair_adjacency_cut_count") or 0)
    row_count_added = endpoint_count + pair_count
    impossible_arcs = int(payload.get("time_window_impossible_arc_option_count") or 0)
    negative_discovery_budget_exhausted = _negative_discovery_budget_exhausted(payload, phase=phase)
    feasibility_proof_budget_exhausted = _feasibility_proof_budget_exhausted(payload, phase=phase)
    optimization_proof_missing = _optimization_proof_missing(payload, phase=phase)
    return {
        "matrix_group": matrix_group,
        "source_json": str(source_json),
        "instance_id": instance_id,
        "phase": phase,
        "round": round_id,
        "variant": variant,
        "formulation_kind": formulation_kind,
        "row_count_added": row_count_added,
        "var_count_before": "",
        "var_count_after": payload.get("variable_count"),
        "constraint_count_before": "",
        "constraint_count_after": payload.get("constraint_count"),
        "arc_options_removed": impossible_arcs,
        "slot_count_before": payload.get("sortie_slot_horizon_count_bound"),
        "slot_count_after": payload.get("sortie_slots_per_journey"),
        "compact_pricing_status": payload.get("status"),
        "compact_pricing_exact_status": payload.get("exact_status"),
        "compact_pricing_best_rc": best_rc,
        "compact_pricing_dual_bound": dual_bound,
        "compact_pricing_gap": payload.get("mip_gap", payload.get("gap")),
        "mip_nodes": (payload.get("solver_info") or {}).get("mip_node_count") if isinstance(payload.get("solver_info"), dict) else None,
        "simplex_iterations": (payload.get("solver_info") or {}).get("simplex_iteration_count") if isinstance(payload.get("solver_info"), dict) else None,
        "wall_time": payload.get("final_judge_wall_time", payload.get("wall_time_sec")),
        "negative_found": bool(payload.get("negative_found") or int(payload.get("negative_column_count") or 0) > 0 or (best_rc is not None and best_rc < -1.0e-6)),
        "negative_rc": best_rc if best_rc is not None and best_rc < -1.0e-6 else None,
        "negative_column_count": int(payload.get("negative_column_count") or 0),
        "new_negative_columns_found": int(payload.get("added_column_count") or payload.get("negative_column_count") or 0),
        "cut_candidate_count": "",
        "cut_violated_count": "",
        "max_violation": "",
        "active_column_count": payload.get("active_column_count", active_columns_after_merge),
        "pool_column_count": payload.get("pool_column_count"),
        "columns_added": int(payload.get("added_column_count") or 0),
        "active_columns_after_merge": active_columns_after_merge,
        "can_certify_no_negative": can_certify,
        "certificate_scope": "BPC_NODE_LP_CERTIFIED" if can_certify else "DIAGNOSTIC_PRICING_FRONTIER",
        "global_remaining_rc_lb": payload.get("global_remaining_rc_lb", payload.get("global_remaining_rc_lower_bound", dual_bound)),
        "frontier_coverage_complete": bool(payload.get("global_remaining_rc_lb_coverage_complete") or can_certify),
        "frontier_region_count": payload.get("frontier_region_count", 1 if dual_bound is not None else 0),
        "frontier_unsupported_region_count": payload.get(
            "frontier_unsupported_region_count",
            0 if can_certify else 1,
        ),
        "pending_complete_min_rc": payload.get("pending_complete_min_rc", best_rc),
        "pricing_proof_kind": payload.get(
            "pricing_proof_kind",
            "EXHAUSTIVE_NO_NEGATIVE" if can_certify else "FRONTIER_BOUND_INCOMPLETE",
        ),
        "compact_final_judge_profile": payload.get("compact_final_judge_profile"),
        "compact_final_judge_formulation_profile": payload.get("compact_final_judge_formulation_profile"),
        "compact_final_judge_phase_mode": payload.get("compact_final_judge_phase_mode"),
        "compact_optimization_harvest_enabled": bool(payload.get("compact_optimization_harvest_enabled")),
        "compact_optimization_harvest_target": payload.get("compact_optimization_harvest_target"),
        "compact_optimization_harvest_no_good_scope": payload.get(
            "compact_optimization_harvest_no_good_scope"
        ),
        "compact_optimization_harvest_found_count": payload.get("compact_optimization_harvest_found_count"),
        "compact_optimization_harvest_search_call_count": payload.get(
            "compact_optimization_harvest_search_call_count"
        ),
        "negative_feasibility_skipped_for_proof_only": bool(
            payload.get("negative_feasibility_skipped_for_proof_only")
        ),
        "negative_feasibility_full_space_proof_attempted": bool(
            payload.get("negative_feasibility_full_space_proof_attempted")
        ),
        "negative_feasibility_full_space_proof_can_certify": bool(
            payload.get("negative_feasibility_full_space_proof_can_certify")
        ),
        "phase_budget_sec": payload.get("phase_budget_sec"),
        "negative_feasibility_budget_sec": payload.get("negative_feasibility_budget_sec"),
        "optimization_proof_budget_sec": payload.get("optimization_proof_budget_sec"),
        "negative_discovery_budget_exhausted": negative_discovery_budget_exhausted,
        "feasibility_proof_budget_exhausted": feasibility_proof_budget_exhausted,
        "optimization_proof_missing": optimization_proof_missing,
        "pricing_complete_by_compact_milp": bool(payload.get("pricing_complete_by_compact_milp")),
        "negative_feasibility_search_enabled": negative_feasibility,
        "mtz_endpoint_order_cuts_enabled": bool(payload.get("mtz_endpoint_order_cuts_enabled")),
        "mtz_endpoint_order_cut_count": endpoint_count,
        "pair_adjacency_cuts_enabled": bool(payload.get("pair_adjacency_cuts_enabled")),
        "pair_adjacency_cut_count": pair_count,
        "sortie_slots_per_journey": payload.get("sortie_slots_per_journey"),
        "sortie_slot_bound_source": payload.get("sortie_slot_bound_source"),
        "latest_service_start_slot_bound_enabled": payload.get("latest_service_start_slot_bound_enabled"),
        "sortie_slot_horizon_count_bound": payload.get("sortie_slot_horizon_count_bound"),
        "sortie_slot_latest_start_count_bound": payload.get("sortie_slot_latest_start_count_bound"),
        "service_start_depot_travel_lb_enabled": bool(payload.get("service_start_depot_travel_lb_enabled")),
        "service_start_depot_travel_lb_count": payload.get("service_start_depot_travel_lb_count"),
        "task_to_depot_return_travel_lb_enabled": bool(payload.get("task_to_depot_return_travel_lb_enabled")),
        "task_to_depot_return_travel_lb_count": payload.get("task_to_depot_return_travel_lb_count"),
        "pair_route_duration_lb_enabled": bool(payload.get("pair_route_duration_lb_enabled")),
        "pair_route_duration_lb_count": payload.get("pair_route_duration_lb_count"),
        "sortie_slot_position_bounds_enabled": bool(payload.get("sortie_slot_position_bounds_enabled")),
        "sortie_slot_position_bound_count": payload.get("sortie_slot_position_bound_count"),
        "demand_cover_cut_enabled": bool(payload.get("demand_cover_cut_enabled")),
        "demand_cover_cut_count": payload.get("demand_cover_cut_count"),
        "demand_cover_subset_count": payload.get("demand_cover_subset_count"),
        "single_task_energy_lb_enabled": bool(payload.get("single_task_energy_lb_enabled")),
        "single_task_energy_lb_count": payload.get("single_task_energy_lb_count"),
        "single_task_shadow_lb_enabled": bool(payload.get("single_task_shadow_lb_enabled")),
        "single_task_shadow_lb_count": payload.get("single_task_shadow_lb_count"),
        "pair_energy_lb_enabled": bool(payload.get("pair_energy_lb_enabled")),
        "pair_energy_lb_count": payload.get("pair_energy_lb_count"),
        "pair_energy_lb_exceeds_limit_count": payload.get("pair_energy_lb_exceeds_limit_count"),
        "pair_energy_infeasible_cut_enabled": bool(payload.get("pair_energy_infeasible_cut_enabled")),
        "pair_energy_infeasible_cut_count": payload.get("pair_energy_infeasible_cut_count"),
        "pair_energy_infeasible_pair_count": payload.get("pair_energy_infeasible_pair_count"),
        "pair_shadow_infeasible_cut_enabled": bool(payload.get("pair_shadow_infeasible_cut_enabled")),
        "pair_shadow_infeasible_cut_count": payload.get("pair_shadow_infeasible_cut_count"),
        "pair_shadow_infeasible_pair_count": payload.get("pair_shadow_infeasible_pair_count"),
        "triple_shadow_infeasible_cut_enabled": bool(payload.get("triple_shadow_infeasible_cut_enabled")),
        "triple_shadow_infeasible_cut_count": payload.get("triple_shadow_infeasible_cut_count"),
        "triple_shadow_infeasible_triple_count": payload.get("triple_shadow_infeasible_triple_count"),
        "triple_energy_infeasible_cut_enabled": bool(payload.get("triple_energy_infeasible_cut_enabled")),
        "triple_energy_infeasible_cut_count": payload.get("triple_energy_infeasible_cut_count"),
        "triple_energy_infeasible_triple_count": payload.get("triple_energy_infeasible_triple_count"),
        "time_window_arc_pruning_enabled": bool(payload.get("time_window_arc_pruning_enabled")),
        "time_window_arc_option_count": payload.get("time_window_arc_option_count"),
        "time_window_impossible_arc_option_count": impossible_arcs,
        "restricted_negative_feasibility_claimed_certificate": restricted_negative_cert,
        "positive_incumbent_rc_claimed_certificate": positive_claim,
    }


def _report_from_rows(rows: list[dict]) -> dict:
    redlines = {
        "restricted_negative_feasibility_claimed_certificate_count": sum(1 for row in rows if row.get("restricted_negative_feasibility_claimed_certificate") is True),
        "positive_incumbent_rc_claimed_certificate_count": sum(1 for row in rows if row.get("positive_incumbent_rc_claimed_certificate") is True),
    }
    progress_rows = [
        row
        for row in rows
        if int(row.get("new_negative_columns_found") or 0) > 0
        or _float_or_none(row.get("compact_pricing_dual_bound")) is not None
        or int(row.get("cut_violated_count") or 0) > 0
    ]
    tested_variants = sorted({str(row.get("variant") or "") for row in rows if row.get("variant")})
    missing_variants = [variant for variant in EXPECTED_VARIANTS if variant not in tested_variants]
    improvement_rows = _pricing_improvement_rows(rows)
    return {
        "schema_version": "lunar_ice_bpc.b4_pricing_formulation_diagnostic.v1",
        "rows": rows,
        "row_count": len(rows),
        "summary_rows": _summary_rows(rows),
        "redlines": redlines,
        "acceptance": {
            "b4_pricing_formulation_diagnostic_accepted": bool(
                progress_rows and all(int(value or 0) == 0 for value in redlines.values())
            ),
            "b4e_pricing_formulation_accepted": bool(
                improvement_rows
                and all(int(value or 0) == 0 for value in redlines.values())
                and not missing_variants
                and any(str(row.get("variant")) == "V4_combined_endpoint_pair_latest_start_time_window" for row in rows)
            ),
            "measurable_progress_row_count": len(progress_rows),
            "measurable_improvement_row_count": len(improvement_rows),
            "no_negative_certified_row_count": sum(1 for row in rows if row.get("can_certify_no_negative") is True),
            "negative_discovery_budget_exhausted_count": sum(
                1 for row in rows if row.get("negative_discovery_budget_exhausted") is True
            ),
            "feasibility_proof_budget_exhausted_count": sum(
                1 for row in rows if row.get("feasibility_proof_budget_exhausted") is True
            ),
            "optimization_proof_missing_count": sum(
                1 for row in rows if row.get("optimization_proof_missing") is True
            ),
            "tested_variants": tested_variants,
            "missing_variants": missing_variants,
            "full_variant_matrix_complete": not missing_variants,
        },
    }


def _pricing_improvement_rows(rows: list[dict], *, eps: float = 1.0e-6) -> list[dict]:
    baseline_by_source_round: dict[tuple[str, str], dict] = {}
    for row in rows:
        if str(row.get("variant") or "") != "V0_current_compact_pricing":
            continue
        dual_bound = _float_or_none(row.get("compact_pricing_dual_bound"))
        if dual_bound is None:
            continue
        key = (_source_identity(row.get("source_json")), str(row.get("round") or ""))
        existing = baseline_by_source_round.get(key)
        existing_bound = _float_or_none(existing.get("compact_pricing_dual_bound")) if existing else None
        if existing is None or existing_bound is None or float(dual_bound) > float(existing_bound):
            baseline_by_source_round[key] = row
    if not baseline_by_source_round:
        return []
    out: list[dict] = []
    for row in rows:
        if str(row.get("variant") or "") in {"", "V0_current_compact_pricing", "V5_subset_row_master_diagnostic_only"}:
            continue
        baseline = baseline_by_source_round.get((_source_identity(row.get("source_json")), str(row.get("round") or "")))
        if baseline is None:
            continue
        best_baseline_bound = _float_or_none(baseline.get("compact_pricing_dual_bound"))
        if best_baseline_bound is None:
            continue
        baseline_negative_count = int(baseline.get("new_negative_columns_found") or 0)
        dual_bound = _float_or_none(row.get("compact_pricing_dual_bound"))
        if dual_bound is not None and float(dual_bound) > best_baseline_bound + abs(float(eps)):
            out.append(row)
            continue
        if int(row.get("new_negative_columns_found") or 0) > baseline_negative_count:
            out.append(row)
    return out


def _source_identity(value) -> str:
    if value is None or value == "":
        return ""
    path = Path(str(value))
    try:
        return str(path.resolve())
    except Exception:
        return str(path)


def _summary_rows(rows: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(str(row.get("variant") or ""), []).append(row)
    out: list[dict] = []
    for variant, group in sorted(groups.items()):
        walls = [_float_or_none(row.get("wall_time")) for row in group if _float_or_none(row.get("wall_time")) is not None]
        negative_rcs = [_float_or_none(row.get("negative_rc")) for row in group if _float_or_none(row.get("negative_rc")) is not None]
        dual_bounds = [_float_or_none(row.get("compact_pricing_dual_bound")) for row in group if _float_or_none(row.get("compact_pricing_dual_bound")) is not None]
        out.append(
            {
                "variant": variant,
                "row_count": len(group),
                "negative_column_count": sum(int(row.get("negative_column_count") or 0) for row in group),
                "cut_violated_count": sum(int(row.get("cut_violated_count") or 0) for row in group),
                "best_negative_rc": round(min(negative_rcs), 9) if negative_rcs else None,
                "best_dual_bound": round(max(dual_bounds), 9) if dual_bounds else None,
                "can_certify_no_negative_count": sum(1 for row in group if row.get("can_certify_no_negative") is True),
                "mean_wall_time": round(mean(walls), 6) if walls else None,
            }
        )
    return out


def _variant(payload: dict) -> tuple[str, str]:
    explicit_variant = str(payload.get("b4_variant") or "")
    if explicit_variant:
        return explicit_variant, str(payload.get("b4_formulation_kind") or explicit_variant)
    kinds: list[str] = []
    if payload.get("mtz_endpoint_order_cuts_enabled"):
        kinds.append("endpoint_order")
    if payload.get("pair_adjacency_cuts_enabled"):
        kinds.append("pair_adjacency")
    latest_enabled = payload.get("latest_service_start_slot_bound_enabled")
    if latest_enabled is True or (
        latest_enabled is None and str(payload.get("sortie_slot_bound_source") or "").startswith("latest")
    ):
        kinds.append("latest_service_start_slot_bound")
    if payload.get("time_window_arc_pruning_enabled"):
        kinds.append("time_window_arc_pruning")
    if payload.get("service_start_depot_travel_lb_enabled"):
        kinds.append("service_start_depot_travel_lb")
    if payload.get("task_to_depot_return_travel_lb_enabled"):
        kinds.append("task_to_depot_return_travel_lb")
    if payload.get("pair_route_duration_lb_enabled"):
        kinds.append("pair_route_duration_lb")
    if payload.get("sortie_slot_position_bounds_enabled"):
        kinds.append("sortie_slot_position_bounds")
    if payload.get("demand_cover_cut_enabled"):
        kinds.append("demand_cover_cut")
    if payload.get("single_task_energy_lb_enabled"):
        kinds.append("single_task_energy_lb")
    if payload.get("single_task_shadow_lb_enabled"):
        kinds.append("single_task_shadow_lb")
    if payload.get("pair_energy_lb_enabled"):
        kinds.append("pair_energy_lb")
    if payload.get("pair_energy_infeasible_cut_enabled"):
        kinds.append("pair_energy_infeasible_cut")
    if payload.get("pair_shadow_infeasible_cut_enabled"):
        kinds.append("pair_shadow_infeasible_cut")
    if payload.get("triple_shadow_infeasible_cut_enabled"):
        kinds.append("triple_shadow_infeasible_cut")
    if payload.get("triple_energy_infeasible_cut_enabled"):
        kinds.append("triple_energy_infeasible_cut")
    if not kinds:
        return "V0_current_compact_pricing", "baseline_compact_pricing"
    if set(kinds) >= {"endpoint_order", "pair_adjacency", "latest_service_start_slot_bound", "time_window_arc_pruning"}:
        return "V4_combined_endpoint_pair_latest_start_time_window", "+".join(kinds)
    if {"endpoint_order", "pair_adjacency"}.issubset(kinds):
        return "V1_endpoint_order_plus_pair_adjacency", "+".join(kinds)
    if "latest_service_start_slot_bound" in kinds:
        return "V2_latest_service_start_slot_bound", "+".join(kinds)
    if "time_window_arc_pruning" in kinds:
        return "V3_time_window_arc_pruning", "+".join(kinds)
    return "V0_current_compact_pricing", "+".join(kinds)


def _csv_value(value):
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def _float_or_none(value) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _negative_discovery_budget_exhausted(payload: dict, *, phase: str) -> bool:
    phase_name = str(payload.get("compact_pricing_phase") or phase or "")
    status = str(payload.get("status") or "")
    if phase_name == "negative_feasibility_proof" or payload.get("negative_feasibility_full_space_proof_attempted"):
        return False
    if "negative_feasibility" not in phase_name:
        return False
    return "TIME_LIMIT" in status or status.endswith("LIMIT_REACHED")


def _feasibility_proof_budget_exhausted(payload: dict, *, phase: str) -> bool:
    phase_name = str(payload.get("compact_pricing_phase") or phase or "")
    status = str(payload.get("status") or "")
    if phase_name != "negative_feasibility_proof" and not payload.get("negative_feasibility_full_space_proof_attempted"):
        return False
    return "TIME_LIMIT" in status or status.endswith("LIMIT_REACHED")


def _optimization_proof_missing(payload: dict, *, phase: str) -> bool:
    if str(phase or "") == "negative_feasibility":
        return False
    phase_name = str(payload.get("compact_pricing_phase") or phase or "")
    if phase_name == "optimization_proof":
        return False
    phase_payloads = payload.get("compact_pricing_phase_payloads")
    if isinstance(phase_payloads, dict) and "optimization_proof" in phase_payloads:
        return False
    status = str(payload.get("status") or "")
    exact_status = str(payload.get("exact_status") or "")
    incomplete = "TIME_LIMIT" in status or exact_status in {"", "NOT_SOLVED"}
    return bool(incomplete and phase_name in {"negative_feasibility", "negative_feasibility_search", "negative_feasibility_batch"})


def _select_history_row(history: list[dict], round_index: int) -> dict:
    if not history:
        raise ValueError("source probe has empty history")
    if round_index < 0:
        return history[round_index]
    for row in history:
        if int(row.get("round") or -1) == int(round_index):
            return row
    raise ValueError(f"history round {round_index} not found")
