#!/usr/bin/env python3
"""Prepare and test the isolated P0V4 bidirectional feasibility prototype."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml

from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.exact.bpc.core.column_signature import (
    column_signature_from_journey,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
    BackendPricingRequest,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
    _manual_backend_reduced_cost,
    _native_request_payload,
    _reconstruct_column,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.native_bidirectional_hybrid import (
    NativeBidirectionalMidpointHybridBackend,
)
from lunar_ice_bpc.exact.bpc.pricing.bidirectional_feasibility import (
    BIDIRECTIONAL_FEASIBILITY_POLICY_ID,
    split_and_rejoin_journey,
)
from lunar_ice_bpc.exact.core.branching import (
    DIFFERENT_JOURNEY,
    SAME_JOURNEY,
    BranchContext,
    PairBranchDecision,
    branch_context_from_payload,
    filter_journey_columns_by_branch_context,
    journey_satisfies_branch_context,
)
from lunar_ice_bpc.exact.core.cuts import (
    CutContext,
    canonical_subset_row_cut,
    cut_context_from_payload,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import (
    JourneyDuals,
    manual_journey_reduced_cost,
)
from lunar_ice_bpc.exact.solver.journey_driver import (
    enumerate_direct_journey_columns,
)
from lunar_ice_bpc.exact.bpc.guidance.replay import (
    load_pricing_snapshot,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    ROOT
    / "configs/experiments/p0v4_bidirectional_feasibility_v1.yaml"
)
DEFAULT_OUTPUT = ROOT / "runs/p0v4_bidirectional_feasibility_v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--stage",
        choices=(
            "prepare",
            "small-differential",
            "heavy-snapshot-probe",
        ),
        default="prepare",
    )
    parser.add_argument("--snapshot-index", type=int, default=1)
    args = parser.parse_args()
    config_path = _resolve(args.config)
    output = _resolve(args.output_dir)
    config = _load_yaml(config_path)
    output.mkdir(parents=True, exist_ok=True)
    if args.stage == "prepare":
        payload = _prepare(config, config_path)
        _write_json(output / "prepare_manifest.json", payload)
    elif args.stage == "small-differential":
        _require_prepared(output)
        payload = _small_differential(config)
        _write_json(output / "small_differential_report.json", payload)
    else:
        _require_prepared(output)
        snapshot_index = int(args.snapshot_index)
        payload = _heavy_snapshot_probe(
            config,
            snapshot_index=snapshot_index,
        )
        _write_json(
            output
            / (
                f"heavy_snapshot_{snapshot_index:02d}_"
                "journey_probe.json"
            ),
            payload,
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if bool(payload.get("gate_pass")) else 1


def _prepare(config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    control = dict(config["frozen_control"])
    verified_files = {}
    issues: list[str] = []
    for field in ("config", "manifest"):
        path = _resolve(control[field])
        observed = _sha256(path) if path.is_file() else ""
        expected = str(control[f"{field}_sha256"])
        verified_files[field] = {
            "path": str(path),
            "expected_sha256": expected,
            "observed_sha256": observed,
            "match": bool(observed == expected),
        }
        if observed != expected:
            issues.append(f"frozen_control_{field}_hash_mismatch")
    verifier = _resolve(control["verifier"])
    verify_process = subprocess.run(
        [sys.executable, str(verifier)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        freeze_audit = json.loads(verify_process.stdout)
    except json.JSONDecodeError:
        freeze_audit = {
            "valid": False,
            "stdout": verify_process.stdout,
            "stderr": verify_process.stderr,
        }
    if verify_process.returncode != 0 or not freeze_audit.get("valid"):
        issues.append("p0v4_freeze_verification_failed")

    native_build = dict(config["isolated_native_build"])
    install_dir = _resolve(native_build["install_directory"])
    build_probe = _probe_native_build(install_dir)
    required_info = dict(native_build["required_build_info"])
    for key, expected in required_info.items():
        if str(build_probe.get("build_info", {}).get(key)) != str(expected):
            issues.append(f"native_build_info_mismatch:{key}")
    if not build_probe.get("probe_callable"):
        issues.append("native_bidirectional_probe_missing")

    registry_path = _resolve(config["heavy_snapshot_stage"]["registry"])
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    heavy_rows = [
        dict(row)
        for row in registry.get("snapshots", [])
        if str(row.get("role")) == "heavy"
    ]
    required_heavy = int(
        config["heavy_snapshot_stage"]["required_heavy_snapshot_count"]
    )
    if len(heavy_rows) != required_heavy:
        issues.append("heavy_snapshot_count_mismatch")
    heavy_snapshot_audit = []
    for row in heavy_rows:
        path = Path(str(row["path"])).resolve()
        observed = _sha256(path) if path.is_file() else ""
        match = observed == str(row.get("sha256") or "")
        if not match:
            issues.append(f"heavy_snapshot_hash_mismatch:{path.name}")
        heavy_snapshot_audit.append(
            {
                "path": str(path),
                "sha256": observed,
                "registry_sha256": str(row.get("sha256") or ""),
                "match": match,
                "source_final_judge_wall_time_sec": row.get(
                    "source_final_judge_wall_time_sec"
                ),
            }
        )

    source_files = []
    for value in config.get("source_files", []):
        path = _resolve(value)
        source_files.append(
            {
                "path": str(path),
                "sha256": _sha256(path) if path.is_file() else "",
                "exists": path.is_file(),
            }
        )
        if not path.is_file():
            issues.append(f"source_file_missing:{value}")
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v4_bidirectional_feasibility_prepare.v1"
        ),
        "experiment_id": config["experiment_id"],
        "policy_id": config["policy_id"],
        "gate_pass": not issues,
        "status": "PREPARED" if not issues else "PREPARE_FAILED",
        "issues": issues,
        "config_path": str(config_path),
        "config_sha256": _sha256(config_path),
        "frozen_control_files": verified_files,
        "frozen_control_audit": freeze_audit,
        "isolated_native_build": build_probe,
        "heavy_snapshots": heavy_snapshot_audit,
        "source_files": source_files,
        "p0v4_runtime_path_mutated": False,
        "production_default_changed": False,
        "can_certify_no_negative": False,
        "next_required_stage": "small-differential",
    }


def _small_differential(config: dict[str, Any]) -> dict[str, Any]:
    policy = dict(config["small_differential"])
    target = int(policy["required_join_cases"])
    instance_count = int(policy["generated_instance_count"])
    midpoint_target = int(policy["required_midpoint_cases"])
    midpoint_instance_count = int(
        policy["midpoint_generated_instance_count"]
    )
    midpoint_split_fractions = tuple(
        float(value)
        for value in policy["midpoint_split_fractions"]
    )
    scale = int(policy["scale"])
    first_seed = int(policy["first_seed"])
    objective_tolerance = float(policy["objective_abs_tolerance"])
    rc_tolerance = float(policy["reduced_cost_abs_tolerance"])
    install_dir = _resolve(
        config["isolated_native_build"]["install_directory"]
    )
    sys.path.insert(0, str(install_dir))
    native = importlib.import_module("lunar_spprc_native")
    module_path = Path(str(native.__file__)).resolve()
    if install_dir not in module_path.parents:
        raise RuntimeError(
            "small differential loaded a non-isolated Native module: "
            f"{module_path}"
        )

    tested = 0
    structural_mismatches = 0
    objective_mismatches = 0
    rc_mismatches = 0
    certificate_leaks = 0
    native_status_mismatches = 0
    branch_fail_closed_failures = 0
    overlap_fail_closed_failures = 0
    max_objective_delta = 0.0
    max_python_rc_delta = 0.0
    max_native_rc_delta = 0.0
    instances_used = 0
    for instance_offset in range(instance_count):
        if tested >= target:
            break
        data = load_lunar_ice_data(
            generate_instance(
                scale,
                seed=first_seed + instance_offset,
                index=instance_offset + 1,
            )
        )
        universe = enumerate_direct_journey_columns(
            data,
            max_exact_tasks=scale,
        )
        cut = canonical_subset_row_cut(data.task_ids[:3])
        cut_context = CutContext(cuts=(cut,))
        duals = JourneyDuals(
            cover={
                task_id: (
                    0.013 * (task_index + 1)
                    + 0.0001 * instance_offset
                )
                for task_index, task_id in enumerate(data.task_ids)
            },
            fleet_limit=0.07 + 0.001 * instance_offset,
            cuts={cut.cut_id: 0.11 + 0.001 * instance_offset},
        )
        request = BackendPricingRequest(
            data=data,
            true_duals=duals,
            cut_context=cut_context,
        )
        native_base = _native_request_payload(request)
        instances_used += 1
        for column in universe.columns:
            expected_rc = manual_journey_reduced_cost(
                column,
                duals,
                cut_coefficients=cut_context.coefficients_for(column),
            )
            sortie_rows = [
                {
                    "tasks": list(sortie.tasks),
                    "path_types": [
                        str(leg.path_type) for leg in sortie.legs
                    ],
                }
                for sortie in column.sorties
            ]
            for split in range(len(sortie_rows) + 1):
                if tested >= target:
                    break
                audit = split_and_rejoin_journey(
                    data,
                    column,
                    split_sortie_index=split,
                    true_duals=duals,
                    cut_context=cut_context,
                )
                native_audit = dict(
                    native.bidirectional_feasibility_probe(
                        {
                            **native_base,
                            "forward_sorties": sortie_rows[:split],
                            "backward_sorties": sortie_rows[split:],
                        }
                    )
                )
                tested += 1
                if (
                    audit.can_certify_no_negative
                    or bool(native_audit["can_certify_no_negative"])
                ):
                    certificate_leaks += 1
                if (
                    not audit.feasible
                    or audit.journey is None
                    or audit.status
                    != "FEASIBLE_JOIN_DIAGNOSTIC_ONLY"
                ):
                    structural_mismatches += 1
                    continue
                source = column_signature_from_journey(column)
                joined = column_signature_from_journey(audit.journey)
                if (
                    source.task_set != joined.task_set
                    or source.sortie_partition
                    != joined.sortie_partition
                    or source.path_option_signature
                    != joined.path_option_signature
                ):
                    structural_mismatches += 1
                objective_delta = abs(
                    float(column.objective)
                    - float(audit.journey.objective)
                )
                max_objective_delta = max(
                    max_objective_delta,
                    objective_delta,
                )
                if objective_delta > objective_tolerance:
                    objective_mismatches += 1
                python_rc_delta = abs(
                    float(expected_rc)
                    - float(audit.true_reduced_cost)
                )
                max_python_rc_delta = max(
                    max_python_rc_delta,
                    python_rc_delta,
                )
                if python_rc_delta > rc_tolerance:
                    rc_mismatches += 1
                if (
                    native_audit["status"]
                    != "FEASIBLE_JOIN_DIAGNOSTIC_ONLY"
                    or not native_audit["feasible"]
                ):
                    native_status_mismatches += 1
                native_rc_delta = abs(
                    float(expected_rc)
                    - float(native_audit["true_reduced_cost"])
                )
                max_native_rc_delta = max(
                    max_native_rc_delta,
                    native_rc_delta,
                )
                if native_rc_delta > rc_tolerance:
                    rc_mismatches += 1

        if universe.columns:
            singleton = next(
                (
                    column
                    for column in universe.columns
                    if len(column.task_set) == 1
                ),
                universe.columns[0],
            )
            present = next(iter(singleton.task_set))
            absent = next(
                task_id
                for task_id in data.task_ids
                if task_id not in singleton.task_set
            )
            branch_context = BranchContext(
                pair_decisions=(
                    PairBranchDecision(
                        task_a=present,
                        task_b=absent,
                        sense=SAME_JOURNEY,
                    ),
                )
            )
            branch_audit = split_and_rejoin_journey(
                data,
                singleton,
                split_sortie_index=0,
                true_duals=duals,
                branch_context=branch_context,
                cut_context=cut_context,
            )
            if (
                branch_audit.status != "BRANCH_CONTEXT_INFEASIBLE"
                or branch_audit.can_certify_no_negative
            ):
                branch_fail_closed_failures += 1
            first_sortie = sortie_rows = [
                {
                    "tasks": list(singleton.sorties[0].tasks),
                    "path_types": [
                        str(leg.path_type)
                        for leg in singleton.sorties[0].legs
                    ],
                }
            ]
            overlap_audit = dict(
                native.bidirectional_feasibility_probe(
                    {
                        **native_base,
                        "forward_sorties": first_sortie,
                        "backward_sorties": first_sortie,
                    }
                )
            )
            if (
                overlap_audit["status"] != "TASK_SET_OVERLAP"
                or overlap_audit["feasible"]
                or overlap_audit["can_certify_no_negative"]
            ):
                overlap_fail_closed_failures += 1

    midpoint_tested = 0
    midpoint_instances_used = 0
    midpoint_exhaustiveness_failures = 0
    midpoint_rc_mismatches = 0
    midpoint_index_accounting_failures = 0
    midpoint_certificate_leaks = 0
    midpoint_limit_fail_closed_failures = 0
    midpoint_route_reconstruction_failures = 0
    midpoint_returned_route_rc_mismatches = 0
    midpoint_returned_route_duplicate_task_sets = 0
    max_midpoint_rc_delta = 0.0
    max_midpoint_returned_route_rc_delta = 0.0
    for instance_offset in range(midpoint_instance_count):
        if midpoint_tested >= midpoint_target:
            break
        data = load_lunar_ice_data(
            generate_instance(
                scale,
                seed=first_seed + 10_000 + instance_offset,
                index=instance_offset + 1,
            )
        )
        universe = enumerate_direct_journey_columns(
            data,
            max_exact_tasks=scale,
        )
        cut = canonical_subset_row_cut(data.task_ids[:3])
        cut_context = CutContext(cuts=(cut,))
        branch_context = BranchContext(
            pair_decisions=(
                PairBranchDecision(
                    task_a=data.task_ids[0],
                    task_b=data.task_ids[1],
                    sense=(
                        SAME_JOURNEY
                        if instance_offset % 2 == 0
                        else DIFFERENT_JOURNEY
                    ),
                ),
            )
        )
        dual_scale = 0.0 if instance_offset % 4 == 0 else 1.0
        duals = JourneyDuals(
            cover={
                task_id: dual_scale * (
                    0.013 * (task_index + 1)
                    + 0.0001 * instance_offset
                )
                for task_index, task_id in enumerate(data.task_ids)
            },
            fleet_limit=dual_scale * (
                0.07 + 0.001 * instance_offset
            ),
            cuts={
                cut.cut_id: dual_scale * (
                    0.11 + 0.001 * instance_offset
                )
            },
        )
        feasible_columns = filter_journey_columns_by_branch_context(
            universe.columns,
            branch_context,
        )
        if not feasible_columns:
            midpoint_exhaustiveness_failures += 1
            continue
        expected_best_rc = min(
            manual_journey_reduced_cost(
                column,
                duals,
                cut_coefficients=cut_context.coefficients_for(column),
            )
            for column in feasible_columns
        )
        request = BackendPricingRequest(
            data=data,
            true_duals=duals,
            branch_context=branch_context,
            cut_context=cut_context,
        )
        native_base = _native_request_payload(request)
        midpoint_instances_used += 1
        for split_fraction in midpoint_split_fractions:
            if midpoint_tested >= midpoint_target:
                break
            midpoint = dict(
                native.bidirectional_midpoint_journey_meet(
                    {
                        **native_base,
                        "bidirectional_max_partial_states_per_direction": (
                            1_000_000
                        ),
                        "bidirectional_max_join_checks": 5_000_000,
                        "bidirectional_sortie_wall_time_limit_sec": 30.0,
                        "bidirectional_midpoint_split_fraction": (
                            split_fraction
                        ),
                        "bidirectional_midpoint_max_forward_labels": (
                            100_000
                        ),
                        "bidirectional_midpoint_max_backward_labels": (
                            100_000
                        ),
                        "bidirectional_midpoint_max_crossing_labels": (
                            100_000
                        ),
                        "bidirectional_midpoint_max_extension_checks": (
                            10_000_000
                        ),
                        "bidirectional_midpoint_max_join_checks": (
                            5_000_000
                        ),
                        "bidirectional_midpoint_wall_time_limit_sec": (
                            30.0
                        ),
                    }
                )
            )
            midpoint_tested += 1
            if bool(midpoint["can_certify_no_negative"]):
                midpoint_certificate_leaks += 1
            if (
                midpoint["status"]
                != "MIDPOINT_MEET_COMPLETE_DIAGNOSTIC_ONLY"
                or not bool(midpoint["search_exhaustive"])
            ):
                midpoint_exhaustiveness_failures += 1
                continue
            if (
                int(midpoint["join_checks"])
                != int(midpoint["time_index_candidate_join_pairs"])
                or int(midpoint["unindexed_active_join_pairs"])
                != int(midpoint["time_index_candidate_join_pairs"])
                + int(midpoint["time_index_pruned_join_pairs"])
            ):
                midpoint_index_accounting_failures += 1
            midpoint_rc_delta = abs(
                float(expected_best_rc)
                - float(midpoint["best_true_reduced_cost"])
            )
            max_midpoint_rc_delta = max(
                max_midpoint_rc_delta,
                midpoint_rc_delta,
            )
            if midpoint_rc_delta > rc_tolerance:
                midpoint_rc_mismatches += 1
            returned_routes = tuple(midpoint.get("routes") or ())
            if int(midpoint["returned_negative_route_count"]) != len(
                returned_routes
            ):
                midpoint_route_reconstruction_failures += 1
            if (
                float(midpoint["best_true_reduced_cost"])
                < -float(native_base["negative_eps"])
                and not returned_routes
            ):
                midpoint_route_reconstruction_failures += 1
            if returned_routes:
                best_returned_delta = abs(
                    float(returned_routes[0]["reduced_cost"])
                    - float(midpoint["best_true_reduced_cost"])
                )
                max_midpoint_returned_route_rc_delta = max(
                    max_midpoint_returned_route_rc_delta,
                    best_returned_delta,
                )
                if best_returned_delta > rc_tolerance:
                    midpoint_returned_route_rc_mismatches += 1
            returned_task_sets: set[frozenset[str]] = set()
            for returned_route in returned_routes:
                try:
                    column = _reconstruct_column(
                        request,
                        returned_route,
                    )
                except Exception:
                    midpoint_route_reconstruction_failures += 1
                    continue
                task_set = frozenset(str(x) for x in column.task_set)
                if task_set in returned_task_sets:
                    midpoint_returned_route_duplicate_task_sets += 1
                returned_task_sets.add(task_set)
                if not journey_satisfies_branch_context(
                    column,
                    branch_context,
                ):
                    midpoint_route_reconstruction_failures += 1
                manual_route_rc = _manual_backend_reduced_cost(
                    column,
                    request,
                )
                returned_route_rc_delta = abs(
                    float(returned_route["reduced_cost"])
                    - float(manual_route_rc)
                )
                max_midpoint_returned_route_rc_delta = max(
                    max_midpoint_returned_route_rc_delta,
                    returned_route_rc_delta,
                )
                if returned_route_rc_delta > rc_tolerance:
                    midpoint_returned_route_rc_mismatches += 1
        if instance_offset == 0:
            limited = dict(
                native.bidirectional_midpoint_journey_meet(
                    {
                        **native_base,
                        "bidirectional_max_partial_states_per_direction": (
                            1_000_000
                        ),
                        "bidirectional_max_join_checks": 5_000_000,
                        "bidirectional_sortie_wall_time_limit_sec": 30.0,
                        "bidirectional_midpoint_split_fraction": 0.5,
                        "bidirectional_midpoint_max_forward_labels": 1,
                        "bidirectional_midpoint_max_backward_labels": (
                            100_000
                        ),
                        "bidirectional_midpoint_max_crossing_labels": (
                            100_000
                        ),
                        "bidirectional_midpoint_max_extension_checks": (
                            10_000_000
                        ),
                        "bidirectional_midpoint_max_join_checks": (
                            5_000_000
                        ),
                        "bidirectional_midpoint_wall_time_limit_sec": (
                            30.0
                        ),
                    }
                )
            )
            if (
                bool(limited["search_exhaustive"])
                or bool(limited["can_certify_no_negative"])
            ):
                midpoint_limit_fail_closed_failures += 1

    issues = []
    if tested < target:
        issues.append("insufficient_join_cases")
    if midpoint_tested < midpoint_target:
        issues.append("insufficient_midpoint_cases")
    for name, value in (
        ("structural_mismatch", structural_mismatches),
        ("objective_mismatch", objective_mismatches),
        ("reduced_cost_mismatch", rc_mismatches),
        ("native_status_mismatch", native_status_mismatches),
        ("certificate_leak", certificate_leaks),
        ("branch_fail_closed_failure", branch_fail_closed_failures),
        ("overlap_fail_closed_failure", overlap_fail_closed_failures),
        (
            "midpoint_exhaustiveness_failure",
            midpoint_exhaustiveness_failures,
        ),
        ("midpoint_rc_mismatch", midpoint_rc_mismatches),
        (
            "midpoint_index_accounting_failure",
            midpoint_index_accounting_failures,
        ),
        ("midpoint_certificate_leak", midpoint_certificate_leaks),
        (
            "midpoint_limit_fail_closed_failure",
            midpoint_limit_fail_closed_failures,
        ),
        (
            "midpoint_route_reconstruction_failure",
            midpoint_route_reconstruction_failures,
        ),
        (
            "midpoint_returned_route_rc_mismatch",
            midpoint_returned_route_rc_mismatches,
        ),
        (
            "midpoint_returned_route_duplicate_task_set",
            midpoint_returned_route_duplicate_task_sets,
        ),
    ):
        if value:
            issues.append(f"{name}:{value}")
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v4_bidirectional_small_differential.v1"
        ),
        "policy_id": BIDIRECTIONAL_FEASIBILITY_POLICY_ID,
        "gate_pass": not issues,
        "status": (
            "SMALL_DIFFERENTIAL_PASSED"
            if not issues
            else "SMALL_DIFFERENTIAL_FAILED"
        ),
        "issues": issues,
        "requested_join_case_count": target,
        "tested_join_case_count": tested,
        "generated_instance_count_used": instances_used,
        "requested_midpoint_case_count": midpoint_target,
        "tested_midpoint_case_count": midpoint_tested,
        "midpoint_generated_instance_count_used": (
            midpoint_instances_used
        ),
        "structural_mismatch_count": structural_mismatches,
        "objective_mismatch_count": objective_mismatches,
        "reduced_cost_mismatch_count": rc_mismatches,
        "native_status_mismatch_count": native_status_mismatches,
        "certificate_leak_count": certificate_leaks,
        "branch_fail_closed_failure_count": (
            branch_fail_closed_failures
        ),
        "overlap_fail_closed_failure_count": (
            overlap_fail_closed_failures
        ),
        "max_objective_abs_delta": max_objective_delta,
        "max_python_reduced_cost_abs_delta": max_python_rc_delta,
        "max_native_reduced_cost_abs_delta": max_native_rc_delta,
        "midpoint_exhaustiveness_failure_count": (
            midpoint_exhaustiveness_failures
        ),
        "midpoint_reduced_cost_mismatch_count": (
            midpoint_rc_mismatches
        ),
        "midpoint_index_accounting_failure_count": (
            midpoint_index_accounting_failures
        ),
        "midpoint_certificate_leak_count": (
            midpoint_certificate_leaks
        ),
        "midpoint_limit_fail_closed_failure_count": (
            midpoint_limit_fail_closed_failures
        ),
        "midpoint_route_reconstruction_failure_count": (
            midpoint_route_reconstruction_failures
        ),
        "midpoint_returned_route_rc_mismatch_count": (
            midpoint_returned_route_rc_mismatches
        ),
        "midpoint_returned_route_duplicate_task_set_count": (
            midpoint_returned_route_duplicate_task_sets
        ),
        "max_midpoint_reduced_cost_abs_delta": (
            max_midpoint_rc_delta
        ),
        "max_midpoint_returned_route_reduced_cost_abs_delta": (
            max_midpoint_returned_route_rc_delta
        ),
        "can_certify_no_negative": False,
        "p0v4_runtime_path_mutated": False,
        "next_required_stage": (
            "journey-level-forward-backward-meet"
            if not issues
            else "correctness-repair"
        ),
    }


def _heavy_snapshot_probe(
    config: dict[str, Any],
    *,
    snapshot_index: int,
) -> dict[str, Any]:
    stage = dict(config["heavy_snapshot_stage"])
    registry_path = _resolve(stage["registry"])
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    heavy_rows = [
        dict(row)
        for row in registry.get("snapshots", [])
        if str(row.get("role")) == "heavy"
    ]
    if snapshot_index < 1 or snapshot_index > len(heavy_rows):
        raise SystemExit(
            f"heavy snapshot index must be in 1..{len(heavy_rows)}"
        )
    row = heavy_rows[snapshot_index - 1]
    snapshot_path = Path(str(row["path"])).resolve()
    if _sha256(snapshot_path) != str(row["sha256"]):
        raise SystemExit("heavy snapshot hash mismatch")
    snapshot = load_pricing_snapshot(snapshot_path)
    data = load_lunar_ice_data(
        json.loads(
            _resolve(stage["instance"]).read_text(encoding="utf-8")
        )
    )
    if data.instance_content_hash != snapshot.instance_content_hash:
        raise SystemExit("heavy snapshot instance binding mismatch")
    request = BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(
            cover=dict(snapshot.true_duals.get("cover") or {}),
            fleet_limit=float(
                snapshot.true_duals.get("fleet_limit") or 0.0
            ),
            cuts=dict(snapshot.true_duals.get("cuts") or {}),
        ),
        branch_context=branch_context_from_payload(
            snapshot.branch_context
        ),
        cut_context=cut_context_from_payload(
            snapshot.full_cut_context
        ),
        memory_limit_gb=float(stage["effective_native_memory_limit_gb"]),
        wall_time_limit_sec=float(
            stage["journey_wall_time_limit_sec"]
        ),
    )
    install_dir = _resolve(
        config["isolated_native_build"]["install_directory"]
    )
    sys.path.insert(0, str(install_dir))
    native = importlib.import_module("lunar_spprc_native")
    module_path = Path(str(native.__file__)).resolve()
    if install_dir not in module_path.parents:
        raise RuntimeError(
            "heavy snapshot probe loaded a non-isolated Native module: "
            f"{module_path}"
        )
    native_payload = _native_request_payload(request)
    native_payload.update(
        {
            "bidirectional_max_partial_states_per_direction": int(
                stage["max_partial_states_per_direction"]
            ),
            "bidirectional_max_join_checks": int(
                stage["max_sortie_join_checks"]
            ),
            "bidirectional_sortie_wall_time_limit_sec": float(
                stage["sortie_wall_time_limit_sec"]
            ),
            "bidirectional_wall_time_limit_sec": float(
                stage["sortie_wall_time_limit_sec"]
            ),
            "bidirectional_max_journey_labels": int(
                stage["max_journey_labels"]
            ),
            "bidirectional_max_journey_extension_checks": int(
                stage["max_journey_extension_checks"]
            ),
            "bidirectional_negative_route_target": int(
                stage["negative_route_target"]
            ),
            "bidirectional_journey_wall_time_limit_sec": float(
                stage["journey_wall_time_limit_sec"]
            ),
            "bidirectional_immediate_subset_dominance_enabled": bool(
                stage["immediate_subset_dominance_enabled"]
            ),
            "bidirectional_midpoint_split_fraction": float(
                stage["midpoint_split_fraction"]
            ),
            "bidirectional_midpoint_max_forward_labels": int(
                stage["max_midpoint_forward_labels"]
            ),
            "bidirectional_midpoint_max_backward_labels": int(
                stage["max_midpoint_backward_labels"]
            ),
            "bidirectional_midpoint_max_crossing_labels": int(
                stage["max_midpoint_crossing_labels"]
            ),
            "bidirectional_midpoint_max_extension_checks": int(
                stage["max_midpoint_extension_checks"]
            ),
            "bidirectional_midpoint_max_join_checks": int(
                stage["max_midpoint_join_checks"]
            ),
            "bidirectional_midpoint_max_returned_negative_routes": int(
                stage["max_midpoint_returned_negative_routes"]
            ),
            "bidirectional_midpoint_wall_time_limit_sec": float(
                stage["midpoint_wall_time_limit_sec"]
            ),
        }
    )
    sortie = dict(
        native.bidirectional_task_meet_frontier_probe(
            native_payload
        )
    )
    journey = dict(
        native.bidirectional_journey_frontier_probe(
            native_payload
        )
    )
    midpoint = dict(
        native.bidirectional_midpoint_journey_meet(
            native_payload
        )
    )
    sortie.pop("build_info", None)
    journey.pop("build_info", None)
    native_build_info = midpoint.pop("build_info", {})
    midpoint_route_rows = tuple(midpoint.get("routes") or ())
    midpoint_route_audit = {
        "returned_count": len(midpoint_route_rows),
        "reconstructed_count": 0,
        "true_negative_count": 0,
        "duplicate_task_set_count": 0,
        "branch_violation_count": 0,
        "reconstruction_failure_count": 0,
        "reduced_cost_mismatch_count": 0,
        "best_route_mismatch_count": 0,
        "max_reduced_cost_abs_delta": 0.0,
    }
    seen_task_sets: set[frozenset[str]] = set()
    for returned_route in midpoint_route_rows:
        try:
            column = _reconstruct_column(request, returned_route)
        except Exception:
            midpoint_route_audit[
                "reconstruction_failure_count"
            ] += 1
            continue
        midpoint_route_audit["reconstructed_count"] += 1
        task_set = frozenset(str(x) for x in column.task_set)
        if task_set in seen_task_sets:
            midpoint_route_audit["duplicate_task_set_count"] += 1
        seen_task_sets.add(task_set)
        if not journey_satisfies_branch_context(
            column,
            request.branch_context,
        ):
            midpoint_route_audit["branch_violation_count"] += 1
        manual_rc = float(
            _manual_backend_reduced_cost(column, request)
        )
        native_rc = float(returned_route["reduced_cost"])
        rc_delta = abs(native_rc - manual_rc)
        midpoint_route_audit["max_reduced_cost_abs_delta"] = max(
            float(
                midpoint_route_audit[
                    "max_reduced_cost_abs_delta"
                ]
            ),
            rc_delta,
        )
        if rc_delta > 2.0e-6:
            midpoint_route_audit[
                "reduced_cost_mismatch_count"
            ] += 1
        if manual_rc < -float(request.negative_eps):
            midpoint_route_audit["true_negative_count"] += 1
    if (
        int(midpoint.get("returned_negative_route_count") or 0)
        != len(midpoint_route_rows)
    ):
        midpoint_route_audit["reconstruction_failure_count"] += 1
    if (
        float(midpoint["best_true_reduced_cost"])
        < -float(request.negative_eps)
        and not midpoint_route_rows
    ):
        midpoint_route_audit["best_route_mismatch_count"] += 1
    if midpoint_route_rows:
        best_route_delta = abs(
            float(midpoint_route_rows[0]["reduced_cost"])
            - float(midpoint["best_true_reduced_cost"])
        )
        if best_route_delta > 2.0e-6:
            midpoint_route_audit["best_route_mismatch_count"] += 1
    hybrid_result = (
        NativeBidirectionalMidpointHybridBackend().solve(request)
    )
    hybrid_payload = hybrid_result.to_payload()
    redlines = []
    if not sortie.get("join_exhaustive"):
        redlines.append("sortie_task_meet_not_exhaustive")
    if sortie.get("can_certify_no_negative"):
        redlines.append("sortie_probe_certificate_leak")
    if journey.get("can_certify_no_negative"):
        redlines.append("journey_probe_certificate_leak")
    if midpoint.get("can_certify_no_negative"):
        redlines.append("midpoint_probe_certificate_leak")
    for field in (
        "duplicate_task_set_count",
        "branch_violation_count",
        "reconstruction_failure_count",
        "reduced_cost_mismatch_count",
        "best_route_mismatch_count",
    ):
        if int(midpoint_route_audit[field]) != 0:
            redlines.append(f"midpoint_route_audit:{field}")
    if (
        int(midpoint_route_audit["true_negative_count"])
        != len(midpoint_route_rows)
    ):
        redlines.append(
            "midpoint_route_audit:nonnegative_route_returned"
        )
    if (
        hybrid_result.engine_status
        != "FOUND_NEGATIVE_PARTIAL"
    ):
        redlines.append("hybrid_backend_did_not_accept_midpoint")
    if not hybrid_result.partial_columns_valid:
        redlines.append("hybrid_backend_column_audit_failed")
    if hybrid_result.can_enter_certificate_audit:
        redlines.append("hybrid_backend_certificate_leak")
    if bool(
        hybrid_result.telemetry.get(
            "bidirectional_midpoint_hybrid_fallback_used"
        )
    ):
        redlines.append("hybrid_backend_unexpected_fallback")
    if len(hybrid_result.columns) != len(midpoint_route_rows):
        redlines.append("hybrid_backend_column_count_mismatch")
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v4_bidirectional_heavy_probe.v1"
        ),
        "gate_pass": not redlines,
        "status": (
            "HEAVY_FEASIBILITY_PROBE_COMPLETE"
            if not redlines
            else "HEAVY_FEASIBILITY_PROBE_REDLINE"
        ),
        "snapshot_index": snapshot_index,
        "source_snapshot": str(snapshot_path),
        "source_snapshot_sha256": _sha256(snapshot_path),
        "source_binding_hash": snapshot.binding.binding_hash,
        "source_final_judge_wall_time_sec": row.get(
            "source_final_judge_wall_time_sec"
        ),
        "sortie_probe": sortie,
        "journey_probe": journey,
        "midpoint_probe": midpoint,
        "midpoint_route_audit": midpoint_route_audit,
        "hybrid_backend_result": hybrid_payload,
        "native_build_info": native_build_info,
        "redlines": redlines,
        "can_certify_no_negative": False,
        "p0v4_runtime_path_mutated": False,
        "production_default_changed": False,
        "interpretation": (
            "Feasibility-only. Exhaustive sortie construction does not "
            "authorize a journey no-negative certificate; an incomplete "
            "journey frontier is an expected fail-closed result."
        ),
    }


def _probe_native_build(install_dir: Path) -> dict[str, Any]:
    code = (
        "import json,lunar_spprc_native as n;"
        "print(json.dumps({'module_path':n.__file__,"
        "'build_info':dict(n.build_info()),"
        "'probe_callable':hasattr(n,'bidirectional_feasibility_probe')},"
        "sort_keys=True))"
    )
    process = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(install_dir),
        },
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        return {
            "build_info": {},
            "probe_callable": False,
            "returncode": process.returncode,
            "stderr": process.stderr,
        }
    payload = json.loads(process.stdout)
    module_path = Path(str(payload["module_path"])).resolve()
    payload["module_in_isolated_install"] = (
        install_dir.resolve() in module_path.parents
    )
    if not payload["module_in_isolated_install"]:
        payload["probe_callable"] = False
    return payload


def _require_prepared(output: Path) -> None:
    path = output / "prepare_manifest.json"
    if not path.is_file():
        raise SystemExit(
            "prepare_manifest.json is required before small-differential"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not payload.get("gate_pass"):
        raise SystemExit("bidirectional feasibility prepare gate failed")


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"configuration is not a mapping: {path}")
    return value


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
