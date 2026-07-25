#!/usr/bin/env python3
"""Collect formal route-order counterfactuals by fixed-P0 RMP rollout."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
from time import perf_counter

from lunar_ice_bpc.exact.bpc.core.column_pool import (
    BpcColumn,
    ColumnPool,
)
from lunar_ice_bpc.exact.bpc.core.column_signature import (
    column_signature_from_journey,
)
from lunar_ice_bpc.exact.bpc.core.master_column_view import (
    MasterColumnView,
)
from lunar_ice_bpc.exact.bpc.guidance.contracts import (
    canonical_harvest_candidate_id,
    canonical_universe_hash,
)
from lunar_ice_bpc.exact.bpc.master.journey_master import (
    solve_root_journey_master,
)
from lunar_ice_bpc.exact.bpc.pricing.harvest import (
    harvest_addable_negative_columns,
)
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (
    _add_selected_to_pool_and_master,
    _load_columns,
    solve_node_pricing_with_b2b_r3,
)
from lunar_ice_bpc.exact.bpc.solver.root_node_solver import (
    _reference_seed_direct_placeholder,
    build_b1_seed_columns,
)
from lunar_ice_bpc.exact.core.cuts import stable_payload_hash
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.core.objective import OBJECTIVE_SPEC_ID
from lunar_ice_bpc.exact.master.journey_rmp import (
    manual_journey_reduced_cost,
)
from lunar_ice_bpc.guidance.trajectory_targets import (
    COUNTERFACTUAL_TRAJECTORY_SCHEMA_V2,
    FIXED_POOL_PRICING_PRESSURE_OBJECTIVE_SPEC_V1,
    P0_CONTROL_ACTION_ID,
    materialize_counterfactual_targets,
    validate_counterfactual_trajectory_record,
)
from lunar_ice_bpc.guidance.opportunity_gate import (
    OPPORTUNITY_OBSERVATION_SCHEMA_V1,
    validate_opportunity_observation,
)


def main() -> int:
    collection_started = perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--max-direct-tasks", type=int, default=30)
    parser.add_argument("--discovery-time-limit-sec", type=float, default=60.0)
    parser.add_argument("--candidate-universe-cap", type=int, default=64)
    parser.add_argument("--probe-count", type=int, default=8)
    parser.add_argument("--rollout-horizon", type=int, default=4)
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument("--negative-eps", type=float, default=1.0e-6)
    parser.add_argument(
        "--sampling-stream",
        choices=("sentinel", "targeted"),
        default="targeted",
    )
    parser.add_argument("--selection-probability", type=float, default=1.0)
    parser.add_argument(
        "--selection-manifest-hash",
        default="",
        help=(
            "Targeted-stream diagnostic only. Sentinel rows derive this "
            "value from --selection-manifest and ignore manual values."
        ),
    )
    parser.add_argument(
        "--selection-manifest",
        default="",
        help=(
            "Required for sentinel rows. The collector verifies that the "
            "instance was selected before looking at its outcomes."
        ),
    )
    parser.add_argument("--context-sequence-id", type=int, default=0)
    parser.add_argument("--solver-elapsed-sec", type=float, default=0.0)
    parser.add_argument("--opportunity-output-jsonl", default="")
    parser.add_argument(
        "--cheap-gate-min-candidates", type=int, default=2
    )
    parser.add_argument(
        "--cheap-gate-min-negative-mass", type=float, default=0.0
    )
    parser.add_argument(
        "--model-call-wall-sec-upper-bound", type=float
    )
    parser.add_argument(
        "--model-cost-source",
        choices=("fresh_runtime_measured", "frozen_budget_upper_bound"),
        default="",
    )
    parser.add_argument("--startup-cost-share-sec", type=float, default=0.0)
    args = parser.parse_args()
    if args.replicates < 3:
        raise SystemExit("formal rollout requires at least 3 replicates")
    if args.probe_count < 2:
        raise SystemExit("formal rollout requires at least 2 promotions")
    if args.rollout_horizon < 1:
        raise SystemExit("rollout horizon must be positive")
    if (
        args.selection_probability <= 0.0
        or args.selection_probability > 1.0
    ):
        raise SystemExit("selection probability must be in (0,1]")
    if args.sampling_stream == "sentinel":
        if not args.selection_manifest:
            raise SystemExit(
                "sentinel collection requires --selection-manifest"
            )
        if args.model_call_wall_sec_upper_bound is None:
            raise SystemExit(
                "sentinel collection requires a frozen/measured model-call "
                "cost upper bound"
            )
        if not args.model_cost_source:
            raise SystemExit(
                "sentinel collection requires --model-cost-source"
            )

    instance_path = Path(args.instance)
    output = Path(args.output_jsonl)
    data = load_lunar_ice_data(
        json.loads(instance_path.read_text(encoding="utf-8"))
    )
    if args.sampling_stream == "sentinel":
        _bind_sentinel_selection(args, data=data)
    b0_seed = _reference_seed_direct_placeholder(data)
    initial_columns, seed_report = build_b1_seed_columns(
        data,
        b0_direct=b0_seed,
        seed_mode="b0_incumbent_plus_singletons",
        max_direct_tasks=int(args.max_direct_tasks),
    )
    discovery = solve_node_pricing_with_b2b_r3(
        data,
        initial_columns=initial_columns,
        b0_direct=b0_seed,
        max_direct_tasks=int(args.max_direct_tasks),
        max_rounds=1,
        max_columns_per_round=int(args.candidate_universe_cap),
        wall_time_limit_sec=float(args.discovery_time_limit_sec),
        harvest_micro_batch_size=int(args.candidate_universe_cap),
        harvest_deferred_candidate_limit=max(
            10000, 4 * int(args.candidate_universe_cap)
        ),
    )
    raw_candidates = tuple(discovery.get("_all_priced_columns") or ())
    initial_master = solve_root_journey_master(
        data,
        tuple(initial_columns),
        negative_eps=float(args.negative_eps),
        rmp_iteration_id="gat-harvest-rmp-rollout-initial",
    )
    if initial_master.rmp.status != "RESTRICTED_RMP_OPTIMAL":
        raise SystemExit("initial rollout RMP is not optimal")
    pool, view = _pool_and_view(tuple(initial_columns))
    negative_pairs = tuple(
        (
            float(
                manual_journey_reduced_cost(
                    column, initial_master.rmp.duals
                )
            ),
            column,
        )
        for column in raw_candidates
    )
    candidate_columns, harvest_audit = (
        harvest_addable_negative_columns(
            negative_pairs,
            pool=pool,
            view=view,
            negative_eps=float(args.negative_eps),
            max_selected=max(2, int(args.candidate_universe_cap)),
        )
    )
    if len(candidate_columns) < 2:
        return _write_ineligible_report(
            output,
            data=data,
            reason="fewer_than_two_legal_route_actions",
            discovery=discovery,
            raw_candidate_count=len(raw_candidates),
            candidate_count=len(candidate_columns),
            harvest_audit=harvest_audit,
            args=args,
            collection_started=collection_started,
        )
    candidate_ids = tuple(
        canonical_harvest_candidate_id(
            column_signature_from_journey(column)
        )
        for column in candidate_columns
    )
    if len(candidate_ids) != len(set(candidate_ids)):
        raise SystemExit("route rollout candidate IDs are not unique")
    legal_hash = canonical_universe_hash(
        candidate_ids, universe_kind="harvest"
    )
    probe_ids = _spread_probe_ids(
        candidate_ids, count=min(int(args.probe_count), len(candidate_ids))
    )
    column_by_id = dict(zip(candidate_ids, candidate_columns, strict=True))
    initial_objective = float(initial_master.rmp.objective_bound)
    objective_scale = max(1.0e-6, abs(initial_objective))
    initial_candidate_rcs = tuple(
        float(
            manual_journey_reduced_cost(
                column, initial_master.rmp.duals
            )
        )
        for column in candidate_columns
    )
    initial_negative_mass = sum(
        max(0.0, -value)
        for value in initial_candidate_rcs
        if value < -abs(float(args.negative_eps))
    )
    initial_negative_count = sum(
        value < -abs(float(args.negative_eps))
        for value in initial_candidate_rcs
    )
    if initial_negative_count <= 0 or initial_negative_mass <= 0.0:
        return _write_ineligible_report(
            output,
            data=data,
            reason="fixed_shortlist_has_no_pricing_pressure",
            discovery=discovery,
            raw_candidate_count=len(raw_candidates),
            candidate_count=len(candidate_columns),
            harvest_audit=harvest_audit,
            args=args,
            collection_started=collection_started,
        )
    binding_hash = stable_payload_hash(
        {
            "schema_version": "lunar_ice_bpc.fixed_rmp_rollout_binding.v1",
            "instance_content_hash": data.instance_content_hash,
            "dual_fingerprint": initial_master.reduced_cost_context.dual_fingerprint,
            "initial_column_ids": [
                canonical_harvest_candidate_id(
                    column_signature_from_journey(column)
                )
                for column in initial_columns
            ],
            "candidate_ids": list(candidate_ids),
        }
    )
    initial_active_columns_hash = stable_payload_hash(
        [
            column.to_solution_payload(vehicle_id=f"initial-{index}")
            for index, column in enumerate(initial_columns)
        ]
    )
    arms = []
    run_order = 0
    action_ids = (P0_CONTROL_ACTION_ID, *probe_ids)
    for replicate in range(int(args.replicates)):
        for action_id in action_ids:
            run_order += 1
            ordered_ids = (
                candidate_ids
                if action_id == P0_CONTROL_ACTION_ID
                else (
                    action_id,
                    *(
                        candidate_id
                        for candidate_id in candidate_ids
                        if candidate_id != action_id
                    ),
                )
            )
            points, compliance = _rollout(
                data,
                initial_columns=tuple(initial_columns),
                ordered_columns=tuple(
                    column_by_id[candidate_id]
                    for candidate_id in ordered_ids
                ),
                horizon=int(args.rollout_horizon),
                negative_eps=float(args.negative_eps),
                initial_objective=initial_objective,
                objective_scale=objective_scale,
                pressure_columns=candidate_columns,
                initial_negative_mass=initial_negative_mass,
                initial_negative_count=initial_negative_count,
            )
            is_control = action_id == P0_CONTROL_ACTION_ID
            arms.append(
                {
                    "action_id": action_id,
                    "intervention_kind": (
                        "control" if is_control else "promote_next"
                    ),
                    "replicate_id": f"replicate-{replicate}",
                    "propensity": (
                        1.0
                        if is_control
                        else len(probe_ids) / len(candidate_ids)
                    ),
                    "action_sampling_probability": (
                        1.0
                        if is_control
                        else len(probe_ids) / len(candidate_ids)
                    ),
                    "probe_policy_id": (
                        "deterministic_spread_over_p0_shortlist_v1"
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
                        else "deterministic_position_spread"
                    ),
                    "run_order": run_order,
                    "machine_block_id": "fixed-rmp-rollout",
                    "measurement_protocol": (
                        "fixed_p0_rmp_column_admission_rollout_v1"
                    ),
                    "trajectory": points,
                    "legal_universe_hash_before_sort": legal_hash,
                    "legal_universe_hash_after_sort": legal_hash,
                    "binding_match": True,
                    "guidance_filter_count": 0,
                    "guidance_arc_drop_count": 0,
                    "guidance_label_drop_count": 0,
                    "guidance_branch_pair_drop_count": 0,
                    "labels_dropped": False,
                    "promotion_requested": not is_control,
                    "promotion_candidate_id": (
                        None if is_control else action_id
                    ),
                    "promotion_installed": not is_control,
                    "promotion_executed": (
                        None if is_control else compliance
                    ),
                    "actual_execution_rank": (
                        None if is_control else (1 if compliance else None)
                    ),
                    "first_effective_action_id": (
                        None if is_control else action_id
                    ),
                    "treatment_compliance": (
                        "p0_noop"
                        if is_control
                        else (
                            "compliant"
                            if compliance
                            else "not_executed"
                        )
                    ),
                    "noncompliance_reason": (
                        ""
                        if is_control or compliance
                        else "promoted_column_did_not_enter_fresh_rmp"
                    ),
                    "termination_reason": "COMPLETED_WITH_EVENT",
                    "competing_risk_reason": "",
                    "memory_adverse_event": False,
                    "resource_safety_gate_pass": True,
                }
            )
    record = {
        "schema_version": COUNTERFACTUAL_TRAJECTORY_SCHEMA_V2,
        "snapshot_hash": stable_payload_hash(
            {
                "binding_hash": binding_hash,
                "candidate_ids": candidate_ids,
            }
        ),
        "binding_hash": binding_hash,
        "instance_content_hash": data.instance_content_hash,
        "rmp_context_hash": binding_hash,
        "scale": len(data.task_ids),
        "candidate_kind": "harvest",
        "candidate_ids": list(candidate_ids),
        "legal_universe_hash_before_sort": legal_hash,
        "pre_action_feature_hash": stable_payload_hash(
            {
                "binding_hash": binding_hash,
                "candidate_ids": candidate_ids,
            }
        ),
        "budget_sec": float(args.rollout_horizon),
        "model_wall_time_budget_sec": float(
            args.discovery_time_limit_sec
        ),
        "budget_mode": "matched_extension_count",
        "extension_budget": int(args.rollout_horizon),
        "budget_axis": "column_admission_count",
        "legacy_elapsed_sec_field_unit": "column_admission_step",
        "guidance_overhead_included": False,
        "solver_model_cost_separated": True,
        "model_cost_included_in_solver_utility": False,
        "post_action_features_exposed_to_model": False,
        "utility_kind": "fixed_pool_pricing_pressure_auc",
        "trajectory_objective_spec_id": (
            FIXED_POOL_PRICING_PRESSURE_OBJECTIVE_SPEC_V1
        ),
        "pre_treatment_rc_scale": objective_scale,
        "pre_treatment_rc_scale_source": "fixed_initial_rmp_objective",
        # This diagnostic adds one route per extension step.  Current P0
        # admits a batch as a set and sorts active semantic signatures before
        # the next RMP, so this is not the online treatment being proposed.
        "formal_first_stage_eligible": False,
        "online_admission_semantics_match": False,
        "online_admission_semantics_mismatch_reason": (
            "single_column_extension_probe_vs_p0_batch_set_admission"
        ),
        "event_time_source": "fixed_p0_rmp_rollout_v1",
        "native_event_trace_valid": False,
        "rmp_rollout_trace_valid": True,
        "p0_rollout_policy_hash": stable_payload_hash(
            {
                "policy": "p0_order_after_optional_single_promotion",
                "horizon": int(args.rollout_horizon),
            }
        ),
        "rollout_horizon": int(args.rollout_horizon),
        "phase_objective_mode": "official",
        "initial_active_columns_hash": initial_active_columns_hash,
        "initial_basis_hash": stable_payload_hash(
            "fresh_rmp_no_basis_reuse"
        ),
        "dual_stabilization_state_hash": stable_payload_hash("off"),
        "worker_policy_hash": stable_payload_hash(
            "fixed_candidate_pool_no_new_pricing"
        ),
        "queue_policy_id": "Q0",
        "column_pool_hash": initial_active_columns_hash,
        "cache_state_hash": stable_payload_hash("fresh"),
        "thread_count": 1,
        "candidate_universe_policy": (
            "deterministic_p0_addable_shortlist_no_guidance"
        ),
        "pricing_pressure_target": (
            "0.5*negative_mass_reduction+"
            "0.5*negative_count_reduction"
        ),
        "initial_fixed_pool_negative_mass": initial_negative_mass,
        "initial_fixed_pool_negative_count": initial_negative_count,
        "candidate_universe_cap": int(args.candidate_universe_cap),
        "raw_priced_candidate_count": len(raw_candidates),
        "harvest_audit": {
            key: harvest_audit.get(key)
            for key in (
                "candidate_negative_count",
                "addable_negative_count",
                "selected_count",
                "legal_action_universe_hash_before_sort",
                "guidance_filter_count",
            )
        },
        "seed_report_hash": stable_payload_hash(
            {
                "seed_mode": seed_report.get("seed_mode"),
                "seed_builder": seed_report.get("seed_builder"),
                "initial_column_count": len(initial_columns),
                "initial_active_columns_hash": (
                    initial_active_columns_hash
                ),
            }
        ),
        "calibration_used": False,
        "protected_final_test_used": False,
        "can_certify": False,
        "sampling_stream": str(args.sampling_stream),
        "selection_probability": float(args.selection_probability),
        "selection_manifest_hash": str(args.selection_manifest_hash),
        "selection_decision_pre_action": True,
        "target_condition_used_for_selection": (
            args.sampling_stream == "targeted"
        ),
        "arms": arms,
    }
    validate_counterfactual_trajectory_record(record)
    targets = materialize_counterfactual_targets(
        record, candidate_ids=record["candidate_ids"]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report = {
        "schema_version": "lunar_ice_bpc.harvest_rmp_rollout_report.v1",
        "output_jsonl": str(output.resolve()),
        "instance_content_hash": data.instance_content_hash,
        "scale": len(data.task_ids),
        "formal_first_stage_eligible": False,
        "online_admission_semantics_match": False,
        "candidate_count": len(candidate_ids),
        "probe_count": len(probe_ids),
        "rollout_horizon": int(args.rollout_horizon),
        "oracle_training_not_authorized_until_headroom_audit": True,
        "calibration_used": False,
        "protected_final_test_used": False,
    }
    report_path = output.with_suffix(output.suffix + ".report.json")
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    cheap_gate_started = perf_counter()
    cheap_gate_eligible = bool(
        len(candidate_ids) >= int(args.cheap_gate_min_candidates)
        and initial_negative_mass
        >= float(args.cheap_gate_min_negative_mass)
    )
    cheap_gate_wall_sec = perf_counter() - cheap_gate_started
    conservative_values = [
        float(value)
        for value, observed in zip(
            targets["counterfactual_conservative_action_values"],
            targets["counterfactual_probe_mask"],
            strict=True,
        )
        if observed
    ]
    oracle_gain = max(0.0, max(conservative_values, default=0.0))
    _write_opportunity_observation(
        output,
        args=args,
        instance_content_hash=data.instance_content_hash,
        scale=len(data.task_ids),
        rmp_context_hash=binding_hash,
        legal_action_count=len(candidate_ids),
        cheap_gate_eligible=cheap_gate_eligible,
        cheap_gate_wall_sec=cheap_gate_wall_sec,
        formal_label_available=True,
        opportunity_outcome_status="FORMAL_COUNTERFACTUAL",
        action_value_identifiable=bool(
            targets["counterfactual_action_value_identifiable"]
        ),
        oracle_solver_gain=oracle_gain,
        collection_wall_sec=perf_counter() - collection_started,
        censored_reason="",
    )
    print(str(report_path.resolve()))
    return 0


def _pool_and_view(columns):
    pool = ColumnPool()
    view = MasterColumnView()
    _load_columns(pool, view, columns)
    return pool, view


def _bind_sentinel_selection(args, *, data) -> None:
    source = Path(args.selection_manifest)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if str(payload.get("schema_version") or "") != (
        "lunar_ice_bpc.gat_sentinel_manifest.v1"
    ):
        raise SystemExit("sentinel manifest schema mismatch")
    expected_hash = stable_payload_hash(
        {
            key: value
            for key, value in payload.items()
            if key != "manifest_hash"
        }
    )
    if str(payload.get("manifest_hash") or "") != expected_hash:
        raise SystemExit("sentinel manifest content hash mismatch")
    matches = [
        row
        for row in payload.get("instances", ())
        if str(row.get("instance_content_hash") or "")
        == data.instance_content_hash
    ]
    if len(matches) != 1 or not bool(matches[0].get("selected")):
        raise SystemExit(
            "instance was not preselected by the sentinel manifest"
        )
    row = matches[0]
    if int(row.get("scale") or 0) != len(data.task_ids):
        raise SystemExit("sentinel manifest scale mismatch")
    args.selection_probability = float(row["selection_probability"])
    args.selection_manifest_hash = expected_hash


def _write_ineligible_report(
    output: Path,
    *,
    data,
    reason: str,
    discovery: dict,
    raw_candidate_count: int,
    candidate_count: int,
    harvest_audit: dict,
    args,
    collection_started: float,
) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    report_path = output.with_suffix(output.suffix + ".report.json")
    report_path.write_text(
        json.dumps(
            {
                "schema_version": (
                    "lunar_ice_bpc.harvest_rmp_rollout_report.v1"
                ),
                "output_jsonl": "",
                "instance_content_hash": data.instance_content_hash,
                "scale": len(data.task_ids),
                "status": "CENSORED_NO_ACTION_UNIVERSE",
                "formal_first_stage_eligible": False,
                "reason": str(reason),
                "raw_priced_candidate_count": int(raw_candidate_count),
                "candidate_count": int(candidate_count),
                "discovery_algorithm_status": discovery.get(
                    "algorithm_status"
                ),
                "discovery_pricing_state": discovery.get(
                    "pricing_state"
                ),
                "discovery_fail_closed_reason": discovery.get(
                    "fail_closed_reason"
                ),
                "harvest_candidate_negative_count": harvest_audit.get(
                    "candidate_negative_count"
                ),
                "harvest_addable_negative_count": harvest_audit.get(
                    "addable_negative_count"
                ),
                "unexplored_candidates_used_as_negative": False,
                "calibration_used": False,
                "protected_final_test_used": False,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_opportunity_observation(
        output,
        args=args,
        instance_content_hash=data.instance_content_hash,
        scale=len(data.task_ids),
        rmp_context_hash=stable_payload_hash(
            {
                "instance_content_hash": data.instance_content_hash,
                "context_sequence_id": int(args.context_sequence_id),
                "reason": str(reason),
            }
        ),
        legal_action_count=int(candidate_count),
        cheap_gate_eligible=False,
        cheap_gate_wall_sec=0.0,
        formal_label_available=False,
        opportunity_outcome_status=(
            "STRUCTURAL_ZERO_NO_LEGAL_ACTION"
            if bool(discovery.get("search_exhaustive"))
            and int(candidate_count) < 2
            else "CENSORED_RESOURCE_OR_DISCOVERY"
        ),
        action_value_identifiable=False,
        oracle_solver_gain=0.0,
        collection_wall_sec=perf_counter() - collection_started,
        censored_reason=str(reason),
    )
    print(str(report_path.resolve()))
    return 2


def _write_opportunity_observation(
    rollout_output: Path,
    *,
    args,
    instance_content_hash: str,
    scale: int,
    rmp_context_hash: str,
    legal_action_count: int,
    cheap_gate_eligible: bool,
    cheap_gate_wall_sec: float,
    formal_label_available: bool,
    opportunity_outcome_status: str,
    action_value_identifiable: bool,
    oracle_solver_gain: float,
    collection_wall_sec: float,
    censored_reason: str,
) -> Path:
    target = (
        Path(args.opportunity_output_jsonl)
        if str(args.opportunity_output_jsonl).strip()
        else rollout_output.with_suffix(
            rollout_output.suffix + ".opportunity.jsonl"
        )
    )
    model_would_be_invoked = bool(
        cheap_gate_eligible
        and args.sampling_stream == "sentinel"
    )
    observation_id = stable_payload_hash(
        {
            "instance_content_hash": instance_content_hash,
            "rmp_context_hash": rmp_context_hash,
            "sampling_stream": str(args.sampling_stream),
            "context_sequence_id": int(args.context_sequence_id),
            "selection_manifest_hash": str(args.selection_manifest_hash),
        }
    )
    row = {
        "schema_version": OPPORTUNITY_OBSERVATION_SCHEMA_V1,
        "observation_id": observation_id,
        "instance_content_hash": str(instance_content_hash),
        "rmp_context_hash": str(rmp_context_hash),
        "executed_objective_spec_id": OBJECTIVE_SPEC_ID,
        "scale": int(scale),
        "sampling_stream": str(args.sampling_stream),
        "selection_probability": float(args.selection_probability),
        "selection_manifest_hash": str(args.selection_manifest_hash),
        "selection_decision_pre_action": True,
        "target_condition_used_for_selection": (
            args.sampling_stream == "targeted"
        ),
        "context_sequence_id": int(args.context_sequence_id),
        "solver_elapsed_sec": float(args.solver_elapsed_sec),
        "collector_wall_sec_diagnostic_only": float(collection_wall_sec),
        "cheap_gate_policy_version": "candidate_pressure_gate_v1",
        "cheap_gate_eligible": bool(cheap_gate_eligible),
        "cheap_gate_wall_sec": float(cheap_gate_wall_sec),
        "legal_action_count": int(legal_action_count),
        "rollout_attempted": bool(formal_label_available),
        "formal_label_available": bool(formal_label_available),
        "opportunity_outcome_status": str(opportunity_outcome_status),
        "action_value_identifiable": bool(action_value_identifiable),
        "oracle_solver_gain": float(oracle_solver_gain),
        "oracle_solver_gain_unit": "fixed_pool_pricing_pressure_auc",
        # Fixed-pool pressure AUC is not a wall-time saving. A separate matched
        # end-to-end counterfactual must fill these fields before the formal
        # net-ROI gate can pass.
        "oracle_solver_time_saved_sec_lcb": None,
        "time_benefit_source": "",
        "model_would_be_invoked": model_would_be_invoked,
        "model_call_wall_sec_upper_bound": (
            0.0
            if not model_would_be_invoked
            else float(args.model_call_wall_sec_upper_bound)
        ),
        "model_cost_source": (
            str(args.model_cost_source)
            if model_would_be_invoked
            else ""
        ),
        "startup_cost_share_sec": (
            float(args.startup_cost_share_sec)
            if model_would_be_invoked
            else 0.0
        ),
        "censored_reason": str(censored_reason),
        "calibration_used": False,
        "protected_final_test_used": False,
    }
    validate_opportunity_observation(row)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def _spread_probe_ids(
    candidate_ids: tuple[str, ...], *, count: int
) -> tuple[str, ...]:
    if count >= len(candidate_ids):
        return candidate_ids
    if count <= 1:
        return (candidate_ids[-1],)
    indices = {
        round(index * (len(candidate_ids) - 1) / (count - 1))
        for index in range(count)
    }
    return tuple(candidate_ids[index] for index in sorted(indices))


def _rollout(
    data,
    *,
    initial_columns,
    ordered_columns,
    horizon: int,
    negative_eps: float,
    initial_objective: float,
    objective_scale: float,
    pressure_columns,
    initial_negative_mass: float,
    initial_negative_count: int,
):
    pool, view = _pool_and_view(initial_columns)
    points = []
    first_executed = False
    for step, column in enumerate(
        ordered_columns[:horizon], start=1
    ):
        added = _add_selected_to_pool_and_master(
            pool, view, (column,)
        )
        if step == 1:
            first_executed = added == 1
        started = perf_counter()
        master = solve_root_journey_master(
            data,
            tuple(
                stored.payload
                for signature in sorted(
                    view.signatures_by_node.get("root", set()),
                    key=repr,
                )
                if (
                    stored := pool.get(signature)
                ) is not None
            ),
            negative_eps=negative_eps,
            rmp_iteration_id=f"gat-fixed-rollout-step-{step}",
        )
        rmp_wall = perf_counter() - started
        if master.rmp.status != "RESTRICTED_RMP_OPTIMAL":
            raise RuntimeError("fixed rollout RMP failed to solve")
        objective_progress = max(
            0.0,
            (initial_objective - float(master.rmp.objective_bound))
            / objective_scale,
        )
        current_rcs = tuple(
            float(
                manual_journey_reduced_cost(
                    candidate, master.rmp.duals
                )
            )
            for candidate in pressure_columns
        )
        remaining_negative_mass = sum(
            max(0.0, -value)
            for value in current_rcs
            if value < -abs(float(negative_eps))
        )
        remaining_negative_count = sum(
            value < -abs(float(negative_eps))
            for value in current_rcs
        )
        mass_reduction = max(
            0.0,
            min(
                1.0,
                1.0
                - remaining_negative_mass / initial_negative_mass,
            ),
        )
        count_reduction = max(
            0.0,
            min(
                1.0,
                1.0
                - remaining_negative_count / initial_negative_count,
            ),
        )
        progress = 0.5 * mass_reduction + 0.5 * count_reduction
        points.append(
            {
                "elapsed_sec": float(step),
                "elapsed_budget_units": float(step),
                "best_true_rc": None,
                "rmp_progress": progress,
                "rmp_objective": float(master.rmp.objective_bound),
                "rmp_objective_progress": objective_progress,
                "remaining_fixed_pool_negative_mass": (
                    remaining_negative_mass
                ),
                "remaining_fixed_pool_negative_count": (
                    remaining_negative_count
                ),
                "fixed_pool_negative_mass_reduction": mass_reduction,
                "fixed_pool_negative_count_reduction": count_reduction,
                "rmp_wall_sec_diagnostic_only": rmp_wall,
                "column_activated": added == 1,
            }
        )
    return points, first_executed


if __name__ == "__main__":
    raise SystemExit(main())
