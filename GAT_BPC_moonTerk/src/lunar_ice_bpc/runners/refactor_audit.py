"""Project-level acceptance audit for the lunar-ice refactor."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lunar_ice_bpc.domain.scenario import (
    DISALLOWED_LINK_KEYS,
    PATH_OPTION_POLICY_ID,
    RISK_SCHEMA_VERSION,
    SCALES,
    SYNTHETIC_GENERATOR_ID,
    TIME_WINDOW_POLICY_ID,
    scale_label,
)
from lunar_ice_bpc.io.instance_io import read_json, validate_instance, write_json


DEFAULT_BENCHMARK_AUDITS: dict[int, str] = {
    5: "runs/csv/lunar_ice_005_label_dp_benchmark_audit.json",
    10: "runs/csv/lunar_ice_010_label_dp_benchmark_audit.json",
    20: "runs/csv/lunar_ice_020_direct20_benchmark_audit.json",
    30: "runs/csv/lunar_ice_030_default_benchmark_audit.json",
    50: "runs/csv/lunar_ice_050_default_benchmark_audit.json",
    100: "runs/csv/lunar_ice_100_default_benchmark_audit.json",
}

DEFAULT_SHADOW_SUMMARIES: tuple[tuple[str, int], ...] = (
    ("runs/logs/gat_shadow_005_010_020_summary.json", 60),
    ("runs/logs/gat_shadow_all_summary.json", 120),
)

SCAN_SUFFIXES = {".py", ".yaml", ".yml", ".toml"}


def audit_refactor_state(
    project_root: str | Path,
    *,
    manifest_path: str | Path | None = None,
    output_json: str | Path | None = None,
    validate_all_instances: bool = False,
    instance_samples_per_scale: int = 1,
) -> dict[str, Any]:
    """Audit the current refactor state without claiming final completion prematurely."""

    root = Path(project_root).resolve()
    manifest = root / (manifest_path or "data/manifests/lunar_ice_benchmark_manifest.json")
    sections = {
        "runtime_legacy_link_scan": _audit_runtime_scan(root),
        "manifest": _audit_manifest(
            root,
            manifest,
            validate_all_instances=validate_all_instances,
            instance_samples_per_scale=instance_samples_per_scale,
        ),
        "gat_shadow": _audit_shadow_summaries(root),
        "benchmark_evidence": _audit_benchmark_evidence(root),
    }
    hard_failures = [
        section_name
        for section_name, section in sections.items()
        if str(section.get("status")) == "FAIL"
    ]
    incomplete = [
        section_name
        for section_name, section in sections.items()
        if str(section.get("status")) == "INCOMPLETE"
    ]
    if hard_failures:
        overall_status = "FAIL"
    elif incomplete:
        overall_status = "IN_PROGRESS"
    else:
        overall_status = "COMPLETE"
    payload = {
        "schema_version": "lunar_ice_bpc.refactor_audit.v1",
        "project_root": str(root),
        "overall_status": overall_status,
        "hard_failure_sections": hard_failures,
        "incomplete_sections": incomplete,
        "sections": sections,
        "note": (
            "COMPLETE means the current evidence satisfies this audit's project-level checks. "
            "IN_PROGRESS means no hard boundary violation was found, but planned final criteria remain open."
        ),
    }
    if output_json is not None:
        write_json(output_json, payload)
    return payload


def _audit_runtime_scan(root: Path) -> dict[str, Any]:
    roots: list[Path] = [root / "src", root / "scripts", root / "configs", root / "pyproject.toml"]
    occurrences: list[dict[str, Any]] = []
    files_scanned = 0
    for path in _iter_scan_files(roots):
        files_scanned += 1
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lowered = text.lower()
        for term in DISALLOWED_LINK_KEYS:
            needle = term.lower()
            if needle in lowered:
                occurrences.append({"path": str(path.relative_to(root)), "term": term})
    return {
        "status": "PASS" if not occurrences else "FAIL",
        "files_scanned": files_scanned,
        "occurrence_count": len(occurrences),
        "occurrences": occurrences[:50],
        "scan_roots": ["src", "scripts", "configs", "pyproject.toml"],
    }


def _iter_scan_files(roots: list[Path]):
    for root in roots:
        if root.is_file():
            if root.suffix in SCAN_SUFFIXES:
                yield root
            continue
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix in SCAN_SUFFIXES:
                yield path


def _audit_manifest(
    root: Path,
    manifest_path: Path,
    *,
    validate_all_instances: bool,
    instance_samples_per_scale: int,
) -> dict[str, Any]:
    if not manifest_path.exists():
        return {"status": "FAIL", "manifest_path": str(manifest_path), "issues": ["manifest file is missing"]}
    manifest = read_json(manifest_path)
    issues: list[str] = []
    if manifest.get("schema_version") != "lunar_ice_bpc.manifest.v1":
        issues.append("unexpected manifest schema_version")
    if manifest.get("status") != "complete":
        issues.append("manifest status is not complete")
    if manifest.get("accepted_total_count") != 120:
        issues.append("accepted_total_count is not 120")
    if manifest.get("total_target_count") != 120:
        issues.append("total_target_count is not 120")
    if manifest.get("generator") != SYNTHETIC_GENERATOR_ID:
        issues.append("unexpected generator id")
    if manifest.get("risk_schema_version") != RISK_SCHEMA_VERSION:
        issues.append("unexpected risk schema version")
    if manifest.get("time_window_policy_id") != TIME_WINDOW_POLICY_ID:
        issues.append("unexpected time-window policy id")
    if manifest.get("path_option_policy_id") != PATH_OPTION_POLICY_ID:
        issues.append("unexpected path-option policy id")

    scale_counts: dict[str, int] = {}
    rows_by_scale: dict[str, list[dict[str, Any]]] = {scale_label(scale): [] for scale in SCALES}
    for row in manifest.get("instances", []):
        label = _row_scale_label(row)
        if label in rows_by_scale:
            rows_by_scale[label].append(row)
        scale_counts[label] = scale_counts.get(label, 0) + 1

    for scale in SCALES:
        label = scale_label(scale)
        scale_row = (manifest.get("scales") or {}).get(label, {})
        if scale_row.get("accepted_count") != 20:
            issues.append(f"{label}: accepted_count is not 20")
        if scale_row.get("status") != "complete":
            issues.append(f"{label}: scale status is not complete")
        if len(rows_by_scale[label]) != 20:
            issues.append(f"{label}: manifest instance row count is not 20")
        if scale_row.get("risk_schema_version") != RISK_SCHEMA_VERSION:
            issues.append(f"{label}: unexpected risk schema version")
        if scale_row.get("time_window_policy_id") != TIME_WINDOW_POLICY_ID:
            issues.append(f"{label}: unexpected time-window policy id")
        if scale_row.get("path_option_policy_id") != PATH_OPTION_POLICY_ID:
            issues.append(f"{label}: unexpected path-option policy id")

    selected_rows = _selected_instance_rows(rows_by_scale, validate_all_instances, instance_samples_per_scale)
    missing_paths: list[str] = []
    validation_issues: list[dict[str, Any]] = []
    for row in selected_rows:
        path = _root_path(root, row.get("path", ""))
        if not path.exists():
            missing_paths.append(str(path))
            continue
        instance = read_json(path)
        instance_issues = validate_instance(instance)
        if instance_issues:
            validation_issues.append({"path": str(path.relative_to(root)), "issues": instance_issues[:20]})

    if missing_paths:
        issues.append(f"{len(missing_paths)} selected instance paths are missing")
    if validation_issues:
        issues.append(f"{len(validation_issues)} selected instances failed validation")

    return {
        "status": "PASS" if not issues else "FAIL",
        "manifest_path": str(manifest_path),
        "accepted_total_count": manifest.get("accepted_total_count"),
        "scale_instance_counts": {label: len(rows_by_scale[label]) for label in rows_by_scale},
        "validated_instance_count": len(selected_rows) - len(missing_paths),
        "validate_all_instances": bool(validate_all_instances),
        "instance_samples_per_scale": None if validate_all_instances else int(instance_samples_per_scale),
        "issues": issues,
        "missing_paths": missing_paths[:20],
        "validation_issues": validation_issues[:20],
    }


def _selected_instance_rows(
    rows_by_scale: dict[str, list[dict[str, Any]]],
    validate_all_instances: bool,
    instance_samples_per_scale: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label in sorted(rows_by_scale):
        scale_rows = rows_by_scale[label]
        if validate_all_instances:
            rows.extend(scale_rows)
        else:
            rows.extend(scale_rows[: max(0, int(instance_samples_per_scale))])
    return rows


def _audit_shadow_summaries(root: Path) -> dict[str, Any]:
    issues: list[str] = []
    summaries: list[dict[str, Any]] = []
    for relative_path, expected_count in DEFAULT_SHADOW_SUMMARIES:
        path = root / relative_path
        if not path.exists():
            issues.append(f"{relative_path}: summary file is missing")
            continue
        payload = read_json(path)
        summary_issues = []
        if payload.get("schema_version") != "lunar_ice_bpc.gat_shadow_summary.v1":
            summary_issues.append("unexpected schema_version")
        if payload.get("run_count") != expected_count or payload.get("report_count") != expected_count:
            summary_issues.append("unexpected report count")
        if payload.get("mode_counts") != {"shadow_only": expected_count}:
            summary_issues.append("unexpected mode_counts")
        if payload.get("mutates_solver_count") != 0:
            summary_issues.append("mutates_solver_count is not zero")
        if payload.get("can_certify_count") != 0:
            summary_issues.append("can_certify_count is not zero")
        if payload.get("exact_status_effect_counts") != {"none": expected_count}:
            summary_issues.append("unexpected exact_status_effect_counts")
        if summary_issues:
            issues.extend(f"{relative_path}: {item}" for item in summary_issues)
        summaries.append(
            {
                "path": relative_path,
                "expected_count": expected_count,
                "run_count": payload.get("run_count"),
                "mode_counts": payload.get("mode_counts"),
                "mutates_solver_count": payload.get("mutates_solver_count"),
                "can_certify_count": payload.get("can_certify_count"),
                "exact_status_effect_counts": payload.get("exact_status_effect_counts"),
            }
        )
    return {"status": "PASS" if not issues else "FAIL", "summaries": summaries, "issues": issues}


def _audit_benchmark_evidence(root: Path) -> dict[str, Any]:
    issues: list[str] = []
    incomplete: list[str] = []
    scales: dict[str, dict[str, Any]] = {}
    for scale, relative_path in DEFAULT_BENCHMARK_AUDITS.items():
        label = scale_label(scale)
        path = root / relative_path
        if not path.exists():
            incomplete.append(f"{label}: benchmark audit file is missing")
            scales[label] = {"status": "MISSING", "path": relative_path}
            continue
        payload = read_json(path)
        scale_payload = (payload.get("scales") or {}).get(label, {})
        final_status = str(scale_payload.get("status") or payload.get("overall_status") or "missing")
        exact_count = int(scale_payload.get("exact_optimal_count") or 0)
        required_exact = int(scale_payload.get("required_exact_optimal_count") or 0)
        valid_gap_count = int(scale_payload.get("valid_gap_count") or 0)
        pricing_count = int(scale_payload.get("pricing_workload_reported_count") or 0)
        incomplete_reason_count = int(scale_payload.get("incomplete_reason_reported_count") or 0)
        run_count = int(scale_payload.get("run_count") or 0)
        true_dual_count = int(scale_payload.get("true_dual_bpc_certificate_count") or 0)
        closure_closed_count = int(scale_payload.get("fixed_graph_pricing_closure_closed_count") or 0)
        closure_diagnostic_only_count = int(
            scale_payload.get("fixed_graph_pricing_closure_diagnostic_only_count") or 0
        )
        completion_bound_consistency_pass_count = int(
            scale_payload.get("completion_bound_consistency_pass_count") or 0
        )
        true_dual_tail_certified_count = int(scale_payload.get("true_dual_pricing_tail_certified_count") or 0)
        true_dual_tail_not_ported_count = int(scale_payload.get("true_dual_pricing_tail_not_ported_count") or 0)
        true_dual_tail_dual_bound_count = int(
            scale_payload.get("true_dual_pricing_tail_dual_vector_bound_count") or 0
        )
        readiness_waiting_count = int(scale_payload.get("true_dual_readiness_waiting_true_dual_count") or 0)
        scale_record = {
            "path": relative_path,
            "audit_status": final_status,
            "run_count": run_count,
            "exact_optimal_count": exact_count,
            "required_exact_optimal_count": required_exact,
            "valid_gap_count": valid_gap_count,
            "pricing_workload_reported_count": pricing_count,
            "incomplete_reason_reported_count": incomplete_reason_count,
            "true_dual_bpc_certificate_count": true_dual_count,
            "fixed_graph_pricing_closure_closed_count": closure_closed_count,
            "fixed_graph_pricing_closure_diagnostic_only_count": closure_diagnostic_only_count,
            "completion_bound_consistency_pass_count": completion_bound_consistency_pass_count,
            "true_dual_pricing_tail_certified_count": true_dual_tail_certified_count,
            "true_dual_pricing_tail_not_ported_count": true_dual_tail_not_ported_count,
            "true_dual_pricing_tail_dual_vector_bound_count": true_dual_tail_dual_bound_count,
            "true_dual_readiness_waiting_true_dual_count": readiness_waiting_count,
            "mean_optimal_wall_time_sec": scale_payload.get("mean_optimal_wall_time_sec"),
        }
        scales[label] = scale_record
        if scale in {5, 10, 20, 100} and final_status != "PASS":
            issues.append(f"{label}: expected current audit PASS, got {final_status}")
        if scale in {30, 50} and final_status != "PASS":
            if valid_gap_count == run_count == 20 and pricing_count == 20 and incomplete_reason_count == 20:
                incomplete.append(f"{label}: final exact closure target is not met yet")
            else:
                issues.append(f"{label}: benchmark is neither accepted nor complete scalable evidence")
    true_dual_total = sum(int(row.get("true_dual_bpc_certificate_count") or 0) for row in scales.values())
    if true_dual_total == 0:
        incomplete.append("true-dual BPC certificate path is not ported yet")
    if issues:
        status = "FAIL"
    elif incomplete:
        status = "INCOMPLETE"
    else:
        status = "PASS"
    return {
        "status": status,
        "scales": scales,
        "true_dual_bpc_certificate_total": true_dual_total,
        "issues": issues,
        "incomplete": incomplete,
    }


def _row_scale_label(row: dict[str, Any]) -> str:
    if row.get("scale_label") is not None:
        return f"{int(str(row['scale_label']).strip()):03d}"
    if row.get("scale") is not None:
        return scale_label(int(row["scale"]))
    path = str(row.get("path", ""))
    for scale in SCALES:
        label = scale_label(scale)
        if f"lunar_ice_{label}" in path:
            return label
    return ""


def _root_path(root: Path, value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else root / path
