"""B5 guidance suite runner over lunar-ice instances."""

from __future__ import annotations

from itertools import combinations
from pathlib import Path
from typing import Any

from lunar_ice_bpc.exact.bpc.guidance.shadow import build_guidance_output_bundle
from lunar_ice_bpc.exact.bpc.solver.gat_guidance_solver import run_b5_guidance_ablation_suite
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.guidance.shadow_policy import build_shadow_report
from lunar_ice_bpc.io.instance_io import read_json, write_json


def run_b5_guidance_suite(
    *,
    project_root: str | Path,
    instances: list[str] | None = None,
    manifest_path: str | Path | None = None,
    scales: list[int] | None = None,
    output_json: str | Path | None = None,
    guidance_mode: str = "shadow_only",
    enabled_ordering_modes: list[str] | None = None,
    max_direct_tasks: int = 5,
    max_rounds: int = 8,
    negative_eps: float = 1.0e-6,
    diagnostic_policy_version: str = "deterministic_shadow_policy_v1",
) -> dict[str, Any]:
    """Run B5 do-no-harm guidance suite and optionally write the JSON payload."""

    root = Path(project_root).resolve()
    instance_paths = _resolve_instance_paths(root, instances=instances, manifest_path=manifest_path, scales=scales)
    ordering_modes = _effective_ordering_modes(guidance_mode, enabled_ordering_modes)
    rows: list[dict[str, Any]] = []
    for instance_path in instance_paths:
        instance = read_json(instance_path)
        data = load_lunar_ice_data(instance)
        row = _build_suite_row(
            instance=instance,
            instance_path=instance_path,
            enabled_ordering_modes=ordering_modes,
            diagnostic_policy_version=diagnostic_policy_version,
        )
        row["data"] = data
        rows.append(row)
    suite = run_b5_guidance_ablation_suite(
        rows,
        max_direct_tasks=max_direct_tasks,
        max_rounds=max_rounds,
        negative_eps=negative_eps,
    )
    suite["runner"] = {
        "schema_version": "lunar_ice_bpc.b5_guidance_suite_runner.v1",
        "guidance_mode": str(guidance_mode),
        "enabled_ordering_modes": list(ordering_modes),
        "instance_count": len(instance_paths),
        "instance_paths": [str(path) for path in instance_paths],
        "diagnostic_policy_version": str(diagnostic_policy_version),
        "mutates_solver": False,
        "can_certify": False,
        "exact_status_effect": "none",
        "note": "Runner builds deterministic shadow guidance heads; B5 suite remains audit-only guidance.",
    }
    if output_json is not None:
        target = _root_path(root, output_json)
        suite["runner"]["output_json"] = str(target)
        write_json(target, suite)
    return suite


def validate_b5_suite_config(config: dict[str, Any]) -> list[str]:
    """Return fail-closed issues for unsafe B5 guidance suite configs."""

    issues: list[str] = []
    guidance_mode = str(config.get("guidance_mode", "shadow_only"))
    allowed_modes = {"shadow_only", "ordering_opt_in", "opt_in"}
    if guidance_mode not in allowed_modes:
        issues.append(f"unsupported guidance_mode={guidance_mode!r}")
    if bool(config.get("mutates_solver", False)):
        issues.append("B5 guidance suite refuses mutates_solver=true")
    if bool(config.get("can_certify", False)):
        issues.append("B5 guidance suite refuses can_certify=true")
    if bool(config.get("can_prune", False)) or bool(config.get("can_fathom", False)):
        issues.append("B5 guidance suite refuses prune/fathom-capable guidance")
    if guidance_mode in {"ordering_opt_in", "opt_in"} and bool(config.get("journey_gat_optin_enabled", False)):
        issues.append("B5 suite ordering opt-in is dry-run only; journey_gat_optin_enabled must remain false")
    if config.get("journey_gat_shadow_enabled") is False:
        issues.append("B5 guidance suite requires journey_gat_shadow_enabled=true")
    return issues


