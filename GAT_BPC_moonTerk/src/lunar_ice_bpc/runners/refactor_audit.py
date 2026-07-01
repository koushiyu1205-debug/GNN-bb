"""Project-level acceptance audit for the lunar-ice refactor."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from lunar_ice_bpc.domain.scenario import (
    DISALLOWED_LINK_KEYS,
    SCALES,
    SYNTHETIC_GENERATOR_ID,
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

DEFAULT_B5_GUIDANCE_SUITE_SUMMARIES: tuple[dict[str, Any], ...] = (
    {
        "ab_mode": "shadow_only",
        "path": "runs/logs/b5_guidance_suite_summary.json",
        "expected_count": 40,
        "expected_scale_counts": {"5": 20, "10": 20},
        "expected_mode_counts": {"shadow_only": 40},
        "expected_enabled_ordering_modes": [],
    },
    {
        "ab_mode": "all_ordering_opt_in",
        "path": "runs/logs/b5_guidance_ordering_suite_summary.json",
        "expected_count": 40,
        "expected_scale_counts": {"5": 20, "10": 20},
        "expected_mode_counts": {"ordering_opt_in": 40},
        "expected_enabled_ordering_modes": ["branch", "harvest", "pricing"],
    },
    {
        "ab_mode": "pricing_ordering_opt_in",
        "path": "runs/logs/b5_guidance_pricing_ordering_suite_summary.json",
        "expected_count": 40,
        "expected_scale_counts": {"5": 20, "10": 20},
        "expected_mode_counts": {"ordering_opt_in": 40},
        "expected_enabled_ordering_modes": ["pricing"],
    },
    {
        "ab_mode": "branch_ordering_opt_in",
        "path": "runs/logs/b5_guidance_branch_ordering_suite_summary.json",
        "expected_count": 40,
        "expected_scale_counts": {"5": 20, "10": 20},
        "expected_mode_counts": {"ordering_opt_in": 40},
        "expected_enabled_ordering_modes": ["branch"],
    },
    {
        "ab_mode": "harvest_ordering_opt_in",
        "path": "runs/logs/b5_guidance_harvest_ordering_suite_summary.json",
        "expected_count": 40,
        "expected_scale_counts": {"5": 20, "10": 20},
        "expected_mode_counts": {"ordering_opt_in": 40},
        "expected_enabled_ordering_modes": ["harvest"],
    },
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
        "b5_guidance_suite": _audit_b5_guidance_suite(root),
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
            if _contains_disallowed_runtime_term(lowered, needle):
                occurrences.append({"path": str(path.relative_to(root)), "term": term})
    return {
        "status": "PASS" if not occurrences else "FAIL",
        "files_scanned": files_scanned,
        "occurrence_count": len(occurrences),
        "occurrences": occurrences[:50],
        "scan_roots": ["src", "scripts", "configs", "pyproject.toml"],
    }


def _contains_disallowed_runtime_term(text: str, needle: str) -> bool:
    if needle.isalnum():
        return re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", text) is not None
    return needle in text


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
    manifest_risk_schema = manifest.get("risk_schema_version")
    manifest_time_window_policy = manifest.get("time_window_policy_id")
    manifest_path_option_policy = manifest.get("path_option_policy_id")
    if not manifest_risk_schema:
        issues.append("manifest risk_schema_version is missing")
    if not manifest_time_window_policy:
        issues.append("manifest time_window_policy_id is missing")
    if not manifest_path_option_policy:
        issues.append("manifest path_option_policy_id is missing")

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
        if scale_row.get("risk_schema_version") != manifest_risk_schema:
            issues.append(f"{label}: risk schema version differs from manifest root")
        if scale_row.get("time_window_policy_id") != manifest_time_window_policy:
            issues.append(f"{label}: time-window policy id differs from manifest root")
        if scale_row.get("path_option_policy_id") != manifest_path_option_policy:
            issues.append(f"{label}: path-option policy id differs from manifest root")

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

    if validation_issues:
        issues.append(f"{len(validation_issues)} selected instances failed validation")

    return {
        "status": "PASS" if not issues else "FAIL",
        "manifest_path": str(manifest_path),
        "accepted_total_count": manifest.get("accepted_total_count"),
        "risk_schema_version": manifest_risk_schema,
        "time_window_policy_id": manifest_time_window_policy,
        "path_option_policy_id": manifest_path_option_policy,
        "scale_instance_counts": {label: len(rows_by_scale[label]) for label in rows_by_scale},
        "validated_instance_count": len(selected_rows),
        "existing_instance_validation_count": len(selected_rows) - len(missing_paths),
        "missing_selected_instance_count": len(missing_paths),
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


def _audit_b5_guidance_suite(root: Path) -> dict[str, Any]:
    issues: list[str] = []
    incomplete: list[str] = []
    summaries: list[dict[str, Any]] = []
    matrix_rows: list[dict[str, Any]] = []
    for expected in DEFAULT_B5_GUIDANCE_SUITE_SUMMARIES:
        ab_mode = str(expected["ab_mode"])
        relative_path = str(expected["path"])
        expected_count = int(expected["expected_count"])
        expected_scale_counts = dict(expected.get("expected_scale_counts") or {})
        expected_mode_counts = dict(expected.get("expected_mode_counts") or {})
        expected_enabled_ordering_modes = list(expected.get("expected_enabled_ordering_modes") or [])
        path = root / relative_path
        if not path.exists():
            incomplete.append(f"{relative_path}: B5 guidance suite summary is missing")
            continue
        payload = read_json(path)
        workload_observed_count = _b5_guidance_workload_observed_count(payload)
        summary_issues = _b5_guidance_suite_issues(
            payload,
            expected_count,
            expected_scale_counts=expected_scale_counts,
            expected_mode_counts=expected_mode_counts,
            expected_enabled_ordering_modes=expected_enabled_ordering_modes,
        )
        if summary_issues:
            issues.extend(f"{relative_path}: {item}" for item in summary_issues)
        summaries.append(
            {
                "ab_mode": ab_mode,
                "path": relative_path,
                "expected_count": expected_count,
                "row_count": payload.get("row_count"),
                "suite_do_no_harm_pass": payload.get("suite_do_no_harm_pass"),
                "mode_counts": payload.get("mode_counts"),
                "scale_counts": payload.get("scale_counts"),
                "certificate_scope_counts": payload.get("certificate_scope_counts"),
                "suite_performance_success_count": payload.get("suite_performance_success_count"),
                "do_no_harm_fail_count": payload.get("do_no_harm_fail_count"),
                "certificate_scope_diff_count": payload.get("certificate_scope_diff_count"),
                "additional_bpc_incomplete_count": payload.get("additional_bpc_incomplete_count"),
                "workload_observed_count": workload_observed_count,
                "runner": payload.get("runner", {}),
            }
        )
        runner = payload.get("runner") if isinstance(payload.get("runner"), dict) else {}
        matrix_rows.append(
            {
                "ab_mode": ab_mode,
                "path": relative_path,
                "row_count": int(payload.get("row_count") or 0),
                "scale_counts": payload.get("scale_counts") if isinstance(payload.get("scale_counts"), dict) else {},
                "enabled_ordering_modes": list(runner.get("enabled_ordering_modes") or []),
                "suite_do_no_harm_pass": bool(payload.get("suite_do_no_harm_pass")),
                "workload_observed_count": workload_observed_count,
                "suite_performance_success_count": int(payload.get("suite_performance_success_count") or 0),
            }
        )
    if issues:
        status = "FAIL"
    elif incomplete:
        status = "INCOMPLETE"
    else:
        status = "PASS"
    matrix_summary = _b5_guidance_ab_matrix_summary(matrix_rows, incomplete)
    return {
        "status": status,
        "summaries": summaries,
        "matrix_summary": matrix_summary,
        "issues": issues,
        "incomplete": incomplete,
    }


def _b5_guidance_ab_matrix_summary(
    matrix_rows: list[dict[str, Any]],
    incomplete: list[str],
) -> dict[str, Any]:
    required_ab_modes = [str(item["ab_mode"]) for item in DEFAULT_B5_GUIDANCE_SUITE_SUMMARIES]
    observed_ab_modes = [str(row["ab_mode"]) for row in matrix_rows]
    missing_ab_modes = [mode for mode in required_ab_modes if mode not in set(observed_ab_modes)]
    row_counts_by_mode = {str(row["ab_mode"]): int(row.get("row_count") or 0) for row in matrix_rows}
    workload_observed_by_mode = {
        str(row["ab_mode"]): int(row.get("workload_observed_count") or 0) for row in matrix_rows
    }
    performance_success_count_by_mode = {
        str(row["ab_mode"]): int(row.get("suite_performance_success_count") or 0) for row in matrix_rows
    }
    expected_count_by_mode = {
        str(item["ab_mode"]): int(item["expected_count"]) for item in DEFAULT_B5_GUIDANCE_SUITE_SUMMARIES
    }
    enabled_ordering_modes_by_mode = {
        str(row["ab_mode"]): list(row.get("enabled_ordering_modes") or []) for row in matrix_rows
    }
    scale_counts_by_mode = {
        str(row["ab_mode"]): dict(row.get("scale_counts") or {}) for row in matrix_rows
    }
    all_suites_do_no_harm_pass = (
        not missing_ab_modes
        and not incomplete
        and all(bool(row.get("suite_do_no_harm_pass")) for row in matrix_rows)
    )
    all_suites_workload_observed = (
        not missing_ab_modes
        and not incomplete
        and all(
            workload_observed_by_mode.get(mode, 0) == expected_count_by_mode[mode]
            for mode in required_ab_modes
        )
    )
    any_performance_success = any(count > 0 for count in performance_success_count_by_mode.values())
    if missing_ab_modes:
        performance_claim_status = "MISSING_AB_MODES"
    elif any_performance_success and all_suites_do_no_harm_pass and all_suites_workload_observed:
        performance_claim_status = "PERFORMANCE_SUCCESS_OBSERVED"
    else:
        performance_claim_status = "NO_IMPROVEMENT_DRY_RUN"
    return {
        "schema_version": "lunar_ice_bpc.b5_guidance_ab_matrix_summary.v1",
        "expected_suite_count": len(required_ab_modes),
        "observed_suite_count": len(matrix_rows),
        "required_ab_modes": required_ab_modes,
        "observed_ab_modes": observed_ab_modes,
        "missing_ab_modes": missing_ab_modes,
        "row_counts_by_mode": row_counts_by_mode,
        "scale_counts_by_mode": scale_counts_by_mode,
        "enabled_ordering_modes_by_mode": enabled_ordering_modes_by_mode,
        "workload_observed_by_mode": workload_observed_by_mode,
        "all_suites_do_no_harm_pass": all_suites_do_no_harm_pass,
        "all_suites_workload_observed": all_suites_workload_observed,
        "performance_success_count_by_mode": performance_success_count_by_mode,
        "any_performance_success": any_performance_success,
        "performance_claim_allowed": performance_claim_status == "PERFORMANCE_SUCCESS_OBSERVED",
        "performance_claim_status": performance_claim_status,
        "random_row_split_is_main_claim": False,
    }


def _b5_guidance_workload_observed_count(payload: dict[str, Any]) -> int:
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    observed_count = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        result = row.get("result") if isinstance(row.get("result"), dict) else {}
        workload = result.get("workload_ablation") if isinstance(result.get("workload_ablation"), dict) else {}
        if (
            bool(workload.get("workload_observed"))
            and str(workload.get("observation_source")) == "dry_run_no_solver_mutation_zero_diff"
            and str(workload.get("workload_units")) == "guidance_delta_proxy"
        ):
            observed_count += 1
    return observed_count


def _b5_guidance_suite_issues(
    payload: dict[str, Any],
    expected_count: int,
    *,
    expected_scale_counts: dict[str, int],
    expected_mode_counts: dict[str, int],
    expected_enabled_ordering_modes: list[str],
) -> list[str]:
    issues: list[str] = []
    if payload.get("schema_version") != "lunar_ice_bpc.b5_guidance_ablation_suite.v1":
        issues.append("unexpected schema_version")
    if int(payload.get("row_count") or 0) != expected_count:
        issues.append("unexpected row_count")
    scale_counts = payload.get("scale_counts") if isinstance(payload.get("scale_counts"), dict) else {}
    normalized_scale_counts = {str(key): int(value) for key, value in scale_counts.items()}
    if normalized_scale_counts != {str(key): int(value) for key, value in expected_scale_counts.items()}:
        issues.append("unexpected scale_counts")
    mode_counts = payload.get("mode_counts") if isinstance(payload.get("mode_counts"), dict) else {}
    normalized_mode_counts = {str(key): int(value) for key, value in mode_counts.items()}
    if normalized_mode_counts != {str(key): int(value) for key, value in expected_mode_counts.items()}:
        issues.append("unexpected mode_counts")
    if not bool(payload.get("suite_do_no_harm_pass")):
        issues.append("suite_do_no_harm_pass is not true")
    if int(payload.get("do_no_harm_fail_count") or 0) != 0:
        issues.append("do_no_harm_fail_count is not zero")
    if int(payload.get("certificate_scope_diff_count") or 0) != 0:
        issues.append("certificate_scope_diff_count is not zero")
    if int(payload.get("additional_bpc_incomplete_count") or 0) != 0:
        issues.append("additional_bpc_incomplete_count is not zero")
    split_policy = payload.get("split_policy") if isinstance(payload.get("split_policy"), dict) else {}
    if split_policy.get("main_split_keys") != ["instance", "scale", "seed_family"]:
        issues.append("unexpected split_policy main keys")
    if bool(split_policy.get("random_row_split_is_main_claim", True)):
        issues.append("random_row_split_is_main_claim is not false")
    runner = payload.get("runner") if isinstance(payload.get("runner"), dict) else {}
    if runner.get("schema_version") != "lunar_ice_bpc.b5_guidance_suite_runner.v1":
        issues.append("unexpected runner schema_version")
    if int(runner.get("instance_count") or 0) != expected_count:
        issues.append("unexpected runner instance_count")
    if bool(runner.get("mutates_solver")):
        issues.append("runner mutates_solver is not false")
    if bool(runner.get("can_certify")):
        issues.append("runner can_certify is not false")
    if str(runner.get("exact_status_effect")) != "none":
        issues.append("runner exact_status_effect is not none")
    enabled_ordering_modes = sorted(str(mode) for mode in runner.get("enabled_ordering_modes", []))
    if enabled_ordering_modes != sorted(str(mode) for mode in expected_enabled_ordering_modes):
        issues.append("unexpected runner enabled_ordering_modes")
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    if len(rows) != expected_count:
        issues.append("unexpected row payload count")
    row_issue_count = 0
    for row in rows:
        if not isinstance(row, dict):
            row_issue_count += 1
            continue
        row_issue_count += len(_b5_guidance_row_issues(row))
    if row_issue_count:
        issues.append(f"{row_issue_count} row-level B5 guidance safety issues")
    return issues


def _b5_guidance_row_issues(row: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if not bool(row.get("do_no_harm_pass")):
        issues.append("row do_no_harm_pass is not true")
    if row.get("certificate_scope_diff"):
        issues.append("row certificate_scope_diff is non-empty")
    if int(row.get("BPC_INCOMPLETE_count_diff") or 0) != 0:
        issues.append("row BPC_INCOMPLETE_count_diff is not zero")
    if not bool(row.get("guidance_output_required_heads_present")):
        issues.append("row guidance output required heads missing")
    workload_diffs = row.get("workload_diffs") if isinstance(row.get("workload_diffs"), dict) else {}
    for key in ("wall_time", "pricing_calls", "final_judge_calls", "generated_labels", "rmp_iterations", "node_count"):
        if workload_diffs.get(key) is None:
            issues.append(f"row workload diff {key} is missing")
        elif float(workload_diffs.get(key) or 0.0) != 0.0:
            issues.append(f"row workload diff {key} is not zero")
    if bool(row.get("performance_success")):
        issues.append("row performance_success is not false")
    performance_gate_issues = [str(item) for item in row.get("performance_gate_issues", [])]
    if "workload_ablation_missing" in performance_gate_issues:
        issues.append("row workload_ablation_missing is present")
    if "no_workload_metric_improved" not in performance_gate_issues:
        issues.append("row no_workload_metric_improved gate issue is missing")
    head_counts = row.get("guidance_output_head_counts") if isinstance(row.get("guidance_output_head_counts"), dict) else {}
    for head_name in ("pricing_priority_head", "branch_priority_head", "harvest_priority_head"):
        if int(head_counts.get(head_name) or 0) <= 0:
            issues.append(f"row {head_name} count is not positive")
    result = row.get("result") if isinstance(row.get("result"), dict) else {}
    for key in ("guidance_can_construct_certificate", "guidance_can_mutate_exact_state", "mutates_solver", "can_certify"):
        if bool(result.get(key)):
            issues.append(f"row result {key} is not false")
    if str(result.get("exact_status_effect")) != "none":
        issues.append("row result exact_status_effect is not none")
    workload = result.get("workload_ablation") if isinstance(result.get("workload_ablation"), dict) else {}
    if not bool(workload.get("workload_observed")):
        issues.append("row workload_ablation workload_observed is not true")
    if str(workload.get("observation_source")) != "dry_run_no_solver_mutation_zero_diff":
        issues.append("row workload observation_source is unexpected")
    if str(workload.get("workload_units")) != "guidance_delta_proxy":
        issues.append("row workload_units is unexpected")
    bundle = result.get("guidance_output_bundle") if isinstance(result.get("guidance_output_bundle"), dict) else {}
    for key in (
        "diagnostics_can_certify",
        "diagnostics_lower_bound_official",
        "guidance_can_construct_certificate",
        "guidance_can_mutate_exact_state",
        "mutates_solver",
        "can_certify",
        "can_fathom",
        "can_prune",
    ):
        if bool(bundle.get(key)):
            issues.append(f"row guidance bundle {key} is not false")
    if not bool(bundle.get("diagnostic_versions_complete")):
        issues.append("row diagnostic versions are incomplete")
    if bundle.get("diagnostic_version_issues"):
        issues.append("row diagnostic_version_issues is non-empty")
    if str(bundle.get("exact_status_effect")) != "none":
        issues.append("row guidance bundle exact_status_effect is not none")
    return issues


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
            "checks": scale_payload.get("checks", {}),
            "true_dual_pricing_tail_status_counts": scale_payload.get(
                "true_dual_pricing_tail_status_counts", {}
            ),
            "true_dual_readiness_status_counts": scale_payload.get("true_dual_readiness_status_counts", {}),
            "pricing_certificate_status_counts": scale_payload.get("pricing_certificate_status_counts", {}),
            "bpc_certificate_status_counts": scale_payload.get("bpc_certificate_status_counts", {}),
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
        "closure_gap_summary": _benchmark_closure_gap_summary(scales),
        "true_dual_bpc_certificate_total": true_dual_total,
        "issues": issues,
        "incomplete": incomplete,
    }


def _benchmark_closure_gap_summary(scales: dict[str, dict[str, Any]]) -> dict[str, Any]:
    target_labels = ["030", "050"]
    blockers: dict[str, dict[str, Any]] = {}
    for label in target_labels:
        row = scales.get(label, {})
        run_count = int(row.get("run_count") or 0)
        exact_count = int(row.get("exact_optimal_count") or 0)
        required_exact = int(row.get("required_exact_optimal_count") or 0)
        checks = row.get("checks") if isinstance(row.get("checks"), dict) else {}
        blockers[label] = {
            "audit_status": row.get("audit_status"),
            "run_count": run_count,
            "required_exact_optimal_count": required_exact,
            "exact_optimal_count": exact_count,
            "missing_exact_optimal_count": max(0, required_exact - exact_count),
            "scalable_diagnostic_evidence_complete": bool(
                run_count == 20
                and int(row.get("valid_gap_count") or 0) == run_count
                and int(row.get("pricing_workload_reported_count") or 0) == run_count
                and int(row.get("incomplete_reason_reported_count") or 0) == run_count
            ),
            "exact_count_target_met": bool(checks.get("exact_count_target_met")),
            "true_dual_bpc_certificate_count": int(row.get("true_dual_bpc_certificate_count") or 0),
            "true_dual_pricing_tail_certified_count": int(
                row.get("true_dual_pricing_tail_certified_count") or 0
            ),
            "true_dual_pricing_tail_status_counts": dict(
                row.get("true_dual_pricing_tail_status_counts") or {}
            ),
            "true_dual_readiness_status_counts": dict(row.get("true_dual_readiness_status_counts") or {}),
            "bpc_certificate_status_counts": dict(row.get("bpc_certificate_status_counts") or {}),
            "next_required_evidence": (
                "produce true-dual no-negative closure and exact optimal rows; "
                "diagnostic gap/workload evidence alone is insufficient"
            ),
        }
    total_missing_exact = sum(int(row.get("missing_exact_optimal_count") or 0) for row in blockers.values())
    return {
        "schema_version": "lunar_ice_bpc.benchmark_closure_gap_summary.v1",
        "target_scale_labels": target_labels,
        "blocking_scale_labels": [
            label for label, row in blockers.items() if int(row.get("missing_exact_optimal_count") or 0) > 0
        ],
        "total_missing_exact_optimal_count": total_missing_exact,
        "all_scalable_diagnostic_evidence_complete": all(
            bool(row.get("scalable_diagnostic_evidence_complete")) for row in blockers.values()
        ),
        "diagnostic_gap_can_complete_project": False,
        "blockers": blockers,
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
    candidate = path if path.is_absolute() else root / path
    if candidate.exists():
        return candidate
    rewritten = re.sub(r"lunar_ice_(\d{3})", r"lunar_ice_sp50_\1", str(path))
    if rewritten != str(path):
        rewrite_candidate = Path(rewritten)
        rewrite_candidate = rewrite_candidate if rewrite_candidate.is_absolute() else root / rewrite_candidate
        if rewrite_candidate.exists():
            return rewrite_candidate
    return candidate
