#!/usr/bin/env python3
"""Collect matched-budget P0/action trajectory interventions from snapshots.

This is a development-only discovery collector.  It reruns the frozen pricing
request with either no guidance (P0 control) or one legal task/arc promotion.
It never filters candidates and never emits a pricing certificate.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from math import log1p
from pathlib import Path
import random
from time import perf_counter

from lunar_ice_bpc.exact.bpc.guidance.contracts import (
    CanonicalSolveBindingV2,
    GUIDANCE_MODE_TASK_ARC,
    PricingOrderingHintsV2,
    canonical_universe_hash,
)
from lunar_ice_bpc.exact.bpc.guidance.replay import load_pricing_snapshot
from lunar_ice_bpc.exact.bpc.pricing.backends import (
    BackendPricingRequest,
    NativeRcsppInprocessBackend,
)
from lunar_ice_bpc.exact.core.branching import branch_context_from_payload
from lunar_ice_bpc.exact.core.cuts import (
    cut_context_from_payload,
    stable_payload_hash,
)
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.guidance.tensorization import (
    build_static_graph_features,
    dynamic_node_features,
    encode_queue_policy_id,
)
from lunar_ice_bpc.guidance.trajectory_targets import (
    COUNTERFACTUAL_TRAJECTORY_SCHEMA_V2,
    P0_CONTROL_ACTION_ID,
    pre_action_feature_hash,
    validate_counterfactual_trajectory_record,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-dir", required=True)
    parser.add_argument("--development-manifest", required=True)
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument(
        "--static-cache-dir",
        default="data/gat_p0v2/static_tensor_cache",
    )
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument(
        "--candidate-kind",
        action="append",
        choices=("task", "arc"),
        dest="candidate_kinds",
    )
    parser.add_argument("--candidate-count", type=int, default=4)
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument(
        "--budget-sec",
        type=float,
        action="append",
        required=True,
        help="Repeat with increasing matched restart horizons.",
    )
    parser.add_argument("--scale", type=int, action="append")
    parser.add_argument("--fold", type=int, action="append")
    parser.add_argument("--max-contexts", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260724)
    args = parser.parse_args()

    if int(args.replicates) < 3:
        raise SystemExit("counterfactual collection requires at least 3 replicates")
    if int(args.candidate_count) < 2:
        raise SystemExit("counterfactual collection requires at least 2 actions")
    horizons = tuple(sorted({float(value) for value in args.budget_sec}))
    if not horizons or horizons[0] <= 0.0:
        raise SystemExit("counterfactual budgets must be positive")
    kinds = tuple(dict.fromkeys(args.candidate_kinds or ("task", "arc")))

    split = json.loads(Path(args.split_manifest).read_text(encoding="utf-8"))
    if not bool((split.get("audit") or {}).get("passed")):
        raise SystemExit("split manifest audit did not pass")
    allowed_folds = set(args.fold or range(int(split["fold_count"])))
    allowed_scales = set(args.scale or (5, 10, 20, 30))
    development_hashes = {
        str(row["instance_content_hash"])
        for row in split.get("development", ())
        if int(row["fold"]) in allowed_folds
        and int(row["scale"]) in allowed_scales
    }
    forbidden_hashes = {
        str(row["instance_content_hash"])
        for partition in ("calibration", "protected_final_test")
        for row in split.get(partition, ())
    }
    if development_hashes & forbidden_hashes:
        raise SystemExit("counterfactual collector partition overlap")

    development = json.loads(
        Path(args.development_manifest).read_text(encoding="utf-8")
    )
    instance_paths = {
        str(row["instance_content_hash"]): Path(row["path"])
        for row in development.get("instances", ())
    }
    static_cache_dir = Path(args.static_cache_dir)
    output = Path(args.output_jsonl)
    output.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(int(args.seed))
    records = []
    context_count = 0
    for snapshot_path in sorted(Path(args.snapshot_dir).rglob("*.json")):
        if context_count >= max(1, int(args.max_contexts)):
            break
        content_hint = snapshot_path.parent.name
        if content_hint in forbidden_hashes:
            continue
        if content_hint not in development_hashes:
            continue
        snapshot = load_pricing_snapshot(snapshot_path)
        if snapshot.instance_content_hash not in development_hashes:
            continue
        instance_path = instance_paths.get(snapshot.instance_content_hash)
        if instance_path is None:
            raise SystemExit(
                f"instance path missing for {snapshot.instance_content_hash}"
            )
        data = load_lunar_ice_data(
            json.loads(instance_path.read_text(encoding="utf-8"))
        )
        base_request = _request_from_snapshot(snapshot, data)
        binding = CanonicalSolveBindingV2.from_backend_request(base_request)
        if binding.binding_hash != snapshot.binding.binding_hash:
            raise SystemExit("snapshot/backend request binding mismatch")
        static = build_static_graph_features(data)
        cache_path = static_cache_dir / f"{data.instance_content_hash}.json"
        if not cache_path.exists():
            raise SystemExit(f"static tensor sidecar missing: {cache_path}")
        static_cache = json.loads(cache_path.read_text(encoding="utf-8"))
        resource_context = [
            log1p(max(0.0, snapshot.memory_limit_gb) * (1024.0**3)),
            log1p(max(horizons)),
            0.0,
            encode_queue_policy_id(snapshot.queue_policy_id),
        ]
        feature_hash = pre_action_feature_hash(
            binding_hash=binding.binding_hash,
            static_tensor_cache_hash=str(
                static_cache["static_tensor_cache_hash"]
            ),
            dynamic_node_features=dynamic_node_features(
                replace(
                    base_request,
                    wall_time_limit_sec=max(horizons),
                )
            ),
            resource_context=resource_context,
        )
        for kind in kinds:
            candidate_ids = (
                tuple(data.task_ids)
                if kind == "task"
                else tuple(static.arc_candidate_ids)
            )
            selected = _select_actions(
                candidate_ids,
                count=int(args.candidate_count),
                context_hash=snapshot.snapshot_hash,
                kind=kind,
                seed=int(args.seed),
            )
            record = _collect_record(
                snapshot=snapshot,
                base_request=base_request,
                candidate_kind=kind,
                candidate_ids=candidate_ids,
                selected_actions=selected,
                horizons=horizons,
                replicates=int(args.replicates),
                feature_hash=feature_hash,
                rng=rng,
                random_seed=int(args.seed),
            )
            validate_counterfactual_trajectory_record(record)
            records.append(record)
        context_count += 1

    if not records:
        raise SystemExit("no eligible development snapshots found")
    output.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in records
        ),
        encoding="utf-8",
    )
    report = {
        "schema_version": (
            "lunar_ice_bpc.gat_counterfactual_collection_report.v1"
        ),
        "output_jsonl": str(output.resolve()),
        "record_count": len(records),
        "context_count": context_count,
        "candidate_kinds": list(kinds),
        "candidate_count_per_record": int(args.candidate_count),
        "replicates": int(args.replicates),
        "requested_budget_horizons_sec": list(horizons),
        "effective_single_run_budget_sec": max(horizons),
        "restart_horizons_used_as_event_times": False,
        "measurement_protocol": (
            "matched_budget_single_run_native_event_trace_v1"
        ),
        "development_only": True,
        "calibration_used": False,
        "protected_final_test_used": False,
        "guidance_filter_count": 0,
        "can_certify": False,
        "utility_semantics": (
            "native_event_time_negative_discovery_auc_diagnostic_only_"
            "not_master_addability_or_rmp_gain"
        ),
        "formal_first_stage_eligible": False,
        "reason": (
            "task_arc_priority_is_mechanism_diagnostic_only; reviewed "
            "first stage requires route-level harvest compliance"
        ),
    }
    report_path = output.with_suffix(output.suffix + ".report.json")
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(str(report_path.resolve()))
    return 0


def _collect_record(
    *,
    snapshot,
    base_request: BackendPricingRequest,
    candidate_kind: str,
    candidate_ids: tuple[str, ...],
    selected_actions: tuple[str, ...],
    horizons: tuple[float, ...],
    replicates: int,
    feature_hash: str,
    rng: random.Random,
    random_seed: int,
) -> dict:
    legal_hash = canonical_universe_hash(
        candidate_ids, universe_kind=candidate_kind
    )
    arm_points: dict[tuple[str, str], list[dict]] = {
        (f"replicate-{replicate}", action_id): []
        for replicate in range(replicates)
        for action_id in (P0_CONTROL_ACTION_ID, *selected_actions)
    }
    arm_audits: dict[tuple[str, str], list[dict]] = {
        key: [] for key in arm_points
    }
    run_orders: dict[tuple[str, str], list[int]] = {
        key: [] for key in arm_points
    }
    backend = NativeRcsppInprocessBackend()
    global_run_order = 0
    horizon = max(horizons)
    for replicate in range(replicates):
        replicate_id = f"replicate-{replicate}"
        action_order = [P0_CONTROL_ACTION_ID, *selected_actions]
        rng.shuffle(action_order)
        for action_id in action_order:
            global_run_order += 1
            request = _intervention_request(
                base_request,
                candidate_kind=candidate_kind,
                action_id=action_id,
                wall_time_limit_sec=horizon,
            )
            started = perf_counter()
            result = backend.solve(request)
            actual_wall = perf_counter() - started
            telemetry = dict(result.telemetry)
            before_hash = str(
                telemetry.get(
                    "legal_action_universe_hash_before_sort"
                    if candidate_kind == "task"
                    else "legal_arc_universe_hash_before_sort"
                )
                or ""
            )
            if before_hash != legal_hash:
                raise RuntimeError(
                    "native counterfactual legal universe hash mismatch"
                )
            validation = dict(telemetry.get("guidance_validation") or {})
            if action_id != P0_CONTROL_ACTION_ID and not bool(
                validation.get("guidance_accepted")
            ):
                raise RuntimeError(
                    "counterfactual ordering hint was not accepted"
                )
            if result.labels_dropped:
                raise RuntimeError(
                    "labels_dropped cannot enter counterfactual targets"
                )
            trace_valid = bool(
                telemetry.get(
                    "best_reduced_cost_event_trace_usable_for_training"
                )
            )
            if not trace_valid:
                raise RuntimeError(
                    "counterfactual collection requires an audited native "
                    "best-RC event trace: "
                    + str(
                        telemetry.get(
                            "best_reduced_cost_event_trace_error"
                        )
                        or "missing"
                    )
                )
            native_wall = min(
                float(horizon),
                max(
                    0.0,
                    float(telemetry.get("wall_time_seconds") or 0.0),
                ),
            )
            install_sec = float(
                telemetry.get("guidance_native_install_sec") or 0.0
            )
            event_rows = list(
                telemetry.get("best_reduced_cost_events_audited") or ()
            )
            points = [
                {
                    "elapsed_sec": float(event["elapsed_sec"]),
                    "allocated_search_budget_sec": float(horizon),
                    "actual_wall_sec": float(actual_wall),
                    "forced_intervention_solver_wall_sec": native_wall,
                    "hint_install_sec_diagnostic_only": install_sec,
                    "best_true_rc": float(event["best_true_rc"]),
                    "rmp_progress": None,
                    "event_extended_labels": int(
                        event["extended_labels"]
                    ),
                    "event_solution_count": int(
                        event["solution_count"]
                    ),
                    "observed_negative_column_count": len(
                        result.columns
                    ),
                    "search_exhaustive": bool(
                        result.search_exhaustive
                    ),
                    "frontier_empty": bool(result.frontier_empty),
                }
                for event in event_rows
            ]
            terminal_time = max(
                native_wall,
                points[-1]["elapsed_sec"] if points else 0.0,
            )
            terminal_time = min(float(horizon), terminal_time)
            if not points or terminal_time > points[-1]["elapsed_sec"]:
                points.append(
                    {
                        "elapsed_sec": terminal_time,
                        "allocated_search_budget_sec": float(horizon),
                        "actual_wall_sec": float(actual_wall),
                        "forced_intervention_solver_wall_sec": native_wall,
                        "hint_install_sec_diagnostic_only": install_sec,
                        "best_true_rc": (
                            None
                            if not points
                            else points[-1]["best_true_rc"]
                        ),
                        "rmp_progress": None,
                        "event_extended_labels": int(
                            telemetry.get("extended_labels") or 0
                        ),
                        "event_solution_count": int(
                            telemetry.get("solution_count") or 0
                        ),
                        "observed_negative_column_count": len(
                            result.columns
                        ),
                        "search_exhaustive": bool(
                            result.search_exhaustive
                        ),
                        "frontier_empty": bool(
                            result.frontier_empty
                        ),
                    }
                )
            arm_points[(replicate_id, action_id)].extend(points)
            arm_audits[(replicate_id, action_id)].append(
                {
                    "engine_status": str(result.engine_status),
                    "binding_match": bool(
                        validation.get(
                            "guidance_accepted",
                            action_id == P0_CONTROL_ACTION_ID,
                        )
                    ),
                    "native_event_trace_valid": trace_valid,
                    "guidance_filter_count": int(
                        telemetry.get("guidance_filter_count") or 0
                    ),
                    "guidance_arc_drop_count": int(
                        telemetry.get("guidance_arc_drop_count") or 0
                    ),
                    "guidance_label_drop_count": int(
                        telemetry.get("guidance_label_drop_count") or 0
                    ),
                    "guidance_branch_pair_drop_count": int(
                        telemetry.get("guidance_branch_pair_drop_count")
                        or 0
                    ),
                }
            )
            run_orders[(replicate_id, action_id)].append(
                global_run_order
            )

    budget_sec = max(horizons)
    arms = []
    for (replicate_id, action_id), points in sorted(arm_points.items()):
        audits = arm_audits[(replicate_id, action_id)]
        memory_adverse_event = any(
            "MEMORY" in str(audit["engine_status"]).upper()
            for audit in audits
        )
        found_event = any(
            point.get("best_true_rc") is not None for point in points
        )
        termination_reason = (
            "MEMORY_LIMIT"
            if memory_adverse_event
            else (
                "COMPLETED_WITH_EVENT"
                if found_event
                else "WALL_TIME_BUDGET_REACHED"
            )
        )
        is_control = action_id == P0_CONTROL_ACTION_ID
        selection_probability = (
            1.0
            if is_control
            else min(1.0, len(selected_actions) / len(candidate_ids))
        )
        arms.append(
            {
                "action_id": action_id,
                "intervention_kind": (
                    "control"
                    if is_control
                    else "promote_next"
                ),
                "replicate_id": replicate_id,
                "propensity": selection_probability,
                "action_sampling_probability": selection_probability,
                "probe_policy_id": (
                    "p0_noop_plus_fixed_seed_uniform_without_replacement_v1"
                ),
                "candidate_pool_size": len(candidate_ids),
                "candidate_position_under_p0": (
                    None
                    if is_control
                    else candidate_ids.index(action_id) + 1
                ),
                "action_selection_reason": (
                    "mandatory_p0_keep_order"
                    if is_control
                    else "fixed_seed_uniform_probe"
                ),
                "random_seed": int(random_seed),
                "run_order": ",".join(
                    str(value)
                    for value in run_orders[(replicate_id, action_id)]
                ),
                "machine_block_id": "local-process-block",
                "measurement_protocol": (
                    "matched_budget_single_run_native_event_trace_v1"
                ),
                "trajectory": points,
                "legal_universe_hash_before_sort": legal_hash,
                "legal_universe_hash_after_sort": legal_hash,
                "binding_match": all(
                    bool(audit["binding_match"])
                    for audit in audits
                    if action_id != P0_CONTROL_ACTION_ID
                )
                if action_id != P0_CONTROL_ACTION_ID
                else True,
                "guidance_filter_count": sum(
                    audit["guidance_filter_count"] for audit in audits
                ),
                "guidance_arc_drop_count": sum(
                    audit["guidance_arc_drop_count"] for audit in audits
                ),
                "guidance_label_drop_count": sum(
                    audit["guidance_label_drop_count"] for audit in audits
                ),
                "guidance_branch_pair_drop_count": sum(
                    audit["guidance_branch_pair_drop_count"]
                    for audit in audits
                ),
                "labels_dropped": False,
                "promotion_requested": not is_control,
                "promotion_candidate_id": (
                    None if is_control else action_id
                ),
                "promotion_installed": not is_control,
                "promotion_executed": None,
                "actual_execution_rank": None,
                "first_effective_action_id": None,
                "treatment_compliance": (
                    "p0_noop"
                    if is_control
                    else "not_observable_for_task_arc_feature_priority"
                ),
                "noncompliance_reason": (
                    ""
                    if is_control
                    else "native_task_arc_score_is_cumulative_not_a_direct_action"
                ),
                "termination_reason": termination_reason,
                "competing_risk_reason": (
                    termination_reason if memory_adverse_event else ""
                ),
                "memory_adverse_event": memory_adverse_event,
                "resource_safety_gate_pass": not memory_adverse_event,
                "engine_statuses": [
                    audit["engine_status"] for audit in audits
                ],
            }
        )
    return {
        "schema_version": COUNTERFACTUAL_TRAJECTORY_SCHEMA_V2,
        "snapshot_hash": snapshot.snapshot_hash,
        "binding_hash": snapshot.binding.binding_hash,
        "instance_content_hash": snapshot.instance_content_hash,
        "rmp_context_hash": snapshot.binding.binding_hash,
        "scale": len(base_request.data.task_ids),
        "candidate_kind": candidate_kind,
        "candidate_ids": list(candidate_ids),
        "legal_universe_hash_before_sort": legal_hash,
        "pre_action_feature_hash": feature_hash,
        "budget_sec": budget_sec,
        "model_wall_time_budget_sec": max(horizons),
        "wall_time_budget_sec": budget_sec,
        "label_budget": None,
        "extension_budget": None,
        "memory_budget_bytes": int(
            max(0.0, base_request.memory_limit_gb) * (1024.0**3)
        ),
        "budget_mode": "matched_wall_time",
        "guidance_overhead_included": False,
        "solver_model_cost_separated": True,
        "model_cost_included_in_solver_utility": False,
        "forced_intervention_solver_wall": True,
        "guidance_import_sec": 0.0,
        "guidance_checkpoint_load_sec": 0.0,
        "guidance_tensorize_sec": 0.0,
        "guidance_forward_sec": 0.0,
        "model_guidance_total_wall_sec": 0.0,
        "post_action_features_exposed_to_model": False,
        "utility_kind": "negative_discovery_auc",
        "pre_treatment_rc_scale": max(
            1.0e-6,
            abs(
                float(
                    snapshot.result_summary.get("best_found_rc")
                    or snapshot.result_summary.get("global_min_rc")
                    or 1.0
                )
            ),
        ),
        "pre_treatment_rc_scale_source": (
            "frozen_p0_snapshot_best_found_rc_before_new_interventions"
        ),
        "rc_utility_transform": "clipped_linear_v1",
        "advantage_risk_kappa": 1.96,
        "soft_target_temperature": 0.05,
        "utility_semantics": (
            "silver_negative_column_discovery_not_master_addability"
        ),
        "event_time_source": "native_best_reduced_cost_events_v1",
        "native_event_trace_valid": all(
            bool(audit.get("native_event_trace_valid"))
            for audits in arm_audits.values()
            for audit in audits
        ),
        "restart_horizon_points_used_as_event_times": False,
        "arms": arms,
        "can_certify": False,
    }


def _intervention_request(
    request: BackendPricingRequest,
    *,
    candidate_kind: str,
    action_id: str,
    wall_time_limit_sec: float,
) -> BackendPricingRequest:
    base = replace(
        request,
        wall_time_limit_sec=float(wall_time_limit_sec),
        guidance_mode="off",
        guidance_hints=None,
        guidance_lifecycle_telemetry=tuple(),
    )
    if action_id == P0_CONTROL_ACTION_ID:
        return base
    binding = CanonicalSolveBindingV2.from_backend_request(base)
    hints = PricingOrderingHintsV2(
        binding_hash=binding.binding_hash,
        task_priorities=(
            ((action_id, 1.0),) if candidate_kind == "task" else tuple()
        ),
        arc_priorities=(
            ((action_id, 1.0),) if candidate_kind == "arc" else tuple()
        ),
        queue_policy_id="Q0",
        uncertainty=0.0,
        ood=False,
        source="counterfactual_development_probe",
        diagnostic_only=False,
    )
    return replace(
        base,
        guidance_mode=GUIDANCE_MODE_TASK_ARC,
        guidance_hints=hints,
    )


def _select_actions(
    candidate_ids: tuple[str, ...],
    *,
    count: int,
    context_hash: str,
    kind: str,
    seed: int,
) -> tuple[str, ...]:
    ordered = sorted(
        candidate_ids,
        key=lambda candidate_id: stable_payload_hash(
            {
                "context_hash": str(context_hash),
                "candidate_kind": str(kind),
                "candidate_id": str(candidate_id),
                "random_seed": int(seed),
            }
        ),
    )
    return tuple(ordered[: min(len(ordered), max(2, int(count)))])


def _request_from_snapshot(snapshot, data) -> BackendPricingRequest:
    return BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(
            cover=dict(snapshot.true_duals.get("cover") or {}),
            fleet_limit=_optional_float_default(
                snapshot.true_duals.get("fleet_limit"), 0.0
            ),
            cuts=dict(snapshot.true_duals.get("cuts") or {}),
        ),
        mode=snapshot.pricing_mode,
        objective_mode=snapshot.objective_mode,
        branch_context=branch_context_from_payload(snapshot.branch_context),
        cut_context=cut_context_from_payload(snapshot.full_cut_context),
        wall_time_limit_sec=snapshot.wall_time_budget_sec,
        memory_limit_gb=snapshot.memory_limit_gb,
        instance_hash=snapshot.binding.instance_hash,
        config_hash=snapshot.binding.config_hash,
        engine_hash=snapshot.binding.engine_hash,
        dual_binding_hash=snapshot.binding.mathematical_dual_hash,
        cut_lineage_hash=snapshot.binding.cut_lineage_hash,
        live_cut_policy_hash=snapshot.binding.live_cut_policy_hash,
        rmp_iteration_id=snapshot.binding.rmp_iteration_id,
        separator_policy_version=snapshot.binding.separator_policy_version,
    )


def _optional_float_default(value, default: float) -> float:
    return float(default) if value is None else float(value)


if __name__ == "__main__":
    raise SystemExit(main())