def _build_suite_row(
    *,
    instance: dict[str, Any],
    instance_path: Path,
    enabled_ordering_modes: tuple[str, ...],
    diagnostic_policy_version: str,
) -> dict[str, Any]:
    shadow = build_shadow_report(instance)
    priority_rows = list(shadow["task_priority"])
    pricing_hints = [
        _hint(
            candidate_id=str(row["id"]),
            priority=float(row["shadow_priority_score"]),
            feature_schema_version=str(shadow["guidance_graph_schema_version"]),
        )
        for row in priority_rows
    ]
    branch_candidates, branch_hints = _branch_candidates_and_hints(
        priority_rows,
        feature_schema_version=str(shadow["guidance_graph_schema_version"]),
    )
    harvest_candidates = [
        {"candidate_id": f"harvest:{row['id']}", "task_id": row["id"]}
        for row in priority_rows
    ]
    harvest_hints = [
        _hint(
            candidate_id=f"harvest:{row['id']}",
            priority=float(row["shadow_priority_score"]),
            feature_schema_version=str(shadow["guidance_graph_schema_version"]),
        )
        for row in priority_rows
    ]
    bundle = build_guidance_output_bundle(
        pricing_priority_head=pricing_hints,
        branch_priority_head=branch_hints,
        harvest_priority_head=harvest_hints,
        ood_diagnostics={
            "status": "SHADOW_AUDIT_ONLY",
            "ood_rule_version": diagnostic_policy_version,
        },
        confidence_diagnostics={
            "status": "SHADOW_AUDIT_ONLY",
            "threshold_version": diagnostic_policy_version,
        },
        diagnostic_policy_versions={"diagnostic_policy_version": diagnostic_policy_version},
    )
    return {
        "instance_path": str(instance_path),
        "instance": shadow["instance_id"],
        "scale": str(instance.get("scale")),
        "seed_family": _seed_family_from_instance_id(str(shadow["instance_id"])),
        "guidance_output_bundle": bundle,
        "pricing_candidates": [{"candidate_id": str(row["id"])} for row in priority_rows],
        "branch_candidates": branch_candidates,
        "harvest_candidates": harvest_candidates,
        "enabled_ordering_modes": enabled_ordering_modes,
        "no_guidance_workload": _dry_run_equal_workload(),
        "guidance_workload": _dry_run_equal_workload(),
    }


def _hint(*, candidate_id: str, priority: float, feature_schema_version: str) -> dict[str, Any]:
    return {
        "candidate_id": str(candidate_id),
        "priority": float(priority),
        "source": "deterministic_shadow_policy",
        "finite_delay_budget": 0,
        "uncertainty": 0.0,
        "diagnostic_only": True,
        "model_version": "no_model_shadow_v1",
        "feature_schema_version": str(feature_schema_version),
    }


def _branch_candidates_and_hints(
    priority_rows: list[dict[str, Any]],
    *,
    feature_schema_version: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    score_by_id = {str(row["id"]): float(row["shadow_priority_score"]) for row in priority_rows}
    candidate_rows: list[dict[str, Any]] = []
    hint_rows: list[dict[str, Any]] = []
    for left, right in combinations(sorted(score_by_id), 2):
        candidate_id = f"branch:{left}|{right}"
        priority = 0.5 * (score_by_id[left] + score_by_id[right])
        candidate_rows.append({"candidate_id": candidate_id, "pair": [left, right]})
        hint_rows.append(
            _hint(
                candidate_id=candidate_id,
                priority=priority,
                feature_schema_version=feature_schema_version,
            )
        )
    return candidate_rows, hint_rows


def _dry_run_equal_workload() -> dict[str, Any]:
    return {
        "wall_time": 0.0,
        "pricing_calls": 0.0,
        "final_judge_calls": 0.0,
        "generated_labels": 0.0,
        "rmp_iterations": 0.0,
        "node_count": 0.0,
        "observation_source": "dry_run_no_solver_mutation_zero_diff",
        "workload_units": "guidance_delta_proxy",
    }


def _resolve_instance_paths(
    root: Path,
    *,
    instances: list[str] | None,
    manifest_path: str | Path | None,
    scales: list[int] | None,
) -> list[Path]:
    if instances:
        return [_root_path(root, raw) for raw in instances]
    if manifest_path is None:
        raise ValueError("provide instances or manifest_path")
    manifest = read_json(_root_path(root, manifest_path))
    allowed = {f"{int(scale):03d}" for scale in scales} if scales else None
    paths: list[Path] = []
    for row in manifest.get("instances", []):
        scale_label = _manifest_row_scale_label(row)
        if allowed is not None and scale_label not in allowed:
            continue
        paths.append(_root_path(root, row["path"]))
    return paths


def _effective_ordering_modes(
    guidance_mode: str,
    enabled_ordering_modes: list[str] | None,
) -> tuple[str, ...]:
    if str(guidance_mode) == "shadow_only":
        return tuple()
    raw_modes = enabled_ordering_modes or ["pricing", "branch", "harvest"]
    return tuple(str(mode) for mode in raw_modes)


def _manifest_row_scale_label(row: dict[str, Any]) -> str:
    if row.get("scale_label") is not None:
        return f"{int(str(row['scale_label']).strip()):03d}"
    if row.get("scale") is not None:
        return f"{int(row['scale']):03d}"
    path = str(row.get("path", ""))
    for scale in (5, 10, 20, 30, 50, 100):
        if f"lunar_ice_{scale:03d}" in path:
            return f"{scale:03d}"
    return ""


def _seed_family_from_instance_id(instance_id: str) -> str:
    marker = "seed"
    value = str(instance_id)
    if marker not in value:
        return "unknown"
    seed = value.rsplit(marker, 1)[-1]
    return seed[:3] if seed else "unknown"


def _root_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path
