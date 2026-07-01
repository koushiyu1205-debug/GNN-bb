"""B2 pricing-tail ablation runner and report writer."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import signal
from statistics import mean
from time import perf_counter
from typing import Callable, Iterable

from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import B2A_MODE, B2B_MODE, solve_b2_pricing_tail_baseline
from lunar_ice_bpc.exact.bpc.solver.root_node_solver import solve_b1_root_node_baseline
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.solver.journey_driver import solve_direct_journey_baseline
from lunar_ice_bpc.io.instance_io import read_json
from lunar_ice_bpc.runners.b0_b1_ablation import B0_MODE, B1A_MODE, B1B_MODE


B2_MODES = (B0_MODE, B1A_MODE, B1B_MODE, B2A_MODE, B2B_MODE)

CSV_COLUMNS = (
    "matrix_group",
    "scale",
    "instance_id",
    "baseline_name",
    "candidate_name",
    "algorithm_status",
    "certificate_scope",
    "pricing_state",
    "uses_true_dual_bpc_certificate",
    "official_lower_bound_source",
    "official_lower_bound_scope",
    "B0_direct_objective",
    "root_lp_bound",
    "root_lp_bound_official",
    "root_bound_le_B0_objective",
    "pricing_round_count",
    "final_judge_call_count",
    "candidate_negative_count",
    "addable_negative_count",
    "duplicate_in_current_master_count",
    "in_pool_not_master_count",
    "forbidden_signature_count",
    "branch_filtered_count",
    "cut_filtered_count",
    "selected_count",
    "added_to_master_count",
    "added_column_count",
    "duplicate_only_count",
    "duplicate_only_audit_status",
    "hidden_negative_count",
    "replacement_only_round_count",
    "manual_rc_audit_pass",
    "pricing_rc_audit_pass",
    "proof_debt_unreleased_count",
    "wall_time",
    "fail_closed_reason",
    "certificate_scope_regression",
    "objective_mismatch",
    "improvement_reason",
)


def run_b2_pricing_tail_ablation(
    instances: Iterable[dict | str | Path],
    *,
    modes: Iterable[str] = B2_MODES,
    max_direct_tasks: int = 5,
    b1_max_rounds: int = 8,
    b2_max_rounds: int = 8,
    matrix_group: str = "",
    row_time_limit_sec: float | None = None,
) -> dict:
    rows: list[dict] = []
    selected_modes = tuple(modes)
    for item in instances:
        instance = _load_instance(item)
        baseline_cache: dict[str, dict] = {}
        for mode in selected_modes:
            row = _run_guarded_mode(
                instance,
                mode=mode,
                baseline_cache=baseline_cache,
                max_direct_tasks=int(max_direct_tasks),
                b1_max_rounds=int(b1_max_rounds),
                b2_max_rounds=int(b2_max_rounds),
                matrix_group=matrix_group,
                row_time_limit_sec=row_time_limit_sec,
            )
            rows.append(row)
            if mode in {B1A_MODE, B1B_MODE}:
                baseline_cache[mode] = dict(row.get("_raw_result") or {})
        _annotate_instance_improvements(rows)
    return _report_from_rows(rows)


def run_b2_pricing_tail_ablation_matrix(
    *,
    manifest_path: str | Path,
    project_root: str | Path,
    scale10_limit: int = 5,
    scale10_row_time_limit_sec: float | None = 30.0,
    scale20_probe_limit: int = 1,
    direct20_probe_time_limit_sec: float = 60.0,
    fail_closed_max_direct_tasks: int = 10,
    b1_max_rounds: int = 8,
    b2_max_rounds: int = 8,
) -> dict:
    project_root = Path(project_root)
    manifest_path = Path(manifest_path)
    if not manifest_path.is_absolute():
        manifest_path = project_root / manifest_path
    rows: list[dict] = []
    notes = [
        "B2 runner is serial by default to avoid concurrent 20-scale final-judge memory spikes.",
        "Completion-bound pruning remains disabled; completion-bound data is audit/order/profiling only.",
    ]

    scale5 = _manifest_instance_paths(manifest_path, project_root, scale=5)
    rows.extend(
        run_b2_pricing_tail_ablation(
            scale5,
            max_direct_tasks=5,
            b1_max_rounds=b1_max_rounds,
            b2_max_rounds=b2_max_rounds,
            matrix_group="5-scale full",
        )["rows"]
    )

    scale10_all = _manifest_instance_paths(manifest_path, project_root, scale=10)
    scale10 = scale10_all[: max(0, int(scale10_limit))]
    rows.extend(
        run_b2_pricing_tail_ablation(
            scale10,
            max_direct_tasks=10,
            b1_max_rounds=b1_max_rounds,
            b2_max_rounds=b2_max_rounds,
            matrix_group="10-scale selected5" if len(scale10) < len(scale10_all) else "10-scale full",
            row_time_limit_sec=scale10_row_time_limit_sec,
        )["rows"]
    )
    if len(scale10) < len(scale10_all):
        notes.append(f"10-scale ran selected {len(scale10)}/{len(scale10_all)} first; full 20 is deferred until row time is acceptable.")

    scale20_all = _manifest_instance_paths(manifest_path, project_root, scale=20)
    rows.extend(
        run_b2_pricing_tail_ablation(
            scale20_all,
            max_direct_tasks=int(fail_closed_max_direct_tasks),
            b1_max_rounds=b1_max_rounds,
            b2_max_rounds=b2_max_rounds,
            matrix_group="20-scale fail-closed guard",
        )["rows"]
    )
    notes.append(
        "20-scale fail-closed guard deliberately sets max_direct_tasks below 20; B0/B1/B2 fail-closed is expected."
    )

    scale20_probe = scale20_all[: max(0, int(scale20_probe_limit))]
    if scale20_probe:
        rows.extend(
            run_b2_pricing_tail_ablation(
                scale20_probe,
                max_direct_tasks=20,
                b1_max_rounds=b1_max_rounds,
                b2_max_rounds=b2_max_rounds,
                matrix_group="20-scale selected direct20 probe",
                row_time_limit_sec=float(direct20_probe_time_limit_sec),
            )["rows"]
        )
        notes.append(
            f"20-scale selected direct20 probe used {len(scale20_probe)} instance(s), modes B0/B1A/B1B/B2A/B2B, "
            f"with per-row timeout {direct20_probe_time_limit_sec}s."
        )

    scale30_all = _manifest_instance_paths(manifest_path, project_root, scale=30)
    rows.extend(
        run_b2_pricing_tail_ablation(
            scale30_all,
            max_direct_tasks=int(fail_closed_max_direct_tasks),
            b1_max_rounds=b1_max_rounds,
            b2_max_rounds=b2_max_rounds,
            matrix_group="30-scale fail-closed diagnostic",
        )["rows"]
    )

    _annotate_instance_improvements(rows)
    report = _report_from_rows(rows)
    report["matrix"] = {
        "manifest_path": str(manifest_path),
        "scale5_count": len(scale5),
        "scale10_selected_count": len(scale10),
        "scale10_total_count": len(scale10_all),
        "scale10_row_time_limit_sec": scale10_row_time_limit_sec,
        "scale20_fail_closed_count": len(scale20_all),
        "scale20_probe_count": len(scale20_probe),
        "scale20_probe_modes": list(B2_MODES),
        "scale30_count": len(scale30_all),
        "fail_closed_max_direct_tasks": int(fail_closed_max_direct_tasks),
        "direct20_probe_time_limit_sec": float(direct20_probe_time_limit_sec),
        "notes": notes,
    }
    report["acceptance"] = _acceptance(report["rows"], report["redlines"], matrix=report["matrix"])
    return report


def run_b2_pricing_tail_direct20_probe(
    *,
    manifest_path: str | Path,
    project_root: str | Path,
    scale20_probe_limit: int = 5,
    scale20_probe_offset: int = 0,
    direct20_probe_time_limit_sec: float = 60.0,
    b1_max_rounds: int = 8,
    b2_max_rounds: int = 8,
) -> dict:
    """Run only the 20-scale selected direct20 probe rows.

    This is intentionally separate from the full matrix so the expensive direct20
    probe can be resumed or expanded without rerunning the already completed
    5/10/fail-closed/30 diagnostic groups.
    """

    project_root = Path(project_root)
    manifest_path = Path(manifest_path)
    if not manifest_path.is_absolute():
        manifest_path = project_root / manifest_path
    scale20_all = _manifest_instance_paths(manifest_path, project_root, scale=20)
    offset = max(0, int(scale20_probe_offset))
    limit = max(0, int(scale20_probe_limit))
    scale20_probe = scale20_all[offset: offset + limit]
    rows = []
    if scale20_probe:
        rows = run_b2_pricing_tail_ablation(
            scale20_probe,
            max_direct_tasks=20,
            b1_max_rounds=b1_max_rounds,
            b2_max_rounds=b2_max_rounds,
            matrix_group="20-scale selected direct20 probe",
            row_time_limit_sec=float(direct20_probe_time_limit_sec),
        )["rows"]
    report = _report_from_rows(rows)
    report["matrix"] = {
        "manifest_path": str(manifest_path),
        "scale20_total_count": len(scale20_all),
        "scale20_probe_offset": offset,
        "scale20_probe_count": len(scale20_probe),
        "scale20_probe_modes": list(B2_MODES),
        "direct20_probe_time_limit_sec": float(direct20_probe_time_limit_sec),
        "notes": [
            "This artifact contains only the 20-scale selected direct20 probe rows.",
            f"20-scale selected direct20 probe used {len(scale20_probe)} instance(s) from offset {offset}, modes B0/B1A/B1B/B2A/B2B.",
        ],
    }
    report["acceptance"] = _acceptance(report["rows"], report["redlines"], matrix=report["matrix"])
    return report


def merge_b2_pricing_tail_reports(base_report: dict, extra_report: dict) -> dict:
    """Merge a direct20-only report into an existing matrix report."""

    base_rows = [
        {key: value for key, value in row.items() if not str(key).startswith("_")}
        for row in base_report.get("rows", [])
    ]
    extra_rows = [
        {key: value for key, value in row.items() if not str(key).startswith("_")}
        for row in extra_report.get("rows", [])
    ]
    extra_keys = {_row_identity(row) for row in extra_rows}
    merged_rows = [row for row in base_rows if _row_identity(row) not in extra_keys]
    merged_rows.extend(extra_rows)
    _annotate_instance_improvements(merged_rows)

    report = _report_from_rows(merged_rows)
    matrix = dict(base_report.get("matrix") or {})
    extra_matrix = extra_report.get("matrix") or {}
    direct20_rows = [row for row in merged_rows if row.get("matrix_group") == "20-scale selected direct20 probe"]
    direct20_instances = {str(row.get("instance_id")) for row in direct20_rows}
    direct20_modes = sorted({str(row.get("candidate_name")) for row in direct20_rows})
    matrix["scale20_probe_count"] = len(direct20_instances)
    matrix["scale20_probe_modes"] = direct20_modes or list(extra_matrix.get("scale20_probe_modes") or B2_MODES)
    if extra_matrix.get("direct20_probe_time_limit_sec") is not None:
        matrix["direct20_probe_time_limit_sec"] = float(extra_matrix["direct20_probe_time_limit_sec"])
    notes = list(matrix.get("notes") or [])
    for note in extra_matrix.get("notes") or []:
        if note not in notes:
            notes.append(note)
    if direct20_instances:
        merged_note = f"20-scale selected direct20 probe rows merged: {len(direct20_instances)} instance(s)."
        if merged_note not in notes:
            notes.append(merged_note)
    matrix["notes"] = notes
    report["matrix"] = matrix
    report["acceptance"] = _acceptance(report["rows"], report["redlines"], matrix=matrix)
    return report


def write_b2_pricing_tail_ablation_artifacts(
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
    with rows_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in report.get("rows", []):
            clean = {key: value for key, value in row.items() if not key.startswith("_")}
            writer.writerow(clean)
    summary_payload = {key: value for key, value in report.items() if key != "rows"}
    summary_payload["rows"] = [
        {key: value for key, value in row.items() if not key.startswith("_")}
        for row in report.get("rows", [])
    ]
    summary_json.write_text(json.dumps(summary_payload, indent=2, sort_keys=True), encoding="utf-8")
    report_md.write_text(render_b2_pricing_tail_markdown(report, rows_csv=rows_csv, summary_json=summary_json), encoding="utf-8")


def render_b2_pricing_tail_markdown(report: dict, *, rows_csv: str | Path, summary_json: str | Path) -> str:
    redlines = report.get("redlines") or {}
    acceptance = report.get("acceptance") or {}
    matrix = report.get("matrix") or {}
    lines = [
        "# B2 Pricing-Tail Optimization 消融报告",
        "",
        "## Completed Scope",
        "",
        "- 当前只评估 B2 root pricing-tail；不进入 B3 branch tree、B4 cuts/formulation、B5 GAT guidance。",
        "- B2B_seeded_tail_CG 是主模式；B2A_full_universe_rc_audit_fast_path 只作为显式 full-universe audit fast path。",
        "- completion-bound pruning 默认关闭；只保留 audit / ordering / profiling 语义。",
        "",
        "## Artifacts",
        "",
        f"- CSV rows: `{rows_csv}`",
        f"- JSON summary: `{summary_json}`",
        "",
        "## Baseline Comparison Matrix",
        "",
        f"- 5-scale full: {matrix.get('scale5_count', 0)} instances。",
        f"- 10-scale: {matrix.get('scale10_selected_count', 0)}/{matrix.get('scale10_total_count', 0)} instances。",
        f"- 20-scale fail-closed guard: {matrix.get('scale20_fail_closed_count', 0)} instances。",
        f"- 20-scale selected direct20 probe: {matrix.get('scale20_probe_count', 0)} instances。",
        f"- 20-scale selected direct20 probe modes: {', '.join(matrix.get('scale20_probe_modes') or [])}。",
        f"- 30-scale fail-closed diagnostic: {matrix.get('scale30_count', 0)} instances。",
        "",
        "## Redlines",
        "",
        "| metric | value | required |",
        "| --- | ---: | ---: |",
    ]
    for key in (
        "root_bound_gt_B0_violation_count",
        "direct_root_official_leak_count",
        "manual_rc_fail_count",
        "pricing_rc_fail_count",
        "certificate_scope_regression_count",
        "objective_mismatch_count",
        "b1_5scale_regression_count",
        "proof_debt_unreleased_certified_count",
    ):
        lines.append(f"| {key} | {redlines.get(key)} | 0 |")
    lines.extend([
        "",
        "## Summary",
        "",
        "| scale | group | candidate | runs | BPC node LP | fail-closed | timeout | mean wall | p90 wall | mean added | mean rounds | mean final judge | candidate negatives | addable negatives | duplicate-only | hidden-negative |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for row in report.get("summary_rows", []):
        lines.append(
            "| {scale} | {matrix_group} | {candidate_name} | {run_count} | {BPC_NODE_LP_CERTIFIED_count} | "
            "{fail_closed_count} | {timeout_count} | {mean_wall_time} | {p90_wall_time} | {mean_added_columns} | "
            "{mean_pricing_rounds} | {mean_final_judge_calls} | {candidate_negative_count} | {addable_negative_count} | "
            "{duplicate_only_count} | {hidden_negative_count} |".format(**row)
        )
    direct20_rows = [
        row for row in report.get("rows", [])
        if row.get("matrix_group") == "20-scale selected direct20 probe"
    ]
    if direct20_rows:
        b0_direct20 = [row for row in direct20_rows if row.get("candidate_name") == B0_MODE]
        bpc_direct20 = [row for row in direct20_rows if row.get("candidate_name") != B0_MODE]
        b0_solved = sum(1 for row in b0_direct20 if row.get("algorithm_status") == "DIRECT_DP_BASELINE_OPTIMAL")
        bpc_timeouts = sum(1 for row in bpc_direct20 if "row_time_limit_sec" in str(row.get("fail_closed_reason") or ""))
        b2b_improved = acceptance.get("b2b_real_scale_improvement_count", 0)
        lines.extend([
            "",
            "## 20-Scale Direct20 Probe Interpretation",
            "",
            f"- B0 direct20 solved rows: {b0_solved}/{len(b0_direct20)}。",
            f"- B1/B2 direct20 timeout rows: {bpc_timeouts}/{len(bpc_direct20)}。",
            "- 若 B0 direct20 闭合而 B1/B2 root rows timeout，本组应解释为 BPC root proof-tail 成本问题，不是 B0 direct-DP 失败。",
            f"- B2B real-scale improvement rows: {b2b_improved}。",
        ])
    lines.extend([
        "",
        "## Addability Breakdown",
        "",
        f"- candidate_negative_count: {report.get('totals', {}).get('candidate_negative_count', 0)}。",
        f"- addable_negative_count: {report.get('totals', {}).get('addable_negative_count', 0)}。",
        f"- duplicate_in_current_master_count: {report.get('totals', {}).get('duplicate_in_current_master_count', 0)}。",
        f"- in_pool_not_master_count: {report.get('totals', {}).get('in_pool_not_master_count', 0)}。",
        f"- forbidden_signature_count: {report.get('totals', {}).get('forbidden_signature_count', 0)}。",
        f"- branch_filtered_count: {report.get('totals', {}).get('branch_filtered_count', 0)}。",
        f"- cut_filtered_count: {report.get('totals', {}).get('cut_filtered_count', 0)}。",
        "",
        "## Duplicate-Only Audit Breakdown",
        "",
        f"- duplicate_only_count: {report.get('totals', {}).get('duplicate_only_count', 0)}。",
        f"- duplicate_only_audit_status_counts: {report.get('duplicate_only_audit_status_counts', {})}。",
        "",
        "## Hidden-Negative Audit",
        "",
        f"- hidden_negative_count: {report.get('totals', {}).get('hidden_negative_count', 0)}。",
        "",
        "## B2 Accepted?",
        "",
        f"- B2 accepted: {acceptance.get('b2_accepted')}。",
        f"- required coverage met: {acceptance.get('required_coverage_met')}。",
        f"- B2A fast path accepted as full-universe audit optimization: {acceptance.get('b2a_fast_path_accepted')}。",
        f"- B2B seeded tail accepted as next baseline: {acceptance.get('b2b_seeded_tail_accepted')}。",
        f"- improvement_count: {acceptance.get('improvement_count')}。",
        f"- reason: {acceptance.get('reason')}。",
    ])
    if matrix.get("notes"):
        lines.extend(["", "## Notes", ""])
        for note in matrix["notes"]:
            lines.append(f"- {note}")
    if int(matrix.get("scale20_fail_closed_count") or 0) > 0:
        lines.extend(
            [
                "- 20-scale fail-closed guard deliberately uses `max_direct_tasks < 20`; this group verifies fail-closed behavior only.",
                "- 20-scale fail-closed guard is not evidence that B0 direct20 failed or timed out.",
            ]
        )
    if int(matrix.get("scale20_probe_count") or 0) == 0:
        lines.append("- 20-scale selected direct20 probe did not run in this artifact; required coverage is incomplete.")
    lines.extend([
        "",
        "## B3 Entry",
        "",
        "- 只有 `b2b_seeded_tail_accepted=true` 且 redlines 全为 0 时，才允许把 B2B 作为进入 B3 的 accepted baseline。",
    ])
    return "\n".join(lines) + "\n"


def _run_guarded_mode(
    instance: dict,
    *,
    mode: str,
    baseline_cache: dict[str, dict],
    max_direct_tasks: int,
    b1_max_rounds: int,
    b2_max_rounds: int,
    matrix_group: str,
    row_time_limit_sec: float | None,
) -> dict:
    fn = lambda: _run_mode(
        instance,
        mode=mode,
        baseline_cache=baseline_cache,
        max_direct_tasks=max_direct_tasks,
        b1_max_rounds=b1_max_rounds,
        b2_max_rounds=b2_max_rounds,
        matrix_group=matrix_group,
    )
    if row_time_limit_sec is None:
        return fn()
    try:
        return _with_timeout(fn, float(row_time_limit_sec))
    except TimeoutError:
        data = load_lunar_ice_data(instance)
        return _timeout_row(
            data,
            mode=mode,
            max_direct_tasks=max_direct_tasks,
            matrix_group=matrix_group,
            row_time_limit_sec=float(row_time_limit_sec),
        )


def _run_mode(
    instance: dict,
    *,
    mode: str,
    baseline_cache: dict[str, dict],
    max_direct_tasks: int,
    b1_max_rounds: int,
    b2_max_rounds: int,
    matrix_group: str,
) -> dict:
    data = load_lunar_ice_data(instance)
    start = perf_counter()
    if mode == B0_MODE:
        result = solve_direct_journey_baseline(data, max_exact_tasks=max_direct_tasks)
        raw = {
            "algorithm_status": result.status,
            "certificate_scope": result.certificate_scope,
            "pricing_state": "",
            "uses_true_dual_bpc_certificate": False,
            "root_lp_bound": None,
            "root_lp_bound_official": False,
            "B0_direct_objective": result.objective,
            "root_bound_le_B0_objective": None,
            "pricing_round_count": 0,
            "final_judge_call_count": 0,
            "manual_rc_audit_pass": None,
            "pricing_rc_audit_pass": None,
            "proof_debt_unreleased_count": 0,
            "fail_closed_reason": "" if result.status == "DIRECT_DP_BASELINE_OPTIMAL" else result.note,
        }
        row = _row_from_raw(data, mode=mode, raw=raw, matrix_group=matrix_group, elapsed=perf_counter() - start)
        row["_raw_result"] = raw
        return row
    if mode == B1A_MODE:
        result = solve_b1_root_node_baseline(data, max_direct_tasks=max_direct_tasks, max_rounds=b1_max_rounds, seed_mode="full_universe")
        row = _row_from_raw(data, mode=mode, raw=result, matrix_group=matrix_group, elapsed=perf_counter() - start)
        row["_raw_result"] = result
        return row
    if mode == B1B_MODE:
        result = solve_b1_root_node_baseline(
            data,
            max_direct_tasks=max_direct_tasks,
            max_rounds=b1_max_rounds,
            seed_mode="b0_incumbent_plus_singletons",
        )
        row = _row_from_raw(data, mode=mode, raw=result, matrix_group=matrix_group, elapsed=perf_counter() - start)
        row["_raw_result"] = result
        return row
    if mode == B2A_MODE:
        result = solve_b2_pricing_tail_baseline(
            data,
            max_direct_tasks=max_direct_tasks,
            max_rounds=b2_max_rounds,
            mode=B2A_MODE,
            previous_baseline=baseline_cache.get(B1A_MODE),
        )
        row = _row_from_raw(data, mode=mode, raw=result, matrix_group=matrix_group, elapsed=perf_counter() - start)
        row["_raw_result"] = result
        return row
    if mode == B2B_MODE:
        result = solve_b2_pricing_tail_baseline(
            data,
            max_direct_tasks=max_direct_tasks,
            max_rounds=b2_max_rounds,
            mode=B2B_MODE,
            previous_baseline=baseline_cache.get(B1B_MODE),
        )
        row = _row_from_raw(data, mode=mode, raw=result, matrix_group=matrix_group, elapsed=perf_counter() - start)
        row["_raw_result"] = result
        return row
    raise ValueError(f"unsupported mode={mode!r}")


def _row_from_raw(data, *, mode: str, raw: dict, matrix_group: str, elapsed: float) -> dict:
    certified = raw.get("certificate_scope") == "BPC_NODE_LP_CERTIFIED"
    root_official = bool(raw.get("root_lp_bound_official"))
    root_le_b0 = raw.get("root_bound_le_direct_dp_integer_objective")
    if root_le_b0 is None:
        root_le_b0 = (raw.get("b0_ablation") or {}).get("root_bound_le_direct_dp_integer_objective")
    b0_obj = raw.get("B0_direct_objective")
    if b0_obj is None:
        b0_obj = (raw.get("b0_ablation") or {}).get("direct_dp_objective")
    baseline_name = _baseline_name(mode)
    candidate_name = mode
    row = {
        "matrix_group": matrix_group,
        "scale": len(data.task_ids),
        "instance_id": data.instance_id,
        "baseline_name": baseline_name,
        "candidate_name": candidate_name,
        "algorithm_status": raw.get("algorithm_status"),
        "certificate_scope": raw.get("certificate_scope"),
        "pricing_state": raw.get("pricing_state"),
        "uses_true_dual_bpc_certificate": bool(raw.get("uses_true_dual_bpc_certificate")),
        "official_lower_bound_source": _official_lower_bound_source(mode, raw),
        "official_lower_bound_scope": "BPC_NODE_LP_CERTIFIED" if root_official else "",
        "B0_direct_objective": b0_obj,
        "root_lp_bound": raw.get("root_lp_bound"),
        "root_lp_bound_official": root_official,
        "root_bound_le_B0_objective": root_le_b0,
        "pricing_round_count": int(raw.get("pricing_round_count") or 0),
        "final_judge_call_count": (
            0
            if mode == B0_MODE
            else int(raw["final_judge_call_count"])
            if "final_judge_call_count" in raw and raw.get("final_judge_call_count") is not None
            else int(raw.get("pricing_round_count") or 0)
        ),
        "candidate_negative_count": int(raw.get("candidate_negative_count") or raw.get("harvest_candidate_negative_count") or 0),
        "addable_negative_count": int(raw.get("addable_negative_count") or raw.get("harvest_addable_candidate_count") or 0),
        "duplicate_in_current_master_count": int(raw.get("duplicate_in_current_master_count") or 0),
        "in_pool_not_master_count": int(raw.get("in_pool_not_master_count") or 0),
        "forbidden_signature_count": int(raw.get("forbidden_signature_count") or 0),
        "branch_filtered_count": int(raw.get("branch_filtered_count") or 0),
        "cut_filtered_count": int(raw.get("cut_filtered_count") or 0),
        "selected_count": int(raw.get("selected_count") or raw.get("harvest_selected_count") or 0),
        "added_to_master_count": int(raw.get("added_to_master_count") or raw.get("added_column_count") or 0),
        "added_column_count": int(raw.get("added_column_count") or 0),
        "duplicate_only_count": int(raw.get("duplicate_only_count") or 0),
        "duplicate_only_audit_status": raw.get("duplicate_only_audit_status") or (raw.get("duplicate_only_audit") or {}).get("status") or "",
        "hidden_negative_count": int(raw.get("hidden_negative_count") or 0),
        "replacement_only_round_count": int(raw.get("replacement_only_round_count") or 0),
        "manual_rc_audit_pass": raw.get("manual_rc_audit_pass"),
        "pricing_rc_audit_pass": raw.get("pricing_rc_audit_pass"),
        "proof_debt_unreleased_count": int(raw.get("proof_debt_unreleased_count") or 0),
        "wall_time": round(elapsed, 6),
        "fail_closed_reason": "" if certified else str(raw.get("fail_closed_reason") or raw.get("note") or ""),
        "certificate_scope_regression": False,
        "objective_mismatch": False,
        "improvement_reason": "",
    }
    return row


def _timeout_row(data, *, mode: str, max_direct_tasks: int, matrix_group: str, row_time_limit_sec: float) -> dict:
    return {
        "matrix_group": matrix_group,
        "scale": len(data.task_ids),
        "instance_id": data.instance_id,
        "baseline_name": _baseline_name(mode),
        "candidate_name": mode,
        "algorithm_status": "DIRECT_DP_TIME_LIMIT" if mode == B0_MODE else "BPC_INCOMPLETE_PRICING",
        "certificate_scope": "FEASIBLE_INCUMBENT_ONLY",
        "pricing_state": "INCOMPLETE_LIMIT",
        "uses_true_dual_bpc_certificate": False,
        "official_lower_bound_source": "",
        "official_lower_bound_scope": "",
        "B0_direct_objective": None,
        "root_lp_bound": None,
        "root_lp_bound_official": False,
        "root_bound_le_B0_objective": None,
        "pricing_round_count": 0,
        "final_judge_call_count": 0,
        "candidate_negative_count": 0,
        "addable_negative_count": 0,
        "duplicate_in_current_master_count": 0,
        "in_pool_not_master_count": 0,
        "forbidden_signature_count": 0,
        "branch_filtered_count": 0,
        "cut_filtered_count": 0,
        "selected_count": 0,
        "added_to_master_count": 0,
        "added_column_count": 0,
        "duplicate_only_count": 0,
        "duplicate_only_audit_status": "",
        "hidden_negative_count": 0,
        "replacement_only_round_count": 0,
        "manual_rc_audit_pass": None,
        "pricing_rc_audit_pass": None,
        "proof_debt_unreleased_count": 0,
        "wall_time": round(float(row_time_limit_sec), 6),
        "fail_closed_reason": f"row_time_limit_sec={row_time_limit_sec} exceeded at max_direct_tasks={max_direct_tasks}",
        "certificate_scope_regression": False,
        "objective_mismatch": False,
        "improvement_reason": "",
    }


def _annotate_instance_improvements(rows: list[dict]) -> None:
    grouped: dict[tuple[str, str], dict[str, dict]] = {}
    for row in rows:
        key = (str(row.get("matrix_group")), str(row.get("instance_id")))
        grouped.setdefault(key, {})[str(row.get("candidate_name"))] = row
    for by_mode in grouped.values():
        _compare_candidate(by_mode, baseline=B1A_MODE, candidate=B2A_MODE)
        _compare_candidate(by_mode, baseline=B1B_MODE, candidate=B2B_MODE)


def _compare_candidate(by_mode: dict[str, dict], *, baseline: str, candidate: str) -> None:
    base = by_mode.get(baseline)
    cand = by_mode.get(candidate)
    if not base or not cand:
        return
    if base.get("certificate_scope") == "BPC_NODE_LP_CERTIFIED" and cand.get("certificate_scope") != "BPC_NODE_LP_CERTIFIED":
        cand["certificate_scope_regression"] = True
    if (
        base.get("root_lp_bound") not in {None, ""}
        and cand.get("root_lp_bound") not in {None, ""}
        and abs(float(base["root_lp_bound"]) - float(cand["root_lp_bound"])) > 1.0e-6
    ):
        cand["objective_mismatch"] = True
    reasons: list[str] = []
    if _float(cand.get("wall_time")) is not None and _float(base.get("wall_time")) is not None and _float(cand["wall_time"]) < _float(base["wall_time"]):
        reasons.append("wall_time_lower")
    if int(cand.get("final_judge_call_count") or 0) < int(base.get("final_judge_call_count") or 0):
        reasons.append("final_judge_call_count_lower")
    if int(cand.get("pricing_round_count") or 0) < int(base.get("pricing_round_count") or 0):
        reasons.append("pricing_round_count_lower")
    if not reasons and cand.get("fail_closed_reason") and cand.get("fail_closed_reason") != base.get("fail_closed_reason"):
        reasons.append("clearer_fail_closed_reason")
    cand["improvement_reason"] = ",".join(reasons)


def _report_from_rows(rows: list[dict]) -> dict:
    clean_rows = [{key: value for key, value in row.items() if not key.startswith("_")} for row in rows]
    summary_rows = _summary_rows(clean_rows)
    redlines = _redlines(clean_rows)
    return {
        "schema_version": "lunar_ice_bpc.b2_pricing_tail_ablation.v1",
        "rows": clean_rows,
        "row_count": len(clean_rows),
        "summary_rows": summary_rows,
        "redlines": redlines,
        "totals": _totals(clean_rows),
        "duplicate_only_audit_status_counts": _count(clean_rows, "duplicate_only_audit_status"),
        "acceptance": _acceptance(clean_rows, redlines),
    }


def _summary_rows(rows: list[dict]) -> list[dict]:
    groups: dict[tuple[int, str, str], list[dict]] = {}
    for row in rows:
        groups.setdefault((int(row["scale"]), str(row["matrix_group"]), str(row["candidate_name"])), []).append(row)
    out = []
    for (scale, group_name, candidate), group in sorted(groups.items()):
        walls = [_float(row.get("wall_time")) for row in group if _float(row.get("wall_time")) is not None]
        out.append(
            {
                "scale": scale,
                "matrix_group": group_name,
                "candidate_name": candidate,
                "run_count": len(group),
                "BPC_NODE_LP_CERTIFIED_count": sum(1 for row in group if row.get("certificate_scope") == "BPC_NODE_LP_CERTIFIED"),
                "fail_closed_count": sum(1 for row in group if row.get("certificate_scope") == "FEASIBLE_INCUMBENT_ONLY" or row.get("pricing_state") == "INCOMPLETE_LIMIT"),
                "timeout_count": sum(1 for row in group if "row_time_limit_sec" in str(row.get("fail_closed_reason") or "")),
                "mean_wall_time": round(mean(walls), 6) if walls else None,
                "p90_wall_time": _p90(walls),
                "mean_added_columns": _mean_int(group, "added_column_count"),
                "mean_pricing_rounds": _mean_int(group, "pricing_round_count"),
                "mean_final_judge_calls": _mean_int(group, "final_judge_call_count"),
                "candidate_negative_count": sum(int(row.get("candidate_negative_count") or 0) for row in group),
                "addable_negative_count": sum(int(row.get("addable_negative_count") or 0) for row in group),
                "duplicate_only_count": sum(int(row.get("duplicate_only_count") or 0) for row in group),
                "hidden_negative_count": sum(int(row.get("hidden_negative_count") or 0) for row in group),
            }
        )
    return out


def _redlines(rows: list[dict]) -> dict:
    certified = [row for row in rows if row.get("certificate_scope") == "BPC_NODE_LP_CERTIFIED"]
    return {
        "root_bound_gt_B0_violation_count": sum(1 for row in rows if row.get("root_bound_le_B0_objective") is False),
        "direct_root_official_leak_count": sum(1 for row in rows if row.get("official_lower_bound_source") == "direct_fixed_graph_root_lp"),
        "manual_rc_fail_count": sum(1 for row in certified if row.get("manual_rc_audit_pass") is not True),
        "pricing_rc_fail_count": sum(1 for row in certified if row.get("pricing_rc_audit_pass") is not True),
        "certificate_scope_regression_count": sum(1 for row in rows if row.get("certificate_scope_regression") is True),
        "objective_mismatch_count": sum(1 for row in rows if row.get("objective_mismatch") is True),
        "b1_5scale_regression_count": sum(
            1
            for row in rows
            if int(row.get("scale") or 0) == 5
            and row.get("candidate_name") in {B2A_MODE, B2B_MODE}
            and row.get("certificate_scope_regression") is True
        ),
        "proof_debt_unreleased_certified_count": sum(1 for row in certified if int(row.get("proof_debt_unreleased_count") or 0) > 0),
    }


def _totals(rows: list[dict]) -> dict:
    keys = (
        "candidate_negative_count",
        "addable_negative_count",
        "duplicate_in_current_master_count",
        "in_pool_not_master_count",
        "forbidden_signature_count",
        "branch_filtered_count",
        "cut_filtered_count",
        "selected_count",
        "added_to_master_count",
        "duplicate_only_count",
        "hidden_negative_count",
    )
    return {key: sum(int(row.get(key) or 0) for row in rows) for key in keys}


def _acceptance(rows: list[dict], redlines: dict, matrix: dict | None = None) -> dict:
    matrix = matrix or {}
    redlines_ok = all(int(value or 0) == 0 for value in redlines.values())
    b2a_improvements = [
        row for row in rows
        if row.get("candidate_name") == B2A_MODE and row.get("improvement_reason")
    ]
    b2b_improvements = [
        row for row in rows
        if row.get("candidate_name") == B2B_MODE and row.get("improvement_reason")
    ]
    b2b_real_scale_improvements = [
        row for row in b2b_improvements
        if (
            int(row.get("scale") or 0) in {10, 20}
            and row.get("matrix_group") in {"10-scale selected5", "10-scale full", "20-scale selected direct20 probe"}
        )
    ]
    coverage_met = bool(
        int(matrix.get("scale10_selected_count") or 0) >= 5
        and int(matrix.get("scale20_probe_count") or 0) >= 1
    )
    b2a_ok = bool(redlines_ok and b2a_improvements)
    b2b_ok = bool(redlines_ok and coverage_met and b2b_real_scale_improvements)
    accepted = bool(b2b_ok)
    if accepted:
        reason = "B2B improves seeded root tail on required 10/20 scale coverage without redline violations."
    elif not coverage_met:
        reason = "B2 remains diagnostic because required coverage is incomplete: need 10-scale selected>=5 and 20-scale selected direct20>=1."
    else:
        reason = "B2 remains diagnostic until B2B shows a 10/20-scale improvement without redline violations."
    return {
        "b2_accepted": accepted,
        "b2a_fast_path_accepted": b2a_ok,
        "b2b_seeded_tail_accepted": b2b_ok,
        "required_coverage_met": coverage_met,
        "improvement_count": len(b2a_improvements) + len(b2b_improvements),
        "b2a_improvement_count": len(b2a_improvements),
        "b2b_improvement_count": len(b2b_improvements),
        "b2b_real_scale_improvement_count": len(b2b_real_scale_improvements),
        "reason": reason,
    }


def _manifest_instance_paths(manifest_path: Path, project_root: Path, *, scale: int) -> list[Path]:
    manifest = read_json(manifest_path)
    rows = []
    for row in manifest.get("instances", []):
        if int(row.get("task_count") or row.get("scale") or 0) != int(scale):
            continue
        raw_path = row.get("path") or row.get("instance_path")
        if not raw_path:
            continue
        path = Path(raw_path)
        rows.append(path if path.is_absolute() else project_root / path)
    return rows


def _load_instance(item: dict | str | Path) -> dict:
    if isinstance(item, dict):
        return item
    return read_json(Path(item))


def _baseline_name(mode: str) -> str:
    if mode == B2A_MODE:
        return B1A_MODE
    if mode == B2B_MODE:
        return B1B_MODE
    if mode in {B1A_MODE, B1B_MODE}:
        return "accepted_B1"
    if mode == B0_MODE:
        return "fixed_graph_direct_dp_oracle"
    return ""


def _official_lower_bound_source(mode: str, raw: dict) -> str:
    if raw.get("root_lp_bound_official"):
        if mode == B2A_MODE:
            return "b2a_full_universe_membership_rc_audit"
        if mode == B2B_MODE:
            return "b2b_true_dual_pricing_closure"
        if mode in {B1A_MODE, B1B_MODE}:
            return "b1_root_true_dual_pricing_closure"
    return ""


def _count(rows: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _row_identity(row: dict) -> tuple[str, str, str, str]:
    return (
        str(row.get("matrix_group") or ""),
        str(row.get("scale") or ""),
        str(row.get("instance_id") or ""),
        str(row.get("candidate_name") or ""),
    )


def _mean_int(rows: list[dict], key: str) -> float:
    return round(mean([int(row.get(key) or 0) for row in rows]), 6) if rows else 0.0


def _p90(values: list[float]) -> float | None:
    if not values:
        return None
    values = sorted(values)
    index = min(len(values) - 1, int(0.9 * (len(values) - 1)))
    return round(values[index], 6)


def _float(value) -> float | None:
    if value in {None, ""}:
        return None
    return float(value)


def _with_timeout(fn: Callable[[], dict], seconds: float) -> dict:
    def _raise_timeout(signum, frame):  # noqa: ARG001
        raise TimeoutError

    old_handler = signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, float(seconds)))
    try:
        return fn()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
